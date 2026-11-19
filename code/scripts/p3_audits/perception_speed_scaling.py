"""临界感知距离随速度的标度：验证 DRAC 曲线是物理规律而非巧合

阶段：P3 ｜ 正对照的推广（为 GPT 第四十二轮 Q1/Q2 的准备）
脚本：code/scripts/p3_audits/perception_speed_scaling.py
产物：code/outputs/analysis/P3_controls/perception_scaling.json

要验证的预测：
  若 DRAC = v²/(2d) 成立，则「临界感知距离」应满足 d_crit = v²/(2·3.4)，
  即**随速度平方增长**。速度翻倍，临界距离应约为四倍。

如果实测各速度下 d_crit 与 v² 的比值保持常数，
说明这不是某一次实验的巧合，而是可以写进论文的物理标度关系。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import positive_control_perception as P  # noqa: E402

DRAC_MAIN = 3.4


def find_critical(v0: float, lo: float = 20.0, hi: float = 400.0,
                  tol: float = 2.0) -> dict:
    """二分找 DRAC 峰值恰好等于阈值的感知距离。"""
    cache: dict[float, dict] = {}

    def probe(R: float) -> dict:
        R = round(R, 1)
        if R not in cache:
            cache[R] = P.run_one(R, v0)
        return cache[R]

    a, b = lo, hi
    # 先确认两端行为符合预期
    ra, rb = probe(a), probe(b)
    if not ra["exceeds_main"] or rb["exceeds_main"]:
        return {"v0_mps": v0, "error": "端点行为不符合预期",
                "at_lo": ra, "at_hi": rb}
    while b - a > tol:
        m = (a + b) / 2
        if probe(m)["exceeds_main"]:
            a = m
        else:
            b = m
    mid = round((a + b) / 2, 1)
    r = probe(mid)
    return {"v0_mps": v0, "v0_kmh": round(v0 * 3.6, 1),
            "d_crit_m": mid, "drac_at_crit": r["drac_max_mps2"],
            "analytic_m": round(v0 * v0 / (2 * DRAC_MAIN), 1),
            "ratio_measured_over_analytic": round(mid / (v0 * v0 / (2 * DRAC_MAIN)), 3)}


def main() -> int:
    speeds = [15.0, 20.0, 23.6, 27.0, 30.0]
    out = {"drac_threshold": DRAC_MAIN, "results": []}
    print(f"{'速度 km/h':>10} {'实测临界距离':>12} {'解析 v²/(2·3.4)':>16} {'比值':>7}")
    print("-" * 52)
    for v in speeds:
        r = find_critical(v)
        out["results"].append(r)
        if "error" in r:
            print(f"{v*3.6:>10.1f}  {r['error']}")
            continue
        print(f"{r['v0_kmh']:>10.1f} {r['d_crit_m']:>12.1f} "
              f"{r['analytic_m']:>16.1f} {r['ratio_measured_over_analytic']:>7.3f}")

    ok = [r for r in out["results"] if "error" not in r]
    if ok:
        ratios = [r["ratio_measured_over_analytic"] for r in ok]
        out["ratio_mean"] = round(sum(ratios) / len(ratios), 3)
        out["ratio_spread"] = round(max(ratios) - min(ratios), 3)
        print(f"\n实测/解析 比值：均值 {out['ratio_mean']}，"
              f"极差 {out['ratio_spread']}")
        print("若比值在各速度下稳定，则「临界感知距离 ∝ 速度²」成立")

    dst = Path("code/outputs/analysis/P3_controls")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "perception_scaling.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written: {dst / 'perception_scaling.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())