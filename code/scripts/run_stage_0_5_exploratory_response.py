"""B0 frozen diagnostic workflow, never formal calibration."""
import argparse
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
from riskprop.stage_0_5_exploratory_response import prepare_batch,execute_phase,run_worker,phase1_checkpoint

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=["prepare","phase1","checkpoint","control","phase2","analyze","worker"])
    p.add_argument("--batch",type=Path,required=True)
    p.add_argument("--run-id")
    a=p.parse_args()
    batch=a.batch.resolve()
    if a.command=="prepare": prepare_batch(ROOT,batch)
    elif a.command=="worker": run_worker(batch,a.run_id)
    elif a.command=="checkpoint": phase1_checkpoint(batch)
    elif a.command=="analyze":
        from riskprop.stage_0_5_exploratory_analysis import finalize
        finalize(ROOT,batch)
    else: execute_phase(batch,a.command)
