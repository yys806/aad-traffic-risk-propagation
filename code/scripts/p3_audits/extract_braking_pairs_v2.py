"""片段质控 v2：用平滑速度差分替代噪声极大的 Lon.Acc 字段

阶段：P3-B（场景资格检查）｜ 数据：T1_DAll.csv + Teleporting_jumps.csv

v1 的问题：直接用数据自带的 Lon. Acc. 字段，中位前车减速度 −14 m/s²，
超过干路面物理极限（约 −8~−10），说明该字段是无人机视觉跟踪的差分噪声，不可用。
另有净距 1.8 m 却闭合 14 m/s 的片段（物理上早已追尾），也是伪影。

v2 的做法（全部预先写定，不按结果挑）：
  1. 排除 Teleporting_jumps 标记为跳变的采样点；
  2. 用平滑后的速度差分算减速度（每车按时间排序，5 点移动平均 ≈ 0.17 s）；
  3. 物理合理性：净距 ≥ 3 m、闭合速度 ≤ 12 m/s、D 峰值 ≤ 8 m/s²；
  4. 时长 ≥ 15 s（够放 3 s 渐入 + 15 s 保持 + 前置观察）。
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(r"D:\shen\TJU\AAD\local_research\staging\task11_20261031\mitra")
ZIP = BASE / "Data_T1.zip"
JUMPS = BASE / "Teleporting_jumps.csv"
OUT = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_candidates")

# 质控参数（预先写定）
SMOOTH = 5          # 速度平滑点数（0.033 s/点 → 约 0.17 s）
ACC_BRAKE = -3.0    # 急刹门槛 m/s²
ACC_FLOOR = -10.0   # 物理下限：干路面最大制动约 -8~-10；低于此值判为跟踪伪影或碰撞，排除
GAP_MIN = 3.0
CLOSING_MAX = 12.0
D_MAX_CAP = 8.0
D_ENTRY = 0.0      # GPT 的连续加权终点不需要硬门槛；这里只排除完全无闭合的片段
DUR_MIN = 15.0
DT = 0.0334

print("读跳变标记 ...", flush=True)
j = pd.read_csv(JUMPS, usecols=["Vehicle_ID", "Time [s]", "is_teleporting_long", "is_teleporting_lat"])
bad = j[(j["is_teleporting_long"] == True) | (j["is_teleporting_lat"] == True)]
bad_keys = set(zip(bad["Vehicle_ID"].astype(str), np.round(bad["Time [s]"], 3)))
print(f"  跳变点 {len(bad_keys)} 个", flush=True)

print("读 T1_DAll.csv ...", flush=True)
with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
    df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                     usecols=["Vehicle_ID", "Vehicle_type", "Time [s]", "x [m]", "y [m]",
                              "Speed [km/h]", "Vehicle_length [m]", "Lane", "Leader_ID"])
df["vid"] = df["Vehicle_ID"].astype(int).astype(str)
df["lkey"] = df["Leader_ID"].astype(int).astype(str)
df["v"] = df["Speed [km/h]"] / 3.6
df = df.sort_values(["vid", "Time [s]"]).reset_index(drop=True)

# 平滑速度 + 差分算加速度
df["v_s"] = df.groupby("vid")["v"].transform(
    lambda s: s.rolling(SMOOTH, center=True, min_periods=1).mean())
df["acc_calc"] = df.groupby("vid")["v_s"].transform(lambda s: s.diff() / DT)

lead = df[["vid", "Time [s]", "x [m]", "y [m]", "v_s", "acc_calc", "Vehicle_length [m]"]].rename(
    columns={"vid": "lkey", "x [m]": "lx", "y [m]": "ly", "v_s": "lv",
             "acc_calc": "lacc", "Vehicle_length [m]": "llen"})
df2 = df[df["Leader_ID"] > 0]          # -1 表示无前车，必须排除，否则会配出幽灵车对
m = df2.merge(lead, on=["lkey", "Time [s]"], how="inner")
m["gap"] = np.hypot(m["lx"] - m["x [m]"], m["ly"] - m["y [m]"]) - (m["Vehicle_length [m]"] + m["llen"]) / 2.0
m["closing"] = m["v_s"] - m["lv"]
m["D"] = np.where(m["gap"] > 0, np.maximum(m["closing"], 0) ** 2 / (2 * np.maximum(m["gap"], 0.1)), np.nan)

# 排跳变
bad_series = m["vid"].astype(str) + "|" + m["Time [s]"].round(3).astype(str)
m = m[~bad_series.isin({f"{a}|{b}" for a, b in bad_keys})]

ok = (m["gap"] >= GAP_MIN) & (m["gap"] <= 200) & (m["closing"] <= CLOSING_MAX) & m["D"].notna()
m = m[ok].copy()

m = m.reset_index(drop=True)
pk = m["vid"] + "|" + m["lkey"]
m["seg"] = ((pk != pk.shift()) | (m["Time [s]"].diff() > 1.0)).cumsum()

segs = []
for _, g in m.groupby("seg"):
    if len(g) < 10:
        continue
    dur = g["Time [s]"].max() - g["Time [s]"].min()
    if dur < DUR_MIN:
        continue
    dmax = g["D"].max()
    if dmax < D_ENTRY or dmax > D_MAX_CAP:
        continue
    if g["lacc"].min() > ACC_BRAKE or g["lacc"].min() < ACC_FLOOR:
        continue
    # GPT 要求：换道与 Leader_ID 跳变必须单独排除，否则一维回放不成立
    if g["Lane"].nunique() > 1:
        continue
    if g["lkey"].nunique() > 1:
        continue
    # 一维回放要求近直线：路径长与首末直线距之比 < 0.99 的片段（含转弯）排除
    xy = g[["x [m]", "y [m]"]].to_numpy(dtype=float)
    plen = float(np.sum(np.hypot(np.diff(xy[:, 0]), np.diff(xy[:, 1]))))
    direct = float(np.hypot(xy[-1, 0] - xy[0, 0], xy[-1, 1] - xy[0, 1]))
    if plen > 5.0 and direct / plen < 0.99:
        continue
    k = g["D"].idxmax()
    segs.append({
        "follower": g["vid"].iloc[0], "leader": str(g["lkey"].iloc[0]),
        "lane": str(g["Lane"].iloc[0]),
        "t_start": round(float(g["Time [s]"].min()), 1), "t_end": round(float(g["Time [s]"].max()), 1),
        "duration_s": round(dur, 1), "n_frames": int(len(g)),
        "D_max": round(float(dmax), 2), "D_p95": round(float(np.percentile(g["D"], 95)), 2),
        "gap_min_m": round(float(g["gap"].min()), 2),
        "closing_max_mps": round(float(g["closing"].max()), 2),
        "leader_brake_min": round(float(g["lacc"].min()), 2),
        "follower_brake_min": round(float(g["acc_calc"].min()), 2),
        "straightness": round(direct / plen, 4) if plen > 5 else None,
    })

segs.sort(key=lambda s: -s["D_max"])
(OUT / "candidate_events_v2.json").write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n质控后合格片段 {len(segs)} 个")
if segs:
    print(f"{'后车':>7} {'前车':>7} {'道':>3} {'起':>7} {'止':>6} {'时长':>6} {'D峰':>6} "
          f"{'净距min':>7} {'闭合max':>7} {'前车减':>7} {'后车减':>7}")
    print("-" * 88)
    for s in segs:
        print(f"{s['follower']:>7} {s['leader']:>7} {s['lane']:>3} {s['t_start']:>7.1f} "
              f"{s['t_end']:>6.1f} {s['duration_s']:>6.1f} {s['D_max']:>6.2f} "
              f"{s['gap_min_m']:>7.1f} {s['closing_max_mps']:>7.2f} "
              f"{s['leader_brake_min']:>7.2f} {s['follower_brake_min']:>7.2f}")
print(f"\n清单：{OUT/'candidate_events_v2.json'}")
