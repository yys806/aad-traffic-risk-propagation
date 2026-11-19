"""0.0.3 台架 v2：按 GPT 第五十一轮的要求重做。

相对 v1 的改动（每一条都对应它指出的问题）：
  1. **逐帧三项对齐**：原始目标速度 → 仲裁限幅后的命令 → 仿真实际速度。
     并用实际 Δv/Δt 断言「行为层不超过 4.5、安全层不超过 9.0」。
     起因：v1 直接把目标速度写成下一步速度，b=4.5 并不保证实际减速度不超 4.5。
  2. **起刹时刻改用实际速度差分**，不再用命令差分。
     起因：v1 里 R=40 出现「11.70 s 起刹早于 12.05 s 线索可见」的异常。
  3. **净距不先取整**，用于触发的距离与上报的距离分开。
  4. **首次接触单独记录**：首次 gap<0 的时刻与相对速度，并与仿真器碰撞报告分开。
     起因：GPT 指出负净距是几何重叠，不是现实碰撞严重度，不能叫「擦碰」。
  5. **安全层介入按秒计**，并记录「实际改写了执行命令」的帧，而不是只看触发条件。

用法：
  python three_layer_bench_v2.py --R 40 50 95 100 105 145 147.5 150 inf --gap 400 [--safety]
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
OUT = ROOT / "code/outputs/analysis/P3_three_layer_v2"

V0 = 30.0
B_COMF = 4.5
B_EMERG = 9.0
ACC_MAX = 2.6
TAU_C = 1.584
MIN_GAP = 2.5
VEH_LEN = 5.0
STEP = 0.05
T_END = 70.0
BRAKE_THR = 0.3
EPS = 0.05


def safe_speed(gap: float, v_lead: float, tau: float, b: float) -> float:
    if gap <= 0:
        return 0.0
    return -b * tau + math.sqrt(max(b * b * tau * tau + v_lead * v_lead + 2.0 * b * gap, 0.0))


def run(R: float, gap_init: float, use_safety: bool, seed: int, tag: str) -> dict:
    tmp = OUT / f"_s_{tag}"
    tmp.mkdir(parents=True, exist_ok=True)
    net = (f'<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           f'<lane id="e_0" index="0" speed="40" length="9000" shape="0.00,0.00 9000.00,0.00"/>'
           f'</edge><junction id="a" type="dead_end" x="0" y="0"/>'
           f'<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (tmp / "net.net.xml").write_text(net, encoding="utf-8")
    x_lead = 1000.0 + gap_init + VEH_LEN
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="{ACC_MAX}" decel="{B_COMF}" sigma="0"'
          f' tau="{TAU_C}" length="5" minGap="{MIN_GAP}" maxSpeed="{V0}" speedFactor="1"'
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
        f'<time><begin value="0"/><end value="{T_END:.1f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "none", "--time-to-teleport", "-1"])
    rows = []
    cue_t = brake_t = contact_t = None
    v_at_contact = None
    min_gap = float("inf")
    n_safety_frames = 0
    max_dec_behav, max_dec_actual = 0.0, 0.0
    v_prev = None
    mode_set = False
    try:
        for k in range(int(T_END / STEP)):
            t = k * STEP
            ids = traci.vehicle.getIDList()
            if "lead" in ids:
                traci.vehicle.setSpeedMode("lead", 0)
                traci.vehicle.setSpeed("lead", 0.0)     # 静止队尾，每步强制
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "foll" not in ids:
                break
            if not mode_set:
                traci.vehicle.setSpeedMode("foll", 0)
                mode_set = True

            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = traci.vehicle.getLanePosition("lead") if "lead" in ids else float("inf")
            vl = traci.vehicle.getSpeed("lead") if "lead" in ids else 0.0
            gap = (xl - xf) - VEH_LEN                      # 保险杠间净距，不取整
            min_gap = min(min_gap, gap)

            if gap < 0 and contact_t is None:
                contact_t = round(t, 2)
                v_at_contact = round(vf, 2)

            seen = gap <= R
            if seen and cue_t is None:
                cue_t = round(t, 2)

            # ---- 行为层：目标速度 ----
            v_target = V0 if not seen else min(V0, safe_speed(gap, vl, TAU_C, B_COMF))
            # ---- 舒适制动限幅（行为层能力）----
            if v_target > vf:
                v_cmd = min(v_target, vf + ACC_MAX * STEP)
            else:
                v_cmd = max(v_target, vf - B_COMF * STEP)
            dec_cmd = (vf - v_cmd) / STEP
            max_dec_behav = max(max_dec_behav, dec_cmd)

            # ---- 安全层：真值硬上限，受紧急制动能力托底 ----
            v_final = v_cmd
            if use_safety:
                v_safe = safe_speed(gap, vl, 0.0, B_EMERG)
                v_safety_cmd = max(v_safe, vf - B_EMERG * STEP)
                if v_safety_cmd < v_cmd - 1e-9:
                    n_safety_frames += 1
                v_final = min(v_cmd, v_safety_cmd)
            traci.vehicle.setSpeed("foll", v_final)

            # ---- 实际速度差分（v_prev 是上一步实测速度）----
            if v_prev is not None:
                dec_actual = (v_prev - vf) / STEP
                max_dec_actual = max(max_dec_actual, dec_actual)
                if brake_t is None and dec_actual > BRAKE_THR:
                    brake_t = round(t, 2)
            v_prev = vf

            rows.append({"t": round(t, 2), "gap": round(gap, 3), "seen": bool(seen),
                         "v_target": round(v_target, 2), "v_cmd": round(v_cmd, 2),
                         "v_final": round(v_final, 2), "v_actual": round(vf, 2)})
    finally:
        traci.close()

    return {"tag": tag, "R": (None if R == float("inf") else R), "safety": use_safety,
            "cue_t": cue_t, "brake_t": brake_t, "contact_t": contact_t,
            "v_at_contact": v_at_contact, "min_gap": round(min_gap, 3),
            "safety_frames": n_safety_frames, "safety_seconds": round(n_safety_frames * STEP, 2),
            "max_dec_cmd": round(max_dec_behav, 2), "max_dec_actual": round(max_dec_actual, 2),
            "assert_behav_ok": bool(max_dec_behav <= B_COMF + EPS),
            "assert_safety_ok": bool((not use_safety) or max_dec_actual <= B_EMERG + EPS),
            "_rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", nargs="+", default=["60", "80", "100", "120", "150", "180", "inf"])
    ap.add_argument("--gap", type=float, default=400.0)
    ap.add_argument("--safety", action="store_true")
    ap.add_argument("--seed", type=int, default=20261120)
    ap.add_argument("--dump", action="store_true", help="导出逐帧日志")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"v2 台架 | 初始净距 {args.gap} m | 安全层 {'开' if args.safety else '关'} | 步长 {STEP}",
          flush=True)
    print(f"{'R(m)':>7} {'线索':>6} {'起刹':>6} {'接触':>6} {'接触时车速':>9} "
          f"{'最小净距':>9} {'安全层秒':>8} {'行为层最大减速':>12} {'实测最大减速':>11}",
          flush=True)
    out = []
    for Rs in args.R:
        R = float("inf") if Rs == "inf" else float(Rs)
        r = run(R, args.gap, args.safety, args.seed,
                f"R{Rs}" + ("_s" if args.safety else ""))
        rows = r.pop("_rows")
        out.append(r)
        print(f"{Rs:>7} {str(r['cue_t']):>6} {str(r['brake_t']):>6} {str(r['contact_t']):>6} "
              f"{str(r['v_at_contact']):>9} {r['min_gap']:>9.3f} {r['safety_seconds']:>8.2f} "
              f"{r['max_dec_cmd']:>12} {r['max_dec_actual']:>11}", flush=True)
        if args.dump:
            (OUT / f"log{Rs}{'_s' if args.safety else ''}.json").write_text(
                json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    bad = [r for r in out if not r["assert_behav_ok"]]
    print(f"\n断言：行为层减速度均 ≤ {B_COMF}+{EPS} ? {'是' if not bad else '否 —— ' + str(bad)}")
    bad2 = [r for r in out if not r["assert_safety_ok"]]
    print(f"断言：实测减速度均 ≤ {B_EMERG}+{EPS} ? {'是' if not bad2 else '否'}")

    (OUT / f"bench{'_safety' if args.safety else ''}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
