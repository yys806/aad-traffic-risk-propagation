from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.legacy.events import coalesce_risk_events  # noqa: E402
from riskprop.legacy.propagation import (  # noqa: E402
    build_propagation_edges,
    rank_intervention_candidates,
    score_event_roles,
    select_direct_propagation_edges,
    summarise_propagation,
)
from riskprop.legacy.visuals import (  # noqa: E402
    create_visual_package,
    plot_edge_selection,
    plot_intervention_screening,
    plot_method_flow,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a readable direct-risk analysis package from an existing rollout result.")
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--candidate-edges", required=False, type=Path, help="Deprecated; candidate edges are rebuilt from risk episodes.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--targets-per-relation", type=int, default=1)
    args = parser.parse_args()

    events = pd.read_csv(args.events)
    episodes = coalesce_risk_events(events)
    candidates = build_propagation_edges(episodes)
    direct = select_direct_propagation_edges(candidates, max_targets_per_relation=args.targets_per_relation)
    roles = score_event_roles(episodes, direct)
    interventions = rank_intervention_candidates(episodes, direct, roles)
    summary = summarise_propagation(episodes, direct, candidate_edges=candidates)
    raw_counts = events.groupby("run_id").size().rename("raw_event_count") if not events.empty else pd.Series(dtype=int)
    summary = summary.merge(raw_counts, left_on="run_id", right_index=True, how="left")
    summary["raw_event_count"] = summary["raw_event_count"].fillna(0).astype(int)

    args.output.mkdir(parents=True, exist_ok=True)
    events.to_csv(args.output / "risk_events.csv", index=False)
    episodes.to_csv(args.output / "risk_episodes.csv", index=False)
    candidates.to_csv(args.output / "risk_candidate_edges.csv", index=False)
    direct.to_csv(args.output / "risk_direct_edges.csv", index=False)
    roles.to_csv(args.output / "risk_node_roles.csv", index=False)
    interventions.to_csv(args.output / "intervention_candidates.csv", index=False)
    summary.to_csv(args.output / "risk_summary.csv", index=False)
    cases = create_visual_package(episodes, direct, roles, args.output)
    figures = args.output / "figures"
    plot_method_flow(figures / "00_method_flow.png")
    plot_edge_selection(candidates, direct, figures / "04_edge_selection.png")
    plot_intervention_screening(interventions, figures / "05_intervention_screening.png")
    _write_readout(args.output, summary, roles, cases, interventions)

    print(f"direct edges: {len(direct)} / {len(candidates)} candidates")
    print(f"output: {args.output}")


def _write_readout(
    output_dir: Path,
    summary: pd.DataFrame,
    roles: pd.DataFrame,
    cases: pd.DataFrame,
    interventions: pd.DataFrame,
) -> None:
    result = summary.iloc[0].to_dict() if not summary.empty else {}
    top_sources = roles.sort_values("source_score", ascending=False).head(5)
    lines = [
        "# 真实 Flow merge 风险传播图：阶段结果",
        "",
        "## 当前结果",
        "",
        f"- 原始逐帧风险事件数：{int(result.get('raw_event_count', 0))}",
        f"- 合并后的风险事件片段数：{int(result.get('event_count', 0))}",
        f"- 候选传播边数：{int(result.get('candidate_edge_count', 0))}",
        f"- 直接传播边数：{int(result.get('edge_count', 0))}",
        f"- 边筛选保留率：{float(result.get('edge_selection_rate', 0.0)):.3f}",
        f"- 平均直接传播延迟：{float(result.get('mean_delay_s', 0.0)):.3f} s",
        f"- 平均直接传播距离：{float(result.get('mean_distance_m', 0.0)):.3f} m",
        "- 非局部传播：当前输入没有有效 lane 字段，未经验证的长距离同车道边已被剔除，暂不评价。",
        "",
        "## 这说明什么",
        "",
        "当前结果将原始时空候选关系筛成每类关系中最强的直接后续事件，因此风险图不再把五秒窗口内的所有事件都当作传播链。由于当前真实 emission 没有有效 lane 字段，未经验证的长距离同车道边已被剔除。该图用于阶段性解释，不构成严格因果证明；后续需要多随机种子和反事实重仿真验证。",
        "",
        "## Top-5 风险源事件",
        "",
        "| 排名 | 事件 | 车辆 | 类型 | source score |",
        "|---:|---|---|---|---:|",
    ]
    for index, row in enumerate(top_sources.itertuples(), start=1):
        lines.append(f"| {index} | {row.event_id} | {row.vehicle_id} | {row.event_type} | {float(row.source_score):.3f} |")
    lines.extend(["", "## 干预候选筛选", "", "下表是基于已观察到的直接风险图进行的筛选，不是闭环重仿真的处理效应。它的用途是确定后续最值得修改的车辆/事件。", "", "| 排名 | 事件 | 车辆 | 可达下游事件数 | 筛选优先级 |", "|---:|---|---|---:|---:|"])
    for index, row in enumerate(interventions.head(5).itertuples(), start=1):
        lines.append(f"| {index} | {row.event_id} ({row.event_type}) | {row.vehicle_id} | {int(row.reachable_event_count)} | {float(row.intervention_priority):.3f} |")
    lines.extend(["", "## 典型风险链", ""])
    for row in cases.itertuples():
        lines.append(f"- {row.case_id}：`{row.root_event_type}` on `{row.root_vehicle_id}` at {float(row.root_time_s):.1f}s，包含 {int(row.event_count)} 个事件和 {int(row.edge_count)} 条直接边，见 `{row.figure}`。")
    (output_dir / "阶段结果说明.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
