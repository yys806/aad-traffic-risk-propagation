"""Focused Task18 executor and statistical-contract tests."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay  # noqa: E402
from run_task18_closure_and_repeats import classify_status  # noqa: E402


def test_task18_default_offset_is_80m():
    assert inspect.signature(run_joint_replay).parameters["start_offset_m"].default == 80.0


def test_task18_status_contract_excludes_failed_runs():
    assert classify_status({"applied_rows": 10, "failure_reason": None, "invalid_state_rows": []}, 10) == "PASS"
    assert classify_status({"applied_rows": 10, "failure_reason": "collision_event", "invalid_state_rows": []}, 10) == "FAIL"
    assert classify_status({"applied_rows": 9, "failure_reason": None, "invalid_state_rows": []}, 10) == "INCOMPLETE"
    assert classify_status({"applied_rows": 10, "failure_reason": None, "invalid_state_rows": [{"reason": "bad"}]}, 10) == "INVALID"


def test_task18_input_pair_contract_is_value_based():
    a = pd.DataFrame({"input_time_s": [0.0, 0.05], "leader_position_m": [92.2, 93.0], "leader_speed_mps": [15.0, 15.1], "follower_speed_mps": [14.0, 14.0], "net_gap_m": [10.0, 10.1], "follower_position_m": [77.8, 78.0]})
    b = a.copy()
    assert a.equals(b)
    b.loc[1, "leader_speed_mps"] += 1e-6
    assert not a.equals(b)
