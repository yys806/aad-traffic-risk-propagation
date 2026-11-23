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
import matplotlib
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
med4 = {a: float(np.median(series(d4, a))) for a in arms}
med6 = {a: float(np.median(series(d6, a))) for a in arms}
for j, arm in enumerate(arms):
    ax.text(j - w / 2, r4[j] - 2.4, f"{r4[j]:.1f}", ha="center", va="top", fontsize=BASE - 2.5)
    ax.text(j + w / 2, r6[j] - 2.4, f"{r6[j]:.1f}", ha="center", va="top", fontsize=BASE - 2.5)

ax.set_xticks(xs)
ax.set_xticklabels(arms)
ax.set_ylabel("Change vs A0 (%)")
ax.set_ylim(-62, 6)
# 600 s 窗 A2/A3 的原始中位倒挂必须点明：相对百分比看不出来，得给绝对数
ax.annotate(f"600 s: A2 {med6['A2']:.0f} < A3 {med6['A3']:.0f}\n(dose inversion)",
            xy=(2 + w / 2, r6[2] + 0.6), xytext=(1.35, -18),
            fontsize=5.8, color="#7D3C98", ha="center",
            arrowprops=dict(arrowstyle="-|>", lw=0.55, color="#7D3C98",
                            connectionstyle="arc3,rad=-0.25"))
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, -0.02), handlelength=1.2)
panel_tag(ax, "a", dy=0.995)

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
def _fmt(v):
    """避免出现 -0.0 这种负零写法。"""
    return "0.0" if abs(v) < 0.05 else f"{v:+.1f}"


for j, (a, b) in enumerate(zip(dl4, dl6)):
    ax.text(j - w / 2, a + (1.6 if a >= 0 else -1.6), _fmt(a), ha="center",
            va="bottom" if a >= 0 else "top", fontsize=BASE - 2.5)
    ax.text(j + w / 2, b + (1.6 if b >= 0 else -1.6), _fmt(b), ha="center",
            va="bottom" if b >= 0 else "top", fontsize=BASE - 2.5)
ax.set_xticks(xs)
ax.set_xticklabels(arms_b)
ax.set_ylabel("Delay change vs A0\n(vehicle·seconds, median)")
ax.set_ylim(-52, 16)
ax.legend(handles=[matplotlib.patches.Patch(facecolor="#5D6D7E", label="400 s"),
                   matplotlib.patches.Patch(facecolor="#AEB6BF", edgecolor="#333333",
                                            hatch="///", label="600 s")],
          frameon=False, loc="lower left", bbox_to_anchor=(0.0, -0.02),
          handlelength=1.2, ncol=2)
panel_tag(ax, "b", dy=0.995)

# ---------------- c：最小净距（逐种子配对，这是真相；跨种子最坏值会掩盖同种子恶化） ----------------
ax = fig.add_subplot(gs[0, 2])
arms_c = ["A2", "A3", "A2S"]
a0g = series(d4, "A0", "min_gap")
xs_c = np.arange(len(arms_c))
w_c = 0.36
ax.axhline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
diffs = [series(d4, a, "min_gap") - a0g for a in arms_c]
rngc = np.random.default_rng(5)
for j, (arm, dl) in enumerate(zip(arms_c, diffs)):
    col = ARM_STYLE[arm][0]
    ax.bar([j], [float(np.median(dl))], width=w_c, color=col, alpha=0.55,
           edgecolor="white", linewidth=0.3, zorder=2)
    ax.scatter(j + rngc.uniform(-0.12, 0.12, NSEED), dl, s=7, color=col,
               zorder=3, edgecolors="white", linewidths=0.3)
    ax.text(j, float(np.median(dl)) - 0.13, f"{np.median(dl):+.2f}", ha="center",
            va="top", fontsize=6.0, color=col, fontweight="bold")
# 最坏的同一颗种子单独点出来（A2 seed 3：A0 2.505 → A2 0.669）
_w = int(np.argmin(diffs[0]))
ax.annotate(f"seed {_w}: A0 {a0g[_w]:.2f} → A2 {a0g[_w] + diffs[0][_w]:.2f} m",
            xy=(0.16, diffs[0][_w]), xytext=(0.55, -1.95),
            fontsize=5.8, color="#B03A2E", ha="left",
            arrowprops=dict(arrowstyle="-|>", lw=0.55, color="#B03A2E",
                            connectionstyle="arc3,rad=0.25"))
ax.set_xticks(xs_c)
ax.set_xticklabels(arms_c)
ax.set_ylabel("Change in worst minimum gap\nvs A0, per seed (m)")
ax.set_xlim(-0.55, len(arms_c) - 0.45)
panel_tag(ax, "c", dy=0.995)
ax.set_ylim(-2.35, 0.55)

fig.subplots_adjust(left=0.085, right=0.985, top=0.90, bottom=0.165)
save(fig, "fig5_window_cost", target_mm=183)
