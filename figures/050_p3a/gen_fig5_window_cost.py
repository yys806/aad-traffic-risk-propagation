"""图 5：时间窗稳健性与代价（两路都认为必须补的一张）
a  400 s vs 600 s：早报两臂的降幅方向是否稳住；同时露出剂量倒挂
b  延误（车·秒）在 400 s 与 600 s 的配对差 —— 400 s 的优势是不是截断瞬态
c  最小净距：A2 有个种子比对照最坏值更差
数据：recon_050_a2s.json（400 s）、recon_050_window600c.json（600 s）
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d4 = load(F400)
d6 = load(r"D:/shen/TJU/AAD/code/scripts/hdm/recon_050_window600c.json")

fig = plt.figure(figsize=(W2, 66 * MM))
gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.0, 1.0], wspace=0.40)

# ---------------- a：400 vs 600 相对降幅 ----------------
ax = fig.add_subplot(gs[0, 0])
arms = ["A2", "A3", "A2L", "A3L"]
xs = np.arange(len(arms))
w = 0.34
r4 = [d4["summary"][a]["rel"] * 100 for a in arms]
r6 = [d6["summary"][a]["rel"] * 100 for a in arms]
ax.axhline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
ax.bar(xs - w / 2, r4, width=w, color="#5D6D7E", edgecolor="white", linewidth=0.3,
       label="400 s window", zorder=2)
ax.bar(xs + w / 2, r6, width=w, color="#AEB6BF", edgecolor="#333333", linewidth=0.35,
       hatch="///", label="600 s window", zorder=2)
for j in xs:
    ax.text(j - w / 2, r4[j] - 2.4, f"{r4[j]:.1f}", ha="center", va="top", fontsize=BASE - 2.5)
    ax.text(j + w / 2, r6[j] - 2.4, f"{r6[j]:.1f}", ha="center", va="top", fontsize=BASE - 2.5)
ax.set_xticks(xs)
ax.set_xticklabels(arms)
ax.set_ylabel("Change vs A0 (%)")
ax.set_ylim(-62, 6)
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, -0.02), handlelength=1.2)
panel_tag(ax, "a")

# ---------------- b：延误配对差 400 vs 600 ----------------
ax = fig.add_subplot(gs[0, 1])
arms_b = ["A2", "A3", "A2S"]
xs = np.arange(len(arms_b))
dl4, dl6 = [], []
for a in arms_b:
    v4 = series(d4, a, "delay") - series(d4, "A0", "delay")
    v6 = series(d6, a, "delay") - series(d6, "A0", "delay")
    dl4.append(float(np.median(v4))); dl6.append(float(np.median(v6)))
ax.axhline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
ax.bar(xs - w / 2, dl4, width=w, color="#5D6D7E", edgecolor="white", linewidth=0.3, zorder=2)
ax.bar(xs + w / 2, dl6, width=w, color="#AEB6BF", edgecolor="#333333", linewidth=0.35,
       hatch="///", zorder=2)
for j, (a, b) in enumerate(zip(dl4, dl6)):
    ax.text(j - w / 2, a + (1.6 if a >= 0 else -1.6), f"{a:+.1f}", ha="center",
            va="bottom" if a >= 0 else "top", fontsize=BASE - 2.5)
    ax.text(j + w / 2, b + (1.6 if b >= 0 else -1.6), f"{b:+.1f}", ha="center",
            va="bottom" if b >= 0 else "top", fontsize=BASE - 2.5)
ax.set_xticks(xs)
ax.set_xticklabels(arms_b)
ax.set_ylabel("Delay change vs A0\n(vehicle·seconds, median)")
ax.set_ylim(-52, 14)
panel_tag(ax, "b")

# ---------------- c：最小净距 ----------------
ax = fig.add_subplot(gs[0, 2])
arms_c = ["A0", "A2", "A3", "A2S"]
mins = [float(series(d4, a, "min_gap").min()) for a in arms_c]
argm = [int(series(d4, a, "min_gap").argmin()) for a in arms_c]
cols = [ARM_STYLE[a][0] for a in arms_c]
ax.bar(range(len(arms_c)), mins, color=cols, width=0.6, edgecolor="white", linewidth=0.3)
for i, (v, s) in enumerate(zip(mins, argm)):
    ax.text(i, v + 0.03, f"{v:.3f}\n(seed {s})", ha="center", va="bottom", fontsize=BASE - 2.5)
ax.axhline(min(mins), color="#B03A2E", lw=0.6, ls=(0, (1.5, 2)), zorder=1)
ax.set_xticks(range(len(arms_c)))
ax.set_xticklabels(arms_c)
ax.set_ylabel("Worst minimum gap\nover seeds (m)")
ax.set_ylim(0, 1.45)
panel_tag(ax, "c")

fig.subplots_adjust(left=0.085, right=0.985, top=0.955, bottom=0.16)
save(fig, "fig5_window_cost", target_mm=183)
