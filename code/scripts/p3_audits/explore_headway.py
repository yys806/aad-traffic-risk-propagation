"""路线 A 指标探索：时间头距对「源事件造成的物理影响」敏感吗

阶段：P3（探索）｜ 数据：P2_batch_v2/hw20_strong_* ｜ 脚本：cache/explore_headway.py

注意这只验证**指标灵敏度**，不证明消息效果——P2 里没有消息臂。
比较的是「有源事件、无响应」与「无事件」，也就是源事件本身会不会让目标区的车头时距变化。

时间头距 h = 净距 / 本车速度。车速趋零时会发散，这里先用两种口径各算一遍：
  h1 = gap / max(v, 2.0)            低速截断
  h2 = gap                      纯间距（不发散，作对照）
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

BASE = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P2_batch_v2")
CELL = "hw20_strong_s20261119"
VEH_LEN = 5.0
TARGET = (4000.0, "2.0 km")          # P3 主站
BAND = 50.0

z = np.load(BASE / CELL / "arms.npz", allow_pickle=True)
step = float(z["step_s"])
t0 = float(z["event_t0"])
k0 = int(round(t0 / step))

SEGMENTS = ((8.0, 25.0, "早子窗 8-25"), (25.0, 50.0, "晚子窗 25-50"),
            (8.0, 50.0, "整窗 8-50"), (50.0, 150.0, "到达后 50-150"))


def headway_stats(POS, SPD, a: float, b: float):
    k1 = k0 + int(round(a / step))
    k2 = min(k0 + int(round(b / step)), POS.shape[0])
    hs1, hs2, sp, gp = [], [], [], []
    for k in range(k1, k2):
        row_p, row_v = POS[k], SPD[k]
        idx = np.where(np.isfinite(row_p) & (row_p >= TARGET[0] - BAND)
                       & (row_p <= TARGET[0] + BAND))[0]
        if len(idx) < 2:
            continue
        order = idx[np.argsort(row_p[idx])]
        for x_, y_ in zip(order[:-1], order[1:]):
            gap = row_p[y_] - row_p[x_] - VEH_LEN
            v = row_v[x_]
            if gap <= 0.1 or not np.isfinite(v):
                continue
            hs1.append(gap / max(v, 2.0))
            hs2.append(gap)
            sp.append(v)
            gp.append(gap)
    if not hs1:
        return None
    return (float(np.mean(hs1)), float(np.mean(hs2)),
            float(np.mean(sp)), float(np.mean(gp)), len(hs1))


print(f"cell = {CELL}   目标区 x∈[{TARGET[0]-BAND:.0f}, {TARGET[0]+BAND:.0f}] ({TARGET[1]})")
print(f"{'段':<14} {'臂':<6} {'h=gap/max(v,2)':>15} {'纯间距':>9} {'均速':>7} {'样本':>7}")
print("-" * 68)
for a, b, name in SEGMENTS:
    for arm in ("plain", "event"):
        POS, SPD = z[f"{arm}_pos"], z[f"{arm}_spd"]
        r = headway_stats(POS, SPD, a, b)
        if r is None:
            print(f"{name:<14} {arm:<6} {'无车对':>15}")
            continue
        h1, h2, mv, mg, n = r
        print(f"{name:<14} {arm:<6} {h1:>15.3f} {h2:>9.2f} {mv:>7.2f} {n:>7d}")
    print()

print("判读：")
print("  若 event 的 h 明显大于 plain，说明源事件确实改变了目标区的车头时距 → 指标有灵敏度")
print("  若两臂几乎相同，说明这个指标在目标区测不到东西，A 路线也要重新考虑")
print("  注意 plain 臂在早期是均匀流（h≈15/20.83≈0.72 s），任何偏离都来自事件")
