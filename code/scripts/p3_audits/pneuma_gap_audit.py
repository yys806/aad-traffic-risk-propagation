"""净距口径复核（GPT gpt21 第 5 节第 1 步）

阶段：P3-B（回放验收·口径复核）
要核对：车头/车尾参考点、实测与仿真车长、时间对齐、取最小值的窗口；
重点查 308 的 0.1 m，以及四例最低点是否恰在换前车、切入或窗口边界。
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
EV = [
    ("308", "306", 338.5, 0.1, 4.2),
    ("238", "246", 310.0, 7.7, 4.2),
    ("471", "482", 538.1, 12.5, 4.6),
    ("524", "523", 586.1, 23.2, 12.3),
]
lat0, lon0 = 37.9777, 23.7375
POST = 20.0

want = {a for a, b, *_ in EV} | {b for a, b, *_ in EV}
recs = {}
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    next(rd)
    for r in rd:
        if len(r) < 16:
            continue
        tid = r[0].strip()
        if tid not in want:
            continue
        try:
            vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
        except ValueError:
            continue
        n = len(vals) // 6
        v = vals[: n * 6].reshape(n, 6)
        o = np.argsort(v[:, 5])
        lat, lon = v[o, 0], v[o, 1]
        recs[tid] = {
            "t": v[o, 5],
            "x": (lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            "y": (lat - lat0) * 110540.0,
            "v": v[o, 2],
            "len": float(r[13]) if len(r) > 13 else float("nan"),
            "type": r[1].strip(),
        }

print("=== 一、车长与车型（实测值）===")
for tid in sorted(want):
    d = recs.get(tid)
    if d:
        print(f"  {tid:>5}: {d['type']:<15} 车长 {d['len']:.2f} m")

print("\n=== 二、四例净距复核 ===")
print(f"{'事件':>12} {'窗口':>10} {'最小净距':>9} {'时刻':>8} {'位置':>9} {'前车速度':>8} {'后车速度':>8} {'是否边界':>8}")
for fol, lead, t0, gap_true, gap_sim in EV:
    gf, gl = recs.get(fol), recs.get(lead)
    if not gf or not gl:
        print(f"  {fol}←{lead}: 缺数据")
        continue
    t_lo, t_hi = t0, min(t0 + POST, gf["t"][-1], gl["t"][-1])
    tt = np.arange(t_lo, t_hi, 0.05)
    if len(tt) < 5:
        print(f"  {fol}←{lead}: 窗口不足")
        continue
    xf = np.interp(tt, gf["t"], gf["x"]); yf = np.interp(tt, gf["t"], gf["y"])
    xl = np.interp(tt, gl["t"], gl["x"]); yl = np.interp(tt, gl["t"], gl["y"])
    vf = np.interp(tt, gf["t"], gf["v"]); vl = np.interp(tt, gl["t"], gl["v"])
    dist = np.hypot(xl - xf, yl - yf)
    # 两种口径
    g_center = dist                                    # 中心距
    g_bumper = dist - (gf["len"] + gl["len"]) / 2.0     # 减两车各半车长
    k = int(np.argmin(g_bumper))
    edge = "窗口起" if k < 3 else ("窗口末" if k > len(tt) - 4 else "内部")
    print(f"{fol+'←'+lead:>12} {len(tt):>10} {g_bumper[k]:>9.2f} {tt[k]-t0:>8.1f} "
          f"{'':>9} {vl[k]:>8.2f} {vf[k]:>8.2f} {edge:>8}")
    print(f"{'':>12} 中心距口径最小值 {g_center.min():.2f} m；报告值 {gap_true} m；"
          f"差 {abs(g_bumper[k]-gap_true):.2f} m")

print("\n=== 三、308 的 0.1 m 逐帧核查（重点）===")
fol, lead, t0 = "308", "306", 338.5
gf, gl = recs[fol], recs[lead]
tt = np.arange(t0, min(t0 + POST, gf["t"][-1], gl["t"][-1]), 0.05)
xf = np.interp(tt, gf["t"], gf["x"]); yf = np.interp(tt, gf["t"], gf["y"])
xl = np.interp(tt, gl["t"], gl["x"]); yl = np.interp(tt, gl["t"], gl["y"])
d = np.hypot(xl - xf, yl - yf)
g = d - (gf["len"] + gl["len"]) / 2.0
k = int(np.argmin(g))
print(f"  最小净距 {g[k]:.3f} m 出现在 t0+{tt[k]-t0:.2f}s")
print(f"  该处中心距 {d[k]:.3f} m，两车车长 {gf['len']:.2f} + {gl['len']:.2f} m，"
      f"半车长和 {(gf['len']+gl['len'])/2:.3f} m")
print(f"  速度：后车 {np.interp(tt[k], gf['t'], gf['v']):.2f} m/s  前车 {np.interp(tt[k], gl['t'], gl['v']):.2f} m/s")
print(f"  若车长实为 4.0 m（而非 {gf['len']:.1f}），净距变为 {d[k] - 4.0:.3f} m")
print(f"  → {'贴着测量精度极限' if abs(g[k]) < 0.5 else '不在极限附近'}")
