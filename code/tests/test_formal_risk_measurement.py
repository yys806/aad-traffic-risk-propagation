import math
import pandas as pd
import pytest
from riskprop.formal_risk_measurement import (
    P2_FORMAL_CONFIG, contribution_bounds, did_interval, equal_vehicle_average,
    integrate_fixed_window, rho_from_ttc, continuity_is_valid, observed_confirmation_time,
)

def test_rho_and_status_bounds():
    assert math.isclose(rho_from_ttc(2.0), math.exp(-2.0 / P2_FORMAL_CONFIG.tau_s))
    assert rho_from_ttc(0) is None
    assert contribution_bounds(measurement_status='valid', in_region=True, ttc_s=2.0)[0] > 0
    assert contribution_bounds(measurement_status='not_applicable', in_region=True, ttc_s=9)[0:2] == (0.0, 0.0)
    assert contribution_bounds(measurement_status='missing', in_region=True, ttc_s=2)[0:2] == (0.0, 1.0)
    assert contribution_bounds(measurement_status='valid', in_region=None, ttc_s=2)[0:2] == (0.0, 1.0)
    assert contribution_bounds(measurement_status='missing', in_region=False, ttc_s=None)[0:2] == (0.0, 0.0)

def test_rho_is_the_approved_exponential_mapping_without_threshold_truncation():
    """The approved main definition is exp(-TTC/tau); no linear or truncated form."""
    tau = P2_FORMAL_CONFIG.tau_s
    for ttc in (0.1, 0.5, 1.0, 2.0, 5.0, 15.0, 60.0):
        value = rho_from_ttc(ttc)
        assert value is not None
        assert math.isclose(value, math.exp(-ttc / tau), rel_tol=1e-12)
        # the linear pre-ratification mapping 1 - TTC/theta must not be reproduced
        assert not math.isclose(value, max(0.0, 1.0 - ttc / 2.0), abs_tol=1e-6)
    # strictly decreasing and strictly positive: no truncation at the P2 threshold
    series = [rho_from_ttc(x) for x in (0.5, 1.0, 2.0, 5.0, 30.0, 120.0)]
    assert all(b < a for a, b in zip(series, series[1:]))
    assert all(value > 0 for value in series)
    assert rho_from_ttc(0) is None
    assert rho_from_ttc(-1.0) is None
    assert rho_from_ttc(float('nan')) is None


def test_fixed_window_keeps_unknown_denominator_and_equal_vehicle_weight():
    records = pd.DataFrame([
        {'time_s': 0.0, 'global_time_ms': 0, 'frame_id': 0, 'diagnostic_clock_anchor_ms': 1, 'dataset':'d', 'site':'s', 'window_id':'w', 'source_member':'m', 'source_period':'p', 'trajectory_id':'f', 'leader_trajectory_id':'l', 'leader_matched':True, 'identity_uncertain':False, 'leader_identity_uncertain':False, 'identity_break':False, 'observation_gap':False, 'lower': 0.2, 'upper': 0.2},
        {'time_s': 0.1, 'global_time_ms': 100, 'frame_id': 1, 'diagnostic_clock_anchor_ms': 1, 'dataset':'d', 'site':'s', 'window_id':'w', 'source_member':'m', 'source_period':'p', 'trajectory_id':'f', 'leader_trajectory_id':'l', 'leader_matched':True, 'identity_uncertain':False, 'leader_identity_uncertain':False, 'identity_break':False, 'observation_gap':False, 'lower': 0.4, 'upper': 0.4},
        {'time_s': 0.3, 'global_time_ms': 300, 'frame_id': 3, 'diagnostic_clock_anchor_ms': 1, 'dataset':'d', 'site':'s', 'window_id':'w', 'source_member':'m', 'source_period':'p', 'trajectory_id':'f', 'leader_trajectory_id':'l', 'leader_matched':True, 'identity_uncertain':False, 'leader_identity_uncertain':False, 'identity_break':False, 'observation_gap':False, 'lower': 0.8, 'upper': 0.8},
    ])
    out = integrate_fixed_window(records, window_start_s=0.0, window_end_s=0.3)
    assert out['known_time_s'] == pytest.approx(0.1)
    assert out['unknown_time_s'] == pytest.approx(0.2)
    assert out['lower_mean'] == pytest.approx(0.2 * 0.1 / 0.3)
    avg = equal_vehicle_average([{'lower_mean': 0.0, 'upper_mean': 1.0}, {'lower_mean': 1.0, 'upper_mean': 1.0}])
    assert avg['lower_mean'] == pytest.approx(0.5)

def test_did_interval_conservative_bounds():
    values = [{'lower_mean': 0.2, 'upper_mean': 0.3}, {'lower_mean': 0.1, 'upper_mean': 0.2}, {'lower_mean': 0.3, 'upper_mean': 0.4}, {'lower_mean': 0.4, 'upper_mean': 0.5}]
    lo, hi = did_interval(*values)
    assert lo == pytest.approx(0.2 - 0.2 - 0.4 + 0.4)
    assert hi == pytest.approx(0.3 - 0.1 - 0.3 + 0.5)

def test_online_confirmation_uses_observed_frame():
    states = pd.DataFrame([dict(original_row_number=10,time_s=1.0,global_time_ms=1000,frame_id=1,diagnostic_clock_anchor_ms=7,dataset='d',site='s',window_id='w',source_member='m',source_period='p',trajectory_id='f',leader_trajectory_id='l',leader_matched=True,identity_uncertain=False,leader_identity_uncertain=False,identity_break=False,observation_gap=False,ttc_valid=True,measurement_status='valid',ttc_s=1.0),dict(original_row_number=11,time_s=1.1,global_time_ms=1100,frame_id=2,diagnostic_clock_anchor_ms=7,dataset='d',site='s',window_id='w',source_member='m',source_period='p',trajectory_id='f',leader_trajectory_id='l',leader_matched=True,identity_uncertain=False,leader_identity_uncertain=False,identity_break=False,observation_gap=False,ttc_valid=True,measurement_status='valid',ttc_s=1.0),dict(original_row_number=12,time_s=1.2,global_time_ms=1200,frame_id=3,diagnostic_clock_anchor_ms=7,dataset='d',site='s',window_id='w',source_member='m',source_period='p',trajectory_id='f',leader_trajectory_id='l',leader_matched=True,identity_uncertain=False,leader_identity_uncertain=False,identity_break=False,observation_gap=False,ttc_valid=True,measurement_status='valid',ttc_s=1.0)])
    assert observed_confirmation_time(states, [10,11,12], 0.2) == pytest.approx(1.2)
    assert continuity_is_valid(states.iloc[0].to_dict(), states.iloc[1].to_dict())
    assert not continuity_is_valid(states.iloc[0].to_dict(), states.iloc[2].to_dict())

def test_continuity_uses_ngsim_clock_anchor_and_fails_closed():
    base = {'time_s': 1.0, 'global_time_ms': 1000, 'frame_id': 10, 'diagnostic_clock_anchor_ms': 1000,
            'dataset': 'd', 'site': 's', 'window_id': 'w', 'source_member': 'm',
            'source_period':'p', 'trajectory_id': 'f', 'leader_trajectory_id': 'l',
            'leader_matched':True,'identity_uncertain':False,'leader_identity_uncertain':False,
            'identity_break':False,'observation_gap':False}
    nxt = dict(base, time_s=1.1, global_time_ms=1100, frame_id=11)
    assert continuity_is_valid(base, nxt)
    assert not continuity_is_valid(base, dict(nxt, diagnostic_clock_anchor_ms=2000))
    missing = dict(nxt); missing.pop('diagnostic_clock_anchor_ms')
    assert not continuity_is_valid(base, missing)

def test_continuity_rejects_pair_switch_and_200ms_step():
    base = {'time_s': 1.0, 'global_time_ms': 1000, 'frame_id': 10, 'diagnostic_clock_anchor_ms': 1000,
            'dataset':'d','site':'s','window_id':'w','source_member':'m','source_period':'p', 'trajectory_id': 'f', 'leader_trajectory_id': 'l', 'leader_matched':True,'identity_uncertain':False,'leader_identity_uncertain':False,'identity_break':False,'observation_gap':False}
    assert not continuity_is_valid(base, dict(base, time_s=1.1, frame_id=11, leader_trajectory_id='other'))
    assert not continuity_is_valid(base, dict(base, time_s=1.2, frame_id=12), expected_step_s=0.1)
    assert continuity_is_valid(base, dict(base, time_s=1.2, global_time_ms=1200, frame_id=12), expected_step_s=0.2, expected_frame_delta=2)
