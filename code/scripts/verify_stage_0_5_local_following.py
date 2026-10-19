"""Pure Git LF evidence verifier. No real data or SUMO execution."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

def verify(root,repo_root=None,source_ref='HEAD'):
    root=Path(root).resolve()
    def path(n):
        p=(root/n).resolve()
        if p.parent!=root:raise ValueError('portable_path_escape')
        return p
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(n):return json.loads(path(n).read_text(encoding='utf-8'))
    actual={p.name for p in root.iterdir() if p.is_file()}-{'manifest.json','SHA256SUMS'};entries=read('manifest.json')['files']
    names=[e['path'] for e in entries]
    if set(names)!=actual or len(names)!=len(set(names)):raise ValueError('manifest_coverage')
    for e in entries:
        if sha(path(e['path']))!=e['sha256'] or path(e['path']).stat().st_size>256*1024:raise ValueError('manifest_SHA_size')
    sums={}
    for line in path('SHA256SUMS').read_text().splitlines():
        d,n=line.split('  ',1)
        if n in sums or sha(path(n))!=d:raise ValueError('SHA256SUMS')
        sums[n]=d
    if set(sums)!=actual|{'manifest.json'}:raise ValueError('SHA_coverage')
    p=read('experiment_plan.json');digest=sha(path('experiment_plan.json'))
    if digest!=path('PLAN_SHA256').read_text().split()[0]:raise ValueError('plan_SHA')
    if p['main_matrix_allowed'] or p['formal_calibration_allowed'] or p['version']!='lf-exploration-plan-v1':raise ValueError('scope')
    if [(r['reader_mode'],r['duration_s'],r['seed']) for r in p['runs']]!=[('sequential',120.,20261019),('batch',120.,20261019),('batch',300.,20261019)]:raise ValueError('frozen_runs')
    if len({(r['network'],r['demand']) for r in p['runs']})!=1 or p['local_space']['start_m']!=50. or p['local_space']['end_m']!=250.:raise ValueError('input_support')
    for n,d in p['frozen_files'].items():
        if '/' not in n and n in actual and sha(path(n))!=d:raise ValueError('frozen_metadata_'+n)
    bundle=read('engineering_input_bundle.json')['files'];required={n for n in p['frozen_files'] if n.startswith('inputs/') and Path(n).suffix in ['.xml','.sumocfg']}
    if set(bundle)!=required:raise ValueError('bundle_coverage')
    for n,e in bundle.items():
        if '..' in Path(n).parts or ':' in n:raise ValueError('input_path')
        raw=gzip.decompress(base64.b64decode(e['gzip_base64'],validate=True))
        if hashlib.sha256(raw).hexdigest()!=e['sha256'] or e['sha256']!=p['frozen_files'][n] or len(raw)!=e['bytes']:raise ValueError('bundle_SHA')
    a=read('audit.json');expected=dict(gate='pending_simulation_sample',scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,
        protocol_lock_allowed=False,stage_1_1_allowed=False,main_matrix_allowed=False,main_matrix_attempts=0,new_integration_micro_attempts=0,
        local_formal_P2='Unresolved',C_entry_spillback='Evidence Insufficient',scientific_evaluation_window_approved=False,scientific_warmup_approved=False,historical_reclassification=False)
    if any(a.get(k)!=v for k,v in expected.items()):raise ValueError('scientific_or_historical_promotion')
    pair=read('paired_equivalence.json')
    if not pair['passed'] or pair['mismatches'] or not pair['all_numeric_values_exact_equal'] or pair['source_plan_sha256']!=digest:raise ValueError('paired_failure')
    if pair['baseline']['getter_requests']!=pair['optimized']['getter_requests'] or pair['rows_compared']*11!=pair['baseline']['getter_requests']:raise ValueError('skipped_getters')
    if pair['baseline']['caching_used'] or pair['optimized']['caching_used'] or pair['optimized']['socket_round_trips']>=pair['baseline']['socket_round_trips']:raise ValueError('transport_claim')
    for field in ['time_s','speed_mps','acceleration_mps2','last_action_time_s','devices_json','remaining_stops_json','route_edges_json','leader_id']:
        if field not in pair['columns_compared']:raise ValueError('omitted_observation_field')
    ledger=read('execution_ledger.json');rm=read('run_manifest.json');budget=read('budget_audit.json')
    attempts=sum(r['status']!='not_attempted' for r in ledger['runs'])
    if not ledger['closed'] or ledger['global_stop'] or attempts!=3 or rm['actual_targeted_attempts']!=attempts or budget['this_task_attempts']!=attempts or budget['targeted_remaining']!=5:raise ValueError('execution_budget')
    if any(r['status'] not in ['completed_valid','completed_with_diagnostic_warning'] for r in ledger['runs']):raise ValueError('unreported_failure')
    n=read('numerical_branch_coverage.json');classes=n['classifications']
    if n['all_adjacent_edges']!=sum(classes.values()) or n['exact_tolerance_m']!=1e-6 or n['max_abs_exact_residual_m']>1e-6 or n['bounded_is_exact']:raise ValueError('numerical')
    if sum(s['numerical']['exact_passed'] for s in rm['summaries'])!=n['exact_checked']:raise ValueError('exact_pass_count')
    for c,v in classes.items():
        if v!=sum(s['numerical']['classifications'][c]['count'] for s in rm['summaries']):raise ValueError('numerical_run_sum')
    for r in read('local_following_results.json'):
        lf=r['local_formal'];core=r['engineering_core'];cand=r['local_candidates']
        if lf['events']!='Unresolved' or lf['evaluable_exposure']!='Unresolved' or lf['rate']!='Not Calculated' or lf['core_threshold_s']!=2. or lf['core_minimum_span_s']!=.2 or lf['closing_epsilon_mps']!=1e-3:raise ValueError('local_P2_policy')
        if core['confirmed_events']!=core['independent_event_count'] or not core['independent_event_recomputed']:raise ValueError('independent_events')
        ex=core['exposure']
        if abs(ex['p2_evaluable_following_exposure_s']-core['independent_evaluable_exposure_s'])>1e-6 or ex['formal_rate_eligible']:raise ValueError('exposure_promotion')
        if cand['endpoint_contained_evaluable_exposure_s']>ex['p2_evaluable_following_exposure_s']+1e-6:raise ValueError('local_exposure_support')
        for e in r['engineering_events']:
            if e['event_confirm_s']-e['event_start_s']<.2-1e-9 or e['event_end_s']<e['event_confirm_s']:raise ValueError('confirmation')
    gap=read('gap_offline_analysis.json')['observation']
    recomputed=gap['remaining_upstream_lane_m']+gap['explicit_internal_path_m']+gap['downstream_lane_rear_position_m']
    if abs(recomputed-gap['independent_gap_m'])>1e-10 or recomputed<=10.:raise ValueError('gap_geometry')
    counter=read('formal_adapter_break_counterexample.json')
    if counter['old_adapter_confirmed_events']!=1 or counter['new_flag_preserving_interface_confirmed_events']!=0 or counter['existing_formal_core_modified']:raise ValueError('formal_flag_counterexample')
    for row in read('point_gap_independent_audit.json'):
        if row['same_lane_max_abs_gap_residual_m']>1e-6 or row['max_conversion_residual_m']>1e-12:raise ValueError('gap_support')
    if any(c['actual']!='Passed' for c in read('boundary_test_matrix.json')['cases']):raise ValueError('boundary_test_failure')
    prefix_audit=read('prefix_consistency_audit.json')
    if not prefix_audit['passed'] or prefix_audit['mismatches'] or prefix_audit['rows']!=pair['rows_compared']:raise ValueError('prefix_comparison')
    if read('full600_forecast_scenarios.json')['full600_run_performed']:raise ValueError('unperformed600_claim')
    verified=0
    if repo_root is not None:
        analysis=read('provenance.json')['analysis_source'];prefix=':' if source_ref=='INDEX' else source_ref+':'
        raw=subprocess.check_output(['git','show',prefix+analysis['path']],cwd=repo_root)
        if hashlib.sha256(raw).hexdigest()!=analysis['sha256']:raise ValueError('analysis_source')
        for e in read('provenance.json').get('additional_analysis_sources',[]):
            raw=subprocess.check_output(['git','show',prefix+e['path']],cwd=repo_root)
            if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise ValueError('additional_analysis_source')
        binding=read('git_source_binding_audit.json');checked=set()
        for e in binding['files']:
            relative=e['path']
            if not relative.startswith('code/') or '..' in Path(relative).parts or ':' in relative:raise ValueError('source_path')
            raw=subprocess.check_output(['git','show',prefix+relative],cwd=repo_root)
            if hashlib.sha256(raw).hexdigest()!=e['canonical_git_blob_sha256']:raise ValueError('Git_source_'+relative)
            if e['byte_transform']=='canonical LF to original CRLF':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            elif e['byte_transform']!='none':raise ValueError('byte_transform')
            name='runtime/'+relative
            if hashlib.sha256(raw).hexdigest()!=e['frozen_sha256'] or e['frozen_sha256']!=p['frozen_files'][name]:raise ValueError('frozen_source')
            checked.add(name)
        for e in binding['generated_runtime']:
            if hashlib.sha256(base64.b64decode(e['base64'],validate=True)).hexdigest()!=e['sha256'] or e['sha256']!=p['frozen_files'][e['path']]:raise ValueError('bootstrap')
            checked.add(e['path'])
        if checked!={n for n in p['frozen_files'] if n.startswith('runtime/code/')}:raise ValueError('source_coverage')
        verified=len(checked)
    result=dict(passed=True,files=len(actual),targeted_attempts=attempts,remaining=5,pair_rows=pair['rows_compared'],frozen_source_files_verified=verified,local_formal_P2='Unresolved',main_matrix_runs=0)
    print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--repo-root',type=Path);p.add_argument('--source-ref',default='HEAD');a=p.parse_args();verify(a.path,a.repo_root,a.source_ref)
