"""P3 前置：前兆审计——目标区在 t0 之后最早什么时候出现可分辨的物理影响

阶段：P3（前置）｜ 数据：P2_batch_v2/hw20_strong_* ｜ 脚本：cache/audit_precursor.py

GPT 的 P3 方案要求：所有策略共用一个固定前置窗 W=[t0+8, t0+40] s。
这个窗能不能用，取决于「目标区最早可分辨的物理前兆」是不是真的晚于 40 s。
如果 20 s 就已经有可分辨差异，那 8–40 s 里有 20 秒是被物理影响的，前置窗就不成立。

判据：固定空间窗里的平均车速差，逐档阈值看首次出现时刻。
因为 sigma=0，两臂在事件前完全一致，所以任何非零差异都是真实的（不是随机噪声）；
门槛只反映「多小的差异我们认为可分辨」。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

BASE = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P2_batch_v2")
CELLS = ("hw20_strong_s20261119", "hw20_strong_s20261120")
STATIONS = ((5500.0, "0.5 km"), (5000.0, "1.0 km"), (4500.0, "1.5 km"), (4000.0, "2.0 km"))
BAND = 50.0
WIN_S = 2.0
THRESHOLDS = (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)


def local_speed(pos, step, lo, hi):
    inb = np.isfinite(pos) & (pos >= lo) & (pos <= hi)
    d = np.diff(pos, axis=0, prepend=np.nan)
    d = np.where(np.isfinite(d) & inb, d, 0.0)
    s_step = inb.sum(axis=1).astype(float) * step
    l_step = d.sum(axis=1)
    n = int(round(WIN_S / step))
    cs_s = np.concatenate([[0.0], np.cumsum(s_step)])
    cs_l = np.concatenate([[0.0], np.cumsum(l_step)])
    idx = np.arange(len(s_step)) + 1
    lo_i = np.maximum(0, idx - n)
    S = cs_s[idx] - cs_s[lo_i]
    L = cs_l[idx] - cs_l[lo_i]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(S > 0, L / S, np.nan), S


for cell in CELLS:
    f = BASE / cell / "arms.npz"
    if not f.exists():
        continue
    z = np.load(f, allow_pickle=True)
    step = float(z["step_s"])
    t0 = float(z["event_t0"])
    k0 = int(round(t0 / step))
    PP, PE = z["plain_pos"], z["event_pos"]
    print(f"\n=== {cell}  (t0={t0:.0f}s, 观测 {(PE.shape[0]-k0)*step:.0f}s) ===")
    print(f"{'站':>8} " + " ".join(f"{t:>7}" for t in THRESHOLDS))
    for xj, name in STATIONS:
        Up, Sp = local_speed(PP[k0:], step, xj - BAND, xj + BAND)
        Ue, Se = local_speed(PE[k0:], step, xj - BAND, xj + BAND)
        ok = (Sp >= 2) & (Se >= 2)
        dv = np.where(ok, Up - Ue, np.nan)
        cells = []
        for thr in THRESHOLDS:
            hit = np.where(np.nan_to_num(dv, nan=-1e9) >= thr)[0]
            cells.append(f"{hit[0]*step:7.1f}" if len(hit) else "   none")
        print(f"{name:>8} " + " ".join(cells))
    print("  （单位：秒，t0 之后；数=该空间窗平均车速差首次达到该阈值）")

print("\n判读：若 0.5 m/s 这一档在 1.0 km 站早于 40 s 出现，则 W=[8,40] 的前置窗不成立。")
