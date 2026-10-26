"""Harmless Linux capsule verification, synthetic files only; never calls SUMO.

Run only in a newly created staging child of /home/shen/AAD/code/tmp. This is
independent native OS evidence, not a scientific run or an isolation acceptance.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_0_5_linux_isolation import build_command,sha


PAYLOAD = r'''
import ctypes,errno,json,os,socket,subprocess,sys
from pathlib import Path
base=Path(sys.argv[1]); mode=sys.argv[2]; result={}
def denied(name,call):
    try:
        value=call()
        if hasattr(value,"close"): value.close()
        result[name]=dict(denied=False)
    except OSError as e: result[name]=dict(denied=True,errno=e.errno)
if mode=="basic":
    result["allowed_read"]=(Path("input.txt").read_text()=="synthetic only")
    Path("allowed.txt").write_text("capsule output")
    result["allowed_write"]=True
    denied("readonly_input",lambda:Path("input.txt").open("w"))
    denied("forbidden_read",lambda:(base/"forbidden.txt").open())
    denied("forbidden_write",lambda:(base/"outside_write.txt").open("w"))
    denied("forbidden_metadata_write",lambda:os.chmod(base/"forbidden.txt",0o600))
    denied("unregistered_exec",lambda:subprocess.run(["/usr/bin/true"],check=True))
    denied("output_symlink",lambda:os.symlink(base/"forbidden.txt","escape"))
    denied("host_unix_socket",lambda:socket.socket(socket.AF_UNIX))
    denied("vsock",lambda:socket.socket(40))
    denied("namespace_escape",lambda:ctypes.CDLL(None,use_errno=True).syscall(272,0x10000000) == 0 and None or (_ for _ in ()).throw(PermissionError(ctypes.get_errno(),"unshare")))
    c=subprocess.run([sys.executable,"-I","-c","from pathlib import Path; import sys;\ntry: Path(sys.argv[1]).read_bytes();sys.exit(9)\nexcept PermissionError:sys.exit(0)",str(base/"forbidden.txt")],check=False)
    result["child_inherits_denial"]=(c.returncode==0)
    with socket.socket() as server:
        server.bind(("127.0.0.1",0));server.listen(1)
        with socket.socket() as client:
            client.connect(server.getsockname());conn,_=server.accept();conn.close()
        result["isolated_loopback_works"]=True
    denied("host_loopback",lambda:socket.create_connection(("127.0.0.1",int(sys.argv[3])),timeout=.2))
    denied("external_network",lambda:socket.create_connection(("192.0.2.1",9),timeout=.2))
    result["namespace_ids"]={n:os.readlink("/proc/self/ns/"+n) for n in ["user","mnt","pid","net","ipc"]}
    result["status"]={r.split(":")[0]:r.split(":",1)[1].strip() for r in Path("/proc/self/status").read_text().splitlines() if r.startswith(("CapEff:","NoNewPrivs:","Seccomp:"))}
elif mode=="output":
    denied("per_file_limit",lambda:Path("too_big").write_bytes(b"x"*(1024*1024+1)))
    Path("too_big").unlink()
    denied("aggregate_tmpfs_limit",lambda:[Path(str(i)).write_bytes(b"x"*65536) for i in range(40)])
elif mode=="pids":
    children=[]
    try:
        for i in range(16): children.append(subprocess.Popen([sys.executable,"-I","-c","import time;time.sleep(5)"]))
    except OSError as e: result["pids_limit"]=dict(denied=True,errno=e.errno,spawned=len(children))
    finally:
        for child in children: child.terminate()
        for child in children: child.wait()
elif mode=="memory":
    import time
    Path("memory_started").write_text("before allocation")
    memory=bytearray(256*1024*1024)
    time.sleep(5)
elif mode=="cpu":
    code="import time; end=time.monotonic()+.6\nwhile time.monotonic()<end: pass"
    children=[subprocess.Popen([sys.executable,"-I","-c",code]) for _ in range(2)]
    for child in children: child.wait()
    result["busy_children_completed"]=all(c.returncode==0 for c in children)
elif mode=="timeout":
    import time
    Path("timeout_started").write_text("before sleep")
    time.sleep(10)
print("PAYLOAD_PROBE="+json.dumps(result,sort_keys=True),flush=True)
'''


def runtime_files():
    # Static ELF inspection; readelf/ldconfig never execute the inspected binary.
    mapping={}
    listing=subprocess.check_output(["/sbin/ldconfig","-p"],text=True)
    for line in listing.splitlines():
        m=re.match(r"\s*(\S+).*=> (\S+)",line)
        if m:mapping[m[1]]=Path(m[2]).resolve()
    stdlib=Path("/usr/lib/python3.12")
    files={str(p):sha(p) for p in stdlib.rglob("*") if p.is_file() and not p.is_symlink()}
    queue=[Path(sys.executable).resolve()]+[Path(n) for n in files if n.endswith(".so")]
    inspected=set()
    while queue:
        path=queue.pop()
        if path in inspected:continue
        inspected.add(path);files[str(path)]=sha(path)
        data=subprocess.check_output(["/usr/bin/readelf","-d",str(path)],text=True,stderr=subprocess.DEVNULL)
        for needed in re.findall(r"\(NEEDED\).*\[(.+?)\]",data):
            if needed not in mapping:raise ValueError("unresolved_ELF_dependency:"+needed)
            queue.append(mapping[needed])
    loader=Path("/lib64/ld-linux-x86-64.so.2").resolve();files[str(loader)]=sha(loader)
    return files,[str(stdlib)]+[n for n in files if not Path(n).is_relative_to(stdlib)]


def main():
    base=Path(__file__).resolve().parent
    if not base.is_relative_to(Path("/home/shen/AAD/code/tmp")):
        raise ValueError("probe_staging_directory_required")
    output=base/"probe_results";output.mkdir(exist_ok=False)
    (base/"input.txt").write_text("synthetic only")
    (base/"forbidden.txt").write_text("synthetic forbidden marker")
    payload=base/"payload.py";payload.write_text(PAYLOAD)
    files,readonly=runtime_files()
    guard=base/"stage_0_5_linux_isolation.py"
    for p in [guard,payload,base/"input.txt"]:files[str(p)]=sha(p)
    readonly += [str(guard),str(payload)]
    host_ns={n:os.readlink("/proc/self/ns/"+n) for n in ["user","mnt","pid","net","ipc"]}
    record=dict(scope="Actual Linux kernel probes with synthetic files and harmless Python only",working_directory=os.getcwd(),
                staging_directory=str(base),host_namespaces=host_ns,commands=[],SUMO_launches=0,real_TraCI_connections=0,new_trajectories=0)
    with socket.socket() as sentinel:
        sentinel.bind(("127.0.0.1",0));sentinel.listen(1)
        for mode in ["basic","output","pids","memory","cpu","timeout"]:
            capsule=base/("capsule_"+mode);capsule.mkdir(exist_ok=False)
            policy=dict(capsule=str(capsule),scratch=str(capsule/"scratch"),archive=str(capsule/"archive"),
                argv=[str(Path(sys.executable).resolve()),"-I",str(payload),str(base),mode,str(sentinel.getsockname()[1])],
                executables=[str(Path(sys.executable).resolve()),str(Path("/lib64/ld-linux-x86-64.so.2").resolve())],file_sha256=files,
                readonly_paths=readonly,kernel_readonly=["/proc"],inputs={"input.txt":str(base/"input.txt")},
                memory_bytes=64*1024**2 if mode=="memory" else 256*1024**2,output_bytes=1024**2,tasks=8,wall_s=2 if mode=="timeout" else 20)
            policy_path=capsule/"policy.json";policy_path.write_text(json.dumps(policy,sort_keys=True,separators=(",",":")))
            argv=build_command(policy_path,policy)
            started=time.monotonic()
            result=subprocess.run(argv,cwd="/home/shen/AAD",capture_output=True,timeout=30)
            (output/(mode+".stdout")).write_bytes(result.stdout);(output/(mode+".stderr")).write_bytes(result.stderr)
            entry=dict(mode=mode,command=argv,exit_code=result.returncode,elapsed_s=time.monotonic()-started,policy_sha256=sha(policy_path),
                       stdout_sha256=sha(output/(mode+".stdout")),stderr_sha256=sha(output/(mode+".stderr")))
            for line in result.stdout.decode(errors="replace").splitlines():
                for tag,key in [("PAYLOAD_PROBE=","observations"),("ISOLATION_RUNTIME=","runtime")]:
                    if line.startswith(tag):entry[key]=json.loads(line[len(tag):])
            record["commands"].append(entry)
            print(json.dumps(entry,sort_keys=True),flush=True)
    record["runtime_files_sha256"]=files
    record["guard_sha256"]=sha(guard)
    record["installed_versions"]=subprocess.check_output(["dpkg-query","-W","sumo","sumo-tools","python3","libseccomp2"],text=True)
    record["linux_sumo_sha256"]=sha("/usr/bin/sumo")
    record["os_release"]=Path("/etc/os-release").read_text()
    record["kernel"]=os.uname().release
    records={r["mode"]:r for r in record["commands"]}
    basic=records["basic"].get("observations",{})
    negatives=["readonly_input","forbidden_read","forbidden_write","forbidden_metadata_write","unregistered_exec",
               "output_symlink","host_unix_socket","vsock","namespace_escape","host_loopback","external_network"]
    def counter(mode,name,key):
        data=records[mode].get("runtime",{}).get("kernel_counters",{}).get(name,"")
        return int(dict(line.split() for line in data.splitlines()).get(key,"0"))
    record["checks"]={
        "positive_file_controls":basic.get("allowed_read") is True and basic.get("allowed_write") is True,
        "all_negative_access_probes":all(basic.get(n,{}).get("denied") is True for n in negatives),
        "children_confined":basic.get("child_inherits_denial") is True,
        "loopback_only":basic.get("isolated_loopback_works") is True and basic.get("host_loopback",{}).get("denied") is True,
        "all_namespaces_changed":all(basic.get("namespace_ids",{}).get(n)!=v for n,v in host_ns.items()) and bool(basic.get("namespace_ids")),
        "kernel_security_status":basic.get("status")==dict(CapEff="0000000000000000",NoNewPrivs="1",Seccomp="2"),
        "output_enforced":all(records["output"].get("observations",{}).get(n,{}).get("denied") is True for n in ["per_file_limit","aggregate_tmpfs_limit"]),
        "pids_enforced":records["pids"].get("observations",{}).get("pids_limit",{}).get("errno")==11 and counter("pids","pids.events","max")>0,
        "memory_enforced":records["memory"].get("runtime",{}).get("payload_exit_code")==-9 and counter("memory","memory.events","oom_kill")>0,
        "CPU_enforced":counter("cpu","cpu.stat","nr_throttled")>0,
        "timeout_enforced":records["timeout"]["elapsed_s"]<5 and bool(records["timeout"].get("runtime",{}).get("termination_signals")),
        "failure_outputs_preserved":all(n+"_started" in records[n].get("runtime",{}).get("artifact_sha256",{}) for n in ["memory","timeout"]),
        "successful_controls":all(records[n]["exit_code"]==0 for n in ["basic","output","pids","cpu"]),
        "expected_resource_failures":all(records[n]["exit_code"]!=0 for n in ["memory","timeout"]),
    }
    record["status"]="Verified for exact harmless Linux capsules" if all(record["checks"].values()) else "Failed; not accepted"
    (output/"record.json").write_text(json.dumps(record,indent=2,sort_keys=True))
    print("PROBE_RECORD="+str(output/"record.json"),flush=True)
    return 0 if all(record["checks"].values()) else 1


if __name__=="__main__":raise SystemExit(main())
