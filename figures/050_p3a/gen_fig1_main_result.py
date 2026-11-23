"""图 1：主结果全景（顶刊版 v3）
a  配对斜率：A0 → A2 → A3；Y 轴 0 起不截断；灰细线=单种子，粗横杠=该列中位数
b  八条消息臂的配对差（Arm − A0）逐种子点 + 中位数 + IQR；零线置于数据下层
c  独立的右侧标签栏（绘图区外），给出「10 个种子里有几个下降」与表头，不与数据争空间
数据：recon_050_a2s.json
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = load(F400)

fig = plt.figure(figsize=(W2, 72 * MM))
gs = fig.add_gridspec(1, 3, width_ratios=[1.00, 1.05, 0.15], wspace=0.16)

# ================= Panel a =================
ax = fig.add_subplot(gs[0, 0])
cols = ["A0", "A2", "A3"]
xs = np.arange(len(cols))
vals = {c: series(d, c, "episodes_total") for c in cols}

for s in range(NSEED):
    ax.plot(xs, [vals[c][s] for c in cols], color="#B9B9B9", lw=0.45, alpha=0.9, zorder=1)
for j, c in enumerate(cols):
    col = ARM_STYLE[c][0]
    ax.scatter(np.full(NSEED, j), vals[c], s=8, color=col, marker="o", zorder=3,
               edgecolors="white", linewidths=0.3)
    m = float(np.median(vals[c]))
    ax.hlines(m, j - 0.26, j + 0.26, color=col, lw=1.9, zorder=4)
    ax.text(j, m + 7, f"{m:g}", ha="center", va="bottom", fontsize=BASE - 0.5,
            color=col, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", pad=0.9), zorder=5)

ax.set_xticks(xs)
ax.set_xticklabels(["None", "8 vehicles", "20 vehicles"])
ax.set_xlabel("Message receivers")
ax.set_ylabel("Target-zone events per run")
ax.set_ylim(0, 340)
ax.set_xlim(-0.5, 2.5)
ax.set_yticks([0, 100, 200, 300])

txt = []
for arm in ("A2", "A3"):
    dl = paired(d, arm)
    txt.append(f"{arm}: {int((dl<0).sum())}/10 lower,  $P$ = {sign_test_p(dl):.3f}")
ax.text(0.02, 0.985, "\n".join(txt), transform=ax.transAxes, ha="left", va="top",
        fontsize=BASE - 1.8, linespacing=1.5,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2, alpha=0.9))

leg = [Line2D([], [], color="#B9B9B9", lw=0.6, label="individual seed"),
       Line2D([], [], color="#333333", lw=1.9, label="median")]
ax.legend(handles=leg, frameon=False, loc="lower left",
          bbox_to_anchor=(0.0, -0.02), handlelength=1.5, labelspacing=0.3)
panel_tag(ax, "a")

# ================= Panel b =================
ax = fig.add_subplot(gs[0, 1])
# 分组必须与事实一致：A1 是早报（t_src+0.6、提前量约 90 s），不是短提前量臂
groups = [("Early broadcast", ["A3", "A2", "A2L", "A3L", "A1"]),
          ("Short lead (8 s)", ["A2S"]),
          ("At / after wave", ["A2P", "A3P"])]
order = [a for _, g in groups for a in g]
ypos, y = {}, 0.0
for _, g in groups:
    for a in g:
        ypos[a] = y
        y += 1.0
    y += 0.55

ax.axvline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
rng = np.random.default_rng(0)
for arm in order:
    dl = paired(d, arm)
    col = ARM_STYLE[arm][0]
    yy = ypos[arm]
    q1, med, q3 = np.percentile(dl, [25, 50, 75])
    ax.hlines(yy, q1, q3, color=col, lw=2.6, alpha=0.30, zorder=1)
    ax.scatter(dl, yy + rng.uniform(-0.10, 0.10, NSEED), s=7, color=col, marker="o",
               zorder=3, edgecolors="white", linewidths=0.3)
    ax.plot([med], [yy], marker="|", ms=7.5, color=col, mew=1.8, zorder=4)

ax.set_yticks([ypos[a] for a in order])
ax.set_yticklabels(order)
ax.set_ylim(-0.7, y - 0.10)
ax.set_xlabel("Change in events relative to A0 (per seed)")
ax.set_xlim(-180, 62)
ax.set_xticks([-150, -100, -50, 0, 50])

# 分组分隔与组名
for name, g in groups:
    ax.axhline(ypos[g[-1]] + 0.52, color="#DDDDDD", lw=0.6, zorder=0)
ax.text(-178, y - 0.80, "groups (top to bottom): early broadcast / short lead / at-or-after wave",
        fontsize=BASE - 2, color="#666666", ha="left", va="top")
panel_tag(ax, "b")

# ================= Panel c：独立标签栏 =================
axn = fig.add_subplot(gs[0, 2], sharey=ax)
axn.axis("off")
axn.text(1.0, 1.008, "seeds lower", transform=axn.transAxes, ha="right", va="bottom",
         fontsize=BASE - 1.8, color="#333333")
for arm in order:
    dl = paired(d, arm)
    axn.text(1.0, ypos[arm], f"{int((dl<0).sum())}/10", ha="right", va="center",
             fontsize=BASE - 1.2, color="#222222")
axn.set_ylim(ax.get_ylim())

fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.155)
save(fig, "fig1_main_result", target_mm=183)
