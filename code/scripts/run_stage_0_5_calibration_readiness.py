"""Run the Stage 0.5.4-A calibration-readiness and measurement-equivalence audit.

The audit reads only the two approved US-101 calibration windows and the formal P2 event
table restricted to those windows.  It never reads the temporal validation window, never
touches the locked holdout, and never freezes a scientific parameter.
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

from riskprop.stage_0_5_calibration_readiness import (  # noqa: E402
    READINESS_RESULT_ID,
    run_calibration_readiness_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--no-package",
        action="store_true",
        help="run the audit and print the summary without sealing a package",
    )
    args = parser.parse_args()
    payload = run_calibration_readiness_audit(
        repo_root=args.repo_root,
        output_dir=args.output,
        write_package=not args.no_package,
    )
    if args.no_package:
        summary = {
            "result_id": READINESS_RESULT_ID,
            "measurement_equivalence_status": payload["measurement_equivalence"]["overall_status"],
            "boundary_cases_all_as_expected": payload["measurement_equivalence"]["boundary_cases_all_as_expected"],
            "verdict_counts": payload["measurement_equivalence"]["verdict_counts"],
            "blocking_measurement_items": payload["measurement_equivalence"]["blocking_items"],
            "ready_to_start_stage_0_5_4b": payload["stage_0_5_4b_admission_checklist"][
                "ready_to_start_stage_0_5_4b"
            ],
            "p2_events_used": payload["audit"]["p2_events_used"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    audit = json.loads((args.output / "audit.json").read_text(encoding="utf-8"))
    print(json.dumps({"output": args.output.as_posix(), "audit": audit}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
