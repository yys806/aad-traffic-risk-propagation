"""0.0.7 模块 1：基线 + 候选车名单（只记录，不抽样、不改路）。

依据 GPT 第五十五轮模块 1：
  跑一条**不因测量改路**的基线；对候选车记 ID、实际发车时刻、决策步 t_i、
  车道、位置、速度；对账计划/实际插入/过线/到达/未完成。

🔴 与规格文档的一处更正：规格里按 660 s 算预测（293 辆），
   但模块 1 需要覆盖「堵塞 + 消散」全窗，故本脚本用 **1680 s**（t0=600、堵塞 180 s）。
   预测相应改为：计划 1600×1680/3600 ≈ **747 辆**。

【跑之前写死的预测】
- 计划车数 ≈ 747
- 实际插入与计划之差 ≤1%
- 每 60 s 实际入口车数与该时段计划值偏差 ≤10%
- departDelay 中位数 <10 s
- 单车空路 2900→3000 m 用时 = 3.33 s（另测，不在本脚本）
- 过线车数 700–745；到达车数 650–730

用法：python module1_roster.py
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_module1"

STEP = 0.1
V_LIM = 30.0
DEMAND = 1600.0
T_END = 1680.0
T0 = 600.0
BLOCK = 180.0
FORK = 3000.0


def build_rou(work: Path) -> tuple[Path, int]:
    """显式车辆清单（不用 flow），每辆车有确定的计划发车时刻。"""
    period = 3600.0 / DEMAND
    n = int(T_END / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    vehs = []
    for i in range(n):
        vehs.append(f'<vehicle id="V{i:04d}" type="c" route="main"'
                    f' depart="{i*period:.3f}" departSpeed="max" departLane="0"/>')
    rou = (f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>'
           f'{"".join(vehs)}</routes>')
    p = work / "r_base.rou.xml"
    p.write_text(rou, encoding="utf-8")
    return p, n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    net = build_net(50.0, OUT)
    rou, n_planned = build_rou(OUT)
    period = 3600.0 / DEMAND

    cfg = OUT / "run_base.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_base.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="trip_base.xml"/></output></configuration>',
        encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    sub = set()
    prev_road: dict[str, str] = {}
    cross_t: dict[str, float] = {}
    cross_state: dict[str, tuple] = {}
    entry_t: dict[str, float] = {}
    sample_every = 5  # 每 0.5 s 查一次位置（降低开销）
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 2)
            if not blocked and t >= T0:
                traci.lane.setMaxSpeed("bn_0", 4.0)
                blocked = True
            if blocked and t >= T0 + BLOCK:
                traci.lane.setMaxSpeed("bn_0", V_LIM)
                blocked = False
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            for v in ids:
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_LANEPOSITION, c.VAR_SPEED,
                                                c.VAR_ROAD_ID))
                    sub.add(v)
                    entry_t[v] = t
            if k % sample_every:
                continue
            res = traci.vehicle.getAllSubscriptionResults()
            for v, val in res.items():
                road = str(val.get(c.VAR_ROAD_ID, ""))
                # 车辆实际路径是 in → :n3_1（交叉口内部边）→ mid，
                # 不是 in → mid 直接跳变。所以判「首次出现在 mid 上」，不判前一条边是什么。
                if road == "mid" and v not in cross_t:
                    cross_t[v] = t
                    cross_state[v] = (road, round(val.get(c.VAR_LANEPOSITION, -1), 1),
                                      round(val.get(c.VAR_SPEED, -1), 2))
                prev_road[v] = road
    finally:
        traci.close()

    # tripinfo：实际发车、departDelay、到达、路程
    trips = {}
    tp = OUT / "trip_base.xml"
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            trips[tri.get("id")] = {
                "depart_actual": round(float(tri.get("depart")), 2),
                "depart_delay": round(float(tri.get("departDelay", "0")), 2),
                "arrival": round(float(tri.get("arrival", "nan")), 2),
                "duration": round(float(tri.get("duration", "nan")), 2),
                "route_len": round(float(tri.get("routeLength", "nan")), 1),
            }

    # 对账
    n_inserted = len(entry_t)
    n_cross = len(cross_t)
    n_arrived = len(trips)
    delays = [d["depart_delay"] for d in trips.values()]
    print(f"计划 {n_planned} 辆 / 实际插入 {n_inserted} / 过线 {n_cross} / 到达 {n_arrived}",
          flush=True)
    if delays:
        print(f"departDelay: 中位 {np.median(delays):.1f} s, p90 {np.percentile(delays,90):.1f} s",
              flush=True)

    # 每 60 s 入口流量对账
    print(f"\n{'时段':>10} {'计划':>6} {'实际':>6} {'偏差':>7}")
    bins_plan: dict[int, int] = defaultdict(int)
    bins_act: dict[int, int] = defaultdict(int)
    for i in range(n_planned):
        bins_plan[int(i * period // 60)] += 1
    for v, t in entry_t.items():
        bins_act[int(t // 60)] += 1
    bad = 0
    for b in sorted(bins_plan):
        p, a = bins_plan[b], bins_act.get(b, 0)
        dev = (a - p) / p if p else 0.0
        if abs(dev) > 0.10:
            bad += 1
        if b < 12 or abs(dev) > 0.10:
            print(f"{b*60:>5d}–{b*60+60:<4d} {p:>6} {a:>6} {dev*100:>6.1f}%")
    print(f"  偏差 >10% 的时段数: {bad}", flush=True)

    # 候选名单
    roster = []
    for v, tc in cross_t.items():
        info = trips.get(v, {})
        roster.append({
            "veh_id": v,
            "cross_t": tc,
            "event_age_s": (None if tc < T0 else round(tc - T0, 2)),
            "road": cross_state[v][0], "pos": cross_state[v][1],
            "speed": cross_state[v][2],
            "depart_actual": info.get("depart_actual"),
            "depart_delay": info.get("depart_delay"),
            "arrival": info.get("arrival"),
            "verdict": "arrived" if v in trips else "no_arrival",
        })
    roster.sort(key=lambda r: r["cross_t"])
    (OUT / "roster.json").write_text(json.dumps(
        {"n_planned": n_planned, "n_inserted": n_inserted, "n_crossed": n_cross,
         "n_arrived": n_arrived,
         "depart_delay_median": (None if not delays else round(float(np.median(delays)), 2)),
         "depart_delay_p90": (None if not delays else round(float(np.percentile(delays, 90)), 2)),
         "timeslot_violations": bad, "roster": roster},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== 对照预测（R08）===")
    print(f"  计划车数: 预测 747  实测 {n_planned}  {'✅' if abs(n_planned-747)<=7 else '❌'}")
    print(f"  插入率:   预测 ≥99%  实测 {n_inserted/n_planned*100:.1f}%  "
          f"{'✅' if n_inserted/n_planned >= 0.99 else '❌'}")
    print(f"  过线车数: 预测 700–745  实测 {n_cross}  {'✅' if 700 <= n_cross <= 745 else '❌'}")
    print(f"  到达车数: 预测 650–730  实测 {n_arrived}  {'✅' if 650 <= n_arrived <= 730 else '❌'}")
    if delays:
        print(f"  departDelay 中位: 预测 <10 s  实测 {np.median(delays):.1f} s  "
              f"{'✅' if np.median(delays) < 10 else '❌'}")
    print(f"  时段偏差>10% 的时段数: 预测 0  实测 {bad}  {'✅' if bad == 0 else '❌'}")
    print(f"\nwritten: {OUT/'roster.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
