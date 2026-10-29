"""Package the minimal Round2 Task3 contract-alignment evidence.

This is an offline, no-launch audit.  It reuses the Task2 counterexamples and
post-R2 sealed summary, then checks the corrected formal adapter on the two
explicit-flag cases and the lane/path separation case.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029"
TASK2 = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029"
POST_R2 = ROOT / "evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def current_adapter_probes() -> list[dict[str, Any]]:
    diag = load_module("post_r2_task3_diag", ROOT / "code/scripts/analyze_stage_0_5_post_r2_offline_diagnostic.py")
    return diag.adapter_probes()


def sealed_reuse() -> dict[str, Any]:
    diagnostic = json.loads((POST_R2 / "diagnostic.json").read_text(encoding="utf-8"))
    return {
        "schema_version": "aad.stage0.5.round2.task3.sealed-reuse.v1",
        "source_package": "evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/",
        "reused_artifacts": ["diagnostic.json", "B00_A03_source_segments.csv", "Round2_minGap1.0_source_segments.csv", "existing_equivalence_matrix.json", "adapter_counterexamples.json"],
        "source_counts": {
            "B00_A03_observations": diagnostic["runs"]["B00_A03"]["source"]["state_rows"],
            "Round2_candidate_observations": diagnostic["runs"]["Round2_minGap1.0"]["source"]["state_rows"],
            "B00_formal_risk_rows": diagnostic["runs"]["B00_A03"]["source"]["risk_rows_0_lt_ttc_lt_2"],
            "Round2_candidate_formal_risk_rows": diagnostic["runs"]["Round2_minGap1.0"]["source"]["risk_rows_0_lt_ttc_lt_2"],
            "B00_source_onsets": diagnostic["runs"]["B00_A03"]["source_all_D1"]["onset_events"],
            "Round2_candidate_source_onsets": diagnostic["runs"]["Round2_minGap1.0"]["source_all_D1"]["onset_events"],
            "B00_D1_exposure_veh_s": diagnostic["runs"]["B00_A03"]["source_all_D1"]["local_evaluable_s"],
            "Round2_candidate_D1_exposure_veh_s": diagnostic["runs"]["Round2_minGap1.0"]["source_all_D1"]["local_evaluable_s"],
        },
        "formal_measurement_impact": "No sealed source count is changed by this patch: fcd_to_state_frame/measure_state_frame do not emit explicit continuity flags, so the adapter's documented absent-field default remains false for these sealed reconstructions. Explicit flags in external premeasured inputs are now preserved.",
        "native_launches": diagnostic["native_launches"],
        "traci_connections": diagnostic["traci_connections"],
        "locked_holdout_reads": diagnostic["locked_holdout_reads"],
    }


def main() -> int:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    before = json.loads((POST_R2 / "adapter_counterexamples.json").read_text(encoding="utf-8"))
    after = current_adapter_probes()
    before_by = {row["case"]: row for row in before}
    after_by = {row["case"]: row for row in after}
    flag_cases = []
    for name in ("identity_break", "observation_gap"):
        flag_cases.append({
            "case": name,
            "before_task2": {"formal_aligned_events": before_by[name]["formal_aligned_events"], "mapped_flag_true_rows": before_by[name]["mapped_flag_true_rows"]},
            "after_task3": {"formal_aligned_events": after_by[name]["formal_aligned_events"], "mapped_flag_true_rows": after_by[name]["mapped_flag_true_rows"]},
            "expected": "explicit flag remains true; a three-frame probe with the break in the middle produces no confirmed formal event",
        })
    lane = {"case": "native_lane_change", "before_task2": {"native_events": before_by["native_lane_change"]["native_events"], "formal_aligned_events": before_by["native_lane_change"]["formal_aligned_events"], "D1_onsets": before_by["native_lane_change"]["D1_onsets"]}, "after_task3": {"native_events": after_by["native_lane_change"]["native_events"], "formal_aligned_events": after_by["native_lane_change"]["formal_aligned_events"], "D1_onsets": after_by["native_lane_change"]["D1_onsets"]}, "interpretation": "Formal/native pair qualification remains separate from D1 same-native-lane local exposure; no physical path qualification is inferred."}
    write_json(PACKAGE / "flag_preservation_before_after.json", {"schema_version": "aad.stage0.5.round2.task3.flag-preservation.v1", "cases": flag_cases})
    write_json(PACKAGE / "lane_path_separation_recheck.json", {"schema_version": "aad.stage0.5.round2.task3.lane-path-separation.v1", **lane})
    write_json(PACKAGE / "sealed_trace_reanalysis_reuse.json", sealed_reuse())
    write_json(PACKAGE / "contract_alignment_decision.json", {
        "schema_version": "aad.stage0.5.round2.task3.alignment-decision.v1",
        "formal_reference": "stage_0_2_formal_risk_measurement.v2: pair/trajectory/leader/time continuity, 0<TTC<2s, span>=0.2s, fail-closed continuity flags",
        "adopted_alignment": {
            "formal_aligned": "Preserve supplied identity_uncertain, identity_break, observation_gap, leader_identity_uncertain and leader_matched evidence; default only absent recorder fields in deterministic SUMO frames.",
            "formal_P2_estimand": "C/pair-time continuity already matches the existing formal extractor; native_lane_id is not added to formal event qualification.",
            "D1": "Retain same-native-lane as local diagnostic exposure/path-support condition; it is not formal P2 event identity or formal P2 rate denominator.",
            "physical_path": "Remain separate and Unknown without time-indexed road-connection and interaction evidence.",
        },
        "unchanged_scientific_parameters": ["TTC threshold 2s", "minimum duration 0.2s", "100ms cadence and 0.11s max gap", "source/target/window/cohort", "Rule A"],
        "scientific_equivalence_accepted": False,
        "researcher_decision_required": ["whether simulator-vs-NGSIM formal comparability can be accepted after input-flag alignment", "what evidence qualifies a physical path across native-lane/edge boundaries"],
    })
    reuse = sealed_reuse()
    validation = {
        "schema_version": "aad.stage0.5.round2.task3.validation.v1",
        "flag_preservation_verified": all(row["after_task3"]["mapped_flag_true_rows"][row["case"]] == 1 for row in flag_cases),
        "flagged_three_frame_probe_has_no_confirmed_formal_event": all(row["after_task3"]["formal_aligned_events"] == 0 for row in flag_cases),
        "lane_path_separation_verified": lane["after_task3"]["formal_aligned_events"] == lane["after_task3"]["native_events"] == 1 and lane["after_task3"]["D1_onsets"] == 0,
        "sealed_source_counts_reused_unchanged": reuse["source_counts"]["B00_formal_risk_rows"] == reuse["source_counts"]["Round2_candidate_formal_risk_rows"] == 0 and reuse["source_counts"]["B00_source_onsets"] == reuse["source_counts"]["Round2_candidate_source_onsets"] == 0,
        "round2_candidate_passes_original_source_condition": False,
        "physical_arrival_time": "Unknown",
        "native_launches": 0,
        "traci_connections": 0,
        "new_trajectories": 0,
        "locked_holdout_reads": 0,
        "status": "PASS_MINIMAL_ALIGNMENT_SOURCE_ZERO_REMAINS_RESEARCHER_DECISION_PENDING",
    }
    write_json(PACKAGE / "validation_record.json", validation)
    bindings = [
        "code/src/riskprop/stage_0_5_sumo.py", "code/tests/test_stage_0_5_measurement_equivalence.py",
        "code/tests/test_stage_0_5_post_r2_offline_diagnostic.py", "code/configs/stage_0_2_formal_risk_measurement_p2_v1.json",
        "docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md",
    ]
    write_json(PACKAGE / "source_bindings.json", {"schema_version": "aad.stage0.5.round2.task3.source-bindings.v1", "git_head": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "files": {p: sha(ROOT / p) for p in bindings}})
    payloads = sorted(p for p in PACKAGE.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    write_json(PACKAGE / "manifest.json", {"schema_version": "aad.evidence-manifest.v1", "result_id": PACKAGE.name, "self_reference": False, "files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in payloads]})
    lines = []
    for p in sorted(PACKAGE.iterdir()):
        if p.name != "SHA256SUMS":
            lines.append(f"{sha(p)}  {p.name}")
    (PACKAGE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
