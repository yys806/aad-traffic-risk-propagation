from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/scripts"))
import analyze_stage_0_5_round2_task4_real_source_support as task4  # noqa: E402


def test_onset_attribution_keeps_unmatched_and_ambiguous_unknown() -> None:
    frame = pd.DataFrame(
        [
            {"trajectory_id": "f", "time_s": 1.0, "lane_id": "1", "y_m": 10.0},
            {"trajectory_id": "amb", "time_s": 1.0, "lane_id": "1", "y_m": 10.0},
            {"trajectory_id": "amb", "time_s": 1.0, "lane_id": "1", "y_m": 11.0},
        ]
    )
    events = pd.DataFrame(
        [
            {"event_id": "unique", "trajectory_id": "f", "event_start_s": 1.0},
            {"event_id": "missing", "trajectory_id": "missing", "event_start_s": 1.0},
            {"event_id": "ambiguous", "trajectory_id": "amb", "event_start_s": 1.0},
        ]
    )
    result = task4.attribute_event_onsets(frame, events)
    assert result["unique"] == 1
    assert result["unmatched"] == 1
    assert result["ambiguous"] == 1
    assert result["source"] == 1
    assert result["auxiliary_or_other"] == 0
    assert result["unknown"] == 2
    assert result["conservation_pass"]


def test_block_rows_uses_actual_partial_end_duration() -> None:
    rows = []
    for time_s in [0.0, 0.1, 29.9, 30.0, 45.0]:
        rows.append(
            {
                "lane_id": "1", "y_m": 10.0, "time_s": time_s, "vehicle_id": "v",
                "speed_mps": 10.0, "acceleration_mps2": 0.0, "net_gap_m": 10.0,
                "closing_speed_mps": 0.0, "ttc_valid": False, "ttc_s": float("nan"),
                "measurement_status": "not_applicable",
            }
        )
    frame = pd.DataFrame(rows)
    blocks = task4.block_rows(frame, dataset="NGSIM", scope="test", region_name="source", region=task4.SOURCE, start=0.0, end=60.0)
    last = [row for row in blocks if row["time_block"] == 1][0]
    assert last["nominal_block_start_s"] == 30.0
    assert last["nominal_block_end_s"] == 60.0
    assert last["block_start_s"] == 30.0
    assert last["block_end_s"] == 45.1
    assert abs(last["effective_duration_s"] - 15.1) < 1e-12


def test_task4_historical_package_is_present_and_sealed() -> None:
    package = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030"
    assert (package / "SHA256SUMS").is_file()
    assert (package / "manifest.json").is_file()
