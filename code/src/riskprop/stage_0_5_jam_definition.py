"""Threshold sensitivity and a spatial-arrangement null model for low-speed regions.

Method grounding
----------------
* Duan et al. (2023), Nat. Commun. 14:8111, Eq. 9: a road e is congested when the
  relative speed ``W_e(t) = U_e(t) / U_e95`` is below 0.5, where ``U_e95`` is the
  95th percentile of that road's velocity records.
* Saberi et al. (2020), Nat. Commun. 11:1619, Eq. 1-2: ``lambda_i(t) = v_i(t)/v_max_i``
  with ``v_max_i`` the maximum observed speed on link i in a 24 h cycle, congested
  when ``lambda_i(t) < rho`` for a pre-specified ``rho``; and the null model is
  "for each time step t, ... randomly drawing lambda_i(t) of each link i from the
  same distribution of the link relative speeds as in the simulated data at the
  same time step".

Project adaptations that are *not* in either paper and are therefore labelled as
project design choices:

* Neither paper observes a 15-minute freeway segment, so neither ``U_e95`` over a
  24 h cycle nor a 24 h ``v_max`` exists here. This module computes the reference
  from the same observation window and reports the sensitivity to that choice,
  including a fixed engineering reference (the SUMO vType ``maxSpeed``), which is
  an engineering setting and **not** a measured free-flow speed.
* The papers work on road networks; here the corridor is discretised into
  longitudinal cells, so the null model permutes cell speeds within each time
  slice (marginal preserved, spatial arrangement destroyed) instead of permuting
  link values. The permutation count is a project implementation choice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

VERSION = "stage-0.5-jam-definition-v1"

#: Threshold candidates. Absolute values are the existing project descriptive
#: threshold plus a finite neighbourhood; relative values follow the two papers.
ABSOLUTE_THRESHOLDS_MPS = (5.0, 10.0, 15.0)
DUAN_RHO = 0.5
SABERI_RHOS = (0.3, 0.4, 0.5, 0.6)
#: FHWA (2019) Chapter 5 rule of thumb: congestion speed threshold ~ one third of
#: observed free-flow speed.
FHWA_FREE_FLOW_FRACTION = 1.0 / 3.0
#: The vType maxSpeed of the frozen SUMO configuration. Engineering setting only.
ENGINEERING_MAX_SPEED_MPS = 27.78


class JamDefinitionError(ValueError):
    """Fail-closed error for schema or definition violations."""


def cell_speed_grid(
    frame: pd.DataFrame,
    *,
    window: tuple[float, float],
    lanes: tuple[str, ...] = ("1", "2", "3", "4", "5"),
    y_step_m: float = 50.0,
    t_step_s: float = 30.0,
) -> pd.DataFrame:
    """Time x longitudinal-cell mean speed (m/s). Cells with no observation stay NaN."""
    low, high = window
    upper = float(frame.y_m.max())
    y_edges = np.arange(0.0, upper + y_step_m, y_step_m)
    t_edges = np.arange(low, high + t_step_s, t_step_s)
    subset = frame[frame.lane_id.isin(lanes) & frame.time_s.between(low, high, inclusive="left")].copy()
    subset["y_bin"] = pd.cut(subset.y_m, bins=y_edges, right=False, labels=y_edges[:-1]).astype(float)
    subset["t_bin"] = pd.cut(subset.time_s, bins=t_edges, right=False, labels=t_edges[:-1]).astype(float)
    grid = subset.pivot_table(index="t_bin", columns="y_bin", values="speed_mps", aggfunc="mean")
    return grid.reindex(index=t_edges[:-1], columns=y_edges[:-1])


def reference_speeds(grid: pd.DataFrame) -> dict[str, pd.Series]:
    """Per-cell reference speed under each reproducible definition."""
    return {
        "p95_of_window": grid.quantile(0.95, axis=0),
        "max_of_window": grid.max(axis=0),
        "engineering_max_speed": pd.Series(ENGINEERING_MAX_SPEED_MPS, index=grid.columns),
    }


def congestion_mask(grid: pd.DataFrame, rule: dict[str, object]) -> pd.DataFrame:
    """Boolean congestion mask for one threshold rule. NaN cells are never congested."""
    kind = rule["kind"]
    if kind == "absolute":
        return grid < float(rule["threshold_mps"])
    if kind == "relative":
        reference = rule["reference"]
        if reference not in reference_speeds(grid):
            raise JamDefinitionError(f"unknown_reference:{reference}")
        reference_values = reference_speeds(grid)[reference]
        relative = grid.div(reference_values.replace(0.0, np.nan), axis=1)
        return relative < float(rule["rho"])
    raise JamDefinitionError(f"unknown_rule_kind:{kind}")


def _components(mask: np.ndarray) -> list[dict[str, object]]:
    """4-neighbour connected components of a boolean (time x space) mask."""
    if mask.size == 0:
        return []
    rows, columns = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    found: list[dict[str, object]] = []
    for row in range(rows):
        for column in range(columns):
            if not mask[row, column] or visited[row, column]:
                continue
            stack = [(row, column)]
            visited[row, column] = True
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_column = current_row + delta_row, current_column + delta_column
                    if 0 <= next_row < rows and 0 <= next_column < columns and mask[next_row, next_column] and not visited[next_row, next_column]:
                        visited[next_row, next_column] = True
                        stack.append((next_row, next_column))
            found.append({"cells": cells, "rows": [cell[0] for cell in cells], "columns": [cell[1] for cell in cells]})
    return found


def describe_mask(grid: pd.DataFrame, mask: pd.DataFrame, *, t_step_s: float, y_step_m: float) -> dict[str, object]:
    """Descriptive statistics of the low-speed structure of one mask."""
    values = mask.to_numpy(dtype=bool)
    times = grid.index.to_numpy(dtype=float)
    positions = grid.columns.to_numpy(dtype=float)
    components = _components(values)
    if not components:
        return {
            "slow_cell_fraction": 0.0 if values.size == 0 else float(values.mean()),
            "component_count": 0,
            "largest_cells": 0,
            "largest_duration_s": 0.0,
            "largest_first_time_s": None,
            "largest_first_position_m": [None, None],
            "largest_last_position_m": [None, None],
            "growth": None,
            "backward_speed_mps": None,
        }
    largest = max(components, key=lambda component: len(component["cells"]))
    first_row = int(min(largest["rows"]))
    last_row = int(max(largest["rows"]))
    first_columns = [column for row, column in zip(largest["rows"], largest["columns"]) if row == first_row]
    last_columns = [column for row, column in zip(largest["rows"], largest["columns"]) if row == last_row]
    first_positions = positions[first_columns]
    last_positions = positions[last_columns]
    growth = (
        "upstream" if last_positions.min() < first_positions.min()
        else "downstream" if last_positions.max() > first_positions.max()
        else "stationary"
    )
    cell_travel = first_positions.min() - last_positions.min() if growth == "upstream" else last_positions.max() - first_positions.max()
    elapsed = times[last_row] - times[first_row]
    backward_speed = float(cell_travel / elapsed) if growth != "stationary" and elapsed > 0 else None
    return {
        "slow_cell_fraction": float(values.mean()),
        "component_count": len(components),
        "largest_cells": len(largest["cells"]),
        "largest_duration_s": float(elapsed + t_step_s),
        "largest_first_time_s": float(times[first_row]),
        "largest_first_position_m": [float(first_positions.min()), float(first_positions.max())],
        "largest_last_position_m": [float(last_positions.min()), float(last_positions.max())],
        "growth": growth,
        "backward_speed_mps": backward_speed,
        "y_step_m": y_step_m,
        "t_step_s": t_step_s,
    }


def null_model(
    grid: pd.DataFrame,
    mask: pd.DataFrame,
    *,
    permutations: int,
    seed: int,
    t_step_s: float,
    y_step_m: float,
    statistics: tuple[str, ...] = ("largest_cells", "slow_cell_fraction", "component_count", "largest_duration_s"),
) -> dict[str, object]:
    """Saberi-style null: permute cell labels within each time slice.

    The marginal distribution of speeds at each time step is preserved exactly;
    only the spatial arrangement is destroyed. Cells that are NaN in the observed
    grid are excluded from the permutation and stay NaN, so missing coverage is
    never silently treated as uncongested.
    """
    observed = describe_mask(grid, mask, t_step_s=t_step_s, y_step_m=y_step_m)
    array = mask.to_numpy(dtype=object).copy()
    valid = pd.notna(grid.to_numpy(dtype=float))
    generator = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {name: [] for name in statistics}
    n_rows, n_columns = array.shape
    for _ in range(permutations):
        shuffled = mask.to_numpy(dtype=bool).copy()
        for row in range(n_rows):
            valid_columns = np.where(valid[row])[0]
            if len(valid_columns) < 2:
                continue
            shuffled[row, valid_columns] = shuffled[row, valid_columns][generator.permutation(len(valid_columns))]
        description = describe_mask(grid, pd.DataFrame(shuffled, index=mask.index, columns=mask.columns), t_step_s=t_step_s, y_step_m=y_step_m)
        for name in statistics:
            value = description[name]
            if isinstance(value, (int, float)):
                draws[name].append(float(value))
    summary: dict[str, object] = {}
    for name in statistics:
        values = np.asarray(draws[name], dtype=float)
        observed_value = observed[name]
        if values.size == 0 or observed_value is None:
            summary[name] = {"observed": observed_value, "null_mean": None, "null_p95": None, "exceedance": None}
            continue
        summary[name] = {
            "observed": float(observed_value),
            "null_mean": float(values.mean()),
            "null_p95": float(np.quantile(values, 0.95)),
            "exceedance": float((values >= float(observed_value)).mean()),
        }
    return {
        "observed": observed,
        "null": summary,
        "permutations": permutations,
        "seed": seed,
        "statistic_note": (
            "exceedance is the fraction of null realisations at least as large as the observed "
            "statistic; the permutation count is a project implementation choice"
        ),
        "missing_cells_never_counted_as_uncongested": True,
    }


def rule_catalogue() -> list[dict[str, object]]:
    """The full pre-declared rule set evaluated by this module."""
    rules: list[dict[str, object]] = []
    for threshold in ABSOLUTE_THRESHOLDS_MPS:
        rules.append({"name": f"absolute_{threshold:.0f}mps", "kind": "absolute", "threshold_mps": threshold,
                      "source": "project descriptive threshold (10 m/s) and a finite neighbourhood"})
    rules.append({
        "name": "duan_w_lt_0.5_p95_reference",
        "kind": "relative",
        "reference": "p95_of_window",
        "rho": DUAN_RHO,
        "source": "Duan et al. (2023) Eq. 9: W=U/U95, congested if W<0.5",
        "adaptation": "U95 computed over the same observation window, not a 24 h record",
    })
    for rho in SABERI_RHOS:
        rules.append({
            "name": f"saberi_lambda_lt_{rho:.1f}_max_reference",
            "kind": "relative",
            "reference": "max_of_window",
            "rho": rho,
            "source": "Saberi et al. (2020) Eq. 1-2: lambda=v/v_max, congested if lambda<rho",
            "adaptation": "v_max computed from the same observation window, not a 24 h cycle",
        })
    rules.append({
        "name": "saberi_lambda_lt_0.5_engineering_reference",
        "kind": "relative",
        "reference": "engineering_max_speed",
        "rho": 0.5,
        "source": "Saberi et al. (2020) Eq. 1-2 with a fixed reference speed",
        "adaptation": f"{ENGINEERING_MAX_SPEED_MPS} m/s is the frozen SUMO vType maxSpeed, an engineering setting and NOT a measured free-flow speed",
    })
    rules.append({
        "name": "fhwa_one_third_engineering_reference",
        "kind": "absolute",
        "threshold_mps": ENGINEERING_MAX_SPEED_MPS * FHWA_FREE_FLOW_FRACTION,
        "source": "FHWA (2019) Chapter 5: congestion speed threshold ~1/3 of observed free-flow speed",
        "adaptation": "the reference is the engineering maxSpeed, so this is a rule-of-thumb anchor, not an observation-anchored threshold",
    })
    return rules
