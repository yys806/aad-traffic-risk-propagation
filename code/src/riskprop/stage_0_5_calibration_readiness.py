"""Stage 0.5.4-A calibration-readiness audit.

This module answers whether the Stage 0.5.4-B SUMO calibration can start scientifically
and what must be frozen before it does.  It

* runs the itemised SUMO-versus-Stage-0.2 measurement-equivalence audit;
* analyses **only** the two approved US-101 calibration windows through the fail-closed
  :class:`CalibrationValidationGuard`;
* derives an identifiability matrix for the demand, the vehicle fleet and the driving
  behaviour;
* proposes candidate time, tolerance and calibration protocols;
* emits a machine-readable admission checklist in which nothing is approved.

It never reads the temporal validation window, never touches the locked holdout and
never freezes a scientific parameter.
"""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .stage_0_5_sumo import (
    CALIBRATION_VALIDATION_POLICY,
    CLOSING_SPEED_SEMANTICS,
    FORMAL_ALGORITHM_VERSION,
    FORMAL_OBSERVATION_STEP_S,
    FORMAL_TTC_THRESHOLD_S,
    MISSING_REASON_EQUIVALENCE,
    NET_GAP_SEMANTICS,
    NGSIM_CLOSING_EPSILON_MPS,
    NGSIM_STATUS_CROSSWALK,
    RESULT_ID as SUMO_ENGINEERING_RESULT_ID,
    SCHEMA_ROOT as SUMO_SCHEMA_ROOT,
    CalibrationValidationGuard,
    Stage05EngineeringError,
    measurement_equivalence_matrix,
    run_p2_boundary_matrix,
)

READINESS_RESULT_ID = "RES-STAGE-0.5-CALIBRATION-READINESS-V1"
SCHEMA_ROOT = "stage_0_5.calibration-readiness.v1"
FORMAL_REFERENCE_RESULT_ID = "RES-STAGE-0.5-REAL-REF-R2"
STAGE_0_2_REFERENCE_RESULT_ID = "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4"

CALIBRATION_GROUPS = ("us101__0750_0805", "us101__0805_0820")
VALIDATION_GROUPS = ("us101__0820_0835",)
AUXILIARY_GROUPS = ("lankershim__complete", "pneuma__athens_d1")

#: State tables of the approved R2 calibration reference, per window group.
STATE_SOURCES: dict[str, str] = {
    group: f"code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_{group}.parquet"
    for group in CALIBRATION_GROUPS
}
#: Approved formal P2 event table (all sources); read with a window predicate so that
#: non-calibration rows are never materialised.
FORMAL_EVENT_SOURCE = "p2_formal_events"
FORMAL_EVENT_PATH = (
    "code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/p2_formal_events.parquet"
)
REAL_REFERENCE_MANIFEST = "evidence/results/RES-STAGE-0.5-REAL-REF-R2/input_manifest.json"

TIME_SLICE_S = 300.0
STRATUM_SLICE_S = 60.0
MIN_STRATUM_SLICE_COVERAGE_S = 45.0
DENSITY_WINDOW_M = (150.0, 350.0)
CROSS_SECTION_PLANES_M = (150.0, 300.0, 450.0)
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261018

ADMISSION_STATUSES = (
    "Ready for Researcher Approval",
    "Blocked by Measurement",
    "Blocked by Scientific Configuration",
    "Evidence Insufficient",
)

#: Dimensions of the audit, in the order of the five approved necessary layers.
LAYER_DIMENSIONS = (
    "layer_1_basic_kinematics",
    "layer_2_following_interaction",
    "layer_3_risk_observability_and_eligibility",
    "layer_4_p2_events_and_evaluable_exposure",
    "layer_5_scenario_support_and_sample_quality",
)


class CalibrationReadinessError(Stage05EngineeringError):
    """Raised when the readiness audit would violate its own access or evidence rules."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    raise TypeError(f"not JSON serialisable: {type(value)!r}")


# --------------------------------------------------------------------------------------
# guarded access to the approved calibration reference
# --------------------------------------------------------------------------------------


def verify_against_real_reference_manifest(repo_root: Path) -> dict[str, Any]:
    """Check that the paths and SHA-256 values used here match the approved R2 manifest."""

    manifest_path = repo_root / REAL_REFERENCE_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared: dict[str, dict[str, Any]] = {}
    for entry in manifest["inputs"]:
        # the approved manifest keys US-101 rows by the short window label ("0750_0805")
        # and the event table by file name; the readiness audit uses the long group key
        key = entry.get("window_id")
        if key:
            declared[f"us101__{key}"] = entry
        declared[str(entry.get("name"))] = entry
    checks: list[dict[str, Any]] = []
    policy_bindings = CALIBRATION_VALIDATION_POLICY["source_bindings"]
    for group, relative in STATE_SOURCES.items():
        entry = declared.get(group)
        checks.append(
            {
                "source": group,
                "path": relative,
                "manifest_path": entry.get("path") if entry else None,
                "path_matches": bool(entry) and entry.get("path") == relative,
                "sha256_matches": bool(entry) and entry.get("sha256") == policy_bindings.get(group),
                "policy_sha256": policy_bindings.get(group),
                "manifest_sha256": entry.get("sha256") if entry else None,
            }
        )
    event_entry = declared.get("p2_formal_events.parquet")
    checks.append(
        {
            "source": FORMAL_EVENT_SOURCE,
            "path": FORMAL_EVENT_PATH,
            "manifest_path": event_entry.get("path") if event_entry else None,
            "path_matches": bool(event_entry) and event_entry.get("path") == FORMAL_EVENT_PATH,
            "sha256_matches": bool(event_entry)
            and event_entry.get("sha256") == policy_bindings.get(FORMAL_EVENT_SOURCE),
            "policy_sha256": policy_bindings.get(FORMAL_EVENT_SOURCE),
            "manifest_sha256": event_entry.get("sha256") if event_entry else None,
        }
    )
    ok = all(item["path_matches"] and item["sha256_matches"] for item in checks)
    if not ok:
        raise CalibrationReadinessError("readiness sources disagree with the approved R2 manifest")
    return {
        "schema_version": f"{SCHEMA_ROOT}.source-binding-check.v1",
        "reference_result_id": FORMAL_REFERENCE_RESULT_ID,
        "manifest": REAL_REFERENCE_MANIFEST,
        "manifest_sha256": _sha256_file(manifest_path),
        "all_bindings_match": ok,
        "checks": checks,
        "validation_window_read": False,
        "locked_holdout_accessed": False,
    }


def load_calibration_states(
    repo_root: Path, guard: CalibrationValidationGuard
) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]]]:
    """Read the approved calibration windows only, with SHA verification per read."""

    frames: dict[str, pd.DataFrame] = {}
    reads: list[dict[str, Any]] = []
    before = len(guard.decisions)
    for group, relative in STATE_SOURCES.items():
        path = repo_root / relative
        digest = guard.require_source_read(
            path, role="calibration", source=group, purpose="stage_0_5_4a calibration-window analysis"
        )
        frame = pd.read_parquet(path)
        windows = set(frame["window_id"].astype(str).unique())
        forbidden = windows & set(VALIDATION_GROUPS) | windows & set(AUXILIARY_GROUPS)
        if forbidden:
            raise CalibrationReadinessError(f"forbidden window in calibration read: {sorted(forbidden)}")
        # the approved state table carries the short window label; the audit uses the
        # long group key for every source reference
        expected_short = {group.removeprefix("us101__")}
        if windows != expected_short:
            raise CalibrationReadinessError(f"unexpected window scope in {relative}: {sorted(windows)}")
        frame = frame.copy()
        frame["source_group"] = group
        frames[group] = frame
        reads.append(
            {
                "source": group,
                "path": relative,
                "sha256": digest,
                "state_rows": int(len(frame)),
                "rows_materialised": int(len(frame)),
                "window_ids": sorted(windows),
                "analysis_purpose": "layer_1_to_layer_5 calibration statistics",
            }
        )
    reads.append({"guard_decisions_added": len(guard.decisions) - before})
    return frames, reads


TIMESTEP_SENSITIVITY_PATH = (
    "code/outputs/formal/calibration/stage_0_5_timestep_sensitivity_v1/timestep_sensitivity.json"
)


def load_timestep_sensitivity(repo_root: Path) -> dict[str, Any]:
    """Read the deterministic time-step probe package if it has been produced."""

    path = repo_root / TIMESTEP_SENSITIVITY_PATH
    if not path.is_file():
        return {
            "available": False,
            "reason": "time-step sensitivity package not produced; run run_stage_0_5_timestep_sensitivity.py",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "available": True,
        "path": TIMESTEP_SENSITIVITY_PATH,
        "sha256": _sha256_file(path),
        "schema_version": payload.get("schema_version"),
        "runs": payload.get("runs", []),
        "comparisons": payload.get("comparisons", []),
        "cost_benchmark": payload.get("cost_benchmark", []),
        "duration_s": payload.get("duration_s"),
        "seed": payload.get("seed"),
        "engineering_only": True,
        "scientific_claim_eligible": False,
    }


def load_formal_events(
    repo_root: Path, guard: CalibrationValidationGuard
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read only calibration-window rows of the approved formal P2 event table."""

    path = repo_root / FORMAL_EVENT_PATH
    allowed = list(CALIBRATION_GROUPS)
    frame, detail = guard.require_row_scoped_read(
        path,
        source=FORMAL_EVENT_SOURCE,
        allowed_values=allowed,
        column="source",
        purpose="stage_0_5_4a formal P2 events of the calibration windows only",
    )
    detail["rows"] = int(len(frame))
    windows = set(frame["source"].astype(str).unique())
    if not windows <= set(CALIBRATION_GROUPS):
        raise CalibrationReadinessError(f"formal event read escaped the calibration windows: {sorted(windows)}")
    return frame, detail


# --------------------------------------------------------------------------------------
# layer 1/2: kinematics, following and observability of one calibration window
# --------------------------------------------------------------------------------------

FOLLOW_SCOPE = ("dataset", "site", "window_id", "source_member", "source_period")
FOLLOW_PAIR = (*FOLLOW_SCOPE, "trajectory_id", "leader_trajectory_id")


def _pct(series: pd.Series, q: float) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.quantile(q))


def edge_exposure_audit(states: pd.DataFrame) -> dict[str, Any]:
    """Reproduce the approved Stage 0.2 exposure edge audit for one window.

    The rule set is copied from ``code/scripts/audit_stage_0_2_exposure_edges.py`` so the
    published denominators can be reproduced and compared.
    """

    scope = ["dataset", "site", "window_id", "source_member", "source_period"]
    pair = scope + ["trajectory_id", "leader_trajectory_id"]
    ordered = states.sort_values(
        [*scope, "trajectory_id", "global_time_ms", "frame_id"], kind="stable"
    ).reset_index(drop=True)
    previous = ordered.shift()
    adjacent = pd.Series(True, index=ordered.index)
    for key in [*pair, "diagnostic_clock_anchor_ms"]:
        adjacent &= ordered[key].notna() & previous[key].notna() & ordered[key].eq(previous[key]).fillna(False)
    adjacent &= ordered.global_time_ms.diff().eq(100)
    adjacent &= ordered.frame_id.diff().eq(1)
    adjacent &= (ordered.time_s.diff() - FORMAL_OBSERVATION_STEP_S).abs().lt(1e-9)
    adjacent &= ~ordered.identity_break.fillna(True) & ~ordered.observation_gap.fillna(True)
    reliable = (
        ordered.leader_matched.fillna(False)
        & ~ordered.identity_uncertain.fillna(True)
        & ~ordered.leader_identity_uncertain.fillna(True)
    )
    edge = adjacent & reliable & reliable.shift(fill_value=False)
    evaluable_status = ordered.measurement_status.isin(["valid", "not_applicable"])
    evaluable_edge = edge & evaluable_status & evaluable_status.shift(fill_value=False)
    ttc_values = pd.to_numeric(ordered.ttc_s, errors="coerce")
    valid_closing = (
        reliable
        & ordered.ttc_valid.fillna(False)
        & ordered.measurement_status.eq("valid")
        & np.isfinite(ttc_values)
        & ttc_values.gt(0)
    )
    closed_link = edge & valid_closing & valid_closing.shift(fill_value=False)
    closing_time_s = float((closed_link.astype(float) + closed_link.shift(-1, fill_value=False).astype(float)).sum() * 0.05)
    edge_count = int(edge.sum())
    evaluable_count = int(evaluable_edge.sum())
    per_vehicle = (
        pd.DataFrame({"vehicle": ordered.trajectory_id, "edge": edge, "evaluable": evaluable_edge})
        .groupby("vehicle", sort=False)[["edge", "evaluable"]]
        .sum()
    )
    return {
        "reliable_following_edges": edge_count,
        "reliable_following_exposure_s": edge_count * FORMAL_OBSERVATION_STEP_S,
        "p2_evaluable_following_edges": evaluable_count,
        "p2_evaluable_following_exposure_s": evaluable_count * FORMAL_OBSERVATION_STEP_S,
        "not_evaluable_following_exposure_s": (edge_count - evaluable_count) * FORMAL_OBSERVATION_STEP_S,
        "reliable_closing_exposure_s": closing_time_s,
        "per_vehicle_evaluable_exposure_s": (per_vehicle["evaluable"] * FORMAL_OBSERVATION_STEP_S).to_dict(),
        "per_vehicle_following_edges": per_vehicle["edge"].to_dict(),
    }


def window_summary(states: pd.DataFrame, events: pd.DataFrame | None = None) -> dict[str, Any]:
    """Layer 1-5 descriptive statistics of one calibration window."""

    group = str(states["source_group"].iloc[0])
    speeds = pd.to_numeric(states["speed_mps"], errors="coerce")
    accelerations = pd.to_numeric(states["acceleration_mps2"], errors="coerce")
    gaps = pd.to_numeric(states["net_gap_m"], errors="coerce")
    closings = pd.to_numeric(states["closing_speed_mps"], errors="coerce")
    ttc = pd.to_numeric(states["ttc_s"], errors="coerce")
    durations = states.groupby("trajectory_id")["time_s"].agg(["min", "max", "size"])
    exposure = edge_exposure_audit(states)
    window_events = events if events is not None else states.iloc[0:0]
    usable_ttc = ttc[states["ttc_valid"].fillna(False)]
    summary = {
        "source_group": group,
        "state_rows": int(len(states)),
        "vehicles": int(states["vehicle_id"].nunique()),
        "trajectory_clusters": int(states["trajectory_id"].nunique()),
        "observation_window_s": float(states["time_s"].max() - states["time_s"].min()),
        "trajectory_duration_s": {
            "median": float(durations["max"].sub(durations["min"]).median()),
            "p10": float(durations["max"].sub(durations["min"]).quantile(0.10)),
            "p90": float(durations["max"].sub(durations["min"]).quantile(0.90)),
        },
        "kinematics": {
            "speed_mps": {
                "mean": float(speeds.mean()),
                "sd": float(speeds.std()),
                "p05": _pct(speeds, 0.05),
                "median": _pct(speeds, 0.5),
                "p85": _pct(speeds, 0.85),
                "p95": _pct(speeds, 0.95),
                "max": float(speeds.max()),
            },
            "acceleration_mps2": {
                "mean": float(accelerations.mean()),
                "sd": float(accelerations.std()),
                "p05": _pct(accelerations, 0.05),
                "median": _pct(accelerations, 0.5),
                "p95": _pct(accelerations, 0.95),
                "min": float(accelerations.min()),
                "max": float(accelerations.max()),
            },
            "low_speed_fractions": {
                "below_1_mps": float((speeds < 1).mean()),
                "below_2_mps": float((speeds < 2).mean()),
                "below_5_mps": float((speeds < 5).mean()),
            },
        },
        "following": {
            "median_net_gap_m": _pct(gaps, 0.5),
            "p10_net_gap_m": _pct(gaps, 0.10),
            "p90_net_gap_m": _pct(gaps, 0.90),
            "mean_closing_speed_mps": float(closings.mean()),
            "positive_closing_share_of_states": float((closings > 0).mean()),
            "ttc_valid_rows": int(states["ttc_valid"].fillna(False).sum()),
            "ttc_valid_share_of_states": float(states["ttc_valid"].fillna(False).mean()),
            "ttc_valid_median_s": _pct(usable_ttc, 0.5),
            "ttc_valid_p05_s": _pct(usable_ttc, 0.05),
            "ttc_valid_min_s": float(usable_ttc.min()) if not usable_ttc.empty else None,
            "drac_p95_mps2": _pct(pd.to_numeric(states["drac_mps2"], errors="coerce"), 0.95),
        },
        "observability": {
            "measurement_status_counts": {
                str(key): int(value) for key, value in states["measurement_status"].value_counts().items()
            },
            "measurement_status_shares": {
                str(key): float(value) for key, value in states["measurement_status"].value_counts(normalize=True).items()
            },
            "missing_reason_counts": {
                str(key): int(value)
                for key, value in states["missing_reason"].fillna("").value_counts().items()
            },
            "identity_defect_rows": int(
                (
                    states["identity_break"].fillna(True)
                    | states["observation_gap"].fillna(True)
                    | states["identity_uncertain"].fillna(True)
                    | states["leader_identity_uncertain"].fillna(True)
                ).sum()
            ),
            "diagnostic_clock_missing_rows": int(states["diagnostic_clock_anchor_ms"].isna().sum()),
        },
        "exposure": {key: value for key, value in exposure.items() if not key.startswith("per_vehicle")},
        "p2": {
            "events": int(len(window_events)),
            "event_rate_per_vehicle_hour": (
                float(len(window_events) / (exposure["p2_evaluable_following_exposure_s"] / 3600.0))
                if exposure["p2_evaluable_following_exposure_s"] > 0
                else None
            ),
            "unique_followers_with_events": int(window_events["trajectory_id"].nunique())
            if len(window_events)
            else 0,
            "unique_pairs_with_events": int(
                window_events[["trajectory_id", "leader_trajectory_id"]].drop_duplicates().shape[0]
            )
            if len(window_events)
            else 0,
            "duration_s": {
                "median": _pct(window_events["event_duration_s"], 0.5) if len(window_events) else None,
                "p90": _pct(window_events["event_duration_s"], 0.90) if len(window_events) else None,
                "max": float(window_events["event_duration_s"].max()) if len(window_events) else None,
            },
            "ttc_min_s": {
                "median": _pct(window_events["ttc_min_s"], 0.5) if len(window_events) else None,
                "p05": _pct(window_events["ttc_min_s"], 0.05) if len(window_events) else None,
                "min": float(window_events["ttc_min_s"].min()) if len(window_events) else None,
            },
            "exit_reason_counts": {
                str(key): int(value)
                for key, value in window_events["exit_reason"].value_counts().items()
            }
            if len(window_events)
            else {},
            "rule": "stage_0_2.formal_risk_measurement.v2 / P2 (TTC < 2.0 s, span >= 0.2 s)",
        },
    }
    summary["lane_motion"] = lane_motion(states)
    summary["time_slices"] = time_slices(states)
    summary["per_vehicle"] = {
        "evaluable_exposure_s": exposure["per_vehicle_evaluable_exposure_s"],
        "following_edges": exposure["per_vehicle_following_edges"],
        "event_counts": (
            window_events.groupby("trajectory_id").size().to_dict() if len(window_events) else {}
        ),
        "speed_sums": states.groupby("trajectory_id")["speed_mps"].sum().to_dict(),
        "speed_counts": states.groupby("trajectory_id")["speed_mps"].size().to_dict(),
        "acceleration_sums": states.groupby("trajectory_id")["acceleration_mps2"].sum().to_dict(),
    }
    return summary


# --------------------------------------------------------------------------------------
# task B: per-lane motion, time slices and demand identifiability
# --------------------------------------------------------------------------------------


def lane_motion(states: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane, group in states.groupby("lane_id", dropna=False, sort=True):
        speeds = pd.to_numeric(group["speed_mps"], errors="coerce")
        rows.append(
            {
                "lane_id": str(lane),
                "state_rows": int(len(group)),
                "vehicles": int(group["vehicle_id"].nunique()),
                "longitudinal_min_m": float(group["y_m"].min()),
                "longitudinal_max_m": float(group["y_m"].max()),
                "lateral_min_m": float(group["x_m"].min()),
                "lateral_max_m": float(group["x_m"].max()),
                "mean_speed_mps": float(speeds.mean()),
                "p85_speed_mps": _pct(speeds, 0.85),
                "low_speed_share_below_5_mps": float((speeds < 5).mean()),
                "ttc_valid_share": float(group["ttc_valid"].fillna(False).mean()),
            }
        )
    return rows


def time_slices(states: pd.DataFrame, *, slice_s: float = TIME_SLICE_S) -> list[dict[str, Any]]:
    """Fixed-length time slices with coverage, kinematics and exposure."""

    lo, hi = DENSITY_WINDOW_M
    inside = states[states["y_m"].between(lo, hi)]
    window_length_m = hi - lo
    rows: list[dict[str, Any]] = []
    total = float(states["time_s"].max())
    for start in np.arange(0.0, total, slice_s):
        end = min(start + slice_s, total)
        if end - start < 1e-9:
            continue
        chunk = states[(states["time_s"] >= start) & (states["time_s"] < end)]
        chunk_inside = inside[(inside["time_s"] >= start) & (inside["time_s"] < end)]
        speeds = pd.to_numeric(chunk["speed_mps"], errors="coerce")
        instants = chunk.groupby("time_s")["vehicle_id"].nunique()
        instants_inside = chunk_inside.groupby("time_s")["vehicle_id"].nunique()
        coverage_s = float(end - start)
        observed_s = float(chunk["time_s"].nunique()) * FORMAL_OBSERVATION_STEP_S
        rows.append(
            {
                "slice_start_s": float(start),
                "slice_end_s": float(end),
                "coverage_s": coverage_s,
                "observed_s": observed_s,
                "coverage_fraction": observed_s / coverage_s if coverage_s else None,
                "state_rows": int(len(chunk)),
                "vehicles": int(chunk["vehicle_id"].nunique()),
                "mean_vehicles_present": float(instants.mean()) if len(instants) else 0.0,
                "mean_speed_mps": float(speeds.mean()) if not speeds.empty else None,
                "p85_speed_mps": _pct(speeds, 0.85),
                "low_speed_share_below_5_mps": float((speeds < 5).mean()) if not speeds.empty else None,
                "mean_vehicles_in_density_window": (
                    float(instants_inside.mean()) if len(instants_inside) else 0.0
                ),
                "density_window_vehicle_density_per_km": (
                    float(instants_inside.mean()) / window_length_m * 1000.0 if len(instants_inside) else 0.0
                ),
                "ttc_valid_share": float(chunk["ttc_valid"].fillna(False).mean()) if len(chunk) else None,
                "measurement_valid_share": (
                    float(chunk["measurement_status"].eq("valid").mean()) if len(chunk) else None
                ),
            }
        )
    return rows


def cross_section_rates(states: pd.DataFrame, planes: Sequence[float] = CROSS_SECTION_PLANES_M) -> list[dict[str, Any]]:
    """Passage rate through interior cross sections (never the state-row count)."""

    duration_h = float(states["time_s"].max() - states["time_s"].min()) / 3600.0
    rows: list[dict[str, Any]] = []
    for plane in planes:
        extents = states.groupby("trajectory_id")["y_m"].agg(["min", "max"])
        passing = extents[(extents["min"] < plane) & (extents["max"] >= plane)]
        rows.append(
            {
                "cross_section_m": float(plane),
                "passing_trajectories": int(len(passing)),
                "observation_duration_h": duration_h,
                "passage_rate_veh_per_h": float(len(passing) / duration_h) if duration_h > 0 else None,
                "interpretation": "interior cross-section passage rate; not a boundary entry demand",
            }
        )
    return rows


def lane_change_and_boundary_evidence(states: pd.DataFrame) -> dict[str, Any]:
    ordered = states.sort_values(["trajectory_id", "time_s"], kind="stable")
    lane_series = ordered.groupby("trajectory_id")["lane_id"].agg(lambda values: int(values.nunique()))
    per_vehicle = ordered.groupby("trajectory_id").agg(
        first_y=("y_m", "first"),
        last_y=("y_m", "last"),
        first_t=("time_s", "min"),
        last_t=("time_s", "max"),
        states=("time_s", "size"),
    )
    y_lo = float(states["y_m"].min())
    y_hi = float(states["y_m"].max())
    extent = 0.05 * (y_hi - y_lo)
    upstream_band = y_lo + extent
    downstream_band = y_hi - extent
    span_m = y_hi - y_lo
    spans = per_vehicle["last_y"] - per_vehicle["first_y"]
    duration_h = float(states["time_s"].max() - states["time_s"].min()) / 3600.0
    return {
        "trajectories_with_lane_change": int((lane_series > 1).sum()),
        "trajectories_total": int(len(lane_series)),
        "lane_change_share": float((lane_series > 1).mean()),
        "observed_longitudinal_extent_m": [y_lo, y_hi],
        "boundary_band_5pct_m": [upstream_band, downstream_band],
        "trajectories_starting_in_upstream_band": int((per_vehicle["first_y"] <= upstream_band).sum()),
        "trajectories_ending_in_downstream_band": int((per_vehicle["last_y"] >= downstream_band).sum()),
        "trajectories_spanning_90pct_of_extent": int((spans >= 0.9 * span_m).sum()),
        "trajectory_span_median_m": float(spans.median()),
        "first_y_deciles_m": [float(per_vehicle["first_y"].quantile(q)) for q in (0.1, 0.5, 0.9)],
        "last_y_deciles_m": [float(per_vehicle["last_y"].quantile(q)) for q in (0.1, 0.5, 0.9)],
        "observed_segment_entry_rate_veh_per_h": float(
            (per_vehicle["first_y"] <= upstream_band).sum() / duration_h
        )
        if duration_h > 0
        else None,
        "interpretation": (
            "almost every trajectory traverses the observed segment, so the entry rate of the observed"
            " segment is measurable; the demand upstream of the study area, ramp flows and route choice"
            " remain unidentifiable"
        ),
    }


def demand_identifiability(states: pd.DataFrame) -> dict[str, Any]:
    """Classify every demand-relevant quantity by what the approved reference can support."""

    rates = cross_section_rates(states)
    slices = time_slices(states, slice_s=TIME_SLICE_S)
    boundary = lane_change_and_boundary_evidence(states)
    coverage = float(states["time_s"].max() - states["time_s"].min())
    observed_extent = boundary["observed_longitudinal_extent_m"]
    lanes = sorted(str(value) for value in states["lane_id"].dropna().unique())

    def row(name: str, klass: str, value: Any, evidence: str, note: str = "") -> dict[str, Any]:
        return {
            "quantity": name,
            "identifiability": klass,
            "value": value,
            "evidence": evidence,
            "note": note,
        }

    rows = [
        row(
            "observed_lane_set",
            "directly_measurable",
            lanes,
            f"{len(lanes)} distinct lane_id values in the approved state table",
            "lane 6-8 occupy short longitudinal ranges and behave as ramp/auxiliary lanes",
        ),
        row(
            "observed_longitudinal_extent_m",
            "directly_measurable",
            observed_extent,
            "min/max y_m of the approved state table",
            "local NGSIM coordinates; the absolute road length beyond this extent is unknown",
        ),
        row(
            "interior_cross_section_passage_rate_veh_per_h",
            "directly_measurable",
            rates,
            "trajectory extent crossing an interior plane, divided by the observation duration",
        ),
        row(
            "local_vehicle_density_per_km",
            "estimable_within_observed_range",
            [
                {
                    "window_m": list(DENSITY_WINDOW_M),
                    "mean_density_per_km": float(
                        np.mean([item["density_window_vehicle_density_per_km"] for item in slices if item["coverage_fraction"]])
                    ),
                }
            ],
            "mean vehicles present inside a fixed longitudinal window per instant",
            "a local density of the observed segment, not a network-wide density",
        ),
        row(
            "local_space_mean_speed_mps",
            "estimable_within_observed_range",
            float(pd.to_numeric(states["speed_mps"], errors="coerce").mean()),
            "state-level speed distribution",
            "state-weighted; vehicle-equal values are reported next to it",
        ),
        row(
            "time_variation_across_slices",
            "estimable_within_observed_range",
            [
                {
                    "slice_start_s": item["slice_start_s"],
                    "mean_speed_mps": item["mean_speed_mps"],
                    "density_per_km": item["density_window_vehicle_density_per_km"],
                    "coverage_fraction": item["coverage_fraction"],
                }
                for item in slices
            ],
            "fixed 300 s slices, coverage reported per slice",
            "the final partial slice must not be used for calibration targets",
        ),
        row(
            "lane_change_rate",
            "estimable_within_observed_range",
            boundary["lane_change_share"],
            "share of trajectories observed in more than one lane",
            "lane changes are frequent, so a single-lane calibration would discard real behaviour",
        ),
        row(
            "absolute_network_length_and_geometry",
            "requires_additional_geometry",
            None,
            "the approved reference carries local coordinates only",
            "real lane count, ramp geometry and cross-section topology require approved geometry evidence",
        ),
        row(
            "observed_segment_entry_rate_veh_per_h",
            "directly_measurable",
            {
                "value": boundary["observed_segment_entry_rate_veh_per_h"],
                "trajectories_starting_in_upstream_band": boundary["trajectories_starting_in_upstream_band"],
                "boundary_band_5pct_m": boundary["boundary_band_5pct_m"],
            },
            "trajectory onsets inside the upstream 5% of the observed extent",
            "this is the entry rate of the observed segment, not the demand of the upstream network",
        ),
        row(
            "upstream_network_demand_and_ramp_flows",
            "not_identifiable",
            None,
            "the observed record starts and ends inside a study area of finite extent",
            "absolute demand, ramp feed and route choice require evidence outside the approved reference",
        ),
        row(
            "route_choice_and_origin_destination",
            "not_identifiable",
            None,
            "no route or OD information in the approved reference",
        ),
        row(
            "ramp_flows",
            "not_identifiable",
            None,
            "ramp/auxiliary lanes are short and their upstream feed cannot be observed",
        ),
        row(
            "vehicle_class_composition",
            "not_identifiable",
            None,
            "the approved state table has no vehicle class field",
            "acquiring it requires a newly approved calibration-only source; pNEUMA classes must not be substituted",
        ),
        row(
            "vehicle_length_distribution",
            "not_identifiable",
            None,
            "the approved state table has no vehicle length field (only net gap)",
            "same conclusion; a new approved source would be required",
        ),
        row(
            "state_row_count_as_flow",
            "not_identifiable",
            None,
            "state rows are observations per vehicle-step, not vehicles per unit time",
            "state rows must never be used as a flow or density substitute",
        ),
        row(
            "observation_duration_s",
            "directly_measurable",
            coverage,
            "recorded time span of the approved window",
        ),
    ]
    return {
        "schema_version": f"{SCHEMA_ROOT}.demand-identifiability.v1",
        "rows": rows,
        "cross_section_rates": rates,
        "time_slices": slices,
        "boundary_evidence": boundary,
        "prohibited_shortcuts": [
            "state rows are not a vehicle flow",
            "trajectory sampling density is not a traffic density",
            "absolute demand cannot be inferred without a complete road boundary",
            "pNEUMA urban class composition must not be used for US-101",
        ],
    }


def candidate_strata(states: pd.DataFrame) -> dict[str, Any]:
    """Candidate traffic-state strata derived from the calibration windows only."""

    slices = time_slices(states, slice_s=STRATUM_SLICE_S)
    usable = [
        item
        for item in slices
        if item["coverage_fraction"] is not None
        and item["coverage_s"] * item["coverage_fraction"] >= MIN_STRATUM_SLICE_COVERAGE_S
    ]
    densities = np.array([item["density_window_vehicle_density_per_km"] for item in usable], dtype=float)
    speeds = np.array([item["mean_speed_mps"] for item in usable], dtype=float)
    low_density, high_density = np.quantile(densities, [1 / 3, 2 / 3])
    low_speed, high_speed = np.quantile(speeds, [1 / 3, 2 / 3])
    for item in usable:
        item["candidate_stratum"] = (
            "low_density" if item["density_window_vehicle_density_per_km"] <= low_density else
            "high_density" if item["density_window_vehicle_density_per_km"] >= high_density else
            "medium_density"
        )
        item["candidate_speed_regime"] = (
            "free_flow" if item["mean_speed_mps"] >= high_speed else
            "congested" if item["mean_speed_mps"] <= low_speed else
            "transitional"
        )
    counts: dict[str, int] = {}
    for item in usable:
        counts[item["candidate_stratum"]] = counts.get(item["candidate_stratum"], 0) + 1
    return {
        "schema_version": f"{SCHEMA_ROOT}.candidate-strata.v1",
        "slice_s": STRATUM_SLICE_S,
        "minimum_slice_coverage_s": MIN_STRATUM_SLICE_COVERAGE_S,
        "usable_slices": len(usable),
        "excluded_partial_slices": len(slices) - len(usable),
        "density_thresholds_per_km": {
            "lower_tercile": float(low_density),
            "upper_tercile": float(high_density),
        },
        "speed_thresholds_mps": {"lower_tercile": float(low_speed), "upper_tercile": float(high_speed)},
        "stratum_slice_counts": counts,
        "slices": usable,
        "status": "candidate_thresholds_derived_from_calibration_windows_only",
        "validation_window_used": False,
        "note": (
            "tercile thresholds are descriptive candidates computed before any SUMO result exists;"
            " they are not approved scientific strata and no extreme state was manufactured"
        ),
    }


# --------------------------------------------------------------------------------------
# task F3: clustered uncertainty
# --------------------------------------------------------------------------------------


def clustered_uncertainty(
    summaries: Mapping[str, Mapping[str, Any]],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Vehicle/trajectory-cluster bootstrap of the calibration-window statistics."""

    rng = np.random.default_rng(seed)
    report: dict[str, Any] = {
        "schema_version": f"{SCHEMA_ROOT}.clustered-uncertainty.v1",
        "cluster_unit": "trajectory (one physical vehicle across its whole observed record)",
        "resamples": int(resamples),
        "seed": int(seed),
        "sources": [],
        "iid_row_bootstrap_warning": (
            "row-level i.i.d. resampling is reported only to show how much narrower it is;"
            " it must not be used for scientific tolerance"
        ),
    }
    for group, summary in summaries.items():
        per_vehicle = summary["per_vehicle"]
        vehicles = sorted(per_vehicle["speed_counts"])
        if not vehicles:
            continue
        exposure = np.array([per_vehicle["evaluable_exposure_s"].get(v, 0.0) for v in vehicles], dtype=float)
        event_counts = np.array([per_vehicle["event_counts"].get(v, 0) for v in vehicles], dtype=float)
        speed_counts = np.array([per_vehicle["speed_counts"][v] for v in vehicles], dtype=float)
        speed_sums = np.array([per_vehicle["speed_sums"][v] for v in vehicles], dtype=float)
        accel_sums = np.array([per_vehicle["acceleration_sums"][v] for v in vehicles], dtype=float)
        edge_counts = np.array([per_vehicle["following_edges"].get(v, 0.0) for v in vehicles], dtype=float)
        n_clusters = len(vehicles)
        draws = rng.integers(0, n_clusters, size=(resamples, n_clusters))
        rate_samples = np.full(resamples, np.nan)
        speed_samples = np.full(resamples, np.nan)
        accel_samples = np.full(resamples, np.nan)
        following_samples = np.full(resamples, np.nan)
        evaluable_samples = np.full(resamples, np.nan)
        for index in range(resamples):
            selection = draws[index]
            total_exposure = exposure[selection].sum()
            total_events = event_counts[selection].sum()
            rate_samples[index] = (
                float(total_events / (total_exposure / 3600.0)) if total_exposure > 0 else np.nan
            )
            state_total = speed_counts[selection].sum()
            if state_total > 0:
                speed_samples[index] = float(speed_sums[selection].sum() / state_total)
                accel_samples[index] = float(accel_sums[selection].sum() / state_total)
                following_samples[index] = float(edge_counts[selection].sum() * 0.1)
                evaluable_samples[index] = float(total_exposure)

        def interval(samples: np.ndarray, point: float | None = None) -> dict[str, Any]:
            values = samples[np.isfinite(samples)]
            if values.size == 0:
                return {"point": point, "lower_95": None, "upper_95": None}
            return {
                # the point estimate stays the observed value; the resamples only
                # describe the uncertainty of that value
                "point": point,
                "bootstrap_mean": float(np.mean(values)),
                "lower_95": float(np.quantile(values, 0.025)),
                "upper_95": float(np.quantile(values, 0.975)),
                "sd": float(np.std(values, ddof=1)),
            }

        point_rate = (
            float(event_counts.sum() / (exposure.sum() / 3600.0)) if exposure.sum() > 0 else None
        )
        point_speed = float(speed_sums.sum() / speed_counts.sum())
        iid_se_speed = float(
            np.sqrt(
                np.sum((speed_sums / np.maximum(speed_counts, 1) - point_speed) ** 2 * speed_counts)
                / max(speed_counts.sum() - 1, 1)
            )
            / np.sqrt(speed_counts.sum())
        )
        report["sources"].append(
            {
                "source_group": group,
                "clusters": int(n_clusters),
                "state_rows": int(speed_counts.sum()),
                "reliable_following_exposure_s": float(edge_counts.sum() * 0.1),
                "p2_evaluable_following_exposure_s": float(exposure.sum()),
                "p2_events": int(event_counts.sum()),
                "p2_event_rate_per_vehicle_hour": interval(rate_samples, point_rate),
                "mean_speed_mps": interval(speed_samples, point_speed),
                "mean_acceleration_mps2": interval(
                    accel_samples, float(accel_sums.sum() / speed_counts.sum())
                ),
                "cluster_ci_width_speed_mps": float(
                    interval(speed_samples, point_speed)["upper_95"]
                    - interval(speed_samples, point_speed)["lower_95"]
                ),
                "iid_row_se_speed_mps": iid_se_speed,
                "iid_row_ci_width_speed_mps": float(4 * 1.96 * iid_se_speed),
                "iid_narrower_by_factor": (
                    float(
                        (interval(speed_samples)["upper_95"] - interval(speed_samples)["lower_95"])
                        / max(4 * 1.96 * iid_se_speed, 1e-12)
                    )
                ),
                "vehicles_with_events": int((event_counts > 0).sum()),
                "event_share_of_vehicles": float((event_counts > 0).mean()),
                "exposure_concentration": {
                    "top_10pct_share": float(
                        np.sort(exposure)[::-1][: max(1, n_clusters // 10)].sum() / max(exposure.sum(), 1e-12)
                    )
                },
            }
        )
    report["usable_for_tolerance"] = False
    report["reason"] = (
        "clustered intervals describe real-data estimation uncertainty only.  They are not a"
        " permissible SUMO model-deviation tolerance (see the tolerance protocol)."
    )
    return report


# --------------------------------------------------------------------------------------
# tasks C/D/E/F/G: candidate protocol, decisions and admission checklist
# --------------------------------------------------------------------------------------


def network_options() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_ROOT}.network-options.v1",
        "current_engineering_network": {
            "network_id": "generic_highway_candidate",
            "mainline_edges": 3,
            "mainline_lanes": 3,
            "on_ramp": 1,
            "off_ramp": 1,
            "built_lane_lengths_m": {
                "main_0": 386.5,
                "main_1": 312.94,
                "main_2": 483.5,
                "onramp": 239.26,
                "offramp": 277.51,
            },
            "status": "engineering_fixture_runnable_not_approved",
        },
        "options": [
            {
                "option_id": "A_generic_corridor",
                "name": "Generic highway corridor with an approved traffic-state envelope",
                "supports": [
                    "controlled longitudinal following experiments",
                    "explicit traffic-state strata",
                    "later causal identification with a stable, simple topology",
                ],
                "cannot_claim": [
                    "US-101 geometry reproduction",
                    "road-structure-driven dynamics",
                    "physical propagation speed calibrated to real US-101",
                ],
                "evidence_available_now": [
                    "3-lane, 3-segment corridor with on/off ramp already runs deterministically",
                    "cross-section flow, density and speed of the calibration windows are measurable",
                ],
                "cost": "low",
                "risks": [
                    "lane count and lane-change opportunity differ from the observed corridor",
                    "ramp merge geometry is not the real merge geometry",
                ],
            },
            {
                "option_id": "B_real_geometry",
                "name": "US-101 corresponding network with verified geometric evidence",
                "supports": [
                    "explicit mapping between observed lanes/ramp and modelled links",
                    "structure-sensitive comparison of following behaviour",
                ],
                "cannot_claim": ["calibrated behaviour before the behaviour calibration is done"],
                "evidence_available_now": [
                    "local assets exist (CAD diagram, GIS files, detector data, aerial imagery) but are"
                    " not part of the approved calibration reference",
                    "the approved state table gives the observed lane set, lateral offsets and a ~660 m"
                    " longitudinal extent",
                ],
                "cost": "high: parsing, verification and a documented geometry provenance chain",
                "risks": [
                    "geometry evidence must be approved and versioned before it can be used",
                    "geometry correctness does not imply behavioural correctness",
                ],
            },
            {
                "option_id": "C_hybrid",
                "name": "Generic corridor now, geometry upgrade later behind an explicit protocol version",
                "supports": [
                    "start calibration without blocking on geometry evidence",
                    "upgrade to option B without invalidating the measurement contract",
                ],
                "cannot_claim": ["that the upgrade preserves previously calibrated behaviour"],
                "evidence_available_now": ["same as option A"],
                "cost": "medium: one extra network/protocol version",
                "risks": ["two protocol versions must be auditable and not silently merged"],
            },
        ],
        "recommendation": "C_hybrid",
        "recommendation_reason": (
            "the approved reference cannot yet support a verified real-geometry network, and the"
            " measurement contract (not the geometry) is what the calibration depends on; the geometry"
            " upgrade must carry its own protocol version and provenance"
        ),
        "claimed_lane_structure_from_reference": {
            "mainline_lanes_observed": 5,
            "ramp_or_auxiliary_lanes_observed": 3,
            "note": (
                "derived from the approved state table lateral offsets and longitudinal ranges; a"
                " 5-lane mainline plus a short ramp/auxiliary group, not a uniform 3-lane corridor"
            ),
        },
        "stage_1_separation": (
            "reality coverage in Stage 0.5 never transfers to a physical-propagation claim in Stage I/II"
        ),
    }


def time_step_options(sensitivity: Mapping[str, Any] | None = None) -> dict[str, Any]:
    measured = dict(sensitivity or {})
    payload = {
        "schema_version": f"{SCHEMA_ROOT}.time-step-options.v1",
        "options": [
            {
                "option_id": "A_uniform_0.1",
                "internal_step_s": 0.1,
                "recorded_observation_step_s": 0.1,
                "decimation_factor": 1,
                "rationale": "recorded cadence matches the 100 ms formal observation semantics exactly",
                "risk": "coarser car-following integration than option B",
            },
            {
                "option_id": "B_fine_internal_0.05",
                "internal_step_s": 0.05,
                "recorded_observation_step_s": 0.1,
                "decimation_factor": 2,
                "rationale": "finer integration while keeping 100 ms recorded evidence",
                "risk": "twice the simulation cost; the recorded series still cannot exceed 100 ms evidence",
            },
        ],
        "recommendation": "B_fine_internal_0.05",
        "recommendation_reason": (
            "the recorded series keeps exact 100 ms formal observation semantics while the finer"
            " integration reduces the transient overshoot of the closing episodes; the measured"
            " convergence probe shows the event boundaries still move when the internal step is"
            " halved, so the internal step must be frozen as part of the measurement protocol"
        ),
        "measured_sensitivity": measured,
        "invariants": [
            "internal_step_s must divide recorded_observation_step_s exactly",
            "a 0.2 s recording must never be relabelled as 100 ms evidence",
            "warm-up seconds are not frozen here: no scientific basis exists yet",
        ],
        "warmup_principle": (
            "fix the warm-up by a traffic-stability diagnostic (network inflow/flow and mean-speed"
            " stabilisation within a pre-declared tolerance window) rather than an arbitrary number of"
            " seconds; the diagnostic rule itself is a researcher decision"
        ),
        "evaluation_window_rules": [
            "declare a fixed evaluation window before running anything",
            "drop the run-in period and keep a constant post-warm-up window",
            "assign an event to the window it starts in; never extrapolate exposure past the last observation",
            "right-censored events at the window end keep their observed confirmation and are reported as censored",
            "vehicles entering or leaving the corridor keep their identity scope and never bridge across it",
        ],
        "unapproved_numbers": ["warmup_s", "evaluation_window_start_s", "evaluation_window_end_s"],
    }
    if measured.get("comparisons"):
        payload["measured_boundary_shift_s"] = {
            row["fixture_id"]: {
                "events_match": row.get("events_match_all_three", row.get("events_match")),
                "start_shift_A_to_B_s": row.get("convergence_A_to_B_start_s"),
                "start_shift_B_to_C_s": row.get("convergence_B_to_C_start_s"),
            }
            for row in measured["comparisons"]
        }
    if measured.get("cost_benchmark"):
        payload["measured_cost"] = measured["cost_benchmark"]
    return payload


def vehicle_fleet_candidates(summaries: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_ROOT}.vehicle-fleet-candidates.v1",
        "identifiable_from_approved_reference": {
            "vehicle_class_composition": None,
            "vehicle_length_distribution": None,
            "vehicle_mass_or_power": None,
            "note": (
                "the approved canonical state table carries no vehicle class, length or performance"
                " field, so no vType composition can be calibrated from it"
            ),
        },
        "approved_reference_fields_present": [
            "speed_mps",
            "acceleration_mps2",
            "net_gap_m",
            "closing_speed_mps",
            "ttc_s",
            "drac_mps2",
            "lane_id",
            "x_m",
            "y_m",
        ],
        "candidate_vtypes": [
            {
                "sumo_vtype": "us101_passenger_candidate",
                "raw_vehicle_type": "unresolved (no class field in the approved reference)",
                "length_m": {"value": None, "source": "not identifiable", "evidence_strength": "none"},
                "min_gap_m": {"value": None, "source": "not identifiable", "evidence_strength": "none"},
                "accel_mps2": {"value": None, "source": "not identifiable", "evidence_strength": "none"},
                "decel_mps2": {"value": None, "source": "not identifiable", "evidence_strength": "none"},
                "max_speed_mps": {"value": None, "source": "not identifiable", "evidence_strength": "none"},
                "status": "Evidence Insufficient",
            }
        ],
        "engineering_fixture_vtypes": {
            "engineering_car": "engineering fixture only; must not be promoted to a scientific mapping",
            "engineering_heavy_fixture": "engineering fixture only; must not be promoted",
            "engineering_queue_fixture": "engineering fixture only; must not be promoted",
        },
        "measurement_identifiable_parameters": {
            "speed_distribution": "identifiable from the approved reference",
            "acceleration_distribution": "identifiable from the approved reference",
            "net_gap_distribution": "identifiable from the approved reference",
            "closing_speed_distribution": "identifiable from the approved reference",
            "ttc_evaluable_share": "identifiable from the approved reference",
        },
        "required_new_evidence": [
            "a researcher-approved calibration-only source with vehicle class and length fields"
            " (raw NGSIM records of the two calibration windows would qualify, but must be approved"
            " and SHA-bound before use)",
        ],
        "prohibited_substitutions": [
            "pNEUMA urban class proportions must not be applied to US-101",
            "engineering fixture vTypes must not be declared as the real fleet",
        ],
        "windows_analysed": sorted(summaries),
    }


def following_model_options() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_ROOT}.following-model-options.v1",
        "primary_candidate": {
            "model": "sumo_default_krauss",
            "reasons": [
                "deterministic, low-dimensional and already exercised by the engineering baseline",
                "its gap/closing/braking response is directly observable in the recorded state contract",
                "few identifiable parameters keep the calibration traceable",
            ],
            "calibratable_parameters": [
                "tau (desired time headway): sets equilibrium gap and closing response",
                "minGap: sets the residual bumper-to-bumper gap",
                "accel / decel / emergencyDecel: set the closing and braking envelope",
                "sigma: driver imperfection / speed noise",
                "maxSpeed",
            ],
            "identifiability_notes": {
                "tau": "constrained by the net-gap distribution at given speeds",
                "minGap": "weakly constrained: the observed low-gap tail is also affected by tau and decel",
                "accel": "constrained by the positive acceleration tail",
                "decel": "constrained by the negative acceleration tail and P2 closing episodes",
                "sigma": "weakly constrained once tau and accel absorb the variance",
                "tau_minGap_decel": "partially compensating in the observed gap distribution",
            },
            "risks": [
                "a static speed and gap fit can succeed while the transient closing response stays wrong",
                "one optimal fit must never be reported as fully calibrated driver behaviour",
            ],
        },
        "alternative_candidate": {
            "model": "sumo_default_krauss_with_imperfection_split",
            "reason": "kept only as a fallback if the primary candidate cannot match the closing behaviour",
            "when": "only after the primary candidate is rejected with recorded evidence",
        },
        "explicitly_not_proposed": [
            "multi-model ensembles or high-dimensional behaviour fits at this stage",
            "per-vehicle parameter fitting that cannot be identified from the available fields",
        ],
        "structural_freeze_recommendation": (
            "freeze the car-following model structure before optimisation and optimise only the"
            " parameter vector, so a failed calibration is attributable"
        ),
    }


def parameter_identifiability() -> dict[str, Any]:
    rows = [
        {
            "parameter": "network_lane_count",
            "class": "approval_required_not_optimisable",
            "basis": "observed lane set in the approved reference plus a network decision",
            "evidence": "5 mainline + 3 short ramp/auxiliary lanes observed",
        },
        {
            "parameter": "demand_level",
            "class": "approval_required_not_optimisable",
            "basis": "interior cross-section passage rate per stratum",
            "evidence": "measurable within the observed extent only",
        },
        {
            "parameter": "tau",
            "class": "constrained_by_current_data",
            "basis": "net-gap distribution conditioned on speed",
        },
        {
            "parameter": "minGap",
            "class": "range_only",
            "basis": "lower tail of the net-gap distribution",
            "note": "partially compensating with tau",
        },
        {
            "parameter": "accel",
            "class": "constrained_by_current_data",
            "basis": "positive acceleration tail",
        },
        {
            "parameter": "decel",
            "class": "constrained_by_current_data",
            "basis": "negative acceleration tail and closing episodes",
        },
        {
            "parameter": "emergencyDecel",
            "class": "not_identifiable_must_be_fixed",
            "basis": "rarely exercised in normal traffic",
        },
        {
            "parameter": "sigma",
            "class": "range_only",
            "basis": "residual speed variance after tau/accel",
        },
        {
            "parameter": "maxSpeed",
            "class": "constrained_by_current_data",
            "basis": "upper speed tail, but confounded with the road speed limit",
        },
        {
            "parameter": "vehicle_length",
            "class": "not_identifiable_from_approved_reference",
            "basis": "no length field",
        },
        {
            "parameter": "vehicle_class_mix",
            "class": "not_identifiable_from_approved_reference",
            "basis": "no class field",
        },
        {
            "parameter": "lane_change_parameters",
            "class": "requires_additional_experiment",
            "basis": "approved reference shows lane changes but no lane-change-specific fields",
        },
    ]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["class"]] = counts.get(row["class"], 0) + 1
    return {
        "schema_version": f"{SCHEMA_ROOT}.parameter-identifiability.v1",
        "rows": rows,
        "class_counts": counts,
        "rule": "a single best fit must never be reported as fully calibrated driver behaviour",
    }


def calibration_objectives(summaries: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Calibration targets, scientific acceptance indicators and tolerance classes."""

    layer_1: list[dict[str, Any]] = []
    layer_2: list[dict[str, Any]] = []
    layer_3: list[dict[str, Any]] = []
    layer_4: list[dict[str, Any]] = []
    layer_5: list[dict[str, Any]] = []
    for group, summary in summaries.items():
        kinematics = summary["kinematics"]
        following = summary["following"]
        observability = summary["observability"]
        exposure = summary["exposure"]
        p2 = summary["p2"]
        layer_1.append(
            {
                "source_group": group,
                "mean_speed_mps": kinematics["speed_mps"]["mean"],
                "p85_speed_mps": kinematics["speed_mps"]["p85"],
                "mean_acceleration_mps2": kinematics["acceleration_mps2"]["mean"],
                "p95_acceleration_mps2": kinematics["acceleration_mps2"]["p95"],
                "p05_acceleration_mps2": kinematics["acceleration_mps2"]["p05"],
                "low_speed_share_below_5_mps": kinematics["low_speed_fractions"]["below_5_mps"],
            }
        )
        layer_2.append(
            {
                "source_group": group,
                "median_net_gap_m": following["median_net_gap_m"],
                "p10_net_gap_m": following["p10_net_gap_m"],
                "mean_closing_speed_mps": following["mean_closing_speed_mps"],
                "positive_closing_share": following["positive_closing_share_of_states"],
            }
        )
        layer_3.append(
            {
                "source_group": group,
                "valid_share": observability["measurement_status_shares"].get("valid"),
                "not_applicable_share": observability["measurement_status_shares"].get("not_applicable"),
                "missing_share": observability["measurement_status_shares"].get("missing"),
                "invalid_share": observability["measurement_status_shares"].get("invalid"),
                "identity_defect_rows": observability["identity_defect_rows"],
                "ttc_valid_share": following["ttc_valid_share_of_states"],
            }
        )
        layer_4.append(
            {
                "source_group": group,
                "p2_events": p2["events"],
                "p2_evaluable_following_exposure_s": exposure["p2_evaluable_following_exposure_s"],
                "not_evaluable_following_exposure_s": exposure["not_evaluable_following_exposure_s"],
                "reliable_closing_exposure_s": exposure["reliable_closing_exposure_s"],
                "p2_event_rate_per_vehicle_hour": p2["event_rate_per_vehicle_hour"],
                "event_duration_median_s": p2["duration_s"]["median"],
                "ttc_min_median_s": p2["ttc_min_s"]["median"],
            }
        )
        layer_5.append(
            {
                "source_group": group,
                "state_rows": summary["state_rows"],
                "trajectory_clusters": summary["trajectory_clusters"],
                "observation_window_s": summary["observation_window_s"],
                "trajectory_duration_median_s": summary["trajectory_duration_s"]["median"],
            }
        )
    metrics = [
        {
            "metric": "speed_distribution",
            "layer": LAYER_DIMENSIONS[0],
            "class": "calibration_target",
            "shared_semantics": "state-weighted longitudinal speed, m/s",
            "reference": layer_1,
            "tolerance": {"form": "distributional (quantile bands)", "value": None, "status": "Tolerance Not Yet Justified"},
            "gate_role": "necessary acceptance indicator",
        },
        {
            "metric": "acceleration_distribution",
            "layer": LAYER_DIMENSIONS[0],
            "class": "calibration_target",
            "shared_semantics": "longitudinal acceleration, m/s^2, from the source acceleration field",
            "reference": layer_1,
            "tolerance": {"form": "distributional (tail quantiles)", "value": None, "status": "Tolerance Not Yet Justified"},
            "gate_role": "necessary acceptance indicator",
        },
        {
            "metric": "net_gap_and_closing",
            "layer": LAYER_DIMENSIONS[1],
            "class": "calibration_target",
            "shared_semantics": NET_GAP_SEMANTICS["physical_net_gap_rule"] + "; " + CLOSING_SPEED_SEMANTICS["definition"],
            "reference": layer_2,
            "tolerance": {"form": "quantile bands on gap and closing speed", "value": None, "status": "Tolerance Not Yet Justified"},
            "gate_role": "necessary acceptance indicator",
        },
        {
            "metric": "risk_observability_composition",
            "layer": LAYER_DIMENSIONS[2],
            "class": "measurement_validity_hard_constraint",
            "shared_semantics": "measurement_status composition using the approved crosswalk",
            "reference": layer_3,
            "tolerance": {"form": "exact rule compliance, not a fitted tolerance", "value": None, "status": "rule_check"},
            "gate_role": "hard constraint; failure blocks the layer, no compensation",
        },
        {
            "metric": "p2_event_rate",
            "layer": LAYER_DIMENSIONS[3],
            "class": "primary_scientific_comparison",
            "shared_semantics": "p2_events / p2_evaluable_following_vehicle_hours, full observations only",
            "reference": layer_4,
            "tolerance": {"form": "interval difference with clustered uncertainty", "value": None, "status": "Tolerance Not Yet Justified"},
            "gate_role": "primary comparison, evaluated only after layers 1-3 pass",
        },
        {
            "metric": "p2_exposure_structure",
            "layer": LAYER_DIMENSIONS[3],
            "class": "necessary_condition",
            "shared_semantics": "reliable following / evaluable / not evaluable / reliable closing exposure",
            "reference": layer_4,
            "tolerance": {"form": "rule compliance plus descriptive comparison", "value": None, "status": "rule_check"},
            "gate_role": "necessary condition: an event rate is meaningless without its denominator",
        },
        {
            "metric": "sample_support",
            "layer": LAYER_DIMENSIONS[4],
            "class": "necessary_condition",
            "shared_semantics": "cluster counts, window duration and slice coverage",
            "reference": layer_5,
            "tolerance": {"form": "minimum support declared before running", "value": None, "status": "Tolerance Not Yet Justified"},
            "gate_role": "necessary condition",
        },
        {
            "metric": "energy_distance_multidimensional",
            "layer": "auxiliary_diagnostic",
            "class": "auxiliary_diagnostic",
            "shared_semantics": "multi-dimensional distribution distance, pooled scalers",
            "reference": "real-real upper bound remains Not Identifiable",
            "tolerance": {"form": "diagnostic only", "value": None, "status": "not_a_scientific_threshold"},
            "gate_role": "never a gate criterion; never fitted on validation data",
        },
    ]
    return {
        "schema_version": f"{SCHEMA_ROOT}.calibration-objectives.v1",
        "layers": {
            LAYER_DIMENSIONS[0]: layer_1,
            LAYER_DIMENSIONS[1]: layer_2,
            LAYER_DIMENSIONS[2]: layer_3,
            LAYER_DIMENSIONS[3]: layer_4,
            LAYER_DIMENSIONS[4]: layer_5,
        },
        "metrics": metrics,
        "layer_rule": "a failed necessary layer cannot be compensated by a better value in another layer",
        "energy_distance_real_real_upper_bound": "Not Identifiable",
        "tolerance_components_required": [
            "real-data estimation uncertainty (clustered)",
            "measurement error of the shared observables",
            "scenario and window differences",
            "scientifically allowed model deviation",
            "potential impact on later AAD risk-propagation conclusions",
        ],
        "prohibited_tolerance_rule": (
            "SUMO falling inside the real-data 95% interval is not, by itself, an accepted scientific"
            " acceptance rule"
        ),
    }


def calibration_target_vs_threshold() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_ROOT}.target-versus-threshold.v1",
        "calibration_target": {
            "purpose": "select candidate traffic-model parameters",
            "examples": ["distance between simulated and real speed/gap/closing distributions"],
            "may_use": ["the two calibration windows", "clustered uncertainty as weights or diagnostics"],
        },
        "acceptance_threshold": {
            "purpose": "decide whether the calibrated model has enough reality consistency",
            "requirements": [
                "declared before the optimisation starts",
                "never selected from the validation window",
                "justified by the five tolerance components",
                "evaluated per layer with hard constraints first",
            ],
        },
        "relationship": "related but not identical; a good optimisation target does not define a bad acceptance result",
        "status": "candidate_protocol_pending_researcher_approval",
    }


def candidate_calibration_protocol(
    summaries: Mapping[str, Mapping[str, Any]], sensitivity: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    event_counts = {group: summary["p2"]["events"] for group, summary in summaries.items()}
    exposure = {group: summary["exposure"]["p2_evaluable_following_exposure_s"] for group, summary in summaries.items()}
    return {
        "schema_version": f"{SCHEMA_ROOT}.candidate-protocol.v1",
        "stage": "0.5.4-B",
        "status": "candidate_pending_researcher_approval",
        "not_executed_by_this_task": True,
        "parameter_space": {
            "frozen_before_optimisation": [
                "network topology and lane count",
                "car-following model structure",
                "recorded observation cadence and evaluation window",
                "traffic-state strata definition",
            ],
            "optimisable": ["tau", "minGap", "accel", "decel", "sigma", "maxSpeed"],
            "fixed_by_declaration": ["emergencyDecel (not identifiable in normal traffic)"],
            "approval_only": ["demand level per stratum", "vType composition if new evidence is approved"],
            "dimensions": 6,
            "guard_against_unidentifiability": (
                "freeze the model structure, keep the parameter vector small, and report the"
                " compensating directions (tau/minGap/decel) explicitly"
            ),
        },
        "phases": [
            {"phase": 1, "name": "network_and_demand_loadability", "exit": "the approved demand strata can be injected and the corridor reaches the target density/speed range"},
            {"phase": 2, "name": "basic_kinematics", "exit": "layer-1 distributions match the calibration targets inside the declared bands"},
            {"phase": 3, "name": "following_interaction", "exit": "layer-2 gap/closing distributions match without breaking layer 1"},
            {"phase": 4, "name": "observability_and_exposure", "exit": "layer-3 composition and the exposure structure are reproduced by rule"},
            {"phase": 5, "name": "p2_event_rate_diagnosis", "exit": "P2 rate and exposure compared with clustered real uncertainty; no rule change allowed"},
            {"phase": 6, "name": "stability", "exit": "seed, stratum and parameter-perturbation stability recorded"},
        ],
        "parameter_search": {
            "recommended": "coarse deterministic grid or low-dimensional quasi-random search over the 6 parameters, with a fixed evaluation budget",
            "not_recommended": "gradient-free black-box fitting of network, demand, vType and behaviour jointly",
            "stopping_rule": "stop when the declared layer-1/2 bands are met or the budget is exhausted; record failure",
        },
        "seed_policy": {
            "seeds_per_configuration": 3,
            "selection_rule": "report all seeds; never select the best seed for a headline number",
            "required_reporting": ["per-seed values", "between-seed spread", "failures"],
        },
        "run_budget": {
            "status": "Evidence Insufficient",
            "measured_benchmark": (sensitivity or {}).get("cost_benchmark", []),
            "benchmark_plan": [
                "a 300 s baseline benchmark with three integration-step candidates is recorded",
                "run the same benchmark at the target stratum density before fixing the final budget",
                "declare the final configuration count only after the density-scaled benchmark",
            ],
            "indicative_structure": {
                "configurations": "to be derived from the benchmark",
                "runs": "configurations x seeds x strata",
            },
        },
        "real_reference_counts_for_planning": {
            "p2_events": event_counts,
            "p2_evaluable_following_exposure_s": exposure,
            "note": (
                "the calibration windows contain a limited number of P2 events, so the P2 rate must be"
                " treated as a comparison with wide uncertainty, never as a tight fitting target"
            ),
        },
        "p2_zero_result_interpretation": (
            "a candidate SUMO baseline with zero P2 events is not a failure by itself: it must be"
            " interpreted against the exposure, the density/speed stratum and the SUMO safe-following"
            " behaviour, and it never justifies manufacturing events or changing the P2 rule"
        ),
        "probe_fixture_policy": (
            "measurement_probe_queue_stop is a measurement-contract fixture only and must never be used"
            " as a traffic-risk calibration scenario"
        ),
        "validation_isolation": {
            "calibration_sources": list(CALIBRATION_GROUPS),
            "validation_source": list(VALIDATION_GROUPS),
            "rules": [
                "the validation window participates in no parameter, stratum or tolerance choice",
                "calibration scalers never read validation data",
                "all seeds and candidate parameters are recorded before the validation run",
                "a failed validation requires a new traceable protocol version, never a silent retune",
                "the project locked holdout stays inaccessible",
            ],
            "fail_closed_entry": "CalibrationValidationGuard refuses calibration access to the validation window at the API level",
        },
        "researcher_decisions_required": [
            "network option",
            "demand strata and target levels",
            "vType evidence route",
            "time configuration and warm-up rule",
            "tolerances per layer",
            "run budget after the benchmark",
        ],
    }


def stage_0_5_4b_admission_checklist(
    equivalence: Mapping[str, Any],
    summaries: Mapping[str, Mapping[str, Any]],
    sensitivity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Machine-readable admission checklist; nothing is approved by this task."""

    items = [
        {
            "item": "p2_measurement_equivalence",
            "status": "Ready for Researcher Approval",
            "evidence": (
                f"{equivalence['equivalent_or_verified_count']} equivalent/verified and"
                f" {equivalence['engineering_only_count']} engineering-consistent dimensions;"
                f" {equivalence['boundary_case_count']} boundary cases all as expected;"
                f" blocking items: {equivalence['blocking_items']}"
            ),
            "blocks_start": True,
            "required_action": "researcher accepts the equivalence scope, including the inherited 1e-3 m/s closing tolerance",
        },
        {
            "item": "calibration_reference_availability",
            "status": "Ready for Researcher Approval",
            "evidence": "R2 state tables and the formal P2 event table verified by SHA-256; both calibration windows analysed",
            "blocks_start": True,
            "required_action": "confirm the two calibration windows as the only calibration reference",
        },
        {
            "item": "network_plan_approval",
            "status": "Blocked by Scientific Configuration",
            "evidence": "generic_highway_candidate runs but is not approved; real geometry evidence is not part of the approved reference",
            "blocks_start": True,
            "required_action": "choose option A, B or C and record the accompanying claim limits",
        },
        {
            "item": "vehicle_type_plan_approval",
            "status": "Evidence Insufficient",
            "evidence": "the approved reference has no vehicle class or length field",
            "blocks_start": True,
            "required_action": "approve a calibration-only source or declare the fleet parameters fixed/ sensitivity-only",
        },
        {
            "item": "demand_strata_approval",
            "status": "Ready for Researcher Approval",
            "evidence": "interior passage rates, local density and 60 s slice strata derived from the calibration windows",
            "blocks_start": True,
            "required_action": "approve the stratum definition and target levels",
        },
        {
            "item": "time_configuration_approval",
            "status": "Blocked by Scientific Configuration",
            "evidence": (
                "internal/recorded options are ready and the measured time-step probe shows the event"
                " boundaries still move when the internal step is halved; warm-up and evaluation windows"
                " have no scientific basis yet"
            ),
            "blocks_start": True,
            "required_action": "approve the step pair and the stability-based warm-up rule, then the window numbers",
        },
        {
            "item": "calibration_targets_and_ranges_approval",
            "status": "Ready for Researcher Approval",
            "evidence": "layer-1 to layer-5 references computed; a 6-parameter optimisable vector is proposed",
            "blocks_start": True,
            "required_action": "approve the target set, the parameter vector and the frozen structure",
        },
        {
            "item": "scientific_tolerance_approval",
            "status": "Evidence Insufficient",
            "evidence": "clustered real uncertainty exists but no model-deviation tolerance is justified",
            "blocks_start": True,
            "required_action": "approve tolerance forms and their components, or declare the calibration exploratory",
        },
        {
            "item": "validation_isolation",
            "status": "Ready for Researcher Approval",
            "evidence": "fail-closed guard implemented and tested; validation window not read by this task",
            "blocks_start": True,
            "required_action": "confirm the isolation rules and the new-protocol-version rule after a failed validation",
        },
        {
            "item": "run_budget_approval",
            "status": "Evidence Insufficient",
            "evidence": (
                "a 300 s baseline benchmark exists for three integration-step candidates"
                f" ({len((sensitivity or {}).get('cost_benchmark', []))} runs), but no"
                " density-scaled benchmark at the target stratum has been executed"
            ),
            "blocks_start": True,
            "required_action": "approve the density-scaled benchmark, then the configuration/seed budget",
        },
    ]
    for item in items:
        if item["status"] not in ADMISSION_STATUSES:
            raise CalibrationReadinessError(f"unknown admission status {item['status']!r}")
    ready = [item["item"] for item in items if item["status"] == "Ready for Researcher Approval"]
    blocked = [item["item"] for item in items if item["status"] != "Ready for Researcher Approval"]
    return {
        "schema_version": f"{SCHEMA_ROOT}.stage-0-5-4b-admission.v1",
        "stage": "0.5.4-B",
        "generated_by": READINESS_RESULT_ID,
        "statuses": list(ADMISSION_STATUSES),
        "items": items,
        "awaiting_researcher_approval": ready,
        "blocking_items": blocked,
        "ready_to_start_stage_0_5_4b": False,
        "reason": (
            "every item must be approved by the researcher before a formal calibration starts;"
            " this task never self-approves a configuration"
        ),
        "stage_0_5_gate": "pending_simulation_sample",
        "scientific_claim_eligible": False,
    }


def researcher_decision_matrix() -> dict[str, Any]:
    decisions = [
        {
            "decision": "1_p2_formal_measurement",
            "question": "Accept the SUMO-versus-Stage-0.2 measurement equivalence and its scope?",
            "verified_facts": [
                "16 deterministic boundary cases agree between the two adapters",
                "net gap conversion, closing sign, TTC rule, P2 threshold, minimum duration, continuity, confirmation and exposure denominator verified",
                "one documented asymmetry: NGSIM labels a missing leader record as missing, SUMO labels a genuine no-leader state as not_applicable",
                "the 1e-3 m/s closing tolerance is inherited from the approved pipeline default",
            ],
            "recommended": "accept the equivalence for P2 event identity, confirmation and rate denominator, with the crosswalk mandatory and no raw status-label comparison",
            "alternatives": ["accept only after re-deriving the closing tolerance", "reject and keep SUMO P2 engineering-only"],
            "scientific_reason": "the event rule, identity scope, continuity and denominator are shared; only two documented label/origin differences remain",
            "main_risk": "a coarse (0.2 s) SUMO recording could be mistaken for 100 ms evidence - explicitly blocked by the cadence guard",
            "missing_evidence": ["an independent reviewer confirmation of the field crosswalk"],
            "ready_for_approval": True,
        },
        {
            "decision": "2_road_network",
            "question": "Generic highway corridor or a network with verified real geometry?",
            "verified_facts": [
                "the approved reference shows a 5-lane mainline plus three short ramp/auxiliary lanes over ~660 m",
                "local geometry assets exist but are not part of the approved reference",
            ],
            "recommended": "option C: calibrate on the generic corridor now and version a geometry upgrade later",
            "alternatives": ["option A only", "option B first, accepting the geometry-evidence cost"],
            "scientific_reason": "the calibration depends on the measurement contract and the traffic state, not on reproducing road geometry; geometry changes must carry their own provenance",
            "main_risk": "claiming road-structure-driven dynamics or a physical propagation speed validated on US-101",
            "missing_evidence": ["approved, versioned geometry evidence if option B is chosen"],
            "ready_for_approval": True,
        },
        {
            "decision": "3_traffic_demand",
            "question": "Which calibration basis, strata and target flow/density levels?",
            "verified_facts": [
                "interior cross-section passage rates and local densities are measurable inside the observed extent",
                "boundary entry demand, ramp flows and route choice are not identifiable",
                "60 s slice terciles give candidate low/medium/high density and free/transitional/congested speed strata",
            ],
            "recommended": "adopt the interior cross-section and local-density basis, with strata defined by pre-declared terciles of the calibration windows",
            "alternatives": ["a single representative state", "density levels taken from external evidence"],
            "scientific_reason": "the approved reference supports interior flow and local density, and strata must come from data rather than convenience",
            "main_risk": "treating a local density as a network density, or manufacturing an extreme state to obtain P2 events",
            "missing_evidence": ["approved target levels per stratum"],
            "ready_for_approval": True,
        },
        {
            "decision": "4_vehicle_fleet_and_driving_behaviour",
            "question": "Which vTypes, model structure, parameter ranges and optimisable dimensions?",
            "verified_facts": [
                "no vehicle class or length field exists in the approved reference",
                "speed, acceleration, gap and closing distributions are identifiable",
                "the engineering fixture vTypes are not scientific mappings",
            ],
            "recommended": "keep the SUMO default Krauss structure, optimise at most 6 parameters, and treat fleet composition as fixed/sensitivity-only until an approved class source exists",
            "alternatives": ["pause calibration until a class source is approved", "fix all vType parameters and calibrate only tau/accel/decel"],
            "scientific_reason": "a 6-parameter vector stays identifiable and attributable; class composition is simply not measurable now",
            "main_risk": "silently substituting pNEUMA class proportions or engineering fixture types",
            "missing_evidence": ["approved class/length evidence"],
            "ready_for_approval": True,
        },
        {
            "decision": "5_time_configuration",
            "question": "Which internal/recorded step and which warm-up/evaluation window?",
            "verified_facts": [
                "0.05 s internal with 0.1 s recorded keeps exact 100 ms evidence and finer integration",
                "cadence is audited and coarse recordings are refused",
                "no scientific basis exists yet for a specific warm-up duration",
            ],
            "recommended": "record at 0.1 s; choose internal 0.05 s if the benchmark shows acceptable cost; derive warm-up from a stability diagnostic",
            "alternatives": ["uniform 0.1 s", "keep the current engineering values as provisional"],
            "scientific_reason": "recorded cadence defines comparability; internal step only affects integration accuracy",
            "main_risk": "freezing an arbitrary warm-up number and calling it scientific",
            "missing_evidence": ["a pre-declared stability criterion and its tolerance"],
            "ready_for_approval": True,
        },
        {
            "decision": "6_scientific_tolerance",
            "question": "Which acceptance indicators, tolerance forms and numeric basis per layer?",
            "verified_facts": [
                "clustered vehicle-level intervals exist for the calibration windows",
                "row-level i.i.d. intervals are much narrower and inadmissible",
                "the real-real Energy Distance upper bound remains Not Identifiable",
            ],
            "recommended": "declare layer-wise tolerance forms now and defer the numbers until the five components are supplied; keep layer 3 and exposure structure as rule compliance",
            "alternatives": ["freeze numbers from clustered intervals alone", "declare the calibration exploratory with no gate"],
            "scientific_reason": "real-data uncertainty is not a model-deviation tolerance; conflating them would manufacture an easy pass",
            "main_risk": "using SUMO-inside-the-real-95%-interval as the sole acceptance rule",
            "missing_evidence": ["measurement-error, scenario-difference and allowed-deviation components"],
            "ready_for_approval": False,
        },
        {
            "decision": "7_calibration_experiment",
            "question": "Optimisation strategy, seeds, run budget, stopping rule and failure handling?",
            "verified_facts": [
                "a 6-parameter optimisable vector is proposed",
                "3 seeds per configuration with all seeds reported",
                "no wall-clock benchmark exists yet",
            ],
            "recommended": "staged calibration (network/demand -> kinematics -> following -> exposure -> P2 diagnosis -> stability) with a benchmark-derived budget",
            "alternatives": ["single-stage joint optimisation", "sensitivity-only study without optimisation"],
            "scientific_reason": "staging makes a failed layer attributable instead of compensating across layers",
            "main_risk": "tuning for a P2 rate at the expense of basic traffic behaviour",
            "missing_evidence": ["the benchmark and the final configuration count"],
            "ready_for_approval": False,
        },
    ]
    for decision in decisions:
        for key in ("verified_facts", "recommended", "alternatives", "scientific_reason", "main_risk", "missing_evidence", "ready_for_approval"):
            if key not in decision:
                raise CalibrationReadinessError(f"decision {decision['decision']} missing field {key}")
    return {
        "schema_version": f"{SCHEMA_ROOT}.researcher-decision-matrix.v1",
        "decisions": decisions,
        "ready_count": sum(1 for decision in decisions if decision["ready_for_approval"]),
        "pending_count": sum(1 for decision in decisions if not decision["ready_for_approval"]),
        "note": "no decision is pre-approved; the matrix is the researcher's approval surface",
    }


def scientific_admission_status(
    equivalence: Mapping[str, Any], checklist: Mapping[str, Any]
) -> dict[str, Any]:
    measurement_ready = bool(equivalence["overall_status"] == "pending_measurement_equivalence_review" and not equivalence["blocking_items"])
    return {
        "schema_version": f"{SCHEMA_ROOT}.scientific-admission-status.v1",
        "engineering_ready": True,
        "measurement_ready": "pending_researcher_acceptance" if measurement_ready else "blocked",
        "calibration_ready": False,
        "reality_coverage_accepted": False,
        "descriptive_status": (
            "Ready for Researcher Approval"
            if not checklist["blocking_items"]
            else "Blocked by Scientific Configuration"
        ),
        "blocked_by": checklist["blocking_items"],
        "allowed_statuses": list(ADMISSION_STATUSES),
        "stage_0_5_gate": "pending_simulation_sample",
        "protocol_lock_allowed": False,
        "stage_1_1_allowed": False,
        "reality_coverage_requires": ["stage_0_5_4b calibration", "stage_0_5_5 independent validation"],
    }


# --------------------------------------------------------------------------------------
# orchestration
# --------------------------------------------------------------------------------------


def run_calibration_readiness_audit(
    *,
    repo_root: str | Path,
    output_dir: str | Path,
    write_package: bool = True,
) -> dict[str, Any]:
    """Run the Stage 0.5.4-A audit and optionally seal a result package."""

    root = Path(repo_root).resolve()
    out = Path(output_dir).resolve() if output_dir is not None else None
    if write_package and out is not None:
        if out.exists():
            raise CalibrationReadinessError(f"refusing to overwrite readiness package: {out}")
        out.mkdir(parents=True, exist_ok=False)

    binding_check = verify_against_real_reference_manifest(root)
    guard = CalibrationValidationGuard(
        log_path=(out / "access_audit.json") if (write_package and out is not None) else None
    )
    states, state_reads = load_calibration_states(root, guard)
    events, event_read = load_formal_events(root, guard)
    boundary = run_p2_boundary_matrix()
    equivalence = measurement_equivalence_matrix(boundary)

    summaries = {
        group: window_summary(
            frame, events[events["source"].astype(str).eq(group)] if len(events) else None
        )
        for group, frame in states.items()
    }
    uncertainty = clustered_uncertainty(summaries)
    identifiability = {group: demand_identifiability(frame) for group, frame in states.items()}
    strata = {group: candidate_strata(frame) for group, frame in states.items()}
    objectives = calibration_objectives(summaries)
    sensitivity = load_timestep_sensitivity(root)
    checklist = stage_0_5_4b_admission_checklist(equivalence, summaries, sensitivity)
    admission = scientific_admission_status(equivalence, checklist)

    payload = {
        "config": {
            "schema_version": f"{SCHEMA_ROOT}.config.v1",
            "result_id": READINESS_RESULT_ID,
            "task": "AAD-0.5.4-A calibration readiness and parameter-protocol audit",
            "upstream_results": [FORMAL_REFERENCE_RESULT_ID, SUMO_ENGINEERING_RESULT_ID, STAGE_0_2_REFERENCE_RESULT_ID],
            "formal_measurement_specification": FORMAL_ALGORITHM_VERSION,
            "calibration_windows": list(CALIBRATION_GROUPS),
            "validation_window": list(VALIDATION_GROUPS),
            "auxiliary_sources_not_analysed": list(AUXILIARY_GROUPS),
            "locked_holdout_accessed": False,
            "validation_window_read": False,
            "p2_ttc_threshold_s": FORMAL_TTC_THRESHOLD_S,
            "p2_minimum_duration_s": 0.2,
            "recorded_observation_step_s": FORMAL_OBSERVATION_STEP_S,
            "closing_epsilon_mps": NGSIM_CLOSING_EPSILON_MPS,
            "bootstrap": {"resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED, "cluster_unit": "trajectory"},
            "time_slice_s": TIME_SLICE_S,
            "stratum_slice_s": STRATUM_SLICE_S,
            "density_window_m": list(DENSITY_WINDOW_M),
            "cross_section_planes_m": list(CROSS_SECTION_PLANES_M),
            "engineering_only": True,
            "scientific_claim_eligible": False,
            "stage_0_5_gate": "pending_simulation_sample",
        },
        "source_binding_check": binding_check,
        "state_reads": state_reads,
        "formal_event_read": event_read,
        "window_summaries": summaries,
        "clustered_uncertainty": uncertainty,
        "demand_identifiability": identifiability,
        "candidate_strata": strata,
        "network_options": network_options(),
        "vehicle_fleet_candidates": vehicle_fleet_candidates(summaries),
        "following_model_options": following_model_options(),
        "parameter_identifiability": parameter_identifiability(),
        "time_step_options": time_step_options(sensitivity),
        "timestep_sensitivity": sensitivity,
        "calibration_objectives": objectives,
        "target_versus_threshold": calibration_target_vs_threshold(),
        "candidate_calibration_protocol": candidate_calibration_protocol(summaries, sensitivity),
        "stage_0_5_4b_admission_checklist": checklist,
        "scientific_admission_status": admission,
        "researcher_decision_matrix": researcher_decision_matrix(),
        "measurement_equivalence": equivalence,
        "crosswalks": {
            "ngsim_status_crosswalk": NGSIM_STATUS_CROSSWALK,
            "missing_reason_equivalence": MISSING_REASON_EQUIVALENCE,
            "net_gap_semantics": NET_GAP_SEMANTICS,
            "closing_speed_semantics": CLOSING_SPEED_SEMANTICS,
        },
        "audit": {
            "schema_version": f"{SCHEMA_ROOT}.audit.v1",
            "created_at_utc": _utc_now(),
            "result_id": READINESS_RESULT_ID,
            "engineering_only": True,
            "scientific_claim_eligible": False,
            "measurement_equivalence_status": equivalence["overall_status"],
            "boundary_cases": equivalence["boundary_case_count"],
            "boundary_cases_all_as_expected": equivalence["boundary_cases_all_as_expected"],
            "blocking_measurement_items": equivalence["blocking_items"],
            "ready_to_start_stage_0_5_4b": checklist["ready_to_start_stage_0_5_4b"],
            "blocking_items": checklist["blocking_items"],
            "stage_0_5_gate": "pending_simulation_sample",
            "protocol_lock_allowed": False,
            "stage_1_1_allowed": False,
            "locked_holdout_accessed": False,
            "validation_window_read": False,
            "validation_window_rows_materialised": 0,
            "analysed_sources": sorted(states),
            "p2_events_used": {group: int(summaries[group]["p2"]["events"]) for group in sorted(summaries)},
            "time_step_sensitivity_available": bool(sensitivity.get("available")),
            "time_step_sensitivity_sha256": sensitivity.get("sha256"),
            "time_step_boundary_shift_recorded": bool(sensitivity.get("comparisons")),
            "tolerances_frozen": False,
            "parameters_approved": [],
        },
    }

    if write_package and out is not None:
        _write_package(out, payload, root)
    return payload


def _write_package(out: Path, payload: Mapping[str, Any], root: Path) -> None:
    _write_json(out / "config.json", payload["config"])
    _write_json(out / "audit.json", payload["audit"])
    _write_json(out / "measurement_equivalence_matrix.json", payload["measurement_equivalence"])
    _write_json(
        out / "calibration_source_analysis.json",
        {
            "schema_version": f"{SCHEMA_ROOT}.calibration-source-analysis.v1",
            "source_binding_check": payload["source_binding_check"],
            "state_reads": payload["state_reads"],
            "formal_event_read": payload["formal_event_read"],
            "window_summaries": {
                group: {key: value for key, value in summary.items() if key != "per_vehicle"}
                for group, summary in payload["window_summaries"].items()
            },
            "clustered_uncertainty": payload["clustered_uncertainty"],
            "demand_identifiability": payload["demand_identifiability"],
            "candidate_strata": payload["candidate_strata"],
        },
    )
    _write_json(
        out / "candidate_protocol.json",
        {
            "schema_version": f"{SCHEMA_ROOT}.candidate-protocol-package.v1",
            "candidate_calibration_protocol": payload["candidate_calibration_protocol"],
            "calibration_objectives": payload["calibration_objectives"],
            "target_versus_threshold": payload["target_versus_threshold"],
            "time_step_options": payload["time_step_options"],
            "timestep_sensitivity": payload["timestep_sensitivity"],
            "network_options": payload["network_options"],
            "vehicle_fleet_candidates": payload["vehicle_fleet_candidates"],
            "following_model_options": payload["following_model_options"],
            "parameter_identifiability": payload["parameter_identifiability"],
        },
    )
    _write_json(
        out / "measurement_crosswalks.json",
        {"schema_version": f"{SCHEMA_ROOT}.crosswalks.v1", **payload["crosswalks"]},
    )
    _write_json(out / "stage_0_5_4b_admission_checklist.json", payload["stage_0_5_4b_admission_checklist"])
    _write_json(out / "researcher_decision_matrix.json", payload["researcher_decision_matrix"])
    _write_json(out / "scientific_admission_status.json", payload["scientific_admission_status"])
    _write_json(
        out / "provenance.json",
        {
            "schema_version": f"{SCHEMA_ROOT}.provenance.v1",
            "result_id": READINESS_RESULT_ID,
            "created_at_utc": _utc_now(),
            "locked_holdout_accessed": False,
            "validation_window_read": False,
            "engineering_only": True,
            "scientific_claim_eligible": False,
            "code_sha256": {
                "code/src/riskprop/stage_0_5_calibration_readiness.py": _sha256_file(Path(__file__).resolve()),
                "code/src/riskprop/stage_0_5_sumo.py": _sha256_file(
                    Path(__file__).resolve().with_name("stage_0_5_sumo.py")
                ),
                "code/scripts/run_stage_0_5_calibration_readiness.py": _sha256_file(
                    Path(__file__).resolve().parents[2] / "scripts" / "run_stage_0_5_calibration_readiness.py"
                ),
            },
            "real_reference_manifest_sha256": payload["source_binding_check"]["manifest_sha256"],
        },
    )
    manifest = _seal_package(out)
    return manifest


def _seal_package(out: Path) -> dict[str, Any]:
    files = sorted(
        path for path in out.iterdir()
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
    manifest = {
        "schema_version": f"{SCHEMA_ROOT}.manifest.v1",
        "result_id": READINESS_RESULT_ID,
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}
            for path in files
        ],
    }
    _write_json(out / "manifest.json", manifest)
    files.append(out / "manifest.json")
    (out / "SHA256SUMS").write_text(
        "\n".join(f"{_sha256_file(path)}  {path.name}" for path in files) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest
