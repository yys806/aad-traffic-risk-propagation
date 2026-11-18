"""路线 A 第一步：早窗校准——目标区那批车自己什么时候开始感到扰动

阶段：P3（校准）｜ 数据：P2_batch_v2/hw20_strong_* ｜ 脚本：cache/calibrate_early_window.py

GPT 的要点：26.6 s 是固定在 x=4000 测站的读数，不是这批车的遭遇时间。
起初在 x=4000、以 20.83 m/s 行驶的车，25 s 内会向源驶近约 521 m，更早感到扰动。
所以早窗必须按「同一批车辆 ID」校准，不能直接沿用测站读数。

做法：
1. t0 前最后一帧、按目标区边界锁定车辆 ID；
2. 两臂按 ID 对齐，跟踪这批车的速度；
3. 找最早出现可检测偏离（0.05 / 0.1 / 0.5 m/s）的时刻；
4. 同时报告这批车净距的最早偏离（辅助，受前车身份变化影响）。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

BASE = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P2_batch_v2")
CELL = "hw20_strong_s20261119"
TARGET_X = 4000.0
BAND = 50.0
VEH_LEN = 5.0
THRESHOLDS = (0.05, 0.1, 0.5)

z = np.load(BASE / CELL / "arms.npz", allow_pickle=True)
step = float(z["step_s"])
t0 = float(z["event_t0"])
k0 = int(round(t0 / step))

plain_ids = np.array([str(s) for s in z["plain_ids"]])
event_ids = np.array([str(s) for s in z["event_ids"]])
PP, PS = z["plain_pos"], z["plain_spd"]
EP, ES = z["event_pos"], z["event_spd"]

# --- 1. 用 plain 臂 t0-1 帧锁定目标区车辆 ---
lock_p = PP[k0 - 1]
in_tgt = np.where(np.isfinite(lock_p) & (lock_p >= TARGET_X - BAND) & (lock_p <= TARGET_X + BAND))[0]
locked = plain_ids[in_tgt]
print(f"t0={t0:.0f}s 锁定目标区车辆 {len(locked)} 辆（x∈[{TARGET_X-BAND:.0f},{TARGET_X+BAND:.0f}]）")

# --- 2. 两臂交集 ---
common = np.array([v for v in locked if v in set(event_ids.tolist())])
print(f"两臂共有的锁定车 {len(common)} 辆")

ip = {v: i for i, v in enumerate(plain_ids)}
ie = {v: i for i, v in enumerate(event_ids)}
rp = np.array([ip[v] for v in common])
re = np.array([ie[v] for v in common])

# --- 3. 一致性检查：t0 帧两臂是否相同 ---
d0 = np.nanmax(np.abs(PP[k0 - 1, rp] - EP[k0 - 1, re])) if len(common) else np.nan
print(f"t0 帧位置最大差 {d0:.6f} m（应≈0）")

# --- 4. 跟踪速度偏离 ---
vp = PS[k0:, rp]      # (T, N)
ve = ES[k0:, re]
dv = np.abs(vp - ve)  # 逐车逐时刻速度差
tt = np.arange(dv.shape[0]) * step

print(f"\n跟踪 {dv.shape[0]} 帧 × {dv.shape[1]} 车，时刻为 t0 之后（秒）")
print(f"{'阈值(m/s)':>10} {'最早偏离':>10} {'该时刻偏离车数':>14} {'累计≥10%车':>12}")
print("-" * 52)
for thr in THRESHOLDS:
    mask = dv >= thr
    any_hit = mask.any(axis=1)
    if not any_hit.any():
        print(f"{thr:>10.2f} {'none':>10}")
        continue
    k = int(np.argmax(any_hit))
    n_hit = int(mask[k].sum())
    # 首次达到 ≥10% 车偏离的时刻
    frac = mask.mean(axis=1)
    k10 = np.where(frac >= 0.10)[0]
    k10s = f"{k10[0]*step:.1f}" if len(k10) else "none"
    print(f"{thr:>10.2f} {k*step:>10.1f} {n_hit:>14d} {k10s:>12}")

# --- 5. 这批车自身位置分布（关键：它们会驶向源） ---
print(f"\n锁定车在 t0 时刻的位置中位数 {np.nanmedian(PP[k0-1, rp]):.0f} m")
for t in (10, 20, 25, 40, 50):
    k = int(round(t / step))
    if k >= PP.shape[0] - k0:
        break
    pm = np.nanmedian(PP[k0 + k, rp])
    print(f"  t0+{t:>2}s 位置中位数 {pm:.0f} m，已向源驶近 {np.nanmedian(PP[k0-1, rp]) - pm:.0f} m")

print("\n判读：若最早偏离明显早于 25 s，早窗上限要按这个结果收紧；")
print("      若在 25 s 内都没偏离，说明这批车在早窗里是干净的，[8,25] 可用。")
