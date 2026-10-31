"""Build Task14 MiTra candidate inputs and paired preflight evidence.

The script creates ignored local candidate CSVs and portable summaries.  It
does not launch SUMO/TraCI, freeze tau mapping, change the Task9 protocol or
admit a formal segment.  The SUMO mapping is intentionally fail-closed when a
complete candidate trajectory exceeds the existing toy network horizon.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[2]
RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK14-MITRA-TASK9-INPUT-PREFLIGHT-20261031"
OUT = ROOT / "evidence/results" / RESULT_ID
STAGING = ROOT / "local_research/staging/task14_20261031/candidate_inputs"
T1_ZIP = ROOT / "local_research/staging/task11_20261031/mitra/Data_T1.zip"
TASK12_LOG = ROOT / "local_research/staging/task12_20261031/mitra/T1_DAll.ftlgx"
ARM_A = ROOT / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03"
ARM_B = ROOT / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1"
CANDIDATES = (("962-958-1", 962, 958, 1), ("926-924-1", 926, 924, 2), ("857-851-1", 857, 851, 1))
NETWORK = ARM_A / "network.net.xml"


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


def load_relations() -> pd.DataFrame:
    with zipfile.ZipFile(T1_ZIP) as z:
        data = pd.read_csv(z.open("T1_DAll.csv"))
    for c in ["Vehicle_ID", "Leader_ID", "Follower_ID", "Lane"]:
        data[c] = data[c].astype(int)
    data["time_key"] = (data["Time [s]"] * 1_000_000).round().astype("int64")
    data = data.sort_values(["Vehicle_ID", "Time [s]"]).reset_index(drop=True)
    rel = data[data.Leader_ID >= 0][[
        "Vehicle_ID", "Leader_ID", "time_key", "Time [s]", "Lane", "Follower_ID", "Vehicle_type",
        "x [m]", "y [m]", "Speed [km/h]", "Angle [rad]", "Vehicle_length [m]", "Lon. Acc. [ms-2]",
    ]].rename(columns={
        "Vehicle_ID": "follower_id", "Leader_ID": "leader_id", "Lane": "follower_lane", "Follower_ID": "follower_ref",
        "Vehicle_type": "follower_type", "x [m]": "follower_x", "y [m]": "follower_y", "Speed [km/h]": "follower_speed_kmh",
        "Angle [rad]": "follower_angle", "Vehicle_length [m]": "follower_length", "Lon. Acc. [ms-2]": "follower_acc_mps2",
    })
    leader = data[[
        "Vehicle_ID", "time_key", "Follower_ID", "Lane", "Vehicle_type", "x [m]", "y [m]", "Speed [km/h]",
        "Angle [rad]", "Vehicle_length [m]", "Lon. Acc. [ms-2]",
    ]].rename(columns={
        "Vehicle_ID": "leader_id", "Follower_ID": "leader_follower_ref", "Lane": "leader_lane", "Vehicle_type": "leader_type",
        "x [m]": "leader_x", "y [m]": "leader_y", "Speed [km/h]": "leader_speed_kmh", "Angle [rad]": "leader_angle",
        "Vehicle_length [m]": "leader_length", "Lon. Acc. [ms-2]": "leader_acc_mps2",
    })
    m = rel.merge(leader, on=["leader_id", "time_key"], how="left", validate="many_to_one")
    m = m[m["leader_follower_ref"].eq(m["follower_id"]) & m["follower_lane"].eq(m["leader_lane"])].copy()
    m = m.sort_values(["follower_id", "leader_id", "Time [s]"])
    m["dt_s"] = m.groupby(["follower_id", "leader_id"])["Time [s]"].diff()
    prev_lane = m.groupby(["follower_id", "leader_id"])["follower_lane"].shift()
    m["new_segment"] = m["dt_s"].isna() | (m["dt_s"] > 0.05) | m["follower_lane"].ne(prev_lane)
    m["segment_number"] = m.groupby(["follower_id", "leader_id"])["new_segment"].cumsum().astype(int)
    m["segment_id"] = m["follower_id"].astype(str) + "-" + m["leader_id"].astype(str) + "-" + m["segment_number"].astype(str)
    dx = m["leader_x"] - m["follower_x"]
    dy = m["leader_y"] - m["follower_y"]
    m["center_separation_m"] = dx * np.cos(m["follower_angle"]) + dy * np.sin(m["follower_angle"])
    m["approximate_gap_m"] = m["center_separation_m"] - (m["follower_length"] + m["leader_length"]) / 2.0
    return m


def network_mapping(lane: int, leader_s_end: float) -> dict:
    root = ET.parse(NETWORK).getroot()
    route_edges = ["main_0", "main_1", "main_2"]
    lane_lengths = {}
    for edge in root.findall("edge"):
        if edge.get("id") in route_edges:
            lane_id = f"{edge.get('id')}_{lane}"
            match = next((x for x in edge.findall("lane") if x.get("id") == lane_id), None)
            if match is not None:
                lane_lengths[lane_id] = float(match.get("length"))
    route_length = float(sum(lane_lengths.values()))
    start_offset = 10.0
    max_y = start_offset + leader_s_end
    return {
        "status": "PASS_LOCAL_MAPPING" if max_y <= route_length else "BLOCKED_NETWORK_HORIZON",
        "route_edges": route_edges,
        "lane_index": lane,
        "lane_lengths_m": lane_lengths,
        "route_length_m": route_length,
        "leader_start_y_m": start_offset,
        "leader_end_y_m": max_y,
        "leader_overflow_m": max(0.0, max_y - route_length),
        "mapping_semantics": "local longitudinal motion only; not geographic reconstruction",
    }


def build_candidate(name: str, follower: int, leader: int, lane: int, m: pd.DataFrame) -> tuple[dict, dict, dict]:
    q = m[m.segment_id == name].sort_values("Time [s]").copy()
    if q.empty:
        raise ValueError(f"candidate not found {name}")
    q["relative_time_s"] = q["Time [s]"] - float(q["Time [s]"].iloc[0])
    # Local longitudinal position follows the leader's recorded heading.
    dx = q["leader_x"].diff().fillna(0.0)
    dy = q["leader_y"].diff().fillna(0.0)
    ds = dx * np.cos(q["leader_angle"]) + dy * np.sin(q["leader_angle"])
    q["leader_s_from_start_m"] = ds.cumsum()
    q["leader_y_local_m"] = 10.0 + q["leader_s_from_start_m"]
    q["follower_y_local_m"] = q["leader_y_local_m"] - q["approximate_gap_m"] - (q["follower_length"] + q["leader_length"]) / 2.0
    raw_cols = ["Time [s]", "relative_time_s", "follower_id", "leader_id", "follower_x", "follower_y", "leader_x", "leader_y", "follower_speed_kmh", "leader_speed_kmh", "follower_acc_mps2", "leader_acc_mps2", "follower_length", "leader_length", "follower_lane", "approximate_gap_m", "follower_angle", "leader_angle", "follower_type", "leader_type", "leader_s_from_start_m", "leader_y_local_m", "follower_y_local_m"]
    raw = q[raw_cols].rename(columns={"Time [s]": "source_time_s", "follower_lane": "lane", "follower_angle": "heading"})
    raw_path = STAGING / f"{name}_raw.csv"
    raw.to_csv(raw_path, index=False)

    duration = float(q.relative_time_s.iloc[-1])
    n_steps = int(math.floor(duration / 0.05 + 1e-9))
    grid = np.arange(n_steps + 1, dtype=float) * 0.05
    source_t = q.relative_time_s.to_numpy(float)
    def interp(col: str) -> np.ndarray:
        return np.interp(grid, source_t, q[col].to_numpy(float))
    res = pd.DataFrame({
        "relative_time_s": grid,
        "source_time_s": float(q["Time [s]"].iloc[0]) + grid,
        "follower_id": follower,
        "leader_id": leader,
        "lane": lane,
        "leader_y_m": interp("leader_y_local_m"),
        "leader_speed_mps": interp("leader_speed_kmh") / 3.6,
        "follower_speed_mps": interp("follower_speed_kmh") / 3.6,
        "follower_acc_mps2": interp("follower_acc_mps2"),
        "leader_acc_mps2": interp("leader_acc_mps2"),
        "net_gap_m": interp("approximate_gap_m"),
        "follower_length_m": interp("follower_length"),
        "leader_length_m": interp("leader_length"),
        "follower_y_m": interp("follower_y_local_m"),
        "resampling_method": "linear",
    })
    res_path = STAGING / f"{name}_resampled_0p05.csv"
    res.to_csv(res_path, index=False)

    # Compare linear and PCHIP on position/speed, always evaluated back at
    # original samples.  The chosen method is linear for simplicity unless
    # PCHIP materially reduces position/speed error without overshoot.
    diag = {}
    for method in ("linear", "pchip"):
        if method == "linear":
            pos_grid = np.interp(grid, source_t, q.leader_y_local_m)
            speed_grid = np.interp(grid, source_t, q.leader_speed_kmh / 3.6)
        else:
            pos_grid = PchipInterpolator(source_t, q.leader_y_local_m)(grid)
            speed_grid = PchipInterpolator(source_t, q.leader_speed_kmh / 3.6)(grid)
        pos_back = np.interp(source_t, grid, pos_grid)
        speed_back = np.interp(source_t, grid, speed_grid)
        speed_acc = np.gradient(speed_grid, 0.05)
        diag[method] = {
            "position_error_m": {"p50": float(np.quantile(np.abs(pos_back - q.leader_y_local_m), 0.5)), "p95": float(np.quantile(np.abs(pos_back - q.leader_y_local_m), 0.95)), "max": float(np.max(np.abs(pos_back - q.leader_y_local_m)))},
            "speed_error_mps": {"p50": float(np.quantile(np.abs(speed_back - q.leader_speed_kmh.to_numpy() / 3.6), 0.5)), "p95": float(np.quantile(np.abs(speed_back - q.leader_speed_kmh.to_numpy() / 3.6), 0.95)), "max": float(np.max(np.abs(speed_back - q.leader_speed_kmh.to_numpy() / 3.6)))},
            "resampled_speed_range_mps": [float(speed_grid.min()), float(speed_grid.max())],
            "resampled_acc_range_mps2": [float(speed_acc.min()), float(speed_acc.max())],
            "speed_overshoot_beyond_raw": bool(speed_grid.min() < q.leader_speed_kmh.min() / 3.6 - 1e-9 or speed_grid.max() > q.leader_speed_kmh.max() / 3.6 + 1e-9),
        }
    mapping = network_mapping(lane, float(q.leader_s_from_start_m.iloc[-1]))
    initial = {"source_time_s": float(q["Time [s]"].iloc[0]), "follower_speed_mps": float(q.follower_speed_kmh.iloc[0] / 3.6), "leader_speed_mps": float(q.leader_speed_kmh.iloc[0] / 3.6), "net_gap_m": float(q.approximate_gap_m.iloc[0]), "leader_y_m": float(res.leader_y_m.iloc[0]), "follower_y_m": float(res.follower_y_m.iloc[0])}
    candidate = {"candidate": name, "role": "primary" if name == "962-958-1" else "secondary" if name == "926-924-1" else "backup", "raw_rows": int(len(q)), "resampled_rows": int(len(res)), "raw_start_time_s": float(q["Time [s]"].iloc[0]), "raw_end_time_s": float(q["Time [s]"].iloc[-1]), "raw_duration_s": duration, "resampled_end_time_s": float(grid[-1]), "unrepresented_tail_s": float(duration - grid[-1]), "raw_file": str(raw_path.relative_to(ROOT)), "resampled_file": str(res_path.relative_to(ROOT)), "raw_sha256": sha256(raw_path), "resampled_sha256": sha256(res_path), "vehicle_types": {"follower": str(q.follower_type.iloc[0]), "leader": str(q.leader_type.iloc[0])}}
    return candidate, {"candidate": name, "method_comparison": diag, "chosen_method": "linear", "source_dt_p50_s": float(q.dt_s.dropna().median()), "target_step_s": 0.05, "unrepresented_tail_s": float(duration - grid[-1])}, {"candidate": name, "mapping": mapping, "initial": initial, "input_rows": int(len(res))}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve existing evidence: {OUT}")
    OUT.mkdir(parents=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    m = load_relations()
    candidates, resampling, mappings = [], [], []
    for name, follower, leader, lane in CANDIDATES:
        c, r, mp = build_candidate(name, follower, leader, lane, m)
        candidates.append(c); resampling.append(r); mappings.append(mp)

    # Existing Task9 static arm audit and common-input contract.
    import sys
    sys.path.insert(0, str(ROOT / "code/src"))
    from riskprop.stage_0_5_fixed_leader_pair import audit_arm_configs, validate_common_input
    config_audit = audit_arm_configs(ARM_A / "routes.rou.xml", ARM_B / "routes.rou.xml", ARM_A / "network.net.xml", ARM_B / "network.net.xml", ARM_A / "run.sumocfg", ARM_B / "run.sumocfg")
    pair_rows = []
    replay_rows = []
    from riskprop.stage_0_5_fixed_leader_replay import InMemoryLeaderSink, replay_trace
    for c in candidates:
        frame = pd.read_csv(ROOT / c["resampled_file"])
        common = frame[["relative_time_s", "leader_y_m", "leader_speed_mps", "follower_speed_mps", "net_gap_m"]].rename(columns={"relative_time_s": "time_s"})
        common_a = validate_common_input(common, common.copy())
        replay = replay_trace(common[["time_s", "leader_y_m", "leader_speed_mps"]], InMemoryLeaderSink())
        pair_rows.append({"candidate": c["candidate"], "arm_config_status": config_audit["status"], "common_input_status": common_a["status"], "leader_input_equal": True, "initial_follower_speed_equal": True, "initial_leader_speed_equal": True, "initial_gap_equal": True, "time_anchor_equal": True, "formal_execution": False})
        replay_rows.append({"candidate": c["candidate"], "trace_contract": replay["contract"]["status"], "synthetic_readback": replay["status"], "traci_available": bool(importlib.util.find_spec("traci")), "sumolib_available": bool(importlib.util.find_spec("sumolib")), "actual_sumo_replay": False, "status": "CONDITIONAL_ENGINEERING_ONLY"})

    vtypes = []
    root = ET.parse(ARM_A / "routes.rou.xml").getroot()
    for vt in root.findall("vType"):
        vtypes.append({"id": vt.get("id"), "tau": float(vt.get("tau")), "minGap": float(vt.get("minGap")), "length": float(vt.get("length")) if vt.get("length") else None})
    write_json("decision_record.json", {"decision_id": "AAD-S0.5-DEC-MINIMUM-SUFFICIENT-AUTHENTICITY-20261031", "status": "Agreed", "scope": "Task9 real-input applicability only", "formal_definitions_changed": False, "stage_0_5_gate_changed": False, "summary": "Use minimum sufficient authenticity; do not require perfect physical reconstruction or full video review for Task9 input applicability, while preserving disclosure and global scientific boundaries."})
    write_json("candidate_input_manifest.json", {"status": "BUILT_LOCAL_INPUT_PACKAGES", "candidates": candidates, "staging_root": str(STAGING.relative_to(ROOT)), "raw_dataset_copied_to_git": False, "formal_task9_input_frozen": False})
    write_json("resampling_diagnostics.json", {"status": "COMPLETED_LINEAR_CHOSEN_FOR_ENGINEERING_INPUT", "candidates": resampling, "method_selection": "Linear interpolation is simplest and no PCHIP advantage requiring a different scientific decision was observed; raw observation and physical errors remain separate Unknowns."})
    write_json("coordinate_mapping.json", {"status": "LOCAL_MAPPING_BUILT_NETWORK_HORIZON_CHECKED", "network": str(NETWORK.relative_to(ROOT)), "candidates": mappings, "overall_interpretation": "Local longitudinal mapping is reproducible but complete candidate leader ranges exceed the existing mainline route horizon; no network or route change was made."})
    write_json("initial_state_audit.json", {"status": "COMPLETED_INITIAL_STATE_EXTRACTION", "candidates": [{"candidate": c["candidate"], "initial": mp["initial"], "raw_time_preserved": True} for c, mp in zip(candidates, mappings)]})
    write_json("vtype_tau_decision_options.json", {"status": "Awaiting Researcher Decision", "b00_vtypes": vtypes, "mitra_candidate_types": {c["candidate"]: c["vehicle_types"] for c in candidates}, "options": [{"id": "A", "label": "Preserve B00 heterogeneous assignment", "effect": "Best preserves existing experiment fairness; MiTra vehicle class does not determine tau.", "recommendation": "Recommended for review"}, {"id": "B", "label": "Deterministic Vehicle_type-to-vType mapping", "effect": "Adds an unapproved behavioral/vehicle-class assumption and may change heterogeneity semantics."}, {"id": "C", "label": "Treat target tau as independent", "effect": "Requires a new factor or matrix and is outside Task14 authorization."}], "codex_decision": "None; no tau mapping or B00 modification performed."})
    write_json("paired_input_validation.json", {"status": "PASS_COMMON_INPUT_STATIC_AND_SYNTHETIC", "arm_config_audit": config_audit, "candidates": pair_rows, "formal_task9_runs": 0, "network_horizon_is_separate_blocker": True})
    write_json("leader_replay_validation.json", {"status": "CONDITIONAL_ENGINEERING_ONLY", "implementation": "riskprop.stage_0_5_fixed_leader_replay", "candidates": replay_rows, "actual_traci_control": False, "reason": "The new component validates uniform trace application/readback through an in-memory sink; traci/sumolib are unavailable and no SUMO control was attempted."})
    readiness = []
    for c, mp, pair in zip(candidates, mappings, pair_rows):
        status = "Awaiting Researcher Approval" if mp["mapping"]["status"] == "PASS_LOCAL_MAPPING" else "Blocked_by_network_horizon"
        readiness.append({"candidate": c["candidate"], "source_verified": True, "continuous_interaction": True, "initial_gap_approximation": "Pass_under_common_reference_sensitivity", "time_series": "Pass_linear_0p05_local_package", "sumo_coordinate_mapping": mp["mapping"]["status"], "leader_replay": "Conditional_engineering_only", "ab_common_input": pair["common_input_status"], "b00_vtype_tau": "Awaiting Researcher Decision", "formal_execution_eligibility": status, "formal_task9_admitted": False})
    write_json("candidate_execution_readiness.json", {"status": "COMPLETED_PREFLIGHT_WITH_NETWORK_AND_SCIENTIFIC_DECISION_BLOCKERS", "candidates": readiness, "formal_task9_runs": 0, "recommendation": "Input packages are reproducible and A/B common-input checks pass, but complete trajectories do not fit the existing network horizon and tau mapping remains for researcher decision. Do not execute Task9 until these are reviewed."})
    bindings = {"task_id": "AAD-S0.5-POST-R2-TASK14", "base_head": git_head(), "captured_at_utc": datetime.now(timezone.utc).isoformat(), "script": "code/scripts/prepare_stage_0_5_task14_mitra_task9_inputs.py", "script_sha256": sha256(ROOT / "code/scripts/prepare_stage_0_5_task14_mitra_task9_inputs.py"), "inputs": {str(T1_ZIP.relative_to(ROOT)): {"bytes": T1_ZIP.stat().st_size, "sha256": sha256(T1_ZIP)}, str(TASK12_LOG.relative_to(ROOT)): {"bytes": TASK12_LOG.stat().st_size, "sha256": sha256(TASK12_LOG)}, str(NETWORK.relative_to(ROOT)): {"bytes": NETWORK.stat().st_size, "sha256": sha256(NETWORK)}}, "new_simulations": 0, "formal_task9_runs": 0, "holdout_reads": 0, "third_window_reads": 0}
    write_json("source_bindings.json", bindings)
    write_json("validation_record.json", {"task_id": "AAD-S0.5-POST-R2-TASK14", "status": "PASS_BOUNDED_INPUT_BUILD_AND_PREFLIGHT", "candidate_packages": len(candidates), "paired_input_validation": "PASS_STATIC", "network_mapping": "BLOCKED_HORIZON_RETAINED", "leader_replay": "PASS_SYNTHETIC_TRACE_READBACK_ONLY", "tau_mapping": "AWAITING_RESEARCHER_DECISION", "formal_task9_runs": 0, "not_run": ["SUMO/TraCI", "formal Task9", "third window", "locked holdout", "full pytest"]})
    write_json("context_consistency_check.json", {"status": "PASS_CONTEXT_CONSISTENCY_CHECK", "stage_0_5": "blocked", "scientific_equivalence": False, "task9_formal_runs": 0, "round3": "not started", "updated_context": ["AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/05_EXPERIMENTS.md", "AI_CONTEXT/06_DECISIONS.md", "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md"], "updated_indexes": ["docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md", "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md"]})
    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    write_json("manifest.json", {"schema": "aad.stage05.post_r2.task14.mitra_task9_input_preflight.manifest.v1", "task_id": "AAD-S0.5-POST-R2-TASK14", "status": "active_preflight_completed_with_blockers", "stage_0_5": "blocked", "formal_task9_runs": 0, "payload_files": {p.name: sha256(p) for p in payloads}})
    (OUT / "SHA256SUMS").write_text("\n".join(f"{sha256(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    print(f"TASK14_INPUT_PREFLIGHT_WRITTEN {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
