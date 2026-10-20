"""Controlled offline protocol design. No SUMO, fitting, calibration or gate command."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

RESULT_ID='RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1'
OLD='RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare(repo,batch):
    if batch.exists():raise ValueError('new_independent_directory_required')
    (batch/'inputs').mkdir(parents=True);(batch/'summary').mkdir();(batch/'runtime/code/src/riskprop').mkdir(parents=True)
    (batch/'runtime/code/tests').mkdir();(batch/'runtime_cache/tmp').mkdir(parents=True);(batch/'dependency_links').mkdir()
    source=repo/'evidence/results'/OLD
    rm=read(source/'run_manifest.json');am=read(source/'analysis_output_bindings.json')
    raw=next(x for x in rm['raw_local_bindings'] if x['run_id']=='lf1_LF3')
    ana=next(x for x in am if x['run_id']=='lf1_LF3');origin=Path(raw['local_path'])
    bindings=[]
    def register(path,digest,name,role):bindings.append(dict(source=str(path),sha256=digest,target='inputs/'+name,role=role,declared_before_read=True))
    def portable(result,names):
        folder=repo/'evidence/results'/result;manifest=read(folder/'manifest.json')
        hashes={e['path']:e['sha256'] for e in manifest['files']}
        for name,alias,role in names:register(folder/name,hashes[name],alias,role)
    portable(OLD,[('experiment_plan.json','LF_plan.json','engineering_summary'),('local_following_results.json','LF_results.json','engineering_summary'),
        ('historical_status_preservation.json','historical_status.json','engineering_summary')])
    portable('RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1',[('real_reference_summary.json','real_local_reference.json','calibration_summary')])
    portable('RES-STAGE-0.5-CALIBRATION-READINESS-V1',[('calibration_source_analysis.json','real_source_reference.json','calibration_summary')])
    for name in ['measured_points.parquet','local_following_analysis.json']:register(origin/name,ana['files'][name]['sha256'],name,'engineering_state' if name.endswith('parquet') else 'engineering_summary')
    for name in ['traffic_frames.csv','queue_snapshots.json','departures.json','exits.json','run_config.json','runtime_settings.json','summary.json']:
        register(origin/name,raw['files'][name]['sha256'],name,'engineering_state' if name.endswith('.csv') else 'engineering_summary')
    write(batch/'source_manifest.json',dict(result_id=RESULT_ID,files=bindings,real_raw_reads=0,third_window_reads=0,role_scope='LF3 engineering and two approved calibration summary windows only'))
    for e in bindings:
        if sha(e['source'])!=e['sha256']:raise PermissionError('source_SHA_'+e['target'])
        shutil.copyfile(e['source'],batch/e['target'])
    prior=repo/'code/outputs/formal/calibration/stage_0_5_local_following_v1'
    policy=read(prior/'isolation_policy.json');policy['executables']=[sys.executable]
    policy['runtime_read_roots']=[r for r in policy['runtime_read_roots'] if 'Sumo' not in r]
    policy['no_new_real_trajectory_inputs']=True
    write(batch/'isolation_policy.json',policy)
    import _winapi
    for p in (prior/'dependency_links').iterdir():_winapi.CreateJunction(str(p.resolve()),str(batch/'dependency_links'/p.name))
    (batch/'runtime/code/src/riskprop/__init__.py').write_text('',encoding='utf-8')
    (batch/'runtime/code/pytest.ini').write_text('[pytest]\npythonpath=src\n',encoding='utf-8')
    refresh(repo,batch)
    write(batch/'preparation.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),sources_verified_before_copy=True,
        original_LF_results_unchanged=True,targeted_already_used=3,targeted_remaining=5,new_integration_micro_remaining=0))

def refresh(repo,batch):
    if (batch/'PLAN_SHA256').exists():raise PermissionError('frozen_runtime_cannot_refresh')
    for name in ['stage_0_5_b1_isolation.py','stage_0_5_lf_protocol.py']:
        shutil.copyfile(repo/'code/src/riskprop'/name,batch/'runtime/code/src/riskprop'/name)
    shutil.copyfile(repo/'code/tests/test_stage_0_5_lf_protocol.py',batch/'runtime/code/tests/test_stage_0_5_lf_protocol.py')
    shutil.copyfile(Path(__file__).resolve(),batch/'protocol_entry.py')

def freeze(batch):
    if (batch/'PLAN_SHA256').exists():raise PermissionError('plan_already_frozen')
    files={p.relative_to(batch).as_posix():sha(p) for folder in ['inputs','runtime'] for p in (batch/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    for n in ['source_manifest.json','isolation_policy.json','protocol_entry.py']:files[n]=sha(batch/n)
    plan=dict(result_id=RESULT_ID,status='Proposed protocol / frozen offline analysis only',version=1,frozen_files=files,new_SUMO_runs=0,targeted_budget_remaining=5,
        analysis_scope='LF3 only; no repeated same-seed pooling; two approved real summaries',
        windows_s=[[x,300.] for x in [0.,60.,120.,180.,240.]],cycle_s=60.,bin_s=[30.,60.],
        candidate_cycle_relative_margins=[.05,.1,.2],candidate_only=True,scientific_tolerance=None,scientific_warmup_s=None,cluster_resamples=2000,statistical_seed=20261020,
        P2_threshold_s=2.,minimum_span_s=.2,recorded_step_s=.1,exact_numerical_tolerance_m=1e-6,
        offline_budget=dict(worker_wall_s=900,tree_RSS_bytes=3*1024**3,output_bytes=1024**3),
        stop=['source/plan SHA mismatch','unknown roles/identity/clock/quality','event/reference disagreement','resource excess'],
        no_new_traffic_reason='Local policy and scientific margins require approval; existing 5 signal cycles answer descriptive questions. Another <=300s seed does not establish unique demand, margins or steady state; preserve remaining budget.',
        ABCD_allowed=False,calibration_allowed=False,scientific_claim_eligible=False)
    write(batch/'experiment_plan.json',plan);(batch/'PLAN_SHA256').write_text(sha(batch/'experiment_plan.json')+'\n')

def controlled(batch,mode):
    if not sys.flags.no_site:raise PermissionError('python_-S_required')
    sys.path.insert(0,str(batch/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(batch)
    os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPYCACHEPREFIX=str(batch/'runtime_cache/pycache'),TEMP=str(batch/'runtime_cache/tmp'),TMP=str(batch/'runtime_cache/tmp'))
    try:
        from riskprop.stage_0_5_lf_protocol import verify_binding
        for e in read(batch/'source_manifest.json')['files']:verify_binding(batch/e['target'],e['sha256'],e['role'])
        if mode=='tests':
            import pytest
            rc=pytest.main([str(batch/'runtime/code/tests/test_stage_0_5_lf_protocol.py'),'-q','-c',str(batch/'runtime/code/pytest.ini'),'--junitxml='+str(batch/'tests.xml'),'--basetemp='+str(batch/'test_tmp')])
            if rc:raise ValueError('protocol_tests_failed')
        elif mode=='inspect':
            import pandas as pd
            import pyarrow.parquet as pq
            write(batch/'schema_probe.json',dict(points_columns=pq.read_schema(batch/'inputs/measured_points.parquet').names,
                traffic_columns=list(pd.read_csv(batch/'inputs/traffic_frames.csv',nrows=1)),queue_sample=read(batch/'inputs/queue_snapshots.json')[:1],
                real_local_keys=list(read(batch/'inputs/real_local_reference.json')['windows']['us101__0750_0805']),
                real_source_summary_keys=list(read(batch/'inputs/real_source_reference.json')['window_summaries']['us101__0750_0805']),
                Aplus_strata_keys=list(read(batch/'inputs/real_Aplus_strata.json')),
                Aplus_diagnostics_keys=list(read(batch/'inputs/real_Aplus_diagnostics.json')['windows']['us101__0750_0805'])))
        elif mode=='analyse':
            from riskprop.stage_0_5_lf_protocol import validate_plan
            validate_plan(batch)
            analyse(batch)
        else:raise ValueError('unknown_mode')
    finally:write(batch/(mode+'_access_audit.json'),guard)
    if guard['denied']:raise PermissionError('unexpected_access')

def analyse(batch):
    import numpy as np
    import pandas as pd
    from collections import Counter
    from riskprop.stage_0_5_lf_protocol import event_audit,exposure_audit,candidate_rates,cycle_diagnostics,clustered_rate
    out=batch/'summary';start=time.monotonic();plan=read(batch/'experiment_plan.json')
    m=pd.read_parquet(batch/'inputs/measured_points.parquet');old=read(batch/'inputs/local_following_analysis.json');events=old['engineering_events']
    if m.run_id.nunique()!=1 or m.run_id.iloc[0]!='lf1_LF3' or len(m)!=433372:raise ValueError('LF3_support')
    # Independent risk-run scan from measured primitive identities/clock/status.
    # A filtered risk-only row cannot bridge a non-risk row: time AND original
    # observation_index must remain adjacent. No event was selected by location.
    r=m[m.ttc_valid&m.ttc_s.gt(0)&m.ttc_s.lt(2)&m.measurement_status.eq('valid')&m.reliable_following_eligible&~m.identity_break&~m.observation_gap].sort_values(['incarnation_id','time_s'])
    br=(r.incarnation_id.ne(r.incarnation_id.shift())|r.leader_incarnation_id.ne(r.leader_incarnation_id.shift())|r.leader_id.ne(r.leader_id.shift())|
        r.time_s.diff().sub(.1).abs().gt(1e-6)|r.observation_index.diff().ne(1))
    independent=[]
    for _,g in r.groupby(br.cumsum(),sort=False):
        a=float(g.time_s.iloc[0]);b=float(g.time_s.iloc[-1])
        if b-a<.2-1e-9:continue
        c=float(g.loc[g.time_s-a>=.2-1e-9,'time_s'].iloc[0])
        independent.append((g.incarnation_id.iloc[0],a,c,b))
    expected=[(e['incarnation_id'],e['event_start_s'],e['event_confirm_s'],e['event_end_s']) for e in events]
    if sorted(independent)!=sorted(expected):raise ValueError('independent_core_events_disagree')
    rows,counts=event_audit(m,events);den=exposure_audit(m,return_clusters=True)
    if [counts[k] for k in ['onset','confirmation','through_end']]!=[86,87,83]:raise ValueError('historical_count_reconstruction')
    if abs(den['global_evaluable_s']-old['engineering_core']['exposure']['p2_evaluable_following_exposure_s'])>1e-6 or abs(den['local_both_s']-old['local_candidates']['endpoint_contained_evaluable_exposure_s'])>1e-6:raise ValueError('historical_exposure_reconstruction')
    pd.DataFrame(rows).to_csv(out/'event_attribution_audit.csv',index=False)
    differences=[r for r in rows if len({r[k] for k in ['onset_inside','confirmation_inside','through_confirmation','through_end']})>1]
    write(out/'attribution_summary.json',dict(counts=counts,old_through_end_83_not_relabelled=True,independent_core_events=len(independent),unique_events=len(set(expected)),
        new_definition='through_confirmation means ALL OBSERVED event members from onset through actual confirmation inside R, distinct from historical full observed event',
        onset_context_counts=dict(Counter(r['onset_context'] for r in rows)),local_onset_context_counts=dict(Counter(r['onset_context'] for r in rows if r['onset_inside'])),
        differences=differences,candidate_rates=candidate_rates(counts,den),local_formal_P2='Unresolved',local_formal_rate='Not Calculated'))
    cluster_seconds=den.pop('cluster_local_seconds');write(out/'denominator_audit.json',den)
    clusters=sorted(cluster_seconds);onsets=Counter(r['incarnation_id'] for r in rows if r['onset_inside'])
    cluster_ci=clustered_rate([onsets[k] for k in clusters],[cluster_seconds[k] for k in clusters],seed=plan['statistical_seed'],resamples=plan['cluster_resamples'])
    write(out/'conditional_cluster_uncertainty.json',cluster_ci)
    cluster_table=pd.DataFrame(dict(incarnation_id=clusters,onset_count=[onsets[k] for k in clusters],local_evaluable_s=[cluster_seconds[k] for k in clusters]))
    cluster_table.to_csv(batch/'cluster_totals_local.csv',index=False)
    sensitivity=[]
    for a,b in plan['windows_s']:
        wr,wc=event_audit(m,events,window=(a,b));wd=exposure_audit(m,window=(a,b))
        local=m[m.in_local&m.time_s.ge(a)&m.time_s.lt(b)]
        sensitivity.append(dict(start_s=a,end_s=b,counts=wc,candidate_rates=candidate_rates(wc,wd),denominator=wd,
            local_points=len(local),TTC_below2_points=int((local.ttc_valid&local.ttc_s.lt(2)).sum()),
            boundary_events=[x['event_id'] for x in wr if x['confirmation_observed_after_window']],
            no_new_event_created_at_window_start=True,not_scientific_evaluation_windows=True))
    write(out/'window_sensitivity.json',sensitivity)
    f=pd.read_csv(batch/'inputs/traffic_frames.csv')
    if len(f)!=6000 or not np.allclose(f.time_s.to_numpy(),np.arange(1,6001)*.05,atol=1e-8,rtol=0):raise ValueError('traffic_clock')
    if f.global_conservation_residual.abs().max()!=0 or f.local_set_balance_residual.abs().max()!=0:raise ValueError('accounting_error')
    def bins(width):
        result=[]
        for a in np.arange(0,300,width):
            b=min(a+width,300);g=f[f.time_s.gt(a)&f.time_s.le(b+1e-8)];vt=float(g.local_present.sum()*.05)
            result.append(dict(start_s=float(a),end_s=float(b),local_vehicle_s=vt,mean_speed_mps=float(g.local_speed_sum.sum()*.05/vt) if vt else None,
                density=float(vt/.6/(b-a)),low_speed_vehicle_time_share=float(g.local_low_vehicles.sum()*.05/vt) if vt else None,
                inserted=int(g.inserted_step.sum()),exited=int(g.exited_step.sum()),present_end=int(g.global_present.iloc[-1]),pending_end=int(g.external_pending.iloc[-1]),
                local_entered=int(g.local_entered.sum()),local_exited=int(g.local_exited.sum()),local_present_end=int(g.local_present.iloc[-1]),
                mean_onroad_stopped=float(g.onroad_stopped_vehicles.mean())))
        return result
    cycles=bins(60);halves=bins(30);seconds=bins(1)
    pd.DataFrame(seconds).to_csv(out/'traffic_state_1s.csv',index=False)
    pd.DataFrame(halves).to_csv(out/'traffic_state_30s.csv',index=False)
    write(out/'traffic_cycle_audit.json',dict(cycles=cycles,denominator_lane_km=.6,right_endpoint_integration_step_s=.05,cycle_phase_origin_s=0.,
        all_six_thousand_clocks_verified=True,global_balance_max_abs=0,local_balance_max_abs=0,
        stationary_network_claim_eligible=False,whole_C_spillback_qualification='Evidence Insufficient'))
    warmups=[cycle_diagnostics(cycles,relative_margin=d) for d in plan['candidate_cycle_relative_margins']]
    q=read(batch/'inputs/queue_snapshots.json');queue_counts=Counter(s['qualification']['state'] for s in q)
    write(out/'warmup_candidate_analysis.json',dict(sensitivity=warmups,thresholds_status='Engineering sensitivity only; no evidence yet for approved acceptable drift margins',
        local_plateau_does_not_resolve_global_pending=True,all_acquisition_retained=True,
        recommendations=['Phase-aligned local traffic-state candidate plus separately reported network/pending trend; no P2 threshold used to select warmup',
            'If demand exceeds supply and backlog keeps growing, steady-network warmup may not exist; choose a time-dynamic finite-horizon target rather than deleting the growth'],
        formal_warmup_s=None,formal_evaluation_window=None,observed_cycles=len(cycles),queue_state_counts=dict(queue_counts),
        queue_first_times={k:next((s['time_s'] for s in q if s['qualification'].get(k)),None) for k in ['onroad_queue_observed','inlet_adjacent_queue_observed','upstream_extension_observed']},
        queue_candidate_not_whole_spillback_admission=True))
    source=read(batch/'inputs/real_source_reference.json');real=read(batch/'inputs/real_local_reference.json');plus=read(batch/'inputs/real_Aplus_diagnostics.json');strata=read(batch/'inputs/real_Aplus_strata.json')
    reference=[]
    for w,v in real['windows'].items():
        sl=[s for s in strata['slices'] if s['source_group']==w and s['eligible']]
        if abs(sum(s['coverage_s'] for s in sl)-v['interior_coverage_s'])>1e-6:raise ValueError('real_summary_support_disagrees')
        speed=v['interior_metrics']['speed_mps']['distribution']['mean'];density=sum(s['density_veh_km_lane']*s['coverage_s'] for s in sl)/sum(s['coverage_s'] for s in sl)
        reference.append(dict(window=w,local_space='mainline1-5 /150<=Local_Y<350m /1.0lane-km',interior_coverage_s=v['interior_coverage_s'],
            mean_speed_mps=speed,mean_density_veh_km_lane=density,eligible_slices=len(sl),interior_metric_summaries=v['interior_metrics'],crossings=v['crossings'],
            local_reliable_following_s=sum(s['local_reliable_following_s'] for s in sl),candidate_local_evaluable_following_s=sum(s['local_evaluable_following_s'] for s in sl),
            formal_local_event_count='Not Calculated',formal_local_rate='Not Calculated',
            full_source_P2=source['window_summaries'][w]['p2'],full_source_exposure=source['window_summaries'][w]['exposure'],
            full_source_observability=source['window_summaries'][w]['observability'],full_source_kinematics=source['window_summaries'][w]['kinematics'],
            fleet_observed=plus['windows'][w]['fleet'],source_P2_scope_not_local=True,
            reference_boundary_guard='Previously frozen descriptive A+ proposal, not a newly approved scientific evaluation window',
            simulation_vs_real_local_speed_difference_mps=cycles[-1]['mean_speed_mps']-speed,
            difference_is_description_not_a_pass_decision=True))
    write(out/'approved_reference_support.json',dict(windows=reference,source_cluster_uncertainty=source['clustered_uncertainty'],
        fleet='Observed trajectory composition/length identified in two approved A+ raw joins; upstream demand fleet and behavior parameters remain unidentified',
        actual_real_trajectory_reads_this_task=0,actual_validation_window_reads=0,real_real_ED_upper_bound='Not Identifiable'))
    write(out/'audit.json',dict(result_id=RESULT_ID,engineering_offline_analysis_complete=True,scientific_claim_eligible=False,
        gate='pending_simulation_sample',ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,
        local_formal_P2='Unresolved',local_formal_rate='Not Calculated',tolerances='Tolerance Not Yet Justified',ED_upper_bound='Not Identifiable',
        C_entry_spillback='Evidence Insufficient',main_matrix_runs=0,formal_calibration_runs=0,new_SUMO_runs=0,targeted_budget_remaining=5))
    write(out/'independent_recomputation.json',dict(core_event_tuples_match=True,confirmed_events=266,old_counts_reproduced=True,old_global_and_local_exposure_reproduced=True,
        current_source_reference_checks='A+ eligible coverage matches B1 frozen two-window projection; no old states/events reopened',
        observed_rows=len(m),analysis_wall_s=time.monotonic()-start))
    print('PROTOCOL_OFFLINE_ANALYSIS_COMPLETE',flush=True)

def execute(batch,mode):
    import psutil
    env=dict(os.environ,PYTHONPYCACHEPREFIX=str(batch/'runtime_cache/pycache'))
    cmd=[sys.executable,'-S',str(batch/'protocol_entry.py'),mode,'--batch',str(batch),'--inside']
    log=batch/(mode+'_worker.log');started=time.monotonic();peak=0;failure=None
    with log.open('w',encoding='utf-8') as output:
        proc=subprocess.Popen(cmd,env=env,stdout=output,stderr=subprocess.STDOUT)
        tree=psutil.Process(proc.pid)
        while proc.poll() is None:
            try:peak=max(peak,sum(p.memory_info().rss for p in [tree]+tree.children(recursive=True) if p.is_running()))
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
            size=sum(p.stat().st_size for p in batch.rglob('*') if p.is_file())
            if time.monotonic()-started>900:failure='offline_wall_budget'
            elif peak>3*1024**3:failure='offline_RSS_budget'
            elif size>1024**3:failure='offline_output_budget'
            if failure:
                for child in tree.children(recursive=True):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                proc.terminate();break
            time.sleep(.2)
        rc=proc.wait(timeout=15)
    write(batch/(mode+'_execution.json'),dict(mode=mode,exit_code=rc,failure=failure,wall_s=time.monotonic()-started,peak_sampled_tree_RSS_bytes=peak,
        log_sha256=sha(log),resource_sampling_not_absolute_peak=True,new_SUMO_runs=0))
    if failure or rc:raise RuntimeError('controlled_offline_failure: '+str(failure)+' exit='+str(rc))
    print('CONTROLLED_'+mode.upper()+'_OK',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','refresh','freeze','tests','inspect','analyse']);p.add_argument('--batch',type=Path,required=True);p.add_argument('--inside',action='store_true');a=p.parse_args();b=a.batch.resolve()
    if a.inside:controlled(b,a.mode)
    elif a.mode=='prepare':prepare(Path(__file__).resolve().parents[2],b)
    elif a.mode=='refresh':refresh(Path(__file__).resolve().parents[2],b)
    elif a.mode=='freeze':freeze(b)
    else:execute(b,a.mode)
