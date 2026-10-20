"""Independent Newell simplified car-following prototype (NOT a SUMO-native model).

SUMO 1.26 has no Newell car-following model, so this module provides an explicitly
non-SUMO prototype that consumes exactly the same observed leader trajectory and is
scored with exactly the same metrics as the SUMO replays. Results from it must never
be presented as SUMO-native behaviour.

Model form used here (project implementation of Newell's "min of two constraints"
simplified car-following, discretised at the recording step):

    v_target(t) = min( v_free , max( 0 , (x_leader(t) - delta - x_follower(t)) / tau ) )
    x_follower(t + dt) = x_follower(t) + v_target(t) * dt

with ``tau`` the effective time lag and ``delta`` the minimum bumper-to-bumper
spacing. The rule is stated here in full because the discretisation choice is a
project decision; it is not copied from a paper's equation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

VERSION = "stage-0.5-newell-prototype-v1"
DEFAULT_TAUS = (1.0, 1.6)
#: delta chosen as minGap + passenger length so that the standing spacing is
#: comparable in spirit to the frozen Krauss configuration.
DEFAULT_DELTA_M = 2.5 + 4.4196


def simulate_newell(observed: pd.DataFrame, *, tau: float, delta_m: float = DEFAULT_DELTA_M,
                    free_speed_mps: float = 27.78, dt: float | None = None) -> pd.DataFrame:
    """Integrate the Newell prototype against one observed leader trajectory."""
    times = observed.time_s.to_numpy(dtype=float) - float(observed.time_s.iloc[0])
    leader_y = observed.leader_y_m.to_numpy(dtype=float)
    if dt is None:
        dt = float(np.median(np.diff(times))) if len(times) > 1 else 0.1
    if dt <= 0:
        raise ValueError("non_positive_dt")
    follower_y = np.empty_like(leader_y)
    follower_v = np.empty_like(leader_y)
    follower_y[0] = float(observed.follower_y_m.iloc[0])
    follower_v[0] = float(observed.follower_speed_mps.iloc[0])
    for index in range(1, len(times)):
        previous_y = follower_y[index - 1]
        constraint_speed = (leader_y[index - 1] - delta_m - previous_y) / tau
        speed = float(np.clip(min(free_speed_mps, constraint_speed), 0.0, free_speed_mps))
        follower_v[index] = speed
        follower_y[index] = previous_y + speed * dt
    return pd.DataFrame({
        "t": times,
        "leader_y": leader_y,
        "leader_target_y": leader_y,
        "follower_y": follower_y,
        "follower_v": follower_v,
        "leader_v": np.gradient(leader_y, times),
        "gap_m": leader_y - follower_y - 4.4196,
    })


def newell_record(observed: pd.DataFrame, *, tau: float, delta_m: float = DEFAULT_DELTA_M,
                  free_speed_mps: float = 27.78, run_id: int = -1, seed: int = 0,
                  trajectory_id: str = "prototype", lane_id: str = "prototype") -> dict[str, object]:
    """Replay-compatible record so that the SUMO metrics apply unchanged.

    The extra keys mirror the SUMO replay record contract; the prototype has no
    insertion step and no leader tracking error, which is stated rather than faked.
    """
    simulated = simulate_newell(observed, tau=tau, delta_m=delta_m, free_speed_mps=free_speed_mps)
    return {
        "run_id": int(run_id),
        "trajectory_id": str(trajectory_id),
        "leader_trajectory_id": str(trajectory_id),
        "lane_id": str(lane_id),
        "seed": int(seed),
        "tau_s": float(tau),
        "duration_s": float(simulated.t.iloc[-1]) if len(simulated) else 0.0,
        "leader_target_max_abs_deviation_m": 0.0,
        "vehicle_length_m": 4.4196,
        "leader_length_inference_spread_m": float(observed.leader_length_inference_spread_m.iloc[0]),
        "initial_speed_offset_mps": 0.0,
        "insertion_delay_s": 0.0,
        "observed": observed,
        "simulated": simulated,
    }
