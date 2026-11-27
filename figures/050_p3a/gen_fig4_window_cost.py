"""图 4：时间窗稳健性与代价（两路都认为必须补的一张）
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
arms = ["A2", "A3"] if PPT_MODE else ["A2", "A3", "A2L", "A3L"]
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
    ax.text(j - w / 2, r4[j] - 2.4, f"{r4[j]:.1f}", ha="center", va="top",
            fontsize=BASE - 2.5 if not PPT_MODE else BASE - 4.5)
    # 投影版只标 400 s 主窗，600 s 数值已在正文里，避免 8 个标签挤成一团
    if not PPT_MODE:
        ax.text(j + w / 2, r6[j] - 2.4, f"{r6[j]:.1f}", ha="center", va="top", fontsize=BASE - 2.5)

ax.set_xticks(xs)
ax.set_xticklabels(arms)
ax.set_ylabel("Change vs A0 (%)")
ax.set_ylim(-62, 6)
# 600 s 窗 A2/A3 的原始中位倒挂必须点明：相对百分比看不出来，得给绝对数
# arms = [A2, A3, A2L, A3L]，A3 是下标 1；之前写成 2 指到了 A2L
# 倒挂标注：论文版需要，投影版省略（正文已写明 115.5 < 119.0），避免挤占面板
if not PPT_MODE:
    ax.annotate(f"600 s: A2 {med6['A2']:.0f} < A3 {med6['A3']:.0f}\n(dose inversion)",
                xy=(1 + w / 2, r6[1] + 0.6), xytext=(1.55, -20),
                fontsize=5.8, color="#7D3C98", ha="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.55, color="#7D3C98",
                                connectionstyle="arc3,rad=-0.22"))
if not PPT_MODE:
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
    if not PPT_MODE:      # 投影版只标主窗数值，600 s 数值在正文里
        ax.text(j + w / 2, b + (1.6 if b >= 0 else -1.6), _fmt(b), ha="center",
                va="bottom" if b >= 0 else "top", fontsize=BASE - 2.5)
ax.set_xticks(xs)
ax.set_xticklabels(arms_b)
ax.set_ylabel("Delay change vs A0\n(vehicle·seconds, median)")
ax.set_ylim(-52, 16)
# 图例放上方内侧：放底部会压住 −41.3 并冲出面板、撞上 c 图纵轴标题
ax.legend(handles=[matplotlib.patches.Patch(facecolor="#5D6D7E", label="400 s"),
                   matplotlib.patches.Patch(facecolor="#AEB6BF", edgecolor="#333333",
                                            hatch="///", label="600 s")],
          frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.0),
          handlelength=1.0, ncol=2, fontsize=BASE - 3.2,
          columnspacing=0.9, handletextpad=0.4, borderpad=0.2)
panel_tag(ax, "b", dy=0.995)

# ---------------- c：最小净距（逐种子配对，这是真相；跨种子最坏值会掩盖同种子恶化） ----------------
ax = fig.add_subplot(gs[0, 2])
arms_c = ["A2", "A3", "A2S"]
a0g = series(d4, "A0", "min_gap")
xs_c = np.arange(len(arms_c))
w_c = 0.36
ax.axhline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
diffs = [series(d4, a, "min_gap") - a0g for a in arms_c]
# 纵轴由实际数据定，绝不写死上限——写死会静默切掉正向改善最大的几个种子
_all = np.concatenate(diffs)
_lo, _hi = float(_all.min()), float(_all.max())
_pad = 0.12 * (_hi - _lo)
rngc = np.random.default_rng(5)
for j, (arm, dl) in enumerate(zip(arms_c, diffs)):
    col = ARM_STYLE[arm][0]
    ax.bar([j], [float(np.median(dl))], width=w_c, color=col, alpha=0.55,
           edgecolor="white", linewidth=0.3, zorder=2)
    ax.scatter(j + rngc.uniform(-0.12, 0.12, NSEED), dl, s=7, color=col,
               zorder=3, edgecolors="white", linewidths=0.3)
    # 投影版省略：三臂中位都≈0，信息量低，且面板窄会压散点；关键案例靠红字批注
    if not PPT_MODE:
        ax.text(j + 0.30, float(np.median(dl)), f"{np.median(dl):+.2f}", ha="left",
                va="center", fontsize=6.0, color=col, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.8, alpha=0.9))
# 最坏的同一颗种子单独点出来（A2 seed 3：A0 2.505 → A2 0.669）
_w = int(np.argmin(diffs[0]))
ax.annotate(f"seed {_w}: A0 {a0g[_w]:.2f} → A2 {a0g[_w] + diffs[0][_w]:.2f} m",
            xy=(0.16, diffs[0][_w]), xytext=(0.55, _lo - 0.55 * _pad),
            fontsize=5.8 if not PPT_MODE else BASE - 4.6, color="#B03A2E", ha="left",
            arrowprops=dict(arrowstyle="-|>", lw=0.55, color="#B03A2E",
                            connectionstyle="arc3,rad=0.25"))
ax.set_xticks(xs_c)
ax.set_xticklabels(arms_c)
ax.set_ylabel("Change in worst minimum gap\nvs A0, per seed (m)")
ax.set_xlim(-0.55, len(arms_c) - 0.45)
panel_tag(ax, "c", dy=0.995)
ax.set_ylim(_lo - _pad, _hi + _pad)

if PPT_MODE:
    # wspace 放大：否则 b 的纵轴标题会横压 a 的柱子、c 的纵轴标题压 b 的右缘
    fig.subplots_adjust(left=0.105, right=0.975, top=0.855, bottom=0.225, wspace=0.46)
else:
    fig.subplots_adjust(left=0.085, right=0.985, top=0.90, bottom=0.165, wspace=0.34)
save(fig, "fig4_window_cost", target_mm=183)
