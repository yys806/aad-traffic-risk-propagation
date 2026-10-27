from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_stage_0_5_initial_speed_v1 import amend_initial_speeds


def fixture():
    network = b'<net><edge id="a"><lane id="a_0" index="0" length="100" speed="20"/></edge><edge id="b"><lane id="b_0" index="0" length="100" speed="10"/></edge><connection from="a" to="b" fromLane="0" toLane="0"/></net>'
    routes = b'<routes><vType id="t" emergencyDecel="9"/><route id="r" edges="a b"/><vehicle id="i1" type="t" route="r" depart="0" departLane="0" departPos="99.9" departSpeed="15.23"/><vehicle id="i2" type="t" route="r" depart="0" departLane="0" departPos="10" departSpeed="15.23"/><vehicle id="i3" type="t" route="r" depart="0" departLane="0" departPos="99" departSpeed="max"/><vehicle id="n1" type="t" route="r" depart="1" departSpeed="10"/></routes>'
    return routes, network


def test_only_proved_conflict_changes_and_all_other_bytes_remain():
    routes, network = fixture()
    result, report = amend_initial_speeds(routes, network)
    assert result == routes.replace(b'departPos="99.9" departSpeed="15.23"', b'departPos="99.9" departSpeed="10.0"')
    assert [r['id'] for r in report['changes']] == ['i1']
    assert report['unchanged_max_speed_initial_ids'] == ['i3']
    assert report['unchanged_noninitial_count'] == 1


def test_second_application_is_a_no_change_and_does_not_modify_ds38():
    routes, network = fixture()
    result, _ = amend_initial_speeds(routes, network)
    again, report = amend_initial_speeds(result, network)
    assert again == result and report['changes'] == []


def test_no_connected_lane_does_not_guess_a_downstream_speed():
    routes, network = fixture()
    network = network.replace(b'<connection from="a" to="b" fromLane="0" toLane="0"/>', b'')
    result, report = amend_initial_speeds(routes, network)
    assert result == routes and report['changes'] == []
