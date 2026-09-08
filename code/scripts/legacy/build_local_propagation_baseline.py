from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.legacy.local_propagation_baseline import (  # noqa: E402
    build_local_propagation_baseline,
)
from riskprop.legacy.local_propagation_visuals import (  # noqa: E402
    create_local_baseline_visual_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the formal local propagation baseline from validated risk episodes."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "risk_event_dataset_20260716",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "local_propagation_baseline_20260718",
    )
    parser.add_argument("--max-delay", type=float, default=3.0)
    parser.add_argument("--max-distance", type=float, default=50.0)
    parser.add_argument("--permutations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260718)
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    episodes = pd.read_csv(args.input / "risk_episodes.csv")
    manifest = pd.read_csv(args.input / "extraction_manifest.csv")
    result = build_local_propagation_baseline(
        episodes,
        manifest,
        max_delay_s=args.max_delay,
        max_distance_m=args.max_distance,
        n_permutations=args.permutations,
        seed=args.seed,
        null_workers=args.workers,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    filenames = {
        "eligible_episodes": "eligible_episodes.csv",
        "candidate_edges": "local_candidate_edges.csv",
        "direct_edges": "local_direct_edges.csv",
        "chain_nodes": "local_chain_nodes.csv",
        "chains": "local_chains.csv",
        "run_summary": "local_run_summary.csv",
        "cell_summary": "local_cell_summary.csv",
        "null_summary": "local_null_summary.csv",
        "sensitivity": "local_threshold_sensitivity.csv",
    }
    for key, filename in filenames.items():
        result[key].to_csv(args.output / filename, index=False)
    figure_catalog = create_local_baseline_visual_package(
        result, args.output / "figures"
    )
    summary = {
        "eligible_episode_count": len(result["eligible_episodes"]),
        "candidate_edge_count": len(result["candidate_edges"]),
        "direct_edge_count": len(result["direct_edges"]),
        "chain_count": len(result["chains"]),
        "multi_hop_chain_count": int(
            (result["chains"].get("max_depth", pd.Series(dtype=float)) >= 2).sum()
        ),
        "max_depth": int(
            result["chains"].get("max_depth", pd.Series([0])).max()
        ),
        "max_delay_s": args.max_delay,
        "max_distance_m": args.max_distance,
        "permutations": args.permutations,
        "seed": args.seed,
        "workers": args.workers,
        "figure_count": len(figure_catalog),
        "gpu_required": False,
    }
    (args.output / "baseline_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
