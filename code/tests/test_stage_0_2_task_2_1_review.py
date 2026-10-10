import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_stage_0_2_task_2_1_extreme_review import independent_recompute, sample_cases


def test_task_2_1_sampling_is_deterministic_and_deduplicates_categories():
    frame = pd.DataFrame(
        {
            "ttc_valid": [True, True, False], "ttc_s": [0.1, 1.99, float("inf")],
            "drac_mps2": [20.0, 1.0, float("nan")], "net_gap_m": [0.1, 4.0, -1.0],
            "closing_speed_mps": [2.0, 1.0, float("nan")], "measurement_status": ["valid", "valid", "invalid"],
            "trajectory_id": ["a", "a", "b"], "leader_trajectory_id": ["la", "la", "lb"],
        }
    )
    first = sample_cases(frame, "source")
    second = sample_cases(frame, "source")
    assert first.index.tolist() == second.index.tolist()
    assert first.loc[first.index[0], "review_categories"] == "drac_gt_10;near_zero_positive_gap;ttc_lt_0_5"


def test_task_2_1_independent_recompute_matches_known_units():
    raw = pd.DataFrame(
        [
            {"Vehicle_ID": 10, "Frame_ID": 1, "Global_Time": 1000, "v_Length": 12.0, "v_Vel": 30.0, "Space_Hdwy": 30.0},
            {"Vehicle_ID": 20, "Frame_ID": 1, "Global_Time": 1000, "v_Length": 15.0, "v_Vel": 20.0, "Space_Hdwy": 0.0},
        ]
    )
    row = pd.Series({"global_time_ms": 1000, "frame_id": 1, "vehicle_id": "10", "leader_id": "20"})
    result = independent_recompute(raw, row)
    assert result["independent_match_status"] == "unique"
    assert abs(result["independent_net_gap_m"] - (15.0 * 0.3048)) < 1e-12
    assert abs(result["independent_closing_speed_mps"] - (10.0 * 0.3048)) < 1e-12
