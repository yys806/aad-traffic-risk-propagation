"""Engineering candidate only: risk information -> native-speed-limit reference.

No TraCI calls, future truth, randomization, direct acceleration, or safety layer.
The caller MUST gate validated messages before constructing PolicyInput.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

PAYLOAD_SCHEMA = "aad.p7.risk-payload.engineering.v1"
INPUT_SCHEMA = "aad.p7.policy-input.engineering.v1"
MODE_VERSION = "aad.p7.run-adoption-mode.v1"
PARAMETER_STATUS = "ENGINEERING_CANDIDATE_NOT_FORMAL"
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def byte_hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def finite_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


@dataclass(frozen=True)
class RunAssignment:
    adoption_mode: str
    assignment_id: str
    adoption_mode_source: str
    adoption_mode_version: str = MODE_VERSION

    def __post_init__(self):
        if self.adoption_mode not in ("ENABLED", "DISABLED"):
            raise ValueError("explicit ENABLED or DISABLED required; fail closed")
        if not self.assignment_id or not self.adoption_mode_source or self.adoption_mode_version != MODE_VERSION:
            raise ValueError("assignment identity/source/version required")

    @classmethod
    def from_dict(cls, data: dict) -> RunAssignment:
        for key in ("adoption_mode", "assignment_id", "adoption_mode_source"):
            if key not in data:
                raise ValueError("missing run assignment field: " + key)
        return cls(**data)

    def assert_matches(self, other: RunAssignment) -> None:
        if self != other:
            raise ValueError("RUN_ASSIGNMENT_CHANGED")


@dataclass(frozen=True)
class LocalState:
    vehicle_id: str
    vehicle_incarnation_id: str
    simulation_time_s: float
    simulation_step: int
    edge_id: str
    lane_id: str
    lane_position_m: float
    position_xy_m: tuple[float, float]
    speed_mps: float
    acceleration_mps2: float
    original_max_speed_mps: float
    lane_max_speed_mps: float
    leader_id: str | None = None
    leader_speed_mps: float | None = None
    net_gap_m: float | None = None

    def validate(self) -> None:
        for name in ("simulation_time_s", "lane_position_m", "speed_mps", "acceleration_mps2",
                     "original_max_speed_mps", "lane_max_speed_mps"):
            if not finite_number(getattr(self, name)):
                raise ValueError("UNOBSERVABLE_LOCAL_STATE: " + name)
        if self.speed_mps < 0 or min(self.original_max_speed_mps, self.lane_max_speed_mps) <= 0:
            raise ValueError("INVALID_LOCAL_SPEED")
        if len(self.position_xy_m) != 2 or not all(finite_number(v) for v in self.position_xy_m):
            raise ValueError("INVALID_POSITION")
        if self.leader_id is not None and (not finite_number(self.leader_speed_mps) or
                not finite_number(self.net_gap_m) or self.net_gap_m < 0 or self.leader_speed_mps < 0):
            raise ValueError("UNOBSERVABLE_LEADER_STATE")


@dataclass(frozen=True)
class RiskPayload:
    payload_schema_version: str
    parameter_status: str
    source_event_id: str
    event_type: str
    risk_level: str
    affected_edge_id: str
    lane_position_min_m: float
    lane_position_max_m: float
    target_vehicle_ids: tuple[str, ...]
    generated_time: float
    valid_from: float
    valid_until: float

    def to_bytes(self) -> bytes:
        return canonical_bytes(asdict(self))

    @classmethod
    def from_bytes(cls, raw: bytes) -> RiskPayload:
        def unique(pairs):
            d = {}
            for key, value in pairs:
                if key in d:
                    raise ValueError("duplicate payload key")
                d[key] = value
            return d
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
        if not isinstance(data, dict) or not isinstance(data.get("target_vehicle_ids"), list):
            raise ValueError("invalid payload object/targets")
        data["target_vehicle_ids"] = tuple(data["target_vehicle_ids"])
        payload = cls(**data)  # extra fields, including commands/future truth, rejected
        if payload.payload_schema_version != PAYLOAD_SCHEMA or payload.parameter_status != PARAMETER_STATUS:
            raise ValueError("unsupported payload version/status")
        if payload.event_type != "SYNTHETIC_REMOTE_RISK" or payload.risk_level not in RISK_LEVELS:
            raise ValueError("engineering event/risk enum required")
        if not payload.source_event_id or not payload.affected_edge_id or not payload.target_vehicle_ids:
            raise ValueError("source/region/target required")
        if any(not isinstance(v, str) or not v for v in payload.target_vehicle_ids):
            raise ValueError("invalid target IDs")
        for name in ("lane_position_min_m", "lane_position_max_m", "generated_time", "valid_from", "valid_until"):
            if not finite_number(getattr(payload, name)):
                raise ValueError("nonfinite payload field")
        if not (payload.generated_time <= payload.valid_from < payload.valid_until and
                0 <= payload.lane_position_min_m < payload.lane_position_max_m):
            raise ValueError("invalid payload interval")
        return payload


@dataclass(frozen=True)
class Message:
    message_id: str
    sender_id: str
    receiver_id: str
    source_event_id: str
    raw_payload: bytes
    payload_hash: str


@dataclass(frozen=True)
class ValidationResult:
    status: str
    reason: str
    payload: RiskPayload | None


def validate_message(message: Message, state: LocalState) -> ValidationResult:
    if byte_hash(message.raw_payload) != message.payload_hash:
        return ValidationResult("INVALID", "PAYLOAD_HASH_MISMATCH", None)
    try:
        p = RiskPayload.from_bytes(message.raw_payload)
    except (ValueError, TypeError, UnicodeError) as exc:
        return ValidationResult("INVALID", "PAYLOAD_SCHEMA: " + str(exc), None)
    if p.source_event_id != message.source_event_id:
        return ValidationResult("INVALID", "SOURCE_MISMATCH", None)
    if state.simulation_time_s >= p.valid_until:
        return ValidationResult("EXPIRED", "VALID_UNTIL_EXCLUSIVE", p)
    if state.simulation_time_s < p.valid_from:
        return ValidationResult("INVALID", "NOT_YET_VALID", p)
    if message.receiver_id != state.vehicle_id or state.vehicle_id not in p.target_vehicle_ids:
        return ValidationResult("INVALID", "TARGET_NOT_APPLICABLE", p)
    if state.edge_id != p.affected_edge_id or not p.lane_position_min_m <= state.lane_position_m < p.lane_position_max_m:
        return ValidationResult("INVALID", "SPATIAL_SCOPE_NOT_APPLICABLE", p)
    return ValidationResult("VALID", "ENGINEERING_PAYLOAD_VALID_NOT_FORMAL_QUALIFICATION", p)


@dataclass(frozen=True)
class PolicyConfig:
    policy_version: str
    risk_speed_factors: tuple[float, float, float]
    headway_reference_s: float
    reference_deceleration_mps2: float | None = None
    step_s: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> PolicyConfig:
        if data.get("parameter_status") != PARAMETER_STATUS or data.get("engineering_candidate_not_formal") is not True:
            raise ValueError("non-formal engineering configuration required")
        factors = tuple(data["risk_speed_factors"][k] for k in RISK_LEVELS)
        if any(not finite_number(v) or not 0 < v <= 1 for v in factors) or not all(
                a >= b for a, b in zip(factors, factors[1:])):
            raise ValueError("risk factors must be positive, bounded, monotone")
        h = data["policy_headway_reference_s"]
        if not finite_number(h) or h <= 0:
            raise ValueError("positive engineering headway reference required")
        rate = data.get("reference_deceleration_mps2")
        step = data.get("step_s")
        if rate is not None and (not finite_number(rate) or rate <= 0 or not finite_number(step) or step <= 0):
            raise ValueError("positive reference-rate and step required")
        return cls(data["policy_version"], factors, h, rate, step)


@dataclass(frozen=True)
class PolicyInput:
    local_state: LocalState
    messages: tuple[tuple[str, RiskPayload], ...]

    def snapshot(self) -> dict:
        return {"input_schema_version": INPUT_SCHEMA, "local_state": asdict(self.local_state),
                "messages": [{"message_id": mid, "payload": asdict(p)} for mid, p in self.messages]}


@dataclass(frozen=True)
class PolicyOutput:
    target_speed_reference_mps: float | None
    control_intent: str
    considered_risk_levels: tuple[str, ...]


def longitudinal_policy(inputs: PolicyInput, config: PolicyConfig) -> PolicyOutput:
    s = inputs.local_state
    s.validate()
    if not inputs.messages:
        return PolicyOutput(None, "NATIVE_FOLLOWING", ())
    # Defensive qualification also protects direct callers of the pure policy.
    for mid, p in inputs.messages:
        result = validate_message(Message(mid, "policy-input", s.vehicle_id, p.source_event_id,
                                          p.to_bytes(), byte_hash(p.to_bytes())), s)
        if result.status != "VALID":
            raise ValueError("unvalidated policy input: " + result.reason)
    reference = min(s.original_max_speed_mps, s.lane_max_speed_mps)
    if s.leader_id is not None:
        # Transparent local-state reference; NOT an independent safety filter.
        reference = min(reference, s.leader_speed_mps + s.net_gap_m / config.headway_reference_s)
    factor = min(config.risk_speed_factors[RISK_LEVELS.index(p.risk_level)] for _, p in inputs.messages)
    target = reference * factor
    if config.reference_deceleration_mps2 is not None:
        # Policy-internal reference shaping, NOT a separate safety event/algorithm.
        # Preserves risk monotonicity; still requires actual SUMO acceptance.
        target = max(target, s.speed_mps - config.reference_deceleration_mps2 * config.step_s)
        target = min(target, s.original_max_speed_mps, s.lane_max_speed_mps)
    return PolicyOutput(target, "MESSAGE_SPEED_CEILING", tuple(p.risk_level for _, p in inputs.messages))


def load_engineering_config(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    PolicyConfig.from_dict(data)
    if data.get("fixture_only") is not True or data.get("scientific_claim_eligible") is not False:
        raise ValueError("engineering-only runner required")
    return data
