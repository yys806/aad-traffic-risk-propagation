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

def test_fixed_window_keeps_unknown_denominator_and_equal_vehicle_weight():
    records = pd.DataFrame([
        {'time_s': 0.0, 'lower': 0.2, 'upper': 0.2},
        {'time_s': 0.1, 'lower': 0.4, 'upper': 0.4},
        {'time_s': 0.3, 'lower': 0.8, 'upper': 0.8},
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
    states = pd.DataFrame({'original_row_number':[10,11,12], 'time_s':[1.0,1.1,1.2], 'frame_id':[1,2,3]})
    assert observed_confirmation_time(states, [10,11,12], 0.2) == pytest.approx(1.2)
    assert continuity_is_valid({'time_s':1.0,'frame_id':1,'diagnostic_clock':'a','follower_trajectory_id':1,'leader_trajectory_id':2}, {'time_s':1.1,'frame_id':2,'diagnostic_clock':'a','follower_trajectory_id':1,'leader_trajectory_id':2})
    assert not continuity_is_valid({'time_s':1.0,'frame_id':1,'diagnostic_clock':'a','follower_trajectory_id':1,'leader_trajectory_id':2}, {'time_s':1.2,'frame_id':3,'diagnostic_clock':'a','follower_trajectory_id':1,'leader_trajectory_id':2})
