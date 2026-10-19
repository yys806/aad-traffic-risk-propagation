"""Reject resealed policy promotion, omitted reads or erased boundary evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import pytest
ROOT=Path(__file__).resolve().parents[2]
def verifier():
    s=importlib.util.spec_from_file_location('lf_verify',ROOT/'code/scripts/verify_stage_0_5_local_following.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def copy(tmp):
    for p in (ROOT/'evidence/results/RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1').iterdir():shutil.copyfile(p,tmp/p.name)
def reseal(tmp):
    entries=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in tmp.iterdir() if p.name not in ['manifest.json','SHA256SUMS']]
    (tmp/'manifest.json').write_text(json.dumps(dict(files=entries)))
    entries.append(dict(path='manifest.json',sha256=hashlib.sha256((tmp/'manifest.json').read_bytes()).hexdigest()))
    (tmp/'SHA256SUMS').write_text(''.join(f'{e["sha256"]}  {e["path"]}\n' for e in entries))
def test_actual_lf_portable_preserves_scientific_limits(tmp_path):
    copy(tmp_path);r=verifier().verify(tmp_path)
    assert r['targeted_attempts']==3 and r['remaining']==5 and r['local_formal_P2']=='Unresolved'
@pytest.mark.parametrize('kind',['pair','reads','field','local_P2','exposure','geometry','counterexample','budget','Gate','spillback','numeric'])
def test_resealed_false_claim_rejected(tmp_path,kind):
    copy(tmp_path);name=dict(pair='paired_equivalence.json',reads='paired_equivalence.json',field='paired_equivalence.json',local_P2='local_following_results.json',exposure='local_following_results.json',geometry='gap_offline_analysis.json',counterexample='formal_adapter_break_counterexample.json',budget='budget_audit.json',Gate='audit.json',spillback='audit.json',numeric='numerical_branch_coverage.json')[kind]
    p=tmp_path/name;d=json.loads(p.read_text(encoding='utf-8'))
    if kind=='pair':d['passed']=False
    elif kind=='reads':d['optimized']['getter_requests']-=1
    elif kind=='field':d['columns_compared'].remove('acceleration_mps2')
    elif kind=='local_P2':d[0]['local_formal']['events']=0
    elif kind=='exposure':d[0]['engineering_core']['exposure']['formal_rate_eligible']=True
    elif kind=='geometry':d['observation']['explicit_internal_path_m']=0.
    elif kind=='counterexample':d['new_flag_preserving_interface_confirmed_events']=1
    elif kind=='budget':d['targeted_remaining']=8
    elif kind=='Gate':d['scientific_claim_eligible']=True
    elif kind=='spillback':d['C_entry_spillback']='Supported'
    else:d['bounded_is_exact']=True
    p.write_text(json.dumps(d),encoding='utf-8');reseal(tmp_path)
    with pytest.raises(ValueError):verifier().verify(tmp_path)
