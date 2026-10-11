"""Versioned formal Stage 0.2 risk measurement semantics.

This module is intentionally separate from the historical engineering baseline.
It provides the approved P2 event configuration, causal confirmation checks,
rho mapping, bounded contribution semantics, fixed-window integration, and DID
interval arithmetic.  It does not choose target regions, cohorts, windows, or
message de-duplication rules.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import exp, isfinite
from typing import Any, Iterable, Mapping

import pandas as pd

from .ngsim_risk_calibration import extract_rear_end_events


@dataclass(frozen=True)
class FormalRiskConfig:
    schema_version: str = "stage_0_2.formal_risk_measurement.config.v1"
    algorithm_version: str = "stage_0_2.formal_risk_measurement.v1"
    ttc_threshold_s: float = 2.0
    minimum_duration_s: float = 0.2
    max_gap_s: float = 0.11
    tau_s: float = 15.364279197080283
    confirmation_semantics: str = "first_observed_timestamp_meeting_span"
    missing_policy: str = "unknown_bounds_full_window"
    target_region: Any = None
    target_vehicle_qualification: Any = None
    evaluation_window: Any = None
    message_deduplication: Any = None
    scientific_defaults_frozen: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


P2_FORMAL_CONFIG = FormalRiskConfig()
P1_SENSITIVITY_CONFIG = FormalRiskConfig(ttc_threshold_s=1.5, minimum_duration_s=0.3)
P3_SENSITIVITY_CONFIG = FormalRiskConfig(ttc_threshold_s=2.5, minimum_duration_s=0.1)


def rho_from_ttc(ttc_s: Any, tau_s: float = P2_FORMAL_CONFIG.tau_s) -> float | None:
    """Map a reliable positive closing TTC to rho; invalid values remain unknown."""
    try:
        value = float(ttc_s)
    except (TypeError, ValueError):
        return None
    if not isfinite(value) or value <= 0 or not isfinite(float(tau_s)) or float(tau_s) <= 0:
        return None
    return exp(-value / float(tau_s))


def extract_formal_source_events(states: pd.DataFrame, config: FormalRiskConfig = P2_FORMAL_CONFIG,
                                 *, return_diagnostics: bool = False):
    """Extract versioned source events without changing historical extractor defaults."""
    result = extract_rear_end_events(
        states,
        provisional_ttc_threshold_s=config.ttc_threshold_s,
        max_gap_s=config.max_gap_s,
        minimum_duration_s=config.minimum_duration_s,
        return_diagnostics=return_diagnostics,
    )
    if return_diagnostics:
        events, reliable, rejected = result
        for frame in (events, reliable):
            if not frame.empty:
                frame["formal_algorithm_version"] = config.algorithm_version
                frame["event_confirm_s"] = [
                    observed_confirmation_time(states, row["original_row_numbers"], config.minimum_duration_s)
                    for _, row in frame.iterrows()
                ]
        return events, reliable, rejected
    events = result
    if not events.empty:
        events = events.copy()
        events["formal_algorithm_version"] = config.algorithm_version
        events["event_confirm_s"] = [
            observed_confirmation_time(states, row["original_row_numbers"], config.minimum_duration_s)
            for _, row in events.iterrows()
        ]
    return events


def observed_confirmation_time(states: pd.DataFrame, member_rows: Iterable[Any], minimum_duration_s: float) -> float:
    """Return the actual observed frame that first completes the required span."""
    if minimum_duration_s <= 0:
        raise ValueError("minimum_duration_s must be positive")
    if "original_row_number" in states.columns:
        members = states[states["original_row_number"].isin(list(member_rows))]
    else:
        members = states.loc[list(member_rows)]
    if members.empty:
        raise ValueError("event member rows are missing from source states")
    members = members.sort_values(["time_s", "frame_id"], kind="stable")
    onset = float(members.iloc[0]["time_s"])
    eligible = members[pd.to_numeric(members["time_s"], errors="coerce") >= onset + minimum_duration_s - 1e-9]
    if eligible.empty:
        raise ValueError("event has no observed confirmation frame")
    return float(eligible.iloc[0]["time_s"])


def contribution_bounds(*, measurement_status: str, in_region: bool | None,
                        ttc_s: Any, reliable: bool = True,
                        tau_s: float = P2_FORMAL_CONFIG.tau_s) -> tuple[float, float, float | None]:
    """Return (lower, upper, rho), preserving not-applicable and unknown semantics."""
    if in_region is False:
        # Spatial exclusion is independently known; measurement quality cannot
        # turn an out-of-region record into an unknown contribution.
        return 0.0, 0.0, None
    if in_region is None:
        return 0.0, 1.0, None
    status = str(measurement_status).lower()
    if not reliable or status in {"invalid", "missing", "not_measurable", "unknown"}:
        return 0.0, 1.0, None
    if status == "not_applicable":
        return 0.0, 0.0, None
    if status != "valid":
        return 0.0, 1.0, None
    rho = rho_from_ttc(ttc_s, tau_s)
    if rho is None:
        return 0.0, 1.0, None
    return rho, rho, rho


def integrate_fixed_window(records: pd.DataFrame, *, window_start_s: float, window_end_s: float,
                           expected_step_s: float = 0.1) -> dict[str, float]:
    """Integrate bounds over the full window with left-observed intervals only."""
    if window_end_s <= window_start_s or expected_step_s <= 0:
        raise ValueError("invalid window or expected step")
    total = float(window_end_s - window_start_s)
    lower = upper = known = observed_pair = 0.0
    if records is None or records.empty:
        return {"lower_integral": 0.0, "upper_integral": total,
                "lower_mean": 0.0, "upper_mean": 1.0,
                "known_time_s": 0.0, "unknown_time_s": total,
                "observed_pair_time_s": 0.0}
    frame = records.sort_values("time_s", kind="stable").reset_index(drop=True)
    times = sorted(set([float(window_start_s), float(window_end_s)] +
                       [float(t) for t in frame["time_s"] if window_start_s <= float(t) <= window_end_s]))
    for a, b in zip(times[:-1], times[1:]):
        if b <= a:
            continue
        left = frame[frame["time_s"] <= a + 1e-9].iloc[-1:]
        if left.empty:
            upper += b - a
            continue
        row = left.iloc[0].to_dict()
        right = frame[frame["time_s"] >= b - 1e-9].iloc[:1]
        same = False
        if not right.empty:
            r = right.iloc[0].to_dict()
            same = (float(r["time_s"]) - float(row["time_s"]) > 0 and
                    float(r["time_s"]) - float(row["time_s"]) <= expected_step_s + 1e-9)
            if "continuous" in row:
                same = same and bool(row["continuous"])
        dt = b - a
        if same:
            lower += float(row.get("lower", 0.0)) * dt
            upper += float(row.get("upper", 1.0)) * dt
            known += dt
        else:
            upper += dt
        if window_start_s <= float(row["time_s"]) < window_end_s:
            observed_pair += dt
    return {"lower_integral": lower, "upper_integral": upper,
            "lower_mean": lower / total, "upper_mean": upper / total,
            "known_time_s": known, "unknown_time_s": total - known,
            "observed_pair_time_s": observed_pair}


def equal_vehicle_average(vehicle_results: Iterable[Mapping[str, float]]) -> dict[str, float]:
    values = list(vehicle_results)
    if not values:
        raise ValueError("fixed target vehicle set is empty")
    return {"lower_mean": sum(float(x["lower_mean"]) for x in values) / len(values),
            "upper_mean": sum(float(x["upper_mean"]) for x in values) / len(values),
            "vehicle_count": float(len(values))}


def did_interval(t11: Mapping[str, float], t10: Mapping[str, float],
                 t01: Mapping[str, float], t00: Mapping[str, float]) -> tuple[float, float]:
    """Conservative interval for (11 - 10 - 01 + 00)."""
    lower = float(t11["lower_mean"]) - float(t10["upper_mean"]) - float(t01["upper_mean"]) + float(t00["lower_mean"])
    upper = float(t11["upper_mean"]) - float(t10["lower_mean"]) - float(t01["lower_mean"]) + float(t00["upper_mean"])
    return lower, upper


def continuity_is_valid(previous: Mapping[str, Any], current: Mapping[str, Any], *, expected_step_s: float = 0.1) -> bool:
    """Check causal adjacency without allowing clock, identity, or gap crossings.

    NGSIM state tables use ``diagnostic_clock_anchor_ms``.  The legacy
    ``diagnostic_clock`` alias remains accepted for small fixtures, but a
    missing clock is always fail-closed.
    """
    def value(row: Mapping[str, Any], *keys: str):
        for key in keys:
            if key in row:
                item = row[key]
                if item is not None and not pd.isna(item):
                    return item
        return None
    prev_clock = value(previous, "diagnostic_clock_anchor_ms", "diagnostic_clock")
    curr_clock = value(current, "diagnostic_clock_anchor_ms", "diagnostic_clock")
    prev_follower = value(previous, "follower_trajectory_id", "trajectory_id", "vehicle_id")
    curr_follower = value(current, "follower_trajectory_id", "trajectory_id", "vehicle_id")
    prev_leader = value(previous, "leader_trajectory_id", "leader_id")
    curr_leader = value(current, "leader_trajectory_id", "leader_id")
    if any(x is None for x in (prev_clock, curr_clock, prev_follower, curr_follower, prev_leader, curr_leader)):
        return False
    scope_keys = ("source_scope", "dataset", "site", "window_id", "source_member", "source_period")
    for key in scope_keys:
        if key in previous or key in current:
            if value(previous, key) is None or value(current, key) is None or value(previous, key) != value(current, key):
                return False
    dt = float(current["time_s"]) - float(previous["time_s"])
    expected_frame_delta = max(1, int(round(expected_step_s / 0.1)))
    return (abs(dt - expected_step_s) <= 1e-9
            and int(current["frame_id"]) - int(previous["frame_id"]) == expected_frame_delta
            and curr_clock == prev_clock
            and curr_follower == prev_follower
            and curr_leader == prev_leader
            and not bool(current.get("identity_break", False))
            and not bool(current.get("observation_gap", False)))
