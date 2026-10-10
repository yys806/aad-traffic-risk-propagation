from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from riskprop.ngsim_risk_calibration import (
    annotate_ngsim_trajectory_identity,
    _read_source,
    extract_rear_end_events,
    standardize_ngsim_states,
    write_stage_0_2_ngsim_package,
)


def _txt_source(tmp_path, text):
    path = tmp_path / "source.zip"
    inner_bytes = io.BytesIO()
    with zipfile.ZipFile(inner_bytes, "w") as inner:
        inner.writestr("window.txt", text)
    with zipfile.ZipFile(path, "w") as outer:
        outer.writestr("inner.zip", inner_bytes.getvalue())
    return path, {"inner_zip_member": "inner.zip", "trajectory_member": "window.txt",
                  "format": "ngsim_us101_txt_v1", "expected_rows": 2}


def test_txt_reader_keeps_first_row_maps_units_and_source(tmp_path):
    path, source = _txt_source(tmp_path,
        "10 1 1 1000 12 100 0 0 12 5 2 30 -2 2 20 0 30 1\n"
        "20 1 1 1000 12 130 0 0 15 5 2 20 0 2 0 10 0 0\n")
    raw = _read_source(path, source)
    assert len(raw) == 2
    assert raw.iloc[0]["Vehicle_ID"] == 10
    assert raw.iloc[0]["Preceeding"] == 20
    states = standardize_ngsim_states(raw, site="US-101", window_id="fixture")
    assert states.iloc[0]["net_gap_m"] == pytest.approx(15 * 0.3048)
    assert states.iloc[0]["speed_mps"] == pytest.approx(30 * 0.3048)
    assert states.iloc[0]["ttc_s"] == pytest.approx(1.5)
    assert states.iloc[0]["source_member"] == "window.txt"
    assert states.iloc[0]["source_format"] == "ngsim_us101_txt_v1"


@pytest.mark.parametrize("text", [
    "10 1 1 1000 12 100 0 0 12 5 2 30 -2 2 20 0 30\n",
    "10 1 1 1000 12 100 0 0 12 5 2 30 -2 2 20 0 30 1 99\n",
    "10 1 1 missing 12 100 0 0 12 5 2 30 -2 2 20 0 30 1\n",
])
def test_txt_reader_rejects_bad_structure_or_values(tmp_path, text):
    path, source = _txt_source(tmp_path, text)
    source.pop("expected_rows")
    with pytest.raises(ValueError):
        _read_source(path, source)


def test_txt_reader_stops_on_expected_row_mismatch(tmp_path):
    path, source = _txt_source(tmp_path,
        "10 1 1 1000 12 100 0 0 12 5 2 30 -2 2 20 0 30 1\n")
    with pytest.raises(ValueError, match="expected.*2.*read.*1"):
        _read_source(path, source)


def _ngsim_rows() -> pd.DataFrame:
    rows = []
    for frame, time_ms, follower_speed in ((1, 1000, 30.0), (2, 1100, 29.0), (3, 1200, 28.0)):
        rows.extend(
            [
                {
                    "Vehicle_ID": 10,
                    "Frame_ID": frame,
                    "Global_Time": time_ms,
                    "Local_X": 12.0,
                    "Local_Y": 100.0 + frame,
                    "v_Length": 12.0,
                    "v_Vel": follower_speed,
                    "v_Acc": -2.0,
                    "Lane_ID": 2,
                    "Preceeding": 20,
                    "Space_Hdwy": 20.0,
                },
                {
                    "Vehicle_ID": 20,
                    "Frame_ID": frame,
                    "Global_Time": time_ms,
                    "Local_X": 12.1,
                    "Local_Y": 120.0 + frame,
                    "v_Length": 15.0,
                    "v_Vel": 20.0,
                    "v_Acc": 0.0,
                    "Lane_ID": 2,
                    "Preceeding": 0,
                    "Space_Hdwy": 0.0,
                },
            ]
        )
    return pd.DataFrame(rows)


def test_standardize_ngsim_state_preserves_raw_and_si_fields() -> None:
    states = standardize_ngsim_states(
        _ngsim_rows(), site="US-101", window_id="0750_0805"
    )
    follower = states[states["vehicle_id"] == "10"].iloc[0]
    assert follower["dataset"] == "NGSIM"
    assert follower["raw_speed_fps"] == pytest.approx(30.0)
    assert follower["speed_mps"] == pytest.approx(30.0 * 0.3048)
    assert follower["net_gap_m"] == pytest.approx(5.0 * 0.3048)
    assert follower["measurement_status"] == "valid"


def test_rear_end_events_merge_frames_and_never_count_frames_as_events() -> None:
    states = standardize_ngsim_states(
        _ngsim_rows(), site="US-101", window_id="0750_0805"
    )
    events = extract_rear_end_events(
        states, provisional_ttc_threshold_s=3.0, max_gap_s=0.11, minimum_duration_s=0.1
    )
    assert len(events) == 1
    assert events.iloc[0]["raw_frame_count"] == 3
    assert events.iloc[0]["event_duration_s"] == pytest.approx(0.2)
    assert events.iloc[0]["conflict_type"] == "rear_end"
    assert events.iloc[0]["inclusion_status"] == "calibration_candidate"


def test_lankershim_spelling_is_supported() -> None:
    rows = _ngsim_rows().rename(
        columns={"v_Length": "v_length", "Preceeding": "Preceding", "Space_Hdwy": "Space_Headway"}
    )
    result = standardize_ngsim_states(rows, site="Lankershim", window_id="all")
    assert result["leader_id"].notna().any()


def test_identity_annotation_preserves_rows_and_marks_frame_reset() -> None:
    rows = _ngsim_rows().iloc[:4].copy()
    rows.loc[2, "Frame_ID"] = 1
    annotated = annotate_ngsim_trajectory_identity(
        rows, site="Lankershim", source_period="unknown", source_member="merged.csv"
    )
    assert len(annotated) == len(rows)
    assert annotated["original_row_number"].tolist() == [1, 2, 3, 4]
    assert annotated["identity_break"].sum() == 1
    assert annotated.loc[2, "segment_index"] == 1
    assert annotated["trajectory_id"].nunique() == 3


def test_events_do_not_merge_across_trajectory_segments_at_adjacent_frames() -> None:
    rows = _ngsim_rows().copy()
    follower = rows[rows["Vehicle_ID"] == 10].copy()
    follower.loc[follower.index[2], "Frame_ID"] = 1
    rows = pd.concat([follower, rows[rows["Vehicle_ID"] == 20]], ignore_index=True)
    states = standardize_ngsim_states(rows, site="Lankershim", window_id="all")
    events = extract_rear_end_events(
        states, provisional_ttc_threshold_s=3.0, max_gap_s=0.11, minimum_duration_s=0.1
    )
    assert len(events) == 1
    assert events.iloc[0]["raw_frame_count"] == 2
    assert events.iloc[0]["event_duration_s"] == pytest.approx(0.1)


def test_event_reliability_filters_uncertain_frames_but_preserves_raw_candidates() -> None:
    states = standardize_ngsim_states(
        _ngsim_rows(), site="Lankershim", window_id="all"
    )
    states.loc[states["vehicle_id"] == "10", "identity_uncertain"] = True
    raw_events, reliable_events, rejected = extract_rear_end_events(
        states,
        provisional_ttc_threshold_s=3.0,
        max_gap_s=0.11,
        minimum_duration_s=0.1,
        return_diagnostics=True,
    )
    assert len(raw_events) == 1
    assert len(reliable_events) == 0
    assert len(rejected) == 1
    assert rejected.iloc[0]["rejection_reason"] == "identity_uncertain"


def test_event_reliability_rejects_uncertain_leader_identity() -> None:
    raw = annotate_ngsim_trajectory_identity(_ngsim_rows(), site="Lankershim")
    raw.loc[raw["Vehicle_ID"] == 20, "identity_uncertain"] = True
    states = standardize_ngsim_states(raw, site="Lankershim", window_id="all")
    _, reliable_events, rejected = extract_rear_end_events(
        states, provisional_ttc_threshold_s=3.0, return_diagnostics=True
    )
    assert reliable_events.empty
    assert rejected["rejection_reason"].eq("leader_identity_uncertain").any()


def test_clock_identity_recovers_interleaved_continuous_sequences():
    raw = _ngsim_rows()
    second = raw.copy()
    second["Global_Time"] += 10000
    second["Total_Frames"] = 3
    raw["Total_Frames"] = 3
    interleaved = pd.concat([raw.iloc[:2], second.iloc[:2], raw.iloc[2:], second.iloc[2:]], ignore_index=True)
    a = annotate_ngsim_trajectory_identity(interleaved, site="Lankershim")
    assert a["trajectory_id"].nunique() == 4
    assert not a["identity_uncertain"].any()
    assert not a["observation_gap"].any()
    assert a["original_row_number"].tolist() == list(range(1, 13))


def test_first_uncertain_frame_rejects_whole_candidate_event():
    states = standardize_ngsim_states(_ngsim_rows(), site="Lankershim", window_id="all")
    states.loc[0, "identity_uncertain"] = True
    raw, reliable, rejected = extract_rear_end_events(states, return_diagnostics=True)
    assert len(raw) == 1 and reliable.empty
    assert rejected.iloc[0].rejection_reason == "identity_uncertain"


def test_gap_after_first_event_allows_new_event_and_keeps_measurement():
    raw = _ngsim_rows()
    after = raw.copy()
    after["Frame_ID"] += 5
    after["Global_Time"] += 500
    states = standardize_ngsim_states(pd.concat([raw, after], ignore_index=True), site="US-101", window_id="all")
    candidates, reliable, rejected = extract_rear_end_events(states, return_diagnostics=True)
    assert len(candidates) == len(reliable) == 2
    assert rejected.empty
    assert states["observation_gap"].sum() == 2
    assert states["ttc_valid"].sum() == 6


def test_full_sequence_blocks_intervening_observation_even_with_large_max_gap():
    states = standardize_ngsim_states(_ngsim_rows(), site="US-101", window_id="all")
    states.loc[2, "ttc_valid"] = False
    raw, reliable, rejected = extract_rear_end_events(states, max_gap_s=1, return_diagnostics=True)
    assert len(raw) == 1 and reliable.empty
    assert "intervening_non_candidate_observation" in rejected.iloc[0].rejection_reason


def test_conflicting_duplicate_frame_marks_entire_sequence_without_dropping_rows():
    raw = _ngsim_rows()
    duplicate = raw.iloc[[2]].copy()
    duplicate["v_Vel"] = 99
    a = annotate_ngsim_trajectory_identity(pd.concat([raw, duplicate], ignore_index=True), site="US-101")
    assert len(a) == 7
    assert a.loc[a.Vehicle_ID.eq(10), "identity_uncertain"].all()
    states = standardize_ngsim_states(a, site="US-101", window_id="all")
    assert not states.loc[states.vehicle_id.eq("10"), "single_frame_reliable"].any()


def test_same_time_different_source_members_never_cross_match():
    raw = _ngsim_rows().iloc[:2].copy()
    raw["source_member"] = ["one.csv", "two.csv"]
    from riskprop.real_trajectory import add_ngsim_leader_ttc
    result = add_ngsim_leader_ttc(raw)
    assert not result.iloc[0].ttc_valid


def test_same_time_reused_ids_match_only_same_clock_and_frame():
    from riskprop.real_trajectory import add_ngsim_leader_ttc
    rows = []
    for frame, anchor in ((1, 0), (2, -100)):
        rows.extend([
            {"Vehicle_ID": 10, "Frame_ID": frame, "Global_Time": 1000, "diagnostic_clock_anchor_ms": anchor,
             "trajectory_id": f"follower-{anchor}", "v_Length": 12.0, "v_Vel": 30.0,
             "Preceeding": 20, "Space_Hdwy": 30.0},
            {"Vehicle_ID": 20, "Frame_ID": frame, "Global_Time": 1000, "diagnostic_clock_anchor_ms": anchor,
             "trajectory_id": f"leader-{anchor}", "v_Length": 15.0, "v_Vel": 20.0,
             "Preceeding": 0, "Space_Hdwy": 0.0},
        ])
    result = add_ngsim_leader_ttc(pd.DataFrame(rows))
    followers = result[result.Vehicle_ID.eq(10)].sort_values("Frame_ID")
    assert followers.leader_matched.all()
    assert followers.leader_trajectory_id.tolist() == ["leader-0", "leader--100"]
    assert followers.ttc_valid.all()


def test_same_clock_time_with_different_frame_does_not_match():
    from riskprop.real_trajectory import add_ngsim_leader_ttc
    raw = pd.DataFrame([
        {"Vehicle_ID": 10, "Frame_ID": 1, "Global_Time": 1000, "diagnostic_clock_anchor_ms": 0,
         "trajectory_id": "follower", "v_Length": 12.0, "v_Vel": 30.0, "Preceeding": 20, "Space_Hdwy": 30.0},
        {"Vehicle_ID": 20, "Frame_ID": 2, "Global_Time": 1000, "diagnostic_clock_anchor_ms": 0,
         "trajectory_id": "leader", "v_Length": 15.0, "v_Vel": 20.0, "Preceeding": 0, "Space_Hdwy": 0.0},
    ])
    result = add_ngsim_leader_ttc(raw)
    assert not result.iloc[0].leader_matched
    assert result.iloc[0].missing_reason == "leader_not_matched"


def test_missing_diagnostic_match_fields_are_not_guessed():
    from riskprop.real_trajectory import add_ngsim_leader_ttc
    raw = pd.DataFrame([
        {"Vehicle_ID": 10, "Frame_ID": 1, "Global_Time": 1000, "diagnostic_clock_anchor_ms": pd.NA,
         "trajectory_id": "follower", "v_Length": 12.0, "v_Vel": 30.0, "Preceeding": 20, "Space_Hdwy": 30.0},
        {"Vehicle_ID": 20, "Frame_ID": 1, "Global_Time": 1000, "diagnostic_clock_anchor_ms": 0,
         "trajectory_id": "leader", "v_Length": 15.0, "v_Vel": 20.0, "Preceeding": 0, "Space_Hdwy": 0.0},
    ])
    result = add_ngsim_leader_ttc(raw)
    assert not result.iloc[0].leader_matched
    assert result.iloc[0].missing_reason == "leader_not_matched"


@pytest.mark.parametrize("gap_ms", [200, 300, 5000])
def test_missing_frames_are_observation_gaps_not_new_physical_identity(gap_ms):
    raw = _ngsim_rows()
    raw.loc[raw.Frame_ID.ge(2), "Global_Time"] += gap_ms - 100
    raw.loc[raw.Frame_ID.ge(2), "Frame_ID"] += gap_ms // 100 - 1
    states = standardize_ngsim_states(raw, site="US-101", window_id="all")
    assert states.trajectory_id.nunique() == 2
    assert states.observation_gap.sum() == 2
    assert not states.identity_uncertain.any()
    events = extract_rear_end_events(states)
    assert len(events) == 1
    assert events.iloc[0].raw_frame_count == 2


def test_total_frames_conflict_propagates_to_whole_sequence():
    raw = _ngsim_rows()
    raw["Total_Frames"] = 3
    raw.loc[2, "Total_Frames"] = 4
    states = standardize_ngsim_states(raw, site="US-101", window_id="all")
    assert states.loc[states.vehicle_id.eq("10"), "identity_uncertain"].all()
    assert states.ttc_valid.sum() == 3
    assert not states.single_frame_reliable.any()
    assert extract_rear_end_events(states).empty


def test_normal_leader_change_flags_are_not_identity_string_comparisons():
    states = standardize_ngsim_states(_ngsim_rows(), site="US-101", window_id="all")
    assert not states.leader_changed.any()
    assert states.trajectory_boundary.sum() == 4


def test_duplicate_leader_at_same_time_is_missing_and_never_arbitrarily_selected():
    raw = _ngsim_rows()
    raw = pd.concat([raw, raw.iloc[[1]]], ignore_index=True)
    states = standardize_ngsim_states(raw, site="US-101", window_id="all")
    assert len(states) == 7
    assert not states.iloc[0].ttc_valid
    assert states.iloc[0].missing_reason == "leader_not_matched"
    assert states.iloc[0].leader_identity_uncertain


def test_stage_0_2_package_reads_only_requested_calibration_member(tmp_path: Path) -> None:
    source = tmp_path / "ngsim.zip"
    csv_bytes = _ngsim_rows().to_csv(index=False).encode()
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, "w") as inner:
        inner.writestr("window/trajectories.csv", csv_bytes)
    with zipfile.ZipFile(source, "w") as outer:
        outer.writestr("trajectories.zip", nested.getvalue())

    output = write_stage_0_2_ngsim_package(
        output_dir=tmp_path / "out",
        sources=[
            {
                "asset_id": "ngsim_us101",
                "site": "US-101",
                "path": source,
                "inner_zip_member": "trajectories.zip",
                "csv_member": "window/trajectories.csv",
                "window_id": "fixture",
            }
        ],
        provisional_ttc_threshold_s=3.0,
    )
    assert (output / "states" / "ngsim_us101__fixture.parquet").is_file()
    assert (output / "risk_events.parquet").is_file()
    written_states = pd.read_parquet(output / "states/ngsim_us101__fixture.parquet")
    assert written_states.source_period.eq("unknown").all()
    assert (output / "audit.json").is_file()
    assert (output / "SHA256SUMS").is_file()
    audit = pd.read_json(output / "audit.json", typ="series")
    assert audit["scientific_claim_eligible"] is False
    assert audit["locked_holdout_opened"] is False
    assert audit["gate_status"] == "active_audit_closure"
