"""E15-A real-trajectory calibration pipeline.

The pipeline measures trajectory-observable rear-end risk only.  It contains no
message, adoption, treatment, or causal-effect inference.
"""

from __future__ import annotations

import hashlib
import io
import json
import platform
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from riskprop.calibration import (
    RISK_EVENT_COLUMNS,
    sha256_file,
    validate_real_state_table,
    validate_risk_event_table,
)
from riskprop.real_trajectory import add_ngsim_leader_ttc


_ALLOWED_CALIBRATION_ASSETS = frozenset({"ngsim_us101", "ngsim_lankershim"})


def standardize_ngsim_states(
    trajectories: pd.DataFrame, *, site: str, window_id: str
) -> pd.DataFrame:
    enriched = add_ngsim_leader_ttc(
        trajectories, run_id=f"ngsim_{_slug(site)}_{_slug(window_id)}"
    )
    frame_id = _optional_numeric(enriched, ("Frame_ID", "frame_id"))
    section = _optional_text(enriched, ("Section_ID", "section_id"))
    intersection = _optional_text(enriched, ("Int_ID", "intersection_id"))
    location = _optional_text(enriched, ("Location", "location"))
    road_id = location.where(location.notna(), section)
    road_id = road_id.where(road_id.notna(), intersection).fillna(site)
    raw_speed = _optional_numeric(enriched, ("v_Vel", "v_vel"))
    raw_acceleration = _optional_numeric(enriched, ("v_Acc", "v_acc"))
    raw_headway = _optional_numeric(
        enriched, ("Space_Hdwy", "Space_Headway", "space_headway")
    )
    result = pd.DataFrame(
        {
            "dataset": "NGSIM",
            "site": site,
            "window_id": window_id,
            "vehicle_id": enriched["id"].astype("string"),
            "time_s": enriched["time_s"],
            "frame_id": frame_id,
            "x_m": enriched["x_m"],
            "y_m": enriched["y_m"],
            "speed_mps": enriched["speed_mps"],
            "acceleration_mps2": enriched["acceleration_mps2"],
            "road_id": road_id.astype("string"),
            "lane_id": enriched["lane_id"].astype("string"),
            "leader_id": enriched["leader_id"].astype("string"),
            "net_gap_m": enriched["headway_m"],
            "closing_speed_mps": enriched["closing_speed_mps"],
            "ttc_valid": enriched["ttc_valid"],
            "ttc_s": enriched["ttc_s"],
            "drac_mps2": enriched["drac_mps2"],
            "measurement_status": enriched["measurement_status"].astype("string"),
            "missing_reason": enriched["missing_reason"].astype("string"),
            "raw_speed_fps": raw_speed,
            "raw_acceleration_fps2": raw_acceleration,
            "raw_space_headway_ft": raw_headway,
            "raw_unit_system": "imperial",
        }
    )
    ordered = result.sort_values(["vehicle_id", "time_s", "frame_id"], na_position="last")
    previous_leader = ordered.groupby("vehicle_id", sort=False)["leader_id"].shift()
    ordered["leader_changed"] = (
        previous_leader.notna()
        & ordered["leader_id"].notna()
        & previous_leader.ne(ordered["leader_id"])
    )
    position = ordered.groupby("vehicle_id", sort=False).cumcount()
    group_size = ordered.groupby("vehicle_id", sort=False)["vehicle_id"].transform("size")
    ordered["trajectory_boundary"] = (position == 0) | (position == group_size - 1)
    result = ordered.sort_index()
    validate_real_state_table(result)
    return result


def extract_rear_end_events(
    states: pd.DataFrame,
    *,
    provisional_ttc_threshold_s: float = 2.0,
    max_gap_s: float = 0.11,
    minimum_duration_s: float = 0.1,
) -> pd.DataFrame:
    """Merge sustained low-TTC frames into calibration candidate episodes."""

    if provisional_ttc_threshold_s <= 0 or max_gap_s <= 0 or minimum_duration_s <= 0:
        raise ValueError("threshold and duration parameters must be positive")
    candidates = states[
        states["ttc_valid"].fillna(False)
        & (pd.to_numeric(states["ttc_s"], errors="coerce") < provisional_ttc_threshold_s)
    ].copy()
    if candidates.empty:
        return pd.DataFrame(columns=RISK_EVENT_COLUMNS)
    candidates = candidates.sort_values(["vehicle_id", "leader_id", "time_s"])
    time_gap = candidates.groupby(["vehicle_id", "leader_id"], dropna=False)["time_s"].diff()
    new_segment = time_gap.isna() | (time_gap > max_gap_s + 1e-9)
    candidates["_segment"] = new_segment.groupby(
        [candidates["vehicle_id"], candidates["leader_id"]], dropna=False
    ).cumsum()
    rows: list[dict[str, object]] = []
    group_columns = ["dataset", "site", "window_id", "vehicle_id", "leader_id", "_segment"]
    for key, group in candidates.groupby(group_columns, dropna=False, sort=True):
        start = float(group["time_s"].min())
        end = float(group["time_s"].max())
        duration = end - start
        if duration + 1e-12 < minimum_duration_s:
            continue
        dataset, site, window_id, vehicle_id, leader_id, segment = key
        stable_key = f"{dataset}|{site}|{window_id}|{vehicle_id}|{leader_id}|{start:.6f}|{segment}"
        rows.append(
            {
                "event_id": "e15a_" + hashlib.sha256(stable_key.encode()).hexdigest()[:16],
                "dataset": dataset,
                "site": site,
                "window_id": window_id,
                "vehicle_id": vehicle_id,
                "leader_id": leader_id,
                "conflict_type": "rear_end",
                "event_start_s": start,
                "event_end_s": end,
                "event_duration_s": duration,
                "ttc_min_s": float(group["ttc_s"].min()),
                "drac_max_mps2": float(group["drac_mps2"].max()),
                "pet_s": float("nan"),
                "inclusion_status": "calibration_candidate",
                "exclusion_reason": "",
                "algorithm_version": "e15a.ngsim.v1",
                "raw_frame_count": int(len(group)),
            }
        )
    events = pd.DataFrame(rows, columns=RISK_EVENT_COLUMNS)
    if not events.empty:
        validate_risk_event_table(events)
    return events


def write_e15a_ngsim_package(
    *,
    output_dir: str | Path,
    sources: Iterable[Mapping[str, object]],
    provisional_ttc_threshold_s: float = 2.0,
) -> Path:
    """Process only explicitly listed calibration windows into a sealed package."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    states_dir = output_dir / "states"
    states_dir.mkdir()
    event_frames = []
    source_audit = []
    for source in sources:
        asset_id = str(source["asset_id"])
        if asset_id not in _ALLOWED_CALIBRATION_ASSETS:
            raise ValueError(f"asset is not authorized for E15-A calibration: {asset_id}")
        path = Path(source["path"])
        raw = _read_source(path, source)
        states = standardize_ngsim_states(
            raw, site=str(source["site"]), window_id=str(source["window_id"])
        )
        state_name = f"{asset_id}__{_slug(str(source['window_id']))}.parquet"
        states.to_parquet(states_dir / state_name, index=False)
        events = extract_rear_end_events(
            states, provisional_ttc_threshold_s=provisional_ttc_threshold_s
        )
        event_frames.append(events)
        source_audit.append(
            {
                "asset_id": asset_id,
                "window_id": str(source["window_id"]),
                "input_sha256": sha256_file(path),
                "state_rows": int(len(states)),
                "valid_ttc_rows": int(states["ttc_valid"].sum()),
                "event_rows": int(len(events)),
            }
        )
    all_events = (
        pd.concat(event_frames, ignore_index=True)
        if event_frames
        else pd.DataFrame(columns=RISK_EVENT_COLUMNS)
    )
    all_events.to_parquet(output_dir / "risk_events.parquet", index=False)
    config = {
        "schema_version": "e15a.config.v1",
        "experiment_id": "E15-A",
        "provisional_ttc_threshold_s": provisional_ttc_threshold_s,
        "scientific_claim_eligible": False,
        "locked_holdout_opened": False,
    }
    audit = {
        "schema_version": "e15a.audit.v1",
        "experiment_id": "E15-A",
        "scientific_claim_eligible": False,
        "locked_holdout_opened": False,
        "gate_status": "pending_pneuma_and_blind_reaudit",
        "sources": source_audit,
    }
    provenance = {
        "schema_version": "e15a.provenance.v1",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "python": sys.version,
        "platform": platform.platform(),
        "working_directory": str(Path.cwd().resolve()),
    }
    for name, payload in (
        ("config_frozen.json", config),
        ("audit.json", audit),
        ("provenance.json", provenance),
    ):
        (output_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _seal_directory(output_dir)
    return output_dir


def _read_source(path: Path, source: Mapping[str, object]) -> pd.DataFrame:
    with zipfile.ZipFile(path) as outer:
        inner_member = source.get("inner_zip_member")
        csv_member = str(source["csv_member"])
        if inner_member:
            with zipfile.ZipFile(io.BytesIO(outer.read(str(inner_member)))) as inner:
                with inner.open(csv_member) as handle:
                    return pd.read_csv(handle)
        with outer.open(csv_member) as handle:
            return pd.read_csv(handle)


def _seal_directory(output_dir: Path) -> None:
    files = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
    entries = [
        {
            "path": path.relative_to(output_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]
    (output_dir / "manifest.json").write_text(
        json.dumps(
            {"schema_version": "e15a.manifest.v1", "files": entries},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    checksum_files = [*files, output_dir / "manifest.json"]
    lines = [
        f"{sha256_file(path)}  {path.relative_to(output_dir).as_posix()}"
        for path in checksum_files
    ]
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


def _optional_numeric(frame: pd.DataFrame, names: tuple[str, ...]) -> pd.Series:
    column = next((name for name in names if name in frame.columns), None)
    if column is None:
        return pd.Series(float("nan"), index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce")


def _optional_text(frame: pd.DataFrame, names: tuple[str, ...]) -> pd.Series:
    column = next((name for name in names if name in frame.columns), None)
    if column is None:
        return pd.Series(pd.NA, index=frame.index, dtype="string")
    return frame[column].astype("string")


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")

