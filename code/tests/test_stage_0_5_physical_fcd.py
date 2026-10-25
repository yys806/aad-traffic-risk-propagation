import pandas as pd
import pytest
from riskprop import stage_0_5_state_support as ss
from riskprop.stage_0_5_scene_reconstruction import parse_fcd


def test_native_geometry_is_separate_from_mapped_support(tmp_path):
    f = tmp_path/'fcd.xml'
    f.write_text('<fcd-export><timestep time="0"><vehicle id="a" lane="main_1_1" pos="10" speed="12"/><vehicle id="b" lane="main_1_1" pos="30" speed="10"/></timestep></fcd-export>')
    parsed = parse_fcd(f, {'main_1':234.04})
    assert parsed.native_position_m.tolist() == [10,30]
    assert parsed.y_m.tolist() != [10,30]
    state = ss.fcd_to_state_frame(parsed,{'a':4,'b':5},run_id='r',scenario_id='s',seed=1)
    measured = ss.measure_state_frame(state).set_index('vehicle_id')
    assert measured.loc['a','net_gap_m'] == 15
    assert measured.loc['a','ttc_s'] == 7.5
    assert measured.loc['b','measurement_status'] == 'missing'
    assert not measured.loc['b','reliable_following_eligible']


def test_cross_edge_and_internal_relations_are_not_inferred(tmp_path):
    f = tmp_path/'fcd.xml'
    f.write_text('<fcd-export><timestep time="0"><vehicle id="a" lane="main_0_0" pos="170" speed="12"/><vehicle id="b" lane="main_1_1" pos="1" speed="10"/><vehicle id="c" lane=":j_0_0" pos="1" speed="10"/><vehicle id="d" lane=":j_0_0" pos="20" speed="8"/></timestep></fcd-export>')
    parsed=parse_fcd(f,{'main_0':172.9,'main_1':234.04})
    measured=ss.measure_state_frame(ss.fcd_to_state_frame(parsed,dict.fromkeys('abcd',4.),run_id='r',scenario_id='s',seed=1))
    assert measured.leader_id.isna().all()
    assert measured.measurement_status.eq('missing').all()
    assert not measured.reliable_following_eligible.any()


def test_missing_physical_coordinates_cannot_fall_back_to_y():
    with pytest.raises(ss.StateSupportError,match='missing_native_physical_coordinates'):
        ss.fcd_to_state_frame(pd.DataFrame({'y_m':[100]}),{},run_id='r',scenario_id='s',seed=1)
