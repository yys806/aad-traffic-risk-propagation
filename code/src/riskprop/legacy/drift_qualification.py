"""Qualification checks for using DRIFT rollouts in risk-propagation studies."""

from __future__ import annotations

from itertools import product
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from riskprop.legacy.events import coalesce_risk_events, extract_risk_events


MISSING_TEXT = {"", "nan", "none", "null", "unknown"}
RAW_REQUIRED_COLUMNS = {
    "time",
    "id",
    "x",
    "y",
    "speed",
    "headway",
    "leader_id",
    "realized_accel",
    "edge_id",
    "lane_number",
    "leader_rel_speed",
}


def audit_formal_coverage(
    coverage: pd.DataFrame,
    *,
    scenarios: Iterable[str],
    methods: Iterable[str],
    penetrations: Iterable[int],
    expected_runs: int,
) -> dict[str, object]:
    """Check that every requested formal experiment cell has per-run evidence."""
    expected = {
        (str(scenario), str(method), int(penetration))
        for scenario, method, penetration in product(scenarios, methods, penetrations)
    }
    indexed = {}
    for row in coverage.to_dict("records"):
        key = (str(row["scenario"]), str(row["method"]), int(row["penetration_pct"]))
        indexed[key] = row

    missing = []
    complete_cells = 0
    for key in sorted(expected):
        row = indexed.get(key)
        complete = bool(
            row
            and str(row.get("expected", "yes")).lower() == "yes"
            and str(row.get("has_per_run", "no")).lower() == "yes"
            and int(row.get("run_count", 0)) >= expected_runs
        )
        if complete:
            complete_cells += 1
        else:
            missing.append(
                {"scenario": key[0], "method": key[1], "penetration_pct": key[2]}
            )

    return {
        "complete": complete_cells == len(expected),
        "expected_cells": len(expected),
        "complete_cells": complete_cells,
        "missing_cells": missing,
        "expected_runs_per_cell": int(expected_runs),
    }


def compare_drift_with_baselines(
    metrics: pd.DataFrame,
    *,
    metric_directions: Mapping[str, str],
    drift_method: str = "ours",
) -> pd.DataFrame:
    """Compare DRIFT with every available baseline on like-for-like cells."""
    key_columns = ["scenario"]
    if "penetration_pct" in metrics.columns:
        key_columns.append("penetration_pct")

    rows: list[dict[str, object]] = []
    for key, group in metrics.groupby(key_columns, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        cell = dict(zip(key_columns, key_values))
        drift_rows = group.loc[group["method"] == drift_method]
        if drift_rows.empty:
            continue
        drift = drift_rows.iloc[0]
        for _, baseline in group.loc[group["method"] != drift_method].iterrows():
            for metric, direction in metric_directions.items():
                if metric not in metrics.columns:
                    continue
                drift_value = pd.to_numeric(pd.Series([drift.get(metric)]), errors="coerce").iloc[0]
                baseline_value = pd.to_numeric(pd.Series([baseline.get(metric)]), errors="coerce").iloc[0]
                if pd.isna(drift_value) or pd.isna(baseline_value):
                    continue
                if direction not in {"higher", "lower"}:
                    raise ValueError(f"Unsupported direction for {metric}: {direction}")
                raw_delta = float(drift_value) - float(baseline_value)
                signed = raw_delta if direction == "higher" else -raw_delta
                rows.append(
                    {
                        **cell,
                        "baseline": str(baseline["method"]),
                        "metric": metric,
                        "direction": direction,
                        "drift_value": float(drift_value),
                        "baseline_value": float(baseline_value),
                        "signed_improvement": signed,
                        "drift_better": signed > 1e-12,
                        "tie": abs(signed) <= 1e-12,
                    }
                )
    return pd.DataFrame(rows)


def compare_with_confidence_intervals(
    statistics: pd.DataFrame,
    *,
    metric_specs: Mapping[str, tuple[str, str, str]],
    drift_method: str = "ours",
) -> pd.DataFrame:
    """Compare mean +/- 95% CI intervals on matching experiment cells."""
    key_columns = ["scenario"]
    if "penetration_pct" in statistics.columns:
        key_columns.append("penetration_pct")
    rows: list[dict[str, object]] = []
    for key, group in statistics.groupby(key_columns, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        cell = dict(zip(key_columns, key_values))
        drift_rows = group.loc[group["method"] == drift_method]
        if drift_rows.empty:
            continue
        drift = drift_rows.iloc[0]
        for _, baseline in group.loc[group["method"] != drift_method].iterrows():
            for metric, (mean_column, ci_column, direction) in metric_specs.items():
                values = [drift.get(mean_column), drift.get(ci_column), baseline.get(mean_column), baseline.get(ci_column)]
                numeric = pd.to_numeric(pd.Series(values), errors="coerce")
                if numeric.isna().any():
                    continue
                drift_mean, drift_ci, baseline_mean, baseline_ci = map(float, numeric)
                drift_low, drift_high = drift_mean - drift_ci, drift_mean + drift_ci
                baseline_low, baseline_high = baseline_mean - baseline_ci, baseline_mean + baseline_ci
                if direction == "higher":
                    confidently_better = drift_low > baseline_high
                    confidently_worse = drift_high < baseline_low
                elif direction == "lower":
                    confidently_better = drift_high < baseline_low
                    confidently_worse = drift_low > baseline_high
                else:
                    raise ValueError(f"Unsupported direction for {metric}: {direction}")
                rows.append(
                    {
                        **cell,
                        "baseline": str(baseline["method"]),
                        "metric": metric,
                        "direction": direction,
                        "drift_mean": drift_mean,
                        "drift_ci95": abs(drift_ci),
                        "baseline_mean": baseline_mean,
                        "baseline_ci95": abs(baseline_ci),
                        "confidently_better": confidently_better,
                        "confidently_worse": confidently_worse,
                        "intervals_overlap": not confidently_better and not confidently_worse,
                    }
                )
    return pd.DataFrame(rows)


def audit_pilot_events(
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    *,
    extreme_deceleration_mps2: float = -15.0,
    long_low_ttc_duration_s: float = 5.0,
    max_unknown_lane_rate: float = 0.05,
) -> dict[str, object]:
    """Audit whether derived risk events retain physically meaningful semantics."""
    identity_columns = [
        column for column in ("run_id", "time", "vehicle_id") if column in events.columns
    ]
    audit_rows = events.drop_duplicates(identity_columns) if identity_columns else events

    leader = audit_rows.get("leader_id", pd.Series(index=audit_rows.index, dtype=object))
    leader_text = leader.fillna("").astype(str).str.strip().str.lower()
    missing_leader = leader_text.isin(MISSING_TEXT)

    ttc = pd.to_numeric(audit_rows.get("ttc", pd.Series(index=audit_rows.index)), errors="coerce")
    finite_ttc = pd.Series(np.isfinite(ttc.to_numpy(dtype=float, na_value=np.nan)), index=audit_rows.index)
    finite_without_leader = missing_leader & finite_ttc

    lane = audit_rows.get("lane", pd.Series(index=audit_rows.index, dtype=object))
    lane_text = lane.fillna("").astype(str).str.strip().str.lower()
    unknown_lane = lane_text.isin(MISSING_TEXT)
    unknown_lane_rate = float(unknown_lane.mean()) if len(audit_rows) else 1.0

    acceleration = pd.to_numeric(
        audit_rows.get("acceleration", pd.Series(index=audit_rows.index)), errors="coerce"
    )
    extreme_deceleration = acceleration < extreme_deceleration_mps2

    episode_type = episodes.get(
        "event_type", pd.Series(index=episodes.index, dtype=object)
    ).fillna("").astype(str)
    duration = pd.to_numeric(
        episodes.get("episode_duration_s", pd.Series(index=episodes.index)), errors="coerce"
    )
    long_low_ttc = episode_type.isin({"low_ttc", "critical_ttc"}) & (
        duration > long_low_ttc_duration_s
    )

    result = {
        "event_count": int(len(events)),
        "physical_row_count": int(len(audit_rows)),
        "episode_count": int(len(episodes)),
        "finite_ttc_without_leader_count": int(finite_without_leader.sum()),
        "finite_ttc_without_leader_rate": float(finite_without_leader.mean()) if len(audit_rows) else 1.0,
        "unknown_lane_count": int(unknown_lane.sum()),
        "unknown_lane_rate": unknown_lane_rate,
        "extreme_deceleration_count": int(extreme_deceleration.sum()),
        "minimum_acceleration_mps2": _finite_min(acceleration),
        "long_low_ttc_episode_count": int(long_low_ttc.sum()),
        "maximum_low_ttc_episode_duration_s": _finite_max(duration[episode_type.isin({"low_ttc", "critical_ttc"})]),
        "thresholds": {
            "extreme_deceleration_mps2": extreme_deceleration_mps2,
            "long_low_ttc_duration_s": long_low_ttc_duration_s,
            "max_unknown_lane_rate": max_unknown_lane_rate,
        },
    }
    result["passed"] = bool(
        result["finite_ttc_without_leader_count"] == 0
        and result["unknown_lane_rate"] <= max_unknown_lane_rate
        and result["extreme_deceleration_count"] == 0
        and result["long_low_ttc_episode_count"] == 0
    )
    return result


def audit_raw_emission_files(
    paths: Iterable[Path],
    *,
    ttc_threshold_s: float = 2.0,
    thw_threshold_s: float = 1.0,
    extreme_deceleration_mps2: float = -15.0,
) -> dict[str, object]:
    """Stream raw Flow emissions and audit schema, metadata, and safety tails."""
    files = [Path(path) for path in paths]
    missing_by_file: dict[str, list[str]] = {}
    scenario_counts: dict[str, int] = {}
    row_count = 0
    lane_missing_count = 0
    leader_row_count = 0
    ttc_valid_count = 0
    ttc_violation_count = 0
    thw_valid_count = 0
    thw_violation_count = 0
    extreme_deceleration_count = 0
    minimum_acceleration: float | None = None

    for path in files:
        scenario = path.name.split("_", 1)[0]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        columns = set(pd.read_csv(path, nrows=0).columns)
        missing = sorted(RAW_REQUIRED_COLUMNS - columns)
        if missing:
            missing_by_file[path.name] = missing
        usecols = sorted(RAW_REQUIRED_COLUMNS & columns)
        for chunk in pd.read_csv(path, usecols=usecols, chunksize=200_000):
            count = len(chunk)
            row_count += count

            edge = chunk.get("edge_id", pd.Series(index=chunk.index, dtype=object))
            lane_number = chunk.get("lane_number", pd.Series(index=chunk.index, dtype=object))
            edge_text = edge.fillna("").astype(str).str.strip().str.lower()
            lane_missing = edge_text.isin(MISSING_TEXT) | pd.to_numeric(
                lane_number, errors="coerce"
            ).isna()
            lane_missing_count += int(lane_missing.sum())

            leader = chunk.get("leader_id", pd.Series(index=chunk.index, dtype=object))
            leader_text = leader.fillna("").astype(str).str.strip().str.lower()
            has_leader = leader.notna() & ~leader_text.isin(MISSING_TEXT)
            leader_row_count += int(has_leader.sum())

            headway = pd.to_numeric(
                chunk.get("headway", pd.Series(index=chunk.index)), errors="coerce"
            )
            finite_headway = headway.notna() & (headway > 0) & (headway < 1e5)
            speed = pd.to_numeric(
                chunk.get("speed", pd.Series(index=chunk.index)), errors="coerce"
            )
            closing = -pd.to_numeric(
                chunk.get("leader_rel_speed", pd.Series(index=chunk.index)), errors="coerce"
            )
            ttc_mask = has_leader & finite_headway & closing.notna() & (closing > 1e-3)
            if ttc_mask.any():
                ttc = headway[ttc_mask] / closing[ttc_mask]
                ttc_valid_count += int(ttc.notna().sum())
                ttc_violation_count += int((ttc < ttc_threshold_s).sum())

            thw_mask = has_leader & finite_headway & speed.notna() & (speed > 1e-3)
            if thw_mask.any():
                thw = headway[thw_mask] / speed[thw_mask]
                thw_valid_count += int(thw.notna().sum())
                thw_violation_count += int((thw < thw_threshold_s).sum())

            acceleration = pd.to_numeric(
                chunk.get("realized_accel", pd.Series(index=chunk.index)), errors="coerce"
            )
            finite_acceleration = acceleration[np.isfinite(acceleration)]
            extreme_deceleration_count += int(
                (finite_acceleration < extreme_deceleration_mps2).sum()
            )
            if not finite_acceleration.empty:
                current_minimum = float(finite_acceleration.min())
                minimum_acceleration = (
                    current_minimum
                    if minimum_acceleration is None
                    else min(minimum_acceleration, current_minimum)
                )

    return {
        "file_count": len(files),
        "scenario_file_counts": scenario_counts,
        "row_count": row_count,
        "required_columns_complete": not missing_by_file and bool(files),
        "missing_columns_by_file": missing_by_file,
        "lane_metadata_missing_count": lane_missing_count,
        "lane_metadata_missing_rate": lane_missing_count / row_count if row_count else 1.0,
        "leader_row_count": leader_row_count,
        "ttc_valid_count": ttc_valid_count,
        "ttc_violation_count": ttc_violation_count,
        "ttc_violation_rate": ttc_violation_count / ttc_valid_count if ttc_valid_count else None,
        "thw_valid_count": thw_valid_count,
        "thw_violation_count": thw_violation_count,
        "thw_violation_rate": thw_violation_count / thw_valid_count if thw_valid_count else None,
        "extreme_deceleration_count": extreme_deceleration_count,
        "extreme_deceleration_rate": extreme_deceleration_count / row_count if row_count else None,
        "minimum_acceleration_mps2": minimum_acceleration,
        "thresholds": {
            "ttc_threshold_s": ttc_threshold_s,
            "thw_threshold_s": thw_threshold_s,
            "extreme_deceleration_mps2": extreme_deceleration_mps2,
        },
    }


def extract_validated_risk_events(
    paths: Iterable[Path],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract leader-aware events from raw files while preserving run identity."""
    event_frames: list[pd.DataFrame] = []
    for path in (Path(item) for item in paths):
        emissions = pd.read_csv(path)
        emissions["run_id"] = path.stem
        events = extract_risk_events(emissions)
        if not events.empty:
            event_frames.append(events)
    if not event_frames:
        empty = extract_risk_events(pd.DataFrame())
        return empty, coalesce_risk_events(empty)

    events = pd.concat(event_frames, ignore_index=True)
    events["event_id"] = [f"e{i:07d}" for i in range(len(events))]
    episodes = coalesce_risk_events(events)
    return events, episodes


def build_extreme_deceleration_catalog(
    paths: Iterable[Path],
    *,
    threshold_mps2: float = -15.0,
) -> pd.DataFrame:
    """Build a frame-level catalog for manually checking implausible speed jumps."""
    frames: list[pd.DataFrame] = []
    for path in (Path(item) for item in paths):
        rows = pd.read_csv(path)
        required = {"time", "id", "speed", "realized_accel"}
        if not required.issubset(rows.columns):
            continue
        for column in ("time", "speed", "realized_accel"):
            rows[column] = pd.to_numeric(rows[column], errors="coerce")
        rows = rows.sort_values(["id", "time"]).copy()
        rows["previous_time_s"] = rows.groupby("id")["time"].shift()
        rows["previous_speed_mps"] = rows.groupby("id")["speed"].shift()
        rows["next_time_s"] = rows.groupby("id")["time"].shift(-1)
        rows["next_speed_mps"] = rows.groupby("id")["speed"].shift(-1)
        dt = rows["time"] - rows["previous_time_s"]
        rows["observed_dvdt_mps2"] = (rows["speed"] - rows["previous_speed_mps"]) / dt
        rows["is_last_vehicle_row"] = rows["next_time_s"].isna()
        rows["acceleration_matches_speed_jump"] = (
            rows["realized_accel"] - rows["observed_dvdt_mps2"]
        ).abs() <= 1e-6
        if {"edge_id", "lane_number"}.issubset(rows.columns):
            lane_number = pd.to_numeric(rows["lane_number"], errors="coerce")
            rows["lane"] = rows["edge_id"].fillna("unknown").astype(str) + ":" + lane_number.map(
                lambda value: str(int(value)) if pd.notna(value) else "unknown"
            )
        else:
            rows["lane"] = "unknown"
        extreme = rows.loc[rows["realized_accel"] < threshold_mps2].copy()
        if extreme.empty:
            continue
        extreme.insert(0, "source_file", path.name)
        extreme["review_class"] = np.where(
            extreme["acceleration_matches_speed_jump"],
            "speed_jump_beyond_controller_limit",
            "acceleration_field_mismatch",
        )
        frames.append(extreme)

    columns = [
        "source_file",
        "time",
        "id",
        "leader_id",
        "lane",
        "headway",
        "leader_rel_speed",
        "previous_time_s",
        "previous_speed_mps",
        "speed",
        "next_time_s",
        "next_speed_mps",
        "realized_accel",
        "observed_dvdt_mps2",
        "acceleration_matches_speed_jump",
        "is_last_vehicle_row",
        "review_class",
    ]
    if not frames:
        return pd.DataFrame(columns=columns)
    catalog = pd.concat(frames, ignore_index=True)
    for column in columns:
        if column not in catalog.columns:
            catalog[column] = pd.NA
    return catalog[columns].sort_values(["source_file", "time", "id"]).reset_index(drop=True)


def qualification_decision(
    *,
    coverage_passed: bool,
    formal_evidence_passed: bool,
    pilot_input_passed: bool,
    raw_emissions_available: bool,
    pilot_audit: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Apply the gate between DRIFT validation and causal propagation analysis."""
    if not coverage_passed or not formal_evidence_passed:
        return {
            "status": "HOLD",
            "may_start_causal_propagation": False,
            "next_action": "先补齐正式基线、消融和多次运行证据，再评估 DRIFT。",
        }
    if not pilot_input_passed:
        audit = dict(pilot_audit or {})
        schema_ready = bool(
            raw_emissions_available
            and int(audit.get("finite_ttc_without_leader_count", 1)) == 0
            and float(audit.get("unknown_lane_rate", 1.0)) <= 0.05
        )
        if schema_ready and (
            int(audit.get("extreme_deceleration_count", 0)) > 0
            or int(audit.get("long_low_ttc_episode_count", 0)) > 0
        ):
            return {
                "status": "HOLD",
                "may_start_causal_propagation": False,
                "next_action": "逐条核查极端减速度和长时低 TTC 片段，区分真实冲突、控制器急变与仿真离散伪影。",
            }
        action = "回到原始 emission 修复 leader、lane、TTC 和加速度字段语义。"
        if not raw_emissions_available:
            action = "取得原始 emission，再修复 leader、lane、TTC 和加速度字段语义。"
        return {
            "status": "HOLD",
            "may_start_causal_propagation": False,
            "next_action": action,
        }
    return {
        "status": "PASS",
        "may_start_causal_propagation": True,
        "next_action": "在固定种子和多基线下开始局部传播与非局部候选检验。",
    }


def write_qualification_outputs(
    *,
    output_dir: Path,
    coverage: Mapping[str, object],
    comparison: pd.DataFrame,
    pilot_audit: Mapping[str, object],
    decision: Mapping[str, object],
    extra_summary: Mapping[str, object] | None = None,
) -> dict[str, Path]:
    """Write the audit tables and a concise Chinese report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "qualification_summary.json"
    comparison_csv = output_dir / "formal_baseline_comparison.csv"
    report_md = output_dir / "DRIFT资格验证报告.md"

    comparison.to_csv(comparison_csv, index=False, encoding="utf-8-sig")
    wins = int(comparison.get("drift_better", pd.Series(dtype=bool)).sum())
    ties = int(comparison.get("tie", pd.Series(dtype=bool)).sum())
    total = int(len(comparison))
    extra = dict(extra_summary or {})
    summary = {
        "coverage": dict(coverage),
        "formal_comparison": {
            "comparison_count": total,
            "drift_win_count": wins,
            "tie_count": ties,
            "drift_win_rate_excluding_ties": (
                wins / (total - ties) if total > ties else None
            ),
        },
        "pilot_input_audit": dict(pilot_audit),
        "decision": dict(decision),
        **extra,
    }
    summary_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    status_text = "通过" if decision.get("status") == "PASS" else "暂缓"
    metric_lines = ["| 指标 | 可比项 | DRIFT 更好 | 并列 |", "|---|---:|---:|---:|"]
    if not comparison.empty and "metric" in comparison.columns:
        for metric, group in comparison.groupby("metric"):
            metric_lines.append(
                f"| {metric} | {len(group)} | {int(group['drift_better'].sum())} | {int(group['tie'].sum())} |"
            )

    candidate_fit = extra.get("candidate_fit", {})
    confidence = extra.get("confidence_interval_summary", {})
    confidence_section = ""
    if isinstance(confidence, Mapping) and confidence:
        confidence_section = f"""
## 95% 置信区间检查

- 可比较项：{confidence.get('comparison_count', 0)}。
- DRIFT 区间整体优于基线：{confidence.get('confidently_better_count', 0)} 项。
- DRIFT 区间整体劣于基线：{confidence.get('confidently_worse_count', 0)} 项。
- 区间重叠：{confidence.get('overlap_count', 0)} 项。

该判断采用保守的置信区间不重叠规则，不等同于完整的配对显著性检验。
"""
    candidate_section = ""
    if isinstance(candidate_fit, Mapping) and candidate_fit:
        candidate_section = f"""
## 候选生成检查

- 单候选拟合误差：{candidate_fit.get('single_candidate', '未提供')}。
- 固定 $K=5$ 拟合误差：{candidate_fit.get('fixed_k5', '未提供')}。
- 学习式 $K=5$ 拟合误差：{candidate_fit.get('learned_k5', '未提供')}。
"""

    raw = extra.get("raw_emission_audit", {})
    raw_by_scenario = extra.get("raw_emission_audit_by_scenario", {})
    raw_section = ""
    if isinstance(raw, Mapping) and raw:
        raw_section = f"""
## 原始 emission 审计

- 文件数：{raw.get('file_count', '未提供')}；总行数：{raw.get('row_count', '未提供')}。
- 必要字段完整：{raw.get('required_columns_complete', '未提供')}。
- 车道元数据缺失率：{_format_percent(raw.get('lane_metadata_missing_rate'))}。
- 有效 TTC 中低于阈值的比例：{_format_percent(raw.get('ttc_violation_rate'))}。
- 有效 THW 中低于阈值的比例：{_format_percent(raw.get('thw_violation_rate'))}。
- 极端减速度记录：{raw.get('extreme_deceleration_count', '未提供')}；最小加速度：{raw.get('minimum_acceleration_mps2', '未提供')} m/s²。
"""
        if isinstance(raw_by_scenario, Mapping) and raw_by_scenario:
            scenario_lines = [
                "### 原始数据按场景",
                "",
                "| 场景 | 文件 | 数据行 | TTC违例率 | THW违例率 | 极端减速度 | 最小加速度 |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
            for scenario, values in raw_by_scenario.items():
                scenario_lines.append(
                    f"| {scenario} | {values.get('file_count', 0)} | {values.get('row_count', 0)} | "
                    f"{_format_percent(values.get('ttc_violation_rate'))} | "
                    f"{_format_percent(values.get('thw_violation_rate'))} | "
                    f"{values.get('extreme_deceleration_count', 0)} | "
                    f"{values.get('minimum_acceleration_mps2', '未提供')} |"
                )
            raw_section += "\n" + "\n".join(scenario_lines) + "\n"

    formal_gate = "通过" if extra.get("formal_evidence_passed") else "未通过"
    raw_schema_gate = (
        "通过"
        if isinstance(raw, Mapping)
        and raw.get("required_columns_complete")
        and float(raw.get("lane_metadata_missing_rate", 1.0)) <= 0.05
        else "未通过"
    )
    risk_gate = "通过" if pilot_audit.get("passed") else "暂缓"
    extreme_rows = int(extra.get("validated_merge_p20_extreme_rows", 0))
    speed_jump_matches = int(extra.get("validated_merge_p20_speed_jump_matches", 0))
    terminal_extremes = int(extra.get("validated_merge_p20_terminal_extreme_rows", 0))
    tail_section = ""
    if extreme_rows:
        tail_section = f"""
### Merge p20 极端点复核

- 5 个运行中共有 {extreme_rows} 个去重后的极端减速度时刻。
- 其中 {speed_jump_matches} 个与相邻帧速度跳变完全一致，说明不是加速度列单独写错。
- 位于车辆最后一条记录的异常点为 {terminal_extremes} 个，不能简单归因于车辆退出记录。
- DRIFT 控制器命令有减速度限幅，而实际速度仍出现更大突变，因此这些点应作为 SUMO 安全速度覆盖或交互冲突候选单独核查，不能直接当作普通急刹传播。
"""

    ood = extra.get("ood_method_summary", [])
    ood_section = ""
    if isinstance(ood, list) and ood:
        ood_lines = [
            "## OOD/压力测试",
            "",
            "| 方法 | Return | Speed | TTC违例率 | HB10 | 最差加速度 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row in ood:
            ood_lines.append(
                "| {method} | {ret:.3f} | {speed:.3f} | {ttc:.4f} | {hb:.3f} | {acc:.3f} |".format(
                    method=row.get("method", ""),
                    ret=float(row.get("mean_return", 0.0)),
                    speed=float(row.get("mean_speed", 0.0)),
                    ttc=float(row.get("mean_ttc_violation", 0.0)),
                    hb=float(row.get("mean_hb10", 0.0)),
                    acc=float(row.get("worst_min_accel", 0.0)),
                )
            )
        ood_lines.extend(
            [
                "",
                "该组结果用于检查分布外稳定性。它显示 DRIFT 的安全尾部有优势，但效率和 TTC 并非全面领先。",
                "",
            ]
        )
        ood_section = "\n".join(ood_lines)

    report = f"""# DRIFT 资格验证报告

## 结论

当前结论：**{status_text}风险传播与因果实验**。

DRIFT 的正式实验覆盖和相对基线表现可以支持继续研究，但不支持“所有场景、所有指标全面领先”的说法。风险传播输入是否可用是独立门槛，不能由闭环 return 或速度结果代替。

## 分层门槛

- DRIFT 性能证据：**{formal_gate}**。
- 原始 emission 字段与车道元数据：**{raw_schema_gate}**。
- 当前风险事件输入：**{risk_gate}**。

## 正式实验审计

- 完整单元：{coverage.get('complete_cells', 0)}/{coverage.get('expected_cells', 0)}。
- 可比指标数：{total}。
- DRIFT 优于对应基线：{wins} 项；并列：{ties} 项。
- 该统计只描述现有结果，不把不同安全、效率指标简单合成为一个总分。

{chr(10).join(metric_lines)}

{confidence_section}

{candidate_section}

{ood_section}

{raw_section}

## 风险输入审计

- 风险事件数：{pilot_audit.get('event_count', '未提供')}。
- 去重后的物理时刻数：{pilot_audit.get('physical_row_count', '未提供')}。
- 无前车但 TTC 有限：{pilot_audit.get('finite_ttc_without_leader_count', '未提供')}。
- 未知车道比例：{_format_percent(pilot_audit.get('unknown_lane_rate'))}。
- 极端减速度记录：{pilot_audit.get('extreme_deceleration_count', '未提供')}。
- 超过阈值的长时低 TTC 片段：{pilot_audit.get('long_low_ttc_episode_count', '未提供')}。

{tail_section}

## 下一步

{decision.get('next_action', '')}

当前审计、统计和报告生成只使用 CPU。重新训练 DRIFT、Flow-AIL 或 Flow-RL 时才需要 GPU。
"""
    report_md.write_text(report, encoding="utf-8")
    return {
        "summary_json": summary_json,
        "comparison_csv": comparison_csv,
        "report_md": report_md,
    }


def _finite_min(values: pd.Series) -> float | None:
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric[np.isfinite(numeric)]
    return float(numeric.min()) if not numeric.empty else None


def _finite_max(values: pd.Series) -> float | None:
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric[np.isfinite(numeric)]
    return float(numeric.max()) if not numeric.empty else None


def _format_percent(value: object) -> str:
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "未提供"
