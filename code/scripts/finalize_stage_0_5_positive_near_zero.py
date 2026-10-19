"""Package only the closed B1.2-P micro probes; no SUMO execution path."""
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

RESULT_ID='RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1'
REPORT='docs/STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ['manifest.json','SHA256SUMS'])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError('portable size limit')
    write(out/'manifest.json',dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]))
    files.append(out/'manifest.json');(out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files),encoding='utf-8',newline='\n')

def stage(repo,batch):
    ledger=read(batch/'execution_ledger.json')
    if not ledger['closed']:raise PermissionError('closed execution required')
    plan=read(batch/'experiment_plan.json');out=batch/'summary';out.mkdir(exist_ok=True)
    for name in ['experiment_plan.json','PLAN_SHA256','execution_ledger.json','admission.json','source_audit.json','source_staging_manifest.json','preparation_manifest.json','preflight.json']:
        shutil.copyfile(batch/name,out/name)
    bindings=[];generated=[];bundle={}
    for name,digest in plan['frozen_files'].items():
        if sha(batch/name)!=digest:raise ValueError('frozen file changed: '+name)
        raw=(batch/name).read_bytes()
        if name.startswith('runtime/code/'):
            relative=name.removeprefix('runtime/')
            if relative in ['code/pytest.ini','code/src/sitecustomize.py','code/src/riskprop/__init__.py']:
                generated.append(dict(path=name,sha256=digest,base64=base64.b64encode(raw).decode()))
            else:
                canonical=raw.replace(b'\r\n',b'\n');transform='none' if raw==canonical else 'canonical LF to original CRLF'
                if transform!='none' and canonical.replace(b'\n',b'\r\n')!=raw:raise ValueError('source newline transform')
                bindings.append(dict(path=relative,frozen_sha256=digest,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),byte_transform=transform))
        if name.startswith('inputs/') and Path(name).suffix in ['.xml','.sumocfg']:
            bundle[name]=dict(bytes=len(raw),sha256=digest,gzip_base64=base64.b64encode(gzip.compress(raw,mtime=0)).decode())
    write(out/'git_source_binding_audit.json',dict(files=bindings,generated_runtime=generated,source_of_bytes='executed frozen B1.2-P capsule'))
    write(out/'micro_input_bundle.json',dict(files=bundle,no_traffic_states=True,no_real_data=True))
    shutil.copyfile(repo/REPORT,out/'report.md')
    entry=batch/'analysis_entry.py';shutil.copyfile(Path(__file__).resolve(),entry)
    write(batch/'analysis_source_manifest.json',dict(source='code/scripts/finalize_stage_0_5_positive_near_zero.py',sha256=sha(entry),report_sha256=sha(repo/REPORT)))
    return subprocess.call([sys.executable,'-S',str(entry),str(batch),'--render'])

def render(batch):
    sys.path.insert(0,str(batch/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(batch)
    try:
        from riskprop.stage_0_5_b12_runtime import environment,SCIENCE
        environment(batch)
        out=batch/'summary';plan=read(out/'experiment_plan.json');ledger=read(out/'execution_ledger.json');admit=read(out/'admission.json')
        summaries=[];target=[];control=[];unresolved=[];coverage=Counter();classes=Counter();runtime=[];raw=[];maximum=None
        accounting=[]
        for spec,entry in zip(plan['runs'],ledger['runs']):
            folder=batch/'runs'/spec['run_id']
            if not (folder/'summary.json').exists():
                summaries.append(dict(run_id=spec['run_id'],status=entry['status'],observed_s=None,target_status='Not Attempted',target_exact_count=None));continue
            s=read(folder/'summary.json');summaries.append(s);coverage.update(s['general_numerical_classifications']);classes.update(s['target_classifications'])
            if s['max_abs_exact_residual_m'] is not None:maximum=max(maximum or 0.,s['max_abs_exact_residual_m'])
            target+=read(folder/'target_edges.json');control+=read(folder/'control_edges.json');unresolved+=read(folder/'unresolved_edges.json')
            runtime.append(dict(run_id=spec['run_id'],settings=s['runtime_settings'],plan_sha256=s['plan_sha256']))
            accounting.append(dict(run_id=spec['run_id'],inserted=s['inserted'],exited=s['exited'],present=s['present'],max_residual=s['max_conservation_residual']))
            raw.append(dict(run_id=spec['run_id'],local_files=[dict(path=p.relative_to(batch).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in folder.iterdir() if p.is_file()]))
        write(out/'target_edges.json',target);write(out/'control_edges.json',control);write(out/'unresolved_edges.json',unresolved)
        exact=sum(coverage[k] for k in ['Exact Without Postprocessing','Exact After Verified Postprocessing'])
        write(out/'numerical_branch_coverage.json',dict(all_adjacent_edges=sum(coverage.values()),general_classifications=dict(coverage),target_classifications=dict(classes),
            exact_checked=exact,exact_passed=exact-sum(s.get('engineering_blockers',[]).count('exact_displacement_violation') for s in summaries),
            target_exact_pass=len(target),bounded=coverage['Bounded Consistency Only'],near_zero_unresolved=coverage['Near-Zero Context Unresolved'],
            not_evaluable=coverage['Not Evaluable'],engineering_blockers=coverage['Engineering Blocker'],max_abs_exact_residual_m=maximum,exact_tolerance_m=1e-6,
            target_success_not_equal_to_general_exact_count=True,bounded_is_exact=False,unresolved_is_exact=False,
            runtime_exact_threshold_equality='Not Observed' if not any(x['result']['u_pre']==5e-6 for x in control) else 'Observed'))
        input_bindings=[dict(run_id=s['run_id'],kind=s['kind'],nominal_w_mps=s['nominal_w_mps'],expected_role=s['expected_role'],seed=s['seed'],duration_s=s['duration_s'],
            inputs={k:dict(path=s[k],sha256=plan['frozen_files'][s[k]]) for k in ['network','demand','config']}) for s in plan['runs']]
        write(out/'run_manifest.json',dict(runs=ledger['runs'],summaries=summaries,input_bindings=input_bindings,actual_runs=sum(r['status']!='not_attempted' for r in ledger['runs']),
            C_D_runs=0,main_matrix_runs=0,main_matrix_authorized=False,raw_local_file_bindings=raw))
        write(out/'runtime_settings_audit.json',runtime);write(out/'vehicle_conservation_audit.json',accounting)
        write(out/'runtime_budget_audit.json',dict(limits=plan['limits'],actual_runs=sum(r['status']!='not_attempted' for r in ledger['runs']),max_runs=5,
            total_simulated_s=sum(s.get('observed_s') or 0 for s in summaries),supervisor_total_wall_s=sum(r.get('wall_s',0) for r in ledger['runs']),
            max_sampled_tree_rss_bytes=max(r.get('peak_sampled_tree_rss_bytes',0) for r in ledger['runs']),per_run=ledger['runs'],no_search_or_retry=True,
            memory_sampling_is_not_absolute_peak=True))
        history=dict(B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised='Unknown',B1_C='completed_with_engineering_blocker',B1_D='not_attempted',
            B11='Pending Numerical Equivalence',B11S_exact=947,B11S_total=948,B12_conflict='Engineering Blocker preserved',B1_2_MAIN_MATRIX_ALLOWED=False,B12_main_matrix='0/8',
            B12N_positive_snap='Not Observed',B12N_integration_allowed=False,historical_reclassification=False,historical_results_modified=False)
        write(out/'historical_status_preservation.json',history)
        logs=[dict(file=p.name,sha256=sha(p),denied=read(p)['denied'],allowed_open_events=read(p).get('allowed_open_events')) for p in sorted((batch/'access_logs').glob('*.json'))]
        write(out/'controlled_access_audit.json',dict(logs=logs,unexpected_denials=sum(len(x['denied']) for x in logs),negative_probe_separate=True,
            no_real_data_inputs=True,old_state_inputs=[],Python_audit_only=True,os_complete_monitoring=False,native_access_monitored=False))
        write(out/'source_observability_audit.json',dict(generic_private_context_identifiable=False,
            proof_scope='Fresh no-stop immutable noncyclic vehicle, no state restore/control/special devices/collisions; source doubleMax invariant',
            actual_positive_target_edges=len(target),no_displacement_or_public_terminal_to_choose_context=True,
            public_terminal_zero_checked_after_independent_selection=True,negative_success_not_used=True,
            dx_tolerance_alone_discriminates_near_zero_alternatives=False,reason='At h=.05, near-zero speed changes can affect dx by <1e-6m; independent source/context and public speed essential',
            general_stop_tasks_state_restore_special_controls='Not Validated',private_state_instrumented=False,
            debug_build_required_for_this_restricted_branch=not admit['target_branch_verified']))
        write(out/'researcher_decision_matrix.json',[dict(item=i,status=s,next_decision=d) for i,s,d in [
            ('Positive restricted branch',admit['target_status'],'Consider as new independent runtime evidence; do not rewrite old result'),
            ('Future numerical admission','Not Approved','Researcher must approve restricted exact/bounded/unknown policy before new integration'),
            ('C/D integration','Not Authorized Here','Separate explicit authorization/frozen plans and queue/path/exit duties'),
            ('ABCD main matrix','Not Authorized Here','Only after remaining integration and independently approved main plan'),
            ('General private context','Unresolved','Keep Unknown; debug build only if that additional scope is necessary and separately approved'),
            ('Calibration / scientific tolerances / P2','Not Ready','Stable traffic evidence and scientific measurement protocol still required')]])
        write(out/'debug_build_feasibility.json',dict(used=False,needed_for_restricted_positive_branch=not admit['target_branch_verified'],
            general_private_context='Unknown; no general getter for cached stopDist',
            proposed_only=dict(scope='Log u_pre/u_final/private stopDist before snap without forcing motion; separate pinned-source binary',
                cost='Unmeasured; requires MSVC/CMake dependencies, build/reproducibility/symbol tracing and binary equivalence audit',
                intrusion='Different instrumented executable; potential floating-point/timing/compiler effects; no equivalence assumed'),
            authorization_required=True,automatic_build=False))
        write(out/'audit.json',dict(result_id=RESULT_ID,status='restricted_positive_branch_verified' if admit['target_branch_verified'] else 'closed_without_target_admission',
            task_mode='engineering_observability_and_admission_only',result_mode='exploratory_diagnostic_only',**SCIENCE,
            target_branch_verified=admit['target_branch_verified'],target_exact_edges=len(target),C_D_allowed=False,main_matrix_allowed=False,main_matrix_attempts=0,
            old_state_inputs_read=False,real_trajectory_inputs=[],historical_reclassification=False,installed_binary_modified=False,debug_build_used=False))
        write(out/'provenance.json',dict(result_id=RESULT_ID,base_commit=read(batch/'preparation_manifest.json')['base_commit'],plan_sha256=sha(batch/'experiment_plan.json'),
            executed_source_and_input_sha256=plan['frozen_files'],analysis=read(batch/'analysis_source_manifest.json'),postrun_execution_logic_changed=False,new_runs_by_analysis=0))
        pre=read(out/'preflight.json')
        if not (out/'test_record.json').exists():
            write(out/'test_record.json',dict(pre_freeze=dict(passed=151,failed=0,skipped=0,command=pre['command'],record_sha256=sha(batch/'preflight.json')),
                test_first='New classifier failed collection before implementation; then independent tests passed; no traffic before source/test/plan freeze',
                final_validation='Pending',skipped_data_tests_are_not_scientific_pass=True))
        write(out/'analysis_access_audit.json',guard)
        if guard['denied']:raise PermissionError('analysis unexpected denial')
        seal(out);print('B12P_PORTABLE_SUMMARY_READY',flush=True)
    finally:write(batch/'analysis_access_audit.json',guard)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch',type=Path);p.add_argument('--render',action='store_true');p.add_argument('--seal',action='store_true')
    a=p.parse_args();b=a.batch.resolve()
    if a.render:render(b)
    elif a.seal:seal(b/'summary')
    else:raise SystemExit(stage(Path(__file__).resolve().parents[2],b))
