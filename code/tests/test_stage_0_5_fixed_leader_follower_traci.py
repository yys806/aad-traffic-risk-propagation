"""Targeted tests for the Task16 engineering-only joint replay adapter."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay  # noqa: E402
from riskprop.stage_0_5_fixed_leader_pair import FixedLeaderPairError  # noqa: E402


def test_joint_replay_requires_follower_input_fields_before_starting_sumo():
    with pytest.raises(FixedLeaderPairError, match="missing_joint_trace_columns"):
        run_joint_replay(
            pd.DataFrame({"relative_time_s": [0.0, 0.05], "leader_y_m": [10.0, 10.5], "leader_speed_mps": [10.0, 10.0]}),
            sumo_cfg=Path("missing.sumocfg"),
            lane_id="main_ext_1",
            geometry_follower_length_m=5.0,
            geometry_leader_length_m=5.0,
            follower_tau_s=1.0,
            follower_min_gap_m=2.5,
        )


def test_joint_replay_rejects_unknown_initialization_mode():
    trace = pd.DataFrame({
        "relative_time_s": [0.0, 0.05],
        "leader_y_m": [10.0, 10.5],
        "leader_speed_mps": [10.0, 10.0],
        "follower_speed_mps": [9.0, 9.0],
        "net_gap_m": [8.0, 8.0],
    })
    with pytest.raises(FixedLeaderPairError, match="unsupported_initialization_mode"):
        run_joint_replay(
            trace,
            sumo_cfg=Path("missing.sumocfg"),
            lane_id="main_ext_1",
            geometry_follower_length_m=5.0,
            geometry_leader_length_m=5.0,
            follower_tau_s=1.0,
            follower_min_gap_m=2.5,
            initialization_mode="unknown",
        )
