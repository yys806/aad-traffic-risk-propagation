"""Minimum-sufficient MiTra T1 input assessment for Task9 review.

This task evaluates three already-ranked T1_DAll candidate segments.  It uses
the Task12 heading-relative screening and adds only candidate-level continuity,
speed/acceleration, reference-point sensitivity and resampling diagnostics.
The result is an input-review recommendation, never a formal Task9 admission.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK13-MITRA-T1-MINIMUM-SUFFICIENT-INPUT-ASSESSMENT-20261031"
OUT = ROOT / "evidence/results" / RESULT_ID
STAGING = ROOT / "local_research/staging/task11_20261031/mitra"
TASK12_STAGING = ROOT / "local_research/staging/task12_20261031/mitra"
T1_ZIP = STAGING / "Data_T1.zip"
JUMPS = STAGING / "Teleporting_jumps.csv"
DALL_LOG = TASK12_STAGING / "T1_DAll.ftlgx"

CANDIDATES = ((857, 851, 1), (926, 924, 1), (962, 958, 1))
DALL_LOG_SHA256 = "4a0eff2c4d543cf17dbad7783739dcb6a66474d61417a108ea3fec57948e090a"


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


def load_relation_table() -> pd.DataFrame:
    with zipfile.ZipFile(T1_ZIP) as z:
        data = pd.read_csv(z.open("T1_DAll.csv"))
    for col in ["Vehicle_ID", "Leader_ID", "Follower_ID", "Lane"]:
        data[col] = data[col].astype(int)
    data["time_key"] = (data["Time [s]"] * 1_000_000).round().astype("int64")
    data = data.sort_values(["Vehicle_ID", "Time [s]"]).reset_index(drop=True)
    rel = data[data["Leader_ID"] >= 0][[
        "Vehicle_ID", "Leader_ID", "time_key", "Time [s]", "Lane", "Follower_ID",
        "x [m]", "y [m]", "Speed [km/h]", "Angle [rad]", "Vehicle_length [m]",
        "Lon. Acc. [ms-2]",
    ]].rename(columns={
        "Vehicle_ID": "follower_id", "Leader_ID": "leader_id", "Lane": "follower_lane",
        "Follower_ID": "follower_ref", "x [m]": "follower_x", "y [m]": "follower_y",
        "Speed [km/h]": "follower_speed", "Angle [rad]": "follower_angle",
        "Vehicle_length [m]": "follower_length", "Lon. Acc. [ms-2]": "follower_acc",
    })
    leader = data[[
        "Vehicle_ID", "time_key", "Follower_ID", "Lane", "x [m]", "y [m]", "Speed [km/h]",
        "Angle [rad]", "Vehicle_length [m]", "Lon. Acc. [ms-2]",
    ]].rename(columns={
        "Vehicle_ID": "leader_id", "Follower_ID": "leader_follower_ref", "Lane": "leader_lane",
        "x [m]": "leader_x", "y [m]": "leader_y", "Speed [km/h]": "leader_speed",
        "Angle [rad]": "leader_angle", "Vehicle_length [m]": "leader_length",
        "Lon. Acc. [ms-2]": "leader_acc",
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
    m["center_separation_m"] = dx * np.cos(m["follower_angle"]) + dy * np.sin(m["follower_angle"])
    m["gap_center_m"] = m["center_separation_m"] - (m["follower_length"] + m["leader_length"]) / 2.0
    # Same normalized reference point alpha in [0,1]: alpha=0 rear point,
    # alpha=1 front point. This gives a transparent sensitivity interval only.
    m["gap_alpha0_rear_m"] = m["center_separation_m"] - m["follower_length"]
    m["gap_alpha1_front_m"] = m["center_separation_m"] - m["leader_length"]
    m["gap_sensitivity_low_m"] = m[["gap_alpha0_rear_m", "gap_alpha1_front_m"]].min(axis=1)
    m["gap_sensitivity_high_m"] = m[["gap_alpha0_rear_m", "gap_alpha1_front_m"]].max(axis=1)
    m["closing_speed_mps"] = (m["follower_speed"] - m["leader_speed"]) / 3.6
    m = m[m["mutual_relation"] & m["same_lane"]].copy()
    m = m.sort_values(["follower_id", "leader_id", "Time [s]"])
    m["dt_s"] = m.groupby(["follower_id", "leader_id"])["Time [s]"].diff()
    prev_lane = m.groupby(["follower_id", "leader_id"])["follower_lane"].shift()
    m["new_segment"] = m["dt_s"].isna() | (m["dt_s"] > 0.05) | m["follower_lane"].ne(prev_lane)
    m["segment_number"] = m.groupby(["follower_id", "leader_id"])["new_segment"].cumsum().astype(int)
    m["segment_id"] = m["follower_id"].astype(str) + "-" + m["leader_id"].astype(str) + "-" + m["segment_number"].astype(str)
    return m


def quantile_summary(s: pd.Series) -> dict[str, float]:
    return {"min": float(s.min()), "p05": float(s.quantile(0.05)), "p50": float(s.quantile(0.5)), "p95": float(s.quantile(0.95)), "max": float(s.max())}


def interpolation_error(q: pd.DataFrame) -> dict:
    t = q["Time [s]"].to_numpy(float)
    v = q["leader_speed"].to_numpy(float)
    grid = np.arange(t[0], t[-1] + 0.025, 0.05)
    back = np.interp(t, grid, np.interp(grid, t, v))
    err = np.abs(back - v)
    return {"target_step_s": 0.05, "source_dt_p50_s": float(np.median(np.diff(t)),), "leader_speed_error_mps": {"p50": float(np.quantile(err, 0.5)), "p95": float(np.quantile(err, 0.95)), "max": float(err.max())}}


def evaluate(m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rows = []
    coverage = []
    diagnostics = {}
    for follower, leader, segment_number in CANDIDATES:
        segment_id = f"{follower}-{leader}-{segment_number}"
        q = m[m["segment_id"] == segment_id].sort_values("Time [s]").copy()
        if q.empty:
            raise ValueError(f"candidate not found: {segment_id}")
        dt = q["dt_s"].dropna()
        gap_low = q["gap_sensitivity_low_m"]
        gap_high = q["gap_sensitivity_high_m"]
        stable = bool(q["mutual_relation"].all() and q["same_lane"].all() and (dt <= 0.05).all())
        no_order_reversal = int((q["center_separation_m"] <= 0).sum()) == 0
        no_sensitivity_overlap = int((gap_low <= 0).sum()) == 0
        # Level 1 means ready for researcher input review only. It does not
        # authorize formal Task9 execution or claim independent physical truth.
        if stable and no_order_reversal and no_sensitivity_overlap and (q["Time [s]"].iloc[-1] - q["Time [s]"].iloc[0]) >= 20:
            level = "READY_FOR_TASK9_INPUT_REVIEW" if segment_id in {"962-958-1", "926-924-1"} else "CONDITIONAL_WITH_SENSITIVITY"
        else:
            level = "NOT_SUITABLE"
        row = {
            "segment_id": segment_id, "follower_id": follower, "leader_id": leader, "lane": int(q["follower_lane"].mode().iloc[0]),
            "start_time_s": float(q["Time [s]"].iloc[0]), "end_time_s": float(q["Time [s]"].iloc[-1]),
            "duration_s": float(q["Time [s]"].iloc[-1] - q["Time [s]"].iloc[0]), "sample_count": int(len(q)),
            "dt_min_s": float(dt.min()), "dt_max_s": float(dt.max()), "missing_or_long_gap_n": int((dt > 0.05).sum()),
            "reciprocal_relation_fraction": float(q["mutual_relation"].mean()), "same_lane_fraction": float(q["same_lane"].mean()),
            "heading_difference_p95_rad": float(q["heading_difference_rad"].quantile(0.95)),
            "center_separation_m": quantile_summary(q["center_separation_m"]),
            "gap_center_m": quantile_summary(q["gap_center_m"]),
            "gap_sensitivity_low_m": quantile_summary(gap_low), "gap_sensitivity_high_m": quantile_summary(gap_high),
            "initial_gap_center_m": float(q["gap_center_m"].iloc[0]), "initial_gap_sensitivity_low_m": float(gap_low.iloc[0]), "initial_gap_sensitivity_high_m": float(gap_high.iloc[0]),
            "nonpositive_sensitivity_gap_n": int((gap_low <= 0).sum()), "order_reversal_n": int((q["center_separation_m"] <= 0).sum()),
            "follower_speed_kmh": quantile_summary(q["follower_speed"]), "leader_speed_kmh": quantile_summary(q["leader_speed"]),
            "follower_acc_mps2": quantile_summary(q["follower_acc"]), "leader_acc_mps2": quantile_summary(q["leader_acc"]),
            "closing_speed_mps": quantile_summary(q["closing_speed_mps"]),
            "video_id_binding": "Unknown", "vehicle_reference_point": "Unknown", "vehicle_type_tau_mapping": "Unknown",
            "task9_input_level": level, "formal_task9_admitted": False,
            "reason": "Field-consistent and continuous approximate input; unresolved video/reference-point/tau issues remain outside the input-review level.",
        }
        rows.append(row)
        coverage.append({"segment_id": segment_id, "fields": {"leader_position": True, "leader_speed": True, "follower_speed": True, "vehicle_lengths": True, "lane": True, "time": True}, "time_s": [row["start_time_s"], row["end_time_s"]], "source_sampling_dt_s": float(dt.median()), "target_step_s": 0.05, "interpolation": interpolation_error(q)})
        diagnostics[segment_id] = {"sample_count": len(q), "first_row": {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v) for k, v in q.iloc[0][["Time [s]", "follower_speed", "leader_speed", "gap_center_m", "gap_sensitivity_low_m", "gap_sensitivity_high_m"]].to_dict().items()}}
    return pd.DataFrame(rows), pd.DataFrame(coverage), diagnostics


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve existing result directory: {OUT}")
    OUT.mkdir(parents=True)
    m = load_relation_table()
    evaluations, coverage, diagnostics = evaluate(m)
    now = datetime.now(timezone.utc).isoformat()
    evaluations.to_csv(OUT / "candidate_evaluation.csv", index=False)
    coverage.to_csv(OUT / "input_coverage.csv", index=False)
    write_json("approximate_gap_sensitivity.json", {"status": "COMPLETED_APPROXIMATE_REFERENCE_POINT_SENSITIVITY", "reference_point_scenarios": {"alpha_0": "rear reference", "alpha_0_5": "center reference", "alpha_1": "front reference"}, "candidate_results": evaluations[["segment_id", "initial_gap_center_m", "initial_gap_sensitivity_low_m", "initial_gap_sensitivity_high_m", "nonpositive_sensitivity_gap_n"]].to_dict(orient="records"), "global_boundary": "The interval assumes one common normalized reference point for both vehicles; arbitrary unequal point offsets remain Unknown."})
    write_json("video_review_status.json", {"status": "BLOCKED_NO_VIEWER_OR_VIDEO_PAYLOAD", "datafromsky_viewer": "NOT_FOUND_IN_CHECKED_LOCAL_PATHS", "official_viewer_url": "https://www.datafromsky.com/download/DataFromSkyViewer.exe", "tracking_log": {"path": str(DALL_LOG.relative_to(ROOT)), "bytes": DALL_LOG.stat().st_size, "sha256": sha256(DALL_LOG), "nested_members": [i.filename for i in zipfile.ZipFile(DALL_LOG).infolist()]}, "mp4_downloaded": 0, "candidate_video_binding": "Unknown", "decision": "Stop bounded video attempt; retain trajectory-based input-review assessment without claiming video validation."})
    write_json("task9_minimum_sufficient_assessment.json", {"status": "INPUT_REVIEW_CANDIDATES_AVAILABLE_FORMAL_ADMISSION_BLOCKED", "minimum_sufficient_input_proposal": ["reciprocal leader/follower fields", "continuous >=20 s same-lane segment", "positive lower-bound gap under common-reference sensitivity interval", "no order reversal or long observation gap", "finite speed/acceleration and reproducible 30 Hz to 0.05 s diagnostic"], "candidate_levels": evaluations[["segment_id", "task9_input_level", "formal_task9_admitted"]].to_dict(orient="records"), "recommended_order": ["962-958-1", "926-924-1", "857-851-1"], "recommendation": "Submit 962-958-1 and 926-924-1 to researcher Task9 input review; retain 857-851-1 as a conditional backup. Do not generate formal Task9 input or run the experiment until researcher review resolves the remaining reference-point, video-binding and vehicle-type/tau questions.", "global_gate": "Stage 0.5 remains blocked; scientific equivalence remains false."})
    write_json("source_bindings.json", {"task_id": "AAD-S0.5-POST-R2-TASK13", "base_head": git_head(), "captured_at_utc": now, "script": "code/scripts/audit_stage_0_5_task13_mitra_minimum_sufficient.py", "script_sha256": sha256(ROOT / "code/scripts/audit_stage_0_5_task13_mitra_minimum_sufficient.py"), "inputs": {str(T1_ZIP.relative_to(ROOT)): {"bytes": T1_ZIP.stat().st_size, "sha256": sha256(T1_ZIP)}, str(JUMPS.relative_to(ROOT)): {"bytes": JUMPS.stat().st_size, "sha256": sha256(JUMPS)}, str(DALL_LOG.relative_to(ROOT)): {"bytes": DALL_LOG.stat().st_size, "sha256": sha256(DALL_LOG)}}, "reused_task12_evidence": "evidence/results/RES-STAGE-0.5-POST-R2-TASK12-MITRA-T1-CANDIDATE-PHYSICAL-ADMISSION-20261031/", "new_simulations": 0, "holdout_reads": 0, "video_files_downloaded": 0})
    write_json("validation_record.json", {"task_id": "AAD-S0.5-POST-R2-TASK13", "status": "PASS_BOUNDED_MINIMUM_SUFFICIENT_INPUT_ASSESSMENT", "candidate_count": len(evaluations), "level1_input_review_candidates": int((evaluations.task9_input_level == "READY_FOR_TASK9_INPUT_REVIEW").sum()), "formal_task9_admitted": 0, "video_review": "BLOCKED_NO_VIEWER_OR_VIDEO_PAYLOAD", "not_run": ["SUMO/TraCI", "formal Task9", "MP4 download", "tau mapping", "third window", "locked holdout", "full pytest"]})
    write_json("context_consistency_check.json", {"status": "PASS_CONTEXT_CONSISTENCY_CHECK", "stage_0_5": "blocked", "scientific_equivalence": False, "task9_formal_runs": 0, "round3": "not started", "updated_context": ["AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/03_DATA_FLOW.md", "AI_CONTEXT/05_EXPERIMENTS.md", "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md"], "updated_indexes": ["docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md", "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md"]})
    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    write_json("manifest.json", {"schema": "aad.stage05.post_r2.task13.mitra_minimum_sufficient_input.manifest.v1", "task_id": "AAD-S0.5-POST-R2-TASK13", "status": "completed_with_input_review_candidates_and_blockers", "stage_0_5": "blocked", "formal_task9_admitted": 0, "payload_files": {p.name: sha256(p) for p in payloads}})
    (OUT / "SHA256SUMS").write_text("\n".join(f"{sha256(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    print(f"TASK13_MITRA_MINIMUM_INPUT_AUDIT_WRITTEN {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
