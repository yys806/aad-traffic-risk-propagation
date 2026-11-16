"""Group the exploratory offline regional-Y results by density and perturbation dose.

Reads the CSV produced by offline_regional_y_exploratory.py and reports, per cell:
n, mean, min, max, sd. Runs that produced no usable Y are listed separately and never
silently dropped (task-book red line).
"""
from __future__ import annotations

import collections
import csv
import statistics
import sys
from pathlib import Path


def parse_run_id(run_id: str):
    parts = run_id.split("_")
    if len(parts) < 3:
        return ("?", "?")
    return (parts[1], parts[2])


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "code/outputs/analysis/offline_regional_y_20261116/regional_y_by_run.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))

    empty = [r for r in rows if r["lower_Y"] == ""]
    print(f"total runs: {len(rows)}   no-Y runs: {len(empty)}")
    for r in empty[:15]:
        print(f"   {r['run_id']}  roster_N={r['roster_N']}  status={r['Y_status']}")
    if len(empty) > 15:
        print(f"   ... and {len(empty) - 15} more")

    groups = collections.defaultdict(list)
    for r in rows:
        if r["lower_Y"] == "":
            continue
        groups[parse_run_id(r["run_id"])].append(float(r["lower_Y"]))

    header = f"{'density':<8}{'dose':<10}{'n':>4}{'mean':>10}{'min':>10}{'max':>10}{'sd':>10}"
    print()
    print(header)
    print("-" * len(header))
    for key in sorted(groups):
        vals = groups[key]
        dens, dose = key
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(f"{dens:<8}{dose:<10}{len(vals):>4}{statistics.mean(vals):>10.5f}"
              f"{min(vals):>10.5f}{max(vals):>10.5f}{sd:>10.5f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
