"""Independent analytic truth, not B1 traffic trajectories."""
import copy
import pytest
from riskprop.stage_0_5_stopping_contract import audit_edge, AuditAccumulator, cohort_member


def edge(v0,v1,dx,dt=.1):
    a=dict(run_id="analytic",vehicle_id="v",incarnation_id="analytic|v|0",time_s=1.,edge_id="e",lane_id="e_0",position_m=20.,speed_mps=v0)
    b=dict(a,time_s=1+dt,position_m=20+dx,speed_mps=v1)
    return a,b


@pytest.mark.parametrize("v0,v1,dx,branch",[(10,10,1.,"normal_motion"),(10,10.2,1.01,"normal_motion"),
    (10,9.8,.99,"decelerating_without_stop"),(0,0,0,"already_stopped"),(0,.2,.01,"starting_from_rest"),
    (1e-10,2e-10,1.5e-11,"normal_motion")])
def test_exact_endpoint_branches(v0,v1,dx,branch):
    a,b=edge(v0,v1,dx);r=audit_edge(a,b,.1)
    assert r["branch"]==branch and r["exact_evaluable"]
    assert abs(r["residual_m"])<1e-12 and not r["anomaly"]


def test_known_step_end_stop_is_exact_only_with_independent_candidate():
    a,b=edge(.2,0,.01)
    r=audit_edge(a,b,.1,signed_candidate=dict(value=0.,origin="analytic_input"))
    assert r["branch"]=="stopping_at_step_end" and r["expected_dx_m"]==pytest.approx(.01)
    assert r["exact_evaluable"]


@pytest.mark.parametrize("dt",[.05,.1,.2])
def test_known_within_step_stop_uses_half_triangle_until_stop(dt):
    # v0=.2, actual braking4 m/s^2 -> stop at.05s and distance.005m.
    a,b=edge(.2,0,.005,dt)
    r=audit_edge(a,b,dt,signed_candidate=dict(value=.2-4*dt,origin="analytic_input"))
    assert r["expected_dx_m"]==pytest.approx(.005)
    assert r["stop_time_s"]==pytest.approx(.05)
    assert not r["anomaly"]
    if dt>.05:assert r["old_trapezoid_residual_m"]<0


def test_traci_mean_acceleration_cannot_reconstruct_signed_candidate():
    a,b=edge(.2,0,.005);b["reported_acceleration_mps2"]=-2.
    r=audit_edge(a,b,.1)
    assert not r["exact_evaluable"] and r["expected_dx_m"] is None
    assert r["stop_time_s"] is None and r["residual_m"] is None
    assert r["dx_bounds_m"]==pytest.approx([0,.01])
    assert r["status"]=="bounded_consistency_only" and r["equivalence"]=="Pending Numerical Equivalence"
    assert not r["anomaly"]


def test_displacement_derived_candidate_is_refused_as_circular():
    a,b=edge(.2,0,.005)
    with pytest.raises(ValueError):audit_edge(a,b,.1,signed_candidate=dict(value=-.2,origin="inferred_from_displacement"))


@pytest.mark.parametrize("field,value,branch",[("incarnation_id","other","insufficient_observation"),
    ("vehicle_id","other","insufficient_observation"),("edge_id","next","edge_or_lane_transition"),
    ("lane_id","e_1","edge_or_lane_transition"),("time_s",1.2,"insufficient_observation"),
    ("speed_mps",float("nan"),"insufficient_observation")])
def test_discontinuities_not_subtracted(field,value,branch):
    a,b=edge(10,10,1);b[field]=value;r=audit_edge(a,b,.1)
    assert r["branch"]==branch and not r["exact_evaluable"] and r["residual_m"] is None


def test_outside_stop_bounds_and_normal_residual_are_not_silently_passed():
    a,b=edge(.2,0,.02);r=audit_edge(a,b,.1)
    assert r["anomaly"] and r["bound_violation_m"]==pytest.approx(.01)
    a,b=edge(10,10,1.000002);r=audit_edge(a,b,.1)
    assert r["anomaly"] and r["residual_m"]>1e-6


def test_all_edge_maximum_not_hidden_by_cohort_or_bounded_records():
    acc=AuditAccumulator(anomaly_limit=2,quantile_limit=3,cohort_modulus=7)
    for i in range(20):
        a,b=edge(10,10,1+i*.001);a["vehicle_id"]=b["vehicle_id"]=f"v{i}"
        a["incarnation_id"]=b["incarnation_id"]=f"run|v{i}"
        acc.add(audit_edge(a,b,.1))
    s=acc.summary()
    assert s["all_edges"]==20 and s["screened_fraction"]==1
    stat=s["branches"]["normal_motion"]
    assert stat["max_abs_residual_m"]==pytest.approx(.019)
    assert stat["anomalies"]==19 and stat["quantile_sample_n"]<=3
    assert len(s["anomaly_edges"])==2 and s["anomaly_edges"][0]["residual_m"]==pytest.approx(.019)
    assert s["anomaly_edges_not_retained"]==17


def test_hash_membership_stable_when_other_vehicles_enter_or_leave():
    expected={f"run|v{i}":cohort_member("run",f"run|v{i}",5) for i in range(20)}
    assert expected=={k:cohort_member("run",k,5) for k in reversed(expected)}
    assert any(expected.values()) and not all(expected.values())


def test_residual_quantile_sample_does_not_depend_on_processing_order():
    rows=[]
    for i in range(20):
        a,b=edge(10,10,1+i*.00001);a["incarnation_id"]=b["incarnation_id"]=str(i)
        rows.append(audit_edge(a,b,.1))
    aa=AuditAccumulator(quantile_limit=5);bb=AuditAccumulator(quantile_limit=5)
    for r in rows:aa.add(r)
    for r in reversed(rows):bb.add(r)
    for key in ["median_abs_residual_m","p95_abs_residual_m","max_abs_residual_m"]:
        assert aa.summary()["branches"]["normal_motion"][key]==bb.summary()["branches"]["normal_motion"][key]
