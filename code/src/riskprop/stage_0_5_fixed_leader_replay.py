"""Minimal fixed-leader trace/readback contract.

This module is deliberately simulator-neutral.  It validates a uniform
0.05-second leader trace and exercises the apply/readback boundary through a
small sink interface.  A real TraCI sink is not provided here; callers must
bind one explicitly and retain its per-step readbacks before formal execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class FixedLeaderReplayError(ValueError):
    """Fail-closed error for malformed or incomplete replay traces."""


class LeaderStateSink(Protocol):
    def set_state(self, vehicle_id: str, time_s: float, position_m: float, speed_mps: float) -> None: ...
    def get_state(self, vehicle_id: str) -> tuple[float, float, float]: ...


def validate_trace(trace, *, step_s: float = 0.05) -> dict[str, object]:
    required = {"time_s", "leader_y_m", "leader_speed_mps"}
    missing = required - set(trace.columns)
    if missing:
        raise FixedLeaderReplayError(f"missing_trace_columns:{sorted(missing)}")
    t = np.asarray(trace["time_s"], dtype=float)
    y = np.asarray(trace["leader_y_m"], dtype=float)
    v = np.asarray(trace["leader_speed_mps"], dtype=float)
    if len(t) < 2 or not (np.isfinite(t).all() and np.isfinite(y).all() and np.isfinite(v).all()):
        raise FixedLeaderReplayError("nonfinite_or_short_trace")
    dt = np.diff(t)
    if np.any(dt <= 0) or not np.allclose(dt, step_s, rtol=0, atol=1e-9):
        raise FixedLeaderReplayError("nonuniform_trace_grid")
    if np.any(v < 0):
        raise FixedLeaderReplayError("negative_leader_speed")
    return {
        "status": "Verified_trace_contract",
        "rows": int(len(t)),
        "time_start_s": float(t[0]),
        "time_end_s": float(t[-1]),
        "step_s": float(step_s),
        "position_start_m": float(y[0]),
        "position_end_m": float(y[-1]),
    }


def replay_trace(trace, sink: LeaderStateSink, *, vehicle_id: str = "leader", step_s: float = 0.05) -> dict[str, object]:
    contract = validate_trace(trace, step_s=step_s)
    rows = []
    for row in trace.itertuples(index=False):
        t = float(getattr(row, "time_s"))
        y = float(getattr(row, "leader_y_m"))
        v = float(getattr(row, "leader_speed_mps"))
        sink.set_state(vehicle_id, t, y, v)
        rt, ry, rv = sink.get_state(vehicle_id)
        rows.append({"time_s": t, "input_position_m": y, "readback_position_m": float(ry), "input_speed_mps": v, "readback_speed_mps": float(rv), "time_error_s": float(rt - t), "position_error_m": float(ry - y), "speed_error_mps": float(rv - v)})
    errors = np.asarray([[r["time_error_s"], r["position_error_m"], r["speed_error_mps"]] for r in rows], dtype=float)
    return {
        "contract": contract,
        "status": "PASS_READBACK" if np.allclose(errors, 0.0, rtol=0, atol=1e-12) else "READBACK_ERROR",
        "rows": rows,
        "max_abs_time_error_s": float(np.abs(errors[:, 0]).max()),
        "max_abs_position_error_m": float(np.abs(errors[:, 1]).max()),
        "max_abs_speed_error_mps": float(np.abs(errors[:, 2]).max()),
    }


@dataclass
class InMemoryLeaderSink:
    """Deterministic sink for engineering smoke tests only."""

    state: dict[str, tuple[float, float, float]]

    def __init__(self) -> None:
        self.state = {}

    def set_state(self, vehicle_id: str, time_s: float, position_m: float, speed_mps: float) -> None:
        self.state[vehicle_id] = (time_s, position_m, speed_mps)

    def get_state(self, vehicle_id: str) -> tuple[float, float, float]:
        return self.state[vehicle_id]
