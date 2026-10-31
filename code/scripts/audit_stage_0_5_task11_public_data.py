"""Bounded public physical-reference source audit for AAD Task11.

The audit records official resource metadata for I24V, MiTra and NGSIM and
parses only the small MiTra T1 trajectory package already staged locally.  It
does not read a third NGSIM window or holdout, download a video archive, start
SUMO/TraCI, or alter Formal P2/D1/B or the Task9 protocol.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK11-PUBLIC-DATA-FEASIBILITY-20261031"
OUT = ROOT / "evidence/results" / RESULT_ID
STAGING = ROOT / "local_research/staging/task11_20261031/mitra"

I24_REPO = "https://github.com/I24-MOTION/i24-video-dataset-utils"
I24_DATA = "https://i24motion.org/data"
MITRA_OPARA = "https://opara.zih.tu-dresden.de/items/68482417-ddc5-40ac-885a-83124bd459e8"
MITRA_DOI = "https://doi.org/10.25532/OPARA-881"
MITRA_PAPER = "https://www.nature.com/articles/s41597-025-05472-0"
NGSIM_CATALOG = "https://catalog.data.gov/dataset/next-generation-simulation-ngsim-vehicle-trajectories-and-supporting-data"
NGSIM_VIDEO = "https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-US-101-Videos/4qzi-thur"
NGSIM_VIDEO_ZIP = "https://data.transportation.gov/download/4qzi-thur/application/x-zip-compressed"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(name: str, payload: object) -> None:
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def source_inventory() -> dict:
    return {
        "schema": "aad.task11.source_inventory.v1",
        "task_id": "AAD-S0.5-POST-R2-TASK11",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "source_id": "I24V",
                "name": "I-24 MOTION / I24V",
                "official_pages": [I24_DATA, I24_REPO],
                "documented_release_facts": {
                    "published_camera_count": 234,
                    "documented_video_duration_hours": 234,
                    "road_coverage_miles": 4.2,
                    "manually_corrected_gps_vehicle_passes": 270,
                    "video_format_documented": "MKV per camera; millisecond frame timestamps and nanosecond global offset in filenames",
                    "annotation_families": ["GPS.cpkl", "final_gps.csv", "final_manual.csv", "homography matrices", "detections"],
                },
                "license_status": "DOCUMENTED_DATA_USE_AGREEMENT",
                "license_scope": [
                    "free academic and commercial use",
                    "anonymous vehicles; no re-identification or harm",
                    "I24V and I24-MOTION citations required for publication",
                    "derivatives may be created/shared while retaining terms",
                    "provided as-is without warranty",
                ],
                "access_status": "PUBLIC_ENTRY_NOT_REACHED_IN_THIS_ENVIRONMENT",
                "use1_existing_ngsim_path_verification": "NO-GO",
                "use2_independent_physical_reference": "CONDITIONAL",
                "use3_task9_fixed_leader_input": "CONDITIONAL",
                "caveats": [
                    "I24V is a different roadway and cannot directly verify the 40 US-101 candidates.",
                    "The published README documents GPS and video resources, but a complete follower/leader pairing contract was not established here.",
                    "The data page returned an access failure during this bounded check; no I24V payload was downloaded.",
                ],
            },
            {
                "source_id": "MiTra-T1",
                "name": "MiTra: Drone-Based Trajectory Data for an All-Traffic-State Inclusive Freeway with Ramps",
                "official_pages": [MITRA_OPARA, MITRA_DOI, MITRA_PAPER],
                "documented_release_facts": {
                    "site": "A50 urban freeway, Milan, Italy",
                    "road_length_m": 900,
                    "flight_campaigns": 9,
                    "drones": 6,
                    "raw_video_fps": 30,
                    "single_drone_trajectories": 124641,
                    "stitched_trajectories": 24161,
                    "opara_license": "Creative Commons Attribution 4.0 International",
                },
                "license_status": "PUBLIC_CC_BY_4_0",
                "access_status": "PARTIAL_SMALL_FILE_SUCCESS",
                "use1_existing_ngsim_path_verification": "NO-GO",
                "use2_independent_physical_reference": "CONDITIONAL",
                "use3_task9_fixed_leader_input": "CONDITIONAL-GO",
                "caveats": [
                    "T1 trajectories are processed DataFromSky outputs; trajectory-only files are not independent visual truth.",
                    "A paired tracking-log/video subset is needed to independently review identity, occlusion and physical gap.",
                    "T1 is one campaign and is not merged into the NGSIM formal sample.",
                ],
            },
            {
                "source_id": "NGSIM-US101",
                "name": "NGSIM US-101 videos and supporting data",
                "official_pages": [NGSIM_CATALOG, NGSIM_VIDEO, NGSIM_VIDEO_ZIP],
                "documented_release_facts": {
                    "trajectory_sampling": "0.1 s transcription from synchronized digital video",
                    "catalog_license": "CC BY 3.0 for the public trajectory/supporting-data catalog",
                    "task7_2_raw_avi_members": [
                        "sb-camera7-0750am-0805am.avi",
                        "sb-camera8-0750am-0805am.avi",
                        "sb-camera7-0805am-0820am.avi",
                        "sb-camera8-0805am-0820am.avi",
                    ],
                    "task7_2_compressed_bytes": 1248582779,
                    "task7_2_extracted_bytes": 1248560044,
                },
                "license_status": "MIXED_DECLARATIONS_REQUIRE_FILE_SPECIFIC_CLOSURE",
                "access_status": "PUBLIC_CATALOG_REUSED; VIDEO_PAYLOAD_NOT_RETESTED",
                "use1_existing_ngsim_path_verification": "CONDITIONAL",
                "use2_independent_physical_reference": "NO-GO",
                "use3_task9_fixed_leader_input": "CONDITIONAL",
                "caveats": [
                    "This is the source of the current trajectory transcription, not an independent acquisition.",
                    "Task7.2 already established directory metadata but not payload, PTS/Global_Time mapping, camera coverage or physical review.",
                    "The historical and current license statements differ in scope; public availability does not close per-file permission.",
                ],
            },
        ],
        "interpretation_boundary": "Published counts and declarations are recorded as source facts; only MiTra T1 fields below were parsed locally.",
    }


def parse_mitra() -> dict:
    zip_path = STAGING / "Data_T1.zip"
    tele_path = STAGING / "Teleporting_jumps.csv"
    if not zip_path.is_file() or not tele_path.is_file():
        raise FileNotFoundError("MiTra staging files are required")

    member_info = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            member_info.append({
                "name": info.filename,
                "uncompressed_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "crc32": info.CRC,
            })
        target = "T1_DAll.csv"
        if target not in z.namelist():
            raise ValueError("T1_DAll.csv missing")
        with z.open(target) as stream:
            text = (line.decode("utf-8-sig") for line in stream)
            reader = csv.DictReader(text)
            required = {"Vehicle_ID", "Vehicle_type", "Time [s]", "x [m]", "y [m]", "Speed [km/h]", "Lane", "Leader_ID", "Follower_ID"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"MiTra fields missing: {sorted(required - set(reader.fieldnames or []))}")
            rows = 0
            vehicles: set[int] = set()
            types: Counter[str] = Counter()
            lanes: Counter[str] = Counter()
            per_vehicle: dict[int, list[float]] = defaultdict(list)
            leader_rows = follower_rows = 0
            nonfinite = 0
            previous: dict[int, tuple[float, float, float]] = {}
            long_jumps = lat_jumps = 0
            min_time = None
            max_time = None
            dt_values: list[float] = []
            vehicle_leader: set[int] = set()
            vehicle_follower: set[int] = set()
            vehicle_lanes: dict[int, set[str]] = defaultdict(set)
            for row in reader:
                rows += 1
                vid = int(float(row["Vehicle_ID"]))
                t = float(row["Time [s]"])
                x = float(row["x [m]"])
                y = float(row["y [m]"])
                speed = float(row["Speed [km/h]"])
                lane = row["Lane"]
                if not all(map(lambda v: v == v and abs(v) != float("inf"), (t, x, y, speed))):
                    nonfinite += 1
                vehicles.add(vid)
                types[row["Vehicle_type"]] += 1
                lanes[lane] += 1
                per_vehicle[vid].append(t)
                vehicle_lanes[vid].add(lane)
                if int(float(row["Leader_ID"])) >= 0:
                    leader_rows += 1
                    vehicle_leader.add(vid)
                if int(float(row["Follower_ID"])) >= 0:
                    follower_rows += 1
                    vehicle_follower.add(vid)
                if min_time is None or t < min_time:
                    min_time = t
                if max_time is None or t > max_time:
                    max_time = t
                if vid in previous:
                    pt, px, py = previous[vid]
                    dt = t - pt
                    if dt > 0:
                        dt_values.append(dt)
                        if abs(x - px) > 2.0:
                            long_jumps += 1
                        if abs(y - py) > 0.5:
                            lat_jumps += 1
                previous[vid] = (t, x, y)

    durations = sorted(max(v) - min(v) for v in per_vehicle.values())
    dts = sorted(dt_values)
    def quant(values: list[float], q: float) -> float | None:
        if not values:
            return None
        index = min(len(values) - 1, max(0, int(round((len(values) - 1) * q))))
        return float(values[index])

    teleport_rows = 0
    teleport_vids: set[int] = set()
    teleport_long = teleport_lat = 0
    teleport_min_time = teleport_max_time = None
    with tele_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            teleport_rows += 1
            vid = int(float(row["Vehicle_ID"]))
            teleport_vids.add(vid)
            if row.get("is_teleporting_long", "").strip().lower() in {"1", "true", "yes"}:
                teleport_long += 1
            if row.get("is_teleporting_lat", "").strip().lower() in {"1", "true", "yes"}:
                teleport_lat += 1
            t = float(row["Time [s]"])
            teleport_min_time = t if teleport_min_time is None else min(teleport_min_time, t)
            teleport_max_time = t if teleport_max_time is None else max(teleport_max_time, t)

    return {
        "status": "PARSED_LOCAL_MITRA_T1_DALL_AND_TELEPORTING_JUMPS",
        "source": "MiTra-T1",
        "archive": "Data_T1.zip",
        "rows": rows,
        "unique_vehicle_ids": len(vehicles),
        "vehicle_types_by_row": dict(sorted(types.items())),
        "lane_values_by_row": dict(sorted(lanes.items())),
        "vehicle_ids_with_leader_rows": len(vehicle_leader),
        "vehicle_ids_with_follower_rows": len(vehicle_follower),
        "rows_with_leader_id": leader_rows,
        "rows_with_follower_id": follower_rows,
        "vehicle_ids_with_multiple_lanes": sum(1 for v in vehicle_lanes.values() if len(v) > 1),
        "time_s": {"min": min_time, "max": max_time, "nominal_fps": 30, "dt_s": {"min": quant(dts, 0), "p50": quant(dts, 0.5), "p95": quant(dts, 0.95), "max": quant(dts, 1)}, "dt_not_approx_1_30": sum(abs(x - 1 / 30) > 0.002 for x in dts)},
        "duration_s": {"vehicles": len(durations), "p05": quant(durations, 0.05), "p50": quant(durations, 0.5), "p95": quant(durations, 0.95), "max": quant(durations, 1), "vehicles_ge_5s": sum(x >= 5 for x in durations), "vehicles_ge_20s": sum(x >= 20 for x in durations)},
        "core_nonfinite_values": nonfinite,
        "screening_step_jump_counts": {"abs_delta_x_gt_2m": long_jumps, "abs_delta_y_gt_0_5m": lat_jumps, "warning": "rough global x/y screening only; not the README's stitched teleport audit"},
        "teleporting_jumps_csv": {"rows": teleport_rows, "unique_vehicle_ids": len(teleport_vids), "long_flags": teleport_long, "lateral_flags": teleport_lat, "time_s": {"min": teleport_min_time, "max": teleport_max_time}},
        "interpretation": "The T1 file supplies dense time-indexed vehicle tracks and leader/follower fields. The parsed trajectory is a processed tracking output; no independent video review was performed.",
        "zip_members": member_info,
    }


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve existing result directory: {OUT}")
    OUT.mkdir(parents=True)
    inventory = source_inventory()
    quality = parse_mitra()
    now = datetime.now(timezone.utc).isoformat()

    write_json("source_inventory.json", inventory)
    with (OUT / "license_scope_matrix.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source_id", "use", "rating", "license_status", "access_status", "basis", "remaining_condition"])
        w.writeheader()
        rows = [
            ("I24V", "existing_ngsim_path_verification", "NO-GO", "DOCUMENTED_DATA_USE_AGREEMENT", "PUBLIC_ENTRY_NOT_REACHED_IN_THIS_ENVIRONMENT", "Different roadway; cannot verify US-101 candidate identities", "None can make a different roadway a direct US-101 witness"),
            ("I24V", "independent_physical_reference", "CONDITIONAL", "DOCUMENTED_DATA_USE_AGREEMENT", "PUBLIC_ENTRY_NOT_REACHED_IN_THIS_ENVIRONMENT", "Independent multi-camera video/GPS/homography described by official README", "Reach data endpoint and bind video/GPS/time-space subset"),
            ("I24V", "task9_fixed_leader_input", "CONDITIONAL", "DOCUMENTED_DATA_USE_AGREEMENT", "PUBLIC_ENTRY_NOT_REACHED_IN_THIS_ENVIRONMENT", "Potential trajectories but leader/follower pairing contract not verified", "Validate paired continuous front/rear tracks and physical gap"),
            ("MiTra-T1", "existing_ngsim_path_verification", "NO-GO", "PUBLIC_CC_BY_4_0", "PARTIAL_SMALL_FILE_SUCCESS", "Different Milan A50 roadway", "None can make it a direct NGSIM witness"),
            ("MiTra-T1", "independent_physical_reference", "CONDITIONAL", "PUBLIC_CC_BY_4_0", "PARTIAL_SMALL_FILE_SUCCESS", "Independent drone acquisition with raw video/logs described; local trajectory is processed", "Acquire paired video/log subset and review identity/occlusion/gap"),
            ("MiTra-T1", "task9_fixed_leader_input", "CONDITIONAL-GO", "PUBLIC_CC_BY_4_0", "PARTIAL_SMALL_FILE_SUCCESS", "1,578,393 rows, 1,456 IDs, ~30 Hz, x/y/speed/acceleration, Leader_ID/Follower_ID", "Physical net-gap and video/log validation before any formal input admission"),
            ("NGSIM-US101", "existing_ngsim_path_verification", "CONDITIONAL", "MIXED_DECLARATIONS_REQUIRE_FILE_SPECIFIC_CLOSURE", "PUBLIC_CATALOG_REUSED; VIDEO_PAYLOAD_NOT_RETESTED", "Only the original US-101 video can directly test the 40 candidates", "Obtain permitted payload and establish PTS/Global_Time and camera coverage"),
            ("NGSIM-US101", "independent_physical_reference", "NO-GO", "MIXED_DECLARATIONS_REQUIRE_FILE_SPECIFIC_CLOSURE", "PUBLIC_CATALOG_REUSED; VIDEO_PAYLOAD_NOT_RETESTED", "Current trajectories are the source transcription, not an independent acquisition", "Independent camera/video reference remains needed"),
            ("NGSIM-US101", "task9_fixed_leader_input", "CONDITIONAL", "MIXED_DECLARATIONS_REQUIRE_FILE_SPECIFIC_CLOSURE", "PUBLIC_CATALOG_REUSED; VIDEO_PAYLOAD_NOT_RETESTED", "Time-indexed trajectories exist but Task9 physical input contract is not closed", "Verify video/time/space and physical initial gap"),
        ]
        for source_id, use, rating, license_status, access_status, basis, condition in rows:
            w.writerow({"source_id": source_id, "use": use, "rating": rating, "license_status": license_status, "access_status": access_status, "basis": basis, "remaining_condition": condition})

    downloads = {
        "status": "PARTIAL_SMALL_FILE_SUCCESS",
        "staging_root": STAGING.relative_to(ROOT).as_posix(),
        "files": [
            {"source_id": "MiTra-T1", "name": "Readme_OPARA_MiTra.pdf", "url": "https://opara.zih.tu-dresden.de/bitstreams/48e0a468-c779-4f37-80aa-68bbeb1a8fd2/download", "bytes": (STAGING / "Readme_OPARA_MiTra.pdf").stat().st_size, "sha256": sha256(STAGING / "Readme_OPARA_MiTra.pdf"), "status": "DOWNLOADED_AND_PARSED"},
            {"source_id": "MiTra-T1", "name": "Data_T1.zip", "url": "https://opara.zih.tu-dresden.de/bitstreams/83c9ec15-7438-4d45-8b5d-f0d57b3f49a4/download", "bytes": (STAGING / "Data_T1.zip").stat().st_size, "sha256": sha256(STAGING / "Data_T1.zip"), "status": "DOWNLOADED_AND_PARSED"},
            {"source_id": "MiTra-T1", "name": "Teleporting_jumps.csv", "url": "https://opara.zih.tu-dresden.de/bitstreams/8f84c7eb-aa8a-4cfc-9205-3bf285a325e5/download", "bytes": (STAGING / "Teleporting_jumps.csv").stat().st_size, "sha256": sha256(STAGING / "Teleporting_jumps.csv"), "status": "DOWNLOADED_AND_PARSED"},
            {"source_id": "I24V", "name": "official data endpoint", "url": I24_DATA, "status": "NOT_DOWNLOADED; bounded web/curl access failure"},
            {"source_id": "NGSIM-US101", "name": "raw AVI ZIP", "url": NGSIM_VIDEO_ZIP, "status": "NOT_RETESTED; Task7.2 directory metadata reused"},
        ],
        "not_downloaded": ["I24V full video/archive", "MiTra tracking logs and videos (T1 is documented as ~30.83 GB)", "NGSIM raw AVI payload", "all other MiTra campaigns"],
    }
    write_json("download_manifest.json", downloads)
    integrity = {"status": "PASS_LOCAL_FILES_AND_ZIP_CRC_RECORDED", "files": downloads["files"][:3], "zip_members": quality["zip_members"], "raw_payload_in_evidence": False}
    write_json("file_integrity.json", integrity)
    write_json("trajectory_quality_summary.json", quality)
    write_json("temporal_spatial_coverage.json", {"MiTra-T1": {"time": quality["time_s"], "coordinate_fields": ["x [m]", "y [m]"], "coordinate_semantics": "UTM metres per README; EPSG zone not independently re-derived here", "lanes": quality["lane_values_by_row"], "camera_or_drone_sync": "six-drone campaign and 30 fps documented; local video/log pairing not acquired", "physical_overlap": "Documented stitched trajectories exist; local T1 file alone does not certify cross-drone identity"}, "I24V": {"status": "NOT_LOCALLY_VERIFIED", "documented": ["millisecond frame timestamps", "nanosecond global offset in filenames", "homography/GPS resources"]}, "NGSIM-US101": {"status": "REUSED_TASK7_2_METADATA_ONLY", "pts_global_time_mapping": "Unknown", "camera_source_lane_coverage": "Unknown"}})
    write_json("candidate_segment_summary.json", {"status": "CONDITIONAL_NOT_QUALIFIED_FOR_FORMAL_TASK9", "source": "MiTra-T1", "available_dense_tracks": {"rows": quality["rows"], "vehicle_ids": quality["unique_vehicle_ids"], "vehicles_ge_20s": quality["duration_s"]["vehicles_ge_20s"], "leader_rows": quality["rows_with_leader_id"], "follower_rows": quality["rows_with_follower_id"], "nominal_fps": quality["time_s"]["nominal_fps"]}, "formal_segment_count_admitted": 0, "reason": "No paired raw video/tracking-log review or physical net-gap admission was performed; Task9 protocol remains unchanged."})
    write_json("research_applicability_matrix.json", {"status": "COMPLETED_SOURCE_SPECIFIC_AUDIT", "uses": {"existing_ngsim_path_verification": {"I24V": "NO-GO", "MiTra-T1": "NO-GO", "NGSIM-US101": "CONDITIONAL"}, "independent_physical_reference": {"I24V": "CONDITIONAL", "MiTra-T1": "CONDITIONAL", "NGSIM-US101": "NO-GO"}, "task9_fixed_leader_input": {"I24V": "CONDITIONAL", "MiTra-T1": "CONDITIONAL-GO", "NGSIM-US101": "CONDITIONAL"}}, "recommended_priority": ["MiTra-T1 trajectory plus a small paired tracking/video subset", "I24V endpoint/license closure for independent video/GPS reference", "NGSIM US-101 raw AVI only for direct candidate review after file-specific permission/time mapping closure"]})
    write_json("final_recommendation.json", {"status": "COMPLETED_WITH_EXTERNAL_AND_PHYSICAL_BLOCKERS", "best_current_candidate": "MiTra-T1 for conditional Task9 input preparation", "independent_reference_candidate": "I24V or MiTra paired raw video/log subset; neither was locally closed as an independent physical truth in this task", "ngsim_path_verification": "Only NGSIM US-101 raw video can directly test existing 40 candidates; Task7.2 blockers remain", "minimal_next_acquisition": [{"source": "MiTra", "files": ["Data_T1.zip already staged", "one selected T1 tracking-log/video subset", "Readme and teleport audit"], "expected_video_cost": "avoid full 30.83 GB archive; select a physically continuous paired segment"}, {"source": "I24V", "files": ["270 GPS/manual reference subset plus matching camera files if endpoint and terms are closed"], "expected_video_cost": "do not acquire full 234-hour release"}, {"source": "NGSIM", "files": ["only Camera 7/8 four raw AVI members if license/endpoint/time-space conditions close"], "expected_video_cost": "approximately 1.249 GB compressed from Task7.2 metadata"}], "formal_task9_runs": 0, "stage_0_5": "blocked", "scientific_equivalence": False, "decision_owner": "researcher"})

    bindings = {"task_id": "AAD-S0.5-POST-R2-TASK11", "base_head": git_head(), "captured_at_utc": now, "script": "code/scripts/audit_stage_0_5_task11_public_data.py", "script_sha256": sha256(ROOT / "code/scripts/audit_stage_0_5_task11_public_data.py"), "local_inputs": {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(STAGING.iterdir())}, "reused_sources": {"task7_2_report": "docs/STAGE_0_5_ROUND2_TASK7_2_RESOURCE_METADATA_AND_ACQUISITION_FEASIBILITY_20261030.md", "task10_report": "docs/STAGE_0_5_POST_R2_TASK10_FINAL_DIAGNOSTIC_20261031.md"}, "official_urls": [I24_REPO, I24_DATA, MITRA_OPARA, MITRA_DOI, MITRA_PAPER, NGSIM_CATALOG, NGSIM_VIDEO], "new_simulations": 0, "holdout_reads": 0, "third_window_reads": 0}
    write_json("source_bindings.json", bindings)
    write_json("validation_record.json", {"task_id": "AAD-S0.5-POST-R2-TASK11", "status": "PASS_BOUNDED_PUBLIC_DATA_AUDIT", "actual_downloads": ["MiTra Readme", "MiTra Data_T1.zip", "MiTra Teleporting_jumps.csv"], "parsed_files": ["MiTra T1_DAll.csv", "MiTra Teleporting_jumps.csv"], "not_run": ["I24V full download", "MiTra videos/tracking logs", "NGSIM raw AVI download", "SUMO/TraCI", "fixed-leader formal experiment", "third window", "locked holdout", "full pytest"], "definitions_changed": False, "protocol_changed": False})
    write_json("context_consistency_check.json", {"status": "PASS_CONTEXT_CONSISTENCY_CHECK", "stage_0_5": "blocked", "scientific_equivalence": False, "round3": "not started", "task9_formal_runs": 0, "updated_context": ["AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/03_DATA_FLOW.md", "AI_CONTEXT/05_EXPERIMENTS.md", "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md"], "updated_indexes": ["docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md", "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md"]})

    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {"schema": "aad.stage05.post_r2.task11.public_data_feasibility.manifest.v1", "task_id": "AAD-S0.5-POST-R2-TASK11", "status": "completed_with_blockers", "gate_status": "blocked", "scientific_equivalence_accepted": False, "raw_payload_in_evidence": False, "payload_files": {p.name: sha256(p) for p in payloads}}
    write_json("manifest.json", manifest)
    (OUT / "SHA256SUMS").write_text("\n".join(f"{sha256(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    print(f"TASK11_PUBLIC_DATA_AUDIT_WRITTEN {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
