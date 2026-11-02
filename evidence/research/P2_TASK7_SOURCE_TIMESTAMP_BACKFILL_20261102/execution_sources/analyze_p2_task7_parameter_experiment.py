"""Task7 offline analysis. Seal complete truth before evaluating any candidate."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
from dataclasses import asdict,dataclass,replace
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from scipy.stats import binom
import p2_task7_measurement as m

LAYERS=('cohort','macro','micro')
DENSITIES=('low','medium','high')
CONDITIONS=('N0','N1','P11','P21','P12','P22','Plocal','A0')
NUMERIC_FLOOR=1e-6  # numerical comparison floor, not a physical measurement certificate

def csv_write(path,rows):
    rows=list(rows)
    if not rows: return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows: w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})

def fast_edie(t,x,lane,window,region=m.REGION,observed=None):
    """Prefix integral at aligned grid endpoints; same clipping as reference oracle."""
    step=float(np.median(np.diff(t)));width=int(round(window/step))
    if abs(width*step-window)>1e-8: raise ValueError('window not aligned to observation grid')
    dt=np.diff(t)[:,None];dx=np.diff(x,axis=0);left,right=region
    moving=dx>1e-10;still=(~moving)&(x[:-1]>=left)&(x[:-1]<right)
    lo=np.zeros_like(dx);hi=np.ones_like(dx)
    np.divide(left-x[:-1],dx,out=lo,where=moving);np.divide(right-x[:-1],dx,out=hi,where=moving)
    fraction=np.where(moving|still,np.maximum(0.,np.minimum(1.,hi)-np.maximum(0.,lo)),0.)
    same=(lane[:-1]==0)&(lane[1:]==0)
    valid=same&(dx>=-1e-8)
    missing=np.zeros_like(valid) if observed is None else ~(observed[:-1]&observed[1:])
    bad=((fraction>0)&same&missing)|((fraction>0)&((lane[:-1]==0)|(lane[1:]==0))&~same)
    fraction=np.where(valid&~missing,fraction,0.)
    ds=(fraction*dx).sum(axis=1);vs=(fraction*dt).sum(axis=1)
    prefix_d=np.r_[0.,np.cumsum(ds)];prefix_v=np.r_[0.,np.cumsum(vs)];prefix_bad=np.r_[0,np.cumsum(bad.any(axis=1))]
    j=np.arange(len(t));k=np.maximum(0,j-width)
    distance=prefix_d[j]-prefix_d[k];vehicle_time=prefix_v[j]-prefix_v[k]
    u=np.full(len(t),np.nan);np.divide(distance,vehicle_time,out=u,where=vehicle_time>0)
    return {'D':distance,'V':vehicle_time,'A':(right-left)*window,'u':u,
            'q':distance/((right-left)*window),'k':vehicle_time/((right-left)*window),
            'complete':(j>=width)&(prefix_bad[j]==prefix_bad[k])}

def fit_baseline(t,y,window,model,train_end=28.):
    use=(t>=train_end-window-1e-9)&(t<train_end-1e-9)
    if not np.isfinite(y[use]).all() or use.sum()<2: return np.full_like(y,np.nan)
    center=t[use].mean();mean=y[use].mean(axis=0)
    if model=='constant': return np.broadcast_to(mean,y.shape).copy()
    slope=np.tensordot(t[use]-center,y[use]-mean,axes=(0,0))/np.sum((t[use]-center)**2)
    return mean+(t-center).reshape((-1,)+(1,)*(y.ndim-1))*slope

def fast_events(t,signal,valid,theta,h,q,inside=None,start=30.,stop=46.):
    """First sustained candidate per entity, never concatenate entity responses."""
    if signal.ndim==1: signal=signal[:,None];valid=valid[:,None]
    if inside is not None: valid=valid&inside
    results=[]
    monitor=(t>=start-1e-9)&(t<=stop+1e-9)
    for entity in range(signal.shape[1]):
        finite=valid[:,entity]&np.isfinite(signal[:,entity])
        idx=np.flatnonzero(monitor&finite&(signal[:,entity]>=theta-1e-10))
        if len(idx)<2: continue
        negatives=np.cumsum(monitor&finite&(signal[:,entity]<theta-1e-10))
        split=np.flatnonzero((np.diff(t[idx])>q+1e-9)|(np.diff(negatives[idx])>0))+1
        for group in np.split(idx,split):
            elapsed=t[group]-t[group[0]];j=int(np.searchsorted(elapsed,h-1e-9))
            if j<len(group):
                first=int(group[0]);confirm=int(group[j])
                results.append({'onset_lower_s':float(t[first-1]) if first else None,
                    'onset_upper_s':float(t[first]),'confirmation_s':float(t[confirm]),
                    'availability_s':float(t[confirm]),'end_s':float(t[group[-1]]),
                    'entity':entity,'gap_bridged':bool(np.any(np.diff(t[group[:j+1]])>np.median(np.diff(t))+1e-8))})
                break
    return sorted(results,key=lambda r:(r['availability_s'],r['onset_upper_s'],r['entity']))

@dataclass(frozen=True)
class Config:
    W:float=9.
    model:str='constant'
    theta:float=.5
    h:float=2.
    q:float=.05
    coverage:float=1.
    recovery:float=0.
    hysteresis:float=0.
    missing:str='bounds'
    w:float=2.
    stride:int=1
    cells:int=1

def config_key(c): return hashlib.sha256(json.dumps(asdict(c),sort_keys=True).encode()).hexdigest()[:12]

def seal(out):
    target=out/'audit/truth_freeze.json'
    if target.exists(): raise FileExistsError('truth already sealed')
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'));rows=[];audits=[];hashes={}
    for unit in manifest['units']:
        uid=unit['unit_id'];a=out/'audit'/f'{uid}.json';p=out/'truth'/f'{uid}.json';raw=out/'raw'/uid/'trajectory.npz'
        audit=json.loads(a.read_text(encoding='utf-8'))
        if audit['status'] not in ('COMPLETE','FAILED_STOP') or m.sha(raw)!=audit['raw_sha256']: raise RuntimeError('unrecorded/corrupt unit '+uid)
        labels=json.loads(p.read_text(encoding='utf-8'))
        if len(labels)!=3 or (audit['status']=='COMPLETE' and not all(x['native_target_verified'] for x in labels)): raise RuntimeError('truth contract '+uid)
        rows.extend(labels);audits.append(audit);hashes[uid]={'truth':m.sha(p),'raw':audit['raw_sha256'],'audit':m.sha(a)}
    if len({a['sumo_seed'] for a in audits})!=576: raise RuntimeError('seed duplicate')
    csv_write(out/'truth/truth_inventory.csv',rows)
    csv_write(out/'audit/run_ledger.csv',[{k:a[k] for k in ['unit_id','dependency_block','density','condition','rep','sumo_seed','split','status','elapsed_s','rows','collisions','teleports','native_target_setters','source_execution','actual_source_onset','raw_sha256']} for a in audits])
    count=Counter((r['measurement_layer'],r['density'],r['condition'],r['state_truth']) for r in rows)
    csv_write(out/'truth/label_counts.csv',[dict(layer=k[0],density=k[1],condition=k[2],state=k[3],n=v) for k,v in sorted(count.items())])
    m.dump(target,{'truth_version':m.TRUTH_VERSION,'units':576,'layer_labels':len(rows),'detector_evaluations_before_freeze':0,
        'freeze_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'manifest_sha256':m.sha(out/'manifest.json'),'truth_inventory_sha256':m.sha(out/'truth/truth_inventory.csv'),
        'hashes':hashes,'independence':'unique traffic realization seed per planned run; same topology/vType conditional domain',
        'formal_A':0,'formal_qualified':0,'real_traffic_truth_error':'Unknown'})
    complete=[a for a in audits if a['status']=='COMPLETE']
    resource={'planned':576,'completed':len(complete),'failed':576-len(complete),
        'median_run_s':float(np.median([a['elapsed_s'] for a in complete])),
        'mean_run_s':float(np.mean([a['elapsed_s'] for a in complete])),
        'max_run_s':max(a['elapsed_s'] for a in complete),'raw_bytes':sum((out/'raw'/a['unit_id']/'trajectory.npz').stat().st_size for a in audits),
        'collisions':sum(a['collisions'] for a in audits),'teleports':sum(a['teleports'] for a in audits),
        'native_target_setters':sum(a['native_target_setters'] for a in audits),'source_onset_width_s':.05}
    m.dump(out/'audit/resource_actual.json',resource);return rows

def candidates(out):
    threshold_data=defaultdict(list);pre_error=[]
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    for unit in manifest['units']:
        if unit['condition'] not in ('N0','N1'): continue
        raw=np.load(out/'raw'/unit['unit_id']/'trajectory.npz');t=raw['t'];v=raw['v'];base=fit_baseline(t,v,9.,'constant')
        post=(t>=30)&(t<=46);signal=(base-v)[:,m.COHORT].mean(axis=1)
        threshold_data['cohort'].append(float(signal[post].max()))
        macro=fast_edie(t,raw['x'],raw['lane'],2.);b=fit_baseline(t,macro['u'],9.,'constant')
        threshold_data['macro'].append(float((b-macro['u'])[post].max()))
        inside=(raw['lane']==0)&(raw['x']>=m.REGION[0])&(raw['x']<m.REGION[1]);inside[:,0]=False
        threshold_data['micro'].append(float(np.max(np.where(inside,base-v,-np.inf)[post])))
        for W in [4.5,9.,13.5]:
            for model in ['constant','linear']:
                pred=fit_baseline(t,v[:,m.COHORT],W,model);test=(t>=28)&(t<30)
                pre_error.append({'unit_id':unit['unit_id'],'density':unit['density'],'condition':unit['condition'],
                    'W':W,'model':model,'RMSE_mps':float(np.sqrt(np.mean((pred[test]-v[test][:,m.COHORT])**2)))})
    configs={};tags={};grids={};refs={}
    interactions={}
    for layer in LAYERS:
        theta=sorted(set([max(NUMERIC_FLOOR,float(np.quantile(threshold_data[layer],q))) for q in [.9,.95,.99]]+[.25,.5,1.]))
        grids[layer]={'W':[4.5,9.,13.5],'model':['constant','linear'],'theta':theta,'h':[1.,2.,4.],
            'q':[.05],'coverage':[.6,.8,.9,.95,1.],'recovery':[0.,2.],
            'hysteresis':[0.,NUMERIC_FLOOR],'missing':['bounds','unknown'],
            'w':[1.,2.,4.],'stride':[1,2,4],'cells':[1,2,4]}
        ref=Config(theta=theta[len(theta)//2]);refs[layer]=asdict(ref);configs[layer]={};tags[layer]={}
        def add(c,tag):
            key=config_key(c);configs[layer][key]=asdict(c);tags[layer].setdefault(key,[]).append(tag);return key
        add(ref,'reference')
        variables=['W','model','theta','h','q','coverage','recovery','hysteresis','missing']
        if layer=='macro':variables+=['w','stride','cells']
        if layer=='micro':variables=['W','model','theta','h','q','stride']
        for variable in variables:
            for value in grids[layer][variable]:add(replace(ref,**{variable:value}),'single:'+variable)
        pairs=[('W','model'),('theta','h'),('h','q'),('recovery','hysteresis')]
        if layer=='macro':pairs +=[('w','theta'),('cells','stride')]
        for a,b in pairs:
            av=[grids[layer][a][0],grids[layer][a][-1]];bv=[grids[layer][b][0],grids[layer][b][-1]]
            keys=[add(replace(ref,**{a:x,b:y}),'interaction:'+a+'x'+b) for x in av for y in bv]
            interactions[layer+':'+a+'x'+b]=keys
    plan={'algorithm_version':'P2T7-offline-v1','truth_freeze_sha256':m.sha(out/'audit/truth_freeze.json'),
        'script_sha256':m.sha(Path(__file__)),'source_detector_sha256':m.sha(Path(m.__file__)),
        'numeric_grid_floor_mps':NUMERIC_FLOOR,'numeric_floor_is_not_real_sensor_error':True,
        'raw_observation':'complete simulator full state; sensor stress is separate',
        'reference':refs,'grids':grids,'configs':configs,'tags':tags,'interactions':interactions,
        'truth_a_b_d':[1.,1.,4.],'stability_epsilon':None,'important_interaction_gamma':None,
        'stability_status':'Unknown; no researcher-frozen scientific equivalence margin',
        'selection':'descriptive calibration screen only; no independent validation yet'}
    m.dump(out/'detector/candidate_manifest.json',plan);csv_write(out/'detector/pre_baseline_predictions.csv',pre_error)
    return plan

def observation(raw,stress,seed):
    t=raw['t'];v=raw['v'].copy();observed=np.ones_like(v,bool);identity=np.ones_like(v,bool)
    post=(t>=30)&(t<=46);rng=np.random.default_rng(np.random.SeedSequence([seed,7717]))
    kind=stress.get('kind','none');amount=stress.get('amount',0.)
    if kind=='MCAR':observed[post]=rng.random(observed[post].shape)>=amount
    elif kind=='block':
        for i in range(v.shape[1]):
            begin=30+rng.uniform(0,max(.01,16-16*amount));observed[:,i]&=~((t>=begin)&(t<begin+16*amount))
    elif kind=='MNAR':
        for j in np.flatnonzero(post):
            selected=np.argsort(v[j])[:max(1,int(round(amount*v.shape[1])))];observed[j,selected]=False
    elif kind=='identity':
        identity[(t>=36)&(t<40),m.COHORT[0]]=False;observed &= identity
    elif kind=='noise':v += rng.uniform(-amount,amount,v.shape)
    elif kind=='quantization':v=np.round(v/amount)*amount
    return v,observed,identity

def evaluate(raw,label,c,stress=None,seed=0,cache=None):
    if len(raw['t'])==0:
        return {'alarm':None,'valid_detection':False,'timely':False,'early_alarm':False,'false_positive':False,
            'pre_alarm':None,'unknown':True,'coverage':0.,'delay_lower_s':None,'delay_upper_s':None,'event_count':None,
            'first_onset_s':None,'confirmation_s':None,'availability_s':None,'first_end_s':None,'source_claim':None,
            'false_attribution':False,'qualified_status':'Unknown_no_observations','qualified_recall':None,
            'truth_positive':False,'truth_negative':False,'truth_unknown':True,'truth_onset':None,
            'source_attribution_truth':'unknown','unknown_reason':'preserved TraCI startup failure; no seed replacement'}
    stress=stress or {'kind':'none'};key=(c.W,c.model,c.w,c.stride,c.cells,stress.get('kind'),stress.get('amount'))
    if cache is None:cache={}
    if key not in cache:
        v,seen,identity=observation(raw,stress,seed);idx=np.arange(0,len(raw['t']),c.stride)
        t=raw['t'][idx];v=v[idx];seen=seen[idx];identity=identity[idx];x=raw['x'][idx];lane=raw['lane'][idx]
        base=fit_baseline(t,v,c.W,c.model);inside=(x>=m.REGION[0])&(x<m.REGION[1])&(lane==0)
        member_seen=seen[:,m.COHORT]&inside[:,m.COHORT]&identity[:,m.COHORT]
        values=(base-v)[:,m.COHORT];coverage=member_seen.mean(axis=1)
        lower=np.where(member_seen,values,base[:,m.COHORT]-10).mean(axis=1)
        upper=np.where(member_seen,values,base[:,m.COHORT]).mean(axis=1)
        mac=fast_edie(t,x,lane,c.w,observed=seen)
        if c.cells>1:
            L=m.REGION[1]-m.REGION[0]
            parts=[fast_edie(t,x,lane,c.w,(m.REGION[0]+j*L/c.cells,m.REGION[0]+(j+1)*L/c.cells),seen) for j in range(c.cells)]
            mac['D']=sum(p['D'] for p in parts);mac['V']=sum(p['V'] for p in parts)
            mac['u']=np.divide(mac['D'],mac['V'],out=np.full(len(t),np.nan),where=mac['V']>0)
            mac['complete']=np.logical_and.reduce([p['complete'] for p in parts])
        if stress.get('kind')=='noise':
            rng=np.random.default_rng([seed,4421]);mu=mac['u']+rng.uniform(-stress['amount'],stress['amount'],len(t))
        elif stress.get('kind')=='quantization':mu=np.round(mac['u']/stress['amount'])*stress['amount']
        else:mu=mac['u']
        mb=fit_baseline(t,mu,c.W,c.model)
        micro=(base-v);inside[:,0]=False
        cache[key]=(t,coverage,lower,upper,member_seen,mb-mu,mac,micro,seen&identity,inside)
    t,cov,lo,hi,member_seen,macro,mac,micro,seen,inside=cache[key];layer=label['measurement_layer']
    monitor=(t>=30)&(t<=46);pre=(t>=28)&(t<30)
    if layer=='cohort':
        full=member_seen.all(axis=1);valid=(cov>=c.coverage-1e-9)&np.isfinite(lo)
        if c.missing=='unknown':valid &= full
        ambiguous=(lo<c.theta)&(hi>=c.theta)&~full
        unknown=bool(np.any((~valid|ambiguous)[monitor]))
        events=m.segments(t,lo,valid,c.theta,c.h,c.q,stop=50.,exit_delta=c.hysteresis,recovery=c.recovery)
        events=[e for e in events if e['onset_upper_s']<=46+1e-9]
        pre_alarm=bool(fast_events(t,lo,valid,c.theta,c.h,c.q,start=28.,stop=29.95)) if c.h<=1.9 else None
        coverage=float(cov[monitor].mean())
    elif layer=='macro':
        valid=mac['complete']&np.isfinite(macro);unknown=bool(np.any(~valid[monitor]))
        events=m.segments(t,macro,valid,c.theta,c.h,c.q,stop=50.,exit_delta=c.hysteresis,recovery=c.recovery)
        events=[e for e in events if e['onset_upper_s']<=46+1e-9]
        pre_alarm=bool(fast_events(t,macro,valid,c.theta,c.h,c.q,start=28.,stop=29.95)) if c.h<=1.9 else None;coverage=float(valid[monitor].mean())
    else:
        events=fast_events(t,micro,seen,c.theta,c.h,c.q,inside=inside,stop=50.)
        events=[e for e in events if e['onset_upper_s']<=46+1e-9]
        quality=seen[:,1:-1].all(axis=1);unknown=bool(np.any(~quality[monitor]));coverage=float(quality[monitor].mean())
        pre_alarm=bool(fast_events(t,micro,seen,c.theta,c.h,c.q,inside=inside,start=28.,stop=29.95)) if c.h<=1.9 else None
    unknown=unknown or bool(np.any(np.diff(t[monitor])>c.q+1e-8))
    event=events[0] if events else None;positive=label['state_truth']=='positive';negative=label['state_truth']=='negative'
    valid_detection=False;early=False;delay_lo=delay_hi=None
    if event and positive:
        L,U=label['onset_allowed_set'];early=event['onset_upper_s']<L-1e-8
        recovery=label['recovery_interval_s'];end=recovery[1] if recovery else 46.
        valid_detection=not early and event['availability_s']<=end+1e-8
        delay_lo=event['availability_s']-U;delay_hi=event['availability_s']-L
    timely=bool(valid_detection and delay_hi<=m.D_STAR+1e-8)
    # Source attribution is never manufactured from a state alarm or shortest path.
    qualified_unknown=layer=='micro' and label['condition'] not in ('N0','N1','A0')
    return {'alarm':bool(event),'valid_detection':valid_detection,'timely':timely,'early_alarm':early,
        'false_positive':bool(negative and event),'pre_alarm':pre_alarm,
        'unknown':bool(unknown or label['state_truth']=='unknown'),'coverage':coverage,
        'delay_lower_s':delay_lo,'delay_upper_s':delay_hi,'event_count':len(events),
        'first_onset_s':event['onset_upper_s'] if event else None,
        'confirmation_s':event['confirmation_s'] if event else None,
        'availability_s':event['availability_s'] if event else None,
        'first_end_s':event['end_s'] if event else None,
        'source_claim':False,'false_attribution':False,
        'qualified_status':'Unknown_W8' if qualified_unknown else 'Not_Qualified',
        'qualified_recall':None,'truth_positive':positive,'truth_negative':negative,'truth_unknown':label['state_truth']=='unknown',
        'truth_onset':label['onset_allowed_set'],'source_attribution_truth':label['source_attribution']}

def summarize(rows):
    n=len(rows);p=[r for r in rows if r['truth_positive']];neg=[r for r in rows if r['truth_negative']]
    y=sum(r['timely'] for r in p);fp=sum(r['false_positive'] for r in neg);u=sum(r['unknown'] for r in rows)
    truth_unknown=sum(r.get('truth_unknown',False) for r in rows)
    known_attr=[r for r in rows if r['source_attribution_truth'] in ('none','other')] if rows and rows[0].get('layer')=='micro' else []
    far=sum(r['false_attribution'] for r in known_attr)
    return {'attempts':n,'positive_n':len(p),'negative_n':len(neg),'timely_n':y,
        'timely_rate':y/len(p) if p else None,'truth_unknown_n':truth_unknown,
        'timely_rate_worst_case':y/(len(p)+truth_unknown) if len(p)+truth_unknown else None,'valid_n':sum(r['valid_detection'] for r in p),
        'miss_n':len(p)-y,'false_positive_n':fp,'FPR':fp/len(neg) if neg else None,
        'unknown_n':u,'unknown_rate':u/n if n else None,'early_alarm_n':sum(r['early_alarm'] for r in rows),
        'pre_alarm_n':sum(bool(r['pre_alarm']) for r in rows),'pre_alarm_denominator':sum(r['pre_alarm'] is not None for r in rows),
        'coverage_mean':sum(r['coverage'] for r in rows)/n if n else None,
        'FAR_n':far,'FAR_denominator':len(known_attr),'FAR':far/len(known_attr) if known_attr else None,
        'delay_median_upper_s':float(np.median([r['delay_upper_s'] for r in p if r['valid_detection']])) if any(r['valid_detection'] for r in p) else None}

def reaction_audit(raw,audit):
    t=raw['t'];v=raw['v'];windows={0:audit['actual_source_onset'] if audit['actuated_source']=='s0' else None};edges=[]
    for i in range(1,v.shape[1]-1):
        events=fast_events(t,10-v[:,i],np.ones(len(t),bool),1.,1.,.05)
        windows[i]=[events[0]['onset_lower_s'],events[0]['onset_upper_s']] if events else None
    for i in range(1,v.shape[1]-1):
        parent=windows.get(i-1);child=windows.get(i)
        for error in [0.,.05,.2]:
            ordered=bool(parent and child and parent[1]+error<child[0]-error)
            edges.append({'unit_id':audit['unit_id'],'density':audit['density'],'condition':audit['condition'],
                'source_entity':i-1,'target_entity':i,'clock_error_each_s':error,'parent_interval':parent,'child_interval':child,
                'W6_strict_order':ordered,'reaction_lower_s':child[0]-parent[1] if parent and child else None,
                'reaction_upper_s':child[1]-parent[0] if parent and child else None,'W8':'Unknown',
                'qualified':False,'reason':'state/relationship evidence does not certify competing-cause exclusion'})
    return edges

def analyze(out):
    if not (out/'audit/truth_freeze.json').exists(): raise RuntimeError('truth not frozen')
    if (out/'detector/candidate_manifest.json').exists(): raise FileExistsError('candidate evaluation already started; do not silently rerun')
    plan=candidates(out);manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    allrows=[];stressrows=[];reaction=[];checks=[];start=time.monotonic()
    stresses=[{'kind':'none','amount':0.}]+[{'kind':k,'amount':a} for k in ['MCAR','block','MNAR'] for a in [.05,.2]]
    stresses +=[{'kind':'noise','amount':a} for a in [NUMERIC_FLOOR,2*NUMERIC_FLOOR,.05,.1]]
    stresses +=[{'kind':'quantization','amount':a} for a in [.1,.2]]+[{'kind':'identity','amount':1.}]
    interaction_specs=[]
    for unit in manifest['units']:
        uid=unit['unit_id'];raw=dict(np.load(out/'raw'/uid/'trajectory.npz'));labels=json.loads((out/'truth'/f'{uid}.json').read_text(encoding='utf-8'))
        audit=json.loads((out/'audit'/f'{uid}.json').read_text(encoding='utf-8'));cache={}
        for label in labels:
            layer=label['measurement_layer']
            for cid,config in plan['configs'][layer].items():
                result=evaluate(raw,label,Config(**config),seed=unit['sumo_seed'],cache=cache)
                allrows.append({'unit_id':uid,'dependency_block':uid,'density':unit['density'],'condition':unit['condition'],
                    'layer':layer,'config_id':cid,'stress':'none',**result})
            ref=Config(**plan['reference'][layer])
            for stress in stresses:
                # Cross coverage x missingness; no complete-case survivor mean.
                coverages=[1.,.8] if stress['kind'] in ('MCAR','block','MNAR') and layer=='cohort' else [ref.coverage]
                for coverage in coverages:
                    c=replace(ref,coverage=coverage);result=evaluate(raw,label,c,stress=stress,seed=unit['sumo_seed'],cache=cache)
                    stressrows.append({'unit_id':uid,'dependency_block':uid,'density':unit['density'],'condition':unit['condition'],
                        'layer':layer,'stress':stress['kind'],'amount':stress['amount'],'coverage_gate':coverage,**result})
            if layer=='cohort':
                # Identity x missingness with shared raw and exact dependency key.
                for identity in [False,True]:
                    for missing in [0.,.2]:
                        changed={k:v.copy() for k,v in raw.items()}
                        stress={'kind':'MCAR','amount':missing}
                        if identity:
                            jj=(changed['t']>=36)&(changed['t']<40);changed['v'][jj,m.COHORT[0]]=np.nan
                        result=evaluate(changed,label,ref,stress=stress,seed=unit['sumo_seed'],cache={})
                        stressrows.append({'unit_id':uid,'dependency_block':uid,'density':unit['density'],'condition':unit['condition'],
                            'layer':layer,'stress':'identity_x_missing','amount':missing,'coverage_gate':ref.coverage,
                            'identity_break':identity,**result})
        if len(raw['t']) and unit['rep'] in (0,23):
            reaction.extend(reaction_audit(raw,audit))
            for w in [1.,2.,4.]:
                fast=fast_edie(raw['t'],raw['x'],raw['lane'],w);slow=m.edie(raw['t'],raw['x'],raw['lane'],w)
                error=max(float(np.max(np.abs(fast[k]-slow[k]))) for k in ['D','V'])
                parts=[fast_edie(raw['t'],raw['x'],raw['lane'],w,(m.REGION[0]+j*(m.REGION[1]-m.REGION[0])/4,m.REGION[0]+(j+1)*(m.REGION[1]-m.REGION[0])/4)) for j in range(4)]
                split_error=max(float(np.max(np.abs(sum(p[k] for p in parts)-fast[k]))) for k in ['D','V'])
                checks.append({'unit_id':uid,'w':w,'fast_reference_max_abs_error':error,'partition_max_abs_error':split_error,
                               'q_ku_max_error':float(np.nanmax(np.abs(fast['q']-fast['k']*fast['u'])))})
                if error>1e-6 or split_error>1e-6: raise RuntimeError('Edie integration discrepancy')
        if (len(allrows)//sum(len(v) for v in plan['configs'].values()))%48==0:
            print(json.dumps({'analyzed_unit':uid,'evaluations':len(allrows),'elapsed_s':time.monotonic()-start}),flush=True)
    csv_write(out/'detector/parameter_evaluations.csv',allrows);csv_write(out/'detector/robustness_evaluations.csv',stressrows)
    csv_write(out/'detector/reaction_clock_evidence.csv',reaction);csv_write(out/'audit/edie_crosschecks.csv',checks)
    groups=defaultdict(list)
    for r in allrows: groups[(r['layer'],r['density'],r['condition'],r['config_id'])].append(r)
    summaries=[]
    for (layer,density,condition,cid),rows in groups.items():
        stats=summarize(rows);stats.update({'layer':layer,'density':density,'condition':condition,'config_id':cid,
            'FPR_upper_pointwise_95':m.cp_upper(stats['false_positive_n'],stats['negative_n']),
            'timely_lower_pointwise_95':m.cp_lower(stats['timely_n'],stats['positive_n']),
            'unknown_upper_pointwise_95':m.cp_upper(stats['unknown_n'],stats['attempts']),
            'CI_scope':'calibration descriptive; no simultaneous acceptance certificate'})
        summaries.append(stats)
    csv_write(out/'detector/parameter_curves.csv',summaries)
    sg=defaultdict(list)
    for r in stressrows:sg[(r['layer'],r['density'],r['condition'],r['stress'],r['amount'],r['coverage_gate'],r.get('identity_break'))].append(r)
    csv_write(out/'detector/robustness_summary.csv',[{'layer':key[0],'density':key[1],'condition':key[2],'stress':key[3],
        'amount':key[4],'coverage_gate':key[5],'identity_break':key[6],**summarize(rows)} for key,rows in sg.items()])
    interaction=[];lookup={(r['unit_id'],r['layer'],r['config_id']):r for r in allrows}
    for name,keys in plan['interactions'].items():
        layer=name.split(':')[0]
        for density in DENSITIES:
            for condition in CONDITIONS:
                values=[]
                for u in manifest['units']:
                    if u['density']!=density or u['condition']!=condition:continue
                    rr=[lookup[(u['unit_id'],layer,k)] for k in keys]
                    loss=[int(r['timely']) if r['truth_positive'] else 1-int(r['false_positive'] or r['unknown']) for r in rr]
                    values.append(loss[3]-loss[2]-loss[1]+loss[0])
                K=len(plan['interactions'])*3*8;radius=4*math.sqrt(math.log(2*K/.05)/(2*len(values)))
                interaction.append({'interaction':name,'density':density,'condition':condition,'independent_blocks':len(values),
                    'mean_D':float(np.mean(values)),'simultaneous_radius':radius,'lower':max(-2.,float(np.mean(values))-radius),
                    'upper':min(2.,float(np.mean(values))+radius),'gamma_int':None,'stability':'Unknown; no equivalence margin and broad simultaneous interval'})
    csv_write(out/'detector/interaction_summary.csv',interaction)
    # Density x threshold is descriptive effect heterogeneity, not paired iid evidence.
    csv_write(out/'detector/density_threshold.csv',[s for s in summaries if 'single:theta' in plan['tags'][s['layer']][s['config_id']]])
    selected={};screen=[]
    for layer in LAYERS:
        choices=[]
        for cid,config in plan['configs'][layer].items():
            rows=[r for r in allrows if r['layer']==layer and r['config_id']==cid]
            stats=summarize(rows);score=stats['timely_rate'] if stats['timely_rate'] is not None else -1.
            unknown_penalty=stats['unknown_rate'];false_penalty=stats['FPR'] or 0.
            choices.append((score-unknown_penalty-false_penalty,-config['h'],-config['W'],cid,stats))
            screen.append({'layer':layer,'config_id':cid,**config,**stats,'status':'Calibration screen; not Recommended-for-freeze'})
        best=max(choices);selected[layer]={'config_id':best[3],'parameters':plan['configs'][layer][best[3]],
            'descriptive_metrics':best[4],'status':'Not established; independent V and scientific stability margin absent'}
    csv_write(out/'detector/calibration_screen.csv',screen);m.dump(out/'detector/calibration_selection.json',selected)
    # Recompute stresses for the selected vector; reference stress alone cannot certify selection.
    chosen_stress=[]
    for unit in manifest['units']:
        raw=dict(np.load(out/'raw'/unit['unit_id']/'trajectory.npz'));labels=json.loads((out/'truth'/f'{unit['unit_id']}.json').read_text(encoding='utf-8'));cache={}
        for label in labels:
            layer=label['measurement_layer'];c=Config(**selected[layer]['parameters'])
            for stress in stresses:
                chosen_stress.append({'unit_id':unit['unit_id'],'density':unit['density'],'condition':unit['condition'],
                    'layer':layer,'stress':stress['kind'],'amount':stress['amount'],
                    **evaluate(raw,label,c,stress=stress,seed=unit['sumo_seed'],cache=cache)})
    csv_write(out/'detector/selected_robustness_evaluations.csv',chosen_stress)
    m.dump(out/'audit/analysis_completion.json',{'parameter_evaluations':len(allrows),'reference_stress_evaluations':len(stressrows),
        'selected_stress_evaluations':len(chosen_stress),'interactions':len(interaction),'edie_checks':len(checks),
        'selected':selected,'elapsed_s':time.monotonic()-start,'independent_V_runs':0,'formal_A':0,'formal_qualified':0})
    return selected

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--phase',choices=['seal','analyze'],required=True);a=p.parse_args();out=a.output_dir.resolve()
    if out.parent!=Path(__file__).resolve().parents[2]/'code/outputs/calibration' or not out.name.startswith('p2_task7_'):raise ValueError('isolated Task7 only')
    if a.phase=='seal':seal(out);print('truth frozen: 576 runs / 1728 layer labels')
    else:analyze(out);print('analysis complete')

if __name__=='__main__':main()
