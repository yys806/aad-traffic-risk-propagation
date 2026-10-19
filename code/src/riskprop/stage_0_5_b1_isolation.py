"""B1 fail-closed summary access and scoped Python execution audit.

This is task-scope protection, not an operating-system sandbox. Native libraries,
SUMO and arbitrary uninstrumented processes are outside Python audit coverage.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import sys
from pathlib import Path

WINDOWS=("us101__0750_0805","us101__0805_0820")
_ACTIVE=None


def command_parts(executable,arguments):
    argv=shlex.split(arguments,posix=False) if isinstance(arguments,str) else list(arguments)
    argv=[str(a).strip('"') for a in argv]
    return str(executable or argv[0]).strip('"'),argv


def read_reference(root,manifest,source_id,*,role):
    if source_id!="calibration_reference" or role!="calibration":
        raise PermissionError("source or role is not allowlisted")
    entry=manifest.get(source_id,{})
    if entry.get("role")!="calibration" or entry.get("kind")!="two_window_aggregate" or entry.get("path")!="calibration_reference.json":
        raise PermissionError("source binding/role/kind mismatch")
    root=Path(root).resolve();path=(root/entry["path"]).resolve()
    if not path.is_relative_to(root):raise PermissionError("source escaped input directory")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=entry.get("sha256"):raise PermissionError("source SHA mismatch")
    data=json.loads(raw)
    if data.get("kind")!="two_window_aggregate" or set(data.get("windows",{}))!=set(WINDOWS):
        raise PermissionError("full/unknown source cannot masquerade as a calibration summary")
    if set(data)-{"kind","windows","fleet","source_bindings","scope","density_thresholds"}:
        raise PermissionError("unexpected aggregate payload")
    payload=json.dumps(data)
    if any(x in payload.lower() for x in ["us101__0820_0835","locked_holdout","full_source_events"]):
        raise PermissionError("forbidden source content")
    return data


def path_access(path,capsule,runtime_roots,*,write):
    if str(path).lower() in ["nul",r"\\.\nul","/dev/null"]:return True
    target=Path(path).resolve();cap=Path(capsule).resolve()
    if target.is_relative_to(cap):return True
    return not write and any(target.is_relative_to(Path(p).resolve()) for p in runtime_roots)


def install_guard(capsule):
    """Install before importing the simulation/analysis implementation."""
    global _ACTIVE
    if _ACTIVE is not None:return _ACTIVE
    if not sys.flags.no_site:raise PermissionError("B1 controlled entry requires python -S (no site/.pth initialization)")
    capsule=Path(capsule).resolve()
    policy=json.loads((capsule/"isolation_policy.json").read_text(encoding="utf-8"))
    runtime=[Path(p).resolve() for p in policy["runtime_read_roots"]]
    safe=[str(capsule/"runtime/code/src"),str(capsule/"dependency_links"),str(Path(sys.prefix)/"Lib/site-packages")]
    safe += [p for p in sys.path if p and path_access(p,capsule,runtime,write=False)]
    sys.path[:]=list(dict.fromkeys(safe))
    binaries={str(Path(p).resolve()).lower() for p in policy["executables"]}
    audit=dict(scope="controlled Python entrypoints",allowed_open_events=0,denied=[],
        os_complete_monitoring=False,native_file_access_monitored=False,
        python_no_site=bool(sys.flags.no_site),sanitized_sys_path=list(sys.path),
        limitations=["Python audit events only; native extensions and SUMO reads not OS-traced",
            "standard-library/package/SUMO/Windows runtime roots are broader than individual dependency files",
            "same-user administrator can bypass this policy; it is not an adversarial security boundary"])
    busy=False
    def hook(event,args):
        nonlocal busy
        if busy:return
        busy=True
        try:
            if event=="open":
                path=args[0]
                if isinstance(path,int):return
                if not isinstance(path,(str,bytes,os.PathLike)):return
                mode=args[1] or "";flags=args[2] or 0
                write=any(c in str(mode) for c in "wax+") or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
                if not path_access(os.fsdecode(path),capsule,runtime,write=write):
                    audit["denied"].append(dict(event=event,path=os.fsdecode(path),write=write))
                    raise PermissionError("B1 capsule refused file access")
                audit["allowed_open_events"]+=1
            elif event in ["os.listdir","os.scandir"] and args[0] is not None and not isinstance(args[0],int):
                if not path_access(os.fsdecode(args[0]),capsule,runtime,write=False):
                    audit["denied"].append(dict(event=event,path=os.fsdecode(args[0])))
                    raise PermissionError("B1 capsule refused directory access")
            elif event=="subprocess.Popen":
                binary,argv=command_parts(args[0],args[1])
                executable=str(Path(binary).resolve()).lower()
                if executable not in binaries:
                    audit["denied"].append(dict(event=event,executable=executable))
                    raise PermissionError("B1 unapproved executable")
                if executable==str(Path(sys.executable).resolve()).lower():
                    if not any(str(capsule).lower() in str(a).lower() for a in argv[1:]):
                        raise PermissionError("B1 Python child must use a capsule entrypoint")
            elif event=="os.system":raise PermissionError("B1 shell execution disabled")
            elif event=="socket.connect":
                address=args[1]
                if isinstance(address,tuple) and address[0] not in ["127.0.0.1","localhost","::1"]:
                    raise PermissionError("B1 permits local TraCI sockets only")
        finally:busy=False
    sys.addaudithook(hook)
    _ACTIVE=audit
    return audit
