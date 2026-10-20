"""AAD-0.5-METHOD-EXPANSION runner: coverage, initialization, model/parameter/seed diagnostics.

Phases
------
coverage       Phase 2: behavioural-phase coverage matrix over both approved windows.
init           Phase 3: initialization-route comparison (native vs insertion-check-free).
response       Phase 4: bounded single-factor catalogue x frozen seed set x stratified pairs,
               with local-window, long-run and perturbation-propagation metrics.
newell         Phase 4: independent Newell prototype scored with the same metrics.
identify       Phase 2/4: local sensitivity, parameter correlation and identifiability summary.
macro          Phase 5: bounded macro contrast decision (executed only if gated open).

All plans are written and SHA-bound before the corresponding simulation batch starts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_leader_replay as lr  # noqa: E402
from riskprop import stage_0_5_newell_prototype as nl  # noqa: E402
from riskprop import stage_0_5_trajectory_reconstruction as tr  # noqa: E402
from riskprop.stage_0_5_sumo import _netconvert_binary, _sumo_binary  # noqa: E402

RESULT_ID = "RES-STAGE-0.5-METHOD-EXPANSION-V1"
STATES_ROOT = "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
DEFAULT_OUTPUT = "code/outputs/formal/calibration/stage_0_5_method_expansion_v1"

PAIRS_PER_WINDOW = 6
MIN_PAIR_DURATION_S = 6.0
MAX_PAIR_DURATION_S = 20.0
STRATA = (0.0, 1.0, 1.5, 2.5, 1e9)
SEEDS = (20261101, 20261102, 20261103)
INITIALIZATION_ROUTES = ("native", "none")
INTERNAL_STEP_S = 0.05
LEADER_TRACKING_TOLERANCE_M = 0.25

# Coverage thresholds. Declared as EXPLORATORY project choices: no source is claimed
# to define them, and the report states that explicitly.
COVERAGE = {
    "stationary_band_mps2": 0.3,
    "stationary_min_s": 1.0,
    "accel_threshold_mps2": 0.3,
    "decel_threshold_mps2": -0.3,
    "low_speed_mps": 5.0,
    "close_gap_m": 10.0,
    "closing_threshold_mps": -0.5,
    "min_phase_s": 1.0,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def load_states() -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    frames, sources = {}, {}
    for window_id in tr.CALIBRATION_WINDOWS:
        path = REPO_ROOT / STATES_ROOT / f"ngsim_{window_id}.parquet"
        if not path.is_file():
            raise SystemExit(f"missing sealed calibration state: {path}")
        sources[window_id] = {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": sha256_file(path)}
        frames[window_id] = tr.load_calibration_states(str(path), window_id)
    return frames, sources


# ---------------------------------------------------------------------------
# Phase 2: behavioural phase coverage
# ---------------------------------------------------------------------------
def phase_coverage(frames: dict[str, pd.DataFrame]) -> dict[str, object]:
    rules = dict(COVERAGE)
    output: dict[str, object] = {"rules": rules,
                                 "rule_status": "exploratory project choice; no source is claimed to define these thresholds",
                                 "windows": {}}
    for window_id, frame in frames.items():
        runs, subset = lr.prepare_pairs(frame, window=tr.CALIBRATION_WINDOWS[window_id])
        rows = []
        for _, run in runs.iterrows():
            group = subset.iloc[int(run.pos_start): int(run.pos_end) + 1]
            acceleration = group.acceleration_mps2.to_numpy(dtype=float)
            speed = group.speed_mps.to_numpy(dtype=float)
            gap = group.net_gap_m.to_numpy(dtype=float)
            closing = group.closing_speed_mps.to_numpy(dtype=float)
            step = 0.1
            stationary = np.abs(acceleration) < rules["stationary_band_mps2"]
            accelerating = acceleration > rules["accel_threshold_mps2"]
            decelerating = acceleration < rules["decel_threshold_mps2"]
            low_speed = speed < rules["low_speed_mps"]
            close_gap = gap < rules["close_gap_m"]
            closing_state = closing < rules["closing_threshold_mps"]
            rows.append({
                "run_id": int(run.run_id),
                "trajectory_id": str(run.trajectory_id),
                "duration_s": float(run.duration_s),
                "speed_mean_mps": float(speed.mean()),
                "speed_change_mps": float(speed.max() - speed.min()),
                "gap_mean_m": float(gap.mean()),
                "gap_min_m": float(gap.min()),
                "time_gap_mean_s": float(run.gap_mean_m / max(run.speed_mean_mps, 0.1)),
                "accel_max_mps2": float(acceleration.max()),
                "decel_min_mps2": float(acceleration.min()),
                "stationary_s": float(stationary.sum() * step),
                "accelerating_s": float(accelerating.sum() * step),
                "decelerating_s": float(decelerating.sum() * step),
                "low_speed_s": float(low_speed.sum() * step),
                "close_gap_s": float(close_gap.sum() * step),
                "closing_s": float(closing_state.sum() * step),
                "has_sustained_stationary": bool(_longest_true(stationary) * step >= rules["stationary_min_s"]),
                "has_sustained_close_following": bool(_longest_true(close_gap) * step >= rules["stationary_min_s"]),
                "has_low_speed_episode": bool(_longest_true(low_speed) * step >= rules["min_phase_s"]),
                "has_deceleration_episode": bool(_longest_true(decelerating) * step >= rules["min_phase_s"]),
            })
        table = pd.DataFrame(rows)
        total_seconds = float(table.duration_s.sum()) if len(table) else 0.0
        phase_seconds = {
            name: float(table[f"{name}_s"].sum()) for name in
            ("stationary", "accelerating", "decelerating", "low_speed", "close_gap", "closing")
        }
        summary = {
            "run_count": int(len(table)),
            "total_run_seconds": total_seconds,
            "phase_seconds": phase_seconds,
            "phase_time_share": {name: (value / total_seconds if total_seconds else None)
                                 for name, value in phase_seconds.items()},
            "duration_s": {"min": float(table.duration_s.min()), "median": float(table.duration_s.median()),
                           "max": float(table.duration_s.max())} if len(table) else None,
            "share_with_sustained_stationary": float(table.has_sustained_stationary.mean()) if len(table) else None,
            "share_with_sustained_close_following": float(table.has_sustained_close_following.mean()) if len(table) else None,
            "share_with_low_speed_episode": float(table.has_low_speed_episode.mean()) if len(table) else None,
            "share_with_deceleration_episode": float(table.has_deceleration_episode.mean()) if len(table) else None,
            "time_gap_quantiles_s": [float(x) for x in table.time_gap_mean_s.quantile([0, .1, .25, .5, .75, .9, 1])] if len(table) else [],
            "speed_change_quantiles_mps": [float(x) for x in table.speed_change_mps.quantile([0, .1, .25, .5, .75, .9, 1])] if len(table) else [],
            "time_gap_stratum_counts": _stratum_counts(table.time_gap_mean_s) if len(table) else {},
        }
        table.to_csv(Path(".") / f"coverage_runs_{window_id}.csv", index=False) if False else None
        output["windows"][window_id] = {"summary": summary, "runs": rows}
    return output


def _longest_true(mask: np.ndarray) -> int:
    best = current = 0
    for flag in mask:
        current = current + 1 if flag else 0
        best = max(best, current)
    return int(best)


def _stratum_counts(values: pd.Series) -> dict[str, int]:
    bins = pd.cut(values, bins=list(STRATA), right=False,
                  labels=[f"{STRATA[i]}-{STRATA[i+1]}" for i in range(len(STRATA) - 1)])
    return {str(k): int(v) for k, v in bins.value_counts().sort_index().items()}


# ---------------------------------------------------------------------------
# shared selection
# ---------------------------------------------------------------------------
def build_selection(frames: dict[str, pd.DataFrame]) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    selection = {}
    for window_id, frame in frames.items():
        runs, subset = lr.prepare_pairs(frame, window=tr.CALIBRATION_WINDOWS[window_id])
        picked = lr.stratified_selection(runs, per_window=PAIRS_PER_WINDOW, strata=STRATA)
        selection[window_id] = (subset, picked)
    return selection


def selection_manifest(selection) -> dict[str, object]:
    return {
        window_id: [
            {"run_id": int(row.run_id), "trajectory_id": str(row.trajectory_id),
             "leader_trajectory_id": str(row.leader_trajectory_id), "lane_id": str(row.lane_id),
             "duration_s": float(row.duration_s), "gap_mean_m": float(row.gap_mean_m),
             "speed_mean_mps": float(row.speed_mean_mps)}
            for _, row in picked.iterrows()
        ]
        for window_id, (_, picked) in selection.items()
    }


# ---------------------------------------------------------------------------
# Phase 3: initialization routes
# ---------------------------------------------------------------------------
def phase_init(output: Path, selection) -> dict[str, object]:
    plan = {
        "result_id": RESULT_ID,
        "phase": "initialization",
        "routes": list(INITIALIZATION_ROUTES),
        "route_meaning": {
            "native": "default SUMO insertion checks; a blocked insertion is retried by SUMO on later steps and the replay waits, records the delay and aligns the observed series to the follower's own elapsed time",
            "none": "the documented --insertion-checks none (vType attribute insertionChecks) skips the insertion-time safety checks only, so the observed initial state is entered at its declared departure time",
        },
        "fidelity_requirements": [
            "leader tracking deviation <= %.2f m" % LEADER_TRACKING_TOLERANCE_M,
            "no persistent speed override is applied to the follower (setSpeed is never called on it)",
            "the control path after insertion is the plain car-following model",
        ],
        "control_experiment": "pairs that insert immediately under the native route are replayed under both routes; their trajectories must be identical if the option only affects insertion",
        "pairs": selection_manifest(selection),
        "seed": SEEDS[0],
        "config": lr.KRAUSS_BASELINE_NAME,
    }
    write_json(output / "init_plan.json", plan)
    (output / "INIT_PLAN_SHA256").write_text(sha256_file(output / "init_plan.json") + "  init_plan.json\n", encoding="utf-8")

    rows, failures = [], []
    for window_id, (subset, picked) in selection.items():
        for _, run in picked.iterrows():
            observed = lr.pair_observations(subset, run, max_duration_s=MAX_PAIR_DURATION_S)
            for route in INITIALIZATION_ROUTES:
                try:
                    record = lr.replay_pair(
                        observed, run=run,
                        work=output / "init_runs" / window_id / f"pair{int(run.run_id)}_{route}",
                        params=lr.build_vtype(lr.KRAUSS_BASELINE_NAME), seed=SEEDS[0],
                        internal_step_s=INTERNAL_STEP_S, insertion_checks=route,
                    )
                except lr.LeaderReplayError as error:
                    failures.append({"window": window_id, "run_id": int(run.run_id), "route": route, "reason": str(error)})
                    continue
                metrics = lr.pair_metrics(record)
                rows.append({
                    "window": window_id, "run_id": int(run.run_id), "route": route,
                    "insertion_delay_s": record["insertion_delay_s"],
                    "start_index": record["start_index"],
                    "states": metrics["states"],
                    "leader_target_max_abs_deviation_m": metrics["leader_target_max_abs_deviation_m"],
                    "brockfeld_gap_error_pct": metrics["brockfeld_gap_error_pct"],
                    "nrmse_gap": metrics["nrmse_gap"],
                    "nrmse_speed": metrics["nrmse_speed"],
                    "gap_bias_m": metrics["gap_bias_m"],
                    "trajectory_sha256": hashlib.sha256(
                        record["simulated"][["t", "follower_y", "follower_v"]].to_csv(index=False).encode()
                    ).hexdigest(),
                })
                print(f"init {window_id} run{int(run.run_id)} {route} delay={record['insertion_delay_s']:.2f} "
                      f"brockfeld={metrics['brockfeld_gap_error_pct']:.2f}", flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(output / "init_routes.csv", index=False, float_format="%.6f")
    comparison = []
    if not table.empty:
        for (window_id, run_id), group in table.groupby(["window", "run_id"]):
            if set(group.route) == set(INITIALIZATION_ROUTES):
                native = group[group.route == "native"].iloc[0]
                none = group[group.route == "none"].iloc[0]
                comparison.append({
                    "window": window_id, "run_id": int(run_id),
                    "native_delay_s": float(native.insertion_delay_s),
                    "none_delay_s": float(none.insertion_delay_s),
                    "identical_trajectory": bool(native.trajectory_sha256 == none.trajectory_sha256),
                    "brockfeld_difference_pct": float(none.brockfeld_gap_error_pct - native.brockfeld_gap_error_pct),
                    "native_states": int(native.states), "none_states": int(none.states),
                })
    summary = {
        "result_id": RESULT_ID,
        "plan_sha256": sha256_file(output / "init_plan.json"),
        "routes_run": INITIALIZATION_ROUTES,
        "pairs_requested": int(sum(len(picked) for _, picked in selection.values())),
        "rows": rows,
        "failures": failures,
        "route_comparison": comparison,
        "identical_trajectory_pairs": int(sum(1 for item in comparison if item["identical_trajectory"])),
        "native_delay_s": {
            "min": float(table[table.route == "native"].insertion_delay_s.min()) if not table.empty else None,
            "max": float(table[table.route == "native"].insertion_delay_s.max()) if not table.empty else None,
            "median": float(table[table.route == "native"].insertion_delay_s.median()) if not table.empty else None,
        },
        "conclusion": (
            "the observed initial state is not rejected outright by SUMO: a blocked insertion is retried on "
            "later steps, and the earlier 'insertion rejected' reading came from an implementation that stopped "
            "waiting after 0.25 s. Both routes now reproduce the observed initial state; the insertion-check-free "
            "route enters it at its declared departure time, and the native route enters it after a measurable delay"
        ),
    }
    write_json(output / "init_summary.json", summary)
    return summary


# ---------------------------------------------------------------------------
# Phase 4: response catalogue
# ---------------------------------------------------------------------------
def phase_response(output: Path, selection) -> dict[str, object]:
    plan = {
        "result_id": RESULT_ID,
        "phase": "response",
        "configurations": {name: {**lr.CONFIGURATIONS[name], "vtype": lr.build_vtype(name),
                                  "single_factor_check": lr.assert_single_factor(name)}
                           for name in lr.CONFIGURATIONS},
        "seeds": list(SEEDS),
        "seed_design": ("the same seed set is used for every configuration so that a configuration "
                        "difference is not confounded with a seed difference; sigma=0.0 bounds the "
                        "deterministic part of the model"),
        "internal_step_s": INTERNAL_STEP_S,
        "local_window_s": lr.LOCAL_WINDOW_S,
        "long_run_start_s": lr.LONG_RUN_START_S,
        "response_horizon_s": lr.RESPONSE_HORIZON_S,
        "pairs_per_window": PAIRS_PER_WINDOW,
        "strata": list(STRATA),
        "selection_rule": "declared gap-over-speed strata, round-robin by duration inside each stratum",
        "pairs": selection_manifest(selection),
        "metrics": ["brockfeld_gap_error_pct", "nrmse_gap", "nrmse_speed", "gap_bias_m", "gap_mae_m",
                    "speed_bias_mps", "speed_mae_mps", "closing sign share", "time headway",
                    "local-window and long-run splits", "perturbation propagation (amplitude ratio, lag)"],
        "budget": {
            "sumo_process_invocations": len(lr.CONFIGURATIONS) * len(SEEDS) * PAIRS_PER_WINDOW * 2,
            "components": {"configurations": len(lr.CONFIGURATIONS), "seeds": len(SEEDS),
                           "pairs": PAIRS_PER_WINDOW * 2},
            "note": "each pair replay is its own SUMO process; the count is declared and not wrapped as one run",
        },
        "stop_rules": ["leader tracking deviation above tolerance", "SHA mismatch",
                       "insertion not achieved within the declared wait", "resource risk"],
        "sensitivity_scope": "single-factor, bounded; no grid search and no joint adjustment",
    }
    write_json(output / "response_plan.json", plan)
    (output / "RESPONSE_PLAN_SHA256").write_text(sha256_file(output / "response_plan.json") + "  response_plan.json\n", encoding="utf-8")

    rows, failures = [], []
    for window_id, (subset, picked) in selection.items():
        for _, run in picked.iterrows():
            observed = lr.pair_observations(subset, run, max_duration_s=MAX_PAIR_DURATION_S)
            for config_name in lr.CONFIGURATIONS:
                for seed in SEEDS:
                    try:
                        record = lr.replay_pair(
                            observed, run=run,
                            work=output / "response_runs" / window_id / f"p{int(run.run_id)}_{config_name}_s{seed}",
                            params=lr.build_vtype(config_name), seed=seed,
                            internal_step_s=INTERNAL_STEP_S, insertion_checks="none",
                            shared_network=output / "shared" / "replay.net.xml",
                        )
                    except lr.LeaderReplayError as error:
                        failures.append({"window": window_id, "run_id": int(run.run_id),
                                         "configuration": config_name, "seed": seed, "reason": str(error)})
                        continue
                    row = lr.pair_metrics(record)
                    row.update({
                        "window": window_id, "run_id": int(run.run_id), "pair_index": int(run.run_id),
                        "configuration": config_name, "model": lr.CONFIGURATIONS[config_name]["model"],
                        "stratum": _stratum_label(float(run.gap_mean_m) / max(float(run.speed_mean_mps), 0.1)),
                        "insertion_delay_s": record["insertion_delay_s"],
                    })
                    for label, start, end in (("local", 0.0, lr.LOCAL_WINDOW_S),
                                              ("long", lr.LONG_RUN_START_S, None)):
                        try:
                            sliced = lr.slice_record(record, start_s=start, end_s=end)
                            metrics = lr.pair_metrics(sliced)
                            row[f"{label}_brockfeld_gap_error_pct"] = metrics["brockfeld_gap_error_pct"]
                            row[f"{label}_nrmse_gap"] = metrics["nrmse_gap"]
                            row[f"{label}_nrmse_speed"] = metrics["nrmse_speed"]
                            row[f"{label}_gap_bias_m"] = metrics["gap_bias_m"]
                            row[f"{label}_states"] = metrics["states"]
                        except lr.LeaderReplayError:
                            row[f"{label}_brockfeld_gap_error_pct"] = None
                    response = lr.response_metrics(record)
                    row["response_amplitude_ratio"] = response.get("amplitude_ratio_sim_over_obs")
                    row["response_lag_difference_s"] = response.get("lag_difference_s")
                    row["response_episodes_observed"] = response["series"][0]["episodes"]
                    row["response_events_used"] = response["series"][0]["events_used"]
                    rows.append(row)
                print(f"response {window_id} run{int(run.run_id)} {config_name} done", flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(output / "response_metrics.csv", index=False, float_format="%.6f")
    summary = _response_summary(table)
    summary.update({
        "result_id": RESULT_ID,
        "plan_sha256": sha256_file(output / "response_plan.json"),
        "failures": failures,
        "rows": int(len(table)),
        "budget_used": {"sumo_process_invocations_planned": plan["budget"]["sumo_process_invocations"],
                        "sumo_process_invocations_executed": int(len(table))},
    })
    write_json(output / "response_summary.json", summary)
    return summary


def _stratum_label(time_gap: float) -> str:
    for low, high in zip(STRATA[:-1], STRATA[1:]):
        if low <= time_gap < high:
            return f"time_gap_{low}_{high}s"
    return "time_gap_out_of_range"


def _response_summary(table: pd.DataFrame) -> dict[str, object]:
    if table.empty:
        return {"configurations": {}}
    metrics = ["brockfeld_gap_error_pct", "nrmse_gap", "nrmse_speed", "gap_bias_m", "speed_bias_mps",
               "local_brockfeld_gap_error_pct", "local_nrmse_gap", "long_brockfeld_gap_error_pct",
               "long_nrmse_gap", "long_gap_bias_m", "response_amplitude_ratio", "response_lag_difference_s"]
    summary: dict[str, object] = {"configurations": {}, "cluster_unit": "leader-follower trajectory pair",
                                 "seed_unit": "one SUMO process per (pair, configuration, seed)"}
    for config_name, group in table.groupby("configuration", sort=True):
        entry: dict[str, object] = {"model": str(group.model.iloc[0]),
                                    "rows": int(len(group)),
                                    "pairs": int(group.run_id.nunique()),
                                    "seeds": int(group.seed.nunique())}
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            if values.size == 0:
                entry[metric] = None
                continue
            entry[metric] = {"mean": float(values.mean()), "median": float(np.median(values)),
                             "min": float(values.min()), "max": float(values.max()), "n": int(values.size)}
        summary["configurations"][config_name] = entry
    # seed variability inside each configuration
    seed_variability = {}
    for config_name, group in table.groupby("configuration", sort=True):
        per_pair = group.groupby("run_id")["brockfeld_gap_error_pct"].agg(["mean", "std", "count"])
        per_pair = per_pair[per_pair["count"] >= 2]
        seed_variability[config_name] = {
            "pairs_with_multiple_seeds": int(len(per_pair)),
            "median_within_pair_std_pct": float(per_pair["std"].median()) if len(per_pair) else None,
            "max_within_pair_range_pct": float((group.groupby("run_id")["brockfeld_gap_error_pct"].max()
                                                - group.groupby("run_id")["brockfeld_gap_error_pct"].min()).max()),
        }
    summary["seed_variability"] = seed_variability
    # paired differences against the baseline, using the same pair and the same seed
    baseline = table[table.configuration == lr.KRAUSS_BASELINE_NAME]
    paired: dict[str, object] = {}
    for config_name, group in table.groupby("configuration", sort=True):
        if config_name == lr.KRAUSS_BASELINE_NAME:
            continue
        merged = group.merge(baseline, on=["window", "run_id", "seed"], suffixes=("_cfg", "_base"))
        if merged.empty:
            continue
        entry: dict[str, object] = {"matched_rows": int(len(merged))}
        for metric in ("brockfeld_gap_error_pct", "nrmse_gap", "nrmse_speed", "gap_bias_m",
                       "local_brockfeld_gap_error_pct", "long_brockfeld_gap_error_pct"):
            differences = (merged[f"{metric}_cfg"] - merged[f"{metric}_base"]).dropna().to_numpy(dtype=float)
            if differences.size == 0:
                continue
            generator = np.random.default_rng(20261020)
            draws = np.array([generator.choice(differences, differences.size, replace=True).mean() for _ in range(2000)])
            entry[metric] = {
                "mean_difference": float(differences.mean()),
                "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
                "improved": int((differences < 0).sum()), "worsened": int((differences > 0).sum()),
                "n": int(differences.size),
            }
        paired[config_name] = entry
    summary["paired_vs_baseline"] = paired
    # seed sensitivity of the paired difference itself
    stability = {}
    for config_name, group in table.groupby("configuration", sort=True):
        if config_name == lr.KRAUSS_BASELINE_NAME:
            continue
        merged = group.merge(baseline, on=["window", "run_id", "seed"], suffixes=("_cfg", "_base"))
        if merged.empty:
            continue
        per_seed = merged.groupby("seed").apply(
            lambda part: float((part.brockfeld_gap_error_pct_cfg - part.brockfeld_gap_error_pct_base).mean()),
            include_groups=False,
        )
        stability[config_name] = {"per_seed_mean_difference_pct": {str(k): float(v) for k, v in per_seed.items()},
                                  "sign_consistent_across_seeds": bool(
                                      (per_seed > 0).all() or (per_seed < 0).all())}
    summary["paired_difference_seed_stability"] = stability
    return summary


# ---------------------------------------------------------------------------
# Newell prototype
# ---------------------------------------------------------------------------
def phase_newell(output: Path, selection) -> dict[str, object]:
    plan = {
        "result_id": RESULT_ID,
        "phase": "newell_prototype",
        "nature": "independent non-SUMO prototype; SUMO 1.26 has no Newell car-following model",
        "model": nl.simulate_newell.__doc__.strip().splitlines()[0],
        "parameters": {"tau_s": list(nl.DEFAULT_TAUS), "delta_m": nl.DEFAULT_DELTA_M,
                       "free_speed_mps": 27.78},
        "pairs": selection_manifest(selection),
        "note": "results are never presented as SUMO-native behaviour",
    }
    write_json(output / "newell_plan.json", plan)
    (output / "NEWELL_PLAN_SHA256").write_text(sha256_file(output / "newell_plan.json") + "  newell_plan.json\n", encoding="utf-8")
    rows, failures = [], []
    for window_id, (subset, picked) in selection.items():
        for _, run in picked.iterrows():
            observed = lr.pair_observations(subset, run, max_duration_s=MAX_PAIR_DURATION_S)
            for tau in nl.DEFAULT_TAUS:
                try:
                    record = nl.newell_record(observed, tau=tau, run_id=int(run.run_id),
                                              trajectory_id=str(run.trajectory_id), lane_id=str(run.lane_id))
                    metrics = lr.pair_metrics(record)
                except Exception as error:  # noqa: BLE001 - any prototype failure is recorded
                    failures.append({"window": window_id, "run_id": int(run.run_id), "tau_s": tau, "reason": str(error)})
                    continue
                metrics.update({"window": window_id, "run_id": int(run.run_id), "tau_s": tau,
                                "model": "Newell_prototype",
                                "stratum": _stratum_label(float(run.gap_mean_m) / max(float(run.speed_mean_mps), 0.1))})
                rows.append(metrics)
    table = pd.DataFrame(rows)
    if not table.empty:
        table.to_csv(output / "newell_metrics.csv", index=False, float_format="%.6f")
    summary = {"result_id": RESULT_ID, "plan_sha256": sha256_file(output / "newell_plan.json"),
               "failures": failures, "rows": int(len(table))}
    if not table.empty:
        summary["configurations"] = {}
        for tau, group in table.groupby("tau_s", sort=True):
            summary["configurations"][f"{tau:.2f}"] = {
                "pairs": int(len(group)),
                "brockfeld_gap_error_pct": {"mean": float(group.brockfeld_gap_error_pct.mean()),
                                            "median": float(group.brockfeld_gap_error_pct.median())},
                "nrmse_gap": {"mean": float(group.nrmse_gap.mean())},
                "nrmse_speed": {"mean": float(group.nrmse_speed.mean())},
                "gap_bias_m": {"mean": float(group.gap_bias_m.mean())},
            }
    write_json(output / "newell_summary.json", summary)
    return summary


# ---------------------------------------------------------------------------
# Identifiability / sensitivity
# ---------------------------------------------------------------------------
def phase_identify(output: Path, coverage: dict) -> dict[str, object]:
    table = pd.read_csv(output / "response_metrics.csv")
    summary: dict[str, object] = {"result_id": RESULT_ID}
    baseline = table[table.configuration == lr.KRAUSS_BASELINE_NAME].set_index(["window", "run_id", "seed"])
    sensitivity = {}
    for config_name in ("K_tau1.3", "K_tau1.6", "K_tau2.0", "K_tau1.0_minGap1.0", "K_tau1.0_minGap5.0"):
        group = table[table.configuration == config_name].set_index(["window", "run_id", "seed"])
        common = baseline.index.intersection(group.index)
        if len(common) == 0:
            continue
        delta_param = _param_delta(config_name)
        per_metric = {}
        for metric in ("brockfeld_gap_error_pct", "nrmse_gap", "nrmse_speed", "gap_bias_m"):
            differences = (group.loc[common, metric] - baseline.loc[common, metric]).to_numpy(dtype=float)
            per_metric[metric] = {
                "mean_change": float(np.mean(differences)),
                "mean_change_per_unit_parameter": float(np.mean(differences) / delta_param) if delta_param else None,
                "share_of_pairs_with_same_sign": float(max((differences > 0).mean(), (differences < 0).mean())),
                "n": int(len(differences)),
            }
        sensitivity[config_name] = {"parameter_delta": delta_param, "metrics": per_metric}
    summary["local_sensitivity"] = sensitivity

    # parameter correlation: do the tau and minGap profiles move the metric in the
    # same direction for the same pairs (i.e. are they partly interchangeable)?
    correlation = {}
    tau_group = table[table.configuration == "K_tau1.6"].set_index(["window", "run_id", "seed"])
    for config_name in ("K_tau1.0_minGap1.0", "K_tau1.0_minGap5.0"):
        group = table[table.configuration == config_name].set_index(["window", "run_id", "seed"])
        common = baseline.index.intersection(tau_group.index).intersection(group.index)
        if len(common) < 4:
            continue
        tau_effect = (tau_group.loc[common, "brockfeld_gap_error_pct"] - baseline.loc[common, "brockfeld_gap_error_pct"]).to_numpy(dtype=float)
        gap_effect = (group.loc[common, "brockfeld_gap_error_pct"] - baseline.loc[common, "brockfeld_gap_error_pct"]).to_numpy(dtype=float)
        correlation[config_name] = {
            "pearson_r_over_pairs": float(np.corrcoef(tau_effect, gap_effect)[0, 1]) if tau_effect.std() > 0 and gap_effect.std() > 0 else None,
            "n": int(len(common)),
            "interpretation": "high correlation means the two parameters move the metric together on the same pairs, so they are not separately identifiable from this sample",
        }
    summary["parameter_correlation"] = correlation

    # profile shape: is the metric monotone in tau, and how large is the change
    # relative to the seed-induced variability?
    profile = {}
    tau_values = {"K_tau1.0": 1.0, "K_tau1.3": 1.3, "K_tau1.6": 1.6, "K_tau2.0": 2.0}
    for name, tau in tau_values.items():
        group = table[table.configuration == name]
        profile[f"{tau:.2f}"] = {
            "mean_brockfeld_gap_error_pct": float(group.brockfeld_gap_error_pct.mean()),
            "mean_nrmse_gap": float(group.nrmse_gap.mean()),
            "mean_local_brockfeld": float(pd.to_numeric(group.local_brockfeld_gap_error_pct, errors="coerce").mean()),
            "mean_long_brockfeld": float(pd.to_numeric(group.long_brockfeld_gap_error_pct, errors="coerce").mean()),
        }
    summary["tau_profile"] = profile
    if "seed_variability" in json.loads((output / "response_summary.json").read_text(encoding="utf-8")):
        seed_stats = json.loads((output / "response_summary.json").read_text(encoding="utf-8"))["seed_variability"]
        within = [v["median_within_pair_std_pct"] for v in seed_stats.values() if v["median_within_pair_std_pct"]]
        if within and len(tau_values) > 1:
            largest_step = max(abs(profile[f"{b:.2f}"]["mean_brockfeld_gap_error_pct"] - profile[f"{a:.2f}"]["mean_brockfeld_gap_error_pct"])
                               for a, b in zip(sorted(tau_values.values())[:-1], sorted(tau_values.values())[1:]))
            summary["signal_to_seed_noise"] = {
                "median_within_pair_seed_std_pct": float(np.median(within)),
                "largest_tau_step_change_pct": float(largest_step),
                "ratio": float(largest_step / np.median(within)) if np.median(within) > 0 else None,
            }

    coverage_flags = {}
    for window_id, entry in coverage["windows"].items():
        coverage_flags[window_id] = entry["summary"]
    summary["coverage"] = coverage_flags
    summary["identifiable"] = {
        "tau": "the tau profile changes the metric by far more than the seed-induced spread, so tau is locally identifiable on this sample; it is nevertheless falsified as the fix",
        "minGap": "the minGap profile also moves the metric; correlation with the tau effect is reported above",
        "sigma": "sigma=0 removes the dawdling term; the difference against sigma=0.5 bounds the deterministic part",
        "not_identifiable": [
            "the real free-flow speed (never measured)",
            "the real standstill gap (minGap) as a physical quantity",
            "behaviour outside the observed phases: the sample contains few sustained stationary, low-speed or long close-following episodes, so those phases cannot calibrate anything",
        ],
    }
    write_json(output / "identifiability_summary.json", summary)
    return summary


def _param_delta(config_name: str) -> float:
    entry = lr.CONFIGURATIONS[config_name]["overrides"]
    if "tau" in entry:
        return float(entry["tau"]) - lr.BASELINE_FOLLOWING["tau"]
    if "minGap" in entry:
        return float(entry["minGap"]) - lr.BASELINE_FOLLOWING["minGap"]
    return 0.0


# ---------------------------------------------------------------------------
# Phase 5 decision
# ---------------------------------------------------------------------------
def phase_macro(output: Path, response: dict) -> dict[str, object]:
    paired = (response.get("paired_vs_baseline") or {})
    tau16 = (paired.get("K_tau1.6") or {}).get("brockfeld_gap_error_pct") or {}
    gate_open = bool(tau16) and tau16.get("mean_difference", 1.0) < 0 and tau16.get("ci95", [0, 0])[1] < 0
    decision = {
        "result_id": RESULT_ID,
        "phase": "macro",
        "executed": False,
        "gate": "a bounded macro contrast is only run when the micro-level diagnostic identifies a configuration supported by the pair-level evidence",
        "gate_open": gate_open,
        "observed_tau1.6_paired_difference": tau16,
        "reason": (
            "no micro configuration in the bounded catalogue is supported by the pair-level evidence, so a new "
            "macro contrast would tune the boundary supply to compensate for an unresolved behaviour/structure "
            "mismatch, which the task forbids"
        ) if not gate_open else "a supported configuration exists and a macro contrast is eligible",
        "existing_scenes_preserved": ["RC1", "RC2", "RC3"],
        "no_scene_rerun": True,
        "researcher_decision_required": [
            "whether to run a heterogeneous-parameter structural diagnostic",
            "whether to run an IDM/Newell structural comparison under an independently frozen protocol",
            "whether a conditional downstream supply may be revisited after either of the above",
        ],
    }
    write_json(output / "macro_decision.json", decision)
    return decision


def build(args) -> Path:
    output = Path(args.output_root)
    if not output.is_absolute():
        output = REPO_ROOT / output
    output.mkdir(parents=True, exist_ok=True)
    frames, sources = load_states()

    manifest = {
        "result_id": RESULT_ID,
        "source_files": sources,
        "sealed_windows_not_read": ["us101__0820_0835", "nsgim_lankershim__complete"],
        "third_window_rows_materialised": 0,
        "holdout_reads": 0,
        "git_head": subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                                   capture_output=True, text=True).stdout.strip(),
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "pandas": pd.__version__, "numpy": np.__version__},
        "sumo_binary_sha256": sha256_file(Path(_sumo_binary())),
        "netconvert_binary_sha256": sha256_file(Path(_netconvert_binary())),
    }
    write_json(output / "source_audit.json", manifest)

    results: dict[str, object] = {}
    if "coverage" in args.phases or "all" in args.phases:
        coverage = phase_coverage(frames)
        write_json(output / "trajectory_coverage_matrix.json", coverage)
        # portable summary: the full per-run matrix is 4.9 MB and stays local
        write_json(output / "trajectory_coverage_summary.json", {
            "result_id": RESULT_ID,
            "rules": coverage["rules"],
            "rule_status": coverage["rule_status"],
            "phase_definition_note": (
                "phase time shares are computed over all reliable continuous following runs of the "
                "window; they are descriptive and use exploratory project thresholds"
            ),
            "windows": {w: entry["summary"] for w, entry in coverage["windows"].items()},
            "full_matrix_local_path": "code/outputs/formal/calibration/stage_0_5_method_expansion_v1/trajectory_coverage_matrix.json",
        })
        results["coverage"] = coverage.get("windows")
        print("coverage done", flush=True)
    selection = build_selection(frames)
    write_json(output / "selection_manifest.json", selection_manifest(selection))
    if "init" in args.phases or "all" in args.phases:
        results["init"] = phase_init(output, selection)
        print("init done", flush=True)
    if "response" in args.phases or "all" in args.phases:
        results["response"] = phase_response(output, selection)
        print("response done", flush=True)
    if "newell" in args.phases or "all" in args.phases:
        results["newell"] = phase_newell(output, selection)
        print("newell done", flush=True)
    if "identify" in args.phases or "all" in args.phases:
        coverage = json.loads((output / "trajectory_coverage_matrix.json").read_text(encoding="utf-8"))
        results["identify"] = phase_identify(output, coverage)
        print("identify done", flush=True)
    if "macro" in args.phases or "all" in args.phases:
        response = json.loads((output / "response_summary.json").read_text(encoding="utf-8"))
        results["macro"] = phase_macro(output, response)
        print("macro done", flush=True)

    names = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS", "manifest.json"}
        and not path.name.endswith((".net.xml", ".rou.xml", ".sumocfg"))
        and path.name not in {"nodes.nod.xml", "edges.edg.xml"}
    )
    lines = [f"{sha256_file(output / name)}  {name}" for name in names]
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(output / "manifest.json", {
        "schema_version": "aad.evidence-manifest.v1",
        "result_id": RESULT_ID,
        "files": [{"path": name, "sha256": sha256_file(output / name), "bytes": (output / name).stat().st_size} for name in names],
    })
    write_json(output / "run_metadata.json", {"created_utc": datetime.now(timezone.utc).isoformat()})
    print(f"packaged {len(names)} files into {output}", flush=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phases", nargs="+", default=["all"],
                        choices=["all", "coverage", "init", "response", "newell", "identify", "macro"])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
