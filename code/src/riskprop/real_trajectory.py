from __future__ import annotations

import csv
import io
import math
import sys
import zipfile
from pathlib import Path

import pandas as pd


FEET_TO_METRES = 0.3048


def read_ngsim_nested_csv(
    outer_zip: str | Path,
    inner_zip_member: str,
    csv_member: str,
    *,
    nrows: int | None = None,
    **read_csv_kwargs: object,
) -> pd.DataFrame:
    """Read an NGSIM trajectory CSV held inside a ZIP within a scenario ZIP."""
    with zipfile.ZipFile(Path(outer_zip)) as outer:
        inner_bytes = outer.read(inner_zip_member)
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
        with inner.open(csv_member) as source:
            return pd.read_csv(source, nrows=nrows, **read_csv_kwargs)


def add_ngsim_leader_ttc(
    trajectories: pd.DataFrame,
    *,
    run_id: str = "ngsim",
    closing_epsilon_mps: float = 1e-3,
) -> pd.DataFrame:
    """Attach a reported-leader match, net gap and leader-aware TTC to NGSIM rows.

    NGSIM uses feet and feet/second. ``Space_Hdwy`` is a front-to-front
    distance, so the bumper-to-bumper gap is obtained by subtracting the
    matched leader's length. TTC is finite only for a matched nonzero leader,
    a positive net gap and a closing follower.
    """
    columns = _resolve_ngsim_columns(trajectories)
    original_index = trajectories.index.copy()
    result = trajectories.reset_index(drop=True).copy()
    follower_id = _identifier_series(result[columns["vehicle_id"]])
    leader_id = _identifier_series(result[columns["preceding"]])
    time = pd.to_numeric(result[columns["global_time"]], errors="coerce")
    speed_fps = pd.to_numeric(result[columns["speed"]], errors="coerce")
    space_headway_ft = pd.to_numeric(result[columns["space_headway"]], errors="coerce")

    lookup = pd.DataFrame(
        {
            "_time": time,
            "_lookup_id": follower_id,
            "_leader_speed_fps": speed_fps,
            "_leader_length_ft": pd.to_numeric(result[columns["length"]], errors="coerce"),
        }
    ).drop_duplicates(["_time", "_lookup_id"], keep=False)
    matches = pd.DataFrame({"_time": time, "_lookup_id": leader_id}).merge(
        lookup,
        on=["_time", "_lookup_id"],
        how="left",
        sort=False,
    )

    has_reported_leader = leader_id.notna() & (leader_id != "0")
    leader_matched = has_reported_leader & matches["_leader_speed_fps"].notna()
    reported_headway_m = space_headway_ft * FEET_TO_METRES
    leader_length_m = matches["_leader_length_ft"] * FEET_TO_METRES
    net_gap_m = reported_headway_m - leader_length_m
    relative_speed_mps = (matches["_leader_speed_fps"] - speed_fps) * FEET_TO_METRES
    closing_speed_mps = -relative_speed_mps
    valid = (
        leader_matched
        & net_gap_m.notna()
        & (net_gap_m > 0)
        & closing_speed_mps.notna()
        & (closing_speed_mps > closing_epsilon_mps)
    )
    ttc = pd.Series(math.inf, index=result.index, dtype=float)
    ttc.loc[valid] = net_gap_m.loc[valid] / closing_speed_mps.loc[valid]

    result["run_id"] = run_id
    result["time_s"] = (time - time.min()) / 1_000.0
    result["id"] = follower_id
    result["leader_id"] = leader_id.where(has_reported_leader)
    result["leader_matched"] = leader_matched.to_numpy()
    result["reported_space_headway_m"] = reported_headway_m
    result["leader_length_m"] = leader_length_m
    result["headway_m"] = net_gap_m
    result["speed_mps"] = speed_fps * FEET_TO_METRES
    result["acceleration_mps2"] = _numeric_optional(result, ("v_Acc", "v_acc")) * FEET_TO_METRES
    result["x_m"] = _numeric_optional(result, ("Local_X", "local_x")) * FEET_TO_METRES
    result["y_m"] = _numeric_optional(result, ("Local_Y", "local_y")) * FEET_TO_METRES
    result["lane_id"] = _identifier_optional(result, ("Lane_ID", "lane_id"))
    result["leader_rel_speed_mps"] = relative_speed_mps
    result["closing_speed_mps"] = closing_speed_mps
    result["ttc_valid"] = valid.to_numpy()
    result["ttc_s"] = ttc
    result.index = original_index
    return result


def read_pneuma_wide(
    source_csv: str | Path,
    *,
    run_id: str = "pneuma",
    max_tracks: int | None = None,
) -> pd.DataFrame:
    """Expand pNEUMA's one-track-per-row format into one row per state."""
    _raise_csv_field_limit()
    records: list[dict[str, object]] = []
    with Path(source_csv).open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, delimiter=";")
        next(reader, None)
        for track_index, raw in enumerate(reader):
            if max_tracks is not None and track_index >= max_tracks:
                break
            values = [value.strip() for value in raw]
            while values and values[-1] == "":
                values.pop()
            if not values:
                continue
            if len(values) < 4 or (len(values) - 4) % 6:
                raise ValueError(
                    f"pNEUMA row {track_index + 2} must contain four metadata values followed by state blocks of six values"
                )
            track_id, vehicle_type, traveled_distance, average_speed = values[:4]
            for state_offset in range(4, len(values), 6):
                latitude, longitude, speed, longitudinal_accel, lateral_accel, time = values[
                    state_offset : state_offset + 6
                ]
                records.append(
                    {
                        "run_id": run_id,
                        "id": track_id,
                        "vehicle_type": vehicle_type,
                        "traveled_distance_m": float(traveled_distance),
                        "average_speed_kmh": float(average_speed),
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "speed_kmh": float(speed),
                        "speed_mps": float(speed) / 3.6,
                        "longitudinal_accel_mps2": float(longitudinal_accel),
                        "lateral_accel_mps2": float(lateral_accel),
                        "time_s": float(time),
                    }
                )
    return pd.DataFrame.from_records(
        records,
        columns=[
            "run_id",
            "id",
            "vehicle_type",
            "traveled_distance_m",
            "average_speed_kmh",
            "latitude",
            "longitude",
            "speed_kmh",
            "speed_mps",
            "longitudinal_accel_mps2",
            "lateral_accel_mps2",
            "time_s",
        ],
    )


def _resolve_ngsim_columns(frame: pd.DataFrame) -> dict[str, str]:
    candidates = {
        "vehicle_id": ("Vehicle_ID", "vehicle_id"),
        "global_time": ("Global_Time", "global_time"),
        "length": ("v_Length", "v_length"),
        "speed": ("v_Vel", "v_vel"),
        "preceding": ("Preceeding", "Preceding", "preceding"),
        "space_headway": ("Space_Hdwy", "space_headway"),
    }
    resolved: dict[str, str] = {}
    for meaning, options in candidates.items():
        match = next((column for column in options if column in frame.columns), None)
        if match is None:
            raise ValueError(f"NGSIM trajectories are missing the required {meaning} column")
        resolved[meaning] = match
    return resolved


def _identifier_series(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    identifiers = numeric.astype("Int64").astype("string")
    return identifiers.where(numeric.notna())


def _numeric_optional(frame: pd.DataFrame, candidates: tuple[str, ...]) -> pd.Series:
    column = next((name for name in candidates if name in frame.columns), None)
    if column is None:
        return pd.Series(float("nan"), index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _identifier_optional(frame: pd.DataFrame, candidates: tuple[str, ...]) -> pd.Series:
    column = next((name for name in candidates if name in frame.columns), None)
    if column is None:
        return pd.Series(pd.NA, index=frame.index, dtype="string")
    return _identifier_series(frame[column])


def _raise_csv_field_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10
