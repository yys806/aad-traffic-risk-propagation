"""Actual C6/D1 acceptance functions on synthetic XML and replay; no SUMO."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import stage_0_5_execution_v2 as execution
import stage_0_5_acceptance_v3 as acceptance
import stage_0_5_admission_v3 as admission
from stage_0_5_identity_observation import IdentityObserver
from stage_0_5_isolation_v2 import Scope,sha
from stage_0_5_research_ledger import ResearchLedger,canonical,CHECKS


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else canonical(value)+b"\n")


def sample(**changes):
    return dict(dict(wall_s=0,process_tree_rss_bytes=1,free_c_bytes=6*1024**3,free_d_bytes=15*1024**3,
                     available_memory_bytes=5*1024**3,task_output_bytes=0),**changes)


@pytest.fixture(scope="module")
def material():
    ids=["i1","i2","i3","i4"]; positions=[13,23,113,123]
    net='<net><edge id="main_1"><lane id="main_1_1" index="1" length="211.64" speed="27.78"/></edge><edge id="main_2">'+''.join(f'<lane id="main_2_{i}" index="{i}" length="269.96" speed="10"/>' for i in range(5))+'</edge></net>'
    routes='<routes><vType id="t" length="4" maxSpeed="27.78"/><route id="r" edges="main_1"/>'+''.join(f'<vehicle id="{k}" type="t" route="r" depart="0" departLane="1" departPos="{pos}" departSpeed="0"/>' for k,pos in zip(ids,positions))+'</routes>'
    config='<configuration><input><net-file value="network.net.xml"/><route-files value="routes.rou.xml"/></input><time><begin value="0"/><end value="420"/><step-length value="0.05"/></time><processing><step-method.ballistic value="true"/><threads value="1"/></processing><output><fcd-output value="fcd.xml"/><device.fcd.period value="0.1"/><summary-output value="summary.xml"/><tripinfo-output value="tripinfo.xml"/><tripinfo-output.write-unfinished value="true"/><tripinfo-output.write-undeparted value="true"/></output><seed value="20261201"/></configuration>'
    fcd='<fcd-export>'+''.join(f'<timestep time="{i/10:.1f}">'+''.join(f'<vehicle id="{k}" lane="main_1_1" pos="{pos}" speed="0"/>' for k,pos in zip(ids,positions))+'</timestep>' for i in range(4200))+'</fcd-export>'
    trip='<tripinfos>'+''.join(f'<tripinfo id="{k}" depart="0" departLane="main_1_1" departPos="{pos}" departSpeed="0" departDelay="0" arrival="-1"/>' for k,pos in zip(ids,positions))+'</tripinfos>'
    frames=[]
    for tick in range(8401):
        f=dict(time_s=round(tick*.05,2),phase="initial_snapshot" if tick==0 else "after_simulationStep",loaded=[],departed=[],arrived=[],pending=[],active=ids if tick else [],teleport_start=[],teleport_end=[],discarded=None,native_departures={})
        if tick==0:
            for key in ["loaded","departed","arrived","teleport_start","teleport_end"]: f[key]=None
        elif tick==1:
            f.update(loaded=ids,departed=ids,native_departures={k:dict(actual_departure_s=0,depart_delay_s=0,post_step_speed_mps=0) for k in ids})
        if tick:
            f["controls"]=dict(applied_before_step_s=round((tick-1)*.05,2),native_clock_before_s=round((tick-1)*.05,2),target_mps=10,native_lane_limits={"main_2_"+str(i):10 for i in range(5)})
        frames.append(f)
    ref='t_block,y_block,states,D1_E_veh_s,support_status,elapsed_start_s,duration_s,y_start_m,y_end_m\n'+''.join(f'{t},{y},300,30,observed,{120+t*30},30,{150+y*100},{250+y*100}\n' for t in range(9) for y in range(2))
    return dict(ids=ids,positions=positions,inputs={"network.net.xml":net.encode(),"routes.rou.xml":routes.encode(),"run.sumocfg":config.encode()},fcd=fcd.encode(),trip=trip.encode(),frames=frames,ref=ref.encode())


def observed(material,frames=None):
    observer=IdentityObserver([dict(id=k,depart_s=0) for k in material["ids"]])
    for f in frames or material["frames"]: observer.ingest(f)
    for tick in range(4200):
        for k in material["ids"]: observer.observe_fcd(k,tick/10)
    observer.observe_tripinfo(material["trip"])
    return observer


def journal_bytes(frames):
    data=[]; previous=None
    for seq,f in enumerate(frames):
        e=dict(seq=seq,previous_sha256=previous,payload=f)
        previous=hashlib.sha256(canonical(e)).hexdigest();e['sha256']=previous;data.append(canonical(e)+b'\n')
    return b''.join(data)


def kernel(binding):
    return dict(kind="synthetic_kernel_transcript",binding_sha256=binding,transcript_sha256="d"*64,
                probes=dict.fromkeys(["files_read_only","exclusive_output","forbidden_resources_denied","children_confined","process_tree_limited","network_confined"],True))


@pytest.fixture
def capsule(tmp_path,material):
    work=tmp_path/'out'; work.mkdir()
    for n,data in material['inputs'].items():write(work/n,data)
    write(tmp_path/'reference.csv',material['ref'])
    obs=observed(material); summary=obs.finish()
    for n,data in {'fcd.xml':material['fcd'],'tripinfo.xml':material['trip'],'identity_events.jsonl':journal_bytes(obs.frames),'identity_summary.json':canonical(summary)}.items():write(work/n,data)
    scope=Scope(tmp_path,{'reference.csv':sha(tmp_path/'reference.csv')},'out')
    limits=json.loads((Path(__file__).resolve().parents[1]/'configs/stage_0_5_interaction_research_v2.json').read_bytes())['single_attempt_limits']
    run=dict(id='SYNTH_B00',condition='synthetic0750',seed=20261201,duration_s=420,evaluation_elapsed_s=[120,390],factors=dict(supply=False,ramp=False),
        supply_target_lanes=['main_2_'+str(i) for i in range(5)],lane_speed_schedule=[dict(start_s=0,end_s=420,speed_mps=10)],common_support_references=['reference.csv'])
    c=dict(work=work,scope=scope,run=run,validated_inputs=material['inputs'],resource_limits=limits,synthetic_only=True,binding_sha256='b'*64,isolation_transcript_sha256=['d'*64],
           runtime_evidence=dict(resource_samples=[sample(),sample()],run_finished_wall_s=0,exit_code=0,watchdog_failure=None,isolation=kernel('b'*64),
            sealed_artifacts={n:sha(work/n) for n in ['fcd.xml','tripinfo.xml','identity_events.jsonl','identity_summary.json']}))
    return c,summary


def test_actual_measurement_acceptance_all_eight_from_synthetic_evidence(capsule):
    c,identity=capsule
    result=execution.measure_completed_capsule(c,identity)
    assert all(result[k] is True for k in CHECKS), {k:result['verdicts'][k] for k in CHECKS if not result[k]}
    assert result['acceptance_scope']=='synthetic_replay_only'
    assert result['verdicts']['task_isolation']['evidence']['native_certificate'] is False
    assert len(result['verdicts']['all18_common_cells']['evidence']['cells'])==18


def test_full_context_onset_before_window_is_not_reassigned_at_confirmation(capsule):
    c,identity=capsule; path=c['work']/'fcd.xml';root=ET.fromstring(path.read_bytes())
    for frame in root:
        t=float(frame.get('time'));v=next(v for v in frame if v.get('id')=='i1')
        v.set('pos',str(13+5*min(max(t-119.9,0),.3)))
        v.set('speed','5' if 119.9<=t<=120.2 else '0')
    write(path,ET.tostring(root));c['runtime_evidence']['sealed_artifacts']['fcd.xml']=sha(path)
    result=execution.measure_completed_capsule(c,identity)
    assert result['full_context_events'] is True
    d=json.loads((c['work']/'D1_measurement.json').read_bytes())
    assert d['onset_events']==0 and d['left_continuing_risk_segments']==1
    event=next(e for e in d['events'] if e['vehicle_id']=='i1')
    assert abs(event['onset_s']-119.9)<1e-7 and abs(event['confirm_s']-120.1)<1e-7 and event['onset_in_window'] is False


@pytest.mark.parametrize('fault',['missing_frame','right_endpoint','zero_D1','unknown_id','broken_XML','artifact_drift','reference_cell','tripinfo_clock_conflict'])
def test_real_C6_acceptance_rejects_missing_support_and_sealed_drift(capsule,fault):
    c,identity=capsule; work=c['work']
    if fault=='reference_cell':
        data=(work.parent/'reference.csv').read_bytes().splitlines();write(work.parent/'reference.csv',b'\n'.join(data[:-1])+b'\n')
        c['scope'].bindings[work.parent/'reference.csv']=sha(work.parent/'reference.csv')
    elif fault=='tripinfo_clock_conflict':
        write(work/'tripinfo.xml',(work/'tripinfo.xml').read_bytes().replace(b'depart="0"',b'depart="1"',1))
        c['runtime_evidence']['sealed_artifacts']['tripinfo.xml']=sha(work/'tripinfo.xml')
    elif fault=='artifact_drift':
        with (work/'fcd.xml').open('ab') as s:s.write(b'\n')
    else:
        root=ET.fromstring((work/'fcd.xml').read_bytes())
        if fault in {'missing_frame','right_endpoint'}:root.remove(next(e for e in root if e.get('time')==('200.0' if fault=='missing_frame' else '390.0')))
        elif fault=='zero_D1':
            for step in root:
                for v in list(step)[1:]:step.remove(v)
        elif fault=='unknown_id':root[0][0].set('id','unknown')
        data=ET.tostring(root)
        if fault=='broken_XML':data=data[:-12]
        write(work/'fcd.xml',data);c['runtime_evidence']['sealed_artifacts']['fcd.xml']=sha(work/'fcd.xml')
    result=execution.measure_completed_capsule(c,identity)
    assert not all(result[k] for k in CHECKS)
    assert not result['all18_common_cells'] or not result['full_context_events']


@pytest.mark.parametrize('fault',['supply_not_applied','missing_resource','resource_limit','fake_native_certificate','identity_boolean_tamper','teleport_API_gap','exit_error'])
def test_real_acceptance_rejects_nonmeasurement_contract_failures(capsule,material,fault):
    c,identity=capsule
    if fault=='missing_resource':c['runtime_evidence'].pop('resource_samples')
    elif fault=='resource_limit':c['runtime_evidence']['resource_samples'][1]['wall_s']=601
    elif fault=='fake_native_certificate':c['runtime_evidence']['isolation'].update(kind='OS_enforced',backend='linux-userns')
    elif fault=='identity_boolean_tamper':identity['native_departure_clock_complete']=False
    elif fault=='exit_error':c['runtime_evidence']['exit_code']=7
    elif fault=='teleport_API_gap':
        frames=[json.loads(x)['payload'] for x in (c['work']/'identity_events.jsonl').read_bytes().splitlines()]
        frames[2]['teleport_start']=None
        rebuilt=observed(material,frames);identity.clear();identity.update(rebuilt.finish())
        write(c['work']/'identity_events.jsonl',journal_bytes(rebuilt.frames));write(c['work']/'identity_summary.json',canonical(identity))
        for n in ['identity_events.jsonl','identity_summary.json']:c['runtime_evidence']['sealed_artifacts'][n]=sha(c['work']/n)
    else:
        lines=(c['work']/'identity_events.jsonl').read_bytes().splitlines();frames=[json.loads(x)['payload'] for x in lines]
        frames[1]['controls']['native_lane_limits']['main_2_0']=9
        write(c['work']/'identity_events.jsonl',journal_bytes(frames));c['runtime_evidence']['sealed_artifacts']['identity_events.jsonl']=sha(c['work']/'identity_events.jsonl')
    result=execution.measure_completed_capsule(c,identity)
    expected={'supply_not_applied':'input_fidelity','missing_resource':'resource_limits','resource_limit':'resource_limits',
              'fake_native_certificate':'task_isolation','identity_boolean_tamper':'identity_clock',
              'teleport_API_gap':'initialization_accounting','exit_error':'resource_limits'}[fault]
    assert result[expected] is False


def test_tripinfo_mismatch_and_undeparted_not_discarded(material):
    o=IdentityObserver([dict(id='i1',depart_s=0)])
    o.ingest(dict(material['frames'][0],active=[],pending=['i1']))
    o.observe_tripinfo(b'<tripinfos><tripinfo id="i1" depart="-1" arrival="-1"/></tripinfos>')
    row=o.finish()['vehicles']['i1']
    assert row['state']=='pending_native' and row['discarded_at'] is None and row['actual_departure_s'] is None
    o=observed(material)
    with pytest.raises(ValueError,match='delay_mismatch|departure_mismatch'):
        o.observe_tripinfo(material['trip'].replace(b'depart="0"',b'depart="1"',1))


def test_native_control_boundaries_and_error_stop_are_mock_only(tmp_path):
    backend=execution.NativeBackend();speeds={};calls=[];clock={'t':180}
    def setter(lane,value):speeds[lane]=value;calls.append((lane,value))
    backend.connection=SimpleNamespace(lane=SimpleNamespace(setMaxSpeed=setter,getMaxSpeed=lambda lane:speeds[lane]),simulation=SimpleNamespace(getTime=lambda:clock['t']),simulationStep=lambda:None)
    run=dict(supply_target_lanes=['main_2_'+str(i) for i in range(5)],lane_speed_schedule=[dict(start_s=0,end_s=180,speed_mps=10),dict(start_s=180,end_s=240,speed_mps=5),dict(start_s=240,end_s=420,speed_mps=10)])
    assert backend.before_step(180,dict(run=run))['target_mps']==5
    clock['t']=240
    assert backend.before_step(240,dict(run=run))['target_mps']==10 and len(calls)==10
    backend.connection.lane.getMaxSpeed=lambda _:9
    clock['t']=180
    with pytest.raises(RuntimeError,match='supply_not_imposed'):backend.before_step(180,dict(run=run))
    log=tmp_path/'synthetic_console.log';log.write_text("Error: Vehicle 'i0007_i0007' cannot depart")
    backend.console_path=log
    with pytest.raises(RuntimeError,match='native_error_log'):backend.step()
    assert backend.process is None


def test_ramp_factor_contract_rejects_non_target_change():
    before=b'<routes><vType id="t"/><route id="entering" edges="onramp"/><vehicle id="m1" type="t" route="entering" depart="1"/><vehicle id="m2" type="t" route="entering" depart="2"/></routes>'
    after=before.replace(b'depart="1"',b'depart="20.00"').replace(b'depart="2"',b'depart="25.00"')
    assert admission.factor_routes(before,after,ramp=True)['ramp_planned']==2
    with pytest.raises(ValueError,match='attribute_scope'):
        admission.factor_routes(before,after.replace(b'depart="25.00"',b'depart="26.00"'),ramp=True)


def test_replay_executes_actual_acceptance_without_all_true_callback(tmp_path,material,monkeypatch):
    config=json.loads((Path(__file__).resolve().parents[1]/'configs/stage_0_5_interaction_research_v2.json').read_bytes())
    config.update(task_id=admission.TASK,ledger_path='journal/events.jsonl',output_root='outputs',historical_references=[])
    write(tmp_path/'budget.json',config); ledger=ResearchLedger(tmp_path,'budget.json',task_id=admission.TASK);ledger.initialize()
    for n,data in material['inputs'].items():write(tmp_path/n,data)
    write(tmp_path/'reference.csv',material['ref']);write(tmp_path/'plan.md',b'synthetic plan');write(tmp_path/'source.py',b'# synthetic fixture')
    write(tmp_path/'scope.json',dict(task_id=admission.TASK,input_and_test_resource_scope_accepted=True))
    run=dict(id='SYNTH_B00',seed=20261201,duration_s=420,evaluation_elapsed_s=[120,390],question='synthetic known truth',contrast='reference',condition='synthetic0750',
        factors=dict(supply=False,ramp=False),initialization_policy='synthetic',artifact_path='outputs/SYNTH_B00',input_files={n:n for n in material['inputs']},
        input_sha256={n:sha(tmp_path/n) for n in material['inputs']},supply_target_lanes=['main_2_'+str(i) for i in range(5)],
        lane_speed_schedule=[dict(start_s=0,end_s=420,speed_mps=10)],common_support_references=['reference.csv'])
    p=dict(task_id=admission.TASK,synthetic_test_only=True,execution_allowed=True,researcher_confirmed=True,protocol_frozen=True,
        budget_sha256=sha(tmp_path/'budget.json'),plan_path='plan.md',plan_sha256=sha(tmp_path/'plan.md'),plan_version='synthetic',
        source_sha256={'source.py':sha(tmp_path/'source.py')},measurement_reference_sha256={'reference.csv':sha(tmp_path/'reference.csv')},
        environment=execution.environment_binding(),git_commit='a'*40,worktree_sha256='b'*64,
        admission=dict(initialization_policy_approved=True,measurement_contract_approved=True,input_fidelity_approved=True),
        isolation=dict(accepted_for_new_task=True,report_path='scope.json',report_sha256=sha(tmp_path/'scope.json')),runs=[run])
    write(tmp_path/'proposal.json',p)
    approval=dict(task_id=admission.TASK,researcher_confirmed=True,decision_record='synthetic only',run_ids=[run['id']],proposal_sha256=sha(tmp_path/'proposal.json'))
    binding=hashlib.sha256(canonical(p)).hexdigest()
    backend=execution.ReplayBackend(material['frames'],outputs={'fcd.xml':material['fcd'],'tripinfo.xml':material['trip']},
                                   runtime_evidence=dict(isolation=kernel(binding),transcript_sha256=['d'*64]))
    state=execution.ExecutionAdapter(tmp_path,ledger,'reports').execute('proposal.json',approval,run['id'],backend=backend,resource_probe=sample)
    assert state['attempts'][run['id']]['status']=='measurement_accepted'
    result=json.loads((tmp_path/'outputs/SYNTH_B00/measurement_acceptance.json').read_bytes())
    assert all(result[k] for k in CHECKS) and result['acceptance_scope']=='synthetic_replay_only'
    with pytest.raises(execution.AdmissionRefused):
        execution.ExecutionAdapter(tmp_path,ledger,'reports').execute('proposal.json',approval,run['id'],backend=execution.ReplayBackend([]),resource_probe=sample)
    monkeypatch.setattr(execution.subprocess,'Popen',lambda *a,**k:pytest.fail('must not create native process'))
    with pytest.raises(execution.AdmissionRefused,match='native_test_override_forbidden'):
        execution.ExecutionAdapter(tmp_path,ledger,'reports').execute('proposal.json',approval,run['id'],resource_probe=sample,
            measurement=lambda *_:pytest.fail('native callback substitution forbidden'))
    failed_run=dict(run,id='SYNTH_FAILED',artifact_path='outputs/SYNTH_FAILED',replicate_of=run['id'],repeat_reason='explicit synthetic failure injection')
    failed_proposal=dict(p,runs=[failed_run]);write(tmp_path/'failure-proposal.json',failed_proposal)
    failed_approval=dict(approval,run_ids=['SYNTH_FAILED'],proposal_sha256=sha(tmp_path/'failure-proposal.json'))
    with pytest.raises(RuntimeError,match='synthetic_runner_failure'):
        execution.ExecutionAdapter(tmp_path,ledger,'reports').execute('failure-proposal.json',failed_approval,'SYNTH_FAILED',
            backend=execution.ReplayBackend(material['frames'],fail_at=1),resource_probe=sample)
    failed=ledger.snapshot()['attempts']['SYNTH_FAILED']
    assert failed['status']=='failed' and failed['artifact_sha256']
    assert all(sha(tmp_path/n)==h for n,h in failed['artifact_sha256'].items())
    retry=dict(failed_run,id='SYNTH_RETRY',artifact_path='outputs/SYNTH_RETRY');write(tmp_path/'retry.json',dict(p,runs=[retry]))
    retry_approval=dict(approval,run_ids=['SYNTH_RETRY'],proposal_sha256=sha(tmp_path/'retry.json'))
    with pytest.raises(execution.AdmissionRefused,match='failure_requires_explicit_review'):
        execution.ExecutionAdapter(tmp_path,ledger,'reports').execute('retry.json',retry_approval,'SYNTH_RETRY',backend=execution.ReplayBackend([]),resource_probe=sample)


@pytest.fixture
def technical_case(tmp_path,material):
    for n,data in material['inputs'].items():write(tmp_path/n,data)
    source={}
    for n in admission.MANDATORY_SOURCES:
        write(tmp_path/n,b'# explicitly synthetic source-binding fixture');source[n]=sha(tmp_path/n)
    tool={}
    for n in ['sumo.exe','_simulation.py','_vehicle.py','domain.py','connection.py','constants.py','tripinfo_file.xsd']:
        write(tmp_path/'tools'/n,b'non-executable binding fixture');tool[str(tmp_path/'tools'/n)]=sha(tmp_path/'tools'/n)
    write(tmp_path/'plan.md',b'synthetic plan');write(tmp_path/'isolation.json',dict(accepted_for_new_task=False))
    limits=json.loads((Path(__file__).resolve().parents[1]/'configs/stage_0_5_interaction_research_v2.json').read_bytes())['single_attempt_limits']
    write(tmp_path/'budget.json',dict(single_attempt_limits=limits))
    write(tmp_path/'deps.json',dict(files=tool));write(tmp_path/'reference.csv',material['ref'])
    write(tmp_path/'validation.json',dict(source_sha256=source,targeted=dict(exit_code=0),full=dict(exit_code=0)))
    run=dict(id='SYNTH_B00',duration_s=420,seed=20261201,evaluation_elapsed_s=[120,390],artifact_path='outputs/new',
        factors=dict(supply=False,ramp=False),input_files={n:n for n in material['inputs']},input_sha256={n:sha(tmp_path/n) for n in material['inputs']},
        paired_base_routes='routes.rou.xml',supply_target_lanes=['main_2_'+str(i) for i in range(5)],lane_speed_schedule=[dict(start_s=0,end_s=420,speed_mps=10)])
    p=dict(task_id=admission.TASK,source_sha256=source,external_file_sha256=tool,native_binary=str(tmp_path/'tools/sumo.exe'),
        measurement_reference_sha256={'reference.csv':sha(tmp_path/'reference.csv')},plan_path='plan.md',plan_sha256=sha(tmp_path/'plan.md'),
        budget_path='budget.json',budget_sha256=sha(tmp_path/'budget.json'),isolation=dict(accepted_for_new_task=False,report_path='isolation.json',report_sha256=sha(tmp_path/'isolation.json')),
        environment=execution.environment_binding(),native_environment={'SystemRoot':'C:/Windows'},traci_tools_root=str(tmp_path/'tools'),native_runtime_version=[22,'SUMO 1.26.0'],tool_version_source='synthetic fixture',
        runtime_dependency_manifest='deps.json',runtime_dependency_manifest_sha256=sha(tmp_path/'deps.json'),runs=[run])
    p.update(software_validation_path='validation.json',software_validation_sha256=sha(tmp_path/'validation.json'))
    write(tmp_path/'proposal.json',p)
    return tmp_path,p


def test_technical_checks_separate_engineering_from_expected_authorization(technical_case):
    root,p=technical_case
    report=admission.technical_preflight(root,root/'proposal.json','SYNTH_B00',resource_sample=sample())
    assert set(report['technical_errors'])=={'OS_native_isolation_not_accepted','native_build_remains_locked_pending_OS_acceptance_and_review'}
    assert 'researcher_confirmed_not_true' in report['authorization_pending'] and report['ready'] is False


@pytest.mark.parametrize('fault',['source','input','tool','environment','missing_input','missing_tool','missing_output','missing_environment','resource'])
def test_real_technical_preflight_rejects_drift_and_incomplete_bindings(technical_case,fault):
    root,p=technical_case
    if fault=='source':write(root/admission.MANDATORY_SOURCES[0],b'drift')
    elif fault=='input':write(root/'routes.rou.xml',b'drift')
    elif fault=='tool':write(root/'tools/domain.py',b'drift')
    elif fault=='environment':p['environment']['python_version']='drift'
    elif fault=='missing_input':p['runs'][0]['input_sha256']={}
    elif fault=='missing_tool':p['external_file_sha256']={}
    elif fault=='missing_environment':p['environment']={}
    elif fault=='missing_output':
        write(root/'run.sumocfg',material_config_without_tripinfo((root/'run.sumocfg').read_bytes()))
        p['runs'][0]['input_sha256']['run.sumocfg']=sha(root/'run.sumocfg')
    write(root/'proposal.json',p)
    report=admission.technical_preflight(root,root/'proposal.json','SYNTH_B00',resource_sample=sample(wall_s=601) if fault=='resource' else sample())
    expected={'source':'input_hash_drift','input':'input_hash_drift','tool':'input_hash_drift','environment':'environment_binding_drift',
        'missing_input':'inexact_input_file_map','missing_tool':'native_binary_binding_missing','missing_output':'tripinfo-output',
        'missing_environment':'packages','resource':'resource_preflight_failed'}[fault]
    assert report['ready'] is False and any(expected in e for e in report['technical_errors']),report


def material_config_without_tripinfo(data):
    root=ET.fromstring(data);node=root.find('output/tripinfo-output');root.find('output').remove(node)
    return ET.tostring(root)


@pytest.mark.parametrize('fault',['none','input','source','proposal'])
def test_versioned_package_hash_and_source_drift_detection(tmp_path,fault):
    from prepare_stage_0_5_admission_v3 import EVIDENCE,verify_package
    folder=tmp_path/EVIDENCE/'candidate-v1'
    write(tmp_path/'source.py',b'# synthetic source')
    p=dict(source_sha256={'source.py':sha(tmp_path/'source.py')},execution_allowed=False,researcher_confirmed=False,protocol_frozen=False,
           isolation=dict(accepted_for_new_task=False))
    write(folder/'proposal.json',p);write(folder/'input.xml',b'<synthetic/>')
    write(folder/'manifest.json',dict(files={n:sha(folder/n) for n in ['proposal.json','input.xml']},proposal_sha256=sha(folder/'proposal.json'),status='BLOCKED_ENGINEERING'))
    if fault=='input':write(folder/'input.xml',b'drift')
    elif fault=='source':write(tmp_path/'source.py',b'drift')
    elif fault=='proposal':write(folder/'proposal.json',dict(p,researcher_confirmed=True))
    if fault=='none':assert verify_package(tmp_path,folder,portable_only=True)['current_package_verified']
    else:
        with pytest.raises(ValueError,match='drift'):verify_package(tmp_path,folder,portable_only=True)


def test_current_CLI_cannot_create_native_process_even_with_execute_argument(tmp_path,monkeypatch):
    import run_stage_0_5_admission_v3 as cli
    monkeypatch.setattr(execution.subprocess,'Popen',lambda *a,**k:pytest.fail('native process forbidden'))
    assert cli.main(['execute','--proposal','nonexistent.json','--run-id','SYNTH_B00','--repo-root',str(tmp_path)])==2
