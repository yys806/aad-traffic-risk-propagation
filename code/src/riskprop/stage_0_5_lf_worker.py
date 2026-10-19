"""LF fixed local .05s worker; identical read-only state semantics, timed transport."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .stage_0_5_lf_runtime import read,write,sha,load_plan
from .stage_0_5_lf_transport import VehicleReader
from .stage_0_5_b12n_worker import definitions,settings as base_settings
from .stage_0_5_cd_observation import QueueContinuity,entry_evidence,journey_audit,movement
from .stage_0_5_positive_worker import DEVICES
from .stage_0_5_near_zero_observability import Coverage,SOURCE_PROOF_KEYS,execution_scope
from .stage_0_5_b12_observation import ScopedAccounting,queue_snapshot,QUEUE_CONFIG
from .stage_0_5_b12_network import coordinate_support
from .stage_0_5_sumo import _sumo_binary,_ensure_traci_importable


def settings(conn,spec,types,out):
    # Reuse type/config checks without historical compressed-C TLS assumption.
    runtime=base_settings(conn,dict(spec,kind='CD'),types,out)
    runtime['mesosim']=conn.simulation.getOption('mesosim');runtime['num_clients']=conn.simulation.getOption('num-clients')
    tls={tid:[dict(duration=p.duration,state=p.state) for p in next(l for l in conn.trafficlight.getAllProgramLogics(tid) if l.programID==conn.trafficlight.getProgram(tid)).phases] for tid in conn.trafficlight.getIDList()}
    runtime['tls']=tls
    actual=[list(p['duration'] for p in phases) for phases in tls.values()]
    runtime['verified'] &= actual==spec['expected_tls_durations'] and runtime['mesosim'].lower() in ['false','0'] and int(runtime['num_clients'])==1
    return runtime


def run_worker(batch,run_id):
    import pyarrow as pa
    import pyarrow.parquet as pq
    plan=load_plan(batch);name='experiment_plan.json';spec=next(r for r in plan["runs"] if r["run_id"]==run_id)
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
    if any(v['input_stops'] for v in vehicle_defs.values()):raise PermissionError('fresh no-stop domain only')
    coverage=Coverage();accounting=ScopedAccounting(spec["local_space"]);tracker=QueueContinuity()
    previous={};raw=[];frames=[];snapshots=[];events=[];departures=[];exits=[];device_proofs={};first_lanes={}
    row_count=0;writer=None;failure=None;conn=None;runtime={};reader=None;global_blockers=[];scenario_blockers=[]
    gap_count=0;gap_max=None;mapping=Counter();mapping_max=None;edge_count=0;junction_count=0;lanes_seen=set();collision=set();teleport=set()
    start=time.monotonic();last_complete_s=0.;due_times=np.array(sorted(v["depart"] for v in vehicle_defs.values()))
    source_verified=read(batch/'source_audit.json')['source_verified'];proof={}
    first_times={k:None for k in ['internal_low','external_pending','internal_queue','upstream_extension','inlet_adjacent','entry_spillback_supported']}
    queue_counts=Counter();queue_max_duration=0.;queue_max_coupled=0.;queue_all_paths_frames=0;queue_qualified_frames=0
    cohort={};route_checks=0;queue_wall_s=0.;min_gap=None;local_moments=Counter();speed_values=[];accel_values=[];bins={}
    def flush():
        nonlocal raw,writer,row_count
        if not raw:return
        df=pd.DataFrame(raw)
        for key in ["net_gap_m","leader_speed_mps","leader_position_m","leader_length_m","raw_traci_leader_distance_m"]:df[key]=pd.to_numeric(df[key],errors="raise").astype(float)
        table=pa.Table.from_pandas(df,preserve_index=False)
        if writer is None:writer=pq.ParquetWriter(out/"internal_states.parquet",table.schema,compression="zstd")
        writer.write_table(table.cast(writer.schema));row_count+=len(raw);raw=[]
    command=[_sumo_binary(),"-c",str(batch/spec["config"]),"--no-step-log","true","--duration-log.disable","true","--error-log",str(out/"sumo_errors.log")]
    write(out/"run_config.json",dict(run=spec,plan_sha256=sha(batch/name),command=command,contract_version=plan["contract_version"],no_vehicle_control=True,P2_calculated=False))
    try:
        if scenario_network_issue:raise ValueError("scenario_network_invalid")
        traci.start(command,label=run_id);conn=traci.getConnection(run_id)
        runtime=settings(conn,spec,types,out);reader=VehicleReader(conn,spec["reader_mode"]);write(out/"runtime_settings.json",runtime)
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
                dev={d:conn.vehicle.getParameter(vid,"has."+d+".device") for d in DEVICES}
                if any(v!="false" for v in dev.values()):raise ValueError("special_device_outside_verified_domain")
                if list(conn.vehicle.getRoute(vid))!=vehicle_defs[vid]["route_edges"]:raise ValueError("route_input_mismatch")
                device_proofs[vid]=dev
                conn.vehicle.subscribe(vid,vv,parameters={c.VAR_LEADER:("d",1000.)})
                departures.append(dict(vehicle_id=vid,scheduled_s=vehicle_defs[vid]["depart"],entered_s=now,assigned_lane=vehicle_defs[vid]["assigned_lane"]))
            for vid in gone:exits.append(dict(vehicle_id=vid,time_s=now,last_edge=previous.get(vid,{}).get("edge_id"),last_lane=previous.get(vid,{}).get("lane_id")))
            data=conn.vehicle.getAllSubscriptionResults();current={}
            extras=reader.collect(sorted(data))
            for vid,v in sorted(data.items()):
                definition=vehicle_defs[vid];tid=v[c.VAR_TYPE]
                if tid!=definition["type"] or abs(v[c.VAR_LENGTH]-float(types[tid]["length"]))>1e-10:raise ValueError("vehicle_type_or_length_mismatch")
                dev=extras[vid]['devices']
                if any(x!='false' for x in dev.values()):raise ValueError('special_device_outside_verified_domain')
                route=extras[vid]['route'];route_checks+=1
                if route!=definition['route_edges']:raise ValueError('route_input_mismatch')
                stops=[dict(lane=s.lane,edge=lane_edges.get(s.lane),end_pos_m=s.endPos,duration_s=s.duration,
                            stop_flags=s.stopFlags,ordinary=definition["ordinary_stops"] and s.stopFlags==0 and s.speed==0) for s in extras[vid]['stops']]
                if not definition["input_stops"] and stops:raise ValueError("unplanned_stop_context")
                proof=dict(official_source_contract_verified=source_verified,fresh_vehicle_lifecycle=runtime['started_empty_fresh'] and vid in accounting.departed.union(new),
                    no_state_restore=runtime['state_load'] is False,no_dynamic_stop_mutation=not stops and not definition['input_stops'],
                    no_route_mutation=route==definition['route_edges'],no_collision_or_teleport=not collision and not teleport,
                    no_special_devices=all(x=='false' for x in dev.values()),noncyclic_route_verified=len(route)==len(set(route)),
                    ordinary_stop_definition_verified=not definition['input_stops'])
                if set(proof)!=set(SOURCE_PROOF_KEYS) or any(x is not True for x in proof.values()):raise ValueError('lifecycle_proof_not_verified')
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
                    if result['classification']=='Near-Zero Context Unresolved':raise ValueError('unresolved_context_in_fresh_no_stop_domain')
                    if movement(previous_row,r)=='lane_change':
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
                if gap is not None:min_gap=min(min_gap if min_gap is not None else gap,gap)
                stored={k:val for k,val in r.items() if k not in ["remaining_stops","route_edges"]}
                stored.update(remaining_stops_json=json.dumps(stops),route_edges_json=json.dumps(r["route_edges"]),leader_id=lid or "",net_gap_m=gap,
                              leader_speed_mps=lv[c.VAR_SPEED] if lv else None,
                              devices_json=json.dumps(dev,sort_keys=True),leader_lane_id=lv[c.VAR_LANE_ID] if lv else '',
                              leader_edge_id=lv[c.VAR_ROAD_ID] if lv else '',leader_position_m=lv[c.VAR_LANEPOSITION] if lv else None,
                              leader_length_m=lv[c.VAR_LENGTH] if lv else None,raw_traci_leader_distance_m=lead[1] if lid else None)
                raw.append(stored)
            due=int(np.searchsorted(due_times,now-1e-8,side="right"));f=accounting.update(current,new,gone,due,now)
            pending=set(sv[c.VAR_PENDING_VEHICLES])
            expected_pending={v for v,d in vehicle_defs.items() if d['depart']<now-1e-8 and v not in accounting.departed}
            if pending!=expected_pending or len(pending)!=f["external_pending"]:raise ValueError("pending_demand_accounting")
            local=[r for r in current.values() if r["edge_id"]==spec["local_space"]["edge"] and spec["local_space"]["start_m"]<=r["position_m"]<spec["local_space"]["end_m"]]
            f.update(local_low_vehicles=sum(r["speed_mps"]<5 for r in local),onroad_low_vehicles=sum(r["speed_mps"]<5 for r in current.values()),
                     onroad_stopped_vehicles=sum(r["speed_mps"]<.1 for r in current.values()),local_speed_sum=sum(r["speed_mps"] for r in local),
                     inserted_step=len(new),exited_step=len(gone))
            frames.append(f)
            for key,present in [('internal_low',f['onroad_low_vehicles']>0),('external_pending',bool(pending))]:
                if present and first_times[key] is None:first_times[key]=now
            local_moments['n']+=len(local);local_moments['speed']+=sum(r['speed_mps'] for r in local);local_moments['low']+=sum(r['speed_mps']<5 for r in local)
            speed_values.extend(r['speed_mps'] for r in local);accel_values.extend(r['acceleration_mps2'] for r in local)
            b=bins.setdefault(str(int((now-1e-8)//60)),dict(frames=0,n=0,speed=0.,low=0,inserted=0,exited=0))
            b['frames']+=1;b['n']+=len(local);b['speed']+=f['local_speed_sum'];b['low']+=f['local_low_vehicles'];b['inserted']+=len(new);b['exited']+=len(gone)
            if support:
                qstart=time.monotonic();blocked=entry_evidence(list(current.values()),pending,vehicle_defs,types)
                q=queue_snapshot(list(current.values()),now,support,QUEUE_CONFIG,pending=len(pending),
                                 physical_entry_space=bool(blocked) and all(x["blocked"] for x in blocked.values()),downstream_context=True)
                q['entry_by_path']=blocked;qual=tracker.update(q);queue_wall_s+=time.monotonic()-qstart
                queue_counts[qual['state']]+=1;queue_all_paths_frames+=q['all_paths_queued'];queue_qualified_frames+=bool(qual['entry_spillback_supported'])
                queue_max_duration=max(queue_max_duration,qual['longest_component_duration_s']);queue_max_coupled=max(queue_max_coupled,qual['continuous_coupled_entry_duration_s'])
                for key,field in [('internal_queue','onroad_queue_observed'),('upstream_extension','upstream_extension_observed'),('inlet_adjacent','inlet_adjacent_queue_observed'),('entry_spillback_supported','entry_spillback_supported')]:
                    if qual[field] and first_times[key] is None:first_times[key]=now
                if tick%20==0:snapshots.append(dict(q,qualification=qual,entry_space_by_pending_lane=blocked))
                with (out/'queue_frames.jsonl').open('a',encoding='utf-8') as qfile:
                    qfile.write(json.dumps(dict(time_s=now,qualification=qual,components=q['components'],entry_by_path=blocked),allow_nan=False)+'\n')
            previous=current;last_complete_s=now
            if tick%100==0:flush()
            wall_limit=plan['micro_per_run_wall_s'] if spec['tier']=='micro' else plan['limits']['per_run_wall_s']
            if time.monotonic()-start>wall_limit-5:raise TimeoutError("worker_wall_limit")
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
    journey=journey_audit(vehicle_defs,first_lanes,events,exits,require_all=spec['tier']=='micro') if spec['kind']=='D' else None
    if spec["kind"]=="D" and not global_blockers:
        if not journey['verified']:scenario_blockers.append('D_required_journey_unverified')
    unknown=coverage.counts["Near-Zero Context Unresolved"]
    ei=[]
    if unknown:ei.append("near_zero_context_unresolved")
    qualified=[x["qualification"] for x in snapshots]
    if spec['kind']=='C' and first_times['entry_spillback_supported'] is None:ei.append('entry_spillback_insufficient')
    blockers=global_blockers+scenario_blockers
    warnings=["descriptive_low_speed_or_pending"] if any(f["onroad_low_vehicles"] or f["external_pending"] for f in frames) else []
    status="completed_with_engineering_blocker" if blockers else "completed_with_diagnostic_warning" if warnings or ei else "completed_valid"
    summary=dict(run_id=run_id,kind=spec["kind"],status=status,engineering_blockers=blockers,global_blockers=global_blockers,scenario_blockers=scenario_blockers,
          diagnostic_warnings=warnings,evidence_insufficient=ei,failure=failure,plan_sha256=sha(batch/name),observed_s=last_complete_s,planned_s=spec["duration_s"],
          numerical=coverage.summary(),planned_vehicles=len(vehicle_defs),actual_inserted=len(accounting.departed),actual_exited=len(accounting.arrived),present=len(previous),
          pending_end=frames[-1]["external_pending"] if frames else None,max_pending=max([f["external_pending"] for f in frames] or [0]),
          local_entered=accounting.local_in,local_exited=accounting.local_out,local_vehicle_s=accounting.local_vehicle_s,local_space=spec["local_space"],
          first_times=first_times,queue_state_counts=dict(queue_counts),queue_temporal_resets=tracker.breaks,
          queue_real_path_member_resets=tracker.lane_resets,queue_frames_processed=tracker.frames,queue_max_component_duration_s=queue_max_duration,
          queue_max_coupled_entry_duration_s=queue_max_coupled,queue_all_paths_frames=queue_all_paths_frames,queue_supported_frames=queue_qualified_frames,
          journey=journey,route_observation_checks=route_checks,
          lane_changes=len(events),lane_change_vehicle_ids=sorted({e["vehicle_id"] for e in events}),first_lanes=first_lanes,
          exit_last_edges=dict(Counter(x["last_edge"] for x in exits)),edge_transitions=edge_count,junction_states=junction_count,lanes_seen=sorted(lanes_seen),
          mapping_checks=dict(mapping),max_mapping_residual_m=mapping_max,physical_gap_checks=gap_count,max_gap_residual_m=gap_max,
          traffic=dict(local_mean_speed_mps=local_moments['speed']/local_moments['n'] if local_moments['n'] else None,
              local_density_veh_km_lane=sum(f['local_density_veh_km_lane'] for f in frames)/len(frames) if frames else None,
              low_share=local_moments['low']/local_moments['n'] if local_moments['n'] else None,
              speed_quantiles_mps=[float(x) for x in np.quantile(speed_values,[0,.1,.5,.9,1])] if speed_values else None,
              acceleration_quantiles_mps2=[float(x) for x in np.quantile(accel_values,[0,.1,.5,.9,1])] if accel_values else None,
              min_onroad_leader_gap_m=min_gap,time_bins=bins,initialization='Empty startup included; no scientific warmup fixed'),
          runtime_settings=runtime,transport=reader.summary() if reader else None,runtime=dict(total_worker_wall_s=time.monotonic()-start,queue_compute_wall_s=queue_wall_s,internal_state_rows=row_count),
          P2_calculated=False,main_matrix_allowed=False,scientific_claim_eligible=False)
    write(out/"summary.json",summary)
    print("LF_WORKER "+run_id+" "+status+" "+str(failure),flush=True)
