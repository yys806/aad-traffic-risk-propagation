"""Deterministic time-step sensitivity probe for the Stage 0.5.4-A protocol audit.

Two engineering configurations are run on the same fixtures:

* ``A_uniform_0.1``: internal 0.1 s, recorded 0.1 s
* ``B_fine_internal_0.05``: internal 0.05 s, recorded 0.1 s

The recorded cadence stays at 100 ms in both, so the comparison isolates the integration
step.  Nothing here calibrates a scientific parameter, and no validation-window data is
touched.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import time

import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.stage_0_5_sumo import (  # noqa: E402
    RESULT_ID as SUMO_ENGINEERING_RESULT_ID,
    run_stage_0_5_no_message_baseline,
    sumo_environment,
)

SENSITIVITY_RESULT_ID = "RES-STAGE-0.5-CALIBRATION-READINESS-V1"
CONFIGURATIONS = (
    {"configuration_id": "A_uniform_0.1", "internal_step_s": 0.1, "recorded_observation_step_s": 0.1},
    {"configuration_id": "B_fine_internal_0.05", "internal_step_s": 0.05, "recorded_observation_step_s": 0.1},
    {"configuration_id": "C_finer_internal_0.025", "internal_step_s": 0.025, "recorded_observation_step_s": 0.1},
)
#: cost benchmark: one longer baseline run per integration-step candidate
BENCHMARK_DURATION_S = 300.0


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def run_sensitivity(*, output_dir: Path, duration_s: float, seed: int) -> dict[str, object]:
    if output_dir.exists():
        raise SystemExit(f"refusing to overwrite {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    runs: list[dict[str, object]] = []
    for configuration in CONFIGURATIONS:
        for fixture in ("measurement_probe_queue_stop", "baseline_mixed_demand"):
            package = output_dir / f"{configuration['configuration_id']}__{fixture}"
            started = time.perf_counter()
            run_stage_0_5_no_message_baseline(
                output_dir=package,
                fixture_id=fixture,
                seed=seed,
                duration_s=duration_s,
                internal_step_s=configuration["internal_step_s"],
                recorded_observation_step_s=configuration["recorded_observation_step_s"],
            )
            wall_s = time.perf_counter() - started
            audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
            runtime = json.loads((package / "runtime_diagnostics.json").read_text(encoding="utf-8"))
            exposure = json.loads((package / "p2_exposure_summary.json").read_text(encoding="utf-8"))
            events = pd.read_parquet(package / "p2_engineering_events.parquet")
            states = pd.read_parquet(package / "state.parquet")
            follows = states.loc[states["leader_observed"]]
            runs.append(
                {
                    "configuration_id": configuration["configuration_id"],
                    "fixture_id": fixture,
                    "internal_step_s": configuration["internal_step_s"],
                    "recorded_observation_step_s": configuration["recorded_observation_step_s"],
                    "observation_decimation_factor": runtime["observation_decimation_factor"],
                    "wall_clock_s": wall_s,
                    "state_rows": int(audit["state_rows"]),
                    "events": int(audit["p2_engineering_events"]),
                    "event_start_s": events["event_start_s"].tolist(),
                    "event_end_s": events["event_end_s"].tolist(),
                    "event_confirm_s": events["event_confirm_s"].tolist(),
                    "ttc_min_s": events["ttc_min_s"].tolist(),
                    "p2_evaluable_following_exposure_s": exposure["p2_evaluable_following_exposure_s"],
                    "reliable_closing_exposure_s": exposure["reliable_closing_exposure_s"],
                    "mean_speed_mps": float(states["speed_mps"].mean()),
                    "min_acceleration_mps2": float(states["acceleration_mps2"].min()),
                    "max_acceleration_mps2": float(states["acceleration_mps2"].max()),
                    "min_net_gap_m": float(follows["net_gap_m"].min()) if len(follows) else None,
                    "collisions": int(runtime["collisions"]),
                    "insertion_failures": runtime["insertion_failures"],
                    "cadence_max_abs_error_s": runtime["observation_cadence_check"]["max_abs_error_s"],
                    "net_gap_lane_position_residual_max_abs_m": runtime["net_gap_crosscheck"][
                        "lane_position_residual_max_abs_m"
                    ],
                    "package": package.name,
                }
            )
    benchmark: list[dict[str, object]] = []
    for configuration in CONFIGURATIONS:
        package = output_dir / f"benchmark__{configuration['configuration_id']}"
        started = time.perf_counter()
        run_stage_0_5_no_message_baseline(
            output_dir=package,
            fixture_id="baseline_mixed_demand",
            seed=seed,
            duration_s=BENCHMARK_DURATION_S,
            internal_step_s=configuration["internal_step_s"],
            recorded_observation_step_s=configuration["recorded_observation_step_s"],
        )
        wall_s = time.perf_counter() - started
        audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
        benchmark.append(
            {
                "configuration_id": configuration["configuration_id"],
                "internal_step_s": configuration["internal_step_s"],
                "duration_s": BENCHMARK_DURATION_S,
                "wall_clock_s": wall_s,
                "state_rows": int(audit["state_rows"]),
                "simulated_seconds_per_wall_second": BENCHMARK_DURATION_S / max(wall_s, 1e-9),
                "vehicle_count": int(audit["vehicle_count"]),
                "package": package.name,
            }
        )
    comparisons: list[dict[str, object]] = []
    for fixture in ("measurement_probe_queue_stop", "baseline_mixed_demand"):
        first = next(row for row in runs if row["fixture_id"] == fixture and row["configuration_id"] == "A_uniform_0.1")
        second = next(
            row for row in runs if row["fixture_id"] == fixture and row["configuration_id"] == "B_fine_internal_0.05"
        )
        third = next(
            row for row in runs if row["fixture_id"] == fixture and row["configuration_id"] == "C_finer_internal_0.025"
        )
        comparisons.append(
            {
                "fixture_id": fixture,
                "events_match": first["events"] == second["events"],
                "event_start_s_max_abs_delta": max(
                    (abs(a - b) for a, b in zip(first["event_start_s"], second["event_start_s"])), default=0.0
                ),
                "event_end_s_max_abs_delta": max(
                    (abs(a - b) for a, b in zip(first["event_end_s"], second["event_end_s"])), default=0.0
                ),
                "event_confirm_s_max_abs_delta": max(
                    (abs(a - b) for a, b in zip(first["event_confirm_s"], second["event_confirm_s"])), default=0.0
                ),
                "exposure_relative_delta": (
                    abs(
                        first["p2_evaluable_following_exposure_s"] - second["p2_evaluable_following_exposure_s"]
                    )
                    / max(first["p2_evaluable_following_exposure_s"], 1e-9)
                ),
                "mean_speed_abs_delta_mps": abs(first["mean_speed_mps"] - second["mean_speed_mps"]),
                "min_acceleration_abs_delta_mps2": abs(
                    first["min_acceleration_mps2"] - second["min_acceleration_mps2"]
                ),
                "wall_clock_ratio": second["wall_clock_s"] / max(first["wall_clock_s"], 1e-9),
                "state_rows_ratio": second["state_rows"] / max(first["state_rows"], 1),
                "convergence_A_to_B_start_s": max(
                    (abs(a - b) for a, b in zip(first["event_start_s"], second["event_start_s"])), default=0.0
                ),
                "convergence_B_to_C_start_s": max(
                    (abs(a - b) for a, b in zip(second["event_start_s"], third["event_start_s"])), default=0.0
                ),
                "events_match_all_three": first["events"] == second["events"] == third["events"],
            }
        )
    payload = {
        "schema_version": "stage_0_5.calibration-readiness.v1.timestep-sensitivity.v1",
        "result_id": SENSITIVITY_RESULT_ID,
        "upstream_engineering_result": SUMO_ENGINEERING_RESULT_ID,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "duration_s": duration_s,
        "seed": seed,
        "environment": sumo_environment(),
        "runs": runs,
        "comparisons": comparisons,
        "cost_benchmark": benchmark,
        "cost_benchmark_note": (
            "one 300 s baseline run per step candidate; the 20 s sensitivity runs are dominated by"
            " process startup and cannot be used as a cost estimate"
        ),
        "engineering_only": True,
        "scientific_claim_eligible": False,
        "no_parameter_was_frozen": True,
        "interpretation": (
            "the recorded series stays at 100 ms in both configurations, so any difference reflects"
            " integration accuracy and cost only; this is a protocol probe, not a calibration"
        ),
    }
    _write_json(output_dir / "timestep_sensitivity.json", payload)
    manifest = {
        "schema_version": "stage_0_5.calibration-readiness.v1.timestep-sensitivity-manifest.v1",
        "result_id": SENSITIVITY_RESULT_ID,
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
            for path in sorted(output_dir.iterdir())
            if path.is_file()
        ],
    }
    _write_json(output_dir / "manifest.json", manifest)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(
            f"{_sha256_file(path)}  {path.name}"
            for path in sorted(output_dir.iterdir())
            if path.is_file()
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration-s", type=float, default=20.0)
    parser.add_argument("--seed", type=int, default=20260907)
    args = parser.parse_args()
    payload = run_sensitivity(output_dir=args.output, duration_s=args.duration_s, seed=args.seed)
    print(json.dumps({"output": args.output.as_posix(), "comparisons": payload["comparisons"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
