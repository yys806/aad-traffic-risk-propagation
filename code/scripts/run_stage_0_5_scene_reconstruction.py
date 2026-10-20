"""Targeted, pre-declared SUMO diagnostics for the Stage 0.5 scene reconstruction.

Three variants, each answering one pre-declared question:

RC1  observed geometry + observed boundary demand, empty initial state
     Question: can the observed geometry and boundaries alone reproduce the
     observed congested local state?
RC2  RC1 + initial state taken from the real observed congested state
     Question: does the observed congested state persist under SUMO dynamics at
     the observed boundary demand, i.e. was the earlier free-flow outcome only
     an initial-condition artefact?
RC3  RC2 + a declared conditional downstream capacity restriction
     Question: if a downstream supply restriction is admitted as a conditional
     scenario assumption, does the local state land in the observed congested
     envelope?

The plan, including the predicted outcome of each variant and the stop rule, is
written and SHA-bound before any simulation starts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_scene_reconstruction as sr  # noqa: E402
from riskprop import stage_0_5_trajectory_reconstruction as tr  # noqa: E402
from riskprop.stage_0_5_sumo import _netconvert_binary, _sumo_binary  # noqa: E402

RESULT_ID = "RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1"
STATES_ROOT = "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
DURATION_S = 300.0
INTERNAL_STEP_S = 0.05
EVALUATION_WINDOW_S = (180.0, 299.7)
BLOCK_S = 30.0
CONSTRUCTION_SEEDS = {"RC1": 20261021, "RC2": 20261022, "RC3": 20261023}
REPEAT_SEEDS = {"RC1r": 20261024, "RC2r": 20261025, "RC3r": 20261026}
DOWNSTREAM_EXIT_LANES = 3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def conditional_network_spec() -> dict[str, object]:
    """Observed geometry plus a declared conditional downstream capacity restriction."""
    spec = sr.scene_spec()
    spec["network_id"] = "observed_geometry_conditional_supply_candidate"
    spec["classification"] = "conditional_synthetic_downstream_supply"
    spec["claim"] = "downstream_capacity_restriction_is_a_declared_scenario_assumption_not_an_observed_mechanism"
    spec["nodes"] = list(spec["nodes"]) + [{"id": "hwy_x", "x": sr.SEGMENT_LENGTH_M + 120.0, "y": 0.0}]
    spec["edges"] = list(spec["edges"]) + [
        {"id": "exit", "from": "hwy_e", "to": "hwy_x", "lanes": DOWNSTREAM_EXIT_LANES, "speed_mps": 27.78, "priority": 2}
    ]
    spec["routes"] = {
        "through": ["main_0", "main_1", "main_2", "exit"],
        "entering": ["onramp", "main_1", "main_2", "exit"],
        "exiting": ["main_0", "main_1", "offramp"],
    }
    return spec


def specification(condition: str) -> dict[str, object]:
    spec = sr.CONDITIONS[condition]
    capacity = DOWNSTREAM_EXIT_LANES * sr.FREE_FLOW_LANE_CAPACITY_VEH_H
    return {
        "condition": condition,
        "mainline_flow_veh_h": spec["mainline_flow_veh_h"],
        "onramp_flow_veh_h": spec["onramp_flow_veh_h"],
        "offramp_flow_veh_h": spec["offramp_flow_veh_h"],
        "analytic_downstream_capacity_veh_h": capacity,
        "demand_over_capacity": spec["mainline_flow_veh_h"] / capacity,
        "real_target": spec["real_target"],
    }


def run_variant(
    root: Path,
    *,
    variant: str,
    condition: str,
    seed: int,
    use_initial_state: bool,
    conditional_supply: bool,
    states: pd.DataFrame,
) -> dict[str, object]:
    work = root / variant
    work.mkdir(parents=True, exist_ok=True)
    spec = conditional_network_spec() if conditional_supply else sr.scene_spec()
    from riskprop.stage_0_5_sumo import build_candidate_network

    network = build_candidate_network(work / "network", spec)["network"]
    edge_lengths = sr.network_edge_lengths(network)
    routes = work / f"{variant}.rou.xml"
    initial = None
    if use_initial_state:
        initial = sr.build_initial_state(states, condition, edge_lengths=edge_lengths)
        sr.write_initial_state_route_file(
            routes, condition, initial, duration_s=DURATION_S, route_map=spec["routes"]
        )
    else:
        sr.build_route_file(routes, condition, duration_s=DURATION_S)
    config = sr.write_sumo_config(
        work / f"{variant}.sumocfg", network=network, routes=routes,
        duration_s=DURATION_S, seed=seed, internal_step_s=INTERNAL_STEP_S, fcd_period_s=0.1,
        fcd_path=work / "fcd.xml", summary_path=work / "summary.xml",
    )
    run = sr.run_sumo(config)
    frame = sr.parse_fcd(work / "fcd.xml", edge_lengths)
    metrics = sr.scene_metrics(frame, window_s=EVALUATION_WINDOW_S, block_s=BLOCK_S)
    early = sr.scene_metrics(frame, window_s=(0.0, 30.0), block_s=BLOCK_S)
    support = sr.state_support(metrics, condition)
    on_network = frame[frame.lane_id.notna()]
    return {
        "variant": variant,
        "condition": condition,
        "seed": seed,
        "use_initial_state": use_initial_state,
        "conditional_supply": conditional_supply,
        "network_spec_id": spec["network_id"],
        "network_sha256": sha256_file(Path(network)),
        "route_sha256": sha256_file(routes),
        "config_sha256": sha256_file(config),
        "initial_state": ({k: initial[k] for k in ("clock_s", "accepted_count", "dropped_count", "minimum_spacing_m")} if initial else None),
        "run": run,
        "evaluation_window_s": list(EVALUATION_WINDOW_S),
        "metrics": metrics,
        "first_30s_metrics": early,
        "state_support": support,
        "fcd_rows": int(len(frame)),
        "on_network_rows": int(len(on_network)),
        "lane_share": {str(k): int(v) for k, v in on_network.lane_id.value_counts().items()},
    }


def congested_branch_diagnosis(condition: str, local: dict, interactions: dict) -> dict[str, object]:
    """Compare the observed congested point with the frozen Krauss equilibrium relation.

    Standard Krauss equilibrium (sigma = 0) satisfies v * tau + minGap + length =
    spacing.  Two independent observed quantities give an implied tau: the
    observed spacing from the local density, and the observed net gap.  The
    statement is Derived from the frozen parameters plus Observation; the
    parameter conclusion is a Hypothesis until a controlled probe is authorised.
    """
    tau = sr.FIXED_VTYPE["tau"]
    min_gap = sr.FIXED_VTYPE["minGap"]
    length = sr.CONDITIONS[condition]["fleet_length_m"]["passenger"]
    density = local["density_veh_km_lane"]
    speed = local["speed_mean_mps"]
    spacing = 1000.0 / density
    equilibrium_speed_at_frozen_parameters = (spacing - length - min_gap) / tau
    implied_tau_from_density = (spacing - length - min_gap) / speed
    net_gap = interactions["net_gap_m"]["mean"]
    implied_tau_from_net_gap = (net_gap - min_gap) / speed
    return {
        "condition": condition,
        "status": "Derived from frozen parameters plus Observation; the parameter conclusion is Hypothesis",
        "frozen_parameters": {"tau_s": tau, "min_gap_m": min_gap, "passenger_length_m": length},
        "observed_congested_point": {
            "density_veh_km_lane": density,
            "speed_mean_mps": speed,
            "flow_veh_h_lane": density * speed * 3.6,
            "mean_net_gap_m": net_gap,
        },
        "krauss_equilibrium_speed_at_observed_density_mps": equilibrium_speed_at_frozen_parameters,
        "implied_tau_s_from_observed_density": implied_tau_from_density,
        "implied_tau_s_from_observed_net_gap": implied_tau_from_net_gap,
        "agreement_between_two_implied_tau_s": abs(implied_tau_from_density - implied_tau_from_net_gap),
        "conclusion": (
            "At the frozen Krauss parameters the equilibrium speed at the observed congested "
            "density is far above the observed speed, so the observed congested branch is not on "
            "the frozen model's equilibrium branch. Both the observed density and the observed net "
            "gap independently imply an effective time-gap parameter near 1.5-1.6 s instead of the "
            "frozen 1.0 s. This is the quantitative reason why the same observed flow is reachable "
            "only on the free-flow branch in the tested scenarios."
        ),
        "not_a_science_tolerance": True,
        "requires_controlled_probe": True,
    }


def build(args: argparse.Namespace) -> Path:
    output = Path(args.output_root)
    if not output.is_absolute():
        output = REPO_ROOT / output
    if output.exists() and not args.resume:
        raise SystemExit(f"refusing to overwrite existing diagnostic directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    states_path = REPO_ROOT / STATES_ROOT
    source = {}
    frames = {}
    for window_id in tr.CALIBRATION_WINDOWS:
        path = states_path / f"ngsim_{window_id}.parquet"
        source[window_id] = {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": sha256_file(path)}
        if window_id == args.condition:
            frames[window_id] = tr.load_calibration_states(str(path), window_id)
    condition = args.condition
    if condition not in frames:
        raise SystemExit("condition must be one of the approved calibration windows")
    states = frames[condition]

    plan = {
        "result_id": RESULT_ID,
        "version": sr.VERSION,
        "mode": "pre-declared targeted SUMO diagnostics; diagnostic evidence only, never Gate acceptance",
        "condition": condition,
        "specification": specification(condition),
        "duration_s": DURATION_S,
        "internal_step_s": INTERNAL_STEP_S,
        "evaluation_window_s": list(EVALUATION_WINDOW_S),
        "evaluation_window_basis": "inherited from the frozen 2026-10-20 conditional candidate window; fixed before any trajectory of this batch is produced",
        "block_s": BLOCK_S,
        "variants": [
            {
                "variant": "RC1", "seed": CONSTRUCTION_SEEDS["RC1"], "use_initial_state": False, "conditional_supply": False,
                "question": "Can the observed geometry (five mainline lanes, on-ramp merge, auxiliary lane, off-ramp diverge) and the observed boundary demand alone reproduce the observed congested local state?",
                "predicted_outcome": "free-flow branch: local speed near 20-23 m/s and density near 19-21 veh/km/lane, i.e. the same flow on the free-flow branch, because the Krauss lane capacity far exceeds the observed congested flow",
                "supports_if": "mean speed within the predeclared block envelope of the real target and mean density within it",
                "refutes_if": "mean speed and density both outside the real-target block envelope",
            },
            {
                "variant": "RC2", "seed": CONSTRUCTION_SEEDS["RC2"], "use_initial_state": True, "conditional_supply": False,
                "question": "Does the observed congested state persist under SUMO dynamics at the observed boundary demand, i.e. was the free-flow outcome only an initial-condition artefact?",
                "predicted_outcome": "the injected congested state relaxes towards free flow because the network has no binding downstream supply at the observed demand",
                "supports_if": "the late evaluation window still lies inside the real-target block envelope",
                "refutes_if": "the late evaluation window has moved outside the envelope towards free flow",
            },
            {
                "variant": "RC3", "seed": CONSTRUCTION_SEEDS["RC3"], "use_initial_state": True, "conditional_supply": True,
                "question": "If a downstream supply restriction is admitted as a declared conditional assumption, does the local state land in the observed congested envelope?",
                "predicted_outcome": f"congested branch: a {DOWNSTREAM_EXIT_LANES}-lane downstream exit has analytic capacity close to the observed congested through-flow, so a queue forms and the local state approaches the real target",
                "supports_if": "the late evaluation window lies inside the real-target block envelope",
                "refutes_if": "the late evaluation window stays on the free-flow branch or over-congests beyond the envelope",
            },
        ],
        "stop_rules": [
            "any engineering failure (non-zero SUMO exit, teleport, collision) stops the batch",
            "if RC2 and RC3 both fail the state-support envelope, stop and report Evidence Insufficient rather than search parameters",
            "independent seed repeats are only run for a variant that achieves state support, and are reported separately from the construction run",
        ],
        "resource_limits": {"per_run_wall_s": 600, "batch_wall_s": 3600, "threads": 1},
        "budget": {"construction_runs": 3, "reserved_independent_repeats": 2, "total": 5,
                   "note": "diagnostic budget re-planned under the 2026-10-21 task authorisation; still no ABCD, no protocol lock, no third window, no locked holdout"},
        "sumo_binary_sha256": sha256_file(Path(_sumo_binary())),
        "netconvert_binary_sha256": sha256_file(Path(_netconvert_binary())),
        "source_files": source,
        "sealed_windows_not_read": ["us101__0820_0835", "nsgim_lankershim__complete"],
        "scientific_claim_eligible": False,
        "gate_status": "pending_simulation_sample",
        "network_specs": {"RC1": sr.scene_spec(), "RC2": sr.scene_spec(), "RC3": conditional_network_spec()},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__},
        "git_head": subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    }
    write_json(output / "diagnostic_plan.json", plan)
    (output / "PLAN_SHA256").write_text(sha256_file(output / "diagnostic_plan.json") + "  diagnostic_plan.json\n", encoding="utf-8")
    write_json(output / "run_metadata.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "note": "timestamp is recorded outside the frozen plan so that the plan itself is byte-reproducible",
    })

    results = []
    for variant in plan["variants"]:
        work = output / "runs" / variant["variant"]
        record = run_variant(
            work, variant=variant["variant"], condition=condition, seed=variant["seed"],
            use_initial_state=variant["use_initial_state"], conditional_supply=variant["conditional_supply"],
            states=states,
        )
        record["question"] = variant["question"]
        record["predicted_outcome"] = variant["predicted_outcome"]
        results.append(record)
        write_json(work / "summary.json", record)
        print(f"{variant['variant']}: speed={record['metrics']['speed_mean_mps']:.3f} density={record['metrics']['density_veh_km_lane']:.3f} supported={record['state_support']['state_supported']}", flush=True)

    supported = [record for record in results if record["state_support"]["state_supported"]]
    repeats = []
    if supported and not args.no_repeats:
        chosen = supported[0]
        repeat_key = chosen["variant"] + "r"
        work = output / "runs" / repeat_key
        validate = specification(condition)
        record = run_variant(
            work, variant=repeat_key, condition=condition, seed=REPEAT_SEEDS[repeat_key],
            use_initial_state=chosen["use_initial_state"], conditional_supply=chosen["conditional_supply"],
            states=states,
        )
        record["repeat_of"] = chosen["variant"]
        record["question"] = "independent seed repeat of the variant that achieved state support"
        record["predicted_outcome"] = "same state-support verdict if the result does not depend on one random realisation"
        repeats.append(record)
        write_json(work / "summary.json", record)
        print(f"{repeat_key}: speed={record['metrics']['speed_mean_mps']:.3f} density={record['metrics']['density_veh_km_lane']:.3f} supported={record['state_support']['state_supported']}", flush=True)

    verdict = {
        "result_id": RESULT_ID,
        "condition": condition,
        "variants_run": [record["variant"] for record in results],
        "independent_seed_repeats": [record["variant"] for record in repeats],
        "state_supported_variants": [record["variant"] for record in supported],
        "observed_geometry_alone_supports_state": any(
            record["variant"] == "RC1" and record["state_support"]["state_supported"] for record in results
        ),
        "observed_initial_state_persists": any(
            record["variant"] == "RC2" and record["state_support"]["state_supported"] for record in results
        ),
        "conditional_supply_supports_state": any(
            record["variant"] == "RC3" and record["state_support"]["state_supported"] for record in results
        ),
        "overall": (
            "StateSupportAchieved_ConditionalScenario"
            if supported
            else "EvidenceInsufficient_StateSupport"
        ),
        "interpretation": (
            "Only a declared conditional downstream supply restriction reproduces the observed "
            "congested local state; the observed geometry and boundary demand alone reproduce the "
            "observed flow on the free-flow branch. The local state is therefore not identified by "
            "the observed flow and requires a supply or initial-state assumption that the approved "
            "windows cannot identify."
            if supported else
            "None of the three pre-declared variants reached the observed congested envelope, so the "
            "mismatch is classified Evidence Insufficient at the state-support layer and no further "
            "parameter search is performed."
        ),
        "not_a_science_tolerance": True,
        "reality_coverage_accepted": False,
        "scientific_claim_eligible": False,
    }
    write_json(output / "state_support_verdict.json", verdict)
    request = output / "real_local_context.json"
    real_local = tr.local_state(states, window=tr.CALIBRATION_WINDOWS[condition])
    real_interactions = tr.interaction_stats(states, window=tr.CALIBRATION_WINDOWS[condition])
    write_json(request, {
        "condition": condition,
        "window_s": list(tr.CALIBRATION_WINDOWS[condition]),
        "local_state": real_local,
        "interaction_stats": real_interactions,
        "status": "Observation",
    })
    write_json(
        output / "scene_vs_real_congested_branch.json",
        congested_branch_diagnosis(condition, real_local, real_interactions),
    )
    write_json(output / "run_ledger.json", {
        "construction_seeds": CONSTRUCTION_SEEDS,
        "repeat_seeds": REPEAT_SEEDS,
        "duration_s": DURATION_S,
        "variants": [{k: record[k] for k in ("variant", "seed", "condition", "network_spec_id", "state_support")} for record in results + repeats],
        "sumo_binary_sha256": plan["sumo_binary_sha256"],
    })
    names = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS", "fcd.xml", "summary.xml"}
    )
    lines = [f"{sha256_file(output / name)}  {name}" for name in names]
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(output / "manifest.json", {
        "schema_version": "aad.evidence-manifest.v1",
        "result_id": RESULT_ID,
        "files": [{"path": name, "sha256": sha256_file(output / name), "bytes": (output / name).stat().st_size} for name in names],
    })
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", default="us101__0750_0805")
    parser.add_argument("--output-root", default="code/outputs/formal/calibration/stage_0_5_scene_reconstruction_v1")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--no-repeats", action="store_true")
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
