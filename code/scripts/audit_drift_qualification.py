from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from riskprop.drift_qualification import (
    audit_formal_coverage,
    audit_pilot_events,
    audit_raw_emission_files,
    build_extreme_deceleration_catalog,
    compare_drift_with_baselines,
    compare_with_confidence_intervals,
    extract_validated_risk_events,
    qualification_decision,
    write_qualification_outputs,
)


METRIC_DIRECTIONS = {
    "returns_mean": "higher",
    "velocities_mean": "higher",
    "outflows_mean": "higher",
    "collision_count_mean": "lower",
    "ttc_violation_rate_mean": "lower",
    "thw_violation_rate_mean": "lower",
    "emission_min_acceleration": "higher",
    "hard_brake_count_lt_6": "lower",
    "hard_brake_count_lt_10": "lower",
}

CI_METRIC_SPECS = {
    "return": ("return_mean", "return_ci95", "higher"),
    "speed": ("speed_mean", "speed_ci95", "higher"),
    "outflow": ("outflow_mean", "outflow_ci95", "higher"),
    "ttc_violation": ("ttc_violation_mean", "ttc_violation_ci95", "lower"),
    "minimum_acceleration": ("min_acc_mean", "min_acc_ci95", "higher"),
    "hard_braking": ("hb_lt6_per_run_mean", "hb_lt6_per_run_ci95", "lower"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit whether DRIFT is ready for risk-propagation research.")
    parser.add_argument("--upstream-root", type=Path, default=Path(r"D:\shen\research\code"))
    parser.add_argument(
        "--raw-output-root",
        type=Path,
        help="Root containing the original DRIFT output folders and emission CSV files.",
    )
    parser.add_argument(
        "--events",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "feasibility_week" / "riskprop_real_merge_server" / "risk_events.csv",
    )
    parser.add_argument(
        "--episodes",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "pilot_20260714" / "real_merge_20pct" / "risk_episodes.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "drift_qualification_20260716",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package = args.upstream_root / "experiments" / "final_results" / "result_package_v1"
    paper_tables = args.upstream_root / "experiments" / "final_results" / "paper_ready_v1" / "tables"
    coverage_df = pd.read_csv(package / "main_grid_per_run_coverage.csv")
    formal_df = pd.read_csv(paper_tables / "external_benchmark_full_grid.csv")
    legacy_events = pd.read_csv(args.events)
    legacy_episodes = pd.read_csv(args.episodes)

    coverage = audit_formal_coverage(
        coverage_df,
        scenarios=("ring", "figure8", "merge"),
        methods=("fs", "pi", "ours"),
        penetrations=(0, 20, 40, 60, 80, 100),
        expected_runs=5,
    )
    comparison = compare_drift_with_baselines(
        formal_df,
        metric_directions=METRIC_DIRECTIONS,
    )
    confidence_df = pd.read_csv(package / "main_grid_key_mean_std_ci.csv")
    confidence_comparison = compare_with_confidence_intervals(
        confidence_df,
        metric_specs=CI_METRIC_SPECS,
    )
    legacy_pilot_audit = audit_pilot_events(legacy_events, legacy_episodes)
    candidate_fit = _read_candidate_fit(args.upstream_root)
    candidate_fit_passed = bool(
        candidate_fit["learned_k5"] < candidate_fit["fixed_k5"]
        and candidate_fit["learned_k5"] < candidate_fit["single_candidate"]
    )
    comparison_wins = int(comparison["drift_better"].sum())
    comparable_non_ties = int((~comparison["tie"]).sum())
    formal_evidence_passed = bool(
        candidate_fit_passed
        and comparable_non_ties > 0
        and comparison_wins / comparable_non_ties >= 0.40
    )
    raw_paths = _discover_final_drift_emissions(args.raw_output_root) if args.raw_output_root else []
    raw_audit = audit_raw_emission_files(raw_paths) if raw_paths else {}
    raw_audit_by_scenario = {
        scenario: audit_raw_emission_files(
            [path for path in raw_paths if path.name.startswith(f"{scenario}_")]
        )
        for scenario in ("ring", "figure8", "merge")
        if any(path.name.startswith(f"{scenario}_") for path in raw_paths)
    }
    raw_emissions_available = bool(raw_paths)
    merge_p20_paths = [path for path in raw_paths if path.name.startswith("merge_ours_p20_")]
    extreme_catalog = pd.DataFrame()
    if merge_p20_paths:
        validated_events, validated_episodes = extract_validated_risk_events(merge_p20_paths)
        args.output.mkdir(parents=True, exist_ok=True)
        validated_events.to_csv(args.output / "validated_merge_p20_risk_events.csv", index=False)
        validated_episodes.to_csv(args.output / "validated_merge_p20_risk_episodes.csv", index=False)
        extreme_catalog = build_extreme_deceleration_catalog(merge_p20_paths)
        extreme_catalog.to_csv(args.output / "merge_p20_extreme_deceleration_catalog.csv", index=False)
        pilot_audit = audit_pilot_events(validated_events, validated_episodes)
    else:
        pilot_audit = legacy_pilot_audit
    ood_path = (
        args.upstream_root
        / "experiments"
        / "clean_reruns"
        / "ood_stress_0521_cleanrerun"
        / "ood_stress_method_summary.csv"
    )
    ood_summary = pd.read_csv(ood_path).to_dict("records") if ood_path.exists() else []
    decision = qualification_decision(
        coverage_passed=bool(coverage["complete"]),
        formal_evidence_passed=formal_evidence_passed,
        pilot_input_passed=bool(pilot_audit["passed"]),
        raw_emissions_available=raw_emissions_available,
        pilot_audit=pilot_audit,
    )
    paths = write_qualification_outputs(
        output_dir=args.output,
        coverage=coverage,
        comparison=comparison,
        pilot_audit=pilot_audit,
        decision=decision,
        extra_summary={
            "candidate_fit": candidate_fit,
            "candidate_fit_passed": candidate_fit_passed,
            "formal_evidence_passed": formal_evidence_passed,
            "raw_emissions_available": raw_emissions_available,
            "raw_emission_audit": raw_audit,
            "raw_emission_audit_by_scenario": raw_audit_by_scenario,
            "legacy_pilot_input_audit": legacy_pilot_audit,
            "validated_merge_p20_run_count": len(merge_p20_paths),
            "validated_merge_p20_extreme_rows": int(len(extreme_catalog)),
            "validated_merge_p20_speed_jump_matches": int(
                extreme_catalog.get("acceleration_matches_speed_jump", pd.Series(dtype=bool)).sum()
            ),
            "validated_merge_p20_terminal_extreme_rows": int(
                extreme_catalog.get("is_last_vehicle_row", pd.Series(dtype=bool)).sum()
            ),
            "ood_method_summary": ood_summary,
            "gpu_required_for_current_audit": False,
            "confidence_interval_summary": {
                "comparison_count": int(len(confidence_comparison)),
                "confidently_better_count": int(confidence_comparison["confidently_better"].sum()),
                "confidently_worse_count": int(confidence_comparison["confidently_worse"].sum()),
                "overlap_count": int(confidence_comparison["intervals_overlap"].sum()),
            },
        },
    )
    confidence_comparison.to_csv(args.output / "confidence_interval_comparison.csv", index=False)
    print(f"status={decision['status']}")
    print(f"formal_coverage={coverage['complete_cells']}/{coverage['expected_cells']}")
    print(f"pilot_input_passed={pilot_audit['passed']}")
    print(f"report={paths['report_md']}")
    return 0


def _read_candidate_fit(upstream_root: Path) -> dict[str, float]:
    table = upstream_root / "doc" / "paper" / "tables" / "tab_open_loop_candidate_fit.tex"
    text = table.read_text(encoding="utf-8")

    def value(label: str) -> float:
        match = re.search(rf"{re.escape(label)}\s*&\s*[^&]+&\s*(?:\\textbf\{{)?([0-9.]+)", text)
        if not match:
            raise ValueError(f"Could not parse candidate fit row: {label}")
        return float(match.group(1))

    return {
        "single_candidate": value("Learned $K=1$"),
        "learned_k5": value("Learned $K=5$"),
        "fixed_k5": value("Fixed $K=5$"),
    }


def _discover_final_drift_emissions(raw_output_root: Path) -> list[Path]:
    groups = (
        ("penetration_main_formal_v1", "ring_ours_*_emission.csv"),
        ("ours_f8_adopted_formal_v1", "figure8_ours_*_emission.csv"),
        ("ours_merge_eta_adopt_formal_v1", "merge_ours_*_emission.csv"),
    )
    paths: list[Path] = []
    for experiment, pattern in groups:
        paths.extend(sorted((raw_output_root / experiment / "emissions").glob(pattern)))
    return paths


if __name__ == "__main__":
    raise SystemExit(main())
