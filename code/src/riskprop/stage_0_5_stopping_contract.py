"""B1.1 independent displacement audit. No TTC/P2 definitions are changed."""
from __future__ import annotations
import hashlib
import heapq
import math

VERSION="b11-displacement-v1"
TOLERANCE_M=1e-6


def cohort_member(run_id,incarnation_id,modulus=1):
    if modulus<1:raise ValueError("positive cohort modulus required")
    return int(hashlib.sha256(f"{run_id}|{incarnation_id}".encode()).hexdigest(),16)%modulus==0


def audit_edge(before,after,step_s,*,signed_candidate=None,tolerance_m=TOLERANCE_M):
    """Exact normal displacement or partial identification of a terminal stop.

    signed_candidate is admissible only from independent analytic input or an
    instrumented signed-vNext trace. TraCI mean acceleration is deliberately not
    used to fabricate that hidden variable. A bounded stop is NOT exact Pass.
    """
    r=dict(version=VERSION,run_id=after.get("run_id"),vehicle_id=after.get("vehicle_id"),
        incarnation_id=after.get("incarnation_id"),before=dict(before),after=dict(after),step_s=step_s,
        branch="insufficient_observation",status="not_evaluable",reason=None,exact_evaluable=False,
        expected_dx_m=None,actual_dx_m=None,residual_m=None,dx_bounds_m=None,bound_violation_m=None,
        stop_time_s=None,old_trapezoid_residual_m=None,anomaly=False,equivalence="Pending Numerical Equivalence")
    def insufficient(reason,branch="insufficient_observation"):
        r.update(reason=reason,branch=branch);return r
    for key in ["run_id","vehicle_id","incarnation_id"]:
        if before.get(key) is None or before.get(key)!=after.get(key):return insufficient("identity_discontinuity:"+key)
    for key in ["time_s","speed_mps","position_m"]:
        if not all(isinstance(s.get(key),(int,float)) and math.isfinite(s[key]) for s in [before,after]):return insufficient("nonfinite_or_missing:"+key)
    if step_s<=0 or abs(after["time_s"]-before["time_s"]-step_s)>1e-9:return insufficient("not_one_internal_step")
    if min(before["speed_mps"],after["speed_mps"])<0:return insufficient("negative_reported_speed")
    for key in ["edge_id","lane_id"]:
        if before.get(key) is None or before.get(key)!=after.get(key):return insufficient("coordinate_transition:"+key,"edge_or_lane_transition")
    if before.get("position_discontinuity") or after.get("position_discontinuity"):return insufficient("explicit_position_discontinuity")
    v0=before["speed_mps"];v1=after["speed_mps"];dx=after["position_m"]-before["position_m"]
    trapezoid=.5*(v0+v1)*step_s
    r.update(actual_dx_m=dx,old_trapezoid_residual_m=dx-trapezoid)
    if signed_candidate is not None:
        if signed_candidate.get("origin") not in ["analytic_input","debug_signed_vnext"]:raise ValueError("candidate must be independently observed, never displacement-derived")
        raw=signed_candidate["value"]
        if not math.isfinite(raw) or abs(max(0,raw)-v1)>1e-10:raise ValueError("candidate incompatible with reported terminal speed")
        r["signed_candidate_evidence"]=dict(signed_candidate)
        if raw<0 and v0>0:
            acceleration=(raw-v0)/step_s;stop=-v0/acceleration
            expected=-v0*v0/(2*acceleration)
            r.update(branch="stopping_within_step",stop_time_s=stop)
        else:
            expected=trapezoid
            r["branch"]="stopping_at_step_end" if v0>0 and raw==0 else "already_stopped" if v0==v1==0 else "starting_from_rest" if v0==0 else "decelerating_without_stop" if v1<v0 else "normal_motion"
            if r["branch"]=="stopping_at_step_end":r["stop_time_s"]=step_s
    elif v0>0 and v1==0:
        upper=.5*v0*step_s;violation=max(0.,-dx,dx-upper)
        r.update(branch="stopping_timing_unresolved",status="bounded_consistency_only",reason="signed_vnext_and_braking_acceleration_not_observed",
            dx_bounds_m=[0.,upper],bound_violation_m=violation,anomaly=violation>tolerance_m)
        return r
    else:
        expected=trapezoid
        r["branch"]="already_stopped" if v0==v1==0 else "starting_from_rest" if v0==0 else "decelerating_without_stop" if v1<v0 else "normal_motion"
    residual=dx-expected
    r.update(exact_evaluable=True,expected_dx_m=expected,residual_m=residual,
        status="exact_check_failed" if abs(residual)>tolerance_m else "exact_check_passed",
        anomaly=abs(residual)>tolerance_m,equivalence="Exact applicable branch check")
    return r


def _quantile(values,q):
    if not values:return None
    x=sorted(values);p=(len(x)-1)*q;a=int(p);b=min(a+1,len(x)-1)
    return x[a]+(x[b]-x[a])*(p-a)


class AuditAccumulator:
    """All-edge screening; bounded top anomalies and deterministic quantiles.

    No cohort can hide the full-population maximum. Quantiles are explicitly
    sample quantiles when more than quantile_limit exact edges exist.
    """
    def __init__(self,anomaly_limit=16,quantile_limit=2048,cohort_modulus=1):
        self.limit=anomaly_limit;self.quantile_limit=quantile_limit;self.modulus=cohort_modulus
        self.count=0;self.branches={};self.anomalies=[];self.anomaly_count=0;self.detail_cohort=0;self.samples={};self.examples={}

    def add(self,row):
        self.count+=1;b=row["branch"]
        s=self.branches.setdefault(b,dict(checks=0,exact_evaluable=0,bounded_evaluable=0,not_evaluable=0,
            anomalies=0,max_abs_residual_m=None,max_bound_violation_m=None,positive_residuals=0,negative_residuals=0,zero_residuals=0,reasons={}))
        s["checks"]+=1;s["exact_evaluable"]+=row["exact_evaluable"]
        s["bounded_evaluable"]+=row["status"]=="bounded_consistency_only"
        s["not_evaluable"]+=row["status"]=="not_evaluable"
        if row["reason"]:s["reasons"][row["reason"]]=s["reasons"].get(row["reason"],0)+1
        self.detail_cohort+=cohort_member(row["run_id"],row["incarnation_id"],self.modulus)
        key=f'{row["run_id"]}|{row["incarnation_id"]}|{row["before"].get("time_s")}|{row["after"].get("time_s")}'
        rank=int(hashlib.sha256(key.encode()).hexdigest(),16)
        self.examples.setdefault(b,[])
        if len(self.examples[b])<2:self.examples[b].append(row)
        if row["residual_m"] is not None:
            v=row["residual_m"];absolute=abs(v)
            if s["max_abs_residual_m"] is None or absolute>=s["max_abs_residual_m"]:s["worst_edge"]=row
            s["max_abs_residual_m"]=max(s["max_abs_residual_m"] or 0,absolute)
            s["positive_residuals" if v>0 else "negative_residuals" if v<0 else "zero_residuals"]+=1
            sample=self.samples.setdefault(b,[]);item=(-rank,self.count,absolute)
            if len(sample)<self.quantile_limit:heapq.heappush(sample,item)
            elif item>sample[0]:heapq.heapreplace(sample,item)
        if row["bound_violation_m"] is not None:s["max_bound_violation_m"]=max(s["max_bound_violation_m"] or 0,row["bound_violation_m"])
        if row["anomaly"]:
            self.anomaly_count+=1;s["anomalies"]+=1
            severity=max(abs(row["residual_m"] or 0),row["bound_violation_m"] or 0)
            item=(severity,self.count,row)
            if len(self.anomalies)<self.limit:heapq.heappush(self.anomalies,item)
            elif item[:2]>self.anomalies[0][:2]:heapq.heapreplace(self.anomalies,item)

    def summary(self):
        result={}
        for b,s in self.branches.items():
            values=[v for _,_,v in self.samples.get(b,[])]
            result[b]=dict(s,quantile_sample_n=len(values),quantile_population_n=s["exact_evaluable"],
                quantiles_are_sample_based=len(values)<s["exact_evaluable"],median_abs_residual_m=_quantile(values,.5),
                p95_abs_residual_m=_quantile(values,.95),p99_abs_residual_m=_quantile(values,.99))
        return dict(version=VERSION,all_edges=self.count,screened_fraction=1. if self.count else None,
            detail_cohort_edges=self.detail_cohort,cohort_modulus=self.modulus,branches=result,
            anomaly_edges=[r for _,_,r in sorted(self.anomalies,reverse=True)],anomalies=self.anomaly_count,
            anomaly_edges_not_retained=self.anomaly_count-len(self.anomalies),examples=self.examples,
            limitations=["No precision proof for terminal-stop exact displacement without independent signed vNext",
                "One-step endpoints cannot detect an unflagged teleport that mimics motion",
                "Coordinate transitions explicitly not evaluated; no local-position subtraction across edges/lanes",
                "Quantile sketches are bounded deterministic samples; maxima/anomaly counts screen every observed edge"])
