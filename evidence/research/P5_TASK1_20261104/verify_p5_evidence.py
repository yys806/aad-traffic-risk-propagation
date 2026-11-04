"""Verify the design-only evidence package using the Python standard library.

Does not import riskprop, launch traffic, or read datasets/holdout.
Git subprocesses read object bytes only. Supports a minimal package-only archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import runpy
import subprocess
from pathlib import Path


def sha(body):
    return hashlib.sha256(body).hexdigest()


def git_bodies(root, revision, paths):
    if not paths:
        return {}
    requests = "".join(revision + ":" + p + "\n" for p in paths).encode("utf-8")
    raw = subprocess.check_output(["git", "cat-file", "--batch"], cwd=root, input=requests)
    pos, result = 0, {}
    for path in paths:
        end = raw.index(b"\n", pos)
        fields = raw[pos:end].split()
        if len(fields) != 3 or fields[1] != b"blob":
            raise ValueError("Missing Git blob: " + path)
        size = int(fields[2])
        pos = end + 1
        result[path] = raw[pos:pos+size]
        pos += size+1
    return result


def verify(root, package_only, view):
    package = root / "evidence/research/P5_TASK1_20261104"
    entries = []
    for line in (package/"SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = (root/rel).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Unsafe or missing package file: " + rel)
        entries.append((expected, rel, path))
    mismatches = [(expected, rel) for expected, rel, path in entries if sha(path.read_bytes()) != expected]
    git_fallback_count = 0
    if mismatches and not package_only:
        # Verify actual committed blob bytes; never silently normalize line endings.
        blobs = git_bodies(root, "HEAD", [rel for _,rel in mismatches])
        for expected,rel in mismatches:
            if sha(blobs[rel]) != expected:
                raise AssertionError("Package SHA mismatch in workspace and Git: " + rel)
            git_fallback_count += 1
    elif mismatches:
        raise AssertionError("Portable package SHA mismatch: " + repr(mismatches))

    namespace = runpy.run_path(str(package/"check_identification_math.py"))
    computed = namespace["run_checks"]()
    saved = json.loads((package/"identification_math_results.json").read_text(encoding="utf-8"))
    if computed != saved:
        raise AssertionError("Saved mathematical results differ from independent recomputation")
    result = {"status": "PASS", "package_files_sha256_verified": len(entries),
              "package_git_blob_fallbacks": git_fallback_count,
              "exact_math_checks_passed": computed["checks_passed"],
              "package_only": package_only, "new_traffic_runs": 0}
    if package_only:
        return result

    protected = json.loads((package/"protected_files.json").read_text(encoding="utf-8"))
    files = protected["files"]
    if view in ("workspace", "both"):
        bad = [p for p,r in files.items() if sha((root/p).read_bytes()) != r["native_sha256"]]
        if bad:
            raise AssertionError("Native protected bytes changed: " + repr(bad))
        result["protected_native_files_verified"] = len(files)
    if view in ("git", "both"):
        blobs = git_bodies(root, "HEAD", list(files))
        bad = [p for p,r in files.items() if sha(blobs[p]) != r["git_blob_sha256"]]
        if bad:
            raise AssertionError("Protected committed bytes changed: " + repr(bad))
        result["protected_git_files_verified"] = len(files)

    sources = json.loads((package/"source_manifest.json").read_text(encoding="utf-8"))
    base = sources["base_commit"]
    blobs = git_bodies(root, base, [s["path"] for s in sources["sources"]])
    for source in sources["sources"]:
        if sha(blobs[source["path"]]) != source["git_blob_sha256_at_base"]:
            raise AssertionError("Historical source binding mismatch: " + source["path"])
    result["baseline_source_bindings_verified"] = len(blobs)
    definitions = (root/"docs/research/definitions/CORE_SCIENTIFIC_DEFINITIONS.md").read_text(encoding="utf-8-sig")
    count = len(re.findall(r"^## DEF-[A-Z]+-\d+\b", definitions, re.M))
    if count != 27:
        raise AssertionError("Definition ID count changed")
    result["definition_ids"] = count

    base_registry = json.loads(git_bodies(root, base, ["docs/PROJECT_REGISTRY.json"])["docs/PROJECT_REGISTRY.json"].decode("utf-8-sig"))
    current = json.loads((root/"docs/PROJECT_REGISTRY.json").read_text(encoding="utf-8-sig"))
    for section in ["experiments", "results", "history"]:
        if current[section] != base_registry[section]:
            raise AssertionError("Historical registry section changed: " + section)
    for key,value in base_registry["current"].items():
        if current["current"].get(key) != value:
            raise AssertionError("Inherited current/Gate field changed: " + key)
    for key,value in base_registry["research_audits"].items():
        if current["research_audits"].get(key) != value:
            raise AssertionError("Historical research audit changed: " + key)
    result["inherited_registry_and_gate_fields_unchanged"] = True
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--package-only", action="store_true")
    parser.add_argument("--view", choices=["workspace", "git", "both"], default="both")
    args = parser.parse_args()
    print(json.dumps(verify(args.repo_root.resolve(), args.package_only, args.view), indent=2))
