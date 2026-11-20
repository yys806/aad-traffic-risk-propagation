"""0.2.3 区域准入：源车急刹脉冲 + 只跑无消息臂（v2，重写）

规格：`docs/tasks/0.2.3_规格_区域准入冻结_源车急刹.md`（v3，GPT 第八十二/八十三轮定）

【v1 的两个缺陷，v2 已修】
 ① 帧查找 O(n²)：v1 每算一对车都去遍历全部帧。v2 改为**逐帧流式**计算，不存全帧。
 ② 跨边跟驰漏检：v1 只比同 `road`。v2 把 mid→bn→out→tail 拼成**连续坐标链**，
    同车道内按全局位置排序取相邻对，跨边自然衔接。

【冻结参数】
  源车选择：t_src=600 s 起**逐仿真步**，在 mid 上距 bn 入口 ≤200 m 的车辆中选最近者，
            并列按车辆 ID 排序；等待上限 30 s；首次实际施刹时刻记 t0
  制动波形：指令速度以 9.0 m/s² 递减，**最长 2.0 s**，触零提前结束；
            末条指令在对应控制步生效，**下一控制更新撤销覆盖**；
            解除后**恢复源车原安全模式、不再发任何速度指令**
  响应车　：保持原生 Krauss，speedMode 默认 31，**一律不接管**
  消散判据：监测 mid/bn/out/tail 全部车道；最后一个慢车帧（v<5）之后
            连续 60 s 为零且此后未再出现 → 确认消散；观测期 t0+600 s
  事件去重：同一后车连续超阈，允许最多 3 个有效低于阈值帧（沿用 0.2.0）
  事件分类：按**计算 DRAC 时的实际前车**判（直接 / 混合 / 非源前车）

用法：
  python region_admit.py --seeds 20261101 --mode pilot
  python region_admit.py --seeds 20261120 --mode formal
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
OUT = ROOT / "code/outputs/analysis/P3_region_admit"

T_SRC = 600.0
WAIT_MAX = 30.0
SRC_ZONE = 200.0
SRC_DECEL = 9.0
PULSE_MAX = 2.0
DRAC_THR = 3.4
MERGE_FRAMES = 3
SLOW_V = 5.0
QUIET_S = 60.0
OBS_H = 600.0              # 正式观测窗： [t0, t0+OBS_H)
DEMAND = 1600.0
TAU = 1.584
# 仿真跑长一点只为诊断；统计严格截在 t0+OBS_H（GPT 第八十四轮 Q4）
SIM_TAIL = 300.0
T_END = T_SRC + WAIT_MAX + OBS_H + SIM_TAIL

# 连续坐标链：mid → bn → out → tail（同车道内才配对）
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
    pulse_end = None
    released = False
    triggered = False
    src_trace = []
    active: dict[str, dict] = {}      # 后车 -> 进行中的事件
    done_events: list[dict] = []
    slow_flags: list[tuple[float, bool]] = []
    collisions = 0
    sub: set[str] = set()
    n_frames = 0

    try:
        for k in range(int(T_END / STEP)):
            t = round(k * STEP, 3)

            # ---------- 源车选择 ----------
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
                    if v_now <= 1e-6:
                        src_trace.append({"t": t, "event": "选中但未施刹"})
                        pulse_end = t
                    else:
                        src_orig_mode = traci.vehicle.getSpeedMode(src_id)
                        traci.vehicle.setSpeedMode(src_id, 0)
                        src_trace.append({"t": t, "event": "开始脉冲",
                                          "pos": round(traci.vehicle.getLanePosition(src_id), 3),
                                          "v": round(v_now, 3),
                                          "dist_to_bn": round(cands[0][0], 2)})

            # ---------- 脉冲推进 ----------
            if src_id is not None and pulse_end is None:
                ids = traci.vehicle.getIDList()
                if src_id not in ids:
                    pulse_end = t
                    src_trace.append({"t": t, "event": "源车离网"})
                elif (t - t0) >= PULSE_MAX - 1e-9:
                    # 已满 2.0 s：本步不再施刹，直接结束（避免多施刹一个控制步）
                    pulse_end = t
                    src_trace.append({"t": t, "event": "脉冲结束",
                                      "reason": "到 2.0 s",
                                      "v_meas_before_release": round(
                                          traci.vehicle.getSpeed(src_id), 3),
                                      "n_steps": int(round((t - t0) / STEP))})
                else:
                    v_cmd = traci.vehicle.getSpeed(src_id)
                    v_new = max(0.0, v_cmd - SRC_DECEL * STEP)
                    traci.vehicle.setSpeed(src_id, v_new)
                    if v_new <= 1e-9:
                        pulse_end = t
                        src_trace.append({"t": t, "event": "脉冲结束",
                                          "reason": "触零", "v_cmd": round(v_new, 3),
                                          "n_steps": int(round((t - t0) / STEP)) + 1})

            # ---------- 撤销覆盖（下一控制更新）----------
            if pulse_end is not None and not released and t > pulse_end:
                if src_id in traci.vehicle.getIDList() and src_orig_mode is not None:
                    traci.vehicle.setSpeedMode(src_id, src_orig_mode)
                released = True
                src_trace.append({"t": t, "event": "撤销覆盖"})

            traci.simulationStep()
            collisions = max(collisions, len(traci.simulation.getCollisions()))

            # GPT 第八十四轮 Q4：统计严格截在 [t0, t0+OBS_H)，之后只跑不记
            if t0 is not None and t >= t0 + OBS_H:
                continue

            # ---------- 逐帧：订阅 + 几何配对 ----------
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
                lane = int(d.get(c.VAR_LANE_INDEX, 0))
                pos = float(d.get(c.VAR_LANEPOSITION, -1))
                cur[v] = (road, lane, OFF[road] + pos,
                          float(d.get(c.VAR_SPEED, -1)), float(d.get(c.VAR_LENGTH, 5.0)))
            n_frames += 1

            # 同车道按全局位置排序，相邻即跟驰对
            chains: dict[tuple, list] = {}
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
                    if v_ego == src_id:
                        continue
                    if drac >= DRAC_THR:
                        a = active.get(v_ego)
                        if a is None:
                            active[v_ego] = {"on_t": t, "peak": drac, "last_t": t,
                                             "pairs": {(v_ego, v_lead)},
                                             "gap": gap, "c": cc, "v": s_ego}
                        else:
                            a["peak"] = max(a["peak"], drac)
                            a["last_t"] = t
                            a["pairs"].add((v_ego, v_lead))
                        active[v_ego]["_miss"] = 0
                    elif v_ego in active:
                        active[v_ego]["_miss"] = active[v_ego].get("_miss", 0) + 1
            # 帧末清理：连续缺帧超阈值超过允许数 → 收事件
            for v_ego in list(active):
                if active[v_ego].get("_miss", 0) > MERGE_FRAMES:
                    done_events.append(_close(active.pop(v_ego), src_id))

            # ---------- 慢车监测 ----------
            if triggered:
                any_slow = any(spd < SLOW_V for (_, _, _, spd, _) in cur.values())
                slow_flags.append((t, any_slow))
    finally:
        traci.close()

    for v_ego, a in list(active.items()):
        done_events.append(_close(a, src_id))

    dissip = _dissipation(slow_flags, t0)
    res = {
        "seed": seed, "src_id": src_id, "t0": t0, "triggered": triggered,
        "not_triggered": not triggered,
        "selected_but_no_brake": any(x.get("event") == "选中但未施刹" for x in src_trace),
        "pulse_end": pulse_end,
        "pulse_duration": (None if (t0 is None or pulse_end is None)
                           else round(pulse_end - t0, 2)),
        "collisions": collisions, "n_frames": n_frames,
        "n_events": len(done_events),
        "events": done_events,
        "dissipation": dissip,
        "src_trace": src_trace,
    }
    (work / "run.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(f"  种子 {seed}: 触发={triggered} 源车={src_id} t0={t0} "
          f"脉冲={res['pulse_duration']}s 事件={len(done_events)} "
          f"碰撞={collisions} 消散={dissip.get('confirmed')}({dissip.get('reason')})",
          flush=True)
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
    if obs_end - last_slow >= QUIET_S:
        return {"confirmed": True, "reason": "确认消散",
                "h_contrib": round(last_slow - t0, 2)}
    return {"confirmed": False, "reason": "窗尾未消散",
            "last_slow": round(last_slow, 2), "obs_end": round(obs_end, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--mode", choices=["pilot", "formal"], default="pilot")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"=== {args.mode}，{len(args.seeds)} 个种子 ===", flush=True)
    res = [run_seed(s) for s in args.seeds]

    print("\n=== 汇总 ===")
    trig = [r for r in res if r["triggered"]]
    print(f"  触发 {len(trig)}/{len(res)}")
    for r in res:
        print(f"    种子 {r['seed']}: 事件 {r['n_events']} "
              f"分类 {_count([e['cause'] for e in r['events']])}")
    if trig:
        ev = sorted(r["n_events"] for r in trig)
        print(f"  阳性运行事件数 {ev}，中位 {ev[len(ev)//2]}")

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