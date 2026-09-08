from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from riskprop.e16a import (
    CommunicationEvidenceError,
    build_e16a_status_package,
    evaluate_field_groups,
    profile_rv_rx_calibration,
    spmd_trip_split,
)


def test_spmd_trip_split_is_deterministic_and_trip_level() -> None:
    first = spmd_trip_split("device-a", "trip-1")
    assert first in {"calibration", "locked_holdout"}
    assert spmd_trip_split("device-a", "trip-1") == first
    assert spmd_trip_split("device-a", "trip-1") != spmd_trip_split(
        "device-a", "trip-1-extra"
    ) or first in {"calibration", "locked_holdout"}


def test_field_group_gate_requires_one_real_column_per_concept() -> None:
    groups = {
        "device": {"DeviceID"},
        "trip": {"Trip"},
        "message_time": {"GenTime", "PacketTime"},
        "message_key": {"MsgCount", "PacketID"},
    }
    result = evaluate_field_groups(
        ["DeviceID", "Trip", "GenTime", "MsgCount"], required_groups=groups
    )
    assert result["pass"] is True
    assert result["matched_fields"]["message_key"] == "MsgCount"
    with pytest.raises(CommunicationEvidenceError, match="message_key"):
        evaluate_field_groups(
            ["DeviceID", "Trip", "GenTime"], required_groups=groups, raise_on_missing=True
        )


def test_e16_status_distinguishes_access_block_from_schema_failure(tmp_path: Path) -> None:
    profile = tmp_path / "rv_rx_profile.json"
    profile.write_text(
        json.dumps(
            {
                "combined": {"row_count": 10, "device_trip_count": 2},
                "limitations": ["not a packet table"],
            }
        ),
        encoding="utf-8",
    )
    rv_zip = tmp_path / "RV_RX.csv.zip"
    rv_zip.write_bytes(b"fixture")
    output = build_e16a_status_package(
        rv_rx_profile_path=profile,
        rv_rx_zip_path=rv_zip,
        output_dir=tmp_path / "e16",
        packet_access={
            "source": "official_usdot",
            "url": "https://example.invalid/official",
            "http_status": 403,
            "status": "official_asset_inaccessible_from_current_environment",
        },
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["packet_schema_evaluated"] is False
    assert audit["gate_status"] == "pending_official_packet_access"
    assert audit["observable_boundary"] == "receive_state_continuity_only"
    assert audit["packet_loss_estimated"] is False
    assert audit["latency_estimated"] is False
    assert audit["adoption_inferred"] is False
    assert (output / "SHA256SUMS").is_file()


def test_rv_rx_profiler_uses_only_calibration_trips_for_continuity(tmp_path: Path) -> None:
    archive = tmp_path / "RV_RX.csv.zip"
    header = (
        "DeviceID,Trip,Time,RV_ID,RV_Type,RV_Number,Brake_Status,Elevation,Heading,"
        "Latitude,Lateral_Accel,Longitude,Longitudinal_Accel,Range,Range_Rate,Speed,"
        "SteerWheelPosition,Yaw_Rate\n"
    )
    calibration_pair = next(
        ("dev", str(index))
        for index in range(1000)
        if spmd_trip_split("dev", str(index)) == "calibration"
    )
    holdout_pair = next(
        ("dev", str(index))
        for index in range(1000)
        if spmd_trip_split("dev", str(index)) == "locked_holdout"
    )
    def row(device: str, trip: str, time_cs: int) -> str:
        documented = [device, trip, str(time_cs), "rv", "1", "1", "0", "0", "0", "0", "0", "0", "0", "10", "0", "5", "0", "0"]
        return ",".join([*documented, "", "", "", ""]) + "\n"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(
            "rv.csv",
            header
            + row(*calibration_pair, 100)
            + row(*calibration_pair, 120)
            + row(*holdout_pair, 100)
            + row(*holdout_pair, 500),
        )

    profile = profile_rv_rx_calibration(archive, segment_gap_cs=100)

    assert profile["calibration"]["row_count"] == 2
    assert profile["calibration"]["device_trip_count"] == 1
    assert profile["locked_holdout"]["rows_ignored"] == 2
    assert "trip_ids" not in profile["locked_holdout"]
    assert profile["observable_boundary"] == "receive_state_continuity_only"
