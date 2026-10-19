"""B1 entrypoint: prepare in project; all other work in the isolated capsule."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("command",choices=["prepare","preflight","freeze","phase1","checkpoint","phase2","worker","analyze","tests"])
p.add_argument("--batch",type=Path,required=True);p.add_argument("--run-id")
a=p.parse_args();batch=a.batch.resolve();audit=None
if a.command!="prepare":
    if not Path(__file__).resolve().is_relative_to(batch/"runtime"):
        raise PermissionError("B1 work must use the capsule copy of this entrypoint")
    from riskprop.stage_0_5_b1_isolation import install_guard
    audit=install_guard(batch)
try:
    from riskprop.stage_0_5_boundary_bottleneck import dispatch
    dispatch(ROOT,batch,a.command,a.run_id)
finally:
    if audit is not None:
        folder=batch/"access_logs";folder.mkdir(exist_ok=True)
        (folder/f"{a.command}_{a.run_id or os.getpid()}.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
        if audit["denied"]:
            raise PermissionError("unexpected capsule denial; stop batch and review access log")
