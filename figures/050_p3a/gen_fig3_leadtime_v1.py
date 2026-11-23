"""图 3：提前量判别（本轮最硬的一张）
a  A2（早报 8 辆）逐车时间轴：送达 / 动作 / 物理波到达 / 有效限幅窗口
b  A2S（提前 8 s）同一时间轴 —— 与 a 共享横轴，直接看出“降完就被接管”
c  四条臂逐种子事件差（配对）
d  有效限幅帧数（对数/线性条）—— A2S 只有 A2 的 6.57%
数据：recon_050_a2s.json（seed 0 画时间轴，n=10 画 c/d）
"""
import sys
sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = load(F400)
DT = d["config"]["dt"]

fig = plt.figure(figsize=(W2, 132 * MM))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05], hspace=0.55, wspace=0.30)

# ---------- 取 seed 0 的逐车时间量 ----------
def timeline(d, arm, s=0):
    a = d["seeds"][str(s)]["arms"][arm]
    recv = list(a["msg"]["cap_bind_frames"].keys())
    td = a["msg"]["t_deliver_per_car"]
    act = a["msg"]["action"]
    rows = []
    for i in recv:
        t_act = act[i]["t_action"]
        lead = act[i]["lead"]
        t_phys = (t_act + lead) if (t_act is not None and lead is not None) else None
        rows.append(dict(car=int(i), t_deliver=td[i], t_action=t_act, t_phys=t_phys,
                         cap=int(a["msg"]["cap_bind_frames"][i]) * DT))
    return rows

# ---------- Panel a / b ----------
for k, (arm, title) in enumerate((("A2", "Early broadcast (29–135 s lead)"),
                                  ("A2S", "Short lead (8 s)"))):
    ax = fig.add_subplot(gs[0, k])
    rows = timeline(d, arm)
    col = ARM_STYLE[arm][0]
    for j, r in enumerate(rows):
        y = j
        if r["t_action"] is not None and r["cap"] > 0:
            ax.barh(y, r["cap"], left=r["t_action"], height=0.55,
                    color=col, alpha=0.28, edgecolor="none", zorder=1)
        if r["t_deliver"] is not None:
            ax.plot(r["t_deliver"], y, marker="v", ms=4.4, mfc="none",
                    mec="#1A1A1A", mew=0.9, zorder=5)
        if r["t_action"] is not None:
            ax.plot(r["t_action"], y, marker="o", ms=3.4, color=col,
                    mec="white", mew=0.5, zorder=6)
        if r["t_phys"] is not None:
            ax.plot(r["t_phys"], y, marker="^", ms=4.6, mfc="none",
                    mec="#B03A2E", mew=1.0, zorder=5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"#{r['car']}" for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Receiver vehicle")
    ax.text(0.0, 1.015, title, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=BASE - 1.5, fontweight="bold")
    ax.margins(x=0.07)
    panel_tag(ax, "a" if k == 0 else "b")

# 统一图例（放在 a 面板下方）
axl = fig.add_subplot(gs[0, 0]); axl.axis("off")
handles = [Line2D([], [], marker="v", ms=4.4, mfc="none", mec="#1A1A1A", mew=0.9,
                  ls="none", label="message delivered"),
           Line2D([], [], marker="o", ms=3.4, color="#555555", mec="white", mew=0.5,
                  ls="none", label="action confirmed"),
           Line2D([], [], marker="^", ms=4.6, mfc="none", mec="#B03A2E", mew=1.0,
                  ls="none", label="physical wave arrives"),
           Line2D([], [], color="#888888", lw=4, alpha=0.35, label="effective capping window")]
fig.legend(handles=handles, frameon=False, ncol=4, loc="upper center",
           bbox_to_anchor=(0.5, 1.005), handlelength=1.4, columnspacing=1.8)

# ---------- Panel c：逐种子配对事件差 ----------
ax = fig.add_subplot(gs[1, 0])
arms_c = ["A2", "A2S", "A2L", "A2P"]
xs = np.arange(len(arms_c))
ax.axhline(0, color="#8C8C8C", lw=0.7, ls=(0, (2.5, 2)), zorder=0)
rng = np.random.default_rng(1)
for j, arm in enumerate(arms_c):
    dl = paired(d, arm)
    col = ARM_STYLE[arm][0]
    ax.scatter(j + rng.uniform(-0.14, 0.14, NSEED), dl, s=8, color=col, marker="o",
               zorder=3, edgecolors="white", linewidths=0.3)
    ax.hlines(float(np.median(dl)), j - 0.22, j + 0.22, color=col, lw=1.8, zorder=4)
    ax.text(j, ax.get_ylim()[0], "", fontsize=1)
ax.set_xticks(xs)
ax.set_xticklabels(arms_c)
ax.set_ylabel("Change in events vs A0")
ax.set_xlim(-0.5, len(arms_c) - 0.5)
ax.margins(y=0.10)
panel_tag(ax, "c")

# ---------- Panel d：有效限幅帧数 ----------
ax = fig.add_subplot(gs[1, 1])
arms_d = ["A2", "A2S", "A2P"]
tot = {a: cap_bind_total(d, a).sum() for a in arms_d}
bars = ax.bar(range(len(arms_d)), [tot[a] for a in arms_d],
              color=[ARM_STYLE[a][0] for a in arms_d], width=0.6)
ax.set_yscale("log")
ax.set_xticks(range(len(arms_d)))
ax.set_xticklabels(arms_d)
ax.set_ylabel("Effective capping frames\n(10 seeds, log scale)")
for i, a in enumerate(arms_d):
    lab = f"{tot[a]:,.0f}" if a == "A2" else f"{tot[a]:,.0f}\n({tot[a]/tot['A2']*100:.2f}%)"
    ax.text(i, tot[a] * 1.15, lab, ha="center", va="bottom", fontsize=BASE - 2)
ax.set_ylim(1e2, 1e6)
panel_tag(ax, "d")

save(fig, "fig3_leadtime")
