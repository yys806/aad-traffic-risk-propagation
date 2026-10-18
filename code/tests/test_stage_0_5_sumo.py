"""Stage 0.5 no-message SUMO baseline engineering tests.

The deterministic analytical tests always run.  The SUMO integration tests are
skipped (never faked) when ``sumo``/``netconvert`` are unavailable, and every
integration artifact is asserted to stay ``engineering_only``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import warnings

import pandas as pd
import pytest

from riskprop.stage_0_5_sumo import (
    CALIBRATION_VALIDATION_POLICY,
    CANDIDATE_SCENARIO_CONFIGS,
    CLOSING_SPEED_SEMANTICS,
    EQUIVALENCE_VERDICTS,
    MISSING_REASON_EQUIVALENCE,
    NGSIM_CLOSING_EPSILON_MPS,
    NGSIM_STATUS_CROSSWALK,
    CLOSING_SPEED_SEMANTICS,
    ENGINEERING_FIXTURE_VTYPES,
    FORMAL_OBSERVATION_STEP_S,
    NETWORK_DESIGN_CANDIDATE,
    NET_GAP_SEMANTICS,
    PNEUMA_RAW_VEHICLE_TYPES,
    RESULT_ID,
    SCENARIO_MANIFEST,
    Stage05AccessDenied,
    Stage05EngineeringError,
    VehicleIdentityTracker,
    build_sumo_formal_source_frame,
    build_sumo_p2_events,
    cadence_max_gap_s,
    compute_exposure,
    measurement_equivalence_matrix,
    p2_boundary_cases,
    compute_sumo_measurements,
    extract_sumo_formal_p2_events,
    measurement_support_matrix,
    run_stage_0_5_no_message_baseline,
    to_canonical_real_state,
    validate_demand_config,
    validate_no_message_config,
    validate_observation_cadence,
    validate_parameter_classification,
    validate_scenario_candidate_config,
    validate_scenario_manifest,
    validate_vehicle_type_mapping,
    vehicle_type_mapping_candidate,
)
from riskprop.calibration import validate_real_state_table

SUMO_AVAILABLE = shutil.which("sumo") is not None and shutil.which("netconvert") is not None
requires_sumo = pytest.mark.skipif(
    not SUMO_AVAILABLE, reason="SUMO/netconvert not available in this environment"
)
REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------


def _states(rows: list[dict]) -> pd.DataFrame:
    defaults = {
        "run_id": "fixture_run",
        "scenario_id": "us101_highway_baseline",
        "fixture_id": "analytical_fixture",
        "experiment_mode": "no_message_baseline",
        "configured_seed": 7,
        "edge_id": "main_0",
        "lane_id": "main_0_0",
        "simulation_step": 0,
        "longitudinal_position_m": 0.0,
        "trajectory_id": None,
        "incarnation_id": None,
        "leader_speed_mps": None,
        "leader_incarnation_id": None,
        "leader_identity_status": "observed",
    }
    frame = pd.DataFrame([{**defaults, **row} for row in rows])
    frame["trajectory_id"] = frame["trajectory_id"].fillna(frame["vehicle_id"].astype(str))
    frame["incarnation_id"] = frame["incarnation_id"].fillna("run|" + frame["vehicle_id"].astype(str) + "|0")
    resolved_leader = frame["leader_id"].astype("string")
    frame["leader_incarnation_id"] = frame["leader_incarnation_id"].fillna(
        pd.Series("run|" + resolved_leader + "|0", index=frame.index).where(resolved_leader.notna())
    )
    if "observation_index" not in frame.columns:
        frame["observation_index"] = frame.groupby("incarnation_id").cumcount()
    # the runner records every active vehicle at every step, so a leader referenced by a
    # follower also has its own observation row; leader_frame_id resolution depends on it
    present = set(zip(frame["vehicle_id"].astype(str), frame["time_s"].astype(float)))
    extras = []
    for row in frame.to_dict("records"):
        leader_id = row.get("leader_id")
        if leader_id is None or pd.isna(leader_id):
            continue
        key = (str(leader_id), float(row["time_s"]))
        if key in present:
            continue
        present.add(key)
        extras.append(
            {
                **defaults,
                "time_s": float(row["time_s"]),
                "observation_index": row.get("observation_index", 0),
                "simulation_step": row.get("simulation_step", 0),
                "vehicle_id": str(leader_id),
                "trajectory_id": f"run|{leader_id}|0",
                "incarnation_id": f"run|{leader_id}|0",
                "speed_mps": row.get("leader_speed_mps") if row.get("leader_speed_mps") is not None else 0.0,
                "leader_id": None,
                "leader_incarnation_id": None,
                "leader_identity_status": "not_applicable",
                "leader_speed_mps": None,
                "net_gap_m": None,
            }
        )
    if extras:
        with warnings.catch_warnings():
            # leader rows legitimately carry all-NA leader columns
            warnings.simplefilter("ignore", FutureWarning)
            frame = pd.concat([frame, pd.DataFrame(extras)], ignore_index=True)
    return frame


def _following_rows(
    *,
    times: list[float],
    leader_ids: list[str | None] | None = None,
    gaps: list[float] | None = None,
    follower_speed: float = 12.0,
    leader_speed: float = 11.4,
    vehicle_id: str = "f",
) -> pd.DataFrame:
    leader_ids = leader_ids or ["l"] * len(times)
    gaps = gaps or [10.0] * len(times)
    return _states(
        [
            {
                "time_s": time_s,
                "simulation_step": index,
                "vehicle_id": vehicle_id,
                "speed_mps": follower_speed,
                "acceleration_mps2": 0.0,
                "leader_id": leader_id,
                "leader_speed_mps": None if leader_id is None else leader_speed,
                "net_gap_m": None if leader_id is None else gap,
            }
            for index, (time_s, leader_id, gap) in enumerate(zip(times, leader_ids, gaps))
        ]
    )


def _verify_sha256sums(package: Path) -> None:
    lines = [line for line in (package / "SHA256SUMS").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines, "SHA256SUMS must not be empty"
    for line in lines:
        digest, name = line.split("  ", 1)
        actual = hashlib.sha256((package / name).read_bytes()).hexdigest()
        assert actual == digest, f"SHA mismatch for {name}"
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["result_id"] == RESULT_ID


# --------------------------------------------------------------------------------------
# scenario architecture and configuration contracts
# --------------------------------------------------------------------------------------


def test_three_scenarios_keep_separate_roles_and_reference_binding() -> None:
    assert set(SCENARIO_MANIFEST) == {
        "us101_highway_baseline",
        "lankershim_urban_auxiliary",
        "pneuma_urban_kinematics",
    }
    assert SCENARIO_MANIFEST["us101_highway_baseline"]["role"] == "highway_following_risk_primary"
    assert SCENARIO_MANIFEST["lankershim_urban_auxiliary"]["role"] == "urban_following_risk_auxiliary"
    assert SCENARIO_MANIFEST["pneuma_urban_kinematics"]["role"] == "urban_kinematics_only"
    validate_scenario_manifest()
    for entry in SCENARIO_MANIFEST.values():
        assert entry["reference_source"]["result_id"] == "RES-STAGE-0.5-REAL-REF-R2"
        assert entry["scientific_parameter_status"]
    assert set(SCENARIO_MANIFEST["pneuma_urban_kinematics"]["forbidden_scope"]) == {
        "ttc", "drac", "leader", "p2", "risk_events"
    }


def test_candidate_auxiliary_scenarios_are_explicitly_unbuilt() -> None:
    assert set(CANDIDATE_SCENARIO_CONFIGS) == {"lankershim_urban_auxiliary", "pneuma_urban_kinematics"}
    for config in CANDIDATE_SCENARIO_CONFIGS.values():
        validate_scenario_candidate_config(config)
        assert config["build_status"] == "not_built"
        assert config["network"]["spec"] is None
        assert config["blocking_decisions"]
    broken = json.loads(json.dumps(CANDIDATE_SCENARIO_CONFIGS["lankershim_urban_auxiliary"]))
    broken["network"]["spec"] = {"lanes": 2}
    with pytest.raises(Stage05EngineeringError, match="must not pre-empt"):
        validate_scenario_candidate_config(broken)
    broken = json.loads(json.dumps(CANDIDATE_SCENARIO_CONFIGS["lankershim_urban_auxiliary"]))
    broken["blocking_decisions"] = []
    with pytest.raises(Stage05EngineeringError, match="blocking decisions"):
        validate_scenario_candidate_config(broken)


def test_network_candidate_is_generic_and_awaits_approval() -> None:
    spec = NETWORK_DESIGN_CANDIDATE
    assert spec["classification"] == "generic_highway_candidate"
    assert spec["claim"] == "not_us101_geometry"
    assert not any("us101" in str(value).lower() for value in spec["supports"])
    assert spec["routes"]["mainline"] == ["main_0", "main_1", "main_2"]
    assert spec["routes"]["entering"][0] == "onramp"
    assert spec["routes"]["exiting"][-1] == "offramp"
    for entry in spec["approval_table"]:
        assert entry["status"] == "pending_scientific"
        assert entry["basis"]
    assert {edge["lanes"] for edge in spec["edges"] if edge["id"].startswith("main")} == {3}


def test_vehicle_type_mapping_reports_gaps_and_never_silently_maps() -> None:
    mapping = vehicle_type_mapping_candidate()
    validate_vehicle_type_mapping(mapping)
    assert mapping["scientific_mapping_approved"] is False
    assert set(mapping["mapping_gaps"]) == set(PNEUMA_RAW_VEHICLE_TYPES)
    for raw, entry in mapping["real_reference_raw_types"].items():
        assert entry["mapping_status"] == "unmapped"
        assert entry["sumo_vtype"] is None
    for name, entry in mapping["engineering_fixtures"].items():
        assert entry["mapping_status"] == "engineering_fixture_only"
        assert name in ENGINEERING_FIXTURE_VTYPES
    for broken in (
        {**mapping, "scientific_mapping_approved": True},
        {**mapping, "mapping_gaps": []},
    ):
        with pytest.raises(Stage05EngineeringError):
            validate_vehicle_type_mapping(broken)
    silently_mapped = json.loads(json.dumps(mapping))
    silently_mapped["real_reference_raw_types"]["Bus"]["sumo_vtype"] = "engineering_car"
    with pytest.raises(Stage05EngineeringError, match="unmapped"):
        validate_vehicle_type_mapping(silently_mapped)


def test_parameter_classification_rejects_overclaiming() -> None:
    validate_parameter_classification({"network": "engineering_fixture_only", "tolerances": "pending_scientific"})
    with pytest.raises(Stage05EngineeringError, match="unknown parameter classes"):
        validate_parameter_classification({"network": "approved"})
    with pytest.raises(Stage05EngineeringError, match="no researcher-approved"):
        validate_parameter_classification({"network": "researcher_approved_scientific"})


def test_no_message_config_fails_closed_on_communication_or_treatment() -> None:
    valid = {
        "experiment_mode": "no_message_baseline",
        "communication_enabled": False,
        "source_risk_treatment_enabled": False,
        "information_adoption_enabled": False,
    }
    validate_no_message_config(valid)
    for key in valid:
        if key == "experiment_mode":
            continue
        with pytest.raises(Stage05EngineeringError, match="no_message_baseline"):
            validate_no_message_config({**valid, key: True})
    with pytest.raises(Stage05EngineeringError, match="no_message_baseline"):
        validate_no_message_config({**valid, "experiment_mode": "message_treatment"})


def test_demand_config_rejects_validation_derived_or_unapproved_levels() -> None:
    base = {
        "schema_version": "stage_0_5.demand.v1",
        "mode": "explicit_departures_fixture",
        "demand_status": "engineering_fixture_only",
        "derived_from": [],
        "vehicle_count": 12,
        "depart_interval_s": 3.0,
        "lane_composition": {"main_0": 3},
        "vehicle_type_mix": {"engineering_car": 1.0},
        "seeds": [7],
    }
    validate_demand_config(base)
    with pytest.raises(Stage05EngineeringError, match="reverse-engineered"):
        validate_demand_config({**base, "derived_from": ["us101__0820_0835"]})
    with pytest.raises(Stage05EngineeringError, match="no approved scientific demand"):
        validate_demand_config({**base, "demand_status": "researcher_approved_scientific"})
    with pytest.raises(Stage05EngineeringError, match="lane composition"):
        validate_demand_config({**base, "lane_composition": {}})
    with pytest.raises(Stage05EngineeringError, match="sum to 1.0"):
        validate_demand_config({**base, "vehicle_type_mix": {"engineering_car": 0.5}})


# --------------------------------------------------------------------------------------
# kinematic and measurement semantics
# --------------------------------------------------------------------------------------


def test_semantics_constants_are_unified_and_explicit() -> None:
    assert CLOSING_SPEED_SEMANTICS["definition"] == "closing_speed_mps = follower_speed_mps - leader_speed_mps"
    assert NET_GAP_SEMANTICS["physical_net_gap_rule"] == "net_gap_m = leader_traci_distance_m + follower_min_gap_m"
    assert NET_GAP_SEMANTICS["verified"] is True


def test_closing_speed_is_follower_minus_leader_and_ttc_is_gap_over_closing() -> None:
    measured = compute_sumo_measurements(
        _states(
            [
                {
                    "time_s": 0.1,
                    "simulation_step": 1,
                    "vehicle_id": "follower",
                    "speed_mps": 12.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "leader",
                    "leader_speed_mps": 10.0,
                    "net_gap_m": 10.0,
                }
            ]
        )
    )
    row = measured.iloc[0]
    assert row["closing_speed_mps"] == pytest.approx(2.0)
    assert row["ttc_s"] == pytest.approx(5.0)
    assert bool(row["ttc_valid"])
    assert row["measurement_status"] == "valid"
    assert row["following_status"] == "following_closing"
    assert bool(row["p2_evaluable_eligible"])


def test_slower_follower_never_produces_a_finite_closing_ttc() -> None:
    measured = compute_sumo_measurements(
        _states(
            [
                {
                    "time_s": 0.1,
                    "simulation_step": 1,
                    "vehicle_id": "follower",
                    "speed_mps": 10.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "leader",
                    "leader_speed_mps": 12.0,
                    "net_gap_m": 10.0,
                },
                {
                    "time_s": 0.1,
                    "simulation_step": 1,
                    "vehicle_id": "equal",
                    "speed_mps": 10.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "leader2",
                    "leader_speed_mps": 10.0,
                    "net_gap_m": 10.0,
                },
            ]
        )
    )
    followers = measured[measured.vehicle_id.isin(["follower", "equal"])]
    assert len(followers) == 2
    for _, row in followers.iterrows():
        assert not bool(row["ttc_valid"])
        assert pd.isna(row["ttc_s"])
        assert row["missing_reason"] == "non_closing"
        assert row["measurement_status"] == "not_applicable"
        # a reliable positive-gap following state still counts as P2-evaluable exposure
        assert bool(row["p2_evaluable_eligible"])
        assert row["closing_speed_mps"] <= 0
    assert measured.loc[measured.vehicle_id == "follower", "closing_speed_mps"].iloc[0] == pytest.approx(-2.0)
    assert measured.loc[measured.vehicle_id == "equal", "closing_speed_mps"].iloc[0] == pytest.approx(0.0)


def test_missing_leader_is_not_treated_as_zero_risk() -> None:
    measured = compute_sumo_measurements(_following_rows(times=[0.1], leader_ids=[None], gaps=[None]))
    row = measured.iloc[0]
    assert row["missing_reason"] == "no_observed_leader"
    assert row["measurement_status"] == "not_applicable"
    assert not bool(row["ttc_valid"])
    assert pd.isna(row["ttc_s"])
    assert not bool(row["reliable_following_eligible"])
    assert not bool(row["p2_evaluable_eligible"])
    assert pd.isna(row["net_gap_m"])


def test_invalid_gap_and_unresolved_identity_are_separated_from_no_leader() -> None:
    measured = compute_sumo_measurements(
        _states(
            [
                {
                    "time_s": 0.1,
                    "simulation_step": 1,
                    "vehicle_id": "overlap",
                    "speed_mps": 10.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "leader",
                    "leader_speed_mps": 5.0,
                    "net_gap_m": -1.0,
                },
                {
                    "time_s": 0.1,
                    "simulation_step": 1,
                    "vehicle_id": "unresolved",
                    "speed_mps": 10.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "leader",
                    "leader_identity_status": "unresolved",
                    "leader_speed_mps": 5.0,
                    "net_gap_m": 10.0,
                },
            ]
        )
    )
    overlap = measured.loc[measured.vehicle_id == "overlap"].iloc[0]
    assert overlap["measurement_status"] == "invalid"
    assert overlap["missing_reason"] == "non_positive_gap"
    assert not bool(overlap["ttc_valid"])
    unresolved = measured.loc[measured.vehicle_id == "unresolved"].iloc[0]
    assert unresolved["measurement_status"] == "missing"
    assert unresolved["missing_reason"] == "leader_identity_unresolved"
    assert not bool(unresolved["p2_evaluable_eligible"])
    assert set(measured["measurement_status"]).issubset({"valid", "not_applicable", "missing", "invalid"})


def test_canonical_projection_satisfies_the_stage_0_3_contract() -> None:
    frame = _states(
        [
            {
                "time_s": 0.1,
                "simulation_step": 1,
                "vehicle_id": "f",
                "speed_mps": 12.0,
                "acceleration_mps2": 0.0,
                "leader_id": "l",
                "leader_speed_mps": 11.4,
                "net_gap_m": 8.0,
                "x_m": 10.0,
                "y_m": 1.6,
            },
            {
                "time_s": 0.1,
                "simulation_step": 1,
                "vehicle_id": "free",
                "speed_mps": 12.0,
                "acceleration_mps2": 0.0,
                "leader_id": None,
                "leader_speed_mps": None,
                "net_gap_m": None,
                "x_m": 30.0,
                "y_m": 1.6,
            },
        ]
    )
    measured = compute_sumo_measurements(frame)
    canonical = to_canonical_real_state(measured)
    validate_real_state_table(canonical)
    assert set(canonical["dataset"]) == {"sumo"}
    missing = canonical[canonical["measurement_status"] == "missing"]
    assert len(missing) == 0
    free = canonical[canonical["vehicle_id"] == "free"].iloc[0]
    assert free["missing_reason"] == "no_observed_leader"
    assert pd.isna(free["net_gap_m"])


# --------------------------------------------------------------------------------------
# P2 engineering adapter and exposure
# --------------------------------------------------------------------------------------


def test_p2_confirmation_happens_only_after_the_observed_duration() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3], gaps=[1.0] * 4, leader_speed=11.4)
    events, exposure = build_sumo_p2_events(frame, recorded_observation_step_s=0.1)
    assert len(events) == 1
    event = events.iloc[0]
    assert event["event_start_s"] == pytest.approx(0.0)
    assert event["event_confirm_s"] == pytest.approx(0.2)
    assert event["event_confirm_s"] - event["event_start_s"] >= 0.2 - 1e-9
    assert event["raw_frame_count"] == 4
    assert event["rule"] == "P2"
    assert event["measurement_equivalence_status"] == "pending_sumo_adapter_review"
    assert bool(event["scientific_claim_eligible"]) is False
    assert exposure["formal_rate_eligible"] is False


def test_p2_requires_the_full_minimum_duration_of_consecutive_risk() -> None:
    frame = _following_rows(times=[0.0, 0.1], gaps=[1.0, 1.0], leader_speed=11.4)
    events, _ = build_sumo_p2_events(frame, recorded_observation_step_s=0.1)
    assert events.empty


def test_p2_does_not_bridge_leader_switch_or_cadence_break() -> None:
    switched = _following_rows(times=[0.0, 0.1, 0.2, 0.3], leader_ids=["l1", "l1", "l2", "l2"], gaps=[1.0] * 4)
    events, _ = build_sumo_p2_events(switched, recorded_observation_step_s=0.1)
    assert events.empty

    # 0.0-0.1 and 0.5-0.6 are separate risk observations; bridging them would create a
    # spurious 0.6 s event, so a correct adapter must return no event at all.
    gap_break = _following_rows(times=[0.0, 0.1, 0.5, 0.6], gaps=[1.0] * 4)
    events, _ = build_sumo_p2_events(gap_break, recorded_observation_step_s=0.1)
    assert events.empty
    bridged, _ = build_sumo_p2_events(
        _following_rows(times=[0.0, 0.1, 0.2, 0.5, 0.6, 0.7], gaps=[1.0] * 6),
        recorded_observation_step_s=0.1,
    )
    # two honest 0.2 s events, never one 0.6 s event spanning the recording break
    assert sorted(bridged["event_start_s"]) == pytest.approx([0.0, 0.5])
    assert bridged["event_duration_s"].le(0.2 + 1e-9).all()


def test_p2_does_not_bridge_a_trajectory_incarnation_change() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3], gaps=[1.0] * 4)
    frame.loc[2:, "incarnation_id"] = "run|f|1"
    events, _ = build_sumo_p2_events(frame, recorded_observation_step_s=0.1)
    assert events.empty


def test_p2_exit_reason_and_event_identity_are_auditable() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3, 0.4], gaps=[1.0] * 3 + [50.0] * 2)
    events, _ = build_sumo_p2_events(frame, recorded_observation_step_s=0.1)
    assert len(events) == 1
    assert events.iloc[0]["event_duration_s"] == pytest.approx(0.2)
    assert events.iloc[0]["ttc_min_s"] == pytest.approx(1.0 / 0.6)


def test_exposure_keeps_reliable_non_closing_following_time() -> None:
    frame = pd.concat(
        [
            _following_rows(times=[0.0, 0.1, 0.2], gaps=[10.0] * 3, leader_speed=12.0),  # opening
            _following_rows(times=[0.0, 0.1], gaps=[1.0, 1.0], leader_speed=11.4, vehicle_id="c"),  # closing
        ],
        ignore_index=True,
    )
    measured = compute_sumo_measurements(frame)
    exposure = compute_exposure(measured, recorded_observation_step_s=0.1)
    assert exposure["reliable_following_exposure_s"] == pytest.approx(0.3)
    assert exposure["p2_evaluable_following_exposure_s"] == pytest.approx(0.3)
    assert exposure["reliable_closing_exposure_s"] == pytest.approx(0.1)
    assert exposure["p2_evaluable_following_vehicle_hours"] == pytest.approx(0.3 / 3600.0)


def test_exposure_never_uses_a_single_closing_observation_as_the_denominator() -> None:
    frame = _following_rows(times=[0.0, 0.1], gaps=[1.0, 1.0], leader_speed=11.4)
    measured = compute_sumo_measurements(frame)
    exposure = compute_exposure(measured, recorded_observation_step_s=0.1)
    assert exposure["p2_evaluable_following_exposure_s"] == pytest.approx(0.1)
    assert exposure["p2_evaluable_following_exposure_s"] > exposure["reliable_closing_exposure_s"] - 1e-9


def test_cadence_scaling_and_coarse_recordings_are_not_relabelled() -> None:
    assert cadence_max_gap_s(0.1) == pytest.approx(0.11)
    assert cadence_max_gap_s(0.2) == pytest.approx(0.22)
    coarse = _following_rows(times=[0.0, 0.2, 0.4, 0.6], gaps=[1.0] * 4)
    events, _ = build_sumo_p2_events(coarse, recorded_observation_step_s=0.2)
    assert len(events) == 1
    assert events.iloc[0]["max_gap_s"] == pytest.approx(0.22)
    assert events.iloc[0]["event_confirm_s"] == pytest.approx(0.2)

    with pytest.raises(Stage05EngineeringError, match="must not be relabelled"):
        extract_sumo_formal_p2_events(coarse, recorded_observation_step_s=0.2)
    formal, audit = extract_sumo_formal_p2_events(
        coarse, recorded_observation_step_s=0.2, allow_nonstandard_cadence=True
    )
    assert formal.empty
    assert audit["equivalence_status"] == "pending_measurement_equivalence_nonstandard_cadence"

    with pytest.raises(Stage05EngineeringError, match="does not match the declared"):
        validate_observation_cadence([0.0, 0.2, 0.4], declared_step_s=0.1)
    check = validate_observation_cadence([0.0, 0.1, 0.2], declared_step_s=0.1)
    assert check["link_count"] == 2


def test_formal_adapter_reuses_stage_0_2_identity_and_continuity_rules() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3], gaps=[1.0] * 4, leader_speed=11.4)
    formal, audit = extract_sumo_formal_p2_events(frame, recorded_observation_step_s=0.1)
    assert len(formal) == 1
    assert formal.iloc[0]["event_start_s"] == pytest.approx(0.0)
    assert formal.iloc[0]["event_confirm_s"] == pytest.approx(0.2)
    assert formal.iloc[0]["algorithm_version"] == "stage_0_2.ngsim.reliability.v2"
    assert audit["equivalence_status"] == "pending_measurement_equivalence_review"
    assert audit["formal_comparability"] is False
    field_map = audit["field_map"]
    assert field_map["original_row_number"]["status"] == "adapter_defined_simulator_frame_index"
    assert field_map["diagnostic_clock_anchor_ms"]["status"] == "definitional_constant"
    assert field_map["drac_mps2"]["status"] == "adapter_reuses_approved_closed_form_pending_review"
    assert audit["ngsim_only_fields"]["diagnostic_clock_conflict"] == "not_applicable_to_simulator_observation"


def test_formal_adapter_fails_closed_on_unmatched_leader_identity() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3], gaps=[1.0] * 4)
    frame["leader_identity_status"] = "unresolved"
    formal, audit = extract_sumo_formal_p2_events(frame, recorded_observation_step_s=0.1)
    assert formal.empty
    assert audit["reliable_candidate_events"] == 0


def test_measurement_support_matrix_keeps_pending_items_pending() -> None:
    matrix = measurement_support_matrix()
    items = matrix["items"]
    assert items["speed_and_acceleration"]["status"] == "verified_engineering"
    assert items["net_gap"]["status"] == "verified_engineering"
    assert items["p2_event_extraction"]["status"] == "engineering_only"
    assert items["formal_p2_equivalence"]["status"] == "pending_measurement_equivalence"
    assert items["reality_coverage"]["status"] == "pending_scientific"
    assert matrix["scientific_claim_eligible"] is False


# --------------------------------------------------------------------------------------
# calibration / validation isolation
# --------------------------------------------------------------------------------------


def test_calibration_entry_rejects_the_temporal_validation_window(tmp_path: Path) -> None:
    from riskprop.stage_0_5_sumo import CalibrationValidationGuard

    log = tmp_path / "access_audit.json"
    guard = CalibrationValidationGuard(log_path=log)
    guard.require(role="calibration", sources=CALIBRATION_VALIDATION_POLICY["calibration"])
    with pytest.raises(Stage05AccessDenied, match="restricted_source_for_role"):
        guard.require(role="calibration", sources=["us101__0820_0835"])
    with pytest.raises(Stage05AccessDenied):
        guard.require(role="calibration", sources=["lankershim__complete"])
    with pytest.raises(Stage05AccessDenied, match="unknown_access_role"):
        guard.require(role="locked_holdout", sources=["us101__0750_0805"])
    audit = guard.audit()
    assert audit["denied_count"] == 3
    assert audit["locked_holdout_accessed"] is False
    assert audit["validation_window_read"] is False
    recorded = json.loads(log.read_text(encoding="utf-8"))
    assert len(recorded) == 4
    assert [entry["allowed"] for entry in recorded] == [True, False, False, False]
    assert any(entry["restricted_sources"] == ["us101__0820_0835"] for entry in recorded)


def test_source_read_is_refused_on_binding_mismatch(tmp_path: Path) -> None:
    from riskprop.stage_0_5_sumo import CalibrationValidationGuard

    source = tmp_path / "us101__0750_0805.parquet"
    source.write_bytes(b"not the bound reference")
    guard = CalibrationValidationGuard(log_path=tmp_path / "audit.json")
    with pytest.raises(Stage05AccessDenied, match="SHA-256"):
        guard.require_source_read(source, role="calibration", source="us101__0750_0805")
    assert guard.audit()["denied_count"] == 1
    with pytest.raises(Stage05AccessDenied, match="restricted_source_for_role"):
        guard.require_source_read(source, role="calibration", source="us101__0820_0835")


def test_policy_never_claims_cross_road_generalization_or_locked_holdout() -> None:
    policy = CALIBRATION_VALIDATION_POLICY
    assert policy["cross_road_generalization_claimed"] is False
    assert policy["validation_is_same_site_time_extrapolation_only"] is True
    assert policy["validation_window_previously_published"] is True
    assert policy["internal_window_isolation_is_not_project_locked_holdout"] is True
    assert policy["locked_holdout_accessed"] is False
    assert policy["reference_result_id"] == "RES-STAGE-0.5-REAL-REF-R2"
    assert len(policy["source_bindings"]["us101__0820_0835"]) == 64


# --------------------------------------------------------------------------------------
# identity scope
# --------------------------------------------------------------------------------------


def test_vehicle_identity_is_run_scoped_and_re_entry_is_auditable() -> None:
    tracker = VehicleIdentityTracker("run_a")
    assert tracker.observe(["v1"], time_s=0.1, observation_index=1) == [
        {"vehicle_id": "v1", "incarnation_id": "run_a|v1|0"}
    ]
    tracker.observe([], time_s=0.2, observation_index=2)
    re_entry = tracker.observe(["v1"], time_s=0.3, observation_index=3)
    assert re_entry == [{"vehicle_id": "v1", "incarnation_id": "run_a|v1|1"}]
    tracker.close(time_s=0.4, observation_index=4)
    events = [event["event_type"] for event in tracker.events]
    assert events == ["enter", "exit", "enter", "active_at_observation_end"]
    assert len({event["incarnation_id"] for event in tracker.events}) == 2
    other_run = VehicleIdentityTracker("run_b")
    assert other_run.observe(["v1"], time_s=0.1, observation_index=1)[0]["incarnation_id"] == "run_b|v1|0"


def test_reliable_following_link_is_evaluable_only_when_the_status_allows_it() -> None:
    """A non-positive-gap link stays reliable exposure but is not P2-evaluable."""

    frame = _states(
        [
            {
                "time_s": 0.0,
                "simulation_step": 0,
                "vehicle_id": "f",
                "speed_mps": 12.0,
                "acceleration_mps2": 0.0,
                "leader_id": "l",
                "leader_speed_mps": 11.0,
                "net_gap_m": 5.0,
            },
            {
                "time_s": 0.1,
                "simulation_step": 1,
                "vehicle_id": "f",
                "speed_mps": 12.0,
                "acceleration_mps2": 0.0,
                "leader_id": "l",
                "leader_speed_mps": 11.0,
                "net_gap_m": -1.0,
            },
        ]
    )
    exposure = compute_exposure(compute_sumo_measurements(frame), recorded_observation_step_s=0.1)
    assert exposure["reliable_following_exposure_s"] == pytest.approx(0.1)
    assert exposure["p2_evaluable_following_exposure_s"] == pytest.approx(0.0)
    assert exposure["not_evaluable_following_exposure_s"] == pytest.approx(0.1)


def test_closing_epsilon_matches_the_approved_pipeline_tolerance() -> None:
    measured = compute_sumo_measurements(
        _states(
            [
                {
                    "time_s": 0.0,
                    "vehicle_id": "tiny",
                    "speed_mps": 12.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "l",
                    "leader_speed_mps": 11.9995,
                    "net_gap_m": 5.0,
                },
                {
                    "time_s": 0.0,
                    "vehicle_id": "over",
                    "speed_mps": 12.0,
                    "acceleration_mps2": 0.0,
                    "leader_id": "l",
                    "leader_speed_mps": 11.998,
                    "net_gap_m": 5.0,
                },
            ]
        )
    )
    tiny = measured.loc[measured.vehicle_id == "tiny"].iloc[0]
    assert tiny["closing_speed_mps"] == pytest.approx(0.0005)
    assert not bool(tiny["ttc_valid"])
    assert tiny["missing_reason"] == "non_closing"
    over = measured.loc[measured.vehicle_id == "over"].iloc[0]
    assert bool(over["ttc_valid"])


def test_drac_is_the_approved_closed_form_and_is_severity_only() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3], gaps=[1.0] * 4, leader_speed=11.4)
    measured = compute_sumo_measurements(frame)
    follower = measured.loc[measured.vehicle_id == "f"].iloc[0]
    assert follower["drac_mps2"] == pytest.approx(0.6 ** 2 / (2 * 1.0))
    with_drac, _ = build_sumo_p2_events(measured, recorded_observation_step_s=0.1)
    without = measured.copy()
    without["drac_mps2"] = float("nan")
    without_drac, _ = build_sumo_p2_events(without, recorded_observation_step_s=0.1)
    assert len(with_drac) == len(without_drac)
    for column in ("event_start_s", "event_end_s", "event_confirm_s", "ttc_min_s"):
        assert with_drac.iloc[0][column] == pytest.approx(without_drac.iloc[0][column])
    formal_with, _ = extract_sumo_formal_p2_events(measured, recorded_observation_step_s=0.1)
    formal_without, _ = extract_sumo_formal_p2_events(without, recorded_observation_step_s=0.1)
    assert len(formal_with) == len(formal_without)
    assert formal_with.iloc[0]["drac_max_mps2"] == pytest.approx(0.6 ** 2 / 2)


def test_formal_source_frame_uses_an_absolute_clock_and_the_leaders_own_frame() -> None:
    frame = _following_rows(times=[30.0, 30.1, 30.2, 30.3], gaps=[1.0] * 4)
    measured = compute_sumo_measurements(frame)
    formal = build_sumo_formal_source_frame(measured, recorded_observation_step_s=0.1)
    follower = formal.loc[formal.vehicle_id == "f"].sort_values("time_s")
    assert follower["global_time_ms"].tolist() == [30000, 30100, 30200, 30300]
    assert follower["frame_id"].tolist() == [0, 1, 2, 3]
    assert follower["leader_frame_id"].notna().all()
    assert follower["leader_frame_id"].diff().dropna().eq(1.0).all()
    assert follower["observation_index"].diff().dropna().eq(1.0).all()


def test_native_event_table_keeps_the_exit_reason_and_drac() -> None:
    frame = _following_rows(times=[0.0, 0.1, 0.2, 0.3], gaps=[1.0] * 4)
    events, _ = build_sumo_p2_events(compute_sumo_measurements(frame), recorded_observation_step_s=0.1)
    assert "exit_reason" in events.columns
    assert "drac_max_mps2" in events.columns
    assert events.iloc[0]["exit_reason"] == "observation_end_right_censored"
    assert float(events.iloc[0]["drac_max_mps2"]) > 0


def test_unresolved_leader_incarnation_cannot_produce_a_finite_ttc() -> None:
    frame = _following_rows(times=[0.0, 0.1], gaps=[1.0, 1.0])
    frame["leader_incarnation_id"] = None
    measured = compute_sumo_measurements(frame)
    follower = measured.loc[measured.vehicle_id == "f"]
    assert follower["measurement_status"].eq("missing").all()
    assert follower["missing_reason"].eq("leader_identity_unresolved").all()
    assert not follower["ttc_valid"].any()
    formal, audit = extract_sumo_formal_p2_events(measured, recorded_observation_step_s=0.1)
    assert formal.empty and audit["reliable_candidate_events"] == 0


def test_measurement_equivalence_matrix_is_itemised_and_never_overclaims() -> None:
    matrix = measurement_equivalence_matrix()
    assert matrix["boundary_case_count"] == len(p2_boundary_cases())
    assert matrix["boundary_cases_all_as_expected"] is True
    assert matrix["blocking_items"] == []
    assert set(matrix["verdict_counts"]) <= set(EQUIVALENCE_VERDICTS)
    assert matrix["equivalent_or_verified_count"] + matrix["engineering_only_count"] + matrix[
        "not_equivalent_count"
    ] + matrix["pending_evidence_count"] == len(matrix["rows"])
    for row in matrix["rows"]:
        assert row["verdict"] in EQUIVALENCE_VERDICTS
        assert row["evidence"]
    # an aggregate count agreement is never sufficient: the reviewed items stay explicit
    assert matrix["overall_status"] == "pending_measurement_equivalence_review"
    assert matrix["scientific_claim_eligible"] is False
    by_dimension = {row["dimension"]: row for row in matrix["rows"]}
    assert by_dimension["measurement_status_vocabulary"]["verdict"] == "Engineering Consistent Only"
    assert by_dimension["p2_threshold"]["verdict"] == "Equivalent / Verified"


def test_reason_crosswalk_documents_the_approved_asymmetry() -> None:
    assert MISSING_REASON_EQUIVALENCE["non_positive_gap"]["sumo_reason"] == "non_positive_gap"
    assert (
        MISSING_REASON_EQUIVALENCE["no_reported_leader"]["comparability"] == "Engineering Consistent Only"
    )
    assert NGSIM_STATUS_CROSSWALK["missing__no_reported_leader"]["sumo_label"].startswith("not_applicable")
    assert CLOSING_SPEED_SEMANTICS["formal_source"].endswith("follower - leader)")
    assert NGSIM_CLOSING_EPSILON_MPS == 1e-3


# --------------------------------------------------------------------------------------
# SUMO integration (skipped, never faked, when SUMO is unavailable)
# --------------------------------------------------------------------------------------


@requires_sumo
def test_sumo_baseline_engineering_run_is_sealed_and_contract_complete(tmp_path: Path) -> None:
    package = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "baseline",
        fixture_id="baseline_mixed_demand",
        duration_s=20.0,
    )
    _verify_sha256sums(package)
    config = json.loads((package / "config.json").read_text(encoding="utf-8"))
    audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
    runtime = json.loads((package / "runtime_diagnostics.json").read_text(encoding="utf-8"))
    assert config["experiment_mode"] == "no_message_baseline"
    assert config["communication_enabled"] is False
    assert config["source_risk_treatment_enabled"] is False
    assert config["information_adoption_enabled"] is False
    assert config["scientific_claim_eligible"] is False
    assert config["gate_status"] == "pending_simulation_sample"
    assert set(config["parameter_status"].values()) <= {"engineering_fixture_only", "pending_scientific"}
    assert audit["stage_0_5_gate"] == "pending_simulation_sample"
    assert audit["protocol_lock_allowed"] is False
    assert audit["stage_1_1_allowed"] is False
    for key in (
        "real_network_geometry_confirmed",
        "scientific_demand_approved",
        "vtype_mapping_approved",
        "scientific_time_step_frozen",
        "warmup_and_evaluation_window_fixed",
        "formal_p2_comparability_proven",
        "reality_coverage_tolerance_approved",
        "independent_validation_performed",
    ):
        assert audit[key] is False, key

    states = pd.read_parquet(package / "state.parquet")
    for column in (
        "run_id", "scenario_id", "fixture_id", "experiment_mode", "configured_seed", "vehicle_id",
        "trajectory_id", "incarnation_id", "edge_id", "lane_id", "simulation_step", "time_s",
        "speed_mps", "acceleration_mps2", "longitudinal_position_m", "vehicle_type",
        "original_vehicle_type", "vtype_mapping_version", "leader_id", "leader_incarnation_id",
        "leader_identity_status", "leader_speed_mps", "net_gap_m", "closing_speed_mps",
        "following_status", "ttc_s", "ttc_valid", "measurement_status", "missing_reason",
        "reliable_following_eligible", "p2_evaluable_eligible",
    ):
        assert column in states.columns, column
    assert set(states["experiment_mode"]) == {"no_message_baseline"}
    assert set(states["measurement_status"]).issubset({"valid", "not_applicable", "missing", "invalid"})
    assert states.loc[states["measurement_status"] == "valid", "ttc_s"].gt(0).all()
    assert states.loc[states["leader_observed"], "net_gap_m"].notna().all()
    observed = states["leader_observed"]
    expected_closing = states.loc[observed, "speed_mps"] - states.loc[observed, "leader_speed_mps"]
    assert (states.loc[observed, "closing_speed_mps"] - expected_closing).abs().max() < 1e-9

    # unified net-gap conversion: verified against independently derived geometry
    same_lane = states[states["net_gap_crosscheck_residual_m"].notna()]
    assert len(same_lane) > 100
    assert same_lane["net_gap_crosscheck_residual_m"].abs().max() < 1e-6
    assert runtime["net_gap_crosscheck"]["lane_position_residual_max_abs_m"] < 1e-6
    assert states["leader_traci_distance_m"].notna().sum() == states["leader_observed"].sum()
    follower_min_gap = states.loc[states["leader_observed"], "follower_min_gap_m"]
    traci_distance = states.loc[states["leader_observed"], "leader_traci_distance_m"]
    net_gap = states.loc[states["leader_observed"], "net_gap_m"]
    assert (net_gap - (traci_distance + follower_min_gap)).abs().max() < 1e-9

    # declared internal/recorded cadence is audited, not relabelled
    assert runtime["observation_cadence_check"]["max_abs_error_s"] < 1e-6
    assert runtime["observation_decimation_factor"] == 1
    assert runtime["simulation_step_length_s"] == pytest.approx(config["internal_step_s"])
    assert config["recorded_observation_step_s"] == pytest.approx(FORMAL_OBSERVATION_STEP_S)
    assert runtime["insertion_failures"] == []
    assert set(runtime["not_departed_within_window"]) <= {
        "entry_1"
    }, "only demand scheduled beyond the run window may be absent"

    lifecycle = pd.read_parquet(package / "vehicle_lifecycle.parquet")
    assert set(lifecycle["event_type"]) <= {"enter", "exit", "active_at_observation_end"}
    assert set(lifecycle["vehicle_id"]) == set(states["vehicle_id"])
    assert states.groupby("incarnation_id")["vehicle_id"].nunique().max() == 1

    canonical = pd.read_parquet(package / "state_canonical_projection.parquet")
    validate_real_state_table(canonical)
    exposure = json.loads((package / "p2_exposure_summary.json").read_text(encoding="utf-8"))
    assert exposure["formal_rate_eligible"] is False
    assert exposure["rate_formula"] == "p2_event_count / p2_evaluable_following_vehicle_hours"
    assert exposure["p2_evaluable_following_exposure_s"] >= exposure["reliable_closing_exposure_s"] - 1e-9
    assert (package / "sumo_formal_field_map.json").is_file()
    assert (package / "access_audit.json").is_file()
    assert (package / "measurement_status_summary.json").is_file()


@requires_sumo
def test_sumo_probe_fixture_confirms_a_p2_event_in_both_adapters(tmp_path: Path) -> None:
    package = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "probe",
        fixture_id="measurement_probe_queue_stop",
        duration_s=8.0,
    )
    _verify_sha256sums(package)
    engineering = pd.read_parquet(package / "p2_engineering_events.parquet")
    formal = pd.read_parquet(package / "p2_formal_alignment_events.parquet")
    assert len(engineering) >= 1
    assert len(formal) == len(engineering)
    left = engineering.iloc[0]
    right = formal.iloc[0]
    assert left["vehicle_id"] == right["vehicle_id"]
    assert left["leader_id"] == right["leader_id"]
    assert left["event_start_s"] == pytest.approx(right["event_start_s"])
    assert left["event_end_s"] == pytest.approx(right["event_end_s"])
    assert left["event_confirm_s"] == pytest.approx(right["event_confirm_s"])
    assert left["ttc_min_s"] == pytest.approx(right["ttc_min_s"])
    assert left["event_confirm_s"] - left["event_start_s"] >= 0.2 - 1e-9
    assert left["event_duration_s"] >= 0.2 - 1e-9
    assert left["measurement_equivalence_status"] == "pending_sumo_adapter_review"
    assert bool(left["scientific_claim_eligible"]) is False
    audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
    assert audit["p2_engineering_events"] == len(engineering)
    assert audit["formal_adapter_equivalence_status"] == "pending_measurement_equivalence_review"
    assert audit["scientific_claim_eligible"] is False
    exposure = json.loads((package / "p2_exposure_summary.json").read_text(encoding="utf-8"))
    assert exposure["p2_event_rate_per_vehicle_hour"] == pytest.approx(
        exposure["p2_event_count"] / exposure["p2_evaluable_following_vehicle_hours"]
    )


@requires_sumo
def test_sumo_run_is_reproducible_for_the_same_seed_and_config(tmp_path: Path) -> None:
    first = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "run_a", fixture_id="baseline_mixed_demand", duration_s=10.0
    )
    second = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "run_b", fixture_id="baseline_mixed_demand", duration_s=10.0
    )
    for name in ("state.parquet", "p2_engineering_events.parquet", "p2_exposure_summary.json", "config.json"):
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == hashlib.sha256(
            (second / name).read_bytes()
        ).hexdigest(), name


@requires_sumo
def test_sumo_internal_and_recorded_steps_are_separately_configurable(tmp_path: Path) -> None:
    package = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "decimated",
        fixture_id="baseline_mixed_demand",
        duration_s=10.0,
        internal_step_s=0.05,
        recorded_observation_step_s=0.1,
    )
    config = json.loads((package / "config.json").read_text(encoding="utf-8"))
    runtime = json.loads((package / "runtime_diagnostics.json").read_text(encoding="utf-8"))
    assert config["internal_step_s"] == pytest.approx(0.05)
    assert config["recorded_observation_step_s"] == pytest.approx(0.1)
    assert runtime["observation_decimation_factor"] == 2
    assert runtime["simulation_step_length_s"] == pytest.approx(0.05)
    assert runtime["observation_cadence_check"]["max_abs_error_s"] < 1e-6
    states = pd.read_parquet(package / "state.parquet")
    deltas = states.loc[states["vehicle_id"] == states["vehicle_id"].iloc[0], "time_s"].diff().dropna()
    assert (deltas - 0.1).abs().max() < 1e-6
    with pytest.raises(Stage05EngineeringError, match="exact multiple"):
        run_stage_0_5_no_message_baseline(
            output_dir=tmp_path / "bad_stride",
            duration_s=5.0,
            internal_step_s=0.3,
            recorded_observation_step_s=0.1,
        )


@requires_sumo
def test_sumo_warmup_window_is_respected_and_unbuilt_scenarios_are_refused(tmp_path: Path) -> None:
    package = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "warmup",
        fixture_id="baseline_mixed_demand",
        duration_s=10.0,
        warmup_s=4.0,
    )
    config = json.loads((package / "config.json").read_text(encoding="utf-8"))
    states = pd.read_parquet(package / "state.parquet")
    assert config["warmup_s"] == pytest.approx(4.0)
    assert states["time_s"].min() >= 4.0 - 1e-9
    with pytest.raises(Stage05EngineeringError, match="only us101_highway_baseline"):
        run_stage_0_5_no_message_baseline(
            output_dir=tmp_path / "aux",
            scenario_id="lankershim_urban_auxiliary",
            duration_s=5.0,
        )
    with pytest.raises(Stage05EngineeringError, match="refusing to overwrite"):
        run_stage_0_5_no_message_baseline(output_dir=tmp_path / "warmup", duration_s=5.0)


@requires_sumo
def test_sumo_smoke_runs_never_change_the_stage_gate(tmp_path: Path) -> None:
    package = run_stage_0_5_no_message_baseline(
        output_dir=tmp_path / "gate", fixture_id="baseline_mixed_demand", duration_s=8.0, seed=123
    )
    audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
    provenance = json.loads((package / "provenance.json").read_text(encoding="utf-8"))
    assert audit["stage_0_5_gate"] == "pending_simulation_sample"
    assert audit["scientific_claim_eligible"] is False
    assert provenance["locked_holdout_accessed"] is False
    assert provenance["validation_window_read"] is False
    evidence_dir = REPO_ROOT / "evidence" / "results" / RESULT_ID
    if (evidence_dir / "audit.json").is_file():
        audit_portable = json.loads((evidence_dir / "audit.json").read_text(encoding="utf-8"))
        assert audit_portable["stage_0_5_gate"] == "pending_simulation_sample"
        assert audit_portable["scientific_claim_eligible"] is False
        config_portable = json.loads((evidence_dir / "config.json").read_text(encoding="utf-8"))
        assert config_portable["result_id"] == RESULT_ID
        assert config_portable["gate_status"] == "pending_simulation_sample"
