"""从 MiTra 原始轨迹里提取「带急刹的真实跟驰对片段」

阶段：P3-B（场景资格检查）｜ 数据：T1_DAll.csv（MiTra, 1456 车 / 12 车道 / 0–440 s）
用途：回答 GPT 要求的「片段清单与准入规则」——库里到底有多少个可用的真实制动事件。

做法：
1. 读全表，按 (Vehicle, Time) 取位置/速度/加速度/前车 ID；
2. 用 Leader_ID 配对，欧氏距离减前车车长得净距；
3. 算所需减速度 D = max(v自 − v前, 0)² / (2·净距)；
4. 把「同一对车、连续时间、D 超阈值」的行聚类成片段；
5. 输出片段清单（车对、起止时刻、峰值 D、最小净距、前车峰值减速度）。

准入规则（预先写定，不按结果挑）：
  - 片段时长 ≥ 8 s（够放 3 s 渐入 + 15 s 保持的前置窗）
  - 前车峰值减速度 ≤ −2.5 m/s²（真实急刹）
  - 片段内最小净距 ≥ 1 m（排除数据错误/近接触伪影）
  - 同车对、同一时间窗只算一个事件
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ZIP = Path(r"D:\shen\TJU\AAD\local_research\staging\task11_20261031\mitra\Data_T1.zip")
OUT = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_candidates")
OUT.mkdir(parents=True, exist_ok=True)

D_THR = 0.8           # 片段入选的所需减速度门槛
MIN_DUR = 8.0         # 片段最小时长 s
EARLY_ACC = -2.5      # 前车峰值减速度门槛
MIN_GAP = 1.0

print("读取 T1_DAll.csv ...", flush=True)
with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
    df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                     usecols=["Vehicle_ID", "Vehicle_type", "Time [s]", "x [m]", "y [m]",
                              "Speed [km/h]", "Lon. Acc. [ms-2]", "Vehicle_length [m]",
                              "Lane", "Leader_ID"])
print(f"  行数 {len(df):,}  车辆 {df['Vehicle_ID'].nunique():,}", flush=True)

df["v"] = df["Speed [km/h]"] / 3.6
df["acc"] = df["Lon. Acc. [ms-2]"]

# 前车同刻状态
lead = df[["Vehicle_ID", "Time [s]", "x [m]", "y [m]", "v", "acc", "Vehicle_length [m]"]].rename(
    columns={"Vehicle_ID": "Leader_ID", "x [m]": "lx", "y [m]": "ly", "v": "lv",
             "acc": "lacc", "Vehicle_length [m]": "llen"})
m = df.merge(lead, on=["Leader_ID", "Time [s]"], how="inner")
print(f"  与前车配对成功的行 {len(m):,}", flush=True)

dist = np.hypot(m["lx"] - m["x [m]"], m["ly"] - m["y [m]"])
m["gap"] = dist - (m["Vehicle_length [m]"] + m["llen"]) / 2.0
m["closing"] = m["v"] - m["lv"]
ok = (m["gap"] > MIN_GAP) & (m["gap"] < 200) & (m["closing"] > 0)
m = m[ok].copy()
m["D"] = m["closing"] ** 2 / (2 * m["gap"])

# 聚类成片段：同一 (Vehicle, Leader) 对，时间间隔 <= 1 s
m = m.sort_values(["Vehicle_ID", "Leader_ID", "Time [s]"]).reset_index(drop=True)
pair_key = m["Vehicle_ID"].astype(str) + "|" + m["Leader_ID"].astype(str)
new_pair = pair_key != pair_key.shift()
gap_t = m["Time [s]"].diff() > 1.0
m["seg"] = (new_pair | gap_t).cumsum()

segs = []
for seg, g in m.groupby("seg"):
    if g["D"].max() < D_THR:
        continue
    dur = g["Time [s]"].max() - g["Time [s]"].min()
    if dur < MIN_DUR:
        continue
    if g["lacc"].min() > EARLY_ACC:
        continue
    k = g["D"].idxmax()
    segs.append({
        "follower": str(g["Vehicle_ID"].iloc[0]),
        "leader": str(g["Leader_ID"].iloc[0]),
        "lane": str(g["Lane"].iloc[0]),
        "t_start": round(float(g["Time [s]"].min()), 2),
        "t_end": round(float(g["Time [s]"].max()), 2),
        "duration_s": round(dur, 2),
        "n_frames": int(len(g)),
        "D_max": round(float(g["D"].max()), 3),
        "D_p95": round(float(np.percentile(g["D"], 95)), 3),
        "gap_min_m": round(float(g["gap"].min()), 2),
        "closing_max_mps": round(float(g["closing"].max()), 2),
        "leader_acc_min": round(float(g["lacc"].min()), 2),
        "follower_acc_min": round(float(g["acc"].min()), 2),
        "D_max_at_s": round(float(g.loc[k, "Time [s]"]), 2),
        "gap_at_Dmax_m": round(float(g.loc[k, "gap"]), 2),
    })

segs.sort(key=lambda s: -s["D_max"])
(OUT / "candidate_events.json").write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n通过准入规则的片段 {len(segs)} 个（全库 {pair_key.nunique():,} 个车对）")
print(f"{'后车':>8} {'前车':>8} {'道':>3} {'起':>7} {'止':>7} {'时长':>6} "
      f"{'D峰':>6} {'Dp95':>6} {'净距min':>7} {'闭合max':>7} {'前车减':>7}")
print("-" * 92)
for s in segs[:30]:
    print(f"{s['follower']:>8} {s['leader']:>8} {s['lane']:>3} {s['t_start']:>7.1f} "
          f"{s['t_end']:>7.1f} {s['duration_s']:>6.1f} {s['D_max']:>6.2f} {s['D_p95']:>6.2f} "
          f"{s['gap_min_m']:>7.1f} {s['closing_max_mps']:>7.2f} {s['leader_acc_min']:>7.2f}")
print(f"\n清单已存 {OUT/'candidate_events.json'}")
