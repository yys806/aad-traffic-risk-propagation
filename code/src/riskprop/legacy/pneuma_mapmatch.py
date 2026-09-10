"""Conservative pNEUMA-to-OSM candidate map matching.

The output deliberately labels road and leader relations as candidates.  It does
not promote them to validated TTC inputs until the preregistered manual audit.
"""

from __future__ import annotations

import csv
import math
import json
import platform
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from riskprop.calibration import sha256_file


EARTH_RADIUS_M = 6_371_008.8
_NON_DRIVING_HIGHWAYS = {
    "bridleway",
    "construction",
    "cycleway",
    "footway",
    "path",
    "pedestrian",
    "steps",
}


def load_osm_segments(osm_path: str | Path) -> pd.DataFrame:
    """Read drivable OSM ways into directed geometric segments."""

    root = ET.parse(Path(osm_path)).getroot()
    nodes = {
        element.attrib["id"]: (float(element.attrib["lat"]), float(element.attrib["lon"]))
        for element in root.findall("node")
    }
    if not nodes:
        raise ValueError("OSM snapshot has no nodes")
    lat0 = sum(value[0] for value in nodes.values()) / len(nodes)
    lon0 = sum(value[1] for value in nodes.values()) / len(nodes)
    rows = []
    for way in root.findall("way"):
        tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        highway = tags.get("highway")
        if not highway or highway in _NON_DRIVING_HIGHWAYS:
            continue
        refs = [node.attrib["ref"] for node in way.findall("nd")]
        refs = [ref for ref in refs if ref in nodes]
        oneway_raw = tags.get("oneway", "no").lower()
        oneway = -1 if oneway_raw == "-1" else (1 if oneway_raw in {"yes", "true", "1"} else 0)
        cumulative = 0.0
        for index, (first_ref, second_ref) in enumerate(zip(refs, refs[1:])):
            lat1, lon1 = nodes[first_ref]
            lat2, lon2 = nodes[second_ref]
            x1, y1 = _project(lon1, lat1, lon0, lat0)
            x2, y2 = _project(lon2, lat2, lon0, lat0)
            length = math.hypot(x2 - x1, y2 - y1)
            if length <= 1e-6:
                continue
            rows.append(
                {
                    "road_id": way.attrib["id"],
                    "segment_index": index,
                    "highway": highway,
                    "oneway": oneway,
                    "x1_m": x1,
                    "y1_m": y1,
                    "x2_m": x2,
                    "y2_m": y2,
                    "segment_length_m": length,
                    "way_start_m": cumulative,
                    "origin_lat": lat0,
                    "origin_lon": lon0,
                }
            )
            cumulative += length
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("OSM snapshot has no drivable highway segments")
    return result


def map_match_pneuma_points(
    points: pd.DataFrame,
    segments: pd.DataFrame,
    *,
    max_distance_m: float = 6.0,
    max_heading_difference_deg: float = 45.0,
) -> pd.DataFrame:
    """Assign the nearest direction-compatible road segment to each point."""

    required = {"id", "time_s", "latitude", "longitude", "speed_mps"}
    missing = required - set(points.columns)
    if missing:
        raise ValueError(f"pNEUMA points are missing: {', '.join(sorted(missing))}")
    if max_distance_m <= 0 or not 0 < max_heading_difference_deg <= 90:
        raise ValueError("map-match distance/heading limits are invalid")
    lat0 = float(segments["origin_lat"].iloc[0])
    lon0 = float(segments["origin_lon"].iloc[0])
    result = points.copy().reset_index(drop=True)
    result["map_x_m"] = (
        np.radians(pd.to_numeric(result["longitude"]) - lon0)
        * EARTH_RADIUS_M
        * math.cos(math.radians(lat0))
    )
    result["map_y_m"] = (
        np.radians(pd.to_numeric(result["latitude"]) - lat0) * EARTH_RADIUS_M
    )
    ordered = result.sort_values(["id", "time_s"])
    previous_x = ordered.groupby("id")["map_x_m"].shift()
    previous_y = ordered.groupby("id")["map_y_m"].shift()
    next_x = ordered.groupby("id")["map_x_m"].shift(-1)
    next_y = ordered.groupby("id")["map_y_m"].shift(-1)
    motion_x = (next_x - previous_x).fillna(next_x - ordered["map_x_m"]).fillna(
        ordered["map_x_m"] - previous_x
    )
    motion_y = (next_y - previous_y).fillna(next_y - ordered["map_y_m"]).fillna(
        ordered["map_y_m"] - previous_y
    )
    ordered["_motion_x"] = motion_x
    ordered["_motion_y"] = motion_y
    result = ordered.sort_index()

    cell_size = max(20.0, 2.0 * max_distance_m)
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, segment in segments.iterrows():
        min_x = min(segment["x1_m"], segment["x2_m"]) - max_distance_m
        max_x = max(segment["x1_m"], segment["x2_m"]) + max_distance_m
        min_y = min(segment["y1_m"], segment["y2_m"]) - max_distance_m
        max_y = max(segment["y1_m"], segment["y2_m"]) + max_distance_m
        for gx in range(math.floor(min_x / cell_size), math.floor(max_x / cell_size) + 1):
            for gy in range(math.floor(min_y / cell_size), math.floor(max_y / cell_size) + 1):
                grid[(gx, gy)].append(index)

    segments = segments.reset_index(drop=True)
    count = len(result)
    best_distance = np.full(count, np.inf)
    best_segment = np.full(count, -1, dtype=int)
    best_projection = np.full(count, np.nan)
    best_direction = np.zeros(count, dtype=int)
    saw_nearby = np.zeros(count, dtype=bool)
    cos_limit = math.cos(math.radians(max_heading_difference_deg))
    px_all = result["map_x_m"].to_numpy(float)
    py_all = result["map_y_m"].to_numpy(float)
    mx_all = result["_motion_x"].to_numpy(float)
    my_all = result["_motion_y"].to_numpy(float)
    motion_norm_all = np.hypot(mx_all, my_all)
    point_cells = pd.DataFrame(
        {
            "gx": np.floor(px_all / cell_size).astype(int),
            "gy": np.floor(py_all / cell_size).astype(int),
            "row": np.arange(count),
        }
    )
    for (gx, gy), cell_rows in point_cells.groupby(["gx", "gy"], sort=False):
        row_indices = cell_rows["row"].to_numpy(int)
        px = px_all[row_indices]
        py = py_all[row_indices]
        mx = mx_all[row_indices]
        my = my_all[row_indices]
        motion_norm = motion_norm_all[row_indices]
        for segment_index in grid.get((int(gx), int(gy)), []):
            segment = segments.iloc[segment_index]
            x1, y1 = float(segment["x1_m"]), float(segment["y1_m"])
            sx = float(segment["x2_m"] - x1)
            sy = float(segment["y2_m"] - y1)
            denominator = sx * sx + sy * sy
            projection = np.clip(((px - x1) * sx + (py - y1) * sy) / denominator, 0.0, 1.0)
            distance = np.hypot(px - (x1 + projection * sx), py - (y1 + projection * sy))
            nearby = distance <= max_distance_m
            saw_nearby[row_indices] |= nearby
            with np.errstate(divide="ignore", invalid="ignore"):
                alignment = (mx * sx + my * sy) / (motion_norm * math.sqrt(denominator))
            direction = np.where(alignment >= 0, 1, -1)
            compatible = nearby & (motion_norm > 1e-6) & (np.abs(alignment) >= cos_limit)
            oneway = int(segment["oneway"])
            if oneway:
                compatible &= direction == oneway
            global_rows = row_indices[compatible]
            local_distance = distance[compatible]
            improves = local_distance < best_distance[global_rows]
            global_rows = global_rows[improves]
            local_positions = np.flatnonzero(compatible)[improves]
            best_distance[global_rows] = distance[local_positions]
            best_segment[global_rows] = segment_index
            best_projection[global_rows] = projection[local_positions]
            best_direction[global_rows] = direction[local_positions]

    matched = best_segment >= 0
    status = np.full(count, "outside_map_tolerance", dtype=object)
    status[saw_nearby & (motion_norm_all <= 1e-6)] = "heading_unobservable"
    status[saw_nearby & (motion_norm_all > 1e-6)] = "direction_mismatch"
    status[matched] = "candidate"
    road_id = np.full(count, None, dtype=object)
    segment_number = np.full(count, np.nan)
    travel_direction = np.full(count, np.nan)
    road_position = np.full(count, np.nan)
    distance_output = np.full(count, np.nan)
    if matched.any():
        selected = segments.iloc[best_segment[matched]]
        road_id[matched] = selected["road_id"].astype(str).to_numpy()
        segment_number[matched] = selected["segment_index"].to_numpy(float)
        travel_direction[matched] = best_direction[matched]
        road_position[matched] = (
            selected["way_start_m"].to_numpy(float)
            + best_projection[matched] * selected["segment_length_m"].to_numpy(float)
        )
        distance_output[matched] = best_distance[matched]
    result["road_id"] = pd.Series(road_id, dtype="string")
    result["segment_index"] = pd.Series(segment_number, dtype="Int64")
    result["travel_direction"] = pd.Series(travel_direction, dtype="Int64")
    result["road_position_m"] = road_position
    result["map_match_distance_m"] = distance_output
    result["map_match_status"] = status
    output = result.drop(columns=["_motion_x", "_motion_y"])
    return output


def infer_candidate_leaders(matched: pd.DataFrame) -> pd.DataFrame:
    """Infer same-road/direction front vehicles, explicitly as unverified candidates."""

    result = matched.rename(columns={"id": "vehicle_id"}).copy()
    result["leader_id"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["front_to_front_m"] = float("nan")
    result["leader_status"] = "unavailable"
    usable = result["map_match_status"].eq("candidate") & result["travel_direction"].notna()
    group_columns = ["time_s", "road_id", "travel_direction"]
    order = result.loc[usable].copy()
    order["_oriented_position"] = (
        pd.to_numeric(order["road_position_m"]) * pd.to_numeric(order["travel_direction"])
    )
    order = order.sort_values([*group_columns, "_oriented_position"])
    grouped = order.groupby(group_columns, dropna=False, sort=False)
    leader_ids = grouped["vehicle_id"].shift(-1)
    leader_positions = grouped["_oriented_position"].shift(-1)
    distances = leader_positions - order["_oriented_position"]
    has_leader = leader_ids.notna() & (distances >= 0)
    result.loc[order.index[has_leader], "leader_id"] = leader_ids.loc[has_leader].astype("string")
    result.loc[order.index[has_leader], "front_to_front_m"] = distances.loc[has_leader]
    result.loc[order.index[has_leader], "leader_status"] = "candidate_unverified"
    result.loc[order.index[~has_leader], "leader_status"] = "no_candidate_ahead"
    return result


def write_pneuma_csv_mapmatch_package(
    *,
    source_path: str | Path,
    osm_path: str | Path,
    output_dir: str | Path,
    max_distance_m: float = 6.0,
    tracks_per_batch: int = 25,
) -> Path:
    """Stream a pNEUMA wide CSV through map matching without a Python-record explosion."""

    import pyarrow as pa
    import pyarrow.parquet as pq

    if tracks_per_batch < 1:
        raise ValueError("tracks_per_batch must be positive")
    source_path = Path(source_path)
    osm_path = Path(osm_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    segments = load_osm_segments(osm_path)
    state_path = output_dir / "map_matched_states.parquet"
    writer = None
    point_count = 0
    try:
        for batch in _iter_pneuma_wide_batches(source_path, tracks_per_batch):
            matched = map_match_pneuma_points(
                batch, segments, max_distance_m=max_distance_m
            )
            table = pa.Table.from_pandas(matched, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(state_path, table.schema, compression="zstd")
            writer.write_table(table)
            point_count += len(matched)
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        raise ValueError("pNEUMA source contains no trajectories")
    matched = pd.read_parquet(state_path)
    leaders = infer_candidate_leaders(matched)
    leader_columns = [
        "vehicle_id",
        "time_s",
        "road_id",
        "travel_direction",
        "road_position_m",
        "leader_id",
        "front_to_front_m",
        "leader_status",
    ]
    leaders[leader_columns].to_parquet(
        output_dir / "candidate_leaders.parquet", index=False
    )
    _write_mapmatch_metadata(
        output_dir=output_dir,
        matched=matched,
        leaders=leaders,
        source_path=source_path,
        osm_path=osm_path,
        max_distance_m=max_distance_m,
    )
    _seal_package(output_dir)
    return output_dir


def write_pneuma_mapmatch_package(
    *,
    points: pd.DataFrame,
    source_path: str | Path,
    osm_path: str | Path,
    output_dir: str | Path,
    max_distance_m: float = 6.0,
) -> Path:
    """Write a sealed candidate-only map-match package for manual QA."""

    source_path = Path(source_path)
    osm_path = Path(osm_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    segments = load_osm_segments(osm_path)
    matched = map_match_pneuma_points(
        points, segments, max_distance_m=max_distance_m
    )
    leaders = infer_candidate_leaders(matched)
    matched.to_parquet(output_dir / "map_matched_states.parquet", index=False)
    leaders[
        [
            "vehicle_id",
            "time_s",
            "road_id",
            "travel_direction",
            "road_position_m",
            "leader_id",
            "front_to_front_m",
            "leader_status",
        ]
    ].to_parquet(output_dir / "candidate_leaders.parquet", index=False)
    _write_mapmatch_metadata(
        output_dir=output_dir,
        matched=matched,
        leaders=leaders,
        source_path=source_path,
        osm_path=osm_path,
        max_distance_m=max_distance_m,
    )
    _seal_package(output_dir)
    return output_dir


def _write_mapmatch_metadata(
    *,
    output_dir: Path,
    matched: pd.DataFrame,
    leaders: pd.DataFrame,
    source_path: Path,
    osm_path: Path,
    max_distance_m: float,
) -> None:
    status_counts = matched["map_match_status"].value_counts(dropna=False).to_dict()
    candidate_distances = pd.to_numeric(
        matched.loc[matched["map_match_status"].eq("candidate"), "map_match_distance_m"],
        errors="coerce",
    ).dropna()
    audit = {
        "schema_version": "e15a.pneuma-mapmatch-audit.v1",
        "experiment_id": "E15-A",
        "scientific_claim_eligible": False,
        "leader_relations_validated": False,
        "ttc_generated": False,
        "gate_status": "pending_manual_map_and_leader_audit",
        "point_count": int(len(matched)),
        "map_match_status_counts": {str(key): int(value) for key, value in status_counts.items()},
        "candidate_fraction": float(matched["map_match_status"].eq("candidate").mean()),
        "candidate_distance_p95_m": (
            float(candidate_distances.quantile(0.95)) if not candidate_distances.empty else None
        ),
        "candidate_leader_count": int(leaders["leader_id"].notna().sum()),
        "note": "Road and leader assignments are candidates only; no pNEUMA TTC is allowed before manual QA.",
    }
    config = {
        "schema_version": "e15a.pneuma-mapmatch-config.v1",
        "max_distance_m": max_distance_m,
        "source_sha256": sha256_file(source_path) if source_path.is_file() else "in_memory_fixture",
        "osm_sha256": sha256_file(osm_path),
        "osm_license": "ODbL; © OpenStreetMap contributors",
        "locked_holdout_opened": False,
    }
    provenance = {
        "schema_version": "e15a.pneuma-mapmatch-provenance.v1",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "python": sys.version,
        "platform": platform.platform(),
        "working_directory": str(Path.cwd().resolve()),
    }
    for name, payload in (
        ("audit.json", audit),
        ("config_frozen.json", config),
        ("provenance.json", provenance),
    ):
        (output_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _iter_pneuma_wide_batches(source_path: Path, tracks_per_batch: int):
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 10
    records: list[dict[str, object]] = []
    tracks_in_batch = 0
    with source_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, delimiter=";")
        next(reader, None)
        for row_number, raw in enumerate(reader, start=2):
            values = [value.strip() for value in raw]
            while values and values[-1] == "":
                values.pop()
            if not values:
                continue
            if len(values) < 4 or (len(values) - 4) % 6:
                raise ValueError(
                    f"pNEUMA row {row_number} must contain four metadata values followed by state blocks of six values"
                )
            track_id, vehicle_type, traveled_distance, average_speed = values[:4]
            for offset in range(4, len(values), 6):
                latitude, longitude, speed, longitudinal_accel, lateral_accel, time = values[offset : offset + 6]
                records.append(
                    {
                        "run_id": "pneuma_d1_0800_0830",
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
            tracks_in_batch += 1
            if tracks_in_batch >= tracks_per_batch:
                yield pd.DataFrame.from_records(records)
                records = []
                tracks_in_batch = 0
    if records:
        yield pd.DataFrame.from_records(records)


def _seal_package(output_dir: Path) -> None:
    files = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
    manifest = {
        "schema_version": "e15a.pneuma-mapmatch-manifest.v1",
        "files": [
            {
                "path": path.relative_to(output_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksum_files = [*files, output_dir / "manifest.json"]
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(
            f"{sha256_file(path)}  {path.relative_to(output_dir).as_posix()}"
            for path in checksum_files
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _project(lon: float, lat: float, lon0: float, lat0: float) -> tuple[float, float]:
    x = math.radians(lon - lon0) * EARTH_RADIUS_M * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * EARTH_RADIUS_M
    return x, y


def _point_segment_projection(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> tuple[float, float]:
    dx, dy = x2 - x1, y2 - y1
    denominator = dx * dx + dy * dy
    projection = 0.0 if denominator <= 0 else ((px - x1) * dx + (py - y1) * dy) / denominator
    projection = min(max(projection, 0.0), 1.0)
    nearest_x = x1 + projection * dx
    nearest_y = y1 + projection * dy
    return projection, math.hypot(px - nearest_x, py - nearest_y)
