"""Engineering-only Stage I mechanism contracts.

This module composes the existing four-cell and protocol-lifecycle contracts.  It
records information-chain events, action observations and risk observations in a
single auditable timeline.  It deliberately refuses to infer a physical arrival
time from distance, speed or event ordering when that time is not supplied.

The functions are suitable for deterministic fixtures and integration checks;
they are not a Stage 1.1 estimator and do not read locked holdout data.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

import pandas as pd

from .formal_design import (
    EXPECTED_CELL_IDS,
    FormalDesignError,
    validate_four_cell_configs,
    validate_pre_treatment_equivalence,
    validate_protocol_lifecycle,
)
from .prelock_metrics import first_sustained_divergence


MECHANISM_EVENT_COLUMNS = (
    "run_id",
    "pair_id",
    "event_id",
    "event_type",
    "time_s",
    "vehicle_id",
    "region",
    "source",
)


class MechanismContractError(ValueError):
    """Raised when a mechanism fixture cannot be audited without guessing."""


def _finite_time(values: Iterable[object], label: str) -> list[float]:
    result = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise MechanismContractError(f"{label} contains a non-numeric time") from exc
        if not math.isfinite(number):
            raise MechanismContractError(f"{label} contains a non-finite time")
        result.append(number)
    return result


def validate_event_timeline(records: pd.DataFrame) -> dict[str, Any]:
    """Validate an ordered event log without treating ordering as causality."""

    required = set(MECHANISM_EVENT_COLUMNS)
    missing = sorted(required - set(records.columns))
    if missing:
        raise MechanismContractError(
            "mechanism timeline is missing fields: " + ", ".join(missing)
        )
    if records.empty:
        return {"record_count": 0, "ordered": True, "event_types": {}, "timeline_pass": True}
    times = _finite_time(records["time_s"].tolist(), "mechanism timeline")
    ordered = all(left <= right for left, right in zip(times, times[1:]))
    if not ordered:
        raise MechanismContractError("mechanism timeline must be non-decreasing by time_s")
    if records[["run_id", "pair_id", "event_id", "event_type", "vehicle_id"]].isna().any().any():
        raise MechanismContractError("mechanism timeline contains missing identity fields")
    counts = records["event_type"].astype(str).value_counts().sort_index().to_dict()
    return {
        "record_count": int(len(records)),
        "ordered": True,
        "event_types": {str(key): int(value) for key, value in counts.items()},
        "timeline_pass": True,
    }


def compare_paired_action(
    baseline: pd.DataFrame,
    treatment: pd.DataFrame,
    *,
    treatment_start_s: float,
    speed_tolerance_mps: float,
    sustain_s: float,
) -> dict[str, Any]:
    """Find a first sustained action difference on an exact common time grid."""

    required = {"time_s", "vehicle_id", "speed_mps"}
    for label, frame in (("baseline", baseline), ("treatment", treatment)):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise MechanismContractError(f"{label} action table is missing: {', '.join(missing)}")
    if not math.isfinite(float(treatment_start_s)) or speed_tolerance_mps < 0:
        raise MechanismContractError("invalid action comparison parameters")
    left = baseline[["time_s", "vehicle_id", "speed_mps"]].copy()
    right = treatment[["time_s", "vehicle_id", "speed_mps"]].copy()
    left["time_s"] = pd.to_numeric(left["time_s"], errors="coerce")
    right["time_s"] = pd.to_numeric(right["time_s"], errors="coerce")
    left["speed_mps"] = pd.to_numeric(left["speed_mps"], errors="coerce")
    right["speed_mps"] = pd.to_numeric(right["speed_mps"], errors="coerce")
    joined = left.merge(right, on=["vehicle_id", "time_s"], suffixes=("_baseline", "_treatment"))
    if joined.empty:
        return {
            "status": "unknown_no_common_observations",
            "common_observations": 0,
            "first_action_change_time_s": None,
            "effect_observed": None,
        }
    joined = joined.sort_values(["vehicle_id", "time_s"], kind="stable")
    joined = joined.loc[joined["time_s"] >= float(treatment_start_s)]
    joined = joined.loc[joined["speed_mps_baseline"].notna() & joined["speed_mps_treatment"].notna()]
    if joined.empty:
        return {
            "status": "unknown_no_post_treatment_observations",
            "common_observations": 0,
            "first_action_change_time_s": None,
            "effect_observed": None,
        }
    # The fixture has one target vehicle.  If a production caller supplies more,
    # each vehicle is audited separately and the earliest identifiable change is kept.
    candidates: list[float] = []
    for _, group in joined.groupby("vehicle_id", sort=True):
        times = group["time_s"].to_numpy(float)
        differences = (
            group["speed_mps_treatment"] - group["speed_mps_baseline"]
        ).abs().to_numpy(float)
        first = first_sustained_divergence(
            times.tolist(),
            differences.tolist(),
            tolerance=float(speed_tolerance_mps),
            sustain_s=float(sustain_s),
        )
        if math.isfinite(first):
            candidates.append(float(first))
    first_change = min(candidates) if candidates else None
    return {
        "status": "pass" if first_change is not None else "no_observable_action_change",
        "common_observations": int(len(joined)),
        "first_action_change_time_s": first_change,
        "effect_observed": first_change is not None,
        "speed_tolerance_mps": float(speed_tolerance_mps),
        "sustain_s": float(sustain_s),
    }


def build_joint_timeline(
    *,
    message_events: pd.DataFrame,
    action_events: pd.DataFrame,
    risk_events: pd.DataFrame,
    physical_arrival_time_s: float | None,
) -> dict[str, Any]:
    """Join information and physical observations while preserving Unknown."""

    frames = []
    for source, frame in (
        ("information", message_events),
        ("action", action_events),
        ("risk", risk_events),
    ):
        if frame.empty:
            continue
        required = {"run_id", "pair_id", "event_id", "event_type", "time_s", "vehicle_id", "region"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise MechanismContractError(f"{source} events are missing: {', '.join(missing)}")
        part = frame.copy()
        part["source"] = source
        frames.append(part[list(MECHANISM_EVENT_COLUMNS)])
    combined = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["time_s", "source", "event_id"], kind="stable")
        .reset_index(drop=True)
        if frames
        else pd.DataFrame(columns=MECHANISM_EVENT_COLUMNS)
    )
    audit = validate_event_timeline(combined)
    if physical_arrival_time_s is None or not math.isfinite(float(physical_arrival_time_s)):
        comparison = {
            "information_before_physical": "Unknown",
            "physical_arrival_time_s": None,
            "reason": "No independently evidenced physical arrival time was supplied; ordering is not treated as proof.",
        }
    else:
        arrival = float(physical_arrival_time_s)
        adopted = combined.loc[combined["event_type"].eq("message_adopted"), "time_s"]
        action = combined.loc[combined["event_type"].eq("action_change"), "time_s"]
        risk = combined.loc[combined["event_type"].eq("risk_observation"), "time_s"]
        comparison = {
            "information_before_physical": bool(not adopted.empty and float(adopted.min()) < arrival),
            "action_before_physical": bool(not action.empty and float(action.min()) < arrival),
            "risk_observation_before_physical": bool(not risk.empty and float(risk.min()) < arrival),
            "physical_arrival_time_s": arrival,
            "reason": "Comparison uses supplied event-specific physical arrival time.",
        }
    return {
        "schema_version": "aad.stage-i.joint-timeline.v1",
        "timeline": combined.to_dict(orient="records"),
        "timeline_audit": audit,
        "time_comparison": comparison,
        "scientific_claim_eligible": False,
    }


def audit_four_cell_mechanism_fixture(
    configs: dict[str, dict[str, Any]],
    lifecycle_by_cell: dict[str, pd.DataFrame],
    pre_treatment: pd.DataFrame,
) -> dict[str, Any]:
    """Run existing four-cell/lifecycle contracts for an engineering fixture."""

    config_audit = validate_four_cell_configs(configs)
    lifecycle_audit = {}
    for cell_id in EXPECTED_CELL_IDS:
        lifecycle_audit[cell_id] = validate_protocol_lifecycle(
            lifecycle_by_cell[cell_id],
            source_present=bool(configs[cell_id]["source_present"]),
            channel_enabled=bool(configs[cell_id]["channel_enabled"]),
        )
    pre_audit = validate_pre_treatment_equivalence(
        pre_treatment,
        treatment_start_s=1.0,
        key_columns=("vehicle_id", "time_s"),
        exact_columns=("edge_id", "lane_id"),
        numeric_tolerances={"speed_mps": 0.0, "x_m": 0.0},
    )
    return {
        "four_cell": config_audit,
        "lifecycle": lifecycle_audit,
        "pre_treatment": pre_audit,
        "scientific_claim_eligible": False,
    }


def build_engineering_fixture() -> dict[str, Any]:
    """Create a deterministic four-cell fixture for interface validation only."""

    configs: dict[str, dict[str, Any]] = {}
    lifecycle: dict[str, pd.DataFrame] = {}
    for source_present in (False, True):
        for channel_enabled in (False, True):
            cell_id = f"s{int(source_present)}c{int(channel_enabled)}"
            run_id = f"task20_fixture_{cell_id}"
            configs[cell_id] = {
                "schema_version": "aad.stage-i.engineering-fixture.v1",
                "experiment_id": "stage_i_engineering_fixture",
                "theory_version": "aad-mechanism-prototype-v1",
                "protocol_version": "stage_i.engineering-fixture.v1",
                "scenario_id": "task20_synthetic_only",
                "pair_id": "task20_fixture_pair",
                "configured_seed": 20261101,
                "simulation_seed": 20261101,
                "source_vehicle_id": "source_0",
                "target_vehicle_id": "target_0",
                "window_start_s": 0.0,
                "window_end_s": 3.0,
                "time_step_s": 0.5,
                "run_id": run_id,
                "cell_id": cell_id,
                "source_present": source_present,
                "channel_enabled": channel_enabled,
                "output_dir": f"task20_20261101/stage_i_engineering_fixture/{cell_id}",
                "fixture_only": True,
                "scientific_claim_eligible": False,
            }
            generated = source_present
            sent = source_present and channel_enabled
            delivered = sent
            adopted = delivered
            lifecycle[cell_id] = pd.DataFrame(
                [
                    {
                        "message_id": f"task20_message_{cell_id}",
                        "message_generated": generated,
                        "message_sent": sent,
                        "message_dropped": generated and not sent,
                        "message_delivered": delivered,
                        "source_valid": source_present,
                        "target_valid": True,
                        "freshness_valid": adopted,
                        "adopted": adopted,
                        "generated_time_s": 1.0 if generated else None,
                        "sent_time_s": 1.1 if sent else None,
                        "delivered_time_s": 1.2 if delivered else None,
                        "validation_time_s": 1.3 if delivered else None,
                        "adopted_time_s": 1.4 if adopted else None,
                        "message_age_s": 0.4 if adopted else None,
                        "message_kind": "source" if source_present else "none",
                    }
                ]
            )
    rows = []
    for cell_id in EXPECTED_CELL_IDS:
        for time_s in (0.0, 0.5):
            rows.append(
                {
                    "cell_id": cell_id,
                    "time_s": time_s,
                    "vehicle_id": "target_0",
                    "edge_id": "road_0",
                    "lane_id": "lane_0",
                    "speed_mps": 10.0,
                    "x_m": 20.0 + 10.0 * time_s,
                }
            )
    pre_treatment = pd.DataFrame(rows)
    message_events = pd.DataFrame(
        [
            {"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "m1", "event_type": "message_generated", "time_s": 1.0, "vehicle_id": "source_0", "region": "source", "source": "information"},
            {"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "m2", "event_type": "message_sent", "time_s": 1.1, "vehicle_id": "source_0", "region": "source", "source": "information"},
            {"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "m3", "event_type": "message_delivered", "time_s": 1.2, "vehicle_id": "target_0", "region": "target", "source": "information"},
            {"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "m4", "event_type": "message_validated", "time_s": 1.3, "vehicle_id": "target_0", "region": "target", "source": "information"},
            {"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "m5", "event_type": "message_adopted", "time_s": 1.4, "vehicle_id": "target_0", "region": "target", "source": "information"},
        ]
    )
    action_events = pd.DataFrame(
        [{"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "a1", "event_type": "action_change", "time_s": 1.5, "vehicle_id": "target_0", "region": "target", "source": "action"}]
    )
    risk_events = pd.DataFrame(
        [{"run_id": "task20_fixture_s1c1", "pair_id": "task20_fixture_pair", "event_id": "r1", "event_type": "risk_observation", "time_s": 2.0, "vehicle_id": "target_0", "region": "target", "source": "risk"}]
    )
    baseline = pd.DataFrame({"time_s": (1.0, 1.5, 2.0), "vehicle_id": ("target_0",) * 3, "speed_mps": (10.0, 10.0, 10.0)})
    treatment = pd.DataFrame({"time_s": (1.0, 1.5, 2.0), "vehicle_id": ("target_0",) * 3, "speed_mps": (10.0, 9.0, 9.0)})
    return {
        "configs": configs,
        "lifecycle": lifecycle,
        "pre_treatment": pre_treatment,
        "message_events": message_events,
        "action_events": action_events,
        "risk_events": risk_events,
        "baseline": baseline,
        "treatment": treatment,
    }
