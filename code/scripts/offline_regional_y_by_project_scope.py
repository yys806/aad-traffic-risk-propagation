"""Offline exploratory regional risk Y using the project's OWN region/cohort definition.

EXPLORATORY / PILOT-ONLY. Simplified rho-based operator, not the formal P4 output.

Region/cohort/windows follow code/scripts/p2_task7_measurement.py (the project's own
definition, not one invented here):
    REGION  = (1600., 3080.) m
    COHORT  = columns 14..17
    PRE     = (10., 28.)
    MONITOR = (30., 46.)

Scope options:
    cohort  -> only the 4 cohort vehicles, must be inside the region
    region  -> every vehicle inside the region at that step
    all     -> every vehicle (superseded exploratory scope, kept for comparison)

rho = exp(-TTC / tau), tau = 15.364279197080283; TTC = gap / (v_self - v_leader)
when v_self > v_leader and gap > 0.
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
MONITOR = (30.0, 46.0)


def compute_run(npz_path: Path, scope: str, ws: float, we: float) -> dict:
    d = np.load(npz_path, allow_pickle=True)
    t = np.asarray(d["t"], float)
    v = np.asarray(d["v"], float)
    gap = np.asarray(d["gap"], float)
    leader = np.asarray(d["leader"]).astype(np.int64)
    x = np.asarray(d["x"], float)

    sel = (t >= ws) & (t <= we)
    t, v, gap, leader, x = t[sel], v[sel], gap[sel], leader[sel], x[sel]
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

    inside = (x >= REGION[0]) & (x < REGION[1]) & present
    cohort_cols = [j for j in COHORT if j < n_veh]
    if scope == "cohort":
        member = np.zeros((n_steps, n_veh), dtype=bool)
        if cohort_cols:
            member[:, cohort_cols] = True
        member &= inside
    elif scope == "region":
        member = inside & applicable
    else:
        member = applicable

    per_veh = []
    for j in range(n_veh):
        m = member[:, j]
        if not m.any():
            continue
        per_veh.append({"col": j, "y": float(rho[m, j].mean()), "steps": int(m.sum())})

    ys = [p["y"] for p in per_veh]
    out = {
        "run_id": npz_path.parent.name,
        "scope": scope,
        "window_s": [ws, we],
        "members": len(ys),
        "lower_Y": float(np.mean(ys)) if ys else None,
        "upper_Y": float(np.mean(ys)) if ys else None,
        "member_max_Y": float(max(ys)) if ys else None,
        "member_median_Y": float(np.median(ys)) if ys else None,
    }
    out["Y_status"] = "POINT_IDENTIFIED" if ys else "UNKNOWN_SCOPE"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--scope", default="cohort", choices=["cohort", "region", "all"])
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
                                    args.window_start, args.window_end))
        except Exception as exc:  # noqa: BLE001
            failures.append({"run_id": run_dir.name, "error": f"{type(exc).__name__}: {exc}"})
        if i % 50 == 0:
            print(f"[{i}/{len(runs)}]", flush=True)

    fields = ["run_id", "scope", "members", "lower_Y", "upper_Y", "member_max_Y",
              "member_median_Y", "Y_status"]
    with open(outdir / f"regional_y_{args.scope}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    ok = [r for r in rows if r["lower_Y"] is not None]
    vals = np.array([r["lower_Y"] for r in ok]) if ok else np.array([])
    summary = {
        "mode": "EXPLORATORY_PILOT_ONLY",
        "scope": args.scope,
        "region_m": REGION,
        "cohort_cols": COHORT,
        "window_s": [args.window_start, args.window_end],
        "tau": TAU,
        "runs_discovered": len(runs),
        "runs_with_Y": len(ok),
        "runs_without_Y": len(rows) - len(ok),
        "failures": failures,
        "Y": {"mean": float(vals.mean()) if vals.size else None,
              "sd": float(vals.std(ddof=1)) if vals.size > 1 else None,
              "min": float(vals.min()) if vals.size else None,
              "max": float(vals.max()) if vals.size else None,
              "p90": float(np.percentile(vals, 90)) if vals.size else None},
        "note": "Simplified rho operator with the project's own region/cohort. "
                "Not the formal P4 outcome; not eligible for any scientific claim.",
    }
    with open(outdir / f"summary_{args.scope}.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
