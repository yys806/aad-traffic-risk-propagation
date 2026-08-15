from pathlib import Path
import subprocess
import sys

import pandas as pd
from PIL import Image, ImageStat

from riskprop.risk_event_visuals import create_risk_event_visual_package


def _write_visual_inputs(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    methods = ["fs", "ours", "pi"]
    scenarios = ["figure8", "merge", "ring"]
    penetrations = [0, 20, 40]

    manifest_rows = []
    rate_rows = []
    sensitivity_rows = []
    comparison_rows = []
    for scenario_index, scenario in enumerate(scenarios):
        for method_index, method in enumerate(methods):
            for penetration in penetrations:
                manifest_rows.append(
                    {
                        "scenario": scenario,
                        "method": method,
                        "penetration_pct": penetration,
                        "run_id": f"{scenario}_{method}_{penetration}",
                        "source_file": "sample.csv",
                        "row_count": 1000,
                        "vehicle_count": 10,
                        "simulation_step_s": 0.2,
                        "vehicle_time_s": 200.0 + 20 * scenario_index,
                    }
                )
                for event_index, event_type in enumerate(
                    [
                        "hard_braking",
                        "low_ttc",
                        "critical_ttc",
                        "low_thw",
                        "near_miss",
                        "safe_speed_override_candidate",
                    ]
                ):
                    base_rate = 2.0 + scenario_index + event_index
                    method_factor = {"ours": 0.8, "fs": 1.0, "pi": 1.15}[method]
                    rate_rows.append(
                        {
                            "scenario": scenario,
                            "method": method,
                            "penetration_pct": penetration,
                            "event_type": event_type,
                            "run_count": 5,
                            "frame_count": 20,
                            "episode_count": 10,
                            "vehicle_time_s": 1000.0,
                            "pooled_frame_rate_per_1000_vehicle_s": base_rate * 2,
                            "pooled_episode_rate_per_1000_vehicle_s": base_rate * method_factor,
                            "episode_rate_run_mean": base_rate * method_factor,
                            "episode_rate_run_std": 0.4,
                            "episode_rate_run_ci95": 0.35,
                            "frame_rate_run_mean": base_rate * 2,
                            "frame_rate_run_std": 0.8,
                            "frame_rate_run_ci95": 0.7,
                        }
                    )
                for metric, thresholds in {
                    "ttc_conflict": [1.0, 1.5, 2.0, 3.0],
                    "ordinary_braking": [-6.0, -4.5, -3.0],
                    "safe_speed_override_candidate": [-15.0],
                }.items():
                    for threshold in thresholds:
                        value = abs(float(threshold)) * {"ours": 0.8, "fs": 1.0, "pi": 1.2}[method]
                        sensitivity_rows.append(
                            {
                                "scenario": scenario,
                                "method": method,
                                "penetration_pct": penetration,
                                "metric": metric,
                                "threshold": threshold,
                                "run_count": 5,
                                "frame_count": 10,
                                "vehicle_time_s": 1000.0,
                                "pooled_rate_per_1000_vehicle_s": value,
                                "run_rate_mean": value,
                                "run_rate_std": 0.3,
                                "run_rate_ci95": 0.25,
                            }
                        )
                        if method != "ours":
                            comparison_rows.append(
                                {
                                    "scenario": scenario,
                                    "penetration_pct": penetration,
                                    "metric": metric,
                                    "threshold": threshold,
                                    "baseline": method,
                                    "drift_rate_per_1000_vehicle_s": value * 0.8,
                                    "baseline_rate_per_1000_vehicle_s": value,
                                    "signed_improvement": value * 0.2,
                                    "drift_better": True,
                                    "tie": False,
                                }
                            )

    review_rows = []
    event_types = [
        "hard_braking",
        "low_ttc",
        "critical_ttc",
        "low_thw",
        "near_miss",
        "safe_speed_override_candidate",
    ]
    for index, event_type in enumerate(event_types):
        review_rows.append(
            {
                "review_status": "excluded" if "override" in event_type else "retained_flagged",
                "review_notes": "override_candidate" if "override" in event_type else "leader_transition|adjacent_override",
                "event_id": f"e{index}",
                "run_id": "merge_ours_p20_sample",
                "time": 10.0 + index,
                "vehicle_id": f"v{index}",
                "leader_id": "lead",
                "speed": 10.0 - index,
                "acceleration": -3.0 - index,
                "headway": 8.0,
                "ttc": 1.0,
                "thw": 0.8,
                "event_type": event_type,
                "event_severity": "critical",
                "risk_score": 1.0 - index * 0.05,
                "previous_time_s": 9.8 + index,
                "previous_speed_mps": 11.0 - index,
                "previous_acceleration_mps2": -1.0,
                "previous_headway_m": 9.0,
                "next_time_s": 10.2 + index,
                "next_speed_mps": 9.0 - index,
                "next_acceleration_mps2": -2.0,
                "next_headway_m": 7.0,
                "previous_leader_changed": index % 2 == 0,
                "next_leader_changed": False,
                "previous_lane_changed": False,
                "next_lane_changed": index % 3 == 0,
                "adjacent_override_candidate": index % 2 == 0,
                "scenario": "merge",
                "method": "ours",
                "penetration_pct": 20,
                "episode_start_s": 10.0 + index,
                "episode_end_s": 10.0 + index,
                "episode_duration_s": 0.0,
                "peak_acceleration_mps2": -3.0 - index,
            }
        )

    pd.DataFrame(manifest_rows).to_csv(directory / "extraction_manifest.csv", index=False)
    pd.DataFrame(rate_rows).to_csv(directory / "event_rates_summary.csv", index=False)
    pd.DataFrame(sensitivity_rows).to_csv(directory / "threshold_sensitivity_summary.csv", index=False)
    pd.DataFrame(comparison_rows).to_csv(directory / "threshold_sensitivity_comparison.csv", index=False)
    pd.DataFrame(review_rows).to_csv(directory / "manual_review_sample.csv", index=False)


def test_creates_complete_nonblank_visual_package(tmp_path: Path):
    input_dir = tmp_path / "dataset"
    output_dir = tmp_path / "figures"
    _write_visual_inputs(input_dir)

    catalog = create_risk_event_visual_package(input_dir, output_dir)

    expected = {
        "01_data_coverage.png",
        "02_episode_composition.png",
        "03_event_rate_by_penetration.png",
        "04_scenario_method_heatmap.png",
        "05_ttc_threshold_sensitivity.png",
        "06_braking_threshold_sensitivity.png",
        "07_drift_improvement_heatmap.png",
        "08_drift_win_rate.png",
        "09_manual_review_outcomes.png",
        "10_context_flag_composition.png",
        "11_override_rate_by_penetration.png",
        "12_representative_event_context.png",
    }
    assert expected.issubset(set(catalog["filename"]))
    assert (output_dir / "figure_catalog.csv").exists()
    for filename in expected:
        path = output_dir / filename
        assert path.stat().st_size > 10_000
        with Image.open(path) as image:
            assert image.width >= 900
            assert image.height >= 500
            assert ImageStat.Stat(image.convert("L")).var[0] > 1.0


def test_renderer_cli_starts_from_project_root():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "render_risk_event_visuals.py"), "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Render the full risk-event visual package" in result.stdout
