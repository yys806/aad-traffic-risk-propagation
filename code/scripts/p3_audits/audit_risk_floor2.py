"""P3 前置：风险底噪审计（修正版）——分时段、分两臂

阶段：P3（前置）｜ 数据：P2_batch_v2/hw20_strong_* ｜ 脚本：cache/audit_risk_floor2.py

上一版的错误：只看了前置窗 [t0+8, t0+50]，那里风险本来就该是零（波还没到）。
P3 真正要削的是**波到达之后**的风险。所以这一版分三段看两臂：

    A 前置窗      t0+8 … t0+50     动作在这里发生，风险应当接近 0
    B 到达后早段  t0+50 … t0+200    1–2 km 站的波已到，风险应在这里出现
    C 观测后段    t0+200 … t0+690

若 event 臂在 B 段仍然几乎无风险，则这个场景确实没有可削的东西，P3 必须换场景。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

BASE = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P2_batch_v2")
CELL = "hw20_strong_s20261119"
STATIONS = ((5500.0, "0.5 km"), (5000.0, "1.0 km"), (4500.0, "1.5 km"), (4000.0, "2.0 km"))
BAND = 50.0
VEH_LEN = 5.0
D_THR = 2.0
SEGMENTS = ((8.0, 50.0, "A 前置"), (50.0, 200.0, "B 到达后"), (200.0, 690.0, "C 后段"))

z = np.load(BASE / CELL / "arms.npz", allow_pickle=True)
step = float(z["step_s"])
t0 = float(z["event_t0"])
k0 = int(round(t0 / step))
ARMS = (("plain", z["plain_pos"], z["plain_spd"]),
        ("event", z["event_pos"], z["event_spd"]))


def seg_risk(POS, SPD, a: float, b: float):
    k1 = k0 + int(round(a / step))
    k2 = min(k0 + int(round(b / step)), POS.shape[0])
    n_pair = n_d = 0
    dvals = []
    for k in range(k1, k2):
        row_p, row_v = POS[k], SPD[k]
        idx = np.where(np.isfinite(row_p))[0]
        if len(idx) < 2:
            continue
        order = idx[np.argsort(row_p[idx])]
        for x_, y_ in zip(order[:-1], order[1:]):
            gap = row_p[y_] - row_p[x_] - VEH_LEN
            if gap <= 0.1:
                continue
            va, vb = row_v[x_], row_v[y_]
            if not (np.isfinite(va) and np.isfinite(vb)):
                continue
            n_pair += 1
            c = va - vb
            d = (c * c) / (2 * gap) if c > 0 else 0.0
            dvals.append(d)
            if d > D_THR:
                n_d += 1
    if n_pair == 0:
        return None
    return n_pair * step, n_d / n_pair, float(np.percentile(dvals, 95)), float(max(dvals))


print(f"cell = {CELL}  (整条路，不分区)")
print(f"{'段':<12} {'臂':<6} {'车·秒':>8} {'D>2占比':>9} {'D p95':>8} {'D max':>8}")
print("-" * 60)
for a, b, name in SEGMENTS:
    for arm, POS, SPD in ARMS:
        r = seg_risk(POS, SPD, a, b)
        if r is None:
            print(f"{name:<12} {arm:<6} {'no pairs':>8}")
            continue
        vs, frac, p95, mx = r
        print(f"{name:<12} {arm:<6} {vs:>8.0f} {frac:>8.3%} {p95:>8.2f} {mx:>8.2f}")
    print()

print("判读：")
print("  A 段两臂都接近 0 → 正常，波还没到，这正是前置窗的前提")
print("  B 段 event 明显高于 plain → 有风险可削，P3 有空间")
print("  B 段 event 也接近 0 → 这个场景没有可削的风险，P3 必须换场景")
