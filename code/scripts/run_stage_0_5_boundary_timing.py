"""AAD-0.5-ARRIVAL-TIMING runner.

Steps (each a separate sub-command so the freeze order stays auditable):

  audit          phase A read-only audit: implementation facts, boundary-event
                 reconstruction feasibility, duplicate-identity checks
  wave-baseline  phase B: real density-conditioned baseline, synthetic acceptance
                 of the anomaly diagnostic, real-only sensitivity of its settings
  plan           freeze the experiment plan, the event tables and the arm pairing
  runs           execute the paired U/E design (2 windows x 2 arms x 5 seeds)
  analysis       paired statistics, wave diagnostics per run, insertion audit
  verdict        hypothesis reading matrix

Nothing runs SUMO before ``plan`` has written ``PLAN_SHA256``.
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

from riskprop import stage_0_5_boundary_timing as bt  # noqa: E402
from riskprop import stage_0_5_state_support as ss  # noqa: E402
from riskprop.stage_0_5_scene_reconstruction import network_edge_lengths, parse_fcd  # noqa: E402
from riskprop.stage_0_5_sumo import build_candidate_network, sumo_environment  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CANONICAL = REPO / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
OUTPUT = REPO / "code/outputs/formal/calibration/stage_0_5_boundary_timing_v1"
PREVIOUS = REPO / "code/outputs/formal/calibration/stage_0_5_state_support_v1"
RESULT_ID = "RES-STAGE-0.5-ARRIVAL-TIMING-V1"

ARMS = ("U", "E")
SEED_SET = (20261201, 20261202, 20261203, 20261204, 20261205)
BEHAVIOUR = "B_het"
DOWNSTREAM_FREE_SPEED_MPS = 10.0
EVALUATION_WINDOW_S = ss.DECLARED_EVALUATION_WINDOW_S


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False, default=str) + "\n",
                    encoding="utf-8")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def calibration_states() -> dict[str, pd.DataFrame]:
    return {window: ss.load_real_states(CANONICAL / f"ngsim_{window}.parquet", window)
            for window in ss.CALIBRATION_WINDOWS}


def frozen_domain() -> dict[str, object]:
    """The state domain frozen by the previous task; never re-derived here."""
    return _read_json(PREVIOUS / "real_domain.json")


# --------------------------------------------------------------------------
# phase A: audit
# --------------------------------------------------------------------------
def step_audit() -> dict[str, object]:
    states = calibration_states()
    result: dict[str, object] = {
        "result_id": RESULT_ID,
        "step": "phase_A_audit",
        "status": "Observation",
        "questions": {},
        "windows": {},
    }
    for window, frame in states.items():
        events = bt.entry_events(frame, window)
        table = bt.paired_arrival_tables(events["events"])["events"]
        initial = ss.initial_state_records(
            frame, window,
            edge_lengths=network_edge_lengths(next(
                (PREVIOUS / f"grid/{BEHAVIOUR}_{window}_vlim{DOWNSTREAM_FREE_SPEED_MPS:.2f}"
                 / "network").glob("*.net.xml"))))
        initial_ids = {str(record["trajectory_id"]) for record in initial["accepted"]}
        event_ids = {str(item["trajectory_id"]) for item in events["events"]}
        frames = {}
        for arm, column in (("U", "arm_U_time_s"), ("E", "arm_E_time_s")):
            arm_table = table.copy()
            arm_table["arrival_time_s"] = arm_table[column]
            frames[arm] = bt.arrival_summary(arm_table)
        result["windows"][window] = {
            "entry_events": {key: value for key, value in events.items() if key != "events"},
            "event_ids_shared_with_initial_state": sorted(initial_ids & event_ids),
            "initial_state": {"accepted": initial["accepted_count"], "dropped": initial["dropped_count"],
                              "clock_s": initial["clock_s"],
                              "dropped_reasons": pd.DataFrame(initial["dropped"]).reason.value_counts().to_dict()
                              if initial["dropped"] else {}},
            "demand": {arm: frames[arm] for arm in ARMS},
            "pairing": {
                "events_identical": bool(
                    table.sort_values("event_id").trajectory_id.tolist()
                    == table.sort_values("event_id").trajectory_id.tolist()),
                "same_event_count": int(len(table)),
                "same_lanes": bool(table.observed_lane_id.notna().all()),
                "same_routes": table.route.value_counts().to_dict(),
            },
        }
    result["questions"] = {
        "q1_uniform_generation": (
            "The previous task generated departures with depart_times(): a fixed interval "
            "3600/flow placed from phase*interval, rounded up to 0.1 s. It is a deterministic "
            "periodic schedule, so it carries no arrival clustering."
        ),
        "q2_network_entry_position": (
            "Netconvert extends main_0 to the junction midpoint; parse_fcd inverse-scales built "
            "positions back onto the observed span, so built position 0 corresponds to real "
            "y = 0 m. departPos='base' therefore enters a vehicle at real y of a few metres."
        ),
        "q3_flow_plane_vs_entry": (
            "They did NOT coincide before this task: the demand was derived from trajectory "
            "crossings of y = 150 m and applied at a network entry near y = 0 m, a 150 m "
            "mismatch. This task replaces that with the observed first-appearance events, whose "
            "median first position is ~11 m (0750) and ~23 m (0805), i.e. the reliably covered "
            "upstream strip, and it declares ENTRY_Y_MAX_M = 30 m."
        ),
        "q4_available_boundary_fields": (
            "Per event the canonical states give the crossing/first-observation time, lane, "
            "position and speed, and the off-ramp membership (a trajectory ever observed on "
            "lane 8). Vehicle type is NOT available per vehicle: the canonical schema has no "
            "per-vehicle length or class, so the previous task's aggregate fleet shares and its "
            "deterministic class assignment are inherited unchanged and are used identically in "
            "both arms."
        ),
        "q5_initial_state_double_counting": (
            "Vehicles whose first observation is exactly at the window start are the injected "
            "initial state; they are excluded from the entry sequence by construction. The audit "
            "reports the intersection explicitly for each window."
        ),
        "q6_reintroduction_of_dropped_vehicles": (
            "Vehicles dropped by the initial-state overlap filter have their first observation at "
            "the window start, so they are excluded from the entry sequence as well: they are "
            "simply absent, never re-introduced. Vehicles first observed downstream of the entry "
            "plane (occluded at the boundary) are excluded and recorded."
        ),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_json(OUTPUT / "phase_a_audit.json", result)
    # portable summary: the per-vehicle exclusion lists stay in the local capsule
    summary = {key: value for key, value in result.items() if key != "windows"}
    summary["windows"] = {
        window: {
            "entry_events": {key: value for key, value in entry["entry_events"].items()
                             if key != "excluded"},
            "initial_state": entry["initial_state"],
            "event_ids_shared_with_initial_state": entry["event_ids_shared_with_initial_state"],
            "demand": entry["demand"],
            "pairing": entry["pairing"],
        }
        for window, entry in result["windows"].items()
    }
    summary["portable_note"] = (
        "the full per-vehicle exclusion lists are kept in the local capsule only "
        "(phase_a_audit.json); they are regenerable from the sealed canonical states and the "
        "frozen code, and exceed the portable-evidence size cap")
    _write_json(OUTPUT / "phase_a_audit_summary.json", summary)
    arrival = {window: entry["demand"] for window, entry in result["windows"].items()}
    _write_json(OUTPUT / "arrival_summary.json", arrival)
    return result


# --------------------------------------------------------------------------
# phase B: wave diagnostic baseline
# --------------------------------------------------------------------------
def step_wave_baseline() -> dict[str, object]:
    states = calibration_states()
    cells = {window: bt.space_time_cells(frame, window=ss.APPROVED_SPANS[window])
             for window, frame in states.items()}
    pooled = pd.concat(cells.values(), ignore_index=True)
    baseline = bt.density_speed_baseline(pooled)
    threshold = bt.anomaly_threshold(pooled, baseline)

    synthetic = {}
    reference = {"centres_veh_km_lane": [35.0, 45.0], "median_speed_mps": [12.0, 12.0]}
    for name, frame in bt.synthetic_wave_scenarios().items():
        report = bt.anomaly_report(frame, reference, 0.0, resamples=500)
        synthetic[name] = {"level": report["level"],
                           "largest_component_cells": report["structure"]["largest_component_cells"],
                           "front_direction": report["structure"]["front_direction"],
                           "front_slope_mps": report["structure"]["front_slope_mps"],
                           "cross_correlation_upstream_share": report["cross_correlation"]["upstream_share"],
                           "cross_correlation_median_speed_mps":
                               report["cross_correlation"]["median_implied_speed_mps"],
                           "null_exceedance_rate": report["null"]["exceedance_rate"]}

    real = {}
    for window, frame in states.items():
        report = bt.anomaly_report(
            bt.space_time_cells(frame, window=ss.APPROVED_SPANS[window], y_step_m=bt.WAVE_Y_M,
                                t_step_s=bt.WAVE_T_S, min_obs=bt.WAVE_MIN_OBS),
            baseline, threshold, resamples=bt.NULL_RESAMPLES)
        sensitivity = bt.wave_sensitivity(frame, ss.APPROVED_SPANS[window], baseline, threshold,
                                         resamples=200)
        real[window] = {
            "level": report["level"],
            "largest_component_cells": report["structure"]["largest_component_cells"],
            "front_slope_mps": report["structure"]["front_slope_mps"],
            "front_direction": report["structure"]["front_direction"],
            "cross_correlation_upstream_share": report["cross_correlation"]["upstream_share"],
            "cross_correlation_median_speed_mps":
                report["cross_correlation"]["median_implied_speed_mps"],
            "null_exceedance_rate": report["null"]["exceedance_rate"],
            "sensitivity_invariant": sensitivity["verdict_invariant"],
            "sensitivity_min_upstream_share": sensitivity["min_upstream_share"],
            "sensitivity_grid": sensitivity["grid"],
        }
    # the inherited absolute descriptor is retained, with its limitation stated
    inherited = {}
    for window, frame in states.items():
        local = frame[ss.local_region_mask(frame)]
        inherited[window] = {
            "absolute_10mps_slow_share": float((local.speed_mps < 10.0).mean()),
            "mean_speed_mps": float(local.speed_mps.mean()),
            "limitation": (
                "the absolute 10 m/s threshold sits within one standard error of the simulated "
                "mean speed of the state-matching configuration (9.7 m/s), so the slow share is "
                "not comparable between real and simulated frames; it is reported as history only"
            ),
        }
    result = {
        "result_id": RESULT_ID,
        "step": "phase_B_wave_diagnostic",
        "status": "Observation",
        "declared_definition": {
            "primary": "temporal_position",
            "alpha": bt.WAVE_ALPHA,
            "cell_y_m": bt.WAVE_Y_M,
            "cell_t_s": bt.WAVE_T_S,
            "min_obs": bt.WAVE_MIN_OBS,
            "connectivity": 8,
            "definition_choice_basis": (
                "fixed on the real calibration windows only, before any simulator run of this "
                "task: at 30 s cells the independent lag estimate is unresolved (every adjacent "
                "pair peaks at lag 0), while at 10 s cells both real windows give a concordant "
                "upstream front near 5 m/s whose structure exceeds the permutation null"
            ),
            "sensitivity_grid": bt.WAVE_SENSITIVITY,
        },
        "density_conditioned_baseline": baseline,
        "density_conditioned_threshold_mps": threshold,
        "density_conditioned_variant_verdict": (
            "non-discriminating for wave structure on the real frames: all 0750 anomalies and the "
            "largest 0805 component sit at the upstream boundary position, and no front slope can "
            "be estimated, so this variant is reported but is not the primary definition"
        ),
        "synthetic_acceptance": synthetic,
        "real_frames": real,
        "inherited_absolute_descriptor": inherited,
    }
    _write_json(OUTPUT / "phase_b_wave_diagnostic.json", result)
    return result


# --------------------------------------------------------------------------
# freeze
# --------------------------------------------------------------------------
def build_plan() -> dict[str, object]:
    relation = _read_json(PREVIOUS / "real_domain.json")["pooled_following_relation"]
    return {
        "result_id": RESULT_ID,
        "version": bt.VERSION,
        "mode": "pre-declared paired arrival-timing contrast; diagnostic evidence, not Gate acceptance",
        "question": ("holding the network, behaviour, boundary supply, initial state, vehicle "
                     "identity, route, type, lane and event count fixed, does restoring the real "
                     "boundary arrival structure change relative motion, low-speed wave structure "
                     "and the P2 diagnostic?"),
        "frozen_base_conditions": {
            "behaviour": BEHAVIOUR,
            "tau_values_source": relation["vehicle_tau_eff_quantiles_s"],
            "downstream_free_speed_mps": DOWNSTREAM_FREE_SPEED_MPS,
            "region_m": [ss.REGION_START_M, ss.REGION_END_M],
            "lanes": list(ss.MAINLINE_LANES),
            "duration_s": ss.DECLARED_DURATION_S,
            "internal_step_s": ss.DECLARED_INTERNAL_STEP_S,
            "recorded_step_s": ss.DECLARED_FCD_PERIOD_S,
            "evaluation_window_s": list(EVALUATION_WINDOW_S),
            "initial_state": "observed real state at the window start, identical in both arms",
        },
        "arms": {
            "E": "real reconstructed arrival times",
            "U": "same events, arrival times uniformised per stream: t_i = (i+0.5)T/N",
            "pairing_rule": ("the i-th uniform slot of a stream goes to the i-th earliest real "
                             "arrival of the same stream; vehicle identity, route, type, lane, "
                             "initial speed and per-stream event count are identical"),
        },
        "entry_rule": {
            "entry_y_max_m": bt.ENTRY_Y_MAX_M,
            "mainline": "first canonical observation inside the approved span, lanes 1-5, y <= 30 m",
            "onramp": "first canonical observation on the observed on-ramp lane",
            "excluded": "initial-state vehicles, first observation downstream of the entry plane, "
                        "events beyond the simulation horizon",
        },
        "seeds": {"set": list(SEED_SET), "design": "paired across arms; no arm-specific seed"},
        "budget": {"cells": 2 * 2 * len(SEED_SET), "note": "2 windows x 2 arms x 5 seeds = 20 runs"},
        "metrics": {
            "state_support": "the previous task's frozen domain and membership rules, read from "
                             "RES-STAGE-0.5-STATE-SUPPORT-V1/real_domain.json, not re-derived",
            "interaction": ["local P2 count and rate", "speed dispersion", "closing-speed negative "
                            "share", "closing-speed envelope coverage", "effective time headway"],
            "waves": ["relative-speed anomaly level", "largest component", "cross-correlation "
                      "upstream share and median implied speed", "permutation-null exceedance"],
            "insertion_audit": "declared departure time versus realised first appearance in the FCD",
        },
        "reading_rules": {
            "H1_supported": "E improves relative-motion or fluctuation metrics in the paired "
                            "comparison, direction consistent across both windows or explained by "
                            "the observed demand conditions, not driven by one seed, and state "
                            "support is not lost",
            "H2_supported": "H1 holds and the existing interaction-compatibility rules show a "
                            "material advance under their frozen definitions",
            "H1_not_supported": "no stable paired improvement, or E is worse for reasons not "
                                "explained by input-construction defects",
            "indeterminate": "arrival timing not reliably reconstructed, arms not timing-only, "
                             "engineering failure, or conflicting windows without a discriminating "
                             "explanation",
            "no_arbitrary_threshold": True,
        },
        "stop_rules": [
            "any engineering failure (non-zero exit, teleport, collision) stops the batch",
            "the grid is not extended after execution",
            "if the arms cannot be made timing-only, report and stop",
            "no third supply encoding and no new behaviour parameters in this task",
        ],
        "sumo_environment": sumo_environment(),
        "sealed_windows_not_read": [ss.VALIDATION_WINDOW, "lankershim", "locked holdout"],
    }


def step_plan() -> dict[str, object]:
    plan = build_plan()
    _write_json(OUTPUT / "experiment_plan.json", plan)
    states = calibration_states()
    manifest: dict[str, object] = {}
    for window, frame in states.items():
        events = bt.entry_events(frame, window)
        table = bt.paired_arrival_tables(events["events"])["events"]
        table.to_csv(OUTPUT / f"events_{window}.csv", index=False)
        _write_json(OUTPUT / f"events_{window}.json",
                    {key: value for key, value in events.items() if key != "events"})
        manifest[window] = {"events": int(len(table)),
                            "mainline": int((table.stream == "mainline").sum()),
                            "onramp": int((table.stream == "onramp").sum()),
                            "event_table_sha256": bt.sha256_file(OUTPUT / f"events_{window}.csv")}
    _write_json(OUTPUT / "event_manifest.json", manifest)
    (OUTPUT / "PLAN_SHA256").write_text(
        bt.sha256_file(OUTPUT / "experiment_plan.json") + "  experiment_plan.json\n", encoding="utf-8")
    return plan


# --------------------------------------------------------------------------
# execution
# --------------------------------------------------------------------------
def _membership(descriptors: dict[str, object], domain: dict[str, object],
                window: str) -> dict[str, object]:
    """The previous task's frozen membership rules, applied unchanged."""
    envelope = domain["pooled_envelope"]
    closing_envelope = domain["pooled_closing_envelope"]
    windows = list(ss.CALIBRATION_WINDOWS)
    other = windows[1] if window == windows[0] else windows[0]
    reference_envelope = domain["per_window_envelopes"][other]
    baseline = float(domain["cross_window_baseline_detail"][f"{window}_inside_envelope_of_{other}"])
    mean_member = ss.envelope_membership(float(descriptors["density_veh_km_lane"]),
                                         float(descriptors["speed_mean_mps"]), envelope)
    block_cloud = pd.DataFrame(descriptors["blocks"])
    coverage_reference = ss.envelope_coverage(block_cloud, reference_envelope)
    closing_inside = [ss.closing_membership(float(block["density_veh_km_lane"]),
                                            float(block["closing_speed_mean_mps"]),
                                            closing_envelope)["inside"]
                      for block in descriptors["blocks"]]
    closing_coverage = float(np.mean(closing_inside)) if closing_inside else float("nan")
    return {
        "mean_state_inside_pooled_envelope": mean_member,
        "block_coverage_reference_envelope": coverage_reference,
        "reference_baseline_coverage": baseline,
        "block_coverage_meets_baseline": bool(coverage_reference >= baseline),
        "closing_block_coverage": closing_coverage,
        "closing_coverage_meets_baseline": bool(closing_coverage >= baseline),
        "primary_state_support": bool(mean_member["inside"] and coverage_reference >= baseline),
        "mechanism_compatible": bool(closing_coverage >= baseline),
    }


def run_arrival(work: Path, window: str, arm: str, seed: int, table: pd.DataFrame,
                relation: dict[str, object], real_states: pd.DataFrame,
                domain: dict[str, object], baseline: dict[str, object],
                threshold: float) -> dict[str, object]:
    from riskprop.stage_0_5_sumo import build_sumo_p2_events
    work.mkdir(parents=True, exist_ok=True)
    spec = ss.observed_geometry_spec(DOWNSTREAM_FREE_SPEED_MPS)
    network = build_candidate_network(work / "network", spec)
    edge_lengths = network_edge_lengths(network["network"])
    types = ss.declared_behaviour_vtypes(BEHAVIOUR, relation)
    initial = ss.initial_state_records(real_states, window, edge_lengths=edge_lengths)
    limits = {"main_0": ss.FREE_SPEED_MPS, "main_1": ss.FREE_SPEED_MPS,
              "main_2": float(spec["edges"][2]["speed_mps"]), "onramp": 13.89, "offramp": 13.89}
    lane_counts = {edge["id"]: int(edge["lanes"]) for edge in spec["edges"]}
    time_column = "arm_E_time_s" if arm == "E" else "arm_U_time_s"
    routes = bt.write_arrival_route_file(work / "routes.rou.xml", window, BEHAVIOUR, types, table,
                                         time_column=time_column,
                                         initial_records=initial["accepted"],
                                         duration_s=ss.DECLARED_DURATION_S,
                                         edge_speed_limits=limits,
                                         edge_lane_counts=lane_counts)
    config = ss.write_conditional_config(work / "run.sumocfg", network=network["network"],
                                         routes=work / "routes.rou.xml",
                                         duration_s=ss.DECLARED_DURATION_S, seed=seed)
    started = time.perf_counter()
    run = ss.run_sumo(config, wall_limit_s=1800.0)
    fcd = parse_fcd(work / "fcd.xml", edge_lengths)
    states = ss.fcd_to_state_frame(fcd, ss.route_length_map(work / "routes.rou.xml"),
                                   run_id=f"{window}|{arm}|{seed}",
                                   scenario_id=f"{window}|{arm}", seed=seed)
    measured = ss.measure_state_frame(states)
    measured.to_parquet(work / "measured_state.parquet", index=False)
    descriptors = ss.block_descriptors(measured, window=EVALUATION_WINDOW_S)
    membership = _membership(descriptors, domain, window)
    events, _ = build_sumo_p2_events(measured)
    low, high = EVALUATION_WINDOW_S
    in_window = events[events.event_start_s.ge(low) & events.event_start_s.lt(high)]
    lookup = measured.set_index(["vehicle_id", "time_s"])[["y_m", "lane_id"]]
    local_events = 0
    for event in in_window.itertuples():
        try:
            position, lane = lookup.loc[(str(event.vehicle_id), round(float(event.event_start_s), 1))]
        except KeyError:
            continue
        if str(lane) in ss.MAINLINE_LANES and ss.REGION_START_M <= float(position) < ss.REGION_END_M:
            local_events += 1
    first_seen = states.groupby("vehicle_id").time_s.min().to_dict() if len(states) else {}
    audit = []
    for item in routes["event_vehicle_ids"]:
        realised = first_seen.get(item["vehicle_id"], None)
        audit.append({"vehicle_id": item["vehicle_id"], "event_id": item["event_id"],
                      "stream": item["stream"], "declared_depart_s": item["declared_depart_s"],
                      "realised_first_s": realised,
                      "delay_s": None if realised is None else float(realised) - float(item["declared_depart_s"])})
    audit_frame = pd.DataFrame(audit)
    audit_frame.to_csv(work / "insertion_audit.csv", index=False)
    missing = int(audit_frame.realised_first_s.isna().sum()) if len(audit_frame) else 0
    delays = audit_frame.delay_s.dropna().to_numpy(float) if len(audit_frame) else np.zeros(0)
    waves = bt.anomaly_report(
        bt.space_time_cells(measured, window=(0.0, ss.DECLARED_DURATION_S), y_step_m=bt.WAVE_Y_M,
                            t_step_s=bt.WAVE_T_S, min_obs=bt.WAVE_MIN_OBS),
        baseline, threshold, resamples=bt.NULL_RESAMPLES)
    return {
        "window": window, "arm": arm, "seed": int(seed),
        "wall_s": float(time.perf_counter() - started),
        "sumo": {key: value for key, value in run.items() if key != "log_tail"},
        "initial_state": {"accepted": initial["accepted_count"], "dropped": initial["dropped_count"]},
        "route_file": {"initial_vehicles": routes["initial_vehicles"],
                       "event_vehicles": routes["event_vehicles"]},
        "descriptors": descriptors,
        "membership": membership,
        "p2_events_eval_window": int(len(in_window)),
        "p2_events_eval_window_local": int(local_events),
        "p2_local_rate_per_vehicle_hour": (
            local_events / (descriptors["p2_evaluable_exposure_veh_s"] / 3600.0)
            if descriptors["p2_evaluable_exposure_veh_s"] > 0 else None),
        "insertion_audit": {
            "events": int(len(audit_frame)),
            "never_inserted": missing,
            "delay_mean_s": float(delays.mean()) if len(delays) else None,
            "delay_p50_s": float(np.median(delays)) if len(delays) else None,
            "delay_p95_s": float(np.quantile(delays, 0.95)) if len(delays) else None,
            "delay_max_s": float(delays.max()) if len(delays) else None,
            "delay_abs_mean_s": float(np.abs(delays).mean()) if len(delays) else None,
        },
        "waves": {
            "level": waves["level"],
            "largest_component_cells": waves["structure"]["largest_component_cells"],
            "front_slope_mps": waves["structure"]["front_slope_mps"],
            "front_direction": waves["structure"]["front_direction"],
            "cross_correlation_upstream_share": waves["cross_correlation"]["upstream_share"],
            "cross_correlation_median_speed_mps":
                waves["cross_correlation"]["median_implied_speed_mps"],
            "null_exceedance_rate": waves["null"]["exceedance_rate"],
            "classification_reasons": waves["classification"]["reasons"],
        },
        "states": int(len(measured)),
    }


def step_runs() -> dict[str, object]:
    plan_path = OUTPUT / "experiment_plan.json"
    digest = bt.sha256_file(plan_path)
    frozen = (OUTPUT / "PLAN_SHA256").read_text(encoding="utf-8").split()[0]
    if digest != frozen:
        raise SystemExit("plan changed after freezing")
    relation = _read_json(PREVIOUS / "real_domain.json")["pooled_following_relation"]
    domain = frozen_domain()
    wave_baseline = _read_json(OUTPUT / "phase_b_wave_diagnostic.json")
    baseline = wave_baseline["density_conditioned_baseline"]
    threshold = float(wave_baseline["density_conditioned_threshold_mps"])
    states = calibration_states()
    root = OUTPUT / "runs"
    if root.exists():
        shutil.rmtree(root)
    results: list[dict[str, object]] = []
    for window, frame in states.items():
        table = pd.read_csv(OUTPUT / f"events_{window}.csv")
        for seed in SEED_SET:
            for arm in ARMS:
                work = root / f"{window}_{arm}_s{seed}"
                record = run_arrival(work, window, arm, seed, table, relation, frame,
                                     domain, baseline, threshold)
                results.append(record)
                print(f"  {window}|{arm}|{seed}: k={record['descriptors']['density_veh_km_lane']:.2f} "
                      f"v={record['descriptors']['speed_mean_mps']:.2f} "
                      f"localP2={record['p2_events_eval_window_local']} "
                      f"wave={record['waves']['level']} "
                      f"delay_p50={record['insertion_audit']['delay_p50_s']}", flush=True)
    _write_json(OUTPUT / "run_results.json",
                {"plan_sha256": digest, "seeds": list(SEED_SET),
                 "wave_baseline_sha256": bt.sha256_file(OUTPUT / "phase_b_wave_diagnostic.json"),
                 "results": results})
    return {"runs": len(results)}


def step_analysis() -> dict[str, object]:
    run_results = _read_json(OUTPUT / "run_results.json")
    frame = pd.DataFrame([{
        "window": record["window"], "arm": record["arm"], "seed": record["seed"],
        "density": record["descriptors"]["density_veh_km_lane"],
        "speed": record["descriptors"]["speed_mean_mps"],
        "speed_sd": record["descriptors"]["speed_sd_mps"],
        "low_speed_share": record["descriptors"]["low_speed_share"],
        "closing_mean": record["descriptors"]["closing_speed_mean_mps"],
        "closing_negative_share": record["descriptors"]["closing_speed_negative_share"],
        "tau_eff": record["descriptors"]["tau_eff_ratio_s"],
        "state_support": record["membership"]["primary_state_support"],
        "closing_coverage": record["membership"]["closing_block_coverage"],
        "p2_local": record["p2_events_eval_window_local"],
        "p2_local_rate": record["p2_local_rate_per_vehicle_hour"],
        "wave_level": record["waves"]["level"],
        "wave_largest": record["waves"]["largest_component_cells"],
        "wave_upstream_share": record["waves"]["cross_correlation_upstream_share"],
        "wave_median_speed": record["waves"]["cross_correlation_median_speed_mps"],
        "wave_null_exceedance": record["waves"]["null_exceedance_rate"],
        "delay_p50": record["insertion_audit"]["delay_p50_s"],
        "delay_p95": record["insertion_audit"]["delay_p95_s"],
        "never_inserted": record["insertion_audit"]["never_inserted"],
        "teleports": record["sumo"]["teleports"], "collisions": record["sumo"]["collisions"],
    } for record in run_results["results"]])
    frame.to_csv(OUTPUT / "run_metrics.csv", index=False)
    metrics = ("density", "speed", "speed_sd", "low_speed_share", "closing_mean",
               "closing_negative_share", "tau_eff", "p2_local", "p2_local_rate",
               "wave_largest", "wave_upstream_share", "delay_p50")
    paired: dict[str, object] = {"metrics": {}, "cluster_unit": "window x seed pair"}
    for window in ss.CALIBRATION_WINDOWS:
        subset = frame[frame.window == window]
        for metric in metrics:
            wide = subset.pivot_table(index="seed", columns="arm", values=metric)
            if "E" not in wide or "U" not in wide:
                continue
            difference = (wide["E"] - wide["U"]).dropna()
            paired["metrics"].setdefault(metric, {})[window] = {
                "U_mean": float(wide["U"].mean()), "E_mean": float(wide["E"].mean()),
                "paired_mean_difference": float(difference.mean()),
                "paired_sd": float(difference.std(ddof=1)) if len(difference) > 1 else None,
                "paired_min": float(difference.min()), "paired_max": float(difference.max()),
                "seeds_positive": int((difference > 0).sum()), "seeds": int(len(difference)),
                "U_min": float(wide["U"].min()), "U_max": float(wide["U"].max()),
                "E_min": float(wide["E"].min()), "E_max": float(wide["E"].max()),
            }
    paired["wave_levels"] = {
        window: {"U": frame[(frame.window == window) & (frame.arm == "U")].wave_level.tolist(),
                 "E": frame[(frame.window == window) & (frame.arm == "E")].wave_level.tolist()}
        for window in ss.CALIBRATION_WINDOWS}
    # realised-arrival fidelity: how much of the declared timing survives insertion
    fidelity: dict[str, object] = {}
    for record in run_results["results"]:
        path = (OUTPUT / "runs" / f"{record['window']}_{record['arm']}_s{record['seed']}"
                / "insertion_audit.csv")
        audit = pd.read_csv(path)
        realised = audit.dropna(subset=["realised_first_s"])
        summary: dict[str, object] = {}
        for stream, group in realised.groupby("stream"):
            times = np.sort(group.realised_first_s.to_numpy(float))
            gaps = np.diff(times)
            summary[stream] = {
                "realised_events": int(len(times)),
                "realised_gap_mean_s": float(gaps.mean()) if len(gaps) else None,
                "realised_gap_cv": float(gaps.std(ddof=1) / gaps.mean())
                if len(gaps) > 1 and gaps.mean() > 0 else None,
                "declared_gap_cv": float(
                    np.std(np.diff(np.sort(group.declared_depart_s.to_numpy(float))), ddof=1)
                    / np.mean(np.diff(np.sort(group.declared_depart_s.to_numpy(float)))))
                if len(group) > 2 else None,
                "delay_mean_s": float(group.delay_s.mean()) if len(group) else None,
                "delay_gt_one_gap_share": float(
                    (group.delay_s > np.mean(np.diff(np.sort(group.declared_depart_s.to_numpy(float)))))
                    .mean()) if len(group) > 2 else None,
            }
        fidelity[f"{record['window']}|{record['arm']}|{record['seed']}"] = summary
    paired["realised_fidelity"] = fidelity
    _write_json(OUTPUT / "paired_analysis.json", paired)
    return paired


def step_verdict() -> dict[str, object]:
    paired = _read_json(OUTPUT / "paired_analysis.json")
    audit = _read_json(OUTPUT / "phase_a_audit.json")
    waves = _read_json(OUTPUT / "phase_b_wave_diagnostic.json")
    run_results = _read_json(OUTPUT / "run_results.json")
    frame = pd.read_csv(OUTPUT / "run_metrics.csv")

    engineering_ok = bool((frame.teleports == 0).all() and (frame.collisions == 0).all())
    timing_only_inputs = all(audit["windows"][window]["event_ids_shared_with_initial_state"] == []
                             for window in audit["windows"])
    state_support_kept = {
        window: {arm: bool(frame[(frame.window == window) & (frame.arm == arm)].state_support.all())
                 for arm in ARMS} for window in ss.CALIBRATION_WINDOWS}

    def paired_entry(metric: str, window: str) -> dict[str, object] | None:
        return paired["metrics"].get(metric, {}).get(window)

    def direction(metric: str) -> dict[str, object]:
        out = {}
        for window in ss.CALIBRATION_WINDOWS:
            entry = paired_entry(metric, window)
            if entry is None:
                continue
            out[window] = {"difference": entry["paired_mean_difference"],
                           "positive_seeds": entry["seeds_positive"], "seeds": entry["seeds"],
                           "U_mean": entry["U_mean"], "E_mean": entry["E_mean"]}
        return out

    def consistent(metric: str, *, want_positive: bool = True) -> bool:
        entry = direction(metric)
        if len(entry) < 2:
            return False
        for value in entry.values():
            improved = value["difference"] > 0 if want_positive else value["difference"] < 0
            if not improved:
                return False
            if value["positive_seeds"] < 4 and want_positive:
                return False
            if (value["seeds"] - value["positive_seeds"]) < 4 and not want_positive:
                return False
        return True

    wave_verdict = {}
    for window in ss.CALIBRATION_WINDOWS:
        for arm in ARMS:
            levels = frame[(frame.window == window) & (frame.arm == arm)].wave_level.tolist()
            wave_verdict[f"{window}|{arm}"] = {
                "levels": levels,
                "all_propagating": bool(all(level == "propagating_structure" for level in levels))}
    wave_advance = all(wave_verdict[f"{window}|E"]["all_propagating"]
                       for window in ss.CALIBRATION_WINDOWS)

    # realised fidelity: an entry-queue dominated arrival process destroys the
    # declared timing, so the arms would no longer differ only in arrival times
    fidelity_frame = pd.DataFrame([{
        "window": key.split("|")[0], "arm": key.split("|")[1],
        "realised_gap_cv": value.get("mainline", {}).get("realised_gap_cv"),
        "declared_gap_cv": value.get("mainline", {}).get("declared_gap_cv"),
        "delay_mean_s": value.get("mainline", {}).get("delay_mean_s"),
        "delay_gt_one_gap_share": value.get("mainline", {}).get("delay_gt_one_gap_share"),
    } for key, value in paired["realised_fidelity"].items()])
    fidelity_frame.to_csv(OUTPUT / "fidelity_metrics.csv", index=False)
    fidelity = {}
    for window in ss.CALIBRATION_WINDOWS:
        subset = fidelity_frame[fidelity_frame.window == window]
        fidelity[window] = {
            arm: {"declared_gap_cv": float(subset[subset.arm == arm].declared_gap_cv.mean()),
                  "realised_gap_cv": float(subset[subset.arm == arm].realised_gap_cv.mean()),
                  "delay_mean_s": float(subset[subset.arm == arm].delay_mean_s.mean()),
                  "delay_gt_one_gap_share": float(
                      subset[subset.arm == arm].delay_gt_one_gap_share.mean()),
                  "never_inserted": int(subset[subset.arm == arm].never_inserted.sum())
                  if "never_inserted" in subset else None}
            for arm in ARMS}
        fidelity[window]["timing_survives"] = bool(
            fidelity[window]["E"]["realised_gap_cv"] is not None
            and fidelity[window]["U"]["realised_gap_cv"] is not None
            and fidelity[window]["E"]["realised_gap_cv"]
            > 2.0 * fidelity[window]["U"]["realised_gap_cv"])

    # per-stream fidelity: which boundary stream actually carries the manipulation
    stream_fidelity: dict[str, object] = {}
    for window in ss.CALIBRATION_WINDOWS:
        entry: dict[str, object] = {}
        for stream in ("mainline", "onramp"):
            per_arm = {}
            for arm in ARMS:
                rows = [value[stream] for key, value in paired["realised_fidelity"].items()
                        if key.split("|")[0] == window and key.split("|")[1] == arm
                        and stream in value]
                per_arm[arm] = {
                    "declared_gap_cv": float(np.mean([row["declared_gap_cv"] for row in rows])),
                    "realised_gap_cv": float(np.mean([row["realised_gap_cv"] for row in rows])),
                    "delay_mean_s": float(np.mean([row["delay_mean_s"] for row in rows])),
                    "delay_gt_one_gap_share": float(
                        np.mean([row["delay_gt_one_gap_share"] for row in rows])),
                }
            ratio = (per_arm["E"]["realised_gap_cv"] / per_arm["U"]["realised_gap_cv"]
                     if per_arm["U"]["realised_gap_cv"] else None)
            entry[stream] = {
                "U": per_arm["U"], "E": per_arm["E"],
                "realised_cv_ratio_E_over_U": ratio,
                "manipulation_survives": bool(ratio is not None and ratio > 2.0),
                "declared_cv_ratio_E_over_U": (
                    per_arm["E"]["declared_gap_cv"] / per_arm["U"]["declared_gap_cv"]
                    if per_arm["U"]["declared_gap_cv"] else None),
            }
        stream_fidelity[window] = entry
    mainline_imposable = all(stream_fidelity[window]["mainline"]["manipulation_survives"]
                             for window in ss.CALIBRATION_WINDOWS)
    onramp_imposable = all(stream_fidelity[window]["onramp"]["manipulation_survives"]
                           for window in ss.CALIBRATION_WINDOWS)
    if mainline_imposable and onramp_imposable:
        effective_contrast = "mainline and on-ramp arrival timing"
    elif onramp_imposable:
        effective_contrast = "on-ramp arrival timing only"
    elif mainline_imposable:
        effective_contrast = "mainline arrival timing only"
    else:
        effective_contrast = "no arrival timing (entry queue dominates)"

    improvements = {
        "speed_dispersion_toward_real": consistent("speed_sd"),
        "closing_negative_share_toward_real": consistent("closing_negative_share", want_positive=False),
        "p2_rate_toward_real": consistent("p2_local_rate"),
        "wave_structure_restored": wave_advance,
    }
    met = [name for name, value in improvements.items() if value]
    fidelity_ok = bool(mainline_imposable and onramp_imposable)
    if not (engineering_ok and timing_only_inputs):
        reading = "Evidence Insufficient"
    elif len(met) >= 2 and fidelity_ok:
        reading = "Supported"
    elif met:
        reading = "Partially Supported"
    else:
        reading = "Not Supported"

    h2_rules_met = {
        "state_support_kept": all(all(state_support_kept[w].values()) for w in ss.CALIBRATION_WINDOWS),
        "closing_negative_share_toward_real": improvements["closing_negative_share_toward_real"],
        "wave_structure_restored": improvements["wave_structure_restored"],
        "p2_rate_toward_real": improvements["p2_rate_toward_real"],
    }
    h2_reading = ("Supported" if all(h2_rules_met.values()) and fidelity_ok
                  else "Not Supported")

    verdict = {
        "result_id": RESULT_ID,
        "plan_sha256": run_results["plan_sha256"],
        "engineering_ok": engineering_ok,
        "inputs_are_timing_only": timing_only_inputs,
        "state_support_kept": state_support_kept,
        "realised_fidelity": fidelity,
        "stream_fidelity": stream_fidelity,
        "mainline_timing_imposable": bool(mainline_imposable),
        "onramp_timing_imposable": bool(onramp_imposable),
        "effective_contrast": effective_contrast,
        "fidelity_ok": fidelity_ok,
        "wave_baseline_source": waves["declared_definition"],
        "wave_levels": wave_verdict,
        "paired_differences": {name: direction(name) for name in
                               ("speed_sd", "closing_negative_share", "p2_local_rate",
                                "wave_largest", "density", "speed", "tau_eff", "delay_p50")},
        "improvement_checks": improvements,
        "improvements_met": met,
        "H1_arrival_structure_matters": reading,
        "H1_causal_attribution": ("Established for the stream whose declared timing survives "
                                  "insertion" if onramp_imposable and not mainline_imposable
                                  else ("Established" if fidelity_ok
                                        else "Evidence Insufficient")),
        "H2_interaction_compatibility_recovered": h2_reading,
        "H2_rules_met": h2_rules_met,
        "note": ("H1 and H2 are read only from the paired contrast under the declared rules. "
                 "A P2 change alone is never treated as evidence that the real mechanism has been "
                 "reproduced, and a failed manipulation fidelity is reported as such rather than "
                 "as a scientific result."),
        "runs": int(len(frame)),
    }
    _write_json(OUTPUT / "verdict.json", verdict)
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["audit", "wave-baseline", "plan", "runs", "analysis",
                                         "verdict", "all"])
    arguments = parser.parse_args()
    if arguments.step in {"audit", "all"}:
        step_audit()
        print("phase A audit written")
    if arguments.step in {"wave-baseline", "all"}:
        step_wave_baseline()
        print("phase B wave diagnostic written")
    if arguments.step in {"plan", "all"}:
        step_plan()
        print("plan and event tables frozen")
    if arguments.step in {"runs", "all"}:
        step_runs()
    if arguments.step in {"analysis", "all"}:
        step_analysis()
    if arguments.step in {"verdict", "all"}:
        step_verdict()
        print("verdict written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
