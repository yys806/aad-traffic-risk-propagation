"""Controlled offline LF analysis/portable packaging; never starts SUMO."""
import argparse
import ast
import base64
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

RESULT_ID='RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ['manifest.json','SHA256SUMS'])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError('portable_file_size')
    write(out/'manifest.json',dict(result_id=RESULT_ID,files=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in files]))
    (out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files+[out/'manifest.json']),encoding='utf-8',newline='\n')

def stage(repo,batch):
    ledger=read(batch/'execution_ledger.json')
    if not ledger['closed']:raise PermissionError('closed_ledger_required')
    out=batch/'summary';out.mkdir(exist_ok=True);plan=read(batch/'experiment_plan.json')
    for n in ['experiment_plan.json','PLAN_SHA256','execution_ledger.json','source_audit.json','protocol_source_audit.json','dependency_fingerprints.json',
              'preflight.json','preparation_manifest.json','lf_preparation.json','lf_source_staging.json','offline_CD_C_staging.json','local_measurement_contract.json','gap_offline_analysis.json']:
        shutil.copyfile(batch/n,out/n)
    if (batch/'paired_equivalence.json').exists():shutil.copyfile(batch/'paired_equivalence.json',out/'paired_equivalence.json')
    else:write(out/'paired_equivalence.json',dict(passed=False,status='Not Calculated',reason='Paired runs incomplete',LF3_allowed=False))
    binding=[];bootstrap=[];bundle={}
    for n,d in plan['frozen_files'].items():
        if sha(batch/n)!=d:raise PermissionError('frozen_bytes_changed_'+n)
        raw=(batch/n).read_bytes()
        if n.startswith('runtime/code/'):
            relative=n.removeprefix('runtime/')
            if relative in ['code/pytest.ini','code/src/sitecustomize.py','code/src/riskprop/__init__.py']:
                bootstrap.append(dict(path=n,sha256=d,base64=base64.b64encode(raw).decode()))
            else:
                canonical=raw.replace(b'\r\n',b'\n')
                if (repo/relative).read_bytes().replace(b'\r\n',b'\n')!=canonical:raise PermissionError('executed_source_not_current_'+relative)
                binding.append(dict(path=relative,frozen_sha256=d,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),byte_transform='none' if raw==canonical else 'canonical LF to original CRLF'))
        if n.startswith('inputs/') and Path(n).suffix in ['.xml','.sumocfg']:
            bundle[n]=dict(sha256=d,bytes=len(raw),gzip_base64=base64.b64encode(gzip.compress(raw,mtime=0)).decode())
    write(out/'git_source_binding_audit.json',dict(files=binding,generated_runtime=bootstrap))
    write(out/'engineering_input_bundle.json',dict(files=bundle,raw_states_exported=False,real_data_exported=False))
    case_tree=ET.parse(batch/'boundary_tests.xml').getroot();cases=[]
    for c in case_tree.iter('testcase'):
        failed=c.find('failure') is not None or c.find('error') is not None;skipped=c.find('skipped') is not None
        file=batch/'runtime/code/tests'/(c.get('classname').split('.')[-1]+'.py')
        source=file.read_text(encoding='utf-8');tree=ast.parse(source);name=c.get('name').split('[')[0]
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        cases.append(dict(test=c.get('classname')+'::'+c.get('name'),seconds=float(c.get('time')),actual='Failed' if failed else 'Skipped' if skipped else 'Passed',
            input_conditions=ast.get_source_segment(source,function),parameter_case=c.get('name'),
            expected_assertions=[ast.unparse(n.test) for n in ast.walk(function) if isinstance(n,ast.Assert)],
            expected_rejections=[ast.unparse(n.context_expr) for n in ast.walk(function) if isinstance(n,ast.withitem)],
            fixture_source_path=file.relative_to(batch).as_posix(),fixture_source_sha256=sha(file),
            failure_reason='None' if not failed else ''.join(c.itertext()),
            formal_effect='No promotion of scientific Gate or local attribution policy'))
    write(out/'boundary_test_matrix.json',dict(cases=cases,source_test_sha256={p.name:sha(p) for p in (batch/'runtime/code/tests').glob('test_*lf*.py')},
        earlier_harness_failure=read(batch/'boundary_test_record.json'),controlled_corrected_run=read(batch/'boundary_test_record_v2.json'),
        note='First detailed-report invocation omitted capsule PYTHONPATH and ran no tests. Failure retained; corrected -S environment passed. Original frozen204-test preflight passed.'))
    entry=batch/'lf_analysis_entry.py';shutil.copyfile(Path(__file__).resolve(),entry)
    write(batch/'lf_analysis_source.json',dict(path='code/scripts/finalize_stage_0_5_local_following.py',sha256=sha(entry)))
    return subprocess.call([sys.executable,'-S',str(entry),str(batch),'--render'],timeout=900)

def render(batch):
    sys.path.insert(0,str(batch/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(batch);begin=time.monotonic()
    try:
        from riskprop.stage_0_5_b12_runtime import environment,SCIENCE
        from riskprop.stage_0_5_local_following import analyse,decorate,LOCAL_SPACE
        environment(batch)
        import pandas as pd
        import numpy as np
        import psutil
        out=batch/'summary';plan=read(out/'experiment_plan.json');ledger=read(out/'execution_ledger.json')
        summaries=[];analyses=[];raw_bindings=[];classes=Counter();maxres=None;gap_support=[];analysis_cost=[];censoring=[];accounting=[];traffic=[]
        for spec,entry in zip(plan['runs'],ledger['runs']):
            folder=batch/'runs'/spec['run_id'];p=folder/'summary.json'
            if not p.exists():
                summaries.append(dict(run_id=spec['run_id'],status=entry['status'],observed_s=None,reason=entry.get('reason')));continue
            s=read(p);summaries.append(s);num=s['numerical'];classes.update({c:v['count'] for c,v in num['classifications'].items()})
            if num['max_abs_residual_m'] is not None:maxres=max(maxres or 0.,num['max_abs_residual_m'])
            raw_bindings.append(dict(run_id=spec['run_id'],local_path=str(folder),files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in folder.iterdir() if p.is_file()}))
            if not (folder/'internal_states.parquet').exists() or not s['runtime']['internal_state_rows']:
                analyses.append(dict(run_id=spec['run_id'],status='Not Calculated',reason='No complete raw state support'));continue
            started=time.monotonic();df=pd.read_parquet(folder/'internal_states.parquet');df=df[np.rint(df.time_s*20).astype(int)%2==0].copy()
            if not df.run_id.eq(spec['run_id']).all() or not df.incarnation_id.eq(df.run_id+'|'+df.vehicle_id).all():raise ValueError('raw_identity_label_mismatch')
            a=analyse(df,measured_output=folder/'measured_points.parquet');a['run_id']=spec['run_id'];write(folder/'local_following_analysis.json',a)
            m=pd.read_parquet(folder/'measured_points.parquet')
            # Raw per-row physical gap oracle, independent of TTC implementation.
            known=m.leader_id.notna();same=known&m.leader_lane_id.eq(m.lane_id)&m.leader_position_m.notna()
            direct=m.loc[same,'leader_position_m']-m.loc[same,'leader_length_m']-m.loc[same,'position_m']
            error=(direct-m.loc[same,'net_gap_m']).abs();maximum=float(error.max()) if len(error) else None
            if maximum is not None and maximum>1e-6:raise ValueError('independent_physical_gap')
            # The getter conversion is independently joined to the actual type
            # definition, whose runtime effect was already checked by worker.
            demand=ET.parse(batch/spec['demand']).getroot();types={t.get('id'):float(t.get('minGap')) for t in demand.findall('vType')}
            defs={v.get('id'):v.get('type') for v in demand.findall('vehicle')}
            expected=m.loc[known,'raw_traci_leader_distance_m']+m.loc[known,'vehicle_id'].map(lambda v:types[defs[v]])
            conversion=(expected-m.loc[known,'net_gap_m']).abs()
            if len(conversion) and conversion.max()>1e-12:raise ValueError('independent_getLeader_conversion')
            gap_support.append(dict(run_id=spec['run_id'],point_rows=len(m),leader_resolved_rows=int(known.sum()),same_lane_independent_rows=int(same.sum()),
                same_lane_max_abs_gap_residual_m=maximum,route_or_cross_edge_API_only_rows=int((known&~same).sum()),
                conversion_rows=len(conversion),max_conversion_residual_m=float(conversion.max()) if len(conversion) else None,
                no_claim_all_route_gaps_independently_reconstructed=True))
            first=m.groupby('incarnation_id',sort=False).time_s.min().to_dict();last=m.groupby('incarnation_id',sort=False).time_s.max().to_dict();cuts=[]
            for e in a['engineering_events']:
                cuts.append(dict(e,left_observation_censored=abs(e['event_start_s']-first[e['incarnation_id']])<1e-8,
                    right_observation_censored=e['exit_reason']=='observation_end_right_censored',
                    local_boundary_intersects=not e['fully_inside'] and (e['onset_inside'] or e['confirmation_inside'])))
            censoring.append(dict(run_id=spec['run_id'],global_confirmed_events=len(cuts),onset_inside=a['local_candidates']['event_onset_inside'],confirmation_inside=a['local_candidates']['event_confirmation_inside'],
                fully_inside=a['local_candidates']['event_fully_inside'],left_observation_censored=sum(e['left_observation_censored'] for e in cuts),right_observation_censored=sum(e['right_observation_censored'] for e in cuts),
                examples=cuts[:20],sampling='First20 events in deterministic core order; all counts use all events',formal_local_policy='Unresolved'))
            frames=pd.read_csv(folder/'traffic_frames.csv');local_mask=df.edge_id.eq('main_1')&df.position_m.ge(50.)&df.position_m.lt(250.)
            # Decimated .1s rows check counts at the corresponding .05s frames.
            observed=df[local_mask].groupby(np.rint(df.loc[local_mask,'time_s']*20).astype(int)).size()
            even=frames[np.rint(frames.time_s*20).astype(int)%2==0]
            count_errors=sum(int(observed.get(round(t*20),0))!=int(n) for t,n in zip(even.time_s,even.local_present))
            if count_errors or frames.global_conservation_residual.ne(0).any():raise ValueError('independent_local_global_count')
            slow=frames[frames.local_low_vehicles>0];stopped=m[m.in_local & m.speed_mps.lt(.1)]
            bins=[]
            for key,v in s['traffic']['time_bins'].items():
                bins.append(dict(start_s=int(key)*60,end_s=min((int(key)+1)*60,s['observed_s']),frames=v['frames'],
                    density_veh_km_lane=v['n']/v['frames']/.6 if v['frames'] else None,mean_speed_mps=v['speed']/v['n'] if v['n'] else None,
                    low_share=v['low']/v['n'] if v['n'] else None,actual_inserted=v['inserted'],actual_exited=v['exited']))
            traffic.append(dict(run_id=spec['run_id'],local_space=LOCAL_SPACE,entire_acquisition_s=[0.,s['observed_s']],no_warmup_removed=True,
                first_local_low_005_s=float(slow.time_s.iloc[0]) if len(slow) else None,first_local_stopped_01_s=float(stopped.time_s.min()) if len(stopped) else None,
                mean_local_speed_005_mps=s['traffic']['local_mean_speed_mps'],mean_local_density_005_veh_km_lane=s['traffic']['local_density_veh_km_lane'],
                low_share_01=a['point']['low_speed_share'],local_vehicle_s_005=s['local_vehicle_s'],point_distribution_01=a['point'],bins_60s=bins,
                acceleration_semantics='Public reported preceding-step mean acceleration; no instantaneous driver-command claim',
                real_reference_comparison='Not Performed',mechanism_or_capacity_comparison=False))
            accounting.append(dict(run_id=spec['run_id'],actual_inserted=s['actual_inserted'],actual_exited=s['actual_exited'],present=s['present'],
                global_residual=s['actual_inserted']-s['actual_exited']-s['present'],due_pending_end=s['pending_end'],future_scheduled_not_pending=spec['declared_vehicles']-s['actual_inserted']-s['pending_end'],
                local_count_checks=len(even),local_count_errors=int(count_errors),local_entered=s['local_entered'],local_exited=s['local_exited'],local_vehicle_s=s['local_vehicle_s'],
                local_space=spec['local_space'],pending_excluded_from_density=True))
            analyses.append(dict(a,engineering_events=a['engineering_events'][:20],all_event_details_local='local_following_analysis.json; first20 portable'))
            analysis_cost.append(dict(run_id=spec['run_id'],wall_s=time.monotonic()-started,RSS_at_end_bytes=psutil.Process().memory_info().rss,recorded_point_rows=len(df),not_absolute_peak=True))
            print('LF_ANALYSED '+spec['run_id']+' rows='+str(len(df)),flush=True)
        write(out/'run_manifest.json',dict(runs=ledger['runs'],summaries=summaries,raw_local_bindings=raw_bindings,actual_targeted_attempts=sum(r['status']!='not_attempted' for r in ledger['runs']),main_matrix_runs=0,new_integration_micro_runs=0))
        write(out/'analysis_output_bindings.json',[dict(run_id=r['run_id'],files={n:dict(sha256=sha(batch/'runs'/r['run_id']/n),bytes=(batch/'runs'/r['run_id']/n).stat().st_size) for n in ['measured_points.parquet','local_following_analysis.json'] if (batch/'runs'/r['run_id']/n).exists()}) for r in plan['runs']])
        write(out/'local_following_results.json',analyses);write(out/'point_gap_independent_audit.json',gap_support);write(out/'event_boundary_computability.json',censoring);write(out/'local_global_accounting_audit.json',accounting)
        write(out/'local_traffic_diagnostics.json',traffic)
        write(out/'numerical_branch_coverage.json',dict(all_adjacent_edges=sum(classes.values()),classifications=dict(classes),exact_checked=sum(classes[c] for c in ['Exact Without Postprocessing','Exact After Verified Postprocessing']),
            max_abs_exact_residual_m=maxres,exact_tolerance_m=1e-6,bounded_is_exact=False,legal_coordinate_change_not_zero_residual=True,
            scope='Fresh/no-stop/no restore/no setter/no special devices only; public endpoint following descriptors independent of hidden substep stopping path'))
        write(out/'local_measurement_support_matrix.json',dict(metrics=[
            dict(metric='follower local membership',status='Independently Recomputed',basis='edge+lane set+front50<=x<250; same-clock counts; .6lane-km; external pending excluded'),
            dict(metric='leader identity outside local domain',status='Computable',basis='Full-network same-clock incarnation join before follower filtering; unresolved remainsmissing'),
            dict(metric='physical gap',status='Independent same-lane / Engineering API elsewhere',basis='Direct positions/length vs converted getLeader; other route gaps not all rebuilt'),
            dict(metric='closing/TTC/quality',status='Computable within stated endpoint support',basis='Inherited Stage0.5 point implementation plus analytical tests/independent gap; missing neverzero'),
            dict(metric='temporal following exposure',status='Core engineering computable',basis='Actual .1s clock/follower/leader links; valid+not_applicable statuses; independent primitive-edge recomputation'),
            dict(metric='global confirmed P2 core',status='Engineering Diagnostic Only',basis='Stage0.2 core reused without thresholds changed; explicit flags preserved; independent native no-error scan'),
            dict(metric='local candidate fragments',status='Computable descriptive only',basis='Local observed risk fragments, threshold points distinct from .2s confirmed spans; truncated by local/time support'),
            dict(metric='local formal P2 count/exposure/rate',status='Unresolved / Not Calculated',basis='Onset/confirmation/fully-contained and exposure boundary allocation not scientificallyapproved; no policy selected')],
            scientific_evaluation_window='Not Approved',engineering_acquisition='Entire0..120/300, empty startup, no removed warmup;60s bins descriptive only',
            not_measurable_alias='observation_quality only; approved measurement_status remainsmissing',C_entry_spillback='Evidence Insufficient',C_D_comparison=False))
        # Unanticipated adapter seam: independently known break is erased by
        # older source-frame adapter. This task only fixes its new interface.
        from riskprop.stage_0_5_sumo import build_sumo_formal_source_frame
        from riskprop.formal_risk_measurement import extract_formal_source_events
        counter=[]
        for i,t in enumerate([0.,.1,.2]):
            for v in ['f','l']:
                counter.append(dict(run_id='synthetic',vehicle_id=v,incarnation_id='synthetic|'+v,time_s=t,edge_id='main_1',lane_id='main_1_0',
                    position_m=100.+i if v=='f' else 106.+i,length_m=5.,speed_mps=10. if v=='f' else 9.,acceleration_mps2=0.,
                    leader_id='l' if v=='f' else '',net_gap_m=1. if v=='f' else None,leader_speed_mps=9. if v=='f' else None,
                    identity_break=v=='f' and i==1,observation_gap=False))
        points=decorate(pd.DataFrame(counter));old=extract_formal_source_events(build_sumo_formal_source_frame(points));new=analyse(pd.DataFrame(counter))
        write(out/'formal_adapter_break_counterexample.json',dict(input_rows=counter,independent_expected_confirmed_events=0,
            old_adapter_confirmed_events=len(old),new_flag_preserving_interface_confirmed_events=new['engineering_core']['confirmed_events'],
            old_adapter_mutation='Sets identity_break=False and observation_gap=False unconditionally; only safe for its original validated fresh/no-error recorder domain',
            affected_function='stage_0_5_sumo.build_sumo_formal_source_frame',new_function='stage_0_5_local_following.formal_frame_preserving_flags',
            existing_formal_core_modified=False,historical_results_reclassified=False))
        pair=read(out/'paired_equivalence.json');write(out/'performance_audit.json',dict(paired=pair,analysis_cost=analysis_cost,
            supervisor_runs=ledger['runs'],actual_worker_summaries=[dict(run_id=s['run_id'],rows=s.get('runtime',{}).get('internal_state_rows'),worker_wall_s=s.get('runtime',{}).get('total_worker_wall_s'),transport=s.get('transport')) for s in summaries],
            micro_budget_reused=False,total_analysis_wall_s=time.monotonic()-begin,full600_simulated=False,full600_cost='Forecast only; conservative scheduled residence upper bound, not measured validation',
            no_cache_or_skipped_state_getters=True,resource_sampling_not_absolute_peak=True))
        write(out/'budget_audit.json',dict(targeted_total_authorized=8,previous_targeted_attempts=0,this_task_attempts=sum(e['status']!='not_attempted' for e in ledger['runs']),
            targeted_remaining=8-sum(e['status']!='not_attempted' for e in ledger['runs']),new_integration_micro_remaining=0,new_integration_micro_attempts=0,
            planned=[dict(run_id=r['run_id'],duration_s=r['duration_s'],role=r['role']) for r in plan['runs']],limits=plan['limits'],no_retry_or_search=True,main_matrix_attempts=0,
            existing_full_pytest_SUMO_smoke='Report separately; pre-existing software tests, not targeted research runs'))
        hist=dict(B0_isolation=False,B0_validation_rows='Unknown',B1_C='completed_with_engineering_blocker',B1_D='not_attempted',B11='Pending Numerical Equivalence',B11S='947/948',
            B12_conflict_preserved=True,B1_2_MAIN_MATRIX_ALLOWED=False,B12_main_matrix='0/8',N_positive='Not Observed',N_integration_allowed=False,P_restricted_positive_verified=True,
            CD_v1_D_false_blocker_preserved=True,CD_C_entry_spillback='Evidence Insufficient',historical_reclassification=False)
        write(out/'historical_status_preservation.json',hist)
        logs=[dict(file=p.name,sha256=sha(p),denied=read(p)['denied']) for p in (batch/'access_logs').glob('*.json')]
        deps=read(batch/'dependency_fingerprints.json');protocol=read(batch/'protocol_source_audit.json');checks={}
        for name,e in deps['modules'].items():checks[name]=sha(Path(e['path']))==e['module_file_sha256']
        checks['python_executable']=sha(Path(deps['python_executable']))==deps['python_executable_sha256']
        for name,e in protocol['installed_tools'].items():checks['traci.'+name]=hashlib.sha256(Path(e['path']).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==e['canonical_sha256']
        if not all(checks.values()):raise PermissionError('dependency_fingerprint_changed')
        write(out/'dependency_before_after_audit.json',dict(checks=checks,matched=True,not_OS_absolute_proof=True))
        write(out/'controlled_access_audit.json',dict(logs=logs,unexpected_denials=sum(len(x['denied']) for x in logs),no_real_trajectory_inputs=True,old_B1_C_state_inputs=[],
            prior_CD_C_offline_role=read(batch/'offline_CD_C_staging.json'),guard_probe=read(batch/'guard_probe_result.json'),Python_only=True,os_complete_monitoring=False,native_access_monitored=False))
        write(out/'audit.json',dict(result_id=RESULT_ID,status='completed_with_engineering_blocker' if ledger['global_stop'] else 'local_engineering_closed_with_formal_attribution_unresolved',**SCIENCE,main_matrix_allowed=False,main_matrix_attempts=0,
            global_stop=ledger['global_stop'],engineering_chain_closed=ledger['global_stop'] is None,
            actual_targeted_attempts=sum(e['status']!='not_attempted' for e in ledger['runs']),new_integration_micro_attempts=0,reader_adopted=pair['passed'] and ledger['global_stop'] is None,local_formal_P2='Unresolved',
            C_entry_spillback='Evidence Insufficient',scientific_evaluation_window_approved=False,scientific_warmup_approved=False,historical_reclassification=False))
        write(out/'provenance.json',dict(result_id=RESULT_ID,base_commit=read(batch/'preparation_manifest.json')['base_commit'],plan_sha256=sha(batch/'experiment_plan.json'),
            analysis_source=read(batch/'lf_analysis_source.json'),execution_logic_changed_after_freeze=False,new_runs_started_by_analysis=0))
        write(out/'analysis_access_audit.json',guard)
        if guard['denied']:raise PermissionError('analysis_unexpected_denial')
        seal(out);print('LF_PORTABLE_READY',flush=True)
    finally:write(batch/'lf_analysis_access_audit.json',guard)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch',type=Path);p.add_argument('--render',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args();b=a.batch.resolve()
    if a.render:render(b)
    elif a.seal:seal(b/'summary')
    else:raise SystemExit(stage(Path(__file__).resolve().parents[2],b))
