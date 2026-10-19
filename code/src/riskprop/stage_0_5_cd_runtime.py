"""C/D only. Separate ledgers, frozen sources and no search/retry/main matrix."""
from __future__ import annotations
import ast
import base64
import gzip
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from .stage_0_5_positive_runtime import prepare as prepare_base,tests,read,write,sha
from .stage_0_5_b12_runtime import environment,SCIENCE
from .stage_0_5_b12n_runtime import config
from .stage_0_5_boundary_bottleneck import execute_commands
from .stage_0_5_b12_network import coordinate_support
from .stage_0_5_cd_observation import VERSION,validate_summary
from .stage_0_5_sumo import _sumo_binary

RESULT_ID='RES-STAGE-0.5-CD-INTEGRATION-V1'
TESTS=['test_stage_0_5_cd_observation.py','test_stage_0_5_b12_integration.py','test_stage_0_5_near_zero_observability.py',
       'test_stage_0_5_stopping_observability.py','test_stage_0_5_positive_near_zero.py','test_stage_0_5_boundary_bottleneck.py']


def prepare(repo,batch):
    prepare_base(repo,batch)
    todo=['stage_0_5_cd_runtime','stage_0_5_cd_worker','stage_0_5_cd_observation'];copied=set()
    while todo:
        name=todo.pop()
        if name in copied:continue
        p=repo/'code/src/riskprop'/(name+'.py');raw=p.read_text(encoding='utf-8');shutil.copyfile(p,batch/'runtime/code/src/riskprop'/p.name);copied.add(name)
        for n in ast.walk(ast.parse(raw)):
            if isinstance(n,ast.ImportFrom) and n.level==1 and n.module and (repo/'code/src/riskprop'/(n.module+'.py')).is_file():todo.append(n.module)
    for n in TESTS:shutil.copyfile(repo/'code/tests'/n,batch/'runtime/code/tests'/n)
    shutil.copyfile(repo/'code/scripts/run_stage_0_5_cd_integration.py',batch/'runtime/code/scripts/run_stage_0_5_cd_integration.py')
    staging={};bundles={}
    for result in ['RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2','RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1','RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1']:
        root=repo/'evidence/results'/result;m=read(root/'manifest.json')
        names=['engineering_input_bundle.json','execution_ledger.json'] if result.endswith('R2') else ['engineering_input_bundle.json'] if result.endswith('BOTTLENECK-V1') else ['admission.json','source_audit.json']
        for n in names:
            expected=next(x['sha256'] for x in m['files'] if x['path']==n)
            staging[result+'/'+n]=dict(sha256=expected,role='sealed_engineering_input_or_audit')
    write(batch/'cd_source_staging.json',dict(sources=staging,declared_before_read=True,real_data_inputs=[],old_state_inputs=[]))
    for key,binding in staging.items():
        p=repo/'evidence/results'/key
        if sha(p)!=binding['sha256']:raise PermissionError('sealed metadata SHA')
        result,n=key.split('/');value=read(p)
        if n=='engineering_input_bundle.json':bundles[result]=value['files']
        else:write(batch/'inputs/history'/(result+'_'+n),value)
    decoded={}
    for result,files in bundles.items():
        for name,e in files.items():
            allowed=(result.endswith('R2') and name.startswith('inputs/b12_integration_')) or (result.endswith('BOTTLENECK-V1') and name in ['inputs/C/C.net.xml','inputs/D/D.net.xml','inputs/demand_uniform_20261019.rou.xml','inputs/types.rou.xml'])
            if not allowed:continue
            if '..' in Path(name).parts or ':' in name:raise PermissionError('input path')
            raw=gzip.decompress(base64.b64decode(e['gzip_base64'],validate=True))
            if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise PermissionError('input SHA')
            target=batch/'inputs/lineage'/result/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);decoded[target.relative_to(batch).as_posix()]=e['sha256']
    p=read(batch/'inputs/history/RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1_admission.json')
    if not p['target_branch_verified']:raise PermissionError('positive runtime branch missing')
    write(batch/'input_lineage.json',dict(decoded=decoded,excluded='No real reference, old raw states, validation or holdout decoded'))
    # Exact capsule byte equality before freezing, including transitive closure.
    checked=[]
    for path in (batch/'runtime/code').rglob('*.py'):
        relative=path.relative_to(batch/'runtime')
        if relative.as_posix() in ['code/src/sitecustomize.py','code/src/riskprop/__init__.py']:continue
        if sha(path)!=sha(repo/relative):raise PermissionError('capsule source copy mismatch')
        checked.append(relative.as_posix())
    write(batch/'capsule_copy_audit.json',dict(verified=True,files=sorted(checked)))
    print('CD_PREPARED',flush=True)


def revalidate_prior_d(batch):
    """Own-task saved D states only; no SUMO and no historical reclassification."""
    import pandas as pd
    from .stage_0_5_cd_observation import journey_audit,movement
    root=batch/'inputs/prior_D';df=pd.read_parquet(root/'internal_states.parquet')
    events=[];first={};derived_transitions=0
    for vid,part in df.groupby('vehicle_id'):
        rows=part.sort_values('time_s').to_dict('records');first[vid]=rows[0]['lane_id']
        for a,b in zip(rows,rows[1:]):
            if a['incarnation_id']!=b['incarnation_id'] or abs(b['time_s']-a['time_s']-.05)>1e-8:raise ValueError('prior_D_identity_clock')
            if movement(a,b)=='lane_change':events.append(dict(vehicle_id=vid,edge=b['edge_id'],from_lane=a['lane_id'],to_lane=b['lane_id'],before_s=a['time_s'],after_s=b['time_s']))
            derived_transitions+=a['edge_id']!=b['edge_id']
    old=read(root/'summary.json');exits=read(root/'exits.json');defs={v:dict(assigned_lane='2') for v in first}
    result=journey_audit(defs,first,events,exits)
    result.update(raw_states_sha256=sha(root/'internal_states.parquet'),derived_lane_changes=events,derived_edge_transitions=derived_transitions,
        old_run_status=old['status'],old_engineering_blockers=old['engineering_blockers'],old_summary_sha256=sha(root/'summary.json'),
        numerical_unchanged=not old['numerical']['blockers'] and old['numerical']['exact_checked']==old['numerical']['exact_passed'],
        original_runtime_settings_verified=old['runtime_settings']['verified'],new_SUMO_runs=0,old_ledger_rewritten=False,
        correction='Wrong added main_1-only location assumption; engineering duty permits actual same-edge main_0 or main_1 lane2 departure before valid downstream exit')
    write(batch/'prior_D_revalidation.json',result)
    return result


def build_inputs(batch):
    lineage=batch/'inputs/lineage';runs=[]
    for kind in ['D','C']:
        source=lineage/'RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2/inputs'
        net=batch/f'inputs/{kind}_micro.net.xml';shutil.copyfile(source/f'b12_integration_{kind}/b12.net.xml',net)
        tree=ET.parse(source/f'b12_integration_{kind}.rou.xml');root=tree.getroot()
        if kind=='D':
            vv=root.findall('vehicle')
            for v in vv:root.remove(v)
            for i,v in enumerate(vv[:9]):v.set('depart',f'{.1+1.5*i:.1f}');root.append(v)
        demand=batch/f'inputs/{kind}_micro.rou.xml';tree.write(demand,encoding='utf-8',xml_declaration=True)
        runs.append(make_spec(batch,kind,'micro',net,demand,60.))
    source=lineage/'RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/inputs'
    tree=ET.parse(source/'demand_uniform_20261019.rou.xml');root=tree.getroot()
    for t in ET.parse(source/'types.rou.xml').getroot().findall('vType'):root.insert(0,t)
    for kind in ['C','D']:
        net=batch/f'inputs/{kind}_sustained.net.xml';shutil.copyfile(source/kind/(kind+'.net.xml'),net)
        demand=batch/f'inputs/{kind}_sustained.rou.xml';tree.write(demand,encoding='utf-8',xml_declaration=True)
        runs.append(make_spec(batch,kind,'sustained',net,demand,600.))
    return runs


def make_spec(batch,kind,tier,net,demand,duration):
    run_id=f'cd1_{kind}_{tier}';cfg=config(batch,run_id,net,demand,duration);support=coordinate_support(net)
    if not support['coordinate_verified']:raise PermissionError('static network coordinate support')
    root=ET.parse(demand).getroot();vehicles=root.findall('vehicle');types={t.get('id'):dict(t.attrib) for t in root.findall('vType')}
    for v in vehicles:
        if v.findall('stop') or v.get('departPos')!='base' or v.get('departLane') not in ['0','1','2']:raise PermissionError('input lifecycle/insertion outside declared proof')
    micro_c=kind=='C' and tier=='micro'
    tls=[[float(p.get('duration')) for p in t.findall('phase')] for t in ET.parse(net).getroot().findall('tlLogic')]
    return dict(run_id=run_id,kind=kind,tier=tier,condition=kind,seed=20261019,duration_s=duration,
                network=net.relative_to(batch).as_posix(),demand=demand.relative_to(batch).as_posix(),config=cfg.relative_to(batch).as_posix(),
                declared_vehicles=len(vehicles),types=types,expected_tls_durations=tls,
                local_space=dict(edge='main_1',start_m=10. if micro_c else 50.,end_m=40. if micro_c else 250.,lanes=3,lane_km=.09 if micro_c else .6),
                required_role='C: independently associated persistent inlet queue/pending/physical geometry' if kind=='C' else 'D: actual same-edge mandatory merges, path and downstream exits',
                coordinate_support=support)


def freeze(batch):
    if (batch/'experiment_plan.json').exists():raise PermissionError('no plan overwrite')
    if not read(batch/'preflight.json')['passed']:raise PermissionError('preflight')
    runs=build_inputs(batch)
    prior=revalidate_prior_d(batch)
    if not prior['verified'] or not prior['numerical_unchanged']:raise PermissionError('prior D revalidation failed')
    from .stage_0_5_b12_observation import QUEUE_CONFIG
    write(batch/'numerical_admission_policy.json',dict(version='cd1-restricted-layered-v1',exact_tolerance_m=1e-6,
        exact='Only independently verified fresh/no-stop/no-control proof; include P positive snap coverage',
        bounded='Source necessary range only; no Exact count; public point states descriptive, no unobserved substep stop time/path inference',
        unknown='Record Evidence Insufficient; stop core qualification at affected location; no inferred hidden speed',
        legal_coordinate_change='Not Evaluable for dx; independently verified path coordinate may serve spatial observation',
        scientific_tolerance_approved=False,new_scientific_thresholds=False))
    write(batch/'execution_scope_audit.json',dict(declared_before_runs=True,
        Global_Blocker=['source/config/binary/plan SHA','identity/time/control/proof','exact displacement or source bounds','collision/teleport','conservation','shared coordinate/gap consistency','resource/worker/severity schema'],
        Scenario_Specific_Blocker=['missing required D merge/exit','scenario network defect'],
        Evidence_Insufficient=['queue continuity or same-path entry linkage missing','unresolved near-zero context','unsupported topology'],
        Diagnostic_Warning=['legal edge/lane dx Not Evaluable','on-road queue or finite pending within frozen demand'],
        no_traffic_threshold_tuning=True,scenario_C_EI_does_not_block_D=True,global_error_stops_all=True))
    plan=dict(result_id=RESULT_ID,version='cd2-plan-v1',contract_version=VERSION,**SCIENCE,main_matrix_allowed=False,P2_calculated=False,
        mode='engineering_observability_and_integration_only',runs=runs,seed=20261019,second_seed='Not Planned',
        queue_candidate=QUEUE_CONFIG,continuity_step_s=.05,output_snapshot_step_s=1.,entry_rule='Same verified path + >=2 common members + inlet+anchor+pending+geometric blockage jointly >=2s; real path changes reset',
        stop_pending='Finite frozen demand; no arbitrary pending threshold. Global/clock/resource/collision errors stop; unfinished service at duration is reported, never unbounded extension',
        micro_budget=dict(historical_B12_attempted=1,historical_B12_unattempted=1,new_max=2,already_consumed_this_task=1,
            second_new_micro_authorized=True,budget_reply='新增授权2次C/D接入；独立验证总额仍最多8次',D_micro_in_this_plan='Not Attempted; no rerun; independent saved-state revalidation'),
        sustained_budget=dict(max_authorized=8,planned=2,historical_attempted_in_this_pool=0,per_sim_s=600),
        limits=dict(per_run_wall_s=600,batch_wall_s=7200,memory_bytes=3*1024**3,artifact_bytes=2*1024**3),
        micro_per_run_wall_s=180,total_output_bytes=2*1024**3,
        expected_cost=dict(reference='B12 partial C19.75s wall8.39s RSS136MB / 1.02MB; new .05s queue graph+proof adds cost',
            micro_wall_s=[15,180],sustained_wall_s=[120,600],memory_upper_bytes=3*1024**3,total_wall_upper_s=1560,output_upper_bytes=2*1024**3,
            P2_cost='Not computed: integration duties only; no modified P2 semantics',queue_cost='All .05s frames, lane separated O(n log n), profiling retained'),
        activation='C micro uses second new allowance; D raw-state independent revalidation; sustained requires scenario checkpoint/no shared blocker. D micro never retried',
        supersedes='v1 after one completed D run with main_1-only engineering false blocker; old plan/ledger preserved; no traffic tuning')
    plan['frozen_files']={p.relative_to(batch).as_posix():sha(p) for d in [batch/'runtime',batch/'inputs',batch/'official_source'] for p in sorted(d.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for n in ['isolation_policy.json','source_audit.json','cd_source_staging.json','input_lineage.json','preparation_manifest.json','preflight.json','capsule_copy_audit.json','numerical_admission_policy.json','execution_scope_audit.json','prior_D_revalidation.json','budget_authorization.json']:plan['frozen_files'][n]=sha(batch/n)
    write(batch/'experiment_plan.json',plan);(batch/'PLAN_SHA256').write_text(sha(batch/'experiment_plan.json')+'  experiment_plan.json\n')
    write(batch/'execution_ledger.json',dict(closed=False,global_stop=None,started_epoch=read(batch/'budget_authorization.json')['original_started_epoch'],runs=[dict(run_id=r['run_id'],status='not_attempted') for r in runs]))
    print('CD_FROZEN '+sha(batch/'experiment_plan.json'),flush=True)


def load_plan(batch):
    from .stage_0_5_exploratory_response import verify_frozen
    p=read(batch/'experiment_plan.json')
    if sha(batch/'experiment_plan.json')!=(batch/'PLAN_SHA256').read_text().split()[0]:raise PermissionError('plan SHA')
    verify_frozen(batch,p['frozen_files'])
    if p['main_matrix_allowed'] or p['P2_calculated'] or p['version']!='cd2-plan-v1' or len(p['runs'])!=4:raise PermissionError('scope')
    if any(r['kind'] not in ['C','D'] or r['duration_s']>(60 if r['tier']=='micro' else 600) for r in p['runs']):raise PermissionError('budget')
    if sha(_sumo_binary())!=read(batch/'preparation_manifest.json')['sumo_binary_sha256']:raise PermissionError('binary SHA')
    return p


def execute(batch,run_id):
    p=load_plan(batch);ledger=read(batch/'execution_ledger.json');r=next(r for r in p['runs'] if r['run_id']==run_id)
    entry=next(x for x in ledger['runs'] if x['run_id']==run_id)
    if ledger['closed'] or ledger['global_stop'] or entry['status']!='not_attempted':raise PermissionError('stop or no retries')
    if r['kind']=='D' and r['tier']=='micro':raise PermissionError('D micro allowance already consumed; no rerun')
    if r['kind']=='C' and r['tier']=='micro' and not read(batch/'budget_authorization.json').get('two_new_micro_fixtures'):raise PermissionError('ambiguous second micro budget')
    if r['tier']=='sustained':
        check=read(batch/f"{r['kind']}_checkpoint.json")
        if not check['sustained_allowed']:raise PermissionError('scenario preflight incomplete')
    if ledger['started_epoch'] is None:ledger['started_epoch']=time.time()
    remaining=p['limits']['batch_wall_s']-(time.time()-ledger['started_epoch'])
    if remaining<=0:raise TimeoutError('total wall budget')
    write(batch/'execution_ledger.json',ledger)
    spec=dict(run_id=run_id,command=[sys.executable,'-S',str(batch/'runtime/code/scripts/run_stage_0_5_cd_integration.py'),'worker','--batch',str(batch),'--run-id',run_id],
              verify_files={str(batch/r[k]):p['frozen_files'][r[k]] for k in ['network','demand','config']})
    limits=dict(p['limits'],batch_wall_s=remaining,per_run_wall_s=p['micro_per_run_wall_s'] if r['tier']=='micro' else p['limits']['per_run_wall_s'])
    result=execute_commands(batch/'runs',[spec],limits=limits);actual=result['runs'][0];entry.update(actual)
    path=batch/'runs'/run_id/'summary.json';summary=read(path) if path.exists() else None
    stop='worker/resource failure' if actual['status']=='failed' else validate_summary(summary)
    if stop:ledger['global_stop']=dict(run_id=run_id,reason=stop)
    if summary and summary.get('plan_sha256')!=sha(batch/'experiment_plan.json'):ledger['global_stop']=dict(run_id=run_id,reason='summary_plan_SHA')
    write(batch/'execution_ledger.json',ledger)
    write(batch/(run_id+'_ledger.json'),result)


def checkpoint(batch,kind):
    load_plan(batch);ledger=read(batch/'execution_ledger.json');path=batch/'runs'/f'cd1_{kind}_micro'/'summary.json'
    s=read(path) if path.exists() else None
    if kind=='D' and s is None:
        audit=read(batch/'prior_D_revalidation.json');old=batch/'inputs/prior_D/summary.json';s=read(old)
        allowed=audit['verified'] and audit['numerical_unchanged'] and audit['original_runtime_settings_verified'] and not ledger['global_stop']
        write(batch/'D_checkpoint.json',dict(sustained_allowed=bool(allowed),scenario=kind,global_stop=ledger['global_stop'],
            old_run_original_status=s['status'],independent_postaudit_sha256=sha(batch/'prior_D_revalidation.json'),
            reason='Saved .05s states independently prove actual same-edge lane changes and all9 downstream exits; v1 false location blocker preserved',
            main_matrix_allowed=False));print('D checkpoint '+str(bool(allowed)),flush=True);return
    allowed=bool(s and not ledger['global_stop'] and not s['engineering_blockers'] and s['observed_s']==60. and s['runtime_settings']['verified'])
    if s and kind=='D':allowed &= s['journey']['verified'] and s['mapping_checks'].get('cross_edge',0)>0
    if s and kind=='C':allowed &= s['first_times']['internal_queue'] is not None and s['first_times']['entry_spillback_supported'] is not None
    write(batch/f'{kind}_checkpoint.json',dict(sustained_allowed=bool(allowed),scenario=kind,global_stop=ledger['global_stop'],
        micro_summary_sha256=sha(path) if s else None,reason='Predeclared role fulfilled' if allowed else 'Evidence Insufficient or Blocker',main_matrix_allowed=False))
    print(kind+' checkpoint '+str(bool(allowed)),flush=True)


def dispatch(repo,batch,command,run_id=None):
    if command=='prepare':return prepare(repo,batch)
    environment(batch)
    if command=='tests':return tests(batch)
    if command=='freeze':return freeze(batch)
    if command=='run':return execute(batch,run_id)
    if command=='checkpoint':return checkpoint(batch,run_id)
    if command=='worker':
        from .stage_0_5_cd_worker import run_worker
        return run_worker(batch,run_id)
    if command=='close':
        ledger=read(batch/'execution_ledger.json');ledger['closed']=True
        for r in ledger['runs']:
            if r['status']=='not_attempted':r['reason']='No remaining approved prerequisite/need; no automatic expansion'
        write(batch/'execution_ledger.json',ledger);return
    raise PermissionError('C/D only; no matrix or search')
