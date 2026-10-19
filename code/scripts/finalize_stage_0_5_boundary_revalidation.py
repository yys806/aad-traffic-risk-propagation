"""Package the closed B1.2 precheck. Never executes SUMO or changes frozen code."""
from pathlib import Path
import argparse
import base64
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

RESULT_ID="RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2"


def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json","SHA256SUMS"])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError("portable size limit")
    write(out/"manifest.json",dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]))
    files.append(out/"manifest.json")
    (out/"SHA256SUMS").write_text("".join(f'{sha(p)}  {p.name}\n' for p in files),encoding="utf-8",newline="\n")


def stage(repo,batch):
    plan=read(batch/"integration_plan.json")
    if not read(batch/"integration_ledger.json")["closed"]:raise ValueError("closed batch required")
    if read(batch/"observability_integration_audit.json")["B1_2_MAIN_MATRIX_ALLOWED"]:raise ValueError("this closure requires blocked admission")
    out=batch/"summary";out.mkdir(exist_ok=True)
    for name in ["integration_plan.json","integration_ledger.json","numerical_admission_policy.json","queue_integration_contract.json",
                 "coordinate_support_audit.json","data_isolation_preflight.json","execution_guard_audit.json","source_staging_manifest.json",
                 "source_manifest.json","preparation_manifest.json","observability_integration_audit.json","queue_integration_test_matrix.json",
                 "local_global_accounting_audit.json","empty_network_prechecks.json"]:shutil.copyfile(batch/name,out/name)
    shutil.copyfile(batch/"integration_plan.json",out/"experiment_plan.json")
    (out/"PLAN_SHA256").write_text(sha(out/"experiment_plan.json")+"  experiment_plan.json\n",encoding="utf-8")
    old=batch.parent/"stage_0_5_boundary_revalidation_b12_v1"
    shutil.copyfile(old/"integration_plan.json",out/"prior_unexecuted_plan.json")
    shutil.copyfile(old/"integration_ledger.json",out/"prior_unexecuted_ledger.json")
    files=[];generated=[]
    for name,digest in plan["frozen_files"].items():
        if sha(batch/name)!=digest:raise ValueError("frozen file changed: "+name)
        if not name.startswith("runtime/code/"):continue
        raw=(batch/name).read_bytes();relative=name.removeprefix("runtime/")
        if relative in ["code/pytest.ini","code/src/sitecustomize.py","code/src/riskprop/__init__.py"]:
            generated.append(dict(path=name,sha256=digest,base64=base64.b64encode(raw).decode()));continue
        canonical=raw.replace(b"\r\n",b"\n")
        transform="none" if canonical==raw else "canonical LF to original CRLF"
        if transform!="none" and canonical.replace(b"\n",b"\r\n")!=raw:raise ValueError("source newline transform")
        files.append(dict(path=relative,frozen_sha256=digest,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),byte_transform=transform))
    write(out/"git_source_binding_audit.json",dict(files=files,generated_runtime=generated,source_of_bytes="frozen v2 capsule; canonical LF compared to Git",new_runs=0))
    bundle={}
    for name,digest in plan["frozen_files"].items():
        if name.startswith("inputs/") and Path(name).suffix in [".xml",".sumocfg",".json"]:
            raw=(batch/name).read_bytes();bundle[name]=dict(bytes=len(raw),sha256=digest,gzip_base64=base64.b64encode(gzip.compress(raw,mtime=0)).decode())
    write(out/"engineering_input_bundle.json",dict(files=bundle,no_traffic_states=True))
    sources=read(batch/"postrun_source_audit/source_manifest.json")
    sources["config.h.cmake"]=read(batch/"postrun_source_audit/config_source_manifest.json")
    write(out/"official_source_manifest.json",sources)
    # Retain only small source facts, never the full external source or raw SUMO
    # tables in Git. Line locations refer to SHA-verified raw files.
    finding=dict(pinned_commit="fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3",sources=sources,
                 locations=dict(MSVehicle_cpp=dict(epsilon_definition=127,nonaction_continuation=4600,near_zero_snap=4644,zero_assignment=4645),
                                config_h_cmake=dict(numerical_epsilon=219,position_epsilon=222),SUMOTime_h=dict(seconds_step=42)),
                 numerical_epsilon=.001,position_epsilon_m=.1,internal_step_s=.05,near_zero_threshold_mps=5e-6,
                 source_effect="Post-continuation vNext may snap to zero before updateState; conditional on private stop context",
                 status="Source-consistent explanation; installed private branch not instrumented",post_stop_only=True,extra_SUMO_runs=0)
    write(out/"near_zero_source_audit.json",finding)
    report=repo/"docs/STAGE_0_5_TASK_0_5_4B1_2_BOUNDARY_BOTTLENECK_REVALIDATION.md"
    shutil.copyfile(report,out/"report.md")
    # Stage independent postprocessing as an extra file; no frozen file changed.
    entry=batch/"analysis_entry.py";shutil.copyfile(Path(__file__).resolve(),entry)
    write(batch/"analysis_source_manifest.json",dict(source="code/scripts/finalize_stage_0_5_boundary_revalidation.py",sha256=sha(entry),report_sha256=sha(report)))
    return subprocess.call([sys.executable,"-S",str(entry),str(batch),"--render"])


def render(batch):
    sys.path.insert(0,str(batch/"runtime/code/src"))
    from riskprop.stage_0_5_b1_isolation import install_guard
    audit=install_guard(batch)
    try:
        os.environ["MPLCONFIGDIR"]=str(batch/"runtime_cache/matplotlib")
        (batch/"runtime_cache/matplotlib").mkdir(parents=True,exist_ok=True)
        import pandas as pd
        import numpy as np
        from riskprop.stage_0_5_b12_runtime import SCIENCE,BOUNDARIES
        out=batch/"summary";ledger=read(batch/"integration_ledger.json");plan=read(batch/"integration_plan.json")
        spec=plan["runs"][0];run=batch/"runs"/spec["run_id"];s=read(run/"summary.json");n=s["numerical"]
        write(out/"numerical_branch_coverage.json",n)
        q=read(run/"queue_snapshots.json");f=pd.read_csv(run/"traffic_frames.csv");states=pd.read_parquet(run/"state.parquet")
        anomaly=n["examples"]["candidate_terminal_speed_inconsistent"];a=anomaly["before"];z=anomaly["after"]
        predicted=a["speed_mps"]+a["acceleration_mps2"]*.05;dx=z["position_m"]-a["position_m"]
        conflict=dict(Documented_Intent="Nonaction final signed vNext always equals v0+a_pub_start*h without vehicle control",
                      Actual_Implementation="Official source has conditional near-zero snap after continuation; actual nonaction positive candidate != reported zero speed",
                      Evidence=dict(anomaly=anomaly,presnap_prediction_mps=predicted,reported_terminal_mps=z["speed_mps"],
                                    measured_dx_m=dx,hypothetical_post_snap_dx_m=.5*a["speed_mps"]*.05,
                                    hypothesis_residual_m=dx-.5*a["speed_mps"]*.05,not_retrospective_acceptance=True),
                      Affected_Files=["stage_0_5_stopping_observability.py::reconstruct_signed_vnext","stage_0_5_b12_observation.py::audit_transition"],
                      Conflict="Previous observed micro domain does not cover all near-zero postprocessing; thresholds unchanged",
                      Status="Awaiting Researcher Decision",no_formula_or_policy_change_after_stop=True)
        write(out/"research_conflict.json",conflict)
        main=[]
        for seed in [20261019,20261020]:
            for cond in ["A","B","C","D"]:main.append(dict(run_id=f"b12_{cond}_s{seed}",condition=cond,seed=seed,
                  status="not_attempted",reason="B1.2 numerical integration blocker; main plan never frozen",network_hash=None,boundary_hash=None,
                  demand_hash=None,fleet_hash=None,duration_s=600,planned_vehicles_candidate=823))
        write(out/"execution_ledger.json",dict(closed=True,integration=ledger["runs"],main_matrix=main,main_plan_frozen=False,
              stop_reason=ledger["stop_reason"],extra_run_after_blocker=False))
        write(out/"run_manifest.json",dict(integration=ledger["runs"],main=main,main_runs_attempted=0,integration_runs_attempted=1,
              per_run_input_bindings=[dict(run_id=r["run_id"],seed=r["seed"],duration_s=r["duration_s"],
                  inputs={k:dict(path=r[k],sha256=plan["frozen_files"][r[k]]) for k in ["network","config","demand"]}) for r in plan["runs"]],
              completed_summary=s))
        support=read(batch/"coordinate_support_audit.json")
        write(out/"network_variant_manifest.json",dict(scope="integration fixture networks only; no main plan/network frozen",
              variants={r["condition"]:dict(network=r["network"],sha256=plan["frozen_files"][r["network"]],coordinate=support["networks"][r["condition"]]) for r in plan["runs"]},
              runtime_audit=read(run/"coordinate_runtime_audit.json"),capacity_matched=False))
        write(out/"boundary_condition_manifest.json",dict(main_candidates_not_frozen=BOUNDARIES,
              actual_integration_C="compressed nodes .2;150 assigned passenger vehicles .3s apart;5G/6.2y/48.8r;60s cap;NOT main C",
              actual_integration_D="not attempted;18 lane2 entrants frozen;full-scale3to2",real_us101_supply_identified=False))
        accounting=read(out/"local_global_accounting_audit.json")
        accounting.update(last_complete_frame_s=float(f.time_s.iloc[-1]),last_global=dict(inserted=s["actual_inserted"],exited=s["actual_exited"],present=s["present"],pending=s["pending_end"]),
                          max_global_residual=int(f.global_conservation_residual.abs().max()),max_local_set_residual=int(f.local_set_balance_residual.abs().max()),
                          local_entered=s["local_entered"],local_exited=s["local_exited"],local_vehicle_s=s["local_vehicle_s"],scope=spec["local_space"],
                          qualification="Partial fixture Verified; entire integration blocked; local flux never derived from global totals")
        write(out/"local_global_accounting_audit.json",accounting)
        sensitivity=[]
        main0=support["networks"]["C"]["all_lane_lengths"]["main_0_0"]
        gate=main0+support["networks"]["C"]["all_lane_lengths"]["main_1_0"]
        for snap in q:
            tt=snap["time_s"];rr=states[np.isclose(states.time_s,tt)&states.speed_mps.lt(5)&states.edge_id.isin(["main_0","main_1"])]
            positions=[r.longitudinal_position_m+(main0 if r.edge_id=="main_1" else 0.) for r in rr.itertuples()]
            hist=np.bincount((np.array(positions)//50).astype(int),minlength=int(gate//50)+1);i=int((gate-1e-9)//50);front=None
            while i>=0 and hist[i]>=2:front=i*50.;i-=1
            sensitivity.append(dict(time_s=tt,graph_components=len(snap["components"]),graph_qualified_state=snap["qualification"]["state"],
                                    graph_upstream_rear_m=min([c["upstream_boundary_m"] for c in snap["components"]] or [None]),
                                    lane_grid_active_cells=sum(c["candidate_active"] for c in snap["grid"]),legacy_pooled_normal_edge_grid_front_m=front))
        write(out/"queue_spillback_diagnostics.json",dict(scope="partial compressed integration C only",first_times=s["first_times"],
              first_internal_low_s=s["first_internal_low_s"],first_pending_s=s["first_pending_s"],qualifications=s["queue_state_counts"],
              supported_spillback=False,entry_spillback_status="Evidence Insufficient",main_C_state="Not Attempted",
              method_sensitivity=sensitivity,method_override_allowed=False,all_paths_have_component_snapshots=sum(x["all_paths_queued"] for x in q),
              all_paths_have_component_is_not_entire_road_blocked=True,member_resets_include_edge_changes=q[-1]["qualification"]["lane_change_member_resets"],
              actual_lane_changes=s["lane_changes"],limitations=["Partial time; numerical blocker","No D dynamic coverage","Conservative edge/lane continuity resets","No unique insertion causality from pending alone"]))
        ref=read(batch/"inputs/calibration_reference.json")
        write(out/"traffic_state_comparison.json",dict(main_conditions={c:None for c in ["A","B","C","D"]},status="Not Assessable: main matrix not admitted",
              real_reference=ref,real_reference_role="two existing calibration summaries only; no new comparison or tolerance",
              compressed_fixture_is_not_realism_sample=True))
        write(out/"following_risk_diagnostics.json",dict(status="Not Attempted in main matrix",P2_status="Engineering Diagnostic Only if later admitted",
              engineering_P2_events=None,engineering_P2_rate=None,reliable_following_exposure_s=None,p2_evaluable_exposure_s=None,
              Stage0_2_definitions_unchanged=True,local_formal_P2="Unresolved",synthetic_P2_boundary_regression="16 cases in preflight; not a traffic result"))
        hypotheses=[]
        for h,description in [("H1","arrival perturbation B-A"),("H2","downstream supply C-A"),("H3","three-to-two D-A"),("H4","fixed Krauss constrained dynamics")]:
            hypotheses.append(dict(hypothesis=h,question=description,support="Partial compressed fixture only" if h in ["H2","H4"] else "None from new main matrix",
                counterevidence="Numerical admission failed; main conditions not attempted",alternative="Artificial short geometry/high insertion pressure/supply" if h in ["H2","H4"] else "Unmeasured input/network effects",
                confirmation="Evidence Insufficient",required_next="Independent numerical postprocessing domain validation, full integration duties, then new frozen main plan"))
        write(out/"mechanism_hypothesis_matrix.json",hypotheses)
        decisions=[dict(item=i,status=st,recommendation=r,approval_needed=ap) for i,st,r,ap in [
            ("Numerical near-zero domain","Awaiting Researcher Decision","Independently verify post-continuation snap; keep1e-6m","New observability policy/fixture plan"),
            ("Engineering mechanisms","Candidates retained","No demand/supply/driver search","New independent plan after integration"),
            ("D and lane changes","Not Attempted dynamically","Validate merge/outlet without bypassing C","New integration budget"),
            ("US101 geometry","generic only","Researcher to decide geometry evidence work","Lane/ramp/weaving evidence"),
            ("Demand","1648 internal-crossing candidate","Do not equate to upstream demand","Upstream/OD/arrival/fleet protocol"),
            ("Scientific tolerances","Tolerance Not Yet Justified","Independent justification","Researcher approval"),
            ("Local formal P2","Unresolved","Freeze spatial event/exposure ownership","Researcher approval"),
            ("Formal calibration","Not Ready","No automatic Krauss tuning","Future formal protocol, not this task")]]
        write(out/"researcher_decision_matrix.json",decisions)
        write(out/"runtime_budget_audit.json",dict(integration_limits=plan["limits"],actual=ledger["runs"],traffic_attempts=1,
              additional_fixture_attempts=0,total_fixture_limit=2,main_runs=0,main_budget_frozen=False,
              main_estimate_only=dict(freeflow_wall_s=150,constrained_wall_s=450,per_run_cap_s=600,batch_cap_s=7200,memory_GiB=6,artifact_GiB=4),
              full_P2_cost="Not Measured; no main run",queue_cost="Included in partial worker wall; not separately timed"))
        write(out/"execution_stop_observation.json",dict(actual_worker_exit_code=ledger["runs"][0]["exit_code"],
              actual_worker_summary_status=s["status"],parent_status=ledger["runs"][0]["status"],
              next_fixture_status=ledger["runs"][1]["status"],stopped_on_summary_blocker=True,no_post_blocker_runs=True))
        write(out/"historical_status_preservation.json",dict(B0_runs=19,B0_task_isolation=False,B0_validation_materialised="Unknown",
              B1_C="completed_with_engineering_blocker",B1_C_original_blockers=["runtime_settings","persistent_external_demand_without_documented_spillback"],
              B1_D="not_attempted",B11_stopping="Pending Numerical Equivalence",B11S_exact=947,B11S_all=948,
              historical_results_modified=False,historical_reclassification=False,old_C_states_read=False))
        logs=[]
        for p in sorted((batch/"access_logs").glob("*.json")):
            d=read(p);logs.append(dict(file=p.name,denied=d.get("denied",[]),allowed_open_events=d.get("allowed_open_events"),sha256=sha(p)))
        write(out/"controlled_access_audit.json",dict(logs=logs,unexpected_denials=sum(len(x["denied"]) for x in logs),
              synthetic_probe_is_separate=True,python_only=True,os_complete_monitoring=False,native_access_monitored=False))
        write(out/"audit.json",dict(result_id=RESULT_ID,status="blocked_at_integration_precondition",B1_2_MAIN_MATRIX_ALLOWED=False,
              mode="exploratory_diagnostic_only",**SCIENCE,numerical_exact_checked=10047,numerical_exact_passed=10047,
              numerical_bounded=14,numerical_not_evaluable=84,numerical_blockers=1,main_matrix_attempts=0,
              integration_attempts=1,old_C_states_read=False,B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised="Unknown",
              researcher_decision_required=True))
        write(out/"provenance.json",dict(result_id=RESULT_ID,base_commit=read(batch/"preparation_manifest.json")["base_commit"],
              integration_plan_sha256=sha(batch/"integration_plan.json"),executed_source_and_input_sha256=plan["frozen_files"],
              source_manifest=read(batch/"source_manifest.json"),post_stop_source_manifest=read(out/"official_source_manifest.json"),
              analysis=read(batch/"analysis_source_manifest.json"),no_new_runs_by_analysis=True,
              superseded_unexecuted_plan_sha256=sha(out/"prior_unexecuted_plan.json")))
        write(out/"config.json",dict(fixed=plan["fixed"],queue_candidate=plan["queue_config"],runs=plan["runs"],internal_step_s=.05,recorded_step_s=.1,
              ballistic=True,threads=1,traci_vehicle_control=False,formal_main_plan=None))
        preflight=read(batch/"synthetic_test_record.json")
        write(out/"test_record.json",dict(pre_freeze=dict(passed=142,failed=0,skipped=0,command=preflight["command"],
              record_sha256=sha(batch/"synthetic_test_record.json")),TDD_before_fix=dict(failed=16,passed=11),
              targeted_after_fix=dict(passed=27),final_validation="Pending final closure; update before commit",data_skips_are_not_scientific_pass=True))
        # Local exportable diagnostic plots; never copied to Git evidence.
        import matplotlib
        matplotlib.use("Agg")
        import re
        manager_source=(Path(matplotlib.__file__).parent/"font_manager.py").read_text(encoding="utf-8")
        cache_version=int(re.search(r"    __version__ = (\d+)",manager_source)[1])
        font=Path(matplotlib.get_data_path())/"fonts/ttf/DejaVuSans.ttf"
        cache=dict(_version=cache_version,_FontManager__default_weight="normal",default_size=None,
                   defaultFamily=dict(ttf="DejaVu Sans",afm="Helvetica"),afmlist=[],
                   ttflist=[dict(fname=str(font),name="DejaVu Sans",style="normal",variant="normal",weight=400,stretch="normal",size="scalable",__class__="FontEntry")],__class__="FontManager")
        write(Path(matplotlib.get_cachedir())/f"fontlist-v{cache_version}.json",cache)
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties
        fp=FontProperties(fname=str(font))
        figs=batch/"figures";figs.mkdir(exist_ok=True)
        fig,ax=plt.subplots(figsize=(9,4))
        ax.plot(f.time_s,f.global_present,label="global on road");ax.plot(f.time_s,f.local_present,label="local on road");ax.plot(f.time_s,f.external_pending,label="external pending")
        ax.set(xlabel="Time (s)",ylabel="Vehicles",title="Partial compressed integration fixture: distinct scopes")
        ax.legend(prop=fp);fig.tight_layout();fig.savefig(figs/"accounting.png",dpi=160);plt.close(fig)
        fig,ax=plt.subplots(figsize=(9,4))
        for snap in q:
            for comp in snap["components"]:ax.plot([snap["time_s"]]*2,[comp["upstream_boundary_m"],comp["downstream_m"]],alpha=.4)
        ax.axhline(50,color="gray",linestyle="--");ax.set(xlabel="Time (s)",ylabel="Verified per-path coordinate (m)",title="Lane-separated candidate components; no main-C inference")
        fig.tight_layout();fig.savefig(figs/"queue_space_time.png",dpi=160);plt.close(fig)
        fig,axs=plt.subplots(1,3,figsize=(12,4),sharey=True)
        for i,ax in enumerate(axs):
            rr=states[states.lane_id.eq(f"main_1_{i}")];im=ax.scatter(rr.time_s,rr.longitudinal_position_m,c=rr.speed_mps,s=2,cmap="viridis",vmin=0,vmax=27.78)
            ax.set(xlabel="Time (s)",title=f"main_1 lane{i}")
        axs[0].set_ylabel("Lane position (m)");fig.colorbar(im,ax=axs.ravel().tolist(),label="Speed (m/s)");fig.savefig(figs/"speed_space_time.png",dpi=160);plt.close(fig)
        write(out/"spacetime_diagnostics.json",dict(status="Partial compressed fixture only",main_matrix="Not Attempted",
              local_figures=["figures/accounting.png","figures/queue_space_time.png","figures/speed_space_time.png"],
              wave_speed_estimated=False,physical_world_coordinate_precision="Unknown",no_images_in_portable_evidence=True))
        write(out/"analysis_access_audit.json",audit)
        previous_attempt=batch/"analysis_access_audit_attempt1.json"
        if previous_attempt.exists():
            failed=read(previous_attempt)
            write(out/"renderer_revision_audit.json",dict(previous_attempt_sha256=sha(previous_attempt),
                  previous_denied=failed["denied"],repair="Use declared capsule MPLCONFIGDIR and package-only font cache; no measurement changes",
                  current_unexpected_denials=len(audit["denied"]),new_SUMO_runs=0))
        if audit["denied"]:raise PermissionError("analysis unexpected denial")
        seal(out)
        print("B12_PORTABLE_SUMMARY_READY",flush=True)
    finally:
        write(batch/"analysis_access_audit.json",audit)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("batch",type=Path);p.add_argument("--render",action="store_true");p.add_argument("--seal",action="store_true")
    args=p.parse_args();batch=args.batch.resolve()
    if args.render:render(batch)
    elif args.seal:seal(batch/"summary")
    else:raise SystemExit(stage(Path(__file__).resolve().parents[2],batch))
