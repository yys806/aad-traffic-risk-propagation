"""Portable proof recomputation must reject resealed false inference/promotion."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT=Path(__file__).resolve().parents[2]
def verifier():
    s=importlib.util.spec_from_file_location('positive_verify',ROOT/'code/scripts/verify_stage_0_5_positive_near_zero.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def copy(tmp):
    for p in (ROOT/'evidence/results/RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1').iterdir():shutil.copyfile(p,tmp/p.name)
def reseal(tmp):
    e=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in tmp.iterdir() if p.name not in ['manifest.json','SHA256SUMS']]
    (tmp/'manifest.json').write_text(json.dumps(dict(files=e)))
    e.append(dict(path='manifest.json',sha256=hashlib.sha256((tmp/'manifest.json').read_bytes()).hexdigest()))
    (tmp/'SHA256SUMS').write_text(''.join(f'{x["sha256"]}  {x["path"]}\n' for x in e))

def test_actual_restricted_positive_result_recomputes(tmp_path):
    copy(tmp_path);r=verifier().verify(tmp_path)
    assert r['target_edges_recomputed']==2 and r['controls_recomputed']==3 and not r['C_D_allowed']

@pytest.mark.parametrize('kind',['terminal','acceleration','clock','context','position','control','link','gate','integrate','history','bounded','bundle','path'])
def test_resealed_false_proof_or_scope_change_is_rejected(tmp_path,kind):
    copy(tmp_path)
    name='target_edges.json' if kind in ['terminal','acceleration','clock','context','position','control','link'] else dict(gate='audit.json',integrate='admission.json',history='historical_status_preservation.json',bounded='numerical_branch_coverage.json',bundle='micro_input_bundle.json',path='manifest.json')[kind]
    p=tmp_path/name;d=json.loads(p.read_text(encoding='utf-8'))
    if kind=='terminal':d[0]['after']['speed_mps']=1e-10
    elif kind=='acceleration':d[0]['before']['acceleration_mps2']=0.
    elif kind=='clock':d[0]['after']['last_action_time_s']=d[0]['before']['time_s']
    elif kind=='context':d[0]['lifecycle_proof']['no_state_restore']=False
    elif kind=='position':d[0]['after']['position_m']+=.01
    elif kind=='control':d[0]['before']['traci_vehicle_control']=None
    elif kind=='link':d[0]['result']['admission_links']['source_input_SHA_verified']=False
    elif kind=='gate':d['scientific_claim_eligible']=True
    elif kind=='integrate':d['C_D_allowed']=True
    elif kind=='history':d['B12N_integration_allowed']=True
    elif kind=='bounded':d['bounded_is_exact']=True
    elif kind=='bundle':next(iter(d['files'].values()))['sha256']='0'*64
    elif kind=='path':d['files'][0]['path']='../escape.json'
    p.write_text(json.dumps(d),encoding='utf-8')
    if kind!='path':reseal(tmp_path)
    with pytest.raises(ValueError):verifier().verify(tmp_path)
