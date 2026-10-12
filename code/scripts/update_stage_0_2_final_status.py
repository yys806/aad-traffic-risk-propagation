"""Synchronize the approved Stage 0.2 scientific acceptance status."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/PROJECT_REGISTRY.json"
PACKAGE = ROOT / "code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4"
PORTABLE = "evidence/results/RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4"

def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    registry["last_verified"] = "2026-10-12"
    experiment = next(item for item in registry["experiments"] if item["id"] == "stage_0_2")
    experiment["status"] = "completed_closed"
    experiment["configuration"] = "Researcher-approved limited scope; P2 rate denominator includes reliable following exposure with both endpoints P2-evaluable (valid or not_applicable)."
    experiment["current_conclusion"] = "Stage 0.2 passed and closed for descriptive longitudinal following-risk proxy calibration in four approved NGSIM sources at 100 ms only."
    experiment["gate"] = {"status": "pass", "portable_path": PORTABLE + "/scientific_gate_report.json", "scope": "limited_four_source_ngsim_descriptive_calibration_100ms"}
    experiment["scientific_claim_eligible"] = True
    for entry in ["code/scripts/finalize_stage_0_2_scientific_acceptance.py", "code/scripts/audit_stage_0_2_exposure_edges.py", "code/scripts/update_stage_0_2_final_status.py"]:
        if entry not in experiment["entrypoints"]:
            experiment["entrypoints"].append(entry)
    experiment["result_ids"] = [x for x in experiment["result_ids"] if x != "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R2"]
    if "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4" not in experiment["result_ids"]:
        experiment["result_ids"].append("RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4")
    result = {
        "id": "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4",
        "experiment_id": "stage_0_2",
        "name": "Stage 0.2 final limited scientific acceptance",
        "status": "verified_limited_scope_closed",
        "portable_evidence_paths": [PORTABLE + "/" + name for name in ["audit.json", "scientific_gate_report.json", "p2_event_rates.json", "scientific_gate_matrix.json", "scope_and_claims.md", "exposure_edge_audit.json", "report.md", "provenance.json", "manifest.json", "SHA256SUMS"]],
        "local_artifact_paths": ["code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4"],
        "code_version_source": "provenance.json",
        "configuration_source": "scientific_gate_report.json",
        "data_version_source": "provenance.json and SHA256SUMS",
        "core_metrics": {"p2_events": 4545, "reliable_following_exposure_s": 512043.2, "p2_evaluable_following_exposure_s": 503922.2, "not_evaluable_following_exposure_s": 8121.0, "reliable_closing_exposure_s": 208026.3, "p2_rate_denominator": "reliable P2-evaluable following exposure; both endpoints valid or not_applicable", "scope": "four approved NGSIM sources, 100 ms"},
        "current_conclusion": "Passed and closed for limited descriptive calibration; physical truth and specified external-validity limitations remain unverified.",
        "gate_status": "pass",
        "paper_locations": ["docs/STAGE_INDEX.md"],
        "scientific_claim_eligible": True,
    }
    registry["results"] = [item for item in registry["results"] if item["id"] not in {result["id"], "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R2", "RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE"}]
    registry["results"].append(result)
    registry["current"]["active_task"] = "Stage 0.2 completed/closed; retain as measurement and descriptive calibration baseline."
    registry["current"]["next_decision_owner"] = None
    registry["current"]["portable_gate_paths"] = [PORTABLE + "/scientific_gate_report.json", "evidence/results/RES-PROTOCOL-READINESS-V1/protocol_lock_readiness_v1.json"]
    registry["current"]["local_gate_paths"] = [str(PACKAGE.relative_to(ROOT)).replace("\\", "/") + "/scientific_gate_report.json", "code/outputs/formal/calibration/protocol_lock_readiness_v1.json"]
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
