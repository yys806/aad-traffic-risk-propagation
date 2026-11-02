from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import backfill_p2_task7_source_timestamps as b
from verify_p2_task7_timestamp_backfill import independent_response

def fixture(actuator='s0'):
    t=np.array([29.95,30.,30.05,30.1]);v=np.full((4,3),10.);a=np.zeros_like(v)
    j=0 if actuator=='s0' else 2;v[2:,j]=[9.775,9.55];a[2:,j]=-4.5
    raw={'t':t,'v':v,'a':a,'native':v.copy()}
    audit={'status':'COMPLETE','actuated_source':actuator,'source_execution':30.,
        'controls':[{'vehicle':actuator,'method':'slowDown','time_s':30.}]}
    return raw,audit

def test_actual_deceleration_signature_does_not_require_native_divergence():
    raw,audit=fixture();r=b.source_record(raw,audit)
    assert r['status']=='Established' and r['corrected_interval']==[30.,30.05]
    assert r['signature_speed']==r['native_readback_at_signature']

def test_no_source_is_not_applicable_and_failure_remains_unknown():
    assert b.source_record({}, {'status':'COMPLETE','actuated_source':None})['status']=='Not Applicable'
    assert b.source_record({}, {'status':'FAILED_STOP'})['status']=='Unknown'

def test_decoy_column_and_actual_vs_specified_identity_are_distinct():
    raw,audit=fixture('decoy');audit['specified_source']='s0'
    r=b.source_record(raw,audit)
    assert r['actuator_column']==2 and r['corrected_interval']==[30.,30.05]

def test_missing_signature_never_returns_planned_time_as_onset():
    raw,audit=fixture();raw['a'][:]=0
    assert b.source_record(raw,audit)['corrected_interval'] is None
    raw,audit=fixture();audit['controls']=[]
    assert b.source_record(raw,audit)['status']=='Unknown'

def test_target_response_does_not_change_source_interval():
    raw,audit=fixture();first=b.source_record(raw,audit)
    raw['v'][:,1]=0;raw['a'][:,1]=-100
    assert b.source_record(raw,audit)==first

def test_strict_interval_touch_overlap_and_clock_sensitivity():
    assert b.ordering([0,1],[1,2])=='Unknown_overlap'
    assert b.ordering([0,1],[1.1,2],.05)=='Unknown_overlap'
    assert b.ordering([0,1],[1.1,2],.049)=='Pass'
    assert b.ordering(None,[1,2])=='Unknown_missing_interval'
    assert b.ordering([3,4],[1,2])=='Not_ordered_reverse'

def test_transition_does_not_turn_missing_evidence_into_negative():
    assert b.transition('Pass','Unknown_overlap')=='unresolved_after_correction'
    assert b.transition('Not_ordered_reverse','Pass')=='not_pass_to_pass'

def test_scalar_response_requires_full_span_and_resets_after_negative_sample():
    t=np.arange(29.95,33,.05);v=np.full(len(t),10.)
    v[(t>=30.05)&(t<31.05)]=8
    assert independent_response(t,v) is None
    v[(t>=31.2)&(t<=32.4)]=8
    result=independent_response(t,v)
    assert result is not None and result[1]>31
