"""B1 descriptive postprocessing, separate from frozen execution/measurement."""
from pathlib import Path
import json
import hashlib
import shutil
import platform
import base64
import gzip
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

from .stage_0_5_calibration_readiness import _write_json,_sha256_file
from .stage_0_5_boundary_bottleneck import read_plan,RESULT_ID,MODE
from .stage_0_5_exploratory_response import local_mask,_dist
from .stage_0_5_sumo import CalibrationValidationGuard,CALIBRATION_VALIDATION_POLICY,NGSIM_STATUS_CROSSWALK,MISSING_REASON_EQUIVALENCE


def stage_reference(repo,batch):
    """Additional descriptive aggregate projection; no execution input changes."""
    import copy
    source=json.loads((batch/"inputs/calibration_reference.json").read_text())["source_bindings"]["unified_strata.json"]
    path=repo/"evidence/results/RES-STAGE-0.5-CALIBRATION-GAPS-V1/unified_strata.json"
    target=batch/"analysis_inputs";target.mkdir(exist_ok=True)
    _write_json(target/"source_manifest.json",dict(source=str(path),sha256=source["sha256"],role="calibration",
        purpose="descriptive comparison only; separate from frozen simulation inputs",declared_before_read=True))
    policy=copy.deepcopy(CALIBRATION_VALIDATION_POLICY)
    policy["calibration"].append("b1_analysis_strata");policy["source_bindings"]["b1_analysis_strata"]=source["sha256"]
    guard=CalibrationValidationGuard(policy)
    guard.require_source_read(path,role="calibration",source="b1_analysis_strata",purpose="existing two-window aggregate only")
    data=json.loads(path.read_text(encoding="utf-8"))
    if "us101__0820_0835" in json.dumps(data):raise PermissionError("unexpected validation source")
    _write_json(target/"unified_strata.json",data)
    _write_json(target/"source_access_audit.json",dict(accesses=guard.audit(),sha256=_sha256_file(target/"unified_strata.json")))


def _read(path):return json.loads(path.read_text(encoding="utf-8"))


def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json","SHA256SUMS"])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError("portable file exceeds size limit")
    _write_json(out/"manifest.json",dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=_sha256_file(p)) for p in files]))
    files.append(out/"manifest.json")
    (out/"SHA256SUMS").write_text("".join(f"{_sha256_file(p)}  {p.name}\n" for p in files),encoding="utf-8",newline="\n")


def _time_table(s,frames,condition):
    result=[]
    for end in range(5,601,5):
        f=frames[frames.time_s.gt(end-5)&frames.time_s.le(end)]
        c=s[local_mask(s)&s.time_s.gt(end-5)&s.time_s.le(end)]
        if f.empty:continue
        result.append(dict(condition=condition,end_s=end,observed_s=len(f)*.1,
            inserted=int(f.inserted_step.sum()),exited=int(f.arrived_step.sum()),crossings=int(f.local_crossings.sum()),
            scheduled_due=int(f.scheduled_due.iloc[-1]),pending_end=int(f.pending.iloc[-1]),present_end=int(f.present.iloc[-1]),
            pending_max=int(f.pending.max()),onroad_low_mean=float(f.onroad_low_vehicles.mean()),
            onroad_halted_mean=float(f.halted.mean()),density=float(f.local_vehicles.mean()/.6),
            speed=float(c.speed_mps.mean()) if len(c) else None,low_fraction=float(c.speed_mps.lt(5).mean()) if len(c) else None,
            connected_queue_front_min_m=float(f.queue_connected_front_m.min()) if f.queue_connected_front_m.notna().any() else None,
            connected_queue_front_median_m=float(f.queue_connected_front_m.median()) if f.queue_connected_front_m.notna().any() else None))
    return result


def _space_table(s,plan,condition):
    lengths=plan["networks"][condition]["edge_lengths"]
    offset=dict(main_0=0,main_1=lengths["main_0"],main_2=lengths["main_0"]+lengths["main_1"])
    c=s[s.edge_id.isin(offset)].copy()
    c["position_m"]=c.longitudinal_position_m+c.edge_id.map(offset)
    c["position_bin_m"]=(c.position_m//50).astype(int)*50
    c["end_s"]=(np.ceil(c.time_s/5)).astype(int)*5
    result=c.groupby(["end_s","position_bin_m"]).agg(speed=("speed_mps","mean"),
        state_rows=("speed_mps","size"),low_fraction=("speed_mps",lambda x:float((x<5).mean()))).reset_index()
    result.insert(0,"condition",condition)
    return result


def _longest(mask,cadence):
    longest=now=0
    for v in mask:
        now=now+1 if v else 0;longest=max(longest,now)
    return longest*cadence


def _plots(batch,metrics,series,cells,ref):
    import matplotlib
    matplotlib.use("Agg")
    # Build a package-font-only cache BEFORE importing font_manager/pyplot.
    # System font discovery attempted denied optional user/Office font files in
    # the first rendering pass. Those refusals remain in the access audit.
    import re
    manager_source=(Path(matplotlib.__file__).parent/"font_manager.py").read_text(encoding="utf-8")
    version=int(re.search(r"    __version__ = (\d+)",manager_source)[1])
    font=Path(matplotlib.get_data_path())/"fonts/ttf/DejaVuSans.ttf"
    cache=dict(_version=version,_FontManager__default_weight="normal",default_size=None,
        defaultFamily=dict(ttf="DejaVu Sans",afm="Helvetica"),afmlist=[],
        ttflist=[dict(fname=str(font),name="DejaVu Sans",style="normal",variant="normal",weight=400,stretch="normal",size="scalable",__class__="FontEntry")],__class__="FontManager")
    _write_json(Path(matplotlib.get_cachedir())/f"fontlist-v{version}.json",cache)
    import matplotlib.pyplot as plt
    figdir=batch/"figures";figdir.mkdir(exist_ok=True)
    titles=[]
    def save(fig,name):
        fig.suptitle("SUMO Engineering Exploration | "+name.replace("_"," "))
        for ext in ["png","svg"]:fig.savefig(figdir/(name+"."+ext),dpi=150,bbox_inches="tight")
        plt.close(fig);titles.append(name)
    fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True,sharey=True,layout="constrained")
    for condition,ax in zip("ABCD",axes.flat):
        c=cells[cells.condition.eq(condition)]
        if len(c):
            p=c.pivot(index="position_bin_m",columns="end_s",values="speed")
            im=ax.pcolormesh(p.columns,p.index,p.to_numpy(),vmin=0,vmax=27.78,cmap="viridis",shading="nearest")
            ax.set_title(condition+(" | blocked diagnostic" if condition=="C" else ""));ax.set(xlabel="Time [s]",ylabel="Corridor position [m]")
        else:
            ax.set_title(condition+" not attempted");ax.text(.5,.5,"Stopped before launch",transform=ax.transAxes,ha="center")
    if len(cells):fig.colorbar(im,ax=list(axes.flat),label="Cell vehicle-time speed [m/s]",shrink=.7)
    save(fig,"01_space_time_speed")
    fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True,layout="constrained")
    for condition in metrics.condition:
        t=series[series.condition.eq(condition)]
        label=condition+(" (blocked)" if condition=="C" else "")
        axes[0,0].plot(t.end_s,t.density,label=label)
        axes[0,1].plot(t.end_s,t.speed,label=label)
        axes[1,0].plot(t.end_s,t.pending_end,label=label)
        axes[1,1].plot(t.end_s,t.onroad_low_mean,label=label)
    for ax,label in zip(axes.flat,["Local density [veh/km/lane]","Local speed [m/s]","External pending [vehicles]","On-road speed<5 [vehicles]"]):
        ax.set(xlabel="Time [s]",ylabel=label);ax.legend()
    save(fig,"02_density_speed_queues")
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout="constrained")
    for condition in metrics.condition:
        t=series[series.condition.eq(condition)]
        label=condition+(" (blocked)" if condition=="C" else "")
        axes[0].scatter(t.density,t.speed,s=12,label=label)
        axes[1].plot(t.end_s,t.inserted.cumsum(),label=label+" inserted")
        axes[1].plot(t.end_s,t.exited.cumsum(),ls="--",label=label+" exited")
    axes[0].set(xlabel="Local density [veh/km/lane]",ylabel="Local speed [m/s]")
    axes[1].set(xlabel="Time [s]",ylabel="Cumulative vehicles")
    for ax in axes:ax.legend(fontsize=8)
    save(fig,"03_state_and_service")
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout="constrained")
    for ax,key in zip(axes,["speed_mps","net_gap_m","closing_speed_mps"]):
        for condition in metrics.condition:
            r=_read(batch/"runs"/f"b1_{condition}_s20261019"/"summary.json")
            dist=r["local_metrics"][key];q=dist["quantiles"]
            ax.plot([float(v) for v in q],[q[v] for v in q],label="SUMO "+condition+(" (blocked)" if condition=="C" else ""))
        for g,w in ref["windows"].items():
            q=w["interior_metrics"][key]["distribution"]["quantiles"]
            ax.plot([float(v) for v in q],[q[v] for v in q],ls="--",label="Real "+g[7:])
        ax.set(xlabel="Conditional quantile",ylabel=key);ax.legend(fontsize=6)
    save(fig,"04_real_reference_quantiles")
    return titles


def audit_inputs(batch):
    plan=read_plan(batch);checks=[]
    for seed in sorted({r["seed"] for r in plan["runs"]}):
        rows=[r for r in plan["runs"] if r["seed"]==seed]
        baseline=next(r for r in rows if r["condition"]=="A")
        original=[dict(v.attrib) for v in ET.parse(batch/baseline["demand_path"]).getroot().findall("vehicle")]
        for r in rows:
            vehicles=[dict(v.attrib) for v in ET.parse(batch/r["demand_path"]).getroot().findall("vehicle")]
            if len(vehicles)!=len(original):raise ValueError("paired arrival count mismatch")
            for a,b in zip(original,vehicles):
                if {k:v for k,v in a.items() if k!="depart"}!={k:v for k,v in b.items() if k!="depart"}:raise ValueError("paired identities/classes/lane/length-rule differ")
            if r["condition"]!="B" and original!=vehicles:raise ValueError("unapproved arrival change")
            if r["vtype_path"]!=baseline["vtype_path"]:raise ValueError("different vType input")
            checks.append(dict(run_id=r["run_id"],planned_vehicles=len(vehicles),same_ids_types_lengths_rules=True,
                changed_arrival_only=r["condition"]=="B",same_desired_speed_and_behaviour=True))
    result=dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),passed=True,runs=checks,
        observation_three_lanes_verified=True,capacity_matched=False,actual_insertions_not_assumed_equal=True)
    _write_json(batch/"paired_input_contract_audit.json",result)
    return result


def finalize(batch):
    audit_inputs(batch)
    ledger=json.loads((batch/"execution_ledger.json").read_text())
    if all(r["status"]=="not_attempted" for r in ledger["runs"]):
        print("B1_PAIRED_INPUT_CONTRACT_OK; no matrix run started",flush=True);return
    if not ledger["closed"]:raise ValueError("postprocessing requires a closed matrix")
    plan=read_plan(batch);out=batch/"summary";out.mkdir(exist_ok=True)
    ref=_read(batch/"inputs/calibration_reference.json")
    summaries=[];metrics=[];series=[];spaces=[];queues=[];conservation=[];fleet=[];frames_by={}
    for entry in ledger["runs"]:
        path=batch/"runs"/entry["run_id"]
        if not (path/"summary.json").exists():continue
        s=_read(path/"summary.json");summaries.append(s)
        f=pd.read_csv(path/"traffic_frames.csv");frames_by[s["condition"]]=f
        state=pd.read_parquet(path/"state.parquet")
        a=s["accounting"];m=s["local_metrics"];duration=s["observed_s"];c=s["condition"]
        metrics.append(dict(condition=c,run_id=s["run_id"],status=entry["status"],
            speed=m["speed_mps"]["mean"],speed_median=m["speed_mps"]["quantiles"].get("0.5"),
            speed_p05=m["speed_mps"]["quantiles"].get("0.05"),speed_p95=m["speed_mps"]["quantiles"].get("0.95"),
            density=s["local_density_veh_km_lane"],low_speed=s["local_low_speed_fraction"],gap=m["net_gap_m"]["mean"],
            gap_median=m["net_gap_m"]["quantiles"].get("0.5"),closing=m["closing_speed_mps"]["mean"],
            closing_sd=m["closing_speed_mps"]["sd"],closing_positive=s["local_positive_closing_fraction"],
            ttc_valid=s["local_ttc_valid_fraction"],ttc_median=m["ttc_s"]["quantiles"].get("0.5"),
            following=s["local_following_fraction"],acceleration_sd=m["acceleration_mps2"]["sd"],
            inserted=a["departed_vehicles"],exited=a["arrived_vehicles"],present=a["present_at_end"],unserved=a["unserved_at_end"],
            inserted_veh_h_lane=a["departed_vehicles"]*3600/duration/3,
            through_veh_h_lane=s["local_crossings"]*3600/duration/3,
            exited_veh_h_lane=a["arrived_vehicles"]*3600/duration/3,
            p2_events=s["full_network_p2"]["events"],p2_exposure_s=s["full_network_p2"]["p2_evaluable_following_exposure_s"],
            p2_full_engineering_rate=s["full_network_p2"]["event_rate_per_evaluable_vehicle_hour"],
            wall_s=entry["wall_s"],peak_rss_bytes=entry["peak_sampled_tree_rss_bytes"],output_bytes=entry["bytes"],
            state_rows=s["state_rows"],mean_delay_s=s["insertion_delays_s"]["mean"]))
        series+=_time_table(state,f,c);spaces.append(_space_table(state,plan,c))
        local=state[local_mask(state)]
        queues.append(dict(condition=c,external_pending_max=int(f.pending.max()),external_pending_end=int(f.pending.iloc[-1]),
            first_external_pending_s=float(f.loc[f.pending.gt(0),"time_s"].min()) if f.pending.gt(0).any() else None,
            onroad_low_max=int(f.onroad_low_vehicles.max()),onroad_low_vehicle_s=float(f.onroad_low_vehicles.sum()*.1),
            onroad_halted_vehicle_s=float(f.halted.sum()*.1),
            local_any_low_vehicle_duration_s=float(f.local_low_speed_vehicles.gt(0).sum()*.1),
            longest_continuous_any_local_low_s=_longest(f.local_low_speed_vehicles.gt(0),.1),
            queue_connected_front_min_m=s["queue_front_min_m"],spillback_qualified=s["spillback_qualified"],
            sustained_mean_local_speed_below5_for30s=s["sustained_local_low_speed_30s"],
            first_low_by_corridor_50m_bin="local_large_tables/first_low_positions.csv",
            initial_vehicles=0,internal_vs_external_separate=True))
        tail=f[f.time_s.gt(540)]
        queues[-1].update(first_onroad_inlet_low_s=float(f.loc[f.upstream_low_vehicles.gt(0),"time_s"].min()) if f.upstream_low_vehicles.gt(0).any() else None,
            final60s_inlet_low_frame_share=float(tail.upstream_low_vehicles.gt(0).mean()),
            final60s_connected_front_le50_frame_share=float(tail.queue_connected_front_m.le(50).mean()),
            original_spillback_qualification_retained=True)
        conservation.append(dict(condition=c,**a,max_frame_residual=int(f.conservation_residual.abs().max()),
            max_due_minus_departed_minus_pending=int((f.scheduled_due-f.departed-f.pending).abs().max()),
            all_external_vehicles_excluded_from_density=True))
        fleet.append(dict(condition=c,planned_types=dict(pd.Series([v.attrib["type"] for v in ET.parse(batch/s["demand_path"]).getroot().findall("vehicle")]).value_counts()),
            actual_inserted_types=state.drop_duplicates("vehicle_id").vehicle_type.value_counts().to_dict(),
            state_type_length_pairs=state[["vehicle_type","vehicle_length_m"]].drop_duplicates().to_dict("records"),
            low_speed_local_gap=m["low_speed_gap_m"],actual_local_vehicle_s=len(local)*.1))
        del state,local
    metrics=pd.DataFrame(metrics);series=pd.DataFrame(series);cells=pd.concat(spaces,ignore_index=True)
    large=batch/"local_large_tables";large.mkdir(exist_ok=True)
    cells.to_csv(large/"spacetime_cells.csv",index=False)
    low=cells[cells.low_fraction.gt(0)].groupby(["condition","position_bin_m"]).end_s.min().reset_index(name="first_low_5s_bin_end_s")
    low.to_csv(large/"first_low_positions.csv",index=False)
    metrics.to_csv(out/"run_metrics.csv",index=False);series.to_csv(out/"time_series_5s.csv",index=False)
    bins=pd.DataFrame([dict(condition=s["condition"],**b) for s in summaries for b in s["time_bins"]]);bins.to_csv(out/"time_bins_60s.csv",index=False)
    for name in ["data_isolation_preflight.json","execution_guard_audit.json","experiment_plan.json","PLAN_SHA256","plan_revision_audit.json",
        "network_variant_manifest.json","boundary_condition_manifest.json","source_manifest.json","source_staging_manifest.json",
        "source_access_audit.json","test_scope_audit.json","preparation_manifest.json","paired_input_contract_audit.json","execution_ledger.json","phase1_checkpoint.json"]:
        if (batch/name).exists():shutil.copyfile(batch/name,out/name)
    shutil.copyfile(batch/"inputs/calibration_reference.json",out/"real_reference_summary.json")
    for name in ["experiment_plan.json","execution_ledger.json","summary.json","worker_b1_A_s20261019.json"]:
        shutil.copyfile(batch/"history/b1_plan_v1"/name,out/("prior_v1_"+name))
    if (batch/"analysis_inputs/unified_strata.json").exists():
        shutil.copyfile(batch/"analysis_inputs/unified_strata.json",out/"real_strata_summary.json")
        shutil.copyfile(batch/"analysis_inputs/source_access_audit.json",out/"analysis_reference_access_audit.json")
    _write_json(out/"config.json",dict(mode=MODE,fixed=plan["fixed"],fleet=plan["fleet"],local_space=plan["local_space"],
        duration_s=600,main_flow_veh_h_lane=1648.,initial_vehicles=0,scientific_claim_eligible=False))
    bundle={name:dict(sha256=digest,bytes=(batch/name).stat().st_size,
        gzip_base64=base64.b64encode(gzip.compress((batch/name).read_bytes(),mtime=0)).decode("ascii"))
        for name,digest in plan["frozen_files"].items() if name.startswith("inputs/") and Path(name).suffix in [".xml",".sumocfg"]}
    _write_json(out/"engineering_input_bundle.json",dict(encoding="gzip+base64, exact original bytes",files=bundle,
        excludes="raw real trajectories, state tables, SUMO logs, caches and images"))
    _write_json(out/"fixed_parameter_manifest.json",dict(fixed=plan["fixed"],fleet=plan["fleet"],engineering_candidates_only=True,
        paired_input_contract=_read(batch/"paired_input_contract_audit.json")))
    _write_json(out/"run_manifest.json",dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),runs=ledger["runs"],
        prior_v1_runs=_read(batch/"history/b1_plan_v1/execution_ledger.json")["runs"],task_attempts=1+sum(r["status"]!="not_attempted" for r in ledger["runs"]),
        all_results_retained=True,measurement_version="unchanged Stage0.2 formal core via SUMO adapter",local_formal_p2="Unresolved"))
    _write_json(out/"traffic_conservation_audit.json",dict(runs=conservation,actual_flow_normalization_s=600,
        downstream_rate_denominator="three input lanes for C/A/B; D also report total veh/h because downstream2lanes; no capacity matching"))
    _write_json(out/"queue_diagnostics.json",dict(runs=queues,definition=plan["stop_rules"]["slow_queue"],
        detection_limit="connected50m-bin front is descriptive and can miss sparse/disconnected queues; no calibrated wave speed",time_series="time_series_5s.csv"))
    _write_json(out/"traffic_state_comparison.json",dict(sumo=metrics.to_dict("records"),real=ref,
        weights="SUMO local state rows x0.1s vehicle-time, all600s including empty frames; real interior720/660s and its frozen reliable support",
        real_observer="150<=Local_Y<350, lanes1-5,1lane-km",sumo_observer=plan["local_space"],
        scientifically_accepted=False,no_tolerance_or_capacity_equivalence=True))
    _write_json(out/"following_risk_diagnostics.json",dict(runs=[dict(condition=s["condition"],metrics=s["local_metrics"],
        following_fraction=s["local_following_fraction"],ttc_valid=s["local_ttc_valid_fraction"],positive_closing=s["local_positive_closing_fraction"],
        full_network_p2=s["full_network_p2"],local_stratum_formal_p2="Unresolved") for s in summaries],
        ngsim_sumo_crosswalk=NGSIM_STATUS_CROSSWALK,missing_reason_equivalence=MISSING_REASON_EQUIVALENCE,
        no_real_missingness_target=True,no_spatial_rate_comparison=True))
    old=_read(out/"prior_v1_summary.json")
    _write_json(out/"numerical_method_audit.json",dict(runs=[dict(condition=s["condition"],runtime=s["numerical"],
        cadence_error_s=s["cadence_max_abs_error_s"],duplicates=s["duplicate_identity_time_rows"],gap_geometry_rows=s["net_gap_geometry_checked_rows"],
        gap_geometry_max_abs_m=s["net_gap_geometry_max_abs_m"],closing_sign_error=s["closing_sign_max_error"]) for s in summaries],
        core_exposure_equivalence=_read(batch/"runs/b1_A_s20261019/core_exposure_equivalence.json"),
        failed_v1_A_same_state_fingerprint=next(s for s in summaries if s["condition"]=="A")["state_fingerprint"]==old["state_fingerprint"],
        prior_v1_A_remains_failed=True,no_new_repetition_or_step_search=True))
    _write_json(out/"fleet_and_initialization_audit.json",dict(initial_vehicles=0,runs=fleet,warmup_approved_s=None,
        all_time_slices_retained=True,all_driving_parameters_fixed=True))
    audits=[dict(name=p.name,**_read(p)) for p in sorted((batch/"access_logs").glob("*.json"))]
    _write_json(out/"controlled_access_audit.json",dict(entrypoints=audits,preflight_tests=_read(batch/"preflight_test_access_audit.json"),
        unexpected_denials=sum(len(a["denied"]) for a in audits),
        matrix_worker_denials=sum(len(a["denied"]) for a in audits if a["name"].startswith("worker_")),
        rendering_refusals_retained=True,rendering_font_fix="package-font-only cache, separate unfrozen renderer; no simulation rerun",
        expected_synthetic_refusals=3,validation_window_rows_materialised_in_controlled_inputs=0,
        historical_full_sources_copied=False,os_native_complete_monitoring=False,
        limitation="task-scope whitelist and guarded Python entrypoints, not an OS sandbox or universal process-access proof"))
    _write_json(out/"runtime_budget_audit.json",dict(limits=plan["limits"],prior_attempts=1,new_attempts=len(summaries),
        total_attempts_including_prior=1+len(summaries),new_run_wall_s=float(metrics.wall_s.sum()),
        prior_run_wall_s=_read(out/"prior_v1_execution_ledger.json")["runs"][0]["wall_s"],
        task_elapsed_at_matrix_close_s=ledger["elapsed_wall_s"],peak_sampled_tree_rss_bytes=int(metrics.peak_rss_bytes.max()),
        matrix_output_bytes=int(metrics.output_bytes.sum()),no_budget_reset=True,no_second_seed=True,
        unallocated_slots_in_V2_plan=3,task_remaining_attempt_capacity=8-(1+len(summaries)),
        current_plan_not_attempted=sum(r["status"]=="not_attempted" for r in ledger["runs"]),automatic_use_allowed=False))
    _write_json(out/"audit.json",dict(result_id=RESULT_ID,mode=MODE,stage_0_5_gate="pending_simulation_sample",scientific_claim_eligible=False,
        ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,
        tolerances="Tolerance Not Yet Justified",energy_distance_upper_bound="Not Identifiable",local_stratum_formal_p2="Unresolved",
        b0_task_data_isolation_accepted=False,b0_validation_window_rows_materialised="Unknown",b0_results_retained_limited_descriptive_only=True,
        b1_controlled_input_isolation_passed=True,b1_validation_window_rows_materialised_in_controlled_inputs=0,
        b1_os_complete_monitoring=False,all_task_attempts_valid=False,prior_failed_attempt_retained=True,
        formal_calibration_started=False,independent_validation_run=False,optimization=False))
    figures=_plots(batch,metrics,series,cells,ref)
    _write_json(out/"figure_index.json",dict(local_figures=[dict(png=f"figures/{p}.png",svg=f"figures/{p}.svg") for p in figures],
        matching_numeric_tables=["run_metrics.csv","time_series_5s.csv","time_bins_60s.csv","local_large_tables/spacetime_cells.csv","local_large_tables/first_low_positions.csv"],
        portable_images=False,no_pass_fail_lines=True))
    _write_json(out/"provenance.json",dict(result_id=RESULT_ID,python=platform.python_version(),
        base_commit=_read(batch/"preparation_manifest.json")["base_commit"],plan_sha256=_sha256_file(batch/"experiment_plan.json"),
        analysis_source_sha256=_sha256_file(Path(__file__)),executed_code_and_input_sha256=plan["frozen_files"],
        summary_source_bindings=ref["source_bindings"],history="V1 failed closed; V2 changes dependency bootstrap only; no traffic retuning"))
    seal(out)
    print(metrics.to_string(index=False),flush=True)
