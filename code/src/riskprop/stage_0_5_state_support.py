"""Conditional traffic-state support for Stage 0.5 (AAD-0.5-STATE-SUPPORT).

Purpose
-------
Stage 0.5 cannot validate SUMO against US-101 by strict equivalence.  It can,
however, test whether a *declared* conditional scenario reproduces a *declared*
local traffic-state domain that the real reference observations actually
support, and it can state the limits of that domain.  This module implements

  (A) a read-only reconstruction of the real following relation and of the real
      state-support domain from the already sealed Stage 0.2 canonical states of
      the two approved calibration windows;
  (B) a declared conditional SUMO construction whose two axes are the boundary
      supply (a downstream capacity restriction) and the car-following time
      headway, with the headway taken from (A) rather than tuned;
  (C) membership tests of a simulated local state in the real state-support
      domain, including a *data-derived* cross-window baseline so that the
      criterion is not an arbitrary threshold.

Boundaries
----------
* No identity, clock, quality or P2 semantic owned by Stage 0.2 is redefined.
* The module does not run SUMO.  It does not write Gate state.
* Every quantity is tagged Observation / Derived / Hypothesis / Unidentifiable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "stage-0.5-state-support-v1"

# --------------------------------------------------------------------------
# inherited, not chosen here
# --------------------------------------------------------------------------
CALIBRATION_WINDOWS: dict[str, tuple[float, float]] = {
    "us101__0750_0805": (120.0, 840.0),
    "us101__0805_0820": (180.0, 840.0),
}
#: pre-designated temporal validation window (researcher-approved split,
#: 2026-10-18 decision); reading it is only permitted after the plan is frozen.
VALIDATION_WINDOW = "us101__0820_0835"
VALIDATION_WINDOW_SPAN: tuple[float, float] = (300.0, 1020.0)
APPROVED_SPANS: dict[str, tuple[float, float]] = {
    **CALIBRATION_WINDOWS,
    VALIDATION_WINDOW: VALIDATION_WINDOW_SPAN,
}
LOCKED_HOLDOUT_MARKERS = ("lankershim", "i80", "peachtree", "spmd")

REGION_START_M = 150.0
REGION_END_M = 350.0
MAINLINE_LANES = ("1", "2", "3", "4", "5")
LOW_SPEED_MPS = 5.0                 # inherited descriptive threshold
BLOCK_S = 30.0                      # inherited evaluation block
BLOCK_Y_M = 100.0                   # real block width used by the reconstruction
MIN_GAP_M = 2.5                     # frozen SUMO Krauss minGap
VEHICLE_LENGTH_M = 4.4196           # frozen SUMO passenger length
FREE_SPEED_MPS = 27.78              # frozen SUMO maxSpeed
GAP_FIT_CAP_M = 80.0                # analysis window of the real following relation

STATE_COLUMNS = (
    "window_id", "trajectory_id", "time_s", "y_m", "speed_mps", "lane_id",
    "net_gap_m", "closing_speed_mps", "measurement_status", "leader_matched",
)


class StateSupportError(ValueError):
    """Fail-closed error for schema, isolation or plan violations."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_not_holdout(window_id: str) -> None:
    lowered = window_id.lower()
    if any(marker in lowered for marker in LOCKED_HOLDOUT_MARKERS):
        raise StateSupportError(f"locked_holdout_refused:{window_id}")


# --------------------------------------------------------------------------
# (A) real reference: loading and the following relation
# --------------------------------------------------------------------------
def load_real_states(path: str | Path, window_id: str) -> pd.DataFrame:
    """Load one approved real window of canonical Stage 0.2 states (read-only)."""
    _assert_not_holdout(window_id)
    frame = pd.read_parquet(path, columns=list(STATE_COLUMNS))
    if frame.empty:
        raise StateSupportError("empty_state_table")
    if frame.window_id.nunique() != 1:
        raise StateSupportError("mixed_windows")
    if not np.isfinite(frame[["time_s", "y_m", "speed_mps"]].to_numpy(float)).all():
        raise StateSupportError("nonfinite_state")
    frame = frame.copy()
    frame["lane_id"] = frame.lane_id.astype(str)
    span = APPROVED_SPANS.get(window_id)
    if span is not None:
        frame = frame[frame.time_s.ge(span[0]) & frame.time_s.lt(span[1])]
        if frame.empty:
            raise StateSupportError("empty_window_after_span_filter")
    return frame.sort_values(["trajectory_id", "time_s"], kind="stable").reset_index(drop=True)


def local_region_mask(states: pd.DataFrame) -> pd.Series:
    lane = pd.to_numeric(states.lane_id, errors="raise")
    y = pd.to_numeric(states.y_m, errors="raise")
    if not np.isfinite(lane).all() or not np.isfinite(y).all():
        raise StateSupportError("invalid_spatial_schema")
    return lane.isin([1, 2, 3, 4, 5]) & y.ge(REGION_START_M) & y.lt(REGION_END_M)


def local_summary(states: pd.DataFrame) -> dict[str, object]:
    """Observation-level descriptors of one real local window."""
    mask = local_region_mask(states)
    subset = states[mask]
    if subset.empty:
        raise StateSupportError("empty_local_region")
    lane_km = (REGION_END_M - REGION_START_M) / 1000.0 * len(MAINLINE_LANES)
    window_id = str(states.window_id.iloc[0])
    approved_span = next((span for key, span in APPROVED_SPANS.items() if key.endswith(window_id)), None)
    span_s = (float(approved_span[1] - approved_span[0]) if approved_span is not None
              else float(subset.time_s.max() - subset.time_s.min()))
    vehicle_s = float(len(subset)) * 0.1
    density = vehicle_s / span_s / lane_km
    speed = float(subset.speed_mps.mean())
    return {
        "status": "Observation",
        "region_m": [REGION_START_M, REGION_END_M],
        "lanes": list(MAINLINE_LANES),
        "span_s": span_s,
        "states": int(len(subset)),
        "local_vehicle_s": vehicle_s,
        "density_veh_km_lane": density,
        "speed_mean_mps": speed,
        "speed_sd_mps": float(subset.speed_mps.std(ddof=1)),
        "flow_veh_h_lane_consistency": density * speed * 3.6,
        "low_speed_share": float((subset.speed_mps < LOW_SPEED_MPS).mean()),
        "closing_speed_mean_mps": float(subset.closing_speed_mps.mean()),
        "closing_speed_negative_share": float((subset.closing_speed_mps < 0).mean()),
        "net_gap_mean_m": float(subset.net_gap_m.mean()),
        "net_gap_median_m": float(subset.net_gap_m.median()),
    }


def following_relation(states: pd.DataFrame, *, gap_cap_m: float = GAP_FIT_CAP_M,
                       min_gap_m: float = MIN_GAP_M) -> dict[str, object]:
    """Real net-gap / speed relation and the implied effective time headway.

    ``tau_eff`` is the ratio estimator of the Krauss/Newell linear equilibrium
    ``net_gap = minGap + tau * v`` over the *whole* following population of the
    local region (not a stratified subsample)::

        tau_eff = (sum(net_gap) - n * minGap) / sum(v)

    The OLS fit of the speed-binned means is reported separately because
    ``(tau, minGap)`` are only jointly identifiable from this relation; neither
    estimator is presented as an identified physical parameter.
    """
    mask = local_region_mask(states)
    subset = states[mask]
    subset = subset[(subset.net_gap_m > 0) & (subset.net_gap_m <= gap_cap_m)]
    if subset.empty:
        raise StateSupportError("empty_following_sample")
    n = len(subset)
    tau_eff = float((subset.net_gap_m.sum() - n * min_gap_m) / subset.speed_mps.sum())
    binned = subset.copy()
    binned["speed_bin"] = pd.cut(binned.speed_mps, [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 25, 30])
    grouped = binned.groupby("speed_bin", observed=True).agg(
        n=("net_gap_m", "size"), gap=("net_gap_m", "mean"), v=("speed_mps", "mean"))
    grouped = grouped[grouped.n > 50]
    slope, intercept = np.polyfit(grouped.v.to_numpy(float), grouped.gap.to_numpy(float), 1)
    per_vehicle = subset.groupby("trajectory_id").agg(
        n=("net_gap_m", "size"), gap=("net_gap_m", "mean"), v=("speed_mps", "mean"))
    per_vehicle = per_vehicle[per_vehicle.n >= 50]
    tau_vehicle = ((per_vehicle.gap - min_gap_m) / per_vehicle.v).to_numpy(float)
    quantiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    return {
        "status": "Derived",
        "sample_states": int(n),
        "gap_cap_m": float(gap_cap_m),
        "min_gap_m": float(min_gap_m),
        "tau_eff_ratio_s": tau_eff,
        "ols_binned_slope_s": float(slope),
        "ols_binned_intercept_m": float(intercept),
        "ols_binned_bins": int(len(grouped)),
        "analytic_lane_capacity_ratio_veh_h": 3600.0 / (
            tau_eff + (VEHICLE_LENGTH_M + min_gap_m) / FREE_SPEED_MPS),
        "analytic_lane_capacity_ols_veh_h": 3600.0 * FREE_SPEED_MPS / (
            FREE_SPEED_MPS * slope + VEHICLE_LENGTH_M + intercept),
        "vehicles": int(len(per_vehicle)),
        "vehicle_tau_eff_mean_s": float(np.mean(tau_vehicle)),
        "vehicle_tau_eff_quantiles_s": [float(x) for x in np.quantile(tau_vehicle, quantiles)],
        "vehicle_tau_eff_quantile_levels": quantiles,
        "identifiability_note": (
            "only the pair (tau, minGap) is jointly identifiable from this relation; "
            "tau_eff is a population-equivalent headway, not an identified driver parameter"
        ),
        "not_a_science_tolerance": True,
    }


# --------------------------------------------------------------------------
# (A2) the real state-support domain (space-time block cloud)
# --------------------------------------------------------------------------
def block_cloud(states: pd.DataFrame, *, block_s: float = BLOCK_S,
                y_step_m: float = BLOCK_Y_M) -> pd.DataFrame:
    """Local 30 s x 100 m block speed/density cloud of one real window.

    The blocks are non-overlapping in time and space; each block must contain
    at least two 0.1 s rows per lane to be reported, which only excludes empty
    space-time cells.
    """
    subset = local_region_mask(states)
    region_states = states[subset].copy()
    origin = float(region_states.time_s.min())
    region_states["t_block"] = np.floor((region_states.time_s - origin) / block_s).astype(int)
    region_states["y_block"] = np.floor(region_states.y_m / y_step_m).astype(int)
    lane_km = y_step_m / 1000.0 * len(MAINLINE_LANES)
    rows: list[dict[str, object]] = []
    for (t_block, y_block), part in region_states.groupby(["t_block", "y_block"], sort=True):
        if len(part) < 2 * len(MAINLINE_LANES):
            continue
        vehicle_s = len(part) * 0.1
        rows.append({
            "t_block": int(t_block),
            "y_block": int(y_block),
            "block_start_s": float(origin + t_block * block_s),
            "y_start_m": float(y_block * y_step_m),
            "states": int(len(part)),
            "speed_mean_mps": float(part.speed_mps.mean()),
            "density_veh_km_lane": vehicle_s / block_s / lane_km,
            "flow_veh_h_lane": float(part.speed_mps.mean()) * vehicle_s / block_s / lane_km * 3.6,
            "low_speed_share": float((part.speed_mps < LOW_SPEED_MPS).mean()),
            "closing_speed_mean_mps": float(part.closing_speed_mps.mean()),
        })
    return pd.DataFrame(rows)


def support_envelope(cloud: pd.DataFrame, *, band_veh_km_lane: float = 7.5,
                     lower: float = 0.025, upper: float = 0.975) -> dict[str, object]:
    """k-band envelope of the observed block cloud.

    A simulated local state is *inside the domain* when its density is inside the
    observed density range and its speed lies between the observed low and high
    quantiles of the real blocks whose density is within one half-band.  The
    quantile levels and the band width are declared once, here, and are used
    identically for every arm, every seed and the temporal validation window.
    """
    if cloud.empty:
        raise StateSupportError("empty_block_cloud")
    density = cloud.density_veh_km_lane.to_numpy(float)
    speed = cloud.speed_mean_mps.to_numpy(float)
    order = np.argsort(density)
    density_sorted = density[order]
    speed_sorted = speed[order]
    centres: list[float] = []
    lows: list[float] = []
    highs: list[float] = []
    for centre in np.unique(np.round(density_sorted / band_veh_km_lane) * band_veh_km_lane):
        select = np.abs(density_sorted - centre) <= band_veh_km_lane
        if int(select.sum()) < 5:
            continue
        centres.append(float(centre))
        lows.append(float(np.quantile(speed_sorted[select], lower)))
        highs.append(float(np.quantile(speed_sorted[select], upper)))
    if not centres:
        raise StateSupportError("empty_envelope_bands")
    return {
        "status": "Observation",
        "band_veh_km_lane": float(band_veh_km_lane),
        "quantiles": [float(lower), float(upper)],
        "density_min_veh_km_lane": float(density_sorted.min()),
        "density_max_veh_km_lane": float(density_sorted.max()),
        "band_centres_veh_km_lane": centres,
        "band_speed_lower_mps": lows,
        "band_speed_upper_mps": highs,
        "block_count": int(len(cloud)),
    }


def envelope_membership(density: float, speed: float, envelope: dict[str, object]) -> dict[str, object]:
    """Membership of one (density, speed) point in a k-band envelope."""
    low_k = float(envelope["density_min_veh_km_lane"])
    high_k = float(envelope["density_max_veh_km_lane"])
    if not (low_k <= density <= high_k):
        return {"inside": False, "reason": "density_outside_observed_range"}
    lower = float(np.interp(density, envelope["band_centres_veh_km_lane"],
                            envelope["band_speed_lower_mps"]))
    upper = float(np.interp(density, envelope["band_centres_veh_km_lane"],
                            envelope["band_speed_upper_mps"]))
    return {
        "inside": bool(lower <= speed <= upper),
        "speed_lower_mps": lower,
        "speed_upper_mps": upper,
        "reason": "inside" if lower <= speed <= upper else "speed_outside_observed_band",
    }


def envelope_coverage(cloud: pd.DataFrame, envelope: dict[str, object]) -> float:
    """Fraction of block-cloud points that lie inside the envelope."""
    if cloud.empty:
        return float("nan")
    inside = [envelope_membership(float(row.density_veh_km_lane), float(row.speed_mean_mps),
                                  envelope)["inside"] for row in cloud.itertuples()]
    return float(np.mean(inside))


def closing_envelope(cloud: pd.DataFrame, *, band_veh_km_lane: float = 7.5,
                     lower: float = 0.025, upper: float = 0.975) -> dict[str, object]:
    """Same k-band construction applied to the observed block mean closing speed.

    This is the mechanism-relevant counterpart of the speed envelope: it states,
    from the real blocks themselves, which net relative-motion levels are observed
    at each density.  Nothing is chosen here beyond the band width and the
    quantile levels already declared for the speed envelope.
    """
    if cloud.empty:
        raise StateSupportError("empty_block_cloud")
    density = cloud.density_veh_km_lane.to_numpy(float)
    closing = cloud.closing_speed_mean_mps.to_numpy(float)
    order = np.argsort(density)
    density_sorted = density[order]
    closing_sorted = closing[order]
    centres: list[float] = []
    lows: list[float] = []
    highs: list[float] = []
    for centre in np.unique(np.round(density_sorted / band_veh_km_lane) * band_veh_km_lane):
        select = np.abs(density_sorted - centre) <= band_veh_km_lane
        if int(select.sum()) < 5:
            continue
        centres.append(float(centre))
        lows.append(float(np.quantile(closing_sorted[select], lower)))
        highs.append(float(np.quantile(closing_sorted[select], upper)))
    if not centres:
        raise StateSupportError("empty_closing_envelope_bands")
    return {"status": "Observation", "band_veh_km_lane": float(band_veh_km_lane),
            "quantiles": [float(lower), float(upper)],
            "band_centres_veh_km_lane": centres,
            "band_closing_lower_mps": lows, "band_closing_upper_mps": highs,
            "block_count": int(len(cloud))}


def closing_membership(density: float, closing: float, envelope: dict[str, object]) -> dict[str, object]:
    centres = envelope["band_centres_veh_km_lane"]
    if not (centres[0] - 2 * envelope["band_veh_km_lane"] <= density
            <= centres[-1] + 2 * envelope["band_veh_km_lane"]):
        return {"inside": False, "reason": "density_outside_observed_closing_bands"}
    lower = float(np.interp(density, centres, envelope["band_closing_lower_mps"]))
    upper = float(np.interp(density, centres, envelope["band_closing_upper_mps"]))
    return {"inside": bool(lower <= closing <= upper), "closing_lower_mps": lower,
            "closing_upper_mps": upper,
            "reason": "inside" if lower <= closing <= upper else "closing_outside_observed_band"}


# --------------------------------------------------------------------------
# (B) declared conditional construction
# --------------------------------------------------------------------------
#: Declared boundary-supply axis.  The downstream boundary of the observed
#: geometry is represented by a capacity restriction expressed as the free
#: speed of the downstream edge; the value 27.78 m/s reproduces the observed
#: geometry without restriction.  Every arm uses the *same* declared values, so
#: the axis is not confounded with the behaviour axis; the analytic capacity
#: realised by each (arm, level) pair is reported as a derived quantity.
DECLARED_SUPPLY_FREE_SPEED_MPS: tuple[float, ...] = (27.78, 15.0, 12.0, 10.0, 8.0)

#: Declared car-following arms.  ``B_frozen`` is the sealed Stage 0.5 baseline;
#: ``B_mean`` and ``B_het`` use the headway derived in (A) from the real
#: following population, never from a simulated outcome.
DECLARED_BEHAVIOURS: dict[str, dict[str, object]] = {
    "B_frozen": {"tau_mode": "frozen", "sigma": 0.5, "status": "sealed Stage 0.5 baseline"},
    "B_mean": {"tau_mode": "mean", "sigma": 0.5, "status": "declared conditional behaviour"},
    "B_het": {"tau_mode": "heterogeneous", "sigma": 0.5, "status": "declared conditional behaviour"},
}

#: Heterogeneity discretisation: the per-vehicle effective headway distribution
#: of (A) is approximated by equal-probability classes at these quantiles.
HETEROGENEITY_QUANTILES: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9)

FIXED_VTYPE_FIELDS = dict(
    maxSpeed=FREE_SPEED_MPS, speedFactor=1.0, speedDev=0.0, carFollowModel="Krauss",
    minGap=MIN_GAP_M, accel=2.6, decel=4.5, apparentDecel=4.5, emergencyDecel=9.0,
    actionStepLength=0.1, sigmaStep=1.0, laneChangeModel="LC2013",
)


def declared_behaviour_vtypes(name: str, relation_pooled: dict[str, object]) -> list[dict[str, object]]:
    """vType list for one declared behaviour arm."""
    if name not in DECLARED_BEHAVIOURS:
        raise StateSupportError(f"unknown_behaviour:{name}")
    mode = DECLARED_BEHAVIOURS[name]["tau_mode"]
    sigma = float(DECLARED_BEHAVIOURS[name]["sigma"])
    if mode == "frozen":
        taus, shares = [1.0], [1.0]
    elif mode == "mean":
        taus, shares = [float(relation_pooled["tau_eff_ratio_s"])], [1.0]
    elif mode == "heterogeneous":
        levels = list(HETEROGENEITY_QUANTILES)
        values = np.interp(levels, relation_pooled["vehicle_tau_eff_quantile_levels"],
                           relation_pooled["vehicle_tau_eff_quantiles_s"])
        taus = [float(x) for x in values]
        shares = [1.0 / len(taus)] * len(taus)
    else:  # pragma: no cover - guarded by the table above
        raise StateSupportError(f"unsupported_tau_mode:{mode}")
    length_map = {"passenger": VEHICLE_LENGTH_M, "truck": 10.009694845360826, "motorcycle": 2.4384}
    types: list[dict[str, object]] = []
    for class_index, (tau, share) in enumerate(zip(taus, shares)):
        for kind, length in length_map.items():
            types.append({
                "id": f"{name}_c{class_index}_{kind}",
                "tau": tau,
                "share": share * {"passenger": 1.0, "truck": 0.0, "motorcycle": 0.0}[kind],
                "length_m": length,
                "sigma": sigma,
                "vClass": "passenger" if kind == "passenger" else ("truck" if kind == "truck" else "motorcycle"),
                "class_index": class_index,
                "kind": kind,
            })
    return [entry for entry in types if entry["id"].endswith("passenger")]


def supply_capacity_veh_h(free_speed_mps: float, tau_s: float, *, lanes: int = 5) -> float:
    """Analytic Krauss lane capacity of the declared downstream restriction."""
    per_lane = 3600.0 * free_speed_mps / (
        free_speed_mps * tau_s + VEHICLE_LENGTH_M + MIN_GAP_M)
    return float(per_lane * lanes)


#: Declared structural supply variants, expressed at matched analytic capacity.
#: ``speed_limit`` restricts the free speed on a five-lane downstream edge;
#: ``lane_drop`` removes a lane at the observed diverge and keeps the free speed.
#: The lane drop is the canonical wave-generating bottleneck, the speed limit is a
#: smooth restriction; the pair separates "how much capacity" from "how the
#: capacity is realised".
DECLARED_SUPPLY_VARIANTS: tuple[dict[str, object], ...] = (
    {"variant_id": "speed_limit_5lane", "kind": "speed_limit", "downstream_lanes": 5},
    {"variant_id": "lane_drop_4lane", "kind": "lane_drop", "downstream_lanes": 4},
)


def observed_geometry_spec(downstream_free_speed_mps: float,
                           downstream_lanes: int = 5) -> dict[str, object]:
    """The observed-geometry candidate with a declared downstream restriction.

    ``downstream_lanes`` below 5 expresses the capacity restriction as a discrete
    lane drop at the observed diverge (399.22 m) rather than as a speed limit.
    Both encodings are declared supply variants of the same boundary condition;
    the realised analytic capacity of each variant is reported.
    """
    spec = {
        "schema_version": "stage_0_5.sumo-engineering.v2.network-candidate.v1",
        "network_id": f"observed_geometry_supply_{str(downstream_free_speed_mps).replace('.', 'p')}_l{int(downstream_lanes)}",
        "classification": "conditional_observed_geometry_candidate",
        "claim": "observed_geometry_from_ngsim_us101_lane_support_not_full_facility_replication",
        "design_basis": [
            "five mainline lanes, a on-ramp merge at 187.58 m and an off-ramp diverge at 399.22 m",
            "the downstream edge carries the declared conditional capacity restriction",
        ],
        "nodes": [
            {"id": "hwy_w", "x": 0.0, "y": 0.0},
            {"id": "hwy_m1", "x": 187.58, "y": 0.0},
            {"id": "hwy_m2", "x": 399.22, "y": 0.0},
            {"id": "hwy_e", "x": 669.18, "y": 0.0},
            {"id": "hwy_on", "x": 60.0, "y": -160.0},
            {"id": "hwy_off", "x": 560.0, "y": -160.0},
        ],
        "edges": [
            {"id": "main_0", "from": "hwy_w", "to": "hwy_m1", "lanes": 5, "speed_mps": FREE_SPEED_MPS, "priority": 2},
            {"id": "main_1", "from": "hwy_m1", "to": "hwy_m2", "lanes": 6, "speed_mps": FREE_SPEED_MPS, "priority": 2},
            {"id": "main_2", "from": "hwy_m2", "to": "hwy_e", "lanes": int(downstream_lanes),
             "speed_mps": float(downstream_free_speed_mps), "priority": 2},
            {"id": "onramp", "from": "hwy_on", "to": "hwy_m1", "lanes": 1, "speed_mps": 13.89, "priority": 1},
            {"id": "offramp", "from": "hwy_m2", "to": "hwy_off", "lanes": 1, "speed_mps": 13.89, "priority": 1},
        ],
        "routes": {
            "through": ["main_0", "main_1", "main_2"],
            "entering": ["onramp", "main_1", "main_2"],
            "exiting": ["main_0", "main_1", "offramp"],
        },
        "lane_change_enabled": True,
    }
    return spec


# --------------------------------------------------------------------------
# (B2) demand, network, execution
# --------------------------------------------------------------------------
#: Observed conditional demand of the two calibration windows, inherited from
#: the Stage 0.5 scene reconstruction (trajectory crossings and official counts).
CONDITIONS: dict[str, dict[str, object]] = {
    "us101__0750_0805": {
        "window_s": [120.0, 840.0],
        "mainline_flow_veh_h": 8345.0,
        "onramp_flow_veh_h": 516.0,
        "offramp_flow_veh_h": 355.0,
        "real_target": {"speed_mps": 10.506118382234925, "density_veh_km_lane": 43.54361111111111},
    },
    "us101__0805_0820": {
        "window_s": [180.0, 840.0],
        "mainline_flow_veh_h": 7227.272727272728,
        "onramp_flow_veh_h": 490.0,
        "offramp_flow_veh_h": 360.0,
        "real_target": {"speed_mps": 7.915276152134783, "density_veh_km_lane": 50.50545454545454},
    },
}

DECLARED_DURATION_S = 420.0
DECLARED_EVALUATION_WINDOW_S = (300.0, 420.0)
DECLARED_INTERNAL_STEP_S = 0.05
DECLARED_FCD_PERIOD_S = 0.1

#: The declared initial condition of every arm is the *observed* real local state
#: at the start of the approved window.  The experiment therefore asks whether the
#: observed state is preserved by the simulated dynamics under the declared
#: boundary supply, not whether the simulator can invent it from an empty network.
INITIAL_STATE_CLOCK_S: dict[str, float] = {
    "us101__0750_0805": 120.0,
    "us101__0805_0820": 180.0,
    VALIDATION_WINDOW: 300.0,
}


def initial_state_records(states: pd.DataFrame, condition: str, *, clock_s: float | None = None,
                          minimum_spacing_m: float = 1.0,
                          edge_lengths: dict[str, float] | None = None) -> dict[str, object]:
    """Observed real initial state at one instant, mapped onto the built network.

    Positions and speeds are taken from the sealed canonical states; the overlap
    filter only removes vehicles that cannot be represented in the same SUMO lane
    and reports every dropped vehicle.
    """
    from .stage_0_5_scene_reconstruction import real_lane_to_sumo, scale_position
    instant = INITIAL_STATE_CLOCK_S[condition] if clock_s is None else float(clock_s)
    frame = states[(states.time_s - instant).abs() < 1e-9]
    if frame.empty:
        observed = np.sort(states.time_s.unique())
        nearest = float(observed[np.argmin(np.abs(observed - instant))])
        frame = states[(states.time_s - nearest).abs() < 1e-9]
        instant = nearest
    offramp_trajectories = set(states.loc[states.lane_id.astype(str) == "8", "trajectory_id"].astype(str))
    waterfall = frame.sort_values(["lane_id", "y_m"], ascending=[True, False])
    records: list[dict[str, object]] = []
    dropped: list[dict[str, object]] = []
    occupancy: dict[tuple[str, int], float] = {}
    for row in waterfall.itertuples():
        mapped = real_lane_to_sumo(str(row.lane_id), float(row.y_m))
        if mapped is None:
            dropped.append({"trajectory_id": str(row.trajectory_id), "reason": "outside_observed_geometry"})
            continue
        edge, lane, position = mapped
        position = scale_position(edge, position, edge_lengths or {})
        key = (edge, lane)
        limit = occupancy.get(key)
        if limit is not None and position > limit - (VEHICLE_LENGTH_M + MIN_GAP_M + minimum_spacing_m):
            dropped.append({"trajectory_id": str(row.trajectory_id), "reason": "position_overlap"})
            continue
        occupancy[key] = position
        trajectory = str(row.trajectory_id)
        route = "entering" if str(row.lane_id) == "7" else (
            "exiting" if trajectory in offramp_trajectories else "through")
        records.append({"id": f"i{len(records):04d}", "trajectory_id": trajectory,
                        "edge": edge, "lane_index": lane, "position_m": position,
                        "speed_mps": float(row.speed_mps), "route": route,
                        "observed_lane": str(row.lane_id), "observed_y_m": float(row.y_m)})
    return {"status": "Observation", "clock_s": instant,
            "observed_states_at_clock": int(len(frame)), "accepted": records,
            "dropped": dropped, "accepted_count": len(records), "dropped_count": len(dropped),
            "minimum_spacing_m": minimum_spacing_m,
            "note": (
                "the injected state is a subset of the observed state at the same instant; "
                "every dropped vehicle is reported with its reason")}


def _quasi_rank(text: str) -> float:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16 ** 12)


def depart_times(flow_veh_h: float, duration_s: float, phase: float) -> np.ndarray:
    if flow_veh_h <= 0:
        return np.zeros(0)
    interval = 3600.0 / flow_veh_h
    times = np.arange(phase * interval, duration_s - 0.05, interval)
    return np.round(np.ceil(times * 10 - 1e-9) / 10.0, 1)


def build_conditional_route_file(path: Path, condition: str, behaviour: str,
                                 types: list[dict[str, object]], *,
                                 demand: dict[str, object] | None = None,
                                 duration_s: float = DECLARED_DURATION_S,
                                 initial_records: list[dict[str, object]] | None = None,
                                 edge_speed_limits: dict[str, float] | None = None,
                                 edge_lane_counts: dict[str, int] | None = None
                                 ) -> dict[str, object]:
    """Deterministic declared demand: the same vehicle sequence in every arm.

    The sequences are generated by the same quasi-random rule for every arm, so
    a difference between arms is not a difference in the arrival realisation.
    Injected initial vehicles keep their observed position, lane and speed.
    """
    import xml.etree.ElementTree as ET

    spec = CONDITIONS[condition] if demand is None else demand
    mainline_flow = float(spec["mainline_flow_veh_h"])
    offramp_share = float(spec["offramp_flow_veh_h"]) / mainline_flow
    root = ET.Element("routes")
    for entry in types:
        ET.SubElement(root, "vType", dict(
            id=entry["id"], vClass=entry["vClass"], length=str(entry["length_m"]),
            tau=str(entry["tau"]), sigma=str(entry["sigma"]),
            **{k: str(v) for k, v in FIXED_VTYPE_FIELDS.items()}))
    routes = observed_geometry_spec(FREE_SPEED_MPS)["routes"]
    for route, edges in routes.items():
        ET.SubElement(root, "route", dict(id=route, edges=" ".join(edges)))
    # start-on-edge variants so an injected vehicle can keep its observed edge
    start_routes: dict[tuple[str, str], str] = {}
    valid_start = {"main_0": ("through", "exiting"), "main_1": ("through", "exiting"),
                   "main_2": ("through",), "onramp": ("entering",)}
    for edge, kinds in valid_start.items():
        for kind in kinds:
            chain = list(routes[kind])
            if edge not in chain:
                raise StateSupportError(f"invalid_start_chain:{edge}:{kind}")
            identifier = f"from_{edge}_{kind}"
            start_routes[(edge, kind)] = identifier
            ET.SubElement(root, "route", dict(id=identifier,
                                               edges=" ".join(chain[chain.index(edge):])))
    class_ids = [entry["id"] for entry in types]
    injected = 0
    clamped = 0
    lanes_clamped = 0
    limits = dict(edge_speed_limits or {})
    counts = dict(edge_lane_counts or {})
    for record in (initial_records or []):
        kind = "entering" if record["edge"] == "onramp" else str(record["route"])
        if (record["edge"], kind) not in start_routes:
            kind = "through"
        class_index = int(_quasi_rank(str(record["trajectory_id"])) * len(class_ids))
        speed = max(float(record["speed_mps"]), 0.1)
        allowed = float(limits.get(str(record["edge"]), speed))
        if speed > allowed:
            speed = allowed
            clamped += 1
        lane_index = int(record["lane_index"])
        available = int(counts.get(str(record["edge"]), lane_index + 1))
        if lane_index >= available:
            lane_index = available - 1
            lanes_clamped += 1
        ET.SubElement(root, "vehicle", dict(
            id=f"i{injected:04d}_{record['id']}", type=class_ids[min(class_index, len(class_ids) - 1)],
            route=start_routes[(record["edge"], kind)], depart="0.0",
            departLane=str(lane_index),
            departPos=f"{float(record['position_m']):.2f}",
            departSpeed=f"{speed:.2f}"))
        injected += 1
    pending: list[dict[str, str]] = []
    for index, depart in enumerate(depart_times(mainline_flow, duration_s, 0.5)):
        class_index = int(np.floor(((index * 0.6180339887498949) + 0.5) % 1.0 * len(class_ids)))
        use_offramp = ((index * 0.4142135623730951) % 1.0) < offramp_share
        pending.append(dict(id=f"m{index:05d}", type=class_ids[class_index],
                            route="exiting" if use_offramp else "through",
                            depart=f"{depart:.1f}", departLane=str(index % 5),
                            departPos="base", departSpeed="max"))
    onramp_class = class_ids[len(class_ids) // 2]
    for index, depart in enumerate(depart_times(float(spec["onramp_flow_veh_h"]), duration_s, 0.5)):
        pending.append(dict(id=f"r{index:05d}", type=onramp_class, route="entering",
                            depart=f"{depart:.1f}", departLane="0",
                            departPos="base", departSpeed="max"))
    pending.sort(key=lambda item: float(item["depart"]))
    for item in pending:
        ET.SubElement(root, "vehicle", item)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return {
        "condition": condition,
        "behaviour": behaviour,
        "duration_s": duration_s,
        "initial_vehicles": injected,
        "initial_speed_clamped": clamped,
        "initial_lane_clamped": lanes_clamped,
        "mainline_vehicles": int(len(depart_times(mainline_flow, duration_s, 0.5))),
        "onramp_vehicles": int(len(depart_times(float(spec["onramp_flow_veh_h"]), duration_s, 0.5))),
        "vtype_ids": class_ids,
    }


def route_length_map(path: Path) -> dict[str, float]:
    """Vehicle id -> length, read back from the written route file."""
    import xml.etree.ElementTree as ET
    root = ET.parse(str(path)).getroot()
    by_type = {entry.get("id"): float(entry.get("length")) for entry in root.findall("vType")}
    lengths: dict[str, float] = {}
    for vehicle in root.findall("vehicle"):
        lengths[vehicle.get("id")] = by_type[vehicle.get("type")]
    return lengths


def write_conditional_config(path: Path, *, network: Path, routes: Path, duration_s: float,
                             seed: int, internal_step_s: float = DECLARED_INTERNAL_STEP_S,
                             fcd_period_s: float = DECLARED_FCD_PERIOD_S) -> Path:
    import os as _os
    net_rel = _os.path.relpath(Path(network).resolve(), Path(path).resolve().parent).replace("\\", "/")
    route_rel = _os.path.relpath(Path(routes).resolve(), Path(path).resolve().parent).replace("\\", "/")
    path.write_text(
        "<configuration>"
        f"<input><net-file value=\"{net_rel}\"/><route-files value=\"{route_rel}\"/></input>"
        f"<time><begin value=\"0\"/><end value=\"{duration_s}\"/><step-length value=\"{internal_step_s}\"/></time>"
        "<processing><step-method.ballistic value=\"true\"/><threads value=\"1\"/>"
        "<time-to-teleport value=\"-1\"/><collision.action value=\"warn\"/></processing>"
        f"<output><fcd-output value=\"fcd.xml\"/><device.fcd.period value=\"{fcd_period_s}\"/>"
        "<summary-output value=\"summary.xml\"/></output>"
        f"<seed value=\"{seed}\"/></configuration>",
        encoding="utf-8",
    )
    return path


def run_sumo(config: Path, *, wall_limit_s: float = 900.0) -> dict[str, object]:
    import subprocess
    import time as _time
    from .stage_0_5_sumo import _sumo_binary
    started = _time.perf_counter()
    process = subprocess.run(
        [_sumo_binary(), "-c", str(config), "--no-step-log", "true", "--duration-log.statistics", "true"],
        capture_output=True, text=True, timeout=wall_limit_s,
    )
    wall = _time.perf_counter() - started
    log = process.stdout + process.stderr
    if process.returncode != 0:
        raise StateSupportError(f"sumo failed: {log[-2000:]}")
    return {"returncode": process.returncode, "wall_s": wall, "log_tail": log[-4000:],
            "teleports": int(log.count("Teleporting")), "collisions": int(log.count("collision"))}


# --------------------------------------------------------------------------
# (B3) simulator-native following measurement
# --------------------------------------------------------------------------
def fcd_to_state_frame(fcd: pd.DataFrame, lengths: dict[str, float], *, run_id: str,
                       scenario_id: str, seed: int) -> pd.DataFrame:
    """Same-lane leader relation from the native FCD record.

    ``pos`` in SUMO FCD is the front-bumper position, so the physical net gap is
    ``leader_front - leader_length - follower_front``.  This is the same
    definition the approved Stage 0.2 following link uses (verified there against
    TraCI ``getLeader`` with a 0.0 m residual).
    """
    frame = fcd.copy()
    frame["length_m"] = frame.vehicle_id.map(lengths).astype(float)
    if frame.length_m.isna().any():
        raise StateSupportError("unknown_vehicle_length")
    frame = frame.sort_values(["time_s", "lane_id", "y_m"], ascending=[True, True, True],
                              kind="stable").reset_index(drop=True)
    keys = [frame.time_s.to_numpy(), frame.lane_id.to_numpy()]
    grouped = frame.groupby(keys, sort=False)
    frame["leader_id"] = grouped["vehicle_id"].shift(-1)
    frame["leader_speed_mps"] = grouped["speed_mps"].shift(-1)
    leader_front = grouped["y_m"].shift(-1)
    leader_length = grouped["length_m"].shift(-1)
    frame["net_gap_m"] = leader_front - leader_length - frame.y_m
    out = pd.DataFrame({
        "run_id": run_id,
        "scenario_id": scenario_id,
        "experiment_mode": "no_message_baseline",
        "configured_seed": int(seed),
        "vehicle_id": frame.vehicle_id.astype(str),
        "trajectory_id": frame.vehicle_id.astype(str),
        "incarnation_id": frame.vehicle_id.astype(str),
        "simulation_step": np.arange(len(frame)),
        "time_s": frame.time_s.astype(float),
        "speed_mps": frame.speed_mps.astype(float),
        "acceleration_mps2": np.nan,
        "leader_id": frame.leader_id,
        "leader_trajectory_id": frame.leader_id,
        "leader_incarnation_id": frame.leader_id,
        "leader_identity_status": np.where(frame.leader_id.notna(), "observed", "not_applicable"),
        "leader_speed_mps": frame.leader_speed_mps,
        "net_gap_m": frame.net_gap_m,
        "lane_id": frame.lane_id.astype(str),
        "y_m": frame.y_m.astype(float),
    })
    return out


def measure_state_frame(states: pd.DataFrame) -> pd.DataFrame:
    from .stage_0_5_sumo import compute_sumo_measurements
    frame = states.copy().reset_index(drop=True)
    frame["acceleration_mps2"] = frame.groupby("vehicle_id")["speed_mps"].transform(
        lambda series: series.diff() / DECLARED_FCD_PERIOD_S)
    frame["acceleration_mps2"] = frame.acceleration_mps2.fillna(0.0)
    return compute_sumo_measurements(frame)


def block_descriptors(measured: pd.DataFrame, *, window: tuple[float, float],
                      block_s: float = BLOCK_S) -> dict[str, object]:
    """Local state descriptors of a simulated run over the declared window."""
    low, high = window
    lane_km = (REGION_END_M - REGION_START_M) / 1000.0 * len(MAINLINE_LANES)
    subset = measured[
        measured.lane_id.isin(list(MAINLINE_LANES))
        & measured.y_m.ge(REGION_START_M) & measured.y_m.lt(REGION_END_M)
        & measured.time_s.between(low, high, inclusive="left")
    ]
    if subset.empty:
        raise StateSupportError("empty_simulated_local_state")
    span = high - low
    vehicle_s = len(subset) * DECLARED_FCD_PERIOD_S
    blocks: list[dict[str, object]] = []
    block_index = ((subset.time_s - low) // block_s).astype(int)
    for index, part in subset.groupby(block_index, sort=True):
        blocks.append({
            "block_start_s": float(low + index * block_s),
            "speed_mean_mps": float(part.speed_mps.mean()),
            "density_veh_km_lane": len(part) * DECLARED_FCD_PERIOD_S / block_s / lane_km,
            "low_speed_share": float((part.speed_mps < LOW_SPEED_MPS).mean()),
            "closing_speed_mean_mps": float(part.closing_speed_mps.mean()),
            "closing_speed_negative_share": float((part.closing_speed_mps < 0).mean()),
        })
    density = vehicle_s / span / lane_km
    speed = float(subset.speed_mps.mean())
    evaluable = subset[subset.measurement_status.isin(["valid", "not_applicable"])]
    return {
        "status": "Observation",
        "window_s": [low, high],
        "states": int(len(subset)),
        "local_vehicle_s": vehicle_s,
        "density_veh_km_lane": density,
        "speed_mean_mps": speed,
        "speed_sd_mps": float(subset.speed_mps.std(ddof=1)),
        "flow_veh_h_lane_consistency": density * speed * 3.6,
        "low_speed_share": float((subset.speed_mps < LOW_SPEED_MPS).mean()),
        "closing_speed_mean_mps": float(subset.closing_speed_mps.mean()),
        "closing_speed_negative_share": float((subset.closing_speed_mps < 0).mean()),
        "net_gap_mean_m": float(subset.net_gap_m.mean()),
        "net_gap_median_m": float(subset.net_gap_m.median()),
        "tau_eff_ratio_s": (float((subset.net_gap_m.sum() - len(subset) * MIN_GAP_M)
                                  / subset.speed_mps.sum())
                            if subset.speed_mps.sum() > 0 else None),
        "p2_evaluable_exposure_veh_s": float(len(evaluable) * DECLARED_FCD_PERIOD_S),
        "blocks": blocks,
    }
      
