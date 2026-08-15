"""Topology-respecting region assignment for the merge nonlocal pilot."""

from __future__ import annotations

import math
from typing import Mapping

import pandas as pd


MERGE_EDGE_LENGTHS_M: dict[str, float] = {
    "inflow_highway": 100.0,
    "left": 500.0,
    "inflow_merge": 100.0,
    "bottom": 100.0,
    "center": 100.0,
}


def _distance_label(value: float) -> str:
    return f"{value:g}"


def assign_topology_region(
    edge_id: str,
    relative_position_m: float,
    nominal_length_m: float,
    *,
    edge_lengths_m: Mapping[str, float] = MERGE_EDGE_LENGTHS_M,
) -> dict[str, object]:
    """Assign one point without allowing a region to cross an edge boundary."""
    if nominal_length_m <= 0:
        raise ValueError("nominal_length_m must be positive")
    edge = str(edge_id).strip()
    if edge.startswith(":"):
        return {
            "region_id": f"{edge}@internal",
            "region_start_m": 0.0,
            "region_end_m": None,
        }
    if edge not in edge_lengths_m:
        raise ValueError(f"Unknown merge edge: {edge}")
    edge_length = float(edge_lengths_m[edge])
    position = float(relative_position_m)
    if not math.isfinite(position):
        raise ValueError("relative_position_m must be finite")
    position = max(0.0, min(position, math.nextafter(edge_length, 0.0)))
    start = math.floor(position / nominal_length_m) * nominal_length_m
    end = min(start + nominal_length_m, edge_length)
    return {
        "region_id": f"{edge}@{_distance_label(start)}-{_distance_label(end)}",
        "region_start_m": float(start),
        "region_end_m": float(end),
    }


def _prepare_emissions(emissions: pd.DataFrame, nominal_length_m: float) -> pd.DataFrame:
    required = {"source_file", "time", "edge_id", "relative_position"}
    missing = sorted(required - set(emissions.columns))
    if missing:
        raise ValueError(f"Emissions missing required columns: {', '.join(missing)}")
    rows = emissions.copy()
    if "vehicle_id" not in rows.columns:
        if "id" not in rows.columns:
            raise ValueError("Emissions missing vehicle identifier: id or vehicle_id")
        rows["vehicle_id"] = rows["id"].astype(str)
    rows["time"] = pd.to_numeric(rows["time"], errors="coerce")
    rows["relative_position"] = pd.to_numeric(
        rows["relative_position"], errors="coerce"
    )
    rows = rows.dropna(subset=["time", "relative_position", "vehicle_id", "edge_id"])
    region_rows = [
        assign_topology_region(edge, position, nominal_length_m)
        for edge, position in zip(rows["edge_id"], rows["relative_position"])
    ]
    regions = pd.DataFrame(region_rows, index=rows.index)
    return pd.concat([rows, regions], axis=1)


def attach_event_regions(
    events: pd.DataFrame,
    emissions: pd.DataFrame,
    nominal_length_m: float,
) -> pd.DataFrame:
    """Recover edge-local coordinates for events and assign topology regions."""
    required = {"event_id", "source_file", "time", "vehicle_id"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"Events missing required columns: {', '.join(missing)}")
    trajectory = _prepare_emissions(emissions, nominal_length_m)
    keys = ["source_file", "time", "vehicle_id"]
    context_columns = keys + [
        "edge_id",
        "relative_position",
        "region_id",
        "region_start_m",
        "region_end_m",
    ]
    context = trajectory[context_columns].drop_duplicates(keys, keep="first")
    result = events.copy()
    for column in context_columns[len(keys) :]:
        if column in result.columns:
            result = result.rename(columns={column: f"legacy_{column}"})
    result["time"] = pd.to_numeric(result["time"], errors="coerce")
    result["vehicle_id"] = result["vehicle_id"].astype(str)
    result = result.merge(context, on=keys, how="left", validate="many_to_one")
    missing_context = result["region_id"].isna()
    if missing_context.any():
        sample = result.loc[missing_context, keys].head(3).to_dict("records")
        raise ValueError(f"Unable to locate emission rows for {int(missing_context.sum())} events: {sample}")
    return result


def _simulation_steps_by_file(emissions: pd.DataFrame) -> pd.Series:
    unique_times = emissions[["source_file", "time"]].drop_duplicates()
    unique_times = unique_times.sort_values(["source_file", "time"])
    unique_times["dt"] = unique_times.groupby("source_file")["time"].diff()
    positive = unique_times.loc[unique_times["dt"] > 0]
    return positive.groupby("source_file")["dt"].median()


def summarize_region_risk(
    events: pd.DataFrame,
    emissions: pd.DataFrame,
    nominal_length_m: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return exposure-normalized region risk and event-level mapped scores."""
    trajectory = _prepare_emissions(emissions, nominal_length_m)
    steps = _simulation_steps_by_file(trajectory)
    trajectory["frame_exposure_s"] = trajectory["source_file"].map(steps).fillna(0.0)
    exposure = (
        trajectory.groupby("region_id", as_index=False)
        .agg(
            edge_id=("edge_id", "first"),
            region_start_m=("region_start_m", "first"),
            region_end_m=("region_end_m", "first"),
            frame_count=("vehicle_id", "size"),
            vehicle_count=("vehicle_id", "nunique"),
            vehicle_time_s=("frame_exposure_s", "sum"),
        )
    )
    attached = attach_event_regions(events, emissions, nominal_length_m)
    if "risk_score" not in attached.columns:
        attached["risk_score"] = 1.0
    event_summary = (
        attached.groupby("region_id", as_index=False)
        .agg(event_count=("event_id", "size"), risk_score_sum=("risk_score", "sum"))
    )
    table = exposure.merge(event_summary, on="region_id", how="left")
    table[["event_count", "risk_score_sum"]] = table[
        ["event_count", "risk_score_sum"]
    ].fillna(0.0)
    denominator = table["vehicle_time_s"].where(table["vehicle_time_s"] > 0)
    table["event_rate_per_1000_vehicle_s"] = (
        1000.0 * table["event_count"] / denominator
    ).fillna(0.0)
    table["risk_score_rate_per_1000_vehicle_s"] = (
        1000.0 * table["risk_score_sum"] / denominator
    ).fillna(0.0)
    rate_map = table.set_index("region_id")["event_rate_per_1000_vehicle_s"]
    attached["event_region_rate"] = attached["region_id"].map(rate_map)
    return table.sort_values("region_id").reset_index(drop=True), attached


def compare_scale_event_scores(
    first: pd.DataFrame,
    second: pd.DataFrame,
    *,
    top_n: int = 20,
) -> dict[str, float | int]:
    """Compare two scales on the same event identifiers."""
    required = {"event_id", "event_region_rate"}
    if not required.issubset(first.columns) or not required.issubset(second.columns):
        raise ValueError("Scale event tables require event_id and event_region_rate")
    paired = first[["event_id", "event_region_rate"]].merge(
        second[["event_id", "event_region_rate"]],
        on="event_id",
        suffixes=("_first", "_second"),
        validate="one_to_one",
    )
    spearman = paired["event_region_rate_first"].corr(
        paired["event_region_rate_second"], method="spearman"
    )

    def top_events(frame: pd.DataFrame) -> set[str]:
        ordered = frame.sort_values(
            ["event_region_rate", "event_id"], ascending=[False, True]
        )
        return set(ordered.head(min(top_n, len(ordered)))["event_id"].astype(str))

    first_top = top_events(first)
    second_top = top_events(second)
    union = first_top | second_top
    jaccard = len(first_top & second_top) / len(union) if union else 1.0
    return {
        "shared_event_count": int(len(paired)),
        "spearman_event_score": float(spearman) if pd.notna(spearman) else 0.0,
        "top_event_jaccard": float(jaccard),
    }
