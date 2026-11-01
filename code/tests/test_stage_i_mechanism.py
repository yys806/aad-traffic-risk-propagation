from __future__ import annotations

import pandas as pd
import pytest

from riskprop.stage_i_mechanism import (
    MechanismContractError,
    audit_four_cell_mechanism_fixture,
    build_engineering_fixture,
    build_joint_timeline,
    compare_paired_action,
    validate_event_timeline,
)


def test_engineering_fixture_reuses_four_cell_and_lifecycle_contracts():
    fixture = build_engineering_fixture()
    audit = audit_four_cell_mechanism_fixture(
        fixture["configs"], fixture["lifecycle"], fixture["pre_treatment"]
    )
    assert audit["four_cell"]["scientific_differences"] == [
        "source_present",
        "channel_enabled",
    ]
    assert all(item["lifecycle_pass"] for item in audit["lifecycle"].values())
    assert audit["pre_treatment"]["equivalence_pass"] is True
    assert audit["scientific_claim_eligible"] is False


def test_joint_timeline_preserves_unknown_physical_arrival():
    fixture = build_engineering_fixture()
    result = build_joint_timeline(
        message_events=fixture["message_events"],
        action_events=fixture["action_events"],
        risk_events=fixture["risk_events"],
        physical_arrival_time_s=None,
    )
    assert result["timeline_audit"]["timeline_pass"] is True
    assert result["time_comparison"]["information_before_physical"] == "Unknown"
    assert result["scientific_claim_eligible"] is False


def test_joint_timeline_can_compare_supplied_physical_arrival():
    fixture = build_engineering_fixture()
    result = build_joint_timeline(
        message_events=fixture["message_events"],
        action_events=fixture["action_events"],
        risk_events=fixture["risk_events"],
        physical_arrival_time_s=2.5,
    )
    assert result["time_comparison"]["information_before_physical"] is True
    assert result["time_comparison"]["action_before_physical"] is True


def test_action_change_requires_common_observations():
    result = compare_paired_action(
        pd.DataFrame({"time_s": [0.0], "vehicle_id": ["a"], "speed_mps": [1.0]}),
        pd.DataFrame({"time_s": [1.0], "vehicle_id": ["a"], "speed_mps": [1.0]}),
        treatment_start_s=0.5,
        speed_tolerance_mps=0.1,
        sustain_s=0.5,
    )
    assert result["status"] == "unknown_no_common_observations"


def test_event_timeline_rejects_non_monotone_order():
    fixture = build_engineering_fixture()
    bad = pd.concat(
        [fixture["message_events"].iloc[[1]], fixture["message_events"].iloc[[0]]],
        ignore_index=True,
    )
    with pytest.raises(MechanismContractError, match="non-decreasing"):
        validate_event_timeline(bad)
