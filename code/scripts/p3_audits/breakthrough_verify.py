"""0.2.2b 短核验（GPT 第八十轮 Q5 第 1 条要求）。

核对五件事：
1. 制动开始时（BRAKE_T 前一步）两车的实际净距与速度
2. 源车实际减速度（从速度轨迹反算，不只看设定值）
3. DRAC 分母口径（几何净距 vs getLeader + minGap）
4. 响应车安全配置（speedMode 是否被改过、apparentDecel 实际取值）
5. 碰撞日志（是否有 SUMO 的 collision 输出）

用法：python breakthrough_verify.py --gap 40 --decel 9.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_breakthrough"
V0 = 30.0
TAU = 1.584
MIN_GAP = 2.5
VEH_LEN = 5.0
STEP = 0.1
T_END = 40.0
BRAKE_T = 10.0
DRAC_THR = 3.4


def build(work: Path, gap0: float, seed: int = 20261120) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           '<lane id="e_0" index="0" speed="40" length="9000" '
           'shape="0.00,0.00 9000.00,0.00"/></edge>'
           '<junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (work / "net.net.xml").write_text(net, encoding="utf-8")
    x_foll = 2000.0
    x_lead = x_foll + gap0 + VEH_LEN
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{TAU}" length="5" minGap="{MIN_GAP}" maxSpeed="{V0}" speedFactor="1"'
          f' actionStepLength="{STEP}"/>')
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
           f' departSpeed="{V0}" departLane="0"/>'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="{x_foll:.2f}"'
           f' departSpeed="{V0}" departLane="0"/></routes>')
    (work / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=float, default=40.0)
    ap.add_argument("--decel", type=float, default=9.0)
    args = ap.parse_args()

    work = OUT / f"_verify_g{int(args.gap)}_d{str(args.decel).replace('.','p')}"
    cfg = build(work, args.gap)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1",
                 "--collision-output", str(work / "collisions.xml")])
    c = traci.constants

    log = []
    at_brake = None
    max_drac, drac_frames = 0.0, []
    braking = False
    v_lead_series = []
    collision_count = 0
    foll_mode_before = None
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)
            ids = traci.vehicle.getIDList()
            if t >= BRAKE_T and "lead" in ids:
                if not braking:
                    foll_mode_before = traci.vehicle.getSpeedMode("foll") if "foll" in ids else None
                    traci.vehicle.setSpeedMode("lead", 0)
                    braking = True
                v_lead = traci.vehicle.getSpeed("lead")
                traci.vehicle.setSpeed("lead", max(0.0, v_lead - args.decel * STEP))
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if traci.simulation.getCollisions():
                collision_count = len(traci.simulation.getCollisions())
            if "foll" not in ids or "lead" not in ids:
                continue
            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = traci.vehicle.getLanePosition("lead")
            vl = traci.vehicle.getSpeed("lead")
            g = (xl - xf) - VEH_LEN
            gap_leader = traci.vehicle.getLeader("foll", 400.0)
            v_lead_series.append((round(t, 1), round(vl, 4)))

            # 制动起点前一步的状态
            if at_brake is None and t >= BRAKE_T:
                at_brake = {"t": t, "gap_geometric": round(g, 4),
                            "gap_getLeader": (None if gap_leader is None
                                              else round(gap_leader[1], 4)),
                            "v_foll": round(vf, 4), "v_lead": round(vl, 4),
                            "foll_speedMode": traci.vehicle.getSpeedMode("foll"),
                            "lead_speedMode": traci.vehicle.getSpeedMode("lead")}
            cc = vf - vl
            if g > 0 and cc > 0:
                d = cc * cc / (2 * g)
                if d > max_drac:
                    max_drac = d
                if d >= DRAC_THR:
                    drac_frames.append({"t": round(t, 2), "g": round(g, 4),
                                        "c": round(cc, 4), "drac": round(d, 4)})
            log.append({"t": round(t, 2), "g": round(g, 4), "vf": round(vf, 4),
                        "vl": round(vl, 4)})
    finally:
        traci.close()

    # 源车实际减速度：从速度序列反算（制动后每 0.1 s 的差值）
    actual_dec = []
    for i in range(1, len(v_lead_series)):
        t0, v0 = v_lead_series[i - 1]
        t1, v1 = v_lead_series[i]
        if t0 >= BRAKE_T and abs(t1 - t0 - STEP) < 1e-6 and v0 > 0:
            actual_dec.append((v0 - v1) / STEP)
    mean_dec = (sum(actual_dec) / len(actual_dec)) if actual_dec else None

    out = {
        "gap0": args.gap, "decel_set": args.decel,
        "at_brake_start": at_brake,
        "actual_lead_decel_mean": (None if mean_dec is None else round(mean_dec, 4)),
        "actual_lead_decel_min": (round(min(actual_dec), 4) if actual_dec else None),
        "actual_lead_decel_max": (round(max(actual_dec), 4) if actual_dec else None),
        "max_drac": round(max_drac, 4),
        "n_frames_over_thr": len(drac_frames),
        "first_over_thr": drac_frames[0] if drac_frames else None,
        "collision_count": collision_count,
        "foll_speedMode_at_brake": (None if at_brake is None else at_brake["foll_speedMode"]),
        "min_gap_seen": round(min(x["g"] for x in log), 4) if log else None,
    }
    (work / "verify.json").write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                      encoding="utf-8")

    print(f"=== 短核验：初始净距 {args.gap} m、设定源车减速 {args.decel} ===")
    print(f"【1】制动起点实际状态：")
    for k, v in (at_brake or {}).items():
        print(f"      {k} = {v}")
    print(f"【2】源车实际减速度（从速度轨迹反算）："
          f"mean={out['actual_lead_decel_mean']} "
          f"min={out['actual_lead_decel_min']} max={out['actual_lead_decel_max']}")
    print(f"【3】DRAC 分母口径：几何 {out['at_brake_start']['gap_geometric'] if at_brake else '?'} m "
          f"vs getLeader {out['at_brake_start']['gap_getLeader'] if at_brake else '?'} m")
    print(f"【4】响应车 speedMode（制动时）：{out['foll_speedMode_at_brake']}"
          f"　（0 = 全部安全校验关闭；默认 31）")
    print(f"【5】碰撞：{out['collision_count']} 次；最小净距 {out['min_gap_seen']} m")
    print(f"\n最大 DRAC {out['max_drac']}；超阈帧 {out['n_frames_over_thr']} 个；"
          f"首帧 {out['first_over_thr']}")
    print(f"written: {work/'verify.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())