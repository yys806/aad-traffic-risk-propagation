"""Explicit P3 -> actual state -> P4 bridges; P3 v1 is read only."""
from __future__ import annotations

from .p4_measurement_contract import CONTEXT, require, same_context, stamp, text


def p3_index(records):
    from .controller_evidence import SPECS, validate_records
    validate_records(records)
    result = {}
    for r in records:
        require(r.get("schema_version") == "aad.p3.controller-evidence.v1", "P3_SCHEMA_MISMATCH", "v1 required")
        field = SPECS[r["kind"]]["id"]
        key = (r["kind"], r["context"].get(field, r["data"].get(field)))
        require(key not in result, "DUPLICATE_P3_ID", str(key))
        result[key] = r
    return result


def link_p3_state(state, action_observation_id, p3_records, *, provenance_id):
    idx = p3_index(p3_records)
    def fetch(kind, key):
        require((kind, key) in idx, "MISSING_P3_REFERENCE", str((kind, key)))
        r = idx[kind, key]
        c = r["context"]
        require(c["run_id"] == state["run_id"] and c.get("assignment_id") == state["assignment_id"]
            and c["vehicle_id"] == state["vehicle_id"] and c["vehicle_incarnation_id"] == state["incarnation_id"],
            "P3_STATE_SCOPE_MISMATCH", str((kind, key)))
        require(c.get("source_event_id") in (None, state.get("event_id")), "P3_EVENT_MISMATCH", str(key))
        return r
    action = fetch("action_observation", action_observation_id)
    require(action["data"]["observation_ref"] == state.get("readback_ref"), "P3_READBACK_REFERENCE_MISMATCH", state["state_id"])
    execution_refs = action["data"]["execution_refs"]
    commands, decisions, receipts, messages = set(), set(), set(), set()
    execution_statuses = {}
    for execution_id in execution_refs:
        execution = fetch("execution", execution_id)
        execution_statuses[execution_id] = execution["data"]["execution_status"]
        require(execution["data"]["state_readback_ref"] == state["readback_ref"], "P3_READBACK_REFERENCE_MISMATCH", execution_id)
        command = fetch("command", execution["data"]["command_id"])
        commands.add(command["data"]["command_id"])
        decision = fetch("decision", command["data"]["decision_id"])
        decisions.add(decision["data"]["decision_id"])
        for ref in decision["data"]["consumed_message_refs"]:
            message_id = ref["message_id"]
            require(("message", message_id) in idx, "MISSING_P3_REFERENCE", message_id)
            message = idx["message", message_id]
            require(message["context"]["run_id"] == state["run_id"] and message["context"].get("assignment_id") == state["assignment_id"],
                    "P3_STATE_SCOPE_MISMATCH", message_id)
            receipt = fetch("consumption", ref["consumption_receipt_id"])
            require(receipt["data"]["decision_id"] == decision["data"]["decision_id"]
                and receipt["data"]["message_id"] == message_id
                and receipt["data"]["consumption_status"] == "POLICY_INPUT_INCLUDED", "ADOPTION_RECEIPT_MISSING", message_id)
            receipts.add(receipt["data"]["consumption_receipt_id"])
            messages.add(message_id)
    # Exact record reference and readback identity, not proximity matching.
    t = action["time"]
    require(t["reference_clock_id"] == state["clock_id"] and t["time_lower"] == state["time_s"] == t["time_upper"]
            and state["time_error_s"] == 0, "P3_STATE_TIME_SUPPORT_MISMATCH", state["state_id"])
    return stamp("action_execution_bridge", {**{k: state.get(k) for k in CONTEXT},
        "bridge_id": "bridge:" + state["state_id"], "state_id": state["state_id"],
        "action_observation_id": action_observation_id, "execution_refs": list(execution_refs),
        "execution_statuses": execution_statuses,
        "command_refs": sorted(commands), "decision_refs": sorted(decisions),
        "consumption_refs": sorted(receipts), "message_refs": sorted(messages),
        "command_status": "EXPLICIT_COMMAND_CHAIN" if commands else "NATIVE_NO_COMMAND",
        "provenance_id": provenance_id})


def native_state_bridge(state, *, provenance_id, native_evidence_ref):
    require(text(native_evidence_ref), "NATIVE_EVIDENCE_REQUIRED", state["state_id"])
    return stamp("action_execution_bridge", {**{k: state.get(k) for k in CONTEXT},
        "bridge_id": "bridge:" + state["state_id"], "state_id": state["state_id"],
        "action_observation_id": None, "execution_refs": [], "command_refs": [], "decision_refs": [],
        "execution_statuses": {},
        "consumption_refs": [], "message_refs": [], "command_status": "NATIVE_NO_COMMAND",
        "native_evidence_ref": native_evidence_ref, "provenance_id": provenance_id})


def link_risk_actions(risk_samples, bridges):
    by_state = {}
    for b in bridges:
        by_state.setdefault(b["state_id"], []).append(b)
    result = []
    for risk in risk_samples:
        require(risk["state_id"] in by_state, "RISK_ACTION_LINK_MISSING", risk["state_id"])
        for b in by_state[risk["state_id"]]:
            same_context(risk, b)
            result.append(stamp("risk_action_bridge", {**{k: risk.get(k) for k in CONTEXT},
                "risk_action_bridge_id": risk["risk_sample_id"] + ":" + b["bridge_id"],
                "risk_sample_id": risk["risk_sample_id"], "bridge_id": b["bridge_id"],
                "association_scope": "EXACT_STATE_ID", "provenance_id": risk["provenance_id"]}))
    return result
