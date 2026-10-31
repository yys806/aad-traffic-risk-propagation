"""Real SUMO/TraCI fixed-leader replay adapter for engineering validation."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np

from .stage_0_5_fixed_leader_replay import FixedLeaderReplayError


def load_traci():
    candidates = []
    if os.environ.get("SUMO_HOME"):
        candidates.append(Path(os.environ["SUMO_HOME"]) / "tools")
    candidates.extend([Path(r"C:\Program Files (x86)\Eclipse\Sumo\tools")])
    for path in candidates:
        if (path / "traci").is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
    if importlib.util.find_spec("traci") is None:
        raise FixedLeaderReplayError("traci_binding_unavailable")
    import traci  # type: ignore
    return traci


def replay_trace_in_sumo(
    trace,
    *,
    sumo_cfg: Path,
    lane_id: str,
    vehicle_id: str,
    start_offset_m: float = 0.0,
    sumo_binary: str = "sumo",
    step_s: float = 0.05,
) -> dict[str, object]:
    """Apply a fixed leader trace and record immediate readback.

    The first trace row is used as the depart state. SUMO applies a speed
    command over the following integration interval, so each readback speed
    is compared with the command from the preceding trace sample. Position is
    placed at the target sample after advancing the clock. This explicit
    one-step control phase is part of the engineering record; it is not a
    scientific reaction-time estimator.
    """
    required = {"relative_time_s", "leader_y_m", "leader_speed_mps"}
    missing = required - set(trace.columns)
    if missing:
        raise FixedLeaderReplayError(f"missing_trace_columns:{sorted(missing)}")
    t = trace["relative_time_s"].to_numpy(float)
    y = trace["leader_y_m"].to_numpy(float) + start_offset_m
    v = trace["leader_speed_mps"].to_numpy(float)
    if len(t) < 2 or not np.isfinite(t).all() or not np.isfinite(y).all() or not np.isfinite(v).all():
        raise FixedLeaderReplayError("invalid_trace_values")
    dt = np.diff(t)
    if np.any(dt <= 0) or not np.allclose(dt, step_s, rtol=0, atol=1e-9):
        raise FixedLeaderReplayError("nonuniform_trace_grid")
    traci = load_traci()
    cmd = [sumo_binary, "-c", str(sumo_cfg), "--step-length", str(step_s), "--time-to-teleport", "-1", "--collision.action", "warn", "--no-step-log", "true"]
    rows = []
    traci.start(cmd)
    try:
        traci.vehicle.add(vehicle_id, "r0", typeID="replay", depart="0", departLane=lane_id.rsplit("_", 1)[-1], departPos=str(float(y[0])), departSpeed=str(max(0.1, float(v[0]))))
        traci.vehicle.setSpeedMode(vehicle_id, 0)
        traci.vehicle.setLaneChangeMode(vehicle_id, 0)
        traci.simulationStep()
        for i in range(1, len(t)):
            target = float(t[i])
            command_speed = float(v[i - 1])
            traci.vehicle.setSpeed(vehicle_id, max(0.0, command_speed))
            traci.simulationStep(target)
            pre_move_position = float(traci.vehicle.getLanePosition(vehicle_id))
            traci.vehicle.moveTo(vehicle_id, lane_id, float(y[i]))
            sim_time = float(traci.simulation.getTime())
            read_y = float(traci.vehicle.getLanePosition(vehicle_id))
            read_v = float(traci.vehicle.getSpeed(vehicle_id))
            read_lane = traci.vehicle.getLaneID(vehicle_id)
            rows.append({"input_time_s": target, "command_time_s": float(t[i - 1]), "simulation_time_s": sim_time, "pre_move_position_m": pre_move_position, "input_position_m": float(y[i]), "moveTo_correction_m": float(y[i] - pre_move_position), "command_speed_mps": command_speed, "readback_position_m": read_y, "readback_speed_mps": read_v, "time_error_s": sim_time - target, "position_error_m": read_y - float(y[i]), "speed_error_mps": read_v - command_speed, "lane_id": read_lane, "starting_teleports": list(traci.simulation.getStartingTeleportIDList()), "ending_teleports": list(traci.simulation.getEndingTeleportIDList()), "collisions": list(traci.simulation.getCollidingVehiclesIDList())})
    finally:
        traci.close()
    errors = np.asarray([[r["time_error_s"], r["position_error_m"], r["speed_error_mps"]] for r in rows], dtype=float)
    teleport_rows = [r for r in rows if r["starting_teleports"] or r["ending_teleports"]]
    collision_rows = [r for r in rows if r["collisions"]]
    return {"status": "PASS_READBACK" if len(rows) and np.isfinite(errors).all() and not teleport_rows and not collision_rows else "READBACK_OR_SAFETY_EVENT", "rows": rows, "applied_rows": len(rows), "speed_phase_lag_s": float(step_s), "position_control_phase": "after_clock_step", "speed_control_phase": "preceding_interval_command", "starting_or_ending_teleport_rows": len(teleport_rows), "collision_rows": len(collision_rows), "max_abs_time_error_s": float(np.abs(errors[:, 0]).max()) if len(rows) else None, "max_abs_position_error_m": float(np.abs(errors[:, 1]).max()) if len(rows) else None, "max_abs_speed_error_mps": float(np.abs(errors[:, 2]).max()) if len(rows) else None, "formal_task9": False}
