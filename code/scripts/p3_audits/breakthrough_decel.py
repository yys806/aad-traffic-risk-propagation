"""0.2.2 决定性数值实验：原生 Krauss 下，前车刹车多狠才能造出 DRAC≥3.4？

背景（0.1.9）：Krauss 安全约束把 DRAC 封顶在 b/(1+2bτ/v)。
破界三条前提之一：**前车实际减速超过后车假设的 apparentDecel**。
本脚本直接量化：把前车制动能力从 4.5 一路调到 9.0，看后车（原生 Krauss，apparentDecel=4.5）
的最大 DRAC 怎么变。

【为什么这个实验关键】
如果「前车刹车 8–9 m/s²」能在原生 SUMO 里稳定产生 DRAC≥3.4，
那区域场景就有了一条**不靠加视距门、不靠关安全校验**的合法破界路径。
如果连 9.0 都造不出来，说明这条路也死了。

【设计】
- 单车道直路，前车在后车前方 GAP 处
- 两车同速 30 m/s 起步，稳态跟驰
- t=BRAKE_T 时前车以 LEAD_DECEL 全力制动（setDecel + setSpeed 逐步降）
- 后车用**原生 Krauss**（不接管），apparentDecel 保持默认 = 4.5
- 记录后车逐帧 DRAC（用几何净距）
- 扫 LEAD_DECEL = 4.5 / 6.0 / 7.0 / 8.0 / 9.0
- 扫 GAP = 40 / 60 / 80 m（不同跟驰间距）

【预期（跑前写死，R08）】
按 0.1.9 的解析式，前车减速不超过 apparentDecel 时上界 3.05（30 m/s、前车停）。
前车减速**超过** 4.5 时上界应被突破。
我预测 LEAD_DECEL=8.0、GAP=40 时能出 DRAC>3.4。
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
OUT = ROOT / "code/outputs/analysis/P3_breakthrough"

V0 = 30.0
TAU = 1.584
MIN_GAP = 2.5
VEH_LEN = 5.0
STEP = 0.1
T_END = 40.0
BRAKE_T = 10.0
DRAC_THR = 3.4


def build(work: Path, tag: str, gap0: float, seed: int = 20261120) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    net = ('<net version="1.20"><edge id="e" from="a" to="b" numLanes="1" speed="40">'
           '<lane id="e_0" index="0" speed="40" length="9000" '
           'shape="0.00,0.00 9000.00,0.00"/></edge>'
           '<junction id="a" type="dead_end" x="0" y="0"/>'
           '<junction id="b" type="dead_end" x="9000" y="0"/></net>')
    (work / "net.net.xml").write_text(net, encoding="utf-8")

    # 后车在 2000 m，前车在其前方 gap0 + 车长处
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


def run_one(gap0: float, lead_decel: float, tag: str) -> dict:
    work = OUT / f"_s_{tag}"
    cfg = build(work, tag, gap0)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "none", "--time-to-teleport", "-1"])
    rows = []
    max_drac, min_gap, drac_at = 0.0, float("inf"), None
    contact_v = None
    braking = False
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)
            # 前车按指定减速度制动（直接写速度，绕开它自己的跟驰模型）
            ids = traci.vehicle.getIDList()
            if t >= BRAKE_T and "lead" in ids:
                if not braking:
                    traci.vehicle.setSpeedMode("lead", 0)
                    braking = True
                v_lead = traci.vehicle.getSpeed("lead")
                v_new = max(0.0, v_lead - lead_decel * STEP)
                traci.vehicle.setSpeed("lead", v_new)
            traci.simulationStep()
            ids = traci.vehicle.getIDList()
            # 车辆是逐步插入的，未齐时继续推进仿真，不能 break
            if "foll" not in ids or "lead" not in ids:
                continue
            xf = traci.vehicle.getLanePosition("foll")
            vf = traci.vehicle.getSpeed("foll")
            xl = traci.vehicle.getLanePosition("lead")
            vl = traci.vehicle.getSpeed("lead")
            g = (xl - xf) - VEH_LEN
            min_gap = min(min_gap, g)
            c = vf - vl
            if g > 0 and c > 0:
                d = c * c / (2 * g)
                if d > max_drac:
                    max_drac, drac_at = d, t
            if g < 0 and contact_v is None:
                contact_v = round(vf, 2)
            rows.append({"t": t, "g": round(g, 3), "vf": round(vf, 3),
                         "vl": round(vl, 3), "c": round(c, 3)})
    finally:
        traci.close()

    return {"tag": tag, "gap0": gap0, "lead_decel": lead_decel,
            "max_drac": round(max_drac, 3), "at_t": drac_at,
            "min_gap": (None if min_gap == float("inf") else round(min_gap, 3)),
            "contact_v": contact_v,
            "exceeds": bool(max_drac >= DRAC_THR)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaps", nargs="+", type=float, default=[40.0, 60.0, 80.0])
    ap.add_argument("--decels", nargs="+", type=float,
                    default=[4.5, 6.0, 7.0, 8.0, 9.0])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    results = []
    print(f"{'GAP':>6} {'前车减速':>9} {'最大DRAC':>10} {'峰值时刻':>9} {'最小净距':>10} {'超3.4':>6}")
    for g0 in args.gaps:
        for dec in args.decels:
            tag = f"g{int(g0)}_d{str(dec).replace('.','p')}"
            r = run_one(g0, dec, tag)
            results.append(r)
            print(f"{g0:>6.0f} {dec:>9.1f} {r['max_drac']:>10.3f} "
                  f"{str(r['at_t']):>9} {str(r['min_gap']):>10} "
                  f"{'是' if r['exceeds'] else '否':>6}", flush=True)

    (OUT / "breakthrough.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for r in results if r["exceeds"])
    print(f"\n{len(results)} 组里 {n_ok} 组超过 3.4")
    print(f"written: {OUT/'breakthrough.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
