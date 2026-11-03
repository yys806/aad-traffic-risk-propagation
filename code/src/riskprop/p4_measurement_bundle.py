"""Small JSON interchange for P4 v1; explicit IDs, no database or simulation."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from .p4_measurement_contract import (CONTEXT, ENTITIES, SCHEMA_VERSION, check_record,
    evidence_present, provenance_index, require, same_context, sha256_json, stamp,
    validate_states, validate_support)
from .p4_regional_risk import RegionalRiskAssembler
from .p4_evidence_bridge import link_p3_state, link_risk_actions, native_state_bridge

ID_FIELDS = dict(zip(ENTITIES, ("support_id", "provenance_id", "member_id", "state_id",
    "bridge_id", "comparison_id", "action_timing_id", "risk_sample_id",
    "risk_action_bridge_id", "vehicle_window_id", "outcome_id")))


def unavailable_outcome(support, *, reason):
    """No roster means no invented members/N. Keep every assignment visible."""
    return stamp("regional_outcome", {**{k: support.get(k) for k in CONTEXT},
        "outcome_id": support["support_id"] + ":Y", "unit_id": support.get("unit_id"),
        "population_scope": "UNKNOWN_SCOPE", "outcome_status": "UNKNOWN_SCOPE",
        "expected_N": None, "roster_sha256": None, "vehicle_window_refs": [],
        **{k: support.get(k) for k in ("region_id", "region_version", "window_version", "window_start_s", "window_end_s")},
        "lower_outcome": None, "upper_outcome": None, "outcome_unit": "1",
        "missing_summary": {"scope": reason}, "provenance_id": support["provenance_id"],
        "scientific_claim_eligible": False})


def build_bundle(support, roster, states, provenance, *, p3_records=None, associations=None):
    """One assignment per bundle; action comparisons may reference another bundle."""
    p = provenance_index(provenance)
    validate_support(support, p)
    validate_states(states, support)
    require(all(evidence_present(x.get("provenance_id"), p) for x in states), "MISSING_STATE_PROVENANCE", "states")
    associations = associations or []
    require(len({a["state_id"] for a in associations}) == len(associations), "DUPLICATE_ASSOCIATION", "use action IDs list per state")
    by_state = {a["state_id"]: a for a in associations}
    require(not set(by_state) - {s["state_id"] for s in states}, "ORPHAN_ASSOCIATION", "unknown state")
    bridges = []
    for state in states:
        a = by_state.get(state["state_id"])
        require(a is not None and evidence_present(a.get("provenance_id"), p), "ASSOCIATION_EVIDENCE_MISSING", state["state_id"])
        if a.get("command_status") == "NATIVE_NO_COMMAND":
            require(not a.get("action_observation_ids"), "AMBIGUOUS_COMMAND_STATUS", state["state_id"])
            bridges.append(native_state_bridge(state, provenance_id=a["provenance_id"], native_evidence_ref=a.get("native_evidence_ref")))
        else:
            require(p3_records is not None and bool(a.get("action_observation_ids")), "P3_REFERENCE_REQUIRED", state["state_id"])
            for action_id in a["action_observation_ids"]:
                b = link_p3_state(state, action_id, p3_records, provenance_id=a["provenance_id"])
                # Several explicit observations may refer to the same state.
                b["bridge_id"] += ":" + action_id
                bridges.append(stamp("action_execution_bridge", b))
    if roster is None:
        measured = {"risk_samples": [], "vehicle_windows": [], "links": [],
            "outcome": unavailable_outcome(support, reason="PREASSIGNMENT_COMPLETE_ROSTER_NOT_AVAILABLE")}
    else:
        measured = RegionalRiskAssembler(support, roster, provenance).measure(states)
    records = {entity: [] for entity in ENTITIES}
    records.update(support_manifest=[stamp("support_manifest", support)],
        provenance=[stamp("provenance", x) for x in provenance],
        cohort_member=[stamp("cohort_member", {**{k: support.get(k) for k in CONTEXT}, **m}) for m in (roster or {}).get("members", [])],
        state_observation=[stamp("state_observation", s) for s in states],
        action_execution_bridge=bridges, risk_sample=measured["risk_samples"],
        risk_action_bridge=link_risk_actions(measured["risk_samples"], bridges),
        vehicle_window=measured["vehicle_windows"], regional_outcome=[measured["outcome"]])
    bundle = {"schema_version": SCHEMA_VERSION, "usage": support.get("usage"),
        "roster": deepcopy(roster), "records": records, "interval_links": measured["links"],
        "p3_records": deepcopy(p3_records) if p3_records is not None else [],
        "scientific_claim_eligible": False}
    bundle["bundle_sha256"] = sha256_json(bundle)
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle, *, artifact_root=None):
    require(bundle.get("schema_version") == SCHEMA_VERSION, "SCHEMA_MISMATCH", "bundle")
    require(bundle.get("bundle_sha256") == sha256_json({k: v for k, v in bundle.items() if k != "bundle_sha256"}),
        "BUNDLE_HASH_MISMATCH", "bundle")
    records = bundle["records"]
    require(set(records) == set(ENTITIES), "ENTITY_SET_MISMATCH", "eleven implemented entities")
    indexes = {}
    for entity, rows in records.items():
        idx = {}
        for r in rows:
            check_record(r, entity)
            key = r.get(ID_FIELDS[entity])
            require(isinstance(key, str) and key and key not in idx, "DUPLICATE_ENTITY_ID", entity)
            idx[key] = r
        indexes[entity] = idx
    require(len(records["support_manifest"]) == 1 and len(records["regional_outcome"]) == 1, "INVALID_BUNDLE_SUPPORT", "one assignment")
    support = records["support_manifest"][0]
    p = provenance_index(records["provenance"], artifact_root)
    validate_support(support, p)
    validate_states(records["state_observation"], support)
    for entity, rows in records.items():
        for r in rows:
            if entity != "provenance":
                require(evidence_present(r.get("provenance_id", support["provenance_id"]), p), "MISSING_PROVENANCE", entity)
            if entity not in ("provenance", "action_comparison", "action_timing"):
                same_context(r, support)
    def ref(entity, key):
        require(key in indexes[entity], "ORPHAN_FOREIGN_KEY", str((entity, key)))
        return indexes[entity][key]
    for b in records["action_execution_bridge"]:
        state = ref("state_observation", b["state_id"])
        require(b["command_status"] in ("NATIVE_NO_COMMAND", "EXPLICIT_COMMAND_CHAIN"), "INVALID_COMMAND_STATUS", b["bridge_id"])
        if b["command_status"] == "NATIVE_NO_COMMAND":
            require(not any(b[k] for k in ("execution_refs", "command_refs", "decision_refs", "consumption_refs", "message_refs")),
                "NATIVE_HAS_COMMAND_REFERENCE", b["bridge_id"])
            require(isinstance(b.get("native_evidence_ref"), str) or b.get("action_observation_id") is not None,
                "NATIVE_EVIDENCE_REQUIRED", b["bridge_id"])
        if b.get("action_observation_id") is not None:
            expected_bridge = link_p3_state(state, b["action_observation_id"], bundle.get("p3_records", []),
                provenance_id=b["provenance_id"])
            for k in ("execution_refs", "execution_statuses", "command_refs", "decision_refs", "consumption_refs", "message_refs", "command_status"):
                require(b[k] == expected_bridge[k], "P3_BRIDGE_MISMATCH", k)
    for r in records["risk_sample"]:
        state = ref("state_observation", r["state_id"])
        require(state["member_id"] == r["member_id"], "RISK_MEMBER_MISMATCH", r["risk_sample_id"])
    for b in records["risk_action_bridge"]:
        risk, action = ref("risk_sample", b["risk_sample_id"]), ref("action_execution_bridge", b["bridge_id"])
        require(risk["state_id"] == action["state_id"], "RISK_ACTION_STATE_MISMATCH", b["risk_action_bridge_id"])
    require({b["state_id"] for b in records["action_execution_bridge"]} == set(indexes["state_observation"]),
        "STATE_BRIDGE_COVERAGE", "all actual states")
    require({b["risk_sample_id"] for b in records["risk_action_bridge"]} == set(indexes["risk_sample"]),
        "RISK_BRIDGE_COVERAGE", "all risk samples")
    for w in records["vehicle_window"]:
        for key in w["risk_sample_refs"]:
            require(ref("risk_sample", key)["member_id"] == w["member_id"], "WINDOW_MEMBER_MISMATCH", key)
    # Recompute through the same public implementation to validate serialized
    # structure. Independent numerical verification is a separate script.
    roster = bundle.get("roster")
    if roster is not None:
        a = RegionalRiskAssembler(support, roster, records["provenance"])
        require(set(indexes["cohort_member"]) == {m["member_id"] for m in a.roster.members}, "ROSTER_ENTITY_MISMATCH", "members")
        for member in a.roster.members:
            require(all(indexes["cohort_member"][member["member_id"]].get(k) == v for k,v in member.items()),
                "ROSTER_MEMBER_CONTENT_MISMATCH", member["member_id"])
        expected = a.measure(records["state_observation"])
        for entity, values in (("risk_sample", expected["risk_samples"]), ("vehicle_window", expected["vehicle_windows"]),
                ("regional_outcome", [expected["outcome"]])):
            # Stamped input records carry transport fields; derived output is
            # compared by exact canonical body including provenance/hash.
            require(records[entity] == values, "DERIVED_RECORD_MISMATCH", entity)
    else:
        require(not records["cohort_member"] and not records["vehicle_window"] and not records["risk_sample"]
            and records["regional_outcome"][0]["outcome_status"] == "UNKNOWN_SCOPE", "UNPROVEN_SCOPE_NUMERIC_RESULT", "no roster")
    return {"status": "VALID_WITH_LIMITATIONS", "entity_counts": {k: len(v) for k, v in records.items()},
        "source_bytes_verified": artifact_root is not None, "P3_bytes_validated_at_bridge_creation": True}


def write_bundle(bundle, path):
    validate_bundle(bundle)
    Path(path).write_text(json.dumps(bundle, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def assignment_result(bundle):
    validate_bundle(bundle)
    outcome = deepcopy(bundle["records"]["regional_outcome"][0])
    outcome["source_hashes"] = sorted({r["source_sha256"] for r in bundle["records"]["provenance"]})
    outcome["independent_unit"] = "ASSIGNMENT_NOT_VEHICLE_OR_SAMPLE"
    return outcome
