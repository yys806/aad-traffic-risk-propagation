"""Tests for the jam-definition sensitivity and null-model module."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop import stage_0_5_jam_definition as jd  # noqa: E402


def _grid(rows: int = 10, columns: int = 8, slow_block: tuple[int, int, int, int] | None = None):
    index = pd.Index(np.arange(rows, dtype=float) * 30.0)
    columns_index = pd.Index(np.arange(columns, dtype=float) * 50.0)
    grid = pd.DataFrame(20.0, index=index, columns=columns_index)
    if slow_block:
        row_low, row_high, column_low, column_high = slow_block
        grid.iloc[row_low:row_high, column_low:column_high] = 4.0
    return grid


def test_absolute_rule_uses_the_threshold_strictly_below():
    grid = _grid(slow_block=(0, 2, 0, 2))
    mask = jd.congestion_mask(grid, {"kind": "absolute", "threshold_mps": 10.0})
    assert mask.iloc[0, 0]
    assert not mask.iloc[9, 7]


def test_relative_rule_preserves_the_paper_definition():
    grid = _grid(slow_block=(0, 2, 0, 2))
    # v_max of the window is 20, so lambda = 0.2 inside the block and 1.0 outside
    mask = jd.congestion_mask(grid, {"kind": "relative", "reference": "max_of_window", "rho": 0.5})
    assert mask.iloc[0, 0]
    assert not mask.iloc[5, 5]


def test_nan_cells_are_never_congested():
    grid = _grid()
    grid.iloc[3, 3] = np.nan
    mask = jd.congestion_mask(grid, {"kind": "absolute", "threshold_mps": 10.0})
    assert not bool(mask.iloc[3, 3])


def test_describe_mask_reports_upstream_growth_and_backward_speed():
    grid = _grid(rows=6, columns=8)
    # one connected band that walks from downstream cells at early times to upstream
    # cells at later times, with consecutive rows sharing an adjacent column
    mask = pd.DataFrame(False, index=grid.index, columns=grid.columns)
    for row in range(6):
        start = max(0, 6 - row)
        mask.iloc[row, start:start + 2] = True
    description = jd.describe_mask(grid, mask, t_step_s=30.0, y_step_m=50.0)
    assert description["largest_cells"] == 12
    assert description["growth"] == "upstream"
    assert description["backward_speed_mps"] > 0
    assert description["largest_first_position_m"][0] >= 300.0


def test_null_model_preserves_the_time_marginal_exactly():
    grid = _grid(rows=8, columns=6)
    mask = pd.DataFrame(False, index=grid.index, columns=grid.columns)
    mask.iloc[2:5, 1:3] = True
    result = jd.null_model(grid, mask, permutations=5, seed=1, t_step_s=30.0, y_step_m=50.0)
    per_row = mask.sum(axis=1).to_numpy()
    # every null realisation keeps the per-time-step count of congested cells
    assert per_row.sum() == mask.to_numpy().sum()
    assert result["permutations"] == 5
    assert result["missing_cells_never_counted_as_uncongested"] is True


def test_null_model_is_deterministic_for_a_fixed_seed():
    grid = _grid(rows=8, columns=6, slow_block=(0, 3, 0, 2))
    mask = jd.congestion_mask(grid, {"kind": "absolute", "threshold_mps": 10.0})
    first = jd.null_model(grid, mask, permutations=20, seed=7, t_step_s=30.0, y_step_m=50.0)
    second = jd.null_model(grid, mask, permutations=20, seed=7, t_step_s=30.0, y_step_m=50.0)
    assert first["null"] == second["null"]


def test_rule_catalogue_documents_reference_and_adaptation():
    rules = jd.rule_catalogue()
    names = {rule["name"] for rule in rules}
    assert "absolute_10mps" in names
    assert "duan_w_lt_0.5_p95_reference" in names
    relative = [rule for rule in rules if rule["kind"] == "relative"]
    assert all(rule.get("adaptation") for rule in relative)
    engineering = next(rule for rule in rules if rule["name"] == "saberi_lambda_lt_0.5_engineering_reference")
    assert "NOT a measured free-flow speed" in engineering["adaptation"]


def test_unknown_rule_kind_is_rejected():
    grid = _grid()
    with pytest.raises(jd.JamDefinitionError):
        jd.congestion_mask(grid, {"kind": "nonsense"})
