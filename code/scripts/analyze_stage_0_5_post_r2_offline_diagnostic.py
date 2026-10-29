"""Offline-only post-R2 diagnosis; reuse production FCD/D1, never launch a tool.

Derived diagnostics are non-authoritative. Sealed trajectories and formal code
are read-only. Parquet is hashed, not decoded; the production assessor's exact
FCD reconstruction is used and reconciled against sealed D1 results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "code/src"), str(ROOT / "code/scripts")]
from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths
from riskprop.stage_0_5_state_support import fcd_to_state_frame, measure_state_frame, route_length_map
from riskprop.stage_0_5_d1_measurement import local_d1_measurement, inside_region
from riskprop.stage_0_5_sumo import (
    measurement_equivalence_matrix, run_p2_boundary_matrix, _synthetic_states,
    compute_sumo_measurements, build_sumo_p2_events, extract_sumo_formal_p2_events,
    build_sumo_formal_source_frame,
)
from analyze_stage_0_5_round2_task1 import route_inventory
from stage_0_5_execution_v2 import verify_journal

WINDOW = (120., 390.)
SOURCE = (0., 150.)
TARGET = (150., 350.)
RUNS = {"B00_A03": "WEEK_0750_B00_IC1_s20261201_A03",
        "Round2_minGap1.0": "AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1"}
PARENT = "evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028"
PACKAGE = "evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                   allow_nan=False, default=_json_value) + "\n", encoding="utf-8")


def _json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def offline_guard(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind"}:
        raise PermissionError("offline diagnostic prohibits process/network: " + event)
    if event == "open" and isinstance(args[0], (str, bytes)):
        name = str(args[0]).lower().replace("\\", "/")
        if "locked_holdout" in name or "/locked/" in name:
            raise PermissionError("locked data forbidden")


def distribution(values):
    values = pd.to_numeric(values, errors="coerce")
    values = values[np.isfinite(values)]
    if not len(values):
        return {"n": 0, "min": None, "mean": None, "sd": None,
                **{k: None for k in ["p01", "p05", "p25", "p50", "p75", "p95", "p99", "max"]}}
    return {"n": len(values), "min": float(values.min()), "max": float(values.max()),
            "mean": float(values.mean()), "sd": float(values.std()) if len(values) > 1 else None,
            **{f"p{int(q*100):02d}": float(values.quantile(q))
               for q in [.01, .05, .25, .5, .75, .95, .99]}}


def source_mask(frame):
    native = frame.native_lane_id.astype(str).str.startswith("main_0_")
    return native & inside_region(frame, SOURCE) & frame.time_s.ge(120) & frame.time_s.lt(390)


def qualified_ttc(frame):
    return (frame.reliable_following_eligible & frame.measurement_status.eq("valid") &
            frame.ttc_valid & frame.ttc_s.gt(0) & np.isfinite(frame.ttc_s))


def summary(frame):
    valid = qualified_ttc(frame)
    return {"state_rows": len(frame), "vehicles": frame.vehicle_id.nunique(),
            "quality_counts": frame.measurement_status.value_counts().to_dict(),
            "reliable_following_rows": int(frame.reliable_following_eligible.sum()),
            "evaluable_point_rows": int((frame.reliable_following_eligible &
                frame.measurement_status.isin(["valid", "not_applicable"])).sum()),
            "valid_ttc_rows": int(valid.sum()),
            "risk_rows_0_lt_ttc_lt_2": int((valid & frame.ttc_s.lt(2)).sum()),
            "near_rows_2_le_ttc_lt_3": int((valid & frame.ttc_s.ge(2) & frame.ttc_s.lt(3)).sum()),
            "ttc_ge_3_rows": int((valid & frame.ttc_s.ge(3)).sum()),
            "ttc_s": distribution(frame.loc[valid, "ttc_s"]),
            "net_gap_m": distribution(frame.net_gap_m),
            "closing_speed_mps": distribution(frame.closing_speed_mps),
            "closing_positive_rows": int(frame.closing_speed_mps.gt(.001).sum()),
            "opening_rows": int(frame.closing_speed_mps.lt(0).sum()),
            "steady_rows_abs_closing_le_epsilon": int(frame.closing_speed_mps.abs().le(.001).sum()),
            "speed_mps": distribution(frame.speed_mps),
            "low_speed_lt5_share": float(frame.speed_mps.lt(5).mean()) if len(frame) else None}


def continuity(frame):
    """Diagnostic decomposition of the D1 adjacency contract; no event promotion."""
    keys = ["run_id", "scenario_id", "vehicle_id", "incarnation_id"]
    d = frame.sort_values(keys + ["time_s"], kind="stable").reset_index(drop=True)
    p = d.shift()
    same = pd.Series(True, index=d.index)
    for k in keys:
        same &= d[k].eq(p[k])
    clock = d.time_s.sub(p.time_s).sub(.1).abs().le(1e-9)
    leader = d.leader_id.notna() & p.leader_id.notna()
    leader &= d.leader_id.eq(p.leader_id) & d.leader_incarnation_id.eq(p.leader_incarnation_id)
    lane = d.native_lane_id.notna() & d.native_lane_id.eq(p.native_lane_id)
    flags = pd.Series(True, index=d.index)
    for name in ["identity_break", "observation_gap"]:
        if name in d:
            flags &= d[name].eq(False) & p[name].eq(False)
    for name in ["observation_index", "frame_id", "original_row_number"]:
        if name in d:
            flags &= d[name].sub(p[name]).eq(1)
    if "global_time_ms" in d:
        flags &= d.global_time_ms.sub(p.global_time_ms).sub(100).abs().le(1e-6)
    return d, same & clock & leader & lane & flags, {
        "same_follower": same, "clock": clock, "same_leader": leader,
        "same_native_lane": lane, "flags_and_optional_indices": flags}


def source_segments(frame, lower=0., upper=3.):
    d, adjacent, checks = continuity(frame)
    selected = source_mask(d) & qualified_ttc(d) & d.ttc_s.ge(lower) & d.ttc_s.lt(upper)
    groups = (selected & ~(selected.shift(fill_value=False) & adjacent)).cumsum()
    rows = []
    for _, g in d.loc[selected].groupby(groups[selected], sort=False):
        a, z = int(g.index[0]), int(g.index[-1])
        next_same = z + 1 < len(d) and bool(checks["same_follower"].iloc[z+1])
        reasons = []
        if not next_same:
            reasons.append("right_censored_follower_end")
        else:
            for key, flag in checks.items():
                if not flag.iloc[z+1]:
                    reasons.append(key + "_break")
            if not source_mask(d.iloc[[z+1]]).iloc[0]:
                reasons.append("source_or_window_exit")
            if not qualified_ttc(d.iloc[[z+1]]).iloc[0]:
                reasons.append("next_ttc_not_evaluable:" + str(d.measurement_status.iloc[z+1]))
            elif not lower <= d.ttc_s.iloc[z+1] < upper:
                reasons.append("diagnostic_band_exit")
        rows.append({"vehicle_id": str(g.vehicle_id.iloc[0]),
                     "incarnation_id": str(g.incarnation_id.iloc[0]),
                     "leader_id": str(g.leader_id.iloc[0]),
                     "native_lane": str(g.native_lane_id.iloc[0]),
                     "onset_s": float(g.time_s.iloc[0]), "end_s": float(g.time_s.iloc[-1]),
                     "span_s": float(g.time_s.iloc[-1]-g.time_s.iloc[0]), "members": len(g),
                     "onset_y_m": float(g.y_m.iloc[0]), "end_y_m": float(g.y_m.iloc[-1]),
                     "minimum_ttc_s": float(g.ttc_s.min()),
                     "band_s": [lower, upper], "diagnostic_only": True,
                     "end_reasons": reasons, "quality": g.measurement_status.value_counts().to_dict()})
    return rows


def adapter_probes():
    """Counterexamples expose contract gaps; they do not propose rule changes."""
    rows = [{"time_s": t, "leader_id": "l", "net_gap_m": 1.,
             "speed_mps": 5., "leader_speed_mps": 4.} for t in [0., .1, .2]]
    clean = compute_sumo_measurements(_synthetic_states(rows))
    clean["lane_id"] = "1"
    clean["y_m"] = 50.
    clean["native_lane_id"] = "main_0_0"
    results = []
    for case in ["clean", "native_lane_change", "identity_break", "observation_gap", "inconsistent_negative_ttc"]:
        frame = clean.copy()
        follower = frame.vehicle_id.eq("f")
        if case == "native_lane_change":
            frame.loc[frame.time_s.ge(.1), "native_lane_id"] = "main_0_1"
        elif case in {"identity_break", "observation_gap"}:
            frame[case] = False
            frame.loc[follower & frame.time_s.eq(.1), case] = True
        elif case == "inconsistent_negative_ttc":
            frame.loc[follower, "ttc_s"] = -1.
        native, _ = build_sumo_p2_events(frame)
        aligned_error = None
        try:
            aligned, _ = extract_sumo_formal_p2_events(frame)
            aligned_count = len(aligned)
        except ValueError as error:
            aligned_count = None
            aligned_error = str(error)
        d1 = local_d1_measurement(frame, (0, .3), region=SOURCE, strict=True)
        mapped = build_sumo_formal_source_frame(frame)
        results.append({"case": case, "native_events": len(native),
                        "formal_aligned_events": aligned_count, "formal_aligned_error": aligned_error,
                        "D1_onsets": d1["onset_events"],
                        "D1_exposure_s": d1["local_evaluable_s"],
                        "input_flag_true_rows": {k: int(frame[k].sum()) if k in frame else None for k in ["identity_break", "observation_gap"]},
                        "mapped_flag_true_rows": {k: int(mapped[k].sum()) for k in ["identity_break", "observation_gap"]},
                        "synthetic_only": True, "scientific_equivalence_accepted": False})
    return results


def audit_run(root, label, rid, sealed, output):
    base = root / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs" / rid
    fcd = parse_fcd(base / "fcd.xml", network_edge_lengths(base / "network.net.xml"))
    _, _, cohort = route_inventory(base / "routes.rou.xml")
    assert len(cohort) == 1112
    frame = measure_state_frame(fcd_to_state_frame(fcd, route_length_map(base / "routes.rou.xml"),
        run_id=rid, scenario_id="US-101 0750", seed=20261201))
    source = local_d1_measurement(frame, WINDOW, region=SOURCE, strict=True)
    target = local_d1_measurement(frame[frame.vehicle_id.isin(cohort)], WINDOW, region=TARGET, strict=True)
    reconciliation = {}
    for kind, actual, expected in [("source", source, sealed["formal"]["source_all"]),
                                    ("target_cohort", target, sealed["formal"]["target_cohort"])]:
        for key in ["onset_events", "local_links", "local_evaluable_s", "unavailable_point_counts",
                    "incomplete_candidates", "right_censored_unconfirmed"]:
            assert actual[key] == expected[key], (label, kind, key, actual[key], expected[key])
        # Scenario labels may differ; compare science-relevant membership values.
        for x, y in zip(actual["events"], expected["events"]):
            for key in ["vehicle_id", "leader_id", "onset_s", "end_s", "confirm_s", "members", "onset_inside", "onset_in_window"]:
                if key in y:
                    assert x[key] == y[key], (label, kind, key)
        assert len(actual["events"]) == len(expected["events"])
        reconciliation[kind] = "PASS_exact_counts_exposure_quality_and_event_membership"
    s = frame.loc[source_mask(frame)].copy()
    assert len(s) == sum(source["unavailable_point_counts"].values())
    source_cohort = s.loc[s.vehicle_id.isin(cohort)]
    blocks = []
    for t in range(9):
        for y in range(3):
            lo, hi = 120+30*t, 150+30*t
            region = (50*y, 50*(y+1))
            g = s[s.time_s.ge(lo) & s.time_s.lt(hi) & s.y_m.ge(region[0]) & s.y_m.lt(region[1])]
            # Include the observed right endpoint; never derive edges after slicing.
            context = frame[frame.time_s.ge(lo-.1-1e-8) & frame.time_s.le(hi+.1+1e-8)]
            result = local_d1_measurement(context, (lo, hi), region=region, strict=True)
            blocks.append({"arm": label, "t_start_s": lo, "t_end_s": hi,
                           "y_start_m": region[0], "y_end_m": region[1],
                           "D1_exposure_veh_s": result["local_evaluable_s"],
                           "diagnostic_only": True, **summary(g)})
    risk = source_segments(frame, 0, 2)
    near = source_segments(frame, 2, 3)
    assert sum(r["members"] for r in risk) == summary(s)["risk_rows_0_lt_ttc_lt_2"]
    assert sum(r["members"] for r in near) == summary(s)["near_rows_2_le_ttc_lt_3"]
    pd.DataFrame(risk + near).to_csv(output / (label + "_source_segments.csv"), index=False)
    d, adjacency, checks = continuity(frame)
    m = source_mask(d)
    identity = json.loads((base / "identity_summary.json").read_bytes())
    journal = verify_journal(base / "identity_events.jsonl")
    lifecycle_mismatches = []
    for vid, g in fcd.groupby("vehicle_id", sort=False):
        record = identity["vehicles"].get(vid, {})
        if (record.get("first_FCD_s") != float(g.time_s.min()) or
                record.get("last_FCD_s") != float(g.time_s.max()) or
                record.get("native_insertion_status") != "observed_actual_departure"):
            lifecycle_mismatches.append(str(vid))
    assert not lifecycle_mismatches, (label, "lifecycle_mismatch", lifecycle_mismatches)
    grid = np.round(fcd.time_s.unique()*10).astype(int)
    gaps = d.time_s.sub(d.time_s.shift()).loc[checks["same_follower"]]
    missing = s[s.measurement_status.eq("missing")]
    event_context = frame[frame.vehicle_id.isin(["m00485", "r00036"]) &
                          frame.time_s.between(271.4, 272.5)]
    cols = ["vehicle_id", "leader_id", "incarnation_id", "leader_incarnation_id", "time_s", "native_lane_id", "y_m",
            "native_position_m", "speed_mps", "leader_speed_mps", "net_gap_m", "closing_speed_mps", "ttc_s", "measurement_status"]
    event_context[cols].to_csv(output / (label + "_target_event_context.csv"), index=False)
    bound_names = ["fcd.xml", "network.net.xml", "routes.rou.xml", "run.sumocfg", "measured_state.parquet",
                   "D1_measurement.json", "identity_summary.json", "identity_events.jsonl", "isolation_runtime.json"]
    isolation = json.loads((base / "isolation_runtime.json").read_bytes())
    bindings = {name: {"path": (base/name).relative_to(root).as_posix(), "sha256": sha(base/name)}
                for name in bound_names}
    raw_checked = {}
    for name, expected in isolation.get("artifact_sha256", {}).items():
        if (base/name).is_file():
            actual = sha(base/name)
            assert actual == expected, (label, name, "raw sealed hash drift")
            raw_checked[name] = actual
    parquet_key = "baseline_measured_state_sha256" if label == "B00_A03" else "candidate_measured_state_sha256"
    parent = json.loads((root/PARENT/"execution_final_v1/offline_comparison.json").read_bytes())
    assert bindings["measured_state.parquet"]["sha256"] == parent[parquet_key]
    return {"run_id": rid, "inputs": bindings, "raw_sealed_hash_checks": raw_checked,
            "reconstruction": "production parse_fcd -> fcd_to_state_frame -> measure_state_frame; no Parquet decode",
            "sealed_reconciliation": reconciliation, "all_frame_rows": len(frame),
            "source": summary(s), "source_cohort": summary(source_cohort),
            "source_all_D1": source, "target_cohort_D1": target,
            "source_blocks": blocks, "risk_segments": risk, "near_threshold_segments": near,
            "sealed_Rule_A": sealed["macro_rule_a"],
            "observability": {"FCD_ticks": len(grid), "FCD_grid_exact_0_through_419p9": bool(np.array_equal(np.sort(grid), np.arange(4200))),
                "duplicate_vehicle_clock": int(frame.duplicated(["vehicle_id", "time_s"]).sum()),
                "identity_journal": journal, "identity_accounting_complete": identity["identity_accounting_complete"],
                "declared_count": identity["declared_count"], "source_unknown_vehicle_ids": sorted(set(s.vehicle_id)-set(identity["vehicles"])),
                "lifecycle_states": identity["states"], "FCD_observed_IDs": int(fcd.vehicle_id.nunique()),
                "all_FCD_ID_lifecycle_bounds_and_actual_departures_match": not lifecycle_mismatches,
                "incarnation_implementation": "vehicle ID alias; independent lifecycle evidence is required, not inferred scientific equivalence",
                "whole_frame_follower_gap_gt_0p11": int(gaps.gt(.11).sum()),
                "source_missing_by_reason": missing.missing_reason.value_counts().to_dict(),
                "source_adjacency_failure_counts_nonexclusive": {k: int((m & ~v).sum()) for k,v in checks.items()},
                "source_qualified_adjacency_rows": int((m & adjacency).sum()),
                "source_missing_fraction": len(missing)/len(s),
                "source_not_reliable_rows": int((~s.reliable_following_eligible).sum())}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT/PACKAGE)
    args = parser.parse_args()
    sys.addaudithook(offline_guard)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    root = args.repo_root.resolve()
    sealed = json.loads((root/PARENT/"execution_final_v1/offline_comparison.json").read_bytes())
    results = {label: audit_run(root, label, rid, sealed["arms"][label], output) for label,rid in RUNS.items()}
    sources = [Path(__file__), root/"code/src/riskprop/stage_0_5_scene_reconstruction.py",
               root/"code/src/riskprop/stage_0_5_state_support.py", root/"code/src/riskprop/stage_0_5_sumo.py",
               root/"code/src/riskprop/stage_0_5_d1_measurement.py", root/"code/src/riskprop/formal_risk_measurement.py",
               root/"code/scripts/stage_0_5_acceptance_v3.py", root/"code/scripts/analyze_stage_0_5_round2_task1.py",
               root/"code/configs/stage_0_2_formal_risk_measurement_p2_v1.json"]
    result = {"schema": "aad.stage05.post-r2-offline-diagnostic.v2", "task": "AAD-S0.5-POST-R2-TASK1-20261029",
              "native_launches": 0, "traci_connections": 0, "locked_holdout_reads": 0,
              "formal_equivalence_accepted": False, "formal_code_changed": False,
              "window_s": list(WINDOW), "source_m": list(SOURCE), "target_m": list(TARGET),
              "cohort": "C_INPUT_ROUTE", "cohort_count": 1112,
              "source_sha256": {p.relative_to(root).as_posix(): sha(p) for p in sources},
              "sealed_comparison_sha256": sha(root/PARENT/"execution_final_v1/offline_comparison.json"),
              "runs": results}
    write_json(output/"diagnostic.json", result)
    write_json(output/"existing_equivalence_matrix.json", measurement_equivalence_matrix())
    write_json(output/"adapter_counterexamples.json", adapter_probes())
    matrix = run_p2_boundary_matrix()
    write_json(output/"existing_boundary_matrix.json", matrix.to_dict("records") if isinstance(matrix,pd.DataFrame) else matrix)
    blocks = [{k:v for k,v in row.items() if not isinstance(v,dict)} for r in results.values() for row in r["source_blocks"]]
    pd.DataFrame(blocks).to_csv(output/"source_time_space_blocks.csv", index=False)
    print(json.dumps({k: {"source": v["source"], "E": v["source_all_D1"]["local_evaluable_s"],
                         "risk_segments": len(v["risk_segments"]), "near_segments": len(v["near_threshold_segments"])}
                     for k,v in results.items()}, default=_json_value))


if __name__ == "__main__":
    main()
