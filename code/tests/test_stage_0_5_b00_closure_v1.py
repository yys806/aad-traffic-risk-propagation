"""Focused ENG-01/02 regressions for the first native B00 closure."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
import sys
sys.path.insert(0, str(SCRIPTS))
import stage_0_5_execution_v2 as execution
import stage_0_5_identity_observation as identity
import stage_0_5_linux_execution_v4 as linux
from stage_0_5_native_capsule_v4 import canonical, sha


def _sim(getter):
    return SimpleNamespace(getTime=lambda: .05, getLoadedIDList=lambda: [],
        getDepartedIDList=lambda: [], getArrivedIDList=lambda: [],
        getPendingVehicles=lambda: [], getStartingTeleportIDList=lambda: [],
        getEndingTeleportIDList=lambda: [], getCollidingVehiclesNumber=getter)


@pytest.mark.parametrize("getter,status", [
    (lambda: (_ for _ in ()).throw(AttributeError("missing")), "unavailable"),
    (lambda: (_ for _ in ()).throw(RuntimeError("boom")), "unavailable"),
    (lambda: None, "invalid"),
    (lambda: 1.5, "invalid"),
    (lambda: True, "invalid"),
])
def test_collision_getter_missing_exception_and_invalid_value_are_not_zero(getter, status):
    frame = identity.collect_snapshot(SimpleNamespace(simulation=_sim(getter), vehicle=SimpleNamespace(getIDList=lambda: [])))
    assert frame["collision_count"] is None
    assert frame["collision_observation_status"] == status
    assert "collision_count" in frame["unavailable"]


def test_collision_getter_explicit_zero_is_valid_vehicle_count():
    frame = identity.collect_snapshot(SimpleNamespace(simulation=_sim(lambda: 0), vehicle=SimpleNamespace(getIDList=lambda: [])))
    assert frame["collision_count"] == 0
    assert frame["collision_observation_status"] == "available"
    assert "vehicle_count" in frame["collision_count_semantics"]


def _native_frame(t, *, collision=0, status="available", teleport_start=None, teleport_end=None):
    return dict(time_s=t, phase="after_simulationStep", loaded=[], departed=[], arrived=[],
        pending=[], active=[], teleport_start=[] if teleport_start is None else teleport_start,
        teleport_end=[] if teleport_end is None else teleport_end, discarded=None,
        native_departures={}, collision_count=collision,
        collision_observation_required=True, collision_observation_status=status,
        collision_count_semantics="colliding_vehicle_count_current_step; not collision_event_count")


class _Backend:
    synthetic_only = False
    def __init__(self, frames):
        self.frames = iter(frames)
    def before_step(self, now, context):
        return dict(applied_before_step_s=now, native_clock_before_s=now, target_mps=10,
                    native_lane_limits={}, failures=[])
    def step(self):
        return next(self.frames)


class _Supervisor:
    def observe(self):
        return None


def _run_one(frame):
    observer = identity.IdentityObserver([dict(id="i1", depart_s=0)], step_s=.05)
    observer.ingest(dict(time_s=0, phase="initial_snapshot", loaded=None, departed=None,
        arrived=None, pending=[], active=[], teleport_start=None, teleport_end=None,
        discarded=None, native_departures={}))
    context = {"run": {"duration_s": .05, "lane_speed_schedule": [dict(start_s=0, end_s=.05, speed_mps=10)]}}
    return execution.run_observation_loop(context, _Backend([frame]), observer, SimpleNamespace(append=lambda _: None), _Supervisor(), synthetic=False)


@pytest.mark.parametrize("frame,match", [
    (_native_frame(.05, status="unavailable", collision=None), "collision_observation_missing"),
    (_native_frame(.05, status="invalid", collision=None), "collision_observation_missing"),
    (_native_frame(.05, collision=1), "collision_or_teleport_stop"),
    (_native_frame(.05, teleport_start=["i1"]), "teleport_before_departure|collision_or_teleport_stop"),
])
def test_native_loop_stops_on_missing_or_nonzero_collision_and_teleport(frame, match):
    with pytest.raises((RuntimeError, identity.IdentityContractError), match=match):
        _run_one(frame)


def test_collision_gap_cannot_be_hidden_by_later_recovery():
    observer = identity.IdentityObserver([dict(id="i1", depart_s=0)], step_s=.05)
    observer.ingest(dict(time_s=0, phase="initial_snapshot", loaded=None, departed=None,
        arrived=None, pending=[], active=[], teleport_start=None, teleport_end=None,
        discarded=None, native_departures={}))
    frames = [_native_frame(.05, status="unavailable", collision=None), _native_frame(.10, collision=0)]
    with pytest.raises((RuntimeError, identity.IdentityContractError), match="collision_observation"):
        execution.run_observation_loop({"run": {"duration_s": .1,
            "lane_speed_schedule": [dict(start_s=0, end_s=.1, speed_mps=10)]}},
            _Backend(frames), observer, SimpleNamespace(append=lambda _: None), _Supervisor(), synthetic=False)


def _policy_fixture(tmp_path, *, accepted=True):
    source = {"stage_0_5_execution_v2.py": "a" * 64}
    runtime = "b" * 64
    policy = {"binding": {"accepted_build": accepted, "source_sha256": source,
                           "runtime_manifest_sha256": runtime, "run_id": "B00"}}
    policy_path = tmp_path / "policy.json"
    policy_path.write_bytes(canonical(policy))
    proposal = {"policy_binding_required": True, "capsule_policy_repo_path": "policy.json",
                "capsule_policy_sha256": sha(policy_path), "controller_source_sha256": source,
                "runtime_manifest_sha256": runtime}
    return proposal, policy_path


@pytest.mark.parametrize("mutation,reason", [
    (lambda p, q: (q.write_bytes(canonical({"binding": {"accepted_build": False,
        "source_sha256": p["controller_source_sha256"], "runtime_manifest_sha256": p["runtime_manifest_sha256"], "run_id": "B00"}})),
        p.update(capsule_policy_sha256=sha(q))), "research_policy_accepted_build_false"),
    (lambda p, q: q.unlink(), "bound_policy_missing"),
    (lambda p, q: q.write_bytes(b"drift"), "bound_policy_hash_mismatch"),
])
def test_bound_policy_rejects_before_any_side_effect(tmp_path, mutation, reason):
    proposal, policy_path = _policy_fixture(tmp_path)
    mutation(proposal, policy_path)
    with pytest.raises(ValueError, match=reason):
        linux.verify_bound_research_policy(tmp_path, proposal, "B00")


def test_false_policy_exact_research_refusal_has_zero_reserve_attempt_and_launch(tmp_path):
    proposal, policy_path = _policy_fixture(tmp_path, accepted=False)
    proposal.update(schema="aad.native-admission.v4", task_id="AAD-0.5-READY-TO-ADMIT-V3",
                    runs=[{"id": "B00"}])
    p = tmp_path / "proposal.json"
    p.write_bytes(canonical(proposal))
    calls = {"reserve": 0, "launch": 0}
    adapter = SimpleNamespace(repo=tmp_path,
        refuse=lambda reasons, run_id: (_ for _ in ()).throw(PermissionError(";".join(reasons))),
        ledger=SimpleNamespace(reserve=lambda *a, **k: calls.__setitem__("reserve", calls["reserve"] + 1)))
    approval = dict(proposal_sha256=sha(p), task_id=proposal["task_id"], run_id="B00",
                    researcher_confirmed=True, execution_allowed=True, protocol_frozen=True,
                    decision_record="User authorized exact B00 closure",
                    admission={"initialization_policy_approved": True,
                               "measurement_contract_approved": True,
                               "input_fidelity_approved": True})
    with pytest.raises(PermissionError):
        linux.execute_research(adapter, "proposal.json", approval, "B00")
    assert calls == {"reserve": 0, "launch": 0}


def test_policy_missing_marker_or_run_binding_is_rejected(tmp_path):
    proposal, path = _policy_fixture(tmp_path)
    proposal.pop("policy_binding_required")
    with pytest.raises(ValueError, match="binding_required"):
        linux.verify_bound_research_policy(tmp_path, proposal, "B00")
    proposal["policy_binding_required"] = True
    policy = json.loads(path.read_bytes())
    policy["binding"].pop("run_id")
    path.write_bytes(canonical(policy))
    proposal["capsule_policy_sha256"] = sha(path)
    with pytest.raises(ValueError, match="run_binding"):
        linux.verify_bound_research_policy(tmp_path, proposal, "B00")


@pytest.mark.parametrize("fault", ["false", "missing", "drift", "run"])
def test_actual_ledger_policy_refusal_leaves_zero_attempts(tmp_path, fault):
    from test_stage_0_5_native_capsule_v4 import v4_ledger_fixture
    ledger, proposal, approval, resources = v4_ledger_fixture(tmp_path)
    before = ledger.path.read_bytes()
    policy_path = tmp_path/"policy.json"
    if fault in {"false", "run"}:
        policy = json.loads(policy_path.read_bytes())
        if fault == "false": policy["binding"]["accepted_build"] = False
        else: policy["binding"].pop("run_id")
        policy_path.write_bytes(canonical(policy))
        proposal["capsule_policy_sha256"] = sha(policy_path)
        (tmp_path/"proposal.json").write_bytes(canonical(proposal))
        approval["proposal_sha256"] = sha(tmp_path/"proposal.json")
    elif fault == "missing": policy_path.unlink()
    else: policy_path.write_bytes(b"drift")
    with pytest.raises(ValueError):
        ledger.reserve("proposal.json", approval, "B00_SYNTHETIC", resources)
    assert ledger.path.read_bytes() == before
    assert ledger.snapshot()["attempt_count"] == 0
def test_collision_method_actually_absent():
    sim = _sim(lambda: 0)
    del sim.getCollidingVehiclesNumber
    frame = identity.collect_snapshot(SimpleNamespace(simulation=sim, vehicle=SimpleNamespace(getIDList=lambda: [])))
    assert frame["collision_count"] is None and "AttributeError" in frame["unavailable"]["collision_count"]


def _observer():
    observer = identity.IdentityObserver([dict(id="i1", depart_s=0)], step_s=.05)
    observer.ingest(dict(time_s=0, phase="initial_snapshot", loaded=[], departed=None,
        arrived=None, pending=["i1"], active=[], teleport_start=None, teleport_end=None,
        discarded=None, native_departures={}))
    return observer


def test_middle_collision_gap_is_sticky_after_recovery_and_raw_journal_retained():
    observer = _observer()
    first = _native_frame(.05); first.update(loaded=["i1"], pending=["i1"])
    observer.ingest(first)
    missing = _native_frame(.10, collision=None, status="unavailable")
    missing["unavailable"] = {"collision_count": "RuntimeError:original getter failure"}
    journal = []
    with pytest.raises(identity.IdentityContractError):
        execution.run_observation_loop({"run": {"duration_s": .05}}, _Backend([missing]), observer,
            SimpleNamespace(append=journal.append), _Supervisor(), synthetic=False)
    assert journal[-1]["unavailable"] == missing["unavailable"]
    recovered = _native_frame(.10); recovered["pending"] = ["i1"]
    observer.ingest(recovered)
    result = observer.finish()
    assert not result["collision_coverage_complete"] and not result["identity_accounting_complete"]
    assert len(result["rejected_observations"]) == 1


def test_all_steps_explicit_zero_and_teleport_after_departure():
    observer = _observer()
    first = _native_frame(.05)
    first.update(loaded=["i1"], departed=["i1"], active=["i1"],
        native_departures={"i1": {"actual_departure_s": 0, "depart_delay_s": 0}})
    observer.ingest(first)
    second = _native_frame(.10); second["active"] = ["i1"]
    observer.ingest(second)
    assert observer.finish()["collision_coverage_complete"]
    third = _native_frame(.15, teleport_start=["i1"])
    with pytest.raises(RuntimeError, match="collision_or_teleport_stop"):
        execution.run_observation_loop({"run": {"duration_s": .05}}, _Backend([third]), observer,
            SimpleNamespace(append=lambda _: None), _Supervisor(), synthetic=False)


def _accounting_fixture():
    import xml.etree.ElementTree as ET
    observer = _observer()
    first = _native_frame(.05); first.update(loaded=["i1"], pending=["i1"])
    observer.ingest(first)
    second = _native_frame(.10); second["pending"] = ["i1"]
    observer.ingest(second)
    observer.observe_tripinfo(b'<tripinfos><tripinfo id="i1" depart="-1" arrival="-1"/></tripinfos>')
    data = b'<summary><step time="0" loaded="1" inserted="0" running="0" waiting="1" ended="0" arrived="0" discarded="0" collisions="0" teleports="0"/><step time="0.05" loaded="1" inserted="0" running="0" waiting="1" ended="0" arrived="0" discarded="0" collisions="0" teleports="0"/></summary>'
    declarations = {"i1": ET.fromstring('<vehicle id="i1" depart="0"/>')}
    return data, observer, declarations


def test_legitimate_pending_is_fully_accounted_without_FCD():
    from stage_0_5_acceptance_v3 import summary_identity_crosscheck
    data, observer, declarations = _accounting_fixture()
    result = summary_identity_crosscheck(data, observer.finish(), declarations, observer.frames,
        dict(duration_s=.1, internal_step_s=.05), {"i1"})
    assert result["passed"] and result["evidence"]["pending"] == 1
    assert result["evidence"]["actual_inserted"] == 0


def test_startup_loaded_getter_is_observed_and_not_lost_before_first_step():
    sim = _sim(lambda: 0)
    sim.getTime = lambda: 0
    sim.getLoadedIDList = lambda: ["i1"]
    frame = identity.collect_snapshot(SimpleNamespace(simulation=sim, vehicle=SimpleNamespace(getIDList=lambda: [])), initial=True)
    assert frame["loaded"] == ["i1"] and frame["departed"] is None
    observer = identity.IdentityObserver([dict(id="i1", depart_s=0)], step_s=.05)
    frame["pending"] = ["i1"]
    observer.ingest(frame)
    step = _native_frame(.05); step["pending"] = ["i1"]
    observer.ingest(step)
    assert observer.finish()["identity_accounting_complete"]
    assert observer.finish()["vehicles"]["i1"]["loaded_at"] == 0


@pytest.mark.parametrize("mutation", ["missing_step", "illegal_balance", "intermediate_mismatch", "discard_unresolved", "missing_tripinfo"])
def test_summary_identity_or_required_artifact_fault_cannot_pass(mutation):
    from stage_0_5_acceptance_v3 import summary_identity_crosscheck
    import xml.etree.ElementTree as ET
    data, observer, declarations = _accounting_fixture()
    tree = ET.fromstring(data)
    if mutation == "missing_step": tree.remove(tree[0])
    elif mutation == "illegal_balance": tree[0].set("inserted", "1")
    elif mutation == "intermediate_mismatch": tree[0].set("waiting", "0")
    elif mutation == "discard_unresolved":
        for step in tree:
            step.set("discarded", "1"); step.set("ended", "1"); step.set("waiting", "0")
    elif mutation == "missing_tripinfo": observer.rows["i1"]["tripinfo"] = None
    try:
        result = summary_identity_crosscheck(ET.tostring(tree), observer.finish(), declarations,
            observer.frames, dict(duration_s=.1, internal_step_s=.05), {"i1"})
    except ValueError:
        return
    assert not result["passed"]
    if mutation == "discard_unresolved":
        assert result["evidence"]["unresolved_discarded"] == 1
