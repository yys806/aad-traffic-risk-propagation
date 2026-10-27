"""Evidence-only regression. No simulator, native connection or research call."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("admission_v6", ROOT / "code/scripts/prepare_stage_0_5_b00_admission_v6.py")
v6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v6)


@pytest.fixture(scope="module")
def evidence():
    return v6.verify_existing(ROOT)


def test_actual_archived_receipt_and_B00_scope_without_any_process(evidence, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("process_or_research_execution_forbidden")
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    import stage_0_5_linux_execution_v4 as driver
    monkeypatch.setattr(driver, "launch_linux", forbidden)
    monkeypatch.setattr(driver, "execute_research", forbidden)
    monkeypatch.setattr(driver, "_execute_authorized", forbidden)
    before = {p.name:v6.sha(p) for p in (ROOT / v6.V5).iterdir()}
    report = v6.verify_existing(ROOT)
    assert report["acceptance"]["status"] == "Pass"
    assert report["measurement_reference_units"] == 18
    assert len(report["production_source_sha256"]) == 12
    assert report["SUMO_launches"] == report["real_TraCI_connections"] == report["new_B00_research_trajectories"] == 0
    assert before == {p.name:v6.sha(p) for p in (ROOT / v6.V5).iterdir()}


@pytest.mark.parametrize("name", list(v6.EXPECTED))
def test_every_key_artifact_hash_tamper_is_refused(name, monkeypatch):
    original = v6.sha
    monkeypatch.setattr(v6, "sha", lambda p: "0" * 64 if Path(p) == ROOT / name else original(p))
    with pytest.raises(ValueError, match="bound_file_drift"):
        v6.verify_map(ROOT, v6.EXPECTED)


@pytest.mark.parametrize("name", ["/etc/passwd", "C:/temp/file", "C:temp", "../file", "a/../../b", "a\\b", "./a"])
def test_unsafe_paths_refused(name):
    with pytest.raises(ValueError):
        v6.relative(ROOT, name)


def test_symlink_path_refused(tmp_path):
    (tmp_path / "target").write_text("test")
    try:
        (tmp_path / "alias").symlink_to(tmp_path / "target")
    except OSError:
        pytest.skip("OS symlink privilege unavailable; path traversal rejection tested separately")
    with pytest.raises(ValueError, match="symlink"):
        v6.relative(tmp_path, "alias")


@pytest.mark.parametrize("kind", ["source", "runtime", "policy", "input"])
def test_source_runtime_policy_and_B00_input_mismatches_refused(kind):
    p = v6.load(ROOT, v6.V5 + "/proposal.json")
    s = v6.load(ROOT, v6.PREP + "/smoke_proposal.json")
    b = v6.load(ROOT, v6.PREP + "/research_policy.json")
    sp = v6.load(ROOT, v6.PREP + "/smoke_policy.json")
    if kind == "source":
        s["controller_source_sha256"][next(iter(s["controller_source_sha256"]))] = "0" * 64
    elif kind == "runtime":
        s["runtime_manifest_sha256"] = "0" * 64
    elif kind == "policy":
        b["kernel_readonly"].append("/tmp")
    else:
        b["file_sha256"][next(iter(b["inputs"].values()))] = "0" * 64
    with pytest.raises(ValueError):
        v6.check_policy(p, s, b, sp)


def test_actual_B00_input_drift_is_refused(monkeypatch):
    p = v6.load(ROOT, v6.V5 + "/proposal.json")
    n = next(iter(p["runs"][0]["input_sha256"]))
    original = v6.sha
    monkeypatch.setattr(v6, "sha", lambda q: "0" * 64 if Path(q) == ROOT / n else original(q))
    with pytest.raises(ValueError, match="bound_file_drift"):
        v6.verify_map(ROOT, p["runs"][0]["input_sha256"])


@pytest.mark.parametrize("field", ["seed", "duration_s", "evaluation_elapsed_s", "single_attempt_limits"])
def test_any_scientific_run_change_is_refused(field):
    old = v6.load(ROOT, v6.V5 + "/proposal.json")
    new = copy.deepcopy(old)
    new["runs"][0][field] = "tampered"
    with pytest.raises(ValueError):
        v6.scientific_diff(old, new)


@pytest.mark.parametrize("field", ["execution_allowed", "researcher_confirmed", "protocol_frozen", "admission"])
def test_research_approvals_cannot_be_flipped(field):
    old = v6.load(ROOT, v6.V5 + "/proposal.json")
    new = copy.deepcopy(old)
    new[field] = True
    with pytest.raises(ValueError):
        v6.scientific_diff(old, new)


def test_candidate_or_audit_existing_is_refused_without_write(tmp_path):
    p = tmp_path / v6.V6
    p.mkdir(parents=True)
    (p / "sentinel").write_bytes(b"original")
    with pytest.raises(ValueError, match="new_immutable_candidate_required"):
        v6.prepare(tmp_path)
    assert (p / "sentinel").read_bytes() == b"original"


def test_missing_and_corrupt_certificate_fail_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        v6.load(tmp_path, "integration_acceptance.json")
    (tmp_path / "integration_acceptance.json").write_bytes(b"not-json")
    with pytest.raises(ValueError):
        v6.load(tmp_path, "integration_acceptance.json")
    with pytest.raises(KeyError):
        v6.check_certificate_claims({}, {}, {})


def test_collect_live_failure_preserves_raw_bytes_and_never_retries(tmp_path, monkeypatch):
    p = v6.load(ROOT, v6.V5 + "/proposal.json")
    monkeypatch.setattr(v6, "load", lambda *a:p)
    calls = []
    def failed(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 7, b"\xffout", b"\xfeerr")
    monkeypatch.setattr(subprocess, "run", failed)
    out = tmp_path / "live"
    with pytest.raises(ValueError, match="read_only_Linux_check_failed"):
        v6.collect_live(tmp_path, out)
    assert len(calls) == 1 and calls[0][-2] == "preflight"
    assert (out / "precertificate_preflight.stdout").read_bytes() == b"\xffout"
    assert (out / "precertificate_preflight.stderr").read_bytes() == b"\xfeerr"
