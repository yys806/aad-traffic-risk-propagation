"""Engineering-only Leader/Follower joint replay in SUMO/TraCI."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .stage_0_5_fixed_leader_pair import FixedLeaderPairError
from .stage_0_5_fixed_leader_traci import load_traci


def run_joint_replay(
    trace,
    *,
    sumo_cfg: Path,
    lane_id: str,
    geometry_follower_length_m: float,
    geometry_leader_length_m: float,
    follower_tau_s: float,
    follower_min_gap_m: float,
    start_offset_m: float = 40.0,
    sumo_binary: str = "sumo",
    step_s: float = 0.05,
    save_trace: bool = False,
    initialization_mode: str = "direct",
) -> dict[str, object]:
    if initialization_mode not in {"direct", "safe_then_move"}:
        raise FixedLeaderPairError(f"unsupported_initialization_mode:{initialization_mode}")
    required = {"relative_time_s", "leader_y_m", "leader_speed_mps", "follower_speed_mps", "net_gap_m"}
    missing = required - set(trace.columns)
    if missing:
        raise FixedLeaderPairError(f"missing_joint_trace_columns:{sorted(missing)}")
    t = trace["relative_time_s"].to_numpy(float)
    leader_center = trace["leader_y_m"].to_numpy(float) + start_offset_m
    leader_front = leader_center + geometry_leader_length_m / 2.0
    leader_speed = trace["leader_speed_mps"].to_numpy(float)
    follower_speed0 = float(trace["follower_speed_mps"].iloc[0])
    gap0 = float(trace["net_gap_m"].iloc[0])
    follower_front0 = float(leader_front[0] - geometry_leader_length_m - gap0)
    if len(t) < 2 or np.any(np.diff(t) <= 0) or not np.allclose(np.diff(t), step_s, rtol=0, atol=1e-9):
        raise FixedLeaderPairError("joint_trace_nonuniform_grid")
    traci = load_traci()
    cmd = [sumo_binary, "-c", str(sumo_cfg), "--step-length", str(step_s), "--time-to-teleport", "-1", "--collision.action", "warn", "--no-step-log", "true"]
    rows = []
    initialization_move_m = 0.0
    traci.start(cmd)
    try:
        traci.vehicletype.setLength("leader", float(geometry_leader_length_m))
        traci.vehicletype.setLength("follower", float(geometry_follower_length_m))
        traci.vehicletype.setTau("follower", float(follower_tau_s))
        traci.vehicletype.setMinGap("follower", float(follower_min_gap_m))
        lane_index = lane_id.rsplit("_", 1)[-1]
        follower_depart_pos = follower_front0 if initialization_mode == "direct" else float(leader_front[0] - geometry_leader_length_m - max(20.0, gap0 + 5.0))
        # Use the observed initial speed even for the safe-depart position;
        # the vehicle is inserted sufficiently far behind the leader, so this
        # does not compromise insertion safety and preserves the t[0] speed
        # anchor before the one-time position relocation.
        follower_depart_speed = follower_speed0
        traci.vehicle.add("leader", "r0", typeID="leader", depart="0", departLane=lane_index, departPos=str(float(leader_front[0])), departSpeed=str(max(0.1, float(leader_speed[0]))))
        traci.vehicle.add("follower", "r0", typeID="follower", depart="0", departLane=lane_index, departPos=str(follower_depart_pos), departSpeed=str(max(0.0, follower_depart_speed)))
        traci.vehicle.setSpeedMode("leader", 0)
        traci.vehicle.setLaneChangeMode("leader", 0)
        traci.vehicle.setLaneChangeMode("follower", 0)
        # Apply the requested initial speeds before the insertion step.  SUMO
        # otherwise exposes the safe-depart speed (0 m/s) for the warmup row
        # and only applies setSpeed after the next simulation step.
        traci.vehicle.setSpeed("leader", float(max(0.0, leader_speed[0])))
        traci.vehicle.setSpeed("follower", float(max(0.0, follower_speed0)))
        traci.simulationStep()
        initial_ids = set(traci.vehicle.getIDList())
        if not {"leader", "follower"}.issubset(initial_ids):
            return {"status": "DIRECT_INSERTION_FAILED" if initialization_mode == "direct" else "JOINT_INSERTION_FAILED", "rows": [], "formal_task9": False, "initialization_mode": initialization_mode, "missing_vehicle_ids": sorted({"leader", "follower"} - initial_ids)}
        initial_sim_time = float(traci.simulation.getTime())
        time_anchor_offset_s = initial_sim_time - float(t[0])
        initialization_move_m = 0.0
        before = float(traci.vehicle.getLanePosition("follower"))
        if initialization_mode == "safe_then_move":
            traci.vehicle.moveTo("follower", lane_id, float(follower_front0))
            initialization_move_m = float(follower_front0 - before)
        traci.vehicle.setSpeed("follower", float(max(0.0, follower_speed0)))
        traci.vehicle.moveTo("leader", lane_id, float(leader_front[0]))
        traci.vehicle.setSpeed("leader", float(max(0.0, leader_speed[0])))
        # The first SUMO step is a vehicle-insertion/initialization step.  Its
        # post-step state is explicitly anchored to input t[0]; subsequent
        # steps advance one complete input interval.  This avoids silently
        # dropping the first follower response interval.
        rows.append({"input_time_s": float(t[0]), "simulation_time_s": initial_sim_time, "leader_position_m": float(traci.vehicle.getLanePosition("leader")), "leader_speed_mps": float(traci.vehicle.getSpeed("leader")), "follower_position_m": float(traci.vehicle.getLanePosition("follower")), "follower_speed_mps": float(traci.vehicle.getSpeed("follower")), "follower_acc_mps2": float(traci.vehicle.getAcceleration("follower")), "net_gap_m": float(traci.vehicle.getLanePosition("leader") - geometry_leader_length_m - traci.vehicle.getLanePosition("follower")), "closing_speed_mps": float(traci.vehicle.getSpeed("follower") - traci.vehicle.getSpeed("leader")), "leader_lane": traci.vehicle.getLaneID("leader"), "follower_lane": traci.vehicle.getLaneID("follower"), "initialization_warmup": True, "starting_teleports": list(traci.simulation.getStartingTeleportIDList()), "ending_teleports": list(traci.simulation.getEndingTeleportIDList()), "collisions": list(traci.simulation.getCollidingVehiclesIDList())})
        for i in range(1, len(t)):
            if "leader" not in traci.vehicle.getIDList() or "follower" not in traci.vehicle.getIDList():
                break
            target = float(t[i])
            traci.vehicle.setSpeed("leader", float(max(0.0, leader_speed[i - 1])))
            traci.simulationStep(target + time_anchor_offset_s)
            traci.vehicle.moveTo("leader", lane_id, float(leader_front[i]))
            sim_time = float(traci.simulation.getTime())
            lp = float(traci.vehicle.getLanePosition("leader")); lv = float(traci.vehicle.getSpeed("leader"))
            fp = float(traci.vehicle.getLanePosition("follower")); fv = float(traci.vehicle.getSpeed("follower"))
            fa = float(traci.vehicle.getAcceleration("follower"))
            gap = lp - geometry_leader_length_m - fp
            rows.append({"input_time_s": target, "simulation_time_s": sim_time, "leader_position_m": lp, "leader_speed_mps": lv, "follower_position_m": fp, "follower_speed_mps": fv, "follower_acc_mps2": fa, "net_gap_m": gap, "closing_speed_mps": fv - lv, "leader_lane": traci.vehicle.getLaneID("leader"), "follower_lane": traci.vehicle.getLaneID("follower"), "initialization_warmup": False, "starting_teleports": list(traci.simulation.getStartingTeleportIDList()), "ending_teleports": list(traci.simulation.getEndingTeleportIDList()), "collisions": list(traci.simulation.getCollidingVehiclesIDList())})
    finally:
        traci.close()
    if not rows:
        return {"status": "NO_JOINT_ROWS", "rows": [], "formal_task9": False}
    frame_rows = rows
    valid_rows = [r for r in frame_rows if not r.get("initialization_warmup", False)]
    eval_rows = valid_rows if valid_rows else frame_rows
    tele = [r for r in frame_rows if r["starting_teleports"] or r["ending_teleports"]]
    coll = [r for r in frame_rows if r["collisions"]]
    gaps = np.asarray([r["net_gap_m"] for r in eval_rows], dtype=float)
    return {"status": "PASS_JOINT_ENGINEERING" if not tele and not coll and np.isfinite(gaps).all() and gaps.min() > 0 else "JOINT_SAFETY_OR_GAP_ISSUE", "rows": frame_rows if save_trace else [], "applied_rows": len(frame_rows), "evaluated_rows": len(eval_rows), "initialization_mode": initialization_mode, "initialization_move_m": initialization_move_m, "time_anchor_offset_s": time_anchor_offset_s, "min_net_gap_m": float(gaps.min()), "p50_net_gap_m": float(np.quantile(gaps, 0.5)), "max_net_gap_m": float(gaps.max()), "follower_speed_range_mps": [float(min(r["follower_speed_mps"] for r in eval_rows)), float(max(r["follower_speed_mps"] for r in eval_rows))], "teleport_rows": len(tele), "collision_rows": len(coll), "formal_task9": False, "geometry_follower_length_m": geometry_follower_length_m, "geometry_leader_length_m": geometry_leader_length_m, "follower_tau_s": follower_tau_s, "follower_min_gap_m": follower_min_gap_m}
