from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.communication_pilot import (  # noqa: E402
    compute_factorial_effects,
    select_valid_run_results,
    summarize_communication_records,
    summarize_target_risk,
)


CONDITIONS = ("off", "oracle", "comm_ideal", "comm_impaired")
PROFILES = ("nominal", "source_high")
PENETRATIONS = (60, 80)
SEEDS = (2026080201, 2026080202)
RISK_METRICS = (
    "ttc_conflict_burden",
    "ttc_violation_rate",
    "minimum_ttc_s",
    "hard_brake_rate_per_1000_steps",
    "mean_speed_mps",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize explicit-communication Pilot B.")
    parser.add_argument("--primary-root", type=Path, required=True)
    parser.add_argument("--corrected-root", type=Path, required=True)
    parser.add_argument("--corrected-communication-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _read_jsonl(path: Path) -> pd.DataFrame:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return pd.DataFrame(rows)


def _read_run_tables(root: Path, conditions: tuple[str, ...]) -> pd.DataFrame:
    frames = []
    for condition in conditions:
        path = root / condition / "per_run_results.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame["condition"] = condition
        frame["data_root"] = str(root.resolve())
        frames.append(frame)
    if not frames:
        raise ValueError(f"No per_run_results.csv files found under {root}")
    return pd.concat(frames, ignore_index=True)


def _find_unique(root: Path, pattern: str, label: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise ValueError(f"Expected one {label}, found {len(matches)}: {matches}")
    return matches[0]


def _mechanism_records(row: pd.Series) -> pd.DataFrame:
    root = Path(str(row["data_root"]))
    exp_tag = str(row["exp_tag"])
    condition = str(row["condition"])
    path = _find_unique(
        root / "mechanism_logs",
        f"{exp_tag}_{condition}_seed*.jsonl",
        f"mechanism log for {exp_tag}/{condition}",
    )
    records = _read_jsonl(path)
    return records.loc[
        pd.to_numeric(records["sumo_seed"], errors="coerce").eq(int(row["sumo_seed"]))
    ].copy()


def _emission_path(row: pd.Series) -> Path:
    root = Path(str(row["data_root"]))
    condition = str(row["condition"])
    exp_tag = str(row["exp_tag"])
    run_index = int(row["run_index"])
    return _find_unique(
        root / condition / "emissions",
        f"{exp_tag}_[0-9]*-{run_index}_emission.csv",
        f"emission for {exp_tag}/{condition}/run {run_index}",
    )


def _paired_effects(run_metrics: pd.DataFrame) -> pd.DataFrame:
    comparisons = (
        ("comm_ideal_minus_off", "comm_ideal", "off"),
        ("oracle_minus_off", "oracle", "off"),
        ("comm_impaired_minus_comm_ideal", "comm_impaired", "comm_ideal"),
        ("comm_ideal_minus_oracle", "comm_ideal", "oracle"),
    )
    keys = ["penetration_pct", "stress_profile", "configured_run_seed"]
    rows: list[dict[str, object]] = []
    for values, group in run_metrics.groupby(keys, sort=True):
        by_condition = group.set_index("condition")
        for label, treatment, reference in comparisons:
            if treatment not in by_condition.index or reference not in by_condition.index:
                continue
            result: dict[str, object] = dict(zip(keys, values))
            result["comparison"] = label
            for metric in RISK_METRICS:
                a = pd.to_numeric(by_condition.loc[treatment, metric], errors="coerce")
                b = pd.to_numeric(by_condition.loc[reference, metric], errors="coerce")
                result[f"delta_{metric}"] = float(a - b) if pd.notna(a) and pd.notna(b) else None
            rows.append(result)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    primary_root = args.primary_root.resolve()
    corrected_root = args.corrected_root.resolve()
    corrected_communication_root = args.corrected_communication_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    primary = _read_run_tables(primary_root, CONDITIONS)
    corrected = _read_run_tables(corrected_root, ("off", "oracle"))
    corrected_communication = _read_run_tables(
        corrected_communication_root, ("comm_ideal", "comm_impaired")
    )
    valid = select_valid_run_results(primary, corrected, corrected_communication)

    metric_rows: list[dict[str, object]] = []
    communication_rows: list[dict[str, object]] = []
    for _, row in valid.iterrows():
        emission_path = _emission_path(row)
        emission = pd.read_csv(emission_path)
        records = _mechanism_records(row)
        common = {
            "condition": str(row["condition"]),
            "stress_profile": str(row["stress_profile"]),
            "penetration_pct": int(row["penetration_pct"]),
            "configured_run_seed": int(row["configured_run_seed"]),
            "sumo_seed": int(row["sumo_seed"]),
        }
        metric_rows.append(
            {
                **common,
                "run_index": int(row["run_index"]),
                "emission_file": str(emission_path),
                "returns": float(row["returns"]),
                "outflows": float(row["outflows"]),
                "collision_count": int(row["collision_count"]),
                **summarize_target_risk(emission),
            }
        )
        communication_rows.append(
            {
                **common,
                **summarize_communication_records(records),
                "would_trigger_count": int(
                    records.get("would_trigger", pd.Series(False, index=records.index))
                    .fillna(False)
                    .astype(bool)
                    .sum()
                ),
            }
        )

    run_metrics = pd.DataFrame(metric_rows).sort_values(
        ["condition", "stress_profile", "penetration_pct", "configured_run_seed"]
    )
    communication = pd.DataFrame(communication_rows).sort_values(
        ["condition", "stress_profile", "penetration_pct", "configured_run_seed"]
    )
    paired = _paired_effects(run_metrics)

    aggregations = {
        metric: ["mean", "std"] for metric in RISK_METRICS
    }
    aggregations.update({"returns": ["mean", "std"], "outflows": ["mean", "std"]})
    cell_summary = (
        run_metrics.groupby(["condition", "stress_profile", "penetration_pct"], sort=True)
        .agg(aggregations)
        .reset_index()
    )
    cell_summary.columns = [
        "_".join(str(part) for part in column if part)
        if isinstance(column, tuple)
        else str(column)
        for column in cell_summary.columns
    ]

    factorial_tables = []
    for metric in RISK_METRICS:
        table = compute_factorial_effects(run_metrics, metric=metric)
        factorial_tables.append(table)
        table.to_csv(output_dir / f"factorial_effects_{metric}.csv", index=False)

    expected_keys = {
        (condition, profile, penetration, seed)
        for condition in CONDITIONS
        for profile in PROFILES
        for penetration in PENETRATIONS
        for seed in SEEDS
    }
    actual_keys = {
        (
            str(row.condition),
            str(row.stress_profile),
            int(row.penetration_pct),
            int(row.configured_run_seed),
        )
        for row in run_metrics.itertuples(index=False)
    }
    comm_by_condition = communication.groupby("condition", sort=True).agg(
        record_count=("record_count", "sum"),
        sent_count=("sent_count", "sum"),
        dropped_count=("dropped_count", "sum"),
        delivered_count=("delivered_count", "sum"),
        applied_count=("applied_count", "sum"),
        would_trigger_count=("would_trigger_count", "sum"),
    )
    audit = {
        "valid_run_count": int(len(run_metrics)),
        "expected_run_count": len(expected_keys),
        "coverage_complete": actual_keys == expected_keys,
        "missing_run_keys": sorted(expected_keys - actual_keys),
        "unexpected_run_keys": sorted(actual_keys - expected_keys),
        "collision_count_total": int(run_metrics["collision_count"].sum()),
        "off_applied_count": int(comm_by_condition.loc["off", "applied_count"]),
        "oracle_applied_count": int(comm_by_condition.loc["oracle", "applied_count"]),
        "comm_ideal_applied_count": int(comm_by_condition.loc["comm_ideal", "applied_count"]),
        "comm_impaired_applied_count": int(comm_by_condition.loc["comm_impaired", "applied_count"]),
        "comm_ideal_dropped_count": int(comm_by_condition.loc["comm_ideal", "dropped_count"]),
        "comm_impaired_dropped_count": int(comm_by_condition.loc["comm_impaired", "dropped_count"]),
        "comm_impaired_sent_count": int(comm_by_condition.loc["comm_impaired", "sent_count"]),
        "comm_impaired_observed_drop_rate": float(
            comm_by_condition.loc["comm_impaired", "dropped_count"]
            / comm_by_condition.loc["comm_impaired", "sent_count"]
        ),
        "invalid_primary_source_high_rows_excluded": int(
            (
                primary["condition"].isin({"off", "oracle"})
                & primary["stress_profile"].eq("source_high")
            ).sum()
        ),
        "invalid_primary_communication_seed2_rows_excluded": int(
            (
                primary["condition"].isin({"comm_ideal", "comm_impaired"})
                & primary["configured_run_seed"].eq(2026080202)
            ).sum()
        ),
    }
    audit["audit_pass"] = bool(
        audit["coverage_complete"]
        and audit["collision_count_total"] == 0
        and audit["off_applied_count"] == 0
        and audit["oracle_applied_count"] > 0
        and audit["comm_ideal_applied_count"] > 0
        and audit["comm_ideal_dropped_count"] == 0
        and audit["comm_impaired_applied_count"] > 0
        and audit["comm_impaired_dropped_count"] > 0
    )

    run_metrics.to_csv(output_dir / "valid_run_metrics.csv", index=False)
    communication.to_csv(output_dir / "communication_summary.csv", index=False)
    paired.to_csv(output_dir / "paired_effects.csv", index=False)
    cell_summary.to_csv(output_dir / "cell_summary.csv", index=False)
    comm_by_condition.reset_index().to_csv(
        output_dir / "communication_by_condition.csv", index=False
    )
    (output_dir / "pilot_b_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if not audit["audit_pass"]:
        raise SystemExit("Pilot B audit failed")


if __name__ == "__main__":
    main()
