from pathlib import Path
import json
import runpy
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from assess_stage_0_5_existing_capsule_v1 import assess


def test_direct_entry_bootstraps_own_package_without_editable_install(monkeypatch):
    code=Path(__file__).resolve().parents[1]
    monkeypatch.setattr(sys,'path',[p for p in sys.path if str(code/'src') not in str(p)])
    runpy.run_path(str(code/'scripts/run_stage_0_5_admission_v3.py'),run_name='direct_entry_import_check')
    assert sys.path[0]==str(code/'src')


def test_no_existing_capsule_means_no_candidate_no_launch(tmp_path):
    (tmp_path/'proposal.json').write_text(json.dumps(dict(runs=[dict(artifact_path='missing')])) )
    with pytest.raises(ValueError,match='existing_sealed_capsule_required'):
        assess(tmp_path,'proposal.json',tmp_path/'assessment',tmp_path/'candidate')
    assert not (tmp_path/'assessment').exists() and not (tmp_path/'candidate').exists()
