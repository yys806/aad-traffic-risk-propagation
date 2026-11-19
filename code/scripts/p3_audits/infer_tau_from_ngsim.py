"""从 NGSIM 实测反推 Krauss 的 tau 在各速度带的等价取值

阶段：P3（场景改造决策支持）
脚本：code/scripts/p3_audits/infer_tau_from_ngsim.py
产物：code/outputs/analysis/P3_scenario_check/tau_inference.json

原理：
  Krauss 模型在稳态跟驰时，车头到车头间距 ≈ v·tau + 车长 + 最小净距。
  两边同除 v，得到稳态时间车头距
        THW ≈ tau + (车长 + 最小净距) / v
  因此可以从实测 THW 反推每个速度带「等价于多大的 tau」：
        tau_equiv = THW_observed − (车长 + 最小净距) / v
  这是**等价换算**，不是标定出真 tau；只用来判断「某个 tau 在哪个工况下才不荒唐」。

口径：THW 用车头到车头（与 NGSIM 官方 Time_Headway 一致）；车长 5 m、最小净距 2.5 m。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

POOL = Path("code/outputs/analysis/P3_scenario_check/ngsim_pool.npz")
VEH = 5.0
MINGAP = 2.5
FIXED = VEH + MINGAP          # 7.5 m

BANDS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 105)]


def main() -> int:
    d = np.load(POOL)
    thw = d["thw"].astype(float)
    spd = d["spd_mps"].astype(float)
    v_kmh = spd * 3.6

    out = {"note": "tau_equiv = THW − (车长+最小净距)/v；用于判断 tau 在哪个工况下不荒唐",
           "fixed_distance_m": FIXED, "bands": []}

    print(f"固定距离项 = 车长 {VEH} + 最小净距 {MINGAP} = {FIXED} m\n")
    print(f"{'速度带':>14} {'n':>7} {'v中位':>8} {'THW p25':>8} {'THW p50':>8} "
          f"{'THW p90':>8} {'τ等价(p25)':>11} {'τ等价(p50)':>11}")
    print("-" * 88)

    for lo, hi in BANDS:
        m = (v_kmh >= lo) & (v_kmh < hi)
        if m.sum() < 200:
            continue
        t = thw[m]
        v = spd[m]
        vm = float(np.median(v))
        p25, p50, p90 = (float(np.percentile(t, q)) for q in (25, 50, 90))
        fix = FIXED / vm
        row = {
            "band_kmh": f"{lo}–{hi}",
            "n": int(m.sum()),
            "v_median_mps": round(vm, 2),
            "v_median_kmh": round(vm * 3.6, 1),
            "thw_p25": round(p25, 2), "thw_p50": round(p50, 2), "thw_p90": round(p90, 2),
            "fixed_term_s": round(fix, 2),
            "tau_equiv_p25": round(p25 - fix, 2),
            "tau_equiv_p50": round(p50 - fix, 2),
            "tau_equiv_p90": round(p90 - fix, 2),
        }
        out["bands"].append(row)
        print(f"{row['band_kmh']:>14} {row['n']:>7} {row['v_median_kmh']:>7.1f} "
              f"{p25:>8.2f} {p50:>8.2f} {p90:>8.2f} "
              f"{row['tau_equiv_p25']:>11.2f} {row['tau_equiv_p50']:>11.2f}")

    print("\n参照：我们现在用的 tau = 0.60 s，跑在 82 km/h（≈22.8 m/s）")
    m = (v_kmh >= 80) & (v_kmh < 105)
    fix80 = FIXED / float(np.median(spd[m]))
    print(f"  80–105 层：固定距离项 {fix80:.2f} s，tau=0.6 对应的 THW = {0.6 + fix80:.2f} s")
    print(f"  实测 p50 THW = {float(np.percentile(thw[m], 50)):.2f} s")

    dst = Path("code/outputs/analysis/P3_scenario_check")
    (dst / "tau_inference.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {dst / 'tau_inference.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())