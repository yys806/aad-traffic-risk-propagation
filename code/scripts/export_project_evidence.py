from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
EVIDENCE_ROOT = REPO_ROOT / "evidence"
MAX_FILE_BYTES = 256 * 1024
EXPORT_VERSION = "aad-portable-evidence-2026-09-09-stage-taxonomy-v2"


def _source_pairs() -> dict[str, list[tuple[str, str]]]:
    pairs: dict[str, list[tuple[str, str]]] = {
        "RES-STAGE-0.1-INFRASTRUCTURE-V3": [
            (
                "code/outputs/formal/stage_0_1/e00_real_sumo_20260907_primary_v3/e00_report.json",
                "stage_0_1_report.json",
            ),
            (
                "code/outputs/formal/stage_0_1/e00_real_sumo_20260907_primary_v3/independent_analysis.json",
                "independent_analysis.json",
            ),
        ],
        "RES-STAGE-0.1-ENV-COMPARE-V3": [
            (
                "code/outputs/formal/stage_0_1/e00_real_sumo_environment_comparison_20260907_v3.json",
                "environment_comparison.json",
            )
        ],
        "RES-STAGE-0.2-NGSIM-V2": [],
        "RES-STAGE-0.2-TASK-1.4": [],
        "RES-STAGE-0.2-TASK-1.5": [],
        "RES-STAGE-0.2-TASK-2": [],
        "RES-STAGE-0.2-TASK-2.1": [],
        "RES-STAGE-0.2-FINAL-CLOSURE": [],
        "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4": [],
        "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3": [],
        "RES-STAGE-0.4-COMM-OBS-V3": [],
        "RES-STAGE-0.5-REAL-REF-V1": [],
        "RES-STAGE-0.5-REAL-REF-R2": [],
        "RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1": [],
        "RES-STAGE-0.5-CALIBRATION-READINESS-V1": [],
        "RES-STAGE-0.5-CALIBRATION-GAPS-V1": [],
        "RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1": [],
        "RES-STAGE-0.6-PRELOCK-V2": [],
        "RES-PROTOCOL-READINESS-V1": [
            (
                "code/outputs/formal/calibration/protocol_lock_readiness_v1.json",
                "protocol_lock_readiness_v1.json",
            )
        ],
        "RES-STAGE-0.3-PNEUMA-KINEMATICS-R1": [],
    }

    stage_0_1_root = "code/outputs/formal/stage_0_1/e00_real_sumo_20260907_primary_v3"
    for cell in ("s0c0", "s0c1", "s1c0", "s1c1"):
        for name in (
            "audit.json",
            "config_frozen.json",
            "manifest.json",
            "provenance.json",
            "SHA256SUMS",
            "topology.json",
        ):
            pairs["RES-STAGE-0.1-INFRASTRUCTURE-V3"].append(
                (f"{stage_0_1_root}/{cell}/{name}", f"{cell}/{name}")
            )

    calibration_sets = {
        "RES-STAGE-0.2-FINAL-CLOSURE": (
            "stage_0_2_final_closure_20261012_final_r1",
            ("audit.json", "config.json", "provenance.json", "manifest.json", "SHA256SUMS", "gate_matrix.json", "summary.json", "validation.json", "final_interface_reverification.json", "report.md", "paper_version_conflict.md"),
        ),
        "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4": (
            "stage_0_2_scientific_acceptance_20261012_r4",
            ("audit.json", "scientific_gate_report.json", "p2_event_rates.json", "scientific_gate_matrix.json", "scope_and_claims.md", "exposure_edge_audit.json", "report.md", "provenance.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3": (
            "stage_0_2_scientific_acceptance_20261012_r3",
            ("audit.json", "scientific_gate_report.json", "p2_event_rates.json", "scientific_gate_matrix.json", "scope_and_claims.md", "exposure_edge_audit.json", "report.md", "provenance.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.2-TASK-2.1": (
            "stage_0_2_task_2_1_extreme_review_20261011_r4",
            ("audit.json", "config.json", "provenance.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.2-TASK-2": (
            "stage_0_2_task_2_risk_quality_audit_20261010_r4",
            ("audit.json", "config.json", "quality_summary.json", "distribution_summary.json", "event_sensitivity.json", "continuity_summary.json", "provenance.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.2-TASK-1.5": (
            "stage_0_2_task_1_5_20261010_r4",
            ("audit.json", "config_frozen.json", "cross_clock_match_audit.json", "regression_comparison.json", "provenance.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.2-TASK-1.4": (
            "stage_0_2_task_1_4_20261010",
            ("audit.json", "comparison.json", "identity_evidence.json", "measurement_comparison.json", "event_boundary_comparison.json", "config_frozen.json", "manifest.json", "provenance.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.2-NGSIM-V2": (
            "stage_0_2_ngsim_v2",
            ("audit.json", "config_frozen.json", "manifest.json", "provenance.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.4-COMM-OBS-V3": (
            "stage_0_4_observability_v3",
            ("audit.json", "manifest.json", "provenance.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.5-REAL-REF-V1": (
            "stage_0_5_real_reference_v1",
            ("audit.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.5-REAL-REF-R2": (
            "stage_0_5_real_reference_r2",
            (
                "audit.json",
                "config.json",
                "input_manifest.json",
                "ngsim_formal_metrics.json",
                "pneuma_statistics_summary.json",
                "sampling_sensitivity.json",
                "independence_audit.json",
                "provenance.json",
                "report.md",
                "manifest.json",
                "SHA256SUMS",
            ),
        ),
        "RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1": (
            "stage_0_5_sumo_baseline_engineering_v1_baseline",
            (
                "access_audit.json",
                "audit.json",
                "calibration_validation_policy.json",
                "config.json",
                "demand_config.json",
                "formal_adapter_audit.json",
                "manifest.json",
                "measurement_status_summary.json",
                "measurement_support_matrix.json",
                "network_design_candidate.json",
                "p2_exposure_summary.json",
                "provenance.json",
                "runtime_diagnostics.json",
                "scenario_manifest.json",
                "SHA256SUMS",
                "sumo_formal_field_map.json",
                "vehicle_type_config.json",
            ),
        ),
        "RES-STAGE-0.6-PRELOCK-V2": (
            "stage_0_6_prelock_validation_v2",
            ("audit.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.3-PNEUMA-KINEMATICS-R1": (
            "stage_0_3_pneuma_kinematics_20261012_r1",
            ("audit.json", "config.json", "provenance.json", "manifest.json", "SHA256SUMS", "gate_matrix_summary.json"),
        ),
        "RES-STAGE-0.3-BOUNDARY-REPAIR-R2": (
            "stage_0_3_pneuma_boundary_repair_20261016_r2",
            ("audit.json", "config.json", "provenance.json", "manifest.json", "SHA256SUMS", "gate_matrix_summary.json"),
        ),
        "RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3": (
            "stage_0_3_scientific_acceptance_20261016_r3",
            ("audit.json", "config.json", "decisions.json", "scientific_gate_report.json", "scientific_gate_matrix.json", "report.md", "scope_and_claims.md", "provenance.json", "manifest.json", "SHA256SUMS"),
        ),
    }
    for name in (
        "access_audit.json",
        "audit.json",
        "calibration_source_analysis.json",
        "candidate_protocol.json",
        "config.json",
        "manifest.json",
        "measurement_crosswalks.json",
        "measurement_equivalence_matrix.json",
        "provenance.json",
        "researcher_decision_matrix.json",
        "scientific_admission_status.json",
        "stage_0_5_4b_admission_checklist.json",
        "SHA256SUMS",
    ):
        pairs["RES-STAGE-0.5-CALIBRATION-READINESS-V1"].append(
            (
                f"code/outputs/formal/calibration/stage_0_5_calibration_readiness_v1/{name}",
                name,
            )
        )
    for name in (
        "access_audit.json", "audit.json", "benchmark_configs.json", "benchmark_plan.json",
        "benchmark_summary.json", "benchmark_numerical_diagnostics.json", "boundary_sensitivity.json",
        "candidate_protocol.json", "config.json", "cost_budget_proposal.json", "diagnostics.json",
        "source_manifest.json", "unified_strata.json", "provenance.json", "test_record.json",
        "report.md", "manifest.json", "SHA256SUMS",
    ):
        pairs["RES-STAGE-0.5-CALIBRATION-GAPS-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_calibration_gaps_v1_final/{name}", name)
        )
    for name in ("timestep_sensitivity.json", "manifest.json", "SHA256SUMS"):
        pairs["RES-STAGE-0.5-CALIBRATION-READINESS-V1"].append(
            (
                f"code/outputs/formal/calibration/stage_0_5_timestep_sensitivity_v1/{name}",
                f"timestep/{name}",
            )
        )
    for name in (
        "experiment_plan.json", "PLAN_SHA256", "config.json", "frozen_input_manifest.json",
        "run_manifest.json", "execution_ledger.json", "fixed_parameter_manifest.json",
        "source_access_audit.json", "validation_activity_audit.json", "real_reference_summary.json", "phase1_checkpoint.json",
        "PHASE1_DIAGNOSTIC.md", "numerical_method_audit.json", "traffic_input_output_audit.json",
        "initialization_warmup_diagnostics.json", "local_kinematics_comparison.json",
        "following_response_diagnostics.json", "parameter_response_matrix.json",
        "mechanism_hypothesis_matrix.json", "network_facts.json", "fleet_and_state_support_audit.json", "boundary_response_diagnostics.json", "runtime_budget_audit.json",
        "run_metrics.csv", "time_bins_60s.csv", "time_series_5s.csv", "figure_index.json",
        "audit.json", "provenance.json", "execution_code_change_audit.json", "test_record.json", "report.md", "manifest.json", "SHA256SUMS",
    ):
        pairs["RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_exploratory_response_v1/{name}", name)
        )
    # The Stage 0.5.3 measurement probe package is exported under the same result id
    # in its own subdirectory so that the two engineering fixtures stay distinguishable.
    for name in (
        "audit.json",
        "config.json",
        "formal_adapter_audit.json",
        "manifest.json",
        "measurement_status_summary.json",
        "p2_exposure_summary.json",
        "provenance.json",
        "runtime_diagnostics.json",
        "SHA256SUMS",
    ):
        pairs["RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1"].append(
            (
                f"code/outputs/formal/calibration/stage_0_5_sumo_baseline_engineering_v1_probe/{name}",
                f"probe/{name}",
            )
        )
    pairs["RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1"] = [
        (
            "code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/gate_report.json",
            "gate_report.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/config.json",
            "config.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/provenance.json",
            "provenance.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/manifest.json",
            "manifest.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/report.md",
            "report.md",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/SHA256SUMS",
            "SHA256SUMS",
        ),
    ]
    pairs["RES-STAGE-0.4-SEE-V2X-GNSS-REPAIR-V1"] = [
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_gnss_repair_v1/audit.json",
            "audit.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_gnss_repair_v1/config.json",
            "config.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_gnss_repair_v1/provenance.json",
            "provenance.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_gnss_repair_v1/manifest.json",
            "manifest.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_gnss_repair_v1/SHA256SUMS",
            "SHA256SUMS",
        ),
    ]
    pairs["RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1"] = [
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_bsm_reaudit_v1/audit.json",
            "audit.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_bsm_reaudit_v1/config.json",
            "config.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_bsm_reaudit_v1/provenance.json",
            "provenance.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_bsm_reaudit_v1/manifest.json",
            "manifest.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_bsm_reaudit_v1/SHA256SUMS",
            "SHA256SUMS",
        ),
    ]
    pairs["RES-STAGE-0.4-SEE-V2X-REAUDIT-V1"] = [
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/audit.json",
            "audit.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/config.json",
            "config.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/provenance.json",
            "provenance.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/manifest.json",
            "manifest.json",
        ),

        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/SHA256SUMS",
            "SHA256SUMS",
        ),
    ]
    pairs["RES-STAGE-0.4-SEE-V2X-MINIMAL-V1"] = [
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_minimal_v1/audit.json",
            "audit.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_minimal_v1/config.json",
            "config.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_minimal_v1/provenance.json",
            "provenance.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_minimal_v1/manifest.json",
            "manifest.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_see_v2x_minimal_v1/SHA256SUMS",
            "SHA256SUMS",
        ),
    ]
    pairs["RES-STAGE-0.4-RSE-BSM-V1"] = [
        (
            "code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/audit.json",
            "audit.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/config.json",
            "config.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/provenance.json",
            "provenance.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/manifest.json",
            "manifest.json",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/report.md",
            "report.md",
        ),
        (
            "code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/SHA256SUMS",
            "SHA256SUMS",
        ),
    ]
    pairs["RES-STAGE-0.3-PNEUMA-KINEMATICS-R1"].append(
        (
            "code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1_independent_verification.json",
            "independent_verification.json",
        )
    )
    pairs["RES-STAGE-0.3-BOUNDARY-REPAIR-R2"] = [
        (
            "code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2_independent_verification.json",
            "independent_verification.json",
        )
    ]
    for result_id, directory in {
        "RES-STAGE-0.2-TASK-2.4": "stage_0_2_task_2_4_20261011_r2",
        "RES-STAGE-0.2-TASK-2.5": "stage_0_2_task_2_5_20261011_r1",
        "RES-STAGE-0.2-TASK-2.5.1": "stage_0_2_task_2_5_1_20261011_r2",
        "RES-STAGE-0.2-TASK-2.5.2": "stage_0_2_task_2_5_2_20261011_r1",
        "RES-STAGE-0.2-DECISION-RATIFICATION": "stage_0_2_decision_ratification_20261011_r1",
        "RES-STAGE-0.2-RHO-TIMESCALE": "stage_0_2_rho_timescale_validation_20261011_r1",
        "RES-STAGE-0.2-FORMAL-RISK-MEASUREMENT": "stage_0_2_formal_risk_measurement_20261011_r1",
        "RES-STAGE-0.2-FORMAL-RISK-MEASUREMENT-CONSISTENCY-REPAIR": "stage_0_2_formal_risk_measurement_20261011_r2",
    }.items():
        calibration_sets[result_id] = (directory, ("audit.json", "config.json", "provenance.json", "manifest.json", "SHA256SUMS"))
    for result_id, (directory, names) in calibration_sets.items():
        pairs.setdefault(result_id, [])
        for name in names:
            pairs[result_id].append(
                (f"code/outputs/formal/calibration/{directory}/{name}", name)
            )
    return pairs


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source(source: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"missing evidence source: {source}")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"evidence source exceeds {MAX_FILE_BYTES} bytes: {source}")
    lowered = source.name.lower()
    if "sealed_sampling_key" in lowered:
        raise ValueError(f"refusing sealed sampling key: {source}")
    # B0 exports only these aggregate tables, never arbitrary trajectory CSVs.
    aggregate_names={"SHA256SUMS","PLAN_SHA256","run_metrics.csv","time_bins_60s.csv","time_series_5s.csv"}
    if source.suffix.lower() not in {".json", ".md", ".txt", ".sha256"} and source.name not in aggregate_names:
        raise ValueError(f"unsupported evidence file type: {source}")


def export_evidence(repo_root: Path) -> dict[str, object]:
    evidence_root = repo_root / "evidence"
    result_entries: list[dict[str, object]] = []
    for result_id, pairs in _source_pairs().items():
        files: list[dict[str, object]] = []
        for source_raw, destination_tail in pairs:
            source = repo_root / source_raw
            _validate_source(source)
            destination = evidence_root / "results" / result_id / destination_tail
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            files.append(
                {
                    "source_path": source_raw,
                    "snapshot_path": destination.relative_to(repo_root).as_posix(),
                    "size_bytes": destination.stat().st_size,
                    "sha256": _sha256(destination),
                }
            )
        result_entries.append({"result_id": result_id, "files": files})

    manifest: dict[str, object] = {
        "schema_version": "aad.evidence-manifest.v1",
        "export_version": EXPORT_VERSION,
        "policy": "exact small evidence snapshots; large and sealed artifacts excluded",
        "source_root": "code/outputs",
        "excluded_classes": [
            "parquet",
            "raw_csv",
            "html",
            "images",
            "logs",
            "sealed_sampling_keys",
        ],
        "results": result_entries,
    }
    manifest_path = evidence_root / "EVIDENCE_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    return manifest


def verify_evidence(repo_root: Path) -> list[str]:
    issues: list[str] = []
    manifest_path = repo_root / "evidence/EVIDENCE_MANIFEST.json"
    if not manifest_path.is_file():
        return ["missing evidence/EVIDENCE_MANIFEST.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for result in manifest.get("results", []):
        result_id = result.get("result_id", "unknown")
        for entry in result.get("files", []):
            source = repo_root / entry["source_path"]
            snapshot = repo_root / entry["snapshot_path"]
            if not snapshot.is_file():
                issues.append(f"{result_id}: missing snapshot {entry['snapshot_path']}")
                continue
            if snapshot.stat().st_size != entry.get("size_bytes"):
                issues.append(f"{result_id}: size mismatch {entry['snapshot_path']}")
            if _sha256(snapshot) != entry.get("sha256"):
                issues.append(f"{result_id}: sha256 mismatch {entry['snapshot_path']}")
            if source.is_file() and _sha256(source) != entry.get("sha256"):
                issues.append(f"{result_id}: source drift {entry['source_path']}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or verify portable AAD evidence.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    if args.verify:
        issues = verify_evidence(repo_root)
        if issues:
            print("PORTABLE_EVIDENCE_INVALID")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("PORTABLE_EVIDENCE_OK")
        return 0
    manifest = export_evidence(repo_root)
    file_count = sum(len(item["files"]) for item in manifest["results"])
    print(f"PORTABLE_EVIDENCE_EXPORTED results={len(manifest['results'])} files={file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
