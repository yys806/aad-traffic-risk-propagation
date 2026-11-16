"""Screen MiTra T1 raw trajectories for real follower pairs that actually produce risk events.

Why: the three existing Task14 candidates were selected by *longest continuous following*,
not by risk. None of them contains a Formal P2 event (min TTC 3.24-6.52 s, verified by
`audit_real_follower_p2.py`). They therefore cannot serve as the reference that a
simulated follower must reproduce.

This script scans the raw MiTra T1 CSVs, reconstructs every leader/follower pair from the
Leader_ID column, computes TTC from positions and speeds, and ranks pairs by the number of
Formal P2 events. The shortlist can be fed straight into the existing
`stage_0_5_leader_replay` machinery.

MiTra T1 columns: Vehicle_ID, Vehicle_type, Time [s], x [m], y [m], Speed [km/h],
Lon. Acc., Lat. Acc., Angle [rad], Vehicle_length, Vehicle_width, Lane, Leader_ID,
Follower_ID, Left/Right Leader/Follower_ID. Leader_ID = "-1" means none.

Usage:
  python code/scripts/screen_mitra_risk_pairs.py --member T1_D1.csv --top 20
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


def norm_id(raw: str | None) -> str:
    """MiTra writes Vehicle_ID as '1.0' but Leader_ID as '11'; normalise both."""
    if not raw:
        return ""
    s = str(raw).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return "" if s in ("", "-1") else s


def load_member(name: str):
    """Parse one MiTra member into per-vehicle arrays."""
    zf = zipfile.ZipFile(ZIP)
    veh: dict[str, dict] = defaultdict(
        lambda: {"t": [], "x": [], "y": [], "v": [], "len": 5.0, "leader": None, "lane": None})
    with zf.open(name) as raw:
        rd = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"))
        for row in rd:
            vid = norm_id(row["Vehicle_ID"])
            try:
                d = veh[vid]
                d["t"].append(float(row["Time [s]"]))
                d["x"].append(float(row["x [m]"]))
                d["y"].append(float(row["y [m]"]))
                d["v"].append(float(row["Speed [km/h]"]) / 3.6)
                d["len"] = float(row["Vehicle_length [m]"])
                if d["leader"] is None:
                    d["leader"] = norm_id(row["Leader_ID"])
                    d["lane"] = row["Lane"]
            except (TypeError, ValueError):
                continue
    for d in veh.values():
        for k in ("t", "x", "y", "v"):
            d[k] = np.asarray(d[k], dtype=float)
    return veh


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", default="T1_D1.csv")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-len-s", type=float, default=2.0,
                    help="minimum overlapping tracking span; MiTra median is only 11 s")
    ap.add_argument("--out", default="code/outputs/analysis/mitra_pair_screen_20261116")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    veh = load_member(args.member)
    print(f"{args.member}: {len(veh)} vehicles")

    rows = []
    for vid, d in veh.items():
        lid = d["leader"]
        if not lid or lid not in veh:
            continue
        ld = veh[lid]
        if d["t"].size < 20 or ld["t"].size < 20:
            continue

        ok = (d["t"] >= ld["t"][0]) & (d["t"] <= ld["t"][-1])
        if ok.sum() < 10:
            continue
        t = d["t"][ok]
        vf = d["v"][ok]
        xf, yf = d["x"][ok], d["y"][ok]
        xl = np.interp(t, ld["t"], ld["x"])
        yl = np.interp(t, ld["t"], ld["y"])
        vl = np.interp(t, ld["t"], ld["v"])

        gap = np.hypot(xl - xf, yl - yf) - (d["len"] + ld["len"]) / 2.0
        closing = vf - vl
        ttc = np.full_like(t, np.inf)
        m = closing > 1e-6
        ttc[m] = gap[m] / closing[m]

        duration = float(t[-1] - t[0])
        if duration < args.min_len_s:
            continue
        ev = p2_events(t, ttc)
        finite = ttc[np.isfinite(ttc)]
        rows.append({
            "pair": f"{vid}-{lid}",
            "follower": vid, "leader": lid,
            "lane": d["lane"],
            "duration_s": round(duration, 2),
            "samples": int(t.size),
            "p2_events": len(ev),
            "min_ttc_s": round(float(finite.min()), 3) if finite.size else None,
            "min_gap_m": round(float(gap.min()), 3),
            "events": ev[:5],
        })

    rows.sort(key=lambda r: (-r["p2_events"], r["min_ttc_s"] or 99))
    spans = [r["duration_s"] for r in rows]
    if spans:
        print(f"pair span: median {np.median(spans):.1f}s, max {max(spans):.1f}s")
    out = {"member": args.member, "vehicles": len(veh),
           "pairs_screened": len(rows), "rows": rows[: args.top]}
    (outdir / f"screen_{args.member.replace('.csv', '')}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    with_events = sum(1 for r in rows if r["p2_events"] > 0)
    print(f"pairs: {len(rows)}, with >=1 P2 event: {with_events}")
    print(f"\n{'pair':<14}{'dur(s)':>8}{'P2':>4}{'minTTC':>8}{'minGap':>8}")
    print("-" * 44)
    for r in rows[: args.top]:
        print(f"{r['pair']:<14}{r['duration_s']:>8.1f}{r['p2_events']:>4}"
              f"{(r['min_ttc_s'] or 0):>8.2f}{r['min_gap_m']:>8.2f}")
    print(f"\nwrote {outdir}/screen_{args.member.replace('.csv', '')}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())