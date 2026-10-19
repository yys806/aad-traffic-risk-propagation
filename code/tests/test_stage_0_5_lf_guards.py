"""LF source/plan/summary fail-closed boundaries, synthetic dictionaries only."""
import pytest
from riskprop.stage_0_5_lf_runtime import assert_scope,summary_stop

def plan():
    return dict(version='lf-exploration-plan-v1',main_matrix_allowed=False,formal_calibration_allowed=False,
        budget=dict(max_remaining_at_start=8,new_integration_micro_allowed=0),
        runs=[dict(run_id='lf1_'+n,kind='C',seed=20261019,duration_s=d,reader_mode=m,network='n',demand='d') for n,d,m in [('LF1',120,'sequential'),('LF2',120,'batch'),('LF3',300,'batch')]])

@pytest.mark.parametrize('change',['seed','duration','matrix','micro','demand','mode'])
def test_scope_errors_rejected(change):
    p=plan()
    if change=='seed':p['runs'][1]['seed']=1
    elif change=='duration':p['runs'][2]['duration_s']=601
    elif change=='matrix':p['main_matrix_allowed']=True
    elif change=='micro':p['budget']['new_integration_micro_allowed']=1
    elif change=='demand':p['runs'][1]['demand']='different'
    else:p['runs'][0]['reader_mode']='batch'
    with pytest.raises(PermissionError):assert_scope(p)

def test_summary_missing_fields_or_wrong_SHA_blocks():
    p=plan();assert_scope(p)
    s=dict(status='completed_valid',global_blockers=[],scenario_blockers=[],engineering_blockers=[],evidence_insufficient=[],run_id='lf1_LF1',plan_sha256='sha')
    assert summary_stop(s,'lf1_LF1','sha') is None
    assert summary_stop(s,'lf1_LF1','wrong')=='summary_plan_SHA'
    assert summary_stop(s,'different','sha')=='summary_run_identity'
    del s['global_blockers']
    assert summary_stop(s,'lf1_LF1','sha') is not None
