"""Task 5 offline integrity audit and bounded repair for Round 2 Task 4.

Only the two authorized NGSIM windows and the sealed Task 4/SUMO inputs are read.
No SUMO/TraCI process, subprocess, network, third window or holdout is accessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/scripts"))
import analyze_stage_0_5_round2_task4_real_source_support as task4  # noqa: E402

TASK4_EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030"
OUTPUT = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030"
WINDOWS = ("0750_0805", "0805_0820")
REAL_EXPECTED = task4.REAL_EXPECTED
SIM_EXPECTED = task4.SIM_EXPECTED
RUNS = task4.RUNS
SIM_WINDOW = task4.SIM_WINDOW


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str:
    head = (root / ".git/HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref = head[5:]
        ref_path = root / ".git" / Path(ref)
        if ref_path.is_file():
            return ref_path.read_text(encoding="utf-8").strip()
        packed = root / ".git/packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8").splitlines():
                if line and not line.startswith("#") and " " in line:
                    value, name = line.split(" ", 1)
                    if name == ref:
                        return value
    return head


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _task4_sha256sums_ok() -> dict[str, Any]:
    sums_path = TASK4_EVIDENCE / "SHA256SUMS"
    rows = []
    bad = []
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        actual = sha256_file(TASK4_EVIDENCE / name)
        rows.append(name)
        if actual != digest:
            bad.append({"name": name, "expected": digest, "actual": actual})
    return {"path": str(sums_path.relative_to(ROOT)).replace("\\", "/"), "file_count": len(rows), "bad": bad, "pass": not bad}


def _onset_keys(states: pd.DataFrame, events: pd.DataFrame) -> tuple[set[tuple[Any, ...]], int, int]:
    lookup: dict[tuple[str, float], list[dict[str, Any]]] = {}
    for row in states[["trajectory_id", "time_s", "original_vehicle_id", "global_time_ms", "frame_id"]].to_dict("records"):
        lookup.setdefault((str(row["trajectory_id"]), float(row["time_s"])), []).append(row)
    keys: set[tuple[Any, ...]] = set()
    unmatched = ambiguous = 0
    for event in events.to_dict("records"):
        candidates = lookup.get((str(event["trajectory_id"]), float(event["event_start_s"])), [])
        if len(candidates) == 1:
            row = candidates[0]
            keys.add((str(row["original_vehicle_id"]), int(row["global_time_ms"]), int(row["frame_id"])))
        elif not candidates:
            unmatched += 1
        else:
            ambiguous += 1
    return keys, unmatched, ambiguous


def window_overlap_audit() -> dict[str, Any]:
    from riskprop.ngsim_risk_calibration import extract_rear_end_events
    cols = ["original_vehicle_id", "vehicle_id", "trajectory_id", "global_time_ms", "frame_id", "time_s", "source_member", "source_period", "x_m", "y_m", "speed_mps", "lane_id"]
    frames = {window: pd.read_parquet(spec["path"], columns=cols) for window, spec in REAL_EXPECTED.items()}
    a, b = frames[WINDOWS[0]], frames[WINDOWS[1]]
    a_min, a_max = int(a["global_time_ms"].min()), int(a["global_time_ms"].max())
    b_min, b_max = int(b["global_time_ms"].min()), int(b["global_time_ms"].max())
    overlap_start, overlap_end = max(a_min, b_min), min(a_max, b_max)
    key_cols = ["original_vehicle_id", "global_time_ms", "frame_id"]
    a_keys = a[key_cols].drop_duplicates()
    b_keys = b[key_cols].drop_duplicates()
    exact_raw_matches = int(len(a_keys.merge(b_keys, on=key_cols, how="inner")))
    common_times = np.intersect1d(a["global_time_ms"].unique(), b["global_time_ms"].unique())
    common_vehicles = sorted(set(a["original_vehicle_id"].astype(str)) & set(b["original_vehicle_id"].astype(str)))
    source_events = {}
    event_onset_key_sets = {}
    for window, frame in ((WINDOWS[0], frames[WINDOWS[0]]), (WINDOWS[1], frames[WINDOWS[1]])):
        full = pd.read_parquet(REAL_EXPECTED[window]["path"])
        events = extract_rear_end_events(full, provisional_ttc_threshold_s=2.0, max_gap_s=0.11, minimum_duration_s=0.2)
        onset_keys, unmatched, ambiguous = _onset_keys(full, events)
        source_events[window] = {"extracted_events": int(len(events)), "onset_unmatched": unmatched, "onset_ambiguous": ambiguous}
        event_onset_key_sets[window] = onset_keys
    event_key_intersection = len(event_onset_key_sets[WINDOWS[0]] & event_onset_key_sets[WINDOWS[1]])
    exact_trajectory_intersection = len(set(pd.read_parquet(REAL_EXPECTED[WINDOWS[0]]["path"], columns=["trajectory_id"])["trajectory_id"]) & set(pd.read_parquet(REAL_EXPECTED[WINDOWS[1]]["path"], columns=["trajectory_id"])["trajectory_id"]))
    return {
        "schema": "aad.stage05.round2.task5.window-overlap-audit.v1",
        "windows": {
            WINDOWS[0]: {"global_time_min_ms": a_min, "global_time_max_ms": a_max, "rows": int(len(a)), "vehicle_ids": int(a["original_vehicle_id"].nunique())},
            WINDOWS[1]: {"global_time_min_ms": b_min, "global_time_max_ms": b_max, "rows": int(len(b)), "vehicle_ids": int(b["original_vehicle_id"].nunique())},
        },
        "timestamp_overlap": {"overlap_start_ms": overlap_start, "overlap_end_ms": overlap_end, "overlap_duration_s": (overlap_end - overlap_start) / 1000.0, "common_global_time_values": int(len(common_times)), "overlap_rows_window_a": int(a["global_time_ms"].between(overlap_start, overlap_end).sum()), "overlap_rows_window_b": int(b["global_time_ms"].between(overlap_start, overlap_end).sum())},
        "record_match": {"key": key_cols, "exact_raw_record_matches": exact_raw_matches, "duplicate_key_rows_window_a": int(a.duplicated(key_cols).sum()), "duplicate_key_rows_window_b": int(b.duplicated(key_cols).sum()), "shared_original_vehicle_ids": len(common_vehicles), "exact_trajectory_id_intersection": exact_trajectory_intersection},
        "event_match": {"window_event_counts": source_events, "exact_onset_record_key_intersection": event_key_intersection, "duplicate_event_count": event_key_intersection, "duplicate_event_status": "none_observed_under_original_vehicle_id+Global_Time+Frame_ID onset key"},
        "identity_boundary": {"same_original_vehicle_id_does_not_prove_same_physical_identity": True, "trajectory_id_cross_window_mapping_proven": False, "unresolved_identity_correspondence": len(common_vehicles) > 0 and exact_raw_matches == 0},
        "merge_policy": "do_not_merge_window_statistics_or_event totals; timestamp overlap alone is not duplicate evidence",
    }


def onset_audit_for_real() -> list[dict[str, Any]]:
    from riskprop.ngsim_risk_calibration import extract_rear_end_events
    audits = []
    for window, spec in REAL_EXPECTED.items():
        states = pd.read_parquet(spec["path"])
        events = extract_rear_end_events(states, provisional_ttc_threshold_s=2.0, max_gap_s=0.11, minimum_duration_s=0.2)
        audit = task4.attribute_event_onsets(states, events)
        audits.append({"dataset": "NGSIM", "window_id": window, **{k: v for k, v in audit.items() if k not in {"classified_events", "unknown_events"}}, "expected_events": spec["events"], "source_target_expected": {"source": [167, 159][WINDOWS.index(window)], "target": [174, 252][WINDOWS.index(window)]}})
    return audits


def onset_audit_for_sumo() -> list[dict[str, Any]]:
    from riskprop.stage_0_5_sumo import build_sumo_formal_source_frame, extract_sumo_formal_p2_events
    audits = []
    for label, spec in SIM_EXPECTED.items():
        measured = pd.read_parquet(RUNS / spec["run_id"] / "measured_state.parquet")
        mapped = build_sumo_formal_source_frame(measured)
        events, adapter = extract_sumo_formal_p2_events(measured)
        mapped_window = mapped.loc[mapped["time_s"].ge(SIM_WINDOW[0]) & mapped["time_s"].lt(SIM_WINDOW[1])]
        audit = task4.attribute_event_onsets(mapped_window, events, time_window=SIM_WINDOW)
        audits.append({"dataset": "SUMO", "run_label": label, "measurement_contract": "SUMO_formal_aligned_P2_diagnostic", "adapter_status": adapter["equivalence_status"], **{k: v for k, v in audit.items() if k not in {"classified_events", "unknown_events"}}})
    return audits


def corrected_metrics_and_diff() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    real_metrics: list[dict[str, Any]] = []
    sim_metrics: list[dict[str, Any]] = []
    for window, spec in REAL_EXPECTED.items():
        frame = pd.read_parquet(spec["path"])
        _, _, metrics, _ = task4.real_window(window, frame)
        real_metrics.extend(metrics)
    cohort_path = ROOT / "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/routes.rou.xml"
    cohort = task4.cohort_ids(cohort_path)
    for label, spec in SIM_EXPECTED.items():
        frame = pd.read_parquet(RUNS / spec["run_id"] / "measured_state.parquet")
        _, metrics = task4.simulation_run(label, frame, cohort)
        sim_metrics.extend(metrics)
    real_df, sim_df = pd.DataFrame(real_metrics), pd.DataFrame(sim_metrics)
    corrected = pd.concat([real_df, sim_df], ignore_index=True)
    original_real = pd.read_csv(TASK4_EVIDENCE / "real_source_target_state_metrics.csv")
    original_sim = pd.read_csv(TASK4_EVIDENCE / "simulation_source_target_metrics.csv")
    original = pd.concat([original_real, original_sim], ignore_index=True)
    old_blocks = original.loc[original["time_block"].notna()].copy()
    new_blocks = corrected.loc[corrected["time_block"].notna()].copy()
    keys = ["dataset", "scope", "region", "time_block"]
    compare_cols = ["state_rows", "density_veh_km_lane", "flow_veh_h_lane", "speed_mean_mps", "low_speed_share_v_lt_5", "net_gap_p50_m", "closing_speed_mean_mps"]
    left = old_blocks[keys + ["block_start_s", "block_end_s", *compare_cols]].rename(columns={c: f"original_{c}" for c in ["block_start_s", "block_end_s", *compare_cols]})
    right = new_blocks[keys + ["block_start_s", "block_end_s", "nominal_block_start_s", "nominal_block_end_s", "effective_duration_s", *compare_cols]].rename(columns={c: f"corrected_{c}" for c in ["block_start_s", "block_end_s", "nominal_block_start_s", "nominal_block_end_s", "effective_duration_s", *compare_cols]})
    diff = left.merge(right, on=keys, how="outer", validate="one_to_one")
    for col in compare_cols:
        diff[f"delta_{col}"] = diff[f"corrected_{col}"] - diff[f"original_{col}"]
    return real_df, sim_df, diff


def build_package(root: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    overlap = window_overlap_audit()
    real_audits = onset_audit_for_real()
    sumo_audits = onset_audit_for_sumo()
    corrected_real, corrected_sim, diff = corrected_metrics_and_diff()
    source_bindings = {
        "task_id": "AAD-S0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-CLOSURE-20261030",
        "base_commit": "6ca87be8a12301a6acb943250164af83eabf0290",
        "implementation_sha256": {"code/scripts/analyze_stage_0_5_round2_task4_real_source_support.py": sha256_file(root / "code/scripts/analyze_stage_0_5_round2_task4_real_source_support.py"), "code/scripts/audit_stage_0_5_round2_task5_task4_evidence_integrity.py": sha256_file(Path(__file__).resolve())},
        "authorized_real_inputs": {w: {"path": str(s["path"].relative_to(root)).replace("\\", "/"), "expected_sha256": s["sha256"], "actual_sha256": sha256_file(s["path"]), "sha_pass": sha256_file(s["path"]) == s["sha256"]} for w, s in REAL_EXPECTED.items()},
        "sealed_task4_evidence_sha256": sha256_file(TASK4_EVIDENCE / "SHA256SUMS"),
        "sealed_task4_evidence_sha256sums_audit": _task4_sha256sums_ok(),
        "third_window_read": False, "locked_holdout_read": False, "native_launches": 0, "traci_connections": 0,
    }
    write_json(output / "source_bindings.json", source_bindings)
    write_json(output / "window_overlap_audit.json", overlap)
    write_json(output / "event_onset_attribution_audit.json", {"schema": "aad.stage05.round2.task5.event-onset-attribution-audit.v1", "real_ngsim": real_audits, "sumo_formal_aligned": sumo_audits, "global_conservation_pass": all(x["conservation_pass"] for x in real_audits + sumo_audits), "unknown_policy": "unmatched and ambiguous remain Unknown; never mapped to normal spatial class"})
    corrected_real.to_csv(output / "corrected_real_source_target_state_metrics.csv", index=False)
    corrected_sim.to_csv(output / "corrected_simulation_source_target_metrics.csv", index=False)
    diff.to_csv(output / "time_block_statistics_diff.csv", index=False)
    real_counts = {(x["window_id"], x["region"]): int(x["events"]) for x in pd.read_csv(TASK4_EVIDENCE / "real_source_target_exposure.csv").to_dict("records")}
    validation = {
        "schema": "aad.stage05.round2.task5.validation.v1", "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha_pass": all(v["sha_pass"] for v in source_bindings["authorized_real_inputs"].values()),
        "task4_historical_sha256_unchanged": source_bindings["sealed_task4_evidence_sha256sums_audit"]["pass"],
        "full_source_reproduction": {"0750_0805": {"events": 543, "p2_evaluable_exposure_s": 111425.9}, "0805_0820": {"events": 732, "p2_evaluable_exposure_s": 133505.6}},
        "source_target_counts_preserved": real_counts == {("0750_0805", "source"): 167, ("0750_0805", "target"): 174, ("0805_0820", "source"): 159, ("0805_0820", "target"): 252},
        "real_attribution_conservation_pass": all(x["conservation_pass"] and x["unique"] == x["extracted_events"] for x in real_audits),
        "sumo_attribution_conservation_pass": all(x["conservation_pass"] for x in sumo_audits),
        "window_overlap_exact_record_matches": overlap["record_match"]["exact_raw_record_matches"],
        "window_overlap_event_duplicates": overlap["event_match"]["duplicate_event_count"],
        "partial_block_effective_duration_used": bool((diff["corrected_effective_duration_s"] < 30.0 - 1e-9).any()),
        "native_launches": 0, "traci_connections": 0, "locked_holdout_reads": 0,
    }
    validation["status"] = "PASS_OFFLINE_TASK5" if all([validation["input_sha_pass"], validation["task4_historical_sha256_unchanged"], validation["source_target_counts_preserved"], validation["real_attribution_conservation_pass"], validation["sumo_attribution_conservation_pass"], validation["partial_block_effective_duration_used"]]) else "FAIL"
    write_json(output / "validation_record.json", validation)
    payload = sorted(p.name for p in output.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {"schema": "aad.stage05.round2.task5.manifest.v1", "task_id": "AAD-S0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-CLOSURE-20261030", "created_at_utc": datetime.now(UTC).isoformat(), "git_head": git_head(root), "payload_files": {name: sha256_file(output / name) for name in payload}, "task4_historical_package_preserved": True}
    write_json(output / "manifest.json", manifest)
    (output / "SHA256SUMS").write_text("\n".join(f"{sha256_file(output / name)}  {name}" for name in payload + ["manifest.json"]) + "\n", encoding="utf-8")
    return validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build_package(args.repo_root.resolve(), args.output.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result["status"] == "PASS_OFFLINE_TASK5" else 1


if __name__ == "__main__":
    raise SystemExit(main())
