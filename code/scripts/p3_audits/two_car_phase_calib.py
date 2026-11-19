"""0.0.1 两车相位标定：actionStepLength 到底产生多大的「有效制动延迟」。

背景（GPT 第四十八轮 Q2）：
  `actionStepLength` 是**决策更新间隔**，不是「感知到制动」的固定延迟。
  同样的间隔，刺激落在决策更新之前还是之后，观测到的制动延迟不同。
  所以不能把人的反应时间样本直接当成 actionStepLength 的取值，
  必须先把「间隔 → 有效延迟」的映射测出来。

设计（GPT 指定的记录项全部保留）：
  - 两车，初速 30 m/s，前车在前，净距 GAP 米（默认 125 m ≈ 车头距 130 m）
  - 前车在 t=BRAKE_T 起以 4.5 m/s² 匀减速到停（6.67 s）
  - 后车 Krauss，actionStepLength = L，从 t=0 起每 L 秒决策一次
  - 扫相位 φ ∈ {0, 0.2, 0.4, 0.6, 0.8} × L：把前车制动起始时刻设成 k·L + φ·L
    这样刺激相对后车决策时钟的相位是可控的
  - 记录三个时刻：前车制动生效 / 后车决策更新 / 后车实际开始制动（减速度超过阈值）
  - 无刺激对照：前车不制动，确认后车本来不会减速

输出：相位 → 有效延迟 的映射表，供整场实验解释用。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_phase_calib"

V0 = 30.0
DECEL = 4.5
VEH_LEN = 5.0
EDGE = 3000.0
STEP = 0.05
T_END = 40.0
BRAKE_THR = 0.5  # 减速度超过 0.5 m/s² 记为「开始制动」


def build(tmp: Path, L: float, gap_net: float, brake_t: float, lead_brakes: bool, tau: float = 0.6) -> Path:
    net = f"""<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">
<lane id="e_0" index="0" speed="40" length="{EDGE}" shape="0.00,0.00 {EDGE:.2f},0.00"/></edge>
<junction id="a" type="dead_end" x="0" y="0"/>
<junction id="b" type="dead_end" x="{EDGE}" y="0"/></net>"""
    (tmp / "net.net.xml").write_text(net, encoding="utf-8")
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="{DECEL}" sigma="0"'
          f' tau="{tau}" length="5" minGap="2.5" maxSpeed="{V0}" speedFactor="1"'
          f' actionStepLength="{L}"/>')
    x_lead = 500.0 + gap_net + VEH_LEN
    rou = (f'<routes>{vt}<route id="r" edges="e"/>'
           f'<vehicle id="lead" type="c" route="r" depart="0" departPos="{x_lead:.2f}"'
           f' departSpeed="{V0}" departLane="0"/>'
           f'<vehicle id="foll" type="c" route="r" depart="0" departPos="500.00"'
           f' departSpeed="{V0}" departLane="0"/></routes>')
    (tmp / "r.rou.xml").write_text(rou, encoding="utf-8")
    cfg = tmp / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<report><no-step-log value="true"/></report></configuration>',
        encoding="utf-8")
    return cfg


def run_one(tmp: Path, L: float, gap_net: float, brake_t: float, lead_brakes: bool, tau: float = 0.6) -> dict:
    tmp.mkdir(parents=True, exist_ok=True)
    cfg = build(tmp, L, gap_net, brake_t, lead_brakes, tau)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    n = int(round(T_END / STEP))
    hist = []
    actual_brake_t = None
    foll_brake_t = None
    decel_trace = []
    try:
        for k in range(n):
            t = k * STEP
            # 前车：按预设曲线制动（setSpeed 强设速度，不交给跟驰模型）
            if lead_brakes and actual_brake_t is None and t >= brake_t - 1e-9:
                actual_brake_t = t
            if actual_brake_t is not None and "lead" in traci.vehicle.getIDList():
                traci.vehicle.setSpeed("lead", max(V0 - DECEL * (t - actual_brake_t), 0.0))
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            if "lead" in ids:
                vl, vlsp = traci.vehicle.getLanePosition("lead"), traci.vehicle.getSpeed("lead")
            else:
                vl, vlsp = float("nan"), 0.0
            if "foll" in ids:
                vf, vfsp = traci.vehicle.getLanePosition("foll"), traci.vehicle.getSpeed("foll")
                acc = traci.vehicle.getAcceleration("foll")
            else:
                vf, vfsp, acc = float("nan"), 0.0, 0.0
            hist.append((t, vl, vlsp, vf, vfsp, acc))
            decel_trace.append((t, -acc))
            if foll_brake_t is None and acc < -BRAKE_THR:
                foll_brake_t = t
    finally:
        traci.close()
    a = np.array(hist)
    gap = (a[:, 1] - a[:, 3]) - VEH_LEN  # 前车位置 − 后车位置 − 车长
    return {"L": L, "gap_net": gap_net, "brake_t": brake_t,
            "lead_brakes": lead_brakes,
            "actual_brake_t": actual_brake_t,
            "foll_brake_t": foll_brake_t,
            "delay_s": (None if (foll_brake_t is None or actual_brake_t is None)
                        else round(foll_brake_t - actual_brake_t, 3)),
            "min_gap": round(float(np.nanmin(gap)), 2),
            "max_decel": round(float(np.nanmax(-a[:, 5])), 2), "tau": tau,
            "collided": bool(np.nanmin(gap) < -0.05)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", nargs="+", type=float, default=[0.6, 1.0, 1.6])
    ap.add_argument("--phase", nargs="+", type=float, default=[0.0, 0.2, 0.4, 0.6, 0.8],
                    help="相对决策时钟的相位，单位是 L 的倍数")
    ap.add_argument("--gap", type=float, default=125.0, help="初始净距（米）")
    ap.add_argument("--tau", type=float, default=0.6, help="期望车头时距")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    res = []
    print(f"两车相位标定：净距 {args.gap} m，初速 {V0} m/s，前车 {DECEL} m/s² 制动",
          flush=True)

    # 无刺激对照
    for L in args.L:
        c = run_one(OUT / f"_s_ctrl_L{L}_t{args.tau}", L, args.gap, 999.0, False, args.tau)
        print(f"  对照 L={L}: 后车是否减速 {c['foll_brake_t'] is not None}  "
              f"最大减速 {c['max_decel']} m/s²", flush=True)
        res.append({"kind": "control", **c})

    for L in args.L:
        base = int(6 / L) * L  # 取一个较早的决策边界作为基准
        for ph in args.phase:
            bt = base + ph * L
            r = run_one(OUT / f"_s_L{L}_p{ph}_t{args.tau}", L, args.gap, bt, True, args.tau)
            r["phase_frac"] = ph
            res.append({"kind": "stimulus", **r})
            print(f"  L={L} 相位={ph:.1f}L  前车制动@{r['actual_brake_t']}  "
                  f"后车制动@{r['foll_brake_t']}  延迟={r['delay_s']} s  "
                  f"最大减速={r['max_decel']}  最小净距={r['min_gap']}", flush=True)

    (OUT / "phase_calib.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    print(f"\nwritten: {OUT/'phase_calib.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
