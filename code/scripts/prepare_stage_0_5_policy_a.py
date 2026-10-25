"""Policy A preflight only. Never imports TraCI or launches SUMO.

Only two approved canonical sources and their existing matched baselines are
read. A proposal manifest/hash is NOT a protocol lock or permission to execute.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import psutil

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/src'))
from riskprop.stage_0_5_d1_measurement import offset100_cloud, local_d1_measurement
from riskprop.stage_0_5_final_closure import checked, links, local_p2, real_region_mask
from audit_stage_0_5_work_package_1 import edge_and_event_audit, sha

SOURCES={'us101__0750_0805':120.,'us101__0805_0820':180.}
RUNS=[('ID1_SUPPLY_0750','us101__0750_0805','supply'),('ID2_SUPPLY_0805','us101__0805_0820','supply'),('ID3_RAMP_0750','us101__0750_0805','ramp')]


def write(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def pulse_routes(source,destination):
    tree=ET.parse(source);root=tree.getroot();vehicles=root.findall('vehicle')
    before={v.get('id'):dict(v.attrib) for v in vehicles}
    bins={}
    for v in vehicles:
        if v.get('route')=='entering' and not v.get('id').startswith('i'):
            bins.setdefault(int(float(v.get('depart'))//60),[]).append(v)
    for block,group in bins.items():
        group.sort(key=lambda v:(float(v.get('depart')),v.get('id')))
        for index,v in enumerate(group):
            depart=60*block+20+(5*index/(len(group)-1) if len(group)>1 else 0)
            v.set('depart',f'{round(depart/.05)*.05:.2f}')
    for v in vehicles:root.remove(v)
    for v in sorted(vehicles,key=lambda v:(float(v.get('depart')),v.get('id'))):root.append(v)
    changed=0
    for v in vehicles:
        old=before[v.get('id')];new=dict(v.attrib)
        if old!=new:
            assert v.get('route')=='entering' and not v.get('id').startswith('i')
            assert {k:x for k,x in old.items() if k!='depart'}=={k:x for k,x in new.items() if k!='depart'}
            assert int(float(old['depart'])//60)==int(float(new['depart'])//60)
            changed+=1
    tree.write(destination,encoding='utf-8',xml_declaration=True)
    return {'changed_departures':changed,'all_other_vehicle_attributes_unchanged':True,
            'ramp_counts_by_60s_block':{str(k):len(v) for k,v in bins.items()}}


def real_support(d,origin):
    window=(origin+120,origin+390)
    d=d.copy();d['_inside']=real_region_mask(d);d['_position']=d.y_m
    result=local_p2(d,window)
    oracle=edge_and_event_audit(d,window,real=True)
    assert result['counts']['onset']==oracle['onset_N']
    assert abs(result['exposure']['local_evaluable_s']-oracle['D1_E_veh_s'])<1e-7
    cloud=offset100_cloud(d,window)
    ordered=checked(d)
    for yi,region in enumerate([(150,250),(250,350)]):
        ordered['_inside']=ordered.lane_id.astype(str).isin(['1','2','3','4','5'])&ordered.y_m.ge(region[0])&ordered.y_m.lt(region[1])
        edges=links(ordered,window)
        for ti in range(9):
            low=origin+120+ti*30;high=low+30
            exposure=int((edges.local&edges.previous_s.ge(low-1e-9)&ordered.time_s.le(high+1e-9)).sum())/10
            mask=cloud.t_block.eq(ti)&cloud.y_block.eq(yi)
            cloud.loc[mask,'D1_E_veh_s']=exposure
    cloud['elapsed_start_s']=cloud.block_start_s-origin
    return result,cloud


def prepare(out):
    out.mkdir(parents=True,exist_ok=False);portable=out/'portable';portable.mkdir()
    authorization={'policy':'A','status':'Agreed task-level initialization policy only',
        'evaluation_elapsed_s':[120,390],'supply_pulse_s':[180,240],'duration_s':420,'seed':20261201,
        'initial_0750':{'at_120':1,'last_local_s':130.5,'records_in_window':106,'vehicle_s':10.6},
        'initial_0805':{'at_120':0},'new_runs_must_measure_own_initialization':True,
        'proposal_frozen':False,'run_permission':False,'attempts':0,'remaining_budget':3,
        'finite_dynamic_not_steady_state':True,'Gate_changed':False}
    write(portable/'authorization.json',authorization)
    inputs={};reports=[];baselines={}
    prior=json.loads((ROOT/'docs/audits/stage_0_5_wp1_v1/provenance.json').read_text())['inputs']
    for w,origin in SOURCES.items():
        print('checking approved source '+w,flush=True)
        relative=f'code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_{w}.parquet'
        path=ROOT/relative;digest=sha(path)
        assert digest==prior[relative]['sha256']
        inputs[relative]=digest
        real=pd.read_parquet(path);r,rc=real_support(real,origin)
        # Full real events stay local; portable only aggregate support.
        write(out/(w+'_real_D1.json'),r)
        simpath=ROOT/f'code/outputs/formal/calibration/stage_0_5_c6_c7_offline_v1/{w}/repaired_measured_state.parquet'
        inputs[simpath.relative_to(ROOT).as_posix()]=sha(simpath)
        sim=pd.read_parquet(simpath);sc=offset100_cloud(sim,(120,390));sr=local_d1_measurement(sim,(120,390),strict=True)
        for yi,region in enumerate([(150,250),(250,350)]):
            for ti in range(9):
                sub=local_d1_measurement(sim,(120+ti*30,150+ti*30),region=region,strict=True)
                sc.loc[sc.t_block.eq(ti)&sc.y_block.eq(yi),'D1_E_veh_s']=sub['local_evaluable_s']
        sc['elapsed_start_s']=sc.block_start_s
        joined=rc.merge(sc,on=['t_block','y_block'],suffixes=('_real','_sim'),validate='one_to_one')
        joined['common_observed_support']=(joined.support_status_real.eq('observed')&joined.support_status_sim.eq('observed')&joined.D1_E_veh_s_real.gt(0)&joined.D1_E_veh_s_sim.gt(0))
        rc.to_csv(portable/(w+'_real_offset100.csv'),index=False);sc.to_csv(portable/(w+'_baseline_offset100.csv'),index=False)
        joined.to_csv(portable/(w+'_common_support.csv'),index=False)
        reports.append({'window':w,'real_absolute_window_s':[origin+120,origin+390],
            'real_N':r['counts']['onset'],'real_E_veh_s':r['exposure']['local_evaluable_s'],
            'baseline_N':sr['onset_events'],'baseline_E_veh_s':sr['local_evaluable_s'],
            'common_cells':int(joined.common_observed_support.sum()),'planned_cells':18,
            'real_density_range':[float(rc.density_veh_km_lane.min()),float(rc.density_veh_km_lane.max())],
            'sim_density_range':[float(sc.density_veh_km_lane.min()),float(sc.density_veh_km_lane.max())],
            'real_speed_range':[float(rc.speed_mean_mps.min()),float(rc.speed_mean_mps.max())],
            'sim_speed_range':[float(sc.speed_mean_mps.min()),float(sc.speed_mean_mps.max())],
            'interpretation':'common geometric/time support and positive qualified exposure only; not matched traffic distribution, physical observability, scientific equivalence or future-run guarantee',
            'real_independent_D1_match':True})
        baselines[w]=ROOT/f'code/outputs/formal/calibration/stage_0_5_state_support_v1/seeds/B_het_{w}_vlim10.00_s20261201'
    run_entries=[]
    for run_id,w,kind in RUNS:
        base=baselines[w];dest=out/'prepared_inputs'/run_id;dest.mkdir(parents=True)
        net=base/'network/observed_geometry_supply_10p0_l5.net.xml';routes=base/'routes.rou.xml'
        for f in [net,routes,base/'run.sumocfg']:inputs[f.relative_to(ROOT).as_posix()]=sha(f)
        shutil.copyfile(net,dest/'network.net.xml')
        static={'route_attributes_unchanged':True}
        if kind=='ramp':static=pulse_routes(routes,dest/'routes.rou.xml')
        else:shutil.copyfile(routes,dest/'routes.rou.xml')
        lanes=[l for e in ET.parse(net).getroot().findall('edge') if e.get('id')=='main_2' for l in e.findall('lane')]
        assert len(lanes)==5 and all(float(l.get('speed'))==10 for l in lanes)
        cfg=ET.parse(base/'run.sumocfg');cfg.getroot().find('input/net-file').set('value','network.net.xml');cfg.write(dest/'run.sumocfg',encoding='utf-8',xml_declaration=True)
        assert float(cfg.getroot().find('time/end').get('value'))==420
        assert int(cfg.getroot().find('seed').get('value'))==20261201
        route_root=ET.parse(dest/'routes.rou.xml').getroot();vehicles=route_root.findall('vehicle')
        declared={route:sum(v.get('route')==route and not v.get('id').startswith('i') for v in vehicles) for route in ['through','entering','exiting']}
        run_entries.append({'id':run_id,'window':w,'role':kind,'evaluation_elapsed_s':[120,390],
            'supply_pulse_s':[180,240] if kind=='supply' else None,'supply_base_mps':10,'supply_pulse_mps':5 if kind=='supply' else None,
            'declared_noninitial_route_vehicle_counts':declared,'actual_insertion_status':'Unknown until authorized run; not internal section demand',
            'route_check':static,'seed':20261201,'duration_s':420,'attempt_status':'not_attempted',
            'prepared_input_sha256':{f.name:sha(f) for f in sorted(dest.iterdir())}})
    disk={drive:shutil.disk_usage(drive).free for drive in ['C:/','D:/']};memory=psutil.virtual_memory()
    binary=shutil.which('sumo')
    if binary is None:raise ValueError('SUMO_binary_not_found_readonly_check')
    historical_bytes=max(sum((b/n).stat().st_size for n in ['fcd.xml','measured_state.parquet','summary.xml']) for b in baselines.values())
    resources={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'disk_free_bytes':disk,
        'available_memory_bytes':memory.available,'historical_largest_baseline_output_bytes':historical_bytes,
        'planning_estimate_three_runs_bytes':historical_bytes*3*2,'artifact_cap_bytes':2*1024**3,
        'runtime_limits':{'per_attempt_wall_s':600,'batch_wall_s':3600,'process_tree_rss_bytes':3*1024**3,'workers':1},
        'disk_threshold_bytes':{'C:/':5*1024**3,'D:/':14*1024**3},
        'snapshot_pass':disk['C:/']>=5*1024**3 and disk['D:/']>=14*1024**3 and memory.available>=4*1024**3 and historical_bytes*6<2*1024**3,
        'must_recheck_before_each_run':True,'runtime_unverified':True,
        'sumo_binary_path':binary,'sumo_binary_sha256':sha(Path(binary)),'SUMO_processes_started':0,
        'python':sys.version,'platform':platform.platform(),'pandas':pd.__version__,'numpy':np.__version__,'psutil':psutil.__version__}
    write(portable/'common_support_summary.json',reports);write(portable/'resource_preflight.json',resources)
    sources=['code/scripts/prepare_stage_0_5_policy_a.py','code/scripts/interaction_diagnostic_worker.py','code/src/riskprop/stage_0_5_state_support.py','code/src/riskprop/stage_0_5_d1_measurement.py','code/src/riskprop/stage_0_5_scene_reconstruction.py','code/src/riskprop/stage_0_5_sumo.py','code/src/riskprop/stage_0_5_final_closure.py','code/src/riskprop/formal_risk_measurement.py']
    proposal={'task_id':'AAD-0.5-INTERACTION-DIAGNOSTICS-V1','policy':'A','status':'Proposed / Awaiting Researcher Confirmation',
        'protocol_frozen':False,'execution_allowed':False,'attempts':0,'runs':run_entries,
        'phase_elapsed_s':[[120,180],[180,240],[240,300],[300,360],[360,390]],
        'source_sha256':{p:sha(ROOT/p) for p in sources},'input_sha256':inputs,
        'git_baseline_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'worktree':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(),
        'all_baseline_cells_observed':all(r['common_cells']==18 for r in reports),'resource_snapshot_pass':resources['snapshot_pass'],
        'initialization':'measure each new run; retain all initial vehicles; disclose local count at120, last local observation, records/vehicle-s, global remaining and pending; do not assert equal initialization',
        'comparison_limits':'Same spatial/time support does not equate real and simulator physical observability or traffic distributions. New runs cannot be verified before execution.',
        'supervision_required':'Single process tree; record attempt before launch; enforce wall/RSS/disk/output caps; stop only owned tree; failures and retries consume budget; no automatic retry.',
        'stop_rules':['identity/clock/source/hash failure','no effective common qualified support','input fidelity failure','resource cap','budget insufficient'],
        'scientific_claim_eligible':False,'protocol_lock_allowed':False}
    write(portable/'final_plan_proposal.json',proposal)
    (portable/'PROPOSAL_SHA256').write_text(sha(portable/'final_plan_proposal.json')+'\n',encoding='utf-8')
    (portable/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(portable.iterdir()) if p.is_file()),encoding='utf-8')
    print(json.dumps({'support':reports,'resource_snapshot_pass':resources['snapshot_pass'],'attempts':0},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    prepare(p.parse_args().output)
