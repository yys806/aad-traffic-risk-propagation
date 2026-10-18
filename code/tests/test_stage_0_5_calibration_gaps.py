"""Supplement contracts: source isolation, identity, and physical denominators."""
import numpy as np
import pandas as pd
import pytest

from riskprop.stage_0_5_calibration_gaps import (
    bind_raw_policy, controlled_join, density_slices, pooled_strata, crossing_counts,
    boundary_qualified_slices,
)
from riskprop.stage_0_5_sumo import Stage05AccessDenied


def test_raw_binding_rejects_validation_before_io():
    with pytest.raises(Stage05AccessDenied):
        bind_raw_policy("us101__0820_0835", "a" * 64)
    with pytest.raises(Stage05AccessDenied):
        bind_raw_policy("unknown", "a" * 64)


def test_join_checks_time_and_does_not_resolve_duplicate_rows():
    raw = pd.DataFrame(dict(original_row_number=[1, 2], source_member=["m"]*2,
        Vehicle_ID=[7, 7], Frame_ID=[1, 2], Global_Time=[100, 200],
        v_Class=[2, 2], v_Length=[15., 15.], Local_Y=[10., 11.]))
    s = pd.DataFrame(dict(original_row_number=[1, 2], source_member=["m"]*2,
        original_vehicle_id=["7", "7"], frame_id=[1, 2], global_time_ms=[100, 999],
        y_m=[3.048, 3.3528]))
    joined, audit = controlled_join(s, raw)
    assert audit["matched_rows"] == 1 and audit["unresolved_rows"] == 1
    assert pd.isna(joined.loc[1, "v_Class"])
    duplicate = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    _, audit = controlled_join(s, duplicate)
    assert audit["duplicate_raw_keys"] == 2 and audit["matched_rows"] == 0


def test_density_counts_empty_local_frames_and_excludes_auxiliary_lane():
    # 600 observed frames, local vehicle present for half; a ramp vehicle is excluded.
    t = np.arange(600) / 10
    all_rows = pd.DataFrame(dict(time_s=t, y_m=500., lane_id="1", speed_mps=10.,
        trajectory_id="outside"))
    local = pd.DataFrame(dict(time_s=t[:300], y_m=200., lane_id="1", speed_mps=5.,
        trajectory_id="local"))
    ramp = local.assign(lane_id="6", trajectory_id="ramp")
    s = pd.concat([all_rows, local, ramp, all_rows.iloc[[-1]].assign(time_s=60.)])
    rows = density_slices(s)
    assert rows[0]["coverage_s"] == pytest.approx(60)
    assert rows[0]["density_veh_km_lane"] == pytest.approx(.5)  # 0.5 veh / (0.2km*5)
    assert rows[0]["local_vehicle_seconds"] == pytest.approx(30)


def test_pooled_thresholds_share_one_definition_and_exclude_short_slice():
    rows = [{"source_group":g,"eligible":True,"density_veh_km_lane":x}
            for g,x in [("a",10),("a",20),("b",30),("b",40)]]
    rows += [{"source_group":"b","eligible":False,"density_veh_km_lane":999}]
    result = pooled_strata(rows)
    assert result["thresholds_veh_km_lane"] == pytest.approx([20,30])
    assert [r["density_stratum"] for r in result["slices"]] == [
        "Low-density","Low-density","Medium-density","High-density","Excluded"]


def test_crossings_use_adjacent_pairs_not_extents_or_state_count():
    # Last jump spans a gap: it cannot establish a measured passage.
    s = pd.DataFrame(dict(trajectory_id=["a"]*4,time_s=[0,.1,.2,1.],
        frame_id=[1,2,3,11],y_m=[140,160,140,310], lane_id=["1"]*4))
    r = crossing_counts(s, planes=[150.,300.])
    assert r[0]["forward_crossings"] == 1
    assert r[1]["forward_crossings"] == 0
    assert r[0]["lane_counts"] == {"1":1}


def test_boundary_guard_is_time_based_and_keeps_high_density_extreme():
    s=pd.DataFrame(dict(trajectory_id=["a","a","b","b"],time_s=[0,20,180,200]))
    rows=[dict(slice_start_s=a,slice_end_s=b,eligible=True,density_veh_km_lane=k)
          for a,b,k in [(0,60,20),(60,120,999),(120,180,40),(180,200,25)]]
    r=boundary_qualified_slices(rows,s)
    assert [x["eligible"] for x in r]==[False,True,True,False]
    assert r[1]["density_veh_km_lane"]==999


def test_benchmark_plan_is_bounded_and_preserves_loads_before_simulation():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/"scripts/benchmark_stage_0_5_calibration_loads.py"
    spec=importlib.util.spec_from_file_location("load_benchmark",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fleet=[dict(vehicles=n,candidate_vClass=v,length_m={"quantiles":{"0.5":l}})
           for n,v,l in [(1,"motorcycle",2),(97,"passenger",4.4),(2,"truck",10)]]
    d={"windows":{"w":{"fleet":{"vehicles":100,"classes":fleet}}}}
    rows=[dict(eligible=True,density_stratum=label,density_veh_km_lane=k,mean_speed_mps=v)
          for label,k,v in [("Low-density",30,15),("Medium-density",45,10),("High-density",60,5)]]
    plan=module.make_plan(d,{"slices":rows})
    assert len(plan["runs"])==4 and plan["optimization"] is False
    assert plan["seed"]==20261018 and plan["duration_s"]==300
    assert plan["runs"][-1]["target_density_veh_km_lane"]==60
    assert plan["runs"][-1]["inflow_veh_h"]==pytest.approx(3240)
    assert module.account(10,{"1","2"},{"1"},{"2"})["insertion_unserved_at_end"]==8
    assert module.account(10,{"1","2"},{"1"},{"2"})["conservation_residual"]==0


def test_portable_supplement_is_scoped_and_preserves_scientific_stop():
    import hashlib
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    p=root/"evidence/results/RES-STAGE-0.5-CALIBRATION-GAPS-V1"
    if not p.exists(): pytest.skip("supplement not exported yet")
    source=json.loads((p/"source_manifest.json").read_text(encoding="utf-8"))
    assert {m["source_group"] for m in source["members"]}=={
        "us101__0750_0805","us101__0805_0820"}
    assert all(m["role"]=="calibration" for m in source["members"])
    audit=json.loads((p/"audit.json").read_text(encoding="utf-8"))
    assert audit["validation_window_rows_materialised"]==0
    assert audit["formal_calibration_run"] is False
    assert audit["ready_to_start_stage_0_5_4b"] is False
    assert audit["gate"]=="pending_simulation_sample"
    assert audit["parameters_approved"]==[] and audit["tolerances_frozen"] is False
    for line in (p/"SHA256SUMS").read_text().splitlines():
        expected,name=line.split("  ",1)
        assert hashlib.sha256((p/name).read_bytes()).hexdigest()==expected
    assert not list(p.rglob("*.parquet")) and not list(p.rglob("*.txt"))


def test_zero_local_occupancy_keeps_speed_unobserved_in_stratum_summary():
    rows=[dict(source_group="a",eligible=True,density_veh_km_lane=0.,coverage_s=60.,
        local_vehicle_seconds=0.,mean_speed_mps=None,low_speed_share_below_5_mps=None)]
    result=pooled_strata(rows)
    assert result["summary"][0]["mean_speed_mps"] is None
    assert result["summary"][0]["density_veh_km_lane"]==0
