"""图 1：通路示意图
设计源 = specs/fig1_pipeline.json（由 figure-spec 技能校验通过的 FigureSpec）
渲染 = matplotlib + style050（保证 Times 内嵌 Type 42、页面宽度精确 183 mm，
        并与图 2–5 的排版完全一致）
"""
import json
import sys

sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import *          # noqa: F401,F403
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

SPEC = json.load(open(r"D:/shen/TJU/AAD/figures/050_p3a/specs/fig1_pipeline.json",
                      encoding="utf-8"))
CW, CH = SPEC["canvas"]["width"], SPEC["canvas"]["height"]
NODES = {n["id"]: n for n in SPEC["nodes"]}

fig = plt.figure(figsize=(W2, W2 * CH / CW))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, CW)
ax.set_ylim(0, CH)
ax.invert_yaxis()
ax.axis("off")


def node_center(n):
    return n["x"], n["y"]


# ---------- 节点 ----------
for n in SPEC["nodes"]:
    x, y, w, h = n["x"], n["y"], n["width"], n["height"]
    pad = 6
    box = FancyBboxPatch((x + pad, y + pad), w - 2 * pad, h - 2 * pad,
                         boxstyle="round,pad=0,rounding_size=7",
                         facecolor=n.get("fill", "#FFFFFF"),
                         edgecolor=n.get("stroke", "#333333"),
                         linewidth=0.7, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, n["label"], ha="center", va="center",
            fontsize=n.get("font_size", 13) * 0.62, color="#111111",
            linespacing=1.35, zorder=3)


# ---------- 连线 ----------
def anchors(a, b):
    """按相对位置取框边界上的出入点。"""
    ax_, ay_ = a["x"] + a["width"] / 2, a["y"] + a["height"] / 2
    bx_, by_ = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    dx, dy = bx_ - ax_, by_ - ay_
    if abs(dx) >= abs(dy):
        if dx >= 0:
            return ((a["x"] + a["width"], ay_), (b["x"], by_))
        return ((a["x"], ay_), (b["x"] + b["width"], by_))
    if dy >= 0:
        return ((ax_, a["y"] + a["height"]), (bx_, b["y"]))
    return ((ax_, a["y"]), (bx_, b["y"] + b["height"]))


for e in SPEC["edges"]:
    a, b = NODES[e["from"]], NODES[e["to"]]
    p0, p1 = anchors(a, b)
    color = e.get("color", "#555555")
    dotted = e.get("style") == "dotted"
    conn = "arc3,rad=0.28" if e.get("curve") else "arc3,rad=0"
    ar = FancyArrowPatch(p0, p1, arrowstyle="-|>" if not dotted else "-",
                         mutation_scale=5.5, linewidth=0.65 if not dotted else 0.55,
                         color=color, connectionstyle=conn,
                         linestyle=(0, (2, 2)) if dotted else "-",
                         shrinkA=0, shrinkB=0, zorder=1)
    ax.add_patch(ar)
    if e.get("label"):
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        off = -11 if abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1]) else 0
        ax.text(mx, my + off, e["label"], ha="center", va="center",
                fontsize=6.3, color="#3A3A3A", zorder=4,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6, alpha=0.95))

save(fig, "fig1_pipeline", target_mm=183)