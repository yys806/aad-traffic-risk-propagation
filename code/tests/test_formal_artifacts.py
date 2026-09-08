import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from riskprop.formal_artifacts import (
    REQUIRED_RUN_ARTIFACTS,
    TABLE_REQUIRED_COLUMNS,
    FormalArtifactError,
    build_run_manifest,
    collect_run_provenance,
    validate_run_manifest,
    validate_theory_artifact_schema,
)
from riskprop.formal_runner import run_artifact_smoke, run_contract_fixture


def _write_minimal_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_RUN_ARTIFACTS:
        path = run_dir / name
        if path.suffix == ".parquet":
            pd.DataFrame({"artifact": [name]}).to_parquet(path, index=False)
        elif path.suffix == ".json":
            path.write_text(json.dumps({"artifact": name}), encoding="utf-8")
        else:
            path.write_text(f"artifact={name}\n", encoding="utf-8")


def test_manifest_rejects_a_run_missing_a_required_artifact(tmp_path: Path):
    run_dir = tmp_path / "run_missing"
    _write_minimal_run(run_dir)
    (run_dir / "risk.parquet").unlink()

    with pytest.raises(FormalArtifactError, match="risk.parquet"):
        build_run_manifest(run_dir, metadata={"run_id": "run_missing"})


def test_manifest_records_hashes_and_round_trips_all_run_artifacts(tmp_path: Path):
    run_dir = tmp_path / "run_complete"
    _write_minimal_run(run_dir)

    manifest = build_run_manifest(
        run_dir,
        metadata={"run_id": "run_complete", "protocol_version": "e00.test"},
    )

    assert manifest["schema_version"] == "e00.v1"
    assert manifest["metadata"]["run_id"] == "run_complete"
    assert {entry["path"] for entry in manifest["files"]} == set(
        REQUIRED_RUN_ARTIFACTS
    )
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "SHA256SUMS").exists()
    assert validate_run_manifest(run_dir) == manifest


def test_manifest_rejects_an_untracked_extra_file_after_build(tmp_path: Path):
    run_dir = tmp_path / "run_extra"
    _write_minimal_run(run_dir)
    build_run_manifest(run_dir, metadata={"run_id": "run_extra"})
    (run_dir / "untracked_debug_dump.txt").write_text("hidden\n", encoding="utf-8")

    with pytest.raises(FormalArtifactError, match="not listed"):
        validate_run_manifest(run_dir)


def test_provenance_records_commit_environment_command_and_exit_code():
    repo_root = Path(__file__).resolve().parents[2]

    provenance = collect_run_provenance(
        repo_root,
        command=["python", "-m", "riskprop.formal_runner"],
        started_at_utc="2026-08-17T00:00:00Z",
        finished_at_utc="2026-08-17T00:00:01Z",
        exit_code=0,
    )

    assert provenance["schema_version"] == "e00.provenance.v1"
    assert len(provenance["git_commit"]) == 40
    assert isinstance(provenance["git_dirty"], bool)
    assert provenance["command"] == ["python", "-m", "riskprop.formal_runner"]
    assert provenance["exit_code"] == 0
    assert provenance["started_at_utc"] < provenance["finished_at_utc"]
    assert provenance["python_version"].startswith("3.")


def test_manifest_rejects_non_parquet_tabular_artifacts(tmp_path: Path):
    run_dir = tmp_path / "run_invalid_table"
    _write_minimal_run(run_dir)
    (run_dir / "risk.parquet").write_text("not parquet\n", encoding="utf-8")

    with pytest.raises(FormalArtifactError, match="valid Parquet"):
        build_run_manifest(run_dir, metadata={"run_id": "run_invalid_table"})


def test_theory_schema_requires_source_lifecycle_and_attribution_columns(
    tmp_path: Path,
):
    run_dir = tmp_path / "run_schema"
    _write_minimal_run(run_dir)
    for name, columns in TABLE_REQUIRED_COLUMNS.items():
        pd.DataFrame(columns=columns).to_parquet(run_dir / name, index=False)
    protocol = pd.read_parquet(run_dir / "protocol.parquet").drop(
        columns=["source_vehicle_id"]
    )
    protocol.to_parquet(run_dir / "protocol.parquet", index=False)

    with pytest.raises(FormalArtifactError, match="source_vehicle_id"):
        validate_theory_artifact_schema(run_dir)


def test_theory_schema_accepts_all_frozen_columns_even_for_an_empty_channel(
    tmp_path: Path,
):
    run_dir = tmp_path / "run_schema_complete"
    _write_minimal_run(run_dir)
    for name, columns in TABLE_REQUIRED_COLUMNS.items():
        pd.DataFrame(columns=columns).to_parquet(run_dir / name, index=False)

    result = validate_theory_artifact_schema(run_dir)

    assert result == {name: 0 for name in TABLE_REQUIRED_COLUMNS}


def test_e00_artifact_smoke_writes_a_sealed_theory_aligned_run(tmp_path: Path):
    run_dir = run_artifact_smoke(
        tmp_path,
        run_id="e00_smoke_001",
        repo_root=Path(__file__).resolve().parents[2],
    )

    config = json.loads((run_dir / "config_frozen.json").read_text(encoding="utf-8"))
    assert config["experiment_id"] == "E00"
    assert config["smoke_only"] is True
    assert validate_run_manifest(run_dir)["metadata"]["run_id"] == "e00_smoke_001"
    assert validate_theory_artifact_schema(run_dir) == {
        name: 0 for name in TABLE_REQUIRED_COLUMNS
    }


def test_e00_artifact_smoke_cli_is_a_one_command_reproducibility_entrypoint(
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        str(repo_root / "code" / "scripts" / "run_e00_artifact_smoke.py"),
        "--output-root",
        str(tmp_path),
        "--run-id",
        "e00_cli_smoke",
        "--repo-root",
        str(repo_root),
    ]
    process = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert (tmp_path / "e00_cli_smoke" / "manifest.json").exists()
    provenance = json.loads(
        (tmp_path / "e00_cli_smoke" / "provenance.json").read_text(
            encoding="utf-8"
        )
    )
    assert provenance["command"] == command


def test_e00_cli_records_a_failed_rerun_without_overwriting_the_first_run(
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        str(repo_root / "code" / "scripts" / "run_e00_artifact_smoke.py"),
        "--output-root",
        str(tmp_path),
        "--run-id",
        "immutable_run",
        "--repo-root",
        str(repo_root),
    ]
    first = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    manifest_before = (tmp_path / "immutable_run" / "manifest.json").read_bytes()

    second = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode != 0
    assert (tmp_path / "immutable_run" / "manifest.json").read_bytes() == manifest_before
    ledger = [
        json.loads(line)
        for line in (tmp_path / "failure_ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert ledger[-1]["run_id"] == "immutable_run"
    assert ledger[-1]["exception_type"] == "FormalArtifactError"
    assert ledger[-1]["exit_code"] != 0


def test_e00_contract_fixture_writes_four_nonempty_theory_audited_runs(
    tmp_path: Path,
):
    fixture_dir = run_contract_fixture(
        tmp_path,
        fixture_id="custom_fixture_001",
        repo_root=Path(__file__).resolve().parents[2],
    )

    report = json.loads(
        (fixture_dir / "fixture_report.json").read_text(encoding="utf-8")
    )
    assert report["scientific_claim_eligible"] is False
    assert report["four_cell_audit"]["cell_ids"] == [
        "s0c0",
        "s0c1",
        "s1c0",
        "s1c1",
    ]
    assert report["pre_treatment_audit"]["equivalence_pass"] is True
    assert report["state_isolation_audit"]["isolation_pass"] is True
    assert report["time_alignment_audit"]["time_alignment_pass"] is True
    assert report["vehicle_lifecycle_audit"]["vehicle_lifecycle_pass"] is True
    assert report["s1c1_protocol_audit"]["adopted_count"] == 1

    for cell_id in ("s0c0", "s0c1", "s1c0", "s1c1"):
        run_dir = fixture_dir / cell_id
        manifest = validate_run_manifest(run_dir)
        rows = validate_theory_artifact_schema(run_dir)
        assert manifest["metadata"]["scientific_claim_eligible"] is False
        assert rows["state.parquet"] > 0
        assert rows["emission.parquet"] > 0
        assert rows["protocol.parquet"] > 0
        assert rows["action.parquet"] > 0
        assert rows["risk.parquet"] > 0
        expected_run_id = f"custom_fixture_001_{cell_id}"
        for table_name in TABLE_REQUIRED_COLUMNS:
            table = pd.read_parquet(run_dir / table_name)
            assert set(table["run_id"]) == {expected_run_id}


def test_e00_contract_fixture_cli_is_a_one_command_nonempty_contract_entrypoint(
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        [
            sys.executable,
            str(repo_root / "code" / "scripts" / "run_e00_contract_fixture.py"),
            "--output-root",
            str(tmp_path),
            "--fixture-id",
            "cli_fixture_001",
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert process.returncode == 0, process.stderr
    fixture_dir = tmp_path / "cli_fixture_001"
    assert (fixture_dir / "fixture_report.json").exists()
    provenance = json.loads(
        (fixture_dir / "s0c0" / "provenance.json").read_text(encoding="utf-8")
    )
    assert provenance["command"] == [
        sys.executable,
        str(repo_root / "code" / "scripts" / "run_e00_contract_fixture.py"),
        "--output-root",
        str(tmp_path),
        "--fixture-id",
        "cli_fixture_001",
        "--repo-root",
        str(repo_root),
    ]
