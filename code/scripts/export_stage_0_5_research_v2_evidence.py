"""Export only V2 engineering evidence; preserve historical manifest entries."""
import argparse
import hashlib
import json
from pathlib import Path
import export_project_evidence as exporter

RESULT = "RES-STAGE-0.5-INTERACTION-RESEARCH-V2"
LOCAL = Path("code/outputs/formal/calibration/stage_0_5_interaction_research_v2/portable")
NAMES = ("audit.json", "budget_config.json", "run_matrix.json", "review_proposal.json", "ledger_snapshot.json",
         "provenance.json", "validation_record.json", "SHA256SUMS")


def export(root):
    source = root / LOCAL
    for name in NAMES[:-1]:
        if not (source / name).is_file():
            raise FileNotFoundError(name)
    (source / "SHA256SUMS").write_bytes(("\n".join(
        hashlib.sha256((source / name).read_bytes()).hexdigest() + "  " + name for name in NAMES[:-1]) + "\n").encode())
    original = exporter._source_pairs
    try:
        exporter._source_pairs = lambda: {RESULT: [((LOCAL / name).as_posix(), name) for name in NAMES]}
        return exporter.export_evidence(root, {RESULT})
    finally:
        exporter._source_pairs = original


def verify_preparation(root):
    issues = exporter.verify_evidence(root, {RESULT})
    if issues:
        raise ValueError(str(issues))
    portable = root / "evidence/results" / RESULT
    for line in (portable / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        if Path(name).name != name or hashlib.sha256((portable / name).read_bytes()).hexdigest() != expected:
            raise ValueError("portable_digest:" + name)
    p = json.loads((portable / "review_proposal.json").read_text(encoding="utf-8"))
    if any(p[k] for k in ["execution_allowed", "researcher_confirmed", "protocol_frozen"]):
        raise ValueError("preparation_is_not_execution_authority")
    bindings = dict(p["source_sha256"], **{p["plan_path"]: p["plan_sha256"],
                    "code/configs/stage_0_5_interaction_research_v2.json": p["budget_sha256"]})
    cfg = json.loads((portable / "budget_config.json").read_text(encoding="utf-8"))
    bindings.update({r["path"]: r["sha256"] for r in cfg["historical_references"]})
    for name, expected in bindings.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError("bound_file_changed:" + name)
    return {"portable_source_plan_budget_history": "verified", "new_trajectories": 0,
            "native_isolation_or_scientific_acceptance": "not claimed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_preparation(args.repo_root)))
    else:
        export(args.repo_root)
        print("V2_EVIDENCE_EXPORTED; historical entries preserved")
