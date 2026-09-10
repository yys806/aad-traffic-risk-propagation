"""Stage 0.5 simulation-to-real coverage gate; no message-effect analysis."""

from __future__ import annotations

from itertools import combinations
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from riskprop.calibration import energy_distance, fit_robust_scaler, sha256_file


def deterministic_state_sample(
    frame: pd.DataFrame, *, max_rows: int, seed: int
) -> pd.DataFrame:
    """Take the smallest stable row hashes, avoiding outcome-based selection."""

    if max_rows < 1:
        raise ValueError("max_rows must be positive")
    key_candidates = (
        "dataset",
        "site",
        "window_id",
        "vehicle_id",
        "id",
        "time_s",
    )
    key_columns = [column for column in key_candidates if column in frame.columns]
    if not key_columns:
        raise ValueError("state sample needs at least one stable identity column")
    result = frame.copy()
    hashes = pd.util.hash_pandas_object(
        result.loc[:, key_columns].astype("string"), index=False
    ).astype("uint64")
    hashes = hashes ^ np.uint64(seed)
    result["_sample_key_u64"] = hashes
    result = result.nsmallest(min(max_rows, len(result)), "_sample_key_u64")
    result["sample_key_hash64"] = result["_sample_key_u64"].map(
        lambda value: f"{int(value):016x}"
    )
    result = result.drop(columns="_sample_key_u64")
    return result.sort_values("sample_key_hash64").reset_index(drop=True)


def evaluate_simulation_coverage(
    *,
    real_groups: Mapping[str, pd.DataFrame],
    simulation: pd.DataFrame,
    continuous_columns: Sequence[str],
    stratum_column: str,
    minimum_stratum_coverage: float = 0.90,
    real_real_quantile: float = 0.95,
) -> dict:
    """Compare sim-real distance against natural real-real variation."""

    if len(real_groups) < 2:
        raise ValueError("at least two independent real calibration groups are required")
    if simulation.empty:
        raise ValueError("simulation calibration sample cannot be empty")
    if not 0 < minimum_stratum_coverage <= 1 or not 0 < real_real_quantile <= 1:
        raise ValueError("coverage and quantile thresholds must be in (0, 1]")
    reference = pd.concat(list(real_groups.values()), ignore_index=True)
    scaler = fit_robust_scaler(reference, continuous_columns)
    pair_distances = [
        energy_distance(first, second, continuous_columns, scaler=scaler)
        for (_, first), (_, second) in combinations(real_groups.items(), 2)
    ]
    threshold = float(np.quantile(pair_distances, real_real_quantile, method="higher"))
    sim_real = energy_distance(reference, simulation, continuous_columns, scaler=scaler)
    distance_pass = sim_real <= threshold + 1e-12
    real_strata = set(reference[stratum_column].dropna().astype(str))
    simulated_strata = set(simulation[stratum_column].dropna().astype(str))
    supported = real_strata & simulated_strata
    coverage = len(supported) / len(real_strata) if real_strata else 0.0
    strata_pass = coverage >= minimum_stratum_coverage
    return {
        "schema_version": "stage_0_5.coverage-gate.v1",
        "scientific_claim_eligible": False,
        "real_real_distances": pair_distances,
        "real_real_upper_bound": threshold,
        "sim_real_distance": sim_real,
        "distance_pass": distance_pass,
        "real_strata": sorted(real_strata),
        "supported_strata": sorted(supported),
        "unsupported_strata": sorted(real_strata - simulated_strata),
        "stratum_coverage": coverage,
        "minimum_stratum_coverage": minimum_stratum_coverage,
        "strata_pass": strata_pass,
        "gate_status": "pass" if distance_pass and strata_pass else "fail",
    }


def write_real_reference_package(
    *,
    ngsim_state_paths: Sequence[str | Path],
    pneuma_state_path: str | Path,
    ngsim_event_path: str | Path,
    output_dir: str | Path,
    max_rows_per_group: int = 5000,
    seed: int = 20260907,
) -> Path:
    """Freeze bounded real calibration references without using pNEUMA TTC."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    kinematics_frames = []
    following_frames = []
    source_audit = []
    for raw_path in ngsim_state_paths:
        path = Path(raw_path)
        state = pd.read_parquet(
            path,
            columns=[
                "dataset",
                "site",
                "window_id",
                "vehicle_id",
                "time_s",
                "speed_mps",
                "acceleration_mps2",
                "net_gap_m",
                "closing_speed_mps",
                "measurement_status",
            ],
        )
        kinematics = state.dropna(subset=["speed_mps", "acceleration_mps2"])
        kinematics_frames.append(
            deterministic_state_sample(kinematics, max_rows=max_rows_per_group, seed=seed)
        )
        following = state.loc[
            state["measurement_status"].astype(str).eq("valid")
        ].dropna(subset=["net_gap_m", "closing_speed_mps"])
        following_frames.append(
            deterministic_state_sample(following, max_rows=max_rows_per_group, seed=seed + 1)
        )
        source_audit.append(
            {
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "state_rows": int(len(state)),
                "kinematics_sample_rows": int(len(kinematics_frames[-1])),
                "following_sample_rows": int(len(following_frames[-1])),
            }
        )
    pneuma_path = Path(pneuma_state_path)
    pneuma = pd.read_parquet(
        pneuma_path,
        columns=[
            "id",
            "time_s",
            "speed_mps",
            "longitudinal_accel_mps2",
        ],
    ).rename(
        columns={
            "id": "vehicle_id",
            "longitudinal_accel_mps2": "acceleration_mps2",
        }
    )
    pneuma["dataset"] = "pNEUMA"
    pneuma["site"] = "Athens-d1"
    pneuma["window_id"] = "20181101_d1_0800_0830"
    pneuma_kinematics = pneuma.dropna(subset=["speed_mps", "acceleration_mps2"])
    kinematics_frames.append(
        deterministic_state_sample(
            pneuma_kinematics, max_rows=max_rows_per_group, seed=seed + 2
        )
    )
    source_audit.append(
        {
            "path": str(pneuma_path.resolve()),
            "sha256": sha256_file(pneuma_path),
            "state_rows": int(len(pneuma)),
            "kinematics_sample_rows": int(len(kinematics_frames[-1])),
            "following_sample_rows": 0,
            "pneuma_ttc_excluded": True,
        }
    )
    kinematics_reference = pd.concat(kinematics_frames, ignore_index=True)
    following_reference = pd.concat(following_frames, ignore_index=True)
    event_path = Path(ngsim_event_path)
    events = pd.read_parquet(event_path)
    kinematics_reference.to_parquet(
        output_dir / "kinematics_reference.parquet", index=False
    )
    following_reference.to_parquet(
        output_dir / "following_reference.parquet", index=False
    )
    events.to_parquet(output_dir / "risk_event_reference.parquet", index=False)
    audit = {
        "schema_version": "stage_0_5.real-reference.v1",
        "experiment_id": "stage_0_5",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scientific_claim_eligible": False,
        "sampling_rule": "smallest stable identity hashes; fixed rows per complete site/window",
        "max_rows_per_group": max_rows_per_group,
        "seed": seed,
        "kinematics_rows": int(len(kinematics_reference)),
        "following_rows": int(len(following_reference)),
        "risk_event_rows": int(len(events)),
        "pneuma_role": "urban_kinematics_only",
        "pneuma_ttc_included": False,
        "gate_status": "pending_simulation_sample",
        "sources": source_audit,
    }
    (output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _seal_reference(output_dir)
    return output_dir


def _seal_reference(output_dir: Path) -> None:
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    manifest = {
        "schema_version": "stage_0_5.real-reference-manifest.v1",
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in files
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files.append(manifest_path)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n",
        encoding="utf-8",
        newline="\n",
    )
