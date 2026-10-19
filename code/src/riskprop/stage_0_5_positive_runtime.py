"""Frozen native braking probes only, maximum five variants and no retries."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .stage_0_5_boundary_bottleneck import _copy_runtime,execute_commands
from .stage_0_5_b12_runtime import environment,SCIENCE
from .stage_0_5_sumo import _sumo_binary,_netconvert_binary
from .stage_0_5_positive_near_zero import VERSION,check_plan,admission

RESULT_ID='RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def audit_source(batch):
    root=batch/'official_source';manifest=read(root/'source_manifest.json')
    for name,e in manifest.items():
        if sha(root/name)!=e['sha256']:raise PermissionError('official source SHA')
    text=(root/'microsim_MSVehicle.cpp').read_text(encoding='utf-8').splitlines()
    refs={token:[dict(line=i+1,text=line.strip()) for i,line in enumerate(text) if token in line] for token in ['myStopDist','newStopDist =','NUMERICAL_EPS_SPEED','getDeltaPos','processTraCISpeedControl','updateState(vNext)']}
    expected_assignments={1143,5829,5869,7409,7830}
    actual={i+1 for i,line in enumerate(text) if 'myStopDist =' in line}
    if actual!=expected_assignments:raise PermissionError('stop distance assignment review needed')
    if [i+1 for i,line in enumerate(text) if 'newStopDist =' in line]!=[2223,2620]:raise PermissionError('stop-distance alias assignments')
    for name in ['microsim_MSLaneChanger.cpp','microsim_MSLaneChangerSublane.cpp']:
        if 'myStopDist' in (root/name).read_text(encoding='utf-8'):raise PermissionError('friend mutation')
    header=(root/'microsim_MSVehicle.h').read_text(encoding='utf-8').splitlines()
    header_refs=[dict(line=i+1,text=line.strip()) for i,line in enumerate(header) if 'myStopDist' in line or 'friend class' in line]
    required=['myStopDist(std::numeric_limits<double>::max())','vSafe = getSpeed() + ACCEL2SPEED(myAcceleration)','fabs(vNext) < NUMERICAL_EPS_SPEED && (myStopDist > POSITION_EPS || (hasStops() && myCurrEdge == getNextStop().edge))']
    if any(not any(s in line for line in text) for s in required):raise PermissionError('source contract changed')
    result=dict(pinned_commit='fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3',source_verified=True,manifest=manifest,full_references=refs,
        header_and_friend_references=header_refs,
        all_stop_alias_references=[dict(line=i+1,text=line.strip()) for i,line in enumerate(text) if 'newStopDist' in line],
        private_assignment_paths=dict(constructor_doublemax=1014,resets_doublemax=[1143,5829,5869,7409],state_restore_zero=7830,
            alias_passed_to_planMoveInternal=2149,alias_default_doublemax=2223,alias_only_finite_assignment_for_first_scheduled_stop=2620),
        proof='Fresh lifecycle, no input/dynamic stops, state restore, route mutation, collision/teleport or special devices => no finite assignment path; myStopDist remains doubleMax',
        full_predicate='abs(u_pre)<0.1*NUMERICAL_EPS*TS AND (myStopDist>POSITION_EPS OR (hasStops AND current route iterator==next stop iterator))',
        numerical_epsilon=.001,position_epsilon_m=.1,threshold_mps=5e-6,strict_comparison=True,
        pipeline=['action finalizeSpeed OR nonaction start acceleration continuation','conditional snap','TraCI speed control then electric hybrid (excluded)','updateState signed final/getDeltaPos','public=max(final,0)'],
        ballistic=dict(final_nonnegative='h*(v0+u_final)/2',final_negative='-v0^2/(2*((u_final-v0)/h))',snap_zero='v0*h/2'),
        analytical_probe_design=dict(source='Krauss::stopSpeed uses actionStep as headway; MSCFModel maximumSafeStopSpeedBallistic',
            gap_formula='NUMERICAL_EPS + T*(v_depart+w)/2 + w*w/(2*decel)',T_s=.1,v_depart_mps=1.,decel_mps2=20.,stopline_offset_m=1.,
            not_an_observation='Nominal w never determines actual branch; no measured dx used in input or candidate reconstruction'),
        generic_stop_context_identifiable=False,public_stop_list_not_general_private_distance=True,
        no_debug_build=True,installed_binary_modified=False,policy_scientifically_approved=False)
    write(batch/'source_audit.json',result);return result

def prepare(repo,batch):
    if (batch/'preparation_manifest.json').exists():raise PermissionError('new capsule; never overwrite preparation')
    audit_source(batch)
    history=repo/'evidence/results/RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1';m=read(history/'manifest.json')
    names=['audit.json','micro_checkpoint.json','near_zero_source_contract.json','historical_status_preservation.json']
    binding={n:next(e['sha256'] for e in m['files'] if e['path']==n) for n in names}
    write(batch/'source_staging_manifest.json',dict(role='sealed engineering metadata and official source only',declared_before_copy=True,sources=binding,
        real_data_inputs=[],old_state_inputs=[],official_source_manifest_sha256=sha(batch/'official_source/source_manifest.json')))
    (batch/'inputs/history').mkdir(parents=True);(batch/'runs').mkdir(exist_ok=True)
    for n,digest in binding.items():
        if sha(history/n)!=digest:raise PermissionError('history SHA')
        shutil.copyfile(history/n,batch/'inputs/history'/n)
    _copy_runtime(repo,batch)
    todo=['stage_0_5_positive_near_zero','stage_0_5_positive_runtime','stage_0_5_positive_worker'];copied=set()
    while todo:
        name=todo.pop()
        if name in copied:continue
        p=repo/'code/src/riskprop'/(name+'.py');raw=p.read_text(encoding='utf-8');shutil.copyfile(p,batch/'runtime/code/src/riskprop'/p.name);copied.add(name)
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module and (repo/'code/src/riskprop'/(node.module+'.py')).is_file():todo.append(node.module)
    for n in ['test_stage_0_5_positive_near_zero.py','test_stage_0_5_near_zero_observability.py','test_stage_0_5_stopping_observability.py']:
        shutil.copyfile(repo/'code/tests'/n,batch/'runtime/code/tests'/n)
    shutil.copyfile(repo/'code/scripts/run_stage_0_5_positive_near_zero.py',batch/'runtime/code/scripts/run_stage_0_5_positive_near_zero.py')
    links=batch/'dependency_links';links.mkdir();dependencies=[]
    for name in ['numpy','pandas','pyarrow','psutil','pytest','packaging','dateutil']:__import__(name)
    import _winapi
    for name,module in list(sys.modules.items()):
        if '.' in name or not getattr(module,'__file__',None):continue
        p=Path(module.__file__).resolve()
        if 'site-packages' not in p.parts or p.is_relative_to(Path(sys.prefix).resolve()):continue
        if p.name=='__init__.py':
            targets=[p.parent]+list(p.parent.parent.glob(name.replace('_','-')+'-*.dist-info'))
            if (p.parent.parent/(name+'.libs')).is_dir():targets.append(p.parent.parent/(name+'.libs'))
            for target in targets:
                link=links/target.name
                if not link.exists():_winapi.CreateJunction(str(target),str(link))
                dependencies.append(str(target))
        else:shutil.copyfile(p,links/p.name)
    write(batch/'isolation_policy.json',dict(runtime_read_roots=[str(Path(sys.prefix).resolve()),str(Path(_sumo_binary()).resolve().parent.parent),os.environ.get('WINDIR','C:/Windows')]+dependencies,
          executables=[sys.executable,_sumo_binary(),_netconvert_binary()],python_no_site_required=True,os_complete_monitoring=False,no_real_data_inputs=True))
    write(batch/'preparation_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),copied_modules=sorted(copied),
          sumo_binary_sha256=sha(_sumo_binary()),netconvert_sha256=sha(_netconvert_binary()),source_manifest_sha256=sha(batch/'source_staging_manifest.json')))
    print('B12P_PREPARED',flush=True)

def tests(batch):
    environment(batch)
    p=subprocess.run([sys.executable,'-S',str(batch/'runtime/code/scripts/b1_guard_probe.py'),str(batch)],capture_output=True,text=True,timeout=30)
    if p.returncode:raise PermissionError('negative access probe')
    paths=sorted((batch/'runtime/code/tests').glob('test_*.py'))
    cmd=[sys.executable,'-S',str(batch/'runtime/code/scripts/b1_test_entry.py'),*[str(p) for p in paths],'-q','-c',str(batch/'runtime/code/pytest.ini'),'--rootdir',str(batch/'runtime/code'),
        '--basetemp',str(batch/'test_tmp'/str(time.time_ns())),'-o',f"cache_dir={batch/'runtime_cache/pytest'}"]
    p=subprocess.run(cmd,cwd=batch/'runtime/code',capture_output=True,text=True,timeout=180);audit=read(batch/'preflight_test_access_audit.json')
    passed=p.returncode==0 and not audit['denied']
    write(batch/'preflight.json',dict(passed=passed,command=cmd,output=p.stdout+p.stderr,exit_code=p.returncode,test_sha256={p.name:sha(p) for p in paths},access_audit=audit,
        guard_probe=read(batch/'guard_probe_result.json'),real_data_inputs=[],os_complete_monitoring=False))
    print(p.stdout+p.stderr,flush=True)
    if not passed:raise PermissionError('preflight failed')

def build_inputs(batch):
    folder=batch/'inputs/network';folder.mkdir()
    (folder/'nodes.nod.xml').write_text('<nodes><node id="a" x="0" y="0"/><node id="b" x="100" y="0" type="traffic_light"/><node id="c" x="200" y="0"/></nodes>')
    (folder/'edges.edg.xml').write_text('<edges><edge id="e0" from="a" to="b" numLanes="1" speed="27.78"/><edge id="e1" from="b" to="c" numLanes="1" speed="27.78"/></edges>')
    net=folder/'probe.net.xml';p=subprocess.run([_netconvert_binary(),'-n',str(folder/'nodes.nod.xml'),'-e',str(folder/'edges.edg.xml'),'-o',str(net),'--no-turnarounds','true'],capture_output=True,text=True,timeout=30)
    (folder/'build.log').write_text(p.stdout+p.stderr)
    if p.returncode:raise ValueError('network build')
    tree=ET.parse(net);root=tree.getroot();logic=root.find('tlLogic');width=len(logic.find('phase').attrib['state'])
    for c in list(logic):logic.remove(c)
    logic.set('programID','b12p_all_red');ET.SubElement(logic,'phase',dict(duration='30',state='r'*width));tree.write(net,encoding='utf-8',xml_declaration=True)
    length=float(root.find("edge[@id='e0']/lane").attrib['length'])
    runs=[]
    for i,w in enumerate([2e-6,4.8e-6,5e-6,5.2e-6,8e-6],1):
        kind=f'P{i}';run_id='b12p_'+kind;gap=.001+.1*(1.+w)/2+w*w/40
        route=batch/'inputs'/(run_id+'.rou.xml');r=ET.Element('routes')
        attrs=dict(id='probe',vClass='passenger',length='5',carFollowModel='Krauss',laneChangeModel='LC2013',tau='1',minGap='2.5',accel='2.6',decel='20',apparentDecel='20',emergencyDecel='20',sigma='0',maxSpeed='27.78',speedFactor='1',speedDev='0',actionStepLength='.1',sigmaStep='1',jmStoplineGap='1')
        ET.SubElement(r,'vType',attrs);ET.SubElement(r,'route',dict(id='r',edges='e0 e1'))
        ET.SubElement(r,'vehicle',dict(id='probe',type='probe',route='r',depart='0',departLane='0',departPos=format(length-1.-gap,'.17g'),departSpeed='1'))
        ET.ElementTree(r).write(route,encoding='utf-8',xml_declaration=True)
        cfg=batch/'inputs'/(run_id+'.sumocfg')
        cfg.write_text(f'<configuration><input><net-file value="network/probe.net.xml"/><route-files value="{route.name}"/></input><time><begin value="0"/><end value="2"/><step-length value=".05"/></time><processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/><collision.action value="warn"/></processing><seed value="20261019"/></configuration>')
        runs.append(dict(run_id=run_id,kind=kind,seed=20261019,duration_s=2.,network=net.relative_to(batch).as_posix(),demand=route.relative_to(batch).as_posix(),config=cfg.relative_to(batch).as_posix(),
            nominal_w_mps=w,design_stop_gap_m=gap,design_stopline_offset_m=1.,network_actual_lane_length_m=length,
            expected_role=['strict interior','near but strictly below','nominal equality; actual floating comparison only','near above control','above control'][i-1]))
    return runs

def freeze(batch):
    if (batch/'experiment_plan.json').exists():raise PermissionError('no plan overwrite')
    if not read(batch/'preflight.json')['passed']:raise PermissionError('preflight')
    runs=build_inputs(batch)
    plan=dict(version='b12p-plan-v1',result_id=RESULT_ID,contract_version=VERSION,task_mode='engineering_observability_and_admission_only',result_mode='exploratory_diagnostic_only',**SCIENCE,
        C_D_allowed=False,main_matrix_allowed=False,runs=runs,limits=dict(max_runs=5,per_run_wall_s=120,batch_wall_s=1800,memory_bytes=3*1024**3,artifact_bytes=1024**3),
        exact_tolerance_m=1e-6,internal_step_s=.05,action_step_s=.1,
        success='At least1 real nonaction positive strict-interior snap with all7 independent links, exact dx and complete SHA; no global error',
        missing_branch='Not Observed; continue only remaining predeclared fixtures; no search/retry',
        stop_on=['identity/time/control','source/config/binary SHA','exact dx or necessary range','collision/teleport','resource/output/worker failure','unexpected access'],
        known_limits=['no general private stop context','no imported success from negative branches','dx tolerance alone cannot distinguish small-speed alternatives; source/context/public velocity independently required'])
    check_plan(plan)
    plan['frozen_files']={p.relative_to(batch).as_posix():sha(p) for d in [batch/'runtime',batch/'inputs',batch/'official_source'] for p in sorted(d.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for n in ['source_audit.json','source_staging_manifest.json','preparation_manifest.json','preflight.json','isolation_policy.json']:plan['frozen_files'][n]=sha(batch/n)
    write(batch/'experiment_plan.json',plan);(batch/'PLAN_SHA256').write_text(sha(batch/'experiment_plan.json')+'  experiment_plan.json\n')
    write(batch/'execution_ledger.json',dict(closed=False,runs=[dict(run_id=r['run_id'],status='not_attempted') for r in runs]))
    print('B12P_FROZEN '+sha(batch/'experiment_plan.json'),flush=True)

def load_plan(batch):
    from .stage_0_5_exploratory_response import verify_frozen
    if sha(batch/'experiment_plan.json')!=(batch/'PLAN_SHA256').read_text().split()[0]:raise PermissionError('plan SHA')
    p=read(batch/'experiment_plan.json');check_plan(p);verify_frozen(batch,p['frozen_files'])
    if sha(_sumo_binary())!=read(batch/'preparation_manifest.json')['sumo_binary_sha256']:raise PermissionError('SUMO binary SHA')
    return p

def execute(batch):
    plan=load_plan(batch);ledger=read(batch/'execution_ledger.json')
    if ledger['closed'] or any(r['status']!='not_attempted' for r in ledger['runs']):raise PermissionError('no retries')
    commands=[dict(run_id=r['run_id'],command=[sys.executable,'-S',str(batch/'runtime/code/scripts/run_stage_0_5_positive_near_zero.py'),'worker','--batch',str(batch),'--run-id',r['run_id']],
        verify_files={str(batch/r[k]):plan['frozen_files'][r[k]] for k in ['network','demand','config']}) for r in plan['runs']]
    result=execute_commands(batch/'runs',commands,limits=plan['limits']);write(batch/'execution_ledger.json',dict(result,closed=True,plan_sha256=sha(batch/'experiment_plan.json')))

def checkpoint(batch):
    load_plan(batch);ledger=read(batch/'execution_ledger.json')
    if not ledger['closed']:raise PermissionError('closed execution required')
    summaries=[]
    for r in ledger['runs']:
        p=batch/'runs'/r['run_id']/'summary.json'
        if p.exists():summaries.append(read(p))
        elif r['status']!='not_attempted':summaries.append(dict(target_exact_count=0,engineering_blockers=['missing worker summary']))
    a=admission(summaries)
    if ledger.get('stop_reason'):a.update(target_branch_verified=False,target_status='Engineering Blocker')
    write(batch/'admission.json',dict(a,plan_sha256=sha(batch/'experiment_plan.json'),historical_B12N_admission_unchanged=True,debug_build_required='Not necessary if restricted branch verified; otherwise researcher feasibility decision'))
    print(json.dumps(a),flush=True)

def dispatch(repo,batch,cmd,run_id=None):
    if cmd not in ['prepare','tests','freeze','run','worker','checkpoint']:raise PermissionError('No integration or main matrix command')
    if cmd=='prepare':return prepare(repo,batch)
    environment(batch)
    if cmd=='tests':return tests(batch)
    if cmd=='freeze':return freeze(batch)
    if cmd=='run':return execute(batch)
    if cmd=='checkpoint':return checkpoint(batch)
    from .stage_0_5_positive_worker import run_worker
    return run_worker(batch,run_id)
