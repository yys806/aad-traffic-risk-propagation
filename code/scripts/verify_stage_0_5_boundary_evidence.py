"""Verify only the selected B1 portable package, without any local traffic data."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path


def verify(root):
    root=Path(root).resolve()
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    for f in manifest["files"]:
        path=(root/f["path"]).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=f["sha256"]:
            raise ValueError("portable manifest binding mismatch")
    for line in (root/"SHA256SUMS").read_text().splitlines():
        digest,name=line.split("  ",1);path=(root/name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError("SHA256SUMS binding mismatch")
    plan=json.loads((root/"experiment_plan.json").read_text())
    digest=hashlib.sha256((root/"experiment_plan.json").read_bytes()).hexdigest()
    if (root/"PLAN_SHA256").read_text().split()[0]!=digest:raise ValueError("plan binding mismatch")
    bundle=json.loads((root/"engineering_input_bundle.json").read_text())["files"]
    for name,entry in bundle.items():
        data=gzip.decompress(base64.b64decode(entry["gzip_base64"]))
        if len(data)!=entry["bytes"] or hashlib.sha256(data).hexdigest()!=entry["sha256"] or entry["sha256"]!=plan["frozen_files"][name]:
            raise ValueError("frozen input bundle mismatch")
    for run in plan["runs"]:
        if any(name not in bundle or bundle[name]["sha256"]!=sha for name,sha in run["input_sha256"].items()):
            raise ValueError("run input missing or mismatched")
    audit=json.loads((root/"audit.json").read_text())
    expected=dict(stage_0_5_gate="pending_simulation_sample",scientific_claim_eligible=False,
        ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,
        stage_1_1_allowed=False,b0_task_data_isolation_accepted=False,b0_validation_window_rows_materialised="Unknown")
    if any(audit.get(k)!=v for k,v in expected.items()):raise ValueError("scientific boundary changed")
    runs=json.loads((root/"run_manifest.json").read_text())
    if runs["task_attempts"]>8:raise ValueError("task run ceiling exceeded")
    print(json.dumps(dict(passed=True,manifest_files=len(manifest["files"]),bundled_inputs=len(bundle),
        plan_sha256=digest,local_real_data_required=False,b0_isolation_still_not_accepted=True)))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("path",type=Path)
    verify(p.parse_args().path)
