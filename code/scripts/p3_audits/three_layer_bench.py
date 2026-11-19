"""0.0.3 有限视距台架：行为层只看得见 R 米，安全层看得见真值，两个日志分开记。

依据（GPT 第五十轮 Q2/Q3）：
  - 不要把 driverstate 当视距用（那是「估错」，不是「看不见」）
  - 主实验应**显式限制行为层可观测到的线索**
  - 从 Python 过滤 getLeader **不会**让 SUMO 原生跟驰忘掉前车
    → 因此用 speedMode=0 完全接管速度，自己实现两层
  - 分别记录：线索何时可见 / 何时被用于决策 / 制动力何时建立
  - 保留原生 Krauss 的那一组另跑（本脚本是「有限感知机制组」）

结构：
  leader   —— 静止（模拟已停住的队尾），或按给定曲线制动
  follower —— 由本脚本完全接管（speedMode=0）
      行为层：只有当与前车净距 ≤ R 时才「看见」它，用舒适制动能力算安全速度；
              看不见时维持期望速度。
      安全层（可选）：用真值净距与紧急制动能力算硬安全速度，若行为指令超出则裁剪并记录。

输出：逐帧日志 + 汇总（起刹时刻、最小净距、是否撞、安全层抢先次数）

用法：python three_layer_bench.py --R 150 --gap 400
      python three_layer_bench.py --R inf --gap 400 --safety
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_three_layer"

# ---- 车辆参数 ----
V0 = 30.0            # 期望速度 m/s
B_COMF = 4.5         # 舒适/最大常规制动 m/s²
B_EMERG = 9.0        # 紧急制动上限 m/s²
ACC_MAX = 2.6        # 最大加速度
TAU_C = 1.584        # 期望车头时距（0.0.2 标定）
MIN_GAP = 2.5
VEH_LEN = 5.0
STEP = 0.05
T_END = 60.0
BRAKE_THR = 0.3      # 减速度超过此值记为「制动力已建立」


def safe_speed(gap: float, v_lead: float, tau: float, b: float) -> float:
    """Krauss 风格安全速度：保证以 b 减速时不会撞上以 v_lead 行的前车。"""
    if gap <= 0:
        return 0.0
    disc = b * b * tau * tau + v_lead * v_lead + 2.0 * b * gap
    return -b * tau + math.sqrt(max(disc, 0.0))


def run(R: float, gap_init: float, use_safety: bool, lead_brake_t: float | None,
        seed: int, tag: str) -> dict:
    tmp = OUT / f"_s_{tag}"
    tmp.mkdir(parents=True, exist_ok=True)
    net = (f'<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           f'<lane id="e_0" index="0" speed="40" length="8000" shape="0.00,0.00 8000.00,0.00"/>'
           f'</edge><junction id="a" type="dead_end" x="0" y="0"/>'
           f'<junction id="b" type="dead_end" x="8000" y="0"/></net>')
    (tmp / "net.net.xml").write_text(net, encoding="utf-8")
    x_lead = 1000.0 + gap_init + VEH_LEN
    lead_v0 = 0.0 if lead_brake_t is None else V0
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="{ACC_MAX}" decel="{B_COMF}" sigma="0"'
          f' tau="{TAU_C}" length="5" minGap="{MIN_GAP}" maxSpeed="{V0}" speedFactor="1"'
          f' actionStepLength="0.05"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
           f' departSpeed="{lead_v0}" departLane="0"/>'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="1000.00"'
           f' departSpeed="{V0}" departLane="0"/></routes>')
    (tmp / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = tmp / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "none", "--time-to-teleport", "-1"])
    log = []
    brake_t = None
    cue_t = None
    n_clip = 0
    min_gap = float("inf")
    try:
        mode_set = False
        for k in range(int(T_END / STEP)):
            t = k * STEP
            # 前车控制（在推进之前施加）。必须每步强制，否则它的跟驰模型会自己起步。
            ids = traci.vehicle.getIDList()
            if "lead" in ids:
                traci.vehicle.setSpeedMode("lead", 0)
                if lead_brake_t is None:
                    traci.vehicle.setSpeed("lead", 0.0)          # 静止队尾
                else:
                    traci.vehicle.setSpeed(
                        "lead", max(V0 - B_COMF * max(0.0, t - lead_brake_t), 0.0))
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "foll" not in ids:
                break
            if not mode_set:
                traci.vehicle.setSpeedMode("foll", 0)   # 完全接管：不做任何内部安全检查
                mode_set = True
            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            if "lead" in ids:
                xl = traci.vehicle.getLanePosition("lead")
                vl = traci.vehicle.getSpeed("lead")
            else:
                xl, vl = float("inf"), 0.0
            gap = (xl - xf) - VEH_LEN
            min_gap = min(min_gap, gap)

            seen = gap <= R                      # 行为层能不能看见
            if seen and cue_t is None:
                cue_t = round(t, 2)
            # 行为层
            v_behav = V0 if not seen else min(V0, safe_speed(gap, vl, TAU_C, B_COMF))
            # 安全层（真值）
            v_safe = safe_speed(gap, vl, 0.0, B_EMERG) if gap < 1e6 else float("inf")
            clipped = False
            v_cmd = v_behav
            # 加速度限幅：行为层只能用舒适制动（B_COMF），紧急制动（B_EMERG）只属于安全层
            if v_cmd > vf:
                v_new = min(v_cmd, vf + ACC_MAX * STEP)
            else:
                v_new = max(v_cmd, vf - B_COMF * STEP)
            if use_safety:
                # 安全层给的是「不许超过 v_safe」，但实际能达到的最低速度受紧急制动能力限制
                v_safety_cmd = max(v_safe, vf - B_EMERG * STEP)
                if v_safety_cmd < v_new - 1e-6:
                    clipped = True
                    n_clip += 1
                v_new = min(v_new, v_safety_cmd)
            traci.vehicle.setSpeed("foll", v_new)

            dec = (vf - v_new) / STEP
            if brake_t is None and dec > BRAKE_THR:
                brake_t = round(t, 2)
            log.append({"t": round(t, 2), "gap": round(gap, 2), "v_ego": round(vf, 2),
                        "v_lead": round(vl, 2), "seen": bool(seen),
                        "v_behav": round(v_behav, 2),
                        "v_safe": (None if v_safe == float("inf") else round(v_safe, 2)),
                        "clipped": clipped})
    finally:
        traci.close()

    return {"tag": tag, "R": R, "gap_init": gap_init, "safety": use_safety,
            "lead_brake_t": lead_brake_t, "cue_t": cue_t, "brake_t": brake_t,
            "min_gap": round(min_gap, 2), "collided": bool(min_gap < -0.05),
            "n_safety_clip_frames": n_clip, "log": log}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", nargs="+", default=["150", "inf"])
    ap.add_argument("--gap", type=float, default=400.0)
    ap.add_argument("--safety", action="store_true")
    ap.add_argument("--seed", type=int, default=20261120)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    print(f"前车静止、后车 {V0} m/s、初始净距 {args.gap} m、安全层={'开' if args.safety else '关'}",
          flush=True)
    print(f"{'R(m)':>7} {'线索时刻':>9} {'起刹时刻':>9} {'最小净距':>9} "
          f"{'撞':>3} {'安全层裁剪帧':>11}", flush=True)
    for Rs in args.R:
        R = float("inf") if Rs == "inf" else float(Rs)
        r = run(R, args.gap, args.safety, None, args.seed, f"R{Rs}_g{int(args.gap)}"
                + ("_s" if args.safety else ""))
        rows.append({k: v for k, v in r.items() if k != "log"})
        print(f"{Rs:>7} {str(r['cue_t']):>9} {str(r['brake_t']):>9} "
              f"{r['min_gap']:>9} {'是' if r['collided'] else '否':>3} "
              f"{r['n_safety_clip_frames']:>11}", flush=True)

    (OUT / f"bench_g{int(args.gap)}{'_s' if args.safety else ''}.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
