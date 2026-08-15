import csv
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = PROJECT_ROOT / "code" / "real_data" / "spmd"
sys.path.insert(0, str(MODULE_DIR))

from profile_rv_rx import EXPECTED_HEADER, ProfileFormatError, profile_zip


def _row(device, trip, time_centiseconds, rv_id, tail=("", "", "", "")):
    values = [
        device,
        trip,
        time_centiseconds,
        rv_id,
        2,
        1,
        0,
        250,
        180,
        42.0,
        0.0,
        -83.0,
        0.0,
        20.0,
        -1.0,
        10.0,
        0.0,
        0.0,
    ]
    return [str(value) for value in values] + list(tail)


def _write_zip(path: Path, members: dict[str, list[list[str]]], header=None):
    header = EXPECTED_HEADER if header is None else header
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member_name, rows in members.items():
            lines = []
            sink = _ListWriter(lines)
            writer = csv.writer(sink, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
            archive.writestr(member_name, "".join(lines))


class _ListWriter:
    def __init__(self, target):
        self.target = target

    def write(self, value):
        self.target.append(value)


def test_profiles_22_column_rows_and_continuity_by_receiver_trip_remote(tmp_path):
    archive = tmp_path / "RV_RX.csv.zip"
    _write_zip(
        archive,
        {
            "april.csv": [
                _row("10", "trip-a", 0, "rv-1"),
                _row("10", "trip-a", 100, "rv-1"),
                _row("10", "trip-a", 1300, "rv-1"),
                _row("10", "trip-a", 50, "rv-2"),
                _row("10", "trip-b", 10, "rv-1"),
                _row("11", "trip-c", 0, "rv-3"),
            ],
            "october.csv": [
                _row("20", "trip-d", 200, "rv-9"),
                _row("20", "trip-d", 300, "rv-9"),
            ],
        },
    )

    result = profile_zip(archive)

    assert result["dataset"] == "SPMD RV_RX received remote-vehicle state observations"
    assert result["statistics_definition"]["continuity_key"] == [
        "DeviceID",
        "Trip",
        "RV_ID",
    ]
    assert result["parameters"]["segment_gap_cs"] == 100
    assert "centiseconds since the receiver DAS started" in result[
        "statistics_definition"
    ]["time"]
    april = result["files"][0]
    assert april["row_count"] == 6
    assert april["device_id_count"] == 2
    assert april["device_trip_count"] == 3
    assert april["rv_id_count"] == 3
    assert april["time_cs"] == {"min": 0, "max": 1300}
    assert april["continuity"]["stream_count"] == 4
    assert april["continuity"]["segment_count"] == 5
    assert april["continuity"]["adjacent_interval_count"] == 2
    assert april["continuity"]["gap_over_threshold_count"] == 1
    assert april["continuity"]["adjacent_interval_cs_mean"] == 650.0
    assert april["format"]["empty_trailing_column_count"] == 4
    assert april["format"]["nonempty_trailing_row_count"] == 0
    assert result["combined"]["row_count"] == 8
    assert "does not identify per-message delivery" in " ".join(result["limitations"])
    assert "adoption" in " ".join(result["limitations"])


def test_rejects_nonempty_undocumented_trailing_columns(tmp_path):
    archive = tmp_path / "bad-tail.zip"
    _write_zip(archive, {"bad.csv": [_row("10", "1", 0, "rv-1", ("x", "", "", ""))]})

    with pytest.raises(ProfileFormatError, match="non-empty undocumented trailing columns"):
        profile_zip(archive)


def test_rejects_unexpected_header(tmp_path):
    archive = tmp_path / "bad-header.zip"
    bad_header = list(EXPECTED_HEADER)
    bad_header[2] = "Timestamp"
    _write_zip(archive, {"bad.csv": [_row("10", "1", 0, "rv-1")]}, bad_header)

    with pytest.raises(ProfileFormatError, match="header"):
        profile_zip(archive)


def test_cli_writes_reproducible_json_profile(tmp_path):
    archive = tmp_path / "RV_RX.csv.zip"
    output = tmp_path / "profile.json"
    _write_zip(archive, {"sample.csv": [_row("10", "1", 0, "rv-1")]})

    result = subprocess.run(
        [
            sys.executable,
            str(MODULE_DIR / "profile_rv_rx.py"),
            str(archive),
            "--output",
            str(output),
            "--segment-gap-cs",
            "50",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["parameters"]["segment_gap_cs"] == 50
    assert payload["combined"]["row_count"] == 1
    assert str(output) in result.stdout
