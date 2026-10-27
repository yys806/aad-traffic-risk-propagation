"""R0 pure offline tests; no dataset, simulator or TraCI entrypoint."""
import copy
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare_stage_0_5_r0_design_packet.py"
spec = importlib.util.spec_from_file_location("r0_packet", SCRIPT)
r0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r0)


def routes():
    root = ET.Element("routes")
    ET.SubElement(root, "vType", id="v", tau="1")
    ET.SubElement(root, "route", id="entering", edges="onramp main_1 main_2")
    for vid, depart, route in [("i0", "0", "entering"), ("a", "2", "entering"),
                                ("b", "40", "entering"), ("x", "50", "through"),
                                ("c", "63", "entering")]:
        ET.SubElement(root, "vehicle", id=vid, depart=depart, route=route, type="v", departSpeed="max")
    return ET.tostring(root)


def test_ramp_mapping_deterministic_conserving_and_only_declared_depart():
    data, rows, diff = r0.ramp_candidate(routes())
    assert r0.ramp_candidate(routes())[0] == data
    assert [x["vehicle_id"] for x in rows] == ["a", "b", "c"]
    assert [x["candidate_depart_s"] for x in rows] == [20., 25., 80.]
    assert diff["blocks"] == {0: 2, 1: 1}
    assert diff["initial_count"] == 1
    assert all(x["status"] == "Proposed" for x in rows)
    assert all(x["source_input_sha256"] == r0.hashlib.sha256(routes()).hexdigest() for x in rows)


@pytest.mark.parametrize("mutation", ["speed", "type", "id", "block", "child", "extra_nonvehicle"])
def test_extra_delta_rejected(mutation):
    candidate, _, _ = r0.ramp_candidate(routes())
    tree = ET.fromstring(candidate)
    v = next(x for x in tree.findall("vehicle") if x.get("id") == "a")
    if mutation == "speed": v.set("departSpeed", "5")
    if mutation == "type": v.set("type", "other")
    if mutation == "id": v.set("id", "other")
    if mutation == "block": v.set("depart", "81")
    if mutation == "child": ET.SubElement(v, "param", key="hidden", value="1")
    if mutation == "extra_nonvehicle": tree.find("vType").set("tau", "2")
    with pytest.raises(ValueError):
        r0.compare_routes(routes(), ET.tostring(tree), allow_ramp=True)


def test_duplicate_and_illegal_ramp_depart_rejected():
    for value in ["nan", "-1", "420"]:
        tree = ET.fromstring(routes())
        tree.findall("vehicle")[1].set("depart", value)
        with pytest.raises(ValueError): r0.ramp_candidate(ET.tostring(tree))
    tree = ET.fromstring(routes())
    tree.findall("vehicle")[2].set("id", "a")
    with pytest.raises(ValueError): r0.ramp_candidate(ET.tostring(tree))


def test_input_cohort_uses_fixed_routes_never_outcomes():
    tree = ET.fromstring(routes())
    ET.SubElement(tree, "route", id="through", edges="main_0 main_1 main_2")
    ET.SubElement(tree, "route", id="from_downstream", edges="main_2")
    ET.SubElement(tree, "vehicle", id="downstream_initial", depart="0", route="from_downstream")
    data = ET.tostring(tree)
    cohort = r0.input_route_cohort(data)
    assert cohort["declared_ID_count"] == 5
    assert cohort["route_only_excluded_IDs"] == ["downstream_initial"]
    candidate, _, _ = r0.ramp_candidate(data)
    assert r0.input_route_cohort(candidate)["included_sorted_IDs_sha256"] == cohort["included_sorted_IDs_sha256"]


def test_candidate_matches_existing_policy_a_algorithm(tmp_path):
    import sys
    sys.path.insert(0, str(SCRIPT.parent))
    from prepare_stage_0_5_policy_a import pulse_routes
    source, target = tmp_path / "source.xml", tmp_path / "candidate.xml"
    source.write_bytes(routes())
    pulse_routes(source, target)
    # ET.write uses platform line endings in the prolog; the candidate has a
    # fixed LF byte binding. Compare all XML content/order, not that prolog.
    assert ET.tostring(ET.fromstring(target.read_bytes())) == ET.tostring(ET.fromstring(r0.ramp_candidate(source.read_bytes())[0]))


def frame(times=(120., 120.1, 120.2, 120.3)):
    return pd.DataFrame([dict(run_id="fixture", scenario_id="fixture", vehicle_id="f", incarnation_id="f0",
        leader_id="l", leader_incarnation_id="l0", time_s=t, lane_id="1", y_m=149 + i,
        native_lane_id="main_0_4", measurement_status="valid", reliable_following_eligible=True,
        ttc_valid=True, ttc_s=1., physical_support_status="observed_same_native_lane") for i, t in enumerate(times)])


def test_full_context_before_region_onset_not_confirmation():
    result = r0.audit_full_context(frame())
    assert result["full_context"]["P2_events"] == 1
    event = result["events"][0]
    assert event["onset_position_m"] == 149
    assert event["confirmation_position_m"] == 151
    assert event["confirm_s"] == 120.2
    assert event["source_attribution"] == ["S_UPSTREAM_MAIN"]
    assert result["existing_target_local_measurement"]["onset_events"] == 0
    assert result["existing_target_local_measurement"]["confirmation_position_events"] == 1


@pytest.mark.parametrize("mode", ["gap", "leader", "identity", "missing"])
def test_observation_gap_identity_and_quality_not_bridged(mode):
    d = frame()
    if mode == "gap": d.loc[2:, "time_s"] += .2
    if mode == "leader": d.loc[2:, "leader_id"] = "different"
    if mode == "identity": d.loc[2:, "incarnation_id"] = "f1"
    if mode == "missing":
        d.loc[2, "measurement_status"] = "missing"
        d.loc[2, "reliable_following_eligible"] = False
    result = r0.audit_full_context(d)
    assert result["events"] == []
    assert result["full_context"]["support"]["D1_E_veh_s"] < .3
    assert result["incomplete_candidates"]


def test_risk_exactly_threshold_not_event_and_no_missing_zero():
    d = frame()
    d["ttc_s"] = 2.
    d.loc[1, "measurement_status"] = "missing"
    d.loc[1, "reliable_following_eligible"] = False
    result = r0.audit_full_context(d)
    assert result["full_context"]["P2_events"] == 0
    assert result["full_context"]["support"]["missing_points"] == 1
    assert result["source_diagnosis_supported"] is False


def test_arms_forbid_extra_delta_and_execution():
    baseline = dict(input_files={"network.net.xml": "n", "routes.rou.xml": "r", "run.sumocfg": "c"})
    arms = []
    for arm, supply, ramp in [("B00", False, False), ("B10", True, False), ("B01", False, True), ("B11", True, True)]:
        inputs = dict(baseline["input_files"])
        if ramp: inputs["routes.rou.xml"] = (r0.CANDIDATE / "ramp_routes.rou.xml").as_posix()
        arms.append(dict(arm=arm, factors=dict(supply=supply, ramp=ramp), execution_allowed=False, seed=20261201,
            duration_s=420, internal_step_s=.05, recording_step_s=.1, evaluation_window_s=[120, 390],
            supply_target_lanes=r0.LANES, lane_speed_schedule=r0.PULSE_SCHEDULE if supply else r0.BASE_SCHEDULE, input_files=inputs))
    assert r0.validate_arms(arms, baseline)
    for field, value in [("seed", 1), ("execution_allowed", True), ("supply_target_lanes", ["main_1_0"])]:
        changed = copy.deepcopy(arms)
        changed[-1][field] = value
        with pytest.raises(ValueError): r0.validate_arms(changed, baseline)


def test_existing_path_helper_direction_and_missing_are_explicit():
    from riskprop.stage_0_1_sumo import analyze_physical_path_from_archived_tables as path
    state = pd.DataFrame([dict(vehicle_id="s", time_s=t, edge_id="a", leader_id=None) for t in [0., .1]] +
                         [dict(vehicle_id="t", time_s=t, edge_id="a", leader_id="s") for t in [0., .1]])
    topology = dict(source_edge="a", target_edge="a", directed_edges=[dict(edge_id="a", from_node="n0", to_node="n1")])
    assert path(state, topology, source_vehicle_id="s", target_vehicle_id="t", source_start_time_s=.1)["tau_p"] == .1
    assert path(state, topology, source_vehicle_id="missing", target_vehicle_id="t")["status"] == "uncertain_missing_vehicle"
    disconnected = dict(source_edge="a", target_edge="b", directed_edges=topology["directed_edges"] + [dict(edge_id="b", from_node="n2", to_node="n3")])
    assert path(state, disconnected, source_vehicle_id="s", target_vehicle_id="t")["status"] == "disconnected_topology"


def test_existing_path_gap_and_reverse_road_precheck_limitations():
    from riskprop.stage_0_1_sumo import analyze_physical_path_from_archived_tables as path
    state = pd.DataFrame([dict(vehicle_id="s", time_s=0., edge_id="a", leader_id=None),
                         dict(vehicle_id="s", time_s=1., edge_id="a", leader_id=None),
                         dict(vehicle_id="t", time_s=1., edge_id="a", leader_id="s")])
    topo = dict(source_edge="a", target_edge="a", directed_edges=[dict(edge_id="a", from_node="n0", to_node="n1")])
    # Existing helper bridges a1s gap: document, do not promote to qualified tau_p.
    assert path(state, topo, source_vehicle_id="s", target_vehicle_id="t")["tau_p"] == 1.
    reverse = dict(source_edge="b", target_edge="a", directed_edges=topo["directed_edges"] + [dict(edge_id="b", from_node="n1", to_node="n2")])
    state.loc[state.vehicle_id.eq("s"), "edge_id"] = "b"
    # Adjacent downstream leader/upstream follower still rejected by road precheck.
    assert path(state, reverse, source_vehicle_id="s", target_vehicle_id="t")["status"] == "disconnected_topology"
