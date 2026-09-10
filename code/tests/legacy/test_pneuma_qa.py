from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from riskprop.legacy.pneuma_qa import write_pneuma_manual_qa_pack


def _write_osm(path: Path) -> None:
    path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">
  <node id="1" lat="37.000000" lon="23.000000" />
  <node id="2" lat="37.000000" lon="23.001000" />
  <way id="10"><nd ref="1"/><nd ref="2"/><tag k="highway" v="primary"/><tag k="oneway" v="yes"/></way>
</osm>
""",
        encoding="utf-8",
    )


def test_pneuma_manual_qa_pack_is_balanced_reviewable_and_not_a_ttc_result(
    tmp_path: Path,
) -> None:
    source = tmp_path / "mapmatch"
    source.mkdir()
    states = pd.DataFrame(
        [
            {
                "id": f"{status}-v{vehicle}",
                "time_s": float(step),
                "latitude": 37.0 + vehicle * 1e-6,
                "longitude": 23.0 + (vehicle * 10 + step) * 1e-6,
                "speed_mps": 5.0,
                "road_id": "10" if status == "candidate" else pd.NA,
                "travel_direction": 1 if status == "candidate" else pd.NA,
                "road_position_m": (
                    float(vehicle * 10 + step) if status == "candidate" else float("nan")
                ),
                "map_match_distance_m": 1.0 if status == "candidate" else float("nan"),
                "map_match_status": status,
                "map_x_m": float(vehicle * 10 + step),
                "map_y_m": float(status != "candidate") * 10.0,
            }
            for status in (
                "candidate",
                "direction_mismatch",
                "heading_unobservable",
                "outside_map_tolerance",
            )
            for vehicle in range(5)
            for step in range(4)
        ]
    )
    leaders = states.loc[states["map_match_status"].eq("candidate"), ["id", "time_s"]].rename(
        columns={"id": "vehicle_id"}
    )
    leaders["road_id"] = "10"
    leaders["travel_direction"] = 1
    leaders["road_position_m"] = range(len(leaders))
    leaders["leader_id"] = leaders["vehicle_id"].map(
        lambda value: f"candidate-v{(int(str(value).rsplit('v', 1)[1]) + 1) % 5}"
    )
    leaders["front_to_front_m"] = 8.0
    leaders["leader_status"] = "candidate_unverified"
    states.to_parquet(source / "map_matched_states.parquet", index=False)
    leaders.to_parquet(source / "candidate_leaders.parquet", index=False)
    osm = tmp_path / "road.osm"
    _write_osm(osm)

    output = write_pneuma_manual_qa_pack(
        mapmatch_dir=source,
        output_dir=tmp_path / "qa",
        osm_path=osm,
        total=40,
        seed=20260907,
        pilot_per_stratum=2,
    )

    review = pd.read_csv(output / "map_leader_review_round1.csv", dtype=str)
    key = pd.read_csv(output / "sealed_sampling_key.csv", dtype=str)
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert len(review) == 40
    assert key["sampling_stratum"].value_counts().to_dict() == {
        "candidate_with_leader": 10,
        "direction_mismatch": 10,
        "heading_unobservable": 10,
        "outside_map_tolerance": 10,
    }
    assert "sampling_stratum" not in review.columns
    assert "system_map_match_status" not in review.columns
    assert "system_map_match_status" in key.columns
    assert review["pilot_batch"].astype(str).str.lower().eq("true").sum() == 8
    assert {"reviewed_road_match", "reviewed_leader_match", "reviewer_uncertain"} <= set(
        review.columns
    )
    assert audit["ttc_generated"] is False
    assert audit["gate_status"] == "pending_human_round1"
    assert audit["pilot_count"] == 8
    assert (output / "review_map.html").is_file()
    html = (output / "review_map.html").read_text(encoding="utf-8")
    assert "离线审计图" in html
    assert "前后轨迹" in html
    assert "周围车辆" in html
    assert "not_applicable" in html
    assert "试标进度" in html
    assert "sampling_stratum" not in html
    assert "head.join(',')+'\\n'+rows.join('\\n')" in html
    match = re.search(r"const DATA=(.*?);const STORAGE_KEY=", html)
    assert match is not None
    data = json.loads(match.group(1))
    assert len(data["cases"]) == 40
    assert sum(case["pilot_batch"] for case in data["cases"]) == 8
    candidate_case = next(case for case in data["cases"] if case["has_candidate_leader"])
    assert len(candidate_case["ego_track"]) >= 2
    assert len(candidate_case["leader_track"]) >= 2
    assert candidate_case["nearby_vehicles"]
    assert {case["display_road_id"] for case in data["cases"]} == {"10"}
    rejected_case = next(case for case in data["cases"] if case["road_id"] is None)
    assert rejected_case["display_road_id"] == "10"
    assert rejected_case["display_road_distance_m"] >= 0
    assert (output / "SHA256SUMS").is_file()
