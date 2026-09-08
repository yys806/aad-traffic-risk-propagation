from pathlib import Path
import subprocess
import sys

import pandas as pd

from riskprop.legacy.events import coalesce_risk_events, extract_risk_events
from riskprop.legacy.feasibility_data import generate_merge_feasibility_emissions
from riskprop.legacy.pipeline import run_pipeline
from riskprop.legacy.propagation import (
    build_propagation_edges,
    rank_intervention_candidates,
    score_event_roles,
    select_direct_propagation_edges,
)


def test_extracts_core_risk_events_from_emission_rows():
    rows = pd.DataFrame(
        [
            {"run_id": "r1", "time": 0.0, "id": "veh_0", "speed": 12.0, "realized_accel": -4.2, "headway": 8.0, "leader_id": "veh_1", "leader_rel_speed": -3.0, "x": 10.0, "lane": "main"},
            {"run_id": "r1", "time": 0.5, "id": "veh_0", "speed": 11.0, "realized_accel": -1.0, "headway": 9.0, "leader_id": "veh_1", "leader_rel_speed": -1.0, "x": 14.0, "lane": "main"},
            {"run_id": "r1", "time": 0.5, "id": "veh_2", "speed": 10.0, "realized_accel": -0.2, "headway": 8.0, "leader_id": "veh_0", "leader_rel_speed": -5.0, "x": 3.0, "lane": "main"},
            {"run_id": "r1", "time": 1.0, "id": "veh_2", "speed": 6.0, "realized_accel": -6.5, "headway": 0.8, "leader_id": "veh_0", "leader_rel_speed": -5.0, "x": 5.0, "lane": "main"},
        ]
    )

    events = extract_risk_events(rows)

    event_types = set(events["event_type"])
    assert "hard_braking" in event_types
    assert "severe_braking" not in event_types
    assert "low_ttc" in event_types
    assert "low_thw" in event_types
    assert "near_miss" in event_types
    severe = events.query("vehicle_id == 'veh_2' and event_type == 'hard_braking'")
    assert severe["event_severity"].tolist() == ["severe"]
    assert float(severe.iloc[0]["headway"]) == 0.8
    assert events["event_id"].is_unique


def test_separates_extreme_speed_jump_from_ordinary_braking():
    rows = pd.DataFrame(
        [
            {
                "run_id": "r1",
                "time": 0.2,
                "id": "veh_0",
                "speed": 0.0,
                "realized_accel": -50.0,
                "headway": 5.0,
                "leader_id": "veh_1",
                "leader_rel_speed": -2.0,
                "x": 1.0,
                "lane": "main",
            }
        ]
    )

    events = extract_risk_events(rows)

    braking = events.loc[
        events["event_type"].isin(
            ["hard_braking", "severe_braking", "safe_speed_override_candidate"]
        )
    ]
    assert len(braking) == 1
    assert braking.iloc[0]["event_type"] == "safe_speed_override_candidate"
    assert braking.iloc[0]["event_severity"] == "extreme"


def test_override_candidate_does_not_create_combined_near_miss_label():
    rows = pd.DataFrame(
        [
            {
                "run_id": "r1",
                "time": 0.2,
                "id": "veh_0",
                "speed": 5.0,
                "realized_accel": -50.0,
                "headway": 1.0,
                "leader_id": "veh_1",
                "leader_rel_speed": -2.0,
                "x": 1.0,
                "lane": "main",
            }
        ]
    )

    events = extract_risk_events(rows)

    assert "safe_speed_override_candidate" in set(events["event_type"])
    assert "near_miss" not in set(events["event_type"])


def test_does_not_create_thw_risk_without_valid_positive_headway():
    rows = pd.DataFrame(
        [
            {
                "run_id": "r1",
                "time": 0.0,
                "id": "veh_0",
                "speed": 10.0,
                "realized_accel": 0.0,
                "headway": 0.05,
                "leader_id": None,
                "leader_rel_speed": 0.0,
                "x": 0.0,
                "lane": "main",
            },
            {
                "run_id": "r1",
                "time": 0.0,
                "id": "veh_1",
                "speed": 10.0,
                "realized_accel": 0.0,
                "headway": -1.0,
                "leader_id": "veh_2",
                "leader_rel_speed": 0.0,
                "x": 1.0,
                "lane": "main",
            },
        ]
    )

    events = extract_risk_events(rows)

    assert events.empty


def test_does_not_create_ttc_risk_without_a_leader():
    rows = pd.DataFrame(
        [
            {
                "run_id": "r1",
                "time": 0.0,
                "id": "veh_0",
                "speed": 0.0,
                "realized_accel": 0.0,
                "headway": 10000.0,
                "leader_id": None,
                "leader_rel_speed": -10010.0,
                "x": 0.0,
                "edge_id": "inflow_highway",
                "lane_number": 0,
            }
        ]
    )

    events = extract_risk_events(rows)

    assert events.empty


def test_builds_lane_identifier_from_flow_edge_and_lane_number():
    rows = pd.DataFrame(
        [
            {
                "run_id": "r1",
                "time": 0.0,
                "id": "veh_0",
                "speed": 10.0,
                "realized_accel": -4.0,
                "headway": 8.0,
                "leader_id": "veh_1",
                "leader_rel_speed": -3.0,
                "x": 0.0,
                "edge_id": "inflow_highway",
                "lane_number": 1,
            }
        ]
    )

    events = extract_risk_events(rows)

    assert set(events["lane"]) == {"inflow_highway:1"}


def test_coalesces_consecutive_frame_events_into_risk_episodes():
    raw_events = pd.DataFrame(
        [
            {"event_id": "e0", "run_id": "r1", "time": 0.0, "vehicle_id": "veh_0", "event_type": "low_ttc", "risk_score": 0.7, "x": 10.0, "lane": "main", "region_id": "main_0"},
            {"event_id": "e1", "run_id": "r1", "time": 0.2, "vehicle_id": "veh_0", "event_type": "low_ttc", "risk_score": 0.9, "x": 11.0, "lane": "main", "region_id": "main_0"},
            {"event_id": "e2", "run_id": "r1", "time": 1.0, "vehicle_id": "veh_0", "event_type": "low_ttc", "risk_score": 0.8, "x": 14.0, "lane": "main", "region_id": "main_0"},
        ]
    )

    episodes = coalesce_risk_events(raw_events, max_gap_s=0.4)

    assert len(episodes) == 2
    assert int(episodes.loc[0, "raw_event_count"]) == 2
    assert float(episodes.loc[0, "risk_score"]) == 0.9


def test_episode_keeps_peak_braking_severity():
    raw_events = pd.DataFrame(
        [
            {"event_id": "e0", "run_id": "r1", "time": 0.0, "vehicle_id": "veh_0", "event_type": "hard_braking", "event_severity": "hard", "risk_score": 0.5, "acceleration": -3.2, "next_time_s": 0.2, "next_speed_mps": 9.0, "adjacent_override_candidate": False},
            {"event_id": "e1", "run_id": "r1", "time": 0.2, "vehicle_id": "veh_0", "event_type": "hard_braking", "event_severity": "severe", "risk_score": 0.8, "acceleration": -7.0, "next_time_s": 0.4, "next_speed_mps": 8.0, "adjacent_override_candidate": True},
        ]
    )

    episodes = coalesce_risk_events(raw_events)

    assert episodes.loc[0, "event_severity"] == "severe"
    assert float(episodes.loc[0, "peak_acceleration_mps2"]) == -7.0
    assert float(episodes.loc[0, "next_time_s"]) == 0.4
    assert float(episodes.loc[0, "next_speed_mps"]) == 8.0
    assert bool(episodes.loc[0, "adjacent_override_candidate"]) is True


def test_builds_time_ordered_interaction_edges_between_events():
    events = pd.DataFrame(
        [
            {"event_id": "e0", "run_id": "r1", "time": 0.0, "vehicle_id": "veh_0", "leader_id": "veh_1", "event_type": "hard_braking", "risk_score": 0.7, "x": 10.0, "lane": "main", "region_id": "main_0"},
            {"event_id": "e1", "run_id": "r1", "time": 1.0, "vehicle_id": "veh_2", "leader_id": "veh_0", "event_type": "low_ttc", "risk_score": 0.8, "x": 6.0, "lane": "main", "region_id": "main_0"},
            {"event_id": "e2", "run_id": "r1", "time": 8.0, "vehicle_id": "veh_9", "leader_id": "veh_8", "event_type": "low_thw", "risk_score": 0.4, "x": 200.0, "lane": "main", "region_id": "main_4"},
        ]
    )

    edges = build_propagation_edges(events, max_delay_s=5.0, max_distance_m=50.0)

    assert len(edges) == 1
    edge = edges.iloc[0]
    assert edge["source_event_id"] == "e0"
    assert edge["target_event_id"] == "e1"
    assert edge["edge_type"] == "leader_follower"
    assert edge["delay_s"] == 1.0


def test_selects_only_the_strongest_direct_successor_per_relation():
    candidates = pd.DataFrame(
        [
            {"source_event_id": "e0", "target_event_id": "e1", "run_id": "r1", "edge_type": "same_region", "delay_s": 0.5, "distance_m": 10.0, "propagation_score": 0.4},
            {"source_event_id": "e0", "target_event_id": "e2", "run_id": "r1", "edge_type": "same_region", "delay_s": 0.8, "distance_m": 12.0, "propagation_score": 0.7},
            {"source_event_id": "e0", "target_event_id": "e3", "run_id": "r1", "edge_type": "leader_follower", "delay_s": 1.0, "distance_m": 8.0, "propagation_score": 0.6},
        ]
    )

    direct = select_direct_propagation_edges(candidates, max_targets_per_relation=1)

    assert set(direct["target_event_id"]) == {"e2", "e3"}
    assert direct["is_direct_edge"].all()


def test_drops_long_range_edges_when_lane_information_is_unknown():
    candidates = pd.DataFrame(
        [
            {"source_event_id": "e0", "target_event_id": "e1", "run_id": "r1", "edge_type": "long_range_same_lane", "delay_s": 1.0, "distance_m": 100.0, "source_region_id": "unknown_1", "target_region_id": "unknown_3", "propagation_score": 0.8},
            {"source_event_id": "e0", "target_event_id": "e2", "run_id": "r1", "edge_type": "long_range_same_lane", "delay_s": 1.1, "distance_m": 105.0, "source_region_id": "main_1", "target_region_id": "main_3", "propagation_score": 0.7},
        ]
    )

    direct = select_direct_propagation_edges(candidates, max_targets_per_relation=1)

    assert direct["target_event_id"].tolist() == ["e2"]


def test_scores_event_roles_from_direct_edges():
    events = pd.DataFrame(
        [
            {"event_id": "e0", "run_id": "r1", "vehicle_id": "veh_0", "event_type": "hard_braking", "risk_score": 0.7},
            {"event_id": "e1", "run_id": "r1", "vehicle_id": "veh_1", "event_type": "low_ttc", "risk_score": 0.9},
            {"event_id": "e2", "run_id": "r1", "vehicle_id": "veh_2", "event_type": "low_thw", "risk_score": 0.6},
        ]
    )
    edges = pd.DataFrame(
        [
            {"source_event_id": "e0", "target_event_id": "e1", "run_id": "r1", "propagation_score": 0.8},
            {"source_event_id": "e1", "target_event_id": "e2", "run_id": "r1", "propagation_score": 0.7},
        ]
    )

    roles = score_event_roles(events, edges)

    assert {"source_score", "amplifier_score", "absorber_score"}.issubset(roles.columns)
    assert float(roles.loc[roles["event_id"] == "e0", "source_score"].iloc[0]) > 0.0
    assert float(roles.loc[roles["event_id"] == "e1", "amplifier_score"].iloc[0]) > 0.0


def test_ranks_intervention_candidates_by_reachable_downstream_events():
    events = pd.DataFrame(
        [
            {"event_id": "e0", "run_id": "r1", "vehicle_id": "veh_0", "event_type": "hard_braking", "risk_score": 0.8},
            {"event_id": "e1", "run_id": "r1", "vehicle_id": "veh_1", "event_type": "low_ttc", "risk_score": 0.9},
            {"event_id": "e2", "run_id": "r1", "vehicle_id": "veh_2", "event_type": "low_thw", "risk_score": 0.6},
        ]
    )
    edges = pd.DataFrame(
        [
            {"source_event_id": "e0", "target_event_id": "e1", "run_id": "r1", "propagation_score": 0.8},
            {"source_event_id": "e1", "target_event_id": "e2", "run_id": "r1", "propagation_score": 0.7},
        ]
    )
    roles = score_event_roles(events, edges)

    ranked = rank_intervention_candidates(events, edges, roles, max_depth=3)

    top = ranked.iloc[0]
    assert top["event_id"] == "e0"
    assert int(top["reachable_event_count"]) == 2


def test_pipeline_writes_events_edges_and_summary(tmp_path: Path):
    input_csv = tmp_path / "emissions.csv"
    output_dir = tmp_path / "out"
    pd.DataFrame(
        [
            {"run_id": "r1", "time": 0.0, "id": "veh_0", "speed": 12.0, "realized_accel": -4.2, "headway": 8.0, "leader_id": "veh_1", "leader_rel_speed": -3.0, "x": 10.0, "lane": "main"},
            {"run_id": "r1", "time": 1.0, "id": "veh_2", "speed": 6.0, "realized_accel": -6.5, "headway": 0.8, "leader_id": "veh_0", "leader_rel_speed": -5.0, "x": 5.0, "lane": "main"},
        ]
    ).to_csv(input_csv, index=False)

    outputs = run_pipeline(input_csv=input_csv, output_dir=output_dir)

    assert outputs.events_csv.exists()
    assert outputs.episodes_csv.exists()
    assert outputs.candidate_edges_csv.exists()
    assert outputs.edges_csv.exists()
    assert outputs.roles_csv.exists()
    assert outputs.summary_csv.exists()
    summary = pd.read_csv(outputs.summary_csv)
    assert int(summary.loc[0, "event_count"]) >= 4
    assert int(summary.loc[0, "edge_count"]) >= 1


def test_runner_script_executes_pipeline(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[2]
    input_csv = project_root / "examples" / "sample_emissions.csv"
    output_dir = tmp_path / "script_out"

    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "legacy" / "run_pipeline.py"), "--input", str(input_csv), "--output", str(output_dir)],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (output_dir / "risk_events.csv").exists()
    assert (output_dir / "risk_edges.csv").exists()
    assert (output_dir / "risk_summary.csv").exists()


def test_feasibility_generator_creates_non_empty_merge_risk_case(tmp_path: Path):
    emission_csv = tmp_path / "merge_feasibility_emissions.csv"
    generate_merge_feasibility_emissions(emission_csv)

    emissions = pd.read_csv(emission_csv)
    required = {"run_id", "time", "id", "speed", "realized_accel", "headway", "leader_id", "leader_rel_speed", "x", "lane"}
    assert required.issubset(emissions.columns)

    outputs = run_pipeline(input_csv=emission_csv, output_dir=tmp_path / "risk_outputs")
    events = pd.read_csv(outputs.events_csv)
    edges = pd.read_csv(outputs.edges_csv)

    assert events["event_type"].nunique() >= 3
    assert len(edges) >= 1
