"""正对照 v2：按「发现瞬间」而不是「撞车前采样峰值」计算制动需求

阶段：P3 ｜ GPT 第四十二轮 Q1/Q2/Q8 第 1 步
脚本：code/scripts/p3_audits/positive_control_perception_v2.py
产物：code/outputs/analysis/P3_controls/positive_perception_v2.json

修正了什么（v1 的三个错）：
  1. v1 的价格表用「整段轨迹的 DRAC 峰值」。撞车前的峰值在净距趋零时对采样步长极敏感，
     45 m/s² 这类数没有意义。正确做法是算**发现瞬间**的需求：
         a_req = v_det² / (2 · g_det)
  2. v1 在施加减速**之后**才记 DRAC，速度已经降了一帧（0.225 m/s），
     导致实测 3.46 低于解析 3.52。v2 在施加制动**之前**记录发现状态。
  3. v1 只报一个阈值。v2 同时报两条临界线：
        指标线：a_req = 3.4  → v²/(2·3.4)
        物理停车线：a_req = 4.5（车辆能力），零剩余净距 → v²/(2·4.5)
     23.6 m/s 时分别是 81.9 m 与 61.9 m。

另外做时间步长收敛检验（0.05 与 0.025）。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

traci = load_traci()
SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"

VEH_LEN = 5.0
V0 = 23.6
DECEL = 4.5
ACCEL = 2.6
EDGE = 2000.0
LEAD_X = 300.0
A_METRIC = 3.4          # 指标阈值
A_PHYS = 4.5            # 车辆最大制动能力


def net_xml() -> str:
    return f"""<net version="1.20">
  <edge id="e" from="a" to="b" priority="1" numLanes="1" speed="40.00" length="{EDGE}">
    <lane id="e_0" index="0" speed="40.00" length="{EDGE}" shape="0.00,0.00 {EDGE:.0f},0.00"/>
  </edge>
  <junction id="a" type="dead_end" x="0.00" y="0.00"/>
  <junction id="b" type="dead_end" x="{EDGE:.0f}" y="0.00"/>
</net>"""


def routes_xml(v0: float) -> str:
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="{ACCEL}" decel="{DECEL}" sigma="0"'
          f' tau="0.6" length="{VEH_LEN}" minGap="2.5" maxSpeed="{v0:.2f}"/>')
    return (f'<routes>{vt}<route id="r" edges="e"/>'
            f'<vehicle id="L" type="cal" route="r" depart="0" departPos="{LEAD_X:.2f}"'
            f' departSpeed="0.00" departLane="0"/>'
            f'<vehicle id="F" type="cal" route="r" depart="0" departPos="1.00"'
            f' departSpeed="{v0:.2f}" departLane="0"/></routes>')


def run_one(R: float, v0: float = V0, step: float = 0.05) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="posctl2_"))
    try:
        (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
        (tmp / "r.rou.xml").write_text(routes_xml(v0), encoding="utf-8")
        (tmp / "c.cfg").write_text(
            f"""<configuration>
  <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
  <time><begin value="0"/><end value="120"/><step-length value="{step}"/></time>
  <processing><time-to-teleport value="-1"/><collision.action value="none"/></processing>
  <report><no-step-log value="true"/></report></configuration>""", encoding="utf-8")
        traci.start([SUMO, "-c", str(tmp / "c.cfg"), "--no-warnings"])
        traci.simulationStep()
        if "F" not in traci.vehicle.getIDList():
            raise RuntimeError("后车 F 未插入")
        traci.vehicle.setSpeedMode("F", 0)
        vf = v0
        d_det = v_det = a_req = None
        min_gap = 9e9
        braking = False
        while traci.simulation.getTime() < 120:
            if "F" not in traci.vehicle.getIDList():
                break
            xf = traci.vehicle.getPosition("F")[0]
            d = (LEAD_X - xf) - VEH_LEN
            # 关键：在施加减速之前判定「是否刚进入感知范围」，并记录此刻状态
            if not braking and d <= R:
                braking = True
                d_det, v_det = d, vf
                a_req = (v_det * v_det) / (2.0 * d_det) if d_det > 0.01 else float("inf")
            if not braking:
                vf = min(v0, vf + ACCEL * step)
            else:
                vf = max(0.0, vf - DECEL * step)
            traci.vehicle.setSpeed("F", vf)
            if d < min_gap:
                min_gap = d
            traci.simulationStep()
        return {
            "perception_range_m": R, "v0_mps": v0, "step_s": step,
            "gap_at_detection_m": round(d_det, 2) if d_det is not None else None,
            "v_at_detection_mps": round(v_det, 2) if v_det is not None else None,
            "a_req_at_detection_mps2": round(a_req, 2) if a_req is not None else None,
            "min_gap_m": round(min_gap, 2),
            "collided": bool(min_gap < 0),
            "exceeds_metric": bool(a_req is not None and a_req >= A_METRIC),
            "exceeds_physical": bool(a_req is not None and a_req >= A_PHYS),
        }
    finally:
        try:
            traci.close()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    Rs = [40, 50, 60, 70, 80, 90, 100, 120, 150, 200, 300]
    out = {"v0_mps": V0, "a_metric": A_METRIC, "a_phys": A_PHYS,
           "analytic_metric_line_m": round(V0 * V0 / (2 * A_METRIC), 1),
           "analytic_physical_line_m": round(V0 * V0 / (2 * A_PHYS), 1),
           "results": [], "convergence": []}

    print(f"后车初速 {V0:.1f} m/s，队尾静止。")
    print(f"解析：指标线 v²/(2·{A_METRIC}) = {out['analytic_metric_line_m']} m；"
          f"物理停车线 v²/(2·{A_PHYS}) = {out['analytic_physical_line_m']} m\n")
    print(f"{'感知距':>7} {'发现净距':>9} {'发现速度':>9} {'发现时需求':>10} "
          f"{'最小净距':>9} {'撞':>3}")
    print("-" * 58)
    for R in Rs:
        r = run_one(R)
        out["results"].append(r)
        print(f"{R:>7} {r['gap_at_detection_m']:>9.2f} {r['v_at_detection_mps']:>9.2f} "
              f"{r['a_req_at_detection_mps2']:>10.2f} {r['min_gap_m']:>9.2f} "
              f"{'是' if r['collided'] else '否':>3}")

    print("\n时间步长收敛检验（在指标线附近细扫）：")
    for step in (0.05, 0.025):
        for R in (78, 80, 82, 84):
            r = run_one(R, step=step)
            out["convergence"].append(r)
            print(f"  步长 {step:.3f}  R={R:>3}  发现净距 {r['gap_at_detection_m']:>6.2f}  "
                  f"发现时需求 {r['a_req_at_detection_mps2']:>6.2f}  "
                  f"{'超阈' if r['exceeds_metric'] else '未超'}")

    dst = Path("code/outputs/analysis/P3_controls")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "positive_perception_v2.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {dst / 'positive_perception_v2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())