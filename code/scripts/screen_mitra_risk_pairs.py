"""Screen MiTra T1 raw trajectories for real follower pairs that actually produce risk events.

Why this exists: the three existing Task14 candidates were selected by *longest continuous
following*, not by risk. None of them contains a Formal P2 event (min TTC 3.24-6.52 s,
verified by `audit_real_follower_p2.py`). Using them to calibrate a follower model can only
ever produce zero events, no matter how good the model is.

Gap definition (fixed 2026-11-16): MiTra gives absolute x/y, and the previous version
computed a straight-line distance between the follower and *the leader recorded at the
first row*. That produced negative gaps (-1.9 to -8.8 m) because the leader relation
changes while driving (lane changes, overtaking). The fix:
  1. leader identity is read per row, not once;
  2. gap is the projection of the follower->leader vector onto the follower's heading,
     so lateral offset from a lane change does not masquerade as a negative gap;
  3. samples are kept only while the recorded leader is the same vehicle and the
     projected gap is positive.

Formal P2: TTC < 2.0 s, first-to-last observed span >= 0.2 s, consecutive samples no
further apart than 0.11 s.

MiTra T1 columns: Vehicle_ID, Vehicle_type, Time [s], x [m], y [m], Speed [km/h],
Lon. Acc., Lat. Acc., Angle [rad], Vehicle_length, Vehicle_width, Lane, Leader_ID,
Follower_ID, Left/Right Leader/Follower_ID. Leader_ID = "-1" means none.

Usage:
  python code/scripts/screen_mitra_risk_pairs.py --member T1_D1.csv --top 25
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

ZIP = Path("local_research/staging/task11_20261031/mitra/Data_T1.zip")
TTC_THRESH = 2.0
PERSIST = 0.2
MAX_GAP = 0.11


def norm_id(raw: str | None) -> str:
    """MiTra writes Vehicle_ID as '1.0' but Leader_ID as '11'; normalise both."""
    if not raw:
        return ""
    s = str(raw).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return "" if s in ("", "-1") else s


def p2_events(t: np.ndarray, ttc: np.ndarray) -> list[dict]:
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
            out.append({"onset_s": round(float(t[g[0]]), 3), "span_s": round(span, 3),
                        "min_ttc_s": round(float(np.nanmin(ttc[g])), 3)})
    return out


def load_member(name: str):
    """Parse one member; keep the per-row leader identity and heading."""
    zf = zipfile.ZipFile(ZIP)
    veh: dict[str, dict] = defaultdict(
        lambda: {"t": [], "x": [], "y": [], "v": [], "len": 5.0,
                 "leader": [], "lane": [], "angle": []})
    with zf.open(name) as raw:
        rd = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"))
        for row in rd:
            vid = norm_id(row["Vehicle_ID"])
            if not vid:
                continue
            try:
                d = veh[vid]
                d["t"].append(float(row["Time [s]"]))
                d["x"].append(float(row["x [m]"]))
                d["y"].append(float(row["y [m]"]))
                d["v"].append(float(row["Speed [km/h]"]) / 3.6)
                d["len"] = float(row["Vehicle_length [m]"])
                d["leader"].append(norm_id(row["Leader_ID"]))
                d["lane"].append(row["Lane"])
                d["angle"].append(float(row["Angle [rad]"]))
            except (TypeError, ValueError):
                continue
    for d in veh.values():
        for k in ("t", "x", "y", "v", "angle"):
            d[k] = np.asarray(d[k], dtype=float)
    return veh


def pair_series(fv: dict, lv: dict):
    """Return (t, gap, vf, vl) for the contiguous stretch where the leader is the same."""
    leader_id = None
    for lid in fv["leader"]:
        if lid:
            leader_id = lid
            break
    if not leader_id:
        return None

    keep = np.array([lid == leader_id for lid in fv["leader"]], dtype=bool)
    if keep.sum() < 10:
        return None

    t = fv["t"][keep]
    vf = fv["v"][keep]
    xf, yf = fv["x"][keep], fv["y"][keep]
    ang = fv["angle"][keep]

    inside = (t >= lv["t"][0]) & (t <= lv["t"][-1])
    if inside.sum() < 10:
        return None
    t, vf, xf, yf, ang = t[inside], vf[inside], xf[inside], yf[inside], ang[inside]

    xl = np.interp(t, lv["t"], lv["x"])
    yl = np.interp(t, lv["t"], lv["y"])
    vl = np.interp(t, lv["t"], lv["v"])

    # longitudinal projection onto the follower's heading
    dx, dy = xl - xf, yl - yf
    gap = dx * np.cos(ang) + dy * np.sin(ang) - (fv["len"] + lv["len"]) / 2.0
    return t, gap, vf, vl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", default="T1_D1.csv")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-samples", type=int, default=10)
    ap.add_argument("--out", default="code/outputs/analysis/mitra_pair_screen_20261116")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    veh = load_member(args.member)
    print(f"{args.member}: {len(veh)} vehicles")

    rows, rejected_negative = [], 0
    for vid, d in veh.items():
        lid = next((x for x in d["leader"] if x), None)
        if not lid or lid not in veh:
            continue
        series = pair_series(d, veh[lid])
        if series is None:
            continue
        t, gap, vf, vl = series
        if t.size < args.min_samples:
            continue
        if gap.min() < 0:
            rejected_negative += 1

        duration = float(t[-1] - t[0])
        closing = vf - vl
        ttc = np.full_like(t, np.inf)
        m = closing > 1e-6
        ttc[m] = gap[m] / closing[m]
        ev = p2_events(t, ttc)
        finite = ttc[np.isfinite(ttc)]
        rows.append({
            "pair": f"{vid}-{lid}",
            "follower": vid, "leader": lid,
            "lane": d["lane"][0] if d["lane"] else None,
            "duration_s": round(duration, 2),
            "samples": int(t.size),
            "p2_events": len(ev),
            "min_ttc_s": round(float(finite.min()), 3) if finite.size else None,
            "min_gap_m": round(float(gap.min()), 3),
            "mean_gap_m": round(float(gap.mean()), 3),
            "events": ev[:5],
        })

    valid = [r for r in rows if r["min_gap_m"] > 0]
    valid.sort(key=lambda r: (-r["p2_events"], r["min_ttc_s"] or 99))

    out = {"member": args.member, "vehicles": len(veh),
           "pairs_with_leader": len(rows),
           "pairs_positive_gap": len(valid),
           "pairs_rejected_negative_gap": len(rows) - len(valid),
           "with_events": sum(1 for r in valid if r["p2_events"] > 0),
           "rows": valid[: args.top]}
    (outdir / f"screen_{args.member.replace('.csv', '')}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"pairs with leader: {len(rows)}, positive-gap pairs: {len(valid)} "
          f"(rejected {len(rows) - len(valid)})")
    print(f"with >=1 P2 event: {out['with_events']}")
    if valid:
        print(f"span: median {np.median([r['duration_s'] for r in valid]):.1f}s")
    print(f"\n{'pair':<14}{'dur(s)':>7}{'gapmin':>8}{'P2':>4}{'minTTC':>8}")
    print("-" * 42)
    for r in valid[: args.top]:
        print(f"{r['pair']:<14}{r['duration_s']:>7.1f}{r['min_gap_m']:>8.2f}"
              f"{r['p2_events']:>4}{(r['min_ttc_s'] or 0):>8.2f}")
    print(f"\nwrote {outdir}/screen_{args.member.replace('.csv', '')}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())