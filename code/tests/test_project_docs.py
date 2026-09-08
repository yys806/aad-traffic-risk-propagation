import json
from pathlib import Path

from riskprop.project_docs import validate_project_docs


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_repo(tmp_path: Path) -> Path:
    for path in [
        "README.md",
        "AGENTS.md",
        "PROJECT_CONTEXT.md",
        "docs/PROJECT_INDEX.md",
        "docs/ARCHITECTURE.md",
        "docs/RESEARCH_STATUS.md",
        "docs/EXPERIMENT_INDEX.md",
        "docs/RESULTS_INDEX.md",
        "docs/CHANGELOG.md",
        "code/src/example.py",
        "code/outputs/example/audit.json",
    ]:
        _write(tmp_path / path)

    _write(
        tmp_path / "docs/EXPERIMENT_INDEX.md",
        "# Experiments\n\n## E00\n",
    )
    _write(
        tmp_path / "docs/RESULTS_INDEX.md",
        "# Results\n\n## RES-E00-V1\n",
    )
    registry = {
        "schema_version": "aad.project-registry.v1",
        "canonical_entries": [
            "README.md",
            "AGENTS.md",
            "PROJECT_CONTEXT.md",
            "docs/PROJECT_INDEX.md",
            "docs/ARCHITECTURE.md",
            "docs/RESEARCH_STATUS.md",
            "docs/EXPERIMENT_INDEX.md",
            "docs/RESULTS_INDEX.md",
            "docs/CHANGELOG.md",
        ],
        "experiments": [
            {
                "id": "E00",
                "status": "verified_engineering_only",
                "scientific_claim_eligible": False,
                "paths": ["code/src/example.py"],
            }
        ],
        "current": {
            "active_experiment_id": "E00",
            "gate_paths": ["code/outputs/example/audit.json"],
        },
        "results": [
            {
                "id": "RES-E00-V1",
                "experiment_id": "E00",
                "scientific_claim_eligible": False,
                "paths": ["code/outputs/example/audit.json"],
            }
        ],
    }
    _write(
        tmp_path / "docs/PROJECT_REGISTRY.json",
        json.dumps(registry),
    )
    return tmp_path


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
    _write(repo / "docs/EXPERIMENT_INDEX.md", "# Experiments\n")
    _write(repo / "docs/RESULTS_INDEX.md", "# Results\n")

    issues = validate_project_docs(repo)

    assert any("E00" in issue and "EXPERIMENT_INDEX" in issue for issue in issues)
    assert any("RES-E00-V1" in issue and "RESULTS_INDEX" in issue for issue in issues)
