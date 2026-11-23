"""图 2：主结果全景
Panel a — A0 → A2 → A3 配对斜率图（Y 轴从 0 起，不截断，防“夸大差异”指控）
Panel b — 八条消息臂的配对差（Arm − A0）逐种子点图 + 中位/IQR + 零线
数据：recon_050_a2s.json（九臂 × 10 种子，400 s）
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt

d = load(F400)

fig = plt.figure(figsize=(W2, 68 * MM))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.55], wspace=0.42)

# ---------------- Panel a：配对斜率 ----------------
ax = fig.add_subplot(gs[0, 0])
cols = ["A0", "A2", "A3"]
xs = np.arange(len(cols))
vals = {c: series(d, c, "episodes_total") for c in cols}

for s in range(NSEED):
    ax.plot(xs, [vals[c][s] for c in cols], color="#BBBBBB", lw=0.5, zorder=1)
for j, c in enumerate(cols):
    col, mk, _ = ARM_STYLE[c]
    ax.scatter(np.full(NSEED, j), vals[c], s=7, color=col, marker=mk, zorder=3,
               edgecolors="white", linewidths=0.25)
    m = float(np.median(vals[c]))
    ax.hlines(m, j - 0.22, j + 0.22, color=col, lw=1.6, zorder=4)
    ax.text(j, m + 9, f"{m:.0f}", ha="center", va="bottom", fontsize=BASE - 1, color=col)

ax.set_xticks(xs)
ax.set_xticklabels(["No message\n(A0)", "8 vehicles\n(A2)", "20 vehicles\n(A3)"])
ax.set_ylabel("Target-zone events per run")
ax.set_ylim(0, 320)                      # 强制从 0 起，不截断
ax.set_xlim(-0.45, 2.45)

pa = sign_test_p(paired(d, "A2")); pb = sign_test_p(paired(d, "A3"))
ax.text(0.5, 0.965, f"A0→A2  {int((paired(d,'A2')<0).sum())}/10 down, {significance_text(pa)}",
        transform=ax.transAxes, ha="center", va="top", fontsize=BASE - 1.5)
ax.text(0.5, 0.895, f"A0→A3  {int((paired(d,'A3')<0).sum())}/10 down, {significance_text(pb)}",
        transform=ax.transAxes, ha="center", va="top", fontsize=BASE - 1.5)
panel_tag(ax, "a")

# ---------------- Panel b：配对差 ----------------
ax = fig.add_subplot(gs[0, 1])
order = ["A3", "A2", "A2L", "A3L", "A2S", "A1", "A2P", "A3P"]
ys = np.arange(len(order))[::-1]

ax.axvline(0, color="#666666", lw=0.6, ls="-", zorder=1)
for y, arm in zip(ys, order):
    dlt = paired(d, arm)
    col, mk, _ = ARM_STYLE[arm]
    q1, med, q3 = np.percentile(dlt, [25, 50, 75])
    ax.hlines(y, q1, q3, color=col, lw=2.2, alpha=0.45, zorder=2)
    rng = np.random.default_rng(0)
    ax.scatter(dlt, y + rng.uniform(-0.13, 0.13, NSEED), s=7, color=col, marker=mk,
               zorder=3, edgecolors="white", linewidths=0.25)
    ax.plot([med], [y], marker="|", ms=8, color=col, mew=1.8, zorder=4)
    n_down = int((dlt < 0).sum())
    ax.text(ax.get_xlim()[0], y, "", fontsize=BASE - 1)
    ax.text(6, y, f"{n_down}/10", va="center", ha="left", fontsize=BASE - 1.5, color=col)

ax.set_yticks(ys)
ax.set_yticklabels(order)
ax.set_xlabel("Change in target-zone events vs no-message (A0), per seed")
ax.set_xlim(-175, 70)
ax.text(6, len(order) - 0.35, "down", fontsize=BASE - 1.5, style="italic")
panel_tag(ax, "b")

save(fig, "fig2_main_result")
