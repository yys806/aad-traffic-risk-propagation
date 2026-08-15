"""Validation helpers for paired cross-branch ETA pilot runs."""

from __future__ import annotations

import math

import pandas as pd


def summarize_mechanism_log(records: pd.DataFrame) -> dict[str, int]:
    if records.empty:
        return {
            "candidate_record_count": 0,
            "would_trigger_count": 0,
            "applied_count": 0,
            "eta_complete_count": 0,
            "remote_vehicle_count": 0,
        }
    would_trigger = records.get("would_trigger", pd.Series(False, index=records.index)).astype(bool)
    applied = records.get("applied", pd.Series(False, index=records.index)).astype(bool)
    ego_eta = pd.to_numeric(records.get("ego_eta_s"), errors="coerce")
    remote_eta = pd.to_numeric(records.get("remote_eta_s"), errors="coerce")
    remote = records.get(
        "remote_vehicle_id", pd.Series("", index=records.index)
    ).fillna("").astype(str)
    return {
        "candidate_record_count": int(len(records)),
        "would_trigger_count": int(would_trigger.sum()),
        "applied_count": int(applied.sum()),
        "eta_complete_count": int((ego_eta.notna() & remote_eta.notna()).sum()),
        "remote_vehicle_count": int(remote.loc[remote.ne("")].nunique()),
    }


def locate_first_applied_time(
    mechanism: pd.DataFrame, emissions: pd.DataFrame
) -> dict[str, float | int | None]:
    applied = mechanism.loc[mechanism["applied"].astype(bool)].sort_values("step")
    if applied.empty:
        return {
            "first_applied_step": None,
            "first_applied_time_s": None,
            "position_match_error_m": None,
        }
    record = applied.iloc[0]
    vehicle_id = str(record["ego_vehicle_id"])
    position = record["ego_position_xy"]
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        raise ValueError("Applied mechanism record lacks ego_position_xy")
    candidates = emissions.loc[emissions["id"].astype(str).eq(vehicle_id)].copy()
    if candidates.empty:
        raise ValueError(f"Applied ego vehicle not found in emissions: {vehicle_id}")
    candidates["position_error_m"] = (
        (pd.to_numeric(candidates["x"]) - float(position[0])) ** 2
        + (pd.to_numeric(candidates["y"]) - float(position[1])) ** 2
    ) ** 0.5
    match = candidates.sort_values(["position_error_m", "time"]).iloc[0]
    return {
        "first_applied_step": int(record["step"]),
        "first_applied_time_s": float(match["time"]),
        "position_match_error_m": float(match["position_error_m"]),
    }


def _time_diverges(
    on_rows: pd.DataFrame,
    off_rows: pd.DataFrame,
    *,
    numeric_columns: list[str],
    categorical_columns: list[str],
    tolerance: float,
) -> tuple[bool, float]:
    on_ids = set(on_rows["id"].astype(str))
    off_ids = set(off_rows["id"].astype(str))
    if on_ids != off_ids:
        return True, math.inf
    if not on_ids:
        return False, 0.0
    left = on_rows.set_index("id")
    right = off_rows.set_index("id")
    max_numeric_difference = 0.0
    for column in numeric_columns:
        difference = (
            pd.to_numeric(left[column], errors="coerce")
            - pd.to_numeric(right[column], errors="coerce")
        ).abs()
        finite = difference.dropna()
        if len(finite):
            max_numeric_difference = max(max_numeric_difference, float(finite.max()))
        if (difference.fillna(0.0) > tolerance).any():
            return True, max_numeric_difference
    for column in categorical_columns:
        if not left[column].fillna("").astype(str).equals(
            right[column].fillna("").astype(str)
        ):
            return True, max_numeric_difference
    return False, max_numeric_difference


def compare_pre_treatment_trajectories(
    on_emissions: pd.DataFrame,
    off_emissions: pd.DataFrame,
    *,
    first_applied_time_s: float,
    tolerance: float = 1e-9,
) -> dict[str, bool | float | None]:
    required = {"time", "id"}
    if not required.issubset(on_emissions.columns) or not required.issubset(
        off_emissions.columns
    ):
        raise ValueError("Emissions require time and id")
    on = on_emissions.copy()
    off = off_emissions.copy()
    on["time"] = pd.to_numeric(on["time"], errors="coerce")
    off["time"] = pd.to_numeric(off["time"], errors="coerce")
    numeric_columns = [
        column
        for column in ("x", "y", "speed", "relative_position", "distance")
        if column in on.columns and column in off.columns
    ]
    categorical_columns = [
        column
        for column in ("edge_id", "lane_number")
        if column in on.columns and column in off.columns
    ]
    times = sorted(set(on["time"].dropna()) | set(off["time"].dropna()))
    first_divergence = None
    pre_keys_match = True
    pre_values_match = True
    max_pre_difference = 0.0
    for time_s in times:
        on_rows = on.loc[on["time"].eq(time_s)]
        off_rows = off.loc[off["time"].eq(time_s)]
        diverges, max_difference = _time_diverges(
            on_rows,
            off_rows,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            tolerance=tolerance,
        )
        if diverges and first_divergence is None:
            first_divergence = float(time_s)
        if float(time_s) < float(first_applied_time_s):
            on_ids = set(on_rows["id"].astype(str))
            off_ids = set(off_rows["id"].astype(str))
            if on_ids != off_ids:
                pre_keys_match = False
            if diverges:
                pre_values_match = False
            max_pre_difference = max(max_pre_difference, max_difference)
    return {
        "pre_treatment_keys_match": bool(pre_keys_match),
        "pre_treatment_values_match": bool(pre_values_match),
        "max_pre_treatment_numeric_difference": float(max_pre_difference),
        "first_divergence_time_s": first_divergence,
    }
