"""抽帧手算：TTC 与所需减速度 D 的口径核对（P3 场景准入前置）

阶段：P3 ｜ 数据：code/outputs/analysis/P2_batch_v2/hw20_strong_s20261119/arms.npz
脚本：code/scripts/p3_audits/handcheck_ttc_d.py
产物：code/outputs/analysis/P3_audit_handcheck/handcheck_hw20_strong_s20261119.json

目的（不是实验，是口径核对）：
1. 确认 P3 准入门槛里的 TTC 与 D 能从现有轨迹算出来；
2. 确认「净距」用的是保险杠净距（位置差 − 车长），不是中心距；
3. 确认旧 P2 冻结场景在随机抽样帧下确实没有 TTC<2 s / D>2 的暴露。

注意：npz 没有保存 leader 索引，这里按位置排序自算前车（同车道、位置递增方向为车流方向）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

VEH_LEN = 5.0          # SUMO vType length
STEP_S = 0.05
# 抽样时刻（相对 event_t0，秒）
OFFSETS_S = [10.0, 30.0, 52.0, 80.0, 127.0, 160.0, 200.0, 300.0, 400.0, 600.0]


def pairs_at(pos_row: np.ndarray, spd_row: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """按位置排序，返回相邻车的 (净距 g, 闭合速度 dv>0)。"""
    ok = np.isfinite(pos_row) & np.isfinite(spd_row)
    x = pos_row[ok].astype(np.float64)
    v = spd_row[ok].astype(np.float64)
    if x.size < 2:
        return np.empty(0), np.empty(0)
    order = np.argsort(x)          # 位置小 -> 大；大的在前方
    x = x[order]
    v = v[order]
    g = (x[1:] - x[:-1]) - VEH_LEN  # 后车 i 的净距 = 前车位置 − 本车位置 − 车长
    dv = v[:-1] - v[1:]             # 后车速度 − 前车速度
    closing = dv > 0
    return g[closing], dv[closing]


def summarize(g: np.ndarray, dv: np.ndarray) -> dict:
    if g.size == 0:
        return {"n_pairs": 0}
    ttc = g / dv
    dreq = dv**2 / (2.0 * g)
    return {
        "n_pairs": int(g.size),
        "g_min": float(g.min()),
        "dv_max": float(dv.max()),
        "ttc_min": float(ttc.min()),
        "ttc_lt2_pairs": int((ttc < 2.0).sum()),
        "ttc_lt2_share": float((ttc < 2.0).mean()),
        "d_max": float(dreq.max()),
        "d_gt2_pairs": int((dreq > 2.0).sum()),
        "d_gt2_share": float((dreq > 2.0).mean()),
        "neg_g_pairs": int((g <= 0).sum()),
    }


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else
               "code/outputs/analysis/P2_batch_v2/hw20_strong_s20261119/arms.npz")
    tag = src.parent.name
    d = np.load(src)
    t0 = float(d["event_t0"])
    step = float(d["step_s"])
    out = {"source": str(src), "event_t0": t0, "step_s": step,
           "veh_len": VEH_LEN, "frames": {}}

    for arm in ("event", "plain"):
        pos = d[f"{arm}_pos"]
        spd = d[f"{arm}_spd"]
        per = []
        for off in OFFSETS_S:
            k = int(round((t0 + off) / step))
            if k >= pos.shape[0]:
                continue
            g, dv = pairs_at(pos[k], spd[k])
            rec = {"offset_s": off, **summarize(g, dv)}
            per.append(rec)
        out["frames"][arm] = per

    dst = Path("code/outputs/analysis/P3_audit_handcheck")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / f"handcheck_{tag}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"source: {tag}  event_t0={t0:.2f}s  step={step}s")
    print(f"{'arm':6} {'t-t0':>6} {'pairs':>6} {'g_min':>7} {'dv_max':>7} "
          f"{'TTC_min':>8} {'TTC<2':>6} {'D_max':>7} {'D>2':>5} {'g<=0':>5}")
    for arm in ("event", "plain"):
        for r in out["frames"][arm]:
            if r["n_pairs"] == 0:
                print(f"{arm:6} {r['offset_s']:6.0f} {0:6d}  (no closing pair)")
                continue
            print(f"{arm:6} {r['offset_s']:6.0f} {r['n_pairs']:6d} {r['g_min']:7.2f} "
                  f"{r['dv_max']:7.2f} {r['ttc_min']:8.2f} {r['ttc_lt2_pairs']:6d} "
                  f"{r['d_max']:7.2f} {r['d_gt2_pairs']:5d} {r['neg_g_pairs']:5d}")
    print(f"\nwritten: {dst / f'handcheck_{tag}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
