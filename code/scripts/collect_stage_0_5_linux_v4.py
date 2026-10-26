"""Read an explicit engineering-only WSL evidence allowlist. Never launches SUMO.

No recursive data search, no remote writes, no existing audit replacement.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT="/home/shen/AAD/"
RUNTIME=ROOT+"code/runtime/stage_0_5_sumo126_v4_r2/"
STAGES=ROOT+"code/tmp/stage05_v4_20261026_"
READER='''import base64,json,pathlib,sys
request=json.load(sys.stdin);records=[]
for name in request:
 p=pathlib.Path(name)
 assert name.startswith("/home/shen/AAD/code/tmp/stage05_v4_20261026_") or name.startswith("/home/shen/AAD/code/runtime/stage_0_5_sumo126_v4_r2/")
 assert ".." not in p.parts and not p.is_symlink() and p.is_file() and p.stat().st_size<8*1024**2
 records.append(dict(source_path=name,data=base64.b64encode(p.read_bytes()).decode()))
print(json.dumps(records))
'''


def collect(destination,*,current_probes=False):
    destination=Path(destination).resolve()
    repo=Path(__file__).resolve().parents[2]
    if not destination.is_relative_to(repo/"docs/audits/stage_0_5_linux_native_v4") or destination.exists():
        raise ValueError("new_scoped_collection_required")
    items={"runtime/installation_record.json":RUNTIME+"installation_record.json",
        "runtime/requirements.lock":RUNTIME+"requirements.lock",
        "runtime/runtime_manifest.json":STAGES+"r4/runtime_manifest.json",
        "failure-r3/staging_record.json":STAGES+"r3/staging_record.json",
        "failure-r3/smoke_proposal.json":STAGES+"r3/smoke_proposal.json",
        "failure-r3/smoke_envelope.json":STAGES+"r3/smoke_envelope.json",
        "staging-r4/staging_record.json":STAGES+"r4/staging_record.json"}
    for name in ["launch_attempt.json","broker.stdout","broker.stderr","coordinator_failure.json","policy.json"]:
        items["failure-r3/"+name]=STAGES+"r3/smoke_capsule/"+name
    # The authorized r4 attempt is synthetic only.  Collect its immutable
    # proposal, envelope, broker records and controller failure separately;
    # this preserves the failed attempt without treating it as a pass.
    for name in ["smoke_proposal.json","smoke_envelope.json","smoke_envelope_authorized.json"]:
        items["failure-r4/"+name]=STAGES+"r4/"+name
    for name in ["launch_attempt.json","broker.stdout","broker.stderr","coordinator_failure.json","policy.json"]:
        items["failure-r4/"+name]=STAGES+"r4/smoke_capsule/"+name
    for name in ["isolation_runtime.json","controller_receipt.json","controller_error.txt","interrupted_identity_summary.json","executed_policy.json","broker_context.json","capability_record.json"]:
        items["failure-r4/archive/"+name]=STAGES+"r4/smoke_capsule/archive/"+name
    from prepare_stage_0_5_linux_stage_v4 import SOURCES
    for name in SOURCES:items["failure-r3/source/"+name]=STAGES+"r3/"+name
    for revision in ["r2"]+(["r4"] if current_probes else []):
        for name in ["record.json"]+[m+e for m in ["basic","output","pids","memory","cpu","timeout"] for e in [".stdout",".stderr"]]:
            items["probe-"+revision+"/"+name]=STAGES+revision+"/probe_results/"+name
    command=["wsl.exe","-d","Ubuntu","--cd","/home/shen/AAD","--exec","/usr/bin/python3","-I","-B","-c",READER]
    result=subprocess.run(command,input=json.dumps(list(items.values())).encode(),capture_output=True,timeout=60)
    if result.returncode:raise RuntimeError("engineering_evidence_read_failed:"+result.stderr.decode(errors="replace"))
    records=json.loads(result.stdout)
    if [r["source_path"] for r in records]!=list(items.values()):raise ValueError("collection_source_order")
    destination.mkdir(parents=True,exist_ok=False);manifest={}
    for (name,origin),record in zip(items.items(),records):
        data=base64.b64decode(record["data"],validate=True);target=destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as f:f.write(data)
        manifest[name]=dict(source_path=origin,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    with (destination/"collection.json").open("x",encoding="utf-8") as f:
        json.dump(dict(scope="Exact allowlisted synthetic/runtime files only",command=command,exit_code=result.returncode,files=manifest),f,indent=2)
    print(json.dumps(dict(destination=str(destination),files=len(manifest)),ensure_ascii=False))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("destination");p.add_argument("--current-probes",action="store_true")
    a=p.parse_args();collect(a.destination,current_probes=a.current_probes)
