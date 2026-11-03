from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p3_controller_evidence_fixtures import (
    by_kind, complete_fixture, invalid_fixtures, journal_from_records, scenario_records, stamp,
)
from riskprop.controller_evidence import (
    ADOPTION_BOUNDARY_STATUS, ADOPTION_BOUNDARY_VERSION, EvidenceError, EvidenceJournal,
    EventContext, TimeEvidence, compare_times, legacy_protocol_observation, schema_description, validate_records,
)


def expect_error(records, code):
    with pytest.raises(EvidenceError) as caught:
        journal_from_records(records).validate()
    assert caught.value.code == code


def test_A_complete_chain_has_explicit_edges_and_preserves_all_fields():
    records = scenario_records("A")
    audit = validate_records(records)
    assert audit["structural_status"] == "VALID"
    assert audit["candidate_policy_input_receipts"] == ["c1"]
    assert audit["timeline"] == records
    pairs = {(e["from_record_id"], e["to_record_id"]) for e in audit["edges"]}
    for pair in [("r-source", "r-message"), ("r-delivery", "r-validation"), ("r-validation", "r-input"),
                 ("r-input", "r-consumption"), ("r-consumption", "r-decision"), ("r-decision", "r-command"),
                 ("r-command", "r-safety"), ("r-safety", "r-execution"), ("r-execution", "r-action"), ("r-action", "r-risk")]:
        assert pair in pairs
    assert audit["fixture_only"] is True
    assert audit["scientific_claim_eligible"] is False
    assert audit["causal_effect_status"] == "NOT_EVALUATED"
    assert audit["physical_arrival_status"] == "UNKNOWN"
    assert audit["adoption_boundary_status"] == "PROPOSED"


def test_B_validated_input_without_consumption_never_becomes_adoption():
    records = scenario_records("B")
    audit = validate_records(records)
    assert by_kind(records, "validation")["data"]["validation_status"] == "VALID"
    assert audit["counts_by_kind"]["consumption"] == 0
    assert audit["candidate_policy_input_receipts"] == []


def test_C_filter_consideration_is_not_policy_input_inclusion():
    audit = validate_records(scenario_records("C"))
    assert audit["counts_by_kind"]["consumption"] == 1
    assert audit["candidate_policy_input_receipts"] == []
    assert audit["counts_by_kind"]["decision"] == 0


def test_D_policy_consumption_survives_unchanged_decision_and_no_command():
    audit = validate_records(scenario_records("D"))
    assert audit["candidate_policy_input_receipts"] == ["c1"]
    assert audit["counts_by_kind"]["command"] == 0
    assert audit["causal_effect_status"] == "NOT_EVALUATED"


def test_E_safety_modification_does_not_erase_consumption_or_equate_actual_acceleration():
    records = scenario_records("E")
    audit = validate_records(records)
    assert audit["candidate_policy_input_receipts"] == ["c1"]
    assert by_kind(records, "command")["data"]["command_value"] == -1.0
    assert by_kind(records, "safety")["data"]["modified_command"] == -0.2
    assert by_kind(records, "execution")["data"]["actual_acceleration"] == -0.15


@pytest.mark.parametrize("case", list(invalid_fixtures()))
def test_F_integrity_errors_are_not_silently_repaired(case):
    records, code = invalid_fixtures()[case]
    expect_error(records, code)


def test_G_many_messages_decisions_receivers_and_retries_are_not_independent_runs():
    records = scenario_records("G")
    audit = validate_records(records)
    assert audit["counts_by_kind"]["message"] == 3
    assert len(audit["candidate_policy_input_receipts"]) == 3
    assert audit["counts_by_kind"]["decision"] == 2
    assert len(by_kind(records, "decision")["data"]["consumed_message_refs"]) == 2
    assert len({r["context"]["run_id"] for r in records}) == 1
    assert any(r["kind"] == "validation" and r["data"]["validation_status"] == "EXPIRED" for r in records)
    assert any(r["context"]["vehicle_id"] == "other-target" for r in records)


def test_H_same_step_order_overlap_unknown_clock_readback_and_censoring():
    records = scenario_records("H")
    audit = validate_records(records)
    cons, decision = by_kind(records, "consumption"), by_kind(records, "decision")
    assert cons["time"]["native_timestamp"] == decision["time"]["native_timestamp"] == 6
    assert compare_times(cons["time"], decision["time"]) == "CALL_ORDER"
    codes = {x["code"] for x in audit["issues"]}
    assert {"UNKNOWN_TIMESTAMP", "UNKNOWN_TEMPORAL_ORDER", "MISSING_STATE_READBACK", "UNKNOWN_EXECUTION"} <= codes
    assert by_kind(records, "execution")["data"]["actual_acceleration"] is None
    assert by_kind(records, "execution")["data"]["execution_status"] == "RIGHT_CENSORED"


def test_idempotent_replay_is_explicit_and_conflicts_still_raise():
    journal = complete_fixture()
    original = journal.records[0]
    journal.append_record(original, idempotent=True)
    assert len(journal.records) == 14
    original["data"]["confirmation_ref"] = "different"
    with pytest.raises(EvidenceError, match="DUPLICATE_ID"):
        journal.append_record(original, idempotent=True)


def test_returned_records_and_legacy_adapter_cannot_modify_or_promote_history():
    journal = complete_fixture()
    view = journal.records
    view[0]["data"]["source_type"] = "FORMAL_A"
    assert journal.records[0]["data"]["source_type"] == "CONTROLLED_B"
    legacy = {"adopted": True, "adopted_time_s": 2.2}
    mapped = legacy_protocol_observation(legacy, evidence_ref="historical://fixture")
    assert mapped["original"] == legacy
    assert mapped["candidate_adoption_status"] == "UNKNOWN"
    assert mapped["consumption_receipts_created"] == 0


def test_json_roundtrip_separate_schema_and_no_overwrite(tmp_path):
    path = tmp_path / "evidence.json"
    journal = complete_fixture()
    journal.write(path)
    restored = EvidenceJournal.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert restored.records == journal.records
    assert restored.validate()["candidate_policy_input_receipts"] == ["c1"]
    with pytest.raises(FileExistsError):
        journal.write(path)
    assert schema_description()["adoption_boundary_status"] == ADOPTION_BOUNDARY_STATUS


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "6.0", True])
def test_times_do_not_accept_nonfinite_strings_or_booleans(bad):
    records = complete_fixture().records
    by_kind(records, "consumption")["time"]["native_timestamp"] = bad
    expect_error(records, "INVALID_FIELD")


def test_invalid_bounds_and_reversed_execution_interval():
    records = complete_fixture().records
    by_kind(records, "consumption")["time"].update(time_lower=8, time_upper=7)
    expect_error(records, "INVALID_TIME_INTERVAL")
    records = complete_fixture().records
    by_kind(records, "execution")["data"]["execution_end"] = stamp(9)
    expect_error(records, "INVALID_TIME_INTERVAL")


def test_unmapped_or_overlapping_intervals_do_not_become_strict_order():
    left, right = stamp(6), stamp(7)
    left.update(time_lower=5, time_upper=8)
    assert compare_times(left, right) == "OVERLAP"
    left["clock_mapping_version"] = None
    assert compare_times(left, right) == "UNKNOWN"
    assert compare_times(asdict(TimeEvidence()), right) == "UNKNOWN"


def test_sender_cannot_create_receiver_input_or_policy_receipt():
    records = complete_fixture().records
    by_kind(records, "input")["context"]["producer_role"] = "sender"
    expect_error(records, "INVALID_PRODUCER")


def test_expired_message_cannot_be_included_and_boundary_stays_proposed():
    records = complete_fixture().records
    by_kind(records, "message")["data"]["valid_until"] = stamp(3.5)
    expect_error(records, "INVALID_STATE_TRANSITION")
    records = complete_fixture().records
    by_kind(records, "consumption")["data"]["adoption_boundary_status"] = "AGREED"
    expect_error(records, "SCHEMA_MISMATCH")


@pytest.mark.parametrize("status", ["RECEIVED", "REJECTED", "CONSIDERED", "UNKNOWN"])
def test_only_policy_input_included_can_back_decision_message_refs(status):
    records = complete_fixture().records
    by_kind(records, "consumption")["data"]["consumption_status"] = status
    expect_error(records, "INVALID_STATE_TRANSITION")


def test_missing_expected_stages_are_unknown_and_never_created():
    records = [r for r in complete_fixture().records if r["kind"] not in ("command", "safety", "execution", "action_observation", "risk_observation")]
    audit = validate_records(records)
    assert "MISSING_COMMAND" in {x["code"] for x in audit["issues"]}
    records = [r for r in complete_fixture().records if r["kind"] not in ("execution", "action_observation", "risk_observation")]
    audit = validate_records(records)
    assert "MISSING_EXECUTION" in {x["code"] for x in audit["issues"]}
    assert audit["counts_by_kind"]["execution"] == 0


def test_multiple_commands_execution_intervals_and_safety_passes():
    records = complete_fixture().records
    safety2 = deepcopy(by_kind(records, "safety"))
    safety2["context"]["record_id"] = "r-safety2"
    safety2["time"] = stamp(9.5)
    safety2["data"].update(intervention_id="sf2", previous_intervention_id="sf1", intervention_status="MODIFIED", modified_command=-0.5)
    records.append(safety2)
    by_kind(records, "execution")["data"].update(safety_intervention_refs=["sf1", "sf2"], execution_status="MODIFIED_EXECUTED")
    execution2 = deepcopy(by_kind(records, "execution"))
    execution2["context"]["record_id"] = "r-ex2"
    execution2["data"].update(execution_id="ex2", execution_end=stamp(12))
    execution2["time"] = stamp(11.5)
    records.append(execution2)
    command2 = deepcopy(by_kind(records, "command"))
    command2["context"]["record_id"] = "r-cmd2"
    command2["data"].update(command_id="cmd2", execution_disposition="UNKNOWN")
    records.append(command2)
    audit = validate_records(records)
    assert audit["counts_by_kind"]["command"] == 2
    assert audit["counts_by_kind"]["execution"] == 2
    assert audit["counts_by_kind"]["safety"] == 2


@pytest.mark.parametrize("status", ["NOT_OBSERVED", "CONFIRMED_NONE", "MODIFIED", "UNKNOWN"])
def test_safety_absence_and_unknown_are_distinct(status):
    records = complete_fixture().records
    by_kind(records, "safety")["data"]["intervention_status"] = status
    audit = validate_records(records)
    assert by_kind(audit["timeline"], "safety")["data"]["intervention_status"] == status
    assert audit["candidate_policy_input_receipts"] == ["c1"]


def test_safety_rejection_preserves_policy_input_but_forbids_executed_claim():
    records = complete_fixture().records
    by_kind(records, "safety")["data"]["intervention_status"] = "REJECTED"
    expect_error(records, "INVALID_STATE_TRANSITION")
    by_kind(records, "execution")["data"]["execution_status"] = "NOT_EXECUTED"
    assert validate_records(records)["candidate_policy_input_receipts"] == ["c1"]


def test_missing_hashes_preserve_claimed_consumption_but_withhold_candidate_evidence():
    records = complete_fixture().records
    for r in records:
        if "payload_hash" in r["data"]:
            r["data"]["payload_hash"] = None
    audit = validate_records(records)
    assert audit["recorded_policy_input_receipts"] == ["c1"]
    assert audit["candidate_policy_input_receipts"] == []
    assert "UNKNOWN_POLICY_INPUT_EVIDENCE" in {x["code"] for x in audit["issues"]}


def test_duplicate_natural_id_is_rejected_even_with_new_record_id():
    records = complete_fixture().records
    extra = deepcopy(by_kind(records, "decision"))
    extra["context"]["record_id"] = "new-record-same-decision"
    records.append(extra)
    expect_error(records, "DUPLICATE_ID")


def test_cyclic_safety_references_fail_even_if_all_event_times_are_unknown():
    records = complete_fixture().records
    first = by_kind(records, "safety")
    first["time"] = asdict(TimeEvidence())
    first["data"]["previous_intervention_id"] = "sf2"
    second = deepcopy(first)
    second["context"]["record_id"] = "r-safety2"
    second["data"].update(intervention_id="sf2", previous_intervention_id="sf1")
    records.append(second)
    expect_error(records, "INVALID_STATE_TRANSITION")


def test_no_safety_observation_does_not_default_to_no_intervention():
    records = [r for r in complete_fixture().records if r["kind"] != "safety"]
    by_kind(records, "execution")["data"]["safety_intervention_refs"] = []
    audit = validate_records(records)
    assert "UNKNOWN_SAFETY" in {x["code"] for x in audit["issues"]}
    assert audit["candidate_policy_input_receipts"] == ["c1"]


def test_execution_outside_explicit_command_interval_is_invalid():
    records = complete_fixture().records
    by_kind(records, "command")["data"]["valid_until"] = stamp(9)
    expect_error(records, "INVALID_TIME_INTERVAL")


def test_wrong_decision_controller_or_changed_policy_fails():
    records = complete_fixture().records
    by_kind(records, "decision")["data"]["policy_version"] = "other-policy"
    expect_error(records, "CONTEXT_MISMATCH")


def test_assignment_metadata_is_neutral_and_unchanged_across_chain():
    records = complete_fixture().records
    for r in records:
        r["context"].update(assignment_id="a-proposed", adoption_mode="PROPOSED_ENABLED",
                            adoption_mode_source="researcher-proposal", adoption_mode_version="unfrozen-v0")
    audit = validate_records(records)
    assert {r["context"]["adoption_mode"] for r in audit["timeline"]} == {"PROPOSED_ENABLED"}
    assert audit["scientific_claim_eligible"] is False


def test_empty_capture_and_nonfinite_command_do_not_fabricate_evidence():
    audit = EvidenceJournal().validate()
    assert audit["fixture_only"] is None
    assert audit["record_count"] == 0
    assert audit["issues"][0]["code"] == "EMPTY_CAPTURE"
    records = complete_fixture().records
    by_kind(records, "command")["data"]["command_value"] = float("inf")
    expect_error(records, "INVALID_FIELD")


def test_context_message_cannot_name_a_message_not_consumed_by_that_decision():
    records = scenario_records("G")
    decision = next(r for r in records if r["kind"] == "decision" and r["data"]["decision_id"] == "d2")
    decision["context"].update(message_id="m2", source_event_id="s1")
    expect_error(records, "CONTEXT_MISMATCH")


def test_conflicting_payload_under_same_message_identity_is_explicit():
    records = complete_fixture().records
    other = deepcopy(by_kind(records, "message"))
    other["context"]["record_id"] = "second-message-record"
    other["data"]["payload_hash"] = "a" * 64
    records.append(other)
    expect_error(records, "CONFLICTING_PAYLOAD_HASH")


def test_body_time_objects_are_serialized_without_losing_time_fields():
    records = complete_fixture().records
    command = by_kind(records, "command")
    command["data"]["valid_from"] = TimeEvidence(**stamp(8))
    journal = EvidenceJournal()
    for r in records:
        journal.append(r["kind"], EventContext(**r["context"]), TimeEvidence(**r["time"]), **r["data"])
    assert journal.validate()["candidate_policy_input_receipts"] == ["c1"]
    assert by_kind(journal.records, "command")["data"]["valid_from"] == stamp(8)


def test_missing_execution_end_remains_unknown():
    records = complete_fixture().records
    by_kind(records, "execution")["data"]["execution_end"] = None
    audit = validate_records(records)
    assert "UNKNOWN_EXECUTION_END" in {x["code"] for x in audit["issues"]}


def test_reverse_capture_order_still_reports_missing_decision():
    records = [r for r in complete_fixture().records if r["kind"] != "decision"]
    expect_error(list(reversed(records)), "MISSING_DECISION")


def test_invalid_decision_reference_container_is_typed_error_before_lookup():
    records = complete_fixture().records
    by_kind(records, "decision")["data"]["consumed_message_refs"] = None
    expect_error(records, "INVALID_FIELD")
