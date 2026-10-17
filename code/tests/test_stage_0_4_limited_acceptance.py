"""Verify stage_0_4 pass_limited does NOT unlock the protocol lock."""
from __future__ import annotations

import pytest

from riskprop.protocol_lock import protocol_lock_readiness, write_protocol_lock

FROZEN = {
    "delta_eq": 0.05, "delta_R": 0.1, "delta_plan": 0.2,
    "sample_size": 1000, "window": "fixed", "target_region": "r",
    "message_semantics": "m", "evaluation_window": "w", "randomization": "s",
    "simulation_applicability": "a", "extrapolation_exclusions": "e",
    "missing_failure_inclusion_rules": "f", "runner_version": "r",
    "analyzer_version": "a", "environment_version": "e", "code_commit": "c",
}


def _gates(s04="pass_limited", s05="pass", s06="pass", s02="pass"):
    return {
        "stage_0_2": {"gate_status": s02},
        "stage_0_4": {"gate_status": s04},
        "stage_0_5": {"gate_status": s05},
        "stage_0_6": {"gate_status": s06},
    }


def test_pass_limited_still_blocked_when_others_not_pass():
    """stage_0_4 pass_limited alone does NOT allow the protocol lock."""
    readiness = protocol_lock_readiness(_gates(s04="pass_limited", s05="pending_simulation_sample",
                                                s06="blocked_by_calibration_and_tolerance_freeze"))
    assert readiness["protocol_lock_allowed"] is False
    assert readiness["stage_1_1_allowed"] is False
    assert any("stage_0_5" in b for b in readiness["blockers"])
    assert any("stage_0_6" in b for b in readiness["blockers"])


def test_pass_limited_does_not_unlock_stage1():
    """Even if all others pass, stage_1_1 is not auto-allowed without a written lock."""
    readiness = protocol_lock_readiness(_gates(s04="pass_limited"))
    assert readiness["stage_1_1_allowed"] is False


def test_pass_limited_is_accepted_for_stage_0_4_only():
    """pass_limited satisfies stage_0_4 in readiness but a write still needs all gates pass."""
    assert protocol_lock_readiness(_gates(s04="pass_limited"))["protocol_lock_allowed"] is True


def test_pending_packet_access_blocks_stage_0_4():
    """The historical pending_official_packet_access status must NOT be accepted."""
    readiness = protocol_lock_readiness(_gates(s04="pending_official_packet_access"))
    assert readiness["protocol_lock_allowed"] is False
    assert any("stage_0_4" in b for b in readiness["blockers"])


def test_write_lock_fails_when_stage_0_4_pending(tmp_path):
    with pytest.raises(Exception):
        write_protocol_lock(output_path=tmp_path / "lock.json",
                            gate_reports=_gates(s04="pending_official_packet_access"),
                            frozen_values=FROZEN)
