from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.simulation_real_coverage import evaluate_simulation_coverage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate an Stage 0.5 calibration package; this command has no message-effect inputs."
    )
    parser.add_argument("--real", type=Path, action="append", required=True)
    parser.add_argument("--simulation", type=Path, required=True)
    parser.add_argument("--continuous", nargs="+", required=True)
    parser.add_argument("--stratum-column", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    real_groups = {path.stem: pd.read_parquet(path) for path in args.real}
    simulation = pd.read_parquet(args.simulation)
    result = evaluate_simulation_coverage(
        real_groups=real_groups,
        simulation=simulation,
        continuous_columns=args.continuous,
        stratum_column=args.stratum_column,
    )
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.output.resolve())
    return 0 if result["gate_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
