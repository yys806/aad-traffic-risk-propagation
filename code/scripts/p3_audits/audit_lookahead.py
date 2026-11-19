"""0.0.2 信息路径审计（简化版）：原生模型到底能「看见」多远的前车。

背景：我判断「仿真里没有视距限制 → 驾驶员全知 → 消息无价值」，
      GPT 第五十轮指出这条推断未被证明——原生跟驰可能只用局部前车，
      队尾信息是逐车传过来的，不是直接进入本车决策。
      它要求先做信息路径审计，不要先假设再改模型。

本探针直接测一件事：
  一辆车以 30 m/s 行驶，前方 D 米处停着一辆车（静止）。
  它从多远开始减速？如果它在很远处就减速，说明它能「看见」很远的静止障碍；
  如果它直到很近才减速，说明原生模型的前视范围有限。

扫 D = 60 / 100 / 150 / 250 / 400 / 800 / 1500 m。
记录：起刹时刻、起刹时与前车的净距、是否撞上、最大减速度。

产物：code/outputs/analysis/P3_info_path/lookahead.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_info_path"

V0 = 30.0
TAU = 1.584
DECEL = 4.5
VEH_LEN = 5.0
STEP = 0.05
T_END = 60.0
BRAKE_THR = 0.3


def run_one(gap_net: float) -> dict:
    tmp = OUT / f"_s_D{int(gap_net)}"
    tmp.mkdir(parents=True, exist_ok=True)
    net = (f'<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           f'<lane id="e_0" index="0" speed="40" length="6000" shape="0.00,0.00 6000.00,0.00"/>'
           f'</edge><junction id="a" type="dead_end" x="0" y="0"/>'
           f'<junction id="b" type="dead_end" x="6000" y="0"/></net>')
    (tmp / "net.net.xml").write_text(net, encoding="utf-8")
    x_lead = 1000.0 + gap_net + VEH_LEN
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="{DECEL}" sigma="0"'
          f' tau="{TAU}" length="5" minGap="2.5" maxSpeed="{V0}" speedFactor="1"'
          f' actionStepLength="0.05"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
           f' departSpeed="0" departLane="0"/>'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="1000.00"'
           f' departSpeed="{V0}" departLane="0"/></routes>')
    (tmp / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = tmp / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    brake_t = None
    gap_at_brake = None
    min_gap, max_dec = np.inf, 0.0
    v_prev = V0
    n_lead_seen = 0
    try:
        for k in range(int(T_END / STEP)):
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "foll" not in ids:
                break
            vf = traci.vehicle.getSpeed("foll")
            xf = traci.vehicle.getLanePosition("foll")
            dec = (v_prev - vf) / STEP          # 由速度差分求减速，避开 getAcceleration 的怪行为
            v_prev = vf
            if "lead" in ids:
                n_lead_seen += 1
                xl = traci.vehicle.getLanePosition("lead")
                g = (xl - xf) - VEH_LEN
                min_gap = min(min_gap, g)
                if brake_t is None and dec > BRAKE_THR:
                    brake_t = round(k * STEP, 2)
                    gap_at_brake = g
            max_dec = max(max_dec, dec)
    finally:
        traci.close()
    return {"gap_initial_m": gap_net, "brake_t": brake_t,
            "gap_at_brake_m": (None if gap_at_brake is None else round(gap_at_brake, 2)),
            "min_gap_m": round(float(min_gap), 2),
            "max_decel": round(float(max_dec), 2),
            "collided": bool(min_gap < -0.05), "lead_frames": n_lead_seen}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"前车静止，后车 {V0} m/s，τ={TAU}：它从多远开始减速？", flush=True)
    print(f"{'初始净距':>9} {'起刹时刻':>9} {'起刹时净距':>11} {'最小净距':>9} "
          f"{'最大减速':>9} {'撞':>3}", flush=True)
    rows = []
    for d in [60.0, 100.0, 150.0, 250.0, 400.0, 800.0, 1500.0]:
        r = run_one(d)
        rows.append(r)
        print(f"{r['gap_initial_m']:>9.0f} {str(r['brake_t']):>9} "
              f"{str(r['gap_at_brake_m']):>11} {r['min_gap_m']:>9} "
              f"{r['max_decel']:>9} {'是' if r['collided'] else '否':>3}", flush=True)
    (OUT / "lookahead.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print(f"\nwritten: {OUT/'lookahead.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
