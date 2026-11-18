"""P3 候选目标区评估：更上游的站，早窗够不够长

阶段：P3（校准）｜ 数据：P2_batch_v2/hw20_strong_* ｜ 脚本：cache/eval_candidate_stations.py

2 km 目标区的早窗只有 8.5 s（16.5 s 就有车开始偏离），装不下一个 3 s 渐入 + 保持的动作。
所以评估更上游的候选：2.5 km、3.0 km、3.5 km。

对每个候选算两件事：
  (1) 测站口径的到达时间（速度场判据，≥5 m/s 连续 3 s）——用于安排观测窗
  (2) 该区锁定车辆的最早可检测偏离（按 ID 跟踪，0.05 / 0.1 / 0.5 m/s）——决定早窗上限
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

BASE = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P2_batch_v2")
CELLS = ("hw20_strong_s20261119", "hw20_strong_s20261120")
CANDIDATES = (2500.0, 3000.0, 3500.0)
BAND = 50.0
WIN_S, THR_DV, HOLD_S = 2.0, 5.0, 3.0
MIN_EXPO = 2.0
EARLY_THR = (0.05, 0.1, 0.5)


def field_arrival(POS, SPD, step, k0, xj):
    lo, hi = xj - BAND, xj + BAND
    inb = np.isfinite(POS) & (POS >= lo) & (POS <= hi)
    v = np.where(inb, SPD, 0.0)
    d = np.diff(POS, axis=0, prepend=np.nan)
    d = np.where(np.isfinite(d) & inb, d, 0.0)
    n = int(round(WIN_S / step))
    S = np.convolve(inb.sum(axis=1) * step, np.ones(n), "full")[: len(inb)]
    L = np.convolve(d.sum(axis=1), np.ones(n), "full")[: len(inb)]
    with np.errstate(invalid="ignore", divide="ignore"):
        U = np.where(S >= MIN_EXPO, L / np.maximum(S, 1e-9), np.nan)
    return U


for xj in CANDIDATES:
    print(f"\n===== 候选目标区 x={xj:.0f} m（离源 {6000-xj:.0f} m）=====")
    for cell in CELLS:
        f = BASE / cell / "arms.npz"
        if not f.exists():
            continue
        z = np.load(f, allow_pickle=True)
        step = float(z["step_s"])
        t0 = float(z["event_t0"])
        k0 = int(round(t0 / step))
        Up = field_arrival(z["plain_pos"], z["plain_spd"], step, k0, xj)[k0:]
        Ue = field_arrival(z["event_pos"], z["event_spd"], step, k0, xj)[k0:]
        dv = Up - Ue
        ok = np.nan_to_num(dv, nan=-1e9) >= THR_DV
        need = int(round(HOLD_S / step))
        arr = None
        run = 0
        for k, h in enumerate(ok):
            run = run + 1 if h else 0
            if run >= need:
                arr = (k - need + 1) * step
                break

        # 锁定车最早偏离
        pid = np.array([str(s) for s in z["plain_ids"]])
        eid = np.array([str(s) for s in z["event_ids"]])
        lp = z["plain_pos"][k0 - 1]
        sel = np.where(np.isfinite(lp) & (lp >= xj - BAND) & (lp <= xj + BAND))[0]
        locked = pid[sel]
        common = [v for v in locked if v in set(eid.tolist())]
        ip = {v: i for i, v in enumerate(pid)}
        ie = {v: i for i, v in enumerate(eid)}
        rp = np.array([ip[v] for v in common])
        re = np.array([ie[v] for v in common])
        dvv = np.abs(z["plain_spd"][k0:, rp] - z["event_spd"][k0:, re])

        earliest = {}
        for thr in EARLY_THR:
            hit = (dvv >= thr).any(axis=1)
            earliest[thr] = f"{np.argmax(hit)*step:.1f}" if hit.any() else "none"

        print(f"  {cell}: 车辆数={len(common):>3}  "
              f"到达(≥5m/s)={arr if arr is not None else 'none':>6}  "
              f"最早偏离 0.05/0.1/0.5 = {earliest[0.05]}/{earliest[0.1]}/{earliest[0.5]} s")

print("\n判读：早窗上限 ≈ 最早偏离(0.05 m/s)。要求窗外留 3 s 渐入 + 保持时间。")
print("      目标区越上游，早窗越长，但波越衰减、效应越小。")
