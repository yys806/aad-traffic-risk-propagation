"""B1.1 descriptive packaging; does not change frozen measurement rules."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import shutil

from .stage_0_5_stopping_contract import audit_edge
from .stage_0_5_queue_contract import observe_queue,qualify_series

RESULT_ID="RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1"


def read(path):return json.loads(path.read_text(encoding="utf-8"))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json","SHA256SUMS"])
    large=[p.name for p in files if p.stat().st_size>256*1024]
    if large:raise ValueError("portable file size limit: "+str(large))
    write(out/"manifest.json",dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]))
    files.append(out/"manifest.json")
    (out/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in files),encoding="utf-8",newline="\n")


def analytic_matrix():
    specs=[("constant",10,10,.1,1,None),("acceleration",10,10.2,.1,1.01,None),
        ("deceleration_no_stop",10,9.8,.1,.99,None),("stop_at_end",.2,0,.05,.005,0.),
        ("stop_early",.2,0,.1,.005,-.2),("already_stopped",0,0,.1,0,None),
        ("restart",0,.2,.1,.01,None),("small_speed",1e-10,2e-10,.1,1.5e-11,None),
        ("same_physics_step02",.2,0,.2,.005,-.6),("terminal_zero_without_latent",.2,0,.1,.005,None)]
    result=[]
    for name,v0,v1,step,truth,raw in specs:
        a=dict(run_id="analytic",vehicle_id="v",incarnation_id="analytic|v|0",time_s=1.,position_m=20.,speed_mps=v0,edge_id="e",lane_id="e_0")
        b=dict(a,time_s=1+step,position_m=20+truth,speed_mps=v1)
        r=audit_edge(a,b,step,signed_candidate=None if raw is None else dict(value=raw,origin="analytic_input"))
        result.append(dict(case=name,independent_displacement_truth_m=truth,result=r))
    for key,val in [("incarnation_id","different"),("lane_id","e_1"),("edge_id","next"),("time_s",1.2)]:
        a=dict(run_id="analytic",vehicle_id="v",incarnation_id="analytic|v|0",time_s=1.,position_m=20.,speed_mps=10.,edge_id="e",lane_id="e_0")
        b=dict(a,time_s=1.1,position_m=21.);b[key]=val
        result.append(dict(case="discontinuity_"+key,independent_expectation="not_evaluable; do not subtract lane coordinates",result=audit_edge(a,b,.1)))
    return result


def finalize(batch):
    # Import the frozen entry script without executing its CLI.
    import importlib.util
    entry=batch/"runtime/code/scripts/run_stage_0_5_stopping_spillback.py"
    spec=importlib.util.spec_from_file_location("b11_entry",entry);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    plan=module.read_plan(batch);ledger=read(batch/"execution_ledger.json")
    if not ledger["closed"]:raise ValueError("analysis requires a closed micro batch")
    out=batch/"summary";out.mkdir(exist_ok=True)
    for name in ["experiment_plan.json","PLAN_SHA256","execution_ledger.json","data_isolation_preflight.json","official_source_manifest.json",
        "historical_source_manifest.json","displacement_branch_contract.json","queue_observation_contract.json","synthetic_queue_truth.json","micro_fixture_manifest.json","source_staging_manifest.json"]:
        shutil.copyfile(batch/name,out/name)
    source=read(batch/"official_source_manifest.json");locations={}
    needles={"microsim_MSVehicle.cpp":["MSVehicle::getDeltaPos(","MSVehicle::updateState(","myAcceleration = SPEED2ACCEL(MAX2", "myState.mySpeed = MAX2(vNext", "continues with constant accel"],
        "microsim_MSVehicle.h":["double getAcceleration() const","SUMOTime getLastActionTime() const"],
        "libsumo_Vehicle.cpp":["Vehicle::getSpeed(","Vehicle::getAcceleration(","Vehicle::getLastActionTime(","Vehicle::setAcceleration("],
        "utils_common_SUMOTime.h":["#define SPEED2DIST", "#define ACCEL2SPEED", "#define SPEED2ACCEL"]}
    for name,patterns in needles.items():
        text=(batch/"official_source"/name).read_text(encoding="utf-8").splitlines()
        locations[name]={pattern:next(i+1 for i,line in enumerate(text) if pattern in line) for pattern in patterns}
    write(out/"stopping_source_audit.json",dict(source_files=source,function_line_locations=locations,
        reported_version="SUMO1.26.0",pinned_commit="fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3",
        findings=dict(candidate_velocity="signed internal vNext is allowed negative in ballistic",
            public_speed="max(vNext,0)",public_acceleration="(max(vNext,0)-v0)/dt, a step-mean; not the hidden braking acceleration",
            exact_motion="dx=(v0+vNext)*dt/2 if vNext>=0",
            exact_stop="a=(vNext-v0)/dt<0; t_stop=-v0/a; dx=-v0^2/(2a) if vNext<0",
            euler="dx=max(vNext,0)*dt; not the ballistic contract",
            observability="speed and mean acceleration alone are non-injective for stopping; displacement-derived latent speed is circular",
            possible_extension="non-action-step source continues previous acceleration; future lastActionTime/previous-acceleration probe may support a restricted independent reconstruction, not validated here"),
        binary_source_build_equivalence="not rebuilt/proven; installed release label and fixture behaviour checked",
        historical_C_residual_attribution="Unresolved; no historical anomalous edge trace, no old C state read"))
    write(out/"displacement_test_matrix.json",dict(cases=analytic_matrix(),tolerance_m=1e-6,
        truth_origin="independent constant-acceleration areas and predefined discontinuities; same cases as frozen test source",
        exact_real_stop_equivalence="Pending Numerical Equivalence"))
    rows=[];branches={};old_residuals=[]
    for run in ledger["runs"]:
        path=batch/"runs"/run["run_id"]/"summary.json"
        if not path.exists():rows.append(run);continue
        s=read(path);rows.append(dict(execution=run,measurement=s))
        old_residuals+=s["old_trapezoid_stop_residuals_m"]
        for name,b in s["audit"]["branches"].items():
            a=branches.setdefault(name,dict(checks=0,exact=0,bounded=0,not_evaluable=0,max_abs_residual_m=None))
            a["checks"]+=b["checks"];a["exact"]+=b["exact_evaluable"];a["bounded"]+=b["bounded_evaluable"];a["not_evaluable"]+=b["not_evaluable"]
            if b["max_abs_residual_m"] is not None:a["max_abs_residual_m"]=max(a["max_abs_residual_m"] or 0,b["max_abs_residual_m"])
    exact=sum(b["exact"] for b in branches.values());edges=sum(b["checks"] for b in branches.values())
    write(out/"micro_sumo_numerical_audit.json",dict(runs=rows,branches=branches,total_observed_adjacent_edges=edges,
        exact_evaluable_edges=exact,exact_fraction=exact/edges if edges else None,all_active_vehicle_edges_screened=True,
        observed_stop_old_trapezoid_residuals_m=old_residuals,
        exact_normal_check_tolerance_m=1e-6,exact_stopping_equivalence="Pending Numerical Equivalence",
        old_C_explained_by_fixture=False,independent_fixture_only=True,no_P2_computation=True))
    config=read(batch/"queue_observation_contract.json");cases=read(batch/"synthetic_queue_truth.json")
    tests=[];comparison={};full=[]
    for method in ["legacy_grid","grid_candidate","vehicle_graph"]:
        totals=dict(queue_false_positive=0,queue_false_negative=0,component_count_mismatch=0,
            front_unknown=0,spillback_false_positive=0,spillback_false_negative=0,spillback_unknown=0)
        for case in cases:
            observations=[observe_queue(f,config,method) for f in case["frames"]]
            q=qualify_series(observations,config);last=observations[-1];truth=case["truth"]
            detected=bool(last["components"])
            totals["queue_false_positive"]+=detected and not truth["queue"]
            totals["queue_false_negative"]+=not detected and truth["queue"]
            totals["component_count_mismatch"]+=len(last["components"])!=truth["components"]
            predicted=q["entry_spillback_supported"]
            totals["spillback_unknown"]+=predicted is None
            if truth["spillback"] is not None:
                totals["spillback_false_positive"]+=predicted is True and not truth["spillback"]
                totals["spillback_false_negative"]+=predicted is False and truth["spillback"]
            totals["front_unknown"]+=any(c["upstream_boundary_m"] is None for c in last["components"])
            tests.append(dict(case=case["id"],method=method,independent_truth=truth,observed_component_count=len(last["components"]),
                components=last["components"],qualification=q))
            full.append(dict(case=case["id"],method=method,observations=observations))
        comparison[method]=totals
    (batch/"analysis_work").mkdir(exist_ok=True);write(batch/"analysis_work/full_synthetic_observation_layers.json",full)
    write(out/"synthetic_queue_test_matrix.json",dict(cases=tests,independent_case_count=len(cases),
        truth_frozen_before_micro=True,universal_real_world_validity=False))
    write(out/"old_new_method_comparison.json",dict(method_counts=comparison,
        scope="old instantaneous pooled50m/2vehicle spatial detector versus new candidates; common prospective qualification used for comparison",
        original_B1_last60s_25percent_acceptance_not_recomputed=True,
        limitations=["grid candidate still merges separate groups inside one cell","sparse front legacy point is50m versus synthetic physical rear40m",
            "zero false negatives in this finite test set is not proof of necessity/sufficiency","vehicle graph requires exact lane/order/length/gap and conservatively refuses unverified topology"] ))
    write(out/"spillback_qualification_candidates.json",dict(config=config,states=["No On-Road Queue","On-Road Queue Observed","Upstream Queue Extension Observed","Inlet-Adjacent Queue Observed","Entry Spillback Supported","Evidence Insufficient"],
        observation="raw position/speed/lane/incarnation/order/gap/density/stopped/arrival/exit/pending separated from qualification",
        entry_support_requires=["downstream anchored physical queue in same lane/path","fully observed inlet support","continuous inlet duration candidate2s",
            "pending due demand","independently supplied physical entry-space evidence","valid arrival manifest/service context/identity/coordinate/time"],
        no_temporal_or_empty_cell_imputation=True,no_default_cross_lane_merge=True,
        absence_of_queue_qualification="mechanism finding or warning, not itself a physics failure",
        quality_error="measurement invalid; can be an engineering blocker under a future approved plan",
        future_thresholds_need_approval=True))
    history_manifest=read(batch/"historical_source_manifest.json")
    for name,entry in history_manifest.items():
        if sha(batch/"inputs/history"/name)!=entry["sha256"]:raise ValueError("historical metadata changed")
    historical=read(batch/"inputs/history/run_manifest.json")
    C=next(r for r in historical["runs"] if r["run_id"]=="b1_C_s20261019")
    D=next(r for r in historical["runs"] if r["run_id"]=="b1_D_s20261019")
    if C["status"]!="completed_with_engineering_blocker" or D["status"]!="not_attempted" or set(C["blockers"])!={"runtime_settings","persistent_external_demand_without_documented_spillback"}:raise ValueError("historical status changed")
    write(out/"historical_b1_status_preservation.json",dict(C=C,D=D,metadata_bindings=history_manifest,
        original_B1_package_git_tree=read(batch/"preparation_manifest.json")["historical_git_tree"],
        old_C_state_read=False,historical_reclassification=False,interpretation="Retrospective Diagnostic Interpretation only",
        b0_task_data_isolation_accepted=False,b0_validation_window_rows_materialised="Unknown"))
    write(out/"future_experiment_preconditions.json",dict(numerical_ready=dict(exact_normal_motion=True,
        stopping_interval_only=True,exact_stopping=False,status="Pending Numerical Equivalence"),
        queue_ready=dict(candidate_software_tested=True,thresholds_scientifically_approved=False,unverified_topology_requires_insufficient=True),
        data_isolation_ready="scoped Python capsule, not complete OS monitoring",stop_control_ready="B1 synthetic stop regressions passed; no micro blocker occurred",
        historical_states_preserved=True,B1_2_authorized=False,
        next_recommended_task="minimal independent stopping-branch observable probe (signed vNext or a source-justified non-action-step reconstruction) before unconditional B1.2 admission",
        researcher_decisions=["exact versus bounded stopping admission policy; no treating bounded as exact Pass",
            "queue gap/low-speed/grid/duration/inlet/anchor/uncertainty scope","observation insufficiency: warning or blocker by purpose",
            "B1.2 independent network/supply/seeds/duration/matrix/budget/stops"],
        not_automatically_started=["B1.2","formal0.5.4-B","Stage0.5.5","Protocol Lock","StageI/II"]))
    write(out/"audit.json",dict(result_id=RESULT_ID,mode="independent_measurement_contract_only",stage_0_5_gate="pending_simulation_sample",
        scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,
        protocol_lock_allowed=False,stage_1_1_allowed=False,tolerances="Tolerance Not Yet Justified",energy_distance_upper_bound="Not Identifiable",
        numerical_exact_stopping="Pending Numerical Equivalence",historical_C=C["status"],historical_D=D["status"],
        historical_B1_overwritten=False,B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised="Unknown",
        no_real_data_inputs=True,old_C_states_read=False,raw_NGSIM_read=False,formal_P2_changed=False,
        micro_runs_attempted=sum(r["status"]!="not_attempted" for r in ledger["runs"]),maximum_micro_runs=4,maximum_duration_s=30,
        old_B1_C_rerun=False,old_D_run=False,B1_second_seed_run=False,B1_2_run=False,formal_calibration_run=False))
    pre=read(batch/"preflight.json");logs=[read(p) for p in sorted(batch.glob("test_*.json"))]
    write(out/"test_record.json",dict(preflight=pre,all_preflight_attempts=logs,
        audited_tests=["test_stage_0_5_stopping_contract.py","test_stage_0_5_queue_contract.py","test_stage_0_5_boundary_bottleneck.py"],
        tests_scope="synthetic fixtures/B1 named metadata and approved code only; no old traffic data",
        root_full_pytest_run=False,full_regression="Pending pure Git clone",data_related_skips_not_passes=True))
    write(out/"runtime_budget_audit.json",dict(plan_limits=plan["limits"],elapsed_wall_s=ledger["elapsed_wall_s"],
        worker_wall_s=sum(r.get("wall_s",0) for r in ledger["runs"]),peak_tree_rss_bytes=max(r.get("peak_sampled_tree_rss_bytes",0) for r in ledger["runs"]),
        output_bytes=sum(r.get("bytes",0) for r in ledger["runs"]),no_resource_exceedance=True,all_attempts_retained=True))
    bundle={name:dict(sha256=digest,bytes=(batch/name).stat().st_size,gzip_base64=base64.b64encode(gzip.compress((batch/name).read_bytes(),mtime=0)).decode())
        for name,digest in plan["frozen_files"].items() if name.startswith("inputs/") and Path(name).suffix in [".xml",".sumocfg"]}
    write(out/"micro_input_bundle.json",dict(files=bundle,encoding="exact gzip+base64 engineering XML bytes; no raw states or real data"))
    accesses=[dict(entry=p.name,**read(p)) for p in sorted((batch/"access_logs").glob("*.json"))]
    write(out/"controlled_access_audit.json",dict(entries=accesses,unexpected_denials=sum(len(a["denied"]) for a in accesses),
        expected_synthetic_path_denials=3,os_native_complete_monitoring=False))
    write(out/"provenance.json",dict(result_id=RESULT_ID,base_commit=read(batch/"preparation_manifest.json")["base_commit"],
        plan_sha256=sha(batch/"experiment_plan.json"),executed_source_and_input_sha256=plan["frozen_files"],
        external_code_sources=source,analysis_source_sha256=sha(Path(__file__)),
        historical_metadata_only=history_manifest,no_old_C_detail_access_after_freeze=True))
    seal(out)
    print(json.dumps(dict(exact_edges=exact,total_edges=edges,branches=branches,queue_comparison=comparison)),flush=True)
