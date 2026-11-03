"""Verify actual saved SUMO captures; never starts SUMO or substitutes trajectories."""
import json
import os
from pathlib import Path

import pytest

from riskprop.controller_evidence import EvidenceJournal
from riskprop.p7_evidence_verification import assess_smoke, verify_run


@pytest.fixture(scope="module")
def captures():
    value = os.environ.get("P7_ENGINEERING_CAPTURE")
    if not value:
        pytest.skip("set P7_ENGINEERING_CAPTURE to saved actual engineering output; no new SUMO allowed")
    root = Path(value)
    assert root.is_dir()
    results = {}
    for name in ("no_message", "disabled", "enabled"):
        r = root / "smoke" / name
        results[name] = {"root": r, "verification": verify_run(r, root / "captured_implementation_v1"),
            "summary": json.loads((r / "run_summary.json").read_text()),
            "trajectory": json.loads((r / "actual_trajectory.json").read_text()),
            "records": EvidenceJournal.from_dict(json.loads((r / "controller_evidence.json").read_text())).records}
    return results


@pytest.mark.parametrize("name", ["no_message", "disabled", "enabled"])
def test_actual_start_incarnation_continuity_exit_and_native_constraints(captures, name):
    c = captures[name]
    s, rows = c["summary"], c["trajectory"]
    assert s["target_entered"] and s["target_exited"]
    assert s["native_model"] == "Krauss" and s["native_speed_modes"] == [31]
    assert s["collision_count"] == s["teleport_count"] == 0
    assert s["native_following_below_vehicle_max_samples"] > 0
    assert s["native_without_traci_speed_max_abs_difference"] == 0
    entered_at = rows[0]["simulation_step"]
    assert [r["simulation_step"] for r in rows] == list(range(entered_at, entered_at + len(rows)))
    assert len({r["vehicle_incarnation_id"] for r in rows}) == 1
    assert rows[-1]["vehicle_existence"] is False and rows[-1]["speed_mps"] is None


def test_disabled_no_message_policy_and_physical_trajectory_equal(captures):
    a, b = captures["no_message"], captures["disabled"]
    keys = ("simulation_time_s", "simulation_step", "speed_mps", "acceleration_mps2", "position_xy_m", "vehicle_existence")
    assert [{k: r.get(k) for k in keys} for r in a["trajectory"]] == [{k: r.get(k) for k in keys} for r in b["trajectory"]]
    for c in (a, b):
        assert not [r for r in c["records"] if r["kind"] == "command"]
        assert all(r["data"]["consumed_message_refs"] == [] for r in c["records"] if r["kind"] == "decision")
    assert b["summary"]["counts_by_kind"]["validation"] > 0
    assert any(r["data"].get("reason") == "ADOPTION_DISABLED" for r in b["records"] if r["kind"] == "consumption")


def test_same_synthetic_message_enabled_actual_consumption_command_and_poststep(captures):
    b, c = captures["disabled"], captures["enabled"]
    assert b["summary"]["source_payload_hashes"] == c["summary"]["source_payload_hashes"]
    assert c["summary"]["policy_input_included"] == 52
    assert c["summary"]["counts_by_kind"]["command"] == 2
    assert c["summary"]["counts_by_kind"]["execution"] == 326
    for r in c["records"]:
        if r["kind"] == "consumption":
            assert r["data"]["adoption_boundary_status"] == "AGREED"
    assert c["summary"]["release_command_count"] == 1 and c["summary"]["first_release_time_s"] == 8
    released = [r for r in c["trajectory"] if r["vehicle_existence"] and r["simulation_time_s"] > 8]
    assert all(r["vehicle_max_speed_mps"] == 20 for r in released)


def test_all_record_types_applicable_handled_no_fabricated_safety_or_formal_risk(captures):
    c = captures["enabled"]
    assert len(c["summary"]["counts_by_kind"]) == 14
    assert {k for k, v in c["summary"]["counts_by_kind"].items() if v == 0} == {"safety"}
    assert c["summary"]["safety_layer_design_status"] == "NOT_INCLUDED_BY_RESEARCHER_DECISION"
    assert all(r["data"]["qualification_status"] == "UNKNOWN" for r in c["records"] if r["kind"] == "source")
    assert all(r["data"]["risk_status"] == "UNKNOWN" for r in c["records"] if r["kind"] == "risk_observation")


def test_enabled_warning_blocks_acceptance_and_preserves_original_false_pass(captures):
    result = captures["enabled"]["verification"]["smoke_acceptance"]
    assert result["capture_reported_status"] == "PASS"
    assert result["acceptance_status"] == "BLOCKED_ABNORMAL_BRAKING" and result["accepted"] is False
    assert result["emergency_braking_warning_count"] == 1
    assert result["observed_min_acceleration_mps2"] == pytest.approx(-9.0)
    assert result["new_sumo_runs_after_detection"] == 0
    assert captures["no_message"]["verification"]["smoke_acceptance"]["accepted"] is True
    assert captures["disabled"]["verification"]["smoke_acceptance"]["accepted"] is True
