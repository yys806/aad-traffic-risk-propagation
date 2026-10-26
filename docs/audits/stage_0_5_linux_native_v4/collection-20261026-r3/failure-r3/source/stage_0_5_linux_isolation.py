"""Linux-only namespace/Landlock/seccomp/cgroup capsule. No simulator entry point.

The controller calls build_command only after exact proposal admission. This
module's CLI runs the child broker; the native build lock lives in the adapter.
Only a new capsule is writable. Kernel restrictions are inherited by children.
"""
from __future__ import annotations
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
try:
    import resource
except ImportError:  # Static review/tests on Windows; launch remains Linux-only.
    resource = None
import shutil
import signal
import socket
import struct
import subprocess
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_path(value):
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("absolute_nontraversing_path_required")
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("symlink_policy_path")
    return path


def validate(policy):
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("linux_x86_64_executor_required")
    capsule = checked_path(policy["capsule"])
    if not capsule.is_dir() or not policy["file_sha256"]:
        raise ValueError("capsule_or_bindings_missing")
    for name, expected in policy["file_sha256"].items():
        if sha(checked_path(name)) != expected:
            raise ValueError("isolation_binding_drift:" + name)
    argv = policy["argv"]
    if not argv or argv[0] not in policy["executables"]:
        raise ValueError("executable_not_allowlisted")
    if not set(policy["executables"]) <= set(policy["file_sha256"]):
        raise ValueError("unbound_executable")
    for name in policy["readonly_paths"]:
        p = checked_path(name)
        if p.is_file() and name not in policy["file_sha256"]:
            raise ValueError("unbound_readonly_file")
        if p.is_dir():
            files = {str(v) for v in p.rglob("*") if v.is_file() and not v.is_symlink()}
            if not files <= set(policy["file_sha256"]):
                raise ValueError("unbound_readonly_directory")
    if not 0 < policy["memory_bytes"] <= 3 * 1024**3 or not 0 < policy["output_bytes"] <= 2 * 1024**3:
        raise ValueError("resource_policy_outside_budget")
    if not 0 < policy["wall_s"] <= 600 or not 3 <= policy["tasks"] <= 32:
        raise ValueError("wall_or_process_budget")
    for name, source in policy["inputs"].items():
        if Path(name).name != name or name in {".", ".."} or source not in policy["file_sha256"]:
            raise ValueError("unbound_or_traversing_input")
    if policy.get("purpose")=="stage0.5-production-v4":
        runtime=json.loads(Path(policy["binding"]["runtime_manifest_path"]).read_bytes())
        if sha(policy["binding"]["runtime_manifest_path"])!=policy["binding"]["runtime_manifest_sha256"]:
            raise ValueError("runtime_manifest_binding_drift")
        if any(policy["file_sha256"].get(n)!=h for n,h in runtime["files"].items()):
            raise ValueError("runtime_closure_not_in_OS_policy")
        if policy["argv"]!=[runtime["python_executable"],"-I","-B",policy["binding"]["source_files"]["stage_0_5_linux_controller_v4.py"]]:
            raise ValueError("exact_production_controller_required")
        probe_path=policy["binding"]["capability_record_path"]
        if policy["file_sha256"].get(probe_path)!=policy["binding"]["capability_record_sha256"]:
            raise ValueError("unbound_kernel_probe")
        probe=json.loads(Path(probe_path).read_bytes())
        from stage_0_5_isolation_admission import probe_checks
        if probe["guard_sha256"]!=sha(__file__) or not all(probe_checks(probe).values()):
            raise ValueError("current_guard_kernel_probe_required")
    for field in ["scratch", "archive"]:
        path = checked_path(policy[field])
        if path.parent != capsule or path.exists():
            raise ValueError("exclusive_capsule_child_required")
    return policy


def policy_bytes(policy):
    return json.dumps(policy,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")


def build_command(policy_path, policy, *, envelope_path=None):
    validate(policy)
    path = checked_path(str(policy_path))
    if path.read_bytes() != policy_bytes(policy):
        raise ValueError("canonical_policy_bytes_required")
    unit = "aad-stage05-" + sha(path)[:24]
    command=["/usr/bin/systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
            "--expand-environment=no", "--unit=" + unit, "-p", "Type=exec",
            "-p", "MemoryMax=" + str(policy["memory_bytes"]), "-p", "MemorySwapMax=0",
            "-p", "TasksMax=" + str(policy["tasks"]), "-p", "CPUQuota=100%",
            "-p", "RuntimeMaxSec=" + str(policy["wall_s"]), "-p", "KillMode=control-group",
            "/usr/bin/unshare", "--user", "--map-root-user", "--mount", "--pid", "--fork",
            "--net", "--ipc", "--uts", "--mount-proc", "/usr/bin/python3", "-I", __file__,
            "--child", str(path), sha(path)]
    if policy.get("purpose")=="stage0.5-production-v4":
        if envelope_path is None:raise ValueError("exact_launch_envelope_required")
        envelope=checked_path(str(envelope_path))
        command.extend(["--envelope",str(envelope),sha(envelope)])
    elif envelope_path is not None:raise ValueError("unexpected_launch_envelope")
    return command


def check_call(result, label):
    if result != 0:
        e = ctypes.get_errno()
        raise OSError(e, label + ":" + os.strerror(e))


def mount(source, target, fs=None, flags=0, data=None):
    libc = ctypes.CDLL(None, use_errno=True)
    check_call(libc.mount(source.encode() if source else None, str(target).encode(),
                         fs.encode() if fs else None, ctypes.c_ulong(flags),
                         data.encode() if data else None), "mount")


def landlock(policy):
    libc = ctypes.CDLL(None, use_errno=True)
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError("landlock_ABI3_required")
    handled = (1 << 15) - 1  # FS rights through TRUNCATE; ABI3, no network claim.
    class Rule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("access", ctypes.c_uint64), ("fd", ctypes.c_int32)]
    attr = ctypes.c_uint64(handled)
    fd = libc.syscall(444, ctypes.byref(attr), 8, 0)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "landlock_create")
    try:
        # Read-only dependencies, exact executable rights, and one writable tmpfs.
        permissions = {}
        for name in policy["readonly_paths"]:
            permissions[name] = 4 | (8 if Path(name).is_dir() else 0)
        # Kernel process observations are dynamic, not a disk-file dependency.
        for name in policy.get("kernel_readonly", []):
            if name not in {"/proc","/sys/fs/cgroup"}:
                raise ValueError("unexpected_kernel_read_scope")
            permissions[name] = 4 | 8
        for name in policy["executables"]:
            permissions[name] = permissions.get(name, 0) | 1 | 4
        # No symlink, device, socket or FIFO creation and no output execution.
        permissions[policy["scratch"]] = 2 | 4 | 8 | 16 | 32 | 128 | 256 | 8192 | 16384
        for name, access in permissions.items():
            descriptor = os.open(name, os.O_PATH | os.O_CLOEXEC)
            try:
                rule = Rule(access, descriptor)
                check_call(libc.syscall(445, fd, 1, ctypes.byref(rule), 0), "landlock_add")
            finally:
                os.close(descriptor)
        check_call(libc.prctl(38, 1, 0, 0, 0), "no_new_privs")
        check_call(libc.syscall(446, fd, 0), "landlock_restrict")
    finally:
        os.close(fd)


def seccomp():
    """x86_64 filter: no namespace escape, host IPC or WSL AF_VSOCK bridge."""
    class Filter(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]
    class Program(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ushort), ("filters", ctypes.POINTER(Filter))]
    deny, allow = 0x00050000 | errno.EPERM, 0x7fff0000
    rows = [(0x20,0,0,4), (0x15,1,0,0xc000003e), (0x06,0,0,0x80000000),
            (0x20,0,0,0), (0x35,0,1,0x40000000), (0x06,0,0,0x80000000)]
    for number in [53,90,91,92,93,94,101,126,132,133,155,161,165,166,169,188,189,190,197,198,199,
                   235,246,260,261,268,272,280,298,303,304,308,310,311,321,323,425,426,427,428,429,430,431,432,433,452]:
        rows += [(0x15,0,1,number),(0x06,0,0,deny)]
    # clone3 cannot be inspected by classic BPF: force libc's clone fallback.
    rows += [(0x15,0,1,435),(0x06,0,0,0x00050000 | errno.ENOSYS)]
    # clone() may create threads/processes, but never a new namespace.
    rows += [(0x15,0,4,56),(0x20,0,0,16),(0x45,0,1,0x7e020000),(0x06,0,0,deny),(0x20,0,0,0)]
    rows += [(0x15,0,5,41),(0x20,0,0,16),(0x15,2,0,socket.AF_INET),
             (0x15,1,0,socket.AF_INET6),(0x06,0,0,deny),(0x06,0,0,allow),(0x06,0,0,allow)]
    array = (Filter * len(rows))(*(Filter(*row) for row in rows))
    program = Program(len(rows),array)
    libc = ctypes.CDLL(None,use_errno=True)
    check_call(libc.prctl(38,1,0,0,0),"no_new_privs")
    check_call(libc.prctl(22,2,ctypes.byref(program)),"seccomp_filter")


def drop_capabilities():
    libc = ctypes.CDLL(None,use_errno=True)
    for cap in range(41):
        check_call(libc.prctl(24,cap,0,0,0),"capability_bounding_drop")
    class Header(ctypes.Structure):
        _fields_=[("version",ctypes.c_uint32),("pid",ctypes.c_int32)]
    class Data(ctypes.Structure):
        _fields_=[("effective",ctypes.c_uint32),("permitted",ctypes.c_uint32),("inheritable",ctypes.c_uint32)]
    check_call(libc.capset(ctypes.byref(Header(0x20080522,0)),(Data*2)()),"capset_clear")


def child(policy_path, expected_sha, envelope_path=None, envelope_sha=None):
    # Never perform mounts or broad signal delivery in the caller's PID domain.
    if os.getpid() != 1 or os.getuid() != 0:
        raise RuntimeError("fresh_user_and_PID_namespace_required")
    if sha(policy_path) != expected_sha:
        raise ValueError("policy_changed_before_child")
    policy = json.loads(Path(policy_path).read_bytes())
    if Path(policy_path).read_bytes()!=policy_bytes(policy):raise ValueError("child_policy_bytes_not_canonical")
    validate(policy)
    production=policy.get("purpose")=="stage0.5-production-v4"
    context=None
    if production:
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from stage_0_5_native_capsule_v4 import verify_envelope
        if envelope_path is None:raise ValueError("production_envelope_missing")
        context=verify_envelope(policy,envelope_path,envelope_sha)
        context.update(source_files=policy["binding"]["source_files"],accepted_build=policy["binding"]["accepted_build"])
    cg = Path("/sys/fs/cgroup") / Path("/proc/self/cgroup").read_text().strip().split(":",2)[2].lstrip("/")
    cgroup = {n:(cg/n).read_text().strip() for n in ["memory.max","memory.swap.max","pids.max","cpu.max"]}
    if cgroup != {"memory.max":str(policy["memory_bytes"]),"memory.swap.max":"0","pids.max":str(policy["tasks"]),"cpu.max":"100000 100000"}:
        raise RuntimeError("cgroup_readback_mismatch")
    scratch, archive = Path(policy["scratch"]),Path(policy["archive"])
    scratch.mkdir(); archive.mkdir()
    # Mounts exist only in this new mount namespace, never alter host mounts.
    mount("tmpfs",scratch,"tmpfs",2|4|8,"size="+str(policy["output_bytes"])+",nr_inodes=4096,mode=0700")
    for name, source in policy["inputs"].items():
        target = scratch / name
        target.touch(exist_ok=False)
        mount(source,target,flags=4096)
        mount(None,target,flags=4096|32|1|2|4|8)
    if production:
        context["output_filesystem_capacity_bytes"]=os.statvfs(scratch).f_blocks*os.statvfs(scratch).f_frsize
        context_path=scratch/"broker_context.json"
        with context_path.open("xb") as f:f.write(policy_bytes(context))
        mount(str(context_path),context_path,flags=4096)
        mount(None,context_path,flags=4096|32|1|2|4|8)
    # TraCI can use only isolated loopback; there are no host NICs/routes.
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        import fcntl
        fcntl.ioctl(s,0x8914,struct.pack("16sH14s",b"lo",1,b""))
    termination = []
    def terminate_descendants(signum, frame):
        termination.append(signum)
        try: os.kill(-1,signal.SIGKILL)
        except ProcessLookupError: pass
    signal.signal(signal.SIGTERM,terminate_descendants)
    child_pid = os.fork()
    if child_pid == 0:
        try:
            os.chdir(scratch)
            os.environ.clear()
            os.environ.update(PATH="/usr/bin",HOME=str(scratch),TMPDIR=str(scratch),PYTHONNOUSERSITE="1",PYTHONDONTWRITEBYTECODE="1")
            allowed_env={"PATH","SUMO_HOME","LD_LIBRARY_PATH","OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS","LANG","LC_ALL"}
            if not set(policy.get("environment",{}))<=allowed_env:raise ValueError("unapproved_native_environment_key")
            os.environ.update(policy.get("environment",{}))
            os.closerange(3,65536)
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            resource.setrlimit(resource.RLIMIT_FSIZE,(policy["output_bytes"],policy["output_bytes"]))
            landlock(policy); drop_capabilities(); seccomp()
            os.execv(policy["argv"][0],policy["argv"])
        except BaseException as error:
            print("ISOLATION_CHILD_ERROR="+repr(error),file=sys.stderr,flush=True)
            import traceback
            traceback.print_exc()
            os._exit(125)
    _, status = os.waitpid(child_pid,0)
    # Namespace PID1 owns all descendants; terminate leftovers before archiving.
    try: os.kill(-1,signal.SIGKILL)
    except ProcessLookupError: pass
    while True:
        try:os.waitpid(-1,0)
        except ChildProcessError:break
    preserved = {}
    total = 0
    for p in scratch.rglob("*"):
        if p.name in policy["inputs"] and p.parent == scratch:
            continue
        if p.is_symlink():raise ValueError("unexpected_output_symlink")
        if p.is_dir():
            (archive/p.relative_to(scratch)).mkdir(parents=True,exist_ok=True)
            continue
        if p.is_symlink() or not p.is_file():
            raise ValueError("unexpected_output_type")
        relative = p.relative_to(scratch)
        total += p.stat().st_size
        if total > policy["output_bytes"]:
            raise ValueError("output_budget_exceeded")
        target = archive / relative
        target.parent.mkdir(parents=True,exist_ok=True)
        with p.open("rb") as source, target.open("xb") as sink:
            shutil.copyfileobj(source,sink)
        preserved[str(relative)] = sha(target)
    record = dict(kind="OS_enforced",backend="linux-userns",policy_sha256=expected_sha,cgroup=cgroup,
                  namespaces={n:os.readlink("/proc/self/ns/"+n) for n in ["user","mnt","pid","net","ipc"]},
                  payload_exit_code=os.waitstatus_to_exitcode(status),artifact_sha256=preserved,
                  termination_signals=termination,
                  kernel_counters={n:(cg/n).read_text().strip() for n in ["memory.events","pids.events","cpu.stat"]},
                  remaining_pids=[int(p.name) for p in Path("/proc").iterdir() if p.name.isdigit() and int(p.name)!=1],
                  output_bytes=total,scope="This exact Linux capsule; not Windows native isolation")
    record["descendants_reaped"]=not record["remaining_pids"]
    if production:
        for name,data in [("executed_policy.json",policy_bytes(policy)),
                          ("capability_record.json",Path(policy["binding"]["capability_record_path"]).read_bytes())]:
            with (archive/name).open("xb") as handle:handle.write(data)
            preserved[name]=sha(archive/name)
        record.update(proposal_sha256=context["proposal_sha256"],run_id=context["run_id"],task_id=context["task_id"],
            input_sha256=context["input_sha256"],source_sha256=context["source_sha256"],
            runtime_manifest_sha256=context["runtime_manifest_sha256"],broker_context_sha256=sha(scratch/"broker_context.json"),
            guard_sha256=sha(__file__),input_mounts={n:next(r for r in Path("/proc/self/mountinfo").read_text().splitlines() if r.split()[4]==str(scratch/n)) for n in policy["inputs"]})
    with (archive/"isolation_runtime.json").open("x") as handle:
        json.dump(record,handle,sort_keys=True)
    print("ISOLATION_RUNTIME="+json.dumps(record,sort_keys=True),flush=True)
    return record["payload_exit_code"]


if __name__ == "__main__":
    if len(sys.argv) not in [4,7] or sys.argv[1] != "--child" or (len(sys.argv)==7 and sys.argv[4]!="--envelope"):
        raise SystemExit("Only exact child-broker invocation is supported")
    raise SystemExit(child(sys.argv[2],sys.argv[3],*(sys.argv[5:7] if len(sys.argv)==7 else [])))
