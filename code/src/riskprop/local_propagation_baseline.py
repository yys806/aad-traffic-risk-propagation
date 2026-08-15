"""Conservative local one-hop and multi-hop propagation baseline."""

from __future__ import annotations

from collections import deque
from concurrent.futures import ProcessPoolExecutor
from math import exp, sqrt
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


MISSING_TEXT = {"", "nan", "none", "null", "unknown"}
RELATION_PRIORITY = {
    "same_vehicle": 4,
    "leader_to_follower": 3,
    "follower_to_leader": 2,
    "same_region_local": 1,
}
RELATION_WEIGHT = {
    "same_vehicle": 1.0,
    "leader_to_follower": 1.0,
    "follower_to_leader": 0.9,
    "same_region_local": 0.65,
}


def prepare_eligible_episodes(episodes: pd.DataFrame) -> pd.DataFrame:
    """Exclude simulator overrides and vehicle boundaries, then label context."""
    if episodes.empty:
        result = episodes.copy()
        result["context_stratum"] = pd.Series(dtype=object)
        return result
    required = {"event_id", "run_id", "time", "vehicle_id", "event_type"}
    missing = sorted(required - set(episodes.columns))
    if missing:
        raise ValueError(f"Episodes missing required columns: {', '.join(missing)}")
    result = episodes.copy()
    override = result["event_type"].astype(str).eq("safe_speed_override_candidate")
    boundary = _bool_column(result, "is_first_vehicle_row") | _bool_column(
        result, "is_last_vehicle_row"
    )
    result = result.loc[~override & ~boundary].copy()
    transition = (
        _bool_column(result, "previous_leader_changed")
        | _bool_column(result, "next_leader_changed")
        | _bool_column(result, "previous_lane_changed")
        | _bool_column(result, "next_lane_changed")
    )
    adjacent = _bool_column(result, "adjacent_override_candidate")
    result["has_interaction_transition"] = transition
    result["has_adjacent_override"] = adjacent
    result["context_stratum"] = np.select(
        [
            transition & adjacent,
            transition,
            adjacent,
        ],
        [
            "transition_and_adjacent_override",
            "interaction_transition_only",
            "adjacent_override_only",
        ],
        default="stable_following",
    )
    result["time"] = pd.to_numeric(result["time"], errors="coerce")
    result = result.dropna(subset=["time"])
    return result.sort_values(["run_id", "time", "event_id"]).reset_index(drop=True)


def build_local_candidate_edges(
    episodes: pd.DataFrame,
    max_delay_s: float = 3.0,
    max_distance_m: float = 50.0,
) -> pd.DataFrame:
    """Build time-directed local candidates using explicit topology relations."""
    if max_delay_s <= 0:
        raise ValueError("max_delay_s must be positive")
    if max_distance_m <= 0:
        raise ValueError("max_distance_m must be positive")
    if episodes.empty:
        return _empty_edges()
    rows: list[dict[str, object]] = []
    for run_id, run in episodes.groupby("run_id", sort=True):
        ordered = run.sort_values(["time", "event_id"]).reset_index(drop=True)
        records = list(ordered.to_dict("records"))
        for source_index, source in enumerate(records):
            source_time = float(source["time"])
            for target in records[source_index + 1 :]:
                delay = float(target["time"]) - source_time
                if delay <= 0:
                    continue
                if delay > max_delay_s:
                    break
                relation = _local_relation(source, target, max_distance_m)
                if relation is None:
                    continue
                edge_type, distance = relation
                score = _local_link_score(
                    source,
                    target,
                    delay_s=delay,
                    distance_m=distance,
                    max_delay_s=max_delay_s,
                    max_distance_m=max_distance_m,
                    edge_type=edge_type,
                )
                rows.append(
                    {
                        "source_event_id": source["event_id"],
                        "target_event_id": target["event_id"],
                        "run_id": run_id,
                        "edge_type": edge_type,
                        "delay_s": delay,
                        "distance_m": distance,
                        "source_vehicle_id": source["vehicle_id"],
                        "target_vehicle_id": target["vehicle_id"],
                        "source_event_type": source.get("event_type", "unknown"),
                        "target_event_type": target.get("event_type", "unknown"),
                        "source_context_stratum": source.get(
                            "context_stratum", "unknown"
                        ),
                        "target_context_stratum": target.get(
                            "context_stratum", "unknown"
                        ),
                        "local_link_score": score,
                        "relation_priority": RELATION_PRIORITY[edge_type],
                        "is_cross_vehicle": source["vehicle_id"]
                        != target["vehicle_id"],
                        "is_direct_edge": False,
                        **_shared_metadata(source),
                    }
                )
    if not rows:
        return _empty_edges()
    return pd.DataFrame(rows).sort_values(
        ["run_id", "source_event_id", "target_event_id"]
    ).reset_index(drop=True)


def select_local_direct_edges(candidate_edges: pd.DataFrame) -> pd.DataFrame:
    """Keep one strongest plausible local predecessor for every target event."""
    if candidate_edges.empty:
        return _empty_edges()
    direct = candidate_edges.sort_values(
        [
            "run_id",
            "target_event_id",
            "local_link_score",
            "relation_priority",
            "delay_s",
            "distance_m",
            "source_event_id",
        ],
        ascending=[True, True, False, False, True, True, True],
    ).copy()
    direct["direct_rank"] = direct.groupby(
        ["run_id", "target_event_id"], sort=False
    ).cumcount() + 1
    direct = direct.loc[direct["direct_rank"] == 1].copy()
    direct["is_direct_edge"] = True
    return direct.reset_index(drop=True)


def traverse_local_chains(
    episodes: pd.DataFrame, direct_edges: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assign roots and hop depths, then summarise every directed component."""
    node_rows: list[dict[str, object]] = []
    chain_rows: list[dict[str, object]] = []
    chain_index = 0
    for run_id, run_events in episodes.groupby("run_id", sort=True):
        run_events = run_events.sort_values(["time", "event_id"]).copy()
        event_info = run_events.set_index("event_id")
        run_edges = (
            direct_edges.loc[direct_edges["run_id"] == run_id].copy()
            if not direct_edges.empty
            else direct_edges.copy()
        )
        incoming = (
            run_edges.set_index("target_event_id").to_dict("index")
            if not run_edges.empty
            else {}
        )
        adjacency = {
            source_id: group.sort_values(["delay_s", "target_event_id"])
            for source_id, group in run_edges.groupby("source_event_id", sort=True)
        }
        target_ids = set(run_edges.get("target_event_id", pd.Series(dtype=str)))
        roots = [event_id for event_id in run_events["event_id"] if event_id not in target_ids]
        visited: set[str] = set()
        for root_event_id in roots:
            chain_id = f"lc{chain_index:06d}"
            chain_index += 1
            queue: deque[tuple[str, int, float, float]] = deque(
                [(root_event_id, 0, 0.0, 0.0)]
            )
            chain_event_ids: list[str] = []
            chain_edge_rows: list[Mapping[str, object]] = []
            while queue:
                event_id, depth, cumulative_distance, cumulative_score = queue.popleft()
                if event_id in visited or event_id not in event_info.index:
                    continue
                visited.add(event_id)
                chain_event_ids.append(event_id)
                event = event_info.loc[event_id]
                parent = incoming.get(event_id, {})
                node_rows.append(
                    {
                        "chain_id": chain_id,
                        "run_id": run_id,
                        "event_id": event_id,
                        "root_event_id": root_event_id,
                        "parent_event_id": parent.get("source_event_id", ""),
                        "incoming_edge_type": parent.get("edge_type", "root"),
                        "hop_depth": depth,
                        "cumulative_distance_m": cumulative_distance,
                        "cumulative_link_score": cumulative_score,
                        "time": float(event["time"]),
                        "vehicle_id": event["vehicle_id"],
                        "event_type": event.get("event_type", "unknown"),
                        "risk_score": float(event.get("risk_score", 0.0)),
                        "context_stratum": event.get("context_stratum", "unknown"),
                        **_shared_metadata(event),
                    }
                )
                for edge in adjacency.get(event_id, []).to_dict("records") if event_id in adjacency else []:
                    chain_edge_rows.append(edge)
                    queue.append(
                        (
                            str(edge["target_event_id"]),
                            depth + 1,
                            cumulative_distance + float(edge["distance_m"]),
                            cumulative_score + float(edge["local_link_score"]),
                        )
                    )
            chain_events = event_info.loc[chain_event_ids]
            root_time = float(event_info.loc[root_event_id, "time"])
            max_time = float(pd.to_numeric(chain_events["time"], errors="coerce").max())
            chain_edges = pd.DataFrame(chain_edge_rows)
            chain_nodes = [row for row in node_rows if row["chain_id"] == chain_id]
            chain_rows.append(
                {
                    "chain_id": chain_id,
                    "run_id": run_id,
                    "root_event_id": root_event_id,
                    "root_vehicle_id": event_info.loc[root_event_id, "vehicle_id"],
                    "root_event_type": event_info.loc[root_event_id].get(
                        "event_type", "unknown"
                    ),
                    "event_count": len(chain_event_ids),
                    "edge_count": len(chain_edge_rows),
                    "max_depth": max((int(row["hop_depth"]) for row in chain_nodes), default=0),
                    "time_span_s": max_time - root_time,
                    "mean_delay_s": float(chain_edges["delay_s"].mean())
                    if not chain_edges.empty
                    else 0.0,
                    "max_path_distance_m": max(
                        (float(row["cumulative_distance_m"]) for row in chain_nodes),
                        default=0.0,
                    ),
                    "cumulative_link_score": float(
                        chain_edges.get("local_link_score", pd.Series(dtype=float)).sum()
                    ),
                    "cross_vehicle_edge_count": int(
                        chain_edges.get("is_cross_vehicle", pd.Series(dtype=bool))
                        .fillna(False)
                        .astype(bool)
                        .sum()
                    ),
                    **_shared_metadata(event_info.loc[root_event_id]),
                }
            )
        for event_id in run_events["event_id"]:
            if event_id in visited:
                continue
            chain_id = f"lc{chain_index:06d}"
            chain_index += 1
            event = event_info.loc[event_id]
            node_rows.append(
                {
                    "chain_id": chain_id,
                    "run_id": run_id,
                    "event_id": event_id,
                    "root_event_id": event_id,
                    "parent_event_id": "",
                    "incoming_edge_type": "root",
                    "hop_depth": 0,
                    "cumulative_distance_m": 0.0,
                    "cumulative_link_score": 0.0,
                    "time": float(event["time"]),
                    "vehicle_id": event["vehicle_id"],
                    "event_type": event.get("event_type", "unknown"),
                    "risk_score": float(event.get("risk_score", 0.0)),
                    "context_stratum": event.get("context_stratum", "unknown"),
                    **_shared_metadata(event),
                }
            )
            chain_rows.append(
                {
                    "chain_id": chain_id,
                    "run_id": run_id,
                    "root_event_id": event_id,
                    "root_vehicle_id": event["vehicle_id"],
                    "root_event_type": event.get("event_type", "unknown"),
                    "event_count": 1,
                    "edge_count": 0,
                    "max_depth": 0,
                    "time_span_s": 0.0,
                    "mean_delay_s": 0.0,
                    "max_path_distance_m": 0.0,
                    "cumulative_link_score": 0.0,
                    "cross_vehicle_edge_count": 0,
                    **_shared_metadata(event),
                }
            )
    return pd.DataFrame(node_rows), pd.DataFrame(chain_rows)


def summarise_local_runs(
    episodes: pd.DataFrame,
    candidate_edges: pd.DataFrame,
    direct_edges: pd.DataFrame,
    chain_nodes: pd.DataFrame,
    chains: pd.DataFrame,
    manifest: pd.DataFrame,
) -> pd.DataFrame:
    """Summarise local graph evidence for every formal run."""
    rows: list[dict[str, object]] = []
    manifest_lookup = (
        manifest.drop_duplicates("run_id").set_index("run_id")
        if not manifest.empty and "run_id" in manifest.columns
        else pd.DataFrame()
    )
    run_ids = sorted(set(episodes.get("run_id", pd.Series(dtype=str))))
    for run_id in run_ids:
        run_events = episodes[episodes["run_id"] == run_id]
        run_candidates = _run_slice(candidate_edges, run_id)
        run_direct = _run_slice(direct_edges, run_id)
        run_chains = _run_slice(chains, run_id)
        meta = (
            manifest_lookup.loc[run_id]
            if not manifest_lookup.empty and run_id in manifest_lookup.index
            else run_events.iloc[0]
        )
        exposure = float(meta.get("vehicle_time_s", 0.0))
        connected_chains = run_chains[run_chains.get("edge_count", 0) > 0]
        multi_hop = connected_chains[connected_chains.get("max_depth", 0) >= 2]
        direct_count = len(run_direct)
        cross_count = int(
            run_direct.get("is_cross_vehicle", pd.Series(dtype=bool))
            .fillna(False)
            .astype(bool)
            .sum()
        )
        rows.append(
            {
                "run_id": run_id,
                "scenario": meta.get("scenario", run_events.iloc[0].get("scenario", "unknown")),
                "method": meta.get("method", run_events.iloc[0].get("method", "unknown")),
                "penetration_pct": int(meta.get("penetration_pct", run_events.iloc[0].get("penetration_pct", 0))),
                "vehicle_time_s": exposure,
                "eligible_event_count": len(run_events),
                "candidate_edge_count": len(run_candidates),
                "direct_edge_count": direct_count,
                "cross_vehicle_edge_count": cross_count,
                "direct_edge_rate_per_1000_vehicle_s": _rate(direct_count, exposure),
                "cross_vehicle_edge_rate_per_1000_vehicle_s": _rate(cross_count, exposure),
                "cross_vehicle_edge_share": cross_count / direct_count if direct_count else 0.0,
                "connected_chain_count": len(connected_chains),
                "multi_hop_chain_count": len(multi_hop),
                "multi_hop_chain_share": len(multi_hop) / len(connected_chains)
                if len(connected_chains)
                else 0.0,
                "max_depth": int(run_chains.get("max_depth", pd.Series([0])).max())
                if not run_chains.empty
                else 0,
                "mean_direct_delay_s": float(run_direct["delay_s"].mean())
                if not run_direct.empty
                else 0.0,
                "mean_direct_distance_m": float(run_direct["distance_m"].mean())
                if not run_direct.empty
                else 0.0,
            }
        )
    return pd.DataFrame(rows)


def summarise_local_cells(run_summary: pd.DataFrame) -> pd.DataFrame:
    """Pool run evidence by scenario, method, and AV penetration."""
    if run_summary.empty:
        return pd.DataFrame()
    keys = ["scenario", "method", "penetration_pct"]
    rows = []
    for key, group in run_summary.groupby(keys, sort=True):
        exposure = float(group["vehicle_time_s"].sum())
        edge_count = int(group["direct_edge_count"].sum())
        cross_count = int(group["cross_vehicle_edge_count"].sum())
        connected = int(group["connected_chain_count"].sum())
        multi = int(group["multi_hop_chain_count"].sum())
        rows.append(
            {
                **dict(zip(keys, key)),
                "run_count": int(group["run_id"].nunique()),
                "vehicle_time_s": exposure,
                "eligible_event_count": int(group["eligible_event_count"].sum()),
                "candidate_edge_count": int(group["candidate_edge_count"].sum()),
                "direct_edge_count": edge_count,
                "cross_vehicle_edge_count": cross_count,
                "direct_edge_rate_per_1000_vehicle_s": _rate(edge_count, exposure),
                "cross_vehicle_edge_rate_per_1000_vehicle_s": _rate(cross_count, exposure),
                "cross_vehicle_edge_share": cross_count / edge_count if edge_count else 0.0,
                "connected_chain_count": connected,
                "multi_hop_chain_count": multi,
                "multi_hop_chain_share": multi / connected if connected else 0.0,
                "max_depth": int(group["max_depth"].max()),
                "run_mean_direct_edge_rate": float(
                    group["direct_edge_rate_per_1000_vehicle_s"].mean()
                ),
                "run_ci95_direct_edge_rate": _ci95(
                    group["direct_edge_rate_per_1000_vehicle_s"]
                ),
            }
        )
    return pd.DataFrame(rows)


def permutation_null_by_run(
    episodes: pd.DataFrame,
    n_permutations: int = 100,
    seed: int = 20260718,
    max_delay_s: float = 3.0,
    max_distance_m: float = 50.0,
    workers: int = 1,
) -> pd.DataFrame:
    """Compare cross-vehicle links with vehicle-wise circular time shifts."""
    if n_permutations < 1:
        raise ValueError("n_permutations must be at least 1")
    if workers < 1:
        raise ValueError("workers must be at least 1")
    groups = [(str(run_id), run.copy()) for run_id, run in episodes.groupby("run_id", sort=True)]
    child_seeds = np.random.SeedSequence(seed).spawn(len(groups))
    tasks = [
        (
            run_id,
            run,
            n_permutations,
            int(child_seed.generate_state(1, dtype=np.uint32)[0]),
            seed,
            max_delay_s,
            max_distance_m,
        )
        for (run_id, run), child_seed in zip(groups, child_seeds)
    ]
    if workers == 1 or len(tasks) <= 1:
        rows = [_permutation_null_one_run(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            rows = list(executor.map(_permutation_null_one_run, tasks))
    return pd.DataFrame(rows).sort_values("run_id").reset_index(drop=True)


def local_threshold_sensitivity(
    episodes: pd.DataFrame,
    time_windows_s: Sequence[float] = (1.0, 2.0, 3.0, 5.0),
    distance_windows_m: Sequence[float] = (25.0, 50.0, 80.0),
) -> pd.DataFrame:
    """Evaluate edge and depth stability over local time-distance settings."""
    rows: list[dict[str, object]] = []
    for run_id, run in episodes.groupby("run_id", sort=True):
        first = run.iloc[0]
        for max_delay_s in time_windows_s:
            for max_distance_m in distance_windows_m:
                candidates = build_local_candidate_edges(
                    run, float(max_delay_s), float(max_distance_m)
                )
                direct = select_local_direct_edges(candidates)
                _, chains = traverse_local_chains(run, direct)
                connected = chains[chains.get("edge_count", 0) > 0]
                multi = connected[connected.get("max_depth", 0) >= 2]
                rows.append(
                    {
                        "run_id": run_id,
                        **_shared_metadata(first),
                        "max_delay_s": float(max_delay_s),
                        "max_distance_m": float(max_distance_m),
                        "candidate_edge_count": len(candidates),
                        "direct_edge_count": len(direct),
                        "cross_vehicle_edge_count": int(
                            direct.get("is_cross_vehicle", pd.Series(dtype=bool))
                            .fillna(False)
                            .astype(bool)
                            .sum()
                        ),
                        "connected_chain_count": len(connected),
                        "multi_hop_chain_count": len(multi),
                        "max_depth": int(chains.get("max_depth", pd.Series([0])).max())
                        if not chains.empty
                        else 0,
                    }
                )
    return pd.DataFrame(rows)


def build_local_propagation_baseline(
    episodes: pd.DataFrame,
    manifest: pd.DataFrame,
    *,
    max_delay_s: float = 3.0,
    max_distance_m: float = 50.0,
    n_permutations: int = 100,
    seed: int = 20260718,
    null_workers: int = 1,
) -> dict[str, pd.DataFrame]:
    """Build all validated local baseline tables from formal event episodes."""
    eligible = prepare_eligible_episodes(episodes)
    candidates = build_local_candidate_edges(eligible, max_delay_s, max_distance_m)
    direct = select_local_direct_edges(candidates)
    nodes, chains = traverse_local_chains(eligible, direct)
    run_summary = summarise_local_runs(
        eligible, candidates, direct, nodes, chains, manifest
    )
    return {
        "eligible_episodes": eligible,
        "candidate_edges": candidates,
        "direct_edges": direct,
        "chain_nodes": nodes,
        "chains": chains,
        "run_summary": run_summary,
        "cell_summary": summarise_local_cells(run_summary),
        "null_summary": permutation_null_by_run(
            eligible,
            n_permutations=n_permutations,
            seed=seed,
            max_delay_s=max_delay_s,
            max_distance_m=max_distance_m,
            workers=null_workers,
        ),
        "sensitivity": local_threshold_sensitivity(eligible),
    }


def _permutation_null_one_run(
    task: tuple[str, pd.DataFrame, int, int, int, float, float]
) -> dict[str, object]:
    run_id, run, n_permutations, child_seed, parent_seed, max_delay_s, max_distance_m = task
    rng = np.random.default_rng(child_seed)
    observed = select_local_direct_edges(
        build_local_candidate_edges(run, max_delay_s, max_distance_m)
    )
    observed_count = int(
        observed.get("is_cross_vehicle", pd.Series(dtype=bool))
        .fillna(False)
        .astype(bool)
        .sum()
    )
    null_counts = []
    times = pd.to_numeric(run["time"], errors="coerce")
    minimum = float(times.min())
    maximum = float(times.max())
    span = maximum - minimum
    for _ in range(n_permutations):
        shifted = run.copy()
        if span > 0:
            for _, indices in shifted.groupby("vehicle_id").groups.items():
                offset = float(rng.uniform(0.0, span))
                original = pd.to_numeric(shifted.loc[indices, "time"], errors="coerce")
                shifted.loc[indices, "time"] = minimum + np.mod(
                    original - minimum + offset, span + 1e-9
                )
        null_direct = select_local_direct_edges(
            build_local_candidate_edges(shifted, max_delay_s, max_distance_m)
        )
        null_counts.append(
            int(
                null_direct.get("is_cross_vehicle", pd.Series(dtype=bool))
                .fillna(False)
                .astype(bool)
                .sum()
            )
        )
    null_array = np.asarray(null_counts, dtype=float)
    mean = float(null_array.mean())
    std = float(null_array.std(ddof=1)) if len(null_array) > 1 else 0.0
    z_score = (observed_count - mean) / std if std > 0 else 0.0
    p_value = float((1 + np.sum(null_array >= observed_count)) / (n_permutations + 1))
    first = run.iloc[0]
    return {
        "run_id": run_id,
        **_shared_metadata(first),
        "observed_cross_vehicle_edges": observed_count,
        "null_mean_cross_vehicle_edges": mean,
        "null_std_cross_vehicle_edges": std,
        "z_score": z_score,
        "empirical_p_value": p_value,
        "permutation_count": n_permutations,
        "seed": parent_seed,
    }


def _local_relation(
    source: Mapping[str, object],
    target: Mapping[str, object],
    max_distance_m: float,
) -> tuple[str, float] | None:
    source_vehicle = _text(source.get("vehicle_id"))
    target_vehicle = _text(target.get("vehicle_id"))
    if source_vehicle == target_vehicle:
        return "same_vehicle", 0.0
    target_leader = _text(target.get("leader_id"))
    if target_leader == source_vehicle:
        distance = _finite_nonnegative(target.get("headway"))
        if distance is not None and distance <= max_distance_m:
            return "leader_to_follower", distance
    source_leader = _text(source.get("leader_id"))
    if source_leader == target_vehicle:
        distance = _finite_nonnegative(source.get("headway"))
        if distance is not None and distance <= max_distance_m:
            return "follower_to_leader", distance
    source_region = _text(source.get("region_id"))
    target_region = _text(target.get("region_id"))
    if (
        source_region not in MISSING_TEXT
        and source_region == target_region
    ):
        source_x = _finite(source.get("x"))
        target_x = _finite(target.get("x"))
        if source_x is not None and target_x is not None:
            distance = abs(target_x - source_x)
            if distance <= max_distance_m:
                return "same_region_local", distance
    return None


def _local_link_score(
    source: Mapping[str, object],
    target: Mapping[str, object],
    *,
    delay_s: float,
    distance_m: float,
    max_delay_s: float,
    max_distance_m: float,
    edge_type: str,
) -> float:
    source_risk = max(float(source.get("risk_score", 0.0)), 0.0)
    target_risk = max(float(target.get("risk_score", 0.0)), 0.0)
    risk_factor = sqrt(source_risk * target_risk)
    time_factor = exp(-delay_s / max_delay_s)
    distance_factor = 1.0 if edge_type == "same_vehicle" else exp(
        -distance_m / max_distance_m
    )
    score = (
        RELATION_WEIGHT[edge_type] * risk_factor * time_factor * distance_factor
    )
    return round(float(np.clip(score, 0.0, 1.0)), 6)


def _shared_metadata(row: Mapping[str, object] | pd.Series) -> dict[str, object]:
    return {
        "scenario": row.get("scenario", "unknown"),
        "method": row.get("method", "unknown"),
        "penetration_pct": int(row.get("penetration_pct", 0)),
    }


def _run_slice(frame: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if frame.empty or "run_id" not in frame.columns:
        return frame.iloc[0:0].copy()
    return frame.loc[frame["run_id"] == run_id].copy()


def _bool_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column].fillna(False).astype(bool)


def _text(value: object) -> str:
    return str(value if value is not None else "").strip().lower()


def _finite(value: object) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(numeric) if pd.notna(numeric) and np.isfinite(numeric) else None


def _finite_nonnegative(value: object) -> float | None:
    numeric = _finite(value)
    return numeric if numeric is not None and numeric >= 0 else None


def _rate(count: int, exposure_s: float) -> float:
    return float(count / exposure_s * 1000.0) if exposure_s > 0 else float("nan")


def _ci95(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) <= 1:
        return 0.0
    return float(1.96 * clean.std(ddof=1) / sqrt(len(clean)))


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
            "source_context_stratum",
            "target_context_stratum",
            "local_link_score",
            "relation_priority",
            "is_cross_vehicle",
            "is_direct_edge",
            "direct_rank",
            "scenario",
            "method",
            "penetration_pct",
        ]
    )
