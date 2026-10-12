"""Independent full-sequence analysis helpers for Stage 0.2 closure.

Exploratory sampling does not modify the official extractor or its defaults.
"""
from __future__ import annotations
import json, hashlib
import numpy as np
import pandas as pd
SCOPE=['dataset','site','window_id','source_member','source_period']
PAIR=SCOPE+['trajectory_id','leader_trajectory_id']

def ordered_states(states):
    d=states.sort_values(SCOPE+['trajectory_id','global_time_ms','frame_id'],kind='stable').reset_index(drop=True).copy()
    prev=d.shift()
    same=pd.Series(True,index=d.index)
    for k in PAIR+['diagnostic_clock_anchor_ms']:
        same &= d[k].notna() & prev[k].notna() & d[k].eq(prev[k]).fillna(False)
    same &= d.global_time_ms.diff().eq(100) & d.frame_id.diff().eq(1)
    same &= (d.time_s.diff()-.1).abs().lt(1e-9)
    same &= ~d.identity_break.fillna(True) & ~d.observation_gap.fillna(True)
    reliable=d.leader_matched.fillna(False)&~d.identity_uncertain.fillna(True)&~d.leader_identity_uncertain.fillna(True)
    d['_reliable']=reliable
    d['_link']=same & reliable & reliable.shift(fill_value=False)
    # Every missing/uncertain identity or real interruption starts a new block.
    d['_block']=(~d['_link']).cumsum()
    return d

def sequence_events(d, threshold=2., minimum_span=.2, *, step_ms=100, phase_ms=0, mask_extreme=False):
    if step_ms not in (100,200) or phase_ms not in range(0,step_ms,100): raise ValueError('unsupported sampling phase')
    cols=list(dict.fromkeys(PAIR+['time_s','global_time_ms','frame_id','diagnostic_clock_anchor_ms','original_row_number','ttc_s','drac_mps2','net_gap_m','ttc_valid','measurement_status','_block','_reliable']))
    selected=d.loc[((d.global_time_ms-d.diagnostic_clock_anchor_ms-phase_ms)%step_ms).eq(0),cols].copy()
    selected['_obspos']=np.arange(len(selected))
    risk=selected._reliable&selected.ttc_valid.fillna(False)&selected.measurement_status.eq('valid')&np.isfinite(selected.ttc_s)&selected.ttc_s.gt(0)&selected.ttc_s.lt(threshold)
    if mask_extreme: risk &= ~((selected.ttc_s<.5)|(selected.drac_mps2>10)|(selected.net_gap_m<1))
    c=selected[risk].copy(); prev=c.shift()
    continued=c._block.eq(prev._block)&c._obspos.diff().eq(1)&c.global_time_ms.diff().eq(step_ms)&c.frame_id.diff().eq(step_ms//100)
    c['_run']=(~continued).cumsum(); output=[]
    for _,g in c.groupby('_run',sort=False):
        times=g.time_s.to_numpy(float)
        if times[-1]-times[0]+1e-12<minimum_span: continue
        confirm=np.flatnonzero(times-times[0]+1e-9>=minimum_span)[0]
        base=g.iloc[0]
        ids=tuple(map(int,g.original_row_number)); key='|'.join(str(base[k]) for k in PAIR)
        identifier=hashlib.sha256((key+'|'+','.join(map(str,ids))).encode()).hexdigest()[:20]
        output.append({**{k:base[k] for k in PAIR},'event_key':identifier,'event_start_s':times[0], 'event_confirm_s':times[confirm], 'event_end_s':times[-1],'raw_frame_count':len(g),'ttc_min_s':float(g.ttc_s.min()),'drac_max_mps2':float(g.drac_mps2.max()),'original_row_numbers':list(ids),'member_hash':hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest(),'confirm_observed':True})
    return pd.DataFrame(output,columns=PAIR+['event_key','event_start_s','event_confirm_s','event_end_s','raw_frame_count','ttc_min_s','drac_max_mps2','original_row_numbers','member_hash','confirm_observed']), {'sampled_rows':len(selected),'sampled_risk_rows':int(risk.sum()),'identity_continuous_span_s':float((selected._block.eq(selected._block.shift())&selected.global_time_ms.diff().eq(step_ms)&selected.frame_id.diff().eq(step_ms//100)).sum()*step_ms/1000)}

def event_edges(a,b):
    index={}; out=[]
    for ib,y in b.iterrows():
        scope=tuple(str(y[k]) for k in PAIR)
        for m in y.original_row_numbers: index.setdefault((scope,int(m)),set()).add(ib)
    for ia,x in a.iterrows():
        scope=tuple(str(x[k]) for k in PAIR); members=set(map(int,x.original_row_numbers)); matches=set()
        for m in members: matches.update(index.get((scope,m),set()))
        for ib in matches:
            y=b.loc[ib]; other=set(map(int,y.original_row_numbers))
            out.append({'a':ia,'b':ib,'intersection_rows':len(members&other),'exact_members':members==other,'confirm_delta_s':float(y.event_confirm_s-x.event_confirm_s),'onset_delta_s':float(y.event_start_s-x.event_start_s),'exit_delta_s':float(y.event_end_s-x.event_end_s)})
    return pd.DataFrame(out,columns=['a','b','intersection_rows','exact_members','confirm_delta_s','onset_delta_s','exit_delta_s'])

def correspondence_summary(a,b,edges):
    da=edges.groupby('a').b.nunique() if len(edges) else pd.Series(dtype=int)
    db=edges.groupby('b').a.nunique() if len(edges) else pd.Series(dtype=int)
    return {'reference_events':len(a),'comparison_events':len(b),'reference_retained':len(da),'reference_disappeared':len(a)-len(da),'comparison_no_overlap':len(b)-len(db),'reference_split':int((da>1).sum()),'comparison_merged':int((db>1).sum()),'one_to_one_exact':int(edges.exact_members.sum()),'median_confirm_delta_s':float(edges.confirm_delta_s.median()) if len(edges) else None,'min_confirm_delta_s':float(edges.confirm_delta_s.min()) if len(edges) else None,'max_confirm_delta_s':float(edges.confirm_delta_s.max()) if len(edges) else None}
