"""Targeted tests for Task9's fail-closed fixed-leader contract."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riskprop import stage_0_5_fixed_leader_pair as flp  # noqa: E402


def _arm(follower_shift: float = 0.0):
    time = np.arange(0.0, 5.0 + 1e-9, 0.1)
    leader_speed = 12.0 - 0.8 * np.sin(time / 2.0)
    follower_speed = 11.0 - 0.4 * np.sin(time / 2.0) + follower_shift * (time / 5.0)
    gap = 10.0 - np.cumsum(np.r_[0.0, np.diff(time) * (leader_speed[:-1] - follower_speed[:-1])])
    return pd.DataFrame({
        "time_s": time,
        "leader_y_m": 100.0 + np.cumsum(np.r_[0.0, np.diff(time) * leader_speed[:-1]]),
        "leader_speed_mps": leader_speed,
        "follower_speed_mps": follower_speed,
        "net_gap_m": gap,
    })


def test_sealed_arms_differ_only_in_min_gap():
    run_root = ROOT / "outputs" / "formal" / "calibration" / "stage_0_5_ready_to_admit_v3" / "runs"
    a = run_root / "WEEK_0750_B00_IC1_s20261201_A03"
    b = run_root / "AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1"
    result = flp.audit_arm_configs(a / "routes.rou.xml", b / "routes.rou.xml", a / "network.net.xml", b / "network.net.xml", a / "run.sumocfg", b / "run.sumocfg")
    assert len(result["differences"]) == 5
    assert result["tau_heterogeneity"] == list(flp.TAU_VALUES)


def test_common_input_cancellation_reports_delta_c_equals_delta_cf():
    a = _arm()
    b = _arm(follower_shift=0.5)
    result = flp.compare_arms(a, b)
    assert result["exact_cancellation_checked"] is True
    assert result["differences"]["delta_C_initial_m"] == pytest.approx(0.0)
    assert result["differences"]["delta_C_l_m"] == pytest.approx(0.0)
    assert result["differences"]["delta_C_m"] == pytest.approx(result["differences"]["delta_C_f_m"])


def test_common_input_rejects_leader_change_and_initial_mismatch():
    a = _arm()
    changed_leader = a.copy()
    changed_leader.loc[10, "leader_speed_mps"] += 0.01
    with pytest.raises(flp.FixedLeaderPairError, match="leader_input_mismatch"):
        flp.validate_common_input(a, changed_leader)
    changed_initial = a.copy()
    changed_initial.loc[0, "follower_speed_mps"] += 0.01
    with pytest.raises(flp.FixedLeaderPairError, match="initial_state_mismatch"):
        flp.validate_common_input(a, changed_initial)
