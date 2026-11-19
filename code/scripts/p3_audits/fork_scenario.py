"""0.0.5 第 1–2 步：分岔路网 + 瓶颈队列形成/回溢/消散验证。

预注册见 docs/tasks/0.0.5_预注册_分岔场景.md
本脚本只做两件事：
  1. 建分岔路网，验证三档绕行代价（+30 / +50 / +60 秒）的自由流通行时间
  2. 在主路 4900–5100 m 处施加「持续 D 秒的通行能力下降」，验证队列能否形成、
     是否向 3000 m 的改道点回溢、以及能否按时消散

不做消息臂、不做决策规则——那些是第 3–5 步。

用法：python fork_scenario.py --tier 50 --demand 1600 --block 180
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_fork"
NETCONVERT = str(Path(SUMO).parent / "netconvert.exe")

STEP = 0.1
V_LIM = 30.0
FORK_X = 3000.0
MERGE_X = 7000.0
BN_LO, BN_HI = 4900.0, 5100.0
MAIN_LEN = 8000.0
VEH_LEN = 5.0


def build_net(tier_s: float, work: Path) -> Path:
    """tier_s = 绕行相对主路多出的时间（秒）。绕行路长 = 4000 + tier_s*30 米。"""
    bypass_len = 4000.0 + tier_s * V_LIM
    nodes = f"""<nodes>
        <node id="n0" x="0" y="0" type="dead_end"/>
        <node id="n3" x="{FORK_X}" y="0" type="priority"/>
        <node id="n49" x="{BN_LO}" y="0" type="priority"/>
        <node id="n51" x="{BN_HI}" y="0" type="priority"/>
        <node id="n7" x="{MERGE_X}" y="0" type="priority"/>
        <node id="n8" x="{MAIN_LEN}" y="0" type="dead_end"/>
    </nodes>"""
    edges = f"""<edges>
        <edge id="in"  from="n0"  to="n3"  numLanes="1" speed="{V_LIM}" priority="2"/>
        <edge id="mid" from="n3"  to="n49" numLanes="1" speed="{V_LIM}" priority="2"/>
        <edge id="bn"  from="n49" to="n51" numLanes="1" speed="{V_LIM}" priority="2"/>
        <edge id="out" from="n51" to="n7"  numLanes="1" speed="{V_LIM}" priority="2"/>
        <edge id="tail" from="n7" to="n8"  numLanes="1" speed="{V_LIM}" priority="2"/>
        <edge id="bypass" from="n3" to="n7" numLanes="1" speed="{V_LIM}" priority="1" length="{bypass_len:.1f}"/>
    </edges>"""
    conns = """<connections>
        <connection from="in"  to="mid"/>
        <connection from="in"  to="bypass"/>
        <connection from="mid" to="bn"/>
        <connection from="bn"  to="out"/>
        <connection from="out" to="tail"/>
        <connection from="bypass" to="tail"/>
    </connections>"""
    work.mkdir(parents=True, exist_ok=True)
    (work / "n.nod.xml").write_text(nodes, encoding="utf-8")
    (work / "e.edg.xml").write_text(edges, encoding="utf-8")
    (work / "c.con.xml").write_text(conns, encoding="utf-8")
    net = work / "net.net.xml"
    r = subprocess.run([NETCONVERT, "-n", str(work / "n.nod.xml"),
                        "-e", str(work / "e.edg.xml"), "-x", str(work / "c.con.xml"),
                        "-o", str(net), "--no-turnarounds", "true",
                        "--junctions.corner-detail", "0"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if not net.exists():
        raise RuntimeError("netconvert 失败:\n" + (r.stdout or "") + (r.stderr or ""))
    return net


def run(net: Path, work: Path, tier_s: float, demand: float, block_s: float,
        t0: float, seed: int) -> dict:
    period = 3600.0 / demand
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    rou = (f'<routes>{vt}'
           f'<route id="main" edges="in mid bn out tail"/>'
           f'<route id="byp"  edges="in bypass tail"/>'
           f'<flow id="f" type="c" route="main" begin="0" end="{t0 + block_s + 900:.0f}"'
           f' period="{period:.3f}" departSpeed="max" departLane="0"/></routes>')
    (work / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{t0 + block_s + 900:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    series = []
    sub = set()
    in_count = 0
    arrived = 0
    last_in_vid = None
    blocked = False
    t_end = t0 + block_s + 900.0
    try:
        for k in range(int(t_end / STEP)):
            t = k * STEP
            # 瓶颈：在 [t0, t0+block) 内把限速压到 4 m/s（等效容量下降）
            if not blocked and t >= t0:
                traci.lane.setMaxSpeed("bn_0", 4.0)
                blocked = True
            if blocked and t >= t0 + block_s:
                traci.lane.setMaxSpeed("bn_0", V_LIM)
                blocked = False
            traci.simulationStep()
            present = traci.vehicle.getIDList()
            arrived += traci.simulation.getArrivedNumber()
            for v in present:
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_LANEPOSITION, c.VAR_SPEED,
                                                c.VAR_ROAD_ID))
                    sub.add(v)
            if k % 10 == 0:
                res = traci.vehicle.getAllSubscriptionResults()
                # 主路上车辆
                main_v = [(v, val) for v, val in res.items()
                          if str(val.get(c.VAR_ROAD_ID, "")).startswith(("mid", "bn", "out"))]
                bypass_v = [v for v, val in res.items()
                            if str(val.get(c.VAR_ROAD_ID, "")).startswith("bypass")]
                # 主路队尾位置（最靠上游的、速度<5 m/s 的车在 mid 上的位置）
                slow = [(val.get(c.VAR_LANEPOSITION, 0.0), v) for v, val in main_v
                        if val.get(c.VAR_ROAD_ID) == "mid"
                        and val.get(c.VAR_SPEED, 99) < 5.0]
                tail_x = (FORK_X + min(p for p, _ in slow)) if slow else None
                speeds = [val.get(c.VAR_SPEED, 0.0) for _, val in main_v]
                series.append({"t": round(t, 1), "n_main": len(main_v),
                               "n_bypass": len(bypass_v),
                               "mean_v_main": round(float(np.mean(speeds)), 2) if speeds else None,
                               "n_slow_main": len(slow),
                               "queue_tail_x": (None if tail_x is None else round(tail_x, 0))})
                in_count = max(in_count, len(sub))
    finally:
        traci.close()

    s = series
    q_tail = [r["queue_tail_x"] for r in s if r["queue_tail_x"] is not None]
    n_slow = [r["n_slow_main"] for r in s]
    return {"tier_s": tier_s, "demand": demand, "block_s": block_s, "t0": t0,
            "n_veh_total": in_count, "arrived": arrived,
            "max_slow_main": int(max(n_slow)) if n_slow else 0,
            "min_queue_tail_x": (min(q_tail) if q_tail else None),
            "queue_reached_fork": bool(q_tail and min(q_tail) <= FORK_X + 50),
            "series": s}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=float, default=50.0, help="绕行多出的秒数")
    ap.add_argument("--demand", type=float, default=1600.0, help="辆/小时")
    ap.add_argument("--block", type=float, default=180.0, help="瓶颈持续秒数")
    ap.add_argument("--t0", type=float, default=600.0, help="瓶颈开始时刻")
    ap.add_argument("--seed", type=int, default=20261120)
    ap.add_argument("--freeflow-only", action="store_true", help="只验自由流，不加瓶颈")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    tier_tag = f"t{int(args.tier)}"
    work = OUT / f"_net_{tier_tag}"
    net = build_net(args.tier, work)
    print(f"路网已建：绕行 {4000 + args.tier*V_LIM:.0f} m "
          f"（主路对应段 4000 m，多 {args.tier:.0f} 秒）", flush=True)

    if args.freeflow_only:
        netinfo = subprocess.run([str(Path(SUMO).parent / "netconvert.exe"), "--sumo-net-file",
                                  str(net)], capture_output=True, text=True)
        print("自由流理论值：主路 3000→7000 段 = 133.3 s；"
              f"绕行 = {(4000 + args.tier*V_LIM)/V_LIM:.1f} s", flush=True)
        return 0

    r = run(net, work, args.tier, args.demand, args.block, args.t0, args.seed)
    s = r.pop("series")
    print(f"\n三档自由流（主路 3000→7000 = 133.3 s）：", flush=True)
    for tier in [30, 50, 60]:
        print(f"  +{tier} 秒档 → 绕行路 {4000 + tier*V_LIM:.0f} m → {(4000 + tier*V_LIM)/V_LIM:.1f} s",
              flush=True)
    print(f"\n本轮：+{args.tier:.0f} 秒档，需求 {args.demand:.0f} 辆/时，"
          f"瓶颈 {args.t0:.0f}–{args.t0+args.block:.0f} s（限速压到 4 m/s）", flush=True)
    print(f"  总车辆 {r['n_veh_total']}，到达 {r['arrived']}", flush=True)
    print(f"  主路低速车峰值 {r['max_slow_main']} 辆", flush=True)
    print(f"  队尾最上游位置 {r['min_queue_tail_x']} m（改道点在 {FORK_X:.0f} m）", flush=True)
    print(f"  队尾是否回溢到改道点：{'是' if r['queue_reached_fork'] else '否'}", flush=True)

    print(f"\n时间序列抽样（每 30 s）：")
    print(f"{'t':>7} {'主路车':>7} {'绕行车':>7} {'主路均速':>9} {'低速车':>7} {'队尾x':>8}")
    for row in s:
        if abs(row["t"] % 30) < 0.06:
            print(f"{row['t']:>7.0f} {row['n_main']:>7} {row['n_bypass']:>7} "
                  f"{str(row['mean_v_main']):>9} {row['n_slow_main']:>7} "
                  f"{str(row['queue_tail_x']):>8}")

    (OUT / f"fork_{tier_tag}_d{int(args.demand)}_b{int(args.block)}.json").write_text(
        json.dumps({"summary": r, "series": s}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
