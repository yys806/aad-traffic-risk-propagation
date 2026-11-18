"""P3-B 可行性审计 第 1 步：解析层 + 计时层

阶段：P3-B（按 P3B_预注册协议_20261118.md 第三节 表1/表2 的原始数据部分）
这一步只回答一件事：**这份文件能不能按契约解析，时间轴能不能用。**
不定义事件、不算减速度、不判风险。

依据契约：
  - 1.4 硬约束 1：先判连续段，再求导
  - 1.4 硬约束 2：按六字段块解析，不按绝对列号猜字段
  - 1.2 换算规则：speed 是 km/h，须 /3.6
"""
from __future__ import annotations

import csv
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
OUT = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_audit")
OUT.mkdir(parents=True, exist_ok=True)

META = 4
BLOCK = 6
FIELDS = ["lat", "lon", "speed", "lon_acc", "lat_acc", "time"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


print("=" * 70)
print("表 1：数据与计时")
print("=" * 70)
print(f"文件：{SRC.name}")
print(f"SHA256：{sha256(SRC)}")
print(f"字节数：{SRC.stat().st_size:,}")

# ---------- 解析层 ----------
n_lines = 0
bad_block = 0
bad_value = 0
rows = []
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    hdr = next(rd)
    print(f"表头 {len(hdr)} 列：{hdr}")
    for r in rd:
        n_lines += 1
        # 去掉末尾因分隔符产生的空槽
        while r and r[-1].strip() == "":
            r.pop()
        if len(r) < META + BLOCK:
            bad_block += 1
            continue
        nblock = (len(r) - META) / BLOCK
        if abs(nblock - round(nblock)) > 1e-9:
            bad_block += 1
            continue
        try:
            meta = r[:META]
            vals = np.array([float(x) for x in r[META:]], dtype=float)
        except ValueError:
            bad_value += 1
            continue
        rows.append((meta, vals.reshape(-1, BLOCK)))

print(f"\n物理数据行数：{n_lines}")
print(f"块长不合规行：{bad_block}")
print(f"数值解析失败行：{bad_value}")
print(f"成功解析轨迹：{len(rows)}")

ids = [m[0].strip() for m, _ in rows]
print(f"唯一 track_id 数：{len(set(ids))}（重复 {len(ids) - len(set(ids))}）")

from collections import Counter
tcnt = Counter(m[1].strip() for m, _ in rows)
print(f"车型分布：{dict(tcnt)}")

# ---------- 计时层 ----------
print("\n" + "-" * 70)
print("计时质量（按原始顺序，不排序不插值）")
print("-" * 70)
dt_all = []
t_start = []
n_nonmono = 0
n_dup = 0
dur = []
for meta, arr in rows:
    t = arr[:, 5]
    if len(t) < 3:
        continue
    dt = np.diff(t)
    dt_all.append(dt)
    if np.any(dt < 0):
        n_nonmono += 1
    if np.any(dt == 0):
        n_dup += 1
    t_start.append(t[0])
    dur.append(t[-1] - t[0])

dt_all = np.concatenate(dt_all)
t_start = np.array(t_start)
dur = np.array(dur)

print(f"原始顺序出现负步长的轨迹：{n_nonmono} / {len(t_start)}")
print(f"出现零步长的轨迹：{n_dup}")
print(f"\n步长分布（秒）：")
for q in [0, 1, 5, 25, 50, 75, 95, 99, 100]:
    print(f"  p{q:<3} {np.percentile(dt_all, q):.5f}")
print(f"  中位对应采样率：{1/np.median(dt_all):.2f} Hz")
print(f"  步长 > 0.5 s 的缺口占比：{100*np.mean(dt_all > 0.5):.3f}%")
print(f"  步长 > 2.0 s 的缺口占比：{100*np.mean(dt_all > 2.0):.3f}%")

print(f"\n轨迹起始时刻（相对文件内时间轴）：")
print(f"  中位 {np.median(t_start):.2f} s   p10 {np.percentile(t_start,10):.2f}   p90 {np.percentile(t_start,90):.2f}")
print(f"  从 0 附近开始的轨迹数（<1 s）：{int((t_start < 1).sum())} / {len(t_start)}")
print(f"  → {'各车独立计时，不是全局统一时间轴' if (t_start<1).sum() > 0.9*len(t_start) else '各车进入时刻不同，可能共用一条时间轴'}")

print(f"\n单车可观测时长（秒）：")
for q in [5, 10, 25, 50, 75, 90, 95, 100]:
    print(f"  p{q:<3} {np.percentile(dur, q):.1f}")
print(f"  中位 {np.median(dur):.1f} s")
print(f"  ≥20 s 的轨迹占比：{100*np.mean(dur>=20):.1f}%")
print(f"  ≥30 s 的轨迹占比：{100*np.mean(dur>=30):.1f}%")
print(f"  ≥60 s 的轨迹占比：{100*np.mean(dur>=60):.1f}%")

# ---------- 速度分布（按契约换算）----------
print("\n" + "-" * 70)
print("速度分布（已按契约 /3.6 换算为 m/s；仅作量级核对，不用于事件定义）")
print("-" * 70)
sp_per_frame = []
sp_per_car = []
for meta, arr in rows:
    v = arr[:, 2] / 3.6
    if len(v) == 0:
        continue
    sp_per_frame.append(v)
    sp_per_car.append(v.mean())
sp_per_frame = np.concatenate(sp_per_frame)
sp_per_car = np.array(sp_per_car)

print(f"按帧等权（{len(sp_per_frame):,} 帧）：")
for q in [5, 25, 50, 75, 95, 99]:
    print(f"  p{q:<3} {np.percentile(sp_per_frame, q):.2f} m/s  ({np.percentile(sp_per_frame,q)*3.6:.1f} km/h)")
print(f"\n按车辆等权（{len(sp_per_car)} 辆车均值）：")
for q in [5, 25, 50, 75, 95]:
    print(f"  p{q:<3} {np.percentile(sp_per_car, q):.2f} m/s  ({np.percentile(sp_per_car,q)*3.6:.1f} km/h)")
print(f"\n两种口径的中位差：{np.median(sp_per_frame)-np.median(sp_per_car):+.2f} m/s")

# 保存
np.save(OUT / "speed_frame_mps.npy", sp_per_frame)
np.save(OUT / "speed_car_mps.npy", sp_per_car)
np.save(OUT / "duration.npy", dur)
print(f"\n诊断数组已保存到 {OUT}")
