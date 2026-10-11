import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pandas as pd
from run_stage_0_2_task_2_2_kinematic_review import diagnose, runs

def base(rows=3):
    return pd.DataFrame({
        'local_role':['follower']*rows, 'global_time_ms':[100*i for i in range(rows)], 'frame_id':list(range(rows)),
        'leader_trajectory_id':['L']*rows, 'time_s':[i*.1 for i in range(rows)], 'ttc_valid':[True]*rows,
        'ttc_s':[1]*rows, 'drac_mps2':[2]*rows, 'net_gap_m':[5]*rows,
        'closing_speed_mps':[2]*rows, 'x_m':list(range(rows)), 'y_m':[0]*rows,
        'speed_mps':[10]*rows, 'acceleration_mps2':[0]*rows,
        'raw_space_headway_ft':[20]*rows, 'raw_unit_system':['imperial']*rows,
        'trajectory_id':['F']*rows, 'identity_break':[False]*rows, 'observation_gap':[False]*rows,
        'leader_changed':[False]*rows, 'trajectory_boundary':[False]*rows,
        'diagnostic_clock_anchor_ms':[0]*rows,
    })

def case():
    return pd.Series({'leader_trajectory_id':'L'})

def test_continuous_pair_is_distinguished_from_missing_frame():
    out=diagnose(base(),case()); assert out['risk_state_continuity']=='multi_frame_continuous'
    g=base(); g.loc[2,'global_time_ms']=400; out=diagnose(g,case()); assert out['risk_state_continuity']=='boundary_limited_or_gapped'

def test_single_frame_spike_and_non_applicable_geometry_are_explicit():
    g=base(); g.ttc_valid=[False,True,False]; g.ttc_s=[float('inf'),.2,float('inf')]; out=diagnose(g,case()); assert out['risk_state_continuity']=='single_frame_spike'; assert out['geometry_check_applicability']=='unverified_missing_fields'

def test_runs_requires_adjacent_risk_and_observation_edges():
    assert runs([True, False, True], [False, True, True])[2] == 2
    assert runs([True, True], [False, True])[1] == 2
    assert runs([True, True], [False, False])[1] == 1

def test_different_predicates_are_counted_separately():
    g=base(); g.ttc_s=[.2, 3, 3]; g.drac_mps2=[2, 20, 2]; out=diagnose(g,case())
    assert out['ttc_lt_0_5_rows']==1 and out['drac_gt_10_rows']==1

def test_risk_at_window_edges_and_three_frame_length():
    g=base(5); g.ttc_valid=[True,True,False,False,True]; g.ttc_s=[1,1,3,3,1]
    out=diagnose(g,case()); assert out['extreme_rows']==3; assert out['extreme_longest_contiguous_frames']==2; assert out['extreme_run_count']==2
    g.ttc_valid=[False,False,True,True,True]; g.ttc_s=[3,3,1,1,1]
    out=diagnose(g,case()); assert out['extreme_longest_contiguous_frames']==3

def test_alternating_and_missing_frame_are_not_continuous():
    g=base(5); g.ttc_valid=[True,False,True,False,False]; g.ttc_s=[1,3,1,3,3]
    assert diagnose(g,case())['extreme_run_count']==2
    g=base(3); g.ttc_s=[1,1,1]; g.global_time_ms=[0,200,300]
    out=diagnose(g,case()); assert out['extreme_run_count']==2 and out['extreme_longest_contiguous_frames']==2

def test_identity_clock_and_leader_boundaries_cut_runs():
    g=base(3); g.ttc_s=[1,1,1]; g.leader_changed=[False,True,False]
    assert diagnose(g,case())['extreme_run_count']==2
    g=base(3); g.ttc_s=[1,1,1]; g.diagnostic_clock_anchor_ms=[0,1,1]
    assert diagnose(g,case())['extreme_run_count']==2

def test_single_and_normal_and_center_frame_attribution():
    g=base(3); g.ttc_valid=[False,True,False]; g.ttc_s=[3,.2,3]; out=diagnose(g,case())
    assert out['extreme_rows']==1 and out['extreme_run_count']==1 and out['center_frame_risk'] is False
    g=base(3); g.ttc_valid=[False]*3; out=diagnose(g,case()); assert out['extreme_rows']==0 and out['extreme_run_count']==0

def test_center_frame_risk_segment_is_reported():
    g=base(3); g.ttc_s=[1,1,3]; g.loc[1,'time_s']=.1
    out=diagnose(g,pd.Series({'leader_trajectory_id':'L','time_s':0.0})); assert out['center_frame_risk'] is True
    assert 'start_time_s' in out['center_frame_segment_json']

def test_ttc_and_drac_masks_are_independent():
    g=base(3); g.ttc_s=[.2,3,3]; g.drac_mps2=[2,20,2]; out=diagnose(g,case())
    stats=__import__('json').loads(out['risk_stats_json']); assert stats['ttc_lt_0_5']['rows']==1 and stats['drac_gt_10']['rows']==1
