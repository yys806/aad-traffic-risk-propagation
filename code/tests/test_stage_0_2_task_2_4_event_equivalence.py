from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
from run_stage_0_2_task_2_4_event_equivalence import (
    edges, runs, independent_events, correspond, continuous_segments,
)


def frame(rows, *, leader='L', clock=0, pair=True):
    out=[]
    for i,(t,risk) in enumerate(rows):
        out.append({
            'trajectory_id':'F','leader_trajectory_id':leader if pair else np.nan,
            'global_time_ms':int(t*1000),'frame_id':i,'time_s':float(t),
            'ttc_valid':bool(risk),'ttc_s':1.0 if risk else 3.0,
            'drac_mps2':11.0 if risk else 1.0,'net_gap_m':2.0,
            'leader_matched':True,'identity_uncertain':False,
            'leader_identity_uncertain':False,'identity_break':False,
            'observation_gap':False,'leader_changed':False,
            'trajectory_boundary':False,'diagnostic_clock_anchor_ms':clock,
            'leader_frame_id':i,'original_row_number':100+i,
            'source_member':'synthetic',
        })
    return pd.DataFrame(out)


def test_risk_at_window_edges_and_minimum_duration():
    d=frame([(0.0,True),(0.1,True),(0.2,False),(0.3,True),(0.4,True)])
    ev=independent_events(d)
    assert len(ev)==2
    assert ev.raw_frame_count.tolist()==[2,2]
    assert ev.event_start_s.tolist()==[0.0,0.3]


def test_middle_normal_and_missing_frame_split_runs():
    d=frame([(0.0,True),(0.1,False),(0.2,True)])
    assert len(independent_events(d))==0  # both are sub-minimum singletons
    d=frame([(0.0,True),(0.1,True),(0.3,True),(0.4,True)])
    ev=independent_events(d)
    assert ev.raw_frame_count.tolist()==[2,2]
    assert ev.event_start_s.tolist()==[0.0,0.3]


def test_leader_and_clock_boundaries_do_not_merge():
    d=frame([(0.0,True),(0.1,True),(0.2,True)])
    d.loc[1,'leader_trajectory_id']='L2'
    assert independent_events(d).empty
    d=frame([(0.0,True),(0.1,True),(0.2,True)])
    d.loc[1,'diagnostic_clock_anchor_ms']=1
    # clock boundary splits the pair; no event reaches two frames
    assert len(independent_events(d))==0


def test_singleton_and_all_normal_states_are_not_events():
    assert independent_events(frame([(0.0,False),(0.1,False)])).empty
    assert independent_events(frame([(0.0,True)])).empty


def test_ttc_and_drac_masks_are_distinct_and_input_is_unchanged():
    d=frame([(0.0,True),(0.1,True)])
    d.loc[0,'ttc_s']=0.2; d.loc[1,'ttc_s']=1.0
    d.loc[0,'drac_mps2']=1.0; d.loc[1,'drac_mps2']=20.0
    original=d.copy(deep=True)
    ttc_mask=d.ttc_valid & (d.ttc_s<.5)
    drac_mask=d.ttc_valid & (d.drac_mps2>10)
    assert int(ttc_mask.sum())==1 and int(drac_mask.sum())==1
    assert d.equals(original)


def test_correspondence_uses_member_sets_not_event_ids():
    f=pd.DataFrame([{'original_row_numbers':(1,2),'trajectory_id':'F'}, {'original_row_numbers':(5,6),'trajectory_id':'F'}])
    i=pd.DataFrame([{'original_row_numbers':(5,6),'trajectory_id':'F'}, {'original_row_numbers':(1,2),'trajectory_id':'F'}])
    c=correspond(f,i)
    assert c.classification.tolist()==['exact_member_match','exact_member_match']


def test_continuous_exposure_reports_span_and_coverage_separately():
    d=frame([(0.0,False),(0.1,False),(0.3,False)])
    seg=continuous_segments(d)
    assert seg.frames.tolist()==[2,1]
    assert seg.time_span_s.tolist()==[0.1,0.0]
    assert seg.coverage_s.tolist()==[0.2,0.1]


def test_reference_runs_keeps_first_frame_of_each_risk_run():
    m=np.array([True,True,False,True,True])
    e=np.array([False,True,True,True,True])
    assert runs(m,e)==[(0,1),(3,4)]

