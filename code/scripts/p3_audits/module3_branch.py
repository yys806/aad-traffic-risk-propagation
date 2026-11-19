"""0.0.8 模块 3：单车分支执行（先只做 1 辆车）。

依据 GPT 第五十五轮模块 3：
  每辆样本车从同一 S_i 独立开两支，只改变目标车剩余路线；
  与基线路线相同的那一支须复现该车的基线到达时间；
  交换两支执行顺序，结果须一致；不可达/未到达/被移除/瞬移要单列。

【先想清的一件事（R08 第 1 条）】
决策时刻 **不能**取「车已经出现在 mid 上」那一刻——那时它已经过了岔口，
改路无效（模块 0 已证：最晚可到距岔口 10 m）。
所以本脚本把决策时刻定义为：
  **最后一次采样到「车还在 in 边上、且位置 ≥ 2900 m」的那一步。**
此时它距岔口 98.5 m 以内，模块 0 已证明此处改路有效。

【跑之前写死的预测】
- 主路支：该车到达时间必须与基线**逐位相同**（确定性重放已证偏差为 0）
- 绕行支：到达时间比主路支晚，晚的量 ≈ 绕行代价（自由流 55.7 s）+ 排队差
- 目标车之外的其他车辆：两支之间**不受影响**（只有目标车改路）
- 两支都到达同一终点（tail 边结束），不发生瞬移
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_module3"

STEP = 0.1
V_LIM = 30.0
DEMAND = 1600.0
T_END = 1680.0
T0 = 600.0
BLOCK = 180.0
DECIDE_POS = 2900.0     # in 边上距岔口 98.5 m 处定义为决策位置

# 🔴 绕行相对主路的**自由流**代价。必须是**当前路网**实测值。
# 单车道汇合时代价是 55.7 s（222.4 − 166.7）；
# 改成两车道汇合后重新实测为 50.1 s（219.9 − 169.8）。用错会让每个 Y 偏 5.6 s。
FREE_PENALTY = 50.1


def build_rou(work: Path) -> int:
    period = 3600.0 / DEMAND
    n = int(T_END / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r_base.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>'
        f'<route id="detour" edges="in bypass tail"/>{vehs}</routes>', encoding="utf-8")
    return n


def write_cfg(work: Path, tag: str, trip: str) -> Path:
    cfg = work / f"run_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_base.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="{trip}"/></output></configuration>',
        encoding="utf-8")
    return cfg


def run_branch(work: Path, tag: str, target: str | None, branch: str) -> dict:
    """跑一支。target 为 None 表示基线（不改任何车）。"""
    trip = f"t_{tag}.xml"
    cfg = write_cfg(work, tag, trip)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    sub = set()
    decide_t = decide_state = None
    switched = False
    roads_of_target = []
    trace = []
    last_trace_t = None
    target_arrival = None
    n_switched_to_detour = 0
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
            if target is not None and target in ids:
                if target not in sub:
                    traci.vehicle.subscribe(target, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                     c.VAR_SPEED))
                    sub.add(target)
                r = traci.vehicle.getSubscriptionResults(target)
                if r is not None:
                    road = str(r.get(c.VAR_ROAD_ID, ""))
                    pos = float(r.get(c.VAR_LANEPOSITION, -1))
                    spd = float(r.get(c.VAR_SPEED, -1))
                    if road not in roads_of_target:
                        roads_of_target.append(road)
                    # 决策时刻：最后一次还在 in 上且 pos ≥ DECIDE_POS
                    if last_trace_t is None or t - last_trace_t >= 10:
                        trace.append({"t": t, "road": road, "pos": round(pos, 1),
                                      "v": round(spd, 2)})
                        last_trace_t = t
                    if road == "in" and pos >= DECIDE_POS:
                        decide_t = t
                        decide_state = (road, round(pos, 1), round(spd, 2))
                        if branch == "detour" and not switched:
                            traci.vehicle.setRoute(target, ["in", "bypass", "tail"])
                            switched = True
                            n_switched_to_detour += 1
    finally:
        traci.close()

    trips = {}
    tp = work / trip
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            trips[tri.get("id")] = {
                "depart": round(float(tri.get("depart")), 2),
                "arrival": round(float(tri.get("arrival", "nan")), 2),
                "route_len": round(float(tri.get("routeLength", "nan")), 1),
                "depart_delay": round(float(tri.get("departDelay", "0")), 2),
            }
    if target and target in trips:
        target_arrival = trips[target]["arrival"]
    return {"tag": tag, "branch": branch, "decide_t": decide_t,
            "decide_state": decide_state, "switched": switched,
            "roads_of_target": roads_of_target, "trace": trace,
            "target_trip": trips.get(target) if target else None,
            "target_arrival": target_arrival, "n_arrived_total": len(trips)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)
    n = build_rou(OUT)
    print(f"基线：计划 {n} 辆", flush=True)

    base = run_branch(OUT, "base", None, "main")
    print(f"  基线到达 {base['n_arrived_total']} 辆", flush=True)

    # 选一辆「决策时刻落在堵塞期内」的车作为本轮的 1 个样本
    # 先跑一次带订阅的基线，拿到所有车的决策时刻，再挑
    print("\n扫描所有车的决策时刻（只订阅、不改路）…", flush=True)
    cfg = write_cfg(OUT, "scan", "t_scan.xml")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    sub = set()
    decide: dict[str, tuple] = {}
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
            if k % 2:
                continue
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED))
                    sub.add(v)
            res = traci.vehicle.getAllSubscriptionResults()
            for v, val in res.items():
                road = str(val.get(c.VAR_ROAD_ID, ""))
                pos = float(val.get(c.VAR_LANEPOSITION, -1))
                if road == "in" and pos >= DECIDE_POS:
                    decide[v] = (t, round(pos, 1), round(float(val.get(c.VAR_SPEED, -1)), 2))
    finally:
        traci.close()

    in_block = [(v, s) for v, s in decide.items() if T0 <= s[0] <= T0 + BLOCK]
    in_block.sort(key=lambda z: z[1][0])
    if not in_block:
        print("没有决策时刻落在堵塞期内的车，无法选样本")
        return 1
    target, (t_i, pos_i, spd_i) = in_block[len(in_block) // 2]
    print(f"  选中样本车 {target}：决策时刻 {t_i} s（堵塞开始后 {t_i - T0:.1f} s），"
          f"位置 {pos_i} m，速度 {spd_i} m/s", flush=True)
    print(f"  堵塞期内决策的车共 {len(in_block)} 辆", flush=True)

    # 三支：基线（不改）、主路（显式不改）、绕行（改）
    r_main = run_branch(OUT, f"main_{target}", target, "main")
    r_det = run_branch(OUT, f"detour_{target}", target, "detour")
    # 交换顺序：先绕行后主路，验证顺序无关
    r_det2 = run_branch(OUT, f"detour2_{target}", target, "detour")
    r_main2 = run_branch(OUT, f"main2_{target}", target, "main")

    print("\n=== 三支结果 ===")
    for tag, r in [("主路支", r_main), ("绕行支", r_det),
                   ("绕行支(换序)", r_det2), ("主路支(换序)", r_main2)]:
        tp = r["target_trip"] or {}
        print(f"  {tag:>12}: 决策时刻={r['decide_t']} 改路={r['switched']} "
              f"到达={tp.get('arrival')} 路程={tp.get('route_len')} "
              f"经过={r['roads_of_target']}")

    print("\n=== 对照预测（R08）===")
    a_main = (r_main["target_trip"] or {}).get("arrival")
    a_main2 = (r_main2["target_trip"] or {}).get("arrival")
    a_det = (r_det["target_trip"] or {}).get("arrival")
    a_det2 = (r_det2["target_trip"] or {}).get("arrival")
    print(f"  主路支与换序后主路支到达相同: {a_main} vs {a_main2} "
          f"{'✅' if a_main == a_main2 else '❌'}")
    print(f"  绕行支与换序后绕行支到达相同: {a_det} vs {a_det2} "
          f"{'✅' if a_det == a_det2 else '❌'}")
    print(f"  绕行支是否真的走了 bypass: {'bypass' in r_det['roads_of_target']} "
          f"{'✅' if 'bypass' in r_det['roads_of_target'] else '❌'}")
    print(f"  主路支是否走了 mid: {'mid' in r_main['roads_of_target']} "
          f"{'✅' if 'mid' in r_main['roads_of_target'] else '❌'}")
    if a_main and a_det:
        print(f"  T主路 = {a_main - t_i:.1f} s, T绕行 = {a_det - t_i:.1f} s, "
              f"Y = {a_main - a_det + FREE_PENALTY:.1f} s")

    (OUT / "module3.json").write_text(json.dumps(
        {"target": target, "decide_t": t_i, "decide_state": [pos_i, spd_i],
         "n_decide_in_block": len(in_block),
         "main": r_main, "detour": r_det, "detour2": r_det2, "main2": r_main2},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'module3.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
