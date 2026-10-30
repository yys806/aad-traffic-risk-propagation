"""Synthetic contract evidence; no raw data, native execution or holdout."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("round2_closure_comparability",
    ROOT / "code/scripts/audit_stage_0_5_round2_closure_comparability.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture(scope="module")
def probes():
    return {name: audit.evaluate_probe(name) for name in audit.PROBES}


def test_valid_domain_event_members_onset_and_confirmation_agree(probes):
    row = probes["normal"]
    for interface in ["native", "formal_aligned"]:
        assert row[interface]["error"] is None
        event, = row[interface]["result"]
        assert (event["event_start_s"], event["event_confirm_s"], event["event_end_s"], event["raw_frame_count"]) == (0., .2, .6, 7)
    event, = row["D1"]["result"]["events"]
    assert (event["onset_s"], event["confirm_s"], event["end_s"], event["members"]) == (0., .2, .6, 7)


@pytest.mark.parametrize("flag", ["identity_break", "observation_gap"])
def test_flag_is_preserved_without_hiding_endpoint_disagreement(probes, flag):
    row = probes[flag]
    assert sum(r[flag] is True for r in row["mapped_follower_clock"]) == 1
    native, = row["native"]["result"]
    formal, = row["formal_aligned"]["result"]
    d1, = row["D1"]["result"]["events"]
    assert native["event_start_s"] == d1["onset_s"] == .3
    assert native["event_confirm_s"] == d1["confirm_s"] == .5
    assert native["raw_frame_count"] == d1["members"] == 4
    assert (formal["event_start_s"], formal["event_confirm_s"], formal["raw_frame_count"]) == (.2, .4, 5)


@pytest.mark.parametrize("case", ["source_frame_discontinuity", "source_clock_discontinuity"])
def test_source_clock_evidence_is_not_certified_by_projection(probes, case):
    row = probes[case]
    assert row["native"]["result"][0]["event_start_s"] == .2
    assert row["D1"]["result"]["events"][0]["onset_s"] == .2
    assert row["formal_aligned"]["result"][0]["event_start_s"] == 0.
    assert [r["frame_id"] for r in row["mapped_follower_clock"]] == list(range(7))
    assert [r["global_time_ms"] for r in row["mapped_follower_clock"]] == list(range(0, 700, 100))


def test_leader_labels_do_not_substitute_for_formal_self_row_evidence(probes):
    row = probes["missing_leader_self_rows"]
    assert len(row["native"]["result"]) == 1
    assert len(row["D1"]["result"]["events"]) == 1
    assert row["formal_aligned"]["result"] == []


def test_unknown_flag_is_rejected_by_strict_interfaces(probes):
    row = probes["unknown_flag"]
    assert "observation_gap_must_be_explicit_boolean" in row["formal_aligned"]["error"]
    assert "unknown_boolean:observation_gap" in row["D1"]["error"]


def test_negative_premeasured_ttc_cannot_establish_equivalence(probes):
    row = probes["negative_ttc_premeasured"]
    assert len(row["native"]["result"]) == 1
    assert row["formal_aligned"]["error"] is not None
    assert row["D1"]["result"]["events"] == []


@pytest.mark.parametrize("name", ["native_lane_id_change_no_connection", "connected_road_boundary", "real_lane_change"])
def test_c_pair_event_does_not_require_same_lane_or_infer_physical_path(name):
    case = audit.task2.case_specs()[name]
    _, measured = audit.task2.build_case_frame(case, name)
    native, _ = audit.build_sumo_p2_events(measured)
    formal, _ = audit.extract_sumo_formal_p2_events(measured)
    d1 = audit.local_d1_measurement(measured, (0., 1.), strict=True)
    assert len(native) == len(formal) == 1
    assert formal.iloc[0].raw_frame_count == 5
    assert d1["local_evaluable_s"] == pytest.approx(.3)
    assert d1["formal_equivalence_accepted"] is False
    assert all(e["members"] < 5 for e in d1["events"])


@pytest.mark.parametrize("field,value", [("net_gap_m", -1.), ("leader_speed_mps", 13.)])
def test_producer_does_not_emit_finite_positive_closing_ttc_for_invalid_domain(field, value):
    measured = audit.probe_frame("normal")
    raw = measured.copy()
    raw.loc[raw.vehicle_id.eq("f"), field] = value
    produced = audit.compute_sumo_measurements(raw)
    follower = produced.loc[produced.vehicle_id.eq("f")]
    assert not follower.ttc_valid.any()
    assert follower.ttc_s.isna().all()
    assert audit.build_sumo_p2_events(produced)[0].empty
