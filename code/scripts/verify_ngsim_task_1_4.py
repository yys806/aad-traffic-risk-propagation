"""Task 1.4 engineering regression; only explicit NGSIM calibration members.

No download, holdout access, risk quantiles or scientific threshold selection.
Historical functions are loaded from the fixed Task 1.3 commit solely to
measure before/after behavior; no parallel production pipeline is installed.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))
from riskprop.calibration import validate_checksum_package
from riskprop.ngsim_risk_calibration import (
    _read_source, _seal_directory, annotate_ngsim_trajectory_identity,
    extract_rear_end_events, standardize_ngsim_states, write_stage_0_2_ngsim_package,
)

BASELINE = "da4072909a93c16e96e89fa436fd23127a581b69"


def fingerprint(frame: pd.DataFrame) -> str:
    # Parquet object lists are serialized separately; scalar core columns only.
    cols = [c for c in frame if c != "original_row_numbers"]
    digest = hashlib.sha256(pd.util.hash_pandas_object(frame[cols], index=False).values.tobytes())
    return digest.hexdigest()


def sources(root: Path) -> list[dict]:
    data = root / "dataset" / "NGSIM"
    result = []
    for window, count in (("0750am-0805am", 1180598), ("0805am-0820am", 1403095), ("0820am-0835am", 1515240)):
        result.append(dict(asset_id="ngsim_us101", site="US-101", path=data / "US-101-LosAngeles-CA.zip",
                           inner_zip_member="us-101-vehicle-trajectory-data.zip",
                           trajectory_member=f"vehicle-trajectory-data/{window}/trajectories-{window}.txt",
                           format="ngsim_us101_txt_v1", expected_rows=count, source_period=window,
                           window_id=window.replace("am-", "_").replace("am", "")))
    result.append(dict(asset_id="ngsim_lankershim", site="Lankershim", path=data / "Lankershim-Boulevard-LosAngeles-CA.zip",
                       csv_member="NGSIM__Lankershim_Vehicle_Trajectories.csv", source_period="unknown", window_id="complete"))
    return result


def baseline_functions(root: Path) -> dict:
    ns = {"__name__": "task_1_3_historical_regression"}
    def code(path):
        return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=root).decode("utf-8")
    exec(compile(code("code/src/riskprop/real_trajectory.py"), "historical_real_trajectory", "exec"), ns)
    old_ttc = ns["add_ngsim_leader_ttc"]
    exec(compile(code("code/src/riskprop/ngsim_risk_calibration.py"), "historical_ngsim", "exec"), ns)
    ns["add_ngsim_leader_ttc"] = old_ttc
    return ns


def write_identity_evidence(output: Path, states: pd.DataFrame, table: pd.DataFrame) -> None:
    """Export aggregate crosschecks and small sequence-boundary examples only."""
    cross = table.groupby(["total_anomaly", "row_order_frame_reset", "row_order_time_backwards"]).size().reset_index(name="vehicle_ids")
    clocks = states.groupby("diagnostic_clock_anchor_ms").agg(
        rows=("frame_id", "size"), vehicles=("vehicle_id", "nunique"),
        min_time_ms=("global_time_ms", "min"), max_time_ms=("global_time_ms", "max"),
    ).reset_index()
    examples = []
    for vehicle in ("75", "80", "88", "91", "207"):
        for _, group in states[states.vehicle_id.eq(vehicle)].groupby("trajectory_id"):
            examples.append(dict(vehicle_id=vehicle, clock_anchor_ms=int(group.diagnostic_clock_anchor_ms.iloc[0]),
                rows=len(group), total_frames=int(group.total_frames.iloc[0]),
                min_frame=int(group.frame_id.min()), max_frame=int(group.frame_id.max()),
                first_original_row=int(group.original_row_number.min()), last_original_row=int(group.original_row_number.max()),
                min_time_ms=int(group.global_time_ms.min()), max_time_ms=int(group.global_time_ms.max())))
    result = dict(crosscheck=cross.to_dict("records"), clock_time_coverage=clocks.to_dict("records"), examples=examples,
        low_ttc_frames=int((states.ttc_valid & states.ttc_s.lt(2)).sum()),
        leader_matched_rows=int(states.leader_matched.sum()), identity_checked_rows=int((~states.identity_uncertain).sum()),
        single_frame_loss_due_to_identity=int((states.ttc_valid & (states.identity_uncertain | states.leader_identity_uncertain)).sum()))
    (output / "identity_evidence.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def write_event_boundary_evidence(output: Path, old_events: pd.DataFrame, new_events: pd.DataFrame,
                                  old_core: pd.DataFrame, current: pd.DataFrame) -> None:
    columns = ["vehicle_id", "leader_id", "event_start_s", "event_end_s", "raw_frame_count"]
    old_keys = set(old_events[columns].itertuples(index=False, name=None))
    new_keys = set(new_events[columns].itertuples(index=False, name=None))
    changed_old = old_events[[r not in new_keys for r in old_events[columns].itertuples(index=False, name=None)]]
    changed_new = new_events[[r not in old_keys for r in new_events[columns].itertuples(index=False, name=None)]]
    links = []
    for _, row in changed_new.iterrows():
        previous = changed_old[changed_old.vehicle_id.eq(row.vehicle_id) & changed_old.leader_id.eq(row.leader_id)
            & changed_old.event_start_s.le(row.event_end_s) & changed_old.event_end_s.ge(row.event_start_s)]
        links.append(dict(vehicle_id=str(row.vehicle_id), leader_id=str(row.leader_id),
            new_start=float(row.event_start_s), new_end=float(row.event_end_s), new_frames=int(row.raw_frame_count),
            old_events=len(previous), old_frames=int(previous.raw_frame_count.sum()),
            old_intervals=previous[["event_start_s", "event_end_s", "raw_frame_count"]].to_dict("records")))
    bits = {}
    for column in ("ttc_s", "drac_mps2", "net_gap_m", "closing_speed_mps"):
        different = old_core[column].to_numpy().view("uint64") != current[column].to_numpy().view("uint64")
        bits[column] = dict(rows=int(different.sum()), all_nan=bool((old_core[column].isna() & current[column].isna())[different].all()))
    result = dict(unchanged_boundaries=len(old_keys & new_keys), old_changed=len(changed_old),
        new_changed=len(changed_new), changed_event_components=links, float_bit_differences=bits)
    (output / "event_boundary_comparison.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume-validation", action="store_true", help="Validate an already written package without rewriting its states/events")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    source_list = sources(root)
    start = time.perf_counter()
    # Baseline run with identical local Lankershim source, fixed historical code.
    raw = _read_source(source_list[-1]["path"], source_list[-1])
    old = baseline_functions(root)
    old_states = old["standardize_ngsim_states"](raw, site="Lankershim", window_id="complete", source_member=source_list[-1]["csv_member"])
    old_events = old["extract_rear_end_events"](old_states)
    core = ["vehicle_id", "time_s", "net_gap_m", "closing_speed_mps", "ttc_valid", "ttc_s", "drac_mps2", "measurement_status", "missing_reason"]
    before = {"events": len(old_events), "state_core_sha256": fingerprint(old_states[core]),
              "uncertain_rows": int(old_states.identity_uncertain.sum()), "segments": int(old_states.trajectory_id.nunique())}
    old_core = old_states[core].copy()
    event_core = ["vehicle_id", "leader_id", "event_start_s", "event_end_s", "raw_frame_count"]
    old_event_core = old_events[event_core].copy()
    old_event_keys = set(old_events[event_core].itertuples(index=False, name=None))
    del raw, old_states, old_events, old
    gc.collect()
    if not args.resume_validation:
        write_stage_0_2_ngsim_package(output_dir=args.output, sources=source_list)
    output = args.output
    comparison = {"baseline_commit": BASELINE, "lankershim_before": before, "us101": []}
    for source in source_list[:-1]:
        name = f"ngsim_us101__{source['window_id']}.parquet"
        current = pd.read_parquet(output / "states" / name)
        previous = pd.read_parquet(root / "code/outputs/formal/calibration/stage_0_2_task_1_3_us101_txt_20261010_r2/states" / name)
        equal = current[core].equals(previous[core])
        assert equal, f"US-101 core measurement changed: {name}"
        comparison["us101"].append({"window": source["window_id"], "rows": len(current), "core_equal_task_1_3": equal,
                                    "state_core_sha256": fingerprint(current[core])})
        del current, previous
        gc.collect()
    current = pd.read_parquet(output / "states/ngsim_lankershim__complete.parquet")
    measurement_comparison = {
        c: dict(different_rows=int((~(old_core[c].eq(current[c]) | (old_core[c].isna() & current[c].isna())).fillna(False)).sum()),
                before_dtype=str(old_core[c].dtype), after_dtype=str(current[c].dtype)) for c in core
    }
    assert all(item["different_rows"] == 0 for item in measurement_comparison.values()), "single-frame regression"
    (output / "measurement_comparison.json").write_text(json.dumps(measurement_comparison, indent=2) + "\n", encoding="utf-8")
    raw = _read_source(source_list[-1]["path"], source_list[-1])
    g = raw.groupby("Vehicle_ID")
    table = g.agg(rows=("Frame_ID", "size"), total_values=("Total_Frames", "nunique"), total_first=("Total_Frames", "first"))
    table["total_anomaly"] = table.total_values.gt(1) | table.rows.ne(table.total_first)
    df = g.Frame_ID.diff()
    dt = g.Global_Time.diff()
    table["row_order_frame_reset"] = df.le(0).groupby(raw.Vehicle_ID).any()
    table["row_order_time_backwards"] = dt.le(0).groupby(raw.Vehicle_ID).any()
    a = annotate_ngsim_trajectory_identity(raw, site="Lankershim", source_member=source_list[-1]["csv_member"])
    table["clock_sequences"] = a.groupby("Vehicle_ID").trajectory_id.nunique()
    table.to_csv(output / "vehicle_crosscheck.csv")  # local per-ID diagnostic, never portable
    groups = a.groupby("trajectory_id")
    seq = groups.agg(rows=("Frame_ID", "size"), total_values=("Total_Frames", "nunique"), total_first=("Total_Frames", "first"),
                     min_frame=("Frame_ID", "min"), max_frame=("Frame_ID", "max"))
    assert len(raw) == len(current) == 1607319
    assert current.original_row_number.tolist() == list(range(1, len(current) + 1))
    assert seq.total_values.eq(1).all() and seq.rows.eq(seq.total_first).all()
    assert seq.rows.eq(seq.max_frame - seq.min_frame + 1).all()
    repeat = standardize_ngsim_states(raw, site="Lankershim", window_id="complete", source_member=source_list[-1]["csv_member"])
    assert current.equals(repeat), "repeat state differs"
    events = extract_rear_end_events(repeat, return_diagnostics=True)
    for name, frame in zip(("risk_events", "reliable_risk_events", "rejected_risk_events"), events):
        saved = pd.read_parquet(output / f"{name}.parquet")
        if "site" in saved:
            saved = saved[saved.site.eq("Lankershim")]
        else:
            saved = saved[saved.event_id.isin(events[0].event_id)]
        assert fingerprint(saved) == fingerprint(frame), f"repeat event differs: {name}"
        if "original_row_numbers" in frame:
            assert [list(x) for x in saved.original_row_numbers] == frame.original_row_numbers.tolist(), f"row provenance differs: {name}"
    comparison["lankershim_after"] = {
        "state_core_sha256": fingerprint(current[core]), "core_equal_task_1_3": old_core.equals(current[core]),
        "serialized_core_fingerprint_equal": before["state_core_sha256"] == fingerprint(current[core]),
        "repeat_state_equal": True, "repeat_event_equal": True, "raw_rows": len(raw), "vehicles": len(table),
        "total_anomaly_ids": int(table.total_anomaly.sum()), "multiple_total_ids": int(table.total_values.gt(1).sum()),
        "anomaly_with_old_frame_reset": int((table.total_anomaly & table.row_order_frame_reset).sum()),
        "anomaly_without_old_frame_reset": int((table.total_anomaly & ~table.row_order_frame_reset).sum()),
        "old_time_backwards_ids": int(table.row_order_time_backwards.sum()), "old_frame_reset_ids": int(table.row_order_frame_reset.sum()),
        "multiple_clock_ids": int(table.clock_sequences.gt(1).sum()), "segments": len(seq),
        "sequence_total_or_span_mismatches": 0, "same_vehicle_time_conflict_rows": int(raw.duplicated(["Vehicle_ID", "Global_Time"], False).sum()),
        "clock_anchor_rows": {str(k): int(v) for k, v in a.diagnostic_clock_anchor_ms.value_counts().items()},
        "record_uncertain_rows": int(current.identity_uncertain_record.sum()), "sequence_uncertain_rows": int(current.identity_uncertain.sum()),
        "leader_uncertain_valid_ttc_rows": int((current.ttc_valid & current.leader_identity_uncertain).sum()),
        "single_frame_reliable_rows": int(current.single_frame_reliable.sum()),
        "sorted_sequence_observation_gaps": int(current.observation_gap.sum()),
        "candidate_events": len(events[0]), "reliable_events": len(events[1]), "rejected_events": len(events[2]),
        "rejection_reasons": {str(k): int(v) for k, v in events[2].rejection_reason.value_counts().items()},
        "reliable_event_frame_rows": int(events[1].raw_frame_count.sum()),
        "unchanged_event_boundaries": len(old_event_keys & set(events[0][event_core].itertuples(index=False, name=None))),
    }
    comparison["wall_seconds"] = time.perf_counter() - start
    comparison["run_mode"] = "resume_validation" if args.resume_validation else "full_pipeline_and_validation"
    write_identity_evidence(output, current, table.reset_index())
    write_event_boundary_evidence(output, old_event_core, events[0], old_core, current)
    (output / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    provenance_path = output / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["git_base_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    provenance["implementation_sha256"] = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in (
        "code/src/riskprop/ngsim_risk_calibration.py", "code/src/riskprop/real_trajectory.py", "code/scripts/verify_ngsim_task_1_4.py")}
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _seal_directory(output)
    validate_checksum_package(output)
    print(json.dumps(comparison, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
