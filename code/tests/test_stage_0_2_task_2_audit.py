import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_stage_0_2_task_2_audit import quality_summary, quantile_summary


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "speed_mps": [10.0, 12.0], "acceleration_mps2": [0.1, -0.2],
            "raw_space_headway_ft": [30.0, 40.0], "net_gap_m": [5.0, 8.0],
            "closing_speed_mps": [2.0, 0.0], "ttc_s": [2.5, float("inf")],
            "drac_mps2": [0.4, float("nan")], "measurement_status": ["valid", "not_applicable"],
            "leader_matched": [True, False], "single_frame_reliable": [True, False],
            "ttc_valid": [True, False], "identity_uncertain": [False, False],
            "leader_identity_uncertain": [False, False], "observation_gap": [False, False],
            "identity_break": [False, False],
        }
    )


def test_task_2_quality_summary_keeps_status_denominators_and_finite_masks():
    summary = quality_summary(_fixture())
    assert summary["rows"] == 2
    assert summary["measurement_status"]["valid"]["n"] == 1
    assert summary["measurement_status"]["not_applicable"]["fraction_of_rows"] == 0.5
    assert summary["finite_ttc"]["n"] == 1
    assert summary["nan_or_inf_ttc"] == 1
    assert summary["subset_counts"]["mathematically_valid_ttc"] == 1


def test_task_2_quantiles_exclude_nonfinite_values():
    result = quantile_summary(_fixture(), "ttc_s")
    assert result["n"] == 1
    assert result["min"] == 2.5
    assert result["max"] == 2.5
