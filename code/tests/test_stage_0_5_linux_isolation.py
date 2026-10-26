"""Portable admission/guard regressions; never execute WSL or a native process."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import stage_0_5_isolation_admission as admission
import stage_0_5_linux_isolation as guard
import stage_0_5_execution_v2 as execution
import stage_0_5_acceptance_v3 as acceptance
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
PROBE="docs/audits/stage_0_5_wsl_isolation_v1/probe/record.json"


def record():return json.loads((ROOT/PROBE).read_bytes())


def test_actual_exported_kernel_observations_pass_without_accepting_native_task():
    result=admission.capability_report(ROOT,PROBE,hashlib.sha256((ROOT/PROBE).read_bytes()).hexdigest())
    assert result["capability_verified"] is True
    assert len(result["checks"])==14 and all(result["checks"].values())
    assert result["accepted_for_new_task"] is False


@pytest.mark.parametrize("fault",["OOM","PID","CPU","negative_access","namespace","child","output","timeout","success_exit","failure_artifact"])
def test_all_true_summary_cannot_hide_missing_kernel_evidence(fault):
    r=record();rows={v["mode"]:v for v in r["commands"]}
    if fault in ["OOM","PID","CPU"]:
        mode,name={"OOM":("memory","memory.events"),"PID":("pids","pids.events"),"CPU":("cpu","cpu.stat")}[fault]
        rows[mode]["runtime"]["kernel_counters"][name]=""
    elif fault=="negative_access":rows["basic"]["observations"]["vsock"]["denied"]=False
    elif fault=="namespace":rows["basic"]["observations"]["namespace_ids"]["net"]=r["host_namespaces"]["net"]
    elif fault=="child":rows["basic"]["observations"]["child_inherits_denial"]=False
    elif fault=="output":rows["output"]["observations"]["aggregate_tmpfs_limit"]["denied"]=False
    elif fault=="timeout":rows["timeout"]["runtime"]["termination_signals"]=[]
    elif fault=="success_exit":rows["basic"]["exit_code"]=125
    elif fault=="failure_artifact":rows["memory"]["runtime"]["artifact_sha256"]={}
    assert all(r["checks"].values())
    assert not all(admission.probe_checks(r).values())


def test_probe_hash_drift_refused():
    with pytest.raises(ValueError,match="probe_evidence_drift"):
        admission.capability_report(ROOT,PROBE,"0"*64)


def test_actual_eighth_acceptance_requires_run_receipt_despite_kernel_capability():
    context=dict(scope=SimpleNamespace(repo=ROOT),proposal=dict(isolation=dict(capability_evidence_path=PROBE,
        capability_evidence_sha256=hashlib.sha256((ROOT/PROBE).read_bytes()).hexdigest())))
    result=acceptance.isolation_acceptance(context)
    assert result["status"]=="Unknown" and result["passed"] is False
    assert result["evidence"]["capability_verified"] is True
    context["proposal"]["isolation"]["capability_evidence_sha256"]="0"*64
    assert acceptance.isolation_acceptance(context)["status"]=="Reject"


def test_missing_modes_not_unknown_zero():
    r=record();r["commands"].pop()
    with pytest.raises(ValueError,match="incomplete_kernel_probe_modes"):
        admission.probe_checks(r)


def test_capability_does_not_admit_wrong_runtime_or_Windows_controller(monkeypatch):
    monkeypatch.setattr(admission.sys,"platform","win32")
    p=dict(native_runtime_version=[22,"SUMO 1.26.0"],native_binary="D:/SUMO/sumo.exe",isolation={})
    errors=admission.runtime_reasons(p,dict(installed_versions=record()["installed_versions"]))
    assert "Linux_SUMO_version_mismatch:installed=1.18.0,required=1.26.0" in errors
    assert "Windows_native_controller_not_inside_verified_Linux_capsule" in errors
    assert "exact_Linux_controller_capsule_and_runtime_not_bound" in errors


def test_direct_broker_entry_refused_before_mounts_or_signals(monkeypatch):
    monkeypatch.setattr(guard.os,"getpid",lambda:98765)
    monkeypatch.setattr(guard,"mount",lambda *a,**k:pytest.fail("must not mount"))
    monkeypatch.setattr(guard.os,"kill",lambda *a,**k:pytest.fail("must not signal"))
    with pytest.raises(RuntimeError,match="fresh_user_and_PID_namespace_required"):
        guard.child("not_read","not_read")


def test_future_native_unlock_still_rejects_unisolated_host_before_Popen(monkeypatch):
    monkeypatch.setattr(execution,"NATIVE_LAUNCH_LOCKED",False)
    monkeypatch.setattr(execution,"gate_reasons",lambda *a,**k:[])
    monkeypatch.setattr(admission.sys,"platform","win32")
    monkeypatch.setattr(execution.subprocess,"Popen",lambda *a,**k:pytest.fail("process creation forbidden"))
    with pytest.raises(PermissionError,match="native_controller_requires_OS_capsule"):
        execution.NativeBackend().start(dict(proposal={},approval={},run={"id":"fake"},proposal_sha256="a",budget_task_id="fake"))


def policy(tmp_path):
    capsule=tmp_path/"capsule";capsule.mkdir()
    source=tmp_path/"program";source.write_bytes(b"synthetic")
    return dict(capsule=str(capsule),scratch=str(capsule/"scratch"),archive=str(capsule/"archive"),
        argv=[str(source)],executables=[str(source)],file_sha256={str(source):guard.sha(source)},
        readonly_paths=[str(source)],inputs={"input.txt":str(source)},memory_bytes=64*1024**2,
        output_bytes=1024**2,wall_s=5,tasks=8)


def test_builder_exact_bindings_and_kernel_resource_command(tmp_path,monkeypatch):
    monkeypatch.setattr(guard.sys,"platform","linux");monkeypatch.setattr(guard.platform,"machine",lambda:"x86_64")
    p=policy(tmp_path);path=tmp_path/"policy.json";path.write_bytes(json.dumps(p,sort_keys=True,separators=(",",":")).encode())
    argv=guard.build_command(path,p)
    assert argv[0]=="/usr/bin/systemd-run" and "MemoryMax=67108864" in argv
    assert "KillMode=control-group" in argv and "--net" in argv and "--mount-proc" in argv
    Path(p["argv"][0]).write_bytes(b"changed")
    with pytest.raises(ValueError,match="isolation_binding_drift"):guard.build_command(path,p)


@pytest.mark.parametrize("fault",["memory","output_exists","input_traversal","unbound_exec"])
def test_guard_rejects_invalid_scope_before_process_creation(tmp_path,monkeypatch,fault):
    monkeypatch.setattr(guard.sys,"platform","linux");monkeypatch.setattr(guard.platform,"machine",lambda:"x86_64")
    p=policy(tmp_path)
    if fault=="memory":p["memory_bytes"]=4*1024**3
    elif fault=="output_exists":Path(p["archive"]).mkdir()
    elif fault=="input_traversal":p["inputs"]={"../outside":p["argv"][0]}
    elif fault=="unbound_exec":p["executables"].append("/unbound")
    with pytest.raises(ValueError):guard.validate(p)


def test_targeted_extension_reuses_only_unchanged_scientific_sources(tmp_path):
    previous=dict(source_sha256={"code/src/riskprop/stage_0_5_d1_measurement.py":"science",
        "code/scripts/stage_0_5_admission_v3.py":"old"},full=dict(exit_code=0,passed=1130))
    path=tmp_path/"previous.json";path.write_text(json.dumps(previous))
    sources=dict(previous["source_sha256"]);sources["code/scripts/stage_0_5_admission_v3.py"]="new"
    r=dict(validation_mode="isolation_targeted_extension",source_sha256=sources,targeted=dict(exit_code=0),
        reused_full_regression=dict(path="previous.json",sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
        modified_existing_sources=["code/scripts/stage_0_5_admission_v3.py"],added_sources=[])
    assert admission.software_extension_verified(tmp_path,r,sources)
    changed=dict(sources);changed["code/src/riskprop/stage_0_5_d1_measurement.py"]="changed"
    r["source_sha256"]=changed;r["modified_existing_sources"].append("code/src/riskprop/stage_0_5_d1_measurement.py")
    assert not admission.software_extension_verified(tmp_path,r,changed)
