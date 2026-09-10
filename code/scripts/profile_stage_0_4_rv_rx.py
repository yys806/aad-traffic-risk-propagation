from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.communication_observability import write_rv_rx_calibration_profile


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile SPMD RV_RX calibration trips only; locked-holdout outcomes are discarded."
    )
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--segment-gap-cs", type=int, default=100)
    args = parser.parse_args()
    output = write_rv_rx_calibration_profile(
        zip_path=args.zip_path,
        output_path=args.output,
        segment_gap_cs=args.segment_gap_cs,
    )
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
