"""检查居中平滑是否把刹车迹象摊到起点之前（会给消息虚假提前量）

阶段：P3-B（配对验收·附加检查）｜ 依据：GPT 2026-11-18（gpt13.md 第 4 节）

问题：片段筛选用 5 点居中平滑（≈0.17 s）算减速度。居中平滑是双向的，
可能把「开始刹车」的时刻往前摊，从而让消息策略凭空获得提前量。

做法：对每个合格片段的前车，分别用「原始速度差分」和「5 点居中平滑差分」
算首次跌破 −3 m/s² 的时刻，比较两者差多少；同时看平滑对峰值 D 的影响。
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
DT = 0.0334
THR = -3.0

segs = json.loads(EV.read_text(encoding="utf-8"))
print(f"片段 {len(segs)} 个")

need = {s["leader"] for s in segs}
with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
    df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                     usecols=["Vehicle_ID", "Time [s]", "Speed [km/h]"], chunksize=400_000)
    parts = []
    for ch in df:
        ch["vid"] = ch["Vehicle_ID"].astype(int).astype(str)
        sel = ch[ch["vid"].isin(need)]
        if len(sel):
            parts.append(sel)
d = pd.concat(parts).sort_values(["vid", "Time [s]"])
by = {v: g for v, g in d.groupby("vid")}

shift, peak_diff, n_ok = [], [], 0
for s in segs:
    g = by.get(str(s["leader"]))
    if g is None or len(g) < 20:
        continue
    g = g[(g["Time [s]"] >= s["t_start"] - 3) & (g["Time [s]"] <= s["t_end"] + 3)]
    if len(g) < 20:
        continue
    t = g["Time [s]"].to_numpy()
    v = g["Speed [km/h]"].to_numpy() / 3.6
    a_raw = np.gradient(v, t)
    a_sm = np.gradient(pd.Series(v).rolling(5, center=True, min_periods=1).mean().to_numpy(), t)

    def first_below(a, tt):
        k = np.where(a < THR)[0]
        return tt[k[0]] if len(k) else np.nan

    t_raw = first_below(a_raw, t)
    t_sm = first_below(a_sm, t)
    if np.isfinite(t_raw) and np.isfinite(t_sm):
        shift.append(t_sm - t_raw)          # 负值 = 平滑让刹车"提前"了
        n_ok += 1
    peak_diff.append(a_raw.min() - a_sm.min())

shift = np.array(shift)
peak_diff = np.array(peak_diff)
print(f"\n可比较的片段 {n_ok} 个")
if n_ok:
    print(f"刹车起点时刻差（平滑 − 原始）：中位 {np.median(shift):+.3f} s  "
          f"均值 {shift.mean():+.3f} s  最小 {shift.min():+.3f}  最大 {shift.max():+.3f}")
    print(f"  提前超过 0.1 s 的片段：{int((shift < -0.1).sum())} 个 ({100*(shift<-0.1).mean():.1f}%)")
    print(f"  提前超过 0.2 s 的片段：{int((shift < -0.2).sum())} 个 ({100*(shift<-0.2).mean():.1f}%)")
print(f"峰值减速度差（原始 − 平滑）：中位 {np.median(peak_diff):+.2f} m/s²  "
      f"（正值表示平滑削峰）")

print("\n判读：")
print("  若中位偏移在 ±0.05 s 内、且提前超过 0.1 s 的片段很少 → 平滑不构成虚假提前量")
print("  若大量片段提前 0.2 s 以上 → 必须改用单向（因果）平滑重算触发起始时刻")
