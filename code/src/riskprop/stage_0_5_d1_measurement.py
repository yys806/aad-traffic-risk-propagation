"""D1 local measurement and common offset100 support (diagnostic v1).

This is an engineering implementation of already-approved event/exposure rules.
It never grants simulator equivalence, chooses a scientific margin, or writes a Gate.
Old tables lacking resolved identities are explicitly ineligible, never repaired.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np
import pandas as pd

VERSION = "stage-0.5-d1-local-v1"
LANES = ("1", "2", "3", "4", "5")
REQUIRED = {
    "run_id", "scenario_id", "vehicle_id", "incarnation_id", "leader_id",
    "leader_incarnation_id", "time_s", "lane_id", "y_m", "measurement_status",
    "reliable_following_eligible", "ttc_valid", "ttc_s",
}


class MeasurementContractError(ValueError):
    pass


def _window(window):
    low, high = map(float, window)
    if not np.isfinite([low, high]).all() or low >= high:
        raise MeasurementContractError("invalid_evaluation_window")
    return low, high


def inside_region(d, region=(150., 350.)):
    return d.lane_id.astype(str).isin(LANES) & d.y_m.ge(region[0]) & d.y_m.lt(region[1])


def _known_identity(s):
    return s.notna() & ~s.astype(str).isin(["", "None", "nan", "<NA>"])


def local_d1_measurement(frame, window, *, region=(150., 350.), strict=False):
    """Full-context native P2, onset attribution and reliable 100 ms local edges.

    ``formal_equivalence_accepted`` remains false: rule implementation is distinct
    from scientific validation. No leader/incarnation is inferred from vehicle ID.
    """
    from .stage_0_5_sumo import (
        FORMAL_OBSERVATION_STEP_S, FORMAL_TTC_THRESHOLD_S, FORMAL_MINIMUM_DURATION_S,
    )
    low, high = _window(window)
    missing = sorted(REQUIRED - set(frame))
    if missing:
        if strict:
            raise MeasurementContractError("missing_identity_or_measurement_fields:" + ",".join(missing))
        return dict(version=VERSION, eligibility="degraded_missing_fields", missing_fields=missing,
                    window_s=[low, high], events=None, onset_events=None,
                    local_evaluable_s=None, rate_per_evaluable_vehicle_hour=None,
                    formal_equivalence_accepted=False)
    dt = float(FORMAL_OBSERVATION_STEP_S)
    keys = ["run_id", "scenario_id", "vehicle_id", "incarnation_id"]
    d = frame.sort_values(keys + ["time_s"], kind="stable").reset_index(drop=True)
    for field in ["time_s", "y_m"]:
        if not np.isfinite(d[field].to_numpy(float)).all():
            raise MeasurementContractError("invalid_clock_or_position:" + field)
    if not np.allclose(d.time_s.to_numpy(float) / dt, np.round(d.time_s.to_numpy(float) / dt), atol=1e-7, rtol=0):
        raise MeasurementContractError("clock_not_on_100ms_grid")
    if d.duplicated(keys + ["time_s"]).any():
        raise MeasurementContractError("duplicate_identity_clock")
    for field in keys:
        if not _known_identity(d[field]).all():
            raise MeasurementContractError("missing_follower_identity:" + field)
    for field in ["reliable_following_eligible", "ttc_valid"]:
        if not d[field].map(lambda x: isinstance(x, (bool, np.bool_))).all():
            raise MeasurementContractError("unknown_boolean:" + field)
    if not d.measurement_status.isin(["valid", "not_applicable", "missing", "invalid"]).all():
        raise MeasurementContractError("unknown_measurement_status")
    reliable = d.reliable_following_eligible
    resolved = _known_identity(d.leader_incarnation_id) & _known_identity(d.leader_id)
    if (reliable & ~resolved).any():
        raise MeasurementContractError("reliable_without_resolved_leader")
    p = d.shift()
    same_follower = pd.Series(True, index=d.index)
    for k in keys:
        same_follower &= d[k].eq(p[k])
    adjacency = same_follower & resolved & resolved.shift(fill_value=False)
    adjacency &= d.leader_incarnation_id.eq(p.leader_incarnation_id) & d.leader_id.eq(p.leader_id)
    adjacency &= d.time_s.sub(p.time_s).sub(dt).abs().le(1e-9)
    if "native_lane_id" in d:
        # No physical path continuity is asserted across native lanes/edges.
        adjacency &= d.native_lane_id.notna() & d.native_lane_id.eq(p.native_lane_id)
    for field in ["identity_break", "observation_gap"]:
        if field in d:
            if not d[field].map(lambda x: isinstance(x, (bool, np.bool_))).all():
                raise MeasurementContractError("unknown_boolean:" + field)
            # Preserve the native adapter's existing both-end qualification.
            adjacency &= d[field].eq(False) & p[field].eq(False)
    for field in ["observation_index", "frame_id", "original_row_number"]:
        if field in d:
            if not np.isfinite(d[field].to_numpy(float)).all():
                raise MeasurementContractError("invalid_clock:" + field)
            adjacency &= d[field].sub(p[field]).eq(1)
    if "global_time_ms" in d:
        if not np.isfinite(d.global_time_ms.to_numpy(float)).all():
            raise MeasurementContractError("invalid_clock:global_time_ms")
        adjacency &= d.global_time_ms.sub(p.global_time_ms).sub(100).abs().le(1e-6)
    quality = d.measurement_status.isin(["valid", "not_applicable"])
    evaluable = adjacency & reliable & reliable.shift(fill_value=False) & quality & quality.shift(fill_value=False)
    inside = inside_region(d, region)
    full_window = p.time_s.ge(low - 1e-9) & d.time_s.le(high + 1e-9)
    local_edges = evaluable & inside & inside.shift(fill_value=False) & full_window
    risk = reliable & d.ttc_valid & d.measurement_status.eq("valid") & d.ttc_s.gt(0) & d.ttc_s.lt(FORMAL_TTC_THRESHOLD_S)
    segment = (risk & ~(risk.shift(fill_value=False) & adjacency)).cumsum()
    events, incomplete = [], []
    left_continuing = 0
    for _, g in d.loc[risk].groupby(segment[risk], sort=False):
        onset, end = float(g.time_s.iloc[0]), float(g.time_s.iloc[-1])
        first_idx, last_idx = int(g.index[0]), int(g.index[-1])
        main = bool(inside.iloc[first_idx] and low <= onset < high)
        if onset < low <= end and inside.loc[g.index[g.time_s.ge(low)]].any():
            left_continuing += 1
        if end - onset < FORMAL_MINIMUM_DURATION_S - 1e-9:
            if main:
                tail = last_idx == len(d) - 1 or not same_follower.iloc[last_idx + 1]
                unavailable_next = tail or not adjacency.iloc[last_idx + 1] or not quality.iloc[last_idx + 1]
                incomplete.append(dict(onset_s=onset, last_s=end,
                                       status="right_censored_unconfirmed" if unavailable_next else "observed_short_risk"))
            continue
        confirmation = g.loc[g.time_s.sub(onset).ge(FORMAL_MINIMUM_DURATION_S - 1e-9)].iloc[0]
        confirm = float(confirmation.time_s)
        token = f"{g.run_id.iloc[0]}|{g.incarnation_id.iloc[0]}|{g.leader_incarnation_id.iloc[0]}|{onset:.1f}"
        events.append(dict(event_id="d1_" + hashlib.sha256(token.encode()).hexdigest()[:20],
                           leader_id=str(g.leader_id.iloc[0]),
                           member_sha256=hashlib.sha256(g[["vehicle_id", "leader_id", "time_s"]].to_csv(index=False, lineterminator="\n").encode()).hexdigest(),
                           vehicle_id=str(g.vehicle_id.iloc[0]), onset_s=onset, confirm_s=confirm, end_s=end,
                           onset_inside=bool(inside.iloc[first_idx]), confirmation_inside=bool(inside.iloc[int(confirmation.name)]),
                           through_confirmation_inside=bool(inside.loc[g.index[g.time_s.le(confirm + 1e-9)]].all()),
                           through_end_inside=bool(inside.loc[g.index].all()), onset_in_window=bool(low <= onset < high),
                           confirmation_in_window=bool(low <= confirm < high), confirmation_after_window=bool(main and confirm >= high),
                           members=len(g), message_earliest_s=confirm))
    onsets = [e for e in events if e["onset_in_window"]]
    n = sum(e["onset_inside"] for e in onsets)
    exposure = int(local_edges.sum()) * dt
    point_mask = inside & d.time_s.ge(low) & d.time_s.lt(high)
    return dict(version=VERSION, eligibility="D1_contract_implemented", window_s=[low, high],
                region_m=list(region), local_evaluable_s=exposure, local_links=int(local_edges.sum()),
                reliable_local_s=int((adjacency & reliable & reliable.shift(fill_value=False) & inside & inside.shift(fill_value=False) & full_window).sum()) * dt,
                onset_events=n, confirmation_position_events=sum(e["confirmation_inside"] for e in onsets),
                through_confirmation_events=sum(e["through_confirmation_inside"] for e in onsets),
                confirmation_time_sensitivity_events=sum(e["confirmation_inside"] and e["confirmation_in_window"] for e in events),
                left_continuing_risk_segments=left_continuing,
                confirmation_after_window=sum(e["confirmation_after_window"] for e in onsets),
                right_censored_unconfirmed=sum(e["status"] == "right_censored_unconfirmed" for e in incomplete),
                incomplete_candidates=incomplete, events=events,
                rate_status="evaluable_zero_events" if exposure and n == 0 else ("evaluable" if exposure else "zero_exposure_not_evaluable"),
                rate_per_evaluable_vehicle_hour=3600 * n / exposure if exposure else None,
                legacy_point_evaluable_s=int((point_mask & quality).sum()) * dt,
                no_reliable_leader_point_s=int((point_mask & quality & ~reliable).sum()) * dt,
                unavailable_point_counts=d.loc[point_mask, "measurement_status"].value_counts().to_dict(),
                formal_equivalence_accepted=False, scientific_claim_eligible=False)


def offset100_cloud(frame, window, *, block_s=30.):
    low, high = _window(window)
    if not np.isfinite(block_s) or block_s <= 0:
        raise MeasurementContractError("invalid_block_length")
    d = frame.loc[inside_region(frame) & frame.time_s.ge(low) & frame.time_s.lt(high)].copy()
    d["_t"] = np.floor((d.time_s - low) / block_s + 1e-9).astype(int)
    d["_y"] = np.floor((d.y_m - 150) / 100).astype(int)
    groups = {(int(t), int(y)): g for (t, y), g in d.groupby(["_t", "_y"], sort=True)}
    rows = []
    for t in range(math.ceil((high - low) / block_s)):
        duration = min(block_s, high - low - t * block_s)
        for y in [0, 1]:
            g = groups.get((t, y), d.iloc[:0])
            n = len(g)
            rows.append(dict(t_block=t, y_block=y, block_start_s=low + t * block_s,
                             block_end_s=low + t * block_s + duration, duration_s=duration,
                             y_start_m=150 + 100 * y, y_end_m=250 + 100 * y,
                             width_m=100., lane_km=.5, states=n,
                             support_status="observed" if n >= 10 else "insufficient_state_support",
                             density_veh_km_lane=n * .1 / duration / .5,
                             speed_mean_mps=float(g.speed_mps.mean()) if n else None,
                             flow_veh_h_lane=n * .1 / duration / .5 * float(g.speed_mps.mean()) * 3.6 if n else None,
                             low_speed_share=float(g.speed_mps.lt(5).mean()) if n else None,
                             closing_speed_mean_mps=float(g.closing_speed_mps.mean()) if n and "closing_speed_mps" in g else None))
    return pd.DataFrame(rows)


def time_gap_values(gap, follower_speed, closing_speed, leader_length=None):
    """Explicit geometry; v<=0 undefined, no hidden epsilon/clamping.

    g/closing here is labelled closing_time_proxy, never the formal TTC interface.
    """
    gap, speed, closing = np.broadcast_arrays(np.asarray(gap, float), np.asarray(follower_speed, float), np.asarray(closing_speed, float))
    valid_gap = np.isfinite(gap) & (gap > 0)
    net = np.full(gap.shape, np.nan)
    np.divide(gap, speed, out=net, where=valid_gap & np.isfinite(speed) & (speed > 0))
    closure = np.full(gap.shape, np.nan)
    np.divide(gap, closing, out=closure, where=valid_gap & np.isfinite(closing) & (closing > 0))
    bumper = np.full(gap.shape, np.nan)
    if leader_length is not None:
        length = np.broadcast_to(np.asarray(leader_length, float), gap.shape)
        np.divide(gap + length, speed, out=bumper,
                  where=valid_gap & np.isfinite(length) & (length > 0) & np.isfinite(speed) & (speed > 0))
    return {"net_time_gap_s": net, "front_bumper_time_headway_s": bumper,
            "closing_time_proxy_s": closure}
