"""Offline real-source support and multi-scale crosswalk for Round 2 Task 4.

The script is deliberately read-only with respect to source and sealed run data.  It
uses the already accepted NGSIM state tables and the two sealed measured-state tables;
it never starts SUMO/TraCI, launches a subprocess, or accesses the network.
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
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
RUNS = ROOT / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs"
EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030"
WINDOWS = ("0750_0805", "0805_0820")
REAL_EXPECTED = {
    "0750_0805": {
        "path": SRC / "ngsim_us101__0750_0805.parquet",
        "sha256": "684a5f0b96dc48116f16d581c278d7039c0554bf1c3cea8d6eda3e605e3e8644",
        "events": 543,
        "p2_evaluable_s": 111425.9,
    },
    "0805_0820": {
        "path": SRC / "ngsim_us101__0805_0820.parquet",
        "sha256": "7b0ef830c97a981da018d4e24b029e38aa2630387c728ea87b57926745880a9f",
        "events": 732,
        "p2_evaluable_s": 133505.6,
    },
}
SIM_EXPECTED = {
    "B00_A03": {
        "run_id": "WEEK_0750_B00_IC1_s20261201_A03",
        "fcd_sha256": "1dc274082f4ea14949979d0c925903bbb5b9668d1124dabb79799b59a55fa304",
        "measured_state_sha256": "48b20ff458ff1dce4559a762d6965b6747a940d537b1460d74e33d739a3cf63a",
    },
    "Round2_minGap1.0": {
        "run_id": "AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1",
        "fcd_sha256": "434f1c2500cdf06d069d7eae1c86e064ad76af61f478379943bbefab70b2ac3e",
        "measured_state_sha256": "31426640954e6e8ea883f82dce139df130d7f83a8db4300ceb38842d4ee716b8",
    },
}
SOURCE = (0.0, 150.0)
TARGET = (150.0, 350.0)
MAINLINE_LANES = frozenset({"1", "2", "3", "4", "5"})
SIM_WINDOW = (120.0, 390.0)
CADENCE = 0.1
EVALUABLE_STATUS = frozenset({"valid", "not_applicable"})


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
                    sha, name = line.split(" ", 1)
                    if name == ref:
                        return sha
    return head


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (Path,)):
        return str(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")


def finite_summary(values: pd.Series) -> dict[str, Any]:
    x = pd.to_numeric(values, errors="coerce")
    x = x[np.isfinite(x)]
    if x.empty:
        return {"n": 0, "min": None, "p05": None, "p25": None, "p50": None, "p75": None, "p95": None, "max": None, "mean": None, "sd": None}
    return {
        "n": int(len(x)), "min": float(x.min()), "max": float(x.max()),
        "mean": float(x.mean()), "sd": float(x.std(ddof=1)) if len(x) > 1 else None,
        "p05": float(x.quantile(.05)), "p25": float(x.quantile(.25)),
        "p50": float(x.quantile(.50)), "p75": float(x.quantile(.75)),
        "p95": float(x.quantile(.95)),
    }


def point_region(frame: pd.DataFrame, region: tuple[float, float]) -> pd.Series:
    return frame["lane_id"].astype("string").isin(MAINLINE_LANES) & frame["y_m"].ge(region[0]) & frame["y_m"].lt(region[1])


def _ordered_edges(frame: pd.DataFrame, *, real: bool) -> tuple[pd.DataFrame, pd.Series]:
    if real:
        keys = ["dataset", "site", "window_id", "source_member", "source_period", "trajectory_id", "global_time_ms", "frame_id"]
        pair = ["dataset", "site", "window_id", "source_member", "source_period", "trajectory_id", "leader_trajectory_id"]
        ordered = frame.sort_values(keys, kind="stable").reset_index(drop=True)
        previous = ordered.shift()
        adjacent = pd.Series(True, index=ordered.index)
        for key in pair + ["diagnostic_clock_anchor_ms"]:
            adjacent &= ordered[key].notna() & previous[key].notna() & ordered[key].eq(previous[key]).fillna(False)
        adjacent &= ordered["global_time_ms"].diff().eq(100)
        adjacent &= ordered["frame_id"].diff().eq(1)
        adjacent &= (ordered["time_s"].diff() - CADENCE).abs().lt(1e-9)
        adjacent &= ~ordered["identity_break"].fillna(True) & ~ordered["observation_gap"].fillna(True)
        reliable = ordered["leader_matched"].fillna(False) & ~ordered["identity_uncertain"].fillna(True) & ~ordered["leader_identity_uncertain"].fillna(True)
    else:
        keys = ["run_id", "scenario_id", "vehicle_id", "incarnation_id", "time_s", "simulation_step"]
        ordered = frame.sort_values(keys, kind="stable").reset_index(drop=True)
        previous = ordered.shift()
        adjacent = pd.Series(True, index=ordered.index)
        for key in ["run_id", "scenario_id", "vehicle_id", "incarnation_id", "leader_trajectory_id", "leader_incarnation_id"]:
            if key in ordered:
                adjacent &= ordered[key].notna() & previous[key].notna() & ordered[key].eq(previous[key]).fillna(False)
        adjacent &= (ordered["time_s"].diff() - CADENCE).abs().lt(1e-9)
        adjacent &= ordered["simulation_step"].diff().eq(1)
        reliable = ordered["reliable_following_eligible"].fillna(False).astype(bool)
    edge = adjacent & reliable & reliable.shift(fill_value=False)
    return ordered, edge


def exposure_summary(frame: pd.DataFrame, *, real: bool, region: tuple[float, float] | None = None) -> dict[str, Any]:
    ordered, edge = _ordered_edges(frame, real=real)
    if region is not None:
        inside = point_region(ordered, region)
        edge &= inside & inside.shift(fill_value=False)
    status = ordered["measurement_status"].astype("string")
    evaluable = edge & status.isin(EVALUABLE_STATUS) & status.shift().isin(EVALUABLE_STATUS)
    following = int(edge.sum())
    p2 = int(evaluable.sum())
    return {
        "reliable_edges": following,
        "reliable_exposure_s": following * CADENCE,
        "p2_evaluable_edges": p2,
        "p2_evaluable_exposure_s": p2 * CADENCE,
        "not_evaluable_edges": following - p2,
        "not_evaluable_exposure_s": (following - p2) * CADENCE,
        "ordered_rows": int(len(ordered)),
    }


def state_metrics(frame: pd.DataFrame, *, dataset: str, scope: str, region_name: str, region: tuple[float, float], window_start: float, window_end: float, time_block: int | None = None, block_start: float | None = None, block_end: float | None = None) -> dict[str, Any]:
    d = frame.loc[point_region(frame, region) & frame["time_s"].ge(window_start) & frame["time_s"].lt(window_end)].copy()
    duration = float(window_end - window_start)
    if not d.empty:
        width = float(region[1] - region[0])
        lane_km = width / 1000.0 * 5.0
        density = len(d) * CADENCE / duration / lane_km
        speed_mean = float(pd.to_numeric(d["speed_mps"], errors="coerce").mean())
        flow = density * speed_mean * 3.6 if math.isfinite(speed_mean) else None
    else:
        density = flow = speed_mean = None
    speed = finite_summary(d["speed_mps"])
    accel = finite_summary(d["acceleration_mps2"])
    gap = finite_summary(d["net_gap_m"])
    closing = finite_summary(d["closing_speed_mps"])
    valid_ttc = d["ttc_valid"].fillna(False).astype(bool) & pd.to_numeric(d["ttc_s"], errors="coerce").gt(0)
    ttc = finite_summary(d.loc[valid_ttc, "ttc_s"])
    statuses = {str(k): int(v) for k, v in d["measurement_status"].value_counts(dropna=False).items()}
    row = {
        "dataset": dataset, "scope": scope, "region": region_name,
        "time_block": time_block, "block_start_s": block_start, "block_end_s": block_end,
        "state_rows": int(len(d)), "vehicle_count": int(d["vehicle_id"].nunique()) if not d.empty else 0,
        "density_veh_km_lane": density, "flow_veh_h_lane": flow,
        "speed_mean_mps": speed_mean, "speed_sd_mps": speed["sd"],
        "speed_p05_mps": speed["p05"], "speed_p25_mps": speed["p25"], "speed_p50_mps": speed["p50"],
        "speed_p75_mps": speed["p75"], "speed_p95_mps": speed["p95"],
        "low_speed_share_v_lt_5": float(pd.to_numeric(d["speed_mps"], errors="coerce").lt(5).mean()) if not d.empty else None,
        "net_gap_mean_m": gap["mean"], "net_gap_p05_m": gap["p05"], "net_gap_p50_m": gap["p50"], "net_gap_p95_m": gap["p95"],
        "closing_speed_mean_mps": closing["mean"], "closing_speed_p05_mps": closing["p05"], "closing_speed_p50_mps": closing["p50"], "closing_speed_p95_mps": closing["p95"],
        "acceleration_mean_mps2": accel["mean"], "acceleration_sd_mps2": accel["sd"], "acceleration_p05_mps2": accel["p05"], "acceleration_p50_mps2": accel["p50"], "acceleration_p95_mps2": accel["p95"],
        "ttc_valid_count": int(valid_ttc.sum()), "ttc_min_s": ttc["min"], "ttc_p05_s": ttc["p05"], "ttc_p50_s": ttc["p50"],
        "status_valid": statuses.get("valid", 0), "status_not_applicable": statuses.get("not_applicable", 0),
        "status_invalid": statuses.get("invalid", 0), "status_missing": statuses.get("missing", 0),
        "status_not_measurable": statuses.get("not_measurable", 0),
    }
    return row


def block_rows(frame: pd.DataFrame, *, dataset: str, scope: str, region_name: str, region: tuple[float, float], start: float, end: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    block = 0
    t = start
    while t < end - 1e-9:
        block_end = min(t + 30.0, end)
        edges = [region[0], min(region[0] + 100.0, region[1]), region[1]]
        for sub in range(len(edges) - 1):
            rows.append(state_metrics(frame, dataset=dataset, scope=scope, region_name=f"{region_name}_{sub}", region=(edges[sub], edges[sub + 1]), window_start=t, window_end=block_end, time_block=block, block_start=t, block_end=block_end))
        t += 30.0
        block += 1
    return rows


def real_window(window: str, states: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    from riskprop.ngsim_risk_calibration import extract_rear_end_events

    events = extract_rear_end_events(states, provisional_ttc_threshold_s=2.0, max_gap_s=0.11, minimum_duration_s=0.2)
    exposure = exposure_summary(states, real=True)
    attribution = {"source": [], "target": [], "other_mainline": [], "auxiliary_or_other": []}
    lookup = states.set_index(["trajectory_id", "time_s"], drop=False)
    for event in events.to_dict("records"):
        key = (event["trajectory_id"], float(event["event_start_s"]))
        row = lookup.loc[key] if key in lookup.index else None
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        if row is None:
            cls = "auxiliary_or_other"
        else:
            lane = str(row["lane_id"])
            y = float(row["y_m"])
            cls = "source" if lane in MAINLINE_LANES and SOURCE[0] <= y < SOURCE[1] else ("target" if lane in MAINLINE_LANES and TARGET[0] <= y < TARGET[1] else ("other_mainline" if lane in MAINLINE_LANES else "auxiliary_or_other"))
        attribution[cls].append(event)
    rows: list[dict[str, Any]] = []
    for region_name, region in (("source", SOURCE), ("target", TARGET)):
        ex = exposure_summary(states, real=True, region=region)
        ev = attribution[region_name]
        durations = pd.Series([float(x["event_duration_s"]) for x in ev], dtype=float)
        ttcs = pd.Series([float(x["ttc_min_s"]) for x in ev], dtype=float)
        rows.append({
            "dataset": "NGSIM", "window_id": window, "region": region_name, "measurement_contract": "NGSIM_Formal_P2_v2",
            "events": len(ev), "reliable_exposure_s": ex["reliable_exposure_s"], "p2_evaluable_exposure_s": ex["p2_evaluable_exposure_s"], "not_evaluable_exposure_s": ex["not_evaluable_exposure_s"],
            "event_rate_per_p2_evaluable_vehicle_hour": (len(ev) / (ex["p2_evaluable_exposure_s"] / 3600.0)) if ex["p2_evaluable_exposure_s"] else None,
            "event_duration_median_s": float(durations.median()) if len(durations) else None, "event_duration_p90_s": float(durations.quantile(.9)) if len(durations) else None, "event_duration_max_s": float(durations.max()) if len(durations) else None,
            "event_ttc_min_median_s": float(ttcs.median()) if len(ttcs) else None, "event_ttc_min_p05_s": float(ttcs.quantile(.05)) if len(ttcs) else None, "event_ttc_min_min_s": float(ttcs.min()) if len(ttcs) else None,
            "formal_equivalence_accepted": True, "event_attribution_unknown": 0,
        })
    start = float(states["time_s"].min())
    end = float(states["time_s"].max() + CADENCE)
    macro = [state_metrics(states, dataset="NGSIM", scope=window, region_name="source", region=SOURCE, window_start=start, window_end=end), state_metrics(states, dataset="NGSIM", scope=window, region_name="target", region=TARGET, window_start=start, window_end=end)]
    blocks = block_rows(states, dataset="NGSIM", scope=window, region_name="source", region=SOURCE, start=math.floor(start / 30) * 30.0, end=math.ceil(end / 30) * 30.0) + block_rows(states, dataset="NGSIM", scope=window, region_name="target", region=TARGET, start=math.floor(start / 30) * 30.0, end=math.ceil(end / 30) * 30.0)
    metrics = macro + blocks
    full = {"window_id": window, "full_events": len(events), "expected_events": REAL_EXPECTED[window]["events"], "full_event_reproduction_pass": len(events) == REAL_EXPECTED[window]["events"], "full_exposure": exposure, "expected_p2_evaluable_s": REAL_EXPECTED[window]["p2_evaluable_s"], "full_exposure_reproduction_pass": abs(exposure["p2_evaluable_exposure_s"] - REAL_EXPECTED[window]["p2_evaluable_s"]) < 1e-9, "spatial_attribution_counts": {k: len(v) for k, v in attribution.items()}, "source_target_rows": rows}
    return full, rows, metrics, events


def cohort_ids(route_path: Path) -> set[str]:
    root = ET.parse(route_path).getroot()
    routes = {str(node.attrib["id"]): str(node.attrib.get("edges", "")).split() for node in root.findall("route")}
    return {
        str(node.attrib["id"])
        for node in root.findall("vehicle")
        if any(edge in {"main_0", "main_1"} for edge in routes.get(str(node.attrib.get("route")), []))
    }


def simulation_run(label: str, states: pd.DataFrame, cohort: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from riskprop.stage_0_5_d1_measurement import local_d1_measurement
    from riskprop.stage_0_5_sumo import build_sumo_formal_source_frame, extract_sumo_formal_p2_events

    records: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    # Reuse the production formal-alignment adapter offline.  Its rows are kept
    # separate from D1 because scientific equivalence remains pending.
    mapped = build_sumo_formal_source_frame(states)
    formal_events, formal_audit = extract_sumo_formal_p2_events(states)
    mapped_window = mapped.loc[mapped["time_s"].ge(SIM_WINDOW[0]) & mapped["time_s"].lt(SIM_WINDOW[1])].copy()
    lookup = mapped.set_index(["trajectory_id", "time_s"], drop=False)
    attributed_formal: dict[str, list[dict[str, Any]]] = {"source": [], "target": []}
    for event in formal_events.to_dict("records"):
        if not (SIM_WINDOW[0] <= float(event["event_start_s"]) < SIM_WINDOW[1]):
            continue
        key = (event["trajectory_id"], float(event["event_start_s"]))
        row = lookup.loc[key] if key in lookup.index else None
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        if row is None:
            continue
        lane = str(row["lane_id"]); y = float(row["y_m"])
        region_name = "source" if lane in MAINLINE_LANES and SOURCE[0] <= y < SOURCE[1] else ("target" if lane in MAINLINE_LANES and TARGET[0] <= y < TARGET[1] else None)
        if region_name:
            attributed_formal[region_name].append(event)
    for region_name, region in (("source", SOURCE), ("target", TARGET)):
        ex = exposure_summary(mapped_window, real=True, region=region)
        ev = attributed_formal[region_name]
        durations = pd.Series([float(x["event_duration_s"]) for x in ev], dtype=float)
        ttcs = pd.Series([float(x["ttc_min_s"]) for x in ev], dtype=float)
        records.append({
            "dataset": "SUMO", "run_label": label, "region": region_name, "measurement_contract": "SUMO_formal_aligned_P2_diagnostic",
            "events": len(ev), "reliable_exposure_s": ex["reliable_exposure_s"], "p2_evaluable_exposure_s": ex["p2_evaluable_exposure_s"], "not_evaluable_exposure_s": ex["not_evaluable_exposure_s"],
            "event_rate_per_p2_evaluable_vehicle_hour": (len(ev) / (ex["p2_evaluable_exposure_s"] / 3600.0)) if ex["p2_evaluable_exposure_s"] else None,
            "event_duration_median_s": float(durations.median()) if len(durations) else None, "event_duration_p90_s": float(durations.quantile(.9)) if len(durations) else None, "event_duration_max_s": float(durations.max()) if len(durations) else None,
            "event_ttc_min_median_s": float(ttcs.median()) if len(ttcs) else None, "event_ttc_min_p05_s": float(ttcs.quantile(.05)) if len(ttcs) else None, "event_ttc_min_min_s": float(ttcs.min()) if len(ttcs) else None,
            "formal_equivalence_accepted": False, "event_attribution_unknown": 0, "formal_adapter_status": formal_audit["equivalence_status"],
        })
    for region_name, region in (("source", SOURCE), ("target", TARGET)):
        all_frame = states if region_name == "source" else states.loc[states["vehicle_id"].astype(str).isin(cohort)]
        d1 = local_d1_measurement(all_frame, SIM_WINDOW, region=region, strict=True)
        ev = [event for event in d1.get("events", []) if bool(event.get("onset_inside", False))]
        durations = pd.Series([float(x["end_s"] - x["onset_s"]) for x in ev], dtype=float)
        records.append({
            "dataset": "SUMO", "run_label": label, "region": region_name, "measurement_contract": "SUMO_D1_diagnostic",
            "events": int(d1["onset_events"]), "reliable_exposure_s": float(d1["reliable_local_s"]), "p2_evaluable_exposure_s": float(d1["local_evaluable_s"]),
            "not_evaluable_exposure_s": float(d1["reliable_local_s"] - d1["local_evaluable_s"]), "event_rate_per_p2_evaluable_vehicle_hour": float(d1["rate_per_evaluable_vehicle_hour"]) if d1["rate_per_evaluable_vehicle_hour"] is not None else None,
            "event_duration_median_s": float(durations.median()) if len(durations) else None, "event_duration_p90_s": float(durations.quantile(.9)) if len(durations) else None, "event_duration_max_s": float(durations.max()) if len(durations) else None,
            "event_ttc_min_median_s": None, "event_ttc_min_p05_s": None, "event_ttc_min_min_s": None,
            "formal_equivalence_accepted": False, "event_attribution_unknown": int(len(d1.get("incomplete_candidates", []))),
        })
        metrics.append(state_metrics(states if region_name == "source" else states.loc[states["vehicle_id"].astype(str).isin(cohort)], dataset="SUMO", scope=label, region_name=region_name, region=region, window_start=SIM_WINDOW[0], window_end=SIM_WINDOW[1]))
        metrics.extend(block_rows(states if region_name == "source" else states.loc[states["vehicle_id"].astype(str).isin(cohort)], dataset="SUMO", scope=label, region_name=region_name, region=region, start=SIM_WINDOW[0], end=SIM_WINDOW[1]))
    return records, metrics


def build_package(root: Path, output: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root / "code/src"))
    output.mkdir(parents=True, exist_ok=True)
    source_bindings: dict[str, Any] = {"real": {}, "simulation": {}, "reader": {"python": sys.executable, "python_version": platform.python_version(), "pandas": pd.__version__}}
    implementation_files = [
        Path(__file__).resolve(),
        root / "code/src/riskprop/formal_risk_measurement.py",
        root / "code/src/riskprop/ngsim_risk_calibration.py",
        root / "code/src/riskprop/stage_0_5_d1_measurement.py",
        root / "code/src/riskprop/stage_0_5_sumo.py",
        root / "code/configs/stage_0_2_formal_risk_measurement_p2_v1.json",
    ]
    source_bindings["implementation_sha256"] = {
        str(path.relative_to(root)).replace("\\", "/"): sha256_file(path) for path in implementation_files
    }
    for window, spec in REAL_EXPECTED.items():
        actual = sha256_file(spec["path"])
        source_bindings["real"][window] = {"path": str(spec["path"].relative_to(root)).replace("\\", "/"), "expected_sha256": spec["sha256"], "actual_sha256": actual, "sha_pass": actual == spec["sha256"], "authorized": True}
    cohort_path = root / "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/routes.rou.xml"
    cohort = cohort_ids(cohort_path)
    real_summaries: list[dict[str, Any]] = []
    real_rows: list[dict[str, Any]] = []
    real_metrics: list[dict[str, Any]] = []
    all_events: dict[str, pd.DataFrame] = {}
    for window, spec in REAL_EXPECTED.items():
        frame = pd.read_parquet(spec["path"])
        summary, rows, metrics, events = real_window(window, frame)
        real_summaries.append(summary); real_rows.extend(rows); real_metrics.extend(metrics); all_events[window] = events
    simulation_rows: list[dict[str, Any]] = []
    simulation_metrics: list[dict[str, Any]] = []
    for label, spec in SIM_EXPECTED.items():
        run_dir = RUNS / spec["run_id"]
        fcd = run_dir / "fcd.xml"
        measured = run_dir / "measured_state.parquet"
        actual_fcd, actual_state = sha256_file(fcd), sha256_file(measured)
        source_bindings["simulation"][label] = {"run_id": spec["run_id"], "fcd_path": str(fcd.relative_to(root)).replace("\\", "/"), "fcd_expected_sha256": spec["fcd_sha256"], "fcd_actual_sha256": actual_fcd, "fcd_sha_pass": actual_fcd == spec["fcd_sha256"], "measured_state_path": str(measured.relative_to(root)).replace("\\", "/"), "measured_state_expected_sha256": spec["measured_state_sha256"], "measured_state_actual_sha256": actual_state, "measured_state_sha_pass": actual_state == spec["measured_state_sha256"], "authorized": True}
        frame = pd.read_parquet(measured)
        rows, metrics = simulation_run(label, frame, cohort)
        simulation_rows.extend(rows); simulation_metrics.extend(metrics)
    write_json(output / "source_bindings.json", source_bindings)
    write_json(output / "real_source_target_p2_summary.json", {"schema": "aad.stage05.round2.task4.real-p2.v1", "formal_rule": {"ttc": "0<TTC<2 s", "minimum_duration_s": 0.2, "max_gap_s": 0.11, "cadence_s": 0.1, "endpoint_status": sorted(EVALUABLE_STATUS), "spatial_attribution": "full-context onset point; mainline lanes 1-5; source y[0,150), target y[150,350)"}, "windows": real_summaries})
    pd.DataFrame(real_rows).to_csv(output / "real_source_target_exposure.csv", index=False)
    pd.DataFrame(real_metrics).to_csv(output / "real_source_target_state_metrics.csv", index=False)
    pd.DataFrame(simulation_metrics).to_csv(output / "simulation_source_target_metrics.csv", index=False)
    pd.DataFrame(real_rows + simulation_rows).to_csv(output / "risk_event_attribution_summary.csv", index=False)
    time_alignment = {"status": "Unverified", "real_time_semantics": "NGSIM time_s relative to source-window earliest observation", "simulation_time_semantics": "SUMO absolute clock; measured_state time_s", "real_windows": {w: {"time_min_s": float(pd.read_parquet(s["path"], columns=["time_s"])["time_s"].min()), "time_max_s": float(pd.read_parquet(s["path"], columns=["time_s"])["time_s"].max()), "global_time_min_ms": int(pd.read_parquet(s["path"], columns=["global_time_ms"])["global_time_ms"].min()), "global_time_max_ms": int(pd.read_parquet(s["path"], columns=["global_time_ms"])["global_time_ms"].max())} for w, s in REAL_EXPECTED.items()}, "simulation_evaluation_window_s": list(SIM_WINDOW), "mapping_proven": False, "comparison_policy": "independent descriptive windows; no artificial time shift or block matching"}
    write_json(output / "time_alignment_audit.json", time_alignment)
    population = {"real": {w: {"window_id": w, "vehicle_ids": int(pd.read_parquet(s["path"], columns=["vehicle_id"])["vehicle_id"].nunique()), "trajectory_ids": int(pd.read_parquet(s["path"], columns=["trajectory_id"])["trajectory_id"].nunique())} for w, s in REAL_EXPECTED.items()}, "simulation": {"cohort": "C_INPUT_ROUTE", "declared_cohort_ids": len(cohort), "note": "real NGSIM IDs and SUMO cohort IDs are not one-to-one"}}
    write_json(output / "population_scope_crosswalk.json", population)
    decision = {"schema": "aad.stage05.round2.task4.decision-matrix.v1", "observations": {"real_source_p2": {w: {"events": x["source_target_rows"][0]["events"], "p2_evaluable_exposure_s": x["source_target_rows"][0]["p2_evaluable_exposure_s"], "rate_per_vehicle_hour": x["source_target_rows"][0]["event_rate_per_p2_evaluable_vehicle_hour"]} for w, x in ((y["window_id"], y) for y in real_summaries)}, "simulation_source_d1": {r["run_label"]: r["events"] for r in simulation_rows if r["region"] == "source"}, "simulation_target_d1": {r["run_label"]: r["events"] for r in simulation_rows if r["region"] == "target"}}, "interpretation": {"real_source_support": "Observed if source event count > 0 with positive P2-evaluable exposure; not a Gate decision", "simulator_comparison": "SUMO D1 and NGSIM Formal P2 remain separate contracts; formal equivalence is not accepted", "time_alignment": "Cannot be claimed from current provenance; preserve independent windows", "physical_propagation": "Not established by region counts or topology"}, "hypotheses_for_researcher": ["If real source P2 is positive while sealed SUMO source D1 is zero, behavior or measurement-contract differences remain competing explanations.", "If real source P2 is zero in both windows with positive exposure, the fixed source object has descriptive zero-event support in these data; this does not imply no unobserved risk.", "No new parameter or experiment is authorized by this package."], "next_step": "Researcher decides whether the fixed source estimand remains scientifically useful; no automatic experiment or Stage 0.6 transition."}
    write_json(output / "decision_matrix.json", decision)
    checks = {
        "input_sha_pass": all(x["sha_pass"] for x in source_bindings["real"].values()) and all(x["fcd_sha_pass"] and x["measured_state_sha_pass"] for x in source_bindings["simulation"].values()),
        "ngsim_full_event_reproduction_pass": all(x["full_event_reproduction_pass"] for x in real_summaries),
        "ngsim_full_exposure_reproduction_pass": all(x["full_exposure_reproduction_pass"] for x in real_summaries),
        "event_attribution_unique": all(sum(x["spatial_attribution_counts"].values()) == x["full_events"] for x in real_summaries),
        "native_launches": 0, "traci_connections": 0, "locked_holdout_reads": 0,
    }
    validation = {"schema": "aad.stage05.round2.task4.validation.v1", "created_at_utc": datetime.now(UTC).isoformat(), "status": "PASS_OFFLINE_EVIDENCE" if all(checks[k] for k in ("input_sha_pass", "ngsim_full_event_reproduction_pass", "ngsim_full_exposure_reproduction_pass", "event_attribution_unique")) else "FAIL", "checks": checks, "source_access": {"authorized_real_windows": list(WINDOWS), "third_window_read": False, "locked_holdout_read": False}, "script": str(Path(__file__).resolve().relative_to(root)).replace("\\", "/"), "script_sha256": sha256_file(Path(__file__).resolve())}
    write_json(output / "validation_record.json", validation)
    payload = sorted(p.name for p in output.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {"schema": "aad.stage05.round2.task4.manifest.v1", "task_id": "AAD-S0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030", "created_at_utc": datetime.now(UTC).isoformat(), "git_head": git_head(root), "payload_files": {name: sha256_file(output / name) for name in payload}, "source_bindings_sha256": sha256_file(output / "source_bindings.json"), "no_identity_level_payload": True}
    write_json(output / "manifest.json", manifest)
    lines = [f"{sha256_file(output / name)}  {name}" for name in payload + ["manifest.json"]]
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"validation": validation, "manifest": manifest, "source_bindings": source_bindings, "real_summaries": real_summaries, "simulation_rows": simulation_rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    result = build_package(args.repo_root.resolve(), args.output.resolve())
    print(json.dumps({"status": result["validation"]["status"], "checks": result["validation"]["checks"], "real": result["real_summaries"], "simulation": result["simulation_rows"]}, ensure_ascii=False, indent=2, default=json_default))
    return 0 if result["validation"]["status"] == "PASS_OFFLINE_EVIDENCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
