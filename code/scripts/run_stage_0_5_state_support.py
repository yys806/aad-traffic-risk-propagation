"""AAD-0.5-STATE-SUPPORT runner: conditional traffic-state support for Stage 0.5.

Steps (each is a separate sub-command so that the freeze order is auditable):

  real-domain  read-only characterisation of the real state-support domain
  plan         write and hash the pre-declared experiment plan (no SUMO)
  grid         execute the declared (supply x behaviour) grid
  seeds        independent-seed repetition of the accepted cells
  temporal     read the pre-designated validation window (only after freeze)
  verdict      assemble the state-support verdict
  all          real-domain -> plan -> grid -> seeds -> verdict -> temporal

The real windows are read through the sealed Stage 0.2 canonical states.  The
locked holdout is refused by construction.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from riskprop import stage_0_5_state_support as ss  # noqa: E402
from riskprop.stage_0_5_scene_reconstruction import network_edge_lengths, parse_fcd  # noqa: E402
from riskprop.stage_0_5_sumo import build_candidate_network, sumo_environment  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CANONICAL = REPO / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
OUTPUT = REPO / "code/outputs/formal/calibration/stage_0_5_state_support_v1"
RESULT_ID = "RES-STAGE-0.5-STATE-SUPPORT-V1"

GRID_SEED = 20261201
SEED_SET = (20261201, 20261202, 20261203, 20261204, 20261205)
TEMPORAL_SEED_SET = (20261211, 20261212)
CELL_CONTROL_SEED = 20261210


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False, default=str) + "\n",
                    encoding="utf-8")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def calibration_states() -> dict[str, pd.DataFrame]:
    return {
        window: ss.load_real_states(CANONICAL / f"ngsim_{window}.parquet", window)
        for window in ss.CALIBRATION_WINDOWS
    }


# --------------------------------------------------------------------------
# step 1: real domain
# --------------------------------------------------------------------------
def step_real_domain() -> dict[str, object]:
    states = calibration_states()
    summary: dict[str, object] = {"result_id": RESULT_ID, "version": ss.VERSION,
                                 "step": "real_domain", "windows": {}, "status": "Observation"}
    clouds: dict[str, pd.DataFrame] = {}
    relations: dict[str, dict[str, object]] = {}
    for window, frame in states.items():
        summary["windows"][window] = ss.local_summary(frame)
        clouds[window] = ss.block_cloud(frame)
        relations[window] = ss.following_relation(frame)
    pooled_states = pd.concat(states.values(), ignore_index=True)
    pooled_relation = ss.following_relation(pooled_states)
    pooled_cloud = pd.concat(clouds.values(), ignore_index=True)
    pooled_envelope = ss.support_envelope(pooled_cloud)
    pooled_closing_envelope = ss.closing_envelope(pooled_cloud)
    cross: dict[str, object] = {}
    for window, cloud in clouds.items():
        cross[window] = {
            "coverage_inside_pooled_envelope": ss.envelope_coverage(cloud, pooled_envelope),
            "own_envelope": ss.support_envelope(cloud),
        }
    # data-derived cross-window baseline: how much of one real window stays inside
    # the envelope built from the other real window
    baselines: dict[str, float] = {}
    keys = list(clouds)
    for other, own in [(keys[0], keys[1]), (keys[1], keys[0])]:
        baselines[f"{own}_inside_envelope_of_{other}"] = ss.envelope_coverage(
            clouds[own], cross[other]["own_envelope"])
    summary["following_relation"] = relations
    summary["pooled_following_relation"] = pooled_relation
    summary["pooled_envelope"] = pooled_envelope
    summary["pooled_closing_envelope"] = pooled_closing_envelope
    summary["cross_window_coverage"] = cross
    summary["cross_window_baseline_coverage_min"] = float(min(baselines.values()))
    summary["cross_window_baseline_detail"] = baselines
    summary["per_window_envelopes"] = {w: cross[w]["own_envelope"] for w in clouds}
    summary["observed_block_flow_max_veh_h_lane"] = float(pooled_cloud.flow_veh_h_lane.max())
    summary["observed_block_density_range"] = [float(pooled_cloud.density_veh_km_lane.min()),
                                               float(pooled_cloud.density_veh_km_lane.max())]
    summary["observed_block_speed_range"] = [float(pooled_cloud.speed_mean_mps.min()),
                                             float(pooled_cloud.speed_mean_mps.max())]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_json(OUTPUT / "real_domain.json", summary)
    pooled_cloud.to_csv(OUTPUT / "real_block_cloud.csv", index=False)
    for window, cloud in clouds.items():
        cloud.to_csv(OUTPUT / f"real_block_cloud_{window}.csv", index=False)
    return summary


# --------------------------------------------------------------------------
# step 2: pre-declared plan (written and hashed before any SUMO step)
# --------------------------------------------------------------------------
def build_plan(real: dict[str, object]) -> dict[str, object]:
    relation = real["pooled_following_relation"]
    cells = []
    for behaviour in ss.DECLARED_BEHAVIOURS:
        for free_speed in ss.DECLARED_SUPPLY_FREE_SPEED_MPS:
            for condition in ss.CONDITIONS:
                cells.append({
                    "cell_id": f"{behaviour}|{condition}|vlim{free_speed:.2f}",
                    "behaviour": behaviour,
                    "condition": condition,
                    "downstream_free_speed_mps": float(free_speed),
                })
    return {
        "result_id": RESULT_ID,
        "version": ss.VERSION,
        "mode": "pre-declared conditional state-support mapping; diagnostic evidence, not Gate acceptance",
        "region_m": [ss.REGION_START_M, ss.REGION_END_M],
        "lanes": list(ss.MAINLINE_LANES),
        "duration_s": ss.DECLARED_DURATION_S,
        "internal_step_s": ss.DECLARED_INTERNAL_STEP_S,
        "recorded_step_s": ss.DECLARED_FCD_PERIOD_S,
        "evaluation_window_s": list(ss.DECLARED_EVALUATION_WINDOW_S),
        "evaluation_window_basis": (
            "300-420 s is the last third of the declared 420 s run: it is far enough from "
            "the injected real initial state for the boundary conditions to act, identical "
            "for every cell, and written here before any trajectory of this batch existed"
        ),
        "block_s": ss.BLOCK_S,
        "supply_axis": {
            "quantity": "downstream edge (main_2, 399.22-669.18 m) free speed",
            "values_mps": list(ss.DECLARED_SUPPLY_FREE_SPEED_MPS),
            "rationale": (
                "the real corridor is congested with low-speed waves that originate downstream "
                "of the observed segment, so the downstream boundary must be a capacity "
                "restriction; 27.78 m/s reproduces the observed geometry without restriction; "
                "the same declared values are used in every behaviour arm so that the supply "
                "axis is not confounded with the behaviour axis"
            ),
            "analytic_capacity_formula": "3600 * v_lim / (v_lim * tau + length + minGap) per lane, 5 lanes",
        },
        "behaviour_axis": {
            "arms": ss.DECLARED_BEHAVIOURS,
            "tau_source": (
                "ratio estimator of net_gap = minGap + tau * v over the full local following "
                "population of the two calibration windows, computed in step 1 before any SUMO run"
            ),
            "tau_values_s": {
                "B_frozen": [1.0],
                "B_mean": [relation["tau_eff_ratio_s"]],
                "B_het": [float(x) for x in np.interp(
                    ss.HETEROGENEITY_QUANTILES,
                    relation["vehicle_tau_eff_quantile_levels"],
                    relation["vehicle_tau_eff_quantiles_s"])],
            },
            "single_factor_rule": "an arm may differ from the sealed baseline in tau only",
        },
        "initial_state": (
            "each arm is initialised at t=0 with the observed real local state of its window "
            "(lanes, positions and speeds taken from the sealed canonical states); the "
            "experiment therefore measures whether the observed state is preserved by the "
            "simulated dynamics under the declared boundary supply"
        ),
        "membership_rules": {
            "primary_state_support": (
                "the simulated evaluation-window mean (density, speed) lies inside the real pooled "
                "k-band envelope, and the fraction of simulated 30 s blocks inside that envelope is "
                "at least the data-derived cross-window baseline coverage"
            ),
            "mechanism_compatibility": (
                "the fraction of simulated 30 s blocks whose density and mean closing speed lie "
                "inside the real closing-speed k-band envelope is at least the data-derived "
                "cross-window baseline, and the simulated low-speed share does not exceed the "
                "maximum observed real 30 s block low-speed share"
            ),
            "not_a_science_tolerance": True,
            "baseline_definition": (
                "minimum over the two directions of 'fraction of one real window's blocks inside the "
                "other real window's envelope' -- a property of the real data, not a chosen threshold"
            ),
        },
        "stop_rules": [
            "any engineering failure (non-zero SUMO exit, teleport, collision) stops the batch",
            "no cell is added to the grid after the grid has been executed",
            "independent-seed repetition is executed only for cells that pass the primary rule",
            "the validation window is read only after the freeze manifest exists",
        ],
        "seeds": {"grid": GRID_SEED, "independent": list(SEED_SET), "temporal": list(TEMPORAL_SEED_SET)},
        "sumo_environment": sumo_environment(),
        "sealed_windows_not_read": [ss.VALIDATION_WINDOW, "lankershim", "locked holdout"],
    }


def step_plan() -> dict[str, object]:
    real = _read_json(OUTPUT / "real_domain.json")
    plan = build_plan(real)
    _write_json(OUTPUT / "experiment_plan.json", plan)
    digest = ss.sha256_file(OUTPUT / "experiment_plan.json")
    (OUTPUT / "PLAN_SHA256").write_text(f"{digest}  experiment_plan.json\n", encoding="utf-8")
    return plan


# --------------------------------------------------------------------------
# execution
# --------------------------------------------------------------------------
def derive_demand(states: pd.DataFrame, condition: str) -> dict[str, object]:
    """Trajectory-derived conditional demand of one real window (uniform basis)."""
    from riskprop.stage_0_5_trajectory_reconstruction import boundary_crossings
    window = ss.APPROVED_SPANS[condition]
    span_s = float(window[1] - window[0])
    frame = states.copy()
    if "vehicle_id" not in frame.columns:
        frame["vehicle_id"] = frame.trajectory_id.astype(str)
    crossings = boundary_crossings(frame, at_m=ss.REGION_START_M,
                                   lanes=ss.MAINLINE_LANES, window=window)
    first = states.sort_values(["trajectory_id", "time_s"], kind="stable").groupby(
        "trajectory_id", sort=False).first()
    onramp = int(((first.lane_id.astype(str) == "7")
                  & first.time_s.ge(window[0]) & first.time_s.lt(window[1])).sum())
    offramp = int(((first.lane_id.astype(str) == "8")
                   & first.time_s.ge(window[0]) & first.time_s.lt(window[1])).sum())
    return {
        "window_s": [float(window[0]), float(window[1])],
        "mainline_flow_veh_h": float(len(crossings) / span_s * 3600.0),
        "mainline_crossings": int(len(crossings)),
        "onramp_flow_veh_h": float(onramp / span_s * 3600.0),
        "offramp_flow_veh_h": float(offramp / span_s * 3600.0),
        "basis": "trajectory crossings of y=150 m on lanes 1-5 plus first lane-7/lane-8 observations",
    }


def run_cell(work: Path, cell: dict[str, object], relation: dict[str, object],
             seed: int, *, demand: dict[str, object] | None = None,
             with_p2: bool = False,
             real_states: pd.DataFrame | None = None) -> dict[str, object]:
    work.mkdir(parents=True, exist_ok=True)
    spec = ss.observed_geometry_spec(float(cell["downstream_free_speed_mps"]),
                                     int(cell.get("downstream_lanes", 5)))
    network = build_candidate_network(work / "network", spec)
    edge_lengths = network_edge_lengths(network["network"])
    types = ss.declared_behaviour_vtypes(str(cell["behaviour"]), relation)
    mean_tau = sum(entry["tau"] * entry["share"] for entry in types) / sum(
        entry["share"] for entry in types)
    initial = None
    if real_states is not None:
        initial = ss.initial_state_records(real_states, str(cell["condition"]),
                                           edge_lengths=edge_lengths)
    limits = {"main_0": ss.FREE_SPEED_MPS, "main_1": ss.FREE_SPEED_MPS,
              "main_2": float(spec["edges"][2]["speed_mps"]),
              "onramp": 13.89, "offramp": 13.89}
    lane_counts = {edge["id"]: int(edge["lanes"]) for edge in spec["edges"]}
    routes = ss.build_conditional_route_file(work / "routes.rou.xml", str(cell["condition"]),
                                             str(cell["behaviour"]), types, demand=demand,
                                             duration_s=ss.DECLARED_DURATION_S,
                                             initial_records=(initial or {}).get("accepted"),
                                             edge_speed_limits=limits,
                                             edge_lane_counts=lane_counts)
    config = ss.write_conditional_config(work / "run.sumocfg", network=network["network"],
                                         routes=work / "routes.rou.xml",
                                         duration_s=ss.DECLARED_DURATION_S, seed=seed)
    started = time.perf_counter()
    run = ss.run_sumo(config, wall_limit_s=1800.0)
    fcd = parse_fcd(work / "fcd.xml", edge_lengths)
    states = ss.fcd_to_state_frame(fcd, ss.route_length_map(work / "routes.rou.xml"),
                                   run_id=str(cell["cell_id"]), scenario_id=str(cell["cell_id"]),
                                   seed=seed)
    measured = ss.measure_state_frame(states)
    descriptors = ss.block_descriptors(measured, window=ss.DECLARED_EVALUATION_WINDOW_S)
    initial_descriptors = ss.block_descriptors(
        measured, window=(0.0, ss.BLOCK_S))
    p2_count = None
    p2_local = None
    if with_p2:
        from riskprop.stage_0_5_sumo import build_sumo_p2_events
        events, _ = build_sumo_p2_events(measured)
        eval_low, eval_high = ss.DECLARED_EVALUATION_WINDOW_S
        in_window = events[events.event_start_s.ge(eval_low) & events.event_start_s.lt(eval_high)]
        p2_count = int(len(in_window))
        lookup = measured.set_index(["vehicle_id", "time_s"])[["y_m", "lane_id"]]
        local = 0
        for ev in in_window.itertuples():
            key = (str(ev.vehicle_id), round(float(ev.event_start_s), 1))
            try:
                position, lane = lookup.loc[key]
            except KeyError:
                continue
            if (str(lane) in ss.MAINLINE_LANES
                    and ss.REGION_START_M <= float(position) < ss.REGION_END_M):
                local += 1
        p2_local = local
    measured.to_parquet(work / "measured_state.parquet", index=False)
    return {
        "cell": cell,
        "seed": int(seed),
        "wall_s": float(time.perf_counter() - started),
        "sumo": {k: v for k, v in run.items() if k != "log_tail"},
        "log_tail": run["log_tail"][-2000:],
        "edge_lengths": edge_lengths,
        "vtypes": types,
        "initial_state": {"accepted": (initial or {}).get("accepted_count"),
                          "dropped": (initial or {}).get("dropped_count"),
                          "clock_s": (initial or {}).get("clock_s"),
                          "speed_clamped": routes.get("initial_speed_clamped"),
                          "lane_clamped": routes.get("initial_lane_clamped")},
        "analytic_capacity_veh_h": ss.supply_capacity_veh_h(
            float(cell["downstream_free_speed_mps"]), mean_tau,
            lanes=int(cell.get("downstream_lanes", 5))),
        "mean_tau_s": mean_tau,
        "descriptors": descriptors,
        "initial_window_descriptors": initial_descriptors,
        "p2_events_eval_window": p2_count,
        "p2_events_eval_window_local": p2_local,
        "p2_local_rate_per_vehicle_hour": (
            (p2_local / (descriptors["p2_evaluable_exposure_veh_s"] / 3600.0))
            if p2_local is not None and descriptors["p2_evaluable_exposure_veh_s"] > 0 else None),
        "p2_network_rate_per_vehicle_hour": (
            (p2_count / (descriptors["local_vehicle_s"] / 3600.0))
            if p2_count is not None and descriptors["local_vehicle_s"] > 0 else None),
        "states": int(len(measured)),
    }


def step_grid() -> dict[str, object]:
    plan = _read_json(OUTPUT / "experiment_plan.json")
    relation = _read_json(OUTPUT / "real_domain.json")["pooled_following_relation"]
    root = OUTPUT / "grid"
    if root.exists():
        shutil.rmtree(root)
    calibration = calibration_states()
    results: list[dict[str, object]] = []
    for behaviour in ss.DECLARED_BEHAVIOURS:
        for free_speed in ss.DECLARED_SUPPLY_FREE_SPEED_MPS:
            for condition in ss.CONDITIONS:
                cell = {"cell_id": f"{behaviour}|{condition}|vlim{free_speed:.2f}",
                        "behaviour": behaviour, "condition": condition,
                        "downstream_free_speed_mps": float(free_speed)}
                record = run_cell(root / cell["cell_id"].replace("|", "_"), cell, relation,
                                  GRID_SEED, real_states=calibration[condition])
                results.append(record)
                print(f"  {cell['cell_id']}: k={record['descriptors']['density_veh_km_lane']:.2f} "
                      f"v={record['descriptors']['speed_mean_mps']:.2f} "
                      f"closing={record['descriptors']['closing_speed_mean_mps']:.3f} "
                      f"low={record['descriptors']['low_speed_share']:.3f}", flush=True)
    _write_json(OUTPUT / "grid_results.json", {"plan_sha256": ss.sha256_file(OUTPUT / "experiment_plan.json"),
                                               "results": results})
    return {"cells": len(results)}


def _membership(record: dict[str, object], real: dict[str, object]) -> dict[str, object]:
    envelope = real["pooled_envelope"]
    closing_envelope = real["pooled_closing_envelope"]
    condition = str(record["cell"]["condition"])
    windows = list(ss.CALIBRATION_WINDOWS)
    # The comparison envelope for a cell of window W is the envelope built from the
    # *other* calibration window, and the baseline is how much of W the real data
    # itself keeps inside that envelope.  Both sides therefore use an envelope that
    # was not fitted to them.
    if condition in windows:
        other = windows[1] if condition == windows[0] else windows[0]
        reference_envelope = real["per_window_envelopes"][other]
        baseline = float(real["cross_window_baseline_detail"][f"{condition}_inside_envelope_of_{other}"])
    else:
        reference_envelope = envelope
        baseline = float(real["cross_window_baseline_coverage_min"])
    descriptors = record["descriptors"]
    mean_member = ss.envelope_membership(float(descriptors["density_veh_km_lane"]),
                                         float(descriptors["speed_mean_mps"]), envelope)
    block_cloud = pd.DataFrame(descriptors["blocks"])
    coverage_pooled = ss.envelope_coverage(block_cloud, envelope)
    coverage_reference = ss.envelope_coverage(block_cloud, reference_envelope)
    closing_inside = [ss.closing_membership(float(block["density_veh_km_lane"]),
                                            float(block["closing_speed_mean_mps"]),
                                            closing_envelope)["inside"]
                      for block in descriptors["blocks"]]
    closing_coverage = float(np.mean(closing_inside)) if closing_inside else float("nan")
    real_low_max = max(float(block["low_speed_share"])
                       for cloud in [pd.read_csv(OUTPUT / f"real_block_cloud_{w}.csv")
                                     for w in ss.CALIBRATION_WINDOWS]
                       for _, block in cloud.iterrows())
    mechanism = bool(closing_coverage >= baseline
                     and float(descriptors["low_speed_share"]) <= real_low_max)
    return {
        "cell_id": record["cell"]["cell_id"],
        "reference_window": other if condition in windows else None,
        "reference_baseline_coverage": baseline,
        "mean_state_inside_pooled_envelope": mean_member,
        "block_coverage_pooled_envelope": coverage_pooled,
        "block_coverage_reference_envelope": coverage_reference,
        "block_coverage_meets_baseline": bool(coverage_reference >= baseline),
        "closing_block_coverage": closing_coverage,
        "closing_coverage_meets_baseline": bool(closing_coverage >= baseline),
        "mechanism_compatible": mechanism,
        "primary_state_support": bool(mean_member["inside"] and coverage_reference >= baseline),
        "observed_real_low_speed_share_max": real_low_max,
    }


def step_verdict() -> dict[str, object]:
    real = _read_json(OUTPUT / "real_domain.json")
    grid = _read_json(OUTPUT / "grid_results.json")
    cells = []
    for record in grid["results"]:
        entry = _membership(record, real)
        entry["density_veh_km_lane"] = record["descriptors"]["density_veh_km_lane"]
        entry["speed_mean_mps"] = record["descriptors"]["speed_mean_mps"]
        entry["flow_veh_h_lane"] = record["descriptors"]["flow_veh_h_lane_consistency"]
        entry["low_speed_share"] = record["descriptors"]["low_speed_share"]
        entry["closing_speed_mean_mps"] = record["descriptors"]["closing_speed_mean_mps"]
        entry["closing_speed_negative_share"] = record["descriptors"]["closing_speed_negative_share"]
        entry["tau_eff_ratio_s"] = record["descriptors"]["tau_eff_ratio_s"]
        entry["analytic_capacity_veh_h"] = record["analytic_capacity_veh_h"]
        entry["p2_events_eval_window"] = record["p2_events_eval_window"]
        entry["engineering_ok"] = bool(record["sumo"]["teleports"] == 0 and record["sumo"]["collisions"] == 0)
        cells.append(entry)
    passing = [cell for cell in cells
               if cell["primary_state_support"] and cell["mechanism_compatible"]
               and cell["engineering_ok"]]
    by_condition: dict[str, set[str]] = {}
    for cell in passing:
        behaviour, condition, supply = cell["cell_id"].split("|")
        by_condition.setdefault(condition, set()).add(f"{behaviour}|{supply}")
    conditions = list(ss.CALIBRATION_WINDOWS)
    dual = (set.intersection(*[by_condition.get(name, set()) for name in conditions])
            if all(name in by_condition for name in conditions) else set())
    verdict = {
        "result_id": RESULT_ID,
        "plan_sha256": grid["plan_sha256"],
        "cells": cells,
        "passing_combinations_per_condition": {k: sorted(v) for k, v in by_condition.items()},
        "cells_passing_both_rules": [cell["cell_id"] for cell in passing],
        "combinations_passing_both_calibration_windows": sorted(dual),
        "cell_count": len(cells),
        "state_support_established": bool(passing),
        "rule": ("primary state support AND mechanism compatibility AND engineering soundness; "
                 "the three are necessary, none compensates another"),
    }
    _write_json(OUTPUT / "state_support_verdict.json", verdict)
    return verdict


def step_seeds() -> dict[str, object]:
    verdict = _read_json(OUTPUT / "state_support_verdict.json")
    relation = _read_json(OUTPUT / "real_domain.json")["pooled_following_relation"]
    accepted_combinations = set(verdict["combinations_passing_both_calibration_windows"])
    if not accepted_combinations:
        _write_json(OUTPUT / "seed_repeats.json",
                    {"executed": False,
                     "reason": "no combination passed on both calibration windows"})
        return {"executed": False}
    calibration = calibration_states()
    cells = _read_json(OUTPUT / "grid_results.json")["results"]
    results: list[dict[str, object]] = []
    for record in cells:
        cell = record["cell"]
        behaviour, condition, supply = cell["cell_id"].split("|")
        if f"{behaviour}|{supply}" not in accepted_combinations:
            continue
        for seed in SEED_SET:
            root = OUTPUT / "seeds" / f"{cell['cell_id'].replace('|', '_')}_s{seed}"
            results.append(run_cell(root, cell, relation, seed, with_p2=True,
                                    real_states=calibration[str(cell["condition"])]))
        print(f"  seeds {cell['cell_id']}", flush=True)
    _write_json(OUTPUT / "seed_repeats.json", {"executed": True, "seeds": list(SEED_SET),
                                               "cells": sorted(accepted_combinations),
                                               "results": results})
    return {"executed": True, "runs": len(results)}


def step_structural() -> dict[str, object]:
    """Declared structural supply variant: a discrete lane drop at the diverge.

    Executed only for the behaviour combinations that already passed both
    calibration windows under the speed-limit encoding, at a declared lane count
    whose analytic capacity matches that restriction.  The purpose is to separate
    "how much downstream capacity" from "how the capacity is realised", because
    only a discrete bottleneck is expected to generate the back-propagating
    low-speed waves that the real local state contains.
    """
    verdict = _read_json(OUTPUT / "state_support_verdict.json")
    real = _read_json(OUTPUT / "real_domain.json")
    relation = real["pooled_following_relation"]
    accepted = verdict.get("combinations_passing_both_calibration_windows", [])
    if not accepted:
        _write_json(OUTPUT / "structural_results.json",
                    {"executed": False, "reason": "no combination passed on both calibration windows"})
        return {"executed": False}
    declared_cells: list[dict[str, object]] = []
    for combination in accepted:
        behaviour, supply = combination.split("|")
        free_speed = float(supply.replace("vlim", ""))
        for variant in ss.DECLARED_SUPPLY_VARIANTS:
            if variant["kind"] != "lane_drop":
                continue
            for condition in ss.CONDITIONS:
                declared_cells.append({
                    "cell_id": f"{behaviour}|{condition}|{variant['variant_id']}",
                    "behaviour": behaviour,
                    "condition": condition,
                    "downstream_free_speed_mps": ss.FREE_SPEED_MPS,
                    "downstream_lanes": int(variant["downstream_lanes"]),
                    "matched_speed_limit_combination": combination,
                    "matched_speed_limit_free_speed_mps": free_speed,
                })
    structural_plan = {
        "result_id": RESULT_ID,
        "step": "structural_supply_variant",
        "hypothesis": (
            "the real local state carries back-propagating low-speed waves and a wide "
            "relative-motion dispersion; a smooth speed limit produces a homogeneous "
            "synchronized flow, whereas a discrete lane drop at the observed diverge "
            "produces the waves. If so, the lane-drop encoding reproduces the observed "
            "relative-motion dispersion and a positive P2 event rate at matched capacity."
        ),
        "falsification_rule": (
            "if, at matched analytic capacity, the lane-drop encoding still yields a closing-speed "
            "distribution and a P2 event rate outside the real block envelopes, the wave-generation "
            "hypothesis is rejected and no further supply encoding is tried in this task"
        ),
        "declared_cells": declared_cells,
        "capacity_matching": (
            "the lane drop removes one of five downstream lanes at 27.78 m/s; the analytic "
            "capacity of that variant is reported next to the speed-limit variant it replaces"
        ),
        "evaluation_window_s": list(ss.DECLARED_EVALUATION_WINDOW_S),
        "seed": GRID_SEED,
        "written_before_execution_of_this_batch": True,
    }
    _write_json(OUTPUT / "structural_plan.json", structural_plan)
    (OUTPUT / "STRUCTURAL_PLAN_SHA256").write_text(
        ss.sha256_file(OUTPUT / "structural_plan.json") + "  structural_plan.json\n",
        encoding="utf-8")
    shutil.rmtree(OUTPUT / "structural", ignore_errors=True)
    calibration = calibration_states()
    results: list[dict[str, object]] = []
    for cell in declared_cells:
        record = run_cell(OUTPUT / "structural" / str(cell["cell_id"]).replace("|", "_"),
                          cell, relation, GRID_SEED, with_p2=True,
                          real_states=calibration[str(cell["condition"])])
        record["membership"] = _membership(record, real)
        results.append(record)
        print(f"  {cell['cell_id']}: k={record['descriptors']['density_veh_km_lane']:.2f} "
              f"v={record['descriptors']['speed_mean_mps']:.2f} "
              f"sd={record['descriptors']['speed_sd_mps']:.2f} "
              f"p2={record['p2_events_eval_window']}", flush=True)
    _write_json(OUTPUT / "structural_results.json",
                {"executed": True, "plan_sha256": ss.sha256_file(OUTPUT / "structural_plan.json"),
                 "results": results})
    return {"executed": True, "runs": len(results)}


# --------------------------------------------------------------------------
# step: temporal validation (only after freezing)
# --------------------------------------------------------------------------
def step_temporal() -> dict[str, object]:
    freeze = OUTPUT / "freeze_manifest.json"
    if not freeze.exists():
        raise SystemExit("refusing to read the validation window before the freeze manifest exists")
    manifest = _read_json(freeze)
    for relative, digest in manifest["frozen_files"].items():
        if ss.sha256_file(OUTPUT / relative) != digest:
            raise SystemExit(f"frozen file changed after freeze: {relative}")
    verdict = _read_json(OUTPUT / "state_support_verdict.json")
    real = _read_json(OUTPUT / "real_domain.json")
    states = ss.load_real_states(CANONICAL / f"ngsim_{ss.VALIDATION_WINDOW}.parquet",
                                 ss.VALIDATION_WINDOW)
    demand = derive_demand(states, ss.VALIDATION_WINDOW)
    summary = ss.local_summary(states)
    relation = ss.following_relation(states)
    cloud = ss.block_cloud(states)
    envelope_pooled = real["pooled_envelope"]
    membership = {
        "mean_state_inside_calibration_envelope": ss.envelope_membership(
            float(summary["density_veh_km_lane"]), float(summary["speed_mean_mps"]), envelope_pooled),
        "block_coverage_inside_calibration_envelope": ss.envelope_coverage(cloud, envelope_pooled),
        "following_relation_inside_calibration_range": bool(
            min(real["following_relation"]["us101__0750_0805"]["tau_eff_ratio_s"],
                real["following_relation"]["us101__0805_0820"]["tau_eff_ratio_s"])
            <= relation["tau_eff_ratio_s"]
            <= max(real["following_relation"]["us101__0750_0805"]["tau_eff_ratio_s"],
                   real["following_relation"]["us101__0805_0820"]["tau_eff_ratio_s"])),
    }
    # the frozen accepted configurations, re-run with the validation window demand
    relation_pooled = real["pooled_following_relation"]
    accepted = verdict.get("combinations_passing_both_calibration_windows", [])
    runs: list[dict[str, object]] = []
    for combination in accepted:
        behaviour, supply = combination.split("|")
        free_speed = float(supply.replace("vlim", ""))
        cell = {"cell_id": f"{behaviour}|{ss.VALIDATION_WINDOW}|vlim{free_speed:.2f}",
                "behaviour": behaviour, "condition": ss.VALIDATION_WINDOW,
                "downstream_free_speed_mps": free_speed}
        for seed in TEMPORAL_SEED_SET:
            root = OUTPUT / "temporal" / f"{cell['cell_id'].replace('|', '_')}_s{seed}"
            runs.append(run_cell(root, cell, relation_pooled, seed, demand=demand,
                                 with_p2=True, real_states=states))
            print(f"  temporal {cell['cell_id']} seed {seed}", flush=True)
    result = {
        "validation_window": ss.VALIDATION_WINDOW,
        "derived_demand": demand,
        "real_local_summary": summary,
        "real_following_relation": relation,
        "membership_of_validation_window_in_calibration_domain": membership,
        "frozen_configuration_runs": runs,
        "read_after_freeze_sha256": ss.sha256_file(freeze),
    }
    _write_json(OUTPUT / "temporal_validation.json", result)
    return result


def _wave_descriptor(measured: pd.DataFrame, window: tuple[float, float]) -> dict[str, object]:
    from riskprop.stage_0_5_trajectory_reconstruction import JAM_SPEED_MPS, jam_waves
    frame = measured[measured.lane_id.isin(list(ss.MAINLINE_LANES))]
    descriptor = jam_waves(frame, lanes=ss.MAINLINE_LANES, window=window,
                           threshold_mps=JAM_SPEED_MPS)
    biggest = descriptor["components"][0] if descriptor["components"] else None
    return {
        "status": "Observation",
        "threshold_mps": descriptor["threshold_mps"],
        "slow_cell_fraction": descriptor["slow_cell_fraction"],
        "components": descriptor["components"][:5],
        "largest_component_growth": biggest["growth"] if biggest else None,
        "largest_component_cells": biggest["cells"] if biggest else 0,
        "upstream_component_count": int(sum(1 for item in descriptor["components"]
                                            if item["growth"] == "upstream")),
    }


def _real_wave_descriptor(window: str, states: pd.DataFrame) -> dict[str, object]:
    from riskprop.stage_0_5_trajectory_reconstruction import JAM_SPEED_MPS, jam_waves
    mask = ss.local_region_mask(states)
    frame = states[mask]
    descriptor = jam_waves(frame, lanes=ss.MAINLINE_LANES,
                           window=ss.APPROVED_SPANS[window], threshold_mps=JAM_SPEED_MPS)
    biggest = descriptor["components"][0] if descriptor["components"] else None
    return {
        "status": "Observation",
        "threshold_mps": descriptor["threshold_mps"],
        "slow_cell_fraction": descriptor["slow_cell_fraction"],
        "components": descriptor["components"][:5],
        "largest_component_growth": biggest["growth"] if biggest else None,
        "largest_component_cells": biggest["cells"] if biggest else 0,
        "upstream_component_count": int(sum(1 for item in descriptor["components"]
                                            if item["growth"] == "upstream")),
    }


def step_analysis() -> dict[str, object]:
    """Mechanism comparison from the stored runs; no simulator is started here."""
    real = _read_json(OUTPUT / "real_domain.json")
    calibration = calibration_states()
    real_waves = {window: _real_wave_descriptor(window, frame)
                  for window, frame in calibration.items()}
    runs: list[dict[str, object]] = []
    for folder in ("grid", "structural", "seeds", "temporal"):
        base = OUTPUT / folder
        if not base.exists():
            continue
        for path in sorted(base.glob("*/measured_state.parquet")):
            measured = pd.read_parquet(path)
            local = measured[
                measured.lane_id.isin(list(ss.MAINLINE_LANES))
                & measured.y_m.ge(ss.REGION_START_M) & measured.y_m.lt(ss.REGION_END_M)
                & measured.time_s.ge(ss.DECLARED_EVALUATION_WINDOW_S[0])
                & measured.time_s.lt(ss.DECLARED_EVALUATION_WINDOW_S[1])]
            if local.empty:
                continue
            waves = _wave_descriptor(measured, ss.DECLARED_EVALUATION_WINDOW_S)
            record_files = {"grid": "grid_results.json", "structural": "structural_results.json",
                            "seeds": "seed_repeats.json", "temporal": "temporal_validation.json"}
            stored = None
            source = OUTPUT / record_files[folder]
            if source.exists():
                blob = _read_json(source)
                entries = blob.get("results", blob.get("frozen_configuration_runs", []))
                for entry in entries:
                    expected = "_".join(entry["cell"]["cell_id"].split("|"))
                    if path.parent.name == expected or path.parent.name.startswith(expected + "_s"):
                        stored = entry
                        break
            mean_tau = None
            declared_capacity = None
            if stored is not None:
                types = stored.get("vtypes") or []
                if types:
                    mean_tau = sum(t["tau"] * t["share"] for t in types) / sum(t["share"] for t in types)
                    declared_capacity = ss.supply_capacity_veh_h(
                        float(stored["cell"]["downstream_free_speed_mps"]), mean_tau,
                        lanes=int(stored["cell"].get("downstream_lanes", 5)))
            runs.append({
                "run": f"{folder}/{path.parent.name}",
                "folder": folder,
                "mean_tau_s": mean_tau,
                "declared_analytic_capacity_veh_h": declared_capacity,
                "density_veh_km_lane": len(local) * 0.1
                / (ss.DECLARED_EVALUATION_WINDOW_S[1] - ss.DECLARED_EVALUATION_WINDOW_S[0])
                / ((ss.REGION_END_M - ss.REGION_START_M) / 1000.0 * len(ss.MAINLINE_LANES)),
                "speed_sd_mps": float(local.speed_mps.std(ddof=1)),
                "closing_speed_mean_mps": float(local.closing_speed_mps.mean()),
                "closing_speed_negative_share": float((local.closing_speed_mps < 0).mean()),
                "low_speed_share": float((local.speed_mps < ss.LOW_SPEED_MPS).mean()),
                "waves": waves,
            })
    result = {"result_id": RESULT_ID, "real_waves": real_waves, "runs": runs,
              "note": ("wave descriptors use the inherited absolute 10 m/s descriptive threshold and are "
                       "compared only between runs measured in the same region")}
    _write_json(OUTPUT / "mechanism_analysis.json", result)
    return result


def step_freeze() -> dict[str, object]:
    manifest = {"result_id": RESULT_ID,
                "frozen_files": {"experiment_plan.json": ss.sha256_file(OUTPUT / "experiment_plan.json"),
                                 "real_domain.json": ss.sha256_file(OUTPUT / "real_domain.json"),
                                 "state_support_verdict.json": ss.sha256_file(OUTPUT / "state_support_verdict.json"),
                                 "grid_results.json": ss.sha256_file(OUTPUT / "grid_results.json")},
                "source_sha256": {
                    "code/src/riskprop/stage_0_5_state_support.py":
                        ss.sha256_file(REPO / "code/src/riskprop/stage_0_5_state_support.py"),
                    "code/scripts/run_stage_0_5_state_support.py":
                        ss.sha256_file(REPO / "code/scripts/run_stage_0_5_state_support.py"),
                }}
    _write_json(OUTPUT / "freeze_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["real-domain", "plan", "grid", "seeds", "verdict",
                                         "structural", "analysis", "freeze", "temporal", "all"])
    arguments = parser.parse_args()
    if arguments.step in {"real-domain", "all"}:
        real = step_real_domain()
        print("real-domain done; pooled tau_eff =",
              real["following_relation"] and real["pooled_following_relation"]["tau_eff_ratio_s"])
    if arguments.step in {"plan", "all"}:
        step_plan()
        print("plan frozen")
    if arguments.step in {"grid", "all"}:
        step_grid()
    if arguments.step in {"verdict", "all"}:
        verdict = step_verdict()
        print("passing cells:", verdict["cells_passing_both_rules"])
    if arguments.step in {"seeds", "all"}:
        step_seeds()
    if arguments.step in {"structural", "all"}:
        step_structural()
    if arguments.step in {"analysis", "all"}:
        step_analysis()
    if arguments.step in {"freeze", "all"}:
        step_freeze()
        print("freeze manifest written")
    if arguments.step in {"temporal", "all"}:
        step_temporal()
        print("temporal validation done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
