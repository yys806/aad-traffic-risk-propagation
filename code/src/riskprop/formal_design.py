"""Counterfactual design contracts for the preregistered four-cell experiment."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import pandas as pd


EXPECTED_CELL_IDS = ("s0c0", "s0c1", "s1c0", "s1c1")
_CELL_SPECIFIC_FIELDS = frozenset(
    {"run_id", "cell_id", "source_present", "channel_enabled", "output_dir"}
)
_REQUIRED_COMMON_FIELDS = frozenset(
    {
        "schema_version",
        "experiment_id",
        "theory_version",
        "protocol_version",
        "scenario_id",
        "pair_id",
        "configured_seed",
        "simulation_seed",
        "source_vehicle_id",
        "target_vehicle_id",
        "window_start_s",
        "window_end_s",
        "time_step_s",
    }
)


class FormalDesignError(ValueError):
    """Raised when a counterfactual design violates the frozen theory contract."""


def _canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _all_finite(values: pd.Series) -> bool:
    return bool(values.map(lambda value: math.isfinite(float(value))).all())


def validate_four_cell_configs(
    configs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Require a four-cell design whose only scientific difference is S×C."""

    if set(configs) != set(EXPECTED_CELL_IDS):
        missing = [cell for cell in EXPECTED_CELL_IDS if cell not in configs]
        extra = sorted(set(configs) - set(EXPECTED_CELL_IDS))
        details = []
        if missing:
            details.append(f"missing cells: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected cells: {', '.join(extra)}")
        raise FormalDesignError("Four-cell config set invalid (" + "; ".join(details) + ")")

    baseline: dict[str, Any] | None = None
    baseline_cell: str | None = None
    run_ids: set[str] = set()
    pair_ids: set[str] = set()
    for cell_id in EXPECTED_CELL_IDS:
        config = configs[cell_id]
        if not isinstance(config, dict):
            raise FormalDesignError(f"Config {cell_id} must be an object")
        expected_source = cell_id[1] == "1"
        expected_channel = cell_id[3] == "1"
        if config.get("cell_id") != cell_id:
            raise FormalDesignError(f"Config cell_id mismatch for {cell_id}")
        if config.get("source_present") is not expected_source:
            raise FormalDesignError(f"Config {cell_id} has an invalid source_present flag")
        if config.get("channel_enabled") is not expected_channel:
            raise FormalDesignError(f"Config {cell_id} has an invalid channel_enabled flag")
        missing_fields = sorted(_REQUIRED_COMMON_FIELDS - set(config))
        if missing_fields:
            raise FormalDesignError(
                f"Config {cell_id} is missing required fields: {', '.join(missing_fields)}"
            )
        run_id = config.get("run_id")
        if not isinstance(run_id, str) or not run_id or run_id in run_ids:
            raise FormalDesignError(f"Config {cell_id} has a non-unique run_id")
        run_ids.add(run_id)
        pair_ids.add(str(config["pair_id"]))
        common = {key: value for key, value in config.items() if key not in _CELL_SPECIFIC_FIELDS}
        if baseline is None:
            baseline = common
            baseline_cell = cell_id
        elif common != baseline:
            differing = sorted(
                key
                for key in set(common) | set(baseline)
                if common.get(key) != baseline.get(key)
            )
            raise FormalDesignError(
                f"Four-cell configs differ outside S×C; differing fields: {', '.join(differing)}"
            )

    if len(pair_ids) != 1:
        raise FormalDesignError("Four-cell configs must share exactly one pair_id")
    assert baseline is not None and baseline_cell is not None
    return {
        "cell_ids": list(EXPECTED_CELL_IDS),
        "pair_id": next(iter(pair_ids)),
        "baseline_cell": baseline_cell,
        "common_config_sha256": _canonical_sha256(baseline),
        "scientific_differences": ["source_present", "channel_enabled"],
    }


_LIFECYCLE_BOOLEAN_COLUMNS = (
    "message_generated",
    "message_sent",
    "message_dropped",
    "message_delivered",
    "source_valid",
    "target_valid",
    "freshness_valid",
    "adopted",
)
_LIFECYCLE_TIME_COLUMNS = (
    "generated_time_s",
    "sent_time_s",
    "delivered_time_s",
    "validation_time_s",
    "adopted_time_s",
    "message_age_s",
)


def validate_protocol_lifecycle(
    records: pd.DataFrame,
    *,
    source_present: bool,
    channel_enabled: bool,
) -> dict[str, Any]:
    """Validate the frozen generate→send→deliver→validate→adopt chain."""

    required = {"message_id", *_LIFECYCLE_BOOLEAN_COLUMNS, *_LIFECYCLE_TIME_COLUMNS}
    missing = sorted(required - set(records.columns))
    if missing:
        raise FormalDesignError(
            f"Protocol records are missing lifecycle fields: {', '.join(missing)}"
        )
    if records.empty:
        return {
            "record_count": 0,
            "generated_count": 0,
            "sent_count": 0,
            "delivered_count": 0,
            "adopted_count": 0,
            "lifecycle_pass": True,
        }

    flags = {
        column: records[column].fillna(False).astype(bool)
        for column in _LIFECYCLE_BOOLEAN_COLUMNS
    }
    message_kind = records.get("message_kind", pd.Series("source", index=records.index)).fillna("source").astype(str)
    source_message = message_kind != "sham"
    if not source_present and (flags["message_generated"] & source_message).any():
        raise FormalDesignError("A source-absent cell generated a source message")
    if not channel_enabled and (
        flags["message_sent"].any()
        or flags["message_delivered"].any()
        or flags["adopted"].any()
    ):
        raise FormalDesignError("A closed channel sent, delivered, or adopted a message")
    if (flags["message_sent"] & ~flags["message_generated"]).any():
        raise FormalDesignError("message_sent requires message_generated")
    if (flags["message_delivered"] & ~flags["message_sent"]).any():
        raise FormalDesignError("message_delivered requires message_sent")
    if (flags["message_delivered"] & flags["message_dropped"]).any():
        raise FormalDesignError("A message cannot be both dropped and delivered")
    if (flags["adopted"] & ~flags["message_delivered"]).any():
        raise FormalDesignError("adopted requires message_delivered")
    valid_for_adoption = (
        flags["source_valid"] & flags["target_valid"] & flags["freshness_valid"]
    )
    if (flags["adopted"] & ~valid_for_adoption).any():
        raise FormalDesignError(
            "adopted requires source_valid, target_valid, and freshness_valid"
        )

    times = {
        column: pd.to_numeric(records[column], errors="coerce")
        for column in _LIFECYCLE_TIME_COLUMNS
    }
    stage_requirements = (
        ("message_generated", "generated_time_s"),
        ("message_sent", "sent_time_s"),
        ("message_delivered", "delivered_time_s"),
        ("message_delivered", "validation_time_s"),
        ("adopted", "adopted_time_s"),
    )
    for flag, column in stage_requirements:
        if (flags[flag] & times[column].isna()).any():
            raise FormalDesignError(f"{flag} requires a finite {column}")
    ordered_pairs = (
        ("message_sent", "generated_time_s", "sent_time_s"),
        ("message_delivered", "sent_time_s", "delivered_time_s"),
        ("message_delivered", "delivered_time_s", "validation_time_s"),
        ("adopted", "validation_time_s", "adopted_time_s"),
    )
    for flag, earlier, later in ordered_pairs:
        invalid = flags[flag] & (times[later] < times[earlier])
        if invalid.any():
            raise FormalDesignError(
                f"Protocol lifecycle time order violated: {earlier} > {later}"
            )
    adopted = flags["adopted"]
    expected_age = times["adopted_time_s"] - times["generated_time_s"]
    invalid_age = adopted & (
        times["message_age_s"].isna()
        | ((times["message_age_s"] - expected_age).abs() > 1e-9)
    )
    if invalid_age.any():
        raise FormalDesignError(
            "message_age_s must equal adopted_time_s - generated_time_s"
        )
    return {
        "record_count": int(len(records)),
        "generated_count": int(flags["message_generated"].sum()),
        "sent_count": int(flags["message_sent"].sum()),
        "delivered_count": int(flags["message_delivered"].sum()),
        "adopted_count": int(flags["adopted"].sum()),
        "lifecycle_pass": True,
    }


def validate_pre_treatment_equivalence(
    records: pd.DataFrame,
    *,
    treatment_start_s: float,
    key_columns: tuple[str, ...],
    exact_columns: tuple[str, ...],
    numeric_tolerances: dict[str, float],
) -> dict[str, Any]:
    """Require four-cell target trajectories to share one aligned prefix."""

    if not math.isfinite(float(treatment_start_s)):
        raise FormalDesignError("treatment_start_s must be finite")
    if not key_columns:
        raise FormalDesignError("At least one pre-treatment key column is required")
    if not numeric_tolerances:
        raise FormalDesignError("At least one numeric equivalence field is required")
    for column, tolerance in numeric_tolerances.items():
        if not math.isfinite(float(tolerance)) or float(tolerance) < 0:
            raise FormalDesignError(
                f"Numeric tolerance for {column} must be finite and non-negative"
            )
    required = {
        "cell_id",
        "time_s",
        *key_columns,
        *exact_columns,
        *numeric_tolerances,
    }
    missing = sorted(required - set(records.columns))
    if missing:
        raise FormalDesignError(
            f"Pre-treatment records are missing fields: {', '.join(missing)}"
        )
    actual_cells = set(records["cell_id"].dropna().astype(str))
    if actual_cells != set(EXPECTED_CELL_IDS):
        raise FormalDesignError("Pre-treatment records must contain exactly four cells")

    time_s = pd.to_numeric(records["time_s"], errors="coerce")
    if time_s.isna().any() or not _all_finite(time_s):
        raise FormalDesignError("Pre-treatment records contain a non-finite time_s")
    prefix = records.loc[time_s < float(treatment_start_s)].copy()
    if prefix.empty:
        raise FormalDesignError("No rows exist before treatment_start_s")

    indexed: dict[str, pd.DataFrame] = {}
    for cell_id in EXPECTED_CELL_IDS:
        cell = prefix.loc[prefix["cell_id"].astype(str) == cell_id].copy()
        if cell.duplicated(list(key_columns)).any():
            raise FormalDesignError(f"Cell {cell_id} has duplicate pre-treatment keys")
        indexed[cell_id] = cell.set_index(list(key_columns)).sort_index()

    baseline = indexed[EXPECTED_CELL_IDS[0]]
    if baseline.empty:
        raise FormalDesignError("Baseline cell has no pre-treatment rows")
    maxima = {column: 0.0 for column in numeric_tolerances}
    for cell_id in EXPECTED_CELL_IDS[1:]:
        candidate = indexed[cell_id]
        if not candidate.index.equals(baseline.index):
            raise FormalDesignError(
                f"Cell {cell_id} has misaligned pre-treatment keys"
            )
        for column in exact_columns:
            if not candidate[column].equals(baseline[column]):
                raise FormalDesignError(
                    f"Pre-treatment exact field differs in {cell_id}: {column}"
                )
        for column, tolerance in numeric_tolerances.items():
            baseline_values = pd.to_numeric(baseline[column], errors="coerce")
            candidate_values = pd.to_numeric(candidate[column], errors="coerce")
            if (
                baseline_values.isna().any()
                or candidate_values.isna().any()
                or not _all_finite(baseline_values)
                or not _all_finite(candidate_values)
            ):
                raise FormalDesignError(
                    f"Pre-treatment numeric field is not finite: {column}"
                )
            maximum = float((candidate_values - baseline_values).abs().max())
            maxima[column] = max(maxima[column], maximum)
            if maximum > float(tolerance):
                raise FormalDesignError(
                    f"Pre-treatment difference exceeds tolerance in {cell_id}: "
                    f"{column}={maximum} > {tolerance}"
                )
    return {
        "reference_cell_id": EXPECTED_CELL_IDS[0],
        "treatment_start_s": float(treatment_start_s),
        "pre_treatment_rows_per_cell": int(len(baseline)),
        "numeric_tolerances": dict(numeric_tolerances),
        "maximum_absolute_differences": maxima,
        "equivalence_pass": True,
    }


def validate_run_state_isolation(audit: pd.DataFrame) -> dict[str, Any]:
    """Require every formal run to start from fresh state, cache, and RNG objects."""

    identity_columns = (
        "run_id",
        "state_instance_id",
        "cache_namespace",
        "rng_stream_id",
    )
    count_columns = ("initial_cache_entries", "initial_pending_messages")
    required = {*identity_columns, *count_columns}
    missing = sorted(required - set(audit.columns))
    if missing:
        raise FormalDesignError(
            f"State isolation audit is missing fields: {', '.join(missing)}"
        )
    if audit.empty:
        raise FormalDesignError("State isolation audit cannot be empty")
    for column in identity_columns:
        values = audit[column]
        if values.isna().any() or (values.astype(str).str.strip() == "").any():
            raise FormalDesignError(f"State isolation field is empty: {column}")
        if values.astype(str).duplicated().any():
            raise FormalDesignError(
                f"State isolation field must be unique across runs: {column}"
            )
    for column in count_columns:
        values = pd.to_numeric(audit[column], errors="coerce")
        if values.isna().any() or (values != 0).any():
            raise FormalDesignError(f"Every run must start with {column}=0")
    return {
        "run_count": int(len(audit)),
        "unique_state_instances": int(audit["state_instance_id"].nunique()),
        "unique_cache_namespaces": int(audit["cache_namespace"].nunique()),
        "unique_rng_streams": int(audit["rng_stream_id"].nunique()),
        "isolation_pass": True,
    }


def validate_simulation_time_alignment(
    audit: pd.DataFrame,
    *,
    time_step_s: float,
    time_origin_s: float,
    alignment_tolerance_s: float = 1e-9,
) -> dict[str, Any]:
    """Require every output stream to use the same explicit simulation clock."""

    for name, value in (
        ("time_step_s", time_step_s),
        ("time_origin_s", time_origin_s),
        ("alignment_tolerance_s", alignment_tolerance_s),
    ):
        if not math.isfinite(float(value)):
            raise FormalDesignError(f"{name} must be finite")
    if float(time_step_s) <= 0:
        raise FormalDesignError("time_step_s must be positive")
    if float(alignment_tolerance_s) < 0:
        raise FormalDesignError("alignment_tolerance_s must be non-negative")
    required = {
        "run_id",
        "stream_name",
        "sequence_index",
        "simulation_step",
        "time_s",
    }
    missing = sorted(required - set(audit.columns))
    if missing:
        raise FormalDesignError(
            f"Time alignment audit is missing fields: {', '.join(missing)}"
        )
    if audit.empty:
        raise FormalDesignError("Time alignment audit cannot be empty")
    for column in ("run_id", "stream_name"):
        if audit[column].isna().any() or (
            audit[column].astype(str).str.strip() == ""
        ).any():
            raise FormalDesignError(f"Time alignment field is empty: {column}")
    numeric = {
        column: pd.to_numeric(audit[column], errors="coerce")
        for column in ("sequence_index", "simulation_step", "time_s")
    }
    if any(values.isna().any() for values in numeric.values()):
        raise FormalDesignError("Time alignment audit contains non-numeric values")
    if any(not _all_finite(values) for values in numeric.values()):
        raise FormalDesignError("Time alignment audit contains non-finite values")
    for column in ("sequence_index", "simulation_step"):
        if (numeric[column] % 1 != 0).any():
            raise FormalDesignError(f"{column} must be integer-valued")
    if audit.duplicated(["run_id", "stream_name", "sequence_index"]).any():
        raise FormalDesignError("A stream contains duplicate sequence_index values")

    expected = float(time_origin_s) + numeric["simulation_step"] * float(time_step_s)
    mismatch = (numeric["time_s"] - expected).abs() > float(alignment_tolerance_s)
    if mismatch.any():
        row = audit.loc[mismatch].iloc[0]
        raise FormalDesignError(
            "simulation_step and time_s are inconsistent for "
            f"{row['run_id']}/{row['stream_name']}"
        )
    normalized = audit.assign(
        _sequence=numeric["sequence_index"],
        _step=numeric["simulation_step"],
        _time=numeric["time_s"],
    )
    for (run_id, stream_name), stream in normalized.groupby(
        ["run_id", "stream_name"], sort=False
    ):
        ordered = stream.sort_values("_sequence")
        if not ordered["_step"].is_monotonic_increasing:
            raise FormalDesignError(
                f"simulation_step decreases in {run_id}/{stream_name}"
            )
        if not ordered["_time"].is_monotonic_increasing:
            raise FormalDesignError(f"time_s decreases in {run_id}/{stream_name}")
    return {
        "run_count": int(audit["run_id"].nunique()),
        "stream_count": int(
            audit[["run_id", "stream_name"]].drop_duplicates().shape[0]
        ),
        "record_count": int(len(audit)),
        "time_step_s": float(time_step_s),
        "time_origin_s": float(time_origin_s),
        "alignment_tolerance_s": float(alignment_tolerance_s),
        "time_alignment_pass": True,
    }


def validate_vehicle_id_lifecycle(records: pd.DataFrame) -> dict[str, Any]:
    """Prohibit stale references and vehicle-ID reuse inside a formal run."""

    required = {
        "run_id",
        "vehicle_id",
        "incarnation_id",
        "event_type",
        "time_s",
        "event_sequence",
    }
    missing = sorted(required - set(records.columns))
    if missing:
        raise FormalDesignError(
            f"Vehicle lifecycle records are missing fields: {', '.join(missing)}"
        )
    if records.empty:
        raise FormalDesignError("Vehicle lifecycle records cannot be empty")
    for column in ("run_id", "vehicle_id", "incarnation_id", "event_type"):
        if records[column].isna().any() or (
            records[column].astype(str).str.strip() == ""
        ).any():
            raise FormalDesignError(f"Vehicle lifecycle field is empty: {column}")
    allowed_events = {"enter", "active", "reference", "exit"}
    unknown = sorted(set(records["event_type"].astype(str)) - allowed_events)
    if unknown:
        raise FormalDesignError(
            f"Unknown vehicle lifecycle event types: {', '.join(unknown)}"
        )
    time_s = pd.to_numeric(records["time_s"], errors="coerce")
    sequence = pd.to_numeric(records["event_sequence"], errors="coerce")
    if time_s.isna().any() or sequence.isna().any():
        raise FormalDesignError("Vehicle lifecycle time and sequence must be numeric")
    if not _all_finite(time_s) or not _all_finite(sequence):
        raise FormalDesignError("Vehicle lifecycle time and sequence must be finite")
    if (sequence % 1 != 0).any():
        raise FormalDesignError("event_sequence must be integer-valued")
    normalized = records.assign(_time=time_s, _sequence=sequence)
    vehicle_count = 0
    for (run_id, vehicle_id), vehicle in normalized.groupby(
        ["run_id", "vehicle_id"], sort=False
    ):
        vehicle_count += 1
        if vehicle["incarnation_id"].astype(str).nunique() != 1:
            raise FormalDesignError(
                f"reused vehicle_id after departure in {run_id}: {vehicle_id}"
            )
        ordered = vehicle.sort_values("_sequence")
        if ordered["_sequence"].duplicated().any():
            raise FormalDesignError(
                f"Duplicate vehicle lifecycle sequence in {run_id}: {vehicle_id}"
            )
        if not ordered["_time"].is_monotonic_increasing:
            raise FormalDesignError(
                f"Vehicle lifecycle time decreases in {run_id}: {vehicle_id}"
            )
        events = ordered["event_type"].astype(str).tolist()
        if events[0] != "enter" or events.count("enter") != 1:
            raise FormalDesignError(
                f"Vehicle lifecycle requires exactly one initial enter: {vehicle_id}"
            )
        if events.count("exit") > 1:
            raise FormalDesignError(
                f"Vehicle lifecycle has multiple exits: {vehicle_id}"
            )
        if "exit" in events and events.index("exit") != len(events) - 1:
            raise FormalDesignError(
                f"Vehicle lifecycle contains an event after exit: {vehicle_id}"
            )
    return {
        "run_count": int(records["run_id"].nunique()),
        "vehicle_count": int(vehicle_count),
        "event_count": int(len(records)),
        "vehicle_lifecycle_pass": True,
    }
