from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.legacy.pneuma_mapmatch import write_pneuma_csv_mapmatch_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build candidate-only pNEUMA map/leader assignments for E15-A manual QA."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--osm", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-distance-m", type=float, default=6.0)
    args = parser.parse_args()
    package = write_pneuma_csv_mapmatch_package(
        source_path=args.source,
        osm_path=args.osm,
        output_dir=args.output,
        max_distance_m=args.max_distance_m,
    )
    print((package / "audit.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
