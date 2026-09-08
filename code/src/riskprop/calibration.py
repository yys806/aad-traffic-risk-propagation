"""Frozen input and measurement contracts for E15-A/E17-A calibration.

This module deliberately contains no treatment-effect analysis.  Its outputs are
calibration infrastructure and are never eligible for a scientific main claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


class CalibrationContractError(ValueError):
    """Raised when calibration inputs violate the preregistered contract."""


REAL_STATE_COLUMNS = (
    "dataset",
    "site",
    "window_id",
    "vehicle_id",
    "time_s",
    "x_m",
    "y_m",
    "speed_mps",
    "acceleration_mps2",
    "road_id",
    "lane_id",
    "leader_id",
    "net_gap_m",
    "closing_speed_mps",
    "measurement_status",
    "missing_reason",
)

RISK_EVENT_COLUMNS = (
    "event_id",
    "dataset",
    "site",
    "window_id",
    "vehicle_id",
    "leader_id",
    "conflict_type",
    "event_start_s",
    "event_end_s",
    "event_duration_s",
    "ttc_min_s",
    "drac_max_mps2",
    "pet_s",
    "inclusion_status",
    "exclusion_reason",
    "algorithm_version",
    "raw_frame_count",
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_default_calibration_manifests(repo_root: str | Path) -> tuple[dict, dict]:
    """Build the fixed AAD calibration inventory without opening holdout records."""

    repo_root = Path(repo_root).resolve()
    data_root = repo_root / "docs" / "归档" / "真实数据与NC文献调研" / "datasets"
    specifications = (
        (
            "ngsim_us101",
            "NGSIM",
            "US-101",
            data_root / "NGSIM" / "US-101-LosAngeles-CA.zip",
            "calibration",
            "trajectory risk measurement and physical-state calibration only",
        ),
        (
            "ngsim_lankershim",
            "NGSIM",
            "Lankershim",
            data_root / "NGSIM" / "Lankershim-Boulevard-LosAngeles-CA.zip",
            "calibration",
            "trajectory risk measurement and physical-state calibration only",
        ),
        (
            "pneuma_d1_0800_0830",
            "pNEUMA",
            "Athens-d1",
            data_root / "pNEUMA" / "20181101_d1_0800_0830.csv",
            "calibration",
            "trajectory fields; leader-aware risk only after map-match gate",
        ),
        (
            "pneuma_d1_osm_20260907",
            "OpenStreetMap",
            "Athens-d1",
            data_root / "pNEUMA" / "osm" / "athens_d1_bbox_20260907.osm",
            "calibration",
            "frozen road-map snapshot for pNEUMA map matching; ODbL, OpenStreetMap contributors",
        ),
        (
            "ngsim_i80",
            "NGSIM",
            "I-80",
            data_root / "NGSIM" / "I-80-Emeryville-CA.zip",
            "locked_holdout",
            "registered only; scientific contents remain sealed in this phase",
        ),
        (
            "ngsim_peachtree",
            "NGSIM",
            "Peachtree",
            data_root / "NGSIM" / "Peachtree-Street-Atlanta-GA.zip",
            "locked_holdout",
            "registered only; scientific contents remain sealed in this phase",
        ),
        (
            "spmd_rv_rx",
            "SPMD",
            "Ann-Arbor",
            data_root / "SPMD" / "selected" / "RV_RX.csv.zip",
            "partitioned_by_trip",
            "receive-state continuity only; not packet loss, latency, or adoption",
        ),
    )
    assets = []
    for asset_id, dataset, site, path, role, boundary in specifications:
        if not path.is_file():
            raise FileNotFoundError(f"Required calibration asset is missing: {path}")
        assets.append(
            {
                "asset_id": asset_id,
                "dataset": dataset,
                "site": site,
                "relative_path": path.relative_to(repo_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "split_role": role,
                "evidence_boundary": boundary,
            }
        )

    data_manifest = {
        "schema_version": "aad.calibration-data.v2",
        "scientific_claim_eligible": False,
        "holdout_contents_inspected": False,
        "assets": assets,
    }
    split_manifest = {
        "schema_version": "aad.calibration-split.v2",
        "split_unit": "complete site/window or complete trip; never frame",
        "calibration": [
            "ngsim_us101",
            "ngsim_lankershim",
            "pneuma_d1_0800_0830",
            "pneuma_d1_osm_20260907",
            "spmd_rv_rx_calibration_trips",
        ],
        "locked_holdout": [
            "ngsim_i80",
            "ngsim_peachtree",
            "spmd_rv_rx_holdout_trips",
        ],
        "spmd_trip_partition": {
            "method": "sha256(DeviceID|Trip) first byte",
            "calibration_rule": "byte < 128",
            "locked_holdout_rule": "byte >= 128",
            "holdout_values_materialized": False,
        },
    }
    validate_split_manifest(split_manifest)
    return data_manifest, split_manifest


def validate_split_manifest(split_manifest: dict) -> None:
    calibration = set(split_manifest.get("calibration", []))
    holdout = set(split_manifest.get("locked_holdout", []))
    overlap = sorted(calibration & holdout)
    if overlap:
        raise CalibrationContractError(
            f"calibration/locked_holdout overlap: {', '.join(overlap)}"
        )
    if not calibration or not holdout:
        raise CalibrationContractError("both calibration and locked_holdout must be non-empty")


def write_frozen_calibration_manifests(
    output_dir: str | Path, data_manifest: dict, split_manifest: dict
) -> Path:
    """Write an immutable manifest package and refuse replacement."""

    validate_split_manifest(split_manifest)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    payloads = {
        "data_manifest.json": data_manifest,
        "split_manifest.json": split_manifest,
    }
    checksum_lines = []
    for name, payload in payloads.items():
        path = output_dir / name
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        checksum_lines.append(f"{sha256_file(path)}  {name}")
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n"
    )
    return output_dir


def validate_checksum_package(output_dir: str | Path) -> dict:
    """Recompute every path listed in SHA256SUMS from read-only files."""

    output_dir = Path(output_dir)
    checksum_path = output_dir / "SHA256SUMS"
    if not checksum_path.is_file():
        raise CalibrationContractError("checksum package is missing SHA256SUMS")
    entries = []
    for line_number, line in enumerate(
        checksum_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError as error:
            raise CalibrationContractError(
                f"invalid SHA256SUMS line {line_number}"
            ) from error
        target = (output_dir / relative).resolve()
        try:
            target.relative_to(output_dir.resolve())
        except ValueError as error:
            raise CalibrationContractError(f"unsafe checksum path: {relative}") from error
        if not target.is_file():
            raise CalibrationContractError(f"checksum target missing: {relative}")
        actual = sha256_file(target)
        if actual.casefold() != expected.casefold():
            raise CalibrationContractError(f"checksum mismatch: {relative}")
        entries.append(relative)
    if not entries:
        raise CalibrationContractError("SHA256SUMS contains no entries")
    return {"pass": True, "verified_files": entries}


def validate_real_state_table(frame: pd.DataFrame) -> None:
    _require_columns(frame, REAL_STATE_COLUMNS, "real-state")
    missing = frame["measurement_status"].astype(str).eq("missing")
    reasons = frame["missing_reason"].fillna("").astype(str).str.strip()
    if (missing & reasons.eq("")).any():
        raise CalibrationContractError(
            "missing measurements require a non-empty missing_reason; never encode missing as zero"
        )
    if frame.loc[missing, ["net_gap_m", "closing_speed_mps"]].eq(0.0).any(axis=None):
        raise CalibrationContractError(
            "missing net gap/closing speed cannot be silently encoded as zero"
        )


def validate_risk_event_table(frame: pd.DataFrame) -> None:
    _require_columns(frame, RISK_EVENT_COLUMNS, "risk-event")
    starts = pd.to_numeric(frame["event_start_s"], errors="coerce")
    ends = pd.to_numeric(frame["event_end_s"], errors="coerce")
    durations = pd.to_numeric(frame["event_duration_s"], errors="coerce")
    raw_counts = pd.to_numeric(frame["raw_frame_count"], errors="coerce")
    if ((raw_counts <= 1) & (durations <= 0)).any():
        raise CalibrationContractError(
            "frame-level detections cannot be treated as independent risk events"
        )
    if ((ends < starts) | ((ends - starts - durations).abs() > 1e-9)).any():
        raise CalibrationContractError("event boundaries and event_duration_s disagree")


def select_blind_audit_windows(
    candidates: pd.DataFrame, *, total: int = 300, seed: int
) -> pd.DataFrame:
    """Select equal preregistered strata and replace event IDs with blind IDs."""

    strata = ("algorithm_positive", "near_threshold", "random_negative")
    if total < len(strata) or total % len(strata):
        raise ValueError("total must be a positive multiple of three")
    _require_columns(candidates, ("event_id", "audit_category"), "audit-candidate")
    per_stratum = total // len(strata)
    selected = []
    for offset, stratum in enumerate(strata):
        subset = candidates[candidates["audit_category"] == stratum]
        if len(subset) < per_stratum:
            raise CalibrationContractError(
                f"audit stratum {stratum} has {len(subset)} rows; need {per_stratum}"
            )
        selected.append(subset.sample(n=per_stratum, random_state=seed + offset))
    result = pd.concat(selected, ignore_index=True)
    result["blind_id"] = result["event_id"].map(
        lambda value: hashlib.sha256(f"{seed}|{value}".encode()).hexdigest()[:16]
    )
    result = result.drop(
        columns=[
            column
            for column in result.columns
            if column.startswith("algorithm_") and column != "audit_category"
        ]
    )
    return result.sort_values("blind_id").reset_index(drop=True)


def build_blind_audit_exports(
    selected: pd.DataFrame, *, round_number: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate a human-facing blind sheet from the sealed sampling key."""

    if round_number not in {1, 2, 3}:
        raise ValueError("round_number must be 1, 2, or 3")
    _require_columns(
        selected,
        ("blind_id", "event_id", "audit_category"),
        "selected blind-audit",
    )
    sensitive = {
        "event_id",
        "audit_category",
        *(column for column in selected.columns if column.startswith("algorithm_")),
    }
    review = selected.drop(
        columns=[column for column in sensitive if column in selected.columns]
    ).copy()
    review["review_round"] = round_number
    review["reviewer_risk_label"] = ""
    review["reviewer_leader_correct"] = ""
    review["reviewer_event_start_s"] = ""
    review["reviewer_event_end_s"] = ""
    review["reviewer_uncertain"] = ""
    review["reviewer_notes"] = ""
    key_columns = [
        "blind_id",
        "event_id",
        "audit_category",
        *[
            column
            for column in selected.columns
            if column.startswith("algorithm_") and column != "audit_category"
        ],
    ]
    key = selected.loc[:, list(dict.fromkeys(key_columns))].copy()
    return review.reset_index(drop=True), key.reset_index(drop=True)


def cohens_kappa(first: Sequence[str], second: Sequence[str]) -> float:
    if len(first) != len(second) or not first:
        raise ValueError("two non-empty label sequences of equal length are required")
    labels = sorted(set(first) | set(second))
    observed = sum(a == b for a, b in zip(first, second, strict=True)) / len(first)
    first_p = {label: first.count(label) / len(first) for label in labels}
    second_p = {label: second.count(label) / len(second) for label in labels}
    expected = sum(first_p[label] * second_p[label] for label in labels)
    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else 0.0
    return (observed - expected) / (1.0 - expected)


def fit_robust_scaler(reference: pd.DataFrame, columns: Sequence[str]) -> dict:
    """Freeze median/IQR scaling from real calibration data only."""

    if reference.empty:
        raise ValueError("reference calibration data cannot be empty")
    values = reference.loc[:, columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if not np.isfinite(values).all():
        raise CalibrationContractError("reference scaler inputs must be finite")
    centre = np.median(values, axis=0)
    q75, q25 = np.percentile(values, [75, 25], axis=0)
    scale = np.where((q75 - q25) > 0, q75 - q25, 1.0)
    return {
        "reference": "real_calibration",
        "columns": list(columns),
        "centre": centre.tolist(),
        "scale": scale.tolist(),
    }


def energy_distance(
    first: pd.DataFrame,
    second: pd.DataFrame,
    columns: Sequence[str],
    *,
    scaler: dict | None = None,
) -> float:
    """Multivariate energy distance under one frozen real-data scaler."""

    if first.empty or second.empty:
        raise ValueError("energy distance requires two non-empty samples")
    first_values = first.loc[:, columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    second_values = second.loc[:, columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if not np.isfinite(first_values).all() or not np.isfinite(second_values).all():
        raise CalibrationContractError("energy-distance inputs must be finite")
    scaler = fit_robust_scaler(first, columns) if scaler is None else scaler
    if list(scaler.get("columns", [])) != list(columns):
        raise CalibrationContractError("scaler columns do not match distance columns")
    centre = np.asarray(scaler.get("centre"), dtype=float)
    scale = np.asarray(scaler.get("scale"), dtype=float)
    if centre.shape != (len(columns),) or scale.shape != (len(columns),):
        raise CalibrationContractError("scaler has an invalid shape")
    if not np.isfinite(centre).all() or not np.isfinite(scale).all() or (scale <= 0).any():
        raise CalibrationContractError("scaler must contain finite positive scales")
    x = (first_values - centre) / scale
    y = (second_values - centre) / scale
    xy = _mean_pairwise_distance(x, y)
    xx = _mean_pairwise_distance(x, x)
    yy = _mean_pairwise_distance(y, y)
    return float(max(2.0 * xy - xx - yy, 0.0))


def _mean_pairwise_distance(
    first: np.ndarray, second: np.ndarray, *, block_rows: int = 512
) -> float:
    """Compute the exact mean distance without allocating the full N×M matrix."""

    if block_rows < 1:
        raise ValueError("block_rows must be positive")
    total = 0.0
    count = 0
    for start in range(0, len(first), block_rows):
        block = first[start : start + block_rows]
        distances = np.linalg.norm(block[:, None, :] - second[None, :, :], axis=2)
        total += float(distances.sum())
        count += distances.size
    return total / count


def _require_columns(frame: pd.DataFrame, required: Iterable[str], label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise CalibrationContractError(
            f"{label} table is missing required columns: {', '.join(missing)}"
        )
