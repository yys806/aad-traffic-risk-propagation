"""Versioned formal Stage 0.2 risk measurement semantics.

This module is intentionally separate from the historical engineering baseline.
It provides the approved P2 event configuration, causal confirmation checks,
rho mapping, bounded contribution semantics, fixed-window integration, and DID
interval arithmetic.  It does not choose target regions, cohorts, windows, or
message de-duplication rules.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
from math import exp, isfinite
from typing import Any, Iterable, Mapping

import pandas as pd

from .ngsim_risk_calibration import extract_rear_end_events


@dataclass(frozen=True)
class FormalRiskConfig:
    schema_version: str = "stage_0_2.formal_risk_measurement.config.v1"
    algorithm_version: str = "stage_0_2.formal_risk_measurement.v2"
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


SOURCE_KEYS = ("dataset", "site", "window_id", "source_member", "source_period")
PAIR_KEYS = (*SOURCE_KEYS, "trajectory_id", "leader_trajectory_id")


def extract_formal_source_events(states: pd.DataFrame, config: FormalRiskConfig = P2_FORMAL_CONFIG,
                                 *, return_diagnostics: bool = False):
    """Versioned 100 ms NGSIM wrapper; historical extractor remains untouched."""
    missing = set((*PAIR_KEYS, "original_row_number", "diagnostic_clock_anchor_ms",
                   "global_time_ms", "frame_id", "time_s")) - set(states.columns)
    if missing:
        raise ValueError(f"missing formal event identity fields: {sorted(missing)}")
    if states.duplicated([*SOURCE_KEYS, "original_row_number"]).any():
        raise ValueError("ambiguous original row in source scope")
    raw, reliable, rejected = extract_rear_end_events(
        states, provisional_ttc_threshold_s=config.ttc_threshold_s,
        max_gap_s=config.max_gap_s, minimum_duration_s=config.minimum_duration_s,
        return_diagnostics=True)
    # Index original rows once per full source scope, avoiding per-event scans.
    indexed_states = {key: group.set_index("original_row_number", drop=False)
                      for key, group in states.groupby(list(SOURCE_KEYS), dropna=False, sort=False)}
    sequences = {}
    positions = {}
    for key, group in states.groupby([*SOURCE_KEYS, "trajectory_id"], dropna=False, sort=False):
        ordered = group.sort_values(["time_s", "frame_id"]).reset_index(drop=True)
        sequences[key] = ordered
        positions[key] = dict(zip(ordered.original_row_number, ordered.index))
    for frame, require_reliable in ((raw, False), (reliable, True)):
        confirmations, reasons = [], []
        for _, event in frame.iterrows():
            ids = list(event.original_row_numbers)
            selected = indexed_states[tuple(event[k] for k in SOURCE_KEYS)].loc[ids].copy()
            if len(selected) != len(ids):
                raise ValueError("ambiguous or missing event member row in source scope")
            for key in SOURCE_KEYS:
                if not selected[key].eq(event[key]).all():
                    raise ValueError("event member crosses source scope")
            if require_reliable:
                full_records = selected.sort_values(["time_s", "frame_id"]).to_dict("records")
                if not all(continuity_is_valid(a, b) for a, b in zip(full_records[:-1], full_records[1:])):
                    raise ValueError("reliable event crosses a full-sequence boundary")
                confirm = observed_confirmation_time(selected, event.original_row_numbers,
                    config.minimum_duration_s, event_scope=event,
                    ttc_threshold_s=config.ttc_threshold_s)
            else:
                confirm = None  # rejected candidates never authorize messages
            confirmations.append(confirm)
            # The historical extractor has already split at identity, clock,
            # gap and threshold boundaries.  The member end is therefore the
            # observed exit boundary; no future row is used for confirmation.
            key = tuple(event[k] for k in (*SOURCE_KEYS, "trajectory_id"))
            ordered = sequences[key]
            last = selected.sort_values(["time_s", "frame_id"]).iloc[-1].to_dict()
            next_pos = positions[key][last["original_row_number"]] + 1
            if next_pos == len(ordered):
                reason = "observation_end_right_censored"
            else:
                following = ordered.iloc[next_pos].to_dict()
                if following["leader_trajectory_id"] != last["leader_trajectory_id"]:
                    reason = "leader_switch_unknown_risk"
                elif not continuity_is_valid(last, following):
                    reason = "continuity_break_unknown_risk"
                elif following.get("measurement_status") != "valid" or not _boolean_evidence(following, "ttc_valid", True):
                    reason = "measurement_unavailable_unknown_risk"
                elif rho_from_ttc(following.get("ttc_s")) is not None and float(following["ttc_s"]) >= config.ttc_threshold_s:
                    reason = "observed_threshold_exit"
                else:
                    reason = "segment_boundary_unknown_risk"
            reasons.append(reason)
        frame["event_confirm_s"] = confirmations
        frame["message_earliest_generation_s"] = confirmations
        frame["exit_reason"] = reasons
        frame["formal_algorithm_version"] = config.algorithm_version
    return (raw, reliable, rejected) if return_diagnostics else reliable


def observed_confirmation_time(states: pd.DataFrame, member_rows: Iterable[Any], minimum_duration_s: float,
                               *, event_scope: Mapping[str, Any] | None = None,
                               ttc_threshold_s: float = 2.0) -> float:
    """Actual online confirmation after unique scoped membership and causal links."""
    if not isfinite(minimum_duration_s) or minimum_duration_s <= 0:
        raise ValueError("minimum duration must be finite and positive")
    ids = list(member_rows)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("empty or duplicate member rows")
    members = states
    if event_scope is not None:
        for key in PAIR_KEYS:
            if key not in event_scope or key not in states:
                raise ValueError(f"missing event scope {key}")
            members = members[members[key].eq(event_scope[key])]
    if "original_row_number" not in members:
        raise ValueError("original_row_number required")
    members = members[members.original_row_number.isin(ids)]
    if len(members) != len(ids) or members.original_row_number.nunique() != len(ids):
        raise ValueError("missing or ambiguous scoped event members")
    members = members.sort_values(["time_s", "frame_id"])
    records = members.to_dict("records")
    onset = float(records[0]["time_s"])
    confirmation = None
    for i, row in enumerate(records):
        if not _reliable_record(row) or row.get("measurement_status") != "valid" or not bool(row.get("ttc_valid", False)):
            raise ValueError("unreliable event member")
        ttc = row.get("ttc_s")
        if rho_from_ttc(ttc) is None or float(ttc) >= ttc_threshold_s:
            raise ValueError("non-risk event member")
        if i and not continuity_is_valid(records[i-1], row):
            raise ValueError("event crosses continuity boundary")
        if confirmation is None and float(row["time_s"]) - onset + 1e-9 >= minimum_duration_s:
            confirmation = float(row["time_s"])
    if confirmation is not None:
        return confirmation
    raise ValueError("no actual confirmation frame")


def contribution_bounds(*, measurement_status: str, in_region: bool | None,
                        ttc_s: Any, reliable: bool = True,
                        region_reliable: bool = True, measurement_reliable: bool | None = None,
                        tau_s: float = P2_FORMAL_CONFIG.tau_s) -> tuple[float, float, float | None]:
    """Independent spatial and measurement reliability; legacy reliable aliases latter."""
    if in_region is None or pd.isna(in_region) or not isinstance(in_region, (bool, np.bool_)) or not region_reliable:
        return 0., 1., None
    if not bool(in_region):
        return 0., 0., None
    measurement_reliable = reliable if measurement_reliable is None else measurement_reliable
    if not measurement_reliable:
        return 0., 1., None
    if str(measurement_status).lower() == "not_applicable":
        return 0., 0., None
    rho = rho_from_ttc(ttc_s, tau_s) if str(measurement_status).lower() == "valid" else None
    return (rho, rho, rho) if rho is not None else (0., 1., None)


def _validate_bounds(lower: float, upper: float) -> None:
    if not (isfinite(lower) and isfinite(upper) and 0 <= lower <= upper <= 1):
        raise ValueError("contribution must satisfy finite 0 <= lower <= upper <= 1")


def integrate_fixed_window(records: pd.DataFrame, *, window_start_s: float, window_end_s: float,
                           expected_step_s: float = 0.1, expected_frame_delta: int = 1) -> dict[str, float]:
    """Full denominator; left observed value only on independently proven links.

    Edge clips are allowed within two bracketing observations. No extension
    before the first/after the last observation. Duplicate times are rejected,
    not silently combined. Missing continuity evidence remains [0,1].
    """
    if not all(isfinite(x) for x in (window_start_s, window_end_s, expected_step_s)) or window_end_s <= window_start_s or expected_step_s <= 0:
        raise ValueError("invalid fixed window")
    total = window_end_s - window_start_s
    lower, upper, covered, unknown = 0., total, 0., total
    if records is not None and not records.empty:
        for row in records.to_dict("records"):
            if not isfinite(float(row["time_s"])):
                raise ValueError("nonfinite observation timestamp")
            _validate_bounds(float(row["lower"]), float(row["upper"]))
        if records.time_s.duplicated().any():
            raise ValueError("duplicate observation timestamps")
        rows = records.sort_values("time_s", kind="stable").to_dict("records")
        for left, right in zip(rows[:-1], rows[1:]):
            start = max(float(left["time_s"]), window_start_s)
            end = min(float(right["time_s"]), window_end_s)
            if end <= start or not continuity_is_valid(left, right, expected_step_s=expected_step_s,
                                                        expected_frame_delta=expected_frame_delta):
                continue
            dt = end-start
            lo, hi = float(left["lower"]), float(left["upper"])
            lower += dt*lo
            upper -= dt*(1-hi)
            covered += dt
            if lo == hi:
                unknown -= dt
    return {"lower_integral":lower, "upper_integral":upper,
            "lower_mean":lower/total, "upper_mean":upper/total,
            "known_time_s":total-unknown, "unknown_time_s":unknown,
            "observed_pair_time_s":covered, "fixed_window_s":total}


def equal_vehicle_average(vehicle_results: Iterable[Mapping[str, float]]) -> dict[str, float]:
    values = list(vehicle_results)
    if not values:
        raise ValueError("fixed target vehicle set is empty")
    for value in values:
        _validate_bounds(float(value["lower_mean"]), float(value["upper_mean"]))
    return {"lower_mean": sum(float(x["lower_mean"]) for x in values) / len(values),
            "upper_mean": sum(float(x["upper_mean"]) for x in values) / len(values),
            "vehicle_count": float(len(values))}


def did_interval(t11: Mapping[str, float], t10: Mapping[str, float],
                 t01: Mapping[str, float], t00: Mapping[str, float]) -> tuple[float, float]:
    """Conservative interval for (11 - 10 - 01 + 00)."""
    for value in (t11, t10, t01, t00):
        _validate_bounds(float(value["lower_mean"]), float(value["upper_mean"]))
    lower = float(t11["lower_mean"]) - float(t10["upper_mean"]) - float(t01["upper_mean"]) + float(t00["lower_mean"])
    upper = float(t11["upper_mean"]) - float(t10["lower_mean"]) - float(t01["lower_mean"]) + float(t00["upper_mean"])
    return lower, upper


def _present(row: Mapping[str, Any], key: str) -> bool:
    return key in row and row[key] is not None and not pd.isna(row[key])


def _reliable_record(row: Mapping[str, Any]) -> bool:
    return (all(_boolean_evidence(row, k, False) for k in
                ("identity_uncertain", "leader_identity_uncertain"))
            and _boolean_evidence(row, "leader_matched", True))


def _boolean_evidence(row: Mapping[str, Any], key: str, expected: bool) -> bool:
    value = row.get(key)
    return isinstance(value, (bool, np.bool_)) and bool(value) == expected


def continuity_is_valid(previous: Mapping[str, Any], current: Mapping[str, Any], *,
                        expected_step_s: float = 0.1, expected_frame_delta: int = 1) -> bool:
    """Fail-closed native-state link; cadence and frame step are explicit.

    A 200 ms native simulator can use frame step 1; decimated NGSIM uses 2
    and additionally needs an independent audit of the discarded 100 ms link.
    """
    if not isfinite(expected_step_s) or expected_step_s <= 0 or expected_frame_delta < 1:
        raise ValueError("invalid cadence")
    required = (*PAIR_KEYS, "diagnostic_clock_anchor_ms", "global_time_ms", "time_s", "frame_id")
    if not all(_present(row,k) for row in (previous,current) for k in required):
        return False
    if not all(previous[k] == current[k] for k in (*PAIR_KEYS, "diagnostic_clock_anchor_ms")):
        return False
    if not all(_reliable_record(row) for row in (previous,current)):
        return False
    if not all(_boolean_evidence(current,k,False) for k in ("identity_break", "observation_gap")):
        return False
    try:
        if not all(isfinite(float(row[k])) for row in (previous,current)
                   for k in ("diagnostic_clock_anchor_ms", "global_time_ms", "time_s", "frame_id")):
            return False
        dt = float(current["time_s"]) - float(previous["time_s"])
        ms = float(current["global_time_ms"]) - float(previous["global_time_ms"])
        frame_delta = float(current["frame_id"]) - float(previous["frame_id"])
        return (isfinite(dt) and abs(dt-expected_step_s) <= 1e-9
                and abs(ms-expected_step_s*1000) <= 1e-6
                and frame_delta == expected_frame_delta)
    except (ValueError, TypeError):
        return False
