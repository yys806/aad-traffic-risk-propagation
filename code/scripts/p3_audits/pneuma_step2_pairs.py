"""pNEUMA 资格盘点·第 2-4 步：车对窗口 + 急刹 + 20 秒后窗

阶段：P3-B（数据资格盘点）｜ 依据：GPT 2026-11-18（gpt15.md 第 2 节）

pNEUMA 不提供 Leader_ID，前后车关系必须自己算：
  对每个时刻，为一辆车找「沿本车朝向、正前方、距离最近」的另一辆车作为前车。
  朝向用相邻采样点的位移方向估计。

四步法的后三步：
  2. 找急刹（前车平滑纵向减速度 ≤ −3 m/s²），分母是全部可识别车对的急刹
  3. 对每个急刹，统计 5/10/15/20 s 时两车是否都还被连续观测、且仍保持跟驰关系
  4. 汇总：急刹总数 → 有效 20 s 车对数 → 达暴露门槛数
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
MAX_GAP = 0.5
GRID = 0.1              # 公共时间网格 s
BRAKE_THR = -3.0        # 急刹阈值 m/s²
SMOOTH = 5              # 平滑点数（0.5 s）
NEAR_MAX = 60.0         # 前车最大距离 m
LAT_M, LON_M = 110540.0, 111320.0

# ---------- 解析 ----------
traj = {}
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    next(rd)
    for r in rd:
        if len(r) < 16:
            continue
        try:
            tid = r[0].strip()
            vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
        except ValueError:
            continue
        n = len(vals) // 6
        v = vals[: n * 6].reshape(n, 6)
        t, lat, lon, sp = v[:, 5], v[:, 0], v[:, 1], v[:, 2]
        o = np.argsort(t)
        traj[tid] = {"t": t[o], "lat": lat[o], "lon": lon[o], "v": sp[o], "type": r[1].strip()}

print(f"车辆 {len(traj)}")
lat0 = np.mean([d["lat"].mean() for d in traj.values()])
lon0 = np.mean([d["lon"].mean() for d in traj.values()])
for d in traj.values():
    d["x"] = (d["lon"] - lon0) * LON_M * np.cos(np.radians(lat0))
    d["y"] = (d["lat"] - lat0) * LAT_M

# ---------- 公共网格 ----------
t_min = min(d["t"].min() for d in traj.values())
t_max = max(d["t"].max() for d in traj.values())
grid = np.arange(t_min, t_max, GRID)
print(f"时间 {t_min:.0f}–{t_max:.0f} s，网格 {len(grid)} 帧")

ids = list(traj)
X = np.full((len(grid), len(ids)), np.nan, dtype=np.float32)
Y = np.full_like(X, np.nan)
V = np.full_like(X, np.nan)
for j, k in enumerate(ids):
    d = traj[k]
    X[:, j] = np.interp(grid, d["t"], d["x"], left=np.nan, right=np.nan)
    Y[:, j] = np.interp(grid, d["t"], d["y"], left=np.nan, right=np.nan)
    V[:, j] = np.interp(grid, d["t"], d["v"], left=np.nan, right=np.nan)
# 超出原始时间范围的置 NaN（np.interp 会外推端点值）
for j, k in enumerate(ids):
    d = traj[k]
    out = (grid < d["t"][0]) | (grid > d["t"][-1])
    X[out, j] = np.nan

# ---------- 逐帧找前车 ----------
print("逐帧配对 ...")
pairs = []      # (frame, lead_idx, fol_idx, gap, closing, D)
for i in range(len(grid)):
    xs, ys, vs = X[i], Y[i], V[i]
    live = np.where(np.isfinite(xs) & np.isfinite(vs))[0]
    if len(live) < 2:
        continue
    px, py, pv = xs[live], ys[live], vs[live]
    n = len(live)
    dx = px[None, :] - px[:, None]
    dy = py[None, :] - py[:, None]
    dist = np.hypot(dx, dy)
    np.fill_diagonal(dist, np.inf)
    # 朝向：本帧到下一帧的位移
    j2 = min(i + 1, len(grid) - 1)
    hx = X[j2, live] - px
    hy = Y[j2, live] - py
    hn = np.hypot(hx, hy)
    hn[hn < 1e-3] = np.nan
    hx, hy = hx / hn, hy / hn
    # 投影到本车朝向（>0 表示在前方）
    proj = dx * hx[:, None] + dy * hy[:, None]
    proj[proj <= 0.5] = np.inf          # 只保留前方
    dist_masked = np.where(np.isfinite(proj) & (proj < NEAR_MAX), dist, np.inf)
    k = np.argmin(dist_masked, axis=1)
    ok = np.isfinite(dist_masked[np.arange(n), k])
    for a in np.where(ok)[0]:
        b = k[a]
        gap = dist_masked[a, b]
        closing = pv[a] - pv[b]
        D = max(closing, 0.0) ** 2 / (2 * max(gap, 0.5))
        pairs.append((i, live[b], live[a], gap, closing, D))

P = np.array(pairs)
print(f"车-帧配对 {len(P):,} 条，涉及 {len(set(P[:, 2].astype(int)))} 辆后车")

# ---------- 找急刹（前车平滑减速度） ----------
print("找急刹 ...")
# 按「后车 + 前车」分组跨帧追踪；原先误用「帧号 + 后车」，导致每组只有一帧
pair_key = P[:, 2].astype(int) * 100000 + P[:, 1].astype(int)
order = np.lexsort((P[:, 0], pair_key))
P = P[order]; pair_key = pair_key[order]
newpair = np.r_[True, pair_key[1:] != pair_key[:-1]]
# 帧号跳跃超过 3 帧（0.3 s）也算断开
frame_jump = np.r_[True, np.diff(P[:, 0].astype(int)) > 3]
pair_uid = np.cumsum(newpair | frame_jump)

brakes = []
for u in np.unique(pair_uid):
    m = pair_uid == u
    if m.sum() < 20:
        continue
    fr = P[m, 0].astype(int)
    lead = P[m, 1].astype(int)
    lid = lead[0]
    v_lead = V[fr, lid]
    good = np.isfinite(v_lead)
    if good.sum() < 20:
        continue
    vs = np.convolve(v_lead[good], np.ones(SMOOTH) / SMOOTH, mode="same")
    acc = np.gradient(vs, GRID)
    kk = np.where(acc <= BRAKE_THR)[0]
    if len(kk) == 0:
        continue
    # 合并同一次制动：减速度跌破阈值后，到它回升到 -1 以上才算结束
    kk = np.where(acc <= BRAKE_THR)[0]
    ends = np.where(acc > -1.0)[0]
    k0 = int(kk[0])
    after = ends[ends > k0]
    k1 = int(after[0]) if len(after) else len(acc) - 1
    if k1 - k0 < int(1.0 / GRID):      # 太短，不算一次制动（<1 s）
        continue
    brakes.append({"frame": fr[good][k0], "last": fr[good][k1], "lead": lid,
                   "fol": int(P[m, 2][0]), "acc_min": float(acc[k0:k1+1].min()),
                   "gap": float(P[m, 3][good][k0])})

print(f"急刹事件（前车平滑减速度 ≤ {BRAKE_THR}）：{len(brakes)} 个")

# ---------- 急刹后两车是否仍可观测 ----------
print("\n急刹后窗口可观测性：")
print(f"{'窗口':>6} {'两车都在':>10} {'仍在跟驰':>10}")
for post in (5, 10, 15, 20):
    both = keep = 0
    for e in brakes:
        f0 = e["frame"]
        n_need = int(post / GRID)
        if f0 + n_need >= len(grid):
            continue
        seg = slice(f0, f0 + n_need)
        okL = np.isfinite(X[seg, e["lead"]]).all()
        okF = np.isfinite(X[seg, e["fol"]]).all()
        if okL and okF:
            both += 1
            # 仍跟驰：这段时间里后车最近的前车一直是它
            same = 0
            for i in range(f0, f0 + n_need):
                xs, ys = X[i], Y[i]
                live = np.where(np.isfinite(xs) & np.isfinite(V[i]))[0]
                if e["fol"] not in live:
                    continue
                p = live
                dx = xs[p] - xs[e["fol"]]
                dy = ys[p] - ys[e["fol"]]
                dist = np.hypot(dx, dy)
                dist[p == e["fol"]] = np.inf
                j2 = min(i + 1, len(grid) - 1)
                hx = X[j2, e["fol"]] - xs[e["fol"]]
                hy = Y[j2, e["fol"]] - ys[e["fol"]]
                hn = np.hypot(hx, hy)
                if hn < 1e-3:
                    continue
                proj = (dx * hx + dy * hy) / hn
                proj[proj <= 0.5] = np.inf
                cand = np.where((proj < NEAR_MAX) & np.isfinite(dist))[0]
                if len(cand) == 0:
                    continue
                best = cand[np.argmin(dist[cand])]
                if p[best] == e["lead"]:
                    same += 1
            if same >= 0.8 * n_need:      # 允许 20% 的帧被插车或抖动
                keep += 1
    print(f"{post:>5}s {both:>10} {keep:>10}")

print(f"\n总计：急刹 {len(brakes)} 个；这是 1 架无人机 30 分钟的数据，全库有 10 架 × 5 天 × 5 场。")

# ---------- 保存 20 s 合格候选事件（供车道验收） ----------
import json as _json
from pathlib import Path as _Path
OUT = _Path("D:/shen/TJU/AAD/code/outputs/analysis/P3B_pneuma")
OUT.mkdir(parents=True, exist_ok=True)
n_need = int(20.0 / GRID)
saved = []
for e in brakes:
    f0 = e["frame"]
    if f0 + n_need >= len(grid):
        continue
    seg = slice(f0, f0 + n_need)
    if not (np.isfinite(X[seg, e["lead"]]).all() and np.isfinite(X[seg, e["fol"]]).all()):
        continue
    same = 0
    for i in range(f0, f0 + n_need):
        xs, ys = X[i], Y[i]
        live = np.where(np.isfinite(xs) & np.isfinite(V[i]))[0]
        if e["fol"] not in live:
            continue
        dx = xs[live] - xs[e["fol"]]
        dy = ys[live] - ys[e["fol"]]
        dist = np.hypot(dx, dy)
        dist[live == e["fol"]] = np.inf
        j2 = min(i + 1, len(grid) - 1)
        hx = X[j2, e["fol"]] - xs[e["fol"]]
        hy = Y[j2, e["fol"]] - ys[e["fol"]]
        hn = np.hypot(hx, hy)
        if hn < 1e-3:
            continue
        proj = (dx * hx + dy * hy) / hn
        proj[proj <= 0.5] = np.inf
        cand = np.where((proj < NEAR_MAX) & np.isfinite(dist))[0]
        if len(cand) == 0:
            continue
        if live[cand[np.argmin(dist[cand])]] == e["lead"]:
            same += 1
    saved.append({
        "lead_id": ids[e["lead"]], "fol_id": ids[e["fol"]],
        "frame": int(f0), "t": round(float(grid[f0]), 2),
        "acc_min": round(float(e["acc_min"]), 3),
        "gap": round(float(e["gap"]), 2),
        "same_frac": round(same / n_need, 3),
    })
(OUT / "events_20s_all.json").write_text(_json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"已保存 {len(saved)} 个「20 s 两车都在」候选事件 -> {OUT/'events_20s_all.json'}")
print(f"其中 80% 跟驰命中 {sum(1 for x in saved if x['same_frac']>=0.8)} 个")
