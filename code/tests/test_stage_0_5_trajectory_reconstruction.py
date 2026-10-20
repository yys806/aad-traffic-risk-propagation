"""Tests for the read-only real traffic reconstruction module."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_trajectory_reconstruction as tr  # noqa: E402


def _frame(lanes=("1",), *, n_vehicles=30, spacing_m=20.0, speed=0.0, steps=10, dt=0.1, y0=0.0):
    """Uniform synthetic stream: vehicle v on each lane starts at y0 + v*spacing."""
    records = []
    for lane in lanes:
        for vehicle in range(n_vehicles):
            start = y0 + vehicle * spacing_m
            for step in range(steps):
                records.append(
                    {
                        "dataset": "NGSIM", "site": "US-101", "window_id": "0750_0805",
                        "vehicle_id": f"{lane}-{vehicle:03d}", "trajectory_id": f"t{lane}-{vehicle:03d}",
                        "time_s": round(step * dt, 4), "y_m": start + speed * step * dt,
                        "x_m": float(lane) * 3.5, "speed_mps": speed, "acceleration_mps2": 0.0,
                        "lane_id": lane, "net_gap_m": spacing_m - 4.4, "closing_speed_mps": 0.0,
                        "measurement_status": "valid", "identity_break": False, "observation_gap": False,
                        "original_row_number": vehicle * steps + step, "source_member": "synthetic",
                        "missing_reason": "", "ttc_s": 100.0, "leader_matched": True,
                    }
                )
    return pd.DataFrame(records).sort_values(["trajectory_id", "time_s"]).reset_index(drop=True)


def test_sealed_window_is_refused():
    with pytest.raises(tr.TrajectoryReconstructionError):
        tr.load_calibration_states("does-not-exist.parquet", "us101__0820_0835")


def test_unapproved_window_id_is_refused():
    with pytest.raises(tr.TrajectoryReconstructionError):
        tr.load_calibration_states("does-not-exist.parquet", "us101__0900_0915")


def test_boundary_crossing_count_and_interpolated_time():
    # vehicles are 20 m apart moving at 10 m/s; over 5 s each advances 50 m
    frame = _frame(n_vehicles=40, spacing_m=20.0, speed=10.0, steps=50, y0=0.0)
    crossings = tr.boundary_crossings(frame, at_m=150.0, lanes=("1",), window=(0.0, 5.0))
    # starts 0,20,...,780: only 120 m and 140 m cross y=150 inside [0,5); the 100 m
    # vehicle crosses exactly at t=5.0 and the half-open window excludes it
    assert len(crossings) == 2
    assert sorted(crossings.time_s.tolist()) == pytest.approx([1.0, 3.0])


def test_conservation_closes_for_a_uniform_flow():
    frame = _frame(n_vehicles=40, spacing_m=20.0, speed=10.0, steps=50, y0=0.0)
    report = tr.vehicle_conservation(
        frame, region=(100.0, 300.0), lanes_in=("1",), lanes_out=("1",), window=(0.0, 5.0),
        edge_average_s=1.0,
    )
    assert report["cross_section_identical"] is True
    # start occupancy 10 vehicles in [100,300), end occupancy 10 vehicles: delta 0,
    # in and out counts agree because the stream is uniform
    assert report["entered"] == report["exited"]
    assert abs(report["conservation_residual_vehicles"]) <= 1


def test_local_state_density_on_a_frozen_uniform_stream():
    # 20 m spacing => 50 veh/km/lane; frozen stream so the time average is exact
    frame = _frame(lanes=("1", "2", "3", "4", "5"), n_vehicles=30, spacing_m=20.0, speed=0.0, steps=50)
    state = tr.local_state(frame, window=(0.0, 5.0))
    assert state["lane_km"] == pytest.approx((tr.REGION_END_M - tr.REGION_START_M) / 1000.0 * 5)
    assert state["density_veh_km_lane"] == pytest.approx(50.0, rel=1e-9)
    assert state["flow_veh_h_lane_consistency"] == pytest.approx(0.0, abs=1e-9)


def test_local_state_flow_is_density_times_speed():
    frame = _frame(lanes=("1", "2"), n_vehicles=30, spacing_m=20.0, speed=12.0, steps=50)
    state = tr.local_state(frame, window=(0.0, 5.0))
    assert state["flow_veh_h_lane_consistency"] == pytest.approx(
        state["density_veh_km_lane"] * state["speed_mean_mps"] * 3.6, rel=1e-12
    )


def test_classify_lanes_rejects_short_mainline_support():
    geometry = pd.DataFrame(
        [
            {"lane_id": lane, "y_min_m": 0.0, "y_max_m": (100.0 if lane == "1" else 660.0)}
            for lane in ("1", "2", "3", "4", "5")
        ]
    )
    with pytest.raises(tr.TrajectoryReconstructionError):
        tr.classify_lanes(geometry)


def test_classify_lanes_accepts_the_observed_chain():
    geometry = pd.DataFrame(
        [
            {"lane_id": "1", "y_min_m": 0.0, "y_max_m": 660.0},
            {"lane_id": "2", "y_min_m": 0.0, "y_max_m": 660.0},
            {"lane_id": "3", "y_min_m": 0.0, "y_max_m": 660.0},
            {"lane_id": "4", "y_min_m": 0.0, "y_max_m": 660.0},
            {"lane_id": "5", "y_min_m": 0.0, "y_max_m": 660.0},
            {"lane_id": "6", "y_min_m": 187.6, "y_max_m": 399.2},
            {"lane_id": "7", "y_min_m": 128.7, "y_max_m": 187.6},
            {"lane_id": "8", "y_min_m": 399.2, "y_max_m": 450.8},
        ]
    )
    roles = tr.classify_lanes(geometry)
    assert roles["mainline_lanes"] == ["1", "2", "3", "4", "5"]
    assert roles["auxiliary_lane"] == "6"
    assert roles["onramp_lane"] == "7"
    assert roles["offramp_lane"] == "8"


def test_real_region_mask_matches_the_approved_d1_region():
    frame = _frame(lanes=("1", "2", "9"), n_vehicles=30, spacing_m=20.0)
    mask = tr.real_region_mask(frame)
    selected = frame[mask]
    assert selected.lane_id.isin(["1", "2"]).all()
    assert selected.y_m.ge(tr.REGION_START_M).all() and selected.y_m.lt(tr.REGION_END_M).all()


def test_fundamental_diagram_flow_matches_density_times_speed():
    frame = _frame(lanes=("1",), n_vehicles=40, spacing_m=20.0, speed=8.0, steps=40)
    table = tr.fundamental_diagram(frame, window=(0.0, 3.9), y_step_m=100.0, t_step_s=1.0)
    assert not table.empty
    assert np.allclose(table.flow_veh_h_lane, table.density_veh_km_lane * table.speed_mean_mps * 3.6, rtol=1e-9)


def test_cluster_bootstrap_is_deterministic_and_brackets_the_point():
    frame = _frame(lanes=("1", "2"), n_vehicles=30, spacing_m=15.0, speed=11.0, steps=40)
    first = tr.cluster_bootstrap(frame, window=(0.0, 3.9), metric="speed", resamples=200, seed=7)
    second = tr.cluster_bootstrap(frame, window=(0.0, 3.9), metric="speed", resamples=200, seed=7)
    assert first == second
    assert first.low <= first.point <= first.high


def test_jam_waves_finds_a_wave_when_speed_drops():
    frame = _frame(lanes=("1",), n_vehicles=60, spacing_m=10.0, speed=0.0, steps=60)
    waves = tr.jam_waves(frame, window=(0.0, 5.9), threshold_mps=1.0, y_step_m=50.0, t_step_s=1.0)
    assert waves["slow_cell_fraction"] == pytest.approx(1.0)
    assert waves["components"]
    assert waves["components"][0]["growth"] in {"upstream", "downstream", "stationary"}


def test_occupancy_series_reports_total_and_per_lane():
    frame = _frame(lanes=("1", "2", "3", "4", "5"), n_vehicles=30, spacing_m=20.0, steps=50)
    table = tr.occupancy_series(frame, window=(0.0, 5.0), block_s=1.0)
    assert "vehicles_total" in table.columns
    assert table.vehicles_total.iloc[0] == pytest.approx(50.0)
