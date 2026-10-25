"""Executable task allowlist. Python audit is not a native/OS access proof."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys


class Boundary:
    def __init__(self, read_files, read_roots, write_root, commands=()):
        self.files = {Path(p).resolve() for p in read_files}
        self.roots = [Path(p).resolve() for p in read_roots]
        self.write = Path(write_root).resolve()
        self.commands = list(commands)
        self.denied = []
        self.opened = set()
        self.launched = []

    def check(self, value, writing=False):
        if isinstance(value, int):
            return
        p = Path(os.fsdecode(value)).resolve()
        allowed = p.is_relative_to(self.write)
        if not writing:
            allowed |= p in self.files or any(p.is_relative_to(r) for r in self.roots)
        if not allowed:
            self.denied.append({'path': str(p), 'write': writing})
            raise PermissionError('task_allowlist_denied:' + str(p))
        self.opened.add(str(p))

    def audit(self, event, args):
        if event == 'open':
            mode, flags = args[1], args[2]
            writing = bool(isinstance(mode, str) and any(x in mode for x in 'wax+'))
            writing |= bool(isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            self.check(args[0], writing)
        elif event in ('os.listdir', 'os.scandir'):
            value = args[0] if args[0] is not None else os.getcwd()
            path = Path(value).resolve()
            directories = {p.parent for p in self.files}
            directories |= {p.parent.parent for p in self.files if p.name == '__init__.py'}
            if path not in directories:
                self.check(value)
        elif event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.utime'):
            self.check(args[0], True)
        elif event in ('os.rename', 'os.link', 'os.symlink'):
            self.check(args[0], True); self.check(args[1], True)
        elif event == 'subprocess.Popen':
            executable, command, cwd, env = args
            # Explicit executable and exact command, including the Windows argv
            # rendering, must match one unused preregistered launch.
            import subprocess
            match = next((c for c in self.commands if not c.get('used') and
                          Path(executable).resolve() == Path(c['executable']).resolve() and
                          (command == c['argv'] or command == subprocess.list2cmdline(c['argv'])) and
                          (cwd is None or Path(cwd).resolve().is_relative_to(self.write))), None)
            if match is None:
                self.denied.append({'process': str(command)})
                raise PermissionError('task_process_not_registered')
            match['used'] = True
            self.launched.append(match['argv'])
        elif event in ('os.system', 'os.exec', 'os.posix_spawn', 'os.spawn'):
            self.denied.append({'event': event})
            raise PermissionError('task_shell_or_exec_forbidden')

    def save(self, path):
        Path(path).write_text(json.dumps({'scope': 'Python audit allowlist; native SUMO constrained by bound XML inputs; not OS/native complete access tracing',
            'denied': self.denied, 'opened_paths': sorted(self.opened), 'launched': self.launched}, indent=2) + '\n', encoding='utf-8')


def worker_bootstrap(spec_path, import_only=False):
    spec = json.loads(Path(spec_path).read_text())
    work = Path(spec['work'])
    binary = Path(spec['binary'])
    argv = [str(binary), '-c', str(work / 'run.sumocfg'), '--remote-port']
    # Port is allocated by the approved worker. Only this one argument is dynamic.
    boundary = Boundary(spec['read_files'], spec['runtime_roots'], work)
    base = boundary.audit
    def audit(event, args):
        if event == 'subprocess.Popen':
            import subprocess
            command = args[1]
            # Windows audit command is a string. Parse only its exact fixed
            # prefix/suffix plus a decimal port; never invoke a shell.
            prefix = subprocess.list2cmdline(argv) + ' '
            suffix = ' --no-step-log true'
            if isinstance(command, (list, tuple)):
                rendered = subprocess.list2cmdline(command)
            else:
                rendered = command
            port = rendered[len(prefix):-len(suffix)] if rendered.startswith(prefix) and rendered.endswith(suffix) else ''
            if not port.isdigit() or not 1 <= int(port) <= 65535:
                raise PermissionError('unexpected_native_command')
            boundary.commands = [{'executable': str(binary), 'argv': argv + [port, '--no-step-log', 'true'], 'used': bool(boundary.launched)}]
        base(event, args)
    sys.addaudithook(audit)
    sys.dont_write_bytecode = True
    # Do not load unbound pre-existing bytecode from tools or project sources.
    sys.pycache_prefix = str(work / 'unused_bytecode')
    sys.path.insert(0, spec['scripts'])
    try:
        from interaction_diagnostic_worker import execute
        if import_only:
            sys.path.insert(0, spec['tools'])
            import traci
        else:
            execute(work, binary, Path(spec['tools']), spec['supply'])
    finally:
        boundary.save(work / 'worker_boundary_audit.json')


if __name__ == '__main__':
    worker_bootstrap(sys.argv[1], '--import-only' in sys.argv[2:])
