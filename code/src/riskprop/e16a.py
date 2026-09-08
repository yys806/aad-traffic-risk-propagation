"""Evidence-bounded E16-A communication observability contracts."""

from __future__ import annotations

import hashlib
import csv
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping

from riskprop.calibration import sha256_file


class CommunicationEvidenceError(ValueError):
    """Raised when a communication field gate is not identifiable."""


RV_RX_HEADER = (
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
)


def spmd_trip_split(device_id: object, trip: object) -> str:
    """Assign a complete SPMD device-trip pair without inspecting its outcomes."""

    digest = hashlib.sha256(f"{device_id}|{trip}".encode("utf-8")).digest()[0]
    return "calibration" if digest < 128 else "locked_holdout"


def evaluate_field_groups(
    columns: Iterable[str],
    *,
    required_groups: Mapping[str, Iterable[str]],
    raise_on_missing: bool = False,
) -> dict:
    """Match actual file columns to preregistered concepts without guessing values."""

    actual = {str(column).casefold(): str(column) for column in columns}
    matched: dict[str, str] = {}
    missing: list[str] = []
    for concept, alternatives in required_groups.items():
        found = next(
            (actual[str(candidate).casefold()] for candidate in alternatives if str(candidate).casefold() in actual),
            None,
        )
        if found is None:
            missing.append(str(concept))
        else:
            matched[str(concept)] = found
    result = {"pass": not missing, "matched_fields": matched, "missing_concepts": missing}
    if missing and raise_on_missing:
        raise CommunicationEvidenceError(
            "missing communication field concepts: " + ", ".join(missing)
        )
    return result


def profile_rv_rx_calibration(
    zip_path: str | Path, *, segment_gap_cs: int = 100
) -> dict:
    """Profile only preassigned calibration trips; ignore holdout outcome fields."""

    if segment_gap_cs < 0:
        raise ValueError("segment_gap_cs must be non-negative")
    zip_path = Path(zip_path)
    calibration_rows = 0
    ignored_rows = 0
    calibration_pairs: set[tuple[str, str]] = set()
    streams: set[tuple[str, str, str]] = set()
    last_time: dict[tuple[str, str, str], int] = {}
    gaps = 0
    nonpositive = 0
    intervals = 0
    member_summaries = []
    with zipfile.ZipFile(zip_path) as archive:
        members = [info for info in archive.infolist() if info.filename.lower().endswith(".csv")]
        if not members:
            raise CommunicationEvidenceError("RV_RX archive contains no CSV members")
        for info in members:
            member_calibration = 0
            member_ignored = 0
            with archive.open(info) as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                try:
                    header = next(reader)
                except StopIteration as error:
                    raise CommunicationEvidenceError(f"{info.filename}: missing header") from error
                if tuple(header) != RV_RX_HEADER:
                    raise CommunicationEvidenceError(f"{info.filename}: unexpected RV_RX header")
                for line_number, row in enumerate(reader, start=2):
                    if len(row) != 22 or any(value.strip() for value in row[18:]):
                        raise CommunicationEvidenceError(
                            f"{info.filename}:{line_number}: expected 18 documented plus four empty columns"
                        )
                    device, trip, time_raw, remote_vehicle = row[:4]
                    if spmd_trip_split(device, trip) != "calibration":
                        ignored_rows += 1
                        member_ignored += 1
                        continue
                    try:
                        time_cs = int(time_raw)
                    except ValueError as error:
                        raise CommunicationEvidenceError(
                            f"{info.filename}:{line_number}: Time must be integer centiseconds"
                        ) from error
                    calibration_rows += 1
                    member_calibration += 1
                    pair = (device, trip)
                    stream = (device, trip, remote_vehicle)
                    calibration_pairs.add(pair)
                    streams.add(stream)
                    previous = last_time.get(stream)
                    if previous is not None:
                        interval = time_cs - previous
                        intervals += 1
                        if interval > segment_gap_cs:
                            gaps += 1
                        if interval <= 0:
                            nonpositive += 1
                    last_time[stream] = time_cs
            member_summaries.append(
                {
                    "member": info.filename,
                    "calibration_rows": member_calibration,
                    "locked_holdout_rows_ignored": member_ignored,
                    "zip_crc32": f"{info.CRC:08x}",
                }
            )
    return {
        "schema_version": "e16a.rv-rx-calibration-profile.v1",
        "scientific_claim_eligible": False,
        "split_rule": "sha256(DeviceID|Trip) first byte < 128",
        "observable_boundary": "receive_state_continuity_only",
        "parameters": {"segment_gap_cs": segment_gap_cs},
        "calibration": {
            "row_count": calibration_rows,
            "device_trip_count": len(calibration_pairs),
            "stream_count": len(streams),
            "adjacent_interval_count": intervals,
            "gap_over_threshold_count": gaps,
            "nonpositive_interval_count": nonpositive,
        },
        "locked_holdout": {
            "rows_ignored": ignored_rows,
            "outcome_fields_retained": False,
            "trip_ids_materialized": False,
        },
        "members": member_summaries,
        "limitations": [
            "RV_RX rows are received remote-vehicle state observations, not message counts.",
            "Observation gaps are not packet-loss events.",
            "RV_RX has no verified controller-adoption field.",
        ],
    }


def write_rv_rx_calibration_profile(
    *, zip_path: str | Path, output_path: str | Path, segment_gap_cs: int = 100
) -> Path:
    output_path = Path(output_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    result = profile_rv_rx_calibration(zip_path, segment_gap_cs=segment_gap_cs)
    result["input_sha256"] = sha256_file(zip_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_path


def build_e16a_status_package(
    *,
    rv_rx_profile_path: str | Path,
    rv_rx_zip_path: str | Path,
    output_dir: str | Path,
    packet_access: dict,
) -> Path:
    """Seal the current observable boundary without inventing packet-level evidence."""

    profile_path = Path(rv_rx_profile_path)
    zip_path = Path(rv_rx_zip_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    packet_status = str(packet_access.get("status", "unknown"))
    packet_available = packet_status == "downloaded_and_verified"
    audit = {
        "schema_version": "e16a.communication-observability.v1",
        "experiment_id": "E16-A",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scientific_claim_eligible": False,
        "rv_rx_sha256": sha256_file(zip_path),
        "rv_rx_profile_sha256": sha256_file(profile_path),
        "rv_rx_row_count": profile.get("calibration", profile.get("combined", {})).get("row_count"),
        "rv_rx_device_trip_count": profile.get("calibration", profile.get("combined", {})).get("device_trip_count"),
        "observable_boundary": "receive_state_continuity_only",
        "packet_access": packet_access,
        "packet_schema_evaluated": False,
        "packet_loss_estimated": False,
        "latency_estimated": False,
        "adoption_inferred": False,
        "gate_status": (
            "pending_packet_schema_audit" if packet_available else "pending_official_packet_access"
        ),
        "limitations": profile.get("limitations", []),
        "note": "An HTTP/access failure is not a Packet schema failure. RV_RX gaps are not packet loss.",
    }
    (output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    provenance = {
        "schema_version": "e16a.provenance.v1",
        "source_profile": str(profile_path.resolve()),
        "source_rv_rx": str(zip_path.resolve()),
    }
    (output_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _seal(output_dir)
    return output_dir


def _seal(output_dir: Path) -> None:
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    manifest = {
        "schema_version": "e16a.manifest.v1",
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in files
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files.append(manifest_path)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n",
        encoding="utf-8",
        newline="\n",
    )
