"""Bounded B0 exploration. Frozen engineering inputs; no calibration or Gate.

Only pre-existing two-window summary evidence is consumed. Existing formal P2
and SUMO measurement semantics are reused without modifying approved sources.
"""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from .stage_0_5_calibration_readiness import _sha256_file, _write_json, _utc_now
from .stage_0_5_sumo import (
    CalibrationValidationGuard, CALIBRATION_VALIDATION_POLICY,
    _ensure_traci_importable, build_candidate_network, compute_sumo_measurements,
    extract_sumo_formal_p2_events, FORMAL_ALGORITHM_VERSION,
)

RESULT_ID="RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1"
MODE="exploratory_diagnostic_only"
REFERENCE_ID="RES-STAGE-0.5-CALIBRATION-GAPS-V1"
GROUPS=("us101__0750_0805","us101__0805_0820")


def build_plan() -> dict:
    fixed=dict(maxSpeed=27.78,speedFactor=1.,speedDev=0.,carFollowModel="Krauss",
        accel=2.6,decel=4.5,apparentDecel=4.5,emergencyDecel=9.,sigma=.5,
        actionStepLength=.1,sigmaStep=1.,internal_step_s=.05,recorded_step_s=.1,
        step_method_ballistic=True,threads=1,laneChangeModel="LC2013",ramp_demand=0,
        communication_enabled=False,source_risk_treatment_enabled=False,information_adoption_enabled=False)
    loads={"low":dict(flow_veh_h_lane=.75*1449.8181818181818,basis="75% of lower observed mainline flow; engineering contrast"),
           "medium":dict(flow_veh_h_lane=1449.8181818181818,basis="0805_0820 interior plane300m mainline per-lane passage rate"),
           "high":dict(flow_veh_h_lane=1648.,basis="0750_0805 interior plane300m mainline per-lane passage rate")}
    runs=[]
    for load in loads:
        for seed in [20261018,20261019]:
            runs.append(dict(run_id=f"b0_{load}_base_s{seed}",phase="phase1",load=load,
                seed=seed,tau=1.,minGap=2.5,internal_step_s=.05,changed_parameter=None))
    for load in ["medium","high"]:
        for seed in [20261018,20261019]:
            for parameter,value in [("tau",.5),("tau",2.),("minGap",1.),("minGap",3.)]:
                run=dict(run_id=f"b0_{load}_{parameter}{value:g}_s{seed}",phase="phase2",load=load,
                    seed=seed,tau=1.,minGap=2.5,internal_step_s=.05,changed_parameter=parameter,
                    baseline_run_id=f"b0_{load}_base_s{seed}")
                run[parameter]=value;runs.append(run)
    runs.append(dict(run_id="b0_medium_repeat_s20261018",phase="control",load="medium",
        seed=20261018,tau=1.,minGap=2.5,internal_step_s=.05,changed_parameter=None,
        baseline_run_id="b0_medium_base_s20261018"))
    return dict(result_id=RESULT_ID,mode=MODE,scientific_claim_eligible=False,
        ready_to_start_stage_0_5_4b=False,gate="pending_simulation_sample",
        tolerances="Tolerance Not Yet Justified",energy_distance_upper_bound="Not Identifiable",
        protocol_lock_allowed=False,stage_1_1_allowed=False,validation_window_read=False,
        fixed=fixed,loads=loads,seeds=[20261018,20261019],duration_s=300.,runs=runs,
        initialization=dict(initial_vehicles=0,space_distribution="empty network",
            initial_speed=None,initial_gap=None,initial_type_mix=None,
            departure_speed="max (free-speed upstream boundary, same for all conditions)",
            departure_lane="round robin 0,1,2",depart_position="base",demand="deterministic equally spaced total 3-lane arrival stream"),
        numerical_control="one identical .05s middle-baseline repeat; no .1s comparison or step search",
        execution_order=["phase1","checkpoint","control","checkpoint","phase2"],
        windows=dict(primary=[0,300],bins_s=60,early=[0,60],late=[240,300],
            warmup_s_approved=None,all_slices_retained=True),
        local_space=dict(edge="main_1",start_m=50.,end_m=250.,lanes=3,lane_km=.6),
        density_strata=dict(low_upper=42.8767,medium_upper=48.0828,status="descriptive exploration only"),
        descriptive_low_speed=dict(threshold_mps=5.,sustained_window_s=30.,bin_s=10.,not_acceptance=True),
        budget=dict(max_runs=23,batch_wall_s=7200,per_run_wall_s=240,
            process_tree_memory_bytes=2*1024**3,artifact_bytes=4*1024**3,
            expected_from_prior_s="23*116s=2668s recorder upper context; new full P2 cost not previously measured",
            regression_fixtures="separate testing, not B0 experimental configurations"),
        phase2_conditions=dict(complete_simulation=True,no_collisions=True,no_teleport=True,
            max_abs_conservation_residual=0,max_cadence_error_s=1e-6,max_gap_geometry_error_m=1e-6,
            runtime_settings_match=True,source_bindings_match=True,
            backlog_block="last3 60s end queues nondecreasing, end>max(10,5%scheduled); stop affected load, no replacement"),
        p2_scope="SUMO full-network exploratory rate; real sealed full-source rates separate; local/stratum formal P2 Unresolved")


def validate_plan(plan: dict) -> None:
    if plan["scientific_claim_eligible"] or plan["ready_to_start_stage_0_5_4b"] or plan["gate"]!="pending_simulation_sample":
        raise ValueError("B0 may not approve scientific admission")
    expected=build_plan()
    for field in ["fixed","loads","seeds","initialization","budget"]:
        if plan[field]!=expected[field]: raise ValueError(f"undeclared B0 design change: {field}")
    declared=[{k:r[k] for k in e} for r,e in zip(plan["runs"],expected["runs"])]
    if len(plan["runs"])!=23 or declared!=expected["runs"]:
        raise ValueError("undeclared run matrix")
    for r in plan["runs"]:
        if r["phase"]=="phase2":
            validate_pair(next(b for b in plan["runs"] if b["run_id"]==r["baseline_run_id"]),r)


def validate_pair(base: dict, run: dict) -> None:
    for key in ["seed","load","internal_step_s"]:
        if run[key]!=base[key]: raise ValueError(f"paired input mismatch {key}")
    changed=[k for k in ["tau","minGap"] if run[k]!=base[k]]
    if changed!=[run["changed_parameter"]]: raise ValueError("not a single-parameter contrast")


def local_mask(states: pd.DataFrame) -> pd.Series:
    return (states.edge_id.eq("main_1") & states.longitudinal_position_m.ge(50)
            & states.longitudinal_position_m.lt(250))


def local_density(state_rows: int, observed_s: float) -> float | None:
    return state_rows*.1/(observed_s*.6) if observed_s else None


def input_accounting(scheduled,departed,arrived,present,*,initial_ids) -> dict:
    return dict(scheduled_vehicles=scheduled,departed_vehicles=len(departed),arrived_vehicles=len(arrived),
        present_at_end=len(present),unserved_at_end=scheduled-len(departed),
        initial_scheduled=len(initial_ids),initial_departed=len(departed & initial_ids),
        initial_present_at_end=len(present & initial_ids),
        conservation_residual=len(departed)-len(arrived)-len(present))


def verify_frozen(root: Path, bindings: dict) -> None:
    for name,digest in bindings.items():
        target=(root/name).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file() or _sha256_file(target)!=digest:
            raise ValueError(f"frozen input mismatch: {name}")


def edge_exposure(states: pd.DataFrame, *, cadence=.1) -> dict:
    """Vectorized equivalent of unchanged compute_exposure (boundary-tested).

    No risk definition is selected here; two endpoint eligibility and the core
    identity/time/optional-frame adjacency requirements are preserved.
    """
    groups=[k for k in ["run_id","scenario_id","fixture_id","vehicle_id","incarnation_id"] if k in states]
    sort=[k for k in ["observation_index","frame_id","time_s","simulation_step"] if k in states]
    o=states.sort_values(groups+sort).reset_index(drop=True)
    p=o.shift();adj=pd.Series(True,index=o.index)
    for key in groups:
        adj &= o[key].eq(p[key]).fillna(False)
    for key in ["incarnation_id","leader_incarnation_id"]:
        adj &= o[key].notna() & p[key].notna() & ~o[key].astype(str).isin(["","None","nan","<NA>"]) & o[key].eq(p[key]).fillna(False)
    if "leader_id" in o:
        both=o.leader_id.notna() & p.leader_id.notna()
        adj &= ~both | o.leader_id.eq(p.leader_id).fillna(False)
    adj &= (o.time_s-p.time_s-cadence).abs().le(1e-6)
    for key in ["observation_index","frame_id","original_row_number"]:
        if key in o: adj &= o[key].sub(p[key]).eq(1)
    if "global_time_ms" in o: adj &= o.global_time_ms.sub(p.global_time_ms).sub(round(cadence*1000)).abs().le(1e-6)
    for key in ["identity_break","observation_gap"]:
        if key in o: adj &= ~o[key].fillna(True).astype(bool) & ~p[key].fillna(True).astype(bool)
    reliable=o.reliable_following_eligible.fillna(False).astype(bool)
    edge=adj & reliable & reliable.shift(fill_value=False)
    evaluable=o.measurement_status.isin(["valid","not_applicable"])
    closing=o.ttc_valid.fillna(False).astype(bool)
    f=int(edge.sum())*cadence
    e=int((edge & evaluable & evaluable.shift(fill_value=False)).sum())*cadence
    c=int((edge & closing & closing.shift(fill_value=False)).sum())*cadence
    return dict(reliable_following_exposure_s=f,p2_evaluable_following_exposure_s=e,
        reliable_closing_exposure_s=c,not_evaluable_following_exposure_s=f-e,
        p2_evaluable_following_vehicle_hours=e/3600,method="vectorized core adjacency equivalence tested")


def _summary_inputs(repo: Path) -> tuple[dict,dict]:
    """Guarded portable summary reads only; no raw/real-state reader is present."""
    paths={"diagnostics":(REFERENCE_ID,"diagnostics.json"),"strata":(REFERENCE_ID,"unified_strata.json"),
        "fleet":(REFERENCE_ID,"benchmark_plan.json"),"prior_runs":(REFERENCE_ID,"benchmark_summary.json"),
        "prior_numerics":(REFERENCE_ID,"benchmark_numerical_diagnostics.json"),
        "real_full":("RES-STAGE-0.5-CALIBRATION-READINESS-V1","calibration_source_analysis.json")}
    policy=copy.deepcopy(CALIBRATION_VALIDATION_POLICY);bindings={}
    for key,(rid,name) in paths.items():
        base=repo/"evidence/results"/rid
        manifest=json.loads((base/"manifest.json").read_text(encoding="utf-8"))
        digest=next(f["sha256"] for f in manifest["files"] if f["path"]==name)
        source="b0_summary::"+key;policy["calibration"].append(source);policy["source_bindings"][source]=digest
        bindings[key]=dict(path=str(base/name),sha256=digest,source=source)
    guard=CalibrationValidationGuard(policy)
    summaries={}
    for key,b in bindings.items():
        guard.require_source_read(b["path"],role="calibration",source=b["source"],purpose="B0 existing calibration summary only")
        summaries[key]=json.loads(Path(b["path"]).read_text(encoding="utf-8"))
    validate_reference_scope(summaries["diagnostics"])
    return summaries,dict(bindings=bindings,access_audit=guard.audit())


def validate_reference_scope(summary: dict) -> None:
    if set(summary["windows"])!=set(GROUPS): raise ValueError("unexpected real reference scope")


def prepare_batch(repo: Path, out: Path) -> None:
    if out.exists(): raise ValueError("refusing to overwrite B0 batch")
    out.mkdir(parents=True);(out/"inputs").mkdir();(out/"runs").mkdir()
    plan=build_plan();validate_plan(plan)
    refs,source=_summary_inputs(repo)
    observed=[next(x["mainline_veh_h_lane"] for x in refs["diagnostics"]["windows"][g]["interior_crossings"] if x["plane_m"]==300) for g in GROUPS]
    if not np.allclose(observed,[1648.,1449.8181818181818],rtol=0,atol=1e-8):
        raise ValueError("fixed demand candidates disagree with bound A+ reference")
    plan["fleet"]=refs["fleet"]["fleet"]
    plan["source_bindings"]=source["bindings"]
    plan["created_at_utc"]=_utc_now()
    plan["source_code_sha256"]={str(p.relative_to(repo)).replace("\\","/"):_sha256_file(p) for p in [
        Path(__file__).resolve(),repo/"code/scripts/run_stage_0_5_exploratory_response.py",
        repo/"code/src/riskprop/stage_0_5_sumo.py",repo/"code/src/riskprop/formal_risk_measurement.py",
        repo/"code/src/riskprop/ngsim_risk_calibration.py"]}
    plan["network_id"]="generic_highway_candidate"
    network=build_candidate_network(out/"inputs")
    plan["network_path"]=str(Path(network["network"]).relative_to(out)).replace("\\","/")
    # All demand and vType files are frozen now, including conditional phase2.
    for load,load_spec in plan["loads"].items():
        for seed in plan["seeds"]:
            rng=np.random.default_rng(seed)
            headway=3600/(load_spec["flow_veh_h_lane"]*3)
            vehicles=[]
            for i,t in enumerate(np.arange(headway,plan["duration_s"]-.1,headway)):
                v=int(rng.choice(3,p=[x["share"] for x in plan["fleet"]]))
                depart=np.ceil(t*10-1e-9)/10  # shared .1s departure grid, not dt-dependent rounding
                vehicles.append(f'<vehicle id="v{i:05d}" type="t{v}" route="through" depart="{depart:.1f}" departLane="{i%3}" departPos="base" departSpeed="max"/>')
            (out/"inputs"/f"demand_{load}_{seed}.rou.xml").write_text('<routes>\n<route id="through" edges="main_0 main_1 main_2"/>\n'+'\n'.join(vehicles)+'\n</routes>\n',encoding="utf-8",newline="\n")
    for run in plan["runs"]:
        key=f'tau{run["tau"]:g}_gap{run["minGap"]:g}'
        vpath=out/"inputs"/f"types_{key}.rou.xml"
        attrs={k:plan["fixed"][k] for k in ["maxSpeed","speedFactor","speedDev","carFollowModel","accel","decel","apparentDecel","emergencyDecel","sigma","actionStepLength","sigmaStep","laneChangeModel"]}
        lines=[]
        for i,fleet in enumerate(plan["fleet"]):
            values=dict(id=f"t{i}",vClass=fleet["vClass"],length=f'{fleet["length_m"]:.10f}',tau=run["tau"],minGap=run["minGap"],**attrs)
            lines.append('<vType '+' '.join(f'{k}="{v}"' for k,v in values.items())+'/>')
        vpath.write_text('<routes>\n'+'\n'.join(lines)+'\n</routes>\n',encoding="utf-8",newline="\n")
        run["vtype_path"]=vpath.relative_to(out).as_posix()
        run["demand_path"]=f'inputs/demand_{run["load"]}_{run["seed"]}.rou.xml'
        cfg=out/"inputs"/(run["run_id"]+".sumocfg")
        cfg.write_text(f'''<configuration>
<input><net-file value="generic_highway_candidate.net.xml"/><route-files value="{vpath.name},demand_{run['load']}_{run['seed']}.rou.xml"/></input>
<time><begin value="0"/><end value="300"/><step-length value="0.05"/></time>
<processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/><collision.action value="warn"/></processing>
<seed value="{run['seed']}"/>
</configuration>
''',encoding="utf-8",newline="\n")
        run["config_path"]=cfg.relative_to(out).as_posix()
        run["input_sha256"]={n:_sha256_file(out/n) for n in [run["config_path"],run["vtype_path"],run["demand_path"],plan["network_path"]]}
    _write_json(out/"real_reference_summary.json",refs)
    _write_json(out/"source_access_audit.json",source)
    _write_json(out/"experiment_plan.json",plan)
    _write_json(out/"frozen_input_manifest.json",{p.relative_to(out).as_posix():_sha256_file(p) for p in sorted((out/"inputs").iterdir()) if p.is_file()})
    plan_hash=_sha256_file(out/"experiment_plan.json")
    (out/"PLAN_SHA256").write_text(plan_hash+"  experiment_plan.json\n",encoding="utf-8",newline="\n")
    _write_json(out/"execution_ledger.json",dict(plan_sha256=plan_hash,started_at_utc=None,attempts=[],run_budget=23,design_deviations=[]))
    print(json.dumps(dict(plan_sha256=plan_hash,planned_runs=len(plan["runs"]),fixed=plan["fixed"],loads=plan["loads"])),flush=True)


def read_plan(batch: Path) -> dict:
    expected=(batch/"PLAN_SHA256").read_text().split()[0]
    if _sha256_file(batch/"experiment_plan.json")!=expected: raise ValueError("plan SHA mismatch")
    plan=json.loads((batch/"experiment_plan.json").read_text(encoding="utf-8"))
    validate_plan(plan)
    verify_frozen(batch,json.loads((batch/"frozen_input_manifest.json").read_text()))
    return plan


def _dist(values) -> dict:
    x=pd.to_numeric(pd.Series(values),errors="coerce");x=x[np.isfinite(x)]
    return dict(n=len(x),mean=float(x.mean()) if len(x) else None,
        sd=float(x.std()) if len(x)>1 else None,
        quantiles={str(q):float(x.quantile(q)) for q in [0,.01,.05,.1,.5,.9,.95,.99,1]} if len(x) else {})


def analyze_run(out: Path, plan: dict, spec: dict, run_audit: dict) -> dict:
    s=pd.read_parquet(out/"state.parquet")
    times=s.sort_values(["vehicle_id","time_s"]).groupby("vehicle_id").time_s.diff().dropna()
    cadence_error=float((times-.1).abs().max()) if len(times) else None
    duplicate=int(s.duplicated(["incarnation_id","time_s"]).sum())
    local=s[local_mask(s)]
    reliable=local.reliable_following_eligible
    stats={k:_dist(local.loc[mask,k]) for k,mask in [
        ("speed_mps",pd.Series(True,index=local.index)),("acceleration_mps2",pd.Series(True,index=local.index)),
        ("net_gap_m",reliable & local.net_gap_m.gt(0)),("closing_speed_mps",reliable),
        ("ttc_s",local.ttc_valid)]}
    stats["low_speed_gap_m"]=_dist(local.loc[reliable & local.speed_mps.lt(5) & local.net_gap_m.gt(0),"net_gap_m"])
    exposure=edge_exposure(s)
    if spec["run_id"]==plan["runs"][0]["run_id"]:
        from .stage_0_5_sumo import compute_exposure
        slow=compute_exposure(s,recorded_observation_step_s=.1)
        differences={k:exposure[k]-slow[k] for k in ["reliable_following_exposure_s","p2_evaluable_following_exposure_s","reliable_closing_exposure_s"]}
        _write_json(out/"core_exposure_equivalence.json",dict(differences_s=differences,maximum_allowed_float_error_s=1e-6,core_rules_unchanged=True))
        if max(abs(x) for x in differences.values())>1e-6: raise ValueError("full-run exposure differs from existing core")
    events,formal=extract_sumo_formal_p2_events(s,recorded_observation_step_s=.1)
    events.to_parquet(out/"full_network_exploratory_p2.parquet",index=False)
    frames=pd.read_csv(out/"traffic_frames.csv")
    bins=[]
    for a in range(0,300,60):
        f=frames[frames.time_s.gt(a)&frames.time_s.le(a+60)]
        c=local[local.time_s.gt(a)&local.time_s.le(a+60)]
        if f.empty: continue
        bins.append(dict(start_s=a,end_s=a+60,observed_s=len(f)*.1,
            density_veh_km_lane=float(f.local_vehicles.mean()/.6),
            mean_speed_mps=float(c.speed_mps.mean()) if len(c) else None,
            low_speed_fraction=float(c.speed_mps.lt(5).mean()) if len(c) else None,
            mean_present=float(f.present.mean()),pending_start=int(f.pending.iloc[0]),pending_end=int(f.pending.iloc[-1]),
            pending_max=int(f.pending.max()),inserted=int(f.inserted_step.sum()),arrived=int(f.arrived_step.sum()),
            crossings=int(f.local_crossings.sum()),initial_present=0,initial_local_share=0.,
            conservation_max_abs=int(f.conservation_residual.abs().max())))
    vals=s[s.net_gap_crosscheck_residual_m.notna()].net_gap_crosscheck_residual_m
    fingerprint=s[["time_s","vehicle_id","edge_id","lane_id","longitudinal_position_m",
        "speed_mps","acceleration_mps2","leader_id","net_gap_m","closing_speed_mps","ttc_s"]].copy()
    fingerprint=fingerprint.sort_values(["time_s","vehicle_id"])
    digest=hashlib.sha256(pd.util.hash_pandas_object(fingerprint,index=False).to_numpy().tobytes()).hexdigest()
    ten=[]
    for a in range(0,300,10):
        c=local[local.time_s.gt(a)&local.time_s.le(a+10)]
        ten.append(float(c.speed_mps.mean()) if len(c) else None)
    sustained=any(all(v is not None and v<5 for v in ten[i:i+3]) for i in range(len(ten)-2))
    summary=dict(**spec,status=run_audit["status"],failure=run_audit["failure"],mode=MODE,
        scientific_claim_eligible=False,numerical=run_audit["numerical"],runtime=run_audit["runtime"],
        accounting=run_audit["accounting"],plan_sha256=_sha256_file(out.parent.parent/"experiment_plan.json"),
        local_metrics=stats,local_density_veh_km_lane=local_density(len(local),300.),
        local_low_speed_fraction=float(local.speed_mps.lt(5).mean()) if len(local) else None,
        local_positive_closing_fraction=float(local.loc[reliable,"closing_speed_mps"].gt(1e-3).mean()) if reliable.any() else None,
        local_ttc_valid_fraction=float(local.ttc_valid.mean()) if len(local) else None,
        local_following_fraction=float(reliable.mean()) if len(local) else None,
        global_measurement_status_counts={str(k):int(v) for k,v in s.measurement_status.value_counts().items()},
        full_network_p2=dict(events=len(events),**exposure,
            event_rate_per_evaluable_vehicle_hour=len(events)/exposure["p2_evaluable_following_vehicle_hours"] if exposure["p2_evaluable_following_vehicle_hours"] else None,
            event_boundaries=events[[k for k in ["vehicle_id","leader_id","event_start_s","event_end_s","event_confirm_s","ttc_min_s","exit_reason"] if k in events]].to_dict("records"),
            formal_adapter_status=formal["equivalence_status"],authorization="B0 exploratory computation only; no measurement Gate"),
        local_stratum_formal_p2_rate="Unresolved",time_bins=bins,
        cadence_max_abs_error_s=cadence_error,duplicate_identity_time_rows=duplicate,
        net_gap_geometry_checked_rows=len(vals),net_gap_geometry_max_abs_m=float(vals.abs().max()) if len(vals) else None,
        closing_sign_max_error=float((s.closing_speed_mps-(s.speed_mps-s.leader_speed_mps)).abs().max()),
        state_fingerprint=digest,state_rows=len(s),state_sha256=_sha256_file(out/"state.parquet"),
        low_speed_10s_means=ten,sustained_local_low_speed_30s=sustained,
        local_crossings=int(frames.local_crossings.sum()),mainline_lane_changes=int(frames.lane_changes.sum()),
        insertion_delays_s=_dist(pd.read_csv(out/"departures.csv").delay_s))
    blockers=[]
    if summary["status"]!="completed": blockers.append("run_failure")
    if cadence_error is None or cadence_error>1e-6 or duplicate: blockers.append("cadence_or_identity")
    if summary["net_gap_geometry_max_abs_m"] is None or summary["net_gap_geometry_max_abs_m"]>1e-6: blockers.append("net_gap_geometry")
    if summary["closing_sign_max_error"]>1e-8: blockers.append("closing_sign")
    if run_audit["accounting"]["conservation_residual"] or frames.conservation_residual.abs().max(): blockers.append("conservation")
    if run_audit["collisions"] or run_audit["teleports"]: blockers.append("collision_or_teleport")
    if not run_audit["numerical"]["verified"]: blockers.append("runtime_settings")
    if summary["global_measurement_status_counts"].get("missing",0) or summary["global_measurement_status_counts"].get("invalid",0): blockers.append("measurement_quality")
    if len(bins)>=3:
        tails=[b["pending_end"] for b in bins[-3:]]
        if tails==sorted(tails) and tails[-1]>max(10,.05*run_audit["accounting"]["scheduled_vehicles"]): blockers.append("persistent_unserved_demand")
    summary["engineering_blockers"]=blockers
    _write_json(out/"summary.json",summary)
    return summary


def run_worker(batch: Path, run_id: str) -> None:
    """One frozen run; outer batch controller enforces hard wall/memory/disk caps."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    plan=read_plan(batch)
    spec=next(r for r in plan["runs"] if r["run_id"]==run_id)
    out=batch/"runs"/run_id
    if out.exists(): raise ValueError("refusing to overwrite run")
    out.mkdir()
    start=time.perf_counter()
    _ensure_traci_importable()
    import traci
    import traci.constants as c
    demand=ET.parse(batch/spec["demand_path"]).getroot().findall("vehicle")
    scheduled={v.attrib["id"]:float(v.attrib["depart"]) for v in demand}
    types={v.attrib["id"]:int(v.attrib["type"][1:]) for v in demand}
    grid=np.array(sorted(scheduled.values()))
    departed=set();arrived=set();collisions=set();teleports=set();present=set();departures=[]
    frames=[];rows=[];counts={};prev_record={};audit_prev={};ballistic=[];row_count=0;writer=None
    numerical={};failure=None;conn=None;tick_insert=0;tick_exit=0
    def flush():
        nonlocal rows,writer,row_count
        if not rows: return
        m=compute_sumo_measurements(pd.DataFrame(rows))
        table=pa.Table.from_pandas(m,preserve_index=False)
        if writer is None: writer=pq.ParquetWriter(out/"state.parquet",table.schema,compression="zstd")
        writer.write_table(table.cast(writer.schema));row_count+=len(rows);rows=[]
    command=[str(Path(traci.__file__).resolve().parents[2]/"bin/sumo.exe"),"-c",str((batch/spec["config_path"]).resolve()),
        "--no-step-log","true","--duration-log.disable","true","--error-log",str((out/"sumo_errors.log").resolve())]
    # Resolve through the same existing executable lookup used by Stage0.5.
    from .stage_0_5_sumo import _sumo_binary
    command[0]=_sumo_binary()
    _write_json(out/"run_config.json",dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),run=spec,fixed=plan["fixed"],command=command))
    try:
        traci.start(command,label=run_id)
        conn=traci.getConnection(run_id)
        options={k:conn.simulation.getOption(k) for k in ["step-method.ballistic","step-length","seed","time-to-teleport","threads","random"]}
        actual_types={}
        for i,fleet in enumerate(plan["fleet"]):
            tid=f"t{i}"
            actual_types[tid]={k:getattr(conn.vehicletype,method)(tid) for k,method in dict(
                tau="getTau",minGap="getMinGap",actionStepLength="getActionStepLength",maxSpeed="getMaxSpeed",
                length="getLength",vClass="getVehicleClass",sigma="getImperfection",accel="getAccel",decel="getDecel",
                apparentDecel="getApparentDecel",emergencyDecel="getEmergencyDecel",speedFactor="getSpeedFactor",speedDev="getSpeedDeviation").items()}
        conn.simulation.saveState(str((out/"runtime_initial_state.xml").resolve()))
        echo={v.attrib["id"]:v.attrib for v in ET.parse(out/"runtime_initial_state.xml").getroot().iter("vType")}
        checks=[]
        checks.append(options["step-method.ballistic"].lower() in ["true","1"])
        checks.append(abs(float(options["step-length"])-.05)<1e-10)
        checks.append(int(options["seed"])==spec["seed"])
        checks.append(int(options["threads"])==1)
        checks.append(options["random"].lower() in ["false","0"])
        checks.append(abs(conn.simulation.getDeltaT()-.05)<1e-10)
        for i,fleet in enumerate(plan["fleet"]):
            values=actual_types[f"t{i}"]
            expected={k:plan["fixed"][k] for k in ["actionStepLength","maxSpeed","sigma","accel","decel","apparentDecel","emergencyDecel","speedFactor","speedDev"]}
            expected.update(tau=spec["tau"],minGap=spec["minGap"],length=fleet["length_m"])
            checks.extend(abs(values[k]-v)<1e-8 for k,v in expected.items())
            checks.append(values["vClass"]==fleet["vClass"])
            checks.append(abs(float(echo.get(f"t{i}",{}).get("sigmaStep","nan"))-1)<1e-10)
        numerical=dict(options=options,actual_types=actual_types,runtime_vtype_echo=echo,
            verified=bool(all(checks)),checks=len(checks),sigmaStep_evidence="runtime save-state vType echo; TraCI has no direct sigmaStep getter")
        numerical["sumo_version"]=conn.getVersion()
        _write_json(out/"runtime_numerical_audit.json",numerical)
        if not numerical["verified"]: raise ValueError("declared runtime numerical/type settings did not take effect")
        sim_vars=(c.VAR_TIME,c.VAR_DEPARTED_VEHICLES_IDS,c.VAR_ARRIVED_VEHICLES_IDS,c.VAR_COLLIDING_VEHICLES_IDS,c.VAR_TELEPORT_STARTING_VEHICLES_IDS,c.VAR_PENDING_VEHICLES)
        conn.simulation.subscribe(sim_vars)
        variables=(c.VAR_SPEED,c.VAR_ACCELERATION,c.VAR_POSITION,c.VAR_LANE_ID,c.VAR_LANEPOSITION,c.VAR_ROAD_ID,c.VAR_LEADER)
        for step in range(1,6001):
            conn.simulationStep()
            sv=conn.simulation.getSubscriptionResults()
            actual_time=float(sv[c.VAR_TIME])
            if abs(actual_time-step*.05)>1e-6: raise ValueError("SUMO runtime clock disagrees with declared cadence")
            now=round(actual_time,6)
            new=sv[c.VAR_DEPARTED_VEHICLES_IDS];gone=sv[c.VAR_ARRIVED_VEHICLES_IDS]
            collisions.update(sv[c.VAR_COLLIDING_VEHICLES_IDS]);teleports.update(sv[c.VAR_TELEPORT_STARTING_VEHICLES_IDS])
            for vid in new:
                if vid in departed: raise ValueError("vehicle identity reused")
                departed.add(vid);tick_insert+=1
                departures.append(dict(vehicle_id=vid,scheduled_s=scheduled[vid],departed_s=now,delay_s=now-scheduled[vid],initial=False))
                conn.vehicle.subscribe(vid,variables,parameters={c.VAR_LEADER:("d",1000.)})
            arrived.update(gone);tick_exit+=len(gone)
            data=conn.vehicle.getAllSubscriptionResults()
            # Independent positional integration check on a fixed upstream ID subset.
            for vid in sorted(data)[:10]:
                v=data[vid];current=(v[c.VAR_ROAD_ID],v[c.VAR_LANE_ID],v[c.VAR_LANEPOSITION],v[c.VAR_SPEED],now)
                prior=audit_prev.get(vid)
                if prior and current[:2]==prior[:2] and abs(now-prior[4]-.05)<1e-8 and abs(current[3]-prior[3])>1e-5:
                    ballistic.append(abs(current[2]-prior[2]-(current[3]+prior[3])*.5*.05))
                audit_prev[vid]=current
            if step%2: continue
            present=set(data);nlocal=0;nlow=0;crossings=0;lane_changes=0;speed_sum=0;local_speed_sum=0;halted=0
            for vid,v in sorted(data.items()):
                road=v[c.VAR_ROAD_ID];lane=v[c.VAR_LANE_ID];pos=v[c.VAR_LANEPOSITION];speed=v[c.VAR_SPEED]
                islocal=road=="main_1" and 50<=pos<250
                nlocal+=islocal;nlow+=islocal and speed<5;halted+=speed<.1
                speed_sum+=speed;local_speed_sum+=speed if islocal else 0
                previous=prev_record.get(vid)
                if previous and previous[0]==road:
                    crossings+=road=="main_1" and previous[2]<150<=pos
                    lane_changes+=previous[1]!=lane
                prev_record[vid]=(road,lane,pos)
                leader=v[c.VAR_LEADER];lid=leader[0] if leader and leader[0] else None
                lv=data.get(lid);gap=leader[1]+spec["minGap"] if lid else np.nan
                residual=np.nan
                if lv and lv[c.VAR_ROAD_ID]==road and lv[c.VAR_LANE_ID]==lane:
                    physical=lv[c.VAR_LANEPOSITION]-plan["fleet"][types[lid]]["length_m"]-pos
                    residual=gap-physical
                obs=counts.get(vid,0);counts[vid]=obs+1
                rows.append(dict(run_id=run_id,scenario_id="us101_highway_baseline",fixture_id="b0_no_message",
                    experiment_mode="no_message_baseline",configured_seed=spec["seed"],simulation_step=step,
                    time_s=now,observation_index=obs,vehicle_id=vid,incarnation_id=run_id+"|"+vid,trajectory_id=run_id+"|"+vid,
                    edge_id=road,lane_id=lane,longitudinal_position_m=pos,x_m=v[c.VAR_POSITION][0],y_m=v[c.VAR_POSITION][1],
                    speed_mps=speed,acceleration_mps2=v[c.VAR_ACCELERATION],vehicle_type=f"t{types[vid]}",initial_vehicle=False,
                    vehicle_length_m=plan["fleet"][types[vid]]["length_m"],follower_min_gap_m=spec["minGap"],
                    leader_id=lid,leader_incarnation_id=run_id+"|"+lid if lv else None,
                    leader_identity_status="observed" if lv else "unresolved" if lid else "not_applicable",
                    leader_speed_mps=lv[c.VAR_SPEED] if lv else np.nan,leader_traci_distance_m=leader[1] if lid else np.nan,
                    net_gap_m=gap,net_gap_crosscheck_residual_m=residual))
            pending=len(sv[c.VAR_PENDING_VEHICLES])
            frames.append(dict(time_s=now,scheduled_due=int(np.searchsorted(grid,now,side="right")),
                departed=len(departed),arrived=len(arrived),present=len(present),pending=pending,
                inserted_step=tick_insert,arrived_step=tick_exit,local_crossings=crossings,lane_changes=lane_changes,
                local_vehicles=nlocal,local_low_speed_vehicles=nlow,halted=halted,
                speed_sum=speed_sum,local_speed_sum=local_speed_sum,
                conservation_residual=len(departed)-len(arrived)-len(present),initial_present=0))
            tick_insert=tick_exit=0
            if step%600==0: flush()
            if time.perf_counter()-start>plan["budget"]["per_run_wall_s"]-5: raise TimeoutError("worker wall cap")
    except Exception as exc:
        failure=f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try: conn.close()
            except Exception: pass
        flush()
        if writer is not None: writer.close()
    pd.DataFrame(frames).to_csv(out/"traffic_frames.csv",index=False)
    pd.DataFrame(departures,columns=["vehicle_id","scheduled_s","departed_s","delay_s","initial"]).to_csv(out/"departures.csv",index=False)
    numerical["ballistic_displacement_checked_edges"]=len(ballistic)
    numerical["ballistic_displacement_max_abs_m"]=float(max(ballistic)) if ballistic else None
    if not ballistic or max(ballistic)>1e-6: numerical["verified"]=False
    run_audit=dict(status="failed" if failure else "completed",failure=failure,mode=MODE,
        numerical=numerical,accounting=input_accounting(len(demand),departed,arrived,present,initial_ids=set()),
        collisions=sorted(collisions),teleports=sorted(teleports),
        runtime=dict(sumo_recording_wall_s=time.perf_counter()-start,output_rows=row_count))
    _write_json(out/"run_audit.json",run_audit)
    if row_count:
        summary=analyze_run(out,plan,spec,run_audit)
        summary["runtime"]["total_worker_wall_s"]=time.perf_counter()-start
        _write_json(out/"summary.json",summary)
        print(json.dumps(dict(run_id=run_id,status=summary["status"],blockers=summary["engineering_blockers"],
            speed=summary["local_metrics"]["speed_mps"]["mean"],density=summary["local_density_veh_km_lane"],
            p2=summary["full_network_p2"]["events"],wall_s=summary["runtime"]["total_worker_wall_s"])),flush=True)
    elif failure: raise RuntimeError(failure)


def phase1_checkpoint(batch: Path) -> dict:
    plan=read_plan(batch);rows=[]
    for r in plan["runs"]:
        if r["phase"]!="phase1": continue
        p=batch/"runs"/r["run_id"]/"summary.json"
        rows.append(json.loads(p.read_text()) if p.exists() else dict(**r,engineering_blockers=["not_completed"]))
    global_blockers=[r["run_id"] for r in rows if set(r["engineering_blockers"])-{"persistent_unserved_demand"}]
    allowed=[]
    for load in ["medium","high"]:
        if not global_blockers and all(not r["engineering_blockers"] for r in rows if r["load"]==load): allowed.append(load)
    control=next(r for r in plan["runs"] if r["phase"]=="control")
    cp=batch/"runs"/control["run_id"]/"summary.json"
    repeat=None
    if cp.exists():
        c=json.loads(cp.read_text());base=json.loads((batch/"runs"/control["baseline_run_id"]/"summary.json").read_text())
        repeat=c["state_fingerprint"]==base["state_fingerprint"] and not c["engineering_blockers"]
        if not repeat: allowed=[]
    result=dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),phase="phase1_diagnostic_checkpoint",
        mode=MODE,scientific_claim_eligible=False,scientific_gate="pending_simulation_sample",
        global_blocking_runs=global_blockers,phase2_eligible_loads=allowed,
        repeatability_control_verified=repeat,
        runs=[{k:r.get(k) for k in ["run_id","load","seed","local_density_veh_km_lane","local_low_speed_fraction","accounting","engineering_blockers"]} for r in rows],
        all_phase1_runs_retained=True,formal_calibration_authorized=False)
    _write_json(batch/"phase1_checkpoint.json",result)
    lines=["# B0 first-phase diagnostic checkpoint\n",f"Plan SHA: {result['plan_sha256']}\n",
        f"Engineering-eligible phase2 loads: {allowed}; repeat control: {repeat}.\n",
        "All six predefined results are retained; this is not scientific acceptance.\n"]
    for r in rows:
        lines.append(json.dumps({k:r.get(k) for k in ["run_id","local_density_veh_km_lane","local_low_speed_fraction","accounting","engineering_blockers"]})+"\n")
    (batch/"PHASE1_DIAGNOSTIC.md").write_text("\n".join(lines),encoding="utf-8",newline="\n")
    print(json.dumps(result),flush=True)
    return result


def stop_after_attempt(attempt: dict) -> bool:
    """A successful process exit does not clear blocking engineering evidence."""
    return attempt["status"]!="completed" or bool(attempt.get("engineering_blockers"))


def execute_phase(batch: Path, phase: str) -> None:
    import psutil
    plan=read_plan(batch)
    repo=Path(__file__).resolve().parents[3]
    for relative,digest in plan["source_code_sha256"].items():
        if _sha256_file(repo/relative)!=digest: raise ValueError("execution code changed since plan freeze; new plan version required")
    ledger=json.loads((batch/"execution_ledger.json").read_text())
    allowed=["low","medium","high"]
    if phase in ["phase2","control"]:
        if not (batch/"phase1_checkpoint.json").exists(): raise ValueError("emit phase1 diagnostic checkpoint first")
        checkpoint=json.loads((batch/"phase1_checkpoint.json").read_text())
        if checkpoint["plan_sha256"]!=_sha256_file(batch/"experiment_plan.json"): raise ValueError("checkpoint plan mismatch")
        allowed=checkpoint["phase2_eligible_loads"]
        if phase=="phase2" and checkpoint["repeatability_control_verified"] is not True:
            raise ValueError("numerical repeatability control not verified")
    if ledger["started_at_utc"] is None:
        ledger["started_at_utc"]=_utc_now();ledger["started_epoch_s"]=time.time()
    def size(): return sum(p.stat().st_size for p in batch.rglob("*") if p.is_file())
    for spec in plan["runs"]:
        if spec["phase"]!=phase or spec["load"] not in allowed: continue
        if any(a["run_id"]==spec["run_id"] for a in ledger["attempts"]): raise ValueError("run already attempted; no silent retry")
        if len(ledger["attempts"])>=23 or time.time()-ledger["started_epoch_s"]>=7200 or size()>plan["budget"]["artifact_bytes"]:
            ledger["stop_reason"]="batch resource cap";break
        attempt=dict(run_id=spec["run_id"],phase=phase,started_at_utc=_utc_now(),plan_sha256=_sha256_file(batch/"experiment_plan.json"),status="running")
        ledger["attempts"].append(attempt);_write_json(batch/"execution_ledger.json",ledger)
        logfile=batch/(spec["run_id"]+".worker.log")
        start=time.monotonic();peak=0;reason=None
        with logfile.open("w",encoding="utf-8") as log:
            process=subprocess.Popen([__import__("sys").executable,str(repo/"code/scripts/run_stage_0_5_exploratory_response.py"),
                "worker","--batch",str(batch.resolve()),"--run-id",spec["run_id"]],stdout=log,stderr=subprocess.STDOUT,cwd=repo)
            parent=psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    rss=parent.memory_info().rss+sum(c.memory_info().rss for c in parent.children(recursive=True) if c.is_running())
                    peak=max(peak,rss)
                    if rss>plan["budget"]["process_tree_memory_bytes"]: reason="memory_cap"
                except psutil.Error: pass
                if time.monotonic()-start>240: reason="per_run_wall_cap"
                if time.time()-ledger["started_epoch_s"]>7200: reason="batch_wall_cap"
                if size()>plan["budget"]["artifact_bytes"]: reason="disk_cap"
                if reason:
                    for child in parent.children(recursive=True):
                        try: child.terminate()
                        except psutil.Error: pass
                    try: parent.terminate()
                    except psutil.Error: pass
                    break
                time.sleep(.25)
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill();process.wait()
        summary_path=batch/"runs"/spec["run_id"]/"summary.json"
        success=process.returncode==0 and summary_path.is_file()
        attempt.update(status="completed" if success else "failed",exit_code=process.returncode,
            wall_s=time.monotonic()-start,sampled_peak_process_tree_rss_bytes=peak,memory_sample_s=.25,
            artifact_bytes_after=size(),failure=reason)
        if success:
            summary=json.loads(summary_path.read_text())
            attempt["engineering_blockers"]=summary["engineering_blockers"]
            attempt["summary_sha256"]=_sha256_file(summary_path)
            print(json.dumps(dict(run_id=spec["run_id"],status=attempt["status"],wall_s=attempt["wall_s"],
                peak_MB=peak/1e6,density=summary["local_density_veh_km_lane"],
                speed=summary["local_metrics"]["speed_mps"]["mean"],p2=summary["full_network_p2"]["events"],
                blockers=summary["engineering_blockers"])),flush=True)
        else:
            attempt["failure"]=reason or "worker_failed_or_summary_missing"
            print(json.dumps(attempt),flush=True)
        _write_json(batch/"execution_ledger.json",ledger)
        if stop_after_attempt(attempt):
            ledger["stop_reason"]="run failure or engineering blocker: stop batch; version plan before retry"
            _write_json(batch/"execution_ledger.json",ledger);break
