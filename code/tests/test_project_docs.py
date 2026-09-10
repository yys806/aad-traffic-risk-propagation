import hashlib
import json
import subprocess
from pathlib import Path

from riskprop.project_docs import validate_project_docs


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _experiment() -> dict[str, object]:
    return {
        "id": "stage_0_1",
        "name": "Engineering gate",
        "purpose": "Validate the artifact chain.",
        "research_question": "Can the chain be reproduced?",
        "date": "2026-09-08",
        "status": "verified_engineering_only",
        "code_version": "fixture",
        "code_paths": ["code/src/example.py"],
        "entrypoints": ["code/scripts/example.py"],
        "test_paths": ["code/tests/test_example.py"],
        "configuration": "fixture config",
        "parameters": {"seed": 1},
        "data_version": "fixture-v1",
        "model": "not_applicable",
        "model_checkpoint": "not_applicable",
        "result_ids": ["RES-STAGE-0.1-V1"],
        "core_metrics": ["schema_valid"],
        "current_conclusion": "Engineering-only evidence.",
        "gate": {
            "status": "passed_engineering_only",
            "portable_path": "evidence/results/RES-STAGE-0.1-V1/audit.json",
        },
        "scientific_claim_eligible": False,
    }


def _result() -> dict[str, object]:
    return {
        "id": "RES-STAGE-0.1-V1",
        "experiment_id": "stage_0_1",
        "name": "Fixture result",
        "status": "verified_engineering_only",
        "portable_evidence_paths": ["evidence/results/RES-STAGE-0.1-V1/audit.json"],
        "local_artifact_paths": ["code/outputs/example/audit.json"],
        "code_version_source": "fixture provenance",
        "configuration_source": "fixture config",
        "data_version_source": "fixture data",
        "core_metrics": {"schema_valid": True},
        "current_conclusion": "Engineering-only evidence.",
        "gate_status": "passed_engineering_only",
        "paper_locations": ["docs/RESEARCH_STATUS.md"],
        "scientific_claim_eligible": False,
    }


def _history() -> dict[str, object]:
    return {
        "id": "HIST-PILOT",
        "name": "Pilot",
        "purpose": "Historical feasibility check.",
        "status": "Historical",
        "code_paths": ["code/src/legacy.py"],
        "local_output_paths": ["code/outputs/pilot"],
        "portable_summary_paths": ["docs/HISTORY_INDEX.md"],
        "why_not_current": "Superseded by the formal protocol.",
        "evidence_boundary": "Not eligible for current scientific claims.",
    }


def _valid_repo(tmp_path: Path) -> Path:
    handoff_sections = "\n".join(f"## {number}. Section" for number in range(1, 16))
    learning_topics = "\n".join(
        [
            "研究问题",
            "核心研究思路",
            "算法原理",
            "方法设计",
            "实验逻辑",
            "结果含义",
            "当前问题",
            "后续研究方向",
        ]
    )
    method_topics = "\n".join(
        [
            "解决什么问题",
            "直觉",
            "为什么需要",
            "具体怎么做",
            "数学表示",
            "代码实现",
            "实验影响",
            "变量",
        ]
    )
    files = {
        "README.md": "# Fixture\n",
        "AGENTS.md": "# Rules\n",
        "PROJECT_CONTEXT.md": handoff_sections,
        "docs/PROJECT_INDEX.md": "# Index\n",
        "docs/ARCHITECTURE.md": "# Architecture\n",
        "docs/RESEARCH_STATUS.md": "# Status\n",
        "docs/STAGE_INDEX.md": "# Stages\n\n### stage_0_1 Engineering\n",
        "docs/RESULTS_INDEX.md": "# Results\n\n## RES-STAGE-0.1-V1 Result\n",
        "docs/HISTORY_INDEX.md": "# History\n\n## HIST-PILOT Pilot\n",
        "docs/LEARNING_PATH.md": learning_topics,
        "docs/METHOD_AND_ALGORITHM_GUIDE.md": method_topics,
        "docs/CHANGELOG.md": "# Changes\n",
        "evidence/README.md": "# Evidence\n",
        "code/src/example.py": "",
        "code/src/legacy.py": "",
        "code/scripts/example.py": "",
        "code/tests/test_example.py": "",
    }
    for path, text in files.items():
        _write(tmp_path / path, text)

    evidence_path = tmp_path / "evidence/results/RES-STAGE-0.1-V1/audit.json"
    _write(evidence_path, "{}\n")
    evidence_content = evidence_path.read_bytes()
    evidence_manifest = {
        "schema_version": "aad.evidence-manifest.v1",
        "export_version": "fixture-v1",
        "policy": "small-portable-evidence-only",
        "results": [
            {
                "result_id": "RES-STAGE-0.1-V1",
                "files": [
                    {
                        "source_path": "code/outputs/example/audit.json",
                        "snapshot_path": "evidence/results/RES-STAGE-0.1-V1/audit.json",
                        "size_bytes": len(evidence_content),
                        "sha256": hashlib.sha256(evidence_content).hexdigest(),
                    }
                ],
            }
        ],
    }
    _write(tmp_path / "evidence/EVIDENCE_MANIFEST.json", json.dumps(evidence_manifest))

    canonical_entries = [
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
    ]
    registry = {
        "schema_version": "aad.project-registry.v2",
        "last_verified": "2026-09-08",
        "repository": {
            "branch_policy": "main",
            "state_semantics": "derive_live",
            "document_commit_command": "git log -1 --format=%H -- PROJECT_CONTEXT.md",
            "live_head_command": "git rev-parse HEAD",
            "live_worktree_command": "git status --short",
        },
        "canonical_entries": canonical_entries,
        "current": {
            "active_experiment_id": "stage_0_1",
            "active_task": "Fixture task",
            "portable_gate_paths": ["evidence/results/RES-STAGE-0.1-V1/audit.json"],
            "local_gate_paths": ["code/outputs/example/audit.json"],
        },
        "experiments": [_experiment()],
        "results": [_result()],
        "history": [_history()],
    }
    _write(tmp_path / "docs/PROJECT_REGISTRY.json", json.dumps(registry))
    return tmp_path


def _load_registry(repo: Path) -> dict[str, object]:
    return json.loads((repo / "docs/PROJECT_REGISTRY.json").read_text(encoding="utf-8"))


def _save_registry(repo: Path, registry: dict[str, object]) -> None:
    _write(repo / "docs/PROJECT_REGISTRY.json", json.dumps(registry))


def _git_init_and_add(repo: Path, paths: list[str] | None = None) -> None:
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "--", *(paths or ["."])], check=True)


def test_validate_project_docs_accepts_consistent_registry(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    assert validate_project_docs(repo) == []


def test_validate_project_docs_reports_missing_registered_path(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    (repo / "code/src/example.py").unlink()
    issues = validate_project_docs(repo)
    assert any("code/src/example.py" in issue for issue in issues)


def test_validate_project_docs_reports_unsynchronized_ids(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    _write(repo / "docs/STAGE_INDEX.md", "# Experiments\n")
    _write(repo / "docs/RESULTS_INDEX.md", "# Results\n")
    issues = validate_project_docs(repo)
    assert any("stage_0_1" in issue and "STAGE_INDEX" in issue for issue in issues)
    assert any("RES-STAGE-0.1-V1" in issue and "RESULTS_INDEX" in issue for issue in issues)


def test_validate_project_docs_reports_missing_required_experiment_field(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    registry = _load_registry(repo)
    del registry["experiments"][0]["status"]  # type: ignore[index]
    _save_registry(repo, registry)
    issues = validate_project_docs(repo)
    assert any("stage_0_1" in issue and "missing required field: status" in issue for issue in issues)


def test_validate_project_docs_reports_non_bidirectional_result_links(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    registry = _load_registry(repo)
    registry["experiments"][0]["result_ids"] = []  # type: ignore[index]
    _save_registry(repo, registry)
    issues = validate_project_docs(repo)
    assert any("result_ids do not match reverse result links" in issue for issue in issues)


def test_validate_project_docs_reports_evidence_hash_mismatch(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    _write(repo / "evidence/results/RES-STAGE-0.1-V1/audit.json", "changed\n")
    issues = validate_project_docs(repo)
    assert any("evidence sha256 mismatch" in issue for issue in issues)


def test_validate_project_docs_reports_unregistered_evidence_file(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    _write(repo / "evidence/results/RES-STAGE-0.1-V1/stale.json", "{}\n")
    issues = validate_project_docs(repo)
    assert any("unregistered evidence snapshot" in issue for issue in issues)


def test_validate_project_docs_reports_stale_transient_claim(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    _write(repo / "AGENTS.md", "当前工作树含大量未提交科研实现")
    issues = validate_project_docs(repo)
    assert any("stale transient claim" in issue for issue in issues)


def test_strict_git_reports_untracked_portable_evidence(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    tracked_without_evidence = [
        str(item.relative_to(repo))
        for item in repo.rglob("*")
        if item.is_file()
        and not item.relative_to(repo).as_posix().startswith("evidence/results/")
    ]
    _git_init_and_add(repo, tracked_without_evidence)
    issues = validate_project_docs(repo, strict_git=True)
    assert any("is not Git-tracked" in issue and "audit.json" in issue for issue in issues)


def test_strict_git_accepts_fully_tracked_fixture(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    _git_init_and_add(repo)
    assert validate_project_docs(repo, strict_git=True) == []
