"""Synthetic preparation replay; never reads the actual local LF outputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

def setup(tmp_path):
    root=Path(__file__).resolve().parents[2]
    s=importlib.util.spec_from_file_location('lf_summary_prepare',root/'code/scripts/prepare_stage_0_5_lf_protocol_summaries.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    upstream=tmp_path/'repo/evidence/results/RES-STAGE-0.5-CALIBRATION-GAPS-V1';upstream.mkdir(parents=True)
    entries=[]
    for name in ['diagnostics.json','unified_strata.json']:
        p=upstream/name;p.write_text('{}');entries.append(dict(path=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (upstream/'manifest.json').write_text(json.dumps(dict(files=entries)))
    batch=tmp_path/'capsule';batch.mkdir();(batch/'source_manifest.json').write_text(json.dumps(dict(files=[])))
    return m,tmp_path/'repo',batch,upstream

def test_summary_supplement_declares_both_before_copy(tmp_path):
    m,repo,batch,up=setup(tmp_path);assert m.supplement(repo,batch)['copied']==2
    d=json.loads((batch/'source_manifest.json').read_text())
    assert len(d['files'])==2 and all(e['role']=='calibration_summary' and e['declared_before_read'] for e in d['files'])
    assert (batch/'inputs/real_Aplus_strata.json').read_bytes()==b'{}'
    with pytest.raises(PermissionError):m.supplement(repo,batch)

def test_frozen_summary_capsule_cannot_be_modified(tmp_path):
    m,repo,batch,up=setup(tmp_path);p=batch/'source_manifest.json';before=p.read_bytes();(batch/'PLAN_SHA256').write_text('sealed')
    with pytest.raises(PermissionError):m.supplement(repo,batch)
    assert p.read_bytes()==before

def test_mismatched_summary_source_rejected_without_copy(tmp_path):
    m,repo,batch,up=setup(tmp_path);(up/'diagnostics.json').write_text('{"changed":true}')
    with pytest.raises(PermissionError):m.supplement(repo,batch)
    assert not (batch/'inputs/real_Aplus_diagnostics.json').exists()
    assert json.loads((batch/'source_manifest.json').read_text())['files'][0]['declared_before_read']
