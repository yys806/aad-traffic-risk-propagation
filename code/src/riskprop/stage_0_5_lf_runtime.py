"""Independent LF plan: only remaining targeted diagnostics, no matrix path."""
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
from .stage_0_5_positive_runtime import prepare as base_prepare,tests,read,write,sha
from .stage_0_5_b12_runtime import environment,SCIENCE
from .stage_0_5_b12n_runtime import config
from .stage_0_5_boundary_bottleneck import execute_commands
from .stage_0_5_cd_observation import validate_summary
from .stage_0_5_cd_runtime import make_spec
from .stage_0_5_sumo import _sumo_binary,_ensure_traci_importable
from .stage_0_5_local_following import VERSION,LOCAL_SPACE

RESULT_ID='RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1'
TEST_NAMES=['test_stage_0_5_local_following.py','test_stage_0_5_lf_transport.py','test_stage_0_5_lf_guards.py','test_stage_0_5_cd_observation.py',
            'test_stage_0_5_near_zero_observability.py','test_stage_0_5_stopping_observability.py']


def protocol_audit(batch):
    root=batch/'official_source';manifest=read(root/'additional_source_manifest.json')
    for n,e in manifest.items():
        if sha(root/n)!=e['sha256']:raise PermissionError('protocol_source_SHA')
    tools=Path(_ensure_traci_importable());installed={}
    for name in ['connection','domain','storage','constants']:
        canonical=(tools/'traci'/(name+'.py')).read_bytes().replace(b'\r\n',b'\n')
        source=(root/('tools_traci_'+name+'.py')).read_bytes().replace(b'\r\n',b'\n')
        if canonical!=source:raise PermissionError('installed_traci_not_pinned_'+name)
        installed[name]=dict(path=str(tools/'traci'/(name+'.py')),canonical_sha256=hashlib.sha256(canonical).hexdigest())
    raw=(tools/'traci/_vehicle.py').read_bytes().replace(b'\r\n',b'\n')
    if raw!=(root/'tools_traci__vehicle.py').read_bytes().replace(b'\r\n',b'\n'):raise PermissionError('installed_vehicle_parser_not_pinned')
    installed['_vehicle']=dict(path=str(tools/'traci/_vehicle.py'),canonical_sha256=hashlib.sha256(raw).hexdigest())
    server=(root/'src_traci-server_TraCIServer.cpp').read_text(encoding='utf-8').splitlines()
    needles=['while (myInputStorage.valid_pos()', 'cmd == libsumo::CMD_SIMSTEP', 'writeStatusCmd(commandID, libsumo::RTYPE_OK', 'writeResponseWithLength(outputStorage, getWrapperStorage())']
    refs={n:[i+1 for i,s in enumerate(server) if n in s] for n in needles}
    if not all(refs.values()):raise PermissionError('protocol_order_not_verified')
    write(batch/'protocol_source_audit.json',dict(pinned_commit='fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3',manifest=manifest,installed_tools=installed,
        server_line_references=refs,source_verified=True,allowed_commands=[0xa4],allowed_variables=[0x7e,0x54,0x74],
        order='GET requests dispatched without advancing simulation; each status precedes corresponding typed variable reply',
        no_cache=True,no_setter=True,no_time_advance=True,one_client_and_microsim_verified_at_runtime=True,
        limitation='Private client transport attributes pinned; fail closed on source/schema/response changes; paired real-run proof still required'))


def prepare(repo,batch):
    base_prepare(repo,batch);protocol_audit(batch)
    source=repo/'evidence/results/RES-STAGE-0.5-CD-INTEGRATION-V1';manifest=read(source/'manifest.json')
    names=['engineering_input_bundle.json','run_manifest.json','admission.json','raw_local_bindings.json','queue_integration_diagnostics.json','researcher_decision_matrix.json','issue_discovery_report.json','C_summary.json','D_summary.json']
    bindings={n:next(e['sha256'] for e in manifest['files'] if e['path']==n) for n in names}
    write(batch/'lf_source_staging.json',dict(role='sealed_CD_engineering_metadata_and_authorized_CD_C_offline_states',sources=bindings,declared_before_read=True,
        real_data_inputs=[],old_B1_C_inputs=[],validation_inputs=[],holdout_inputs=[]))
    history=batch/'inputs/CD_metadata';history.mkdir()
    for n,d in bindings.items():
        if sha(source/n)!=d:raise PermissionError('CD_metadata_SHA')
        shutil.copyfile(source/n,history/n)
    bundle=read(history/'engineering_input_bundle.json')['files'];decoded={}
    for name in ['C_sustained.net.xml','C_sustained.rou.xml','C_micro.net.xml']:
        key='v2/inputs/'+name;e=bundle[key];raw=gzip.decompress(base64.b64decode(e['gzip_base64'],validate=True))
        if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise PermissionError('engineering_input_SHA')
        (batch/'inputs'/name).write_bytes(raw);decoded[name]=e['sha256']
    own=read(history/'raw_local_bindings.json')['C'];base=Path(own['local_path']).resolve()
    expected=(repo/'code/outputs/formal/calibration/stage_0_5_cd_integration_v2/runs/cd1_C_micro').resolve()
    if base!=expected:raise PermissionError('offline_input_not_authorized_CD_C')
    selected=['internal_states.parquet','queue_frames.jsonl'];declared={n:own['files'][n] for n in selected}
    write(batch/'offline_CD_C_staging.json',dict(role='Authorized previous CD task C, NOT historic B1 C',source=str(base),files=declared,declared_before_read=True))
    dest=batch/'inputs/prior_CD_C';dest.mkdir()
    for n,e in declared.items():
        if sha(base/n)!=e['sha256']:raise PermissionError('offline_CD_C_SHA')
        shutil.copyfile(base/n,dest/n)
    todo=['stage_0_5_lf_runtime','stage_0_5_lf_worker','stage_0_5_lf_transport','stage_0_5_local_following'];copied=set()
    while todo:
        name=todo.pop()
        if name in copied:continue
        p=repo/'code/src/riskprop'/(name+'.py');raw=p.read_text(encoding='utf-8');shutil.copyfile(p,batch/'runtime/code/src/riskprop'/p.name);copied.add(name)
        for n in ast.walk(ast.parse(raw)):
            if isinstance(n,ast.ImportFrom) and n.level==1 and n.module and (repo/'code/src/riskprop'/(n.module+'.py')).is_file():todo.append(n.module)
    for n in TEST_NAMES:shutil.copyfile(repo/'code/tests'/n,batch/'runtime/code/tests'/n)
    shutil.copyfile(repo/'code/scripts/run_stage_0_5_local_following.py',batch/'runtime/code/scripts/run_stage_0_5_local_following.py')
    write(batch/'lf_preparation.json',dict(decoded=decoded,copy_equality=all(sha(p)==sha(repo/p.relative_to(batch/'runtime')) for p in (batch/'runtime/code').rglob('*.py') if p.name not in ['__init__.py','sitecustomize.py']),
        prior_CD_targeted_used=0,targeted_remaining_at_start=8,old_micro_remaining=0,actual_real_trajectories_read=0))
    print('LF_PREPARED',flush=True)


def freeze(batch):
    if (batch/'experiment_plan.json').exists():raise PermissionError('no plan overwrite')
    if not read(batch/'preflight.json')['passed'] or not read(batch/'lf_preparation.json')['copy_equality']:raise PermissionError('preflight')
    net=batch/'inputs/C_sustained.net.xml';demand=batch/'inputs/C_sustained.rou.xml';runs=[]
    for rid,mode,duration,role in [('LF1','sequential',120.,'Unoptimized reference for identical-input observation and cost'),('LF2','batch',120.,'Candidate read-only transport: every field/every internal step paired equality before adoption'),('LF3','batch',300.,'Longer fixed local descriptive following/measurement coverage; not calibration window')]:
        spec=make_spec(batch,'C','local_diagnostic',net,demand,duration)
        spec['run_id']='lf1_'+rid;cfg=config(batch,spec['run_id'],net,demand,duration);spec['config']=cfg.relative_to(batch).as_posix()
        spec.update(reader_mode=mode,role=role,local_space=dict(edge='main_1',start_m=50.,end_m=250.,lanes=3,lane_km=.6));runs.append(spec)
    write(batch/'local_measurement_contract.json',dict(version=VERSION,space=LOCAL_SPACE,internal_step_s=.05,recorded_point_s=.1,
        local_filter_after_full_network_leader_resolution=True,identity='Run-scoped fresh unique incarnation; actual same-clock leader row',
        closing='follower minus leader, m/s; epsilon1e-3 inherited',gap='TraCI distance + follower minGap; independently same-lane physical rear minus follower front',
        sampling='Every .05s numerical/state audit, even ticks .1s P2 core; full global context retained',
        edge_or_lane_change='Record actual edge vs same-edge lane transition; does not itself redefine P2 identity rule',
        quality='Approved measurement_status valid/not_applicable/invalid/missing; missing is aliased not_measurable only in observation_quality',
        exposure='Stage0.2 inherited reliable adjacent same follower/leader/time .1s; evaluable endpoints statuses valid/not_applicable',
        local_attribution='Unresolved: event onset vs confirmation vs fully-contained; endpoint containment exposure is audit alternative only',
        formal_local_P2='Unresolved',formal_local_rate='Not Calculated',scientific_evaluation_window='Not Approved',warmup='None applied; entire engineering acquisition support described',
        old_C_entry_spillback='Evidence Insufficient; no retrospective upgrade'))
    plan=dict(result_id=RESULT_ID,version='lf-exploration-plan-v1',contract_version=VERSION,**SCIENCE,
        task_mode='independent_local_descriptive_exploration_only',runs=runs,main_matrix_allowed=False,formal_calibration_allowed=False,
        local_space=LOCAL_SPACE,seed=20261019,second_seed='Not Planned',initialization='Empty fresh network; entire acquisition interval, no approved warmup/evaluation choice',
        demand='Unchanged823 engineering vehicles scheduled0..600; only due demand counted pending in shorter runs',
        network='Original-scale generic C; original23.8/6.2/30 signal; no C/D comparison or geometry realism claim',
        thresholds='Inherited exact1e-6, source5e-6 near-zero at.05, existing queue5/.1/2/10/50/2 unchanged, Stage0.2 TTC2/span.2/epsilon1e-3 unchanged',
        limits=dict(per_run_wall_s=600,batch_wall_s=7200,memory_bytes=3*1024**3,artifact_bytes=2*1024**3),
        budget=dict(previous_targeted_attempts=0,max_remaining_at_start=8,planned=3,new_integration_micro_allowed=0,all_diagnostic_attempts_consume_budget=True),
        success='Paired all-state/context equality (exact, NaNs equal), no shared blocker; full raw/summary fingerprints; local point/continuity computability, no forced positive risk',
        LF3_activation='Paired equality required, no global blocker, candidate observed row cost * conservative scheduled vehicle-time bound for300s <540s; else Not Attempted',
        stop_on=['source/binary/config/plan SHA','identity/time/control/collision/teleport','conservation','exact/range/shared gap-coordinate conflict','batch protocol or paired field mismatch','worker/schema/resource failure'],
        cost_estimate=dict(reference='Prior CD C54,849 rows/82.29 worker seconds; D7,930/18.57. Forecasts only, no full600 run claimed',
            pair_worker_wall_upper_s=1200,LF3_worker_wall_upper_s=600,total_worker_wall_upper_s=1800,full600='Forecast only, not planned in this finite task',
            P2_analysis_wall_budget_s=900,queue_rules_unchanged=True),
        scientific_exclusions=['Entry spillback causality','Cross-junction upstream risk propagation','C/D capacity/risk comparison','Calibration/coverage/tolerances','ABCD/Stage0.5.5/Lock/StageI-II'])
    plan['frozen_files']={p.relative_to(batch).as_posix():sha(p) for folder in ['runtime','inputs','official_source'] for p in sorted((batch/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for n in ['preparation_manifest.json','source_audit.json','isolation_policy.json','protocol_source_audit.json','lf_source_staging.json','offline_CD_C_staging.json','lf_preparation.json','preflight.json','local_measurement_contract.json','dependency_fingerprints.json','gap_offline_analysis.json']:plan['frozen_files'][n]=sha(batch/n)
    write(batch/'experiment_plan.json',plan);(batch/'PLAN_SHA256').write_text(sha(batch/'experiment_plan.json')+'  experiment_plan.json\n')
    write(batch/'execution_ledger.json',dict(closed=False,global_stop=None,started_epoch=None,runs=[dict(run_id=r['run_id'],status='not_attempted') for r in runs]))
    print('LF_FROZEN '+sha(batch/'experiment_plan.json'),flush=True)


def offline_gap(batch):
    import pandas as pd
    from .stage_0_5_b12_network import coordinate_support
    metadata=batch/'inputs/CD_metadata';w=read(metadata/'queue_integration_diagnostics.json')['disconnected_component_witness']
    df=pd.read_parquet(batch/'inputs/prior_CD_C/internal_states.parquet');last=df[df.time_s==w['time_s']].copy()
    support=coordinate_support(batch/'inputs/C_micro.net.xml')
    last['coordinate']=[support['lanes'][lane]['offset_m']+x if lane in support['lanes'] else float('nan') for lane,x in zip(last.lane_id,last.position_m)]
    last['rear']=last.coordinate-last.length_m
    inlet,anchor=w['source_components'];front=last[last.incarnation_id.isin(inlet['members'])].sort_values('coordinate').iloc[-1]
    rear=last[last.incarnation_id.isin(anchor['members'])].sort_values('rear').iloc[0]
    mapping=support['lanes'];remaining=mapping[front.lane_id]['length_m']-front.position_m
    internal=mapping[rear.lane_id]['offset_m']-(mapping[front.lane_id]['offset_m']+mapping[front.lane_id]['length_m'])
    downstream_rear=rear.position_m-rear.length_m;independent=remaining+internal+downstream_rear
    actual=rear.rear-front.coordinate
    if abs(independent-actual)>1e-10 or abs(actual-w['physical_net_gap_m'])>1e-10:raise ValueError('gap_geometry_recomputation_mismatch')
    net=ET.parse(batch/'inputs/C_micro.net.xml').getroot()
    connections=[dict(c.attrib) for c in net.findall('connection') if c.get('from')=='main_0' and c.get('to')=='main_1']
    junctions=[dict(id=j.get('id'),type=j.get('type'),shape=j.get('shape'),requests=[dict(r.attrib) for r in j.findall('request')]) for j in net.findall('junction') if j.get('id')=='hwy_j1']
    source=(batch/'official_source/microsim_MSVehicle.cpp').read_text(encoding='utf-8').splitlines()
    refs=[dict(line=i+1,text=s.strip()) for i,s in enumerate(source) if 'keepClear(' in s or 'link->hasFoes()' in s]
    write(batch/'gap_offline_analysis.json',dict(observation=dict(time_s=w['time_s'],path=w['path'],upstream_vehicle=front.vehicle_id,downstream_vehicle=rear.vehicle_id,
        front_lane=front.lane_id,front_position_m=float(front.position_m),upstream_front_coordinate_m=float(front.coordinate),
        rear_lane=rear.lane_id,downstream_front_position_m=float(rear.position_m),downstream_length_m=float(rear.length_m),downstream_rear_coordinate_m=float(rear.rear),
        remaining_upstream_lane_m=float(remaining),explicit_internal_path_m=float(internal),downstream_lane_rear_position_m=float(downstream_rear),
        independent_gap_m=float(independent),queue_witness_gap_m=w['physical_net_gap_m'],no_simple_normal_edge_sum=True,
        physical_position_and_odometer_audit=read(metadata/'C_summary.json')['mapping_checks']),
        network=dict(connections=connections,junctions=junctions),source_references=refs,
        interpretation='Real model-path spatial gap, reproduced from original vehicle fronts/lengths plus explicit internal geometry. Not an ID/lane membership or omitted-junction artefact',
        keep_clear=dict(source_requires='link->hasFoes() AND link->keepClear(), then wait-time setting permits',
            actual_private_branch_logged=False,compiled_link_keep_clear_observed=False,causal_activation='Unresolved',
            compatible_evidence='Upstream front near junction stop line and downstream queue; network foes/priority context recorded',
            alternatives=['keep-clear/blocked downstream link planning','other native link/priority stopping context; no ablation performed']),
        insertion='Independent upstream physical entry obstruction/pending; does not prove the junction stopping cause',
        engineering_candidate_limit='10m connection cannot bridge this actual gap; retain2s and10m; no retrospective spillback upgrade',
        historical_C_entry_spillback='Evidence Insufficient',new_SUMO_runs=0))
    print('LF_OFFLINE_GAP '+str(float(independent)),flush=True)


def assert_scope(p):
    if p['version']!='lf-exploration-plan-v1' or p['main_matrix_allowed'] or p['formal_calibration_allowed'] or len(p['runs'])!=3:raise PermissionError('scope')
    if p['budget']['max_remaining_at_start']!=8 or p['budget']['new_integration_micro_allowed']!=0:raise PermissionError('budget')
    if any(r['duration_s']>600 or r['kind']!='C' or r['seed']!=20261019 for r in p['runs']):raise PermissionError('run_scope')
    if [(r['run_id'],r['reader_mode']) for r in p['runs']]!=[('lf1_LF1','sequential'),('lf1_LF2','batch'),('lf1_LF3','batch')]:raise PermissionError('pair_modes')
    if len({(r['network'],r['demand']) for r in p['runs']})!=1 or p['runs'][0]['duration_s']!=p['runs'][1]['duration_s']:raise PermissionError('paired_input_mismatch')


def summary_stop(summary,run_id,plan_sha):
    stop=validate_summary(summary)
    if stop:return stop
    if summary.get('plan_sha256')!=plan_sha:return 'summary_plan_SHA'
    if summary.get('run_id')!=run_id:return 'summary_run_identity'
    return None


def load_plan(batch):
    from .stage_0_5_exploratory_response import verify_frozen
    p=read(batch/'experiment_plan.json')
    if sha(batch/'experiment_plan.json')!=(batch/'PLAN_SHA256').read_text().split()[0]:raise PermissionError('plan_SHA')
    verify_frozen(batch,p['frozen_files'])
    assert_scope(p)
    if sha(_sumo_binary())!=read(batch/'preparation_manifest.json')['sumo_binary_sha256']:raise PermissionError('SUMO_binary_SHA')
    return p


def execute(batch,run_id):
    p=load_plan(batch);l=read(batch/'execution_ledger.json');s=next(r for r in p['runs'] if r['run_id']==run_id);e=next(r for r in l['runs'] if r['run_id']==run_id)
    if l['closed'] or l['global_stop'] or e['status']!='not_attempted':raise PermissionError('stop_or_no_retry')
    if run_id=='lf1_LF2' and l['runs'][0]['status'] not in ['completed_valid','completed_with_diagnostic_warning']:raise PermissionError('reference_not_completed')
    if run_id=='lf1_LF3' and not read(batch/'paired_equivalence.json')['LF3_allowed']:raise PermissionError('paired_admission_incomplete')
    if l['started_epoch'] is None:l['started_epoch']=time.time()
    remaining=7200-(time.time()-l['started_epoch'])
    if remaining<=0:raise TimeoutError('task_wall')
    write(batch/'execution_ledger.json',l)
    spec=dict(run_id=run_id,command=[sys.executable,'-S',str(batch/'runtime/code/scripts/run_stage_0_5_local_following.py'),'worker','--batch',str(batch),'--run-id',run_id],
        verify_files={str(batch/s[k]):p['frozen_files'][s[k]] for k in ['network','demand','config']})
    result=execute_commands(batch/'runs',[spec],limits=dict(p['limits'],batch_wall_s=remaining));e.update(result['runs'][0])
    path=batch/'runs'/run_id/'summary.json';summary=read(path) if path.exists() else None
    stop='worker_resource_failure' if e['status']=='failed' else summary_stop(summary,run_id,sha(batch/'experiment_plan.json'))
    if stop:l['global_stop']=dict(run_id=run_id,reason=stop)
    write(batch/'execution_ledger.json',l);write(batch/(run_id+'_ledger.json'),result)


def paired(batch):
    import pandas as pd
    import numpy as np
    plan=load_plan(batch);l=read(batch/'execution_ledger.json')
    if l['global_stop']:raise PermissionError('global_stop')
    dirs=[batch/'runs'/('lf1_'+n) for n in ['LF1','LF2']]
    a,b=[pd.read_parquet(d/'internal_states.parquet').sort_values(['time_s','vehicle_id']).reset_index(drop=True) for d in dirs]
    ignored=['run_id','incarnation_id'];columns=[c for c in a if c not in ignored];mismatches=[]
    if len(a)!=len(b) or set(a)!=set(b):mismatches.append('shape_or_columns')
    else:
        for c in columns:
            equal=(a[c].eq(b[c])|(a[c].isna()&b[c].isna())).all()
            if not equal:mismatches.append(c)
    summaries=[read(d/'summary.json') for d in dirs]
    for key in ['first_times','actual_inserted','actual_exited','present','pending_end','queue_state_counts','lane_changes','mapping_checks','physical_gap_checks','traffic']:
        if summaries[0][key]!=summaries[1][key]:mismatches.append('summary.'+key)
    sa,sb=[s['numerical'] for s in summaries]
    if sa['classifications']!=sb['classifications'] or sa['max_abs_residual_m']!=sb['max_abs_residual_m']:mismatches.append('numerical')
    wall=summaries[1]['runtime']['total_worker_wall_s'];rows=summaries[1]['runtime']['internal_state_rows']
    # True conservative residence upper bound: each due vehicle stays on road
    # from its scheduled departure until acquisition end, ignoring all exits.
    defs=ET.parse(batch/plan['runs'][0]['demand']).getroot().findall('vehicle')
    def bound(duration):return sum(max(0.,duration-float(v.get('depart'))) for v in defs)*20
    forecast300=wall/rows*bound(300.) if rows else None;forecast600=wall/rows*bound(600.) if rows else None
    allowed=not mismatches and forecast300 is not None and forecast300<540 and all(not s['engineering_blockers'] for s in summaries)
    write(batch/'paired_equivalence.json',dict(passed=not mismatches,rows_compared=len(a),columns_compared=columns,ignored_only_run_identity_labels=ignored,
        mismatches=mismatches,source_plan_sha256=sha(batch/'experiment_plan.json'),all_numeric_values_exact_equal=True if not mismatches else False,
        baseline=summaries[0]['transport'],optimized=summaries[1]['transport'],worker_wall_s=[s['runtime']['total_worker_wall_s'] for s in summaries],
        conservative_forecast_300_wall_s=forecast300,conservative_forecast_600_wall_s=forecast600,forecast_not_measurement=True,
        LF3_allowed=bool(allowed),zero_micro_budget_reused=True))
    if mismatches:
        l['global_stop']=dict(reason='paired_observation_mismatch',columns=mismatches);write(batch/'execution_ledger.json',l)
    print('LF_PAIRED '+str(not mismatches)+' LF3 '+str(bool(allowed)),flush=True)


def dispatch(repo,batch,cmd,run_id=None):
    if cmd=='prepare':return prepare(repo,batch)
    environment(batch)
    if cmd=='tests':return tests(batch)
    if cmd=='freeze':return freeze(batch)
    if cmd=='offline':return offline_gap(batch)
    if cmd=='run':return execute(batch,run_id)
    if cmd=='paired':return paired(batch)
    if cmd=='worker':
        from .stage_0_5_lf_worker import run_worker
        return run_worker(batch,run_id)
    if cmd=='close':
        l=read(batch/'execution_ledger.json');l['closed']=True
        for e in l['runs']:
            if e['status']=='not_attempted':e['reason']='Frozen activation or resource criterion not met; no search/retry'
        write(batch/'execution_ledger.json',l);return
    raise PermissionError('local_diagnostics_only')
