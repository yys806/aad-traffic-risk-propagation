"""Independent analytic expectations for B1.2; never reads local traffic data."""
from copy import deepcopy
import pytest

from riskprop.stage_0_5_b12_observation import (
    audit_transition, ScopedAccounting, QueueTracker, queue_snapshot, QUEUE_CONFIG,
)


def state(vid="v", t=0., x=10., speed=10., accel=-2., lane="main_1_0", edge="main_1"):
    return dict(run_id="r", vehicle_id=vid, incarnation_id="r|"+vid, time_s=t,
                position_m=x, speed_mps=speed, acceleration_mps2=accel,
                last_action_time_s=0., lane_id=lane, edge_id=edge,
                length_m=5., traci_vehicle_control=False, numerical_config_verified=True)


def pair(**changes):
    a=state();b=state(t=.05,x=10.4975,speed=9.9)
    b.update(changes)
    return a,b


def test_exact_action_motion_uses_terminal_speed():
    r=audit_transition(*pair())
    assert r["classification"]=="Exact Observable" and r["passed"] is True
    assert abs(r["residual_m"])<1e-12


def test_nonaction_stop_uses_start_acceleration_not_end_acceleration():
    a=state(t=.05,x=10.,speed=.1,accel=-4.)
    b=state(t=.1,x=10.00125,speed=0.,accel=-2.)
    r=audit_transition(a,b)
    assert r["classification"]=="Exact Reconstructable Under Verified Conditions"
    assert r["candidate"]==pytest.approx(-.1) and r["passed"]


def test_decision_stop_is_only_bounded_and_violation_blocks():
    a=state(speed=.2);b=state(t=.05,x=10.002,speed=0.)
    r=audit_transition(a,b)
    assert r["classification"]=="Bounded Consistency Only" and r["passed"]
    assert r["residual_m"] is None and r["candidate"] is None
    b["position_m"]=10.006
    assert audit_transition(a,b)["blocker"]=="bounded_range_violation"


def test_exact_residual_failure_is_blocker():
    assert audit_transition(*pair(position_m=10.51))["blocker"]=="exact_displacement_violation"


@pytest.mark.parametrize("change,reason", [
    ({"incarnation_id":"other"},"identity_discontinuity"),
    ({"time_s":.1},"internal_clock_inconsistent"),
    ({"last_action_time_s":None},"action_clock_unknown"),
    ({"traci_vehicle_control":None},"vehicle_control_unconfirmed"),
    ({"numerical_config_verified":False},"numerical_configuration_unconfirmed"),
])
def test_fail_closed_identity_clock_control_config(change,reason):
    r=audit_transition(*pair(**change))
    assert r["classification"]=="Not Evaluable" and r["blocker"]==reason
    assert r["candidate"] is None and r["residual_m"] is None


@pytest.mark.parametrize("change", [{"edge_id":"main_2","lane_id":"main_2_0","position_m":.1},
                                  {"lane_id":"main_1_1","position_m":10.51}])
def test_legal_coordinate_change_has_no_fabricated_residual(change):
    r=audit_transition(*pair(**change))
    assert r["classification"]=="Not Evaluable" and r["blocker"] is None
    assert r["residual_m"] is None and r["actual_dx_m"] is None


def test_nonaction_candidate_must_match_reported_speed():
    a=state(t=.05);b=state(t=.1,speed=8.,x=10.45)
    assert audit_transition(a,b)["blocker"]=="candidate_terminal_speed_inconsistent"


def test_global_local_and_spatial_boundary_accounting_are_separate():
    a=ScopedAccounting()
    rows={"a":state("a",x=40.),"b":state("b",x=300.)}
    f=a.update(rows,["a","b"],[],2,0.)
    assert f["global_present"]==2 and f["local_present"]==0
    rows["a"]["position_m"]=60.
    f=a.update(rows,[],[],2,.05)
    assert f["local_entered"]==1 and f["local_exited"]==0 and f["local_present"]==1
    assert f["global_conservation_residual"]==0 and f["local_set_balance_residual"]==0
    rows["a"]["position_m"]=251.
    f=a.update(rows,[],[],2,.1)
    assert f["local_exited"]==1 and f["local_present"]==0
    assert f["edge_counts"]=={"main_1":2}


def test_uninserted_demand_is_not_local_density():
    a=ScopedAccounting();f=a.update({"a":state("a",x=100.)},["a"],[],10,0.)
    assert f["external_pending"]==9
    assert f["local_density_veh_km_lane"]==pytest.approx(1/.6)
    with pytest.raises(ValueError,match="global_identity_conservation"):
        a.update({},[],[],10,.05)


def support():
    return dict(lanes={f"main_0_{i}":dict(path=str(i),offset_m=0.,length_m=200.) for i in range(3)},
                path_lengths={str(i):200. for i in range(3)},
                coordinate_verified=True,engineering_position_uncertainty_m=0.,
                cross_edge_verified=False,unknown_paths=[])


def qrow(vid,x,lane="main_0_0",speed=0.):
    return state(vid,x=x,speed=speed,lane=lane,edge="main_0")


def snapshot(t,rows,pending=0,physical=False):
    return queue_snapshot(list(rows),t,support(),QUEUE_CONFIG,pending=pending,
                          physical_entry_space=physical,downstream_context=True)


def test_pending_alone_and_two_lanes_cannot_create_queue():
    o=snapshot(0,[qrow("a",10),qrow("b",15,"main_0_1")],pending=100)
    assert not o["components"]
    r=QueueTracker(QUEUE_CONFIG).update(o)
    assert r["state"]=="No On-Road Queue" and r["entry_spillback_supported"] is False


def test_physical_rear_and_net_gap_and_partial_lane_queue():
    o=snapshot(0,[qrow("a",45),qrow("b",60)])
    c=o["components"][0]
    assert c["upstream_boundary_m"]==40 and c["max_net_gap_m"]==10
    assert o["queued_paths"]==["0"] and not o["all_paths_queued"]
    assert c["inlet_adjacent"]


def test_internal_queue_before_inlet_and_actual_inlet_persistence():
    tracker=QueueTracker(QUEUE_CONFIG)
    r=tracker.update(snapshot(0,[qrow("a",175),qrow("b",190)],pending=5,physical=True))
    assert r["state"]=="On-Road Queue Observed"
    # A connected chain from inlet to downstream anchor; fixed identities.
    rows=[qrow(str(i),x) for i,x in enumerate(range(10,191,15))]
    for t in [1,2,3]:r=tracker.update(snapshot(t,rows,pending=5,physical=True))
    assert r["entry_spillback_supported"] and r["state"]=="Entry Spillback Supported"


def test_lane_change_and_missing_snapshot_break_member_continuity():
    tracker=QueueTracker(QUEUE_CONFIG)
    rows=[qrow(str(i),x) for i,x in enumerate(range(10,191,15))]
    tracker.update(snapshot(0,rows,pending=5,physical=True))
    for row in rows:row["lane_id"]="main_0_1"
    r=tracker.update(snapshot(1,rows,pending=5,physical=True))
    assert not r["entry_spillback_supported"] and r["lane_change_member_resets"]==len(rows)
    r=tracker.update(snapshot(3,rows,pending=5,physical=True))
    assert not r["entry_spillback_supported"] and r["temporal_breaks"]==1


def test_unverified_or_missing_spatial_support_is_evidence_insufficient():
    s=support();s["coordinate_verified"]=False
    o=queue_snapshot([qrow("a",10),qrow("b",20)],0,s,QUEUE_CONFIG,pending=5,
                     physical_entry_space=True,downstream_context=True)
    assert QueueTracker(QUEUE_CONFIG).update(o)["state"]=="Evidence Insufficient"


def test_upstream_extension_requires_current_not_past_component():
    tracker=QueueTracker(QUEUE_CONFIG)
    rows=[qrow("a",175),qrow("b",190)]
    tracker.update(snapshot(0,rows))
    rows.insert(0,qrow("c",160))
    assert tracker.update(snapshot(1,rows))["upstream_extension_observed"]
    assert tracker.update(snapshot(2,[]))["state"]=="No On-Road Queue"


def test_cross_edge_queue_requires_verified_explicit_path_support():
    s=support()
    s["lanes"]["main_1_0"]=dict(path="0",offset_m=100.,length_m=100.)
    a=qrow("a",95.);b=qrow("b",10.,"main_1_0");b["edge_id"]="main_1"
    kwargs=dict(pending=0,physical_entry_space=False,downstream_context=True)
    assert not queue_snapshot([a,b],0,s,QUEUE_CONFIG,**kwargs)["components"]
    s["cross_edge_verified"]=True
    c=queue_snapshot([a,b],0,s,QUEUE_CONFIG,**kwargs)["components"][0]
    assert c["max_net_gap_m"]==10. and c["upstream_boundary_m"]==90.


def test_unknown_precision_cannot_qualify_inlet():
    s=support();s["engineering_position_uncertainty_m"]="Unknown"
    o=queue_snapshot([qrow("a",10),qrow("b",20)],0,s,QUEUE_CONFIG,pending=5,
                     physical_entry_space=True,downstream_context=True)
    assert o["components"][0]["inlet_adjacent"] is None
    assert QueueTracker(QUEUE_CONFIG).update(o)["state"]=="Evidence Insufficient"


def test_integration_admission_prevents_main_freeze(tmp_path):
    import json
    from riskprop.stage_0_5_b12_runtime import freeze_main
    (tmp_path/"observability_integration_audit.json").write_text(json.dumps(dict(B1_2_MAIN_MATRIX_ALLOWED=False)))
    with pytest.raises(PermissionError,match="not admitted"):freeze_main(tmp_path)
    assert not (tmp_path/"experiment_plan.json").exists()


def test_coordinate_support_includes_internal_length_and_rejects_gap(tmp_path):
    from riskprop.stage_0_5_b12_network import coordinate_support
    import xml.etree.ElementTree as ET
    root=ET.Element("net")
    for edge,start,end in [("main_0",0,100),(":j_0",100,102),("main_1",102,202),("main_2",204,304)]:
        e=ET.SubElement(root,"edge",id=edge)
        for i in range(3):ET.SubElement(e,"lane",id=f"{edge}_{i}",index=str(i),length=str(end-start),shape=f"{start},{i} {end},{i}")
    for i in range(3):
        ET.SubElement(root,"connection",dict(**{"from":"main_0","to":"main_1"},fromLane=str(i),toLane=str(i),via=f":j_0_{i}"))
        ET.SubElement(root,"connection",dict(**{"from":":j_0","to":"main_1"},fromLane=str(i),toLane=str(i)))
        ET.SubElement(root,"connection",dict(**{"from":"main_1","to":"main_2"},fromLane=str(i),toLane=str(i)))
    p=tmp_path/"network.xml";ET.ElementTree(root).write(p)
    s=coordinate_support(p)
    assert s["coordinate_verified"] and s["path_lengths"]["0"]==202.
    assert s["lanes"]["main_1_0"]["offset_m"]==102.
    root.find("edge[@id='main_1']/lane").set("shape","103,0 202,0")
    ET.ElementTree(root).write(p)
    assert not coordinate_support(p)["coordinate_verified"]
