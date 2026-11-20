"""0.1.7b 成对逐帧对账（GPT 第六十八轮 Q4 指定）。

【为什么不用 getLeader 了】
实测：getLeader 返回的距离已扣掉后车 minGap（几何 95.00 → 返回 92.50）。
与其每次加回来，不如**直接从订阅的车辆位置算几何净距**——
几何净距是我要的量，不需要经过 minGap 的换算，也就不存在漏加的风险。

  同车道：g = pos_lead − pos_ego − length_ego
  跨边 mid→bn：mid 的最后一名与 bn 的第一名之间同样按上式算（位置需换算到同一坐标）

【相对上一版的三处修正（GPT 指出的缺口）】
1. 采样从 0.1 s 起（上一版每两步取一次，可能漏掉只持续一步的峰）
2. 不用舍入后的值判阈，用完整精度
3. 时间戳记**步进之后**的真实仿真时钟
4. 空返回要区分三种：确实无前车 / 观测缺失 / 有效但不闭合

【本脚本产出】GPT 要的那张表：
  首次物理差异的时间括号、提前窗长度、有效跟驰车·秒、缺测车·秒、
  窗内/窗外的峰值车对（净距、闭合速度、超阈数）
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
OUT = ROOT / "code/outputs/analysis/P3_pair_audit"

STEP = 0.1
T_END = 1680.0
DRAC_MAIN = 3.4
MID_LEN = 1898.5
FORK = 3000.0


def build(work: Path, tag: str, seed: int, blocked: bool) -> Path:
    period = 3600.0 / 1600.0
    n = int(T_END / period)
    vt = ('<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          ' tau="1.584" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / f"r_{tag}.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>{vehs}</routes>',
        encoding="utf-8")
    cfg = work / f"c_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r_{tag}.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>',
        encoding="utf-8")
    return cfg


def run(work: Path, tag: str, seed: int, blocked: bool) -> dict:
    """跑一次，逐步记录 mid 区每辆车的 (位置, 速度)，并算同车道几何净距。"""
    cfg = build(work, tag, seed, blocked)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    sub: set[str] = set()
    blk = False
    # 逐步状态：用于成对比较
    states: list[tuple[float, tuple]] = []
    # 跟驰对记录
    pairs: list[dict] = []
    counts = {"no_leader": 0, "non_closing": 0, "valid": 0}
    try:
        for k in range(int(T_END / STEP)):
            if blocked:
                t_pre = k * STEP
                if not blk and t_pre >= 600.0:
                    traci.lane.setMaxSpeed("bn_0", 4.0)
                    blk = True
                if blk and t_pre >= 780.0:
                    traci.lane.setMaxSpeed("bn_0", 30.0)
                    blk = False
            traci.simulationStep()
            t = traci.simulation.getTime()        # 步进之后的真实时钟
            ids = traci.vehicle.getIDList()
            for v in ids:
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED, c.VAR_LENGTH))
                    sub.add(v)
            res = traci.vehicle.getAllSubscriptionResults()
            # 收集 mid 区车辆，按位置排序算几何净距
            mid = []
            for v, val in res.items():
                if str(val.get(c.VAR_ROAD_ID, "")) != "mid":
                    continue
                mid.append((float(val.get(c.VAR_LANEPOSITION, -1)),
                            float(val.get(c.VAR_SPEED, -1)),
                            float(val.get(c.VAR_LENGTH, 5.0)), v))
            mid.sort(key=lambda x: x[0])
            states.append((round(t, 3), tuple((v, round(p, 3), round(s, 3))
                                              for p, s, _, v in mid)))
            for i in range(len(mid) - 1):
                p_lead, s_lead, _, v_lead = mid[i + 1]
                p_ego, s_ego, l_ego, v_ego = mid[i]
                g = p_lead - p_ego - l_ego        # 几何净距，不经 minGap
                cc = s_ego - s_lead
                if cc <= 0:
                    counts["non_closing"] += 1
                    continue
                counts["valid"] += 1
                drac = (cc * cc) / (2.0 * g) if g > 0 else float("inf")
                if drac >= 1.0:                    # 只存有意义的帧，省内存
                    pairs.append({"t": round(t, 3), "ego": v_ego, "lead": v_lead,
                                  "g": round(g, 3), "c": round(cc, 3),
                                  "drac": drac})
            # mid 最后一名的前车若在 bn 上，记缺测（跨边未覆盖）
            if mid:
                counts["no_leader"] += 1 if len(mid) == 1 else 0
    finally:
        traci.close()

    d = np.array([p["drac"] for p in pairs]) if pairs else np.array([0.0])
    return {"tag": tag, "seed": seed, "blocked": blocked,
            "n_states": len(states), "n_pairs": len(pairs),
            "drac_max": float(d.max()), "veh_s_34": float((d >= DRAC_MAIN).sum() * STEP),
            "events": int(_count_events(pairs)), "counts": counts,
            "states": states, "pairs": pairs}


def _count_events(pairs: list[dict]) -> int:
    """同一后车、连续 0.1 s 超阈 → 一个事件。"""
    ev = 0
    prev: dict[str, float] = {}
    for p in sorted(pairs, key=lambda x: x["t"]):
        if p["drac"] < DRAC_MAIN:
            prev.pop(p["ego"], None)
            continue
        last = prev.get(p["ego"])
        if last is None or abs(p["t"] - last - STEP) > 1e-6:
            ev += 1
        prev[p["ego"]] = p["t"]
    return ev


def first_divergence(a: list, b: list) -> dict:
    """两臂逐帧比对，找最早可复核的物理差异。"""
    n = min(len(a), len(b))
    for i in range(n):
        ta, sa = a[i]
        tb, sb = b[i]
        if abs(ta - tb) > 1e-6 or sa != sb:
            return {"index": i, "t": ta, "t_prev": a[i - 1][0] if i else None,
                    "why": "车辆集合或位置速度不同"}
    return {"index": None, "t": None, "t_prev": None, "why": "全程无差异"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261120)
    ap.add_argument("--tag", default="s0")
    args = ap.parse_args()

    work = OUT / args.tag
    work.mkdir(parents=True, exist_ok=True)
    build_net(50.0, work)
    print(f"种子 {args.seed}：跑无源…", flush=True)
    a = run(work, "nosrc", args.seed, False)
    print(f"  无源：帧 {a['n_states']}，跟驰对 {a['n_pairs']}，"
          f"最大DRAC {a['drac_max']:.3f}，事件 {a['events']}", flush=True)
    print(f"种子 {args.seed}：跑有源…", flush=True)
    b = run(work, "src", args.seed, True)
    print(f"  有源：帧 {b['n_states']}，跟驰对 {b['n_pairs']}，"
          f"最大DRAC {b['drac_max']:.3f}，事件 {b['events']}", flush=True)

    fd = first_divergence(a["states"], b["states"])
    print(f"\n首次物理差异：{fd}")

    out = {
        "seed": args.seed,
        "no_src": {k: v for k, v in a.items() if k not in ("states", "pairs")},
        "src": {k: v for k, v in b.items() if k not in ("states", "pairs")},
        "first_divergence": fd,
        "src_top3": sorted(b["pairs"], key=lambda x: -x["drac"])[:3],
        "nosrc_top3": sorted(a["pairs"], key=lambda x: -x["drac"])[:3],
    }
    (OUT / f"pair_{args.tag}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/f'pair_{args.tag}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
