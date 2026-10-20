"""Independent candidate protocol arithmetic; never changes formal measurement.

Counts are observed event attributions, not approved local P2 results. Spatial
exposure is a proposed restriction of already-evaluable links, not new risk
eligibility. No scientific margin, warmup, or event policy is approved here.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='lf-protocol-candidate-v1'
WINDOWS={'us101__0750_0805','us101__0805_0820'}

def verify_binding(path,digest,role):
    if role not in {'calibration_summary','engineering_state','engineering_summary'}:raise PermissionError('source_role')
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest:raise PermissionError('source_SHA')
    if role=='engineering_state':return None
    data=json.loads(raw)
    if role=='calibration_summary':
        # Deny actual unapproved window keys/values, allowing metadata describing
        # its exclusion. Exact approved source SHA is checked before parsing.
        for key in ['windows','window_summaries','candidate_strata','demand_identifiability']:
            if key in data and set(data[key])!=WINDOWS:raise PermissionError('calibration_window_scope')
        groups=set()
        def walk(node):
            if isinstance(node,dict):
                if 'source_group' in node:groups.add(node['source_group'])
                for value in node.values():walk(value)
            elif isinstance(node,list):
                for value in node:walk(value)
        walk(data)
        if groups and not groups.issubset(WINDOWS):raise PermissionError('unapproved_summary_group')
        if 'windows' not in data and 'window_summaries' not in data and groups!=WINDOWS:raise PermissionError('unrecognised_summary')
    return data

def checked_points(frame):
    m=frame.copy()
    required={'incarnation_id','leader_incarnation_id','vehicle_id','leader_id','time_s','position_m','edge_id','lane_id','in_local',
        'reliable_following_eligible','measurement_status','ttc_valid','ttc_s','identity_break','observation_gap','observation_index'}
    if required-set(m):raise ValueError('missing_point_fields_'+str(sorted(required-set(m))))
    if m[['incarnation_id','time_s']].isna().any().any() or m.duplicated(['incarnation_id','time_s']).any():raise ValueError('ambiguous_identity_time')
    if not np.isfinite(m[['time_s','position_m']].to_numpy(float)).all():raise ValueError('nonfinite_time_or_position')
    for c in ['in_local','reliable_following_eligible','ttc_valid','identity_break','observation_gap']:
        if not m[c].map(lambda v:isinstance(v,(bool,np.bool_))).all():raise ValueError('unknown_boolean_'+c)
    actual=m.edge_id.eq('main_1')&m.lane_id.isin(['main_1_0','main_1_1','main_1_2'])&m.position_m.ge(50.)&m.position_m.lt(250.)
    if not m.in_local.eq(actual).all():raise ValueError('local_membership_conflict')
    return m.sort_values(['incarnation_id','time_s']).reset_index(drop=True)

def exposure_audit(frame,window=None,*,return_clusters=False):
    m=checked_points(frame);p=m.groupby('incarnation_id',sort=False).shift()
    prev=m.incarnation_id.eq(m.incarnation_id.shift());dt=m.time_s-p.time_s
    flags=m.identity_break|m.observation_gap|p.identity_break.ne(False)|p.observation_gap.ne(False)
    clock=(dt-.1).abs().le(1e-6)&(m.observation_index-p.observation_index).eq(1)
    leader=m.leader_incarnation_id.notna()&p.leader_incarnation_id.notna()&m.leader_incarnation_id.eq(p.leader_incarnation_id)&m.leader_id.eq(p.leader_id)
    linked=prev&clock&~flags&leader
    reliable=linked&m.reliable_following_eligible&p.reliable_following_eligible.eq(True)
    quality=m.measurement_status.isin(['valid','not_applicable'])&p.measurement_status.isin(['valid','not_applicable'])
    support=pd.Series(True,index=m.index)
    if window is not None:
        a,b=window
        if not np.isfinite([a,b]).all() or a>=b:raise ValueError('invalid_window')
        support=(p.time_s>=a-1e-9)&(m.time_s<=b+1e-9)
    eligible=reliable&quality&support
    left=p.in_local.eq(True);right=m.in_local
    # Mutually exclusive failed-link reasons; not counting them as zero risk.
    reason=np.full(len(m),'eligible',dtype=object)
    conditions=[(~prev,'no_previous_observation'),(prev&~clock,'clock_or_index_discontinuity'),(prev&clock&flags,'identity_or_observation_flag'),
        (prev&clock&~flags&~leader,'leader_unknown_or_switch'),(linked&~reliable,'unreliable_following'),(reliable&~quality,'invalid_or_missing_measurement'),
        (reliable&quality&~support,'outside_temporal_support')]
    for mask,label in conditions:reason[np.asarray(mask)]=label
    if not m.measurement_status.isin(['valid','not_applicable','invalid','missing']).all():raise ValueError('unknown_measurement_status')
    result=dict(global_evaluable_s=float(eligible.sum()/10),global_reliable_s=float((reliable&support).sum()/10),
        local_both_s=float((eligible&left&right).sum()/10),local_left_s=float((eligible&left).sum()/10),local_right_s=float((eligible&right).sum()/10),
        boundary_crossing_evaluable_s=float((eligible&(left!=right)).sum()/10),excluded_link_reasons=dict(Counter(reason)),
        quality_by_local_point=dict(Counter(m.loc[m.in_local,'measurement_status'])),
        denominator_definition='Inherited reliable same-follower/same-leader 100ms links; both statuses valid/not_applicable. Proposed local support: both observed follower endpoints inside R and full edge inside W.',
        no_lane_change_interruption_added=True,endpoint_support_not_continuous_geometry=True,formal_policy_approved=False)
    if return_clusters:
        result['cluster_local_seconds']=(eligible&left&right).groupby(m.incarnation_id).sum().div(10).to_dict()
    return result

def event_audit(frame,events,window=None):
    m=checked_points(frame);groups={k:g for k,g in m.groupby('incarnation_id',sort=False)}
    rows=[];counts=Counter({k:0 for k in ['onset','confirmation','through_confirmation','through_end']});seen=set();last_end={}
    for index,e in enumerate(sorted(events,key=lambda e:(e['incarnation_id'],e['event_start_s'],e['event_end_s']))):
        inc=e['incarnation_id'];a=float(e['event_start_s']);c=float(e['event_confirm_s']);b=float(e['event_end_s'])
        key=(inc,a,b)
        if key in seen or inc not in groups or c<a or b<c:raise ValueError('event_identity_or_interval')
        seen.add(key)
        g=groups[inc];memb=g[g.time_s.between(a-1e-9,b+1e-9)]
        if len(memb)<3 or abs(memb.time_s.iloc[0]-a)>1e-8 or abs(memb.time_s.iloc[-1]-b)>1e-8:raise ValueError('missing_event_context')
        if inc in last_end and a<=last_end[inc]+1e-9:raise ValueError('overlapping_events')
        last_end[inc]=b
        if not memb.measurement_status.eq('valid').all() or not (memb.ttc_valid&memb.ttc_s.lt(2.)&memb.ttc_s.gt(0)).all():raise ValueError('nonrisk_event_member')
        if not memb.reliable_following_eligible.all() or memb.identity_break.any() or memb.observation_gap.any():raise ValueError('unreliable_event')
        if memb.leader_incarnation_id.isna().any() or memb.leader_incarnation_id.nunique()!=1 or memb.leader_id.nunique()!=1:raise ValueError('event_leader_break')
        if not np.allclose(np.diff(memb.time_s),.1,atol=1e-6,rtol=0) or not memb.observation_index.diff().dropna().eq(1).all():raise ValueError('event_clock_break')
        first_confirm=float(memb.loc[memb.time_s-a>=.2-1e-9,'time_s'].iloc[0]) if b-a>=.2-1e-9 else None
        if first_confirm is None or abs(first_confirm-c)>1e-8:raise ValueError('wrong_confirmation')
        first=memb.iloc[0];conf=memb[(memb.time_s-c).abs()<1e-8].iloc[0];last=memb.iloc[-1]
        before=g[g.time_s<a-1e-9].tail(1)
        onset_context='first_observed_follower_row'
        if len(before):
            p=before.iloc[0]
            if abs(a-p.time_s-.1)>1e-6 or p.identity_break or p.observation_gap:onset_context='prior_clock_or_quality_break'
            elif p.leader_incarnation_id!=first.leader_incarnation_id:onset_context='new_or_unobserved_leader_pair'
            elif p.measurement_status not in ['valid','not_applicable']:onset_context='prior_measurement_unavailable'
            elif not p.ttc_valid or not np.isfinite(p.ttc_s) or p.ttc_s>=2.:onset_context='observed_nonrisk_to_risk'
            else:raise ValueError('unexplained_event_split')
        aW=cW=True
        if window is not None:
            lo,hi=window
            if lo>=hi:raise ValueError('invalid_window')
            aW=lo<=a<hi;cW=lo<=c<hi
        through=bool(memb.loc[memb.time_s<=c+1e-9,'in_local'].all());fully=bool(memb.in_local.all())
        on=bool(first.in_local);cf=bool(conf.in_local)
        for k,v in [('onset',on and aW),('confirmation',cf and cW),('through_confirmation',through and aW),('through_end',fully and aW)]:counts[k]+=int(v)
        crosses=[]
        for j in range(1,len(memb)):
            if memb.in_local.iloc[j]!=memb.in_local.iloc[j-1]:crosses.append(f'{memb.time_s.iloc[j]:.1f}:'+('enter' if memb.in_local.iloc[j] else 'leave'))
        rows.append(dict(event_id=f'E{index+1:04d}',incarnation_id=inc,vehicle_id=first.vehicle_id,leader_incarnation_id=first.leader_incarnation_id,
            start_s=a,confirm_s=c,end_s=b,onset_position_m=float(first.position_m),confirm_position_m=float(conf.position_m),end_position_m=float(last.position_m),
            onset_edge=first.edge_id,onset_lane=first.lane_id,confirm_edge=conf.edge_id,confirm_lane=conf.lane_id,end_edge=last.edge_id,end_lane=last.lane_id,
            onset_inside=on,confirmation_inside=cf,through_confirmation=through,through_end=fully,onset_context=onset_context,
            onset_in_window=aW,confirmation_in_window=cW,confirmation_observed_after_window=bool(window and aW and c>=window[1]),
            boundary_crossings=';'.join(crosses),member_count=len(memb),same_pair_and_clock_verified=True,
            member_support_sha256=hashlib.sha256(memb[['incarnation_id','leader_incarnation_id','time_s','edge_id','lane_id','position_m']].to_csv(index=False).encode()).hexdigest()))
    return rows,dict(counts)

def candidate_rates(counts,exposure):
    d=exposure['local_both_s']
    return {k:dict(observed_events=int(n),evaluable_vehicle_s=d,evaluable_vehicle_h=d/3600.,rate_per_evaluable_vehicle_hour=3600*n/d if d>0 else None,
        status='Proposed audit statistic; not formal result' if d>0 else 'Not Calculated',
        shared_denominator_not_derived_from_events=True,formal_policy_approved=False) for k,n in counts.items()}

def admission(*,difference_ci,margin,approved,support):
    if not approved or margin is None:return dict(status='Awaiting Researcher Decision',gate_pass=False)
    if not support:return dict(status='Evidence Insufficient',gate_pass=False)
    lo,hi=difference_ci
    if not np.isfinite([lo,hi,margin]).all() or margin<=0 or lo>hi:raise ValueError('invalid_admission_input')
    return dict(status='Candidate criterion satisfied' if lo>=-margin and hi<=margin else 'Model discrepancy or imprecision',gate_pass=False)

def cycle_diagnostics(bins,*,relative_margin):
    if relative_margin<=0 or not np.isfinite(relative_margin):raise ValueError('invalid_candidate_margin')
    changes=[];consecutive=0;first=None
    for a,b in zip(bins[:-1],bins[1:]):
        if abs(a['end_s']-b['start_s'])>1e-6:raise ValueError('nonadjacent_cycles')
        dv=abs(b['mean_speed_mps']-a['mean_speed_mps'])/max(abs(a['mean_speed_mps']),1e-12)
        dk=abs(b['density']-a['density'])/max(abs(a['density']),1e-12)
        ok=max(dv,dk)<=relative_margin
        consecutive=consecutive+1 if ok else 0
        if consecutive>=2 and first is None:first=b['end_s']
        changes.append(dict(end_s=b['end_s'],speed_relative_change=dv,density_relative_change=dk,candidate_within_margin=ok))
    global_balanced=all(x['inserted']==x['exited'] for x in bins) and all(b['pending_end']<=a['pending_end'] for a,b in zip(bins[:-1],bins[1:]))
    return dict(relative_margin_engineering_sensitivity=relative_margin,changes=changes,local_candidate_end_s=first,
        network_stationarity_supported=global_balanced,exact_balance_is_only_necessary_not_sufficient=True,
        risk_used_to_choose_warmup=False,scientific_warmup_approved=False,confirmation_rule='Two consecutive phase-aligned cycle-to-cycle speed AND density changes; candidate burn-in ends at third cycle end, not retrospectively at first cycle start')

def validate_plan(batch):
    batch=Path(batch).resolve();p=batch/'experiment_plan.json'
    if hashlib.sha256(p.read_bytes()).hexdigest()!=(batch/'PLAN_SHA256').read_text().strip():raise PermissionError('plan_SHA_mismatch')
    plan=json.loads(p.read_text())
    for name,digest in plan['frozen_files'].items():
        target=(batch/name).resolve()
        if not target.is_relative_to(batch) or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise PermissionError('frozen_binding')
    if plan['new_SUMO_runs']!=0 or plan['scientific_tolerance'] is not None or plan['ABCD_allowed'] or plan['calibration_allowed']:raise PermissionError('unapproved_execution_or_policy')
    return plan

def clustered_rate(counts,seconds,*,seed,resamples):
    n=np.asarray(counts,dtype=float);e=np.asarray(seconds,dtype=float)
    if len(n)!=len(e) or not len(n) or not np.isfinite(np.r_[n,e]).all() or min(n.min(),e.min())<0:raise ValueError('invalid_cluster_totals')
    base=dict(point_rate=float(3600*n.sum()/e.sum()) if e.sum()>0 else None,interval=None,clusters=len(n),resamples=resamples,seed=seed,
        iid_rows_used_as_clusters=False,scope='Conditional trajectory-cluster sensitivity only; interactions, time regime and between-seed uncertainty not covered',
        zero_event_bootstrap_not_evidence_of_zero_risk=bool(n.sum()==0),formal_policy_approved=False)
    if e.sum()==0 or n.sum()==0:return base
    rng=np.random.default_rng(seed);values=[]
    for _ in range(resamples):
        ids=rng.integers(0,len(n),len(n));den=e[ids].sum()
        if den>0:values.append(float(3600*n[ids].sum()/den))
    base['interval']=[float(v) for v in np.quantile(values,[.025,.975])] if values else None
    base['invalid_denominator_resamples']=resamples-len(values)
    return base
