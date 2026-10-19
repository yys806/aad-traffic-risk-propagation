"""B1.2-P positive-only evidence chain, separate from general numerical coverage."""
from __future__ import annotations
from .stage_0_5_near_zero_observability import audit_transition

VERSION="b12p-positive-near-zero-v1"

def classify_edge(before,after,proof,*,bindings_verified):
    r=audit_transition(before,after,proof)
    r['numerical_classification']=r['classification']
    r.update(target_exact_pass=False,target_candidate=False,admission_links={})
    if bindings_verified is not True:
        r.update(classification='Engineering Blocker',blocker='source_input_binding_unverified');return r
    u=r['u_pre'];eps=r['near_zero_threshold_mps']
    positive=r['is_action'] is False and u is not None and 0<u<eps
    r['target_candidate']=positive
    if r['blocker']:return r
    if r['classification'] in ['Bounded Consistency Only','Near-Zero Context Unresolved','Not Evaluable']:return r
    if not positive:r['classification']='Not Target Branch';return r
    # Actual terminal must be EXACTLY zero; the old auxiliary velocity comparison
    # is not enough to award this task's target admission.
    if after['speed_mps']!=0.:
        r.update(classification='Engineering Blocker',blocker='positive_snap_public_not_zero');return r
    links=dict(actual_positive_below_strict_threshold=positive,nonaction_step=r['is_action'] is False,
        context_independently_proven=r['context'] is True and r['context_evidence']['basis']=='fresh_no_stops_stopdist_doublemax_invariant',
        no_control_or_postprocessing_override=all(proof.get(k) is True for k in ['fresh_vehicle_lifecycle','no_state_restore','no_special_devices','no_dynamic_stop_mutation','no_route_mutation','no_collision_or_teleport']) and all(s['traci_vehicle_control'] is False for s in [before,after]),
        actual_public_terminal_zero=after['speed_mps']==0.,
        source_final_branch_and_displacement_exact=r['u_final']==0. and r['numerical_classification']=='Exact After Verified Postprocessing' and r['exact_pass'] is True,
        source_input_SHA_verified=bindings_verified is True)
    r['admission_links']=links;r['target_exact_pass']=all(links.values())
    r['classification']='Exact Pass' if r['target_exact_pass'] else 'Near-Zero Context Unresolved'
    if not r['target_exact_pass']:r.update(residual_m=None,exact_pass=None)
    return r

def admission(summaries):
    count=sum(s['target_exact_count'] for s in summaries)
    blockers=[b for s in summaries for b in s['engineering_blockers']]
    return dict(target_branch_verified=count>0 and not blockers,target_exact_count=count,
                target_status='Verified in restricted runtime domain' if count>0 and not blockers else 'Engineering Blocker' if blockers else 'Not Observed',
                engineering_blockers=blockers,C_D_allowed=False,main_matrix_allowed=False,
                future_numerical_policy_approved=False,scientific_claim_eligible=False)

def check_plan(plan):
    runs=plan.get('runs',[]);kinds=[r.get('kind') for r in runs]
    if plan.get('version')!='b12p-plan-v1' or plan.get('C_D_allowed') is not False or plan.get('main_matrix_allowed') is not False:
        raise PermissionError('positive micro task only')
    if not 1<=len(runs)<=5 or len(set(kinds))!=len(kinds) or any(k not in ['P1','P2','P3','P4','P5'] for k in kinds):raise PermissionError('fixed unique probe budget')
    if any(type(r.get('duration_s')) not in [int,float] or not 0<r['duration_s']<=30 or r.get('seed')!=20261019 for r in runs):raise PermissionError('duration/seed scope')
