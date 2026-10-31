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
    seed: int | None = None,
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
    if seed is not None:
        cmd.extend(["--seed", str(int(seed)), "--random", "false"])
    rows = []
    initialization_move_m = 0.0
    traci.start(cmd)
    execution_status = "PASS"
    failure_reason = None
    lifecycle_events: list[dict[str, object]] = []
    invalid_state_rows: list[dict[str, object]] = []
    expected_rows = len(t)

    def _ids() -> set[str]:
        return set(traci.vehicle.getIDList())

    def _state(vehicle_id: str, input_time_s: float, phase: str) -> dict[str, object] | None:
        ids = _ids()
        if vehicle_id not in ids:
            return None
        try:
            position = float(traci.vehicle.getLanePosition(vehicle_id))
            speed = float(traci.vehicle.getSpeed(vehicle_id))
            accel = float(traci.vehicle.getAcceleration(vehicle_id))
            lane = str(traci.vehicle.getLaneID(vehicle_id))
        except Exception as exc:  # TraCI lifecycle can change between calls.
            invalid_state_rows.append({"input_time_s": input_time_s, "vehicle_id": vehicle_id, "phase": phase, "reason": f"read_error:{exc!r}"})
            return None
        values = (position, speed, accel)
        # SUMO exposes INVALID_DOUBLE_VALUE as roughly +/-1.073741824e9.
        if not all(np.isfinite(values)) or any(abs(v) > 1.0e6 for v in values) or speed < -1.0e-6:
            invalid_state_rows.append({"input_time_s": input_time_s, "vehicle_id": vehicle_id, "phase": phase, "position_m": position, "speed_mps": speed, "acceleration_mps2": accel, "reason": "nonfinite_or_invalid_sentinel"})
            return None
        return {"position_m": position, "speed_mps": speed, "acceleration_mps2": accel, "lane": lane}

    def _lifecycle_snapshot(input_time_s: float, phase: str) -> dict[str, object]:
        return {
            "input_time_s": input_time_s,
            "phase": phase,
            "vehicle_ids": sorted(_ids()),
            "starting_teleports": list(traci.simulation.getStartingTeleportIDList()),
            "ending_teleports": list(traci.simulation.getEndingTeleportIDList()),
            "arrived_ids": list(traci.simulation.getArrivedIDList()),
            "collisions": list(traci.simulation.getCollidingVehiclesIDList()),
        }

    def _fail(reason: str) -> None:
        nonlocal execution_status, failure_reason
        if execution_status == "PASS":
            execution_status = "FAIL"
            failure_reason = reason
    try:
        traci.vehicletype.setLength("leader", float(geometry_leader_length_m))
        traci.vehicletype.setLength("follower", float(geometry_follower_length_m))
        traci.vehicletype.setTau("follower", float(follower_tau_s))
        traci.vehicletype.setMinGap("follower", float(follower_min_gap_m))
        lane_index = lane_id.rsplit("_", 1)[-1]
        safe_insertion_gap = max(20.0, gap0 + 5.0, float(follower_tau_s) * follower_speed0 + float(follower_min_gap_m) + 5.0)
        follower_depart_pos = follower_front0 if initialization_mode == "direct" else float(leader_front[0] - geometry_leader_length_m - safe_insertion_gap)
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
        initial_ids = _ids()
        if not {"leader", "follower"}.issubset(initial_ids):
            missing = sorted({"leader", "follower"} - initial_ids)
            lifecycle_events.append(_lifecycle_snapshot(float(t[0]), "after_initial_step"))
            return {"status": "FAIL", "execution_status": "FAIL", "failure_reason": "missing_vehicle_after_initial_step", "rows": [], "formal_task9": False, "initialization_mode": initialization_mode, "missing_vehicle_ids": missing, "expected_rows": expected_rows, "applied_rows": 0, "evaluated_rows": 0, "lifecycle_events": lifecycle_events, "invalid_state_rows": invalid_state_rows}
        initial_sim_time = float(traci.simulation.getTime())
        time_anchor_offset_s = initial_sim_time - float(t[0])
        initialization_move_m = 0.0
        before_state = _state("follower", float(t[0]), "before_initial_move")
        if before_state is None:
            _fail("invalid_follower_state_before_initial_move")
            return {"status": "FAIL", "execution_status": execution_status, "failure_reason": failure_reason, "rows": [], "formal_task9": False, "initialization_mode": initialization_mode, "expected_rows": expected_rows, "applied_rows": 0, "evaluated_rows": 0, "lifecycle_events": lifecycle_events, "invalid_state_rows": invalid_state_rows}
        before = float(before_state["position_m"])
        if initialization_mode == "safe_then_move":
            traci.vehicle.moveTo("follower", lane_id, float(follower_front0))
            initialization_move_m = float(follower_front0 - before)
        traci.vehicle.setSpeed("follower", float(max(0.0, follower_speed0)))
        traci.vehicle.moveTo("leader", lane_id, float(leader_front[0]))
        traci.vehicle.setSpeed("leader", float(max(0.0, leader_speed[0])))
        # Formal t=0 is the first post-insertion state after the one-time
        # initialization move.  SUMO applies setSpeed over the following
        # integration interval, so the speed for sample i is issued before
        # the step ending at i and read back at that same sample.  Position
        # is placed at the same sample clock and read back after moveTo.
        def _append_sample(i: int, *, warmup: bool) -> bool:
            current = float(t[i])
            leader_state = _state("leader", current, "sample_readback")
            follower_state = _state("follower", current, "sample_readback")
            if leader_state is None or follower_state is None:
                lifecycle_events.append(_lifecycle_snapshot(current, "invalid_sample_state"))
                _fail("invalid_vehicle_state_at_sample_readback")
                return False
            position_error = float(leader_state["position_m"]) - float(leader_front[i])
            speed_error = float(leader_state["speed_mps"]) - max(0.0, float(leader_speed[i]))
            if abs(position_error) > 1e-7 or abs(speed_error) > 1e-7:
                invalid_state_rows.append({"input_time_s": current, "vehicle_id": "leader", "phase": "sample_readback", "position_error_m": position_error, "speed_error_mps": speed_error, "reason": "current_input_readback_mismatch"})
                _fail("leader_current_input_readback_mismatch")
                return False
            lp = float(leader_state["position_m"]); lv = float(leader_state["speed_mps"])
            fp = float(follower_state["position_m"]); fv = float(follower_state["speed_mps"])
            gap = lp - geometry_leader_length_m - fp
            rows.append({"input_time_s": current, "simulation_time_s": float(traci.simulation.getTime()), "leader_position_m": lp, "leader_speed_mps": lv, "follower_position_m": fp, "follower_speed_mps": fv, "follower_acc_mps2": float(follower_state["acceleration_mps2"]), "net_gap_m": gap, "closing_speed_mps": fv - lv, "leader_lane": leader_state["lane"], "follower_lane": follower_state["lane"], "initialization_warmup": warmup, "starting_teleports": list(traci.simulation.getStartingTeleportIDList()), "ending_teleports": list(traci.simulation.getEndingTeleportIDList()), "arrived_ids": list(traci.simulation.getArrivedIDList()), "collisions": list(traci.simulation.getCollidingVehiclesIDList())})
            lifecycle_events.append(_lifecycle_snapshot(current, "sample_recorded"))
            return True

        if not _append_sample(0, warmup=True):
            return {"status": "FAIL", "execution_status": execution_status, "failure_reason": failure_reason, "rows": rows if save_trace else [], "formal_task9": False, "initialization_mode": initialization_mode, "expected_rows": expected_rows, "applied_rows": len(rows), "evaluated_rows": 0, "lifecycle_events": lifecycle_events, "invalid_state_rows": invalid_state_rows}
        for i in range(1, len(t)):
            target = float(t[i])
            if not {"leader", "follower"}.issubset(_ids()):
                lifecycle_events.append(_lifecycle_snapshot(target, "before_dynamic_step"))
                _fail("vehicle_missing_before_dynamic_step")
                break
            traci.vehicle.setSpeed("leader", float(max(0.0, leader_speed[i])))
            traci.simulationStep(target + time_anchor_offset_s)
            if not {"leader", "follower"}.issubset(_ids()):
                lifecycle_events.append(_lifecycle_snapshot(target, "after_dynamic_step"))
                _fail("vehicle_missing_after_dynamic_step")
                break
            traci.vehicle.moveTo("leader", lane_id, float(leader_front[i]))
            if not _append_sample(i, warmup=False):
                break
    finally:
        traci.close()
    if not rows:
        return {"status": "FAIL", "execution_status": "FAIL", "failure_reason": failure_reason or "no_joint_rows", "rows": [], "formal_task9": False, "expected_rows": expected_rows, "applied_rows": 0, "evaluated_rows": 0, "lifecycle_events": lifecycle_events, "invalid_state_rows": invalid_state_rows}
    frame_rows = rows
    valid_rows = [r for r in frame_rows if not r.get("initialization_warmup", False)]
    eval_rows = valid_rows if valid_rows else frame_rows
    tele = [r for r in frame_rows if r["starting_teleports"] or r["ending_teleports"]]
    coll = [r for r in frame_rows if r["collisions"]]
    gaps = np.asarray([r["net_gap_m"] for r in eval_rows], dtype=float)
    if len(frame_rows) != expected_rows:
        _fail("incomplete_trace_length")
    if tele:
        _fail("teleport_event")
    if coll:
        _fail("collision_event")
    if not np.isfinite(gaps).all() or gaps.min() <= 0:
        _fail("invalid_or_nonpositive_gap")
    if invalid_state_rows:
        _fail("invalid_state_readback")
    status = "PASS" if execution_status == "PASS" else execution_status
    return {"status": status, "execution_status": execution_status, "failure_reason": failure_reason, "rows": frame_rows if save_trace else [], "expected_rows": expected_rows, "applied_rows": len(frame_rows), "evaluated_rows": len(eval_rows), "initialization_mode": initialization_mode, "initialization_move_m": initialization_move_m, "safe_insertion_gap_m": safe_insertion_gap, "time_anchor_offset_s": time_anchor_offset_s, "min_net_gap_m": float(gaps.min()), "p50_net_gap_m": float(np.quantile(gaps, 0.5)), "max_net_gap_m": float(gaps.max()), "follower_speed_range_mps": [float(min(r["follower_speed_mps"] for r in eval_rows)), float(max(r["follower_speed_mps"] for r in eval_rows))], "teleport_rows": len(tele), "collision_rows": len(coll), "formal_task9": False, "geometry_follower_length_m": geometry_follower_length_m, "geometry_leader_length_m": geometry_leader_length_m, "follower_tau_s": follower_tau_s, "follower_min_gap_m": follower_min_gap_m, "lifecycle_events": lifecycle_events, "invalid_state_rows": invalid_state_rows}
