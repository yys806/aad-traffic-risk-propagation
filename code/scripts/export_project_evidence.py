from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
EVIDENCE_ROOT = REPO_ROOT / "evidence"
MAX_FILE_BYTES = 256 * 1024
EXPORT_VERSION = "aad-portable-evidence-2026-09-09-stage-taxonomy-v2"


def _source_pairs() -> dict[str, list[tuple[str, str]]]:
    pairs: dict[str, list[tuple[str, str]]] = {
        "RES-STAGE-0.1-INFRASTRUCTURE-V3": [
            (
                "code/outputs/formal/stage_0_1/e00_real_sumo_20260907_primary_v3/e00_report.json",
                "stage_0_1_report.json",
            ),
            (
                "code/outputs/formal/stage_0_1/e00_real_sumo_20260907_primary_v3/independent_analysis.json",
                "independent_analysis.json",
            ),
        ],
        "RES-STAGE-0.1-ENV-COMPARE-V3": [
            (
                "code/outputs/formal/stage_0_1/e00_real_sumo_environment_comparison_20260907_v3.json",
                "environment_comparison.json",
            )
        ],
        "RES-STAGE-0.2-NGSIM-V2": [],
        "RES-STAGE-0.4-COMM-OBS-V3": [],
        "RES-STAGE-0.5-REAL-REF-V1": [],
        "RES-STAGE-0.6-PRELOCK-V2": [],
        "RES-PROTOCOL-READINESS-V1": [
            (
                "code/outputs/formal/calibration/protocol_lock_readiness_v1.json",
                "protocol_lock_readiness_v1.json",
            )
        ],
    }

    stage_0_1_root = "code/outputs/formal/stage_0_1/e00_real_sumo_20260907_primary_v3"
    for cell in ("s0c0", "s0c1", "s1c0", "s1c1"):
        for name in (
            "audit.json",
            "config_frozen.json",
            "manifest.json",
            "provenance.json",
            "SHA256SUMS",
            "topology.json",
        ):
            pairs["RES-STAGE-0.1-INFRASTRUCTURE-V3"].append(
                (f"{stage_0_1_root}/{cell}/{name}", f"{cell}/{name}")
            )

    calibration_sets = {
        "RES-STAGE-0.2-NGSIM-V2": (
            "stage_0_2_ngsim_v2",
            ("audit.json", "config_frozen.json", "manifest.json", "provenance.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.4-COMM-OBS-V3": (
            "stage_0_4_observability_v3",
            ("audit.json", "manifest.json", "provenance.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.5-REAL-REF-V1": (
            "stage_0_5_real_reference_v1",
            ("audit.json", "manifest.json", "SHA256SUMS"),
        ),
        "RES-STAGE-0.6-PRELOCK-V2": (
            "stage_0_6_prelock_validation_v2",
            ("audit.json", "manifest.json", "SHA256SUMS"),
        ),
    }
    for result_id, (directory, names) in calibration_sets.items():
        for name in names:
            pairs[result_id].append(
                (f"code/outputs/formal/calibration/{directory}/{name}", name)
            )
    return pairs


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source(source: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"missing evidence source: {source}")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"evidence source exceeds {MAX_FILE_BYTES} bytes: {source}")
    lowered = source.name.lower()
    if "sealed_sampling_key" in lowered:
        raise ValueError(f"refusing sealed sampling key: {source}")
    if source.suffix.lower() not in {".json", ".md", ".txt", ".sha256"} and source.name != "SHA256SUMS":
        raise ValueError(f"unsupported evidence file type: {source}")


def export_evidence(repo_root: Path) -> dict[str, object]:
    evidence_root = repo_root / "evidence"
    result_entries: list[dict[str, object]] = []
    for result_id, pairs in _source_pairs().items():
        files: list[dict[str, object]] = []
        for source_raw, destination_tail in pairs:
            source = repo_root / source_raw
            _validate_source(source)
            destination = evidence_root / "results" / result_id / destination_tail
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            files.append(
                {
                    "source_path": source_raw,
                    "snapshot_path": destination.relative_to(repo_root).as_posix(),
                    "size_bytes": destination.stat().st_size,
                    "sha256": _sha256(destination),
                }
            )
        result_entries.append({"result_id": result_id, "files": files})

    manifest: dict[str, object] = {
        "schema_version": "aad.evidence-manifest.v1",
        "export_version": EXPORT_VERSION,
        "policy": "exact small evidence snapshots; large and sealed artifacts excluded",
        "source_root": "code/outputs",
        "excluded_classes": [
            "parquet",
            "raw_csv",
            "html",
            "images",
            "logs",
            "sealed_sampling_keys",
        ],
        "results": result_entries,
    }
    manifest_path = evidence_root / "EVIDENCE_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    return manifest


def verify_evidence(repo_root: Path) -> list[str]:
    issues: list[str] = []
    manifest_path = repo_root / "evidence/EVIDENCE_MANIFEST.json"
    if not manifest_path.is_file():
        return ["missing evidence/EVIDENCE_MANIFEST.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for result in manifest.get("results", []):
        result_id = result.get("result_id", "unknown")
        for entry in result.get("files", []):
            source = repo_root / entry["source_path"]
            snapshot = repo_root / entry["snapshot_path"]
            if not snapshot.is_file():
                issues.append(f"{result_id}: missing snapshot {entry['snapshot_path']}")
                continue
            if snapshot.stat().st_size != entry.get("size_bytes"):
                issues.append(f"{result_id}: size mismatch {entry['snapshot_path']}")
            if _sha256(snapshot) != entry.get("sha256"):
                issues.append(f"{result_id}: sha256 mismatch {entry['snapshot_path']}")
            if source.is_file() and _sha256(source) != entry.get("sha256"):
                issues.append(f"{result_id}: source drift {entry['source_path']}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or verify portable AAD evidence.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    if args.verify:
        issues = verify_evidence(repo_root)
        if issues:
            print("PORTABLE_EVIDENCE_INVALID")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("PORTABLE_EVIDENCE_OK")
        return 0
    manifest = export_evidence(repo_root)
    file_count = sum(len(item["files"]) for item in manifest["results"])
    print(f"PORTABLE_EVIDENCE_EXPORTED results={len(manifest['results'])} files={file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
