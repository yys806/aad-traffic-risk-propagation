"""B0 contracts; no real trajectory or validation data needed."""
import copy
import pandas as pd
import pytest

from riskprop.stage_0_5_exploratory_response import (
    build_plan, validate_plan, validate_pair, local_mask, edge_exposure,
    input_accounting, local_density, verify_frozen, validate_reference_scope,
)
from riskprop.stage_0_5_sumo import compute_exposure, p2_boundary_cases, _synthetic_states, compute_sumo_measurements


def test_plan_is_bounded_and_has_no_state_dependent_speed_cap():
    p=build_plan()
    validate_plan(p)
    assert len(p["runs"])==23
    assert sum(r["phase"]=="phase1" for r in p["runs"])==6
    assert p["fixed"]["maxSpeed"]==27.78
    assert p["fixed"]["step_method_ballistic"] is True
    assert p["initialization"]["initial_vehicles"]==0
    assert p["loads"]["low"]["flow_veh_h_lane"]==pytest.approx(.75*1449.8181818181818)
    assert p["scientific_claim_eligible"] is False
    assert p["ready_to_start_stage_0_5_4b"] is False


def test_single_parameter_pairs_do_not_change_demand_seed_or_numerical_settings():
    p=build_plan()
    for r in p["runs"]:
        if r["phase"]=="phase2":
            base=next(b for b in p["runs"] if b["run_id"]==r["baseline_run_id"])
            validate_pair(base,r)
            bad=copy.deepcopy(r);bad["seed"]+=1
            with pytest.raises(ValueError): validate_pair(base,bad)


def test_plan_refuses_scientific_pass_or_hidden_speed_factor_changes():
    p=build_plan();p["scientific_claim_eligible"]=True
    with pytest.raises(ValueError): validate_plan(p)
    p=build_plan();p["fixed"]["speedFactor"]=.4
    with pytest.raises(ValueError): validate_plan(p)


def test_local_space_is_half_open_and_density_is_per_lane_km():
    s=pd.DataFrame(dict(edge_id=["main_1"]*4+["main_0"],
        longitudinal_position_m=[49.9,50,249.9,250,100]))
    assert local_mask(s).tolist()==[False,True,True,False,False]
    assert local_density(30,10)==pytest.approx(.5)  # 3veh-s/(10s*.6lane-km)


def test_demand_insertions_and_initial_population_are_separate():
    result=input_accounting(10,{"v1","v2"},{"v1"},{"v2"},initial_ids=set())
    assert result["scheduled_vehicles"]==10
    assert result["departed_vehicles"]==2 and result["unserved_at_end"]==8
    assert result["conservation_residual"]==0 and result["initial_departed"]==0


@pytest.mark.parametrize("name",list(p2_boundary_cases()))
def test_fast_edge_exposure_matches_existing_core_boundary_contract(name):
    case=p2_boundary_cases()[name]
    rows=[dict(time_s=t,**spec) for t,spec in zip(case["times"],case["specs"])]
    if "incarnation_switch_at" in case:
        for row in rows[case["incarnation_switch_at"]:]: row["incarnation_id"]="run|f|1"
    s=compute_sumo_measurements(_synthetic_states(rows))
    cadence=case.get("cadence_s",.1)
    actual=edge_exposure(s,cadence=cadence)
    expected=compute_exposure(s,recorded_observation_step_s=cadence)
    for key in ["reliable_following_exposure_s","p2_evaluable_following_exposure_s",
                "reliable_closing_exposure_s"]:
        assert actual[key]==pytest.approx(expected[key],abs=1e-8)


def test_frozen_inputs_reject_tampering(tmp_path):
    import hashlib
    f=tmp_path/"fixed.xml";f.write_bytes(b"fixed")
    bindings={"fixed.xml":hashlib.sha256(f.read_bytes()).hexdigest()}
    verify_frozen(tmp_path,bindings)
    f.write_bytes(b"changed")
    with pytest.raises(ValueError): verify_frozen(tmp_path,bindings)


def test_reference_scope_rejects_validation_summary():
    with pytest.raises(ValueError):
        validate_reference_scope({"windows":{"us101__0820_0835":{}}})


def test_empty_initialization_and_pending_diagnostics_keep_external_demand_separate():
    from riskprop.stage_0_5_exploratory_analysis import frame_diagnostics
    f=pd.DataFrame(dict(time_s=[.1,.2,.3],local_vehicles=[0,1,1],arrived_step=[0,0,1],
                        pending=[0,2,3],present=[1,2,1]))
    a=frame_diagnostics(f)
    assert a["first_local_vehicle_s"]==.2
    assert a["first_exit_s"]==.3 and a["first_pending_s"]==.2
    assert a["pending_max"]==3 and a["initial_vehicle_share"]==0
    assert a["pending_frame_fraction"]==pytest.approx(2/3)


def test_scheduler_stops_completed_worker_with_blocking_engineering_result():
    from riskprop.stage_0_5_exploratory_response import stop_after_attempt
    assert stop_after_attempt({"status":"completed","engineering_blockers":["persistent_unserved_demand"]})
    assert stop_after_attempt({"status":"failed"})
    assert not stop_after_attempt({"status":"completed","engineering_blockers":[]})


def test_executor_does_not_launch_next_run_after_completed_blocker(tmp_path,monkeypatch):
    import json
    import psutil
    import riskprop.stage_0_5_exploratory_response as module
    plan=build_plan();plan["source_code_sha256"]={}
    plan["runs"]=plan["runs"][:2]
    monkeypatch.setattr(module,"read_plan",lambda batch:plan)
    (tmp_path/"experiment_plan.json").write_text("{}")
    (tmp_path/"execution_ledger.json").write_text(json.dumps(dict(attempts=[],started_at_utc=None)))
    directory=tmp_path/"runs"/plan["runs"][0]["run_id"];directory.mkdir(parents=True)
    (directory/"summary.json").write_text(json.dumps(dict(engineering_blockers=["persistent_unserved_demand"],
        local_density_veh_km_lane=10,local_metrics={"speed_mps":{"mean":25}},full_network_p2={"events":0})))
    launched=[]
    class Worker:
        pid=123;returncode=0
        def __init__(self,args,**kwargs):launched.append(args)
        def poll(self):return 0
        def wait(self,timeout):return 0
    monkeypatch.setattr(module.subprocess,"Popen",Worker)
    monkeypatch.setattr(psutil,"Process",lambda pid:object())
    module.execute_phase(tmp_path,"phase1")
    result=json.loads((tmp_path/"execution_ledger.json").read_text())
    assert len(launched)==1 and len(result["attempts"])==1
    assert "engineering blocker" in result["stop_reason"]


def test_portable_export_accepts_frozen_plan_checksum_filename(tmp_path):
    import runpy
    from pathlib import Path
    exporter=runpy.run_path(str(Path(__file__).resolve().parents[1]/"scripts/export_project_evidence.py"))
    checksum=tmp_path/"PLAN_SHA256";checksum.write_text("a"*64+"\n")
    exporter["_validate_source"](checksum)
    for name in ["run_metrics.csv","time_bins_60s.csv","time_series_5s.csv"]:
        table=tmp_path/name;table.write_text("run_id,mean_speed\nfixture,20\n")
        exporter["_validate_source"](table)
    raw=tmp_path/"state.csv";raw.write_text("vehicle_id,time_s\nprivate,0\n")
    with pytest.raises(ValueError):exporter["_validate_source"](raw)


def test_portable_b0_evidence_retains_failures_and_never_passes_science():
    import json
    import hashlib
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/"evidence/results/RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1"
    if not root.exists(): pytest.skip("B0 portable result has not been finalized")
    read=lambda name:json.loads((root/name).read_text(encoding="utf-8"))
    audit=read("audit.json");plan=read("experiment_plan.json");runs=read("run_manifest.json")
    assert audit["scientific_claim_eligible"] is False
    assert audit["stage_0_5_gate"]=="pending_simulation_sample"
    assert audit["ready_to_start_stage_0_5_4b"] is False
    assert audit["protocol_lock_allowed"] is False and audit["stage_1_1_allowed"] is False
    assert audit["validation_window_rows_materialised"]==0
    assert audit["tolerances"]=="Tolerance Not Yet Justified"
    assert audit["energy_distance_upper_bound"]=="Not Identifiable"
    assert len(runs["attempts"])<=23 and len(runs["planned_runs"])==23
    assert hashlib.sha256((root/"experiment_plan.json").read_bytes()).hexdigest()==runs["plan_sha256"]
    validate_plan(plan)
    for f in read("manifest.json")["files"]:
        assert hashlib.sha256((root/f["path"]).read_bytes()).hexdigest()==f["sha256"]
    params=read("parameter_response_matrix.json")
    assert params["no_best_parameter_selected"]
    assert all(p["demand_sha_equal"] for p in params["pairs"])
    # Blocking parameter responses must remain visible alongside successful pairs.
    assert any("persistent_unserved_demand" in p["engineering_blockers"] for p in params["pairs"])
