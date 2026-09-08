from __future__ import annotations

import math

import pandas as pd
import pytest

from riskprop.e01_metrics import (
    derive_delta_eq,
    derive_delta_r,
    evaluate_timestep_convergence,
    first_sustained_divergence,
    integrated_ttc_exposure,
    paired_confirmatory_sample_size,
    post_encroachment_time,
    rear_end_analytic_truth,
)


def test_integrated_ttc_exposure_uses_valid_mask_and_time_weights() -> None:
    rows = pd.DataFrame(
        {
            "ttc_s": [math.inf, 1.0, 0.0, 1.5],
            "valid": [True, True, True, False],
            "dt_s": [0.1, 0.1, 0.1, 0.1],
            "collision": [False, False, True, False],
        }
    )
    result = integrated_ttc_exposure(rows, threshold_s=2.0)
    assert result == pytest.approx((0.0 + 0.5 + 1.0) / 3.0)


def test_integrated_ttc_exposure_returns_missing_without_valid_observation() -> None:
    rows = pd.DataFrame(
        {"ttc_s": [math.inf], "valid": [False], "dt_s": [0.1], "collision": [False]}
    )
    assert math.isnan(integrated_ttc_exposure(rows, threshold_s=2.0))


def test_pet_uses_non_overlapping_conflict_zone_intervals() -> None:
    assert post_encroachment_time((1.0, 2.0), (2.4, 3.0)) == pytest.approx(0.4)
    assert post_encroachment_time((2.4, 3.0), (1.0, 2.0)) == pytest.approx(0.4)
    assert post_encroachment_time((1.0, 2.5), (2.0, 3.0)) == pytest.approx(0.0)


def test_first_divergence_requires_sustained_exceedance() -> None:
    times = [0.0, 0.1, 0.2, 0.3, 0.4]
    differences = [0.0, 0.2, 0.0, 0.3, 0.4]
    assert first_sustained_divergence(times, differences, tolerance=0.1, sustain_s=0.2) == pytest.approx(0.3)
    assert math.isinf(
        first_sustained_divergence(times, [0.0] * 5, tolerance=0.1, sustain_s=0.2)
    )


def test_effect_boundaries_follow_frozen_generation_rules() -> None:
    delta_eq = derive_delta_eq(
        numerical_errors=[0.01, 0.02],
        timestep_errors=[0.03, 0.04],
        analyzer_errors=[0.02, 0.05],
        reconstruction_errors=[0.01, 0.02],
        quantile=1.0,
    )
    assert delta_eq == pytest.approx(0.05)
    assert derive_delta_r(delta_eq, minimum_actionable_risk_change=0.08) == pytest.approx(0.08)
    with pytest.raises(ValueError, match="strictly larger"):
        derive_delta_r(delta_eq, minimum_actionable_risk_change=0.04)


def test_confirmatory_sample_size_respects_power_precision_and_floor() -> None:
    result = paired_confirmatory_sample_size(
        paired_sd=0.15,
        delta_r=0.05,
        delta_plan=0.10,
        alpha=0.025,
        power=0.90,
        minimum=100,
    )
    assert result["n_confirm"] >= 100
    assert result["n_confirm"] >= result["n_power"]
    assert result["n_confirm"] >= result["n_precision"]
    with pytest.raises(ValueError, match="delta_plan"):
        paired_confirmatory_sample_size(
            paired_sd=0.15,
            delta_r=0.05,
            delta_plan=0.05,
        )


def test_rear_end_analytic_truth_covers_closing_stationary_and_collision_cases() -> None:
    closing = rear_end_analytic_truth(
        net_gap_m=20.0, follower_speed_mps=10.0, leader_speed_mps=5.0
    )
    assert closing == {
        "status": "valid",
        "collision": False,
        "closing_speed_mps": 5.0,
        "ttc_s": 4.0,
        "drac_mps2": 0.625,
    }
    assert rear_end_analytic_truth(
        net_gap_m=20.0, follower_speed_mps=0.0, leader_speed_mps=5.0
    )["status"] == "not_applicable"
    assert rear_end_analytic_truth(
        net_gap_m=0.0, follower_speed_mps=5.0, leader_speed_mps=0.0
    )["collision"] is True


def test_timestep_convergence_is_pending_until_zero_tolerance_is_frozen() -> None:
    raw = evaluate_timestep_convergence(
        {0.10: 0.200, 0.05: 0.195, 0.02: 0.194, 0.01: 0.1938},
        zero_tolerance=None,
    )
    assert raw["gate_status"] == "pending_delta_eq"
    assert raw["difference_005_002"] == pytest.approx(0.001)
    passed = evaluate_timestep_convergence(
        {0.10: 0.200, 0.05: 0.195, 0.02: 0.194, 0.01: 0.1938},
        zero_tolerance=0.002,
    )
    assert passed["gate_status"] == "pass"
    failed = evaluate_timestep_convergence(
        {0.10: 0.200, 0.05: 0.195, 0.02: -0.194, 0.01: -0.1938},
        zero_tolerance=1.0,
    )
    assert failed["direction_consistent"] is False
    assert failed["gate_status"] == "fail"
