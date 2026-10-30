"""Task8: bounded five-second kinematics, using original Task6 sample anchors.

No event extraction, control matching, interpolation or simulator invocation.
Identity-level bindings/profiles and figures stay in ignored local output.
Portable event rows contain ordinal analysis units, never physical-review keys.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/scripts'))
import analyze_stage_0_5_round2_task6_micro_interaction as t6

RESULT_ID = 'RES-STAGE-0.5-POST-R2-TASK8-KINEMATIC-MECHANISM-DIAG-20261030'
OUT = ROOT / 'evidence/results' / RESULT_ID
LOCAL = ROOT / 'code/outputs/diagnostics/post_r2_task8_20261030'
METRICS = ['initial_gap_m', 'onset_gap_m', 'initial_closing_mps', 'onset_closing_mps',
           'initial_follower_speed_mps', 'onset_follower_speed_mps', 'initial_leader_speed_mps',
           'onset_leader_speed_mps', 'C_m', 'C_initial_m', 'C_f_m', 'C_l_m', 'C_gap_m', 'R_m',
           'follower_delta_speed_mps', 'leader_delta_speed_mps', 'leader_speed_range_mps',
           'leader_max_drawdown_mps', 'follower_speed_range_mps']


def dump(path, value):
    t6.write_json(path, value)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return t6.sha(Path(path))


def decompose(times, gap, follower_speed, leader_speed):
    """Signed trapezoids on exactly 51 observed samples; rejects missingness."""
    arrays = [np.asarray(a, dtype=float) for a in (times, gap, follower_speed, leader_speed)]
    t, g, vf, vl = arrays
    if any(len(a) != 51 or not np.isfinite(a).all() for a in arrays):
        raise ValueError('Strict decomposition requires 51 finite original observations')
    if not np.allclose(np.diff(t), .1, rtol=0, atol=1e-8) or abs(t[-1]-t[0]-5) > 1e-8:
        raise ValueError('No interpolation or integration across missing timestamps')
    trap = lambda x: float(np.sum(np.diff(t) * .5 * (x[:-1]+x[1:])))
    c0 = float(vf[0]-vl[0])
    ci, cf, cl = 5*c0, trap(vf-vf[0]), -trap(vl-vl[0])
    c = trap(vf-vl)
    cg = float(g[0]-g[-1])
    if abs(c-ci-cf-cl) > 1e-9:
        raise ValueError('Algebraic closure failed')
    return {'initial_gap_m': g[0], 'onset_gap_m': g[-1],
            'initial_closing_mps': c0, 'onset_closing_mps': vf[-1]-vl[-1],
            'initial_follower_speed_mps': vf[0], 'onset_follower_speed_mps': vf[-1],
            'initial_leader_speed_mps': vl[0], 'onset_leader_speed_mps': vl[-1],
            'C_m': c, 'C_initial_m': ci, 'C_f_m': cf, 'C_l_m': cl, 'C_gap_m': cg, 'R_m': cg-c,
            'follower_delta_speed_mps': vf[-1]-vf[0], 'leader_delta_speed_mps': vl[-1]-vl[0],
            'leader_speed_range_mps': np.ptp(vl), 'follower_speed_range_mps': np.ptp(vf),
            'leader_max_drawdown_mps': np.max(np.maximum.accumulate(vl)-vl)}


class Precursors:
    def __init__(self, raw, real):
        self.real = real
        self.d = t6.normalize(raw, real)
        self.d['_tick8'] = np.rint(self.d.time_s*10).astype(np.int64)
        self.groups = self.d.groupby('trajectory_id', sort=False).indices
        self.ticks = self.d['_tick8'].to_numpy()

    def window(self, identity, tick):
        ix = self.groups.get(str(identity), np.array([], dtype=int))
        z = self.ticks[ix]
        return self.d.iloc[ix[(z >= tick-50) & (z <= tick)]]

    def complete(self, d, tick):
        return (len(d) == 51 and np.array_equal(d['_tick8'].to_numpy(), np.arange(tick-50, tick+1))
                and bool(d['_edge'].iloc[1:].all()))

    def sample(self, identity, time_s):
        tick = int(round(time_s*10))
        if abs(time_s*10-tick)>1e-7:
            return {'status':'anchor_off_grid','strict':False,'follower_rows':0,'leader_rows':0},pd.DataFrame()
        f = self.window(identity, tick)
        onset = f.loc[f['_tick8'].eq(tick)]
        if len(onset) != 1:
            return {'status': 'onset_unmatched', 'strict': False, 'follower_rows': len(f),
                    'leader_rows': 0}, pd.DataFrame()
        row = onset.iloc[0]
        leader = row.leader_trajectory_id
        l = self.window(leader, tick) if pd.notna(leader) else self.d.iloc[0:0]
        fc, lc = self.complete(f, tick), self.complete(l, tick)
        ff = f.loc[f['_tick8'].gt(tick-50)]
        ll = l.loc[l['_tick8'].gt(tick-50)]
        known_leaders = f.loc[f['_rel'] & f.leader_trajectory_id.notna(), 'leader_trajectory_id']
        switched = bool(ff['_ls'].any() or known_leaders.nunique() > 1)
        flc, llc = bool(ff['_lc'].any()), bool(ll['_lc'].any())
        consistent = bool(fc and lc and f['_eval'].all() and f.leader_trajectory_id.eq(leader).all())
        timestamp_match = False
        speed_residual = None
        if fc and lc:
            timestamp_match = True
            if self.real:
                timestamp_match = all(np.array_equal(f[k].to_numpy(), l[k].to_numpy())
                                      for k in ['global_time_ms', 'frame_id', 'source_member', 'source_period', 'diagnostic_clock_anchor_ms'])
                timestamp_match &= np.array_equal(f.leader_frame_id.to_numpy(), l.frame_id.to_numpy())
            speed_residual = float(np.max(np.abs(f.closing_speed_mps.to_numpy() -
                                                (f.speed_mps.to_numpy()-l.speed_mps.to_numpy())))) if consistent else None
        strict = consistent and timestamp_match and speed_residual is not None and speed_residual < 1e-7
        if not fc:
            status = 'follower_incomplete_or_discontinuous'
        elif not len(l.loc[l['_tick8'].eq(tick)]):
            status = 'onset_leader_unmatched'
        elif not lc:
            status = 'onset_leader_incomplete_or_discontinuous'
        elif switched:
            status = 'leader_changed'
        elif not timestamp_match:
            status = 'pair_timestamp_or_frame_unmatched'
        elif not strict:
            status = 'pair_quality_or_speed_inconsistent'
        else:
            status = 'complete_fixed_pair_with_lane_change' if flc or llc else 'complete_fixed_pair_no_lane_change'
        result = {'status': status, 'strict': strict, 'follower_rows': len(f), 'leader_rows': len(l),
                  'follower_complete': fc, 'leader_complete': lc, 'leader_changed_observed': switched,
                  'follower_lane_change_observed': flc, 'onset_leader_lane_change_observed': llc,
                  'timestamp_frame_match': timestamp_match, 'closing_field_max_residual_mps': speed_residual,
                  'onset_gap_m': row.net_gap_m, 'onset_closing_mps': row.closing_speed_mps,
                  'onset_follower_speed_mps': row.speed_mps}
        # Longest continuous suffix in which the current leader is the onset leader.
        suffix = []
        for ix in reversed(f.index.tolist()):
            r = self.d.loc[ix]
            if not bool(r['_eval']) or pd.isna(r.leader_trajectory_id) or r.leader_trajectory_id != leader:
                break
            if suffix and (self.ticks[suffix[-1]]-self.ticks[ix] != 1 or not bool(self.d.loc[suffix[-1], '_pair_edge'])):
                break
            suffix.append(ix)
        result['fixed_pair_suffix_duration_s'] = (len(suffix)-1)*.1 if suffix else None
        if strict:
            result.update(decompose(f.time_s.to_numpy(), f.net_gap_m.to_numpy(), f.speed_mps.to_numpy(), l.speed_mps.to_numpy()))
        # For switched cases, retain onset leader as one fixed role, never splice old leaders.
        prof = f[['_tick8', 'speed_mps', 'net_gap_m', 'closing_speed_mps', 'leader_trajectory_id', '_lc', '_ls', '_edge']].copy()
        prof['relative_time_s'] = (prof['_tick8']-tick)/10
        prof['onset_leader_speed_mps'] = prof['_tick8'].map(l.set_index('_tick8').speed_mps)
        prof['onset_pair_active'] = prof.leader_trajectory_id.eq(leader) & f['_rel']
        prof['fixed_pair_gap_m'] = prof.net_gap_m.where(prof.onset_pair_active)
        prof['fixed_pair_closing_mps'] = (prof.speed_mps-prof.onset_leader_speed_mps).where(prof.onset_pair_active)
        prof['reported_gap_link_valid'] = f['_pair_edge'].to_numpy()
        return result, prof


def summaries(rows):
    out = []
    for key, g in rows.groupby(['scope', 'region', 'sample_kind'], sort=True):
        base = dict(zip(['scope', 'region', 'sample_kind'], key))
        s = g.loc[g.strict]
        for metric in METRICS:
            q = t6.quant(s[metric] if metric in s else [])
            out.append({**base, 'metric': metric, 'all_samples': len(g), 'strict_samples': len(s), **q})
    return pd.DataFrame(out)


def compare(rows, keys):
    joined = rows.merge(keys, on=['scope', 'region', 'sample_kind', 'unit_index'], validate='one_to_one')
    out = []
    for key, g in joined.groupby(['scope', 'region'], sort=True):
        events = g.loc[g.sample_kind.eq('formal_event')].set_index('event_id8')
        controls = g.loc[g.sample_kind.eq('nonrisk_control')].set_index('event_id8')
        shared = events.index.intersection(controls.index)
        strict = [i for i in shared if bool(events.loc[i, 'strict']) and bool(controls.loc[i, 'strict'])]
        for metric in METRICS:
            e = events.loc[strict, metric].to_numpy(float) if strict else np.array([])
            c = controls.loc[strict, metric].to_numpy(float) if strict else np.array([])
            out.append({'scope': key[0], 'region': key[1], 'metric': metric, 'formal_events': len(events),
                        'existing_matched_controls': len(controls), 'paired_strict_samples': len(strict),
                        'event_p50_paired': np.median(e) if len(e) else None, 'control_p50_paired': np.median(c) if len(c) else None,
                        **{'event_minus_control_'+k: v for k, v in t6.quant(e-c).items()}})
    return pd.DataFrame(out)


def aggregate_profiles(profiles):
    out = []
    if profiles.empty:
        return pd.DataFrame()
    metrics = ['speed_mps', 'onset_leader_speed_mps', 'net_gap_m', 'fixed_pair_closing_mps']
    for key, g in profiles.groupby(['scope', 'region', 'sample_kind', 'relative_time_s'], sort=True):
        row = dict(zip(['scope', 'region', 'sample_kind', 'relative_time_s'], key))
        for m in metrics:
            q = t6.quant(g[m])
            row.update({m+'_'+k: q[k] for k in ['n', 'p25', 'p50', 'p75']})
        out.append(row)
    return pd.DataFrame(out)


def validate_samples(rows, keys):
    records = []
    for key, g in rows.groupby(['scope', 'region', 'sample_kind'], sort=True):
        k = keys.loc[keys.scope.eq(key[0]) & keys.region.eq(key[1]) & keys.sample_kind.eq(key[2])]
        statuses = g.status.value_counts().to_dict()
        s = g.loc[g.strict]
        records.append({'scope': key[0], 'region': key[1], 'sample_kind': key[2], 'samples': len(g),
                        'strict': len(s), 'strict_fraction': len(s)/len(g), 'status_counts': statuses,
                        'observed_flags_nonexclusive': {name: int(g[name].fillna(False).sum()) for name in
                            ['leader_changed_observed', 'follower_lane_change_observed', 'onset_leader_lane_change_observed']},
                        'unique_followers': k.trajectory_id.nunique(), 'unique_anchor_rows': len(k.drop_duplicates(['trajectory_id', 'time_s'])),
                        'maximum_samples_per_follower': int(k.trajectory_id.value_counts().max()),
                        'strict_unique_followers': k.loc[k.unit_index.isin(s.unit_index), 'trajectory_id'].nunique(),
                        'algebraic_max_abs_error_m': float((s.C_m-s.C_initial_m-s.C_f_m-s.C_l_m).abs().max()) if len(s) else None,
                        'residual_abs_m': t6.quant(s.R_m.abs()) if len(s) else t6.quant([]),
                        'positive_initial_closing_n': int(s.initial_closing_mps.gt(0).sum()),
                        'positive_follower_contribution_n': int(s.C_f_m.gt(0).sum()),
                        'positive_leader_contribution_n': int(s.C_l_m.gt(0).sum())})
    return records


def plots(rows, profile, near):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures = LOCAL/'figures'
    figures.mkdir(exist_ok=True)
    for region in ['source', 'target']:
        fig, axes = plt.subplots(4, 2, figsize=(11, 12), sharex=True)
        for col, scope in enumerate(t6.t4.WINDOWS):
            for kind, color in [('formal_event', '#b43232'), ('nonrisk_control', '#2865a3')]:
                p = profile.loc[profile.scope.eq(scope) & profile.region.eq(region) & profile.sample_kind.eq(kind)]
                count = rows.loc[rows.scope.eq(scope) & rows.region.eq(region) & rows.sample_kind.eq(kind)]
                label = f'{kind}: strict {int(count.strict.sum())}/{len(count)}'
                x = p.relative_time_s.to_numpy()
                for j, metric in enumerate(['net_gap_m','fixed_pair_closing_mps','speed_mps','onset_leader_speed_mps']):
                    ax = axes[j,col]
                    ax.plot(x, p[metric+'_p50'], color=color, label=label)
                    ax.fill_between(x, p[metric+'_p25'], p[metric+'_p75'], color=color, alpha=.16)
                    ax.set_ylabel(metric.replace('_mps',' (m/s)').replace('_m',' (m)'))
                    ax.grid(alpha=.2)
                axes[0,col].set_title(f'NGSIM {scope}, {region}; median / IQR')
                axes[0,col].legend(fontsize=7)
        for ax in axes[-1]:
            ax.set_xlabel('Observed seconds relative to original onset/control anchor')
        fig.suptitle('Task8: complete fixed-pair five-second precursors; excluded samples retained in coverage table',fontsize=10)
        fig.tight_layout()
        fig.savefig(figures/f'{region}_precursors.png',dpi=160)
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12,5))
    for ax, scope in zip(axes, t6.t4.WINDOWS):
        for i, kind in enumerate(['formal_event','nonrisk_control']):
            s = rows.loc[rows.scope.eq(scope) & rows.region.eq('source') & rows.sample_kind.eq(kind) & rows.strict]
            for j, m in enumerate(['C_initial_m','C_f_m','C_l_m']):
                x = j+i*.3
                q = s[m].quantile([.25,.5,.75]).to_numpy()
                ax.errorbar(x,q[1],yerr=[[q[1]-q[0]],[q[2]-q[1]]],fmt='o',capsize=5,label=f'{kind} n={len(s)}' if j==0 else None)
        ax.set_xticks(np.arange(3)+.15,['initial closing','follower change','leader change'])
        ax.axhline(0,color='grey',lw=.8)
        ax.set_title(scope)
        ax.set_ylabel('Signed closing contribution (m); median / IQR')
        ax.legend(fontsize=8)
    fig.suptitle('Marginal component medians are not additive; individual identities close algebraically')
    fig.tight_layout()
    fig.savefig(figures/'source_closing_contributions.png',dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(7, 3, figsize=(13,18), sharex=True)
    for r, (case, p) in enumerate(near.groupby('case_number',sort=True)):
        x = p.relative_time_s.to_numpy()
        axes[r,0].plot(x,p.speed_mps,label='follower')
        axes[r,0].plot(x,p.onset_leader_speed_mps,label='fixed onset leader')
        axes[r,0].set_ylabel(f'{p.scope.iloc[0]} case {case}')
        axes[r,1].scatter(x,p.net_gap_m,s=8,label='reported current-leader gap')
        axes[r,1].plot(x,p.fixed_pair_gap_m,color='#b43232',label='onset-pair gap')
        axes[r,1].scatter(x,p.fixed_pair_gap_m,color='#b43232',s=9)
        axes[r,2].plot(x,p.fixed_pair_closing_mps,color='#2865a3',label='onset-pair closing')
        axes[r,2].scatter(x,p.fixed_pair_closing_mps,color='#2865a3',s=9)
        axes[r,2].text(.03,.93,f'onset-pair support {int(p.onset_pair_active.sum())}/{len(p)}',
                       transform=axes[r,2].transAxes,va='top',fontsize=7)
        for ax in axes[r]:
            ax.grid(alpha=.2)
        if r==0:
            for ax in axes[r]:
                ax.legend(fontsize=6)
    for j,label in enumerate(['speed (m/s)','net gap (m)','closing (m/s)']):
        axes[0,j].set_title(label)
        axes[-1,j].set_xlabel('Seconds before existing TTC [2,3) segment onset')
    fig.suptitle('All 7 sealed SUMO cases; dots retain current-leader gap; no splicing of leaders; 51 observations per complete role')
    fig.tight_layout()
    fig.savefig(figures/'all_sumo_near_threshold.png',dpi=160)
    plt.close(fig)
    return [p.relative_to(ROOT).as_posix() for p in figures.glob('*.png')]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    bindings = {'base_head': t6.t4.git_head(ROOT), 'inputs': {}, 'reader': {
        'python': platform.python_version(), 'executable': sys.executable, 'pandas': pd.__version__,
        'numpy': np.__version__, 'pyarrow': __import__('pyarrow').__version__},
        'task6_local_anchor_provenance': 'Original saved Task6 identity_contexts, now SHA bound; no original cryptographic seal of local tables. Counts/onsets/metrics cross-checked against portable Task6 and authorized canonical rows.',
        'history_preserved': True}
    def bind(p, expected=None):
        actual = sha(p)
        if expected and actual != expected:
            raise ValueError(f'Bound input changed: {p}')
        bindings['inputs'][p.relative_to(ROOT).as_posix()] = {'sha256':actual, 'expected_sha256':expected}
    rows, keys, profiles, near_profiles, near_rows = [], [], [], [], []
    expected = {'0750_0805': {'source':(167,165),'target':(174,168)},
                '0805_0820': {'source':(159,149),'target':(252,242)}}
    for scope, spec in t6.t4.REAL_EXPECTED.items():
        print('Task8 original anchors and 100ms precursors:',scope,flush=True)
        p = t6.LOCAL/f'{scope}_identity_contexts.csv'
        bind(p)
        anchors = pd.read_csv(p).loc[lambda x:x.horizon_s.eq(1)].reset_index(drop=True)
        if anchors.duplicated(['region','sample_kind','event_id']).any():
            raise ValueError('Task6 anchor duplication')
        for region,(ne,nc) in expected[scope].items():
            a = anchors.loc[anchors.region.eq(region)]
            assert int(a.sample_kind.eq('formal_event').sum())==ne
            assert int(a.sample_kind.eq('nonrisk_control').sum())==nc
        bind(spec['path'],spec['sha256'])
        raw = pd.read_parquet(spec['path'])
        ctx = Precursors(raw,True)
        for k,a in anchors.iterrows():
            res, p = ctx.sample(a.trajectory_id,float(a.time_s))
            assert abs(res['onset_gap_m']-a.onset_gap_m)<1e-7
            assert abs(res['onset_closing_mps']-a.onset_closing_mps)<1e-7
            base = {'scope':scope,'region':a.region,'sample_kind':a.sample_kind,'unit_index':int(k+1)}
            rows.append({**base, **res})
            keys.append({**base,'event_id8':a.event_id,'trajectory_id':a.trajectory_id,'time_s':a.time_s})
            if res['strict']:
                profiles.append(p.assign(**base))
        del raw,ctx
        gc.collect()
    case = 0
    for scope,spec in t6.t4.SIM_EXPECTED.items():
        run = t6.t4.RUNS/spec['run_id']
        p = run/'measured_state.parquet'
        bind(p,spec['measured_state_sha256'])
        anchors_path = ROOT/'evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029'/f'{scope}_source_segments.csv'
        bind(anchors_path)
        anchors = pd.read_csv(anchors_path)
        assert len(anchors)==(4 if scope=='B00_A03' else 3)
        raw = pd.read_parquet(p)
        ctx=Precursors(raw,False)
        for _,a in anchors.iterrows():
            case+=1
            found=ctx.d.loc[ctx.d.vehicle_id.eq(a.vehicle_id)&ctx.d.time_s.sub(a.onset_s).abs().lt(1e-8)]
            assert len(found)==1
            row=found.iloc[0]
            assert str(row.leader_id)==str(a.leader_id)
            res,p=ctx.sample(row.trajectory_id,float(a.onset_s))
            base={'scope':scope,'region':'source','sample_kind':'near_TTC_2_to_3','unit_index':case}
            rows.append({**base,**res})
            p=p.assign(scope=scope,case_number=case)
            near_profiles.append(p)
            near_rows.append({'scope':scope,'case_number':case,'segment_members':a.members,
                              'segment_span_s':a.span_s,'segment_min_ttc_s':a.minimum_ttc_s,**res})
            keys.append({**base,'event_id8':f'near_{case}','trajectory_id':row.trajectory_id,'time_s':a.onset_s})
        del raw,ctx
        gc.collect()
    data=pd.DataFrame(rows)
    identities=pd.DataFrame(keys)
    data.to_csv(LOCAL/'all_precursor_decomposition.csv',index=False,float_format='%.12g')
    for kind,name in [('formal_event','event_precursor_decomposition.csv'),
                      ('nonrisk_control','control_precursor_decomposition.csv')]:
        data.loc[data.sample_kind.eq(kind)].to_csv(OUT/name,index=False,float_format='%.12g')
    identities.to_csv(LOCAL/'identity_bindings.csv',index=False)
    summaries(data).to_csv(OUT/'precursor_summary.csv',index=False,float_format='%.12g')
    real=data.loc[data.sample_kind.ne('near_TTC_2_to_3')]
    realkeys=identities.loc[identities.sample_kind.ne('near_TTC_2_to_3')]
    compare(real,realkeys).to_csv(OUT/'event_control_comparison.csv',index=False,float_format='%.12g')
    rawprof=pd.concat(profiles,ignore_index=True)
    rawprof.to_csv(LOCAL/'strict_pair_profiles.csv',index=False)
    prof=aggregate_profiles(rawprof)
    prof.to_csv(OUT/'precursor_profiles.csv',index=False,float_format='%.12g')
    near=pd.concat(near_profiles,ignore_index=True)
    near.to_csv(LOCAL/'sumo_near_profiles_full.csv',index=False)
    keep=['scope','case_number','relative_time_s','speed_mps','onset_leader_speed_mps',
          'net_gap_m','onset_pair_active','fixed_pair_gap_m','fixed_pair_closing_mps','reported_gap_link_valid','_lc','_ls']
    near[keep].to_csv(OUT/'sumo_near_threshold_profiles.csv',index=False,float_format='%.12g')
    pd.DataFrame(near_rows).to_csv(OUT/'sumo_near_threshold_cases.csv',index=False,float_format='%.12g')
    coverage=validate_samples(data,identities)
    dump(OUT/'sample_coverage.json',coverage)
    # Repeated-event/control windows can overlap. Count unique follower-time observations explicitly.
    overlap=[]
    for key,g in rawprof.groupby(['scope','region','sample_kind'],sort=True):
        k=realkeys.loc[realkeys.scope.eq(key[0])&realkeys.region.eq(key[1])&realkeys.sample_kind.eq(key[2])]
        q=g.merge(k[['unit_index','trajectory_id']],on='unit_index',validate='many_to_one')
        overlap.append({'scope':key[0],'region':key[1],'sample_kind':key[2],
                        'strict_event_weighted_observations':len(q),
                        'unique_follower_time_observations':len(q.drop_duplicates(['trajectory_id','_tick8'])),
                        'unique_follower_windows':q.unit_index.nunique(),
                        'unique_followers':q.trajectory_id.nunique()})
    dump(OUT/'overlap_and_repeated_units.json',overlap)
    figs=plots(data,prof,near)
    dump(OUT/'figure_index.json',{'local_figures':figs,'git_included':False,
                                'reason':'Project portable evidence excludes images; aggregate CSV and code reproduce figures.'})
    dump(OUT/'source_bindings.json',bindings)
    dump(OUT/'analysis_validation.json',{'status':'PASS_OFFLINE_KINEMATICS',
          'formal_event_counts_unchanged':expected,'all_formal_source_counts':[167,159],
          'all_formal_target_counts':[174,252], 'scope':'all Task6 source/target anchors; other-region events not relabelled or re-extracted',
          'samples':len(data),'complete_fixed_pair_samples':int(data.strict.sum()),
          'near_threshold_cases':case,'interpolated_samples':0,'rematched_controls':0,
          'formal_equivalence_accepted':False,'new_simulations':0,'traci_connections':0,
          'third_window_trajectory_reads':0,'holdout_reads':0})
    return coverage


def offline_guard(event,args):
    if event in {'subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'}:
        raise PermissionError(f'Task8 offline analysis forbids {event}')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        name=str(args[0]).lower().replace(chr(92),'/')
        if any(x in name for x in ['locked_holdout','0820_0835','0820am-0835am','/dataset/','/shen/ob/']):
            raise PermissionError('Outside Task8 authorized trajectory scope')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    sys.addaudithook(offline_guard)
    print(json.dumps(t6.clean(build()),ensure_ascii=False,indent=2))
