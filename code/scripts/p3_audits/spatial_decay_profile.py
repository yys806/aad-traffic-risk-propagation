"""P3 准入收口：风险暴露沿上游的空间衰减（第 1 试 stop 臂）

阶段：P3 ｜ 数据：code/outputs/analysis/P3_stop_queue_stop/arms.npz
脚本：code/scripts/p3_audits/spatial_decay_profile.py
产物：code/outputs/analysis/P3_spatial_decay/profile.json + profile.csv

回答一个问题：源车急停后，短 TTC 风险暴露到底出现在哪里、往上游衰减多快？
这是「回堵传到了、风险暴露没传到」的直接证据。
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
GAP_EPS = 0.5
STEP_S = 0.05
SOURCE_X = 6000.0
BIN = 250.0            # 空间分档宽度（米）
X_MAX = 6500.0


def profile(arm: str, d) -> list[dict]:
    pos = d[f"{arm}_pos"]
    spd = d[f"{arm}_spd"]
    t0 = float(d["event_t0"])
    k0 = int(round(t0 / STEP_S))
    n_steps = pos.shape[0]
    nbins = int(np.ceil(X_MAX / BIN))
    ttc_min = np.full(nbins, np.inf)
    d_max = np.zeros(nbins)
    ttc_lt2 = np.zeros(nbins)      # 车·秒
    d_gt2 = np.zeros(nbins)
    veh_s = np.zeros(nbins)
    gap_min = np.full(nbins, np.inf)
    dv_max = np.zeros(nbins)

    for k in range(k0, n_steps):
        x_all = pos[k].astype(np.float64)
        v_all = spd[k].astype(np.float64)
        ok = np.isfinite(x_all) & np.isfinite(v_all)
        if ok.sum() < 2:
            continue
        x = x_all[ok]
        v = v_all[ok]
        o = np.argsort(x)
        x, v = x[o], v[o]
        g = (x[1:] - x[:-1]) - VEH_LEN
        dv = v[:-1] - v[1:]
        rear_x = x[:-1]
        b = np.floor(rear_x / BIN).astype(int)
        inb = (b >= 0) & (b < nbins)
        # 车·秒（按后车所在档计）
        np.add.at(veh_s, b[inb], STEP_S)
        keep = (dv > 0) & (g > GAP_EPS) & inb
        if keep.any():
            ttc = g[keep] / dv[keep]
            dreq = dv[keep] ** 2 / (2.0 * g[keep])
            bb = b[keep]
            for j in range(bb.size):
                i = bb[j]
                if ttc[j] < ttc_min[i]:
                    ttc_min[i] = ttc[j]
                if dreq[j] > d_max[i]:
                    d_max[i] = dreq[j]
                if dv[j] > dv_max[i]:
                    dv_max[i] = dv[j]
                if g[j] < gap_min[i]:
                    gap_min[i] = g[j]
            np.add.at(ttc_lt2, bb, (ttc < 2.0) * STEP_S)
            np.add.at(d_gt2, bb, (dreq > 2.0) * STEP_S)

    rows = []
    for i in range(nbins):
        lo = i * BIN
        rows.append({
            "x_lo_m": round(lo, 0),
            "x_hi_m": round(lo + BIN, 0),
            "dist_to_source_m": round(SOURCE_X - lo, 0),
            "veh_seconds": round(float(veh_s[i]), 1),
            "ttc_min_s": None if not np.isfinite(ttc_min[i]) else round(float(ttc_min[i]), 2),
            "ttc_lt2_veh_s": round(float(ttc_lt2[i]), 2),
            "d_max_mps2": round(float(d_max[i]), 3),
            "d_gt2_veh_s": round(float(d_gt2[i]), 2),
            "dv_max_mps": round(float(dv_max[i]), 2),
            "gap_min_m": None if not np.isfinite(gap_min[i]) else round(float(gap_min[i]), 2),
        })
    return rows


def main() -> int:
    src = Path("code/outputs/analysis/P3_stop_queue_stop/arms.npz")
    d = np.load(src)
    out = {"source": str(src), "bin_m": BIN, "source_x": SOURCE_X,
           "note": "只统计后车落在该档、且存在闭合（dv>0、g>0.5）的帧；车·秒按后车位置归类"}
    for arm in ("stop", "plain"):
        out[arm] = profile(arm, d)

    dst = Path("code/outputs/analysis/P3_spatial_decay")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "profile.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    with (dst / "profile.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arm", "x_lo_m", "x_hi_m", "dist_to_source_m", "veh_seconds",
                    "ttc_min_s", "ttc_lt2_veh_s", "d_max_mps2", "d_gt2_veh_s",
                    "dv_max_mps", "gap_min_m"])
        for arm in ("stop", "plain"):
            for r in out[arm]:
                w.writerow([arm, r["x_lo_m"], r["x_hi_m"], r["dist_to_source_m"],
                            r["veh_seconds"], r["ttc_min_s"], r["ttc_lt2_veh_s"],
                            r["d_max_mps2"], r["d_gt2_veh_s"], r["dv_max_mps"],
                            r["gap_min_m"]])

    for arm in ("stop", "plain"):
        print(f"\n=== {arm} 臂：风险暴露沿上游的空间分布（250 m 一档）===")
        print(f"{'x 区间(m)':>16} {'距源(m)':>8} {'车·秒':>8} {'TTC最小':>8} "
              f"{'TTC<2车·秒':>10} {'D最大':>7} {'dv最大':>7}")
        for r in reversed(out[arm]):
            if r["veh_seconds"] <= 0:
                continue
            print(f"{r['x_lo_m']:7.0f}-{r['x_hi_m']:6.0f} {r['dist_to_source_m']:8.0f} "
                  f"{r['veh_seconds']:8.1f} {str(r['ttc_min_s']):>8} {r['ttc_lt2_veh_s']:10.2f} "
                  f"{r['d_max_mps2']:7.2f} {r['dv_max_mps']:7.2f}")
    print(f"\nwritten: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
