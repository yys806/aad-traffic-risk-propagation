"""0.2.14 区域场景 τ 异质 vs 均质（配对比较，GPT 第九十二轮 Q3 批准）

【设计】
  - 与 0.2.7（region_stop.py）**完全同一个场景、同一个种子、同一套检测**
  - 唯一变量：车流的 τ 分配
      · homogeneous：全体 τ = 1.584（= 0.2.7 原设置）
      · hetero_54_80：逐车从 NGSIM 54–80 km/h 层经验分布抽样（区域场景实际速度层）
      · hetero_hi：逐车从 NGSIM 80–105 km/h 层抽样（与 0.0.2 同层，作对照）
  - 种子固定 20261101，源车选择规则不变，前车减速至停不变

【为什么用 54–80 层作主方案】
区域场景稳态速度 21.378 m/s = 77.0 km/h，落在 54–80 km/h 层（GPT 第九十三轮 Q2）。

【判据】不设「必须越阈」。只比：
  峰值 DRAC、事件数、最小净距、碰撞、合格暴露车·公里、连续 DRAC 暴露（车·秒/车·公里）
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
OUT = ROOT / "code/outputs/analysis/P3_region_hetero"
TAU_NPY = ROOT / "code/outputs/analysis/P3_tau_dist/tau_samples.npy"
SPD_NPY = ROOT / "code/outputs/analysis/P3_tau_dist/speed_samples.npy"

T_SRC = 600.0
WAIT_MAX = 30.0
SRC_ZONE = 200.0
SRC_DECEL = 9.0
DRAC_THR = 3.4
MERGE_FRAMES = 3
OBS_H = 600.0
DEMAND = 1600.0
TAU_FIXED = 1.584
V_MIN = 5.0
ACC_MAX = 1.0
T_END = T_SRC + WAIT_MAX + OBS_H + 120.0

MID_LEN, BN_LEN, OUT_LEN = 1898.5, 200.0, 1898.5
OFF = {"mid": 0.0, "bn": MID_LEN, "out": MID_LEN + BN_LEN,
       "tail": MID_LEN + BN_LEN + OUT_LEN}


def tau_pool(layer: str) -> np.ndarray:
    tau = np.load(TAU_NPY)
    spd = np.load(SPD_NPY)
    if layer == "hi":
        m = (spd >= 22.2) & (spd <= 29.2)
    elif layer == "mid":
        m = (spd >= 15.0) & (spd < 22.2)
    else:
        m = np.ones(len(tau), dtype=bool)
    pool = tau[m]
    print(f"  τ 池 [{layer}]: n={len(pool)} 中位 {np.median(pool):.3f} "
          f"p10 {np.percentile(pool, 10):.3f}", flush=True)
    return pool


def build_routes(work: Path, seed: int, mode: str, layer: str, n: int) -> Path:
    period = 3600.0 / DEMAND
    rng = np.random.default_rng(seed)
    if mode == "homogeneous":
        taus = np.full(n, TAU_FIXED)
    else:
        taus = rng.choice(tau_pool(layer), size=n, replace=True)
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


def run(seed: int, mode: str, layer: str, force_src: str | None = None) -> dict:
    tag = f"{mode}_{layer}"
    work = OUT / tag
    work.mkdir(parents=True, exist_ok=True)
    build_net(50.0, work)
    n = int(T_END / (3600.0 / DEMAND)) + 50
    build_routes(work, seed, mode, layer, n)
    cfg = build_cfg(work, seed)

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    src_id = None
    t0 = None
    src_pos_t0 = None
    src_v_t0 = None
    stopped = False
    triggered = False
    sub: set[str] = set()
    active: dict[str, dict] = {}
    events: list[dict] = []
    peak = 0.0
    peak_at = None
    collisions = 0
    veh_km = 0.0
    drac_integral = 0.0    # 连续风险暴露：Σ DRAC·dt（车·秒的 DRAC 积分）
    min_gap = float("inf")

    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)
            if (not triggered) and T_SRC <= t <= T_SRC + WAIT_MAX:
                ids_now = traci.vehicle.getIDList()
                if force_src is not None:
                    # 配对模式：强制同一辆车当源车，只在它出现后触发
                    if force_src in ids_now:
                        src_id, t0, triggered = force_src, t, True
                        src_pos_t0 = round(traci.vehicle.getLanePosition(src_id), 3)
                        src_v_t0 = round(traci.vehicle.getSpeed(src_id), 3)
                        if traci.vehicle.getSpeed(src_id) > 1e-6:
                            traci.vehicle.setSpeedMode(src_id, 0)
                        else:
                            stopped = True
                else:
                    cands = []
                    for v in ids_now:
                        if traci.vehicle.getRoadID(v) != "mid":
                            continue
                        d = MID_LEN - traci.vehicle.getLanePosition(v)
                        if 0.0 <= d <= SRC_ZONE:
                            cands.append((d, v))
                    if cands:
                        cands.sort(key=lambda x: (x[0], x[1]))
                        src_id, t0, triggered = cands[0][1], t, True
                        src_pos_t0 = round(traci.vehicle.getLanePosition(src_id), 3)
                        src_v_t0 = round(traci.vehicle.getSpeed(src_id), 3)
                        if traci.vehicle.getSpeed(src_id) > 1e-6:
                            traci.vehicle.setSpeedMode(src_id, 0)
                        else:
                            stopped = True
            if src_id is not None and not stopped:
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
            if t0 is not None and t >= t0 + OBS_H:
                continue

            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED, c.VAR_LENGTH,
                                                c.VAR_LANE_INDEX,
                                                c.VAR_ACCELERATION))
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
                    if s_ego < V_MIN or abs(a_ego) > ACC_MAX or gap <= 0:
                        continue
                    veh_km += s_ego * STEP / 1000.0
                    cc = s_ego - s_lead
                    if cc > 0:
                        drac = cc * cc / (2 * gap)
                        drac_integral += drac * STEP
                        if drac > peak:
                            peak, peak_at = drac, t
                        if drac >= DRAC_THR and v_ego != src_id:
                            r = active.get(v_ego)
                            if r is None:
                                active[v_ego] = {"on_t": t, "peak": drac, "gap": gap,
                                                 "c": cc, "miss": 0, "lead": v_lead}
                            else:
                                r["peak"] = max(r["peak"], drac)
                                r["miss"] = 0
                        elif v_ego in active:
                            active[v_ego]["miss"] += 1
            for v_ego in list(active):
                if active[v_ego]["miss"] > MERGE_FRAMES:
                    r = active.pop(v_ego)
                    events.append({"on_t": r["on_t"], "peak": round(r["peak"], 4),
                                   "gap": round(r["gap"], 3), "c": round(r["c"], 3),
                                   "lead": r["lead"]})
    finally:
        traci.close()

    for v_ego, r in list(active.items()):
        events.append({"on_t": r["on_t"], "peak": round(r["peak"], 4),
                       "gap": round(r["gap"], 3), "c": round(r["c"], 3),
                       "lead": r["lead"]})

    res = {"seed": seed, "mode": mode, "layer": layer, "src_id": src_id, "t0": t0,
           "src_pos_at_t0": src_pos_t0, "src_v_at_t0": src_v_t0,
           "forced": force_src is not None,
           "n_events": len(events), "peak_drac": round(peak, 4), "peak_at": peak_at,
           "min_gap": (None if min_gap == float("inf") else round(min_gap, 3)),
           "collisions": collisions, "veh_km": round(veh_km, 3),
           "drac_integral_veh_s": round(drac_integral, 3),
           "drac_per_veh_km": (round(drac_integral / veh_km, 4) if veh_km else None),
           "events": events}
    (work / "run.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    print(f"  [{tag}] 源车 {src_id} t0={t0} 位置={src_pos_t0} 车速={src_v_t0} "
          f"峰值 {res['peak_drac']} "
          f"事件 {len(events)} 最小净距 {res['min_gap']} 碰撞 {collisions} "
          f"暴露 {veh_km:.0f} 车·公里 DRAC积分/车·公里 {res['drac_per_veh_km']}",
          flush=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261101)
    ap.add_argument("--force-src", default=None,
                    help="强制指定源车 ID（配对比较用；None 则按最近者规则选）")
    ap.add_argument("--only", default=None,
                    help="只跑其中一个配置，如 homogeneous 或 hetero_mid")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"=== 区域场景 τ 配对比较（种子 {args.seed}"
          f"{'，强制源车 '+args.force_src if args.force_src else ''}）===", flush=True)
    runs = [("homogeneous", "none"), ("hetero", "mid"), ("hetero", "hi")]
    if args.only:
        sel = {"homogeneous": ("homogeneous", "none"),
               "hetero_mid": ("hetero", "mid"),
               "hetero_hi": ("hetero", "hi")}[args.only]
        runs = [sel]
    res = [run(args.seed, m, l, args.force_src) for m, l in runs]
    print("\n=== 汇总 ===")
    print(f"{'配置':<22}{'峰值DRAC':>10}{'事件':>6}{'最小净距':>10}"
          f"{'碰撞':>6}{'DRAC积分/车·公里':>18}")
    for r in res:
        print(f"{r['mode']+'/'+r['layer']:<22}{r['peak_drac']:>10.4f}"
              f"{r['n_events']:>6}{str(r['min_gap']):>10}"
              f"{r['collisions']:>6}{str(r['drac_per_veh_km']):>18}")
    (OUT / f"compare_{args.seed}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/f'compare_{args.seed}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())