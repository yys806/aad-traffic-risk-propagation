from __future__ import annotations

from pathlib import Path

import pandas as pd


def generate_merge_feasibility_emissions(output_csv: str | Path) -> Path:
    """Generate a small Flow-like emission CSV for feasibility validation.

    The sequence encodes a simple merge/bottleneck risk chain:
    a merging vehicle slows abruptly, the following vehicle gets low TTC/THW,
    and a third upstream vehicle reacts with delayed braking.
    """
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    times = [round(i * 0.5, 1) for i in range(13)]
    vehicle_specs = {
        "merge_0": {"lane": "merge", "x0": 80.0, "speed0": 12.0, "leader": "main_0"},
        "main_0": {"lane": "main", "x0": 95.0, "speed0": 11.0, "leader": "main_1"},
        "main_1": {"lane": "main", "x0": 70.0, "speed0": 11.5, "leader": "main_0"},
        "main_2": {"lane": "main", "x0": 45.0, "speed0": 12.0, "leader": "main_1"},
        "av_0": {"lane": "main", "x0": 25.0, "speed0": 12.5, "leader": "main_2"},
    }

    for t in times:
        for vehicle_id, spec in vehicle_specs.items():
            speed, accel = _profile(vehicle_id, t, float(spec["speed0"]))
            x = float(spec["x0"]) + speed * t
            headway, rel_speed = _safety_state(vehicle_id, t)
            rows.append(
                {
                    "run_id": "feas_merge_r0",
                    "time": t,
                    "id": vehicle_id,
                    "speed": round(speed, 3),
                    "realized_accel": round(accel, 3),
                    "headway": round(headway, 3),
                    "leader_id": str(spec["leader"]),
                    "leader_rel_speed": round(rel_speed, 3),
                    "x": round(x, 3),
                    "lane": str(spec["lane"]),
                    "edge_id": str(spec["lane"]),
                    "av_type": "AV" if vehicle_id.startswith("av") else "HV",
                }
            )

    pd.DataFrame(rows).to_csv(output_csv, index=False)
    return output_csv


def _profile(vehicle_id: str, t: float, base_speed: float) -> tuple[float, float]:
    if vehicle_id == "merge_0" and 2.0 <= t <= 3.0:
        accel = -4.5
    elif vehicle_id == "main_1" and 2.5 <= t <= 3.5:
        accel = -6.8
    elif vehicle_id == "main_2" and 3.0 <= t <= 4.0:
        accel = -3.8
    else:
        accel = -0.2 if 2.0 <= t <= 4.0 else 0.1
    speed = max(1.0, base_speed + accel * max(0.0, min(t - 1.5, 2.5)))
    return speed, accel


def _safety_state(vehicle_id: str, t: float) -> tuple[float, float]:
    if vehicle_id == "main_1" and 2.5 <= t <= 3.5:
        return 4.0, -4.5
    if vehicle_id == "main_2" and 3.0 <= t <= 4.0:
        return 6.0, -3.2
    if vehicle_id == "av_0" and 3.5 <= t <= 4.5:
        return 12.0, -1.5
    if vehicle_id == "merge_0" and 2.0 <= t <= 3.0:
        return 7.0, -3.0
    return 18.0, -0.5
