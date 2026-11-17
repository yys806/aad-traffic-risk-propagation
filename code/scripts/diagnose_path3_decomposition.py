"""Decompose the path-3 information-content effect: which vehicles actually carry it?

The regional effect is only -0.63%, while a single vehicle moving from tau 0.6 to 1.0 s
should see its own risk fall by roughly 5%. That gap has to be explained before the number
can be used, and there are several candidate explanations that are not distinguishable from
the aggregate alone:

  H1  denominator/treated mismatch: risk is averaged over the roster locked at t=WARMUP, but
      the treatment is applied to whoever is in the region at each step. If most roster
      vehicles have already left the region by the time the event fires, the treated vehicles
      contribute little to the measured average.
  H2  dose dilution: the content-graded delta is multiplied by depth (min 0.2) and validity
      (min 0.1), so the mean applied delta is far below the nominal peak.
  H3  short dwell: vehicles spend little time in the 1 km region, so a headway change has
      little time to affect their measured gap.
  H4  convexity: sham spreads a constant delta while opn1 concentrates it near the zone
      centre; if risk is convex in headway, spreading and concentrating give different means
      even at equal total dose.

This script reruns a single seed and records per-vehicle traces so each hypothesis can be
checked directly instead of argued about.

Usage:
  python code/scripts/diagnose_path3_decomposition.py --seed 20261116
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

import run_stage1_isolated_two_arm as base
import run_stage1_path3 as p3
from riskprop.stage_0_5_fixed_leader_traci import load_traci

SUMO = "sumo"
STEP = base.STEP
WARMUP = base.WARMUP
END = base.END
TGT_REGION = base.TGT_REGION


def run(seed: int, arm: str, sham_delta: float = 0.43) -> dict:
    scratch = ROOT / f"code/outputs/analysis/_diag_path3/{arm}"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "net.net.xml").write_text(base.net_xml(), encoding="utf-8")
    (scratch / "routes.rou.xml").write_text(base.routes_xml(), encoding="utf-8")
    cfg = scratch / "c.sumocfg"
    cfg.write_text(f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="routes.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{seed}"/></random_number>
</configuration>""", encoding="utf-8")

    opn = arm == "opn1"
    sham = arm == "sham"

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn"])
    steps = int(round(END / STEP))
    tgt_ids = [f"T{i}" for i in range(base.cohort_size())]

    event_time: float | None = None
    src_speed0 = None
    roster: tuple[str, ...] | None = None

    # per-vehicle records
    veh_tau: dict[str, dict[float, float]] = defaultdict(dict)     # v -> {t: tau}
    veh_rho: dict[str, dict[float, float]] = defaultdict(dict)     # v -> {t: rho}
    veh_gap: dict[str, dict[float, float]] = defaultdict(dict)
    veh_in: dict[str, list[float]] = defaultdict(list)             # v -> times in region
    veh_applied: dict[str, float] = {}                             # v -> first time treated
    applied_delta: dict[str, list[float]] = defaultdict(list)

    try:
        for k in range(steps):
            now = k * STEP
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())

            if "S0" in present:
                s = traci.vehicle.getSpeed("S0")
                if src_speed0 is None:
                    src_speed0 = s
                if event_time is None and src_speed0 is not None and s < src_speed0 - 1.0:
                    event_time = now

            in_region = []
            for v in tgt_ids:
                if v not in present:
                    continue
                x = traci.vehicle.getLanePosition(v)
                if TGT_REGION[0] <= x < TGT_REGION[1]:
                    in_region.append((v, x, traci.vehicle.getSpeed(v)))
                    veh_in[v].append(now)

            if roster is None and now >= WARMUP:
                roster = tuple(sorted(v for v, _, _ in in_region))
            if roster is None:
                continue

            # per-vehicle risk and state (same definition as the experiment)
            for v in roster:
                if v not in present:
                    continue
                x = traci.vehicle.getLanePosition(v)
                if not (TGT_REGION[0] <= x < TGT_REGION[1]):
                    continue
                sp = traci.vehicle.getSpeed(v)
                lead = traci.vehicle.getLeader(v, 200.0)
                if not lead:
                    continue
                lid, gap = lead
                if gap <= 0 or lid not in present:
                    continue
                lsp = traci.vehicle.getSpeed(lid)
                veh_rho[v][now] = p3.rho_from_ttc(p3.ttc_braking(gap, sp, lsp))
                veh_gap[v][now] = gap
                veh_tau[v][now] = float(traci.vehicle.getTau(v))

            # treatment (identical to the experiment)
            if sham and event_time is not None:
                for v, _x, _sp in in_region:
                    traci.vehicle.setTau(v, min(p3.TAU_CAP, p3.NATIVE_TAU + sham_delta))
                    if v not in veh_applied:
                        veh_applied[v] = now
                    applied_delta[v].append(sham_delta)
                    veh_tau[v][now] = float(traci.vehicle.getTau(v))
            elif opn and event_time is not None:
                for v, x, _sp in in_region:
                    delta = p3.headway_delta("HIGH", x, now, event_time, event_time + 45.0,
                                             content_graded=True)
                    traci.vehicle.setTau(v, min(p3.TAU_CAP, p3.NATIVE_TAU + delta))
                    if v not in veh_applied:
                        veh_applied[v] = now
                    applied_delta[v].append(delta)
                    veh_tau[v][now] = float(traci.vehicle.getTau(v))
    finally:
        traci.close()

    return {
        "arm": arm, "seed": seed, "event_time": event_time,
        "roster": list(roster) if roster else [],
        "veh_rho": {v: {round(t, 3): r for t, r in d.items()} for v, d in veh_rho.items()},
        "veh_tau": {v: {round(t, 3): x for t, x in d.items()} for v, d in veh_tau.items()},
        "veh_gap": {v: {round(t, 3): g for t, g in d.items()} for v, d in veh_gap.items()},
        "veh_in_region_times": {v: [round(t, 3) for t in ts] for v, ts in veh_in.items()},
        "veh_applied_at": veh_applied,
        "applied_delta": {v: ds for v, ds in applied_delta.items()},
    }


def analyse(res: dict) -> None:
    arm = res["arm"]
    ev = res["event_time"]
    roster = res["roster"]
    print(f"\n{'='*66}\n臂 {arm}   事件时刻 {ev} s   roster {len(roster)} 辆\n{'='*66}")

    post = [t for t in [round(ev + i * 0.05, 3) for i in range(1, 800)]]

    # H1: how many roster vehicles are still in the region after the event?
    in_after = [v for v in roster
                if any(t >= ev for t in res["veh_in_region_times"].get(v, []))]
    print(f"H1 分母/处理错配")
    print(f"   roster 锁定 {len(roster)} 辆")
    print(f"   事件后仍在区域内的 roster 车: {len(in_after)} 辆 "
          f"({len(in_after)/max(1,len(roster)):.1%})")
    treated = set(res["veh_applied_at"])
    print(f"   实际被处理的车: {len(treated)} 辆")
    print(f"   其中属于 roster 的: {len(treated & set(roster))} 辆")
    print(f"   被处理但不在 roster 里（不计入风险分子）: {len(treated - set(roster))} 辆")

    # H2: dose actually applied
    deltas = [d for ds in res["applied_delta"].values() for d in ds]
    if deltas:
        print(f"\nH2 剂量稀释")
        print(f"   实际施加的 delta: 均值 {np.mean(deltas):.4f} s  "
              f"中位 {np.median(deltas):.4f}  p10 {np.percentile(deltas,10):.4f}  "
              f"p90 {np.percentile(deltas,90):.4f}  最大 {max(deltas):.4f}")
        print(f"   标称峰值 1.2 s，实际均值只有峰值的 {np.mean(deltas)/1.2:.1%}")

    # H3: dwell time in region
    dwell = {v: len(ts) * STEP for v, ts in res["veh_in_region_times"].items()}
    if dwell:
        print(f"\nH3 停留时长")
        print(f"   区域内停留时长: 中位 {np.median(list(dwell.values())):.1f} s  "
              f"最大 {max(dwell.values()):.1f} s")
        post_dwell = {v: sum(1 for t in ts if t >= ev) * STEP
                      for v, ts in res["veh_in_region_times"].items()}
        nz = [x for x in post_dwell.values() if x > 0]
        if nz:
            print(f"   事件后停留时长: 中位 {np.median(nz):.1f} s  "
                  f"平均 {np.mean(nz):.1f} s")

    # per-vehicle risk change: treated vs untreated
    def mean_rho(v, t_lo, t_hi):
        vals = [r for t, r in res["veh_rho"].get(v, {}).items() if t_lo <= t <= t_hi]
        return float(np.mean(vals)) if vals else None

    pre_lo, pre_hi = ev - 10.0, ev
    post_lo, post_hi = ev, ev + 25.0

    rows = []
    for v in roster:
        rp = mean_rho(v, pre_lo, pre_hi)
        ra = mean_rho(v, post_lo, post_hi)
        if rp is None or ra is None:
            continue
        rows.append({"v": v, "pre": rp, "post": ra, "d": ra - rp,
                     "treated": v in treated,
                     "dwell_post": sum(1 for t in res["veh_in_region_times"].get(v, [])
                                       if t >= ev) * STEP})
    if rows:
        print(f"\n逐车风险变化（事件前 10 s → 事件后 25 s，仅 roster 内可测车 {len(rows)} 辆）")
        for label, sel in [("被处理", [r for r in rows if r["treated"]]),
                           ("未处理", [r for r in rows if not r["treated"]])]:
            if sel:
                d = [r["d"] for r in sel]
                print(f"   {label:<6} n={len(sel):>3}  平均变化 {np.mean(d):+.6f}  "
                      f"中位 {np.median(d):+.6f}  负向占比 "
                      f"{sum(1 for x in d if x<0)/len(d):.1%}")

    # H4: convexity check - risk vs tau curvature
    pairs = []
    for v, d in res["veh_tau"].items():
        for t, tau in d.items():
            if v in res["veh_rho"] and t in res["veh_rho"][v]:
                pairs.append((tau, res["veh_rho"][v][t]))
    if len(pairs) > 50:
        arr = np.array(pairs)
        order = np.argsort(arr[:, 0])
        arr = arr[order]
        bins = np.array_split(arr, 8)
        print(f"\nH4 凸性检查（tau 分箱 → 平均风险）")
        for b in bins:
            if len(b):
                print(f"   tau≈{np.mean(b[:,0]):.2f}  n={len(b):>4}  "
                      f"平均 rho={np.mean(b[:,1]):.5f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261116)
    ap.add_argument("--out", default="code/outputs/analysis/path3_decomposition_20261116")
    args = ap.parse_args()

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    all_res = {}
    for arm in ("opn0", "sham", "opn1"):
        res = run(args.seed, arm)
        all_res[arm] = res
        analyse(res)

    (outdir / f"decomposition_seed{args.seed}.json").write_text(
        json.dumps(all_res, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {outdir}/decomposition_seed{args.seed}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())