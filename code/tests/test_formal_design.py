from copy import deepcopy

import pandas as pd
import pytest

from riskprop.formal_design import (
    FormalDesignError,
    validate_four_cell_configs,
    validate_pre_treatment_equivalence,
    validate_protocol_lifecycle,
    validate_run_state_isolation,
    validate_simulation_time_alignment,
    validate_vehicle_id_lifecycle,
)


def _four_cell_configs() -> dict[str, dict[str, object]]:
    common = {
        "schema_version": "stage_0_1.four-cell.v1",
        "experiment_id": "Stage 1.1",
        "theory_version": "nc-prereg-v1.0",
        "protocol_version": "dual-corridor-v1",
        "scenario_id": "dual_corridor_calibration",
        "pair_id": "pair_0001",
        "configured_seed": 2026081701,
        "simulation_seed": 1701,
        "source_vehicle_id": "source_0",
        "target_vehicle_id": "target_0",
        "window_start_s": 10.0,
        "window_end_s": 15.0,
        "time_step_s": 0.05,
    }
    configs = {}
    for source in (False, True):
        for channel in (False, True):
            cell_id = f"s{int(source)}c{int(channel)}"
            configs[cell_id] = {
                **deepcopy(common),
                "run_id": f"pair_0001_{cell_id}",
                "cell_id": cell_id,
                "source_present": source,
                "channel_enabled": channel,
                "output_dir": f"outputs/{cell_id}",
            }
    return configs


def test_four_cell_configs_allow_only_source_channel_and_output_identity():
    result = validate_four_cell_configs(_four_cell_configs())

    assert result["cell_ids"] == ["s0c0", "s0c1", "s1c0", "s1c1"]
    assert result["pair_id"] == "pair_0001"
    assert len(result["common_config_sha256"]) == 64


def test_four_cell_configs_reject_a_hidden_simulation_seed_difference():
    configs = _four_cell_configs()
    configs["s1c1"]["simulation_seed"] = 9999

    with pytest.raises(FormalDesignError, match="simulation_seed"):
        validate_four_cell_configs(configs)


def test_four_cell_configs_reject_a_missing_counterfactual_cell():
    configs = _four_cell_configs()
    del configs["s0c1"]

    with pytest.raises(FormalDesignError, match="missing.*s0c1"):
        validate_four_cell_configs(configs)


def _valid_protocol_row() -> dict[str, object]:
    return {
        "message_id": "m1",
        "message_generated": True,
        "message_sent": True,
        "message_dropped": False,
        "message_delivered": True,
        "source_valid": True,
        "target_valid": True,
        "freshness_valid": True,
        "adopted": True,
        "generated_time_s": 1.0,
        "sent_time_s": 1.1,
        "delivered_time_s": 1.2,
        "validation_time_s": 1.25,
        "adopted_time_s": 1.3,
        "message_age_s": 0.3,
    }


def test_protocol_lifecycle_accepts_a_traceable_monotone_adoption_chain():
    result = validate_protocol_lifecycle(
        pd.DataFrame([_valid_protocol_row()]),
        source_present=True,
        channel_enabled=True,
    )

    assert result["record_count"] == 1
    assert result["adopted_count"] == 1
    assert result["lifecycle_pass"] is True


def test_protocol_lifecycle_rejects_adoption_without_delivery():
    row = _valid_protocol_row()
    row["message_delivered"] = False
    row["delivered_time_s"] = None

    with pytest.raises(FormalDesignError, match="adopted.*message_delivered"):
        validate_protocol_lifecycle(
            pd.DataFrame([row]), source_present=True, channel_enabled=True
        )


def test_protocol_lifecycle_rejects_reversed_delivery_and_validation_times():
    row = _valid_protocol_row()
    row["validation_time_s"] = 1.15

    with pytest.raises(FormalDesignError, match="delivered_time_s > validation_time_s"):
        validate_protocol_lifecycle(
            pd.DataFrame([row]), source_present=True, channel_enabled=True
        )


def test_protocol_lifecycle_rejects_messages_sent_through_a_closed_channel():
    with pytest.raises(FormalDesignError, match="closed channel"):
        validate_protocol_lifecycle(
            pd.DataFrame([_valid_protocol_row()]),
            source_present=True,
            channel_enabled=False,
        )


def test_protocol_lifecycle_accepts_open_channel_sham_without_source_event():
    row = _valid_protocol_row()
    row.update(
        {
            "message_kind": "sham",
            "message_generated": True,
            "source_valid": False,
            "freshness_valid": False,
            "adopted": False,
            "adopted_time_s": None,
            "message_age_s": None,
            "rejection_reason": "sham_no_source_event",
        }
    )
    result = validate_protocol_lifecycle(
        pd.DataFrame([row]), source_present=False, channel_enabled=True
    )
    assert result["generated_count"] == 1
    assert result["delivered_count"] == 1
    assert result["adopted_count"] == 0


def test_protocol_lifecycle_rejects_source_absent_message_without_sham_kind():
    with pytest.raises(FormalDesignError, match="source-absent"):
        validate_protocol_lifecycle(
            pd.DataFrame([_valid_protocol_row()]),
            source_present=False,
            channel_enabled=True,
        )


def _pre_treatment_rows() -> pd.DataFrame:
    rows = []
    for cell_id in ("s0c0", "s0c1", "s1c0", "s1c1"):
        for time_s, speed, acceleration in (
            (0.0, 10.0, 0.0),
            (1.0, 10.2, 0.2),
            (2.0, 9.0 if cell_id == "s1c1" else 10.4, -1.0),
        ):
            rows.append(
                {
                    "cell_id": cell_id,
                    "time_s": time_s,
                    "vehicle_id": "target_0",
                    "edge_id": "target_edge",
                    "lane_id": "target_edge_0",
                    "leader_id": "leader_0",
                    "x_m": 100.0 + 10.0 * time_s,
                    "speed_mps": speed,
                    "acceleration_mps2": acceleration,
                }
            )
    return pd.DataFrame(rows)


def test_pre_treatment_equivalence_ignores_only_post_treatment_divergence():
    result = validate_pre_treatment_equivalence(
        _pre_treatment_rows(),
        treatment_start_s=2.0,
        key_columns=("time_s", "vehicle_id"),
        exact_columns=("edge_id", "lane_id", "leader_id"),
        numeric_tolerances={
            "x_m": 1e-9,
            "speed_mps": 1e-9,
            "acceleration_mps2": 1e-9,
        },
    )

    assert result["pre_treatment_rows_per_cell"] == 2
    assert result["equivalence_pass"] is True


def test_pre_treatment_equivalence_rejects_a_hidden_prefix_difference():
    rows = _pre_treatment_rows()
    mask = (rows["cell_id"] == "s1c1") & (rows["time_s"] == 1.0)
    rows.loc[mask, "speed_mps"] += 0.01

    with pytest.raises(FormalDesignError, match="speed_mps"):
        validate_pre_treatment_equivalence(
            rows,
            treatment_start_s=2.0,
            key_columns=("time_s", "vehicle_id"),
            exact_columns=("edge_id", "lane_id", "leader_id"),
            numeric_tolerances={"speed_mps": 1e-9},
        )


def test_pre_treatment_equivalence_rejects_infinite_state_values():
    rows = _pre_treatment_rows()
    mask = (rows["cell_id"] == "s1c1") & (rows["time_s"] == 1.0)
    rows.loc[mask, "speed_mps"] = float("inf")

    with pytest.raises(FormalDesignError, match="not finite.*speed_mps"):
        validate_pre_treatment_equivalence(
            rows,
            treatment_start_s=2.0,
            key_columns=("time_s", "vehicle_id"),
            exact_columns=(),
            numeric_tolerances={"speed_mps": 1e-9},
        )


def _state_isolation_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": "pair_1_s0c0",
                "state_instance_id": "state_1",
                "cache_namespace": "cache_1",
                "rng_stream_id": "rng_1",
                "initial_cache_entries": 0,
                "initial_pending_messages": 0,
            },
            {
                "run_id": "pair_1_s0c1",
                "state_instance_id": "state_2",
                "cache_namespace": "cache_2",
                "rng_stream_id": "rng_2",
                "initial_cache_entries": 0,
                "initial_pending_messages": 0,
            },
        ]
    )


def test_run_state_isolation_requires_fresh_state_cache_and_rng_namespaces():
    result = validate_run_state_isolation(_state_isolation_audit())

    assert result["run_count"] == 2
    assert result["isolation_pass"] is True


def test_run_state_isolation_rejects_a_reused_cache_namespace():
    audit = _state_isolation_audit()
    audit.loc[1, "cache_namespace"] = audit.loc[0, "cache_namespace"]

    with pytest.raises(FormalDesignError, match="cache_namespace"):
        validate_run_state_isolation(audit)


def _aligned_stream_audit() -> pd.DataFrame:
    rows = []
    for stream_name in ("state", "protocol", "action"):
        for sequence_index, simulation_step in enumerate((10, 11)):
            rows.append(
                {
                    "run_id": "run_1",
                    "stream_name": stream_name,
                    "sequence_index": sequence_index,
                    "simulation_step": simulation_step,
                    "time_s": simulation_step * 0.1,
                }
            )
    return pd.DataFrame(rows)


def test_simulation_time_alignment_accepts_explicit_synchronized_streams():
    result = validate_simulation_time_alignment(
        _aligned_stream_audit(), time_step_s=0.1, time_origin_s=0.0
    )

    assert result["stream_count"] == 3
    assert result["time_alignment_pass"] is True


def test_simulation_time_alignment_rejects_a_one_step_protocol_shift():
    audit = _aligned_stream_audit()
    shifted = (audit["stream_name"] == "protocol") & (
        audit["simulation_step"] == 11
    )
    audit.loc[shifted, "time_s"] = 1.2

    with pytest.raises(FormalDesignError, match="simulation_step.*time_s"):
        validate_simulation_time_alignment(
            audit, time_step_s=0.1, time_origin_s=0.0
        )


def test_simulation_time_alignment_rejects_non_finite_timestamps():
    audit = _aligned_stream_audit()
    audit.loc[0, "time_s"] = float("inf")

    with pytest.raises(FormalDesignError, match="non-finite"):
        validate_simulation_time_alignment(
            audit, time_step_s=0.1, time_origin_s=0.0
        )


def _vehicle_lifecycle() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": "run_1",
                "vehicle_id": "veh_1",
                "incarnation_id": "run_1:veh_1:0",
                "event_type": "enter",
                "time_s": 0.0,
                "event_sequence": 0,
            },
            {
                "run_id": "run_1",
                "vehicle_id": "veh_1",
                "incarnation_id": "run_1:veh_1:0",
                "event_type": "active",
                "time_s": 0.1,
                "event_sequence": 1,
            },
            {
                "run_id": "run_1",
                "vehicle_id": "veh_1",
                "incarnation_id": "run_1:veh_1:0",
                "event_type": "exit",
                "time_s": 0.2,
                "event_sequence": 2,
            },
        ]
    )


def test_vehicle_id_lifecycle_accepts_one_incarnation_and_monotone_events():
    result = validate_vehicle_id_lifecycle(_vehicle_lifecycle())

    assert result["vehicle_count"] == 1
    assert result["vehicle_lifecycle_pass"] is True


def test_vehicle_id_lifecycle_rejects_reference_after_vehicle_exit():
    lifecycle = _vehicle_lifecycle()
    lifecycle.loc[len(lifecycle)] = {
        "run_id": "run_1",
        "vehicle_id": "veh_1",
        "incarnation_id": "run_1:veh_1:0",
        "event_type": "reference",
        "time_s": 0.3,
        "event_sequence": 3,
    }

    with pytest.raises(FormalDesignError, match="after exit"):
        validate_vehicle_id_lifecycle(lifecycle)


def test_vehicle_id_lifecycle_rejects_reuse_of_a_departed_vehicle_id():
    lifecycle = _vehicle_lifecycle()
    lifecycle.loc[len(lifecycle)] = {
        "run_id": "run_1",
        "vehicle_id": "veh_1",
        "incarnation_id": "run_1:veh_1:1",
        "event_type": "enter",
        "time_s": 0.3,
        "event_sequence": 3,
    }

    with pytest.raises(FormalDesignError, match="reused.*vehicle_id"):
        validate_vehicle_id_lifecycle(lifecycle)


def test_vehicle_id_lifecycle_rejects_non_finite_event_time():
    lifecycle = _vehicle_lifecycle()
    lifecycle.loc[1, "time_s"] = float("inf")

    with pytest.raises(FormalDesignError, match="finite"):
        validate_vehicle_id_lifecycle(lifecycle)
