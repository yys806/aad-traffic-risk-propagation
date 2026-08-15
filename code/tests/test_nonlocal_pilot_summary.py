import pandas as pd

from riskprop.nonlocal_pilot_summary import (
    compare_pre_treatment_trajectories,
    locate_first_applied_time,
    summarize_mechanism_log,
)


def test_mechanism_summary_distinguishes_shadow_trigger_from_application():
    records = pd.DataFrame(
        [
            {
                "ego_vehicle_id": "av_0",
                "remote_vehicle_id": "human_1",
                "ego_eta_s": 1.0,
                "remote_eta_s": 1.2,
                "would_trigger": False,
                "applied": False,
            },
            {
                "ego_vehicle_id": "av_0",
                "remote_vehicle_id": "human_1",
                "ego_eta_s": 0.8,
                "remote_eta_s": 0.9,
                "would_trigger": True,
                "applied": False,
            },
        ]
    )

    summary = summarize_mechanism_log(records)

    assert summary["candidate_record_count"] == 2
    assert summary["would_trigger_count"] == 1
    assert summary["applied_count"] == 0
    assert summary["eta_complete_count"] == 2
    assert summary["remote_vehicle_count"] == 1


def test_locates_applied_record_in_emission_by_vehicle_and_position():
    mechanism = pd.DataFrame(
        [
            {
                "ego_vehicle_id": "av_0",
                "ego_position_xy": [10.0, 1.0],
                "applied": True,
                "step": 2,
            }
        ]
    )
    emissions = pd.DataFrame(
        [
            {"time": 0.2, "id": "av_0", "x": 9.0, "y": 1.0},
            {"time": 0.4, "id": "av_0", "x": 10.0, "y": 1.0},
        ]
    )

    result = locate_first_applied_time(mechanism, emissions)

    assert result["first_applied_step"] == 2
    assert result["first_applied_time_s"] == 0.4
    assert result["position_match_error_m"] == 0.0


def test_pre_treatment_pair_matches_before_first_application_and_diverges_after():
    common = [
        {"time": 0.0, "id": "v0", "x": 0.0, "y": 0.0, "speed": 1.0, "edge_id": "left", "lane_number": 0},
        {"time": 0.2, "id": "v0", "x": 0.2, "y": 0.0, "speed": 1.0, "edge_id": "left", "lane_number": 0},
    ]
    on = pd.DataFrame(common + [
        {"time": 0.4, "id": "v0", "x": 0.35, "y": 0.0, "speed": 0.8, "edge_id": "left", "lane_number": 0}
    ])
    off = pd.DataFrame(common + [
        {"time": 0.4, "id": "v0", "x": 0.4, "y": 0.0, "speed": 1.0, "edge_id": "left", "lane_number": 0}
    ])

    result = compare_pre_treatment_trajectories(on, off, first_applied_time_s=0.4)

    assert result["pre_treatment_keys_match"] is True
    assert result["pre_treatment_values_match"] is True
    assert result["first_divergence_time_s"] == 0.4
