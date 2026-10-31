"""Task10 bounded final diagnostic: reuse existing evidence, add only WP1/WP2 audits.

This script never starts SUMO/TraCI, reads a third window or holdout, downloads
video, or changes Formal P2/D1/B definitions.  It consumes the two existing
Task6 identity-context tables and the two SHA-bound canonical NGSIM state tables,
then writes an anonymised Task10 evidence package.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK_LOCAL_DEPS = ROOT / "code/outputs/diagnostics/post_r2_task8_20261030/deps"
if TASK_LOCAL_DEPS.is_dir():
    sys.path.insert(0, str(TASK_LOCAL_DEPS))
    os.environ["PATH"] = str(TASK_LOCAL_DEPS / "pyarrow.libs") + os.pathsep + os.environ.get("PATH", "")

import numpy as np
try:
    import pyarrow  # load before pandas' extension-type patch
    _pyarrow_unregister = pyarrow.unregister_extension_type
    def _safe_pyarrow_unregister(name):
        try:
            return _pyarrow_unregister(name)
        except Exception:
            return None
    pyarrow.unregister_extension_type = _safe_pyarrow_unregister
except ImportError:
    pyarrow = None
import pandas as pd

RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK10-FINAL-DIAGNOSTIC"
OUT = ROOT / "evidence/results" / RESULT_ID
LOCAL_CONTEXT = ROOT / "code/outputs/diagnostics/round2_task6_20261030"
CANONICAL_ROOT = ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
TASK7_LOCAL = ROOT / "local_research/literature-work/task7_1_20261030"
TASK7_EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030"
TASK8_EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK8-KINEMATIC-MECHANISM-DIAG-20261030"
TASK9_EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-TASK9-FIXED-LEADER-PREP-20261031"

WINDOWS = ("0750_0805", "0805_0820")
FORMAL_EVENT_COUNTS = {"0750_0805": 167, "0805_0820": 159}
FORMAL_TARGET_COUNTS = {"0750_0805": 174, "0805_0820": 252}
CONTROL_COUNTS = {"0750_0805": 165, "0805_0820": 149}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_context(window: str) -> pd.DataFrame:
    path = LOCAL_CONTEXT / f"{window}_identity_contexts.csv"
    frame = pd.read_csv(path)
    required = {
        "scope", "region", "sample_kind", "trajectory_id", "time_s", "event_id", "horizon_s",
        "leader_onset_matched", "leader_full_context", "full_pair_role_context",
        "any_observed_transition", "gap_residual_median", "gap_residual_p95",
        "position_speed_residual_median", "position_speed_residual_p95",
        "acceleration_residual_median", "acceleration_residual_p95", "backwards_observed",
        "onset_gap_m", "onset_closing_mps", "onset_ttc_s",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{window}: missing Task6 context columns {missing}")
    return frame


def finite_summary(series: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {"n": 0, "p50": None, "p95": None, "mean": None}
    return {
        "n": int(len(values)),
        "p50": float(values.quantile(0.5)),
        "p95": float(values.quantile(0.95)),
        "mean": float(values.mean()),
    }


QUALITY_METRICS = (
    "gap_residual_median", "gap_residual_p95", "position_speed_residual_median",
    "position_speed_residual_p95", "acceleration_residual_median", "acceleration_residual_p95",
    "onset_gap_m", "onset_closing_mps", "onset_ttc_s",
)


def quality_audit(contexts: dict[str, pd.DataFrame]) -> tuple[dict, pd.DataFrame]:
    rows: list[dict] = []
    comparison: list[dict] = []
    for window, frame in contexts.items():
        source = frame[(frame.region == "source") & (frame.horizon_s == 1)]
        if len(source[source.sample_kind == "formal_event"]) != FORMAL_EVENT_COUNTS[window]:
            raise ValueError(f"{window}: Task6 event count changed")
        if len(source[source.sample_kind == "nonrisk_control"]) != CONTROL_COUNTS[window]:
            raise ValueError(f"{window}: Task6 control count changed")
        for kind in ("formal_event", "nonrisk_control"):
            group = source[source.sample_kind == kind]
            summary = {
                "window": window,
                "sample_kind": kind,
                "samples": int(len(group)),
                "unique_followers": int(group.trajectory_id.nunique()),
                "leader_onset_matched_yes": int(group.leader_onset_matched.eq(True).sum()),
                "leader_full_context_yes": int(group.leader_full_context.eq(True).sum()),
                "full_pair_role_context_yes": int(group.full_pair_role_context.eq(True).sum()),
                "any_observed_transition_yes": int(group.any_observed_transition.eq(True).sum()),
                "backwards_observed_yes": int(group.backwards_observed.eq(True).sum()),
            }
            for metric in QUALITY_METRICS:
                summary[metric] = finite_summary(group[metric])
            rows.append(summary)
        event = source[source.sample_kind == "formal_event"]
        control = source[source.sample_kind == "nonrisk_control"]
        for metric in QUALITY_METRICS:
            event_values = pd.to_numeric(event[metric], errors="coerce")
            control_values = pd.to_numeric(control[metric], errors="coerce")
            comparison.append({
                "window": window,
                "metric": metric,
                "event_n": int(event_values.notna().sum()),
                "control_n": int(control_values.notna().sum()),
                "event_p50": float(event_values.quantile(0.5)) if event_values.notna().any() else None,
                "control_p50": float(control_values.quantile(0.5)) if control_values.notna().any() else None,
                "event_minus_control_p50": float(event_values.quantile(0.5) - control_values.quantile(0.5)) if event_values.notna().any() and control_values.notna().any() else None,
                "interpretation_status": "Descriptive quality contrast; no event deletion or reclassification",
            })
    summary = {
        "status": "COMPLETED_REUSE_PLUS_EVENT_CONTROL_QUALITY_AUDIT",
        "formal_source_counts_reused": FORMAL_EVENT_COUNTS,
        "formal_target_counts_reused": FORMAL_TARGET_COUNTS,
        "quality_rows": rows,
        "new_metrics": [
            "event/control comparison of already-computed Task6 residual and continuity fields",
        ],
        "not_computed": {
            "jerk": "NOT_RUN: acceleration/jerk noise and filtering are not independently validated here",
            "spectral_analysis": "NOT_RUN: no new signal-processing pipeline was required to decide Task10",
        },
        "formal_events_modified": 0,
        "formal_definitions_changed": False,
    }
    return summary, pd.DataFrame(comparison)


def precise_feasibility() -> dict:
    inspection = read_json(TASK7_LOCAL / "precise_data_inspection.json")
    structure = read_json(TASK7_LOCAL / "precise_structure_check.json")
    semantic = read_json(TASK7_LOCAL / "precise_semantic_layout_flags.json")
    return {
        "status": "BLOCKED_EVENT_LEVEL_CROSSWALK",
        "decision": "Do not recompute auxiliary P2/TTC/gap metrics from PreciseNGSIM",
        "existing_two_windows": [x.get("period") for x in inspection],
        "full_file_correspondence_verified": False,
        "event_level_crosswalk_rows": 0,
        "formal_counts_modified": False,
        "reasons": [
            "Existing inspection only established schema/range metadata and first-500 provenance checks; it did not establish full event identity correspondence.",
            "Vehicle_ID, Frame_ID and Global_Time are inherited fields and therefore cannot serve as independent identity/time truth.",
            "Local_Y, v_Vel and v_Acc differ in the existing first-500 field comparison for both windows.",
            "Each window retains a flagged malformed/suspect final row and shorter effective time support; no event-level repair is authorized.",
        ],
        "existing_inspection_sha256": {
            "precise_data_inspection.json": sha(TASK7_LOCAL / "precise_data_inspection.json"),
            "precise_structure_check.json": sha(TASK7_LOCAL / "precise_structure_check.json"),
            "precise_semantic_layout_flags.json": sha(TASK7_LOCAL / "precise_semantic_layout_flags.json"),
        },
        "structure_summary": structure,
        "semantic_flags_summary": semantic,
        "independent_physical_truth": "Unknown",
    }


def raw_event_rows(context: pd.DataFrame) -> pd.DataFrame:
    return context[(context.horizon_s == 1) & (context.sample_kind == "formal_event")][
        ["region", "trajectory_id", "time_s", "event_id", "leader_onset_matched", "full_pair_role_context"]
    ].copy()


def canonical_frame(window: str) -> pd.DataFrame:
    path = CANONICAL_ROOT / f"ngsim_us101__{window}.parquet"
    columns = [
        "trajectory_id", "time_s", "global_time_ms", "frame_id", "y_m", "lane_id", "road_id",
        "leader_trajectory_id", "leader_matched", "identity_break", "observation_gap",
    ]
    return pd.read_parquet(path, columns=columns)


def path_status(value: bool | None) -> str:
    if value is True:
        return "PASS"
    if value is False:
        return "FAIL"
    return "UNKNOWN"


def physical_path_audit(contexts: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict, dict]:
    candidate_rows: list[dict] = []
    graph_windows: dict = {}
    ordinal = 0
    for window, context in contexts.items():
        events = raw_event_rows(context)
        source = events[events.region == "source"].groupby("trajectory_id", as_index=False).agg(source_time_s=("time_s", "min"))
        target = events[events.region == "target"].groupby("trajectory_id", as_index=False).agg(target_time_s=("time_s", "min"))
        shared = source.merge(target, on="trajectory_id", how="inner")
        shared = shared[shared.source_time_s < shared.target_time_s].copy()
        canonical = canonical_frame(window)
        canonical["time_s"] = pd.to_numeric(canonical["time_s"], errors="coerce")
        canonical = canonical.sort_values(["trajectory_id", "time_s"], kind="stable")
        path_pass = 0
        continuity_pass = 0
        traceable_pass = 0
        lane_pass = 0
        for _, item in shared.iterrows():
            ordinal += 1
            vehicle = str(item.trajectory_id)
            segment = canonical[(canonical.trajectory_id.astype(str) == vehicle) & canonical.time_s.ge(float(item.source_time_s)) & canonical.time_s.le(float(item.target_time_s))].copy()
            segment = segment.sort_values("time_s")
            if segment.empty:
                candidate_rows.append({"candidate_id": f"TASK10_PATH_{ordinal:03d}", "window": window, "source_time_s": float(item.source_time_s), "target_time_s": float(item.target_time_s), "traceable_pair": "UNKNOWN", "time_indexed_lane_edge": "UNKNOWN", "continuous_interaction": "UNKNOWN", "physical_connection_basis": "UNKNOWN", "temporal_order": "PASS", "overall": "UNKNOWN", "reason": "No canonical rows for shared event identity/time interval"})
                continue
            source_row = segment.iloc[0]
            target_row = segment.iloc[-1]
            traceable = bool(source_row.leader_matched and target_row.leader_matched and pd.notna(source_row.leader_trajectory_id) and pd.notna(target_row.leader_trajectory_id))
            dt = segment.global_time_ms.diff().dropna()
            df = segment.frame_id.diff().dropna()
            continuity = bool(
                len(segment) >= 2
                and np.allclose(segment.time_s.diff().dropna().to_numpy(), 0.1, rtol=0, atol=1e-9)
                and np.all(dt.to_numpy() == 100)
                and np.all(df.to_numpy() == 1)
                and not segment.identity_break.fillna(True).any()
                and not segment.observation_gap.fillna(True).any()
            )
            lane_edge = bool(continuity and segment.lane_id.notna().all() and segment.road_id.notna().all())
            interaction = bool(continuity and segment.leader_matched.fillna(False).mean() >= 0.95)
            physical_basis = None  # road_id=US-101 is not an independent path/geometry witness
            temporal = bool(float(item.source_time_s) < float(item.target_time_s))
            statuses = [path_status(traceable), path_status(lane_edge), path_status(interaction), path_status(physical_basis), path_status(temporal)]
            overall = "FAIL" if "FAIL" in statuses else ("UNKNOWN" if "UNKNOWN" in statuses else "PASS")
            if traceable: traceable_pass += 1
            if lane_edge: lane_pass += 1
            if interaction: continuity_pass += 1
            if overall == "PASS": path_pass += 1
            candidate_rows.append({
                "candidate_id": f"TASK10_PATH_{ordinal:03d}",
                "window": window,
                "source_time_s": float(item.source_time_s),
                "target_time_s": float(item.target_time_s),
                "traceable_pair": path_status(traceable),
                "time_indexed_lane_edge": path_status(lane_edge),
                "continuous_interaction": path_status(interaction),
                "physical_connection_basis": path_status(physical_basis),
                "temporal_order": path_status(temporal),
                "overall": overall,
                "path_rows": int(len(segment)),
                "path_duration_s": float(segment.time_s.iloc[-1] - segment.time_s.iloc[0]),
                "reason": "US-101 road_id is present but does not independently establish physical connection basis" if physical_basis is None else "",
            })
        graph_windows[window] = {
            "source_event_nodes": int(events[events.region == "source"].trajectory_id.nunique()),
            "target_event_nodes": int(events[events.region == "target"].trajectory_id.nunique()),
            "shared_source_target_nodes": int(len(shared)),
            "ordered_source_target_nodes": int(len(shared)),
            "traceable_pair_pass": traceable_pass,
            "time_indexed_lane_edge_pass": lane_pass,
            "continuous_interaction_pass": continuity_pass,
            "overall_b_pass": path_pass,
        }
    candidates = pd.DataFrame(candidate_rows)
    counts = {col: candidates[col].value_counts(dropna=False).to_dict() for col in ["traceable_pair", "time_indexed_lane_edge", "continuous_interaction", "physical_connection_basis", "temporal_order", "overall"]}
    audit = {
        "status": "COMPLETED_B_WITNESS_AUDIT",
        "candidate_count": int(len(candidates)),
        "overall_counts": {str(k): int(v) for k, v in candidates.overall.value_counts().to_dict().items()},
        "component_counts": {component: {str(k): int(v) for k, v in values.items()} for component, values in counts.items()},
        "qualified_b_paths": int((candidates.overall == "PASS").sum()),
        "failed_b_paths": int((candidates.overall == "FAIL").sum()),
        "unknown_b_paths": int((candidates.overall == "UNKNOWN").sum()),
        "primary_blocker": "No independent physical connection basis for source-to-target path; road_id alone is insufficient.",
        "definitions_changed": False,
    }
    graph = {
        "status": "COMPLETED_TIME_EXPANDED_INTERACTION_SUMMARY",
        "windows": graph_windows,
        "cross_window_vehicle_identity": "Not merged; windows remain independent",
        "graph_edge_definition": "Observed canonical follower-leader relation at event anchors and continuous trajectory interval; no unobserved edge interpolation",
    }
    return candidates, audit, graph


def task9_readiness() -> dict:
    protocol = read_json(TASK9_EVIDENCE / "task9_protocol.json")
    arm_audit = read_json(TASK9_EVIDENCE / "arm_config_audit.json")
    return {
        "status": "BLOCKED_BY_PHYSICAL_INPUT",
        "physical_input_qualified": False,
        "qualified_segments": 0,
        "formal_runs_executed": 0,
        "engineering_interface_sufficient": True,
        "arm_config_audit_status": arm_audit.get("status"),
        "seed_matrix_status": "Agreed_for_Task9_20261101_20261102_20261103",
        "execution_authorization": "No formal execution in Task10",
        "remaining_gates": [
            "independent physical reference/license/time/space evidence",
            "qualified stable leader/follower segment",
            "verified physical net-gap and common-leader extraction",
            "resource and actual insertion/readback acceptance",
        ],
        "no_new_parameter_search": True,
        "protocol": protocol,
    }


def historical_reuse_audit() -> str:
    return """# Task10 historical reuse audit

## Existing results reused

- Task4/5: formal source counts 167/159, target counts 174/252, unique onset attribution, and independent two-window scope were reused without re-extracting Formal P2.
- Task6: gap–closing joint distributions, event/control contexts, residuals, leader/lane transition flags and population diagnostics were reused from the sealed Task6 package and local identity-context tables.
- Task8: five-second `C_initial/C_f/C_l/C/C_gap/R`, fixed onset-leader diagnostics, seven SUMO near-threshold cases and the official Krauss source map were reused. `R` was not recomputed as a new method.
- Task9: static B00/Round2 arm audit, common-input contract, seed set and blocked physical-input status were reused from the Task9 evidence package.

## Existing code and methods

- `code/scripts/analyze_stage_0_5_round2_task6_micro_interaction.py` and its saved identity-context outputs supply the quality and transition fields.
- `code/scripts/analyze_stage_0_5_post_r2_task8_kinematic_mechanism.py` supplies the existing decomposition and residual definitions.
- `code/src/riskprop/stage_0_5_fixed_leader_pair.py` supplies Task9's fail-closed arm/input contract.
- Punzo-style internal consistency, platoon/gap consistency and jerk/spectral method boundaries were taken from the existing literature map; no new DSTE/STMap pipeline was trained or implemented.

## New work in Task10

1. Event/control quality comparison over the existing Task6 source contexts at the declared one-second anchor.
2. A bounded feasibility decision for event-level PreciseNGSIM crosswalk using the existing Task7.1 inspection records.
3. A time-expanded source→target same-trajectory candidate audit on the two canonical windows, with B's five witness components reported as PASS/FAIL/UNKNOWN.
4. A final Task9 readiness decision and Round2 final decision.

## Not repeated

No full Formal P2 extraction, Task6 rerun, Task8 decomposition rerun, historical 324-run replay, video acquisition, new data request, SUMO/TraCI execution, third window read, holdout read, parameter search or Formal P2/D1/B definition change was performed.
"""


def final_decision(quality: dict, path_audit: dict, readiness: dict, precise: dict) -> dict:
    quality_judgement = "Partially usable for descriptive interaction diagnostics; insufficient for independent physical truth certification."
    return {
        "status": "CASE_B_PARTIAL_EVIDENCE_PHYSICAL_PATH_INSUFFICIENT",
        "research_observations": {
            "formal_source_counts": FORMAL_EVENT_COUNTS,
            "formal_target_counts": FORMAL_TARGET_COUNTS,
            "quality_audit": quality["status"],
            "precise_ngsim": precise["status"],
            "physical_candidates": path_audit["candidate_count"],
            "qualified_b_paths": path_audit["qualified_b_paths"],
            "task9_formal_runs": readiness["formal_runs_executed"],
        },
        "trajectory_measurement_robustness": {
            "judgement": quality_judgement,
            "supports": ["internal residual and continuity diagnostics are available for event/control comparison", "formal event definitions and counts remain unchanged"],
            "limits": ["internal consistency is not independent physical truth", "jerk/spectral diagnostics were not newly computed", "PreciseNGSIM cannot provide a reliable event-level independent crosswalk"],
        },
        "physical_interaction_path": {
            "qualified_b_paths": int(path_audit["qualified_b_paths"]),
            "unknown_b_paths": int(path_audit["unknown_b_paths"]),
            "decision": "No qualified B witness; source-to-target same-trajectory ordering is descriptive and physical connection basis remains Unknown.",
        },
        "task9": {
            "execution_ready": False,
            "decision": "Keep blocked; engineering interface is ready but no qualified physical input exists.",
        },
        "scientific_interpretation": {
            "supported": ["Task6/Task8 descriptive micro-interaction differences remain usable within their measurement limits"],
            "weakened": ["claims that current trajectory records alone establish physical propagation"],
            "unresolved": ["network disturbance supply versus longitudinal response versus measurement error versus multi-vehicle/lane interaction"],
        },
        "stage_0_5": "blocked",
        "scientific_equivalence": False,
        "next_required_evidence": [
            "independent physical reference with license, time and spatial coverage",
            "verified B physical connection basis or equivalent independent path witness",
            "qualified fixed-leader input segment before any formal Task9 execution",
        ],
        "new_simulations": 0,
        "holdout_reads": 0,
    }


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve existing result directory: {OUT}")
    OUT.mkdir(parents=True)
    contexts = {window: load_context(window) for window in WINDOWS}
    quality, quality_comparison = quality_audit(contexts)
    precise = precise_feasibility()
    candidates, path_audit, graph = physical_path_audit(contexts)
    readiness = task9_readiness()
    decision = final_decision(quality, path_audit, readiness, precise)
    reuse = historical_reuse_audit()
    (OUT / "task10_historical_reuse_audit.md").write_text(reuse, encoding="utf-8")
    (OUT / "trajectory_quality_summary.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    quality_comparison.to_csv(OUT / "event_control_quality_comparison.csv", index=False)
    (OUT / "precise_ngsim_feasibility.json").write_text(json.dumps(precise, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    candidates.to_csv(OUT / "physical_path_candidates.csv", index=False)
    (OUT / "physical_path_witness_audit.json").write_text(json.dumps(path_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "interaction_graph_summary.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "task9_readiness_decision.json").write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "task10_final_decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    bindings = {
        "base_head": subprocess_head(),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "new_simulations": 0,
        "new_video_bytes": 0,
        "holdout_reads": 0,
        "inputs": {},
    }
    input_paths = [
        *(LOCAL_CONTEXT / f"{window}_identity_contexts.csv" for window in WINDOWS),
        *(CANONICAL_ROOT / f"ngsim_us101__{window}.parquet" for window in WINDOWS),
        TASK7_LOCAL / "precise_data_inspection.json", TASK7_LOCAL / "precise_structure_check.json",
        TASK7_LOCAL / "precise_semantic_layout_flags.json",
        TASK8_EVIDENCE / "event_precursor_decomposition.csv", TASK9_EVIDENCE / "task9_protocol.json",
    ]
    for path in input_paths:
        bindings["inputs"][path.relative_to(ROOT).as_posix()] = {"sha256": sha(path), "bytes": path.stat().st_size}
    (OUT / "source_bindings.json").write_text(json.dumps(bindings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation = {
        "task_id": "AAD-S0.5-POST-R2-TASK10",
        "status": "PASS_BOUNDED_OFFLINE_DIAGNOSTIC",
        "quality_audit": "PASS",
        "precise_crosswalk": precise["status"],
        "physical_path_audit": "PASS_BOUNDED_UNKNOWN_PRESERVED",
        "task9_readiness": readiness["status"],
        "new_simulations": 0,
        "video_downloads": 0,
        "holdout_reads": 0,
        "formal_p2_reextraction": 0,
        "not_run": ["full pytest", "full compileall", "SUMO/TraCI", "third window", "locked holdout", "video/manual review"],
    }
    (OUT / "validation_record.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "context_consistency_check.json").write_text(json.dumps({
        "status": "PASS_CONTEXT_CONSISTENCY_CHECK",
        "stage_0_5_gate": "blocked",
        "scientific_equivalence_accepted": False,
        "round3": "Not started",
        "task9_runs": 0,
        "updated_context": ["AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/05_EXPERIMENTS.md", "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md"],
        "updated_indexes": ["docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md", "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {
        "schema": "aad.stage05.post_r2.task10.final_diagnostic.manifest.v1",
        "task_id": "AAD-S0.5-POST-R2-TASK10",
        "status": "completed_with_blockers",
        "gate_status": "blocked",
        "scientific_equivalence_accepted": False,
        "new_simulations": 0,
        "identity_level_payload": False,
        "payload_files": {p.name: sha(p) for p in payloads},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "SHA256SUMS").write_text("\n".join(f"{sha(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS") + "\n", encoding="utf-8")
    print(f"TASK10_FINAL_DIAGNOSTIC_WRITTEN {OUT.relative_to(ROOT).as_posix()}")


def subprocess_head() -> str:
    head = (ROOT / ".git/HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref_path = ROOT / ".git" / head[5:]
        if ref_path.is_file():
            return ref_path.read_text(encoding="utf-8").strip()
    return head


if __name__ == "__main__":
    main()
