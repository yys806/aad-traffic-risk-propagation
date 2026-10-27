"""Production controller inside the kernel capsule, used by B00 and smoke.

The scientific measurer stays independent; no risk algorithm is implemented here.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import shutil
import socket
import subprocess
import sys
import time
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_0_5_native_capsule_v4 import canonical,sha,require,verify_live_context,SMOKE_SCHEMA,smoke_inputs,sumo_version_output_matches
from stage_0_5_execution_v2 import NativeBackend,EventJournal,attach_FCD_observations,run_observation_loop,ResourceSupervisor,ResourceWatchdog
from stage_0_5_identity_observation import IdentityObserver
from stage_0_5_input_fidelity import inventory
from stage_0_5_isolation_v2 import Scope


def linux_resource_probe(backend,context):
    import psutil
    started=time.monotonic()
    mount_lines=Path("/proc/self/mountinfo").read_text().splitlines()
    origins={}
    for target,drive in [("/mnt/c","C:"),("/mnt/d","D:")]:
        matches=[r for r in mount_lines if r.split()[4]==target]
        require(len(matches)==1 and matches[0].split(" - ")[1].split()[0]=="9p" and
                matches[0].split(" - ")[1].split()[1].upper().startswith(drive),"Windows_volume_mount_unverified:"+drive)
        origins[drive]=dict(path=target,mountinfo=matches[0])
    cg=verify_live_context(context)
    owner_pid=os.getpid()
    def observe():
        current=psutil.Process(owner_pid)
        rss=sum(p.memory_info().rss for p in [current]+current.children(recursive=True) if p.is_running())
        wsl=shutil.disk_usage("/home/shen/AAD");output=os.statvfs(Path.cwd())
        require(output.f_blocks*output.f_frsize==context["output_filesystem_capacity_bytes"],"capsule_filesystem_capacity_mismatch")
        sample=dict(wall_s=time.monotonic()-started,process_tree_rss_bytes=rss,
            free_c_bytes=shutil.disk_usage("/mnt/c").free,free_d_bytes=shutil.disk_usage("/mnt/d").free,
            free_wsl_bytes=wsl.free,capsule_fs_free_bytes=output.f_bavail*output.f_frsize,
            capsule_fs_capacity_bytes=output.f_blocks*output.f_frsize,available_memory_bytes=psutil.virtual_memory().available,
            cgroup_memory_current_bytes=int((cg/"memory.current").read_text()),task_output_bytes=0,
            filesystem_origins=origins,WSL_filesystem="/home/shen/AAD",output_filesystem=str(Path.cwd()))
        require(wsl.free>=context["resource_limits"]["task_output_bytes"]+1024**3,"WSL_archive_headroom_insufficient")
        require(sample["capsule_fs_free_bytes"]>0,"capsule_output_filesystem_full")
        return sample
    return observe


class ProcessResourceWatchdog:
    """Sampler in the same capsule, independent of the controller's GIL.

    Every sample is a fresh full probe. Nothing is interpolated or cached.
    The controller checks child health at each step; kernel limits also remain
    active while a controller call blocks. The broker reaps both processes.
    """
    def __init__(self,supervisor,path,*,interval_s=.1):
        self.supervisor,self.path,self.interval=supervisor,Path(path),interval_s
        self.pid=self.stop_fd=self.status=None
        self.failure=None
        self.closed=False

    def start(self):
        require(self.pid is None and not self.path.exists(),"exclusive_resource_sampler_required")
        read_fd,write_fd=os.pipe()
        owner=os.getpid()
        self.pid=os.fork()
        if self.pid==0:
            os.close(write_fd)
            status=0
            try:
                with self.path.open("xb",buffering=0) as log:
                    while os.getppid()==owner:
                        try:
                            sample=self.supervisor.observe()
                        except BaseException as error:
                            log.write(canonical(dict(error=type(error).__name__+":"+str(error)))+b"\n")
                            raise
                        log.write(canonical(dict(sample=sample))+b"\n")
                        if select.select([read_fd],[],[],self.interval)[0]:
                            os.read(read_fd,1)
                            break
            except BaseException:
                status=1
            finally:
                os.close(read_fd)
            os._exit(status)
        os.close(read_fd)
        self.stop_fd=write_fd

    def observe(self,**unused):
        if self.status is None:
            pid,status=os.waitpid(self.pid,os.WNOHANG)
            if pid:
                self.status=status
                self.failure="resource_sampler_exited_before_stop:"+str(os.waitstatus_to_exitcode(status))
        if self.failure:
            raise RuntimeError(self.failure)
        return self.supervisor.last

    def close(self,*,raise_on_failure=True):
        if not self.closed:
            self.closed=True
            if self.stop_fd is not None:
                try:os.write(self.stop_fd,b"x")
                except BrokenPipeError:pass
                os.close(self.stop_fd)
                self.stop_fd=None
            deadline=time.monotonic()+2
            while self.status is None and time.monotonic()<deadline:
                pid,status=os.waitpid(self.pid,os.WNOHANG)
                if pid:self.status=status
                else:time.sleep(.01)
            if self.status is None:
                # Only the exact child created by this instance is targeted.
                os.kill(self.pid,signal.SIGKILL)
                _,self.status=os.waitpid(self.pid,0)
                self.failure="resource_sampler_stop_timeout"
            if os.waitstatus_to_exitcode(self.status)!=0:
                self.failure=self.failure or "resource_sampler_failed"
            try:
                records=[json.loads(line) for line in self.path.read_bytes().splitlines()]
                errors=[r["error"] for r in records if "error" in r]
                if errors:self.failure=";".join(errors)
                samples=[r["sample"] for r in records if "sample" in r]
                require(bool(samples),"independent_resource_samples_missing")
                self.supervisor.samples.extend(samples)
                self.supervisor.last=samples[-1]
            except BaseException as error:
                self.failure=self.failure or type(error).__name__+":"+str(error)
        if raise_on_failure and self.failure:
            raise RuntimeError(self.failure)


def main():
    work=Path.cwd()
    context=json.loads((work/"broker_context.json").read_bytes())
    verify_live_context(context)
    run=context["run"]
    inputs={n:(work/n).read_bytes() for n in context["input_sha256"]}
    if context["schema"]==SMOKE_SCHEMA:smoke_inputs(run,inputs)
    _,vehicles,_,_,_=inventory(inputs["routes.rou.xml"])
    observer=IdentityObserver([dict(id=k,depart_s=float(v.get("depart"))) for k,v in vehicles.items()])
    scope=Scope(work.parent,{context["runtime"]["sumo_binary"]:context["runtime"]["sumo_sha256"]},work,native_allowed=True)
    backend=NativeBackend();supervisor=None;watchdog=None
    receipt=dict(proposal_sha256=context["proposal_sha256"],policy_sha256=context["policy_sha256"],
        controller_namespaces={n:os.readlink("/proc/self/ns/"+n) for n in ["user","mnt","pid","net","ipc"]},
        sumo_binary_sha256=sha(context["runtime"]["sumo_binary"]),controls=[],resource_samples=[],exit_code=None)
    def security_status(pid):
        values=dict(r.split(":",1) for r in Path("/proc/"+str(pid)+"/status").read_text().splitlines() if ":" in r)
        return {k:values.get(k,"").strip() for k in ["NoNewPrivs","Seccomp","CapEff"]}
    receipt["controller_security"]=security_status("self")
    receipt["network_interfaces"]=[r.split(":",1)[0].strip() for r in Path("/proc/net/dev").read_text().splitlines()[2:]]
    log=(work/"native_console.log").open("xb")
    try:
        # Same confined executable and exact binary used for both version and run.
        version=subprocess.run([context["runtime"]["sumo_binary"],"--version"],capture_output=True,env=context["native_environment"],timeout=10)
        require(version.returncode==0,"SUMO_version_process_failed")
        receipt["sumo_version_output"]=version.stdout.decode("utf-8",errors="strict")
        require(sumo_version_output_matches(receipt["sumo_version_output"],context["runtime"]["sumo_release"]),"SUMO_release_mismatch")
        with socket.socket() as s:s.bind(("127.0.0.1",0));port=s.getsockname()[1]
        native=[context["runtime"]["sumo_binary"],"-c",str(work/"run.sumocfg"),"--remote-port",str(port),"--no-step-log","true"]
        scope.commands=[native]
        context.update(scope=scope,work=work,validated_inputs=inputs,native_command=native,native_environment=context["native_environment"],
            native_log=log,port=port,traci_tools_root=context["runtime"]["traci_tools_root"],
            expected_runtime_version=[context["runtime"]["traci_protocol"],"SUMO "+context["runtime"]["sumo_release"]],
            native_capsule_context=context.copy())
        supervisor=ResourceSupervisor(context["resource_limits"],scope,work,linux_resource_probe(backend,context))
        supervisor.observe(startup=True)
        watchdog=ProcessResourceWatchdog(supervisor,work/"resource_samples.jsonl",interval_s=context["resource_limits"]["supervision_poll_s"]/5)
        watchdog.start()
        receipt.update(resource_supervision_mode="independent_process",resource_sampler_pid=watchdog.pid)
        journal=EventJournal(scope,work/"identity_events.jsonl")
        frame=backend.start(context);observer.ingest(frame);journal.append(frame)
        import traci
        receipt.update(getVersion=list(backend.connection.getVersion()),traci_source_sha256=sha(traci.__file__),
            sumo_namespaces={n:os.readlink("/proc/"+str(backend.process.pid)+"/ns/"+n) for n in receipt["controller_namespaces"]},
            sumo_security=security_status(backend.process.pid))
        run_observation_loop(context,backend,observer,journal,watchdog,synthetic=False)
        receipt["controls"]=[f["controls"] for f in observer.frames[1:]]
        backend.finish();receipt["exit_code"]=backend.exit_code
        attach_FCD_observations(observer,work/"fcd.xml",heartbeat=watchdog.observe)
        observer.observe_tripinfo((work/"tripinfo.xml").read_bytes())
        scope.create(work/"identity_summary.json",canonical(observer.finish())+b"\n")
        watchdog.close()
        supervisor.observe()
    except BaseException as error:
        receipt["error"]=type(error).__name__+":"+str(error)
        (work/"controller_error.txt").write_text(traceback.format_exc())
        try:backend.stop()
        except Exception as cleanup:receipt["cleanup_error"]=repr(cleanup)
        scope.create(work/"interrupted_identity_summary.json",canonical(observer.finish(interrupted=True))+b"\n")
        raise
    finally:
        if watchdog is not None:
            watchdog.close(raise_on_failure=False)
        if supervisor is not None:receipt["resource_samples"]=supervisor.samples
        receipt["watchdog_failure"]=None if watchdog is None else watchdog.failure
        log.close()
        with (work/"controller_receipt.json").open("xb") as f:f.write(canonical(receipt)+b"\n")


if __name__=="__main__":main()
