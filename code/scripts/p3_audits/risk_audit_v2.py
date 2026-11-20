"""0.1.7 风险可测性审计 —— 修正版检测器（GPT 第六十七轮裁决后重写）。

【相对旧稿的三处修正，每处都有实测或裁决依据】

1) 物理净距必须加回后车 minGap
   实测（probe_getleader_gap.py）：两车几何车头到车尾 95.00 m，
   getLeader 返回 92.50 m，差正好 2.50 m = 后车 minGap。
   → g = raw_gap + follower_minGap
   不修的话 DRAC 系统性偏高，且越近错得越狠（g=5 时 DRAC 直接翻倍）。

2) 取消速度门
   旧稿跳过 ego 速度 ≤3 m/s 的车。GPT：取消，全车都算。
   低速度车也可能有正闭合速度，不该丢。

3) 目标区固定为 mid
   GPT 裁决：改道发生在岔口前，风险在 mid 测；以**后车车头** roadID=="mid" 判归属。
   mid 长 1898.5 m，bn 是相邻独立边、不在区内。

【本脚本的职责边界】
只做**检测器验收**（正负对照 + 边界样例），不跑 10 种子批。
GPT 明确：当前版本不放行批跑，须先补齐数值门槛与可执行条款。
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
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_risk_audit_v2"

STEP = 0.1
DRAC_MAIN = 3.4
TARGET_ROAD = "mid"


def drac(g_phys: float, c: float) -> float:
    """GPT 定的公式：DRAC = c²/(2g)，c = max(v_ego − v_lead, 0)，g 为物理保险杠净距。"""
    if g_phys <= 0 or c <= 0:
        return 0.0
    return (c * c) / (2.0 * g_phys)


def unit_tests() -> int:
    """GPT 指定的可手算对照，全部要过。"""
    print("=== 检测器单元验收（GPT 指定，可手算）===")
    fails = 0

    # 正对照 1：原始净距 2.5、minGap 2.5 → 物理 5.0；闭合 6 m/s
    raw, mgap, c = 2.5, 2.5, 6.0
    g_fix = raw + mgap
    d_fix = drac(g_fix, c)
    d_raw = drac(raw, c)          # 未修正（错的做法）
    print(f"  正对照：raw_gap={raw} + minGap={mgap} → g={g_fix}, c={c}")
    print(f"    修正后 DRAC = {d_fix:.3f}（应为 3.600）  "
          f"{'✅' if abs(d_fix - 3.6) < 1e-6 else '❌'}")
    print(f"    未修正 DRAC = {d_raw:.3f}（应为 7.200）  "
          f"{'✅' if abs(d_raw - 7.2) < 1e-6 else '❌'}")
    print(f"    修正降幅 = {(d_raw - d_fix) / d_raw:.1%}（应为 50.0%，等于 minGap/g）")
    fails += abs(d_fix - 3.6) > 1e-6
    fails += abs(d_raw - 7.2) > 1e-6

    # 负对照：排队蠕行，物理净距 2.5、闭合 1 m/s
    g_neg, c_neg = 2.5, 1.0
    d_neg = drac(g_neg, c_neg)
    print(f"  负对照：g={g_neg}, c={c_neg} → DRAC = {d_neg:.3f}（应为 0.200，远低于 3.4）  "
          f"{'✅' if abs(d_neg - 0.2) < 1e-6 else '❌'}")
    fails += abs(d_neg - 0.2) > 1e-6

    # 阈值边界：恰好 3.4 要算「超阈」（用 ≥）
    g_b, c_b = 5.0, 2.0 * (2 * 3.4 * 5.0) ** 0.5 / 2
    c_b = (2 * 3.4 * g_b) ** 0.5
    d_b = drac(g_b, c_b)
    print(f"  阈值边界：g={g_b}, c={c_b:.6f} → DRAC = {d_b:.6f}（应恰为 3.400000，判 ≥ 时算超阈）  "
          f"{'✅' if abs(d_b - 3.4) < 1e-9 else '❌'}")
    fails += abs(d_b - 3.4) > 1e-9

    # 闭合速度为负（前车更快）→ 不算风险
    print(f"  负闭合速度：c=−2 → DRAC = {drac(5.0, -2.0):.3f}（应为 0.000）  "
          f"{'✅' if drac(5.0, -2.0) == 0.0 else '❌'}")
    fails += drac(5.0, -2.0) != 0.0

    print(f"\n  单元验收：{'全部通过 ✅' if fails == 0 else f'{fails} 项未过 ❌'}")
    return fails


def scan_once(seed: int, blocked: bool, work: Path) -> dict:
    """跑一次无消息仿真，返回目标区内全部跟驰对的逐帧记录。"""
    period = 3600.0 / 1600.0
    n = int(1680.0 / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>{vehs}</routes>',
        encoding="utf-8")
    (work / "c.sumocfg").write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="1680"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>',
        encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(work / "c.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    blocked_now = False
    frames = []
    try:
        for k in range(int(1680 / STEP)):
            t = round(k * STEP, 2)
            if blocked:
                if not blocked_now and t >= 600.0:
                    traci.lane.setMaxSpeed("bn_0", 4.0)
                    blocked_now = True
                if blocked_now and t >= 780.0:
                    traci.lane.setMaxSpeed("bn_0", 30.0)
                    blocked_now = False
            traci.simulationStep()
            if k % 2:                      # 0.2 s 采样
                continue
            for v in traci.vehicle.getIDList():
                # 目标区归属：后车车头在 mid
                if traci.vehicle.getRoadID(v) != TARGET_ROAD:
                    continue
                ld = traci.vehicle.getLeader(v, 300.0)
                if ld is None or ld[0] is None or ld[0] == "":
                    continue
                lead, raw_gap = ld
                if raw_gap is None:
                    continue
                v_e = traci.vehicle.getSpeed(v)
                v_l = traci.vehicle.getSpeed(lead)
                c = v_e - v_l
                mgap = traci.vehicle.getMinGap(v)
                g = raw_gap + mgap            # ← 修正：加回 minGap
                frames.append({
                    "t": t, "ego": v, "lead": lead,
                    "raw_gap": round(raw_gap, 3), "minGap": round(mgap, 3),
                    "g": round(g, 3), "v_ego": round(v_e, 3), "v_lead": round(v_l, 3),
                    "c": round(c, 3), "drac": round(drac(g, c), 4),
                })
    finally:
        traci.close()
    return {"seed": seed, "blocked": blocked, "n_frames": len(frames), "frames": frames}


def summarize(run: dict) -> dict:
    fr = run["frames"]
    if not fr:
        return {"seed": run["seed"], "blocked": run["blocked"], "n": 0,
                "drac_max": 0.0, "veh_s_34": 0.0, "events": 0, "n_veh": 0}
    d = np.array([f["drac"] for f in fr])
    # 事件合并：同一后车、连续采样超阈 → 一个事件；断帧即断开
    events = 0
    by_ego: dict[str, list] = {}
    for f in fr:
        by_ego.setdefault(f["ego"], []).append(f)
    for ego, fs in by_ego.items():
        prev_over = False
        prev_t = None
        for f in fs:
            over = f["drac"] >= DRAC_MAIN
            contiguous = prev_t is not None and abs(f["t"] - prev_t - 0.2) < 1e-6
            if over and not (prev_over and contiguous):
                events += 1
            prev_over, prev_t = over, f["t"]
    return {"seed": run["seed"], "blocked": run["blocked"], "n": len(fr),
            "n_veh": len(by_ego), "drac_max": round(float(d.max()), 3),
            "veh_s_34": round(float((d >= DRAC_MAIN).sum() * 0.2), 1),
            "events": events}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit-only", action="store_true", help="只跑单元验收")
    ap.add_argument("--seeds", type=int, nargs="+", default=[20261120, 20261121])
    ap.add_argument("--one", nargs=2, metavar=("SEED", "BLOCKED"),
                    help="只跑一个组合，避免同进程反复起停 SUMO 导致连接被关")
    args = ap.parse_args()

    fails = unit_tests()
    if args.unit_only:
        return 1 if fails else 0

    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)
    if args.one:
        sd = int(args.one[0])
        bl = str(args.one[1]).lower() in ("1", "true", "yes")
        r = scan_once(sd, bl, OUT)
        sm = summarize(r)
        print(f"  种子 {sd} {'有源' if bl else '无源'}: 帧 {sm['n']}, 车 {sm['n_veh']}, "
              f"最大DRAC {sm['drac_max']:.3f}, 超阈车·秒 {sm['veh_s_34']}, 事件 {sm['events']}")
        return 1 if fails else 0

    print(f"\n=== 小样探查（{len(args.seeds)} 种子 × 有源/无源）===")
    rows = []
    for s in args.seeds:
        for blocked in (False, True):
            r = scan_once(s, blocked, OUT)
            sm = summarize(r)
            rows.append(sm)
            tag = "有源" if blocked else "无源"
            print(f"  种子 {s} {tag}: 帧 {sm['n']}, 车 {sm['n_veh']}, "
                  f"最大DRAC {sm['drac_max']:.3f}, 超阈车·秒 {sm['veh_s_34']}, 事件 {sm['events']}")

    (OUT / "detector_probe.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'detector_probe.json'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
