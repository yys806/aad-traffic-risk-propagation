"""Resealed false admission or erased failure must be rejected in pure Git."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT=Path(__file__).resolve().parents[2]
def verifier():
    spec=importlib.util.spec_from_file_location('cd_verify',ROOT/'code/scripts/verify_stage_0_5_cd_integration.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def fixture(tmp):
    for p in (ROOT/'evidence/results/RES-STAGE-0.5-CD-INTEGRATION-V1').iterdir():shutil.copyfile(p,tmp/p.name)
def reseal(tmp):
    entries=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in tmp.iterdir() if p.name not in ['manifest.json','SHA256SUMS']]
    (tmp/'manifest.json').write_text(json.dumps(dict(files=entries)))
    entries.append(dict(path='manifest.json',sha256=hashlib.sha256((tmp/'manifest.json').read_bytes()).hexdigest()))
    (tmp/'SHA256SUMS').write_text(''.join(f'{e["sha256"]}  {e["path"]}\n' for e in entries))
def test_cd_portable_independent_journeys_and_limits(tmp_path):
    fixture(tmp_path);r=verifier().verify(tmp_path)
    assert r['D_actual_journeys']==9 and r['actual_micro_runs']==2 and not r['main_matrix_runs']
@pytest.mark.parametrize('kind',['admission','history','bounded','gap','D_exit','D_event','D_failure','count','budget','gate'])
def test_resealed_false_result_rejected(tmp_path,kind):
    fixture(tmp_path)
    name=dict(admission='admission.json',history='historical_status_preservation.json',bounded='numerical_branch_coverage.json',gap='queue_integration_diagnostics.json',D_exit='D_exits.json',D_event='D_lane_changes.json',D_failure='prior_D_revalidation.json',count='numerical_branch_coverage.json',budget='run_manifest.json',gate='audit.json')[kind]
    p=tmp_path/name;d=json.loads(p.read_text(encoding='utf-8'))
    if kind=='admission':d['C_persistent_entry_spillback_qualified']=True
    elif kind=='history':d['B12N_integration_allowed']=True
    elif kind=='bounded':d['bounded_is_exact']=True
    elif kind=='gap':d['disconnected_component_witness']['physical_net_gap_m']=0.
    elif kind=='D_exit':d[0]['last_edge']='main_1'
    elif kind=='D_event':d[:]=[e for e in d if e['vehicle_id']!='v00000']
    elif kind=='D_failure':d['old_run_status']='completed_valid'
    elif kind=='count':d['all_adjacent_edges']+=1
    elif kind=='budget':d['additional_targeted_runs']=1
    elif kind=='gate':d['protocol_lock_allowed']=True
    p.write_text(json.dumps(d),encoding='utf-8');reseal(tmp_path)
    with pytest.raises(ValueError):verifier().verify(tmp_path)
