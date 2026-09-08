import pandas as pd
import pytest
import subprocess
import sys

from riskprop.legacy.regions import (
    MERGE_EDGE_LENGTHS_M,
    assign_topology_region,
    attach_event_regions,
    compare_scale_event_scores,
    summarize_region_risk,
)


def test_assigns_regular_edges_with_topology_boundaries_and_clamps_endpoint():
    first = assign_topology_region("left", 0.0, 25.0)
    second = assign_topology_region("left", 25.0, 25.0)
    endpoint = assign_topology_region("left", 500.0, 25.0)

    assert first == {
        "region_id": "left@0-25",
        "region_start_m": 0.0,
        "region_end_m": 25.0,
    }
    assert second["region_id"] == "left@25-50"
    assert endpoint == {
        "region_id": "left@475-500",
        "region_start_m": 475.0,
        "region_end_m": 500.0,
    }
    assert MERGE_EDGE_LENGTHS_M["bottom"] == 100.0


def test_keeps_internal_edge_as_one_topological_region():
    start = assign_topology_region(":center_1", 0.0, 25.0)
    end = assign_topology_region(":center_1", 23.9, 75.0)

    assert start == end
    assert start == {
        "region_id": ":center_1@internal",
        "region_start_m": 0.0,
        "region_end_m": None,
    }


def test_rejects_unknown_regular_edge_instead_of_guessing_length():
    with pytest.raises(ValueError, match="Unknown merge edge"):
        assign_topology_region("mystery", 3.0, 25.0)


def test_attaches_event_to_emission_by_file_time_and_vehicle():
    events = pd.DataFrame(
        [
            {
                "event_id": "e0",
                "source_file": "run.csv",
                "time": 1.0,
                "vehicle_id": "av_0",
                "risk_score": 0.8,
            }
        ]
    )
    emissions = pd.DataFrame(
        [
            {
                "source_file": "run.csv",
                "time": 1.0,
                "id": "av_0",
                "edge_id": "bottom",
                "relative_position": 61.0,
            }
        ]
    )

    attached = attach_event_regions(events, emissions, nominal_length_m=25.0)

    assert attached.loc[0, "region_id"] == "bottom@50-75"
    assert attached.loc[0, "edge_id"] == "bottom"
    assert attached.loc[0, "relative_position"] == 61.0


def test_region_summary_uses_vehicle_time_exposure():
    emissions = pd.DataFrame(
        [
            {"source_file": "run.csv", "time": 0.0, "id": "v0", "edge_id": "left", "relative_position": 1.0},
            {"source_file": "run.csv", "time": 0.2, "id": "v0", "edge_id": "left", "relative_position": 2.0},
            {"source_file": "run.csv", "time": 0.0, "id": "v1", "edge_id": "bottom", "relative_position": 51.0},
            {"source_file": "run.csv", "time": 0.2, "id": "v1", "edge_id": "bottom", "relative_position": 52.0},
        ]
    )
    events = pd.DataFrame(
        [
            {"event_id": "e0", "source_file": "run.csv", "time": 0.2, "vehicle_id": "v0", "risk_score": 0.5},
            {"event_id": "e1", "source_file": "run.csv", "time": 0.2, "vehicle_id": "v0", "risk_score": 1.0},
        ]
    )

    region_table, attached = summarize_region_risk(events, emissions, 25.0)

    left = region_table.set_index("region_id").loc["left@0-25"]
    bottom = region_table.set_index("region_id").loc["bottom@50-75"]
    assert left["vehicle_time_s"] == pytest.approx(0.4)
    assert left["event_count"] == 2
    assert left["event_rate_per_1000_vehicle_s"] == pytest.approx(5000.0)
    assert bottom["event_count"] == 0
    assert set(attached["event_id"]) == {"e0", "e1"}


def test_scale_comparison_maps_region_rates_back_to_same_events():
    scores_25 = pd.DataFrame(
        [
            {"event_id": "e0", "event_region_rate": 3.0},
            {"event_id": "e1", "event_region_rate": 2.0},
            {"event_id": "e2", "event_region_rate": 1.0},
        ]
    )
    scores_50 = pd.DataFrame(
        [
            {"event_id": "e0", "event_region_rate": 30.0},
            {"event_id": "e1", "event_region_rate": 20.0},
            {"event_id": "e2", "event_region_rate": 10.0},
        ]
    )

    result = compare_scale_event_scores(scores_25, scores_50, top_n=2)

    assert result["shared_event_count"] == 3
    assert result["spearman_event_score"] == pytest.approx(1.0)
    assert result["top_event_jaccard"] == pytest.approx(1.0)


def test_region_scale_pilot_cli_writes_reproducible_tables(tmp_path):
    emission_dir = tmp_path / "emissions"
    output_dir = tmp_path / "output"
    emission_dir.mkdir()
    source_file = "merge_ours_p60_sample-0_emission.csv"
    pd.DataFrame(
        [
            {"time": 0.0, "id": "v0", "edge_id": "left", "relative_position": 1.0, "x": 101.0},
            {"time": 0.2, "id": "v0", "edge_id": "left", "relative_position": 2.0, "x": 102.0},
            {"time": 0.0, "id": "v1", "edge_id": "bottom", "relative_position": 51.0, "x": 551.0},
            {"time": 0.2, "id": "v1", "edge_id": "bottom", "relative_position": 52.0, "x": 552.0},
        ]
    ).to_csv(emission_dir / source_file, index=False)
    events_path = tmp_path / "risk_episodes.csv"
    pd.DataFrame(
        [
            {
                "event_id": "e0",
                "run_id": source_file.removesuffix(".csv"),
                "source_file": source_file,
                "time": 0.2,
                "vehicle_id": "v0",
                "leader_id": "v1",
                "event_type": "low_ttc",
                "risk_score": 1.0,
                "x": 102.0,
                "lane": "left:0",
                "region_id": "left:0_2",
                "scenario": "merge",
                "method": "ours",
                "penetration_pct": 60,
                "is_first_vehicle_row": False,
                "is_last_vehicle_row": False,
            }
        ]
    ).to_csv(events_path, index=False)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/legacy/run_region_scale_pilot.py",
            "--events",
            str(events_path),
            "--emission-dir",
            str(emission_dir),
            "--output-dir",
            str(output_dir),
            "--scales",
            "25",
            "50",
        ],
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (output_dir / "region_summary_L25.csv").exists()
    assert (output_dir / "event_regions_L50.csv").exists()
    assert (output_dir / "scale_comparison.csv").exists()
    assert (output_dir / "distance_quantiles.csv").exists()
    distance_quantiles = pd.read_csv(output_dir / "distance_quantiles.csv")
    assert set(distance_quantiles["scope"]) == {"all_direct", "cross_vehicle"}
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "区域尺度实验.md").exists()
