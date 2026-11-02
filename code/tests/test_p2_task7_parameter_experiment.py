"""Task7 isolated measurement and planning invariants; no historical inputs."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import p2_task7_measurement as m

def test_exact_planning_is_powered_and_matches_known_example():
    result=m.exact_plan(.01,.002,.05)
    assert result['n']==773 and result['max_bad']==3 and result['power']>=.9

def test_cp_endpoints_and_empty_are_not_zeros():
    assert m.cp_upper(0,0) is None and m.cp_lower(0,0) is None
    assert m.cp_upper(0,6)==pytest.approx(1-.05**(1/6))
    assert m.cp_lower(6,6)==pytest.approx(.05**(1/6))
    assert m.cp_upper(6,6)==1 and m.cp_lower(0,6)==0

def test_positive_span_no_extra_frame():
    t=np.arange(12)/10;s=np.ones(12);v=np.ones(12,bool)
    event=m.segments(t,s,v,.5,1.,.1,start=0,stop=2)[0]
    assert event['confirmation_s']==pytest.approx(1.)
    assert not m.segments(t[:1],s[:1],v[:1],.5,.1,.1,start=0,stop=2)

def test_negative_and_long_missing_gap_reset():
    t=np.arange(12)/10;s=np.ones(12);v=np.ones(12,bool);s[5]=0
    assert not m.segments(t,s,v,.5,1.,.1,start=0,stop=2)
    s[5]=1;v[4:6]=False
    assert not m.segments(t,s,v,.5,1.,.1,start=0,stop=2)
    assert m.segments(t,s,v,.5,1.,.31,start=0,stop=2)

def test_edie_clips_space_and_time_exactly():
    t=np.arange(4,dtype=float);x=t[:,None];lane=np.zeros_like(x,int)
    r=m.edie(t,x,lane,3.,region=(1.,2.))
    assert r['D'][-1]==pytest.approx(1.) and r['V'][-1]==pytest.approx(1.)
    assert r['q'][-1]==pytest.approx(r['k'][-1]*r['u'][-1])
    r=m.edie(t,x,lane,.5,region=(1.,3.))
    assert r['D'][-1]==pytest.approx(.5) and r['V'][-1]==pytest.approx(.5)

def test_empty_region_is_undefined_and_stationary_inside_is_zero():
    t=np.arange(4,dtype=float);lane=np.zeros((4,1),int)
    r=m.edie(t,np.zeros((4,1)),lane,1.,region=(1.,2.))
    assert np.isnan(r['u']).all() and not r['V'].any()
    r=m.edie(t,np.ones((4,1))*1.5,lane,1.,region=(1.,2.))
    assert r['V'][-1]==1 and r['u'][-1]==0

def test_lane_change_and_missing_are_not_interpolated_as_full_truth():
    t=np.arange(4,dtype=float);x=t[:,None];lane=np.zeros_like(x,int);lane[2]=1
    r=m.edie(t,x,lane,1.,region=(0.,4.))
    assert r['V'][2]==0
    lane[:]=0;observed=np.ones_like(x,bool);observed[2]=False
    r=m.edie(t,x,lane,1.,region=(0.,4.),observed=observed)
    assert not r['complete'][2] and np.isnan(r['u'][2])

def test_recovery_and_hysteresis_change_lifetime_not_first_onset():
    t=np.arange(31)/10;s=np.where(t<1.5,1.1,.9);v=np.ones(31,bool)
    a=m.segments(t,s,v,1.,.5,.1,start=0,stop=3)
    b=m.segments(t,s,v,1.,.5,.1,start=0,stop=3,exit_delta=.2)
    assert a[0]['onset_upper_s']==b[0]['onset_upper_s']
    assert a[0]['end_s']==1.5 and b[0]['end_s'] is None

def test_fast_edie_matches_separate_reference_and_spatial_partition():
    import analyze_p2_task7_parameter_experiment as a
    t=np.arange(101)/10;x=np.column_stack((t,2*t+.3,np.ones(len(t))*3.5));lane=np.zeros_like(x,int)
    for w in [.2,1.,2.]:
        fast=a.fast_edie(t,x,lane,w,(1.,5.));reference=m.edie(t,x,lane,w,(1.,5.))
        assert np.allclose(fast['D'],reference['D']) and np.allclose(fast['V'],reference['V'])
        p=a.fast_edie(t,x,lane,w,(1.,3.));q=a.fast_edie(t,x,lane,w,(3.,5.))
        assert np.allclose(p['V']+q['V'],fast['V'])

def test_micro_candidates_never_concatenate_different_entities():
    import analyze_p2_task7_parameter_experiment as a
    t=30+np.arange(21)/10;s=np.zeros((21,2));s[:7,0]=2;s[7:14,1]=2
    assert not a.fast_events(t,s,np.ones_like(s,bool),1.,1.,.1)

def test_baseline_is_fitted_only_before_frozen_end():
    import analyze_p2_task7_parameter_experiment as a
    t=np.arange(100)/2;y=np.where(t<30,10.,1.)
    b=a.fit_baseline(t,y,9.,'constant')
    assert np.all(b==10.)

def test_truth_uses_followup_for_onset_near_horizon():
    t=np.arange(1,1001)/20;v=np.full((1000,20),10.);v[(t>=45.5)&(t<48),14:18]=9.
    x=2100-np.arange(20)[None,:]*15+np.cumsum(v*.05,axis=0)
    raw={'t':t,'v':v,'x':x,'lane':np.zeros_like(v,int),'native':v.copy()}
    audit={'unit_id':'fixture','condition':'P22','density':'high','actual_source_onset':[30.,30.05],'source_execution':30.}
    label=next(r for r in m.truth(raw,audit) if r['measurement_layer']=='cohort')
    assert label['state_truth']=='positive' and label['confirmation_s']==pytest.approx(46.5)
    assert label['onset_allowed_set']==pytest.approx([45.45,45.5])

def test_startup_failure_is_unknown_and_retains_attempt_denominator():
    import analyze_p2_task7_parameter_experiment as a
    r=a.evaluate({'t':np.array([])},{'measurement_layer':'cohort'},a.Config())
    s=a.summarize([{'layer':'cohort',**r}])
    assert r['alarm'] is None and s['attempts']==1 and s['unknown_n']==1
    assert s['truth_unknown_n']==1 and s['timely_rate_worst_case']==0.
