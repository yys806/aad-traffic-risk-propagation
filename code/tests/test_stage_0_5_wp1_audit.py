"""Independent hand-computed boundary cases for the offline Issue #1 audit."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "wp1_audit", Path(__file__).resolve().parents[1] / "scripts/audit_stage_0_5_work_package_1.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture():
    return pd.DataFrame(dict(
        dataset="ngsim", site="us101", window_id="fixture", trajectory_id="f",
        vehicle_id="f", incarnation_id="f", leader_id="l", leader_trajectory_id="l",
        leader_incarnation_id="l", diagnostic_clock_anchor_ms=0,
        global_time_ms=np.arange(7) * 100, frame_id=np.arange(7), time_s=np.arange(7) / 10,
        identity_break=False, observation_gap=False, leader_matched=True,
        identity_uncertain=False, leader_identity_uncertain=False,
        reliable_following_eligible=True, lane_id="1", y_m=[149, 149.9, 150, 151, 152, 153, 154],
        measurement_status="valid", ttc_valid=True, ttc_s=[3, 1, 1, 1, 1, 3, 3]))


def test_full_context_onset_and_entire_edge_support():
    d = fixture()
    r = audit.edge_and_event_audit(d, (0, .6), real=True)
    assert r["onset_N"] == 0
    assert r["confirmation_position_N_same_onset_window"] == 1
    assert r["D1_E_veh_s"] == .4
    r = audit.edge_and_event_audit(d, (.2, .4), real=True)
    assert r["onset_N"] == 0  # left cut must not manufacture a new event
    assert r["confirmation_time_sensitivity_N"] == 1
    assert r["D1_E_veh_s"] == .2


def test_incoming_break_does_not_erase_the_next_real_edge():
    d = fixture(); d["y_m"] = 200
    d.loc[0, "identity_break"] = True
    assert audit.edge_and_event_audit(d, (0, .6), real=True)["D1_E_veh_s"] == .6
    d.loc[3, "identity_break"] = True
    assert audit.edge_and_event_audit(d, (0, .6), real=True)["D1_E_veh_s"] == .5


def test_missing_leader_points_are_not_following_time():
    d = fixture(); d["y_m"] = 200
    d["leader_id"] = None; d["leader_incarnation_id"] = None
    d["reliable_following_eligible"] = False; d["measurement_status"] = "not_applicable"
    r = audit.edge_and_event_audit(d, (0, .6), real=False)
    assert r["diagnostic_point_E_veh_s"] == .6
    assert r["D1_E_veh_s"] == 0
    assert r["onset_rate_D1_audit"] is None


def test_right_confirmation_and_unconfirmed_tail_are_retained():
    d = fixture(); d["y_m"] = 200
    r = audit.edge_and_event_audit(d, (0, .25), real=True)
    assert r["onset_N"] == 1 and r["confirmation_after_window"] == 1
    r = audit.edge_and_event_audit(d.iloc[:3], (0, .2), real=True)
    assert r["onset_N"] == 0 and r["right_censored_unconfirmed"] == 1


def test_duplicate_clock_and_unknown_quality_fail_closed():
    d = fixture(); d.loc[2, "time_s"] = .1
    with pytest.raises(ValueError, match="duplicate"):
        audit.edge_and_event_audit(d, (0, .6), real=True)
    d = fixture(); d["leader_matched"] = None
    with pytest.raises(ValueError, match="unknown_boolean"):
        audit.edge_and_event_audit(d, (0, .6), real=True)


def test_partition_area_and_state_weights_hand_computed():
    d = pd.DataFrame(dict(lane_id="1", y_m=[175] * 10 + [225] * 10 + [325] * 10,
                          time_s=1., speed_mps=10., closing_speed_mps=0.))
    global_cloud = audit.cloud(d, (0, 30), "global_intersection")
    assert global_cloud.density_veh_km_lane.tolist() == pytest.approx([1 / 7.5, 1 / 15, 1 / 7.5])
    whole = audit.cloud(d, (0, 30), "whole200")
    assert whole.density_veh_km_lane.iloc[0] == pytest.approx(3 / 30)


def test_unapproved_temporal_and_outside_paths_rejected(tmp_path):
    reader = audit.Reader(tmp_path)
    for name in ["../private", "code/outputs/formal/calibration/stage_0_5_state_support_v1/temporal/x.parquet",
                 "code/outputs/formal/calibration/stage_0_5_state_support_v1/grid/us101__0820_0835/measured_state.parquet"]:
        with pytest.raises(ValueError):
            reader.path(name)
