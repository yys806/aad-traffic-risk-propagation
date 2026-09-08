"""Analytic E01 measurement functions with no confirmatory-effect access."""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


def integrated_ttc_exposure(states: pd.DataFrame, *, threshold_s: float) -> float:
    """Return valid-time-normalized TTC exposure; missing is NaN, never zero."""

    if threshold_s <= 0:
        raise ValueError("threshold_s must be positive")
    required = {"ttc_s", "valid", "dt_s", "collision"}
    missing = required - set(states.columns)
    if missing:
        raise ValueError(f"states are missing: {', '.join(sorted(missing))}")
    valid = states["valid"].fillna(False).astype(bool)
    dt = pd.to_numeric(states["dt_s"], errors="coerce")
    usable = valid & dt.notna() & (dt > 0)
    if not usable.any():
        return float("nan")
    ttc = pd.to_numeric(states["ttc_s"], errors="coerce")
    collision = states["collision"].fillna(False).astype(bool)
    risk = pd.Series(0.0, index=states.index)
    risk.loc[usable & (collision | (ttc <= 0))] = 1.0
    within = usable & ~collision & (ttc > 0) & (ttc < threshold_s)
    risk.loc[within] = 1.0 - ttc.loc[within] / threshold_s
    return float((risk.loc[usable] * dt.loc[usable]).sum() / dt.loc[usable].sum())


def post_encroachment_time(
    first_interval: tuple[float, float], second_interval: tuple[float, float]
) -> float:
    """Time between two agents occupying the same conflict zone; overlap is zero."""

    a_start, a_end = map(float, first_interval)
    b_start, b_end = map(float, second_interval)
    if a_end < a_start or b_end < b_start:
        raise ValueError("conflict-zone intervals must have non-negative duration")
    if a_end < b_start:
        return b_start - a_end
    if b_end < a_start:
        return a_start - b_end
    return 0.0


def rear_end_analytic_truth(
    *, net_gap_m: float, follower_speed_mps: float, leader_speed_mps: float
) -> dict[str, float | bool | str]:
    """Closed-form rear-end truth used to test, not replace, the data pipeline."""

    values = (net_gap_m, follower_speed_mps, leader_speed_mps)
    if not all(math.isfinite(float(value)) for value in values):
        return {
            "status": "missing",
            "collision": False,
            "closing_speed_mps": float("nan"),
            "ttc_s": float("nan"),
            "drac_mps2": float("nan"),
        }
    closing_speed = float(follower_speed_mps) - float(leader_speed_mps)
    if net_gap_m <= 0:
        return {
            "status": "collision_or_overlap",
            "collision": True,
            "closing_speed_mps": closing_speed,
            "ttc_s": 0.0,
            "drac_mps2": float("inf"),
        }
    if closing_speed <= 0:
        return {
            "status": "not_applicable",
            "collision": False,
            "closing_speed_mps": closing_speed,
            "ttc_s": float("inf"),
            "drac_mps2": 0.0,
        }
    return {
        "status": "valid",
        "collision": False,
        "closing_speed_mps": closing_speed,
        "ttc_s": float(net_gap_m) / closing_speed,
        "drac_mps2": closing_speed**2 / (2.0 * float(net_gap_m)),
    }


def evaluate_timestep_convergence(
    metric_by_step: dict[float, float], *, zero_tolerance: float | None
) -> dict[str, float | bool | str | None]:
    """Check the frozen 0.10/0.05/0.02 s ladder without inventing delta_eq."""

    required = (0.10, 0.05, 0.02)
    missing = [step for step in required if step not in metric_by_step]
    if missing:
        raise ValueError(f"missing required time steps: {missing}")
    values = {float(step): float(value) for step, value in metric_by_step.items()}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("timestep metrics must be finite")
    direction_values = [values[step] for step in sorted(values, reverse=True)]
    nonzero_signs = {math.copysign(1.0, value) for value in direction_values if value != 0}
    direction_consistent = len(nonzero_signs) <= 1
    difference = abs(values[0.05] - values[0.02])
    if zero_tolerance is None:
        status = "pending_delta_eq"
        tolerance_pass = None
    else:
        if zero_tolerance < 0 or not math.isfinite(float(zero_tolerance)):
            raise ValueError("zero_tolerance must be finite and non-negative")
        tolerance_pass = difference <= float(zero_tolerance)
        status = "pass" if tolerance_pass and direction_consistent else "fail"
    return {
        "difference_005_002": difference,
        "direction_consistent": direction_consistent,
        "zero_tolerance": zero_tolerance,
        "within_zero_tolerance": tolerance_pass,
        "gate_status": status,
    }


def first_sustained_divergence(
    times: Sequence[float],
    differences: Sequence[float],
    *,
    tolerance: float,
    sustain_s: float,
) -> float:
    """Find the first tolerance exceedance lasting the preregistered duration."""

    if len(times) != len(differences) or not times:
        raise ValueError("times and differences must be non-empty and equally sized")
    if tolerance < 0 or sustain_s <= 0:
        raise ValueError("tolerance must be non-negative and sustain_s positive")
    t = np.asarray(times, dtype=float)
    d = np.asarray(differences, dtype=float)
    if np.any(np.diff(t) <= 0):
        raise ValueError("times must be strictly increasing")
    representative_step = float(np.median(np.diff(t))) if len(t) > 1 else 0.0
    above = np.isfinite(d) & (np.abs(d) > tolerance)
    start: int | None = None
    for index, is_above in enumerate(above):
        if is_above and start is None:
            start = index
        if start is not None and (not is_above or index == len(above) - 1):
            end_index = index - 1 if not is_above else index
            observed_until = t[end_index] + representative_step
            if observed_until - t[start] + 1e-12 >= sustain_s:
                return float(t[start])
            start = None
    return math.inf


def derive_delta_eq(
    *,
    numerical_errors: Iterable[float],
    timestep_errors: Iterable[float],
    analyzer_errors: Iterable[float],
    reconstruction_errors: Iterable[float],
    quantile: float = 0.99,
) -> float:
    """Take the largest preregistered upper quantile across all error sources."""

    if not 0 < quantile <= 1:
        raise ValueError("quantile must be in (0, 1]")
    groups = [numerical_errors, timestep_errors, analyzer_errors, reconstruction_errors]
    bounds = []
    for values in groups:
        array = np.abs(np.asarray(list(values), dtype=float))
        array = array[np.isfinite(array)]
        if array.size == 0:
            raise ValueError("every error source must contain at least one finite value")
        bounds.append(float(np.quantile(array, quantile, method="higher")))
    return max(bounds)


def derive_delta_r(delta_eq: float, *, minimum_actionable_risk_change: float) -> float:
    delta_eq = float(delta_eq)
    actionable = float(minimum_actionable_risk_change)
    if delta_eq < 0 or actionable < 0:
        raise ValueError("effect boundaries must be non-negative")
    if actionable <= delta_eq:
        raise ValueError(
            "minimum actionable risk change must be strictly larger than delta_eq"
        )
    return actionable


def paired_confirmatory_sample_size(
    *,
    paired_sd: float,
    delta_r: float,
    delta_plan: float,
    alpha: float = 0.025,
    power: float = 0.90,
    minimum: int = 100,
) -> dict[str, int | float]:
    """Normal-approximation planning rule for preregistered paired seeds."""

    if paired_sd <= 0 or delta_r <= 0:
        raise ValueError("paired_sd and delta_r must be positive")
    if delta_plan <= delta_r:
        raise ValueError("delta_plan must be strictly larger than delta_r")
    if not 0 < alpha < 0.5 or not 0.5 < power < 1:
        raise ValueError("alpha/power are outside supported planning ranges")
    gap = delta_plan - delta_r
    normal = NormalDist()
    z_alpha = normal.inv_cdf(1.0 - alpha)
    z_power = normal.inv_cdf(power)
    n_power = math.ceil(((z_alpha + z_power) * paired_sd / gap) ** 2)
    target_half_width = min(0.25 * delta_r, 0.50 * gap)
    z_95 = normal.inv_cdf(0.975)
    n_precision = math.ceil((z_95 * paired_sd / target_half_width) ** 2)
    return {
        "n_power": n_power,
        "n_precision": n_precision,
        "minimum": int(minimum),
        "n_confirm": max(int(minimum), n_power, n_precision),
        "target_half_width": target_half_width,
    }
