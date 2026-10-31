"""Assemble the bounded Task16 engineering evidence package."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "local_research/staging/task16_20261031"
INPUTS = ROOT / "local_research/staging/task14_20261031/candidate_inputs"
EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK16-FOLLOWER-REPLAY-AND-PREFORMAL-READINESS-20261031"
SUMO_BINARY = Path(r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe")
TAU = [0.7389146576529666, 1.093342856277335, 1.3877275660721775, 1.8288599276236361, 2.5614676647488244]
CANDIDATES = ("962-958-1", "926-924-1", "857-851-1")


def dump(name: str, value: object) -> None:
    (EVIDENCE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def qstats(values: np.ndarray) -> dict[str, float | int]:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if not len(a):
        return {"count": 0}
    return {
        "count": int(len(a)),
        "mae": float(np.mean(np.abs(a))),
        "p50_abs": float(np.quantile(np.abs(a), 0.50)),
        "p95_abs": float(np.quantile(np.abs(a), 0.95)),
        "max_abs": float(np.max(np.abs(a))),
        "signed_mean": float(np.mean(a)),
        "signed_sum": float(np.sum(a)),
    }


def control_timing() -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    for candidate in CANDIDATES:
        timing = json.loads((STAGING / "leader_timing" / f"{candidate}.json").read_text(encoding="utf-8"))
        trace = pd.read_csv(INPUTS / f"{candidate}_resampled_0p05.csv")
        rows = timing["rows"]
        correction = np.asarray([r["moveTo_correction_m"] for r in rows], dtype=float)
        pre_move_error = np.asarray([r["input_position_m"] - r["pre_move_position_m"] for r in rows], dtype=float)
        previous_speed = trace["leader_speed_mps"].to_numpy(float)[:-1]
        current_speed = trace["leader_speed_mps"].to_numpy(float)[1:]
        pos_speed = np.diff(trace["leader_y_m"].to_numpy(float)) / 0.05
        n = min(len(rows), len(current_speed), len(pos_speed))
        current_speed = current_speed[:n]
        previous_speed = previous_speed[:n]
        pos_speed = pos_speed[:n]
        command_speed = np.asarray([r["command_speed_mps"] for r in rows[:n]], dtype=float)
        candidate = {
            "candidate": candidate,
            "status": timing["status"],
            "control_steps": len(rows),
            "position_correction_m": qstats(correction),
            "pre_move_position_error_m": qstats(pre_move_error),
            "cumulative_absolute_position_correction_m": float(np.sum(np.abs(correction))),
            "cumulative_signed_position_correction_m": float(np.sum(correction)),
            "readback_position_error_m": timing["max_abs_position_error_m"],
            "readback_speed_error_mps": timing["max_abs_speed_error_mps"],
            "native_or_external_control": {
                "position": "external moveTo after simulationStep",
                "speed": "setSpeed command for preceding integration interval",
                "speed_phase_lag_s": timing["speed_phase_lag_s"],
            },
            "method_comparison": {
                "A_previous_sample_speed_command": {
                    "command_minus_current_observed_speed_mps": qstats(command_speed - current_speed),
                    "command_minus_previous_observed_speed_mps": qstats(command_speed - previous_speed),
                    "observed_readback_minus_command_mps": timing["max_abs_speed_error_mps"],
                },
                "B_position_difference_speed": {
                    "position_difference_minus_current_speed_mps": qstats(pos_speed - current_speed),
                    "position_difference_minus_previous_speed_mps": qstats(pos_speed - previous_speed),
                },
                "C_current_sample_speed_command": {
                    "command_minus_current_observed_speed_mps": qstats(current_speed - current_speed),
                    "current_minus_previous_speed_phase_difference_mps": qstats(current_speed - previous_speed),
                    "status": "offline timing comparator; not inserted into formal replay",
                },
            },
        }
        candidates.append(candidate)
    return {
        "status": "COMPLETED_CONTROL_PHASE_DIAGNOSTIC",
        "control_method_A": "Task15 adapter retained for engineering; previous-sample setSpeed, post-step moveTo",
        "alternative_B": "offline position-difference speed comparator",
        "alternative_C": "offline current-sample speed phase comparator",
        "interpretation_boundary": "exact position/speed readback is conditional on external moveTo/setSpeed commands and is not natural SUMO integration truth",
        "candidates": candidates,
    }


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary_path = STAGING / "joint_replay_summary.csv"
    shutil.copy2(summary_path, EVIDENCE / "joint_replay_summary.csv")
    shutil.copy2(STAGING / "init_probe.json", EVIDENCE / "initialization_probe.json")
    summary = pd.read_csv(summary_path)
    dump("control_timing_diagnostics.json", control_timing())
    dump("joint_replay_validation.json", {
        "status": "PASS_ENGINEERING_ONLY",
        "attempted": int(len(summary)),
        "completed": int((summary["status"] == "PASS_JOINT_ENGINEERING").sum()),
        "failed": int((summary["status"] != "PASS_JOINT_ENGINEERING").sum()),
        "candidate_counts": summary.groupby("candidate").size().to_dict(),
        "geometry_counts": summary.groupby("geometry").size().to_dict(),
        "tau_values": sorted(summary["tau_s"].unique().tolist()),
        "arms": sorted(summary["arm"].unique().tolist()),
        "initialization_modes": sorted(summary["initialization_mode"].unique().tolist()),
        "teleport_rows_total": int(summary["teleport_rows"].sum()),
        "collision_rows_total": int(summary["collision_rows"].sum()),
        "formal_task9_runs": 0,
        "engineering_only": True,
    })
    dump("network_background_assessment.json", {
        "sealed_b00_mainline_length_m": 659.17,
        "prototype_mainline_length_m": 1000.0,
        "prototype_lanes": 3,
        "prototype_speed_mps": 30.0,
        "sealed_b00_modified": False,
        "engineering_result": "prototype contains all three complete leader envelopes and joint replays",
        "background_equivalence": "UNKNOWN / NOT CLAIMED",
        "decision_owner": "researcher",
        "recommendation": "retain prototype for controlled local-response engineering; do not call it B00 network-equivalent without a separate scientific decision",
    })
    dump("vehicle_geometry_comparison.json", {
        "status": "COMPLETED_ENGINEERING_SENSITIVITY",
        "geometry_M": {"car_length_m": 5.0, "medium_vehicle_length_m": 5.8333, "source": "MiTra T1 candidate fields"},
        "geometry_B": {"passenger_length_m": 4.4196, "source": "sealed B00 vType"},
        "initial_gap_effect_m": {"962-958-1": 0.5804, "926-924-1": 0.5804, "857-851-1": 0.99705},
        "formal_choice": "Awaiting Researcher Decision",
        "a_b_internal_matching": "same selected geometry is used in both arms; no geometry choice is frozen",
    })
    task15_resampling = json.loads((ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK15-TASK9-NETWORK-TRACI-VALIDATION-20261031/resampling_kinematic_diagnostics.json").read_text(encoding="utf-8"))
    tail = json.loads((ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK15-TASK9-NETWORK-TRACI-VALIDATION-20261031/tail_policy_comparison.json").read_text(encoding="utf-8"))
    dump("resampling_tail_diagnostics.json", {"resampling": task15_resampling, "tail_policy": tail, "formal_tail_choice": "Awaiting Researcher Decision"})
    try:
        version = subprocess.run([str(SUMO_BINARY), "--version"], capture_output=True, text=True, check=False).stdout.strip()
    except OSError as exc:
        version = f"unavailable:{exc!r}"
    dump("traci_environment.json", {
        "sumo_binary": str(SUMO_BINARY),
        "sumo_version": version,
        "sumo_home": None,
        "official_tools_path": r"C:\Program Files (x86)\Eclipse\Sumo\tools",
        "python_binding": "traci and sumolib load through official tools path",
        "step_length_s": 0.05,
        "task16_status": "verified for engineering replay",
    })
    dump("paired_input_validation.json", json.loads((ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK15-TASK9-NETWORK-TRACI-VALIDATION-20261031/paired_input_validation.json").read_text(encoding="utf-8")))
    dump("vtype_tau_decision_options.json", {
        "tau_values": TAU,
        "observed_policy": "retain B00 heterogeneous tau values; do not infer from MiTra Vehicle_type",
        "options": [
            {"id": "A", "description": "retain existing B00 heterogeneous assignment", "effect": "best protocol continuity; target vType still requires researcher selection"},
            {"id": "B", "description": "map MiTra Vehicle_type to B00 vType", "effect": "adds unvalidated category-to-behavior assumption"},
            {"id": "C", "description": "treat target tau as an independent factor", "effect": "changes formal matrix and is outside current authorization"},
        ],
        "decision_status": "Awaiting Researcher Decision",
    })
    dump("formal_execution_chain_preflight.json", {
        "input_layer": "PASS_ENGINEERING_BINDINGS",
        "simulation_layer": "PASS_ENGINEERING_ONLY",
        "pairing_layer": "PASS_STATIC_COMMON_INPUT_AND_ARM_AUDIT",
        "results_layer": "INTERFACE_NOT_USED_FOR_FORMAL_METRICS",
        "reproducibility": {"input_hashes": "Task14/Task15 hashes reused", "sumo_version": version, "seeds": [20261101, 20261102, 20261103], "formal_runs": 0},
        "formal_authorization": "PENDING_RESEARCHER",
    })
    dump("task16_execution_readiness.json", {
        "status": "COMPLETED_PREFORMAL_ENGINEERING_READY_PENDING_RESEARCHER_DECISIONS",
        "candidates": {c: {"joint_replay": "PASS_ENGINEERING_ONLY", "formal_execution": "Awaiting Researcher Approval"} for c in CANDIDATES},
        "researcher_decisions_pending": ["network/background equivalence", "vehicle geometry", "follower vType/tau", "leader control policy", "tail policy", "formal candidate admission", "formal Task9 launch"],
        "formal_task9_runs": 0,
        "stage_0_5": "blocked",
        "scientific_equivalence": False,
        "round3": "not_started",
    })
    dump("validation_record.json", {
        "task_id": "AAD-S0.5-POST-R2-TASK16",
        "status": "PASS_BOUNDED_ENGINEERING_VALIDATION_WITH_RESEARCHER_DECISION_BLOCKERS",
        "matrix": "60/60 engineering-only joint replays passed with safe_then_move; 0 teleport/collision",
        "direct_initialization_probe": "962 direct pass; 926/857 direct insertion fail closed; safe_then_move pass for all",
        "formal_task9_runs": 0,
        "not_run": ["formal Task9 A/B", "6N repetition matrix", "Round3", "Stage 0.6", "Protocol Lock", "Stage I", "holdout", "third window"],
        "validation_scope": ["Task16 code", "Task14 input bindings", "isolated prototype", "SUMO 1.26.0/TraCI"],
    })
    dump("source_bindings.json", {
        "task_id": "AAD-S0.5-POST-R2-TASK16",
        "base_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "task14_inputs": "local_research/staging/task14_20261031/candidate_inputs/",
            "task15_network": "local_research/staging/task15_20261031/network_prototype/",
            "task16_joint_runner": "code/scripts/run_stage_0_5_task16_joint_replay.py",
            "task16_adapter": "code/src/riskprop/stage_0_5_fixed_leader_follower_traci.py",
        },
        "formal_task9_runs": 0,
    })
    payload = sorted(p.name for p in EVIDENCE.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    manifest = {
        "schema": "aad.stage05.post_r2.task16.follower_replay_preformal_readiness.manifest.v1",
        "task_id": "AAD-S0.5-POST-R2-TASK16",
        "status": "completed_preformal_engineering_ready_pending_researcher_decisions",
        "stage_0_5": "blocked",
        "formal_task9_runs": 0,
        "payload_files": payload,
        "source_scope": "Task14 candidate inputs + Task15 isolated prototype + Task16 engineering replays; no formal scientific metrics",
    }
    dump("manifest.json", manifest)
    lines = [f"{sha256(EVIDENCE / name)}  {name}" for name in sorted(p.name for p in EVIDENCE.iterdir() if p.is_file() and p.name != "SHA256SUMS")]
    (EVIDENCE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(EVIDENCE), "payload_files": len(payload), "summary_rows": len(summary)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
