"""Unified offline measurement for B00/B10/B01/B11 R1 diagnostics.

The analyzer is fail-closed: it uses the existing SUMO state adapter and D1
contract, never infers missing paths or risk, and keeps lifecycle and support
counts separate from formal P2 events.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskprop.stage_0_5_d1_measurement import inside_region, local_d1_measurement, offset100_cloud
from riskprop.stage_0_5_scene_reconstruction import network_edge_lengths, parse_fcd
from riskprop.stage_0_5_state_support import fcd_to_state_frame, measure_state_frame, route_length_map


RESULT = "RES-STAGE-0.5-R1-DIAGNOSTICS-20261028"
WIN = (120.0, 390.0)
TARGET = (150.0, 350.0)
SOURCE = (0.0, 150.0)
LANES = {"1", "2", "3", "4", "5"}
R0_COHORT_SHA = "76db89e2ff2d9df997516b59a23bc4d88a85c7a0161dca6a222f2a8bfee277f8"
BASELINE_ROUTE = Path("evidence/results/RES-STAGE-0.5-R1-DIAGNOSTICS-20261028/inputs/B00_routes.rou.xml")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def finite_summary(values):
    a = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(float)
    a = a[np.isfinite(a)]
    return {"n": int(len(a)), "mean": float(a.mean()) if len(a) else None,
            "quantiles": {str(q): float(np.quantile(a, q)) for q in (.05, .5, .95)} if len(a) else None}


def route_inventory(path: Path):
    root = ET.fromstring(path.read_bytes())
    routes = {n.get("id"): n.get("edges", "").split() for n in root.findall("route")}
    vehicles = {n.get("id"): n for n in root.findall("vehicle")}
    cohort = sorted(k for k, v in vehicles.items() if any(e in {"main_0", "main_1"} for e in routes[v.get("route")]))
    initial = sorted(k for k in cohort if k.startswith("i"))
    return root, routes, vehicles, cohort, initial


def ramp_departure_rows(path: Path, baseline_vehicles, vehicles):
    rows = []
    for ident, v in vehicles.items():
        if ident.startswith("i") or v.get("route") != "entering":
            continue
        original = baseline_vehicles[ident]
        rows.append(dict(id=ident, block=int(float(original.get("depart")) // 60),
                         original_depart_s=float(original.get("depart")),
                         candidate_depart_s=float(v.get("depart"))))
    return rows


def lifecycle(identity_path: Path, *, route_path: Path, baseline_path: Path):
    identity = json.loads(identity_path.read_bytes())
    _, _, vehicles, cohort, initial = route_inventory(route_path)
    _, _, baseline_vehicles, _, _ = route_inventory(baseline_path)
    rows = identity["vehicles"]
    ramp = ramp_departure_rows(route_path, baseline_vehicles, vehicles)
    by_id = {r["id"]: r for r in ramp}
    actual_ramp = []
    for r in ramp:
        x = rows[r["id"]]
        actual_ramp.append({**r, "actual_departure_s": x.get("actual_departure_s"),
                            "depart_delay_s": x.get("depart_delay_s"), "state": x.get("state"),
                            "native_insertion_status": x.get("native_insertion_status"),
                            "on_road_observed": x.get("on_road_observed"),
                            "right_censored": x.get("right_censored"),
                            "discarded_at": x.get("discarded_at"),
                            "tripinfo": x.get("tripinfo")})
    states = identity["states"]
    declared = len(rows)
    inserted = sum(x.get("actual_departure_s") is not None for x in rows.values())
    pending = sum(x.get("state") == "pending_native" for x in rows.values())
    discarded = sum(x.get("state") == "discarded_native" for x in rows.values())
    active = sum(x.get("state") == "active_native" for x in rows.values())
    arrived = sum(x.get("state") == "arrived_native" for x in rows.values())
    return dict(declared=declared, inserted=inserted, pending=pending, discarded=discarded,
                active=active, arrived=arrived, identity_states=states,
                identity_accounting_complete=identity["identity_accounting_complete"],
                native_departure_clock_complete=identity["native_departure_clock_complete"],
                collision_coverage_complete=identity["collision_coverage_complete"],
                cohort_count=len(cohort), cohort_initial_count=len(initial),
                cohort_sha256=hashlib.sha256(("\n".join(cohort) + "\n").encode()).hexdigest(),
                ramp_declared_count=len(ramp), ramp_rows=actual_ramp,
                ramp_block_counts={str(k): sum(r["block"] == k for r in ramp) for k in sorted({r["block"] for r in ramp})},
                cohort_ids=cohort)


def controls(receipt_path: Path, arm: str):
    c = json.loads(receipt_path.read_bytes())["controls"]
    expected = [10] * 8400 if arm == "B01" else [10] * 3600 + [5] * 1200 + [10] * 3600
    ok_len = len(c) == 8400
    failures = sum(len(x.get("failures", [])) for x in c)
    readback = all(set(x.get("native_lane_limits", {})) == {f"main_2_{i}" for i in range(5)} and
                   all(abs(float(v) - float(x["target_mps"])) <= 1e-9 for v in x.get("native_lane_limits", {}).values()) for x in c)
    clock = all(abs(float(x.get("applied_before_step_s", -1)) - i * .05) <= 1e-7 and
                abs(float(x.get("native_clock_before_s", -1)) - i * .05) <= 1e-7 and
                x.get("target_mps") == expected[i] for i, x in enumerate(c)) if ok_len else False
    return dict(step_count=len(c), expected_step_count=8400, failures=failures,
                all_lane_readback=readback, clock_and_schedule=clock,
                t180=c[3600] if ok_len else None, t240=c[4800] if ok_len else None,
                controls_pass=bool(ok_len and failures == 0 and readback and clock))


def analyze_arm(arm: str, fcd_path: Path, route_path: Path, out: Path, *, run_id: str, net_path: Path, b00=False):
    edge_lengths = network_edge_lengths(net_path)
    fcd = parse_fcd(fcd_path, edge_lengths)
    states = fcd_to_state_frame(fcd, route_length_map(route_path), run_id=run_id, scenario_id="US-101 0750", seed=20261201)
    measured = measure_state_frame(states)
    measured.to_parquet(out / "measured_state.parquet", index=False)
    root, routes, vehicles, cohort, initial = route_inventory(route_path)
    cohort_frame = measured[measured.vehicle_id.isin(cohort)].copy()
    source = local_d1_measurement(measured, WIN, region=SOURCE, strict=True)
    target = local_d1_measurement(cohort_frame, WIN, region=TARGET, strict=True)
    all_target = local_d1_measurement(measured, WIN, region=TARGET, strict=True)
    cloud = offset100_cloud(cohort_frame, WIN)
    cells = []
    for row in cloud.itertuples(index=False):
        cell = local_d1_measurement(cohort_frame, (row.block_start_s, row.block_end_s),
                                    region=(row.y_start_m, row.y_end_m), strict=True)
        cells.append(dict(t_block=int(row.t_block), y_block=int(row.y_block),
                          D1_E_veh_s=cell["local_evaluable_s"], P2_events=cell["onset_events"],
                          support_status=row.support_status, states=int(row.states),
                          density_veh_km_lane=row.density_veh_km_lane,
                          speed_mean_mps=row.speed_mean_mps, low_speed_share=row.low_speed_share,
                          closing_speed_mean_mps=row.closing_speed_mean_mps))
    life = lifecycle(out / "identity_summary.json", route_path=route_path, baseline_path=BASELINE_ROUTE)
    receipt = json.loads((out / "controller_receipt.json").read_bytes())
    control = controls(out / "controller_receipt.json", arm)
    local = cohort_frame[inside_region(cohort_frame, TARGET) & cohort_frame.time_s.ge(WIN[0]) & cohort_frame.time_s.lt(WIN[1])]
    valid = local[local.measurement_status.eq("valid") & local.ttc_valid]
    source_events = [e for e in source.get("events", []) if e.get("onset_in_window") and e.get("onset_inside")]
    for e in source_events:
        v = measured[(measured.vehicle_id.astype(str) == str(e["vehicle_id"])) & (measured.time_s == e["onset_s"])]
        e["onset_position_m"] = float(v.y_m.iloc[0]) if len(v) else None
        e["confirmation_position_m"] = None
        v2 = measured[(measured.vehicle_id.astype(str) == str(e["vehicle_id"])) & (measured.time_s == e["confirm_s"])]
        if len(v2): e["confirmation_position_m"] = float(v2.y_m.iloc[0])
    result = dict(schema="aad.r1.arm-measurement.v1", arm=arm, run_id=run_id,
        execution=dict(duration_s=420, internal_step_s=.05, recording_step_s=.1, fcd_rows=int(len(fcd)),
                       recording_times=int(fcd.time_s.nunique()), min_time_s=float(fcd.time_s.min()), max_time_s=float(fcd.time_s.max()),
                       native_exit_code=receipt.get("exit_code"), controller_error=receipt.get("error"), controls=control),
        lifecycle=life,
        source_event_measurement=dict(region="S_UPSTREAM_MAIN", window_s=list(WIN), formal_rule="stage_0_2_formal_risk_measurement_p2_v1",
                                      onset_events=int(len(source_events)), events=source_events,
                                      incomplete_candidates=source.get("incomplete_candidates", []),
                                      D1_E_veh_s=source.get("local_evaluable_s"), reliable_D1_E_veh_s=source.get("reliable_local_s"),
                                      measurement_status=measured.loc[measured.y_m.lt(150) & measured.time_s.ge(WIN[0]) & measured.time_s.lt(WIN[1]), "measurement_status"].value_counts().to_dict()),
        target_measurement=dict(cohort="C_INPUT_ROUTE", region="main_0/main_1 lanes1-5 y[150,350)", window_s=list(WIN),
                                D1_E_veh_s=target.get("local_evaluable_s"), reliable_D1_E_veh_s=target.get("reliable_local_s"),
                                P2_events=target.get("onset_events"), confirmation_position_events=target.get("confirmation_position_events"),
                                confirmation_after_window=target.get("confirmation_after_window"),
                                right_censored_unconfirmed=target.get("right_censored_unconfirmed"),
                                incomplete_candidates=target.get("incomplete_candidates", []),
                                all_vehicle_reference=all_target,
                                measurement_status=local.measurement_status.value_counts().to_dict(),
                                valid_ttc_summary=finite_summary(valid.ttc_s)),
        traffic=dict(target_speed_mps=finite_summary(local.speed_mps), target_closing_speed_mps=finite_summary(local.closing_speed_mps),
                     target_net_gap_m=finite_summary(local.net_gap_m), low_speed_share=float(local.speed_mps.lt(5).mean()) if len(local) else None,
                     risk_state_count=int(valid.ttc_s.gt(0).mul(valid.ttc_s.lt(2)).sum()),
                     block_support=cells),
        physical_path=dict(status="uncertain_or_unobservable" if not source_events else "requires_qualified_witness_audit",
                           source_event_count=len(source_events), event_specific_physical_arrival_times=None,
                           rule="time-expanded identity/clock/native-connection/leader-follower witness; missing support is uncertain"),
        scientific_boundary=dict(scientific_effect_claim_eligible=False, source_support_status="CANDIDATE_SOURCE_EVENT_SUPPORT" if source_events else "NO_QUALIFIED_SOURCE_EVENT",
                                stage_0_5_gate="blocked"))
    (out / "measurement_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main(repo: Path):
    base = repo / "evidence/results" / RESULT
    net = base / "inputs/network.net.xml"
    arms = {"B10": (base / "B10/fcd.xml", base / "inputs/B00_routes.rou.xml", "AAD-S0.5-R1-B10-20261028"),
            "B01": (base / "B01/fcd.xml", base / "inputs/ramp_routes.rou.xml", "AAD-S0.5-R1-B01-20261028"),
            "B11": (base / "B11/fcd.xml", base / "inputs/ramp_routes.rou.xml", "AAD-S0.5-R1-B11-20261028")}
    # Accepted B00 is read from its sealed existing output; it is never run.
    b00 = repo / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03"
    results = {}
    for arm, (fcd, route, run_id) in arms.items():
        results[arm] = analyze_arm(arm, fcd, route, base / arm, run_id=run_id, net_path=net)
    # B00 has an accepted measured_state parquet and is analyzed with the same
    # state/D1 contract; the existing route is copied into the R1 evidence tree
    # only as a reference binding.
    b00_out = base / "B00_unified_analysis"
    b00_out.mkdir()
    d = pd.read_parquet(b00 / "measured_state.parquet")
    cohort = route_inventory(BASELINE_ROUTE)[3]
    cf = d[d.vehicle_id.isin(cohort)]
    target = local_d1_measurement(cf, WIN, region=TARGET, strict=True)
    source = local_d1_measurement(d, WIN, region=SOURCE, strict=True)
    results["B00"] = dict(schema="aad.r1.arm-measurement.v1", arm="B00", run_id="WEEK_0750_B00_IC1_s20261201_A03",
        execution=dict(duration_s=420, internal_step_s=.05, recording_step_s=.1, measured_state_rows=int(len(d)), source="accepted sealed A03"),
        lifecycle=dict(source="evidence/results/RES-AAD-WEEK-20261027-V1/population_accounting.json", status="accepted baseline; see bound evidence"),
        source_event_measurement=dict(region="S_UPSTREAM_MAIN", onset_events=source.get("onset_events"), D1_E_veh_s=source.get("local_evaluable_s"), reliable_D1_E_veh_s=source.get("reliable_local_s"), incomplete_candidates=source.get("incomplete_candidates", [])),
        target_measurement=dict(cohort="C_INPUT_ROUTE", D1_E_veh_s=target.get("local_evaluable_s"), reliable_D1_E_veh_s=target.get("reliable_local_s"), P2_events=target.get("onset_events"), incomplete_candidates=target.get("incomplete_candidates", [])),
        physical_path=dict(status="uncertain_or_unobservable", event_specific_physical_arrival_times=None),
        scientific_boundary=dict(scientific_effect_claim_eligible=False, source_support_status="NO_QUALIFIED_SOURCE_EVENT", stage_0_5_gate="blocked"))
    (b00_out / "measurement_result.json").write_text(json.dumps(results["B00"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (base / "arm_comparison.json").write_text(json.dumps({"schema": "aad.r1.arm-comparison.v1", "arms": results}, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: {"P2": v.get("target_measurement", {}).get("P2_events", v.get("source_event_measurement", {}).get("onset_events")),
                          "D1": v.get("target_measurement", {}).get("D1_E_veh_s"), "source_P2": v.get("source_event_measurement", {}).get("onset_events")} for k, v in results.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main(Path("/mnt/d/shen/TJU/AAD"))
