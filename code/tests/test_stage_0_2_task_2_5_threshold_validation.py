from pathlib import Path
import json
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/formal/calibration/stage_0_2_task_2_5_20261011_r1'
pytestmark = pytest.mark.skipif(not OUT.is_dir(), reason="requires sealed local Task 2.5 outputs; excluded from portable Git evidence")

def test_grid_has_complete_6x4_and_baseline():
    d=pd.read_csv(OUT/'threshold_duration_grid.csv')
    assert d[['ttc_threshold_s','minimum_duration_s']].drop_duplicates().shape[0]==24
    x=d[(d.ttc_threshold_s==2.0)&(d.minimum_duration_s==.1)]
    assert int(x.reliable_event_count.sum())==5381


def test_duration_monotonicity_is_explicitly_observed():
    d=pd.read_csv(OUT/'threshold_duration_grid.csv')
    for th,g in d.groupby('ttc_threshold_s'):
        vals=g.groupby('minimum_duration_s').reliable_event_count.sum().sort_index().tolist()
        assert vals==sorted(vals,reverse=True)


def test_confirmation_is_causal_and_delayed():
    d=pd.read_parquet(OUT/'event_characteristics.parquet')
    assert (d.event_confirm_s >= d.event_start_s).all()
    assert ((d.event_confirm_s-d.event_start_s-d.minimum_duration_s).abs()<1e-8).all()
    assert (d.event_end_s + 1e-8 >= d.event_confirm_s).all()


def test_sampling_sensitivity_does_not_interpolate():
    d=pd.read_csv(OUT/'temporal_sampling_sensitivity.csv')
    assert set(d.phase)=={0,1}
    assert (d.event_count==0).all()
    assert 'non-interpolated' in d.note.iloc[0]


def test_case_pool_preserves_lankershim_row_31245():
    d=pd.read_csv(OUT/'selected_review_cases.csv')
    assert ((d.source=='lankershim__complete')&(d.original_row_number==31245)).any()
    assert len(d)==24


def test_audit_keeps_scientific_rule_unfrozen():
    a=json.loads((OUT/'audit.json').read_text(encoding='utf-8'))
    assert a['baseline_events']==5381
    assert a['formal_rule_frozen'] is False
    assert a['locked_holdout_opened'] is False


