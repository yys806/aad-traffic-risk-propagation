from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.local_propagation_baseline import (  # noqa: E402
    build_local_candidate_edges,
    prepare_eligible_episodes,
    select_local_direct_edges,
)
from riskprop.regions import (  # noqa: E402
    compare_scale_event_scores,
    summarize_region_risk,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run merge topology region-scale pilot.")
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--emission-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scales", type=float, nargs="+", default=[25.0, 50.0, 75.0])
    return parser.parse_args()


def _load_selected_events(path: Path) -> pd.DataFrame:
    events = pd.read_csv(path)
    if "scenario" in events.columns:
        events = events.loc[events["scenario"].astype(str).eq("merge")]
    if "method" in events.columns:
        events = events.loc[events["method"].astype(str).eq("ours")]
    if "penetration_pct" in events.columns:
        penetration = pd.to_numeric(events["penetration_pct"], errors="coerce")
        events = events.loc[penetration.isin([60, 80])]
    return prepare_eligible_episodes(events).reset_index(drop=True)


def _load_emissions(emission_dir: Path, source_files: list[str]) -> pd.DataFrame:
    frames = []
    keep = ["time", "id", "edge_id", "relative_position", "x"]
    for source_file in sorted(set(source_files)):
        path = emission_dir / source_file
        if not path.exists():
            raise FileNotFoundError(f"Missing emission file: {path}")
        available = pd.read_csv(path, nrows=0).columns
        columns = [column for column in keep if column in available]
        frame = pd.read_csv(path, usecols=columns)
        frame.insert(0, "source_file", source_file)
        frames.append(frame)
    if not frames:
        raise ValueError("No selected emission files")
    return pd.concat(frames, ignore_index=True)


def _distance_quantiles(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = [("p60_p80", events)]
    if "penetration_pct" in events.columns:
        groups.extend(
            (f"p{int(penetration)}", group)
            for penetration, group in events.groupby("penetration_pct", sort=True)
        )
    for label, group in groups:
        candidates = build_local_candidate_edges(
            group, max_delay_s=3.0, max_distance_m=200.0
        )
        direct = select_local_direct_edges(candidates)
        scoped = {"all_direct": direct}
        scoped["cross_vehicle"] = (
            direct.loc[direct["is_cross_vehicle"].astype(bool)]
            if not direct.empty and "is_cross_vehicle" in direct.columns
            else direct.iloc[0:0]
        )
        for scope, scoped_edges in scoped.items():
            distances = pd.to_numeric(
                scoped_edges.get("distance_m", pd.Series(dtype=float)),
                errors="coerce",
            ).dropna()
            for quantile in (0.90, 0.95, 0.99):
                rows.append(
                    {
                        "group": label,
                        "scope": scope,
                        "max_delay_s": 3.0,
                        "candidate_distance_limit_m": 200.0,
                        "direct_edge_count": int(len(distances)),
                        "quantile": quantile,
                        "distance_m": (
                            float(distances.quantile(quantile))
                            if len(distances)
                            else None
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _scale_label(scale: float) -> str:
    return f"{scale:g}"


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    events = _load_selected_events(args.events)
    emissions = _load_emissions(args.emission_dir, events["source_file"].astype(str).tolist())

    scale_tables: dict[float, pd.DataFrame] = {}
    event_tables: dict[float, pd.DataFrame] = {}
    scale_rows = []
    for scale in args.scales:
        region_table, event_table = summarize_region_risk(events, emissions, scale)
        label = _scale_label(scale)
        region_table.to_csv(output_dir / f"region_summary_L{label}.csv", index=False)
        event_table.to_csv(output_dir / f"event_regions_L{label}.csv", index=False)
        scale_tables[scale] = region_table
        event_tables[scale] = event_table
        scale_rows.append(
            {
                "nominal_length_m": float(scale),
                "exposed_region_count": int(len(region_table)),
                "risk_region_count": int((region_table["event_count"] > 0).sum()),
                "event_count": int(len(event_table)),
                "vehicle_time_s": float(region_table["vehicle_time_s"].sum()),
            }
        )

    comparison_rows = []
    for first_scale, second_scale in combinations(args.scales, 2):
        comparison = compare_scale_event_scores(
            event_tables[first_scale], event_tables[second_scale], top_n=20
        )
        comparison_rows.append(
            {
                "first_scale_m": float(first_scale),
                "second_scale_m": float(second_scale),
                **comparison,
            }
        )
    scale_summary = pd.DataFrame(scale_rows)
    comparisons = pd.DataFrame(comparison_rows)
    distance_quantiles = _distance_quantiles(events)
    scale_summary.to_csv(output_dir / "scale_summary.csv", index=False)
    comparisons.to_csv(output_dir / "scale_comparison.csv", index=False)
    distance_quantiles.to_csv(output_dir / "distance_quantiles.csv", index=False)

    summary = {
        "events_path": str(args.events.resolve()),
        "emission_dir": str(args.emission_dir.resolve()),
        "selected_event_count": int(len(events)),
        "selected_file_count": int(events["source_file"].nunique()),
        "scales_m": [float(scale) for scale in args.scales],
        "scale_summary": scale_rows,
        "scale_comparison": comparison_rows,
        "distance_quantiles": distance_quantiles.to_dict("records"),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# 区域尺度实验",
        "",
        f"纳入 {len(events)} 条风险 episode、{events['source_file'].nunique()} 个 p60/p80 轨迹文件。",
        "",
        "| L0 (m) | 有车辆区域 | 有风险区域 | 风险 episode |",
        "|---:|---:|---:|---:|",
    ]
    for row in scale_rows:
        lines.append(
            f"| {row['nominal_length_m']:g} | {row['exposed_region_count']} | "
            f"{row['risk_region_count']} | {row['event_count']} |"
        )
    lines.extend(
        [
            "",
            "该结果只检验区域划分和机制实验的可运行性，不构成正式因果效应估计。",
        ]
    )
    (output_dir / "区域尺度实验.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
