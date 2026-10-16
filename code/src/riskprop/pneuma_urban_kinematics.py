"""Stage 0.3 pNEUMA urban kinematics calibration.

This module provides data-integrity auditing, reliability flags, descriptive
kinematic statistics (time-weighted and vehicle-equal-weight), sensitivity and
sampling-uncertainty analysis, a Stage 0.5 reference interface adapter, and an
immutable acceptance-package writer for one approved pNEUMA trajectory file.

Scientific boundaries:
- pNEUMA is used only for urban speed, longitudinal acceleration and vehicle
  type composition.  No map matching, leader inference, TTC/DRAC, risk-event
  identification or manual leader QA is performed or reactivated.
- Time-continuity and outlier-masking rules are exploratory candidates only.
  They are never selected by result favourability and never delete raw data.
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from riskprop.calibration import CalibrationContractError, sha256_file
from riskprop.real_trajectory import read_pneuma_wide


QUANTILE_LEVELS = (0.05, 0.25, 0.50, 0.75, 0.95, 0.99)
CONTINUITY_CANDIDATES_S = (0.04, 0.045, 0.05, 0.06, 0.08, 0.10, 0.12, 0.16)
EXPLORATORY_SPEED_SCREEN_MPS = (20.0, 25.0, 30.0, 35.0)
EXPLORATORY_ACCEL_SCREEN_MPS2 = (2.0, 3.0, 4.0, 5.0)
EARTH_RADIUS_M = 6_371_000.0
BOOTSTRAP_REPLICATES = 2000
BOOTSTRAP_SEED = 20261012
ACCEL_BY_SPEED_BINS_MPS = (0.0, 2.0, 5.0, 8.0, 12.0, 18.0, 25.0, float("inf"))
ACCEL_NEAR_ZERO_BAND_MPS2 = 0.05
LOW_SPEED_EXPLORATORY_BAND_MPS = (1.0 / 3.6, 0.5)

AUDIT_OUTPUT_COLUMNS = (
    "raw_index",
    "run_id",
    "vehicle_id",
    "vehicle_type",
    "time_s",
    "latitude",
    "longitude",
    "speed_mps",
    "speed_kmh",
    "longitudinal_accel_mps2",
    "lateral_accel_mps2",
    "traveled_distance_m",
    "average_speed_kmh",
    "parse_ok",
    "parse_error",
    "identity_status",
    "identity_ambiguous",
    "identity_conflict",
    "dt_to_next_s",
    "time_regression_in_raw_order",
    "time_increment_nonpositive",
    "raw_order_time_anomaly",
    "duplicate_time_in_track",
    "time_gap_flag",
)

# Columns whose truthiness disqualifies a state from reliable time weighting
# (fail-closed: parse quality, trajectory identity, raw record order and
# duplicated (track, time) keys).  Absent columns are treated as "not
# evaluated, assumed clean" for backward compatibility with minimal frames.
_RELIABILITY_EXCLUDE_COLUMNS = (
    "parse_ok",
    "identity_ambiguous",
    "raw_order_time_anomaly",
    "duplicate_time_in_track",
)


def _analysis_frame(states: pd.DataFrame) -> pd.DataFrame:
    """Return the canonical analysis view with raw-order interval dt attached.

    Time weighting intervals are defined by *raw record order* (``raw_index``
    within each trajectory, i.e. the order the provider wrote the states), not
    by time-sorted order: sorting must never let a raw-order anomaly regain a
    reliable interval.  The returned frame is sorted exactly like the R1
    analysis order (``vehicle_id, time_s, raw_index``) so that on clean data
    (raw order == time order within every track) all downstream summations
    remain bit-identical to the sealed R1 package.  The attached column
    ``_dt_raw_next`` is the raw-order adjacent interval of each state.
    """

    frame = states.copy()
    if "raw_index" in frame.columns:
        raw_order = frame.sort_values("raw_index", kind="stable")
    else:
        raw_order = frame
    group = raw_order.groupby("vehicle_id", sort=False)
    next_time = group["time_s"].shift(-1)
    same_next = raw_order["vehicle_id"].eq(raw_order["vehicle_id"].shift(-1))
    dt = (next_time - raw_order["time_s"]).where(same_next)
    frame["_dt_raw_next"] = dt
    sort_columns = ["vehicle_id", "time_s"]
    if "raw_index" in frame.columns:
        sort_columns.append("raw_index")
    return frame.sort_values(sort_columns).reset_index(drop=True)


def _reliability_excludes(frame: pd.DataFrame) -> np.ndarray | None:
    """Boolean mask of states disqualified from reliable time weighting."""

    columns = [name for name in _RELIABILITY_EXCLUDE_COLUMNS if name in frame.columns]
    if not columns:
        return None
    unreliable = np.zeros(len(frame), dtype=bool)
    for name in columns:
        values = frame[name]
        if name == "parse_ok":
            # Missing/NaN parse verdicts are treated as not reliably parsed.
            unreliable |= ~values.fillna(False).astype(bool).to_numpy()
        else:
            unreliable |= values.fillna(False).astype(bool).to_numpy()
    return unreliable


def _usable_interval_mask(
    frame: pd.DataFrame,
    values: np.ndarray,
    *,
    tolerance_s: float,
) -> np.ndarray:
    """States whose raw-order interval is usable for time weighting."""

    same_track = frame["vehicle_id"].eq(frame["vehicle_id"].shift(-1)).to_numpy()
    dt = frame["_dt_raw_next"].to_numpy(float)
    usable = (
        same_track
        & np.isfinite(values)
        & (dt > 0)
        & (dt <= tolerance_s)
    )
    unreliable = _reliability_excludes(frame)
    if unreliable is not None:
        usable &= ~unreliable
    return usable


def reliable_exposure_frame(
    states: pd.DataFrame,
    *,
    tolerance_s: float,
    value_column: str | None = None,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Raw-order reliable interval view for plotting and audits.

    Returns the canonical analysis frame with ``_dt`` (usable interval length,
    zero when unusable) plus the boolean usable mask.  ``value_column``
    additionally requires a finite observed value.
    """

    frame = _analysis_frame(states)
    if value_column is None:
        values = np.zeros(len(frame))
    else:
        values = frame[value_column].to_numpy(float)
    usable = _usable_interval_mask(frame, values, tolerance_s=tolerance_s)
    frame = frame.copy()
    frame["_dt"] = np.where(usable, frame["_dt_raw_next"].to_numpy(float), 0.0)
    return frame, usable


def audit_pneuma_source(source_csv: str | Path) -> tuple[pd.DataFrame, dict]:
    """Stream the raw wide CSV with fail-closed per-row parsing.

    The audit unit is the **raw trajectory row**: every source data row is
    retained with its row number, even when ``track_id`` values repeat.
    Duplicate ``track_id`` values across different rows never overwrite each
    other; all their states are flagged ``identity_ambiguous`` (fail-closed,
    excluded from reliable statistics by the weighting mask) and the rejection
    reason is recorded in the audit.  States are never silently merged,
    renamed, interpolated or dropped.

    Returns one row per state (including malformed fields flagged
    ``parse_ok=False``) and a source-level audit dictionary.
    """

    source_csv = Path(source_csv)
    _raise_csv_field_limit()
    import csv as _csv

    records: list[dict[str, object]] = []
    row_records: list[dict[str, object]] = []
    malformed_rows: list[str] = []
    metadata_failures: list[str] = []
    with source_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _csv.reader(handle, delimiter=";")
        header = next(reader, None)
        for row_number, raw in enumerate(reader, start=2):
            values = [value.strip() for value in raw]
            while values and values[-1] == "":
                values.pop()
            track_id = values[0] if values else f"row_{row_number}"
            vehicle_type = values[1] if len(values) > 1 else ""
            parse_ok = True
            parse_error = ""
            traveled_distance = float("nan")
            average_speed = float("nan")
            try:
                traveled_distance = float(values[2])
                average_speed = float(values[3])
            except (IndexError, ValueError):
                parse_ok = False
                parse_error = "unparseable_metadata"
                metadata_failures.append(track_id)
            if len(values) < 4 or (len(values) - 4) % 6:
                parse_ok = False
                parse_error = "incomplete_state_block"
            state_block_count = max((len(values) - 4) // 6, 0)
            row_records.append(
                {
                    "track_id": track_id,
                    "vehicle_type": vehicle_type,
                    "traveled_distance_m": traveled_distance,
                    "average_speed_kmh": average_speed,
                    "source_row_number": row_number,
                    "raw_field_count": len(values),
                    "state_block_count": state_block_count,
                    "row_parse_ok": parse_ok,
                    "row_parse_error": parse_error,
                }
            )
            if parse_error == "incomplete_state_block":
                malformed_rows.append(track_id)
                continue
            for state_offset in range(4, len(values), 6):
                chunk = values[state_offset : state_offset + 6]
                row: dict[str, object] = {
                    "raw_index": len(records),
                    "run_id": "pneuma_d1_0800_0830",
                    "vehicle_id": track_id,
                    "vehicle_type": vehicle_type,
                    "traveled_distance_m": traveled_distance,
                    "average_speed_kmh": average_speed,
                    "source_row_number": row_number,
                }
                field_names = (
                    "latitude",
                    "longitude",
                    "speed_kmh",
                    "longitudinal_accel_mps2",
                    "lateral_accel_mps2",
                    "time_s",
                )
                row_ok = parse_ok
                row_error = parse_error
                for name, raw_value in zip(field_names, chunk, strict=True):
                    try:
                        row[name] = float(raw_value)
                    except ValueError:
                        row[name] = float("nan")
                        row_ok = False
                        row_error = f"unparseable_{name}"
                row["speed_mps"] = (
                    row["speed_kmh"] / 3.6 if np.isfinite(row["speed_kmh"]) else float("nan")
                )
                row["parse_ok"] = bool(row_ok)
                row["parse_error"] = row_error
                records.append(row)
    frame = pd.DataFrame.from_records(records)
    tracks = pd.DataFrame.from_records(row_records)

    # Row-based duplicate / identity audit (no dict key overwriting).
    id_counts = tracks["track_id"].value_counts()
    duplicate_track_ids = sorted(str(k) for k, c in id_counts.items() if c > 1)
    ambiguous_set = set(duplicate_track_ids)
    identity_conflicts: list[dict[str, object]] = []
    conflict_ids: set[str] = set()
    for track_id in duplicate_track_ids:
        rows = tracks.loc[tracks["track_id"] == track_id]
        reasons: list[str] = []
        if rows["vehicle_type"].nunique(dropna=False) > 1:
            reasons.append("vehicle_type_mismatch")
        if (
            rows["traveled_distance_m"].nunique(dropna=False) > 1
            or rows["average_speed_kmh"].nunique(dropna=False) > 1
        ):
            reasons.append("metadata_mismatch")
        if reasons:
            conflict_ids.add(track_id)
            identity_conflicts.append(
                {
                    "track_id": track_id,
                    "source_row_numbers": sorted(int(r) for r in rows["source_row_number"]),
                    "reasons": reasons,
                    "rejection_rule": "identity_ambiguous_fail_closed",
                }
            )
    if len(frame):
        is_ambiguous = frame["vehicle_id"].isin(ambiguous_set)
        frame["identity_status"] = np.where(
            is_ambiguous, "ambiguous_duplicate_track_id", "unique"
        )
        frame["identity_ambiguous"] = is_ambiguous
        frame["identity_conflict"] = frame["vehicle_id"].isin(conflict_ids)
        duplicate_state_keys_count = int(
            frame.duplicated(subset=["vehicle_id", "time_s"], keep=False).sum()
        )
    else:
        duplicate_state_keys_count = 0

    audit = {
        "schema_version": "aad.stage-0-3.source-audit.v2",
        "header": header,
        "raw_track_rows": int(len(tracks)),
        "unique_track_ids": int(tracks["track_id"].nunique()),
        "duplicate_track_ids": duplicate_track_ids,
        "duplicate_track_rows": int(tracks["track_id"].duplicated(keep=False).sum()),
        "identity_conflicts": identity_conflicts,
        "parsed_state_records": int(len(frame)),
        "duplicate_state_keys_count": duplicate_state_keys_count,
        "malformed_tracks": malformed_rows,
        "metadata_failures": metadata_failures,
        "tracks_table": tracks,
        "audit_unit": "raw trajectory row (source_row_number); duplicate ids never merged or renamed",
    }
    return frame, audit


def flag_state_quality(
    states: pd.DataFrame, *, gap_tolerance_s: float | None = None
) -> pd.DataFrame:
    """Add per-state time-quality flags computed in *raw record order*.

    Rows are never removed or altered.  Time continuity (regressions,
    duplicates, non-positive increments) is evaluated on the original record
    order (``raw_index``) **before** any time sorting, so a raw sequence like
    ``0.00 -> 0.08 -> 0.04`` is flagged as a time regression and can never be
    silently repaired by sorting.  ``dt_to_next_s`` is the raw-order adjacent
    interval.  The returned frame is sorted for downstream analysis only;
    ``raw_order_time_anomaly`` / ``duplicate_time_in_track`` states remain
    excluded from reliable time weighting everywhere in this module.
    """

    frame = states.copy()
    if "raw_index" in frame.columns:
        raw_order = frame.sort_values("raw_index", kind="stable")
    else:
        raw_order = frame
    group = raw_order.groupby("vehicle_id", sort=False)
    next_time = group["time_s"].shift(-1)
    prev_time = group["time_s"].shift(1)
    same_next = raw_order["vehicle_id"].eq(raw_order["vehicle_id"].shift(-1))
    same_prev = raw_order["vehicle_id"].eq(raw_order["vehicle_id"].shift(1))
    dt_next = (next_time - raw_order["time_s"]).where(same_next)
    dt_prev = (raw_order["time_s"] - prev_time).where(same_prev)
    frame["dt_to_next_s"] = dt_next
    frame["time_regression_in_raw_order"] = (dt_prev < 0)
    frame["time_increment_nonpositive"] = (dt_prev <= 0)
    frame["raw_order_time_anomaly"] = ((dt_prev <= 0) | (dt_next <= 0))
    frame["duplicate_time_in_track"] = frame.duplicated(
        subset=["vehicle_id", "time_s"], keep=False
    )
    if gap_tolerance_s is None:
        frame["time_gap_flag"] = False
    else:
        frame["time_gap_flag"] = dt_next > float(gap_tolerance_s)
    sort_columns = ["vehicle_id", "time_s"]
    if "raw_index" in frame.columns:
        sort_columns.append("raw_index")
    return frame.sort_values(sort_columns).reset_index(drop=True)


def compute_track_stats(states: pd.DataFrame) -> pd.DataFrame:
    """Per-row coverage, duration and self-summary statistics.

    The audit unit is the raw trajectory row: when ``source_row_number`` is
    available the grouping key is ``(vehicle_id, source_row_number)`` so that
    states of duplicate track ids from different raw rows are never silently
    merged into one trajectory.  Time increments are evaluated in raw record
    order, never on a time-sorted copy.
    """

    frame = states
    if "raw_index" in frame.columns:
        frame = frame.sort_values("raw_index", kind="stable")
    group_keys = ["vehicle_id"]
    if "source_row_number" in frame.columns:
        group_keys.append("source_row_number")
    records = []
    for _, group in frame.groupby(group_keys, sort=False):
        times = group["time_s"].to_numpy(float)
        speeds = group["speed_mps"].to_numpy(float)
        accels = group["longitudinal_accel_mps2"].to_numpy(float)
        finite_speed = np.isfinite(speeds)
        increments = np.diff(times) if len(times) > 1 else np.asarray([], dtype=float)
        record: dict[str, object] = {
            "vehicle_id": group["vehicle_id"].iloc[0],
            "vehicle_type": group["vehicle_type"].iloc[0],
            "state_records": int(len(group)),
            "duration_s": float(times.max() - times.min()) if len(times) else 0.0,
            "time_start_s": float(times.min()),
            "time_end_s": float(times.max()),
            "mean_speed_mps_unweighted": float(np.nanmean(speeds)) if finite_speed.any() else float("nan"),
            "sd_speed_mps_unweighted": float(np.nanstd(speeds)) if finite_speed.sum() > 1 else float("nan"),
            "mean_accel_mps2_unweighted": float(np.nanmean(accels)) if np.isfinite(accels).any() else float("nan"),
            "median_speed_mps_unweighted": float(np.nanmedian(speeds)) if finite_speed.any() else float("nan"),
            "median_accel_mps2_unweighted": float(np.nanmedian(accels)) if np.isfinite(accels).any() else float("nan"),
            "mean_dt_s": float(increments.mean()) if len(increments) else float("nan"),
            "dt_sd_s": float(increments.std()) if len(increments) > 1 else float("nan"),
            "n_nonpositive_increments": int((increments <= 0).sum()) if len(increments) else 0,
            "traveled_distance_m": float(group["traveled_distance_m"].iloc[0]),
            "average_speed_kmh": float(group["average_speed_kmh"].iloc[0]),
        }
        if "source_row_number" in group.columns:
            record["source_row_number"] = int(group["source_row_number"].iloc[0])
        if "identity_status" in group.columns:
            record["identity_status"] = str(group["identity_status"].iloc[0])
        if "identity_ambiguous" in group.columns:
            record["identity_ambiguous"] = bool(group["identity_ambiguous"].iloc[0])
        records.append(record)
    return pd.DataFrame.from_records(records)


def integrate_time_weighted(
    states: pd.DataFrame,
    *,
    value_column: str,
    tolerance_s: float,
    nominal_dt_s: float | None,
) -> dict:
    """Rectangle (left-rule) time weighting over reliable adjacent intervals.

    Intervals are defined by **raw record order** within each trajectory: a
    state at raw position ``i`` represents ``[t_i, t_{i+1_raw})`` when
    ``0 < t_{i+1_raw} - t_i <= tolerance_s`` and neither endpoint is flagged
    by the reliability mask (parse failure, ambiguous identity, raw-order time
    anomaly, duplicated (track, time) key).  Sorting is used only for the
    canonical analysis order and can never let an anomalous observation regain
    a reliable interval.  The final observed state of a track contributes
    zero duration.  ``nominal_dt_s`` is reported for context only and is never
    used to fill gaps.
    """

    frame = _analysis_frame(states)
    dt = frame["_dt_raw_next"].to_numpy(float)
    same_track = frame["vehicle_id"].eq(frame["vehicle_id"].shift(-1)).to_numpy()
    values = frame[value_column].to_numpy(float)
    valid_value = np.isfinite(values)
    valid_interval = same_track & (dt > 0) & (dt <= tolerance_s)
    unreliable = _reliability_excludes(frame)
    if unreliable is not None:
        valid_interval &= ~unreliable
    usable = valid_value & valid_interval
    weights = np.where(usable, dt, 0.0)
    total_time = float(weights.sum())
    masked_values = np.where(usable, values, np.nan)
    result = {
        "value_column": value_column,
        "tolerance_s": float(tolerance_s),
        "nominal_dt_s": nominal_dt_s,
        "states_total": int(len(frame)),
        "states_with_valid_value": int(valid_value.sum()),
        "states_time_weighted": int(usable.sum()),
        "states_excluded_by_gap": int((valid_value & ~valid_interval).sum()),
        "states_excluded_by_time_gap": int(
            (valid_value & same_track & ~valid_interval).sum()
        ),
        "final_states_zero_duration": int(
            (valid_value & ~same_track).sum()
        ),
        "exposure_time_s": total_time,
        "endpoint_rule": "left rectangle over raw record order [t_i, t_i+1_raw); final state zero duration; no gap fill; reliability mask excludes parse/identity/raw-order anomalies",
    }
    if total_time > 0:
        finite = np.isfinite(masked_values)
        w = weights[finite]
        v = masked_values[finite]
        result.update(_weighted_summary(v, w))
    else:
        result.update({key: float("nan") for key in _SUMMARY_KEYS})
    return result


_SUMMARY_KEYS = (
    "mean",
    "sd",
    "p5",
    "p25",
    "p50",
    "p75",
    "p95",
    "p99",
    "min",
    "max",
)


def _weighted_summary(values: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    total = float(weights.sum())
    mean = float((values * weights).sum() / total)
    variance = float((weights * (values - mean) ** 2).sum() / total)
    quantiles = _weighted_quantiles(values, weights, QUANTILE_LEVELS)
    keys = ("p5", "p25", "p50", "p75", "p95", "p99")
    return {
        "mean": mean,
        "sd": float(np.sqrt(max(variance, 0.0))),
        **{name: float(quantile) for name, quantile in zip(keys, quantiles, strict=True)},
        "min": float(values.min()),
        "max": float(values.max()),
    }


def _weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, quantiles: Sequence[float]
) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    total = float(cumulative[-1]) if len(cumulative) else 0.0
    if total <= 0:
        return np.full(len(quantiles), np.nan)
    results = []
    for q in quantiles:
        threshold = q * total
        index = int(np.searchsorted(cumulative, threshold, side="left"))
        index = min(index, len(sorted_values) - 1)
        results.append(sorted_values[index])
    return np.asarray(results, dtype=float)


def compute_descriptive_stats(
    states: pd.DataFrame,
    *,
    value_column: str,
    group_column: str | None = None,
    tolerance_s: float,
    nominal_dt_s: float | None,
) -> pd.DataFrame:
    """Time-weighted descriptive statistics overall or per group."""

    records = []
    groups: list[tuple[str, pd.DataFrame]]
    if group_column is None:
        groups = [("ALL", states)]
    else:
        groups = [(str(key), frame) for key, frame in states.groupby(group_column, sort=True)]
    for label, frame in groups:
        summary = integrate_time_weighted(
            frame,
            value_column=value_column,
            tolerance_s=tolerance_s,
            nominal_dt_s=nominal_dt_s,
        )
        summary["group"] = label
        records.append(summary)
    return pd.DataFrame.from_records(records)


def compute_vehicle_equal_weight_stats(
    track_stats: pd.DataFrame,
    *,
    value_column: str,
    group_column: str | None = None,
) -> pd.DataFrame:
    """Equal-weight summary over per-track statistics (one vote per vehicle)."""

    records = []
    groups: list[tuple[str, pd.DataFrame]]
    if group_column is None:
        groups = [("ALL", track_stats)]
    else:
        groups = [(str(key), frame) for key, frame in track_stats.groupby(group_column, sort=True)]
    for label, frame in groups:
        values = pd.to_numeric(frame[value_column], errors="coerce").to_numpy(float)
        finite = np.isfinite(values)
        values = values[finite]
        record: dict[str, object] = {
            "group": label,
            "value_column": value_column,
            "vehicles_total": int(len(frame)),
            "vehicles_with_finite_stat": int(finite.sum()),
        }
        if len(values):
            quantiles = np.quantile(values, QUANTILE_LEVELS)
            record.update(
                {
                    "mean": float(values.mean()),
                    "sd": float(values.std(ddof=0)),
                    "p5": float(quantiles[0]),
                    "p25": float(quantiles[1]),
                    "p50": float(quantiles[2]),
                    "p75": float(quantiles[3]),
                    "p95": float(quantiles[4]),
                    "p99": float(quantiles[5]),
                    "min": float(values.min()),
                    "max": float(values.max()),
                }
            )
        else:
            record.update({key: float("nan") for key in _SUMMARY_KEYS})
        records.append(record)
    return pd.DataFrame.from_records(records)


def compute_vehicle_type_composition(track_stats: pd.DataFrame) -> pd.DataFrame:
    """Unique-trajectory composition, exposure and per-type coverage."""

    total_tracks = len(track_stats)
    total_records = int(track_stats["state_records"].sum())
    records = []
    for vehicle_type, frame in track_stats.groupby("vehicle_type", sort=True):
        records.append(
            {
                "vehicle_type": vehicle_type,
                "unique_trajectories": int(len(frame)),
                "trajectory_share": float(len(frame) / total_tracks) if total_tracks else float("nan"),
                "state_records": int(frame["state_records"].sum()),
                "state_record_share": float(frame["state_records"].sum() / total_records)
                if total_records
                else float("nan"),
                "total_observed_duration_s": float(frame["duration_s"].sum()),
                "median_track_duration_s": float(frame["duration_s"].median()),
                "median_state_records": float(frame["state_records"].median()),
            }
        )
    return pd.DataFrame.from_records(records)


def compute_kinematic_consistency(states: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Internal-consistency diagnostics between position, speed and acceleration.

    These checks are data diagnostics, not independent physical ground truth.
    Adjacent pairs are taken in **raw record order** (the provider's own
    consecutive records), not in time-sorted order.
    """

    raw = states.copy()
    if "raw_index" in raw.columns:
        raw = raw.sort_values("raw_index", kind="stable")
    group = raw.groupby("vehicle_id", sort=False)
    same_track_next = raw["vehicle_id"].eq(raw["vehicle_id"].shift(-1))
    next_time = group["time_s"].shift(-1)
    dt = (next_time - raw["time_s"]).where(same_track_next)
    next_speed = group["speed_mps"].shift(-1)
    speed_change_accel = ((next_speed - raw["speed_mps"]) / dt).where(
        same_track_next & (dt > 0)
    )
    accel_deviation = (speed_change_accel - raw["longitudinal_accel_mps2"]).abs()

    lat = np.deg2rad(raw["latitude"].to_numpy(float))
    lon = np.deg2rad(raw["longitude"].to_numpy(float))
    next_lat = np.deg2rad(group["latitude"].shift(-1).to_numpy(float))
    next_lon = np.deg2rad(group["longitude"].shift(-1).to_numpy(float))
    dlat = next_lat - lat
    dlon = next_lon - lon
    haversine = 2.0 * EARTH_RADIUS_M * np.arcsin(
        np.sqrt(
            np.clip(
                np.sin(dlat / 2.0) ** 2
                + np.cos(lat) * np.cos(next_lat) * np.sin(dlon / 2.0) ** 2,
                0.0,
                1.0,
            )
        )
    )
    displacement_m = pd.Series(
        np.where(same_track_next.to_numpy(), haversine, np.nan), index=raw.index
    )
    implied_speed = (displacement_m / dt).where(same_track_next & (dt > 0))
    speed_deviation = (implied_speed - raw["speed_mps"]).abs()

    raw["accel_deviation_mps2"] = accel_deviation
    raw["speed_deviation_mps"] = speed_deviation
    raw["displacement_to_next_m"] = displacement_m
    raw["implied_speed_mps"] = implied_speed

    valid_accel = np.isfinite(accel_deviation.to_numpy(float))
    valid_speed = np.isfinite(speed_deviation.to_numpy(float))
    summary = {
        "schema_version": "aad.stage-0-3.kinematic-consistency.v1",
        "adjacent_pairs": int(same_track_next.sum()),
        "adjacent_pair_order": "raw record order",
        "accel_deviation_pairs": int(valid_accel.sum()),
        "accel_deviation_mps2_median": float(np.nanmedian(accel_deviation)) if valid_accel.any() else float("nan"),
        "accel_deviation_mps2_p95": float(np.nanpercentile(accel_deviation, 95)) if valid_accel.any() else float("nan"),
        "accel_deviation_mps2_max": float(np.nanmax(accel_deviation)) if valid_accel.any() else float("nan"),
        "speed_deviation_pairs": int(valid_speed.sum()),
        "speed_deviation_mps_median": float(np.nanmedian(speed_deviation)) if valid_speed.any() else float("nan"),
        "speed_deviation_mps_p95": float(np.nanpercentile(speed_deviation, 95)) if valid_speed.any() else float("nan"),
        "speed_deviation_mps_max": float(np.nanmax(speed_deviation)) if valid_speed.any() else float("nan"),
    }

    # Track-level metadata consistency: reported traveled distance vs sum of
    # haversine displacements; reported average speed vs state-mean speed.
    track_records = []
    for vehicle_id, group_frame in raw.groupby("vehicle_id", sort=False):
        group_frame = group_frame.sort_values("time_s")
        displacements = group_frame["displacement_to_next_m"].dropna()
        integrated_distance = float(displacements.sum())
        reported_distance = float(group_frame["traveled_distance_m"].iloc[0])
        reported_avg_speed_kmh = float(group_frame["average_speed_kmh"].iloc[0])
        mean_state_speed_kmh = float(group_frame["speed_kmh"].mean())
        track_records.append(
            {
                "vehicle_id": vehicle_id,
                "reported_traveled_distance_m": reported_distance,
                "integrated_displacement_m": integrated_distance,
                "distance_deviation_m": abs(reported_distance - integrated_distance),
                "distance_relative_deviation": abs(reported_distance - integrated_distance)
                / max(abs(reported_distance), 1e-9),
                "reported_average_speed_kmh": reported_avg_speed_kmh,
                "mean_state_speed_kmh": mean_state_speed_kmh,
                "average_speed_deviation_kmh": abs(reported_avg_speed_kmh - mean_state_speed_kmh),
            }
        )
    track_consistency = pd.DataFrame.from_records(track_records)
    summary["track_distance_relative_deviation_median"] = float(
        track_consistency["distance_relative_deviation"].median()
    )
    summary["track_distance_relative_deviation_p95"] = float(
        track_consistency["distance_relative_deviation"].quantile(0.95)
    )
    summary["track_avg_speed_deviation_kmh_median"] = float(
        track_consistency["average_speed_deviation_kmh"].median()
    )
    summary["track_avg_speed_deviation_kmh_p95"] = float(
        track_consistency["average_speed_deviation_kmh"].quantile(0.95)
    )
    sort_columns = ["vehicle_id", "time_s"]
    if "raw_index" in raw.columns:
        sort_columns.append("raw_index")
    return raw.sort_values(sort_columns).reset_index(drop=True), summary, track_consistency


def empirical_cdf_arrays(
    states: pd.DataFrame,
    *,
    value_column: str,
    tolerance_s: float,
    group_column: str | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    """Weighted empirical CDF coordinates per group for plotting and export."""

    frame = _analysis_frame(states)
    values = frame[value_column].to_numpy(float)
    usable = _usable_interval_mask(frame, values, tolerance_s=tolerance_s)
    dt_values = frame["_dt_raw_next"].to_numpy(float)
    frame = frame.loc[usable].copy()
    frame["_w"] = dt_values[usable]
    result: dict[str, dict[str, np.ndarray]] = {}
    groups = [("ALL", frame)] if group_column is None else list(frame.groupby(group_column, sort=True))
    for label, group_frame in groups:
        v = group_frame[value_column].to_numpy(float)
        w = group_frame["_w"].to_numpy(float)
        order = np.argsort(v, kind="stable")
        v_sorted = v[order]
        w_sorted = w[order]
        cumulative = np.cumsum(w_sorted)
        total = float(cumulative[-1]) if len(cumulative) else 0.0
        result[str(label)] = {
            "x": v_sorted,
            "cdf": cumulative / total if total else np.asarray([]),
            "total_time_s": total,
        }
    return result


def continuity_sensitivity(
    states: pd.DataFrame,
    *,
    tolerances_s: Sequence[float] = CONTINUITY_CANDIDATES_S,
) -> pd.DataFrame:
    """Exposure retained under each candidate continuity tolerance."""

    records = []
    for tolerance in tolerances_s:
        speed = integrate_time_weighted(
            states, value_column="speed_mps", tolerance_s=tolerance, nominal_dt_s=None
        )
        records.append(
            {
                "tolerance_s": float(tolerance),
                "states_time_weighted": speed["states_time_weighted"],
                "exposure_time_s": speed["exposure_time_s"],
                "speed_mean_mps": speed["mean"],
                "speed_p50_mps": speed["p50"],
                "states_excluded_by_gap": speed["states_excluded_by_gap"],
            }
        )
    return pd.DataFrame.from_records(records)


def extreme_value_sensitivity(
    states: pd.DataFrame,
    *,
    tolerance_s: float,
    speed_screens_mps: Sequence[float] = EXPLORATORY_SPEED_SCREEN_MPS,
    accel_screens_mps2: Sequence[float] = EXPLORATORY_ACCEL_SCREEN_MPS2,
) -> pd.DataFrame:
    """Exploratory masking sensitivity; raw values are never deleted."""

    records = []
    for screen in speed_screens_mps:
        masked = states.loc[states["speed_mps"] <= screen].reset_index(drop=True)
        summary = integrate_time_weighted(
            masked, value_column="speed_mps", tolerance_s=tolerance_s, nominal_dt_s=None
        )
        records.append(
            {
                "screen": f"speed<={screen:.1f}mps",
                "states_remaining": int(len(masked)),
                "exposure_time_s": summary["exposure_time_s"],
                "mean": summary["mean"],
                "p95": summary["p95"],
                "max": summary["max"],
            }
        )
    for screen in accel_screens_mps2:
        masked = states.loc[states["longitudinal_accel_mps2"].abs() <= screen].reset_index(drop=True)
        summary = integrate_time_weighted(
            masked,
            value_column="longitudinal_accel_mps2",
            tolerance_s=tolerance_s,
            nominal_dt_s=None,
        )
        records.append(
            {
                "screen": f"|accel|<={screen:.1f}mps2",
                "states_remaining": int(len(masked)),
                "exposure_time_s": summary["exposure_time_s"],
                "mean": summary["mean"],
                "p95": summary["p95"],
                "max": summary["max"],
            }
        )
    return pd.DataFrame.from_records(records)


def bootstrap_track_intervals(
    track_stats: pd.DataFrame,
    *,
    value_column: str,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
    group_column: str | None = None,
) -> pd.DataFrame:
    """Nonparametric percentile bootstrap resampling complete trajectories."""

    rng = np.random.default_rng(seed)
    records = []
    groups: list[tuple[str, pd.DataFrame]]
    if group_column is None:
        groups = [("ALL", track_stats)]
    else:
        groups = [(str(key), frame) for key, frame in track_stats.groupby(group_column, sort=True)]
    for label, frame in groups:
        values = pd.to_numeric(frame[value_column], errors="coerce").to_numpy(float)
        values = values[np.isfinite(values)]
        n = len(values)
        record: dict[str, object] = {
            "group": label,
            "value_column": value_column,
            "vehicles": int(n),
            "replicates": int(replicates),
        }
        if n == 0:
            record.update({"mean_ci_low": float("nan"), "mean_ci_high": float("nan"),
                           "median_ci_low": float("nan"), "median_ci_high": float("nan")})
        else:
            sample_index = rng.integers(0, n, size=(replicates, n))
            samples = values[sample_index]
            means = samples.mean(axis=1)
            medians = np.median(samples, axis=1)
            record.update(
                {
                    "point_mean": float(values.mean()),
                    "point_median": float(np.median(values)),
                    "mean_ci_low": float(np.quantile(means, 0.025)),
                    "mean_ci_high": float(np.quantile(means, 0.975)),
                    "median_ci_low": float(np.quantile(medians, 0.025)),
                    "median_ci_high": float(np.quantile(medians, 0.975)),
                }
            )
        records.append(record)
    return pd.DataFrame.from_records(records)


def time_weighted_bootstrap(
    states: pd.DataFrame,
    *,
    value_column: str,
    tolerance_s: float,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    """Cluster bootstrap of the time-weighted mean by resampling whole tracks."""

    frame = _analysis_frame(states)
    values = frame[value_column].to_numpy(float)
    usable = _usable_interval_mask(frame, values, tolerance_s=tolerance_s)
    dt_values = frame["_dt_raw_next"].to_numpy(float)
    frame = frame.loc[usable].copy()
    frame["_dt"] = dt_values[usable]
    track_ids = frame["vehicle_id"].unique()
    sums = (frame[value_column] * frame["_dt"]).groupby(frame["vehicle_id"], sort=False).sum()
    exposure = frame["_dt"].groupby(frame["vehicle_id"], sort=False).sum()
    track_sums = sums.to_numpy(float)
    track_exposure = exposure.to_numpy(float)
    point = float(track_sums.sum() / track_exposure.sum()) if track_exposure.sum() > 0 else float("nan")
    rng = np.random.default_rng(seed)
    n = len(track_ids)
    estimates = []
    for _ in range(replicates):
        index = rng.integers(0, n, size=n)
        total_exposure = float(track_exposure[index].sum())
        if total_exposure <= 0:
            continue
        estimates.append(float(track_sums[index].sum() / total_exposure))
    estimates_arr = np.asarray(estimates)
    return {
        "value_column": value_column,
        "tolerance_s": float(tolerance_s),
        "vehicles": int(n),
        "replicates": int(replicates),
        "point_estimate": point,
        "ci_low": float(np.quantile(estimates_arr, 0.025)) if len(estimates_arr) else float("nan"),
        "ci_high": float(np.quantile(estimates_arr, 0.975)) if len(estimates_arr) else float("nan"),
        "bootstrap_sd": float(estimates_arr.std()) if len(estimates_arr) else float("nan"),
    }


def speed_state_shares(
    states: pd.DataFrame,
    *,
    tolerance_s: float,
    low_speed_threshold_mps: float = 1.0 / 3.6,
    near_stop_threshold_mps: float = 0.5,
    high_speed_threshold_mps: float = 16.67,
) -> pd.DataFrame:
    """Time-weighted shares of low-speed, near-stop and high-speed states.

    Thresholds are exploratory descriptive candidates, not approved quality or
    safety classifications.
    """

    frame = _analysis_frame(states)
    values = frame["speed_mps"].to_numpy(float)
    usable = _usable_interval_mask(frame, values, tolerance_s=tolerance_s)
    dt_values = frame["_dt_raw_next"].to_numpy(float)
    frame = frame.loc[usable].copy()
    frame["_dt"] = dt_values[usable]
    records = []
    for label, group_frame in [("ALL", frame), *list(frame.groupby("vehicle_type", sort=True))]:
        total = float(group_frame["_dt"].sum())
        v = group_frame["speed_mps"].to_numpy(float)
        w = group_frame["_dt"].to_numpy(float)
        records.append(
            {
                "group": label,
                "exposure_time_s": total,
                "low_speed_share": float(w[v < low_speed_threshold_mps].sum() / total) if total else float("nan"),
                "near_stop_share": float(w[v < near_stop_threshold_mps].sum() / total) if total else float("nan"),
                "high_speed_share": float(w[v >= high_speed_threshold_mps].sum() / total) if total else float("nan"),
                "low_speed_threshold_mps": low_speed_threshold_mps,
                "near_stop_threshold_mps": near_stop_threshold_mps,
                "high_speed_threshold_mps": high_speed_threshold_mps,
            }
        )
    return pd.DataFrame.from_records(records)


def acceleration_state_shares(
    states: pd.DataFrame,
    *,
    tolerance_s: float,
    near_zero_band_mps2: float = ACCEL_NEAR_ZERO_BAND_MPS2,
) -> pd.DataFrame:
    """Time-weighted shares of accelerating / decelerating / near-zero states."""

    frame = _analysis_frame(states)
    values = frame["longitudinal_accel_mps2"].to_numpy(float)
    usable = _usable_interval_mask(frame, values, tolerance_s=tolerance_s)
    dt_values = frame["_dt_raw_next"].to_numpy(float)
    frame = frame.loc[usable].copy()
    frame["_dt"] = dt_values[usable]
    records = []
    for label, group_frame in [("ALL", frame), *list(frame.groupby("vehicle_type", sort=True))]:
        total = float(group_frame["_dt"].sum())
        a = group_frame["longitudinal_accel_mps2"].to_numpy(float)
        w = group_frame["_dt"].to_numpy(float)
        records.append(
            {
                "group": label,
                "exposure_time_s": total,
                "accelerating_share": float(w[a > near_zero_band_mps2].sum() / total) if total else float("nan"),
                "decelerating_share": float(w[a < -near_zero_band_mps2].sum() / total) if total else float("nan"),
                "near_zero_share": float(w[np.abs(a) <= near_zero_band_mps2].sum() / total) if total else float("nan"),
                "near_zero_band_mps2": near_zero_band_mps2,
            }
        )
    return pd.DataFrame.from_records(records)


def acceleration_by_speed_stratum(
    states: pd.DataFrame,
    *,
    tolerance_s: float,
    bins_mps: Sequence[float] = ACCEL_BY_SPEED_BINS_MPS,
) -> pd.DataFrame:
    """Time-weighted conditional acceleration distribution per speed stratum."""

    frame = _analysis_frame(states)
    values = frame["speed_mps"].to_numpy(float)
    usable = _usable_interval_mask(frame, values, tolerance_s=tolerance_s)
    usable &= np.isfinite(frame["longitudinal_accel_mps2"].to_numpy(float))
    dt_values = frame["_dt_raw_next"].to_numpy(float)
    frame = frame.loc[usable].copy()
    frame["_dt"] = dt_values[usable]
    labels = []
    bounds = list(bins_mps)
    for low, high in zip(bounds[:-1], bounds[1:], strict=True):
        labels.append(f"[{low:g},{high:g})")
    frame["_speed_stratum"] = pd.cut(frame["speed_mps"], bins=bounds, right=False, labels=labels)
    records = []
    for stratum, group_frame in frame.groupby("_speed_stratum", observed=False, sort=True):
        v = group_frame["longitudinal_accel_mps2"].to_numpy(float)
        w = group_frame["_dt"].to_numpy(float)
        total = float(w.sum())
        record = {
            "speed_stratum_mps": str(stratum),
            "states": int(len(group_frame)),
            "exposure_time_s": total,
        }
        if total > 0:
            record.update(_weighted_summary(v, w))
        else:
            record.update({key: float("nan") for key in _SUMMARY_KEYS})
        records.append(record)
    return pd.DataFrame.from_records(records)


def derive_state_quality_status(states: pd.DataFrame) -> pd.Series:
    """Per-state quality label derived from the actual audit flags.

    Priority: parse failure > ambiguous identity > raw-order time anomaly >
    duplicated (track, time) key > reliably parsed observation.  States with an
    unreliable time interval (gap to the next raw record, or final state with
    no next record) are still ``raw_parsed`` observations; their reduced
    statistical weight is expressed by ``time_weighting_eligible`` instead of
    being conflated with observation quality.
    """

    status = pd.Series("raw_parsed", index=states.index, dtype="object")
    conditions: list[pd.Series] = []
    labels: list[str] = []
    if "parse_ok" in states.columns:
        conditions.append(~states["parse_ok"].fillna(False).astype(bool))
        labels.append("parse_failed")
    if "identity_ambiguous" in states.columns:
        conditions.append(states["identity_ambiguous"].fillna(False).astype(bool))
        labels.append("identity_ambiguous")
    if "raw_order_time_anomaly" in states.columns:
        conditions.append(states["raw_order_time_anomaly"].fillna(False).astype(bool))
        labels.append("raw_time_anomaly")
    if "duplicate_time_in_track" in states.columns:
        conditions.append(states["duplicate_time_in_track"].fillna(False).astype(bool))
        labels.append("duplicate_time")
    if conditions:
        status = pd.Series(
            np.select(
                [condition.to_numpy() for condition in conditions],
                labels,
                default="raw_parsed",
            ),
            index=states.index,
            dtype="object",
        )
    return status


def build_stage_0_5_reference_states(
    states: pd.DataFrame,
    *,
    quality_status: str | None = None,
    gap_tolerance_s: float | None = None,
) -> pd.DataFrame:
    """Standardized pNEUMA state table for the Stage 0.5 reference interface.

    ``quality_status`` reflects the *per-state* audit result: when ``None`` it
    is derived from the parse / identity / raw-order flags on each state; an
    explicit string is still accepted for backward compatibility but must be
    understood as an operator assertion, not a measured status.
    ``time_weighting_eligible`` is taken from the precomputed column when
    present; otherwise it is derived fail-closed from the same flags plus the
    raw-order interval (``0 < dt_to_next_s <= gap_tolerance_s``).  Missing,
    anomalous or non-evaluable states are traceable through these columns and
    are never silently defaulted to reliable.
    """

    if quality_status is None:
        flag_columns = [
            name
            for name in ("parse_ok", "identity_ambiguous", "raw_order_time_anomaly", "duplicate_time_in_track")
            if name in states.columns
        ]
        if not flag_columns:
            raise CalibrationContractError(
                "build_stage_0_5_reference_states: states carry no parse/identity/"
                "raw-order quality flags, so per-state quality_status cannot be "
                "derived; pass audited states or an explicit quality_status"
            )
        quality = derive_state_quality_status(states)
    else:
        quality = pd.Series(quality_status, index=states.index, dtype="object")

    if "time_weighting_eligible" in states.columns:
        eligible = states["time_weighting_eligible"].astype(bool)
    else:
        if "dt_to_next_s" not in states.columns or gap_tolerance_s is None:
            raise CalibrationContractError(
                "build_stage_0_5_reference_states: time_weighting_eligible cannot "
                "be derived without dt_to_next_s and gap_tolerance_s; refusing to "
                "default states to reliable"
            )
        eligible = (
            states["dt_to_next_s"].gt(0)
            & states["dt_to_next_s"].le(float(gap_tolerance_s))
        )
        for name in ("parse_ok", "identity_ambiguous", "raw_order_time_anomaly", "duplicate_time_in_track"):
            if name in states.columns:
                if name == "parse_ok":
                    eligible &= states[name].fillna(False).astype(bool)
                else:
                    eligible &= ~states[name].fillna(False).astype(bool)

    reference = pd.DataFrame(
        {
            "dataset": "pNEUMA",
            "site": "Athens-d1",
            "window_id": "20181101_d1_0800_0830",
            "vehicle_id": states["vehicle_id"].astype("string"),
            "vehicle_type": states["vehicle_type"].astype("string"),
            "time_s": pd.to_numeric(states["time_s"], errors="coerce"),
            "speed_mps": pd.to_numeric(states["speed_mps"], errors="coerce"),
            "acceleration_mps2": pd.to_numeric(
                states["longitudinal_accel_mps2"], errors="coerce"
            ),
            "quality_status": quality.astype("string"),
            "time_weighting_eligible": eligible.astype(bool),
            "source_file_sha256": states.get("source_file_sha256", pd.Series(pd.NA, index=states.index)),
        }
    )
    return reference.reset_index(drop=True)


def audit_sampling_balance(
    sampled: pd.DataFrame,
    reference: pd.DataFrame,
    *,
    group_column: str = "vehicle_type",
) -> dict:
    """Compare stratum shares and trajectory retention between sample and reference."""

    if group_column not in sampled.columns or group_column not in reference.columns:
        return {"available": False, "reason": f"{group_column} missing"}
    ref_states = reference.groupby(group_column).size()
    sam_states = sampled.groupby(group_column).size()
    ref_tracks = reference.groupby(group_column)["vehicle_id"].nunique()
    sam_tracks = sampled.groupby(group_column)["vehicle_id"].nunique()
    strata = sorted(set(ref_states.index) | set(sam_states.index))
    rows = []
    for stratum in strata:
        rows.append(
            {
                "stratum": stratum,
                "reference_state_share": float(ref_states.get(stratum, 0) / ref_states.sum()),
                "sample_state_share": float(sam_states.get(stratum, 0) / sam_states.sum()) if len(sampled) else 0.0,
                "reference_trajectories": int(ref_tracks.get(stratum, 0)),
                "sample_trajectories": int(sam_tracks.get(stratum, 0)),
                "trajectory_retention": float(sam_tracks.get(stratum, 0) / ref_tracks.get(stratum, 0))
                if ref_tracks.get(stratum, 0)
                else float("nan"),
            }
        )
    table = pd.DataFrame.from_records(rows)
    return {
        "available": True,
        "max_state_share_deviation": float(
            (table["sample_state_share"] - table["reference_state_share"]).abs().max()
        ),
        "max_trajectory_loss_share": float(1.0 - table["trajectory_retention"].min()),
        "table": table,
    }


def write_acceptance_package(
    *,
    output_dir: str | Path,
    config: Mapping[str, object],
    source_csv: str | Path,
    tables: Mapping[str, pd.DataFrame],
    figures: Mapping[str, Path],
    report_markdown: str,
    audit: Mapping[str, object],
    code_files: Sequence[str | Path],
    started_monotonic: float,
    started_wall_utc: str,
) -> Path:
    """Write the immutable Stage 0.3 acceptance package with checksums."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    config = dict(config)
    config_payload = dict(config)
    config_payload.setdefault("schema_version", "aad.stage-0-3.config.v1")
    (output_dir / "config.json").write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for name, table in tables.items():
        if name.endswith(".parquet"):
            table.to_parquet(output_dir / name, index=False)
        elif name.endswith(".csv"):
            table.to_csv(output_dir / name, index=False)
        elif name.endswith(".json"):
            payload = table if isinstance(table, (dict, list)) else table.to_dict("records")
            (output_dir / name).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
        else:
            raise CalibrationContractError(f"unsupported table output: {name}")
    for name, figure_path in figures.items():
        target = output_dir / name
        target.write_bytes(Path(figure_path).read_bytes())
    (output_dir / "report.md").write_text(report_markdown, encoding="utf-8")

    provenance = {
        "schema_version": "aad.stage-0-3.provenance.v1",
        "created_utc": started_wall_utc,
        "python": sys.version,
        "platform": sys.platform,
        "inputs": {
            str(Path(source_csv).as_posix()): sha256_file(source_csv),
        },
        "code_sha256": {
            str(Path(path).as_posix()): sha256_file(path) for path in code_files
        },
        "runtime_seconds": time.monotonic() - started_monotonic,
    }
    (output_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit_payload = dict(audit)
    audit_payload.setdefault("schema_version", "aad.stage-0-3.audit.v1")
    (output_dir / "audit.json").write_text(
        json.dumps(audit_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    manifest = {
        "schema_version": "aad.stage-0-3.manifest.v1",
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in files
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files.append(manifest_path)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_dir


def _raise_csv_field_limit() -> None:
    import csv as _csv

    limit = sys.maxsize
    while True:
        try:
            _csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10
