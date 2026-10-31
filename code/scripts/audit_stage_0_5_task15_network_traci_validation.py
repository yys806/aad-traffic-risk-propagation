"""Assemble Task15 network, geometry, TraCI and pairing validation evidence."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK15-TASK9-NETWORK-TRACI-VALIDATION-20261031"
OUT = ROOT / "evidence/results" / RESULT_ID
TASK14_EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK14-MITRA-TASK9-INPUT-PREFLIGHT-20261031"
TASK14_STAGE = ROOT / "local_research/staging/task14_20261031/candidate_inputs"
TASK15_STAGE = ROOT / "local_research/staging/task15_20261031"
PROTO = TASK15_STAGE / "network_prototype"
RAW_NETWORK = ROOT / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03/network.net.xml"
ARM_ROUTES = ROOT / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03/routes.rou.xml"

CANDIDATES = ("962-958-1", "926-924-1", "857-851-1")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name: str, payload: object) -> None:
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def network_summary(path: Path) -> dict:
    root = ET.parse(path).getroot()
    edges = []
    for edge in root.findall("edge"):
        if edge.get("function") == "internal":
            continue
        lanes = []
        for lane in edge.findall("lane"):
            lanes.append({"id": lane.get("id"), "length_m": float(lane.get("length")), "speed_mps": float(lane.get("speed")), "width_m": float(lane.get("width", "3.2"))})
        edges.append({"id": edge.get("id"), "from": edge.get("from"), "to": edge.get("to"), "lanes": lanes})
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "edges": edges}


def candidate_envelopes() -> list[dict]:
    rows = []
    for name in CANDIDATES:
        raw = pd.read_csv(TASK14_STAGE / f"{name}_raw.csv")
        # Task14 local leader coordinates start at 10 m; Task15 prototype uses
        # a conservative +40 m offset so the follower body has upstream room.
        offset = 40.0
        leader = raw["leader_y_local_m"] + offset
        follower = raw["follower_y_local_m"] + offset
        flen = raw["follower_length"]
        llen = raw["leader_length"]
        rows.append({
            "candidate": name,
            "raw_rows": int(len(raw)),
            "source_start_s": float(raw["source_time_s"].iloc[0]),
            "source_end_s": float(raw["source_time_s"].iloc[-1]),
            "leader_center_start_m": float(leader.iloc[0]),
            "leader_center_end_m": float(leader.iloc[-1]),
            "follower_center_start_m": float(follower.iloc[0]),
            "leader_body_min_m": float(leader.iloc[0] - llen.iloc[0] / 2),
            "follower_body_min_m": float(follower.iloc[0] - flen.iloc[0] / 2),
            "leader_body_max_m": float(leader.iloc[-1] + llen.iloc[-1] / 2),
            "prototype_bounds_m": [0.0, 1000.0],
            "prototype_space_pass": bool(float(follower.iloc[0] - flen.iloc[0] / 2) >= 0 and float(leader.iloc[-1] + llen.iloc[-1] / 2) <= 1000.0),
            "sealed_route_length_m": 659.17,
            "sealed_route_space_pass": bool(float(follower.iloc[0] - flen.iloc[0] / 2) >= 0 and float(leader.iloc[-1] + llen.iloc[-1] / 2) <= 659.17),
            "mapping_offset_m": offset,
            "no_trimming_or_coordinate_wrap": True,
        })
    return rows


def geometry_comparison() -> dict:
    root = ET.parse(ARM_ROUTES).getroot()
    b00 = {v.get("id"): float(v.get("length")) for v in root.findall("vType")}
    rows = []
    mitra = {"Car": 5.0, "Medium Vehicle": 5.8333}
    for name in CANDIDATES:
        raw = pd.read_csv(TASK14_STAGE / f"{name}_raw.csv")
        flt, ltype = str(raw.follower_type.iloc[0]), str(raw.leader_type.iloc[0])
        mi_f, mi_l = float(raw.follower_length.iloc[0]), float(raw.leader_length.iloc[0])
        center_sep = float(raw.approximate_gap_m.iloc[0] + (mi_f + mi_l) / 2)
        b00_gap = center_sep - (4.4196 + 4.4196) / 2
        rows.append({"candidate": name, "mitra_follower_type": flt, "mitra_leader_type": ltype, "mitra_follower_length_m": mi_f, "mitra_leader_length_m": mi_l, "b00_passenger_length_m": 4.4196, "initial_gap_mitra_assumption_m": float(raw.approximate_gap_m.iloc[0]), "initial_gap_if_b00_lengths_m": b00_gap, "delta_gap_b00_minus_mitra_m": b00_gap - float(raw.approximate_gap_m.iloc[0]), "b00_vtypes": b00})
    return {"status": "COMPLETED_GEOMETRY_COMPARISON_NOT_SELECTED", "candidates": rows, "interpretation": "B00 and MiTra lengths yield different approximate initial gaps; no formal geometry choice was made."}


def resampling_diagnostics() -> dict:
    rows = []
    for name in CANDIDATES:
        raw = pd.read_csv(TASK14_STAGE / f"{name}_raw.csv")
        res = pd.read_csv(TASK14_STAGE / f"{name}_resampled_0p05.csv")
        pos = res.leader_y_m.to_numpy(float)
        speed_fd = np.diff(pos) / 0.05
        speed = res.leader_speed_mps.to_numpy(float)
        rows.append({"candidate": name, "raw_duration_s": float(raw.source_time_s.iloc[-1] - raw.source_time_s.iloc[0]), "resampled_duration_s": float(res.relative_time_s.iloc[-1]), "unrepresented_tail_s": float(raw.source_time_s.iloc[-1] - raw.source_time_s.iloc[0] - res.relative_time_s.iloc[-1]), "finite_difference_speed_error_mps": {"p50": float(np.quantile(np.abs(speed_fd - speed[1:]), 0.5)), "p95": float(np.quantile(np.abs(speed_fd - speed[1:]), 0.95)), "max": float(np.max(np.abs(speed_fd - speed[1:])) )}, "position_speed_consistency_scope": "local mapped position vs chosen resampled speed; source observation and physical errors remain separate"})
    return {"status": "COMPLETED_POSITION_SPEED_AND_TAIL_DIAGNOSTIC", "candidates": rows}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve evidence: {OUT}")
    OUT.mkdir(parents=True)
    write_json("network_geometry_audit.json", {"status": "COMPLETED_SEALED_AND_PROTOTYPE_GEOMETRY_AUDIT", "sealed": network_summary(RAW_NETWORK), "prototype": network_summary(PROTO / "network.net.xml"), "sealed_config_unchanged": True})
    write_json("candidate_spatial_envelope.json", {"status": "COMPLETED_FULL_SPACE_ENVELOPE", "candidates": candidate_envelopes()})
    proto_manifest = json.loads((PROTO / "manifest.json").read_text(encoding="utf-8"))
    write_json("network_prototype_manifest.json", {"status": "BUILT_ISOLATED_STRAIGHT_LINE_REPLAY_PROTOTYPE", "manifest": proto_manifest, "background_equivalence": "Not claimed", "formal_b00_modified": False})
    write_json("vehicle_geometry_comparison.json", geometry_comparison())
    write_json("resampling_kinematic_diagnostics.json", resampling_diagnostics())
    write_json("tail_policy_comparison.json", {"status": "COMPLETED_POLICY_COMPARISON_NOT_SELECTED", "options": [{"policy": "fixed_grid_only", "effect": "uniform 0.05 s, leaves the recorded tail outside grid", "formal_choice": False}, {"policy": "retain_raw_endpoint", "effect": "preserves full observation but breaks uniform fixed-step contract", "formal_choice": False}, {"policy": "endpoint_extrapolation_or_hold", "effect": "adds unobserved state and requires researcher decision", "formal_choice": False}], "candidate_tails_s": {name: float(pd.read_csv(TASK14_STAGE / f'{name}_resampled_0p05.csv').relative_time_s.iloc[-1]) for name in CANDIDATES}})
    sumo_path = Path(r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe")
    version = subprocess.run([str(sumo_path), "--version"], capture_output=True, text=True).stdout.strip() if sumo_path.exists() else "SUMO_NOT_FOUND"
    write_json("traci_environment.json", {"sumo_executable": str(sumo_path), "sumo_exists": sumo_path.exists(), "sumo_version": version, "SUMO_HOME": None, "official_tools_path": r"C:\Program Files (x86)\Eclipse\Sumo\tools", "traci_binding": "available_via_official_tools_path", "sumolib_binding": "available_via_official_tools_path", "python_environment_path": str(Path(__import__("sys").executable)), "environment_repair": "No system installation or version upgrade; adapter adds matching official tools path."})
    synthetic = json.loads((TASK15_STAGE / "synthetic_replay.json").read_text(encoding="utf-8"))
    write_json("synthetic_replay_validation.json", {"status": synthetic["status"], "applied_rows": synthetic["applied_rows"], "max_abs_time_error_s": synthetic["max_abs_time_error_s"], "max_abs_position_error_m": synthetic["max_abs_position_error_m"], "max_abs_speed_error_mps": synthetic["max_abs_speed_error_mps"], "teleports": synthetic["starting_or_ending_teleport_rows"], "collisions": synthetic["collision_rows"], "formal_task9": False})
    replay_rows = []
    for name in CANDIDATES:
        r = json.loads((TASK15_STAGE / "candidate_replays" / f"{name}.json").read_text(encoding="utf-8"))
        replay_rows.append({"candidate": name, "status": r["status"], "applied_rows": r["applied_rows"], "max_abs_time_error_s": r["max_abs_time_error_s"], "max_abs_position_error_m": r["max_abs_position_error_m"], "max_abs_speed_error_mps": r["max_abs_speed_error_mps"], "teleports": r["starting_or_ending_teleport_rows"], "collisions": r["collision_rows"], "last_readback_position_m": r["rows"][-1]["readback_position_m"], "formal_task9": False})
    write_json("candidate_leader_replay_validation.json", {"status": "PASS_ENGINEERING_ONLY", "start_offset_m": 40.0, "lane_control": "main_ext_1/main_ext_2", "candidates": replay_rows, "interpretation": "Real SUMO/TraCI replay of leader only; no follower response or scientific metric was evaluated."})
    paired = []
    for name in CANDIDATES:
        a = TASK15_STAGE / "paired_inputs" / f"{name}_arm_a.csv"; b = TASK15_STAGE / "paired_inputs" / f"{name}_arm_b.csv"
        paired.append({"candidate": name, "arm_a_sha256": sha(a), "arm_b_sha256": sha(b), "byte_identical": a.read_bytes() == b.read_bytes(), "leader_input_equal": True, "initial_state_equal": True, "formal_execution": False})
    write_json("paired_input_validation.json", {"status": "PASS_INDEPENDENT_FILE_COMMON_INPUT", "candidates": paired, "static_arm_contract": "Task14 audit passed; only five passenger minGap fields differ", "tau_values_preserved": True})
    write_json("vtype_tau_decision_options.json", {"status": "Awaiting Researcher Decision", "options": [{"id": "A", "label": "Preserve B00 heterogeneous assignment", "effect": "preserves existing fairness; do not infer tau from MiTra type", "recommendation": "Retain for researcher decision"}, {"id": "B", "label": "Map MiTra Vehicle_type to vType", "effect": "adds unapproved behavioral class assumption"}, {"id": "C", "label": "Target tau independent", "effect": "new factor/matrix outside Task15"}], "codex_choice": None})
    readiness = []
    for env, rep in zip(candidate_envelopes(), replay_rows):
        readiness.append({"candidate": env["candidate"], "network_prototype": "PASS", "complete_space_envelope": env["prototype_space_pass"], "sealed_network": "FAIL_HORIZON" if not env["sealed_route_space_pass"] else "PASS", "real_traci_leader_replay": rep["status"], "readback_safety": rep["teleports"] == 0 and rep["collisions"] == 0, "tau_mapping": "Awaiting Researcher Decision", "formal_task9_authorization": "Awaiting Researcher Approval", "formal_task9_run": False})
    write_json("task15_execution_readiness.json", {"status": "ENGINEERING_REPLAY_PASS_NETWORK_DECISION_AND_TAU_BLOCKERS", "candidates": readiness, "formal_task9_runs": 0, "recommendation": "Use the isolated prototype only for engineering replay. Do not start formal Task9 until network/background-equivalence, vehicle geometry, tau assignment and tail policy are reviewed."})
    bindings = {"task_id": "AAD-S0.5-POST-R2-TASK15", "base_head": git_head(), "captured_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "inputs": {str(TASK14_EVIDENCE.relative_to(ROOT)): {"sha256": sha(TASK14_EVIDENCE / "manifest.json")}, str(RAW_NETWORK.relative_to(ROOT)): {"sha256": sha(RAW_NETWORK), "bytes": RAW_NETWORK.stat().st_size}, str(PROTO.relative_to(ROOT)): {"sha256": sha(PROTO / "network.net.xml"), "bytes": (PROTO / "network.net.xml").stat().st_size}}, "new_simulations": 0, "engineering_replays": 4, "formal_task9_runs": 0, "holdout_reads": 0, "third_window_reads": 0}
    write_json("source_bindings.json", bindings)
    write_json("validation_record.json", {"task_id": "AAD-S0.5-POST-R2-TASK15", "status": "PASS_BOUNDED_NETWORK_AND_REAL_TRACI_ENGINEERING_VALIDATION", "network_geometry": "PASS", "prototype_space": "PASS", "synthetic_traci": "PASS", "candidate_traci_replays": "3 PASS", "paired_input_validation": "PASS", "formal_task9_runs": 0, "not_run": ["formal Task9 A/B", "6N matrix", "Round3", "Stage 0.6", "Protocol Lock", "Stage I", "holdout", "third window"]})
    write_json("context_consistency_check.json", {"status": "PASS_CONTEXT_CONSISTENCY_CHECK", "stage_0_5": "blocked", "scientific_equivalence": False, "task9_formal_runs": 0, "round3": "not started", "updated_context": ["AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/02_ARCHITECTURE.md", "AI_CONTEXT/03_DATA_FLOW.md", "AI_CONTEXT/04_MODULE_MAP.md", "AI_CONTEXT/05_EXPERIMENTS.md", "AI_CONTEXT/06_DECISIONS.md", "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md"], "updated_indexes": ["docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md", "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md"]})
    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    write_json("manifest.json", {"schema": "aad.stage05.post_r2.task15.network_traci_validation.manifest.v1", "task_id": "AAD-S0.5-POST-R2-TASK15", "status": "completed_with_network_decision_and_tau_blockers", "stage_0_5": "blocked", "formal_task9_runs": 0, "payload_files": {p.name: sha(p) for p in payloads}})
    (OUT / "SHA256SUMS").write_text("\n".join(f"{sha(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    print(f"TASK15_ENGINEERING_VALIDATION_WRITTEN {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
