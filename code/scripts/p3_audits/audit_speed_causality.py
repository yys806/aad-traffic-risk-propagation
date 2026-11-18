"""决定性检验：speed 字段是否用了未来帧（是否因果可得）

阶段：P3-B（数据契约·计时因果性）
为什么做：GPT 第四轮指出——标签可以离线用未来帧，预测器不可以。
  即便预测器只读「已发布的 speed」，若该字段在生成时已用了未来帧，
  就不能据此主张「实时提前 1.0 s」。

方法：位置量化 8.8 cm，在 1.0 s 窗下速度不确定度仅 0.088 m/s（可忽略）。
  分别构造三种由位置得到的 1.0 s 平均速度：
    后向  v_back(t) = |p(t) - p(t-1.0)| / 1.0      —— 只用过去
    前向  v_fwd(t)  = |p(t+1.0) - p(t)| / 1.0      —— 只用未来
    居中  v_ctr(t)  = |p(t+0.5) - p(t-0.5)| / 1.0  —— 前后各半
  与 speed(t)/3.6 比较。谁最贴近，speed 就最可能是用哪种窗算的。

第二个检验（更灵敏）：减速起点对齐。
  若 speed 用了未来帧，它的下降会比「后向位置速度」的下降提前出现。
  统计 speed 首次跌破某比例的时刻 与 v_back 首次跌破的时刻之差。
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
lat0, lon0 = 37.9777, 23.7375
DT = 0.04
W = 1.0                    # 长窗，压住量化噪声
K = int(round(W / DT))     # 25 帧
MAX_CARS = 250


def load():
    out = []
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
            if len(v) < 4 * K:
                continue
            out.append({
                "id": r[0].strip(),
                "type": r[1].strip(),
                "lat": v[:, 0], "lon": v[:, 1],
                "speed": v[:, 2] / 3.6,
                "t": v[:, 5],
            })
    return out


cars = load()
print(f"可分析轨迹（长度 ≥ {4*K} 帧 = {4*W:.0f} s）：{len(cars)}")

rng = np.random.default_rng(20261118)
idx = rng.choice(len(cars), size=min(MAX_CARS, len(cars)), replace=False)

print("\n" + "=" * 72)
print("检验一：speed 与三种位置速度的相关（逐车 Spearman，取中位）")
print("=" * 72)
res = {"back": [], "fwd": [], "ctr": []}
rmse = {"back": [], "fwd": [], "ctr": []}

for i in idx:
    c = cars[i]
    x = (c["lon"] - lon0) * 111320.0 * math.cos(math.radians(lat0))
    y = (c["lat"] - lat0) * 110540.0
    s = c["speed"]
    n = len(x)
    lo, hi = 2 * K, n - 2 * K
    if hi - lo < 40:
        continue

    v_back = np.hypot(x[lo:hi] - x[lo - K:hi - K], y[lo:hi] - y[lo - K:hi - K]) / W
    v_fwd = np.hypot(x[lo + K:hi + K] - x[lo:hi], y[lo + K:hi + K] - y[lo:hi]) / W
    v_ctr = np.hypot(x[lo + K // 2:hi + K // 2] - x[lo - K // 2:hi - K // 2],
                     y[lo + K // 2:hi + K // 2] - y[lo - K // 2:hi - K // 2]) / W
    sv = s[lo:hi]

    if sv.std() < 0.5:          # 几乎恒速，无信息
        continue

    from scipy.stats import spearmanr
    for name, vv in (("back", v_back), ("fwd", v_fwd), ("ctr", v_ctr)):
        rho = spearmanr(sv, vv).statistic
        res[name].append(rho)
        rmse[name].append(float(np.sqrt(np.mean((sv - vv) ** 2))))

for name in ("back", "fwd", "ctr"):
    a = np.array(res[name])
    e = np.array(rmse[name])
    print(f"  {name:>5}: Spearman 中位 {np.median(a):.4f}   RMSE 中位 {np.median(e):.3f} m/s   (n={len(a)})")

best = max(("back", "fwd", "ctr"), key=lambda k: np.median(res[k]))
print(f"\n  → 最贴近的是 {best}")

print("\n" + "=" * 72)
print("检验二：减速起点对齐（speed 是否领先于后向位置速度）")
print("=" * 72)
leads = []
for i in idx:
    c = cars[i]
    x = (c["lon"] - lon0) * 111320.0 * math.cos(math.radians(lat0))
    y = (c["lat"] - lat0) * 110540.0
    s = c["speed"]
    n = len(x)
    lo, hi = 2 * K, n - 2 * K
    if hi - lo < 60:
        continue
    v_back = np.hypot(x[lo:hi] - x[lo - K:hi - K], y[lo:hi] - y[lo - K:hi - K]) / W
    sv = s[lo:hi]
    # 找一次明显减速：窗口内最大速度到其后最低速度，降幅 ≥ 3 m/s
    if sv.max() - sv.min() < 3.0:
        continue
    k_peak = int(np.argmax(sv[: len(sv) // 2]))
    tail = sv[k_peak:]
    k_trough = k_peak + int(np.argmin(tail))
    if k_trough - k_peak < 10:
        continue
    drop_s = sv[k_peak] - sv[k_trough]
    if drop_s < 2.0:
        continue
    # 首次跌破 peak - 20% drop 的时刻（两种信号各自）
    thr = sv[k_peak] - 0.2 * drop_s
    ks = k_peak + int(np.argmax(sv[k_peak:k_trough] < thr)) if np.any(sv[k_peak:k_trough] < thr) else None
    thr_b = v_back[k_peak] - 0.2 * (v_back[k_peak] - v_back[k_trough])
    kb = k_peak + int(np.argmax(v_back[k_peak:k_trough] < thr_b)) if np.any(v_back[k_peak:k_trough] < thr_b) else None
    if ks is None or kb is None:
        continue
    leads.append((kb - ks) * DT)      # >0 表示 speed 更早下跌（用了未来帧）

if leads:
    a = np.array(leads)
    print(f"  样本 {len(a)} 次减速")
    print(f"  speed 领先后向位置速度的量（秒）：中位 {np.median(a):+.3f}  p25 {np.percentile(a,25):+.3f}  p75 {np.percentile(a,75):+.3f}")
    print(f"  领先 > 0.1 s 的比例：{100*np.mean(a>0.1):.1f}%")
    print(f"  领先 < -0.1 s 的比例：{100*np.mean(a<-0.1):.1f}%")
    print(f"  → {'speed 明显领先，可能用了未来帧' if np.median(a) > 0.1 else ('speed 滞后或同步，未发现未来帧迹象' if np.median(a) < 0.1 else '无法判定')}")
else:
    print("  没有足够的明显减速样本")
