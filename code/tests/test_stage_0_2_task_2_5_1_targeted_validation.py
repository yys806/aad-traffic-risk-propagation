from pathlib import Path
import json
import pandas as pd
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'run_stage_0_2_task_2_5_1_targeted_validation.py'
spec=importlib.util.spec_from_file_location('task251', SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def _ev(rule, eid, source, pair, rows, start, end):
    return {'source':source,'rule':rule,'event_id':eid,'trajectory_id':pair[0],'leader_trajectory_id':pair[1],
            'event_start_s':start,'event_end_s':end,'event_duration_s':end-start,'raw_frame_count':len(rows),
            'ttc_min_s':1.0,'drac_max_mps2':2.0,'inclusion_status':'reliable','original_row_numbers':json.dumps(rows),
            'minimum_duration_s':0.1}


def test_overlap_edges_preserve_split_merge_and_source_scope():
    a=pd.DataFrame([_ev('A','a1','s1',('f','l'),[1,2,3],0,0.2),_ev('A','a2','s2',('f','l'),[1,2],0,0.1)])
    b=pd.DataFrame([_ev('B','b1','s1',('f','l'),[2,3],0.1,0.2),_ev('B','b2','s1',('f','l'),[1],0,0),_ev('B','b3','s2',('f','l'),[1],0,0)])
    edges=mod.overlap_edges({'A':a,'B':b})
    assert set(zip(edges.event_id_a,edges.event_id_b))=={('a1','b1'),('a1','b2'),('a2','b3')}
    assert not ((edges.source=='s1')&(edges.event_id_b=='b3')).any()


def test_zero_overlap_is_unmatched_only_in_classification():
    a=pd.DataFrame([_ev('A','a1','s1',('f','l'),[1],0,0)])
    b=pd.DataFrame([_ev('B','b1','s1',('f','l'),[2],0.1,0.1)])
    edges=mod.overlap_edges({'A':a,'B':b})
    assert edges.empty


def test_online_confirmation_uses_observed_timestamp():
    ev=pd.DataFrame([_ev('P','e','s',('f','l'),[10,11,12],1.0,1.2)])
    d=pd.DataFrame({'original_row_number':[10,11,12],'global_time_ms':[1000,1100,1200],'frame_id':[1,2,3],'time_s':[1.0,1.1,1.2]})
    out=mod.confirm_from_members(ev,d)
    assert out.event_confirm_s.iloc[0]==1.1
    assert abs(out.confirm_delay_s.iloc[0]-0.1)<1e-12
    assert bool(out.confirm_observed.iloc[0])


def test_rejected_event_joins_raw_candidate_without_field_assumption(monkeypatch):
    raw=pd.DataFrame([{'event_id':'e1','dataset':'d','site':'s','window_id':'w','source_member':'m','source_period':'p','trajectory_id':'f','leader_trajectory_id':'l','event_start_s':1.0,'event_end_s':1.2,'event_duration_s':0.2,'ttc_min_s':0.4,'drac_max_mps2':12.0,'original_row_numbers':'[1,2,3]'}])
    rel=pd.DataFrame(columns=raw.columns)
    rej=pd.DataFrame([{'event_id':'e1','rejection_reason':'identity_uncertain','raw_frame_count':3}])
    monkeypatch.setattr(mod,'extract_rear_end_events',lambda *args,**kwargs:(raw,rel,rej))
    out=mod.add_event_rows('s',pd.DataFrame(), 'P', 2.0, 0.1)
    assert len(out)==1 and out.inclusion_status.iloc[0]=='rejected'
    assert out.rejection_reason.iloc[0]=='identity_uncertain'
    assert out.trajectory_id.iloc[0]=='f' and out.raw_frame_count.iloc[0]==3


def test_new_casebook_has_24_pages_and_metrics_match_locked_counts():
    from pypdf import PdfReader
    out=ROOT/'outputs'/'formal'/'calibration'/'stage_0_2_task_2_5_1_20261011_r2'
    assert len(pd.read_csv(out/'case_analysis_24.csv'))==24
    assert len(PdfReader(str(out/'casebook_24.pdf')).pages)==24
    m=pd.read_csv(out/'candidate_rule_metrics.csv')
    assert dict(zip(m[m.source=='ALL'].rule,m[m.source=='ALL'].events))=={'P1_strict':1900,'P2_middle':4545,'P3_sensitive':8523,'REF_2.0_0.1':5381}
