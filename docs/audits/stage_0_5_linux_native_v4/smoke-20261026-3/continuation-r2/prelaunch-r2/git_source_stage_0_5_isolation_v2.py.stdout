"""Explicit path/byte/process policy. Python checks are not native OS isolation."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


class ScopeViolation(PermissionError):
    pass


class Scope:
    def __init__(self, repo, bindings, output_root, *, runtime_roots=(), commands=(), native_allowed=False):
        self.repo = Path(repo).resolve()
        self.output = self._lexical(output_root)
        if not self.output.is_relative_to(self.repo) or self.output == self.repo:
            raise ScopeViolation("output_outside_repository")
        self.bindings = {self._lexical(name): value for name, value in bindings.items()}
        self.runtime = [Path(p).resolve() for p in runtime_roots]
        self.commands = [list(c) for c in commands]
        self.native_allowed = native_allowed
        self.used = []
        self.denied = []
        self.reads = []
        self.opened = set()

    def _lexical(self, value):
        path = Path(value)
        if ".." in path.parts:
            raise ScopeViolation("path_traversal")
        if not path.is_absolute():
            path = self.repo / path
        for part in [path, *path.parents]:
            if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
                raise ScopeViolation("symlink_or_junction_forbidden")
        if any(marker in str(path).lower() for marker in ["locked_holdout", "0820_0835"]):
            raise ScopeViolation("validation_path_forbidden")
        return path.resolve()

    def check(self, value, *, writing=False):
        try:
            path = self._lexical(value)
            allowed = path.is_relative_to(self.output)
            if not writing:
                allowed |= path in self.bindings or any(path.is_relative_to(p) for p in self.runtime)
            if not allowed:
                raise ScopeViolation("path_not_allowlisted:" + str(path))
            return path
        except (ScopeViolation, OSError) as error:
            self.denied.append({"path": str(value), "writing": writing, "reason": str(error)})
            raise

    def read_bound(self, name):
        path = self.check(name)
        if path not in self.bindings:
            raise ScopeViolation("exact_binding_required")
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != self.bindings[path]:
            raise ScopeViolation("input_hash_drift:" + str(path))
        self.reads.append({"path": str(path), "sha256": actual})
        return data

    def create(self, name, data):
        path = self.check(name, writing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path = self.check(path, writing=True)
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return path

    def process(self, argv, *, cwd, shell=False):
        # A decision interface, never a launcher. Consume exact commands once.
        self.check(cwd, writing=True)
        normalized = [str(x) for x in argv]
        native = any("sumo" in Path(str(x)).name.lower() or "netconvert" in Path(str(x)).name.lower() for x in argv[:1])
        if shell or (native and not self.native_allowed):
            self.denied.append({"process": normalized, "reason": "native_launch_locked_this_round"})
            raise ScopeViolation("native_launch_locked_this_round")
        if normalized not in self.commands or normalized in self.used:
            self.denied.append({"process": normalized, "reason": "command_not_allowlisted_or_reused"})
            raise ScopeViolation("command_not_allowlisted_or_reused")
        self.used.append(normalized)

    def audit(self, event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            mode, flags = args[1], args[2]
            writing = bool(isinstance(mode, str) and any(c in mode for c in "wax+"))
            writing |= bool(isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            path = self.check(os.fsdecode(args[0]), writing=writing)
            self.opened.add((str(path), bool(writing)))
        elif event in ("os.listdir", "os.scandir"):
            path = self._lexical(args[0] or os.getcwd())
            if path not in {p.parent for p in self.bindings}:
                self.check(path)
        elif event == "subprocess.Popen":
            self.denied.append({"process": str(args[1]), "reason": "offline_scope_no_subprocess"})
            raise ScopeViolation("offline_scope_no_subprocess")
        elif event in ("os.system", "os.exec", "os.spawn", "os.posix_spawn"):
            raise ScopeViolation("shell_or_exec_forbidden")
        elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime"):
            self.check(args[0], writing=True)
        elif event in ("os.rename", "os.link", "os.symlink"):
            self.check(args[0], writing=True)
            self.check(args[1], writing=True)

    def summary(self):
        return {"scope": "Python exact files and output root; no native OS certificate", "bound_read_snapshots": self.reads,
                "Python_opened_paths": [{"path": p, "write": w} for p, w in sorted(self.opened)],
                "denied": self.denied, "command_decisions": self.used, "native_isolation": "Unknown",
                "accepted_for_new_task": False}
