"""Post-run B0 descriptive evidence, tables and scientific figures.

No input design, parameter selection, formal tolerance, or Gate is changed here.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .stage_0_5_calibration_readiness import _write_json,_sha256_file,_utc_now
from .stage_0_5_exploratory_response import read_plan,RESULT_ID,MODE,local_mask
from .stage_0_5_sumo import NGSIM_STATUS_CROSSWALK,MISSING_REASON_EQUIVALENCE

REPORT="docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md"


def _read(path): return json.loads(path.read_text(encoding="utf-8"))


def frame_diagnostics(frames):
    """Empty frames remain in time denominators; waiting demand stays external."""
    def first(mask):
        return float(frames.loc[mask,"time_s"].iloc[0]) if mask.any() else None
    return dict(first_local_vehicle_s=first(frames.local_vehicles.gt(0)),
        first_exit_s=first(frames.arrived_step.gt(0)),
        first_pending_s=first(frames.pending.gt(0)),
        pending_max=int(frames.pending.max()),
        pending_frame_fraction=float(frames.pending.gt(0).mean()),
        first_pending_note="a single waiting frame can be normal insertion cadence; inspect persistence and growth",
        final_present=int(frames.present.iloc[-1]),initial_vehicle_share=0.,
        actual_local_density_layer="Low-density" if float(frames.local_vehicles.mean()/.6)<=42.87666666666667 else "Higher-density",
        local_density_layer_is_descriptive_only=True)


def scalar_metrics(s):
    m=s["local_metrics"];p=s["full_network_p2"];a=s["accounting"]
    r=dict(density=s["local_density_veh_km_lane"],speed=m["speed_mps"]["mean"],
        speed_median=m["speed_mps"]["quantiles"].get("0.5"),low_speed=s["local_low_speed_fraction"],
        acceleration=m["acceleration_mps2"]["mean"],gap=m["net_gap_m"]["mean"],
        gap_median=m["net_gap_m"]["quantiles"].get("0.5"),closing=m["closing_speed_mps"]["mean"],
        closing_positive=s["local_positive_closing_fraction"],ttc_valid=s["local_ttc_valid_fraction"],
        ttc_median=m["ttc_s"]["quantiles"].get("0.5"),
        following=s["local_following_fraction"],p2_events=p["events"],exposure_s=p["p2_evaluable_following_exposure_s"],
        p2_rate=p["event_rate_per_evaluable_vehicle_hour"],scheduled=a["scheduled_vehicles"],
        inserted=a["departed_vehicles"],exited=a["arrived_vehicles"],unserved=a["unserved_at_end"],present=a["present_at_end"],
        inserted_veh_h_lane=a["departed_vehicles"]*3600/300/3,
        through_veh_h_lane=s["local_crossings"]*3600/300/3,
        exited_veh_h_lane=a["arrived_vehicles"]*3600/300/3)
    return r


def prior_initialization(repo,batch,refs):
    """Optional existing simulation-state reuse; never real trajectories."""
    result=[]
    base=repo/"code/outputs/formal/calibration/stage_0_5_calibration_load_benchmark_v1"
    for run in refs["prior_numerics"]["runs"]:
        if run["id"]=="medium_0.10": continue
        path=base/run["id"]/"state.parquet"
        row=dict(run_id=run["id"],source="sealed A+ engineering simulation",expected_sha256=run["raw_state_sha256"])
        if not path.exists():
            row["status"]="Unavailable in this clone";result.append(row);continue
        if _sha256_file(path)!=run["raw_state_sha256"]: raise ValueError("prior engineering-state SHA mismatch")
        s=pd.read_parquet(path,columns=["vehicle_id","time_s","edge_id","longitudinal_position_m","speed_mps"])
        local=s[local_mask(s)].copy();local["initial"]=local.vehicle_id.str.startswith("initial_")
        bins=[]
        for a in range(0,300,60):
            c=local[local.time_s.gt(a)&local.time_s.le(a+60)]
            bins.append(dict(start_s=a,end_s=a+60,local_initial_vehicle_time_share=float(c.initial.mean()) if len(c) else None,
                local_mean_speed_mps=float(c.speed_mps.mean()) if len(c) else None,
                local_low_speed_fraction=float(c.speed_mps.lt(5).mean()) if len(c) else None))
        init=s[s.vehicle_id.str.startswith("initial_")]
        row.update(status="Verified hash",bins=bins,initial_vehicles_observed=int(init.vehicle_id.nunique()),
            initial_last_observed_s=float(init.time_s.max()),
            initial_still_present_at_last_frame=int(init[init.time_s.eq(300)].vehicle_id.nunique()),
            exit_note="last observed time is not an independently observed exit event")
        result.append(row)
    return result


def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json","SHA256SUMS"]
                 and (p.suffix in [".json",".csv",".md"] or p.name=="PLAN_SHA256"))
    _write_json(out/"manifest.json",dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=_sha256_file(p)) for p in files]))
    files.append(out/"manifest.json")
    (out/"SHA256SUMS").write_text("".join(f"{_sha256_file(p)}  {p.name}\n" for p in files),encoding="utf-8",newline="\n")


def _make_plots(batch,rows,metrics,series,refs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":10,"figure.dpi":140,"axes.spines.top":False,"axes.spines.right":False})
    out=batch/"figures";out.mkdir(exist_ok=True)
    paths=[]
    def save(fig,name):
        fig.tight_layout();fig.savefig(out/(name+".png"),dpi=160,bbox_inches="tight")
        fig.savefig(out/(name+".svg"),bbox_inches="tight");plt.close(fig);paths.append(name)
    baseline=metrics[metrics.phase.eq("phase1")]
    fig,ax=plt.subplots(figsize=(8,5))
    for group in refs["strata"]["slices"]:
        if group["eligible"]:
            ax.scatter(group["density_veh_km_lane"],group["mean_speed_mps"],marker="x",s=55,color="#a44b32",label="Real Reference (calibration interior)")
    for phase,marker in [("phase1","o"),("phase2","^")]:
        c=metrics[metrics.phase.eq(phase)]
        ax.scatter(c.density,c.speed,marker=marker,s=45,label=f"SUMO Engineering Exploration ({phase})",alpha=.8)
    handles,labels=ax.get_legend_handles_labels();unique=dict(zip(labels,handles));ax.legend(unique.values(),unique.keys(),fontsize=8)
    ax.set(xlabel="Local density [veh/km/lane]",ylabel="Vehicle-time mean speed [m/s]",title="B0: actual traffic support, not acceptance scores")
    save(fig,"01_density_speed")
    fig,axes=plt.subplots(3,2,figsize=(11,9),sharex=True)
    for i,load in enumerate(["low","medium","high"]):
        for seed,style in [(20261018,"-"),(20261019,"--")]:
            rid=f"b0_{load}_base_s{seed}";c=series[series.run_id.eq(rid)]
            axes[i,0].plot(c.end_s,c.inserted_veh_h_lane,style,label=f"inserted s{seed}")
            axes[i,0].plot(c.end_s,c.exited_veh_h_lane,style,alpha=.5,label=f"exited s{seed}")
            axes[i,1].plot(c.end_s,c.pending_end,style,label=f"pending s{seed}")
        demand=read_plan(batch)["loads"][load]["flow_veh_h_lane"]
        axes[i,0].axhline(demand,color="#555",lw=.8,label="Configured demand")
        axes[i,0].set(ylabel=f"{load} input [veh/h/lane]");axes[i,1].set(ylabel="Waiting outside network [veh]")
    axes[0,0].legend(fontsize=7);axes[0,1].legend(fontsize=8)
    for ax in axes[-1]: ax.set_xlabel("Simulation time [s]")
    fig.suptitle("SUMO Engineering Exploration: configured input vs served traffic",y=1.01)
    save(fig,"02_input_exit_pending")
    fig,axes=plt.subplots(2,1,figsize=(9,7),sharex=True)
    for load,color in zip(["low","medium","high"],["#4579a6","#be8d3a","#8d4b65"]):
        c=series[series.run_id.eq(f"b0_{load}_base_s20261018")]
        axes[0].plot(c.end_s,c.density,label=load,color=color);axes[1].plot(c.end_s,c.speed,label=load,color=color)
    axes[0].set(ylabel="Local density [veh/km/lane]",title="B0 starts empty: initial-vehicle fraction = 0 throughout")
    axes[1].set(ylabel="Local speed [m/s]",xlabel="Simulation time [s]");axes[0].legend()
    save(fig,"03_empty_start_evolution")
    for parameter,num in [("tau","04"),("minGap","05")]:
        fig,axes=plt.subplots(2,3,figsize=(12,7))
        keys=["gap","closing","density","speed","ttc_median","unserved"]
        for ax,key in zip(axes.flat,keys):
            for load,color in [("medium","#4579a6"),("high","#a44b32")]:
                for seed,style in [(20261018,"-o"),(20261019,"--s")]:
                    c=metrics[(metrics.load.eq(load))&metrics.seed.eq(seed)&(metrics.phase.eq("phase1")|metrics.changed_parameter.eq(parameter))].sort_values(parameter)
                    label=f"{load}, s{seed}"+(" (baseline only)" if len(c)==1 else "")
                    ax.plot(c[parameter],c[key],style,color=color,label=label,markersize=4)
                    blocked=c[c.engineering_blockers.fillna("").ne("")]
                    if len(blocked): ax.scatter(blocked[parameter],blocked[key],marker="x",s=75,color="#9a1723",zorder=5)
            units=dict(gap="Physical net gap [m]",closing="Closing speed [m/s]",density="Density [veh/km/lane]",
                       speed="Speed [m/s]",ttc_median="Valid TTC median [s]",unserved="Unserved demand at 300s [veh]")
            ax.set(xlabel=f"{parameter} [{'s' if parameter=='tau' else 'm'}]",ylabel=units[key])
        axes[0,0].legend(fontsize=6)
        fig.suptitle(f"SUMO Engineering Exploration: {parameter} response; red x = blocking backlog")
        save(fig,f"{num}_{parameter}_response")
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,key in zip(axes,["speed","gap"]):
        for i,load in enumerate(["low","medium","high"]):
            c=baseline[baseline.load.eq(load)]
            ax.scatter([i]*len(c),c[key],s=60)
        ax.set(xticks=range(3),xticklabels=["low input","medium input","high input"],ylabel=key,
            title="Two seeds: descriptive spread, not a confidence interval")
    save(fig,"06_seed_spread")
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,key in zip(axes,["speed_mps","net_gap_m","closing_speed_mps"]):
        for group,w in refs["diagnostics"]["windows"].items():
            q=w["interior_local_metrics"][key]["distribution"]["quantiles"]
            pairs=[(float(k),v) for k,v in q.items() if .05<=float(k)<=.95]
            pairs.sort()
            ax.plot([p[0] for p in pairs],[p[1] for p in pairs],"x-",label="Real Reference "+group[-10:])
        for load in ["medium","high"]:
            r=next(r for r in rows if r["run_id"]==f"b0_{load}_base_s20261018")
            q=r["local_metrics"][key]["quantiles"]
            pairs=sorted((float(k),v) for k,v in q.items() if .05<=float(k)<=.95)
            ax.plot([p[0] for p in pairs],[p[1] for p in pairs],"o--",label="SUMO Exploration "+load)
        ax.set(xlabel="Empirical quantile",ylabel=key)
    axes[0].legend(fontsize=6)
    fig.suptitle("Local descriptive distributions; different temporal/structural support")
    save(fig,"07_real_sumo_quantiles")
    # Space-time speed cells: empty cells remain missing, never zero speed.
    run=next(r for r in rows if r["run_id"]=="b0_high_base_s20261018")
    s=pd.read_parquet(batch/"runs"/run["run_id"]/"state.parquet",columns=["time_s","edge_id","longitudinal_position_m","speed_mps"])
    lengths={e.attrib["id"]:float(e.find("lane").attrib["length"]) for e in ET.parse(batch/read_plan(batch)["network_path"]).getroot().findall("edge") if not e.attrib["id"].startswith(":")}
    offsets={"main_0":0,"main_1":lengths["main_0"],"main_2":lengths["main_0"]+lengths["main_1"]}
    s=s[s.edge_id.isin(offsets)].copy();s["space_bin"]=(s.longitudinal_position_m+s.edge_id.map(offsets))//50
    s["time_bin"]=(s.time_s-1e-8)//5
    cells=s.groupby(["space_bin","time_bin"]).speed_mps.agg(["mean","count"]).reset_index()
    cells.to_csv(batch/"local_large_tables/spacetime_cells.csv",index=False)
    grid=cells.pivot(index="space_bin",columns="time_bin",values="mean").reindex(index=range(24),columns=range(60))
    fig,ax=plt.subplots(figsize=(10,4));im=ax.imshow(grid,origin="lower",aspect="auto",extent=[0,300,0,1200],vmin=0,vmax=27.78,cmap="viridis")
    ax.set(xlabel="Simulation time [s]",ylabel="Concatenated normal-edge coordinate [m]",title="SUMO high-input baseline: space-time speed; empty cells missing")
    fig.colorbar(im,ax=ax,label="Speed [m/s]");save(fig,"08_spacetime_speed")
    return paths


def finalize(repo: Path,batch: Path):
    plan=read_plan(batch);ledger=_read(batch/"execution_ledger.json");refs=_read(batch/"real_reference_summary.json")
    validation_activity=_read(batch/"validation_activity_audit.json") if (batch/"validation_activity_audit.json").exists() else None
    rows=[]
    for r in plan["runs"]:
        p=batch/"runs"/r["run_id"]/"summary.json"
        if p.exists(): rows.append(_read(p))
    if not rows: raise ValueError("no results; retain execution ledger and diagnose failures")
    (batch/"local_large_tables").mkdir(exist_ok=True)
    data=[];series=[];bins=[];frame_audits={};fleet_audits=[];state_support=[];boundary=[]
    for r in rows:
        data.append(dict(run_id=r["run_id"],phase=r["phase"],load=r["load"],seed=r["seed"],tau=r["tau"],minGap=r["minGap"],
            changed_parameter=r["changed_parameter"],engineering_blockers=";".join(r["engineering_blockers"]),**scalar_metrics(r)))
        for b in r["time_bins"]: bins.append(dict(run_id=r["run_id"],**b))
        frames=pd.read_csv(batch/"runs"/r["run_id"]/"traffic_frames.csv")
        frame_audits[r["run_id"]]=frame_diagnostics(frames)
        demand=ET.parse(batch/r["demand_path"]).getroot().findall("vehicle")
        departed=set(pd.read_csv(batch/"runs"/r["run_id"]/"departures.csv").vehicle_id)
        fleet_audits.append(dict(run_id=r["run_id"],classes=[dict(type_id=f"t{i}",ngsim_code=t["code"],
            sumo_class=t["vClass"],length_m=t["length_m"],planned_share=t["share"],
            scheduled=sum(v.attrib["type"]==f"t{i}" for v in demand),
            inserted=sum(v.attrib["type"]==f"t{i}" and v.attrib["id"] in departed for v in demand)) for i,t in enumerate(plan["fleet"])]))
        support=pd.read_parquet(batch/"runs"/r["run_id"]/"state.parquet",columns=["ttc_s","measurement_status","speed_mps","time_s","vehicle_id","edge_id","longitudinal_position_m"])
        raw=_read(batch/"runs"/r["run_id"]/"run_audit.json")
        state_support.append(dict(run_id=r["run_id"],state_rows=len(support),
            full_network_valid_ttc_rows=int(support.measurement_status.eq("valid").sum()),
            full_network_valid_ttc_below_2s_rows=int((support.measurement_status.eq("valid")&support.ttc_s.lt(2)).sum()),
            full_network_low_speed_rows=int(support.speed_mps.lt(5).sum()),
            collisions=raw["collisions"],teleports=raw["teleports"]))
        slow=support[support.speed_mps.lt(5)]
        first=support.sort_values("time_s").drop_duplicates("vehicle_id")
        boundary.append(dict(run_id=r["run_id"],low_speed_edges=[dict(edge_id=e,rows=len(c),vehicles=c.vehicle_id.nunique(),
            minimum_position_m=c.longitudinal_position_m.min(),maximum_position_m=c.longitudinal_position_m.max(),
            first_s=c.time_s.min(),last_s=c.time_s.max(),minimum_speed_mps=c.speed_mps.min()) for e,c in slow.groupby("edge_id")],
            first_record_speed=dict(minimum_mps=float(first.speed_mps.min()),median_mps=float(first.speed_mps.median()),
                below_5mps_vehicles=int(first.speed_mps.lt(5).sum()),note="first recorded state within observation cadence, not exact departure-time speed"),
            bins=[dict(start_s=a,end_s=a+60,upstream_low_vehicle_s=float(((slow.time_s.gt(a))&slow.time_s.le(a+60)&slow.edge_id.eq("main_0")).sum()*.1)) for a in range(0,300,60)],
            departSpeed_semantics="max may be lowered for safe insertion; it does not force27.78m/s",
            pending_external_vs_low_onroad="distinct populations, both retained"))
        frames["bin"]=np.floor((frames.time_s-1e-8)/5).astype(int)
        for index,f in frames.groupby("bin"):
            n=f.local_vehicles.sum()
            series.append(dict(run_id=r["run_id"],start_s=int(index*5),end_s=int((index+1)*5),
                density=float(f.local_vehicles.mean()/.6),speed=float(f.local_speed_sum.sum()/n) if n else None,
                low_speed_fraction=float(f.local_low_speed_vehicles.sum()/n) if n else None,
                inserted_veh_h_lane=float(f.inserted_step.sum()*3600/5/3),exited_veh_h_lane=float(f.arrived_step.sum()*3600/5/3),
                through_veh_h_lane=float(f.local_crossings.sum()*3600/5/3),pending_end=int(f.pending.iloc[-1]),
                pending_max=int(f.pending.max()),present_mean=float(f.present.mean()),initial_share=0.))
    metrics=pd.DataFrame(data);time_series=pd.DataFrame(series)
    metrics.to_csv(batch/"run_metrics.csv",index=False);pd.DataFrame(bins).to_csv(batch/"time_bins_60s.csv",index=False)
    time_series.to_csv(batch/"time_series_5s.csv",index=False)
    paired=[]
    for r in rows:
        if r["phase"]!="phase2": continue
        base=next(b for b in rows if b["run_id"]==r["baseline_run_id"])
        a=scalar_metrics(r);b=scalar_metrics(base)
        paired.append(dict(run_id=r["run_id"],baseline_run_id=base["run_id"],load=r["load"],seed=r["seed"],
            changed_parameter=r["changed_parameter"],value=r[r["changed_parameter"]],
            delta={k:a[k]-b[k] if a[k] is not None and b[k] is not None else None for k in a},
            engineering_blockers=r["engineering_blockers"],demand_sha_equal=r["input_sha256"][r["demand_path"]]==base["input_sha256"][base["demand_path"]],
            warning="served traffic can differ despite identical configured demand; do not attribute all deltas to on-road behavior"))
    _write_json(batch/"parameter_response_matrix.json",dict(mode=MODE,pairs=paired,no_best_parameter_selected=True))
    _write_json(batch/"fleet_and_state_support_audit.json",dict(fleet_runs=fleet_audits,state_support=state_support,
        note="separate scheduled and inserted fleet; empirical annotations constrain engineering input only; missing risk is not zero risk"))
    _write_json(batch/"boundary_response_diagnostics.json",dict(runs=boundary,
        source="https://eclipse.dev/sumo/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#departspeed",
        interpretation="tau2 changes safe insertion and low-speed acceleration near upstream boundary; no local congestion equivalence"))
    _write_json(batch/"config.json",dict(mode=MODE,fixed=plan["fixed"],local_space=plan["local_space"],windows=plan["windows"],
        scientific_claim_eligible=False,tolerances="Tolerance Not Yet Justified",local_stratum_p2="Unresolved"))
    _write_json(batch/"fixed_parameter_manifest.json",dict(fixed=plan["fixed"],fleet=plan["fleet"],initialization=plan["initialization"],
        engineering_candidates_only=True,source_bindings=plan["source_bindings"],
        planned_single_parameter_pairs=16,completed_single_parameter_pairs=len(paired)))
    _write_json(batch/"run_manifest.json",dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),planned_runs=plan["runs"],
        attempts=ledger["attempts"],not_attempted=[r["run_id"] for r in plan["runs"] if r["run_id"] not in {a["run_id"] for a in ledger["attempts"]}],
        measurement_version="stage_0_2.formal_risk_measurement.v2 via existing SUMO adapter",mode=MODE))
    _write_json(batch/"numerical_method_audit.json",dict(runs=[dict(run_id=r["run_id"],runtime=r["numerical"],
        cadence_error_s=r["cadence_max_abs_error_s"],identity_duplicate_rows=r["duplicate_identity_time_rows"],
        gap_geometry_rows=r["net_gap_geometry_checked_rows"],gap_geometry_max_abs_m=r["net_gap_geometry_max_abs_m"],
        closing_sign_max_abs=r["closing_sign_max_error"]) for r in rows],
        repeatability=_read(batch/"phase1_checkpoint.json")["repeatability_control_verified"],time_step_search=False,
        full_run_core_exposure_equivalence=_read(batch/"runs"/plan["runs"][0]["run_id"]/"core_exposure_equivalence.json")))
    _write_json(batch/"traffic_input_output_audit.json",dict(runs=[dict(run_id=r["run_id"],configured_veh_h_lane=plan["loads"][r["load"]]["flow_veh_h_lane"],
        **r["accounting"],time_bins=r["time_bins"],delays=r["insertion_delays_s"],local_crossings=r["local_crossings"],
        frame_diagnostics=frame_audits[r["run_id"]],engineering_blockers=r["engineering_blockers"]) for r in rows],all_attempts_retained=True))
    _write_json(batch/"initialization_warmup_diagnostics.json",dict(primary_initial_vehicles=0,
        prior_Aplus=prior_initialization(repo,batch,refs),warmup_s_approved=None,
        rule="all five 60s bins retained; early/late fixed before simulation; no stable-speed requirement",
        runs=[dict(run_id=r["run_id"],time_bins=r["time_bins"],frame_diagnostics=frame_audits[r["run_id"]],sustained_low_speed_30s=r["sustained_local_low_speed_30s"]) for r in rows]))
    _write_json(batch/"local_kinematics_comparison.json",dict(real={g:w["interior_local_metrics"] for g,w in refs["diagnostics"]["windows"].items()},
        real_strata_summary=refs["strata"]["summary"],sumo=[dict(run_id=r["run_id"],metrics=r["local_metrics"],density=r["local_density_veh_km_lane"],low_speed=r["local_low_speed_fraction"]) for r in rows],
        scope_note="real interior720/660s,1lane-km vs SUMO full300s including empty start,.6lane-km; descriptive only"))
    _write_json(batch/"following_response_diagnostics.json",dict(runs=[dict(run_id=r["run_id"],positive_closing=r["local_positive_closing_fraction"],
        ttc_valid=r["local_ttc_valid_fraction"],following=r["local_following_fraction"],
        full_network_p2={k:v for k,v in r["full_network_p2"].items() if k!="event_boundaries"},local_stratum_p2="Unresolved") for r in rows],
        ngsim_sumo_status_crosswalk=NGSIM_STATUS_CROSSWALK,missing_reason_equivalence=MISSING_REASON_EQUIVALENCE,
        real_full_source_p2_uncertainty=refs["real_full"]["clustered_uncertainty"],
        no_missing_as_zero_risk=True,space_denominators_not_equated=True))
    _write_json(batch/"runtime_budget_audit.json",dict(limits=plan["budget"],attempts=len(ledger["attempts"]),
        total_run_wall_s=sum(a.get("wall_s",0) for a in ledger["attempts"]),
        peak_sampled_process_tree_rss_bytes=max(a.get("sampled_peak_process_tree_rss_bytes") or 0 for a in ledger["attempts"]),
        memory_scope="maximum of fully monitored attempts; final handoff attempt peak Unverified",
        incomplete_memory_attempts=[a["run_id"] for a in ledger["attempts"] if a.get("sampled_peak_process_tree_rss_bytes") is None],
        stop_reason=ledger.get("stop_reason"),design_deviations=ledger["design_deviations"],
        batch_elapsed_wall_s=__import__("time").time()-ledger["started_epoch_s"],
        disk_bytes=sum(p.stat().st_size for p in batch.rglob("*") if p.is_file()),
        failures=[a for a in ledger["attempts"] if a["status"]!="completed"],no_budget_expansion=True))
    _write_json(batch/"audit.json",dict(result_id=RESULT_ID,mode=MODE,scientific_claim_eligible=False,
        stage_0_5_gate="pending_simulation_sample",ready_to_start_stage_0_5_4b=False,
        protocol_lock_allowed=False,stage_1_1_allowed=False,tolerances="Tolerance Not Yet Justified",
        energy_distance_upper_bound="Not Identifiable",
        b0_experiment_validation_window_read=False,b0_experiment_validation_window_rows_materialised=0,
        validation_window_read="Not Certified" if validation_activity else "Unverified",
        validation_window_rows_materialised=None,
        validation_activity_audit="validation_activity_audit.json" if validation_activity else None,
        task_data_isolation_accepted=False,
        locked_holdout_accessed=False,raw_real_data_read=False,formal_calibration_started=False,stage_0_5_5_run=False,
        planned_runs=23,attempted_runs=len(ledger["attempts"]),completed_summaries=len(rows),optimization=False,
        engineering_blocking_runs=[r["run_id"] for r in rows if r["engineering_blockers"]],
        execution_design_deviations=ledger["design_deviations"],
        all_attempts_engineering_valid=not any(r["engineering_blockers"] for r in rows) and not ledger["design_deviations"],
        not_attempted_retained_in_manifest=True,local_stratum_p2="Unresolved"))
    _write_json(batch/"provenance.json",dict(result_id=RESULT_ID,created_at_utc=_utc_now(),python=platform.python_version(),
        plan_sha256=_sha256_file(batch/"experiment_plan.json"),code_sha256={str(p.relative_to(repo)).replace("\\","/"):_sha256_file(p) for p in [Path(__file__).resolve(),repo/"code/src/riskprop/stage_0_5_exploratory_response.py",repo/"code/scripts/run_stage_0_5_exploratory_response.py"]},
        git_base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),source_evidence_bindings=plan["source_bindings"],
        executed_source_sha256=plan["source_code_sha256"],
        current_source_lf_sha256={str(p.relative_to(repo)).replace("\\","/"):hashlib.sha256(p.read_bytes().replace(b"\r\n",b"\n")).hexdigest() for p in [Path(__file__).resolve(),repo/"code/src/riskprop/stage_0_5_exploratory_response.py",repo/"code/scripts/run_stage_0_5_exploratory_response.py"]},
        execution_ledger_sha256=_sha256_file(batch/"execution_ledger.json"),notes="all execution code and inputs frozen before simulation; scheduler stop bug patched only after manual batch close; no runs after patch; see execution_code_change_audit.json"))
    change=_read(batch/"execution_code_change_audit.json")
    current=repo/"code/src/riskprop/stage_0_5_exploratory_response.py"
    change["current_patched_sha256"]=_sha256_file(current)
    change["patch_diff"]="".join(__import__("difflib").unified_diff(
        (batch/change["snapshot_path"]).read_text(encoding="utf-8").splitlines(keepends=True),
        current.read_text(encoding="utf-8").splitlines(keepends=True),fromfile="frozen-executed",tofile="post-batch-patched"))
    _write_json(batch/"execution_code_change_audit.json",change)
    paths=_make_plots(batch,rows,metrics,time_series,refs)
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for r in rows:
        if not r["engineering_blockers"]: continue
        c=time_series[time_series.run_id.eq(r["run_id"])]
        axes[0].plot(c.end_s,c.pending_end,label=r["run_id"].replace("b0_",""))
        d=next(d for d in boundary if d["run_id"]==r["run_id"])
        axes[1].plot([v["end_s"] for v in d["bins"]],[v["upstream_low_vehicle_s"] for v in d["bins"]],marker="o",label=r["run_id"].replace("b0_",""))
    axes[0].set(xlabel="Time [s]",ylabel="Pending outside network [vehicles]")
    axes[1].set(xlabel="Fixed60s bin end [s]",ylabel="On-road upstream speed<5m/s [vehicle-s]")
    axes[0].legend(fontsize=7);fig.suptitle("SUMO Engineering Exploration: blocked tau2 boundary response")
    fig.tight_layout()
    for ext in ["png","svg"]:fig.savefig(batch/f"figures/09_boundary_response.{ext}",dpi=160,bbox_inches="tight")
    plt.close(fig);paths.append("09_boundary_response")
    _write_json(batch/"figure_index.json",dict(local_figures=[dict(png=f"figures/{p}.png",svg=f"figures/{p}.svg") for p in paths],
        matching_tables=["run_metrics.csv","time_bins_60s.csv","time_series_5s.csv","local_kinematics_comparison.json","boundary_response_diagnostics.json","local_large_tables/spacetime_cells.csv"],portable_figures=False))
    # Scientific interpretation and researcher decisions are written after reviewing
    # the complete numeric tables, not generated as an automatic acceptance score.
    net=ET.parse(batch/plan["network_path"]).getroot()
    _write_json(batch/"network_facts.json",dict(network_sha256=_sha256_file(batch/plan["network_path"]),
        normal_edges=[dict(id=e.attrib["id"],lanes=[dict(l.attrib) for l in e.findall("lane")]) for e in net.findall("edge") if not e.attrib["id"].startswith(":")],
        connections=[dict(c.attrib) for c in net.findall("connection")],
        active_route=["main_0","main_1","main_2"],ramp_demand=0,
        interpretation="three continuing mainline lanes; unused onramp/offramp; no lane drop or downstream restriction in this design; capacity not identified"))
    budget=_read(batch/"runtime_budget_audit.json")
    budget["disk_bytes"]=sum(p.stat().st_size for p in batch.rglob("*") if p.is_file())
    budget["engineering_blocking_runs"]=[r["run_id"] for r in rows if r["engineering_blockers"]]
    _write_json(batch/"runtime_budget_audit.json",budget)
    seal(batch)
    print(json.dumps(dict(completed=len(rows),attempted=len(ledger["attempts"]),figures=paths)),flush=True)
