"""核实 Claude 的说法：改 τ 后区域场景的来流速度会变吗？

【要回答】Claude 说 R5 设置下 trigger 区来流中位在 22.15–25.98 m/s，
而 0.2.22（τ=1.584）实测源车初速是 21.378 m/s。

若成立，则「用旧设置的车速选 τ 的层」是循环论证。

【做法】无源、无任何控制，只跑纯车流。两个 τ 各跑 4 个种子，
在 mid 上距 bn 入口 200 m 的区域内统计车速中位与分位。
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

OUT = Path(r"D:/shen/TJU/AAD/code/outputs/analysis/P3_speed_probe")
MID_LEN, BN_LEN, OUT_LEN = 1898.5, 200.0, 1898.5
OFF = {"mid": 0.0, "bn": MID_LEN, "out": MID_LEN + BN_LEN,
       "tail": MID_LEN + BN_LEN + OUT_LEN}
TRIGGER_ZONE = 200.0      # 距 bn 入口 200 m 内（与源车选区一致）
DEMAND = 1600.0
T_END = 900.0
SEEDS = [20261201, 20261202, 20261203, 20261204]
TAUS = [1.350, 1.584]
REACT = 0.8


def build(tau: float, seed: int, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    build_net(50.0, work)
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{tau}" length="5" minGap="2.5" maxSpeed="{V_LIM}" speedFactor="1"'
          f' lcKeepRight="0" actionStepLength="{REACT}"/>')
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


def run(tau: float, seed: int) -> dict:
    work = OUT / f"tau{tau}_{seed}"
    cfg = build(tau, seed, work)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1",
                 "--step-method.ballistic", "true"])
    c = traci.constants
    sub: set[str] = set()
    speeds_zone = []
    gaps_zone = []
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)
            traci.simulationStep()
            if t < 600.0:          # 只看稳定后
                continue
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED, c.VAR_LENGTH,
                                                c.VAR_LANE_INDEX))
                    sub.add(v)
            cur = {}
            for v, d in traci.vehicle.getAllSubscriptionResults().items():
                road = str(d.get(c.VAR_ROAD_ID, ""))
                if road not in OFF:
                    continue
                pos = float(d.get(c.VAR_LANEPOSITION, -1))
                cur[v] = (OFF[road] + pos, float(d.get(c.VAR_SPEED, -1)),
                          float(d.get(c.VAR_LENGTH, 5.0)),
                          int(d.get(c.VAR_LANE_INDEX, 0)))
            # trigger 区：mid 上距 bn 入口 ≤200 m
            for v, (gp, spd, ln, lane) in cur.items():
                if 0 <= gp and (MID_LEN - gp) <= TRIGGER_ZONE:
                    if spd > 0.5:
                        speeds_zone.append(spd)
            # 车距分布
            lanes: dict[int, list] = {}
            for v, (gp, spd, ln, lane) in cur.items():
                if 0 <= gp and (MID_LEN - gp) <= 600.0:
                    lanes.setdefault(lane, []).append((gp, ln))
            for lane, lst in lanes.items():
                lst.sort()
                for i in range(len(lst) - 1):
                    gaps_zone.append((lst[i + 1][0] - lst[i][0]) - lst[i][1])
    finally:
        traci.close()

    if not speeds_zone:
        return {"tau": tau, "seed": seed, "n": 0}
    arr = np.array(speeds_zone)
    garr = np.array(gaps_zone) if gaps_zone else np.array([0.0])
    return {"tau": tau, "seed": seed, "n": len(arr),
            "v_median": round(float(np.median(arr)), 3),
            "v_p10": round(float(np.percentile(arr, 10)), 3),
            "v_p25": round(float(np.percentile(arr, 25)), 3),
            "v_p75": round(float(np.percentile(arr, 75)), 3),
            "v_p90": round(float(np.percentile(arr, 90)), 3),
            "v_mean": round(float(arr.mean()), 3),
            "gap_median": round(float(np.median(garr)), 3)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== 无源纯车流：τ 对来流速度的影响 ===")
    print(f"{'tau':>7}{'seed':>12}{'v中位':>8}{'v_p10':>8}{'v_p25':>8}"
          f"{'v_p75':>8}{'v_p90':>8}{'净距中位':>10}{'样本':>8}")
    res = []
    for tau in TAUS:
        for s in SEEDS:
            r = run(tau, s)
            res.append(r)
            if r["n"]:
                print(f"{tau:>7.3f}{s:>12}{r['v_median']:>8.2f}{r['v_p10']:>8.2f}"
                      f"{r['v_p25']:>8.2f}{r['v_p75']:>8.2f}{r['v_p90']:>8.2f}"
                      f"{r['gap_median']:>10.2f}{r['n']:>8}", flush=True)

    print("\n=== 汇总 ===")
    for tau in TAUS:
        rs = [r for r in res if r["tau"] == tau and r["n"]]
        if not rs:
            continue
        meds = [r["v_median"] for r in rs]
        print(f"  τ={tau}: 各seed中位的范围 {min(meds):.2f}–{max(meds):.2f} m/s"
              f"（{min(meds)*3.6:.0f}–{max(meds)*3.6:.0f} km/h）"
              f"  总中位 {st.median(meds):.2f}")
    (OUT / "speed_probe.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'speed_probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())