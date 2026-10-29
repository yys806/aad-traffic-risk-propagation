"""Synchronize the small set of project indexes required by Round2 Task2."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = "AAD-S0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029"
SUMMARY = ("Verified offline measurement-contract audit: 16 deterministic synthetic cases reproduce "
           "formal P2, SUMO-native, formal-aligned and D1 differences; candidate A/B/C remain pending "
           "researcher adjudication. Reused post-R2 sealed evidence; no SUMO/TraCI/new trajectories/holdout. "
           "Stage 0.5 Gate, Stage 0.6, Protocol Lock, Stage I and Round3 unchanged.")


def prepend(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        return
    path.write_text(block.rstrip() + "\n\n" + text, encoding="utf-8")


def main() -> None:
    prepend(ROOT / "AI_CONTEXT/00_PROJECT_STATE.md", f"## Current — {TASK}\n\n{SUMMARY}\nReport: docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md; evidence: evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/.\n")
    prepend(ROOT / "AI_CONTEXT/05_EXPERIMENTS.md", f"## {TASK}\n\n{SUMMARY} Synthetic native/formal-aligned/D1 outputs and A/B/C candidate comparison are in the evidence package.\n")
    prepend(ROOT / "AI_CONTEXT/06_DECISIONS.md", f"## {TASK}\n\nAgreed scope: offline contract audit only. Proposed choices A/B/C are evidence for researcher decision, not a scientific freeze; production rules, thresholds, Rule A and Gate states are unchanged.\n")
    prepend(ROOT / "AI_CONTEXT/07_KNOWN_ISSUES.md", f"## {TASK}\n\nDocumented Intent: measurement interfaces should preserve TTC quality, identity, flags, time and path semantics. Actual Implementation: lane, explicit-flag and inconsistent-TTC counterexamples remain. Evidence: RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029. Conflict: candidate A/B/C and flag provenance require researcher adjudication. Status: Awaiting Researcher Decision.\n")
    prepend(ROOT / "AI_CONTEXT/08_CHANGELOG.md", f"## {TASK}\n\nAdded the offline contract-audit evidence package, 16-case synthetic inputs/results, candidate A/B/C comparison, sealed-evidence reuse index and Zotero dedup/acquisition ledger. No formal implementation or Gate state changed.\n")
    prepend(ROOT / "docs/RESEARCH_STATUS.md", f"## {TASK}\n\n{SUMMARY} This task is complete as an audit package and remains scientifically pending.\n")
    prepend(ROOT / "docs/PROJECT_INDEX.md", f"## {TASK}\n\nReport: `docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md`; generator: `code/scripts/audit_stage_0_5_round2_task2_measurement_contract.py`; context synchronizer: `code/scripts/synchronize_stage_0_5_round2_task2_context.py`; evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/`.\n\n{SUMMARY}\n")
    prepend(ROOT / "docs/RESULTS_INDEX.md", f"## RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029\n\n{SUMMARY} See `docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md` and the portable evidence package.\n")

    registry_path = ROOT / "docs/PROJECT_REGISTRY.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = [
        "docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md",
        "code/scripts/audit_stage_0_5_round2_task2_measurement_contract.py",
        "code/scripts/register_stage_0_5_round2_task2_literature.py",
        "code/scripts/synchronize_stage_0_5_round2_task2_context.py",
    ]
    for entry in entries:
        if entry not in registry["canonical_entries"]:
            registry["canonical_entries"].append(entry)
    registry["last_verified"] = "2026-10-29"
    registry["current"]["active_task"] = f"{TASK}: offline audit complete; scientific equivalence and A/B/C choice pending researcher decision"
    registry["current"]["why_now"] = "Round2 Task2 reused sealed post-R2 evidence to audit formal P2, SUMO-native, formal-aligned and D1 measurement contracts without new simulation."
    result = {
        "id": "RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029",
        "experiment_id": "stage_0_5",
        "name": "Round2 Task2 offline measurement-contract audit and scientific-equivalence evidence",
        "status": "verified_offline_scientific_decision_pending",
        "portable_evidence_paths": [
            "evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/manifest.json",
            "evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/SHA256SUMS",
            "evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/validation_record.json",
        ],
        "local_artifact_paths": ["evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029"],
        "code_version_source": "source_bindings.json in the task evidence package",
        "configuration_source": "unchanged stage_0_2_formal_risk_measurement_p2_v1.json and current Stage 0.5 adapters",
        "data_version_source": "sealed post-R2 B00/candidate evidence; no new trajectories",
        "core_metrics": {
            "synthetic_cases": 16,
            "candidate_rules": ["A_strict_native_lane", "B_connected_boundary", "C_pair_time_continuity"],
            "new_native_launches": 0,
            "new_trajectories": 0,
            "holdout_reads": 0,
            "formal_equivalence_accepted": False,
            "zotero_new_items": 8,
            "zotero_existing_reused": 1,
            "full_text_attachments_created": 0,
        },
        "current_conclusion": "Synthetic cases reproduce interface differences and candidate-rule impacts. Sealed source evidence still has zero observed formal P2 states; no interface difference is established as its cause. A/B/C and flag/time provenance remain for researcher decision.",
        "gate_status": "blocked",
        "paper_locations": ["docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md"],
        "scientific_claim_eligible": False,
    }
    registry["results"] = [r for r in registry["results"] if r.get("id") != result["id"]]
    registry["results"].append(result)
    for experiment in registry["experiments"]:
        if experiment.get("id") == "stage_0_5" and result["id"] not in experiment.get("result_ids", []):
            experiment.setdefault("result_ids", []).append(result["id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
