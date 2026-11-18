"""筛出「急刹后前车仍有足够轨迹」的可用片段

阶段：P3-B（场景资格检查·最终）
背景：279 个合格片段里，85% 的前车在急刹后 0.6 s 内就离开数据（无人机视野/跟踪丢失），
      而判断消息能否改善后车响应，必须看急刹之后 15–20 s。所以必须加这条硬约束。

规则（预先写定）：
  - 前车在急刹时刻之后仍有 ≥ 20 s 的轨迹（≥ 15 s 有效、帧数 ≥ 400）
  - 急刹时刻之前至少 10 s 的轨迹（用于预热与消息触发）
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ZIP = Path(r"D:\shen\TJU\AAD\local_research\staging\task11_20261031\mitra\Data_T1.zip")
SRC = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_candidates\candidate_events_v2.json")
OUT = SRC.parent

POST_MIN = 15.0
PRE_MIN = 10.0
MIN_FRAMES = 400

segs = [s for s in json.loads(SRC.read_text(encoding="utf-8"))
        if s.get("straightness") and s["straightness"] >= 0.99]
print(f"直线片段 {len(segs)} 个")

need = set()
for s in segs:
    need.add(s["leader"]); need.add(s["follower"])
with zipfile.ZipFile(ZIP) as z, z.open("T1_DAll.csv") as f:
    it = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                     usecols=["Vehicle_ID", "Time [s]", "Speed [km/h]", "Lane"],
                     chunksize=400_000)
    parts = []
    for ch in it:
        ch["vid"] = ch["Vehicle_ID"].astype(int).astype(str)
        sel = ch[ch["vid"].isin(need)]
        if len(sel):
            parts.append(sel)
d = pd.concat(parts).sort_values(["vid", "Time [s]"])
by = {v: g for v, g in d.groupby("vid")}

keep = []
for s in segs:
    gl = by.get(str(s["leader"]))
    if gl is None or len(gl) < 20:
        continue
    g_in = gl[(gl["Time [s]"] >= s["t_start"]) & (gl["Time [s]"] <= s["t_end"])]
    if len(g_in) < 10:
        continue
    t_ = g_in["Time [s]"].to_numpy()
    v_ = g_in["Speed [km/h]"].to_numpy() / 3.6
    a_ = np.gradient(v_, t_)
    k = int(np.argmin(a_))
    t_brake = float(t_[k])
    # 前车全部轨迹（不受片段边界限制）
    after = gl[(gl["Time [s]"] > t_brake) & (gl["Time [s]"] <= t_brake + POST_MIN + 5)]
    before = gl[(gl["Time [s]"] < t_brake) & (gl["Time [s]"] >= t_brake - PRE_MIN - 5)]
    if len(after) < MIN_FRAMES or (after["Time [s]"].max() - t_brake) < POST_MIN:
        continue
    if len(before) < 200 or (t_brake - before["Time [s]"].min()) < PRE_MIN:
        continue
    rec = dict(s)
    rec.update({
        "t_brake": round(t_brake, 2),
        "pre_avail_s": round(t_brake - float(before["Time [s]"].min()), 1),
        "post_avail_s": round(float(after["Time [s]"].max()) - t_brake, 1),
        "post_frames": int(len(after)),
    })
    keep.append(rec)

keep.sort(key=lambda x: -x["D_max"])
(OUT / "usable_events.json").write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n可用片段（急刹后前车续存 ≥{POST_MIN:.0f}s、急刹前 ≥{PRE_MIN:.0f}s）：{len(keep)} 个\n")
print(f"{'后车':>6} {'前车':>6} {'道':>3} {'D峰':>5} {'净距min':>7} {'前车减':>7} "
      f"{'急刹前':>7} {'急刹后':>7} {'时长':>6}")
print("-" * 74)
for s in keep:
    print(f"{s['follower']:>6} {s['leader']:>6} {s['lane']:>3} {s['D_max']:>5.2f} "
          f"{s['gap_min_m']:>7.1f} {s['leader_brake_min']:>7.2f} "
          f"{s['pre_avail_s']:>7.1f} {s['post_avail_s']:>7.1f} {s['duration_s']:>6.1f}")
print(f"\n清单：{OUT/'usable_events.json'}")
