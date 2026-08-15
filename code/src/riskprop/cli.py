from __future__ import annotations

import argparse
from pathlib import Path

from riskprop.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract risk events and propagation edges from an emission CSV.")
    parser.add_argument("--input", required=True, type=Path, help="Input emission CSV path.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for risk_events/risk_edges/risk_summary CSV files.")
    args = parser.parse_args()

    outputs = run_pipeline(input_csv=args.input, output_dir=args.output)
    print(f"events={outputs.events_csv}")
    print(f"edges={outputs.edges_csv}")
    print(f"chains={outputs.chains_csv}")
    print(f"summary={outputs.summary_csv}")


if __name__ == "__main__":
    main()
