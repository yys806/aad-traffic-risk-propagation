"""B1.2-N controlled entry. There is deliberately no main-matrix command."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=["prepare","tests","freeze-micro","micro","micro-checkpoint","freeze-integration","C","D","worker"])
    p.add_argument("--batch",type=Path,required=True);p.add_argument("--run-id");p.add_argument("--plan",default="micro_plan.json")
    a=p.parse_args();b=a.batch.resolve();audit=None
    if a.command!="prepare":
        if not Path(__file__).resolve().is_relative_to(b/"runtime"):raise PermissionError("use B1.2-N -S capsule copy")
        from riskprop.stage_0_5_b1_isolation import install_guard
        audit=install_guard(b)
    try:
        from riskprop.stage_0_5_b12n_runtime import dispatch
        dispatch(ROOT,b,a.command,a.run_id,a.plan)
    finally:
        if audit is not None:
            folder=b/"access_logs";folder.mkdir(exist_ok=True)
            (folder/f'{a.command}_{a.run_id or os.getpid()}.json').write_text(json.dumps(audit,indent=2),encoding="utf-8")
            if audit["denied"]:raise PermissionError("unexpected capsule denial: global stop")
