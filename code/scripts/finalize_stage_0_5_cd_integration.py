"""Close and independently analyse own C/D micro states; never start SUMO."""
import argparse
import base64
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

RESULT='RES-STAGE-0.5-CD-INTEGRATION-V1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ['manifest.json','SHA256SUMS'])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError('portable size')
    write(out/'manifest.json',dict(result_id=RESULT,files=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in files]))
    (out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files+[out/'manifest.json']),encoding='utf-8',newline='\n')

def stage(repo,batch,prior):
    if not read(batch/'execution_ledger.json')['closed'] or not read(prior/'execution_ledger.json')['closed']:raise PermissionError('closed ledgers required')
    out=batch/'summary';out.mkdir(exist_ok=True)
    for name in ['experiment_plan.json','PLAN_SHA256','execution_ledger.json','source_audit.json','preflight.json','preparation_manifest.json','numerical_admission_policy.json','execution_scope_audit.json','budget_authorization.json','prior_D_revalidation.json','C_checkpoint.json','D_checkpoint.json','cd_source_staging.json','input_lineage.json','capsule_copy_audit.json']:
        shutil.copyfile(batch/name,out/name)
    for name in ['experiment_plan.json','execution_ledger.json','preflight.json']:shutil.copyfile(prior/name,out/('v1_'+name))
    bindings=[];generated=[];bundle={}
    for label,root in [('v1',prior),('v2',batch)]:
        p=read(root/'experiment_plan.json')
        for name,digest in p['frozen_files'].items():
            if sha(root/name)!=digest:raise ValueError('frozen bytes '+label+' '+name)
            raw=(root/name).read_bytes()
            if name.startswith('runtime/code/'):
                relative=name.removeprefix('runtime/');canonical=raw.replace(b'\r\n',b'\n')
                current=repo/relative
                if relative in ['code/pytest.ini','code/src/sitecustomize.py','code/src/riskprop/__init__.py'] or not current.exists() or current.read_bytes().replace(b'\r\n',b'\n')!=canonical:
                    generated.append(dict(plan=label,path=name,sha256=digest,base64=base64.b64encode(raw).decode(),reason='historical frozen v1 source or generated bootstrap'))
                else:bindings.append(dict(plan=label,path=relative,frozen_sha256=digest,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),byte_transform='none' if raw==canonical else 'canonical LF to original CRLF'))
            if name.startswith('inputs/') and Path(name).suffix in ['.xml','.sumocfg']:
                bundle[label+'/'+name]=dict(sha256=digest,bytes=len(raw),gzip_base64=base64.b64encode(gzip.compress(raw,mtime=0)).decode())
    write(out/'git_source_binding_audit.json',dict(files=bindings,generated_or_preserved=generated))
    write(out/'engineering_input_bundle.json',dict(files=bundle,real_data=False,raw_state_inputs_exported=False))
    own={}
    for label,root,run in [('D',prior,'cd1_D_micro'),('C',batch,'cd1_C_micro')]:
        folder=root/'runs'/run
        own[label]=dict(files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in folder.iterdir() if p.is_file()},local_path=str(folder))
        for n in ['summary.json','lane_changes.json','exits.json','departures.json']:shutil.copyfile(folder/n,out/(label+'_'+n))
    write(out/'raw_local_bindings.json',own)
    write(out/'v1_controlled_access_audit.json',dict(logs=[dict(file=p.name,sha256=sha(p),denied=read(p)['denied']) for p in sorted((prior/'access_logs').glob('*.json'))],
        guard_probe=read(prior/'guard_probe_result.json'),Python_audit_only=True,os_complete_monitoring=False))
    entry=batch/'analysis_entry.py';shutil.copyfile(Path(__file__).resolve(),entry)
    write(batch/'analysis_source_manifest.json',dict(path='code/scripts/finalize_stage_0_5_cd_integration.py',sha256=sha(entry)))
    return subprocess.call([sys.executable,'-S',str(entry),str(batch),'--render'])

def render(batch):
    sys.path.insert(0,str(batch/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(batch)
    try:
        from riskprop.stage_0_5_b12_runtime import environment,SCIENCE
        from riskprop.stage_0_5_b12_observation import QueueTracker
        from riskprop.stage_0_5_cd_observation import QueueContinuity
        environment(batch)
        import numpy as np
        import pandas as pd
        import xml.etree.ElementTree as ET
        out=batch/'summary';plan=read(out/'experiment_plan.json');C=read(out/'C_summary.json');D=read(out/'D_summary.json')
        # Independent vectorised raw-position count and network-connection check.
        accounting=[];coordinates=[];following=[]
        for kind,s,path in [('C',C,batch/'runs/cd1_C_micro/internal_states.parquet'),('D',D,batch/'inputs/prior_D/internal_states.parquet')]:
            df=pd.read_parquet(path);space=s['local_space'];sel=(df.edge_id==space['edge'])&(df.position_m>=space['start_m'])&(df.position_m<space['end_m'])
            counts=df.loc[sel].groupby('time_s').size();vehicle_s=float(sel.sum()*.05)
            if abs(vehicle_s-s['local_vehicle_s'])>1e-6:raise ValueError('independent local vehicle-time')
            r=next(x for x in plan['runs'] if x['kind']==kind and x['tier']=='micro');net=ET.parse(batch/r['network']).getroot();pairs=set()
            for c in net.findall('connection'):
                a=c.get('from')+'_'+c.get('fromLane');b=c.get('to')+'_'+c.get('toLane');via=c.get('via')
                if via:pairs.add((a,via));pairs.add((via,b))
                else:pairs.add((a,b))
            checked=0;errors=[];local_crossings=Counter();largest_step=0.
            for vid,part in df.groupby('vehicle_id'):
                rows=part.sort_values('time_s').to_dict('records')
                for a,b in zip(rows,rows[1:]):
                    if a['edge_id']!=b['edge_id']:
                        checked+=1
                        if (a['lane_id'],b['lane_id']) not in pairs:errors.append((vid,a['lane_id'],b['lane_id']))
                    elif a['edge_id']==space['edge']:
                        dx=b['position_m']-a['position_m'];largest_step=max(largest_step,abs(dx))
                        if a['position_m']<space['start_m']<=b['position_m']:local_crossings['lower']+=1
                        if a['position_m']<space['end_m']<=b['position_m']:local_crossings['upper']+=1
            if errors or largest_step>=space['end_m']-space['start_m']:raise ValueError('independent path or local crossing support')
            accounting.append(dict(kind=kind,global_inserted=s['actual_inserted'],global_exited=s['actual_exited'],present=s['present'],
                global_residual=s['actual_inserted']-s['actual_exited']-s['present'],local_entered=s['local_entered'],local_exited=s['local_exited'],
                independently_counted_local_vehicle_s=vehicle_s,independent_spatial_crossings=dict(local_crossings),
                largest_observed_local_step_m=largest_step,local_width_m=space['end_m']-space['start_m'],
                no_unobserved_whole_local_domain_jump=True,local_flux_not_global_insertions=True,pending_end=s['pending_end']))
            coordinates.append(dict(kind=kind,actual_connection_pairs_checked=checked,connection_errors=errors,
                metric_mapping_checks=s['mapping_checks'],metric_mapping_max_residual_m=s['max_mapping_residual_m'],
                independent_physical_gaps_checked=s['physical_gap_checks'],physical_gap_max_residual_m=s['max_gap_residual_m'],
                exact_dx_not_evaluable_reasons={k:v for k,v in s['numerical']['reasons'].items() if k.startswith('legal_')}))
            # Point-state following descriptors ONLY: no invented event rate/exposure.
            local=df.loc[sel & ((df.time_s*20).round().astype(int)%2==0)].copy()
            valid=local.net_gap_m.notna()&local.leader_speed_mps.notna()&(local.net_gap_m>0)
            gap=local.loc[valid,'net_gap_m'];closing=local.loc[valid,'speed_mps']-local.loc[valid,'leader_speed_mps'];ttc=gap[closing>1e-3]/closing[closing>1e-3]
            def quant(x):return [float(v) for v in np.quantile(x,[0,.1,.5,.9,1])] if len(x) else None
            following.append(dict(kind=kind,mode='Engineering Diagnostic Only',sampling_s=.1,local_point_samples=len(local),leader_resolved_samples=int(valid.sum()),
                gap_quantiles_m=quant(gap),closing_quantiles_mps=quant(closing),finite_closing_TTC_samples=len(ttc),TTC_quantiles_s=quant(ttc),
                TTC_below_2_point_samples=int((ttc<2).sum()),P2_events='Not Calculated',P2_exposure='Not Calculated',local_formal_P2='Unresolved',
                limitation='Public point-state descriptors; absence/resolution not certified reliable-following exposure; .2s event identity/confirmation not computed'))
        write(out/'local_global_accounting_audit.json',accounting);write(out/'coordinate_support_audit.json',coordinates);write(out/'following_state_diagnostics.json',following)
        # Full .05s candidate frames, including a concrete no-bridge witness.
        earliest_obstruction=None;coupled_unanchored=None;witness=None;flags=Counter();last=None
        for line in (batch/'runs/cd1_C_micro/queue_frames.jsonl').open(encoding='utf-8'):
            q=json.loads(line);last=q
            if earliest_obstruction is None and any(e.get('blocked') and e.get('pending_ids') for e in q['entry_by_path'].values()):earliest_obstruction=q['time_s']
            for c in q['components']:
                e=q['entry_by_path'].get(c['path'],{})
                if e.get('blocked') and e.get('pending_ids'):
                    if earliest_obstruction is None:earliest_obstruction=q['time_s']
                    if c['inlet_adjacent'] and not c['downstream_anchored']:
                        flags['inlet_blocked_unanchored_component_frames']+=1
                        if coupled_unanchored is None:coupled_unanchored=q['time_s']
                for d in q['components']:
                    if d['path']==c['path'] and c['inlet_adjacent'] and not c['downstream_anchored'] and d['downstream_anchored'] and d['upstream_boundary_m']>c['downstream_m']:
                        gap=d['upstream_boundary_m']-c['downstream_m']
                        if witness is None or q['time_s']>witness['time_s']:
                            witness=dict(time_s=q['time_s'],path=c['path'],inlet_component_front_m=c['downstream_m'],anchored_component_rear_m=d['upstream_boundary_m'],
                                physical_net_gap_m=gap,connection_candidate_max_m=10.,same_component=False,source_components=[c,d],entry=e)
        queue=dict(candidate=plan['queue_candidate'],continuity_step_s=.05,output_snapshot_s=1.,first_times=C['first_times'],
            first_geometric_blockage_s=earliest_obstruction,first_inlet_blocked_but_unanchored_component_s=coupled_unanchored,
            entry_spillback='Evidence Insufficient',not_equivalent_to_queue_absent=True,disconnected_component_witness=witness,
            max_component_duration_s=C['queue_max_component_duration_s'],max_coupled_entry_duration_s=C['queue_max_coupled_entry_duration_s'],
            finite_pending_end=C['pending_end'],flags=dict(flags),D_queue='Not Observed',
            limitations=['10m/2s/50m are engineering candidates, not scientific thresholds','Graph components do not prove all-road blockage',
                'Cross-edge coordinate support verified does not imply vehicles spatially connected','Actual path change resets continuity; membership changes alone are not lane changes',
                'Continuity observed discretely at .05s, no hidden within-step continuity claim'])
        write(out/'queue_integration_diagnostics.json',queue)
        # Reproduce old defect from an independent three-frame example.
        def synthetic(t,blocked='1',complete=True,lane='main_0_0'):
            c=dict(path='0',members=['r|a','r|b'],member_lanes={'r|a':lane,'r|b':lane},upstream_interval_m=[10.,10.],inlet_adjacent=True,downstream_anchored=True)
            return dict(time_s=t,components=[c],member_lanes=c['member_lanes'],observation_valid=True,support_complete=complete,all_paths_queued=False,
                downstream_context=True,pending=1,physical_entry_space_observed=True,entry_by_path={blocked:dict(pending_ids=['p'],blocked=True)})
        from riskprop.stage_0_5_b12_observation import QUEUE_CONFIG
        old=QueueTracker(QUEUE_CONFIG);new=QueueContinuity(step=1.)
        for t in [0.,1.,2.]:a=old.update(synthetic(t));b=new.update(synthetic(t))
        old2=QueueTracker(QUEUE_CONFIG);new2=QueueContinuity(step=1.)
        for t in [0.,1.,2.]:a2=old2.update(synthetic(t,blocked='0',complete=t!=1.));b2=new2.update(synthetic(t,blocked='0',complete=t!=1.))
        write(out/'independent_counterexamples.json',dict(lane_mismatch=dict(old_support=a['entry_spillback_supported'],new_support=b['entry_spillback_supported']),
            incomplete_support_bridge=dict(old_support=a2['entry_spillback_supported'],new_support=b2['entry_spillback_supported']),synthetic_expected_support=False))
        totals=Counter();reasons=Counter();exact=passed=0;maximum=None
        for s in [C,D]:
            totals.update({k:v['count'] for k,v in s['numerical']['classifications'].items()});reasons.update(s['numerical']['reasons']);exact+=s['numerical']['exact_checked'];passed+=s['numerical']['exact_passed']
            maximum=max(maximum or 0.,s['numerical']['max_abs_residual_m'])
        write(out/'numerical_branch_coverage.json',dict(all_adjacent_edges=sum(totals.values()),classifications=dict(totals),exact_checked=exact,exact_passed=passed,
            exact_pass_fraction=passed/exact,exact_tolerance_m=1e-6,max_abs_exact_residual_m=maximum,reasons=dict(reasons),
            bounded_is_exact=False,unknown_is_exact=False,not_evaluable_is_zero_residual=False,source_scope='restricted fresh/no-stop/no restore/control/devices/noncyclic only',
            metric_admission='Public positions/speed/gaps may describe point states independently of hidden substep stopping time. No Exact promotion, derived substep trajectories excluded'))
        write(out/'run_manifest.json',dict(actual_runs=2,micro_runs=2,additional_targeted_runs=0,main_matrix_runs=0,seed=20261019,
            v1=read(out/'v1_execution_ledger.json'),v2=read(out/'execution_ledger.json'),actual_summaries=[D,C],
            unattempted=dict(C_sustained='Scenario prerequisite false: no anchored continuous inlet topology',
                D_sustained='Path duty already verified by9 actual journeys; sustained run not necessary for this integration decision; measured per-state cost forecasts exceed600s wall. Do not spend run merely to fill budget',
                v2_D_micro='Already consumed in v1; never rerun'),old_v1_status_preserved=True))
        # Engineering cost forecast, not a fabricated measured full-run cost.
        forecasts={s['kind']:s['runtime']['total_worker_wall_s']/s['runtime']['internal_state_rows']*823*44.*20 for s in [D,C]}
        write(out/'runtime_budget_audit.json',dict(historical_B12_micro_attempted=1,historical_N_numerical=3,historical_P_numerical=5,
            current_authorized_new_micro=2,current_actual_new_micro=2,current_targeted_authorized=8,current_targeted_actual=0,current_main_matrix_authorized=False,
            no_retry_or_parameter_search=True,original_limits=plan['limits'],current_actual_micro_simulated_s=120.,
            actual_controller=[read(out/'v1_execution_ledger.json')['runs'][0],next(x for x in read(out/'execution_ledger.json')['runs'] if x['run_id']=='cd1_C_micro')],
            forecast_full600_D_wall_s_by_observed_per_state_cost=forecasts,forecast_assumptions='823 vehicles *44s approximate residence *20 states/s; linear cost from actual micros. Not an observed full run and not exact performance prediction',
            future_engineering='Reduce redundant synchronous read calls only after source-supported lifecycle invariants or batching audit; no weakening of observation proof',
            memory_sampling_not_absolute_peak=True))
        write(out/'traffic_state_comparison.json',dict(C_compressed_micro=C['traffic'],D_original_scale_sparse_micro=D['traffic'],
            comparable_capacity=False,real_data_read=False,real_reference_comparison='Not Performed; compressed pressure and sparse path probes unsuitable',
            startup='Both start empty; no approved warmup',mechanism_conclusion='Integration only, no paired A baseline, no congestion/real-fit comparison'))
        write(out/'admission.json',dict(restricted_numerical_integration_verified=True,C_internal_queue_observation_verified=True,
            C_persistent_entry_spillback_qualified=False,C_status='Evidence Insufficient',D_actual_lane_change_and_exit_verified=read(out/'prior_D_revalidation.json')['verified'],
            D_original_execution_status=D['status'],D_independent_postvalidation='Verified from saved raw states; original error preserved',
            C_targeted_allowed=False,D_checkpoint_passed=read(out/'D_checkpoint.json')['sustained_allowed'],D_more_runs_needed_for_current_path_duty=False,
            new_ABCD_main_matrix_allowed=False,formal_calibration_allowed=False,scientific_claim_eligible=False,
            policy='Latest researcher authorization permits layered engineering only; no general stop context or scientific threshold approval'))
        history=dict(B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised='Unknown',B1_C='completed_with_engineering_blocker',B1_D='not_attempted',
            B11='Pending Numerical Equivalence',B11S_exact=947,B11S_total=948,B12_conflict='Engineering Blocker preserved',B1_2_MAIN_MATRIX_ALLOWED=False,B12_main_matrix='0/8',
            B12N_positive_snap='Not Observed',B12N_integration_allowed=False,B12P_target_branch_verified=True,B12P_C_D_allowed=False,historical_reclassification=False)
        write(out/'historical_status_preservation.json',history)
        logs=[dict(file=p.name,sha256=sha(p),denied=read(p)['denied'],allowed_open_events=read(p).get('allowed_open_events')) for p in sorted((batch/'access_logs').glob('*.json'))]
        write(out/'controlled_access_audit.json',dict(logs=logs,unexpected_denials=sum(len(x['denied']) for x in logs),negative_probe=read(batch/'guard_probe_result.json'),
            v1=read(out/'v1_controlled_access_audit.json'),Python_audit_only=True,os_complete_monitoring=False,native_access_monitored=False,no_real_trajectory_inputs=True,old_B1_C_state_inputs=[]))
        write(out/'audit.json',dict(result_id=RESULT,status='C_queue_and_D_path_observed_entry_qualification_insufficient',**SCIENCE,
            mode='engineering_observability_and_integration_only',result_mode='exploratory_diagnostic_only',main_matrix_allowed=False,main_matrix_runs=0,
            micro_runs=2,targeted_runs=0,numerical_blockers=totals['Engineering Blocker'],v1_scenario_false_blocker_preserved=True,historical_reclassification=False))
        write(out/'provenance.json',dict(result_id=RESULT,base_commit=read(batch/'preparation_manifest.json')['base_commit'],v1_plan_sha256=sha(out/'v1_experiment_plan.json'),
            v2_plan_sha256=sha(out/'experiment_plan.json'),analysis=read(batch/'analysis_source_manifest.json'),raw_bindings_sha256=sha(out/'raw_local_bindings.json'),
            execution_logic_changed_between_v1_v2=True,change='main_1-only location assumption corrected; micro C wall180s estimated prospectively; no driving/network/demand/threshold tuning; D not retried',
            analysis_starts_no_new_runs=True))
        write(out/'analysis_access_audit.json',guard)
        if guard['denied']:raise PermissionError('analysis denial')
        seal(out);print('CD_SUMMARY_READY',flush=True)
    finally:write(batch/'analysis_access_audit.json',guard)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch',type=Path);p.add_argument('--prior',type=Path);p.add_argument('--render',action='store_true');p.add_argument('--seal',action='store_true')
    a=p.parse_args();b=a.batch.resolve()
    if a.render:render(b)
    elif a.seal:seal(b/'summary')
    else:raise SystemExit(stage(Path(__file__).resolve().parents[2],b,a.prior.resolve()))
