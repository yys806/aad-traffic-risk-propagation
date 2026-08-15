"""Render traceable figures from the validated full risk-event dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm


METHOD_COLORS = {"ours": "#167D8D", "fs": "#D1495B", "pi": "#E9A03B"}
METHOD_LABELS = {"ours": "DRIFT", "fs": "FS", "pi": "PI"}
SCENARIO_LABELS = {"ring": "Ring", "figure8": "Figure-eight", "merge": "Merge"}
EVENT_LABELS = {
    "hard_braking": "Ordinary braking",
    "low_ttc": "Low TTC",
    "critical_ttc": "Critical TTC",
    "low_thw": "Low THW",
    "near_miss": "Near miss",
    "safe_speed_override_candidate": "SUMO override candidate",
}
EVENT_COLORS = {
    "hard_braking": "#3A7CA5",
    "low_ttc": "#E76F51",
    "critical_ttc": "#A11D33",
    "low_thw": "#E9A03B",
    "near_miss": "#7A5195",
    "safe_speed_override_candidate": "#5C677D",
}

REQUIRED_INPUTS = {
    "manifest": "extraction_manifest.csv",
    "rates": "event_rates_summary.csv",
    "sensitivity": "threshold_sensitivity_summary.csv",
    "comparison": "threshold_sensitivity_comparison.csv",
    "review": "manual_review_sample.csv",
}


def create_risk_event_visual_package(
    input_dir: str | Path,
    output_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Create the full figure package and return its traceability catalog."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir) if output_dir is not None else input_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = _load_inputs(input_dir)
    _configure_matplotlib()

    jobs: list[tuple[str, str, str, str, Callable[[Path], None]]] = [
        (
            "01_data_coverage.png",
            "Formal data coverage and vehicle-time exposure",
            "coverage",
            REQUIRED_INPUTS["manifest"],
            lambda path: _plot_data_coverage(tables["manifest"], path),
        ),
        (
            "02_episode_composition.png",
            "Risk episode composition",
            "taxonomy",
            REQUIRED_INPUTS["rates"],
            lambda path: _plot_episode_composition(tables["rates"], path),
        ),
        (
            "03_event_rate_by_penetration.png",
            "Event rates across AV penetration",
            "rates",
            REQUIRED_INPUTS["rates"],
            lambda path: _plot_event_rate_by_penetration(tables["rates"], path),
        ),
        (
            "04_scenario_method_heatmap.png",
            "Scenario and method event-rate matrix",
            "rates",
            REQUIRED_INPUTS["rates"],
            lambda path: _plot_scenario_method_heatmap(tables["rates"], path),
        ),
        (
            "05_ttc_threshold_sensitivity.png",
            "TTC threshold sensitivity",
            "sensitivity",
            REQUIRED_INPUTS["sensitivity"],
            lambda path: _plot_threshold_sensitivity(
                tables["sensitivity"], "ttc_conflict", path
            ),
        ),
        (
            "06_braking_threshold_sensitivity.png",
            "Ordinary-braking threshold sensitivity",
            "sensitivity",
            REQUIRED_INPUTS["sensitivity"],
            lambda path: _plot_threshold_sensitivity(
                tables["sensitivity"], "ordinary_braking", path
            ),
        ),
        (
            "07_drift_improvement_heatmap.png",
            "DRIFT improvement relative to FS and PI",
            "comparison",
            REQUIRED_INPUTS["comparison"],
            lambda path: _plot_drift_improvement(tables["comparison"], path),
        ),
        (
            "08_drift_win_rate.png",
            "DRIFT win, tie, and loss composition",
            "comparison",
            REQUIRED_INPUTS["comparison"],
            lambda path: _plot_drift_win_rate(tables["comparison"], path),
        ),
        (
            "09_manual_review_outcomes.png",
            "Manual review outcomes by event class",
            "review",
            REQUIRED_INPUTS["review"],
            lambda path: _plot_manual_review_outcomes(tables["review"], path),
        ),
        (
            "10_context_flag_composition.png",
            "Manual-review context flags",
            "review",
            REQUIRED_INPUTS["review"],
            lambda path: _plot_context_flags(tables["review"], path),
        ),
        (
            "11_override_rate_by_penetration.png",
            "SUMO override-candidate rate",
            "diagnostic",
            REQUIRED_INPUTS["sensitivity"],
            lambda path: _plot_override_rate(tables["sensitivity"], path),
        ),
        (
            "12_representative_event_context.png",
            "Representative adjacent-frame event context",
            "review",
            REQUIRED_INPUTS["review"],
            lambda path: _plot_representative_context(tables["review"], path),
        ),
    ]

    rows: list[dict[str, str]] = []
    for filename, title, category, source_table, render in jobs:
        path = output_dir / filename
        render(path)
        rows.append(
            {
                "filename": filename,
                "title": title,
                "category": category,
                "source_table": source_table,
            }
        )
    catalog = pd.DataFrame(rows)
    catalog.to_csv(output_dir / "figure_catalog.csv", index=False)
    return catalog


def _load_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for key, filename in REQUIRED_INPUTS.items():
        path = input_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required visual input is missing: {path}")
        tables[key] = pd.read_csv(path)
    required_columns = {
        "manifest": {"scenario", "method", "penetration_pct", "vehicle_time_s"},
        "rates": {
            "scenario",
            "method",
            "penetration_pct",
            "event_type",
            "episode_count",
            "vehicle_time_s",
            "pooled_episode_rate_per_1000_vehicle_s",
            "episode_rate_run_mean",
            "episode_rate_run_ci95",
        },
        "sensitivity": {
            "scenario",
            "method",
            "penetration_pct",
            "metric",
            "threshold",
            "frame_count",
            "vehicle_time_s",
            "pooled_rate_per_1000_vehicle_s",
            "run_rate_mean",
            "run_rate_ci95",
        },
        "comparison": {
            "scenario",
            "penetration_pct",
            "metric",
            "threshold",
            "baseline",
            "signed_improvement",
            "drift_better",
            "tie",
        },
        "review": {"event_type", "review_status", "review_notes"},
    }
    for key, columns in required_columns.items():
        missing = sorted(columns - set(tables[key].columns))
        if missing:
            raise ValueError(f"{REQUIRED_INPUTS[key]} missing columns: {', '.join(missing)}")
    return tables


def _configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Microsoft YaHei",
                "SimHei",
                "Noto Sans CJK SC",
                "Arial",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "axes.edgecolor": "#495057",
            "axes.labelcolor": "#212529",
            "xtick.color": "#343A40",
            "ytick.color": "#343A40",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _plot_data_coverage(manifest: pd.DataFrame, path: Path) -> None:
    grouped = (
        manifest.groupby(["scenario", "method"], as_index=False)
        .agg(file_count=("source_file", "count"), vehicle_time_s=("vehicle_time_s", "sum"))
    )
    scenarios = _ordered(grouped["scenario"], ["ring", "figure8", "merge"])
    methods = _ordered(grouped["method"], ["ours", "fs", "pi"])
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), constrained_layout=True)
    _grouped_bars(
        axes[0], grouped, scenarios, methods, "file_count", "Formal emission files"
    )
    grouped["vehicle_hours"] = grouped["vehicle_time_s"] / 3600.0
    _grouped_bars(
        axes[1], grouped, scenarios, methods, "vehicle_hours", "Vehicle-time exposure (h)"
    )
    fig.suptitle("Formal dataset coverage", fontsize=15, fontweight="bold")
    _save(fig, path)


def _plot_episode_composition(rates: pd.DataFrame, path: Path) -> None:
    grouped = rates.groupby(["method", "event_type"], as_index=False)["episode_count"].sum()
    event_types = _ordered(grouped["event_type"], list(EVENT_LABELS))
    methods = _ordered(grouped["method"], ["ours", "fs", "pi"])
    fig, ax = plt.subplots(figsize=(11.6, 6.0), constrained_layout=True)
    x = np.arange(len(event_types), dtype=float)
    width = 0.24
    for index, method in enumerate(methods):
        subset = grouped[grouped["method"] == method].set_index("event_type")
        values = [float(subset["episode_count"].get(event_type, 0.0)) for event_type in event_types]
        ax.bar(
            x + (index - (len(methods) - 1) / 2) * width,
            values,
            width,
            label=METHOD_LABELS.get(method, method),
            color=METHOD_COLORS.get(method, "#6C757D"),
        )
    ax.set_xticks(x, [EVENT_LABELS.get(item, item) for item in event_types], rotation=18, ha="right")
    ax.set_ylabel("Episode count")
    ax.set_title("Risk episode composition (override candidates shown separately)", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, ncol=3)
    _save(fig, path)


def _plot_event_rate_by_penetration(rates: pd.DataFrame, path: Path) -> None:
    event_types = [
        "hard_braking",
        "low_ttc",
        "critical_ttc",
        "low_thw",
        "near_miss",
        "safe_speed_override_candidate",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14.5, 8.2), sharex=True)
    for ax, event_type in zip(axes.flat, event_types):
        subset = rates[rates["event_type"] == event_type]
        pooled = _pool_counts(subset, ["method", "penetration_pct"], "episode_count")
        for method in _ordered(pooled["method"], ["ours", "fs", "pi"]):
            line = pooled[pooled["method"] == method].sort_values("penetration_pct")
            ax.plot(
                line["penetration_pct"],
                line["pooled_rate"],
                marker="o",
                linewidth=2.0,
                label=METHOD_LABELS.get(method, method),
                color=METHOD_COLORS.get(method, "#6C757D"),
            )
        ax.set_title(EVENT_LABELS.get(event_type, event_type), loc="left", fontweight="bold")
        ax.grid(alpha=0.2)
        ax.set_xlabel("AV penetration (%)")
        ax.set_ylabel("Episodes / 1000 vehicle-s")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.suptitle(
        "Exposure-normalised event rates across penetration",
        y=0.985,
        fontsize=15,
        fontweight="bold",
    )
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.945),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.89))
    _save(fig, path)


def _plot_scenario_method_heatmap(rates: pd.DataFrame, path: Path) -> None:
    pooled = _pool_counts(rates, ["scenario", "method", "event_type"], "episode_count")
    rows = [
        (scenario, method)
        for scenario in ["ring", "figure8", "merge"]
        for method in ["ours", "fs", "pi"]
        if ((pooled["scenario"] == scenario) & (pooled["method"] == method)).any()
    ]
    columns = _ordered(pooled["event_type"], list(EVENT_LABELS))
    matrix = np.full((len(rows), len(columns)), np.nan)
    for row_index, (scenario, method) in enumerate(rows):
        lookup = pooled[(pooled["scenario"] == scenario) & (pooled["method"] == method)].set_index("event_type")
        for column_index, event_type in enumerate(columns):
            matrix[row_index, column_index] = float(lookup["pooled_rate"].get(event_type, np.nan))
    fig, ax = plt.subplots(figsize=(12.6, 6.8), constrained_layout=True)
    image = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(columns)), [EVENT_LABELS.get(item, item) for item in columns], rotation=24, ha="right")
    ax.set_yticks(
        range(len(rows)),
        [f"{SCENARIO_LABELS.get(s, s)} | {METHOD_LABELS.get(m, m)}" for s, m in rows],
    )
    _annotate_heatmap(ax, matrix, fmt=".1f")
    fig.colorbar(image, ax=ax, label="Episodes / 1000 vehicle-s", shrink=0.82)
    ax.set_title("Scenario-method risk-event rate matrix", loc="left", fontweight="bold")
    _save(fig, path)


def _plot_threshold_sensitivity(data: pd.DataFrame, metric: str, path: Path) -> None:
    subset = data[data["metric"] == metric].copy()
    scenarios = _ordered(subset["scenario"], ["ring", "figure8", "merge"])
    fig, axes = plt.subplots(1, max(len(scenarios), 1), figsize=(14.0, 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, scenario in zip(axes, scenarios):
        scenario_data = subset[subset["scenario"] == scenario]
        pooled = _pool_counts(scenario_data, ["method", "threshold"], "frame_count")
        for method in _ordered(pooled["method"], ["ours", "fs", "pi"]):
            line = pooled[pooled["method"] == method].sort_values("threshold")
            ax.plot(
                line["threshold"],
                line["pooled_rate"],
                marker="o",
                linewidth=2.1,
                color=METHOD_COLORS.get(method, "#6C757D"),
                label=METHOD_LABELS.get(method, method),
            )
        ax.set_title(SCENARIO_LABELS.get(scenario, scenario), fontweight="bold")
        ax.set_xlabel("TTC threshold (s)" if metric == "ttc_conflict" else "Acceleration threshold (m/s²)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Frames / 1000 vehicle-s")
    handles, labels = axes[0].get_legend_handles_labels()
    title = "Leader-aware TTC threshold sensitivity" if metric == "ttc_conflict" else "Ordinary-braking threshold sensitivity (override candidates excluded)"
    fig.suptitle(title, y=0.985, fontsize=15, fontweight="bold")
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.91),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.87))
    _save(fig, path)


def _plot_drift_improvement(comparison: pd.DataFrame, path: Path) -> None:
    selected = comparison[
        ((comparison["metric"] == "ttc_conflict") & np.isclose(comparison["threshold"], 2.0))
        | ((comparison["metric"] == "ordinary_braking") & np.isclose(comparison["threshold"], -3.0))
    ].copy()
    metrics = ["ttc_conflict", "ordinary_braking"]
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.6), constrained_layout=True)
    for ax, metric in zip(axes, metrics):
        part = selected[selected["metric"] == metric]
        rows = [
            (scenario, baseline)
            for scenario in ["ring", "figure8", "merge"]
            for baseline in ["fs", "pi"]
            if ((part["scenario"] == scenario) & (part["baseline"] == baseline)).any()
        ]
        penetrations = sorted(part["penetration_pct"].dropna().unique())
        matrix = np.full((len(rows), len(penetrations)), np.nan)
        for row_index, (scenario, baseline) in enumerate(rows):
            lookup = part[(part["scenario"] == scenario) & (part["baseline"] == baseline)].set_index("penetration_pct")
            for column_index, penetration in enumerate(penetrations):
                matrix[row_index, column_index] = float(lookup["signed_improvement"].get(penetration, np.nan))
        finite = matrix[np.isfinite(matrix)]
        limit = max(float(np.max(np.abs(finite))) if finite.size else 1.0, 1e-6)
        image = ax.imshow(matrix, cmap="RdBu", norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit), aspect="auto")
        ax.set_xticks(range(len(penetrations)), [f"{int(value)}%" for value in penetrations])
        ax.set_yticks(
            range(len(rows)),
            [f"{SCENARIO_LABELS.get(s, s)} | vs {METHOD_LABELS.get(b, b)}" for s, b in rows],
        )
        _annotate_heatmap(ax, matrix, fmt="+.1f")
        label = "TTC ≤ 2.0 s" if metric == "ttc_conflict" else "Braking ≤ -3.0 m/s²"
        ax.set_title(label, loc="left", fontweight="bold")
        fig.colorbar(image, ax=ax, label="Baseline rate - DRIFT rate", shrink=0.78)
    fig.suptitle("DRIFT rate improvement (positive values favour DRIFT)", fontsize=15, fontweight="bold")
    _save(fig, path)


def _plot_drift_win_rate(comparison: pd.DataFrame, path: Path) -> None:
    grouped_rows = []
    for (baseline, metric), group in comparison.groupby(["baseline", "metric"], sort=True):
        wins = int(group["drift_better"].fillna(False).astype(bool).sum())
        ties = int(group["tie"].fillna(False).astype(bool).sum())
        losses = int(len(group) - wins - ties)
        grouped_rows.append({"label": f"vs {METHOD_LABELS.get(baseline, baseline)} | {metric}", "win": wins, "tie": ties, "loss": losses})
    grouped = pd.DataFrame(grouped_rows)
    totals = grouped[["win", "tie", "loss"]].sum(axis=1).replace(0, np.nan)
    shares = grouped[["win", "tie", "loss"]].div(totals, axis=0) * 100.0
    fig, ax = plt.subplots(figsize=(11.5, 5.8), constrained_layout=True)
    left = np.zeros(len(grouped))
    for column, color, label in [
        ("win", "#2A9D8F", "DRIFT lower"),
        ("tie", "#ADB5BD", "Tie"),
        ("loss", "#D1495B", "DRIFT higher"),
    ]:
        ax.barh(grouped["label"], shares[column], left=left, color=color, label=label)
        for index, value in enumerate(shares[column]):
            if value >= 8:
                ax.text(left[index] + value / 2, index, f"{value:.0f}%", ha="center", va="center", fontsize=9, color="white" if column != "tie" else "#212529")
        left += shares[column].fillna(0).to_numpy()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of scenario-penetration-threshold comparisons (%)")
    ax.set_title("DRIFT comparison outcomes", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    ax.grid(axis="x", alpha=0.15)
    _save(fig, path)


def _plot_manual_review_outcomes(review: pd.DataFrame, path: Path) -> None:
    table = pd.crosstab(review["event_type"], review["review_status"])
    event_types = _ordered(table.index.to_series(), list(EVENT_LABELS))
    table = table.reindex(event_types, fill_value=0)
    statuses = [item for item in ["retained", "retained_flagged", "excluded"] if item in table.columns]
    colors = {"retained": "#2A9D8F", "retained_flagged": "#E9A03B", "excluded": "#D1495B"}
    labels = {"retained": "Retained", "retained_flagged": "Retained with flags", "excluded": "Excluded"}
    fig, ax = plt.subplots(figsize=(11.5, 5.8), constrained_layout=True)
    bottom = np.zeros(len(table))
    for status in statuses:
        values = table[status].to_numpy(dtype=float)
        ax.bar([EVENT_LABELS.get(item, item) for item in table.index], values, bottom=bottom, color=colors[status], label=labels[status])
        bottom += values
    ax.set_ylabel("Reviewed episodes")
    ax.set_title("Manual review outcomes by event class", loc="left", fontweight="bold")
    ax.tick_params(axis="x", rotation=18)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.2)
    _save(fig, path)


def _plot_context_flags(review: pd.DataFrame, path: Path) -> None:
    notes = review["review_notes"].fillna("").astype(str)
    labels = ["Leader transition", "Lane transition", "Adjacent override", "Entry/exit boundary"]
    patterns = ["leader_transition", "lane_transition", "adjacent_override", "vehicle_boundary"]
    counts = [int(notes.str.contains(pattern, regex=False).sum()) for pattern in patterns]
    fig, ax = plt.subplots(figsize=(9.8, 5.4), constrained_layout=True)
    bars = ax.barh(labels[::-1], counts[::-1], color=["#5C677D", "#7A5195", "#E9A03B", "#3A7CA5"][::-1])
    for bar, value in zip(bars, counts[::-1]):
        ax.text(bar.get_width() + 0.25, bar.get_y() + bar.get_height() / 2, str(value), va="center")
    ax.set_xlabel("Reviewed episodes with flag")
    ax.set_title("Context flags retained for sensitivity strata", loc="left", fontweight="bold")
    ax.grid(axis="x", alpha=0.2)
    _save(fig, path)


def _plot_override_rate(data: pd.DataFrame, path: Path) -> None:
    subset = data[data["metric"] == "safe_speed_override_candidate"]
    scenarios = _ordered(subset["scenario"], ["ring", "figure8", "merge"])
    fig, axes = plt.subplots(1, max(len(scenarios), 1), figsize=(14.0, 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, scenario in zip(axes, scenarios):
        part = subset[subset["scenario"] == scenario]
        for method in _ordered(part["method"], ["ours", "fs", "pi"]):
            line = part[part["method"] == method].sort_values("penetration_pct")
            ax.plot(
                line["penetration_pct"],
                line["pooled_rate_per_1000_vehicle_s"],
                marker="o",
                linewidth=2.1,
                color=METHOD_COLORS.get(method, "#6C757D"),
                label=METHOD_LABELS.get(method, method),
            )
        ax.set_title(SCENARIO_LABELS.get(scenario, scenario), fontweight="bold")
        ax.set_xlabel("AV penetration (%)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Frames / 1000 vehicle-s")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle(
        "SUMO safe-speed override candidates (excluded from ordinary braking)",
        y=0.985,
        fontsize=15,
        fontweight="bold",
    )
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.91),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.87))
    _save(fig, path)


def _plot_representative_context(review: pd.DataFrame, path: Path) -> None:
    selected = _select_representative_rows(review, max_rows=3)
    fig, axes = plt.subplots(max(len(selected), 1), 1, figsize=(11.8, 3.1 * max(len(selected), 1)), constrained_layout=True)
    axes = np.atleast_1d(axes)
    if selected.empty:
        axes[0].text(0.5, 0.5, "No review examples available", ha="center", va="center")
        axes[0].set_axis_off()
    for ax, row in zip(axes, selected.itertuples()):
        times = np.array([row.previous_time_s, row.time, row.next_time_s], dtype=float)
        speeds = np.array([row.previous_speed_mps, row.speed, row.next_speed_mps], dtype=float)
        accelerations = np.array(
            [row.previous_acceleration_mps2, row.acceleration, row.next_acceleration_mps2],
            dtype=float,
        )
        speed_line = ax.plot(times, speeds, marker="o", linewidth=2.1, color="#167D8D", label="Speed")[0]
        ax.set_ylabel("Speed (m/s)", color="#167D8D")
        ax.tick_params(axis="y", labelcolor="#167D8D")
        twin = ax.twinx()
        accel_line = twin.plot(times, accelerations, marker="s", linewidth=1.9, color="#D1495B", label="Acceleration")[0]
        twin.axhline(-15.0, color="#5C677D", linestyle="--", linewidth=1.0, alpha=0.75)
        twin.set_ylabel("Acceleration (m/s²)", color="#D1495B")
        twin.tick_params(axis="y", labelcolor="#D1495B")
        ax.axvline(float(row.time), color="#343A40", linestyle=":", linewidth=1.2)
        ax.set_title(
            f"{EVENT_LABELS.get(row.event_type, row.event_type)} | {row.scenario} | {METHOD_LABELS.get(row.method, row.method)} | {row.vehicle_id}",
            loc="left",
            fontweight="bold",
        )
        ax.set_xlabel("Simulation time (s)")
        ax.grid(alpha=0.18)
        ax.legend([speed_line, accel_line], ["Speed", "Acceleration"], frameon=False, ncol=2, loc="upper right")
    fig.suptitle("Representative adjacent-frame event context", fontsize=15, fontweight="bold")
    _save(fig, path)


def _select_representative_rows(review: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    candidates = []
    preferred = ["hard_braking", "low_ttc", "safe_speed_override_candidate"]
    for event_type in preferred:
        subset = review[review["event_type"] == event_type].copy()
        if subset.empty:
            continue
        sort_column = "risk_score" if "risk_score" in subset.columns else "time"
        candidates.append(subset.sort_values(sort_column, ascending=False).head(1))
    if not candidates:
        return review.head(max_rows).copy()
    return pd.concat(candidates, ignore_index=True).head(max_rows)


def _pool_counts(data: pd.DataFrame, keys: list[str], count_column: str) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame(columns=[*keys, "pooled_rate"])
    pooled = (
        data.groupby(keys, as_index=False)
        .agg(count=(count_column, "sum"), vehicle_time_s=("vehicle_time_s", "sum"))
    )
    pooled["pooled_rate"] = np.where(
        pooled["vehicle_time_s"] > 0,
        pooled["count"] / pooled["vehicle_time_s"] * 1000.0,
        np.nan,
    )
    return pooled


def _grouped_bars(
    ax: plt.Axes,
    data: pd.DataFrame,
    scenarios: list[str],
    methods: list[str],
    value_column: str,
    ylabel: str,
) -> None:
    x = np.arange(len(scenarios), dtype=float)
    width = 0.24
    for index, method in enumerate(methods):
        subset = data[data["method"] == method].set_index("scenario")
        values = [float(subset[value_column].get(scenario, 0.0)) for scenario in scenarios]
        ax.bar(
            x + (index - (len(methods) - 1) / 2) * width,
            values,
            width,
            label=METHOD_LABELS.get(method, method),
            color=METHOD_COLORS.get(method, "#6C757D"),
        )
    ax.set_xticks(x, [SCENARIO_LABELS.get(item, item) for item in scenarios])
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, ncol=3)


def _ordered(values: pd.Series, preferred: list[str]) -> list[str]:
    present = [str(value) for value in pd.Series(values).dropna().unique()]
    return [item for item in preferred if item in present] + sorted(
        item for item in present if item not in preferred
    )


def _annotate_heatmap(ax: plt.Axes, matrix: np.ndarray, fmt: str) -> None:
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            if np.isfinite(value):
                ax.text(column, row, format(float(value), fmt), ha="center", va="center", fontsize=8, color="#212529")


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
