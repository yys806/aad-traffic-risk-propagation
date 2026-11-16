"""Diagnose the isolated two-arm result: did the message arm really raise risk, and why?

The first run gave risk_mean 0.00145 (opn=0) vs 0.108 (opn=1) — a 74x INCREASE, the
opposite of the intended direction. Before reporting that as a finding it must be shown
not to be an artifact.

Candidate explanations to separate:
  A. Composition artifact: the arm with more vehicles in the region accumulates more risk
     simply because more pairs are measurable.
  B. Timing artifact: the difference is concentrated before the event (i.e. the two arms
     diverged for a reason unrelated to the message).
  C. Real mechanism: the policy caps speed, vehicles decelerate, and their followers close
     in, so local TTC risk rises even though the intended effect was mitigation.

Usage:
  python code/scripts/diagnose_isolated_two_arm.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "code/outputs/analysis/stage1_isolated_20261116"
STEP = 0.05
TGT_REGION = (3000.0, 4000.0)


def load(arm: str):
    s = json.loads((OUT / "arms_series.json").read_text(encoding="utf-8"))
    return s[f"20261116_{arm}"]


def in_region_counts(series: dict) -> np.ndarray:
    n = len(next(iter(series.values()))["x"])
    out = np.zeros(n)
    for k in range(n):
        out[k] = sum(1 for v in series
                     if series[v]["x"][k] is not None
                     and TGT_REGION[0] <= series[v]["x"][k] < TGT_REGION[1])
    return out


def speeds_in_region(series: dict) -> np.ndarray:
    n = len(next(iter(series.values()))["v"])
    out = np.full(n, np.nan)
    for k in range(n):
        vals = [series[v]["v"][k] for v in series
                if series[v]["x"][k] is not None
                and TGT_REGION[0] <= series[v]["x"][k] < TGT_REGION[1]
                and series[v]["v"][k] is not None]
        if vals:
            out[k] = float(np.mean(vals))
    return out


def main() -> int:
    a0, a1 = load("opn0"), load("opn1")
    c0, c1 = in_region_counts(a0), in_region_counts(a1)
    v0, v1 = speeds_in_region(a0), speeds_in_region(a1)
    t = np.arange(len(c0)) * STEP

    print(f"{'t':>7}{'区内车(opn0)':>13}{'区内车(opn1)':>13}{'均速0':>9}{'均速1':>9}")
    print("-" * 54)
    for k in range(0, len(t), 40):
        print(f"{t[k]:>7.1f}{int(c0[k]):>13}{int(c1[k]):>13}"
              f"{v0[k]:>9.2f}{v1[k]:>9.2f}")

    print(f"\n区内车数  全程均值  opn0={c0.mean():.1f}  opn1={c1.mean():.1f}")
    print(f"区内均速  全程均值  opn0={np.nanmean(v0):.2f}  opn1={np.nanmean(v1):.2f}")
    pre = t < 12.2
    post = t >= 12.2
    print(f"\n事件前（t<12.2s）区内车数  opn0={c0[pre].mean():.1f}  opn1={c1[pre].mean():.1f}")
    print(f"事件前（t<12.2s）区内均速  opn0={np.nanmean(v0[pre]):.2f}  opn1={np.nanmean(v1[pre]):.2f}")
    print(f"事件后（t>=12.2s）区内车数 opn0={c0[post].mean():.1f}  opn1={c1[post].mean():.1f}")
    print(f"事件后（t>=12.2s）区内均速 opn0={np.nanmean(v0[post]):.2f}  opn1={np.nanmean(v1[post]):.2f}")

    # A: is the vehicle population identical between arms?
    same_pop = bool(np.array_equal(c0, c1))
    print(f"\n[A] 两臂区内车数逐帧完全相同: {same_pop}")
    if not same_pop:
        diff = np.abs(c0 - c1)
        print(f"    最大差 {diff.max():.0f} 辆，出现在 t={t[diff.argmax()]:.1f}s")

    # B: speed divergence before the event would indicate a non-message cause
    pre_gap = np.nanmax(np.abs(v0[pre] - v1[pre])) if pre.any() else 0.0
    post_gap = np.nanmax(np.abs(v0[post] - v1[post])) if post.any() else 0.0
    print(f"[B] 事件前两臂均速最大差 {pre_gap:.4f} m/s")
    print(f"    事件后两臂均速最大差 {post_gap:.4f} m/s")

    verdict = []
    if same_pop:
        verdict.append("A 排除：两臂车辆构成逐帧一致，风险差不是由分母不同造成的")
    else:
        verdict.append("A 不排除：两臂车辆构成不同，风险差可能部分来自分母")
    if pre_gap > 0.05:
        verdict.append("B 不排除：事件前两臂已分叉，需查是否有非消息原因")
    else:
        verdict.append("B 排除：事件前两臂完全一致，分叉只发生在事件之后")
    print("\n判读：")
    for v in verdict:
        print("  -", v)

    res = {
        "in_region_opn0_mean": float(c0.mean()), "in_region_opn1_mean": float(c1.mean()),
        "speed_opn0_mean": float(np.nanmean(v0)), "speed_opn1_mean": float(np.nanmean(v1)),
        "pre_event_speed_max_diff": float(pre_gap), "post_event_speed_max_diff": float(post_gap),
        "identical_population": same_pop, "verdict": verdict,
    }
    (OUT / "diagnosis.json").write_text(json.dumps(res, indent=2, ensure_ascii=False),
                                        encoding="utf-8")
    print(f"\nwrote {OUT/'diagnosis.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())