from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.e17a import write_real_reference_package


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze real-only E17-A reference features; does not run SUMO or message effects."
    )
    parser.add_argument("--ngsim-state", type=Path, action="append", required=True)
    parser.add_argument("--pneuma-state", type=Path, required=True)
    parser.add_argument("--ngsim-events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-rows-per-group", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260907)
    args = parser.parse_args()
    output = write_real_reference_package(
        ngsim_state_paths=args.ngsim_state,
        pneuma_state_path=args.pneuma_state,
        ngsim_event_path=args.ngsim_events,
        output_dir=args.output,
        max_rows_per_group=args.max_rows_per_group,
        seed=args.seed,
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    print(json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
