"""按官方 README 车长重算净距（GPT 第七轮要求：现在就重算，不等补采）

阶段：P3-B（数据契约修正）
官方车长（米）：Car 5.00、Taxi 5.00、Motorcycle 2.50、Medium Vehicle 5.83、
              Bus 12.5、Heavy Vehicle 12.5
此前误用：Car/Taxi 4.5、Motorcycle 2.0、Medium 6.0、Bus 12.0
净距 = 中心距 −（本车长 + 前车长）/2
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
LAT0, LON0 = 37.9777, 23.7375

OFFICIAL = {"Car": 5.00, "Taxi": 5.00, "Motorcycle": 2.50,
            "Medium Vehicle": 5.83, "Bus": 12.5, "Heavy Vehicle": 12.5}
OLD = {"Car": 4.5, "Taxi": 4.5, "Motorcycle": 2.0,
       "Medium Vehicle": 6.0, "Bus": 12.0, "Heavy Vehicle": 12.5}

EV = [("308", "306", 338.5), ("238", "246", 310.0),
      ("471", "482", 538.1), ("524", "523", 586.1)]
want = {a for a, b, _ in EV} | {b for a, b, _ in EV}

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
            "x": (lon - LON0) * 111320.0 * math.cos(math.radians(LAT0)),
            "y": (lat - LAT0) * 110540.0,
            "type": r[1].strip(),
        }

print(f"{'事件':>12} {'车型':>24} {'中心距min':>9} {'旧净距':>8} {'官方净距':>9} {'差':>6}")
rows = []
for fol, lead, t0 in EV:
    if fol not in recs or lead not in recs:
        continue
    gf, gl = recs[fol], recs[lead]
    t_lo, t_hi = t0, min(t0 + 20, gf["t"][-1], gl["t"][-1])
    tt = np.arange(t_lo, t_hi, 0.05)
    if len(tt) < 5:
        continue
    xf = np.interp(tt, gf["t"], gf["x"]); yf = np.interp(tt, gf["t"], gf["y"])
    xl = np.interp(tt, gl["t"], gl["x"]); yl = np.interp(tt, gl["t"], gl["y"])
    d = np.hypot(xl - xf, yl - yf)
    k = int(np.argmin(d))
    tf, tl = gf["type"], gl["type"]
    half_old = (OLD.get(tf, 4.5) + OLD.get(tl, 4.5)) / 2
    half_new = (OFFICIAL.get(tf, 5.0) + OFFICIAL.get(tl, 5.0)) / 2
    g_old, g_new = d[k] - half_old, d[k] - half_new
    print(f"{fol+'←'+lead:>12} {tf+'+'+tl:>24} {d[k]:>9.2f} {g_old:>8.2f} {g_new:>9.2f} {g_new-g_old:>+6.2f}")
    rows.append((fol, lead, d[k], g_old, g_new))

if rows:
    diff = np.array([r[4] - r[3] for r in rows])
    print(f"\n官方车长使净距平均变化 {diff.mean():+.3f} m（范围 {diff.min():+.2f} 到 {diff.max():+.2f}）")
    print("注：变化量取决于车型组合。汽车-汽车对同为 −0.5 m；摩托-摩托对同为 −0.5 m。")
