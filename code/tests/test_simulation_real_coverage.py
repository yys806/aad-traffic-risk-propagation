from __future__ import annotations

import pandas as pd

from pathlib import Path
import json
import pytest

from riskprop.simulation_real_coverage import (
    CANONICAL_PNEUMA_COLUMNS,
    deterministic_state_sample,
    evaluate_simulation_coverage,
    write_real_reference_package,
)
from riskprop.calibration import CalibrationContractError


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


def test_real_reference_package_propagates_pneuma_quality_fields(tmp_path: Path) -> None:
    ngsim_state = pd.DataFrame(
        {
            "dataset": ["NGSIM"] * 2,
            "site": ["US-101"] * 2,
            "window_id": ["w"] * 2,
            "vehicle_id": ["1", "1"],
            "time_s": [0.0, 0.1],
            "speed_mps": [10.0, 11.0],
            "acceleration_mps2": [0.0, 1.0],
            "net_gap_m": [10.0, 9.0],
            "closing_speed_mps": [1.0, 1.0],
            "measurement_status": ["valid", "valid"],
        }
    )
    ngsim_path = tmp_path / "ngsim.parquet"
    ngsim_state.to_parquet(ngsim_path, index=False)
    pneuma = pd.DataFrame(
        {
            "id": ["p1", "p1", "p1"],
            "time_s": [0.0, 0.04, 0.08],
            "speed_mps": [5.0, 5.1, 5.2],
            "longitudinal_accel_mps2": [0.0, 0.1, 0.0],
            "quality_status": ["raw_parsed", "parse_failed", "raw_parsed"],
            "time_weighting_eligible": [True, False, True],
        }
    )
    pneuma_path = tmp_path / "pneuma_quality.parquet"
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
        output_dir=tmp_path / "reference_quality",
        max_rows_per_group=10,
        seed=7,
        pneuma_schema="legacy",
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    pneuma_source = audit["sources"][-1]
    assert pneuma_source["pneuma_quality_semantics"]["pneuma_quality_columns_present"] is True
    assert pneuma_source["pneuma_quality_semantics"]["pneuma_states_total"] == 3
    assert pneuma_source["pneuma_quality_semantics"]["pneuma_states_not_reliably_parsed_excluded"] == 1
    assert pneuma_source["pneuma_quality_semantics"]["pneuma_states_time_weighting_eligible"] == 2
    assert pneuma_source["kinematics_pool_rows"] == 2
    kinematics = pd.read_parquet(output / "kinematics_reference.parquet")
    pneuma_rows = kinematics[kinematics["dataset"] == "pNEUMA"]
    # The parse-failed state never enters the frozen reference; the eligible
    # flag is carried through so later statistics keep the expected weighting.
    assert set(pneuma_rows["time_s"]) == {0.0, 0.08}
    assert set(pneuma_rows["time_weighting_eligible"].astype(bool)) == {True}
    assert "quality_status" in pneuma_rows.columns


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
        pneuma_schema="legacy",
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["gate_status"] == "pending_simulation_sample"
    assert audit["experiment_id"] == "stage_0_5"
    assert audit["pneuma_role"] == "urban_kinematics_only"
    assert audit["pneuma_ttc_included"] is False
    assert (output / "kinematics_reference.parquet").is_file()
    assert (output / "following_reference.parquet").is_file()
    assert (output / "risk_event_reference.parquet").is_file()


def _canonical_pneuma_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dataset": ["pNEUMA", "pNEUMA", "pNEUMA"],
            "site": ["Athens-d1"] * 3,
            "window_id": ["20181101_d1_0800_0830"] * 3,
            "vehicle_id": ["p1", "p1", "p2"],
            "vehicle_type": ["Car", "Car", "Taxi"],
            "time_s": [0.0, 0.04, 0.0],
            "speed_mps": [5.0, 5.1, 4.0],
            "acceleration_mps2": [0.0, 0.1, -0.1],
            "quality_status": ["raw_parsed", "raw_parsed", "raw_parsed"],
            "time_weighting_eligible": [True, False, True],
            "source_file_sha256": ["a" * 64] * 3,
        }
    )


def test_canonical_pneuma_schema_is_consumed_directly_and_preserved(
    tmp_path: Path,
) -> None:
    ngsim_state = pd.DataFrame(
        {
            "dataset": ["NGSIM"] * 2,
            "site": ["US-101"] * 2,
            "window_id": ["w"] * 2,
            "vehicle_id": ["1", "1"],
            "time_s": [0.0, 0.1],
            "speed_mps": [10.0, 11.0],
            "acceleration_mps2": [0.0, 1.0],
            "net_gap_m": [10.0, 9.0],
            "closing_speed_mps": [1.0, 1.0],
            "measurement_status": ["valid", "valid"],
        }
    )
    ngsim_path = tmp_path / "ngsim.parquet"
    ngsim_state.to_parquet(ngsim_path, index=False)
    pneuma_path = tmp_path / "canonical.parquet"
    _canonical_pneuma_fixture().to_parquet(pneuma_path, index=False)
    events_path = tmp_path / "events.parquet"
    pd.DataFrame(
        {
            "event_id": ["e1"],
            "dataset": ["NGSIM"],
            "site": ["US-101"],
            "window_id": ["w"],
            "rule": ["P2_middle"],
        }
    ).to_parquet(events_path, index=False)

    output = write_real_reference_package(
        ngsim_state_paths=[ngsim_path],
        pneuma_state_path=pneuma_path,
        ngsim_event_path=events_path,
        output_dir=tmp_path / "canonical_reference",
        max_rows_per_group=10,
        seed=7,
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["pneuma_schema"] == "canonical"
    assert audit["formal_reference_eligible"] is True
    assert audit["sources"][-1]["pneuma_quality_columns_present"] is True
    reference = pd.read_parquet(output / "kinematics_reference.parquet")
    pneuma_rows = reference[reference["dataset"] == "pNEUMA"]
    assert set(pneuma_rows["vehicle_type"]) == {"Car", "Taxi"}
    assert set(pneuma_rows["source_file_sha256"]) == {"a" * 64}
    assert set(pneuma_rows["vehicle_id"]) == {"p1", "p2"}
    assert set(CANONICAL_PNEUMA_COLUMNS).issubset(
        set(pneuma_rows.columns)
    )


def test_canonical_pneuma_quality_contract_is_fail_closed(tmp_path: Path) -> None:
    ngsim_state = pd.DataFrame(
        {
            "dataset": ["NGSIM"],
            "site": ["US-101"],
            "window_id": ["w"],
            "vehicle_id": ["1"],
            "time_s": [0.0],
            "speed_mps": [10.0],
            "acceleration_mps2": [0.0],
            "net_gap_m": [10.0],
            "closing_speed_mps": [1.0],
            "measurement_status": ["valid"],
        }
    )
    ngsim_path = tmp_path / "ngsim.parquet"
    ngsim_state.to_parquet(ngsim_path, index=False)
    incomplete = _canonical_pneuma_fixture().drop(columns=["time_weighting_eligible"])
    pneuma_path = tmp_path / "incomplete.parquet"
    incomplete.to_parquet(pneuma_path, index=False)
    events_path = tmp_path / "events.parquet"
    pd.DataFrame({"event_id": ["e1"]}).to_parquet(events_path, index=False)

    with pytest.raises(CalibrationContractError, match="time_weighting_eligible"):
        write_real_reference_package(
            ngsim_state_paths=[ngsim_path],
            pneuma_state_path=pneuma_path,
            ngsim_event_path=events_path,
            output_dir=tmp_path / "reject",
            max_rows_per_group=10,
            seed=7,
        )


def test_legacy_pneuma_schema_requires_explicit_mode(tmp_path: Path) -> None:
    ngsim_state = pd.DataFrame(
        {
            "dataset": ["NGSIM"],
            "site": ["US-101"],
            "window_id": ["w"],
            "vehicle_id": ["1"],
            "time_s": [0.0],
            "speed_mps": [10.0],
            "acceleration_mps2": [0.0],
            "net_gap_m": [10.0],
            "closing_speed_mps": [1.0],
            "measurement_status": ["valid"],
        }
    )
    ngsim_path = tmp_path / "ngsim.parquet"
    ngsim_state.to_parquet(ngsim_path, index=False)
    legacy = pd.DataFrame(
        {
            "id": ["p1"],
            "time_s": [0.0],
            "speed_mps": [5.0],
            "longitudinal_accel_mps2": [0.0],
        }
    )
    pneuma_path = tmp_path / "legacy.parquet"
    legacy.to_parquet(pneuma_path, index=False)
    events_path = tmp_path / "events.parquet"
    pd.DataFrame({"event_id": ["e1"]}).to_parquet(events_path, index=False)

    with pytest.raises(CalibrationContractError, match="canonical"):
        write_real_reference_package(
            ngsim_state_paths=[ngsim_path],
            pneuma_state_path=pneuma_path,
            ngsim_event_path=events_path,
            output_dir=tmp_path / "reject",
            max_rows_per_group=10,
            seed=7,
        )
    output = write_real_reference_package(
        ngsim_state_paths=[ngsim_path],
        pneuma_state_path=pneuma_path,
        ngsim_event_path=events_path,
        output_dir=tmp_path / "legacy",
        max_rows_per_group=10,
        seed=7,
        pneuma_schema="legacy",
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["pneuma_schema"] == "legacy"
    assert audit["formal_reference_eligible"] is False


def test_sealed_stage_0_3_canonical_parquet_directly_reaches_writer(tmp_path: Path) -> None:
    """Use the real sealed canonical file; skip only in a pure clone without data."""

    repo_root = Path(__file__).resolve().parents[2]
    canonical_path = repo_root / "code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/stage_0_5_reference_states.parquet"
    if not canonical_path.is_file():
        pytest.skip("sealed Stage 0.3 canonical pNEUMA input is not available in this clone")
    canonical = pd.read_parquet(canonical_path, columns=list(CANONICAL_PNEUMA_COLUMNS))
    assert list(canonical.columns) == list(CANONICAL_PNEUMA_COLUMNS)
    ngsim_path = tmp_path / "ngsim.parquet"
    pd.DataFrame(
        {
            "dataset": ["NGSIM", "NGSIM"],
            "site": ["US-101", "US-101"],
            "window_id": ["w", "w"],
            "vehicle_id": ["1", "1"],
            "time_s": [0.0, 0.1],
            "speed_mps": [10.0, 10.5],
            "acceleration_mps2": [0.0, 0.5],
            "net_gap_m": [10.0, 9.5],
            "closing_speed_mps": [1.0, 1.0],
            "measurement_status": ["valid", "valid"],
        }
    ).to_parquet(ngsim_path, index=False)
    events_path = tmp_path / "events.parquet"
    pd.DataFrame({"event_id": ["e1"], "dataset": ["NGSIM"], "site": ["US-101"], "window_id": ["w"]}).to_parquet(events_path, index=False)
    output = write_real_reference_package(
        ngsim_state_paths=[ngsim_path],
        pneuma_state_path=canonical_path,
        ngsim_event_path=events_path,
        output_dir=tmp_path / "real_canonical_reference",
        max_rows_per_group=10,
        seed=7,
    )
    reference = pd.read_parquet(output / "kinematics_reference.parquet")
    pneuma_rows = reference[reference["dataset"] == "pNEUMA"]
    assert not pneuma_rows.empty
    assert {"vehicle_type", "quality_status", "time_weighting_eligible", "source_file_sha256"}.issubset(pneuma_rows.columns)
