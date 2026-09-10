"""Validation helpers for the AAD long-term research knowledge system."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


EXPECTED_SCHEMA = "aad.project-registry.v2"
EXPECTED_EVIDENCE_SCHEMA = "aad.evidence-manifest.v1"

REQUIRED_ENTRY_PATHS = (
    "README.md",
    "AGENTS.md",
    "PROJECT_CONTEXT.md",
    "docs/PROJECT_INDEX.md",
    "docs/PROJECT_REGISTRY.json",
    "docs/ARCHITECTURE.md",
    "docs/RESEARCH_STATUS.md",
    "docs/STAGE_INDEX.md",
    "docs/RESULTS_INDEX.md",
    "docs/HISTORY_INDEX.md",
    "docs/LEARNING_PATH.md",
    "docs/METHOD_AND_ALGORITHM_GUIDE.md",
    "docs/CHANGELOG.md",
    "evidence/README.md",
    "evidence/EVIDENCE_MANIFEST.json",
)

REQUIRED_EXPERIMENT_FIELDS = (
    "id",
    "name",
    "purpose",
    "research_question",
    "date",
    "status",
    "code_version",
    "code_paths",
    "entrypoints",
    "test_paths",
    "configuration",
    "parameters",
    "data_version",
    "model",
    "model_checkpoint",
    "result_ids",
    "core_metrics",
    "current_conclusion",
    "gate",
    "scientific_claim_eligible",
)

REQUIRED_RESULT_FIELDS = (
    "id",
    "experiment_id",
    "name",
    "status",
    "portable_evidence_paths",
    "local_artifact_paths",
    "code_version_source",
    "configuration_source",
    "data_version_source",
    "core_metrics",
    "current_conclusion",
    "gate_status",
    "paper_locations",
    "scientific_claim_eligible",
)

REQUIRED_HISTORY_FIELDS = (
    "id",
    "name",
    "purpose",
    "status",
    "code_paths",
    "local_output_paths",
    "portable_summary_paths",
    "why_not_current",
    "evidence_boundary",
)

REQUIRED_HANDOFF_SECTIONS = tuple(f"## {number}." for number in range(1, 16))
REQUIRED_LEARNING_TOPICS = (
    "研究问题",
    "核心研究思路",
    "算法原理",
    "方法设计",
    "实验逻辑",
    "结果含义",
    "当前问题",
    "后续研究方向",
)
REQUIRED_METHOD_TOPICS = (
    "解决什么问题",
    "直觉",
    "为什么需要",
    "具体怎么做",
    "数学表示",
    "代码实现",
    "实验影响",
    "变量",
)
FORBIDDEN_TRANSIENT_CLAIMS = (
    "当前工作树含大量未提交",
    "工作树存在大量已跟踪修改",
    "目前是未跟踪文件",
    "多数仍是未跟踪",
    "current dirty worktree",
)


def _load_json(path: Path, label: str, issues: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        issues.append(f"missing {label}: {path.as_posix()}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(f"invalid {label}: {exc}")
        return None
    if not isinstance(data, dict):
        issues.append(f"{label} root must be a JSON object")
        return None
    return data


def _read_text(path: Path, label: str, issues: list[str]) -> str:
    if not path.is_file():
        issues.append(f"missing {label}: {path.as_posix()}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issues.append(f"cannot read {label}: {exc}")
        return ""


def _tracked_paths(repo_root: Path, issues: list[str]) -> set[str] | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        issues.append(f"strict git validation unavailable: {detail or 'git ls-files failed'}")
        return None
    return {
        item.replace("\\", "/")
        for item in result.stdout.decode("utf-8", errors="strict").split("\0")
        if item
    }


def _check_repo_path(
    repo_root: Path,
    raw_path: object,
    context: str,
    issues: list[str],
    *,
    tracked: set[str] | None = None,
    require_tracked: bool = False,
    require_exists: bool = True,
) -> str | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(f"{context} contains an invalid path")
        return None
    normalized = raw_path.replace("\\", "/")
    path = Path(normalized)
    if path.is_absolute():
        issues.append(f"{context} must use a repository-relative path: {raw_path}")
        return None
    candidate = (repo_root / path).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        issues.append(f"{context} escapes the repository: {raw_path}")
        return None
    if require_exists and not candidate.exists():
        issues.append(f"{context} references missing path: {raw_path}")
    if require_tracked and tracked is not None and normalized not in tracked:
        issues.append(f"{context} is not Git-tracked: {raw_path}")
    return normalized


def _check_path_list(
    repo_root: Path,
    value: object,
    context: str,
    issues: list[str],
    *,
    tracked: set[str] | None = None,
    require_tracked: bool = False,
    require_exists: bool = True,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "possibly empty " if allow_empty else "non-empty "
        issues.append(f"{context} must be a {qualifier}list")
        return []
    checked: list[str] = []
    for raw_path in value:
        normalized = _check_repo_path(
            repo_root,
            raw_path,
            context,
            issues,
            tracked=tracked,
            require_tracked=require_tracked,
            require_exists=require_exists,
        )
        if normalized is not None:
            checked.append(normalized)
    return checked


def _check_required_fields(
    entry: dict[str, Any], required: Iterable[str], context: str, issues: list[str]
) -> None:
    for field in required:
        if field not in entry:
            issues.append(f"{context} missing required field: {field}")


def _has_heading(text: str, identifier: str) -> bool:
    pattern = rf"^##{{1,3}}\s+{re.escape(identifier)}(?:\s|$)"
    return re.search(pattern, text, flags=re.MULTILINE) is not None


def _check_required_topics(
    text: str, topics: Iterable[str], context: str, issues: list[str]
) -> None:
    for topic in topics:
        if topic not in text:
            issues.append(f"{context} is missing required topic: {topic}")


def _validate_evidence_manifest(
    repo_root: Path,
    result_ids: set[str],
    result_portable_paths: dict[str, set[str]],
    issues: list[str],
    *,
    tracked: set[str] | None,
    strict_git: bool,
) -> None:
    manifest = _load_json(
        repo_root / "evidence/EVIDENCE_MANIFEST.json", "evidence manifest", issues
    )
    if manifest is None:
        return
    if manifest.get("schema_version") != EXPECTED_EVIDENCE_SCHEMA:
        issues.append(
            f"unexpected evidence manifest schema: {manifest.get('schema_version')!r}; "
            f"expected {EXPECTED_EVIDENCE_SCHEMA!r}"
        )
    entries = manifest.get("results")
    if not isinstance(entries, list):
        issues.append("evidence manifest results must be a list")
        return
    manifest_ids: set[str] = set()
    manifest_paths: dict[str, set[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            issues.append("evidence manifest contains a non-object result entry")
            continue
        result_id = entry.get("result_id")
        if not isinstance(result_id, str) or not result_id:
            issues.append("evidence manifest result entry has no valid result_id")
            continue
        if result_id in manifest_ids:
            issues.append(f"duplicate evidence result_id: {result_id}")
        manifest_ids.add(result_id)
        files = entry.get("files")
        if not isinstance(files, list) or not files:
            issues.append(f"{result_id} evidence files must be a non-empty list")
            continue
        seen: set[str] = set()
        for file_entry in files:
            if not isinstance(file_entry, dict):
                issues.append(f"{result_id} evidence contains a non-object file entry")
                continue
            _check_required_fields(
                file_entry,
                ("source_path", "snapshot_path", "size_bytes", "sha256"),
                f"{result_id} evidence file",
                issues,
            )
            snapshot_path = _check_repo_path(
                repo_root,
                file_entry.get("snapshot_path"),
                f"{result_id}.snapshot_path",
                issues,
                tracked=tracked,
                require_tracked=strict_git,
            )
            if snapshot_path is None:
                continue
            if snapshot_path in seen:
                issues.append(f"{result_id} repeats snapshot path: {snapshot_path}")
            seen.add(snapshot_path)
            candidate = repo_root / snapshot_path
            if not candidate.is_file():
                continue
            content = candidate.read_bytes()
            if file_entry.get("size_bytes") != len(content):
                issues.append(f"{result_id} evidence size mismatch: {snapshot_path}")
            if file_entry.get("sha256") != hashlib.sha256(content).hexdigest():
                issues.append(f"{result_id} evidence sha256 mismatch: {snapshot_path}")
            if "sealed_sampling_key" in snapshot_path.lower():
                issues.append(f"{result_id} includes forbidden sealed sampling key")
        manifest_paths[result_id] = seen

    if manifest_ids != result_ids:
        missing = sorted(result_ids - manifest_ids)
        extra = sorted(manifest_ids - result_ids)
        if missing:
            issues.append(f"evidence manifest is missing result ids: {', '.join(missing)}")
        if extra:
            issues.append(f"evidence manifest has unknown result ids: {', '.join(extra)}")
    for result_id, portable_paths in result_portable_paths.items():
        if not portable_paths.issubset(manifest_paths.get(result_id, set())):
            issues.append(
                f"{result_id} portable_evidence_paths are not fully declared in evidence manifest"
            )

    declared_snapshots = set().union(*manifest_paths.values()) if manifest_paths else set()
    evidence_results_root = repo_root / "evidence/results"
    if evidence_results_root.is_dir():
        actual_snapshots = {
            path.relative_to(repo_root).as_posix()
            for path in evidence_results_root.rglob("*")
            if path.is_file()
        }
        for unexpected in sorted(actual_snapshots - declared_snapshots):
            issues.append(f"unregistered evidence snapshot: {unexpected}")


def validate_project_docs(
    repo_root: str | Path,
    *,
    strict_git: bool = False,
    require_clean: bool = False,
) -> list[str]:
    """Return consistency and portability issues for the project knowledge system."""

    root = Path(repo_root).resolve()
    issues: list[str] = []
    tracked = _tracked_paths(root, issues) if strict_git else None
    registry = _load_json(root / "docs/PROJECT_REGISTRY.json", "project registry", issues)
    if registry is None:
        return issues
    if registry.get("schema_version") != EXPECTED_SCHEMA:
        issues.append(
            f"unexpected registry schema: {registry.get('schema_version')!r}; "
            f"expected {EXPECTED_SCHEMA!r}"
        )

    repository = registry.get("repository")
    if not isinstance(repository, dict):
        issues.append("repository must be an object")
    else:
        if repository.get("state_semantics") != "derive_live":
            issues.append("repository.state_semantics must be 'derive_live'")
        for forbidden_field in ("head", "worktree"):
            if forbidden_field in repository:
                issues.append(f"repository must not persist transient field: {forbidden_field}")

    canonical_entries = registry.get("canonical_entries")
    if not isinstance(canonical_entries, list):
        issues.append("canonical_entries must be a list")
        canonical_entries = []
    for required in REQUIRED_ENTRY_PATHS:
        if required not in canonical_entries:
            issues.append(f"canonical_entries is missing required entry: {required}")
    for path in canonical_entries:
        _check_repo_path(
            root,
            path,
            "canonical_entries",
            issues,
            tracked=tracked,
            require_tracked=strict_git,
        )

    experiment_index = _read_text(root / "docs/STAGE_INDEX.md", "STAGE_INDEX", issues)
    result_index = _read_text(root / "docs/RESULTS_INDEX.md", "RESULTS_INDEX", issues)
    history_index = _read_text(root / "docs/HISTORY_INDEX.md", "HISTORY_INDEX", issues)
    handoff = _read_text(root / "PROJECT_CONTEXT.md", "PROJECT_CONTEXT", issues)
    agents = _read_text(root / "AGENTS.md", "AGENTS", issues)
    learning = _read_text(root / "docs/LEARNING_PATH.md", "LEARNING_PATH", issues)
    method_guide = _read_text(
        root / "docs/METHOD_AND_ALGORITHM_GUIDE.md", "METHOD_AND_ALGORITHM_GUIDE", issues
    )
    _check_required_topics(handoff, REQUIRED_HANDOFF_SECTIONS, "PROJECT_CONTEXT", issues)
    _check_required_topics(learning, REQUIRED_LEARNING_TOPICS, "LEARNING_PATH", issues)
    _check_required_topics(method_guide, REQUIRED_METHOD_TOPICS, "METHOD_AND_ALGORITHM_GUIDE", issues)
    for phrase in FORBIDDEN_TRANSIENT_CLAIMS:
        if phrase.lower() in handoff.lower() or phrase.lower() in agents.lower():
            issues.append(f"current governance contains stale transient claim: {phrase}")

    experiments = registry.get("experiments")
    if not isinstance(experiments, list):
        issues.append("experiments must be a list")
        experiments = []
    experiment_ids: set[str] = set()
    experiment_result_ids: dict[str, set[str]] = {}
    for experiment in experiments:
        if not isinstance(experiment, dict):
            issues.append("experiments contains a non-object entry")
            continue
        experiment_id = experiment.get("id")
        context = experiment_id if isinstance(experiment_id, str) and experiment_id else "experiment"
        _check_required_fields(experiment, REQUIRED_EXPERIMENT_FIELDS, context, issues)
        if not isinstance(experiment_id, str) or not experiment_id:
            issues.append("experiment entry has no valid id")
            continue
        if experiment_id in experiment_ids:
            issues.append(f"duplicate experiment id: {experiment_id}")
        experiment_ids.add(experiment_id)
        if not _has_heading(experiment_index, experiment_id):
            issues.append(f"{experiment_id} is not synchronized to STAGE_INDEX")
        allow_empty_paths = experiment.get("status") in {
            "agreed_pending_blocked",
            "not_started",
        }
        for field in ("code_paths", "entrypoints", "test_paths"):
            _check_path_list(
                root,
                experiment.get(field),
                f"{experiment_id}.{field}",
                issues,
                allow_empty=allow_empty_paths,
            )
        result_ids = experiment.get("result_ids")
        if not isinstance(result_ids, list):
            issues.append(f"{experiment_id}.result_ids must be a list")
            result_ids = []
        experiment_result_ids[experiment_id] = {
            item for item in result_ids if isinstance(item, str) and item
        }
        if not isinstance(experiment.get("core_metrics"), list):
            issues.append(f"{experiment_id}.core_metrics must be a list")
        if not isinstance(experiment.get("parameters"), dict):
            issues.append(f"{experiment_id}.parameters must be an object")
        if not isinstance(experiment.get("scientific_claim_eligible"), bool):
            issues.append(f"{experiment_id} has no boolean scientific_claim_eligible")
        gate = experiment.get("gate")
        if not isinstance(gate, dict) or "status" not in gate:
            issues.append(f"{experiment_id}.gate must contain status")
        elif gate.get("portable_path"):
            _check_repo_path(
                root,
                gate.get("portable_path"),
                f"{experiment_id}.gate.portable_path",
                issues,
                tracked=tracked,
                require_tracked=strict_git,
            )

    results = registry.get("results")
    if not isinstance(results, list):
        issues.append("results must be a list")
        results = []
    result_ids: set[str] = set()
    result_to_experiment: dict[str, str] = {}
    result_portable_paths: dict[str, set[str]] = {}
    for result in results:
        if not isinstance(result, dict):
            issues.append("results contains a non-object entry")
            continue
        result_id = result.get("id")
        context = result_id if isinstance(result_id, str) and result_id else "result"
        _check_required_fields(result, REQUIRED_RESULT_FIELDS, context, issues)
        if not isinstance(result_id, str) or not result_id:
            issues.append("result entry has no valid id")
            continue
        if result_id in result_ids:
            issues.append(f"duplicate result id: {result_id}")
        result_ids.add(result_id)
        if not _has_heading(result_index, result_id):
            issues.append(f"{result_id} is not synchronized to RESULTS_INDEX")
        experiment_id = result.get("experiment_id")
        if experiment_id not in experiment_ids:
            issues.append(f"{result_id} references unknown experiment id: {experiment_id}")
        elif isinstance(experiment_id, str):
            result_to_experiment[result_id] = experiment_id
        portable = _check_path_list(
            root,
            result.get("portable_evidence_paths"),
            f"{result_id}.portable_evidence_paths",
            issues,
            tracked=tracked,
            require_tracked=strict_git,
        )
        result_portable_paths[result_id] = set(portable)
        _check_path_list(
            root,
            result.get("local_artifact_paths"),
            f"{result_id}.local_artifact_paths",
            issues,
            require_exists=False,
        )
        _check_path_list(
            root,
            result.get("paper_locations"),
            f"{result_id}.paper_locations",
            issues,
            tracked=tracked,
            require_tracked=strict_git,
        )
        if not isinstance(result.get("core_metrics"), dict):
            issues.append(f"{result_id}.core_metrics must be an object")
        if not isinstance(result.get("scientific_claim_eligible"), bool):
            issues.append(f"{result_id} has no boolean scientific_claim_eligible")

    for experiment_id, declared_results in experiment_result_ids.items():
        actual_results = {
            result_id for result_id, owner in result_to_experiment.items() if owner == experiment_id
        }
        if declared_results != actual_results:
            issues.append(
                f"{experiment_id} result_ids do not match reverse result links: "
                f"declared={sorted(declared_results)}, actual={sorted(actual_results)}"
            )

    history = registry.get("history")
    if not isinstance(history, list):
        issues.append("history must be a list")
        history = []
    history_ids: set[str] = set()
    for item in history:
        if not isinstance(item, dict):
            issues.append("history contains a non-object entry")
            continue
        history_id = item.get("id")
        context = history_id if isinstance(history_id, str) and history_id else "history"
        _check_required_fields(item, REQUIRED_HISTORY_FIELDS, context, issues)
        if not isinstance(history_id, str) or not history_id:
            issues.append("history entry has no valid id")
            continue
        if history_id in history_ids:
            issues.append(f"duplicate history id: {history_id}")
        history_ids.add(history_id)
        if not _has_heading(history_index, history_id):
            issues.append(f"{history_id} is not synchronized to HISTORY_INDEX")
        _check_path_list(root, item.get("code_paths"), f"{history_id}.code_paths", issues)
        _check_path_list(
            root,
            item.get("local_output_paths"),
            f"{history_id}.local_output_paths",
            issues,
            require_exists=False,
        )
        _check_path_list(
            root,
            item.get("portable_summary_paths"),
            f"{history_id}.portable_summary_paths",
            issues,
            tracked=tracked,
            require_tracked=strict_git,
        )

    current = registry.get("current")
    if not isinstance(current, dict):
        issues.append("current must be an object")
    else:
        active_experiment = current.get("active_experiment_id")
        if active_experiment not in experiment_ids:
            issues.append(f"current.active_experiment_id is unknown: {active_experiment}")
        _check_path_list(
            root,
            current.get("portable_gate_paths"),
            "current.portable_gate_paths",
            issues,
            tracked=tracked,
            require_tracked=strict_git,
        )
        _check_path_list(
            root,
            current.get("local_gate_paths"),
            "current.local_gate_paths",
            issues,
            require_exists=False,
        )

    _validate_evidence_manifest(
        root,
        result_ids,
        result_portable_paths,
        issues,
        tracked=tracked,
        strict_git=strict_git,
    )

    if require_clean:
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
            encoding="utf-8",
        )
        if status.returncode != 0:
            issues.append("cannot inspect Git worktree for cleanliness")
        elif status.stdout.strip():
            issues.append("Git worktree is not clean")

    return issues
