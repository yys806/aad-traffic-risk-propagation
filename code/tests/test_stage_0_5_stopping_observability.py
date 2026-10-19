"""Analytic identifiability tests for the public-interface stopping reconstruction.

Independent truth uses constant-acceleration kinematics; no displacement is ever
used to infer a candidate terminal speed (circular verification is forbidden).
"""
import math

import pytest

from riskprop.stage_0_5_stopping_observability import (
    TOLERANCE_M, expected_displacement, prove_clamp_non_injective,
    reconstruct_signed_vnext, step_is_action,
)


def test_action_step_detection_uses_step_start_alignment():
    # Step [7.1 -> 7.15]: lastAction read at 7.15 equals 7.05 -> NON-action step
    assert step_is_action(7.05, 7.1, 0.05, 0.1) is False
    # Step [7.15 -> 7.2]: lastAction read at 7.2 equals 7.15 -> action step
    assert step_is_action(7.15, 7.15, 0.05, 0.1) is True
    # A timestamp older than an action period is inconsistent, not non-action.
    assert step_is_action(7.1, 7.25, 0.05, 0.1) is None
    # floating-point tolerance near the grid
    assert step_is_action(7.15 + 1e-9, 7.15, 0.05, 0.1) is True


def test_action_step_detection_rejects_bad_input():
    assert step_is_action(0.4, 0.3, 0.05, 0.0) is None
    assert step_is_action(float("nan"), 0.3, 0.05, 0.1) is None
    # lastAction AFTER the step start cannot happen for a finished step
    assert step_is_action(0.5, 0.45, 0.05, 0.1) is None


def test_non_action_step_reconstructs_signed_candidate_exactly():
    # v0=10, carried a_pub=-2, h=0.05 -> u=9.9
    r = reconstruct_signed_vnext(10.0, -2.0, 0.05, is_action=False, v1=9.9)
    assert r["classification"] == "Exact Reconstructable Under Verified Conditions"
    assert r["candidate"] == pytest.approx(9.9)
    assert expected_displacement(10.0, r["candidate"], 0.05) == pytest.approx((10 + 9.9) / 2 * 0.05)


def test_non_action_step_within_step_stop_is_exact():
    # verified live trace: v0=0.1236955143419339, carried a=-4.5, h=0.05
    # u = v0 - 0.225 < 0 -> stop within step; dx = -v0^2/(2a) = 0.0017000644742637405
    v0 = 0.1236955143419339
    r = reconstruct_signed_vnext(v0, -4.5, 0.05, is_action=False, v1=0.0)
    assert r["candidate"] == pytest.approx(v0 - 0.225)
    assert r["candidate"] < 0
    dx = expected_displacement(v0, r["candidate"], 0.05)
    # C++ evaluation order differs at the last bits; agreement to float rounding
    assert dx == pytest.approx(0.0017000644742637405, abs=1e-14)
    # old trapezoid would give .5*v0*h -> the millimetre-scale error B1 saw
    assert 0.5 * v0 * 0.05 - dx == pytest.approx(0.0013923233842846072, abs=1e-12)


def test_action_step_positive_terminal_is_exact_observable():
    # action step ending at v1=9.8>0: no clamp triggered, u==v1 exactly
    r = reconstruct_signed_vnext(10.0, -2.0, 0.1, is_action=True, v1=9.8)
    assert r["classification"] == "Exact Observable"
    assert r["candidate"] == pytest.approx(9.8)


def test_action_step_terminal_stop_is_bounded_only():
    # decision stop: v0=0.2 -> v1=0. Public a_pub=(max(u,0)-v0)/h=-2 for ANY u<=0,
    # so an exact u (u=0 step-end or u<0 early stop) cannot be recovered.
    r = reconstruct_signed_vnext(0.2, -2.0, 0.1, is_action=True, v1=0.0)
    assert r["classification"] == "Bounded Consistency Only"
    assert r["candidate"] is None


def test_action_step_stop_cannot_distinguish_step_end_from_early():
    # same public record for u=0 and u=-0.2 -> both bounded, neither exact
    r0 = reconstruct_signed_vnext(0.2, -2.0, 0.1, is_action=True, v1=0.0)
    assert r0["candidate"] is None and r0["classification"] == "Bounded Consistency Only"


def test_candidate_formula_matches_getdeltaPos_stop_truncation():
    # independent: v0=0.2, u=-0.2, h=0.1 -> a=-4, t_stop=0.05, dx=0.5*0.2*0.05=0.005
    dx = expected_displacement(0.2, -0.2, 0.1)
    assert dx == pytest.approx(0.005)
    # normal branch
    assert expected_displacement(10.0, 9.9, 0.05) == pytest.approx(0.4975)


def test_public_record_is_non_injective_for_negative_candidates():
    proof = prove_clamp_non_injective(0.2, -0.2, -0.6, 0.1)
    assert proof["v_public_equal"] and proof["a_public_equal"]
    assert proof["displacements_differ"]
    # the SAME public record maps to different true displacements -> cannot invert
    assert proof["displacement_u1_m"] != pytest.approx(proof["displacement_u2_m"])


def test_displacement_back_inference_is_not_a_public_method():
    # There is deliberately NO API that takes a measured displacement and returns u.
    import riskprop.stage_0_5_stopping_observability as m
    assert not hasattr(m, "infer_vnext_from_displacement")


def test_reconstruct_rejects_nonfinite_and_nonpositive():
    for bad in [(float("nan"), -2.0, 0.1), (1.0, float("inf"), 0.1)]:
        assert reconstruct_signed_vnext(bad[0], bad[1], bad[2], is_action=False, v1=1.0)["classification"] == "Not Evaluable"
    assert reconstruct_signed_vnext(1.0, -2.0, 0.0, is_action=False, v1=1.0)["classification"] == "Not Evaluable"
    assert reconstruct_signed_vnext(-1.0, -2.0, 0.1, is_action=False, v1=1.0)["classification"] == "Not Evaluable"
    assert reconstruct_signed_vnext(1.0, -2.0, 0.1, is_action=False, v1=-1.0)["classification"] == "Not Evaluable"


def test_tolerance_is_fixed_not_result_derived():
    assert TOLERANCE_M == 1e-6


@pytest.mark.parametrize("bad", [None, 0, 1, "false", "True", [], {}, 0.0])
def test_unknown_or_non_boolean_action_never_reconstructs(bad):
    r = reconstruct_signed_vnext(.1, -4.5, .05, is_action=bad, v1=0.)
    assert r == dict(candidate=None, classification="Not Evaluable",
                     reason="action_step_identity_not_boolean")


@pytest.mark.parametrize("last,start,h,action", [
    (0., .15, .05, .1), (.03, .05, .05, .1), (0., .05, 0., .1),
    (0., .05, float("nan"), .1), (0., .05, .2, .1),
    (0., .05, .05, .075), (False, .05, .05, .1),
])
def test_inconsistent_action_clock_is_unknown(last, start, h, action):
    assert step_is_action(last, start, h, action) is None
