"""复核高 D 片段的减速度尖峰：是持续减速还是单点伪影

阶段：P3-B（场景资格检查）
GPT 要求：用原始位置、速度和时间戳核对单位、缺帧及差分边界，
看 −10 到 −28 m/s² 是持续减速还是单点伪影。

做法：对 D 峰最高的若干片段，打印前车逐帧速度、位置、时间间隔与差分加速度，
并检查：① 帧间隔是否均匀（缺帧会造出假尖峰）；② 减速度是否只出现在单帧；
③ 位置差分与速度是否自洽（不自洽说明定位跳变）。
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ZIP = Path(r"D:\shen\TJU\AAD\local_research\staging\task11_20261031\mitra\Data_T1.zip")
EV = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_candidates\candidate_events_v2.json")

segs = json.loads(EV.read_text(encoding="utf-8"))
segs.sort(key=lambda s: -s["D_max"])
top = segs[:6]
print(f"复核 D 峰最高的 {len(top)} 个片段\n")

want = {s["leader"] for s in top} | {s["follower"] for s in top}
with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
    df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                     usecols=["Vehicle_ID", "Time [s]", "x [m]", "y [m]", "Speed [km/h]",
                              "Lon. Acc. [ms-2]", "Vehicle_length [m]", "Vehicle_type", "Lane"])
df["vid"] = df["Vehicle_ID"].astype(int).astype(str)
df = df[df["vid"].isin(want)].sort_values(["vid", "Time [s]"])

for s in top:
    print("=" * 96)
    print(f"片段 后车{s['follower']} 前车{s['leader']} 道{s['lane']} "
          f"{s['t_start']}–{s['t_end']}s  D峰{s['D_max']}  净距min{s['gap_min_m']}m")
    for role, vid in (("前车", s["leader"]), ("后车", s["follower"])):
        g = df[(df["vid"] == str(vid)) &
               (df["Time [s]"] >= s["t_start"] - 1) & (df["Time [s]"] <= s["t_end"] + 1)]
        if len(g) < 3:
            print(f"  {role} {vid}: 数据不足")
            continue
        t = g["Time [s]"].to_numpy()
        v = g["Speed [km/h]"].to_numpy() / 3.6
        y = g["y [m]"].to_numpy()
        acc_raw = g["Lon. Acc. [ms-2]"].to_numpy()
        dt = np.diff(t)
        vdiff_acc = np.diff(v) / np.maximum(dt, 1e-6)
        pos_acc = np.diff(y, 2) / np.maximum(dt[:-1], 1e-6) ** 2 if len(y) > 2 else np.array([])
        print(f"  {role} {vid} ({g['Vehicle_type'].iloc[0]}, 长{g['Vehicle_length [m]'].iloc[0]:.1f}m): "
              f"{len(g)} 帧, 时间间隔 中位{np.median(dt):.4f}s 最大{dt.max():.4f}s 最小{dt.min():.4f}s")
        print(f"     速度 {v.min():.1f}–{v.max():.1f} m/s | 速度差分加速度 最负 {vdiff_acc.min():.2f} m/s² "
              f"| 数据自报加速度 最负 {acc_raw.min():.2f} m/s²")
        # 单帧尖峰检测
        if len(vdiff_acc):
            k = int(np.argmin(vdiff_acc))
            near = vdiff_acc[max(0, k - 2):k + 3]
            print(f"     最猛减速在 t={t[k+1]:.2f}s：{vdiff_acc[k]:.2f} m/s²，"
                  f"相邻 ±2 帧为 {np.round(near,2)}  → "
                  f"{'单帧尖峰（可疑）' if np.sum(near < -5) <= 1 else '持续减速（可信）'}")
        if len(pos_acc):
            print(f"     位置二阶差分 最负 {np.nanmin(pos_acc):.2f} m/s²（与速度差分应大致同量级）")

print("\n" + "=" * 96)
print("判读要点：")
print("  帧间隔若出现明显不均匀 → 缺帧，差分会造假尖峰")
print("  若最猛减速只在单帧出现、相邻帧迅速回到正常 → 单点伪影")
print("  若位置二阶差分与速度差分差一个量级 → 定位跳变或单位错误")
