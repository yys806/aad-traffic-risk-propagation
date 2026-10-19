"""Independent B1.2 entry; all execution after prepare requires the -S capsule."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=["prepare","tests","freeze-integration","integration","admit",
                                      "freeze-main","phase1","checkpoint","phase2","worker"])
    p.add_argument("--batch",type=Path,required=True);p.add_argument("--run-id");p.add_argument("--plan",default="integration_plan.json")
    a=p.parse_args();batch=a.batch.resolve();audit=None
    if a.command!="prepare":
        if not Path(__file__).resolve().is_relative_to(batch/"runtime"):
            raise PermissionError("use B1.2 capsule copy")
        from riskprop.stage_0_5_b1_isolation import install_guard
        audit=install_guard(batch)
    try:
        from riskprop.stage_0_5_b12_runtime import dispatch
        dispatch(ROOT,batch,a.command,a.run_id,a.plan)
    finally:
        if audit is not None:
            folder=batch/"access_logs";folder.mkdir(exist_ok=True)
            (folder/f'{a.command}_{a.run_id or os.getpid()}.json').write_text(json.dumps(audit,indent=2),encoding="utf-8")
            if audit["denied"]:raise PermissionError("unexpected B1.2 access denial; stop")
