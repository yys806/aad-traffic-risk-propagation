"""Formal test of whether the risk measure adds information beyond the gap.

The stratified version of this test is underpowered here: the clean follower sample has only a
few dozen hard-braking pairs, so per-stratum AUC values swing wildly between 0.44 and 0.92 on
three positives each. Those numbers are noise and must not be quoted.

Instead, fit a logistic regression with both the gap and the risk measure as predictors and test
whether the risk-measure coefficient is distinguishable from zero. Two parameters with a few
dozen events is at the edge of what is supportable, so results are reported with bootstrap
confidence intervals and at two label thresholds; a conclusion that does not survive those is
not reported as a conclusion.

Outcome of interest: does TTC explain the label once the gap is already in the model?
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import optimize

ROOT = Path(__file__).resolve().parents[2]
VJSON = ROOT / "code/outputs/analysis/risk_measure_validation_20261117/validation.json"


def auc_rank(pv, nv) -> float:
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


def fit_logit(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Newton-Raphson logistic regression. Returns coefficients and standard errors."""
    n, k = X.shape
    beta = np.zeros(k)

    def nll(b):
        z = X @ b
        return float(np.sum(np.logaddexp(0.0, z) - y * z))

    res = optimize.minimize(nll, beta, method="BFGS")
    b = res.x
    p = 1.0 / (1.0 + np.exp(-(X @ b)))
    W = p * (1 - p)
    H = X.T @ (X * W[:, None])
    try:
        cov = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        cov = np.linalg.pinv(H)
    return b, np.sqrt(np.diag(cov))


def analyse(pairs: list[dict], thr: float, seed: int = 20261117) -> dict:
    pos = [p for p in pairs if p["max_decel"] > thr]
    neg = [p for p in pairs if p["max_decel"] <= thr]
    if len(pos) < 8 or len(neg) < 30:
        return {}

    y = np.array([1.0] * len(pos) + [0.0] * len(neg))
    lg = np.log(np.array([p["min_gap"] for p in pos] + [p["min_gap"] for p in neg]) + 0.1)
    lt = np.log(np.array([max(p["min_ttc_brake"], 1e-3) for p in pos]
                         + [max(p["min_ttc_brake"], 1e-3) for p in neg]))
    one = np.ones_like(y)

    Xg = np.column_stack([one, lg])
    Xb = np.column_stack([one, lg, lt])
    bg, sg = fit_logit(Xg, y)
    bb, sb = fit_logit(Xb, y)

    def pred(X, b):
        return 1.0 / (1.0 + np.exp(-(X @ b)))

    pg = pred(Xg, bg)
    pb = pred(Xb, bb)
    n1, n0 = len(pos), len(neg)
    auc_g = auc_rank(pg[:n1], pg[n1:])
    auc_b = auc_rank(pb[:n1], pb[n1:])

    # bootstrap the AUC gain from adding the risk measure
    rng = np.random.default_rng(seed)
    gains = []
    idx1, idx0 = np.arange(n1), np.arange(n1, n1 + n0)
    for _ in range(1000):
        a = rng.choice(idx1, n1, True)
        c = rng.choice(idx0, n0, True)
        ii = np.concatenate([a, c])
        Xg_, Xb_, y_ = Xg[ii], Xb[ii], y[ii]
        try:
            b1, _ = fit_logit(Xg_, y_)
            b2, _ = fit_logit(Xb_, y_)
        except Exception:
            continue
        p1, p2 = pred(Xg_, b1), pred(Xb_, b2)
        gains.append(auc_rank(p2[:n1], p2[n1:]) - auc_rank(p1[:n1], p1[n1:]))
    lo, hi = (float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5))) \
        if len(gains) > 50 else (float("nan"), float("nan"))

    z = bb[2] / sb[2] if sb[2] > 0 else float("nan")
    return dict(threshold=thr, n_pos=n1, n_neg=n0,
                coef_gap=float(bg[1]), coef_gap_se=float(sg[1]),
                coef_ttc=float(bb[2]), coef_ttc_se=float(sb[2]),
                z_ttc=float(z), auc_gap_only=auc_g,
                auc_gap_plus_ttc=auc_b, auc_gain=auc_b - auc_g,
                auc_gain_ci=[lo, hi])


def main() -> int:
    d = json.loads(VJSON.read_text(encoding="utf-8"))
    pairs = [p for p in d["pairs"] if p.get("interior")] or d["pairs"]
    out = []
    print(f"pairs: {len(pairs)}")
    for thr in (2.0, 3.0):
        r = analyse(pairs, thr)
        if not r:
            continue
        out.append(r)
        print(f"\n--- label: hardest braking > {thr} m/s2 "
              f"({r['n_pos']} events / {r['n_neg']} ordinary) ---")
        print(f"  gap coefficient      {r['coef_gap']:+.3f}  (SE {r['coef_gap_se']:.3f})")
        print(f"  TTC coefficient      {r['coef_ttc']:+.3f}  (SE {r['coef_ttc_se']:.3f})"
              f"   z = {r['z_ttc']:+.2f}")
        print(f"  AUC gap only         {r['auc_gap_only']:.3f}")
        print(f"  AUC gap + TTC        {r['auc_gap_plus_ttc']:.3f}")
        print(f"  gain from TTC        {r['auc_gain']:+.3f}"
              f"   95% CI [{r['auc_gain_ci'][0]:+.3f}, {r['auc_gain_ci'][1]:+.3f}]")

    # verdict, stated conservatively
    print("\n=== verdict ===")
    for r in out:
        ci = r["auc_gain_ci"]
        if np.isfinite(ci[0]) and ci[0] > 0:
            v = "TTC adds information beyond the gap (bootstrap CI excludes 0)"
        elif np.isfinite(ci[1]) and ci[1] < 0:
            v = "TTC adds nothing and actively hurts"
        else:
            v = "no reliable evidence that TTC adds anything beyond the gap"
        print(f"  thr {r['threshold']}: {v}")
    print("\n  Caveat: events are few, so an AUC near 0.65 with a CI spanning zero means")
    print("  'not demonstrated', not 'disproved'. It is enough to forbid claiming the")
    print("  measure is a validated risk predictor, and enough to require that effects be")
    print("  reported in physical units (seconds of TTC, counts of hard braking) as well.")

    p = ROOT / "code/outputs/analysis/risk_measure_validation_20261117/gap_control_logit.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())