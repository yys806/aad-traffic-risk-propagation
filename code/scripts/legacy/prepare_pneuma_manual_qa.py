from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.legacy.pneuma_qa import write_pneuma_manual_qa_pack


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare candidate-only pNEUMA road/leader QA; never computes TTC."
    )
    parser.add_argument("--mapmatch-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--osm", type=Path)
    parser.add_argument("--total", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--pilot-per-stratum", type=int, default=12)
    args = parser.parse_args()
    output = write_pneuma_manual_qa_pack(
        mapmatch_dir=args.mapmatch_dir,
        output_dir=args.output,
        osm_path=args.osm,
        total=args.total,
        seed=args.seed,
        pilot_per_stratum=args.pilot_per_stratum,
    )
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "sample_count": args.total,
                "pilot_count": args.pilot_per_stratum * 4,
                "gate_status": "pending_human_round1",
                "ttc_generated": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
