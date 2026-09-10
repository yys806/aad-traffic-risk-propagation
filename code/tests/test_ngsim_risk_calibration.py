from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from riskprop.ngsim_risk_calibration import (
    extract_rear_end_events,
    standardize_ngsim_states,
    write_stage_0_2_ngsim_package,
)


def _ngsim_rows() -> pd.DataFrame:
    rows = []
    for frame, time_ms, follower_speed in ((1, 1000, 30.0), (2, 1100, 29.0), (3, 1200, 28.0)):
        rows.extend(
            [
                {
                    "Vehicle_ID": 10,
                    "Frame_ID": frame,
                    "Global_Time": time_ms,
                    "Local_X": 12.0,
                    "Local_Y": 100.0 + frame,
                    "v_Length": 12.0,
                    "v_Vel": follower_speed,
                    "v_Acc": -2.0,
                    "Lane_ID": 2,
                    "Preceeding": 20,
                    "Space_Hdwy": 20.0,
                },
                {
                    "Vehicle_ID": 20,
                    "Frame_ID": frame,
                    "Global_Time": time_ms,
                    "Local_X": 12.1,
                    "Local_Y": 120.0 + frame,
                    "v_Length": 15.0,
                    "v_Vel": 20.0,
                    "v_Acc": 0.0,
                    "Lane_ID": 2,
                    "Preceeding": 0,
                    "Space_Hdwy": 0.0,
                },
            ]
        )
    return pd.DataFrame(rows)


def test_standardize_ngsim_state_preserves_raw_and_si_fields() -> None:
    states = standardize_ngsim_states(
        _ngsim_rows(), site="US-101", window_id="0750_0805"
    )
    follower = states[states["vehicle_id"] == "10"].iloc[0]
    assert follower["dataset"] == "NGSIM"
    assert follower["raw_speed_fps"] == pytest.approx(30.0)
    assert follower["speed_mps"] == pytest.approx(30.0 * 0.3048)
    assert follower["net_gap_m"] == pytest.approx(5.0 * 0.3048)
    assert follower["measurement_status"] == "valid"


def test_rear_end_events_merge_frames_and_never_count_frames_as_events() -> None:
    states = standardize_ngsim_states(
        _ngsim_rows(), site="US-101", window_id="0750_0805"
    )
    events = extract_rear_end_events(
        states, provisional_ttc_threshold_s=3.0, max_gap_s=0.11, minimum_duration_s=0.1
    )
    assert len(events) == 1
    assert events.iloc[0]["raw_frame_count"] == 3
    assert events.iloc[0]["event_duration_s"] == pytest.approx(0.2)
    assert events.iloc[0]["conflict_type"] == "rear_end"
    assert events.iloc[0]["inclusion_status"] == "calibration_candidate"


def test_lankershim_spelling_is_supported() -> None:
    rows = _ngsim_rows().rename(
        columns={"v_Length": "v_length", "Preceeding": "Preceding", "Space_Hdwy": "Space_Headway"}
    )
    result = standardize_ngsim_states(rows, site="Lankershim", window_id="all")
    assert result["leader_id"].notna().any()


def test_stage_0_2_package_reads_only_requested_calibration_member(tmp_path: Path) -> None:
    source = tmp_path / "ngsim.zip"
    csv_bytes = _ngsim_rows().to_csv(index=False).encode()
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, "w") as inner:
        inner.writestr("window/trajectories.csv", csv_bytes)
    with zipfile.ZipFile(source, "w") as outer:
        outer.writestr("trajectories.zip", nested.getvalue())

    output = write_stage_0_2_ngsim_package(
        output_dir=tmp_path / "out",
        sources=[
            {
                "asset_id": "ngsim_us101",
                "site": "US-101",
                "path": source,
                "inner_zip_member": "trajectories.zip",
                "csv_member": "window/trajectories.csv",
                "window_id": "fixture",
            }
        ],
        provisional_ttc_threshold_s=3.0,
    )
    assert (output / "states" / "ngsim_us101__fixture.parquet").is_file()
    assert (output / "risk_events.parquet").is_file()
    assert (output / "audit.json").is_file()
    assert (output / "SHA256SUMS").is_file()
    audit = pd.read_json(output / "audit.json", typ="series")
    assert audit["scientific_claim_eligible"] is False
    assert audit["locked_holdout_opened"] is False
    assert audit["gate_status"] == "active_audit_closure"
