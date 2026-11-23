"""图 3：提前量判别（GPT + Gemini 两路共同裁决的版式）
a  逐车「送达—动作—物理波到达—有效限幅」时间轴，早报臂 A2（29.0–134.9 s）
b  同轴，等短提前量臂 A2S（8 s）—— 直接看出作用期塌缩
c  三条处理条件的实际提前量分布（A2P = 0 s、A2S = 8 s、A2 = 29–134.9 s）
d  有效限幅帧数（A2S 仅 A2 的 6.57%）
数据：recon_050_a2s.json + probe_vcap.json
"""
import json
import sys

sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = load(F400)
DT = d["config"]["dt"]
VC = json.load(open(r"D:/shen/TJU/AAD/code/scripts/hdm/probe_vcap.json", encoding="utf-8"))


def timeline(arm, s=0):
    a = d["seeds"][str(s)]["arms"][arm]
    recv = sorted(a["msg"]["cap_bind_frames"].keys(), key=int)
    td = a["msg"]["t_deliver_per_car"]
    act = a["msg"]["action"]
    rows = []
    for i in recv:
        t_act = act[i]["t_action"]
        lead = act[i]["lead"]
        rows.append(dict(car=int(i), t_deliver=td[i], t_action=t_act,
                         t_phys=(t_act + lead) if (t_act is not None and lead is not None) else None,
                         cap=int(a["msg"]["cap_bind_frames"][i]) * DT))
    return rows


fig = plt.figure(figsize=(W2, 150 * MM))
gs = fig.add_gridspec(3, 2, height_ratios=[1.00, 1.00, 0.92],
                      hspace=0.52, wspace=0.30)

# ---------------- a / b 时间轴 ----------------
for k, (arm, title) in enumerate((
        ("A2", "Early broadcast: lead 29.0–134.9 s"),
        ("A2S", "Short lead: 8 s by design"))):
    ax = fig.add_subplot(gs[k, :])
    rows = timeline(arm)
    col = ARM_STYLE[arm][0]
    for j, r in enumerate(rows):
        if r["t_action"] is not None and r["cap"] > 0:
            ax.barh(j, r["cap"], left=r["t_action"], height=0.52,
                    color=col, alpha=0.26, edgecolor="none", zorder=1)
        if r["t_deliver"] is not None:
            ax.plot(r["t_deliver"], j, marker="v", ms=4.4, mfc="none",
                    mec="#1A1A1A", mew=0.9, zorder=5)
        if r["t_action"] is not None:
            ax.plot(r["t_action"], j, marker="o", ms=3.4, color=col,
                    mec="white", mew=0.5, zorder=6)
        if r["t_phys"] is not None:
            ax.plot(r["t_phys"], j, marker="^", ms=4.6, mfc="none",
                    mec="#B03A2E", mew=1.0, zorder=5)
        # 提前量数值标在行右端
        if r["t_phys"] is not None and r["t_deliver"] is not None:
            lead = r["t_phys"] - r["t_deliver"]
            ax.text(1.005, j, f"{lead:.0f}", transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=BASE - 2.6, color="#444444")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"#{r['car']}" for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Time since simulation start (s)")
    ax.set_ylabel("Receiver vehicle")
    ax.text(0.0, 1.02, title, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=BASE - 1.2, fontweight="bold")
    ax.text(1.005, -0.9, "lead\n(s)", transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=BASE - 2.6, color="#444444")
    ax.margins(x=0.05)
    panel_tag(ax, "ab"[k])

handles = [Line2D([], [], marker="v", ms=4.4, mfc="none", mec="#1A1A1A", mew=0.9,
                  ls="none", label="message delivered"),
           Line2D([], [], marker="o", ms=3.4, color="#555555", mec="white", mew=0.5,
                  ls="none", label="action confirmed"),
           Line2D([], [], marker="^", ms=4.6, mfc="none", mec="#B03A2E", mew=1.0,
                  ls="none", label="physical wave arrives"),
           Line2D([], [], color="#888888", lw=4, alpha=0.30, label="effective capping window")]
fig.legend(handles=handles, frameon=False, ncol=4, loc="upper center",
           bbox_to_anchor=(0.5, 1.008), handlelength=1.4, columnspacing=1.6)

# ---------------- c 实际提前量分布 ----------------
ax = fig.add_subplot(gs[2, 0])
conds = [("A2P", "0 s\n(A2P)"), ("A2S", "8 s\n(A2S)"), ("A2", "29–135 s\n(A2)")]
rng = np.random.default_rng(2)
for j, (arm, lab) in enumerate(conds):
    leads = []
    for s in range(NSEED):
        a = d["seeds"][str(s)]["arms"][arm]
        for i, v in a["msg"]["action"].items():
            if v.get("lead") is not None:
                leads.append(v["lead"])
    col = ARM_STYLE[arm][0]
    ax.scatter(j + rng.uniform(-0.16, 0.16, len(leads)), leads, s=5, color=col,
               alpha=0.55, edgecolors="none", zorder=3)
    ax.hlines(float(np.median(leads)), j - 0.24, j + 0.24, color=col, lw=1.8, zorder=4)
    ax.text(j + 0.30, float(np.median(leads)), f"{np.median(leads):.0f}", ha="left",
            va="center", fontsize=BASE - 2.2, color=col, fontweight="bold")
ax.set_xticks(range(len(conds)))
ax.set_xticklabels([c[1] for c in conds])
ax.set_ylabel("Actual lead time (s)")
ax.set_xlim(-0.5, len(conds) - 0.2)
ax.set_ylim(-8, 150)
panel_tag(ax, "c")

# ---------------- d 有效限幅帧 ----------------
ax = fig.add_subplot(gs[2, 1])
arms_d = ["A2", "A2S", "A2P"]
tot = {a: cap_bind_total(d, a).sum() for a in arms_d}
ax.bar(range(len(arms_d)), [tot[a] for a in arms_d],
       color=[ARM_STYLE[a][0] for a in arms_d], width=0.58)
ax.set_yscale("log")
ax.set_xticks(range(len(arms_d)))
ax.set_xticklabels(arms_d)
ax.set_ylabel("Effective capping frames\n(10 seeds, log scale)")
for i, a in enumerate(arms_d):
    lab = f"{tot[a]:,.0f}" if a == "A2" else f"{tot[a]:,.0f}\n({tot[a]/tot['A2']*100:.2f}%)"
    ax.text(i, tot[a] * 1.18, lab, ha="center", va="bottom", fontsize=BASE - 2)
ax.set_ylim(1e2, 2e6)
panel_tag(ax, "d")

fig.subplots_adjust(left=0.075, right=0.955, top=0.945, bottom=0.075)
save(fig, "fig3_leadtime", target_mm=183)

# 打印实测基准，供图注引用
for a in ("A2", "A2S", "A2P"):
    v = [x["v_cap"] for s in VC[a].values() for x in s.values()]
    print(f"{a}: v_cap {min(v):.2f}–{max(v):.2f} m/s (median {np.median(v):.2f}), n={len(v)}")