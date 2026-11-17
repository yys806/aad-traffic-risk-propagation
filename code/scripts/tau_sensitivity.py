"""Recompute the regional risk at any tau from the dumped raw TTC values.

Why this works: tau enters only the risk readout rho = exp(-TTC/tau); it never touches the
simulation. So one run of each arm is enough to evaluate every tau, and the three arms are
compared on identical trajectories.

Also checks a property that matters for how tau may be argued in the paper: AUC is invariant
under monotone transforms, so every tau gives exactly the same discrimination. tau can
therefore be defended as a scale choice but never as an accident-risk optimum.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "code/outputs/analysis/stage1_path3_taudump_20261117"
TAU0 = 15.364279197080283
TAUS = [("5", 5.0), ("tau/2", TAU0 / 2), ("tau", TAU0), ("2*tau", 2 * TAU0), ("30", 30.0)]


def load(arm: str) -> dict[float, list[float]]:
    """Return step time -> TTC values for every measured vehicle at that step."""
    steps: dict[float, list[float]] = defaultdict(list)
    with open(OUT / f"ttc_20261116/{arm}.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            steps[round(float(row["t"]), 2)].append(float(row["ttc_braking"]))
    return steps


def regional_risk(steps: dict[float, list[float]], tau: float) -> tuple[float, int]:
    per_step = [float(np.mean([math.exp(-x / tau) for x in v])) for v in steps.values() if v]
    return float(np.mean(per_step)), len(per_step)


def main() -> int:
    arms = {a: load(a) for a in ("opn0", "sham", "opn1")}
    ref = json.loads((OUT / "path3_summary.json").read_text(encoding="utf-8"))
    print(f"steps per arm: " + ", ".join(f"{a}={len(v)}" for a, v in arms.items()))

    print(f"\n{'tau':<8}{'label':>8}{'opn0':>12}{'sham':>12}{'opn1':>12}"
          f"{'Δ(no-content)':>16}{'Δ(content)':>14}{'content %':>11}")
    print("-" * 95)
    table = {}
    for label, tau in TAUS:
        r = {a: regional_risk(arms[a], tau)[0] for a in arms}
        nc = r["sham"] - r["opn0"]
        ct = r["opn1"] - r["sham"]
        pct = 100.0 * ct / r["sham"]
        print(f"{label:<8}{tau:>8.2f}{r['opn0']:>12.6f}{r['sham']:>12.6f}{r['opn1']:>12.6f}"
              f"{nc:>+16.6f}{ct:>+14.6f}{pct:>+10.2f}%")
        table[label] = dict(tau=tau, opn0=r["opn0"], sham=r["sham"], opn1=r["opn1"],
                            no_content=nc, content=ct, content_pct=pct)

    # reproduction check against the recorded run
    print("\n--- reproduction check at tau = 15.364 ---")
    seed_key = next(iter(ref["arms"]))
    rec = {a: ref["arms"][seed_key][a]["risk_meantime"] for a in ("opn0", "sham", "opn1")}
    for a in ("opn0", "sham", "opn1"):
        got = table["tau"][a]
        print(f"  {a}: recomputed {got:.6f}  recorded {rec[a]:.6f}  diff {got-rec[a]:+.2e}")

    # The property that decides how tau may be argued in the paper. AUC is computed from
    # ranks, and rho = exp(-TTC/tau) is a strictly monotone transform of TTC for any tau > 0,
    # so every tau must give bit-identical discrimination. Demonstrated on real pairs rather
    # than asserted.
    print("\n--- tau cannot change discrimination (AUC is rank-based) ---")
    vpath = ROOT / "code/outputs/analysis/risk_measure_validation_20261117/validation.json"
    if vpath.exists():
        vd = json.loads(vpath.read_text(encoding="utf-8"))
        pairs = vd["pairs"]
        pos = [p for p in pairs if p["max_decel"] > 3.0 and p["interior"]]
        neg = [p for p in pairs if p["max_decel"] <= 3.0 and p["interior"]]
        print(f"  pairs: {len(pos)} hard-braking vs {len(neg)} ordinary")

        def auc_rank(pv: np.ndarray, nv: np.ndarray) -> float:
            allv = np.concatenate([pv, nv])
            order = allv.argsort(kind="mergesort")
            ranks = np.empty(len(allv), float)
            ranks[order] = np.arange(1, len(allv) + 1)
            _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
            sr = np.zeros(len(cnt))
            np.add.at(sr, inv, ranks)
            ranks = (sr / cnt)[inv]
            return float((ranks[:len(pv)].sum() - len(pv) * (len(pv) + 1) / 2) / (len(pv) * len(nv)))

        identical = []
        for label, tau in TAUS:
            pr = np.array([math.exp(-p["min_ttc_brake"] / tau) for p in pos])
            ng = np.array([math.exp(-p["min_ttc_brake"] / tau) for p in neg])
            a = auc_rank(pr, ng)
            identical.append(a)
            print(f"  tau={label:<6} AUC(rho vs hard braking) = {a:.10f}")
        print(f"  max spread across tau = {max(identical)-min(identical):.2e}"
              f"  -> identical, exactly as rank invariance requires")
        print("  consequence: tau cannot be justified or invalidated by discrimination;")
        print("               it is a display scale, and any claim that it is an accident-risk")
        print("               optimum needs evidence that does not exist in this project.")
    else:
        print("  validation.json missing - run validate_risk_measure.py first")

    # how much of the small effect is just tau compressing the scale
    print("\n--- effect size vs tau (relative change is what the paper would report) ---")
    for label, d in table.items():
        print(f"  tau={label:<6} no-content {d['no_content']:+.6f} ({d['no_content']/d['opn0']*100:+.3f}%)"
              f"   content {d['content']:+.6f} ({d['content_pct']:+.3f}%)")

    (OUT / "tau_sensitivity.json").write_text(
        json.dumps(table, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT/'tau_sensitivity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())