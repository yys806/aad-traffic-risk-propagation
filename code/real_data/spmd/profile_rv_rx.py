"""Stream and profile the two SPMD RV_RX CSV members in their ZIP archive."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import zipfile


EXPECTED_HEADER = [
    "DeviceID",
    "Trip",
    "Time",
    "RV_ID",
    "RV_Type",
    "RV_Number",
    "Brake_Status",
    "Elevation",
    "Heading",
    "Latitude",
    "Lateral_Accel",
    "Longitude",
    "Longitudinal_Accel",
    "Range",
    "Range_Rate",
    "Speed",
    "SteerWheelPosition",
    "Yaw_Rate",
]
EXPECTED_DATA_COLUMN_COUNT = 22


class ProfileFormatError(ValueError):
    """Raised when an RV_RX member does not match its audited physical format."""


def _parse_time(value: str, member: str, line_number: int) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ProfileFormatError(
            f"{member}:{line_number}: Time must be an integer centisecond value; got {value!r}"
        ) from error


def _profile_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    segment_gap_cs: int,
) -> tuple[dict, set[str], set[tuple[str, str]], set[str]]:
    devices: set[str] = set()
    device_trips: set[tuple[str, str]] = set()
    remote_vehicles: set[str] = set()
    last_time_by_stream: dict[tuple[str, str, str], int] = {}

    row_count = 0
    time_min: int | None = None
    time_max: int | None = None
    interval_count = 0
    interval_sum = 0
    interval_min: int | None = None
    interval_max: int | None = None
    gap_count = 0
    nonpositive_interval_count = 0

    with archive.open(info) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ProfileFormatError(f"{info.filename}: missing header") from error
        if header != EXPECTED_HEADER:
            raise ProfileFormatError(
                f"{info.filename}: unexpected header; expected {EXPECTED_HEADER!r}, got {header!r}"
            )

        for line_number, row in enumerate(reader, start=2):
            if len(row) != EXPECTED_DATA_COLUMN_COUNT:
                raise ProfileFormatError(
                    f"{info.filename}:{line_number}: expected 22 physical columns "
                    f"(18 documented plus 4 empty trailing), got {len(row)}"
                )
            if any(value.strip() for value in row[18:]):
                raise ProfileFormatError(
                    f"{info.filename}:{line_number}: non-empty undocumented trailing columns: "
                    f"{row[18:]!r}"
                )

            device, trip, time_value, rv_id = row[:4]
            time_centiseconds = _parse_time(time_value, info.filename, line_number)
            row_count += 1
            devices.add(device)
            device_trips.add((device, trip))
            remote_vehicles.add(rv_id)
            time_min = time_centiseconds if time_min is None else min(time_min, time_centiseconds)
            time_max = time_centiseconds if time_max is None else max(time_max, time_centiseconds)

            stream = (device, trip, rv_id)
            previous_time = last_time_by_stream.get(stream)
            if previous_time is not None:
                interval = time_centiseconds - previous_time
                interval_count += 1
                interval_sum += interval
                interval_min = interval if interval_min is None else min(interval_min, interval)
                interval_max = interval if interval_max is None else max(interval_max, interval)
                if interval > segment_gap_cs:
                    gap_count += 1
                if interval <= 0:
                    nonpositive_interval_count += 1
            last_time_by_stream[stream] = time_centiseconds

    continuity = {
        "stream_count": len(last_time_by_stream),
        "segment_count": len(last_time_by_stream) + gap_count,
        "adjacent_interval_count": interval_count,
        "adjacent_interval_cs_min": interval_min,
        "adjacent_interval_cs_max": interval_max,
        "adjacent_interval_cs_mean": (
            interval_sum / interval_count if interval_count else None
        ),
        "gap_over_threshold_count": gap_count,
        "nonpositive_interval_count": nonpositive_interval_count,
    }
    profile = {
        "member": info.filename,
        "zip_uncompressed_bytes": info.file_size,
        "zip_compressed_bytes": info.compress_size,
        "zip_crc32": f"{info.CRC:08x}",
        "row_count": row_count,
        "device_id_count": len(devices),
        "device_trip_count": len(device_trips),
        "rv_id_count": len(remote_vehicles),
        "time_cs": {"min": time_min, "max": time_max},
        "continuity": continuity,
        "format": {
            "header_column_count": len(EXPECTED_HEADER),
            "physical_data_column_count": EXPECTED_DATA_COLUMN_COUNT,
            "empty_trailing_column_count": 4,
            "nonempty_trailing_row_count": 0,
        },
    }
    return profile, devices, device_trips, remote_vehicles


def profile_zip(zip_path: Path | str, segment_gap_cs: int = 100) -> dict:
    """Profile every CSV member without extracting it or retaining observation rows."""
    if segment_gap_cs < 0:
        raise ValueError("segment_gap_cs must be non-negative")

    zip_path = Path(zip_path)
    all_devices: set[str] = set()
    all_device_trips: set[tuple[str, str]] = set()
    all_remote_vehicles: set[str] = set()
    profiles = []

    with zipfile.ZipFile(zip_path) as archive:
        members = [info for info in archive.infolist() if info.filename.lower().endswith(".csv")]
        if not members:
            raise ProfileFormatError(f"{zip_path}: archive contains no CSV members")
        for info in members:
            profile, devices, device_trips, remote_vehicles = _profile_member(
                archive, info, segment_gap_cs
            )
            profiles.append(profile)
            all_devices.update(devices)
            all_device_trips.update(device_trips)
            all_remote_vehicles.update(remote_vehicles)

    time_min_values = [item["time_cs"]["min"] for item in profiles if item["time_cs"]["min"] is not None]
    time_max_values = [item["time_cs"]["max"] for item in profiles if item["time_cs"]["max"] is not None]
    combined = {
        "file_count": len(profiles),
        "row_count": sum(item["row_count"] for item in profiles),
        "device_id_count": len(all_devices),
        "device_trip_count": len(all_device_trips),
        "rv_id_count": len(all_remote_vehicles),
        "time_cs": {
            "min": min(time_min_values) if time_min_values else None,
            "max": max(time_max_values) if time_max_values else None,
        },
        "continuity": {
            "stream_count_sum_across_files": sum(
                item["continuity"]["stream_count"] for item in profiles
            ),
            "segment_count_sum_across_files": sum(
                item["continuity"]["segment_count"] for item in profiles
            ),
            "adjacent_interval_count": sum(
                item["continuity"]["adjacent_interval_count"] for item in profiles
            ),
            "gap_over_threshold_count": sum(
                item["continuity"]["gap_over_threshold_count"] for item in profiles
            ),
            "nonpositive_interval_count": sum(
                item["continuity"]["nonpositive_interval_count"] for item in profiles
            ),
        },
    }
    return {
        "dataset": "SPMD RV_RX received remote-vehicle state observations",
        "input_zip": str(zip_path.resolve()),
        "parameters": {"segment_gap_cs": segment_gap_cs},
        "schema": {
            "documented_columns": EXPECTED_HEADER,
            "physical_data_column_count": EXPECTED_DATA_COLUMN_COUNT,
            "undocumented_trailing_columns": 4,
            "required_trailing_values": "empty",
        },
        "statistics_definition": {
            "row_count": "CSV data records, excluding the header.",
            "device_trip_count": "Distinct (DeviceID, Trip) pairs; Trip is not globally unique.",
            "time": "RV_RX Time is centiseconds since the receiver DAS started, not an absolute timestamp; it is distinct from millisecond-valued GpsTimeWsu and GenTime fields in other SPMD tables.",
            "continuity_key": ["DeviceID", "Trip", "RV_ID"],
            "adjacent_interval": "Current Time minus the preceding encountered Time for the same continuity key.",
            "segment": "One initial segment per continuity key, plus one segment for each adjacent interval strictly greater than segment_gap_cs.",
        },
        "files": profiles,
        "combined": combined,
        "limitations": [
            "RV_RX is a received remote-vehicle state observation table; it does not identify per-message delivery or provide Tx-Rx message matching.",
            "The table has no verified message generation timestamp, receiver timestamp, or MsgCount, so intervals and gaps are not latency or packet-loss estimates.",
            "The table has no controller, driver-warning response, or adoption field; it cannot establish message adoption or causal action effects.",
            "Time is relative to each receiver DAS start, so the combined minimum and maximum are coverage bounds in relative trip time, not a calendar range.",
            "Continuity statistics use file encounter order and are basic diagnostics; nonpositive intervals are reported because they can indicate duplicate or out-of-order observations.",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path, help="Path to RV_RX.csv.zip")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    parser.add_argument(
        "--segment-gap-cs",
        type=int,
        default=100,
        help="Start a new diagnostic segment after an interval greater than this value (default: 100, i.e. one second)",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = profile_zip(
        args.zip_path,
        segment_gap_cs=args.segment_gap_cs,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
