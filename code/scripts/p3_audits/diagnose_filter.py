"""诊断：v2 为什么筛出 0 个——逐条看每个门槛排除了多少

阶段：P3-B（场景资格检查）
不改变任何判定，只做归因：是数据不支持，还是我的门槛定得太死。
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ZIP = Path(r"D:\shen\TJU\AAD\local_research\staging\task11_20261031\mitra\Data_T1.zip")
DT = 0.0334

with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
    df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                     usecols=["Vehicle_ID", "Time [s]", "x [m]", "y [m]", "Speed [km/h]",
                              "Vehicle_length [m]", "Lane", "Leader_ID"])
df["vid"] = df["Vehicle_ID"].astype(int).astype(str)
df["lkey"] = df["Leader_ID"].astype(int).astype(str)
df["v"] = df["Speed [km/h]"] / 3.6
df = df.sort_values(["vid", "Time [s]"]).reset_index(drop=True)
df["v_s"] = df.groupby("vid")["v"].transform(lambda s: s.rolling(5, center=True, min_periods=1).mean())
df["acc_calc"] = df.groupby("vid")["v_s"].transform(lambda s: s.diff() / DT)

lead = df[["vid", "Time [s]", "x [m]", "y [m]", "v_s", "acc_calc", "Vehicle_length [m]"]].rename(
    columns={"vid": "lkey", "x [m]": "lx", "y [m]": "ly", "v_s": "lv", "acc_calc": "lacc",
             "Vehicle_length [m]": "llen"})
m = df[df["Leader_ID"] > 0].merge(lead, on=["lkey", "Time [s]"], how="inner")
m["gap"] = np.hypot(m["lx"] - m["x [m]"], m["ly"] - m["y [m]"]) - m["llen"]
m["closing"] = m["v_s"] - m["lv"]
m["D"] = np.where(m["gap"] > 0, np.maximum(m["closing"], 0) ** 2 / (2 * np.maximum(m["gap"], 0.1)), np.nan)
print(f"配对行 {len(m):,}")

m = m[(m["gap"] >= 1) & (m["gap"] <= 200)].copy()
print(f"净距合法（1–200 m）后 {len(m):,}")

pk = m["vid"] + "|" + m["lkey"]
m["seg"] = ((pk != pk.shift()) | (m["Time [s]"].diff() > 1.0)).cumsum()

rows = []
for _, g in m.groupby("seg"):
    if len(g) < 10:
        continue
    rows.append({
        "dur": g["Time [s]"].max() - g["Time [s]"].min(),
        "D_max": g["D"].max(),
        "gap_min": g["gap"].min(),
        "closing_max": g["closing"].max(),
        "lacc_min": g["lacc"].min(),
        "n": len(g),
    })
S = pd.DataFrame(rows)
print(f"候选片段 {len(S):,}\n")

print("=== 各门槛单独看（不叠加）===")
for name, cond in [
    ("时长 >= 8 s", S["dur"] >= 8),
    ("时长 >= 15 s", S["dur"] >= 15),
    ("D峰 <= 8", S["D_max"] <= 8),
    ("D峰 0.8–8（入门+上限）", (S["D_max"] >= 0.8) & (S["D_max"] <= 8)),
    ("闭合 <= 12 m/s", S["closing_max"] <= 12),
    ("前车平滑减 <= -3", S["lacc_min"] <= -3),
    ("前车平滑减 <= -1.5", S["lacc_min"] <= -1.5),
    ("净距min >= 3 m", S["gap_min"] >= 3),
]:
    print(f"  {name:<24} 通过 {int(cond.sum()):>5} 个  ({100*cond.mean():.1f}%)")

print("\n=== 逐步叠加，看是哪一条把结果打到 0 ===")
c = pd.Series(True, index=S.index)
steps = [
    ("时长 >= 8", S["dur"] >= 8),
    ("+ D峰 <= 8", S["D_max"] <= 8),
    ("+ 闭合 <= 12", S["closing_max"] <= 12),
    ("+ 净距min >= 3", S["gap_min"] >= 3),
    ("+ 前车减 <= -3", S["lacc_min"] <= -3),
]
for name, cond in steps:
    c = c & cond
    print(f"  {name:<18} 剩 {int(c.sum()):>5} 个")

print("\n=== 分布 ===")
for col, q in [("dur", [50, 75, 90, 99]), ("D_max", [50, 75, 90, 99]),
               ("gap_min", [1, 5, 25, 50]), ("lacc_min", [1, 5, 25, 50])]:
    v = S[col].replace([np.inf, -np.inf], np.nan).dropna()
    print(f"  {col:<10} " + "  ".join(f"p{p}={np.percentile(v,p):.2f}" for p in q)
          + f"   max={v.max():.2f} min={v.min():.2f}")
