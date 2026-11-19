"""验收异质场景：看热身之后**实际跑出来**的速度与车头距分布

阶段：P3 ｜ GPT 第三十九轮 Q6 第 3 步要求
脚本：code/scripts/p3_audits/audit_hetero_scene.py
产物：code/outputs/analysis/P3_hetero_audit.json

为什么看实跑而不看输入：
  GPT 原话——「最终验收看事件触发前实际跑出来的速度与 THW 联合分布，
  而不是输入参数是否写在 80–100 之间」。输入抽对了不代表跑起来还对。

口径：
  * 只在观测窗内（warmup 之后）、只在目标区附近 x ∈ [3500, 6500] 取样
  * THW = (前车位置 − 本车位置) / 本车速度，**车头到车头**口径
  * 只统计本车速度 > 15 m/s 的跟驰对
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
REGION = (3500.0, 6500.0)
V_MIN = 15.0
POOL = Path("code/outputs/analysis/P3_scenario_check/ngsim_pool.npz")


def realized(arm: Path) -> dict:
    d = np.load(arm / "arms.npz")
    pos, spd = d["plain_pos"], d["plain_spd"]
    warm = int(round(float(d["warmup_s"]) / float(d["step_s"])))
    step = float(d["step_s"])
    # 每 1 s 取一帧，避免相邻帧高度相关
    every = max(1, int(round(1.0 / step)))
    thw, vs = [], []
    for k in range(warm, pos.shape[0], every):
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v) & (x >= REGION[0]) & (x <= REGION[1])
        idx = np.where(ok)[0]
        if idx.size < 2:
            continue
        idx = idx[np.argsort(x[idx])]
        for a, b in zip(idx[:-1], idx[1:]):
            gap = (x[b] - x[a]) - VEH_LEN
            if gap <= 0.5 or v[a] < V_MIN:
                continue
            thw.append((x[b] - x[a]) / v[a])
            vs.append(v[a])
    if not thw:
        return {"error": "区域内无有效跟驰对"}
    t = np.array(thw)
    v = np.array(vs) * 3.6
    return {
        "n_pairs": int(t.size),
        "speed_kmh": {"p10": round(float(np.percentile(v, 10)), 1),
                      "p50": round(float(np.percentile(v, 50)), 1),
                      "p90": round(float(np.percentile(v, 90)), 1),
                      "std": round(float(np.std(v)), 2)},
        "thw_s": {"p10": round(float(np.percentile(t, 10)), 2),
                  "p25": round(float(np.percentile(t, 25)), 2),
                  "p50": round(float(np.percentile(t, 50)), 2),
                  "p75": round(float(np.percentile(t, 75)), 2),
                  "p90": round(float(np.percentile(t, 90)), 2),
                  "std": round(float(np.std(t)), 3)},
    }


def reference() -> dict:
    d = np.load(POOL)
    thw, spd = d["thw"].astype(float), d["spd_mps"].astype(float)
    m = (spd * 3.6 >= 80) & (spd * 3.6 <= 105)
    t, v = thw[m], spd[m] * 3.6
    return {"n_pairs": int(t.size),
            "speed_kmh": {"p10": round(float(np.percentile(v, 10)), 1),
                          "p50": round(float(np.percentile(v, 50)), 1),
                          "p90": round(float(np.percentile(v, 90)), 1),
                          "std": round(float(np.std(v)), 2)},
            "thw_s": {"p10": round(float(np.percentile(t, 10)), 2),
                      "p25": round(float(np.percentile(t, 25)), 2),
                      "p50": round(float(np.percentile(t, 50)), 2),
                      "p75": round(float(np.percentile(t, 75)), 2),
                      "p90": round(float(np.percentile(t, 90)), 2),
                      "std": round(float(np.std(t)), 3)}}


def main() -> int:
    root = Path("code/outputs/analysis")
    arms = sorted(root.glob("P3_hetero_2*/arms.npz"))
    if not arms:
        raise SystemExit("没找到任何 P3_hetero_* 产物")
    out = {"reference_ngsim_80_105": reference(), "scenes": []}
    print("NGSIM 80–105 km/h 参考：")
    r = out["reference_ngsim_80_105"]
    print(f"  速度 p10/p50/p90 = {r['speed_kmh']['p10']}/{r['speed_kmh']['p50']}/{r['speed_kmh']['p90']} km/h")
    print(f"  THW  p25/p50/p90 = {r['thw_s']['p25']}/{r['thw_s']['p50']}/{r['thw_s']['p90']} s\n")
    for a in arms:
        res = realized(a.parent)
        res["scene"] = a.parent.name
        out["scenes"].append(res)
        if "error" in res:
            print(f"{a.parent.name}: {res['error']}")
            continue
        s, t = res["speed_kmh"], res["thw_s"]
        print(f"{a.parent.name}:  {res['n_pairs']} 对")
        print(f"  速度 p10/p50/p90 = {s['p10']}/{s['p50']}/{s['p90']} km/h （std {s['std']}）")
        print(f"  THW  p25/p50/p90 = {t['p25']}/{t['p50']}/{t['p90']} s （std {t['std']}）")
    (root / "P3_hetero_audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {root / 'P3_hetero_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())