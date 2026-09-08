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
        "E15-A": {"gate_status": "pending_human_round1"},
        "E16-A": {"gate_status": "pending_official_packet_access"},
        "E17-A": {"gate_status": "not_started"},
        "E01": {"gate_status": "not_started"},
    }
    with pytest.raises(ProtocolLockError, match="E15-A"):
        write_protocol_lock(
            output_path=tmp_path / "protocol_lock_v1.1.yaml",
            gate_reports=gates,
            frozen_values={},
        )
    assert not (tmp_path / "protocol_lock_v1.1.yaml").exists()


def test_protocol_lock_requires_all_numeric_and_boundary_fields(tmp_path: Path) -> None:
    gates = {name: {"gate_status": "pass"} for name in ("E15-A", "E16-A", "E17-A", "E01")}
    with pytest.raises(ProtocolLockError, match="missing frozen fields"):
        write_protocol_lock(
            output_path=tmp_path / "protocol_lock_v1.1.yaml",
            gate_reports=gates,
            frozen_values={"time_step_s": 0.05},
        )


def test_readiness_report_lists_blockers_without_creating_a_lock() -> None:
    gates = {
        "E15-A": {"gate_status": "pending_human_round1"},
        "E16-A": {"gate_status": "pending_official_packet_access"},
        "E17-A": {"gate_status": "pending_pneuma_manual_and_simulation_sample"},
        "E01": {"gate_status": "pending_e15_e17_and_frozen_tolerances"},
    }
    report = protocol_lock_readiness(gates)
    assert report["protocol_lock_allowed"] is False
    assert report["e02_allowed"] is False
    assert report["blockers"] == [
        "E15-A=pending_human_round1",
        "E16-A=pending_official_packet_access",
        "E17-A=pending_pneuma_manual_and_simulation_sample",
        "E01=pending_e15_e17_and_frozen_tolerances",
    ]
