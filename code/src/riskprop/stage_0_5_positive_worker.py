"""B1.2-P read-only native signal probes; no vehicle or signal control setters."""
from collections import Counter
import csv
import json
import time
import xml.etree.ElementTree as ET

from .stage_0_5_positive_runtime import read,write,sha,load_plan
from .stage_0_5_positive_near_zero import classify_edge
from .stage_0_5_near_zero_observability import SOURCE_PROOF_KEYS
from .stage_0_5_b12n_worker import settings,definitions
from .stage_0_5_sumo import _sumo_binary,_ensure_traci_importable

DEVICES=('elecHybrid','driverstate','rerouting','taxi','bluelight','toc','glosa','friction','stationfinder')

def run_worker(batch,run_id):
    plan=load_plan(batch);spec=next(r for r in plan['runs'] if r['run_id']==run_id)
    out=batch/'runs'/run_id;out.mkdir(exist_ok=True)
    if (out/'summary.json').exists():raise PermissionError('no run overwrite')
    types,defs=definitions(batch/spec['demand']);cfg=ET.parse(batch/spec['config']).getroot()
    if cfg.find('input/load-state') is not None or cfg.find('input/additional-files') is not None:raise PermissionError('unexpected controller or state input')
    if len(defs)!=1 or any(v['input_stops'] or len(v['route_edges'])!=len(set(v['route_edges'])) for v in defs.values()):raise PermissionError('probe lifecycle outside proof')
    net=ET.parse(batch/spec['network']).getroot();lanes={l.attrib['id']:(e.attrib['id'],float(l.attrib['length'])) for e in net.findall('edge') for l in e.findall('lane')}
    _ensure_traci_importable();import traci;import traci.constants as c
    command=[_sumo_binary(),'-c',str(batch/spec['config']),'--no-step-log','true','--duration-log.disable','true','--error-log',str(out/'sumo_errors.log')]
    write(out/'run_config.json',dict(run=spec,plan_sha256=sha(batch/'experiment_plan.json'),command=command,source_audit_sha256=sha(batch/'source_audit.json'),vehicle_setters=False,signal_setters=False))
    conn=None;previous={};states=[];targets=[];controls=[];contexts=[];departed=set();arrived=set();blockers=[];runtime={};failure=None;last_complete=0.
    counts=Counter();numerical=Counter();reason_counts=Counter();residuals=[];positive_values=[];device_proofs={};conservation=[];begin=time.monotonic()
    with (out/'edge_audit.jsonl').open('w',encoding='utf-8') as audits:
        try:
            traci.start(command,label=run_id);conn=traci.getConnection(run_id)
            runtime=settings(conn,spec,types,out)
            runtime['mesosim']=conn.simulation.getOption('mesosim');runtime['num_clients']=conn.simulation.getOption('num-clients')
            runtime['verified'] &= runtime['mesosim'].lower() in ['false','0'] and int(runtime['num_clients'])==1
            programs=conn.trafficlight.getAllProgramLogics('b')
            runtime['trafficlight_programs']=[dict(program=p.programID,phases=[dict(duration=x.duration,state=x.state) for x in p.phases]) for p in programs]
            runtime['verified'] &= any(p.programID=='b12p_all_red' and len(p.phases)==1 and set(p.phases[0].state)=={'r'} for p in programs)
            # The saved vType echo is produced by the running binary; it does
            # not load or restore any state. JM is a probe input, never inferred.
            runtime['jmStoplineGap_echo']=runtime['type_echo']['probe'].get('jmStoplineGap')
            runtime['verified'] &= runtime['jmStoplineGap_echo'] is not None and float(runtime['jmStoplineGap_echo'])==1.
            write(out/'runtime_settings.json',runtime)
            if not runtime['verified']:raise ValueError('runtime_configuration_mismatch')
            conn.simulation.subscribe((c.VAR_TIME,c.VAR_DEPARTED_VEHICLES_IDS,c.VAR_ARRIVED_VEHICLES_IDS,c.VAR_COLLIDING_VEHICLES_IDS,c.VAR_TELEPORT_STARTING_VEHICLES_IDS,c.VAR_PENDING_VEHICLES))
            vv=(c.VAR_SPEED,c.VAR_ACCELERATION,c.VAR_LANE_ID,c.VAR_LANEPOSITION,c.VAR_ROAD_ID,c.VAR_LASTACTIONTIME,c.VAR_LENGTH,c.VAR_TYPE,c.VAR_DISTANCE,c.VAR_ROUTE_INDEX)
            for tick in range(1,round(spec['duration_s']/.05)+1):
                conn.simulationStep();sv=conn.simulation.getSubscriptionResults();now=float(sv[c.VAR_TIME])
                if abs(now-tick*.05)>1e-8:raise ValueError('runtime_clock')
                if sv[c.VAR_COLLIDING_VEHICLES_IDS] or sv[c.VAR_TELEPORT_STARTING_VEHICLES_IDS]:raise ValueError('collision_or_teleport')
                tls=conn.trafficlight.getRedYellowGreenState('b')
                if set(tls)!={'r'}:raise ValueError('unexpected_signal_state')
                new=set(sv[c.VAR_DEPARTED_VEHICLES_IDS]);gone=set(sv[c.VAR_ARRIVED_VEHICLES_IDS])
                if departed&new or not new<=set(defs) or not gone<=departed:raise ValueError('identity_lifecycle_error')
                departed.update(new);arrived.update(gone)
                for vid in new:conn.vehicle.subscribe(vid,vv)
                data=conn.vehicle.getAllSubscriptionResults();current={}
                for vid,v in sorted(data.items()):
                    if vid not in defs or v[c.VAR_TYPE]!=defs[vid]['type'] or abs(v[c.VAR_LENGTH]-float(types[v[c.VAR_TYPE]]['length']))>1e-10:raise ValueError('identity_type_length_error')
                    dev={d:conn.vehicle.getParameter(vid,'has.'+d+'.device') for d in DEVICES}
                    if any(s!='false' for s in dev.values()):raise ValueError('special_device_outside_domain')
                    route=list(conn.vehicle.getRoute(vid));stops=conn.vehicle.getStops(vid,0)
                    if route!=defs[vid]['route_edges'] or stops:raise ValueError('stop_or_route_mutation')
                    lane=v[c.VAR_LANE_ID];edge=v[c.VAR_ROAD_ID];x=v[c.VAR_LANEPOSITION]
                    if lane not in lanes or lanes[lane][0]!=edge or not -1e-6<=x<=lanes[lane][1]+1e-6:raise ValueError('coordinate_support_error')
                    proof=dict(official_source_contract_verified=read(batch/'source_audit.json')['source_verified'],fresh_vehicle_lifecycle=runtime['started_empty_fresh'] and vid in departed,
                        no_state_restore=runtime['state_load'] is False,no_dynamic_stop_mutation=not stops and not defs[vid]['input_stops'],no_route_mutation=route==defs[vid]['route_edges'],
                        no_collision_or_teleport=not sv[c.VAR_COLLIDING_VEHICLES_IDS] and not sv[c.VAR_TELEPORT_STARTING_VEHICLES_IDS],no_special_devices=all(s=='false' for s in dev.values()),
                        noncyclic_route_verified=len(route)==len(set(route)),ordinary_stop_definition_verified=not defs[vid]['input_stops'])
                    if set(proof)!=set(SOURCE_PROOF_KEYS):raise ValueError('proof_schema_error')
                    r=dict(run_id=run_id,vehicle_id=vid,incarnation_id=run_id+'|'+vid,time_s=now,speed_mps=float(v[c.VAR_SPEED]),acceleration_mps2=float(v[c.VAR_ACCELERATION]),
                        position_m=float(x),edge_id=edge,lane_id=lane,last_action_time_s=float(v[c.VAR_LASTACTIONTIME]),length_m=float(v[c.VAR_LENGTH]),traveled_distance_m=float(v[c.VAR_DISTANCE]),
                        route_index=int(v[c.VAR_ROUTE_INDEX]),route_edges=route,remaining_stops=[],input_has_stops=False,traci_vehicle_control=False,numerical_config_verified=runtime['verified'])
                    states.append(r);current[vid]=r;device_proofs[vid]=dev
                    if vid in previous:
                        a=previous[vid];result=classify_edge(a,r,proof,bindings_verified=True)
                        record=dict(before=a,after=r,lifecycle_proof=proof,postprocessing_exclusion_devices=dev,source_audit_sha256=sha(batch/'source_audit.json'),
                            plan_sha256=sha(batch/'experiment_plan.json'),result=result)
                        audits.write(json.dumps(record,allow_nan=False)+'\n');audits.flush()
                        counts[result['classification']]+=1;numerical[result['numerical_classification']]+=1;reason_counts[result['reason']]+=1
                        if result['residual_m'] is not None:residuals.append(abs(result['residual_m']))
                        if result['u_pre'] is not None and result['u_pre']>0:positive_values.append(result['u_pre'])
                        if result['target_exact_pass']:targets.append(record)
                        if result['classification']=='Near-Zero Context Unresolved':contexts.append(record)
                        if result['is_action'] is False and result['u_pre'] is not None and 0<result['u_pre']<1e-4 and not result['target_candidate']:controls.append(record)
                        if result['blocker']:raise ValueError(result['blocker'])
                pending=set(sv[c.VAR_PENDING_VEHICLES]);residual=len(departed)-len(arrived)-len(current)
                if residual or set(current)!=(departed-arrived) or pending!=(set(defs)-departed):raise ValueError('vehicle_conservation_error')
                conservation.append(dict(time_s=now,inserted=len(departed),exited=len(arrived),present=len(current),pending=len(pending),residual=residual))
                previous=current;last_complete=now
                if time.monotonic()-begin>plan['limits']['per_run_wall_s']-5:raise TimeoutError('worker_wall_limit')
        except Exception as exc:
            failure=f'{type(exc).__name__}: {exc}';blockers.append(str(exc))
        finally:
            if conn is not None:
                try:conn.close()
                except Exception:pass
    for name,value in [('states.json',states),('target_edges.json',targets),('control_edges.json',controls),('unresolved_edges.json',contexts),('accounting.json',conservation),('device_proofs.json',device_proofs)]:write(out/name,value)
    status='completed_with_engineering_blocker' if blockers else 'completed_valid'
    write(out/'summary.json',dict(run_id=run_id,kind=spec['kind'],status=status,failure=failure,engineering_blockers=blockers,warnings=[],planned_s=spec['duration_s'],observed_s=last_complete,
        target_exact_count=len(targets),target_status='Exact Pass' if targets and not blockers else 'Engineering Blocker' if blockers else 'Not Observed',
        target_classifications=dict(counts),general_numerical_classifications=dict(numerical),reasons=dict(reason_counts),all_adjacent_edges=sum(counts.values()),
        max_abs_exact_residual_m=max(residuals) if residuals else None,exact_tolerance_m=1e-6,control_edges=len(controls),unresolved_edges=len(contexts),
        positive_candidates=positive_values,inserted=len(departed),exited=len(arrived),present=len(previous),max_conservation_residual=max([abs(x['residual']) for x in conservation] or [0]),
        runtime_settings=runtime,wall_s=time.monotonic()-begin,state_rows=len(states),plan_sha256=sha(batch/'experiment_plan.json'),
        C_D_allowed=False,main_matrix_allowed=False,scientific_claim_eligible=False))
    print(f'B12P_WORKER {run_id} {status} target={len(targets)} failure={failure}',flush=True)
