"""One-shot, auditable synchronisation of the paper's TTC risk mapping.

The approved research design (AI_CONTEXT/06_DECISIONS.md, 2026-10-11 and
2026-10-12; implementation `code/src/riskprop/formal_risk_measurement.py`,
config `code/configs/stage_0_2_formal_risk_measurement_p2_v1.json`, tests
`code/tests/test_formal_risk_measurement.py`) uses

    rho = exp(-TTC / tau),  tau = 15.364279197080283 s

with vehicle-equal aggregation over a fixed target-vehicle set.  The manuscript
still carried the pre-ratification thresholded linear mapping and a sum over
target vehicles.  This script replaces exactly those two constructs and marks the
linear version as a historical baseline.  It asserts the expected source text
before writing, so it cannot silently edit a different revision.
"""
from __future__ import annotations

from pathlib import Path

PAPER = Path(__file__).resolve().parents[2] / "paper" / "主论文" / "main.tex"

THETA_SENTENCE = "令 $\\theta^{\\mathsf{TTC}}>0$ 为校准后冻结的风险阈值"
SUM_SENTENCE = "为目\\textsuperscript{}标车辆集合内单车风险暴露之和"
SUM_LINE = "&:=\\sum_{v\\in\\mathcal V^{\\mathsf T}_{\\omega}}I_{v,\\omega}^{\\mathsf{TTC}}(\\pi)."

NEW_INTRO = (
    "令 $\\tau^{\\mathsf{TTC}}>0$ 为校准后冻结的 TTC 风险时间尺度"
    "（正式值 $\\tau^{\\mathsf{TTC}}=15.364279197080283$ s，取四个批准 NGSIM 来源"
    "可靠闭合 TTC 的来源内时间加权中位数的排序中间两源平均），令 $[y]_+=\\max(y,0)$。"
    "单个时间步的归一化风险暴露取指数映射，且不以事件阈值截断："
)
NEW_EQUATION = [
    "\\begin{equation*}",
    "\\rho_{v,t}^{\\mathsf{TTC}}",
    "=\\exp\\!\\left(-\\operatorname{TTC}_{v,t}\\big/\\tau^{\\mathsf{TTC}}\\right)",
    "\\quad\\text{仅在可作用的有效闭合观测上计算。}",
    "\\end{equation*}",
    "",
    "因为 $\\operatorname{TTC}_{v,t}\\to 0$ 时 $\\rho_{v,t}^{\\mathsf{TTC}}\\to 1$，"
    "碰撞与近碰撞被连续覆盖，不需要单独的碰撞分支；该映射不假设一个可截断的风险阈值。"
    "早期的阈值线性映射（$1-\\operatorname{TTC}_{v,t}/\\theta^{\\mathsf{TTC}}$，"
    "仅当 $0<\\operatorname{TTC}_{v,t}<\\theta^{\\mathsf{TTC}}$）属于正式记录确认之前的历史基线，"
    "仅作为明确标记的历史对照保留，不再作为主定义；未知贡献不补零，"
    "而是进入区间算术的 $[0,1]$ 上下界。",
]
NEW_TARGET = (
    "在采用 TTC 主终点的运行中，"
    "$R_{v,\\omega}(\\hat{\\mathsf{scr}},\\hat{\\mathsf{opn}})$ 就是对应处理格下的 "
    "$I_{v,\\omega}^{\\mathsf{TTC}}$；目标区域总体风险 "
    "$R_{\\mathcal R^{\\mathsf T},\\omega}(\\hat{\\mathsf{scr}},\\hat{\\mathsf{opn}})$ "
    "为目标车辆集合内的车辆等权平均，而不是求和，以免区域风险随目标车辆数变化；"
    "评价窗口 $\\mathcal W_\\omega$ 与目标车辆资格在运行前冻结，且横跨缺帧不插值。"
)
NEW_AGGREGATION = [
    "J_{\\omega}^{\\mathsf{risk}}(\\pi)",
    "&:=\\frac{1}{\\left|\\mathcal V^{\\mathsf T}_{\\omega}\\right|}"
    "\\sum_{v\\in\\mathcal V^{\\mathsf T}_{\\omega}}I_{v,\\omega}^{\\mathsf{TTC}}(\\pi).",
]


def main() -> int:
    text = PAPER.read_text(encoding="utf-8")
    lines = text.split("\n")
    intro_index = next(i for i, line in enumerate(lines) if line.startswith(THETA_SENTENCE))
    assert lines[intro_index + 1] == "\\begin{equation*}", lines[intro_index + 1]
    assert lines[intro_index + 9] == "\\end{equation*}", lines[intro_index + 9]
    target_index = intro_index + 10
    aggregation_line = next(i for i, line in enumerate(lines) if line.strip() == SUM_LINE)
    assert aggregation_line == target_index + 8, (aggregation_line, target_index)
    out = (
        lines[:intro_index]
        + [NEW_INTRO]
        + NEW_EQUATION
        + [NEW_TARGET]
        + lines[target_index + 1:aggregation_line]
        + NEW_AGGREGATION
        + lines[aggregation_line + 1:]
    )
    PAPER.write_text("\n".join(out), encoding="utf-8")
    remaining = PAPER.read_text(encoding="utf-8").count("\\theta^{\\mathsf{TTC}}")
    print("paper updated; remaining theta-TTC references:", remaining)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
