"""0.1.7 分岔场景风险可测性审计（GPT 第六十二轮 Q4 指定）。

【为什么做这个】
GPT 裁决：`Y` 只是机制量，AAD 的唯一主结局是「区域内 DRAC ≥ 3.4 m/s² 的事件数」。
但分岔场景到底能不能产生这种事件，**目前未知**——
旧场景 D 最大只有 0.93 m/s²，那是旧场景的证据，不能套到修复后的分岔场景上。
必须先审计，不许直接开四臂。

【审计口径（严格照 GPT 要求）】
- 修复后的分岔场景（tail 已改两车道）
- **无消息参照**（本场景本来就没有消息臂，跑的是纯基线）
- **多种子**，种子是独立单位
- **不比较任何干预臂效果**
- 逐种子报告：最大 DRAC / 超阈值车·秒 / 去重后事件数

【DRAC 定义（沿用 code/scripts/p3_audits/decompose_low_ttc_drac.py 第 13 行）】
  DRAC = c² / (2g)
  c = 闭合速度（后车 − 前车），g = 物理净距（车头到车尾，不减 minGap）
  主阈值 3.4 m/s²；敏感性 3.0 / 4.5
  同一后车连续帧超阈值 → 合并为一个事件

【跑之前写死的预测（R08 第 3 条）】
1. 所有种子的 **最大 DRAC < 2.0 m/s²**。
   理由：SUMO 的 Krauss 模型没有感知限制，车能瞬间看到任意远的前车与队尾，
   会提前平滑减速；旧场景已经证明这条路走不通（D 最大 0.93）。
2. **DRAC ≥ 3.4 的事件数 = 0**（全部种子）。
3. 超阈值车·秒 = 0。
4. 事件若真的非零，必须抽查是否为汇合口或轨迹拼接伪影，不得直接采信。

【判据（GPT 给的裁决规则）】
- 窗口内零事件 → **不放行**确认性风险实验
- 事件稀少到无法区分目标降幅 → **不放行**
- 只有事件频度与种子间波动都够，才放行

【这次没证明什么（先写在这，免得以后自欺）】
即使结果是零事件，也**只证明「这个参数下的分岔场景造不出风险」**，
不证明「消息对风险无效」，也不证明「所有分岔场景都造不出风险」。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_risk_audit"

STEP = 0.1
V_LIM = 30.0
DEMAND = 1600.0
T_END = 1680.0
T0 = 600.0
BLOCK = 180.0
DRAC_MAIN = 3.4
DRAC_SENS = (3.0, 4.5)
LOOKAHEAD = 250.0
SPEED_GATE = 3.0          # 只查速度 >3 m/s 的车，队列里蠕行的车不查（省时间且不失真）
ROADS_GATE = {"mid", "bn", "out"}


def build_rou(work: Path, seed: int) -> None:
    period = 3600.0 / DEMAND
    n = int(T_END / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r_audit.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>{vehs}</routes>',
        encoding="utf-8")
    (work / "c_audit.sumocfg").write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_audit.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>',
        encoding="utf-8")


def run_seed(work: Path, seed: int) -> dict:
    build_rou(work, seed)
    traci = load_traci()
    traci.start([SUMO, "-c", str(work / "c_audit.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    blocked = False
    frames = []
    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 2)
            if not blocked and t >= T0:
                traci.lane.setMaxSpeed("bn_0", 4.0)
                blocked = True
            if blocked and t >= T0 + BLOCK:
                traci.lane.setMaxSpeed("bn_0", V_LIM)
                blocked = False
            traci.simulationStep()
            if k % 2:                      # 0.2 s 采样
                continue
            for v in traci.vehicle.getIDList():
                if traci.vehicle.getRoadID(v) not in ROADS_GATE:
                    continue
                ve = traci.vehicle.getSpeed(v)
                if ve <= SPEED_GATE:
                    continue
                ld = traci.vehicle.getLeader(v, LOOKAHEAD)
                if ld is None or ld[0] is None:
                    continue
                lead_id, gap = ld
                if gap is None or gap <= 0.1:
                    continue
                vl = traci.vehicle.getSpeed(lead_id)
                c = ve - vl
                if c <= 0:
                    continue
                drac = (c * c) / (2.0 * gap)
                frames.append({"t": t, "ego": v, "lead": lead_id,
                               "g": round(gap, 3), "c": round(c, 3),
                               "drac": round(drac, 4),
                               "ego_road": traci.vehicle.getRoadID(v)})
    finally:
        traci.close()

    if not frames:
        return {"seed": seed, "n_frames": 0, "drac_max": 0.0,
                "veh_s_over": {str(x): 0.0 for x in (DRAC_MAIN,) + DRAC_SENS},
                "events": 0, "note": "无有效帧"}

    drac = np.array([f["drac"] for f in frames])
    dt = 0.2
    over = {th: float((drac >= th).sum() * dt) for th in (DRAC_MAIN,) + DRAC_SENS}

    # 事件合并：同一后车、连续帧超阈值 -> 一个事件
    events = []
    cur = None
    by_ego = defaultdict(list)
    for f in frames:
        by_ego[f["ego"]].append(f)
    for ego, fs in by_ego.items():
        cur = None
        for f in fs:
            if f["drac"] >= DRAC_MAIN:
                if cur is None:
                    cur = {"ego": ego, "t_first": f["t"], "t_last": f["t"],
                           "peak": f["drac"], "n": 1, "road": f["ego_road"],
                           "g_min": f["g"]}
                else:
                    cur["t_last"] = f["t"]
                    cur["peak"] = max(cur["peak"], f["drac"])
                    cur["n"] += 1
                    cur["g_min"] = min(cur["g_min"], f["g"])
            else:
                if cur is not None:
                    events.append(cur)
                    cur = None
        if cur is not None:
            events.append(cur)

    top = sorted(frames, key=lambda x: -x["drac"])[:3]
    return {"seed": seed, "n_frames": len(frames),
            "drac_max": round(float(drac.max()), 3),
            "drac_p50": round(float(np.median(drac)), 3),
            "drac_p99": round(float(np.percentile(drac, 99)), 3),
            "veh_s_over": over,
            "events": len(events),
            "event_roads": sorted({e["road"] for e in events}),
            "top3": [{"t": x["t"], "ego": x["ego"], "drac": x["drac"],
                      "g": x["g"], "c": x["c"], "road": x["ego_road"]} for x in top],
            }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+",
                    default=[20261120, 20261121, 20261122, 20261123, 20261124,
                             20261125, 20261126, 20261127, 20261128, 20261129])
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)
    print(f"审计 {len(args.seeds)} 个种子；DRAC 主阈值 {DRAC_MAIN} m/s²", flush=True)
    print(f"{'种子':>10} {'帧数':>7} {'最大DRAC':>9} {'p99':>7} {'超阈车·秒':>10} {'事件':>5}")
    rows = []
    for s in args.seeds:
        r = run_seed(OUT, s)
        rows.append(r)
        print(f"{s:>10} {r['n_frames']:>7} {r['drac_max']:>9.3f} "
              f"{r.get('drac_p99', 0):>7.3f} {r['veh_s_over'][str(DRAC_MAIN)]:>10.1f} "
              f"{r['events']:>5}", flush=True)

    mx = [r["drac_max"] for r in rows]
    ev = [r["events"] for r in rows]
    print("\n=== 对照预测（R08）===")
    print(f"  最大 DRAC 全部 <2.0 ? 实测 {min(mx):.3f}–{max(mx):.3f}  "
          f"{'✅' if max(mx) < 2.0 else '❌'}")
    print(f"  DRAC≥3.4 事件数全部为 0 ? 实测 {ev}  {'✅' if sum(ev) == 0 else '❌'}")
    print("\n=== 审计判定（GPT 规则）===")
    if sum(ev) == 0:
        print("  窗口内零事件 → **不放行确认性风险实验**")
        print("  下一步走 GPT 的第二条分支：风险场景单列，分岔场景只答延误")
    else:
        print(f"  有 {sum(ev)} 个事件，须抽查是否汇合口/轨迹拼接伪影，再判断频度是否够")
        for r in rows:
            if r["events"]:
                print(f"    种子 {r['seed']}：事件所在边 {r['event_roads']}，最高 {r['top3'][0]}")

    (OUT / "risk_audit.json").write_text(
        json.dumps({"seeds": args.seeds, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\nwritten: {OUT/'risk_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
