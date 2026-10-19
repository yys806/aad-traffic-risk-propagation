"""Independent counterexamples; no local data or SUMO process."""
from copy import deepcopy
import pytest
from riskprop.stage_0_5_cd_observation import QueueContinuity, movement, entry_evidence, journey_audit, validate_summary


def frame(t, path='0', lane='main_0_0', valid=True, complete=True, blocked_path='0'):
    component=dict(path=path,members=['r|a','r|b'],member_lanes={'r|a':lane,'r|b':lane},
                   upstream_interval_m=[10.,10.],upstream_boundary_m=10.,inlet_adjacent=True,downstream_anchored=True)
    return dict(time_s=t,components=[component],member_lanes=component['member_lanes'],observation_valid=valid,
                support_complete=complete,all_paths_queued=False,downstream_context=True,pending=1,
                entry_by_path={blocked_path:dict(pending_ids=['p'],blocked=True)},physical_entry_space_observed=True)


def test_lane_mismatch_never_supports_entry_spillback():
    tracker=QueueContinuity(step=1.)
    for t in [0.,1.,2.]: r=tracker.update(frame(t,blocked_path='1'))
    assert r['entry_spillback_supported'] is False
    assert r['supported_entry_paths']==[]


def test_same_path_support_needs_continuous_physical_demand_evidence():
    tracker=QueueContinuity(step=1.)
    for t in [0.,1.,2.]:r=tracker.update(frame(t))
    assert r['entry_spillback_supported'] is True and r['supported_entry_paths']==['0']
    f=frame(3.);f['entry_by_path']={};r=tracker.update(f)
    assert not r['entry_spillback_supported']


@pytest.mark.parametrize('field',['observation_valid','support_complete'])
def test_invalid_current_frame_cannot_bridge_persistence(field):
    tracker=QueueContinuity(step=1.)
    tracker.update(frame(0.));bad=frame(1.);bad[field]=False
    assert tracker.update(bad)['state']=='Evidence Insufficient'
    r=tracker.update(frame(2.))
    assert r['continuous_inlet_duration_s']==0. and not r['entry_spillback_supported']


def test_verified_same_path_edge_progression_is_not_lane_change():
    tracker=QueueContinuity(step=1.)
    tracker.update(frame(0.))
    tracker.update(frame(1.,lane=':j_0'))
    r=tracker.update(frame(2.,lane='main_1_0'))
    assert r['entry_spillback_supported'] and r['lane_change_member_resets']==0


def test_real_path_change_resets_component_continuity():
    tracker=QueueContinuity(step=1.)
    tracker.update(frame(0.));tracker.update(frame(1.))
    r=tracker.update(frame(2.,path='1',lane='main_0_1',blocked_path='1'))
    assert r['continuous_inlet_duration_s']==0. and r['lane_change_member_resets']==2


def test_release_between_one_second_outputs_resets_duration():
    tracker=QueueContinuity()
    for i in range(41):
        f=frame(i*.05)
        if i==19:f['components']=[]
        r=tracker.update(f)
    assert r['continuous_inlet_duration_s']==pytest.approx(1.)
    assert not r['entry_spillback_supported']


def test_missing_frame_resets_and_component_split_is_conservative():
    tracker=QueueContinuity(step=1.)
    tracker.update(frame(0.));r=tracker.update(frame(2.))
    assert r['temporal_breaks']==1 and r['continuous_inlet_duration_s']==0.


def test_edge_change_not_counted_as_real_same_edge_lane_change():
    a=dict(edge_id='main_0',lane_id='main_0_2');b=dict(edge_id='main_1',lane_id='main_1_2')
    assert movement(a,b)=='edge_transition'
    b.update(edge_id='main_0',lane_id='main_0_1')
    assert movement(a,b)=='lane_change'


def test_entry_blockage_is_per_pending_lane_and_physical_rear():
    rows=[dict(lane_id='main_0_0',position_m=8.,length_m=5.)]
    defs={'p':dict(assigned_lane='0',type='car'),'q':dict(assigned_lane='1',type='car')}
    types={'car':dict(length='5',minGap='2.5')}
    r=entry_evidence(rows,{'p','q'},defs,types)
    assert r['0']['nearest_rear_m']==3. and r['0']['blocked']
    assert r['1']['nearest_rear_m'] is None and not r['1']['blocked']


def test_each_mandatory_vehicle_must_actually_merge_and_exit():
    defs={v:dict(assigned_lane='2') for v in ['a','b']}
    first={'a':'main_0_2','b':'main_0_2'}
    events=[dict(vehicle_id='a',edge='main_1',from_lane='main_1_2',to_lane='main_1_1')]
    exits=[dict(vehicle_id=v,last_edge='main_2') for v in defs]
    r=journey_audit(defs,first,events,exits)
    assert not r['verified'] and r['vehicles']['b']['actual_required_merge'] is False
    events.append(dict(events[0],vehicle_id='b'))
    assert journey_audit(defs,first,events,exits)['verified']


def test_legitimate_upstream_lane_change_fulfils_path_duty_without_forcing_location():
    r=journey_audit({'a':dict(assigned_lane='2')},{'a':'main_0_2'},
        [dict(vehicle_id='a',edge='main_0',from_lane='main_0_2',to_lane='main_0_1')],
        [dict(vehicle_id='a',last_edge='main_2')])
    assert r['verified'] and r['vehicles']['a']['actual_required_merge']


@pytest.mark.parametrize('value',[{}, {'status':'completed_valid'}, {'global_blockers':[],'scenario_blockers':[],'engineering_blockers':[]}])
def test_missing_severity_schema_is_global_blocker(value):
    assert validate_summary(value) is not None


def test_scenario_failure_does_not_become_global_but_inconsistent_schema_does():
    value=dict(global_blockers=[],scenario_blockers=['D_no_exit'],engineering_blockers=['D_no_exit'],evidence_insufficient=[],
               status='completed_with_engineering_blocker')
    assert validate_summary(value) is None
    value['engineering_blockers']=[]
    assert validate_summary(value) is not None
