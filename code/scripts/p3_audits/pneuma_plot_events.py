"""pNEUMA 三态复核用图：把 t0 附近候选两车与周围所有车画出来

阶段：P3-B（结构门槛·人工复核）
依据：gpt18.md 第 5 节——「把 t0 附近的候选两车和周围第三车一起画出来」

用途：只看数值分不清「横向残差 3–6 m」是真邻道还是弯道投影误差，画出来一眼就能分辨。
输出：每个事件一张 PNG，灰色为周围车，绿=候选前车，红=候选后车，覆盖 t0-6 s 到 t0+6 s。
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
EV = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_pneuma\three_state.json")
OUT = EV.parent / "figs"
OUT.mkdir(parents=True, exist_ok=True)

WIN = 6.0
rows = json.loads(EV.read_text(encoding="utf-8"))
# 只画「未知」里横向残差 3–7 m 的（边界情形），外加 1 个残差很大的
sel = [r for r in rows if r["state"] == "未知" and r.get("e_m") is not None and 2.9 <= abs(r["e_m"]) <= 7.5]
sel = sel[:6]
if not sel:
    sel = [r for r in rows if r["state"] == "未知"][:6]
print("将绘制：")
for r in sel:
    print(f"  {r['fol_id']}←{r['lead_id']} t0={r['t']} 残差 {r.get('e_m')}")

want = set()
for r in sel:
    want.add(r["lead_id"]); want.add(r["fol_id"])

lat0, lon0 = 37.9777, 23.7375
recs = {}
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
        t, lat, lon = v[o, 5], v[o, 0], v[o, 1]
        x = (lon - lon0) * 111320.0 * math.cos(math.radians(lat0))
        y = (lat - lat0) * 110540.0
        recs[row[0].strip()] = {"t": t, "x": x, "y": y}

for k, r in enumerate(sel):
    t0 = r["t"]
    fig, ax = plt.subplots(figsize=(9, 9))
    # 周围所有车
    for tid, d in recs.items():
        m = (d["t"] >= t0 - WIN) & (d["t"] <= t0 + WIN)
        if m.sum() < 3:
            continue
        if tid in (r["lead_id"], r["fol_id"]):
            continue
        ax.plot(d["x"][m], d["y"][m], lw=0.8, color="0.75", alpha=0.7, zorder=1)
    for tid, color, lbl in ((r["lead_id"], "green", "LEAD"), (r["fol_id"], "red", "FOL")):
        d = recs.get(tid)
        if d is None:
            continue
        m = (d["t"] >= t0 - WIN) & (d["t"] <= t0 + WIN)
        ax.plot(d["x"][m], d["y"][m], lw=2.0, color=color, label=f"{lbl} {tid}", zorder=3)
        # t0 时刻的位置点
        if m.sum():
            xt = float(np.interp(t0, d["t"], d["x"]))
            yt = float(np.interp(t0, d["t"], d["y"]))
            ax.plot([xt], [yt], "o", color=color, ms=9, zorder=4)
    ax.set_title(f"event {r['fol_id']}<-{r['lead_id']}  t0={t0:.1f}s  lateral_res={r.get('e_m')} m",
                 fontsize=10)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    p = OUT / f"ev_{k:02d}_{r['fol_id']}_{r['lead_id']}.png"
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {p}")

print(f"\n共 {len(sel)} 张，目录 {OUT}")
