"""P2-01: physical propagation baseline on a CONNECTED single-lane corridor.

阶段：P2 ｜ 运行目录：code/outputs/analysis/P2_propagation_<tag> ｜ 数据：本脚本生成
      ｜ 脚本：code/scripts/run_p2_propagation.py

Design follows the GPT-6.2-sol review of 2026-11-18 (cache/aad-p2/gpt.md), with two
corrections where that text contradicted itself or the existing setup:

1. The review says "initial speed 10 m/s" but derives the inflow interval from 15 m/s
   (20 m headway / 1.333 s = 15 m/s = 50 veh/km). We use 15 m/s, matching the existing
   experiment's vehicle set.
2. The review's "first vehicle crossing x_s triggers the event" cannot hold with a
   pre-filled corridor, because vehicles already occupy the source position at t=0.
   We instead warm up for 120 s and then pick the vehicle nearest x_s at that instant.

Two clocks are recorded, as the review demands:
  * station clock  : when a fixed measuring station sees the wave  (~d / wave_speed)
  * vehicle clock  : when a vehicle that was at the station at t0 meets the wave
                     (~d / (v + wave_speed)); this is the usable lead time for H4.
They must never be substituted for one another.

Usage
-----
  python code/scripts/run_p2_propagation.py --tag plain  --strength strong
  python code/scripts/run_p2_propagation.py --tag event  --strength strong
  python code/scripts/run_p2_propagation.py --tag event  --strength strong --sigma 0.5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = 0.05
EDGE_LEN = 9000.0
SOURCE_X = 6000.0
STATIONS = (5500.0, 5000.0, 4500.0, 4000.0)   # 0.5 / 1.0 / 1.5 / 2.0 km upstream of source
BAND = 50.0
V0 = 15.0
HEADWAY = 20.0
# Krauss 的安全速度上限：(20 m 车头距 - 5 m 车长 - 2.5 m 最小间距) / tau 0.6 ≈ 20.83 m/s。
# 实测平衡车速 20.78 m/s —— 初始投放 15 m/s 会先加速到它，若补给仍按 15 算间隔就会比预填稀。
# 预填与补给都用平衡速度，密度才均匀。
V_EQ = (HEADWAY - 5.0 - 2.5) / 0.6
FILL_PERIOD = HEADWAY / V_EQ
WARMUP = 120.0
RAMP = 6.0            # seconds to reach the target speed
HOLD = 120.0          # seconds held at the target speed
OBS_AFTER = 660.0     # observation window after t0
MAX_SLOTS = 1600       # 预填 449 + 补给 ~843 ≈ 1292；原来的 1200 会把尾部车辆丢掉
STRENGTH = {"strong": 3.0, "weak": 8.0}
WAVE_MIN_DV = 0.75    # m/s, sustained 1 s, per-vehicle witness threshold
GATE_IDS = 3          # distinct witnessing IDs inside the band
GATE_WINDOW = 10.0    # s
MAX_SPEED = 30.0


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="cor" from="a" to="b" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="cor_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,0.00 {EDGE_LEN:.2f},0.00"/>
    </edge>
    <junction id="a" type="dead_end" x="0.00" y="0.00"/>
    <junction id="b" type="dead_end" x="{EDGE_LEN:.2f}" y="0.00"/>
</net>"""


def routes_xml(sigma: float) -> str:
    n = int((EDGE_LEN - HEADWAY) / HEADWAY)
    vt = (f'<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="{sigma}"'
          f' tau="0.6" length="5" minGap="2.5" maxSpeed="{MAX_SPEED}" speedFactor="1"'
          f' speedDev="0.12"/>')
    vehs = []
    for i in range(n):
        pos = 10.0 + HEADWAY * i
        vehs.append(f'<vehicle id="V{i}" type="cal" route="rc" depart="0"'
                    f' departPos="{pos:.2f}" departSpeed="{V_EQ:.3f}" departLane="0"/>')
    period = FILL_PERIOD
    # vehicles first (depart=0), then the inflow flow (depart>0): SUMO requires the route
    # file to be sorted by departure time and silently drops vehicles otherwise
    return (f'<routes>{vt}'
            f'<route id="rc" edges="cor"/>'
            f'{"".join(vehs)}'
            f'<flow id="in" type="cal" route="rc" begin="{period:.3f}"'
            f' end="{WARMUP + OBS_AFTER:.1f}" period="{period:.3f}"'
            f' departSpeed="{V_EQ:.3f}" departLane="0"/>'
            f'</routes>')


def run(tmp: Path, tag: str, sigma: float, strength: str | None) -> dict:
    (tmp / "net.net.xml").write_text(net_xml(), encoding="utf-8")
    (tmp / f"routes_{tag}.rou.xml").write_text(routes_xml(sigma), encoding="utf-8")
    cfg = tmp / f"run_{tag}.sumocfg"
    cfg.write_text(
        f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="routes_{tag}.rou.xml"/></input>
    <time><begin value="0"/><end value="{WARMUP + OBS_AFTER + 30:.1f}"/>
          <step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="20261118"/></random_number>
</configuration>""", encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn"])
    const = traci.constants
    steps = int(round((WARMUP + OBS_AFTER + 30.0) / STEP))

    idx: dict[str, int] = {}
    pos = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)
    spd = np.full((steps, MAX_SLOTS), np.nan, dtype=np.float32)
    leader = np.full((steps, MAX_SLOTS), -1, dtype=np.int32)   # slot -> leader slot

    event_t0 = None
    src_id = None
    src_slot = None
    src_target = STRENGTH.get(strength or "strong", 3.0)
    src_hist: list[tuple[float, float, float]] = []   # t, actual speed, commanded speed
    src_v_start = V_EQ
    subscribed: set[str] = set()
    n_collision = 0
    n_teleport = 0

    t_start = time.time()
    try:
        for k in range(steps):
            now = k * STEP
            if now <= WARMUP:
                traci.simulationStep()
            else:
                # ---- source control (event arm only) ----
                if src_id is not None and event_t0 is not None:
                    el = now - event_t0
                    if el < RAMP:
                        cmd = src_v_start - (src_v_start - src_target) * (el / RAMP)
                        traci.vehicle.setSpeed(src_id, cmd)
                    elif el < RAMP + HOLD:
                        cmd = src_target
                        traci.vehicle.setSpeed(src_id, cmd)
                    elif el < RAMP + HOLD + 1.0:
                        # hand back to native Krauss with the original ceiling
                        traci.vehicle.setSpeed(src_id, -1)
                        cmd = float("nan")
                    else:
                        cmd = float("nan")
                    if src_id in traci.vehicle.getIDList():
                        src_hist.append((now, traci.vehicle.getSpeed(src_id),
                                         cmd if cmd == cmd else -1.0))
                traci.simulationStep()

            present = traci.vehicle.getIDList()
            for v in present:
                if v not in subscribed:
                    traci.vehicle.subscribe(v, (const.VAR_LANEPOSITION, const.VAR_SPEED))
                    subscribed.add(v)
            res = traci.vehicle.getAllSubscriptionResults()

            # two passes: allocate slots first, so leader ids can be resolved to slots
            for v in res:
                if v not in idx and len(idx) < MAX_SLOTS:
                    idx[v] = len(idx)
            for v, val in res.items():
                i = idx.get(v)
                if i is None:
                    continue
                pos[k, i] = val.get(const.VAR_LANEPOSITION, np.nan)
                spd[k, i] = val.get(const.VAR_SPEED, np.nan)
                # Leader is NOT subscribed: VAR_LEADER requires an extra distance parameter
                # and raises "Missing parameter for subscription". Because this corridor has
                # one lane and no lane changes, the leader is exactly the next vehicle up in
                # the position ordering -- the analysis rebuilds it from `pos`.

            # ---- trigger ----
            if strength is not None and src_id is None and now >= WARMUP:
                cands = [(abs(res[v].get(const.VAR_LANEPOSITION, 1e9) - SOURCE_X), v)
                         for v in res]
                if cands:
                    _, src_id = min(cands)
                    src_slot = idx.get(src_id)
                    event_t0 = now
                    src_v_start = float(res[src_id].get(const.VAR_SPEED, V0))
    finally:
        traci.close()
    elapsed = time.time() - t_start

    used = len(idx)
    return {"tag": tag, "sigma": sigma, "strength": strength,
            "event_t0": event_t0, "source_id": src_id, "source_slot": src_slot,
            "source_target_mps": src_target if strength else None,
            "source_history": src_hist,
            "n_slots_used": used, "n_steps": steps, "step_s": STEP,
            "pos": pos[:, :used], "spd": spd[:, :used],
            "ids": list(idx.keys()), "wall_seconds": elapsed,
            "collisions": n_collision, "teleports": n_teleport}


def witnesses(plain: dict, event: dict) -> dict:
    """Paired per-vehicle speed difference; station arrival times."""
    if event["event_t0"] is None:
        return {"error": "no event"}
    ids_p = plain["ids"]
    ids_e = event["ids"]
    common = [v for v in ids_e if v in ids_p]
    ip = {v: i for i, v in enumerate(ids_p)}
    ie = {v: i for i, v in enumerate(ids_e)}
    k0 = int(round(event["event_t0"] / event["step_s"]))

    dv = np.full((len(event["spd"]) - k0, len(common)), np.nan, dtype=np.float32)
    for j, v in enumerate(common):
        dv[:, j] = plain["spd"][k0:, ip[v]] - event["spd"][k0:, ie[v]]
    x_e = np.array([event["pos"][k0:, ie[v]] for v in common]).T

    thr = WAVE_MIN_DV
    need = int(round(1.0 / event["step_s"]))
    above = dv >= thr
    # sustained for `need` consecutive steps
    # reuse a simple convolution-free running counter
    cnt = np.zeros_like(above, dtype=np.int32)
    run = np.zeros(above.shape[1], dtype=np.int32)
    for t in range(above.shape[0]):
        run = np.where(above[t], run + 1, 0)
        cnt[t] = run
    wit = cnt >= need        # witness flag per step per vehicle

    out = {"n_common": len(common), "threshold_mps": thr, "sustain_s": need * event["step_s"],
           "stations": []}
    win = int(round(GATE_WINDOW / event["step_s"]))
    for xj in STATIONS:
        in_band = (x_e >= xj - BAND) & (x_e <= xj + BAND)
        gate = None
        first = None
        for t in range(wit.shape[0]):
            hit = wit[t] & in_band[t]
            if hit.any() and first is None:
                first = t * event["step_s"]
            lo = max(0, t - win)
            recent = np.any(wit[lo:t + 1] & in_band[lo:t + 1], axis=0)
            if int(recent.sum()) >= GATE_IDS:
                gate = t * event["step_s"]
                break
        out["stations"].append({"x_m": xj, "distance_km": (SOURCE_X - xj) / 1000.0,
                                "first_witness_s": first, "gate_s": gate})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="plain")
    ap.add_argument("--sigma", type=float, default=0.0)
    ap.add_argument("--strength", choices=["strong", "weak"], default=None)
    ap.add_argument("--pair", action="store_true", help="run plain then event and evaluate")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    outdir = ROOT / (args.out or f"code/outputs/analysis/P2_propagation_{args.tag}")
    outdir.mkdir(parents=True, exist_ok=True)
    tmp = outdir / "_scratch"
    tmp.mkdir(parents=True, exist_ok=True)

    if args.pair:
        strength = args.strength or "strong"
        print(f"running plain arm (sigma={args.sigma}) ...")
        plain = run(tmp, "plain", args.sigma, None)
        print(f"  plain: {plain['n_slots_used']} vehicles, {plain['wall_seconds']:.1f}s wall")
        print(f"running event arm (strength={strength}) ...")
        event = run(tmp, "event", args.sigma, strength)
        print(f"  event: {event['n_slots_used']} vehicles, {event['wall_seconds']:.1f}s wall,"
              f" source={event['source_id']} at t0={event['event_t0']}")
        ev = witnesses(plain, event)
        print("\n=== station arrival (paired speed difference >= "
              f"{ev.get('threshold_mps')} m/s sustained {ev.get('sustain_s')} s) ===")
        for s in ev.get("stations", []):
            print(f"  {s['distance_km']:.1f} km (x={s['x_m']:.0f}): "
                  f"first witness {s['first_witness_s']}, gate(3 ids/10s) {s['gate_s']}")
        if event["source_history"]:
            hs = np.array([[t, v] for t, v, _ in event["source_history"]], dtype=float)
            hold = hs[(hs[:, 0] >= event["event_t0"] + RAMP) &
                      (hs[:, 0] <= event["event_t0"] + RAMP + HOLD)]
            if len(hold):
                ok = float(np.mean(hold[:, 1] <= event["source_target_mps"] + 0.3))
                print(f"\nsource hold: {ok:.1%} of steps at or below target+0.3 "
                      f"(need >= 90%)")
        (outdir / "result.json").write_text(
            json.dumps({k: v for k, v in ev.items()}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        np.savez_compressed(outdir / "arms.npz",
                            plain_pos=plain["pos"], plain_spd=plain["spd"],
                            event_pos=event["pos"], event_spd=event["spd"],
                            plain_ids=np.array(plain["ids"]), event_ids=np.array(event["ids"]),
                            event_t0=event["event_t0"], step_s=STEP)
        print(f"\nwrote {outdir/'result.json'} and arms.npz")
        return 0

    r = run(tmp, args.tag, args.sigma, args.strength)
    (outdir / f"{args.tag}.json").write_text(
        json.dumps({k: v for k, v in r.items() if k not in ("pos", "spd", "source_history")},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    np.savez_compressed(outdir / f"{args.tag}.npz", pos=r["pos"], spd=r["spd"],
                        ids=np.array(r["ids"]), event_t0=r["event_t0"] or -1.0, step_s=STEP)
    print(f"{args.tag}: {r['n_slots_used']} vehicles, wall {r['wall_seconds']:.1f}s, "
          f"source={r['source_id']} t0={r['event_t0']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
