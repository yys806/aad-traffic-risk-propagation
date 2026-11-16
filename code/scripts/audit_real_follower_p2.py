"""Compute Formal-P2 event counts on the REAL follower in each Task14 candidate pair.

The Task14 candidate inputs already contain the real follower and the real leader
(both positions and speeds), so the event count of the real follower is directly
computable. This gives the per-pair reference that a simulated follower must match,
which is the cheapest possible check of where the event gap comes from.

Formal P2 (unchanged definition): TTC < 2.0 s, first-to-last observed span >= 0.2 s,
consecutive samples no further apart than 0.11 s.

Usage:
  python code/scripts/audit_real_follower_p2.py [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

TTC_THRESH = 2.0
PERSIST = 0.2
MAX_GAP = 0.11

INPUT_DIR = Path("local_research/staging/task14_20261031/candidate_inputs")


def load_pair(path: Path):
    """Return (t, follower_speed, leader_speed, gap) in SI units."""
    t, vf, vl, gap = [], [], [], []
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t.append(float(row["relative_time_s"]))
            vf.append(float(row["follower_speed_kmh"]) / 3.6)
            vl.append(float(row["leader_speed_kmh"]) / 3.6)
            gap.append(float(row["approximate_gap_m"]))
    return t, vf, vl, gap


def ttc_series(vf, vl, gap):
    """TTC = gap / closing speed; only defined when the follower is closing."""
    out = []
    for v_f, v_l, g in zip(vf, vl, gap):
        closing = v_f - v_l
        out.append(g / closing if closing > 1e-6 else float("inf"))
    return out


def p2_events(t, ttc, thresh=TTC_THRESH, persist=PERSIST, max_gap=MAX_GAP):
    below = [i for i, x in enumerate(ttc) if x < thresh]
    if len(below) < 2:
        return []
    events, group = [], [below[0]]
    for prev, cur in zip(below, below[1:]):
        step = t[cur] - t[prev]
        if step > max_gap + 1e-12:
            events.append(group)
            group = [cur]
        else:
            group.append(cur)
    events.append(group)

    out = []
    for g in events:
        if len(g) < 2:
            continue
        span = t[g[-1]] - t[g[0]]
        if span >= persist - 1e-12:
            out.append({"onset_s": t[g[0]], "span_s": span,
                        "min_ttc_s": min(ttc[i] for i in g), "n": len(g)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="code/outputs/analysis/real_follower_p2_20261116")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(INPUT_DIR.glob("*_raw.csv")):
        name = path.name.replace("_raw.csv", "")
        t, vf, vl, gap = load_pair(path)
        ttc = ttc_series(vf, vl, gap)
        ev = p2_events(t, ttc)

        duration_s = t[-1] - t[0]
        exposure_h = duration_s / 3600.0
        finite = [x for x in ttc if x != float("inf")]
        rows.append({
            "pair": name,
            "samples": len(t),
            "duration_s": round(duration_s, 2),
            "exposure_veh_h": round(exposure_h, 5),
            "p2_events": len(ev),
            "p2_rate_per_veh_h": round(len(ev) / exposure_h, 1) if exposure_h else None,
            "min_ttc_s": round(min(finite), 3) if finite else None,
            "below_2s_samples": sum(1 for x in finite if x < 2.0),
            "events": ev,
        })

    (outdir / "real_follower_p2.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{'pair':<14}{'dur(s)':>8}{'expo(h)':>9}{'P2':>4}{'rate':>8}{'minTTC':>8}{'<2s':>5}")
    print("-" * 56)
    for r in rows:
        print(f"{r['pair']:<14}{r['duration_s']:>8.1f}{r['exposure_veh_h']:>9.4f}"
              f"{r['p2_events']:>4}{(r['p2_rate_per_veh_h'] or 0):>8.1f}"
              f"{(r['min_ttc_s'] or 0):>8.2f}{r['below_2s_samples']:>5}")
    print(f"\nwrote {outdir/'real_follower_p2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
