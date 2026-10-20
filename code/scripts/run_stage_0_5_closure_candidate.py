"""Two-condition finite candidate; never a C/D/ABCD mechanism comparison."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/src'))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare(b,reference):
    import numpy as np
    from riskprop.stage_0_5_b12_runtime import build_network,make_config,FIXED
    from riskprop.stage_0_5_b12_network import coordinate_support
    from riskprop.stage_0_5_sumo import _sumo_binary
    if b.exists():raise PermissionError('new_candidate_capsule_required')
    for n in ['inputs','runs','summary','runtime/code/src/riskprop','runtime_cache/tmp','dependency_links']:(b/n).mkdir(parents=True,exist_ok=True)
    p=read(reference/'reference_plan.json')
    for n,d in p['frozen_files'].items():
        if n.startswith('runtime/') or n.startswith('official_source/'):
            if sha(reference/n)!=d:raise PermissionError('reference_runtime_SHA')
            target=b/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(reference/n,target)
    import _winapi
    for link in (reference/'dependency_links').iterdir():_winapi.CreateJunction(str(link.resolve()),str(b/'dependency_links'/link.name))
    shutil.copyfile(reference/'isolation_policy.json',b/'isolation_policy.json')
    shutil.copyfile(reference/'source_audit.json',b/'source_audit.json') if (reference/'source_audit.json').exists() else None
    # Fresh/no-stop lifecycle proof is pinned independently in the official
    # contract audited by the prior LF capsule; no traffic output is imported.
    old=ROOT/'code/outputs/formal/calibration/stage_0_5_local_following_v1'
    source=read(old/'source_audit.json')
    if not source['source_verified']:raise PermissionError('official_source_not_verified')
    write(b/'source_audit.json',source)
    shutil.copyfile(reference/'closure_entry.py',b/'closure_analysis.py')
    shutil.copyfile(Path(__file__),b/'candidate_entry.py')
    ref=read(reference/'inputs/real_reference_summary.json');details=read(reference/'inputs/diagnostics.json')
    write(b/'inputs/target_summary.json',dict(windows=details['windows'],fleet=ref['fleet'],source_sha256=sha(reference/'inputs/diagnostics.json')))
    specs=[]
    for j,(group,flow,green) in enumerate([('us101__0750_0805',1648.,48.),('us101__0805_0820',1449.8181818181818,42.2)]):
        network=build_network(b/'inputs'/group,'C',1.)
        tree=ET.parse(network);logic=tree.getroot().find('tlLogic')
        phases=logic.findall('phase');durations=[green,6.2,round(60-green-6.2,1)]
        for phase,duration in zip(phases,durations):phase.set('duration',str(duration))
        logic.set('programID','closure_conditional_supply_v1');tree.write(network,encoding='utf-8',xml_declaration=True)
        support=coordinate_support(network)
        if not support['coordinate_verified']:raise PermissionError('static_coordinate_support')
        routes=ET.Element('routes')
        for i,f in enumerate(ref['fleet']):ET.SubElement(routes,'vType',dict(id='t'+str(i),vClass=f['vClass'],length=str(f['length_m']),**{k:str(v) for k,v in FIXED.items()}))
        ET.SubElement(routes,'route',dict(id='through',edges='main_0 main_1 main_2'))
        times=np.arange(3600/(3*flow),300-.1,3600/(3*flow));times=np.ceil(times*10-1e-8)/10
        # Deterministic systematic fleet quantiles: fixed observed composition
        # is a conditional arrival assumption, not identified upstream fleet.
        probs=np.cumsum([f['share'] for f in ref['fleet']]);counts=[0]*len(probs)
        for k,t in enumerate(times):
            u=((k*.6180339887498949)+.5)%1;kind=int(np.searchsorted(probs,u));kind=min(kind,len(probs)-1);counts[kind]+=1
            ET.SubElement(routes,'vehicle',dict(id=f'v{k:05d}',type='t'+str(kind),route='through',depart=f'{t:.1f}',departLane=str(k%3),departPos='base',departSpeed='max'))
        demand=b/'inputs'/(group+'.rou.xml');ET.ElementTree(routes).write(demand,encoding='utf-8',xml_declaration=True)
        for role,seed in [('construction',20261019),('repeat',20261020+j)]:
            rid=('FC'+str(j+1)) if role=='construction' else ('FR'+str(j+1));cfg=make_config(b,rid,network,demand,300.,seed)
            specs.append(dict(run_id=rid,kind='LF',tier='local_candidate',role=role,condition=group,seed=seed,duration_s=300.,
                network=network.relative_to(b).as_posix(),demand=demand.relative_to(b).as_posix(),config=cfg.relative_to(b).as_posix(),
                declared_vehicles=len(times),fleet_counts=counts,flow_veh_h_lane=flow,expected_tls_durations=[durations],reader_mode='batch',
                local_space=dict(edge='main_1',start_m=50.,end_m=250.,lanes=3,lane_km=.6)))
    specs.sort(key=lambda r:(r['role']!='construction',r['run_id']))
    old_summary=read(old/'runs/lf1_LF3/summary.json')
    cost=old_summary['runtime']['total_worker_wall_s']/old_summary['runtime']['internal_state_rows']
    # Independent, conservative no-exit row bound. If above the worker cap,
    # actual live resource guards still stop; no450s extension is admitted.
    bounds={r['run_id']:float(sum((300-t)/.05 for t in np.ceil(np.arange(3600/(3*r['flow_veh_h_lane']),299.9,3600/(3*r['flow_veh_h_lane']))*10-1e-8)/10)*cost) for r in specs}
    plan=dict(result_id='RES-STAGE-0.5-FINAL-CLOSURE-V1',version='closure-conditional-candidate-v1',contract_version='verified-fresh-no-stop-layered-plus-approved-D1',
        mode='Authorized finite calibration candidate construction; conditional supply not real facility',runs=specs,
        scientific_delta=None,precision_h=None,validation_access=False,ABCD_allowed=False,
        limits=dict(per_run_wall_s=600,batch_wall_s=7200,memory_bytes=3*1024**3,artifact_bytes=2*1024**3),
        budget=dict(previous_targeted_used=3,new_max=5,max_construction=3,planned_construction=2,reserved_independent_repeats=2,unallocated=1,micro_remaining=0),
        evaluation=dict(mode='finite_time_dynamic',window_s=[180.,299.7],initialization='Fresh empty network;0..180s retained and described, not an approved steady-state warmup',
            basis='180s exceeds free travel to and across R at both real mean speeds including native junction lengths; last0.3s reserves actual confirmation. Fixed before trajectories/P2. No stationarity claim.',
            blocks_s=30.,full_network_pending_and_occupancy_retained=True),
        boundary=dict(origin='Independent new supply candidate, not retrospective oldC upgrade',cycle_s=60.,yellow_s=6.2,
            construction='Green48s at first observed internal flow,42.2s proportional to second;80% first duty is an engineering interior between open and old39.7% stress supply, not a scientific traffic fact or fitted P2 setting',
            demand='Observed internal mainline plane300 mean passage used only as conditional scheduled inflow, not true upstream demand',
            driving='Krauss/LC2013 FIXED unchanged; no driver parameter search',fleet='A+ observed class/length candidate; fixed conditional systematic sequence'),
        repeat_activation=dict(require_all_conditions=True,
            rule='All engineering checks complete; each target mean speed and density must lie within the envelope of predeclared30s evaluation blocks, and low-speed/closing states observed if present in real reference. This is necessary state support only, not a science tolerance or equivalence test.',
            otherwise='No further search or repeat; report Evidence Insufficient, preserve reserved runs'),
        stop=['SHA/source/config/binary/identity/clock/control','collision/teleport/conservation','exact1e-6m or source necessary range failure','resource cap','unexplained terminal-speed conflict'],
        uncertainty=read(reference/'reference_plan.json')['uncertainty'],
        cost_preflight=dict(old300_worker_s=old_summary['runtime']['total_worker_wall_s'],observed_cost_s_per_row=cost,no_exit_bound_s=bounds,
            estimate_not_guarantee=True,actual_same_scale300_verified_before=True,per_worker_cap_s=600,extension450_admitted=False,
            output_forecast_bytes_per_run=170*1024**2,tree_memory_reference_bytes=228253696,full_P2_postprocessing_wall_budget_s=900),
        sumo_binary_sha256=sha(_sumo_binary()),reference_plan_sha256=sha(reference/'reference_plan.json'),
        scientific_claim_eligible=False,reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False)
    from riskprop.stage_0_5_final_closure import check_run_plan
    check_run_plan(plan)
    write(b/'candidate_draft.json',plan)
    write(b/'execution_ledger.json',dict(global_stop=None,closed=False,actual_new_attempts=0,runs=[dict(run_id=r['run_id'],role=r['role'],condition=r['condition'],seed=r['seed'],status='not_attempted') for r in specs]))


def freeze(b):
    if (b/'PLAN_SHA256').exists():raise PermissionError('no_plan_overwrite')
    p=read(b/'candidate_draft.json')
    if not read(b/'empty_preflight.json')['passed']:raise PermissionError('empty_preflight_required')
    if not read(b/'isolation_probe.json')['passed']:raise PermissionError('negative_access_probe_required')
    p['frozen_files']={f.relative_to(b).as_posix():sha(f) for folder in ['inputs','runtime','official_source'] for f in (b/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts and '.pytest_cache' not in f.parts}
    for n in ['candidate_entry.py','closure_analysis.py','source_audit.json','isolation_policy.json','empty_preflight.json','isolation_probe.json','execution_guard_audit.json']:p['frozen_files'][n]=sha(b/n)
    p['controller_sha256']=sha(ROOT/'code/scripts/supervise_stage_0_5_closure.py')
    write(b/'experiment_plan.json',p);(b/'PLAN_SHA256').write_text(sha(b/'experiment_plan.json')+'\n')


def load(b):
    from riskprop.stage_0_5_final_closure import check_run_plan
    from riskprop.stage_0_5_sumo import _sumo_binary
    p=read(b/'experiment_plan.json')
    if sha(b/'experiment_plan.json')!=(b/'PLAN_SHA256').read_text().strip():raise PermissionError('plan_SHA')
    check_run_plan(p)
    for n,d in p['frozen_files'].items():
        path=(b/n).resolve()
        if not path.is_relative_to(b) or sha(path)!=d:raise PermissionError('frozen_SHA:'+n)
    if sha(_sumo_binary())!=p['sumo_binary_sha256']:raise PermissionError('binary_SHA')
    return p


def empty(b):
    from riskprop.stage_0_5_sumo import _sumo_binary,_ensure_traci_importable
    from riskprop.stage_0_5_b12n_worker import definitions
    from riskprop.stage_0_5_lf_worker import settings
    _ensure_traci_importable();import traci
    records=[]
    for r in read(b/'candidate_draft.json')['runs']:
        d=b/'empty_checks'/r['run_id'];d.mkdir(parents=True,exist_ok=False)
        traci.start([_sumo_binary(),'-c',str(b/r['config']),'--no-step-log','true'],label=r['run_id'])
        conn=traci.getConnection(r['run_id'])
        try:
            types,_=definitions(b/r['demand']);actual=settings(conn,r,types,d)
            records.append(dict(run_id=r['run_id'],verified=actual['verified'],vehicle_count=conn.simulation.getDepartedNumber(),actual=actual))
        finally:conn.close()
    write(b/'empty_preflight.json',dict(passed=all(x['verified'] and x['vehicle_count']==0 for x in records),zero_simulation_steps=True,new_trajectory_runs=0,software_smokes=len(records),records=records))


def worker(b,rid):
    from riskprop.stage_0_5_lf_worker import run_worker
    p=load(b);ledger=read(b/'execution_ledger.json');r=next(x for x in p['runs'] if x['run_id']==rid);e=next(x for x in ledger['runs'] if x['run_id']==rid)
    if ledger['global_stop'] or ledger['closed'] or e['status']!='not_attempted' or ledger['actual_new_attempts']>=5:raise PermissionError('stop_or_no_retry')
    if r['role']=='repeat' and not read(b/'candidate_checkpoint.json')['repeats_allowed']:raise PermissionError('candidate_support_not_qualified')
    e['status']='running';ledger['actual_new_attempts']+=1;write(b/'execution_ledger.json',ledger)
    run_worker(b,rid,plan_loader=load)
    s=read(b/'runs'/rid/'summary.json');e.update(status=s['status'],observed_s=s['observed_s'],plan_sha256=s['plan_sha256'])
    if s['engineering_blockers'] or s['observed_s']!=r['duration_s']:
        ledger['global_stop']=dict(run_id=rid,reason=s['engineering_blockers'] or 'incomplete_run')
    write(b/'execution_ledger.json',ledger)
    if ledger['global_stop']:raise ValueError('candidate_worker_blocked')


def analyse(b,rid):
    import numpy as np
    import pandas as pd
    from riskprop.stage_0_5_local_following import decorate,formal_frame_preserving_flags
    from riskprop.stage_0_5_final_closure import local_p2
    import closure_analysis
    p=load(b);r=next(x for x in p['runs'] if x['run_id']==rid);folder=b/'runs'/rid;out=b/'summary'/rid;out.mkdir(exist_ok=False)
    s=read(folder/'summary.json')
    if s['engineering_blockers'] or s['plan_sha256']!=sha(b/'experiment_plan.json'):raise PermissionError('invalid_run_or_SHA')
    raw=pd.read_parquet(folder/'internal_states.parquet');m=decorate(raw.loc[np.rint(raw.time_s*20).astype(int)%2==0].copy())
    m['scenario_id']='closure_conditional_supply_v1';m['configured_seed']=r['seed'];m['experiment_mode']='stage_0_5_authorized_candidate';m['_inside']=m.in_local;m['_position']=m.position_m
    m.to_parquet(folder/'measured_points.parquet',index=False)
    d=formal_frame_preserving_flags(m);w=p['evaluation']['window_s'];a=local_p2(d,w)
    rows=a.pop('events');pd.DataFrame(rows).to_csv(out/'events.csv',index=False)
    E=a.pop('cluster_evaluable_s');N=a.pop('cluster_events');keys=sorted(set(E)|set(N))
    pd.DataFrame([dict(trajectory_id=k,evaluable_s=E.get(k,0),onset_events=N.get(k,0)) for k in keys]).to_csv(out/'clusters.csv',index=False)
    write(out/'P2.json',a);closure_analysis.descriptive(b,out,d,w,.6,rows)
    f=pd.read_csv(folder/'traffic_frames.csv');blocks=[]
    for start in [180.,210.,240.,270.]:
        end=min(start+30,w[1]);g=f[f.time_s.gt(start)&f.time_s.le(end+1e-8)];vt=float(g.local_present.sum()*.05)
        blocks.append(dict(start_s=start,end_s=end,mean_speed_mps=float(g.local_speed_sum.sum()*.05/vt) if vt else None,
            density=float(vt/.6/(end-start)),inserted=int(g.inserted_step.sum()),exited=int(g.exited_step.sum()),
            local_in=int(g.local_entered.sum()),local_out=int(g.local_exited.sum()),present_end=int(g.global_present.iloc[-1]),pending_end=int(g.external_pending.iloc[-1])))
    write(out/'state_support_blocks.json',dict(blocks=blocks,window_fixed_before_P2=True,global_conservation_max=float(f.global_conservation_residual.abs().max()),
        local_balance_max=float(f.local_set_balance_residual.abs().max()),full_network_final_present=s['present'],full_network_pending=s['pending_end']))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','empty','probe','freeze','worker','analyse']);p.add_argument('--batch',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--run-id');a=p.parse_args();b=a.batch.resolve()
    if a.command=='prepare':prepare(b,a.reference.resolve());return
    if a.command=='freeze':freeze(b);return
    if not sys.flags.no_site:raise PermissionError('python_-S_required')
    sys.path.insert(0,str(b/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(b);os.environ.update(PYTHONPYCACHEPREFIX=str(b/'runtime_cache/pycache'),TEMP=str(b/'runtime_cache/tmp'),TMP=str(b/'runtime_cache/tmp'))
    try:
        if a.command=='probe':
            from riskprop.stage_0_5_sumo import CalibrationValidationGuard,Stage05AccessDenied
            expected=0
            try:open(b.parent/'forbidden_probe.txt','r')
            except PermissionError:expected+=1
            g=CalibrationValidationGuard()
            for role,sources in [('calibration',['us101__0820_0835']),('locked_holdout',['us101__0750_0805'])]:
                try:g.require(role=role,sources=sources,purpose='negative role probe; no file read')
                except Stage05AccessDenied:expected+=1
            write(b/'isolation_probe.json',dict(passed=expected==3 and len(guard['denied'])==1,expected_denials=expected,guard=guard,role_audit=g.audit(),no_forbidden_content_read=True))
        elif a.command=='empty':empty(b)
        elif a.command=='worker':worker(b,a.run_id)
        else:analyse(b,a.run_id)
    finally:write(b/(a.command+'_'+str(a.run_id or 'all')+'_access_audit.json'),guard)
    if guard['denied'] and a.command!='probe':raise PermissionError('unexpected_access')


if __name__=='__main__':main()
