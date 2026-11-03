"""Package truthful P7 Task2 evidence; read-only toward all SUMO/historical outputs."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskprop.controller_evidence import schema_description
from riskprop.message_driven_longitudinal_controller import byte_hash, canonical_bytes
from riskprop.p7_evidence_verification import read_json, verify_run
from riskprop.p7_sumo_integration import compare_conditions


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True, help="Existing local engineering capture root")
    args = parser.parse_args()
    root, local = args.repo_root.resolve(), args.output.resolve()
    dest = root / "evidence/research/P7_TASK2_20261103"
    dest.mkdir(parents=True, exist_ok=True)
    verified, summaries, bindings, sample_artifacts = {}, {}, {}, {}
    for name in ("no_message", "disabled", "enabled"):
        run = local / "smoke" / name
        verified[name] = verify_run(run, local / "captured_implementation_v1")
        summaries[name] = read_json(run / "run_summary.json")
        for filename in ("run_config.json", "run_summary.json", "artifact_manifest.json", "provenance.json", "command_tenures.json"):
            write_json(dest / "conditions" / name / filename, read_json(run / filename))
        sidecar = (run / "controller_evidence.json").read_bytes()
        (dest / "conditions" / name / "controller_evidence.json.gz").write_bytes(gzip.compress(sidecar, mtime=0))
        (dest / "conditions" / name / "association_validation.json.gz").write_bytes(
            gzip.compress((run / "association_validation.json").read_bytes(), mtime=0))
        bindings[name] = {"sidecar_sha256": byte_hash(sidecar),
            "artifact_manifest_sha256": byte_hash((run / "artifact_manifest.json").read_bytes()),
            "trajectory_sha256": byte_hash((run / "actual_trajectory.json").read_bytes()),
            "local_run": run.relative_to(root).as_posix()}
        records = read_json(run / "controller_evidence.json")["records"]
        selected = []
        selected += [r["data"]["payload_ref"] for r in records if r["kind"] == "message"]
        decisions = [r for r in records if r["kind"] == "decision" and r["data"]["consumed_message_refs"]]
        if decisions:
            out = read_json(run / decisions[0]["data"]["decision_output_ref"])
            selected += [out["input_snapshot_ref"]]
        sample_artifacts[name] = {rel: base64.b64encode((run / rel).read_bytes()).decode("ascii") for rel in selected}
    compare = compare_conditions(local / "smoke")
    write_json(dest / "trajectory_summary.json", compare)
    write_json(dest / "association_validation.json", verified)
    write_json(dest / "controller_evidence_manifest.json", {"schema_version": "aad.p7.controller-evidence-manifest.v1",
        "conditions": bindings, "sample_artifacts": sample_artifacts,
        "portable_verification_scope": "complete P3 graph and selected payload/snapshot bytes; all external bytes verified locally before export",
        "full_raw_trajectories_and_logs": "LOCAL_ONLY_NOT_PORTABLE", "fixture_only": True, "scientific_claim_eligible": False})
    code = ["code/src/riskprop/controller_evidence.py", "code/scripts/p3_controller_evidence_fixtures.py",
        "code/src/riskprop/message_driven_longitudinal_controller.py", "code/src/riskprop/p7_evidence_adapter.py",
        "code/src/riskprop/p7_message_runtime.py", "code/src/riskprop/p7_sumo_integration.py",
        "code/src/riskprop/p7_evidence_verification.py", "code/scripts/run_p7_task2_engineering.py",
        "code/scripts/finalize_p7_task2_engineering.py", "code/tests/test_p7_message_controller.py", "code/tests/test_p7_sumo_evidence.py"]
    captured = read_json(local / "smoke/enabled/provenance.json")["source_closure"]
    captured_bytes = {p: base64.b64encode((local / "captured_implementation_v1" / p).read_bytes()).decode("ascii") for p in captured}
    (dest / "captured_source_v1.json.gz").write_bytes(gzip.compress(canonical_bytes(captured_bytes), mtime=0))
    write_json(dest / "source_manifest.json", {"baseline_git_sha": read_json(local / "protected_baseline.json")["baseline_sha"],
        "current_worktree_source_hashes": {p: byte_hash((root / p).read_bytes()) for p in code},
        "captured_v1_source_hashes": captured, "captured_v1_source_bytes": "captured_source_v1.json.gz",
        "captured_source_scope": "nine recorded entry/direct-dependency files, not a claim of all transitive dependencies",
        "corrected_v2_sumo_status": "NOT_EXECUTED_STOP_RULE",
        "working_tree": subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root).decode("utf-8", errors="replace")})
    write_json(dest / "controller_config.json", read_json(root / "code/configs/p7_task2_engineering_candidate_v2.json"))
    write_json(dest / "captured_controller_config_v1.json", read_json(local / "smoke/enabled/controller_config.json"))
    write_json(dest / "schema_versions.json", {"p3": schema_description(), "payload": "aad.p7.risk-payload.engineering.v1",
        "captured_policy": "aad.p7.longitudinal.engineering.v1", "current_policy": "aad.p7.longitudinal.engineering.v1.1",
        "current_config": "aad.p7.engineering-controller-config.v2",
        "legacy_boundary": "aad.p3.policy-input-adoption.proposed.v0.1 / PROPOSED retained"})
    baseline = read_json(local / "protected_baseline.json")
    changed = [p for p, h in baseline["files"].items() if byte_hash((root / p).read_bytes()) != h]
    if changed:
        raise RuntimeError("protected history changed: " + repr(changed))
    write_json(dest / "historical_protection.json", {**baseline, "files_checked": len(baseline["files"]), "changed": changed,
        "scope": "selected tracked evidence/config/definitions/legacy interfaces; not re-reading historical large trajectories"})
    tests = []
    for name in ("unit_first", "unit_second", "targeted_final", "targeted_sealed", "correction_final"):
        p = local / (name + ".xml")
        if p.exists():
            suite = ET.parse(p).getroot()
            suites = suite.findall("testsuite") if suite.tag != "testsuite" else [suite]
            counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ("tests", "errors", "failures", "skipped")}
            tests.append({"run": name, **counts, "xml_path": p.relative_to(root).as_posix(), "xml_sha256": byte_hash(p.read_bytes())})
    write_json(dest / "test_results.json", {"executions": tests, "native_launch_tests_deselected": 7,
        "reason": "three engineering conditions already run; additional SUMO stopped after emergency braking",
        "tests_are_not_sumo_acceptance": True,
        "other_failed_commands": ["two invalid workdir reconnaissance commands (no writes)",
            "one patch framing failure (atomic no write)", "temporary inline JSON-edit Python quoting errors (no file change; task transcript retained)"]})
    write_json(dest / "official_sumo_api_sources.json", read_json(local / "official_docs/sources.json"))
    if (local / "final_checks.json").exists():
        write_json(dest / "final_checks.json", read_json(local / "final_checks.json"))
    validation = {"task_id": "AAD-P7-TASK2-20261103", "date": "2026-11-03",
        "status": "ENGINEERING_IMPLEMENTED_SUMO_ACCEPTANCE_BLOCKED",
        "new_sumo_runs": 3, "unique_engineering_conditions": 3, "seeds": [20261103],
        "sumo_acceptance": {k: v["smoke_acceptance"] for k, v in verified.items()},
        "current_corrected_candidate_sumo_verified": False, "current_corrected_candidate_unit_tested": True,
        "p3_complete_graphs_verified": True, "formal_a": 0, "independent_qualified": 0,
        "regional_risk_effect": "UNKNOWN", "f0_and_overall_tr_tp": "UNKNOWN",
        "pilot_runs": 0, "independent_v_runs": 0, "locked_holdout_reads": 0,
        "scientific_claim_eligible": False, "formal_definitions_changed": False,
        "formal_config_changed": False, "gate_changed": False, "protocol_lock": "BLOCKED", "stage1_1": "NOT_AUTHORIZED",
        "new_sumo_runs_after_anomaly_detection": 0,
        "commit": None, "push": None,
        "git_reason": "SUMO acceptance blocker retained; no incomplete/failed research deliverable pushed",
        "completion_limit": "A/B capture passed; C emergency braking rejects final acceptance; corrected v2 unit-only, needs separately authorized bounded SUMO recheck"}
    write_json(dest / "validation.json", validation)
    # Explicit in-place registration; exporter already understands self-managed bundles.
    manifest_path = root / "evidence/EVIDENCE_MANIFEST.json"
    registry = read_json(manifest_path)
    files = [{"source_path": p.relative_to(root).as_posix(), "snapshot_path": p.relative_to(root).as_posix(),
        "size_bytes": p.stat().st_size, "sha256": byte_hash(p.read_bytes())} for p in sorted(dest.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"]
    sha = chr(10).join(f'{i["sha256"]}  {Path(i["snapshot_path"]).relative_to(dest.relative_to(root)).as_posix()}' for i in files) + chr(10)
    (dest / "SHA256SUMS").write_text(sha, encoding="utf-8", newline=chr(10))
    p = dest / "SHA256SUMS"
    files.append({"source_path": p.relative_to(root).as_posix(), "snapshot_path": p.relative_to(root).as_posix(),
                  "size_bytes": p.stat().st_size, "sha256": byte_hash(p.read_bytes())})
    result = {"result_id": "RES-P7-TASK2-20261103", "files": files}
    registry["results"] = [r for r in registry["results"] if r["result_id"] != result["result_id"]] + [result]
    manifest_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8", newline=chr(10))
    print(json.dumps({"validation_status": validation["status"], "conditions": validation["sumo_acceptance"],
                      "comparison": compare, "portable_files": len(files)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
