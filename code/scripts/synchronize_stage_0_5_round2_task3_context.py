"""Synchronize project indexes for Round2 Task3."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = "AAD-S0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029"
REPORT = "docs/STAGE_0_5_ROUND2_TASK3_MEASUREMENT_CONTRACT_ALIGNMENT_20261029.md"
EVIDENCE = "evidence/results/RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029/"
SUMMARY = ("Verified minimal formal-alignment repair preserves explicit identity/continuity flags; "
           "formal pair/time qualification remains separate from D1 same-native-lane diagnostics. "
           "B00 and Round2 candidate sealed source P2 remain zero; no SUMO/TraCI/new trajectories/holdout. "
           "Stage 0.5 Gate, Stage 0.6, Protocol Lock, Stage I and Round3 unchanged.")


def prepend(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if block.strip() not in text:
        path.write_text(block.rstrip() + "\n\n" + text, encoding="utf-8")


def main() -> None:
    prepend(ROOT / "AI_CONTEXT/00_PROJECT_STATE.md", f"## Current — {TASK}\n\n{SUMMARY}\nReport: {REPORT}; evidence: {EVIDENCE}\n")
    prepend(ROOT / "AI_CONTEXT/05_EXPERIMENTS.md", f"## {TASK}\n\n{SUMMARY} The required source condition is still not met; candidate confirmation remains closed.\n")
    prepend(ROOT / "AI_CONTEXT/06_DECISIONS.md", f"## {TASK}\n\nAgreed engineering alignment: preserve explicit continuity flags in formal-aligned mapping. Existing formal P2 pair/time semantics and D1 lane diagnostic separation remain unchanged. Scientific simulator comparability and physical-path evidence remain AWAITING_RESEARCHER_DECISION.\n")
    prepend(ROOT / "AI_CONTEXT/07_KNOWN_ISSUES.md", f"## {TASK}\n\nResolved implementation issue: build_sumo_formal_source_frame no longer erases supplied identity_break/observation_gap/identity quality flags. Remaining issues: simulator-vs-NGSIM scientific equivalence and time-indexed physical-path witness. Status: Awaiting Researcher Decision.\n")
    prepend(ROOT / "AI_CONTEXT/08_CHANGELOG.md", f"## {TASK}\n\nPreserved explicit formal-aligned continuity evidence, updated targeted regression expectations, and packaged sealed source-zero recheck. No scientific thresholds, cohort, window, Rule A or Gate state changed.\n")
    prepend(ROOT / "docs/RESEARCH_STATUS.md", f"## {TASK}\n\n{SUMMARY}\n")
    prepend(ROOT / "docs/PROJECT_INDEX.md", f"## {TASK}\n\nReport: `{REPORT}`; alignment script: `code/scripts/align_stage_0_5_round2_task3_measurement_contract.py`; evidence: `{EVIDENCE}`.\n\n{SUMMARY}\n")
    prepend(ROOT / "docs/RESULTS_INDEX.md", f"## RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029\n\n{SUMMARY} See `{REPORT}` and the portable evidence package.\n")
    registry_path = ROOT / "docs/PROJECT_REGISTRY.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for entry in [REPORT, "code/scripts/align_stage_0_5_round2_task3_measurement_contract.py", "code/scripts/synchronize_stage_0_5_round2_task3_context.py"]:
        if entry not in registry["canonical_entries"]:
            registry["canonical_entries"].append(entry)
    result_id = "RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029"
    result = {
        "id": result_id,
        "experiment_id": "stage_0_5",
        "name": "Round2 Task3 minimal measurement-contract alignment and sealed source-P2 recheck",
        "status": "verified_minimal_alignment_source_zero_researcher_decision_pending",
        "portable_evidence_paths": [f"{EVIDENCE}manifest.json", f"{EVIDENCE}SHA256SUMS", f"{EVIDENCE}validation_record.json"],
        "local_artifact_paths": [EVIDENCE],
        "code_version_source": "source_bindings.json in Task3 evidence package",
        "configuration_source": "unchanged formal P2 config and existing Rule A/source/target/window/cohort",
        "data_version_source": "reused B00 A03 and Round2 candidate sealed post-R2 diagnostic; no new trajectories",
        "core_metrics": {"flag_preservation_fixed": True, "formal_source_P2_B00": 0, "formal_source_P2_candidate": 0, "source_onsets_B00": 0, "source_onsets_candidate": 0, "new_native_launches": 0, "new_trajectories": 0, "holdout_reads": 0, "round2_candidate_passes_original_source_condition": False, "physical_arrival_time": "Unknown", "scientific_equivalence_accepted": False},
        "current_conclusion": "Explicit continuity flags are now preserved. The formal pair/time estimator remains separate from D1 lane/path diagnostics. Sealed B00 and candidate source P2 remain zero; the candidate does not pass the original source-event condition.",
        "gate_status": "blocked",
        "paper_locations": [REPORT],
        "scientific_claim_eligible": False,
    }
    registry["current"]["active_task"] = f"{TASK}: minimal flag-preservation repair complete; sealed source P2 remains zero; researcher decision pending"
    registry["current"]["why_now"] = "Task2 identified an implementation-level formal-aligned flag-loss bug; Task3 repaired it without changing formal scientific parameters and rechecked sealed source qualification."
    registry["results"] = [x for x in registry["results"] if x.get("id") != result_id] + [result]
    for experiment in registry["experiments"]:
        if experiment.get("id") == "stage_0_5" and result_id not in experiment.get("result_ids", []):
            experiment.setdefault("result_ids", []).append(result_id)
    registry["last_verified"] = "2026-10-30"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
