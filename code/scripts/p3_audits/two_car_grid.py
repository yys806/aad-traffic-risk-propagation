"""双车对照：固定 tau 变净距 / 固定净距变 tau，看哪个机制在放大低 TTC

阶段：P3 ｜ GPT 第四十轮 Q7 第 2 步
脚本：code/scripts/p3_audits/two_car_grid.py
产物：code/outputs/analysis/P3_two_car/grid.json + 文本表

要分开回答两件事（GPT 原话）：
  A. 「短净距是否放大低 TTC」
  B. 「改 tau 后完整场景结果是否改变」——本脚本只回答 A 与 tau 的直接作用，
     不代替区域结果。

装置：
  * 两辆车在同一条单车道，后车在 x=0，前车在 x = 净距 + 车长
  * 同初速 v0（取 NGSIM 80–105 层中位速度）
  * t = 5 s 时前车以 4.5 m/s² 制动到停并保持
  * 后车用 Krauss 跟驰，actionStepLength 0.6 s
  * 记录：最小净距、最小 TTC、是否碰撞、碰撞时刻（相对制动开始）

口径与主场景一致：净距 = 前车位置 − 本车位置 − 车长；
TTC = 净距 / 闭合速度，只计闭合为正。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]      # 本脚本在 code/scripts/p3_audits/ 下
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

traci = load_traci()
SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"

VEH_LEN = 5.0
MINGAP = 2.5
DECEL = 4.5
REACT = 0.6
V0 = 23.6               # m/s（≈85 km/h，NGSIM 80–105 层中位）
T_BRAKE = 5.0
T_END = 30.0
STEP = 0.05
EDGE = 3000.0


def net_xml() -> str:
    return f"""<net version="1.20">
  <edge id="e" from="a" to="b" priority="1" numLanes="1" speed="40.00" length="{EDGE}">
    <lane id="e_0" index="0" speed="40.00" length="{EDGE}" shape="0.00,0.00 {EDGE:.0f},0.00"/>
  </edge>
  <junction id="a" type="dead_end" x="0.00" y="0.00"/>
  <junction id="b" type="dead_end" x="{EDGE:.0f}" y="0.00"/>
</net>"""


def routes_xml(gap: float, tau: float, v0: float) -> str:
    lead_x = gap + VEH_LEN
    # maxSpeed 必须锁成 v0，否则两车在制动前会一路加速，初速守不住
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="{DECEL}" sigma="0"'
          f' tau="{tau}" length="{VEH_LEN}" minGap="{MINGAP}" maxSpeed="{v0:.2f}"'
          f' actionStepLength="{REACT}"/>')
    return (f'<routes>{vt}<route id="r" edges="e"/>'
            f'<vehicle id="L" type="cal" route="r" depart="0" departPos="{lead_x:.2f}"'
            f' departSpeed="{v0:.2f}" departLane="0"/>'
            f'<vehicle id="F" type="cal" route="r" depart="0" departPos="10.00"'
            f' departSpeed="{v0:.2f}" departLane="0"/></routes>')


def run_one(gap: float, tau: float, v0: float = V0) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="twocar_"))
    try:
        (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
        (tmp / "r.rou.xml").write_text(routes_xml(gap, tau, v0), encoding="utf-8")
        (tmp / "c.cfg").write_text(
            f"""<configuration>
  <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
  <time><begin value="0"/><end value="{T_END}"/><step-length value="{STEP}"/></time>
  <processing><time-to-teleport value="-1"/><collision.action value="none"/></processing>
  <report><no-step-log value="true"/></report></configuration>""", encoding="utf-8")
        traci.start([SUMO, "-c", str(tmp / "c.cfg"), "--no-warnings"])
        min_gap = 9e9
        min_ttc = 9e9
        collided = False
        t_coll = None
        brake_done = False
        ttc_at_min_gap = None
        v_f_at_min_ttc = None
        v_l_at_min_ttc = None
        while traci.simulation.getTime() < T_END:
            t = traci.simulation.getTime()
            # 前车制动
            if t >= T_BRAKE and not brake_done:
                if "L" in traci.vehicle.getIDList():
                    traci.vehicle.setSpeed("L", max(0.0, traci.vehicle.getSpeed("L") - DECEL * STEP))
            ids = traci.vehicle.getIDList()
            if "L" in ids and "F" in ids:
                xl = traci.vehicle.getPosition("L")[0]
                xf = traci.vehicle.getPosition("F")[0]
                vl = traci.vehicle.getSpeed("L")
                vf = traci.vehicle.getSpeed("F")
                g = (xl - xf) - VEH_LEN
                if g < min_gap:
                    min_gap = g
                dv = vf - vl
                if g > 0.01 and dv > 0.05:
                    ttc = g / dv
                    if ttc < min_ttc:
                        min_ttc = ttc
                        v_f_at_min_ttc = vf
                        v_l_at_min_ttc = vl
            elif "F" not in ids and min_gap < 9e8:
                pass
            if traci.simulation.getCollisions():
                cols = [c for c in traci.simulation.getCollisions()
                        if {c.collider, c.victim} == {"F", "L"}]
                if cols and not collided:
                    collided = True
                    t_coll = t
            traci.simulationStep()
        return {"gap_init_m": gap, "tau_s": tau, "v0_mps": v0,
                "min_gap_m": round(min_gap, 2) if min_gap < 9e8 else None,
                "min_ttc_s": round(min_ttc, 3) if min_ttc < 9e8 else None,
                "v_follower_at_min_ttc_mps": round(v_f_at_min_ttc, 2) if v_f_at_min_ttc is not None else None,
                "v_leader_at_min_ttc_mps": round(v_l_at_min_ttc, 2) if v_l_at_min_ttc is not None else None,
                "collided": collided,
                "t_collision_rel_brake_s": round(t_coll - T_BRAKE, 2) if t_coll else None}
    finally:
        try:
            traci.close()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    gaps = [10, 15, 20, 25, 30, 40, 50, 60]
    taus = [0.6, 0.9, 1.0, 1.2, 1.5, 1.8]
    out = {"v0_mps": V0, "decel": DECEL, "react_s": REACT,
           "t_brake_s": T_BRAKE, "results": []}

    print(f"初速 {V0:.1f} m/s ({V0*3.6:.0f} km/h)，前车 t={T_BRAKE}s 起以 {DECEL} m/s² 制动到停\n")
    header = "净距\\tau " + "".join(f"{t:>13.1f}" for t in taus)
    print(header)
    print("-" * len(header))

    for g in gaps:
        row = {}
        cells = []
        for tau in taus:
            r = run_one(g, tau)
            out["results"].append(r)
            row[f"{tau}"] = r
            if r["collided"]:
                cells.append(f"{'撞':>13}")
            else:
                cells.append(f"{r['min_ttc_s']:>13.2f}" if r["min_ttc_s"] else f"{'-':>13}")
        out.setdefault("table", {})[f"{g}"] = row
        print(f"{g:>7}   " + "".join(cells), flush=True)

    print("\n表内数字 = 最小 TTC（秒）；「撞」= 发生碰撞")
    dst = Path("code/outputs/analysis/P3_two_car")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "grid.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {dst / 'grid.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())