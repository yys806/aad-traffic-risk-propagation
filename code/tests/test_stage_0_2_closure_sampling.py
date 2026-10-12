import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from stage_0_2_closure_analysis import ordered_states, sequence_events, event_edges, correspondence_summary
from test_stage_0_2_final_closure import record
import pandas as pd
import pytest

def test_sampling_checks_discarded_identity_and_all_phases():
    d=pd.DataFrame([record(i) for i in range(7)])
    a,_=sequence_events(ordered_states(d),step_ms=100)
    b,_=sequence_events(ordered_states(d),step_ms=200,phase_ms=0)
    c,_=sequence_events(ordered_states(d),step_ms=200,phase_ms=100)
    assert len(a)==len(b)==len(c)==1
    assert b.iloc[0].original_row_numbers==[0,2,4,6]
    assert c.iloc[0].original_row_numbers==[1,3,5]
    changed=d.copy();changed.loc[1,'leader_trajectory_id']='other'
    b,_=sequence_events(ordered_states(changed),step_ms=200,phase_ms=0)
    assert 0 not in b.iloc[0].original_row_numbers

def test_sampling_preserves_interruption_and_online_quantization():
    d=pd.DataFrame([record(i) for i in range(8)])
    p1,_=sequence_events(ordered_states(d),threshold=1.5,minimum_span=.3,step_ms=200)
    assert p1.iloc[0].event_confirm_s==pytest.approx(.4)
    d.loc[2,'ttc_s']=3
    a,_=sequence_events(ordered_states(d),minimum_span=.1)
    b,_=sequence_events(ordered_states(d),minimum_span=.1,step_ms=200,phase_ms=100)
    e=event_edges(a,b)
    assert correspondence_summary(a,b,e)['comparison_merged']==1

def test_source_collision_never_overlaps():
    d=ordered_states(pd.DataFrame([record(i) for i in range(5)]))
    a,_=sequence_events(d)
    b=a.copy();b['source_member']='else'
    assert len(event_edges(a,b))==0
