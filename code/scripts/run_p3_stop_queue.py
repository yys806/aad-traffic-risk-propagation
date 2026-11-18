"""P3-01a: 场景准入第 1 试 —— 单车道源车急停并保持，测上游移动队尾能否产生超阈暴露

阶段：P3 ｜ 运行目录：code/outputs/analysis/P3_stop_queue_<tag> ｜ 数据：本脚本生成（SUMO）
      ｜ 脚本：code/scripts/run_p3_stop_queue.py

与 P2 的唯一差别是源事件形态：
  P2  ：6 s 平滑降到 3 m/s（或 8 m/s），然后保持       —— 太温和，激发不出闭合
  P3  ：4.5 m/s² 线性减到 0，然后一直停着             —— 形成静止队尾向上游传播

准入判据见 docs/P3_场景准入规则_20261119.md：
  风险门 = 固定目标区内 TTC<2 s 暴露累计 >= 2 车·秒，来自 >= 2 辆不同后车，每辆连续 >= 0.5 s，
           且主终点占比高于配对背景。
  这里只报分子/分母/占比，不自动签「过门」——签名由人做。

用法
-----
  python code/scripts/run_p3_stop_queue.py --pair --headway 20 --seed 20261119
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = 0.05
EDGE_LEN = 15000.0
SOURCE_X = 6000.0
# 固定目标区：P3 主站 x=4000（源上游 2 km），±50 m 测量带
TARGET_X = 4000.0
BAND = 50.0
HEADWAY = 20.0
V_EQ = (HEADWAY - 5.0 - 2.5) / 0.6
WARMUP = 120.0
# ---- 源事件形态（本试的核心变量）----
DECEL = 4.5           # m/s²，Krauss 的 decel 参数，正常制动能力
HOLD = 660.0          # 停住后一直保持到观测窗结束（源车不动，波源不消失）
OBS_AFTER = 660.0
MAX_SLOTS = 1600
MAX_SPEED = 30.0
VEH_LEN = 5.0
TTC_THR = 2.0         # 秒，P0 主终点
D_THR = 2.0           # m/s²，机制诊断


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="cor_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>
    </edge>
    <junction id="a" type="dead_end" x="0.00" y="0.00"/>
    <junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/>
</net>"""


def routes_xml(sigma: float, headway: float = HEADWAY, react_s: float = 0.0) -> str:
    n = int((EDGE_LEN - headway) / headway)
    v_req = (headway - 5.0 - 2.5) / 0.6
    v_eq = min(v_req, MAX_SPEED)
    period = headway / v_eq
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="{sigma}"'
          f' tau="0.6" length="5" minGap="2.5" maxSpeed="{MAX_SPEED}" speedFactor="1"'
          f' speedDev="0.12"'
          + (f' actionStepLength="{react_s}"' if react_s > 0 else '')
          + '/>')
    vehs = []
    for i in range(n):
        pos = 10.0 + headway * i
        vehs.append(f'<vehicle id="V{i}" type="cal" route="rc" depart="0"'
                    f' departPos="{pos:.2f}" departSpeed="{v_eq:.3f}" departLane="0"/>')
    return (f'<routes>{vt}'
            f'<route id="rc" edges="cor"/>'
            f'{"".join(vehs)}'
            f'<flow id="in" type="cal" route="rc" begin="{period:.3f}"'
            f' end="{WARMUP + OBS_AFTER:.1f}" period="{period:.3f}"'
            f' departSpeed="{v_eq:.3f}" departLane="0"/>'
            f'</routes>')


def run(tmp: Path, tag: str, sigma: float, stop: bool,
        headway: float = HEADWAY, seed: int = 20261119,
        react_s: float = 0.0) -> dict:
    (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
    (tmp / f"routes_{tag}.rou.xml").write_text(
        routes_xml(sigma, headway, react_s), encoding="utf-8")
    cfg = tmp / f"run_{tag}.sumocfg"
    cfg.write_text(
        f'<configuration><input><net-file value="net.net.xml"/>'
        f'<route-files value="routes_{tag}.rou.xml"/></input>'
        f'<time><begin value="0"/><end value="{WARMUP + OBS_AFTER + 30:.0f}"/></time>'
        f'<processing><step-length value="{STEP}"/></processing>'
        f'<random_number><seed value="{seed}"/></random_number>'
        f'<report><no-step-log value="true"/><duration-log.statistics value="false"/></report>'
        f'</configuration>', encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn",
                 "--time-to-teleport", "-1"])
    const = traci.constants
    steps = int(round((WARMUP + OBS_AFTER + 30.0) / STEP))

    idx: dict[str, int] = {}
    pos = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)
    spd = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)

    event_t0 = None
    src_id = None
    src_slot = None
    src_v_start = V_EQ
    src_hist: list[tuple[float, float, float]] = []
    src_gone_at = None
    subscribed: set[str] = set()
    n_collision = 0

    t_start = time.time()
    try:
        for k in range(steps):
            now = k * STEP
            if now <= WARMUP:
                traci.simulationStep()
            else:
                if src_id is not None and event_t0 is not None and stop:
                    el = now - event_t0
                    cmd = max(src_v_start - DECEL * el, 0.0)
                    alive = src_id in traci.vehicle.getIDList()
                    if el < HOLD and alive:
                        traci.vehicle.setSpeed(src_id, cmd)
                    elif alive:
                        traci.vehicle.setSpeed(src_id, -1)
                        cmd = float("nan")
                    else:
                        # 源车已离网：记录并停止控制，不再调用 setSpeed（会抛 TraCIException）
                        cmd = float("nan")
                    if alive:
                        src_hist.append((now, traci.vehicle.getSpeed(src_id),
                                         cmd if cmd == cmd else -1.0))
                    elif event_t0 is not None and not src_gone_at:
                        src_gone_at = now
                traci.simulationStep()

            present = traci.vehicle.getIDList()
            for v in present:
                if v not in subscribed:
                    traci.vehicle.subscribe(v, (const.VAR_LANEPOSITION, const.VAR_SPEED))
                    subscribed.add(v)
            res = traci.vehicle.getAllSubscriptionResults()

            for v in res:
                if v not in idx and len(idx) < MAX_SLOTS:
                    idx[v] = len(idx)
            for v, val in res.items():
                i = idx.get(v)
                if i is None:
                    continue
                pos[k, i] = val.get(const.VAR_LANEPOSITION, np.nan)
                spd[k, i] = val.get(const.VAR_SPEED, np.nan)

            if stop and src_id is None and now >= WARMUP:
                cands = [(abs(res[v].get(const.VAR_LANEPOSITION, 1e9) - SOURCE_X), v)
                         for v in res]
                if cands:
                    _, src_id = min(cands)
                    src_slot = idx.get(src_id)
                    event_t0 = now
                    src_v_start = float(res[src_id].get(const.VAR_SPEED, V_EQ))
    finally:
        traci.close()

    used = len(idx)
    return {"tag": tag, "sigma": sigma, "stop": stop,
            "event_t0": event_t0, "source_id": src_id, "source_slot": src_slot,
            "source_v_start": src_v_start, "source_history": src_hist,
            "n_slots_used": used, "n_steps": steps, "step_s": STEP,
            "pos": pos[:, :used], "spd": spd[:, :used],
            "ids": list(idx.keys()), "wall_seconds": time.time() - t_start,
            "collisions": n_collision, "source_gone_at": src_gone_at}


def exposure_series(pos: np.ndarray, spd: np.ndarray, x_c: float, band: float) -> dict:
    """逐帧算目标区内的 TTC<2s 暴露车·秒与 D 诊断。

    返回逐帧：(n_veh_in_band, n_ttc_lt2, n_d_gt2, ttc_min, d_max)
    「暴露车·秒」= 该帧落在区内的车数 × step，对 n_ttc_lt2 计数累加。
    """
    n_steps = pos.shape[0]
    rows = np.full((n_steps, 5), np.nan, dtype=np.float64)
    for k in range(n_steps):
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 2:
            continue
        x, v = x[ok], v[ok]
        order = np.argsort(x)
        x, v = x[order], v[order]
        # 只保留区内跟驰对（后车在区内）
        g = (x[1:] - x[:-1]) - VEH_LEN
        dv = v[:-1] - v[1:]
        rear_in = (x[:-1] >= x_c - band) & (x[:-1] <= x_c + band)
        closing = (dv > 0) & (g > 0) & rear_in
        n_veh = int(((x >= x_c - band) & (x <= x_c + band)).sum())
        if not closing.any():
            rows[k] = (n_veh, 0, 0, np.nan, 0.0)
            continue
        gg, dd = g[closing], dv[closing]
        ttc = gg / dd
        dreq = dd**2 / (2.0 * gg)
        rows[k] = (n_veh, int((ttc < TTC_THR).sum()), int((dreq > D_THR).sum()),
                   float(ttc.min()), float(dreq.max()))
    return {"per_step": rows}


def summarize(arr: dict, event_t0: float, step: float, offsets: Sequence[float]) -> dict:
    rows = arr["per_step"]
    out = {}
    for off in offsets:
        k = int(round((event_t0 + off) / step))
        if k >= rows.shape[0]:
            continue
        r = rows[k]
        out[f"t0+{off:.0f}"] = {
            "n_veh_in_band": None if np.isnan(r[0]) else int(r[0]),
            "n_ttc_lt2": None if np.isnan(r[1]) else int(r[1]),
            "n_d_gt2": None if np.isnan(r[2]) else int(r[2]),
            "ttc_min": None if np.isnan(r[3]) else round(float(r[3]), 2),
            "d_max": None if np.isnan(r[4]) else round(float(r[4]), 2),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="stop")
    ap.add_argument("--sigma", type=float, default=0.0)
    ap.add_argument("--headway", type=float, default=HEADWAY)
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--react", type=float, default=0.0,
                    help="驾驶员动作间隔（秒）：0=每步都判断（机器反应）；1.0≈人类反应时间")
    ap.add_argument("--pair", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    outdir = ROOT / (args.out or f"code/outputs/analysis/P3_stop_queue_{args.tag}")
    outdir.mkdir(parents=True, exist_ok=True)
    tmp = outdir / "_scratch"
    tmp.mkdir(parents=True, exist_ok=True)

    if not args.pair:
        raise SystemExit("this trial is always paired (plain + stop); pass --pair")

    print(f"running plain arm (sigma={args.sigma}) ...")
    plain = run(tmp, "plain", args.sigma, False, args.headway, args.seed, args.react)
    print(f"  plain: {plain['n_slots_used']} vehicles, {plain['wall_seconds']:.1f}s")
    print("running stop arm ...")
    stop = run(tmp, "stop", args.sigma, True, args.headway, args.seed, args.react)
    print(f"  stop : {stop['n_slots_used']} vehicles, {stop['wall_seconds']:.1f}s,"
          f" source={stop['source_id']} t0={stop['event_t0']}")

    t0 = stop["event_t0"]
    step = stop["step_s"]
    offsets = [0, 10, 20, 30, 45, 60, 90, 120, 180, 240, 300, 400, 500, 600]

    res = {"event_t0": t0, "step_s": step, "headway": args.headway,
           "seed": args.seed, "decel": DECEL, "target_x": TARGET_X, "band": BAND,
           "react_s": args.react,
           "arms": {}}
    for name, arm in (("plain", plain), ("stop", stop)):
        e = exposure_series(arm["pos"], arm["spd"], TARGET_X, BAND)
        res["arms"][name] = summarize(e, t0, step, offsets)
        rows = e["per_step"]
        # 累计暴露车·秒（t0 之后）
        k0 = int(round(t0 / step))
        seg = rows[k0:]
        res["arms"][name]["cum"] = {
            "ttc_lt2_veh_s": round(float(np.nansum(seg[:, 1])) * step, 2),
            "d_gt2_veh_s": round(float(np.nansum(seg[:, 2])) * step, 2),
            "veh_s_in_band": round(float(np.nansum(seg[:, 0])) * step, 1),
            "ttc_min": None if np.all(np.isnan(seg[:, 3])) else round(float(np.nanmin(seg[:, 3])), 2),
            "d_max": None if np.all(np.isnan(seg[:, 4])) else round(float(np.nanmax(seg[:, 4])), 2),
        }

    print(f"\n{'arm':6} {'t-t0':>7} {'veh':>5} {'TTC<2':>6} {'D>2':>4} {'TTCmin':>7} {'Dmax':>6}")
    for name in ("plain", "stop"):
        for key, r in res["arms"][name].items():
            if key == "cum":
                continue
            print(f"{name:6} {key:>7} {str(r['n_veh_in_band']):>5} {str(r['n_ttc_lt2']):>6} "
                  f"{str(r['n_d_gt2']):>4} {str(r['ttc_min']):>7} {str(r['d_max']):>6}")
    print("\ncumulative (t0 onward):")
    for name in ("plain", "stop"):
        c = res["arms"][name]["cum"]
        print(f"  {name:6} TTC<2 = {c['ttc_lt2_veh_s']:.2f} veh·s | D>2 = {c['d_gt2_veh_s']:.2f} veh·s "
              f"| band veh·s = {c['veh_s_in_band']:.1f} | TTCmin={c['ttc_min']} Dmax={c['d_max']}")

    (outdir / "p3_stop_queue.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    np.savez_compressed(outdir / "arms.npz",
                        plain_pos=plain["pos"], plain_spd=plain["spd"],
                        stop_pos=stop["pos"], stop_spd=stop["spd"],
                        event_t0=t0, step_s=step)
    print(f"\nwritten: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
