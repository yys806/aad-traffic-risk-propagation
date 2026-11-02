"""Isolated Task7 calibration operators, truth, and exact planning.

No production imports; no data discovery or holdout access.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.stats import beta, binom

TRUTH_VERSION = 'AAD-P2T7-TRUTH-20261102-v2'
REGION = (1600., 3080.)
COHORT = tuple(range(14, 18))
PRE = (10., 28.)
MONITOR = (30., 46.)
A_STAR = 1.
B_STAR = 1.
D_STAR = 4.

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+chr(10), encoding='utf-8')

def cp_upper(x, n, failure=.05):
    if not n: return None
    return 1. if x == n else float(beta.ppf(1-failure, x+1, n-x))

def cp_lower(x, n, failure=.05):
    if not n: return None
    return 0. if x == 0 else float(beta.ppf(failure, x, n-x+1))

def exact_plan(limit, good, failure, power=.9, cap=2000000):
    """Enumerate sample sizes; no monotonic-power/binary-search assumption."""
    if not 0 <= good < limit < 1: raise ValueError('invalid planning rates')
    for start in range(1, cap+1, 10000):
        n = np.arange(start, min(cap+1, start+10000))
        critical = binom.ppf(failure, n, limit).astype(int)
        critical -= binom.cdf(critical, n, limit) > failure
        achieved = binom.cdf(critical, n, good)
        ok = np.flatnonzero(achieved >= power)
        if len(ok):
            j = int(ok[0])
            return {'n':int(n[j]), 'max_bad':int(critical[j]), 'power':float(achieved[j]),
                    'limit':limit, 'good':good, 'failure':failure, 'target_power':power}
    return {'n':None, 'status':'exceeds_computation_cap', 'cap':cap}

def segments(t, signal, valid, threshold, persistence, max_gap, start=30., stop=46., exit_delta=0., recovery=0.):
    """Observed spans only; negative and unsupported gaps reset confirmation."""
    events=[]; first=None; previous=None; lower=None; negative_since=None; active=None
    for i in np.flatnonzero((t >= start-1e-9) & (t <= stop+1e-9)):
        now=float(t[i]); good=bool(valid[i]) and np.isfinite(signal[i])
        if not good:
            if previous is not None and now-previous > max_gap+1e-9:
                first=previous=lower=negative_since=None
                if active is not None: active['end_s']=now; active=None
            continue
        if previous is not None and now-previous > max_gap+1e-9:
            first=previous=lower=negative_since=None
            if active is not None: active['end_s']=now; active=None
        level=threshold-exit_delta if active is not None else threshold
        if signal[i] >= level:
            if first is None:
                first=now; lower=float(t[i-1]) if i else None
            previous=now; negative_since=None
            if active is None and now-first >= persistence-1e-9:
                active={'onset_lower_s':lower,'onset_upper_s':first,'confirmation_s':now,
                        'availability_s':now,'end_s':None}
                events.append(active)
        else:
            if active is not None:
                if negative_since is None: negative_since=now
                if now-negative_since >= recovery-1e-9:
                    active['end_s']=now; active=None; first=previous=lower=None
            else: first=previous=lower=None
    return events

def edie(t, x, lane, window, region=REGION, observed=None):
    """Piecewise-linear same-lane segment clipping, lane 0, past window.

    Integrates clipped space-time support without turning empty area into zero speed.
    A lane switch or unknown segment is excluded and its support is marked incomplete.
    """
    n=len(t); distance=np.zeros(n); vehicle_time=np.zeros(n); complete=np.ones(n, bool)
    if observed is None: observed=np.ones_like(x,dtype=bool)
    left,right=region
    dt=np.diff(t)
    dx=np.diff(x,axis=0)
    same=(lane[1:]==0)&(lane[:-1]==0)
    ok=observed[1:]&observed[:-1]&np.isfinite(dx)&(dx >= -1e-8)&same
    lo=np.zeros_like(dx); hi=np.ones_like(dx)
    moving=dx>1e-10
    np.divide(left-x[:-1],dx,out=lo,where=moving)
    np.divide(right-x[:-1],dx,out=hi,where=moving)
    lo=np.maximum(0.,lo);hi=np.minimum(1.,hi)
    stationary=(~moving)&(x[:-1]>=left)&(x[:-1]<right)
    lo=np.where(stationary,0.,lo);hi=np.where(stationary,1.,hi)
    fraction=np.where(moving|stationary,np.maximum(0.,hi-lo),0.)
    fraction=np.where(ok,fraction,0.)
    entry=t[:-1,None]+lo*dt[:,None]
    leave=t[:-1,None]+hi*dt[:,None]
    rate=np.divide(dx,dt[:,None])
    for j in range(1,n):
        begin=max(0,int(np.searchsorted(t,t[j]-window,side='right'))-1)
        span=np.maximum(0.,np.minimum(leave[begin:j],t[j])-np.maximum(entry[begin:j],t[j]-window))
        span=np.where(ok[begin:j]&(fraction[begin:j]>0),span,0.)
        vehicle_time[j]=span.sum();distance[j]=(span*rate[begin:j]).sum()
        relevant=((x[begin:j]>=left)&(x[begin:j]<right))|((x[begin+1:j+1]>=left)&(x[begin+1:j+1]<right))
        complete[j]=not np.any(relevant & same[begin:j] & ~ok[begin:j])
    area=(right-left)*window
    u=np.full(n,np.nan);np.divide(distance,vehicle_time,out=u,where=vehicle_time>0)
    complete &= (t-t[0]>=window-1e-9)
    return {'D':distance,'V':vehicle_time,'A':area,'q':distance/area,'k':vehicle_time/area,'u':u,'complete':complete}

def truth(raw, audit):
    """Frozen clean high-frequency oracle; never calls a candidate detector."""
    t=raw['t'];v=raw['v'];x=raw['x'];lane=raw['lane'];native=raw['native']
    monitor=(t>=30-1e-9)&(t<=46+1e-9)
    macro=edie(t,x,lane,.1)
    inside=(x[:,COHORT]>=REGION[0])&(x[:,COHORT]<REGION[1])&(lane[:,COHORT]==0)
    cohort_ok=inside.all(axis=1)
    target=(lane==0)&(x>=REGION[0])&(x<REGION[1])
    target[:,0]=False
    micro=np.max(np.where(target,10-v,-np.inf),axis=1)
    signals={'cohort':np.mean(10-v[:,COHORT],axis=1),'macro':10-macro['u'],'micro':micro}
    valid={'cohort':cohort_ok,'macro':macro['complete']&np.isfinite(macro['u']),'micro':target.any(axis=1)}
    answer=[]
    for layer,s in signals.items():
        # Oracle interval construction uses fixed a*/b*, not theta/h candidates.
        positive=valid[layer] & (s>=A_STAR-1e-10) & (t>=30-1e-9) & (t<=50+1e-9)
        indices=np.flatnonzero(positive); runs=[]; terminal=None
        if layer=='micro':
            # A sustained response must belong to the same real entity.
            for entity in range(1,v.shape[1]-1):
                indices=np.flatnonzero(target[:,entity]&(10-v[:,entity]>=A_STAR-1e-10)&(t>=30-1e-9)&(t<=50+1e-9))
                for group in np.split(indices,np.flatnonzero(np.diff(indices)>1)+1):
                    if len(group) and t[group[0]]<=46+1e-9 and t[group[-1]]-t[group[0]]>=B_STAR-1e-9: runs.append((group,entity))
            runs.sort(key=lambda pair:t[pair[0][0]])
            if runs: terminal=runs[0][1];runs=[pair[0] for pair in runs]
        else:
            for group in np.split(indices,np.flatnonzero(np.diff(indices)>1)+1):
                if len(group) and t[group[0]]<=46+1e-9 and t[group[-1]]-t[group[0]]>=B_STAR-1e-9: runs.append(group)
        if runs:
            g=runs[0];i=int(g[0]);end=int(g[-1]); onset=[float(t[i-1]),float(t[i])]
            state='positive';confirmation=float(t[int(g[np.searchsorted(t[g]-t[i],B_STAR-1e-9)])])
            recovery=[float(t[end]),float(t[end+1])] if end<len(t)-1 and valid[layer][end+1] else None
        else: onset=confirmation=recovery=None;state='negative' if valid[layer][monitor].all() else 'unknown'
        source_attr=('other' if audit['condition']=='A0' else 'none' if audit['condition'] in ('N0','N1') else 'unknown')
        answer.append({'truth_version':TRUTH_VERSION,'unit_id':audit['unit_id'],'measurement_layer':layer,
            'state_truth':state,'source_attribution':source_attr,'onset_allowed_set':onset,
            'confirmation_s':confirmation,'recovery_interval_s':recovery,
            'a_star_mps':A_STAR,'b_star_s':B_STAR,'d_star_s':D_STAR,
            'truth_error_s':.05,'truth_error_mps':None,'numeric_comparison_tolerance_mps':1e-6,
            'physical_model_error':'Unknown; finite step and real-traffic discrepancy not certified',
            'terminal_entity':terminal,'clock_id':'SUMO simulation time',
            'sampling_s':.05,'label_source':'complete native model state; fixed 10m/s reference and oracle support',
            'label_scope':'finite amplitude-duration state; earliest arbitrary physical onset Unknown',
            'native_target_verified':bool(np.max(np.abs(v[:,1:-1]-native[:,1:-1]))<1e-8),
            'peak_decline_mps':float(np.max(s[monitor & valid[layer]])) if np.any(monitor & valid[layer]) else None,
            'coverage':float(np.mean(valid[layer][monitor])),
            'dependency_block':audit['unit_id'],'density':audit['density'],'condition':audit['condition'],
            'actual_source_onset':audit['actual_source_onset'],'source_execution':audit['source_execution'],
            'label_hash':None})
    for row in answer:
        row['label_hash']=hashlib.sha256(json.dumps(row,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return answer
