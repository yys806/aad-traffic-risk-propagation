"""图 3：全队持平背后的抵消（逐种子配对拆分）
关键：中位数不可加（−5.0 + 2.5 ≠ 0.0），所以必须逐种子画，
      每根堆叠条满足 Δrecv + Δnonrecv = Δall（恒等，可当场核）。
a  A2S（提前 8 s）：接收车 8 辆 vs 非接收车 72 辆
b  A2P（零提前）：接收车 8 辆 vs 非接收车 72 辆
数据：recon_050_a2s.json
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = load(F400)

fig = plt.figure(figsize=(W2, 62 * MM))
gs = fig.add_gridspec(1, 2, wspace=0.28)

# 送达提前量取实测值：A2S = +8.00 s，A2P = −0.60 s（送达时物理波已过）
CASES = [("A2S", "8 s lead", "recv_A2", "nonrecv_A2"),
         ("A2P", "After wave (−0.6 s lead)", "recv_A2", "nonrecv_A2")]

for k, (arm, label, bk, nk) in enumerate(CASES):
    ax = fig.add_subplot(gs[0, k])
    rec = split_events(d, arm, "recv", bk)
    non = split_events(d, arm, "nonrecv", nk)
    tot = rec + non
    xs = np.arange(NSEED)

    ax.axhline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
    w = 0.36
    ax.bar(xs - w / 2, rec, width=w, color=OKABE["green"], alpha=0.85,
           edgecolor="white", linewidth=0.3, label="receivers (8 veh.)", zorder=2)
    ax.bar(xs + w / 2, non, width=w, color=OKABE["orange"], alpha=0.85,
           edgecolor="#333333", linewidth=0.35, hatch="///",
           label="non-receivers (72 veh.)", zorder=2)
    ax.plot(xs, tot, marker="D", ms=2.8, ls="none", color="#111111",
            mec="white", mew=0.4, label="whole target zone", zorder=4)

    ax.set_xticks(xs)
    ax.set_xticklabels([str(i) for i in xs])
    ax.set_xlabel("Seed")
    if k == 0:
        ax.set_ylabel("Change in events vs A0")
    lo = float(min(rec.min(), non.min(), tot.min()))
    hi = float(max(rec.max(), non.max(), tot.max()))
    pad = max(3.0, 0.18 * (hi - lo))
    ax.set_ylim(lo - pad, hi + pad)
    # 两面板纵轴范围不同，必须写明，否则并排会被误读成同一把尺
    # 放在 x 轴标题上方，否则会与 "Seed" 重叠
    # 放在 x 标签与 x 轴标题之间的空档里，既不压刻度数字也不压标题
    ax.text(0.5, -0.215, f"axis range {lo - pad:.0f} to {hi + pad:.0f}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=BASE - 4.8, color="#666666")
    _names = {"A2S": "A2S: 8 s early", "A2P": "A2P: 0.6 s after wave hit"}
    ax.text(0.0, 1.015,
            f"{_names.get(arm, arm)} · recv. lower {int((rec<0).sum())}/10",
            transform=ax.transAxes, ha="left", va="bottom",
            fontsize=BASE - 3.0, fontweight="bold")
    # 一致性命中率：放面板右下内侧，不与标题行抢位置
    panel_tag(ax, "a" if k == 0 else "b")

_leg = [Line2D([], [], marker="s", ms=4, ls="none", color=OKABE["green"],
                label="receivers (8)"),
        matplotlib.patches.Patch(facecolor=OKABE["orange"], edgecolor="#333333",
                                 hatch="///", lw=0.35, label="non-receivers (72)"),
        Line2D([], [], marker="D", ms=3, ls="none", color="#111111",
               label="whole zone (per-seed sum)")]
if PPT_MODE:      # 字大，图例分两行放，避免横向出画布
    fig.legend(handles=_leg, frameon=False, ncol=2, loc="upper center",
               bbox_to_anchor=(0.5, 1.005), handlelength=1.0, columnspacing=1.2,
               fontsize=BASE - 2)
else:
    fig.legend(handles=_leg, frameon=False, ncol=3, loc="upper center",
               bbox_to_anchor=(0.5, 0.995), handlelength=1.2, columnspacing=1.6)

if PPT_MODE:
    fig.subplots_adjust(left=0.105, right=0.975, top=0.72, bottom=0.225)
else:
    fig.subplots_adjust(left=0.085, right=0.985, top=0.775, bottom=0.155)
save(fig, "fig3_offset", target_mm=183)
