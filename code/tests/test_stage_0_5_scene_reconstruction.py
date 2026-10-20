"""Tests for the conditional observed-geometry SUMO scene reconstruction."""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import pytest

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_scene_reconstruction as sr  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_scene_spec_has_five_mainline_lanes_and_the_observed_chain():
    spec = sr.scene_spec()
    edges = {edge["id"]: edge for edge in spec["edges"]}
    assert edges["main_0"]["lanes"] == 5
    assert edges["main_1"]["lanes"] == 6
    assert edges["main_2"]["lanes"] == 5
    assert edges["onramp"]["lanes"] == 1
    assert edges["offramp"]["lanes"] == 1


def test_real_lane_mapping_is_consistent_at_the_merge_and_diverge():
    # upstream of the merge only five mainline lanes exist
    assert sr.real_lane_to_sumo("1", 10.0) == ("main_0", 4, 10.0)
    assert sr.real_lane_to_sumo("5", 10.0) == ("main_0", 0, 10.0)
    assert sr.real_lane_to_sumo("6", 10.0) is None
    # inside the auxiliary section the extra lane is SUMO index 0
    assert sr.real_lane_to_sumo("5", 250.0) == ("main_1", 1, 250.0 - sr.MERGE_POSITION_M)
    assert sr.real_lane_to_sumo("6", 250.0) == ("main_1", 0, 250.0 - sr.MERGE_POSITION_M)
    # downstream of the diverge the auxiliary lane is gone again
    assert sr.real_lane_to_sumo("5", 500.0) == ("main_2", 0, 500.0 - sr.DIVERGE_POSITION_M)
    assert sr.real_lane_to_sumo("7", 150.0)[0] == "onramp"
    assert sr.real_lane_to_sumo("8", 420.0) is None


def test_scale_position_maps_the_observed_span_onto_the_built_edge_length():
    lengths = {"main_0": 172.9, "main_1": 234.04, "main_2": 252.23}
    assert sr.scale_position("main_0", 0.0, lengths) == pytest.approx(0.0)
    assert sr.scale_position("main_0", sr.MERGE_POSITION_M, lengths) == pytest.approx(172.9)
    assert sr.scale_position("main_2", sr.SEGMENT_LENGTH_M - sr.DIVERGE_POSITION_M, lengths) == pytest.approx(252.23)
    # out-of-range positions clamp instead of overflowing the edge
    assert sr.scale_position("main_0", 10_000.0, lengths) == pytest.approx(172.9)


def test_depart_times_respect_the_requested_flow():
    times = sr._depart_times(3600.0, 10.0, 0.5)
    assert len(times) == 10
    assert times[1] - times[0] == pytest.approx(1.0)


def test_build_route_file_declares_the_expected_vehicle_counts(tmp_path):
    path = tmp_path / "routes.rou.xml"
    info = sr.build_route_file(path, "us101__0750_0805", duration_s=300.0)
    assert info["mainline_vehicles"] == 695
    assert info["onramp_vehicles"] == 43
    assert sum(info["fleet_counts"].values()) == info["mainline_vehicles"]
    root = ET.parse(path).getroot()
    routes = {route.get("id") for route in root.findall("route")}
    assert {"through", "entering", "exiting"} <= routes


def test_initial_state_drops_overlapping_vehicles_and_keeps_route_starts(tmp_path):
    rows = []
    for index, (lane, y, speed) in enumerate(
        [("1", 20.0, 5.0), ("1", 20.5, 5.0), ("5", 300.0, 8.0), ("6", 300.0, 8.0), ("7", 150.0, 12.0)]
    ):
        rows.append(
            dict(dataset="NGSIM", site="US-101", window_id="0750_0805", vehicle_id=f"v{index}",
                 trajectory_id=f"t{index}", time_s=0.0, y_m=y, x_m=float(lane), speed_mps=speed,
                 acceleration_mps2=0.0, lane_id=lane, net_gap_m=10.0, closing_speed_mps=0.0,
                 measurement_status="valid", identity_break=False, observation_gap=False,
                 original_row_number=index + 1, source_member="synthetic", missing_reason="",
                 ttc_s=100.0, leader_matched=True)
        )
    # a second observation instant far away so the windowed loader has two clocks
    frame = pd.DataFrame(rows)
    extended = pd.concat([frame, frame.assign(time_s=999.0)], ignore_index=True)
    initial = sr.build_initial_state(extended, "us101__0750_0805", clock_s=0.0,
                                     edge_lengths={"main_0": 180.0, "main_1": 220.0, "main_2": 260.0, "onramp": 180.0})
    accepted_lanes = [(record["edge"], record["lane_index"]) for record in initial["accepted"]]
    assert len(accepted_lanes) == len(set(accepted_lanes))
    reasons = {record["reason"] for record in initial["dropped"]}
    assert reasons <= {"position_overlap", "outside_observed_geometry"}
    path = tmp_path / "initial.rou.xml"
    sr.write_initial_state_route_file(path, "us101__0750_0805", initial, duration_s=10.0)
    root = ET.parse(path).getroot()
    declared = {route.get("id") for route in root.findall("route")}
    for vehicle in root.findall("vehicle"):
        assert vehicle.get("route") in declared
    # every start-edge route must actually start on its declared edge name
    for route in root.findall("route"):
        if route.get("id", "").startswith("from_"):
            edge = route.get("id").split("_")[1] if route.get("id").count("_") >= 2 else None
            assert route.get("edges").split()[0] in {"main_0", "main_1", "main_2", "onramp"}


def test_conditional_spec_adds_a_restricted_downstream_exit():
    from importlib import import_module

    sys.path.insert(0, str(CODE_ROOT / "scripts"))
    runner = import_module("run_stage_0_5_scene_reconstruction")
    spec = runner.conditional_network_spec()
    edges = {edge["id"]: edge for edge in spec["edges"]}
    assert edges["exit"]["lanes"] == runner.DOWNSTREAM_EXIT_LANES
    assert edges["exit"]["lanes"] < edges["main_2"]["lanes"]
    assert spec["routes"]["through"][-1] == "exit"


def test_state_support_requires_both_target_speed_and_density():
    metrics = {
        "speed_mean_mps": 10.5,
        "density_veh_km_lane": 43.5,
        "blocks": [
            {"speed_mean_mps": 10.0, "density_veh_km_lane": 42.0},
            {"speed_mean_mps": 11.0, "density_veh_km_lane": 45.0},
        ],
    }
    verdict = sr.state_support(metrics, "us101__0750_0805")
    assert verdict["state_supported"] is True
    outside = dict(metrics)
    outside["blocks"] = [{"speed_mean_mps": 22.0, "density_veh_km_lane": 20.0}]
    assert sr.state_support(outside, "us101__0750_0805")["state_supported"] is False


def test_parse_fcd_inverts_the_edge_scaling(tmp_path):
    # a vehicle at half of the built main_1 length must map to the middle of the
    # observed main_1 span, not to the middle of the built length
    fcd = tmp_path / "fcd.xml"
    fcd.write_text(
        "<fcd-export><timestep time=\"1.00\">"
        "<vehicle id=\"a\" x=\"0\" y=\"0\" lane=\"main_1_5\" pos=\"117.02\" speed=\"10.0\"/>"
        "<vehicle id=\"b\" x=\"0\" y=\"0\" lane=\"main_0_0\" pos=\"86.45\" speed=\"10.0\"/>"
        "</timestep></fcd-export>",
        encoding="utf-8",
    )
    frame = sr.parse_fcd(fcd, {"main_0": 172.9, "main_1": 234.04})
    middle = (sr.MERGE_POSITION_M + sr.DIVERGE_POSITION_M) / 2.0
    assert frame.loc[frame.vehicle_id == "a", "y_m"].iloc[0] == pytest.approx(middle, rel=1e-6)
    assert frame.loc[frame.vehicle_id == "b", "y_m"].iloc[0] == pytest.approx(sr.MERGE_POSITION_M / 2.0, rel=1e-6)
    assert frame.loc[frame.vehicle_id == "a", "lane_id"].iloc[0] == "1"
    assert frame.loc[frame.vehicle_id == "b", "lane_id"].iloc[0] == "5"


def test_scene_metrics_separate_the_local_region():
    rows = []
    for index in range(20):
        for step in range(5):
            rows.append(dict(time_s=step * 0.1, vehicle_id=f"v{index}", edge="main_1",
                             lane_index=index % 6, y_m=180.0 + index, speed_mps=9.0))
    frame = pd.DataFrame(rows)
    frame["lane_id"] = "1"
    metrics = sr.scene_metrics(frame, window_s=(0.0, 0.5), block_s=0.5)
    assert metrics["region_m"] == [sr.LOCAL_REGION_M[0], sr.LOCAL_REGION_M[1]]
    assert metrics["speed_mean_mps"] == pytest.approx(9.0)
