"""Offline exploratory regional Y with a roster LOCKED before treatment.

Why this exists: the dynamic-region scope counts whoever happens to be inside the
region at each step, which lets the treatment change the denominator (post-treatment
selection). P4 requires a pre-assignment roster. This script locks the member list at
`--lock-time` and never re-selects afterwards.

EXPLORATORY / PILOT-ONLY. Simplified rho operator; not the formal P4 output.

Project definitions reused (code/scripts/p2_task7_measurement.py):
    REGION  = (1600., 3080.) m
    PRE     = (10., 28.)      -> lock time defaults to the end of PRE
    MONITOR = (30., 46.)

Scopes:
    locked_region : vehicles inside REGION at lock_time, used for every later step
    locked_cohort : the fixed cohort columns inside REGION at lock_time
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

TAU = 15.364279197080283
REGION = (1600.0, 3080.0)
COHORT = tuple(range(14, 18))
PRE_END = 28.0
MONITOR = (30.0, 46.0)


def compute_run(npz_path: Path, scope: str, lock_time: float, ws: float, we: float) -> dict:
    d = np.load(npz_path, allow_pickle=True)
    t = np.asarray(d["t"], float)
    v = np.asarray(d["v"], float)
    gap = np.asarray(d["gap"], float)
    leader = np.asarray(d["leader"]).astype(np.int64)
    x = np.asarray(d["x"], float)

    # --- roster locked before treatment ---
    lock_idx = int(np.argmin(np.abs(t - lock_time)))
    x_lock, v_lock = x[lock_idx], v[lock_idx]
    inside_lock = (x_lock >= REGION[0]) & (x_lock < REGION[1]) & (v_lock > 0)
    if scope == "locked_cohort":
        roster = np.zeros_like(inside_lock, dtype=bool)
        for j in COHORT:
            if j < roster.size:
                roster[j] = True
        roster &= inside_lock
    else:
        roster = inside_lock

    if not roster.any():
        return {"run_id": npz_path.parent.name, "scope": scope, "locked_N": 0,
                "lower_Y": None, "upper_Y": None, "member_max_Y": None,
                "member_median_Y": None, "Y_status": "EMPTY_ROSTER"}

    # --- measurement window ---
    sel = (t >= ws) & (t <= we)
    v, gap, leader = v[sel], gap[sel], leader[sel]
    n_steps, n_veh = v.shape

    has_leader = leader >= 0
    safe_idx = np.where(has_leader, leader, 0)
    v_leader = np.take_along_axis(v, safe_idx, axis=1)
    present = v > 0
    applicable = has_leader & present

    closing = np.where(applicable, v - np.where(has_leader, v_leader, np.nan), np.nan)
    gap_ok = np.isfinite(gap) & (gap > 0)
    valid = applicable & gap_ok & np.isfinite(closing)
    approaching = valid & (closing > 0)

    rho = np.zeros((n_steps, n_veh))
    if approaching.any():
        rho[approaching] = np.exp(-(gap[approaching] / closing[approaching]) / TAU)

    per_veh = []
    for j in np.nonzero(roster)[0]:
        m = applicable[:, j]
        if m.any():
            per_veh.append(float(rho[m, j].mean()))

    if not per_veh:
        return {"run_id": npz_path.parent.name, "scope": scope, "locked_N": int(roster.sum()),
                "lower_Y": None, "upper_Y": None, "member_max_Y": None,
                "member_median_Y": None, "Y_status": "NO_APPLICABLE_STEPS"}

    ys = np.array(per_veh)
    return {
        "run_id": npz_path.parent.name, "scope": scope,
        "locked_N": int(roster.sum()), "measured_members": int(ys.size),
        "lower_Y": float(ys.mean()), "upper_Y": float(ys.mean()),
        "member_max_Y": float(ys.max()), "member_median_Y": float(np.median(ys)),
        "Y_status": "POINT_IDENTIFIED",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--scope", default="locked_region", choices=["locked_region", "locked_cohort"])
    ap.add_argument("--lock-time", type=float, default=PRE_END)
    ap.add_argument("--window-start", type=float, default=MONITOR[0])
    ap.add_argument("--window-end", type=float, default=MONITOR[1])
    args = ap.parse_args()

    raw, outdir = Path(args.raw), Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    runs = sorted(p.parent for p in raw.glob("*/trajectory.npz"))

    rows, failures = [], []
    for i, run_dir in enumerate(runs, 1):
        try:
            rows.append(compute_run(run_dir / "trajectory.npz", args.scope,
                                    args.lock_time, args.window_start, args.window_end))
        except Exception as exc:  # noqa: BLE001
            failures.append({"run_id": run_dir.name, "error": f"{type(exc).__name__}: {exc}"})
        if i % 50 == 0:
            print(f"[{i}/{len(runs)}]", flush=True)

    fields = ["run_id", "scope", "locked_N", "measured_members", "lower_Y", "upper_Y",
              "member_max_Y", "member_median_Y", "Y_status"]
    with open(outdir / f"regional_y_{args.scope}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    ok = [r for r in rows if r["lower_Y"] is not None]
    vals = np.array([r["lower_Y"] for r in ok]) if ok else np.array([])
    ns = np.array([r["locked_N"] for r in ok]) if ok else np.array([])
    summary = {
        "mode": "EXPLORATORY_PILOT_ONLY", "scope": args.scope,
        "region_m": REGION, "lock_time_s": args.lock_time, "window_s": [args.window_start, args.window_end],
        "tau": TAU, "runs_discovered": len(runs), "runs_with_Y": len(ok),
        "runs_without_Y": len(rows) - len(ok), "failures": failures,
        "locked_N": {"mean": float(ns.mean()) if ns.size else None,
                     "min": int(ns.min()) if ns.size else None,
                     "max": int(ns.max()) if ns.size else None},
        "Y": {"mean": float(vals.mean()) if vals.size else None,
              "sd": float(vals.std(ddof=1)) if vals.size > 1 else None,
              "min": float(vals.min()) if vals.size else None,
              "max": float(vals.max()) if vals.size else None},
        "note": "Roster locked at lock_time, never re-selected. Simplified rho operator. "
                "Not the formal P4 outcome; not eligible for any scientific claim.",
    }
    with open(outdir / f"summary_{args.scope}.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
