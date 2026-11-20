"""0.2.7 区域停车组诊断（GPT 第八十七轮 Q3 要求）

【配对诊断】复用 0.2.4 的初始状态、种子、后车 Krauss 设置；
**只改前车的制动终止条件**：
  - 原 0.2.4：脉冲 9.0 m/s²、最长 2.0 s，到时释放
  - 本组　：以 9.0 m/s² 减速至**实际停稳**，再保持至预先声明的观察窗结束
其余（路网、需求、源车选择规则、响应车不接管、事件口径）一律不动。

【预先声明】观察窗 = t0 + 600 s（与 0.2.3 规格 §5 一致）。
             保持时长的真实依据尚未取得（GPT 要求用 FHWA RCT 类运营记录），
             所以**本组只作诊断，不把观察窗写成真实事故持续时间**。

用法：python region_stop.py --seeds 20261101 --mode pilot
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_p3_stop_queue import SUMO, load_traci  # noqa: E402
from fork_scenario import build_net, V_LIM, STEP  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "code/outputs/analysis/P3_region_stop"

T_SRC = 600.0
WAIT_MAX = 30.0
SRC_ZONE = 200.0
SRC_DECEL = 9.0
DRAC_THR = 3.4
MERGE_FRAMES = 3
SLOW_V = 5.0
OBS_H = 600.0
DEMAND = 1600.0
TAU = 1.584
T_END = T_SRC + WAIT_MAX + OBS_H + 120.0

MID_LEN, BN_LEN, OUT_LEN = 1898.5, 200.0, 1898.5
OFF = {"mid": 0.0, "bn": MID_LEN, "out": MID_LEN + BN_LEN,
       "tail": MID_LEN + BN_LEN + OUT_LEN}


def build_demand(work: Path, seed: int) -> Path:
    period = 3600.0 / DEMAND
    n = int(T_END / period)
    vt = (f'<vType id="c" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0"'
          f' tau="{TAU}" length="5" minGap="2.5" maxSpeed="{V_LIM}" speedFactor="1"'
          f' lcKeepRight="0"/>')
    vehs = "".join(
        f'<vehicle id="V{i:04d}" type="c" route="main" depart="{i*period:.3f}"'
        f' departSpeed="max" departLane="0"/>' for i in range(n))
    (work / "r.rou.xml").write_text(
        f'<routes>{vt}<route id="main" edges="in mid bn out tail"/>{vehs}</routes>',
        encoding="utf-8")
    cfg = work / "run.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="r.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{T_END:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/></report></configuration>', encoding="utf-8")
    return cfg


def run_seed(seed: int) -> dict:
    work = OUT / str(seed)
    work.mkdir(parents=True, exist_ok=True)
    build_net(50.0, work)
    cfg = build_demand(work, seed)

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    c = traci.constants

    src_id = None
    src_orig_mode = None
    t0 = None
    stopped_at = None
    released = False
    triggered = False
    src_trace = []
    active: dict[str, dict] = {}
    done_events: list[dict] = []
    slow_flags: list[tuple[float, bool]] = []
    collisions = 0
    sub: set[str] = set()
    n_frames = 0
    peak_global = 0.0
    peak_global_at = None

    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)

            # 源车选择（与 0.2.4 完全一致）
            if (not triggered) and T_SRC <= t <= T_SRC + WAIT_MAX:
                cands = []
                for v in traci.vehicle.getIDList():
                    if traci.vehicle.getRoadID(v) != "mid":
                        continue
                    dist = MID_LEN - traci.vehicle.getLanePosition(v)
                    if 0.0 <= dist <= SRC_ZONE:
                        cands.append((dist, v))
                if cands:
                    cands.sort(key=lambda x: (x[0], x[1]))
                    src_id, t0 = cands[0][1], t
                    triggered = True
                    v_now = traci.vehicle.getSpeed(src_id)
                    src_orig_mode = traci.vehicle.getSpeedMode(src_id)
                    if v_now <= 1e-6:
                        src_trace.append({"t": t, "event": "选中但未施刹"})
                        stopped_at = t
                    else:
                        traci.vehicle.setSpeedMode(src_id, 0)
                        src_trace.append({"t": t, "event": "开始减速至停",
                                          "pos": round(traci.vehicle.getLanePosition(src_id), 3),
                                          "v": round(v_now, 3),
                                          "dist_to_bn": round(cands[0][0], 2)})

            # 减速至实际停稳（唯一改动：不再有 2.0 s 上限）
            if src_id is not None and stopped_at is None:
                ids = traci.vehicle.getIDList()
                if src_id not in ids:
                    stopped_at = t
                    src_trace.append({"t": t, "event": "源车离网"})
                else:
                    v_now = traci.vehicle.getSpeed(src_id)
                    if v_now <= 1e-6:
                        stopped_at = t
                        src_trace.append({"t": t, "event": "已停稳",
                                          "stop_dur": round(t - t0, 2),
                                          "pos": round(traci.vehicle.getLanePosition(src_id), 3)})
                    else:
                        traci.vehicle.setSpeed(src_id, max(0.0, v_now - SRC_DECEL * STEP))

            traci.simulationStep()
            collisions = max(collisions, len(traci.simulation.getCollisions()))

            if t0 is not None and t >= t0 + OBS_H:
                continue

            cur = {}
            for v in traci.vehicle.getIDList():
                if v not in sub:
                    traci.vehicle.subscribe(v, (c.VAR_ROAD_ID, c.VAR_LANEPOSITION,
                                                c.VAR_SPEED, c.VAR_LENGTH,
                                                c.VAR_LANE_INDEX))
                    sub.add(v)
            for v, d in traci.vehicle.getAllSubscriptionResults().items():
                road = str(d.get(c.VAR_ROAD_ID, ""))
                if road not in OFF:
                    continue
                cur[v] = (road, int(d.get(c.VAR_LANE_INDEX, 0)),
                          OFF[road] + float(d.get(c.VAR_LANEPOSITION, -1)),
                          float(d.get(c.VAR_SPEED, -1)), float(d.get(c.VAR_LENGTH, 5.0)))
            n_frames += 1

            chains: dict[int, list] = {}
            for v, (road, lane, gp, spd, ln) in cur.items():
                chains.setdefault(lane, []).append((gp, spd, ln, v, road))
            for lane, lst in chains.items():
                lst.sort(key=lambda x: x[0])
                for i in range(len(lst) - 1):
                    g_lead, s_lead, _, v_lead, _ = lst[i + 1]
                    g_ego, s_ego, l_ego, v_ego, _ = lst[i]
                    gap = g_lead - g_ego - l_ego
                    cc = s_ego - s_lead
                    drac = (cc * cc / (2 * gap)) if (gap > 0 and cc > 0) else 0.0
                    if drac > peak_global:
                        peak_global, peak_global_at = drac, t
                    if v_ego == src_id:
                        continue
                    if drac >= DRAC_THR:
                        a = active.get(v_ego)
                        if a is None:
                            active[v_ego] = {"on_t": t, "peak": drac, "pairs": {(v_ego, v_lead)},
                                             "gap": gap, "c": cc, "v": s_ego}
                        else:
                            a["peak"] = max(a["peak"], drac)
                            a["pairs"].add((v_ego, v_lead))
                        active[v_ego]["_miss"] = 0
                    elif v_ego in active:
                        active[v_ego]["_miss"] = active[v_ego].get("_miss", 0) + 1
            for v_ego in list(active):
                if active[v_ego].get("_miss", 0) > MERGE_FRAMES:
                    done_events.append(_close(active.pop(v_ego), src_id))

            if triggered:
                slow_flags.append((t, any(spd < SLOW_V for (_, _, _, spd, _) in cur.values())))
    finally:
        traci.close()

    for v_ego, a in list(active.items()):
        done_events.append(_close(a, src_id))

    res = {
        "seed": seed, "src_id": src_id, "t0": t0, "triggered": triggered,
        "not_triggered": not triggered,
        "selected_but_no_brake": any(x.get("event") == "选中但未施刹" for x in src_trace),
        "stopped_at": stopped_at,
        "stop_dur": (None if (t0 is None or stopped_at is None)
                     else round(stopped_at - t0, 2)),
        "collisions": collisions, "n_frames": n_frames,
        "peak_drac_global": round(peak_global, 4), "peak_at": peak_global_at,
        "n_events": len(done_events), "events": done_events,
        "dissipation": _dissipation(slow_flags, t0),
        "src_trace": src_trace,
    }
    (work / "run.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(f"  种子 {seed}: 源车={src_id} t0={t0} 停稳耗时={res['stop_dur']}s "
          f"全局峰值DRAC={res['peak_drac_global']}(t={peak_global_at}) "
          f"事件={len(done_events)} 碰撞={collisions}", flush=True)
    return res


def _close(a: dict, src_id: str | None) -> dict:
    leads = {ld for (_, ld) in a["pairs"]}
    if src_id is not None and leads == {src_id}:
        cause = "直接事件"
    elif src_id is not None and src_id in leads:
        cause = "混合事件"
    else:
        cause = "非源前车事件"
    return {"on_t": a["on_t"], "peak_drac": round(a["peak"], 3),
            "gap_m": round(a["gap"], 3), "closing_ms": round(a["c"], 3),
            "v_ego": round(a["v"], 3), "lead_ids": sorted(leads), "cause": cause}


def _dissipation(slow: list, t0: float | None) -> dict:
    if t0 is None or not slow:
        return {"confirmed": False, "reason": "未触发或无监测"}
    after = [(t, s) for t, s in slow if t >= t0]
    if not any(s for _, s in after):
        return {"confirmed": True, "reason": "无排队", "h_contrib": 0.0}
    last_slow = max(t for t, s in after if s)
    obs_end = after[-1][0]
    if obs_end - last_slow >= 60.0:
        return {"confirmed": True, "reason": "确认消散", "h_contrib": round(last_slow - t0, 2)}
    return {"confirmed": False, "reason": "窗尾未消散",
            "last_slow": round(last_slow, 2), "obs_end": round(obs_end, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--mode", choices=["pilot", "formal"], default="pilot")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"=== {args.mode}（减速至停，无 2.0 s 上限），{len(args.seeds)} 个种子 ===", flush=True)
    res = [run_seed(s) for s in args.seeds]
    print("\n=== 汇总 ===")
    for r in res:
        print(f"  种子 {r['seed']}: 触发={r['triggered']} 停稳={r['stop_dur']}s "
              f"峰值={r['peak_drac_global']} 事件={r['n_events']} "
              f"分类={_count([e['cause'] for e in r['events']])}")
    (OUT / f"{args.mode}_summary.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT/f'{args.mode}_summary.json'}")
    return 0


def _count(items):
    d = {}
    for x in items:
        d[x] = d.get(x, 0) + 1
    return d


if __name__ == "__main__":
    raise SystemExit(main())