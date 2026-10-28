from __future__ import annotations

import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from stage_0_5_linux_execution_v4 import (
    ROUND2_TASK1_BASE_INPUTS,
    ROUND2_TASK1_BASE_RUN,
    ROUND2_TASK1_CANDIDATE,
    ROUND2_TASK1_CANDIDATE_INPUTS,
    ROUND2_TASK1_EXPERIMENT,
    ROUND2_TASK1_INPUT_SHA256,
    TASK,
    _round2_task1_route_contract,
    validate_round2_task1_min_gap_candidate,
)


ROOT = Path(__file__).resolve().parents[2]
APPROVAL = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/approval_record.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _proposal_runs():
    approval_sha = _sha(APPROVAL)
    locked = dict(
        condition="us101__0750_0805",
        seed=20261201,
        duration_s=420,
        internal_step_s=0.05,
        evaluation_elapsed_s=[120, 390],
        common_support_references=["evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/us101__0750_0805_real_offset100.csv"],
        supply_target_lanes=["main_2_0", "main_2_1", "main_2_2", "main_2_3", "main_2_4"],
        lane_speed_schedule=[dict(start_s=0, end_s=420, speed_mps=10)],
        single_attempt_limits=dict(per_attempt_wall_s=600),
    )
    base = dict(locked, id=ROUND2_TASK1_BASE_RUN, task_id=TASK,
                input_files=ROUND2_TASK1_BASE_INPUTS,
                input_sha256={k: _sha(ROOT / v) for k, v in ROUND2_TASK1_BASE_INPUTS.items()},
                artifact_path="code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03",
                paired_base_routes=ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"])
    candidate = dict(locked, id=ROUND2_TASK1_CANDIDATE, task_id=TASK,
                     input_files=ROUND2_TASK1_CANDIDATE_INPUTS,
                     input_sha256={ROUND2_TASK1_CANDIDATE_INPUTS[k]: v for k, v in ROUND2_TASK1_INPUT_SHA256.items()},
                     artifact_path="code/outputs/formal/calibration/stage_0_5_round2_task1/runs/AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1",
                     paired_base_routes=ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"])
    proposal = dict(experiment_id=ROUND2_TASK1_EXPERIMENT, candidate_id=ROUND2_TASK1_CANDIDATE,
                    task_id=TASK, round2_baseline_run_id=ROUND2_TASK1_BASE_RUN,
                    round2_approval_path="evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/approval_record.json",
                    round2_approval_sha256=approval_sha)
    return proposal, candidate, base


def test_round2_exact_candidate_passes_task_specific_contract():
    proposal, candidate, base = _proposal_runs()
    result = validate_round2_task1_min_gap_candidate(ROOT, proposal, candidate, base)
    assert result["status"] == "Pass"
    assert result["route_contract"]["changed_vtypes"] == [f"B_het_c{i}_passenger" for i in range(5)]


def test_round2_rejects_extra_vtype_change():
    base = (ROOT / ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"]).read_bytes()
    candidate = ET.fromstring((ROOT / ROUND2_TASK1_CANDIDATE_INPUTS["routes.rou.xml"]).read_bytes())
    candidate.find("vType[@id='B_het_c0_passenger']").set("tau", "9.0")
    with pytest.raises(ValueError, match="non_target|scope|value"):
        _round2_task1_route_contract(base, ET.tostring(candidate))


def test_round2_rejects_non_target_vehicle_type_and_identity_changes():
    base = (ROOT / ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"]).read_bytes()
    candidate = ET.fromstring((ROOT / ROUND2_TASK1_CANDIDATE_INPUTS["routes.rou.xml"]).read_bytes())
    candidate.find("vehicle").set("type", "B_het_c1_passenger")
    with pytest.raises(ValueError):
        _round2_task1_route_contract(base, ET.tostring(candidate))
    candidate = ET.fromstring((ROOT / ROUND2_TASK1_CANDIDATE_INPUTS["routes.rou.xml"]).read_bytes())
    candidate.find("vehicle").set("id", "unapproved_identity")
    with pytest.raises(ValueError):
        _round2_task1_route_contract(base, ET.tostring(candidate))


def test_round2_rejects_route_or_departure_change():
    base = (ROOT / ROUND2_TASK1_BASE_INPUTS["routes.rou.xml"]).read_bytes()
    candidate = ET.fromstring((ROOT / ROUND2_TASK1_CANDIDATE_INPUTS["routes.rou.xml"]).read_bytes())
    candidate.find("route").set("edges", "not_the_approved_route")
    with pytest.raises(ValueError):
        _round2_task1_route_contract(base, ET.tostring(candidate))
    candidate = ET.fromstring((ROOT / ROUND2_TASK1_CANDIDATE_INPUTS["routes.rou.xml"]).read_bytes())
    candidate.find("vehicle").set("depart", "1.0")
    with pytest.raises(ValueError):
        _round2_task1_route_contract(base, ET.tostring(candidate))


@pytest.mark.parametrize("field,value", [
    ("candidate_id", "other-candidate"),
    ("experiment_id", "other-task"),
])
def test_round2_rejects_candidate_or_task_identity(field, value):
    proposal, candidate, base = _proposal_runs()
    proposal[field] = value
    with pytest.raises(ValueError):
        validate_round2_task1_min_gap_candidate(ROOT, proposal, candidate, base)


def test_round2_rejects_input_hash_drift_and_locked_field_change():
    proposal, candidate, base = _proposal_runs()
    drifted = copy.deepcopy(candidate)
    drifted["input_sha256"][ROUND2_TASK1_CANDIDATE_INPUTS["routes.rou.xml"]] = "0" * 64
    with pytest.raises(ValueError):
        validate_round2_task1_min_gap_candidate(ROOT, proposal, drifted, base)
    changed = copy.deepcopy(candidate)
    changed["seed"] = 20261202
    with pytest.raises(ValueError):
        validate_round2_task1_min_gap_candidate(ROOT, proposal, changed, base)


def test_round2_negative_contract_is_prelaunch_only():
    """Negative validation is pure and creates no process/launch artifact."""
    proposal, candidate, base = _proposal_runs()
    proposal["candidate_id"] = "wrong"
    with pytest.raises(ValueError):
        validate_round2_task1_min_gap_candidate(ROOT, proposal, candidate, base)
    assert not (ROOT / candidate["artifact_path"]).exists()
