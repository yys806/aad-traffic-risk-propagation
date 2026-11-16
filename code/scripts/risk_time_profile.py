"""Recompute the per-step regional risk for both arms and look at its time profile.

The summary file only stores aggregate risk; the question "is the rise transient or
sustained" needs the per-step series. Because the roster is fixed and vehicles outside the
region contribute zero, risk can be recomputed from the stored positions and speeds plus
the leader relation, which is reconstructed from ordering along the lane.

Usage:
  python code/scripts/risk_time_profile.py
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


def step_risk(series: dict, roster: tuple[str, ...]) -> np.ndarray:
    n = len(next(iter(series.values()))["x"])
    out = np.zeros(n)
    for k in range(n):
        # gather vehicles inside the region with valid state
        rows = []
        for v in series:
            x = series[v]["x"][k]
            sp = series[v]["v"][k]
            if x is None or sp is None:
                continue
            rows.append((x, sp, v))
        rows.sort()          # increasing lane position; the last one is the leader-most
        total = 0.0
        for i in range(len(rows) - 1):
            x, sp, v = rows[i]
            if not (TGT_REGION[0] <= x < TGT_REGION[1]):
                continue
            if v not in roster:
                continue
            lx, lsp, lv = rows[i + 1]
            gap = lx - x - 5.0            # net gap, vehicle length 5 m
            closing = sp - lsp
            if gap <= 0 or closing <= 1e-6:
                continue
            ttc = gap / closing
            total += float(np.exp(-ttc / TAU))
        out[k] = total / len(roster) if roster else 0.0
    return out


def main() -> int:
    ev = json.loads((OUT / "arms_summary.json").read_text(encoding="utf-8"))
    a0, a1 = load("opn0"), load("opn1")
    # The roster is the set of vehicles inside the region at the warmup boundary, which is
    # how run_stage1_isolated_two_arm locks it. Vehicle IDs are T0..T386, so assuming
    # T0..T59 (the roster size) would silently select the wrong vehicles.
    lock = int(round(WARMUP / STEP))
    roster = tuple(sorted(v for v in a0
                          if a0[v]["x"][lock] is not None
                          and TGT_REGION[0] <= a0[v]["x"][lock] < TGT_REGION[1]))
    print(f"reconstructed roster: {len(roster)} vehicles")
    r0 = step_risk(a0, roster)
    r1 = step_risk(a1, roster)
    t = np.arange(len(r0)) * STEP

    print(f"{'t':>7}{'opn0风险':>12}{'opn1风险':>12}{'比值':>10}")
    print("-" * 43)
    for k in range(0, len(t), 100):
        ratio = (r1[k] / r0[k]) if r0[k] > 1e-12 else float("nan")
        print(f"{t[k]:>7.1f}{r0[k]:>12.3e}{r1[k]:>12.3e}{ratio:>10.2f}")

    post = t >= 52.2
    print(f"\n事件前 opn0 均值 {r0[~post].mean():.3e}   opn1 均值 {r1[~post].mean():.3e}")
    print(f"事件后 opn0 均值 {r0[post].mean():.3e}   opn1 均值 {r1[post].mean():.3e}")
    # is the rise front-loaded or sustained?
    if post.any():
        idx = np.flatnonzero(post)
        third = len(idx) // 3
        segs = [idx[:third], idx[third:2*third], idx[2*third:]]
        labels = ["事件后前段", "事件后中段", "事件后后段"]
        for lab, seg in zip(labels, segs):
            if seg.size:
                print(f"  {lab}: opn0={r0[seg].mean():.3e}  opn1={r1[seg].mean():.3e}  "
                      f"比值={r1[seg].mean()/max(r0[seg].mean(),1e-12):.2f}")

    res = {"opn0_pre": float(r0[~post].mean()), "opn1_pre": float(r1[~post].mean()),
           "opn0_post": float(r0[post].mean()), "opn1_post": float(r1[post].mean()),
           "note": "risk recomputed from stored kinematics; leader = next vehicle ahead in lane position"}
    (OUT / "risk_profile.json").write_text(json.dumps(res, indent=2, ensure_ascii=False),
                                           encoding="utf-8")
    print(f"\nwrote {OUT/'risk_profile.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())