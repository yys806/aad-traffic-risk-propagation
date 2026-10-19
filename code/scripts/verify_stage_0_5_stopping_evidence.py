"""Verify one B1.1 portable package; no traffic files or implicit local lookup."""
import argparse
import base64
import gzip
import hashlib
import json
import subprocess
from pathlib import Path


def verify_sources(root,repo_root,frozen):
    """Read canonical Git code blobs, not a CRLF-converted checkout or data."""
    binding=json.loads((Path(root)/"git_source_binding_audit.json").read_text(encoding="utf-8"))
    checked=set()
    for entry in binding["files"]:
        relative=entry["path"]
        if not relative.startswith("code/") or ".." in Path(relative).parts or ":" in relative:
            raise ValueError("invalid Git source path")
        raw=subprocess.check_output(["git","show","HEAD:"+relative],cwd=repo_root)
        if hashlib.sha256(raw).hexdigest()!=entry["canonical_git_blob_sha256"]:raise ValueError("canonical source SHA mismatch")
        if entry["byte_transform"]=="canonical LF to original CRLF":raw=raw.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")
        elif entry["byte_transform"]!="none":raise ValueError("unknown source transform")
        name="runtime/"+relative
        if hashlib.sha256(raw).hexdigest()!=entry["frozen_sha256"] or entry["frozen_sha256"]!=frozen[name]:
            raise ValueError("frozen source SHA mismatch")
        checked.add(name)
    for entry in binding["generated_runtime"]:
        raw=base64.b64decode(entry["base64"],validate=True);name=entry["path"]
        if hashlib.sha256(raw).hexdigest()!=entry["sha256"] or entry["sha256"]!=frozen[name]:raise ValueError("generated bootstrap SHA mismatch")
        checked.add(name)
    if checked!={n for n in frozen if n.startswith("runtime/code/")}:raise ValueError("runtime source coverage mismatch")
    return len(checked)


def verify(root,repo_root=None):
    root=Path(root).resolve()
    def path(name):
        p=(root/name).resolve()
        if p.parent!=root:raise ValueError("portable path escape")
        return p
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(name):return json.loads(path(name).read_text(encoding="utf-8"))
    manifest=read("manifest.json");entries=manifest["files"]
    names=[f["path"] for f in entries]
    actual={p.name for p in root.iterdir() if p.is_file()}-{"manifest.json","SHA256SUMS"}
    if len(set(names))!=len(names) or set(names)!=actual:raise ValueError("manifest coverage mismatch")
    for entry in entries:
        if sha(path(entry["path"]))!=entry["sha256"]:raise ValueError("manifest SHA mismatch")
    sums={}
    for line in path("SHA256SUMS").read_text().splitlines():
        digest,name=line.split("  ",1)
        if name in sums or sha(path(name))!=digest:raise ValueError("SHA256SUMS mismatch")
        sums[name]=digest
    if set(sums)!=set(names)|{"manifest.json"}:raise ValueError("SHA256SUMS coverage mismatch")
    plan=read("experiment_plan.json");digest=sha(path("experiment_plan.json"))
    if path("PLAN_SHA256").read_text().split()[0]!=digest:raise ValueError("plan SHA mismatch")
    for name,expected in plan["frozen_files"].items():
        if "/" not in name and name in actual and sha(path(name))!=expected:
            raise ValueError("frozen protocol SHA mismatch")
    bundle=read("micro_input_bundle.json")["files"]
    required={n for n in plan["frozen_files"] if n.startswith("inputs/") and Path(n).suffix in [".xml",".sumocfg"]}
    if set(bundle)!=required:raise ValueError("frozen input bundle coverage mismatch")
    for name,entry in bundle.items():
        raw=gzip.decompress(base64.b64decode(entry["gzip_base64"],validate=True))
        if len(raw)!=entry["bytes"] or hashlib.sha256(raw).hexdigest()!=entry["sha256"] or entry["sha256"]!=plan["frozen_files"][name]:
            raise ValueError("frozen input bundle SHA mismatch")
    for run in plan["runs"]:
        required_run=list(run.get("input_sha256",{})) or [run["config"],run["network"],run["demand"]]
        if any(n not in bundle for n in required_run):raise ValueError("run input missing")
        if run["duration_s"]>60:raise ValueError("micro duration exceeded")
    ledger=read("execution_ledger.json")
    if len(plan["runs"])>4 or not ledger["closed"] or [r["run_id"] for r in ledger["runs"]]!=[r["run_id"] for r in plan["runs"]]:
        raise ValueError("micro execution plan mismatch")
    audit=read("audit.json")
    expected=dict(stage_0_5_gate="pending_simulation_sample",scientific_claim_eligible=False,
        ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,
        stage_1_1_allowed=False,numerical_exact_stopping="Pending Numerical Equivalence",
        B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised="Unknown",old_C_states_read=False)
    if any(audit.get(k)!=v for k,v in expected.items()):raise ValueError("scientific boundary mismatch")
    h=read("historical_b1_status_preservation.json")
    if h["C"]["status"]!="completed_with_engineering_blocker" or h["D"]["status"]!="not_attempted" or h["historical_reclassification"] or h["old_C_state_read"] or set(h["C"]["blockers"])!={"runtime_settings","persistent_external_demand_without_documented_spillback"}:
        raise ValueError("historical boundary mismatch")
    result=dict(passed=True,manifest_files=len(entries),bundled_inputs=len(bundle),plan_sha256=digest,
        no_local_traffic_required=True,exact_stopping_still_pending=True)
    if repo_root is not None:result["verified_frozen_runtime_files"]=verify_sources(root,repo_root,plan["frozen_files"])
    print(json.dumps(result));return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("path",type=Path);p.add_argument("--repo-root",type=Path)
    args=p.parse_args();verify(args.path,args.repo_root)
