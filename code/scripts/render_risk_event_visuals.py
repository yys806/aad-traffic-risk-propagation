from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.risk_event_visuals import create_risk_event_visual_package  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the full risk-event visual package from validated CSV outputs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "risk_event_dataset_20260716",
        help="Directory containing the validated full risk-event CSV files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Figure output directory; defaults to INPUT/figures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog = create_risk_event_visual_package(args.input, args.output)
    output = args.output if args.output is not None else args.input / "figures"
    print(f"figures={len(catalog)}")
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
