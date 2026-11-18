"""P3-01b: 场景准入第 2 试 —— 固定目标区内合流，下游队尾扫过合流口

阶段：P3 ｜ 运行目录：code/outputs/analysis/P3_merge_<tag> ｜ 数据：本脚本生成（SUMO）
      ｜ 脚本：code/scripts/run_p3_merge.py

为什么做这一试（见 docs/P3_场景准入规则_20261119.md 第六节）：
  第 1 试证明「急停 + 保持」在单车道里传得到但不产生闭合 —— Krauss 的预见距离约 55 m，
  远大于 20 m 车头距，队尾还没贴上就已经减完速了。
  合流改变的是**后车面对的前车本身**：一辆低速车插进来，后车没有那 55 m 的预见距离。

路网：主线 1 车道 + 入口辅助车道 200 m，在 x=4000 汇入；下游 x=6000 放停车源事件。
目标区：合流段 x=4000 ± 100 m。

用法
-----
  python code/scripts/run_p3_merge.py --pair --headway 30 --aux-rate 250 --seed 20261119
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
NETCONVERT = "netconvert"
STEP = 0.05
EDGE_LEN = 15000.0
MERGE_X = 4000.0          # 合流点
AUX_LEN = 200.0           # 入口辅助车道长度
SOURCE_X = 6000.0         # 停车源事件（下游）
TARGET_X = MERGE_X        # 目标区中心
BAND = 100.0              # 目标区半宽
WARMUP = 120.0
DECEL = 4.5
HOLD = 660.0
OBS_AFTER = 660.0
MAX_SLOTS = 2000
MAX_SPEED = 30.0
LANE_SPEED = 17.0         # 车道限速：让主线跑在自由流 17 m/s，30 m 车头距 ≈ 1.76 s 时距
VEH_LEN = 5.0
GAP_EPS = 0.5              # m，净距小于此值视为重叠/数值假象，不计入
TTC_THR = 2.0
D_THR = 2.0


def build_net(tmp: Path) -> Path:
    """用 netconvert 生成「车道缩减」式合流：入口车道在 200 m 内必须并进主线。

    不用「两条边同时汇入一条边」的路口式合流——实测那种接法会让主线在路口前堵死
    （netconvert 把路口中心放到 y=4，主线的车进不去），造出的是假暴露。
    车道缩减是 SUMO 原生支持的强制并道，行为可靠。
    """
    n1 = MERGE_X - AUX_LEN
    (tmp / "nodes.nod.xml").write_text(f"""<nodes>
  <node id="a"  x="0"        y="0"  type="dead_end"/>
  <node id="am" x="{n1 - AUX_LEN:.1f}" y="-4" type="dead_end"/>
  <node id="n1" x="{n1:.1f}" y="0"  type="priority"/>
  <node id="m"  x="{MERGE_X:.1f}" y="0" type="priority"/>
  <node id="b"  x="{EDGE_LEN:.1f}" y="0" type="dead_end"/>
</nodes>""", encoding="utf-8")

    (tmp / "edges.edg.xml").write_text(f"""<edges>
  <edge id="main1"  from="a"  to="n1" numLanes="1" speed="{LANE_SPEED}" priority="2"/>
  <edge id="aux"    from="am" to="n1" numLanes="1" speed="{LANE_SPEED}" priority="1"/>
  <edge id="merge2" from="n1" to="m"  numLanes="2" speed="{LANE_SPEED}" priority="2"/>
  <edge id="main2"  from="m"  to="b"  numLanes="1" speed="{LANE_SPEED}" priority="2"/>
</edges>""", encoding="utf-8")

    (tmp / "con.con.xml").write_text(f"""<connections>
  <connection from="main1"  to="merge2" fromLane="0" toLane="0"/>
  <connection from="aux"    to="merge2" fromLane="0" toLane="1"/>
  <connection from="merge2" to="main2"  fromLane="0" toLane="0"/>
</connections>""", encoding="utf-8")

    net = tmp / "net.net.xml"
    subprocess.run([NETCONVERT,
                    "--node-files", str(tmp / "nodes.nod.xml"),
                    "--edge-files", str(tmp / "edges.edg.xml"),
                    "--connection-files", str(tmp / "con.con.xml"),
                    "--output-file", str(net),
                    "--no-turnarounds", "true",
                    "--junctions.corner-detail", "5",
                    "--no-internal-links", "false"],
                   check=True, capture_output=True)
    return net


def routes_xml(sigma: float, headway: float, aux_rate: float, seed: int) -> str:
    v_eq = min((headway - VEH_LEN - 2.5) / 0.6, LANE_SPEED - 1.0)
    period = headway / v_eq
    aux_period = 3600.0 / aux_rate
    n = int((MERGE_X - AUX_LEN - 50.0) / headway)   # 只预填 main1 段（长度 = MERGE_X − AUX_LEN）
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="{sigma}"'
          f' tau="0.6" length="5" minGap="2.5" maxSpeed="{MAX_SPEED}" speedFactor="1"'
          f' speedDev="0.12"/>')
    vehs = []
    for i in range(n):
        pos = 10.0 + headway * i
        vehs.append(f'<vehicle id="V{i}" type="cal" route="rm" depart="0"'
                    f' departPos="{pos:.2f}" departSpeed="{v_eq:.3f}" departLane="0"/>')
    end = WARMUP + OBS_AFTER
    return (f'<routes>{vt}'
            f'<route id="rm" edges="main1 merge2 main2"/>'
            f'<route id="ra" edges="aux merge2 main2"/>'
            f'{"".join(vehs)}'
            f'<flow id="in" type="cal" route="rm" begin="{period:.3f}" end="{end:.1f}"'
            f' period="{period:.3f}" departSpeed="{v_eq:.3f}" departLane="0"/>'
            f'<flow id="auxf" type="cal" route="ra" begin="{WARMUP*0.5:.1f}" end="{end:.1f}"'
            f' period="{aux_period:.3f}" departSpeed="8.0" departLane="0"/>'
            f'</routes>')


def run(tmp: Path, tag: str, sigma: float, stop: bool,
        headway: float, aux_rate: float, seed: int) -> dict:
    net = build_net(tmp)
    (tmp / f"routes_{tag}.rou.xml").write_text(
        routes_xml(sigma, headway, aux_rate, seed), encoding="utf-8")
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
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true",
                 "--collision.action", "warn", "--time-to-teleport", "-1"])
    const = traci.constants
    steps = int(round((WARMUP + OBS_AFTER + 30.0) / STEP))

    idx: dict[str, int] = {}
    pos = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)
    spd = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)
    # 边缘编号：合流口有两条并行车道，必须按 edge 分组配对，否则横坐标相近的两车
    # 会被当成净距≈0 的跟驰对，凭空造出 D=1e5 的假暴露（实测过）
    road_code: dict[str, int] = {}
    road = np.full((steps, MAX_SLOTS), -1, dtype=np.int16)

    event_t0 = None
    src_id = None
    src_v_start = min(max((headway - VEH_LEN - 2.5) / 0.6, 1.0), LANE_SPEED - 1.0)
    src_hist: list[tuple[float, float, float]] = []
    src_gone_at = None
    subscribed: set[str] = set()

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
                        cmd = float("nan")
                        if src_gone_at is None:
                            src_gone_at = now
                    if alive:
                        src_hist.append((now, traci.vehicle.getSpeed(src_id),
                                         cmd if cmd == cmd else -1.0))
                traci.simulationStep()

            present = traci.vehicle.getIDList()
            for v in present:
                if v not in subscribed:
                    traci.vehicle.subscribe(v, (const.VAR_LANEPOSITION, const.VAR_SPEED,
                                                const.VAR_ROAD_ID))
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
                rid = val.get(const.VAR_ROAD_ID, "")
                if rid not in road_code:
                    road_code[rid] = len(road_code)
                road[k, i] = road_code[rid]

            if stop and src_id is None and now >= WARMUP:
                cands = [(abs(res[v].get(const.VAR_LANEPOSITION, 1e9) - SOURCE_X), v)
                         for v in res]
                if cands:
                    _, src_id = min(cands)
                    event_t0 = now
                    src_v_start = float(res[src_id].get(const.VAR_SPEED, src_v_start))
    finally:
        traci.close()

    used = len(idx)
    return {"tag": tag, "sigma": sigma, "stop": stop, "headway": headway,
            "aux_rate": aux_rate, "event_t0": event_t0, "source_id": src_id,
            "source_v_start": src_v_start, "source_history": src_hist,
            "source_gone_at": src_gone_at,
            "n_slots_used": used, "n_steps": steps, "step_s": STEP,
            "pos": pos[:, :used], "spd": spd[:, :used], "road": road[:, :used],
            "ids": list(idx.keys()), "wall_seconds": time.time() - t_start}


def exposure_series(pos: np.ndarray, spd: np.ndarray, road: np.ndarray,
                    x_c: float, band: float) -> np.ndarray:
    """逐帧算目标区暴露。**只在同一条 edge 内配对**。

    合流口有 main1 与 aux 两条并行车道，两条道上的车横坐标可以几乎相同；
    按位置排序配对会把它们当成净距≈0 的跟驰对，造出 D=1e5 量级的假暴露。
    """
    n_steps = pos.shape[0]
    rows = np.full((n_steps, 6), np.nan, dtype=np.float64)
    for k in range(n_steps):
        x_all = pos[k].astype(np.float64)
        v_all = spd[k].astype(np.float64)
        r_all = road[k]
        ok = np.isfinite(x_all) & np.isfinite(v_all) & (r_all >= 0)
        if ok.sum() < 2:
            continue
        n_veh = int((ok & (x_all >= x_c - band) & (x_all <= x_c + band)).sum())
        gs, dvs = [], []
        for code in np.unique(r_all[ok]):
            m = ok & (r_all == code)
            x = x_all[m]
            v = v_all[m]
            if x.size < 2:
                continue
            order = np.argsort(x)
            x, v = x[order], v[order]
            g = (x[1:] - x[:-1]) - VEH_LEN
            dv = v[:-1] - v[1:]
            rear_in = (x[:-1] >= x_c - band) & (x[:-1] <= x_c + band)
            keep = (dv > 0) & (g > GAP_EPS) & rear_in
            if keep.any():
                gs.append(g[keep])
                dvs.append(dv[keep])
        if not gs:
            rows[k] = (n_veh, 0, 0, np.nan, 0.0, 0.0)
            continue
        gg = np.concatenate(gs)
        dd = np.concatenate(dvs)
        ttc = gg / dd
        dreq = dd**2 / (2.0 * gg)
        rows[k] = (n_veh, int((ttc < TTC_THR).sum()), int((dreq > D_THR).sum()),
                   float(ttc.min()), float(dreq.max()), float(dd.max()))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="merge")
    ap.add_argument("--sigma", type=float, default=0.0)
    ap.add_argument("--headway", type=float, default=30.0)
    ap.add_argument("--aux-rate", type=float, default=250.0, help="入口流量 veh/h")
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--pair", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    outdir = ROOT / (args.out or f"code/outputs/analysis/P3_merge_{args.tag}")
    outdir.mkdir(parents=True, exist_ok=True)
    tmp = outdir / "_scratch"
    tmp.mkdir(parents=True, exist_ok=True)

    if not args.pair:
        raise SystemExit("this trial is always paired; pass --pair")

    print(f"running plain arm (headway={args.headway}, aux={args.aux_rate}/h) ...")
    plain = run(tmp, "plain", args.sigma, False, args.headway, args.aux_rate, args.seed)
    print(f"  plain: {plain['n_slots_used']} vehicles, {plain['wall_seconds']:.1f}s")
    print("running event arm (downstream stop at x=6000) ...")
    stop = run(tmp, "event", args.sigma, True, args.headway, args.aux_rate, args.seed)
    print(f"  event: {stop['n_slots_used']} vehicles, {stop['wall_seconds']:.1f}s,"
          f" source={stop['source_id']} t0={stop['event_t0']}")

    t0 = stop["event_t0"]
    step = stop["step_s"]
    offsets = [0, 10, 20, 30, 45, 60, 90, 120, 180, 240, 300, 400, 500, 600]
    res = {"event_t0": t0, "step_s": step, "headway": args.headway,
           "aux_rate": args.aux_rate, "seed": args.seed,
           "target_x": TARGET_X, "band": BAND, "arms": {}}

    print(f"\n{'arm':6} {'t-t0':>7} {'veh':>4} {'TTC<2':>6} {'D>2':>4} {'TTCmin':>8} {'Dmax':>6} {'dvmax':>6}")
    for name, arm in (("plain", plain), ("event", stop)):
        rows = exposure_series(arm["pos"], arm["spd"], arm["road"], TARGET_X, BAND)
        k0 = int(round(t0 / step))
        seg = rows[k0:]
        cum = {
            "ttc_lt2_veh_s": round(float(np.nansum(seg[:, 1])) * step, 2),
            "d_gt2_veh_s": round(float(np.nansum(seg[:, 2])) * step, 2),
            "veh_s_in_band": round(float(np.nansum(seg[:, 0])) * step, 1),
            "ttc_min": None if np.all(np.isnan(seg[:, 3])) else round(float(np.nanmin(seg[:, 3])), 2),
            "d_max": None if np.all(np.isnan(seg[:, 4])) else round(float(np.nanmax(seg[:, 4])), 2),
            "dv_max": None if np.all(np.isnan(seg[:, 5])) else round(float(np.nanmax(seg[:, 5])), 2),
        }
        res["arms"][name] = {"cum": cum, "snap": {}}
        for off in offsets:
            k = int(round((t0 + off) / step))
            if k >= rows.shape[0]:
                continue
            r = rows[k]
            rng = {"n_veh": None if np.isnan(r[0]) else int(r[0]),
                   "n_ttc_lt2": None if np.isnan(r[1]) else int(r[1]),
                   "n_d_gt2": None if np.isnan(r[2]) else int(r[2]),
                   "ttc_min": None if np.isnan(r[3]) else round(float(r[3]), 2),
                   "d_max": None if np.isnan(r[4]) else round(float(r[4]), 2),
                   "dv_max": None if np.isnan(r[5]) else round(float(r[5]), 2)}
            res["arms"][name]["snap"][f"t0+{off}"] = rng
            print(f"{name:6} {off:7d} {str(rng['n_veh']):>4} {str(rng['n_ttc_lt2']):>6} "
                  f"{str(rng['n_d_gt2']):>4} {str(rng['ttc_min']):>8} {str(rng['d_max']):>6} "
                  f"{str(rng['dv_max']):>6}")

    print("\ncumulative (t0 onward):")
    for name in ("plain", "event"):
        c = res["arms"][name]["cum"]
        print(f"  {name:6} TTC<2 = {c['ttc_lt2_veh_s']:.2f} veh·s | D>2 = {c['d_gt2_veh_s']:.2f} veh·s "
              f"| band veh·s = {c['veh_s_in_band']:.1f} | TTCmin={c['ttc_min']} Dmax={c['d_max']} "
              f"| dvmax={c['dv_max']}")

    (outdir / "p3_merge.json").write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    np.savez_compressed(outdir / "arms.npz",
                        plain_pos=plain["pos"], plain_spd=plain["spd"], plain_road=plain["road"],
                        event_pos=stop["pos"], event_spd=stop["spd"], event_road=stop["road"],
                        event_t0=t0, step_s=step)
    print(f"\nwritten: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
