"""Synthetic ledger transactions only. Never imports a simulator."""
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import stage_0_5_research_ledger as m


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def capsule(tmp_path):
    config = json.loads((Path(__file__).parents[1] / "configs/stage_0_5_interaction_research_v2.json").read_text(encoding="utf-8"))
    config.update(ledger_path="journal/events.jsonl", output_root="outputs", historical_references=[])
    write(tmp_path / "budget.json", config)
    ledger = m.ResearchLedger(tmp_path, "budget.json")
    ledger.initialize()
    (tmp_path / "plan.md").write_text("synthetic approved plan")
    (tmp_path / "source.py").write_text("# synthetic executable binding")
    (tmp_path / "input.xml").write_text("<synthetic/>")
    write(tmp_path / "isolation.json", {"task_id": m.TASK, "input_and_test_resource_scope_accepted": True})
    return tmp_path, ledger


def proposal(capsule, run_id="R1", seed=1, **change):
    root, ledger = capsule
    run = dict(id=run_id, seed=seed, question="synthetic question", contrast="paired B00", condition="0750",
               factors={"supply": False, "ramp": False}, initialization_policy="synthetic",
               input_sha256={"input.xml": m.digest(root / "input.xml")}, artifact_path="outputs/" + run_id)
    run.update(change)
    p = dict(task_id=m.TASK, execution_allowed=True, researcher_confirmed=True,
             budget_sha256=m.digest(root / "budget.json"), plan_version="synthetic-v1", plan_path="plan.md",
             plan_sha256=m.digest(root / "plan.md"), git_commit="a" * 40, worktree_sha256="b" * 64,
             environment={"python": sys.version}, source_sha256={"source.py": m.digest(root / "source.py")},
             admission=dict(initialization_policy_approved=True, measurement_contract_approved=True, input_fidelity_approved=True),
             isolation=dict(accepted_for_new_task=True, report_path="isolation.json", report_sha256=m.digest(root / "isolation.json")), runs=[run])
    write(root / "proposal.json", p)
    approval = dict(task_id=m.TASK, researcher_confirmed=True, proposal_sha256=m.digest(root / "proposal.json"), decision_record="synthetic test decision")
    return p, approval


def sample():
    return dict(free_c_bytes=6 * 1024**3, free_d_bytes=15 * 1024**3, available_memory_bytes=5 * 1024**3,
                task_output_bytes=0, wall_s=0, process_tree_rss_bytes=0)


def reserve(capsule, run_id="R1", seed=1, **change):
    _, ledger = capsule
    _, approval = proposal(capsule, run_id, seed, **change)
    ledger.reserve("proposal.json", approval, run_id, sample())


def finish(ledger, run_id, status="completed"):
    ledger.transition(run_id, "running")
    ledger.transition(run_id, status, reason="synthetic failure" if status != "completed" else None,
                      resources=dict(wall_s=1, process_tree_rss_bytes=100, artifact_bytes=10))


def accept(capsule, run_id):
    root, ledger = capsule
    artifact = root / "outputs" / run_id / "summary.json"
    write(artifact, {"synthetic": True})
    ledger.transition(run_id, "measurement_accepted", checks=dict.fromkeys(m.CHECKS, True),
                      artifact_sha256={artifact.relative_to(root).as_posix(): m.digest(artifact)})


def test_more_than_three_attempts_and_append_only_prefix(capsule):
    _, ledger = capsule
    prefix = ledger.path.read_bytes()
    for n in range(1, 7):
        reserve(capsule, f"R{n}", seed=n)
        finish(ledger, f"R{n}")
        accept(capsule, f"R{n}")
        assert ledger.path.read_bytes().startswith(prefix)
        prefix = ledger.path.read_bytes()
    state = ledger.snapshot()
    assert state["attempt_count"] == 6 and state["maximum_new_trajectory_attempts"] is None
    assert all(a["started_utc"] and a["resources"] for a in state["attempts"].values())


def test_failure_retained_review_then_explicit_new_retry(capsule):
    _, ledger = capsule
    reserve(capsule)
    finish(ledger, "R1", "failed")
    with pytest.raises(ValueError, match="failure_requires_explicit_review"):
        reserve(capsule, "R2", seed=2)
    ledger.review_failure("R1", dict(researcher_confirmed=True, task_id=m.TASK, run_id="R1", decision_record="synthetic correction reviewed"))
    with pytest.raises(ValueError, match="duplicate_configuration_requires_reason"):
        reserve(capsule, "R2")
    reserve(capsule, "R2", replicate_of="R1", repeat_reason="synthetic corrected validity defect")
    assert ledger.snapshot()["attempts"]["R1"]["status"] == "failed"
    assert ledger.snapshot()["attempt_count"] == 2


@pytest.mark.parametrize("status", ["reserved", "running", "completed"])
def test_unreviewed_attempt_blocks_next(capsule, status):
    _, ledger = capsule
    reserve(capsule)
    if status in {"running", "completed"}:
        ledger.transition("R1", "running")
    if status == "completed":
        ledger.transition("R1", "completed", resources=dict(wall_s=1, process_tree_rss_bytes=1, artifact_bytes=1))
    with pytest.raises(ValueError, match="previous_attempt_unreviewed_or_active"):
        reserve(capsule, "R2", seed=2)


def test_rejected_measurement_does_not_relabel_as_success(capsule):
    _, ledger = capsule
    reserve(capsule); finish(ledger, "R1")
    checks = dict.fromkeys(m.CHECKS, True); checks["all18_common_cells"] = False
    with pytest.raises(ValueError, match="measurement_acceptance_failed"):
        ledger.transition("R1", "measurement_accepted", checks=checks, artifact_sha256={"x": "a" * 64})
    ledger.transition("R1", "measurement_rejected", checks=checks, reason="missing cell")
    with pytest.raises(ValueError, match="invalid_transition"):
        ledger.transition("R1", "running")


@pytest.mark.parametrize("mutation", ["unconfirmed", "proposal_drift", "source_drift", "isolation", "input_scope"])
def test_admission_fails_before_attempt(capsule, mutation):
    root, ledger = capsule
    p, approval = proposal(capsule)
    if mutation == "unconfirmed": approval["researcher_confirmed"] = False
    if mutation == "proposal_drift": (root / "proposal.json").write_text("{}")
    if mutation == "source_drift": (root / "source.py").write_text("changed")
    if mutation == "isolation":
        p["isolation"]["accepted_for_new_task"] = False; write(root / "proposal.json", p)
        approval["proposal_sha256"] = m.digest(root / "proposal.json")
    if mutation == "input_scope":
        p["runs"][0]["input_sha256"] = {"../outside": "a" * 64}; write(root / "proposal.json", p)
        approval["proposal_sha256"] = m.digest(root / "proposal.json")
    with pytest.raises((ValueError, FileNotFoundError)):
        ledger.reserve("proposal.json", approval, "R1", sample())
    assert ledger.snapshot()["attempt_count"] == 0


def test_no_reset_duplicate_id_lock_and_partial_journal(capsule):
    _, ledger = capsule
    with pytest.raises(ValueError, match="ledger_exists_no_reset"): ledger.initialize()
    with ledger.lock():
        with pytest.raises(FileExistsError): reserve(capsule)
    reserve(capsule)
    with pytest.raises(ValueError, match="duplicate_run_id"): reserve(capsule)
    with ledger.path.open("ab") as stream: stream.write(b'{"partial":')
    with pytest.raises(ValueError, match="incomplete_journal"): ledger.snapshot()


def test_journal_and_budget_drift_fail_closed(capsule):
    root, ledger = capsule
    raw = ledger.path.read_bytes()
    ledger.path.write_bytes(raw.replace(b'"execution_allowed":false', b'"execution_allowed":true'))
    with pytest.raises(ValueError, match="journal_digest"): ledger.snapshot()
    ledger.path.write_bytes(raw)
    (root / "budget.json").write_text((root / "budget.json").read_text() + " ")
    with pytest.raises(ValueError, match="budget_binding_changed"): ledger.snapshot()


@pytest.mark.parametrize("field,value", [("free_c_bytes", 0), ("free_d_bytes", 0), ("available_memory_bytes", 0),
                                         ("wall_s", 601), ("process_tree_rss_bytes", 4 * 1024**3), ("task_output_bytes", 3 * 1024**3)])
def test_single_attempt_limits_retained(capsule, field, value):
    _, ledger = capsule
    _, approval = proposal(capsule); s = sample(); s[field] = value
    with pytest.raises(ValueError, match="resource_preflight_failed"):
        ledger.reserve("proposal.json", approval, "R1", s)
    assert ledger.snapshot()["attempt_count"] == 0


def test_current_repository_candidate_cannot_be_admitted():
    root = Path(__file__).resolve().parents[2]
    ledger = m.ResearchLedger(root, "code/configs/stage_0_5_interaction_research_v2.json")
    assert ledger.snapshot()["attempt_count"] == 0
    with pytest.raises(ValueError, match="exact_researcher_confirmation_required"):
        ledger.reserve("docs/audits/stage_0_5_interaction_research_v2/review_proposal.json", {}, "R2_0750_B00_s20261201", sample())


def test_measurement_cannot_accept_unknown_resources(capsule):
    root, ledger = capsule
    reserve(capsule); ledger.transition("R1", "running")
    ledger.transition("R1", "completed", resources=dict(wall_s=1, process_tree_rss_bytes=None, artifact_bytes=0))
    artifact = root / "outputs/R1/summary.json"; write(artifact, {})
    with pytest.raises(ValueError, match="resource_observation_missing"):
        accept(capsule, "R1")


def test_artifact_hash_drift_is_not_measurement_acceptance(capsule):
    root, ledger = capsule
    reserve(capsule); finish(ledger, "R1")
    artifact = root / "outputs/R1/summary.json"; write(artifact, {})
    with pytest.raises(ValueError, match="artifact_binding_changed"):
        ledger.transition("R1", "measurement_accepted", checks=dict.fromkeys(m.CHECKS, True),
                          artifact_sha256={"outputs/R1/summary.json": "a" * 64})


@pytest.mark.parametrize("marker", ["locked_holdout", "us101__0820_0835"])
def test_unapproved_validation_inputs_refused(capsule, marker):
    root, ledger = capsule
    path = root / marker / "synthetic.xml"; path.parent.mkdir(); path.write_text("synthetic only")
    _, approval = proposal(capsule, input_sha256={path.relative_to(root).as_posix(): m.digest(path)})
    with pytest.raises(ValueError, match="validation_input_forbidden"):
        ledger.reserve("proposal.json", approval, "R1", sample())


def test_export_scoped_and_manifest_history_preserved(tmp_path):
    import export_stage_0_5_research_v2_evidence as export
    local = tmp_path / export.LOCAL; local.mkdir(parents=True)
    for name in export.NAMES[:-1]: (local / name).write_text('{}\n')
    old = {"result_id": "HISTORY", "files": [{"source_path": "must-not-read"}]}
    write(tmp_path / "evidence/EVIDENCE_MANIFEST.json", {"results": [old]})
    result = export.export(tmp_path)
    assert result["results"][0] == old
    assert export.exporter.verify_evidence(tmp_path, {export.RESULT}) == []


def test_validation_entry_refuses_its_source_workspace():
    import subprocess
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "validate_stage_0_5_research_v2.py"),
                             "--source-workspace", str(root)], capture_output=True, text=True)
    assert result.returncode != 0 and "Refused" in result.stderr


def test_matrix_has_paired_four_cells_without_execution_authorization():
    root = Path(__file__).resolve().parents[2]
    matrix = json.loads((root / "docs/audits/stage_0_5_interaction_research_v2/run_matrix.json").read_text(encoding="utf-8"))
    assert matrix["execution_allowed"] is False and matrix["maximum_new_trajectory_attempts"] is None
    assert matrix["initial_block_candidate_count"] == 8
    for window in {r["condition"] for r in matrix["runs"]}:
        rows = [r for r in matrix["runs"] if r["condition"] == window]
        assert {r["arm"] for r in rows} == {"B00", "S10", "R01", "SR11"}
        assert len({r["seed"] for r in rows}) == 1 and len({r["initialization_policy"] for r in rows}) == 1
        assert {tuple(r["factors"].values()) for r in rows} == {(False, False), (True, False), (False, True), (True, True)}
