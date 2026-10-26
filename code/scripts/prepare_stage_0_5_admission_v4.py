"""Prepare a new Linux admission candidate without launching B00 or a capsule.

The Linux policy mode copies only the three already-bound candidate XML inputs.
The candidate mode consumes an exact engineering collection and software record.
Neither mode creates an authorization or an accepted production certificate.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))

from stage_0_5_native_capsule_v4 import canonical,sha,require,SCHEMA,TASK
from prepare_stage_0_5_linux_stage_v4 import SOURCES,STAGE_PARENT,write

BASE="evidence/admission/AAD-0.5-READY-TO-ADMIT-V3"
PREVIOUS=BASE+"/candidate-v4/proposal.json"


def sources(root):
    old=json.loads((Path(root)/PREVIOUS).read_bytes())
    names=set(old["source_sha256"])|{"code/scripts/"+n for n in SOURCES}
    names.update("code/scripts/"+n+".py" for n in ["prepare_stage_0_5_admission_v4",
        "prepare_stage_0_5_linux_stage_v4","validate_stage_0_5_linux_v4"])
    names.add("code/tests/test_stage_0_5_native_capsule_v4.py")
    return {n:sha(Path(root)/n) for n in sorted(names)}


def linux_policy(root,stage):
    """Only static input/policy preparation; no broker or native invocation."""
    from stage_0_5_linux_runtime_v4 import check_runtime,make_policy
    root=Path(root);stage=Path(stage)
    require(stage.parent==STAGE_PARENT and stage.name.startswith("stage05_v4_"),"authorized_stage_required")
    require(not any(p.is_symlink() for p in [stage,*stage.parents]),"symlink_stage_forbidden")
    old=json.loads((root/PREVIOUS).read_bytes());run=copy.deepcopy(old["runs"][0])
    budget=json.loads((root/old["budget_path"]).read_bytes())
    run["single_attempt_limits"]=budget["single_attempt_limits"]
    runtime_path=stage/"runtime_manifest.json";runtime=json.loads(runtime_path.read_bytes());check_runtime(runtime)
    for n in SOURCES:require(sha(root/"code/scripts"/n)==sha(stage/n),"current_staging_source_required:"+n)
    inputs=stage/"research_inputs";inputs.mkdir(exist_ok=False)
    for name,relative in run["input_files"].items():
        require(sha(root/relative)==run["input_sha256"][relative],"scientific_input_drift")
        write(inputs/name,(root/relative).read_bytes())
    path,policy=make_policy(stage/"research_capsule",runtime,runtime_path,{n:str(stage/n) for n in SOURCES},
        {n:str(inputs/n) for n in run["input_files"]},run,accepted_build=False,
        capability_record=stage/"probe_results/record.json")
    binding=dict(capsule_policy_path=str(path),capsule_policy_sha256=sha(path),
        native_environment=dict(policy["environment"],PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1"),
        input_sha256={n:sha(inputs/n) for n in run["input_files"]},
        previous_proposal_sha256=sha(root/PREVIOUS),SUMO_launches=0,real_TraCI_connections=0,new_trajectories=0)
    write(stage/"research_policy_binding.json",binding)
    return binding


def prepare(root,collection,validation,destination):
    root=Path(root).resolve();collection=Path(collection);validation=Path(validation);folder=Path(destination)
    require(folder.parent==root/BASE and not folder.exists(),"new_immutable_candidate_required")
    for path in [collection,validation,folder]:require(path.is_relative_to(root),"candidate_artifact_outside_repository")
    captured=json.loads((collection/"collection.json").read_bytes())
    for n,row in captured["files"].items():require(sha(collection/n)==row["sha256"],"engineering_collection_drift:"+n)
    stage_record=json.loads((collection/"staging_record.json").read_bytes())
    current=sources(root);software=json.loads(validation.read_bytes())
    require(software["source_sha256"]==current,"current_software_source_binding_required")
    from stage_0_5_isolation_admission import software_extension_verified,probe_checks
    require(software_extension_verified(root,software,current),"current_software_validation_required")
    require(stage_record["source_sha256"]=={n:current["code/scripts/"+n] for n in SOURCES},"current_staging_source_required")
    runtime_path=collection/"runtime_manifest.json";runtime=json.loads(runtime_path.read_bytes())
    require(sha(runtime_path)==stage_record["runtime_manifest_sha256"],"staging_runtime_manifest_drift")
    probe_path=collection/"probe/record.json";probe=json.loads(probe_path.read_bytes())
    require(probe["guard_sha256"]==current["code/scripts/stage_0_5_linux_isolation.py"] and all(probe_checks(probe).values()),"current_probe_required")
    binding=json.loads((collection/"research_policy_binding.json").read_bytes())
    old=json.loads((root/PREVIOUS).read_bytes());p=copy.deepcopy(old);run=copy.deepcopy(old["runs"][0])
    require(binding["previous_proposal_sha256"]==sha(root/PREVIOUS),"previous_candidate_drift")
    run["native_environment"]=binding["native_environment"]
    run["capsule_input_sha256"]={n:run["input_sha256"][v] for n,v in run["input_files"].items()}
    require(run["capsule_input_sha256"]==binding["input_sha256"],"Linux_scientific_input_mismatch")
    budget=json.loads((root/p["budget_path"]).read_bytes());run["single_attempt_limits"]=budget["single_attempt_limits"]
    for key in ["linux_integration","runtime_dependency_manifest","runtime_dependency_manifest_sha256","tool_version_source"]:p.pop(key,None)
    # POSIX path strings must survive authoring on Windows unchanged.
    stage=probe["staging_directory"]
    relative=lambda path:Path(path).relative_to(root).as_posix()
    folder.mkdir(exist_ok=False)
    integration=dict(accepted_for_new_task=False,input_and_test_resource_scope_accepted=False,
        status="BLOCKED_ENGINEERING",reason="Current production smoke receipt not yet available or verified",
        controller_source_sha256=stage_record["source_sha256"],runtime_manifest_sha256=sha(runtime_path),
        smoke_proposal_path=relative(collection/"smoke_proposal.json"),smoke_proposal_sha256=sha(collection/"smoke_proposal.json"),
        smoke_archive_path=None,historical_incident="Not Accepted")
    write(folder/"integration_pending.json",integration)
    p.update(schema=SCHEMA,task_id=TASK,plan_version="candidate-v5-linux-v4-prepared",
        status="Proposed / BLOCKED_ENGINEERING",runs=[run],source_sha256=current,
        controller_source_sha256=stage_record["source_sha256"],runtime=runtime,
        runtime_manifest_path=stage+"/runtime_manifest.json",runtime_manifest_sha256=sha(runtime_path),
        native_binary=runtime["sumo_binary"],traci_tools_root=runtime["traci_tools_root"],
        native_runtime_version=[runtime["traci_protocol"],"SUMO "+runtime["sumo_release"]],
        native_environment=binding["native_environment"],external_file_sha256=runtime["files"],
        capsule_policy_path=binding["capsule_policy_path"],capsule_policy_sha256=binding["capsule_policy_sha256"],
        kernel_probe_sha256=sha(probe_path),single_attempt_limits=budget["single_attempt_limits"],
        linux_distribution="Ubuntu",linux_driver=stage+"/stage_0_5_linux_execution_v4.py",
        linux_proposal_path=stage+"/research_proposal.json",linux_envelope_path=stage+"/research_envelope.json",
        linux_archive_path=stage+"/research_capsule/archive",
        environment=dict(platform=runtime["OS_release"],python_version=runtime["python_version"],
            python_executable=runtime["python_executable"],python_executable_sha256=runtime["python_sha256"],
            packages=runtime["packages"],linux_runtime_manifest_sha256=sha(runtime_path)),
        previous_proposal=dict(path=PREVIOUS,sha256=sha(root/PREVIOUS),authorization_migrated=False),
        software_validation_path=relative(validation),software_validation_sha256=sha(validation),
        execution_allowed=False,researcher_confirmed=False,protocol_frozen=False,
        worktree_sha256=hashlib.sha256(canonical(current)).hexdigest())
    p["git_commit"]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    p["git_state"]=dict(observed_HEAD=p["git_commit"],branch="main",working_tree_dirty=True,
        semantics="Baseline SHA plus exact current source hashes; preparation includes uncommitted engineering fixes")
    p["isolation"]=dict(accepted_for_new_task=False,report_path=relative(folder/"integration_pending.json"),
        report_sha256=sha(folder/"integration_pending.json"),capability_evidence_path=relative(probe_path),
        capability_evidence_sha256=sha(probe_path),controller_capsule_policy=binding["capsule_policy_path"],
        controller_capsule_status="Prepared; current production receipt not verified",historical_incident="Not Accepted")
    p["support_input_sha256"].update({relative(probe_path):sha(probe_path)})
    write(folder/"proposal.json",p)
    from stage_0_5_linux_execution_v4 import technical_preflight_v4
    report=technical_preflight_v4(root,folder/"proposal.json",run["id"],inspect_runtime=False)
    require(report["technical_errors"]==["ValueError:integration_not_accepted"],"unexpected_candidate_defect:"+str(report))
    write(folder/"technical_preflight.json",report)
    write(folder/"admission_profile.json",dict(status=report["status"],execution_allowed=False,researcher_confirmed=False,
        protocol_frozen=False,accepted_for_new_task=False,native_launch_locked=True,historical_incident="Not Accepted",
        SUMO_launches=0,real_TraCI_connections=0,new_trajectories=0))
    write(folder/"manifest.json",dict(status=report["status"],proposal_sha256=sha(folder/"proposal.json"),
        files={q.name:sha(q) for q in folder.iterdir() if q.is_file()}))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=["linux-policy","candidate"])
    parser.add_argument("--repo-root",type=Path,required=True);parser.add_argument("--stage",type=Path)
    parser.add_argument("--collection",type=Path);parser.add_argument("--validation",type=Path);parser.add_argument("--destination",type=Path)
    a=parser.parse_args()
    result=linux_policy(a.repo_root,a.stage) if a.mode=="linux-policy" else prepare(a.repo_root,a.collection,a.validation,a.destination)
    print(json.dumps(result,ensure_ascii=False))
