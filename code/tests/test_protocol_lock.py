from __future__ import annotations

import json
from pathlib import Path

import pytest

from riskprop.protocol_lock import (
    ProtocolLockError,
    protocol_lock_readiness,
    write_protocol_lock,
)


def test_protocol_lock_refuses_to_sign_while_any_required_gate_is_pending(
    tmp_path: Path,
) -> None:
    gates = {
        "stage_0_2": {"gate_status": "active"},
        "stage_0_4": {"gate_status": "pending_official_packet_access"},
        "stage_0_5": {"gate_status": "not_started"},
        "stage_0_6": {"gate_status": "not_started"},
    }
    with pytest.raises(ProtocolLockError, match="stage_0_2"):
        write_protocol_lock(
            output_path=tmp_path / "protocol_lock_v1.1.yaml",
            gate_reports=gates,
            frozen_values={},
        )
    assert not (tmp_path / "protocol_lock_v1.1.yaml").exists()


def test_protocol_lock_requires_all_numeric_and_boundary_fields(tmp_path: Path) -> None:
    gates = {name: {"gate_status": "pass"} for name in ("stage_0_2", "stage_0_4", "stage_0_5", "stage_0_6")}
    with pytest.raises(ProtocolLockError, match="missing frozen fields"):
        write_protocol_lock(
            output_path=tmp_path / "protocol_lock_v1.1.yaml",
            gate_reports=gates,
            frozen_values={"time_step_s": 0.05},
        )


def test_readiness_report_lists_blockers_without_creating_a_lock() -> None:
    gates = {
        "stage_0_2": {"gate_status": "active"},
        "stage_0_4": {"gate_status": "pending_official_packet_access"},
        "stage_0_5": {"gate_status": "pending_simulation_sample"},
        "stage_0_6": {"gate_status": "pending_calibration_and_frozen_tolerances"},
    }
    report = protocol_lock_readiness(gates)
    assert report["protocol_lock_allowed"] is False
    assert report["stage_1_1_allowed"] is False
    assert report["blockers"] == [
        "stage_0_2=active",
        "stage_0_4=pending_official_packet_access",
        "stage_0_5=pending_simulation_sample",
        "stage_0_6=pending_calibration_and_frozen_tolerances",
    ]
