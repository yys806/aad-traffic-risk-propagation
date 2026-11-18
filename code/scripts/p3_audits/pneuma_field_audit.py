"""pNEUMA 字段自洽性校验（动手前的数据契约核实）

阶段：P3-B（数据契约）
目的：不靠读文档，用数据自己互相验证字段含义与单位。

四项校验：
  1. 位置差分速度 vs speed 字段        —— 若对得上，说明 speed 单位是 m/s、lat/lon 单位正确
  2. traveled_d vs 累积路径长           —— 校验累计距离字段
  3. avg_speed vs speed 字段均值        —— 校验平均速度字段
  4. 时间间隔分布                       —— 校验采样率与缺帧
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
MAX_CARS = 120          # 抽多少辆车做校验
lat0, lon0 = 37.9777, 23.7375


def to_xy(lat, lon):
    return ((lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            (lat - lat0) * 110540.0)


rows = []
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    hdr = next(rd)
    for r in rd:
        if len(r) < 16:
            continue
        rows.append(r)
print(f"总车数 {len(rows)}，表头 {len(hdr)} 列")
print(f"表头：{hdr}\n")

rng = np.random.default_rng(20261118)
pick = rng.choice(len(rows), size=min(MAX_CARS, len(rows)), replace=False)

err_v, err_d, err_avg, dts = [], [], [], []
bad = []
for i in pick:
    r = rows[i]
    try:
        traveled = float(r[2]); avg = float(r[3])
        vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
    except ValueError:
        continue
    n = len(vals) // 6
    v = vals[: n * 6].reshape(n, 6)
    o = np.argsort(v[:, 5])
    t, lat, lon, sp = v[o, 5], v[o, 0], v[o, 1], v[o, 2]
    if len(t) < 20:
        continue
    x, y = to_xy(lat, lon)
    dt = np.diff(t)
    dts.append(dt)
    ds = np.hypot(np.diff(x), np.diff(y))
    good = dt > 0
    if good.sum() < 10:
        continue

    # 1) 位置差分速度 vs speed 字段
    v_from_pos = ds[good] / dt[good]
    v_field = (sp[:-1][good] + sp[1:][good]) / 2.0
    if np.median(v_field) > 0.5:          # 排除几乎静止的车
        err = np.median(np.abs(v_from_pos - v_field)) / np.median(v_field)
        err_v.append(err)
        if err > 0.25:
            bad.append((r[0], "速度不自洽", round(float(err), 3)))

    # 2) traveled_d vs 累积路径长
    if traveled > 5:
        err_d.append(abs(ds.sum() - traveled) / traveled)

    # 3) avg_speed vs speed 均值
    if avg > 0.5:
        err_avg.append(abs(sp.mean() - avg) / avg)

dts = np.concatenate(dts)
print("=== 4. 时间间隔 ===")
print(f"  中位 {np.median(dts):.5f} s  p1 {np.percentile(dts,1):.5f}  p99 {np.percentile(dts,99):.5f}")
print(f"  对应采样率 {1/np.median(dts):.2f} Hz")
print(f"  间隔 > 0.5 s 的缺口占比：{100*np.mean(dts > 0.5):.2f}%")

print("\n=== 1. 位置差分速度 vs speed 字段（相对误差中位）===")
if err_v:
    e = np.array(err_v)
    print(f"  样本 {len(e)} 辆车：中位 {np.median(e)*100:.1f}%  p90 {np.percentile(e,90)*100:.1f}%")
    print(f"  相对误差 > 25% 的车：{int((e>0.25).sum())} 辆")
    print(f"  → {'speed 字段单位与 lat/lon 自洽（m/s）' if np.median(e) < 0.15 else '存在系统性不自洽，需查单位或坐标'}")

print("\n=== 2. traveled_d vs 累积路径长 ===")
if err_d:
    e = np.array(err_d)
    print(f"  样本 {len(e)} 辆车：中位 {np.median(e)*100:.1f}%  p90 {np.percentile(e,90)*100:.1f}%")
    print(f"  → {'traveled_d 与位置自洽' if np.median(e) < 0.15 else '不一致，traveled_d 可能不是直线/路径累计或单位不同'}")

print("\n=== 3. avg_speed vs speed 均值 ===")
if err_avg:
    e = np.array(err_avg)
    print(f"  样本 {len(e)} 辆车：中位 {np.median(e)*100:.1f}%  p90 {np.percentile(e,90)*100:.1f}%")

if bad:
    print(f"\n=== 不自洽车辆（前 10）===")
    for b in bad[:10]:
        print(f"  {b}")
else:
    print("\n没有发现严重不自洽的车辆。")
