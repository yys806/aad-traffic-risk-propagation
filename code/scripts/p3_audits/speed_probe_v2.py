"""0.2.28 查清车速波动的真正来源：speedDev 还是 τ

【背景】
0.2.27 的探针有两个错：
  ① 区域条件缺上界 -> 实际算了 mid末200m + bn + out + tail 共 3300 m（Gemini 发现）
  ② 只写 speedFactor="1"、没写 speedDev -> SUMO 默认 speedDev=0.1 生效
     这个坑 0.1.1 的 freeflow_baseline.py 第 4 行就记录过，我又踩了一遍

【要回答】
来流车速的波动到底来自 τ 还是 speedDev？
若 speedDev=0 时车速恒为 30、τ 完全不影响 -> 结论：speedDev 是主因

【设计】
4 个条件 × 4 个种子 = 16 次无源纯车流：
  (τ=1.350, speedDev=0.1)  (τ=1.584, speedDev=0.1)
  (τ=1.350, speedDev=0)    (τ=1.584, speedDev=0)
区域严格限定：mid 上 [MID_LEN-200, MID_LEN]，即 1698.5–1898.5 m
"""
import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/p3_audits")
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts")
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net, V_LIM, STEP  # noqa: E402

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_speed_probe_v2")
MID_LEN, BN_LEN, OUT_LEN = 1898.5, 200.0, 1898.5
OFF = {"mid": 0.0, "bn": MID_LEN, "out": MID_LEN + BN_LEN,
       "tail": MID_LEN + BN_LEN + OUT_LEN}
ZONE_LO, ZONE_HI = MID_LEN - 200.0, MID_LEN      # 严格 mid 末 200 m
DEMAND = 1600.0
T_END = 900.0
T_STAT = 600.0
SEEDS = [20261201, 20261202, 20261203, 20261204]
CONDS = [(1.350, 0.1), (1.584, 0.1), (1.350, 0.0), (1.584, 0.0)]
REACT = 0.8


def build(tau, sdev, seed, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    build_net(50.0, work)
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{tau}" length="5" minGap="2.5" maxSpeed="{V_LIM}"'
          f' speedFactor="1" speedDev="{sdev}" lcKeepRight="0"'
          f' actionStepLength="{REACT}"/>')
    period = 3600.0 / DEMAND
    n = int(T_END / period) + 50
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>{vehs}</routes>',
        encoding="utf-8")
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def run(tau, sdev, seed) -> dict:
    work = OUT / f"t{tau}_d{sdev}_{seed}"
    cfg = build(tau, sdev, seed, work)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1",
                 "--step-method.ballistic", "true"])
    c = traci.constants
    sub: set[str] = set()
    speeds = []
    factors = {}
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)
            traci.simulationStep()
            if t < T_STAT:
                continue
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED))
                    sub.add(v)
            for v, d in traci.vehicle.getAllSubscriptionResults().items():
                road = str(d.get(c.VAR_ROAD_ID, ""))
                if road != "mid":
                    continue
                gp = OFF[road] + float(d.get(c.VAR_LANEPOSITION, -1))
                if not (ZONE_LO <= gp <= ZONE_HI):      # 严格上界与下界
                    continue
                spd = float(d.get(c.VAR_SPEED, -1))
                if spd > 0.5:
                    speeds.append(spd)
            if not factors and t > T_STAT + 5:
                for v in traci.vehicle.getIDList()[:40]:
                    factors[v] = round(traci.vehicle.getSpeedFactor(v), 4)
    finally:
        traci.close()

    if not speeds:
        return {"tau": tau, "sdev": sdev, "seed": seed, "n": 0}
    a = np.array(speeds)
    return {"tau": tau, "sdev": sdev, "seed": seed, "n": len(a),
            "v_median": round(float(np.median(a)), 3),
            "v_mean": round(float(a.mean()), 3),
            "v_min": round(float(a.min()), 3),
            "v_max": round(float(a.max()), 3),
            "speedfactors": factors}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== 无源纯车流：speedDev 与 τ 对来流车速的影响 ===")
    print("区域严格限定 mid 末 200 m（1698.5–1898.5），t∈[600,900]")
    print()
    print(f"{'tau':>7}{'speedDev':>10}{'seed':>12}{'v中位':>9}{'v均值':>9}"
          f"{'v最小':>9}{'v最大':>9}{'样本':>9}")
    res = []
    for tau, sdev in CONDS:
        for s in SEEDS:
            r = run(tau, sdev, s)
            res.append(r)
            if r["n"]:
                print(f"{tau:>7.3f}{sdev:>10.1f}{s:>12}{r['v_median']:>9.2f}"
                      f"{r['v_mean']:>9.2f}{r['v_min']:>9.2f}{r['v_max']:>9.2f}"
                      f"{r['n']:>9}", flush=True)

    print("\n=== 汇总（每个条件 4 个种子的组中位）===")
    print(f"{'tau':>7}{'speedDev':>10}{'组中位':>9}{'种子极差':>10}{'配对差(对 0.1)':>16}")
    base = {}
    for tau, sdev in CONDS:
        rs = [r for r in res if r["tau"] == tau and r["sdev"] == sdev and r["n"]]
        if not rs:
            continue
        meds = [r["v_median"] for r in rs]
        base[(tau, sdev)] = meds
        print(f"{tau:>7.3f}{sdev:>10.1f}{st.median(meds):>9.2f}"
              f"{max(meds)-min(meds):>10.2f}")

    print("\n=== 关键判读 ===")
    for tau in (1.350, 1.584):
        d1 = base.get((tau, 0.1))
        d0 = base.get((tau, 0.0))
        if d1 and d0:
            print(f"  τ={tau}: speedDev 0.1 → 组中位 {st.median(d1):.2f}"
                  f"（极差 {max(d1)-min(d1):.2f}）"
                  f" | speedDev 0 → 组中位 {st.median(d0):.2f}"
                  f"（极差 {max(d0)-min(d0):.2f}）")
    print()
    s01 = [r["speedfactors"] for r in res if r["sdev"] == 0.1 and r["speedfactors"]]
    s00 = [r["speedfactors"] for r in res if r["sdev"] == 0.0 and r["speedfactors"]]
    if s01:
        vals = [v for f in s01 for v in f.values()]
        print(f"  speedDev=0.1 时实测 speedFactor: 最小 {min(vals)}, 最大 {max(vals)}")
    if s00:
        vals = [v for f in s00 for v in f.values()]
        print(f"  speedDev=0   时实测 speedFactor: 最小 {min(vals)}, 最大 {max(vals)}")

    (OUT / "speed_probe_v2.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'speed_probe_v2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())