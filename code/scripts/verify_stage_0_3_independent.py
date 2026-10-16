"""Independent cross-check of the Stage 0.3 package against the raw CSV.

This script deliberately re-implements parsing and aggregation without using
``riskprop.pneuma_urban_kinematics``.  It recomputes the headline counts and
time-weighted statistics and compares them with the sealed package tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
REPO_ROOT = CODE_ROOT.parent

EXPECTED_SHA256 = "F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C"


def _independent_parse(source_csv: Path) -> pd.DataFrame:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 10
    rows = []
    with source_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        next(reader, None)
        for raw in reader:
            values = [v.strip() for v in raw]
            while values and values[-1] == "":
                values.pop()
            track_id, vehicle_type = values[0], values[1]
            for offset in range(4, len(values), 6):
                lat, lon, speed, lon_acc, lat_acc, t = values[offset : offset + 6]
                rows.append((track_id, vehicle_type, float(speed), float(lon_acc), float(t)))
    frame = pd.DataFrame(
        rows, columns=["track_id", "vehicle_type", "speed_kmh", "lon_acc", "time_s"]
    )
    frame["speed_mps"] = frame["speed_kmh"] / 3.6
    return frame


def _independent_identity_and_raw_order(
    source_csv: Path, frame: pd.DataFrame, tolerance_s: float
) -> dict:
    """Row/identity/raw-order checks recomputed without the production module.

    The wide rows are streamed in file order and each track's state chunks are
    appended in file order, so ``frame`` preserves raw record order.
    """

    raw_rows = 0
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    with source_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        next(reader, None)
        for raw in reader:
            values = [v.strip() for v in raw]
            while values and values[-1] == "":
                values.pop()
            if not values:
                continue
            raw_rows += 1
            track_id = values[0]
            if track_id in seen_ids:
                duplicate_ids.add(track_id)
            seen_ids.add(track_id)
    regression_edges = 0
    nonpositive_edges = 0
    gap_edges = 0
    eligible_edges = 0
    duplicate_time_keys = 0
    for track_id, group in frame.groupby("track_id", sort=False):
        t = group["time_s"].to_numpy(float)
        increments = np.diff(t)
        regression_edges += int((increments < 0).sum())
        nonpositive_edges += int((increments <= 0).sum())
        positive = increments[increments > 0]
        gap_edges += int((positive > tolerance_s).sum())
        eligible_edges += int(((positive > 0) & (positive <= tolerance_s)).sum())
        duplicate_time_keys += int(
            group.duplicated(subset=["track_id", "time_s"], keep=False).sum()
        )
    return {
        "raw_track_rows": raw_rows,
        "unique_track_ids": len(seen_ids),
        "duplicate_track_ids": sorted(duplicate_ids),
        "regression_raw_order_edges": regression_edges,
        "nonpositive_raw_order_edges": nonpositive_edges,
        "time_gap_states": gap_edges,
        "eligible_states": eligible_edges,
        "duplicate_state_keys": duplicate_time_keys,
    }


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    total = float(cumulative[-1])
    index = int(np.searchsorted(cumulative, q * total, side="left"))
    return float(values[order][min(index, len(values) - 1)])


def _independent_time_weighted(frame: pd.DataFrame, tolerance_s: float, value_column: str):
    """Raw-record-order left-rectangle weighting, independently implemented.

    Groups keep file order (raw record order); no time sorting is applied, so
    an out-of-order recording could never be repaired here either.
    """

    totals: dict[str, dict[str, float]] = {}
    overall_sum = 0.0
    overall_time = 0.0
    overall_values: list[np.ndarray] = []
    overall_weights: list[np.ndarray] = []
    per_type_values: dict[str, list[np.ndarray]] = {}
    per_type_weights: dict[str, list[np.ndarray]] = {}
    for track_id, group in frame.groupby("track_id", sort=False):
        t = group["time_s"].to_numpy(float)
        v = group[value_column].to_numpy(float)
        dt = np.diff(t)
        usable = (dt > 0) & (dt <= tolerance_s)
        w = np.where(usable, dt, 0.0)
        v = v[:-1]
        w = w
        total_time = float(w.sum())
        if total_time <= 0:
            continue
        vehicle_type = group["vehicle_type"].iloc[0]
        bucket = totals.setdefault(vehicle_type, {"sum": 0.0, "time": 0.0})
        bucket["sum"] += float((v * w).sum())
        bucket["time"] += total_time
        overall_sum += float((v * w).sum())
        overall_time += total_time
        overall_values.append(v)
        overall_weights.append(w)
        per_type_values.setdefault(vehicle_type, []).append(v)
        per_type_weights.setdefault(vehicle_type, []).append(w)
    results = {"ALL": (overall_sum, overall_time)}
    results.update({k: (v["sum"], v["time"]) for k, v in totals.items()})
    quantiles = {"ALL": (np.concatenate(overall_values), np.concatenate(overall_weights))}
    quantiles.update(
        {k: (np.concatenate(vv), np.concatenate(ww)) for k, (vv, ww) in
         ((key, (per_type_values[key], per_type_weights[key])) for key in per_type_values)}
    )
    return results, quantiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-csv", type=Path, default=REPO_ROOT / "dataset" / "pNEUMA" / "20181101_d1_0800_0830.csv")
    parser.add_argument(
        "--allow-unknown-source-sha",
        action="store_true",
        help="smoke-test escape hatch; result is recorded as not SHA-pinned",
    )
    args = parser.parse_args()

    package = args.package
    source_csv = args.source_csv.resolve()

    from riskprop.calibration import sha256_file

    digest = sha256_file(source_csv).upper()
    if not args.allow_unknown_source_sha and digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected source sha256: {digest}")

    frame = _independent_parse(source_csv)
    audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
    tolerance_s = float(audit["anchor_tolerance_s"])

    independent_audit = _independent_identity_and_raw_order(source_csv, frame, tolerance_s)

    speed_tw = pd.read_csv(package / "speed_time_weighted_by_type.csv")
    accel_tw = pd.read_csv(package / "acceleration_time_weighted_by_type.csv")
    composition = pd.read_csv(package / "vehicle_type_composition.csv")

    discrepancies: list[str] = []

    # Identity and raw record order (R2 boundary semantics).
    if int(independent_audit["raw_track_rows"]) != int(audit["raw_track_rows"]):
        discrepancies.append(
            f"raw track rows mismatch: independent {independent_audit['raw_track_rows']} "
            f"vs audit {audit['raw_track_rows']}"
        )
    if int(independent_audit["unique_track_ids"]) != int(audit["unique_track_ids"]):
        discrepancies.append(
            f"unique track ids mismatch: independent {independent_audit['unique_track_ids']} "
            f"vs audit {audit['unique_track_ids']}"
        )
    if len(independent_audit["duplicate_track_ids"]) != len(audit["duplicate_track_ids"]):
        discrepancies.append(
            f"duplicate track ids mismatch: independent {independent_audit['duplicate_track_ids']} "
            f"vs audit {audit['duplicate_track_ids']}"
        )
    raw_order_audit = audit.get("raw_order_time_audit", {})
    for key, audit_key in (
        ("regression_raw_order_edges", "regression_raw_order_edges"),
        ("nonpositive_raw_order_edges", "nonpositive_raw_order_edges"),
        ("time_gap_states", "time_gap_states"),
        ("eligible_states", "eligible_states"),
        ("duplicate_state_keys", None),
    ):
        if audit_key is None:
            expected = int(audit["duplicate_state_keys"])
        else:
            if audit_key not in raw_order_audit:
                discrepancies.append(f"audit missing raw_order_time_audit.{audit_key}")
                continue
            expected = int(raw_order_audit[audit_key])
        if int(independent_audit[key]) != expected:
            discrepancies.append(
                f"raw-order audit mismatch for {key}: independent {independent_audit[key]} vs audit {expected}"
            )
    clean_raw_order = (
        int(independent_audit["nonpositive_raw_order_edges"]) == 0
        and int(independent_audit["duplicate_state_keys"]) == 0
    )
    if not clean_raw_order:
        # Eligibility additionally excludes quality-flagged states; an exact
        # edge-count comparison is only meaningful for a clean raw order.
        discrepancies.append(
            "independent raw-order audit found anomalies; package eligibility "
            "cannot be cross-checked by pure interval counting"
        )

    # Stage 0.5 reference quality semantics.
    reference_path = package / "stage_0_5_reference_states.parquet"
    if reference_path.is_file():
        reference = pd.read_parquet(reference_path)
        reference_eligible = int(reference["time_weighting_eligible"].sum())
        if reference_eligible != int(independent_audit["eligible_states"]):
            discrepancies.append(
                f"reference eligible states mismatch: package {reference_eligible} vs "
                f"independent {independent_audit['eligible_states']}"
            )
        package_quality_counts = {
            str(key): int(value)
            for key, value in reference["quality_status"].value_counts().items()
        }
        audit_quality_counts = {
            str(key): int(value)
            for key, value in audit["stage_0_5_reference_quality_counts"].items()
        }
        if package_quality_counts != audit_quality_counts:
            discrepancies.append(
                f"reference quality counts mismatch: package {package_quality_counts} vs "
                f"audit {audit_quality_counts}"
            )
    else:
        discrepancies.append("stage_0_5_reference_states.parquet missing from package")

    # Counts.
    if int(frame["track_id"].nunique()) != int(audit["unique_tracks"]):
        discrepancies.append(
            f"unique tracks mismatch: independent {frame['track_id'].nunique()} vs audit {audit['unique_tracks']}"
        )
    if int(len(frame)) != int(audit["parsed_state_records"]):
        discrepancies.append(
            f"state records mismatch: independent {len(frame)} vs audit {audit['parsed_state_records']}"
        )
    independent_types = Counter(frame.groupby("track_id")["vehicle_type"].first())
    for row in composition.itertuples(index=False):
        if int(independent_types.get(row.vehicle_type, 0)) != int(row.unique_trajectories):
            discrepancies.append(
                f"vehicle type count mismatch for {row.vehicle_type}: independent "
                f"{independent_types.get(row.vehicle_type, 0)} vs package {row.unique_trajectories}"
            )

    # Time-weighted statistics.
    speed_totals, speed_quantiles = _independent_time_weighted(frame, tolerance_s, "speed_mps")
    accel_totals, _ = _independent_time_weighted(frame, tolerance_s, "lon_acc")
    for label, (total_sum, total_time) in speed_totals.items():
        package_row = speed_tw[speed_tw["group"] == label]
        if package_row.empty:
            discrepancies.append(f"missing package speed row for group {label}")
            continue
        package_row = package_row.iloc[0]
        mean = total_sum / total_time
        if not np.isclose(mean, package_row["mean"], rtol=1e-9, atol=1e-9):
            discrepancies.append(
                f"speed mean mismatch for {label}: independent {mean} vs package {package_row['mean']}"
            )
        if not np.isclose(total_time, package_row["exposure_time_s"], rtol=1e-9, atol=1e-6):
            discrepancies.append(
                f"speed exposure mismatch for {label}: independent {total_time} vs package {package_row['exposure_time_s']}"
            )
        v, w = speed_quantiles[label]
        p50 = _weighted_quantile(v, w, 0.5)
        if not np.isclose(p50, package_row["p50"], rtol=1e-9, atol=1e-9):
            discrepancies.append(
                f"speed p50 mismatch for {label}: independent {p50} vs package {package_row['p50']}"
            )
    for label, (total_sum, total_time) in accel_totals.items():
        package_row = accel_tw[accel_tw["group"] == label]
        if package_row.empty:
            discrepancies.append(f"missing package accel row for group {label}")
            continue
        package_row = package_row.iloc[0]
        mean = total_sum / total_time
        if not np.isclose(mean, package_row["mean"], rtol=1e-9, atol=1e-9):
            discrepancies.append(
                f"accel mean mismatch for {label}: independent {mean} vs package {package_row['mean']}"
            )

    # Checksum verification.
    from riskprop.calibration import validate_checksum_package

    try:
        validate_checksum_package(package)
    except Exception as exc:  # noqa: BLE001
        discrepancies.append(f"checksum package invalid: {exc}")

    result = {
        "schema_version": "aad.stage-0-3.independent-verification.v1",
        "package": str(package.as_posix()),
        "tolerance_s": tolerance_s,
        "source_sha_pin_enforced": not args.allow_unknown_source_sha,
        "independent_tracks": int(frame["track_id"].nunique()),
        "independent_states": int(len(frame)),
        "independent_raw_track_rows": int(independent_audit["raw_track_rows"]),
        "independent_raw_order_audit": {
            key: value for key, value in independent_audit.items() if key != "duplicate_track_ids"
        },
        "independent_duplicate_track_ids": independent_audit["duplicate_track_ids"],
        "package_tracks": int(audit["unique_tracks"]),
        "package_states": int(audit["parsed_state_records"]),
        "discrepancies": discrepancies,
        "pass": not discrepancies,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not discrepancies else 1


if __name__ == "__main__":
    raise SystemExit(main())
