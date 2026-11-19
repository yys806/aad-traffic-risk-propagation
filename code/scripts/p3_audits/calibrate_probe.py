"""0.0.5 第 4 步：预测器校准（探测车查表法）。

依据 GPT 第五十四轮 Q3 —— 首选做法不是拟合 p_block / D / 容量，
而是用**独立校准集**冻结一张「条件平均剩余行程时间差」表：

  Y = (T_主 − T_绕) + 50.1   （自由流时 Y = 0；主路更慢时 Y > 0）
  选绕行  ⟺  Ê[Y | B, M] > 50.1  ⟺  T_主 > T_绕

做法：在相同的背景条件下，从最后可改道点放一辆探测车，
分别沿主路与绕行走完到终点，实测两条路的剩余用时。
背景车辆使用预先固定的参考策略（全部走主路）。

B = 预先规定、少量、**可用的**信息分箱：
    堵塞世界：按「事件年龄」（决策时刻 − 事件发生时刻）分桶
    畅通世界：单一桶
  不传队列长度、不传未来时长。

产物：code/outputs/analysis/P3_fork_calib/table.json

用法：python calibrate_probe.py --tier 50 --demand 1600 --block 180 --seeds 3
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
from fork_scenario import build_net, OUT as FORK_OUT  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_fork_calib"

STEP = 0.1
V_LIM = 30.0
FORK_X = 3000.0
BN_LO, BN_HI = 4900.0, 5100.0
T_END_PAD = 900.0
PENALTY = 55.7          # 绕行相对主路的自由流代价（实测 222.4 − 166.7）
FREE_MAIN = 166.7      # 3000→8000 全程自由流（5 000 m / 30 m/s）
FREE_DETOUR = 222.4    # 绕行全程自由流（实测，含汇合口 5.7 s）


def one_run(net: Path, work: Path, demand: float, block_s: float, t0: float,
            decision_t: float, probe_route: str, seed: int) -> dict:
    """背景全走主路；在 decision_t 于改道点上游 100 m 插入一辆探测车，走指定路由。

    🔴 文件名只算一次（stem），路由文件、配置、行程记录三处共用，杜绝改名漏改引用。
    """
    stem = f"{probe_route}_d{int(demand)}_t{int(decision_t)}_s{seed % 10000}"
    rou_file = f"r_{stem}.rou.xml"
    cfg_file = f"run_{stem}.sumocfg"
    trip_file = f"trip_{stem}.xml"

    period = 3600.0 / demand
    t_end = t0 + block_s + T_END_PAD
    probe_rid = "pmain" if probe_route == "main" else "pbyp"
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1"/>')
    rou = (f'<routes>{vt}'
           f'<route id="main" edges="in mid bn out tail"/>'
           f'<route id="byp" edges="in bypass tail"/>'
           f'<route id="pmain" edges="in mid bn out tail"/>'
           f'<route id="pbyp" edges="in bypass tail"/>'
           f'<flow id="f" type="c" route="main" begin="0" end="{t_end:.0f}"'
           f' period="{period:.3f}" departSpeed="max" departLane="0"/>'
           f'<vehicle id="probe" type="c" route="{probe_rid}"'
           f' depart="{decision_t:.1f}" departPos="2900" departSpeed="max" departLane="0"/>'
           f'</routes>')
    (work / rou_file).write_text(rou, encoding="utf-8")

    cfg = work / cfg_file
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="{rou_file}"/></input>'
        f'<time><begin value="0"/><end value="{t_end:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report>'
        f'<output><tripinfo-output value="{trip_file}"/></output></configuration>',
        encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    blocked = False
    try:
        for k in range(int(t_end / STEP)):
            t = k * STEP
            if not blocked and t >= t0:
                traci.lane.setMaxSpeed("bn_0", 4.0)
                blocked = True
            if blocked and t >= t0 + block_s:
                traci.lane.setMaxSpeed("bn_0", V_LIM)
                blocked = False
            traci.simulationStep()
    finally:
        traci.close()

    # 从 tripinfo 读探测车实际行程与出发等待（departDelay 是判断「没按时进网」的关键）
    import xml.etree.ElementTree as ET
    travelled = depart_delay = None
    tp = work / trip_file
    if tp.exists():
        for tri in ET.parse(tp).getroot().iter("tripinfo"):
            if tri.get("id") == "probe":
                travelled = round(float(tri.get("duration")), 1)
                depart_delay = round(float(tri.get("departDelay", "nan")), 1)
                break
    age = None if decision_t < t0 else round(decision_t - t0, 1)
    return {"decision_t": decision_t, "probe_route": probe_route, "age_s": age,
            "travelled_s": travelled, "depart_delay_s": depart_delay}



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=float, default=50.0)
    ap.add_argument("--demand", type=float, default=1600.0)
    ap.add_argument("--block", type=float, default=180.0)
    ap.add_argument("--t0", type=float, default=600.0)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    work = OUT / f"_net_t{int(args.tier)}"
    net = build_net(args.tier, work)
    decisions = [args.t0 - 120, args.t0 - 60, args.t0,
                 args.t0 + 60, args.t0 + 120, args.t0 + 180, args.t0 + 240]
    rows = []
    print(f"校准：+{args.tier:.0f} 秒档 | 需求 {args.demand:.0f} 辆/时 | "
          f"瓶颈 {args.t0:.0f}–{args.t0+args.block:.0f}s | {args.seeds} 个种子", flush=True)
    print(f"{'决策时刻':>8} {'事件年龄':>8} {'T主路':>8} {'T绕行':>8} {'Y':>8}", flush=True)
    for seed in range(args.seeds):
        for dt in decisions:
            tm = one_run(net, work, args.demand, args.block, args.t0, dt, "main",
                         seed + 20261120)["travelled_s"]
            td = one_run(net, work, args.demand, args.block, args.t0, dt, "byp",
                         seed + 20261120)["travelled_s"]
            y = None if (tm is None or td is None) else round(tm - td + PENALTY, 1)
            age = None if dt < args.t0 else round(dt - args.t0, 1)
            rows.append({"seed": seed + 20261120, "decision_t": dt, "age_s": age,
                         "t_main_s": tm, "t_detour_s": td, "Y": y})
            print(f"{dt:>8.0f} {str(age):>8} {str(tm):>8} {str(td):>8} {str(y):>8}",
                  flush=True)

    # 冻结分箱：按事件年龄分桶（可从消息字段得到），畅通世界单独一桶
    def bucket(age):
        if age is None:
            return "pre_event"
        if age < 60:
            return "age_0_60"
        if age < 120:
            return "age_60_120"
        if age < 180:
            return "age_120_180"
        return "age_180_plus"

    table = {}
    for r in rows:
        if r["Y"] is None:
            continue
        b = bucket(r["age_s"])
        table.setdefault(b, []).append(r["Y"])
    frozen = {b: {"n": len(v), "Y_mean": round(float(np.mean(v)), 1),
                  "Y_median": round(float(np.median(v)), 1),
                  "choose_detour": bool(np.mean(v) > PENALTY)}
              for b, v in table.items()}
    print(f"\n冻结查表（判据 Ê[Y|B] > 50.1 才绕行）：")
    for b, v in frozen.items():
        print(f"  {b:>14}: n={v['n']:>2}  Y均值={v['Y_mean']:>7}  "
              f"绕行? {'是' if v['choose_detour'] else '否'}")

    (OUT / "table.json").write_text(json.dumps(
        {"tier_s": args.tier, "demand": args.demand, "block_s": args.block,
         "t0": args.t0, "free_main_s": FREE_MAIN, "free_detour_s": FREE_DETOUR,
         "rows": rows, "frozen_table": frozen}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\nwritten: {OUT/'table.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
