"""0.1.3b 敏感性场景的逐车自由流基准（修正常数偏差）。

【为什么重做】
speedDev=0 时我在 module3_batch 里用了固定常数 FREE_MAIN=170.1 / FREE_DET=220.1，
那两个数是从 **departPos=2900** 测的。
但每辆车的决策位置其实在 2900–2998 m 之间，最多已经多走了 98 m（约 3.3 s）。
于是 T0 偏高 → 绕行超额耗时系统性为负（实测 −3.15 s，80/80 全负）→ Y 被抬高约 3.15 s。

这也违反了 GPT 指出的不等式：delay_绕 ≥ 0 时必有 Y_i ≤ delay_主,i，
Y 的中位数不能超过主路超额耗时的中位数。

【做法】
对每辆车，用**它自己的决策位置** p_i 跑主路与绕行两条空路单程，得到 T0主,i、T0绕,i。
speedFactor 钉死为 1.0、speedDev=0（与敏感性场景一致）。

【跑之前写死的预测】
1. 每辆车的 T0主,i = (5101.6 − (p_i−2900))/30，T0绕,i = (6603.0 − (p_i−2900))/30，误差 <0.2 s。
2. 修正后绕行超额耗时应落在 ±0.2 s 内（不再系统性为负）。
3. 修正后 Y 中位 ≤ 主路超额耗时中位（不等式成立）。
4. 修正后 Y 中位应低于原来的 81.65 s，约 78 秒量级。
"""
from __future__ import annotations

import json
import statistics as st
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_freeflow_sens"
BATCH = ROOT / "code/outputs/analysis/P3_module3_batch/batch.json"
STEP = 0.1


def free_run(tag: str, route: str, pos: float) -> float | None:
    vt = ('<vType id="p" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"'
          ' speedDev="0" lcKeepRight="0"/>')
    edges = "in mid bn out tail" if route == "main" else "in bypass tail"
    (OUT / f"r_{tag}.rou.xml").write_text(
        f'<routes>{vt}<route id="r" edges="{edges}"/>'
        f'<vehicle id="P" type="p" route="r" depart="0" departPos="{pos}"'
        f' departSpeed="max" departLane="0"/></routes>', encoding="utf-8")
    cfg = OUT / f"c_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_{tag}.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="900"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="t_{tag}.xml"/></output></configuration>',
        encoding="utf-8")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--time-to-teleport", "-1"])
    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
    finally:
        traci.close()
    tp = OUT / f"t_{tag}.xml"
    if not tp.exists():
        return None
    for tri in ET.parse(tp).getroot().iter("tripinfo"):
        if tri.get("id") == "P":
            return round(float(tri.get("duration")), 2)
    return None


def scan_positions() -> dict:
    """复刻 module3_batch 的决策位置判定：每 2 步采样，最后一次 road=in 且 pos>=2900。
    speedDev=0，加同样的堵塞，与敏感性场景一致。"""
    period = 3600.0 / 1600.0
    n = int(1680.0 / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"'
          ' speedDev="0" lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (OUT / "r_scan.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>{vehs}</routes>',
        encoding="utf-8")
    cfg = OUT / "c_scan.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_scan.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="1680"/></time>'
        f'<processing><step-length value="0.1"/></processing>'
        f'<random_number><seed value="20261120"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>',
        encoding="utf-8")
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    blocked, sub = False, set()
    decide: dict[str, dict] = {}
    try:
        for k in range(int(1680 / STEP)):
            t = round(k * STEP, 2)
            if not blocked and t >= 600.0:
                traci.lane.setMaxSpeed("bn_0", 4.0); blocked = True
            if blocked and t >= 780.0:
                traci.lane.setMaxSpeed("bn_0", 30.0); blocked = False
            traci.simulationStep()
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION))
                    sub.add(v)
            if k % 2:
                continue
            for v, val in traci.vehicle.getAllSubscriptionResults().items():
                if str(val.get(c.VAR_ROAD_ID, "")) == "in" and float(val.get(c.VAR_LANEPOSITION, -1)) >= 2900:
                    decide[v] = {"t": t, "pos": round(float(val.get(c.VAR_LANEPOSITION, -1)), 1)}
    finally:
        traci.close()
    return decide


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)
    print("扫描决策位置…", flush=True)
    decide = scan_positions()
    print(f"  扫到 {len(decide)} 辆", flush=True)
    b = json.load(open(BATCH, encoding="utf-8"))
    S = [s for s in b["summary"] if s["T_main"] and s["T_detour"]]
    print(f"要重算 {len(S)} 辆", flush=True)

    rows = []
    for j, s in enumerate(S, 1):
        tgt = s["target"]
        pos = (decide.get(tgt) or {}).get("pos")
        if pos is None:
            print(f"  {tgt}: 无决策位置，跳过", flush=True)
            continue
        t0m = free_run(f"{tgt}_m", "main", pos)
        t0d = free_run(f"{tgt}_d", "detour", pos)
        if t0m is None or t0d is None:
            print(f"  {tgt}: 空路跑失败", flush=True)
            continue
        dm = round(s["T_main"] - t0m, 2)
        dd = round(s["T_detour"] - t0d, 2)
        rows.append({"target": tgt, "decide_pos": pos, "T0_main": t0m, "T0_detour": t0d,
                     "T_main": s["T_main"], "T_detour": s["T_detour"],
                     "delay_main": dm, "delay_detour": dd,
                     "Y": round(dm - dd, 2), "dT": round(s["T_main"] - s["T_detour"], 2)})
        if j % 10 == 0 or j == len(S):
            print(f"  [{j}/{len(S)}]", flush=True)

    dm = [r["delay_main"] for r in rows]
    dd = [r["delay_detour"] for r in rows]
    y = [r["Y"] for r in rows]
    print("\n=== 修正后（逐车基准）===")
    print(f"  n={len(rows)}")
    print(f"  主路超额耗时 中位 {st.median(dm):.2f}  范围 [{min(dm):.2f}, {max(dm):.2f}]")
    print(f"  绕行超额耗时 中位 {st.median(dd):.2f}  范围 [{min(dd):.2f}, {max(dd):.2f}]")
    print(f"  Y 中位 {st.median(y):.2f}  范围 [{min(y):.2f}, {max(y):.2f}]")
    ok = st.median(y) <= st.median(dm) + 1e-9
    print(f"  不等式 Y中位 <= 主路超额中位: {st.median(y):.2f} <= {st.median(dm):.2f}  "
          f"{'✅ 成立' if ok else '❌ 仍违反'}")
    neg = [r for r in rows if r["delay_detour"] < -0.2]
    print(f"  绕行超额 < −0.2 s 的车: {len(neg)} / {len(rows)}")
    print(f"  实际净节时 ΔT 中位 {st.median([r['dT'] for r in rows]):.2f} s")

    (OUT / "freeflow_sens.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'freeflow_sens.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
