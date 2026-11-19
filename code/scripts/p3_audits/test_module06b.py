"""0.0.6b 模块 0 与模块 2 重做（各自独立、各自先写预测）。

【模块 0：空路改路可达性】
装置：路网上**只有一辆车**（无背景车流——这是上次踩坑的地方：
      30 m/s 插入需约 100 m 净空，背景密集时探针根本进不来）。
做法：车从 in 边 2900 m 出发，路线初设为主路；
      在位置达到 X 的那一步，用 setRoute 改成绕行路线。
扫 X = 2900（进岔口前 98.5 m）、2950（前 48.5 m）、2990（前 8.5 m）。
预测：三处都应成功切入 bypass；routeLength ≈ 6500 m。
      若 2990 失败，说明必须提前 ≥10 m 决定，这个界限要写进决策点约定。

【模块 2：确定性重放】
装置：同一份配置（含背景车流）从 t=0 完整跑两次，各步记录全部车辆位置与速度。
预测：**逐帧完全一致，位置与速度最大偏差 = 0**（同种子、sigma=0、无随机项）。
      若不为 0，说明仿真本身不确定，先查配置，不谈分叉。
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_module06b"
STEP = 0.1
V_LIM = 30.0
DEMAND = 1600.0


def write_cfg(work: Path, tag: str, rou: str, end: float, trip: str | None = None) -> Path:
    cfg = work / f"run_{tag}.sumocfg"
    out = f'<output><tripinfo-output value="{trip}"/></output>' if trip else ""
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="{rou}"/></input>'
        f'<time><begin value="0"/><end value="{end:.1f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>{out}</configuration>',
        encoding="utf-8")
    return cfg


def module0_switch_at(work: Path, switch_pos: float) -> dict:
    """空路、一辆车，到 switch_pos 时把路线改到绕行。"""
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    rou_name = f"r_m0_{int(switch_pos)}.rou.xml"
    (work / rou_name).write_text(
        f'<routes>{vt}'
        f'<route id="rmain" edges="in mid bn out tail"/>'
        f'<route id="rbyp" edges="in bypass tail"/>'
        f'<vehicle id="probe" type="c" route="rmain" depart="0" departPos="2900"'
        f' departSpeed="max" departLane="0"/></routes>', encoding="utf-8")
    trip = f"t_m0_{int(switch_pos)}.xml"
    cfg = write_cfg(work, f"m0_{int(switch_pos)}", rou_name, 400.0, trip)

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    switched = False
    roads_seen = []
    try:
        for _ in range(int(400.0 / STEP)):
            ids = traci.vehicle.getIDList()
            if "probe" in ids:
                pos = traci.vehicle.getLanePosition("probe")
                rd = traci.vehicle.getRoadID("probe")
                if rd not in roads_seen:
                    roads_seen.append(rd)
                if not switched and pos >= switch_pos:
                    traci.vehicle.setRoute("probe", ["in", "bypass", "tail"])
                    switched = True
            traci.simulationStep()
    finally:
        traci.close()
    length = None
    tp = work / trip
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            if tri.get("id") == "probe":
                length = round(float(tri.get("routeLength")), 0)
    return {"switch_pos": switch_pos, "switched": switched,
            "roads": roads_seen, "route_length_m": length,
            "went_bypass": "bypass" in roads_seen}


def module2_run_twice(work: Path) -> dict:
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    period = 3600.0 / DEMAND
    rou_name = "r_m2.rou.xml"
    (work / rou_name).write_text(
        f'<routes>{vt}'
        f'<route id="main" edges="in mid bn out tail"/>'
        f'<flow id="f" type="c" route="main" begin="0" end="700" period="{period:.3f}"'
        f' departSpeed="max" departLane="0"/></routes>', encoding="utf-8")

    def once(tag: str):
        cfg = write_cfg(work, tag, rou_name, 660.0)
        traci = load_traci()
        traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                     "--collision.action", "warn", "--time-to-teleport", "-1"])
        c = traci.constants
        frames, sub = [], set()
        try:
            for _ in range(int(660.0 / STEP)):
                traci.simulationStep()
                for v in traci.vehicle.getIDList():
                    if v not in sub:
                        traci.vehicle.subscribe(v, (c.VAR_LANEPOSITION, c.VAR_SPEED))
                        sub.add(v)
                res = traci.vehicle.getAllSubscriptionResults()
                frames.append({v: (val.get(c.VAR_LANEPOSITION), val.get(c.VAR_SPEED))
                               for v, val in res.items()})
        finally:
            traci.close()
        return frames

    a, b = once("m2_run1"), once("m2_run2")
    n = min(len(a), len(b))
    max_dp = max_dv = 0.0
    id_mismatch = 0
    for fa, fb in zip(a[:n], b[:n]):
        if set(fa) != set(fb):
            id_mismatch += 1
        for v in set(fa) & set(fb):
            max_dp = max(max_dp, abs(fa[v][0] - fb[v][0]))
            max_dv = max(max_dv, abs(fa[v][1] - fb[v][1]))
    return {"frames": n, "max_dpos": max_dp, "max_dv": max_dv,
            "id_mismatch_frames": id_mismatch,
            "n_veh_last": len(a[-1]) if a else 0}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)

    print("=== 模块 0：空路改路可达性（无背景车流）===", flush=True)
    print(f"{'改路位置':>8} {'距岔口':>7} {'是否切入绕行':>11} {'路程m':>8} {'经过的边'}")
    for pos in (2900.0, 2950.0, 2990.0):
        r = module0_switch_at(OUT, pos)
        print(f"{pos:>8.0f} {3000 - pos:>7.1f} "
              f"{'是' if r['went_bypass'] else '否':>11} "
              f"{str(r['route_length_m']):>8} {r['roads']}", flush=True)
    print("  预测：三处都应切入绕行，路程约 6500 m", flush=True)

    print("\n=== 模块 2：同一配置跑两次是否逐帧一致 ===", flush=True)
    m2 = module2_run_twice(OUT)
    print(f"  对比帧数 {m2['frames']}，最后一帧 {m2['n_veh_last']} 辆车")
    print(f"  位置最大偏差 {m2['max_dpos']:.9f} m")
    print(f"  速度最大偏差 {m2['max_dv']:.9f} m/s")
    print(f"  车辆集合不一致帧数 {m2['id_mismatch_frames']}")
    ok = m2["max_dpos"] < 1e-6 and m2["max_dv"] < 1e-6 and m2["id_mismatch_frames"] == 0
    print(f"  预测为「偏差 = 0」→ {'通过 ✅' if ok else '不通过 ❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
