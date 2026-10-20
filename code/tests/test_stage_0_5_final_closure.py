"""D1 expected values are hand-computed, independent of the new implementation."""
import numpy as np
import pandas as pd
import pytest

from riskprop.stage_0_5_final_closure import local_p2, equivalence, check_run_plan,real_region_mask


def states():
    t=np.arange(7)/10
    return pd.DataFrame(dict(dataset='ngsim',site='us101',window_id='fixture',
        source_member='fixture',source_period='fixture',trajectory_id='f',vehicle_id='f',
        leader_trajectory_id='l',leader_id='l',original_row_number=np.arange(7),
        diagnostic_clock_anchor_ms=0,global_time_ms=np.arange(7)*100,frame_id=np.arange(7),
        time_s=t,identity_uncertain=False,leader_identity_uncertain=False,
        identity_break=False,observation_gap=False,leader_matched=True,
        measurement_status='valid',ttc_valid=True,ttc_s=[3,1,1,1,1,3,3],drac_mps2=1.,
        _inside=[False,False,True,True,True,True,True],_position=[149,149.9,150,151,152,153,154]))


def test_onset_vs_confirmation_same_time_window_and_no_left_restart():
    d=states();a=local_p2(d,[0,.6])
    assert a['counts']==dict(onset=0,confirmation=1,through_confirmation=0,through_end=0)
    assert a['exposure']['local_evaluable_s']==pytest.approx(.4)
    assert a['events'][0]['confirm_s']==pytest.approx(.3)
    # The same event is not manufactured at the left cut or counted by confirm time.
    b=local_p2(d,[.2,.4]);assert all(v==0 for v in b['counts'].values())
    assert b['exposure']['local_evaluable_s']==pytest.approx(.2)
    assert b['confirmation_time_sensitivity']==1


def test_original_exposure_only_current_link_break_flag():
    d=states();d['_inside']=True;d.loc[0,'identity_break']=True
    assert local_p2(d,[0,.6])['exposure']['local_evaluable_s']==pytest.approx(.6)
    d.loc[3,'identity_break']=True
    assert local_p2(d,[0,.6])['exposure']['local_evaluable_s']==pytest.approx(.5)


def test_full_link_window_and_outside_leader_kept():
    d=states();d['_inside']=True
    a=local_p2(d,[.15,.45])
    assert a['exposure']['local_evaluable_s']==pytest.approx(.2)
    assert a['counts']['onset']==0


def test_right_confirmation_outside_window_retained():
    d=states();d['_inside']=True
    a=local_p2(d,[0,.25]);assert a['counts']['onset']==1
    assert a['events'][0]['confirmation_after_window']
    d=d.iloc[:3].copy()
    b=local_p2(d,[0,.2]);assert b['counts']['onset']==0
    assert b['right_censored_unconfirmed_candidates']==1


@pytest.mark.parametrize('field,value',[('identity_uncertain',None),('time_s',np.nan),('_inside',1)])
def test_unknown_inputs_fail_closed(field,value):
    d=states();d[field]=d[field].astype(object);d.loc[2,field]=value
    with pytest.raises(ValueError):local_p2(d,[0,.6])


def test_duplicate_clock_rejected():
    d=states();d.loc[2,'time_s']=.1
    with pytest.raises(ValueError):local_p2(d,[0,.6])


def test_complete_follower_partitions_preserve_formal_events_and_exposure():
    a=states();b=states();b['trajectory_id']='f2';b['vehicle_id']='f2';b['original_row_number']+=7
    whole=local_p2(pd.concat([a,b],ignore_index=True),[0,.6]);parts=[local_p2(d,[0,.6]) for d in [a,b]]
    assert whole['counts']=={k:sum(x['counts'][k] for x in parts) for k in whole['counts']}
    assert whole['exposure']['local_evaluable_s']==pytest.approx(sum(x['exposure']['local_evaluable_s'] for x in parts))
    assert {e['event_id'] for e in whole['events']}=={e['event_id'] for x in parts for e in x['events']}


def test_real_lane_storage_type_does_not_silently_empty_region():
    d=pd.DataFrame(dict(lane_id=['1','5','6','2'],y_m=[150,349.9,200,350]))
    assert real_region_mask(d).tolist()==[True,True,False,False]
    d['lane_id']=pd.to_numeric(d.lane_id)
    assert real_region_mask(d).tolist()==[True,True,False,False]
    d.loc[0,'lane_id']=1.5
    with pytest.raises(ValueError):real_region_mask(d)


def test_runtime_seed_is_checked_against_declared_spec(tmp_path):
    from riskprop.stage_0_5_b12n_worker import settings
    class Sim:
        def getOption(self,k):return {'step-method.ballistic':'true','step-length':'.05','seed':'20261020','threads':'1','time-to-teleport':'-1','random':'false'}[k]
        def getDeltaT(self):return .05
        def getTime(self):return 0.
        def saveState(self,p):p.write_text('<snapshot/>')
    class Vehicle:
        def getIDList(self):return []
    class Conn:
        simulation=Sim();vehicle=Vehicle()
        def getVersion(self):return (22,'SUMO 1.26.0')
    # saveState receives a string in TraCI; fake converts it just for this test.
    Conn.simulation.saveState=lambda p: __import__('pathlib').Path(p).write_text('<snapshot/>')
    assert settings(Conn(),dict(kind='CD',seed=20261020),{},tmp_path)['verified']
    assert not settings(Conn(),dict(kind='CD',seed=20261019),{},tmp_path)['verified']


def test_unknown_margin_or_system_error_never_pass():
    assert equivalence([-1,1],None,0)['status']=='Awaiting Researcher Decision'
    assert equivalence([-1,1],2,None)['status']=='Evidence Insufficient'
    assert equivalence([-1,1],2,.5)['metric_satisfied']
    assert not equivalence([-1,1],1,.1)['metric_satisfied']


def test_plan_reserves_seeds_and_prohibits_validation_without_complete_protocol():
    p=dict(runs=[dict(role='construction',seed=1,duration_s=300),dict(role='repeat',seed=2,duration_s=300),dict(role='repeat',seed=3,duration_s=300)],
        limits=dict(per_run_wall_s=600,memory_bytes=3*1024**3,artifact_bytes=2*1024**3),
        scientific_delta=None,precision_h=None,validation_access=False,ABCD_allowed=False)
    check_run_plan(p)
    p['validation_access']=True
    with pytest.raises(PermissionError):check_run_plan(p)
    p['validation_access']=False;p['runs'][1]['seed']=1
    with pytest.raises(PermissionError):check_run_plan(p)
