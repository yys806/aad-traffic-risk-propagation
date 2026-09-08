from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.legacy.feasibility_data import generate_merge_feasibility_emissions  # noqa: E402
from riskprop.legacy.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    output_root = PROJECT_ROOT / "outputs" / "feasibility_week" / "riskprop_synthetic_merge"
    emission_csv = output_root / "input" / "merge_feasibility_emissions.csv"
    risk_output_dir = output_root / "risk_outputs"
    summary_json = output_root / "validation_summary.json"

    generate_merge_feasibility_emissions(emission_csv)
    outputs = run_pipeline(input_csv=emission_csv, output_dir=risk_output_dir)

    events = pd.read_csv(outputs.events_csv)
    edges = pd.read_csv(outputs.edges_csv)
    chains = pd.read_csv(outputs.chains_csv)
    summary = pd.read_csv(outputs.summary_csv)

    validation = {
        "input_csv": str(emission_csv),
        "events_csv": str(outputs.events_csv),
        "edges_csv": str(outputs.edges_csv),
        "chains_csv": str(outputs.chains_csv),
        "summary_csv": str(outputs.summary_csv),
        "event_count": int(len(events)),
        "event_types": sorted(events["event_type"].dropna().unique().tolist()),
        "edge_count": int(len(edges)),
        "chain_proxy_count": int(len(chains)),
        "mean_delay_s": float(summary.loc[0, "mean_delay_s"]) if len(summary) else 0.0,
        "mean_distance_m": float(summary.loc[0, "mean_distance_m"]) if len(summary) else 0.0,
        "long_range_trigger_ratio": float(summary.loc[0, "long_range_trigger_ratio"]) if len(summary) else 0.0,
        "feasibility_read": "pipeline_feasible_with_flow_like_emission_fields; real_flow_rollout_pending_environment_setup",
    }
    summary_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(validation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
