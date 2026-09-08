"""Validation helpers for the AAD project knowledge indexes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "aad.project-registry.v1"
REQUIRED_ENTRY_PATHS = (
    "README.md",
    "AGENTS.md",
    "PROJECT_CONTEXT.md",
    "docs/PROJECT_INDEX.md",
    "docs/ARCHITECTURE.md",
    "docs/RESEARCH_STATUS.md",
    "docs/EXPERIMENT_INDEX.md",
    "docs/RESULTS_INDEX.md",
    "docs/CHANGELOG.md",
)


def _load_registry(path: Path, issues: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        issues.append("missing registry: docs/PROJECT_REGISTRY.json")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(f"invalid registry docs/PROJECT_REGISTRY.json: {exc}")
        return None
    if not isinstance(data, dict):
        issues.append("registry root must be a JSON object")
        return None
    return data


def _check_repo_path(repo_root: Path, raw_path: object, context: str, issues: list[str]) -> None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(f"{context} contains an invalid path")
        return
    path = Path(raw_path)
    if path.is_absolute():
        issues.append(f"{context} must use a repository-relative path: {raw_path}")
        return
    if not (repo_root / path).exists():
        issues.append(f"{context} references missing path: {raw_path}")


def _read_index(path: Path, label: str, issues: list[str]) -> str:
    if not path.is_file():
        issues.append(f"missing {label}: {path.as_posix()}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issues.append(f"cannot read {label}: {exc}")
        return ""


def validate_project_docs(repo_root: str | Path) -> list[str]:
    """Return human-readable consistency issues for the project indexes."""

    root = Path(repo_root).resolve()
    issues: list[str] = []
    registry = _load_registry(root / "docs/PROJECT_REGISTRY.json", issues)
    if registry is None:
        return issues

    if registry.get("schema_version") != EXPECTED_SCHEMA:
        issues.append(
            f"unexpected registry schema: {registry.get('schema_version')!r}; "
            f"expected {EXPECTED_SCHEMA!r}"
        )

    canonical_entries = registry.get("canonical_entries")
    if not isinstance(canonical_entries, list):
        issues.append("canonical_entries must be a list")
        canonical_entries = []

    for required in REQUIRED_ENTRY_PATHS:
        if required not in canonical_entries:
            issues.append(f"canonical_entries is missing required entry: {required}")
    for path in canonical_entries:
        _check_repo_path(root, path, "canonical_entries", issues)

    experiment_index = _read_index(
        root / "docs/EXPERIMENT_INDEX.md", "EXPERIMENT_INDEX", issues
    )
    result_index = _read_index(root / "docs/RESULTS_INDEX.md", "RESULTS_INDEX", issues)

    experiments = registry.get("experiments")
    if not isinstance(experiments, list):
        issues.append("experiments must be a list")
        experiments = []

    experiment_ids: set[str] = set()
    for experiment in experiments:
        if not isinstance(experiment, dict):
            issues.append("experiments contains a non-object entry")
            continue
        experiment_id = experiment.get("id")
        if not isinstance(experiment_id, str) or not experiment_id:
            issues.append("experiment entry has no valid id")
            continue
        if experiment_id in experiment_ids:
            issues.append(f"duplicate experiment id: {experiment_id}")
        experiment_ids.add(experiment_id)
        if experiment_id not in experiment_index:
            issues.append(f"{experiment_id} is not synchronized to EXPERIMENT_INDEX")
        if not isinstance(experiment.get("scientific_claim_eligible"), bool):
            issues.append(f"{experiment_id} has no boolean scientific_claim_eligible")
        for path in experiment.get("paths", []):
            _check_repo_path(root, path, experiment_id, issues)

    results = registry.get("results")
    if not isinstance(results, list):
        issues.append("results must be a list")
        results = []

    result_ids: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            issues.append("results contains a non-object entry")
            continue
        result_id = result.get("id")
        if not isinstance(result_id, str) or not result_id:
            issues.append("result entry has no valid id")
            continue
        if result_id in result_ids:
            issues.append(f"duplicate result id: {result_id}")
        result_ids.add(result_id)
        if result_id not in result_index:
            issues.append(f"{result_id} is not synchronized to RESULTS_INDEX")
        experiment_id = result.get("experiment_id")
        if experiment_id not in experiment_ids:
            issues.append(f"{result_id} references unknown experiment id: {experiment_id}")
        if not isinstance(result.get("scientific_claim_eligible"), bool):
            issues.append(f"{result_id} has no boolean scientific_claim_eligible")
        for path in result.get("paths", []):
            _check_repo_path(root, path, result_id, issues)

    current = registry.get("current")
    if not isinstance(current, dict):
        issues.append("current must be an object")
    else:
        active_experiment = current.get("active_experiment_id")
        if active_experiment not in experiment_ids:
            issues.append(f"current.active_experiment_id is unknown: {active_experiment}")
        for path in current.get("gate_paths", []):
            _check_repo_path(root, path, "current.gate_paths", issues)

    return issues
