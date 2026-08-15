from __future__ import annotations

from collections import deque
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


EVENT_COLORS = {
    "critical_ttc": "#b42318",
    "low_ttc": "#e65a3d",
    "low_thw": "#f0a202",
    "severe_braking": "#7a3e9d",
    "hard_braking": "#2b6cb0",
    "near_miss": "#d14c8b",
}


def create_visual_package(
    events: pd.DataFrame,
    direct_edges: pd.DataFrame,
    roles: pd.DataFrame,
    output_dir: str | Path,
    max_cases: int = 3,
) -> pd.DataFrame:
    """Create concise, presentation-ready visualisations for one analysed run."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    _plot_event_distribution(events, figures_dir / "01_event_distribution.png")
    _plot_top_sources(roles, figures_dir / "02_top_risk_sources.png")
    _plot_overview(events, direct_edges, roles, figures_dir / "03_direct_risk_graph_overview.png")

    cases = _select_cases(events, direct_edges, roles, max_cases=max_cases)
    rows: list[dict[str, object]] = []
    for index, root_event_id in enumerate(cases, start=1):
        case_events, case_edges = _case_subgraph(events, direct_edges, root_event_id)
        image_name = f"case_{index:02d}_risk_chain.png"
        _plot_case_chain(case_events, case_edges, root_event_id, figures_dir / image_name)
        root = case_events.loc[case_events["event_id"] == root_event_id].iloc[0]
        rows.append(
            {
                "case_id": f"case_{index:02d}",
                "root_event_id": root_event_id,
                "root_vehicle_id": root["vehicle_id"],
                "root_event_type": root["event_type"],
                "root_time_s": round(float(root["time"]), 3),
                "event_count": int(len(case_events)),
                "edge_count": int(len(case_edges)),
                "figure": f"figures/{image_name}",
            }
        )

    case_frame = pd.DataFrame(rows)
    case_frame.to_csv(output_dir / "case_catalog.csv", index=False)
    return case_frame


def plot_method_flow(path: str | Path) -> None:
    path = Path(path)
    fig, ax = plt.subplots(figsize=(12.0, 3.2), constrained_layout=True)
    ax.set_axis_off()
    boxes = [
        (0.12, "Closed-loop\nFlow rollout", "#dbeafe"),
        (0.36, "Risk event\nextraction", "#fee2e2"),
        (0.60, "Candidate edges\n(time-space)", "#fef3c7"),
        (0.84, "Direct risk\npropagation graph", "#dcfce7"),
    ]
    for x, label, color in boxes:
        ax.text(
            x,
            0.5,
            label,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color="#1f2937",
            bbox={"boxstyle": "round,pad=0.65", "facecolor": color, "edgecolor": "#64748b", "linewidth": 1.2},
        )
    for x in [0.215, 0.455, 0.695]:
        ax.annotate("", xy=(x + 0.065, 0.5), xytext=(x, 0.5), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "lw": 2.0, "color": "#475569"})
    ax.text(0.5, 0.08, "Role scoring and intervention-candidate screening", transform=ax.transAxes, ha="center", fontsize=12, color="#475569")
    _save(fig, path)


def plot_edge_selection(candidate_edges: pd.DataFrame, direct_edges: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
    axes[0].bar(["Candidate edges", "Direct edges"], [len(candidate_edges), len(direct_edges)], color=["#fbbf24", "#2563eb"])
    axes[0].set_title("Edge selection compresses dense candidate links", loc="left", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Edge count")
    for index, value in enumerate([len(candidate_edges), len(direct_edges)]):
        axes[0].text(index, value + max(len(candidate_edges) * 0.01, 1), f"{value:,}", ha="center", fontsize=10)
    relation_counts = direct_edges["edge_type"].value_counts().sort_values(ascending=True) if not direct_edges.empty else pd.Series(dtype=int)
    axes[1].barh(relation_counts.index, relation_counts.values, color="#0f766e")
    axes[1].set_title("Direct edge composition", loc="left", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Edge count")
    axes[1].grid(axis="x", alpha=0.2)
    _save(fig, path)


def plot_intervention_screening(candidates: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    ranked = candidates.head(10).copy()
    fig, ax = plt.subplots(figsize=(9.5, 5.5), constrained_layout=True)
    labels = [f"{row.event_id}\n{row.event_type}" for row in ranked.itertuples()]
    colors = [EVENT_COLORS.get(event_type, "#64748b") for event_type in ranked["event_type"]]
    ax.barh(labels[::-1], ranked["intervention_priority"].iloc[::-1], color=colors[::-1])
    ax.set_title("Graph-level intervention candidate screening", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Screening priority (not a simulated treatment effect)")
    ax.grid(axis="x", alpha=0.2)
    _save(fig, path)


def _plot_event_distribution(events: pd.DataFrame, path: Path) -> None:
    counts = events["event_type"].value_counts().sort_values(ascending=True) if not events.empty else pd.Series(dtype=int)
    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    colors = [EVENT_COLORS.get(name, "#64748b") for name in counts.index]
    ax.barh(counts.index, counts.values, color=colors)
    for y, value in enumerate(counts.values):
        ax.text(value + max(counts.values.max() * 0.01, 0.2), y, str(int(value)), va="center", fontsize=10)
    ax.set_title("Risk event composition (real Flow merge rollout)", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Event count")
    ax.grid(axis="x", alpha=0.2)
    _save(fig, path)


def _plot_top_sources(roles: pd.DataFrame, path: Path) -> None:
    ranked = roles.sort_values(["source_score", "out_strength"], ascending=False).head(10).copy()
    labels = [f"{row.event_id}\n{row.event_type}" for row in ranked.itertuples()]
    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    colors = [EVENT_COLORS.get(event_type, "#64748b") for event_type in ranked["event_type"]]
    ax.barh(labels[::-1], ranked["source_score"].iloc[::-1], color=colors[::-1])
    ax.set_title("Top source events by direct propagation strength", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Normalised source score")
    ax.set_xlim(0, 1.05)
    ax.grid(axis="x", alpha=0.2)
    _save(fig, path)


def _plot_overview(events: pd.DataFrame, edges: pd.DataFrame, roles: pd.DataFrame, path: Path) -> None:
    ranked_roots = _select_cases(events, edges, roles, max_cases=6)
    selected_ids: set[str] = set()
    for root_event_id in ranked_roots:
        case_events, _ = _case_subgraph(events, edges, root_event_id, max_nodes=8, max_depth=1)
        selected_ids.update(case_events["event_id"].tolist())
    selected_events = events[events["event_id"].isin(selected_ids)].copy()
    selected_edges = edges[edges["source_event_id"].isin(selected_ids) & edges["target_event_id"].isin(selected_ids)].copy()

    fig, ax = plt.subplots(figsize=(11.5, 6.4), constrained_layout=True)
    _draw_time_vehicle_graph(ax, selected_events, selected_edges, label_nodes=False)
    ax.set_title("Direct risk propagation graph: representative high-risk subgraph", loc="left", fontsize=14, fontweight="bold")
    _add_event_legend(ax)
    _save(fig, path)


def _plot_case_chain(events: pd.DataFrame, edges: pd.DataFrame, root_event_id: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.5, 6.6), constrained_layout=True)
    _draw_time_vehicle_graph(ax, events, edges, label_nodes=True, root_event_id=root_event_id)
    root = events.loc[events["event_id"] == root_event_id].iloc[0]
    ax.set_title(
        f"Risk chain from {root['event_type']} on {root['vehicle_id']} at t={float(root['time']):.1f}s",
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    _add_event_legend(ax)
    _save(fig, path)


def _draw_time_vehicle_graph(
    ax: plt.Axes,
    events: pd.DataFrame,
    edges: pd.DataFrame,
    label_nodes: bool,
    root_event_id: str | None = None,
) -> None:
    if events.empty:
        ax.text(0.5, 0.5, "No direct propagation edges", ha="center", va="center")
        ax.set_axis_off()
        return

    ordered_vehicles = (
        events.groupby("vehicle_id", as_index=False)["time"].min().sort_values(["time", "vehicle_id"])["vehicle_id"].tolist()
    )
    vehicle_y = {vehicle_id: index for index, vehicle_id in enumerate(ordered_vehicles)}
    positions = {row.event_id: (float(row.time), vehicle_y[row.vehicle_id]) for row in events.itertuples()}

    for edge in edges.itertuples():
        if edge.source_event_id not in positions or edge.target_event_id not in positions:
            continue
        x0, y0 = positions[edge.source_event_id]
        x1, y1 = positions[edge.target_event_id]
        arrow = FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2 + 1.5 * float(edge.propagation_score),
            color="#475569",
            alpha=0.62,
            connectionstyle="arc3,rad=0.08" if y0 == y1 else "arc3,rad=0.0",
        )
        ax.add_patch(arrow)

    label_offsets = [(7, 15), (7, -31), (-73, 15), (-73, -31), (7, 37), (-73, 37)]
    for node_index, row in enumerate(events.itertuples()):
        x, y = positions[row.event_id]
        is_root = row.event_id == root_event_id
        ax.scatter(
            x,
            y,
            s=155 if is_root else 95,
            c=EVENT_COLORS.get(row.event_type, "#64748b"),
            edgecolors="#111827" if is_root else "white",
            linewidths=2.1 if is_root else 0.8,
            zorder=3,
        )
        if label_nodes:
            offset_x, offset_y = label_offsets[node_index % len(label_offsets)]
            ax.annotate(
                f"{row.event_type}\n{row.vehicle_id}\nt={float(row.time):.1f}",
                (x, y),
                xytext=(offset_x, offset_y),
                textcoords="offset points",
                fontsize=7.5,
                color="#1f2937",
                ha="left" if offset_x > 0 else "right",
            )

    ax.set_yticks(range(len(ordered_vehicles)), ordered_vehicles)
    ax.set_xlabel("Simulation time (s)")
    ax.set_ylabel("Vehicle")
    ax.grid(alpha=0.16)
    ax.margins(x=0.08, y=0.28)


def _select_cases(events: pd.DataFrame, edges: pd.DataFrame, roles: pd.DataFrame, max_cases: int) -> list[str]:
    if events.empty or edges.empty or roles.empty:
        return []
    ranked = roles.sort_values(["source_score", "out_strength"], ascending=False)
    chosen: list[str] = []
    used_vehicles: set[str] = set()
    for row in ranked.itertuples():
        if row.event_id not in set(edges["source_event_id"]):
            continue
        if row.vehicle_id in used_vehicles and len(chosen) < max_cases:
            continue
        chosen.append(row.event_id)
        used_vehicles.add(row.vehicle_id)
        if len(chosen) >= max_cases:
            break
    return chosen


def _case_subgraph(
    events: pd.DataFrame,
    edges: pd.DataFrame,
    root_event_id: str,
    max_nodes: int = 12,
    max_depth: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    outgoing = {source_id: group.sort_values(["propagation_score", "delay_s"], ascending=[False, True]) for source_id, group in edges.groupby("source_event_id")}
    selected_ids = {root_event_id}
    queue: deque[tuple[str, int]] = deque([(root_event_id, 0)])
    selected_edges: list[pd.DataFrame] = []
    while queue and len(selected_ids) < max_nodes:
        source_id, depth = queue.popleft()
        if depth >= max_depth or source_id not in outgoing:
            continue
        for edge in outgoing[source_id].itertuples():
            if len(selected_ids) >= max_nodes:
                break
            selected_edges.append(pd.DataFrame([edge._asdict()]))
            if edge.target_event_id not in selected_ids:
                selected_ids.add(edge.target_event_id)
                queue.append((edge.target_event_id, depth + 1))
    case_events = events[events["event_id"].isin(selected_ids)].sort_values(["time", "event_id"]).copy()
    case_edges = pd.concat(selected_edges, ignore_index=True) if selected_edges else edges.iloc[0:0].copy()
    return case_events, case_edges


def _add_event_legend(ax: plt.Axes) -> None:
    handles = [plt.Line2D([0], [0], marker="o", linestyle="", color="w", markerfacecolor=color, markeredgecolor="white", markersize=8, label=name) for name, color in EVENT_COLORS.items()]
    ax.legend(handles=handles, title="Event type", loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
