from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from riskprop.legacy.events import EventThresholds, coalesce_risk_events, extract_risk_events
from riskprop.legacy.propagation import (
    build_propagation_edges,
    score_event_roles,
    select_direct_propagation_edges,
    summarise_propagation,
)


@dataclass(frozen=True)
class PipelineOutputs:
    events_csv: Path
    episodes_csv: Path
    candidate_edges_csv: Path
    edges_csv: Path
    chains_csv: Path
    roles_csv: Path
    summary_csv: Path


def run_pipeline(
    input_csv: str | Path,
    output_dir: str | Path,
    thresholds: EventThresholds | None = None,
) -> PipelineOutputs:
    """Run the first-pass risk propagation pipeline on one emission CSV."""
    input_csv = Path(input_csv)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    emissions = pd.read_csv(input_csv)
    events = extract_risk_events(emissions, thresholds=thresholds)
    episodes = coalesce_risk_events(events)
    candidate_edges = build_propagation_edges(episodes)
    edges = select_direct_propagation_edges(candidate_edges)
    chains = _chain_proxy(edges)
    roles = score_event_roles(episodes, edges)
    summary = summarise_propagation(episodes, edges, candidate_edges=candidate_edges)
    raw_counts = events.groupby("run_id").size().rename("raw_event_count") if not events.empty else pd.Series(dtype=int)
    summary = summary.merge(raw_counts, left_on="run_id", right_index=True, how="left")
    summary["raw_event_count"] = summary["raw_event_count"].fillna(0).astype(int)

    outputs = PipelineOutputs(
        events_csv=output_dir / "risk_events.csv",
        episodes_csv=output_dir / "risk_episodes.csv",
        candidate_edges_csv=output_dir / "risk_candidate_edges.csv",
        edges_csv=output_dir / "risk_edges.csv",
        chains_csv=output_dir / "risk_chains.csv",
        roles_csv=output_dir / "risk_node_roles.csv",
        summary_csv=output_dir / "risk_summary.csv",
    )
    events.to_csv(outputs.events_csv, index=False)
    episodes.to_csv(outputs.episodes_csv, index=False)
    candidate_edges.to_csv(outputs.candidate_edges_csv, index=False)
    edges.to_csv(outputs.edges_csv, index=False)
    chains.to_csv(outputs.chains_csv, index=False)
    roles.to_csv(outputs.roles_csv, index=False)
    summary.to_csv(outputs.summary_csv, index=False)
    return outputs


def _chain_proxy(edges: pd.DataFrame) -> pd.DataFrame:
    """Create a lightweight chain table before full graph traversal is added."""
    if edges.empty:
        return pd.DataFrame(
            columns=[
                "chain_id",
                "run_id",
                "source_event_id",
                "event_count_proxy",
                "max_delay_s",
                "max_distance_m",
                "mean_propagation_score",
            ]
        )

    grouped = edges.groupby(["run_id", "source_event_id"], as_index=False).agg(
        event_count_proxy=("target_event_id", "count"),
        max_delay_s=("delay_s", "max"),
        max_distance_m=("distance_m", "max"),
        mean_propagation_score=("propagation_score", "mean"),
    )
    grouped.insert(0, "chain_id", [f"c{i:06d}" for i in range(len(grouped))])
    return grouped
