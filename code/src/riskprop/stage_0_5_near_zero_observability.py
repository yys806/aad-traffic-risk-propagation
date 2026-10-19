"""B1.2-N candidate contract: independently qualified near-zero postprocessing.

u_pre is distinct from u_final and public max(u_final,0). Displacement and the
reported terminal speed NEVER select the private stop-context predicate.
This module does not modify the sealed B1/B1.1/B1.1-S/B1.2 implementations.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import math

from .stage_0_5_stopping_observability import step_is_action,expected_displacement

VERSION="b12n-near-zero-observability-v1"
EPSILON_NUMERICAL=.001
POSITION_EPS_M=.1
TOLERANCE_M=1e-6
PUBLIC_SPEED_CHECK_MPS=1e-9
CLASSES=("Exact After Verified Postprocessing","Exact Without Postprocessing",
         "Bounded Consistency Only","Near-Zero Context Unresolved","Not Evaluable","Engineering Blocker")
SOURCE_PROOF_KEYS=("official_source_contract_verified","fresh_vehicle_lifecycle","no_state_restore",
                   "no_dynamic_stop_mutation","no_route_mutation","no_collision_or_teleport",
                   "no_special_devices","noncyclic_route_verified","ordinary_stop_definition_verified")


def execution_scope(reason):
    if reason in ("queue_continuity_insufficient","entry_spillback_insufficient","near_zero_context_unresolved"):
        return "Evidence Insufficient"
    if reason in ("D_no_required_lane_change","D_no_downstream_exit","scenario_network_invalid"):
        return "Scenario-Specific Blocker"
    if reason in ("legal_edge_transition","legal_lane_change","onroad_low_speed","external_pending"):
        return "Diagnostic Warning"
    return "Global Blocker"


def context_from_public(before,after,proof,*,is_action):
    """Sufficient source proofs, NOT a general TraCI myStopDist equivalence.

    No-stops invariant: constructor/reset sets doubleMax; planMoveInternal only
    replaces it with a finite value for the first scheduled stop. No state load,
    dynamic stops, collisions, devices or route mutation is permitted here.
    Same-edge proof is used only on NON-action steps, which skip finalizeSpeed
    (and thus its processNextStop mutation), with a stable regular stop list.
    """
    unknown=dict(predicate=None,basis="Near-Zero Context Unresolved",
                 missing=["independent execution-time stop-distance/first-stop route-context proof"])
    if not all(proof.get(k) is True for k in SOURCE_PROOF_KEYS):return unknown
    a=before.get("remaining_stops");b=after.get("remaining_stops")
    if not isinstance(a,list) or not isinstance(b,list):return unknown
    if before.get("input_has_stops") is False and after.get("input_has_stops") is False and not a and not b:
        return dict(predicate=True,basis="fresh_no_stops_stopdist_doublemax_invariant",missing=[])
    if is_action is not False or not a or not b or a!=b:return unknown
    route=before.get("route_edges");index=before.get("route_index")
    if not isinstance(route,list) or len(set(route))!=len(route) or type(index) is not int or not 0<=index<len(route):return unknown
    edge=before.get("edge_id")
    if edge!=route[index] or after.get("edge_id")!=edge:return unknown
    if a[0].get("ordinary") is True and a[0].get("edge")==edge:
        return dict(predicate=True,basis="stable_same_route_edge_regular_stop_nonaction",missing=[])
    return unknown


def candidate_speeds(v0,a_start,h,*,is_action,public_terminal,context):
    """Context True/False is independent truth; runtime must use qualified proof.

    False is available to analytic fixtures. The live public-interface qualifier
    never invents False from an empty getStops list. Unknown remains Unknown
    even when only one candidate matches public_terminal.
    """
    r=dict(u_pre=None,u_final=None,classification="Not Evaluable",reason=None,
           near_zero_threshold_mps=None,possible_final_candidates=None)
    if type(is_action) is not bool:r["reason"]="decision_identity_not_boolean";return r
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (v0,a_start,h,public_terminal)) or h<=0 or min(v0,public_terminal)<0:
        r["reason"]="invalid_numeric_input";return r
    if context is not None and type(context) is not bool:r["reason"]="context_predicate_not_boolean";return r
    eps=.1*EPSILON_NUMERICAL*h;r["near_zero_threshold_mps"]=eps
    if is_action:
        if public_terminal>0:r.update(u_final=public_terminal,classification="Exact Without Postprocessing",reason="decision_positive_final_observable_no_overrides")
        elif v0==0:r.update(classification="Exact Without Postprocessing",reason="stationary_displacement_identified_independent_of_hidden_final")
        else:r.update(classification="Bounded Consistency Only",reason="decision_terminal_zero_hidden_signed_candidate")
        return r
    u=v0+a_start*h;r["u_pre"]=u
    if abs(u)>=eps or u==0:
        r.update(u_final=u,classification="Exact Without Postprocessing",reason="outside_strict_snap_interval" if u else "zero_is_postprocessing_fixed_point")
    elif context is True:
        r.update(u_final=0.,classification="Exact After Verified Postprocessing",reason="independently_verified_stop_context_snap")
    elif context is False:
        r.update(u_final=u,classification="Exact Without Postprocessing",reason="independently_false_stop_context_no_snap")
    else:
        r.update(classification="Near-Zero Context Unresolved",reason="near_zero_context_unresolved",possible_final_candidates=[u,0.])
    return r


def audit_transition(before,after,proof,h=.05,action_step=.1):
    r=dict(version=VERSION,classification="Not Evaluable",u_pre=None,u_final=None,context=None,
           context_evidence=None,is_action=None,reason=None,blocker=None,scope=None,
           exact_pass=None,residual_m=None,actual_dx_m=None,expected_dx_m=None,
           dx_support_m=None,within_support=None,near_zero_threshold_mps=.1*EPSILON_NUMERICAL*h)
    def stop(reason,blocking=True):
        r.update(reason=reason,blocker=reason if blocking else None,scope=execution_scope(reason),
                 classification="Engineering Blocker" if blocking else "Not Evaluable")
        return r
    if any(not before.get(k) or before.get(k)!=after.get(k) for k in ("run_id","vehicle_id","incarnation_id")):return stop("identity_discontinuity")
    if any(s.get("traci_vehicle_control") is not False for s in (before,after)):return stop("vehicle_control_unconfirmed")
    if any(s.get("numerical_config_verified") is not True for s in (before,after)):return stop("numerical_configuration_unconfirmed")
    for s in (before,after):
        if any(type(s.get(k)) not in (int,float) or not math.isfinite(s[k]) for k in ("time_s","speed_mps","acceleration_mps2","position_m")):return stop("nonfinite_runtime_observation")
    if h<=0 or abs(after["time_s"]-before["time_s"]-h)>1e-8:return stop("internal_clock_inconsistent")
    action=step_is_action(after.get("last_action_time_s"),before["time_s"],h,action_step);r["is_action"]=action
    if type(action) is not bool:return stop("action_clock_unknown")
    for s in (before,after):
        if s.get("input_has_stops") is False and s.get("remaining_stops"):return stop("unplanned_stop_context")
    ctx=context_from_public(before,after,proof,is_action=action)
    r.update(context=ctx["predicate"],context_evidence=ctx)
    v0=before["speed_mps"];v1=after["speed_mps"]
    selected=candidate_speeds(v0,before["acceleration_mps2"],h,is_action=action,public_terminal=v1,context=ctx["predicate"])
    r.update(selected)
    if selected["classification"]=="Not Evaluable":return stop(selected["reason"])
    u=selected["u_final"]
    if u is not None and abs(max(u,0.)-v1)>PUBLIC_SPEED_CHECK_MPS:return stop("final_public_velocity_inconsistent")
    if not all(s.get(k) for s in (before,after) for k in ("edge_id","lane_id")):return stop("coordinate_identity_missing")
    if before["edge_id"]!=after["edge_id"]:return stop("legal_edge_transition",False)
    if before["lane_id"]!=after["lane_id"]:return stop("legal_lane_change",False)
    dx=after["position_m"]-before["position_m"];r["actual_dx_m"]=dx
    if r["classification"]=="Near-Zero Context Unresolved":
        finals=r["possible_final_candidates"]
        public_support=[max(x,0.) for x in finals]
        if min(abs(v1-x) for x in public_support)>PUBLIC_SPEED_CHECK_MPS:return stop("near_zero_public_support_violation")
        support=sorted(expected_displacement(v0,x,h) for x in finals)
        r.update(dx_support_m=[support[0],support[-1]],within_support=support[0]-TOLERANCE_M<=dx<=support[-1]+TOLERANCE_M,
                 scope="Evidence Insufficient",support_origin="exact two source alternatives {u_pre,0}; neither selected by dx or terminal speed")
        if not r["within_support"]:return stop("near_zero_necessary_support_violation")
        return r
    if r["classification"]=="Bounded Consistency Only":
        upper=.5*v0*h;r.update(dx_support_m=[0.,upper],within_support=-TOLERANCE_M<=dx<=upper+TOLERANCE_M,
                              scope="Diagnostic Warning",support_origin="public terminal clamp implies final<=0; official ballistic necessary range")
        if not r["within_support"]:return stop("bounded_range_violation")
        return r
    expected=0. if u is None else expected_displacement(v0,u,h)
    residual=dx-expected;r.update(expected_dx_m=expected,residual_m=residual,exact_pass=abs(residual)<=TOLERANCE_M)
    if not r["exact_pass"]:return stop("exact_displacement_violation")
    return r


class Coverage:
    def __init__(self):
        self.counts=Counter();self.reasons=Counter();self.contexts=Counter();self.branch_counts=Counter()
        self.exact_checked=0;self.exact_passed=0;self.max_abs_residual=None;self.blockers=Counter();self.examples={};self.locations={};self.worst=None

    def add(self,a,b,proof):
        r=audit_transition(a,b,proof);self.counts[r["classification"]]+=1;self.reasons[r["reason"]]+=1
        if r["context_evidence"]:self.contexts[r["context_evidence"]["basis"]]+=1
        if r["is_action"] is not None:self.branch_counts["action" if r["is_action"] else "nonaction"]+=1
        if r["u_pre"] is not None:
            self.branch_counts["positive_pre" if r["u_pre"]>0 else "negative_pre" if r["u_pre"]<0 else "zero_pre"]+=1
            if r["classification"]=="Exact After Verified Postprocessing":self.branch_counts["positive_snap" if r["u_pre"]>0 else "negative_snap"]+=1
        if r["exact_pass"] is not None:
            self.exact_checked+=1;self.exact_passed+=r["exact_pass"] is True
            value=abs(r["residual_m"])
            if self.max_abs_residual is None or value>self.max_abs_residual:
                self.max_abs_residual=value;self.worst=dict(before=a,after=b,**r)
        if r["blocker"]:self.blockers[r["blocker"]]+=1
        key=r["classification"]+"|"+r["reason"]
        self.examples.setdefault(key,dict(before=a,after=b,**r))
        if r["classification"] in ("Near-Zero Context Unresolved","Not Evaluable","Engineering Blocker"):
            loc_key=r["reason"]+"|"+a["edge_id"]+"|"+a["lane_id"]
            loc=self.locations.setdefault(loc_key,dict(count=0,first_s=b["time_s"],last_s=b["time_s"],vehicle_step_s=0.))
            loc["count"]+=1;loc["last_s"]=b["time_s"];loc["vehicle_step_s"]+=.05
        return r

    def summary(self):
        total=sum(self.counts.values())
        return dict(version=VERSION,all_adjacent_edges=total,classifications={c:dict(count=self.counts[c],fraction=self.counts[c]/total if total else None) for c in CLASSES},
                    exact_checked=self.exact_checked,exact_passed=self.exact_passed,exact_pass_fraction=self.exact_passed/self.exact_checked if self.exact_checked else None,
                    max_abs_residual_m=self.max_abs_residual,tolerance_m=TOLERANCE_M,blockers=dict(self.blockers),reasons=dict(self.reasons),
                    context_bases=dict(self.contexts),branch_counts=dict(self.branch_counts),locations=self.locations,examples=self.examples,worst_exact_edge=self.worst,
                    context_unknown_is_exact=False,threshold_is_internal_SUMO_constant_not_scientific_tolerance=True)
