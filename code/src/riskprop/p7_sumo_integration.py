"""Bounded P7 engineering runner. Never invokes Formal measurement or experiments."""
from __future__ import annotations

from dataclasses import asdict
import json
import importlib.metadata
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import traceback

import pandas as pd

from .message_driven_longitudinal_controller import (LocalState, RunAssignment, byte_hash, canonical_bytes, load_engineering_config)
from .p7_evidence_adapter import P7EvidenceAdapter
from .p7_message_runtime import InProcessSingleHop, MessageController, generate_synthetic_message
from .stage_0_1_sumo import _write_network
from .stage_0_5_fixed_leader_traci import load_traci
from .stage_0_5_sumo import compute_sumo_measurements, FORMAL_ALGORITHM_VERSION

CONDITIONS = {"NO_MESSAGE": ("DISABLED", False), "DISABLED": ("DISABLED", True), "ENABLED": ("ENABLED", True)}
FLOAT_DECEL_TOLERANCE = 1e-9  # numerical roundoff only, m/s^2


def start_sumo_once(traci, cmd: list[str], run_id: str, adapter: P7EvidenceAdapter):
    """Explicit port prevents TraCI's outer process-relaunch loop on connection failure.

    TraCI may retry socket connections to this one process. A failed start consumes
    the launch budget; the exclusive receipt cannot be overwritten or retried.
    """
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    adapter.blob("launch_consumed.json", {"run_id": run_id, "launch_budget": 1,
        "launch_attempt": 1, "explicit_port": port, "connection_retries": 60,
        "process_relaunch_allowed": False, "budget_consumed_before_start_call": True})
    return traci.start(cmd, port=port, numRetries=60, label=run_id)


def abnormal_deceleration(acceleration: float, native_decel: float) -> bool:
    return acceleration < -native_decel - FLOAT_DECEL_TOLERANCE


def write_json(path: Path, value):
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def read_state(conn, vehicle: str, incarnation: str, step: int, original_max: float) -> tuple[LocalState, dict]:
    v = conn.vehicle
    lane = v.getLaneID(vehicle)
    leader = v.getLeader(vehicle)
    leader_id, gap = (leader[0], float(leader[1])) if leader else (None, None)
    leader_speed = float(v.getSpeed(leader_id)) if leader else None
    state = LocalState(vehicle, incarnation, float(conn.simulation.getTime()), step, v.getRoadID(vehicle), lane,
        float(v.getLanePosition(vehicle)), tuple(v.getPosition(vehicle)), float(v.getSpeed(vehicle)),
        float(v.getAcceleration(vehicle)), original_max, float(conn.lane.getMaxSpeed(lane)),
        leader_id, leader_speed, gap)
    state.validate()
    row = {**asdict(state), "vehicle_existence": True, "readback_status": "OBSERVED",
           "vehicle_max_speed_mps": float(v.getMaxSpeed(vehicle)), "speed_mode": int(v.getSpeedMode(vehicle)),
           "native_speed_without_traci_mps": float(v.getSpeedWithoutTraCI(vehicle))}
    if row["speed_mode"] != 31:
        raise RuntimeError("NATIVE_SPEED_MODE_CHANGED")
    return state, row


def existing_measurement_attachment(adapter: P7EvidenceAdapter, rows: list[dict], config: dict) -> dict:
    actual = [r for r in rows if r["readback_status"] == "OBSERVED"]
    frame = pd.DataFrame([{**r, "run_id": adapter.run_id, "scenario_id": "P7_SYNTHETIC_ENGINEERING",
        "experiment_mode": "ENGINEERING_DIAGNOSTIC_ONLY", "configured_seed": config["seed"],
        "trajectory_id": r["vehicle_incarnation_id"], "incarnation_id": r["vehicle_incarnation_id"],
        "time_s": r["simulation_time_s"], "leader_identity_status": "observed" if r["leader_id"] else "not_present",
        "leader_incarnation_id": adapter.run_id + ":" + r["leader_id"] + ":entry1" if r["leader_id"] else None} for r in actual])
    # Existing per-state TTC/quality core only; no event/rho/regional aggregation.
    measured = compute_sumo_measurements(frame)
    path = adapter.root / "existing_measurement_states.csv"
    measured.to_csv(path, index=False, lineterminator="\n")
    adapter.artifacts[path.name] = byte_hash(path.read_bytes())
    return {"measurement_version": "aad.p7.existing-sumo-quality-adapter.v1",
        "existing_formal_measurement_version": FORMAL_ALGORITHM_VERSION,
        "adapter_version": "aad.p7.existing-risk-reference.v1",
        "raw_observation_ref": "actual_trajectory.json",
        "measurement_ref": path.name, "measurement_sha256": adapter.artifacts[path.name],
        "measurement_status_counts": {str(k): int(v) for k, v in measured.measurement_status.value_counts().items()},
        "formal_region": None, "formal_cohort": None, "formal_observation_window": None,
        "regional_risk_status": "UNKNOWN_MISSING_FORMAL_SCOPE", "risk_effect_status": "UNKNOWN",
        "formal_rho_or_p2_recomputed": False, "formal_source_qualification": "UNKNOWN",
        "scientific_claim_eligible": False}


def run_condition(output: Path, config_path: Path, *, condition: str, adoption_mode: str, assignment_id: str,
                  adoption_mode_source: str, run_id: str | None = None) -> dict:
    if condition not in CONDITIONS:
        raise ValueError("unsupported engineering condition")
    expected_mode, generate = CONDITIONS[condition]
    assignment = RunAssignment(adoption_mode, assignment_id, adoption_mode_source)
    if adoption_mode != expected_mode:
        raise ValueError("CONDITION_ASSIGNMENT_MISMATCH")
    config = load_engineering_config(config_path)
    if not config.get("reference_deceleration_mps2"):
        raise ValueError("UNBOUNDED_REFERENCE_STEP_NOT_ADMITTED; v1 capture is historical failed engineering evidence")
    run_id = run_id if run_id is not None else "p7-task2-" + condition.lower()
    if not isinstance(run_id, str) or not run_id or any(c in run_id for c in ("/", "\\", "\n", "\r")):
        raise ValueError("INVALID_RUN_ID")
    adapter = P7EvidenceAdapter(output, run_id, assignment)
    adapter.blob("controller_config.json", config_path.read_bytes(), raw=True)
    adapter.blob("run_config.json", {"condition": condition, **asdict(assignment), "config": config})
    root = Path(__file__).resolve().parents[3]
    tracked_dirty = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root).decode("utf-8", errors="replace")
    source_paths = [Path(__file__), Path(__file__).with_name("message_driven_longitudinal_controller.py"),
        Path(__file__).with_name("p7_message_runtime.py"), Path(__file__).with_name("p7_evidence_adapter.py"),
        Path(__file__).with_name("controller_evidence.py"), Path(__file__).with_name("stage_0_1_sumo.py"),
        Path(__file__).with_name("stage_0_5_sumo.py"), Path(__file__).with_name("formal_risk_measurement.py"),
        root / "code/scripts/run_p7_task2_engineering.py"]
    for module in tuple(sys.modules.values()):
        candidate = getattr(module, "__file__", None)
        if candidate:
            p = Path(candidate).resolve()
            if p.is_relative_to(root / "code/src/riskprop") and p.suffix == ".py":
                source_paths.append(p)
    closure = {p.relative_to(root).as_posix(): byte_hash(p.read_bytes()) for p in sorted(set(source_paths))}
    code_hash = byte_hash(canonical_bytes(closure))
    sumo = shutil.which("sumo")
    if not sumo:
        raise RuntimeError("SUMO_UNAVAILABLE")
    version = subprocess.check_output([sumo, "--version"]).decode("utf-8", errors="replace")
    if "sumo 1.26.0" not in version:
        raise RuntimeError("SUMO_1_26_0_REQUIRED_FOR_THIS_ENGINEERING_CAPTURE")
    traci = load_traci()
    tools_dir = Path(traci.__file__).parent
    bindings = {str(p): byte_hash(p.read_bytes()) for p in sorted(tools_dir.glob("*.py"))}
    adapter.blob("provenance.json", {"git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
        "dirty_worktree": tracked_dirty, "source_closure": closure, "source_closure_hash": code_hash,
        "python": sys.version, "python_executable": sys.executable, "sumo_version": version,
        "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "pandas")},
        "sumo_executable": sumo, "sumo_executable_sha256": byte_hash(Path(sumo).read_bytes()),
        "traci_import": str(traci.__file__), "traci_binding_files": bindings,
        "data_source": "synthetic engineering network/routes only; no dataset/holdout", "seed": config["seed"],
        "free_disk_bytes": shutil.disk_usage(output).free, "estimated_output_bytes": 50000000})
    network = output / "network"
    network.mkdir()
    _write_network(network)  # reuse existing engineering topology, no historical output access
    route = network / "p7.rou.xml"
    c = config
    attrs = f'accel="{c["native_accel_mps2"]}" decel="{c["native_decel_mps2"]}" sigma="{c["native_sigma"]}" tau="{c["native_tau_s"]}" minGap="{c["native_min_gap_m"]}" speedFactor="{c["native_speed_factor"]}" length="5" carFollowModel="Krauss"'
    route.write_text(f'''<routes>
<vType id="p7_leader_type" {attrs} maxSpeed="{c["leader_max_speed_mps"]}"/>
<vType id="p7_target_type" {attrs} maxSpeed="{c["target_max_speed_mps"]}"/>
<route id="p7route" edges="tgt_in tgt_road tgt_out"/>
<vehicle id="{c["leader_vehicle_id"]}" type="p7_leader_type" route="p7route" depart="0" departPos="{c["leader_depart_pos_m"]}" departSpeed="{c["leader_depart_speed_mps"]}"/>
<vehicle id="{c["target_vehicle_id"]}" type="p7_target_type" route="p7route" depart="0" departPos="{c["target_depart_pos_m"]}" departSpeed="{c["target_depart_speed_mps"]}"/>
</routes>''', encoding="utf-8", newline="\n")
    for p in network.iterdir():
        adapter.artifacts[p.relative_to(output).as_posix()] = byte_hash(p.read_bytes())
    cmd = [sumo, "--net-file", str((network / "dual_corridor.net.xml").resolve()), "--route-files", str(route.resolve()),
        "--step-length", str(c["step_s"]), "--seed", str(c["seed"]), "--random", "false",
        "--no-step-log", "true", "--duration-log.disable", "true", "--collision.action", "warn",
        "--error-log", str((output / "sumo_errors.log").resolve()), "--log", str((output / "sumo.log").resolve())]
    adapter.blob("sumo_launch.json", {"command": cmd, "native_speed_mode_expected": 31, "vehicle_setters": ["setMaxSpeed"]})
    conn, controller = None, None
    rows, actions, decisions, lifecycle, faults, simulation_events = [], [], [], [], [], []
    message_sent, entered, exited = False, False, False
    status = "PASS"
    step = 0
    try:
        start_sumo_once(traci, cmd, run_id, adapter)
        conn = traci.getConnection(run_id)
        adapter.blob("traci_runtime_version.json", {"getVersion": conn.getVersion()})
        while step < int(c["max_duration_s"] / c["step_s"]):
            if controller and not controller.closed:
                state, _ = read_state(conn, controller.vehicle, controller.incarnation, step, controller.original_max)
                if generate and not message_sent and state.simulation_time_s >= c["message_generated_time_s"]:
                    message = generate_synthetic_message(adapter, state, c)
                    InProcessSingleHop(adapter).send(message, controller, state)
                    message_sent = True
                decision = controller.decide(state, assignment, conn.vehicle)
                decisions.append({"simulation_time_s": state.simulation_time_s, "simulation_step": step, **decision})
            conn.simulationStep()
            step += 1
            now = float(conn.simulation.getTime())
            coll = list(conn.simulation.getCollidingVehiclesIDList())
            tele = list(conn.simulation.getStartingTeleportIDList()) + list(conn.simulation.getEndingTeleportIDList())
            emergency = list(conn.simulation.getEmergencyStoppingVehiclesIDList())
            simulation_events.append({"simulation_time_s": now, "simulation_step": step,
                "colliding_vehicle_ids": coll, "teleport_vehicle_ids": tele,
                "emergency_stopping_vehicle_ids": emergency})
            arrived = list(conn.simulation.getArrivedIDList())
            departed = list(conn.simulation.getDepartedIDList())
            ids = set(conn.vehicle.getIDList())
            stop_reason = "COLLISION_TELEPORT_OR_EMERGENCY: " + repr((coll, tele, emergency)) if coll or tele or emergency else None
            if departed or arrived:
                lifecycle.append({"simulation_time_s": now, "simulation_step": step, "departed": departed, "arrived": arrived})
            if c["target_vehicle_id"] in ids:
                if exited:
                    raise RuntimeError("UNEXPECTED_TARGET_REINCARNATION")
                if not entered:
                    incarnation = run_id + ":" + c["target_vehicle_id"] + ":entry1"
                    state, row = read_state(conn, c["target_vehicle_id"], incarnation, step, float(conn.vehicle.getMaxSpeed(c["target_vehicle_id"])))
                    controller = MessageController(adapter, assignment, c, state, code_hash, byte_hash(config_path.read_bytes()))
                    entered = True
                else:
                    state, row = read_state(conn, controller.vehicle, controller.incarnation, step, controller.original_max)
                ref, _ = adapter.blob(f"readbacks/{step}.json", row)
                rows.append(row)
                actions.append(controller.observe(row, ref))
                if abnormal_deceleration(row["acceleration_mps2"], c["native_decel_mps2"]):
                    stop_reason = "ABNORMAL_BRAKING_BEYOND_CONFIGURED_NATIVE_DECEL"
            elif entered and not exited:
                if c["target_vehicle_id"] not in arrived:
                    raise RuntimeError("TARGET_DISAPPEARED_WITHOUT_LIFECYCLE")
                row = {"simulation_time_s": now, "simulation_step": step, "vehicle_id": controller.vehicle,
                       "vehicle_incarnation_id": controller.incarnation, "vehicle_existence": False,
                       "readback_status": "VEHICLE_EXITED", "position_xy_m": None, "lane_position_m": None,
                       "speed_mps": None, "acceleration_mps2": None, "leader_id": None, "net_gap_m": None}
                ref, _ = adapter.blob(f"readbacks/{step}.json", row)
                rows.append(row)
                actions.append(controller.observe(row, ref))
                exited = True
            if stop_reason:
                raise RuntimeError(stop_reason)
            if conn.simulation.getMinExpectedNumber() == 0:
                break
        if not entered or not exited:
            raise RuntimeError("TARGET_LIFECYCLE_INCOMPLETE_WITHIN_ENGINEERING_BOUND")
    except Exception as exc:
        status = "FAIL_STOPPED"
        faults.append({"failure": repr(exc), "simulation_step": step, "traceback": traceback.format_exc()})
    finally:
        if conn is not None:
            conn.close()
    emergency_warnings = {line.strip().lower() for name in ("sumo_errors.log", "sumo.log")
        if (output / name).exists()
        for line in (output / name).read_text(encoding="utf-8", errors="replace").splitlines()
        if "emergency braking" in line.lower()}
    if emergency_warnings:
        status = "FAIL_STOPPED"
        faults.append({"failure": "SUMO_EMERGENCY_BRAKING_WARNING", "simulation_step": step})
    adapter.blob("actual_trajectory.json", rows)
    adapter.blob("policy_decisions.json", decisions)
    adapter.blob("lifecycle.json", lifecycle)
    adapter.blob("simulation_events.json", simulation_events)
    adapter.blob("failures.json", faults)
    if status != "PASS" and controller and not controller.closed:
        controller.censor(rows[-1]["simulation_time_s"] if rows else step * c["step_s"], step, repr(faults))
    adapter.blob("command_tenures.json", controller.command_tenures if controller else [])
    if controller and rows:
        measurement = existing_measurement_attachment(adapter, rows, c)
        controller.risk_attachment(actions, rows[-1]["simulation_time_s"], step, measurement)
    audit = adapter.finalize()
    present = [r for r in rows if r["vehicle_existence"]]
    native_follow = [r for r in present if r["leader_id"] and r["speed_mps"] < r["vehicle_max_speed_mps"] - 1e-6]
    commands = [r for r in adapter.journal.records if r["kind"] == "command"]
    release = [r for r in commands if r["data"]["command_type"] == "RESTORE_NATIVE_MAX_SPEED"]
    summary = {"status": status, "condition": condition, "run_id": run_id, "assignment": asdict(assignment), "seed": c["seed"],
        "fixture_only": True, "scientific_claim_eligible": False, "parameter_status": c["parameter_status"],
        "safety_layer_design_status": "NOT_INCLUDED_BY_RESEARCHER_DECISION",
        "native_model": "Krauss", "native_speed_modes": sorted({r["speed_mode"] for r in present}),
        "native_following_below_vehicle_max_samples": len(native_follow),
        "native_without_traci_speed_max_abs_difference": max((abs(r["speed_mps"] - r["native_speed_without_traci_mps"]) for r in present), default=None),
        "target_entered": entered, "target_exited": exited, "observed_state_rows": len(present),
        "trajectory_rows_including_exit": len(rows),
        "collision_count": sum(bool(e["colliding_vehicle_ids"]) for e in simulation_events),
        "teleport_count": sum(bool(e["teleport_vehicle_ids"]) for e in simulation_events),
        "emergency_stopping_step_count": sum(bool(e["emergency_stopping_vehicle_ids"]) for e in simulation_events),
        "emergency_braking_warning_count": len(emergency_warnings),
        "observed_min_acceleration_mps2": min((r["acceleration_mps2"] for r in present), default=None),
        "deceleration_roundoff_tolerance_mps2": FLOAT_DECEL_TOLERANCE,
        "message_generated": message_sent,
        "release_command_count": len(release), "first_release_time_s": release[0]["time"]["native_timestamp"] if release else None,
        "source_payload_hashes": [r["data"]["payload_hash"] for r in adapter.journal.records if r["kind"] == "message"],
        "p3_structural_status": audit["structural_status"], "counts_by_kind": audit["counts_by_kind"],
        "policy_input_included": len(audit["recorded_policy_input_receipts"]),
        "risk_effect_status": "UNKNOWN", "faults": faults}
    write_json(output / "run_summary.json", summary)
    return summary


def compare_conditions(root: Path) -> dict:
    data = {condition: json.loads((root / condition.lower() / "actual_trajectory.json").read_text(encoding="utf-8")) for condition in CONDITIONS}
    ds = {condition: json.loads((root / condition.lower() / "policy_decisions.json").read_text(encoding="utf-8")) for condition in CONDITIONS}
    def physical(rows):
        return [{k: r.get(k) for k in ("simulation_time_s", "simulation_step", "speed_mps", "acceleration_mps2", "lane_position_m", "vehicle_existence")} for r in rows]
    def decisions(rows):
        return [{k: r[k] for k in ("simulation_time_s", "target_speed_reference_mps", "control_intent", "considered_risk_levels", "new_command_needed")} for r in rows]
    n, d, e = data["NO_MESSAGE"], data["DISABLED"], data["ENABLED"]
    baseline = {r["simulation_step"]: r for r in n if r["vehicle_existence"]}
    common = [(baseline[r["simulation_step"]], r) for r in e if r["vehicle_existence"] and r["simulation_step"] in baseline]
    return {"status": "ENGINEERING_DIAGNOSTIC_ONLY",
        "no_message_disabled_physical_rows_identical": physical(n) == physical(d),
        "no_message_disabled_policy_outputs_identical": decisions(ds["NO_MESSAGE"]) == decisions(ds["DISABLED"]),
        "enabled_policy_reference_present": any(r["target_speed_reference_mps"] is not None for r in ds["ENABLED"]),
        "common_post_step_samples": len(common),
        "enabled_no_message_max_abs_speed_difference_mps": max(abs(a["speed_mps"] - b["speed_mps"]) for a, b in common),
        "enabled_no_message_max_abs_acceleration_difference_mps2": max(abs(a["acceleration_mps2"] - b["acceleration_mps2"]) for a, b in common),
        "comparison_support": "common observed simulation steps only; engineering, not formal observation window",
        "adoption_induced_action_effect": "NOT_IDENTIFIED", "regional_risk_effect": "UNKNOWN"}
