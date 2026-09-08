"""Run-level artifact contracts for preregistered experiments."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REQUIRED_RUN_ARTIFACTS = (
    "config_frozen.json",
    "provenance.json",
    "state.parquet",
    "emission.parquet",
    "protocol.parquet",
    "action.parquet",
    "risk.parquet",
    "audit.json",
    "run.log",
)


class FormalArtifactError(ValueError):
    """Raised when a formal run cannot satisfy the frozen artifact contract."""


def append_failure_record(
    output_root: Path,
    *,
    experiment_id: str,
    run_id: str,
    stage: str,
    error: Exception,
    exit_code: int,
    command: list[str],
) -> Path:
    """Append one machine-readable failure without touching an existing run."""

    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": "e00.failure.v1",
        "experiment_id": experiment_id,
        "run_id": run_id,
        "stage": stage,
        "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "exception_type": type(error).__name__,
        "message": str(error),
        "exit_code": int(exit_code),
        "command": list(command),
        "working_directory": str(Path.cwd().resolve()),
    }
    ledger = output_root / "failure_ledger.jsonl"
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with ledger.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
    return ledger


MANIFEST_NAME = "manifest.json"
CHECKSUM_NAME = "SHA256SUMS"
SCHEMA_VERSION = "e00.v1"
_SEAL_FILES = frozenset({MANIFEST_NAME, CHECKSUM_NAME})
_PARQUET_ARTIFACTS = (
    "state.parquet",
    "emission.parquet",
    "protocol.parquet",
    "action.parquet",
    "risk.parquet",
)
_JSON_ARTIFACTS = ("config_frozen.json", "provenance.json", "audit.json")

TABLE_REQUIRED_COLUMNS = {
    "state.parquet": (
        "run_id",
        "experiment_id",
        "scenario_id",
        "cell_id",
        "configured_seed",
        "simulation_seed",
        "time_s",
        "vehicle_id",
        "edge_id",
        "lane_id",
        "x_m",
        "y_m",
        "speed_mps",
        "acceleration_mps2",
        "leader_id",
        "net_gap_m",
        "relative_speed_mps",
    ),
    "emission.parquet": (
        "run_id",
        "cell_id",
        "time_s",
        "vehicle_id",
        "x_m",
        "y_m",
        "speed_mps",
        "acceleration_mps2",
        "edge_id",
        "lane_id",
        "leader_id",
        "net_gap_m",
        "relative_speed_mps",
    ),
    "protocol.parquet": (
        "run_id",
        "cell_id",
        "message_id",
        "source_event_id",
        "source_vehicle_id",
        "target_vehicle_id",
        "generated_time_s",
        "sent_time_s",
        "delivered_time_s",
        "validation_time_s",
        "adopted_time_s",
        "message_age_s",
        "message_generated",
        "message_sent",
        "message_dropped",
        "message_delivered",
        "source_valid",
        "target_valid",
        "freshness_valid",
        "adopted",
        "rejection_reason",
        "payload_type",
        "payload_risk",
        "message_kind",
    ),
    "action.parquet": (
        "run_id",
        "cell_id",
        "target_vehicle_id",
        "time_s",
        "command_acceleration_mps2",
        "applied_acceleration_mps2",
        "safety_intervened",
        "action_diverged",
        "paired_reference_cell_id",
    ),
    "risk.parquet": (
        "run_id",
        "cell_id",
        "target_vehicle_id",
        "window_id",
        "window_start_s",
        "window_end_s",
        "metric",
        "value",
        "tau_p_lower_s",
        "attributable",
        "inclusion_status",
        "inclusion_reason",
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_required_files(run_dir: Path) -> None:
    if not run_dir.is_dir():
        raise FormalArtifactError(f"Formal run directory does not exist: {run_dir}")
    missing = [
        name for name in REQUIRED_RUN_ARTIFACTS if not (run_dir / name).is_file()
    ]
    if missing:
        raise FormalArtifactError(
            f"Formal run is missing required artifacts: {', '.join(missing)}"
        )


def _validate_payload_formats(run_dir: Path) -> None:
    try:
        import pyarrow
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise FormalArtifactError(
            "Formal Parquet validation requires the frozen pyarrow dependency"
        ) from exc
    for name in _PARQUET_ARTIFACTS:
        try:
            parquet.ParquetFile(run_dir / name)
        except (OSError, pyarrow.ArrowInvalid) as exc:
            raise FormalArtifactError(
                f"Formal artifact is not valid Parquet: {name}: {exc}"
            ) from exc
    for name in _JSON_ARTIFACTS:
        try:
            value = json.loads((run_dir / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FormalArtifactError(
                f"Formal artifact is not valid JSON: {name}: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise FormalArtifactError(f"Formal JSON artifact must be an object: {name}")


def validate_theory_artifact_schema(run_dir: Path) -> dict[str, int]:
    """Require fields that make the frozen theory chain independently auditable."""

    run_dir = Path(run_dir)
    _validate_required_files(run_dir)
    try:
        import pyarrow
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise FormalArtifactError(
            "Theory schema validation requires the frozen pyarrow dependency"
        ) from exc
    rows: dict[str, int] = {}
    for name, required_columns in TABLE_REQUIRED_COLUMNS.items():
        try:
            file = parquet.ParquetFile(run_dir / name)
        except (OSError, pyarrow.ArrowInvalid) as exc:
            raise FormalArtifactError(
                f"Formal artifact is not valid Parquet: {name}: {exc}"
            ) from exc
        actual = set(file.schema_arrow.names)
        missing = [column for column in required_columns if column not in actual]
        if missing:
            raise FormalArtifactError(
                f"{name} is missing theory-required columns: {', '.join(missing)}"
            )
        rows[name] = int(file.metadata.num_rows)
    return rows


def _content_files(run_dir: Path) -> list[Path]:
    files = []
    for path in run_dir.rglob("*"):
        if not path.is_file() or path.name in _SEAL_FILES:
            continue
        if path.is_symlink():
            raise FormalArtifactError(f"Formal artifacts cannot be symlinks: {path}")
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(run_dir).as_posix())


def _file_entry(run_dir: Path, path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(run_dir).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _git_output(repo_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if process.returncode != 0:
        message = process.stderr.strip() or process.stdout.strip()
        raise FormalArtifactError(f"Git provenance command failed: {message}")
    return process.stdout.strip()


def collect_run_provenance(
    repo_root: Path,
    *,
    command: list[str],
    started_at_utc: str,
    finished_at_utc: str,
    exit_code: int,
) -> dict[str, Any]:
    """Collect the minimum immutable provenance needed for a formal run."""

    repo_root = Path(repo_root).resolve()
    if not command or not all(isinstance(part, str) and part for part in command):
        raise FormalArtifactError("Provenance command must be a non-empty string list")
    commit = _git_output(repo_root, "rev-parse", "HEAD")
    if len(commit) != 40:
        raise FormalArtifactError(f"Unexpected Git commit identifier: {commit!r}")
    status = _git_output(repo_root, "status", "--porcelain", "--untracked-files=all")
    return {
        "schema_version": "e00.provenance.v1",
        "repo_root": str(repo_root),
        "git_commit": commit,
        "git_dirty": bool(status),
        "command": list(command),
        "working_directory": str(Path.cwd().resolve()),
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "exit_code": int(exit_code),
        "python_version": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
    }


def build_run_manifest(
    run_dir: Path, *, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Seal a complete formal run with a deterministic manifest and checksums."""

    run_dir = Path(run_dir)
    _validate_required_files(run_dir)
    _validate_payload_formats(run_dir)
    if not isinstance(metadata, dict) or not metadata.get("run_id"):
        raise FormalArtifactError("Manifest metadata requires a non-empty run_id")
    files = _content_files(run_dir)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "metadata": metadata,
        "required_artifacts": list(REQUIRED_RUN_ARTIFACTS),
        "files": [_file_entry(run_dir, path) for path in files],
    }
    try:
        encoded = json.dumps(
            manifest, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
        ) + "\n"
    except (TypeError, ValueError) as exc:
        raise FormalArtifactError(f"Manifest metadata is not valid JSON: {exc}") from exc

    manifest_path = run_dir / MANIFEST_NAME
    manifest_path.write_text(encoded, encoding="utf-8", newline="\n")
    checksum_paths = [*files, manifest_path]
    checksum_text = "".join(
        f"{_sha256(path)}  {path.relative_to(run_dir).as_posix()}\n"
        for path in checksum_paths
    )
    (run_dir / CHECKSUM_NAME).write_text(
        checksum_text, encoding="utf-8", newline="\n"
    )
    return manifest


def validate_run_manifest(run_dir: Path) -> dict[str, Any]:
    """Verify that a sealed formal run is complete and has not changed."""

    run_dir = Path(run_dir)
    _validate_required_files(run_dir)
    _validate_payload_formats(run_dir)
    manifest_path = run_dir / MANIFEST_NAME
    checksum_path = run_dir / CHECKSUM_NAME
    if not manifest_path.is_file() or not checksum_path.is_file():
        raise FormalArtifactError("Formal run is not sealed by manifest.json and SHA256SUMS")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FormalArtifactError(f"Cannot read manifest.json: {exc}") from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise FormalArtifactError(
            f"Unsupported manifest schema: {manifest.get('schema_version')!r}"
        )

    listed_entries = manifest.get("files")
    if not isinstance(listed_entries, list):
        raise FormalArtifactError("manifest.json files must be a list")
    listed: dict[str, dict[str, Any]] = {}
    for entry in listed_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise FormalArtifactError("manifest.json contains an invalid file entry")
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise FormalArtifactError(f"Unsafe manifest path: {entry['path']}")
        if entry["path"] in listed:
            raise FormalArtifactError(f"Duplicate manifest path: {entry['path']}")
        listed[entry["path"]] = entry

    actual_paths = {
        path.relative_to(run_dir).as_posix(): path for path in _content_files(run_dir)
    }
    unlisted = sorted(set(actual_paths) - set(listed))
    missing = sorted(set(listed) - set(actual_paths))
    if unlisted:
        raise FormalArtifactError(
            f"Formal run contains files not listed in manifest.json: {', '.join(unlisted)}"
        )
    if missing:
        raise FormalArtifactError(
            f"manifest.json lists missing files: {', '.join(missing)}"
        )
    for relative, path in actual_paths.items():
        expected = listed[relative]
        if expected.get("bytes") != path.stat().st_size:
            raise FormalArtifactError(f"Artifact size changed: {relative}")
        if expected.get("sha256") != _sha256(path):
            raise FormalArtifactError(f"Artifact checksum changed: {relative}")

    checksum_entries: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise FormalArtifactError(f"Invalid SHA256SUMS line: {line}")
        checksum_entries[parts[1]] = parts[0]
    checksum_targets = {**actual_paths, MANIFEST_NAME: manifest_path}
    if set(checksum_entries) != set(checksum_targets):
        raise FormalArtifactError("SHA256SUMS does not cover exactly the sealed artifacts")
    for relative, path in checksum_targets.items():
        if checksum_entries[relative] != _sha256(path):
            raise FormalArtifactError(f"SHA256SUMS mismatch: {relative}")
    return manifest
