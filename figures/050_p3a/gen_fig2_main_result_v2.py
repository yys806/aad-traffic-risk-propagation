"""图 2：主结果全景（顶刊版，第二轮）
Panel a — A0→A2→A3 配对斜率图（Y 从 0 起、不截断；灰细线=单种子，粗横杠=中位）
Panel b — 八条消息臂的配对差（Arm−A0）逐种子点图 + 中位/IQR + 零线；n/10 列置于绘图区外右侧
数据：recon_050_a2s.json
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = load(F400)

fig = plt.figure(figsize=(W2, 70 * MM))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.45], wspace=0.50)

# ---------------- Panel a ----------------
ax = fig.add_subplot(gs[0, 0])
cols = ["A0", "A2", "A3"]
xs = np.arange(len(cols))
vals = {c: series(d, c, "episodes_total") for c in cols}

for s in range(NSEED):
    ax.plot(xs, [vals[c][s] for c in cols], color="#C8C8C8", lw=0.45, zorder=1)
for j, c in enumerate(cols):
    col = ARM_STYLE[c][0]
    ax.scatter(np.full(NSEED, j), vals[c], s=8, color=col, marker="o", zorder=3,
               edgecolors="white", linewidths=0.3)
    m = float(np.median(vals[c]))
    ax.hlines(m, j - 0.24, j + 0.24, color=col, lw=1.8, zorder=4)
    ax.text(j + 0.30, m, f"{m:.0f}", ha="left", va="center",
            fontsize=BASE - 0.5, color=col, fontweight="bold")

ax.set_xticks(xs)
ax.set_xticklabels(["None\n(A0)", "8 veh.\n(A2)", "20 veh.\n(A3)"])
ax.set_ylabel("Target-zone events per run")
ax.set_ylim(0, 330)
ax.set_xlim(-0.5, 2.95)
ax.set_yticks([0, 100, 200, 300])

for arm, yy in (("A2", 0.32), ("A3", 0.44)):
    dl = paired(d, arm)
    ax.text(0.03, yy, f"{arm}: {int((dl<0).sum())}/10 seeds lower\n"
                       f"$P$ = {sign_test_p(dl):.3f}",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=BASE - 1.5)

leg = [Line2D([], [], color="#C8C8C8", lw=0.6, label="individual seed"),
       Line2D([], [], color="#444444", lw=1.8, label="median")]
ax.legend(handles=leg, frameon=False, loc="upper right",
          bbox_to_anchor=(1.03, 1.02), handlelength=1.4, labelspacing=0.3)
panel_tag(ax, "a")

# ---------------- Panel b ----------------
ax = fig.add_subplot(gs[0, 1])
order = ["A3", "A2", "A2L", "A3L", "A2S", "A1", "A2P", "A3P"]
ys = np.arange(len(order))[::-1]

ax.axvline(0, color="#9A9A9A", lw=0.6, ls=(0, (3, 2)), zorder=1)
rng = np.random.default_rng(0)
for y, arm in zip(ys, order):
    dl = paired(d, arm)
    col = ARM_STYLE[arm][0]
    q1, med, q3 = np.percentile(dl, [25, 50, 75])
    ax.hlines(y, q1, q3, color=col, lw=2.4, alpha=0.35, zorder=2)
    ax.scatter(dl, y + rng.uniform(-0.11, 0.11, NSEED), s=7, color=col, marker="o",
               zorder=3, edgecolors="white", linewidths=0.3)
    ax.plot([med], [y], marker="|", ms=7.5, color=col, mew=1.7, zorder=4)
    ax.text(1.015, y, f"{int((dl<0).sum())}/10", transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=BASE - 1.2, color="#222222")

ax.set_yticks(ys)
ax.set_yticklabels(order)
ax.set_ylim(-0.65, len(order) - 0.35)
ax.set_xlabel("Change in target-zone events vs A0 (per seed)")
ax.set_xlim(-180, 60)
ax.set_xticks([-150, -100, -50, 0, 50])
ax.text(1.015, len(order) - 0.30, "lower", transform=ax.get_yaxis_transform(),
        ha="right", va="bottom", fontsize=BASE - 1.5, style="italic", color="#555555")
panel_tag(ax, "b")

save(fig, "fig2_main_result")
