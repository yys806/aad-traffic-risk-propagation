"""Tests for Stage 0.3 pNEUMA urban kinematics (synthetic fixtures + semantics)."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from riskprop.pneuma_urban_kinematics import (
    acceleration_by_speed_stratum,
    acceleration_state_shares,
    audit_pneuma_source,
    audit_sampling_balance,
    bootstrap_track_intervals,
    build_stage_0_5_reference_states,
    compute_descriptive_stats,
    compute_kinematic_consistency,
    compute_track_stats,
    compute_vehicle_equal_weight_stats,
    compute_vehicle_type_composition,
    continuity_sensitivity,
    extreme_value_sensitivity,
    flag_state_quality,
    integrate_time_weighted,
    speed_state_shares,
    time_weighted_bootstrap,
    write_acceptance_package,
)


def _write_wide(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["track_id", " type", " traveled_d", " avg_speed", " lat", " lon", " speed", " lon_acc", " lat_acc", " time"])
        writer.writerows(rows)


def _states_frame(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(records)
    if "raw_index" not in frame:
        frame["raw_index"] = range(len(frame))
    return frame


def test_audit_streams_and_flags_unparseable_numeric(tmp_path: Path) -> None:
    source = tmp_path / "pneuma.csv"
    _write_wide(
        source,
        [
            ["1", "Car", "100.0", "20.0",
             "37.0", "23.0", "10.0", "0.1", "0.0", "0.00",
             "37.0", "23.0", "bad", "0.1", "0.0", "0.04"],
            ["2", "Taxi", "50.0", "18.0",
             "37.1", "23.1", "5.0", "0.0", "0.0", "1.00"],
        ],
    )
    frame, audit = audit_pneuma_source(source)
    assert audit["raw_track_rows"] == 2
    assert audit["parsed_state_records"] == 3
    bad = frame[(frame["vehicle_id"] == "1") & (frame["time_s"].round(2) == 0.04)]
    assert not bad["parse_ok"].iloc[0]
    assert bad["parse_error"].iloc[0] == "unparseable_speed_kmh"
    assert frame[frame["vehicle_id"] == "2"]["parse_ok"].iloc[0]


def test_audit_rejects_incomplete_state_block_without_dropping_metadata(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    _write_wide(
        source,
        [
            ["7", "Car", "12.5", "18.0", "37.1", "23.1", "10.0", "-0.2", "0.1"],
        ],
    )
    frame, audit = audit_pneuma_source(source)
    assert audit["malformed_tracks"] == ["7"]
    assert frame.empty
    assert audit["tracks_table"].iloc[0]["track_id"] == "7"


def test_flag_state_quality_detects_reversal_duplicate_and_gap() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.00},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04},  # duplicate
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.02},  # reversal vs next sort
            {"vehicle_id": "b", "vehicle_type": "Taxi", "time_s": 0.0},
        ]
    )
    flagged = flag_state_quality(states)
    assert flagged["duplicate_time_in_track"].sum() == 2
    # Sorted view: times 0.00,0.02,0.04,0.04 → dt 0.02,0.02,0.00,nan; nonpositive at dt==0.
    assert flagged["dt_to_next_s"].tolist()[:3] == pytest.approx([0.02, 0.02, 0.0])


def test_integrate_time_weighted_left_rectangle_and_no_gap_fill() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 20.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 1.0, "speed_mps": 30.0},  # gap 0.9
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 1.1, "speed_mps": 40.0},
        ]
    )
    summary = integrate_time_weighted(
        states, value_column="speed_mps", tolerance_s=0.12, nominal_dt_s=0.1
    )
    # Usable intervals: [0,0.1) value 10 weight 0.1; [1.0,1.1) value 30 weight 0.1.
    assert summary["states_time_weighted"] == 2
    assert summary["exposure_time_s"] == pytest.approx(0.2)
    assert summary["mean"] == pytest.approx(20.0)
    assert summary["states_excluded_by_time_gap"] == 1  # state at 0.1 excluded (dt 0.9)
    assert summary["final_states_zero_duration"] == 1
    # Final state never extrapolated.
    assert summary["max"] == pytest.approx(30.0)


def test_integrate_time_weighted_nan_value_excluded_not_zero() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": np.nan},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.2, "speed_mps": 20.0},
        ]
    )
    summary = integrate_time_weighted(
        states, value_column="speed_mps", tolerance_s=0.12, nominal_dt_s=0.1
    )
    assert summary["states_time_weighted"] == 1
    assert summary["mean"] == pytest.approx(10.0)


def test_vehicle_equal_weight_stats_uses_one_row_per_track() -> None:
    track_stats = pd.DataFrame(
        {
            "vehicle_id": ["a", "b", "c"],
            "vehicle_type": ["Car", "Car", "Taxi"],
            "mean_speed_mps_unweighted": [10.0, 20.0, 30.0],
            "mean_accel_mps2_unweighted": [0.0, 1.0, -1.0],
        }
    )
    overall = compute_vehicle_equal_weight_stats(
        track_stats, value_column="mean_speed_mps_unweighted"
    )
    assert overall.iloc[0]["mean"] == pytest.approx(20.0)
    by_type = compute_vehicle_equal_weight_stats(
        track_stats, value_column="mean_speed_mps_unweighted", group_column="vehicle_type"
    )
    taxi = by_type[by_type["group"] == "Taxi"].iloc[0]
    assert taxi["mean"] == pytest.approx(30.0)
    assert taxi["vehicles_total"] == 1


def test_compute_descriptive_stats_grouped_matches_manual() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 20.0},
            {"vehicle_id": "b", "vehicle_type": "Taxi", "time_s": 0.0, "speed_mps": 40.0},
            {"vehicle_id": "b", "vehicle_type": "Taxi", "time_s": 0.1, "speed_mps": 50.0},
        ]
    )
    grouped = compute_descriptive_stats(
        states, value_column="speed_mps", group_column="vehicle_type",
        tolerance_s=0.12, nominal_dt_s=0.1
    )
    car = grouped[grouped["group"] == "Car"].iloc[0]
    assert car["mean"] == pytest.approx(10.0)  # only first interval usable value 10*0.1
    taxi = grouped[grouped["group"] == "Taxi"].iloc[0]
    assert taxi["mean"] == pytest.approx(40.0)


def test_vehicle_type_composition_unique_trajectories_not_frames() -> None:
    track_stats = pd.DataFrame(
        {
            "vehicle_id": ["a", "b", "c"],
            "vehicle_type": ["Car", "Car", "Taxi"],
            "state_records": [100, 50, 10],
            "duration_s": [10.0, 5.0, 1.0],
        }
    )
    composition = compute_vehicle_type_composition(track_stats)
    car = composition[composition["vehicle_type"] == "Car"].iloc[0]
    assert car["unique_trajectories"] == 2
    assert car["trajectory_share"] == pytest.approx(2 / 3)
    assert car["state_records"] == 150


def test_speed_and_accel_state_shares_sum_to_one() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 0.1, "longitudinal_accel_mps2": 0.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 10.0, "longitudinal_accel_mps2": 1.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.2, "speed_mps": 30.0, "longitudinal_accel_mps2": -2.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.3, "speed_mps": 40.0, "longitudinal_accel_mps2": -0.01},
        ]
    )
    speed = speed_state_shares(states, tolerance_s=0.12)
    row = speed[speed["group"] == "ALL"].iloc[0]
    assert row["exposure_time_s"] == pytest.approx(0.3)
    assert row["low_speed_share"] == pytest.approx(1 / 3)
    assert row["near_stop_share"] == pytest.approx(1 / 3)
    assert row["high_speed_share"] == pytest.approx(1 / 3)
    accel = acceleration_state_shares(states, tolerance_s=0.12)
    arow = accel[accel["group"] == "ALL"].iloc[0]
    total = arow["accelerating_share"] + arow["decelerating_share"] + arow["near_zero_share"]
    assert total == pytest.approx(1.0)


def test_acceleration_by_speed_stratum_covers_all_weight() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 1.0, "longitudinal_accel_mps2": 0.5},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 6.0, "longitudinal_accel_mps2": -0.5},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.2, "speed_mps": 20.0, "longitudinal_accel_mps2": 0.0},
        ]
    )
    table = acceleration_by_speed_stratum(states, tolerance_s=0.12)
    assert table["exposure_time_s"].sum() == pytest.approx(0.2)
    assert table["states"].sum() == 2


def test_continuity_sensitivity_monotonic_exposure() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04, "speed_mps": 10.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.10, "speed_mps": 10.0},  # 0.06 gap
        ]
    )
    table = continuity_sensitivity(states, tolerances_s=[0.045, 0.08])
    assert table.loc[0, "exposure_time_s"] == pytest.approx(0.04)
    assert table.loc[1, "exposure_time_s"] == pytest.approx(0.10)


def test_extreme_value_sensitivity_never_mutates_input() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0, "longitudinal_accel_mps2": 0.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 100.0, "longitudinal_accel_mps2": 9.0},
        ]
    )
    snapshot = states.copy(deep=True)
    table = extreme_value_sensitivity(states, tolerance_s=0.12)
    pd.testing.assert_frame_equal(states, snapshot)
    assert table["states_remaining"].min() >= 1


def test_bootstrap_track_intervals_resamples_whole_tracks() -> None:
    track_stats = pd.DataFrame(
        {
            "vehicle_id": [f"v{i}" for i in range(30)],
            "vehicle_type": ["Car"] * 30,
            "mean_speed_mps_unweighted": np.linspace(5, 15, 30),
        }
    )
    result = bootstrap_track_intervals(
        track_stats, value_column="mean_speed_mps_unweighted", replicates=200, seed=1
    )
    row = result.iloc[0]
    assert row["vehicles"] == 30
    assert row["mean_ci_low"] < row["point_mean"] < row["mean_ci_high"]


def test_time_weighted_bootstrap_brackets_point_estimate() -> None:
    records = []
    for i in range(20):
        for k in range(5):
            records.append(
                {
                    "vehicle_id": f"v{i}",
                    "vehicle_type": "Car",
                    "time_s": k * 0.1,
                    "speed_mps": 5.0 + i * 0.5,
                }
            )
    states = _states_frame(records)
    result = time_weighted_bootstrap(
        states, value_column="speed_mps", tolerance_s=0.12, replicates=200, seed=2
    )
    assert result["vehicles"] == 20
    assert result["ci_low"] <= result["point_estimate"] <= result["ci_high"]


def test_kinematic_consistency_reports_deviations() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0,
             "longitudinal_accel_mps2": 0.0, "latitude": 37.0, "longitude": 23.0,
             "traveled_distance_m": 1.0, "average_speed_kmh": 36.0, "speed_kmh": 36.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 10.01,
             "longitudinal_accel_mps2": 0.1, "latitude": 37.0, "longitude": 23.00001,
             "traveled_distance_m": 1.0, "average_speed_kmh": 36.0, "speed_kmh": 36.036},
        ]
    )
    frame, summary, track_consistency = compute_kinematic_consistency(states)
    assert summary["adjacent_pairs"] == 1
    assert summary["accel_deviation_mps2_median"] == pytest.approx(0.0, abs=0.1)
    assert track_consistency.iloc[0]["reported_traveled_distance_m"] == 1.0


def test_build_stage_0_5_reference_states_schema() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0,
             "longitudinal_accel_mps2": 0.1, "dt_to_next_s": 0.04},
        ]
    )
    states["time_weighting_eligible"] = True
    states["source_file_sha256"] = "abc"
    reference = build_stage_0_5_reference_states(states)
    assert set(reference.columns) == {
        "dataset", "site", "window_id", "vehicle_id", "vehicle_type", "time_s",
        "speed_mps", "acceleration_mps2", "quality_status", "time_weighting_eligible",
        "source_file_sha256",
    }
    assert reference.iloc[0]["dataset"] == "pNEUMA"
    assert reference.iloc[0]["site"] == "Athens-d1"


def test_sampling_balance_audit_detects_type_shifts() -> None:
    reference = pd.DataFrame(
        {
            "vehicle_id": ["a", "a", "b", "b", "c", "c"],
            "vehicle_type": ["Car", "Car", "Car", "Car", "Taxi", "Taxi"],
            "speed_mps": [1, 2, 3, 4, 5, 6],
        }
    )
    sampled = reference.iloc[:2].copy()
    result = audit_sampling_balance(sampled, reference)
    assert result["available"]
    assert result["max_state_share_deviation"] > 0
    assert result["max_trajectory_loss_share"] == pytest.approx(1.0)  # Taxi lost entirely


def test_write_acceptance_package_is_immutable(tmp_path: Path) -> None:
    output = tmp_path / "pkg"
    write_acceptance_package(
        output_dir=output,
        config={"x": 1},
        source_csv=__file__,
        tables={"t.csv": pd.DataFrame({"a": [1]})},
        figures={},
        report_markdown="# r\n",
        audit={"k": "v"},
        code_files=[__file__],
        started_monotonic=0.0,
        started_wall_utc="2026-10-12T00:00:00Z",
    )
    assert (output / "SHA256SUMS").is_file()
    with pytest.raises(FileExistsError):
        write_acceptance_package(
            output_dir=output,
            config={},
            source_csv=__file__,
            tables={},
            figures={},
            report_markdown="",
            audit={},
            code_files=[__file__],
            started_monotonic=0.0,
            started_wall_utc="2026-10-12T00:00:00Z",
        )


def test_track_stats_and_duplicate_detection() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 1.0,
             "longitudinal_accel_mps2": 0.0, "traveled_distance_m": 1.0, "average_speed_kmh": 3.6},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.1, "speed_mps": 2.0,
             "longitudinal_accel_mps2": 0.0, "traveled_distance_m": 1.0, "average_speed_kmh": 3.6},
        ]
    )
    stats = compute_track_stats(states)
    assert stats.iloc[0]["state_records"] == 2
    assert stats.iloc[0]["duration_s"] == pytest.approx(0.1)
    assert stats.iloc[0]["mean_speed_mps_unweighted"] == pytest.approx(1.5)
