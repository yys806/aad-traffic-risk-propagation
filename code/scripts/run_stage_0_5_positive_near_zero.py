"""Independent B1.2-P entry; no C/D, main-matrix or calibration command."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/src'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','tests','freeze','run','worker','checkpoint'])
    p.add_argument('--batch',type=Path,required=True);p.add_argument('--run-id')
    a=p.parse_args();b=a.batch.resolve();guard=None
    if a.command!='prepare':
        if not Path(__file__).resolve().is_relative_to(b/'runtime'):raise PermissionError('use -S capsule entry')
        from riskprop.stage_0_5_b1_isolation import install_guard
        guard=install_guard(b)
    try:
        from riskprop.stage_0_5_positive_runtime import dispatch
        dispatch(ROOT,b,a.command,a.run_id)
    finally:
        if guard is not None:
            d=b/'access_logs';d.mkdir(exist_ok=True)
            (d/f'{a.command}_{a.run_id or os.getpid()}.json').write_text(json.dumps(guard,indent=2),encoding='utf-8')
            if guard['denied']:raise PermissionError('global unexpected access denial')
