"""Regression tests for the conditional state-support module and runner."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from riskprop import stage_0_5_state_support as ss


def _real_like_frame(n_blocks: int = 12) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(7)
    for block in range(n_blocks):
        density = 20.0 + block * 3.0
        speed = 16.0 - block * 0.8
        for vehicle in range(40):
            rows.append({
                "window_id": "0750_0805",
                "trajectory_id": f"t{block:02d}_{vehicle:03d}",
                "time_s": 120.0 + block * 0.1 + vehicle * 1e-4,
                "y_m": 150.0 + (vehicle % 20) * 10.0,
                "speed_mps": max(speed + rng.normal(0.0, 0.4), 0.2),
                "lane_id": str(1 + vehicle % 5),
                "net_gap_m": max(speed + rng.normal(0.0, 0.5), 0.5),
                "closing_speed_mps": rng.normal(-0.1, 0.6),
                "measurement_status": "valid",
                "leader_matched": True,
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# real following relation
# --------------------------------------------------------------------------
def _following_frame(tau: float, min_gap: float, *, speeds=None, rows: int = 60) -> pd.DataFrame:
    speeds = np.linspace(4.0, 20.0, 80) if speeds is None else np.asarray(speeds, dtype=float)
    records = []
    for index, speed in enumerate(speeds):
        for step in range(rows):
            records.append({
                "window_id": "0750_0805",
                "trajectory_id": f"t{index:03d}",
                "time_s": 120.0 + step * 0.1,
                "y_m": 200.0,
                "speed_mps": float(speed),
                "lane_id": "1",
                "net_gap_m": float(min_gap + tau * speed),
                "closing_speed_mps": 0.0,
                "measurement_status": "valid",
                "leader_matched": True,
            })
    return pd.DataFrame(records)


def test_following_relation_recovers_a_known_time_headway():
    tau, min_gap = 1.5, 2.5
    frame = _following_frame(tau, min_gap)
    relation = ss.following_relation(frame, min_gap_m=min_gap)
    assert relation["tau_eff_ratio_s"] == pytest.approx(tau, rel=1e-9)
    assert relation["ols_binned_slope_s"] == pytest.approx(tau, rel=1e-6)
    assert relation["ols_binned_intercept_m"] == pytest.approx(min_gap, rel=1e-6)
    expected = 3600.0 / (tau + (ss.VEHICLE_LENGTH_M + min_gap) / ss.FREE_SPEED_MPS)
    assert relation["analytic_lane_capacity_ratio_veh_h"] == pytest.approx(expected, rel=1e-9)
    assert relation["not_a_science_tolerance"] is True


def test_following_relation_is_population_level_not_a_stratified_subsample():
    """One very close follower must not move the population estimator much."""
    frame = _following_frame(1.5, 2.5)
    baseline = ss.following_relation(frame)["tau_eff_ratio_s"]
    tail = frame.copy()
    mask = tail.trajectory_id == "t000"
    tail.loc[mask, "net_gap_m"] = 2.6
    tail.loc[mask, "speed_mps"] = 10.0
    shifted = ss.following_relation(tail)["tau_eff_ratio_s"]
    assert abs(shifted - baseline) < 0.05


# --------------------------------------------------------------------------
# envelopes
# --------------------------------------------------------------------------
def test_support_envelope_and_membership_are_data_derived():
    cloud = pd.DataFrame({
        "density_veh_km_lane": np.repeat([15.0, 45.0, 70.0], 10),
        "speed_mean_mps": np.concatenate([np.linspace(12.0, 15.0, 10),
                                          np.linspace(8.0, 11.0, 10),
                                          np.linspace(3.0, 5.0, 10)]),
        "closing_speed_mean_mps": np.concatenate([np.linspace(-0.4, 0.2, 10),
                                                  np.linspace(-0.6, 0.4, 10),
                                                  np.linspace(-0.2, 0.1, 10)]),
    })
    envelope = ss.support_envelope(cloud)
    assert envelope["density_min_veh_km_lane"] == pytest.approx(15.0)
    assert envelope["density_max_veh_km_lane"] == pytest.approx(70.0)
    inside = ss.envelope_membership(45.0, 9.5, envelope)
    assert inside["inside"] is True
    outside_speed = ss.envelope_membership(45.0, 20.0, envelope)
    assert outside_speed["inside"] is False
    assert outside_speed["reason"] == "speed_outside_observed_band"
    outside_density = ss.envelope_membership(5.0, 9.5, envelope)
    assert outside_density["inside"] is False
    assert outside_density["reason"] == "density_outside_observed_range"
    assert ss.envelope_coverage(cloud, envelope) == pytest.approx(0.9, abs=0.15)

    closing = ss.closing_envelope(cloud)
    assert ss.closing_membership(45.0, -0.2, closing)["inside"] is True
    assert ss.closing_membership(45.0, 3.0, closing)["inside"] is False


# --------------------------------------------------------------------------
# declared construction
# --------------------------------------------------------------------------
def test_declared_behaviour_arms_are_single_factor():
    relation = {
        "tau_eff_ratio_s": 1.55,
        "vehicle_tau_eff_quantile_levels": [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95],
        "vehicle_tau_eff_quantiles_s": [0.6, 0.7, 1.0, 1.35, 1.9, 2.5, 3.0],
    }
    frozen = ss.declared_behaviour_vtypes("B_frozen", relation)
    mean = ss.declared_behaviour_vtypes("B_mean", relation)
    het = ss.declared_behaviour_vtypes("B_het", relation)
    assert [entry["tau"] for entry in frozen] == [1.0]
    assert [entry["tau"] for entry in mean] == [pytest.approx(1.55)]
    assert len(het) == len(ss.HETEROGENEITY_QUANTILES)
    taus = [entry["tau"] for entry in het]
    assert taus == sorted(taus)
    assert min(taus) < 1.0 < max(taus)
    for entry in frozen + mean + het:
        assert entry["sigma"] == 0.5
        assert entry["kind"] == "passenger"
    with pytest.raises(ss.StateSupportError):
        ss.declared_behaviour_vtypes("B_unknown", relation)


def test_geometry_spec_lane_counts_and_downstream_restriction():
    baseline = ss.observed_geometry_spec(ss.FREE_SPEED_MPS)
    restricted = ss.observed_geometry_spec(10.0)
    drop = ss.observed_geometry_spec(ss.FREE_SPEED_MPS, 4)
    assert [edge["lanes"] for edge in baseline["edges"]] == [5, 6, 5, 1, 1]
    assert [edge["lanes"] for edge in drop["edges"]] == [5, 6, 4, 1, 1]
    assert restricted["edges"][2]["speed_mps"] == pytest.approx(10.0)
    assert restricted["edges"][0]["speed_mps"] == pytest.approx(ss.FREE_SPEED_MPS)
    assert baseline["routes"]["through"] == ["main_0", "main_1", "main_2"]


def test_supply_capacity_uses_the_krauss_equilibrium_form():
    slow = ss.supply_capacity_veh_h(10.0, 1.0)
    fast = ss.supply_capacity_veh_h(27.78, 1.0)
    longer_headway = ss.supply_capacity_veh_h(27.78, 1.6)
    assert slow < fast
    assert longer_headway < fast
    assert fast == pytest.approx(3600.0 * 27.78 / (27.78 + ss.VEHICLE_LENGTH_M + ss.MIN_GAP_M) * 5)
    assert ss.supply_capacity_veh_h(27.78, 1.5, lanes=4) == pytest.approx(
        4 / 5 * ss.supply_capacity_veh_h(27.78, 1.5))


def test_depart_times_are_deterministic_and_bounded():
    first = ss.depart_times(3600.0, 100.0, 0.5)
    second = ss.depart_times(3600.0, 100.0, 0.5)
    assert np.array_equal(first, second)
    assert first.min() >= 0.0 and first.max() < 100.0
    assert len(first) == 100


# --------------------------------------------------------------------------
# simulator-native following measurement (regression for the leader sign bug)
# --------------------------------------------------------------------------
def test_fcd_leader_is_ahead_and_gap_is_positive():
    frame = pd.DataFrame({
        "time_s": [0.0, 0.0, 0.1, 0.1],
        "vehicle_id": ["lead", "follow", "lead", "follow"],
        "edge": ["main_0"] * 4,
        "lane_index": [0, 0, 0, 0],
        "y_m": [100.0, 80.0, 101.0, 81.0],
        "speed_mps": [10.0, 10.0, 10.0, 10.0],
        "lane_id": ["5", "5", "5", "5"],
    })
    lengths = {"lead": 4.0, "follow": 4.0}
    frame["native_position_m"] = frame.y_m
    frame["native_lane_id"] = frame.edge + "_" + frame.lane_index.astype(str)
    states = ss.fcd_to_state_frame(frame, lengths, run_id="r", scenario_id="s", seed=1)
    follower = states[states.vehicle_id == "follow"].sort_values("time_s")
    assert follower.leader_id.tolist() == ["lead", "lead"]
    assert follower.net_gap_m.to_numpy() == pytest.approx([16.0, 16.0])
    assert follower.leader_incarnation_id.tolist() == ["lead", "lead"]
    lead = states[states.vehicle_id == "lead"]
    assert lead.leader_id.isna().all()


def test_measure_state_frame_marks_non_closing_as_not_applicable():
    frame = pd.DataFrame({
        "time_s": [0.0, 0.0, 0.1, 0.1],
        "vehicle_id": ["lead", "follow", "lead", "follow"],
        "edge": ["main_0"] * 4,
        "lane_index": [0, 0, 0, 0],
        "y_m": [100.0, 80.0, 100.5, 80.6],
        "speed_mps": [10.0, 9.0, 10.0, 9.5],
        "lane_id": ["5", "5", "5", "5"],
    })
    frame["native_position_m"] = frame.y_m
    frame["native_lane_id"] = frame.edge + "_" + frame.lane_index.astype(str)
    states = ss.fcd_to_state_frame(frame, {"lead": 4.0, "follow": 4.0},
                                   run_id="r", scenario_id="s", seed=1)
    measured = ss.measure_state_frame(states)
    follower = measured[measured.vehicle_id == "follow"]
    assert set(follower.measurement_status) <= {"valid", "not_applicable", "invalid", "missing"}
    assert (follower.closing_speed_mps < 0).all()


# --------------------------------------------------------------------------
# isolation
# --------------------------------------------------------------------------
def test_locked_holdout_is_refused_by_construction():
    for bad in ("nsgim_lankershim__complete", "i80", "peachtree", "spmd2014"):
        with pytest.raises(ss.StateSupportError, match="locked_holdout_refused"):
            ss._assert_not_holdout(bad)
    ss._assert_not_holdout("us101__0750_0805")
    ss._assert_not_holdout(ss.VALIDATION_WINDOW)


def test_approved_spans_cover_the_three_windows():
    assert set(ss.APPROVED_SPANS) == set(ss.CALIBRATION_WINDOWS) | {ss.VALIDATION_WINDOW}
    assert ss.APPROVED_SPANS[ss.VALIDATION_WINDOW] == ss.VALIDATION_WINDOW_SPAN
