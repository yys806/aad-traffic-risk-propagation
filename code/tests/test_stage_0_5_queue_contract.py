"""Prospective synthetic truths and explicit limitations of queue candidates."""
from copy import deepcopy
import pytest
from riskprop.stage_0_5_contract_fixtures import synthetic_queue_cases,QUEUE_CONFIG,snapshot,vehicle
from riskprop.stage_0_5_queue_contract import observe_queue,qualify_series


@pytest.mark.parametrize("case",synthetic_queue_cases(),ids=lambda c:c["id"])
def test_vehicle_graph_against_independent_queue_truth(case):
    observations=[observe_queue(f,QUEUE_CONFIG,"vehicle_graph") for f in case["frames"]]
    result=qualify_series(observations,QUEUE_CONFIG)
    truth=case["truth"];last=observations[-1]
    assert bool(last["components"])==truth["queue"]
    assert len(last["components"])==truth["components"]
    assert result["inlet_adjacent_queue_observed"]==truth["inlet"]
    assert result["entry_spillback_supported"]==truth["spillback"]
    if "causal_queue" in truth:
        assert result["onroad_queue_observed"] is truth["causal_queue"] and result["state"]=="Evidence Insufficient"
    if truth.get("extension"):assert result["upstream_extension_observed"]
    if truth.get("front_censored"):
        assert result["state"]=="Evidence Insufficient"
        assert last["components"][0]["upstream_boundary_m"] is None
    if "front_m" in truth:assert last["components"][0]["upstream_boundary_m"]==truth["front_m"]


def test_external_pending_never_substitutes_for_onroad_queue():
    c=synthetic_queue_cases()[1]
    for method in ["legacy_grid","grid_candidate","vehicle_graph"]:
        r=qualify_series([observe_queue(f,QUEUE_CONFIG,method) for f in c["frames"]],QUEUE_CONFIG)
        assert not r["onroad_queue_observed"] and not r["entry_spillback_supported"]


def test_pooled_legacy_grid_can_merge_two_different_lanes():
    f=synthetic_queue_cases()[8]["frames"][0]
    assert len(observe_queue(f,QUEUE_CONFIG,"legacy_grid")["components"])==1
    assert not observe_queue(f,QUEUE_CONFIG,"grid_candidate")["components"]
    assert not observe_queue(f,QUEUE_CONFIG,"vehicle_graph")["components"]


def test_grid_candidates_cannot_resolve_two_groups_inside_one_cell():
    f=synthetic_queue_cases()[10]["frames"][0]
    assert len(observe_queue(f,QUEUE_CONFIG,"grid_candidate")["components"])==1
    assert len(observe_queue(f,QUEUE_CONFIG,"vehicle_graph")["components"])==2


def test_sparse_front_boundary_has_more_support_than_old_grid_estimate():
    f=synthetic_queue_cases()[5]["frames"][0]
    old=observe_queue(f,QUEUE_CONFIG,"legacy_grid")["components"][0]
    new=observe_queue(f,QUEUE_CONFIG,"vehicle_graph")["components"][0]
    assert old["upstream_boundary_m"]==50 and new["upstream_boundary_m"]==40


def test_missing_frame_and_lane_change_do_not_carry_persistence():
    frames=[snapshot(t,list(range(10,191,15)),pending=5,physical_entry=True) for t in [0,1,3]]
    r=qualify_series([observe_queue(f,QUEUE_CONFIG,"vehicle_graph") for f in frames],QUEUE_CONFIG)
    assert not r["entry_spillback_supported"] and r["temporal_breaks"]==1


def test_bad_identity_or_coordinate_scope_is_not_no_queue():
    f=snapshot(0,[175,185,195]);f["vehicles"][1]["vehicle_id"]=f["vehicles"][0]["vehicle_id"]
    r=observe_queue(f,QUEUE_CONFIG,"vehicle_graph")
    assert not r["observation_valid"] and r["quality_errors"]
    f=snapshot(0,[175,185,195]);f["positions_verified"]=False
    r=qualify_series([observe_queue(f,QUEUE_CONFIG,"vehicle_graph")],QUEUE_CONFIG)
    assert r["state"]=="Evidence Insufficient"


def test_unknown_insertion_cause_cannot_be_upgraded_to_supported_spillback():
    f=[snapshot(t,list(range(10,191,15)),pending=5) for t in [0,1,2]]
    r=qualify_series([observe_queue(x,QUEUE_CONFIG,"vehicle_graph") for x in f],QUEUE_CONFIG)
    assert r["inlet_adjacent_queue_observed"] and not r["entry_spillback_supported"]
    assert r["entry_cause_status"]=="Unresolved"


def test_density_denominator_does_not_shrink_when_one_lane_is_empty():
    f=snapshot(0,[175,185],supported_lanes=["e_0","e_1"])
    r=observe_queue(f,QUEUE_CONFIG)
    assert r["local_density_veh_km_lane"]==pytest.approx(2/(.2*2))


def test_conservation_and_declared_lane_support_are_quality_requirements():
    f=snapshot(0,[175,185]);f["inserted_total"]+=1
    assert "vehicle_conservation" in observe_queue(f,QUEUE_CONFIG)["quality_errors"]
    f=snapshot(0,[],vehicles=[vehicle("v",175,lane="e_1")])
    assert "vehicle_outside_lane_support" in observe_queue(f,QUEUE_CONFIG)["quality_errors"]


def test_past_extension_does_not_replace_current_queue_absence():
    f=synthetic_queue_cases()[3]["frames"]+[snapshot(3,[],vehicles=[vehicle("f",100,20)])]
    r=qualify_series([observe_queue(x,QUEUE_CONFIG) for x in f],QUEUE_CONFIG)
    assert r["upstream_extension_observed"] and r["state"]=="No On-Road Queue"
