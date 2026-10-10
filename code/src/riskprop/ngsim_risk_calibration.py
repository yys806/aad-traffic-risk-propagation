"""Stage 0.2 real-trajectory calibration pipeline.

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
_NGSIM_TXT_COLUMNS = (
    "Vehicle_ID", "Frame_ID", "Total_Frames", "Global_Time", "Local_X", "Local_Y",
    "Global_X", "Global_Y", "v_Length", "v_Width", "v_Class", "v_Vel", "v_Acc",
    "Lane_ID", "Preceeding", "Following", "Space_Hdwy", "Time_Hdwy",
)


def annotate_ngsim_trajectory_identity(
    trajectories: pd.DataFrame,
    *,
    site: str,
    source_period: str = "unknown",
    source_member: str = "unknown",
) -> pd.DataFrame:
    """Identify diagnostic clock/frame sequences, not physical vehicles.

    Global_Time - 100 * Frame_ID is an observed clock anchor, not an official
    period label. Original rows remain in file order. Conflicting sequences
    are retained with uncertainty propagated over the whole diagnostic group.
    """
    columns = {
        "vehicle": next(c for c in ("Vehicle_ID", "vehicle_id") if c in trajectories),
        "frame": next(c for c in ("Frame_ID", "frame_id") if c in trajectories),
        "time": next(c for c in ("Global_Time", "global_time") if c in trajectories),
    }
    result = trajectories.reset_index(drop=True).copy()
    for name, fallback in (("source_member", source_member), ("source_period", source_period)):
        if name not in result:
            result[name] = fallback
        result[name] = result[name].astype("string").fillna("unknown")
    result["original_row_number"] = pd.RangeIndex(len(result)) + 1
    result["original_vehicle_id"] = result[columns["vehicle"]].astype("string")
    frame = pd.to_numeric(result[columns["frame"]], errors="coerce")
    time = pd.to_numeric(result[columns["time"]], errors="coerce")
    valid_fields = time.notna() & frame.notna() & time.mod(1).eq(0) & frame.mod(1).eq(0)
    anchor = (time - frame * 100).where(valid_fields).astype("Int64")
    result["diagnostic_clock_anchor_ms"] = anchor
    # Rank observed anchors per ID; independent of original file row ordering.
    identity_scope = [result[c] for c in ("source_member", "source_period", "original_vehicle_id")]
    segment_index = anchor.groupby(identity_scope).rank(method="dense").sub(1).fillna(-1).astype("int64")
    result["segment_index"] = segment_index
    result["trajectory_id"] = (
        "NGSIM|" + str(site) + "|" + result["source_period"] + "|" + result["source_member"]
        + "|" + result["original_vehicle_id"] + "|clock" + anchor.astype("string").fillna("unknown")
    )
    duplicate_time = result.duplicated(["source_member", "source_period", "original_vehicle_id", columns["time"]], keep=False)
    duplicate_frame = result.duplicated(["trajectory_id", columns["frame"]], keep=False)
    direct_uncertain = ~valid_fields | duplicate_time | duplicate_frame
    if "Total_Frames" in result:
        totals = pd.to_numeric(result["Total_Frames"], errors="coerce")
        direct_uncertain |= totals.isna() | totals.groupby(result["trajectory_id"]).transform("nunique").gt(1)
    identity_uncertain = direct_uncertain.groupby(result["trajectory_id"]).transform("any")
    ordered = result.assign(_time=time, _frame=frame).sort_values(
        ["trajectory_id", "_time", "_frame", "original_row_number"], kind="stable"
    )
    sequence = ordered.groupby("trajectory_id", sort=False)
    identity_break = sequence.cumcount().eq(0) & segment_index.loc[ordered.index].gt(0)
    observation_gap = sequence["_time"].diff().gt(100).fillna(False)
    result["identity_uncertain_record"] = direct_uncertain.to_numpy()
    result["identity_break"] = identity_break.reindex(result.index).to_numpy()
    result["observation_gap"] = observation_gap.reindex(result.index).to_numpy()
    result["identity_uncertain"] = identity_uncertain.to_numpy()
    result["identity_status"] = "confirmed"
    segment_counts = result.groupby(["source_member", "source_period", "original_vehicle_id"])["trajectory_id"].transform("nunique")
    result.loc[segment_counts.gt(1), "identity_status"] = "confirmed_segment"
    result.loc[identity_uncertain, "identity_status"] = "identity_uncertain"
    return result


def standardize_ngsim_states(
    trajectories: pd.DataFrame,
    *,
    site: str,
    window_id: str,
    source_period: str = "unknown",
    source_member: str = "unknown",
) -> pd.DataFrame:
    if source_member == "unknown" and "source_member" in trajectories.columns:
        source_member = str(trajectories["source_member"].iloc[0])
    if source_period == "unknown" and "source_period" in trajectories.columns:
        source_period = str(trajectories["source_period"].iloc[0])
    if "trajectory_id" not in trajectories.columns:
        trajectories = annotate_ngsim_trajectory_identity(
            trajectories,
            site=site,
            source_period=source_period,
            source_member=source_member,
        )
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
            "leader_trajectory_id": enriched.get(
                "leader_trajectory_id", enriched["leader_id"]
            ).astype("string"),
            "leader_identity_uncertain": enriched["leader_identity_uncertain"].astype(bool),
            "leader_frame_id": enriched["leader_frame_id"],
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
            "source_member": _optional_text(enriched, ("source_member",)),
            "source_format": _optional_text(enriched, ("source_format",)),
            "trajectory_id": enriched["trajectory_id"].astype("string"),
            "original_vehicle_id": enriched["original_vehicle_id"].astype("string"),
            "source_period": enriched["source_period"].astype("string"),
            "identity_status": enriched["identity_status"].astype("string"),
            "identity_break": enriched["identity_break"].astype(bool),
            "observation_gap": enriched["observation_gap"].astype(bool),
            "identity_uncertain": enriched["identity_uncertain"].astype(bool),
            "identity_uncertain_record": enriched["identity_uncertain_record"].astype(bool),
            "segment_index": enriched["segment_index"],
            "global_time_ms": _optional_numeric(enriched, ("Global_Time", "global_time")).astype("Int64"),
            "diagnostic_clock_anchor_ms": enriched["diagnostic_clock_anchor_ms"],
            "total_frames": _optional_numeric(enriched, ("Total_Frames",)),
            "leader_matched": enriched["leader_matched"].astype(bool),
            "original_row_number": enriched["original_row_number"].astype("int64"),
        }
    )
    ordered = result.sort_values(["trajectory_id", "time_s", "frame_id"], na_position="last")
    previous_leader = ordered.groupby("trajectory_id", sort=False)["leader_trajectory_id"].shift()
    ordered["leader_changed"] = (
        previous_leader.notna()
        & ordered["leader_trajectory_id"].notna()
        & previous_leader.ne(ordered["leader_trajectory_id"])
    )
    position = ordered.groupby("trajectory_id", sort=False).cumcount()
    group_size = ordered.groupby("trajectory_id", sort=False)["trajectory_id"].transform("size")
    ordered["trajectory_boundary"] = (position == 0) | (position == group_size - 1)
    result = ordered.sort_index()
    result["single_frame_reliable"] = (
        result["ttc_valid"] & ~result["identity_uncertain"]
        & ~result["leader_identity_uncertain"] & result["leader_matched"]
    )
    validate_real_state_table(result)
    return result


def extract_rear_end_events(
    states: pd.DataFrame,
    *,
    provisional_ttc_threshold_s: float = 2.0,
    max_gap_s: float = 0.11,
    minimum_duration_s: float = 0.1,
    return_diagnostics: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return reliable engineering candidates; optionally raw/reliable/rejected.

    Reliability is evaluated on the complete state sequence, not only on
    threshold-positive frames. Temporary thresholds are not scientific locks.
    Raw candidates containing any uncertain observation are rejected intact.
    """

    if provisional_ttc_threshold_s <= 0 or max_gap_s <= 0 or minimum_duration_s <= 0:
        raise ValueError("threshold and duration parameters must be positive")
    follower_key = "trajectory_id" if "trajectory_id" in states else "vehicle_id"
    leader_key = "leader_trajectory_id" if "leader_trajectory_id" in states else "leader_id"
    scope_keys = ["dataset", "site", "window_id"]
    scope_keys += [c for c in ("source_period", "source_member") if c in states]
    sequence_keys = [*scope_keys, follower_key]
    ordered = states.copy().sort_values([*sequence_keys, "time_s", "frame_id"], kind="stable")
    full_sequence = ordered.groupby(sequence_keys, dropna=False, sort=False)
    ordered["_observation_position"] = full_sequence.cumcount()
    previous_leader = full_sequence[leader_key].shift()
    ordered["_pair_run"] = (
        previous_leader.isna() | ordered[leader_key].isna()
        | previous_leader.ne(ordered[leader_key]).fillna(True)
    ).groupby([ordered[c] for c in sequence_keys], dropna=False).cumsum()
    candidates = ordered[
        ordered["ttc_valid"].fillna(False)
        & (pd.to_numeric(ordered["ttc_s"], errors="coerce") < provisional_ttc_threshold_s)
    ].copy()
    if candidates.empty:
        empty = pd.DataFrame(columns=RISK_EVENT_COLUMNS)
        if return_diagnostics:
            return empty, empty.copy(), pd.DataFrame(columns=["event_id", "rejection_reason", "raw_frame_count"])
        return empty
    pair_keys = [*sequence_keys, leader_key, "_pair_run"]
    time_gap = candidates.groupby(pair_keys, dropna=False)["time_s"].diff()
    def flag(frame, name):
        return frame[name].fillna(True).astype(bool) if name in frame else pd.Series(False, index=frame.index)
    continuity_block = (
        time_gap.isna()
        | (time_gap > max_gap_s + 1e-9)
        | flag(candidates, "identity_break")
        | flag(candidates, "observation_gap")
    )
    candidates["_segment"] = continuity_block.groupby(
        [candidates[c] for c in pair_keys], dropna=False
    ).cumsum()
    rows: list[dict[str, object]] = []
    reliable_rows: list[dict[str, object]] = []
    rejected_rows: list[dict[str, object]] = []
    group_columns = [*pair_keys, "_segment"]
    for key, group in candidates.groupby(group_columns, dropna=False, sort=True):
        start = float(group["time_s"].min())
        end = float(group["time_s"].max())
        duration = end - start
        if duration + 1e-12 < minimum_duration_s:
            continue
        dataset, site, window_id = (group[c].iloc[0] for c in ("dataset", "site", "window_id"))
        vehicle_id = group["vehicle_id"].iloc[0]
        leader_id = group["leader_id"].iloc[0]
        stable_key = f"{key}|{start:.6f}"
        event_row = {
                "event_id": "stage_0_2_" + hashlib.sha256(stable_key.encode()).hexdigest()[:16],
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
                "algorithm_version": "stage_0_2.ngsim.reliability.v2",
                "raw_frame_count": int(len(group)),
                "trajectory_id": group[follower_key].iloc[0],
                "leader_trajectory_id": group[leader_key].iloc[0],
                "source_member": group["source_member"].iloc[0] if "source_member" in group else "unknown",
                "source_period": group["source_period"].iloc[0] if "source_period" in group else "unknown",
                "original_row_numbers": group["original_row_number"].tolist() if "original_row_number" in group else group.index.tolist(),
            }
        rows.append(event_row)
        rejection_reasons = []
        if bool(flag(group, "identity_uncertain").any()):
            rejection_reasons.append("identity_uncertain")
        if bool(flag(group, "leader_identity_uncertain").any()):
            rejection_reasons.append("leader_identity_uncertain")
        # The first frame after a gap can begin a valid new event. Only links
        # within this event require complete consecutive observations.
        if group["_observation_position"].diff().iloc[1:].ne(1).any():
            rejection_reasons.append("intervening_non_candidate_observation")
        event_ms = (group["global_time_ms"] if "global_time_ms" in group
                    else (group["time_s"] * 1000).round().astype("Int64"))
        if event_ms.diff().iloc[1:].ne(100).any() or group["frame_id"].diff().iloc[1:].ne(1).any():
            rejection_reasons.append("non_consecutive_observations")
        if "leader_frame_id" in group and group["leader_frame_id"].diff().iloc[1:].ne(1).any():
            rejection_reasons.append("non_consecutive_leader_observations")
        leader_matched = group["leader_matched"].fillna(False) if "leader_matched" in group else pd.Series(True, index=group.index)
        if not bool(leader_matched.all()):
            rejection_reasons.append("leader_not_unique_or_matched")
        if rejection_reasons:
            rejected_rows.append(
                {
                    "event_id": event_row["event_id"],
                    "rejection_reason": ";".join(rejection_reasons),
                    "raw_frame_count": int(len(group)),
                }
            )
        else:
            reliable_rows.append(event_row)
    event_columns = (*RISK_EVENT_COLUMNS, "trajectory_id", "leader_trajectory_id", "source_member", "source_period", "original_row_numbers")
    events = pd.DataFrame(rows, columns=event_columns)
    reliable_events = pd.DataFrame(reliable_rows, columns=event_columns)
    rejected_events = pd.DataFrame(rejected_rows, columns=["event_id", "rejection_reason", "raw_frame_count"])
    if not events.empty:
        validate_risk_event_table(events)
    if not reliable_events.empty:
        validate_risk_event_table(reliable_events)
    if return_diagnostics:
        return events, reliable_events, rejected_events
    return reliable_events


def write_stage_0_2_ngsim_package(
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
    reliable_event_frames = []
    rejected_event_frames = []
    source_audit = []
    for source in sources:
        asset_id = str(source["asset_id"])
        if asset_id not in _ALLOWED_CALIBRATION_ASSETS:
            raise ValueError(f"asset is not authorized for Stage 0.2 calibration: {asset_id}")
        path = Path(source["path"])
        raw = _read_source(path, source)
        states = standardize_ngsim_states(
            raw,
            site=str(source["site"]),
            window_id=str(source["window_id"]),
            source_period=str(source.get("source_period", "unknown")),
            source_member=str(source.get("trajectory_member", source.get("csv_member", "unknown"))),
        )
        state_name = f"{asset_id}__{_slug(str(source['window_id']))}.parquet"
        states.to_parquet(states_dir / state_name, index=False)
        events, reliable_events, rejected_events = extract_rear_end_events(
            states, provisional_ttc_threshold_s=provisional_ttc_threshold_s,
            return_diagnostics=True,
        )
        event_frames.append(events)
        reliable_event_frames.append(reliable_events)
        rejected_event_frames.append(rejected_events)
        source_audit.append(
            {
                "asset_id": asset_id,
                "window_id": str(source["window_id"]),
                "input_sha256": sha256_file(path),
                "state_rows": int(len(states)),
                "valid_ttc_rows": int(states["ttc_valid"].sum()),
                "event_rows": int(len(events)),
                "reliable_event_rows": int(len(reliable_events)),
                "rejected_event_rows": int(len(rejected_events)),
                "rejection_reason_counts": {
                    str(key): int(value)
                    for key, value in rejected_events["rejection_reason"].value_counts(dropna=False).items()
                },
                "source_member": str(source.get("trajectory_member", source.get("csv_member", ""))),
                "source_format": str(source.get("format", source.get("source_format", "csv"))),
                "expected_rows": source.get("expected_rows"),
                "measurement_status_counts": {
                    str(key): int(value)
                    for key, value in states["measurement_status"].value_counts(dropna=False).items()
                },
                "identity_status_counts": {
                    str(key): int(value)
                    for key, value in states["identity_status"].value_counts(dropna=False).items()
                },
                "identity_uncertain_rows": int(states["identity_uncertain"].sum()),
                "observation_gap_rows": int(states["observation_gap"].sum()),
                "identity_break_rows": int(states["identity_break"].sum()),
                "trajectory_segment_count": int(states["trajectory_id"].nunique()),
                "raw_row_preservation": int(len(raw) == len(states)),
            }
        )
        del raw, states
    all_events = (
        pd.concat(event_frames, ignore_index=True)
        if event_frames
        else pd.DataFrame(columns=RISK_EVENT_COLUMNS)
    )
    all_events.to_parquet(output_dir / "risk_events.parquet", index=False)
    (pd.concat(reliable_event_frames, ignore_index=True) if reliable_event_frames
     else pd.DataFrame(columns=RISK_EVENT_COLUMNS)).to_parquet(
        output_dir / "reliable_risk_events.parquet", index=False
    )
    (pd.concat(rejected_event_frames, ignore_index=True) if rejected_event_frames
     else pd.DataFrame(columns=["event_id", "rejection_reason", "raw_frame_count"])).to_parquet(
        output_dir / "rejected_risk_events.parquet", index=False
    )
    config = {
        "schema_version": "stage_0_2.config.v1",
        "experiment_id": "stage_0_2",
        "provisional_ttc_threshold_s": provisional_ttc_threshold_s,
        "scientific_claim_eligible": False,
        "locked_holdout_opened": False,
        "trajectory_identity_policy": {
            "segment_boundary": "observed_global_time_minus_100_times_frame_id_clock_anchor",
            "observation_gap_rule": "sorted_diagnostic_sequence_delta_gt_100ms_is_flag_only",
            "unknown_source_period": "preserved_as_unknown",
            "uncertainty": "duplicate_time_or_frame_or_inconsistent_total_propagates_to_whole_diagnostic_sequence",
        },
        "event_reliability_policy": "complete_state_sequence; unique follower_and_leader; consecutive_integer_ms_and_frames; first_frame_after_gap_allowed",
        "max_gap_s": 0.11,
        "minimum_duration_s": 0.1,
    }
    audit = {
        "schema_version": "stage_0_2.audit.v1",
        "experiment_id": "stage_0_2",
        "scientific_claim_eligible": False,
        "locked_holdout_opened": False,
        "gate_status": "active_audit_closure",
        "trajectory_identity_policy": config["trajectory_identity_policy"],
        "sources": source_audit,
    }
    provenance = {
        "schema_version": "stage_0_2.provenance.v1",
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
        source_format = str(source.get("format", source.get("source_format", "csv")))
        member_key = "trajectory_member" if source_format.startswith("ngsim_us101_txt") else "csv_member"
        member = str(source.get(member_key, source.get("txt_member", "")))
        if not member:
            raise ValueError(f"missing source member for format {source_format}")
        def read_member(handle):
            if source_format.startswith("ngsim_us101_txt") or source_format == "txt":
                return _read_ngsim_txt(handle, source, member, source_format)
            frame = pd.read_csv(handle)
            frame["source_member"] = member
            frame["source_format"] = source_format
            return frame
        if inner_member:
            with zipfile.ZipFile(io.BytesIO(outer.read(str(inner_member)))) as inner:
                with inner.open(member) as handle:
                    return read_member(handle)
        with outer.open(member) as handle:
            return read_member(handle)


def _read_ngsim_txt(handle, source: Mapping[str, object], member: str, source_format: str) -> pd.DataFrame:
    rows: list[list[str]] = []
    for line_number, raw_line in enumerate(handle, start=1):
        line = raw_line.decode("utf-8", errors="strict").strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != len(_NGSIM_TXT_COLUMNS):
            raise ValueError(
                f"invalid NGSIM TXT structure at line {line_number}: expected "
                f"{len(_NGSIM_TXT_COLUMNS)} fields, read {len(fields)}"
            )
        rows.append(fields)
    expected_rows = source.get("expected_rows")
    if expected_rows is not None and len(rows) != int(expected_rows):
        raise ValueError(f"expected {int(expected_rows)} rows, read {len(rows)}")
    frame = pd.DataFrame(rows, columns=_NGSIM_TXT_COLUMNS)
    for column in _NGSIM_TXT_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["source_member"] = member
    frame["source_format"] = source_format
    return frame


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
            {"schema_version": "stage_0_2.manifest.v1", "files": entries},
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
