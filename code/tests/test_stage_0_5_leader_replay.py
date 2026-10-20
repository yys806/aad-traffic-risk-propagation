"""Tests for the leader-trajectory replay module (selection, metrics, guards)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_leader_replay as lr  # noqa: E402


def _pair_frame(step_s: float = 0.1, samples: int = 60, gap_m: float = 12.0, speed: float = 10.0):
    rows = []
    for index in range(samples):
        time_s = round(index * step_s, 4)
        follower_y = 100.0 + speed * time_s
        leader_y = follower_y + gap_m + 4.0
        rows.append(
            {
                "trajectory_id": "follower", "leader_trajectory_id": "leader",
                "time_s": time_s, "y_m": follower_y, "speed_mps": speed, "lane_id": "2",
                "net_gap_m": gap_m, "closing_speed_mps": 0.0, "measurement_status": "valid",
                "identity_break": False, "observation_gap": False, "leader_matched": True,
                "frame_id": index + 1, "global_time_ms": 1000 + index * 100,
            }
        )
    follower = pd.DataFrame(rows)
    leader = follower.assign(
        trajectory_id="leader", leader_trajectory_id=None, y_m=follower.y_m + gap_m + 4.0,
        net_gap_m=np.nan, leader_matched=False,
    )
    return pd.concat([follower, leader], ignore_index=True)


def test_prepare_pairs_builds_one_continuous_run():
    frame = _pair_frame()
    runs, subset = lr.prepare_pairs(frame, window=(0.0, 6.0))
    assert len(runs) == 1
    run = runs.iloc[0]
    assert run.trajectory_id == "follower"
    assert run.leader_trajectory_id == "leader"
    assert run.duration_s >= 5.9
    assert len(subset) > 0


def test_prepare_pairs_splits_on_observation_gap():
    frame = _pair_frame()
    frame.loc[frame.trajectory_id.eq("follower"), "observation_gap"] = False
    follower_index = frame.index[frame.trajectory_id.eq("follower")][30]
    frame.loc[follower_index, "observation_gap"] = True
    runs, _ = lr.prepare_pairs(frame, window=(0.0, 6.0))
    assert len(runs) == 2


def test_pair_observations_infers_the_leader_length_from_positions():
    frame = _pair_frame(gap_m=12.0)
    runs, subset = lr.prepare_pairs(frame, window=(0.0, 6.0))
    observed = lr.pair_observations(subset, runs.iloc[0])
    assert observed.leader_length_inferred_m.iloc[0] == pytest.approx(4.0, abs=1e-6)
    assert observed.gap_definition_residual_m.abs().max() == pytest.approx(0.0, abs=1e-6)


def test_pair_observations_rejects_an_unstable_leader_length():
    frame = _pair_frame()
    follower = frame.trajectory_id.eq("follower")
    frame.loc[follower, "net_gap_m"] = frame.loc[follower, "net_gap_m"].to_numpy() + np.linspace(0, 5, follower.sum())
    runs, subset = lr.prepare_pairs(frame, window=(0.0, 6.0))
    with pytest.raises(lr.LeaderReplayError):
        lr.pair_observations(subset, runs.iloc[0])


def test_configuration_only_allows_tau_to_change():
    params = lr.configuration(1.6)
    assert params["tau"] == 1.6
    assert params["minGap"] == lr.BASELINE_FOLLOWING["minGap"]
    with pytest.raises(lr.LeaderReplayError):
        lr.configuration(1.6, overrides={"minGap": 3.0})
    with pytest.raises(lr.LeaderReplayError):
        lr.configuration(1.6, overrides={"sigma": 0.0})


def test_brockfeld_error_matches_the_published_formula():
    observed = np.array([10.0, 12.0, 14.0])
    simulated = np.array([11.0, 13.0, 13.0])
    expected = (abs(1.0) + abs(1.0) + abs(-1.0)) / (10.0 + 12.0 + 14.0) * 100.0
    assert lr.brockfeld_error(observed, simulated) == pytest.approx(expected)


def test_brockfeld_error_rejects_a_degenerate_denominator():
    with pytest.raises(lr.LeaderReplayError):
        lr.brockfeld_error(np.zeros(3), np.zeros(3))


def test_nrmse_matches_the_published_formula():
    observed = np.array([1.0, 2.0, 2.0])
    simulated = np.array([1.0, 2.0, 3.0])
    expected = np.sqrt(np.mean((observed - simulated) ** 2)) / np.sqrt(np.mean(observed ** 2))
    assert lr.nrmse(observed, simulated) == pytest.approx(expected)


def test_insertion_safe_speed_decreases_with_the_time_gap():
    short = lr.insertion_safe_speed(8.0, 8.0, decel=4.5, tau=1.0)
    long = lr.insertion_safe_speed(8.0, 8.0, decel=4.5, tau=1.6)
    assert short > long > 0


def test_summarise_reports_paired_differences_per_pair_not_per_row():
    rows = [
        {"trajectory_id": "a", "pair_index": 0, "window": "w", "tau_s": 1.0, "brockfeld_gap_error_pct": 20.0,
         "nrmse_gap": 0.2, "nrmse_speed": 0.1, "gap_bias_m": -1.0, "gap_mae_m": 1.0, "speed_bias_mps": 0.0,
         "speed_mae_mps": 0.0, "observed_time_gap_mean_s": 1.0},
        {"trajectory_id": "a", "pair_index": 0, "window": "w", "tau_s": 1.6, "brockfeld_gap_error_pct": 10.0,
         "nrmse_gap": 0.1, "nrmse_speed": 0.1, "gap_bias_m": 0.5, "gap_mae_m": 0.5, "speed_bias_mps": 0.0,
         "speed_mae_mps": 0.0, "observed_time_gap_mean_s": 1.0},
        {"trajectory_id": "b", "pair_index": 1, "window": "w", "tau_s": 1.0, "brockfeld_gap_error_pct": 30.0,
         "nrmse_gap": 0.3, "nrmse_speed": 0.2, "gap_bias_m": -2.0, "gap_mae_m": 2.0, "speed_bias_mps": 0.0,
         "speed_mae_mps": 0.0, "observed_time_gap_mean_s": 2.0},
        {"trajectory_id": "b", "pair_index": 1, "window": "w", "tau_s": 1.6, "brockfeld_gap_error_pct": 40.0,
         "nrmse_gap": 0.4, "nrmse_speed": 0.2, "gap_bias_m": 0.5, "gap_mae_m": 0.5, "speed_bias_mps": 0.0,
         "speed_mae_mps": 0.0, "observed_time_gap_mean_s": 2.0},
    ]
    summary = lr.summarise(rows, resamples=50)
    paired = summary["paired_difference"]
    assert paired["paired_pairs"] == 2
    # -10 and +10 average to zero, one improved and one worsened
    assert paired["brockfeld_gap_error_pct"]["mean_difference"] == pytest.approx(0.0)
    assert paired["brockfeld_gap_error_pct"]["improved_pairs"] == 1
    assert paired["brockfeld_gap_error_pct"]["worsened_pairs"] == 1
