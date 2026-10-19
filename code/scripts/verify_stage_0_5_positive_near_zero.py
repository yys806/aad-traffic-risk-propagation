"""Pure-Git SHA and independent seven-link recomputation for B1.2-P."""
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
        if sha(path(e['path']))!=e['sha256'] or path(e['path']).stat().st_size>256*1024:raise ValueError('manifest SHA/size')
    sums={}
    for line in path('SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        if name in sums or sha(path(name))!=digest:raise ValueError('SHA256SUMS mismatch')
        sums[name]=digest
    if set(sums)!=actual|{'manifest.json'}:raise ValueError('SHA256SUMS coverage')
    p=read('experiment_plan.json');digest=sha(path('experiment_plan.json'))
    if path('PLAN_SHA256').read_text().split()[0]!=digest:raise ValueError('plan SHA')
    if p['version']!='b12p-plan-v1' or [r['kind'] for r in p['runs']]!=['P1','P2','P3','P4','P5'] or p['C_D_allowed'] or p['main_matrix_allowed']:raise ValueError('frozen task scope')
    if any(r['duration_s']>30 or r['seed']!=20261019 for r in p['runs']) or p['exact_tolerance_m']!=1e-6:raise ValueError('frozen numeric budget')
    for name,expected in p['frozen_files'].items():
        if '/' not in name and name in actual and sha(path(name))!=expected:raise ValueError('frozen policy SHA')
    bundle=read('micro_input_bundle.json')['files']
    required={n for n in p['frozen_files'] if n.startswith('inputs/') and Path(n).suffix in ['.xml','.sumocfg']}
    if set(bundle)!=required:raise ValueError('input bundle coverage')
    for name,e in bundle.items():
        if not name.startswith('inputs/') or '..' in Path(name).parts or ':' in name or '\\' in name:raise ValueError('input path')
        raw=gzip.decompress(base64.b64decode(e['gzip_base64'],validate=True))
        if hashlib.sha256(raw).hexdigest()!=e['sha256'] or len(raw)!=e['bytes'] or e['sha256']!=p['frozen_files'][name]:raise ValueError('input SHA')
    audit=read('audit.json');admit=read('admission.json');history=read('historical_status_preservation.json')
    expected=dict(gate='pending_simulation_sample',scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,
        C_D_allowed=False,main_matrix_allowed=False,main_matrix_attempts=0,historical_reclassification=False,installed_binary_modified=False,debug_build_used=False)
    if any(audit.get(k)!=v for k,v in expected.items()):raise ValueError('scientific/execution boundary')
    if not admit['target_branch_verified'] or admit['C_D_allowed'] or admit['main_matrix_allowed'] or admit['future_numerical_policy_approved']:raise ValueError('admission boundary')
    if history['B12N_integration_allowed'] or history['B12N_positive_snap']!='Not Observed' or history['B1_2_MAIN_MATRIX_ALLOWED'] or history['B12_main_matrix']!='0/8' or history['historical_reclassification'] or history['historical_results_modified']:raise ValueError('historical rewrite')
    source=read('source_audit.json')
    if source['pinned_commit']!='fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3' or not source['source_verified'] or source['generic_stop_context_identifiable'] or source['installed_binary_modified']:raise ValueError('source domain')
    if source['manifest']['microsim_MSVehicle.cpp']['sha256']!='8499ebe445906b19395d5c70945b012f320a439327e9cb3c20f0abd26d15a6a4':raise ValueError('pinned primary source')
    targets=read('target_edges.json');controls=read('control_edges.json');h=.05;eps=.1*.001*h
    if not targets or len(targets)!=admit['target_exact_count'] or len(targets)!=audit['target_exact_edges']:raise ValueError('target count')
    for x in targets:
        a=x['before'];b=x['after'];r=x['result'];proof=x['lifecycle_proof']
        u=a['speed_mps']+a['acceleration_mps2']*h
        if not 0<u<eps or r['u_pre']!=u or r['u_final']!=0. or b['speed_mps']!=0.:raise ValueError('actual positive snap chain')
        age=a['time_s']-b['last_action_time_s']
        if abs(b['time_s']-a['time_s']-h)>1e-8 or abs(age-.05)>1e-8 or r['is_action'] is not False:raise ValueError('nonaction start alignment')
        if any(a[k]!=b[k] for k in ['run_id','vehicle_id','incarnation_id','edge_id','lane_id']) or a['incarnation_id']!=a['run_id']+'|'+a['vehicle_id']:raise ValueError('target identity/coordinate')
        if len(proof)!=9 or any(v is not True for v in proof.values()) or any(v!='false' for v in x['postprocessing_exclusion_devices'].values()):raise ValueError('independent lifecycle proof')
        if any(s['traci_vehicle_control'] is not False or s['input_has_stops'] is not False or s['remaining_stops'] or s['numerical_config_verified'] is not True for s in [a,b]):raise ValueError('control/context proof')
        if r['context'] is not True or r['context_evidence']['basis']!='fresh_no_stops_stopdist_doublemax_invariant':raise ValueError('context inferred/unknown')
        dx=b['position_m']-a['position_m'];expected_dx=.5*a['speed_mps']*h
        if abs(dx-expected_dx)>1e-6 or abs(r['expected_dx_m']-expected_dx)>1e-15 or abs(r['residual_m']-(dx-expected_dx))>1e-15:raise ValueError('independent ballistic displacement')
        if r['classification']!='Exact Pass' or r['exact_pass'] is not True or not r['target_exact_pass'] or len(r['admission_links'])!=7 or any(v is not True for v in r['admission_links'].values()):raise ValueError('incomplete seven links')
        if x['plan_sha256']!=digest or x['source_audit_sha256']!=sha(path('source_audit.json')):raise ValueError('target source/input binding')
    for x in controls:
        a=x['before'];b=x['after'];r=x['result'];u=a['speed_mps']+a['acceleration_mps2']*h
        if u<eps or r['target_exact_pass'] or abs(b['speed_mps']-u)>1e-9 or abs((b['position_m']-a['position_m'])-.5*(a['speed_mps']+u)*h)>1e-6:raise ValueError('above-threshold control')
    n=read('numerical_branch_coverage.json');cc=n['general_classifications'];rm=read('run_manifest.json');ledger=read('execution_ledger.json')
    if n['all_adjacent_edges']!=sum(cc.values()) or n['exact_checked']!=sum(cc.get(k,0) for k in ['Exact Without Postprocessing','Exact After Verified Postprocessing']) or n['exact_passed']!=n['exact_checked'] or n['bounded_is_exact'] or n['unresolved_is_exact']:raise ValueError('numerical coverage')
    if n['target_exact_pass']!=len(targets) or n['exact_tolerance_m']!=1e-6 or n['max_abs_exact_residual_m']>1e-6:raise ValueError('target/precision coverage')
    if not ledger['closed'] or ledger['stop_reason'] is not None or any(r['status']!='completed_valid' for r in ledger['runs']) or rm['runs']!=ledger['runs'] or rm['C_D_runs'] or rm['main_matrix_runs']:raise ValueError('execution ledger')
    if len(rm['summaries'])!=5 or sum(s['target_exact_count'] for s in rm['summaries'])!=len(targets):raise ValueError('per-run target count')
    for c in cc:
        if cc[c]!=sum(s['general_numerical_classifications'].get(c,0) for s in rm['summaries']):raise ValueError('per-run numerical count')
    verified=0
    if repo_root is not None:
        binding=read('git_source_binding_audit.json');checked=set()
        for e in binding['files']:
            relative=e['path']
            if not relative.startswith('code/') or '..' in Path(relative).parts or ':' in relative:raise ValueError('source path')
            raw=subprocess.check_output(['git','show',(':' if source_ref=='INDEX' else source_ref+':')+relative],cwd=repo_root)
            if hashlib.sha256(raw).hexdigest()!=e['canonical_git_blob_sha256']:raise ValueError('Git source SHA: '+relative)
            if e['byte_transform']=='canonical LF to original CRLF':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            elif e['byte_transform']!='none':raise ValueError('source byte transform')
            name='runtime/'+relative
            if hashlib.sha256(raw).hexdigest()!=e['frozen_sha256'] or e['frozen_sha256']!=p['frozen_files'][name]:raise ValueError('frozen source SHA')
            checked.add(name)
        for e in binding['generated_runtime']:
            raw=base64.b64decode(e['base64'],validate=True);name=e['path']
            if hashlib.sha256(raw).hexdigest()!=e['sha256'] or e['sha256']!=p['frozen_files'][name]:raise ValueError('bootstrap SHA')
            checked.add(name)
        if checked!={n for n in p['frozen_files'] if n.startswith('runtime/code/')}:raise ValueError('source coverage')
        verified=len(checked)
    result=dict(passed=True,files=len(actual),target_edges_recomputed=len(targets),controls_recomputed=len(controls),frozen_source_files_verified=verified,
        target_branch_verified=True,C_D_allowed=False,main_matrix_allowed=False,plan_sha256=digest)
    print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--repo-root',type=Path);p.add_argument('--source-ref',default='HEAD')
    a=p.parse_args();verify(a.path,a.repo_root,a.source_ref)
