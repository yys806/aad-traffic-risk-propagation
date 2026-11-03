"""P4 measurement v1: explicit identity, provenance and finite JSON records.

No simulator launch, statistical estimation, parameter selection or P3 mutation.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

SCHEMA_VERSION = "aad.p4.measurement.v1"
DERIVATION_VERSION = "aad.p4.measurement-implementation.v1"
CONTEXT = ("support_id", "run_id", "assignment_id", "event_id")
ENTITIES = ("support_manifest", "provenance", "cohort_member", "state_observation",
            "action_execution_bridge", "action_comparison", "action_timing", "risk_sample",
            "risk_action_bridge", "vehicle_window", "regional_outcome")


class P4InputError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise P4InputError(code, detail)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def sha256_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def stamp(entity, data):
    require(entity in ENTITIES, "INVALID_ENTITY", entity)
    result = deepcopy(data)
    if entity == "provenance":
        result.setdefault("source_derivation_version", result.get("derivation_version"))
    result.update(schema_version=SCHEMA_VERSION, entity=entity, derivation_version=DERIVATION_VERSION)
    result.pop("record_sha256", None)
    try:
        result["record_sha256"] = sha256_json(result)
    except (TypeError, ValueError) as exc:
        raise P4InputError("INVALID_JSON_VALUE", entity) from exc
    return result


def check_record(record, entity):
    require(record.get("schema_version") == SCHEMA_VERSION and record.get("entity") == entity,
            "SCHEMA_MISMATCH", entity)
    body = {k: v for k, v in record.items() if k != "record_sha256"}
    require(record.get("record_sha256") == sha256_json(body), "RECORD_HASH_MISMATCH", entity)


def same_context(row, support):
    require(all(row.get(k) == support.get(k) for k in CONTEXT), "CROSS_SCOPE_REFERENCE", str(row.get("state_id")))


def provenance_index(records, artifact_root=None):
    result = {}
    for row in records:
        key = row.get("provenance_id")
        require(text(key) and key not in result, "DUPLICATE_OR_MISSING_PROVENANCE", str(key))
        h = row.get("source_sha256")
        require(text(row.get("source_ref")) and isinstance(h, str) and len(h) == 64
                and all(c in "0123456789abcdef" for c in h), "INVALID_PROVENANCE", key)
        require(text(row.get("derivation_version")), "INVALID_PROVENANCE", key)
        if artifact_root is not None:
            root = Path(artifact_root).resolve()
            path = (root / row["source_ref"]).resolve()
            require(path.is_relative_to(root) and path.is_file(), "SOURCE_OUTSIDE_ARTIFACT_ROOT", key)
            require(hashlib.sha256(path.read_bytes()).hexdigest() == h, "SOURCE_HASH_MISMATCH", key)
        result[key] = row
    return result


def evidence_present(key, provenance):
    return text(key) and key in provenance


def validate_support(support, provenance):
    require(all(text(support.get(k)) for k in CONTEXT if k != "event_id"), "INVALID_SUPPORT", "context")
    require(support.get("event_id") is None or text(support["event_id"]), "INVALID_SUPPORT", "event_id")
    require(text(support.get("reference_clock_id")), "INVALID_SUPPORT", "reference_clock_id")
    require(evidence_present(support.get("provenance_id"), provenance), "INVALID_SUPPORT", "provenance")
    cadence = support.get("cadence", {})
    require(finite(cadence.get("step_s")) and cadence["step_s"] > 0
            and type(cadence.get("frame_delta")) is int and cadence["frame_delta"] >= 1
            and evidence_present(cadence.get("provenance_id"), provenance), "CADENCE_UNPROVEN", "explicit source cadence required")
    start, end = support.get("window_start_s"), support.get("window_end_s")
    require((start is None and end is None) or (finite(start) and finite(end) and end > start),
            "INVALID_WINDOW", "fixed positive window or explicit null scope")


def scope_defined(support, provenance):
    return (all(text(support.get(k)) for k in ("region_id", "region_version", "window_version", "coordinate_system"))
        and finite(support.get("window_start_s")) and finite(support.get("window_end_s"))
        and evidence_present(support.get("scope_provenance_id"), provenance)
        and finite(support.get("scope_frozen_time_upper_s"))
        and finite(support.get("assignment_time_lower_s"))
        and support["scope_frozen_time_upper_s"] < support["assignment_time_lower_s"])


def validate_states(states, support=None):
    ids, keys = set(), set()
    for row in states:
        key = row.get("state_id")
        require(text(key) and key not in ids, "DUPLICATE_STATE_ID", str(key))
        ids.add(key)
        require(all(text(row.get(k)) for k in ("run_id", "assignment_id", "vehicle_id", "incarnation_id", "clock_id", "phase")),
                "INVALID_STATE_IDENTITY", key)
        require(finite(row.get("time_s")) and finite(row.get("time_error_s")) and row["time_error_s"] >= 0,
                "INVALID_STATE_TIME", key)
        pk = tuple(row.get(k) for k in ("run_id", "vehicle_id", "incarnation_id", "clock_id", "time_s", "phase"))
        require(pk not in keys, "DUPLICATE_STATE_TIME", str(pk))
        keys.add(pk)
        require(row.get("lifecycle_status") in ("PRESENT", "EXITED", "UNOBSERVABLE"), "INVALID_LIFECYCLE", key)
        require(row.get("observation_basis") in ("ACTUAL_READBACK", "SOURCE_OBSERVATION", "SYNTHETIC_VALIDATION_ONLY"),
                "ESTIMATED_STATE_NOT_ACTUAL", key)
        for name in ("speed_mps", "acceleration_mps2", "lane_position_m", "leader_speed_mps", "net_gap_m"):
            require(row.get(name) is None or finite(row[name]), "NONFINITE_STATE", key + ":" + name)
        if support is not None:
            same_context(row, support)


def validate_bounds(lower, upper):
    require(finite(lower) and finite(upper) and 0 <= lower <= upper <= 1, "INVALID_BOUNDS", str((lower, upper)))
