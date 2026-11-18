"""pNEUMA 两张表：事件表（全量）+ 帧级三态表（抽样）

阶段：P3-B（结构门槛·输出两张表）
依据：gpt18.md 第 4 节第 3 步——「一张事件表，列触发时资格、两车可观测时长和结束原因；
      一张帧级表，列三态、当前直接前车 ID 和判定原因。用它们重新统计入组数、完整观测数、
      确认中断数、含未知数和严格持续数。不要拿 26 或 25 当复现目标。」

纪律：
  - 触发时资格只用 t0 及之前的信息
  - 帧级三态逐帧保留时间轴，未知帧不删
  - 「带内无第三车」只代表本帧可见范围内没有，不等于客观不存在
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
import os as _os
_TIER = _os.environ.get("TIER", "m10")
EV = Path("D:/shen/TJU/AAD/code/outputs/analysis/P3B_pneuma_" + _TIER + "/events_20s_all.json")
OUT = EV.parent

REF_BACK = 5.0
BAND_W = 3.0
MIN_SPEED = 2.0
GRID = 0.1
FRAME_SAMPLE = 40

lat0, lon0 = 37.9777, 23.7375

print("读轨迹 ...", flush=True)
evs = json.loads(EV.read_text(encoding="utf-8"))
want = {e["lead_id"] for e in evs} | {e["fol_id"] for e in evs}
allcars = {}
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    next(rd)
    for r in rd:
        if len(r) < 16:
            continue
        try:
            vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
        except ValueError:
            continue
        n = len(vals) // 6
        v = vals[: n * 6].reshape(n, 6)
        o = np.argsort(v[:, 5])
        t, lat, lon, sp = v[o, 5], v[o, 0], v[o, 1], v[o, 2]
        allcars[r[0].strip()] = {
            "t": t,
            "x": (lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            "y": (lat - lat0) * 110540.0,
            "v": sp,
        }
print(f"  车辆 {len(allcars)}，候选事件 {len(evs)}", flush=True)


def at(rec, t):
    if t < rec["t"][0] or t > rec["t"][-1]:
        return None
    return (float(np.interp(t, rec["t"], rec["x"])),
            float(np.interp(t, rec["t"], rec["y"])),
            float(np.interp(t, rec["t"], rec["v"])))


def build_curve(rec, t_from, t_to):
    m = (rec["t"] >= t_from) & (rec["t"] <= t_to)
    if m.sum() < 2:
        return None
    return np.column_stack([rec["x"][m], rec["y"][m]])


def project(px, py, curve):
    best = (1e18, 0.0, 0.0)
    acc = 0.0
    for (x1, y1), (x2, y2) in zip(curve[:-1], curve[1:]):
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (L * L)))
        cx, cy = x1 + tt * dx, y1 + tt * dy
        d = math.hypot(px - cx, py - cy)
        if d < best[0]:
            cross = dx * (py - y1) - dy * (px - x1)
            best = (d, acc + tt * L, math.copysign(d, cross))
        acc += L
    return best[1], best[2], best[0]


# ---------- 表一：事件表（全量 735） ----------
print("\n生成事件表 ...", flush=True)
ev_rows = []
for i, e in enumerate(evs):
    gl, gf = allcars.get(e["lead_id"]), allcars.get(e["fol_id"])
    if gl is None or gf is None:
        ev_rows.append({"idx": i, **e, "t0_state": "未知", "t0_why": "轨迹缺失",
                        "obs_20s": 0.0, "end_reason": "数据缺失"})
        continue
    t0 = e["t"]
    fl, ff = at(gl, t0), at(gf, t0)
    if fl is None or ff is None:
        ev_rows.append({"idx": i, **e, "t0_state": "未知", "t0_why": "越界",
                        "obs_20s": 0.0, "end_reason": "越界"})
        continue
    state, why, e_m = "未知", "", None
    if ff[2] < MIN_SPEED:
        why = f"后车低速 {ff[2]:.1f}"
    else:
        curve = build_curve(gl, t0 - REF_BACK, t0)
        if curve is None:
            why = "前车前史不足"
        else:
            s_f, e_f, _ = project(ff[0], ff[1], curve)
            e_m = round(e_f, 2)
            s_end = sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(curve[:-1], curve[1:]))
            third = 0
            for tid, rec in allcars.items():
                if tid in (e["lead_id"], e["fol_id"]):
                    continue
                p = at(rec, t0)
                if p is None:
                    continue
                s_o, e_o, _ = project(p[0], p[1], curve)
                if s_f + 0.5 < s_o < s_end - 0.5 and abs(e_o) <= BAND_W:
                    third += 1
            if third:
                state, why = "中断", f"带内第三车 {third}"
            elif abs(e_f) <= BAND_W:
                state, why = "直跟", f"残差 {e_f:+.2f} m"
            else:
                why = f"残差 {e_f:+.2f} m 超带宽"
    # 可观测时长与结束原因
    t_lo = max(gl["t"][0], gf["t"][0], t0)
    t_hi = min(gl["t"][-1], gf["t"][-1], t0 + 20.0)
    obs = max(0.0, t_hi - t_lo)
    if t_hi - t0 >= 19.9:
        end = "满 20 s"
    elif gl["t"][-1] < t0 + 20.0 and gl["t"][-1] <= gf["t"][-1]:
        end = "前车离开视野"
    elif gf["t"][-1] < t0 + 20.0:
        end = "后车离开视野"
    else:
        end = "其他"
    ev_rows.append({"idx": i, **e, "t0_state": state, "t0_why": why, "e_m": e_m,
                    "obs_20s": round(obs, 1), "end_reason": end})

(OUT / "table_events.csv").write_text(
    "\n".join([",".join(ev_rows[0].keys())] +
              [",".join(str(r.get(k, "")) for k in ev_rows[0].keys()) for r in ev_rows]),
    encoding="utf-8-sig")
from collections import Counter
cs = Counter(r["t0_state"] for r in ev_rows)
ce = Counter(r["end_reason"] for r in ev_rows)
print(f"  事件表 {len(ev_rows)} 行")
print(f"  触发时三态：直跟 {cs.get('直跟',0)}  中断 {cs.get('中断',0)}  未知 {cs.get('未知',0)}")
print(f"  结束原因：{dict(ce)}")

# ---------- 表二：帧级三态（抽 40 个事件） ----------
print("\n生成帧级表（抽 40 个事件）...", flush=True)
rng = np.random.default_rng(20261118)
pick = rng.choice(len(evs), size=min(FRAME_SAMPLE, len(evs)), replace=False)
fr_rows = []
for i in sorted(pick):
    e = evs[i]
    gl, gf = allcars.get(e["lead_id"]), allcars.get(e["fol_id"])
    if gl is None or gf is None:
        continue
    t0 = e["t"]
    t_hi = min(t0 + 20.0, gl["t"][-1], gf["t"][-1])
    for t in np.arange(t0, t_hi, GRID):
        fl, ff = at(gl, t), at(gf, t)
        if fl is None or ff is None:
            fr_rows.append({"event": i, "t": round(t - t0, 2), "state": "未知",
                            "lead_id": e["lead_id"], "cur_lead": "", "why": "数据缺"})
            continue
        if ff[2] < MIN_SPEED:
            fr_rows.append({"event": i, "t": round(t - t0, 2), "state": "未知",
                            "lead_id": e["lead_id"], "cur_lead": "", "why": "低速航向不稳"})
            continue
        curve = build_curve(gl, t0 - REF_BACK, t)
        if curve is None:
            fr_rows.append({"event": i, "t": round(t - t0, 2), "state": "未知",
                            "lead_id": e["lead_id"], "cur_lead": "", "why": "前史不足"})
            continue
        s_f, e_f, _ = project(ff[0], ff[1], curve)
        s_end = sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(curve[:-1], curve[1:]))
        best_other, best_s = "", None
        for tid, rec in allcars.items():
            if tid in (e["lead_id"], e["fol_id"]):
                continue
            p = at(rec, t)
            if p is None:
                continue
            s_o, e_o, _ = project(p[0], p[1], curve)
            if s_f + 0.5 < s_o < s_end - 0.5 and abs(e_o) <= BAND_W:
                if best_s is None or s_o > best_s:
                    best_s, best_other = s_o, tid
        if best_other:
            st, why = "中断", f"第三车 {best_other}"
        elif abs(e_f) <= BAND_W:
            st, why = "直跟", f"残差 {e_f:+.2f}"
        else:
            st, why = "未知", f"残差 {e_f:+.2f}"
        fr_rows.append({"event": i, "t": round(t - t0, 2), "state": st,
                        "lead_id": e["lead_id"], "cur_lead": best_other or e["lead_id"], "why": why})

(OUT / "table_frames.csv").write_text(
    "\n".join([",".join(fr_rows[0].keys())] +
              [",".join(str(r.get(k, "")) for k in fr_rows[0].keys()) for r in fr_rows]),
    encoding="utf-8-sig")
csf = Counter(r["state"] for r in fr_rows)
print(f"  帧级表 {len(fr_rows)} 行")
print(f"  帧级三态：直跟 {csf.get('直跟',0)}  中断 {csf.get('中断',0)}  未知 {csf.get('未知',0)}"
      f"  (占比 {100*csf.get('直跟',0)/max(len(fr_rows),1):.0f}% / "
      f"{100*csf.get('中断',0)/max(len(fr_rows),1):.0f}% / "
      f"{100*csf.get('未知',0)/max(len(fr_rows),1):.0f}%)")

print(f"\n两张表：{OUT/'table_events.csv'}  {OUT/'table_frames.csv'}")
