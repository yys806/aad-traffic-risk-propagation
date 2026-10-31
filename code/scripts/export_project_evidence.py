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
        "RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1": [],
        "RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1": [],
        "RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1": [],
        "RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2": [],
        "RES-STAGE-0.6-PRELOCK-V2": [],
        "RES-PROTOCOL-READINESS-V1": [
            (
                "code/outputs/formal/calibration/protocol_lock_readiness_v1.json",
                "protocol_lock_readiness_v1.json",
            )
        ],
        "RES-STAGE-0.3-PNEUMA-KINEMATICS-R1": [],
    }

    # Round2 Task2 is a self-contained offline contract-audit package.  Its
    # evidence files are already portable snapshots; register them in the
    # manifest without reaching into sealed trajectories or raw outputs.
    task2_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029"
    pairs["RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029"] = [
        (f"{task2_root}/{name}", name)
        for name in (
            "candidate_rule_comparison.json", "contract_audit_matrix.json",
            "literature_dedup_acquisition.json", "manifest.json", "sealed_trace_reuse.json",
            "SHA256SUMS", "source_bindings.json", "synthetic_case_inputs.json",
            "synthetic_case_results.json", "validation_record.json", "full_pytest_failure_inventory.json", "zotero_registration_result.json",
        )
    ]
    task3_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029"
    pairs["RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029"] = [
        (f"{task3_root}/{name}", name)
        for name in (
            "contract_alignment_decision.json", "flag_preservation_before_after.json",
            "lane_path_separation_recheck.json", "manifest.json", "sealed_trace_reanalysis_reuse.json",
            "SHA256SUMS", "source_bindings.json", "validation_record.json",
        )
    ]
    task4_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030"
    pairs["RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030"] = [
        (f"{task4_root}/{name}", name)
        for name in (
            "decision_matrix.json", "manifest.json", "population_scope_crosswalk.json",
            "real_source_target_exposure.csv", "real_source_target_p2_summary.json",
            "real_source_target_state_metrics.csv", "risk_event_attribution_summary.csv",
            "SHA256SUMS", "simulation_source_target_metrics.csv", "source_bindings.json",
            "time_alignment_audit.json", "validation_record.json",
        )
    ]
    task5_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030"
    pairs["RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030"] = [
        (f"{task5_root}/{name}", name)
        for name in (
            "corrected_real_source_target_state_metrics.csv", "corrected_simulation_source_target_metrics.csv",
            "event_onset_attribution_audit.json", "manifest.json", "SHA256SUMS", "source_bindings.json",
            "time_block_statistics_diff.csv", "validation_record.json", "window_overlap_audit.json",
        )
    ]

    # Task6 aggregates are already portable; never read sealed trajectories here.
    task6_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030"
    pairs["RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030"] = [
        (f"{task6_root}/{name}", name)
        for name in (
            "analysis_config.json", "analysis_validation.json",
            "common_support_crosswalk.json", "context_consistency_check.json",
            "control_matching_audit.json", "engineering_validation.json",
            "event_concentration.json", "event_context_summary.csv",
            "event_relative_profiles.csv", "evidence_reuse_matrix.csv",
            "gap_closing_joint_histogram.csv", "independent_time_block_joint_metrics.csv",
            "joint_distribution_summary.csv", "literature_review.json",
            "macro_common_support_cells.csv", "mechanism_matrix.json",
            "population_and_quality.json", "source_bindings.json",
            "validation_record.json", "manifest.json", "SHA256SUMS",
        )
    ]

    # Task8: bounded anonymous derived rows/profiles, no native IDs or raw tables.
    task8_root = 'evidence/results/RES-STAGE-0.5-POST-R2-TASK8-KINEMATIC-MECHANISM-DIAG-20261030'
    pairs['RES-STAGE-0.5-POST-R2-TASK8-KINEMATIC-MECHANISM-DIAG-20261030'] = [
        (f'{task8_root}/{name}', name) for name in (
            'analysis_config.json', 'analysis_validation.json',
            'event_precursor_decomposition.csv', 'control_precursor_decomposition.csv',
            'precursor_summary.csv', 'event_control_comparison.csv', 'precursor_profiles.csv',
            'sumo_near_threshold_profiles.csv', 'sumo_near_threshold_cases.csv',
            'sample_coverage.json', 'overlap_and_repeated_units.json', 'precursor_window_caveats.json',
            'contribution_signs.json', 'representative_profile_selection.json', 'figure_index.json',
            'krauss_source_map.json', 'sealed_configuration_audit.json', 'krauss_constraint_scope.json',
            'historical_evidence_review.json', 'literature_reuse_review.json',
            'mechanism_evidence_matrix.json', 'fixed_leader_design_assessment.json',
            'evidence_reuse_matrix.csv', 'source_bindings.json', 'context_consistency_check.json',
            'validation_record.json', 'manifest.json', 'SHA256SUMS',
        )
    ]

    # Task7 availability metadata only; no videos or identity-level cases.
    task7_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK7-INDEPENDENT-PHYSICAL-QUALITY-REVIEW-20261030"
    pairs["RES-STAGE-0.5-ROUND2-TASK7-INDEPENDENT-PHYSICAL-QUALITY-REVIEW-20261030"] = [
        (f"{task7_root}/{name}", name)
        for name in (
            "agents_section8_change.txt", "agents_section8_scope.json",
            "camera_coverage_audit.json", "conditional_review_plan.json",
            "context_consistency_check.json", "documented_video_resources.csv",
            "evidence_reuse_matrix.csv", "literature_reuse.json",
            "official_video_catalog_metadata.json", "resource_request.json",
            "review_summary.json", "source_availability.json", "source_bindings.json",
            "validation_scope.json", "video_time_alignment_audit.json",
            "validation_record.json", "manifest.json", "SHA256SUMS",
        )
    ]

    # Task7.1 spatial controls are a small ID-free, risk-independent sample.
    task71_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030"
    pairs["RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030"] = [
        (f"{task71_root}/{name}", name)
        for name in (
            "spatial_mapping_audit.json", "camera_localy_coverage.csv",
            "spatial_control_points.csv", "video_time_alignment_status.json",
            "license_resource_matrix.csv", "literature_reuse_assessment.md",
            "candidate_acquisition_manifest.json", "alternative_reference_assessment.json",
            "evidence_reuse_matrix.csv", "source_bindings.json",
            "validation_record.json", "manifest.json", "SHA256SUMS",
        )
    ]

    # Task7.2: directory/permission/time metadata and old-control diagnostics only.
    task72_root = "evidence/results/RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030"
    pairs["RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030"] = [
        (f"{task72_root}/{name}", name)
        for name in (
            "resource_inventory.csv", "license_scope_matrix.csv",
            "time_metadata_matrix.csv", "spatial_shift_diagnostic.json",
            "provider_inquiry_draft.md", "decision_summary.json",
            "source_bindings.json", "validation_record.json",
            "manifest.json", "SHA256SUMS",
        )
    ]

    # Task9: fixed-leader preparation and provider-dispatch status only; no video,
    # identity-level physical cases or simulation payloads.
    task9_root = "evidence/results/RES-STAGE-0.5-POST-R2-TASK9-FIXED-LEADER-PREP-20261031"
    pairs["RES-STAGE-0.5-POST-R2-TASK9-FIXED-LEADER-PREP-20261031"] = [
        (f"{task9_root}/{name}", name)
        for name in (
            "arm_config_audit.json", "historical_seed_audit.json", "provider_dispatch_status.json",
            "source_bindings.json", "task9_protocol.json", "validation_record.json",
            "context_consistency_check.json", "manifest.json", "SHA256SUMS",
        )
    ]

    # Policy A preflight proposals, not a frozen execution protocol.
    pairs['RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1'] = [
        ('code/outputs/formal/calibration/stage_0_5_interaction_diagnostics_v1/portable/' + name, name)
        for name in ['execution_freeze.json', 'execution_freeze_engineering_precheck.json',
                     'execution_freeze_before_utf8_fix.json', 'readonly_hash_verification.json',
                     'researcher_ruling.json', 'execution_ledger.json', 'failure_review.json',
                     'common_support_18_cells.csv', 'provenance.json', 'raw_artifact_sha256.json',
                     'validation_record.json', 'SHA256SUMS']]
    pairs["RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1"] = [("code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/portable/" + name, name) for name in ['authorization.json', 'common_support_summary.json', 'final_plan_proposal.json', 'PROPOSAL_SHA256', 'resource_preflight.json', 'REVIEW_PROPOSAL_SHA256', 'review_ready_plan.json', 'SHA256SUMS', 'static_input_audit.json', 'validation_scope_incident.json', 'test_record.json', 'us101__0750_0805_baseline_offset100.csv', 'us101__0750_0805_common_support.csv', 'us101__0750_0805_real_offset100.csv', 'us101__0805_0820_baseline_offset100.csv', 'us101__0805_0820_common_support.csv', 'us101__0805_0820_real_offset100.csv']]

    # Zero-trajectory C6 repair and C7 initialization decision evidence.
    pairs["RES-STAGE-0.5-C6-C7-OFFLINE-V1"] = [("code/outputs/formal/calibration/stage_0_5_c6_c7_offline_v1/portable/" + name, name) for name in ['comparison_summary.json', 'execution_ledger.json', 'independent_verification.json', 'initialization_evidence.json', 'initialization_policy.json', 'provenance.json', 'raw_artifact_SHA256SUMS.txt', 'SHA256SUMS', 'test_record.json']]

    # Stage 0.5 real-traffic reconstruction and conditional scene diagnostics.
    pairs.setdefault("RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1", [])
    for name in (
        "PLAN_SHA256", "SHA256SUMS", "boundary_flow_30s.csv", "boundary_flows.json",
        "capacity_diagnosis.json", "cluster_uncertainty.json", "conservation.json",
        "experiment_plan.json", "fundamental_diagram_30s.csv", "hypothesis_register.json",
        "interaction_stats.json", "jam_waves.json", "lane_geometry.json", "local_state.json",
        "manifest.json", "occupancy_30s.csv", "official_crosscheck.json",
        "official_reference_provenance.json", "ramp_flows.json",
        "reconstruction_summary.json", "sectional_minimum_300s.csv", "source_audit.json",
        "space_time_60s.csv",
    ):
        pairs["RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_trajectory_reconstruction_v1/{name}", name)
        )
    for name in (
        "PLAN_SHA256", "SHA256SUMS", "diagnostic_plan.json", "manifest.json",
        "real_local_context.json", "run_ledger.json", "run_metadata.json",
        "scene_vs_real_congested_branch.json", "state_support_verdict.json",
    ):
        pairs["RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_scene_reconstruction_v1/{name}", f"scene_{name}")
        )
    for run_id in ("RC1", "RC2", "RC3"):
        pairs["RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1"].append(
            (
                f"code/outputs/formal/calibration/stage_0_5_scene_reconstruction_v1/runs/{run_id}/summary.json",
                f"runs_{run_id}_summary.json",
            )
        )

    # Stage 0.5 method diagnostics: jam-definition sensitivity, null model, leader replay.
    pairs.setdefault("RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1", [])
    for name in (
        "REPLAY_PLAN_SHA256", "SHA256SUMS", "budget_ledger_audit.json",
        "jam_definition_rules.csv", "jam_definition_sensitivity.json", "manifest.json",
        "phase_c_decision.json", "replay_plan.json", "replay_summary.json", "run_metadata.json",
    ):
        pairs["RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_method_diagnostics_v1/{name}", name)
        )

    # AAD-0.5-METHOD-EXPANSION: coverage, initialization, response, identifiability.
    pairs.setdefault("RES-STAGE-0.5-METHOD-EXPANSION-V1", [])
    for name in (
        "INIT_PLAN_SHA256", "NEWELL_PLAN_SHA256", "RESPONSE_PLAN_SHA256", "SHA256SUMS",
        "identifiability_summary.json", "init_plan.json", "init_routes.csv", "init_summary.json",
        "macro_decision.json", "manifest.json", "newell_metrics.csv", "newell_plan.json",
        "newell_summary.json", "response_metrics.csv", "response_plan.json", "response_summary.json",
        "run_metadata.json", "selection_manifest.json", "source_audit.json",
        "trajectory_coverage_summary.json",
    ):
        pairs["RES-STAGE-0.5-METHOD-EXPANSION-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_method_expansion_v1/{name}", name)
        )

    # AAD-0.5-CLOSURE: conditional state support (following relation, state domain,
    # declared supply x behaviour grid, structural variant, frozen temporal validation).
    pairs.setdefault("RES-STAGE-0.5-STATE-SUPPORT-V1", [])
    for name in (
        "PLAN_SHA256", "STRUCTURAL_PLAN_SHA256", "SHA256SUMS", "experiment_plan.json",
        "structural_plan.json", "real_domain.json", "real_block_cloud.csv",
        "real_block_cloud_us101__0750_0805.csv", "real_block_cloud_us101__0805_0820.csv",
        "grid_results.json", "state_support_verdict.json", "seed_repeats.json",
        "structural_results.json", "mechanism_analysis.json", "freeze_manifest.json",
        "temporal_validation.json",
    ):
        pairs["RES-STAGE-0.5-STATE-SUPPORT-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_state_support_v1/{name}", name)
        )

    # AAD-0.5-ARRIVAL-TIMING: boundary event reconstruction, parity audit, relative-speed
    # wave diagnostic, paired U/E contrast and the realised-arrival fidelity audit.
    pairs.setdefault("RES-STAGE-0.5-ARRIVAL-TIMING-V1", [])
    for name in (
        "PLAN_SHA256", "SHA256SUMS", "experiment_plan.json", "phase_a_audit_summary.json",
        "arrival_summary.json", "phase_b_wave_diagnostic.json", "event_manifest.json",
        "run_results.json", "run_metrics.csv", "paired_analysis.json",
        "fidelity_metrics.csv", "verdict.json",
    ):
        pairs["RES-STAGE-0.5-ARRIVAL-TIMING-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/{name}", name)
        )

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
    for name in (
        "analysis_reference_access_audit.json", "audit.json", "boundary_condition_manifest.json",
        "config.json", "controlled_access_audit.json", "data_isolation_preflight.json",
        "engineering_input_bundle.json", "execution_guard_audit.json", "execution_ledger.json",
        "execution_stop_observation.json", "experiment_plan.json", "figure_index.json",
        "fixed_parameter_manifest.json", "fleet_and_initialization_audit.json", "following_risk_diagnostics.json",
        "manifest.json", "mechanism_hypothesis_matrix.json", "network_variant_manifest.json",
        "numerical_method_audit.json", "numerical_stop_diagnostic.json", "paired_input_contract_audit.json",
        "phase1_checkpoint.json", "plan_revision_audit.json", "PLAN_SHA256", "preparation_manifest.json",
        "prior_v1_execution_ledger.json", "prior_v1_experiment_plan.json", "prior_v1_summary.json",
        "prior_v1_worker_b1_A_s20261019.json", "provenance.json", "queue_diagnostics.json",
        "real_reference_summary.json", "real_strata_summary.json", "report.md", "researcher_decision_matrix.json",
        "run_manifest.json", "run_metrics.csv", "runtime_budget_audit.json", "SHA256SUMS",
        "source_access_audit.json", "source_manifest.json", "source_staging_manifest.json",
        "test_record.json", "test_scope_audit.json", "time_bins_60s.csv", "time_series_5s.csv",
        "traffic_conservation_audit.json", "traffic_state_comparison.json",
    ):
        pairs["RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_boundary_bottleneck_v2/summary/{name}", name)
        )
    for name in (
        "audit.json", "controlled_access_audit.json", "data_isolation_preflight.json",
        "displacement_branch_contract.json", "displacement_test_matrix.json", "execution_ledger.json",
        "experiment_plan.json", "future_experiment_preconditions.json", "git_source_binding_audit.json", "historical_b1_status_preservation.json",
        "historical_source_manifest.json", "micro_fixture_manifest.json", "micro_input_bundle.json",
        "micro_sumo_numerical_audit.json", "official_source_manifest.json", "old_new_method_comparison.json",
        "PLAN_SHA256", "provenance.json", "queue_observation_contract.json", "runtime_budget_audit.json",
        "source_staging_manifest.json", "spillback_qualification_candidates.json", "stopping_source_audit.json",
        "synthetic_queue_test_matrix.json", "synthetic_queue_truth.json", "test_record.json",
        "report.md", "manifest.json", "SHA256SUMS",
    ):
        pairs["RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_stopping_spillback_v1/summary/{name}", name)
        )
    for name in (
        "action_step_semantics.json", "audit.json", "controlled_access_audit.json",
        "data_isolation_preflight.json", "debug_feasibility_audit.json", "execution_ledger.json",
        "experiment_plan.json", "future_b1_2_preconditions.json", "git_source_binding_audit.json",
        "historical_source_manifest.json", "historical_status_preservation.json",
        "independent_observation_audit.json", "micro_fixture_manifest.json", "micro_input_bundle.json",
        "non_intrusiveness_audit.json", "numerical_admission_options.json",
        "official_observability_source_audit.json", "official_source_manifest.json", "PLAN_SHA256",
        "provenance.json", "source_staging_manifest.json", "stopping_identifiability_matrix.json",
        "test_record.json", "report.md", "manifest.json", "SHA256SUMS",
    ):
        pairs["RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1"].append(
            (f"code/outputs/formal/calibration/stage_0_5_stopping_observability_v3/summary/{name}", name)
        )
    for name in (
        "analysis_access_audit.json", "audit.json", "boundary_condition_manifest.json", "config.json",
        "controlled_access_audit.json", "coordinate_support_audit.json", "data_isolation_preflight.json",
        "empty_network_prechecks.json", "engineering_input_bundle.json", "execution_guard_audit.json",
        "execution_ledger.json", "execution_stop_observation.json", "experiment_plan.json", "following_risk_diagnostics.json",
        "git_source_binding_audit.json", "historical_status_preservation.json", "integration_ledger.json", "integration_plan.json",
        "local_global_accounting_audit.json", "manifest.json", "mechanism_hypothesis_matrix.json", "near_zero_source_audit.json",
        "network_variant_manifest.json", "numerical_admission_policy.json", "numerical_branch_coverage.json",
        "observability_integration_audit.json", "official_source_manifest.json", "PLAN_SHA256", "preparation_manifest.json",
        "prior_unexecuted_ledger.json", "prior_unexecuted_plan.json", "provenance.json", "queue_integration_contract.json",
        "queue_integration_test_matrix.json", "queue_spillback_diagnostics.json", "renderer_revision_audit.json", "report.md",
        "research_conflict.json", "researcher_decision_matrix.json", "run_manifest.json", "runtime_budget_audit.json",
        "SHA256SUMS", "source_manifest.json", "source_staging_manifest.json", "spacetime_diagnostics.json",
        "test_record.json", "traffic_state_comparison.json",
    ):
        pairs["RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2"].append(
            (f"code/outputs/formal/calibration/stage_0_5_boundary_revalidation_b12_v2/summary/{name}", name)
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
    # B1.2-N exports only this explicit closed micro-observability summary.
    for name in ('PLAN_SHA256', 'SHA256SUMS', 'analysis_access_audit.json', 'audit.json', 'config.json', 'controlled_access_audit.json', 'engineering_input_bundle.json', 'engineering_input_lineage.json', 'execution_scope_audit.json', 'experiment_plan.json', 'git_source_binding_audit.json', 'historical_status_preservation.json', 'integration_C_audit.json', 'integration_D_audit.json', 'integration_preflight.json', 'lane_change_and_exit_diagnostics.json', 'local_global_accounting_audit.json', 'manifest.json', 'micro_checkpoint.json', 'micro_ledger.json', 'micro_plan.json', 'near_zero_observability_matrix.json', 'near_zero_runtime_diagnostics.json', 'near_zero_source_contract.json', 'near_zero_test_matrix.json', 'numerical_admission_candidate.json', 'numerical_branch_coverage.json', 'preparation_manifest.json', 'provenance.json', 'queue_integration_diagnostics.json', 'report.md', 'researcher_decision_matrix.json', 'run_manifest.json', 'runtime_budget_audit.json', 'source_staging_manifest.json', 'task_ledger.json', 'test_record.json', 'unresolved_context_audit.json'):
        pairs.setdefault("RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1", []).append(
            (f"code/outputs/formal/calibration/stage_0_5_near_zero_integration_v1/summary/{name}", name)
        )
    # Independent positive-only numerical micro evidence; never raw states.
    for name in (
        'PLAN_SHA256',
        'SHA256SUMS',
        'admission.json',
        'analysis_access_audit.json',
        'audit.json',
        'control_edges.json',
        'controlled_access_audit.json',
        'debug_build_feasibility.json',
        'execution_ledger.json',
        'experiment_plan.json',
        'git_source_binding_audit.json',
        'historical_status_preservation.json',
        'manifest.json',
        'micro_input_bundle.json',
        'numerical_branch_coverage.json',
        'preflight.json',
        'preparation_manifest.json',
        'provenance.json',
        'report.md',
        'researcher_decision_matrix.json',
        'run_manifest.json',
        'runtime_budget_audit.json',
        'runtime_settings_audit.json',
        'source_audit.json',
        'source_observability_audit.json',
        'source_staging_manifest.json',
        'target_edges.json',
        'test_record.json',
        'unresolved_edges.json',
        'vehicle_conservation_audit.json',
    ):
        pairs.setdefault("RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1", []).append(
            (f"code/outputs/formal/calibration/stage_0_5_positive_near_zero_v1/summary/{name}", name)
        )
    for name in ('C_checkpoint.json', 'C_departures.json', 'C_exits.json', 'C_lane_changes.json', 'C_summary.json', 'D_checkpoint.json', 'D_departures.json', 'D_exits.json', 'D_lane_changes.json', 'D_summary.json', 'PLAN_SHA256', 'SHA256SUMS', 'admission.json', 'analysis_access_audit.json', 'audit.json', 'budget_authorization.json', 'capsule_copy_audit.json', 'cd_source_staging.json', 'controlled_access_audit.json', 'coordinate_support_audit.json', 'engineering_input_bundle.json', 'execution_ledger.json', 'execution_scope_audit.json', 'experiment_plan.json', 'following_state_diagnostics.json', 'git_source_binding_audit.json', 'historical_status_preservation.json', 'independent_counterexamples.json', 'input_lineage.json', 'issue_discovery_report.json', 'local_global_accounting_audit.json', 'manifest.json', 'next_task_plan.json', 'numerical_admission_policy.json', 'numerical_branch_coverage.json', 'preflight.json', 'preparation_manifest.json', 'prior_D_revalidation.json', 'provenance.json', 'queue_integration_diagnostics.json', 'raw_local_bindings.json', 'report.md', 'researcher_decision_matrix.json', 'run_manifest.json', 'runtime_budget_audit.json', 'source_audit.json', 'test_record.json', 'traffic_state_comparison.json', 'v1_controlled_access_audit.json', 'v1_execution_ledger.json', 'v1_experiment_plan.json', 'v1_preflight.json'):
        pairs.setdefault("RES-STAGE-0.5-CD-INTEGRATION-V1", []).append(
            (f"code/outputs/formal/calibration/stage_0_5_cd_integration_v2/summary/{name}", name)
        )
    for name in (
        'PLAN_SHA256',
        'SHA256SUMS',
        'admission.json',
        'analysis_access_audit.json',
        'analysis_output_bindings.json',
        'audit.json',
        'boundary_test_matrix.json',
        'budget_audit.json',
        'controlled_access_audit.json',
        'dependency_before_after_audit.json',
        'dependency_fingerprints.json',
        'engineering_input_bundle.json',
        'event_boundary_computability.json',
        'execution_ledger.json',
        'experiment_plan.json',
        'extension_access_audit.json',
        'formal_adapter_break_counterexample.json',
        'full600_forecast_scenarios.json',
        'gap_offline_analysis.json',
        'git_source_binding_audit.json',
        'historical_status_preservation.json',
        'issue_discovery_report.json',
        'lf_preparation.json',
        'lf_source_staging.json',
        'local_following_results.json',
        'local_global_accounting_audit.json',
        'local_measurement_contract.json',
        'local_measurement_support_matrix.json',
        'local_traffic_diagnostics.json',
        'manifest.json',
        'numerical_branch_coverage.json',
        'offline_CD_C_staging.json',
        'paired_equivalence.json',
        'performance_audit.json',
        'point_gap_independent_audit.json',
        'prefix_consistency_audit.json',
        'preflight.json',
        'preparation_manifest.json',
        'protocol_source_audit.json',
        'provenance.json',
        'report.md',
        'researcher_decision_matrix.json',
        'run_manifest.json',
        'source_audit.json',
        'test_record.json',
):
        pairs.setdefault("RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1", []).append(
            (f"code/outputs/formal/calibration/stage_0_5_local_following_v1/summary/{name}", name)
        )
    for name in (
        'PLAN_SHA256','SHA256SUMS','analyse_access_audit.json','analyse_execution.json',
        'approved_reference_support.json','attribution_summary.json','audit.json',
        'conditional_cluster_uncertainty.json','demand_identifiability_matrix.json','denominator_audit.json',
        'event_attribution_audit.csv','execution_ledger.json','experiment_plan.json','git_source_bindings.json',
        'historical_status_preservation.json','independent_recomputation.json','isolation_preflight.json',
        'issue_discovery_report.json','local_measurement_candidate.json','manifest.json','method_sources.json',
        'preparation.json','provenance.json','report.md','researcher_decision_matrix.json',
        'scientific_admission_table.json','source_manifest.json','temporal_boundary_audit.json','test_record.json',
        'tests_access_audit.json','tests_execution.json','traffic_cycle_audit.json','traffic_state_1s.csv',
        'traffic_state_30s.csv','warmup_candidate_analysis.json','window_sensitivity.json',
    ):
        pairs.setdefault('RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1', []).append(
            (f'code/outputs/formal/calibration/stage_0_5_lf_protocol_v1/summary/{name}',name)
        )
    for name in (
        'audit.json','candidate_analyse_FC1_access_audit.json','candidate_analyse_FC2_access_audit.json',
        'candidate_empty_all_access_audit.json','candidate_empty_preflight.json','candidate_execution_guard_audit.json',
        'candidate_experiment_plan.json','candidate_isolation_probe.json','candidate_PLAN_SHA256',
        'candidate_probe_all_access_audit.json','candidate_run_ledger.json','candidate_run_summary.json',
        'candidate_worker_FC1_access_audit.json','candidate_worker_FC2_access_audit.json','cluster_exposure_audit.csv',
        'delta_h_basis_audit.json','event_attribution_audit.csv','execution_ledger.json','five_layer_admission.json',
        'historical_status_preservation.json','isolation_evidence.json','issue_discovery_report.json',
        'member_support_audit.csv','provenance.json','real_local_reference_summary.json',
        'real_us101__0750_0805_full_acquisition_P2.json','real_us101__0750_0805_interior_P2.json',
        'real_us101__0750_0805_joint_uncertainty.json','real_us101__0750_0805_P2_cluster_uncertainty.json',
        'real_us101__0750_0805_source_audit.json','real_us101__0750_0805_traffic_metrics.json',
        'real_us101__0805_0820_full_acquisition_P2.json','real_us101__0805_0820_interior_P2.json',
        'real_us101__0805_0820_joint_uncertainty.json','real_us101__0805_0820_P2_cluster_uncertainty.json',
        'real_us101__0805_0820_source_audit.json','real_us101__0805_0820_traffic_metrics.json',
        'reference_REFERENCE_PLAN_SHA256','reference_isolation_policy.json','reference_preparation.json',
        'reference_reference_plan.json','reference_reference_us101__0750_0805_access_audit.json',
        'reference_reference_us101__0805_0820_access_audit.json','reference_source_manifest.json',
        'reference_statistics_plan.json','reference_statistics_us101__0750_0805_access_audit.json',
        'reference_statistics_us101__0805_0820_access_audit.json','reference_test_pass.json',
        'reference_tests_tests_access_audit.json','report.md','researcher_decision_package.json',
        'sim_FC1_P2.json','sim_FC1_state_support_blocks.json','sim_FC1_traffic_metrics.json',
        'sim_FC2_P2.json','sim_FC2_state_support_blocks.json','sim_FC2_traffic_metrics.json',
        'stage_0_6_handoff.json','state_support_verdict.json','test_record.json','manifest.json','SHA256SUMS',
    ):
        pairs.setdefault('RES-STAGE-0.5-FINAL-CLOSURE-V1', []).append(
            (f'code/outputs/formal/calibration/stage_0_5_final_closure_package/summary/{name}', name)
        )
    # Preserve the independently registered Stage 0.5 extensions in full exports.
    for result_id, directory, names in [
        ('RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1', 'stage_0_5_depart_speed_candidate_v1',
         ['impact_summary.json', 'official_semantics.json', 'review_proposal.json',
          'provenance.json', 'validation_record.json', 'boundary_summary.json',
          'PROPOSAL_SHA256', 'SHA256SUMS']),
        ('RES-STAGE-0.5-INTERACTION-RESEARCH-V2', 'stage_0_5_interaction_research_v2',
         ['audit.json', 'budget_config.json', 'run_matrix.json', 'review_proposal.json',
          'ledger_snapshot.json', 'provenance.json', 'validation_record.json', 'SHA256SUMS']),
        ('RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1', 'stage_0_5_v2_admission_engineering_v1',
         ['identity_contract.json', 'initialization_audit.json', 'history_allowlist.json',
          'C6_comparison.json', 'C6_independent_verification.json', 'admission_profile.json',
          'provenance.json', 'validation_record.json', 'SHA256SUMS']),
        ('RES-STAGE-0.5-B00-NATIVE-V1', 'stage_0_5_b00_native_v1',
         ['execution_result.json', 'population_accounting.json', 'measurement_acceptance.json',
          'scientific_conflict.json', 'ledger_snapshot.json', 'provenance.json',
          'artifact_sha256.json', 'validation_record.json', 'SHA256SUMS']),
        ('RES-AAD-WEEK-20261027-V1', 'aad_week_20261027_v1',
         ['audit.json', 'population_accounting.json', 'measurement_acceptance.json',
          'independent_execution_receipt.json', 'scene_audit.json', 'matched18.csv',
          'failure_archive.json', 'provenance.json', 'validation_record.json',
          'ledger_snapshot.json', 'manifest.json', 'SHA256SUMS']),
        ('RES-STAGE-0.5-R0-DESIGN-PACKET-20261028', 'stage_0_5_r0_20261028_v2',
         ['baseline_binding.json', 'source_event_support.json', 'source_target_candidates.json',
          'scenario_diff_matrix.json', 'ramp_departure_map_candidate.csv', 'arm_input_candidates.json', 'topology_candidate_audit.json',
          'decision_register.json', 'r0_gate_report.json', 'manifest.json', 'validation_record.json', 'SHA256SUMS']),
        ('RES-STAGE-0.5-R1-DIAGNOSTICS-20261028', 'stage_0_5_r1_diagnostics_20261028',
         ['r1_design_freeze.json', 'run_admission_B10.json', 'run_admission_B01.json', 'run_admission_B11.json',
          'measurement_acceptance.json', 'arm_comparison.json', 'source_event_support.json',
          'physical_path_audit.json', 'r2_gate_review.json', 'manifest.json', 'validation_record.json', 'SHA256SUMS',
          'B10_independent_receipt.json', 'B10_execution_summary.json', 'B10_measurement_acceptance.json',
          'B01_independent_receipt.json', 'B01_execution_summary.json', 'B01_measurement_acceptance.json',
          'B11_independent_receipt.json', 'B11_execution_summary.json', 'B11_measurement_acceptance.json']),
        ('RES-STAGE-0.5-OFFLINE-MECHANISM-AUDIT-20261028', 'stage_0_5_offline_mechanism_audit_20261028',
         ['event_inventory.csv', 'spatial_counts.csv', 'source_observability.csv', 'arm_state_blocks.csv',
          'count_reconciliation.json', 'validation_record.json', 'manifest.json', 'SHA256SUMS']),
        ('RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028', 'stage_0_5_first_round_offline_decision_20261028',
         ['candidate_comparison_matrix.json', 'file_audit.csv', 'offline_reconciliation.json', 'run_record.json', 'validation_summary.json', 'manifest.json', 'SHA256SUMS']),
        ('RES-STAGE-0.6-WEEK-20261027-V1', 'stage_0_6_week_20261027_v1',
         ['audit.json', 'numerical_manifest.json', 'protocol_candidate.json',
          'current_gate_reports.json', 'stage_0_5_gate.json', 'stage_0_6_gate.json',
          'protocol_lock_readiness.json', 'protocol_lock_writer_check.json',
          'input_manifest.json', 'provenance.json', 'validation_record.json',
          'manifest.json', 'SHA256SUMS']),
    ]:
        pairs[result_id] = [
            ('code/outputs/formal/calibration/' + directory + '/portable/' + name, name)
            for name in names
        ]
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
    aggregate_names={"common_support_18_cells.csv","PROPOSAL_SHA256","REVIEW_PROPOSAL_SHA256",'us101__0750_0805_baseline_offset100.csv','us101__0750_0805_common_support.csv','us101__0750_0805_real_offset100.csv','us101__0805_0820_baseline_offset100.csv','us101__0805_0820_common_support.csv','us101__0805_0820_real_offset100.csv',"SHA256SUMS","PLAN_SHA256","run_metrics.csv","time_bins_60s.csv","time_series_5s.csv",
        "event_attribution_audit.csv","traffic_state_1s.csv","traffic_state_30s.csv",
        "member_support_audit.csv","cluster_exposure_audit.csv",
        "candidate_PLAN_SHA256","reference_REFERENCE_PLAN_SHA256",
        "boundary_flow_30s.csv","fundamental_diagram_30s.csv","occupancy_30s.csv",
        "sectional_minimum_300s.csv","space_time_60s.csv","jam_definition_rules.csv",
        "REPLAY_PLAN_SHA256","INIT_PLAN_SHA256","RESPONSE_PLAN_SHA256","NEWELL_PLAN_SHA256",
        "init_routes.csv","newell_metrics.csv","response_metrics.csv",
        "STRUCTURAL_PLAN_SHA256","real_block_cloud.csv",
        "real_block_cloud_us101__0750_0805.csv","real_block_cloud_us101__0805_0820.csv",
        "fidelity_metrics.csv", "matched18.csv",
        # Explicit R0 design input map, not a raw measured trajectory table.
        "ramp_departure_map_candidate.csv",
        # Stage 0.5 offline mechanism audit aggregate tables.
        "event_inventory.csv", "spatial_counts.csv", "source_observability.csv", "arm_state_blocks.csv",
        # Task 4 derived descriptive summaries; these are not raw trajectory tables.
        "real_source_target_exposure.csv", "real_source_target_state_metrics.csv",
        "risk_event_attribution_summary.csv", "simulation_source_target_metrics.csv",
        "corrected_real_source_target_state_metrics.csv", "corrected_simulation_source_target_metrics.csv",
        "time_block_statistics_diff.csv",
        # Task6 counts, quantiles and joint histograms; never identity-level rows.
        "event_context_summary.csv", "event_relative_profiles.csv",
        "evidence_reuse_matrix.csv", "gap_closing_joint_histogram.csv",
        "independent_time_block_joint_metrics.csv", "joint_distribution_summary.csv",
        "macro_common_support_cells.csv",
        # Task7 official file metadata, not traffic observations or case identities.
        "documented_video_resources.csv",
        # Task7.1 metadata/coverage and 130 ID-free, risk-independent controls only.
        "camera_localy_coverage.csv", "spatial_control_points.csv",
        "license_resource_matrix.csv",
        # Task8: ordinal event/control derived diagnostics and seven anonymous cases.
        'event_precursor_decomposition.csv', 'control_precursor_decomposition.csv',
        'precursor_summary.csv', 'event_control_comparison.csv', 'precursor_profiles.csv',
        'sumo_near_threshold_profiles.csv', 'sumo_near_threshold_cases.csv',
        # Task7.2: four raw-file inventory and official license/time statements.
        "resource_inventory.csv", "license_scope_matrix.csv", "time_metadata_matrix.csv",
        }
    if source.suffix.lower() not in {".json", ".md", ".txt", ".sha256"} and source.name not in aggregate_names:
        raise ValueError(f"unsupported evidence file type: {source}")


def export_evidence(repo_root: Path, result_ids: set[str] | None = None) -> dict[str, object]:
    evidence_root = repo_root / "evidence"
    previous_path = evidence_root / "EVIDENCE_MANIFEST.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {"results": []}
    # Later sealed bundles are deliberately registered in place. Never replace
    # them with an older output/portable source or drop them on a full export.
    # Registration/authorized resealing is separate: drift must fail here.
    self_managed = {
        entry["result_id"]: entry for entry in previous["results"]
        if entry.get("files") and all(f.get("source_path") == f.get("snapshot_path")
                                      for f in entry["files"])
    }
    result_entries: list[dict[str, object]] = []
    for result_id, pairs in _source_pairs().items():
        if result_ids is not None and result_id not in result_ids:
            continue
        if result_id in self_managed:
            continue
        files: list[dict[str, object]] = []
        for source_raw, destination_tail in pairs:
            source = repo_root / source_raw
            _validate_source(source)
            destination = evidence_root / "results" / result_id / destination_tail
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Sealed history may be read-only. Equal snapshots need no write;
            # different bytes still require the existing explicit copy path.
            if not destination.is_file() or _sha256(source) != _sha256(destination):
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

    for result_id, entry in self_managed.items():
        if result_ids is not None and result_id not in result_ids:
            continue
        for item in entry["files"]:
            source = (repo_root / item["snapshot_path"]).resolve()
            if not source.is_relative_to(evidence_root.resolve()) or not source.is_file():
                raise ValueError("invalid self-managed evidence path: " + item["snapshot_path"])
            if source.stat().st_size != item["size_bytes"] or _sha256(source) != item["sha256"]:
                raise ValueError("self-managed evidence drift; explicit resealing required: " + item["snapshot_path"])
        result_entries.append(entry)

    if result_ids is not None:
        unknown = result_ids - {entry['result_id'] for entry in result_entries}
        if unknown:
            raise ValueError('unknown scoped result IDs: ' + ','.join(sorted(unknown)))
        previous_path = evidence_root / 'EVIDENCE_MANIFEST.json'
        previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {'results': []}
        replacements = {entry['result_id']: entry for entry in result_entries}
        merged = [replacements.pop(entry['result_id'], entry) for entry in previous['results']]
        result_entries = merged + list(replacements.values())

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


def verify_evidence(repo_root: Path, result_ids: set[str] | None = None) -> list[str]:
    issues: list[str] = []
    manifest_path = repo_root / "evidence/EVIDENCE_MANIFEST.json"
    if not manifest_path.is_file():
        return ["missing evidence/EVIDENCE_MANIFEST.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for result in manifest.get("results", []):
        if result_ids is not None and result['result_id'] not in result_ids:
            continue
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
    parser.add_argument('--result-id', action='append', help='Restrict local source access to named results; preserve other manifest entries.')
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    if args.verify:
        issues = verify_evidence(repo_root, set(args.result_id) if args.result_id else None)
        if issues:
            print("PORTABLE_EVIDENCE_INVALID")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("PORTABLE_EVIDENCE_OK")
        return 0
    manifest = export_evidence(repo_root, set(args.result_id) if args.result_id else None)
    file_count = sum(len(item["files"]) for item in manifest["results"])
    print(f"PORTABLE_EVIDENCE_EXPORTED results={len(manifest['results'])} files={file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
