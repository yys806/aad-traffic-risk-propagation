"""Pure-Git validation of B1.2-N closure; never opens local simulation states."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

def verify(root,repo_root=None,source_ref="HEAD"):
    root=Path(root).resolve()
    def path(name):
        p=(root/name).resolve()
        if p.parent!=root:raise ValueError("portable path escape")
        return p
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(n):return json.loads(path(n).read_text(encoding="utf-8"))
    actual={p.name for p in root.iterdir() if p.is_file()}-{"manifest.json","SHA256SUMS"}
    manifest=read("manifest.json");names=[e["path"] for e in manifest["files"]]
    if set(names)!=actual or len(names)!=len(set(names)):raise ValueError("manifest coverage")
    for e in manifest["files"]:
        if sha(path(e["path"]))!=e["sha256"] or path(e["path"]).stat().st_size>256*1024:raise ValueError("manifest SHA/size")
    sums={}
    for line in path("SHA256SUMS").read_text().splitlines():
        digest,name=line.split("  ",1)
        if name in sums or sha(path(name))!=digest:raise ValueError("SHA256SUMS mismatch")
        sums[name]=digest
    if set(sums)!=actual|{"manifest.json"}:raise ValueError("SHA256SUMS coverage")
    plan=read("experiment_plan.json");plan_sha=sha(path("experiment_plan.json"))
    if path("PLAN_SHA256").read_text().split()[0]!=plan_sha or sha(path("micro_plan.json"))!=plan_sha:raise ValueError("plan SHA")
    if [r["kind"] for r in plan["runs"]]!=["N1","N2","N3"] or any(r["duration_s"]>30 or r["seed"]!=20261019 for r in plan["runs"]):raise ValueError("micro scope")
    if plan["main_matrix_allowed"] or plan["P2_calculated"]:raise ValueError("plan scope")
    bundle=read("engineering_input_bundle.json")["files"]
    required={n for n in plan["frozen_files"] if n.startswith("inputs/") and Path(n).suffix in [".xml",".sumocfg"]}
    if set(bundle)!=required:raise ValueError("input bundle coverage")
    for name,e in bundle.items():
        if ".." in Path(name).parts or ":" in name or "\\" in name or not name.startswith("inputs/"):raise ValueError("input path")
        raw=gzip.decompress(base64.b64decode(e["gzip_base64"],validate=True))
        if len(raw)!=e["bytes"] or hashlib.sha256(raw).hexdigest()!=e["sha256"] or e["sha256"]!=plan["frozen_files"][name]:raise ValueError("input SHA")
    for name,expected in plan["frozen_files"].items():
        if "/" not in name and name in actual and sha(path(name))!=expected:raise ValueError("frozen policy SHA")
    audit=read("audit.json")
    fixed=dict(gate="pending_simulation_sample",scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,
               reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,integration_allowed=False,
               main_matrix_allowed=False,main_matrix_attempts=0,micro_runs=3,integration_attempts=0,old_C_states_read=False,
               validation_window_rows_materialised=0,positive_snap_runtime="Not Observed")
    if any(audit.get(k)!=v for k,v in fixed.items()):raise ValueError("scientific/execution boundary")
    checkpoint=read("micro_checkpoint.json");candidate=read("numerical_admission_candidate.json")
    if checkpoint["integration_allowed"] or checkpoint["observed_positive_snap"]!=0 or checkpoint["observed_exact_after"]!=1 or candidate["integration_allowed"] or candidate["main_matrix_allowed"] or candidate["exact_tolerance_m"]!=1e-6:raise ValueError("missing positive-snap gate")
    if sha(path("micro_checkpoint.json"))!=candidate["micro_checkpoint_sha256"]:raise ValueError("candidate checkpoint binding")
    task=read("task_ledger.json");runs=task["runs"];rm=read("run_manifest.json")
    if not task["closed"] or len(runs)!=5 or [r["status"] for r in runs[3:]]!=["not_attempted"]*2 or task["global_stop"] is not None:raise ValueError("closed unattempted C/D")
    if any(r["status"]!="completed_with_diagnostic_warning" for r in runs[:3]) or rm["runs"]!=runs or rm["main_matrix_runs"]!=0 or rm["C_D_plans_frozen"]:raise ValueError("run ledger consistency")
    for k in ["C","D"]:
        s=read(f"integration_{k}_audit.json")
        if s["status"]!="Not Attempted" or s["plan_frozen"] or s["observed_s"] is not None or s["numerical_coverage"] is not None:raise ValueError("invented C/D evidence")
    n=read("numerical_branch_coverage.json");classes=n["classifications"]
    if sum(e["count"] for e in classes.values())!=n["all_adjacent_edges"]:raise ValueError("coverage sum")
    exact=sum(classes[k]["count"] for k in ["Exact Without Postprocessing","Exact After Verified Postprocessing"])
    if n["exact_checked"]!=exact or n["exact_passed"]!=exact or n["tolerance_m"]!=1e-6 or n["max_abs_residual_m"]>1e-6:raise ValueError("exact numerical accounting")
    for c,e in classes.items():
        if e["count"]!=sum(v["classifications"][c]["count"] for v in n["per_fixture"].values()):raise ValueError("per-fixture coverage")
        if abs(e["fraction"]-e["count"]/n["all_adjacent_edges"])>1e-14:raise ValueError("coverage fraction")
    if n["bounded_is_exact"] or n["unresolved_is_exact"] or n["branch_counts"].get("positive_snap",0)!=0:raise ValueError("classification promotion")
    for v in n["per_fixture"].values():
        for e in v["examples"].values():
            if e["classification"] in ["Bounded Consistency Only","Near-Zero Context Unresolved","Not Evaluable"] and (e["residual_m"] is not None or e["exact_pass"] is not None):raise ValueError("pseudo-exact residual")
    h=read("historical_status_preservation.json")
    if h["B1_C"]!="completed_with_engineering_blocker" or h["B1_D"]!="not_attempted" or h["B12_MAIN_MATRIX_ALLOWED"] or h["B12_main_runs"] or h["historical_results_modified"] or h["historical_reclassification"]:raise ValueError("history preservation")
    source=read("near_zero_source_contract.json")
    if source["pinned_commit"]!="fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3" or source["generic_stop_context_identifiable"] or source["installed_binary_modified"]:raise ValueError("source domain")
    verified=0
    if repo_root is not None:
        binding=read("git_source_binding_audit.json");checked=set()
        for e in binding["files"]:
            relative=e["path"]
            if not relative.startswith("code/") or ".." in Path(relative).parts or ":" in relative:raise ValueError("source path")
            raw=subprocess.check_output(["git","show",(":" if source_ref=="INDEX" else source_ref+":")+relative],cwd=repo_root)
            if hashlib.sha256(raw).hexdigest()!=e["canonical_git_blob_sha256"]:raise ValueError("Git source SHA: "+relative)
            if e["byte_transform"]=="canonical LF to original CRLF":raw=raw.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")
            elif e["byte_transform"]!="none":raise ValueError("source transform")
            name="runtime/"+relative
            if hashlib.sha256(raw).hexdigest()!=e["frozen_sha256"] or e["frozen_sha256"]!=plan["frozen_files"][name]:raise ValueError("frozen source SHA")
            checked.add(name)
        for e in binding["generated_runtime"]:
            raw=base64.b64decode(e["base64"],validate=True);name=e["path"]
            if hashlib.sha256(raw).hexdigest()!=e["sha256"] or e["sha256"]!=plan["frozen_files"][name]:raise ValueError("bootstrap SHA")
            checked.add(name)
        if checked!={n for n in plan["frozen_files"] if n.startswith("runtime/code/")}:raise ValueError("source coverage")
        verified=len(checked)
    result=dict(passed=True,files=len(actual),bundled_inputs=len(bundle),frozen_source_files_verified=verified,main_matrix_attempts=0,integration_allowed=False,plan_sha256=plan_sha)
    print(json.dumps(result));return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("path",type=Path);p.add_argument("--repo-root",type=Path);p.add_argument("--source-ref",default="HEAD")
    a=p.parse_args();verify(a.path,a.repo_root,a.source_ref)
