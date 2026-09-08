from __future__ import annotations

import pandas as pd


def build_propagation_edges(
    events: pd.DataFrame,
    max_delay_s: float = 5.0,
    max_distance_m: float = 80.0,
    long_range_distance_m: float = 120.0,
) -> pd.DataFrame:
    """Connect risk events into simple, explainable propagation edges."""
    if events.empty:
        return _empty_edges()

    ordered = events.sort_values(["run_id", "time", "event_id"]).reset_index(drop=True)
    edges: list[dict[str, object]] = []

    for source_index, source in ordered.iterrows():
        candidates = ordered.iloc[source_index + 1 :]
        candidates = candidates[candidates["run_id"] == source["run_id"]]
        candidates = candidates[candidates["time"] > source["time"]]
        candidates = candidates[candidates["time"] - source["time"] <= max_delay_s]

        for _, target in candidates.iterrows():
            relation = _relation(source, target, max_distance_m, long_range_distance_m)
            if relation is None:
                continue
            delay = float(target["time"] - source["time"])
            distance = abs(float(target.get("x", 0.0)) - float(source.get("x", 0.0)))
            score = _edge_score(source, target, delay, distance, max_delay_s, max_distance_m, relation)
            edges.append(
                {
                    "source_event_id": source["event_id"],
                    "target_event_id": target["event_id"],
                    "run_id": source["run_id"],
                    "edge_type": relation,
                    "delay_s": delay,
                    "distance_m": distance,
                    "source_vehicle_id": source["vehicle_id"],
                    "target_vehicle_id": target["vehicle_id"],
                    "source_event_type": source["event_type"],
                    "target_event_type": target["event_type"],
                    "source_region_id": source["region_id"],
                    "target_region_id": target["region_id"],
                    "propagation_score": score,
                    "is_direct_edge": False,
                }
            )

    if not edges:
        return _empty_edges()
    return pd.DataFrame(edges).sort_values(["run_id", "source_event_id", "target_event_id"]).reset_index(drop=True)


def select_direct_propagation_edges(
    candidate_edges: pd.DataFrame,
    max_targets_per_relation: int = 1,
    min_propagation_score: float = 0.0,
) -> pd.DataFrame:
    """Keep a small, readable set of high-confidence direct propagation edges.

    Candidate edges retain every plausible time-space relation. A direct edge is
    the strongest next event for a source event within each relation type. This
    deliberately avoids treating every event in a five-second window as a causal
    successor.
    """
    if candidate_edges.empty:
        return _empty_edges()
    if max_targets_per_relation < 1:
        raise ValueError("max_targets_per_relation must be at least 1")

    direct = candidate_edges.copy()
    direct = direct[direct["propagation_score"] >= min_propagation_score]
    direct = _drop_unverified_long_range_edges(direct)
    direct = direct.sort_values(
        ["run_id", "source_event_id", "edge_type", "propagation_score", "delay_s", "distance_m", "target_event_id"],
        ascending=[True, True, True, False, True, True, True],
    )
    direct["direct_rank"] = direct.groupby(["run_id", "source_event_id", "edge_type"]).cumcount() + 1
    direct = direct[direct["direct_rank"] <= max_targets_per_relation].copy()
    direct["is_direct_edge"] = True
    return direct.reset_index(drop=True)


def score_event_roles(events: pd.DataFrame, direct_edges: pd.DataFrame) -> pd.DataFrame:
    """Create transparent source/amplifier/absorber proxy scores for events."""
    columns = [
        "event_id",
        "run_id",
        "vehicle_id",
        "event_type",
        "risk_score",
        "in_strength",
        "out_strength",
        "risk_gain",
        "source_score",
        "amplifier_score",
        "absorber_score",
    ]
    if events.empty:
        return pd.DataFrame(columns=columns)

    roles = events[[column for column in ["event_id", "run_id", "vehicle_id", "event_type", "risk_score"] if column in events.columns]].copy()
    for column, value in {"run_id": "run_0", "vehicle_id": "", "event_type": "unknown", "risk_score": 0.0}.items():
        if column not in roles.columns:
            roles[column] = value
    roles["risk_score"] = pd.to_numeric(roles["risk_score"], errors="coerce").fillna(0.0)

    if direct_edges.empty:
        roles["in_strength"] = 0.0
        roles["out_strength"] = 0.0
        roles["risk_gain"] = 0.0
        roles["source_score"] = 0.0
        roles["amplifier_score"] = 0.0
        roles["absorber_score"] = 0.0
        return roles[columns]

    weighted_edges = direct_edges.copy()
    weighted_edges["propagation_score"] = pd.to_numeric(weighted_edges["propagation_score"], errors="coerce").fillna(0.0)
    event_risk = roles.set_index("event_id")["risk_score"]
    weighted_edges["source_risk"] = weighted_edges["source_event_id"].map(event_risk).fillna(0.0)
    weighted_edges["target_risk"] = weighted_edges["target_event_id"].map(event_risk).fillna(0.0)
    weighted_edges["positive_risk_gain"] = (weighted_edges["target_risk"] - weighted_edges["source_risk"]).clip(lower=0.0)

    outgoing = weighted_edges.groupby("source_event_id", as_index=False).agg(
        out_strength=("propagation_score", "sum"),
        risk_gain=("positive_risk_gain", "mean"),
    ).rename(columns={"source_event_id": "event_id"})
    incoming = weighted_edges.groupby("target_event_id", as_index=False).agg(
        in_strength=("propagation_score", "sum"),
    ).rename(columns={"target_event_id": "event_id"})
    roles = roles.merge(outgoing, on="event_id", how="left").merge(incoming, on="event_id", how="left")
    for column in ["in_strength", "out_strength", "risk_gain"]:
        roles[column] = roles[column].fillna(0.0)

    roles["source_score"] = _normalise_by_run(roles, "out_strength")
    amplifier_raw = roles[["in_strength", "out_strength"]].min(axis=1) * (1.0 + roles["risk_gain"])
    roles["amplifier_score"] = _normalise_by_run(roles.assign(_amplifier_raw=amplifier_raw), "_amplifier_raw")
    absorber_raw = roles["in_strength"] / (1.0 + roles["out_strength"])
    roles["absorber_score"] = _normalise_by_run(roles.assign(_absorber_raw=absorber_raw), "_absorber_raw")
    return roles[columns].sort_values(["run_id", "source_score", "event_id"], ascending=[True, False, True]).reset_index(drop=True)


def rank_intervention_candidates(
    events: pd.DataFrame,
    direct_edges: pd.DataFrame,
    roles: pd.DataFrame,
    max_depth: int = 3,
) -> pd.DataFrame:
    """Rank graph-level intervention candidates by downstream direct propagation.

    This is a screening score only: it identifies events worth changing in a
    future closed-loop counterfactual rollout. It does not claim a causal effect.
    """
    columns = [
        "run_id",
        "event_id",
        "vehicle_id",
        "event_type",
        "source_score",
        "reachable_event_count",
        "affected_direct_edge_count",
        "downstream_mean_risk",
        "cumulative_propagation_score",
        "intervention_priority",
    ]
    if events.empty or direct_edges.empty or roles.empty:
        return pd.DataFrame(columns=columns)

    event_info = events.set_index("event_id")
    roles_by_event = roles.set_index("event_id")
    rows: list[dict[str, object]] = []
    for run_id, run_edges in direct_edges.groupby("run_id"):
        sort_columns = ["propagation_score"] + (["delay_s"] if "delay_s" in run_edges.columns else [])
        sort_ascending = [False] + ([True] if "delay_s" in run_edges.columns else [])
        adjacency = {
            source_id: group.sort_values(sort_columns, ascending=sort_ascending)
            for source_id, group in run_edges.groupby("source_event_id")
        }
        for event_id in adjacency:
            if event_id not in event_info.index or event_id not in roles_by_event.index:
                continue
            visited = {event_id}
            frontier = [(event_id, 0)]
            selected_edges: list[pd.DataFrame] = []
            while frontier:
                current, depth = frontier.pop(0)
                if depth >= max_depth or current not in adjacency:
                    continue
                group = adjacency[current]
                selected_edges.append(group)
                for target_id in group["target_event_id"].tolist():
                    if target_id not in visited:
                        visited.add(target_id)
                        frontier.append((target_id, depth + 1))
            downstream_ids = [value for value in visited if value != event_id and value in event_info.index]
            selected = pd.concat(selected_edges, ignore_index=True) if selected_edges else run_edges.iloc[0:0]
            downstream_risk = pd.to_numeric(event_info.loc[downstream_ids, "risk_score"], errors="coerce").mean() if downstream_ids else 0.0
            source_score = float(roles_by_event.loc[event_id, "source_score"])
            cumulative_strength = float(pd.to_numeric(selected.get("propagation_score", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
            rows.append(
                {
                    "run_id": run_id,
                    "event_id": event_id,
                    "vehicle_id": str(event_info.loc[event_id, "vehicle_id"]),
                    "event_type": str(event_info.loc[event_id, "event_type"]),
                    "source_score": source_score,
                    "reachable_event_count": int(len(downstream_ids)),
                    "affected_direct_edge_count": int(len(selected)),
                    "downstream_mean_risk": float(downstream_risk) if pd.notna(downstream_risk) else 0.0,
                    "cumulative_propagation_score": cumulative_strength,
                    "intervention_priority": source_score * (1.0 + len(downstream_ids)) * (1.0 + cumulative_strength),
                }
            )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["intervention_priority", "reachable_event_count", "event_id"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def summarise_propagation(
    events: pd.DataFrame,
    edges: pd.DataFrame,
    candidate_edges: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create a small run-level summary for pilot comparisons."""
    run_ids = sorted(set(events.get("run_id", pd.Series(dtype=str))).union(edges.get("run_id", pd.Series(dtype=str))))
    if not run_ids:
        run_ids = ["run_0"]

    rows = []
    for run_id in run_ids:
        run_events = events[events["run_id"] == run_id] if not events.empty else events
        run_edges = edges[edges["run_id"] == run_id] if not edges.empty else edges
        run_candidates = candidate_edges[candidate_edges["run_id"] == run_id] if candidate_edges is not None and not candidate_edges.empty else run_edges
        candidate_count = int(len(run_candidates))
        direct_count = int(len(run_edges))
        rows.append(
            {
                "run_id": run_id,
                "event_count": int(len(run_events)),
                "candidate_edge_count": candidate_count,
                "edge_count": direct_count,
                "edge_selection_rate": float(direct_count / candidate_count) if candidate_count else 0.0,
                "chain_count_proxy": int(run_edges["source_event_id"].nunique()) if not run_edges.empty else 0,
                "mean_delay_s": float(run_edges["delay_s"].mean()) if not run_edges.empty else 0.0,
                "mean_distance_m": float(run_edges["distance_m"].mean()) if not run_edges.empty else 0.0,
                "mean_propagation_score": float(run_edges["propagation_score"].mean()) if not run_edges.empty else 0.0,
                "long_range_trigger_ratio": _long_range_ratio(run_edges),
            }
        )
    return pd.DataFrame(rows)


def _relation(
    source: pd.Series,
    target: pd.Series,
    max_distance_m: float,
    long_range_distance_m: float,
) -> str | None:
    same_vehicle = source["vehicle_id"] == target["vehicle_id"]
    source_follows_target = source.get("leader_id", "") == target["vehicle_id"]
    target_follows_source = target.get("leader_id", "") == source["vehicle_id"]
    same_region = source.get("region_id") == target.get("region_id")
    source_lane = str(source.get("lane", "")).strip().lower()
    target_lane = str(target.get("lane", "")).strip().lower()
    lane_known = source_lane not in {"", "unknown", "nan", "none"} and target_lane not in {"", "unknown", "nan", "none"}
    same_lane = lane_known and source_lane == target_lane
    distance = abs(float(target.get("x", 0.0)) - float(source.get("x", 0.0)))

    if same_vehicle:
        return "same_vehicle"
    if source_follows_target or target_follows_source:
        return "leader_follower"
    if same_region and distance <= max_distance_m:
        return "same_region"
    if same_lane and max_distance_m < distance <= long_range_distance_m:
        return "long_range_same_lane"
    return None


def _edge_score(
    source: pd.Series,
    target: pd.Series,
    delay_s: float,
    distance_m: float,
    max_delay_s: float,
    max_distance_m: float,
    relation: str,
) -> float:
    w_time = max(0.1, 1.0 - delay_s / max_delay_s)
    w_space = max(0.1, 1.0 - min(distance_m, max_distance_m) / max_distance_m)
    w_risk = max(float(source.get("risk_score", 0.0)), float(target.get("risk_score", 0.0)))
    relation_weight = {
        "same_vehicle": 0.9,
        "leader_follower": 1.0,
        "same_region": 0.7,
        "long_range_same_lane": 0.5,
    }.get(relation, 0.5)
    return round(max(0.0, min(w_time * w_space * w_risk * relation_weight, 1.0)), 4)


def _long_range_ratio(edges: pd.DataFrame) -> float:
    if edges.empty:
        return 0.0
    return float(edges["edge_type"].str.contains("long_range").mean())


def _normalise_by_run(frame: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    maxima = values.groupby(frame["run_id"]).transform("max")
    return values.div(maxima.where(maxima > 0, 1.0)).round(4)


def _drop_unverified_long_range_edges(edges: pd.DataFrame) -> pd.DataFrame:
    """Avoid treating missing lane labels as evidence for a same-lane effect."""
    required = {"edge_type", "source_region_id", "target_region_id"}
    if not required.issubset(edges.columns):
        return edges
    long_range = edges["edge_type"].eq("long_range_same_lane")
    verified = edges["source_region_id"].map(_region_lane_known) & edges["target_region_id"].map(_region_lane_known)
    return edges.loc[~long_range | verified].copy()


def _region_lane_known(region_id: object) -> bool:
    lane = str(region_id).rsplit("_", 1)[0].strip().lower()
    return lane not in {"", "unknown", "nan", "none"}


def _empty_edges() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "source_event_id",
            "target_event_id",
            "run_id",
            "edge_type",
            "delay_s",
            "distance_m",
            "source_vehicle_id",
            "target_vehicle_id",
            "source_event_type",
            "target_event_type",
            "source_region_id",
            "target_region_id",
            "propagation_score",
            "is_direct_edge",
            "direct_rank",
        ]
    )
