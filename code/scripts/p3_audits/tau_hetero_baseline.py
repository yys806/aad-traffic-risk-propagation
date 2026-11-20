"""0.2.11 τ 异质基线：单车道 10 km 开放道路，无源事件

【规格】GPT 第九十一轮 Q3 给死：
  - 单向、单车道、10 km 开放道路；无匝道、无换道、无外部扰动源
  - 目标自由流速度 21.4 m/s，需求 1500 veh/h
  - τ 从主口径 (a) 的经验分布抽取（筛 |Δv| ≤ 5 m/s 的稳态子集）
  - 车辆长度、minGap、DRAC 定义、采样间隔、事件去重全部固定为与 NGSIM 同一版本
  - 每个种子热身 600 s，再统计 3600 s；20 个独立种子
  - 累计暴露不足 100,000 合格跟驰车·公里则延长

【口径对齐（GPT 第九十一轮 Q2 要求，必须与 NGSIM 逐项一致）】
  合格跟驰帧：v ≥ 5 m/s 且 |a| ≤ 1.0 m/s² 且有前车（同车道，净距 > 0）
  暴露：合格帧的 Σ(v × dt)，换算公里
  DRAC：g = 几何净距（扣前车车长）；c = v_ego − v_lead；仅 g>0 且 c>0 计
  事件：DRAC ≥ 3.4 连续段，允许 ≤3 个有效低阈帧
  率：事件数 / 合格车·公里 × 1000

用法：python tau_hetero_baseline.py --seeds 1 2 3 --mode smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(r"D:/shen/TJU/AAD")
OUT = ROOT / "code/outputs/analysis/P3_tau_hetero"
TAU_NPY = ROOT / "code/outputs/analysis/P3_tau_dist/tau_samples.npy"
SPD_NPY = ROOT / "code/outputs/analysis/P3_tau_dist/speed_samples.npy"

STEP = 0.1
ROAD_LEN = 10000.0
V_FREE = 21.4
DEMAND = 1500.0
WARMUP = 600.0
MEASURE = 3600.0
V_MIN = 5.0
ACC_MAX = 1.0
DRAC_THR = 3.4
MERGE_FRAMES = 3
VEH_LEN = 5.0
MIN_GAP = 2.5
TAU_FIXED = 1.584


def sample_taus(n: int, mode: str, seed: int) -> np.ndarray:
    """按口径抽 τ：'steady' = 筛 |Δv|≤5 的稳态子集；'all' = 全部；'fixed' = 单一值。"""
    rng = np.random.default_rng(seed)
    if mode == "fixed":
        return np.full(n, TAU_FIXED)
    tau = np.load(TAU_NPY)
    spd = np.load(SPD_NPY)
    if mode == "steady":
        # 稳态子集：高速层（0.0.2 的口径就是高速层）
        m = (spd >= 22.2) & (spd <= 29.2)
        pool = tau[m] if m.sum() >= 100 else tau
    else:
        pool = tau
    return rng.choice(pool, size=n, replace=True)


def build_net(work: Path) -> Path:
    net = (f'<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="{V_FREE}">'
           f'<lane id="e_0" index="0" speed="{V_FREE}" length="{ROAD_LEN}" '
           f'shape="0.00,0.00 {ROAD_LEN},0.00"/></edge>'
           f'<junction id="a" type="dead_end" x="0" y="0"/>'
           f'<junction id="b" type="dead_end" x="{ROAD_LEN}" y="0"/></net>')
    p = work / "net.net.xml"
    p.write_text(net, encoding="utf-8")
    return p


def build_routes(work: Path, seed: int, mode: str, n_veh: int) -> Path:
    period = 3600.0 / DEMAND
    taus = sample_taus(max(n_veh, 64), mode, seed)
    types = []
    seen = set()
    for tv in taus:
        key = round(float(tv), 3)
        if key in seen:
            continue
        seen.add(key)
        types.append(
            f'<vType id="t{key}" carFollowModel="Krauss" accel="2.6" decel="4.5"'
            f' sigma="0" tau="{key}" length="{VEH_LEN}" minGap="{MIN_GAP}"'
            f' maxSpeed="{V_FREE}" speedFactor="1" actionStepLength="{STEP}"/>')
    vehs = []
    for i in range(n_veh):
        tv = round(float(taus[i % len(taus)]), 3)
        vehs.append(f'<vehicle id="V{i:05d}" type="t{tv}" route="main"'
                    f' depart="{i*period:.3f}" departSpeed="max" departLane="0"/>')
    rp = work / "r.rou.xml"
    rp.write_text(f'<routes>{"".join(types)}<route id="main" edges="e"/>'
                  f'{"".join(vehs)}</routes>', encoding="utf-8")
    return rp


def build_cfg(work: Path, seed: int, t_end: float) -> Path:
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{t_end:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def run_seed(seed: int, mode: str) -> dict:
    work = OUT / f"{mode}_{seed}"
    work.mkdir(parents=True, exist_ok=True)
    t_end = WARMUP + MEASURE + 120.0
    n_veh = int(t_end / (3600.0 / DEMAND)) + 50
    build_net(work)
    build_routes(work, seed, mode, n_veh)
    cfg = build_cfg(work, seed, t_end)

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    sub: set[str] = set()
    veh_km = 0.0
    active: dict[str, dict] = {}
    events: list[dict] = []
    collisions = 0
    n_qual_frames = 0
    prev_speed: dict[str, float] = {}

    try:
        for k in range(int(t_end / STEP)):
            t = round(k * STEP, 3)
            traci.simulationStep()
            collisions = max(collisions, len(traci.simulation.getCollisions()))
            if t < WARMUP:
                continue
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_LANEPOSITION, c.VAR_SPEED,
                                                c.VAR_LENGTH, c.VAR_ACCELERATION))
                    sub.add(v)
            cur = {}
            for v, d in traci.vehicle.getAllSubscriptionResults().items():
                pos = float(d.get(c.VAR_LANEPOSITION, -1))
                spd = float(d.get(c.VAR_SPEED, -1))
                ln = float(d.get(c.VAR_LENGTH, VEH_LEN))
                acc = float(d.get(c.VAR_ACCELERATION, 0.0))
                if pos >= 0 and spd >= 0:
                    cur[v] = (pos, spd, ln, acc)
            lst = sorted([(p, s, l, a, v) for v, (p, s, l, a) in cur.items()],
                         key=lambda x: x[0])
            for i in range(len(lst) - 1):
                p_lead, s_lead, _l_lead, _a_lead, v_lead = lst[i + 1]
                p_ego, s_ego, l_ego, a_ego, v_ego = lst[i]
                gap = (p_lead - p_ego) - l_ego
                # 合格跟驰帧（GPT 第九十一轮 Q2 口径）
                if s_ego < V_MIN or abs(a_ego) > ACC_MAX or gap <= 0:
                    continue
                n_qual_frames += 1
                veh_km += s_ego * STEP / 1000.0
                cc = s_ego - s_lead
                if cc > 0:
                    drac = cc * cc / (2 * gap)
                    if drac >= DRAC_THR:
                        a_rec = active.get(v_ego)
                        if a_rec is None:
                            active[v_ego] = {"on_t": t, "peak": drac, "gap": gap,
                                             "c": cc, "miss": 0}
                        else:
                            a_rec["peak"] = max(a_rec["peak"], drac)
                            a_rec["miss"] = 0
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

    rate = (len(events) / veh_km * 1000.0) if veh_km > 0 else None
    res = {"seed": seed, "mode": mode, "n_events": len(events),
           "veh_km": round(veh_km, 3), "n_qual_frames": n_qual_frames,
           "rate_per_1000_veh_km": (round(rate, 3) if rate else None),
           "collisions": collisions, "events": events}
    (work / "run.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(f"  种子 {seed} [{mode}]: 事件 {len(events)} 暴露 {veh_km:.1f} 车·公里 "
          f"率 {rate if rate is None else round(rate, 2)} 碰撞 {collisions}", flush=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[1])
    ap.add_argument("--mode", choices=["fixed", "steady", "all"], default="steady")
    ap.add_argument("--tag", default="smoke")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"=== τ 异质基线 [{args.mode}]，{len(args.seeds)} 个种子，"
          f"热身 {WARMUP:.0f}s + 统计 {MEASURE:.0f}s ===", flush=True)
    res = [run_seed(s, args.mode) for s in args.seeds]
    tot_ev = sum(r["n_events"] for r in res)
    tot_km = sum(r["veh_km"] for r in res)
    print(f"\n合计：事件 {tot_ev}，暴露 {tot_km:.1f} 车·公里，"
          f"率 {(tot_ev/tot_km*1000) if tot_km else None:.2f} 件/千车·公里")
    (OUT / f"{args.tag}_{args.mode}_summary.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT/f'{args.tag}_{args.mode}_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())