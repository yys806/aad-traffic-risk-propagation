from copy import deepcopy
from dataclasses import asdict, replace, FrozenInstanceError
import json
from pathlib import Path

import pytest

from riskprop.controller_evidence import (ADOPTION_BOUNDARY_STATUS, ADOPTION_BOUNDARY_VERSION,
    EvidenceError, EvidenceJournal, validate_records)
from riskprop.message_driven_longitudinal_controller import (LocalState, Message, PolicyConfig, PolicyInput,
    RiskPayload, RunAssignment, byte_hash, longitudinal_policy, validate_message, load_engineering_config)
from riskprop.p7_evidence_adapter import P7EvidenceAdapter
from riskprop.p7_message_runtime import InProcessSingleHop, MessageController, generate_synthetic_message

CONFIG = Path(__file__).resolve().parents[1] / "configs/p7_task2_engineering_candidate_v1.json"


def config():
    return load_engineering_config(CONFIG)


def state(**changes):
    return replace(LocalState("p7_target", "target:entry1", 2.0, 20, "tgt_road", "tgt_road_0",
        50.0, (150.0, 50.0), 12.0, 0.0, 20.0, 20.0, "p7_leader", 12.0, 25.0), **changes)


class NativeAPI:
    def __init__(self):
        self.limit = 20.0
        self.calls = []

    def setMaxSpeed(self, vehicle, value):
        self.calls.append((vehicle, value))
        self.limit = value

    def getMaxSpeed(self, vehicle):
        return self.limit


def runtime(tmp_path, mode="ENABLED", policy=None):
    assignment = RunAssignment(mode, "engineering-assignment", "explicit-test")
    a = P7EvidenceAdapter(tmp_path / "capture", "test-run", assignment)
    a.blob("controller_config.json", CONFIG.read_bytes(), raw=True)
    kwargs = {"policy": policy} if policy else {}
    c = MessageController(a, assignment, config(), state(), "a" * 64, byte_hash(CONFIG.read_bytes()), **kwargs)
    return a, c, assignment, NativeAPI()


def send(a, c):
    m = generate_synthetic_message(a, state(), config())
    InProcessSingleHop(a).send(m, c, state())
    return m


def kind(a, name):
    return [r for r in a.journal.records if r["kind"] == name]


def test_no_message_native_no_command(tmp_path):
    a, c, z, api = runtime(tmp_path)
    out = c.decide(state(), z, api)
    assert out["target_speed_reference_mps"] is None and api.calls == []
    assert kind(a, "decision")[0]["data"]["command_disposition"] == "NONE"
    a.finalize()


@pytest.mark.parametrize("mode,expected", [("ENABLED", "POLICY_INPUT_INCLUDED"), ("DISABLED", "REJECTED")])
def test_real_gate_receive_validate_input_and_agreed_boundary(tmp_path, mode, expected):
    a, c, z, api = runtime(tmp_path, mode)
    send(a, c)
    out = c.decide(state(), z, api)
    assert len(kind(a, "delivery")) == len(kind(a, "validation")) == len(kind(a, "input")) == 1
    receipt = kind(a, "consumption")[0]["data"]
    assert receipt["consumption_status"] == expected
    assert receipt["adoption_boundary_status"] == "AGREED" == ADOPTION_BOUNDARY_STATUS
    assert receipt["adoption_boundary_version"] == ADOPTION_BOUNDARY_VERSION
    snap = json.loads((a.root / out["input_snapshot_ref"]).read_text())
    assert len(snap["messages"]) == int(mode == "ENABLED")
    assert (out["target_speed_reference_mps"] is None) == (mode == "DISABLED")
    if mode == "DISABLED":
        assert receipt["reason"] == "ADOPTION_DISABLED" and api.calls == []
    a.finalize()


@pytest.mark.parametrize("changes,reason", [
    ({"simulation_time_s": 8.0}, "VALID_UNTIL_EXCLUSIVE"),
    ({"edge_id": "other"}, "SPATIAL_SCOPE_NOT_APPLICABLE"),
    ({"vehicle_id": "other"}, "TARGET_NOT_APPLICABLE"),
    ({"simulation_time_s": 1.0}, "NOT_YET_VALID"),
    ({"lane_position_m": 300.0}, "SPATIAL_SCOPE_NOT_APPLICABLE"),
])
def test_validation_never_allows_expired_future_or_inapplicable(tmp_path, changes, reason):
    a, c, z, api = runtime(tmp_path)
    m = send(a, c)
    assert validate_message(m, state(**changes)).reason == reason
    a.producer_log.close()


def test_expired_release_original_limit_and_no_lingering_policy_input(tmp_path):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    first = c.decide(state(), z, api)
    assert first["target_speed_reference_mps"] == 10.0
    end = c.decide(state(simulation_time_s=8.0, simulation_step=80), z, api)
    assert end["target_speed_reference_mps"] is None
    assert api.calls == [("p7_target", 10.0), ("p7_target", 20.0)]
    assert kind(a, "consumption")[-1]["data"]["consumption_status"] == "REJECTED"
    a.finalize()


def test_monotone_risk_and_local_traffic_dependency(tmp_path):
    a, c, z, api = runtime(tmp_path)
    m = send(a, c)
    p = RiskPayload.from_bytes(m.raw_payload)
    pc = PolicyConfig.from_dict(config())
    speeds = [longitudinal_policy(PolicyInput(state(), (("m", replace(p, risk_level=level)),)), pc).target_speed_reference_mps
              for level in ("LOW", "MEDIUM", "HIGH")]
    assert speeds == [18, 14, 10]
    close = longitudinal_policy(PolicyInput(state(net_gap_m=1.0, leader_speed_mps=4.0), (("m", p),)), pc)
    assert close.target_speed_reference_mps == 2.5
    a.producer_log.close()


def test_hash_and_payload_unknown_extra_future_command_rejected(tmp_path):
    a, c, z, api = runtime(tmp_path)
    m = send(a, c)
    assert validate_message(replace(m, payload_hash="b" * 64), state()).reason == "PAYLOAD_HASH_MISMATCH"
    d = json.loads(m.raw_payload)
    for name in ("acceleration_command", "future_trajectory"):
        raw = json.dumps({**d, name: 3}).encode()
        assert validate_message(replace(m, raw_payload=raw, payload_hash=byte_hash(raw)), state()).status == "INVALID"
    a.producer_log.close()


def test_invalid_message_cannot_influence_policy(tmp_path):
    a, c, z, api = runtime(tmp_path)
    m = send(a, c)
    c.inbox[m.message_id] = replace(m, raw_payload=b"bad"), c.inbox[m.message_id][1]
    out = c.decide(state(), z, api)
    assert out["target_speed_reference_mps"] is None and not api.calls
    assert kind(a, "validation")[0]["data"]["validation_status"] == "INVALID"
    a.finalize()


@pytest.mark.parametrize("data", [{}, {"adoption_mode": "UNKNOWN"}, {"adoption_mode": "ENABLED"}])
def test_missing_mode_assignment_is_fail_closed(data):
    with pytest.raises(ValueError):
        RunAssignment.from_dict(data)


def test_run_mode_immutable_and_mismatch_fails(tmp_path):
    a, c, z, api = runtime(tmp_path)
    with pytest.raises(FrozenInstanceError):
        z.adoption_mode = "DISABLED"
    with pytest.raises(ValueError, match="RUN_ASSIGNMENT_CHANGED"):
        c.decide(state(), replace(z, adoption_mode="DISABLED"), api)
    assert not api.calls
    a.finalize()


def test_unchanged_decision_still_has_consumption_no_new_command(tmp_path):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    c.decide(state(), z, api)
    second = c.decide(state(simulation_time_s=2.1, simulation_step=21), z, api)
    assert len(kind(a, "consumption")) == 2 and len(api.calls) == 1
    assert kind(a, "decision")[-1]["data"]["decision_status"] == "UNCHANGED"
    assert second["new_command_needed"] is False
    a.finalize()


def test_policy_failure_recorded_without_command_and_input_not_erased(tmp_path):
    def fails(inputs, config):
        assert inputs.messages
        raise RuntimeError("test-policy-failure")
    a, c, z, api = runtime(tmp_path, policy=fails)
    send(a, c)
    with pytest.raises(RuntimeError, match="test-policy-failure"):
        c.decide(state(), z, api)
    assert kind(a, "decision")[-1]["data"]["decision_status"] == "FAILED"
    assert len(kind(a, "consumption")) == 1 and not api.calls
    a.finalize()


@pytest.mark.parametrize("send_status,delivery_status", [("FAILED", "RECEIVED"), ("UNKNOWN", "RECEIVED"), ("SENT", "CONFIRMED_FAILURE"), ("SENT", "UNKNOWN")])
def test_transport_failures_and_unknown_preserved(tmp_path, send_status, delivery_status):
    a, c, z, api = runtime(tmp_path)
    m = generate_synthetic_message(a, state(), config())
    InProcessSingleHop(a).send(m, c, state(), send_status=send_status, delivery_status=delivery_status)
    c.decide(state(), z, api)
    assert not c.inbox and not api.calls
    assert kind(a, "send")[0]["data"]["send_status"] == send_status
    a.finalize()


def test_legacy_bundle_read_keeps_proposed_and_cannot_silently_promote():
    root = Path(__file__).resolve().parents[2] / "evidence/research/P3_TASK2_20261103"
    candidates = list(root.rglob("*.json"))
    bundles = []
    for p in candidates:
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict) and set(d) == {"schema_version", "adoption_boundary_version", "adoption_boundary_status", "scientific_claim_eligible", "records"}:
            bundles.append(d)
    assert bundles
    for d in bundles:
        j = EvidenceJournal.from_dict(d)
        assert j.to_dict() == d and j.to_dict()["adoption_boundary_status"] == "PROPOSED"
        j.validate()
    d = deepcopy(next(d for d in bundles if any(r["kind"] == "consumption" for r in d["records"])))
    d["adoption_boundary_version"], d["adoption_boundary_status"] = ADOPTION_BOUNDARY_VERSION, ADOPTION_BOUNDARY_STATUS
    with pytest.raises(EvidenceError, match="SCHEMA_MISMATCH"):
        EvidenceJournal.from_dict(d)


def test_many_decisions_one_command_poststep_reads_exit_and_p4_unknown(tmp_path):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    for i in range(2):
        s = state(simulation_time_s=2.0 + i * 0.1, simulation_step=20 + i)
        c.decide(s, z, api)
        row = {**asdict(state(simulation_time_s=2.1 + i * 0.1, simulation_step=21 + i)),
               "vehicle_existence": True, "readback_status": "OBSERVED"}
        ref, _ = a.blob(f"readbacks/{i}.json", row)
        c.observe(row, ref)
    row = {"simulation_time_s": 2.3, "simulation_step": 23, "vehicle_existence": False, "readback_status": "VEHICLE_EXITED"}
    ref, _ = a.blob("readbacks/exit.json", row)
    action = c.observe(row, ref)
    c.risk_attachment([action], 2.3, 23, {"measurement_version": "existing-version", "risk_effect_status": "UNKNOWN"})
    audit = a.finalize()
    assert audit["counts_by_kind"]["safety"] == 0
    assert audit["counts_by_kind"]["execution"] == 3 and len(api.calls) == 1
    assert len(audit["candidate_policy_input_receipts"]) == 2
    assert {r["data"]["command_id"] for r in kind(a, "execution")} == {kind(a, "command")[0]["data"]["command_id"]}
    assert kind(a, "execution")[-1]["data"]["actual_speed"] is None
    assert kind(a, "execution")[-1]["data"]["execution_status"] == "VEHICLE_EXITED"
    assert kind(a, "risk_observation")[0]["data"]["risk_status"] == "UNKNOWN"
    with pytest.raises(ValueError, match="LIFECYCLE_MISMATCH"):
        c.decide(state(), z, api)


def test_external_artifacts_payload_and_snapshot_byte_hashes(tmp_path):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    c.decide(state(), z, api)
    a.finalize()
    for r in kind(a, "message"):
        assert byte_hash((a.root / r["data"]["payload_ref"]).read_bytes()) == r["data"]["payload_hash"]
    for r in kind(a, "decision"):
        result = json.loads((a.root / r["data"]["decision_output_ref"]).read_bytes())
        assert byte_hash((a.root / result["input_snapshot_ref"]).read_bytes()) == r["data"]["input_snapshot_hash"]
    for p, h in a.artifacts.items():
        assert byte_hash((a.root / p).read_bytes()) == h


def test_multi_message_one_decision(tmp_path):
    a, c, z, api = runtime(tmp_path)
    m = send(a, c)
    m2 = replace(m, message_id="second-message")
    # Message generator owns its distinct second record; not a forged consumption.
    first = kind(a, "message")[0]
    row = deepcopy(first)
    row["context"].update(record_id=a.identity("record"), message_id=m2.message_id)
    a.journal.append_record(row)
    InProcessSingleHop(a).send(m2, c, state())
    c.decide(state(), z, api)
    assert len(kind(a, "decision")[0]["data"]["consumed_message_refs"]) == 2
    a.finalize()


@pytest.mark.parametrize("change,code", [("run", "CROSS_RUN_REFERENCE"), ("incarnation", "CROSS_VEHICLE_REFERENCE"), ("duplicate", "DUPLICATE_ID"), ("hash", "CONFLICTING_PAYLOAD_HASH")])
def test_actual_capture_foreign_keys_and_duplicate_rejections(tmp_path, change, code):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    c.decide(state(), z, api)
    rows = a.journal.records
    receipt = next(r for r in rows if r["kind"] == "consumption")
    if change == "run": receipt["context"]["run_id"] = "other"
    if change == "incarnation": receipt["context"]["vehicle_incarnation_id"] = "other-life"
    if change == "hash": receipt["data"]["payload_hash"] = "b" * 64
    if change == "duplicate": rows.append(deepcopy(receipt))
    with pytest.raises(EvidenceError) as exc:
        validate_records(rows)
    assert exc.value.code == code
    a.producer_log.close()


def test_corrected_reference_rate_is_local_state_bound_and_risk_monotone(tmp_path):
    a, c, z, api = runtime(tmp_path)
    m = send(a, c)
    p = RiskPayload.from_bytes(m.raw_payload)
    cfg = load_engineering_config(CONFIG.with_name("p7_task2_engineering_candidate_v2.json"))
    pc = PolicyConfig.from_dict(cfg)
    references = [longitudinal_policy(PolicyInput(state(), (("m", replace(p, risk_level=l)),)), pc).target_speed_reference_mps
                  for l in ("LOW", "MEDIUM", "HIGH")]
    assert references == sorted(references, reverse=True)
    assert references[-1] == pytest.approx(11.9)
    assert references[-1] >= state().speed_mps - cfg["reference_deceleration_mps2"] * cfg["step_s"]
    assert longitudinal_policy(PolicyInput(state(), ()), pc).target_speed_reference_mps is None
    a.producer_log.close()


def test_active_sumo_entry_refuses_historical_unbounded_candidate(tmp_path):
    from riskprop.p7_sumo_integration import run_condition
    with pytest.raises(ValueError, match="UNBOUNDED_REFERENCE_STEP_NOT_ADMITTED"):
        run_condition(tmp_path / "must-not-create", CONFIG, condition="ENABLED", adoption_mode="ENABLED",
                      assignment_id="explicit", adoption_mode_source="test")
    assert not (tmp_path / "must-not-create").exists()


def test_run_termination_preserves_right_censoring_without_fake_readback(tmp_path):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    c.decide(state(), z, api)
    c.censor(2.1, 21, "bounded-stop")
    audit = a.finalize()
    ex = kind(a, "execution")[-1]["data"]
    assert ex["execution_status"] == "RIGHT_CENSORED"
    assert ex["state_readback_ref"] is None and ex["actual_speed"] is None
    assert {"UNKNOWN_EXECUTION", "MISSING_STATE_READBACK"} <= {i["code"] for i in audit["issues"]}


def test_future_expiry_is_declared_known_now_not_future_observation(tmp_path):
    a, c, z, api = runtime(tmp_path)
    send(a, c)
    expiry = kind(a, "message")[0]["data"]["valid_until"]
    assert expiry["native_timestamp"] == 8 and expiry["observed_at"] == expiry["available_at"] == 2
    a.finalize()


@pytest.mark.parametrize("bad", [None, [], {}])
def test_malformed_boundary_never_passes_or_crashes_hash_lookup(bad):
    with pytest.raises(EvidenceError, match="SCHEMA_MISMATCH"):
        EvidenceJournal(adoption_boundary_version=bad, adoption_boundary_status="AGREED")
