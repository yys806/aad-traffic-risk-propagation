"""Test whether the sign of the message effect depends on how regional risk is normalised.

Codex's point 6.4: "区域总体风险" is not uniquely defined. The candidates respond
differently to a treatment that also changes how long vehicles stay in the region:
  - per roster vehicle        : sum over fixed roster / N          (current)
  - per vehicle-time in region: sum / (vehicle-seconds inside region)
  - per distance travelled    : sum / (metres driven inside region)

The message arm keeps vehicles in the region longer (0.698 -> 0.745) and slower
(15.25 -> 11.26 m/s). If the rise is an exposure artefact, normalising by vehicle-time
should shrink or reverse it.

Usage:
  python code/scripts/risk_normalisation_test.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "code/outputs/analysis/stage1_isolated_20261116"
STEP = 0.05
TGT_REGION = (3000.0, 4000.0)
TAU = 15.364279197080283
WARMUP = 40.0


def load(arm: str):
    s = json.loads((OUT / "arms_series.json").read_text(encoding="utf-8"))
    return s[f"20261116_{arm}"]


def series_of(series: dict, roster: tuple[str, ...]):
    """Per-step raw risk sum and per-step exposure denominators."""
    n = len(next(iter(series.values()))["x"])
    risk_sum = np.zeros(n)
    veh_time = np.zeros(n)
    veh_dist = np.zeros(n)
    for k in range(n):
        rows = []
        for v in series:
            x, sp = series[v]["x"][k], series[v]["v"][k]
            if x is None or sp is None:
                continue
            rows.append((x, sp, v))
        rows.sort()
        for i in range(len(rows) - 1):
            x, sp, v = rows[i]
            if v not in roster or not (TGT_REGION[0] <= x < TGT_REGION[1]):
                continue
            lx, lsp, _ = rows[i + 1]
            gap = lx - x - 5.0
            closing = sp - lsp
            if gap <= 0 or closing <= 1e-6:
                continue
            risk_sum[k] += float(np.exp(-(gap / closing) / TAU))
        # exposure denominators over the roster inside the region
        for v in roster:
            x, sp = series[v]["x"][k], series[v]["v"][k]
            if x is None or sp is None:
                continue
            if TGT_REGION[0] <= x < TGT_REGION[1]:
                veh_time[k] += STEP
                veh_dist[k] += max(0.0, sp) * STEP
    return risk_sum, veh_time, veh_dist


def main() -> int:
    a0, a1 = load("opn0"), load("opn1")
    lock = int(round(WARMUP / STEP))
    roster = tuple(sorted(v for v in a0
                          if a0[v]["x"][lock] is not None
                          and TGT_REGION[0] <= a0[v]["x"][lock] < TGT_REGION[1]))
    print(f"roster {len(roster)}")

    r0, t0, d0 = series_of(a0, roster)
    r1, t1, d1 = series_of(a1, roster)

    def report(name, num0, num1, den0, den1):
        a, b = num0.sum() / den0.sum(), num1.sum() / den1.sum()
        sign = "opn1 更高" if b > a else "opn1 更低"
        print(f"{name:<26} opn0={a:.4e}  opn1={b:.4e}  比值={b/a if a else float('nan'):7.3f}  {sign}")

    print()
    report("按固定名单车辆归一", r0, r1, np.full_like(r0, len(roster)), np.full_like(r1, len(roster)))
    report("按区内车辆-时间归一", r0, r1, t0, t1)
    report("按区内行驶距离归一", r0, r1, d0, d1)
    print()
    print(f"区内车辆-时间总数: opn0={t0.sum():.1f} 车·秒   opn1={t1.sum():.1f} 车·秒  "
          f"比值={t1.sum()/max(t0.sum(),1e-9):.3f}")
    print(f"区内行驶距离总数:   opn0={d0.sum():.1f} m       opn1={d1.sum():.1f} m      "
          f"比值={d1.sum()/max(d0.sum(),1e-9):.3f}")

    res = {
        "roster": len(roster),
        "per_vehicle_opn0": float(r0.sum() / (len(roster) * len(r0))),
        "per_vehicle_opn1": float(r1.sum() / (len(roster) * len(r1))),
        "per_veh_time_opn0": float(r0.sum() / max(t0.sum(), 1e-9)),
        "per_veh_time_opn1": float(r1.sum() / max(t1.sum(), 1e-9)),
        "per_distance_opn0": float(r0.sum() / max(d0.sum(), 1e-9)),
        "per_distance_opn1": float(r1.sum() / max(d1.sum(), 1e-9)),
        "veh_time_ratio": float(t1.sum() / max(t0.sum(), 1e-9)),
        "distance_ratio": float(d1.sum() / max(d0.sum(), 1e-9)),
    }
    (OUT / "normalisation_test.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {OUT/'normalisation_test.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())