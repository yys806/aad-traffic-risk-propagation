"""Deterministic synthetic producer calls for P3 Task2; never starts SUMO."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from riskprop.controller_evidence import (
    LEGACY_ADOPTION_BOUNDARY_STATUS as ADOPTION_BOUNDARY_STATUS,
    LEGACY_ADOPTION_BOUNDARY_VERSION as ADOPTION_BOUNDARY_VERSION, EvidenceJournal,
    EventContext, SPECS, TimeEvidence, canonical_hash,
)


def stamp(t: float, *, phase: str = "fixture", sequence: int = 0) -> dict:
    return asdict(TimeEvidence(native_timestamp=t, clock_id="synthetic-clock", time_unit="s",
                              simulation_step=int(t * 20), phase=phase, sequence=sequence,
                              time_lower=t, time_upper=t, reference_clock_id="synthetic-reference",
                              clock_mapping_version="fixture-identity-v1", observed_at=t, available_at=t))


def complete_fixture() -> EvidenceJournal:
    journal = EvidenceJournal(adoption_boundary_version=ADOPTION_BOUNDARY_VERSION,
                              adoption_boundary_status=ADOPTION_BOUNDARY_STATUS)
    payload, snapshot = canonical_hash({"synthetic_risk": "example"}), canonical_hash({"input": "synthetic"})

    def add(kind: str, rid: str, t: float, data: dict, *, vehicle="target", message=None, source=None):
        role = SPECS[kind]["role"]
        context = EventContext(record_id=rid, run_id="p3-task2-synthetic", pair_id="fixture-pair",
                               cell_id="fixture-s1c1", block_id="fixture-block", producer_id="fixture-" + role,
                               producer_role=role, evidence_ref="synthetic://" + rid, fixture_only=True,
                               vehicle_id=vehicle, vehicle_incarnation_id=vehicle + "-life-1",
                               source_event_id=source, message_id=message)
        journal.append(kind, context, TimeEvidence(**stamp(t)), **data)

    add("source", "r-source", 0, dict(source_type="CONTROLLED_B", qualification_status="SYNTHETIC_CONFIRMED", confirmation_ref="synthetic://confirmation"), vehicle="source", source="s1")
    add("controller", "r-controller", 0.5, dict(controller_id="synthetic-controller", controller_instance_id="ci1",
        controller_version="fixture-v1", controller_code_hash=canonical_hash("fixture-code"), policy_version="fixture-policy-v1",
        policy_config_hash=canonical_hash("fixture-config"), controlled_vehicle_id="target"))
    add("message", "r-message", 1, dict(sender_id="source", payload_hash=payload, payload_type="synthetic-risk",
        payload_ref="synthetic://payload", message_kind="SOURCE", valid_from=stamp(1), valid_until=stamp(100),
        validity_rule_ref="synthetic-only-rule-not-a-frozen-TTL"), vehicle="source", source="s1", message="m1")
    add("send", "r-send", 2, dict(attempt_id="a1", send_status="SENT", transport_ref="synthetic://send"), vehicle="source", source="s1", message="m1")
    add("delivery", "r-delivery", 3, dict(delivery_id="dl1", attempt_id="a1", delivery_status="RECEIVED"), source="s1", message="m1")
    add("validation", "r-validation", 4, dict(validation_id="v1", delivery_id="dl1", validator_id="fixture-validator",
        validator_version="v1", validation_status="VALID", reason="synthetic validation"), source="s1", message="m1")
    add("input", "r-input", 5, dict(receipt_id="i1", message_id="m1", payload_hash=payload, validation_id="v1",
        controller_instance_id="ci1", available_time=stamp(5.2), input_schema_version="synthetic-input-v1",
        input_snapshot_ref="synthetic://input", input_status="AVAILABLE"), source="s1", message="m1")
    add("consumption", "r-consumption", 6, dict(consumption_receipt_id="c1", input_receipt_id="i1", message_id="m1",
        payload_hash=payload, controller_instance_id="ci1", decision_id="d1", policy_version="fixture-policy-v1",
        input_snapshot_hash=snapshot, consumption_status="POLICY_INPUT_INCLUDED", reason="synthetic policy-path receipt",
        adoption_boundary_version=ADOPTION_BOUNDARY_VERSION, adoption_boundary_status=ADOPTION_BOUNDARY_STATUS), source="s1", message="m1")
    add("decision", "r-decision", 7, dict(decision_id="d1", controller_instance_id="ci1", policy_version="fixture-policy-v1",
        input_snapshot_hash=snapshot, consumed_message_refs=[dict(message_id="m1", consumption_receipt_id="c1")],
        decision_status="DECIDED", decision_output_ref="synthetic://decision", control_intent="synthetic-decelerate",
        no_change_reason=None, command_disposition="EXPECTED"))
    add("command", "r-command", 8, dict(command_id="cmd1", decision_id="d1", controller_instance_id="ci1", target_vehicle_id="target",
        command_type="synthetic-acceleration", command_value=-1.0, command_unit="m/s2", valid_from=stamp(8), valid_until=stamp(15),
        command_status="ACKNOWLEDGED", execution_interface_ref="synthetic://not-a-SUMO-call", ack_time=stamp(8.2),
        failure_reason=None, execution_disposition="EXPECTED"))
    add("safety", "r-safety", 9, dict(intervention_id="sf1", command_id="cmd1", safety_layer_id="synthetic-safety",
        safety_layer_version="v1", constraint_version="synthetic-v1", original_command=-1.0, modified_command=-1.0,
        intervention_status="CONFIRMED_NONE", intervention_reason="explicit synthetic observation"))
    add("execution", "r-execution", 10, dict(execution_id="ex1", command_id="cmd1", target_vehicle_id="target", execution_end=stamp(11),
        execution_status="EXECUTED", actual_acceleration=-0.8, actual_speed=20.0, actual_position=2000.0,
        state_readback_ref="synthetic://readback", execution_reason="synthetic readback, not causal attribution", safety_intervention_refs=["sf1"]))
    add("action_observation", "r-action", 12, dict(action_observation_id="ao1", execution_refs=["ex1"], comparison_ref=None,
        action_change_status="UNKNOWN", observation_ref="synthetic://action"))
    add("risk_observation", "r-risk", 13, dict(risk_observation_id="ro1", action_observation_refs=["ao1"],
        measurement_version="synthetic-placeholder-not-Formal-computation", observation_ref="synthetic://risk", risk_status="UNKNOWN"))
    return journal


def by_kind(records: list[dict], kind: str) -> dict:
    return next(r for r in records if r["kind"] == kind)


def journal_from_records(records: list[dict]) -> EvidenceJournal:
    journal = EvidenceJournal(adoption_boundary_version=ADOPTION_BOUNDARY_VERSION,
                              adoption_boundary_status=ADOPTION_BOUNDARY_STATUS)
    for r in records:
        journal.append_record(r)
    return journal


def scenario_records(name: str) -> list[dict]:
    records = complete_fixture().records
    if name == "A":
        return records
    if name in ("B", "C"):
        records = [r for r in records if r["kind"] in ("source", "controller", "message", "send", "delivery", "validation", "input", "consumption")]
        if name == "B":
            return [r for r in records if r["kind"] != "consumption"]
        c = by_kind(records, "consumption")["data"]
        c.update(consumption_status="CONSIDERED", decision_id=None, reason="synthetic filter only")
    elif name == "D":
        records = [r for r in records if r["kind"] not in ("command", "safety", "execution", "action_observation", "risk_observation")]
        by_kind(records, "decision")["data"].update(decision_status="UNCHANGED", command_disposition="NONE", no_change_reason="same synthetic policy output")
    elif name == "E":
        by_kind(records, "safety")["data"].update(intervention_status="MODIFIED", modified_command=-0.2, intervention_reason="synthetic bound")
        by_kind(records, "execution")["data"].update(execution_status="MODIFIED_EXECUTED", actual_acceleration=-0.15)
    elif name == "G":
        # A second send, another receiver, and a duplicate arrival are distinct observations.
        send = deepcopy(by_kind(records, "send"))
        send["context"]["record_id"] = "r-send-retry"
        send["data"]["attempt_id"] = "a2"
        send["time"] = stamp(2.2)
        records.append(send)
        for rid, did, vehicle, when in [("r-delivery-repeat", "dl-repeat", "target", 3.2), ("r-delivery-other", "dl-other", "other-target", 3.3)]:
            delivery = deepcopy(by_kind(records, "delivery"))
            delivery["context"].update(record_id=rid, vehicle_id=vehicle, vehicle_incarnation_id=vehicle + "-life-1")
            delivery["data"].update(delivery_id=did, attempt_id="a2")
            delivery["time"] = stamp(when)
            records.append(delivery)
        # A second message is consumed by the first decision, with its own input evidence.
        for kind, when, primary in [("message", 1.1, "m2"), ("send", 2.1, "a-m2"), ("delivery", 3.1, "dl-m2"),
                                    ("validation", 4.1, "v-m2"), ("input", 5.1, "i-m2"), ("consumption", 6.1, "c-m2")]:
            row = deepcopy(by_kind(records, kind))
            row["context"].update(record_id="r-" + kind + "-m2", message_id="m2")
            row["time"] = stamp(when)
            d = row["data"]
            if SPECS[kind]["id"] in d:
                d[SPECS[kind]["id"]] = primary
            if "message_id" in d:
                d["message_id"] = "m2"
            for key, value in [("attempt_id", "a-m2"), ("delivery_id", "dl-m2"), ("validation_id", "v-m2"), ("input_receipt_id", "i-m2")]:
                if key in d and key != SPECS[kind]["id"]:
                    d[key] = value
            records.append(row)
        by_kind(records, "decision")["data"]["consumed_message_refs"].append(dict(message_id="m2", consumption_receipt_id="c-m2"))
        # The original message can enter a second decision; it is not a new independent run.
        consumption = deepcopy(by_kind(records, "consumption"))
        consumption["context"]["record_id"] = "r-consumption-cycle2"
        consumption["data"].update(consumption_receipt_id="c-cycle2", decision_id="d2", input_snapshot_hash=canonical_hash("cycle2"))
        consumption["time"] = stamp(16)
        decision = deepcopy(by_kind(records, "decision"))
        decision["context"]["record_id"] = "r-decision-cycle2"
        decision["data"].update(decision_id="d2", consumed_message_refs=[dict(message_id="m1", consumption_receipt_id="c-cycle2")],
                                input_snapshot_hash=canonical_hash("cycle2"), command_disposition="NONE", decision_status="UNCHANGED", no_change_reason="same output")
        decision["time"] = stamp(17)
        records.extend([consumption, decision])
        # Explicitly expired validation is kept, not silently discarded or consumed.
        for kind, when, identity in [("message", 18, "m-exp"), ("send", 19, "a-exp"), ("delivery", 21, "dl-exp"), ("validation", 22, "v-exp")]:
            row = deepcopy(by_kind(records, kind))
            row["context"].update(record_id="r-"+kind+"-expired", message_id="m-exp")
            row["time"] = stamp(when)
            d=row["data"]
            if SPECS[kind]["id"] in d:
                d[SPECS[kind]["id"]]=identity
            if kind=="message":
                d.update(valid_from=stamp(18), valid_until=stamp(20))
            elif kind=="delivery":
                d["attempt_id"]="a-exp"
            elif kind=="validation":
                d.update(delivery_id="dl-exp", validation_status="EXPIRED", reason="explicit synthetic expiry")
            records.append(row)
    elif name == "H":
        for seq, kind in enumerate(("consumption", "decision", "command"), start=1):
            by_kind(records, kind)["time"] = stamp(6, phase=kind, sequence=seq)
        by_kind(records, "command")["data"]["valid_from"] = stamp(6)
        by_kind(records, "validation")["time"].update(time_lower=3.5, time_upper=5)
        by_kind(records, "risk_observation")["time"] = asdict(TimeEvidence(reason="unknown clock and mapping"))
        by_kind(records, "execution")["data"].update(execution_status="RIGHT_CENSORED", execution_end=None,
            actual_acceleration=None, actual_speed=None, actual_position=None, state_readback_ref=None, execution_reason="observed only up to fixture cutoff")
    else:
        raise ValueError(name)
    return records


def invalid_fixtures() -> dict[str, tuple[list[dict], str]]:
    result = {}
    for name, kind, section, key, value, code in [
        ("orphan_message", "input", "context", "message_id", "missing", "ORPHAN_REFERENCE"),
        ("missing_decision", "consumption", "data", "decision_id", "missing", "MISSING_DECISION"),
        ("cross_run", "input", "context", "run_id", "other-run", "CROSS_RUN_REFERENCE"),
        ("cross_incarnation", "input", "context", "vehicle_incarnation_id", "other-life", "CROSS_VEHICLE_REFERENCE"),
        ("payload_conflict", "consumption", "data", "payload_hash", "f"*64, "CONFLICTING_PAYLOAD_HASH"),
        ("missing_command", "execution", "data", "command_id", "missing", "MISSING_COMMAND"),
    ]:
        records = complete_fixture().records
        by_kind(records, kind)[section][key] = value
        result[name] = (records, code)
    records = complete_fixture().records
    records.append(deepcopy(records[0]))
    result["duplicate_id"] = (records, "DUPLICATE_ID")
    return result
