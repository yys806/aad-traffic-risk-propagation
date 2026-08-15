from pathlib import Path
import subprocess
import sys

import pandas as pd

from riskprop.risk_event_dataset import (
    apply_review_checklist,
    compare_sensitivity_with_drift,
    compute_vehicle_time_seconds,
    discover_formal_emissions,
    extract_formal_event_dataset,
    parse_emission_metadata,
    select_manual_review_sample,
    summarise_event_rates,
    threshold_sensitivity_for_run,
)


def test_parses_formal_emission_metadata():
    metadata = parse_emission_metadata(
        Path("merge_ours_p20_20260511-1629261778488166.3086374-1_emission.csv")
    )

    assert metadata == {
        "scenario": "merge",
        "method": "ours",
        "penetration_pct": 20,
        "run_index": 1,
    }


def test_discovers_only_adopted_drift_and_formal_fs_pi(tmp_path: Path):
    layouts = {
        "penetration_main_formal_v1/emissions": [
            "ring_ours_p20_stamp-0_emission.csv",
            "figure8_ours_p20_stale-0_emission.csv",
            "merge_ours_p20_stale-0_emission.csv",
            "ring_fs_p20_stamp-0_emission.csv",
            "figure8_pi_p20_stamp-0_emission.csv",
        ],
        "ours_f8_adopted_formal_v1/emissions": [
            "figure8_ours_p20_adopted-0_emission.csv"
        ],
        "ours_merge_eta_adopt_formal_v1/emissions": [
            "merge_ours_p20_adopted-0_emission.csv"
        ],
    }
    for directory, names in layouts.items():
        target = tmp_path / directory
        target.mkdir(parents=True)
        for name in names:
            (target / name).touch()

    paths = discover_formal_emissions(tmp_path)

    assert {path.name for path in paths} == {
        "ring_ours_p20_stamp-0_emission.csv",
        "figure8_ours_p20_adopted-0_emission.csv",
        "merge_ours_p20_adopted-0_emission.csv",
        "ring_fs_p20_stamp-0_emission.csv",
        "figure8_pi_p20_stamp-0_emission.csv",
    }


def test_vehicle_time_uses_frame_exposure():
    rows = pd.DataFrame(
        [
            {"time": 0.0, "id": "v0"},
            {"time": 0.0, "id": "v1"},
            {"time": 0.2, "id": "v0"},
            {"time": 0.2, "id": "v1"},
        ]
    )

    assert compute_vehicle_time_seconds(rows) == 0.8


def test_threshold_sensitivity_excludes_override_candidates_from_braking():
    rows = pd.DataFrame(
        [
            {"time": 0.0, "id": "v0", "speed": 10.0, "headway": 3.0, "leader_id": "v1", "leader_rel_speed": -2.0, "realized_accel": -4.0},
            {"time": 0.2, "id": "v0", "speed": 0.0, "headway": 2.0, "leader_id": "v1", "leader_rel_speed": -2.0, "realized_accel": -50.0},
            {"time": 0.0, "id": "v1", "speed": 8.0, "headway": 1000.0, "leader_id": None, "leader_rel_speed": 0.0, "realized_accel": 0.0},
            {"time": 0.2, "id": "v1", "speed": 8.0, "headway": 1000.0, "leader_id": None, "leader_rel_speed": 0.0, "realized_accel": 0.0},
        ]
    )

    result = threshold_sensitivity_for_run(
        rows,
        metadata={"scenario": "merge", "method": "ours", "penetration_pct": 20, "run_index": 0},
        source_file="test.csv",
        ttc_thresholds=(1.0, 1.5, 2.0),
        braking_thresholds=(-3.0, -4.5, -6.0),
    )

    ordinary = result.query("metric == 'ordinary_braking'").set_index("threshold")
    assert int(ordinary.loc[-3.0, "frame_count"]) == 1
    assert int(ordinary.loc[-4.5, "frame_count"]) == 0
    assert int(ordinary.loc[-6.0, "frame_count"]) == 0
    override = result.query("metric == 'safe_speed_override_candidate'")
    assert override["frame_count"].tolist() == [1]
    ttc = result.query("metric == 'ttc_conflict'").set_index("threshold")
    assert int(ttc.loc[1.0, "frame_count"]) == 1
    assert int(ttc.loc[1.5, "frame_count"]) == 2


def test_summarises_episode_rates_with_vehicle_time_denominator():
    by_run = pd.DataFrame(
        [
            {"scenario": "merge", "method": "ours", "penetration_pct": 20, "run_id": "r0", "event_type": "low_ttc", "frame_count": 2, "episode_count": 1, "vehicle_time_s": 10.0, "frame_rate_per_1000_vehicle_s": 200.0, "episode_rate_per_1000_vehicle_s": 100.0},
            {"scenario": "merge", "method": "ours", "penetration_pct": 20, "run_id": "r1", "event_type": "low_ttc", "frame_count": 3, "episode_count": 2, "vehicle_time_s": 20.0, "frame_rate_per_1000_vehicle_s": 150.0, "episode_rate_per_1000_vehicle_s": 100.0},
        ]
    )

    summary = summarise_event_rates(by_run)

    assert int(summary.loc[0, "frame_count"]) == 5
    assert int(summary.loc[0, "episode_count"]) == 3
    assert float(summary.loc[0, "vehicle_time_s"]) == 30.0
    assert float(summary.loc[0, "pooled_episode_rate_per_1000_vehicle_s"]) == 100.0


def test_compares_drift_sensitivity_to_matching_baseline():
    summary = pd.DataFrame(
        [
            {"scenario": "merge", "method": "ours", "penetration_pct": 20, "metric": "ttc_conflict", "threshold": 2.0, "pooled_rate_per_1000_vehicle_s": 3.0},
            {"scenario": "merge", "method": "fs", "penetration_pct": 20, "metric": "ttc_conflict", "threshold": 2.0, "pooled_rate_per_1000_vehicle_s": 5.0},
        ]
    )

    comparison = compare_sensitivity_with_drift(summary)

    assert comparison.loc[0, "baseline"] == "fs"
    assert float(comparison.loc[0, "signed_improvement"]) == 2.0
    assert bool(comparison.loc[0, "drift_better"]) is True


def test_manual_review_sampling_is_deterministic_and_capped():
    events = pd.DataFrame(
        [
            {"event_id": f"e{i}", "event_type": "low_ttc", "risk_score": float(i), "scenario": "merge", "method": "ours", "penetration_pct": 20, "run_id": "r0", "time": float(i), "vehicle_id": f"v{i}"}
            for i in range(15)
        ]
    )

    first = select_manual_review_sample(events, per_event_type=10)
    second = select_manual_review_sample(events, per_event_type=10)

    assert len(first) == 10
    assert first["event_id"].tolist() == second["event_id"].tolist()
    assert first.iloc[0]["event_id"] == "e14"


def test_manual_review_sampling_covers_available_method_strata():
    events = pd.DataFrame(
        [
            {"event_id": "fs0", "event_type": "low_ttc", "risk_score": 1.0, "scenario": "figure8", "method": "fs", "penetration_pct": 20, "run_id": "r0", "time": 1.0, "vehicle_id": "v0"},
            {"event_id": "fs1", "event_type": "low_ttc", "risk_score": 0.9, "scenario": "figure8", "method": "fs", "penetration_pct": 20, "run_id": "r1", "time": 2.0, "vehicle_id": "v1"},
            {"event_id": "ours0", "event_type": "low_ttc", "risk_score": 0.8, "scenario": "merge", "method": "ours", "penetration_pct": 20, "run_id": "r2", "time": 3.0, "vehicle_id": "v2"},
        ]
    )

    sample = select_manual_review_sample(events, per_event_type=2)

    assert set(sample["method"]) == {"fs", "ours"}


def test_full_extraction_script_can_start_from_project_root():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "extract_full_risk_events.py"), "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Extract the formal risk-event dataset" in result.stdout


def test_review_sample_keeps_adjacent_interaction_context(tmp_path: Path):
    path = tmp_path / "merge_ours_p20_stamp-0_emission.csv"
    pd.DataFrame(
        [
            {"time": 0.0, "id": "v0", "speed": 10.0, "headway": 8.0, "leader_id": "v1", "leader_rel_speed": -1.0, "realized_accel": 0.0, "edge_id": "main", "lane_number": 0, "x": 0.0},
            {"time": 0.2, "id": "v0", "speed": 0.0, "headway": 5.0, "leader_id": "v1", "leader_rel_speed": -2.0, "realized_accel": -50.0, "edge_id": "main", "lane_number": 0, "x": 1.0},
            {"time": 0.4, "id": "v0", "speed": 0.2, "headway": 6.0, "leader_id": "v2", "leader_rel_speed": -1.0, "realized_accel": 1.0, "edge_id": "ramp", "lane_number": 1, "x": 2.0},
        ]
    ).to_csv(path, index=False)

    sample = extract_formal_event_dataset([path])["manual_review_sample"]
    row = sample.query("event_type == 'safe_speed_override_candidate'").iloc[0]

    assert float(row["headway"]) == 5.0
    assert float(row["previous_headway_m"]) == 8.0
    assert float(row["next_headway_m"]) == 6.0
    assert row["previous_leader_id"] == "v1"
    assert row["next_leader_id"] == "v2"
    assert row["previous_lane"] == "main:0"
    assert row["next_lane"] == "ramp:1"
    assert float(row["previous_acceleration_mps2"]) == 0.0
    assert float(row["next_acceleration_mps2"]) == 1.0
    assert bool(row["is_first_vehicle_row"]) is False
    assert bool(row["is_last_vehicle_row"]) is False
    assert bool(row["previous_leader_changed"]) is False
    assert bool(row["next_leader_changed"]) is True
    assert bool(row["previous_lane_changed"]) is False
    assert bool(row["next_lane_changed"]) is True
    assert bool(row["adjacent_override_candidate"]) is False


def test_review_checklist_excludes_override_and_flags_interaction_transition():
    sample = pd.DataFrame(
        [
            {"event_type": "safe_speed_override_candidate", "is_first_vehicle_row": False, "is_last_vehicle_row": False, "previous_leader_changed": False, "next_leader_changed": False, "previous_lane_changed": False, "next_lane_changed": False, "adjacent_override_candidate": False},
            {"event_type": "low_ttc", "is_first_vehicle_row": False, "is_last_vehicle_row": False, "previous_leader_changed": True, "next_leader_changed": False, "previous_lane_changed": False, "next_lane_changed": False, "adjacent_override_candidate": True},
            {"event_type": "hard_braking", "is_first_vehicle_row": False, "is_last_vehicle_row": False, "previous_leader_changed": False, "next_leader_changed": False, "previous_lane_changed": False, "next_lane_changed": False, "adjacent_override_candidate": False},
        ]
    )

    reviewed = apply_review_checklist(sample)

    assert reviewed["review_status"].tolist() == ["excluded", "retained_flagged", "retained"]
    assert "override_candidate" in reviewed.loc[0, "review_notes"]
    assert "leader_transition" in reviewed.loc[1, "review_notes"]
    assert "adjacent_override" in reviewed.loc[1, "review_notes"]
