"""Calibrate EIDM's human-driver parameters to reproduce real near-conflict TTCs.

Background: Krauss/EIDM/IDM at default settings never enter the near-conflict states observed
in real trajectories (real min-TTC median 0.26 s vs simulated 5-10 s). The literature
(Bevrani & Chung 2012; Friedrich et al. 2022) confirms this is structural — car-following
models are crash-free by construction — and that the fix is to relax the safety constraint
and use the model's own behavioural error parameters, not to swap models.

EIDM exposes exactly those knobs. All twelve were verified to take effect as vType XML
attributes (`code/scripts/eidm_attr_probe.py`), which is the only reliable check because
SUMO ignores unknown keys silently.

This script sweeps parameter sets on the same real leader trajectories and reports how close
the simulated follower gets to the real follower's minimum TTC.

Usage:
  python code/scripts/eidm_calibration_sweep.py --top 6
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

from screen_mitra_risk_pairs import load_member, pair_series  # noqa: E402
from compare_real_vs_sim_follower import build_trace, ttc_of, count_p2, STEP  # noqa: E402

STAGING = ROOT / "local_research/staging/task16_20261031"

# Each set gives EIDM attributes as vType XML attributes (verified to take effect).
# Defaults in SUMO 1.26: sigmagap=0.1 sigmaleader=0.02 sigmaerror=0.04 treaction=0.5
# tPersEstimate=10 tPersDrive=3 tpreview=4 ccoolness=0.99 jerkmax=3 taccmax=1.2
# Mflatness=2 Mbegin=0.7
PARAM_SETS = {
    "default": {},
    "salles2020": {"sigmagap": "0.1", "sigmaleader": "0.02", "sigmaerror": "0.1",
                   "ccoolness": "0.99", "taccmax": "1.2", "Mflatness": "2.0",
                   "Mbegin": "0.7", "tpreview": "4", "tPersEstimate": "10",
                   "tPersDrive": "3", "jerkmax": "3"},
    "perception_mid": {"sigmaerror": "0.35", "sigmagap": "0.35", "sigmaleader": "0.20",
                       "treaction": "1.2", "tPersEstimate": "5"},
    "perception_high": {"sigmaerror": "0.60", "sigmagap": "0.60", "sigmaleader": "0.40",
                        "treaction": "1.8", "tPersEstimate": "3", "tPersDrive": "1.5"},
    "aggressive": {"sigmaerror": "0.90", "sigmagap": "0.90", "sigmaleader": "0.70",
                   "treaction": "2.5", "tPersEstimate": "1.5", "tPersDrive": "1.0",
                   "tau": "0.7", "minGap": "0.5"},
    "realtime_lag": {"sigmaerror": "0.60", "sigmagap": "0.60", "sigmaleader": "0.40",
                     "treaction": "2.0", "tPersEstimate": "1.0", "tPersDrive": "8",
                     "tpreview": "1.0", "ccoolness": "0.5", "epsilonacc": "3.0"},
}


def make_cfg(workdir: Path, attrs: dict[str, str]) -> Path:
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    shutil.copy2(STAGING / "network.net.xml", workdir / "network.net.xml")
    base = {"carFollowModel": "EIDM", "accel": "2.6", "decel": "4.5", "tau": "1.0",
            "length": "5.0", "minGap": "1.0", "maxSpeed": "30"}
    base.update(attrs)
    attrs_s = " ".join(f'{k}="{v}"' for k, v in base.items())
    routes = f"""<routes>
  <vType id="leader" {attrs_s}/>
  <vType id="follower" {attrs_s}/>
  <route id="r0" edges="main_ext"/>
</routes>"""
    (workdir / "joint_routes.rou.xml").write_text(routes, encoding="utf-8")
    cfg = (workdir / "joint.sumocfg")
    cfg.write_text(f"""<configuration>
    <input><net-file value="network.net.xml"/><route-files value="joint_routes.rou.xml"/></input>
    <time><begin value="0"/><end value="120"/><step-length value="0.05"/></time>
    <processing><time-to-teleport value="-1"/><collision.action value="warn"/><no-step-log value="true"/></processing>
</configuration>""", encoding="utf-8")
    return cfg


def collect_pairs(top: int):
    veh = load_member("T1_D1.csv")
    out = []
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
        ev = [e for e in count_p2(t, ttc) if t[-1] - e["onset_s"] >= 1.0]
        if ev:
            out.append((float(np.nanmin(ttc)), t, gap, vf, vl, f"{vid}-{lid}"))
    out.sort(key=lambda x: x[0])
    return out[:top]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--out", default="code/outputs/analysis/eidm_calibration_20261116")
    args = ap.parse_args()

    from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    pairs = collect_pairs(args.top)
    print(f"{len(pairs)} pairs, real min-TTC median "
          f"{np.median([p[0] for p in pairs]):.3f}\n")

    results = []
    for name, attrs in PARAM_SETS.items():
        cfg = make_cfg(outdir / f"_p_{name}", attrs)
        rows = []
        for real_ttc, t, gap, vf, vl, label in pairs:
            trace = build_trace(t, gap, vf, vl)
            if trace.empty:
                continue
            rec = {"pair": label, "real_min_ttc": round(real_ttc, 3)}
            try:
                res = run_joint_replay(
                    trace, sumo_cfg=cfg, lane_id="main_ext_0",
                    geometry_follower_length_m=5.0, geometry_leader_length_m=5.0,
                    follower_tau_s=float(attrs.get("tau", 1.0)),
                    follower_min_gap_m=float(attrs.get("minGap", 1.0)),
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
                                "sim_events": len(count_p2(tt, st))})
                else:
                    rec.update({"sim_min_ttc": None,
                                "reason": res.get("failure_reason")})
            except Exception as exc:  # noqa: BLE001
                rec.update({"sim_min_ttc": None, "error": f"{type(exc).__name__}: {exc}"})
            rows.append(rec)

        good = [r for r in rows if r.get("sim_min_ttc") is not None]
        med_sim = float(np.median([r["sim_min_ttc"] for r in good])) if good else None
        med_real = float(np.median([r["real_min_ttc"] for r in good])) if good else None
        summary = {"param_set": name, "attrs": attrs, "n_ok": len(good), "n_total": len(rows),
                   "median_sim_min_ttc": med_sim, "median_real_min_ttc": med_real,
                   "ratio": (med_sim / med_real) if (med_sim and med_real) else None,
                   "sim_events_total": sum(r.get("sim_events") or 0 for r in good),
                   "rows": rows}
        results.append(summary)
        print(f"{name:<16} 成功{len(good)}/{len(rows)}  仿真TTC中位 {med_sim}  "
              f"真实 {med_real}  比值 {summary['ratio']}  事件 {summary['sim_events_total']}")

    (outdir / "sweep.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    print(f"\n{'param set':<16}{'sim中位':>10}{'real中位':>10}{'比值':>8}{'事件':>6}")
    print("-" * 50)
    for r in results:
        print(f"{r['param_set']:<16}{str(r['median_sim_min_ttc']):>10}"
              f"{str(r['median_real_min_ttc']):>10}"
              f"{(round(r['ratio'],2) if r['ratio'] else '-'):>8}{r['sim_events_total']:>6}")
    print(f"\nwrote {outdir/'sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())