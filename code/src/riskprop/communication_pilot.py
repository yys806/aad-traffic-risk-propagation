"""Risk and communication summaries for the explicit-communication pilot."""

from __future__ import annotations

import math

import pandas as pd


TARGET_EDGES = frozenset({"bottom", "left", ":center_1"})
MISSING_TEXT = frozenset({"", "-1", "nan", "none", "null"})
RUN_KEY_COLUMNS = [
    "condition",
    "stress_profile",
    "penetration_pct",
    "configured_run_seed",
]


def select_valid_run_results(
    primary: pd.DataFrame,
    corrected_source_high: pd.DataFrame,
    corrected_communication: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Replace run cells invalidated by parsing or cross-run channel-state bugs."""
    required = set(RUN_KEY_COLUMNS)
    frames = [("primary", primary), ("corrected", corrected_source_high)]
    if corrected_communication is not None:
        frames.append(("corrected_communication", corrected_communication))
    for label, frame in frames:
        if not required.issubset(frame.columns):
            missing = sorted(required - set(frame.columns))
            raise ValueError(f"{label} run table missing columns: {missing}")
    invalid_source = primary["condition"].isin({"off", "oracle"}) & primary[
        "stress_profile"
    ].eq("source_high")
    invalid_communication = pd.Series(False, index=primary.index)
    if corrected_communication is not None:
        corrected_keys = pd.MultiIndex.from_frame(
            corrected_communication[RUN_KEY_COLUMNS]
        )
        invalid_communication = pd.MultiIndex.from_frame(
            primary[RUN_KEY_COLUMNS]
        ).isin(corrected_keys)
    selected = pd.concat(
        [
            primary.loc[~(invalid_source | invalid_communication)].copy(),
            corrected_source_high.copy(),
            *(
                [corrected_communication.copy()]
                if corrected_communication is not None
                else []
            ),
        ],
        ignore_index=True,
    )
    duplicates = selected.duplicated(RUN_KEY_COLUMNS, keep=False)
    if duplicates.any():
        keys = selected.loc[duplicates, RUN_KEY_COLUMNS].to_dict("records")
        raise ValueError(f"Duplicate valid run keys: {keys}")
    return selected.sort_values(RUN_KEY_COLUMNS).reset_index(drop=True)


def target_zone_mask(
    emissions: pd.DataFrame,
    *,
    x_min: float = 540.0,
    x_max: float = 612.0,
) -> pd.Series:
    if not {"edge_id", "x"}.issubset(emissions.columns):
        raise ValueError("Emissions require edge_id and x for target-zone filtering")
    edge = emissions["edge_id"].fillna("").astype(str)
    x = pd.to_numeric(emissions["x"], errors="coerce")
    return edge.isin(TARGET_EDGES) & x.between(float(x_min), float(x_max))


def _leader_aware_ttc(emissions: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    index = emissions.index
    leader = emissions.get("leader_id", pd.Series(index=index, dtype=object))
    leader_text = leader.fillna("").astype(str).str.strip().str.lower()
    has_leader = leader.notna() & ~leader_text.isin(MISSING_TEXT)
    headway = pd.to_numeric(
        emissions.get("headway", pd.Series(index=index, dtype=float)),
        errors="coerce",
    )
    closing = -pd.to_numeric(
        emissions.get("leader_rel_speed", pd.Series(index=index, dtype=float)),
        errors="coerce",
    )
    valid = (
        has_leader
        & headway.notna()
        & (headway > 0)
        & (headway < 1e5)
        & (closing > 1e-3)
    )
    ttc = pd.Series(float("inf"), index=index, dtype=float)
    ttc.loc[valid] = headway.loc[valid] / closing.loc[valid]
    return ttc, valid


def summarize_target_risk(
    emissions: pd.DataFrame,
    *,
    ttc_threshold_s: float = 2.0,
    hard_brake_threshold_mps2: float = -4.5,
) -> dict[str, float | int | None]:
    target = emissions.loc[target_zone_mask(emissions)].copy()
    ttc, valid = _leader_aware_ttc(target)
    valid_ttc = ttc.loc[valid]
    violation = valid_ttc < float(ttc_threshold_s)
    burden = (float(ttc_threshold_s) - valid_ttc).clip(lower=0.0)
    accel = pd.to_numeric(
        target.get("realized_accel", pd.Series(index=target.index, dtype=float)),
        errors="coerce",
    )
    speed = pd.to_numeric(
        target.get("speed", pd.Series(index=target.index, dtype=float)),
        errors="coerce",
    )
    target_steps = int(len(target))
    valid_count = int(valid.sum())
    hard_brake_count = int((accel < float(hard_brake_threshold_mps2)).sum())
    return {
        "target_vehicle_step_count": target_steps,
        "valid_ttc_count": valid_count,
        "ttc_violation_count": int(violation.sum()),
        "ttc_violation_rate": (
            float(violation.mean()) if valid_count else None
        ),
        "ttc_conflict_burden": (
            float(burden.sum() / valid_count) if valid_count else None
        ),
        "minimum_ttc_s": float(valid_ttc.min()) if valid_count else None,
        "hard_brake_count": hard_brake_count,
        "hard_brake_rate_per_1000_steps": (
            float(hard_brake_count / target_steps * 1000.0)
            if target_steps
            else None
        ),
        "mean_speed_mps": float(speed.mean()) if speed.notna().any() else None,
    }


def _bool_series(records: pd.DataFrame, column: str) -> pd.Series:
    if column not in records.columns:
        return pd.Series(False, index=records.index, dtype=bool)
    values = records[column]
    if values.dtype == bool:
        return values.fillna(False)
    text = values.fillna(False).astype(str).str.strip().str.lower()
    return text.isin({"1", "true", "yes"})


def summarize_communication_records(
    records: pd.DataFrame,
) -> dict[str, float | int | None]:
    generated = _bool_series(records, "message_generated")
    sent = _bool_series(records, "message_sent")
    dropped = _bool_series(records, "message_dropped")
    delivered = _bool_series(records, "message_delivered")
    cache_usable = _bool_series(records, "cache_usable")
    applied = _bool_series(records, "applied")
    sent_count = int(sent.sum())
    return {
        "record_count": int(len(records)),
        "generated_count": int(generated.sum()),
        "sent_count": sent_count,
        "dropped_count": int(dropped.sum()),
        "delivered_count": int(delivered.sum()),
        "cache_usable_count": int(cache_usable.sum()),
        "applied_count": int(applied.sum()),
        "drop_rate": float(dropped.sum() / sent_count) if sent_count else None,
    }


def merge_communication_episodes(records: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "run_token",
        "sumo_seed",
        "ego_vehicle_id",
        "start_step",
        "end_step",
        "record_count",
    ]
    if records.empty:
        return pd.DataFrame(columns=columns)
    required = {"run_token", "sumo_seed", "ego_vehicle_id", "step", "applied"}
    if not required.issubset(records.columns):
        missing = sorted(required - set(records.columns))
        raise ValueError(f"Communication records missing columns: {missing}")
    applied = records.loc[_bool_series(records, "applied")].copy()
    if applied.empty:
        return pd.DataFrame(columns=columns)
    applied["step"] = pd.to_numeric(applied["step"], errors="raise").astype(int)
    rows: list[dict[str, object]] = []
    group_columns = ["run_token", "sumo_seed", "ego_vehicle_id"]
    for keys, group in applied.sort_values(group_columns + ["step"]).groupby(
        group_columns, sort=True, dropna=False
    ):
        start = None
        end = None
        count = 0
        for step in group["step"].tolist():
            if start is None or (end is not None and step > end + 1):
                if start is not None:
                    rows.append(
                        {
                            **dict(zip(group_columns, keys)),
                            "start_step": start,
                            "end_step": end,
                            "record_count": count,
                        }
                    )
                start = step
                count = 1
            else:
                count += 1
            end = step
        rows.append(
            {
                **dict(zip(group_columns, keys)),
                "start_step": start,
                "end_step": end,
                "record_count": count,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_factorial_effects(
    run_metrics: pd.DataFrame,
    *,
    metric: str,
) -> pd.DataFrame:
    required = {
        "penetration_pct",
        "configured_run_seed",
        "stress_profile",
        "condition",
        metric,
    }
    if not required.issubset(run_metrics.columns):
        missing = sorted(required - set(run_metrics.columns))
        raise ValueError(f"Run metrics missing columns: {missing}")
    rows = []
    keys = ["penetration_pct", "configured_run_seed"]
    for (penetration, run_seed), group in run_metrics.groupby(keys, sort=True):
        values = {
            (str(row.stress_profile), str(row.condition)): float(getattr(row, metric))
            for row in group.itertuples(index=False)
            if not pd.isna(getattr(row, metric))
        }
        needed = {
            ("nominal", "off"),
            ("nominal", "comm_ideal"),
            ("source_high", "off"),
            ("source_high", "comm_ideal"),
        }
        if not needed.issubset(values):
            continue
        nominal_effect = values[("nominal", "comm_ideal")] - values[("nominal", "off")]
        source_high_effect = (
            values[("source_high", "comm_ideal")]
            - values[("source_high", "off")]
        )
        rows.append(
            {
                "penetration_pct": int(penetration),
                "configured_run_seed": int(run_seed),
                "metric": metric,
                "communication_effect_nominal": nominal_effect,
                "communication_effect_source_high": source_high_effect,
                "factorial_interaction": source_high_effect - nominal_effect,
            }
        )
    return pd.DataFrame(rows).sort_values(keys).reset_index(drop=True)
