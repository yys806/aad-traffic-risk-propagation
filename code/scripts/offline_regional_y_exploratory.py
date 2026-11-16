"""Offline exploratory regional risk Y from existing B-source SUMO runs (P2 Task8).

EXPLORATORY / PILOT-ONLY.

This is NOT the formal P4 operator output. Region, window and roster are provisional
(see docs/plans/2026-11-16-offline-regional-y.md). It exists to answer one question:
can a regional risk value be produced from data we already have, and how wide is it.

Definitions used here:
  rho        = exp(-TTC / tau), tau = 15.364279197080283  (Approved 2026-10-12)
  TTC        = gap / (v_self - v_leader), only when v_self > v_leader and gap > 0
  no leader                 -> not applicable (excluded, counted separately)
  leader present, no closing-> rho = 0 (point identified)
  missing/invalid inputs    -> [0, 1] interval (never imputed)
  vehicle window value      -> mean of rho over applicable steps in window
  regional Y                -> equal-vehicle mean over vehicles in the roster

Usage:
  python code/scripts/offline_regional_y_exploratory.py --raw <dir> --output <dir>
  python code/scripts/offline_regional_y_exploratory.py --npz <one.npz>
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

TAU = 15.364279197080283
WINDOW_START_S = 5.0
WINDOW_END_S = 45.0


def compute_run(npz_path: Path, window_start_s: float, window_end_s: float) -> dict:
    d = np.load(npz_path, allow_pickle=True)
    t = np.asarray(d["t"], dtype=float)
    v = np.asarray(d["v"], dtype=float)
    gap = np.asarray(d["gap"], dtype=float)
    leader = np.asarray(d["leader"]).astype(np.int64)

    sel = (t >= window_start_s) & (t <= window_end_s)
    t_sel = t[sel]
    v, gap, leader = v[sel], gap[sel], leader[sel]
    n_steps, n_veh = v.shape

    has_leader = leader >= 0
    safe_idx = np.where(has_leader, leader, 0)
    v_leader = np.take_along_axis(v, safe_idx, axis=1)
    # vehicles absent at this step (never inserted / already gone) show v <= 0
    present = v > 0

    lower = np.zeros((n_steps, n_veh))
    upper = np.zeros((n_steps, n_veh))
    applicable = has_leader & present
    invalid = np.zeros((n_steps, n_veh), dtype=bool)

    closing = np.where(applicable, v - np.where(has_leader, v_leader, np.nan), np.nan)
    gap_ok = np.isfinite(gap) & (gap > 0)
    valid_closing = applicable & gap_ok & np.isfinite(closing)
    approaching = valid_closing & (closing > 0)

    ttc = np.full((n_steps, n_veh), np.nan)
    ttc[approaching] = gap[approaching] / closing[approaching]
    rho = np.exp(-ttc / TAU)

    lower[approaching] = rho[approaching]
    upper[approaching] = rho[approaching]
    # leader present but not closing: rho = 0, point identified
    lower[valid_closing & ~approaching] = 0.0
    upper[valid_closing & ~approaching] = 0.0
    # leader present but inputs invalid: uninformative interval
    invalid = applicable & ~valid_closing
    lower[invalid] = 0.0
    upper[invalid] = 1.0

    vehicle_rows = []
    lower_means, upper_means = [], []
    for j in range(n_veh):
        mask = applicable[:, j]
        if not mask.any():
            vehicle_rows.append({"vehicle_col": j, "applicable_steps": 0, "invalid_steps": 0,
                                 "lower_mean": None, "upper_mean": None, "status": "NOT_APPLICABLE"})
            continue
        lo = float(lower[mask, j].mean())
        hi = float(upper[mask, j].mean())
        inv = int(invalid[mask, j].sum())
        vehicle_rows.append({"vehicle_col": j, "applicable_steps": int(mask.sum()), "invalid_steps": inv,
                             "lower_mean": lo, "upper_mean": hi,
                             "status": "INTERVAL_IDENTIFIED" if hi > lo else "POINT_IDENTIFIED"})
        lower_means.append(lo)
        upper_means.append(hi)

    out = {
        "run_id": npz_path.parent.name,
        "npz": str(npz_path),
        "window_s": [window_start_s, window_end_s],
        "steps_in_window": int(n_steps),
        "vehicles_total": int(n_veh),
        "vehicles_with_leader": int(sum(1 for r in vehicle_rows if r["applicable_steps"] > 0)),
        "applicable_step_fraction": float(applicable.mean()),
        "invalid_step_fraction_of_applicable": (
            float(invalid.sum() / applicable.sum()) if applicable.sum() else None
        ),
        "roster_N": len(lower_means),
        "lower_Y": float(np.mean(lower_means)) if lower_means else None,
        "upper_Y": float(np.mean(upper_means)) if upper_means else None,
    }
    if out["lower_Y"] is not None:
        out["Y_width"] = out["upper_Y"] - out["lower_Y"]
        out["Y_status"] = "INTERVAL_IDENTIFIED" if out["Y_width"] > 0 else "POINT_IDENTIFIED"
    else:
        out["Y_width"] = None
        out["Y_status"] = "UNKNOWN_SCOPE"
    out["_vehicles"] = vehicle_rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", help="directory containing <run_id>/trajectory.npz")
    ap.add_argument("--npz", help="single trajectory.npz")
    ap.add_argument("--output", help="output directory")
    ap.add_argument("--window-start", type=float, default=WINDOW_START_S)
    ap.add_argument("--window-end", type=float, default=WINDOW_END_S)
    args = ap.parse_args()

    if args.npz:
        res = compute_run(Path(args.npz), args.window_start, args.window_end)
        res.pop("_vehicles", None)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if not args.raw or not args.output:
        ap.error("--raw and --output are required for batch mode")

    raw = Path(args.raw)
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    runs = sorted(p.parent for p in raw.glob("*/trajectory.npz"))
    rows, failures = [], []
    for i, run_dir in enumerate(runs, 1):
        try:
            res = compute_run(run_dir / "trajectory.npz", args.window_start, args.window_end)
            res.pop("_vehicles", None)
            rows.append(res)
        except Exception as exc:  # noqa: BLE001 - failures must be listed, never dropped
            failures.append({"run_id": run_dir.name, "error": f"{type(exc).__name__}: {exc}"})
        if i % 20 == 0:
            print(f"[{i}/{len(runs)}] processed", flush=True)

    fields = ["run_id", "roster_N", "lower_Y", "upper_Y", "Y_width", "Y_status",
              "applicable_step_fraction", "invalid_step_fraction_of_applicable",
              "vehicles_with_leader", "vehicles_total", "steps_in_window"]
    with open(outdir / "regional_y_by_run.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    vals_lo = [r["lower_Y"] for r in rows if r["lower_Y"] is not None]
    vals_hi = [r["upper_Y"] for r in rows if r["upper_Y"] is not None]
    summary = {
        "mode": "EXPLORATORY_PILOT_ONLY",
        "window_s": [args.window_start, args.window_end],
        "tau": TAU,
        "runs_discovered": len(runs),
        "runs_completed": len(rows),
        "runs_failed": len(failures),
        "failures": failures,
        "lower_Y": {"mean": float(np.mean(vals_lo)) if vals_lo else None,
                    "sd": float(np.std(vals_lo, ddof=1)) if len(vals_lo) > 1 else None,
                    "min": float(np.min(vals_lo)) if vals_lo else None,
                    "max": float(np.max(vals_lo)) if vals_lo else None},
        "upper_Y": {"mean": float(np.mean(vals_hi)) if vals_hi else None,
                    "sd": float(np.std(vals_hi, ddof=1)) if len(vals_hi) > 1 else None,
                    "min": float(np.min(vals_hi)) if vals_hi else None,
                    "max": float(np.max(vals_hi)) if vals_hi else None},
        "note": "Provisional region/window/roster. Not the formal P4 outcome. "
                "Not eligible for any scientific claim.",
    }
    with open(outdir / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
