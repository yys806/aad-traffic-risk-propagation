"""Visual package for the formal local propagation baseline."""

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
RELATION_COLORS = {
    "same_vehicle": "#3A7CA5",
    "leader_to_follower": "#2A9D8F",
    "follower_to_leader": "#E9A03B",
    "same_region_local": "#7A5195",
}
CONTEXT_LABELS = {
    "stable_following": "Stable following",
    "interaction_transition_only": "Transition only",
    "adjacent_override_only": "Adjacent override only",
    "transition_and_adjacent_override": "Transition + adjacent override",
}


def create_local_baseline_visual_package(
    tables: dict[str, pd.DataFrame], output_dir: str | Path
) -> pd.DataFrame:
    """Render ten traceable figures from local baseline output tables."""
    required = {
        "eligible_episodes",
        "direct_edges",
        "chain_nodes",
        "chains",
        "cell_summary",
        "null_summary",
        "sensitivity",
    }
    missing = sorted(required - set(tables))
    if missing:
        raise ValueError(f"Missing local visual tables: {', '.join(missing)}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _configure_matplotlib()
    jobs: list[tuple[str, str, str, str, Callable[[Path], None]]] = [
        ("01_graph_coverage.png", "Local graph coverage", "coverage", "cell_summary", lambda path: _plot_graph_coverage(tables["cell_summary"], path)),
        ("02_relation_composition.png", "Local relation composition", "one_hop", "direct_edges", lambda path: _plot_relation_composition(tables["direct_edges"], path)),
        ("03_edge_rate_by_penetration.png", "Direct-edge rates across penetration", "one_hop", "cell_summary", lambda path: _plot_edge_rate(tables["cell_summary"], path)),
        ("04_depth_heatmap.png", "Maximum local propagation depth", "multi_hop", "cell_summary", lambda path: _plot_depth_heatmap(tables["cell_summary"], path)),
        ("05_multihop_share.png", "Multi-hop chain share", "multi_hop", "cell_summary", lambda path: _plot_multihop_share(tables["cell_summary"], path)),
        ("06_delay_distance_distribution.png", "Local link delay and distance", "one_hop", "direct_edges", lambda path: _plot_delay_distance(tables["direct_edges"], path)),
        ("07_context_strata.png", "Context strata of local links", "robustness", "direct_edges", lambda path: _plot_context_strata(tables["direct_edges"], path)),
        ("08_permutation_null.png", "Vehicle-wise time-shift null comparison", "null", "null_summary", lambda path: _plot_permutation_null(tables["null_summary"], path)),
        ("09_threshold_sensitivity.png", "Local threshold sensitivity", "sensitivity", "sensitivity", lambda path: _plot_threshold_sensitivity(tables["sensitivity"], path)),
        ("10_representative_chains.png", "Representative local multi-hop chains", "multi_hop", "chain_nodes|chains", lambda path: _plot_representative_chains(tables["chain_nodes"], tables["chains"], path)),
    ]
    rows = []
    for filename, title, category, source_table, render in jobs:
        render(output_dir / filename)
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


def _configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "axes.edgecolor": "#495057",
            "axes.labelcolor": "#212529",
            "xtick.color": "#343A40",
            "ytick.color": "#343A40",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def _plot_graph_coverage(cells: pd.DataFrame, path: Path) -> None:
    grouped = cells.groupby(["scenario", "method"], as_index=False).agg(
        eligible_events=("eligible_event_count", "sum"),
        direct_edges=("direct_edge_count", "sum"),
    )
    scenarios = _ordered(grouped["scenario"], ["ring", "figure8", "merge"])
    methods = _ordered(grouped["method"], ["ours", "fs", "pi"])
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), constrained_layout=True)
    _grouped_bars(axes[0], grouped, scenarios, methods, "eligible_events", "Eligible episodes")
    _grouped_bars(axes[1], grouped, scenarios, methods, "direct_edges", "Selected local edges")
    fig.suptitle("Local propagation baseline coverage", fontsize=15, fontweight="bold")
    _save(fig, path)


def _plot_relation_composition(edges: pd.DataFrame, path: Path) -> None:
    table = pd.crosstab(edges.get("method", pd.Series(dtype=str)), edges.get("edge_type", pd.Series(dtype=str)))
    methods = _ordered(table.index.to_series(), ["ours", "fs", "pi"])
    relations = [item for item in RELATION_COLORS if item in table.columns]
    table = table.reindex(index=methods, columns=relations, fill_value=0)
    fig, ax = plt.subplots(figsize=(10.5, 5.6), constrained_layout=True)
    bottom = np.zeros(len(table))
    for relation in relations:
        values = table[relation].to_numpy(dtype=float)
        ax.bar([METHOD_LABELS.get(item, item) for item in table.index], values, bottom=bottom, color=RELATION_COLORS[relation], label=relation.replace("_", " "))
        bottom += values
    ax.set_ylabel("Direct local edges")
    ax.set_title("Composition of selected one-hop relations", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="y", alpha=0.2)
    _save(fig, path)


def _plot_edge_rate(cells: pd.DataFrame, path: Path) -> None:
    scenarios = _ordered(cells["scenario"], ["ring", "figure8", "merge"])
    fig, axes = plt.subplots(1, max(len(scenarios), 1), figsize=(14.0, 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, scenario in zip(axes, scenarios):
        part = cells[cells["scenario"] == scenario]
        for method in _ordered(part["method"], ["ours", "fs", "pi"]):
            line = part[part["method"] == method].sort_values("penetration_pct")
            ax.plot(line["penetration_pct"], line["direct_edge_rate_per_1000_vehicle_s"], marker="o", linewidth=2.1, color=METHOD_COLORS.get(method, "#6C757D"), label=METHOD_LABELS.get(method, method))
        ax.set_title(SCENARIO_LABELS.get(scenario, scenario), fontweight="bold")
        ax.set_xlabel("AV penetration (%)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Direct edges / 1000 vehicle-s")
    _top_title_legend(fig, axes[0], "Exposure-normalised local edge rate")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.87))
    _save(fig, path)


def _plot_depth_heatmap(cells: pd.DataFrame, path: Path) -> None:
    rows = [(scenario, method) for scenario in ["ring", "figure8", "merge"] for method in ["ours", "fs", "pi"] if ((cells["scenario"] == scenario) & (cells["method"] == method)).any()]
    penetrations = sorted(cells["penetration_pct"].dropna().unique())
    matrix = np.full((len(rows), len(penetrations)), np.nan)
    for row_index, (scenario, method) in enumerate(rows):
        lookup = cells[(cells["scenario"] == scenario) & (cells["method"] == method)].set_index("penetration_pct")
        for column_index, penetration in enumerate(penetrations):
            matrix[row_index, column_index] = float(lookup["max_depth"].get(penetration, np.nan))
    fig, ax = plt.subplots(figsize=(11.8, 6.5), constrained_layout=True)
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=0)
    ax.set_xticks(range(len(penetrations)), [f"{int(value)}%" for value in penetrations])
    ax.set_yticks(range(len(rows)), [f"{SCENARIO_LABELS.get(s, s)} | {METHOD_LABELS.get(m, m)}" for s, m in rows])
    _annotate(ax, matrix, ".0f")
    fig.colorbar(image, ax=ax, label="Maximum hop depth", shrink=0.82)
    ax.set_title("Maximum local propagation depth", loc="left", fontweight="bold")
    _save(fig, path)


def _plot_multihop_share(cells: pd.DataFrame, path: Path) -> None:
    scenarios = _ordered(cells["scenario"], ["ring", "figure8", "merge"])
    fig, axes = plt.subplots(1, max(len(scenarios), 1), figsize=(14.0, 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, scenario in zip(axes, scenarios):
        part = cells[cells["scenario"] == scenario]
        for method in _ordered(part["method"], ["ours", "fs", "pi"]):
            line = part[part["method"] == method].sort_values("penetration_pct")
            ax.plot(line["penetration_pct"], line["multi_hop_chain_share"] * 100.0, marker="o", linewidth=2.1, color=METHOD_COLORS.get(method, "#6C757D"), label=METHOD_LABELS.get(method, method))
        ax.set_title(SCENARIO_LABELS.get(scenario, scenario), fontweight="bold")
        ax.set_xlabel("AV penetration (%)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Connected chains with depth ≥ 2 (%)")
    _top_title_legend(fig, axes[0], "Multi-hop share among connected local chains")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.87))
    _save(fig, path)


def _plot_delay_distance(edges: pd.DataFrame, path: Path) -> None:
    relations = [item for item in RELATION_COLORS if item in set(edges.get("edge_type", []))]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4), constrained_layout=True)
    if relations:
        delay_data = [pd.to_numeric(edges.loc[edges["edge_type"] == relation, "delay_s"], errors="coerce").dropna() for relation in relations]
        distance_data = [pd.to_numeric(edges.loc[edges["edge_type"] == relation, "distance_m"], errors="coerce").dropna() for relation in relations]
        axes[0].boxplot(delay_data, tick_labels=[item.replace("_", "\n") for item in relations], showfliers=False)
        axes[1].boxplot(distance_data, tick_labels=[item.replace("_", "\n") for item in relations], showfliers=False)
    axes[0].set_ylabel("Delay (s)")
    axes[1].set_ylabel("Local distance (m)")
    axes[0].set_title("One-hop delay", loc="left", fontweight="bold")
    axes[1].set_title("One-hop distance", loc="left", fontweight="bold")
    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Distribution of selected local links", fontsize=15, fontweight="bold")
    _save(fig, path)


def _plot_context_strata(edges: pd.DataFrame, path: Path) -> None:
    table = pd.crosstab(edges.get("edge_type", pd.Series(dtype=str)), edges.get("target_context_stratum", pd.Series(dtype=str)))
    relations = [item for item in RELATION_COLORS if item in table.index]
    contexts = [item for item in CONTEXT_LABELS if item in table.columns]
    table = table.reindex(index=relations, columns=contexts, fill_value=0)
    shares = table.div(table.sum(axis=1).replace(0, np.nan), axis=0) * 100.0
    colors = ["#2A9D8F", "#E9A03B", "#5C677D", "#D1495B"]
    fig, ax = plt.subplots(figsize=(11.2, 5.8), constrained_layout=True)
    left = np.zeros(len(shares))
    for context, color in zip(contexts, colors):
        values = shares[context].fillna(0).to_numpy()
        ax.barh([item.replace("_", " ") for item in shares.index], values, left=left, color=color, label=CONTEXT_LABELS[context])
        left += values
    ax.set_xlim(0, 100)
    ax.set_xlabel("Target-event context share (%)")
    ax.set_title("Context composition of selected local relations", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="x", alpha=0.15)
    _save(fig, path)


def _plot_permutation_null(null: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.5), constrained_layout=True)
    for scenario in _ordered(null["scenario"], ["ring", "figure8", "merge"]):
        part = null[null["scenario"] == scenario]
        axes[0].scatter(part["null_mean_cross_vehicle_edges"], part["observed_cross_vehicle_edges"], s=34, alpha=0.7, label=SCENARIO_LABELS.get(scenario, scenario))
    maxima = max(float(null["null_mean_cross_vehicle_edges"].max()), float(null["observed_cross_vehicle_edges"].max()), 1.0)
    axes[0].plot([0, maxima], [0, maxima], linestyle="--", color="#6C757D")
    axes[0].set_xlabel("Null mean cross-vehicle edges")
    axes[0].set_ylabel("Observed cross-vehicle edges")
    axes[0].set_title("Observed versus shifted-time null", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)
    grouped = null.groupby(["scenario", "method"], as_index=False)["z_score"].mean()
    labels = [f"{SCENARIO_LABELS.get(row.scenario, row.scenario)}\n{METHOD_LABELS.get(row.method, row.method)}" for row in grouped.itertuples()]
    colors = [METHOD_COLORS.get(method, "#6C757D") for method in grouped["method"]]
    axes[1].bar(labels, grouped["z_score"], color=colors)
    axes[1].axhline(0, color="#495057", linewidth=1.0)
    axes[1].set_ylabel("Mean null z-score")
    axes[1].set_title("Excess local timing alignment", loc="left", fontweight="bold")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y", alpha=0.2)
    fig.suptitle("Vehicle-wise circular time-shift null", fontsize=15, fontweight="bold")
    _save(fig, path)


def _plot_threshold_sensitivity(sensitivity: pd.DataFrame, path: Path) -> None:
    grouped = sensitivity.groupby(["max_delay_s", "max_distance_m"], as_index=False).agg(
        direct_edges=("direct_edge_count", "sum"),
        max_depth=("max_depth", "max"),
    )
    delays = sorted(grouped["max_delay_s"].unique())
    distances = sorted(grouped["max_distance_m"].unique())
    edge_matrix = _matrix(grouped, delays, distances, "direct_edges")
    depth_matrix = _matrix(grouped, delays, distances, "max_depth")
    default = grouped[np.isclose(grouped["max_delay_s"], 3.0) & np.isclose(grouped["max_distance_m"], 50.0)]
    baseline = float(default["direct_edges"].iloc[0]) if not default.empty and float(default["direct_edges"].iloc[0]) > 0 else 1.0
    edge_matrix = edge_matrix / baseline
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4), constrained_layout=True)
    image0 = axes[0].imshow(edge_matrix, cmap="YlGnBu", aspect="auto")
    image1 = axes[1].imshow(depth_matrix, cmap="YlOrRd", aspect="auto", vmin=0)
    for ax in axes:
        ax.set_xticks(range(len(distances)), [f"{int(value)}" for value in distances])
        ax.set_yticks(range(len(delays)), [f"{value:g}" for value in delays])
        ax.set_xlabel("Local distance window (m)")
        ax.set_ylabel("Time window (s)")
    _annotate(axes[0], edge_matrix, ".2f")
    _annotate(axes[1], depth_matrix, ".0f")
    axes[0].set_title("Edge count relative to 3 s / 50 m", loc="left", fontweight="bold")
    axes[1].set_title("Maximum hop depth", loc="left", fontweight="bold")
    fig.colorbar(image0, ax=axes[0], label="Relative direct-edge count", shrink=0.8)
    fig.colorbar(image1, ax=axes[1], label="Depth", shrink=0.8)
    fig.suptitle("Local definition sensitivity", fontsize=15, fontweight="bold")
    _save(fig, path)


def _plot_representative_chains(nodes: pd.DataFrame, chains: pd.DataFrame, path: Path) -> None:
    ranked = chains.sort_values(["max_depth", "event_count", "cumulative_link_score"], ascending=False).head(3)
    fig, axes = plt.subplots(max(len(ranked), 1), 1, figsize=(12.0, 3.3 * max(len(ranked), 1)), constrained_layout=True)
    axes = np.atleast_1d(axes)
    if ranked.empty:
        axes[0].text(0.5, 0.5, "No local chains available", ha="center", va="center")
        axes[0].set_axis_off()
    for ax, chain in zip(axes, ranked.itertuples()):
        part = nodes[nodes["chain_id"] == chain.chain_id].sort_values(["hop_depth", "time", "event_id"])
        positions = {row.event_id: (float(row.time), int(row.hop_depth)) for row in part.itertuples()}
        max_depth = int(part["hop_depth"].max())
        for row in part.itertuples():
            x, y = positions[row.event_id]
            ax.scatter(x, y, s=95, color=METHOD_COLORS.get(row.method, "#167D8D"), edgecolor="white", linewidth=0.8, zorder=3)
            should_label = int(row.hop_depth) == 0 or int(row.hop_depth) % 5 == 0
            if should_label:
                ax.annotate(f"{row.vehicle_id}\n{row.event_type}", (x, y), xytext=(5, 8), textcoords="offset points", fontsize=7.5)
            if row.parent_event_id and row.parent_event_id in positions:
                px, py = positions[row.parent_event_id]
                ax.annotate("", xy=(x, y), xytext=(px, py), arrowprops={"arrowstyle": "-|>", "color": "#5C677D", "lw": 1.3})
        ax.set_yticks(range(max_depth + 1))
        ax.set_ylabel("Hop depth")
        ax.set_xlabel("Simulation time (s)")
        ax.set_title(f"{SCENARIO_LABELS.get(chain.scenario, chain.scenario)} | {METHOD_LABELS.get(chain.method, chain.method)} | depth={int(chain.max_depth)} | events={int(chain.event_count)}", loc="left", fontweight="bold")
        ax.grid(alpha=0.18)
    fig.suptitle("Representative local propagation chains", fontsize=15, fontweight="bold")
    _save(fig, path)


def _grouped_bars(ax: plt.Axes, data: pd.DataFrame, scenarios: list[str], methods: list[str], column: str, ylabel: str) -> None:
    x = np.arange(len(scenarios), dtype=float)
    width = 0.24
    for index, method in enumerate(methods):
        lookup = data[data["method"] == method].set_index("scenario")
        values = [float(lookup[column].get(scenario, 0.0)) for scenario in scenarios]
        ax.bar(x + (index - (len(methods) - 1) / 2) * width, values, width, color=METHOD_COLORS.get(method, "#6C757D"), label=METHOD_LABELS.get(method, method))
    ax.set_xticks(x, [SCENARIO_LABELS.get(item, item) for item in scenarios])
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.2)


def _top_title_legend(fig: plt.Figure, legend_ax: plt.Axes, title: str) -> None:
    handles, labels = legend_ax.get_legend_handles_labels()
    fig.suptitle(title, y=0.985, fontsize=15, fontweight="bold")
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.91), ncol=3, frameon=False)


def _matrix(data: pd.DataFrame, rows: list[float], columns: list[float], value: str) -> np.ndarray:
    matrix = np.full((len(rows), len(columns)), np.nan)
    lookup = data.set_index(["max_delay_s", "max_distance_m"])[value]
    for row_index, row in enumerate(rows):
        for column_index, column in enumerate(columns):
            matrix[row_index, column_index] = float(lookup.get((row, column), np.nan))
    return matrix


def _ordered(values: pd.Series, preferred: list[str]) -> list[str]:
    present = [str(value) for value in pd.Series(values).dropna().unique()]
    return [item for item in preferred if item in present] + sorted(item for item in present if item not in preferred)


def _annotate(ax: plt.Axes, matrix: np.ndarray, fmt: str) -> None:
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            if np.isfinite(value):
                ax.text(column, row, format(float(value), fmt), ha="center", va="center", fontsize=8, color="#212529")


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
