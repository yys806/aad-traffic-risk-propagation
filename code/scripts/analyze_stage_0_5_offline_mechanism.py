"""Offline mechanism audit for the sealed Stage 0.5-R1 trajectories.

This script is intentionally separate from the formal R1 analyzer.  It only
reads sealed trajectories and the current measurement implementation; it does
not change formal results, start SUMO, or infer physical paths.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskprop.stage_0_5_d1_measurement import inside_region, local_d1_measurement


RESULT = "RES-STAGE-0.5-OFFLINE-MECHANISM-AUDIT-20261028"
R1_RESULT = "RES-STAGE-0.5-R1-DIAGNOSTICS-20261028"
WINDOW = (120.0, 390.0)
SOURCE_REGION = (0.0, 150.0)
TARGET_REGION = (150.0, 350.0)
LANES = {"1", "2", "3", "4", "5"}
COHORT_SHA = "76db89e2ff2d9df997516b59a23bc4d88a85c7a0161dca6a222f2a8bfee277f8"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def route_inventory(path: Path):
    root = ET.fromstring(path.read_bytes())
    routes = {node.get("id"): node.get("edges", "").split() for node in root.findall("route")}
    vehicles = {node.get("id"): node for node in root.findall("vehicle")}
    cohort = sorted(
        ident for ident, node in vehicles.items()
        if any(edge in {"main_0", "main_1"} for edge in routes.get(node.get("route"), []))
    )
    return routes, vehicles, cohort


def edge_from_lane(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value)
    if "_" not in text:
        return None
    return text.rsplit("_", 1)[0]


def lane_text(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text


def finite_summary(values):
    a = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(float)
    a = a[np.isfinite(a)]
    if not len(a):
        return {"n": 0, "mean": None, "median": None, "p05": None, "p95": None, "minimum": None}
    return {"n": int(len(a)), "mean": float(a.mean()), "median": float(np.median(a)),
            "p05": float(np.quantile(a, .05)), "p95": float(np.quantile(a, .95)), "minimum": float(a.min())}


def load_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    required = {"vehicle_id", "time_s", "y_m", "lane_id", "native_lane_id", "measurement_status",
                "reliable_following_eligible", "ttc_valid", "ttc_s", "closing_speed_mps", "net_gap_m",
                "leader_id", "incarnation_id", "leader_incarnation_id"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"sealed measured_state missing required fields: {missing}")
    return frame


def scoped(frame: pd.DataFrame, region, cohort: set[str] | None = None) -> pd.DataFrame:
    d = frame
    if cohort is not None:
        d = d[d.vehicle_id.astype(str).isin(cohort)]
    return d[
        d.time_s.ge(WINDOW[0]) & d.time_s.lt(WINDOW[1]) &
        d.lane_id.map(lane_text).isin(LANES) & d.y_m.ge(region[0]) & d.y_m.lt(region[1])
    ].copy()


def formal_counts(frame: pd.DataFrame, region, cohort: set[str] | None = None):
    d = frame if cohort is None else frame[frame.vehicle_id.astype(str).isin(cohort)]
    measurement = local_d1_measurement(d, WINDOW, region=region, strict=True)
    return measurement


def risk_segments(frame: pd.DataFrame, region):
    """Diagnostic contiguous risk runs inside a fixed region.

    This is not a replacement formal extractor.  It exposes short runs and
    gaps so the report can distinguish threshold hits from formal events.
    """
    d = scoped(frame, region).copy()
    if d.empty:
        return []
    d["_lane"] = d.lane_id.map(lane_text)
    d["_risk"] = (
        d.reliable_following_eligible.astype(bool) & d.ttc_valid.astype(bool) &
        d.measurement_status.eq("valid") & d.ttc_s.gt(0) & d.ttc_s.lt(2)
    )
    key_cols = ["vehicle_id", "incarnation_id", "leader_id", "leader_incarnation_id"]
    d = d.sort_values(key_cols + ["time_s"], kind="stable")
    out = []
    for key, group in d[d["_risk"]].groupby(key_cols, dropna=False, sort=False):
        group = group.sort_values("time_s", kind="stable")
        rows = group.to_dict("records")
        run = [rows[0]]
        for row in rows[1:]:
            if abs(float(row["time_s"]) - float(run[-1]["time_s"]) - .1) <= 1e-7:
                run.append(row)
            else:
                out.append(_segment_row(run, key))
                run = [row]
        out.append(_segment_row(run, key))
    return out


def _segment_row(rows, key):
    onset = rows[0]
    end = rows[-1]
    return dict(vehicle_id=str(key[0]), incarnation_id=str(key[1]), leader_id=None if pd.isna(key[2]) else str(key[2]),
                leader_incarnation_id=None if pd.isna(key[3]) else str(key[3]),
                onset_s=float(onset["time_s"]), end_s=float(end["time_s"]),
                span_s=float(end["time_s"] - onset["time_s"]), members=len(rows),
                qualifies_duration=bool(float(end["time_s"] - onset["time_s"]) >= .2 - 1e-9),
                onset_y_m=float(onset["y_m"]), onset_lane=lane_text(onset["lane_id"]),
                onset_native_lane=str(onset["native_lane_id"]))


def row_at(frame: pd.DataFrame, event: dict, time_key: str):
    vehicle = str(event.get("vehicle_id"))
    leader = event.get("leader_id")
    time = float(event[time_key])
    candidates = frame[frame.vehicle_id.astype(str).eq(vehicle) & frame.time_s.sub(time).abs().le(1e-7)]
    if leader is not None and "leader_id" in candidates:
        exact = candidates[candidates.leader_id.astype(str).eq(str(leader))]
        if len(exact):
            candidates = exact
    if len(candidates) != 1:
        return None, "missing_or_ambiguous"
    return candidates.iloc[0], "unique"


def classify_event(frame: pd.DataFrame, event: dict):
    row, status = row_at(frame, event, "onset_s")
    if row is None:
        return dict(event_id=event.get("event_id"), association_status=status,
                    spatial_class="unknown", onset_in_window=bool(event.get("onset_in_window")),
                    onset_inside_existing=bool(event.get("onset_inside")),
                    confirmation_inside_existing=bool(event.get("confirmation_inside")))
    edge = edge_from_lane(row.native_lane_id)
    lane = lane_text(row.lane_id)
    y = float(row.y_m)
    if edge == "main_0" and lane in LANES and 0 <= y < 150:
        category = "source_upstream_main"
    elif edge in {"main_0", "main_1"} and lane in LANES and 150 <= y < 350:
        category = "target_main"
    elif edge in {"main_0", "main_1"} and lane in LANES:
        category = "other_upstream_mainline"
    elif edge == "main_2":
        category = "downstream_mainline"
    elif edge == "onramp":
        category = "onramp"
    elif edge == "offramp":
        category = "offramp"
    elif edge in {"main_1", "main_0"}:
        category = "auxiliary_or_unmapped_lane"
    elif edge is None:
        category = "unknown"
    else:
        category = "other_network_edge"
    confirm, confirm_status = row_at(frame, event, "confirm_s")
    end, end_status = row_at(frame, event, "end_s")
    return dict(event_id=event.get("event_id"), vehicle_id=str(event.get("vehicle_id")),
                leader_id=None if event.get("leader_id") is None else str(event.get("leader_id")),
                association_status=status, confirmation_association_status=confirm_status,
                end_association_status=end_status, spatial_class=category,
                onset_s=float(event["onset_s"]), confirm_s=float(event["confirm_s"]), end_s=float(event["end_s"]),
                onset_y_m=y, onset_native_lane=str(row.native_lane_id), onset_edge=edge, onset_lane=lane,
                onset_in_window=bool(event.get("onset_in_window")),
                onset_inside_existing=bool(event.get("onset_inside")),
                confirmation_inside_existing=bool(event.get("confirmation_inside")),
                through_confirmation_inside_existing=bool(event.get("through_confirmation_inside")),
                through_end_inside_existing=bool(event.get("through_end_inside")),
                members=int(event.get("members", 0)))


def status_counts(frame: pd.DataFrame):
    return {str(k): int(v) for k, v in frame.measurement_status.value_counts(dropna=False).to_dict().items()}


def observability(frame: pd.DataFrame, source_measurement):
    d = scoped(frame, SOURCE_REGION)
    valid_ttc = d[d.measurement_status.eq("valid") & d.ttc_valid.astype(bool) & np.isfinite(d.ttc_s)]
    reliable = d[d.reliable_following_eligible.astype(bool)]
    risk = valid_ttc[valid_ttc.ttc_s.gt(0) & valid_ttc.ttc_s.lt(2)]
    segments = risk_segments(frame, SOURCE_REGION)
    return dict(state_records=int(len(d)), observed_vehicle_count=int(d.vehicle_id.nunique()),
                measurement_status=status_counts(d), reliable_following_states=int(len(reliable)),
                reliable_following_exposure_veh_s=source_measurement.get("reliable_local_s"),
                local_evaluable_exposure_veh_s=source_measurement.get("local_evaluable_s"),
                valid_ttc_states=int(len(valid_ttc)), valid_ttc_summary=finite_summary(valid_ttc.ttc_s),
                closing_speed_summary=finite_summary(valid_ttc.closing_speed_mps),
                net_gap_summary=finite_summary(valid_ttc.net_gap_m),
                risk_state_count_ttc_lt_2=int(len(risk)),
                diagnostic_risk_segments=int(len(segments)),
                diagnostic_short_segments=int(sum(not x["qualifies_duration"] for x in segments)),
                diagnostic_duration_qualifying_segments=int(sum(x["qualifies_duration"] for x in segments)),
                diagnostic_segments=segments,
                formal_event_count=int(source_measurement.get("onset_events") or 0),
                formal_incomplete_candidates=source_measurement.get("incomplete_candidates", []))


def block_rows(frame: pd.DataFrame, arm: str, region_name: str, region, cohort: set[str] | None):
    rows = []
    for start in np.arange(WINDOW[0], WINDOW[1], 30.0):
        end = min(float(start + 30.0), WINDOW[1])
        d = frame
        if cohort is not None:
            d = d[d.vehicle_id.astype(str).isin(cohort)]
        d = d[d.time_s.ge(start) & d.time_s.lt(end) & d.lane_id.map(lane_text).isin(LANES) &
              d.y_m.ge(region[0]) & d.y_m.lt(region[1])]
        valid = d[d.measurement_status.eq("valid") & d.ttc_valid.astype(bool) & np.isfinite(d.ttc_s)]
        risk = valid[valid.ttc_s.gt(0) & valid.ttc_s.lt(2)]
        rows.append(dict(arm=arm, region=region_name, block_start_s=float(start), block_end_s=end,
                         states=int(len(d)), vehicles=int(d.vehicle_id.nunique()),
                         speed_mean_mps=float(d.speed_mps.mean()) if len(d) else None,
                         speed_summary=finite_summary(d.speed_mps),
                         low_speed_share=float(d.speed_mps.lt(5).mean()) if len(d) else None,
                         closing_speed_mean_mps=float(valid.closing_speed_mps.mean()) if len(valid) else None,
                         net_gap_mean_m=float(valid.net_gap_m.mean()) if len(valid) else None,
                         valid_ttc_states=int(len(valid)), risk_states_ttc_lt_2=int(len(risk)),
                         reliable_states=int(d.reliable_following_eligible.astype(bool).sum()),
                         measurement_status=status_counts(d)))
    return rows


def main(repo: Path):
    out = repo / "code/outputs/formal/calibration/stage_0_5_offline_mechanism_audit_20261028"
    evidence = repo / "evidence/results" / RESULT
    out.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    raw = repo / "code/outputs/formal/calibration/stage_0_5_r1_diagnostics_20261028"
    b00_raw = repo / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03"
    routes_root = raw / "portable_extras/inputs"
    arms = {
        "B00": (b00_raw / "measured_state.parquet", repo / "evidence/admission/AAD-WEEK-2026-10-27-TO-STAGE-I-V1/candidate-v1/routes.rou.xml", "WEEK_0750_B00_IC1_s20261201_A03"),
        "B10": (raw / "B10/measured_state.parquet", routes_root / "B00_routes.rou.xml", "AAD-S0.5-R1-B10-20261028"),
        "B01": (raw / "B01/measured_state.parquet", routes_root / "ramp_routes.rou.xml", "AAD-S0.5-R1-B01-20261028"),
        "B11": (raw / "B11/measured_state.parquet", routes_root / "ramp_routes.rou.xml", "AAD-S0.5-R1-B11-20261028"),
    }
    event_rows = []
    spatial_counter = Counter()
    source_rows = []
    block_rows_all = []
    reconciliation = dict(schema="aad.offline-mechanism-count-reconciliation.v1", task_id="AAD-S0.5-OFFLINE-MECHANISM-AUDIT-20261028", arms={})
    raw_hashes = {}
    script_path = Path(__file__).resolve()
    for arm, (state_path, route_path, run_id) in arms.items():
        frame = load_frame(state_path)
        raw_hashes[f"{arm}/measured_state.parquet"] = sha(state_path)
        _, _, cohort_ids = route_inventory(route_path)
        cohort = set(cohort_ids)
        raw_hashes[f"{arm}/routes.rou.xml"] = sha(route_path)
        full_target = formal_counts(frame, TARGET_REGION, None)
        target_cohort = formal_counts(frame, TARGET_REGION, cohort)
        source_formal = formal_counts(frame, SOURCE_REGION, None)
        full_events = list(full_target.get("events", []))
        classified = [classify_event(frame, event) for event in full_events]
        for row in classified:
            row.update(arm=arm, run_id=run_id)
            event_rows.append(row)
            spatial_counter[(arm, row.get("spatial_class", "unknown"), bool(row.get("onset_in_window", False)))] += 1
        existing = None
        if arm != "B00":
            existing_path = raw / arm / "measurement_result.json"
            if not existing_path.exists():
                existing_path = raw / "portable_extras" / arm / "measurement_result.json"
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            existing_events = existing["target_measurement"]["all_vehicle_reference"]["events"]
            existing_ids = [str(x.get("event_id")) for x in existing_events]
            recomputed_ids = [str(x.get("event_id")) for x in full_events]
            existing_window = sum(bool(x.get("onset_in_window")) for x in existing_events)
            reconciliation["arms"][arm] = dict(
                recomputed_event_array_length=len(full_events), existing_event_array_length=len(existing_events),
                recomputed_window_onsets=sum(bool(x.get("onset_in_window")) for x in full_events),
                existing_window_onsets=existing_window,
                event_ids_match=(existing_ids == recomputed_ids),
                source_formal_events=int(source_formal.get("onset_events") or 0),
                target_all_vehicle_formal_onsets=int(full_target.get("onset_events") or 0),
                target_cohort_formal_events=int(target_cohort.get("onset_events") or 0),
                existing_target_p2=int(existing["target_measurement"]["P2_events"]),
                existing_source_p2=int(existing["source_event_measurement"]["onset_events"]),
                differences=[])
            if existing_ids != recomputed_ids:
                reconciliation["arms"][arm]["differences"].append("event_id_sequence_mismatch")
            if existing_window != sum(bool(x.get("onset_in_window")) for x in full_events):
                reconciliation["arms"][arm]["differences"].append("window_onset_count_mismatch")
        else:
            reconciliation["arms"][arm] = dict(
                recomputed_event_array_length=len(full_events), recomputed_window_onsets=sum(bool(x.get("onset_in_window")) for x in full_events),
                source_formal_events=int(source_formal.get("onset_events") or 0),
                target_all_vehicle_formal_onsets=int(full_target.get("onset_events") or 0),
                target_cohort_formal_events=int(target_cohort.get("onset_events") or 0), existing_target_p2=0, existing_source_p2=0, differences=[])
        source_diag = observability(frame, source_formal)
        source_diag.update(arm=arm, run_id=run_id, cohort_count=len(cohort), cohort_sha256=hashlib.sha256(("\n".join(sorted(cohort)) + "\n").encode()).hexdigest())
        source_rows.append(source_diag)
        block_rows_all.extend(block_rows(frame, arm, "source_upstream_main", SOURCE_REGION, None))
        block_rows_all.extend(block_rows(frame, arm, "target_main_cohort", TARGET_REGION, cohort))
        if arm != "B00":
            raw_hashes[f"{arm}/identity_summary.json"] = sha(raw / arm / "identity_summary.json")
    # Integrity check against R1 portable raw-output hash map.
    manifest = json.loads((repo / "evidence/results/RES-STAGE-0.5-R1-DIAGNOSTICS-20261028/manifest.json").read_text(encoding="utf-8"))
    raw_expected = manifest.get("raw_output_files", {})
    integrity = {}
    for arm in ["B10", "B01", "B11"]:
        integrity[arm] = {}
        for name, expected in raw_expected.get(arm, {}).items():
            path = raw / arm / name
            if path.exists():
                integrity[arm][name] = dict(expected=expected, actual=sha(path), match=sha(path) == expected)
    reconciliation["raw_output_hash_integrity"] = integrity
    reconciliation["source_sha256"] = {"offline_analyzer": sha(script_path), "formal_d1": sha(repo / "code/src/riskprop/stage_0_5_d1_measurement.py"), "state_support": sha(repo / "code/src/riskprop/stage_0_5_state_support.py")}
    reconciliation["repository_head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    reconciliation["all_raw_hashes_match"] = all(row.get("match") is True for arm in integrity.values() for row in arm.values())
    pd.DataFrame(event_rows).to_csv(evidence / "event_inventory.csv", index=False, lineterminator="\n")
    pd.DataFrame([dict(arm=a, spatial_class=c, onset_in_window=w, event_count=n) for (a, c, w), n in sorted(spatial_counter.items())]).to_csv(evidence / "spatial_counts.csv", index=False, lineterminator="\n")
    pd.DataFrame(source_rows).drop(columns=["diagnostic_segments"], errors="ignore").to_csv(evidence / "source_observability.csv", index=False, lineterminator="\n")
    # Keep the detailed diagnostic segments in local output, not portable evidence.
    (out / "source_observability_detailed.json").write_text(json.dumps(source_rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    pd.DataFrame(block_rows_all).to_csv(evidence / "arm_state_blocks.csv", index=False, lineterminator="\n")
    (out / "event_inventory.json").write_text(json.dumps(event_rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_json(evidence / "count_reconciliation.json", reconciliation)
    validation = dict(schema="aad.offline-mechanism-validation.v1", task_id="AAD-S0.5-OFFLINE-MECHANISM-AUDIT-20261028",
                      status="Completed offline audit; no SUMO launched", repository_head=reconciliation["repository_head"],
                      formal_measurement_implementation_unchanged=True, raw_hash_integrity=reconciliation["all_raw_hashes_match"],
                      count_reconciliation_differences={a:v.get("differences", []) for a,v in reconciliation["arms"].items()},
                      event_inventory_rows=len(event_rows), source_observability_rows=len(source_rows), state_block_rows=len(block_rows_all),
                      notes=["all_vehicle_reference event arrays are not equivalent to source/target formal P2 counts",
                             "unknown spatial associations are retained as unknown", "no AI_CONTEXT modification performed"])
    write_json(evidence / "validation_record.json", validation)
    # Portable manifest and checksums include only the small audit evidence.
    files = [p for p in sorted(evidence.iterdir()) if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"}]
    manifest_out = dict(schema="aad.offline-mechanism-manifest.v1", result_id=RESULT,
                        task_id="AAD-S0.5-OFFLINE-MECHANISM-AUDIT-20261028", repository_head=reconciliation["repository_head"],
                        files={p.name: sha(p) for p in files}, raw_output_root=str(raw.relative_to(repo)).replace("\\", "/"),
                        raw_output_hashes=raw_hashes, analyzer_sha256=sha(script_path))
    write_json(evidence / "manifest.json", manifest_out)
    sums = [f"{sha(p)}  {p.name}" for p in sorted(evidence.iterdir()) if p.is_file() and p.name != "SHA256SUMS"]
    (evidence / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(json.dumps({"result_id": RESULT, "event_inventory_rows": len(event_rows), "source_rows": len(source_rows),
                      "block_rows": len(block_rows_all), "reconciliation": reconciliation["arms"],
                      "raw_hashes_match": reconciliation["all_raw_hashes_match"]}, ensure_ascii=False))


if __name__ == "__main__":
    main(Path("/mnt/d/shen/TJU/AAD"))
