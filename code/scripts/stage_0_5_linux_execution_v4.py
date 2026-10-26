"""External coordination and the single Linux broker launch path (no bare SUMO)."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_0_5_native_capsule_v4 import canonical,sha,require,authorization_reasons,verify_receipt,SCHEMA,SMOKE_SCHEMA,SMOKE_TASK,TASK,safe_relative


def linux_preflight(proposal,policy):
    from stage_0_5_linux_runtime_v4 import check_runtime
    from stage_0_5_linux_isolation import validate
    runtime=json.loads(Path(proposal["runtime_manifest_path"]).read_bytes())
    require(sha(proposal["runtime_manifest_path"])==proposal["runtime_manifest_sha256"],"runtime_manifest_drift")
    check_runtime(runtime);validate(policy)
    require(proposal["runtime"]==runtime,"proposal_runtime_manifest_mismatch")
    for name,expected in proposal["controller_source_sha256"].items():
        require(Path(name).name==name and sha(Path(__file__).resolve().parent/name)==expected,"Linux_driver_source_drift:"+name)
    require(sha(proposal["capsule_policy_path"])==proposal["capsule_policy_sha256"],"preflight_policy_drift")
    require(policy["binding"]["source_sha256"]==proposal["controller_source_sha256"],"preflight_controller_source_binding")
    require(proposal["native_environment"]==dict(policy["environment"],PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1"),"native_environment_policy_mismatch")
    require(len(proposal["runs"])==1,"single_run_policy_required")
    require({n:sha(path) for n,path in policy["inputs"].items()}==proposal["runs"][0]["capsule_input_sha256"],"preflight_exact_input_binding")
    origins={}
    mounts=Path("/proc/self/mountinfo").read_text().splitlines()
    for target,drive in [("/mnt/c","C:"),("/mnt/d","D:")]:
        rows=[r for r in mounts if r.split()[4]==target]
        require(len(rows)==1 and rows[0].split(" - ")[1].split()[1].upper().startswith(drive),"resource_volume_origin_missing")
        origins[drive]=dict(path=target,mountinfo=rows[0])
    limits=proposal["single_attempt_limits"]
    import psutil
    sample=dict(free_c_bytes=shutil.disk_usage("/mnt/c").free,free_d_bytes=shutil.disk_usage("/mnt/d").free,
        free_wsl_bytes=shutil.disk_usage("/home/shen/AAD").free,archive_free_bytes=shutil.disk_usage(policy["capsule"]).free,
        available_memory_bytes=psutil.virtual_memory().available,filesystem_origins=origins,wall_s=0,
        process_tree_rss_bytes=psutil.Process().memory_info().rss,task_output_bytes=0)
    from stage_0_5_research_ledger import resource_reason
    require(resource_reason(limits,sample,startup=True) is None,"resource_preflight_failed")
    require(sample["free_wsl_bytes"]>=limits["task_output_bytes"]+1024**3 and sample["archive_free_bytes"]>=limits["task_output_bytes"]+1024**3,"WSL_output_headroom_insufficient")
    return dict(runtime_files_verified=len(runtime["files"]),resources=sample,linux_runtime_verified=True)


def launch_linux(envelope_path,envelope_sha):
    from stage_0_5_linux_isolation import build_command
    from stage_0_5_native_capsule_v4 import verify_envelope
    require(sha(envelope_path)==envelope_sha,"coordinator_envelope_drift")
    envelope=json.loads(Path(envelope_path).read_bytes())
    proposal=json.loads(Path(envelope["proposal_path"]).read_bytes());policy_path=Path(proposal["capsule_policy_path"])
    policy=json.loads(policy_path.read_bytes())
    verify_envelope(policy,envelope_path,envelope_sha)
    preflight=linux_preflight(proposal,policy)
    capsule=Path(policy["capsule"])
    # Exclusive attempt record forbids restart/retry even after a failed launch.
    with (capsule/"launch_attempt.json").open("xb") as f:f.write(canonical(dict(envelope_sha256=envelope_sha,preflight=preflight))+b"\n")
    argv=build_command(policy_path,policy,envelope_path=envelope_path)
    result=None;started=time.monotonic()
    try:
        with (capsule/"broker.stdout").open("xb") as out,(capsule/"broker.stderr").open("xb") as err:
            result=subprocess.run(argv,cwd="/home/shen/AAD",stdout=out,stderr=err,timeout=policy["wall_s"]+30)
        if result.returncode!=0:raise RuntimeError("capsule_native_nonzero:"+str(result.returncode))
        accepted=verify_receipt(capsule/"archive",proposal,envelope["proposal_sha256"],proposal["capsule_policy_sha256"])
        accepted.update(outer_elapsed_s=time.monotonic()-started,preflight=preflight)
        with (capsule/"engineering_acceptance.json").open("xb") as f:f.write(canonical(accepted)+b"\n")
        print(json.dumps(dict(status="Pass",capsule=str(capsule),acceptance=accepted)),flush=True)
        return accepted
    except BaseException as error:
        unit="aad-stage05-"+sha(policy_path)[:24]
        cleanup=subprocess.run(["/usr/bin/systemctl","--user","stop",unit],capture_output=True)
        failure=dict(error=repr(error),traceback=traceback.format_exc(),cleanup_exit_code=cleanup.returncode,
            cleanup_stderr=cleanup.stderr.decode(errors="replace"),elapsed_s=time.monotonic()-started,
            process_exit_code=None if result is None else result.returncode,automatic_retry=False)
        with (capsule/"coordinator_failure.json").open("xb") as f:f.write(canonical(failure)+b"\n")
        raise


def wsl_command(proposal,args):
    return ["wsl.exe","-d",proposal["linux_distribution"],"--cd","/home/shen/AAD","--exec",
            proposal["runtime"]["python_executable"],"-I","-B",proposal["linux_driver"]]+args


def inspect_linux(proposal,expected_sha):
    argv=wsl_command(proposal,["preflight",proposal["linux_proposal_path"]])
    result=subprocess.run(argv,capture_output=True,timeout=120)
    require(result.returncode==0,"Linux_technical_preflight_failed:"+result.stderr.decode(errors="replace")[-1000:])
    report=json.loads(result.stdout)
    require(report.get("proposal_sha256")==expected_sha,"Linux_proposal_copy_drift")
    return report


def technical_preflight_v4(repo,proposal_path,run_id,*,inspect_runtime=True):
    root=Path(repo).resolve();path=Path(proposal_path)
    if not path.is_absolute():path=root/path
    p=json.loads(path.read_bytes());errors=[]
    try:
        require(p["schema"]==SCHEMA and p["task_id"]==TASK,"wrong_v4_proposal")
        require(len(p["runs"])==1 and p["runs"][0]["id"]==run_id,"exact_B00_run_required")
        run=p["runs"][0]
        from stage_0_5_admission_v3 import MANDATORY_SOURCES,validate_config,factor_routes
        require(set(MANDATORY_SOURCES)<=set(p["source_sha256"]),"mandatory_execution_and_measurement_bindings_missing")
        from prepare_stage_0_5_linux_stage_v4 import SOURCES
        require(set(p["controller_source_sha256"])==set(SOURCES) and all(
            p["source_sha256"].get("code/scripts/"+n)==h for n,h in p["controller_source_sha256"].items()),"controller_source_closure_mismatch")
        require(bool(p["support_input_sha256"]) and bool(p["measurement_reference_sha256"]),"support_and_reference_bindings_required")
        for key in ["source_sha256","support_input_sha256"]:
            for n,h in p[key].items():require(sha(safe_relative(root,n))==h,"bound_file_drift:"+n)
        for n,h in run["input_sha256"].items():require(sha(safe_relative(root,n))==h,"scientific_input_drift")
        require(set(run["input_files"])=={"network.net.xml","routes.rou.xml","run.sumocfg"} and
            set(run["input_files"].values())==set(run["input_sha256"]),"inexact_scientific_input_map")
        require(run["capsule_input_sha256"]=={n:run["input_sha256"][v] for n,v in run["input_files"].items()},"capsule_and_research_input_mismatch")
        validate_config(safe_relative(root,run["input_files"]["run.sumocfg"]).read_bytes(),run)
        factor_routes(safe_relative(root,run["paired_base_routes"]).read_bytes(),safe_relative(root,run["input_files"]["routes.rou.xml"]).read_bytes(),ramp=run["factors"]["ramp"])
        previous=p["previous_proposal"]
        require(sha(safe_relative(root,previous["path"]))==previous["sha256"],"previous_candidate_drift")
        old=json.loads(safe_relative(root,previous["path"]).read_bytes())["runs"][0]
        require(all(run.get(k)==v for k,v in old.items() if k!="native_environment"),"B00_scientific_definition_changed")
        output=safe_relative(root,run["artifact_path"])
        require(not output.exists(),"research_output_already_exists")
        for n,h in p["measurement_reference_sha256"].items():require(sha(safe_relative(root,n))==h,"measurement_reference_drift")
        for name,key in [("plan_path","plan_sha256"),("budget_path","budget_sha256"),("software_validation_path","software_validation_sha256")]:
            require(sha(safe_relative(root,p[name]))==p[key],"technical_document_drift:"+name)
        budget=json.loads(safe_relative(root,p["budget_path"]).read_bytes())
        require(p["single_attempt_limits"]==run["single_attempt_limits"]==budget["single_attempt_limits"],"single_attempt_budget_drift")
        require(budget["workers"]==1 and budget["automatic_retry"] is False and budget["maximum_new_trajectory_attempts"] is None,"budget_semantics_changed")
        require(output.is_relative_to(safe_relative(root,budget["output_root"])),"output_outside_task")
        require(p["environment"]["linux_runtime_manifest_sha256"]==p["runtime_manifest_sha256"],"Linux_environment_binding_missing")
        require(p["worktree_sha256"]==hashlib.sha256(canonical(p["source_sha256"])).hexdigest(),"source_closure_digest_drift")
        software=json.loads((root/p["software_validation_path"]).read_bytes())
        from stage_0_5_isolation_admission import software_extension_verified
        require(software_extension_verified(root,software,p["source_sha256"]),"software_verification_binding")
        proof=json.loads((root/p["isolation"]["report_path"]).read_bytes())
        require(sha(root/p["isolation"]["report_path"])==p["isolation"]["report_sha256"],"integration_certificate_drift")
        require(proof["accepted_for_new_task"] is True and proof["input_and_test_resource_scope_accepted"] is True,"integration_not_accepted")
        require(proof["controller_source_sha256"]==p["controller_source_sha256"] and proof["runtime_manifest_sha256"]==p["runtime_manifest_sha256"],"production_build_certificate_mismatch")
        smoke=json.loads((root/proof["smoke_proposal_path"]).read_bytes())
        require(sha(root/proof["smoke_proposal_path"])==proof["smoke_proposal_sha256"],"smoke_proposal_drift")
        verify_receipt(root/proof["smoke_archive_path"],smoke,proof["smoke_proposal_sha256"],smoke["capsule_policy_sha256"])
        require(smoke["controller_source_sha256"]==p["controller_source_sha256"] and smoke["runtime_manifest_sha256"]==p["runtime_manifest_sha256"],"smoke_not_current_production_build")
        from stage_0_5_isolation_admission import runtime_reasons
        errors.extend(runtime_reasons(p,dict(controller_receipt=json.loads((root/proof["smoke_archive_path"]/"controller_receipt.json").read_bytes()))))
        require(p["isolation"]["accepted_for_new_task"] is True,"new_task_OS_isolation_unaccepted")
        linux=inspect_linux(p,sha(path)) if inspect_runtime else None
        if linux is None:errors.append("live_Linux_runtime_and_resource_check_required")
    except (ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
        errors.append(type(error).__name__+":"+str(error))
    pending=authorization_reasons(p,{},sha(path),run_id)
    return dict(task_id=TASK,run_id=run_id,proposal_sha256=sha(path),technical_errors=errors,authorization_pending=pending,
        ready=not errors,status="READY_FOR_RESEARCHER_APPROVAL" if not errors else "BLOCKED_ENGINEERING")


def execute_research(adapter,proposal_path,approval,run_id):
    """Future exact-authorized B00 path; never called by engineering preparation."""
    root=adapter.repo;path=root/proposal_path;p=json.loads(path.read_bytes());digest=sha(path)
    reasons=authorization_reasons(p,approval,digest,run_id)
    if reasons:adapter.refuse(reasons,run_id)
    report=technical_preflight_v4(root,path,run_id)
    if report["technical_errors"]:adapter.refuse(report["technical_errors"],run_id)
    return _execute_authorized(adapter,p,proposal_path,approval,run_id)


def _execute_authorized(adapter,p,proposal_path,approval,run_id):
    """Coordinate one isolated run, seal outputs, call the existing measurer/ledger."""
    from stage_0_5_execution_v2 import measure_completed_capsule,artifacts,native_resource_probe,NativeBackend
    from stage_0_5_isolation_v2 import Scope
    root=adapter.repo;run=p["runs"][0]
    host_resources=native_resource_probe(NativeBackend())()
    adapter.ledger.reserve(proposal_path,approval,run_id,host_resources)
    work=root/run["artifact_path"];scope=Scope(root,p["source_sha256"],work)
    envelope=dict(proposal_path=p["linux_proposal_path"],proposal_sha256=sha(root/proposal_path),run_id=run_id,approval=approval)
    try:
        # Only the envelope is written by the coordinator after admission. The
        # fixed Linux stage/policy already contains the exact read-only inputs.
        write_code="from pathlib import Path;import base64,sys; p=Path(sys.argv[1]);p.open('xb').write(base64.b64decode(sys.stdin.buffer.read()))"
        target=p["linux_envelope_path"];payload=canonical(envelope)
        command=["wsl.exe","-d",p["linux_distribution"],"--cd","/home/shen/AAD","--exec",p["runtime"]["python_executable"],"-I","-B","-c",write_code,target]
        result=subprocess.run(command,input=base64.b64encode(payload),capture_output=True);require(result.returncode==0,"envelope_transfer_failed")
        adapter.ledger.transition(run_id,"running")
        result=subprocess.run(wsl_command(p,["launch",target,hashlib.sha256(payload).hexdigest()]),capture_output=True,timeout=p["single_attempt_limits"]["per_attempt_wall_s"]+60)
        scope.create(work/"coordinator.stdout",result.stdout);scope.create(work/"coordinator.stderr",result.stderr)
        # Return file listing only from this exact new capsule, then stream each
        # regular output separately; never buffer a research FCD in JSON/base64.
        archive=p["linux_archive_path"]
        listing="import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print(json.dumps([str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and not q.is_symlink()]))"
        base=["wsl.exe","-d",p["linux_distribution"],"--cd","/home/shen/AAD","--exec",p["runtime"]["python_executable"],"-I","-B"]
        listing_result=subprocess.run(base+["-c",listing,archive],capture_output=True);require(listing_result.returncode==0,"output_listing_failed")
        reader="import pathlib,sys,shutil; p=pathlib.Path(sys.argv[1]); n=pathlib.Path(sys.argv[2]); assert not n.is_absolute() and '..' not in n.parts; q=p/n; assert not q.is_symlink() and q.resolve().is_relative_to(p.resolve()); shutil.copyfileobj(q.open('rb'),sys.stdout.buffer)"
        for name in json.loads(listing_result.stdout):
            target_path=scope.check(safe_relative(work,name),writing=True);target_path.parent.mkdir(parents=True,exist_ok=True)
            with target_path.open("xb") as out:
                copied=subprocess.run(base+["-c",reader,archive,name],stdout=out,stderr=subprocess.PIPE)
            require(copied.returncode==0,"output_transfer_failed")
        for name,path in run["input_files"].items():scope.create(work/name,(root/path).read_bytes())
        acceptance=verify_receipt(work,p,sha(root/proposal_path),p["capsule_policy_sha256"])
        require(result.returncode==0,"native_process_failed")
        controller=json.loads((work/"controller_receipt.json").read_bytes());identity=json.loads((work/"identity_summary.json").read_bytes())
        runtime=dict(resource_samples=controller["resource_samples"],run_finished_wall_s=controller["resource_samples"][-1]["wall_s"],
            exit_code=controller["exit_code"],watchdog_failure=controller["watchdog_failure"],sealed_artifacts={n:sha(work/n) for n in ["fcd.xml","tripinfo.xml","identity_events.jsonl","identity_summary.json"]})
        receipt_sha=acceptance["receipt_sha256"]
        proof=dict(kind="OS_enforced",backend="linux-userns",binding_sha256=sha(root/proposal_path),transcript_sha256=receipt_sha,
            probes=acceptance["probes"])
        runtime["isolation"]=proof
        references={n:h for n,h in p["measurement_reference_sha256"].items()}
        scope.bindings.update({root/n:h for n,h in references.items()})
        context=dict(work=work,scope=scope,run=run,proposal=p,validated_inputs={n:(work/n).read_bytes() for n in run["input_files"]},
            resource_limits=p["single_attempt_limits"],runtime_evidence=runtime,binding_sha256=sha(root/proposal_path),
            native_enforcement_verified=acceptance["status"]=="Pass",isolation_transcript_sha256=[receipt_sha])
        hashes,size=artifacts(scope,work);resources=dict(wall_s=runtime["run_finished_wall_s"],process_tree_rss_bytes=max(s["process_tree_rss_bytes"] for s in controller["resource_samples"]),artifact_bytes=size)
        adapter.ledger.transition(run_id,"completed",resources=resources)
        checks=measure_completed_capsule(context,identity);scope.create(work/"measurement_acceptance.json",canonical(checks)+b"\n")
        hashes,size=artifacts(scope,work)
        from stage_0_5_research_ledger import CHECKS
        passed=all(checks.get(k) is True for k in CHECKS)
        adapter.ledger.transition(run_id,"measurement_accepted" if passed else "measurement_rejected",checks=checks,
            reason=None if passed else "evidence_measurement_rejected",artifact_sha256=hashes,resources=resources)
        return adapter.ledger.snapshot()
    except BaseException as error:
        state=adapter.ledger.snapshot()["attempts"][run_id]["status"]
        if state in {"reserved","running"}:
            adapter.ledger.transition(run_id,"failed",reason=repr(error),resources=dict(wall_s=None,process_tree_rss_bytes=None,artifact_bytes=None))
        elif state=="completed":
            from stage_0_5_research_ledger import CHECKS
            adapter.ledger.transition(run_id,"measurement_rejected",reason=repr(error),checks=dict.fromkeys(CHECKS,False))
        raise


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=["launch","preflight"]);parser.add_argument("path");parser.add_argument("sha",nargs="?")
    a=parser.parse_args()
    if a.mode=="launch":launch_linux(a.path,a.sha)
    else:
        p=json.loads(Path(a.path).read_bytes());policy=json.loads(Path(p["capsule_policy_path"]).read_bytes())
        print(json.dumps(dict(linux_preflight(p,policy),proposal_sha256=sha(a.path))))
