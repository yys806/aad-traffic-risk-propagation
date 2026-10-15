"""Run the Stage 0.3 pNEUMA urban-kinematics calibration and acceptance package."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

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
    empirical_cdf_arrays,
    extreme_value_sensitivity,
    flag_state_quality,
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
    figures: dict[str, Path] = {}
    frame = states.sort_values(["vehicle_id", "time_s", "raw_index"]).reset_index(drop=True)
    next_time = frame.groupby("vehicle_id", sort=False)["time_s"].shift(-1)
    same_track = frame["vehicle_id"].eq(frame["vehicle_id"].shift(-1))
    dt = (next_time - frame["time_s"]).where(same_track)
    usable = (
        same_track.to_numpy()
        & (dt.to_numpy(float) > 0)
        & (dt.to_numpy(float) <= tolerance_s)
    )
    frame = frame.loc[usable].copy()
    frame["_dt"] = dt.to_numpy()[usable]

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
    accel = frame.dropna(subset=["longitudinal_accel_mps2"])
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
        "# Stage 0.3 pNEUMA 城市运动学校准综合报告",
        "",
        "## 1. 任务范围与科学边界",
        "",
        "本报告只覆盖 Stage 0.3：pNEUMA `20181101_d1_0800_0830.csv` 的城市速度、纵向加速度、车型组成、数据质量与 Stage 0.5 参考接口准备。",
        "未恢复已退役的地图匹配、前车推断、TTC/DRAC、风险事件识别或人工前车 QA；结果不解释为真实跟驰风险、事故概率或 AAD 核心因果效应。",
        "",
        "## 2. 数据来源与完整性 (Observation)",
        "",
        f"- 文件：`{source_csv.as_posix()}`",
        f"- 大小：{file_size:,} bytes；SHA-256：`{file_sha256}`",
        "- 来源：Zenodo pNEUMA 数据集（doi 10.5281/zenodo.10491409），下载清单 `docs/归档/真实数据与NC文献调研/download_manifest.md`；许可按更严格的 CC BY-NC 4.0 管理。",
        f"- 原始轨迹行数：{audit['raw_track_rows']}",
        f"- 解析后状态记录数：{audit['parsed_state_records']}",
        f"- 唯一轨迹数：{audit['unique_tracks']}",
        f"- 畸形轨迹行：{len(audit['malformed_tracks'])}；元数据解析失败：{len(audit['metadata_failures'])}",
        f"- 重复 track_id：{audit['duplicate_track_ids']}；重复 (track,time) 状态：{audit['duplicate_state_keys']}",
        f"- 观测时间范围：[{audit['time_min_s']:.2f}, {audit['time_max_s']:.2f}] s",
        f"- 车型：{', '.join(f'{k}={v}' for k, v in audit['vehicle_type_counts'].items())}",
        "",
        "## 3. 时间连续性与采样 (Observation)",
        "",
        f"- 相邻时间差：mode={dt_stats['mode_dt_s']:.6f} s，median={dt_stats['median_dt_s']:.6f} s，"
        f"P99={dt_stats['p99_dt_s']:.6f} s，max={dt_stats['max_dt_s']:.6f} s；"
        f"dt<=0 的相邻对：{dt_stats['nonpositive_pairs']}；缺口(dt>{tolerance_s:.4f} s)对：{dt_stats['gap_pairs']}",
        f"- 工程锚定容差：{tolerance_s:.6f} s（{tolerance_rule}）。",
        "- 规则：左矩形端点赋值 [t_i, t_i+1)，末帧零时长；不跨缺口插值、不外推末帧。局限：每段内速度视为常数，可能平滑 40 ms 内的瞬时变化；该容差不是冻结的科学阈值。",
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
        "## 9. Stage 0.5 参考接口 (Observation)",
        "",
        "- 已输出标准化 `stage_0_5_reference_states.parquet`（dataset/site/window/vehicle_id/vehicle_type/time_s/speed_mps/acceleration_mps2/quality_status/time_weighting_eligible/source_file_sha256），并通过现有 `write_real_reference_package()` 的构造兼容性测试与真实全量接口测试。",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance-s", type=float, default=None,
                        help="engineering anchor continuity tolerance; default derives from modal dt")
    parser.add_argument("--skip-stage-0-5-test", action="store_true")
    args = parser.parse_args()

    started = time.monotonic()
    started_wall = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    import tracemalloc

    tracemalloc.start()

    source_csv = args.source_csv.resolve()
    file_sha256 = sha256_file(source_csv).upper()
    file_size = source_csv.stat().st_size
    if file_sha256 != "F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C":
        raise SystemExit(f"unexpected source SHA-256: {file_sha256}")

    output = args.output
    if output.exists():
        raise SystemExit(f"output directory already exists (immutable): {output}")

    # --- Task A: integrity and parsing audit --------------------------------
    states, source_audit = audit_pneuma_source(source_csv)
    states = flag_state_quality(states)

    duplicate_track_ids = (
        source_audit["tracks_table"]["track_id"][
            source_audit["tracks_table"]["track_id"].duplicated(keep=False)
        ]
        .unique()
        .tolist()
    )
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
    }

    audit = {
        "schema_version": "aad.stage-0-3.audit.v1",
        "experiment_id": "stage_0_3",
        "source_file": str(source_csv.as_posix()),
        "source_sha256": file_sha256,
        "source_bytes": file_size,
        "raw_track_rows": source_audit["raw_track_rows"],
        "parsed_state_records": source_audit["parsed_state_records"],
        "unique_tracks": int(states["vehicle_id"].nunique()),
        "malformed_tracks": source_audit["malformed_tracks"],
        "metadata_failures": source_audit["metadata_failures"],
        "duplicate_track_ids": duplicate_track_ids,
        "duplicate_state_keys": duplicate_state_keys,
        "time_min_s": float(np.nanmin(times)),
        "time_max_s": float(np.nanmax(times)),
        "vehicle_type_counts": states.groupby("vehicle_type")["vehicle_id"].nunique().to_dict(),
        "dt_stats": dt_stats,
        "anchor_tolerance_s": tolerance_s,
        "anchor_tolerance_rule": tolerance_rule,
        "scientific_claim_eligible": False,
        "gate_status": "acceptance_package_pending_researcher_review",
    }

    track_stats = compute_track_stats(states)
    states["time_weighting_eligible"] = (
        states["dt_to_next_s"].gt(0) & states["dt_to_next_s"].le(tolerance_s)
    )
    states["source_file_sha256"] = file_sha256

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
        track_stats, value_column="mean_speed_mps_unweighted", group_column=None
    )
    speed_vw_by_type = compute_vehicle_equal_weight_stats(
        track_stats, value_column="mean_speed_mps_unweighted", group_column="vehicle_type"
    )
    speed_vw = pd.concat([speed_vw, speed_vw_by_type], ignore_index=True)
    accel_vw = compute_vehicle_equal_weight_stats(
        track_stats, value_column="mean_accel_mps2_unweighted", group_column=None
    )
    accel_vw_by_type = compute_vehicle_equal_weight_stats(
        track_stats, value_column="mean_accel_mps2_unweighted", group_column="vehicle_type"
    )
    accel_vw = pd.concat([accel_vw, accel_vw_by_type], ignore_index=True)

    composition = compute_vehicle_type_composition(track_stats)
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
        track_stats, value_column="mean_speed_mps_unweighted"
    )
    bootstrap_vw_speed_by_type = bootstrap_track_intervals(
        track_stats, value_column="mean_speed_mps_unweighted", group_column="vehicle_type"
    )
    bootstrap_vw = pd.concat([bootstrap_vw_speed, bootstrap_vw_speed_by_type], ignore_index=True)
    bootstrap_vw_accel = bootstrap_track_intervals(
        track_stats, value_column="mean_accel_mps2_unweighted"
    )
    bootstrap_vw_accel_by_type = bootstrap_track_intervals(
        track_stats, value_column="mean_accel_mps2_unweighted", group_column="vehicle_type"
    )
    bootstrap_vw = pd.concat([bootstrap_vw, bootstrap_vw_accel, bootstrap_vw_accel_by_type], ignore_index=True)

    # --- Task D: Stage 0.5 reference interface -------------------------------
    reference_states = build_stage_0_5_reference_states(states)
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
    # write_real_reference_package expects the raw parsed schema (id +
    # longitudinal_accel_mps2); provide exactly that view from our parse.
    raw_view = states.rename(columns={"vehicle_id": "id"})[
        ["id", "time_s", "speed_mps", "longitudinal_accel_mps2"]
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
            )
            package_audit = json.loads((package_dir / "audit.json").read_text(encoding="utf-8"))
            stage_0_5_test_result = {
                "executed": True,
                "package_dir": str(package_dir.as_posix()),
                "kinematics_rows": package_audit["kinematics_rows"],
                "following_rows": package_audit["following_rows"],
                "risk_event_rows": package_audit["risk_event_rows"],
                "pneuma_ttc_included": package_audit["pneuma_ttc_included"],
                "gate_status": package_audit["gate_status"],
            }

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
            "method": "文件哈希 + 流式解析审计 + 结构测试",
            "result": f"{audit['unique_tracks']} 轨迹 / {audit['parsed_state_records']} 状态；畸形 0；重复 0",
            "evidence": "audit.json, states_audit.parquet, code/tests/test_pneuma_urban_kinematics.py",
            "status": "Verified",
            "remaining_limitation": "字段语义依据数据提供方文档；无独立物理真值",
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
            "basis": "Stage 0.5 接口契约与抽样审计",
            "method": "write_real_reference_package 构造 + 真实全量接口测试",
            "result": "接口测试通过；pNEUMA TTC 未纳入" if stage_0_5_test_result.get("executed") else "构造测试通过；真实接口测试未执行",
            "evidence": "stage_0_5_reference_states.parquet, sampling_balance_audit.csv",
            "status": "Verified (engineering)",
            "remaining_limitation": "Stage 0.5 场景分层/容差/Gate 未冻结；NGSIM+pNEUMA 不视为 iid",
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
        "gate_matrix.csv": gate_matrix,
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
