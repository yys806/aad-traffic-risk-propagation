"""P3 路线乙 · 容量校准：测出并道瓶颈的实际放行能力

阶段：P3 ｜ GPT 第四十四轮 Q6「容量用校准批次估计，不按 DRAC 修订」
脚本：code/scripts/run_p3_capacity.py
产物：code/outputs/analysis/P3_capacity/calib.json

为什么要这一步：
  首次试跑用 2100 辆/h，队列根本没长出来——说明这个瓶颈的通行能力高于 2100。
  GPT 给的参考区间是 1550–1800 辆/h，与实际不符时**必须按预先写明的需求/容量规则修订**，
  不能反过来按 DRAC 调。

做法：
  固定 2 车道→1 车道、固定车型与跟驰参数，只扫**恒定需求**，
  看哪个需求开始出现持续队列。判据是「走廊内平均速度明显下降 + 队尾出现」。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

traci = load_traci()
SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
NETCONVERT = str(Path(SUMO).parent / "netconvert.exe")

LEN_A, LEN_B = 8000.0, 2000.0
STEP = 0.5
DUR = 1800.0            # 30 min 恒定需求
OBS_LO, OBS_HI = 1000.0, 8000.0


def build_net(tmp: Path) -> None:
    (tmp / "n.nod.xml").write_text(
        '<nodes><node id="a" x="0" y="0" type="priority"/>'
        f'<node id="m" x="{LEN_A:.0f}" y="0" type="priority"/>'
        f'<node id="b" x="{LEN_A+LEN_B:.0f}" y="0" type="priority"/></nodes>',
        encoding="utf-8")
    (tmp / "e.edg.xml").write_text(
        f'<edges><edge id="up" from="a" to="m" priority="1" numLanes="2" speed="27.78"/>'
        f'<edge id="down" from="m" to="b" priority="1" numLanes="1" speed="27.78"/></edges>',
        encoding="utf-8")
    r = subprocess.run([NETCONVERT, "-n", str(tmp / "n.nod.xml"), "-e", str(tmp / "e.edg.xml"),
                        "-o", str(tmp / "net.net.xml"), "--no-turnarounds", "true"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:1500])


def routes_xml(rate: float) -> str:
    car = ('<vType id="car" vClass="passenger" length="5" minGap="2.5" maxSpeed="26.39"'
           ' accel="2.6" decel="4.5" sigma="0" tau="1.1" speedFactor="normc(1,0.06,0.94,1.12)"/>')
    hv = ('<vType id="hv" vClass="truck" length="12" minGap="2.5" maxSpeed="23.61"'
          ' accel="1.3" decel="3.5" sigma="0" tau="1.4" speedFactor="normc(1,0.05,0.90,1.08)"/>')
    return (f'<routes>{car}{hv}<route id="r" edges="up down"/>'
            f'<flow id="c" type="car" route="r" begin="0" end="{DUR:.0f}"'
            f' period="{3600.0/(rate*0.9):.3f}" departLane="random" departSpeed="max"/>'
            f'<flow id="h" type="hv" route="r" begin="0" end="{DUR:.0f}"'
            f' period="{3600.0/(rate*0.1):.3f}" departLane="random" departSpeed="max"/></routes>')


def run_rate(rate: float, seed: int = 20261120) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="cap_"))
    try:
        build_net(tmp)
        (tmp / "r.rou.xml").write_text(routes_xml(rate), encoding="utf-8")
        (tmp / "c.cfg").write_text(
            f"""<configuration>
  <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
  <time><begin value="0"/><end value="{DUR}"/><step-length value="{STEP}"/></time>
  <processing><time-to-teleport value="300"/></processing>
  <random_number><seed value="{seed}"/></random_number>
  <report><no-step-log value="true"/></report></configuration>""", encoding="utf-8")
        traci.start([SUMO, "-c", str(tmp / "c.cfg"), "--no-warnings"])
        vs, tails, arrived = [], [], 0
        while traci.simulation.getTime() < DUR:
            t = traci.simulation.getTime()
            if t > DUR * 0.4 and abs(t % 60.0) < 1e-9:      # 后 60% 每 1 min 采样
                xs = np.array([traci.vehicle.getPosition(v)[0]
                               for v in traci.vehicle.getIDList()])
                sp = np.array([traci.vehicle.getSpeed(v)
                               for v in traci.vehicle.getIDList()])
                if xs.size > 5:
                    m = (xs >= OBS_LO) & (xs <= OBS_HI)
                    if m.sum() > 5:
                        vs.append(float(sp[m].mean()))
                        slow = xs[m][sp[m] < 2.0]
                        tails.append(float(slow.min()) if slow.size else np.nan)
            traci.simulationStep()
        arrived = traci.simulation.getArrivedNumber()
    finally:
        try:
            traci.close()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)
    v = np.array([x for x in vs if x == x])
    tl = np.array([x for x in tails if x == x])
    return {"demand_vph": rate,
            "v_mean_mps": round(float(v.mean()), 2) if v.size else None,
            "v_p10_mps": round(float(np.percentile(v, 10)), 2) if v.size else None,
            "frac_samples_with_queue": round(float(tl.size / max(len(vs), 1)), 3),
            "min_tail_x": round(float(tl.min()), 0) if tl.size else None,
            "arrived": int(arrived),
            "throughput_vph": round(arrived / DUR * 3600, 0)}


def main() -> int:
    rates = [1400, 1800, 2100, 2400, 2600, 2800, 3000, 3200]
    out = {"dur_s": DUR, "step_s": STEP, "results": []}
    print(f"{'需求':>7} {'均速':>7} {'p10速度':>8} {'出现队列比例':>12} {'最远队尾':>9} {'实际吞吐':>9}")
    print("-" * 62)
    for r in rates:
        d = run_rate(r)
        out["results"].append(d)
        print(f"{r:>7} {str(d['v_mean_mps']):>7} {str(d['v_p10_mps']):>8} "
              f"{d['frac_samples_with_queue']:>12.0%} {str(d['min_tail_x']):>9} "
              f"{d['throughput_vph']:>9.0f}", flush=True)
    dst = Path("code/outputs/analysis/P3_capacity")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "calib.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {dst / 'calib.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())