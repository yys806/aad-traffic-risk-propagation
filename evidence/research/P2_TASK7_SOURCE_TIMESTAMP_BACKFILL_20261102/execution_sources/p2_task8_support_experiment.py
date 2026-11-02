"""Bounded Task8 support recovery, reusing Task7 native executor and operators."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
import psutil
import p2_task7_measurement as m
import analyze_p2_task7_parameter_experiment as a
import run_p2_task7_parameter_experiment as runner

ROOT=Path(__file__).resolve().parents[2]
HISTORY=ROOT/'code/outputs/calibration/p2_task7_20261102_v2'
TASK='AAD-P2-TASK8-BOUNDED-POSITIVE-SUPPORT-AND-V-DECISION-20261102'
TRUTH='AAD-P2T8-TRUTH-20261102-v1'

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,value):m.dump(p,value)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def utc():return datetime.now(timezone.utc).isoformat()

def spans(t,positive):
    groups=np.split(np.flatnonzero(positive),np.flatnonzero(np.diff(np.flatnonzero(positive))>1)+1)
    usable=[g for g in groups if len(g) and t[g[0]]<=46+1e-9]
    longest=max((float(t[g[-1]]-t[g[0]]) for g in usable),default=0.)
    qualified=[g for g in usable if t[g[-1]]-t[g[0]]>=1-1e-9]
    return {'span_s':longest,'onset_s':float(t[qualified[0][0]]) if qualified else None,'positive':bool(qualified)}

def physical_source_interval(raw,audit):
    """Command-time lower bound and independently observed change upper bound.

    The legacy conjunction speed != getSpeedWithoutTraCI can be late when SUMO
    clips a commanded ramp to native deceleration. Preserve that legacy field.
    A pre-only realized acceleration envelope is an audit signature, not a
    universal physical precision certificate. A missing signature is Unknown.
    """
    if not audit.get('actuated_source') or not len(raw['t']):return None
    t=raw['t'];i=0 if audit['actuated_source']=='s0' else raw['v'].shape[1]-1
    execution=audit['source_execution'];pre=(t>=10)&(t<=execution+1e-9)
    reference=float(raw['v'][np.flatnonzero(t<=execution+1e-9)[-1],i])
    floor=float(raw['a'][pre,i].min())
    idx=np.flatnonzero((t>execution+1e-9)&(raw['a'][:,i]<floor-1e-6)&(raw['v'][:,i]<reference-1e-6))
    return [float(execution),float(t[idx[0]])] if len(idx) else None

def measures(raw):
    t=raw['t'];v=raw['v'];x=raw['x'];lane=raw['lane']
    inside=(x>=m.REGION[0])&(x<m.REGION[1])&(lane==0);inside[:,0]=False
    macro=a.fast_edie(t,x,lane,.1)
    valid={'cohort':inside[:,m.COHORT].all(axis=1),'macro':macro['complete']&np.isfinite(macro['u'])}
    signals={'cohort':np.mean(10-v[:,m.COHORT],axis=1),'macro':10-macro['u']}
    micro=[]
    for i in range(1,v.shape[1]-1):
        s=10-v[:,i];positive=inside[:,i]&(s>=1-1e-10)&(t>=30-1e-9)
        r=spans(t,positive);r['entity']=i
        if r['positive']:micro.append(r)
    result={}
    for layer in ('cohort','macro'):
        support=valid[layer]&(t>=30-1e-9);monitor=support&(t<=46+1e-9)
        result[layer]={'peak_mps':float(np.max(signals[layer][monitor])) if monitor.any() else None,
            'a1':spans(t,support&(signals[layer]>=1-1e-10)),
            'a2':spans(t,support&(signals[layer]>=2-1e-10)),'coverage':float(valid[layer][(t>=30)&(t<=46)].mean())}
    region=(t>=30)&(t<=46)
    values=np.where(inside,10-v,-np.inf)
    result['micro']={'peak_mps':float(values[region].max()),'a1':{'positive':bool(micro),
        'onset_s':min((r['onset_s'] for r in micro),default=None),'span_s':max((r['span_s'] for r in micro),default=0.)},
        'a2':{'positive':any(spans(t,inside[:,i]&(10-v[:,i]>=2-1e-10)&(t>=30))['positive'] for i in range(1,v.shape[1]-1))},
        'responding_entities':[r['entity'] for r in micro],'max_response_entity':max((r['entity'] for r in micro),default=None)}
    return result

def audit_history(out):
    if out.exists():raise FileExistsError('Do not overwrite Task8 output '+str(out))
    out.mkdir(parents=True)
    for name in ['audit','raw','truth','detector','config','snapshots']:(out/name).mkdir()
    start=time.time();manifest=load(HISTORY/'manifest.json');rows=[];sources=[];hashes={}
    for unit in manifest['units']:
        uid=unit['unit_id'];audit=load(HISTORY/'audit'/f'{uid}.json');labels=load(HISTORY/'truth'/f'{uid}.json')
        rawpath=HISTORY/'raw'/uid/'trajectory.npz'
        hashes[uid]={'raw':m.sha(rawpath),'truth':m.sha(HISTORY/'truth'/f'{uid}.json'),'audit':m.sha(HISTORY/'audit'/f'{uid}.json')}
        if audit['status']!='COMPLETE':
            for label in labels:rows.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'layer':label['measurement_layer'],'state':'unknown','cause':'preserved startup failure'})
            continue
        with np.load(rawpath) as f:raw={k:f[k] for k in f.files}
        detail=measures(raw);actual=physical_source_interval(raw,audit);t=raw['t']
        sources.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],
            'source_amplitude_mps':unit['amplitude_mps'],'hold_s':unit['hold_s'],
            'source_min_speed':float(raw['v'][:,0].min()),'source_min_acceleration':float(raw['a'][:,0].min()),
            'legacy_source_interval':audit['actual_source_onset'],'independent_signature_interval':actual,
            'physical_source_interval_is_finite_audit_only':True,'native_targets':bool(np.allclose(raw['v'][:,1:-1],raw['native'][:,1:-1],atol=1e-8,rtol=0))})
        for label in labels:
            layer=label['measurement_layer'];d=detail[layer]
            if d['a1']['positive']!=(label['state_truth']=='positive'):raise AssertionError('Independent state audit mismatch '+uid+' '+layer)
            reason='realized' if d['a1']['positive'] else 'below_a_star' if d['peak_mps']<1 else 'duration_b_star_or_fixed_support'
            rows.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'layer':layer,
                'state':label['state_truth'],'peak_mps':d['peak_mps'],'span_a1_s':d['a1']['span_s'],
                'onset_a1_s':d['a1']['onset_s'],'a2_realized':d['a2']['positive'],
                'fixed_cohort_peak':detail['cohort']['peak_mps'],'macro_peak':detail['macro']['peak_mps'],
                'responding_entities':detail['micro']['responding_entities'],'max_response_entity':detail['micro']['max_response_entity'],
                'source_actual_interval':actual,'cause':reason,'native_target_verified':label['native_target_verified']})
    a.csv_write(out/'audit/task7_support_audit.csv',rows);a.csv_write(out/'audit/task7_source_dynamics.csv',sources)
    counts=Counter((r['layer'],r['density'],r['condition'],r['state']) for r in rows)
    a.csv_write(out/'audit/task7_support_counts.csv',[dict(layer=k[0],density=k[1],condition=k[2],state=k[3],n=v) for k,v in sorted(counts.items())])
    dump(out/'audit/task7_input_hashes.json',{'hashes':hashes,'frozen_truth_version':m.TRUTH_VERSION,'task7_modified':False})
    summary=[]
    for density in runner.DENSITIES:
        for condition in ['P22','Plocal']:
            rr=[r for r in rows if r['density']==density and r['condition']==condition]
            summary.append({'density':density,'condition':condition,'layers':{layer:{'peak_range':[min(r['peak_mps'] for r in rr if r['layer']==layer),max(r['peak_mps'] for r in rr if r['layer']==layer)],'positive':sum(r['state']=='positive' for r in rr if r['layer']==layer),'max_entity_range':sorted(set(r['max_response_entity'] for r in rr if r['layer']==layer),key=lambda x:-1 if x is None else x)} for layer in a.LAYERS}})
    dump(out/'audit/task7_audit_summary.json',{'completed':575,'failed':1,'layer_records':len(rows),'examples':summary,
        'elapsed_s':time.time()-start,'new_experiment_budget_start_epoch':start,'source_timestamp_issue':'legacy source onset AND native-inequality can lag actual deceleration; original truth immutable',
        'input_freeze_sha256':m.sha(HISTORY/'audit/truth_freeze.json'),'git_sha':git('rev-parse','HEAD')})
    print(json.dumps({'status':'AUDIT_COMPLETE','examples':summary,'elapsed_s':time.time()-start}))

def budget(out,estimated_s=0.,estimated_bytes=0):
    start=load(out/'audit/task7_audit_summary.json')['new_experiment_budget_start_epoch']
    used=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    if time.time()-start+estimated_s>7200:raise RuntimeError('Task8 two-hour wall budget exhausted')
    if used+estimated_bytes>10*2**30:raise RuntimeError('Task8 10GiB output budget exhausted')
    if shutil.disk_usage(out.anchor).free<20*2**30+estimated_bytes:raise RuntimeError('20GiB disk reserve unavailable')
    return {'elapsed_wall_s':time.time()-start,'output_bytes':used,'disk_free':shutil.disk_usage(out.anchor).free}

def units_for(designs,round_number):
    namespace=[20261102,8,101 if round_number==1 else 202]
    seeds=np.random.SeedSequence(namespace).spawn(sum(d['n'] for d in designs));units=[];j=0
    for design in designs:
        density=design['density'];count,spacing=runner.DENSITIES[density]
        for rep in range(design['n']):
            condition=design['condition'];uid=f'S{round_number}_{density}_{condition}_{rep:02d}'
            units.append({'unit_id':uid,'dependency_block':uid,'split':'calibration_support_feasibility' if round_number==1 else 'supplementary_support',
                'density':density,'condition':condition,'rep':rep,'count':count,'spacing_m':spacing,
                'sumo_seed':int(seeds[j].generate_state(1)[0]%2147483646)+1,'seed_spawn_key':list(seeds[j].spawn_key),
                'amplitude_mps':design['amplitude'],'hold_s':design['hold'],
                'specified_source':'decoy' if condition in ('N1','A0') else 's0',
                'actuated_source':None if condition=='N0' else 'decoy' if condition=='N1' else 's0',
                'scenario_family':'straight_same_lane_native_Krauss_v1','input_trace':'new generated native traffic; no historical replay'})
            j+=1
    return units

def prepare(out):
    budget(out,estimated_s=2400,estimated_bytes=2*2**30)
    if (out/'manifest.json').exists():raise FileExistsError('Task8 already prepared')
    old=load(HISTORY/'manifest.json');designs=[]
    for density in runner.DENSITIES:
        for condition,amplitude,hold,n in [('LONG',8.,12.,8),('MAX',10.,12.,8),('N0',0.,0.,4),('N1',10.,12.,4),('A0',10.,12.,4)]:
            designs.append(dict(density=density,condition=condition,amplitude=amplitude,hold=hold,n=n))
    for condition,amplitude in [('LOCAL4',4.),('LOCAL8',8.)]:designs.append(dict(density='high',condition=condition,amplitude=amplitude,hold=1.,n=8))
    units=units_for(designs,1)
    prior={u['sumo_seed'] for u in old['units']}
    assert len(units)==100 and len({u['sumo_seed'] for u in units})==100 and not prior&{u['sumo_seed'] for u in units}
    shutil.copy2(HISTORY/'config/network.net.xml',out/'config/network.net.xml')
    paths=[Path(__file__),Path(m.__file__),Path(a.__file__),Path(runner.__file__)]
    for path in paths:shutil.copy2(path,out/'snapshots'/path.name)
    manifest={'task_id':TASK,'frozen_utc':utc(),'truth_version':TRUTH,'round':1,'designs':designs,'units':units,
        'source_design_rationale':'Task7 8m/s x8s failed support. LONG extends hold to12s; MAX reaches nonnegative speed floor0 for12s; local4/8 x1s interpolate source dose without moving support.',
        'strongest_allowed':{'amplitude_mps':10.,'hold_s':12.,'minimum_speed_mps':0.,'no_third_escalation':True},
        'curve':'Unchanged Task7 slowDown(1s) request, held speed, restoration and release; default SUMO speedMode enforces native 4.5 deceleration/2.6 acceleration. Requested ramp is not claimed realized.',
        'fixed':{k:old[k] for k in ['region','cohort','pre','monitor','followup_end','source_plan','raw_dt','truth_a','truth_b','truth_d','network_sha256']},
        'binary':old['binary'],'source_hashes':{p.relative_to(ROOT).as_posix():m.sha(p) for p in paths},
        'seed_namespaces':{'calibration_R1':[20261102,8,101],'supplementary_R2':[20261102,8,202],'independent_V':[20261102,8,303]},
        'round2_rule':'Truth-only: one LONG/MAX per density if any previously missing layer realized (high requires Macro2a); rank supported missing layers, then Macro2a count, then MAX fixed tie. One high local design if native Micro positive AND Cohort negative. Entire chosen design gets24 new seeds; no seed filtering. Controls8 per density/condition if any design selected.',
        'detector_candidates':{'center':asdict(a.Config(theta=1.,h=1.)),'theta_neighbor':asdict(a.Config(theta=.5,h=1.)),'h_neighbor':asdict(a.Config(theta=1.,h=2.))},
        'epsilon_stab':None,'gamma_int':None,'resource_cap':{'wall_s':7200,'bytes':10*2**30,'workers':4},
        'independent_V_requires_all_layers_all_densities':True,'historical_data_not_V':True,'locked_holdout_reads':0}
    dump(out/'manifest.json',manifest)
    dump(out/'provenance.json',{'git_sha':git('rev-parse','HEAD'),'dirty_status':git('status','--short'),
        'source_hashes':manifest['source_hashes'],'python':sys.version,'numpy':np.__version__,
        'SUMO':subprocess.check_output([old['binary'],'--version'],text=True),'binary_sha256':m.sha(old['binary']),
        'cpu_logical':psutil.cpu_count(),'memory':psutil.virtual_memory()._asdict(),'resources':budget(out),
        'history_truth_freeze_sha256':m.sha(HISTORY/'audit/truth_freeze.json'),'manifest_sha256':m.sha(out/'manifest.json')})
    print(json.dumps({'prepared_units':len(units),'resource':budget(out)}))

def failed_labels(unit,reason):
    return [{'truth_version':TRUTH,'unit_id':unit['unit_id'],'measurement_layer':layer,'state_truth':'unknown',
        'source_attribution':'unknown','onset_allowed_set':None,'confirmation_s':None,'recovery_interval_s':None,
        'a_star_mps':1.,'b_star_s':1.,'d_star_s':4.,'truth_error_s':.05,'truth_error_mps':None,
        'label_source':reason,'native_target_verified':False,'density':unit['density'],'condition':unit['condition'],
        'dependency_block':unit['unit_id'],'actual_source_onset':None,'source_execution':None,'label_hash':None} for layer in a.LAYERS]

def hash_labels(labels):
    for label in labels:
        label['label_hash']=None;label['label_hash']=hashlib.sha256(json.dumps(label,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return labels

def one(unit,out_string,binary):
    # Keep route, vType, movement, identity checks and observation code unchanged.
    home=Path(binary).parent.parent;sys.path.insert(0,str(home/'tools'));import traci
    original_start=traci.start
    def bounded_start(*args,**kwargs):
        kwargs.setdefault('numRetries',3);return original_start(*args,**kwargs)
    traci.start=bounded_start
    try:result=runner.one(unit,out_string,binary)
    finally:traci.start=original_start
    out=Path(out_string);uid=unit['unit_id'];path=out/'audit'/f'{uid}.json';audit=load(path)
    if result['status']=='COMPLETE':
        with np.load(out/'raw'/uid/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
        audit['legacy_executor_source_interval']=audit['actual_source_onset'];audit['actual_source_onset']=physical_source_interval(raw,audit)
        audit['source_interval_method']='command lower / observed native-state deceleration signature upper; pre-only realized envelope; no arbitrary physical precision certificate'
        source_index=0 if unit['actuated_source']!='decoy' else len(raw['v'][0])-1
        audit['source_min_acceleration']=float(raw['a'][:,source_index].min());audit['source_max_acceleration']=float(raw['a'][:,source_index].max())
        audit['source_min_speed']=float(raw['v'][:,source_index].min());audit['source_final_speed']=float(raw['v'][-1,source_index])
        if audit['source_min_acceleration']< -4.5-1e-6 or audit['source_max_acceleration']>2.6+1e-6 or audit['source_min_speed']< -1e-9:
            audit['status']=result['status']='FAILED_STOP';audit['error']='source physical dynamics violated existing vType bounds'
        labels=m.truth(raw,audit) if audit['status']=='COMPLETE' else failed_labels(unit,audit['error'])
        for label in labels:
            label['truth_version']=TRUTH;label['task7_state_operator_unchanged']=True
    else:labels=failed_labels(unit,audit.get('error','execution failure'))
    dump(path,audit);dump(out/'truth'/f'{uid}.json',hash_labels(labels));return result

def seal_round(out,units,round_number):
    hashes={};rows=[]
    for unit in units:
        uid=unit['unit_id'];labels=load(out/'truth'/f'{uid}.json');rows.extend(labels)
        hashes[uid]={k:m.sha(p) for k,p in {'raw':out/'raw'/uid/'trajectory.npz','truth':out/'truth'/f'{uid}.json','audit':out/'audit'/f'{uid}.json'}.items()}
    a.csv_write(out/'truth'/f'round{round_number}_inventory.csv',rows)
    dump(out/'audit'/f'round{round_number}_truth_freeze.json',{'frozen_utc':utc(),'hashes':hashes,'labels':len(rows),'detector_evaluations_before_freeze':0,'version':TRUTH})

def execute(out,round_number):
    manifest=load(out/('manifest.json' if round_number==1 else 'round2_manifest.json'));base=load(out/'manifest.json');units=manifest['units']
    for path,digest in base['source_hashes'].items():
        if m.sha(ROOT/path)!=digest:raise RuntimeError('frozen source hash drift '+path)
    if any((out/'audit'/f'{u["unit_id"]}.json').exists() for u in units):raise RuntimeError('Do not repeat or resume an attempted round')
    budget(out,estimated_s=20*len(units)/4+120,estimated_bytes=3_000_000*len(units))
    started=time.time();results=[];pending=iter(units);stopped=False
    with ProcessPoolExecutor(max_workers=4) as pool:
        active={}
        for _ in range(min(4,len(units))):
            u=next(pending);active[pool.submit(one,u,str(out),base['binary'])]=u
        while active:
            done,_=wait(active,return_when=FIRST_COMPLETED)
            for f in done:
                u=active.pop(f);r=f.result();results.append(r)
                if r['status']!='COMPLETE':stopped=True;dump(out/'audit/FAILED_STOP.json',r)
                print(json.dumps(r),flush=True)
            if not stopped:
                for _ in range(4-len(active)):
                    u=next(pending,None)
                    if u is None:break
                    try:budget(out,estimated_s=30,estimated_bytes=3_000_000)
                    except RuntimeError as error:stopped=True;dump(out/'audit/RESOURCE_STOP.json',{'reason':str(error)});break
                    active[pool.submit(one,u,str(out),base['binary'])]=u
    completed={r['unit_id'] for r in results}
    for u in units:
        if u['unit_id'] in completed:continue
        uid=u['unit_id'];folder=out/'raw'/uid;folder.mkdir();np.savez_compressed(folder/'trajectory.npz',t=np.array([]))
        dump(out/'audit'/f'{uid}.json',{**u,'status':'NOT_EXECUTED_STOP','rows':0,'native_target_setters':0,'collisions':0,'teleports':0,'elapsed_s':0})
        dump(out/'truth'/f'{uid}.json',hash_labels(failed_labels(u,'not executed after hard/resource stop')))
    seal_round(out,units,round_number)
    dump(out/'audit'/f'round{round_number}_completion.json',{'results':results,'stopped':stopped,'elapsed_s':time.time()-started,'resources':budget(out)})

def select_round2(out):
    if (out/'round2_manifest.json').exists():raise FileExistsError('R2 already frozen')
    first=load(out/'manifest.json');group={};details=[]
    for design in first['designs']:
        rr=[]
        for unit in first['units']:
            if unit['density']!=design['density'] or unit['condition']!=design['condition']:continue
            audit=load(out/'audit'/f'{unit["unit_id"]}.json')
            if audit['status']!='COMPLETE':continue
            with np.load(out/'raw'/unit['unit_id']/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
            rr.append(measures(raw))
        counts={layer:sum(r[layer]['a1']['positive'] for r in rr) for layer in a.LAYERS}
        macro2=sum(r['macro']['a2']['positive'] for r in rr)
        local=sum(r['micro']['a1']['positive'] and not r['cohort']['a1']['positive'] for r in rr)
        row={**design,'positive':counts,'macro2':macro2,'local_native_positive':local};details.append(row);group[(design['density'],design['condition'])]=row
    selected=[]
    for density in runner.DENSITIES:
        choices=[group[(density,c)] for c in ['LONG','MAX']]
        missing=['cohort','macro','micro'] if density=='low' else ['cohort','macro'] if density=='medium' else []
        def score(r):return (sum(r['positive'][layer]>0 for layer in missing) if missing else int(r['macro2']>0),r['macro2'],r['condition']=='MAX')
        best=max(choices,key=score)
        if score(best)[0]>0:selected.append({k:best[k] for k in ['density','condition','amplitude','hold']}|{'n':24})
    local=max([group[('high',c)] for c in ['LOCAL4','LOCAL8']],key=lambda r:(r['local_native_positive'],r['condition']=='LOCAL4'))
    if local['local_native_positive']>0:selected.append({k:local[k] for k in ['density','condition','amplitude','hold']}|{'n':24})
    if selected:
        for density in runner.DENSITIES:
            for condition in ['N0','N1','A0']:selected.append(dict(density=density,condition=condition,amplitude=0. if condition=='N0' else 10.,hold=0. if condition=='N0' else 12.,n=8))
    units=units_for(selected,2);old_seeds={u['sumo_seed'] for u in first['units']}|{u['sumo_seed'] for u in load(HISTORY/'manifest.json')['units']}
    assert not old_seeds&{u['sumo_seed'] for u in units} and len({u['sumo_seed'] for u in units})==len(units)
    dump(out/'round2_manifest.json',{'task_id':TASK,'frozen_utc':utc(),'round':2,'selected_designs':selected,'units':units,'R1_truth_freeze_sha256':m.sha(out/'audit/round1_truth_freeze.json'),'selection_used_detector':False,'all_R1_designs':details,'no_additional_escalation':True})
    print(json.dumps({'R1_truth_results':details,'R2_units':len(units),'selected_designs':selected}))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--phase',choices=['audit','prepare','R1','select','R2'],required=True)
    args=p.parse_args();out=args.output_dir.resolve()
    if out.parent!=ROOT/'code/outputs/calibration' or not out.name.startswith('p2_task8_'):raise ValueError('Task8 isolated output only')
    if args.phase=='audit':audit_history(out)
    elif args.phase=='prepare':prepare(out)
    elif args.phase=='select':select_round2(out)
    else:execute(out,1 if args.phase=='R1' else 2)

if __name__=='__main__':main()
