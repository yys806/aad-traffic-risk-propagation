from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/scripts"))
import analyze_stage_0_5_round2_task4_real_source_support as task4  # noqa: E402


def _real_rows() -> pd.DataFrame:
    rows = []
    statuses = ["valid", "not_applicable", "missing"]
    for i, status in enumerate(statuses):
        rows.append({
            "dataset": "NGSIM", "site": "US-101", "window_id": "test",
            "source_member": "member", "source_period": "period",
            "trajectory_id": "f", "leader_trajectory_id": "l",
            "diagnostic_clock_anchor_ms": 1000, "global_time_ms": 1000 + 100 * i,
            "time_s": i * 0.1, "frame_id": i,
            "identity_break": False, "observation_gap": False,
            "leader_matched": True, "identity_uncertain": False,
            "leader_identity_uncertain": False, "measurement_status": status,
            "lane_id": "1", "y_m": 10.0 + i, "vehicle_id": "f",
        })
    return pd.DataFrame(rows)


def test_point_region_excludes_auxiliary_and_uses_half_open_bounds() -> None:
    frame = pd.DataFrame({"lane_id": ["1", "6", "5"], "y_m": [0.0, 20.0, 150.0]})
    assert task4.point_region(frame, task4.SOURCE).tolist() == [True, False, False]
    assert task4.point_region(frame, task4.TARGET).tolist() == [False, False, True]


def test_real_exposure_uses_both_endpoint_statuses_and_no_final_extrapolation() -> None:
    result = task4.exposure_summary(_real_rows(), real=True)
    assert result["reliable_edges"] == 2
    assert result["reliable_exposure_s"] == 0.2
    assert result["p2_evaluable_edges"] == 1
    assert result["p2_evaluable_exposure_s"] == 0.1
    assert result["not_evaluable_exposure_s"] == 0.1


def test_route_inventory_scope_matches_bound_c_input_route() -> None:
    path = ROOT / "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/routes.rou.xml"
    assert len(task4.cohort_ids(path)) == 1112
