"""Independent offline hash/graph/command verification; never starts SUMO."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def digest(b):
    return hashlib.sha256(b).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    p.add_argument("--local-output", type=Path)
    args = p.parse_args()
    root, here = args.repo_root.resolve(), Path(__file__).resolve().parent
    checksums = {}
    for line in (here / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = (here / rel).resolve()
        assert path.is_relative_to(here) and rel not in checksums
        assert digest(path.read_bytes()) == expected, rel
        checksums[rel] = expected
    assert set(checksums) == {p.relative_to(here).as_posix() for p in here.rglob("*") if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts}
    sys.path.insert(0, str(root / "code/src"))
    from riskprop.controller_evidence import EvidenceJournal
    from riskprop.message_driven_longitudinal_controller import canonical_bytes
    sources = read(here / "source_manifest.json")
    bundles = json.loads(gzip.decompress((here / "source_bytes.json.gz").read_bytes()))
    for owner in ("captured_v2", "task_start_sources"):
        assert set(bundles[owner]) == set(sources[owner]), owner
        for rel, encoded in bundles[owner].items():
            assert digest(base64.b64decode(encoded, validate=True)) == sources[owner][rel], rel
    git_line_ending_variants = []
    for rel, h in sources["current_source_hashes"].items():
        actual = (root / rel).read_bytes()
        if digest(actual) == h:
            continue
        assert digest(actual) == sources["git_index_source_hashes"][rel], rel
        captured = base64.b64decode(bundles["captured_v2"][rel], validate=True)
        assert actual.replace(b"\r\n", b"\n") == captured.replace(b"\r\n", b"\n"), rel
        git_line_ending_variants.append(rel)
    raw = gzip.decompress((here / "controller_evidence.json.gz").read_bytes())
    assert digest(raw) == sources["controller_evidence_raw_sha256"]
    journal = EvidenceJournal.from_dict(json.loads(raw))
    audit = journal.validate()
    old_audit = json.loads(gzip.decompress((here / "association_validation.json.gz").read_bytes()))
    comparable = dict(audit)
    if "timeline" not in old_audit:
        comparable.pop("timeline", None)
    assert canonical_bytes(comparable) == canonical_bytes(old_audit)
    assert audit["structural_status"] in ("VALID", "VALID_WITH_UNKNOWNS")
    validation = read(here / "validation.json")
    assert audit["counts_by_kind"] == validation["counts_by_kind"]
    assert validation["status"] == "ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS" and all(validation["checks"].values())
    assert digest((here / "controller_config.json").read_bytes()) == sources["config_original_bytes_sha256"]
    artifacts = read(here / "artifact_manifest.json")["files"]
    byte_samples = read(here / "byte_samples.json")
    readbacks = read(here / "readback_samples.json")
    commands = json.loads(gzip.decompress((here / "command_bytes.json.gz").read_bytes()))
    for rel, encoded in {**byte_samples, **readbacks, **commands}.items():
        assert digest(base64.b64decode(encoded, validate=True)) == artifacts[rel], rel
    command_records = [r for r in journal.records if r["kind"] == "command"]
    assert len(commands) == len(command_records)
    for record in command_records:
        d = record["data"]
        raw = json.loads(base64.b64decode(commands[d["execution_interface_ref"]], validate=True))
        assert raw["api"] == "traci.vehicle.setMaxSpeed"
        assert raw["command_id"] == d["command_id"] and raw["decision_id"] == d["decision_id"]
        assert raw["value_mps"] == raw["getter_max_speed_mps"] == d["command_value"]
        assert raw["status"] == "ACKNOWLEDGED"
    for record in journal.records:
        if record["kind"] == "message":
            d = record["data"]
            assert digest(base64.b64decode(byte_samples[d["payload_ref"]], validate=True)) == d["payload_hash"]
    for rel, encoded in byte_samples.items():
        if rel.startswith("inputs/"):
            hashes = {r["data"]["input_snapshot_hash"] for r in journal.records if r["kind"] == "decision"}
            assert digest(base64.b64decode(encoded, validate=True)) in hashes
    if args.local_output:
        spec = importlib.util.spec_from_file_location("p7_task2_1_finalize", root / "code/scripts/finalize_p7_task2_1.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.analyze(root, args.local_output.resolve())
        assert canonical_bytes(result) == canonical_bytes(validation)
    print(json.dumps({"status": "P7_TASK2_1_PORTABLE_VERIFIED", "sealed_files": len(checksums),
        "full_p3_records": audit["record_count"], "command_getter_witnesses": len(commands),
        "full_local_raw_comparison_recomputed": bool(args.local_output), "sumo_started": False,
        "explicit_git_line_ending_variants": git_line_ending_variants,
        "scientific_claim_eligible": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
