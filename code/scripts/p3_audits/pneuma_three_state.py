"""pNEUMA 触发时刻三态判定（Sol 2026-11-18 指定的今天这一步）

阶段：P3-B（结构门槛·主队列入口）
依据：gpt18.md 第 5 节——「从 735 个完整观测候选里抽取一批，把 t0 附近的候选两车和周围
      第三车一起画出来，先判触发时的三态，不用后续 20 s 帮忙判资格。」

三态定义（严格按 gpt18.md 第 3 节）：
  直跟：后车投到「前车截至该时刻已驶过的局部轨迹」上，有符号横向残差在同一窄带；
        两车经过同一位置时切向一致；且两车之间没有第三车占位
  中断：确认有第三车在带内且成为更近的前车
  未知：投影多解、低速方向不稳、前史不足、第三车归属不清

关键纪律：
  - 入组资格只用 t0 及之前的信息，不看 t0 之后
  - 不要因为「数据里没看到第三车」就当作「没有第三车」——本脚本只报告「本帧可见范围内无第三车」
  - 结论叫「同轨迹带直接跟驰」，不叫「同一标线车道」
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
EV = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_pneuma\events_20s_all.json")
OUT = EV.parent

REF_BACK = 5.0        # 用前车 t0 之前多少秒的轨迹作参考曲线
BAND_W = 3.0          # 轨迹带半宽 m（一个车道宽级别）
MIN_SPEED = 2.0       # 低于此速度判「未知」（航向不稳）
SAMPLE = 40           # 抽多少事件做首轮

# ---------- 读轨迹 ----------
evs = json.loads(EV.read_text(encoding="utf-8"))
print(f"候选事件 {len(evs)} 个")

want = {e["lead_id"] for e in evs} | {e["fol_id"] for e in evs}
traj = {}
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
        rec = {"t": t, "lat": lat, "lon": lon, "v": sp}
        tid = r[0].strip()
        if tid in want:
            traj[tid] = rec
        allcars[tid] = rec

lat0 = 37.9777
lon0 = 23.7375


def to_xy(lat, lon):
    return ((lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            (lat - lat0) * 110540.0)


for d in allcars.values():
    d["x"], d["y"] = to_xy(d["lat"], d["lon"])

print(f"相关车 {len(traj)}，全部车 {len(allcars)}")


def at(rec, t):
    if t < rec["t"][0] - 0.5 or t > rec["t"][-1] + 0.5:
        return None
    return (float(np.interp(t, rec["t"], rec["x"])),
            float(np.interp(t, rec["t"], rec["y"])),
            float(np.interp(t, rec["t"], rec["v"])))


def project(px, py, curve):
    """投影到折线，返回 (沿程里程 s, 有符号横向残差 e)"""
    best = (1e18, 0.0, 0.0)
    acc = 0.0
    for (x1, y1), (x2, y2) in zip(curve[:-1], curve[1:]):
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (L * L)))
        cx, cy = x1 + t * dx, y1 + t * dy
        d = math.hypot(px - cx, py - cy)
        if d < best[0]:
            # 有符号：叉积正负
            cross = dx * (py - y1) - dy * (px - x1)
            best = (d, acc + t * L, math.copysign(d, cross))
        acc += L
    return best[1], best[2], best[0]


# ---------- 逐事件判三态 ----------
rows = []
rng = np.random.default_rng(20261118)
idx_sample = rng.choice(len(evs), size=min(SAMPLE, len(evs)), replace=False)

for i in sorted(idx_sample):
    e = evs[i]
    t0 = e["t"]
    gl, gf = traj.get(e["lead_id"]), traj.get(e["fol_id"])
    if gl is None or gf is None:
        rows.append({**e, "state": "未知", "why": "轨迹缺失"})
        continue
    fl = at(gl, t0)
    ff = at(gf, t0)
    if fl is None or ff is None:
        rows.append({**e, "state": "未知", "why": "t0 插值越界"})
        continue
    v_fol = ff[2]
    if v_fol < MIN_SPEED:
        rows.append({**e, "state": "未知", "why": f"后车低速 {v_fol:.1f} m/s，航向不稳"})
        continue

    # 参考曲线：前车 t0-REF_BACK → t0 的已驶过轨迹
    m = (gl["t"] >= t0 - REF_BACK) & (gl["t"] <= t0)
    if m.sum() < 5:
        rows.append({**e, "state": "未知", "why": "前车前史不足"})
        continue
    curve = np.column_stack([gl["x"][m], gl["y"][m]])
    s_end = 0.0
    for (x1, y1), (x2, y2) in zip(curve[:-1], curve[1:]):
        s_end += math.hypot(x2 - x1, y2 - y1)

    s_f, e_f, d_f = project(ff[0], ff[1], curve)

    # 第三车：t0 时刻所有车，投影落在 (s_f, s_end) 且带内
    third = []
    for tid, rec in allcars.items():
        if tid in (e["lead_id"], e["fol_id"]):
            continue
        p = at(rec, t0)
        if p is None:
            continue
        s_o, e_o, d_o = project(p[0], p[1], curve)
        if s_f + 0.5 < s_o < s_end - 0.5 and abs(e_o) <= BAND_W and abs(e_f - e_o) <= 2 * BAND_W:
            third.append((tid, round(s_o - s_f, 1), round(e_o, 1)))

    in_band = abs(e_f) <= BAND_W
    if third:
        state, why = "中断", f"带内有第三车 {len(third)} 辆"
    elif in_band:
        state, why = "直跟", f"横向残差 {e_f:+.2f} m，带内无第三车"
    else:
        state, why = "未知", f"横向残差 {e_f:+.2f} m 超出带宽"

    rows.append({**e, "state": state, "why": why,
                 "e_m": round(e_f, 2), "s_fol": round(s_f, 1), "s_lead": round(s_end, 1),
                 "third": third[:3], "v_fol": round(v_fol, 1)})

# ---------- 汇总 ----------
from collections import Counter
c = Counter(r["state"] for r in rows)
print(f"\n=== 触发时刻三态（抽样 {len(rows)} 个）===")
for k in ("直跟", "中断", "未知"):
    print(f"  {k}: {c.get(k,0)} 个 ({100*c.get(k,0)/max(len(rows),1):.0f}%)")

print(f"\n{'后车':>5} {'前车':>5} {'t0':>7} {'态':>4} {'横向残差':>9} {'带内第三车':>10}  原因")
print("-" * 90)
for r in rows[:30]:
    print(f"{r['fol_id']:>5} {r['lead_id']:>5} {r['t']:>7.1f} {r['state']:>4} "
          f"{r.get('e_m',float('nan')):>9.2f} {len(r.get('third',[])):>10}  {r['why']}")

(OUT / "three_state.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n结果：{OUT/'three_state.json'}")
