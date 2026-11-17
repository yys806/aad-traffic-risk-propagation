"""Validate the risk measure's discrimination on real trajectories.

Question: does the risk measure actually separate dangerous car-following pairs from
ordinary ones? Everything downstream depends on this, and three external reviewers
independently doubted it — the metric may only be re-measuring the gap.

Method, following the established surrogate-safety literature (FHWA SSAM; the QUT systematic
review lists ROC/AUC as the standard way to validate a surrogate measure):

  * Candidate metrics, all computed from gap and speed only:
        min TTC (constant-velocity, the SSAM/industry standard)
        min TTC_braking (the variant this project uses: leader brakes at 4.5 m/s^2)
        max DRAC (deceleration rate to avoid crash)
        min gap (a deliberately naive baseline)
        rho = exp(-TTC_braking / tau), reported at tau/2, tau, 2*tau
  * Label, deliberately INDEPENDENT of every metric above:
        the follower's own measured longitudinal deceleration exceeds a threshold.
    Using TTC to define "dangerous" and then showing TTC predicts it would be circular.
    Acceleration is an observed evasive action, which the literature treats as a separate
    conflict criterion, so it breaks the circularity.

Output: AUC per metric per threshold, with sample sizes and confidence intervals.

Usage:
  python code/scripts/validate_risk_measure.py
"""
from __future__ import annotations

import csv
import io
import json
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "scripts"))
from screen_mitra_risk_pairs import norm_id  # noqa: E402

ZIP = ROOT / "local_research/staging/task11_20261031/mitra/Data_T1.zip"
MEMBER = "T1_D1.csv"
LEADER_BRAKE = 4.5     # same value the experiment uses
TAU = 15.364279197080283
TRUNC_GUARD_S = 1.0    # ignore events starting this close to the end of a trajectory
FOLLOW_GAP = 30.0      # metres; beyond this the follower is not interacting with the leader


def load_member(name: str) -> dict[str, dict]:
    """Parse one member, keeping acceleration (the label source) and heading."""
    zf = zipfile.ZipFile(ZIP)
    veh: dict[str, dict] = defaultdict(
        lambda: {"t": [], "x": [], "y": [], "v": [], "acc": [], "len": 5.0,
                 "leader": [], "lane": [], "angle": []})
    with zf.open(name) as raw:
        rd = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"))
        for row in rd:
            vid = norm_id(row.get("Vehicle_ID"))
            if not vid:
                continue
            # Parse every field into locals FIRST, then append. Appending as we go leaves
            # partially-filled lists when one column is missing or malformed, which silently
            # misaligns the arrays instead of failing loudly.
            try:
                t_ = float(row["Time [s]"])
                x_ = float(row["x [m]"])
                y_ = float(row["y [m]"])
                v_ = float(row["Speed [km/h]"]) / 3.6
                a_ = float(row.get("Lon. Acc. [ms-2]") or row.get("Lon. Acc.") or 0.0)
                ang_ = float(row.get("Angle [rad]") or 0.0)
                len_ = float(row.get("Vehicle_length [m]") or 5.0)
            except (TypeError, ValueError, KeyError):
                continue
            d = veh[vid]
            d["t"].append(t_)
            d["x"].append(x_)
            d["y"].append(y_)
            d["v"].append(v_)
            d["acc"].append(a_)
            d["angle"].append(ang_)
            d["len"] = len_
            d["leader"].append(norm_id(row.get("Leader_ID")))
            d["lane"].append(row.get("Lane"))
    for d in veh.values():
        for k in ("t", "x", "y", "v", "acc", "angle"):
            d[k] = np.asarray(d[k], dtype=float)
    return veh


def lid_of(fv: dict, lv: dict) -> str:
    for x in fv["leader"]:
        if x:
            return x
    return ""


def pair_metrics(fv: dict, lv: dict) -> dict | None:
    """Align a follower with its leader in time and compute all candidate metrics."""
    # leader rows are indexed by time
    lt, lx, ly, lvsp, ll = lv["t"], lv["x"], lv["y"], lv["v"], lv["len"]
    if len(lt) < 10:
        return None
    order = np.argsort(lt)
    lt, lx, ly, lvsp = lt[order], lx[order], ly[order], lvsp[order]

    ft, fx, fy, fvsp, facc, fl = fv["t"], fv["x"], fv["y"], fv["v"], fv["acc"], fv["len"]
    if len(ft) < 10:
        return None

    # Use only the contiguous stretch where this leader stays the same, otherwise
    # interpolating one leader across a leader change invents following that never happened.
    led = fv["leader"]
    target = lid_of(fv, lv)
    best = None
    start = 0
    for i in range(1, len(led) + 1):
        if i == len(led) or led[i] != led[start]:
            seg = (start, i)
            if best is None or (seg[1] - seg[0]) > (best[1] - best[0]):
                best = seg
            start = i
    if best is None or best[1] - best[0] < 10:
        return None
    s, e = best

    t = ft[s:e]
    fx_i, fy_i, fv_i, facc_i = fx[s:e], fy[s:e], fvsp[s:e], facc[s:e]
    ang_i = fv["angle"][s:e]

    inside = (t >= lt[0]) & (t <= lt[-1])
    if inside.sum() < 10:
        return None
    t = t[inside]
    fx_i, fy_i, fv_i, facc_i, ang_i = (fx_i[inside], fy_i[inside], fv_i[inside],
                                       facc_i[inside], ang_i[inside])
    lx_i = np.interp(t, lt, lx)
    ly_i = np.interp(t, lt, ly)
    lv_i = np.interp(t, lt, lvsp)

    # project the follower->leader vector onto the follower's heading, so a lateral offset
    # during a lane change does not masquerade as a negative gap
    dx, dy = lx_i - fx_i, ly_i - fy_i
    gap = dx * np.cos(ang_i) + dy * np.sin(ang_i) - 0.5 * (fl + ll)
    if np.nanmin(gap) <= 0:
        return None    # overlapping / bad geometry: not a clean following pair

    # Restrict to the car-following regime. A driver who brakes hard at a traffic light or
    # through a curve is NOT reacting to the leader, and counting that as a positive would
    # add label noise that has nothing to do with following risk.
    near = gap < FOLLOW_GAP
    if near.sum() < 10:
        return None

    dv = fv_i - lv_i          # >0 means closing
    # --- candidate metrics, gap and speed only ---
    with np.errstate(divide="ignore", invalid="ignore"):
        ttc_const = np.where(dv > 1e-6, gap / dv, np.inf)
        disc = dv * dv + 2.0 * LEADER_BRAKE * gap
        ttc_brake = np.where(disc > 0, (-dv + np.sqrt(np.maximum(disc, 0))) / LEADER_BRAKE, 0.0)
        drac = np.where(dv > 0, dv * dv / (2.0 * gap), 0.0)

    min_ttc = float(np.min(ttc_const[near]))
    min_ttc_b = float(np.min(ttc_brake[near]))
    max_drac = float(np.max(drac[near]))
    min_gap = float(np.min(gap[near]))
    # --- label source: the follower's own braking, independent of all of the above ---
    # measured only while following, so it reflects a reaction to the leader
    dec_follow = np.maximum(0.0, -facc_i[near])
    max_decel = float(np.max(dec_follow))             # magnitude of hardest braking
    mean_decel_pos = float(np.mean(dec_follow))
    # fraction of steps with meaningful braking: guards against one noise spike = "event"
    brake_frac = float(np.mean(dec_follow > 2.0))

    # does any hard-braking onset happen far enough from the trajectory end?
    dur = float(t[-1] - t[0])
    interior = dur > 2 * TRUNC_GUARD_S and (t[-1] - t[np.argmin(facc_i)]) > TRUNC_GUARD_S

    return dict(min_ttc=min_ttc, min_ttc_brake=min_ttc_b, max_drac=max_drac,
                min_gap=min_gap, max_decel=max_decel, mean_decel=mean_decel_pos,
                brake_frac=brake_frac, n_follow=int(near.sum()),
                duration_s=dur, samples=int(len(t)), interior=bool(interior))


def auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Rank-based AUC: probability a positive scores higher than a negative."""
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    order = allv.argsort()
    ranks = np.empty(len(allv), dtype=float)
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks for ties
    _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    sum_ranks = np.zeros(len(cnt))
    np.add.at(sum_ranks, inv, ranks)
    ranks = (sum_ranks / cnt)[inv]
    r_pos = ranks[:len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def bootstrap_ci(pos, neg, n=2000, seed=20261117):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        p = rng.choice(pos, len(pos), replace=True)
        q = rng.choice(neg, len(neg), replace=True)
        vals.append(auc(p, q))
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))


def main() -> int:
    print("loading MiTra trajectories ...")
    veh = load_member(MEMBER)
    print(f"  vehicles: {len(veh)}")

    rows = []
    for vid, d in veh.items():
        lid = next((x for x in d["leader"] if x), None)
        if not lid or lid not in veh:
            continue
        m = pair_metrics(d, veh[lid])
        if m is None:
            continue
        m["pair"] = f"{vid}-{lid}"
        rows.append(m)
    print(f"  usable pairs: {len(rows)}")

    # Metrics where LOWER means more dangerous, and where HIGHER means more dangerous.
    # Orientation: a LARGER value must mean "more dangerous" before computing AUC.
    # rho = exp(-TTC/tau) is near 1 when TTC is small, so higher rho = more dangerous.
    lower_better = {"min_ttc": 1, "min_ttc_brake": 1, "min_gap": 1}
    higher_better = {"max_drac": 1, "max_decel": 1,
                     "rho_tau": 1, "rho_tau_half": 1, "rho_tau_double": 1}

    for r in rows:
        r["rho_tau"] = math.exp(-r["min_ttc_brake"] / TAU)
        r["rho_tau_half"] = math.exp(-r["min_ttc_brake"] / (TAU / 2))
        r["rho_tau_double"] = math.exp(-r["min_ttc_brake"] / (2 * TAU))

    metric_names = ["min_ttc", "min_ttc_brake", "max_drac", "min_gap",
                    "rho_tau", "rho_tau_half", "rho_tau_double"]

    results = {}
    print(f"\n{'label (max decel >)':<22}{'n_pos':>7}{'n_neg':>7}", end="")
    for mn in metric_names:
        print(f"{mn[:13]:>15}", end="")
    print()
    print("-" * (36 + 15 * len(metric_names)))

    label_defs = []
    for thr in (2.0, 3.0, 4.0, 5.0):
        label_defs.append((f"peak>{thr:.1f}m/s2", lambda r, t=thr: r["max_decel"] > t))
    # sustained braking is a stricter, less noise-prone definition than a single peak sample
    for frac in (0.02, 0.05, 0.10):
        label_defs.append((f"sustained>{frac:.0%}", lambda r, f=frac: r["brake_frac"] > f))

    for lname, lfn in label_defs:
        for interior_only in (False, True):
            subset = [r for r in rows if (r["interior"] if interior_only else True)]
            pos_r = [r for r in subset if lfn(r)]
            neg_r = [r for r in subset if not lfn(r)]
            if len(pos_r) < 10 or len(neg_r) < 10:
                continue
            tag = lname + (" interior" if interior_only else "")
            line = {}
            print(f"{tag:<22}{len(pos_r):>7}{len(neg_r):>7}", end="")
            for mn in metric_names:
                p = np.array([r[mn] for r in pos_r])
                q = np.array([r[mn] for r in neg_r])
                # orient so that a larger value means "more dangerous"
                if mn in lower_better:
                    p, q = -p, -q
                a = auc(p, q)
                lo, hi = bootstrap_ci(p, q)
                line[mn] = dict(auc=a, ci=[lo, hi])
                print(f"{a:>7.3f}      ", end="")
            print()
            results[tag] = {"n_pos": len(pos_r), "n_neg": len(neg_r), "metrics": line}

    print("\n--- label distribution (max decel while following, m/s2) ---")
    md = np.array([r["max_decel"] for r in rows])
    for q in (10, 25, 50, 75, 90, 95, 99):
        print(f"  p{q:<3} = {np.percentile(md, q):.2f}")
    bf = np.array([r["brake_frac"] for r in rows])
    print(f"  sustained-braking fraction: median {np.median(bf):.3f}, "
          f"p90 {np.percentile(bf, 90):.3f}")

    # what do the metrics actually correlate with?
    print("\n--- sanity: correlation of each metric with the independent label ---")
    dec = np.array([r["max_decel"] for r in rows])
    for mn in metric_names:
        v = np.array([r[mn] for r in rows])
        v = np.where(np.isfinite(v), v, np.nan)
        ok = np.isfinite(v)
        if ok.sum() > 50:
            c = float(np.corrcoef(v[ok], dec[ok])[0, 1])
            print(f"  {mn:<16} r = {c:+.3f}  (n={int(ok.sum())})")

    outdir = ROOT / "code/outputs/analysis/risk_measure_validation_20261117"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "validation.json").write_text(json.dumps({
        "member": MEMBER, "n_pairs": len(rows), "tau": TAU,
        "leader_brake_mps2": LEADER_BRAKE, "results": results,
        "pairs": [{k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                   for k, v in r.items()} for r in rows],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {outdir/'validation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())