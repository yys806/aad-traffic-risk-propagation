import pandas as pd
import pytest

from riskprop.upstream_adapter import (
    UpstreamAdapterError,
    audit_flow_dependency,
    convert_drift_state_rows,
    map_drift_cell,
    validate_drift_mechanism_fields,
)


def test_drift_cell_mapping_is_explicit_and_bijective():
    assert [map_drift_cell(cell) for cell in ("r00", "r01", "r10", "r11")] == [
        "s0c0",
        "s0c1",
        "s1c0",
        "s1c1",
    ]


def test_drift_cell_mapping_rejects_unknown_cell_instead_of_guessing():
    with pytest.raises(UpstreamAdapterError, match="Unknown DRIFT cell"):
        map_drift_cell("r99")


def _valid_drift_state_row() -> dict[str, object]:
    return {
        "step": 4,
        "time_s": 0.8,
        "sumo_seed": 31,
        "cell": "r11",
        "vehicle_id": "tgt_receiver",
        "edge": "tgt_road",
        "x": 75.0,
        "y": 50.0,
        "lane_id": "tgt_road_0",
        "speed": 12.0,
        "headway": 15.0,
        "net_gap": 13.0,
        "relative_speed": -1.0,
        "leader_id": "tgt_leader",
        "follower_id": "",
        "realized_accel": 0.0,
    }


def test_drift_state_conversion_maps_only_explicit_fields_to_frozen_schema():
    converted = convert_drift_state_rows(
        pd.DataFrame([_valid_drift_state_row()]),
        run_id="run_31_r11",
        experiment_id="Stage 1.1",
        scenario_id="dual_corridor",
    )

    assert converted.loc[0, "cell_id"] == "s1c1"
    assert converted.loc[0, "edge_id"] == "tgt_road"
    assert converted.loc[0, "y_m"] == pytest.approx(50.0)
    assert converted.loc[0, "configured_seed"] == 31
    assert list(converted.columns) == [
        "run_id",
        "experiment_id",
        "scenario_id",
        "cell_id",
        "configured_seed",
        "simulation_seed",
        "time_s",
        "vehicle_id",
        "edge_id",
        "lane_id",
        "x_m",
        "y_m",
        "speed_mps",
        "acceleration_mps2",
        "leader_id",
        "net_gap_m",
        "relative_speed_mps",
    ]


def test_drift_state_conversion_rejects_missing_fields_instead_of_filling_zero():
    row = _valid_drift_state_row()
    del row["relative_speed"]

    with pytest.raises(UpstreamAdapterError, match="relative_speed"):
        convert_drift_state_rows(
            pd.DataFrame([row]),
            run_id="run_31_r11",
            experiment_id="Stage 1.1",
            scenario_id="dual_corridor",
        )


def test_drift_mechanism_validation_exposes_missing_formal_lifecycle_fields():
    rows = pd.DataFrame(
        [
            {
                "event_id": "e1",
                "step": 10,
                "vehicle_role": "target_receiver",
                "message_generated": True,
                "message_delivered": True,
                "message_provenance_valid": True,
                "adopted": True,
            }
        ]
    )

    with pytest.raises(UpstreamAdapterError, match="message_sent"):
        validate_drift_mechanism_fields(rows)


def test_flow_dependency_audit_is_explicit_when_expected_path_is_missing(tmp_path):
    result = audit_flow_dependency(tmp_path / "missing_flow")

    assert result["available"] is False
    assert result["reason"] == "flow_repository_missing"
