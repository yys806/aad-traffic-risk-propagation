from __future__ import annotations

import io
import math
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from riskprop.real_trajectory import (
    add_ngsim_leader_ttc,
    read_ngsim_nested_csv,
    read_pneuma_wide,
)


def test_ngsim_pairs_reported_leader_and_uses_positive_net_gap() -> None:
    rows = pd.DataFrame(
        [
            {
                "Vehicle_ID": 10,
                "Frame_ID": 1,
                "Global_Time": 1_000,
                "Local_X": 12.0,
                "Local_Y": 100.0,
                "v_Length": 12.0,
                "v_Vel": 30.0,
                "v_Acc": -2.0,
                "Lane_ID": 2,
                "Preceeding": 20,
                "Space_Hdwy": 30.0,
            },
            {
                "Vehicle_ID": 20,
                "Frame_ID": 1,
                "Global_Time": 1_000,
                "Local_X": 12.1,
                "Local_Y": 130.0,
                "v_Length": 15.0,
                "v_Vel": 20.0,
                "v_Acc": 0.0,
                "Lane_ID": 2,
                "Preceeding": 0,
                "Space_Hdwy": 0.0,
            },
        ]
    )

    result = add_ngsim_leader_ttc(rows, run_id="us101_0750")
    follower = result.loc[result["id"] == "10"].iloc[0]

    assert follower["leader_id"] == "20"
    assert follower["reported_space_headway_m"] == pytest.approx(30.0 * 0.3048)
    assert follower["leader_length_m"] == pytest.approx(15.0 * 0.3048)
    assert follower["headway_m"] == pytest.approx(15.0 * 0.3048)
    assert follower["leader_rel_speed_mps"] == pytest.approx(-10.0 * 0.3048)
    assert follower["speed_mps"] == pytest.approx(30.0 * 0.3048)
    assert follower["acceleration_mps2"] == pytest.approx(-2.0 * 0.3048)
    assert follower["x_m"] == pytest.approx(12.0 * 0.3048)
    assert follower["y_m"] == pytest.approx(100.0 * 0.3048)
    assert follower["lane_id"] == "2"
    assert bool(follower["ttc_valid"])
    assert follower["ttc_s"] == pytest.approx(1.5)
    assert follower["drac_mps2"] == pytest.approx((10.0 * 0.3048) ** 2 / (2 * 15.0 * 0.3048))
    assert follower["measurement_status"] == "valid"
    assert follower["missing_reason"] == ""


def test_ngsim_ttc_requires_matched_leader_positive_gap_and_closing_speed() -> None:
    rows = pd.DataFrame(
        [
            {"Vehicle_ID": 1, "Frame_ID": 1, "Global_Time": 1_000, "Local_Y": 0, "v_Length": 15, "v_Vel": 20, "Lane_ID": 1, "Preceeding": 0, "Space_Hdwy": 0},
            {"Vehicle_ID": 2, "Frame_ID": 1, "Global_Time": 1_000, "Local_Y": 10, "v_Length": 15, "v_Vel": 20, "Lane_ID": 1, "Preceeding": 99, "Space_Hdwy": 20},
            {"Vehicle_ID": 3, "Frame_ID": 1, "Global_Time": 1_000, "Local_Y": 20, "v_Length": 15, "v_Vel": 10, "Lane_ID": 1, "Preceeding": 1, "Space_Hdwy": 20},
            {"Vehicle_ID": 4, "Frame_ID": 1, "Global_Time": 1_000, "Local_Y": 30, "v_Length": 15, "v_Vel": 30, "Lane_ID": 1, "Preceeding": 1, "Space_Hdwy": 10},
        ]
    )

    result = add_ngsim_leader_ttc(rows)

    assert not result["ttc_valid"].any()
    assert result["ttc_s"].map(math.isinf).all()
    by_id = result.set_index("id")
    assert by_id.loc["1", "measurement_status"] == "missing"
    assert by_id.loc["2", "measurement_status"] == "missing"
    assert by_id.loc["3", "measurement_status"] == "not_applicable"
    assert by_id.loc["4", "measurement_status"] == "invalid"
    assert set(result["missing_reason"]) == {
        "no_reported_leader",
        "leader_not_matched",
        "non_closing",
        "non_positive_gap",
    }


def test_ngsim_leader_match_preserves_nondefault_input_index() -> None:
    rows = pd.DataFrame(
        [
            {"Vehicle_ID": 10, "Global_Time": 1_000, "v_Length": 12, "v_Vel": 30, "Preceeding": 20, "Space_Hdwy": 30},
            {"Vehicle_ID": 20, "Global_Time": 1_000, "v_Length": 15, "v_Vel": 20, "Preceeding": 0, "Space_Hdwy": 0},
        ],
        index=[8, 9],
    )

    result = add_ngsim_leader_ttc(rows)

    assert result.index.tolist() == [8, 9]
    assert bool(result.loc[8, "leader_matched"])
    assert result.loc[8, "ttc_s"] == pytest.approx(1.5)


def test_reads_csv_from_nested_ngsim_zip(tmp_path: Path) -> None:
    inner_bytes = io.BytesIO()
    with zipfile.ZipFile(inner_bytes, "w") as inner:
        inner.writestr("window/trajectories.csv", "Vehicle_ID,Global_Time\n1,1000\n2,1100\n")
    outer_path = tmp_path / "ngsim.zip"
    with zipfile.ZipFile(outer_path, "w") as outer:
        outer.writestr("vehicle-trajectory-data.zip", inner_bytes.getvalue())

    result = read_ngsim_nested_csv(
        outer_path,
        "vehicle-trajectory-data.zip",
        "window/trajectories.csv",
        nrows=1,
    )

    assert result.to_dict("records") == [{"Vehicle_ID": 1, "Global_Time": 1000}]


def test_pneuma_wide_row_expands_six_field_state_blocks(tmp_path: Path) -> None:
    source = tmp_path / "pneuma.csv"
    source.write_text(
        "track_id; type; traveled_d; avg_speed; lat; lon; speed; lon_acc; lat_acc; time\n"
        "7; Car; 12.5; 18.0; 37.1; 23.1; 10.0; -0.2; 0.1; 0.00; "
        "37.2; 23.2; 11.0; -0.1; 0.0; 0.04; \n",
        encoding="utf-8",
    )

    result = read_pneuma_wide(source, run_id="pneuma_d1_0800")

    assert len(result) == 2
    assert result["id"].tolist() == ["7", "7"]
    assert result["time_s"].tolist() == pytest.approx([0.0, 0.04])
    assert result["speed_kmh"].tolist() == pytest.approx([10.0, 11.0])
    assert result["speed_mps"].tolist() == pytest.approx([10.0 / 3.6, 11.0 / 3.6])
    assert result["run_id"].tolist() == ["pneuma_d1_0800", "pneuma_d1_0800"]
    assert set(result.columns) == {
        "run_id",
        "id",
        "vehicle_type",
        "traveled_distance_m",
        "average_speed_kmh",
        "latitude",
        "longitude",
        "speed_kmh",
        "speed_mps",
        "longitudinal_accel_mps2",
        "lateral_accel_mps2",
        "time_s",
    }


def test_pneuma_rejects_incomplete_state_block(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text(
        "track_id; type; traveled_d; avg_speed; lat; lon; speed; lon_acc; lat_acc; time\n"
        "7; Car; 12.5; 18.0; 37.1; 23.1; 10.0; -0.2; 0.1; \n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="six values"):
        read_pneuma_wide(source)
