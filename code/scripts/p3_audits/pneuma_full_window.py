"""统计：触发时直跟的 443 个事件里，整段 20 s 有多少能全程判为直跟

阶段：P3-B（第 4 步前的前置统计）
用途：回答「在这批数据上，能完整回放 20 s 的事件有多少个」——决定双车回放能用多大样本。

优化：先按每辆车的观测时间窗预筛，只对 t 时刻真正在场的车做投影。
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
import os as _os
_TIER = _os.environ.get("TIER", "m10")
EVT = Path("D:/shen/TJU/AAD/code/outputs/analysis/P3B_pneuma_" + _TIER + "/table_events.csv")
OUT = EVT.parent

REF_BACK = 5.0
BAND_W = 3.0
MIN_SPEED = 2.0
GRID = 0.1
lat0, lon0 = 37.9777, 23.7375

print("读事件表与轨迹 ...", flush=True)
evs = []
with EVT.open("r", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r.get("t0_state") == "直跟":
            evs.append(r)
print(f"  触发时直跟的事件 {len(evs)} 个")

want = {r["lead_id"] for r in evs} | {r["fol_id"] for r in evs}
allcars = {}
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    next(rd)
    for row in rd:
        if len(row) < 16:
            continue
        try:
            vals = np.array([float(x) for x in row[4:] if x.strip() != ""])
        except ValueError:
            continue
        n = len(vals) // 6
        v = vals[: n * 6].reshape(n, 6)
        o = np.argsort(v[:, 5])
        t, lat, lon, sp = v[o, 5], v[o, 0], v[o, 1], v[o, 2]
        allcars[row[0].strip()] = {
            "t": t,
            "x": (lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            "y": (lat - lat0) * 110540.0,
            "v": sp,
        }
# 预筛索引：每辆车的时间窗
tspan = {k: (d["t"][0], d["t"][-1]) for k, d in allcars.items()}


def at(rec, t):
    if t < rec["t"][0] or t > rec["t"][-1]:
        return None
    return (float(np.interp(t, rec["t"], rec["x"])),
            float(np.interp(t, rec["t"], rec["y"])),
            float(np.interp(t, rec["t"], rec["v"])))


def prep_curve(curve):
    a = curve[:-1]
    b = curve[1:]
    d = b - a
    L2 = (d ** 2).sum(1)
    segL = np.sqrt(np.maximum(L2, 1e-12))
    s0 = np.concatenate([[0.0], np.cumsum(segL)[:-1]])
    return a, d, np.maximum(L2, 1e-9), s0, segL


def project_fast(px, py, C):
    a, d, L2, s0, segL = C
    tt = ((px - a[:, 0]) * d[:, 0] + (py - a[:, 1]) * d[:, 1]) / L2
    np.clip(tt, 0.0, 1.0, out=tt)
    cx = a[:, 0] + tt * d[:, 0]
    cy = a[:, 1] + tt * d[:, 1]
    dist = np.hypot(px - cx, py - cy)
    k = int(np.argmin(dist))
    return float(s0[k] + tt[k] * segL[k]), float(dist[k])


print("逐事件统计 ...", flush=True)
rows = []
for k, r in enumerate(evs):
    lid, fid = r["lead_id"], r["fol_id"]
    gl, gf = allcars.get(lid), allcars.get(fid)
    if gl is None or gf is None:
        continue
    t0 = float(r["t"])
    t_hi = min(t0 + 20.0, gl["t"][-1], gf["t"][-1])
    n_tot = n_ok = n_int = n_unk = 0
    first_interrupt = None
    for t in np.arange(t0, t_hi, GRID):
        n_tot += 1
        ff = at(gf, t)
        if ff is None or ff[2] < MIN_SPEED:
            n_unk += 1
            continue
        m = (gl["t"] >= t0 - REF_BACK) & (gl["t"] <= t)
        if m.sum() < 2:
            n_unk += 1
            continue
        curve = np.column_stack([gl["x"][m], gl["y"][m]])
        C = prep_curve(curve)
        s_f, e_f = project_fast(ff[0], ff[1], C)
        s_end = float(C[3][-1] + C[4][-1])
        # 包围盒预筛：只对曲线附近 BAND_MAX 内的车做精确投影
        xmin, xmax = curve[:, 0].min() - 8.0, curve[:, 0].max() + 8.0
        ymin, ymax = curve[:, 1].min() - 8.0, curve[:, 1].max() + 8.0
        hit = False
        for tid, rec in allcars.items():
            if tid in (lid, fid):
                continue
            a, b = tspan[tid]
            if t < a or t > b:
                continue
            p = at(rec, t)
            if p is None:
                continue
            if p[0] < xmin or p[0] > xmax or p[1] < ymin or p[1] > ymax:
                continue
            s_o, e_o = project_fast(p[0], p[1], C)
            if s_f + 0.5 < s_o < s_end - 0.5 and abs(e_o) <= BAND_W:
                hit = True
                break
        if hit:
            n_int += 1
            if first_interrupt is None:
                first_interrupt = round(t - t0, 1)
        elif abs(e_f) <= BAND_W:
            n_ok += 1
        else:
            n_unk += 1
    if n_tot == 0:
        continue
    rows.append({
        "lead": lid, "fol": fid, "t0": t0, "frames": n_tot,
        "straight": n_ok, "interrupt": n_int, "unknown": n_unk,
        "frac_straight": round(n_ok / n_tot, 3),
        "frac_unknown": round(n_unk / n_tot, 3),
        "first_interrupt_s": first_interrupt,
    })
    if (k + 1) % 50 == 0:
        print(f"  已处理 {k+1}/{len(evs)}", flush=True)

fr = np.array([r["frac_straight"] for r in rows])
fu = np.array([r["frac_unknown"] for r in rows])
print(f"\n=== 443 个「触发时直跟」事件的 20 s 全窗表现（{len(rows)} 个有效）===")
print(f"  直跟帧占比：中位 {np.median(fr):.2f}  均值 {fr.mean():.2f}  p90 {np.percentile(fr,90):.2f}")
print(f"  未知帧占比：中位 {np.median(fu):.2f}")
for thr in (1.0, 0.95, 0.9, 0.8, 0.5):
    n = int((fr >= thr - 1e-9).sum())
    print(f"  直跟帧占比 ≥ {thr:.0%} 的事件：{n:>3} 个 ({100*n/max(len(rows),1):.1f}%)")

print(f"\n=== 分布 ===")
bins = [(0.95, 1.01, "几乎全程直跟"), (0.8, 0.95, "大部分直跟"),
        (0.5, 0.8, "一半左右"), (0.2, 0.5, "少部分"), (0.0, 0.2, "几乎判不清")]
for lo, hi, name in bins:
    n = int(((fr >= lo) & (fr < hi)).sum())
    print(f"  {name:<12} ({lo:.0%}–{hi:.0%}): {n:>3} 个")

(OUT / "full_window_stats.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n明细：{OUT/'full_window_stats.json'}")
