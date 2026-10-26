"""Rebind existing B00 inputs to new isolation evidence; never launch a process."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from stage_0_5_admission_v3 import technical_preflight
from stage_0_5_execution_v2 import NativeBackend,native_resource_probe
from stage_0_5_isolation_v2 import sha
from stage_0_5_research_ledger import canonical

BASE="evidence/admission/AAD-0.5-READY-TO-ADMIT-V3"
AUDIT="docs/audits/stage_0_5_wsl_isolation_v1"


def sources(root):
    p=json.loads((root/BASE/"candidate-v2/proposal.json").read_bytes())
    names=set(p["source_sha256"])
    names.update("code/scripts/"+n+".py" for n in ["stage_0_5_linux_isolation","stage_0_5_isolation_admission","probe_stage_0_5_linux_isolation","prepare_stage_0_5_wsl_b00"])
    names.add("code/tests/test_stage_0_5_linux_isolation.py")
    return {name:sha(root/name) for name in sorted(names)}


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as f:f.write(value if isinstance(value,bytes) else canonical(value)+b"\n")


def prepare(root):
    folder=root/BASE/"candidate-v3"
    if folder.exists():raise FileExistsError("immutable_candidate_exists")
    old_path=root/BASE/"candidate-v2/proposal.json"
    old=json.loads(old_path.read_bytes());p=copy.deepcopy(old)
    validation=root/AUDIT/"validation_record.json"
    data=json.loads(validation.read_bytes())
    if data["source_sha256"]!=sources(root) or data["targeted"]["exit_code"]!=0:
        raise ValueError("current_targeted_validation_required")
    p.update(plan_version="candidate-v3-isolation-extension",status="Proposed / BLOCKED_ENGINEERING",
        source_sha256=sources(root),runs=[copy.deepcopy(old["runs"][0])],
        previous_proposal=dict(path=old_path.relative_to(root).as_posix(),sha256=sha(old_path),authorization_migrated=False))
    p["candidate_run_order"]=[p["runs"][0]["id"]]
    p["worktree_sha256"]=hashlib.sha256(canonical(p["source_sha256"])).hexdigest()
    p["software_validation_path"]=validation.relative_to(root).as_posix()
    p["software_validation_sha256"]=sha(validation)
    p["isolation"].update(report_path=AUDIT+"/provenance.json",report_sha256=sha(root/AUDIT/"provenance.json"),
        capability_evidence_path=AUDIT+"/probe/record.json",capability_evidence_sha256=sha(root/AUDIT/"probe/record.json"),
        capability_status="Verified for Linux harmless processes, not accepted for Windows SUMO1.26",
        controller_capsule_policy=None,controller_capsule_status="Blocked: no matching Linux1.26 runtime/controller binding",
        accepted_for_new_task=False)
    p["support_input_sha256"].update({AUDIT+"/probe/record.json":sha(root/AUDIT/"probe/record.json"),
        "docs/STAGE_0_5_WSL_ISOLATION_2026-10-26.md":sha(root/"docs/STAGE_0_5_WSL_ISOLATION_2026-10-26.md")})
    p["git_state"]=dict(observed_HEAD="00d19793502ccbd7cb9f1c5c508501c79631d3fb",branch="main",
        semantics="Isolation extension exact source hashes; final commit and Git-only review recorded after commit")
    write(folder/"proposal.json",p)
    resource=native_resource_probe(NativeBackend())()
    report=technical_preflight(root,folder/"proposal.json",p["runs"][0]["id"],resource_sample=resource)
    write(folder/"technical_preflight.json",report)
    write(folder/"admission_profile.json",dict(status=report["status"],proposal_sha256=sha(folder/"proposal.json"),
        execution_allowed=False,researcher_confirmed=False,protocol_frozen=False,accepted_for_new_task=False,
        native_launch_locked=True,historical_incident="Not Accepted",SUMO_launches=0,real_TraCI_connections=0,new_trajectories=0))
    write(folder/"manifest.json",dict(task_id=p["task_id"],status=report["status"],proposal_sha256=sha(folder/"proposal.json"),
        files={q.relative_to(folder).as_posix():sha(q) for q in folder.iterdir() if q.is_file()}))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    a=p.parse_args();print(json.dumps(prepare(a.repo_root.resolve()),ensure_ascii=False))
