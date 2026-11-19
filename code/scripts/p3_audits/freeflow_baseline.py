"""0.1.1 逐车自由流基准 + Y 重定义（GPT 第五十八轮选 B）。

【为什么重做】
vType 只写了 speedFactor="1"、漏写 speedDev="0"，SUMO 默认 speedDev=0.1，
每辆车抽到自己期望车速（实测 0.79–1.02 倍）。于是：
  - 22/88 辆「绕行额外耗时」其实只是开得慢，不是路网缺陷（已查清）
  - 但 Y = ΔT + 50.1 里的 50.1 是**假定 30 m/s** 的代价，对慢车不成立

【新定义（GPT 逐字）】
  Y_i = (T主,i − T0主,i) − (T绕,i − T0绕,i)
      = (T主,i − T绕,i) + (T0绕,i − T0主,i)
T0 是**同一辆车、同一条路线、同一个计时区间**的自由流时间。
偏差方向：基准差是**加项**，慢车的 T0绕−T0主 更大 → 正确 Y 比旧 Y **更大**（旧式是低估）。

【为了不循环论证】
T0 不许用正式运行的绕行耗时反推（那样等于用结果算结果），
改为**另跑空路单程**，并把该车实际抽到的 speedFactor 钉死。

【距离口径（GPT 要求核对 6507 与 6597）】
两者不是同一个计时区间：
  6507 = 从岔口 3000 m 起算（5500 + 998.5 + …）—— 错的口径
  6597 = 从决策位置 2900 m 起算（98.5 + 5500 + 998.5）—— 正确
本脚本一律从**网络实际读取**边长度，不手打常数。

【跑之前写死的预测】
1. 每辆车 main 支与 detour 支抽到的 speedFactor **相同**（插入在改路之前，RNG 顺序不变）。
2. T0主 < T0绕（绕行路更远），且两者比值 = 6597 口径下的距离比 ≈ 1.295。
3. 新 Y ≥ 旧 Y，差值 = (T0绕−T0主) − 50.1，对 30 m/s 的车为 0，对慢车为正。
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
OUT = ROOT / "code/outputs/analysis/P3_freeflow"
BATCH = ROOT / "code/outputs/analysis/P3_module3_batch/batch.json"

STEP = 0.1
V_LIM = 30.0
DEMAND = 1600.0
T_END = 1680.0
T0_BLK, BLOCK = 600.0, 180.0
DECIDE_POS = 2900.0
ENROLL_LO, ENROLL_HI = 600.0, 780.0


def build_rou(work: Path) -> int:
    period = 3600.0 / DEMAND
    n = int(T_END / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r_base.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>'
        f'<route id="detour" edges="in bypass tail"/>{vehs}</routes>', encoding="utf-8")
    return n


def cfg_for(work: Path, tag: str, trip: str) -> Path:
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


def scan_speedfactors(work: Path) -> dict:
    """跑一次基线，读每辆车实际抽到的 speedFactor 与决策时刻。"""
    cfg = cfg_for(work, "scan", "t_scan.xml")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked = False
    sub = set()
    sf: dict[str, float] = {}
    decide: dict[str, dict] = {}
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 2)
            if not blocked and t >= T0_BLK:
                traci.lane.setMaxSpeed("bn_0", 4.0)
                blocked = True
            if blocked and t >= T0_BLK + BLOCK:
                traci.lane.setMaxSpeed("bn_0", V_LIM)
                blocked = False
            traci.simulationStep()
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION))
                    sub.add(v)
                    sf[v] = round(traci.vehicle.getSpeedFactor(v), 6)
            if k % 2:
                continue
            for v, val in traci.vehicle.getAllSubscriptionResults().items():
                road = str(val.get(c.VAR_ROAD_ID, ""))
                pos = float(val.get(c.VAR_LANEPOSITION, -1))
                if road == "in" and pos >= DECIDE_POS:
                    decide[v] = {"t": t, "pos": round(pos, 1)}
    finally:
        traci.close()
    return {"sf": sf, "decide": decide}


def free_run(work: Path, veh: str, f: float, route: str, pos: float) -> float | None:
    """空路单程：把该车的 speedFactor 钉死，从 decision 位置出发，返回 T0。"""
    tag = f"ff_{veh}_{route}"
    vt = ('<vType id="p" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="{f}"'
          ' speedDev="0" lcKeepRight="0"/>')
    edges = "in mid bn out tail" if route == "main" else "in bypass tail"
    (work / f"r_{tag}.rou.xml").write_text(
        f'<routes>{vt}<route id="r" edges="{edges}"/>'
        f'<vehicle id="{veh}" type="p" route="r" depart="0" departPos="{pos}"'
        f' departSpeed="max" departLane="0"/></routes>', encoding="utf-8")
    cfg = work / f"run_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_{tag}.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="1200"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="t_{tag}.xml"/></output></configuration>',
        encoding="utf-8")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    try:
        for _ in range(int(1200 / STEP)):
            traci.simulationStep()
            if traci.simulation.getMinExpectedNumber() == 0:
                break
    finally:
        traci.close()
    tp = work / f"t_{tag}.xml"
    if not tp.exists():
        return None
    for tri in ET.parse(tp).getroot().iter("tripinfo"):
        if tri.get("id") == veh:
            return round(float(tri.get("duration")), 2)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=88)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)
    n_plan = build_rou(OUT)
    print(f"计划车辆 {n_plan}", flush=True)

    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    summary = {s["target"]: s for s in batch["summary"]}
    targets = list(summary)[:args.n]
    print(f"要重算 Y 的车 {len(targets)} 辆", flush=True)

    print("\n[1/3] 跑基线，读每辆车抽到的 speedFactor 与决策位置…", flush=True)
    scan = scan_speedfactors(OUT)
    enrolled = [v for v, d in scan["decide"].items()
                if ENROLL_LO <= d["t"] <= ENROLL_HI]
    print(f"  读到 speedFactor {len(scan['sf'])} 辆；入组窗内 {len(enrolled)} 辆", flush=True)
    sfs = sorted(scan["sf"].values())
    print(f"  speedFactor：min {sfs[0]:.3f} p50 {sfs[len(sfs)//2]:.3f} "
          f"max {sfs[-1]:.3f}", flush=True)
    missing = [t for t in targets if t not in scan["sf"]]
    print(f"  缺 speedFactor 的车：{missing}", flush=True)

    print(f"\n[2/3] 逐车跑空路基准（{len(targets)} 辆 × 2 条路线）…", flush=True)
    rows = []
    for j, tgt in enumerate(targets, 1):
        f = scan["sf"].get(tgt)
        dec = scan["decide"].get(tgt) or {}
        pos = dec.get("pos", DECIDE_POS)
        if f is None:
            rows.append({"target": tgt, "error": "无 speedFactor"})
            continue
        t0m = free_run(OUT, tgt, f, "main", pos)
        t0d = free_run(OUT, tgt, f, "detour", pos)
        s = summary[tgt]
        T_main, T_det = s["T_main"], s["T_detour"]
        row = {"target": tgt, "speedFactor": f, "decide_pos": pos,
               "T0_main": t0m, "T0_detour": t0d,
               "T_main": T_main, "T_detour": T_det,
               "dT": round(T_main - T_det, 1) if T_main and T_det else None,
               "Y_old": s["Y"]}
        if t0m and t0d and T_main and T_det:
            row["penalty"] = round(t0d - t0m, 2)
            row["Y_new"] = round((T_main - t0m) - (T_det - t0d), 1)
            row["delay_main"] = round(T_main - t0m, 1)
            row["delay_detour"] = round(T_det - t0d, 1)
        rows.append(row)
        if j % 10 == 0 or j == len(targets):
            print(f"  [{j}/{len(targets)}] …", flush=True)

    print("\n[3/3] 汇总", flush=True)
    ok = [r for r in rows if "Y_new" in r]
    pen = [r["penalty"] for r in ok]
    yn = [r["Y_new"] for r in ok]
    yo = [r["Y_old"] for r in ok if r["Y_old"] is not None]
    dm = [r["delay_main"] for r in ok]
    dd = [r["delay_detour"] for r in ok]
    print(f"  成功 {len(ok)} / {len(rows)}")
    print(f"  基准差 T0绕−T0主：中位 {statistics.median(pen):.2f} s，"
          f"范围 [{min(pen):.2f}, {max(pen):.2f}]")
    print(f"  主路超额耗时：中位 {statistics.median(dm):.1f} s，范围 [{min(dm):.1f}, {max(dm):.1f}]")
    print(f"  绕行超额耗时：中位 {statistics.median(dd):.1f} s，范围 [{min(dd):.1f}, {max(dd):.1f}]")
    print(f"  Y_new：中位 {statistics.median(yn):.1f} s，均值 {statistics.mean(yn):.1f}，"
          f"范围 [{min(yn):.1f}, {max(yn):.1f}]")
    if yo:
        print(f"  Y_old：中位 {statistics.median(yo):.1f}，范围 [{min(yo):.1f}, {max(yo):.1f}]")
    dlt = [r["dT"] for r in ok]
    print(f"  实际净节时 ΔT：中位 {statistics.median(dlt):.1f} s，"
          f"范围 [{min(dlt):.1f}, {max(dlt):.1f}]")

    (OUT / "freeflow.json").write_text(json.dumps(
        {"rows": rows, "n_sf": len(scan["sf"])}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\nwritten: {OUT/'freeflow.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
