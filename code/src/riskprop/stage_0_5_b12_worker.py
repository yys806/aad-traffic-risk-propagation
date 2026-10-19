"""Read-only SUMO observer; numerical audit screens every 0.05s adjacent edge."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .stage_0_5_b12_runtime import read,write,sha,load_plan,FIXED
from .stage_0_5_b12_observation import NumericalCoverage,ScopedAccounting,queue_snapshot,QueueTracker
from .stage_0_5_b12_network import coordinate_support
from .stage_0_5_sumo import _sumo_binary,_ensure_traci_importable,compute_sumo_measurements


def runtime_settings(conn,plan,spec,out):
    options={k:conn.simulation.getOption(k) for k in ["step-method.ballistic","step-length","seed","threads","time-to-teleport","random"]}
    checks=[options["step-method.ballistic"].lower() in ["1","true"],abs(float(options["step-length"])-.05)<1e-10,
            int(options["seed"])==spec["seed"],int(options["threads"])==1,options["random"].lower() in ["0","false"],
            abs(conn.simulation.getDeltaT()-.05)<1e-10,options["time-to-teleport"]=="-1"]
    conn.simulation.saveState(str(out/"runtime_initial_state.xml"))
    echo={v.attrib["id"]:dict(v.attrib) for v in ET.parse(out/"runtime_initial_state.xml").getroot().iter("vType")}
    actual={}
    for i,f in enumerate(plan["fleet"]):
        tid=f"t{i}"
        actual[tid]={k:getattr(conn.vehicletype,method)(tid) for k,method in dict(
            tau="getTau",minGap="getMinGap",actionStepLength="getActionStepLength",maxSpeed="getMaxSpeed",length="getLength",vClass="getVehicleClass",
            sigma="getImperfection",accel="getAccel",decel="getDecel",apparentDecel="getApparentDecel",emergencyDecel="getEmergencyDecel",
            speedFactor="getSpeedFactor",speedDev="getSpeedDeviation").items()}
        for k,v in actual[tid].items():
            expected=f["length_m"] if k=="length" else f["vClass"] if k=="vClass" else FIXED[k]
            checks.append(v==expected if isinstance(expected,str) else abs(v-expected)<1e-8)
        checks.extend(echo.get(tid,{}).get(k)==str(v) if isinstance(v,str) else abs(float(echo.get(tid,{}).get(k,"nan"))-v)<1e-8
                      for k,v in [("carFollowModel","Krauss"),("laneChangeModel","LC2013"),("sigmaStep",1.)])
    version=conn.getVersion();checks.append("1.26.0" in version[1])
    tls=[]
    if spec["condition"]=="C":
        logic=next(l for l in conn.trafficlight.getAllProgramLogics("hwy_j2") if l.programID=="b12_supply_v1")
        tls=[dict(duration=p.duration,state=p.state) for p in logic.phases]
        expected=[23.8,6.2,30.] if spec["duration_s"]==600 else [5.,6.2,48.8]
        checks.append([p["duration"] for p in tls]==expected)
    return dict(options=options,actual_types=actual,runtime_echo=echo,sumo_version=version,tls=tls,
                verified=bool(all(checks)),checks=len(checks),traci_vehicle_control=False,
                control_basis="Frozen read-only worker API; route/vType inputs checked; no vehicle setter or dynamic control called")


def run_worker(batch,run_id,plan_name):
    import pyarrow as pa
    import pyarrow.parquet as pq
    plan=load_plan(batch,plan_name);spec=next(r for r in plan["runs"] if r["run_id"]==run_id)
    out=batch/"runs"/run_id;out.mkdir(exist_ok=True)
    if (out/"summary.json").exists():raise PermissionError("no retry/overwrite")
    _ensure_traci_importable();import traci;import traci.constants as c
    support=coordinate_support(batch/spec["network"])
    demand=ET.parse(batch/spec["demand"]).getroot().findall("vehicle")
    scheduled={v.attrib["id"]:float(v.attrib["depart"]) for v in demand}
    assigned_lane={v.attrib["id"]:v.attrib["departLane"] for v in demand}
    types={v.attrib["id"]:int(v.attrib["type"][1:]) for v in demand}
    times=np.array(sorted(scheduled.values()))
    coverage=NumericalCoverage();accounting=ScopedAccounting(spec["local_space"]);tracker=QueueTracker(plan["queue_config"])
    previous={};raw=[];recorded=[];frames=[];queue=[];snapshots=[];departures=[]
    writers={};row_counts=Counter();mapping_checks=Counter();max_map_residual=0.;mapping_examples=[]
    same_lane_gap_checks=0;max_gap_residual=0.;lane_changes=0;edge_transitions=0;junction_states=0
    lanes_seen=set();edges_seen=set();collisions=set();teleports=set();settings={};failure=None;conn=None
    begin=time.monotonic();tick_insert=tick_exit=0
    def flush(name,rows,measure=False):
        if not rows:return
        df=pd.DataFrame(rows)
        if measure:df=compute_sumo_measurements(df)
        table=pa.Table.from_pandas(df,preserve_index=False)
        if name not in writers:writers[name]=pq.ParquetWriter(out/(name+".parquet"),table.schema,compression="zstd")
        writers[name].write_table(table.cast(writers[name].schema));row_counts[name]+=len(rows);rows.clear()
    command=[_sumo_binary(),"-c",str(batch/spec["config"]),"--no-step-log","true","--duration-log.disable","true",
             "--error-log",str(out/"sumo_errors.log")]
    write(out/"run_config.json",dict(plan_sha256=sha(batch/plan_name),run=spec,fixed=plan["fixed"],command=command,
          observation_version="b12-integration-v1",vehicle_control=False))
    try:
        traci.start(command,label=run_id);conn=traci.getConnection(run_id)
        settings=runtime_settings(conn,plan,spec,out)
        write(out/"runtime_settings.json",settings)
        if not settings["verified"]:raise ValueError("runtime_configuration_mismatch")
        simvars=(c.VAR_TIME,c.VAR_DEPARTED_VEHICLES_IDS,c.VAR_ARRIVED_VEHICLES_IDS,c.VAR_COLLIDING_VEHICLES_IDS,
                 c.VAR_TELEPORT_STARTING_VEHICLES_IDS,c.VAR_PENDING_VEHICLES)
        conn.simulation.subscribe(simvars)
        vv=(c.VAR_SPEED,c.VAR_ACCELERATION,c.VAR_POSITION,c.VAR_LANE_ID,c.VAR_LANEPOSITION,c.VAR_ROAD_ID,c.VAR_LEADER,
            c.VAR_LASTACTIONTIME,c.VAR_LENGTH,c.VAR_TYPE,c.VAR_DISTANCE)
        for tick in range(1,round(spec["duration_s"]/.05)+1):
            conn.simulationStep();sv=conn.simulation.getSubscriptionResults();now=float(sv[c.VAR_TIME])
            if abs(now-tick*.05)>1e-8:raise ValueError("runtime_clock")
            new=sv[c.VAR_DEPARTED_VEHICLES_IDS];gone=sv[c.VAR_ARRIVED_VEHICLES_IDS]
            collisions.update(sv[c.VAR_COLLIDING_VEHICLES_IDS]);teleports.update(sv[c.VAR_TELEPORT_STARTING_VEHICLES_IDS])
            if collisions or teleports:raise ValueError("collision_or_teleport")
            for vid in new:
                if vid not in scheduled:raise ValueError("unplanned_vehicle")
                conn.vehicle.subscribe(vid,vv,parameters={c.VAR_LEADER:("d",1000.)})
                departures.append(dict(vehicle_id=vid,scheduled_s=scheduled[vid],departed_s=now,delay_s=now-scheduled[vid],initial=False))
            data=conn.vehicle.getAllSubscriptionResults();current={}
            for vid,v in data.items():
                length=v[c.VAR_LENGTH];cls=types[vid]
                if abs(length-plan["fleet"][cls]["length_m"])>1e-8 or v[c.VAR_TYPE]!=f"t{cls}":raise ValueError("runtime_fleet_identity")
                r=dict(run_id=run_id,vehicle_id=vid,incarnation_id=run_id+"|"+vid,time_s=now,
                       edge_id=v[c.VAR_ROAD_ID],lane_id=v[c.VAR_LANE_ID],position_m=v[c.VAR_LANEPOSITION],
                       speed_mps=v[c.VAR_SPEED],acceleration_mps2=v[c.VAR_ACCELERATION],last_action_time_s=v[c.VAR_LASTACTIONTIME],
                       length_m=length,traveled_distance_m=v[c.VAR_DISTANCE],x_m=v[c.VAR_POSITION][0],y_m=v[c.VAR_POSITION][1],
                       traci_vehicle_control=False,numerical_config_verified=True)
                current[vid]=r;raw.append(r);lanes_seen.add(r["lane_id"]);edges_seen.add(r["edge_id"])
                junction_states+=r["edge_id"].startswith(":")
                prior=previous.get(vid)
                if prior:
                    a=coverage.add(prior,r)
                    if a["blocker"]:raise ValueError(a["blocker"])
                    lane_changes+=prior["edge_id"]==r["edge_id"] and prior["lane_id"]!=r["lane_id"]
                    edge_transitions+=prior["edge_id"]!=r["edge_id"]
                    oldmap=support["lanes"].get(prior["lane_id"]);newmap=support["lanes"].get(r["lane_id"])
                    if oldmap and newmap and oldmap["path"]==newmap["path"]:
                        route_delta=newmap["offset_m"]+r["position_m"]-oldmap["offset_m"]-prior["position_m"]
                        distance_delta=r["traveled_distance_m"]-prior["traveled_distance_m"]
                        residual=route_delta-distance_delta
                        key="cross_edge" if prior["edge_id"]!=r["edge_id"] else "same_edge"
                        mapping_checks[key]+=1;max_map_residual=max(max_map_residual,abs(residual))
                        if key=="cross_edge" and len(mapping_examples)<8:mapping_examples.append(dict(before=prior,after=r,route_delta_m=route_delta,distance_delta_m=distance_delta,residual_m=residual))
                        if abs(residual)>1e-6:raise ValueError("path_coordinate_distance_crosscheck")
                lead=v[c.VAR_LEADER];lid=lead[0] if lead and lead[0] else None;lv=data.get(lid)
                if lv and lv[c.VAR_LANE_ID]==r["lane_id"]:
                    gap=lead[1]+FIXED["minGap"];physical=lv[c.VAR_LANEPOSITION]-lv[c.VAR_LENGTH]-r["position_m"]
                    same_lane_gap_checks+=1;max_gap_residual=max(max_gap_residual,abs(gap-physical))
                    if abs(gap-physical)>1e-6:raise ValueError("physical_gap_geometry")
                if tick%2==0:
                    recorded.append(dict(run_id=run_id,scenario_id="us101_highway_baseline",fixture_id="b12_no_message",
                        experiment_mode="no_message_baseline",configured_seed=spec["seed"],simulation_step=tick,time_s=now,
                        observation_index=tick//2,vehicle_id=vid,incarnation_id=r["incarnation_id"],trajectory_id=r["incarnation_id"],
                        edge_id=r["edge_id"],lane_id=r["lane_id"],longitudinal_position_m=r["position_m"],x_m=r["x_m"],y_m=r["y_m"],
                        speed_mps=r["speed_mps"],acceleration_mps2=r["acceleration_mps2"],vehicle_type=f"t{cls}",initial_vehicle=False,
                        vehicle_length_m=length,follower_min_gap_m=FIXED["minGap"],leader_id=lid,
                        leader_incarnation_id=run_id+"|"+lid if lv else None,
                        leader_identity_status="observed" if lv else "unresolved" if lid else "not_applicable",
                        leader_speed_mps=lv[c.VAR_SPEED] if lv else np.nan,leader_traci_distance_m=lead[1] if lid else np.nan,
                        net_gap_m=lead[1]+FIXED["minGap"] if lid else np.nan,
                        net_gap_crosscheck_residual_m=(lead[1]+FIXED["minGap"]-(lv[c.VAR_LANEPOSITION]-lv[c.VAR_LENGTH]-r["position_m"])) if lv and lv[c.VAR_LANE_ID]==r["lane_id"] else np.nan))
            # Departures are processed on [t-h,t), so departures scheduled AT t
            # are not due until the following internal step. TraCI pending is
            # checked independently rather than inventing a balance.
            due=int(np.searchsorted(times,now-1e-8,side="right"))
            f=accounting.update(current,new,gone,due,now)
            actual_pending=set(sv[c.VAR_PENDING_VEHICLES])
            if len(actual_pending)!=f["external_pending"]:raise ValueError("pending_demand_accounting")
            tick_insert+=len(new);tick_exit+=len(gone)
            if tick%2==0:
                local=[r for r in current.values() if r["edge_id"]==spec["local_space"]["edge"] and spec["local_space"]["start_m"]<=r["position_m"]<spec["local_space"]["end_m"]]
                f.update(inserted_step=tick_insert,arrived_step=tick_exit,local_low_speed_vehicles=sum(r["speed_mps"]<5 for r in local),
                         local_speed_sum=sum(r["speed_mps"] for r in local),onroad_low_vehicles=sum(r["speed_mps"]<5 for r in current.values()),
                         stopped=sum(r["speed_mps"]<.1 for r in current.values()),
                         tls_state=conn.trafficlight.getRedYellowGreenState("hwy_j2") if spec["condition"]=="C" else "none")
                frames.append(f);tick_insert=tick_exit=0
            if tick%20==0:
                # All assigned pending lanes must independently lack sufficient
                # physical front-to-rear insertion space. No control is applied.
                pending_lanes={assigned_lane[v] for v in actual_pending}
                blocked={}
                for lane in pending_lanes:
                    first=min([r["position_m"]-r["length_m"] for r in current.values() if r["lane_id"]=="main_0_"+lane] or [float("inf")])
                    required=max([plan["fleet"][types[v]]["length_m"]+FIXED["minGap"] for v in actual_pending if assigned_lane[v]==lane])
                    blocked[lane]=dict(nearest_rear_m=first if np.isfinite(first) else None,required_front_space_m=required,blocked=first<required)
                physical=bool(blocked) and all(v["blocked"] for v in blocked.values())
                q=queue_snapshot(list(current.values()),now,support,plan["queue_config"],pending=len(actual_pending),
                                 physical_entry_space=physical,downstream_context=True)
                qual=tracker.update(q)
                snapshots.append(dict(q,qualification=qual,entry_space_by_pending_lane=blocked))
                queue.append(dict(qual,components=len(q["components"]),low_vehicles=q["low_vehicles"],pending=len(actual_pending),
                                  upstream_boundary_m=min([c["upstream_boundary_m"] for c in q["components"]] or [None]),
                                  physical_entry_space_observed=physical))
            previous=current
            if tick%100==0:flush("internal_states",raw);flush("state",recorded,True)
            if time.monotonic()-begin>plan["limits"]["per_run_wall_s"]-5:raise TimeoutError("worker_wall_limit")
    except Exception as exc:failure=f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try:conn.close()
            except Exception:pass
        flush("internal_states",raw);flush("state",recorded,True)
        for writer in writers.values():writer.close()
    pd.DataFrame(frames).to_csv(out/"traffic_frames.csv",index=False)
    pd.DataFrame(departures).to_csv(out/"departures.csv",index=False)
    write(out/"numerical_branch_coverage.json",coverage.summary())
    write(out/"queue_snapshots.json",snapshots);write(out/"queue_qualifications.json",queue)
    write(out/"coordinate_runtime_audit.json",dict(checks=dict(mapping_checks),max_abs_distance_residual_m=max_map_residual,
          junction_states=junction_states,examples=mapping_examples,paths=support["path_checks"],
          lanes_seen=sorted(lanes_seen),edges_seen=sorted(edges_seen),edge_transitions=edge_transitions,lane_changes=lane_changes,
          physical_gap_checks=same_lane_gap_checks,max_abs_physical_gap_residual_m=max_gap_residual))
    last=frames[-1] if frames else {}
    blockers=[failure] if failure else []
    summary=dict(run_id=run_id,condition=spec["condition"],status="failed" if failure else "completed_valid",engineering_blockers=blockers,
        diagnostic_warnings=[],plan_sha256=sha(batch/plan_name),numerical=coverage.summary(),runtime_settings=settings,
        observed_s=last.get("time_s",0),planned_s=spec["duration_s"],actual_inserted=len(accounting.departed),actual_exited=len(accounting.arrived),
        present=len(previous),pending_end=last.get("external_pending"),max_pending=max([f["external_pending"] for f in frames] or [0]),
        local_entered=accounting.local_in,local_exited=accounting.local_out,local_vehicle_s=accounting.local_vehicle_s,
        lane_changes=lane_changes,edge_transitions=edge_transitions,junction_states=junction_states,
        coordinate_crosschecks=dict(mapping_checks),max_coordinate_residual_m=max_map_residual,
        max_gap_residual_m=max_gap_residual,gap_checks=same_lane_gap_checks,
        queue_state_counts=dict(Counter(q["state"] for q in queue)),
        first_times={k:next((q["time_s"] for q in queue if q.get(field)),None) for k,field in [
            ("internal_queue","onroad_queue_observed"),("inlet_queue","inlet_adjacent_queue_observed"),
            ("supported_spillback","entry_spillback_supported"),("upstream_extension","upstream_extension_observed")]},
        first_internal_low_s=next((f["time_s"] for f in frames if f["onroad_low_vehicles"]>0),None),
        first_pending_s=next((f["time_s"] for f in frames if f["external_pending"]>0),None),
        collisions=sorted(collisions),teleports=sorted(teleports),failure=failure,
        runtime=dict(total_worker_wall_s=time.monotonic()-begin,rows=dict(row_counts)),scientific_claim_eligible=False)
    if spec["duration_s"]==600 and not failure:
        summary.update(analyze_traffic(out,plan,spec))
        summary["runtime"]["total_worker_wall_s"]=time.monotonic()-begin
    write(out/"summary.json",summary)
    print("B12_WORKER "+run_id+" "+summary["status"]+" "+str(failure),flush=True)


def analyze_traffic(out,plan,spec):
    from .stage_0_5_exploratory_response import _dist,edge_exposure
    from .stage_0_5_sumo import extract_sumo_formal_p2_events
    start=time.monotonic();s=pd.read_parquet(out/"state.parquet");f=pd.read_csv(out/"traffic_frames.csv")
    space=spec["local_space"]
    local=s[s.edge_id.eq(space["edge"]) & s.longitudinal_position_m.ge(space["start_m"]) & s.longitudinal_position_m.lt(space["end_m"])]
    reliable=local.reliable_following_eligible
    metrics={k:_dist(local.loc[mask,k]) for k,mask in [
        ("speed_mps",pd.Series(True,index=local.index)),("acceleration_mps2",pd.Series(True,index=local.index)),
        ("net_gap_m",reliable & local.net_gap_m.gt(0)),("closing_speed_mps",reliable),("ttc_s",local.ttc_valid),
        ("vehicle_length_m",pd.Series(True,index=local.index))]}
    metrics["low_speed_gap_m"]=_dist(local.loc[reliable & local.speed_mps.lt(5) & local.net_gap_m.gt(0),"net_gap_m"])
    exposure=edge_exposure(s);events,formal=extract_sumo_formal_p2_events(s,recorded_observation_step_s=.1)
    events.to_parquet(out/"engineering_p2.parquet",index=False)
    bins=[]
    for lo in range(0,600,60):
        ff=f[f.time_s.gt(lo)&f.time_s.le(lo+60)];ss=local[local.time_s.gt(lo)&local.time_s.le(lo+60)]
        bins.append(dict(start_s=lo,end_s=lo+60,density_veh_km_lane=float(ff.local_present.mean()/space["lane_km"]),
                         mean_speed_mps=float(ss.speed_mps.mean()) if len(ss) else None,
                         low_speed_fraction=float(ss.speed_mps.lt(5).mean()) if len(ss) else None,
                         pending_end=int(ff.external_pending.iloc[-1]),pending_max=int(ff.external_pending.max()),
                         inserted=int(ff.inserted_step.sum()),exited=int(ff.arrived_step.sum()),
                         mean_present=float(ff.global_present.mean()),local_vehicle_s=len(ss)*.1))
    # Explicit retained slices describe startup sensitivity, not an approved warmup.
    startup=[]
    for lo in [0,60,120,300]:
        ff=f[f.time_s.gt(lo)];ss=local[local.time_s.gt(lo)]
        startup.append(dict(start_s=lo,end_s=600,selection="predeclared descriptive startup sensitivity; not scientific warmup",
                            mean_speed_mps=float(ss.speed_mps.mean()) if len(ss) else None,
                            density_veh_km_lane=float(ff.local_present.mean()/space["lane_km"]),
                            low_speed_fraction=float(ss.speed_mps.lt(5).mean()) if len(ss) else None))
    differences=s.sort_values(["vehicle_id","time_s"]).groupby("vehicle_id").time_s.diff().dropna()
    cadence=float((differences-.1).abs().max()) if len(differences) else None
    statuses={str(k):int(v) for k,v in s.measurement_status.value_counts().items()}
    if cadence is None or cadence>1e-6 or s.duplicated(["incarnation_id","time_s"]).any():raise ValueError("recorded_identity_cadence")
    if statuses.get("missing",0) or statuses.get("invalid",0):raise ValueError("following_measurement_quality")
    small=s[["time_s","edge_id","lane_id","longitudinal_position_m","speed_mps"]].copy()
    # These are edge/lane-specific bins, never normal-edge cumulative coordinates.
    small["space_bin_m"]=(small.longitudinal_position_m//50)*50
    small["time_bin_s"]=(small.time_s//5)*5
    st=small.groupby(["edge_id","lane_id","space_bin_m","time_bin_s"]).speed_mps.agg(["mean","count",lambda v:float((v<5).mean())]).reset_index()
    st.columns=["edge_id","lane_id","space_bin_m","time_bin_s","mean_speed_mps","state_rows","low_share"]
    st.to_csv(out/"spacetime_edge_lane_5s_50m.csv",index=False)
    rate=len(events)/exposure["p2_evaluable_following_vehicle_hours"] if exposure["p2_evaluable_following_vehicle_hours"] else None
    return dict(local_metrics=metrics,local_density_veh_km_lane=float(f.local_present.mean()/space["lane_km"]),
                local_mean_speed_mps=metrics["speed_mps"]["mean"],local_low_speed_fraction=float(local.speed_mps.lt(5).mean()) if len(local) else None,
                local_vehicle_s_recorded=len(local)*.1,local_following_fraction=float(reliable.mean()) if len(local) else None,
                local_ttc_valid_fraction=float(local.ttc_valid.mean()) if len(local) else None,
                full_network_p2=dict(events=len(events),**exposure,event_rate_per_evaluable_vehicle_hour=rate,
                                     event_boundaries=events[[k for k in ["vehicle_id","leader_id","event_start_s","event_end_s","event_confirm_s","ttc_min_s","exit_reason"] if k in events]].to_dict("records"),
                                     formal_adapter_status=formal["equivalence_status"],status="Engineering Diagnostic Only"),
                local_formal_p2="Unresolved",time_bins=bins,startup_sensitivity=startup,
                global_measurement_status_counts=statuses,cadence_max_abs_error_s=cadence,
                full_P2_analysis_wall_s=time.monotonic()-start,initial_vehicles=0,
                warmup_s_approved=None,state_sha256=sha(out/"state.parquet"))
