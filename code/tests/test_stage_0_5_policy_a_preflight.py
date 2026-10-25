import importlib.util
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pytest


def module(name):
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    sys.path.insert(0,str(scripts))
    spec=importlib.util.spec_from_file_location(name,scripts/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def test_ramp_pulse_preserves_all_other_inputs_and_blocks(tmp_path):
    m=module('prepare_stage_0_5_policy_a');source=tmp_path/'routes.xml';target=tmp_path/'new.xml'
    source.write_text('<routes><vType id="t"/><route id="entering" edges="onramp main_1 main_2"/><vehicle id="i1" route="entering" depart="0" type="t"/><vehicle id="m1" route="through" depart="10" type="t"/><vehicle id="r1" route="entering" depart="1" type="t"/><vehicle id="r2" route="entering" depart="59" type="t"/><vehicle id="r3" route="entering" depart="61" type="t"/></routes>')
    result=m.pulse_routes(source,target);rows={x.get('id'):x.attrib for x in ET.parse(target).getroot().findall('vehicle')}
    assert result['changed_departures']==3
    assert rows['i1']['depart']=='0' and rows['m1']['depart']=='10'
    assert [rows[k]['depart'] for k in ['r1','r2','r3']]==['20.00','25.00','80.00']


def test_supervisor_requires_exact_confirmation_before_launch(tmp_path,monkeypatch):
    m=module('supervise_stage_0_5_diagnostic');p=tmp_path/'proposal.json';p.write_text('{}')
    monkeypatch.setattr(m.subprocess,'Popen',lambda *a,**k:pytest.fail('must not launch'))
    with pytest.raises(PermissionError,match='confirmation_required'):
        m.run_authorized_attempt(tmp_path,p,{},'ID1',tmp_path/'run',tmp_path,tmp_path/'ledger.json','sumo','tools')
    assert not (tmp_path/'ledger.json').exists()


def test_budget_counts_failures_and_blocks_retries(tmp_path):
    m=module('supervise_stage_0_5_diagnostic');p=tmp_path/'ledger.json'
    m.reserve_attempt(p,'ID1','sha')
    with pytest.raises(PermissionError):m.reserve_attempt(p,'ID1','sha')
    with pytest.raises(PermissionError):m.reserve_attempt(p,'ID2','sha')
    d=json.loads(p.read_text());d['attempts'][0]['status']='verified';p.write_text(json.dumps(d))
    m.reserve_attempt(p,'ID2','sha')
    d=json.loads(p.read_text());d['attempts'][-1]['status']='verified';p.write_text(json.dumps(d))
    m.reserve_attempt(p,'ID3','sha')
    with pytest.raises(PermissionError):m.reserve_attempt(p,'ID4','sha')


def test_dependency_binding_rejects_null_and_uses_module_version_when_metadata_missing(monkeypatch):
    m=module('supervise_stage_0_5_diagnostic')
    monkeypatch.setattr(m.importlib.metadata,'version',lambda name:None)
    monkeypatch.setattr(m.importlib,'import_module',lambda name:type('Package',(),{'__version__':'25.0.1'})())
    assert m.dependency_version('pyarrow')=='25.0.1'
    m.verify_dependencies({'pyarrow':'25.0.1'})
    with pytest.raises(ValueError,match='dependency_version_changed'):
        m.verify_dependencies({'pyarrow':None})
    with pytest.raises(ValueError,match='dependency_version_changed'):
        m.verify_dependencies({'pyarrow':'24.0.0'})


def test_worker_accepts_windows_audit_shape_and_rejects_relaunch_or_other_binary(tmp_path):
    m=module('interaction_diagnostic_worker')
    binary=(tmp_path/'sumo.exe').resolve();processes=[]
    m.audit_process_launch((str(binary),'"'+str(binary)+'" -c run.sumocfg',None,None),binary,processes)
    assert processes==[str(binary)]
    with pytest.raises(PermissionError,match='only_one_fixed_SUMO_process'):
        m.audit_process_launch((str(binary),[str(binary)],None,None),binary,processes)
    for args in [(None,[sys.executable],None,None),(None,[],None,None),
                 (None,'"'+str(binary)+'" -c run.sumocfg',None,None)]:
        with pytest.raises(PermissionError,match='only_one_fixed_SUMO_process'):
            m.audit_process_launch(args,binary,[])


@pytest.mark.parametrize('values,reason',[(dict(elapsed=601),'wall_limit'),(dict(rss=4*1024**3),'process_tree_RSS_limit'),(dict(output_bytes=3*1024**3),'task_output_limit'),(dict(free_d=0),'disk_headroom_limit')])
def test_resource_stops(values,reason):
    m=module('supervise_stage_0_5_diagnostic')
    args=dict(elapsed=0,rss=0,output_bytes=0,free_c=10*1024**3,free_d=20*1024**3);args.update(values)
    assert m.resource_reason(**args)==reason
