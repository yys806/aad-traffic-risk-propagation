"""Read-only B1.2-N worker; no TraCI vehicle setters, no main-matrix/P2 path."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .stage_0_5_b12n_runtime import read,write,sha,load_plan
from .stage_0_5_near_zero_observability import Coverage,SOURCE_PROOF_KEYS,execution_scope
from .stage_0_5_b12_observation import ScopedAccounting,queue_snapshot,QueueTracker,QUEUE_CONFIG
from .stage_0_5_b12_network import coordinate_support
from .stage_0_5_sumo import _sumo_binary,_ensure_traci_importable


def definitions(path):
    root=ET.parse(path).getroot();types={v.attrib["id"]:dict(v.attrib) for v in root.findall("vType")}
    routes={r.attrib["id"]:r.attrib["edges"].split() for r in root.findall("route")}
    vehicles={}
    for v in root.findall("vehicle"):
        stops=[dict(s.attrib) for s in v.findall("stop")]
        route=routes[v.attrib["route"]]
        if len(set(route))!=len(route):raise ValueError("cyclic route outside verified context")
        ordinary=all(s.get("parking","false")=="false" and not any(k in s for k in ["triggered","containerTriggered","busStop","parkingArea","chargingStation","speed","onDemand","join","split"]) for s in stops)
        if not ordinary:raise ValueError("nonordinary stop outside proof")
        vehicles[v.attrib["id"]]=dict(type=v.attrib["type"],depart=float(v.attrib["depart"]),assigned_lane=v.attrib["departLane"],
             route_edges=route,input_stops=stops,ordinary_stops=ordinary)
    if root.findall("flow") or root.findall("person") or root.findall("container") or root.findall("trip"):raise ValueError("unexpected dynamic demand")
    return types,vehicles


def settings(conn,spec,types,out):
    options={k:conn.simulation.getOption(k) for k in ["step-method.ballistic","step-length","seed","threads","time-to-teleport","random"]}
    checks=[options["step-method.ballistic"].lower() in ["true","1"],abs(float(options["step-length"])-.05)<1e-10,
            int(options["seed"])==20261019,int(options["threads"])==1,options["time-to-teleport"]=="-1",options["random"].lower() in ["false","0"],
            abs(conn.simulation.getDeltaT()-.05)<1e-10,conn.simulation.getTime()==0.,len(conn.vehicle.getIDList())==0]
    conn.simulation.saveState(str(out/"runtime_initial_state.xml"))
    echo={t.attrib["id"]:dict(t.attrib) for t in ET.parse(out/"runtime_initial_state.xml").getroot().iter("vType")}
    actual={}
    methods=dict(tau="getTau",minGap="getMinGap",actionStepLength="getActionStepLength",maxSpeed="getMaxSpeed",length="getLength",vClass="getVehicleClass",
                 sigma="getImperfection",accel="getAccel",decel="getDecel",apparentDecel="getApparentDecel",emergencyDecel="getEmergencyDecel",speedFactor="getSpeedFactor",speedDev="getSpeedDeviation")
    for tid,expected in types.items():
        actual[tid]={k:getattr(conn.vehicletype,m)(tid) for k,m in methods.items()}
        for k,v in actual[tid].items():checks.append(v==expected[k] if isinstance(v,str) else abs(v-float(expected[k]))<1e-10)
        for k in ["carFollowModel","laneChangeModel"]:checks.append(echo[tid].get(k)==expected[k])
        checks.append(abs(float(echo[tid].get("sigmaStep","nan"))-1.)<1e-10)
    version=conn.getVersion();checks.append("1.26.0" in version[1])
    tls=[]
    if spec["kind"]=="C":
        logic=next(l for l in conn.trafficlight.getAllProgramLogics("hwy_j2") if l.programID=="b12_supply_v1")
        tls=[dict(duration=p.duration,state=p.state) for p in logic.phases];checks.append([p["duration"] for p in tls]==[5.,6.2,48.8])
    if spec["kind"]=="N2":checks.append(all(s=="r" for s in conn.trafficlight.getRedYellowGreenState("n1")))
    return dict(verified=bool(all(checks)),checks=len(checks),options=options,types=actual,type_echo=echo,sumo_version=version,tls=tls,
                started_empty_fresh=True,vehicle_control=False,state_load=False,P2_calculated=False)


def run_worker(batch,run_id,name):
    import pyarrow as pa
    import pyarrow.parquet as pq
    plan=load_plan(batch,name);spec=next(r for r in plan["runs"] if r["run_id"]==run_id)
    out=batch/"runs"/run_id;out.mkdir(exist_ok=True)
    if (out/"summary.json").exists():raise PermissionError("no run overwrite")
    _ensure_traci_importable();import traci;import traci.constants as c
    types,vehicle_defs=definitions(batch/spec["demand"])
    cfg=ET.parse(batch/spec["config"]).getroot()
    if cfg.find("input/load-state") is not None or cfg.find("input/additional-files") is not None:raise PermissionError("unverified state/device input")
    net=ET.parse(batch/spec["network"]).getroot()
    lane_edges={l.attrib["id"]:e.attrib["id"] for e in net.findall("edge") for l in e.findall("lane")}
    lane_lengths={l.attrib["id"]:float(l.attrib["length"]) for e in net.findall("edge") for l in e.findall("lane")}
    support=coordinate_support(batch/spec["network"]) if spec["kind"] in ["C","D"] else None
    scenario_network_issue=bool(support and not support["coordinate_verified"])
    coverage=Coverage();accounting=ScopedAccounting(spec["local_space"]);tracker=QueueTracker(QUEUE_CONFIG)
    previous={};raw=[];frames=[];snapshots=[];events=[];departures=[];exits=[];device_proofs={};first_lanes={}
    row_count=0;writer=None;failure=None;conn=None;runtime={};global_blockers=[];scenario_blockers=[]
    gap_count=0;gap_max=None;mapping=Counter();mapping_max=None;edge_count=0;junction_count=0;lanes_seen=set();collision=set();teleport=set()
    start=time.monotonic();last_complete_s=0.;due_times=np.array(sorted(v["depart"] for v in vehicle_defs.values()))
    proof={k:True for k in SOURCE_PROOF_KEYS};proof["official_source_contract_verified"]=read(batch/"near_zero_source_contract.json")["source_audit_verified"]
    def flush():
        nonlocal raw,writer,row_count
        if not raw:return
        df=pd.DataFrame(raw)
        for key in ["net_gap_m","leader_speed_mps"]:df[key]=pd.to_numeric(df[key],errors="raise").astype(float)
        table=pa.Table.from_pandas(df,preserve_index=False)
        if writer is None:writer=pq.ParquetWriter(out/"internal_states.parquet",table.schema,compression="zstd")
        writer.write_table(table.cast(writer.schema));row_count+=len(raw);raw=[]
    command=[_sumo_binary(),"-c",str(batch/spec["config"]),"--no-step-log","true","--duration-log.disable","true","--error-log",str(out/"sumo_errors.log")]
    write(out/"run_config.json",dict(run=spec,plan_sha256=sha(batch/name),command=command,contract_version=plan["contract_version"],no_vehicle_control=True,P2_calculated=False))
    try:
        if scenario_network_issue:raise ValueError("scenario_network_invalid")
        traci.start(command,label=run_id);conn=traci.getConnection(run_id)
        runtime=settings(conn,spec,types,out);write(out/"runtime_settings.json",runtime)
        if not runtime["verified"]:raise ValueError("runtime_configuration_mismatch")
        conn.simulation.subscribe((c.VAR_TIME,c.VAR_DEPARTED_VEHICLES_IDS,c.VAR_ARRIVED_VEHICLES_IDS,c.VAR_COLLIDING_VEHICLES_IDS,c.VAR_TELEPORT_STARTING_VEHICLES_IDS,c.VAR_PENDING_VEHICLES))
        vv=(c.VAR_SPEED,c.VAR_ACCELERATION,c.VAR_POSITION,c.VAR_LANE_ID,c.VAR_LANEPOSITION,c.VAR_ROAD_ID,c.VAR_LEADER,c.VAR_LASTACTIONTIME,c.VAR_LENGTH,c.VAR_TYPE,c.VAR_DISTANCE,c.VAR_ROUTE_INDEX,c.VAR_STOPSTATE)
        for tick in range(1,round(spec["duration_s"]/.05)+1):
            conn.simulationStep();sv=conn.simulation.getSubscriptionResults();now=float(sv[c.VAR_TIME])
            if abs(now-tick*.05)>1e-8:raise ValueError("runtime_clock")
            new=sv[c.VAR_DEPARTED_VEHICLES_IDS];gone=sv[c.VAR_ARRIVED_VEHICLES_IDS]
            collision.update(sv[c.VAR_COLLIDING_VEHICLES_IDS]);teleport.update(sv[c.VAR_TELEPORT_STARTING_VEHICLES_IDS])
            if collision or teleport:raise ValueError("collision_or_teleport")
            for vid in new:
                if vid not in vehicle_defs:raise ValueError("unplanned_vehicle_identity")
                dev={d:conn.vehicle.getParameter(vid,"has."+d+".device") for d in ["elecHybrid","driverstate","rerouting","taxi","bluelight","toc"]}
                if any(v!="false" for v in dev.values()):raise ValueError("special_device_outside_verified_domain")
                if list(conn.vehicle.getRoute(vid))!=vehicle_defs[vid]["route_edges"]:raise ValueError("route_input_mismatch")
                device_proofs[vid]=dev
                conn.vehicle.subscribe(vid,vv,parameters={c.VAR_LEADER:("d",1000.)})
                departures.append(dict(vehicle_id=vid,scheduled_s=vehicle_defs[vid]["depart"],entered_s=now,assigned_lane=vehicle_defs[vid]["assigned_lane"]))
            for vid in gone:exits.append(dict(vehicle_id=vid,time_s=now,last_edge=previous.get(vid,{}).get("edge_id"),last_lane=previous.get(vid,{}).get("lane_id")))
            data=conn.vehicle.getAllSubscriptionResults();current={}
            for vid,v in sorted(data.items()):
                definition=vehicle_defs[vid];tid=v[c.VAR_TYPE]
                if tid!=definition["type"] or abs(v[c.VAR_LENGTH]-float(types[tid]["length"]))>1e-10:raise ValueError("vehicle_type_or_length_mismatch")
                stops=[dict(lane=s.lane,edge=lane_edges.get(s.lane),end_pos_m=s.endPos,duration_s=s.duration,
                            stop_flags=s.stopFlags,ordinary=definition["ordinary_stops"] and s.stopFlags==0 and s.speed==0) for s in conn.vehicle.getStops(vid,0)]
                if not definition["input_stops"] and stops:raise ValueError("unplanned_stop_context")
                r=dict(run_id=run_id,vehicle_id=vid,incarnation_id=run_id+"|"+vid,time_s=now,edge_id=v[c.VAR_ROAD_ID],lane_id=v[c.VAR_LANE_ID],
                       position_m=v[c.VAR_LANEPOSITION],speed_mps=v[c.VAR_SPEED],acceleration_mps2=v[c.VAR_ACCELERATION],last_action_time_s=v[c.VAR_LASTACTIONTIME],
                       length_m=v[c.VAR_LENGTH],traveled_distance_m=v[c.VAR_DISTANCE],x_m=v[c.VAR_POSITION][0],y_m=v[c.VAR_POSITION][1],
                       traci_vehicle_control=False,numerical_config_verified=True,remaining_stops=stops,input_has_stops=bool(definition["input_stops"]),
                       route_edges=definition["route_edges"],route_index=v[c.VAR_ROUTE_INDEX],public_stop_state=v[c.VAR_STOPSTATE])
                if r["lane_id"] not in lane_edges or lane_edges[r["lane_id"]]!=r["edge_id"] or not -.000001<=r["position_m"]<=lane_lengths[r["lane_id"]]+.000001:raise ValueError("invalid_network_coordinate_support")
                current[vid]=r;first_lanes.setdefault(vid,r["lane_id"]);lanes_seen.add(r["lane_id"]);junction_count+=r["edge_id"].startswith(":")
                previous_row=previous.get(vid)
                if previous_row:
                    result=coverage.add(previous_row,r,proof)
                    if result["blocker"]:raise ValueError(result["blocker"])
                    if previous_row["edge_id"]==r["edge_id"] and previous_row["lane_id"]!=r["lane_id"]:
                        events.append(dict(vehicle_id=vid,incarnation_id=r["incarnation_id"],before_s=previous_row["time_s"],after_s=now,
                             edge=r["edge_id"],from_lane=previous_row["lane_id"],to_lane=r["lane_id"],before_speed_mps=previous_row["speed_mps"],after_speed_mps=r["speed_mps"],
                             assigned_departure_lane=definition["assigned_lane"],numerical_classification=result["classification"],controlled=False))
                    if previous_row["edge_id"]!=r["edge_id"]:edge_count+=1
                    if support:
                        old=support["lanes"].get(previous_row["lane_id"]);newmap=support["lanes"].get(r["lane_id"])
                        if old and newmap and old["path"]==newmap["path"]:
                            dx=newmap["offset_m"]+r["position_m"]-old["offset_m"]-previous_row["position_m"]
                            dd=r["traveled_distance_m"]-previous_row["traveled_distance_m"];error=abs(dx-dd)
                            mapping["cross_edge" if previous_row["edge_id"]!=r["edge_id"] else "same_edge"]+=1
                            mapping_max=max(mapping_max or 0.,error)
                            if error>1e-6:raise ValueError("shared_coordinate_distance_mismatch")
                lead=v[c.VAR_LEADER];lid=lead[0] if lead and lead[0] else None;lv=data.get(lid);gap=None
                if lid:gap=lead[1]+float(types[tid]["minGap"])
                if lv and lv[c.VAR_LANE_ID]==r["lane_id"]:
                    physical=lv[c.VAR_LANEPOSITION]-lv[c.VAR_LENGTH]-r["position_m"];err=abs(gap-physical)
                    gap_count+=1;gap_max=max(gap_max or 0.,err)
                    if err>1e-6:raise ValueError("shared_physical_gap_mismatch")
                stored={k:val for k,val in r.items() if k not in ["remaining_stops","route_edges"]}
                stored.update(remaining_stops_json=json.dumps(stops),route_edges_json=json.dumps(r["route_edges"]),leader_id=lid or "",net_gap_m=gap,
                              leader_speed_mps=lv[c.VAR_SPEED] if lv else None)
                raw.append(stored)
            due=int(np.searchsorted(due_times,now-1e-8,side="right"));f=accounting.update(current,new,gone,due,now)
            pending=set(sv[c.VAR_PENDING_VEHICLES])
            if len(pending)!=f["external_pending"]:raise ValueError("pending_demand_accounting")
            local=[r for r in current.values() if r["edge_id"]==spec["local_space"]["edge"] and spec["local_space"]["start_m"]<=r["position_m"]<spec["local_space"]["end_m"]]
            f.update(local_low_vehicles=sum(r["speed_mps"]<5 for r in local),onroad_low_vehicles=sum(r["speed_mps"]<5 for r in current.values()),
                     onroad_stopped_vehicles=sum(r["speed_mps"]<.1 for r in current.values()),local_speed_sum=sum(r["speed_mps"] for r in local),
                     inserted_step=len(new),exited_step=len(gone))
            frames.append(f)
            if support and tick%20==0:
                blocked={}
                for lane in {vehicle_defs[v]["assigned_lane"] for v in pending}:
                    rear=min([r["position_m"]-r["length_m"] for r in current.values() if r["lane_id"]=="main_0_"+lane] or [float("inf")])
                    needed=max(float(types[vehicle_defs[v]["type"]]["length"])+float(types[vehicle_defs[v]["type"]]["minGap"]) for v in pending if vehicle_defs[v]["assigned_lane"]==lane)
                    blocked[lane]=dict(nearest_rear_m=rear if np.isfinite(rear) else None,required_front_space_m=needed,blocked=rear<needed)
                q=queue_snapshot(list(current.values()),now,support,QUEUE_CONFIG,pending=len(pending),
                                 physical_entry_space=bool(blocked) and all(x["blocked"] for x in blocked.values()),downstream_context=True)
                qual=tracker.update(q);snapshots.append(dict(q,qualification=qual,entry_space_by_pending_lane=blocked))
            previous=current;last_complete_s=now
            if tick%100==0:flush()
            if time.monotonic()-start>plan["limits"]["per_run_wall_s"]-5:raise TimeoutError("worker_wall_limit")
    except Exception as exc:
        failure=f"{type(exc).__name__}: {exc}"
        (scenario_blockers if execution_scope(str(exc))=="Scenario-Specific Blocker" else global_blockers).append(str(exc))
    finally:
        if conn is not None:
            try:conn.close()
            except Exception:pass
        flush()
        if writer is not None:writer.close()
    pd.DataFrame(frames).to_csv(out/"traffic_frames.csv",index=False)
    write(out/"queue_snapshots.json",snapshots);write(out/"departures.json",departures);write(out/"exits.json",exits);write(out/"lane_changes.json",events)
    write(out/"numerical_branch_coverage.json",coverage.summary())
    write(out/"runtime_device_proof.json",device_proofs)
    if spec["kind"]=="D" and not global_blockers:
        if not events:scenario_blockers.append("D_no_required_lane_change")
        if len(accounting.arrived)!=len(vehicle_defs):scenario_blockers.append("D_no_downstream_exit")
    unknown=coverage.counts["Near-Zero Context Unresolved"]
    ei=[]
    if unknown:ei.append("near_zero_context_unresolved")
    qualified=[x["qualification"] for x in snapshots]
    if snapshots and not any(q["entry_spillback_supported"] for q in qualified):ei.append("entry_spillback_insufficient")
    blockers=global_blockers+scenario_blockers
    warnings=["descriptive_low_speed_or_pending"] if any(f["onroad_low_vehicles"] or f["external_pending"] for f in frames) else []
    status="completed_with_engineering_blocker" if blockers else "completed_with_diagnostic_warning" if warnings or ei else "completed_valid"
    summary=dict(run_id=run_id,kind=spec["kind"],status=status,engineering_blockers=blockers,global_blockers=global_blockers,scenario_blockers=scenario_blockers,
          diagnostic_warnings=warnings,evidence_insufficient=ei,failure=failure,plan_sha256=sha(batch/name),observed_s=last_complete_s,planned_s=spec["duration_s"],
          numerical=coverage.summary(),planned_vehicles=len(vehicle_defs),actual_inserted=len(accounting.departed),actual_exited=len(accounting.arrived),present=len(previous),
          pending_end=frames[-1]["external_pending"] if frames else None,max_pending=max([f["external_pending"] for f in frames] or [0]),
          local_entered=accounting.local_in,local_exited=accounting.local_out,local_vehicle_s=accounting.local_vehicle_s,local_space=spec["local_space"],
          first_times=dict(internal_low=next((f["time_s"] for f in frames if f["onroad_low_vehicles"]>0),None),
               external_pending=next((f["time_s"] for f in frames if f["external_pending"]>0),None),
               internal_queue=next((q["time_s"] for q in qualified if q["onroad_queue_observed"]),None),
               upstream_extension=next((q["time_s"] for q in qualified if q["upstream_extension_observed"]),None),
               inlet_adjacent=next((q["time_s"] for q in qualified if q["inlet_adjacent_queue_observed"]),None),
               entry_spillback_supported=next((q["time_s"] for q in qualified if q["entry_spillback_supported"]),None)),
          queue_state_counts=dict(Counter(q["state"] for q in qualified)),queue_temporal_resets=qualified[-1]["temporal_breaks"] if qualified else None,
          queue_conservative_edge_or_lane_member_resets=qualified[-1]["lane_change_member_resets"] if qualified else None,
          lane_changes=len(events),lane_change_vehicle_ids=sorted({e["vehicle_id"] for e in events}),first_lanes=first_lanes,
          exit_last_edges=dict(Counter(x["last_edge"] for x in exits)),edge_transitions=edge_count,junction_states=junction_count,lanes_seen=sorted(lanes_seen),
          mapping_checks=dict(mapping),max_mapping_residual_m=mapping_max,physical_gap_checks=gap_count,max_gap_residual_m=gap_max,
          runtime_settings=runtime,runtime=dict(total_worker_wall_s=time.monotonic()-start,internal_state_rows=row_count),
          P2_calculated=False,main_matrix_allowed=False,scientific_claim_eligible=False)
    write(out/"summary.json",summary)
    print("B12N_WORKER "+run_id+" "+status+" "+str(failure),flush=True)
