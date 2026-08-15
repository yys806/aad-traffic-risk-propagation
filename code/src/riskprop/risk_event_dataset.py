"""Build a validated event dataset from formal Flow emission files."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from riskprop.events import coalesce_risk_events, extract_risk_events


EVENT_TYPES = (
    "hard_braking",
    "safe_speed_override_candidate",
    "low_ttc",
    "critical_ttc",
    "low_thw",
    "near_miss",
)
MISSING_TEXT = {"", "nan", "none", "null", "unknown"}
FILENAME_PATTERN = re.compile(
    r"^(?P<scenario>ring|figure8|merge)_(?P<method>[^_]+)_p(?P<penetration>\d+)_.*-(?P<run>\d+)_emission\.csv$"
)


def parse_emission_metadata(path: Path) -> dict[str, object]:
    """Parse scenario, method, penetration, and run index from a formal filename."""
    match = FILENAME_PATTERN.match(Path(path).name)
    if not match:
        raise ValueError(f"Unsupported formal emission filename: {Path(path).name}")
    return {
        "scenario": match.group("scenario"),
        "method": match.group("method"),
        "penetration_pct": int(match.group("penetration")),
        "run_index": int(match.group("run")),
    }


def discover_formal_emissions(raw_output_root: Path) -> list[Path]:
    """Select adopted DRIFT emissions and matching formal FS/PI emissions."""
    root = Path(raw_output_root)
    main = root / "penetration_main_formal_v1" / "emissions"
    groups = (
        (main, "ring_ours_*_emission.csv"),
        (root / "ours_f8_adopted_formal_v1" / "emissions", "figure8_ours_*_emission.csv"),
        (root / "ours_merge_eta_adopt_formal_v1" / "emissions", "merge_ours_*_emission.csv"),
        (main, "*_fs_*_emission.csv"),
        (main, "*_pi_*_emission.csv"),
    )
    paths: list[Path] = []
    for directory, pattern in groups:
        paths.extend(sorted(directory.glob(pattern)))
    return sorted(set(paths), key=lambda path: path.name)


def compute_vehicle_time_seconds(emissions: pd.DataFrame) -> float:
    """Return vehicle-time exposure as frame rows times the median simulation step."""
    if emissions.empty or "time" not in emissions.columns:
        return 0.0
    times = np.sort(pd.to_numeric(emissions["time"], errors="coerce").dropna().unique())
    positive_steps = np.diff(times)
    positive_steps = positive_steps[positive_steps > 0]
    if len(positive_steps) == 0:
        return 0.0
    step_s = float(np.median(positive_steps))
    return float(len(emissions) * step_s)


def threshold_sensitivity_for_run(
    emissions: pd.DataFrame,
    *,
    metadata: Mapping[str, object],
    source_file: str,
    ttc_thresholds: Sequence[float] = (1.0, 1.5, 2.0, 3.0),
    braking_thresholds: Sequence[float] = (-3.0, -4.5, -6.0),
    override_candidate_accel: float = -15.0,
) -> pd.DataFrame:
    """Compute leader-aware TTC and ordinary-braking rates for one run."""
    exposure = compute_vehicle_time_seconds(emissions)
    ttc = _leader_aware_ttc(emissions)
    acceleration = pd.to_numeric(
        emissions.get("realized_accel", pd.Series(index=emissions.index, dtype=float)),
        errors="coerce",
    )
    base = {
        **metadata,
        "run_id": Path(source_file).stem,
        "source_file": source_file,
        "row_count": int(len(emissions)),
        "vehicle_time_s": exposure,
    }
    rows: list[dict[str, object]] = []
    for threshold in ttc_thresholds:
        count = int((ttc <= float(threshold)).sum())
        rows.append(
            {
                **base,
                "metric": "ttc_conflict",
                "threshold": float(threshold),
                "frame_count": count,
                "rate_per_1000_vehicle_s": _rate(count, exposure),
            }
        )
    ordinary = acceleration >= override_candidate_accel
    for threshold in braking_thresholds:
        count = int(((acceleration <= float(threshold)) & ordinary).sum())
        rows.append(
            {
                **base,
                "metric": "ordinary_braking",
                "threshold": float(threshold),
                "frame_count": count,
                "rate_per_1000_vehicle_s": _rate(count, exposure),
            }
        )
    override_count = int((acceleration < override_candidate_accel).sum())
    rows.append(
        {
            **base,
            "metric": "safe_speed_override_candidate",
            "threshold": float(override_candidate_accel),
            "frame_count": override_count,
            "rate_per_1000_vehicle_s": _rate(override_count, exposure),
        }
    )
    return pd.DataFrame(rows)


def event_rates_for_run(
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    *,
    metadata: Mapping[str, object],
    run_id: str,
    source_file: str,
    vehicle_time_s: float,
) -> pd.DataFrame:
    """Count frame detections and episodes for every event class in one run."""
    rows = []
    for event_type in EVENT_TYPES:
        frame_count = int((events.get("event_type") == event_type).sum()) if not events.empty else 0
        episode_count = int((episodes.get("event_type") == event_type).sum()) if not episodes.empty else 0
        rows.append(
            {
                **metadata,
                "run_id": run_id,
                "source_file": source_file,
                "event_type": event_type,
                "frame_count": frame_count,
                "episode_count": episode_count,
                "vehicle_time_s": vehicle_time_s,
                "frame_rate_per_1000_vehicle_s": _rate(frame_count, vehicle_time_s),
                "episode_rate_per_1000_vehicle_s": _rate(episode_count, vehicle_time_s),
            }
        )
    return pd.DataFrame(rows)


def summarise_event_rates(by_run: pd.DataFrame) -> pd.DataFrame:
    """Aggregate event counts and rates across matching formal runs."""
    if by_run.empty:
        return pd.DataFrame()
    keys = ["scenario", "method", "penetration_pct", "event_type"]
    rows = []
    for key, group in by_run.groupby(keys, sort=True, dropna=False):
        frame_rates = pd.to_numeric(group["frame_rate_per_1000_vehicle_s"], errors="coerce")
        episode_rates = pd.to_numeric(group["episode_rate_per_1000_vehicle_s"], errors="coerce")
        exposure = float(group["vehicle_time_s"].sum())
        frame_count = int(group["frame_count"].sum())
        episode_count = int(group["episode_count"].sum())
        rows.append(
            {
                **dict(zip(keys, key)),
                "run_count": int(group["run_id"].nunique()),
                "frame_count": frame_count,
                "episode_count": episode_count,
                "vehicle_time_s": exposure,
                "pooled_frame_rate_per_1000_vehicle_s": _rate(frame_count, exposure),
                "pooled_episode_rate_per_1000_vehicle_s": _rate(episode_count, exposure),
                "episode_rate_run_mean": float(episode_rates.mean()),
                "episode_rate_run_std": float(episode_rates.std(ddof=1)) if len(episode_rates) > 1 else 0.0,
                "episode_rate_run_ci95": _ci95(episode_rates),
                "frame_rate_run_mean": float(frame_rates.mean()),
                "frame_rate_run_std": float(frame_rates.std(ddof=1)) if len(frame_rates) > 1 else 0.0,
                "frame_rate_run_ci95": _ci95(frame_rates),
            }
        )
    return pd.DataFrame(rows)


def summarise_threshold_sensitivity(by_run: pd.DataFrame) -> pd.DataFrame:
    """Aggregate threshold results while retaining run-level uncertainty."""
    if by_run.empty:
        return pd.DataFrame()
    keys = ["scenario", "method", "penetration_pct", "metric", "threshold"]
    rows = []
    for key, group in by_run.groupby(keys, sort=True, dropna=False):
        rates = pd.to_numeric(group["rate_per_1000_vehicle_s"], errors="coerce")
        exposure = float(group["vehicle_time_s"].sum())
        count = int(group["frame_count"].sum())
        rows.append(
            {
                **dict(zip(keys, key)),
                "run_count": int(group["run_id"].nunique()),
                "frame_count": count,
                "vehicle_time_s": exposure,
                "pooled_rate_per_1000_vehicle_s": _rate(count, exposure),
                "run_rate_mean": float(rates.mean()),
                "run_rate_std": float(rates.std(ddof=1)) if len(rates) > 1 else 0.0,
                "run_rate_ci95": _ci95(rates),
            }
        )
    return pd.DataFrame(rows)


def compare_sensitivity_with_drift(
    summary: pd.DataFrame, *, drift_method: str = "ours"
) -> pd.DataFrame:
    """Compare exposure-normalized DRIFT rates with matching baselines."""
    if summary.empty:
        return pd.DataFrame()
    keys = ["scenario", "penetration_pct", "metric", "threshold"]
    rows = []
    for key, group in summary.groupby(keys, sort=True, dropna=False):
        drift = group.loc[group["method"] == drift_method]
        if drift.empty:
            continue
        drift_rate = float(drift.iloc[0]["pooled_rate_per_1000_vehicle_s"])
        for _, baseline in group.loc[group["method"] != drift_method].iterrows():
            baseline_rate = float(baseline["pooled_rate_per_1000_vehicle_s"])
            improvement = baseline_rate - drift_rate
            rows.append(
                {
                    **dict(zip(keys, key)),
                    "baseline": str(baseline["method"]),
                    "drift_rate_per_1000_vehicle_s": drift_rate,
                    "baseline_rate_per_1000_vehicle_s": baseline_rate,
                    "signed_improvement": improvement,
                    "drift_better": improvement > 1e-12,
                    "tie": abs(improvement) <= 1e-12,
                }
            )
    return pd.DataFrame(rows)


def select_manual_review_sample(
    events: pd.DataFrame, *, per_event_type: int = 10
) -> pd.DataFrame:
    """Select deterministic high-risk examples for manual adjacent-frame review."""
    if events.empty:
        return events.copy()
    if per_event_type <= 0:
        raise ValueError("per_event_type must be positive")
    priority_columns = [
        column
        for column in (
            "event_type",
            "risk_score",
            "scenario",
            "method",
            "penetration_pct",
            "run_id",
            "time",
            "vehicle_id",
            "event_id",
        )
        if column in events.columns
    ]
    ascending = [column != "risk_score" for column in priority_columns]
    ranked = events.sort_values(priority_columns, ascending=ascending, kind="mergesort").copy()
    strata = [column for column in ("event_type", "scenario", "method") if column in ranked.columns]
    ranked["_stratum_rank"] = ranked.groupby(strata, sort=True).cumcount()
    selection_columns = [
        column
        for column in (
            "event_type",
            "_stratum_rank",
            "risk_score",
            "scenario",
            "method",
            "penetration_pct",
            "run_id",
            "time",
            "vehicle_id",
            "event_id",
        )
        if column in ranked.columns
    ]
    selection_ascending = [column != "risk_score" for column in selection_columns]
    ranked = ranked.sort_values(
        selection_columns, ascending=selection_ascending, kind="mergesort"
    )
    sample = ranked.groupby("event_type", sort=True, group_keys=False).head(per_event_type).copy()
    sample = sample.drop(columns="_stratum_rank")
    return apply_review_checklist(sample.reset_index(drop=True))


def apply_review_checklist(sample: pd.DataFrame) -> pd.DataFrame:
    """Record exclusion and context flags after adjacent-frame review."""
    reviewed = sample.copy()
    statuses: list[str] = []
    notes: list[str] = []
    for _, row in reviewed.iterrows():
        row_notes: list[str] = []
        excluded = False
        if str(row.get("event_type", "")) == "safe_speed_override_candidate":
            row_notes.append("override_candidate")
            excluded = True
        if bool(row.get("is_first_vehicle_row", False)) or bool(
            row.get("is_last_vehicle_row", False)
        ):
            row_notes.append("entry_exit_boundary")
            excluded = True
        if bool(row.get("previous_leader_changed", False)) or bool(
            row.get("next_leader_changed", False)
        ):
            row_notes.append("leader_transition")
        if bool(row.get("previous_lane_changed", False)) or bool(
            row.get("next_lane_changed", False)
        ):
            row_notes.append("lane_transition")
        if bool(row.get("adjacent_override_candidate", False)):
            row_notes.append("adjacent_override")
        if excluded:
            status = "excluded"
        elif row_notes:
            status = "retained_flagged"
        else:
            status = "retained"
            row_notes.append("stable_context")
        statuses.append(status)
        notes.append("|".join(row_notes))
    reviewed.insert(0, "review_status", statuses)
    reviewed.insert(1, "review_notes", notes)
    return reviewed


def extract_formal_event_dataset(paths: Iterable[Path]) -> dict[str, pd.DataFrame]:
    """Extract events, episodes, rates, sensitivity, and review samples."""
    event_frames: list[pd.DataFrame] = []
    episode_frames: list[pd.DataFrame] = []
    rate_frames: list[pd.DataFrame] = []
    sensitivity_frames: list[pd.DataFrame] = []
    manifest_rows: list[dict[str, object]] = []

    for path in (Path(item) for item in paths):
        metadata = parse_emission_metadata(path)
        emissions = pd.read_csv(path)
        required = {"time", "id", "speed", "realized_accel"}
        missing = sorted(required - set(emissions.columns))
        if missing:
            raise ValueError(f"{path.name} missing required columns: {', '.join(missing)}")
        run_id = path.stem
        emissions["run_id"] = run_id
        exposure = compute_vehicle_time_seconds(emissions)
        events = extract_risk_events(emissions)
        events = _attach_context(events, emissions, metadata, path.name)
        episodes = coalesce_risk_events(events)
        if not events.empty:
            event_frames.append(events)
        if not episodes.empty:
            episode_frames.append(episodes)
        rate_frames.append(
            event_rates_for_run(
                events,
                episodes,
                metadata=metadata,
                run_id=run_id,
                source_file=path.name,
                vehicle_time_s=exposure,
            )
        )
        sensitivity_frames.append(
            threshold_sensitivity_for_run(
                emissions, metadata=metadata, source_file=path.name
            )
        )
        time_values = np.sort(pd.to_numeric(emissions["time"], errors="coerce").dropna().unique())
        steps = np.diff(time_values)
        steps = steps[steps > 0]
        manifest_rows.append(
            {
                **metadata,
                "run_id": run_id,
                "source_file": path.name,
                "row_count": int(len(emissions)),
                "vehicle_count": int(emissions["id"].nunique()),
                "simulation_step_s": float(np.median(steps)) if len(steps) else float("nan"),
                "vehicle_time_s": exposure,
            }
        )

    events = pd.concat(event_frames, ignore_index=True) if event_frames else pd.DataFrame()
    if not events.empty:
        events["event_id"] = [f"e{i:08d}" for i in range(len(events))]
        episodes = coalesce_risk_events(events)
    else:
        episodes = pd.concat(episode_frames, ignore_index=True) if episode_frames else pd.DataFrame()
    by_run = pd.concat(rate_frames, ignore_index=True) if rate_frames else pd.DataFrame()
    sensitivity_by_run = (
        pd.concat(sensitivity_frames, ignore_index=True) if sensitivity_frames else pd.DataFrame()
    )
    sensitivity_summary = summarise_threshold_sensitivity(sensitivity_by_run)
    return {
        "manifest": pd.DataFrame(manifest_rows),
        "events": events,
        "episodes": episodes,
        "event_rates_by_run": by_run,
        "event_rates_summary": summarise_event_rates(by_run),
        "threshold_sensitivity_by_run": sensitivity_by_run,
        "threshold_sensitivity_summary": sensitivity_summary,
        "threshold_sensitivity_comparison": compare_sensitivity_with_drift(
            sensitivity_summary
        ),
        "manual_review_sample": select_manual_review_sample(episodes),
    }


def _attach_context(
    events: pd.DataFrame,
    emissions: pd.DataFrame,
    metadata: Mapping[str, object],
    source_file: str,
) -> pd.DataFrame:
    if events.empty:
        return events
    context = emissions.copy()
    context["time"] = pd.to_numeric(context["time"], errors="coerce")
    context["_context_acceleration"] = pd.to_numeric(
        context.get("realized_accel", pd.Series(index=context.index, dtype=float)),
        errors="coerce",
    )
    context["_context_headway"] = pd.to_numeric(
        context.get("headway", pd.Series(index=context.index, dtype=float)),
        errors="coerce",
    )
    context["_context_lane"] = _context_lane(context)
    context = context.sort_values(["id", "time"]).copy()
    context["previous_time_s"] = context.groupby("id")["time"].shift()
    context["previous_speed_mps"] = context.groupby("id")["speed"].shift()
    context["previous_acceleration_mps2"] = context.groupby("id")["_context_acceleration"].shift()
    context["previous_headway_m"] = context.groupby("id")["_context_headway"].shift()
    context["previous_leader_id"] = context.groupby("id")["leader_id"].shift()
    context["previous_lane"] = context.groupby("id")["_context_lane"].shift()
    context["next_time_s"] = context.groupby("id")["time"].shift(-1)
    context["next_speed_mps"] = context.groupby("id")["speed"].shift(-1)
    context["next_acceleration_mps2"] = context.groupby("id")["_context_acceleration"].shift(-1)
    context["next_headway_m"] = context.groupby("id")["_context_headway"].shift(-1)
    context["next_leader_id"] = context.groupby("id")["leader_id"].shift(-1)
    context["next_lane"] = context.groupby("id")["_context_lane"].shift(-1)
    keep = [
        "run_id",
        "time",
        "id",
        "previous_time_s",
        "previous_speed_mps",
        "previous_acceleration_mps2",
        "previous_headway_m",
        "previous_leader_id",
        "previous_lane",
        "next_time_s",
        "next_speed_mps",
        "next_acceleration_mps2",
        "next_headway_m",
        "next_leader_id",
        "next_lane",
    ]
    context = context[keep].rename(columns={"id": "vehicle_id"})
    result = events.merge(context, on=["run_id", "time", "vehicle_id"], how="left")
    result["is_first_vehicle_row"] = result["previous_time_s"].isna()
    result["is_last_vehicle_row"] = result["next_time_s"].isna()
    result["previous_leader_changed"] = _changed_text(
        result["previous_leader_id"], result["leader_id"]
    )
    result["next_leader_changed"] = _changed_text(
        result["leader_id"], result["next_leader_id"]
    )
    result["previous_lane_changed"] = _changed_text(
        result["previous_lane"], result["lane"]
    )
    result["next_lane_changed"] = _changed_text(result["lane"], result["next_lane"])
    previous_acceleration = pd.to_numeric(
        result["previous_acceleration_mps2"], errors="coerce"
    )
    next_acceleration = pd.to_numeric(
        result["next_acceleration_mps2"], errors="coerce"
    )
    result["adjacent_override_candidate"] = (previous_acceleration < -15.0) | (
        next_acceleration < -15.0
    )
    for key, value in metadata.items():
        result[key] = value
    result["source_file"] = source_file
    return result


def _context_lane(emissions: pd.DataFrame) -> pd.Series:
    if "lane" in emissions.columns:
        return emissions["lane"].fillna("unknown").astype(str)
    if "edge_id" not in emissions.columns:
        return pd.Series("unknown", index=emissions.index)
    edge = emissions["edge_id"].fillna("unknown").astype(str).str.strip()
    edge = edge.mask(edge.eq(""), "unknown")
    lane_number = pd.to_numeric(
        emissions.get("lane_number", pd.Series(index=emissions.index, dtype=float)),
        errors="coerce",
    )
    lane_text = lane_number.map(
        lambda value: str(int(value)) if pd.notna(value) else "unknown"
    )
    return edge + ":" + lane_text


def _changed_text(left: pd.Series, right: pd.Series) -> pd.Series:
    left_text = left.fillna("").astype(str).str.strip().str.lower()
    right_text = right.fillna("").astype(str).str.strip().str.lower()
    left_valid = ~left_text.isin(MISSING_TEXT)
    right_valid = ~right_text.isin(MISSING_TEXT)
    return left_valid & right_valid & left_text.ne(right_text)


def _leader_aware_ttc(emissions: pd.DataFrame) -> pd.Series:
    index = emissions.index
    leader = emissions.get("leader_id", pd.Series(index=index, dtype=object))
    leader_text = leader.fillna("").astype(str).str.strip().str.lower()
    has_leader = leader.notna() & ~leader_text.isin(MISSING_TEXT)
    headway = pd.to_numeric(
        emissions.get("headway", pd.Series(index=index, dtype=float)), errors="coerce"
    )
    closing = -pd.to_numeric(
        emissions.get("leader_rel_speed", pd.Series(index=index, dtype=float)),
        errors="coerce",
    )
    valid = has_leader & headway.notna() & (headway > 0) & (headway < 1e5) & (closing > 1e-3)
    result = pd.Series(float("inf"), index=index, dtype=float)
    result.loc[valid] = headway.loc[valid] / closing.loc[valid]
    return result


def _rate(count: int, vehicle_time_s: float) -> float:
    return float(count / vehicle_time_s * 1000.0) if vehicle_time_s > 0 else float("nan")


def _ci95(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) <= 1:
        return 0.0
    return float(1.96 * clean.std(ddof=1) / np.sqrt(len(clean)))
