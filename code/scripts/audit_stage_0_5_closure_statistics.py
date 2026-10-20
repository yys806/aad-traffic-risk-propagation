"""Predeclared clustered/block uncertainty; no iid-row or equivalence shortcut."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
METRICS=['speed','density','flow','acceleration','gap','closing','low_speed_share','P2_rate']


def freeze(b,candidate):
    if (b/'statistics_plan.json').exists():raise PermissionError('no_statistics_plan_overwrite')
    script=b/'statistics_entry.py';script.write_bytes(Path(__file__).read_bytes())
    entries=[]
    for group in ['us101__0750_0805','us101__0805_0820']:
        src=next(e for e in read(b/'source_manifest.json')['files'] if e['source']==group)
        folder=b/'summary'/group
        entries.append(dict(label=group,kind='real',state_path=src['target'],state_sha256=src['sha256'],
            events_path=(folder/'interior_events.csv').relative_to(b).as_posix(),events_sha256=sha(folder/'interior_events.csv'),
            clusters_path=(folder/'interior_clusters.csv').relative_to(b).as_posix(),clusters_sha256=sha(folder/'interior_clusters.csv'),
            window_s=read(b/'reference_plan.json')['reference_windows_s'][group],lane_km=1.,lanes=5))
    p=dict(version='closure-statistics-v1',script_sha256=sha(script),entries=entries,confidence=.95,resamples=2000,seed=20261020,
        primary_time_block_s=60.,metrics=METRICS,family_size=16,multiplicity='Bonferroni across8 scalars x2 target conditions',
        dependence='Vehicle clusters and nonoverlapping60s blocks reported separately; conservative interval envelope is sensitivity, not proof that unknown cross-block interactions vanish',
        seed_uncertainty='Report separately only after frozen engineering-qualified candidate repeats; insufficient repetitions never silently zero',
        system_error_bound=None,scientific_delta=None,precision_h=None,third_window_access=False)
    write(b/'statistics_plan.json',p);(b/'STATISTICS_PLAN_SHA256').write_text(sha(b/'statistics_plan.json')+'\n')


def bootstrap(num,den,*,fixed_denominator=False,scale=1.):
    import numpy as np
    n=np.asarray(num,float);d=np.asarray(den,float)
    if len(n)!=len(d) or not len(n) or not np.isfinite(np.r_[n,d]).all() or d.sum()<=0:return dict(point=None,ci95=None,simultaneous_ci=None,status='Not Calculated')
    point=float(n.sum()/d.sum()*scale);rng=np.random.default_rng(20261020);values=[]
    for _ in range(2000):
        ix=rng.integers(0,len(n),len(n));D=d.sum() if fixed_denominator else d[ix].sum()
        if D>0:values.append(float(n[ix].sum()/D*scale))
    # A zero numerator is observed, but resampling zero cannot establish a
    # population upper bound. Do not manufacture zero-width rate uncertainty.
    if np.all(n==0):return dict(point=point,ci95=None,simultaneous_ci=None,clusters=len(n),status='Zero numerator; upper uncertainty not identifiable by empirical bootstrap')
    return dict(point=point,ci95=[float(x) for x in np.quantile(values,[.025,.975])],
        simultaneous_ci=[float(x) for x in np.quantile(values,[.05/32,1-.05/32])],clusters=len(n),resamples=len(values),status='Conditional bootstrap sensitivity',
        tail_order_statistics_expected=2000*.05/32,small_tail_Monte_Carlo_precision_limited=True)


def analyse(b,label):
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    from riskprop.stage_0_5_final_closure import real_region_mask
    p=read(b/'statistics_plan.json')
    if sha(b/'statistics_plan.json')!=(b/'STATISTICS_PLAN_SHA256').read_text().strip() or sha(Path(__file__))!=p['script_sha256']:raise PermissionError('statistics_plan_or_source_SHA')
    e=next(e for e in p['entries'] if e['label']==label)
    for k in ['state','events','clusters']:
        if sha(b/e[k+'_path'])!=e[k+'_sha256']:raise PermissionError('statistics_input_SHA')
    cols=['trajectory_id','time_s','frame_id','global_time_ms','lane_id','y_m','speed_mps','acceleration_mps2','net_gap_m','closing_speed_mps',
        'leader_matched','identity_uncertain','leader_identity_uncertain','identity_break','observation_gap','measurement_status','ttc_valid','ttc_s']
    d=pd.read_parquet(b/e['state_path'],columns=cols);lo,hi=e['window_s'];d=d.sort_values(['trajectory_id','time_s']).reset_index(drop=True)
    inside=real_region_mask(d);in_time=d.time_s.ge(lo)&d.time_s.lt(hi);local=inside&in_time
    events=pd.read_csv(b/e['events_path']);clusters=pd.read_csv(b/e['clusters_path']);clusters.trajectory_id=clusters.trajectory_id.astype(str)
    # Crossing uses native adjacent trajectories and global frames, not state
    # row counts or inferred demand. Both positions are on observed mainline.
    prev=d.shift();lane=pd.to_numeric(d.lane_id);prevlane=pd.to_numeric(prev.lane_id)
    cross=d.trajectory_id.eq(prev.trajectory_id)&d.time_s.diff().sub(.1).abs().lt(1e-9)&d.frame_id.diff().eq(1)&d.global_time_ms.diff().eq(100)
    cross &= lane.isin([1,2,3,4,5])&prevlane.isin([1,2,3,4,5])&prev.y_m.lt(300)&d.y_m.ge(300)&prev.time_s.ge(lo-1e-9)&d.time_s.le(hi+1e-9)&~d.identity_break&~d.observation_gap
    physical=d.leader_matched&~d.identity_uncertain&~d.leader_identity_uncertain
    scalars={'speed':(d.speed_mps,local&np.isfinite(d.speed_mps)),
        'acceleration':(d.acceleration_mps2,local&np.isfinite(d.acceleration_mps2)),
        'gap':(d.net_gap_m,local&physical&np.isfinite(d.net_gap_m)&d.net_gap_m.gt(0)),
        'closing':(d.closing_speed_mps,local&physical&np.isfinite(d.closing_speed_mps)&d.net_gap_m.gt(0)),
        'low_speed_share':(d.speed_mps.lt(5).astype(float),local)}
    aggregates={};time_table=pd.DataFrame(index=np.arange(int(np.ceil((hi-lo)/60))))
    blocks=np.floor((d.time_s-lo)/60).astype(int);trajectory=d.trajectory_id.astype(str)
    for name,(values,mask) in scalars.items():
        x=pd.DataFrame(dict(id=trajectory,block=blocks,numerator=np.where(mask,values,0),denominator=mask.astype(int)))
        by_vehicle=x.groupby('id')[['numerator','denominator']].sum();by_block=x[x.block.ge(0)&x.block.lt(len(time_table))].groupby('block')[['numerator','denominator']].sum().reindex(time_table.index,fill_value=0)
        aggregates[name]=dict(vehicle=bootstrap(by_vehicle.numerator,by_vehicle.denominator),time_block=bootstrap(by_block.numerator,by_block.denominator))
        for key in ['numerator','denominator']:time_table[name+'_'+key]=by_block[key]
    # Density, actual plane flow and P2 each have their own denominator.
    raw_vt=local.astype(float)*.1
    vt=raw_vt.groupby(trajectory).sum();flow=cross.astype(float).groupby(trajectory).sum()
    block_vt=raw_vt.groupby(blocks).sum().reindex(time_table.index,fill_value=0)
    # Allocate boundary crossings by their left interval endpoint, matching
    # full-link temporal support; exact upper endpoint belongs to prior block.
    crossing_blocks=np.floor(np.round((d.time_s-.1-lo)/60,6)).astype(int)
    block_q=cross.astype(float).groupby(crossing_blocks).sum().reindex(time_table.index,fill_value=0)
    duration=np.minimum(60.,hi-lo-np.arange(len(time_table))*60)
    aggregates['density']=dict(vehicle=bootstrap(vt,np.full(len(vt),(hi-lo)*e['lane_km']/len(vt)),fixed_denominator=True),
        time_block=bootstrap(block_vt,duration*e['lane_km']))
    aggregates['flow']=dict(vehicle=bootstrap(flow,np.full(len(flow),(hi-lo)*e['lanes']/len(flow)),fixed_denominator=True,scale=3600),
        time_block=bootstrap(block_q,duration*e['lanes'],scale=3600))
    block_events=[];block_E=[]
    # Exposure by 60s blocks was independently emitted by D1 reference analysis.
    blocks_ref=pd.read_csv(b/'summary'/label/'time_blocks.csv')
    for a in blocks_ref.itertuples():block_events.append(a.onset_events);block_E.append(a.evaluable_s)
    aggregates['P2_rate']=dict(vehicle=bootstrap(clusters.onset_events,clusters.evaluable_s,scale=3600),
        time_block=bootstrap(block_events,block_E,scale=3600))
    time_table['duration_s']=duration;time_table['vehicle_s']=block_vt;time_table['actual_crossings']=block_q
    time_table['P2_events']=block_events;time_table['P2_evaluable_s']=block_E
    folder=b/'summary'/label;time_table.to_csv(folder/'statistics_time_blocks.csv',index=False)
    write(folder/'joint_uncertainty.json',dict(source=label,window_s=e['window_s'],metrics=aggregates,confidence=.95,family_size=16,
        system_error_bounds=None,scientific_delta=None,precision_h=None,independent_seed_uncertainty='Not Applicable to single real observation window; cannot identify road population',
        complete_joint_equivalence_test_available=False,known_limits=p['dependence'],zero_event_interval_not_zero_risk=True))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['freeze','analyse']);ap.add_argument('--batch',required=True,type=Path);ap.add_argument('--candidate',type=Path);ap.add_argument('--label');a=ap.parse_args();b=a.batch.resolve()
    if a.command=='freeze':freeze(b,a.candidate)
    else:
        if not sys.flags.no_site:raise PermissionError('python_-S_required')
        sys.path.insert(0,str(b/'runtime/code/src'));from riskprop.stage_0_5_b1_isolation import install_guard
        guard=install_guard(b);os.environ.update(PYTHONPYCACHEPREFIX=str(b/'runtime_cache/pycache'),TEMP=str(b/'runtime_cache/tmp'),TMP=str(b/'runtime_cache/tmp'))
        try:analyse(b,a.label)
        finally:write(b/('statistics_'+a.label+'_access_audit.json'),guard)
        if guard['denied']:raise PermissionError('unexpected_statistics_access')
