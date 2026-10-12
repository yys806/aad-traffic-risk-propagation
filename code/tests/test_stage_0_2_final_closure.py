"""Independent numerical truth tests for final hardening."""
import itertools
import math
import pandas as pd
import pytest
from riskprop.formal_risk_measurement import *

def record(i, **changes):
    r = dict(time_s=i*.1, global_time_ms=100000+i*100, frame_id=i,
             diagnostic_clock_anchor_ms=100000, dataset='NGSIM', site='test',
             window_id='w', source_member='s', source_period='p', trajectory_id='f',
             leader_trajectory_id='l', identity_uncertain=False,
             leader_identity_uncertain=False, identity_break=False, observation_gap=False,
             leader_matched=True, vehicle_id=1, leader_id=2, leader_frame_id=i,
             lower=.4, upper=.4, ttc_valid=True,
             measurement_status='valid', ttc_s=1., drac_mps2=2., net_gap_m=5., original_row_number=i)
    r.update(changes)
    return r

def test_time_only_cannot_establish_coverage():
    d=pd.DataFrame([{'time_s':0.,'lower':.4,'upper':.4}, {'time_s':.1,'lower':.4,'upper':.4}])
    r=integrate_fixed_window(d,window_start_s=0.,window_end_s=.1)
    assert (r['lower_mean'],r['upper_mean']) == (0.,1.)

@pytest.mark.parametrize('changes',[{'leader_trajectory_id':'other'},{'diagnostic_clock_anchor_ms':1}, {'source_member':'other'}, {'identity_break':True}, {'observation_gap':True}, {'identity_uncertain':True}, {'frame_id':9}])
def test_every_boundary_prevents_integral(changes):
    r=integrate_fixed_window(pd.DataFrame([record(0),record(1,**changes)]),window_start_s=0.,window_end_s=.1)
    assert (r['lower_mean'],r['upper_mean']) == (0.,1.)

@pytest.mark.parametrize('bounds',[(float('nan'),1),(0,float('inf')),(-.1,.2),(.8,.2),(0,1.1)])
def test_illegal_contribution_rejected(bounds):
    d=pd.DataFrame([record(0,lower=bounds[0],upper=bounds[1]),record(1)])
    with pytest.raises(ValueError): integrate_fixed_window(d,window_start_s=0.,window_end_s=.1)

def test_no_extrapolation_clipping_and_duplicate_rejected():
    d=pd.DataFrame([record(1),record(2)])
    r=integrate_fixed_window(d,window_start_s=0.,window_end_s=.3)
    assert r['lower_integral']==pytest.approx(.04)
    assert r['upper_integral']==pytest.approx(.24)
    r=integrate_fixed_window(d,window_start_s=.125,window_end_s=.175)
    assert r['lower_mean']==pytest.approx(.4)
    with pytest.raises(ValueError):integrate_fixed_window(pd.concat([d,d]),window_start_s=0.,window_end_s=.3)

def test_scope_and_confirmation_members_are_unique():
    d=pd.DataFrame([record(i) for i in range(3)])
    collision=pd.concat([d,d.assign(source_member='other',trajectory_id='other')])
    with pytest.raises(ValueError): observed_confirmation_time(collision,[0,1,2],.2)
    assert observed_confirmation_time(collision,[0,1,2],.2,event_scope=record(0))==pytest.approx(.2)
    with pytest.raises(ValueError): observed_confirmation_time(d,[0,2],.2)
    with pytest.raises(ValueError): observed_confirmation_time(d.assign(ttc_s=[1,3,1]),[0,1,2],.2)

def test_spatial_reliability_independent_and_numpy_bool():
    assert contribution_bounds(measurement_status='invalid',in_region=False,ttc_s=None,reliable=False)==(0,0,None)
    assert contribution_bounds(measurement_status='valid',in_region=False,ttc_s=1,region_reliable=False)==(0,1,None)
    assert contribution_bounds(measurement_status='valid',in_region=True,ttc_s=1,measurement_reliable=False)==(0,1,None)

def test_full_window_product_equal_vehicles_and_corner_did_oracle():
    d=pd.DataFrame([record(0,lower=.8,upper=.8),record(1,lower=0,upper=0),record(2)])
    r=integrate_fixed_window(d,window_start_s=0.,window_end_s=.2)
    assert r['lower_mean']==pytest.approx(.5*.8)
    intervals=[{'lower_mean':.1,'upper_mean':.4},{'lower_mean':.2,'upper_mean':.6},{'lower_mean':.3,'upper_mean':.5},{'lower_mean':.4,'upper_mean':.7}]
    corners=[a-b-c+d for a,b,c,d in itertools.product(*[(x['lower_mean'],x['upper_mean']) for x in intervals])]
    assert did_interval(*intervals)==pytest.approx((min(corners),max(corners)))

def test_missing_clock_and_conflicting_timestamp_fail_closed():
    a,b=record(0),record(1)
    b.pop('diagnostic_clock_anchor_ms')
    assert not continuity_is_valid(a,b)
    assert not continuity_is_valid(a,record(1,global_time_ms=100900))
    assert not continuity_is_valid(a,record(1,source_member=None))

def test_explicit_native_vs_decimated_frame_steps():
    assert continuity_is_valid(record(0),record(2),expected_step_s=.2,expected_frame_delta=2)
    assert not continuity_is_valid(record(0),record(2),expected_step_s=.2,expected_frame_delta=1)

def test_confirmation_checks_members_after_confirmation():
    d = pd.DataFrame([record(i) for i in range(5)])
    d.loc[4, 'leader_trajectory_id'] = 'switched'
    with pytest.raises(ValueError):
        observed_confirmation_time(d, range(5), .2)

def test_extraction_allows_row_numbers_reused_across_sources():
    d = pd.DataFrame([record(i) for i in range(4)])
    both = pd.concat([d, d.assign(source_member='second')], ignore_index=True)
    events = extract_formal_source_events(both)
    assert len(events) == 2
    assert events.event_confirm_s.tolist() == pytest.approx([.2, .2])

@pytest.mark.parametrize('flag', ['identity_uncertain', 'leader_identity_uncertain', 'leader_matched', 'identity_break', 'observation_gap'])
def test_malformed_boolean_evidence_fails_closed(flag):
    assert not continuity_is_valid(record(0), record(1, **{flag: 'False'}))

@pytest.mark.parametrize('last_change,expected', [
    ({'ttc_s': 3.}, 'observed_threshold_exit'),
    ({'leader_trajectory_id': 'new'}, 'leader_switch_unknown_risk'),
    ({'measurement_status': 'missing', 'ttc_valid': False}, 'measurement_unavailable_unknown_risk'),
    ({'observation_gap': True, 'ttc_valid': False}, 'continuity_break_unknown_risk'),
])
def test_exit_observation_does_not_authorize_earlier_message(last_change, expected):
    d = pd.DataFrame([record(i) for i in range(3)] + [record(3, **last_change)])
    events = extract_formal_source_events(d)
    assert len(events) == 1
    assert events.iloc[0].exit_reason == expected
    assert events.iloc[0].event_end_s == pytest.approx(.2)
    assert events.iloc[0].message_earliest_generation_s == pytest.approx(.2)

def test_nonfinite_clock_is_not_evidence():
    assert not continuity_is_valid(record(0, diagnostic_clock_anchor_ms=math.inf),
                                   record(1, diagnostic_clock_anchor_ms=math.inf))
