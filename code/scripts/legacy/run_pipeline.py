from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.legacy.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the risk propagation pilot pipeline.")
    parser.add_argument("--input", required=True, type=Path, help="Input emission CSV path.")
    parser.add_argument("--output", required=True, type=Path, help="Output folder.")
    args = parser.parse_args()

    outputs = run_pipeline(input_csv=args.input, output_dir=args.output)
    print(f"events: {outputs.events_csv}")
    print(f"edges: {outputs.edges_csv}")
    print(f"chains: {outputs.chains_csv}")
    print(f"summary: {outputs.summary_csv}")


if __name__ == "__main__":
    main()
