"""Run only the authorized AAD-0.5.4-A+ diagnostics (never calibration)."""
import argparse
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
from riskprop.stage_0_5_calibration_gaps import run_diagnostics

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    run_diagnostics(args.repo_root.resolve(),args.output.resolve())
