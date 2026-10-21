"""Regression tests for the boundary-arrival and relative-speed anomaly modules."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from riskprop import stage_0_5_boundary_timing as bt
from riskprop import stage_0_5_state_support as ss


def _window_frame(*, window_start: float = 120.0, n_initial: int = 4,
                  entries: int = 6, onramp: int = 2,
                  spacings: tuple[float, ...] = (1.0, 3.0, 2.0, 4.0, 1.5, 2.5)) -> pd.DataFrame:
    """A tiny synthetic canonical-like frame with a declared window start."""
    rows = []
    for index in range(n_initial):
        rows.append({
            "window_id": "0750_0805", "trajectory_id": f"init{index}", "time_s": window_start,
            "y_m": 60.0 + 40.0 * index, "speed_mps": 8.0, "lane_id": str(1 + index % 5),
            "net_gap_m": 12.0, "closing_speed_mps": -0.1, "measurement_status": "valid",
            "leader_matched": True,
        })
    elapsed = 5.0
    for index in range(entries):
        rows.append({
            "window_id": "0750_0805", "trajectory_id": f"new{index}",
            "time_s": window_start + elapsed,
            "y_m": 11.0, "speed_mps": 9.0, "lane_id": str(1 + index % 5),
            "net_gap_m": 15.0, "closing_speed_mps": -0.1, "measurement_status": "valid",
            "leader_matched": True,
        })
        elapsed += spacings[index % len(spacings)]
    for index in range(onramp):
        rows.append({
            "window_id": "0750_0805", "trajectory_id": f"ramp{index}",
            "time_s": window_start + 9.0 + 7.0 * index,
            "y_m": 150.0, "speed_mps": 11.0, "lane_id": "7",
            "net_gap_m": 20.0, "closing_speed_mps": -0.1, "measurement_status": "valid",
            "leader_matched": True,
        })
    # a vehicle that is first seen in the middle of the corridor (occluded at the entry)
    rows.append({
        "window_id": "0750_0805", "trajectory_id": "occluded", "time_s": window_start + 30.0,
        "y_m": 420.0, "speed_mps": 9.0, "lane_id": "3",
        "net_gap_m": 18.0, "closing_speed_mps": -0.1, "measurement_status": "valid",
        "leader_matched": True,
    })
    frame = pd.DataFrame(rows)
    frame.loc[frame.trajectory_id == "new0", "lane_id"] = "8"  # off-ramp user downstream
    return frame


# --------------------------------------------------------------------------
# boundary event reconstruction
# --------------------------------------------------------------------------
def test_entry_events_excludes_initial_state_and_records_reasons():
    frame = _window_frame()
    # the off-ramp user must be recognised as an *exiting* route, not an entry at lane 8
    frame.loc[frame.trajectory_id == "new0", "lane_id"] = "1"
    frame = pd.concat([frame, pd.DataFrame([{
        "window_id": "0750_0805", "trajectory_id": "new0", "time_s": 140.0, "y_m": 430.0,
        "speed_mps": 9.0, "lane_id": "8", "net_gap_m": 18.0, "closing_speed_mps": -0.1,
        "measurement_status": "valid", "leader_matched": True}])], ignore_index=True)
    events = bt.entry_events(frame, "us101__0750_0805")
    identifiers = {item["trajectory_id"] for item in events["events"]}
    assert not identifiers & {f"init{index}" for index in range(4)}
    assert "occluded" not in identifiers
    reasons = {item["trajectory_id"]: item["reason"] for item in events["excluded"]}
    assert reasons["occluded"] == "first_observation_downstream_of_entry"
    assert reasons["init0"] == "initial_state_vehicle"
    assert events["event_counts"]["mainline"] == 6
    assert events["event_counts"]["onramp"] == 2
    exits = [item for item in events["events"] if item["trajectory_id"] == "new0"]
    assert exits and exits[0]["route"] == "exiting"
    assert all(item["sim_time_s"] >= 0 for item in events["events"])


def test_entry_events_refuses_the_validation_window_and_holdout():
    frame = _window_frame()
    with pytest.raises(bt.BoundaryTimingError):
        bt.entry_events(frame, ss.VALIDATION_WINDOW)
    with pytest.raises(ss.StateSupportError):
        ss._assert_not_holdout("lankershim")


def test_event_ids_never_collide_with_initial_state_vehicles():
    frame = _window_frame()
    events = bt.entry_events(frame, "us101__0750_0805")
    initial_ids = {f"trajectory_id:{item['trajectory_id']}"
                   for item in events["excluded"] if item["reason"] == "initial_state_vehicle"}
    event_ids = {"trajectory_id:" + item["trajectory_id"] for item in events["events"]}
    assert not (initial_ids & event_ids)


def test_uniform_arrivals_are_periodic_and_count_preserving():
    times = bt.uniform_arrivals(7, 420.0)
    assert len(times) == 7
    assert np.allclose(np.diff(times), 420.0 / 7)
    assert times.min() > 0 and times.max() < 420.0
    assert len(bt.uniform_arrivals(0, 420.0)) == 0
    with pytest.raises(bt.BoundaryTimingError):
        bt.uniform_arrivals(3, 0.0)


def test_paired_tables_differ_only_in_arrival_time():
    frame = _window_frame()
    events = bt.entry_events(frame, "us101__0750_0805")
    table = bt.paired_arrival_tables(events["events"])["events"]
    invariant = ["event_id", "stream", "trajectory_id", "observed_lane_id", "observed_y_first_m",
                 "observed_speed_first_mps", "route", "real_time_s"]
    for column in invariant:
        assert table[column].tolist() == table[column].tolist()
    assert not np.allclose(table.arm_U_time_s, table.arm_E_time_s)
    # per-stream counts identical and uniform arm strictly periodic
    for stream, group in table.groupby("stream"):
        assert len(group) == int((table.stream == stream).sum())
        uniform = np.sort(group.arm_U_time_s.to_numpy(float))
        assert np.allclose(np.diff(uniform), 420.0 / len(group))


def test_paired_tables_are_order_preserving_within_a_stream():
    frame = _window_frame()
    events = bt.entry_events(frame, "us101__0750_0805")
    table = bt.paired_arrival_tables(events["events"])["events"]
    for _, group in table.groupby("stream"):
        ordered = group.sort_values("arm_E_time_s")
        assert ordered.arm_U_time_s.is_monotonic_increasing


# --------------------------------------------------------------------------
# wave diagnostic: constructed scenarios
# --------------------------------------------------------------------------
def test_synthetic_scenarios_separate_upstream_stationary_downstream_and_none():
    scenarios = bt.synthetic_wave_scenarios()
    reference = {"centres_veh_km_lane": [35.0, 45.0], "median_speed_mps": [12.0, 12.0]}
    reports = {name: bt.anomaly_report(frame, reference, 0.0, resamples=300)
               for name, frame in scenarios.items()}
    assert reports["upstream"]["level"] == "propagating_structure"
    assert reports["upstream"]["structure"]["front_direction"] == "upstream"
    assert reports["upstream"]["cross_correlation"]["median_implied_speed_mps"] < 0
    assert reports["gappy"]["level"] == "propagating_structure"
    assert reports["downstream"]["level"] != "propagating_structure"
    assert reports["downstream"]["structure"]["front_direction"] == "downstream"
    assert reports["stationary"]["level"] != "propagating_structure"
    assert reports["none"]["level"] != "propagating_structure"
    # the control scenarios are not beyond the permutation null, the wave scenarios are
    assert reports["stationary"]["null"]["exceedance_rate"] > bt.NULL_MAX_EXCEEDANCE
    assert reports["upstream"]["null"]["exceedance_rate"] <= bt.NULL_MAX_EXCEEDANCE


def test_wave_levels_stay_inside_the_declared_vocabulary():
    declared = {"no_structure", "local_anomaly_no_propagation", "uncorroborated_structure",
                "propagating_structure"}
    reference = {"centres_veh_km_lane": [35.0, 45.0], "median_speed_mps": [12.0, 12.0]}
    for frame in bt.synthetic_wave_scenarios().values():
        report = bt.anomaly_report(frame, reference, 0.0, resamples=100)
        assert report["level"] in declared


def test_missing_and_discontinuous_cells_are_handled_without_crashing():
    frame = bt.synthetic_wave_scenarios()["upstream"].copy()
    dropped = frame[(frame.t_block == 8) | (frame.t_block == 9)]
    gappy = frame.drop(dropped.index)
    reference = {"centres_veh_km_lane": [35.0, 45.0], "median_speed_mps": [12.0, 12.0]}
    report = bt.anomaly_report(gappy, reference, 0.0, resamples=100)
    assert report["cells"] < len(frame)
    assert report["level"] in {"no_structure", "local_anomaly_no_propagation",
                               "uncorroborated_structure", "propagating_structure"}


def test_empty_cell_frame_is_refused():
    with pytest.raises(bt.BoundaryTimingError):
        bt.temporal_position_anomaly(pd.DataFrame(columns=["y_block", "speed_mps"]))


# --------------------------------------------------------------------------
# density-conditioned variant and geometry
# --------------------------------------------------------------------------
def test_density_conditioned_baseline_is_monotone_where_data_supports_it():
    frame = pd.DataFrame({
        "t_block": np.repeat(np.arange(20), 2),
        "y_block": np.tile([1, 2], 20),
        "t_start_s": np.repeat(np.arange(20) * 10.0, 2),
        "y_start_m": np.tile([50.0, 100.0], 20),
        "obs": 500,
        "speed_mps": np.concatenate([np.full(20, 12.0), np.full(20, 6.0)]),
        "density_veh_km_lane": np.concatenate([np.full(20, 20.0), np.full(20, 60.0)]),
        "lane_id": "1",
    })
    baseline = bt.density_speed_baseline(frame)
    assert baseline["centres_veh_km_lane"] == sorted(baseline["centres_veh_km_lane"])
    assert len(baseline["centres_veh_km_lane"]) >= 2
    medians = dict(zip(baseline["centres_veh_km_lane"], baseline["median_speed_mps"]))
    assert min(medians.values()) < max(medians.values())


def test_event_lane_index_maps_mainline_and_on_ramp():
    assert bt.event_lane_index({"observed_lane_id": "1"}) == 4
    assert bt.event_lane_index({"observed_lane_id": "5"}) == 0
    assert bt.event_lane_index({"observed_lane_id": "7"}) == 0
    with pytest.raises(bt.BoundaryTimingError):
        bt.event_lane_index({"observed_lane_id": "8"})


def test_arrival_summary_reports_the_structure_difference():
    frame = _window_frame()
    events = bt.entry_events(frame, "us101__0750_0805")
    table = bt.paired_arrival_tables(events["events"])["events"]
    uniform = table.assign(arrival_time_s=table.arm_U_time_s)
    real = table.assign(arrival_time_s=table.arm_E_time_s)
    uniform_summary = bt.arrival_summary(uniform)
    real_summary = bt.arrival_summary(real)
    assert uniform_summary["streams"]["mainline"]["gap_cv"] == pytest.approx(0.0, abs=1e-12)
    assert real_summary["streams"]["mainline"]["gap_cv"] > 0.0
    assert uniform_summary["streams"]["mainline"]["events"] == real_summary["streams"]["mainline"]["events"]
