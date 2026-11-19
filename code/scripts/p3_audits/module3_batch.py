"""0.1.0 模块 3 批处理：88 辆全跑（先 6–8 辆验收）。

依据 GPT 第五十七轮：
  ① 三窗口分开：观察 [0,1680) / 入组 [600,780) / 随访 决策步→到达
  ② 88 辆全跑，先 6–8 辆批处理验收，通过后直接计入，不重跑
  ③ 每次重放只允许一辆目标车改路
  ④ 三项硬门槛：主路支对拍基线 / 汇合等待写进日志 / 其他车扰动按车号配对

【先想清的规格（R08）】

入组：在**基线**里首次有效跨过 3000 m 的时刻落在 [600,780] 的车，冻结 ID 与决策步。
      不按分支结果重新入组。

决策步：最后一次采样到「车还在 in 上、位置 ≥2900」的那一步。
      （模块 0 已证：距岔口 10 m 改路仍有效；取 2900 留余量）

每车三次仿真：
  baseline —— 不改任何车（全场景共享一次，不重复跑）
  main     —— 对目标车显式「不改」，用于对拍基线
  detour   —— 在决策步 setRoute 到 bypass

【跑之前写死的预测】
1. 门槛 1：main 支与 baseline 的**整车队 tripinfo 逐辆一致**（确定性已证偏差 0）。
2. 门槛 2：detour 支目标车的汇合等待 < 5 s（双车道修复后实测约 2 s）。
3. 门槛 3：两支架构间其他车的到达时差，中位数应接近 0；
   但**允许非零**——目标车改路会占用绕过路线、改变下游车流。
   只有「差异出现在决策步之前」或「传送/异常退出」才判为仿真问题。
   本脚本用 --time-to-teleport -1，传送在结构上不可能。
4. detour 支的 T_绕 应接近自由流 219.9 s（±5%）。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_module3_batch"

STEP = 0.1
V_LIM = 30.0
DEMAND = 1600.0
T_END = 1680.0
T0 = 600.0
BLOCK = 180.0
DECIDE_POS = 2900.0
ENROLL_LO, ENROLL_HI = 600.0, 780.0
FORK = 3000.0
FREE_MAIN = 169.8
FREE_DET = 219.9
FREE_PENALTY = FREE_DET - FREE_MAIN      # 50.1，必须用当前路网实测值


def build_rou(work: Path) -> int:
    period = 3600.0 / DEMAND
    n = int(T_END / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r_batch.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>'
        f'<route id="detour" edges="in bypass tail"/>{vehs}</routes>', encoding="utf-8")
    return n


def write_cfg(work: Path, tag: str, trip: str) -> Path:
    cfg = work / f"run_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_batch.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="{trip}"/></output></configuration>',
        encoding="utf-8")
    return cfg


def run_one(work: Path, tag: str, target: str | None, mode: str,
            watch: list[str] | None = None) -> dict:
    """mode: baseline / main / detour。watch 里的车记录决策步与轨迹摘要。"""
    trip = f"t_{tag}.xml"
    cfg = write_cfg(work, tag, trip)
    watch = watch or []
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    sub = set()
    decide: dict[str, dict] = {}
    byp_end: dict[str, float] = {}
    enter_tail: dict[str, float] = {}
    switched = False
    roads: dict[str, list] = {}
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
            # 只订阅要记录的车：基线要全车队（watch 为空 = 全订），
            # 主路/绕行支只要目标车。全订会让 16 次重放拖到近一小时。
            if watch:
                for v in watch:
                    if v in sub:
                        continue
                    try:
                        traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                    c.VAR_SPEED))
                        sub.add(v)
                    except Exception:
                        pass
            else:
                for v in traci.vehicle.getIDList():
                    if v not in sub:
                        traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                    c.VAR_SPEED))
                        sub.add(v)
            if k % 2:
                continue
            res = traci.vehicle.getAllSubscriptionResults()
            for v, val in res.items():
                if watch and v not in watch:
                    continue
                road = str(val.get(c.VAR_ROAD_ID, ""))
                pos = float(val.get(c.VAR_LANEPOSITION, -1))
                spd = float(val.get(c.VAR_SPEED, -1))
                if v not in roads:
                    roads[v] = []
                if not roads[v] or roads[v][-1] != road:
                    roads[v].append(road)
                if road == "in" and pos >= DECIDE_POS:
                    decide[v] = {"t": t, "pos": round(pos, 1), "v": round(spd, 2)}
                    if mode == "detour" and v == target and not switched:
                        traci.vehicle.setRoute(v, ["in", "bypass", "tail"])
                        switched = True
                if road == "bypass" and pos > 5400:
                    byp_end.setdefault(v, t)
                if road == "tail" and v in byp_end and v not in enter_tail:
                    enter_tail[v] = t
    finally:
        traci.close()

    trips = {}
    tp = work / trip
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            trips[tri.get("id")] = round(float(tri.get("arrival", "nan")), 2)

    info = {"tag": tag, "mode": mode, "n_arrived": len(trips), "trips": trips,
            "decide": decide, "roads": roads, "switched": switched}
    if target:
        info["target"] = {
            "id": target,
            "decide": decide.get(target),
            "roads": roads.get(target, []),
            "bypass_end_t": byp_end.get(target),
            "enter_tail_t": enter_tail.get(target),
            "merge_wait": (round(enter_tail[target] - byp_end[target], 1)
                           if target in byp_end and target in enter_tail else None),
            "arrival": trips.get(target),        # None = 截尾
            "censored": target not in trips,
        }
    return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8, help="验收批车辆数（0=全跑 88 辆）")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)
    n_plan = build_rou(OUT)
    print(f"计划车辆 {n_plan}", flush=True)

    print("\n[1/4] 跑基线…", flush=True)
    base = run_one(OUT, "baseline", None, "baseline")
    print(f"  基线到达 {base['n_arrived']} 辆，扫到决策步 {len(base['decide'])} 辆", flush=True)

    enrolled = sorted(
        [(v, d) for v, d in base["decide"].items() if ENROLL_LO <= d["t"] <= ENROLL_HI],
        key=lambda z: z[1]["t"])
    print(f"  入组窗 [{ENROLL_LO:.0f},{ENROLL_HI:.0f}] 内决策的车：{len(enrolled)} 辆", flush=True)
    if not enrolled:
        print("  入组为空，停")
        return 1

    # 选验收批：最早 / 最晚 / 中位 / 均匀铺开
    if args.n == 0 or args.n >= len(enrolled):
        batch = [v for v, _ in enrolled]
    else:
        m = len(enrolled)
        idx = sorted({0, m - 1, m // 2} | {
            round(i * (m - 1) / max(1, args.n - 1)) for i in range(args.n)})
        idx = idx[:args.n]
        batch = [enrolled[i][0] for i in idx]
    print(f"  验收批 {len(batch)} 辆：{batch}", flush=True)

    records = []
    print(f"\n[2/4] 逐车跑 main / detour（{2*len(batch)} 次重放）…", flush=True)
    for j, tgt in enumerate(batch, 1):
        rm = run_one(OUT, f"m_{tgt}", tgt, "main", watch=[tgt])
        rd = run_one(OUT, f"d_{tgt}", tgt, "detour", watch=[tgt])
        records.append({"target": tgt, "main": rm, "detour": rd})
        tm = rm["target"]
        print(f"  [{j}/{len(batch)}] {tgt}: 决策 {tm['decide']['t'] if tm['decide'] else None} s；"
              f"main 到达 {tm['arrival']}；detour 到达 {rd['target']['arrival']}；"
              f"汇合等待 {rd['target']['merge_wait']} s", flush=True)

    print("\n[3/4] 门槛 1：main 支对拍基线（整车队逐辆）", flush=True)
    bad1 = []
    for rec in records:
        tgt = rec["target"]
        m, b = rec["main"]["trips"], base["trips"]
        diff = [v for v in set(m) | set(b) if m.get(v) != b.get(v)]
        if diff:
            bad1.append((tgt, len(diff), diff[:5]))
    print(f"  整车队 tripinfo 与基线不一致的车次：{len(bad1)} / {len(records)}"
          f"  {'✅' if not bad1 else '❌'}", flush=True)
    for x in bad1[:5]:
        print(f"    车 {x[0]}：{x[1]} 辆到达时刻不同，例 {x[2]}", flush=True)

    print("\n[4/4] 门槛 2/3 + Y 汇总", flush=True)
    summary = []
    for rec in records:
        tgt = rec["target"]
        rt, dt = rec["main"]["target"], rec["detour"]["target"]
        a_m, a_d = rt["arrival"], dt["arrival"]
        t_i = (rt["decide"] or {}).get("t")
        Y = T_m = T_d = None
        if a_m is not None and a_d is not None and t_i is not None:
            T_m, T_d = round(a_m - t_i, 1), round(a_d - t_i, 1)
            Y = round(T_m - T_d + FREE_PENALTY, 1)
        # 门槛 3：两支架构间其他车的到达时差
        mm, dd = rec["main"]["trips"], rec["detour"]["trips"]
        common = [v for v in set(mm) & set(dd) if v != tgt]
        deltas = [dd[v] - mm[v] for v in common]
        only_m = sorted(set(mm) - set(dd) - {tgt})
        only_d = sorted(set(dd) - set(mm) - {tgt})
        s = {
            "target": tgt, "decide_t": t_i,
            "arrival_main": a_m, "arrival_detour": a_d,
            "T_main": T_m, "T_detour": T_d, "Y": Y,
            "censored_main": rt["censored"], "censored_detour": dt["censored"],
            "merge_wait": dt["merge_wait"],
            "took_bypass": "bypass" in (dt["roads"] or []),
            "other_n": len(deltas),
            "other_median": round(statistics.median(deltas), 2) if deltas else None,
            "other_p95": (round(sorted(deltas)[int(0.95 * (len(deltas) - 1))], 2)
                          if deltas else None),
            "other_max_abs": round(max(abs(x) for x in deltas), 2) if deltas else None,
            "only_in_main": len(only_m), "only_in_detour": len(only_d),
        }
        summary.append(s)

    print(f"\n{'车号':>7} {'决策s':>7} {'主到达':>8} {'绕到达':>8} {'T主':>7} {'T绕':>7} "
          f"{'Y':>7} {'等待':>6} {'他车中位':>8} {'p95':>7} {'最大|Δ|':>8}")
    for s in summary:
        print(f"{s['target']:>7} {str(s['decide_t']):>7} {str(s['arrival_main']):>8} "
              f"{str(s['arrival_detour']):>8} {str(s['T_main']):>7} {str(s['T_detour']):>7} "
              f"{str(s['Y']):>7} {str(s['merge_wait']):>6} "
              f"{str(s['other_median']):>8} {str(s['other_p95']):>7} {str(s['other_max_abs']):>8}")

    ok_mw = [s for s in summary if s["merge_wait"] is not None and s["merge_wait"] < 5]
    print(f"\n汇合等待 <5 s: {len(ok_mw)} / {len(summary)} "
          f"{'✅' if len(ok_mw) == len(summary) else '⚠️'}")
    ok_by = [s for s in summary if s["took_bypass"]]
    print(f"确实走 bypass: {len(ok_by)} / {len(summary)} "
          f"{'✅' if len(ok_by) == len(summary) else '❌'}")
    ys = [s["Y"] for s in summary if s["Y"] is not None]
    if ys:
        print(f"Y: n={len(ys)} 中位 {statistics.median(ys):.1f} s  范围 [{min(ys):.1f}, {max(ys):.1f}]")
    cens = [s for s in summary if s["censored_main"] or s["censored_detour"]]
    print(f"截尾车次: {len(cens)}（{[(s['target'], s['censored_main'], s['censored_detour']) for s in cens]}）")

    (OUT / "batch.json").write_text(json.dumps(
        {"n_plan": n_plan, "enrolled": len(enrolled),
         "batch": batch, "summary": summary,
         "gate1_tripinfo_mismatch": len(bad1),
         "base_arrived": base["n_arrived"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'batch.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
