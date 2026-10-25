"""Only this engineering result is exported; old manifest entries are retained."""
import argparse
import hashlib
import json
from pathlib import Path
import export_project_evidence as exporter

RESULT = "RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1"
LOCAL = Path("code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1/portable")
NAMES = ("identity_contract.json", "initialization_audit.json", "history_allowlist.json", "C6_comparison.json",
         "C6_independent_verification.json", "admission_profile.json", "provenance.json", "validation_record.json", "SHA256SUMS")


def export(root):
    folder = root / LOCAL
    lines = [hashlib.sha256((folder / n).read_bytes()).hexdigest() + "  " + n for n in NAMES[:-1]]
    (folder / "SHA256SUMS").write_bytes(("\n".join(lines) + "\n").encode())
    original = exporter._source_pairs
    try:
        exporter._source_pairs = lambda: {RESULT: [((LOCAL / n).as_posix(), n) for n in NAMES]}
        return exporter.export_evidence(root, {RESULT})
    finally:
        exporter._source_pairs = original


def verify(root):
    errors = exporter.verify_evidence(root, {RESULT})
    if errors:
        raise ValueError(str(errors))
    folder = root / "evidence/results" / RESULT
    for line in (folder / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split("  ", 1)
        if Path(name).name != name or hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:
            raise ValueError("portable_hash:" + name)
    provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
    for name, expected in provenance["source_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError("source_binding:" + name)
    profile = json.loads((folder / "admission_profile.json").read_text(encoding="utf-8"))
    if any(profile[k] is not False for k in ["execution_allowed", "researcher_confirmed", "protocol_frozen", "accepted_for_new_task"]):
        raise ValueError("engineering_preparation_cannot_approve_execution")
    return {"portable_source_verified": True, "new_trajectories": 0, "native_isolation_accepted": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    if a.verify:
        print(json.dumps(verify(a.repo_root)))
    else:
        export(a.repo_root)
        print("V2_ADMISSION_EVIDENCE_EXPORTED; historical entries preserved")
