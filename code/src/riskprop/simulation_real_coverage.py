"""Stage 0.5 simulation-to-real coverage gate; no message-effect analysis."""

from __future__ import annotations

from itertools import combinations
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import pandas as pd

from riskprop.calibration import (
    CalibrationContractError,
    energy_distance,
    fit_robust_scaler,
    sha256_file,
)


CANONICAL_PNEUMA_COLUMNS = (
    "dataset",
    "site",
    "window_id",
    "vehicle_id",
    "vehicle_type",
    "time_s",
    "speed_mps",
    "acceleration_mps2",
    "quality_status",
    "time_weighting_eligible",
    "source_file_sha256",
)

LEGACY_PNEUMA_COLUMNS = (
    "id",
    "time_s",
    "speed_mps",
    "longitudinal_accel_mps2",
)

CANONICAL_PNEUMA_QUALITY_STATUSES = frozenset(
    {"raw_parsed", "parse_failed", "identity_ambiguous", "raw_time_anomaly", "duplicate_time"}
)


def _require_columns(frame: pd.DataFrame, required: Sequence[str], label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise CalibrationContractError(
            f"{label} is missing required columns: {', '.join(missing)}"
        )


def _validate_canonical_pneuma_frame(frame: pd.DataFrame) -> dict[str, Any]:
    """Validate the canonical Stage 0.3 pNEUMA contract without changing it."""

    _require_columns(frame, CANONICAL_PNEUMA_COLUMNS, "canonical pNEUMA reference")
    for column in ("dataset", "site", "window_id", "vehicle_id", "vehicle_type", "quality_status", "source_file_sha256"):
        values = frame[column].astype("string")
        if values.isna().any() or values.str.strip().eq("").any():
            raise CalibrationContractError(
                f"canonical pNEUMA column {column} contains null or empty values"
            )
    for column in ("time_s", "speed_mps", "acceleration_mps2"):
        values = pd.to_numeric(frame[column], errors="coerce")
        if not np.isfinite(values.to_numpy(float)).all():
            raise CalibrationContractError(
                f"canonical pNEUMA column {column} must contain finite numeric values"
            )
    speed = pd.to_numeric(frame["speed_mps"], errors="coerce")
    if (speed < 0).any():
        raise CalibrationContractError("canonical pNEUMA speed_mps cannot be negative")
    quality = frame["quality_status"].astype("string")
    unknown_quality = sorted(set(quality.dropna().astype(str)) - CANONICAL_PNEUMA_QUALITY_STATUSES)
    if unknown_quality:
        raise CalibrationContractError(
            "canonical pNEUMA quality_status contains unknown values: "
            + ", ".join(unknown_quality)
        )
    eligible = frame["time_weighting_eligible"]
    if not pd.api.types.is_bool_dtype(eligible):
        raise CalibrationContractError(
            "canonical pNEUMA time_weighting_eligible must be a complete boolean column"
        )
    if eligible.isna().any():
        raise CalibrationContractError(
            "canonical pNEUMA time_weighting_eligible cannot contain null values"
        )
    inconsistent = quality.ne("raw_parsed") & eligible.astype(bool)
    if inconsistent.any():
        raise CalibrationContractError(
            "canonical pNEUMA non-raw_parsed states cannot be time_weighting_eligible"
        )
    fingerprints = frame["source_file_sha256"].astype("string").str.upper()
    if (~fingerprints.str.fullmatch(r"[0-9A-F]{64}")).any():
        raise CalibrationContractError(
            "canonical pNEUMA source_file_sha256 must be 64 hexadecimal characters"
        )
    return {
        "rows": int(len(frame)),
        "quality_status_counts": {
            str(key): int(value)
            for key, value in quality.value_counts(dropna=False).items()
        },
        "time_weighting_eligible_rows": int(eligible.astype(bool).sum()),
        "vehicle_count": int(frame["vehicle_id"].nunique()),
        "vehicle_type_counts": {
            str(key): int(value)
            for key, value in frame["vehicle_type"].value_counts(dropna=False).items()
        },
        "dataset": sorted(frame["dataset"].astype(str).unique()),
        "site": sorted(frame["site"].astype(str).unique()),
        "window_id": sorted(frame["window_id"].astype(str).unique()),
        "source_file_sha256": sorted(fingerprints.unique()),
    }


def _read_pneuma_reference(
    path: Path, *, schema: Literal["canonical", "legacy"]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read either the formal canonical schema or an explicitly marked legacy view."""

    from pyarrow.parquet import ParquetFile

    available = set(ParquetFile(path).schema_arrow.names)
    if schema == "canonical":
        _require_columns(
            pd.DataFrame(columns=list(available)),
            CANONICAL_PNEUMA_COLUMNS,
            "canonical pNEUMA reference",
        )
        frame = pd.read_parquet(path, columns=list(CANONICAL_PNEUMA_COLUMNS))
        audit = _validate_canonical_pneuma_frame(frame)
        audit.update(
            {
                "input_rows": int(len(frame)),
                "pneuma_schema": "canonical",
                "formal_reference_eligible": True,
                "quality_columns_present": True,
            }
        )
        return frame, audit
    if schema != "legacy":
        raise CalibrationContractError(
            f"unsupported pNEUMA schema mode {schema!r}; use canonical or legacy"
        )
    _require_columns(
        pd.DataFrame(columns=list(available)), LEGACY_PNEUMA_COLUMNS, "legacy pNEUMA reference"
    )
    quality_present = {
        name for name in ("quality_status", "time_weighting_eligible") if name in available
    }
    if quality_present and quality_present != {"quality_status", "time_weighting_eligible"}:
        raise CalibrationContractError(
            "legacy pNEUMA input must provide both quality_status and "
            "time_weighting_eligible, or neither"
        )
    columns = list(LEGACY_PNEUMA_COLUMNS) + sorted(quality_present)
    if "vehicle_type" in available:
        columns.append("vehicle_type")
    if "source_file_sha256" in available:
        columns.append("source_file_sha256")
    frame = pd.read_parquet(path, columns=list(dict.fromkeys(columns))).rename(
        columns={
            "id": "vehicle_id",
            "longitudinal_accel_mps2": "acceleration_mps2",
        }
    )
    for column in ("time_s", "speed_mps", "acceleration_mps2"):
        values = pd.to_numeric(frame[column], errors="coerce")
        if not np.isfinite(values.to_numpy(float)).all():
            raise CalibrationContractError(
                f"legacy pNEUMA column {column} must contain finite numeric values"
            )
    frame["dataset"] = "pNEUMA"
    frame["site"] = "Athens-d1"
    frame["window_id"] = "20181101_d1_0800_0830"
    if "vehicle_type" not in frame:
        frame["vehicle_type"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    if "source_file_sha256" not in frame:
        frame["source_file_sha256"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    input_rows = int(len(frame))
    excluded = 0
    quality_counts: dict[str, int] = {}
    eligible_count = 0
    if quality_present:
        quality = frame["quality_status"].astype("string")
        frame["time_weighting_eligible"] = frame["time_weighting_eligible"].astype(bool)
        excluded = int(quality.ne("raw_parsed").sum())
        quality_counts = {str(key): int(value) for key, value in quality.value_counts(dropna=False).items()}
        eligible_count = int(frame["time_weighting_eligible"].sum())
        frame = frame.loc[quality.eq("raw_parsed")].copy()
    audit = {
        "input_rows": input_rows,
        "not_reliably_parsed_excluded": excluded,
        "quality_status_counts": quality_counts,
        "time_weighting_eligible_rows": eligible_count,
        "pneuma_schema": "legacy",
        "formal_reference_eligible": False,
        "quality_columns_present": bool(quality_present),
        "rows": int(len(frame)),
        "legacy_input_path": str(path),
        "note": "legacy mode is retained only for historical compatibility and is not a formal R2 reference",
    }
    return frame, audit


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
    pneuma_schema: Literal["canonical", "legacy"] = "canonical",
    input_manifest: Mapping[str, Any] | None = None,
    package_schema_version: str = "stage_0_5.real-reference.v2",
) -> Path:
    """Freeze bounded real calibration references without using pNEUMA TTC.

    pNEUMA quality semantics: when the state parquet carries
    ``quality_status`` / ``time_weighting_eligible`` columns (the Stage 0.3
    reference adapter output), states whose observation is not reliably
    parsed (any status other than ``raw_parsed``) are excluded from the
    kinematics pool before sampling (fail-closed, counts recorded in the
    audit).  ``time_weighting_eligible`` is carried through to the frozen
    reference so later statistics can keep the expected weighting; the
    bounded per-state sampling rule itself is unchanged.  Legacy four-column
    parquets remain accepted for backward compatibility and are recorded as
    ``pneuma_quality_columns_present=false``.
    """

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
                "source_role": (
                    "highway_following_risk_primary"
                    if state["site"].astype(str).eq("US-101").all()
                    else "urban_following_risk_auxiliary"
                ),
                "state_rows": int(len(state)),
                "kinematics_sample_rows": int(len(kinematics_frames[-1])),
                "following_sample_rows": int(len(following_frames[-1])),
            }
        )
    pneuma_path = Path(pneuma_state_path)
    pneuma, pneuma_quality_audit = _read_pneuma_reference(
        pneuma_path, schema=pneuma_schema
    )
    not_reliably_parsed = (
        pneuma["quality_status"].astype("string").ne("raw_parsed")
        if "quality_status" in pneuma.columns
        else pd.Series(False, index=pneuma.index)
    )
    pneuma_kinematics = pneuma.loc[~not_reliably_parsed].dropna(
        subset=["speed_mps", "acceleration_mps2"]
    )
    pneuma["source_role"] = "pneuma_urban_kinematics"
    pneuma_quality_audit.update(
        {
            "pneuma_quality_columns_present": bool(
                pneuma_quality_audit.get("quality_columns_present", False)
            ),
            "pneuma_quality_status_counts": {
                str(key): int(value)
                for key, value in pneuma["quality_status"].value_counts(dropna=False).items()
            }
            if "quality_status" in pneuma.columns
            else {},
            "pneuma_states_total": int(
                pneuma_quality_audit.get("input_rows", len(pneuma))
            ),
            "pneuma_states_not_reliably_parsed_excluded": int(
                pneuma_quality_audit.get("not_reliably_parsed_excluded", not_reliably_parsed.sum())
            ),
            "pneuma_states_time_weighting_eligible": int(
                pneuma_quality_audit.get(
                    "time_weighting_eligible_rows",
                    pneuma["time_weighting_eligible"].fillna(False).astype(bool).sum()
                    if "time_weighting_eligible" in pneuma.columns
                    else 0,
                )
            ),
            "exclusion_rule": "only quality_status == raw_parsed enters the bounded kinematics pool",
            "sampling_weight_note": (
                "bounded per-state sampling is unweighted; time_weighting_eligible is "
                "preserved for later statistics and is not itself a duration weight"
            ),
        }
    )
    kinematics_frames.append(
        deterministic_state_sample(
            pneuma_kinematics, max_rows=max_rows_per_group, seed=seed + 2
        )
    )
    source_audit.append(
        {
            "path": str(pneuma_path.resolve()),
            "sha256": sha256_file(pneuma_path),
            "source_role": "urban_kinematics_only",
            "state_rows": int(len(pneuma)),
            "kinematics_pool_rows": int(len(pneuma_kinematics)),
            "kinematics_sample_rows": int(len(kinematics_frames[-1])),
            "following_sample_rows": 0,
            "pneuma_ttc_excluded": True,
            "pneuma_quality_columns_present": bool(
                pneuma_quality_audit.get("quality_columns_present", False)
            ),
            "pneuma_quality_semantics": pneuma_quality_audit,
            "pneuma_schema": pneuma_schema,
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
        "schema_version": package_schema_version,
        "experiment_id": "stage_0_5",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scientific_claim_eligible": False,
        "formal_reference_eligible": bool(
            pneuma_schema == "canonical"
            and pneuma_quality_audit.get("formal_reference_eligible", False)
        ),
        "pneuma_schema": pneuma_schema,
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
    if input_manifest is not None:
        audit["input_manifest"] = input_manifest
    (output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _seal_reference(output_dir)
    return output_dir


def _seal_reference(output_dir: Path) -> None:
    # Seal payload files first; the manifest and checksum list describe the
    # payload and the manifest itself, without self-referential checksum lines.
    files = sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
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

# Formal Stage 0.5 R2 input contract and reference rebuild helpers.
FORMAL_STAGE_0_5_RESULT_ID = "RES-STAGE-0.5-REAL-REF-R2"
FORMAL_STAGE_0_5_INPUT_SCHEMA_VERSION = "stage_0_5.real-reference-input.v2"
FORMAL_PNEUMA_SOURCE_SHA256 = "F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C"
FORMAL_STAGE_0_5_EXPECTED_INPUTS = {
    "ngsim_us101__0750_0805.parquet": {
        "relative_path": "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_us101__0750_0805.parquet",
        "sha256": "684a5f0b96dc48116f16d581c278d7039c0554bf1c3cea8d6eda3e605e3e8644",
        "result_id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "role": "highway_following_risk",
        "site": "US-101",
        "window_id": "0750_0805",
    },
    "ngsim_us101__0805_0820.parquet": {
        "relative_path": "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_us101__0805_0820.parquet",
        "sha256": "7b0ef830c97a981da018d4e24b029e38aa2630387c728ea87b57926745880a9f",
        "result_id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "role": "highway_following_risk",
        "site": "US-101",
        "window_id": "0805_0820",
    },
    "ngsim_us101__0820_0835.parquet": {
        "relative_path": "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_us101__0820_0835.parquet",
        "sha256": "a673217765b9a57ed3ea2c743b56fae0c5f538c7517e8e78685721c750082abb",
        "result_id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "role": "highway_following_risk",
        "site": "US-101",
        "window_id": "0820_0835",
    },
    "ngsim_lankershim__complete.parquet": {
        "relative_path": "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states/ngsim_lankershim__complete.parquet",
        "sha256": "650969c29bfe0e604694dc9d4cc5a47076a6d10188bcd81443b55628a713356c",
        "result_id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "role": "urban_following_risk_auxiliary",
        "site": "Lankershim",
        "window_id": "complete",
    },
    "p2_formal_events.parquet": {
        "relative_path": "code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/p2_formal_events.parquet",
        "sha256": "aa749da3c8d68521111cc59f0d0f2746fecef868121d37ae76d3c75d43c10ae1",
        "result_id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "role": "formal_p2_events",
    },
    "stage_0_5_reference_states.parquet": {
        "relative_path": "code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/stage_0_5_reference_states.parquet",
        "sha256": "15893115824c43b00069b13308d9bff5048b92d7d217ac0c38c14523c7d42d65",
        "result_id": "RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3",
        "parent_result_id": "RES-STAGE-0.3-BOUNDARY-REPAIR-R2",
        "role": "urban_kinematics_only",
        "site": "Athens-d1",
        "window_id": "20181101_d1_0800_0830",
    },
}

FORMAL_NGSIM_STATE_REQUIRED = (
    "dataset", "site", "window_id", "vehicle_id", "time_s", "speed_mps",
    "acceleration_mps2", "net_gap_m", "closing_speed_mps", "measurement_status",
)
FORMAL_P2_REQUIRED = (
    "event_id", "dataset", "site", "window_id", "vehicle_id", "leader_id",
    "event_duration_s", "ttc_min_s", "drac_max_mps2", "inclusion_status",
    "algorithm_version", "formal_algorithm_version", "rule", "source",
)


def _canonical_input_entry(repo_root: Path, name: str, spec: dict[str, Any]) -> dict[str, Any]:
    path = (repo_root / spec["relative_path"]).resolve()
    if not path.is_file():
        raise CalibrationContractError(f"formal Stage 0.5 input is missing: {path}")
    actual = sha256_file(path)
    if actual.casefold() != spec["sha256"].casefold():
        raise CalibrationContractError(
            f"formal Stage 0.5 input SHA mismatch for {name}: expected {spec['sha256']}, got {actual}"
        )
    return {
        **spec,
        "name": name,
        "bytes": int(path.stat().st_size),
        "sha256_verified": actual,
        "path": path.relative_to(repo_root.resolve()).as_posix(),
    }


def _validate_formal_ngsim_state(path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    from pyarrow.parquet import ParquetFile

    columns = set(ParquetFile(path).schema_arrow.names)
    missing = sorted(set(FORMAL_NGSIM_STATE_REQUIRED) - columns)
    if missing:
        raise CalibrationContractError(f"NGSIM state missing required columns: {', '.join(missing)}")
    frame = pd.read_parquet(path, columns=list(FORMAL_NGSIM_STATE_REQUIRED))
    if set(frame["dataset"].astype(str).unique()) != {"NGSIM"}:
        raise CalibrationContractError(f"NGSIM state dataset mismatch: {path}")
    if set(frame["site"].astype(str).unique()) != {spec["site"]}:
        raise CalibrationContractError(f"NGSIM state site mismatch: {path}")
    if set(frame["window_id"].astype(str).unique()) != {spec["window_id"]}:
        raise CalibrationContractError(f"NGSIM state window mismatch: {path}")
    for column in ("time_s", "speed_mps", "acceleration_mps2"):
        values = pd.to_numeric(frame[column], errors="coerce")
        if not np.isfinite(values.to_numpy(float)).all():
            raise CalibrationContractError(f"NGSIM state has non-finite {column}: {path}")
    return {
        "state_rows": int(len(frame)),
        "vehicle_count": int(frame["vehicle_id"].nunique()),
        "measurement_status_counts": {
            str(key): int(value) for key, value in frame["measurement_status"].value_counts().items()
        },
    }


def _validate_formal_p2_events(path: Path) -> dict[str, Any]:
    from pyarrow.parquet import ParquetFile

    columns = set(ParquetFile(path).schema_arrow.names)
    missing = sorted(set(FORMAL_P2_REQUIRED) - columns)
    if missing:
        raise CalibrationContractError(f"formal P2 event table missing columns: {', '.join(missing)}")
    events = pd.read_parquet(path)
    if len(events) != 4545:
        raise CalibrationContractError(f"formal P2 event count must be 4545, got {len(events)}")
    if set(events["dataset"].astype(str).unique()) != {"NGSIM"}:
        raise CalibrationContractError("formal P2 event dataset must be NGSIM")
    if set(events["rule"].astype(str).unique()) != {"P2_middle"}:
        raise CalibrationContractError("formal P2 event rule must be P2_middle")
    if set(events["formal_algorithm_version"].astype(str).unique()) != {"stage_0_2.formal_risk_measurement.v2"}:
        raise CalibrationContractError("formal P2 event algorithm version mismatch")
    if set(events["algorithm_version"].astype(str).unique()) != {"stage_0_2.ngsim.reliability.v2"}:
        raise CalibrationContractError("formal P2 event reliability algorithm version mismatch")
    if set(events["inclusion_status"].astype(str).unique()) != {"calibration_candidate"}:
        raise CalibrationContractError("formal P2 event inclusion_status mismatch")
    event_ids = events["event_id"].astype(str)
    if event_ids.eq("").any() or not event_ids.is_unique:
        raise CalibrationContractError("formal P2 event identities must be non-empty and unique")
    expected = {
        ("US-101", "0750_0805"): 543,
        ("US-101", "0805_0820"): 732,
        ("US-101", "0820_0835"): 1043,
        ("Lankershim", "complete"): 2227,
    }
    counts = {
        (str(site), str(window)): int(group.shape[0])
        for (site, window), group in events.groupby(["site", "window_id"], sort=True)
    }
    if counts != expected:
        raise CalibrationContractError(f"formal P2 source counts mismatch: {counts}")
    expected_sources = {
        "lankershim__complete",
        "us101__0750_0805",
        "us101__0805_0820",
        "us101__0820_0835",
    }
    if set(events["source"].astype(str).unique()) != expected_sources:
        raise CalibrationContractError("formal P2 source labels mismatch")
    return {
        "event_rows": int(len(events)),
        "source_counts": {f"{site}::{window}": count for (site, window), count in sorted(counts.items())},
        "rule": "P2_middle",
        "formal_algorithm_version": "stage_0_2.formal_risk_measurement.v2",
    }


def build_formal_stage_0_5_input_manifest(repo_root: str | Path) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    entries = []
    validation: dict[str, Any] = {"ngsim_states": {}, "p2_events": {}, "pneuma": {}}
    for name, spec in FORMAL_STAGE_0_5_EXPECTED_INPUTS.items():
        entry = _canonical_input_entry(repo_root, name, spec)
        path = repo_root / spec["relative_path"]
        if name.endswith(".parquet") and name.startswith("ngsim_"):
            validation["ngsim_states"][name] = _validate_formal_ngsim_state(path, spec)
            entry.update(
                {
                    "schema_version": "stage_0_2.manifest.v1::states",
                    "required_fields": list(FORMAL_NGSIM_STATE_REQUIRED),
                    "quality_contract": {
                        "measurement_status": ["valid", "missing", "invalid", "not_applicable"],
                        "missing_is_not_safe": True,
                        "not_applicable_is_not_zero_risk": True,
                    },
                }
            )
            entry["allowed_metrics"] = [
                "speed_mps", "acceleration_mps2", "net_gap_m", "closing_speed_mps",
                "ttc_s", "ttc_valid", "measurement_status", "p2_exposure",
            ]
        elif name == "p2_formal_events.parquet":
            validation["p2_events"] = _validate_formal_p2_events(path)
            entry.update(
                {
                    "schema_version": "stage_0_2.final_closure.manifest.v1",
                    "required_fields": list(FORMAL_P2_REQUIRED),
                    "quality_contract": {
                        "formal_algorithm_version": "stage_0_2.formal_risk_measurement.v2",
                        "rule": "P2_middle",
                        "event_count": 4545,
                    },
                }
            )
            entry["allowed_metrics"] = ["P2_events", "event_duration_s", "ttc_min_s", "drac_max_mps2"]
        else:
            frame, pneuma_audit = _read_pneuma_reference(path, schema="canonical")
            if set(frame["dataset"].astype(str).unique()) != {"pNEUMA"}:
                raise CalibrationContractError("canonical pNEUMA dataset identity mismatch")
            if set(frame["site"].astype(str).unique()) != {spec["site"]}:
                raise CalibrationContractError("canonical pNEUMA site identity mismatch")
            if set(frame["window_id"].astype(str).unique()) != {spec["window_id"]}:
                raise CalibrationContractError("canonical pNEUMA window identity mismatch")
            source_hashes = {str(value).upper() for value in frame["source_file_sha256"].unique()}
            if source_hashes != {FORMAL_PNEUMA_SOURCE_SHA256}:
                raise CalibrationContractError(
                    "canonical pNEUMA source_file_sha256 does not match the approved Stage 0.3 input"
                )
            pneuma_audit["approved_source_file_sha256"] = FORMAL_PNEUMA_SOURCE_SHA256
            validation["pneuma"] = pneuma_audit
            entry.update(
                {
                    "schema_version": "aad.stage-0-3.manifest.v1::stage_0_5_reference_states",
                    "required_fields": list(CANONICAL_PNEUMA_COLUMNS),
                    "quality_contract": {
                        "quality_status_required": True,
                        "time_weighting_eligible_required": True,
                        "duration_weight_not_present": True,
                        "source_file_sha256": FORMAL_PNEUMA_SOURCE_SHA256,
                        "role": "urban_kinematics_only",
                        "forbidden_metrics": ["front_vehicle", "ttc", "drac", "P2", "risk_events", "map_match"],
                    },
                }
            )
            entry["allowed_metrics"] = ["speed_mps", "acceleration_mps2", "vehicle_type"]
            entry["canonical_schema"] = list(CANONICAL_PNEUMA_COLUMNS)
        entries.append(entry)
    return {
        "schema_version": FORMAL_STAGE_0_5_INPUT_SCHEMA_VERSION,
        "result_id": FORMAL_STAGE_0_5_RESULT_ID,
        "scientific_claim_eligible": False,
        "stage_gate_status": "pending_simulation_sample",
        "approved_references": [
            "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
            "RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3",
            "RES-STAGE-0.3-BOUNDARY-REPAIR-R2",
        ],
        "roles": {
            "US-101": "highway_following_risk_primary",
            "Lankershim": "urban_following_risk_auxiliary",
            "pNEUMA": "urban_kinematics_only",
        },
        "inputs": entries,
        "validation": validation,
    }


def _summary_stats(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {
        "rows": int(len(frame)),
        "vehicles": int(frame["vehicle_id"].nunique()) if "vehicle_id" in frame else None,
    }
    for column in ("speed_mps", "acceleration_mps2", "net_gap_m", "closing_speed_mps"):
        if column not in frame:
            continue
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if values.empty:
            continue
        result[column] = {
            "mean": float(values.mean()),
            "p05": float(values.quantile(0.05)),
            "p50": float(values.quantile(0.50)),
            "p95": float(values.quantile(0.95)),
            "min": float(values.min()),
            "max": float(values.max()),
        }
    if "measurement_status" in frame:
        result["measurement_status_counts"] = {
            str(key): int(value) for key, value in frame["measurement_status"].value_counts().items()
        }
    if "vehicle_type" in frame:
        result["vehicle_type_counts"] = {
            str(key): int(value) for key, value in frame["vehicle_type"].value_counts().items()
        }
    if "time_weighting_eligible" in frame:
        result["time_weighting_eligible_rows"] = int(frame["time_weighting_eligible"].astype(bool).sum())
    return result


def _trajectory_cluster_sample(frame: pd.DataFrame, *, max_rows: int, seed: int) -> pd.DataFrame:
    identity = "trajectory_id" if "trajectory_id" in frame.columns else "vehicle_id"
    group_cols = [column for column in ("dataset", "site", "window_id", identity) if column in frame.columns]
    groups = frame.groupby(group_cols, dropna=False, sort=False).size().rename("_rows").reset_index()
    hashes = pd.util.hash_pandas_object(groups[group_cols].astype("string"), index=False).astype("uint64") ^ np.uint64(seed)
    groups["_hash"] = hashes
    selected = []
    total = 0
    for _, row in groups.sort_values("_hash").iterrows():
        count = int(row["_rows"])
        if selected and total + count > max_rows:
            continue
        selected.append(tuple(row[col] for col in group_cols))
        total += count
        if total >= max_rows:
            break
    if not selected and len(groups):
        row = groups.sort_values("_hash").iloc[0]
        selected = [tuple(row[col] for col in group_cols)]
    if not selected:
        return frame.iloc[0:0].copy()
    selected_frame = frame.merge(pd.DataFrame(selected, columns=group_cols), on=group_cols, how="inner")
    return selected_frame.reset_index(drop=True)


def _build_sampling_sensitivity(repo_root: Path, *, max_rows: int, seed: int) -> dict[str, Any]:
    sensitivity: dict[str, Any] = {"seed": seed, "max_rows": max_rows, "sources": {}}
    state_paths = [
        repo_root / spec["relative_path"]
        for name, spec in FORMAL_STAGE_0_5_EXPECTED_INPUTS.items()
        if name.startswith("ngsim_")
    ]
    for path in state_paths:
        frame = pd.read_parquet(path)
        kinematics = frame.dropna(subset=["speed_mps", "acceleration_mps2"])
        row_sample = deterministic_state_sample(kinematics, max_rows=max_rows, seed=seed)
        cluster_sample = _trajectory_cluster_sample(kinematics, max_rows=max_rows, seed=seed)
        sensitivity["sources"][path.stem] = {
            "full": _summary_stats(kinematics),
            "stable_hash_state_sample": _summary_stats(row_sample),
            "trajectory_cluster_sample": _summary_stats(cluster_sample),
            "interpretation": "diagnostic only; neither bounded sample estimates formal P2 event rate",
        }
    pneuma_path = repo_root / FORMAL_STAGE_0_5_EXPECTED_INPUTS["stage_0_5_reference_states.parquet"]["relative_path"]
    pneuma, _ = _read_pneuma_reference(pneuma_path, schema="canonical")
    row_sample = deterministic_state_sample(pneuma, max_rows=max_rows, seed=seed + 2)
    cluster_sample = _trajectory_cluster_sample(pneuma, max_rows=max_rows, seed=seed + 2)
    sensitivity["sources"]["pNEUMA_Athens-d1"] = {
        "full": _summary_stats(pneuma),
        "stable_hash_state_sample": _summary_stats(row_sample),
        "trajectory_cluster_sample": _summary_stats(cluster_sample),
        "interpretation": "diagnostic only; official R3 time-weighted statistics are cited separately",
    }
    return sensitivity


def _build_independence_audit(repo_root: Path) -> dict[str, Any]:
    frames: dict[str, pd.DataFrame] = {}
    for name, spec in FORMAL_STAGE_0_5_EXPECTED_INPUTS.items():
        if not name.startswith("ngsim_"):
            continue
        path = repo_root / spec["relative_path"]
        frame = pd.read_parquet(path, columns=["site", "window_id", "vehicle_id"])
        frames[name] = frame
    overlaps = []
    names = sorted(frames)
    for i, first_name in enumerate(names):
        for second_name in names[i + 1:]:
            first = set(frames[first_name]["vehicle_id"].astype(str))
            second = set(frames[second_name]["vehicle_id"].astype(str))
            overlap = sorted(first & second)
            overlaps.append({"first": first_name, "second": second_name, "vehicle_id_overlap_count": len(overlap), "vehicle_id_overlap_examples": overlap[:10]})
    return {
        "schema_version": "stage_0_5.source-independence-audit.v1",
        "groups": names,
        "vehicle_id_overlap_pairs": overlaps,
        "pNEUMA_single_file_no_independent_real_group": True,
        "Lankershim_source_period": "unknown",
        "interpretation": "US-101 windows and Lankershim remain separately scoped; this audit does not create real-real iid groups or authorize coverage thresholds",
    }


def write_formal_stage_0_5_reference_r2(
    *, repo_root: str | Path, output_dir: str | Path, max_rows_per_group: int = 5000, seed: int = 20260907
) -> Path:
    repo_root = Path(repo_root).resolve()
    output_dir = Path(output_dir).resolve()
    manifest = build_formal_stage_0_5_input_manifest(repo_root)
    if output_dir.exists():
        raise CalibrationContractError(f"refusing to overwrite formal reference package: {output_dir}")
    state_paths = [repo_root / spec["relative_path"] for name, spec in FORMAL_STAGE_0_5_EXPECTED_INPUTS.items() if name.startswith("ngsim_")]
    pneuma_path = repo_root / FORMAL_STAGE_0_5_EXPECTED_INPUTS["stage_0_5_reference_states.parquet"]["relative_path"]
    events_path = repo_root / FORMAL_STAGE_0_5_EXPECTED_INPUTS["p2_formal_events.parquet"]["relative_path"]
    output = write_real_reference_package(
        ngsim_state_paths=state_paths,
        pneuma_state_path=pneuma_path,
        ngsim_event_path=events_path,
        output_dir=output_dir,
        max_rows_per_group=max_rows_per_group,
        seed=seed,
        pneuma_schema="canonical",
        input_manifest=manifest,
        package_schema_version="stage_0_5.real-reference.v2",
    )
    (output / "input_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    r4_dir = repo_root / "code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4"
    ngsim_metrics = {
        "result_id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "p2_rule": "P2_middle; reliable TTC < 2.0 s; first-last observed span >= 0.2 s",
        "p2_event_rates_by_source": pd.read_csv(r4_dir / "p2_event_rates_by_source.csv").to_dict("records"),
        "measurement_status_by_source": pd.read_csv(r4_dir / "measurement_status_by_source.csv").to_dict("records"),
        "source_files": {
            name: {"path": str((r4_dir / name).relative_to(repo_root).as_posix()), "sha256": sha256_file(r4_dir / name)}
            for name in ("p2_event_rates_by_source.csv", "measurement_status_by_source.csv", "exposure_edge_audit.json")
        },
        "formal_p2_event_table": "p2_formal_events.parquet",
        "sampled_event_rate_forbidden": True,
    }
    (output / "ngsim_formal_metrics.json").write_text(json.dumps(ngsim_metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    r2_dir = repo_root / "code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2"
    summary_files = ("speed_time_weighted_by_type.csv", "acceleration_time_weighted_by_type.csv", "speed_vehicle_equal_weight.csv", "acceleration_vehicle_equal_weight.csv", "vehicle_type_composition.csv", "sampling_balance_audit.csv")
    pneuma_summary = {
        "result_id": "RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3",
        "parent_result_id": "RES-STAGE-0.3-BOUNDARY-REPAIR-R2",
        "role": "urban_kinematics_only",
        "canonical_input_sha256": FORMAL_STAGE_0_5_EXPECTED_INPUTS["stage_0_5_reference_states.parquet"]["sha256"],
        "official_statistics_source": {
            name: {"path": (r2_dir / name).relative_to(repo_root).as_posix(), "sha256": sha256_file(r2_dir / name)}
            for name in summary_files
        },
        "time_weighting_note": "Canonical state table contains eligibility but not interval durations; official R3/R2 sealed summaries are cited instead of pretending to independently recompute duration weights from the canonical table.",
        "statistics": {name: pd.read_csv(r2_dir / name).to_dict("records") for name in summary_files},
    }
    (output / "pneuma_statistics_summary.json").write_text(json.dumps(pneuma_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sampling = _build_sampling_sensitivity(repo_root, max_rows=max_rows_per_group, seed=seed)
    (output / "sampling_sensitivity.json").write_text(json.dumps(sampling, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    independence = _build_independence_audit(repo_root)
    (output / "independence_audit.json").write_text(json.dumps(independence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    config = {
        "schema_version": "stage_0_5.real-reference-config.v2",
        "result_id": FORMAL_STAGE_0_5_RESULT_ID,
        "input_manifest_schema": FORMAL_STAGE_0_5_INPUT_SCHEMA_VERSION,
        "max_rows_per_group": max_rows_per_group,
        "seed": seed,
        "pneuma_schema": "canonical",
        "pneuma_role": "urban_kinematics_only",
        "gate_status": "pending_simulation_sample",
        "scientific_claim_eligible": False,
        "simulation_sample_included": False,
        "formal_thresholds_frozen": False,
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    provenance = {
        "schema_version": "stage_0_5.real-reference-provenance.v2",
        "result_id": FORMAL_STAGE_0_5_RESULT_ID,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "python": sys.version,
        "platform": sys.platform,
        "code_sha256": {"code/src/riskprop/simulation_real_coverage.py": sha256_file(repo_root / "code/src/riskprop/simulation_real_coverage.py")},
        "input_manifest_sha256": sha256_file(output / "input_manifest.json"),
        "no_sumo_run": True,
        "locked_holdout_accessed": False,
    }
    (output / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    audit.update({"result_id": FORMAL_STAGE_0_5_RESULT_ID, "input_manifest_sha256": sha256_file(output / "input_manifest.json"), "statistics_files": ["ngsim_formal_metrics.json", "pneuma_statistics_summary.json", "sampling_sensitivity.json", "independence_audit.json"], "simulation_sample_included": False})
    (output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = """# Stage 0.5 R2 formal real-reference rebuild\n\nThis package rebuilds the approved real references only. US-101 is the primary highway risk reference, Lankershim is an independent auxiliary urban risk reference, and pNEUMA is urban kinematics only. No SUMO sample, calibration, coverage threshold, Gate decision, or Protocol Lock is included.\n\nThe bounded state tables are engineering previews. Formal P2 counts and rates come from the complete Stage 0.2 R4 event and exposure references; sampled rows must not be used to recompute P2 rates. pNEUMA duration-weighted statistics are cited from the sealed Stage 0.3 R2/R3 summaries because the canonical state table carries eligibility but not interval durations.\n"""
    (output / "report.md").write_text(report, encoding="utf-8")
    _seal_reference(output)
    return output
