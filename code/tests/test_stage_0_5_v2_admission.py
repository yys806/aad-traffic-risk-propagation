"""Synthetic evidence and replay only. No simulator import/start/probe."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import stage_0_5_identity_observation as identity
import stage_0_5_input_fidelity as inputs
import stage_0_5_isolation_v2 as isolation
import stage_0_5_execution_v2 as execution
import stage_0_5_research_ledger as ledger_module
from review_stage_0_5_c6_admission_v1 import CORE, validate_allowlist, validate_output


def frame(t, **values):
    x = dict(time_s=t, phase="initial_snapshot" if t == 0 else "after_simulationStep",
             loaded=[], departed=[], arrived=[], pending=[], active=[], teleport_start=[], teleport_end=[],
             discarded=None, native_departures={})
    x.update(values)
    return x


def observer():
    return identity.IdentityObserver([dict(id="i1", depart_s=0), dict(id="m1", depart_s=0.1)])


def test_no_frames_cannot_establish_complete_accounting():
    assert observer().finish()["identity_accounting_complete"] is False


def test_identity_accounting_does_not_imply_exact_departure_clock():
    o = identity.IdentityObserver([dict(id="i1", depart_s=0)])
    o.ingest(frame(0)); o.ingest(frame(.05, departed=["i1"], active=["i1"]))
    result = o.finish()
    assert result["identity_accounting_complete"] is True
    assert result["native_departure_clock_complete"] is False


def test_native_departure_and_FCD_observation_are_distinct():
    o = observer(); o.ingest(frame(0))
    o.ingest(frame(.05, loaded=["i1"], departed=["i1"], active=["i1"],
                   native_departures={"i1": dict(actual_departure_s=0, depart_delay_s=0)}))
    o.ingest(frame(.1, active=["i1"]))
    o.observe_fcd("i1", .1)
    o.ingest(frame(.15, arrived=["i1"]))
    report = o.finish()["vehicles"]
    assert report["i1"]["actual_departure_s"] == 0 and report["i1"]["first_FCD_s"] == .1
    assert report["i1"]["state"] == "arrived_native" and report["i1"]["right_censored"] is False
    assert report["m1"]["state"] == "Unknown" and report["m1"]["native_insertion_status"] == "Unknown"


def test_pending_is_a_direct_identity_snapshot_and_censored_at_stop():
    o = observer(); o.ingest(frame(0))
    o.ingest(frame(.05, loaded=["i1"], pending=["i1"]))
    o.ingest(frame(.1, pending=["i1"]))
    r = o.finish(interrupted=True)["vehicles"]["i1"]
    assert r["state"] == "pending_native" and r["first_FCD_s"] is None and r["right_censored"] is True
    o.ingest(frame(.15, departed=["i1"], active=["i1"], native_departures={"i1": dict(actual_departure_s=.1, depart_delay_s=.1)}))
    assert o.finish()["vehicles"]["i1"]["depart_delay_s"] == .1


def test_disappearance_without_arrival_is_unknown_even_with_equal_counts():
    o = observer(); o.ingest(frame(0)); o.ingest(frame(.05, departed=["i1"], active=["i1"]))
    o.ingest(frame(.1, active=["m1"]))
    r = o.finish()["vehicles"]["i1"]
    assert r["state"] == "Unknown" and r["arrived_at"] is None and r["discarded_at"] is None
    assert not o.finish()["identity_accounting_complete"]


def test_teleport_roundtrip_and_explicit_discard_evidence():
    o = observer(); o.ingest(frame(0)); o.ingest(frame(.05, departed=["i1"], active=["i1"]))
    o.ingest(frame(.1, teleport_start=["i1"]))
    assert o.finish()["vehicles"]["i1"]["state"] == "teleporting_native"
    o.ingest(frame(.15, teleport_end=["i1"], active=["i1"]))
    o.ingest(frame(.2, discarded=[dict(id="i1", source="synthetic_explicit_discard", evidence_sha256="a" * 64)]))
    assert o.finish()["vehicles"]["i1"]["state"] == "discarded_explicit_evidence"


@pytest.mark.parametrize("change,reason", [
    (dict(active=["unknown"]), "unknown_identity"),
    (dict(departed=["i1", "i1"]), "duplicate_event_identity"),
    (dict(arrived=["i1"]), "arrival_before_departure"),
    (dict(active=["i1"], pending=["i1"]), "contradictory_sets"),
    (dict(teleport_end=["i1"]), "teleport_end_without_start"),
    (dict(discarded=[dict(id="i1", source="missing_FCD", evidence_sha256="a" * 64)]), "discard_identity_evidence_required"),
])
def test_inconsistent_events_rejected_transactionally(change, reason):
    o = observer(); o.ingest(frame(0))
    with pytest.raises(identity.IdentityContractError, match=reason): o.ingest(frame(.05, **change))
    assert len(o.frames) == 1 and o.time == 0


def test_duplicate_declaration_clock_FCD_and_terminal_reappearance():
    with pytest.raises(identity.IdentityContractError, match="duplicate_declared_identity"):
        identity.IdentityObserver([dict(id="i1", depart_s=0)] * 2)
    o = observer(); o.ingest(frame(0))
    with pytest.raises(identity.IdentityContractError, match="clock_gap_or_duplicate"): o.ingest(frame(.1))
    o.ingest(frame(.05, departed=["i1"], active=["i1"]))
    o.ingest(frame(.1, arrived=["i1"]))
    o.observe_fcd("i1", .1)
    with pytest.raises(identity.IdentityContractError, match="duplicate_or_reversed_FCD"): o.observe_fcd("i1", .1)
    with pytest.raises(identity.IdentityContractError, match="terminal_identity_reappeared"): o.ingest(frame(.15, active=["i1"]))


def test_missing_event_APIs_degrade_without_zero_or_fabricated_state():
    o = observer(); o.ingest(frame(0))
    o.ingest(frame(.05, departed=None, active=None, pending=None, arrived=None))
    o.ingest(frame(.1, departed=None, active=None, pending=None, arrived=["i1"]))
    assert o.finish()["vehicles"]["i1"]["state"] == "arrived_native"
    assert o.finish()["vehicles"]["i1"]["native_insertion_status"] == "Unknown"
    assert o.finish()["API_coverage"]["pending_unavailable"] == 2


def test_read_only_collector_does_not_connect_or_start():
    sim = SimpleNamespace(getTime=lambda: .05, getLoadedIDList=lambda: ["i1"], getDepartedIDList=lambda: ["i1"],
                          getArrivedIDList=lambda: [], getPendingVehicles=lambda: [], getStartingTeleportIDList=lambda: [],
                          getEndingTeleportIDList=lambda: [], getCollidingVehiclesNumber=lambda: 0)
    veh = SimpleNamespace(getIDList=lambda: ["i1"], getDeparture=lambda _: 0, getDepartDelay=lambda _: 0, getLaneID=lambda _: "main_2_0")
    result = identity.collect_snapshot(SimpleNamespace(simulation=sim, vehicle=veh))
    assert result["native_departures"]["i1"]["actual_departure_s"] == 0 and result["on_road"] == ["i1"]
    del veh.getDeparture
    assert identity.collect_snapshot(SimpleNamespace(simulation=sim, vehicle=veh))["native_departures"]["i1"]["actual_departure_s"] is None


ROUTES = (b'<routes><vType id="t" length="4"/><route id="r" edges="main_2"/>'
          b'<vehicle id="i1" type="t" route="r" depart="0" departLane="0" departPos="1" departSpeed="10.00"/>'
          b'<vehicle id="m1" type="t" route="r" depart="1" departLane="0" departPos="base" departSpeed="max"/></routes>')
NETWORK = b'<net><edge id="main_2"><lane id="main_2_0" index="0" speed="10" length="100"/></edge></net>'


def config(duration=.1, seed=1):
    return (f'<configuration><input><net-file value="network.net.xml"/><route-files value="routes.rou.xml"/></input>'
            f'<time><begin value="0"/><end value="{duration}"/><step-length value=".05"/></time><output>'
            f'<fcd-output value="fcd.xml"/><summary-output value="summary.xml"/></output><seed value="{seed}"/></configuration>').encode()


def test_static_DS_scope_preserves_noninitial_order_and_exact_bytes():
    changed = ROUTES.replace(b'departSpeed="10.00"', b'departSpeed="max"')
    result = inputs.compare_initial_policy(ROUTES, changed, target_ids=["i1"])
    assert result["changed_initial_count"] == 1 and result["exact_allowed_bytes_only"] is True
    assert inputs.audit_bundle(ROUTES, NETWORK, config())["potential_dynamic_pulse_conflicts"] == 1
    assert inputs.audit_bundle(changed, NETWORK, config())["potential_dynamic_pulse_conflicts"] == 0


@pytest.mark.parametrize("mutation", [
    lambda s: s.replace(b'depart="1"', b'depart="2"'),
    lambda s: s.replace(b'departPos="base"', b'departPos="2"'),
    lambda s: s.replace(b'id="m1"', b'id="m2"'),
    lambda s: s.replace(b'length="4"', b'length="5"'),
    lambda s: s.replace(b'departLane="0"', b'departLane="1"', 1),
])
def test_forbidden_static_changes_fail(mutation):
    changed = ROUTES.replace(b'departSpeed="10.00"', b'departSpeed="max"')
    with pytest.raises(inputs.InputContractError): inputs.compare_initial_policy(ROUTES, mutation(changed), target_ids=["i1"])


@pytest.mark.parametrize("reference", ["../escape.xml", "C:/escape.xml", "\\\\host\\share\\escape.xml"])
def test_XML_path_escape_rejected(reference):
    with pytest.raises(inputs.InputContractError, match="XML_path_escape"):
        inputs.config_references(config().replace(b'network.net.xml', reference.encode()))


def test_XML_external_entity_duplicate_ID_and_wrong_native_geometry():
    with pytest.raises(inputs.InputContractError): inputs.inventory(b'<!DOCTYPE a><routes/>')
    with pytest.raises(inputs.InputContractError): inputs.inventory(ROUTES.replace(b'id="m1"', b'id="i1"'))
    with pytest.raises(inputs.InputContractError, match="invalid_start_position"):
        inputs.audit_bundle(ROUTES.replace(b'departPos="1"', b'departPos="101"'), NETWORK, config())


def test_scope_exact_read_write_traversal_hash_drift_and_process(tmp_path):
    root = tmp_path / "repo"; root.mkdir(); bound = root / "allowed.txt"; bound.write_text("ok")
    scope = isolation.Scope(root, {"allowed.txt": isolation.sha(bound)}, "outputs", commands=[["fake", "only"]])
    assert scope.read_bound("allowed.txt") == b"ok"
    scope.create("outputs/new.txt", b"new")
    with pytest.raises(FileExistsError): scope.create("outputs/new.txt", b"replace")
    for value in ["../outside", "unapproved.txt", "locked_holdout/raw.xml"]:
        with pytest.raises(isolation.ScopeViolation): scope.check(value)
    with pytest.raises(isolation.ScopeViolation): scope.check("allowed.txt", writing=True)
    bound.write_text("drift")
    with pytest.raises(isolation.ScopeViolation, match="input_hash_drift"): scope.read_bound("allowed.txt")
    scope.process(["fake", "only"], cwd=root / "outputs")
    for command in [["fake", "only"], ["fake", "other"], ["sumo.EXE", "-c", "x"]]:
        with pytest.raises(isolation.ScopeViolation): scope.process(command, cwd=root / "outputs")


def test_symlink_or_junction_guard_with_injected_filesystem_flag(tmp_path, monkeypatch):
    root = tmp_path / "repo"; root.mkdir(); link = root / "outputs/link"
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda p: p == link or original(p))
    scope = isolation.Scope(root, {}, "outputs")
    with pytest.raises(isolation.ScopeViolation, match="symlink_or_junction"):
        scope.create(link / "escape.txt", b"never")


def test_real_symlink_escape_if_operating_system_permits(tmp_path):
    import os
    root = tmp_path / "repo"; (root / "outputs").mkdir(parents=True)
    outside = tmp_path / "outside"; outside.mkdir()
    try:
        os.symlink(outside, root / "outputs/link", target_is_directory=True)
    except OSError as error:
        pytest.skip("OS symlink creation unavailable: " + str(error))
    scope = isolation.Scope(root, {}, "outputs")
    with pytest.raises(isolation.ScopeViolation, match="symlink_or_junction"):
        scope.create("outputs/link/escape.txt", b"never")
    assert not (outside / "escape.txt").exists()


def test_offline_output_namespace_does_not_accept_old_history(tmp_path):
    with pytest.raises(ValueError, match="offline_output_outside_versioned_task"):
        validate_output(tmp_path, tmp_path / "code/outputs/formal/calibration/old_history")


def test_journal_hash_chain_and_partial_record_refused(tmp_path):
    scope = isolation.Scope(tmp_path, {}, "outputs")
    journal = execution.EventJournal(scope, "outputs/events.jsonl")
    journal.append(frame(0)); prefix = journal.path.read_bytes(); journal.append(frame(.05))
    assert journal.path.read_bytes().startswith(prefix) and execution.verify_journal(journal.path)["events"] == 2
    with journal.path.open("ab") as stream: stream.write(b'{"incomplete":')
    with pytest.raises(ValueError, match="incomplete"): execution.verify_journal(journal.path)


def test_FCD_sidecar_observation_and_partial_XML_preserve_known_rows(tmp_path):
    o = observer(); o.ingest(frame(0)); o.ingest(frame(.05, departed=["i1"], active=["i1"]))
    o.ingest(frame(.1, active=["i1"]))
    p = tmp_path / "fcd.xml"
    p.write_text('<fcd-export><timestep time="0.1"><vehicle id="i1"/></timestep>')
    result = execution.attach_FCD_observations(o, p, allow_partial=True)
    assert result["parse_complete"] is False and o.finish()["vehicles"]["i1"]["first_FCD_s"] == .1
    assert o.finish()["vehicles"]["i1"]["actual_departure_s"] is None


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def execution_case(tmp_path):
    source_root = Path(__file__).resolve().parents[2]
    cfg = json.loads((source_root / "code/configs/stage_0_5_interaction_research_v2.json").read_text(encoding="utf-8"))
    cfg.update(ledger_path="journal/events.jsonl", output_root="outputs", historical_references=[])
    write(tmp_path / "budget.json", cfg)
    ledger = ledger_module.ResearchLedger(tmp_path, "budget.json"); ledger.initialize()
    files = {"routes.rou.xml": ROUTES, "network.net.xml": NETWORK, "run.sumocfg": config()}
    for name, data in files.items(): (tmp_path / name).write_bytes(data)
    (tmp_path / "plan.md").write_text("synthetic plan")
    (tmp_path / "source.py").write_text("# synthetic source")
    (tmp_path / "fake_tool.bin").write_bytes(b"not executable")
    write(tmp_path / "isolation.json", dict(task_id=ledger_module.TASK, input_and_test_resource_scope_accepted=True))
    run = dict(id="SYNTH_R1", seed=1, duration_s=.1, question="synthetic", contrast="synthetic control", condition="synthetic0750",
               factors={"supply": False, "ramp": False}, initialization_policy="synthetic", artifact_path="outputs/SYNTH_R1",
               input_files={n: n for n in files}, input_sha256={n: isolation.sha(tmp_path / n) for n in files})
    p = dict(task_id=ledger_module.TASK, synthetic_test_only=True, execution_allowed=True, researcher_confirmed=True, protocol_frozen=True,
             budget_sha256=isolation.sha(tmp_path / "budget.json"), plan_path="plan.md", plan_sha256=isolation.sha(tmp_path / "plan.md"), plan_version="synthetic",
             source_sha256={"source.py": isolation.sha(tmp_path / "source.py")}, external_file_sha256={"fake_tool.bin": isolation.sha(tmp_path / "fake_tool.bin")},
             environment=execution.environment_binding(), git_commit="a" * 40, worktree_sha256="b" * 64,
             admission=dict(initialization_policy_approved=True, measurement_contract_approved=True, input_fidelity_approved=True),
             isolation=dict(accepted_for_new_task=True, report_path="isolation.json", report_sha256=isolation.sha(tmp_path / "isolation.json")), runs=[run])
    write(tmp_path / "proposal.json", p)
    approval = dict(task_id=ledger_module.TASK, researcher_confirmed=True, decision_record="synthetic test only", run_ids=[run["id"]], proposal_sha256=isolation.sha(tmp_path / "proposal.json"))
    return tmp_path, ledger, p, approval


def resources():
    return dict(wall_s=0, process_tree_rss_bytes=1, free_c_bytes=6 * 1024**3, free_d_bytes=15 * 1024**3,
                available_memory_bytes=5 * 1024**3, task_output_bytes=0)


def backend():
    return execution.ReplayBackend([frame(0), frame(.05, loaded=["i1"], departed=["i1"], active=["i1"]), frame(.1, active=["i1"])])


@pytest.mark.parametrize("flag", ["execution_allowed", "researcher_confirmed", "protocol_frozen", "accepted_for_new_task", "initialization_policy_approved"])
def test_missing_approval_flags_refuse_before_process_or_attempt(execution_case, monkeypatch, flag):
    root, ledger, p, approval = execution_case
    if flag == "accepted_for_new_task": p["isolation"][flag] = False
    elif flag.endswith("approved"): p["admission"][flag] = False
    else: p[flag] = False
    write(root / "proposal.json", p); approval["proposal_sha256"] = isolation.sha(root / "proposal.json")
    monkeypatch.setattr(execution.subprocess, "Popen", lambda *a, **k: pytest.fail("native process forbidden"))
    a = execution.ExecutionAdapter(root, ledger, "reports")
    with pytest.raises(execution.AdmissionRefused): a.execute("proposal.json", approval, "SYNTH_R1")
    assert ledger.snapshot()["attempt_count"] == 0 and list((root / "reports").glob("refusal_*.json"))


def test_native_build_lock_cannot_be_enabled_by_complete_fixture(execution_case, monkeypatch):
    root, ledger, _, approval = execution_case
    monkeypatch.setattr(execution.NativeBackend, "start", lambda *_: pytest.fail("must reject before native backend"))
    monkeypatch.setattr(execution.subprocess, "Popen", lambda *a, **k: pytest.fail("must not spawn"))
    with pytest.raises(execution.AdmissionRefused, match="native_launch_locked"):
        execution.ExecutionAdapter(root, ledger, "reports").execute("proposal.json", approval, "SYNTH_R1")
    assert ledger.snapshot()["attempt_count"] == 0


@pytest.mark.parametrize("value", [None, "Unknown", 0, "true"])
def test_unknown_or_untyped_gate_flag_is_not_approval(value):
    reasons = execution.gate_reasons(dict(execution_allowed=value, admission=None, isolation=None), {"run_ids": None}, "R", "sha")
    assert "execution_allowed_not_true" in reasons and "single_run_authorization_missing" in reasons


@pytest.mark.parametrize("target", ["input", "source", "tool", "environment"])
def test_bound_drift_rejected_before_fake_start(execution_case, target):
    root, ledger, p, approval = execution_case
    if target == "environment":
        p["environment"]["python_version"] = "wrong"; write(root / "proposal.json", p); approval["proposal_sha256"] = isolation.sha(root / "proposal.json")
    else:
        (root / {"input": "routes.rou.xml", "source": "source.py", "tool": "fake_tool.bin"}[target]).write_bytes(b"drift")
    with pytest.raises(execution.AdmissionRefused):
        execution.ExecutionAdapter(root, ledger, "reports").execute("proposal.json", approval, "SYNTH_R1", backend=backend(), resource_probe=resources, measurement=lambda *_: dict.fromkeys(ledger_module.CHECKS, True))
    assert ledger.snapshot()["attempt_count"] == 0


def test_replay_complete_identity_journal_artifacts_and_measurement(execution_case):
    root, ledger, _, approval = execution_case
    state = execution.ExecutionAdapter(root, ledger, "reports").execute("proposal.json", approval, "SYNTH_R1", backend=backend(), resource_probe=resources,
        measurement=lambda *_: dict.fromkeys(ledger_module.CHECKS, True))
    assert state["attempts"]["SYNTH_R1"]["status"] == "measurement_accepted"
    assert execution.verify_journal(root / "outputs/SYNTH_R1/identity_events.jsonl")["events"] == 3
    assert (root / "routes.rou.xml").read_bytes() == ROUTES


def test_replay_failure_is_retained_and_censored(execution_case):
    root, ledger, _, approval = execution_case
    b = backend(); b.fail_at = 1
    with pytest.raises(RuntimeError, match="synthetic_runner_failure"):
        execution.ExecutionAdapter(root, ledger, "reports").execute("proposal.json", approval, "SYNTH_R1", backend=b, resource_probe=resources,
            measurement=lambda *_: dict.fromkeys(ledger_module.CHECKS, True))
    assert ledger.snapshot()["attempts"]["SYNTH_R1"]["status"] == "failed" and b.stopped
    assert (root / "outputs/SYNTH_R1/interrupted_identity_summary.json").is_file()


def test_cleanup_error_cannot_hide_original_failure(execution_case, monkeypatch):
    root, ledger, _, approval = execution_case
    b = backend(); b.fail_at = 1
    def broken_stop():
        raise RuntimeError("synthetic_cleanup_failure")
    monkeypatch.setattr(b, "stop", broken_stop)
    with pytest.raises(RuntimeError, match="synthetic_runner_failure"):
        execution.ExecutionAdapter(root, ledger, "reports").execute("proposal.json", approval, "SYNTH_R1", backend=b, resource_probe=resources,
            measurement=lambda *_: dict.fromkeys(ledger_module.CHECKS, True))
    assert ledger.snapshot()["attempts"]["SYNTH_R1"]["status"] == "failed"
    assert "synthetic_cleanup_failure" in (root / "outputs/SYNTH_R1/cleanup_errors.json").read_text()


def test_additive_evidence_export_retains_historical_manifest(tmp_path):
    import export_stage_0_5_v2_admission_evidence as evidence
    import export_project_evidence as base
    old = tmp_path / "old"; old.mkdir(); (old / "summary.json").write_text("{}")
    original = base._source_pairs
    try:
        base._source_pairs = lambda: {"RES-HISTORICAL-TEST": [("old/summary.json", "summary.json")]}
        base.export_evidence(tmp_path, {"RES-HISTORICAL-TEST"})
    finally:
        base._source_pairs = original
    manifest_path = tmp_path / "evidence/EVIDENCE_MANIFEST.json"
    before = json.loads(manifest_path.read_text())
    folder = tmp_path / evidence.LOCAL; folder.mkdir(parents=True)
    for name in evidence.NAMES[:-1]:
        write(folder / name, {})
    evidence.export(tmp_path)
    after = json.loads(manifest_path.read_text())
    old_entries = [x for x in before["results"] if x["result_id"] == "RES-HISTORICAL-TEST"]
    assert old_entries and all(x in after["results"] for x in old_entries)
    assert (tmp_path / "evidence/results/RES-HISTORICAL-TEST/summary.json").read_text() == "{}"


def test_replay_resource_failure_retains_attempt_and_stops_fake(execution_case):
    root, ledger, _, approval = execution_case
    calls = []
    def probe():
        calls.append(1); sample = resources()
        if len(calls) > 2: sample["wall_s"] = 601
        return sample
    b = backend()
    with pytest.raises(RuntimeError, match="resource_limit"):
        execution.ExecutionAdapter(root, ledger, "reports").execute("proposal.json", approval, "SYNTH_R1", backend=b, resource_probe=probe,
            measurement=lambda *_: dict.fromkeys(ledger_module.CHECKS, True))
    assert b.stopped and ledger.snapshot()["attempt_count"] == 1


def test_watchdog_only_calls_owned_stop_on_resource_violation(tmp_path):
    stopped = []
    scope = isolation.Scope(tmp_path, {}, "out"); (tmp_path / "out").mkdir()
    limits = dict(per_attempt_wall_s=600, process_tree_rss_bytes=3 * 1024**3, task_output_bytes=100,
                  min_free_c_bytes=1, min_free_d_bytes=1, min_available_memory_bytes=1)
    s = execution.ResourceSupervisor(limits, scope, tmp_path / "out", lambda: dict(resources(), wall_s=601))
    w = execution.ResourceWatchdog(s, lambda: stopped.append("own fake"), interval_s=.001)
    w.start(); w.done.wait(timeout=1)
    with pytest.raises(RuntimeError, match="resource_limit"): w.close()
    assert stopped == ["own fake"]


def test_task_output_limit_is_per_capsule_not_historical_lifetime(tmp_path):
    scope = isolation.Scope(tmp_path, {}, "outputs")
    scope.create("outputs/old_history/large.bin", b"x" * 100)
    scope.create("outputs/current/small.bin", b"x")
    limits = dict(per_attempt_wall_s=600, process_tree_rss_bytes=3 * 1024**3, task_output_bytes=10,
                  min_free_c_bytes=1, min_free_d_bytes=1, min_available_memory_bytes=1)
    s = execution.ResourceSupervisor(limits, scope, tmp_path / "outputs/current", resources)
    assert s.observe()["task_output_bytes"] == 1
    scope.create("outputs/current/too_large.bin", b"x" * 20)
    with pytest.raises(RuntimeError, match="task_output_bytes"): s.observe()


def test_C6_allowlist_rejects_third_window_path_and_duplicate_case():
    case = dict(id="timing_us101__0750_0805_U_s20261201", window="us101__0750_0805", seed=20261201, kind="timing", arm="U", files={})
    root = "code/outputs/formal/calibration/stage_0_5_boundary_timing_v1/runs/us101__0750_0805_U_s20261201/"
    for key, name in [("fcd", "fcd.xml"), ("routes", "routes.rou.xml"), ("network", "network/observed_geometry_supply_10p0_l5.net.xml"), ("config", "run.sumocfg"), ("old_measurements", "measured_state.parquet")]:
        case["files"][key] = dict(path=root + name, sha256="a" * 64)
    manifest = dict(schema="aad.c6-history-allowlist.v1", new_trajectory_attempts=0, cases=[case], core_sha256=dict.fromkeys(CORE, "a" * 64))
    validate_allowlist(manifest)
    manifest["cases"].append(case)
    with pytest.raises(ValueError, match="duplicate"): validate_allowlist(manifest)
    manifest["cases"].pop()
    original = case["files"]["fcd"]["path"]
    case["files"]["fcd"]["path"] = root + "other.xml"
    with pytest.raises(ValueError, match="history_path_scope"): validate_allowlist(manifest)
    case["files"]["fcd"]["path"] = original
    case["files"]["fcd"]["path"] = root.replace("0750_0805", "0820_0835") + "fcd.xml"
    with pytest.raises(ValueError, match="history_path_scope"): validate_allowlist(manifest)


def test_C6_reuse_cannot_extend_scope_and_case_ID_cannot_escape_output():
    manifest = dict(schema="aad.c6-history-allowlist.v1", new_trajectory_attempts=0, cases=[], core_sha256=dict.fromkeys(CORE, "a" * 64),
                    reuses=[dict(window="us101__0750_0805", seed=20261201, files={
                        "repaired_measured_state.parquet": dict(path="locked_holdout/table.parquet", sha256="a" * 64),
                        "after_events.json": dict(path="locked_holdout/events.json", sha256="a" * 64)})])
    with pytest.raises(ValueError, match="history_path_scope"): validate_allowlist(manifest)
    manifest["reuses"] = []
    manifest["cases"] = [dict(id="../escape", window="us101__0750_0805", seed=20261201, kind="timing", arm="U", files={})]
    with pytest.raises(ValueError, match="inexact_case_identity"): validate_allowlist(manifest)
