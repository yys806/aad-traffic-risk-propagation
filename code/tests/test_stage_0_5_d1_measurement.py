"""Hand-derived boundary cases and independent native-adapter comparisons."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from riskprop.stage_0_5_d1_measurement import (
    MeasurementContractError, local_d1_measurement, offset100_cloud, time_gap_values,
)
from riskprop.stage_0_5_sumo import compute_exposure, build_sumo_p2_events
from riskprop import stage_0_5_state_support as ss


def frame():
    return pd.DataFrame(dict(run_id="r", scenario_id="s", vehicle_id="f", incarnation_id="f1",
        leader_id="l", leader_incarnation_id="l1", time_s=np.arange(7)/10,
        lane_id="1", y_m=200., speed_mps=5., leader_speed_mps=4., closing_speed_mps=1., net_gap_m=1.,
        reliable_following_eligible=True, ttc_valid=True,
        measurement_status="valid", ttc_s=[3.,1.,1.,1.,1.,3.,3.], drac_mps2=1.))


def test_full_source_native_oracle_matches_events_and_edges():
    d = frame()
    native, exposure = build_sumo_p2_events(d)
    result = local_d1_measurement(d, (0,.6), strict=True)
    assert result["local_evaluable_s"] == pytest.approx(exposure["p2_evaluable_following_exposure_s"])
    assert result["local_evaluable_s"] == pytest.approx(.6)
    assert result["onset_events"] == 1
    assert [e["onset_s"] for e in result["events"]] == native.event_start_s.tolist()
    assert result["events"][0]["confirm_s"] == pytest.approx(.3)


def test_left_continuation_and_distinct_confirmation_attribution():
    d = frame(); d["y_m"]=[149,149.9,150,151,152,153,154]
    result=local_d1_measurement(d,(0,.6))
    assert result["onset_events"]==0 and result["confirmation_position_events"]==1
    assert result["local_evaluable_s"]==pytest.approx(.4)
    result=local_d1_measurement(d,(.2,.4))
    assert result["onset_events"]==0 and result["left_continuing_risk_segments"]==1
    assert result["confirmation_time_sensitivity_events"]==1
    assert result["local_evaluable_s"]==pytest.approx(.2)


def test_confirmation_context_and_unconfirmed_tail():
    result=local_d1_measurement(frame(),(0,.25))
    assert result["onset_events"]==1 and result["confirmation_after_window"]==1
    result=local_d1_measurement(frame().iloc[:3],(0,.2))
    assert result["onset_events"]==0 and result["right_censored_unconfirmed"]==1


@pytest.mark.parametrize("field",["incarnation_id","leader_incarnation_id"])
def test_identity_change_never_bridges_risk_or_exposure(field):
    d=frame();d.loc[3:,field]="new"
    result=local_d1_measurement(d,(0,.6))
    assert result["onset_events"]==0
    assert result["local_evaluable_s"]==pytest.approx(.5)


def test_no_leader_zero_exposure_differs_from_zero_events():
    d=frame();d["leader_id"]=None;d["leader_incarnation_id"]=None
    d["reliable_following_eligible"]=False;d["measurement_status"]="not_applicable";d["ttc_valid"]=False
    r=local_d1_measurement(d,(0,.6))
    assert r["onset_events"]==0 and r["local_evaluable_s"]==0
    assert r["rate_per_evaluable_vehicle_hour"] is None
    d=frame();d["ttc_s"]=3.
    assert local_d1_measurement(d,(0,.6))["rate_per_evaluable_vehicle_hour"]==0


def test_invalid_quality_endpoints_excluded_but_not_relabelled_zero_risk():
    d=frame();d.loc[3,"measurement_status"]="invalid";d.loc[3,"ttc_valid"]=False
    r=local_d1_measurement(d,(0,.6))
    assert r["local_evaluable_s"]==pytest.approx(.4)
    assert r["unavailable_point_counts"]["invalid"]==1


@pytest.mark.parametrize("field,value",[("time_s",np.nan),("time_s",.15),("measurement_status","uncertain"),("ttc_valid",None)])
def test_unknown_or_invalid_clock_fails_closed(field,value):
    d=frame();d[field]=d[field].astype(object);d.loc[2,field]=value
    with pytest.raises(MeasurementContractError):local_d1_measurement(d,(0,.6))


def test_duplicate_clock_and_missing_grid_identity():
    d=frame();d.loc[2,"time_s"]=.1
    with pytest.raises(MeasurementContractError):local_d1_measurement(d,(0,.6))
    d=frame().drop(columns="leader_incarnation_id")
    r=local_d1_measurement(d,(0,.6))
    assert r["eligibility"]=="degraded_missing_fields" and r["local_evaluable_s"] is None
    with pytest.raises(MeasurementContractError):local_d1_measurement(d,(0,.6),strict=True)


def test_spatial_boundaries_and_entire_time_edge():
    d=frame();d["y_m"]=[149.9,150,249.9,250,349.9,350,350]
    assert local_d1_measurement(d,(0,.6))["local_evaluable_s"]==pytest.approx(.3)
    assert local_d1_measurement(frame(),(.15,.45))["local_evaluable_s"]==pytest.approx(.2)


def test_common_offset100_area_and_partial_time_block():
    d=pd.DataFrame(dict(lane_id="1", y_m=[150]*10+[250]*10+[350]*10,
                        time_s=30.,speed_mps=10.,closing_speed_mps=0.))
    blocks=offset100_cloud(d,(0,45))
    assert len(blocks)==4
    assert blocks.width_m.tolist()==[100]*4
    assert blocks.states.tolist()==[0,0,10,10]
    assert blocks.density_veh_km_lane.tolist()==pytest.approx([0,0,1/7.5,1/7.5])
    assert blocks.support_status.tolist()[:2]==["insufficient_state_support"]*2


def test_time_gaps_use_aligned_rows_and_no_hidden_speed_floor():
    r=time_gap_values([10,10,10],[5,0,-1],[1,1,-1],[4,4,4])
    assert r["net_time_gap_s"][0]==2
    assert r["front_bumper_time_headway_s"][0]==2.8
    assert r["closing_time_proxy_s"][0]==10
    assert np.isnan(r["net_time_gap_s"][1:]).all()
    assert np.isnan(time_gap_values([10],[5],[1])["front_bumper_time_headway_s"]).all()


def test_actual_state_runner_uses_d1_not_point_exposure(tmp_path,monkeypatch):
    p=Path(__file__).resolve().parents[1]/"scripts/run_stage_0_5_state_support.py"
    spec=importlib.util.spec_from_file_location("state_runner_d1",p);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    tail=frame();tail["time_s"]+=300
    d=pd.concat([frame(),tail],ignore_index=True)
    monkeypatch.setattr(runner,"build_candidate_network",lambda *a,**k:{"network":tmp_path/"network.net.xml"})
    monkeypatch.setattr(runner,"network_edge_lengths",lambda *a:{})
    monkeypatch.setattr(runner,"parse_fcd",lambda *a:d)
    monkeypatch.setattr(ss,"fcd_to_state_frame",lambda *a,**k:d)
    monkeypatch.setattr(ss,"measure_state_frame",lambda *a:d)
    monkeypatch.setattr(ss,"run_sumo",lambda *a,**k:{"returncode":0,"wall_s":0,"log_tail":"","teleports":0,"collisions":0})
    record=runner.run_cell(tmp_path/"run",dict(cell_id="fixture",condition="us101__0750_0805",behaviour="B_frozen",downstream_free_speed_mps=10.),{},1,with_p2=True)
    assert record["descriptors"]["p2_evaluable_exposure_veh_s"]==pytest.approx(.6)
    assert record["descriptors"]["legacy_point_evaluable_exposure_veh_s"]==pytest.approx(.7)
    assert record["p2_local_rate_per_vehicle_hour"]==pytest.approx(6000.)
    assert record["p2_network_rate_per_vehicle_hour"] is None


def test_native_lane_transition_breaks_physical_edge_and_risk_segment():
    d=frame();d["native_lane_id"]=["main_0_0"]*2+["main_1_1"]*5
    r=local_d1_measurement(d,(0,.6))
    assert r["local_evaluable_s"]==pytest.approx(.5)
    assert len(r["events"])==1
    assert r["events"][0]["onset_s"]==pytest.approx(.2)
