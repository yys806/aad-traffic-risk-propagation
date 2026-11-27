"""PPT 专用：只画主结果面板（配对斜率 A0→A2→A3），字号按投影放大。
右面板（八臂全景）不放这一页——它信息密度高，投影必糊，留给备份页/论文图。
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
import os
os.environ["AAD_FIG_MODE"] = "ppt"
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = load(F400)

fig = plt.figure(figsize=(232 * MM, 84 * MM))
ax = fig.add_axes([0.095, 0.235, 0.875, 0.655])

cols = ["A0", "A2", "A3"]
xs = np.arange(len(cols))
vals = {c: series(d, c, "episodes_total") for c in cols}

for s in range(NSEED):
    ax.plot(xs, [vals[c][s] for c in cols], color="#9A9A9A", lw=1.1, zorder=1)

for j, c in enumerate(cols):
    col = ARM_STYLE[c][0]
    ax.scatter(np.full(NSEED, j), vals[c], s=28, color=col, marker="o", zorder=3,
               edgecolors="white", linewidths=0.7)
    m = float(np.median(vals[c]))
    ax.hlines(m, j - 0.26, j + 0.26, color=col, lw=3.2, zorder=4)
    # 标签放柱子旁侧、不压散点；最右一组放左侧，避免出画布
    _r = j < (len(xs) - 1)
    ax.text(j + (0.22 if _r else -0.22), m, f"{m:g}",
            ha="left" if _r else "right", va="center", fontsize=BASE - 0.5,
            color=col, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.2, alpha=0.95), zorder=5)

ax.set_xticks(xs)
ax.set_xticklabels(["No message", "8 vehicles", "20 vehicles"])
ax.set_xlabel("Message receivers")
ax.set_ylabel("Target-zone events\nper run")
ax.set_ylim(0, 330)
ax.set_xlim(-0.55, 2.55)
ax.set_yticks([0, 100, 200, 300])

_t = []
for arm in ("A2", "A3"):
    dl = paired(d, arm)
    _n = {"A2": "8 vehicles", "A3": "20 vehicles"}[arm]
    _t.append(f"vs No message, {_n}: {int((dl<0).sum())}/10 runs lower,  $P$ = {sign_test_p(dl):.3f}")
# 放到图下方（figure 坐标），两行分开放，避免横向出界
fig.text(0.085, 0.060, _t[0], ha="left", va="bottom",
         fontsize=BASE - 2.8, color="#222222")
fig.text(0.085, 0.012, _t[1], ha="left", va="bottom",
         fontsize=BASE - 2.8, color="#222222")

leg = [Line2D([], [], color="#9A9A9A", lw=1.1, label="one seed"),
       Line2D([], [], color="#333333", lw=3.0, label="group median (colour = arm)")]
ax.legend(handles=leg, frameon=False, loc="upper right",
          bbox_to_anchor=(1.02, 1.0), handlelength=1.5, labelspacing=0.35,
          fontsize=BASE - 1.8)

save(fig, "fig_main_only")