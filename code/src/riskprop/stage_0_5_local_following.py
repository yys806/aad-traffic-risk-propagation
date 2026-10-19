"""Local descriptive contract, with Stage0.2 core unchanged and no local policy.

Measure on full-network same-clock context BEFORE marking follower front in
main_1 [50,250). Local event/edge attribution alternatives are audits only.
"""
from __future__ import annotations
from collections import Counter
import numpy as np
import pandas as pd
from .stage_0_5_sumo import compute_sumo_measurements,compute_exposure,following_link_is_valid,build_sumo_formal_source_frame
from .formal_risk_measurement import extract_formal_source_events,P2_FORMAL_CONFIG

VERSION='local-following-engineering-v1'
LOCAL_SPACE=dict(edge='main_1',lanes=['main_1_0','main_1_1','main_1_2'],start_m=50.,end_m=250.,lane_km=.6,position_reference='follower front',interval='[start,end)')


def decorate(raw):
    df=raw.copy()
    if df.duplicated(['run_id','vehicle_id','time_s']).any():raise ValueError('duplicate_identity_clock')
    df=df.sort_values(['incarnation_id','time_s']).reset_index(drop=True)
    df['scenario_id']='generic_highway_fixed_C';df['fixture_id']='local_following';df['experiment_mode']='exploratory_diagnostic_only';df['configured_seed']=20261019
    df['trajectory_id']=df.incarnation_id;df['simulation_step']=np.rint(df.time_s*20).astype(int)
    df['leader_id']=df.leader_id.replace('',None)
    lookup={(r.run_id,r.vehicle_id,r.time_s):r.incarnation_id for r in df[['run_id','vehicle_id','time_s','incarnation_id']].itertuples(index=False)}
    df['leader_incarnation_id']=[lookup.get((r.run_id,r.leader_id,r.time_s)) for r in df[['run_id','leader_id','time_s']].itertuples(index=False)]
    df['leader_identity_status']=np.where(df.leader_incarnation_id.notna(),'observed',np.where(df.leader_id.notna(),'unresolved','not_applicable'))
    for k in ['identity_break','observation_gap']:
        if k not in df:df[k]=False
        if df[k].isna().any():raise ValueError('unknown_identity_continuity_flag')
    df['observation_index']=df.groupby('incarnation_id',sort=False).cumcount()
    df['in_local']=df.edge_id.eq(LOCAL_SPACE['edge'])&df.lane_id.isin(LOCAL_SPACE['lanes'])&df.position_m.ge(50.)&df.position_m.lt(250.)
    measured=compute_sumo_measurements(df)
    # Alias only: approved measurement_status retains "missing" exactly.
    measured['observation_quality']=measured.measurement_status.replace({'missing':'not_measurable'})
    return measured


def _quant(values):
    a=pd.to_numeric(values,errors='coerce').dropna()
    return [float(v) for v in np.quantile(a,[0,.1,.5,.9,1])] if len(a) else None


def formal_frame_preserving_flags(measured):
    frame=build_sumo_formal_source_frame(measured)
    original=measured.set_index(['incarnation_id','time_s'])
    # The older general SUMO adapter intentionally fabricates constant native
    # flags in its narrow recorder domain. This defensive interface preserves
    # supplied evidence instead of erasing a real break in external frames.
    for key in ['identity_break','observation_gap']:
        frame[key]=[bool(original.loc[(r.incarnation_id,r.time_s),key]) for r in frame[['incarnation_id','time_s']].itertuples(index=False)]
    return frame


def analyse(raw,*,measured_output=None):
    m=decorate(raw);local=m[m.in_local];risk=m.ttc_valid & m.ttc_s.lt(P2_FORMAL_CONFIG.ttc_threshold_s)
    if measured_output is not None:m.to_parquet(measured_output,index=False)
    exposure=compute_exposure(m,recorded_observation_step_s=.1)
    frame=formal_frame_preserving_flags(m)
    _,events,rejected=extract_formal_source_events(frame,P2_FORMAL_CONFIG,return_diagnostics=True)
    event_rows=[];candidates=Counter();continuity=Counter();fragments=[];endpoint_exposure=0.;independent_global_exposure=0.;independent_confirmations=[]
    grouped={k:g.sort_values('time_s').to_dict('records') for k,g in m.groupby('incarnation_id',sort=False)}
    # Independent link/exposure arithmetic, checking primitive identities and
    # clock; does not call the tested adjacency function for its expected sum.
    for inc,rows in grouped.items():
        active=[];global_active=[]
        def end_fragment():
            if active:
                fragments.append(dict(start_s=active[0]['time_s'],end_s=active[-1]['time_s'],span_s=active[-1]['time_s']-active[0]['time_s'],samples=len(active)))
                active.clear()
        def end_global():
            if global_active and global_active[-1]['time_s']-global_active[0]['time_s']>=.2-1e-9:
                confirm=next(x['time_s'] for x in global_active if x['time_s']-global_active[0]['time_s']>=.2-1e-9)
                independent_confirmations.append((inc,global_active[0]['time_s'],confirm,global_active[-1]['time_s']))
            global_active.clear()
        previous=None
        for r in rows:
            adjacent=bool(previous and r['incarnation_id']==previous['incarnation_id'] and r['leader_incarnation_id'] is not None and r['leader_incarnation_id']==previous['leader_incarnation_id']
                and r['leader_id']==previous['leader_id'] and abs(r['time_s']-previous['time_s']-.1)<=1e-6
                and not any(x[k] for x in [previous,r] for k in ['identity_break','observation_gap']))
            if previous:
                continuity['edge_changes']+=r['edge_id']!=previous['edge_id']
                continuity['actual_same_edge_lane_changes']+=r['edge_id']==previous['edge_id'] and r['lane_id']!=previous['lane_id']
                continuity['time_gap_links']+=abs(r['time_s']-previous['time_s']-.1)>1e-6
                continuity['leader_switch_links']+=r['leader_id']!=previous['leader_id']
            if adjacent and previous['reliable_following_eligible'] and r['reliable_following_eligible'] and previous['measurement_status'] in ['valid','not_applicable'] and r['measurement_status'] in ['valid','not_applicable']:
                independent_global_exposure+=.1
                if previous['in_local'] and r['in_local']:endpoint_exposure+=.1
            is_risk=r['ttc_valid'] and r['ttc_s']<2.
            if not (is_risk and adjacent):end_global()
            if is_risk:global_active.append(r)
            if not (is_risk and r['in_local'] and adjacent):end_fragment()
            if is_risk and r['in_local']:active.append(r)
            previous=r
        end_fragment();end_global()
    for _,e in events.iterrows():
        inc=e['trajectory_id'];members=[r for r in grouped[inc] if e['event_start_s']-1e-9<=r['time_s']<=e['event_end_s']+1e-9]
        confirm=next(r for r in members if abs(r['time_s']-e['event_confirm_s'])<1e-8)
        on=bool(members[0]['in_local']);cf=bool(confirm['in_local']);fully=all(r['in_local'] for r in members)
        candidates['event_onset_inside']+=on;candidates['event_confirmation_inside']+=cf;candidates['event_fully_inside']+=fully
        event_rows.append(dict(vehicle_id=members[0]['vehicle_id'],incarnation_id=inc,leader_incarnation_id=members[0]['leader_incarnation_id'],
            event_start_s=float(e['event_start_s']),event_confirm_s=float(e['event_confirm_s']),event_end_s=float(e['event_end_s']),exit_reason=e['exit_reason'],
            onset_inside=on,confirmation_inside=cf,fully_inside=fully,raw_frame_count=len(members)))
    # Comparison of two implementations is only within the native no-error
    # runtime domain. Synthetic flagged gaps may have conservative differences.
    no_flags=not m.identity_break.any() and not m.observation_gap.any()
    expected=sorted(independent_confirmations);actual=sorted((e['incarnation_id'],e['event_start_s'],e['event_confirm_s'],e['event_end_s']) for e in event_rows)
    if no_flags and actual!=expected:raise ValueError('independent_event_recomputation_mismatch')
    if abs(exposure['p2_evaluable_following_exposure_s']-independent_global_exposure)>1e-6:raise ValueError('independent_exposure_mismatch')
    return dict(version=VERSION,local_space=LOCAL_SPACE,point=dict(local_samples=len(local),ttc_below_2_samples=int((local.ttc_valid&local.ttc_s.lt(2.)).sum()),
        measurement_status_counts={str(k):int(v) for k,v in local.measurement_status.value_counts().items()},quality_counts={str(k):int(v) for k,v in local.observation_quality.value_counts().items()},
        speed_quantiles_mps=_quant(local.speed_mps),acceleration_quantiles_mps2=_quant(local.acceleration_mps2),net_gap_quantiles_m=_quant(local.net_gap_m),closing_quantiles_mps=_quant(local.closing_speed_mps),TTC_quantiles_s=_quant(local.ttc_s),
        low_speed_share=float((local.speed_mps<5).mean()) if len(local) else None),
        engineering_core=dict(scope='Full-network engineering only; Stage0.2 core directly reused',confirmed_events=len(events),rejected_candidates=len(rejected),exposure=exposure,
            independent_event_recomputed=no_flags,independent_event_count=len(expected),independent_evaluable_exposure_s=independent_global_exposure,scientific_claim_eligible=False),
        engineering_events=event_rows,continuity={k:continuity[k] for k in ['edge_changes','actual_same_edge_lane_changes','time_gap_links','leader_switch_links']},
        local_candidates=dict(**{k:candidates[k] for k in ['event_onset_inside','event_confirmation_inside','event_fully_inside']},
            risk_fragments=len(fragments),fragments_meeting_02_span=sum(f['span_s']>=.2-1e-9 for f in fragments),
            endpoint_contained_evaluable_exposure_s=endpoint_exposure,policy_status='Unapproved audit alternatives; none chosen as formal local attribution'),
        local_formal=dict(events='Unresolved',evaluable_exposure='Unresolved',rate='Not Calculated',reason='Local event and exposure attribution policy not approved',
            core_threshold_s=2.,core_minimum_span_s=.2,closing_epsilon_mps=1e-3,core_config=P2_FORMAL_CONFIG.to_dict(),no_new_P2_definition=True))
