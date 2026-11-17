"""Does the risk measure add anything beyond the gap it is computed from?

The sharpest objection from review was that the measure is a monotone function of the gap, so
"risk went down" may only mean "cars got farther apart". If that is true, reporting risk changes
is close to tautological.

Test: stratify pairs by minimum gap (deciles) and compute discrimination WITHIN each stratum.
If TTC still separates hard-braking from ordinary pairs among pairs that had the same gap, the
measure carries information the gap does not. If discrimination collapses to chance inside the
strata, the gap explains it and the measure adds nothing.

This is a nonparametric control for confounding: no model form is assumed, and no linearity is
imposed on a relationship that is known to be nonlinear.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
VJSON = ROOT / "code/outputs/analysis/risk_measure_validation_20261117/validation.json"


def auc_rank(pv: np.ndarray, nv: np.ndarray) -> float:
    if len(pv) == 0 or len(nv) == 0:
        return float("nan")
    allv = np.concatenate([pv, nv])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv), float)
    ranks[order] = np.arange(1, len(allv) + 1)
    _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    sr = np.zeros(len(cnt))
    np.add.at(sr, inv, ranks)
    ranks = (sr / cnt)[inv]
    return float((ranks[:len(pv)].sum() - len(pv) * (len(pv) + 1) / 2) / (len(pv) * len(nv)))


def main() -> int:
    d = json.loads(VJSON.read_text(encoding="utf-8"))
    pairs = [p for p in d["pairs"] if p.get("interior")]
    if len(pairs) < 50:
        pairs = d["pairs"]
    print(f"pairs used: {len(pairs)}")

    # orientation: lower TTC = more dangerous, so negate for AUC
    ttc = np.array([-p["min_ttc_brake"] for p in pairs])
    gap = np.array([p["min_gap"] for p in pairs])
    lab = np.array([1 if p["max_decel"] > 3.0 else 0 for p in pairs])
    print(f"positives (hard braking > 3 m/s2): {int(lab.sum())} / {len(lab)}")

    overall = auc_rank(ttc[lab == 1], ttc[lab == 0])
    gap_only = auc_rank(-gap[lab == 1], -gap[lab == 0])
    print(f"\nunconditional AUC   TTC(neg) = {overall:.3f}   gap(neg) = {gap_only:.3f}")

    print("\n--- within gap deciles: does TTC still discriminate? ---")
    qs = np.percentile(gap, np.arange(0, 101, 10))
    rows = []
    for i in range(10):
        lo, hi = qs[i], qs[i + 1]
        sel = (gap >= lo) & (gap <= hi) if i == 9 else (gap >= lo) & (gap < hi)
        if sel.sum() < 20:
            continue
        l, t = lab[sel], ttc[sel]
        if l.sum() < 2 or (1 - l).sum() < 2:
            print(f"  decile {i+1}: gap {lo:5.2f}-{hi:5.2f} m  n={sel.sum():4d}  "
                  f"pos={int(l.sum()):3d}  too few positives, skipped")
            continue
        a = auc_rank(t[l == 1], t[l == 0])
        rows.append((lo, hi, int(sel.sum()), int(l.sum()), a))
        print(f"  decile {i+1}: gap {lo:5.2f}-{hi:5.2f} m  n={sel.sum():4d}  "
              f"pos={int(l.sum()):3d}  AUC = {a:.3f}")

    if rows:
        w = np.array([r[2] for r in rows], float)
        a = np.array([r[4] for r in rows], float)
        ok = np.isfinite(a)
        pooled = float(np.sum(a[ok] * w[ok]) / np.sum(w[ok]))
        print(f"\n  gap-stratified pooled AUC = {pooled:.3f}  (vs {overall:.3f} unconditional)")
        if pooled >= overall - 0.05:
            verdict = ("measurement carries information the gap does not: discrimination "
                       "survives holding the gap fixed")
        elif pooled >= 0.55:
            verdict = ("measurement keeps a weak signal beyond the gap, but most of the "
                       "apparent discrimination was the gap")
        else:
            verdict = ("after holding the gap fixed the measure is at chance: it is a "
                       "re-expression of the gap, not an independent risk signal")
        print(f"  verdict: {verdict}")

        out = ROOT / "code/outputs/analysis/risk_measure_validation_20261117/gap_control.json"
        out.write_text(json.dumps({
            "n_pairs": len(pairs), "n_pos": int(lab.sum()),
            "unconditional_auc_ttc": overall, "unconditional_auc_gap": gap_only,
            "strata": [{"lo": r[0], "hi": r[1], "n": r[2], "pos": r[3], "auc": r[4]} for r in rows],
            "pooled_stratified_auc": pooled, "verdict": verdict,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())