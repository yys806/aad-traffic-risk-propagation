"""Read-only real-traffic reconstruction runner for Stage 0.5.

Produces the evidence package that explains how the real target congestion is
formed, from the sealed Stage 0.2 canonical trajectory states plus the bundled
official NGSIM aggregates. It never runs SUMO and never writes Gate state.

Usage
-----
python code/scripts/run_stage_0_5_trajectory_reconstruction.py --output-root <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_trajectory_reconstruction as tr  # noqa: E402

DEFAULT_STATES = (
    "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states"
)
DEFAULT_OFFICIAL = "code/configs/stage_0_5_ngsim_official_reference_v1.json"
DEFAULT_OUTPUT = "code/outputs/formal/calibration/stage_0_5_trajectory_reconstruction_v1"
RESULT_ID = "RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1"

# SUMO Krauss parameters actually used by the frozen conditional candidate
# (code/outputs/.../stage_0_5_final_candidate_v1). Recorded here so that the
# capacity statement is bound to the parameters that produced the failed runs.
SUMO_KRAUSS = {
    "car_follow_model": "Krauss",
    "tau_s": 1.0,
    "min_gap_m": 2.5,
    "length_m": {"motorcycle": 2.4384, "passenger": 4.4196, "truck": 10.009694845360826},
    "accel_mps2": 2.6,
    "decel_mps2": 4.5,
    "emergency_decel_mps2": 9.0,
    "sigma": 0.5,
    "speed_factor": 1.0,
    "max_speed_mps": 27.78,
    "action_step_length_s": 0.1,
}
FREE_FLOW_SPEED_MPS = 27.78
NGSIM_FREE_FLOW_SPEED_MPS = 29.06  # 65 mph posted-speed reference, informational


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False), encoding="utf-8")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.6f")


def peak_capacity_veh_h_lane(tau_s: float, length_m: float, min_gap_m: float, speed_mps: float) -> float:
    """Analytic Krauss saturation capacity: headway = tau + (length + minGap)/v."""
    headway = tau_s + (length_m + min_gap_m) / speed_mps
    return 3600.0 / headway


def official_reference_provenance(spec: dict) -> dict[str, object]:
    """Record the source ZIP members and sizes behind the transcribed official tables."""
    import zipfile

    members = []
    for entry in spec.get("source_files", []):
        if " :: " not in entry:
            members.append({"source": entry, "kind": "dataset_file", "exists": (REPO_ROOT / entry).is_file()})
            continue
        archive, _, inner = entry.partition(" :: ")
        archive = archive.strip()
        inner = inner.strip()
        path = REPO_ROOT / archive
        record: dict[str, object] = {"source": entry, "archive": archive, "member": inner, "exists": path.is_file()}
        if path.is_file():
            record["archive_bytes"] = path.stat().st_size
            record["archive_sha256"] = sha256_file(path)
            try:
                with zipfile.ZipFile(path) as outer:
                    if " :: " in inner:
                        nested, _, leaf = inner.partition(" :: ")
                        payload = outer.read(nested.strip())
                        nested_bytes = __import__("io").BytesIO(payload)
                        with zipfile.ZipFile(nested_bytes) as inner_zip:
                            leaf = leaf.strip()
                            record["member_bytes"] = inner_zip.getinfo(leaf).file_size
                            record["member_crc32"] = inner_zip.getinfo(leaf).CRC
                    else:
                        record["member_bytes"] = outer.getinfo(inner).file_size
                        record["member_crc32"] = outer.getinfo(inner).CRC
            except Exception as exc:  # pragma: no cover - provenance best effort
                record["read_error"] = str(exc)
        members.append(record)
    return {
        "result_id": RESULT_ID,
        "transcription_method": spec.get("transcription_method"),
        "transcription_status": spec.get("transcription_status"),
        "ocr_engine": "rapidocr_onnxruntime (local, offline)",
        "note": (
            "The bundled official PDFs carry vector text without a usable ToUnicode mapping, so pages "
            "were rasterised and transcribed by local OCR plus manual reading; each recorded number was "
            "read back against the rendered page. The reference is Unverified until it cross-checks "
            "against the independently computed trajectory aggregates."
        ),
        "members": members,
    }


def build_official_crosscheck(
    official: dict,
    boundary: dict[str, dict],
    geometry: dict[str, dict],
    local: dict[str, dict],
    ramps: dict[str, dict],
) -> dict[str, object]:
    checks = []
    for window_id, entry in official["windows"].items():
        flows = boundary[window_id]
        aux = geometry[window_id]["roles"]
        ramp = ramps[window_id]
        upstream = entry.get("input_output", {}).get("entering_freeway_lanes_sum_vehicles")
        official_total = next(
            row["flow_vph"] for row in entry["aggregate_by_time"] if row["period"] == "average"
        )
        official_sms = next(
            row["sms_fps"] for row in entry["aggregate_by_time"] if row["period"] == "average"
        ) * 0.3048
        checks.append(
            {
                "window": window_id,
                "official_entering_freeway_lanes_vehicles": upstream,
                "derived_upstream_crossings_vehicles": flows["entered_vehicles"],
                "official_entering_flow_veh_h": (
                    upstream / 900.0 * 3600.0 if upstream is not None else None
                ),
                "derived_upstream_flow_veh_h_at_150m": flows["entry_flow_veh_h"],
                "derived_upstream_flow_veh_h_lane": flows["entry_flow_veh_h_lane"],
                "official_average_section_flow_vph": official_total,
                "derived_exit_flow_veh_h_at_350m": flows["exit_flow_veh_h"],
                "official_average_sms_mps": official_sms,
                "derived_local_speed_mps": local[window_id]["speed_mean_mps"],
                "derived_local_density_veh_km_lane": local[window_id]["density_veh_km_lane"],
                "official_on_ramp_sum_vehicles": entry.get("input_output", {}).get("on_ramp_flow_sum_vehicles"),
                "derived_on_ramp_entry_flow_veh_h": ramp["onramp_entry_flow_veh_h"],
                "lane_roles": {
                    "mainline": aux["mainline_lanes"],
                    "auxiliary": aux["auxiliary_lane"],
                    "onramp": aux["onramp_lane"],
                    "offramp": aux["offramp_lane"],
                },
            }
        )
    return {
        "status": "Derived",
        "purpose": "Independent comparison between the bundled official NGSIM aggregates and the trajectory-derived boundary flows, so that neither alone carries the reconstruction.",
        "checks": checks,
        "agreement_note": (
            "The official section flow table is measured at section midpoints over the whole "
            "2,100 ft cross-section (including the auxiliary lane) and over 15 minutes; the "
            "trajectory-derived numbers are 720 s crossings of one interior plane. Agreement is "
            "expected in magnitude, not to the digit."
        ),
    }


def capacity_diagnosis(local: dict[str, dict]) -> dict[str, object]:
    capacities = {
        kind: peak_capacity_veh_h_lane(
            SUMO_KRAUSS["tau_s"], length, SUMO_KRAUSS["min_gap_m"], FREE_FLOW_SPEED_MPS
        )
        for kind, length in SUMO_KRAUSS["length_m"].items()
    }
    observed = {
        window: {
            "density_veh_km_lane": value["density_veh_km_lane"],
            "speed_mean_mps": value["speed_mean_mps"],
            "flow_veh_h_lane": value["flow_veh_h_lane_consistency"],
            "implied_free_flow_density_at_same_flow_veh_km_lane": value["flow_veh_h_lane_consistency"]
            / (FREE_FLOW_SPEED_MPS * 3.6),
        }
        for window, value in local.items()
    }
    return {
        "status": "Derived",
        "sumo_krauss_parameters": SUMO_KRAUSS,
        "analytic_saturation_capacity_veh_h_lane": capacities,
        "sumo_passenger_capacity_veh_h_lane": capacities["passenger"],
        "observed_congested_branch": observed,
        "ratio_capacity_to_observed_flow": {
            window: capacities["passenger"] / value["flow_veh_h_lane"]
            for window, value in observed.items()
        },
        "conclusion": (
            "The two real windows sit on the congested branch: the same measured cross-section "
            "flow is compatible with a free-flow state at about 16.5 veh/km/lane and with the "
            "observed congested state at 43.5-50.5 veh/km/lane. The Krauss parameters actually "
            "used by the failed conditional candidate give an analytic lane capacity far above "
            "the observed congested flow, so at the observed demand that scenario has no binding "
            "supply and can only reach the free-flow branch. Matching the observed flow therefore "
            "cannot identify the observed state; the state has to be supported by the initial "
            "condition, by the demand history, or by a supply restriction whose capacity is on "
            "the order of the observed congested flow."
        ),
        "not_a_science_tolerance": True,
    }


def hypothesis_register(official: dict) -> list[dict[str, str]]:
    return [
        {
            "id": "R1",
            "statement": "The observed local region sits immediately downstream of an on-ramp merge and just upstream of an off-ramp diverge, and a dedicated auxiliary lane exists inside the region from the merge to the diverge.",
            "class": "Observation",
            "evidence": "lane_geometry.json + lane_geometry per lane 6/7/8 support; official NGSIM metadata states five mainline lanes throughout plus one auxiliary lane between the Ventura Boulevard on-ramp and the Cahuenga Boulevard off-ramp.",
        },
        {
            "id": "R2",
            "statement": "Both approved windows are on the congested branch of the fundamental diagram, not the free-flow branch.",
            "class": "Observation",
            "evidence": "local_state.json (10.51 m/s / 43.54 and 7.92 m/s / 50.51) with measured cross-section flows 1,647 and 1,451-1,474 veh/h/lane; official Table 3 SMS 21.45-27.70 mph and 20.88-23.22 mph.",
        },
        {
            "id": "R3",
            "statement": "The observed cross-section flow does not identify the traffic state: one flow value maps to two density/speed combinations.",
            "class": "Derived",
            "evidence": "capacity_diagnosis.json (implied free-flow density at the same flow is about 16.5 veh/km/lane versus the observed 43.5-50.5) and the failed conditional runs that reproduced the same flow on the free-flow branch.",
        },
        {
            "id": "R4",
            "statement": "During 7:50-8:05 the whole study cross-section is congested and gets worse over time in every section, while the section first accumulates then drains vehicles.",
            "class": "Observation",
            "evidence": "official Table 8 (space mean speed by section and 5-minute period: 45.44 fps then 41.88 fps then 30.03 fps) and Table 4 (net entering minus exiting +31, +24, +16, -38, -33 vehicles).",
        },
        {
            "id": "R5",
            "statement": "The on-ramp contributes a measurable inflow that the failed SUMO candidate did not contain at all.",
            "class": "Observation",
            "evidence": "official Table 4 on-ramp sum 137 vehicles per 15 minutes (548 veh/h) for 0750 and 130 (520 veh/h) for 0805; trajectory lane-7 entries and official Table 6 flow step 8,064 -> 8,612 veh/h across the merge.",
        },
        {
            "id": "R6",
            "statement": "The upstream boundary demand of the real segment is directly observable; the true upstream demand of the freeway beyond the observed segment is not.",
            "class": "Unidentifiable",
            "evidence": "the canonical states start at the segment boundary, so arrivals are observed only from that boundary inward; congestion upstream of the boundary is not observable.",
        },
        {
            "id": "R7",
            "statement": "The on-ramp arrival process is only partially observed because the ramp lane is observed over about 59 m immediately before the merge.",
            "class": "Unidentifiable",
            "evidence": "lane_geometry on-ramp support (128.7-187.6 m) and ramp_flows.json first-observation caveat.",
        },
        {
            "id": "R8",
            "statement": "Which mechanism holds the region on the congested branch (initial condition / hysteresis, demand transient, or a downstream capacity restriction) cannot be identified from the observed windows alone.",
            "class": "Unidentifiable",
            "evidence": "the windows are already congested at their start and the net in-out difference is small compared with the accumulation needed to build the queue, so the queue-forming event lies outside the observed time interval.",
        },
        {
            "id": "R9",
            "statement": "A SUMO scenario whose only capacity limit is the Krauss car-following model at the recorded parameters cannot be made to reproduce the observed congested state at the observed flow by adding the observed ramp or by matching the observed flow.",
            "class": "Derived",
            "evidence": "capacity_diagnosis.json plus the failed conditional candidate that reproduced the internal cross-section flow on the free-flow branch.",
        },
    ]


def build(args: argparse.Namespace) -> Path:
    output = Path(args.output_root)
    if not output.is_absolute():
        output = REPO_ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    states_root = REPO_ROOT / args.states_root
    source_files = {}
    frames: dict[str, pd.DataFrame] = {}
    for window_id in tr.CALIBRATION_WINDOWS:
        path = states_root / f"ngsim_{window_id}.parquet"
        if not path.is_file():
            raise SystemExit(f"missing sealed calibration state: {path}")
        source_files[window_id] = {
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        frames[window_id] = tr.load_calibration_states(str(path), window_id)

    # refuse any sealed window before producing anything
    for sealed in ("us101__0820_0835", "ngsim_lankershim__complete"):
        if sealed in str(states_root):
            raise SystemExit("sealed window path refused")

    geometry: dict[str, object] = {}
    local: dict[str, dict] = {}
    conservation: dict[str, object] = {}
    boundary: dict[str, object] = {}
    ramps: dict[str, object] = {}
    waves: dict[str, object] = {}
    interactions: dict[str, object] = {}
    uncertainty: dict[str, object] = {}
    space_time_tables: list[pd.DataFrame] = []
    fd_tables: list[pd.DataFrame] = []
    occupancy_tables: list[pd.DataFrame] = []
    boundary_block_tables: list[pd.DataFrame] = []
    sectional_tables: list[pd.DataFrame] = []

    for window_id, frame in frames.items():
        window = tr.CALIBRATION_WINDOWS[window_id]
        span = tr.window_clock_span(frame)
        geo = tr.lane_geometry(frame)
        geometry[window_id] = {
            "status": "Observation",
            "clock_span_s": list(span),
            "states": int(len(frame)),
            "vehicles": int(frame.vehicle_id.nunique()),
            "trajectories": int(frame.trajectory_id.nunique()),
            "per_lane": geo.round(6).to_dict(orient="records"),
            "roles": tr.classify_lanes(geo),
        }
        local[window_id] = tr.local_state(frame, window=window)
        entry = tr.boundary_crossings(frame, at_m=tr.REGION_START_M, lanes=tr.MAINLINE_LANES, window=window)
        exit_all = tr._crossings_from_subset(
            frame, at_m=tr.REGION_END_M, lanes=(*tr.MAINLINE_LANES, tr.AUXILIARY_LANE), window=window
        )
        boundary[window_id] = {
            "status": "Derived",
            "window_s": list(window),
            "region_m": [tr.REGION_START_M, tr.REGION_END_M],
            "entry_lanes": list(tr.MAINLINE_LANES),
            "exit_lanes": [*tr.MAINLINE_LANES, tr.AUXILIARY_LANE],
            "entered_vehicles": int(len(entry)),
            "exited_vehicles": int(len(exit_all)),
            "entry_flow_veh_h": len(entry) / (window[1] - window[0]) * 3600.0,
            "exit_flow_veh_h": len(exit_all) / (window[1] - window[0]) * 3600.0,
            "entry_flow_veh_h_lane": len(entry) / (window[1] - window[0]) * 3600.0 / 5.0,
            "entry_speed_mean_mps": float(entry.speed_mps.mean()),
            "exit_speed_mean_mps": float(pd.Series(exit_all.speed_mps).mean()) if len(exit_all) else None,
            "entry_by_lane": {str(k): int(v) for k, v in entry.lane_id.value_counts().items()},
            "exit_by_lane": {str(k): int(v) for k, v in exit_all.lane_id.value_counts().items()},
        }
        closed = tr.vehicle_conservation(
            frame,
            region=(200.0, 350.0),
            lanes_in=(*tr.MAINLINE_LANES, tr.AUXILIARY_LANE),
            lanes_out=(*tr.MAINLINE_LANES, tr.AUXILIARY_LANE),
            window=window,
            label="closed_six_lane_cross_section",
        )
        approved_region = tr.vehicle_conservation(
            frame,
            region=(tr.REGION_START_M, tr.REGION_END_M),
            lanes_in=tr.MAINLINE_LANES,
            lanes_out=(*tr.MAINLINE_LANES, tr.AUXILIARY_LANE),
            window=window,
            label="approved_D1_region_five_lanes_in_six_lanes_out",
        )
        conservation[window_id] = {
            "status": "Derived",
            "closed_cross_section": closed,
            "approved_region": approved_region,
            "interpretation": (
                "The approved D1 region sees lanes 1-5 only, but a sixth (auxiliary) lane is "
                "physically present inside it from the on-ramp merge onward, so that region is not "
                "a closed control volume and its residual mixes accumulation with lateral "
                "transfer. The six-lane cross-section region starting after the merge is closed "
                "and is the conservation check used here."
            ),
        }
        ramps[window_id] = tr.ramp_flows(frame, window=window)
        space = tr.space_time(frame, window=window, y_step_m=50.0, t_step_s=60.0)
        speed_table = space["speed_mps"].stack().rename("speed_mps").reset_index()
        speed_table.columns = ["y_start_m", "t_start_s", "speed_mps"]
        density_table = space["density_veh_km_lane"].stack().rename("density_veh_km_lane").reset_index()
        density_table.columns = ["y_start_m", "t_start_s", "density_veh_km_lane"]
        low_table = space["low_speed_share"].stack().rename("low_speed_share").reset_index()
        low_table.columns = ["y_start_m", "t_start_s", "low_speed_share"]
        merged = speed_table.merge(density_table, on=["y_start_m", "t_start_s"]).merge(
            low_table, on=["y_start_m", "t_start_s"]
        )
        merged.insert(0, "window", window_id)
        space_time_tables.append(merged)

        fd = tr.fundamental_diagram(frame, window=window, y_step_m=100.0, t_step_s=30.0)
        fd = fd.rename(columns={"t_bin": "t_start_s", "y_bin": "y_start_m"})
        fd.insert(0, "window", window_id)
        fd_tables.append(fd)

        occupancy = tr.occupancy_series(frame, window=window, block_s=30.0)
        occupancy.insert(0, "window", window_id)
        occupancy_tables.append(occupancy)

        blocks = tr.flow_table(entry, window, block_s=30.0)
        blocks.insert(0, "window", window_id)
        blocks["kind"] = f"entry_{int(tr.REGION_START_M)}m"
        boundary_block_tables.append(blocks)

        sectional = tr.sectional_minimum(frame, window=window, y_step_m=100.0, t_step_s=300.0)
        sectional.insert(0, "window", window_id)
        sectional_tables.append(sectional)

        waves[window_id] = tr.jam_waves(frame, window=window)
        interactions[window_id] = tr.interaction_stats(frame, window=window)
        uncertainty[window_id] = {
            "speed": vars(tr.cluster_bootstrap(frame, window=window, metric="speed")),
            "density": vars(tr.cluster_bootstrap(frame, window=window, metric="density")),
            "status": "Conditional cluster bootstrap sensitivity only; within-source sampling variability of trajectory clusters, not a rate confidence interval and not a science tolerance.",
        }

    write_json(output / "source_audit.json", {
        "result_id": RESULT_ID,
        "version": tr.VERSION,
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": source_files,
        "approved_windows": list(tr.CALIBRATION_WINDOWS),
        "sealed_windows_not_read": ["us101__0820_0835", "ngsim_lankershim__complete", "locked_holdout"],
        "sealed_window_rows_materialised": 0,
        "validation_window_read": False,
        "canonical_region_m": [tr.REGION_START_M, tr.REGION_END_M],
        "canonical_mainline_lanes": list(tr.MAINLINE_LANES),
        "p2_semantics_modified": False,
        "identity_clock_quality_semantics_modified": False,
    })
    write_json(output / "lane_geometry.json", geometry)
    write_json(output / "boundary_flows.json", boundary)
    write_json(output / "conservation.json", conservation)
    write_json(output / "ramp_flows.json", ramps)
    write_json(output / "local_state.json", local)
    write_json(output / "jam_waves.json", waves)
    write_json(output / "interaction_stats.json", interactions)
    write_json(output / "cluster_uncertainty.json", uncertainty)

    write_csv(output / "space_time_60s.csv", pd.concat(space_time_tables, ignore_index=True))
    write_csv(output / "fundamental_diagram_30s.csv", pd.concat(fd_tables, ignore_index=True))
    write_csv(output / "occupancy_30s.csv", pd.concat(occupancy_tables, ignore_index=True))
    write_csv(output / "boundary_flow_30s.csv", pd.concat(boundary_block_tables, ignore_index=True))
    write_csv(output / "sectional_minimum_300s.csv", pd.concat(sectional_tables, ignore_index=True))

    official = json.loads((REPO_ROOT / args.official_reference).read_text(encoding="utf-8"))
    write_json(output / "official_reference_provenance.json", official_reference_provenance(official))
    write_json(output / "official_crosscheck.json", build_official_crosscheck(official, boundary, geometry, local, ramps))
    write_json(output / "capacity_diagnosis.json", capacity_diagnosis(local))
    write_json(output / "hypothesis_register.json", {
        "status": "Mixed; each entry carries its own evidence class",
        "classes": ["Observation", "Derived", "Hypothesis", "Unidentifiable"],
        "entries": hypothesis_register(official),
    })

    summary = {
        "result_id": RESULT_ID,
        "version": tr.VERSION,
        "windows": {
            window_id: {
                "local": local[window_id],
                "boundary": boundary[window_id],
                "conservation_closed": conservation[window_id]["closed_cross_section"],
                "ramp": ramps[window_id],
                "slow_cell_fraction": waves[window_id]["slow_cell_fraction"],
                "largest_slow_component": (waves[window_id]["components"][0] if waves[window_id]["components"] else None),
            }
            for window_id in local
        },
        "scientific_claim_eligible": False,
        "gate_status": "pending_simulation_sample",
        "reality_coverage_accepted": False,
    }
    write_json(output / "reconstruction_summary.json", summary)

    plan = {
        "result_id": RESULT_ID,
        "version": tr.VERSION,
        "mode": "read-only trajectory reconstruction; no SUMO run; no Gate mutation",
        "inputs": source_files,
        "official_reference": {
            "path": args.official_reference,
            "sha256": sha256_file(REPO_ROOT / args.official_reference),
        },
        "code": {
            "module": "code/src/riskprop/stage_0_5_trajectory_reconstruction.py",
            "entrypoint": "code/scripts/run_stage_0_5_trajectory_reconstruction.py",
            "module_sha256": sha256_file(CODE_ROOT / "src/riskprop/stage_0_5_trajectory_reconstruction.py"),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "git_head": subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "sealed_windows_not_read": ["us101__0820_0835", "nsgim_lankershim__complete"],
    }
    write_json(output / "experiment_plan.json", plan)
    plan_bytes = (output / "experiment_plan.json").read_bytes()
    (output / "PLAN_SHA256").write_text(hashlib.sha256(plan_bytes).hexdigest() + "  experiment_plan.json\n", encoding="utf-8")

    names = sorted(path.name for path in output.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    lines = []
    for name in names:
        lines.append(f"{sha256_file(output / name)}  {name}")
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(output / "manifest.json", {
        "schema_version": "aad.evidence-manifest.v1",
        "result_id": RESULT_ID,
        "files": [{"path": name, "sha256": sha256_file(output / name), "bytes": (output / name).stat().st_size} for name in names],
    })
    print(f"wrote {len(names)} files to {output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states-root", default=DEFAULT_STATES)
    parser.add_argument("--official-reference", default=DEFAULT_OFFICIAL)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
