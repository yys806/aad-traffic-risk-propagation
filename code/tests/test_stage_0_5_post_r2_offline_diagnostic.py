"""Offline diagnostics preserve science boundaries and demonstrate contract gaps."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("post_r2", ROOT / "code/scripts/analyze_stage_0_5_post_r2_offline_diagnostic.py")
diag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diag)


def fixture(ttc=(2.5, 2.4, 2.6)):
    n = len(ttc)
    return pd.DataFrame(dict(run_id="r", scenario_id="s", vehicle_id="f", incarnation_id="i",
        leader_id="l", leader_incarnation_id="j", time_s=120+np.arange(n)/10,
        lane_id="1", native_lane_id="main_0_0", y_m=50., speed_mps=5.,
        net_gap_m=2., closing_speed_mps=1., measurement_status="valid",
        reliable_following_eligible=True, ttc_valid=True, ttc_s=list(ttc)))


def test_near_threshold_never_counts_as_risk():
    result = diag.summary(fixture())
    assert result["risk_rows_0_lt_ttc_lt_2"] == 0
    assert result["near_rows_2_le_ttc_lt_3"] == 3
    segment = diag.source_segments(fixture(), 2, 3)[0]
    assert segment["span_s"] == pytest.approx(.2)
    assert segment["diagnostic_only"] is True
    assert diag.source_segments(fixture(), 0, 2) == []


@pytest.mark.parametrize("field,value", [("leader_id", "other"), ("leader_incarnation_id", "other"),
    ("incarnation_id", "new"), ("native_lane_id", "main_0_1")])
def test_segment_respects_identity_and_lane_breaks(field, value):
    frame = fixture()
    frame.loc[1:, field] = value
    segments = diag.source_segments(frame, 2, 3)
    assert sorted(x["members"] for x in segments) == [1, 2]


def test_time_gap_missing_and_region_do_not_become_zero_risk():
    frame = fixture()
    frame.loc[1:, "time_s"] += .1
    assert len(diag.source_segments(frame, 2, 3)) == 2
    frame.loc[1, "measurement_status"] = "missing"
    assert diag.summary(frame)["valid_ttc_rows"] == 2
    frame.loc[2, "native_lane_id"] = "main_1_1"
    assert diag.source_mask(frame).sum() == 2


def test_formal_bounds_and_window_remain_half_open():
    frame = fixture((0, 2, 3))
    result = diag.summary(frame)
    assert result["risk_rows_0_lt_ttc_lt_2"] == 0
    assert result["near_rows_2_le_ttc_lt_3"] == 1
    frame["y_m"] = [0, 150, 149.999]
    frame.loc[2, "time_s"] = 390
    assert diag.source_mask(frame).tolist() == [True, False, False]


def test_adapter_counterexamples_are_not_scientific_equivalence():
    probes = {row["case"]: row for row in diag.adapter_probes()}
    assert probes["clean"]["native_events"] == probes["clean"]["D1_onsets"] == 1
    assert probes["native_lane_change"]["native_events"] == 1
    assert probes["native_lane_change"]["D1_onsets"] == 0
    for name in ["identity_break", "observation_gap"]:
        assert probes[name]["native_events"] == probes[name]["D1_onsets"] == 0
        assert probes[name]["formal_aligned_events"] == 1
        assert probes[name]["mapped_flag_true_rows"][name] == 0
    assert probes["inconsistent_negative_ttc"]["native_events"] == 1
    assert probes["inconsistent_negative_ttc"]["D1_onsets"] == 0
    assert probes["inconsistent_negative_ttc"]["formal_aligned_error"] == "non-risk event member"
    assert all(not x["scientific_equivalence_accepted"] for x in probes.values())


@pytest.mark.parametrize("event,args", [("subprocess.Popen", ()), ("socket.connect", ())])
def test_offline_guard_prohibits_native_and_network(event, args):
    with pytest.raises(PermissionError):
        diag.offline_guard(event, args)


def test_archived_source_counts_are_reconciled_when_bundle_present():
    path = ROOT / diag.PACKAGE / "diagnostic.json"
    if not path.exists():
        pytest.skip("portable diagnostic not present")
    result = json.loads(path.read_bytes())
    assert result["native_launches"] == result["traci_connections"] == result["locked_holdout_reads"] == 0
    assert result["formal_equivalence_accepted"] is False
    for arm in result["runs"].values():
        source = arm["source"]
        assert source["state_rows"] == sum(source["quality_counts"].values())
        assert source["risk_rows_0_lt_ttc_lt_2"] == 0
        assert arm["source_all_D1"]["onset_events"] == 0
        assert sum(x["members"] for x in arm["near_threshold_segments"]) == source["near_rows_2_le_ttc_lt_3"]


def test_independent_verifier_rejects_hash_drift_and_self_reference(tmp_path):
    spec = importlib.util.spec_from_file_location("verify_post_r2", ROOT / "code/scripts/verify_stage_0_5_post_r2_offline_diagnostic.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    payload = tmp_path / "payload.json"
    payload.write_text('{}\n')
    row = dict(path=payload.name, bytes=payload.stat().st_size, sha256=verifier.sha(payload))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(dict(files=[row])))
    sums = tmp_path / "SHA256SUMS"
    sums.write_text(row['sha256']+'  payload.json\n'+verifier.sha(manifest)+'  manifest.json\n')
    assert verifier.verify_bundle(tmp_path)['status'] == 'PASS'
    payload.write_text('{"changed": true}\n')
    with pytest.raises(AssertionError, match='manifest_hash'):
        verifier.verify_bundle(tmp_path)
    manifest.write_text(json.dumps(dict(files=[dict(path='manifest.json')])))
    with pytest.raises(AssertionError, match='self_reference'):
        verifier.verify_bundle(tmp_path)


def test_global_export_preserves_registered_sealed_bundle_and_rejects_drift(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('export_post_r2', ROOT/'code/scripts/export_project_evidence.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    bundle = tmp_path/'evidence/results/RES-TEST'
    bundle.mkdir(parents=True)
    payload = bundle/'result.json'
    payload.write_bytes(b'{"sealed":true}\n')
    name = payload.relative_to(tmp_path).as_posix()
    entry = dict(result_id='RES-TEST', files=[dict(source_path=name, snapshot_path=name,
                 size_bytes=payload.stat().st_size, sha256=exporter._sha256(payload))])
    (tmp_path/'evidence/EVIDENCE_MANIFEST.json').write_text(json.dumps(dict(results=[entry])))
    monkeypatch.setattr(exporter, '_source_pairs', lambda: {'RES-TEST': [('missing_old_output/result.json', 'result.json')]})
    result = exporter.export_evidence(tmp_path)
    assert result['results'] == [entry]
    assert payload.read_bytes() == b'{"sealed":true}\n'
    assert exporter.verify_evidence(tmp_path) == []
    payload.write_bytes(b'{"drift":true}\n')
    with pytest.raises(ValueError, match='self-managed evidence drift'):
        exporter.export_evidence(tmp_path)


def test_global_export_does_not_rewrite_identical_read_only_history(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('export_noop', ROOT/'code/scripts/export_project_evidence.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    source = tmp_path/'small.json'
    source.write_bytes(b'{}\n')
    destination = tmp_path/'evidence/results/RES-TEST/small.json'
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())
    monkeypatch.setattr(exporter, '_source_pairs', lambda: {'RES-TEST': [('small.json', 'small.json')]})
    def forbid(*args, **kwargs):
        raise AssertionError('identical sealed evidence must not be rewritten')
    monkeypatch.setattr(exporter.shutil, 'copyfile', forbid)
    assert exporter.export_evidence(tmp_path)['results'][0]['result_id'] == 'RES-TEST'
    assert exporter.verify_evidence(tmp_path) == []
