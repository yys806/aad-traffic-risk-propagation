"""Pure-Git B1.2 verification; never discovers/opens local traffic artifacts."""
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
    def read(name):return json.loads(path(name).read_text(encoding="utf-8"))
    manifest=read("manifest.json");entries=manifest["files"];names=[e["path"] for e in entries]
    actual={p.name for p in root.iterdir() if p.is_file()}-{"manifest.json","SHA256SUMS"}
    if len(set(names))!=len(names) or set(names)!=actual:raise ValueError("manifest coverage")
    for e in entries:
        if path(e["path"]).stat().st_size>256*1024 or sha(path(e["path"]))!=e["sha256"]:raise ValueError("manifest SHA/size")
    sums={}
    for line in path("SHA256SUMS").read_text().splitlines():
        digest,name=line.split("  ",1)
        if name in sums or sha(path(name))!=digest:raise ValueError("SHA256SUMS mismatch")
        sums[name]=digest
    if set(sums)!=actual|{"manifest.json"}:raise ValueError("SHA256SUMS coverage")
    plan=read("experiment_plan.json");digest=sha(path("experiment_plan.json"))
    if path("PLAN_SHA256").read_text().split()[0]!=digest or sha(path("integration_plan.json"))!=digest:raise ValueError("plan SHA")
    if len(plan["runs"])!=2 or any(r["duration_s"]>60 for r in plan["runs"]):raise ValueError("fixture budget")
    bundle=read("engineering_input_bundle.json")["files"]
    required={n for n in plan["frozen_files"] if n.startswith("inputs/") and Path(n).suffix in [".xml",".sumocfg",".json"]}
    if set(bundle)!=required:raise ValueError("input bundle coverage")
    for name,e in bundle.items():
        if not name.startswith("inputs/") or ".." in Path(name).parts or ":" in name or "\\" in name:raise ValueError("input path")
        raw=gzip.decompress(base64.b64decode(e["gzip_base64"],validate=True))
        if len(raw)!=e["bytes"] or hashlib.sha256(raw).hexdigest()!=e["sha256"] or e["sha256"]!=plan["frozen_files"][name]:raise ValueError("input bundle SHA")
    for name,expected in plan["frozen_files"].items():
        if "/" not in name and name in actual and sha(path(name))!=expected:raise ValueError("frozen policy SHA")
    audit=read("audit.json")
    expected=dict(B1_2_MAIN_MATRIX_ALLOWED=False,gate="pending_simulation_sample",scientific_claim_eligible=False,
                  ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,
                  main_matrix_attempts=0,integration_attempts=1,old_C_states_read=False,
                  B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised="Unknown")
    if any(audit.get(k)!=v for k,v in expected.items()):raise ValueError("scientific/execution boundary")
    ledger=read("execution_ledger.json")
    if not ledger["closed"] or ledger["main_plan_frozen"] or any(r["status"]!="not_attempted" for r in ledger["main_matrix"]) or len(ledger["main_matrix"])!=8:raise ValueError("unattempted matrix")
    if ledger["integration"][0]["status"]!="completed_with_engineering_blocker" or ledger["integration"][1]["status"]!="not_attempted":raise ValueError("stop sequence")
    n=read("numerical_branch_coverage.json");cc=n["classifications"]
    if sum(c["count"] for c in cc.values())!=n["all_adjacent_edges"]:raise ValueError("numerical coverage counts")
    if n["exact_checked"]!=sum(cc[k]["count"] for k in ["Exact Observable","Exact Reconstructable Under Verified Conditions"]):raise ValueError("exact classification count")
    if n["exact_passed"]!=n["exact_checked"] or n["tolerance_m"]!=1e-6 or n["blockers"]!={"candidate_terminal_speed_inconsistent":1}:raise ValueError("numerical blocker preservation")
    example=n["examples"]["candidate_terminal_speed_inconsistent"]
    if example["classification"]!="Not Evaluable" or example["candidate"] is not None or example["residual_m"] is not None:raise ValueError("anomaly falsely accepted")
    if read("observability_integration_audit.json")["B1_2_MAIN_MATRIX_ALLOWED"] or read("research_conflict.json")["Status"]!="Awaiting Researcher Decision":raise ValueError("admission/conflict")
    h=read("historical_status_preservation.json")
    if h["B1_C"]!="completed_with_engineering_blocker" or h["B1_D"]!="not_attempted" or h["historical_results_modified"] or h["historical_reclassification"]:raise ValueError("historical boundary")
    verified=0
    if repo_root is not None:
        binding=read("git_source_binding_audit.json");checked=set()
        for e in binding["files"]:
            relative=e["path"]
            if not relative.startswith("code/") or ".." in Path(relative).parts or ":" in relative:raise ValueError("source path")
            ref=(":" if source_ref=="INDEX" else source_ref+":")+relative
            raw=subprocess.check_output(["git","show",ref],cwd=repo_root)
            if hashlib.sha256(raw).hexdigest()!=e["canonical_git_blob_sha256"]:raise ValueError("canonical source SHA: "+relative)
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
    result=dict(passed=True,files=len(entries),bundled_inputs=len(bundle),frozen_source_files_verified=verified,
                main_matrix_attempts=0,main_matrix_allowed=False,plan_sha256=digest)
    print(json.dumps(result));return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("path",type=Path);p.add_argument("--repo-root",type=Path);p.add_argument("--source-ref",default="HEAD")
    a=p.parse_args();verify(a.path,a.repo_root,a.source_ref)
