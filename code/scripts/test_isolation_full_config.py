"""Isolation check at the FULL main-experiment configuration (P1).

阶段：P1 ｜ 运行目录：code/outputs/analysis/isolation_full_config_20261118 ｜ 数据：— 
      ｜ 脚本：code/scripts/test_isolation_full_config.py

Why this exists
---------------
The earlier check (`test_isolation_rng_coupling.py`) ran speedDev=0 with 60 vehicles on
2000 m edges and reported PASS (27,770/27,770 identical samples). The main experiment runs
speedDev=0.12 with 387 vehicles on 6000 m edges. That PASS cannot be carried over: driver
imperfection (sigma, speedDev) is exactly what consumes the random stream, and speedDev=0
removes it. So the old test removed the very mechanism it was meant to rule out.

Method
------
Same seed, same network, same 387 target-road vehicles (identical vType, departures, spacing).
The source road carries the same 387 vehicles at the same positions. The ONLY difference:
vehicle A194 stops for 12 s two hundred metres ahead of its start. Vehicle count, positions and
departure times are identical, so any difference on the target road is caused by the random
stream being shared, not by traffic.

PASS  = every target-road vehicle is bit-identical in both runs.
FAIL  = any difference; the isolated design then needs per-vehicle RNG isolation or sigma=0.

Usage
-----
  python code/scripts/test_isolation_full_config.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

import run_stage1_isolated_two_arm as base  # noqa: E402
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = base.STEP
END = base.END
SEED = 20261116
N = base.cohort_size()
BRAKE_INDEX = 194          # which source-road vehicle stops
BRAKE_AHEAD_M = 200.0
BRAKE_DUR = 12.0


def routes_xml(brake: bool) -> str:
    vt = ('<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0.5"'
          ' tau="0.6" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" speedDev="0.12"/>')
    vehs = []
    for i in range(N):
        pos = base.TGT_COHORT_START - base.FILL_GAP * i
        vehs.append(f'<vehicle id="T{i}" type="cal" route="rt" depart="0"'
                    f' departPos="{pos:.2f}" departSpeed="15" departLane="0"/>')
        if brake and i == BRAKE_INDEX:
            # same vehicle, same slot, same departure; only its behaviour differs
            vehs.append(f'<vehicle id="A{i}" type="cal" route="rs" depart="0"'
                        f' departPos="{pos:.2f}" departSpeed="15" departLane="0">'
                        f'<stop lane="src_0" duration="{BRAKE_DUR:.0f}"'
                        f' startPos="{pos + BRAKE_AHEAD_M:.2f}"'
                        f' endPos="{pos + BRAKE_AHEAD_M:.2f}" speed="0"/>'
                        f'</vehicle>')
        else:
            vehs.append(f'<vehicle id="A{i}" type="cal" route="rs" depart="0"'
                        f' departPos="{pos:.2f}" departSpeed="15" departLane="0"/>')
    return (f'<routes>{vt}<route id="rs" edges="src"/><route id="rt" edges="tgt"/>'
            f'{"".join(vehs)}</routes>')


def run(tmp: Path, brake: bool, tag: str) -> dict[str, dict[str, list[float]]]:
    (tmp / f"routes_{tag}.rou.xml").write_text(routes_xml(brake), encoding="utf-8")
    cfg = tmp / f"run_{tag}.sumocfg"
    cfg.write_text(
        f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="routes_{tag}.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{SEED}"/></random_number>
</configuration>""", encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn"])
    steps = int(round(END / STEP))
    ids = [f"T{i}" for i in range(N)]
    rec: dict[str, dict[str, list[float]]] = {v: {"x": [], "v": []} for v in ids}
    try:
        for _ in range(steps):
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())
            for v in ids:
                if v in present:
                    rec[v]["x"].append(traci.vehicle.getLanePosition(v))
                    rec[v]["v"].append(traci.vehicle.getSpeed(v))
                else:
                    rec[v]["x"].append(float("nan"))
                    rec[v]["v"].append(float("nan"))
    finally:
        traci.close()
    return rec


def main() -> int:
    scratch = ROOT / "code" / "outputs" / "analysis" / "_iso_full_scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="iso_full_", dir=str(scratch)))
    (tmp / "net.net.xml").write_text(base.net_xml(), encoding="utf-8")

    print(f"full-config isolation: {N} vehicles per edge, speedDev=0.12, {END:.0f} s, seed {SEED}")
    plain = run(tmp, brake=False, tag="plain")
    brake = run(tmp, brake=True, tag="brake")

    same_x = same_v = total = 0
    max_dx = 0.0
    n_veh_diff = 0
    for v in plain:
        ax, bx = np.array(plain[v]["x"]), np.array(brake[v]["x"])
        av, bv = np.array(plain[v]["v"]), np.array(brake[v]["v"])
        m = np.isfinite(ax) & np.isfinite(bx)
        if not m.any():
            continue
        total += int(m.sum())
        eq_x = int(np.sum(ax[m] == bx[m]))
        eq_v = int(np.sum(av[m] == bv[m]))
        same_x += eq_x
        same_v += eq_v
        if eq_x != int(m.sum()) or eq_v != int(m.sum()):
            n_veh_diff += 1
        max_dx = max(max_dx, float(np.max(np.abs(ax[m] - bx[m]))))

    verdict = "PASS" if same_x == total and same_v == total else "FAIL"
    print(f"target-edge samples compared : {total}")
    print(f"identical positions          : {same_x} ({100*same_x/max(total,1):.4f}%)")
    print(f"identical speeds             : {same_v} ({100*same_v/max(total,1):.4f}%)")
    print(f"vehicles with any difference : {n_veh_diff} / {len(plain)}")
    print(f"max position difference (m)  : {max_dx:.6g}")
    print(f"\nVERDICT: {verdict}")

    out = {"verdict": verdict, "config": {"vehicles_per_edge": N, "speed_dev": 0.12,
                                          "edge_len_m": 6000.0, "end_s": END, "step_s": STEP,
                                          "seed": SEED, "brake_index": BRAKE_INDEX,
                                          "brake_ahead_m": BRAKE_AHEAD_M,
                                          "brake_duration_s": BRAKE_DUR},
           "samples": total, "identical_positions": same_x, "identical_speeds": same_v,
           "vehicles_with_difference": n_veh_diff, "n_vehicles": len(plain),
           "max_position_difference_m": max_dx}
    outdir = ROOT / "code" / "outputs" / "analysis"
    outdir.mkdir(parents=True, exist_ok=True)
    p = outdir / "isolation_full_config_20261118.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {p}")
    return 0 if verdict == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
