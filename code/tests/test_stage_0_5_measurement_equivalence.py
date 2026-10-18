"""Stage 0.5.4-A measurement-equivalence and calibration-readiness tests.

The equivalence matrix is exercised case by case so that a single failing boundary case
cannot be hidden by an aggregate count.  The readiness tests only touch synthetic data or
the guard's policy layer; the real calibration windows are never read here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from riskprop.stage_0_5_sumo import (
    CALIBRATION_VALIDATION_POLICY,
    EQUIVALENCE_VERDICTS,
    Stage05AccessDenied,
    build_sumo_p2_events,
    compute_exposure,
    compute_sumo_measurements,
    extract_sumo_formal_p2_events,
    measurement_equivalence_matrix,
    p2_boundary_cases,
    run_p2_boundary_matrix,
)
from riskprop.stage_0_5_sumo import CalibrationValidationGuard
from riskprop.stage_0_5_calibration_readiness import (
    ADMISSION_STATUSES,
    CALIBRATION_GROUPS,
    READINESS_RESULT_ID,
    VALIDATION_GROUPS,
    CalibrationReadinessError,
    candidate_strata,
    clustered_uncertainty,
    demand_identifiability,
    load_formal_events,
    load_timestep_sensitivity,
    parameter_identifiability,
    researcher_decision_matrix,
    scientific_admission_status,
    stage_0_5_4b_admission_checklist,
    time_step_options,
    window_summary,
)
from riskprop.stage_0_5_sumo import _synthetic_states  # noqa: PLC2701 - test uses the audit fixture builder

CASES = p2_boundary_cases()
CASE_IDS = sorted(CASES)


def _case_frame(name: str) -> tuple[pd.DataFrame, float]:
    case = CASES[name]
    cadence = float(case.get("cadence_s", 0.1))
    rows = [{"time_s": time_s, **spec} for time_s, spec in zip(case["times"], case["specs"])]
    if "incarnation_switch_at" in case:
        switch = int(case["incarnation_switch_at"])
        for position, row in enumerate(rows):
            if position >= switch:
                row["incarnation_id"] = "run|f|1"
    return _synthetic_states(rows), cadence


# --------------------------------------------------------------------------------------
# A3: boundary test matrix, one test per case
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("case_name", CASE_IDS)
def test_boundary_case_matches_the_declared_expectation(case_name: str) -> None:
    frame, cadence = _case_frame(case_name)
    measured = compute_sumo_measurements(frame)
    native, _ = build_sumo_p2_events(measured, recorded_observation_step_s=cadence)
    formal, _ = extract_sumo_formal_p2_events(
        measured, recorded_observation_step_s=cadence, allow_nonstandard_cadence=True
    )
    case = CASES[case_name]
    assert len(native) == case["expected_native_events"], case_name
    assert len(formal) == case["expected_formal_events"], case_name


@pytest.mark.parametrize("case_name", CASE_IDS)
def test_boundary_case_adapters_agree_on_identity_and_confirmation(case_name: str) -> None:
    frame, cadence = _case_frame(case_name)
    measured = compute_sumo_measurements(frame)
    native, _ = build_sumo_p2_events(measured, recorded_observation_step_s=cadence)
    formal, _ = extract_sumo_formal_p2_events(
        measured, recorded_observation_step_s=cadence, allow_nonstandard_cadence=True
    )
    if CASES[case_name].get("cadence_s", 0.1) != 0.1:
        # a coarse recording may never be presented as 100 ms formal evidence
        assert formal.empty
        return
    assert len(native) == len(formal)
    if not len(native):
        return
    left = native.sort_values("event_start_s").reset_index(drop=True)
    right = formal.sort_values("event_start_s").reset_index(drop=True)
    for index in range(len(left)):
        for column in ("event_start_s", "event_end_s", "event_confirm_s", "ttc_min_s"):
            assert left.iloc[index][column] == pytest.approx(right.iloc[index][column])
        assert str(left.iloc[index]["vehicle_id"]) == str(right.iloc[index]["vehicle_id"])
        assert str(left.iloc[index]["leader_id"]) == str(right.iloc[index]["leader_id"])
        assert str(left.iloc[index]["exit_reason"]) == str(right.iloc[index]["exit_reason"])


def test_boundary_matrix_reports_the_full_matrix() -> None:
    results = run_p2_boundary_matrix()
    assert len(results) == len(CASES)
    for row in results:
        assert row["case_matches_expectation"] is True, row["case"]
    by_case = {row["case"]: row for row in results}
    assert by_case["leader_switch"]["no_bridging_verified"] is True
    assert by_case["incarnation_change"]["no_bridging_verified"] is True
    assert by_case["coarse_cadence_0_2"]["formal_equivalence_status"].endswith("nonstandard_cadence")
    assert by_case["right_censored_end"]["exit_reason_matches_expectation"] is True


def test_equivalence_matrix_never_promotes_a_dimension_from_a_count_alone() -> None:
    matrix = measurement_equivalence_matrix()
    assert matrix["boundary_cases_all_as_expected"] is True
    assert matrix["blocking_items"] == []
    assert matrix["overall_status"] == "pending_measurement_equivalence_review"
    assert set(matrix["verdict_counts"]) <= set(EQUIVALENCE_VERDICTS)
    documented = {row["dimension"] for row in matrix["rows"]}
    for required in (
        "vehicle_identity",
        "leader_identity",
        "net_gap",
        "closing_speed",
        "ttc_units_and_rule",
        "p2_threshold",
        "minimum_duration",
        "time_continuity",
        "time_origin",
        "event_confirmation",
        "event_exit_reason",
        "measurement_status_vocabulary",
        "evaluable_exposure",
        "event_rate",
        "drac",
        "coarse_recording",
    ):
        assert required in documented, required
    for row in matrix["rows"]:
        assert row["verdict"] in EQUIVALENCE_VERDICTS
        assert isinstance(row["blocking"], bool)
        assert row["evidence"], row["dimension"]


def test_exposure_layers_reproduce_the_approved_edge_rule() -> None:
    """reliable_following - not_evaluable = p2_evaluable, and closing is link-based."""

    frame = _synthetic_states(
        [
            {"time_s": 0.0, "leader_id": "l", "leader_speed_mps": 11.4, "net_gap_m": 1.0},
            {"time_s": 0.1, "leader_id": "l", "leader_speed_mps": 11.4, "net_gap_m": 1.0},
            {"time_s": 0.2, "leader_id": "l", "leader_speed_mps": 11.4, "net_gap_m": -1.0},
        ]
    )
    exposure = compute_exposure(compute_sumo_measurements(frame), recorded_observation_step_s=0.1)
    assert exposure["reliable_following_exposure_s"] == pytest.approx(0.2)
    assert exposure["not_evaluable_following_exposure_s"] == pytest.approx(0.1)
    assert exposure["p2_evaluable_following_exposure_s"] == pytest.approx(0.1)
    assert exposure["reliable_following_exposure_s"] - exposure["not_evaluable_following_exposure_s"] == pytest.approx(
        exposure["p2_evaluable_following_exposure_s"]
    )
    assert exposure["reliable_closing_exposure_s"] == pytest.approx(0.1)
    assert "time_delta_equals_cadence" in exposure["adjacency_checks_applied"]


def test_readiness_window_summary_reproduces_the_published_exposure_rule() -> None:
    """A synthetic frame exercises the same edge audit that reproduces the sealed numbers."""

    rows = []
    for index in range(4):
        rows.append({"time_s": round(0.1 * index, 10), "leader_id": "l", "leader_speed_mps": 11.4, "net_gap_m": 2.0})
    frame = _synthetic_states(rows)
    frame["dataset"] = "NGSIM"
    frame["site"] = "US-101"
    frame["window_id"] = "0750_0805"
    frame["source_member"] = "synthetic"
    frame["source_period"] = "synthetic"
    frame["identity_uncertain"] = False
    frame["leader_identity_uncertain"] = False
    frame["identity_break"] = False
    frame["observation_gap"] = False
    frame["diagnostic_clock_anchor_ms"] = 0
    frame["leader_matched"] = frame["leader_id"].notna()
    frame["leader_trajectory_id"] = frame["leader_incarnation_id"]
    frame["global_time_ms"] = (pd.to_numeric(frame["time_s"]) * 1000).round().astype("int64")
    frame["frame_id"] = frame.groupby("trajectory_id").cumcount()
    frame["source_group"] = "us101__0750_0805"
    frame["x_m"] = 1.0
    frame["y_m"] = 200.0 + pd.to_numeric(frame["time_s"]) * 10.0
    measured = compute_sumo_measurements(frame)
    measured["measurement_status"] = "valid"
    summary = window_summary(measured)
    assert summary["exposure"]["reliable_following_exposure_s"] == pytest.approx(0.3)
    assert summary["exposure"]["p2_evaluable_following_exposure_s"] == pytest.approx(0.3)
    assert summary["exposure"]["not_evaluable_following_exposure_s"] == pytest.approx(0.0)
    assert summary["exposure"]["reliable_closing_exposure_s"] == pytest.approx(0.3)
    assert summary["source_group"] == "us101__0750_0805"


# --------------------------------------------------------------------------------------
# A2: time and frame mapping
# --------------------------------------------------------------------------------------


def test_formal_frame_clock_is_absolute_and_leader_frame_is_resolved() -> None:
    frame, _ = _case_frame("late_entry_absolute_clock")
    measured = compute_sumo_measurements(frame)
    from riskprop.stage_0_5_sumo import build_sumo_formal_source_frame

    formal = build_sumo_formal_source_frame(measured, recorded_observation_step_s=0.1)
    follower = formal.loc[formal.vehicle_id == "f"].sort_values("time_s")
    assert follower["global_time_ms"].tolist() == [30000, 30100, 30200, 30300, 30400, 30500]
    assert follower["observation_index"].tolist() == [0, 1, 2, 3, 4, 5]
    assert follower["frame_id"].tolist() == follower["observation_index"].tolist()
    assert follower["leader_frame_id"].tolist() == follower["observation_index"].tolist()
    assert follower["global_time_ms"].diff().dropna().eq(100).all()


def test_missing_leader_row_fails_closed_in_the_formal_adapter() -> None:
    frame, _ = _case_frame("normal_sustained_closing")
    without_leader = frame[frame["vehicle_id"] == "f"].copy()
    measured = compute_sumo_measurements(without_leader)
    formal, audit = extract_sumo_formal_p2_events(measured, recorded_observation_step_s=0.1)
    assert formal.empty
    assert audit["reliable_candidate_events"] == 0


# --------------------------------------------------------------------------------------
# Guard behaviour: fail-closed access and row scoping
# --------------------------------------------------------------------------------------


def test_guard_denies_row_scoped_reads_outside_the_calibration_windows(tmp_path: Path) -> None:
    events = pd.DataFrame(
        {
            "source": ["us101__0750_0805", "us101__0805_0820", "us101__0820_0835", "lankershim__complete"],
            "event_id": ["a", "b", "c", "d"],
        }
    )
    path = tmp_path / "p2_formal_events.parquet"
    events.to_parquet(path, index=False)
    guard = CalibrationValidationGuard()
    # the parquet file is not the approved one, so the SHA check fires before the scope check
    with pytest.raises(Stage05AccessDenied):
        guard.require_row_scoped_read(
            path,
            source="p2_formal_events",
            allowed_values=["us101__0750_0805"],
            column="source",
        )
    with pytest.raises(Stage05AccessDenied, match="exceeds the policy"):
        guard.require_row_scoped_read(
            path,
            source="p2_formal_events",
            allowed_values=list(VALIDATION_GROUPS),
            column="source",
        )
    with pytest.raises(Stage05AccessDenied, match="unknown|not declared"):
        guard.require_row_scoped_read(
            path,
            source="not_a_source",
            allowed_values=["us101__0750_0805"],
            column="source",
        )
    assert CALIBRATION_VALIDATION_POLICY["calibration_row_scoped_sources"]["p2_formal_events"][
        "allowed_values"
    ] == list(CALIBRATION_GROUPS)


def test_calibration_states_read_helper_refuses_a_foreign_window(tmp_path: Path) -> None:
    frame = pd.DataFrame({"window_id": ["0820_0835"]})
    path = tmp_path / "state.parquet"
    frame.to_parquet(path, index=False)
    guard = CalibrationValidationGuard()
    with pytest.raises(Stage05AccessDenied):
        guard.require_source_read(path, role="calibration", source="us101__0750_0805")


def test_formal_event_reader_rejects_non_calibration_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader must fail closed if a read ever returns a validation-window row."""

    class _FakeGuard:
        def require_row_scoped_read(self, *args: object, **kwargs: object):
            return pd.DataFrame({"source": ["us101__0820_0835"]}), {"rows": 1}

    with pytest.raises(CalibrationReadinessError, match="escaped the calibration windows"):
        load_formal_events(Path("."), _FakeGuard())  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# readiness protocol candidates
# --------------------------------------------------------------------------------------


def _summary_fixture(group: str = "us101__0750_0805") -> dict:
    return {
        "source_group": group,
        "state_rows": 10,
        "vehicles": 2,
        "trajectory_clusters": 2,
        "observation_window_s": 0.9,
        "kinematics": {
            "speed_mps": {"mean": 12.0, "sd": 1.0, "p05": 8.0, "median": 12.0, "p85": 14.0, "p95": 15.0, "max": 16.0},
            "acceleration_mps2": {"mean": 0.0, "sd": 0.5, "p05": -1.0, "median": 0.0, "p95": 1.0, "min": -2.0, "max": 2.0},
            "low_speed_fractions": {"below_1_mps": 0.0, "below_2_mps": 0.0, "below_5_mps": 0.1},
        },
        "following": {
            "median_net_gap_m": 10.0,
            "p10_net_gap_m": 3.0,
            "p90_net_gap_m": 40.0,
            "mean_closing_speed_mps": 0.1,
            "positive_closing_share_of_states": 0.4,
            "ttc_valid_rows": 4,
            "ttc_valid_share_of_states": 0.4,
            "ttc_valid_median_s": 10.0,
            "ttc_valid_p05_s": 2.0,
            "ttc_valid_min_s": 1.5,
            "drac_p95_mps2": 1.0,
        },
        "observability": {
            "measurement_status_counts": {"valid": 4, "not_applicable": 4, "missing": 1, "invalid": 1},
            "measurement_status_shares": {"valid": 0.4, "not_applicable": 0.4, "missing": 0.1, "invalid": 0.1},
            "missing_reason_counts": {"non_closing": 4, "no_reported_leader": 1, "non_positive_gap": 1},
            "identity_defect_rows": 1,
            "diagnostic_clock_missing_rows": 0,
        },
        "exposure": {
            "reliable_following_exposure_s": 0.6,
            "p2_evaluable_following_exposure_s": 0.5,
            "not_evaluable_following_exposure_s": 0.1,
            "reliable_closing_exposure_s": 0.3,
        },
        "p2": {
            "events": 1,
            "event_rate_per_vehicle_hour": 7200.0,
            "duration_s": {"median": 0.2, "p90": 0.3, "max": 0.3},
            "ttc_min_s": {"median": 1.5, "p05": 1.5, "min": 1.5},
            "exit_reason_counts": {"observed_threshold_exit": 1},
        },
        "per_vehicle": {
            "evaluable_exposure_s": {f"t{index}": 0.25 for index in range(2)},
            "following_edges": {f"t{index}": 3.0 for index in range(2)},
            "event_counts": {"t0": 1},
            "speed_sums": {f"t{index}": 12.0 for index in range(2)},
            "speed_counts": {f"t{index}": 5 for index in range(2)},
            "acceleration_sums": {f"t{index}": 0.0 for index in range(2)},
        },
    }


def test_clustered_uncertainty_uses_vehicle_clusters_and_flags_iid() -> None:
    report = clustered_uncertainty({"us101__0750_0805": _summary_fixture()}, resamples=200, seed=1)
    source = report["sources"][0]
    assert source["clusters"] == 2
    assert source["p2_event_rate_per_vehicle_hour"]["point"] == pytest.approx(7200.0)
    assert "lower_95" in source["mean_speed_mps"]
    assert report["cluster_unit"].startswith("trajectory")
    assert report["usable_for_tolerance"] is False
    assert "not a permissible SUMO model-deviation tolerance" in report["reason"]


def test_parameter_identifiability_marks_unidentifiable_items() -> None:
    table = parameter_identifiability()
    classes = {row["parameter"]: row["class"] for row in table["rows"]}
    assert classes["tau"] == "constrained_by_current_data"
    assert classes["emergencyDecel"] == "not_identifiable_must_be_fixed"
    assert classes["vehicle_class_mix"] == "not_identifiable_from_approved_reference"
    assert table["rule"].endswith("fully calibrated driver behaviour")


def test_time_step_options_recommend_recorded_100ms_and_keep_warmup_open() -> None:
    sensitivity = {
        "available": True,
        "comparisons": [
            {
                "fixture_id": "measurement_probe_queue_stop",
                "events_match_all_three": True,
                "convergence_A_to_B_start_s": 0.2,
                "convergence_B_to_C_start_s": 0.2,
            }
        ],
        "cost_benchmark": [{"configuration_id": "A_uniform_0.1", "wall_clock_s": 24.2}],
    }
    options = time_step_options(sensitivity)
    assert options["recommendation"] == "B_fine_internal_0.05"
    assert "warmup_s" in options["unapproved_numbers"]
    assert options["measured_boundary_shift_s"]["measurement_probe_queue_stop"]["start_shift_A_to_B_s"] == 0.2
    assert options["measured_cost"][0]["wall_clock_s"] == 24.2
    assert all(option["recorded_observation_step_s"] == 0.1 for option in options["options"])


def test_missing_sensitivity_package_is_reported_not_invented(tmp_path: Path) -> None:
    payload = load_timestep_sensitivity(tmp_path)
    assert payload["available"] is False
    assert "not produced" in payload["reason"]


def test_admission_checklist_blocks_everything_until_approved() -> None:
    matrix = measurement_equivalence_matrix()
    summaries = {"us101__0750_0805": _summary_fixture()}
    checklist = stage_0_5_4b_admission_checklist(matrix, summaries, {"cost_benchmark": []})
    assert checklist["ready_to_start_stage_0_5_4b"] is False
    assert len(checklist["items"]) == 10
    for item in checklist["items"]:
        assert item["status"] in ADMISSION_STATUSES
        assert item["required_action"]
    assert "vehicle_type_plan_approval" in checklist["blocking_items"]
    admission = scientific_admission_status(matrix, checklist)
    assert admission["engineering_ready"] is True
    assert admission["calibration_ready"] is False
    assert admission["reality_coverage_accepted"] is False
    assert admission["stage_0_5_gate"] == "pending_simulation_sample"


def test_researcher_decision_matrix_covers_every_required_field() -> None:
    matrix = researcher_decision_matrix()
    assert len(matrix["decisions"]) == 7
    for decision in matrix["decisions"]:
        assert decision["verified_facts"]
        assert decision["recommended"]
        assert decision["alternatives"]
        assert decision["scientific_reason"]
        assert decision["main_risk"]
        assert decision["missing_evidence"] is not None
        assert isinstance(decision["ready_for_approval"], bool)
    pending = [d["decision"] for d in matrix["decisions"] if not d["ready_for_approval"]]
    assert pending == ["6_scientific_tolerance", "7_calibration_experiment"]


def test_demand_identifiability_refuses_row_counts_as_flow() -> None:
    rows = []
    for vehicle in range(4):
        for step in range(6):
            rows.append(
                {
                    "time_s": round(0.1 * step, 10),
                    "leader_id": "l",
                    "leader_speed_mps": 11.4,
                    "net_gap_m": 5.0,
                    "vehicle_id": f"v{vehicle}",
                }
            )
    frame = _synthetic_states(rows)
    frame["x_m"] = 1.0
    frame["y_m"] = pd.to_numeric(frame["time_s"]) * 10.0
    table = demand_identifiability(compute_sumo_measurements(frame))
    quantities = {row["quantity"]: row["identifiability"] for row in table["rows"]}
    assert quantities["state_row_count_as_flow"] == "not_identifiable"
    assert quantities["interior_cross_section_passage_rate_veh_per_h"] == "directly_measurable"
    assert quantities["vehicle_class_composition"] == "not_identifiable"
    assert table["prohibited_shortcuts"]


def test_candidate_strata_are_data_derived_and_exclude_partial_slices() -> None:
    rows = []
    for vehicle in range(3):
        for step in range(700):
            rows.append(
                {
                    "time_s": round(0.1 * step, 10),
                    "leader_id": "l",
                    "leader_speed_mps": 11.4,
                    "net_gap_m": 5.0,
                    "vehicle_id": f"v{vehicle}",
                }
            )
    frame = _synthetic_states(rows)
    frame["x_m"] = 1.0
    frame["y_m"] = 200.0 + (pd.to_numeric(frame["time_s"]) % 50.0)
    strata = candidate_strata(compute_sumo_measurements(frame))
    assert strata["slice_s"] == 60.0
    assert strata["validation_window_used"] is False
    assert strata["status"].startswith("candidate_thresholds")
    assert strata["density_thresholds_per_km"]["lower_tercile"] <= strata["density_thresholds_per_km"]["upper_tercile"]


def test_readiness_result_id_and_gate_are_unchanged() -> None:
    assert READINESS_RESULT_ID == "RES-STAGE-0.5-CALIBRATION-READINESS-V1"
    assert CALIBRATION_GROUPS == ("us101__0750_0805", "us101__0805_0820")
    assert VALIDATION_GROUPS == ("us101__0820_0835",)
    evidence = Path(__file__).resolve().parents[2] / "evidence/results" / READINESS_RESULT_ID
    if evidence.is_dir():
        audit = json.loads((evidence / "audit.json").read_text(encoding="utf-8"))
        assert audit["stage_0_5_gate"] == "pending_simulation_sample"
        assert audit["scientific_claim_eligible"] is False
        assert audit["locked_holdout_accessed"] is False
        assert audit["validation_window_read"] is False
        assert audit["validation_window_rows_materialised"] == 0
        assert audit["ready_to_start_stage_0_5_4b"] is False
