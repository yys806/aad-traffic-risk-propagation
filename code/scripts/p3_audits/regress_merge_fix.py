"""0.0.8b 汇合口修复后的四项回归（改动前必须验，不许跳过）。

改动：tail 由单车道改为**两车道**，out（主路）接 0 车道、bypass（绕行）接 1 车道，
两股车流到终点各走各的，不再抢道。

【跑之前写死的预测】
1. 自由流：主路（in@2900 起）6597 m ÷ 30 = 219.9 s；绕行同路程 219.9 s。
   实际两条路剩余距离相同（都是 6597 m），所以自由流用时应当相同。
2. 汇合等待：无背景时 0 s；1600 辆/时背景下 **< 5 s**（改动前是约 300 s）。
3. 队列仍能形成：低速车峰值 ≥20 辆，队尾回溢但不越过 3000 m。
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
OUT = ROOT / "code/outputs/analysis/P3_regress"
STEP = 0.1
V_LIM = 30.0
T0, BLOCK = 600.0, 180.0
FORK = 3000.0


def single_run(work: Path, route_edges: str, tag: str, demand: float,
               end: float, with_block: bool) -> dict:
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    extra = ""
    if demand > 0:
        period = 3600.0 / demand
        extra = (f'<flow id="f" type="c" route="main" begin="0" end="{end:.0f}"'
                 f' period="{period:.3f}" departSpeed="max" departLane="0"/>')
    (work / f"r_{tag}.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>'
        f'<route id="detour" edges="in bypass tail"/>'
        f'<route id="probe_main" edges="in mid bn out tail"/>'
        f'<route id="probe_det" edges="in bypass tail"/>{extra}'
        f'<vehicle id="probe" type="c" route="{route_edges}" depart="300"'
        f' departPos="2900" departSpeed="max" departLane="0"/></routes>',
        encoding="utf-8")
    cfg = work / f"run_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_{tag}.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{end:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="t_{tag}.xml"/></output></configuration>',
        encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    sub = set()
    end_of_bypass_t = enter_tail_t = None
    reached_end_pos = False
    try:
        for k in range(int(end / STEP)):
            t = round(k * STEP, 2)
            if with_block:
                if not blocked and t >= T0:
                    traci.lane.setMaxSpeed("bn_0", 4.0)
                    blocked = True
                if blocked and t >= T0 + BLOCK:
                    traci.lane.setMaxSpeed("bn_0", V_LIM)
                    blocked = False
            traci.simulationStep()
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED))
                    sub.add(v)
            if k % 2:
                continue
            r = traci.vehicle.getSubscriptionResults("probe")
            if r:
                road = str(r.get(c.VAR_ROAD_ID, ""))
                pos = float(r.get(c.VAR_LANEPOSITION, -1))
                if road == "bypass" and pos > 5400:
                    reached_end_pos = True
                if road == "tail" and reached_end_pos and enter_tail_t is None:
                    enter_tail_t = t
    finally:
        traci.close()

    trip = None
    tp = work / f"t_{tag}.xml"
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            if tri.get("id") == "probe":
                trip = {"duration": round(float(tri.get("duration")), 1),
                        "route_len": round(float(tri.get("routeLength")), 0)}
    return {"tag": tag, "trip": trip, "enter_tail_t": enter_tail_t,
            "reached_bypass_end": reached_end_pos}


def queue_check(work: Path, demand: float = 1600.0) -> dict:
    period = 3600.0 / demand
    end = T0 + BLOCK + 900
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    (work / "r_q.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>'
        f'<flow id="f" type="c" route="main" begin="0" end="{end:.0f}" period="{period:.3f}"'
        f' departSpeed="max" departLane="0"/></routes>', encoding="utf-8")
    cfg = work / "run_q.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_q.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{end:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    max_slow = 0
    min_tail_x = 1e9
    try:
        for k in range(int(end / STEP)):
            t = round(k * STEP, 2)
            if not blocked and t >= T0:
                traci.lane.setMaxSpeed("bn_0", 4.0)
                blocked = True
            if blocked and t >= T0 + BLOCK:
                traci.lane.setMaxSpeed("bn_0", V_LIM)
                blocked = False
            traci.simulationStep()
            if k % 10:
                continue
            slow = 0
            for v in traci.vehicle.getIDList():
                if traci.vehicle.getRoadID(v) == "mid":
                    if traci.vehicle.getSpeed(v) < 5.0:
                        slow += 1
                        min_tail_x = min(min_tail_x, FORK + traci.vehicle.getLanePosition(v))
            max_slow = max(max_slow, slow)
    finally:
        traci.close()
    return {"max_slow": max_slow,
            "min_tail_x": (None if min_tail_x > 1e8 else round(min_tail_x, 0))}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)

    print("=== 回归 1：自由流（无背景车流）===", flush=True)
    print("  预测：两条路剩余均为 6597 m，30 m/s → 219.9 s", flush=True)
    a = single_run(OUT, "probe_main", "ff_main", 0.0, 700.0, False)
    b = single_run(OUT, "probe_det", "ff_det", 0.0, 700.0, False)
    for lbl, r in [("主路", a), ("绕行", b)]:
        t = (r["trip"] or {}).get("duration")
        dev = None if t is None else (t - 219.9) / 219.9 * 100
        print(f"  {lbl}: {t} s（偏差 {dev:+.1f}%）" if dev is not None else f"  {lbl}: 无记录")

    print("\n=== 回归 2：汇合等待（1600 辆/时背景）===", flush=True)
    print("  预测：从 bypass 尽头到进入 tail 的等待 < 5 s（改动前约 300 s）", flush=True)
    c1 = single_run(OUT, "probe_det", "bg_det", 1600.0, 1700.0, True)
    d = c1["trip"] or {}
    print(f"  绕行支: 总行程 {d.get('duration')} s，路程 {d.get('route_len')} m，"
          f"到达过绕行尽头={c1['reached_bypass_end']}，进入 tail 时刻={c1['enter_tail_t']}")
    arrived_bypass_end = 300 + 100 + 183.3   # 粗估
    wait = None if c1["enter_tail_t"] is None else round(c1["enter_tail_t"] - arrived_bypass_end, 1)
    print(f"  估计汇合等待 ≈ {wait} s（粗估，仅供判断量级）")

    print("\n=== 回归 3：队列仍能形成 ===", flush=True)
    q = queue_check(OUT)
    ok3 = q["max_slow"] >= 20 and (q["min_tail_x"] is None or q["min_tail_x"] > FORK + 100)
    print(f"  低速车峰值 {q['max_slow']} 辆（预测 ≥20）")
    print(f"  队尾最上游 {q['min_tail_x']} m（预测 > 3100，即不越过改道点）")
    print(f"  判定 {'✅' if ok3 else '❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
