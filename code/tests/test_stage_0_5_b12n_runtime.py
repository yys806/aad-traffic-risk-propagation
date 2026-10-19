"""Shared vs scenario severity and scope guards; synthetic only."""
import ast
import inspect
import json
import pytest
from riskprop.stage_0_5_b12n_runtime import global_stop_reason,freeze_integration,dispatch


def summary(**changes):
    r=dict(global_blockers=[],scenario_blockers=[],engineering_blockers=[],evidence_insufficient=[]);r.update(changes);return r


def test_C_queue_insufficiency_does_not_block_independent_D_path_duty():
    entry=dict(status="completed_with_diagnostic_warning")
    assert global_stop_reason(entry,summary(evidence_insufficient=["entry_spillback_insufficient"])) is None


def test_scenario_blocker_and_global_blocker_are_distinct():
    entry=dict(status="completed_with_engineering_blocker")
    assert global_stop_reason(entry,summary(scenario_blockers=["C_queue_domain"],engineering_blockers=["C_queue_domain"])) is None
    assert global_stop_reason(entry,summary(global_blockers=["exact_displacement_violation"],engineering_blockers=["exact_displacement_violation"]))


@pytest.mark.parametrize("entry,s",[(dict(status="failed"),summary()),(dict(status="completed_valid"),None),
                                  (dict(status="completed_valid"),{}),
                                  (dict(status="completed_with_engineering_blocker"),summary(engineering_blockers=["unknown"]))])
def test_unknown_failure_scope_is_global(entry,s):
    assert global_stop_reason(entry,s)


def test_unattempted_run_does_not_invent_an_error():
    assert global_stop_reason(dict(status="not_attempted"),None) is None


def test_integration_cannot_freeze_without_independent_micro_checkpoint(tmp_path):
    (tmp_path/"micro_checkpoint.json").write_text(json.dumps(dict(integration_allowed=False)))
    with pytest.raises(PermissionError):freeze_integration(tmp_path)
    assert not (tmp_path/"integration_C_plan.json").exists()


def test_no_main_matrix_dispatch(tmp_path):
    with pytest.raises(PermissionError,match="No main matrix"):
        dispatch(tmp_path,tmp_path,"phase1")


def test_worker_is_read_only_for_vehicle_control():
    from riskprop import stage_0_5_b12n_worker as m
    tree=ast.parse(inspect.getsource(m))
    calls=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            target=ast.unparse(node.func.value)
            if target.endswith("vehicle"):calls.append(node.func.attr)
    assert calls
    assert all(not c.startswith(("set","add","remove","change","move","replace","resume","reroute")) for c in calls)


def test_frozen_plan_rejects_binary_change_and_excess_duration(tmp_path,monkeypatch):
    import hashlib
    import riskprop.stage_0_5_b12n_runtime as m
    fake=tmp_path/"synthetic.exe";fake.write_bytes(b"original")
    monkeypatch.setattr(m,"_sumo_binary",lambda:str(fake))
    (tmp_path/"preparation_manifest.json").write_text(json.dumps(dict(sumo_binary_sha256=m.sha(fake))))
    plan=dict(P2_calculated=False,main_matrix_allowed=False,frozen_files={},runs=[dict(kind=k,duration_s=30.,seed=20261019) for k in ["N1","N2","N3"]])
    def save():
        p=tmp_path/"micro_plan.json";p.write_text(json.dumps(plan));(tmp_path/"micro_plan.json.sha256").write_text(m.sha(p))
    save();assert m.load_plan(tmp_path,"micro_plan.json")["runs"][0]["duration_s"]==30.
    fake.write_bytes(b"changed")
    with pytest.raises(PermissionError,match="binary SHA"):m.load_plan(tmp_path,"micro_plan.json")
    fake.write_bytes(b"original");plan["runs"][0]["duration_s"]=31.;save()
    with pytest.raises(PermissionError,match="duration"):m.load_plan(tmp_path,"micro_plan.json")
