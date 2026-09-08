from pathlib import Path

import pandas as pd
from PIL import Image, ImageStat

from riskprop.legacy.local_propagation_baseline import build_local_propagation_baseline
from riskprop.legacy.local_propagation_visuals import create_local_baseline_visual_package


def _episodes() -> pd.DataFrame:
    rows = []
    for scenario_index, scenario in enumerate(["ring", "figure8", "merge"]):
        for method_index, method in enumerate(["ours", "fs", "pi"]):
            run_id = f"{scenario}_{method}_p20_r0"
            for event_index in range(5):
                rows.append(
                    {
                        "event_id": f"{run_id}_e{event_index}",
                        "run_id": run_id,
                        "time": float(event_index),
                        "vehicle_id": f"v{event_index}",
                        "leader_id": f"v{event_index - 1}" if event_index else "lead",
                        "x": float(50 - event_index * 5),
                        "headway": 5.0,
                        "lane": "main:0",
                        "region_id": "main:0_0",
                        "event_type": ["hard_braking", "low_ttc", "low_thw"][event_index % 3],
                        "event_severity": "low",
                        "risk_score": 0.6 + event_index * 0.08,
                        "is_first_vehicle_row": False,
                        "is_last_vehicle_row": False,
                        "previous_leader_changed": event_index == 2,
                        "next_leader_changed": False,
                        "previous_lane_changed": False,
                        "next_lane_changed": False,
                        "adjacent_override_candidate": event_index == 3,
                        "scenario": scenario,
                        "method": method,
                        "penetration_pct": 20,
                    }
                )
    return pd.DataFrame(rows)


def test_creates_ten_nonblank_local_baseline_figures(tmp_path: Path):
    episodes = _episodes()
    manifest = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "scenario": group.iloc[0]["scenario"],
                "method": group.iloc[0]["method"],
                "penetration_pct": 20,
                "vehicle_time_s": 1000.0,
            }
            for run_id, group in episodes.groupby("run_id")
        ]
    )
    tables = build_local_propagation_baseline(
        episodes, manifest, n_permutations=5, seed=4
    )

    catalog = create_local_baseline_visual_package(tables, tmp_path / "figures")

    expected = {
        "01_graph_coverage.png",
        "02_relation_composition.png",
        "03_edge_rate_by_penetration.png",
        "04_depth_heatmap.png",
        "05_multihop_share.png",
        "06_delay_distance_distribution.png",
        "07_context_strata.png",
        "08_permutation_null.png",
        "09_threshold_sensitivity.png",
        "10_representative_chains.png",
    }
    assert expected == set(catalog["filename"])
    assert (tmp_path / "figures" / "figure_catalog.csv").exists()
    for filename in expected:
        path = tmp_path / "figures" / filename
        assert path.stat().st_size > 10_000
        with Image.open(path) as image:
            assert image.width >= 900
            assert image.height >= 500
            assert ImageStat.Stat(image.convert("L")).var[0] > 1.0
