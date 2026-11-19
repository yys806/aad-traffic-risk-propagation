"""0.0.4 台架 v3：无刺激对照 + 单车消息臂。

依据（GPT 第五十一轮 Q3 实施顺序）：
  1. 先补单车对照：**「没有前车」才是无刺激对照**，静止前车本身就是刺激
  2. 再接单车消息臂：消息让目标信息**提前可用**，但**不改写物理可见时刻**；
     分别记「消息到达 / 首次使用 / 实际起刹」
  3. 先在安全层关闭下检验能否促成有效制动，再开安全层做配对

本脚本做三件事：
  A. 无刺激对照：完全没有前车，后车应一路 30 m/s 不减速（必须为 0）
  B. 消息臂：物理可见距离 R_phys 不变；消息到达后，可用信息距离抬到 R_msg
     —— 关键：这不改变「看得见」的物理事实，只改变「被告知」的信息可用性
  C. 消息到达时刻扫描：找出**最晚还有用的消息到达时刻**（信息价值的物理刻度）

用法：
  python three_layer_bench_v3.py --control
  python three_layer_bench_v3.py --r-phys 60 --r-msg 150 --msg-t 0
  python three_layer_bench_v3.py --r-phys 60 --r-msg 150 --sweep
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_msg_arm"

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


def run(r_phys: float, r_msg: float | None, msg_t: float | None,
        with_leader: bool, use_safety: bool, seed: int, tag: str) -> dict:
    tmp = OUT / f"_s_{tag}"
    tmp.mkdir(parents=True, exist_ok=True)
    net = (f'<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           f'<lane id="e_0" index="0" speed="40" length="9000" shape="0.00,0.00 9000.00,0.00"/>'
           f'</edge><junction id="a" type="dead_end" x="0" y="0"/>'
           f'<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (tmp / "net.net.xml").write_text(net, encoding="utf-8")
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="{ACC_MAX}" decel="{B_COMF}" sigma="0"'
          f' tau="{TAU_C}" length="5" minGap="{MIN_GAP}" maxSpeed="{V0}" speedFactor="1"'
          f' actionStepLength="0.05"/>')
    vehs = (f'<vehicle id="foll" type="c" route="r" depart="0" departPos="1000.00"'
            f' departSpeed="{V0}" departLane="0"/>')
    if with_leader:
        x_lead = 1000.0 + 400.0 + VEH_LEN
        vehs += (f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
                 f' departSpeed="0" departLane="0"/>')
    (tmp / "r.rou.xml").write_text(f'<routes>{vt}<route id="r" edges="e"/>{vehs}</routes>',
                                   encoding="utf-8")
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
    cue_t = use_t = brake_t = contact_t = None
    v_contact = None
    min_gap = float("inf")
    n_safety = 0
    v_prev = None
    max_dec_actual = 0.0
    mode_set = False
    decel_any = 0.0
    try:
        for k in range(int(T_END / STEP)):
            t = k * STEP
            ids = traci.vehicle.getIDList()
            if with_leader and "lead" in ids:
                traci.vehicle.setSpeedMode("lead", 0)
                traci.vehicle.setSpeed("lead", 0.0)
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "foll" not in ids:
                break
            if not mode_set:
                traci.vehicle.setSpeedMode("foll", 0)
                mode_set = True

            vf = traci.vehicle.getSpeed("foll")
            xf = traci.vehicle.getLanePosition("foll")
            if with_leader and "lead" in ids:
                gap = (traci.vehicle.getLanePosition("lead") - xf) - VEH_LEN
                vl = traci.vehicle.getSpeed("lead")
            else:
                gap, vl = float("inf"), 0.0
            min_gap = min(min_gap, gap)
            if gap < 0 and contact_t is None:
                contact_t, v_contact = round(t, 2), round(vf, 2)

            # 物理可见
            seen_phys = gap <= r_phys
            if seen_phys and cue_t is None:
                cue_t = round(t, 2)
            # 消息使信息提前可用（不改写物理可见时刻）
            msg_ok = (r_msg is not None and msg_t is not None and t >= msg_t)
            seen = seen_phys or (msg_ok and gap <= r_msg)
            if msg_ok and gap <= r_msg and use_t is None:
                use_t = round(t, 2)

            v_target = V0 if not seen else min(V0, safe_speed(gap, vl, TAU_C, B_COMF))
            v_cmd = (min(v_target, vf + ACC_MAX * STEP) if v_target > vf
                     else max(v_target, vf - B_COMF * STEP))
            v_final = v_cmd
            if use_safety:
                v_safe = safe_speed(gap, vl, 0.0, B_EMERG) if gap < 1e6 else float("inf")
                v_safety = max(v_safe, vf - B_EMERG * STEP)
                if v_safety < v_cmd - 1e-9:
                    n_safety += 1
                v_final = min(v_cmd, v_safety)
            traci.vehicle.setSpeed("foll", v_final)

            if v_prev is not None:
                dec = (v_prev - vf) / STEP
                max_dec_actual = max(max_dec_actual, dec)
                decel_any = max(decel_any, dec)
                if brake_t is None and dec > BRAKE_THR:
                    brake_t = round(t, 2)
            v_prev = vf
    finally:
        traci.close()

    return {"tag": tag, "r_phys": (None if r_phys == float("inf") else r_phys),
            "r_msg": r_msg, "msg_t": msg_t, "with_leader": with_leader,
            "safety": use_safety, "cue_t": cue_t, "use_t": use_t, "brake_t": brake_t,
            "contact_t": contact_t, "v_at_contact": v_contact,
            "min_gap": (None if min_gap == float("inf") else round(min_gap, 3)),
            "safety_seconds": round(n_safety * STEP, 2),
            "max_dec_actual": round(max_dec_actual, 2),
            "any_decel": round(decel_any, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true", help="无刺激对照：完全没有前车")
    ap.add_argument("--r-phys", type=float, default=60.0)
    ap.add_argument("--r-msg", type=float, default=150.0)
    ap.add_argument("--msg-t", type=float, default=0.0)
    ap.add_argument("--sweep", action="store_true", help="扫消息到达时刻")
    ap.add_argument("--safety", action="store_true")
    ap.add_argument("--seed", type=int, default=20261120)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []

    if args.control:
        print("=== 无刺激对照（完全没有前车）===", flush=True)
        for rp in [60.0, 100.0, float("inf")]:
            r = run(rp, None, None, False, args.safety, args.seed, f"ctl_{int(rp) if rp != float('inf') else 'inf'}")
            rows.append(r)
            print(f"  物理可见 {rp if rp != float('inf') else 'inf'}: 起刹={r['brake_t']} "
                  f"实际最大减速={r['any_decel']}（应为 0）", flush=True)
        ok = all(r["any_decel"] < 0.05 for r in rows)
        print(f"  对照通过？ {'是' if ok else '否 —— 无刺激时不应有任何减速'}")
    else:
        if args.sweep:
            print(f"=== 消息到达时刻扫描（物理可见 {args.r_phys} m，消息给 {args.r_msg} m）===",
                  flush=True)
            print(f"{'消息到达s':>10} {'首次使用s':>10} {'起刹s':>7} {'接触s':>7} "
                  f"{'接触车速':>9} {'最小净距':>9}", flush=True)
            for mt in [0.0, 8.0, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 13.0]:
                r = run(args.r_phys, args.r_msg, mt, True, args.safety, args.seed, f"mt{mt}")
                rows.append(r)
                print(f"{mt:>10.1f} {str(r['use_t']):>10} {str(r['brake_t']):>7} "
                      f"{str(r['contact_t']):>7} {str(r['v_at_contact']):>9} "
                      f"{str(r['min_gap']):>9}", flush=True)
        else:
            print(f"=== 单车消息臂：物理可见 {args.r_phys} m，消息给 {args.r_msg} m ===",
                  flush=True)
            for label, rp, rm, mt in [
                    ("无消息（只能看 60 m）", args.r_phys, None, None),
                    ("有消息（告知 150 m）", args.r_phys, args.r_msg, args.msg_t),
                    ("看得见 150 m（正对照）", args.r_msg, None, None)]:
                r = run(rp, rm, mt, True, args.safety, args.seed,
                        f"arm_{label[:4]}_{mt}")
                rows.append(r)
                print(f"  {label}: 线索={r['cue_t']} 消息起用={r['use_t']} "
                      f"起刹={r['brake_t']} 接触={r['contact_t']} "
                      f"接触车速={r['v_at_contact']} 最小净距={r['min_gap']}", flush=True)

    (OUT / ("control.json" if args.control else
            ("sweep.json" if args.sweep else "arms.json"))).write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
