from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class EventThresholds:
    hard_brake_accel: float = -3.0
    severe_brake_accel: float = -6.0
    override_candidate_accel: float = -15.0
    low_ttc_s: float = 2.0
    critical_ttc_s: float = 1.0
    low_thw_s: float = 1.0
    near_miss_ttc_s: float = 1.5
    near_miss_accel: float = -3.0
    region_length_m: float = 50.0


def extract_risk_events(
    emissions: pd.DataFrame,
    thresholds: EventThresholds | None = None,
) -> pd.DataFrame:
    """Extract rule-based risk events from rollout/emission rows."""
    thresholds = thresholds or EventThresholds()
    rows = _normalise_emissions(emissions, thresholds.region_length_m)

    events: list[dict[str, object]] = []
    for _, row in rows.iterrows():
        base = _event_base(row)
        accel = _as_float(row.get("acceleration"))
        ttc = _as_float(row.get("ttc"))
        thw = _as_float(row.get("thw"))

        if accel < thresholds.override_candidate_accel:
            events.append(
                {
                    **base,
                    "event_type": "safe_speed_override_candidate",
                    "event_severity": "extreme",
                    "risk_score": 1.0,
                }
            )
        elif accel <= thresholds.hard_brake_accel:
            severity = "severe" if accel <= thresholds.severe_brake_accel else "hard"
            events.append(
                {
                    **base,
                    "event_type": "hard_braking",
                    "event_severity": severity,
                    "risk_score": _score_by_threshold(
                        abs(accel), abs(thresholds.hard_brake_accel), 8.0
                    ),
                }
            )

        if ttc <= thresholds.low_ttc_s:
            events.append({**base, "event_type": "low_ttc", "event_severity": "low", "risk_score": _inverse_score(ttc, thresholds.low_ttc_s)})

        if ttc <= thresholds.critical_ttc_s:
            events.append({**base, "event_type": "critical_ttc", "event_severity": "critical", "risk_score": _inverse_score(ttc, thresholds.critical_ttc_s)})

        if thw <= thresholds.low_thw_s:
            events.append({**base, "event_type": "low_thw", "event_severity": "low", "risk_score": _inverse_score(thw, thresholds.low_thw_s)})

        if (
            ttc <= thresholds.near_miss_ttc_s
            and thresholds.override_candidate_accel <= accel <= thresholds.near_miss_accel
        ):
            events.append({**base, "event_type": "near_miss", "event_severity": "critical", "risk_score": max(_inverse_score(ttc, thresholds.near_miss_ttc_s), 0.8)})

    if not events:
        return _empty_events()

    event_frame = pd.DataFrame(events).sort_values(["run_id", "time", "vehicle_id", "event_type"]).reset_index(drop=True)
    event_frame.insert(0, "event_id", [f"e{i:06d}" for i in range(len(event_frame))])
    return event_frame


def coalesce_risk_events(events: pd.DataFrame, max_gap_s: float = 0.4) -> pd.DataFrame:
    """Merge consecutive frame-level detections into event-level risk episodes."""
    if events.empty:
        return _empty_episodes()
    if max_gap_s <= 0:
        raise ValueError("max_gap_s must be positive")

    required_defaults = {"run_id": "run_0", "vehicle_id": "", "event_type": "unknown", "risk_score": 0.0}
    rows = events.copy()
    for column, default in required_defaults.items():
        if column not in rows.columns:
            rows[column] = default
    rows = rows.sort_values(["run_id", "vehicle_id", "event_type", "time", "event_id"]).reset_index(drop=True)

    episodes: list[dict[str, object]] = []
    for _, group in rows.groupby(["run_id", "vehicle_id", "event_type"], sort=False):
        current: list[pd.Series] = []
        previous_time: float | None = None
        for _, row in group.iterrows():
            time = _as_float(row.get("time"))
            if current and previous_time is not None and time - previous_time > max_gap_s:
                episodes.append(_episode_from_rows(current))
                current = []
            current.append(row)
            previous_time = time
        if current:
            episodes.append(_episode_from_rows(current))

    episode_frame = pd.DataFrame(episodes).sort_values(["run_id", "time", "vehicle_id", "event_type"]).reset_index(drop=True)
    episode_frame.insert(0, "event_id", [f"ep{i:06d}" for i in range(len(episode_frame))])
    return episode_frame


def _normalise_emissions(emissions: pd.DataFrame, region_length_m: float) -> pd.DataFrame:
    rows = emissions.copy()
    if "run_id" not in rows.columns:
        rows["run_id"] = "run_0"
    if "vehicle_id" not in rows.columns:
        rows["vehicle_id"] = rows["id"] if "id" in rows.columns else rows.index.astype(str)
    if "acceleration" not in rows.columns:
        if "realized_accel" in rows.columns:
            rows["acceleration"] = rows["realized_accel"]
        else:
            rows = rows.sort_values(["run_id", "vehicle_id", "time"])
            rows["acceleration"] = rows.groupby(["run_id", "vehicle_id"])["speed"].diff() / rows.groupby(["run_id", "vehicle_id"])["time"].diff()
    if {"headway", "speed", "leader_id"}.issubset(rows.columns):
        rows["thw"] = _estimate_thw(rows)
    elif "thw" not in rows.columns:
        rows["thw"] = float("inf")
    if "ttc" not in rows.columns:
        rows["ttc"] = _estimate_ttc(rows)
    if "x" not in rows.columns:
        rows["x"] = 0.0
    if "lane" not in rows.columns:
        rows["lane"] = _flow_lane_identifier(rows)
    if "leader_id" not in rows.columns:
        rows["leader_id"] = ""
    rows["region_id"] = rows.apply(lambda row: _region_id(row, region_length_m), axis=1)
    return rows


def _estimate_ttc(rows: pd.DataFrame) -> pd.Series:
    if not {"headway", "leader_id", "leader_rel_speed"}.issubset(rows.columns):
        return pd.Series(float("inf"), index=rows.index)
    closing_speed = -pd.to_numeric(rows["leader_rel_speed"], errors="coerce")
    headway = pd.to_numeric(rows["headway"], errors="coerce")
    leader = rows["leader_id"]
    leader_text = leader.fillna("").astype(str).str.strip().str.lower()
    has_leader = leader.notna() & ~leader_text.isin({"", "nan", "none", "null", "unknown"})
    valid_closing = has_leader & (closing_speed > 0)
    ttc = headway / closing_speed.where(valid_closing)
    return ttc.fillna(float("inf"))


def _estimate_thw(rows: pd.DataFrame) -> pd.Series:
    leader = rows["leader_id"]
    leader_text = leader.fillna("").astype(str).str.strip().str.lower()
    has_leader = leader.notna() & ~leader_text.isin(
        {"", "nan", "none", "null", "unknown"}
    )
    headway = pd.to_numeric(rows["headway"], errors="coerce")
    speed = pd.to_numeric(rows["speed"], errors="coerce")
    valid = has_leader & (headway > 0) & (headway < 1e5) & (speed > 1e-3)
    thw = headway / speed.where(valid)
    return thw.fillna(float("inf"))


def _flow_lane_identifier(rows: pd.DataFrame) -> pd.Series:
    if "edge_id" not in rows.columns:
        return pd.Series("unknown", index=rows.index)
    edge = rows["edge_id"].fillna("unknown").astype(str).str.strip()
    edge = edge.mask(edge.eq(""), "unknown")
    if "lane_number" not in rows.columns:
        return edge
    lane_number = pd.to_numeric(rows["lane_number"], errors="coerce")
    lane_text = lane_number.map(lambda value: str(int(value)) if pd.notna(value) else "unknown")
    return edge + ":" + lane_text


def _event_base(row: pd.Series) -> dict[str, object]:
    return {
        "run_id": str(row.get("run_id", "run_0")),
        "time": _as_float(row.get("time")),
        "vehicle_id": str(row.get("vehicle_id", row.get("id", ""))),
        "leader_id": str(row.get("leader_id", "")),
        "x": _as_float(row.get("x")),
        "lane": str(row.get("lane", "unknown")),
        "region_id": str(row.get("region_id", "unknown_0")),
        "speed": _as_float(row.get("speed")),
        "acceleration": _as_float(row.get("acceleration")),
        "headway": _as_float(row.get("headway")),
        "ttc": _as_float(row.get("ttc")),
        "thw": _as_float(row.get("thw")),
    }


def _episode_from_rows(rows: list[pd.Series]) -> dict[str, object]:
    first = rows[0].to_dict()
    last = rows[-1]
    risk_scores = [_as_float(row.get("risk_score")) for row in rows]
    times = [_as_float(row.get("time")) for row in rows]
    first["risk_score"] = max(risk_scores)
    first["episode_start_s"] = min(times)
    first["episode_end_s"] = max(times)
    first["episode_duration_s"] = max(times) - min(times)
    first["raw_event_count"] = len(rows)
    first["raw_event_ids"] = "|".join(str(row.get("event_id", "")) for row in rows)
    severities = [str(row.get("event_severity", "")) for row in rows]
    if any(severities):
        severity_order = {"": 0, "low": 1, "hard": 2, "severe": 3, "critical": 4, "extreme": 5}
        first["event_severity"] = max(
            severities, key=lambda value: severity_order.get(value, 0)
        )
    accelerations = [_as_float(row.get("acceleration")) for row in rows]
    finite_accelerations = [value for value in accelerations if math.isfinite(value)]
    first["peak_acceleration_mps2"] = (
        min(finite_accelerations) if finite_accelerations else float("nan")
    )
    for column in (
        "next_time_s",
        "next_speed_mps",
        "next_acceleration_mps2",
        "next_headway_m",
        "next_leader_id",
        "next_lane",
        "is_last_vehicle_row",
    ):
        if column in last.index:
            first[column] = last.get(column)
    for column in (
        "previous_leader_changed",
        "next_leader_changed",
        "previous_lane_changed",
        "next_lane_changed",
        "adjacent_override_candidate",
    ):
        if any(column in row.index for row in rows):
            first[column] = any(bool(row.get(column, False)) for row in rows)
    first.pop("event_id", None)
    return first


def _region_id(row: pd.Series, region_length_m: float) -> str:
    lane = str(row.get("lane", "unknown"))
    x = _as_float(row.get("x"))
    bucket = int(x // region_length_m) if region_length_m > 0 else 0
    return f"{lane}_{bucket}"


def _empty_events() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "event_id",
            "run_id",
            "time",
            "vehicle_id",
            "leader_id",
            "event_type",
            "event_severity",
            "risk_score",
            "x",
            "lane",
            "region_id",
            "speed",
            "acceleration",
            "headway",
            "ttc",
            "thw",
        ]
    )


def _empty_episodes() -> pd.DataFrame:
    columns = _empty_events().columns.tolist() + ["episode_start_s", "episode_end_s", "episode_duration_s", "raw_event_count", "raw_event_ids"]
    return pd.DataFrame(columns=columns)


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")


def _score_by_threshold(value: float, threshold: float, cap: float) -> float:
    if threshold <= 0:
        return 0.0
    return min(max(value / cap, threshold / cap), 1.0)


def _inverse_score(value: float, threshold: float) -> float:
    if value == float("inf") or threshold <= 0:
        return 0.0
    return min(max((threshold - value) / threshold + 0.5, 0.0), 1.0)
