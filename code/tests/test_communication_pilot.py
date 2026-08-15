import pandas as pd
import pytest

from riskprop.communication_pilot import (
    compute_factorial_effects,
    merge_communication_episodes,
    select_valid_run_results,
    summarize_communication_records,
    summarize_target_risk,
    target_zone_mask,
)


def test_target_zone_uses_downstream_merge_conflict_edges_and_coordinates():
    rows = pd.DataFrame(
        [
            {"edge_id": "bottom", "x": 550.0},
            {"edge_id": "left", "x": 580.0},
            {"edge_id": ":center_1", "x": 600.0},
            {"edge_id": "inflow_merge", "x": 520.0},
            {"edge_id": "left", "x": 530.0},
            {"edge_id": "center", "x": 650.0},
        ]
    )

    assert target_zone_mask(rows).tolist() == [True, True, True, False, False, False]


def test_target_risk_requires_valid_leader_and_reports_continuous_burden():
    emissions = pd.DataFrame(
        [
            {
                "edge_id": "bottom",
                "x": 550.0,
                "leader_id": "v_lead",
                "headway": 2.0,
                "leader_rel_speed": -2.0,
                "realized_accel": -5.0,
                "speed": 10.0,
            },
            {
                "edge_id": "left",
                "x": 580.0,
                "leader_id": "v_lead_2",
                "headway": 9.0,
                "leader_rel_speed": -3.0,
                "realized_accel": 0.0,
                "speed": 20.0,
            },
            {
                "edge_id": "bottom",
                "x": 560.0,
                "leader_id": None,
                "headway": 1000.0,
                "leader_rel_speed": -1000.0,
                "realized_accel": 0.0,
                "speed": 15.0,
            },
            {
                "edge_id": "inflow_merge",
                "x": 520.0,
                "leader_id": "v_other",
                "headway": 1.0,
                "leader_rel_speed": -4.0,
                "realized_accel": -6.0,
                "speed": 5.0,
            },
        ]
    )

    result = summarize_target_risk(emissions, ttc_threshold_s=2.0)

    assert result["target_vehicle_step_count"] == 3
    assert result["valid_ttc_count"] == 2
    assert result["ttc_violation_count"] == 1
    assert result["ttc_violation_rate"] == pytest.approx(0.5)
    assert result["ttc_conflict_burden"] == pytest.approx(0.5)
    assert result["minimum_ttc_s"] == pytest.approx(1.0)
    assert result["hard_brake_count"] == 1
    assert result["hard_brake_rate_per_1000_steps"] == pytest.approx(1000 / 3)
    assert result["mean_speed_mps"] == pytest.approx(15.0)


def test_communication_summary_counts_message_lifecycle_and_application():
    records = pd.DataFrame(
        [
            {
                "message_generated": True,
                "message_sent": True,
                "message_dropped": False,
                "message_delivered": True,
                "cache_usable": True,
                "applied": True,
            },
            {
                "message_generated": True,
                "message_sent": True,
                "message_dropped": True,
                "message_delivered": False,
                "cache_usable": True,
                "applied": False,
            },
            {
                "message_generated": True,
                "message_sent": False,
                "message_dropped": False,
                "message_delivered": False,
                "cache_usable": False,
                "applied": False,
            },
        ]
    )

    result = summarize_communication_records(records)

    assert result["record_count"] == 3
    assert result["generated_count"] == 3
    assert result["sent_count"] == 2
    assert result["dropped_count"] == 1
    assert result["delivered_count"] == 1
    assert result["cache_usable_count"] == 2
    assert result["applied_count"] == 1
    assert result["drop_rate"] == pytest.approx(0.5)


def test_contiguous_applied_records_merge_into_communication_episodes():
    records = pd.DataFrame(
        [
            {"run_token": "r", "sumo_seed": 1, "ego_vehicle_id": "a", "step": 1, "applied": True},
            {"run_token": "r", "sumo_seed": 1, "ego_vehicle_id": "a", "step": 2, "applied": True},
            {"run_token": "r", "sumo_seed": 1, "ego_vehicle_id": "a", "step": 3, "applied": False},
            {"run_token": "r", "sumo_seed": 1, "ego_vehicle_id": "a", "step": 4, "applied": True},
            {"run_token": "r", "sumo_seed": 2, "ego_vehicle_id": "a", "step": 1, "applied": True},
        ]
    )

    episodes = merge_communication_episodes(records)

    assert len(episodes) == 3
    first = episodes.sort_values(["sumo_seed", "start_step"]).iloc[0]
    assert first["start_step"] == 1
    assert first["end_step"] == 2
    assert first["record_count"] == 2


def test_factorial_effect_uses_paired_source_by_channel_difference():
    run_metrics = pd.DataFrame(
        [
            {"penetration_pct": 60, "configured_run_seed": 11, "stress_profile": "nominal", "condition": "off", "ttc_conflict_burden": 1.0},
            {"penetration_pct": 60, "configured_run_seed": 11, "stress_profile": "nominal", "condition": "comm_ideal", "ttc_conflict_burden": 2.0},
            {"penetration_pct": 60, "configured_run_seed": 11, "stress_profile": "source_high", "condition": "off", "ttc_conflict_burden": 3.0},
            {"penetration_pct": 60, "configured_run_seed": 11, "stress_profile": "source_high", "condition": "comm_ideal", "ttc_conflict_burden": 6.0},
            {"penetration_pct": 60, "configured_run_seed": 12, "stress_profile": "nominal", "condition": "off", "ttc_conflict_burden": 2.0},
            {"penetration_pct": 60, "configured_run_seed": 12, "stress_profile": "nominal", "condition": "comm_ideal", "ttc_conflict_burden": 2.5},
            {"penetration_pct": 60, "configured_run_seed": 12, "stress_profile": "source_high", "condition": "off", "ttc_conflict_burden": 4.0},
            {"penetration_pct": 60, "configured_run_seed": 12, "stress_profile": "source_high", "condition": "comm_ideal", "ttc_conflict_burden": 5.5},
        ]
    )

    effects = compute_factorial_effects(run_metrics, metric="ttc_conflict_burden")

    assert effects["configured_run_seed"].tolist() == [11, 12]
    assert effects["communication_effect_nominal"].tolist() == pytest.approx([1.0, 0.5])
    assert effects["communication_effect_source_high"].tolist() == pytest.approx([3.0, 1.5])
    assert effects["factorial_interaction"].tolist() == pytest.approx([2.0, 1.0])


def test_valid_run_selector_replaces_only_invalid_off_oracle_source_high_rows():
    primary = pd.DataFrame(
        [
            {"condition": condition, "stress_profile": profile, "penetration_pct": 60,
             "configured_run_seed": 11, "marker": "primary"}
            for condition in ["off", "oracle", "comm_ideal", "comm_impaired"]
            for profile in ["nominal", "source_high"]
        ]
    )
    corrected = pd.DataFrame(
        [
            {"condition": condition, "stress_profile": "source_high", "penetration_pct": 60,
             "configured_run_seed": 11, "marker": "corrected"}
            for condition in ["off", "oracle"]
        ]
    )

    selected = select_valid_run_results(primary, corrected)

    markers = selected.set_index(["condition", "stress_profile"])["marker"].to_dict()
    assert len(selected) == 8
    assert markers[("off", "source_high")] == "corrected"
    assert markers[("oracle", "source_high")] == "corrected"
    assert markers[("comm_ideal", "source_high")] == "primary"
    assert markers[("off", "nominal")] == "primary"


def test_valid_run_selector_can_replace_cross_run_communication_cells():
    primary = pd.DataFrame(
        [
            {"condition": "comm_ideal", "stress_profile": "nominal", "penetration_pct": 60,
             "configured_run_seed": seed, "marker": "primary"}
            for seed in [11, 12]
        ]
    )
    corrected_source = primary.iloc[0:0].copy()
    corrected_communication = primary.loc[
        primary["configured_run_seed"].eq(12)
    ].assign(marker="corrected")

    selected = select_valid_run_results(
        primary, corrected_source, corrected_communication
    )

    markers = selected.set_index("configured_run_seed")["marker"].to_dict()
    assert markers == {11: "primary", 12: "corrected"}
