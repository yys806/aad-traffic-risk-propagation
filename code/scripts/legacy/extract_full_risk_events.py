from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.legacy.risk_event_dataset import (  # noqa: E402
    discover_formal_emissions,
    extract_formal_event_dataset,
)
from riskprop.legacy.risk_event_visuals import create_risk_event_visual_package  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract the formal risk-event dataset with exposure-normalized rates."
    )
    parser.add_argument(
        "--raw-output-root",
        required=True,
        type=Path,
        help="Root containing formal Flow emission output directories.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "risk_event_dataset_20260716",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = discover_formal_emissions(args.raw_output_root)
    if not paths:
        raise FileNotFoundError(f"No formal emission files found under {args.raw_output_root}")
    dataset = extract_formal_event_dataset(paths)
    args.output.mkdir(parents=True, exist_ok=True)

    output_names = {
        "manifest": "extraction_manifest.csv",
        "events": "risk_events.csv",
        "episodes": "risk_episodes.csv",
        "event_rates_by_run": "event_rates_by_run.csv",
        "event_rates_summary": "event_rates_summary.csv",
        "threshold_sensitivity_by_run": "threshold_sensitivity_by_run.csv",
        "threshold_sensitivity_summary": "threshold_sensitivity_summary.csv",
        "threshold_sensitivity_comparison": "threshold_sensitivity_comparison.csv",
        "manual_review_sample": "manual_review_sample.csv",
    }
    for key, filename in output_names.items():
        dataset[key].to_csv(args.output / filename, index=False)

    taxonomy = {
        "hard_braking": {
            "definition": "-15 m/s^2 <= realized_accel <= -3 m/s^2",
            "severity": {"hard": "(-6, -3] m/s^2", "severe": "[-15, -6] m/s^2"},
            "propagation_input": "eligible after manual review",
        },
        "safe_speed_override_candidate": {
            "definition": "realized_accel < -15 m/s^2",
            "meaning": "SUMO safe-speed override or closed-loop interaction candidate; not ordinary braking",
            "propagation_input": "excluded until manually classified",
        },
        "low_ttc": {"definition": "leader-aware TTC <= 2 s"},
        "critical_ttc": {"definition": "leader-aware TTC <= 1 s"},
        "low_thw": {"definition": "leader-aware THW <= 1 s"},
        "near_miss": {"definition": "leader-aware TTC <= 1.5 s and realized_accel <= -3 m/s^2"},
        "rate_denominator": "1000 vehicle-seconds of observed exposure",
        "ttc_sensitivity_s": [1.0, 1.5, 2.0, 3.0],
        "braking_sensitivity_mps2": [-3.0, -4.5, -6.0],
    }
    (args.output / "event_taxonomy.json").write_text(
        json.dumps(taxonomy, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = _build_summary(dataset)
    (args.output / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    create_risk_event_visual_package(args.output)
    (args.output / "事件提取与敏感性报告.md").write_text(
        _render_report(dataset, summary), encoding="utf-8"
    )

    print(f"files={summary['file_count']}")
    print(f"rows={summary['row_count']}")
    print(f"events={summary['event_count']}")
    print(f"episodes={summary['episode_count']}")
    print(f"output={args.output}")
    return 0


def _build_summary(dataset: dict[str, pd.DataFrame]) -> dict[str, object]:
    manifest = dataset["manifest"]
    events = dataset["events"]
    episodes = dataset["episodes"]
    comparison = dataset["threshold_sensitivity_comparison"]
    review = dataset["manual_review_sample"]
    ordinary_episodes = episodes.loc[
        episodes.get("event_type", pd.Series(index=episodes.index, dtype=object))
        != "safe_speed_override_candidate"
    ]
    boundary = _bool_series(ordinary_episodes, "is_first_vehicle_row") | _bool_series(
        ordinary_episodes, "is_last_vehicle_row"
    )
    transition = (
        _bool_series(ordinary_episodes, "previous_leader_changed")
        | _bool_series(ordinary_episodes, "next_leader_changed")
        | _bool_series(ordinary_episodes, "previous_lane_changed")
        | _bool_series(ordinary_episodes, "next_lane_changed")
    )
    adjacent_override = _bool_series(ordinary_episodes, "adjacent_override_candidate")
    method_files = {
        str(method): int(count)
        for method, count in manifest.groupby("method")["source_file"].count().items()
    }
    scenario_files = {
        str(scenario): int(count)
        for scenario, count in manifest.groupby("scenario")["source_file"].count().items()
    }
    event_counts = {
        str(event_type): int(count)
        for event_type, count in events.groupby("event_type").size().items()
    } if not events.empty else {}
    episode_counts = {
        str(event_type): int(count)
        for event_type, count in episodes.groupby("event_type").size().items()
    } if not episodes.empty else {}
    return {
        "file_count": int(len(manifest)),
        "row_count": int(manifest["row_count"].sum()),
        "vehicle_time_s": float(manifest["vehicle_time_s"].sum()),
        "event_count": int(len(events)),
        "episode_count": int(len(episodes)),
        "method_file_counts": method_files,
        "scenario_file_counts": scenario_files,
        "event_counts": event_counts,
        "episode_counts": episode_counts,
        "sensitivity_comparison_count": int(len(comparison)),
        "drift_better_count": int(comparison["drift_better"].sum()) if not comparison.empty else 0,
        "tie_count": int(comparison["tie"].sum()) if not comparison.empty else 0,
        "manual_review_row_count": int(len(dataset["manual_review_sample"])),
        "manual_review_status_counts": {
            str(status): int(count)
            for status, count in review.groupby("review_status").size().items()
        },
        "manual_review_leader_transition_count": int(
            review["review_notes"].astype(str).str.contains("leader_transition").sum()
        ),
        "manual_review_lane_transition_count": int(
            review["review_notes"].astype(str).str.contains("lane_transition").sum()
        ),
        "manual_review_adjacent_override_count": int(
            review["review_notes"].astype(str).str.contains("adjacent_override").sum()
        ),
        "ordinary_episode_count": int(len(ordinary_episodes)),
        "boundary_episode_count": int(boundary.sum()),
        "interaction_transition_episode_count": int(transition.sum()),
        "adjacent_override_episode_count": int(adjacent_override.sum()),
        "local_baseline_eligible_episode_count": int((~boundary).sum()),
        "risk_propagation_input_status": "READY_FOR_LOCAL_BASELINE_WITH_EXCLUSIONS",
        "raw_event_baselines_available": ["fs", "pi"],
        "raw_event_baselines_unavailable": ["idm", "flow-ail", "flow-rl"],
        "gpu_required": False,
    }


def _render_report(
    dataset: dict[str, pd.DataFrame], summary: dict[str, object]
) -> str:
    manifest = dataset["manifest"]
    episodes = dataset["episodes"]
    comparison = dataset["threshold_sensitivity_comparison"]
    method_rows = "\n".join(
        f"- {method}: {count} 个文件"
        for method, count in summary["method_file_counts"].items()
    )
    episode_rows = "\n".join(
        f"- `{event_type}`: {count} 个片段"
        for event_type, count in summary["episode_counts"].items()
    ) or "- 未提取到事件片段"
    comparison_rows = []
    if not comparison.empty:
        grouped = comparison.groupby(["baseline", "metric", "threshold"], sort=True)
        for (baseline, metric, threshold), group in grouped:
            wins = int(group["drift_better"].sum())
            ties = int(group["tie"].sum())
            losses = int(len(group) - wins - ties)
            comparison_rows.append(
                f"- {baseline}, `{metric}`, 阈值 {threshold:g}: DRIFT {wins} 胜、{ties} 平、{losses} 负"
            )
    comparison_text = "\n".join(comparison_rows) or "- 没有可比较结果"
    override_episodes = int(
        (episodes.get("event_type", pd.Series(dtype=object)) == "safe_speed_override_candidate").sum()
    )
    exposure_hours = float(summary["vehicle_time_s"]) / 3600.0
    run_cells = (
        manifest.groupby(["scenario", "method", "penetration_pct"])["run_id"]
        .nunique()
        .reset_index()
    )
    incomplete_cells = int((run_cells["run_id"] != 5).sum())
    review_counts = summary["manual_review_status_counts"]
    return f"""# 风险事件全量提取与阈值敏感性报告

## 数据范围

本次使用正式实验目录中的 DRIFT、FS 和 PI 逐帧 emission。共处理 {summary['file_count']} 个文件、{summary['row_count']} 行记录，累计观测暴露为 {exposure_hours:.2f} 车辆小时。正式单元中运行数不等于 5 的单元有 {incomplete_cells} 个。

{method_rows}

IDM、Flow-AIL 和 Flow-RL 当前只有汇总指标，本地没有对应逐帧 emission，因此不生成它们的事件级结果。

## 事件分类

制动事件不再同时生成 hard 和 severe 两个标签。`hard_braking` 使用 `event_severity` 区分 hard 与 severe；实际减速度低于 -15 m/s² 的记录单列为 `safe_speed_override_candidate`。该类共形成 {override_episodes} 个片段，人工确认前不作为普通急刹传播输入。

TTC 只在前车有效、净间距有效且车辆正在接近前车时计算。所有发生率均以 1000 车辆秒为分母。

## 提取结果

共得到 {summary['event_count']} 条逐帧事件记录和 {summary['episode_count']} 个事件片段：

{episode_rows}

## 阈值敏感性

TTC 检查 1、1.5、2、3 秒，普通制动检查 -3、-4.5、-6 m/s²。以下数字按场景和渗透率逐单元比较暴露率，越低越好：

{comparison_text}

这些比较只说明事件发生率随阈值的变化，不等于风险传播或因果结论。

## 人工复核

`manual_review_sample.csv` 按事件类型各抽取 10 个片段，共 {summary['manual_review_row_count']} 条，保留前后帧速度、前车、车道、间距和加速度。复核结果为：保留 {review_counts.get('retained', 0)} 条，带上下文标志保留 {review_counts.get('retained_flagged', 0)} 条，排除 {review_counts.get('excluded', 0)} 条。

- 前车切换片段：{summary['manual_review_leader_transition_count']} 条；
- 车道切换片段：{summary['manual_review_lane_transition_count']} 条；
- 相邻帧存在覆盖候选：{summary['manual_review_adjacent_override_count']} 条。

全量片段中，去除覆盖候选后剩余 {summary['ordinary_episode_count']} 个风险片段，其中 {summary['boundary_episode_count']} 个位于车辆首末记录，{summary['interaction_transition_episode_count']} 个涉及前车或车道切换，{summary['adjacent_override_episode_count']} 个紧邻覆盖候选。局部传播基线可以使用 {summary['local_baseline_eligible_episode_count']} 个非首末边界片段，但必须排除 `safe_speed_override_candidate`，并分别报告稳定跟驰、交互切换和相邻覆盖三类结果。

当前输入状态记为 `READY_FOR_LOCAL_BASELINE_WITH_EXCLUSIONS`。该状态只允许进入局部一跳/多跳基线，不支持直接开始非局部因果发现。

## 计算资源

本次提取和统计只使用 CPU，没有重新训练模型。
"""


def _bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column].fillna(False).astype(bool)


if __name__ == "__main__":
    raise SystemExit(main())
