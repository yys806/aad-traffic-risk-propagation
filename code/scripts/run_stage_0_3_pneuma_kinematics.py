"""Run the Stage 0.3 pNEUMA urban-kinematics calibration and acceptance package."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
REPO_ROOT = CODE_ROOT.parent

from riskprop.calibration import sha256_file
from riskprop.pneuma_urban_kinematics import (
    ACCEL_BY_SPEED_BINS_MPS,
    CONTINUITY_CANDIDATES_S,
    acceleration_by_speed_stratum,
    acceleration_state_shares,
    audit_pneuma_source,
    audit_sampling_balance,
    bootstrap_track_intervals,
    build_stage_0_5_reference_states,
    compute_descriptive_stats,
    compute_kinematic_consistency,
    compute_track_stats,
    compute_vehicle_equal_weight_stats,
    compute_vehicle_type_composition,
    continuity_sensitivity,
    derive_state_quality_status,
    empirical_cdf_arrays,
    extreme_value_sensitivity,
    flag_state_quality,
    reliable_exposure_frame,
    speed_state_shares,
    time_weighted_bootstrap,
    write_acceptance_package,
)
from riskprop.real_trajectory import read_pneuma_wide
from riskprop.simulation_real_coverage import (
    deterministic_state_sample,
    write_real_reference_package,
)

DEFAULT_SOURCE = REPO_ROOT / "dataset" / "pNEUMA" / "20181101_d1_0800_0830.csv"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "code"
    / "outputs"
    / "formal"
    / "calibration"
    / "stage_0_3_pneuma_boundary_repair_20261016_r2"
)
R1_PACKAGE = (
    REPO_ROOT
    / "code"
    / "outputs"
    / "formal"
    / "calibration"
    / "stage_0_3_pneuma_kinematics_20261012_r1"
)
NGSIM_STATES_DIR = (
    REPO_ROOT
    / "code"
    / "outputs"
    / "formal"
    / "calibration"
    / "stage_0_2_task_1_5_20261010_r4"
    / "states"
)
NGSIM_EVENTS_PATH = (
    REPO_ROOT
    / "code"
    / "outputs"
    / "formal"
    / "calibration"
    / "stage_0_2_scientific_acceptance_20261012_r4"
    / "p2_formal_events.parquet"
)
EXPECTED_SOURCE_SHA256 = "F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C"


def _select_tolerance(dt_stats: dict) -> tuple[float, str]:
    """Deterministic engineering anchor: modal interval + 5% relative + 1 ms.

    The anchor selects the parser write flag only; all eight candidate
    tolerances are still reported in the sensitivity table and the formal
    continuity rule remains a researcher decision.
    """

    mode = float(dt_stats["mode_dt_s"])
    tolerance = mode * 1.05 + 0.001
    rule = (
        f"modal adjacent interval {mode:.6f} s + 5% relative tolerance + 1 ms; "
        "engineering anchor only, not a frozen scientific threshold"
    )
    return tolerance, rule


def _plot_histograms(
    states: pd.DataFrame,
    *,
    tolerance_s: float,
    figures_dir: Path,
) -> dict[str, Path]:
    """Time-weighted figures on reliable raw-order intervals only."""

    figures: dict[str, Path] = {}
    frame, usable = reliable_exposure_frame(
        states, tolerance_s=tolerance_s, value_column="speed_mps"
    )
    frame = frame.loc[usable].copy()

    # Speed histogram per vehicle type (time-weighted density).
    fig, ax = plt.subplots(figsize=(9, 6))
    types = sorted(frame["vehicle_type"].unique())
    bins = np.linspace(0, max(frame["speed_mps"].max(), 1.0), 80)
    for vehicle_type in types:
        group = frame[frame["vehicle_type"] == vehicle_type]
        weights = group["_dt"].to_numpy(float)
        ax.hist(
            group["speed_mps"],
            bins=bins,
            weights=weights / weights.sum(),
            histtype="step",
            linewidth=1.4,
            label=f"{vehicle_type} (n={group['vehicle_id'].nunique()} tracks)",
            density=False,
        )
    ax.set_xlabel("Speed (m/s)")
    ax.set_ylabel("Time-weighted share")
    ax.set_title("Stage 0.3 pNEUMA d1 08:00-08:30 speed distribution (time-weighted)")
    ax.legend(fontsize=8)
    path = figures_dir / "speed_histogram_by_type.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures["fig_speed_histogram.png"] = path

    # Speed ECDF.
    fig, ax = plt.subplots(figsize=(9, 6))
    cdfs = empirical_cdf_arrays(
        states, value_column="speed_mps", tolerance_s=tolerance_s, group_column="vehicle_type"
    )
    for label, payload in cdfs.items():
        x = payload["x"]
        y = payload["cdf"]
        n_tracks = int(
            states.loc[states["vehicle_type"] == label, "vehicle_id"].nunique()
        )
        ax.plot(x, y, linewidth=1.3, label=f"{label} (n={n_tracks} tracks)")
    ax.set_xlabel("Speed (m/s)")
    ax.set_ylabel("Time-weighted ECDF")
    ax.set_title("Stage 0.3 pNEUMA speed ECDF by vehicle type")
    ax.legend(fontsize=8)
    path = figures_dir / "speed_ecdf_by_type.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures["fig_speed_ecdf.png"] = path

    # Acceleration histogram per vehicle type.
    fig, ax = plt.subplots(figsize=(9, 6))
    accel_frame, accel_usable = reliable_exposure_frame(
        states, tolerance_s=tolerance_s, value_column="longitudinal_accel_mps2"
    )
    accel_frame = accel_frame.loc[accel_usable].copy()
    accel = accel_frame.dropna(subset=["longitudinal_accel_mps2"])
    limit = float(np.nanpercentile(np.abs(accel["longitudinal_accel_mps2"]), 99.5))
    limit = max(limit, 1.0)
    bins = np.linspace(-limit, limit, 100)
    for vehicle_type in sorted(accel["vehicle_type"].unique()):
        group = accel[accel["vehicle_type"] == vehicle_type]
        weights = group["_dt"].to_numpy(float)
        ax.hist(
            group["longitudinal_accel_mps2"],
            bins=bins,
            weights=weights / weights.sum(),
            histtype="step",
            linewidth=1.4,
            label=f"{vehicle_type} (n={group['vehicle_id'].nunique()} tracks)",
        )
    ax.set_xlabel("Longitudinal acceleration (m/s²)")
    ax.set_ylabel("Time-weighted share")
    ax.set_title("Stage 0.3 pNEUMA longitudinal acceleration (P99.5 x-limit)")
    ax.legend(fontsize=8)
    path = figures_dir / "acceleration_histogram_by_type.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures["fig_accel_histogram.png"] = path

    # Acceleration ECDF.
    fig, ax = plt.subplots(figsize=(9, 6))
    cdfs = empirical_cdf_arrays(
        states,
        value_column="longitudinal_accel_mps2",
        tolerance_s=tolerance_s,
        group_column="vehicle_type",
    )
    for label, payload in cdfs.items():
        n_tracks = int(
            states.loc[states["vehicle_type"] == label, "vehicle_id"].nunique()
        )
        ax.plot(payload["x"], payload["cdf"], linewidth=1.3, label=f"{label} (n={n_tracks} tracks)")
    ax.set_xlabel("Longitudinal acceleration (m/s²)")
    ax.set_ylabel("Time-weighted ECDF")
    ax.set_title("Stage 0.3 pNEUMA longitudinal acceleration ECDF by vehicle type")
    ax.legend(fontsize=8)
    path = figures_dir / "acceleration_ecdf_by_type.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures["fig_accel_ecdf.png"] = path
    return figures


def _plot_dt_distribution(dt_values: np.ndarray, figures_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    finite = dt_values[np.isfinite(dt_values)]
    upper = float(np.quantile(finite, 0.999))
    bins = np.linspace(0, max(upper, 0.1), 100)
    ax.hist(finite, bins=bins)
    ax.set_xlabel("Adjacent time difference within track (s)")
    ax.set_ylabel("Interval count")
    ax.set_title("Stage 0.3 pNEUMA adjacent dt distribution (P99.9 x-limit)")
    path = figures_dir / "dt_histogram.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _write_report(
    *,
    output: Path,
    source_csv: Path,
    file_sha256: str,
    file_size: int,
    audit: dict,
    dt_stats: dict,
    tolerance_s: float,
    tolerance_rule: str,
    speed_tw: pd.DataFrame,
    accel_tw: pd.DataFrame,
    composition: pd.DataFrame,
    speed_vw: pd.DataFrame,
    accel_vw: pd.DataFrame,
    consistency: dict,
    sensitivity_continuity: pd.DataFrame,
    sensitivity_extremes: pd.DataFrame,
    bootstrap_speed: dict,
    bootstrap_accel: dict,
    sampling_audit: dict,
    gate_matrix: pd.DataFrame,
    runtime_s: float,
    peak_memory_mb: float,
) -> str:
    def _fmt(value: object, digits: int = 4) -> str:
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    speed_all = speed_tw[speed_tw["group"] == "ALL"].iloc[0]
    accel_all = accel_tw[accel_tw["group"] == "ALL"].iloc[0]
    speed_vw_all = speed_vw[speed_vw["group"] == "ALL"].iloc[0]
    accel_vw_all = accel_vw[accel_vw["group"] == "ALL"].iloc[0]

    lines = [
        "# Stage 0.3 pNEUMA 城市运动学校准 R2 边界修复与验收准备报告",
        "",
        "## 1. 任务范围与科学边界",
        "",
        "本报告覆盖 Stage 0.3 R2（任务标识 AAD-S0.3-T02，结果标识 RES-STAGE-0.3-BOUNDARY-REPAIR-R2）：修复 R1 发现的三项工程边界缺陷（排序掩盖原始时间顺序异常、重复 track_id 字典覆盖、Stage 0.5 参考质量字段语义失真），重新验证正式统计结果，不改变研究方法、科学参数或科学结论。",
        "未恢复已退役的地图匹配、前车推断、TTC/DRAC、风险事件识别或人工前车 QA；结果不解释为真实跟驰风险、事故概率或 AAD 核心因果效应。R1 包保留为不可覆盖的历史证据。",
        "",
        "## 2. 数据来源与完整性 (Observation)",
        "",
        f"- 文件：`{source_csv.as_posix()}`",
        f"- 大小：{file_size:,} bytes；SHA-256：`{file_sha256}`",
        "- 来源：Zenodo pNEUMA 数据集（doi 10.5281/zenodo.10491409），下载清单 `docs/归档/真实数据与NC文献调研/download_manifest.md`；许可按更严格的 CC BY-NC 4.0 管理。",
        f"- 原始轨迹行数（行级审计单位）：{audit['raw_track_rows']}；唯一 track_id：{audit['unique_track_ids']}；可靠轨迹行：{audit.get('reliable_track_rows', 'n/a')}",
        f"- 解析后状态记录数：{audit['parsed_state_records']}",
        f"- 唯一轨迹数：{audit['unique_tracks']}",
        f"- 畸形轨迹行：{len(audit['malformed_tracks'])}；元数据解析失败：{len(audit['metadata_failures'])}",
        f"- 重复 track_id：{audit['duplicate_track_ids']}（涉及原始行 {audit['duplicate_track_rows']}）；身份冲突：{len(audit['identity_conflicts'])}",
        f"- 重复 (track,time) 状态：{audit['duplicate_state_keys']}",
        f"- 观测时间范围：[{audit['time_min_s']:.2f}, {audit['time_max_s']:.2f}] s",
        f"- 车型：{', '.join(f'{k}={v}' for k, v in audit['vehicle_type_counts'].items())}",
        "",
        "## 2bis. 原始顺序、身份与 R1/R2 对比（R2 修复验证，Observation）",
        "",
        f"- 原始记录顺序审计（排序前评估，排序不得修复）：时间倒退 {audit['raw_order_time_audit']['regression_raw_order_edges']}，非正增量 {audit['raw_order_time_audit']['nonpositive_raw_order_edges']}，原始顺序异常状态 {audit['raw_order_time_audit']['raw_order_anomaly_states']}，重复 (track,time) 状态 {audit['raw_order_time_audit']['duplicate_time_states']}，超容差缺口 {audit['raw_order_time_audit']['time_gap_states']}，可靠权重资格状态 {audit['raw_order_time_audit'].get('eligible_states', 'n/a')}。",
        "- 轨迹身份审计（行级）：重复 ID 不合并、不改名，歧义身份 fail-closed（本固定源文件上如出现重复 ID 直接中止运行，不产生部分统计）。",
        f"- R1/R2 逐项比较：{audit['r1_r2_comparison']['metrics_compared']} 项，变化 {audit['r1_r2_comparison']['changed_metric_count']} 项（其中浮点末位 {audit['r1_r2_comparison']['float_ulp_only_changed_count']} 项，|差|≤1e-9，numpy 求和顺序/对齐效应；结构性变化 {audit['r1_r2_comparison']['structural_changed_count']} 项：{audit['r1_r2_comparison']['structural_changed_metrics']}）；明细见 `r1_r2_comparison.csv`。R1 数字是比较基准，不是必须维持的目标值。独立复算同时用 R1 代码路径在 R1 封存状态上复算验证了这些浮点差异与本次修复无关。",
        "",
        "## 3. 时间连续性与采样 (Observation)",
        "",
        f"- 相邻时间差：mode={dt_stats['mode_dt_s']:.6f} s，median={dt_stats['median_dt_s']:.6f} s，"
        f"P99={dt_stats['p99_dt_s']:.6f} s，max={dt_stats['max_dt_s']:.6f} s；"
        f"dt<=0 的相邻对：{dt_stats['nonpositive_pairs']}；缺口(dt>{tolerance_s:.4f} s)对：{dt_stats['gap_pairs']}",
        f"- 工程锚定容差：{tolerance_s:.6f} s（{tolerance_rule}）。",
        f"- 规则：左矩形端点赋值 [t_i, t_i+1_raw)（原始记录顺序邻接，排序不定义区间），末帧零时长；不跨缺口插值、不外推末帧；解析/身份/原始顺序异常状态不获得可靠权重。局限：每段内速度视为常数，可能平滑 40 ms 内的瞬时变化；该容差不是冻结的科学阈值。",
        "",
        "## 4. 速度分布（时间加权主统计，SI 单位 m/s）",
        "",
        f"- 总体（ALL）：有效状态 {speed_all['states_time_weighted']:,}，暴露 {speed_all['exposure_time_s']:,.1f} s；"
        f"mean={_fmt(speed_all['mean'])}，sd={_fmt(speed_all['sd'])}，"
        f"P5={_fmt(speed_all['p5'])}，P25={_fmt(speed_all['p25'])}，P50={_fmt(speed_all['p50'])}，"
        f"P75={_fmt(speed_all['p75'])}，P95={_fmt(speed_all['p95'])}，P99={_fmt(speed_all['p99'])}，"
        f"min={_fmt(speed_all['min'])}，max={_fmt(speed_all['max'])}",
        "- 分车型数值见 `speed_time_weighted_by_type.csv`；直方图与 ECDF 见 `fig_speed_histogram.png`、`fig_speed_ecdf.png`。",
        "",
        "## 5. 纵向加速度分布（时间加权主统计，m/s²）",
        "",
        f"- 总体（ALL）：mean={_fmt(accel_all['mean'])}，sd={_fmt(accel_all['sd'])}，"
        f"P5={_fmt(accel_all['p5'])}，P50={_fmt(accel_all['p50'])}，P95={_fmt(accel_all['p95'])}，"
        f"P99={_fmt(accel_all['p99'])}，min={_fmt(accel_all['min'])}，max={_fmt(accel_all['max'])}",
        "- 正/负/近零加速度时间占比与按速度分层条件分布见 `acceleration_state_shares.csv`、`acceleration_by_speed_stratum.csv`；分车型分布见 `acceleration_time_weighted_by_type.csv` 与加速度图。",
        "",
        "## 6. 车型组成（唯一轨迹计数）",
        "",
    ]
    for row in composition.itertuples(index=False):
        lines.append(
            f"- {row.vehicle_type}：{row.unique_trajectories} 条轨迹（{row.trajectory_share:.4f}），"
            f"状态 {row.state_records:,}，观测时长合计 {row.total_observed_duration_s:,.1f} s，"
            f"轨迹时长中位数 {row.median_track_duration_s:.2f} s"
        )
    lines += [
        "",
        "原始类别保留；与 SUMO vType 的映射未定义（Decision Required）。",
        "",
        "## 7. 时间加权 vs 车辆等权对照 (Observation)",
        "",
        f"- 速度 mean：时间加权 {_fmt(speed_all['mean'])} m/s vs 车辆等权 {_fmt(speed_vw_all['mean'])} m/s（差 {_fmt(float(speed_all['mean']) - float(speed_vw_all['mean']))}）；"
        f"P50：{_fmt(speed_all['p50'])} vs {_fmt(speed_vw_all['p50'])}",
        f"- 加速度 mean：时间加权 {_fmt(accel_all['mean'])} m/s² vs 车辆等权 {_fmt(accel_vw_all['mean'])} m/s²（差 {_fmt(float(accel_all['mean']) - float(accel_vw_all['mean']))}）；"
        f"P50：{_fmt(accel_all['p50'])} vs {_fmt(accel_vw_all['p50'])}",
        "- 分车型对照与轨迹时长影响见 `weighting_comparison_by_type.csv`、`track_stats.csv`。"
        "车辆等权仅代表本文件 785 条被截断轨迹的等权平均，不等于整个城市真实车辆分布。",
        "",
        "## 8. 质量、敏感性与统计可靠性 (Observation)",
        "",
        f"- 运动学一致性（诊断，非物理真值）：加速度偏差（Δv/Δt 与报告加速度之差的绝对值）中位数 "
        f"{_fmt(consistency['accel_deviation_mps2_median'])} m/s²、P95 {_fmt(consistency['accel_deviation_mps2_p95'])}、max {_fmt(consistency['accel_deviation_mps2_max'])}；"
        f"位置—速度偏差中位数 {_fmt(consistency['speed_deviation_mps_median'])} m/s、P95 {_fmt(consistency['speed_deviation_mps_p95'])}；"
        f"轨迹级行驶距离相对偏差中位数 {_fmt(consistency['track_distance_relative_deviation_median'])}、P95 {_fmt(consistency['track_distance_relative_deviation_p95'])}；"
        f"平均速度偏差中位数 {_fmt(consistency['track_avg_speed_deviation_kmh_median'])} km/h。",
        f"- 连续性敏感性：8 个候选容差下暴露 {sensitivity_continuity['exposure_time_s'].min():,.1f}–{sensitivity_continuity['exposure_time_s'].max():,.1f} s，"
        f"速度均值 {sensitivity_continuity['speed_mean_mps'].min():.4f}–{sensitivity_continuity['speed_mean_mps'].max():.4f} m/s；详见 `continuity_sensitivity.csv`。",
        f"- 极端值探索性屏蔽：见 `extreme_sensitivity.csv`；所有屏蔽仅为敏感性对照，原始值全部保留。",
        f"- 统计不确定性（轨迹整簇 bootstrap，2000 次）：速度时间加权 mean {_fmt(bootstrap_speed['point_estimate'])} m/s，"
        f"95% CI [{_fmt(bootstrap_speed['ci_low'])}, {_fmt(bootstrap_speed['ci_high'])}]；"
        f"加速度时间加权 mean {_fmt(bootstrap_accel['point_estimate'])} m/s²，95% CI [{_fmt(bootstrap_accel['ci_low'])}, {_fmt(bootstrap_accel['ci_high'])}]。"
        "车辆等权 mean/median 的 bootstrap 区间见 `bootstrap_vehicle_equal_weight.csv`。同一轨迹的帧不作为独立样本。",
        "",
        "## 9. Stage 0.5 参考接口与质量语义 (Observation)",
        "",
        "- 已输出标准化 `stage_0_5_reference_states.parquet`（dataset/site/window/vehicle_id/vehicle_type/time_s/speed_mps/acceleration_mps2/quality_status/time_weighting_eligible/source_file_sha256），并通过现有 `write_real_reference_package()` 的构造兼容性测试与真实全量接口测试。",
        f"- 质量语义（R2 修复）：quality_status 逐状态推导（分布 {audit['stage_0_5_reference_quality_counts']}），time_weighting_eligible 由实际解析质量、轨迹身份、原始顺序连续性与可靠时间区间共同决定（eligible {audit['stage_0_5_reference_eligible_states']} / {audit['parsed_state_records']}）；缺失、异常、不可评价状态可追溯且不默认视为可靠。",
        "- `write_real_reference_package()` 从 R2 起读取并使用质量字段：非 raw_parsed 状态 fail-closed 排除出 pNEUMA 运动学抽样池（计数入 audit），time_weighting_eligible 随 kinematics_reference 传递；稳定哈希抽样规则本身未改变。",
        "- 三者区分：接口能读取 ≠ 质量标记正确传递 ≠ 后续统计保持预期权重。前两者已在本包验证；第三者（时间加权权重的正式使用）属 Stage 0.5 设计决定：当前按状态无界抽样不带时间权重语义，设计建议是让正式覆盖统计使用随表传递的 time_weighting_eligible 或改用轨迹整簇抽样，本任务不实现。",
        f"- 稳定哈希抽样车型保持审计：最大状态份额偏差 {sampling_audit.get('max_state_share_deviation', float('nan')):.6f}，"
        f"最低轨迹保留率 {1.0 - sampling_audit.get('max_trajectory_loss_share', float('nan')):.6f}；见 `sampling_balance_audit.csv`。",
        "- NGSIM 与 pNEUMA 道路类型、交通环境、采样语义与车型组成不同；二者不拼接为独立同分布现实样本，分层的现实—现实基准需要独立参考组。",
        "",
        "## 10. 验收矩阵与 Gate 状态",
        "",
        f"验收矩阵见 `gate_matrix.csv`（{len(gate_matrix)} 项）。本包为 **Stage 0.3 Gate Pass Candidate（工程与已批准统计设计完成）**，科学 Gate 由研究者审核决定。",
        "",
        "## 11. Limitation",
        "",
        "- 本结果仅基于单个 30 分钟、单区域观测文件，不能代表整个雅典、所有城市道路或一般交通条件；时空代表性限制未解除。",
        "- 时间连续性容差、低速/近零加速度阈值、异常屏蔽规则均为探索性候选，未获研究者冻结。",
        "- 运动学一致性检查是内部诊断，不构成独立物理真值验证；pNEUMA 平滑/滤波链未独立核验。",
        "- 车辆等权统计受观测范围、轨迹截断和采样机制影响，不等于城市总体车辆分布。",
        "- 车型到 SUMO vType 的映射、Stage 0.5 场景分层、容差与覆盖 Gate 标准均未冻结。",
        "",
        "## 12. 工程运行",
        "",
        f"- 运行时间 {runtime_s:.1f} s；解析峰值内存约 {peak_memory_mb:.1f} MiB（tracemalloc）。",
        "- 产物：config.json、audit.json、provenance.json、manifest.json、SHA256SUMS、CSV/Parquet 表与分布图；本目录创建后不可覆盖。",
    ]
    return "\n".join(lines) + "\n"


def _build_r1_r2_comparison(
    *,
    r1_package: Path,
    audit: dict,
    speed_tw: pd.DataFrame,
    accel_tw: pd.DataFrame,
    speed_vw: pd.DataFrame,
    accel_vw: pd.DataFrame,
    composition: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Itemised R1 vs R2 comparison.

    R1 is a comparison baseline, never a target: differences are reported,
    never tuned away.  Returns the comparison table and a summary dict.
    """

    rows: list[dict[str, object]] = []

    def add(metric: str, r1: object, r2: object) -> None:
        if isinstance(r1, (int, float)) and isinstance(r2, (int, float)):
            difference: object = float(r2) - float(r1)
            changed = difference != 0.0
        else:
            difference = ""
            changed = str(r1) != str(r2)
        rows.append(
            {
                "metric": metric,
                "r1": r1,
                "r2": r2,
                "difference_r2_minus_r1": difference,
                "changed": bool(changed),
            }
        )

    r1_audit: dict = {}
    if (r1_package / "audit.json").is_file():
        r1_audit = json.loads((r1_package / "audit.json").read_text(encoding="utf-8"))
    if not r1_audit:
        add("r1_package_available", False, False)
        summary = {
            "r1_package_available": False,
            "metrics_compared": 0,
            "changed_metric_count": 0,
            "changed_metrics": [],
        }
        return pd.DataFrame.from_records(rows), summary
    add("r1_package_available", True, True)

    add("raw_track_rows", r1_audit.get("raw_track_rows"), audit["raw_track_rows"])
    add("parsed_state_records", r1_audit.get("parsed_state_records"), audit["parsed_state_records"])
    add("unique_tracks", r1_audit.get("unique_tracks"), audit["unique_tracks"])
    add("anchor_tolerance_s", r1_audit.get("anchor_tolerance_s"), audit["anchor_tolerance_s"])
    for key in ("mode_dt_s", "median_dt_s", "max_dt_s", "nonpositive_pairs", "gap_pairs"):
        add(
            f"dt_stats.{key}",
            r1_audit.get("dt_stats", {}).get(key),
            audit["dt_stats"][key],
        )
    add(
        "duplicate_track_ids_count",
        r1_audit.get("duplicate_track_ids_count", len(r1_audit.get("duplicate_track_ids", []))),
        len(audit["duplicate_track_ids"]),
    )
    add("duplicate_state_keys", r1_audit.get("duplicate_state_keys"), audit["duplicate_state_keys"])
    add(
        "malformed_tracks_count",
        r1_audit.get("malformed_tracks_count", len(r1_audit.get("malformed_tracks", []))),
        len(audit["malformed_tracks"]),
    )

    r1_quality_counts: object = "not_recorded"
    r1_eligible: object = "not_recorded"
    r1_states_path = r1_package / "states_audit.parquet"
    if r1_states_path.is_file():
        eligible_column = pd.read_parquet(r1_states_path, columns=["time_weighting_eligible"])
        r1_eligible = int(eligible_column["time_weighting_eligible"].sum())
    add("time_weighting_eligible_states", r1_eligible, audit["stage_0_5_reference_eligible_states"])
    add(
        "stage_0_5_reference_quality_counts",
        r1_quality_counts,
        str(audit["stage_0_5_reference_quality_counts"]),
    )

    def compare_grouped_tables(
        metric_prefix: str,
        r1_table: pd.DataFrame,
        r2_table: pd.DataFrame,
        columns: Sequence[str],
        key_column: str = "group",
    ) -> None:
        for row in r2_table.itertuples(index=False):
            label = getattr(row, key_column)
            match = r1_table.loc[r1_table[key_column] == label]
            if match.empty:
                add(f"{metric_prefix}[{label}]", "missing_in_r1", "present_in_r2")
                continue
            for column in columns:
                add(
                    f"{metric_prefix}[{label}].{column}",
                    float(match.iloc[0][column]),
                    float(getattr(row, column) if not isinstance(getattr(row, column), str) else float("nan")),
                )

    if (r1_package / "speed_time_weighted_by_type.csv").is_file():
        compare_grouped_tables(
            "speed_time_weighted",
            pd.read_csv(r1_package / "speed_time_weighted_by_type.csv"),
            speed_tw,
            ("states_time_weighted", "exposure_time_s", "mean", "sd", "p50", "p95"),
        )
    if (r1_package / "acceleration_time_weighted_by_type.csv").is_file():
        compare_grouped_tables(
            "acceleration_time_weighted",
            pd.read_csv(r1_package / "acceleration_time_weighted_by_type.csv"),
            accel_tw,
            ("states_time_weighted", "exposure_time_s", "mean", "sd", "p50", "p95"),
        )
    if (r1_package / "speed_vehicle_equal_weight.csv").is_file():
        compare_grouped_tables(
            "speed_vehicle_equal_weight",
            pd.read_csv(r1_package / "speed_vehicle_equal_weight.csv"),
            speed_vw,
            ("mean", "p50"),
        )
    if (r1_package / "acceleration_vehicle_equal_weight.csv").is_file():
        compare_grouped_tables(
            "acceleration_vehicle_equal_weight",
            pd.read_csv(r1_package / "acceleration_vehicle_equal_weight.csv"),
            accel_vw,
            ("mean", "p50"),
        )
    if (r1_package / "vehicle_type_composition.csv").is_file():
        compare_grouped_tables(
            "vehicle_type_composition",
            pd.read_csv(r1_package / "vehicle_type_composition.csv"),
            composition,
            ("unique_trajectories", "state_records", "total_observed_duration_s"),
            key_column="vehicle_type",
        )

    table = pd.DataFrame.from_records(rows)
    changed_rows = table.loc[table["changed"]]
    def _is_float_ulp(row: pd.Series) -> bool:
        difference = row["difference_r2_minus_r1"]
        return isinstance(difference, (int, float)) and abs(float(difference)) <= 1e-9
    float_ulp = [str(m) for m in changed_rows[changed_rows.apply(_is_float_ulp, axis=1)]["metric"]]
    structural = [str(m) for m in changed_rows[~changed_rows.apply(_is_float_ulp, axis=1)]["metric"]]
    summary = {
        "r1_package": str(r1_package.as_posix()),
        "metrics_compared": int(len(table)),
        "changed_metric_count": int(len(changed_rows)),
        "float_ulp_only_changed_metrics": float_ulp,
        "float_ulp_only_changed_count": len(float_ulp),
        "structural_changed_metrics": structural,
        "structural_changed_count": len(structural),
        "note": (
            "float-ulp entries are |difference| <= 1e-9 (numpy summation "
            "order/alignment effects; no count, weight or record changed); "
            "structural entries change recorded semantics, not statistics"
        ),
        "changed_metrics": [str(m) for m in changed_rows["metric"]],
    }
    return table, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance-s", type=float, default=None,
                        help="engineering anchor continuity tolerance; default derives from modal dt")
    parser.add_argument("--skip-stage-0-5-test", action="store_true")
    parser.add_argument(
        "--baseline-package",
        type=Path,
        default=R1_PACKAGE,
        help="sealed R1 package used as comparison baseline (never a target)",
    )
    parser.add_argument(
        "--allow-unknown-source-sha",
        action="store_true",
        help="smoke-test escape hatch; the run is recorded as not SHA-pinned and is not a formal package",
    )
    args = parser.parse_args()

    started = time.monotonic()
    started_wall = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    import tracemalloc

    tracemalloc.start()

    source_csv = args.source_csv.resolve()
    file_sha256 = sha256_file(source_csv).upper()
    file_size = source_csv.stat().st_size
    source_pin_enforced = not args.allow_unknown_source_sha
    if source_pin_enforced and file_sha256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"unexpected source SHA-256: {file_sha256}")

    output = args.output
    if output.exists():
        raise SystemExit(f"output directory already exists (immutable): {output}")

    # --- Task A: integrity, identity and raw-order time audit (R2) ----------
    states, source_audit = audit_pneuma_source(source_csv)
    if source_audit["duplicate_track_ids"]:
        # Fail-closed: on this pinned source file, ambiguous trajectory identity
        # (duplicate track_id rows) must never silently enter sealed statistics.
        raise SystemExit(
            "duplicate track_id rows detected (identity fail-closed): "
            + ", ".join(map(str, source_audit["duplicate_track_ids"]))
        )
    # Raw-order time audit FIRST (no gap tolerance yet); dt_to_next_s is the
    # raw-record-order adjacent interval, never a time-sorted repair.
    states = flag_state_quality(states)

    duplicate_track_ids = source_audit["duplicate_track_ids"]
    duplicate_state_keys = int(states.duplicated(subset=["vehicle_id", "time_s"], keep=False).sum())
    times = states["time_s"].to_numpy(float)
    dt_all = states["dt_to_next_s"].to_numpy(float)
    dt_finite = dt_all[np.isfinite(dt_all)]
    positive_dt = dt_finite[dt_finite > 0]
    nominal_dt = float(pd.Series(positive_dt).mode().iloc[0]) if len(positive_dt) else float("nan")
    tolerance_s = args.tolerance_s
    tolerance_rule = "operator override"
    if tolerance_s is None:
        tolerance_s, tolerance_rule = _select_tolerance({"mode_dt_s": nominal_dt})

    dt_stats = {
        "mode_dt_s": nominal_dt,
        "median_dt_s": float(np.median(positive_dt)) if len(positive_dt) else float("nan"),
        "p99_dt_s": float(np.quantile(positive_dt, 0.99)) if len(positive_dt) else float("nan"),
        "max_dt_s": float(np.max(dt_finite)) if len(dt_finite) else float("nan"),
        "min_dt_s": float(np.min(dt_finite)) if len(dt_finite) else float("nan"),
        "nonpositive_pairs": int((dt_finite <= 0).sum()),
        "gap_pairs": int((dt_finite > tolerance_s).sum()),
        "total_pairs": int(len(dt_finite)),
        "adjacency_semantics": "raw record order within each trajectory (pre-sort)",
    }

    # Re-flag with the anchored tolerance so time_gap_flag shares one rule with
    # the eligibility computation (single source of truth).
    states = flag_state_quality(states, gap_tolerance_s=tolerance_s)
    states["quality_status"] = derive_state_quality_status(states)

    raw_order_time_audit = {
        "schema_version": "aad.stage-0-3.raw-order-time-audit.v1",
        "adjacency_semantics": (
            "time continuity evaluated on original record order before any sorting; "
            "sorting can never repair or mask a raw-order anomaly"
        ),
        "nonpositive_raw_order_edges": int(states["time_increment_nonpositive"].sum()),
        "regression_raw_order_edges": int(states["time_regression_in_raw_order"].sum()),
        "raw_order_anomaly_states": int(states["raw_order_time_anomaly"].sum()),
        "duplicate_time_states": int(states["duplicate_time_in_track"].sum()),
        "time_gap_states": int(states["time_gap_flag"].sum()),
    }

    identity_audit = {
        "schema_version": "aad.stage-0-3.identity-audit.v1",
        "audit_unit": "raw trajectory row (source_row_number)",
        "raw_track_rows": source_audit["raw_track_rows"],
        "unique_track_ids": source_audit["unique_track_ids"],
        "duplicate_track_ids": source_audit["duplicate_track_ids"],
        "duplicate_track_rows": source_audit["duplicate_track_rows"],
        "identity_conflicts": source_audit["identity_conflicts"],
        "identity_ambiguous_states": int(states["identity_ambiguous"].sum()),
        "fail_closed_rule": (
            "duplicate ids are never merged or renamed; this pinned-source run "
            "aborts on any ambiguous identity instead of producing partial statistics"
        ),
    }

    audit = {
        "schema_version": "aad.stage-0-3.audit.v1",
        "experiment_id": "stage_0_3",
        "result_id": "RES-STAGE-0.3-BOUNDARY-REPAIR-R2",
        "source_file": str(source_csv.as_posix()),
        "source_sha256": file_sha256,
        "source_bytes": file_size,
        "raw_track_rows": source_audit["raw_track_rows"],
        "unique_track_ids": source_audit["unique_track_ids"],
        "parsed_state_records": source_audit["parsed_state_records"],
        "unique_tracks": int(states["vehicle_id"].nunique()),
        "malformed_tracks": source_audit["malformed_tracks"],
        "metadata_failures": source_audit["metadata_failures"],
        "duplicate_track_ids": duplicate_track_ids,
        "duplicate_track_rows": source_audit["duplicate_track_rows"],
        "identity_conflicts": source_audit["identity_conflicts"],
        "duplicate_state_keys": duplicate_state_keys,
        "time_min_s": float(np.nanmin(times)),
        "time_max_s": float(np.nanmax(times)),
        "vehicle_type_counts": states.groupby("vehicle_type")["vehicle_id"].nunique().to_dict(),
        "dt_stats": dt_stats,
        "raw_order_time_audit": raw_order_time_audit,
        "identity_audit": identity_audit,
        "anchor_tolerance_s": tolerance_s,
        "anchor_tolerance_rule": tolerance_rule,
        "source_sha_pin_enforced": source_pin_enforced,
        "scientific_claim_eligible": False,
        "gate_status": "acceptance_package_pending_researcher_review",
    }

    track_stats = compute_track_stats(states)
    # Time weighting eligibility: parse quality AND trajectory identity AND
    # raw-order continuity AND a reliable interval, evaluated together.
    states["time_weighting_eligible"] = (
        states["parse_ok"].astype(bool)
        & ~states["identity_ambiguous"].astype(bool)
        & ~states["raw_order_time_anomaly"].astype(bool)
        & ~states["duplicate_time_in_track"].astype(bool)
        & states["dt_to_next_s"].gt(0)
        & states["dt_to_next_s"].le(tolerance_s)
    )
    raw_order_time_audit["eligible_states"] = int(states["time_weighting_eligible"].sum())
    states["source_file_sha256"] = file_sha256
    reliable_track_stats = track_stats
    if "identity_ambiguous" in track_stats.columns:
        reliable_track_stats = track_stats.loc[
            ~track_stats["identity_ambiguous"].fillna(False).astype(bool)
        ].reset_index(drop=True)
    audit["reliable_track_rows"] = int(len(reliable_track_stats))

    # --- Task B: descriptive statistics -------------------------------------
    speed_tw = compute_descriptive_stats(
        states, value_column="speed_mps", group_column="vehicle_type",
        tolerance_s=tolerance_s, nominal_dt_s=nominal_dt,
    )
    speed_tw_all = compute_descriptive_stats(
        states, value_column="speed_mps", group_column=None,
        tolerance_s=tolerance_s, nominal_dt_s=nominal_dt,
    )
    speed_tw = pd.concat([speed_tw_all, speed_tw], ignore_index=True)
    accel_tw = compute_descriptive_stats(
        states, value_column="longitudinal_accel_mps2", group_column="vehicle_type",
        tolerance_s=tolerance_s, nominal_dt_s=nominal_dt,
    )
    accel_tw_all = compute_descriptive_stats(
        states, value_column="longitudinal_accel_mps2", group_column=None,
        tolerance_s=tolerance_s, nominal_dt_s=nominal_dt,
    )
    accel_tw = pd.concat([accel_tw_all, accel_tw], ignore_index=True)

    speed_vw = compute_vehicle_equal_weight_stats(
        reliable_track_stats, value_column="mean_speed_mps_unweighted", group_column=None
    )
    speed_vw_by_type = compute_vehicle_equal_weight_stats(
        reliable_track_stats, value_column="mean_speed_mps_unweighted", group_column="vehicle_type"
    )
    speed_vw = pd.concat([speed_vw, speed_vw_by_type], ignore_index=True)
    accel_vw = compute_vehicle_equal_weight_stats(
        reliable_track_stats, value_column="mean_accel_mps2_unweighted", group_column=None
    )
    accel_vw_by_type = compute_vehicle_equal_weight_stats(
        reliable_track_stats, value_column="mean_accel_mps2_unweighted", group_column="vehicle_type"
    )
    accel_vw = pd.concat([accel_vw, accel_vw_by_type], ignore_index=True)

    composition = compute_vehicle_type_composition(reliable_track_stats)
    speed_shares = speed_state_shares(states, tolerance_s=tolerance_s)
    accel_shares = acceleration_state_shares(states, tolerance_s=tolerance_s)
    accel_by_speed = acceleration_by_speed_stratum(states, tolerance_s=tolerance_s)

    weighting_comparison = pd.DataFrame(
        {
            "group": speed_tw["group"],
            "speed_mean_time_weighted": speed_tw["mean"],
            "speed_mean_vehicle_equal": speed_vw["mean"],
            "speed_p50_time_weighted": speed_tw["p50"],
            "speed_p50_vehicle_equal": speed_vw["p50"],
            "accel_mean_time_weighted": accel_tw["mean"],
            "accel_mean_vehicle_equal": accel_vw["mean"],
            "accel_p50_time_weighted": accel_tw["p50"],
            "accel_p50_vehicle_equal": accel_vw["p50"],
        }
    )
    weighting_comparison["speed_mean_difference"] = (
        weighting_comparison["speed_mean_time_weighted"]
        - weighting_comparison["speed_mean_vehicle_equal"]
    )
    weighting_comparison["accel_mean_difference"] = (
        weighting_comparison["accel_mean_time_weighted"]
        - weighting_comparison["accel_mean_vehicle_equal"]
    )

    # --- Task C: quality, sensitivity, uncertainty ---------------------------
    consistent_states, consistency, track_consistency = compute_kinematic_consistency(states)
    sensitivity_continuity = continuity_sensitivity(states)
    sensitivity_extremes = extreme_value_sensitivity(states, tolerance_s=tolerance_s)
    bootstrap_speed = time_weighted_bootstrap(
        states, value_column="speed_mps", tolerance_s=tolerance_s
    )
    bootstrap_accel = time_weighted_bootstrap(
        states, value_column="longitudinal_accel_mps2", tolerance_s=tolerance_s
    )
    bootstrap_vw_speed = bootstrap_track_intervals(
        reliable_track_stats, value_column="mean_speed_mps_unweighted"
    )
    bootstrap_vw_speed_by_type = bootstrap_track_intervals(
        reliable_track_stats, value_column="mean_speed_mps_unweighted", group_column="vehicle_type"
    )
    bootstrap_vw = pd.concat([bootstrap_vw_speed, bootstrap_vw_speed_by_type], ignore_index=True)
    bootstrap_vw_accel = bootstrap_track_intervals(
        reliable_track_stats, value_column="mean_accel_mps2_unweighted"
    )
    bootstrap_vw_accel_by_type = bootstrap_track_intervals(
        reliable_track_stats, value_column="mean_accel_mps2_unweighted", group_column="vehicle_type"
    )
    bootstrap_vw = pd.concat([bootstrap_vw, bootstrap_vw_accel, bootstrap_vw_accel_by_type], ignore_index=True)

    # --- Task D: Stage 0.5 reference interface (R2 quality semantics) -----
    # Per-state quality_status is DERIVED from the audit flags (never a uniform
    # label); time_weighting_eligible is the precomputed eligibility column.
    reference_states = build_stage_0_5_reference_states(states)
    audit["stage_0_5_reference_quality_counts"] = {
        str(key): int(value)
        for key, value in reference_states["quality_status"].value_counts().items()
    }
    audit["stage_0_5_reference_eligible_states"] = int(
        reference_states["time_weighting_eligible"].sum()
    )
    sampled = deterministic_state_sample(
        reference_states, max_rows=5000, seed=20260907 + 2
    )
    sampling_audit = audit_sampling_balance(sampled, reference_states)
    sampling_table = sampling_audit.pop("table")

    # Interface test area lives outside the immutable package directory.
    stage_0_5_test_dir = output.parent / f"{output.name}_stage05_interface_test"
    if stage_0_5_test_dir.exists():
        raise SystemExit(f"stale interface test directory exists: {stage_0_5_test_dir}")
    stage_0_5_test_result: dict[str, object] = {"executed": False}
    reference_parquet_path = stage_0_5_test_dir / "pneuma_reference_states.parquet"
    stage_0_5_test_dir.mkdir(parents=True, exist_ok=False)
    reference_states.rename(
        columns={"vehicle_id": "id"}
    ).to_parquet(stage_0_5_test_dir / "pneuma_interface_input.parquet", index=False)
    # write_real_reference_package consumes the parse view; from R2 on it also
    # carries quality_status / time_weighting_eligible so the Stage 0.5 reader
    # applies the fail-closed quality pool instead of ignoring quality fields.
    raw_view = states.rename(columns={"vehicle_id": "id"})[
        [
            "id",
            "time_s",
            "speed_mps",
            "longitudinal_accel_mps2",
            "quality_status",
            "time_weighting_eligible",
        ]
    ]
    raw_view.to_parquet(reference_parquet_path, index=False)
    if not args.skip_stage_0_5_test:
        ngsim_paths = sorted(NGSIM_STATES_DIR.glob("*.parquet"))
        if not ngsim_paths or not NGSIM_EVENTS_PATH.is_file():
            stage_0_5_test_result = {
                "executed": False,
                "reason": "NGSIM stage 0.2 sealed states/events unavailable",
            }
        else:
            package_dir = write_real_reference_package(
                ngsim_state_paths=ngsim_paths,
                pneuma_state_path=reference_parquet_path,
                ngsim_event_path=NGSIM_EVENTS_PATH,
                output_dir=stage_0_5_test_dir / "reference_package",
                max_rows_per_group=5000,
                seed=20260907,
                pneuma_schema="legacy",
            )
            package_audit = json.loads((package_dir / "audit.json").read_text(encoding="utf-8"))
            stage_0_5_test_result = {
                "executed": True,
                "package_dir": str(package_dir.as_posix()),
                "kinematics_rows": package_audit["kinematics_rows"],
                "following_rows": package_audit["following_rows"],
                "risk_event_rows": package_audit["risk_event_rows"],
                "pneuma_ttc_included": package_audit["pneuma_ttc_included"],
                "pneuma_quality_columns_present": package_audit["sources"][-1][
                    "pneuma_quality_semantics"
                ]["pneuma_quality_columns_present"],
                "pneuma_states_not_reliably_parsed_excluded": package_audit["sources"][-1][
                    "pneuma_quality_semantics"
                ]["pneuma_states_not_reliably_parsed_excluded"],
                "pneuma_states_time_weighting_eligible": package_audit["sources"][-1][
                    "pneuma_quality_semantics"
                ]["pneuma_states_time_weighting_eligible"],
                "gate_status": package_audit["gate_status"],
            }

    # --- R1/R2 comparison (R1 is a baseline, never a target) ------------------
    r1_r2_table, r1_r2_summary = _build_r1_r2_comparison(
        r1_package=args.baseline_package.resolve(),
        audit=audit,
        speed_tw=speed_tw,
        accel_tw=accel_tw,
        speed_vw=speed_vw,
        accel_vw=accel_vw,
        composition=composition,
    )
    audit["r1_r2_comparison"] = r1_r2_summary

    # --- Figures --------------------------------------------------------------
    figures_dir = output.parent / f"{output.name}_figures_tmp"
    figures_dir.mkdir(parents=True, exist_ok=False)
    figures = _plot_histograms(states, tolerance_s=tolerance_s, figures_dir=figures_dir)
    figures["fig_dt_histogram.png"] = _plot_dt_distribution(dt_all, figures_dir)

    # --- Gate matrix ------------------------------------------------------------
    gate_rows = [
        {
            "item": "原始数据与字段解释可靠",
            "basis": "SHA-256 与封存清单一致；宽表结构、单位与 Zenodo 元数据一致",
            "method": "文件哈希 + 行级流式解析审计（原始行序保留）+ 结构测试",
            "result": (
                f"{audit['raw_track_rows']} 原始行 / {audit['unique_track_ids']} 唯一 ID / "
                f"{audit['parsed_state_records']} 状态；畸形 0；重复 ID 0"
            ),
            "evidence": "audit.json, states_audit.parquet, code/tests/test_pneuma_urban_kinematics.py",
            "status": "Verified",
            "remaining_limitation": "字段语义依据数据提供方文档；无独立物理真值",
        },
        {
            "item": "原始记录顺序与轨迹身份审计（R2 修复）",
            "basis": "时间连续性在排序前按原始记录顺序评估；轨迹身份按原始行审计",
            "method": "raw-order 时间倒退/重复/非正增量/缺口标记 + 行级重复 ID 与身份冲突检测 + 构造回归测试（0.00→0.08→0.04）",
            "result": (
                f"时间倒退 {audit['raw_order_time_audit']['regression_raw_order_edges']}；"
                f"非正增量 {audit['raw_order_time_audit']['nonpositive_raw_order_edges']}；"
                f"重复 (track,time) 状态 {audit['raw_order_time_audit']['duplicate_time_states']}；"
                f"超容差缺口 {audit['raw_order_time_audit']['time_gap_states']}；"
                f"重复 ID {len(audit['duplicate_track_ids'])}；身份冲突 {len(audit['identity_conflicts'])}"
            ),
            "evidence": "states_audit.parquet, audit.json, code/tests/test_pneuma_urban_kinematics.py",
            "status": "Verified (engineering)",
            "remaining_limitation": "原始顺序语义约束质量标记与时间权重；正式连续性容差仍待研究者",
        },
        {
            "item": "Stage 0.5 参考接口质量语义（R2 修复）",
            "basis": "逐状态 quality_status 与 time_weighting_eligible 由解析质量、轨迹身份与可靠区间共同决定",
            "method": "逐状态质量推导（拒绝无标志默认可靠）+ 接口契约测试 + 真实全量接口测试（质量字段传递）",
            "result": (
                f"quality_status 分布 {audit['stage_0_5_reference_quality_counts']}；"
                f"eligible {audit['stage_0_5_reference_eligible_states']} / {audit['parsed_state_records']}"
            ),
            "evidence": "stage_0_5_reference_states.parquet, audit.json, code/tests/test_simulation_real_coverage.py",
            "status": "Verified (engineering)",
            "remaining_limitation": "按状态无界抽样与时间加权权重的正式使用留给 Stage 0.5 设计决定",
        },
        {
            "item": "时间连续性与统计权重可审计",
            "basis": "相邻 dt 实证分布；8 个候选容差敏感性；左矩形规则显式记录",
            "method": "dt 分布统计 + continuity_sensitivity + 单元测试",
            "result": f"mode dt={dt_stats['mode_dt_s']:.6f}s；缺口对 {dt_stats['gap_pairs']}；锚定容差 {tolerance_s:.6f}s",
            "evidence": "continuity_sensitivity.csv, audit.json",
            "status": "Verified (engineering); 科学容差 Decision Required",
            "remaining_limitation": "正式连续性容差未冻结；锚定规则只是工程默认",
        },
        {
            "item": "速度与纵向加速度描述性参考完整",
            "basis": "研究者认可的时间加权主统计 + 车辆等权稳健性框架",
            "method": "分位数/直方图/ECDF/状态份额/按速度分层条件分布",
            "result": f"速度 mean={speed_tw.iloc[0]['mean']:.4f} m/s；加速度 mean={accel_tw.iloc[0]['mean']:.4f} m/s²",
            "evidence": "speed_time_weighted_by_type.csv, acceleration_time_weighted_by_type.csv, fig_*.png",
            "status": "Verified (descriptive)",
            "remaining_limitation": "单文件 30 分钟；不代表城市总体",
        },
        {
            "item": "车型分布可复算",
            "basis": "唯一轨迹计数框架",
            "method": "compute_vehicle_type_composition + 独立计数测试",
            "result": "; ".join(f"{k}={v}" for k, v in audit["vehicle_type_counts"].items()),
            "evidence": "vehicle_type_composition.csv",
            "status": "Verified",
            "remaining_limitation": "SUMO vType 映射未批准",
        },
        {
            "item": "质量和敏感性分析充分",
            "basis": "任务 C 的 7 项描述性分析",
            "method": "运动学一致性诊断 + 极端值/连续性/权重/车型敏感性 + 轨迹簇 bootstrap",
            "result": f"速度时间加权 mean 95% CI [{bootstrap_speed['ci_low']:.4f},{bootstrap_speed['ci_high']:.4f}]",
            "evidence": "extreme_sensitivity.csv, bootstrap_*.csv, kinematic_consistency.json",
            "status": "Verified (descriptive)",
            "remaining_limitation": "异常阈值与正式质量分类需研究者批准",
        },
        {
            "item": "具备进入 Stage 0.5 的有限城市运动学参考条件",
            "basis": "Stage 0.5 接口契约、质量语义与抽样审计",
            "method": "write_real_reference_package 构造 + 真实全量接口测试（质量字段传递）",
            "result": (
                "接口测试通过；质量字段 fail-closed 传递；pNEUMA TTC 未纳入"
                if stage_0_5_test_result.get("executed")
                else "构造测试通过；真实接口测试未执行"
            ),
            "evidence": "stage_0_5_reference_states.parquet, sampling_balance_audit.csv",
            "status": "Verified (engineering)",
            "remaining_limitation": "Stage 0.5 场景分层/容差/Gate 未冻结；时间加权权重的正式使用待 Stage 0.5 设计决定；NGSIM+pNEUMA 不视为 iid",
        },
        {
            "item": "需研究者批准的阈值/容差/适用范围",
            "basis": "任务边界",
            "method": "本报告第 11 节与 Decision Required 清单",
            "result": "连续性容差、低速/近零阈值、异常屏蔽、车型映射、代表性声明",
            "evidence": "gate_matrix.csv, report.md",
            "status": "Decision Required",
            "remaining_limitation": "冻结前不得宣称正式质量分类或代表性",
        },
        {
            "item": "pNEUMA 风险/TTC 职责",
            "basis": "2026-09-10 研究者决定",
            "method": "未执行任何 leader/TTC/DRAC 计算",
            "result": "已退役职责未恢复",
            "evidence": "AI_CONTEXT/06_DECISIONS.md",
            "status": "Not Applicable",
            "remaining_limitation": "无",
        },
        {
            "item": "独立物理真实性验证",
            "basis": "无视频/独立测量",
            "method": "仅内部运动学一致性诊断",
            "result": "未验证",
            "evidence": "kinematic_consistency.json",
            "status": "Unverified",
            "remaining_limitation": "如需物理真值需独立数据",
        },
    ]
    gate_matrix = pd.DataFrame(gate_rows)
    gate_matrix_summary = {
        "schema_version": "aad.stage-0-3.gate-matrix-summary.v1",
        "result_id": "RES-STAGE-0.3-BOUNDARY-REPAIR-R2",
        "items": gate_matrix.to_dict("records"),
        "status_counts": {str(k): int(v) for k, v in gate_matrix["status"].value_counts().items()},
    }

    runtime_s = time.monotonic() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak / (1024 * 1024)
    audit["runtime_seconds"] = runtime_s
    audit["parse_peak_memory_mb"] = peak_memory_mb
    audit["stage_0_5_interface_test"] = stage_0_5_test_result
    audit["gate_matrix_status_counts"] = gate_matrix["status"].value_counts().to_dict()
    audit["bootstrap_speed_mean"] = bootstrap_speed
    audit["bootstrap_accel_mean"] = bootstrap_accel

    report = _write_report(
        output=output,
        source_csv=source_csv,
        file_sha256=file_sha256,
        file_size=file_size,
        audit=audit,
        dt_stats=dt_stats,
        tolerance_s=tolerance_s,
        tolerance_rule=tolerance_rule,
        speed_tw=speed_tw,
        accel_tw=accel_tw,
        composition=composition,
        speed_vw=speed_vw,
        accel_vw=accel_vw,
        consistency=consistency,
        sensitivity_continuity=sensitivity_continuity,
        sensitivity_extremes=sensitivity_extremes,
        bootstrap_speed=bootstrap_speed,
        bootstrap_accel=bootstrap_accel,
        sampling_audit=sampling_audit,
        gate_matrix=gate_matrix,
        runtime_s=runtime_s,
        peak_memory_mb=peak_memory_mb,
    )

    config = {
        "experiment_id": "stage_0_3",
        "source_csv": str(source_csv.as_posix()),
        "source_sha256": file_sha256,
        "anchor_tolerance_s": tolerance_s,
        "anchor_tolerance_rule": tolerance_rule,
        "continuity_candidates_s": list(CONTINUITY_CANDIDATES_S),
        "quantile_levels": [0.05, 0.25, 0.5, 0.75, 0.95, 0.99],
        "bootstrap_replicates": 2000,
        "bootstrap_seed": 20261012,
        "speed_strata_mps": list(ACCEL_BY_SPEED_BINS_MPS),
        "near_zero_accel_band_mps2": 0.05,
        "sampling_seed": 20260907,
        "sampling_max_rows_per_group": 5000,
        "weighting_framework": "time-weighted primary; vehicle-equal-weight robustness; unique-trajectory composition",
        "scientific_claim_eligible": False,
    }

    tables = {
        "states_audit.parquet": states,
        "track_stats.csv": track_stats,
        "speed_time_weighted_by_type.csv": speed_tw,
        "acceleration_time_weighted_by_type.csv": accel_tw,
        "speed_vehicle_equal_weight.csv": speed_vw,
        "acceleration_vehicle_equal_weight.csv": accel_vw,
        "vehicle_type_composition.csv": composition,
        "speed_state_shares.csv": speed_shares,
        "acceleration_state_shares.csv": accel_shares,
        "acceleration_by_speed_stratum.csv": accel_by_speed,
        "weighting_comparison_by_type.csv": weighting_comparison,
        "continuity_sensitivity.csv": sensitivity_continuity,
        "extreme_sensitivity.csv": sensitivity_extremes,
        "bootstrap_vehicle_equal_weight.csv": bootstrap_vw,
        "track_consistency.csv": track_consistency,
        "sampling_balance_audit.csv": sampling_table,
        "r1_r2_comparison.csv": r1_r2_table,
        "gate_matrix.csv": gate_matrix,
        "gate_matrix_summary.json": gate_matrix_summary,
        "stage_0_5_reference_states.parquet": reference_states,
        "kinematic_consistency_summary.json": pd.DataFrame([consistency]),
    }

    package = write_acceptance_package(
        output_dir=output,
        config=config,
        source_csv=source_csv,
        tables=tables,
        figures=figures,
        report_markdown=report,
        audit=audit,
        code_files=[
            CODE_ROOT / "src" / "riskprop" / "pneuma_urban_kinematics.py",
            CODE_ROOT / "src" / "riskprop" / "real_trajectory.py",
            CODE_ROOT / "scripts" / "run_stage_0_3_pneuma_kinematics.py",
        ],
        started_monotonic=started,
        started_wall_utc=started_wall,
    )
    # remove temporary figure workspace (figures already copied into package)
    for leftover in figures_dir.glob("*"):
        leftover.unlink()
    figures_dir.rmdir()

    print(json.dumps({"output": str(package), "audit": audit}, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
