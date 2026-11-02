"""Targeted measurement-contract tests, not scientific traffic validation."""
import importlib.util
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

spec = importlib.util.spec_from_file_location("p2t3_proxy", Path(__file__).parents[1] / "scripts/run_p2_task3_calibration_only.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def test_observed_span_and_onset_interval():
    t = np.arange(15) / 10
    s = np.where(t < 0.2, 0, 1)
    r = m.first_confirmation(t, s, np.ones(15, bool), .5, 1, .11, 0)
    assert np.isclose(r['confirmation_s'], 1.2)
    assert np.isclose(r['onset_lower_s'], .1)
    assert np.isclose(r['onset_upper_s'], .2)


def test_one_sample_cannot_establish_duration():
    r = m.first_confirmation(np.array([0.]), np.array([1.]), np.array([True]), .5, .1, .1, 0)
    assert r['confirmation_s'] is None


def test_gap_needs_explicit_q_and_is_flagged():
    t = np.arange(11)/10
    valid = np.ones(11, bool); valid[4:6] = False
    assert m.first_confirmation(t, np.ones(11), valid, .5, 1, .11, 0)['confirmation_s'] is None
    r = m.first_confirmation(t, np.ones(11), valid, .5, 1, .31, 0)
    assert r['gap_bridged'] and np.isclose(r['confirmation_s'], 1)
    assert r['left_censored']


def test_negative_resets_and_invalid_does_not_become_zero():
    t = np.arange(11)/10
    s = np.ones(11); s[5] = 0
    assert m.first_confirmation(t, s, np.ones(11, bool), .5, 1, .11, 0)['confirmation_s'] is None


def test_source_and_recovery_classification():
    assert m.classify({'confirmation_s': 2, 'onset_upper_s': 1}, 3, 2, True)['pre_source_alarm']
    assert not m.classify({'confirmation_s': 5, 'onset_upper_s': 3}, 3, 2, True)['event_detected']
    assert m.classify({'confirmation_s': 4, 'onset_upper_s': 3}, 3, 2, True)['event_detected']


def test_shared_panel_reproducibility_and_three_aggregators():
    s = m.Scenario('test')
    t, x = m.panel(s, 123)
    t2, x2 = m.panel(s, 123)
    assert np.array_equal(x, x2)
    for agg in ('mean','median','proportion'):
        stat, cov = m.signals(t, x, m.Detector(agg))
        assert np.all(cov == 1) and np.all(np.isfinite(stat))
    assert len(m.scenarios()) == 16 and len(m.detectors()) == 42


def test_fixed_denominator_coverage():
    t, x = m.panel(m.Scenario('test'), 123)
    x[:4,t>=30] = np.nan
    _, cov = m.signals(t, x, m.Detector())
    assert np.all(cov[t>=30] == .8)


def test_response_location_join_preserves_region_and_cohort_distinction():
    import audit_p2_task3_sumo_b_calibration_only as a
    rows=[{'vehicle_id':'s1','time_s':'31.2','lane_position_m':'2234.4'},
          {'vehicle_id':'s0','time_s':'30.6','lane_position_m':'2255.4'}]
    responses=[{'vehicle_id':'s0','confirmation_s':'30.6'},
               {'vehicle_id':'s1','confirmation_s':'31.2'},
               {'vehicle_id':'s5','confirmation_s':''}]
    result=a.response_locations(rows,responses,[1300,2240],['s5'])
    assert len(result)==2
    assert not result[0]['in_region'] and result[1]['in_region']
    assert not any(r['in_fixed_cohort'] or r['qualified_witness'] for r in result)


def test_response_without_position_fails_instead_of_fabricating_location():
    import pytest
    import audit_p2_task3_sumo_b_calibration_only as a
    with pytest.raises(KeyError):
        a.response_locations([], [{'vehicle_id':'s1','confirmation_s':'31.2'}], [1300,2240], ['s5'])
