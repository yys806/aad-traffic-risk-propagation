"""Stage 0.5 method diagnostics: jam-definition sensitivity, null model, leader replay.

Phase A (no SUMO): threshold sensitivity and a Saberi-style spatial null model.
Phase B (bounded SUMO): leader-trajectory replay of the frozen Krauss baseline
against one pre-declared ``tau = 1.6 s`` candidate, on the same frozen sample.

A plan with the sample, configurations, seeds, predictions, budget and stop rules
is written and SHA-bound before the first simulation step.
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

from riskprop import stage_0_5_jam_definition as jd  # noqa: E402
from riskprop import stage_0_5_leader_replay as lr  # noqa: E402
from riskprop import stage_0_5_trajectory_reconstruction as tr  # noqa: E402
from riskprop.stage_0_5_sumo import _netconvert_binary, _sumo_binary  # noqa: E402

RESULT_ID = "RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1"
STATES_ROOT = "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
DEFAULT_OUTPUT = "code/outputs/formal/calibration/stage_0_5_method_diagnostics_v1"

# Frozen Phase-A design
PERMUTATIONS = 1000
NULL_SEED = 20261031
GRID = dict(y_step_m=50.0, t_step_s=30.0)

# Frozen Phase-B design
PAIRS_PER_WINDOW = 12
MIN_PAIR_DURATION_S = 8.0
MAX_PAIR_DURATION_S = 25.0
TAUS = (1.0, lr.CANDIDATE_TAU_S)
REPLAY_SEEDS = {1.0: 20261101, lr.CANDIDATE_TAU_S: 20261102}
INTERNAL_STEP_S = 0.05
RECORD_STEP_S = 0.1
LEADER_TRACKING_TOLERANCE_M = 0.25
#: Secondary pass only: settle interval excluded after a clamped initial speed.
SECONDARY_SETTLE_S = 1.0
#: Observed time-gap strata (gap / speed), declared before the replay.
TIME_GAP_STRATA = ((0.0, 1.0), (1.0, 1.5), (1.5, 10.0))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def stratum_of(time_gap: float) -> str:
    for low, high in TIME_GAP_STRATA:
        if low <= time_gap < high:
            return f"time_gap_{low:.1f}_{high:.1f}s"
    return "time_gap_out_of_range"


def phase_a(states: dict[str, pd.DataFrame]) -> dict[str, object]:
    rules = jd.rule_catalogue()
    results: dict[str, object] = {"rules": rules, "windows": {}}
    for window_id, frame in states.items():
        window = tr.CALIBRATION_WINDOWS[window_id]
        grid = jd.cell_speed_grid(frame, window=window, **GRID)
        per_rule = {}
        for rule in rules:
            mask = jd.congestion_mask(grid, rule)
            description = jd.describe_mask(grid, mask, t_step_s=GRID["t_step_s"], y_step_m=GRID["y_step_m"])
            null = jd.null_model(
                grid, mask, permutations=PERMUTATIONS, seed=NULL_SEED,
                t_step_s=GRID["t_step_s"], y_step_m=GRID["y_step_m"],
            )
            per_rule[rule["name"]] = {
                "description": description,
                "null": null["null"],
                "exceedance_largest_cells": null["null"].get("largest_cells", {}).get("exceedance"),
            }
        results["windows"][window_id] = {
            "grid_cells": [int(grid.shape[0]), int(grid.shape[1])],
            "missing_cells": int(grid.isna().to_numpy().sum()),
            "per_rule": per_rule,
        }
    # robustness summary: does the propagation direction / first position agree?
    robustness = {}
    for window_id, entry in results["windows"].items():
        directions = {name: value["description"]["growth"] for name, value in entry["per_rule"].items()}
        first_positions = {name: value["description"]["largest_first_position_m"] for name, value in entry["per_rule"].items()}
        upstream = sum(1 for direction in directions.values() if direction == "upstream")
        robustness[window_id] = {
            "growth_by_rule": directions,
            "rules_with_upstream_growth": upstream,
            "rules_total": len(directions),
            "largest_first_position_by_rule": first_positions,
            "direction_stable": upstream == len(directions),
        }
    results["robustness"] = robustness
    results["design"] = {
        "permutations": PERMUTATIONS, "null_seed": NULL_SEED, "grid": GRID,
        "note": "permutation count, seed and grid are project implementation choices, not paper values",
    }
    return results


def freeze_phase_b(states: dict[str, pd.DataFrame]) -> tuple[dict[str, object], dict[str, tuple]]:
    selections: dict[str, tuple] = {}
    plan_samples = {}
    for window_id, frame in states.items():
        runs, subset = lr.prepare_pairs(frame, window=tr.CALIBRATION_WINDOWS[window_id])
        selected = lr.select_pairs(runs, count=PAIRS_PER_WINDOW, min_duration_s=MIN_PAIR_DURATION_S, max_duration_s=MAX_PAIR_DURATION_S)
        selections[window_id] = (subset, selected)
        plan_samples[window_id] = [
            {
                "trajectory_id": str(row.trajectory_id),
                "leader_trajectory_id": str(row.leader_trajectory_id),
                "lane_id": str(row.lane_id),
                "start_s": float(row.start_s),
                "duration_s": float(row.duration_s),
            }
            for _, row in selected.iterrows()
        ]
    plan = {
        "result_id": RESULT_ID,
        "version": lr.VERSION,
        "mode": "bounded leader-replay diagnostics; no parameter search; no Gate mutation",
        "clone_shape": "naturalistic US-101 following with lane changes and varying drivers",
        "configurations": {f"{tau:.2f}": lr.configuration(tau) for tau in TAUS},
        "only_difference": "tau (minGap, accel, decel, sigma, maxSpeed, actionStepLength all frozen)",
        "seeds": {f"{tau:.2f}": REPLAY_SEEDS[tau] for tau in TAUS},
        "internal_step_s": INTERNAL_STEP_S,
        "record_step_s": RECORD_STEP_S,
        "leader_tracking_tolerance_m": LEADER_TRACKING_TOLERANCE_M,
        "pairs_per_window": PAIRS_PER_WINDOW,
        "min_pair_duration_s": MIN_PAIR_DURATION_S,
        "max_pair_duration_s": MAX_PAIR_DURATION_S,
        "time_gap_strata": [list(item) for item in TIME_GAP_STRATA],
        "secondary_pass": {
            "trigger": "primary insertion rejected by SUMO's Krauss safety envelope",
            "policy": f"clamp the initial speed to 0.95x safe speed and exclude the first {SECONDARY_SETTLE_S} s",
            "reporting": "reported separately per pair; never pooled with the primary pass",
        },
        "sample": plan_samples,
        "metrics": [
            "brockfeld_gap_error_pct (Brockfeld et al. 2004 Eq. 2)",
            "nrmse_gap and nrmse_speed (Schrader et al. 2024 Eqs. 5-6); acceleration withheld",
            "gap/speed bias and MAE",
            "observed vs simulated time headway",
            "closing speed distribution and sign",
        ],
        "predictions": {
            "baseline_tau_1.0": "systematically keeps a larger gap than observed where the observed time gap is short, because SUMO's Krauss enforces v*tau + minGap",
            "candidate_tau_1.6": "reduces the gap bias for pairs whose observed time gap exceeds about 1.5 s, and increases it for pairs observed following more closely",
            "falsifier_of_candidate": "no improvement in either window, or improvement confined to a single window",
        },
        "interpretation_rules": [
            "candidate improves gap error in both windows with no stable worsening of the core metrics -> the behaviour-parameter hypothesis gains support",
            "gap improves but speed worsens, or the effect is single-window -> report indicator conflict / state heterogeneity",
            "both configurations show systematic error -> inspect model structure, replay implementation and data quality rather than scanning parameters",
        ],
        "insertion_policy": (
            "the observed initial speed is inserted as-is; if SUMO's Krauss insertion safety check "
            "rejects that state the pair/configuration is recorded as a representability finding "
            "(the observed initial state is not representable under the model's own safety envelope) "
            "instead of being masked by clamping the initial speed, because a clamped initial speed "
            "changes the response being measured"
        ),
        "stop_rules": [
            "leader tracking deviation above tolerance on any pair stops the batch",
            "SHA mismatch, insertion failure or missing observed leader rows stops the batch",
            "no tau search, no joint minGap adjustment, no P2-based selection of pairs",
        ],
        "budget": {
            "sumo_process_invocations": 2 * PAIRS_PER_WINDOW * len(TAUS),
            "windows": 2,
            "pairs_per_window": PAIRS_PER_WINDOW,
            "configurations": list(TAUS),
            "note": (
                "each leader-follower pair is replayed in its own SUMO process; the invocation count is declared "
                "explicitly and is not wrapped as a single run. These are micro-runs of at most 25 s simulated time. "
                "This budget is separate from the sealed Stage 0.5 closure repeats and from the RC diagnostic budget."
            ),
        },
        "reserved_runs_not_used": {
            "RES-STAGE-0.5-FINAL-CLOSURE-V1": "FR1/FR2 independent-seed repeats remain reserved to the closure candidate protocol",
            "RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1": "RC1r/RC2r reserved repeats remain unused and are not transferred",
        },
        "third_window_or_holdout_access": False,
        "sumo_binary_sha256": sha256_file(Path(_sumo_binary())),
        "netconvert_binary_sha256": sha256_file(Path(_netconvert_binary())),
        "scientific_claim_eligible": False,
        "gate_status": "pending_simulation_sample",
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__},
        "git_head": subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    }
    return plan, selections


def phase_b(output: Path, states: dict[str, pd.DataFrame]) -> dict[str, object]:
    plan, selections = freeze_phase_b(states)
    write_json(output / "replay_plan.json", plan)
    (output / "REPLAY_PLAN_SHA256").write_text(
        sha256_file(output / "replay_plan.json") + "  replay_plan.json\n", encoding="utf-8"
    )
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for window_id, (subset, selected) in selections.items():
        for index, run in selected.iterrows():
            try:
                observed = lr.pair_observations(subset, run, max_duration_s=MAX_PAIR_DURATION_S)
            except lr.LeaderReplayError as error:
                failures.append({"window": window_id, "pair_index": int(index), "trajectory_id": str(run.trajectory_id), "reason": str(error)})
                continue
            for tau in TAUS:
                record = None
                try:
                    record = lr.replay_pair(
                        observed, run=run,
                        work=output / "runs" / window_id / f"pair{index:02d}_tau{tau:.1f}",
                        params=lr.configuration(tau), seed=REPLAY_SEEDS[tau],
                        internal_step_s=INTERNAL_STEP_S, record_step_s=RECORD_STEP_S,
                    )
                except lr.LeaderReplayError as error:
                    failures.append({"window": window_id, "pair_index": int(index), "trajectory_id": str(run.trajectory_id), "tau_s": tau, "reason": str(error)})
                    if "insertion_failed" not in str(error):
                        continue
                if record is None:
                    # declared secondary pass: clamp the initial speed so that the pair can
                    # be initialised at all, and exclude a fixed settling interval
                    try:
                        record = lr.replay_pair(
                            observed, run=run,
                            work=output / "runs_secondary" / window_id / f"pair{index:02d}_tau{tau:.1f}",
                            params=lr.configuration(tau), seed=REPLAY_SEEDS[tau],
                            internal_step_s=INTERNAL_STEP_S, record_step_s=RECORD_STEP_S,
                            clamp_initial_speed=True,
                        )
                        metrics = lr.pair_metrics(record, settle_s=SECONDARY_SETTLE_S)
                        metrics["pass"] = "secondary_clamped_initial_speed"
                    except lr.LeaderReplayError as error:
                        failures.append({"window": window_id, "pair_index": int(index), "trajectory_id": str(run.trajectory_id), "tau_s": tau, "pass": "secondary", "reason": str(error)})
                        continue
                else:
                    metrics = lr.pair_metrics(record)
                    metrics["pass"] = "primary_exact_initial_state"
                metrics["window"] = window_id
                metrics["pair_index"] = int(index)
                metrics["stratum"] = stratum_of(metrics["observed_time_gap_mean_s"])
                metrics["leader_tracking_ok"] = bool(metrics["leader_target_max_abs_deviation_m"] <= LEADER_TRACKING_TOLERANCE_M)
                metrics["initial_speed_offset_mps"] = float(record["initial_speed_offset_mps"])
                rows.append(metrics)
                print(
                    f"{window_id} pair{index:02d} tau{tau:.1f} brockfeld={metrics['brockfeld_gap_error_pct']:.2f}% "
                    f"nrmse_gap={metrics['nrmse_gap']:.4f} track={metrics['leader_target_max_abs_deviation_m']:.3f}",
                    flush=True,
                )
    tracking_failures = [row for row in rows if not row["leader_tracking_ok"]]
    summary = lr.summarise(rows)
    summary["per_window"] = {}
    for window_id in states:
        window_rows = [row for row in rows if row["window"] == window_id]
        if window_rows:
            summary["per_window"][window_id] = lr.summarise(window_rows)
    summary["per_stratum"] = {}
    frame = pd.DataFrame(rows)
    if not frame.empty:
        for stratum, group in frame.groupby("stratum", sort=True):
            summary["per_stratum"][stratum] = lr.summarise(group.to_dict(orient="records"))
    distinct_pairs = len({(row["window"], row["pair_index"]) for row in rows})
    summary["pairs_selected"] = int(2 * PAIRS_PER_WINDOW)
    summary["distinct_pairs_replayed"] = int(distinct_pairs)
    summary["pair_config_combinations_replayed"] = int(len(rows))
    insertion_rejections = [row for row in failures if "insertion_failed" in row.get("reason", "")]
    summary["insertion_rejections"] = insertion_rejections
    summary["insertion_rejection_count"] = len(insertion_rejections)
    summary["insertion_rejection_share"] = float(len(insertion_rejections) / max(2 * PAIRS_PER_WINDOW * len(TAUS), 1))
    summary["failures"] = failures
    summary["passes"] = {}
    if not pd.DataFrame(rows).empty:
        for pass_name, group in pd.DataFrame(rows).groupby("pass", sort=True):
            summary["passes"][pass_name] = lr.summarise(group.to_dict(orient="records"))
    summary["leader_tracking_failures"] = tracking_failures
    summary["leader_tracking_tolerance_m"] = LEADER_TRACKING_TOLERANCE_M
    summary["budget_used"] = {
        "sumo_process_invocations_planned": plan["budget"]["sumo_process_invocations"],
        "sumo_process_invocations_executed": int(len(rows)),
    }
    return summary


def build(args: argparse.Namespace) -> Path:
    output = Path(args.output_root)
    if not output.is_absolute():
        output = REPO_ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    states: dict[str, pd.DataFrame] = {}
    sources = {}
    for window_id in tr.CALIBRATION_WINDOWS:
        path = REPO_ROOT / STATES_ROOT / f"ngsim_{window_id}.parquet"
        if not path.is_file():
            raise SystemExit(f"missing sealed calibration state: {path}")
        sources[window_id] = {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": sha256_file(path)}
        states[window_id] = tr.load_calibration_states(str(path), window_id)

    if args.phase in ("A", "both"):
        results = phase_a(states)
        results["result_id"] = RESULT_ID
        results["source_files"] = sources
        write_json(output / "jam_definition_sensitivity.json", results)
        rules_frame = pd.DataFrame(
            [
                {
                    "window": window_id,
                    "rule": rule_name,
                    "growth": value["description"]["growth"],
                    "largest_cells": value["description"]["largest_cells"],
                    "largest_duration_s": value["description"]["largest_duration_s"],
                    "largest_first_time_s": value["description"]["largest_first_time_s"],
                    "first_position_low_m": (value["description"]["largest_first_position_m"] or [None, None])[0],
                    "first_position_high_m": (value["description"]["largest_first_position_m"] or [None, None])[1],
                    "backward_speed_mps": value["description"]["backward_speed_mps"],
                    "slow_cell_fraction": value["description"]["slow_cell_fraction"],
                    "null_largest_cells_mean": value["null"].get("largest_cells", {}).get("null_mean"),
                    "null_largest_cells_p95": value["null"].get("largest_cells", {}).get("null_p95"),
                    "null_exceedance_largest_cells": value["null"].get("largest_cells", {}).get("exceedance"),
                }
                for window_id, entry in results["windows"].items()
                for rule_name, value in entry["per_rule"].items()
            ]
        )
        rules_frame.to_csv(output / "jam_definition_rules.csv", index=False, float_format="%.6f")
        print("phase A written", flush=True)

    if args.phase in ("B", "both"):
        summary = phase_b(output, states)
        summary["result_id"] = RESULT_ID
        summary["source_files"] = sources
        write_json(output / "replay_summary.json", summary)
        rows = summary.get("failures") or []
        print("phase B written; distinct_pairs=%s combos=%s failures=%d insertion_rejections=%d" % (summary.get("distinct_pairs_replayed"), summary.get("pair_config_combinations_replayed"), len(rows), summary.get("insertion_rejection_count")), flush=True)

    # Phase C is gated on Phase B supporting the behaviour candidate. The pre-declared
    # rule was not met, so C is recorded as not executed with the reason.
    replay = json.loads((output / "replay_summary.json").read_text(encoding="utf-8")) if (output / "replay_summary.json").is_file() else {}
    paired = (replay.get("paired_difference") or {})
    gap = paired.get("brockfeld_gap_error_pct") or {}
    phases_supported = bool(gap) and gap.get("mean_difference", 1.0) < 0 and gap.get("ci95", [0, 0])[1] < 0
    write_json(output / "phase_c_decision.json", {
        "result_id": RESULT_ID,
        "phase_c_executed": False,
        "gate_condition": "phase B must support the behaviour candidate before a conditional downstream supply is constructed",
        "observed_paired_gap_error_difference": gap,
        "gate_satisfied": phases_supported,
        "reason": (
            "the pre-declared interpretation rule was not met: the candidate tau=1.6 does not reduce the gap error "
            "in both windows and it increases the gap bias for every paired sample, so the behaviour-parameter "
            "hypothesis is not supported and a new conditional supply would mask a behaviour-model discrepancy"
        ) if not phases_supported else "candidate supported; phase C would be eligible",
        "existing_scenes_preserved": ["RC1", "RC2", "RC3"],
        "no_rerun_of_existing_runs": True,
        "new_supply_candidate_created": False,
        "researcher_decision_required": [
            "whether to run a heterogeneous-tau structural diagnostic (observation-driven per-pair tau, no search)",
            "whether to run an IDM comparison under the same leader replay and metrics",
            "whether a conditional downstream supply may be revisited after either of the above",
        ],
    })
    write_json(output / "budget_ledger_audit.json", {
        "result_id": RESULT_ID,
        "ledgers": {
            "RES-STAGE-0.5-FINAL-CLOSURE-V1": {
                "path": "evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/candidate_experiment_plan.json",
                "granted": "at most 5 runs in that task: <=3 construction, >=2 reserved independent-seed repeats",
                "executed": ["FC1 (construction)", "FC2 (construction)"],
                "reserved_unused": ["FR1", "FR2"],
                "status": "reserved repeats remain with the closure candidate protocol and are not transferred",
            },
            "RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1": {
                "path": "evidence/results/RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1/scene_diagnostic_plan.json",
                "granted": "3 construction runs plus 2 reserved repeats under that task's own authorisation",
                "executed": ["RC1", "RC2", "RC3"],
                "reserved_unused": ["RC1r", "RC2r"],
                "status": "unused; not transferred; the batch stopped under its own pre-declared rule",
            },
            "this_task": {
                "granted": "48 micro-runs declared in replay_plan.json (2 windows x 12 pairs x 2 configurations)",
                "executed": replay.get("pair_config_combinations_replayed"),
                "insertion_rejections": replay.get("insertion_rejection_count"),
            },
        },
        "no_budget_transfer": True,
        "date_discrepancy": {
            "finding": "documents from commit afdc3d0 were labelled 2026-10-21 but the commit timestamp is 2026-10-20 20:20:17 +08:00 and the local timezone is +08:00",
            "cause": "authoring date error, not a timezone artefact: the work was executed on 2026-10-20 (Asia/Shanghai)",
            "action": "explicit erratum recorded in the documents and in AI_CONTEXT; committed text and filenames preserved",
        },
    })

    names = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS", "manifest.json"}
        and not path.name.endswith((".net.xml", ".rou.xml", ".sumocfg"))
        and "nodes.nod.xml" not in path.name and "edges.edg.xml" not in path.name
    )
    lines = [f"{sha256_file(output / name)}  {name}" for name in names]
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(output / "manifest.json", {
        "schema_version": "aad.evidence-manifest.v1",
        "result_id": RESULT_ID,
        "files": [{"path": name, "sha256": sha256_file(output / name), "bytes": (output / name).stat().st_size} for name in names],
    })
    write_json(output / "run_metadata.json", {"created_utc": datetime.now(timezone.utc).isoformat(),
                                              "note": "timestamp kept outside the frozen plans so the plans are byte-reproducible"})
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("A", "B", "both"), default="both")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
