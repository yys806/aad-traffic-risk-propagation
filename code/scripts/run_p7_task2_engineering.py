"""Explicit single-condition P7 SUMO engineering entry; no implicit Enabled mode."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskprop.p7_sumo_integration import run_condition


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--condition", choices=("NO_MESSAGE", "DISABLED", "ENABLED"), required=True)
    p.add_argument("--adoption-mode", choices=("DISABLED", "ENABLED"), required=True)
    p.add_argument("--assignment-id", required=True)
    p.add_argument("--adoption-mode-source", required=True)
    p.add_argument("--run-id", help="Independent run identity; omitted only for legacy callers")
    args = p.parse_args()
    summary = run_condition(args.output, args.config, condition=args.condition, adoption_mode=args.adoption_mode,
        assignment_id=args.assignment_id, adoption_mode_source=args.adoption_mode_source, run_id=args.run_id)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
