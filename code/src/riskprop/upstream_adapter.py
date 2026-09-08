"""Explicit, non-destructive adapters for importing DRIFT assets into AAD."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from .formal_artifacts import TABLE_REQUIRED_COLUMNS


class UpstreamAdapterError(ValueError):
    """Raised when an upstream field cannot be mapped without inventing data."""


DRIFT_TO_AAD_CELL = {
    "r00": "s0c0",
    "r01": "s0c1",
    "r10": "s1c0",
    "r11": "s1c1",
}

DRIFT_STATE_REQUIRED = frozenset(
    {
        "step",
        "time_s",
        "sumo_seed",
        "cell",
        "vehicle_id",
        "edge",
        "x",
        "y",
        "lane_id",
        "speed",
        "headway",
        "net_gap",
        "relative_speed",
        "leader_id",
        "follower_id",
        "realized_accel",
    }
)

DRIFT_MECHANISM_REQUIRED = frozenset(
    {
        "event_id",
        "step",
        "vehicle_role",
        "message_generated",
        "message_sent",
        "message_delivered",
        "validation_time_s",
        "message_provenance_valid",
        "adopted",
    }
)


def map_drift_cell(cell: str) -> str:
    try:
        return DRIFT_TO_AAD_CELL[str(cell)]
    except KeyError as exc:
        raise UpstreamAdapterError(f"Unknown DRIFT cell: {cell!r}") from exc


def _require_columns(records: pd.DataFrame, required: set[str] | frozenset[str], label: str) -> None:
    missing = sorted(set(required) - set(records.columns))
    if missing:
        raise UpstreamAdapterError(
            f"{label} cannot be converted; missing explicit fields: {', '.join(missing)}"
        )


def _finite_numeric(records: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    for column in columns:
        values = pd.to_numeric(records[column], errors="coerce")
        if values.isna().any() or not values.map(lambda value: math.isfinite(float(value))).all():
            raise UpstreamAdapterError(f"{label} contains non-finite numeric field: {column}")


def convert_drift_state_rows(
    records: pd.DataFrame,
    *,
    run_id: str,
    experiment_id: str,
    scenario_id: str,
) -> pd.DataFrame:
    """Convert only explicitly observed DRIFT state fields to AAD state schema."""

    _require_columns(records, DRIFT_STATE_REQUIRED, "DRIFT state")
    if not run_id or not experiment_id or not scenario_id:
        raise UpstreamAdapterError("run_id, experiment_id and scenario_id are required")
    _finite_numeric(
        records,
        ("step", "time_s", "sumo_seed", "x", "y", "speed", "headway", "net_gap", "relative_speed", "realized_accel"),
        "DRIFT state",
    )
    converted = pd.DataFrame(
        {
            "run_id": str(run_id),
            "experiment_id": str(experiment_id),
            "scenario_id": str(scenario_id),
            "cell_id": records["cell"].map(map_drift_cell),
            "configured_seed": pd.to_numeric(records["sumo_seed"], downcast="integer"),
            "simulation_seed": pd.to_numeric(records["sumo_seed"], downcast="integer"),
            "time_s": pd.to_numeric(records["time_s"]),
            "vehicle_id": records["vehicle_id"].astype(str),
            "edge_id": records["edge"].astype(str),
            "lane_id": records["lane_id"].astype(str),
            "x_m": pd.to_numeric(records["x"]),
            "y_m": pd.to_numeric(records["y"]),
            "speed_mps": pd.to_numeric(records["speed"]),
            "acceleration_mps2": pd.to_numeric(records["realized_accel"]),
            "leader_id": records["leader_id"].astype(str),
            "net_gap_m": pd.to_numeric(records["net_gap"]),
            "relative_speed_mps": pd.to_numeric(records["relative_speed"]),
        },
        columns=TABLE_REQUIRED_COLUMNS["state.parquet"],
    )
    return converted


def validate_drift_mechanism_fields(records: pd.DataFrame) -> dict[str, Any]:
    """Check whether a DRIFT mechanism log exposes AAD's lifecycle fields."""

    _require_columns(records, DRIFT_MECHANISM_REQUIRED, "DRIFT mechanism")
    return {
        "record_count": int(len(records)),
        "aad_lifecycle_ready": True,
        "required_fields": sorted(DRIFT_MECHANISM_REQUIRED),
    }


def audit_flow_dependency(flow_repo: Path) -> dict[str, Any]:
    """Report Flow availability without importing or mutating the environment."""

    flow_repo = Path(flow_repo).expanduser().resolve()
    package_dir = flow_repo / "flow"
    if not flow_repo.is_dir() or not package_dir.is_dir():
        return {
            "flow_repo": str(flow_repo),
            "available": False,
            "reason": "flow_repository_missing",
        }
    return {
        "flow_repo": str(flow_repo),
        "available": True,
        "reason": "flow_repository_present",
    }
