from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_stage_0_5_week_scene_v1 import finite_summary,analyze


def test_empty_or_missing_summary_is_not_observed_zero():
    assert finite_summary([None,float('nan'),'bad'])==dict(n=0,mean=None,quantiles=None)
    result=finite_summary([None,0,2])
    assert result['n']==2 and result['mean']==1


def test_seal_drift_rejects_before_any_trajectory_analysis(tmp_path):
    work=tmp_path/'run';work.mkdir();(work/'fcd.xml').write_text('<fcd-export/>')
    (work/'isolation_runtime.json').write_text(json.dumps(dict(artifact_sha256={'fcd.xml':'0'*64})))
    (tmp_path/'proposal.json').write_text(json.dumps(dict(runs=[dict(artifact_path='run')])))
    with pytest.raises(ValueError,match='sealed_output_drift:fcd.xml'):
        analyze(tmp_path,'proposal.json',tmp_path/'diagnostic')
    assert not (tmp_path/'diagnostic/audit.json').exists()
