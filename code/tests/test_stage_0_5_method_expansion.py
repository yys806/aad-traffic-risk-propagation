"""Tests for the AAD-0.5-METHOD-EXPANSION additions."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_leader_replay as lr  # noqa: E402
from riskprop import stage_0_5_newell_prototype as nl  # noqa: E402


def _observed(samples: int = 60, gap_m: float = 12.0, speed: float = 10.0, decel_at: int | None = None):
    times = np.round(np.arange(samples) * 0.1, 4)
    follower_speed = np.full(samples, float(speed))
    if decel_at is not None:
        # the follower responds with a smaller, delayed drop so that the amplitude
        # ratio and the lag are defined and comparable
        start = min(decel_at + 5, samples - 1)
        follower_speed[start:start + 10] = speed - 1.0 * (np.arange(min(10, samples - start)) + 1) / 10.0
    follower_y = 100.0 + np.cumsum(follower_speed) * 0.1
    leader_speed = np.full(samples, float(speed))
    if decel_at is not None:
        # ramp over 1.0 s so the derived acceleration stays below -0.5 m/s^2 long
        # enough to satisfy the declared episode duration rule
        leader_speed[decel_at:decel_at + 10] = speed - 3.0 * (np.arange(10) + 1) / 10.0
    # the leader's position must integrate its own speed series, otherwise a
    # deceleration profile would not appear in the derived acceleration at all
    leader_y = (follower_y[0] + gap_m + 4.4196) + np.cumsum(leader_speed) * 0.1
    frame = pd.DataFrame({
        "time_s": times,
        "leader_y_m": leader_y,
        "leader_speed_mps": leader_speed,
        "follower_y_m": follower_y,
        "follower_speed_mps": follower_speed,
        "observed_gap_m": gap_m,
        "reported_gap_m": gap_m,
        "gap_definition_residual_m": 0.0,
        "leader_length_inferred_m": 4.4196,
        "leader_length_inference_spread_m": 0.0,
        "net_gap_m": gap_m,
        "closing_speed_mps": 0.0,
        "lane_id": "2",
    })
    return frame


def test_configuration_catalogue_is_single_factor_and_frozen_elsewhere():
    assert lr.assert_single_factor("K_tau1.6")["changed"] == ["tau"]
    assert lr.assert_single_factor("K_tau1.0_minGap5.0")["changed"] == ["minGap"]
    assert lr.assert_single_factor("K_tau1.0_sigma0.0")["changed"] == ["sigma"]
    for name in lr.CONFIGURATIONS:
        params = lr.build_vtype(name)
        for key in ("accel", "decel", "maxSpeed", "actionStepLength"):
            assert params[key] == lr.BASELINE_FOLLOWING[key], f"{name} changed {key}"


def test_build_vtype_sets_the_model_and_delta_only_for_idm():
    krauss = lr.build_vtype("K_tau1.0")
    assert krauss["carFollowModel"] == "Krauss"
    assert "delta" not in krauss
    idm = lr.build_vtype("IDM_T1.6")
    assert idm["carFollowModel"] == "IDM"
    assert idm["tau"] == 1.6 and idm["delta"] == 4.0


def test_unknown_configuration_is_rejected():
    with pytest.raises(lr.LeaderReplayError):
        lr.build_vtype("K_tau9.9")


def test_slice_record_keeps_observed_and_simulated_aligned():
    observed = _observed(samples=60)
    simulated = pd.DataFrame({
        "t": observed.time_s.to_numpy(),
        "leader_y": observed.leader_y_m.to_numpy(),
        "leader_target_y": observed.leader_y_m.to_numpy(),
        "follower_y": observed.follower_y_m.to_numpy(),
        "follower_v": observed.follower_speed_mps.to_numpy(),
        "leader_v": observed.leader_speed_mps.to_numpy(),
        "gap_m": observed.observed_gap_m.to_numpy(),
    })
    record = {"observed": observed, "simulated": simulated, "run_id": 1, "trajectory_id": "t",
              "leader_trajectory_id": "l", "lane_id": "2", "seed": 0, "tau_s": 1.0,
              "duration_s": 6.0, "leader_target_max_abs_deviation_m": 0.0,
              "vehicle_length_m": 4.4196, "leader_length_inference_spread_m": 0.0,
              "initial_speed_offset_mps": 0.0}
    sliced = lr.slice_record(record, start_s=0.0, end_s=5.0)
    assert len(sliced["observed"]) == len(sliced["simulated"]) == 51
    later = lr.slice_record(record, start_s=5.0, end_s=None)
    assert len(later["observed"]) == len(later["simulated"])


def test_brake_episodes_respects_threshold_and_duration():
    times = np.arange(0, 5.0, 0.1)
    acceleration = np.full(len(times), 0.1)
    acceleration[10:20] = -1.0
    episodes = lr.brake_episodes(acceleration, times)
    assert len(episodes) == 1
    assert episodes[0]["start_index"] == 10
    brief = np.full(len(times), 0.1)
    brief[10:12] = -1.0
    assert lr.brake_episodes(brief, times) == []


def test_response_metrics_reports_amplitude_and_lag_for_a_braking_leader():
    observed = _observed(samples=120, decel_at=20)
    simulated = pd.DataFrame({
        "t": observed.time_s.to_numpy(),
        "leader_y": observed.leader_y_m.to_numpy(),
        "leader_target_y": observed.leader_y_m.to_numpy(),
        "follower_y": observed.follower_y_m.to_numpy(),
        "follower_v": observed.follower_speed_mps.to_numpy(),
        "leader_v": observed.leader_speed_mps.to_numpy(),
        "gap_m": observed.observed_gap_m.to_numpy(),
    })
    # leader decelerates by 3 m/s, so its derived acceleration is strongly negative
    metrics = lr.response_metrics({"observed": observed, "simulated": simulated})
    assert metrics["series"][0]["episodes"] >= 1
    # observed and simulated series are identical here, so the drop ratio is exactly 1
    assert metrics["amplitude_ratio_sim_over_obs"] == pytest.approx(1.0, abs=1e-9)
    assert metrics["lag_difference_s"] == pytest.approx(0.0, abs=1e-9)


def test_stratified_selection_covers_more_than_one_stratum():
    runs = pd.DataFrame([
        {"run_id": 1, "trajectory_id": "a", "duration_s": 20.0, "gap_mean_m": 5.0, "speed_mean_mps": 10.0},
        {"run_id": 2, "trajectory_id": "b", "duration_s": 19.0, "gap_mean_m": 12.0, "speed_mean_mps": 10.0},
        {"run_id": 3, "trajectory_id": "c", "duration_s": 18.0, "gap_mean_m": 18.0, "speed_mean_mps": 10.0},
        {"run_id": 4, "trajectory_id": "d", "duration_s": 17.0, "gap_mean_m": 40.0, "speed_mean_mps": 10.0},
    ])
    picked = lr.stratified_selection(runs, per_window=4)
    assert picked.run_id.nunique() == 4
    assert picked.observed_time_gap_s.max() >= 3.0
    assert picked.observed_time_gap_s.min() <= 1.0


def test_newell_prototype_keeps_the_safety_gap_and_respects_free_speed():
    observed = _observed(samples=80, gap_m=30.0, speed=20.0)
    simulated = nl.simulate_newell(observed, tau=1.0)
    assert (simulated.gap_m > -1e-6).all(), "prototype must not close within the minimum spacing"
    assert (simulated.follower_v <= 27.78 + 1e-9).all()
    assert len(simulated) == len(observed)


def test_newell_prototype_slows_down_when_the_leader_decelerates():
    observed = _observed(samples=120, gap_m=15.0, speed=15.0, decel_at=30)
    observed.loc[30:, "leader_y_m"] = observed.loc[30, "leader_y_m"] + np.minimum(
        np.arange(len(observed) - 30) * 1.2, 60.0)
    simulated = nl.simulate_newell(observed, tau=1.0)
    assert simulated.follower_v.iloc[-1] < simulated.follower_v.iloc[0]


def test_newell_record_satisfies_the_replay_metric_contract():
    observed = _observed(samples=60)
    record = nl.newell_record(observed, tau=1.0, run_id=7, trajectory_id="x", lane_id="2")
    metrics = lr.pair_metrics(record)
    assert metrics["run_id"] == 7
    assert metrics["states"] == 60
    assert metrics["nrmse_acceleration"] is None
    assert "not validated" in metrics["nrmse_acceleration_reason"]
