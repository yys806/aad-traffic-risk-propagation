"""B1.1-S: independent public-interface observability of SUMO ballistic stopping.

This module only *observes* through the public TraCI interface. It never reads a
displacement to infer the hidden signed candidate terminal speed (that would be
circular) and never modifies any Stage 0.5 measurement or SUMO binary.

Source basis (official SUMO v1_26_0, commit fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3):
  MSVehicle::planMove/executeMove (microsim_MSVehicle.cpp ~2105/~4569)
  MSVehicle::updateState   (microsim_MSVehicle.cpp ~4895)  myAcceleration=SPEED2ACCEL(MAX2(vNext,0)-v0)
  MSVehicle::getDeltaPos   (microsim_MSVehicle.cpp ~3658)  ballistic stop truncation
  MSVehicle::checkActionStep/isActionStep (2072 / MSVehicle.h ~636)
  libsumo Vehicle::getAcceleration/getSpeed/getLastActionTime

Timing semantics (verified against live TraCI traces):
  The step spanning [t_prev -> t_now] is an ACTION step iff the lastActionTime
  observable read AT t_now equals t_prev (the action was taken at the start of
  the executed step; checkActionStep(t_prev) set myLastActionTime=t_prev).
  Non-action steps keep lastActionTime < t_prev (older action point).

Definitions (internal step h, start-of-step public speed v0, hidden signed
candidate terminal speed u, stored public acceleration a_pub):
  action step     : vNext recomputed via finalizeSpeed; a_pub OVERWRITTEN =
                    (max(u,0)-v0)/h. If the vehicle reports v1==0 the clamp hides
                    u<=0 -> NOT exactly reconstructable (bounded only). If v1>0
                    then u==v1 exactly.
  non-action step : vSafe = v0 + a_pub_at_step_start*h with a_pub carried from
                    the last action step; u = v0 + a_pub_start*h EXACTLY (any
                    sign, including a within-step stop u<0).
"""
from __future__ import annotations

import math

VERSION = "b11s-observability-v2"
TOLERANCE_M = 1e-6

# Time-tolerance (s) for matching TraCI floating-point seconds against the
# integer-millisecond action-step grid. Far below the 50 ms internal step.
_TIME_TOL_S = 1e-6


def step_is_action(last_action_time_at_end, step_start_time, step_s, action_step_s):
    """True iff the step [step_start_time -> end] was an action step.

    last_action_time_at_end is getLastActionTime() read at the END of the step.
    The step is an action step iff that value equals the step-start time (the
    action was taken at the step start). Returns None on unusable inputs.
    """
    if not all(isinstance(x, (int, float)) and math.isfinite(x)
               for x in (last_action_time_at_end, step_start_time, action_step_s)):
        return None
    if action_step_s <= 0:
        return None
    if abs(last_action_time_at_end - step_start_time) <= _TIME_TOL_S:
        return True
    if last_action_time_at_end < step_start_time - _TIME_TOL_S:
        return False
    # lastActionTime after the step start cannot happen for a finished step
    return None


def reconstruct_signed_vnext(v0, a_pub_start, step_s, *, is_action, v1):
    """Attempt to reconstruct the hidden signed candidate terminal speed u.

    a_pub_start is the public acceleration observable read at the START of the
    step (i.e. at t_prev), which is the value executeMove's non-action branch
    continues from.

    Returns dict(candidate=u or None, classification, reason).

    - is_action True: vNext was recomputed via finalizeSpeed and the stored public
      acceleration is a_pub=(max(u,0)-v0)/h. Any action step ending at v1==0 has a
      clamped (hidden) u<=0 and CANNOT be exactly reconstructed (u=0 step-end stop
      and u<0 early stop share the same public record). An action step ending at
      v1>0 has u==v1 exactly (no clamp).
    - is_action False: u = v0 + a_pub_start*h EXACTLY, any sign, including a
      within-step stop u<0 (the carried acceleration may drive vSafe negative).
    """
    for x in (v0, a_pub_start, step_s, v1):
        if not isinstance(x, (int, float)) or not math.isfinite(x):
            return dict(candidate=None, classification="Not Evaluable", reason="nonfinite_input")
    if step_s <= 0:
        return dict(candidate=None, classification="Not Evaluable", reason="nonpositive_step")
    if v0 < 0 or v1 < 0:
        return dict(candidate=None, classification="Not Evaluable", reason="negative_reported_speed")
    if is_action:
        if v1 > 0:
            return dict(candidate=v1, classification="Exact Observable",
                        reason="action_step_positive_terminal_speed_no_clamp")
        return dict(candidate=None, classification="Bounded Consistency Only",
                    reason="action_step_terminal_stop_clamped_public_acceleration")
    u = v0 + a_pub_start * step_s
    return dict(candidate=u, classification="Exact Reconstructable Under Verified Conditions",
                reason="non_action_acceleration_continuation")


def expected_displacement(v0, u, step_s):
    """Official ballistic displacement for a known signed candidate terminal speed.

    Mirrors MSVehicle::getDeltaPos for the ballistic (non-Euler) branch.
    """
    a = (u - v0) / step_s
    if u >= 0:
        return (v0 + u) / 2.0 * step_s
    # stop within step: t_stop=-v0/a, dx = v0*t_stop + .5*a*t_stop^2 = -v0^2/(2a)
    return -v0 * v0 / (2.0 * a)


def prove_clamp_non_injective(v0, u1, u2, step_s):
    """Demonstrate that two distinct negative candidates u1,u2 (<0) produce the SAME
    public terminal speed and the SAME public mean acceleration, hence public
    observables cannot recover u. This is a structural proof, not a measurement."""
    if not (u1 < 0 and u2 < 0 and u1 != u2 and v0 > 0):
        raise ValueError("proof requires distinct negative candidates and positive v0")
    def public(u):
        return dict(v_public=max(u, 0.0), a_public=(max(u, 0.0) - v0) / step_s)
    p1, p2 = public(u1), public(u2)
    d1 = expected_displacement(v0, u1, step_s)
    d2 = expected_displacement(v0, u2, step_s)
    return dict(v_public_equal=p1["v_public"] == p2["v_public"] == 0.0,
                a_public_equal=math.isclose(p1["a_public"], p2["a_public"], rel_tol=0, abs_tol=1e-15),
                displacements_differ=not math.isclose(d1, d2, rel_tol=0, abs_tol=1e-15),
                public_record=p1, u1=u1, u2=u2,
                displacement_u1_m=d1, displacement_u2_m=d2)
