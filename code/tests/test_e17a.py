from __future__ import annotations

import pandas as pd

from pathlib import Path
import json

from riskprop.e17a import (
    deterministic_state_sample,
    evaluate_simulation_coverage,
    write_real_reference_package,
)


def test_e17_gate_compares_sim_real_to_real_real_and_category_support() -> None:
    real_a = pd.DataFrame(
        {
            "speed_mps": [5.0, 10.0, 15.0, 20.0],
            "net_gap_m": [4.0, 8.0, 12.0, 16.0],
            "stratum": ["ordinary", "ordinary", "rear_end", "hard_brake"],
        }
    )
    real_b = pd.DataFrame(
        {
            "speed_mps": [5.2, 9.8, 15.1, 19.9],
            "net_gap_m": [4.2, 8.1, 11.8, 16.1],
            "stratum": ["ordinary", "ordinary", "rear_end", "hard_brake"],
        }
    )
    simulation = pd.concat([real_a, real_b], ignore_index=True)
    result = evaluate_simulation_coverage(
        real_groups={"a": real_a, "b": real_b},
        simulation=simulation,
        continuous_columns=["speed_mps", "net_gap_m"],
        stratum_column="stratum",
        minimum_stratum_coverage=0.90,
        real_real_quantile=0.95,
    )
    assert result["distance_pass"] is True
    assert result["strata_pass"] is True
    assert result["gate_status"] == "pass"


def test_e17_gate_rejects_unrealistic_simulation_or_missing_strata() -> None:
    real_a = pd.DataFrame(
        {"speed_mps": [5.0, 10.0], "net_gap_m": [4.0, 8.0], "stratum": ["a", "b"]}
    )
    real_b = pd.DataFrame(
        {"speed_mps": [5.1, 9.9], "net_gap_m": [4.1, 8.1], "stratum": ["a", "b"]}
    )
    simulation = pd.DataFrame(
        {"speed_mps": [100.0, 110.0], "net_gap_m": [100.0, 110.0], "stratum": ["a", "a"]}
    )
    result = evaluate_simulation_coverage(
        real_groups={"a": real_a, "b": real_b},
        simulation=simulation,
        continuous_columns=["speed_mps", "net_gap_m"],
        stratum_column="stratum",
    )
    assert result["gate_status"] == "fail"
    assert result["distance_pass"] is False
    assert result["strata_pass"] is False


def test_deterministic_state_sample_is_bounded_and_reproducible() -> None:
    frame = pd.DataFrame(
        {
            "dataset": "d",
            "site": "s",
            "window_id": "w",
            "vehicle_id": [f"v{i % 5}" for i in range(100)],
            "time_s": [i / 10 for i in range(100)],
            "speed_mps": range(100),
        }
    )
    first = deterministic_state_sample(frame, max_rows=20, seed=7)
    second = deterministic_state_sample(frame, max_rows=20, seed=7)
    assert len(first) == 20
    assert first.equals(second)
    assert first["sample_key_hash64"].is_monotonic_increasing


def test_real_reference_package_keeps_pneuma_risk_pending(tmp_path: Path) -> None:
    ngsim_state = pd.DataFrame(
        {
            "dataset": ["NGSIM"] * 4,
            "site": ["US-101"] * 4,
            "window_id": ["w"] * 4,
            "vehicle_id": ["1", "1", "2", "2"],
            "time_s": [0.0, 0.1, 0.0, 0.1],
            "speed_mps": [10.0, 11.0, 8.0, 8.5],
            "acceleration_mps2": [0.0, 1.0, 0.0, 0.5],
            "net_gap_m": [10.0, 9.0, 12.0, 11.0],
            "closing_speed_mps": [1.0, 1.0, 0.5, 0.5],
            "measurement_status": ["valid"] * 4,
        }
    )
    ngsim_path = tmp_path / "ngsim.parquet"
    ngsim_state.to_parquet(ngsim_path, index=False)
    pneuma = pd.DataFrame(
        {
            "id": ["p1", "p1"],
            "time_s": [0.0, 0.04],
            "speed_mps": [5.0, 5.1],
            "longitudinal_accel_mps2": [0.0, 0.1],
            "map_match_status": ["candidate", "heading_unobservable"],
        }
    )
    pneuma_path = tmp_path / "pneuma.parquet"
    pneuma.to_parquet(pneuma_path, index=False)
    events = pd.DataFrame(
        {
            "dataset": ["NGSIM"],
            "site": ["US-101"],
            "window_id": ["w"],
            "event_duration_s": [0.2],
            "ttc_min_s": [1.0],
            "drac_max_mps2": [2.0],
            "conflict_type": ["rear_end"],
        }
    )
    events_path = tmp_path / "events.parquet"
    events.to_parquet(events_path, index=False)
    output = write_real_reference_package(
        ngsim_state_paths=[ngsim_path],
        pneuma_state_path=pneuma_path,
        ngsim_event_path=events_path,
        output_dir=tmp_path / "reference",
        max_rows_per_group=10,
        seed=7,
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["gate_status"] == "pending_pneuma_manual_and_simulation_sample"
    assert audit["pneuma_ttc_included"] is False
    assert (output / "kinematics_reference.parquet").is_file()
    assert (output / "following_reference.parquet").is_file()
    assert (output / "risk_event_reference.parquet").is_file()
