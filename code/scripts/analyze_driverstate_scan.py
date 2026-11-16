"""Summarise a driverstate awareness scan: event rate per dose with uncertainty.

Reports, for each awareness level: number of runs, mean/sd event rate, min/max,
a Poisson-based 95% interval on the pooled event count, collisions, density and speed.
Also compares against the NGSIM reference band (17.0 / 23.5 events per veh-hour).

Usage:
  python code/scripts/analyze_driverstate_scan.py <scan_summary.json> [more.json ...]
"""
from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

NGSIM_RATES = (17.0, 23.5)


def poisson_ci(k: int, alpha: float = 0.05):
    """Exact-ish Poisson interval (Garwood) without scipy."""
    if k == 0:
        return (0.0, 3.689)  # upper bound for 0 events at 95%
    # Wilson-Hilferty approximation of chi-square quantiles
    def chi2_lower(df):
        z = 1.959963985
        return df * (1 - 2 / (9 * df) - z * math.sqrt(2 / (9 * df))) ** 3

    def chi2_upper(df):
        z = 1.959963985
        return df * (1 - 2 / (9 * df) + z * math.sqrt(2 / (9 * df))) ** 3

    lo = chi2_lower(2 * k) / 2
    hi = chi2_upper(2 * k + 2) / 2
    return (lo, hi)


def main() -> int:
    files = [Path(f) for f in sys.argv[1:]]
    if not files:
        print(__doc__)
        return 1

    rows = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        for r in data:
            if r.get("status") != "OK":
                continue
            r["_src"] = f.name
            rows.append(r)

    if not rows:
        print("no OK runs")
        return 1

    by_aw = collections.defaultdict(list)
    for r in rows:
        by_aw[r["awareness"]].append(r)

    print(f"runs total: {len(rows)}")
    print(f"NGSIM reference: {NGSIM_RATES[0]:.1f} / {NGSIM_RATES[1]:.1f} events per veh-hour\n")

    hdr = (f"{'awareness':<10}{'n':>3}{'events':>7}{'exposure':>9}"
           f"{'rate mean':>10}{'sd':>7}{'min':>7}{'max':>7}"
           f"{'pooled':>8}{'95% CI':>16}{'coll':>6}{'density':>9}{'v':>7}")
    print(hdr)
    print("-" * len(hdr))

    for aw in sorted(by_aw):
        rs = by_aw[aw]
        rates = [x["p2_rate_per_veh_h"] for x in rs if x.get("p2_rate_per_veh_h") is not None]
        ev = sum(x.get("p2_events", 0) for x in rs)
        expo = sum(x.get("exposure_veh_h", 0) for x in rs)
        pooled = ev / expo if expo else float("nan")
        lo, hi = poisson_ci(ev)
        lo_r, hi_r = (lo / expo if expo else float("nan")), (hi / expo if expo else float("nan"))
        coll = sum(x.get("collisions", 0) for x in rs)
        dens = sum(x.get("density_veh_per_km_lane") or 0 for x in rs) / len(rs)
        vel = sum(x.get("v_mean_in_region") or 0 for x in rs) / len(rs)
        sd = (sum((r - sum(rates) / len(rates)) ** 2 for r in rates) / (len(rates) - 1)) ** 0.5 if len(rates) > 1 else 0.0
        print(f"{aw:<10.2f}{len(rs):>3}{ev:>7}{expo:>9.2f}"
              f"{sum(rates)/len(rates):>10.1f}{sd:>7.1f}"
              f"{min(rates):>7.1f}{max(rates):>7.1f}"
              f"{pooled:>8.1f}{f'[{lo_r:.1f},{hi_r:.1f}]':>16}"
              f"{coll:>6}{dens:>9.1f}{vel:>7.2f}")

    print("\n判读要点：")
    print("- 看 pooled 的 95% 区间是否覆盖 17.0–23.5；覆盖说明该剂量与现场一致。")
    print("- 看 sd：同剂量下种子间离散度过大时，单次运行不能代表该剂量。")
    print("- 看 coll：撞车次数明显高于现场水平说明剂量过头。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
