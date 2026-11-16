"""Does changing the car-following model recover the near-conflicts Krauss misses?

The isolated experiment showed Krauss keeps safe gaps; the real-follower comparison showed
real followers reach min-TTC 0.807 s while Krauss stays at 4.96 s. Before committing to a
model switch (decision D3), the cheapest useful test is: same real leader trajectory, same
initial state, only carFollowModel changed. If a candidate reproduces real-follower TTCs,
switching is worth the re-run cost; if every model stays far away, the model is not the lever.

Models available in SUMO 1.26: Krauss, EIDM, IDM, W99, Wiedemann, DKel, ACC, CACC.
EIDM is the one designed for human drivers (perception error, reaction time, estimation
update interval), so it is the primary candidate.

Usage:
  python code/scripts/model_switch_trial.py --models Krauss EIDM IDM
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

from screen_mitra_risk_pairs import load_member, pair_series  # noqa: E402
from compare_real_vs_sim_follower import (  # noqa: E402
    build_trace, ttc_of, count_p2, STEP,
)

STAGING = ROOT / "local_research/staging/task16_20261031"


def make_cfg(workdir: Path, model: str) -> Path:
    """Copy the Task16 prototype and swap carFollowModel on both vTypes."""
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    shutil.copy2(STAGING / "network.net.xml", workdir / "network.net.xml")
    routes = f"""<routes>
  <vType id="leader" carFollowModel="{model}" accel="2.6" decel="4.5" sigma="0" tau="1.0" length="5.0" minGap="1.0" maxSpeed="30"/>
  <vType id="follower" carFollowModel="{model}" accel="2.6" decel="4.5" sigma="0.0" tau="1.0" length="5.0" minGap="1.0" maxSpeed="30"/>
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
    return p


def collect_pairs(top: int, interior_only: bool = True):
    veh = load_member("T1_D1.csv")
    scored = []
    for vid, d in veh.items():
        lid = next((x for x in d["leader"] if x), None)
        if not lid or lid not in veh:
            continue
        s = pair_series(d, veh[lid])
        if s is None:
            continue
        t, gap, vf, vl = s
        if gap.min() <= 0:
            continue
        ttc = ttc_of(gap, vf, vl)
        ev = count_p2(t, ttc)
        if interior_only:
            ev = [e for e in ev if t[-1] - e["onset_s"] >= 1.0]
        if ev:
            scored.append((float(np.nanmin(ttc)), float(gap.min()), t, gap, vf, vl, f"{vid}-{lid}"))
    scored.sort(key=lambda x: x[0])
    return scored[:top]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["Krauss", "EIDM", "IDM"])
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--out", default="code/outputs/analysis/model_switch_trial_20261116")
    args = ap.parse_args()

    from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    pairs = collect_pairs(args.top)
    print(f"{len(pairs)} pairs with trustworthy events\n")

    results = []
    for model in args.models:
        cfg = make_cfg(outdir / f"_proto_{model}", model)
        rows = []
        for min_ttc, min_gap, t, gap, vf, vl, name in pairs:
            trace = build_trace(t, gap, vf, vl)
            if trace.empty:
                continue
            rec = {"pair": name, "model": model,
                   "real_min_ttc": round(min_ttc, 3), "real_min_gap": round(min_gap, 3)}
            try:
                res = run_joint_replay(
                    trace, sumo_cfg=cfg, lane_id="main_ext_0",
                    geometry_follower_length_m=5.0, geometry_leader_length_m=5.0,
                    follower_tau_s=1.0, follower_min_gap_m=1.0,
                    sumo_binary="sumo", seed=20261116, step_s=STEP,
                    save_trace=True, initialization_mode="safe_then_move",
                )
                rr = res.get("rows") or []
                if rr:
                    tt = np.array([r["input_time_s"] for r in rr], float)
                    gg = np.array([r["net_gap_m"] for r in rr], float)
                    ff = np.array([r["follower_speed_mps"] for r in rr], float)
                    ll = np.array([r["leader_speed_mps"] for r in rr], float)
                    st = ttc_of(gg, ff, ll)
                    rec.update({"sim_min_ttc": round(float(np.nanmin(st)), 3),
                                "sim_min_gap": round(float(np.nanmin(gg)), 3),
                                "sim_events": len(count_p2(tt, st)),
                                "status": res.get("status")})
                else:
                    rec.update({"sim_min_ttc": None, "status": res.get("status"),
                                "reason": res.get("failure_reason")})
            except Exception as exc:  # noqa: BLE001
                rec.update({"sim_min_ttc": None, "status": "ERROR",
                            "error": f"{type(exc).__name__}: {exc}"})
            rows.append(rec)
            print(f"  {model:<8} {name:<12} real={rec['real_min_ttc']:>7} sim={rec.get('sim_min_ttc')}")

        good = [r for r in rows if r.get("sim_min_ttc") is not None]
        summary = {
            "model": model,
            "n_pairs": len(rows),
            "n_ok": len(good),
            "median_sim_min_ttc": float(np.median([r["sim_min_ttc"] for r in good])) if good else None,
            "median_real_min_ttc": float(np.median([r["real_min_ttc"] for r in good])) if good else None,
            "sim_events_total": sum(r.get("sim_events") or 0 for r in good),
            "real_events_total": len(good),
        }
        results.append({**summary, "rows": rows})
        print(f"  -> {model}: 成功 {len(good)}/{len(rows)}, 仿真最小TTC中位 "
              f"{summary['median_sim_min_ttc']}, 真实 {summary['median_real_min_ttc']}, "
              f"仿真事件 {summary['sim_events_total']}\n")

    (outdir / "trial.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    print(f"{'model':<10}{'n_ok':>6}{'sim TTC中位':>12}{'real TTC中位':>13}{'sim事件':>8}")
    print("-" * 50)
    for r in results:
        print(f"{r['model']:<10}{r['n_ok']:>6}{str(r['median_sim_min_ttc']):>12}"
              f"{str(r['median_real_min_ttc']):>13}{r['sim_events_total']:>8}")
    print(f"\nwrote {outdir/'trial.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())