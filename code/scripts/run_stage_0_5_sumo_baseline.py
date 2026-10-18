"""Run one Stage 0.5 no-message SUMO engineering fixture.

The output is engineering-only.  It is not a SUMO calibration result, does not
perform message, adoption, treatment or Stage I logic, and does not read the
temporal validation window.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.stage_0_5_sumo import (  # noqa: E402
    FORMAL_OBSERVATION_STEP_S,
    run_stage_0_5_no_message_baseline,
    sumo_environment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario-id", default="us101_highway_baseline")
    parser.add_argument(
        "--fixture",
        default="baseline_mixed_demand",
        choices=("baseline_mixed_demand", "measurement_probe_queue_stop"),
        help="explicitly engineering-only demand fixture",
    )
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--duration-s", type=float, default=40.0)
    parser.add_argument("--internal-step-s", type=float, default=FORMAL_OBSERVATION_STEP_S)
    parser.add_argument("--recorded-observation-step-s", type=float, default=FORMAL_OBSERVATION_STEP_S)
    parser.add_argument("--warmup-s", type=float, default=0.0)
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--check-environment",
        action="store_true",
        help="only report the local SUMO environment and exit",
    )
    args = parser.parse_args()

    if args.check_environment:
        print(json.dumps(sumo_environment(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    output = run_stage_0_5_no_message_baseline(
        output_dir=args.output,
        fixture_id=args.fixture,
        scenario_id=args.scenario_id,
        seed=args.seed,
        duration_s=args.duration_s,
        internal_step_s=args.internal_step_s,
        recorded_observation_step_s=args.recorded_observation_step_s,
        warmup_s=args.warmup_s,
        run_id=args.run_id,
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    print(json.dumps({"output": output.as_posix(), "audit": audit}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
