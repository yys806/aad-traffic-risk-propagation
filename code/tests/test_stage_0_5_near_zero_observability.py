"""Independent analytic near-zero truths; no real or historical traffic input."""
from copy import deepcopy
import math
import pytest

from riskprop.stage_0_5_near_zero_observability import (
    EPSILON_NUMERICAL, POSITION_EPS_M, TOLERANCE_M, SOURCE_PROOF_KEYS,
    candidate_speeds, context_from_public, audit_transition, execution_scope,
)


def proof(**changes):
    p={k:True for k in SOURCE_PROOF_KEYS};p.update(changes);return p


def state(t=.05,v=.2,a=-4.,x=10.,edge="e",lane="e_0"):
    return dict(run_id="r",vehicle_id="v",incarnation_id="r|v",time_s=t,
                speed_mps=v,acceleration_mps2=a,position_m=x,edge_id=edge,lane_id=lane,
                last_action_time_s=0.,traci_vehicle_control=False,numerical_config_verified=True,
                remaining_stops=[],input_has_stops=False,route_edges=["e"],route_index=0)


@pytest.mark.parametrize("u,context,final,category",[
    (.1,True,.1,"Exact Without Postprocessing"),
    (6e-6,True,6e-6,"Exact Without Postprocessing"),
    (4e-6,True,0.,"Exact After Verified Postprocessing"),
    (4e-6,False,4e-6,"Exact Without Postprocessing"),
    (-4e-6,True,0.,"Exact After Verified Postprocessing"),
    (-4e-6,False,-4e-6,"Exact Without Postprocessing"),
    (-.1,True,-.1,"Exact Without Postprocessing"),
    (0.,None,0.,"Exact Without Postprocessing"),
])
def test_independent_candidate_truth_table(u,context,final,category):
    # Deliberately use v0=0, a=u/h; acceleration continuation does not read dx.
    r=candidate_speeds(0.,u/.05,.05,is_action=False,public_terminal=max(final,0.),context=context)
    assert r["classification"]==category
    assert r["u_final"]==pytest.approx(final,abs=1e-18)


@pytest.mark.parametrize("sign",[1,-1])
def test_threshold_is_strict_in_both_directions(sign):
    eps=.1*EPSILON_NUMERICAL*.05
    # Public v0 is nonnegative; a signed negative candidate comes from braking.
    acceleration=0. if sign>0 else -2*eps/.05
    r=candidate_speeds(eps,acceleration,.05,is_action=False,public_terminal=max(sign*eps,0.),context=True)
    assert r["u_final"]==sign*eps and r["classification"]=="Exact Without Postprocessing"


@pytest.mark.parametrize("u",[4e-6,-4e-6])
@pytest.mark.parametrize("public",[0.,4e-6])
def test_unknown_context_never_selected_using_reported_terminal(u,public):
    r=candidate_speeds(.01,(u-.01)/.05,.05,is_action=False,public_terminal=public,context=None)
    assert r["classification"]=="Near-Zero Context Unresolved"
    assert r["u_final"] is None and r["u_pre"]==pytest.approx(u)
    assert r["possible_final_candidates"]==pytest.approx([u,0.])


def test_unknown_is_not_false_and_false_does_not_snap():
    for context in [None,False]:
        r=candidate_speeds(.000004,0.,.05,is_action=False,public_terminal=0.,context=context)
        assert r["u_final"] is None if context is None else r["u_final"]==.000004


@pytest.mark.parametrize("bad",[None,0,1,"False",[],{}])
def test_invalid_decision_identity_never_enters_nonaction(bad):
    r=candidate_speeds(.1,-2.,.05,is_action=bad,public_terminal=0.,context=True)
    assert r["classification"]=="Not Evaluable" and r["u_final"] is None


def test_source_no_stops_invariant_is_true_not_false_context():
    a=state();b=dict(a,time_s=.1)
    c=context_from_public(a,b,proof(),is_action=False)
    assert c["predicate"] is True and c["basis"]=="fresh_no_stops_stopdist_doublemax_invariant"


@pytest.mark.parametrize("missing",SOURCE_PROOF_KEYS)
def test_no_stops_public_getter_alone_is_not_complete_proof(missing):
    a=state();b=dict(a,time_s=.1)
    assert context_from_public(a,b,proof(**{missing:False}),is_action=False)["predicate"] is None


def test_same_edge_regular_stop_proves_second_disjunct_on_nonaction():
    a=state();a.update(input_has_stops=True,remaining_stops=[dict(lane="e_0",edge="e",end_pos_m=80.,ordinary=True)])
    b=dict(a,time_s=.1)
    c=context_from_public(a,b,proof(),is_action=False)
    assert c["predicate"] is True and c["basis"]=="stable_same_route_edge_regular_stop_nonaction"
    assert context_from_public(a,b,proof(),is_action=True)["predicate"] is None


def test_other_edge_or_filtered_unknown_stops_not_equated_to_stopdist():
    a=state();a.update(input_has_stops=True,remaining_stops=[dict(lane="other_0",edge="other",end_pos_m=80.,ordinary=True)])
    assert context_from_public(a,dict(a,time_s=.1),proof(),is_action=False)["predicate"] is None
    a["remaining_stops"]=None
    assert context_from_public(a,dict(a,time_s=.1),proof(),is_action=False)["predicate"] is None


def test_context_is_independent_of_speed_and_tested_displacement():
    a=state();b=dict(a,time_s=.1)
    expected=context_from_public(a,b,proof(),is_action=False)
    b.update(speed_mps=123.,position_m=100000.)
    assert context_from_public(a,b,proof(),is_action=False)==expected


def test_independent_positive_snap_uses_postprocessed_ballistic_velocity():
    a=state(v=6e-6,a=-4e-5);b=state(t=.1,v=0.,a=-1.2e-4,x=10.+1.5e-7)
    r=audit_transition(a,b,proof())
    assert r["classification"]=="Exact After Verified Postprocessing" and r["exact_pass"]
    assert r["u_pre"]==pytest.approx(4e-6) and r["u_final"]==0.
    assert r["expected_dx_m"]==pytest.approx(1.5e-7,abs=1e-16)


def test_nonaction_early_stop_uses_start_not_end_acceleration():
    a=state(v=.1,a=-4.);b=state(t=.1,v=0.,a=-2.,x=10.00125)
    r=audit_transition(a,b,proof())
    assert r["u_final"]==pytest.approx(-.1) and r["exact_pass"]


def test_decision_stop_bounded_not_exact_and_boundary_violation_blocks():
    a=state(t=0.,v=.2);b=state(t=.05,v=0.,x=10.002)
    r=audit_transition(a,b,proof())
    assert r["classification"]=="Bounded Consistency Only" and r["exact_pass"] is None
    assert r["within_support"] and r["residual_m"] is None
    b["position_m"]=10.006
    assert audit_transition(a,b,proof())["classification"]=="Engineering Blocker"


def test_unknown_context_keeps_source_derived_two_branch_support():
    a=state(v=.01,a=(4e-6-.01)/.05);a["input_has_stops"]=True
    b=dict(a,time_s=.1,speed_mps=0.,position_m=10.+.00025)
    r=audit_transition(a,b,proof())
    assert r["classification"]=="Near-Zero Context Unresolved"
    assert r["residual_m"] is None and r["exact_pass"] is None
    assert r["dx_support_m"][0]==pytest.approx(.00025)
    assert r["dx_support_m"][1]==pytest.approx(.0002501)
    b["position_m"]=10.1
    assert audit_transition(a,b,proof())["blocker"]=="near_zero_necessary_support_violation"


def test_stationary_and_restart_are_observable_without_inverting_hidden_speed():
    a=state(t=0.,v=0.,a=0.);b=state(t=.05,v=0.,a=0.,x=10.)
    assert audit_transition(a,b,proof())["exact_pass"]
    b.update(speed_mps=.1,position_m=10.0025)
    assert audit_transition(a,b,proof())["exact_pass"]


@pytest.mark.parametrize("key,value,reason",[
    ("incarnation_id","wrong","identity_discontinuity"),
    ("time_s",.2,"internal_clock_inconsistent"),
    ("last_action_time_s",None,"action_clock_unknown"),
    ("traci_vehicle_control",None,"vehicle_control_unconfirmed"),
    ("traci_vehicle_control",True,"vehicle_control_unconfirmed"),
    ("numerical_config_verified",False,"numerical_configuration_unconfirmed"),
])
def test_invalid_shared_state_is_global_blocker(key,value,reason):
    a=state(v=10.,a=-2.);b=dict(a,time_s=.1,speed_mps=9.9,position_m=10.4975);b[key]=value
    r=audit_transition(a,b,proof())
    assert r["blocker"]==reason and r["scope"]=="Global Blocker"


@pytest.mark.parametrize("changes",[{"edge_id":"next","lane_id":"next_0","position_m":.1},{"lane_id":"e_1"}])
def test_legal_coordinate_changes_never_fabricate_zero_residual(changes):
    a=state(v=10.,a=-2.);b=dict(a,time_s=.1,speed_mps=9.9,position_m=10.4975);b.update(changes)
    r=audit_transition(a,b,proof())
    assert r["classification"]=="Not Evaluable" and r["residual_m"] is None and r["blocker"] is None


def test_exact_velocity_and_displacement_violations_cannot_be_hidden():
    a=state(v=10.,a=-2.);b=dict(a,time_s=.1,speed_mps=8.,position_m=10.4975)
    assert audit_transition(a,b,proof())["blocker"]=="final_public_velocity_inconsistent"
    b["speed_mps"]=9.9;b["position_m"]=10.51
    assert audit_transition(a,b,proof())["blocker"]=="exact_displacement_violation"


def test_stop_scope_does_not_tie_scenario_queue_evidence_to_D_execution():
    assert execution_scope("queue_continuity_insufficient")=="Evidence Insufficient"
    assert execution_scope("D_no_required_lane_change")=="Scenario-Specific Blocker"
    assert execution_scope("exact_displacement_violation")=="Global Blocker"
    assert execution_scope("unknown_failure")=="Global Blocker"


def test_fixed_tolerance_and_no_displacement_to_velocity_API():
    import inspect
    assert TOLERANCE_M==1e-6 and POSITION_EPS_M==.1 and EPSILON_NUMERICAL==.001
    assert "displacement" not in inspect.signature(candidate_speeds).parameters
    assert "position" not in inspect.signature(candidate_speeds).parameters
