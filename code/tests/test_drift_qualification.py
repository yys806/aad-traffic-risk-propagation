from pathlib import Path
import subprocess
import sys

import pandas as pd

from riskprop.drift_qualification import (
    audit_formal_coverage,
    audit_pilot_events,
    audit_raw_emission_files,
    build_extreme_deceleration_catalog,
    compare_drift_with_baselines,
    compare_with_confidence_intervals,
    extract_validated_risk_events,
    qualification_decision,
    write_qualification_outputs,
)


def test_audits_complete_scenario_penetration_run_coverage():
    rows = []
    for scenario in ("ring", "merge"):
        for method in ("ours", "fs"):
            for penetration in (0, 100):
                rows.append(
                    {
                        "scenario": scenario,
                        "method": method,
                        "penetration_pct": penetration,
                        "expected": "yes",
                        "has_per_run": "yes",
                        "run_count": 5,
                    }
                )
    coverage = audit_formal_coverage(
        pd.DataFrame(rows),
        scenarios=("ring", "merge"),
        methods=("ours", "fs"),
        penetrations=(0, 100),
        expected_runs=5,
    )

    assert coverage["complete"] is True
    assert coverage["expected_cells"] == 8
    assert coverage["complete_cells"] == 8
    assert coverage["missing_cells"] == []


def test_compares_drift_against_each_baseline_with_metric_direction():
    metrics = pd.DataFrame(
        [
            {"scenario": "ring", "method": "ours", "returns_mean": 25.0, "hard_brake_count_lt_6": 0.0},
            {"scenario": "ring", "method": "fs", "returns_mean": 18.0, "hard_brake_count_lt_6": 80.0},
            {"scenario": "ring", "method": "pi", "returns_mean": 12.0, "hard_brake_count_lt_6": 0.0},
        ]
    )

    comparison = compare_drift_with_baselines(
        metrics,
        metric_directions={"returns_mean": "higher", "hard_brake_count_lt_6": "lower"},
    )

    fs_return = comparison.query("baseline == 'fs' and metric == 'returns_mean'").iloc[0]
    pi_braking = comparison.query("baseline == 'pi' and metric == 'hard_brake_count_lt_6'").iloc[0]
    assert bool(fs_return["drift_better"]) is True
    assert float(fs_return["signed_improvement"]) == 7.0
    assert bool(pi_braking["tie"]) is True


def test_compares_non_overlapping_confidence_intervals():
    stats = pd.DataFrame(
        [
            {"scenario": "ring", "method": "ours", "penetration_pct": 20, "return_mean": 10.0, "return_ci95": 1.0, "hb_mean": 2.0, "hb_ci95": 0.2},
            {"scenario": "ring", "method": "fs", "penetration_pct": 20, "return_mean": 5.0, "return_ci95": 1.0, "hb_mean": 5.0, "hb_ci95": 0.5},
        ]
    )

    comparison = compare_with_confidence_intervals(
        stats,
        metric_specs={
            "return": ("return_mean", "return_ci95", "higher"),
            "hard_brake": ("hb_mean", "hb_ci95", "lower"),
        },
    )

    assert comparison["confidently_better"].all()
    assert not comparison["confidently_worse"].any()


def test_flags_invalid_risk_event_semantics_and_metadata():
    events = pd.DataFrame(
        [
            {"leader_id": None, "lane": "unknown", "ttc": 0.99, "acceleration": 0.0},
            {"leader_id": "veh_0", "lane": "unknown", "ttc": 1.50, "acceleration": -32.0},
            {"leader_id": "veh_1", "lane": "main", "ttc": float("inf"), "acceleration": -1.0},
        ]
    )
    episodes = pd.DataFrame(
        [
            {"event_type": "low_ttc", "episode_duration_s": 12.0},
            {"event_type": "hard_braking", "episode_duration_s": 0.2},
        ]
    )

    audit = audit_pilot_events(events, episodes)

    assert audit["finite_ttc_without_leader_count"] == 1
    assert audit["unknown_lane_rate"] == 2 / 3
    assert audit["extreme_deceleration_count"] == 1
    assert audit["long_low_ttc_episode_count"] == 1
    assert audit["passed"] is False


def test_counts_one_extreme_physical_row_across_overlapping_labels():
    events = pd.DataFrame(
        [
            {
                "run_id": "r1",
                "time": 1.0,
                "vehicle_id": "veh_0",
                "leader_id": "veh_1",
                "lane": "main",
                "ttc": float("inf"),
                "acceleration": -20.0,
                "event_type": "hard_braking",
            },
            {
                "run_id": "r1",
                "time": 1.0,
                "vehicle_id": "veh_0",
                "leader_id": "veh_1",
                "lane": "main",
                "ttc": float("inf"),
                "acceleration": -20.0,
                "event_type": "severe_braking",
            },
        ]
    )

    audit = audit_pilot_events(events, pd.DataFrame())

    assert audit["extreme_deceleration_count"] == 1


def test_blocks_propagation_when_input_semantics_fail():
    decision = qualification_decision(
        coverage_passed=True,
        formal_evidence_passed=True,
        pilot_input_passed=False,
        raw_emissions_available=False,
    )

    assert decision["status"] == "HOLD"
    assert decision["may_start_causal_propagation"] is False
    assert "原始 emission" in decision["next_action"]


def test_requests_tail_review_after_schema_issues_are_fixed():
    decision = qualification_decision(
        coverage_passed=True,
        formal_evidence_passed=True,
        pilot_input_passed=False,
        raw_emissions_available=True,
        pilot_audit={
            "finite_ttc_without_leader_count": 0,
            "unknown_lane_rate": 0.0,
            "extreme_deceleration_count": 15,
            "long_low_ttc_episode_count": 0,
        },
    )

    assert decision["status"] == "HOLD"
    assert "极端减速度" in decision["next_action"]


def test_audits_raw_emissions_with_leader_aware_ttc(tmp_path: Path):
    emission = tmp_path / "merge_ours_p20_run0_emission.csv"
    pd.DataFrame(
        [
            {
                "time": 0.0,
                "id": "veh_0",
                "x": 0.0,
                "y": 0.0,
                "speed": 10.0,
                "headway": 3.0,
                "leader_id": "veh_1",
                "realized_accel": -2.0,
                "edge_id": "main",
                "lane_number": 0,
                "leader_rel_speed": -3.0,
            },
            {
                "time": 0.0,
                "id": "veh_2",
                "x": 10.0,
                "y": 0.0,
                "speed": 0.0,
                "headway": 10000.0,
                "leader_id": None,
                "realized_accel": -20.0,
                "edge_id": "main",
                "lane_number": 1,
                "leader_rel_speed": -10010.0,
            },
        ]
    ).to_csv(emission, index=False)

    audit = audit_raw_emission_files([emission])

    assert audit["required_columns_complete"] is True
    assert audit["file_count"] == 1
    assert audit["row_count"] == 2
    assert audit["lane_metadata_missing_rate"] == 0.0
    assert audit["ttc_valid_count"] == 1
    assert audit["ttc_violation_count"] == 1
    assert audit["extreme_deceleration_count"] == 1


def test_extracts_validated_events_from_multiple_raw_runs(tmp_path: Path):
    paths = []
    for run_index in range(2):
        path = tmp_path / f"merge_ours_p20_run{run_index}_emission.csv"
        pd.DataFrame(
            [
                {
                    "time": 0.0,
                    "id": "veh_0",
                    "speed": 10.0,
                    "headway": 6.0,
                    "leader_id": "veh_1",
                    "realized_accel": -4.0,
                    "edge_id": "main",
                    "lane_number": 0,
                    "leader_rel_speed": -3.0,
                    "x": 0.0,
                },
                {
                    "time": 0.0,
                    "id": "veh_2",
                    "speed": 0.0,
                    "headway": 10000.0,
                    "leader_id": None,
                    "realized_accel": 0.0,
                    "edge_id": "main",
                    "lane_number": 1,
                    "leader_rel_speed": -10010.0,
                    "x": 10.0,
                },
            ]
        ).to_csv(path, index=False)
        paths.append(path)

    events, episodes = extract_validated_risk_events(paths)

    assert events["run_id"].nunique() == 2
    assert events["event_id"].is_unique
    assert set(events["lane"]) == {"main:0"}
    assert not events["leader_id"].isna().any()
    assert len(episodes) == 6


def test_builds_extreme_deceleration_catalog_with_adjacent_frames(tmp_path: Path):
    path = tmp_path / "merge_ours_p20_run0_emission.csv"
    pd.DataFrame(
        [
            {"time": 0.0, "id": "veh_0", "speed": 10.0, "realized_accel": 0.0, "edge_id": "main", "lane_number": 0, "leader_id": "veh_1", "headway": 8.0, "leader_rel_speed": -1.0},
            {"time": 0.2, "id": "veh_0", "speed": 0.0, "realized_accel": -50.0, "edge_id": "main", "lane_number": 0, "leader_id": "veh_1", "headway": 5.0, "leader_rel_speed": -2.0},
            {"time": 0.4, "id": "veh_0", "speed": 0.2, "realized_accel": 1.0, "edge_id": "main", "lane_number": 0, "leader_id": "veh_1", "headway": 5.1, "leader_rel_speed": -1.0},
        ]
    ).to_csv(path, index=False)

    catalog = build_extreme_deceleration_catalog([path])

    assert len(catalog) == 1
    row = catalog.iloc[0]
    assert float(row["observed_dvdt_mps2"]) == -50.0
    assert bool(row["acceleration_matches_speed_jump"]) is True
    assert bool(row["is_last_vehicle_row"]) is False
    assert row["lane"] == "main:0"


def test_writes_machine_readable_and_chinese_report(tmp_path: Path):
    paths = write_qualification_outputs(
        output_dir=tmp_path,
        coverage={"complete": True, "expected_cells": 1, "complete_cells": 1, "missing_cells": []},
        comparison=pd.DataFrame(
            [
                {
                    "scenario": "ring",
                    "baseline": "fs",
                    "metric": "returns_mean",
                    "drift_value": 25.0,
                    "baseline_value": 18.0,
                    "signed_improvement": 7.0,
                    "drift_better": True,
                    "tie": False,
                }
            ]
        ),
        pilot_audit={"passed": False, "finite_ttc_without_leader_count": 1},
        decision={
            "status": "HOLD",
            "may_start_causal_propagation": False,
            "next_action": "回到原始 emission 修复字段语义。",
        },
        extra_summary={
            "candidate_fit": {"single_candidate": 1.228, "fixed_k5": 0.595, "learned_k5": 0.094},
            "raw_emission_audit": {
                "file_count": 90,
                "row_count": 1000,
                "required_columns_complete": True,
                "lane_metadata_missing_rate": 0.0,
                "ttc_violation_rate": 0.01,
                "thw_violation_rate": 0.02,
                "extreme_deceleration_count": 3,
                "minimum_acceleration_mps2": -20.0,
            },
            "raw_emission_audit_by_scenario": {
                "merge": {
                    "file_count": 30,
                    "row_count": 500,
                    "ttc_violation_rate": 0.01,
                    "thw_violation_rate": 0.02,
                    "extreme_deceleration_count": 3,
                    "minimum_acceleration_mps2": -20.0,
                }
            },
            "confidence_interval_summary": {
                "comparison_count": 10,
                "confidently_better_count": 6,
                "confidently_worse_count": 2,
                "overlap_count": 2,
            },
            "formal_evidence_passed": True,
            "validated_merge_p20_run_count": 5,
            "validated_merge_p20_extreme_rows": 3,
            "validated_merge_p20_speed_jump_matches": 3,
            "validated_merge_p20_terminal_extreme_rows": 0,
        },
    )

    assert paths["summary_json"].exists()
    assert paths["comparison_csv"].exists()
    assert paths["report_md"].exists()
    report = paths["report_md"].read_text(encoding="utf-8")
    assert "DRIFT 资格验证报告" in report
    assert "暂缓" in report
    assert "原始 emission 审计" in report
    assert "90" in report
    assert "原始数据按场景" in report
    assert "95% 置信区间" in report
    assert "DRIFT 性能证据" in report
    assert "速度跳变" in report


def test_audit_script_can_start_from_project_root():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "audit_drift_qualification.py"), "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Audit whether DRIFT" in result.stdout
