"""Verify P7 portable bytes/graphs; optionally verify local raw capture. Never launches SUMO."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sys


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--local-output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "code/src"))
    from riskprop.controller_evidence import EvidenceJournal
    from riskprop.message_driven_longitudinal_controller import canonical_bytes

    checksums = {}
    for line in (here / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = (here / relative).resolve()
        assert path.is_relative_to(here) and path.is_file(), relative
        assert relative not in checksums, relative
        assert digest(path.read_bytes()) == expected, relative
        checksums[relative] = expected
    actual = {p.relative_to(here).as_posix() for p in here.rglob("*")
              if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts}
    assert actual == set(checksums), "unsealed or missing portable files"
    source = read(here / "source_manifest.json")
    for rel, expected in source["current_worktree_source_hashes"].items():
        assert digest((root / rel).read_bytes()) == expected, rel
    captured = json.loads(gzip.decompress((here / source["captured_v1_source_bytes"]).read_bytes()))
    assert set(captured) == set(source["captured_v1_source_hashes"])
    for rel, encoded in captured.items():
        assert digest(base64.b64decode(encoded, validate=True)) == source["captured_v1_source_hashes"][rel], rel
    bindings = read(here / "controller_evidence_manifest.json")
    verification = read(here / "association_validation.json")
    result = {}
    for name, binding in bindings["conditions"].items():
        directory = here / "conditions" / name
        sidecar = gzip.decompress((directory / "controller_evidence.json.gz").read_bytes())
        assert digest(sidecar) == binding["sidecar_sha256"]
        audit = EvidenceJournal.from_dict(json.loads(sidecar)).validate()
        saved = json.loads(gzip.decompress((directory / "association_validation.json.gz").read_bytes()))
        # Original exporter omits the redundant timeline; full sidecar is still validated.
        comparable = dict(audit)
        if "timeline" not in saved:
            comparable.pop("timeline", None)
        elif saved["timeline"] is None:
            comparable["timeline"] = None
        assert canonical_bytes(comparable) == canonical_bytes(saved), name
        for key in ("record_count", "counts_by_kind", "structural_status"):
            assert audit[key] == verification[name][key], (name, key)
        assert audit["structural_status"] in ("VALID", "VALID_WITH_UNKNOWNS")
        records = json.loads(sidecar)["records"]
        samples = bindings["sample_artifacts"][name]
        for record in records:
            data = record["data"]
            if record["kind"] == "message":
                assert digest(base64.b64decode(samples[data["payload_ref"]], validate=True)) == data["payload_hash"]
        for rel, encoded in samples.items():
            if "snapshot" in rel:
                expected = {r["data"]["input_snapshot_hash"] for r in records if r["kind"] == "decision"}
                assert digest(base64.b64decode(encoded, validate=True)) in expected
        result[name] = {"records": audit["record_count"], "structural_status": audit["structural_status"],
                        "smoke_acceptance": verification[name]["smoke_acceptance"]["acceptance_status"]}
    validation = read(here / "validation.json")
    assert validation["status"] == "ENGINEERING_IMPLEMENTED_SUMO_ACCEPTANCE_BLOCKED"
    assert result["enabled"]["smoke_acceptance"] == "BLOCKED_ABNORMAL_BRAKING"
    assert validation["current_corrected_candidate_sumo_verified"] is False
    if args.local_output:
        from riskprop.p7_evidence_verification import verify_run
        local = args.local_output.resolve()
        for name in result:
            checked = verify_run(local / "smoke" / name, local / "captured_implementation_v1")
            assert canonical_bytes(checked) == canonical_bytes(verification[name]), name
    print(json.dumps({"status": "PORTABLE_VERIFIED_ACCEPTANCE_STILL_BLOCKED", "sealed_files": len(checksums),
        "conditions": result, "full_local_external_bytes_verified": bool(args.local_output),
        "sumo_launched": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
