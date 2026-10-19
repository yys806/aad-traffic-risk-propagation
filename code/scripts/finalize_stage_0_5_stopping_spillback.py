"""Stage the separately hashed descriptive renderer, then finalize in B1.1 capsule.

This entry never runs SUMO or edits a frozen measurement/input file.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("batch",type=Path)
    batch=p.parse_args().batch.resolve()
    if not (batch/"PLAN_SHA256").is_file() or not (batch/"execution_ledger.json").is_file():
        raise ValueError("frozen completed capsule required")
    root=Path(__file__).resolve().parents[2]
    source=root/"code/src/riskprop/stage_0_5_contract_analysis.py"
    shutil.copyfile(source,batch/"runtime/code/src/riskprop"/source.name)
    plan=json.loads((batch/"experiment_plan.json").read_text(encoding="utf-8"));files=[];generated=[]
    for name,digest in plan["frozen_files"].items():
        if not name.startswith("runtime/code/"):continue
        original=(batch/name).read_bytes()
        if hashlib.sha256(original).hexdigest()!=digest:raise ValueError("frozen runtime changed")
        relative=name.removeprefix("runtime/")
        if relative in ["code/pytest.ini","code/src/sitecustomize.py","code/src/riskprop/__init__.py"]:
            generated.append(dict(path=name,sha256=digest,base64=base64.b64encode(original).decode(),purpose="B1 minimal bootstrap/config"));continue
        canonical=original.replace(b"\r\n",b"\n")
        transform="none" if canonical==original else "canonical LF to original CRLF"
        if transform!="none" and canonical.replace(b"\n",b"\r\n")!=original:raise ValueError("unverified source byte transform")
        files.append(dict(path=relative,frozen_sha256=digest,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),byte_transform=transform))
    summary=batch/"summary";summary.mkdir(exist_ok=True)
    (summary/"git_source_binding_audit.json").write_text(json.dumps(dict(files=files,generated_runtime=generated,
        source_of_bytes="frozen capsule source, LF canonicalisation; verify separately against Git HEAD",new_runs=0),indent=2)+"\n",encoding="utf-8")
    entry=batch/"runtime/code/scripts/run_stage_0_5_stopping_spillback.py"
    raise SystemExit(subprocess.call([sys.executable,"-S",str(entry),"finalize","--batch",str(batch)]))
