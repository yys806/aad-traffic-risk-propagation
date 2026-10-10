import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pandas as pd
from run_stage_0_2_task_2_2_kinematic_review import diagnose

def base(rows=3):
    return pd.DataFrame({
        'local_role':['follower']*rows, 'global_time_ms':[0,100,200][:rows], 'frame_id':list(range(rows)),
        'leader_trajectory_id':['L']*rows, 'time_s':[0,.1,.2][:rows], 'ttc_valid':[True]*rows,
        'ttc_s':[1,1,1][:rows], 'drac_mps2':[2,2,2][:rows], 'net_gap_m':[5,5,5][:rows],
        'closing_speed_mps':[2,2,2][:rows], 'x_m':[0,1,2][:rows], 'y_m':[0,0,0][:rows],
        'speed_mps':[10,10,10][:rows], 'acceleration_mps2':[0,0,0][:rows],
        'raw_space_headway_ft':[20]*rows, 'raw_unit_system':['imperial']*rows,
    })

def case():
    return pd.Series({'leader_trajectory_id':'L'})

def test_continuous_pair_is_distinguished_from_missing_frame():
    out=diagnose(base(),case()); assert out['risk_state_continuity']=='multi_frame_continuous'
    g=base(); g.loc[2,'global_time_ms']=400; out=diagnose(g,case()); assert out['risk_state_continuity']=='boundary_limited_or_gapped'

def test_single_frame_spike_and_non_applicable_geometry_are_explicit():
    g=base(); g.ttc_valid=[False,True,False]; g.ttc_s=[float('inf'),.2,float('inf')]; out=diagnose(g,case()); assert out['risk_state_continuity']=='single_frame_spike'; assert out['geometry_check_applicability']=='unverified_missing_fields'
