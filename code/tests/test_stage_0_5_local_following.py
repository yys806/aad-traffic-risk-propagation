"""Analytical boundary expectations, never reads local traffic data."""
import pandas as pd
import pytest
from riskprop.stage_0_5_local_following import decorate,analyse,LOCAL_SPACE

def source(times=(0.,.1,.2),positions=(100.,101.,102.),leaders=None):
    rows=[]
    for i,(t,x) in enumerate(zip(times,positions)):
        lid=(leaders or ['l']*len(times))[i]
        for vid in ['f','l','m']:
            rows.append(dict(run_id='r',vehicle_id=vid,incarnation_id='r|'+vid,time_s=t,edge_id='main_1',lane_id='main_1_0',
                position_m=x if vid=='f' else x+6.,length_m=5.,speed_mps=10. if vid=='f' else 9.,acceleration_mps2=0.,
                leader_id=lid if vid=='f' else '',net_gap_m=1. if vid=='f' else None,leader_speed_mps=9. if vid=='f' and lid else None))
    return pd.DataFrame(rows)

def test_full_risk_span_and_actual_confirmation_are_distinct_from_point_count():
    r=analyse(source())
    assert r['point']['ttc_below_2_samples']==3
    assert r['engineering_core']['confirmed_events']==1
    assert r['engineering_events'][0]['event_confirm_s']==pytest.approx(.2)
    assert r['engineering_core']['exposure']['p2_evaluable_following_exposure_s']==pytest.approx(.2)
    assert r['local_formal']['events']=='Unresolved' and r['local_formal']['rate']=='Not Calculated'

def test_entry_boundary_has_two_distinct_event_assignment_candidates():
    r=analyse(source(positions=(49.,50.,51.)))
    assert r['point']['ttc_below_2_samples']==2
    assert r['local_candidates']['event_onset_inside']==0
    assert r['local_candidates']['event_confirmation_inside']==1
    assert r['local_candidates']['endpoint_contained_evaluable_exposure_s']==pytest.approx(.1)
    assert r['local_candidates']['risk_fragments']==1 and r['local_candidates']['fragments_meeting_02_span']==0

def test_leader_outside_region_remains_resolved_at_same_clock():
    df=source(positions=(249.,249.,249.));m=decorate(df)
    f=m[m.vehicle_id=='f']
    assert f.in_local.all() and f.leader_identity_status.eq('observed').all()
    assert f.measurement_status.eq('valid').all()

@pytest.mark.parametrize('leaders',[['l','m','l'],['l','','l'],['l','unknown','l']])
def test_leader_break_and_return_never_bridge_risk_or_exposure(leaders):
    r=analyse(source(leaders=leaders))
    assert r['engineering_core']['confirmed_events']==0
    assert r['engineering_core']['exposure']['p2_evaluable_following_exposure_s']==0.

def test_missing_frame_and_short_risk_do_not_confirm():
    r=analyse(source(times=(0.,.2,.3)))
    assert r['engineering_core']['confirmed_events']==0
    assert r['engineering_core']['exposure']['p2_evaluable_following_exposure_s']==pytest.approx(.1)
    assert analyse(source(times=(0.,.1),positions=(100.,101.)))['engineering_core']['confirmed_events']==0

def test_real_lane_change_is_not_membership_change_and_does_not_redefine_P2():
    df=source();df.loc[(df.vehicle_id=='f')&(df.time_s>=.1),'lane_id']='main_1_1'
    r=analyse(df)
    assert r['continuity']['actual_same_edge_lane_changes']==1 and r['engineering_core']['confirmed_events']==1

def test_legal_edge_progression_keeps_global_identity_but_leaves_local_support():
    df=source();df.loc[(df.vehicle_id=='f')&(df.time_s==.2),['edge_id','lane_id','position_m']]=['main_2','main_2_0',1.]
    r=analyse(df)
    assert r['continuity']['edge_changes']==1 and r['engineering_core']['confirmed_events']==1
    assert r['local_candidates']['event_fully_inside']==0

@pytest.mark.parametrize('field,value,status,quality',[
    ('net_gap_m',0.,'invalid','invalid'),('leader_speed_mps',None,'missing','not_measurable'),
    ('leader_speed_mps',10.,'not_applicable','not_applicable'),('leader_speed_mps',9.,'valid','valid')])
def test_quality_vocabulary_preserves_approved_status(field,value,status,quality):
    df=source();df.loc[df.vehicle_id=='f',field]=value;m=decorate(df);f=m[m.vehicle_id=='f']
    assert f.measurement_status.eq(status).all() and f.observation_quality.eq(quality).all()
    if status!='valid':assert f.ttc_s.isna().all()

def test_nonclosing_counts_evaluable_exposure_but_invalid_gap_does_not():
    df=source();df.loc[df.vehicle_id=='f','leader_speed_mps']=10.
    r=analyse(df);assert r['engineering_core']['exposure']['p2_evaluable_following_exposure_s']==pytest.approx(.2)
    df.loc[df.vehicle_id=='f','net_gap_m']=0.
    r=analyse(df);assert r['engineering_core']['exposure']['reliable_following_exposure_s']==pytest.approx(.2)
    assert r['engineering_core']['exposure']['p2_evaluable_following_exposure_s']==0.

def test_explicit_identity_break_must_reach_formal_core_not_be_erased():
    df=source();df['identity_break']=False;df.loc[(df.vehicle_id=='f')&(df.time_s==.1),'identity_break']=True
    assert analyse(df)['engineering_core']['confirmed_events']==0

def test_window_and_local_end_truncation_are_not_observed_risk_exit():
    r=analyse(source(positions=(248.,249.,250.)))
    assert r['engineering_events'][0]['exit_reason']=='observation_end_right_censored'
    assert r['local_candidates']['event_confirmation_inside']==0
    assert r['point']['local_samples']==2  # f2; both leaders are already outside

def test_duplicate_identity_clock_is_rejected():
    df=source()
    with pytest.raises(ValueError,match='duplicate'):decorate(pd.concat([df,df.iloc[:1]]))
