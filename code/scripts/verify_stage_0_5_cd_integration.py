"""Pure Git portable proof verification for C/D integration; no traffic data."""
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
        if p.parent!=root:raise ValueError('portable path escape')
        return p
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(n):return json.loads(path(n).read_text(encoding='utf-8'))
    actual={p.name for p in root.iterdir() if p.is_file()}-{'manifest.json','SHA256SUMS'}
    entries=read('manifest.json')['files'];names=[e['path'] for e in entries]
    if set(names)!=actual or len(names)!=len(set(names)):raise ValueError('manifest coverage')
    for e in entries:
        if sha(path(e['path']))!=e['sha256'] or path(e['path']).stat().st_size>256*1024:raise ValueError('SHA/size')
    sums={}
    for line in path('SHA256SUMS').read_text().splitlines():
        d,n=line.split('  ',1)
        if n in sums or sha(path(n))!=d:raise ValueError('SHA256SUMS')
        sums[n]=d
    if set(sums)!=actual|{'manifest.json'}:raise ValueError('SHA coverage')
    plans={'v1':read('v1_experiment_plan.json'),'v2':read('experiment_plan.json')}
    if sha(path('experiment_plan.json'))!=path('PLAN_SHA256').read_text().split()[0]:raise ValueError('plan SHA')
    for p in plans.values():
        if p['main_matrix_allowed'] or p['P2_calculated'] or p['limits']['memory_bytes']>3*1024**3:raise ValueError('scope or budget')
        if any(r['kind'] not in ['C','D'] or r['seed']!=20261019 or r['duration_s']>(60 if r['tier']=='micro' else 600) for r in p['runs']):raise ValueError('run scope')
    for label,p in plans.items():
        for name,digest in p['frozen_files'].items():
            if '/' in name:continue
            portable=('v1_'+name) if label=='v1' and ('v1_'+name) in actual else name
            if portable in actual and sha(path(portable))!=digest:raise ValueError('frozen metadata SHA '+label+' '+name)
    a=read('audit.json');ad=read('admission.json');h=read('historical_status_preservation.json');n=read('numerical_branch_coverage.json')
    for k,v in dict(gate='pending_simulation_sample',scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,main_matrix_allowed=False,main_matrix_runs=0,historical_reclassification=False).items():
        if a.get(k)!=v:raise ValueError('scientific boundary '+k)
    if ad['C_persistent_entry_spillback_qualified'] or ad['new_ABCD_main_matrix_allowed'] or ad['formal_calibration_allowed']:raise ValueError('unjustified admission')
    if h['B12N_integration_allowed'] or h['B12P_C_D_allowed'] or h['B1_2_MAIN_MATRIX_ALLOWED'] or h['B12_main_matrix']!='0/8':raise ValueError('history rewrite')
    if n['exact_tolerance_m']!=1e-6 or n['max_abs_exact_residual_m']>1e-6 or n['bounded_is_exact'] or n['not_evaluable_is_zero_residual']:raise ValueError('numerical promotion')
    summaries=[read('C_summary.json'),read('D_summary.json')]
    if n['all_adjacent_edges']!=sum(s['numerical']['all_adjacent_edges'] for s in summaries) or n['exact_checked']!=sum(s['numerical']['exact_checked'] for s in summaries) or n['exact_passed']!=n['exact_checked']:raise ValueError('numerical count')
    for c,v in n['classifications'].items():
        if v!=sum(s['numerical']['classifications'][c]['count'] for s in summaries):raise ValueError('class count')
    d=read('prior_D_revalidation.json');events=read('D_lane_changes.json');first=read('D_summary.json')['first_lanes'];exits={x['vehicle_id']:x for x in read('D_exits.json')}
    if not d['verified'] or d['old_ledger_rewritten'] or d['old_run_status']!='completed_with_engineering_blocker':raise ValueError('D original status or revalidation')
    count=0
    for vid,v in d['vehicles'].items():
        merged=any(e['vehicle_id']==vid and e['edge'] in ['main_0','main_1'] and e['from_lane']==e['edge']+'_2' and e['to_lane'] in [e['edge']+'_0',e['edge']+'_1'] for e in events)
        if first.get(vid)!='main_0_2' or not merged or not v['actual_required_merge'] or exits.get(vid,{}).get('last_edge')!='main_2':raise ValueError('actual D path duty')
        count+=1
    if count!=9:raise ValueError('D cohort')
    q=read('queue_integration_diagnostics.json');w=q['disconnected_component_witness']
    gap=w['anchored_component_rear_m']-w['inlet_component_front_m']
    if abs(gap-w['physical_net_gap_m'])>1e-10 or gap<=10 or w['same_component'] or q['entry_spillback']!='Evidence Insufficient' or q['first_times']['entry_spillback_supported'] is not None:raise ValueError('C topology unsupported')
    for x in read('local_global_accounting_audit.json'):
        if x['global_inserted']-x['global_exited']-x['present'] or x['global_residual'] or x['largest_observed_local_step_m']>=x['local_width_m']:raise ValueError('accounting')
        if x['independent_spatial_crossings']['lower']!=x['local_entered'] or x['independent_spatial_crossings']['upper']!=x['local_exited']:raise ValueError('independent local flux')
    counter=read('independent_counterexamples.json')
    if any(not counter[k]['old_support'] or counter[k]['new_support'] for k in ['lane_mismatch','incomplete_support_bridge']):raise ValueError('counterexample')
    rm=read('run_manifest.json');budget=read('runtime_budget_audit.json')
    if rm['actual_runs']!=2 or rm['main_matrix_runs'] or rm['additional_targeted_runs'] or budget['current_actual_new_micro']!=2 or budget['current_targeted_actual']:raise ValueError('actual run budget')
    if not rm['v1']['closed'] or not rm['v2']['closed'] or rm['v1']['global_stop'] or rm['v2']['global_stop']:raise ValueError('ledger')
    bundle=read('engineering_input_bundle.json')['files']
    for label,p in plans.items():
        for name in [n for n in p['frozen_files'] if n.startswith('inputs/') and Path(n).suffix in ['.xml','.sumocfg']]:
            e=bundle[label+'/'+name];raw=gzip.decompress(base64.b64decode(e['gzip_base64'],validate=True))
            if hashlib.sha256(raw).hexdigest()!=e['sha256'] or e['sha256']!=p['frozen_files'][name] or len(raw)!=e['bytes']:raise ValueError('input SHA')
    verified=0
    if repo_root is not None:
        analysis=read('provenance.json')['analysis']
        raw_analysis=subprocess.check_output(['git','show',(':' if source_ref=='INDEX' else source_ref+':')+analysis['path']],cwd=repo_root)
        if hashlib.sha256(raw_analysis).hexdigest()!=analysis['sha256']:raise ValueError('analysis source SHA')
        b=read('git_source_binding_audit.json');checked={'v1':set(),'v2':set()}
        for e in b['files']:
            relative=e['path']
            if not relative.startswith('code/') or '..' in Path(relative).parts or ':' in relative:raise ValueError('source path')
            raw=subprocess.check_output(['git','show',(':' if source_ref=='INDEX' else source_ref+':')+relative],cwd=repo_root)
            if hashlib.sha256(raw).hexdigest()!=e['canonical_git_blob_sha256']:raise ValueError('Git source SHA '+relative)
            if e['byte_transform']=='canonical LF to original CRLF':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            elif e['byte_transform']!='none':raise ValueError('source transform')
            label=e['plan'];name='runtime/'+relative
            if hashlib.sha256(raw).hexdigest()!=e['frozen_sha256'] or e['frozen_sha256']!=plans[label]['frozen_files'][name]:raise ValueError('frozen source SHA')
            checked[label].add(name)
        for e in b['generated_or_preserved']:
            label=e['plan'];name=e['path'];raw=base64.b64decode(e['base64'],validate=True)
            if hashlib.sha256(raw).hexdigest()!=e['sha256'] or e['sha256']!=plans[label]['frozen_files'][name]:raise ValueError('preserved source bytes')
            checked[label].add(name)
        for label,p in plans.items():
            if checked[label]!={x for x in p['frozen_files'] if x.startswith('runtime/code/')}:raise ValueError('source coverage')
        verified=sum(len(v) for v in checked.values())
    result=dict(passed=True,files=len(actual),actual_micro_runs=2,D_actual_journeys=count,C_entry_spillback='Evidence Insufficient',frozen_source_files_verified=verified,main_matrix_runs=0)
    print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--repo-root',type=Path);p.add_argument('--source-ref',default='HEAD')
    a=p.parse_args();verify(a.path,a.repo_root,a.source_ref)
