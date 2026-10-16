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
    assert audit["tracks_table"].iloc[0]["source_row_number"] == 2
    assert audit["raw_track_rows"] == 1
    assert audit["unique_track_ids"] == 1


def test_flag_state_quality_detects_reversal_duplicate_and_gap() -> None:
    # Raw record order: 0.00 -> 0.04 -> 0.04 -> 0.02
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.00},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04},  # duplicate
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.02},  # raw-order reversal
            {"vehicle_id": "b", "vehicle_type": "Taxi", "time_s": 0.0},
        ]
    )
    flagged = flag_state_quality(states)
    a = flagged[flagged["vehicle_id"] == "a"].set_index("raw_index").sort_index()
    assert flagged["duplicate_time_in_track"].sum() == 2
    # Raw-order dt (NOT sorted dt): 0.04, 0.00, -0.02, NaN for vehicle a.
    assert a["dt_to_next_s"].tolist() == pytest.approx([0.04, 0.00, -0.02, float("nan")], nan_ok=True)
    # The 0.02 state regressed against its raw-order predecessor and must be
    # flagged even though a time sort would place it before 0.04.
    assert a["time_regression_in_raw_order"].tolist() == [False, False, False, True]
    assert a["time_increment_nonpositive"].tolist() == [False, False, True, True]
    # States involved in a nonpositive raw-order edge (out or in) lose
    # reliable-interval status: the first 0.04 (outgoing 0.00), the second
    # 0.04 and the 0.02 reversal; the 0.00 state keeps a clean raw interval.
    assert a["raw_order_time_anomaly"].tolist() == [False, True, True, True]


def test_flag_state_quality_raw_order_regression_not_masked_by_sort() -> None:
    # Required regression: 0.00 -> 0.08 -> 0.04 in raw record order must be
    # identified as a time regression; sorting must not repair it.
    states = _states_frame(
        [
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.00, "speed_mps": 10.0},
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.08, "speed_mps": 11.0},
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.04, "speed_mps": 12.0},
        ]
    )
    flagged = flag_state_quality(states, gap_tolerance_s=0.043).set_index("raw_index").sort_index().sort_index()
    assert flagged["time_regression_in_raw_order"].tolist() == [False, False, True]
    # The reversal edge (0.08 -> 0.04) flags both endpoints; the first state
    # is a raw-order gap (0.08 > tolerance), not a usable 0.04 s interval.
    assert flagged["raw_order_time_anomaly"].tolist() == [False, True, True]
    assert flagged["time_gap_flag"].tolist() == [True, False, False]
    # Time weighting must not let the sorted view (0.00, 0.04, 0.08) hand a
    # reliable interval back to the anomalous observations.
    summary = integrate_time_weighted(
        flagged, value_column="speed_mps", tolerance_s=0.043, nominal_dt_s=None
    )
    assert summary["states_time_weighted"] == 0
    assert summary["exposure_time_s"] == pytest.approx(0.0)


def test_time_weighting_respects_raw_order_anomaly_flags() -> None:
    # A duplicated (track, time) state must not regain reliable weight even
    # though the time-sorted view has a well-formed interval before it.
    states = _states_frame(
        [
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.00, "speed_mps": 10.0},
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.04, "speed_mps": 20.0},
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.04, "speed_mps": 21.0},
            {"vehicle_id": "v", "vehicle_type": "Car", "time_s": 0.08, "speed_mps": 30.0},
        ]
    )
    flagged = flag_state_quality(states)
    summary = integrate_time_weighted(
        flagged, value_column="speed_mps", tolerance_s=0.043, nominal_dt_s=None
    )
    # Only the pre-duplicate interval [0.00, 0.04) remains reliable; the
    # duplicated (track, time) states themselves must not regain weight from
    # the time-sorted adjacency (the pre-repair sorted view would have handed
    # the second 0.04 state a full 0.04 s interval).
    assert summary["states_time_weighted"] == 1
    assert summary["exposure_time_s"] == pytest.approx(0.04)
    assert summary["mean"] == pytest.approx(10.0)


def test_flag_state_quality_gap_flag_respects_tolerance() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.5},
        ]
    )
    flagged = flag_state_quality(states, gap_tolerance_s=0.08)
    assert flagged["time_gap_flag"].tolist() == [False, True, False]


def test_audit_duplicate_track_rows_are_flagged_not_merged(tmp_path: Path) -> None:
    # Same track id on two different raw rows with non-overlapping times: no
    # dict overwrite, no silent merge into one reliable trajectory.
    source = tmp_path / "dup.csv"
    _write_wide(
        source,
        [
            ["X", "Car", "10.0", "30.0",
             "37.0", "23.0", "10.0", "0.0", "0.0", "0.00",
             "37.0", "23.0", "12.0", "0.0", "0.0", "0.04"],
            ["X", "Car", "10.0", "30.0",
             "37.5", "23.5", "20.0", "0.0", "0.0", "10.00",
             "37.5", "23.5", "22.0", "0.0", "0.0", "10.04"],
            ["Y", "Taxi", "7.0", "25.0",
             "37.9", "23.9", "15.0", "0.0", "0.0", "0.00"],
        ],
    )
    frame, audit = audit_pneuma_source(source)
    assert audit["raw_track_rows"] == 3
    assert audit["unique_track_ids"] == 2
    assert audit["duplicate_track_ids"] == ["X"]
    assert audit["duplicate_track_rows"] == 2
    assert audit["identity_conflicts"] == []  # identical type and metadata, ambiguous only by row duplication
    x_states = frame[frame["vehicle_id"] == "X"]
    assert len(x_states) == 4  # all raw states retained, none dropped
    assert set(x_states["source_row_number"]) == {2, 3}
    assert x_states["identity_status"].eq("ambiguous_duplicate_track_id").all()
    assert x_states["identity_ambiguous"].all()
    y_states = frame[frame["vehicle_id"] == "Y"]
    assert y_states["identity_status"].eq("unique").all()
    # Fail-closed: ambiguous states are excluded from reliable time weighting.
    flagged = flag_state_quality(x_states)
    summary = integrate_time_weighted(
        flagged, value_column="speed_mps", tolerance_s=0.043, nominal_dt_s=None
    )
    assert summary["states_time_weighted"] == 0


def test_audit_records_identity_conflicts_for_duplicate_rows(tmp_path: Path) -> None:
    source = tmp_path / "conflict.csv"
    _write_wide(
        source,
        [
            ["Z", "Car", "10.0", "30.0",
             "37.0", "23.0", "10.0", "0.0", "0.0", "0.00"],
            ["Z", "Bus", "10.0", "30.0",
             "37.0", "23.0", "10.0", "0.0", "0.0", "0.00"],
        ],
    )
    frame, audit = audit_pneuma_source(source)
    assert audit["duplicate_track_ids"] == ["Z"]
    assert len(audit["identity_conflicts"]) == 1
    conflict = audit["identity_conflicts"][0]
    assert conflict["track_id"] == "Z"
    assert conflict["source_row_numbers"] == [2, 3]
    assert "vehicle_type_mismatch" in conflict["reasons"]
    assert conflict["rejection_rule"] == "identity_ambiguous_fail_closed"
    assert frame["identity_conflict"].all()


def test_audit_flags_duplicate_track_time_within_row(tmp_path: Path) -> None:
    source = tmp_path / "dup_time.csv"
    _write_wide(
        source,
        [
            ["D", "Car", "10.0", "30.0",
             "37.0", "23.0", "10.0", "0.0", "0.0", "0.00",
             "37.0", "23.0", "12.0", "0.0", "0.0", "0.04",
             "37.0", "23.0", "14.0", "0.0", "0.0", "0.04"],
        ],
    )
    frame, audit = audit_pneuma_source(source)
    assert audit["duplicate_state_keys_count"] == 2
    flagged = flag_state_quality(frame)
    assert flagged["duplicate_time_in_track"].sum() == 2
    assert flagged["time_increment_nonpositive"].sum() == 1


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
             "longitudinal_accel_mps2": 0.1, "dt_to_next_s": 0.04, "parse_ok": True,
             "identity_ambiguous": False, "raw_order_time_anomaly": False,
             "duplicate_time_in_track": False},
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
    assert reference.iloc[0]["quality_status"] == "raw_parsed"
    assert bool(reference.iloc[0]["time_weighting_eligible"]) is True


def test_build_stage_0_5_reference_states_derives_per_state_quality() -> None:
    states = _states_frame(
        [
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0,
             "longitudinal_accel_mps2": 0.1, "parse_ok": True, "identity_ambiguous": False,
             "raw_order_time_anomaly": False, "duplicate_time_in_track": False},
            {"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.04, "speed_mps": 11.0,
             "longitudinal_accel_mps2": 0.1, "parse_ok": False, "parse_error": "unparseable_speed_kmh",
             "identity_ambiguous": False, "raw_order_time_anomaly": False,
             "duplicate_time_in_track": False},
            {"vehicle_id": "b", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 12.0,
             "longitudinal_accel_mps2": 0.0, "parse_ok": True, "identity_ambiguous": True,
             "raw_order_time_anomaly": False, "duplicate_time_in_track": False},
            {"vehicle_id": "c", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 13.0,
             "longitudinal_accel_mps2": 0.0, "parse_ok": True, "identity_ambiguous": False,
             "raw_order_time_anomaly": True, "duplicate_time_in_track": False},
        ]
    )
    states["dt_to_next_s"] = [0.04, float("nan"), 0.04, 0.04]
    reference = build_stage_0_5_reference_states(states, gap_tolerance_s=0.043)
    assert reference["quality_status"].tolist() == [
        "raw_parsed",
        "parse_failed",
        "identity_ambiguous",
        "raw_time_anomaly",
    ]
    # Fail-closed eligibility: derived from parse + identity + raw-order + interval.
    assert reference["time_weighting_eligible"].tolist() == [True, False, False, False]


def test_build_stage_0_5_reference_states_refuses_unaudited_states() -> None:
    states = _states_frame(
        [{"vehicle_id": "a", "vehicle_type": "Car", "time_s": 0.0, "speed_mps": 10.0,
          "longitudinal_accel_mps2": 0.1}]
    )
    from riskprop.calibration import CalibrationContractError

    with pytest.raises(CalibrationContractError):
        build_stage_0_5_reference_states(states)
    with pytest.raises(CalibrationContractError):
        # Explicit uniform status without an eligibility column and without
        # interval information must not silently default to reliable.
        build_stage_0_5_reference_states(states, quality_status="raw_parsed")


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
