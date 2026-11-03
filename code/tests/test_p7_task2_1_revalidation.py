"""Offline preparation only: these tests never launch SUMO."""
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from riskprop.message_driven_longitudinal_controller import (
    PolicyConfig, PolicyInput, load_engineering_config, longitudinal_policy)
from riskprop.p7_evidence_adapter import P7EvidenceAdapter
from riskprop.p7_sumo_integration import abnormal_deceleration, start_sumo_once
from test_p7_message_controller import state
from riskprop.message_driven_longitudinal_controller import RunAssignment

ROOT = Path(__file__).resolve().parents[2]


def test_v2_config_frozen_and_empty_policy_input_matches_v1():
    c1 = load_engineering_config(ROOT / "code/configs/p7_task2_engineering_candidate_v1.json")
    c2 = load_engineering_config(ROOT / "code/configs/p7_task2_engineering_candidate_v2.json")
    assert c2["policy_version"] == "aad.p7.longitudinal.engineering.v1.1"
    assert c2["reference_deceleration_mps2"] == 1.0 and c2["step_s"] == 0.1
    allowed = {"config_version", "policy_version", "source", "reference_deceleration_mps2"}
    assert {k for k in set(c1) | set(c2) if c1.get(k) != c2.get(k)} <= allowed
    for speed in (0, 10, 20):
        inputs = PolicyInput(replace(state(), speed_mps=float(speed)), ())
        assert longitudinal_policy(inputs, PolicyConfig.from_dict(c1)) == longitudinal_policy(inputs, PolicyConfig.from_dict(c2))
        assert longitudinal_policy(inputs, PolicyConfig.from_dict(c2)).target_speed_reference_mps is None


@pytest.mark.parametrize("a,expected", [(-4.5, False), (-4.5 - 1e-12, False), (-4.5 - 1e-7, True), (-9, True)])
def test_decel_boundary_allows_only_roundoff(a, expected):
    assert abnormal_deceleration(a, 4.5) is expected


@pytest.mark.parametrize("failure", [False, True])
def test_explicit_port_start_is_single_attempt_and_receipt_cannot_repeat(tmp_path, failure):
    calls = []
    def fake_start(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if failure:
            raise RuntimeError("deliberate fake connection failure, no process")
    adapter = P7EvidenceAdapter(tmp_path / "fake", "independent-run", RunAssignment("ENABLED", "assignment", "offline-test"))
    traci = SimpleNamespace(start=fake_start)
    if failure:
        with pytest.raises(RuntimeError, match="fake connection"):
            start_sumo_once(traci, ["FAKE_NOT_EXECUTED"], "independent-run", adapter)
    else:
        start_sumo_once(traci, ["FAKE_NOT_EXECUTED"], "independent-run", adapter)
    assert len(calls) == 1 and calls[0][1]["port"] > 0 and calls[0][1]["label"] == "independent-run"
    with pytest.raises(FileExistsError):
        start_sumo_once(traci, ["FAKE_NOT_EXECUTED"], "independent-run", adapter)
    assert len(calls) == 1
    assert json.loads((adapter.root / "launch_consumed.json").read_text())["process_relaunch_allowed"] is False
