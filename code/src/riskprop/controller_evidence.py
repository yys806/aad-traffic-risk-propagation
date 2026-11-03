"""Independent P3 event evidence; no SUMO, causal inference, or Formal migration.

Producer attestations are audited, not authenticated. The policy-input adoption
boundary is versioned: P7 ratification does not rewrite Proposed history.
Historical adopted flags never create receipts.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, fields
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "aad.p3.controller-evidence.v1"
LEGACY_ADOPTION_BOUNDARY_VERSION = "aad.p3.policy-input-adoption.proposed.v0.1"
LEGACY_ADOPTION_BOUNDARY_STATUS = "PROPOSED"
ADOPTION_BOUNDARY_VERSION = "aad.p3.policy-input-adoption.agreed.v1"
ADOPTION_BOUNDARY_STATUS = "AGREED"
SUPPORTED_ADOPTION_BOUNDARIES = {
    LEGACY_ADOPTION_BOUNDARY_VERSION: LEGACY_ADOPTION_BOUNDARY_STATUS,
    ADOPTION_BOUNDARY_VERSION: ADOPTION_BOUNDARY_STATUS,
}


def _supported_boundary(version: Any, status: Any) -> bool:
    return isinstance(version, str) and isinstance(status, str) and SUPPORTED_ADOPTION_BOUNDARIES.get(version) == status


class EvidenceError(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, TimeEvidence):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return deepcopy(value)


@dataclass(frozen=True, kw_only=True)
class TimeEvidence:
    """Mapped bounds/observed_at/available_at use reference-clock seconds.

    Native time uses time_unit. sequence attests call order in one clock/step;
    phase names have no implicit order. Missing bounds never imply zero error.
    """
    native_timestamp: float | None = None
    clock_id: str | None = None
    time_unit: str = "s"
    simulation_step: int | None = None
    phase: str | None = None
    sequence: int | None = None
    time_lower: float | None = None
    time_upper: float | None = None
    reference_clock_id: str | None = None
    clock_mapping_version: str | None = None
    observed_at: float | None = None
    available_at: float | None = None
    reason: str | None = None


@dataclass(frozen=True, kw_only=True)
class EventContext:
    record_id: str
    run_id: str
    pair_id: str
    cell_id: str
    producer_id: str
    producer_role: str
    evidence_ref: str
    fixture_only: bool
    vehicle_id: str
    vehicle_incarnation_id: str
    block_id: str | None = None
    source_event_id: str | None = None
    message_id: str | None = None
    assignment_id: str | None = None
    adoption_mode: str = "UNKNOWN"
    adoption_mode_source: str = "UNKNOWN"
    adoption_mode_version: str = "UNKNOWN"


# Required body fields can be explicitly null where the observation is unknown.
# Primary times live in record.time; schema_description declares their aliases.
SPECS: dict[str, dict[str, Any]] = {
    "source": dict(id="source_event_id", role="source_observer", required="source_type qualification_status confirmation_ref", optional="", statuses=None),
    "message": dict(id="message_id", role="message_generator", required="sender_id payload_hash payload_type payload_ref message_kind valid_from valid_until validity_rule_ref", optional="", statuses=None),
    "send": dict(id="attempt_id", role="sender", required="attempt_id send_status transport_ref", optional="", status="send_status", statuses="SENT FAILED QUEUED NOT_ATTEMPTED UNKNOWN"),
    "delivery": dict(id="delivery_id", role="receiver", required="delivery_id attempt_id delivery_status", optional="", status="delivery_status", statuses="RECEIVED CONFIRMED_FAILURE NOT_OBSERVED UNKNOWN RIGHT_CENSORED"),
    "validation": dict(id="validation_id", role="validator", required="validation_id delivery_id validator_id validator_version validation_status reason", optional="", status="validation_status", statuses="VALID INVALID EXPIRED UNKNOWN"),
    "controller": dict(id="controller_instance_id", role="controller_registry", required="controller_id controller_instance_id controller_version controller_code_hash policy_version policy_config_hash controlled_vehicle_id", optional="", statuses=None),
    "input": dict(id="receipt_id", role="controller_input", required="receipt_id message_id payload_hash validation_id controller_instance_id available_time input_schema_version input_snapshot_ref input_status", optional="", status="input_status", statuses="RECEIVED QUEUED AVAILABLE NOT_RECEIVED UNKNOWN RIGHT_CENSORED"),
    "consumption": dict(id="consumption_receipt_id", role="policy", required="consumption_receipt_id input_receipt_id message_id payload_hash controller_instance_id decision_id policy_version input_snapshot_hash consumption_status reason adoption_boundary_version adoption_boundary_status", optional="", status="consumption_status", statuses="RECEIVED CONSIDERED REJECTED POLICY_INPUT_INCLUDED UNKNOWN"),
    "decision": dict(id="decision_id", role="policy", required="decision_id controller_instance_id policy_version input_snapshot_hash consumed_message_refs decision_status decision_output_ref control_intent no_change_reason command_disposition", optional="", status="decision_status", statuses="DECIDED UNCHANGED FAILED UNKNOWN"),
    "command": dict(id="command_id", role="command_interface", required="command_id decision_id controller_instance_id target_vehicle_id command_type command_value command_unit valid_from valid_until command_status execution_interface_ref ack_time failure_reason execution_disposition", optional="superseded_by", status="command_status", statuses="CREATED ISSUED ACKNOWLEDGED REJECTED CANCELLED SUPERSEDED UNKNOWN"),
    "safety": dict(id="intervention_id", role="safety_layer", required="intervention_id command_id safety_layer_id safety_layer_version constraint_version original_command modified_command intervention_status intervention_reason", optional="previous_intervention_id", status="intervention_status", statuses="NOT_OBSERVED CONFIRMED_NONE MODIFIED REJECTED UNKNOWN"),
    "execution": dict(id="execution_id", role="execution_reader", required="execution_id command_id target_vehicle_id execution_end execution_status actual_acceleration actual_speed actual_position state_readback_ref execution_reason safety_intervention_refs", optional="", status="execution_status", statuses="EXECUTED PARTIAL NOT_EXECUTED MODIFIED_EXECUTED UNKNOWN VEHICLE_EXITED UNOBSERVABLE RIGHT_CENSORED"),
    "action_observation": dict(id="action_observation_id", role="action_observer", required="action_observation_id execution_refs comparison_ref action_change_status observation_ref", optional="", status="action_change_status", statuses="OBSERVED_CHANGE NO_CHANGE UNKNOWN NOT_APPLICABLE"),
    "risk_observation": dict(id="risk_observation_id", role="risk_observer", required="risk_observation_id action_observation_refs measurement_version observation_ref risk_status", optional="", status="risk_status", statuses="OBSERVED UNKNOWN RIGHT_CENSORED NOT_APPLICABLE"),
}
PRIMARY_TIME = {"source": "confirmation_time", "message": "generated_time", "send": "sent_time",
                "delivery": "delivered_time", "validation": "validation_time", "controller": "registered_time",
                "input": "received_time", "consumption": "consumption_time", "decision": "decision_time",
                "command": "issue_time", "safety": "intervention_time", "execution": "execution_start",
                "action_observation": "observation_time", "risk_observation": "observation_time"}
TIME_FIELDS = {"valid_from", "valid_until", "available_time", "ack_time", "execution_end"}


def schema_description() -> dict[str, Any]:
    """Machine-readable inventory, not an upgrade of Formal artifact schemas."""
    return {"schema_version": SCHEMA_VERSION, "adoption_boundary_version": ADOPTION_BOUNDARY_VERSION,
            "adoption_boundary_status": ADOPTION_BOUNDARY_STATUS,
            "context_fields": [f.name for f in fields(EventContext)], "time_fields": [f.name for f in fields(TimeEvidence)],
            "time_units": "native time uses time_unit; mapped bounds/observation/availability use reference seconds",
            "kinds": {k: {**v, "required": v["required"].split(), "optional": v["optional"].split(),
                           "primary_time": PRIMARY_TIME[k], "statuses": v["statuses"].split() if v["statuses"] else None}
                      for k, v in SPECS.items()}, "scientific_claim_eligible": False}


def _fail(code: str, detail: str) -> None:
    raise EvidenceError(code, detail)


def _text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _fail("INVALID_FIELD", label + " must be a nonempty string")


def _number(value: Any, label: str) -> None:
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
        _fail("INVALID_FIELD", label + " must be finite numeric or null (never string/bool)")


def _validate_time(t: Mapping[str, Any], label: str) -> None:
    if not isinstance(t, Mapping) or set(t) != {f.name for f in fields(TimeEvidence)}:
        _fail("INVALID_FIELD", label + " has unsupported/missing time fields")
    for key in ("native_timestamp", "time_lower", "time_upper", "observed_at", "available_at"):
        _number(t[key], label + "." + key)
    if t["time_unit"] not in ("s", "ms", "us", "ns"):
        _fail("INVALID_FIELD", label + ".time_unit")
    for key in ("simulation_step", "sequence"):
        if t[key] is not None and (type(t[key]) is not int or t[key] < 0):
            _fail("INVALID_FIELD", label + "." + key)
    for key in ("clock_id", "phase", "reference_clock_id", "clock_mapping_version", "reason"):
        if t[key] is not None:
            _text(t[key], label + "." + key)
    if t["time_lower"] is not None and t["time_upper"] is not None and t["time_lower"] > t["time_upper"]:
        _fail("INVALID_TIME_INTERVAL", label)


def compare_times(left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    """BEFORE is strict interval separation; CALL_ORDER is not physical time proof."""
    _validate_time(left, "left")
    _validate_time(right, "right")
    mapped = all(t["reference_clock_id"] and t["clock_mapping_version"] and
                 t["time_lower"] is not None and t["time_upper"] is not None for t in (left, right))
    if mapped and left["reference_clock_id"] == right["reference_clock_id"]:
        if left["time_upper"] < right["time_lower"]:
            return "BEFORE"
        if left["time_lower"] > right["time_upper"]:
            return "AFTER"
    same_step = (left["clock_id"] is not None and left["clock_id"] == right["clock_id"] and
                 left["simulation_step"] is not None and left["simulation_step"] == right["simulation_step"] and
                 left["native_timestamp"] is not None and left["native_timestamp"] == right["native_timestamp"] and
                 left["time_unit"] == right["time_unit"] and left["phase"] is not None and right["phase"] is not None)
    if same_step and left["sequence"] is not None and right["sequence"] is not None:
        if left["sequence"] < right["sequence"]:
            return "CALL_ORDER"
        if left["sequence"] > right["sequence"]:
            return "REVERSED_CALL_ORDER"
    return "OVERLAP" if mapped and left["reference_clock_id"] == right["reference_clock_id"] else "UNKNOWN"


def _validate_record(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping) or set(record) != {"schema_version", "kind", "context", "time", "data"} or record["schema_version"] != SCHEMA_VERSION:
        _fail("SCHEMA_MISMATCH", "unsupported record envelope")
    kind = record["kind"]
    _text(kind, "kind")
    if kind not in SPECS:
        _fail("SCHEMA_MISMATCH", str(kind))
    c, d, spec = record["context"], record["data"], SPECS[kind]
    if not isinstance(c, Mapping) or not isinstance(d, Mapping) or set(c) != {f.name for f in fields(EventContext)}:
        _fail("INVALID_FIELD", "context/data field set")
    for key in ("record_id", "run_id", "pair_id", "cell_id", "producer_id", "producer_role", "evidence_ref", "vehicle_id", "vehicle_incarnation_id", "adoption_mode", "adoption_mode_source", "adoption_mode_version"):
        _text(c[key], key)
    for key in ("block_id", "source_event_id", "message_id", "assignment_id"):
        if c[key] is not None:
            _text(c[key], key)
    if type(c["fixture_only"]) is not bool:
        _fail("INVALID_FIELD", "fixture_only must be an explicit boolean")
    if c["producer_role"] != spec["role"]:
        _fail("INVALID_PRODUCER", kind + " must originate at " + spec["role"])
    required, optional = set(spec["required"].split()), set(spec["optional"].split())
    if not required <= set(d) or set(d) - required - optional:
        _fail("INVALID_FIELD", f"{kind} missing={required-set(d)} extra={set(d)-required-optional}")
    if spec["statuses"] and d[spec["status"]] not in spec["statuses"].split():
        _fail("INVALID_STATE_TRANSITION", f"{kind} status")
    # Validate containers before cross-record lookups: capture order is arbitrary.
    for key in ("consumed_message_refs", "safety_intervention_refs", "execution_refs", "action_observation_refs"):
        if key in d:
            refs = d[key]
            if not isinstance(refs, list):
                _fail("INVALID_FIELD", key + " must be a list")
            if key == "consumed_message_refs":
                for ref in refs:
                    if not isinstance(ref, dict) or set(ref) != {"message_id", "consumption_receipt_id"}:
                        _fail("INVALID_FIELD", "decision message reference shape")
                    for value in ref.values():
                        _text(value, "decision message reference")
            elif any(not isinstance(ref, str) or not ref.strip() for ref in refs):
                _fail("INVALID_FIELD", key + " must contain nonempty IDs")
    identity = c.get(spec["id"], d.get(spec["id"]))
    _text(identity, kind + "." + spec["id"])
    _validate_time(record["time"], kind + ".time")
    for key in TIME_FIELDS & set(d):
        if d[key] is not None:
            _validate_time(d[key], kind + "." + key)
    for key in ("payload_hash", "controller_code_hash", "policy_config_hash", "input_snapshot_hash"):
        if key in d and d[key] is not None:
            val = d[key]
            if not isinstance(val, str) or len(val) != 64 or any(x not in "0123456789abcdef" for x in val):
                _fail("INVALID_FIELD", key + " must be lower-case SHA256")
    for key in ("actual_acceleration", "actual_speed", "actual_position"):
        if key in d:
            _number(d[key], key)
    try:
        canonical_hash(record)
    except (TypeError, ValueError) as exc:
        _fail("INVALID_FIELD", "record must be strict finite JSON: " + str(exc))


class EvidenceJournal:
    """P7 appends at actual producer boundaries; validate resolves explicit IDs.

    Forward decision references are allowed while recording. Exact replay is
    opt-in. Returned records are deep copies, not writable journal internals.
    """
    def __init__(self, *, adoption_boundary_version: str | None = None,
                 adoption_boundary_status: str | None = None) -> None:
        self._boundary_explicit = adoption_boundary_version is not None or adoption_boundary_status is not None
        if not self._boundary_explicit:
            adoption_boundary_version, adoption_boundary_status = ADOPTION_BOUNDARY_VERSION, ADOPTION_BOUNDARY_STATUS
        if not _supported_boundary(adoption_boundary_version, adoption_boundary_status):
            _fail("SCHEMA_MISMATCH", "unsupported adoption boundary version/status pair")
        self.adoption_boundary_version = adoption_boundary_version
        self.adoption_boundary_status = adoption_boundary_status
        self._records: dict[str, dict[str, Any]] = {}
        self._has_consumption = False

    def append(self, kind: str, context: EventContext, time: TimeEvidence,
               *, idempotent: bool = False, **data: Any) -> str:
        record = {"schema_version": SCHEMA_VERSION, "kind": kind, "context": asdict(context),
                  "time": asdict(time), "data": _plain(data)}
        return self.append_record(record, idempotent=idempotent)

    def append_record(self, record: Mapping[str, Any], *, idempotent: bool = False) -> str:
        record = deepcopy(dict(record))
        _validate_record(record)
        if record["kind"] == "consumption" and not self._boundary_explicit and not self._has_consumption:
            version, status = record["data"]["adoption_boundary_version"], record["data"]["adoption_boundary_status"]
            if not _supported_boundary(version, status):
                _fail("SCHEMA_MISMATCH", "unsupported adoption boundary version/status pair")
            self.adoption_boundary_version, self.adoption_boundary_status = version, status
        if record["kind"] == "consumption" and (
            record["data"]["adoption_boundary_version"], record["data"]["adoption_boundary_status"]
        ) != (self.adoption_boundary_version, self.adoption_boundary_status):
            _fail("SCHEMA_MISMATCH", "receipt boundary differs from journal; no silent promotion")
        rid = record["context"]["record_id"]
        if rid in self._records:
            if idempotent and self._records[rid] == record:
                return rid
            _fail("DUPLICATE_ID", rid)
        self._records[rid] = record
        self._has_consumption |= record["kind"] == "consumption"
        return rid

    @property
    def records(self) -> list[dict[str, Any]]:
        return deepcopy(list(self._records.values()))

    def validate(self) -> dict[str, Any]:
        result = validate_records(self.records)
        result.update(adoption_boundary_version=self.adoption_boundary_version,
                      adoption_boundary_status=self.adoption_boundary_status)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "adoption_boundary_version": self.adoption_boundary_version,
                "adoption_boundary_status": self.adoption_boundary_status, "scientific_claim_eligible": False,
                "records": self.records}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> EvidenceJournal:
        if (set(payload) != {"schema_version", "scientific_claim_eligible", "adoption_boundary_version", "adoption_boundary_status", "records"} or
            payload.get("schema_version") != SCHEMA_VERSION or payload.get("scientific_claim_eligible") is not False or
            not _supported_boundary(payload.get("adoption_boundary_version"), payload.get("adoption_boundary_status"))):
            _fail("SCHEMA_MISMATCH", "bundle version/boundary/claim")
        if not isinstance(payload["records"], list):
            _fail("INVALID_FIELD", "records must be a list")
        journal = cls(adoption_boundary_version=payload["adoption_boundary_version"],
                      adoption_boundary_status=payload["adoption_boundary_status"])
        for record in payload["records"]:
            journal.append_record(record)
        return journal

    def write(self, path: Path) -> None:
        self.validate()
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(self.to_dict(), stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")


def legacy_protocol_observation(row: Mapping[str, Any], *, evidence_ref: str) -> dict[str, Any]:
    """Historical field annotation only; never emit a consumption receipt."""
    _text(evidence_ref, "evidence_ref")
    return {"schema_version": "aad.p3.legacy-observation.v1", "evidence_grade": "HISTORICAL_FIELD_ONLY",
            "original": deepcopy(dict(row)), "evidence_ref": evidence_ref,
            "consumption_evidence_status": "UNKNOWN", "candidate_adoption_status": "UNKNOWN",
            "consumption_receipts_created": 0, "scientific_claim_eligible": False}


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit complete or partial capture. Bad FKs raise; absent observations stay unknown.

    Returned edges reference record IDs and retain all input fields in timeline.
    They assert recorded provenance relationships, never causal identification.
    """
    indices: dict[str, dict[str, dict[str, Any]]] = {k: {} for k in SPECS}
    record_ids: set[str] = set()
    issues: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []
    candidates: list[str] = []
    included_receipts: list[str] = []
    if not records:
        issues.append({"code": "EMPTY_CAPTURE", "record_id": "", "status": "UNKNOWN", "detail": "no observed events"})

    def issue(code: str, r: dict, detail: str) -> None:
        issues.append({"code": code, "record_id": r["context"]["record_id"], "status": "UNKNOWN", "detail": detail})

    def edge(a: dict, b: dict, relation: str, *, order: bool = True) -> None:
        temporal = compare_times(a["time"], b["time"]) if order else "NOT_TESTED"
        if temporal in ("AFTER", "REVERSED_CALL_ORDER"):
            _fail("INVALID_TIME_INTERVAL", relation + " has reversed recorded order")
        if order and temporal in ("UNKNOWN", "OVERLAP"):
            issue("UNKNOWN_TEMPORAL_ORDER", b, relation + ": " + temporal)
        item = {"from_record_id": a["context"]["record_id"], "to_record_id": b["context"]["record_id"],
                "relation": relation, "time_relation": temporal}
        if item not in edges:
            edges.append(item)

    def scope(a: dict, b: dict, vehicle: bool = False) -> None:
        ac, bc = a["context"], b["context"]
        if ac["run_id"] != bc["run_id"]:
            _fail("CROSS_RUN_REFERENCE", ac["record_id"] + " -> " + bc["record_id"])
        for key in ("pair_id", "cell_id", "block_id", "assignment_id"):
            if ac[key] != bc[key]:
                _fail("CONTEXT_MISMATCH", key)
        if ac["fixture_only"] != bc["fixture_only"]:
            _fail("EVIDENCE_GRADE_MISMATCH", "cannot merge synthetic and non-synthetic edges")
        if vehicle and (ac["vehicle_id"], ac["vehicle_incarnation_id"]) != (bc["vehicle_id"], bc["vehicle_incarnation_id"]):
            _fail("CROSS_VEHICLE_REFERENCE", ac["record_id"] + " -> " + bc["record_id"])

    def get(kind: str, identity: Any, r: dict, *, vehicle: bool = False, link: bool = True) -> dict:
        if not isinstance(identity, str) or identity not in indices[kind]:
            code = {"decision": "MISSING_DECISION", "command": "MISSING_COMMAND"}.get(kind, "ORPHAN_REFERENCE")
            _fail(code, f"{kind}:{identity} referenced by {r['context']['record_id']}")
        parent = indices[kind][identity]
        scope(parent, r, vehicle)
        if link:
            edge(parent, r, kind + "->" + r["kind"])
        return parent

    def same_controller(a: dict, b: dict) -> None:
        if a["data"]["controller_instance_id"] != b["data"]["controller_instance_id"]:
            _fail("CONTEXT_MISMATCH", "controller_instance_id")

    for r in records:
        _validate_record(r)
        c, d, kind = r["context"], r["data"], r["kind"]
        rid = c["record_id"]
        identity = c.get(SPECS[kind]["id"], d.get(SPECS[kind]["id"]))
        if kind == "message" and identity in indices[kind] and indices[kind][identity]["data"]["payload_hash"] != d["payload_hash"]:
            _fail("CONFLICTING_PAYLOAD_HASH", "same message_id, different payload hash")
        if rid in record_ids or identity in indices[kind]:
            _fail("DUPLICATE_ID", rid + " / " + str(identity))
        record_ids.add(rid)
        indices[kind][identity] = r
        t = r["time"]
        if (t["clock_id"] is None or t["clock_mapping_version"] is None or t["reference_clock_id"] is None or
            t["time_lower"] is None or t["time_upper"] is None):
            issue("UNKNOWN_TIMESTAMP", r, "missing clock/mapping/bounds; not filled with zero")

    for r in records:
        c, d, kind = r["context"], r["data"], r["kind"]
        message = None
        if kind not in ("source", "controller") and c["source_event_id"] is not None:
            get("source", c["source_event_id"], r)
        if kind not in ("source", "controller", "message") and c["message_id"] is not None:
            message = get("message", c["message_id"], r)
            if message["context"]["source_event_id"] != c["source_event_id"]:
                _fail("CONTEXT_MISMATCH", "source_event_id")
            if "payload_hash" in d and d["payload_hash"] != message["data"]["payload_hash"]:
                _fail("CONFLICTING_PAYLOAD_HASH", c["record_id"])
            if "message_id" in d and d["message_id"] != c["message_id"]:
                _fail("CONTEXT_MISMATCH", "message_id in body and context")
        if kind in ("send", "delivery", "validation", "input", "consumption") and message is None:
            _fail("ORPHAN_REFERENCE", "message_id required for " + kind)
        if kind == "source":
            if d["source_type"] not in ("FORMAL_A", "CONTROLLED_B", "SHAM", "UNKNOWN"):
                _fail("INVALID_FIELD", "source_type")
            if d["qualification_status"] == "UNKNOWN":
                issue("UNKNOWN_SOURCE_QUALIFICATION", r, "interface does not qualify a source")
        elif kind == "message":
            if d["message_kind"] not in ("SOURCE", "SHAM"):
                _fail("INVALID_FIELD", "message_kind")
            if d["sender_id"] != c["vehicle_id"]:
                _fail("CROSS_VEHICLE_REFERENCE", "message sender")
            if d["message_kind"] == "SOURCE" and c["source_event_id"] is None:
                _fail("ORPHAN_REFERENCE", "SOURCE message needs explicit source reference")
            if d["payload_hash"] is None:
                issue("UNKNOWN_PAYLOAD_HASH", r, "payload cannot be byte matched")
            if d["valid_from"] is not None and d["valid_until"] is not None:
                if compare_times(d["valid_from"], d["valid_until"]) == "AFTER":
                    _fail("INVALID_TIME_INTERVAL", "message validity interval")
        elif kind == "send":
            scope(message, r, True)
        elif kind == "delivery":
            sent = get("send", d["attempt_id"], r)
            if sent["context"]["message_id"] != c["message_id"]:
                _fail("CONTEXT_MISMATCH", "delivery attempt/message")
            if d["delivery_status"] == "RECEIVED" and sent["data"]["send_status"] != "SENT":
                _fail("INVALID_STATE_TRANSITION", "received without recorded send")
        elif kind == "validation":
            delivery = get("delivery", d["delivery_id"], r, vehicle=True)
            if delivery["context"]["message_id"] != c["message_id"]:
                _fail("CONTEXT_MISMATCH", "validation message")
            if d["validation_status"] in ("VALID", "INVALID", "EXPIRED") and delivery["data"]["delivery_status"] != "RECEIVED":
                _fail("INVALID_STATE_TRANSITION", "validation without reception evidence")
        elif kind in ("controller", "input", "consumption", "decision", "command"):
            controller = r if kind == "controller" else get("controller", d["controller_instance_id"], r, vehicle=True)
            cd = controller["data"]
            for key in ("controller_id", "controller_version", "policy_version"):
                _text(cd[key], key)
            if cd["controlled_vehicle_id"] != c["vehicle_id"]:
                _fail("CROSS_VEHICLE_REFERENCE", "controlled vehicle")
            if "policy_version" in d and d["policy_version"] != cd["policy_version"]:
                _fail("CONTEXT_MISMATCH", "policy_version")
            if kind == "input":
                validation = get("validation", d["validation_id"], r, vehicle=True)
                if validation["context"]["message_id"] != c["message_id"]:
                    _fail("CONTEXT_MISMATCH", "input validation message")
                if d["input_status"] == "AVAILABLE":
                    if validation["data"]["validation_status"] != "VALID":
                        _fail("INVALID_STATE_TRANSITION", "available policy input must be validated")
                    if d["available_time"] is None:
                        issue("UNKNOWN_TIMESTAMP", r, "input available time not observed")
                    elif compare_times(r["time"], d["available_time"]) in ("AFTER", "REVERSED_CALL_ORDER"):
                        _fail("INVALID_TIME_INTERVAL", "available before received")
                receipts = [x for x in records if x["kind"] == "consumption" and x["data"]["input_receipt_id"] == d["receipt_id"]]
                if not receipts:
                    issue("MISSING_CONSUMPTION_OBSERVATION", r, "no policy-input receipt observed; not proof of non-adoption")
            elif kind == "consumption":
                receipt = get("input", d["input_receipt_id"], r, vehicle=True)
                same_controller(receipt, r)
                if receipt["context"]["message_id"] != c["message_id"]:
                    _fail("CONTEXT_MISMATCH", "consumed input message")
                if not _supported_boundary(d["adoption_boundary_version"], d["adoption_boundary_status"]):
                    _fail("SCHEMA_MISMATCH", "unsupported adoption boundary version/status pair")
                included = d["consumption_status"] == "POLICY_INPUT_INCLUDED"
                if included and receipt["data"]["input_status"] != "AVAILABLE":
                    _fail("INVALID_STATE_TRANSITION", "policy input not available")
                if d["consumption_status"] in ("RECEIVED", "CONSIDERED", "REJECTED") and receipt["data"]["input_status"] not in ("RECEIVED", "QUEUED", "AVAILABLE"):
                    _fail("INVALID_STATE_TRANSITION", "reading/rejection without input reception")
                if d["decision_id"] is not None or included:
                    decision = get("decision", d["decision_id"], r, vehicle=True, link=False)
                    same_controller(decision, r)
                    if (d["policy_version"], d["input_snapshot_hash"]) != (decision["data"]["policy_version"], decision["data"]["input_snapshot_hash"]):
                        _fail("CONTEXT_MISMATCH", "decision policy/input snapshot")
                    edge(r, decision, "consumption->decision")
                    ref = {"message_id": c["message_id"], "consumption_receipt_id": d["consumption_receipt_id"]}
                    if included != (ref in decision["data"]["consumed_message_refs"]):
                        _fail("INVALID_STATE_TRANSITION", "decision/consumption inclusion mismatch")
                if included:
                    available = receipt["data"]["available_time"]
                    if available is None:
                        issue("UNKNOWN_TEMPORAL_ORDER", r, "availability vs consumption unknown")
                    else:
                        relation = compare_times(available, r["time"])
                        if relation in ("AFTER", "REVERSED_CALL_ORDER"):
                            _fail("INVALID_TIME_INTERVAL", "consumption before available")
                        if relation in ("UNKNOWN", "OVERLAP"):
                            issue("UNKNOWN_TEMPORAL_ORDER", r, "availability vs consumption " + relation)
                    included_receipts.append(d["consumption_receipt_id"])
                    if (d["payload_hash"] is None or d["input_snapshot_hash"] is None or not receipt["data"]["input_snapshot_ref"] or cd["controller_code_hash"] is None or
                        cd["policy_config_hash"] is None or cd["policy_version"] == "UNKNOWN"):
                        issue("UNKNOWN_POLICY_INPUT_EVIDENCE", r, "identity/version/hash evidence incomplete")
                    else:
                        candidates.append(d["consumption_receipt_id"])
            elif kind == "decision":
                refs = d["consumed_message_refs"]
                if not isinstance(refs, list) or len({canonical_hash(x) for x in refs}) != len(refs):
                    _fail("INVALID_FIELD", "decision message references must be a unique list")
                for ref in refs:
                    if not isinstance(ref, dict) or set(ref) != {"message_id", "consumption_receipt_id"}:
                        _fail("INVALID_FIELD", "decision message reference shape")
                    receipt = get("consumption", ref["consumption_receipt_id"], r, vehicle=True)
                    same_controller(receipt, r)
                    rd = receipt["data"]
                    if rd["decision_id"] != d["decision_id"] or receipt["context"]["message_id"] != ref["message_id"] or rd["consumption_status"] != "POLICY_INPUT_INCLUDED":
                        _fail("INVALID_STATE_TRANSITION", "decision reference does not identify an included receipt")
                if c["message_id"] is not None and c["message_id"] not in {x["message_id"] for x in refs}:
                    _fail("CONTEXT_MISMATCH", "decision context message not in policy input list")
                if d["command_disposition"] not in ("EXPECTED", "NONE", "UNKNOWN", "RIGHT_CENSORED"):
                    _fail("INVALID_FIELD", "command_disposition")
                commands = [x for x in records if x["kind"] == "command" and x["data"]["decision_id"] == d["decision_id"]]
                if d["command_disposition"] == "NONE" and commands:
                    _fail("INVALID_STATE_TRANSITION", "decision declares no command but has one")
                if d["command_disposition"] != "NONE" and not commands:
                    issue("MISSING_COMMAND", r, d["command_disposition"] + "; no inferred command")
            elif kind == "command":
                decision = get("decision", d["decision_id"], r, vehicle=True)
                same_controller(decision, r)
                if d["target_vehicle_id"] != c["vehicle_id"]:
                    _fail("CROSS_VEHICLE_REFERENCE", "command target")
                if decision["data"]["decision_status"] == "FAILED":
                    _fail("INVALID_STATE_TRANSITION", "failed decision issued command")
                if c["message_id"] is not None and c["message_id"] not in {x["message_id"] for x in decision["data"]["consumed_message_refs"]}:
                    _fail("CONTEXT_MISMATCH", "command context message not consumed by decision")
                if d["execution_disposition"] not in ("EXPECTED", "NONE", "UNKNOWN", "RIGHT_CENSORED"):
                    _fail("INVALID_FIELD", "execution_disposition")
                if d["valid_from"] is not None and d["valid_until"] is not None and compare_times(d["valid_from"], d["valid_until"]) == "AFTER":
                    _fail("INVALID_TIME_INTERVAL", "command validity interval")
                if d["ack_time"] is not None and compare_times(r["time"], d["ack_time"]) in ("AFTER", "REVERSED_CALL_ORDER"):
                    _fail("INVALID_TIME_INTERVAL", "ack before issue")
                if d.get("superseded_by") is not None:
                    replacement = get("command", d["superseded_by"], r, vehicle=True, link=False)
                    if replacement is r:
                        _fail("INVALID_STATE_TRANSITION", "self supersession")
                    if d["command_status"] != "SUPERSEDED":
                        _fail("INVALID_STATE_TRANSITION", "supersession without corresponding status")
                    edge(r, replacement, "superseded_by")
                executions = [x for x in records if x["kind"] == "execution" and x["data"]["command_id"] == d["command_id"]]
                if not executions and d["execution_disposition"] != "NONE":
                    issue("MISSING_EXECUTION", r, d["execution_disposition"] + "; unobserved is not not-executed")
                if executions and d["execution_disposition"] == "NONE":
                    _fail("INVALID_STATE_TRANSITION", "execution exists for command declaring none")
        elif kind in ("safety", "execution"):
            command = get("command", d["command_id"], r, vehicle=True)
            decision = get("decision", command["data"]["decision_id"], command, vehicle=True, link=False)
            if c["message_id"] is not None and c["message_id"] not in {x["message_id"] for x in decision["data"]["consumed_message_refs"]}:
                _fail("CONTEXT_MISMATCH", "execution/safety message not consumed by command decision")
            if kind == "safety":
                for key in ("safety_layer_id", "safety_layer_version", "constraint_version"):
                    _text(d[key], key)
                original = command["data"]["command_value"]
                if d.get("previous_intervention_id") is not None:
                    prev = get("safety", d["previous_intervention_id"], r, vehicle=True)
                    if prev is r or prev["data"]["command_id"] != d["command_id"]:
                        _fail("INVALID_STATE_TRANSITION", "safety predecessor")
                    original = prev["data"]["modified_command"]
                if d["original_command"] != original:
                    _fail("INVALID_STATE_TRANSITION", "safety original command mismatch")
                if d["intervention_status"] == "MODIFIED" and d["modified_command"] is None:
                    _fail("INVALID_STATE_TRANSITION", "modified command missing")
                if d["intervention_status"] == "CONFIRMED_NONE" and d["modified_command"] != d["original_command"]:
                    _fail("INVALID_STATE_TRANSITION", "no intervention declared but command modified")
                if d["intervention_status"] in ("UNKNOWN", "NOT_OBSERVED"):
                    issue("UNKNOWN_SAFETY", r, d["intervention_status"])
            else:
                if d["target_vehicle_id"] != c["vehicle_id"]:
                    _fail("CROSS_VEHICLE_REFERENCE", "execution target")
                if d["execution_end"] is not None and compare_times(r["time"], d["execution_end"]) in ("AFTER", "REVERSED_CALL_ORDER"):
                    _fail("INVALID_TIME_INTERVAL", "execution end precedes start")
                if d["execution_end"] is None:
                    issue("UNKNOWN_EXECUTION_END", r, "execution end not observed")
                refs = d["safety_intervention_refs"]
                if not isinstance(refs, list) or any(not isinstance(x, str) for x in refs) or len(set(refs)) != len(refs):
                    _fail("INVALID_FIELD", "safety references")
                safety = [get("safety", x, r, vehicle=True) for x in refs]
                if any(x["data"]["command_id"] != d["command_id"] for x in safety):
                    _fail("CONTEXT_MISMATCH", "execution safety command")
                executed = d["execution_status"] in ("EXECUTED", "PARTIAL", "MODIFIED_EXECUTED")
                if executed and command["data"]["command_status"] not in ("ISSUED", "ACKNOWLEDGED", "SUPERSEDED"):
                    _fail("INVALID_STATE_TRANSITION", "execution without issued command")
                if executed and any(x["data"]["intervention_status"] == "REJECTED" for x in safety):
                    _fail("INVALID_STATE_TRANSITION", "execution contradicts linked safety rejection")
                if executed:
                    begin, end = command["data"]["valid_from"], command["data"]["valid_until"]
                    if begin is not None and compare_times(begin, r["time"]) == "AFTER":
                        _fail("INVALID_TIME_INTERVAL", "execution before command validity")
                    if end is not None and compare_times(end, r["time"]) == "BEFORE":
                        _fail("INVALID_TIME_INTERVAL", "execution starts after command validity")
                if d["execution_status"] == "MODIFIED_EXECUTED" and not any(x["data"]["intervention_status"] == "MODIFIED" for x in safety):
                    _fail("INVALID_STATE_TRANSITION", "modified execution needs explicit safety evidence")
                if not refs:
                    issue("UNKNOWN_SAFETY", r, "no safety observation; not default False")
                if not d["state_readback_ref"] or any(d[k] is None for k in ("actual_acceleration", "actual_speed", "actual_position")):
                    issue("MISSING_STATE_READBACK", r, "actual state remains unknown")
                if d["execution_status"] in ("UNKNOWN", "VEHICLE_EXITED", "UNOBSERVABLE", "RIGHT_CENSORED"):
                    issue("UNKNOWN_EXECUTION", r, d["execution_status"])
        elif kind == "action_observation":
            if not isinstance(d["execution_refs"], list) or any(not isinstance(x, str) for x in d["execution_refs"]):
                _fail("INVALID_FIELD", "execution_refs")
            for ref in d["execution_refs"]:
                get("execution", ref, r, vehicle=True)
            if d["action_change_status"] in ("OBSERVED_CHANGE", "NO_CHANGE") and not d["comparison_ref"]:
                issue("UNKNOWN_ACTION_COMPARISON", r, "comparison evidence missing")
        elif kind == "risk_observation":
            if not isinstance(d["action_observation_refs"], list) or any(not isinstance(x, str) for x in d["action_observation_refs"]):
                _fail("INVALID_FIELD", "action_observation_refs")
            for ref in d["action_observation_refs"]:
                get("action_observation", ref, r)

        if message is not None and (kind == "consumption" and d["consumption_status"] == "POLICY_INPUT_INCLUDED" or kind == "validation" and d["validation_status"] == "VALID"):
            expires, starts = message["data"]["valid_until"], message["data"]["valid_from"]
            if expires is not None:
                relation = compare_times(expires, r["time"])
                if relation == "BEFORE":
                    _fail("INVALID_STATE_TRANSITION", "included/valid after explicit expiry")
                if relation in ("UNKNOWN", "OVERLAP"):
                    issue("UNKNOWN_EXPIRATION", r, relation)
            if starts is not None and compare_times(starts, r["time"]) == "AFTER":
                _fail("INVALID_STATE_TRANSITION", "included/valid before validity starts")

    # Detect graph cycles independently of timestamps (unknown clocks cannot hide cycles).
    adjacency = {rid: [] for rid in record_ids}
    for e in edges:
        adjacency[e["from_record_id"]].append(e["to_record_id"])
    visiting, visited = set(), set()

    def walk(rid: str) -> None:
        if rid in visiting:
            _fail("INVALID_STATE_TRANSITION", "reference cycle")
        if rid not in visited:
            visiting.add(rid)
            for child in adjacency[rid]:
                walk(child)
            visiting.remove(rid)
            visited.add(rid)
    for rid in adjacency:
        walk(rid)
    boundaries = {(r["data"]["adoption_boundary_version"], r["data"]["adoption_boundary_status"])
                  for r in records if r["kind"] == "consumption"}
    version, status = next(iter(boundaries)) if len(boundaries) == 1 else (
        ("MIXED", "MIXED") if boundaries else (ADOPTION_BOUNDARY_VERSION, ADOPTION_BOUNDARY_STATUS))
    return {"schema_version": SCHEMA_VERSION, "structural_status": "VALID_WITH_UNKNOWNS" if issues else "VALID",
            "record_count": len(records), "counts_by_kind": {k: len(v) for k, v in indices.items()},
            "fixture_only": all(r["context"]["fixture_only"] for r in records) if records else None,
            "candidate_policy_input_receipts": candidates, "adoption_boundary_status": status,
            "recorded_policy_input_receipts": included_receipts,
            "adoption_boundary_version": version, "scientific_claim_eligible": False,
            "issues": issues, "edges": edges, "timeline": deepcopy(records),
            "causal_effect_status": "NOT_EVALUATED", "physical_arrival_status": "UNKNOWN"}
