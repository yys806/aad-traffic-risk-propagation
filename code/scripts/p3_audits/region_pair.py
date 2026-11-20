"""0.2.16 区域 τ 异质 2×2 配对实验（GPT 第九十四轮 Q4 定稿设计）

【设计：2×2】每个种子跑四臂
    H_brake   均质 τ=1.584  + 源车刹车至停
    D_brake   异质 τ 抽样    + 源车刹车至停
    H_nobrake 均质 τ=1.584  + 不刹车（对照）
    D_nobrake 异质 τ 抽样    + 不刹车（对照）

【为什么加无刹车臂】GPT 原话：
  「只比较有刹车时异质组和均质组的风险，无法区分『异质性提高背景风险』
    与『异质性放大刹车扰动风险』。」
  风险增量 ΔRisk = Risk(brake) − Risk(nobrake)，再比较 ΔRisk 在两种 τ 配置间是否不同。

【空间锚定】GPT 第九十四轮 Q3：
  「指定源车首次越过上游 30 m 触发线时开始施刹」
  触发线 = mid 上距 bn 入口 30 m，即 lanePosition = 1868.5 m
  记录实际触发位置、t0、速度、车道
  **不再用「t=600 s 时最近者」**

【峰值口径】GPT 第九十四轮：
  「不建议把 v≥5 且 |a|≤1.0 作为安全风险峰值的主分析筛选」
  → 主分析用**全帧峰值**；另报 NGSIM 合格帧峰值作可比性分析

用法：python region_pair.py --seeds 20261101 20261102 --tag pilot
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net, V_LIM, STEP  # noqa: E402

ROOT = Path(r"D:/shen/TJU/AAD")
OUT = ROOT / "code/outputs/analysis/P3_region_pair"
TAU_NPY = ROOT / "code/outputs/analysis/P3_tau_dist/tau_samples.npy"
SPD_NPY = ROOT / "code/outputs/analysis/P3_tau_dist/speed_samples.npy"

MID_LEN, BN_LEN, OUT_LEN = 1898.5, 200.0, 1898.5
OFF = {"mid": 0.0, "bn": MID_LEN, "out": MID_LEN + BN_LEN,
       "tail": MID_LEN + BN_LEN + OUT_LEN}

TRIGGER_POS = MID_LEN - 30.0     # 距 bn 入口 30 m
ARM_START = 300.0                # 起跑后先让车流演化 300 s 再等触发
TRIGGER_WAIT = 300.0             # 等待触发线上限
OBS_H = 600.0
DEMAND = 1600.0
SRC_DECEL = 9.0
DRAC_THR = 3.4
MERGE_FRAMES = 3
TAU_FIXED = 1.584
V_MIN = 5.0
ACC_MAX = 1.0
T_END = ARM_START + TRIGGER_WAIT + OBS_H + 150.0
TAU_LAYER = "mid"                # 54–80 km/h，区域场景实际速度层


def tau_pool() -> np.ndarray:
    tau = np.load(TAU_NPY)
    spd = np.load(SPD_NPY)
    m = (spd >= 15.0) & (spd < 22.2)
    return tau[m]


def build_arm(work: Path, seed: int, hetero: bool, n: int) -> Path:
    period = 3600.0 / DEMAND
    rng = np.random.default_rng(seed)
    if hetero:
        taus = rng.choice(tau_pool(), size=n, replace=True)
    else:
        taus = np.full(n, TAU_FIXED)
    types, seen = [], set()
    for tv in taus:
        key = round(float(tv), 3)
        if key in seen:
            continue
        seen.add(key)
        types.append(
            f'<vType id="t{key}" carFollowModel="Krauss" accel="2.6" decel="4.5"'
            f' sigma="0" tau="{key}" length="5" minGap="2.5" maxSpeed="{V_LIM}"'
            f' speedFactor="1" lcKeepRight="0"/>')
    vehs = [f'<vehicle id="V{i:04d}" type="t{round(float(taus[i]), 3)}" route="main"'
            f' depart="{i*period:.3f}" departSpeed="max" departLane="0"/>'
            for i in range(n)]
    p = work / "r.rou.xml"
    p.write_text(f'<routes>{"".join(types)}<route id="main" edges="in mid bn out tail"/>'
                 f'{"".join(vehs)}</routes>', encoding="utf-8")
    return p


def build_cfg(work: Path, seed: int) -> Path:
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def run_arm(seed: int, hetero: bool, brake: bool) -> dict:
    tag = f"{'D' if hetero else 'H'}_{'brake' if brake else 'nobrake'}"
    work = OUT / f"{seed}_{tag}"
    work.mkdir(parents=True, exist_ok=True)
    build_net(50.0, work)
    n = int(T_END / (3600.0 / DEMAND)) + 50
    build_arm(work, seed, hetero, n)
    cfg = build_cfg(work, seed)

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    sub: set[str] = set()
    src_id = None
    t0 = None
    src_pos = None
    src_v = None
    stopped = False
    triggered = False
    active: dict[str, dict] = {}
    events: list[dict] = []
    peak_all = 0.0
    peak_all_at = None
    peak_qual = 0.0
    peak_qual_at = None
    collisions = 0
    veh_km_all = 0.0
    veh_km_qual = 0.0
    drac_int_all = 0.0
    drac_int_qual = 0.0
    min_gap = float("inf")

    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)

            # 触发线：源车首次越过 TRIGGER_POS（只在 [ARM_START, ARM_START+TRIGGER_WAIT] 内找）
            if (not triggered) and ARM_START <= t <= ARM_START + TRIGGER_WAIT:
                for v in traci.vehicle.getIDList():
                    if traci.vehicle.getRoadID(v) != "mid":
                        continue
                    if traci.vehicle.getLanePosition(v) >= TRIGGER_POS:
                        src_id, t0, triggered = v, t, True
                        src_pos = round(traci.vehicle.getLanePosition(v), 3)
                        src_v = round(traci.vehicle.getSpeed(v), 3)
                        if brake and src_v > 1e-6:
                            traci.vehicle.setSpeedMode(v, 0)
                        elif brake:
                            stopped = True
                        break

            if brake and src_id is not None and not stopped:
                ids = traci.vehicle.getIDList()
                if src_id not in ids:
                    stopped = True
                else:
                    v = traci.vehicle.getSpeed(src_id)
                    if v <= 1e-6:
                        stopped = True
                    else:
                        traci.vehicle.setSpeed(src_id, max(0.0, v - SRC_DECEL * STEP))

            traci.simulationStep()
            collisions = max(collisions, len(traci.simulation.getCollisions()))
            if t0 is None or t < t0 or t >= t0 + OBS_H:
                continue

            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED, c.VAR_LENGTH,
                                                c.VAR_LANE_INDEX, c.VAR_ACCELERATION))
                    sub.add(v)
            cur = {}
            for v, d in traci.vehicle.getAllSubscriptionResults().items():
                road = str(d.get(c.VAR_ROAD_ID, ""))
                if road not in OFF:
                    continue
                cur[v] = (road, int(d.get(c.VAR_LANE_INDEX, 0)),
                          OFF[road] + float(d.get(c.VAR_LANEPOSITION, -1)),
                          float(d.get(c.VAR_SPEED, -1)), float(d.get(c.VAR_LENGTH, 5.0)),
                          float(d.get(c.VAR_ACCELERATION, 0.0)))
            chains: dict[int, list] = {}
            for v, (road, lane, gp, spd, ln, acc) in cur.items():
                chains.setdefault(lane, []).append((gp, spd, ln, v, acc))
            for lane, lst in chains.items():
                lst.sort(key=lambda x: x[0])
                for i in range(len(lst) - 1):
                    g_lead, s_lead, _, v_lead, _ = lst[i + 1]
                    g_ego, s_ego, l_ego, v_ego, a_ego = lst[i]
                    gap = g_lead - g_ego - l_ego
                    if gap > 0:
                        min_gap = min(min_gap, gap)
                        # 全帧（主分析）：只要有前车、净距为正
                        veh_km_all += s_ego * STEP / 1000.0
                        cc = s_ego - s_lead
                        if cc > 0:
                            drac = cc * cc / (2 * gap)
                            drac_int_all += drac * STEP
                            if drac > peak_all:
                                peak_all, peak_all_at = drac, t
                            # 合格帧（可比性分析，NGSIM 口径）
                            if s_ego >= V_MIN and abs(a_ego) <= ACC_MAX:
                                veh_km_qual += s_ego * STEP / 1000.0
                                drac_int_qual += drac * STEP
                                if drac > peak_qual:
                                    peak_qual, peak_qual_at = drac, t
                                if drac >= DRAC_THR and v_ego != src_id:
                                    r = active.get(v_ego)
                                    if r is None:
                                        active[v_ego] = {"on_t": t, "peak": drac,
                                                         "gap": gap, "c": cc,
                                                         "miss": 0, "lead": v_lead}
                                    else:
                                        r["peak"] = max(r["peak"], drac)
                                        r["miss"] = 0
                                elif v_ego in active:
                                    active[v_ego]["miss"] += 1
            for v_ego in list(active):
                if active[v_ego]["miss"] > MERGE_FRAMES:
                    r = active.pop(v_ego)
                    events.append({"on_t": r["on_t"], "peak": round(r["peak"], 4),
                                   "gap": round(r["gap"], 3), "c": round(r["c"], 3)})
    finally:
        traci.close()

    for v_ego, r in list(active.items()):
        events.append({"on_t": r["on_t"], "peak": round(r["peak"], 4),
                       "gap": round(r["gap"], 3), "c": round(r["c"], 3)})

    res = {"seed": seed, "arm": tag, "hetero": hetero, "brake": brake,
           "src_id": src_id, "t0": t0, "src_pos": src_pos, "src_v": src_v,
           "triggered": triggered,
           "peak_all": round(peak_all, 4), "peak_all_at": peak_all_at,
           "peak_qual": round(peak_qual, 4), "peak_qual_at": peak_qual_at,
           "n_events": len(events),
           "min_gap": None if min_gap == float("inf") else round(min_gap, 3),
           "collisions": collisions,
           "veh_km_all": round(veh_km_all, 3), "veh_km_qual": round(veh_km_qual, 3),
           "drac_int_all": round(drac_int_all, 3),
           "drac_int_qual": round(drac_int_qual, 3),
           "drac_per_km_all": (round(drac_int_all / veh_km_all, 5)
                               if veh_km_all else None),
           "drac_per_km_qual": (round(drac_int_qual / veh_km_qual, 5)
                                if veh_km_qual else None),
           "events": events}
    (work / "run.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    print(f"  [{tag}] 源车 {src_id} t0={t0} pos={src_pos} v={src_v} | "
          f"全帧峰值 {res['peak_all']:.4f} 合格帧峰值 {res['peak_qual']:.4f} | "
          f"事件 {len(events)} 最小净距 {res['min_gap']} 碰撞 {collisions}",
          flush=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--tag", default="pilot")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    all_res = []
    for s in args.seeds:
        print(f"=== 种子 {s} ===", flush=True)
        for hetero in (False, True):
            for brake in (True, False):
                all_res.append(run_arm(s, hetero, brake))

    print("\n=== 2×2 汇总（以种子为配对单位）===")
    print(f"{'种子':>10}{'臂':<12}{'全帧峰值':>10}{'合格帧峰值':>12}"
          f"{'事件':>6}{'最小净距':>10}{'碰撞':>6}{'DRAC/公里':>12}")
    for r in all_res:
        print(f"{r['seed']:>10}{r['arm']:<12}{r['peak_all']:>10.4f}"
              f"{r['peak_qual']:>12.4f}{r['n_events']:>6}"
              f"{str(r['min_gap']):>10}{r['collisions']:>6}"
              f"{str(r['drac_per_km_all']):>12}")

    # 配对效应：ΔRisk = Risk(brake) − Risk(nobrake)
    print("\n=== 风险增量 ΔRisk（brake − nobrake，按种子配对）===")
    print(f"{'种子':>10}{'均质Δ峰值':>12}{'异质Δ峰值':>12}"
          f"{'均质ΔDRAC/公里':>16}{'异质ΔDRAC/公里':>16}")
    deltas = []
    for s in args.seeds:
        hb = next(r for r in all_res if r["seed"] == s and r["arm"] == "H_brake")
        hn = next(r for r in all_res if r["seed"] == s and r["arm"] == "H_nobrake")
        db = next(r for r in all_res if r["seed"] == s and r["arm"] == "D_brake")
        dn = next(r for r in all_res if r["seed"] == s and r["arm"] == "D_nobrake")
        d = {"seed": s,
             "dh_peak": round(hb["peak_all"] - hn["peak_all"], 4),
             "dd_peak": round(db["peak_all"] - dn["peak_all"], 4),
             "dh_drac": round((hb["drac_per_km_all"] or 0)
                              - (hn["drac_per_km_all"] or 0), 5),
             "dd_drac": round((db["drac_per_km_all"] or 0)
                              - (dn["drac_per_km_all"] or 0), 5)}
        deltas.append(d)
        print(f"{s:>10}{d['dh_peak']:>12.4f}{d['dd_peak']:>12.4f}"
              f"{d['dh_drac']:>16}{d['dd_drac']:>16}")

    if len(args.seeds) > 1:
        import statistics as st
        dh = [x["dh_drac"] for x in deltas]
        dd = [x["dd_drac"] for x in deltas]
        print(f"\n均质 ΔDRAC/公里：中位 {st.median(dh):.5f}  范围 "
              f"[{min(dh):.5f}, {max(dh):.5f}]")
        print(f"异质 ΔDRAC/公里：中位 {st.median(dd):.5f}  范围 "
              f"[{min(dd):.5f}, {max(dd):.5f}]")

    (OUT / f"{args.tag}_summary.json").write_text(
        json.dumps({"runs": all_res, "deltas": deltas}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\nwritten: {OUT/f'{args.tag}_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())