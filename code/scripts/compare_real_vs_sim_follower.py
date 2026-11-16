"""Compare a REAL follower against a SUMO-native follower, driven by the same real leader.

Purpose: answer the question that decides the whole experimental route —
is the missing risk-event rate caused by the *follower model*, or by the *leader input*?

Existing Task16 replays cannot answer this: their three candidate pairs contain zero
Formal P2 events (see docs/EXPERIMENT_driverstate_scan_20261116.md §19), because they were
selected by longest-following-duration rather than by risk.

Method: take real pairs that DO contain P2 events (from `screen_mitra_risk_pairs.py`),
replay the real leader through the existing `run_joint_replay` adapter, let the SUMO-native
Krauss follower drive itself, then compute Formal P2 on both the real follower and the
simulated follower over the same time window.

Formal P2 (unchanged): TTC < 2.0 s, span >= 0.2 s, sample spacing <= 0.11 s.

Usage:
  python code/scripts/compare_real_vs_sim_follower.py --top 8
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

from screen_mitra_risk_pairs import load_member, pair_series  # noqa: E402

TTC_THRESH = 2.0
PERSIST = 0.2
MAX_GAP = 0.11
STEP = 0.05

STAGING = ROOT / "local_research/staging/task16_20261031"
SUMO_CFG = STAGING / "joint.sumocfg"
LANE_CANDIDATES = ("main_ext_0", "main_ext_1", "main_ext_2")


def count_p2(t: np.ndarray, ttc: np.ndarray) -> list[dict]:
    below = np.flatnonzero(np.isfinite(ttc) & (ttc < TTC_THRESH))
    if below.size < 2:
        return []
    breaks = np.flatnonzero(np.diff(t[below]) > MAX_GAP + 1e-12)
    out = []
    for g in np.split(below, breaks + 1):
        if g.size < 2:
            continue
        span = float(t[g[-1]] - t[g[0]])
        if span >= PERSIST - 1e-12:
            out.append({"onset_s": round(float(t[g[0]]), 3),
                        "span_s": round(span, 3),
                        "min_ttc_s": round(float(np.nanmin(ttc[g])), 3)})
    return out


def ttc_of(gap: np.ndarray, vf: np.ndarray, vl: np.ndarray) -> np.ndarray:
    closing = vf - vl
    ttc = np.full_like(gap, np.inf, dtype=float)
    m = closing > 1e-6
    ttc[m] = gap[m] / closing[m]
    return ttc


def build_trace(t: np.ndarray, gap: np.ndarray, vf: np.ndarray, vl: np.ndarray) -> pd.DataFrame:
    """Uniform 0.05 s grid; leader position from integrated leader speed."""
    grid = np.arange(t[0], t[-1] + 1e-9, STEP)
    if grid.size < 10:
        return pd.DataFrame()
    g_gap = np.interp(grid, t, gap)
    g_vf = np.interp(grid, t, vf)
    g_vl = np.interp(grid, t, vl)
    # leader arc-length position, integrated from the leader's own speed
    dist = np.concatenate([[0.0], np.cumsum((g_vl[1:] + g_vl[:-1]) / 2.0 * STEP)])
    return pd.DataFrame({
        "relative_time_s": grid,
        "leader_y_m": dist,
        "leader_speed_mps": g_vl,
        "follower_speed_mps": g_vf,
        "net_gap_m": g_gap,
    })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", default="T1_D1.csv")
    ap.add_argument("--top", type=int, default=8, help="how many risky pairs to replay")
    ap.add_argument("--tau", type=float, default=1.0)
    ap.add_argument("--min-gap", type=float, default=2.5)
    ap.add_argument("--out", default="code/outputs/analysis/real_vs_sim_follower_20261116")
    ap.add_argument("--interior-only", action="store_true",
                    help="keep only events whose onset is >=1 s before the track ends "
                         "(MiTra tracks are short and truncated, so an event right at the "
                         "end is a boundary artifact, not an observed conflict)")
    args = ap.parse_args()

    from riskprop.stage_0_5_fixed_leader_follower_traci import run_joint_replay

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    veh = load_member(args.member)
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
        if args.interior_only:
            ev = [e for e in ev if t[-1] - e["onset_s"] >= 1.0]
        if ev:
            scored.append((len(ev), float(np.nanmin(ttc)), vid, lid, t, gap, vf, vl, ev))

    scored.sort(key=lambda x: (-x[0], x[1]))
    print(f"risky pairs available: {len(scored)}, replaying top {args.top}")

    results = []
    for n, min_ttc, vid, lid, t, gap, vf, vl, real_ev in scored[: args.top]:
        trace = build_trace(t, gap, vf, vl)
        if trace.empty:
            continue
        rec = {"pair": f"{vid}-{lid}", "real_events": len(real_ev),
               "real_min_ttc": round(min_ttc, 3),
               "real_min_gap": round(float(gap.min()), 3),
               "duration_s": round(float(t[-1] - t[0]), 2)}
        try:
            res = run_joint_replay(
                trace,
                sumo_cfg=SUMO_CFG,
                lane_id=LANE_CANDIDATES[0],
                geometry_follower_length_m=5.0,
                geometry_leader_length_m=5.0,
                follower_tau_s=args.tau,
                follower_min_gap_m=args.min_gap,
                sumo_binary="sumo",
                seed=20261116,
                step_s=STEP,
                save_trace=True,
                initialization_mode="safe_then_move",
            )
            rows = res.get("rows") or []
            if rows:
                tt = np.array([r["input_time_s"] for r in rows], dtype=float)
                gg = np.array([r["net_gap_m"] for r in rows], dtype=float)
                ff = np.array([r["follower_speed_mps"] for r in rows], dtype=float)
                ll = np.array([r["leader_speed_mps"] for r in rows], dtype=float)
                sim_ttc = ttc_of(gg, ff, ll)
                sim_ev = count_p2(tt, sim_ttc)
                rec.update({"sim_status": res.get("status"),
                            "sim_events": len(sim_ev),
                            "sim_min_ttc": round(float(np.nanmin(sim_ttc)), 3)
                            if np.isfinite(sim_ttc).any() else None,
                            "sim_min_gap": round(float(np.nanmin(gg)), 3),
                            "sim_events_detail": sim_ev[:3]})
            else:
                rec.update({"sim_status": res.get("status"),
                            "sim_events": None,
                            "note": "no rows returned"})
        except Exception as exc:  # noqa: BLE001 - report, never swallow
            rec.update({"sim_status": "ERROR", "error": f"{type(exc).__name__}: {exc}"})
        results.append(rec)
        print(f"{rec['pair']:<14} real={rec.get('real_events')} "
              f"sim={rec.get('sim_events')} status={rec.get('sim_status')}")

    (outdir / "compare.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {outdir/'compare.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())