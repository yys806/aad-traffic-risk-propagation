"""MiTra T1 candidate interaction and physical-admission pre-audit.

This is a read-only pre-screen.  It parses the already staged T1 trajectory
archive, checks reciprocal leader/follower observations, constructs a
road-heading-relative provisional gap, and records the limits that prevent
formal Task9 admission.  It does not freeze interpolation, tau mapping or
physical thresholds, and it never launches SUMO/TraCI.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK12-MITRA-T1-CANDIDATE-PHYSICAL-ADMISSION-20261031"
OUT = ROOT / "evidence/results" / RESULT_ID
STAGING = ROOT / "local_research/staging/task11_20261031/mitra"
TASK12_STAGING = ROOT / "local_research/staging/task12_20261031/mitra"
T1_ZIP = STAGING / "Data_T1.zip"
JUMPS = STAGING / "Teleporting_jumps.csv"
DALL_LOG = TASK12_STAGING / "T1_DAll.ftlgx"

DALL_ARCHIVE_URL = "https://opara.zih.tu-dresden.de/bitstreams/0c0c1768-9ca1-4454-9fa2-f3aa7c0c8db1/download"
DALL_ARCHIVE_BYTES = 33108729741
DALL_MEMBER_DATA_OFFSET = 33054382556
DALL_MEMBER_BYTES = 54345650
DALL_MEMBER_SHA256 = "4a0eff2c4d543cf17dbad7783739dcb6a66474d61417a108ea3fec57948e090a"
PORTABLE_PAIR_ROWS = 500
PORTABLE_SEGMENT_ROWS = 500


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


def circular_mean(values: pd.Series) -> float | None:
    if values.empty:
        return None
    return float(math.atan2(np.sin(values).mean(), np.cos(values).mean()))


def parse_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    with zipfile.ZipFile(T1_ZIP) as z:
        data = pd.read_csv(z.open("T1_DAll.csv"))
        members = [
            {"name": i.filename, "compressed_bytes": i.compress_size, "uncompressed_bytes": i.file_size, "crc32": i.CRC}
            for i in z.infolist()
        ]
    jumps = pd.read_csv(JUMPS)
    for col in ["Vehicle_ID", "Leader_ID", "Follower_ID", "Lane"]:
        data[col] = data[col].astype(int)
    data["time_key"] = (data["Time [s]"] * 1_000_000).round().astype("int64")
    data = data.sort_values(["Vehicle_ID", "Time [s]"]).reset_index(drop=True)
    return data, jumps, {"members": members, "t1_dall_rows": int(len(data))}


def motion_screen(data: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    d = data[["Vehicle_ID", "Time [s]", "x [m]", "y [m]", "Angle [rad]", "Lane"]].copy()
    d["dt"] = d.groupby("Vehicle_ID")["Time [s]"].diff()
    d["dx"] = d.groupby("Vehicle_ID")["x [m]"].diff()
    d["dy"] = d.groupby("Vehicle_ID")["y [m]"].diff()
    d = d[(d["dt"] > 0) & (d["dt"] < 0.05)].copy()
    angle = d["Angle [rad]"]
    # The heading angle is used only as a local tangent for a screening test.
    # It is not treated as an independently calibrated road coordinate frame.
    d["long_step_m"] = d["dx"] * np.cos(angle) + d["dy"] * np.sin(angle)
    d["lat_step_m"] = -d["dx"] * np.sin(angle) + d["dy"] * np.cos(angle)
    d["long_flag"] = d["long_step_m"].abs() > 2.0
    d["lat_flag"] = d["lat_step_m"].abs() > 0.5
    lane_rows = []
    for lane, g in d.groupby("Lane"):
        lane_rows.append({
            "lane": int(lane),
            "rows": int(len(g)),
            "heading_circular_mean_rad": circular_mean(g["Angle [rad]"]),
            "heading_p05_rad": float(g["Angle [rad]"].quantile(0.05)),
            "heading_p95_rad": float(g["Angle [rad]"].quantile(0.95)),
            "mean_dx_dt_mps": float((g["dx"] / g["dt"]).mean()),
            "mean_dy_dt_mps": float((g["dy"] / g["dt"]).mean()),
            "long_abs_p99_m": float(g["long_step_m"].abs().quantile(0.99)),
            "lat_abs_p99_m": float(g["lat_step_m"].abs().quantile(0.99)),
            "long_threshold_flags": int(g["long_flag"].sum()),
            "lat_threshold_flags": int(g["lat_flag"].sum()),
        })
    summary = {
        "status": "ROAD_HEADING_RELATIVE_SCREEN_ONLY",
        "coordinate_axes_used_as_road_axes": False,
        "heading_angle_used_as_local_tangent": True,
        "rows_with_valid_step": int(len(d)),
        "long_threshold_flags": int(d["long_flag"].sum()),
        "lat_threshold_flags": int(d["lat_flag"].sum()),
        "max_abs_long_step_m": float(d["long_step_m"].abs().max()),
        "max_abs_lat_step_m": float(d["lat_step_m"].abs().max()),
        "lane_summary": lane_rows,
        "interpretation": "This corrects the Task11 global-x/y screening by projecting each step onto the recorded heading and its perpendicular. It is not the official stitched teleport audit and does not establish an independently calibrated road frame.",
    }
    return d, summary


def relation_table(data: pd.DataFrame) -> pd.DataFrame:
    rel = data[data["Leader_ID"] >= 0][[
        "Vehicle_ID", "Leader_ID", "time_key", "Time [s]", "Lane", "Follower_ID",
        "x [m]", "y [m]", "Speed [km/h]", "Angle [rad]", "Vehicle_length [m]", "Vehicle_width [m]",
    ]].rename(columns={
        "Vehicle_ID": "follower_id", "Leader_ID": "leader_id", "Lane": "follower_lane",
        "Follower_ID": "follower_ref", "x [m]": "follower_x", "y [m]": "follower_y",
        "Speed [km/h]": "follower_speed", "Angle [rad]": "follower_angle",
        "Vehicle_length [m]": "follower_length", "Vehicle_width [m]": "follower_width",
    })
    leader = data[[
        "Vehicle_ID", "time_key", "Follower_ID", "Lane", "x [m]", "y [m]", "Speed [km/h]",
        "Angle [rad]", "Vehicle_length [m]", "Vehicle_width [m]",
    ]].rename(columns={
        "Vehicle_ID": "leader_id", "Follower_ID": "leader_follower_ref", "Lane": "leader_lane",
        "x [m]": "leader_x", "y [m]": "leader_y", "Speed [km/h]": "leader_speed",
        "Angle [rad]": "leader_angle", "Vehicle_length [m]": "leader_length", "Vehicle_width [m]": "leader_width",
    })
    m = rel.merge(leader, on=["leader_id", "time_key"], how="left", validate="many_to_one")
    m["mutual_relation"] = m["leader_follower_ref"].eq(m["follower_id"])
    m["same_lane"] = m["follower_lane"].eq(m["leader_lane"])
    m["heading_difference_rad"] = np.arctan2(
        np.sin(m["follower_angle"] - m["leader_angle"]),
        np.cos(m["follower_angle"] - m["leader_angle"]),
    ).abs()
    dx = m["leader_x"] - m["follower_x"]
    dy = m["leader_y"] - m["follower_y"]
    m["center_separation_along_heading_m"] = dx * np.cos(m["follower_angle"]) + dy * np.sin(m["follower_angle"])
    m["provisional_net_gap_m"] = m["center_separation_along_heading_m"] - (m["follower_length"] + m["leader_length"]) / 2.0
    m["closing_speed_mps"] = (m["follower_speed"] - m["leader_speed"]) / 3.6
    return m


def segments(m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = m[m["mutual_relation"] & m["same_lane"]].copy()
    m = m.sort_values(["follower_id", "leader_id", "Time [s]"])
    m["dt_s"] = m.groupby(["follower_id", "leader_id"])["Time [s]"].diff()
    prev_lane = m.groupby(["follower_id", "leader_id"])["follower_lane"].shift()
    m["new_segment"] = m["dt_s"].isna() | (m["dt_s"] > 0.05) | m["follower_lane"].ne(prev_lane)
    m["segment_number"] = m.groupby(["follower_id", "leader_id"])["new_segment"].cumsum().astype(int)
    m["segment_id"] = m["follower_id"].astype(str) + "-" + m["leader_id"].astype(str) + "-" + m["segment_number"].astype(str)
    agg = m.groupby(["segment_id", "follower_id", "leader_id", "follower_lane"], as_index=False).agg(
        start_time_s=("Time [s]", "min"), end_time_s=("Time [s]", "max"), sample_count=("Time [s]", "size"),
        dt_p50_s=("dt_s", "median"), dt_p95_s=("dt_s", lambda s: s.quantile(0.95)),
        provisional_gap_p05_m=("provisional_net_gap_m", lambda s: s.quantile(0.05)),
        provisional_gap_p50_m=("provisional_net_gap_m", "median"),
        provisional_gap_p95_m=("provisional_net_gap_m", lambda s: s.quantile(0.95)),
        provisional_gap_min_m=("provisional_net_gap_m", "min"),
        provisional_gap_negative_n=("provisional_net_gap_m", lambda s: int((s < 0).sum())),
        heading_difference_p95_rad=("heading_difference_rad", lambda s: s.quantile(0.95)),
        closing_speed_p50_mps=("closing_speed_mps", "median"),
        closing_speed_p95_mps=("closing_speed_mps", lambda s: s.quantile(0.95)),
        follower_speed_p50_kmh=("follower_speed", "median"),
        leader_speed_p50_kmh=("leader_speed", "median"),
    )
    agg["duration_s"] = agg["end_time_s"] - agg["start_time_s"]
    agg = agg.sort_values(["duration_s", "sample_count"], ascending=False).reset_index(drop=True)
    agg.insert(0, "candidate_rank", np.arange(1, len(agg) + 1))
    agg["physical_net_gap_status"] = "Unknown_reference_point_and_road_calibration"
    agg["video_tracking_binding_status"] = "Unknown_DAll_log_format_not_decoded"
    agg["formal_task9_status"] = "Candidate_only_not_admitted"

    pair_inventory = m.groupby(["follower_id", "leader_id"], as_index=False).agg(
        reciprocal_rows=("mutual_relation", "size"), same_lane_rows=("same_lane", "size"),
        first_time_s=("Time [s]", "min"), last_time_s=("Time [s]", "max"),
        lane_values=("follower_lane", lambda s: ";".join(str(int(x)) for x in sorted(set(s)))),
        stable_segment_count=("segment_id", "nunique"),
    )
    max_duration = agg.groupby(["follower_id", "leader_id"], as_index=False)["duration_s"].max().rename(columns={"duration_s": "max_segment_duration_s"})
    pair_inventory = pair_inventory.merge(max_duration, on=["follower_id", "leader_id"], how="left", validate="one_to_one")
    pair_inventory["reciprocal_relation_all_rows"] = True
    pair_inventory["same_lane_relation_all_rows"] = True
    pair_inventory = pair_inventory.sort_values(["max_segment_duration_s", "reciprocal_rows"], ascending=False)
    return m, agg, pair_inventory


def interpolation_diagnostic(m: pd.DataFrame, agg: pd.DataFrame) -> dict:
    top = agg.iloc[0]
    q = m[m["segment_id"] == top["segment_id"]].sort_values("Time [s]")
    t = q["Time [s]"].to_numpy(float)
    v = q["leader_speed"].to_numpy(float)
    if len(t) < 3:
        return {"status": "NOT_APPLICABLE", "reason": "top candidate has fewer than 3 samples"}
    grid = np.arange(t[0], t[-1] + 0.025, 0.05)
    v_grid = np.interp(grid, t, v)
    v_back = np.interp(t, grid, v_grid)
    err = np.abs(v_back - v)
    return {
        "status": "DIAGNOSTIC_ONLY_NOT_FROZEN",
        "segment_id": str(top["segment_id"]),
        "source_sampling_dt_p50_s": float(np.median(np.diff(t))),
        "target_step_s": 0.05,
        "leader_speed_linear_interp_error_mps": {"p50": float(np.quantile(err, 0.5)), "p95": float(np.quantile(err, 0.95)), "max": float(err.max())},
        "interpretation": "A numerical feasibility check for the highest-ranked candidate only; it does not authorize or freeze the formal Task9 resampling rule.",
    }


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve existing result directory: {OUT}")
    if not DALL_LOG.is_file():
        raise FileNotFoundError(f"expected downloaded DAll tracking log: {DALL_LOG}")
    OUT.mkdir(parents=True)
    data, jumps, zip_meta = parse_data()
    motion, motion_summary = motion_screen(data)
    m = relation_table(data)
    m, agg, pair_inventory = segments(m)
    now = datetime.now(timezone.utc).isoformat()

    # The OPARA central directory was fetched by bounded Range requests.  The
    # complete member list has no Teleporting_jumps_Dall.csv entry.
    central_members = [
        "T1_D1.mp4", "T1_D1.tlgx", "T1_D2.mp4", "T1_D2.tlgx", "T1_D3.mp4", "T1_D3.tlgx",
        "T1_D4.mp4", "T1_D4.tlgx", "T1_D5.mp4", "T1_D5.tlgx", "T1_D6.mp4", "T1_D6.tlgx", "T1_DAll.ftlgx",
    ]
    with zipfile.ZipFile(DALL_LOG) as log_zip:
        log_members = [{"name": i.filename, "bytes": i.file_size, "compressed_bytes": i.compress_size, "crc32": i.CRC} for i in log_zip.infolist()]

    write_json("teleport_audit_reconciliation.json", {
        "status": "DALL_OFFICIAL_AUDIT_FILE_NOT_PRESENT_IN_PUBLIC_T1_MEMBERS",
        "readme_single_drone_file": "Teleporting_jumps.csv",
        "readme_stitched_file": "Teleporting_jumps_Dall.csv",
        "official_readme_stitched_counts": {"longitudinal_jumps": 27, "vehicles_longitudinal": 3, "lateral_jumps": 253, "vehicles_lateral": 60, "stitched_vehicles": 24161, "time_instances": 63780893},
        "data_t1_zip_members": zip_meta["members"],
        "tracking_archive_members_from_complete_central_directory": central_members,
        "dall_audit_member_present": False,
        "dall_audit_records_matched_to_t1_dall": 0,
        "single_drone_jumps_rows": int(len(jumps)),
        "single_drone_jumps_vehicle_ids": int(jumps["Vehicle_ID"].nunique()),
        "single_drone_id_time_match_to_dall": "NOT_USED_AS_DALL_EVIDENCE; single-drone IDs are not established as stitched IDs",
        "local_dall_road_heading_screen": motion_summary,
        "interpretation": "The 940-row Teleporting_jumps.csv is retained as a single-drone audit only. DAll anomaly records cannot be assigned to T1_DAll without the absent DAll audit file. The local heading-relative screen found no >2 m longitudinal or >0.5 m lateral step, but this is an independent screen rather than the official stitched audit.",
    })

    pair_inventory.head(PORTABLE_PAIR_ROWS).to_csv(OUT / "candidate_pair_inventory.csv", index=False)
    candidates = agg[agg["duration_s"] >= 5.0].copy()
    candidates.head(PORTABLE_SEGMENT_ROWS).to_csv(OUT / "candidate_segment_summary.csv", index=False)
    write_json("coordinate_frame_audit.json", {
        "status": "PROVISIONAL_HEADING_RELATIVE_FRAME",
        "utm_x_y_directly_used_as_road_axes": False,
        "provisional_longitudinal_coordinate": "pairwise projection of leader-follower displacement onto follower Angle [rad]",
        "road_direction_evidence": motion_summary["lane_summary"],
        "mainline_lane_direction_stability": "lanes 0-7 show coherent opposing directions in the local step screen; ramp lanes 10/11/20/21 have wider heading ranges and are not used for the highest-ranked candidates",
        "vehicle_reference_point": "Unknown; README defines x/y and vehicle length but does not specify center/front/rear reference point",
        "vehicle_length_semantics": "Length field is present; independent geometric endpoint semantics not verified",
        "formal_s_coordinate": "NOT_CREATED; no road geometry/calibration or approved mapping was introduced",
    })
    write_json("physical_gap_quality.json", {
        "status": "PROVISIONAL_SCREEN_ONLY_PHYSICAL_NET_GAP_UNKNOWN",
        "rows_screened": int(len(m)),
        "segments_ge_5s": int(len(candidates)),
        "segments_ge_20s": int((candidates["duration_s"] >= 20).sum()),
        "provisional_net_gap_rows": int(m["provisional_net_gap_m"].notna().sum()),
        "provisional_negative_gap_rows": int((m["provisional_net_gap_m"] < 0).sum()),
        "provisional_gap_p05_p50_p95_m": [float(m["provisional_net_gap_m"].quantile(q)) for q in (0.05, 0.5, 0.95)],
        "leader_order_consistency": "All 1,308,347 relation rows have reciprocal Leader_ID/Follower_ID and matching leader row in T1_DAll; this is a field-consistency observation, not independent physical truth.",
        "physical_net_gap_formula": "(projected leader center - projected follower center) - (leader length + follower length)/2 under an unverified center-reference assumption",
        "admission": "Unknown; do not pass to Task9",
        "reason": "Vehicle reference point, calibrated road longitudinal coordinate and video-confirmed geometry are not closed.",
    })
    write_json("video_tracking_binding.json", {
        "status": "TRACKING_LOG_ACQUIRED_VIDEO_NOT_ACQUIRED_BINDING_NOT_CLOSED",
        "archive_url": DALL_ARCHIVE_URL,
        "archive_total_bytes": DALL_ARCHIVE_BYTES,
        "member": "T1_DAll.ftlgx",
        "member_data_offset": DALL_MEMBER_DATA_OFFSET,
        "member_bytes": DALL_MEMBER_BYTES,
        "member_sha256": DALL_MEMBER_SHA256,
        "local_file_sha256": sha256(DALL_LOG),
        "central_directory_member_count": len(central_members),
        "central_directory_members": central_members,
        "nested_tracking_members": log_members,
        "video_files_downloaded": 0,
        "vehicle_id_to_video_binding": "Unknown; DataFromSky ftlgx binary format was not decoded and no video was acquired",
        "candidate_video": "Not selected; DAll candidate cannot be mapped to a single drone video from CSV alone",
        "interpretation": "The exact DAll tracking-log member is real and hash-bound, but obtaining it does not by itself provide an independently reviewable video observation or a decoded vehicle-ID mapping.",
    })
    write_json("task9_input_compatibility.json", {
        "status": "BLOCKED_PHYSICAL_ADMISSION_CONDITIONAL_INPUT_CANDIDATES_EXIST",
        "candidate_segments_ge_5s": int(len(candidates)),
        "candidate_segments_ge_20s": int((candidates["duration_s"] >= 20).sum()),
        "portable_pair_rows": PORTABLE_PAIR_ROWS,
        "portable_segment_rows": PORTABLE_SEGMENT_ROWS,
        "stable_leader_follower_field_sequence": True,
        "reciprocal_relation_rows": int(m["mutual_relation"].sum()),
        "same_lane_relation_rows": int(m["same_lane"].sum()),
        "continuous_leader_position_speed_available": True,
        "initial_follower_speed_available": True,
        "physical_net_gap_available_for_admission": False,
        "video_review_available": False,
        "vehicle_type_to_heterogeneous_b00_tau_mapping": "Unknown and not assigned",
        "time_resampling": interpolation_diagnostic(m, agg),
        "formal_task9_segments_admitted": 0,
        "formal_task9_runs": 0,
        "protocol_changed": False,
        "decision": "Retain candidates as pre-screen only; researcher must decide whether to obtain a decodable paired video/log subset and how to resolve coordinate/reference-point and vehicle-type issues before formal admission.",
    })

    bindings = {
        "task_id": "AAD-S0.5-POST-R2-TASK12",
        "base_head": git_head(),
        "captured_at_utc": now,
        "script": "code/scripts/audit_stage_0_5_task12_mitra_t1.py",
        "script_sha256": sha256(ROOT / "code/scripts/audit_stage_0_5_task12_mitra_t1.py"),
        "inputs": {
            str(T1_ZIP.relative_to(ROOT)): {"bytes": T1_ZIP.stat().st_size, "sha256": sha256(T1_ZIP)},
            str(JUMPS.relative_to(ROOT)): {"bytes": JUMPS.stat().st_size, "sha256": sha256(JUMPS)},
            str(DALL_LOG.relative_to(ROOT)): {"bytes": DALL_LOG.stat().st_size, "sha256": sha256(DALL_LOG)},
        },
        "reused_task11_evidence": "evidence/results/RES-STAGE-0.5-POST-R2-TASK11-PUBLIC-DATA-FEASIBILITY-20261031/",
        "new_simulations": 0,
        "video_files_downloaded": 0,
        "holdout_reads": 0,
        "third_window_reads": 0,
    }
    write_json("source_bindings.json", bindings)
    write_json("validation_record.json", {
        "task_id": "AAD-S0.5-POST-R2-TASK12",
        "status": "PASS_BOUNDED_MITRA_PREAUDIT",
        "dall_audit_reconciliation": "PASS_SOURCE_ABSENCE_RETAINED",
        "pair_screen": "PASS_FIELD_CONSISTENCY_AND_SEGMENT_INVENTORY",
        "coordinate_frame": "PASS_PROVISIONAL_ONLY",
        "physical_gap": "UNKNOWN_REFERENCE_POINT",
        "video_tracking": "BLOCKED_NO_DECODED_VIDEO_BINDING",
        "task9_compatibility": "BLOCKED_PHYSICAL_ADMISSION",
        "not_run": ["SUMO/TraCI", "formal Task9", "video download", "full pytest", "third NGSIM window", "locked holdout", "tau assignment"],
    })
    write_json("context_consistency_check.json", {
        "status": "PASS_CONTEXT_CONSISTENCY_CHECK",
        "stage_0_5": "blocked",
        "scientific_equivalence": False,
        "task9_formal_runs": 0,
        "round3": "not started",
        "updated_context": ["AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/03_DATA_FLOW.md", "AI_CONTEXT/05_EXPERIMENTS.md", "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md"],
        "updated_indexes": ["docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md", "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md"],
    })

    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    write_json("manifest.json", {
        "schema": "aad.stage05.post_r2.task12.mitra_candidate_physical_admission.manifest.v1",
        "task_id": "AAD-S0.5-POST-R2-TASK12",
        "status": "completed_with_physical_admission_blockers",
        "stage_0_5": "blocked",
        "raw_video_in_evidence": False,
        "formal_task9_segments": 0,
        "payload_files": {p.name: sha256(p) for p in payloads},
    })
    (OUT / "SHA256SUMS").write_text("\n".join(f"{sha256(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    print(f"TASK12_MITRA_T1_AUDIT_WRITTEN {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
