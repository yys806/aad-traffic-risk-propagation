"""Read named evidence/approved XML only; never import a simulator or raw data.

Produces a new engineering audit, not repaired historical risk measurements.
Existing outputs are refused. Full logs and individual trajectories are not copied.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

WINDOWS = ("us101__0750_0805", "us101__0805_0820")
RESULTS = {
    "micro": "RES-STAGE-0.5-METHOD-EXPANSION-V1",
    "state": "RES-STAGE-0.5-STATE-SUPPORT-V1",
    "arrival": "RES-STAGE-0.5-ARRIVAL-TIMING-V1",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root, *, local_inputs=False):
    bindings = {}

    def read(name):
        path = root / name
        data = path.read_bytes()
        bindings[name] = hashlib.sha256(data).hexdigest()
        return json.loads(data)

    def evidence(kind, name):
        return read("evidence/results/" + RESULTS[kind] + "/" + name)

    micro = evidence("micro", "response_summary.json")
    init = evidence("micro", "init_summary.json")
    metric_path = "evidence/results/" + RESULTS["micro"] + "/response_metrics.csv"
    with (root / metric_path).open(encoding="utf-8") as stream:
        metrics = list(csv.DictReader(stream))
    bindings[metric_path] = sha(root / metric_path)
    assert len(metrics) == micro["rows"] == micro["budget_used"]["sumo_process_invocations_executed"] == 324
    assert not micro["failures"]
    groups = Counter((r["window"], r["pair_index"], r["configuration"], r["seed"]) for r in metrics)
    assert len(groups) == 324 and max(groups.values()) == 1
    grid = evidence("state", "grid_results.json")["results"]
    seeds = evidence("state", "seed_repeats.json")["results"]
    structural = evidence("state", "structural_results.json")["results"]
    # Historical aggregate only. No third-window raw source or FCD is opened.
    temporal = evidence("state", "temporal_validation.json")["frozen_configuration_runs"]
    arrival = evidence("arrival", "run_results.json")["results"]
    assert [len(grid), len(seeds), len(structural), len(temporal), len(arrival)] == [30, 20, 4, 4, 20]
    successful = lambda rows: sum(r["sumo"]["returncode"] == 0 for r in rows)
    state_keys = lambda rows: {(r["cell"]["cell_id"], r["seed"]) for r in rows}
    variability = {}
    for window in WINDOWS:
        rows = [r for r in seeds if r["cell"]["behaviour"] == "B_het" and r["cell"]["condition"] == window]
        variability[window] = {"n": len(rows), "seeds": [r["seed"] for r in rows], "state_metrics": {}}
        for metric in ["density_veh_km_lane", "speed_mean_mps", "speed_sd_mps"]:
            values = [r["descriptors"][metric] for r in rows]
            variability[window]["state_metrics"][metric] = {"mean": statistics.mean(values), "sample_sd": statistics.stdev(values)}
        pair = {}
        for seed in sorted({r["seed"] for r in arrival if r["window"] == window}):
            arms = {r["arm"]: r for r in arrival if r["window"] == window and r["seed"] == seed}
            pair[seed] = {k: arms["E"]["descriptors"][k] - arms["U"]["descriptors"][k]
                          for k in ["density_veh_km_lane", "speed_mean_mps", "speed_sd_mps"]}
        variability[window]["arrival_E_minus_U"] = {k: {"mean": statistics.mean(v[k] for v in pair.values()),
            "sample_sd": statistics.stdev(v[k] for v in pair.values())} for k in next(iter(pair.values()))}
    original = read("docs/audits/stage_0_5_interaction_preflight_v1/execution_ledger.json")
    actual = read("evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/execution_ledger.json")
    review = read("evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/failure_review.json")
    candidate = read("evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/review_proposal.json")
    c6 = read("evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/comparison_summary.json")
    c6_sources = read("evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/provenance.json")["source_sha256"]
    for name, expected in c6_sources.items():
        bindings[name] = sha(root / name)
        assert bindings[name] == expected, name
    input_scope = {}
    if local_inputs:
        for parent in ["ID1_SUPPLY_0750", "ID2_SUPPLY_0805"]:
            prefix = "code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs/" + parent + "/"
            path = prefix + "routes.rou.xml"
            bindings[path] = sha(root / path)
            assert bindings[path] == candidate["approved_input_sha256"][path]
            data = (root / path).read_bytes()
            assert b"<!DOCTYPE" not in data.upper() and b"<!ENTITY" not in data.upper()
            xml = ET.fromstring(data)
            routes = {r.get("id"): r.get("edges").split() for r in xml.findall("route")}
            initial = [v for v in xml.findall("vehicle") if v.get("id").startswith("i")]
            downstream = [v for v in initial if routes[v.get("route")][0] == "main_2"]
            other = [float(v.get("departSpeed")) for v in downstream if float(v.get("departSpeed")) != 10]
            input_scope[parent] = {"initial_count": len(initial), "initial_start_edge_counts": dict(Counter(routes[v.get("route")][0] for v in initial)),
                "numeric10_count": sum(float(v.get("departSpeed")) == 10 for v in initial),
                "main2_non10_count": len(other), "main2_non10_gt5_count": sum(v > 5 for v in other),
                "main2_non10_speed_range_mps": [min(other), max(other)] if other else None,
                "dynamic_effect": "Unknown; static input audit only, no simulation"}
    return {"task_id": "AAD-0.5-INTERACTION-RESEARCH-V2", "status": "Verified engineering facts; scientific plan Proposed",
        "counts": {"micro_response": {"attempts": 324, "unique_pair_configuration_seed_keys": len(groups), "failures": 0,
            "pairs": len({(r['window'], r['pair_index']) for r in metrics}), "configurations": len({r['configuration'] for r in metrics}),
            "seeds": sorted({int(r['seed']) for r in metrics}), "separate_initialization_runs": len(init['rows']),
            "newell": "24 non-SUMO prototypes, separate from 324; see newell_summary.json"},
            "conditional_state": {"attempts": 58, "grid": len(grid), "seed_repetitions": len(seeds), "structural": len(structural),
                "historical_third_window_aggregate_only": len(temporal), "returncode_zero_first54": successful(grid + seeds + structural),
                "grid_seed_same_cell_seed_overlap": len(state_keys(grid) & state_keys(seeds)),
                "overlap_limit": "Four matching condition/behaviour/supply/seed keys are attempts, not additional independent seeds; byte equivalence not asserted"},
            "arrival_timing": {"attempts": len(arrival), "returncode_zero": successful(arrival),
                "unique_window_arm_seed_keys": len({(r['window'], r['arm'], r['seed']) for r in arrival})}},
        "noise_planning_only": {"evaluation_window_s": [300, 420], "state_seed_summary": variability,
            "micro_seed_variability": micro["seed_variability"],
            "limits": "Old window/initialization differ. Old gap/closing/P2 and denominators are not C6-certified for new inference. No automatic h/delta/B or repeat count derived."},
        "C6": c6, "C6_source_sha256_matches": c6_sources,
        "historical_budget": {"task_id": original["task_id"], "original_cap": original["maximum_new_trajectory_attempts"],
            "preflight_snapshot_attempts": original["actual_attempts"], "actual_execution_attempts": actual["attempts"],
            "unattempted": review["not_attempted"], "snapshot_explanation": "preflight is a preserved earlier snapshot, not the live execution ledger"},
        "candidate_flags": {k: candidate[k] for k in ["execution_allowed", "researcher_confirmed", "protocol_frozen"]},
        "local_input_scope": input_scope, "new_trajectories": 0, "raw_validation_or_holdout_reads": 0,
        "Gate_changed": False, "scientific_claim_eligible": False, "read_sha256": bindings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--local-inputs", action="store_true")
    args = parser.parse_args()
    result = audit(args.repo_root.resolve(), local_inputs=args.local_inputs)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"counts": result["counts"], "local_input_scope": result["local_input_scope"], "new_trajectories": 0}, ensure_ascii=False))
