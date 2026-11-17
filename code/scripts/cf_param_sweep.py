"""Can the simulator be pushed into the near-conflict regime at all?

Background: on real leader trajectories the simulated follower never gets closer than its
starting gap, while real followers get within 0.3-1.6 m and produce formal safety events. Two
explanations were on the table:
  (a) the hardcoded EIDM constant EST_REAC_THRESHOLD = 3 m, which disables perception error and
      reaction time below 3 m, so behaviour in the near-conflict band is unrealistic;
  (b) the models' safety constraint itself, which keeps the follower from ever entering that band.

The distinction decides whether patching SUMO's source is worth a rebuild: (a) only matters if
the vehicle already got below 3 m, so if (b) holds the patch changes behaviour in a regime we
never reach.

Check: sweep the vType parameters that govern how close a model is willing to get, on the same
real leader trajectories, and report the minimum gap each setting reaches. No source change, no
rebuild.

emergencyDecel is the interesting one: it caps the hardest braking the vehicle may use, so a low
value makes stopping physically impossible and forces proximity (and eventually collisions).

Usage:
  python code/scripts/cf_param_sweep.py --grid coarse
"""
from __future__ import annotations

import argparse
import itertools
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "scripts"))

from model_switch_trial import collect_pairs, STAGING  # noqa: E402
from compare_real_vs_sim_follower import build_trace, ttc_of, count_p2, STEP  # noqa: E402


def make_cfg(workdir: Path, attrs: dict) -> tuple[Path, float, float]:
    """Write a vType for each role from a single attribute set, plus the run config.

    Attributes are built as a dict and rendered once: emitting the same attribute twice makes
    SUMO exit, and TraCI then only reports 'Connection closed by SUMO', which hides the cause.
    """
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    shutil.copy2(STAGING / "network.net.xml", workdir / "network.net.xml")

    base = {"length": "5.0", "maxSpeed": "30", "accel": "2.6", "decel": "4.5"}
    base.update(attrs)
    # carFollowModel is rendered separately below; letting it through here would emit the
    # attribute twice and SUMO would exit with only "Connection closed by SUMO" to show for it
    rendered = " ".join(f'{k}="{v}"' for k, v in base.items() if k != "carFollowModel")
    tau = float(base.get("tau", 1.0))
    mingap = float(base.get("minGap", 1.0))

    routes = f"""<routes>
  <vType id="leader" carFollowModel="{base.get('carFollowModel', 'Krauss')}" {rendered}/>
  <vType id="follower" carFollowModel="{base.get('carFollowModel', 'Krauss')}" {rendered}/>
  <route id="r0" edges="main_ext"/>
</routes>"""
    (workdir / "joint_routes.rou.xml").write_text(routes, encoding="utf-8")
    cfg = f"""<configuration>
    <input><net-file value="network.net.xml"/><route-files value="joint_routes.rou.xml"/></input>
    <time><begin value="0"/><end value="60"/><step-length value="0.05"/></time>
    <processing><time-to-teleport value="-1"/><collision.action value="warn"/><no-step-log value="true"/></processing>
</configuration>"""
    p = workdir / "joint.sumocfg"
    p.write_text(cfg, encoding="utf-8")
    return p, tau, mingap


def sweep(grid: list[dict], pairs: list, outdir: Path) -> list[dict]:
    from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay

    results = []
    for i, attrs in enumerate(grid, 1):
        tag = "_".join(f"{k}{v}" for k, v in sorted(attrs.items())
                       if k in ("emergencyDecel", "sigma", "tau", "carFollowModel"))
        cfg, tau, mingap = make_cfg(outdir / f"_p{i}", attrs)
        gaps, ttcs, status = [], [], None
        for min_ttc, min_gap, t, gap, vf, vl, name in pairs:
            trace = build_trace(t, gap, vf, vl)
            if trace.empty:
                continue
            try:
                res = run_joint_replay(
                    trace, sumo_cfg=cfg, lane_id="main_ext_0",
                    geometry_follower_length_m=5.0, geometry_leader_length_m=5.0,
                    follower_tau_s=tau, follower_min_gap_m=mingap,
                    sumo_binary="sumo", seed=20261116, step_s=STEP,
                    save_trace=True, initialization_mode="safe_then_move",
                )
            except Exception as exc:  # noqa: BLE001
                status = f"{type(exc).__name__}: {str(exc)[:80]}"
                continue
            status = res.get("status")
            rr = res.get("rows") or []
            if not rr:
                continue
            gg = np.array([r["net_gap_m"] for r in rr], float)
            ff = np.array([r["follower_speed_mps"] for r in rr], float)
            ll = np.array([r["leader_speed_mps"] for r in rr], float)
            tt = np.array([r["input_time_s"] for r in rr], float)
            gaps.append(float(np.nanmin(gg)))
            ttcs.append(float(np.nanmin(ttc_of(gg, ff, ll))))
        row = dict(attrs)
        row.update({
            "tag": tag,
            "n_ok": len(gaps),
            "min_gap_overall": round(min(gaps), 3) if gaps else None,
            "median_min_gap": round(float(np.median(gaps)), 3) if gaps else None,
            "min_ttc_overall": round(min(ttcs), 3) if ttcs else None,
            "median_min_ttc": round(float(np.median(ttcs)), 3) if ttcs else None,
            "n_below_3m": sum(1 for g in gaps if g < 3.0),
            "n_below_1m": sum(1 for g in gaps if g < 1.0),
            "status": status,
        })
        results.append(row)
        print(f"[{i}/{len(grid)}] {tag:<56} "
              f"minGap={row['min_gap_overall']}  median={row['median_min_gap']}  "
              f"<3m {row['n_below_3m']}/{row['n_ok']}  <1m {row['n_below_1m']}")
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default="coarse", choices=["coarse", "fine"])
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--out", default="code/outputs/analysis/cf_param_sweep_20261117")
    args = ap.parse_args()

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    pairs = collect_pairs(args.top)
    print(f"{len(pairs)} real pairs with trustworthy events")
    print(f"real min gaps: {[round(p[1], 2) for p in pairs]}\n")

    if args.grid == "coarse":
        # Focus on the two levers that decide whether proximity is even reachable:
        # emergencyDecel caps how hard the vehicle may brake, sigma controls randomness.
        grid = [dict(carFollowModel="Krauss", decel="4.5", **{
                    "tau": str(tau), "minGap": "0.5", "sigma": str(sig),
                    "emergencyDecel": str(ed)})
                for tau, sig, ed in itertools.product(
                    [1.0, 0.5], [0.0, 0.5, 0.9], [9.0, 7.0, 5.0, 4.0, 3.0])]
    else:
        grid = [dict(carFollowModel="Krauss", decel="4.5", tau=str(tau), minGap="0.5",
                     sigma=str(sig), emergencyDecel=str(ed))
                for tau, sig, ed in itertools.product(
                    [1.0, 0.6, 0.4], [0.5, 0.9, 1.0], [4.0, 3.0, 2.0])]

    print(f"sweeping {len(grid)} settings x {len(pairs)} pairs\n")
    results = sweep(grid, pairs, outdir)

    ok = [r for r in results if r["n_ok"]]
    print("\n=== can the simulator reach the near-conflict band? ===")
    if not ok:
        print("  no setting produced usable trajectories")
    else:
        best = min(ok, key=lambda r: r["min_gap_overall"])
        reached = [r for r in ok if r["n_below_3m"] >= 3]
        print(f"  closest setting: {best['tag']}")
        print(f"    minimum gap {best['min_gap_overall']} m, median {best['median_min_gap']} m, "
              f"{best['n_below_3m']}/{best['n_ok']} pairs below 3 m")
        print(f"  settings reaching <3 m in at least half the pairs: {len(reached)}/{len(ok)}")
        print(f"  settings reaching <1 m in at least one pair: "
              f"{sum(1 for r in ok if r['n_below_1m'] > 0)}/{len(ok)}")
        print(f"  real followers reached: {[round(p[1], 2) for p in pairs]}")

    (outdir / "sweep.json").write_text(
        json.dumps({"grid": args.grid, "pairs": len(pairs),
                    "real_min_gaps": [round(p[1], 3) for p in pairs],
                    "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {outdir/'sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())