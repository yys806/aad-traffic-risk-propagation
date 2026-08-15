from pathlib import Path
import subprocess
import sys

import pandas as pd

from riskprop.local_propagation_baseline import (
    build_local_candidate_edges,
    build_local_propagation_baseline,
    local_threshold_sensitivity,
    permutation_null_by_run,
    prepare_eligible_episodes,
    select_local_direct_edges,
    summarise_local_runs,
    traverse_local_chains,
)


def _episodes() -> pd.DataFrame:
    common = {
        "run_id": "run_1",
        "lane": "main:0",
        "region_id": "main:0_0",
        "event_type": "low_ttc",
        "event_severity": "low",
        "risk_score": 0.8,
        "headway": 8.0,
        "is_first_vehicle_row": False,
        "is_last_vehicle_row": False,
        "previous_leader_changed": False,
        "next_leader_changed": False,
        "previous_lane_changed": False,
        "next_lane_changed": False,
        "adjacent_override_candidate": False,
        "scenario": "merge",
        "method": "ours",
        "penetration_pct": 20,
    }
    rows = [
        {**common, "event_id": "e0", "time": 0.0, "vehicle_id": "v0", "leader_id": "v9", "x": 10.0, "risk_score": 0.9},
        {**common, "event_id": "e1", "time": 1.0, "vehicle_id": "v1", "leader_id": "v0", "x": 5.0, "headway": 5.0, "previous_leader_changed": True},
        {**common, "event_id": "e2", "time": 2.0, "vehicle_id": "v2", "leader_id": "v1", "x": 1.0, "headway": 4.0, "adjacent_override_candidate": True},
        {**common, "event_id": "e3", "time": 2.5, "vehicle_id": "v0", "leader_id": "v9", "x": 20.0, "risk_score": 0.7},
        {**common, "event_id": "e4", "time": 1.5, "vehicle_id": "v4", "leader_id": "v8", "x": 25.0, "risk_score": 0.6},
        {**common, "event_id": "e_override", "time": 1.2, "vehicle_id": "v5", "leader_id": "v4", "x": 21.0, "event_type": "safe_speed_override_candidate"},
        {**common, "event_id": "e_boundary", "time": 1.8, "vehicle_id": "v6", "leader_id": "v4", "x": 18.0, "is_first_vehicle_row": True},
    ]
    return pd.DataFrame(rows)


def test_prepares_eligible_episodes_and_mutually_exclusive_context_strata():
    eligible = prepare_eligible_episodes(_episodes())

    assert set(eligible["event_id"]) == {"e0", "e1", "e2", "e3", "e4"}
    strata = eligible.set_index("event_id")["context_stratum"].to_dict()
    assert strata["e0"] == "stable_following"
    assert strata["e1"] == "interaction_transition_only"
    assert strata["e2"] == "adjacent_override_only"


def test_builds_local_edges_with_relation_priority_and_physical_distance():
    eligible = prepare_eligible_episodes(_episodes())

    candidates = build_local_candidate_edges(eligible, max_delay_s=3.0, max_distance_m=50.0)

    edge = candidates.query("source_event_id == 'e0' and target_event_id == 'e1'").iloc[0]
    assert edge["edge_type"] == "leader_to_follower"
    assert float(edge["distance_m"]) == 5.0
    same_vehicle = candidates.query("source_event_id == 'e0' and target_event_id == 'e3'").iloc[0]
    assert same_vehicle["edge_type"] == "same_vehicle"
    assert float(same_vehicle["distance_m"]) == 0.0
    assert (candidates["delay_s"] > 0).all()


def test_direct_edges_keep_one_strongest_parent_per_target():
    candidates = build_local_candidate_edges(
        prepare_eligible_episodes(_episodes()), max_delay_s=3.0, max_distance_m=50.0
    )

    direct = select_local_direct_edges(candidates)

    assert direct.groupby(["run_id", "target_event_id"]).size().max() == 1
    assert direct.set_index("target_event_id").loc["e2", "source_event_id"] == "e1"
    assert direct["is_direct_edge"].all()


def test_traverses_real_multihop_chains_and_assigns_depth():
    events = prepare_eligible_episodes(_episodes())
    candidates = build_local_candidate_edges(events)
    direct = select_local_direct_edges(candidates)

    nodes, chains = traverse_local_chains(events, direct)

    node_depth = nodes.set_index("event_id")["hop_depth"].to_dict()
    assert node_depth["e0"] == 0
    assert node_depth["e1"] == 1
    assert node_depth["e2"] == 2
    chain = chains.loc[chains["root_event_id"] == "e0"].iloc[0]
    assert int(chain["max_depth"]) == 2
    assert int(chain["event_count"]) >= 3


def test_summarises_runs_with_vehicle_time_exposure():
    events = prepare_eligible_episodes(_episodes())
    candidates = build_local_candidate_edges(events)
    direct = select_local_direct_edges(candidates)
    nodes, chains = traverse_local_chains(events, direct)
    manifest = pd.DataFrame(
        [{"run_id": "run_1", "scenario": "merge", "method": "ours", "penetration_pct": 20, "vehicle_time_s": 1000.0}]
    )

    summary = summarise_local_runs(events, candidates, direct, nodes, chains, manifest)

    assert int(summary.loc[0, "eligible_event_count"]) == 5
    assert float(summary.loc[0, "direct_edge_rate_per_1000_vehicle_s"]) == float(summary.loc[0, "direct_edge_count"])
    assert int(summary.loc[0, "max_depth"]) >= 2


def test_permutation_null_is_deterministic_and_reports_empirical_p_value():
    events = prepare_eligible_episodes(_episodes())

    first = permutation_null_by_run(events, n_permutations=12, seed=17)
    second = permutation_null_by_run(events, n_permutations=12, seed=17)

    pd.testing.assert_frame_equal(first, second)
    assert int(first.loc[0, "permutation_count"]) == 12
    assert 0.0 < float(first.loc[0, "empirical_p_value"]) <= 1.0


def test_parallel_permutation_matches_serial_result():
    events = prepare_eligible_episodes(_episodes())

    serial = permutation_null_by_run(events, n_permutations=8, seed=23, workers=1)
    parallel = permutation_null_by_run(events, n_permutations=8, seed=23, workers=2)

    pd.testing.assert_frame_equal(serial, parallel)


def test_threshold_sensitivity_covers_requested_time_distance_grid():
    events = prepare_eligible_episodes(_episodes())

    sensitivity = local_threshold_sensitivity(
        events, time_windows_s=(1.0, 2.0, 3.0, 5.0), distance_windows_m=(25.0, 50.0, 80.0)
    )

    assert len(sensitivity) == 12
    assert set(sensitivity["max_delay_s"]) == {1.0, 2.0, 3.0, 5.0}
    assert set(sensitivity["max_distance_m"]) == {25.0, 50.0, 80.0}
    assert (sensitivity["direct_edge_count"] <= sensitivity["candidate_edge_count"]).all()


def test_builds_complete_baseline_tables():
    manifest = pd.DataFrame(
        [{"run_id": "run_1", "scenario": "merge", "method": "ours", "penetration_pct": 20, "vehicle_time_s": 1000.0}]
    )

    result = build_local_propagation_baseline(
        _episodes(), manifest, n_permutations=5, seed=3
    )

    expected = {
        "eligible_episodes",
        "candidate_edges",
        "direct_edges",
        "chain_nodes",
        "chains",
        "run_summary",
        "cell_summary",
        "null_summary",
        "sensitivity",
    }
    assert expected == set(result)


def test_local_baseline_cli_starts_from_project_root():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "build_local_propagation_baseline.py"), "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Build the formal local propagation baseline" in result.stdout
