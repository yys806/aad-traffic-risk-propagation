"""Run the read-only Stage 0.2 NGSIM risk-quality and event-rule audit."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from riskprop.ngsim_risk_calibration import extract_rear_end_events


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4"
DEFAULT_OUTPUT = ROOT / "code/outputs/formal/calibration/stage_0_2_task_2_risk_quality_audit_20261010"
STATE_COLUMNS = [
    "speed_mps", "acceleration_mps2", "raw_space_headway_ft", "net_gap_m",
    "closing_speed_mps", "ttc_s", "drac_mps2",
]
CORE_COLUMNS = ["vehicle_id", "time_s", "net_gap_m", "closing_speed_mps", "ttc_valid", "ttc_s", "drac_mps2", "measurement_status"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_input_package(input_dir: Path) -> dict[str, object]:
    sums_path = input_dir / "SHA256SUMS"
    expected: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(None, 1)
        expected[relative.strip()] = digest
    checked = {}
    for relative, digest in expected.items():
        path = input_dir / relative
        checked[relative] = {"exists": path.exists(), "sha256": sha256_file(path) if path.exists() else None, "expected": digest}
        if not path.exists() or checked[relative]["sha256"] != digest:
            raise ValueError(f"input package hash mismatch: {relative}")
    return {"sha256sums": str(sums_path), "files_checked": len(checked), "files": checked}


def finite(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).notna()


def quantile_summary(frame: pd.DataFrame, column: str) -> dict[str, object]:
    values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return {"n": 0}
    quantiles = values.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999])
    return {
        "n": int(values.size),
        "min": float(values.min()), "max": float(values.max()),
        "mean": float(values.mean()), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "p01": float(quantiles.loc[0.01]), "p05": float(quantiles.loc[0.05]),
        "p25": float(quantiles.loc[0.25]), "p50": float(quantiles.loc[0.5]),
        "p75": float(quantiles.loc[0.75]), "p95": float(quantiles.loc[0.95]),
        "p99": float(quantiles.loc[0.99]), "p999": float(quantiles.loc[0.999]),
    }


def quality_summary(frame: pd.DataFrame) -> dict[str, object]:
    n = len(frame)
    status = frame["measurement_status"].fillna("missing").value_counts(dropna=False).to_dict()
    def count(mask: pd.Series) -> int:
        return int(mask.fillna(False).sum())
    ttc_finite = finite(frame["ttc_s"])
    drac_finite = finite(frame["drac_mps2"])
    out = {
        "rows": n,
        "measurement_status": {str(k): {"n": int(v), "fraction_of_rows": float(v / n) if n else None} for k, v in status.items()},
        "leader_matched": {"n": count(frame["leader_matched"]), "fraction_of_rows": count(frame["leader_matched"]) / n if n else None},
        "single_frame_reliable": {"n": count(frame["single_frame_reliable"]), "fraction_of_rows": count(frame["single_frame_reliable"]) / n if n else None},
        "positive_net_gap": {"n": count(pd.to_numeric(frame["net_gap_m"], errors="coerce") > 0), "fraction_of_rows": count(pd.to_numeric(frame["net_gap_m"], errors="coerce") > 0) / n if n else None},
        "positive_closing_speed": {"n": count(pd.to_numeric(frame["closing_speed_mps"], errors="coerce") > 0), "fraction_of_rows": count(pd.to_numeric(frame["closing_speed_mps"], errors="coerce") > 0) / n if n else None},
        "finite_ttc": {"n": int(ttc_finite.sum()), "fraction_of_rows": float(ttc_finite.mean()) if n else None},
        "finite_drac": {"n": int(drac_finite.sum()), "fraction_of_rows": float(drac_finite.mean()) if n else None},
        "nan_or_inf_ttc": int((~ttc_finite).sum()),
        "nan_or_inf_drac": int((~drac_finite).sum()),
        "identity_uncertain_rows": count(frame["identity_uncertain"]),
        "leader_identity_uncertain_rows": count(frame["leader_identity_uncertain"]),
        "observation_gap_rows": count(frame["observation_gap"]),
        "identity_break_rows": count(frame["identity_break"]),
        "diagnostic_extremes": {
            "ttc_lt_0_5_s": count(frame["ttc_valid"] & (frame["ttc_s"] < 0.5)),
            "ttc_0_5_to_1_s": count(frame["ttc_valid"] & frame["ttc_s"].between(0.5, 1.0, inclusive="left")),
            "drac_gt_10_mps2": count(frame["ttc_valid"] & (frame["drac_mps2"] > 10)),
            "net_gap_lt_1_m": count(frame["ttc_valid"] & (frame["net_gap_m"] < 1)),
            "closing_speed_gt_15_mps": count(frame["ttc_valid"] & (frame["closing_speed_mps"] > 15)),
        },
        "subset_counts": {
            "all_rows": n,
            "mathematically_valid_ttc": count(frame["ttc_valid"]),
            "identity_reliable_ttc": count(frame["single_frame_reliable"]),
            "no_explicit_constraint_conflict": count(frame["ttc_valid"] & ~frame["identity_uncertain"] & ~frame["leader_identity_uncertain"]),
            "exploratory_non_extreme_ttc": count(frame["ttc_valid"] & (frame["ttc_s"] >= 0.5) & (frame["drac_mps2"] <= 10) & (frame["net_gap_m"] >= 1)),
        },
    }
    out["variable_summary"] = {column: quantile_summary(frame, column) for column in STATE_COLUMNS}
    out["reliable_variable_summary"] = {column: quantile_summary(frame[frame["single_frame_reliable"]], column) for column in STATE_COLUMNS}
    return out


def event_grid(frame: pd.DataFrame, thresholds: list[float], durations: list[float], max_gap: float) -> list[dict[str, object]]:
    rows = []
    for threshold in thresholds:
        # Re-extract from the complete state sequence once per TTC threshold.
        # Duration is an event-level inclusion filter in the implementation, so
        # applying it to this freshly extracted result avoids repeating the
        # expensive full-sequence sort for every duration value.
        raw_all, reliable_all, rejected_all = extract_rear_end_events(
            frame, provisional_ttc_threshold_s=threshold, max_gap_s=max_gap,
            minimum_duration_s=1e-9, return_diagnostics=True,
        )
        low_frames = int((frame["ttc_valid"] & (frame["ttc_s"] < threshold)).sum())
        for duration in durations:
            raw = raw_all[raw_all["event_duration_s"] + 1e-12 >= duration].copy()
            reliable = reliable_all[reliable_all["event_duration_s"] + 1e-12 >= duration].copy()
            kept_ids = set(raw["event_id"])
            rejected = rejected_all[rejected_all["event_id"].isin(kept_ids)].copy()
            rows.append({
                "ttc_threshold_s": threshold, "minimum_duration_s": duration, "max_gap_s": max_gap,
                "low_ttc_frame_count": low_frames, "raw_event_count": len(raw),
                "reliable_event_count": len(reliable), "rejected_event_count": len(rejected),
                "rejection_reason_counts": {str(k): int(v) for k, v in rejected["rejection_reason"].value_counts().items()} if not rejected.empty else {},
                "event_vehicle_pairs": int(reliable[["trajectory_id", "leader_trajectory_id"]].drop_duplicates().shape[0]) if not reliable.empty else 0,
                "event_trajectory_count": int(reliable["trajectory_id"].nunique()) if not reliable.empty else 0,
                "duration_summary": quantile_summary(reliable.rename(columns={"event_duration_s": "duration"}), "duration") if not reliable.empty else {"n": 0},
                "ttc_min_summary": quantile_summary(reliable.rename(columns={"ttc_min_s": "ttc_min"}), "ttc_min") if not reliable.empty else {"n": 0},
                "drac_max_summary": quantile_summary(reliable.rename(columns={"drac_max_mps2": "drac_max"}), "drac_max") if not reliable.empty else {"n": 0},
            })
    return rows


def make_figures(frames: dict[str, pd.DataFrame], output_dir: Path) -> list[str]:
    rng = np.random.default_rng(20261010)
    samples = []
    for name, frame in frames.items():
        valid = frame[frame["ttc_valid"] & finite(frame["ttc_s"])].copy()
        if len(valid) > 100_000:
            valid = valid.iloc[np.sort(rng.choice(len(valid), 100_000, replace=False))]
        valid["source"] = name
        samples.append(valid[["source", "ttc_s", "drac_mps2", "net_gap_m", "closing_speed_mps", "speed_mps", "acceleration_mps2"]])
    data = pd.concat(samples, ignore_index=True)
    paths = []
    plt.figure(figsize=(10, 6))
    for source, group in data.groupby("source", sort=False):
        values = group.loc[group["ttc_s"] > 0, "ttc_s"]
        plt.hist(values, bins=np.logspace(-1, 2, 80), histtype="step", linewidth=1.2, label=source, density=True)
    plt.xscale("log"); plt.xlabel("TTC (s)"); plt.ylabel("Density"); plt.legend(fontsize=7); plt.tight_layout()
    path = output_dir / "ttc_distribution_log.png"; plt.savefig(path, dpi=160); plt.close(); paths.append(path.name)
    plt.figure(figsize=(10, 6))
    for source, group in data.groupby("source", sort=False):
        plt.scatter(group["net_gap_m"], group["closing_speed_mps"], s=2, alpha=0.12, label=source)
    plt.xscale("symlog", linthresh=0.1); plt.xlabel("Net gap (m)"); plt.ylabel("Closing speed (m/s)"); plt.legend(fontsize=7); plt.tight_layout()
    path = output_dir / "gap_closing_joint.png"; plt.savefig(path, dpi=160); plt.close(); paths.append(path.name)
    plt.figure(figsize=(10, 6))
    for source, group in data.groupby("source", sort=False):
        values = group.loc[group["drac_mps2"] > 0, "drac_mps2"]
        plt.hist(values, bins=np.logspace(-2, 2, 80), histtype="step", linewidth=1.2, label=source, density=True)
    plt.xscale("log"); plt.xlabel("DRAC (m/s²)"); plt.ylabel("Density"); plt.legend(fontsize=7); plt.tight_layout()
    path = output_dir / "drac_distribution_log.png"; plt.savefig(path, dpi=160); plt.close(); paths.append(path.name)
    return paths


def run(input_dir: Path = DEFAULT_INPUT, output_dir: Path = DEFAULT_OUTPUT) -> Path:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    output_dir.mkdir(parents=True)
    integrity = verify_input_package(input_dir)
    state_paths = sorted((input_dir / "states").glob("*.parquet"))
    frames: dict[str, pd.DataFrame] = {}
    quality: dict[str, object] = {}
    distributions: list[dict[str, object]] = []
    sensitivity: list[dict[str, object]] = []
    thresholds = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    durations = [0.1, 0.2, 0.3, 0.5]
    for path in state_paths:
        name = path.stem.replace("ngsim_", "")
        frame = pd.read_parquet(path)
        frames[name] = frame
        quality[name] = quality_summary(frame)
        for column in STATE_COLUMNS:
            distributions.append({"source": name, "variable": column, **quantile_summary(frame, column)})
        for row in event_grid(frame, thresholds, durations, 0.11):
            sensitivity.append({"source": name, **row})
    figure_names = make_figures(frames, output_dir)
    extreme_rows = []
    continuity = {}
    for source, frame in frames.items():
        mask = frame["ttc_valid"] & ((frame["ttc_s"] < 0.5) | (frame["drac_mps2"] > 10) | (frame["net_gap_m"] < 1) | (frame["closing_speed_mps"] > 15))
        extreme = frame.loc[mask, ["original_row_number", "trajectory_id", "leader_trajectory_id", "leader_id", "global_time_ms", "frame_id", "ttc_s", "drac_mps2", "net_gap_m", "closing_speed_mps", "speed_mps", "acceleration_mps2", "raw_space_headway_ft"]].copy()
        extreme["source"] = source
        extreme_rows.append(extreme.sort_values(["ttc_s", "drac_mps2"], na_position="last").head(100))
        ordered = frame.sort_values(["trajectory_id", "global_time_ms", "frame_id"], kind="stable")
        previous = ordered.groupby("trajectory_id")[["global_time_ms", "frame_id"]].shift()
        consecutive = (ordered["global_time_ms"] - previous["global_time_ms"] == 100) & (ordered["frame_id"] - previous["frame_id"] == 1)
        extreme_mask = ordered["ttc_valid"] & ((ordered["ttc_s"] < 0.5) | (ordered["drac_mps2"] > 10) | (ordered["net_gap_m"] < 1) | (ordered["closing_speed_mps"] > 15))
        continuity[source] = {
            "extreme_rows": int(extreme_mask.sum()),
            "extreme_trajectory_count": int(ordered.loc[extreme_mask, "trajectory_id"].nunique()),
            "extreme_rows_with_consecutive_predecessor": int((extreme_mask & consecutive).sum()),
            "extreme_fraction_with_consecutive_predecessor": float((extreme_mask & consecutive).sum() / extreme_mask.sum()) if extreme_mask.any() else None,
        }
    pd.concat(extreme_rows, ignore_index=True).to_csv(output_dir / "extreme_records.csv", index=False)
    pd.DataFrame(distributions).to_csv(output_dir / "distribution_summary.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(output_dir / "event_sensitivity.csv", index=False)
    (output_dir / "distribution_summary.json").write_text(json.dumps(distributions, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "event_sensitivity.json").write_text(json.dumps(sensitivity, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "continuity_summary.json").write_text(json.dumps(continuity, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "quality_summary.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    config = {
        "schema_version": "stage_0_2.task_2.audit.v1", "input_dir": str(input_dir),
        "input_sha256sums": str(input_dir / "SHA256SUMS"), "ttc_threshold_grid_s": thresholds,
        "minimum_duration_grid_s": durations, "max_gap_s": 0.11,
        "diagnostic_extreme_flags": {"ttc_lt_s": 0.5, "drac_gt_mps2": 10.0, "net_gap_lt_m": 1.0, "closing_speed_gt_mps": 15.0},
        "sampling": {"figure_max_rows_per_source": 100000, "seed": 20261010},
        "scientific_claim_eligible": False, "locked_holdout_opened": False,
    }
    (output_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {
        "schema_version": "stage_0_2.task_2.audit.v1", "created_at": datetime.now(UTC).isoformat(),
        "input_integrity": integrity, "sources": list(frames), "quality_summary": quality,
        "sensitivity_rows": len(sensitivity), "figures": figure_names,
        "scientific_status": "descriptive_audit_only; no_threshold_or_gate_frozen",
    }
    (output_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    provenance = {"schema_version": "stage_0_2.task_2.provenance.v1", "created_at": datetime.now(UTC).isoformat(), "python": sys.version, "platform": platform.platform(), "input_package": str(input_dir)}
    (output_dir / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"}):
        files.append({"path": path.relative_to(output_dir).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    (output_dir / "manifest.json").write_text(json.dumps({"schema_version": "stage_0_2.task_2.manifest.v1", "files": files}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = []
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        lines.append(f"{sha256_file(path)}  {path.relative_to(output_dir).as_posix()}")
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_dir


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(run(args.input, args.output))
