"""Fail-closed writer for the post-Stage 0.6 protocol lock."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ProtocolLockError(ValueError):
    """Raised when a protocol lock would be premature or incomplete."""


REQUIRED_GATES = ("stage_0_2", "stage_0_4", "stage_0_5", "stage_0_6")
REQUIRED_FROZEN_FIELDS = {
    "data_manifest_sha256",
    "split_manifest_sha256",
    "target_region_rule",
    "target_vehicle_eligibility_rule",
    "primary_risk_type",
    "primary_endpoint",
    "secondary_endpoint",
    "ttc_threshold_s",
    "event_merge_rule",
    "valid_observation_mask",
    "time_step_s",
    "risk_window_s",
    "observation_window_s",
    "epsilon_input",
    "epsilon_state",
    "physical_path_rule",
    "right_censoring_rule",
    "delta_eq",
    "delta_R",
    "calibration_seeds",
    "delta_plan",
    "paired_variance",
    "stage_1_1_sample_size",
    "communication_observability",
    "simulation_applicability",
    "extrapolation_exclusions",
    "missing_failure_inclusion_rules",
    "runner_version",
    "analyzer_version",
    "environment_version",
    "code_commit",
}


def protocol_lock_readiness(gate_reports: dict) -> dict:
    """Return a machine-readable fail-closed status without writing a lock."""

    blockers = []
    for name in REQUIRED_GATES:
        status = gate_reports.get(name, {}).get("gate_status", "missing")
        allowed = {"pass", "pass_limited"} if name == "stage_0_4" else {"pass"}
        if status not in allowed:
            blockers.append(f"{name}={status}")
    return {
        "schema_version": "aad.protocol-lock-readiness.v1",
        "protocol_version": "v1.1",
        "protocol_lock_allowed": not blockers,
        "stage_1_1_allowed": False,
        "blockers": blockers,
        "note": (
            "Stage 1.1 remains forbidden until a complete protocol lock is written and verified."
        ),
    }


def write_protocol_lock(
    *, output_path: str | Path, gate_reports: dict, frozen_values: dict
) -> Path:
    """Write JSON-compatible YAML only after every prerequisite passes."""

    missing_gates = [name for name in REQUIRED_GATES if name not in gate_reports]
    if missing_gates:
        raise ProtocolLockError("missing gate reports: " + ", ".join(missing_gates))
    failed = []
    for name in REQUIRED_GATES:
        status = gate_reports[name].get("gate_status")
        allowed = {"pass", "pass_limited"} if name == "stage_0_4" else {"pass"}
        if status not in allowed:
            failed.append(f"{name}={status}")
    if failed:
        raise ProtocolLockError("required gates are not passed: " + ", ".join(failed))
    missing_fields = sorted(REQUIRED_FROZEN_FIELDS - set(frozen_values))
    if missing_fields:
        raise ProtocolLockError("missing frozen fields: " + ", ".join(missing_fields))
    if not (0 <= float(frozen_values["delta_eq"]) < float(frozen_values["delta_R"])):
        raise ProtocolLockError("protocol requires 0 <= delta_eq < delta_R")
    if float(frozen_values["delta_plan"]) <= float(frozen_values["delta_R"]):
        raise ProtocolLockError("delta_plan must be strictly larger than delta_R")
    output_path = Path(output_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    payload = {
        "schema_version": "aad.protocol-lock.v1.1",
        "status": "locked",
        "gate_reports": gate_reports,
        "frozen_values": frozen_values,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_path
