"""Analytical counterexamples for candidate-only local protocol audits."""
import hashlib
import json
import pandas as pd
import pytest
from riskprop.stage_0_5_lf_protocol import event_audit, exposure_audit, candidate_rates, admission, verify_binding, cycle_diagnostics, validate_plan, clustered_rate

def points(positions=(40.,60.,70.,260.), *, times=(0.,.1,.2,.3)):
    return pd.DataFrame([dict(vehicle_id='v',incarnation_id='run|v',leader_id='l',leader_incarnation_id='run|l',time_s=t,
        edge_id='main_1',lane_id='main_1_0',position_m=x,in_local=50<=x<250,speed_mps=2.,
        reliable_following_eligible=True,measurement_status='valid',ttc_valid=True,ttc_s=1.,
        identity_break=False,observation_gap=False,observation_index=i) for i,(t,x) in enumerate(zip(times,positions))])

def event():return dict(incarnation_id='run|v',event_start_s=0.,event_confirm_s=.2,event_end_s=.3)

def test_onset_confirmation_and_two_containment_definitions():
    rows,counts=event_audit(points(),[event()])
    assert counts==dict(onset=0,confirmation=1,through_confirmation=0,through_end=0)
    m=points((60.,70.,80.,260.));rows,counts=event_audit(m,[event()])
    assert counts==dict(onset=1,confirmation=1,through_confirmation=1,through_end=0)
    assert rows[0]['confirm_position_m']==80. and rows[0]['end_position_m']==260.

@pytest.mark.parametrize('column,value',[('leader_incarnation_id','run|other'),('identity_break',True),('observation_gap',True),('ttc_s',3.),('measurement_status','invalid')])
def test_invalid_event_members_fail_closed(column,value):
    m=points();m.loc[1,column]=value
    with pytest.raises(ValueError):event_audit(m,[event()])

def test_duplicate_event_and_wrong_confirmation_rejected():
    with pytest.raises(ValueError):event_audit(points(),[event(),event()])
    e=event();e['event_confirm_s']=.3
    with pytest.raises(ValueError):event_audit(points(),[e])

def test_missing_frame_cannot_bridge():
    with pytest.raises(ValueError):event_audit(points(times=(0.,.1,.3,.4)),[dict(event(),event_end_s=.4)])

def test_boundary_denominator_not_vehicle_time_or_risk_points():
    d=exposure_audit(points())
    assert d['global_evaluable_s']==pytest.approx(.3)
    assert d['local_both_s']==pytest.approx(.1)
    assert d['local_left_s']==pytest.approx(.2) and d['local_right_s']==pytest.approx(.2)
    assert d['boundary_crossing_evaluable_s']==pytest.approx(.2)
    assert candidate_rates(dict(onset=1,confirmation=1,through_confirmation=0,through_end=0),d)['onset']['rate_per_evaluable_vehicle_hour']==pytest.approx(36000.)

def test_no_lane_break_and_cross_edge_membership_rechecked():
    m=points((60.,70.,80.,90.));m.loc[1,'lane_id']='main_1_1'
    assert exposure_audit(m)['local_both_s']==pytest.approx(.3)
    m.loc[3,['edge_id','lane_id','in_local']]=['main_2','main_2_0',False]
    assert exposure_audit(m)['local_both_s']==pytest.approx(.2)
    m.loc[3,'in_local']=True
    with pytest.raises(ValueError):exposure_audit(m)

def test_window_filter_does_not_manufacture_onset_and_keeps_lookahead():
    rows,c=event_audit(points((60.,70.,80.,90.)),[event()],window=(.1,.3))
    assert c['onset']==0 and c['confirmation']==1 and not rows[0]['onset_in_window']
    rows,c=event_audit(points((60.,70.,80.,90.)),[event()],window=(0.,.1))
    assert c['onset']==1 and c['confirmation']==0 and rows[0]['confirmation_observed_after_window']
    d=exposure_audit(points(),window=(.1,.2))
    assert d['local_both_s']==pytest.approx(.1)

def test_unknown_quality_and_zero_exposure_never_zero_rate():
    m=points();m['identity_break']=m.identity_break.astype(object);m.loc[1,'identity_break']=None
    with pytest.raises(ValueError):exposure_audit(m)
    m=points();m['measurement_status']='invalid'
    d=exposure_audit(m);r=candidate_rates(dict(onset=0),d)
    assert d['local_both_s']==0 and r['onset']['rate_per_evaluable_vehicle_hour'] is None
    assert r['onset']['status']=='Not Calculated'

def test_unknown_spatial_support_is_not_outside_region():
    m=points();m.loc[0,'position_m']=float('nan')
    with pytest.raises(ValueError):exposure_audit(m)

def test_no_approval_cannot_pass_even_small_difference():
    assert admission(difference_ci=(-.01,.01),margin=None,approved=False,support=True)['status']=='Awaiting Researcher Decision'
    assert admission(difference_ci=(-.01,.01),margin=.1,approved=False,support=True)['status']=='Awaiting Researcher Decision'
    assert admission(difference_ci=(-.01,.01),margin=.1,approved=True,support=False)['status']=='Evidence Insufficient'
    assert admission(difference_ci=(-.2,.01),margin=.1,approved=True,support=True)['status']=='Model discrepancy or imprecision'
    assert admission(difference_ci=(-.01,.01),margin=.1,approved=True,support=True)['status']=='Candidate criterion satisfied'

def test_binding_role_hash_and_window_fail_closed(tmp_path):
    p=tmp_path/'x.json';p.write_text(json.dumps(dict(windows={'us101__0750_0805':{},'us101__0805_0820':{}})))
    d=hashlib.sha256(p.read_bytes()).hexdigest()
    assert verify_binding(p,d,'calibration_summary')['windows']
    for digest,role in [('0'*64,'calibration_summary'),(d,'validation'),(d,'unknown')]:
        with pytest.raises(PermissionError):verify_binding(p,digest,role)
    p.write_text(json.dumps(dict(windows={'us101__0820_0835':{}})))
    with pytest.raises(PermissionError):verify_binding(p,hashlib.sha256(p.read_bytes()).hexdigest(),'calibration_summary')

def test_phase_aligned_cycles_do_not_equate_local_to_global_stability():
    bins=[dict(start_s=i*60,end_s=(i+1)*60,mean_speed_mps=2.,density=100.,inserted=80,exited=40,pending_end=40*i) for i in range(3)]
    d=cycle_diagnostics(bins,relative_margin=.05)
    assert d['local_candidate_end_s']==180. and not d['network_stationarity_supported']
    assert d['risk_used_to_choose_warmup'] is False

def test_plan_sha_and_frozen_input_mismatch_rejected(tmp_path):
    p=tmp_path/'experiment_plan.json';p.write_text(json.dumps(dict(frozen_files={},new_SUMO_runs=0,scientific_tolerance=None,ABCD_allowed=False,calibration_allowed=False)))
    (tmp_path/'PLAN_SHA256').write_text(hashlib.sha256(p.read_bytes()).hexdigest())
    assert validate_plan(tmp_path)['new_SUMO_runs']==0
    p.write_text(p.read_text()+' ')
    with pytest.raises(PermissionError):validate_plan(tmp_path)

def test_event_order_does_not_create_duplicate_or_omission():
    m=pd.concat([points((60.,70.,80.,90.)),points((60.,70.,80.,90.)).assign(time_s=lambda d:d.time_s+1.,observation_index=lambda d:d.observation_index+4)],ignore_index=True)
    e1=event();e2=dict(event(),event_start_s=1.,event_confirm_s=1.2,event_end_s=1.3)
    assert event_audit(m,[e2,e1])[1]['onset']==2

def test_cluster_ratio_uses_ratio_of_totals_not_mean_of_rates():
    r=clustered_rate([1,0],[100.,900.],seed=42,resamples=100)
    assert r['point_rate']==pytest.approx(3.6)
    assert r['iid_rows_used_as_clusters'] is False
    z=clustered_rate([0,0],[100.,900.],seed=42,resamples=100)
    assert z['interval'] is None and z['zero_event_bootstrap_not_evidence_of_zero_risk']
