"""pNEUMA 资格盘点·第 1 步：单车可观测时长与急刹后车对窗口

阶段：P3-B（数据资格盘点）｜ 依据：GPT 2026-11-18（gpt15.md 第 2 节四步法）
数据：dataset/pNEUMA/20181101_d1_0800_0830.csv（1 架无人机 × 30 分钟早高峰）

pNEUMA 宽表格式（已核）：
  前 4 列元数据 track_id; type; traveled_d; avg_speed
  之后每 6 列一组：lat; lon; speed; lon_acc; lat_acc; time
  每行 = 一辆车的完整轨迹

第 1 步只做 GPT 说的「先看连续轨迹」，先不算加速度、不算车对：
  1. 单车可观测时长分布（按 ID 的连续观测段，不跨长缺帧）
  2. 有没有能容纳「急刹前 10 s + 急刹后 20 s」的时长
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
MAX_GAP = 0.5      # 组内相邻采样间隔超过此值就算断裂

rows = []
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    header = next(rd)
    for r in rd:
        if len(r) < 10:
            continue
        rows.append(r)

print(f"车辆行数 {len(rows)}")
print(f"表头 {len(header)} 列：{header[:10]}")

dur_list, frames_list, types = [], [], {}
for r in rows:
    try:
        tid = r[0]
        typ = r[1]
        vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
    except ValueError:
        continue
    n_groups = len(vals) // 6
    vals = vals[: n_groups * 6].reshape(n_groups, 6)
    t = vals[:, 5]
    if len(t) < 2:
        continue
    dt = np.diff(t)
    # 按 MAX_GAP 切成连续段，取最长段
    brk = np.where(dt > MAX_GAP)[0]
    segs = np.split(np.arange(len(t)), brk + 1)
    longest = max(segs, key=len)
    dur = t[longest[-1]] - t[longest[0]]
    dur_list.append(dur)
    frames_list.append(len(longest))
    types[typ] = types.get(typ, 0) + 1

dur = np.array(dur_list)
fr = np.array(frames_list)
print(f"\n可用车辆 {len(dur)}")
print("车型分布：", dict(sorted(types.items(), key=lambda kv: -kv[1])))
print(f"\n单车可观测时长（秒）：中位 {np.median(dur):.0f}  p10 {np.percentile(dur,10):.0f}  "
      f"p90 {np.percentile(dur,90):.0f}  最大 {dur.max():.0f}")
print(f"单车帧数：中位 {np.median(fr):.0f}  最大 {fr.max():.0f}")

for need in (10, 20, 30, 40, 60, 120):
    n = int((dur >= need).sum())
    print(f"  时长 ≥ {need:>3} s 的车：{n:>3} 辆 ({100*n/len(dur):.1f}%)")

print("\n对照：MiTra T1 每车中位追踪 8.7–11.0 s（此前实测），所以那批数据装不下急刹后 20 s。")
print(f"pNEUMA 这一架无人机：{100*(dur>=30).mean():.0f}% 的车能观测 ≥30 s。")
