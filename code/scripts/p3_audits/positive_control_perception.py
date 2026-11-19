"""正对照：高速车接近静止队尾，感知距离决定制动需求

阶段：P3 ｜ GPT 第四十一轮 Q4 要求的正对照
脚本：code/scripts/p3_audits/positive_control_perception.py
产物：code/outputs/analysis/P3_controls/positive_perception.json

为什么这个对照同时是研究设计的核心：
  远端消息的作用，本质上就是**延长后车能"看见"前方队尾的距离**。
  所以「感知距离 → 制动需求」这条曲线，就是信息价值的物理载体。

装置：
  * 单车道，前车静止停在 x=300（代表队尾）
  * 后车从 x=0 以 v0 出发，手动控制（setSpeedMode 0），
    只用以下规则：
       感知距离 R 之外 -> 加速到 v0 并保持
       进入 R 之内   -> 以最大减速度 4.5 m/s² 制动到停
  * 扫 R = 40/60/80/100/120/150/200/300 m
  * 计算整段轨迹的 DRAC = c²/(2g)，报峰值与是否超过 3.4

预期（可解析验算）：
  后车在 R 处才发现队尾，所需减速度约 v0² / (2(R − 车长 − 净距))。
  v0 = 23.6 m/s 时，临界感知距离约 v0²/(2×3.4) ≈ 82 m。
  => R < 约 82 m 应检出高制动需求，R 更大则不应检出。
  这是**可证伪的预测**：如果实跑与解析不符，说明实现有问题。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

traci = load_traci()
SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"

VEH_LEN = 5.0
MINGAP = 2.5
V0 = 23.6
DECEL = 4.5
ACCEL = 2.6
STEP = 0.05
EDGE = 2000.0
LEAD_X = 300.0
DRAC_MAIN = 3.4


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
          f' tau="0.6" length="{VEH_LEN}" minGap="{MINGAP}" maxSpeed="{v0:.2f}"/>')
    return (f'<routes>{vt}<route id="r" edges="e"/>'
            f'<vehicle id="L" type="cal" route="r" depart="0" departPos="{LEAD_X:.2f}"'
            f' departSpeed="0.00" departLane="0"/>'
            f'<vehicle id="F" type="cal" route="r" depart="0" departPos="1.00"'
            f' departSpeed="{v0:.2f}" departLane="0"/></routes>')


def run_one(R: float, v0: float = V0) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="posctl_"))
    try:
        (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
        (tmp / "r.rou.xml").write_text(routes_xml(v0), encoding="utf-8")
        (tmp / "c.cfg").write_text(
            f"""<configuration>
  <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
  <time><begin value="0"/><end value="120"/><step-length value="{STEP}"/></time>
  <processing><time-to-teleport value="-1"/><collision.action value="none"/></processing>
  <report><no-step-log value="true"/></report></configuration>""", encoding="utf-8")
        traci.start([SUMO, "-c", str(tmp / "c.cfg"), "--no-warnings"])
        traci.simulationStep()          # 先步进一步，车辆才会被插入
        if "F" not in traci.vehicle.getIDList():
            raise RuntimeError("后车 F 未插入")
        # 后车完全由我们手动控制，关掉 SUMO 自带的安全校验
        traci.vehicle.setSpeedMode("F", 0)
        vf = v0
        drac_max = 0.0
        min_gap = 9e9
        det_dist = None
        collided = False
        while traci.simulation.getTime() < 120:
            ids = traci.vehicle.getIDList()
            if "F" not in ids:
                break
            xf = traci.vehicle.getPosition("F")[0]
            d = (LEAD_X - xf) - VEH_LEN          # 到前车的净距
            if det_dist is None and d <= R:
                det_dist = d
            if d > R:
                vf = min(v0, vf + ACCEL * STEP)   # 还没看见 -> 加速/保持
            else:
                vf = max(0.0, vf - DECEL * STEP)  # 看见了 -> 全力制动
            traci.vehicle.setSpeed("F", vf)
            min_gap = min(min_gap, d)
            if vf > 0.05 and d > 0.01:
                drac_max = max(drac_max, vf * vf / (2.0 * d))
            traci.simulationStep()
        return {"perception_range_m": R, "v0_mps": v0,
                "detected_at_gap_m": round(det_dist, 2) if det_dist else None,
                "min_gap_m": round(min_gap, 2),
                "drac_max_mps2": round(drac_max, 2),
                "exceeds_main": bool(drac_max >= DRAC_MAIN)}
    finally:
        try:
            traci.close()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    Rs = [40, 60, 80, 100, 120, 150, 200, 300]
    out = {"v0_mps": V0, "drac_main": DRAC_MAIN, "results": []}
    crit = V0 * V0 / (2 * DRAC_MAIN)
    print(f"后车初速 {V0:.1f} m/s（{V0*3.6:.0f} km/h），队尾静止于 x={LEAD_X:.0f}\n")
    print(f"解析预测：临界感知距离 ≈ v²/(2·3.4) = {crit:.1f} m")
    print(f"  => 感知距离 < {crit:.0f} m 时应检出（DRAC ≥ 3.4）；更远则不应检出\n")
    print(f"{'感知距离':>9} {'发现时净距':>10} {'最小净距':>9} {'DRAC峰值':>9} {'超阈':>5}")
    print("-" * 50)
    for R in Rs:
        r = run_one(R)
        out["results"].append(r)
        print(f"{R:>9} {str(r['detected_at_gap_m']):>10} {r['min_gap_m']:>9.2f} "
              f"{r['drac_max_mps2']:>9.2f} {'是' if r['exceeds_main'] else '否':>5}")
    out["analytic_critical_range_m"] = round(crit, 1)

    # 核对与解析是否一致
    ok = all(
        (r["perception_range_m"] < crit) == r["exceeds_main"]
        for r in out["results"] if abs(r["perception_range_m"] - crit) > 15
    )
    out["matches_analytic"] = ok
    print(f"\n与解析预测一致：{'是' if ok else '否（需查实现）'}")

    dst = Path("code/outputs/analysis/P3_controls")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "positive_perception.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written: {dst / 'positive_perception.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())