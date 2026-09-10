"""Executable analytic and archived-path checks that precede Stage 0.6 locking."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from riskprop.calibration import sha256_file
from riskprop.prelock_metrics import (
    evaluate_timestep_convergence,
    integrated_ttc_exposure,
    post_encroachment_time,
    rear_end_analytic_truth,
)
from riskprop.real_trajectory import add_ngsim_leader_ttc
from riskprop.stage_0_1_sumo import analyze_physical_path_from_archived_tables


def _ngsim_pair(*, gap_m: float, follower_speed: float, leader_speed: float) -> pd.DataFrame:
    leader_length_ft = 15.0
    gap_ft = gap_m / 0.3048
    return pd.DataFrame(
        [
            {
                "Vehicle_ID": 1,
                "Global_Time": 1000,
                "v_Length": 15.0,
                "v_Vel": follower_speed / 0.3048,
                "Preceeding": 2,
                "Space_Hdwy": gap_ft + leader_length_ft,
            },
            {
                "Vehicle_ID": 2,
                "Global_Time": 1000,
                "v_Length": leader_length_ft,
                "v_Vel": leader_speed / 0.3048,
                "Preceeding": 0,
                "Space_Hdwy": 0.0,
            },
        ]
    )


def _analytic_truth_audit() -> dict:
    cases = []
    definitions = (
        ("uniform_closing", 20.0, 10.0, 5.0),
        ("stationary_leader", 12.0, 6.0, 0.0),
        ("stationary_follower", 12.0, 0.0, 6.0),
        ("equal_speed", 12.0, 6.0, 6.0),
    )
    for name, gap, follower, leader in definitions:
        expected = rear_end_analytic_truth(
            net_gap_m=gap,
            follower_speed_mps=follower,
            leader_speed_mps=leader,
        )
        measured = add_ngsim_leader_ttc(
            _ngsim_pair(gap_m=gap, follower_speed=follower, leader_speed=leader)
        ).set_index("id").loc["1"]
        expected_valid = expected["status"] == "valid"
        ttc_match = (
            math.isclose(float(measured["ttc_s"]), float(expected["ttc_s"]), rel_tol=1e-9)
            if expected_valid
            else math.isinf(float(measured["ttc_s"]))
        )
        drac_match = (
            math.isclose(float(measured["drac_mps2"]), float(expected["drac_mps2"]), rel_tol=1e-9)
            if expected_valid
            else pd.isna(measured["drac_mps2"])
        )
        cases.append(
            {
                "case": name,
                "expected_status": expected["status"],
                "measured_status": str(measured["measurement_status"]),
                "ttc_match": ttc_match,
                "drac_match": drac_match,
                "pass": bool(
                    ttc_match
                    and drac_match
                    and bool(measured["ttc_valid"]) is expected_valid
                ),
            }
        )
    pet_cases = [
        math.isclose(post_encroachment_time((1.0, 2.0), (2.4, 3.0)), 0.4),
        math.isclose(post_encroachment_time((1.0, 2.5), (2.0, 3.0)), 0.0),
    ]
    collision = rear_end_analytic_truth(
        net_gap_m=0.0, follower_speed_mps=5.0, leader_speed_mps=0.0
    )
    return {
        "cases": cases,
        "pet_cases_pass": all(pet_cases),
        "collision_case_pass": collision["collision"] is True and collision["ttc_s"] == 0.0,
        "pass": all(item["pass"] for item in cases)
        and all(pet_cases)
        and collision["collision"] is True,
    }


def _path_truth_audit() -> dict:
    disconnected_topology = {
        "source_edge": "src",
        "target_edge": "tgt",
        "directed_edges": [
            {"edge_id": "src", "from_node": "a", "to_node": "b"},
            {"edge_id": "tgt", "from_node": "c", "to_node": "d"},
        ],
    }
    connected_topology = {
        "source_edge": "road",
        "target_edge": "road",
        "directed_edges": [{"edge_id": "road", "from_node": "a", "to_node": "b"}],
    }
    cases = []
    disconnected_state = pd.DataFrame(
        [
            {"time_s": 0.0, "vehicle_id": "source", "edge_id": "src", "leader_id": None},
            {"time_s": 0.0, "vehicle_id": "target", "edge_id": "tgt", "leader_id": None},
        ]
    )
    cases.append(
        (
            "disconnected",
            analyze_physical_path_from_archived_tables(
                disconnected_state,
                disconnected_topology,
                source_vehicle_id="source",
                target_vehicle_id="target",
            ),
            "disconnected_topology",
            None,
        )
    )
    chain_state = pd.DataFrame(
        [
            {"time_s": time, "vehicle_id": vehicle, "edge_id": "road", "leader_id": leader}
            for time, vehicle, leader in (
                (0.0, "source", None),
                (1.0, "source", None),
                (2.0, "source", None),
                (0.0, "middle", None),
                (1.0, "middle", "source"),
                (2.0, "middle", None),
                (0.0, "target", None),
                (1.0, "target", None),
                (2.0, "target", "middle"),
            )
        ]
    )
    cases.append(
        (
            "multivehicle_chain",
            analyze_physical_path_from_archived_tables(
                chain_state,
                connected_topology,
                source_vehicle_id="source",
                target_vehicle_id="target",
                source_start_time_s=0.0,
            ),
            "finite_arrival",
            2.0,
        )
    )
    censored_state = chain_state.copy()
    censored_state.loc[censored_state["vehicle_id"].eq("target"), "leader_id"] = None
    cases.append(
        (
            "right_censored",
            analyze_physical_path_from_archived_tables(
                censored_state,
                connected_topology,
                source_vehicle_id="source",
                target_vehicle_id="target",
            ),
            "right_censored",
            None,
        )
    )
    missing_target = chain_state.loc[~chain_state["vehicle_id"].eq("target")]
    cases.append(
        (
            "missing_target",
            analyze_physical_path_from_archived_tables(
                missing_target,
                connected_topology,
                source_vehicle_id="source",
                target_vehicle_id="target",
            ),
            "uncertain_missing_vehicle",
            None,
        )
    )
    rows = []
    for name, actual, expected_status, expected_tau in cases:
        tau_match = actual["tau_p"] == expected_tau
        rows.append(
            {
                "case": name,
                "expected_status": expected_status,
                "actual_status": actual["status"],
                "expected_tau_p": expected_tau,
                "actual_tau_p": actual["tau_p"],
                "pass": actual["status"] == expected_status and tau_match,
            }
        )
    return {"cases": rows, "pass": all(item["pass"] for item in rows)}


def _timestep_audit() -> dict:
    metric_by_step = {}
    horizon_s = 3.83
    for step in (0.10, 0.05, 0.02, 0.01):
        times = np.arange(0.0, horizon_s, step)
        durations = np.minimum(step, horizon_s - times)
        ttc = (20.0 - 5.0 * times) / 5.0
        states = pd.DataFrame(
            {
                "ttc_s": ttc,
                "valid": True,
                "dt_s": durations,
                "collision": False,
            }
        )
        metric_by_step[step] = integrated_ttc_exposure(states, threshold_s=5.0)
    result = evaluate_timestep_convergence(metric_by_step, zero_tolerance=None)
    result["metric_by_step"] = {f"{key:.2f}": value for key, value in metric_by_step.items()}
    result["analytic_reference"] = 0.2 + horizon_s / 10.0
    result["horizon_s"] = horizon_s
    return result


def write_stage_0_6_prelock_validation(output_dir: str | Path) -> Path:
    """Write preliminary Stage 0.6 truth evidence while failing closed on final lock."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    audit = {
        "schema_version": "stage_0_6.prelock-validation.v1",
        "experiment_id": "stage_0_6",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scientific_claim_eligible": False,
        "analytic_truth": _analytic_truth_audit(),
        "physical_path_truth": _path_truth_audit(),
        "timestep_convergence": _timestep_audit(),
        "gate_status": "pending_e15_e17_and_frozen_tolerances",
        "note": "Truth fixtures can validate implementations, but cannot set thresholds, delta_eq, delta_R, or Stage 1.1 sample size.",
    }
    (output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": "stage_0_6.prelock-manifest.v1",
        "files": [
            {
                "path": "audit.json",
                "bytes": (output_dir / "audit.json").stat().st_size,
                "sha256": sha256_file(output_dir / "audit.json"),
            }
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(
            f"{sha256_file(output_dir / name)}  {name}" for name in ("audit.json", "manifest.json")
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_dir
