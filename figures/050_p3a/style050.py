"""AAD 0.5.0 汇报图：统一绘图样式（顶刊口径）

口径来源：
  · PAPER-SKILL `research-figures:paper-figure` —— 矢量 PDF、无图内标题、字体内嵌、色盲友好
  · AAD 目标刊 Nature Communications —— 单栏 89 mm / 双栏 183 mm，缩放后字号 ≥ 5 pt
  · 数据一律从 recon_050_a2s.json / recon_050_window600b.json 读，禁止硬编码

用法：在每张图的脚本里 `from style050 import *`
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------- 尺寸（英寸，1 mm = 1/25.4 in） ----------
MM = 1 / 25.4
W1 = 89 * MM          # 单栏 3.50 in
W15 = 120 * MM        # 1.5 栏
W2 = 183 * MM         # 双栏 7.20 in

# ---------- 字体与刻度 ----------
# AAD_FIG_MODE=ppt 时放大字号与线宽，供投影/汇报用（论文版保持 8 pt）
import os as _os
PPT_MODE = _os.environ.get("AAD_FIG_MODE", "").lower() == "ppt"
BASE = 13 if PPT_MODE else 8
matplotlib.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    # 数学符号也用 Times，避免 Times + STIX 混排
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman",
    "mathtext.it": "Times New Roman:italic",
    "mathtext.bf": "Times New Roman:bold",
    "font.size": BASE,
    "axes.labelsize": BASE,
    "axes.titlesize": BASE,          # 图内不放标题，保留以防误用
    "xtick.labelsize": BASE - 1,
    "ytick.labelsize": BASE - 1,
    "legend.fontsize": BASE - 1,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    # 投稿要求页面尺寸精确等于 89 / 183 mm：不用 tight（tight 会把版面裁小、宽高不再等于目标）
    "savefig.bbox": None,
    "savefig.pad_inches": 0.0,
    "axes.grid": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 1.1 if PPT_MODE else 0.6,
    "xtick.major.width": 1.1 if PPT_MODE else 0.6,
    "ytick.major.width": 1.1 if PPT_MODE else 0.6,
    "xtick.major.size": 4.0 if PPT_MODE else 2.5,
    "ytick.major.size": 4.0 if PPT_MODE else 2.5,
    "lines.linewidth": 1.6 if PPT_MODE else 0.8,
    "lines.markersize": 4.5 if PPT_MODE else 2.2,
    "pdf.fonttype": 42,              # 内嵌 TrueType，投稿要求
    "ps.fonttype": 42,
})

# ---------- 色盲友好调色（Okabe–Ito，灰度下靠线型/标记再区分） ----------
OKABE = {
    "black": "#000000",
    "orange": "#E69F00",
    "skyblue": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "grey": "#999999",
}

# 臂 → (颜色, 标记, 线型) —— 保证黑白打印也能区分
ARM_STYLE = {
    "A0":  (OKABE["black"],      "o", "-"),
    "A1":  (OKABE["grey"],       "s", "-"),
    "A2":  (OKABE["blue"],       "^", "-"),
    "A3":  (OKABE["vermillion"], "v", "-"),
    "A2L": (OKABE["skyblue"],    "D", "--"),
    "A3L": (OKABE["purple"],     "P", "--"),
    "A2S": (OKABE["green"],      "X", "-"),
    "A2P": (OKABE["orange"],     "*", ":"),
    "A3P": ("#8C6D1F",           "h", ":"),   # 原浅黄在白底不可见，改深褐
}

# ---------- 数据 ----------
HDM = r"D:/shen/TJU/AAD/code/scripts/hdm"
F400 = os.path.join(HDM, "recon_050_a2s.json")
F600 = os.path.join(HDM, "recon_050_window600b.json")
OUT = r"D:/shen/TJU/AAD/figures/050_p3a"

MSG_ARMS = ("A1", "A2", "A3", "A2L", "A3L", "A2S", "A2P", "A3P")
ALL_ARMS = ("A0",) + MSG_ARMS
NSEED = 10


def load(path=F400):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def series(d, arm, key="episodes_total"):
    return np.array([d["seeds"][str(s)]["arms"][arm][key] for s in range(NSEED)], dtype=float)


def paired(d, arm, key="episodes_total", base="A0"):
    return series(d, arm, key) - series(d, base, key)


def cap_bind_total(d, arm):
    return np.array([sum(d["seeds"][str(s)]["arms"][arm]["msg"]["cap_bind_frames"].values())
                     for s in range(NSEED)], dtype=float)


def lead_times(d, arm):
    """每辆接收车在 10 个种子里的实际提前量 T_phys − t_deliver（秒）。"""
    out = []
    for s in range(NSEED):
        a = d["seeds"][str(s)]["arms"][arm]
        if a.get("msg") is None:
            continue
        for i, v in (a["msg"].get("action") or {}).items():
            if v.get("lead") is not None:
                out.append(float(v["lead"]))
    return np.array(out, dtype=float)


def delivery_lead(d, arm):
    """送达提前量 = T_phys(i) − t_deliver(i)，秒。

    注意与 trace 里的 `action[i]["lead"]` 区分：后者是 T_phys − t_action
    （动作确认到物理波到达），不是送达提前量。A2P 的送达提前量是 **−0.6 s**
    （送达时物理波已过），用 action 的 lead 会错算成 −15…−86。
    只统计真正触发过限幅的车（未触发的没有 T_phys 可算）。
    """
    out = []
    for s in range(NSEED):
        m = d["seeds"][str(s)]["arms"][arm]["msg"]
        for i, t in (m.get("t_deliver_per_car") or {}).items():
            if t is None:
                continue
            a = (m.get("action") or {}).get(i)
            if not a or a.get("t_action") is None or a.get("lead") is None:
                continue
            out.append(float(a["t_action"] + a["lead"] - t))
    return np.array(out, dtype=float)


def v_cap_range(d, arm):
    """该臂送达时刻冻结的限速上限区间（直接读 trace，不要自己用 A0 轨迹反推）。"""
    v = []
    for s in range(NSEED):
        t = d["seeds"][str(s)]["arms"][arm]["trace"].get("v_cap") or {}
        v += [x for x in t.values() if x is not None]
    return (float(min(v)), float(max(v))) if v else (float("nan"), float("nan"))


def split_events(d, arm, part, base_key):
    """part ∈ {recv, nonrecv}；base_key 是 A0 里对应的键。"""
    a = np.array([d["seeds"][str(s)]["arms"][arm]["split"][part]["events"] for s in range(NSEED)])
    b = np.array([d["seeds"][str(s)]["arms"]["A0"]["split"][base_key]["events"] for s in range(NSEED)])
    return a - b


def panel_tag(ax, letter, dx=-0.135, dy=1.005):
    ax.text(dx, dy, letter, transform=ax.transAxes,
            fontsize=BASE + 1, fontweight="bold", ha="left", va="bottom")


def save(fig, name, target_mm=None):
    """保存矢量 PDF；页面尺寸严格等于 figsize（投稿按 89 / 183 mm 验收）。
    PPT 模式文件名加 _ppt 后缀，不覆盖论文版。"""
    os.makedirs(OUT, exist_ok=True)
    if PPT_MODE:
        name = name + "_ppt"
    p = os.path.join(OUT, name + ".pdf")
    fig.savefig(p, bbox_inches=None, pad_inches=0.0)
    plt.close(fig)
    w_in, h_in = fig.get_size_inches()
    print(f"saved {p}  ({w_in * 25.4:.1f} x {h_in * 25.4:.1f} mm)")
    if target_mm is not None:
        assert abs(w_in * 25.4 - target_mm) < 0.5, "宽度偏离目标"
    return p


def significance_text(p):
    """只报 p，不写“显著/不显著”这类结论词。"""
    return f"$p={p:.3f}$" if p >= 0.01 else f"$p={p:.4f}$".replace("0.", ".", 1)


def sign_test_p(diffs):
    from math import comb
    d = np.asarray([x for x in diffs if x != 0], dtype=float)
    n = len(d)
    if n == 0:
        return 1.0
    k = int(min((d < 0).sum(), (d > 0).sum()))
    return min(1.0, sum(comb(n, i) for i in range(k + 1)) / 2 ** n * 2)
