"""图 4：全队持平背后的抵消（逐种子配对拆分）
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

CASES = [("A2S", "8 s lead", "recv_A2", "nonrecv_A2"),
         ("A2P", "At-wave (0 s lead)", "recv_A2", "nonrecv_A2")]

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
    ax.text(0.02, 1.015, f"{arm} — {label}", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=BASE - 1.2, fontweight="bold")
    # 一致性命中率
    ax.text(0.98, 0.04,
            f"receivers lower in {int((rec<0).sum())}/10;  whole zone median {np.median(tot):+.1f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=BASE - 2)
    panel_tag(ax, "a" if k == 0 else "b")

fig.legend(handles=[Line2D([], [], marker="s", ms=4, ls="none", color=OKABE["green"],
                           label="receivers (8 veh.)"),
                    matplotlib.patches.Patch(facecolor=OKABE["orange"], edgecolor="#333333",
                                             hatch="///", lw=0.35,
                                             label="non-receivers (72 veh.)"),
                    Line2D([], [], marker="D", ms=3, ls="none", color="#111111",
                           label="whole target zone (= receivers + non-receivers)")],
           frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.06),
           handlelength=1.2, columnspacing=1.6)

fig.subplots_adjust(left=0.085, right=0.985, top=0.86, bottom=0.155)
save(fig, "fig4_offset", target_mm=183)
