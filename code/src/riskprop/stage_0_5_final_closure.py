"""Approved D1 local attribution over the unchanged Stage 0.2 event core.

Science acceptance is deliberately separate from calculable formal statistics.
No data loader, simulator control, tolerance default or Gate mutation lives here.
"""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd
from .formal_risk_measurement import SOURCE_KEYS, P2_FORMAL_CONFIG, extract_formal_source_events

VERSION='stage-0.5-final-closure-d1-v1'
BOOLS=['identity_uncertain','leader_identity_uncertain','identity_break','observation_gap','leader_matched','ttc_valid','_inside']


def real_region_mask(states):
    """Canonical lane IDs are stored as strings in the real parquet schema."""
    lane=pd.to_numeric(states.lane_id,errors='raise');y=pd.to_numeric(states.y_m,errors='raise')
    if not np.isfinite(lane).all() or not lane.eq(np.floor(lane)).all() or not np.isfinite(y).all():raise ValueError('invalid_real_spatial_schema')
    return lane.isin([1,2,3,4,5])&y.ge(150)&y.lt(350)


def checked(states):
    required=set(SOURCE_KEYS)|set(BOOLS)|{'trajectory_id','leader_trajectory_id','original_row_number','diagnostic_clock_anchor_ms',
        'global_time_ms','frame_id','time_s','measurement_status','_position','ttc_s','drac_mps2','vehicle_id','leader_id'}
    if required-set(states):raise ValueError('missing_fields:'+str(sorted(required-set(states))))
    d=states.copy()
    for key in BOOLS:
        if not d[key].map(lambda x:isinstance(x,(bool,np.bool_))).all():raise ValueError('unknown_boolean:'+key)
    numeric=['time_s','global_time_ms','frame_id','diagnostic_clock_anchor_ms','_position']
    if not np.isfinite(d[numeric].to_numpy(float)).all():raise ValueError('nonfinite_clock_or_position')
    if d[list(SOURCE_KEYS)+['trajectory_id','original_row_number']].isna().any().any():raise ValueError('unknown_identity')
    if d.duplicated([*SOURCE_KEYS,'trajectory_id','time_s']).any():raise ValueError('duplicate_identity_clock')
    if not d.measurement_status.isin(['valid','not_applicable','invalid','missing']).all():raise ValueError('unknown_quality')
    return d.sort_values([*SOURCE_KEYS,'trajectory_id','global_time_ms','frame_id'],kind='stable').reset_index(drop=True)


def links(d,window):
    """Exact vector transcription of audit_stage_0_2_exposure_edges.py.

    In particular the current endpoint's break flags describe the incoming
    link. The previous endpoint's flags must not erase the following link.
    """
    lo,hi=window
    if not np.isfinite([lo,hi]).all() or lo>=hi:raise ValueError('invalid_window')
    keys=[*SOURCE_KEYS,'trajectory_id','leader_trajectory_id','diagnostic_clock_anchor_ms']
    p=d[keys+['time_s','global_time_ms','frame_id','measurement_status','_inside']].shift()
    adjacent=pd.Series(True,index=d.index)
    for key in keys:adjacent &= d[key].notna() & p[key].notna() & d[key].eq(p[key]).fillna(False)
    adjacent &= d.global_time_ms.diff().eq(100)&d.frame_id.diff().eq(1)&d.time_s.diff().sub(.1).abs().lt(1e-9)
    adjacent &= ~d.identity_break&~d.observation_gap
    reliable=d.leader_matched&~d.identity_uncertain&~d.leader_identity_uncertain
    inherited=adjacent&reliable&reliable.shift(fill_value=False)
    quality=d.measurement_status.isin(['valid','not_applicable'])
    evaluable=inherited&quality&quality.shift(fill_value=False)
    full=p.time_s.ge(lo-1e-9)&d.time_s.le(hi+1e-9)
    local=evaluable&d._inside&p._inside.eq(True)&full
    return pd.DataFrame(dict(eligible=evaluable,local=local,in_window=full,
        left_inside=p._inside.eq(True),right_inside=d._inside,previous_s=p.time_s))


def local_p2(states,window):
    d=checked(states);l=links(d,window);lo,hi=window
    _,formal,rejected=extract_formal_source_events(d,P2_FORMAL_CONFIG,return_diagnostics=True)
    # Source + trajectory indexes retain external leader and event history.
    groups=d.groupby([*SOURCE_KEYS,'trajectory_id'],sort=False,dropna=False).indices
    rows=[];counts=dict(onset=0,confirmation=0,through_confirmation=0,through_end=0);confirmation_time=0
    for _,event in formal.iterrows():
        key=tuple(event[k] for k in [*SOURCE_KEYS,'trajectory_id']);g=d.iloc[groups[key]]
        a=float(event.event_start_s);c=float(event.event_confirm_s);b=float(event.event_end_s)
        m=g[g.original_row_number.isin(event.original_row_numbers)]
        if len(m)!=len(event.original_row_numbers):raise ValueError('missing_event_members')
        first=m.iloc[0];last=m.iloc[-1];conf=m.loc[m.time_s.sub(c).abs().lt(1e-8)].iloc[0]
        inside=dict(onset=bool(first._inside),confirmation=bool(conf._inside),
            through_confirmation=bool(m.loc[m.time_s.le(c+1e-9),'_inside'].all()),through_end=bool(m._inside.all()))
        in_w=bool(lo<=a<hi)
        for k,v in inside.items():counts[k]+=int(v and in_w)
        confirmation_time+=int(inside['confirmation'] and lo<=c<hi)
        before=g[g.time_s.lt(a-1e-9)].tail(1)
        context='first_observed_follower_row' if before.empty else 'prior_observation_available'
        rows.append(dict(event_id=event.event_id,trajectory_id=str(event.trajectory_id),leader_trajectory_id=str(event.leader_trajectory_id),
            onset_s=a,confirm_s=c,end_s=b,onset_position_m=float(first._position),confirm_position_m=float(conf._position),
            **inside,onset_in_window=in_w,confirmation_in_window=bool(lo<=c<hi),confirmation_after_window=bool(in_w and c>=hi),
            actual_message_earliest_s=float(event.message_earliest_generation_s),onset_context=context,exit_reason=event.exit_reason,
            members=len(m),member_sha256=hashlib.sha256(m[['original_row_number','time_s','_position','_inside']].to_csv(index=False).encode()).hexdigest()))
    # Short trailing risk sequences are not zero events: explicitly right censored.
    risk=d.ttc_valid & d.ttc_s.gt(0)&d.ttc_s.lt(2)&d.measurement_status.eq('valid')&d.leader_matched&~d.identity_uncertain&~d.leader_identity_uncertain
    samepair=pd.Series(False,index=d.index)
    p=d.shift()
    samepair=d.trajectory_id.eq(p.trajectory_id)&d.leader_trajectory_id.eq(p.leader_trajectory_id)
    for key in SOURCE_KEYS:samepair &= d[key].eq(p[key])
    cont=samepair&d.time_s.diff().sub(.1).abs().lt(1e-9)&d.frame_id.diff().eq(1)&d.global_time_ms.diff().eq(100)&~d.identity_break&~d.observation_gap
    starts=risk&~(risk.shift(fill_value=False)&cont)
    segment=starts.cumsum()
    candidates=[]
    for _,r in d.loc[risk].groupby(segment[risk],sort=False):
        a=float(r.time_s.iloc[0]);b=float(r.time_s.iloc[-1])
        if b-a>=.2-1e-9:continue
        idx=r.index[-1];tail=idx==len(d)-1 or not all(d.loc[idx,k]==d.loc[idx+1,k] for k in [*SOURCE_KEYS,'trajectory_id'])
        if tail and lo<=a<hi and bool(r._inside.iloc[0]):candidates.append(dict(onset_s=a,last_s=b,trajectory_id=str(r.trajectory_id.iloc[0]),status='right_censored_unconfirmed'))
    seconds=float(l.local.sum()/10)
    cluster_e=d.loc[l.local].groupby('trajectory_id',sort=False).size().div(10).to_dict()
    cluster_n={}
    for r in rows:
        if r['onset'] and r['onset_in_window']:cluster_n[r['trajectory_id']]=cluster_n.get(r['trajectory_id'],0)+1
    return dict(version=VERSION,policy_status='Approved D1',window_s=list(window),counts=counts,events=rows,
        confirmation_time_sensitivity=confirmation_time,full_source_confirmed_events=len(formal),rejected_formal_candidates=len(rejected),
        right_censored_unconfirmed_candidates=len(candidates),censored_candidates=candidates,
        exposure=dict(local_evaluable_s=seconds,local_evaluable_h=seconds/3600,global_evaluable_s=float(l.eligible.sum()/10),
            whole_window_global_evaluable_s=float((l.eligible&l.in_window).sum()/10),
            boundary_crossing_evaluable_s=float((l.eligible&l.in_window&l.left_inside.ne(l.right_inside)).sum()/10),
            local_links=int(l.local.sum()),original_current_incoming_break_semantics=True),
        formal_local_rate_per_evaluable_vehicle_hour=3600*counts['onset']/seconds if seconds else None,
        rates={k:3600*n/seconds if seconds else None for k,n in counts.items()},
        cluster_evaluable_s=cluster_e,cluster_events=cluster_n,
        point_counts=dict(local_points=int((d._inside&d.time_s.ge(lo)&d.time_s.lt(hi)).sum()),
            local_TTC_below2=int((risk&d._inside&d.time_s.ge(lo)&d.time_s.lt(hi)).sum())),
        reality_coverage_accepted=False)


def equivalence(difference_interval,delta,system_error_bound):
    if delta is None:return dict(status='Awaiting Researcher Decision',metric_satisfied=False)
    if system_error_bound is None or difference_interval is None:return dict(status='Evidence Insufficient',metric_satisfied=False)
    lo,hi=difference_interval
    if not np.isfinite([lo,hi,delta,system_error_bound]).all() or lo>hi or delta<=0 or system_error_bound<0:raise ValueError('invalid_equivalence_input')
    bounds=[lo-system_error_bound,hi+system_error_bound]
    ok=bounds[0]>=-delta and bounds[1]<=delta
    return dict(status='criterion_satisfied' if ok else 'discrepancy_or_imprecision',metric_satisfied=bool(ok),expanded_interval=bounds)


def check_run_plan(p):
    runs=p['runs'];construction=[r for r in runs if r['role']=='construction'];repeat=[r for r in runs if r['role']=='repeat']
    if len(runs)>5 or len(construction)>3 or len(repeat)<2:raise PermissionError('budget_or_seed_reservation')
    cs={r['seed'] for r in construction};rs=[r['seed'] for r in repeat]
    if cs&set(rs) or len(set(rs))!=len(rs):raise PermissionError('independent_repeat_seeds')
    lim=p['limits']
    if lim['per_run_wall_s']>600 or lim['memory_bytes']>3*1024**3 or lim['artifact_bytes']>2*1024**3:raise PermissionError('resource_increase')
    if any(r['duration_s']>450 for r in runs) or p['ABCD_allowed']:raise PermissionError('unauthorized_scope')
    if p['validation_access'] and (p['scientific_delta'] is None or p['precision_h'] is None):raise PermissionError('incomplete_acceptance_protocol')
    return True
