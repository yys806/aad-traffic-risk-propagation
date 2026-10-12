"""Synchronize the approved Stage 0.2 scientific acceptance status."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/PROJECT_REGISTRY.json"
PACKAGE = ROOT / "code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3"
PORTABLE = "evidence/results/RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3"

def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    registry["last_verified"] = "2026-10-12"
    experiment = next(item for item in registry["experiments"] if item["id"] == "stage_0_2")
    experiment["status"] = "active_audit_closure"
    experiment["configuration"] = "Approved limited scope; denominator audit found invalid/non_positive_gap endpoint edges; researcher decision required before formal closure."
    experiment["current_conclusion"] = "P2=4545 and sealed exposure reproduce, but formal Gate is blocked pending denominator semantic decision."
    experiment["gate"] = {"status": "blocked", "portable_path": PORTABLE + "/scientific_gate_report.json", "scope": "limited_four_source_ngsim_descriptive_calibration"}
    experiment["scientific_claim_eligible"] = False
    for entry in ["code/scripts/finalize_stage_0_2_scientific_acceptance.py", "code/scripts/audit_stage_0_2_exposure_edges.py", "code/scripts/update_stage_0_2_final_status.py"]:
        if entry not in experiment["entrypoints"]:
            experiment["entrypoints"].append(entry)
    experiment["result_ids"] = [x for x in experiment["result_ids"] if x != "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R2"]
    if "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3" not in experiment["result_ids"]:
        experiment["result_ids"].append("RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3")
    result = {
        "id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R3",
        "experiment_id": "stage_0_2",
        "name": "Stage 0.2 final limited scientific acceptance",
        "status": "blocked_denominator_semantics",
        "portable_evidence_paths": [PORTABLE + "/" + name for name in ["audit.json", "scientific_gate_report.json", "p2_event_rates.json", "scientific_gate_matrix.json", "scope_and_claims.md", "exposure_edge_audit.json", "report.md", "provenance.json", "manifest.json", "SHA256SUMS"]],
        "local_artifact_paths": ["code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3"],
        "code_version_source": "provenance.json",
        "configuration_source": "scientific_gate_report.json",
        "data_version_source": "provenance.json and SHA256SUMS",
        "core_metrics": {"p2_events": 4545, "reliable_following_exposure_s": 512043.2, "reliable_closing_exposure_s": 208026.3, "p2_rate_denominator": "reliable_following_exposure_time", "scope": "four approved NGSIM sources, 100 ms"},
        "current_conclusion": "Blocked pending researcher decision on invalid/non_positive_gap endpoint edges in the approved P2 rate denominator.",
        "gate_status": "blocked",
        "paper_locations": ["docs/STAGE_INDEX.md"],
        "scientific_claim_eligible": False,
    }
    registry["results"] = [item for item in registry["results"] if item["id"] not in {result["id"], "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R2", "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE"}]
    registry["results"].append(result)
    registry["current"]["active_task"] = "Stage 0.2 final acceptance blocked pending denominator semantic decision."
    registry["current"]["next_decision_owner"] = "human_researcher"
    registry["current"]["portable_gate_paths"] = [PORTABLE + "/scientific_gate_report.json", "evidence/results/RES-PROTOCOL-READINESS-V1/protocol_lock_readiness_v1.json"]
    registry["current"]["local_gate_paths"] = [str(PACKAGE.relative_to(ROOT)).replace("\\", "/") + "/scientific_gate_report.json", "code/outputs/formal/calibration/protocol_lock_readiness_v1.json"]
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
