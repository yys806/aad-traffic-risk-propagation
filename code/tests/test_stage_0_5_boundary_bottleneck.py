"""Audited B1 tests: synthetic fixtures and two-window aggregate capsule only."""
import hashlib
import json
from pathlib import Path
import os
import sys

import pytest

from riskprop.stage_0_5_b1_isolation import read_reference, path_access
from riskprop.stage_0_5_boundary_bottleneck import classify_result, execute_commands, arrival_times
from riskprop.stage_0_5_sumo import p2_boundary_cases,_synthetic_states,compute_sumo_measurements,compute_exposure,run_p2_boundary_matrix
from riskprop.stage_0_5_exploratory_response import edge_exposure


def reference(tmp_path, **changes):
    payload=dict(kind="two_window_aggregate",windows={"us101__0750_0805":{},"us101__0805_0820":{}})
    payload.update(changes)
    f=tmp_path/"calibration_reference.json";f.write_text(json.dumps(payload))
    return {"calibration_reference":dict(path=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),role="calibration",kind="two_window_aggregate")}


def test_allow_pinned_two_window_reference(tmp_path):
    m=reference(tmp_path)
    assert len(read_reference(tmp_path,m,"calibration_reference",role="calibration")["windows"])==2


@pytest.mark.parametrize("source,role",[("us101__0820_0835","calibration"),("locked_holdout","calibration"),("unknown","calibration"),("calibration_reference","validation"),("calibration_reference","engineering")])
def test_roles_and_unknown_sources_refused_before_any_data_read(tmp_path,source,role):
    with pytest.raises(PermissionError):read_reference(tmp_path,{},source,role=role)


def test_sha_mismatch_refused(tmp_path):
    m=reference(tmp_path);m["calibration_reference"]["sha256"]="0"*64
    with pytest.raises(PermissionError):read_reference(tmp_path,m,"calibration_reference",role="calibration")


def test_full_source_cannot_masquerade_as_calibration(tmp_path):
    for changes in [dict(kind="full_source_events"),dict(windows={"us101__0750_0805":{},"us101__0805_0820":{},"us101__0820_0835":{}}),dict(extra_source="locked_holdout"),dict(events=[{"source":"foreign"}])]:
        m=reference(tmp_path,**changes)
        with pytest.raises(PermissionError):read_reference(tmp_path,m,"calibration_reference",role="calibration")


def test_manifest_role_cannot_be_overridden_by_caller(tmp_path):
    m=reference(tmp_path);m["calibration_reference"]["role"]="validation"
    with pytest.raises(PermissionError):read_reference(tmp_path,m,"calibration_reference",role="calibration")


def test_entry_escape_refused(tmp_path):
    m=reference(tmp_path);m["calibration_reference"]["path"]="../calibration_reference.json"
    with pytest.raises(PermissionError):read_reference(tmp_path,m,"calibration_reference",role="calibration")


def test_path_guard_denies_project_historical_data_even_when_named_summary(tmp_path):
    capsule=tmp_path/"capsule";runtime=tmp_path/"runtime";project=tmp_path/"project"
    assert path_access(capsule/"inputs/x.json",capsule,[runtime],write=False)
    assert path_access(runtime/"pandas/a.py",capsule,[runtime],write=False)
    assert not path_access(project/"code/outputs/formal/calibration/summary.json",capsule,[runtime],write=False)
    assert not path_access(project/"dataset/locked_holdout.json",capsule,[runtime],write=False)
    assert not path_access(runtime/"x.py",capsule,[runtime],write=True)


def test_windows_audit_event_with_implicit_executable_is_parsed():
    from riskprop.stage_0_5_b1_isolation import command_parts
    exe,args=command_parts(None,'"C:\\Program Files\\Python\\python.exe" "D:\\capsule\\worker.py"')
    assert exe==r'C:\Program Files\Python\python.exe'
    assert args[-1]==r'D:\capsule\worker.py'


def test_capsule_bootstrap_avoids_ambient_site_paths():
    if not os.environ.get("AAD_B1_CAPSULE"):
        pytest.skip("bootstrap contract is exercised by the dedicated -S capsule preflight")
    from riskprop.stage_0_5_b1_isolation import _ACTIVE
    assert sys.flags.no_site and _ACTIVE["python_no_site"]
    cap=Path(os.environ["AAD_B1_CAPSULE"])
    policy=json.loads((cap/"isolation_policy.json").read_text())
    assert all(path_access(p,cap,policy["runtime_read_roots"],write=False) for p in sys.path)
    assert not _ACTIVE["denied"]


def test_synthetic_parquet_metadata_roundtrip_under_guard(tmp_path):
    import pyarrow
    import pandas as pd
    frame=pd.DataFrame({"vehicle_id":["synthetic"],"time_s":[.1],"speed_mps":[12.]})
    path=tmp_path/"synthetic.parquet"
    frame.to_parquet(path,index=False)
    pd.testing.assert_frame_equal(pd.read_parquet(path),frame)
    if os.environ.get("AAD_B1_CAPSULE"):
        from riskprop.stage_0_5_b1_isolation import _ACTIVE
        assert not _ACTIVE["denied"]


def test_arrival_contrast_preserves_count_identity_order_and_interval():
    a=arrival_times(1648,600,"uniform");b=arrival_times(1648,600,"platoon")
    assert len(a)==len(b) and len(a)>800
    assert all(0<t<600 for t in b)
    assert all(x<=y for x,y in zip(b,b[1:]))
    assert max(t%30 for t in b)<15.1
    assert a!=b


@pytest.mark.parametrize("kind,status",[("valid","completed_valid"),("queue","completed_with_diagnostic_warning"),("blocker","completed_with_engineering_blocker"),("failed","failed")])
def test_exit_success_is_not_engineering_acceptance(kind,status):
    blockers=["conservation"] if kind=="blocker" else []
    assert classify_result(0 if kind!="failed" else 2,True,blockers,["inside_queue"] if kind=="queue" else [])==status


def test_missing_output_is_failure():
    assert classify_result(0,False,[],[])=="failed"


@pytest.mark.parametrize("name",list(p2_boundary_cases()))
def test_p2_exposure_preserves_core_identity_and_cadence_contract(name):
    case=p2_boundary_cases()[name]
    rows=[dict(time_s=t,**s) for t,s in zip(case["times"],case["specs"])]
    if "incarnation_switch_at" in case:
        for row in rows[case["incarnation_switch_at"]:]:row["incarnation_id"]="run|f|1"
    frame=compute_sumo_measurements(_synthetic_states(rows));cadence=case.get("cadence_s",.1)
    actual=edge_exposure(frame,cadence=cadence);expected=compute_exposure(frame,recorded_observation_step_s=cadence)
    for key in ["reliable_following_exposure_s","p2_evaluable_following_exposure_s","reliable_closing_exposure_s"]:
        assert actual[key]==pytest.approx(expected[key],abs=1e-8)


def test_p2_event_identity_confirmation_and_closing_epsilon_boundary_matrix():
    cases=run_p2_boundary_matrix()
    assert len(cases)==16 and all(c["case_matches_expectation"] for c in cases)


@pytest.mark.parametrize("fault",["blocker","exit","missing","timeout","memory","disk","hash"])
def test_synthetic_worker_stops_all_following_commands(tmp_path,fault):
    first=dict(run_id="first",synthetic=fault)
    if fault=="hash":
        f=tmp_path/"frozen.txt";f.write_bytes(b"fixed")
        first["verify_files"]={str(f):"0"*64}
    result=execute_commands(tmp_path,[first,dict(run_id="must_not_start",synthetic="valid")],
        synthetic=True,limits=dict(per_run_wall_s=.4 if fault=="timeout" else 8,memory_bytes=60*1024**2,artifact_bytes=500_000,batch_wall_s=15))
    assert result["runs"][0]["status"] in ["failed","completed_with_engineering_blocker"]
    assert result["runs"][1]["status"]=="not_attempted"
    assert not (tmp_path/"must_not_start").exists()
    if fault in ["timeout","memory","disk","hash"]:assert result["runs"][0]["failure"]==fault


def test_synthetic_valid_warning_continue_and_cancellation_is_explicit(tmp_path):
    r=execute_commands(tmp_path,[dict(run_id="a",synthetic="valid"),dict(run_id="b",synthetic="warning")],synthetic=True,
        limits=dict(per_run_wall_s=5,memory_bytes=200*1024**2,artifact_bytes=1_000_000,batch_wall_s=20))
    assert [x["status"] for x in r["runs"]]==["completed_valid","completed_with_diagnostic_warning"]
    r=execute_commands(tmp_path/"cancelled",[dict(run_id="x",synthetic="valid")],synthetic=True,cancelled=True,
        limits=dict(per_run_wall_s=5,memory_bytes=200*1024**2,artifact_bytes=1_000_000,batch_wall_s=20))
    assert r["runs"][0]["status"]=="cancelled"
