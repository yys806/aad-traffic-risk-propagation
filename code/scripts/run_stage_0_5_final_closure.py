"""Independent final-closure capsule, approved two-source reference and finite runs."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
RESULT='RES-STAGE-0.5-FINAL-CLOSURE-V1'
GROUPS=['us101__0750_0805','us101__0805_0820']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def prepare(repo,b):
    if b.exists() or (repo/'evidence/results'/RESULT).exists():raise PermissionError('new_result_required')
    for n in ['inputs','summary','runs','runtime/code/src/riskprop','runtime/code/tests','runtime/code/scripts','runtime_cache/tmp','dependency_links']:(b/n).mkdir(parents=True,exist_ok=True)
    old=repo/'code/outputs/formal/calibration/stage_0_5_local_following_v1';p=read(old/'experiment_plan.json')
    for n,digest in p['frozen_files'].items():
        if n.startswith('official_source/') or (n.startswith('runtime/code/src/') and n.endswith('.py')):
            if sha(old/n)!=digest:raise PermissionError('old_runtime_SHA')
            target=b/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
    policy=read(old/'isolation_policy.json');policy['real_inputs']='Only two separately SHA-bound canonical calibration state files; no full-source event table'
    write(b/'isolation_policy.json',policy)
    import _winapi
    for link in (old/'dependency_links').iterdir():_winapi.CreateJunction(str(link.resolve()),str(b/'dependency_links'/link.name))
    source=read(repo/'evidence/results/RES-STAGE-0.5-CALIBRATION-READINESS-V1/calibration_source_analysis.json')
    entries=[]
    for e in source['state_reads']:
        if e.get('source') in GROUPS:entries.append(dict(source=e['source'],path=e['path'],target='inputs/'+e['source']+'.parquet',sha256=e['sha256'],role='calibration_state'))
    for result,names in [
        ('RES-STAGE-0.5-CALIBRATION-GAPS-V1',['diagnostics.json','unified_strata.json']),
        ('RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1',['real_reference_summary.json']),
        ('RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1',['issue_discovery_report.json','researcher_decision_matrix.json'])]:
        folder=repo/'evidence/results'/result;m=read(folder/'manifest.json')
        for n in names:entries.append(dict(source=result,path=(folder/n).relative_to(repo).as_posix(),target='inputs/'+n,sha256=next(x['sha256'] for x in m['files'] if x['path']==n),role='sealed_metadata'))
    if len([e for e in entries if e['role']=='calibration_state'])!=2:raise PermissionError('two_sources_required')
    write(b/'source_manifest.json',dict(result_id=RESULT,declared_before_read=True,files=entries,third_window_access=False,full_source_event_access=False,holdout_access=False))
    for e in entries:
        if sha(repo/e['path'])!=e['sha256']:raise PermissionError('source_SHA')
        shutil.copyfile(repo/e['path'],b/e['target'])
    refresh(repo,b)
    write(b/'preparation.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
        old_results_tree=subprocess.check_output(['git','rev-parse','HEAD:evidence/results'],cwd=repo,text=True).strip(),
        previous_targeted_used=3,targeted_remaining=5,micro_remaining=0,SUMO_binary_sha256=sha(Path(policy['executables'][1]))))


def refresh(repo,b):
    if (b/'REFERENCE_PLAN_SHA256').exists() or (b/'PLAN_SHA256').exists():raise PermissionError('frozen_runtime')
    todo=['stage_0_5_final_closure','stage_0_5_calibration_readiness','stage_0_5_lf_worker','stage_0_5_local_following','stage_0_5_lf_protocol'];done=set()
    while todo:
        name=todo.pop()
        if name in done:continue
        p=repo/'code/src/riskprop'/(name+'.py');raw=p.read_text(encoding='utf-8')
        shutil.copyfile(p,b/'runtime/code/src/riskprop'/p.name);done.add(name)
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node,ast.ImportFrom):
                module=node.module or ''
                child=module if node.level==1 else module.removeprefix('riskprop.') if module.startswith('riskprop.') else None
                if child and (repo/'code/src/riskprop'/(child+'.py')).is_file():todo.append(child)
    for n in ['test_stage_0_5_final_closure.py','test_stage_0_5_lf_protocol.py','test_stage_0_5_lf_transport.py','test_stage_0_5_lf_guards.py']:
        shutil.copyfile(repo/'code/tests'/n,b/'runtime/code/tests'/n)
    (b/'runtime/code/pytest.ini').write_text('[pytest]\npythonpath=src\n',encoding='utf-8')
    shutil.copyfile(Path(__file__),b/'closure_entry.py')


def freeze_reference(b):
    if (b/'REFERENCE_PLAN_SHA256').exists():raise PermissionError('no_overwrite')
    tested=read(b/'test_pass.json')
    if not tested['passed'] or any(sha(b/n)!=d for n,d in tested['code_sha256'].items()):raise PermissionError('untested_runtime')
    p=dict(result_id=RESULT,mode='Approved D1 real local reference re-extraction',groups=GROUPS,
        real_region=dict(lanes=[1,2,3,4,5],start_m=150,end_m=350,lane_km=1),
        reference_windows_s={GROUPS[0]:[120.,840.],GROUPS[1]:[180.,840.]},
        window_basis='Pre-existing A+ complete 60s interior blocks, guard by maximum observed trajectory duration; empirical guard not proof of census. Full acquisition sensitivity separately retained. Fixed before new event extraction.',
        event_config=dict(ttc_s=2.,minimum_span_s=.2,recorded_step_s=.1,exact_numerical_tolerance_m=1e-6),
        attribution='D1 onset position and time; confirmation/through_confirmation spatial auxiliary share onset window',
        uncertainty=dict(level=.95,statistical_seed=20261020,resamples=2000,time_block_s=60,
            family_metrics=['speed','density','flow','acceleration','gap','closing','low_speed_share','P2_rate'],family_conditions=2,
            multiplicity='Bonferroni across16 scalar condition-metric decisions; retain vehicle-cluster and60s-block marginal sensitivity separately. No row-iid CI. Small independent-seed intervals must be reported separately; no complete uncertainty claimed from one source.',
            system_error_bounds=None,scientific_delta=None,precision_h=None),
        offline_limits=dict(wall_s=900,memory_bytes=3*1024**3,artifact_bytes=2*1024**3),
        third_window_access=False,full_event_table_access=False,ABCD_allowed=False,
        processing=dict(complete_follower_trajectories_per_partition=96,no_trajectory_split=True,
            arrow_source_columns=True,reason='Bound original core copies below unchanged3GiB; source SHA and full per-follower sequence preserved'),
        frozen_files={p.relative_to(b).as_posix():sha(p) for folder in ['runtime','inputs','official_source'] for p in (b/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts})
    for n in ['source_manifest.json','isolation_policy.json','closure_entry.py','preparation.json']:p['frozen_files'][n]=sha(b/n)
    write(b/'reference_plan.json',p);(b/'REFERENCE_PLAN_SHA256').write_text(sha(b/'reference_plan.json')+'\n')


def validate_reference(b):
    p=read(b/'reference_plan.json')
    if sha(b/'reference_plan.json')!=(b/'REFERENCE_PLAN_SHA256').read_text().strip():raise PermissionError('reference_plan_SHA')
    for n,d in p['frozen_files'].items():
        path=(b/n).resolve()
        if not path.is_relative_to(b) or sha(path)!=d:raise PermissionError('frozen_SHA:'+n)
    return p


def reference(b,group):
    import gc
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    import pyarrow as pa
    import pyarrow.compute as pc
    from riskprop.stage_0_5_sumo import CalibrationValidationGuard
    from riskprop.stage_0_5_final_closure import local_p2,checked,links,real_region_mask
    from riskprop.stage_0_5_calibration_readiness import edge_exposure_audit
    p=validate_reference(b)
    if group not in GROUPS:raise PermissionError('source_role')
    e=next(x for x in read(b/'source_manifest.json')['files'] if x['source']==group)
    guard=CalibrationValidationGuard(log_path=b/(group+'_source_access.json'))
    path=b/e['target'];guard.require_source_read(path,role='calibration',source=group,purpose='Approved D1 full-context local re-extraction')
    columns=pq.read_schema(path).names
    write(b/(group+'_schema.json'),dict(columns=columns,source_sha256=sha(path)))
    # Keep the exact original full source, but only fields required for formal
    # measurement and the five-layer descriptive/uncertainty audit.
    required=['dataset','site','window_id','source_member','source_period','trajectory_id','leader_trajectory_id','vehicle_id','leader_id',
        'original_row_number','diagnostic_clock_anchor_ms','global_time_ms','frame_id','time_s','identity_uncertain','leader_identity_uncertain',
        'identity_break','observation_gap','leader_matched','measurement_status','ttc_valid','ttc_s','drac_mps2','lane_id','y_m','speed_mps','acceleration_mps2',
        'net_gap_m','closing_speed_mps','leader_frame_id','missing_reason']
    table=pq.read_table(path,columns=[c for c in required if c in columns])
    if set(table.column('window_id').unique().to_pylist())!={group.removeprefix('us101__')}:raise PermissionError('materialised_scope_mismatch')
    ids=table.column('trajectory_id').unique().to_pylist();seen=set();parts={'interior':[],'full_acquisition':[]};local_rows=[];eligible_times=[]
    time_grid=np.sort(np.asarray(table.column('time_s').unique().to_pylist(),float));interior=p['reference_windows_s'][group]
    windows=dict(interior=interior,full_acquisition=[float(time_grid.min()),float(time_grid.max())])
    out=b/'summary'/group;out.mkdir(exist_ok=False)
    for offset in range(0,len(ids),96):
        subset=ids[offset:offset+96]
        if seen.intersection(subset):raise ValueError('trajectory_split')
        seen.update(subset)
        d=table.filter(pc.is_in(table.column('trajectory_id'),value_set=pa.array(subset,type=table.schema.field('trajectory_id').type))).to_pandas()
        d['_inside']=real_region_mask(d);d['_position']=d.y_m
        expected=edge_exposure_audit(d)['p2_evaluable_following_exposure_s']
        for label,w in windows.items():
            a=local_p2(d,w)
            if abs(a['exposure']['global_evaluable_s']-expected)>1e-7:raise ValueError('original_exposure_disagreement')
            parts[label].append(a)
        loc=d[d._inside&d.time_s.ge(interior[0])&d.time_s.lt(interior[1])]
        local_rows.append(loc[['time_s','trajectory_id','speed_mps','acceleration_mps2','net_gap_m','closing_speed_mps','ttc_s','measurement_status','_inside']].copy())
        o=checked(d);ll=links(o,interior);eligible_times.extend(o.loc[ll.local,'time_s'].tolist())
        del d,o,ll,loc;gc.collect()
        print(group+' partition '+str(offset)+'/'+str(len(ids)),flush=True)
    if set(ids)!=seen:raise ValueError('partition_coverage')
    for label,w in windows.items():
        values=parts[label];a={k:values[0][k] for k in ['version','policy_status','window_s','reality_coverage_accepted']}
        for key in ['counts','point_counts']:a[key]={k:sum(x[key][k] for x in values) for k in values[0][key]}
        a['exposure']={k:sum(x['exposure'][k] for x in values) for k in values[0]['exposure'] if k!='original_current_incoming_break_semantics'}
        a['exposure']['original_current_incoming_break_semantics']=True
        for k in ['full_source_confirmed_events','rejected_formal_candidates','right_censored_unconfirmed_candidates','confirmation_time_sensitivity']:a[k]=sum(x[k] for x in values)
        a['censored_candidates']=[r for x in values for r in x['censored_candidates']]
        rows=[r for x in values for r in x['events']]
        if len({r['event_id'] for r in rows})!=len(rows):raise ValueError('duplicated_partition_event')
        pd.DataFrame(rows).to_csv(out/(label+'_events.csv'),index=False)
        cE={k:v for x in values for k,v in x['cluster_evaluable_s'].items()};cN={k:v for x in values for k,v in x['cluster_events'].items()}
        E=a['exposure']['local_evaluable_s'];a['formal_local_rate_per_evaluable_vehicle_hour']=3600*a['counts']['onset']/E if E else None
        if E<=0 or not cE:raise ValueError('known_reference_local_scope_empty')
        a['rates']={k:3600*n/E if E else None for k,n in a['counts'].items()}
        clusters=sorted(set(cE)|set(cN));pd.DataFrame([dict(trajectory_id=k,evaluable_s=cE.get(k,0),onset_events=cN.get(k,0)) for k in clusters]).to_csv(out/(label+'_clusters.csv'),index=False)
        write(out/(label+'_P2.json'),a)
        if label=='interior':
            from riskprop.stage_0_5_lf_protocol import clustered_rate
            ci=clustered_rate([cN.get(k,0) for k in clusters],[cE.get(k,0) for k in clusters],seed=20261020,resamples=2000)
            ci['formal_policy_approved']=True;ci['scope']='95% conditional vehicle-cluster interval only; not complete time/seed/system-error uncertainty'
            write(out/'P2_cluster_uncertainty.json',ci)
            descriptive(b,out,pd.concat(local_rows,ignore_index=True),w,1.,rows,eligible_times=eligible_times,time_grid=time_grid)
        del a;gc.collect()
    write(out/'source_audit.json',dict(source=group,rows=table.num_rows,trajectories=len(ids),partitions=len(parts['interior']),sha256=e['sha256'],window_ids=[group.removeprefix('us101__')],
        original_exposure_independently_reproduced=True,old_formal_events_read=False,third_window_rows_materialised=0,
        source_access=guard.audit(),reference_plan_sha256=sha(b/'reference_plan.json')))


def descriptive(b,out,d,w,lane_km,events,*,eligible_times=None,time_grid=None):
    import numpy as np
    import pandas as pd
    from riskprop.stage_0_5_final_closure import checked,links
    lo,hi=w;m=d[d._inside&d.time_s.ge(lo)&d.time_s.lt(hi)]
    fields=['speed_mps','acceleration_mps2','net_gap_m','closing_speed_mps','ttc_s']
    stats={}
    for f in fields:
        x=pd.to_numeric(m[f],errors='coerce');x=x[np.isfinite(x)]
        stats[f]=dict(n=len(x),mean=float(x.mean()) if len(x) else None,sd=float(x.std()) if len(x)>1 else None,
            quantiles=[float(q) for q in x.quantile([.01,.1,.5,.9,.99])] if len(x) else None)
    times=np.sort(d.loc[d.time_s.ge(lo)&d.time_s.lt(hi),'time_s'].unique()) if time_grid is None else time_grid[(time_grid>=lo)&(time_grid<hi)]
    coverage=len(times)*.1
    if abs(coverage-(hi-lo))>1e-6:raise ValueError('incomplete_global_clock_support')
    if eligible_times is None:
        o=checked(d);l=links(o,w);eligible_times=o.loc[l.local,'time_s'].to_numpy()
    eligible_times=np.asarray(eligible_times,float)
    block=[]
    for start in np.arange(lo,hi,60):
        end=min(start+60,hi);g=m[m.time_s.ge(start)&m.time_s.lt(end)]
        eligible=(eligible_times>start+1e-9)&(eligible_times<=end+1e-9)
        n=sum(r['onset'] and start<=r['onset_s']<end for r in events)
        block.append(dict(start_s=float(start),end_s=float(end),vehicle_s=len(g)*.1,
            speed_sum=float(g.speed_mps.sum())*.1,density=float(len(g)*.1/lane_km/(end-start)),
            mean_speed_mps=float(g.speed_mps.mean()) if len(g) else None,
            evaluable_s=float(eligible.sum()/10),onset_events=int(n),low_share=float(g.speed_mps.lt(5).mean()) if len(g) else None))
    pd.DataFrame(block).to_csv(out/'time_blocks.csv',index=False)
    write(out/'traffic_metrics.json',dict(window_s=w,lane_km=lane_km,coverage_s=coverage,local_vehicle_s=len(m)*.1,
        density_veh_km_lane=len(m)*.1/lane_km/(hi-lo),low_speed_share=float(m.speed_mps.lt(5).mean()) if len(m) else None,
        metrics=stats,quality_counts={str(k):int(v) for k,v in m.measurement_status.value_counts().items()},
        spatial_support='Follower front; all sources retained for leader/event history',no_row_iid_intervals=True))


def controlled(b,mode,group=None):
    if not sys.flags.no_site:raise PermissionError('python_-S_required')
    sys.path.insert(0,str(b/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    audit=install_guard(b)
    os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPYCACHEPREFIX=str(b/'runtime_cache/pycache'),TEMP=str(b/'runtime_cache/tmp'),TMP=str(b/'runtime_cache/tmp'))
    try:
        if mode=='tests':
            import pytest
            tests=[str(p) for p in (b/'runtime/code/tests').glob('test_*.py')]
            (b/'test_runs').mkdir(exist_ok=True);test_id=str(time.time_ns())
            rc=pytest.main(tests+['-q','-c',str(b/'runtime/code/pytest.ini'),'--basetemp='+str(b/'test_runs'/test_id),'-o','cache_dir='+str(b/'runtime_cache/pytest'),'--junitxml='+str(b/('tests_'+test_id+'.xml'))])
            if rc:raise ValueError('controlled_tests_failed')
            write(b/'test_pass.json',dict(passed=True,code_sha256={p.relative_to(b).as_posix():sha(p) for p in (b/'runtime/code').rglob('*.py') if '__pycache__' not in p.parts}))
        elif mode=='reference':reference(b,group)
        else:raise ValueError('unknown_controlled_mode')
    finally:write(b/(mode+'_'+str(group or 'tests')+'_access_audit.json'),audit)
    if audit['denied']:raise PermissionError('unexpected_access_denial')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['prepare','refresh','tests','freeze-reference','reference']);ap.add_argument('--batch',type=Path,required=True);ap.add_argument('--group');a=ap.parse_args();b=a.batch.resolve()
    if a.command=='prepare':prepare(ROOT,b)
    elif a.command=='refresh':refresh(ROOT,b)
    elif a.command=='freeze-reference':freeze_reference(b)
    else:controlled(b,a.command,a.group)


if __name__=='__main__':main()
