from __future__ import annotations

from pathlib import Path

import pandas as pd

from riskprop.legacy.pneuma_mapmatch import (
    infer_candidate_leaders,
    load_osm_segments,
    map_match_pneuma_points,
    write_pneuma_mapmatch_package,
    write_pneuma_csv_mapmatch_package,
)


def _write_osm(path: Path) -> None:
    path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">
  <node id="1" lat="37.000000" lon="23.000000" />
  <node id="2" lat="37.000000" lon="23.001000" />
  <way id="10">
    <nd ref="1"/><nd ref="2"/>
    <tag k="highway" v="primary"/><tag k="oneway" v="yes"/>
  </way>
</osm>
""",
        encoding="utf-8",
    )


def test_osm_match_and_candidate_leader_are_direction_aware(tmp_path: Path) -> None:
    osm = tmp_path / "road.osm"
    _write_osm(osm)
    segments = load_osm_segments(osm)
    points = pd.DataFrame(
        [
            {"id": "rear", "time_s": 0.0, "latitude": 37.0, "longitude": 23.0002, "speed_mps": 10.0},
            {"id": "rear", "time_s": 0.1, "latitude": 37.0, "longitude": 23.0003, "speed_mps": 10.0},
            {"id": "front", "time_s": 0.0, "latitude": 37.0, "longitude": 23.0006, "speed_mps": 8.0},
            {"id": "front", "time_s": 0.1, "latitude": 37.0, "longitude": 23.0007, "speed_mps": 8.0},
        ]
    )
    matched = map_match_pneuma_points(points, segments, max_distance_m=8.0)
    assert matched["map_match_status"].eq("candidate").all()
    assert matched["road_id"].eq("10").all()
    assert matched["travel_direction"].eq(1).all()

    leaders = infer_candidate_leaders(matched)
    rear = leaders[(leaders["vehicle_id"] == "rear") & (leaders["time_s"] == 0.0)].iloc[0]
    assert rear["leader_id"] == "front"
    assert rear["front_to_front_m"] > 0
    assert rear["leader_status"] == "candidate_unverified"


def test_reverse_motion_is_rejected_on_one_way_road(tmp_path: Path) -> None:
    osm = tmp_path / "road.osm"
    _write_osm(osm)
    segments = load_osm_segments(osm)
    points = pd.DataFrame(
        [
            {"id": "v", "time_s": 0.0, "latitude": 37.0, "longitude": 23.0008, "speed_mps": 5.0},
            {"id": "v", "time_s": 0.1, "latitude": 37.0, "longitude": 23.0007, "speed_mps": 5.0},
        ]
    )
    matched = map_match_pneuma_points(points, segments, max_distance_m=8.0)
    assert matched["map_match_status"].eq("direction_mismatch").all()
    assert matched["road_id"].isna().all()


def test_mapmatch_package_is_sealed_and_remains_candidate_only(tmp_path: Path) -> None:
    osm = tmp_path / "road.osm"
    _write_osm(osm)
    points = pd.DataFrame(
        [
            {"id": "v", "time_s": 0.0, "latitude": 37.0, "longitude": 23.0002, "speed_mps": 5.0},
            {"id": "v", "time_s": 0.1, "latitude": 37.0, "longitude": 23.0003, "speed_mps": 5.0},
        ]
    )
    output = write_pneuma_mapmatch_package(
        points=points,
        source_path=tmp_path / "points.csv",
        osm_path=osm,
        output_dir=tmp_path / "out",
        max_distance_m=8.0,
    )
    assert (output / "map_matched_states.parquet").is_file()
    assert (output / "candidate_leaders.parquet").is_file()
    assert (output / "audit.json").is_file()
    assert (output / "SHA256SUMS").is_file()


def test_csv_mapmatch_package_streams_wide_tracks(tmp_path: Path) -> None:
    osm = tmp_path / "road.osm"
    _write_osm(osm)
    source = tmp_path / "pneuma.csv"
    source.write_text(
        "track_id;type;distance;avg_speed;lat;lon;speed;lon_acc;lat_acc;time\n"
        "rear;Car;10;10;37;23.0002;36;0;0;0;37;23.0003;36;0;0;0.1;\n"
        "front;Car;10;8;37;23.0006;28.8;0;0;0;37;23.0007;28.8;0;0;0.1;\n",
        encoding="utf-8",
    )
    output = write_pneuma_csv_mapmatch_package(
        source_path=source,
        osm_path=osm,
        output_dir=tmp_path / "streamed",
        max_distance_m=8.0,
        tracks_per_batch=1,
    )
    states = pd.read_parquet(output / "map_matched_states.parquet")
    leaders = pd.read_parquet(output / "candidate_leaders.parquet")
    assert len(states) == 4
    assert leaders["leader_id"].notna().any()
