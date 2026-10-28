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
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_0_5_native_capsule_v4 import canonical,sha,require,authorization_reasons,verify_receipt,SCHEMA,SMOKE_SCHEMA,SMOKE_TASK,TASK,safe_relative


# This contract is deliberately separate from the generic route-factor
# validator.  It is enabled only by an exact Round2 Task1 proposal marker and
# therefore cannot broaden any other admission path.
ROUND2_TASK1_EXPERIMENT = "AAD-S0.5-ROUND2-TASK1"
ROUND2_TASK1_CANDIDATE = "AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1"
ROUND2_TASK1_BASE_RUN = "WEEK_0750_B00_IC1_s20261201_A03"
ROUND2_TASK1_TARGET_VTYPES = tuple(f"B_het_c{i}_passenger" for i in range(5))
ROUND2_TASK1_BASE_INPUTS = {
    "network.net.xml": "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03/network.net.xml",
    "routes.rou.xml": "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03/routes.rou.xml",
    "run.sumocfg": "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03/run.sumocfg",
}
ROUND2_TASK1_CANDIDATE_INPUTS = {
    "network.net.xml": "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/network.net.xml",
    "routes.rou.xml": "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/routes.rou.xml",
    "run.sumocfg": "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/run.sumocfg",
}
ROUND2_TASK1_INPUT_SHA256 = {
    "network.net.xml": "d69c79c4c2303125e696d86b5907cbd1e043f21971dde4c4903eb3ccf84dbdcf",
    "routes.rou.xml": "a4c78db55984cc8c320b06ec2e257bdf6d4902c0dfdf015348157e30cdb80e79",
    "run.sumocfg": "c55b242f09b6a86527852bf686f06f3347abc44aa1c16c199c51935ce93dc6c6",
}
ROUND2_TASK1_BASE_SHA256 = {
    "network.net.xml": "d69c79c4c2303125e696d86b5907cbd1e043f21971dde4c4903eb3ccf84dbdcf",
    "routes.rou.xml": "b6df8d9ce52b56fac50899cc2e6d1329c7858325aae0f0c86c76d77f796a7574",
    "run.sumocfg": "c55b242f09b6a86527852bf686f06f3347abc44aa1c16c199c51935ce93dc6c6",
}


def _round2_task1_route_contract(base_bytes, candidate_bytes):
    """Validate the exact five-vType minGap contrast, without generic factors."""
    base = ET.fromstring(base_bytes)
    candidate = ET.fromstring(candidate_bytes)
    require(base.tag == candidate.tag and base.attrib == candidate.attrib,
            "round2_minGap_route_root_changed")
    base_children = list(base)
    candidate_children = list(candidate)
    require(len(base_children) == len(candidate_children), "round2_minGap_route_count_changed")
    base_types = {n.get("id"): n for n in base.findall("vType")}
    candidate_types = {n.get("id"): n for n in candidate.findall("vType")}
    require(set(base_types) == set(candidate_types), "round2_minGap_vtype_identity_changed")
    require(set(ROUND2_TASK1_TARGET_VTYPES) <= set(base_types), "round2_minGap_target_vtype_missing")
    changes = []
    for ident, old in base_types.items():
        new = candidate_types[ident]
        require(list(old) == list(new), "round2_minGap_vtype_nested_content_changed")
        old_attrs, new_attrs = dict(old.attrib), dict(new.attrib)
        changed = {k for k in set(old_attrs) | set(new_attrs) if old_attrs.get(k) != new_attrs.get(k)}
        if ident in ROUND2_TASK1_TARGET_VTYPES:
            require(changed == {"minGap"}, "round2_minGap_target_scope_changed:" + ident)
            require(old_attrs.get("minGap") == "2.5" and new_attrs.get("minGap") == "1.0",
                    "round2_minGap_value_changed:" + ident)
            changes.append(ident)
        else:
            require(not changed, "round2_minGap_non_target_vtype_changed:" + ident)
    # Preserve vehicle/route order and every attribute byte-for-attribute.
    for old, new in zip(base_children, candidate_children):
        if old.tag == "vType":
            continue
        require(old.tag == new.tag and old.attrib == new.attrib and
                [ET.tostring(c) for c in old] == [ET.tostring(c) for c in new],
                "round2_minGap_vehicle_or_route_changed")
    require(sorted(changes) == sorted(ROUND2_TASK1_TARGET_VTYPES),
            "round2_minGap_changed_vtype_count")
    return dict(changed_vtypes=sorted(changes), only_attribute="minGap", before="2.5", after="1.0")


def validate_round2_task1_min_gap_candidate(root, proposal, run, base_run):
    """Task-specific admission contract; raises before reservation or launch."""
    root = Path(root).resolve()
    require(proposal.get("experiment_id") == ROUND2_TASK1_EXPERIMENT,
            "round2_minGap_wrong_experiment")
    require(proposal.get("candidate_id") == ROUND2_TASK1_CANDIDATE,
            "round2_minGap_wrong_candidate_id")
    require(proposal.get("round2_baseline_run_id") == ROUND2_TASK1_BASE_RUN,
            "round2_minGap_wrong_baseline_run")
    require(proposal.get("round2_factor") == dict(
        attribute="minGap", from_m=2.5, to_m=1.0,
        vtypes=list(ROUND2_TASK1_TARGET_VTYPES)), "round2_minGap_factor_definition_changed")
    require(proposal.get("task_id") == TASK and run.get("task_id") == TASK,
            "round2_minGap_wrong_task_id")
    require(run.get("id") == ROUND2_TASK1_CANDIDATE,
            "round2_minGap_wrong_run_id")
    require(run.get("input_files") == ROUND2_TASK1_CANDIDATE_INPUTS,
            "round2_minGap_candidate_input_paths_changed")
    require(run.get("paired_base_routes") == ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"],
            "round2_minGap_base_route_binding_changed")
    require(base_run.get("id") == ROUND2_TASK1_BASE_RUN,
            "round2_minGap_previous_base_id_changed")
    require(base_run.get("input_files") == ROUND2_TASK1_BASE_INPUTS,
            "round2_minGap_previous_base_inputs_changed")
    require(run.get("input_sha256") == {ROUND2_TASK1_CANDIDATE_INPUTS[k]: v
                                         for k, v in ROUND2_TASK1_INPUT_SHA256.items()},
            "round2_minGap_candidate_hash_binding_changed")
    require({v: sha(safe_relative(root, v)) for v in run["input_files"].values()} ==
            run["input_sha256"], "round2_minGap_candidate_input_hash_drift")
    require({v: sha(safe_relative(root, v)) for v in base_run["input_files"].values()} ==
            {v: ROUND2_TASK1_BASE_SHA256[k] for k, v in base_run["input_files"].items()},
            "round2_minGap_base_input_hash_drift")
    # These are the science-bearing fields that must remain identical to A03.
    locked = ["condition", "seed", "duration_s", "internal_step_s", "evaluation_elapsed_s",
              "common_support_references", "supply_target_lanes", "lane_speed_schedule",
              "single_attempt_limits"]
    for key in locked:
        require(run.get(key) == base_run.get(key), "round2_minGap_locked_field_changed:" + key)
    route_report = _round2_task1_route_contract(
        safe_relative(root, ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"]).read_bytes(),
        safe_relative(root, run["input_files"]["routes.rou.xml"]).read_bytes())
    approval_path = safe_relative(root, proposal.get("round2_approval_path"))
    require(sha(approval_path) == proposal.get("round2_approval_sha256"),
            "round2_minGap_approval_record_drift")
    approval = json.loads(approval_path.read_bytes())
    require(approval.get("experiment_id") == ROUND2_TASK1_EXPERIMENT and
            approval.get("candidate_id") == ROUND2_TASK1_CANDIDATE and
            approval.get("macro_rule") == "Rule A strict joint support" and
            approval.get("decision") == "Approved by researcher via request_user_input_async",
            "round2_minGap_approval_record_not_exact")
    return dict(status="Pass", candidate_id=ROUND2_TASK1_CANDIDATE,
                baseline_run_id=ROUND2_TASK1_BASE_RUN, route_contract=route_report,
                locked_fields=locked, candidate_input_sha256=ROUND2_TASK1_INPUT_SHA256,
                base_input_sha256=ROUND2_TASK1_BASE_SHA256,
                approval_sha256=proposal["round2_approval_sha256"])


def linux_preflight(proposal,policy):
    from stage_0_5_linux_runtime_v4 import check_runtime
    from stage_0_5_linux_isolation import validate
    runtime=json.loads(Path(proposal["runtime_manifest_path"]).read_bytes())
    require(sha(proposal["runtime_manifest_path"])==proposal["runtime_manifest_sha256"],"runtime_manifest_drift")
    check_runtime(runtime);validate(policy)
    if proposal.get("schema") == SCHEMA:
        require(policy.get("binding", {}).get("run_id") == proposal["runs"][0]["id"], "research_policy_run_binding")
        require(policy.get("binding", {}).get("accepted_build") is True,
                "research_policy_accepted_build_false")
        require(policy.get("binding", {}).get("source_sha256") == proposal["controller_source_sha256"],
                "research_policy_source_binding")
        require(policy.get("binding", {}).get("runtime_manifest_sha256") == proposal["runtime_manifest_sha256"],
                "research_policy_runtime_binding")
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


def verify_bound_research_policy(root, proposal, run_id):
    """Read and validate the policy mirror bound by one exact proposal.

    This function is deliberately side-effect free.  Callers use it before
    ledger reservation, attempt creation, envelope transfer, or process start.
    """
    root = Path(root).resolve()
    require(proposal.get("policy_binding_required") is True, "bound_policy_binding_required")
    name = proposal.get("capsule_policy_repo_path")
    require(isinstance(name, str), "bound_policy_path_missing")
    path = safe_relative(root, name)
    require(path.exists(), "bound_policy_missing")
    require(sha(path) == proposal.get("capsule_policy_sha256"), "bound_policy_hash_mismatch")
    policy = json.loads(path.read_bytes())
    binding = policy.get("binding", {})
    require(binding.get("accepted_build") is True, "research_policy_accepted_build_false")
    require(binding.get("source_sha256") == proposal.get("controller_source_sha256"), "research_policy_source_binding")
    require(binding.get("runtime_manifest_sha256") == proposal.get("runtime_manifest_sha256"), "research_policy_runtime_binding")
    require(binding.get("run_id") == run_id, "research_policy_run_binding")
    return dict(path=str(path), policy=policy, policy_sha256=sha(path))


def technical_preflight_v4(repo,proposal_path,run_id,*,inspect_runtime=True):
    root=Path(repo).resolve();path=Path(proposal_path)
    if not path.is_absolute():path=root/path
    p=json.loads(path.read_bytes());errors=[]
    try:
        require(p["schema"]==SCHEMA and p["task_id"]==TASK,"wrong_v4_proposal")
        require(len(p["runs"])==1 and p["runs"][0]["id"]==run_id,"exact_B00_run_required")
        run=p["runs"][0]
        # ENG-01: read the policy bound to this exact candidate before any
        # ledger reserve, attempt record, envelope write, or native launch.
        verify_bound_research_policy(root, p, run_id)
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
        previous=p["previous_proposal"]
        require(sha(safe_relative(root,previous["path"]))==previous["sha256"],"previous_candidate_drift")
        old=json.loads(safe_relative(root,previous["path"]).read_bytes())["runs"][0]
        if p.get("experiment_id") == ROUND2_TASK1_EXPERIMENT:
            p["round2_min_gap_validation"] = validate_round2_task1_min_gap_candidate(root, p, run, old)
        else:
            # Preserve the generic B00/R1 contract byte-for-byte for every
            # other proposal. The generic factor validator is unchanged.
            from stage_0_5_admission_v3 import factor_routes
            factor_routes(safe_relative(root,run["paired_base_routes"]).read_bytes(),
                          safe_relative(root,run["input_files"]["routes.rou.xml"]).read_bytes(),
                          ramp=run["factors"]["ramp"])
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
        require(software_extension_verified(root,software,p["source_sha256"],
                                            task_experiment=p.get("experiment_id")),
                "software_verification_binding")
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
    # Build acceptance is an engineering prerequisite checked above. It must
    # not be presented as a researcher decision or normal approval pending.
    pending=[reason for reason in authorization_reasons(p,{},sha(path),run_id)
             if reason!="capsule_build_not_accepted"]
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
            exit_code=controller["exit_code"],watchdog_failure=controller["watchdog_failure"],sealed_artifacts={n:sha(work/n) for n in ["fcd.xml","summary.xml","tripinfo.xml","identity_events.jsonl","identity_summary.json"]})
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
