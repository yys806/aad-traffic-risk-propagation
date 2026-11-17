"""Would reproducing real near-conflicts make the effects look better?

Rather than speculate, ask the question of our own data: the existing experiment already records
every measured vehicle's TTC each step after the event. If the treatment effect lives in the
near-conflict band, then a simulation that produces more near-conflicts would show bigger
effects. If the effect lives in the bulk (large TTC), reproducing near-conflicts would mostly
add noise.

Reports:
  * how much of the risk is contributed by vehicles below various TTC thresholds
  * the treatment contrast recomputed inside and outside the near-conflict band
  * what the contrast would be if the arm distributions were shifted toward small TTC
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "code/outputs/analysis/stage1_path3_taudump_20261117"
TAU = 15.364279197080283


def load(arm: str) -> list[tuple[float, float, float]]:
    """(t, vehicle, ttc) for every measured vehicle-step after the event."""
    rows = []
    with open(OUT / f"ttc_20261116/{arm}.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((float(r["t"]), r["vehicle"], float(r["ttc_braking"])))
    return rows


def main() -> int:
    arms = {a: load(a) for a in ("opn0", "sham", "opn1")}
    print(f"vehicle-steps: " + ", ".join(f"{a}={len(v)}" for a, v in arms.items()))

    # --- how the risk mass is distributed over TTC ---
    print("\n--- share of vehicle-steps and of rho mass, by TTC band (opn0) ---")
    v = np.array([r[2] for r in arms["opn0"]])
    rho = np.exp(-v / TAU)
    bands = [(0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 5), (5, 10), (10, 1e9)]
    print(f"{'band (s)':<14}{'share of steps':>16}{'share of rho mass':>20}{'mean rho':>12}")
    for lo, hi in bands:
        m = (v >= lo) & (v < hi)
        if m.sum() == 0:
            continue
        label = f"{lo}-{hi if hi < 1e9 else 'inf'}"
        print(f"{label:<14}{m.mean()*100:>15.2f}%"
              f"{rho[m].sum()/rho.sum()*100:>19.2f}%{rho[m].mean():>12.4f}")

    print(f"\n  TTC percentiles (opn0): " + ", ".join(
        f"p{q}={np.percentile(v, q):.2f}" for q in (1, 5, 10, 25, 50, 75, 90)))
    for thr in (1.0, 2.0, 3.0):
        print(f"  steps with TTC < {thr}: "
              + ", ".join(f"{a}={100*np.mean(np.array([r[2] for r in arms[a]]) < thr):.2f}%"
                          for a in arms))

    # --- treatment contrast inside vs outside the near-conflict band ---
    print("\n--- treatment contrast by TTC band (rho means) ---")
    print(f"{'band (s)':<14}{'opn0':>10}{'sham':>10}{'opn1':>10}"
          f"{'no-content':>13}{'content':>11}")
    for lo, hi in bands:
        vals = {}
        for a in arms:
            sel = [math.exp(-r[2] / TAU) for r in arms[a] if lo <= r[2] < hi]
            vals[a] = float(np.mean(sel)) if sel else float("nan")
        nc = vals["sham"] - vals["opn0"]
        ct = vals["opn1"] - vals["sham"]
        label = f"{lo}-{hi if hi < 1e9 else 'inf'}"
        print(f"{label:<14}{vals['opn0']:>10.4f}"
              f"{vals['sham']:>10.4f}{vals['opn1']:>10.4f}{nc:>+13.4f}{ct:>+11.4f}")

    # --- what a shift toward small TTC would do to the absolute effect ---
    print("\n--- sensitivity of the absolute effect to where the mass sits ---")
    print("  For fixed change dTTC, d(rho) = -rho * dTTC / tau, so the absolute effect scales")
    print("  with the level of rho. Moving mass from TTC=5 s to TTC=1 s raises rho from:")
    for ttc in (10.0, 5.0, 3.0, 2.0, 1.0, 0.5):
        r = math.exp(-ttc / TAU)
        print(f"    TTC={ttc:>4.1f}s -> rho={r:.4f}"
              f"   absolute effect for dTTC=0.06s = {-r*0.06/TAU:+.6f}")
    print("\n  Relative effect is d(rho)/rho = -dTTC/tau, which does NOT depend on the level,")
    print("  so reproducing near-conflicts cannot improve any relative effect at all.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())