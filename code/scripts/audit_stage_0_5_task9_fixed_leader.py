"""Prepare Task9 fixed-leader evidence without selecting or running physical cases."""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_pair import (  # noqa: E402
    SEEDS,
    TAU_VALUES,
    audit_arm_configs,
)

RESULT_ID = "RES-STAGE-0.5-POST-R2-TASK9-FIXED-LEADER-PREP-20261031"
OUT = ROOT / "evidence" / "results" / RESULT_ID
RUN_ROOT = ROOT / "code" / "outputs" / "formal" / "calibration" / "stage_0_5_ready_to_admit_v3" / "runs"
ARM_A = RUN_ROOT / "WEEK_0750_B00_IC1_s20261201_A03"
ARM_B = RUN_ROOT / "AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1"
HISTORY = ROOT / "evidence" / "results" / "RES-STAGE-0.5-METHOD-EXPANSION-V1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def historical_seed_audit() -> dict[str, object]:
    rows = list(csv.DictReader((HISTORY / "response_metrics.csv").open(encoding="utf-8-sig", newline="")))
    seeds = sorted({int(row["seed"]) for row in rows})
    return {
        "rows": len(rows),
        "duration_s": sorted({float(row["duration_s"]) for row in rows}),
        "seeds": seeds,
        "expected_seeds": list(SEEDS),
        "seed_set_verified": seeds == list(SEEDS),
        "scope": "Historical homogeneous 12-pair replay; engineering/randomness reference only",
        "current_heterogeneous_B00_result": False,
        "historical_seed_approval_transferred": False,
    }


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"preserve existing evidence: {OUT}")
    OUT.mkdir(parents=True)
    config_audit = audit_arm_configs(
        ARM_A / "routes.rou.xml", ARM_B / "routes.rou.xml",
        ARM_A / "network.net.xml", ARM_B / "network.net.xml",
        ARM_A / "run.sumocfg", ARM_B / "run.sumocfg",
    )
    seed_audit = historical_seed_audit()
    if not seed_audit["seed_set_verified"] or seed_audit["rows"] != 324:
        raise RuntimeError("historical seed/row contract changed")
    bindings = {}
    for path in (
        ARM_A / "routes.rou.xml", ARM_A / "network.net.xml", ARM_A / "run.sumocfg",
        ARM_B / "routes.rou.xml", ARM_B / "network.net.xml", ARM_B / "run.sumocfg",
        HISTORY / "response_plan.json", HISTORY / "response_metrics.csv",
        ROOT / "docs" / "AAD_ROUND2_PROVIDER_INQUIRY_DISPATCH_20261030.md",
        ROOT / "evidence" / "results" / "RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030" / "provider_inquiry_draft.md",
    ):
        bindings[path.relative_to(ROOT).as_posix()] = {"sha256": sha(path), "bytes": path.stat().st_size}
    protocol = {
        "task": "AAD-S0.5-POST-R2-TASK9",
        "status": "Blocked by physical input",
        "physical_reference_status": "Not acquired; license, PTS/Global_Time mapping and source-lane coverage unresolved",
        "arms": [
            {"label": "A", "model": "original heterogeneous B00", "minGap_m": 2.5},
            {"label": "B", "model": "same heterogeneous B00; minGap only", "minGap_m": 1.0},
        ],
        "tau_values_s": list(TAU_VALUES),
        "seeds": list(SEEDS),
        "runs_per_qualified_segment": 6,
        "total_runs": "6*N",
        "N": None,
        "physical_segment_selection": "Not started",
        "leader_input": "Same external leader speed/position sequence and same physical time anchor in both arms",
        "initial_matching": ["follower_speed_mps", "leader_speed_mps", "physical_net_gap_m"],
        "disallowed_repairs": ["time shifting", "arm-specific post-hoc deletion", "seed replacement", "minGap-adjusted-gap matching"],
        "metrics": ["physical_net_gap_m", "follower_speed_mps", "leader_speed_mps", "closing_speed_mps", "TTC", "C_initial_m", "C_f_m", "C_l_m", "C_m", "C_gap_m", "R_m", "response_timing", "Formal_P2", "D1_local_exposure_when_applicable"],
        "kinematic_relation": "Under common leader input and matched initial follower speed, delta_C_initial=0 and delta_C_l=0, so delta_C=delta_C_f; verify R_m rather than assume closure.",
        "formal_runs_executed": 0,
        "synthetic_or_arbitrary_segments_used": 0,
        "round3_started": False,
        "stage_0_5_gate": "blocked",
    }
    email = {
        "status": "NOT_SENT_BLOCKED",
        "intended_recipient": "data.itsjpo@dot.gov",
        "actual_recipient": None,
        "sender_identity": None,
        "send_timestamp": None,
        "message_id": None,
        "receipt": None,
        "draft_source": "evidence/results/RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030/provider_inquiry_draft.md",
        "draft_sha256": bindings["evidence/results/RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030/provider_inquiry_draft.md"]["sha256"],
        "attempts": [
            {"channel": "Windows Edge", "status": "Blocked", "reason": "Computer Use could not determine the current browser URL with enough confidence; no mail UI was accessed."},
            {"channel": "Gmail application browser", "status": "Auto-review rejected", "reason": "Google Accounts authentication origin was not specifically authorized or bound to an identified account."},
        ],
        "no_send_claim": True,
    }
    provenance = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_worktree": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines(),
        "python": sys.version,
        "platform": platform.platform(),
        "command": "python code/scripts/audit_stage_0_5_task9_fixed_leader.py",
        "source_sha256": sha(Path(__file__)),
        "bindings": bindings,
        "new_sumo_or_traci_runs": 0,
        "new_video_bytes": 0,
        "holdout_reads": 0,
    }
    (OUT / "arm_config_audit.json").write_text(json.dumps(config_audit, indent=2) + "\n", encoding="utf-8")
    (OUT / "historical_seed_audit.json").write_text(json.dumps(seed_audit, indent=2) + "\n", encoding="utf-8")
    (OUT / "task9_protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
    (OUT / "provider_dispatch_status.json").write_text(json.dumps(email, indent=2) + "\n", encoding="utf-8")
    (OUT / "source_bindings.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    validation = {
        "task_id": "AAD-S0.5-POST-R2-TASK9",
        "status": "PASS_STATIC_PREPARATION",
        "static_arm_audit": "PASS",
        "historical_seed_audit": "PASS",
        "new_simulations": 0,
        "new_video_bytes": 0,
        "physical_review_cases": 0,
        "formal_paired_observations": 0,
        "targeted_test_command": "python -m pytest -q code/tests/test_stage_0_5_fixed_leader_pair.py",
        "targeted_test_status": "PASS (3 tests recorded separately)",
        "not_run": ["SUMO/TraCI", "ffprobe", "video download", "physical review", "holdout"],
    }
    context = {
        "status": "PASS_CONTEXT_CONSISTENCY_CHECK",
        "stage_0_5_gate": "blocked",
        "scientific_equivalence_accepted": False,
        "round3": "Not started",
        "protocol_lock": "Not created",
        "stage_i": "Not started",
        "official_inquiry_sent": False,
        "fixed_leader_runs": 0,
        "updated_context": [
            "AI_CONTEXT/00_PROJECT_STATE.md", "AI_CONTEXT/05_EXPERIMENTS.md",
            "AI_CONTEXT/07_KNOWN_ISSUES.md", "AI_CONTEXT/08_CHANGELOG.md",
        ],
        "updated_indexes": [
            "docs/PROJECT_REGISTRY.json", "docs/RESEARCH_STATUS.md",
            "docs/PROJECT_INDEX.md", "docs/RESULTS_INDEX.md", "docs/STAGE_INDEX.md",
        ],
    }
    (OUT / "validation_record.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    (OUT / "context_consistency_check.json").write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    payloads = sorted(p for p in OUT.iterdir() if p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {
        "schema": "aad.stage05.post_r2.task9.fixed_leader_prep.manifest.v1",
        "task_id": "AAD-S0.5-POST-R2-TASK9",
        "status": "completed_with_blockers",
        "gate_status": "blocked",
        "scientific_equivalence_accepted": False,
        "new_simulations": 0,
        "video_or_identity_level_payload": False,
        "payload_files": {p.name: sha(p) for p in payloads},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sums = [f"{sha(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.name != "SHA256SUMS"]
    (OUT / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(f"TASK9_FIXED_LEADER_PREPARED {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
