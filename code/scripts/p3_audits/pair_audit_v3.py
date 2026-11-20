"""0.1.7c 补对账：跨边跟驰 + 物理首差逐车明细（GPT 第七十轮 Q4 指定）。

【要回答的三个问题】
1. `mid → bn_0` 的跨边前车有没有被漏掉？（上一版只算同边车对）
2. `600.0 → 600.1 s` 的首差，到底差在谁身上、差多少？
   是路段限速导致的预减速、前车响应，还是测量抖动？
3. `675 s` 前后 V0204/V0205 两车各自的实际速度与净距是多少？
   （GPT：汇总里只存了闭合速度，没存两车各速，无法判断前车是否真在 12 m/s）

【记录策略】
逐步保存 `mid` 与 `bn` 两段每辆车的 (位置, 速度)，
离线再算同边与跨边车对，避免仿真里做重活。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_pair_audit_v3"
STEP = 0.1
T_END = 1680.0
DRAC_MAIN = 3.4


def build(work: Path, tag: str, seed: int) -> Path:
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
    cfg = build(work, tag, seed)
    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants
    sub: set[str] = set()
    blk = False
    # 每步：(t, {veh: (road, pos, speed, length)})
    steps: list[dict] = []
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
            t = round(traci.simulation.getTime(), 3)
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED, c.VAR_LENGTH))
                    sub.add(v)
            snap = {}
            for v, val in traci.vehicle.getAllSubscriptionResults().items():
                road = str(val.get(c.VAR_ROAD_ID, ""))
                if road not in ("mid", "bn"):
                    continue
                snap[v] = (road, round(float(val.get(c.VAR_LANEPOSITION, -1)), 3),
                           round(float(val.get(c.VAR_SPEED, -1)), 3),
                           float(val.get(c.VAR_LENGTH, 5.0)))
            steps.append({"t": t, "veh": snap})
    finally:
        traci.close()

    # 离线算车对：mid 同边 + 跨边 mid→bn
    pairs = []
    for st in steps:
        t = st["t"]
        snap = st["veh"]
        mid = sorted([(v, d) for v, d in snap.items() if d[0] == "mid"],
                     key=lambda x: x[1][1])
        bn = sorted([(v, d) for v, d in snap.items() if d[0] == "bn"],
                    key=lambda x: x[1][1])
        seq = mid + bn                      # 沿行驶方向排序：mid 后接 bn
        for i in range(len(seq) - 1):
            v_e, (r_e, p_e, s_e, l_e) = seq[i]
            v_l, (r_l, p_l, s_l, _) = seq[i + 1]
            if r_e != r_l:
                # 跨边：mid 末端 → bn 起点，位置需衔接（bn 的 0 位置 = mid 末端）
                continue
            g = p_l - p_e - l_e
            cc = s_e - s_l
            pairs.append({"t": t, "ego": v_e, "lead": v_l, "road": r_e,
                          "g": round(g, 3), "c": round(cc, 3),
                          "v_ego": s_e, "v_lead": s_l,
                          "drac": round((cc * cc) / (2 * g), 4) if g > 0 and cc > 0 else 0.0})
        # 跨边对：mid 最后一名 vs bn 第一名
        if mid and bn:
            v_e, (r_e, p_e, s_e, l_e) = mid[-1]
            v_l, (r_l, p_l, s_l, _) = bn[0]
            # bn 位置 + mid 长度 = 连续坐标
            gap = (p_l + 1898.5) - p_e - l_e
            cc = s_e - s_l
            pairs.append({"t": t, "ego": v_e, "lead": v_l, "road": "mid→bn",
                          "g": round(gap, 3), "c": round(cc, 3),
                          "v_ego": s_e, "v_lead": s_l,
                          "drac": round((cc * cc) / (2 * gap), 4) if gap > 0 and cc > 0 else 0.0})

    return {"steps": steps, "pairs": pairs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261120)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    build_net(50.0, OUT)

    print(f"种子 {args.seed}：无源…", flush=True)
    a = run(OUT, "nosrc", args.seed, False)
    print(f"  车对 {len(a['pairs'])}", flush=True)
    print(f"种子 {args.seed}：有源…", flush=True)
    b = run(OUT, "src", args.seed, True)
    print(f"  车对 {len(b['pairs'])}", flush=True)

    # 1) 首差逐车明细
    detail = None
    for i in range(min(len(a["steps"]), len(b["steps"]))):
        sa, sb = a["steps"][i]["veh"], b["steps"][i]["veh"]
        if sa != sb:
            keys = set(sa).union(set(sb))
            diffs = []
            for v in sorted(keys):
                da, db = sa.get(v), sb.get(v)
                if da != db:
                    diffs.append({"veh": v, "nosrc": da, "src": db})
            detail = {"index": i, "t": a["steps"][i]["t"],
                      "t_prev": a["steps"][i - 1]["t"] if i else None,
                      "n_diff": len(diffs), "diffs": diffs[:10]}
            break
    print(f"\n首差：{detail['t'] if detail else None} s，"
          f"涉及 {detail['n_diff'] if detail else 0} 辆车")
    if detail:
        for d in detail["diffs"][:5]:
            print(f"   {d['veh']}: 无源={d['nosrc']} / 有源={d['src']}")

    # 2) 675 s 前后 V0204/V0205
    win = [p for p in b["pairs"] if 674.0 <= p["t"] <= 676.0
           and p["ego"] in ("V0205",) and p["lead"] in ("V0204",)]
    print(f"\n675 s 前后 V0205→V0204 共 {len(win)} 帧：")
    for w in win[:6]:
        print(f"   t={w['t']} g={w['g']} v_ego={w['v_ego']} v_lead={w['v_lead']} "
              f"c={w['c']} drac={w['drac']}")

    # 3) 跨边对的最大 DRAC
    cross = [p for p in b["pairs"] if p["road"] == "mid→bn"]
    ctop = sorted(cross, key=lambda x: -x["drac"])[:3]
    print(f"\n跨边对共 {len(cross)} 帧，最大 DRAC {ctop[0]['drac'] if ctop else 0}")
    for w in ctop:
        print(f"   t={w['t']} {w['ego']}→{w['lead']} g={w['g']} c={w['c']} drac={w['drac']}")

    out = {"seed": args.seed, "first_divergence": detail,
           "v0205_win": win[:20], "cross_top3": ctop,
           "n_pairs_nosrc": len(a["pairs"]), "n_pairs_src": len(b["pairs"]),
           "drac_max_src": max([p["drac"] for p in b["pairs"]], default=0.0),
           "drac_max_nosrc": max([p["drac"] for p in a["pairs"]], default=0.0)}
    (OUT / "v3_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print(f"\nwritten: {OUT/'v3_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
