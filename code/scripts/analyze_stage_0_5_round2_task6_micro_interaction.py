"""Bounded offline Task6 diagnostics. No simulation, network or subprocess use.

Reuses sealed states and Task4/5 results. All extra bins, controls, temporal
contexts and residuals are descriptive diagnostics, never Formal P2 changes.
Identity-level context tables are written only to ignored local output.
"""
from __future__ import annotations

import argparse
import gc
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
sys.path.insert(0, str(ROOT / 'code/src'))
import analyze_stage_0_5_round2_task4_real_source_support as t4

RESULT_ID = 'RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030'
OUT = ROOT / 'evidence/results' / RESULT_ID
LOCAL = ROOT / 'code/outputs/diagnostics/round2_task6_20261030'
T4 = t4.EVIDENCE
T5 = ROOT / 'evidence/results/RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030'
REGIONS = {'source': t4.SOURCE, 'target': t4.TARGET}
sha = t4.sha256_file


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    return value


def write_json(path, value):
    path.write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def quant(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    out = {'n': len(x)}
    for name, p in [('min', 0), ('p01', .01), ('p05', .05), ('p25', .25), ('p50', .5), ('p75', .75), ('p95', .95), ('p99', .99), ('max', 1)]:
        out[name] = float(np.quantile(x, p)) if len(x) else None
    out['mean'] = float(x.mean()) if len(x) else None
    return out


def verify_bundle(path, strict=True):
    records = []
    bad = []
    for line in (path / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split('  ', 1)
        actual = sha(path / name) if (path / name).is_file() else None
        if actual != digest:
            bad.append({'name': name, 'expected_sha256': digest, 'actual_sha256': actual})
            if strict:
                raise ValueError(f'Historical evidence hash mismatch: {path.name}/{name}')
        records.append({'name': name, 'sha256': actual})
    return {'sha256sums': sha(path / 'SHA256SUMS'), 'files_checked': len(records), 'mismatches': bad, 'pass': not bad,
            'verified_payload_files': [x['name'] for x in records if x['name'] not in {b['name'] for b in bad}]}


def normalize(frame, real):
    d = frame.sort_values(['trajectory_id', 'time_s'], kind='stable').reset_index(drop=True).copy()
    if d.duplicated(['trajectory_id', 'time_s']).any():
        raise ValueError('Ambiguous trajectory/time; no first-record fallback allowed')
    if not np.allclose(d.time_s * 10, np.rint(d.time_s * 10), rtol=0, atol=1e-7):
        raise ValueError('Non-100ms input cannot be silently snapped')
    p = d.shift()
    edge = d.trajectory_id.eq(p.trajectory_id) & d.time_s.sub(p.time_s).sub(.1).abs().lt(1e-8)
    if real:
        for key in ['source_member', 'source_period', 'diagnostic_clock_anchor_ms']:
            edge &= d[key].notna() & d[key].eq(p[key]).fillna(False)
        edge &= d.global_time_ms.sub(p.global_time_ms).eq(100).fillna(False)
        edge &= d.frame_id.sub(p.frame_id).eq(1)
        edge &= ~d.identity_break.fillna(True) & ~d.observation_gap.fillna(True)
        reliable_identity = ~d.identity_uncertain.fillna(True)
        edge &= reliable_identity & reliable_identity.shift(fill_value=False)
        rel = reliable_identity & d.leader_matched.fillna(False) & ~d.leader_identity_uncertain.fillna(True)
    else:
        edge &= d.incarnation_id.notna() & d.incarnation_id.eq(p.incarnation_id).fillna(False)
        for key in ['identity_break', 'observation_gap']:
            if key in d:
                edge &= ~d[key].fillna(True)
        rel = d.reliable_following_eligible.fillna(False).astype(bool)
    lane = d.lane_id.astype('string')
    prevlane = lane.shift()
    leader = d.leader_trajectory_id.astype('string')
    prevlead = leader.shift()
    pair = edge & rel & rel.shift(fill_value=False) & leader.notna() & leader.eq(prevlead).fillna(False)
    evaluable = rel & d.measurement_status.isin(['valid', 'not_applicable'])
    d['_rel'] = rel
    d['_eval'] = evaluable & np.isfinite(d.net_gap_m) & d.net_gap_m.gt(0) & np.isfinite(d.closing_speed_mps)
    d['_edge'] = edge.fillna(False).astype(bool)
    d['_lc'] = (edge & lane.notna() & prevlane.notna() & lane.ne(prevlane)).fillna(False).astype(bool)
    d['_aux_to_main'] = d['_lc'] & lane.isin(t4.MAINLINE_LANES) & ~prevlane.isin(t4.MAINLINE_LANES)
    d['_ls'] = (edge & rel & rel.shift(fill_value=False) & leader.notna() & prevlead.notna() & leader.ne(prevlead)).fillna(False).astype(bool)
    d['_pair_edge'] = pair.fillna(False).astype(bool)
    d['_gap_residual'] = (d.net_gap_m.sub(p.net_gap_m) / .1 + .5 * (d.closing_speed_mps + p.closing_speed_mps)).abs().where(pair & evaluable & evaluable.shift(fill_value=False))
    # SUMO research y is a piecewise map, not the physical metric used by speed.
    # Use physical native displacement only within one native lane; no edge reset
    # or mapping jump may masquerade as a trajectory quality defect.
    coordinate = d.y_m if real else d.native_position_m
    physical_edge = edge if real else edge & d.native_lane_id.eq(p.native_lane_id).fillna(False)
    d['_position_speed_residual'] = (coordinate.diff() / .1 - .5 * (d.speed_mps + p.speed_mps)).abs().where(physical_edge)
    d['_acceleration_residual'] = (d.speed_mps.sub(p.speed_mps) / .1 - .5 * (d.acceleration_mps2 + p.acceleration_mps2)).abs().where(edge)
    d['_backwards'] = physical_edge & coordinate.diff().lt(0)
    d['_speed_bin'] = np.floor(d.speed_mps.clip(lower=0) / 5).clip(upper=3).astype('Int64')
    d['_block'] = np.floor(d.time_s / 30).astype(int)
    return d


def independent_tail(gap, closing):
    """Exact product-marginal P(gap < 2*closing), not a random permutation."""
    g, c = np.sort(np.asarray(gap, float)), np.asarray(closing, float)
    return float(np.searchsorted(g, 2 * c, side='left').sum() / (len(g) * len(c))) if len(g) else None


def joint_metrics(d, label, region, stratum='all', bootstrap=False):
    e = d.loc[d['_eval']]
    c = e.loc[e.closing_speed_mps.gt(0) & e.measurement_status.eq('valid') & e.ttc_valid.fillna(False)]
    out = {'scope': label, 'region': region, 'stratum': stratum, 'observed_rows': len(d), 'evaluable_point_rows': len(e), 'positive_closing_rows': len(c),
           'risk_point_rows_0_lt_ttc_lt_2': int((c.ttc_s.gt(0) & c.ttc_s.lt(2)).sum()),
           'positive_closing_fraction': len(c) / len(e) if len(e) else None,
           'joint_tail_fraction_positive': float(c.ttc_s.between(0, 2, inclusive='neither').mean()) if len(c) else None,
           'product_marginal_tail_fraction': independent_tail(c.net_gap_m, c.closing_speed_mps),
           'spearman_gap_positive_closing': c.net_gap_m.rank(method='average').corr(c.closing_speed_mps.rank(method='average')) if len(c) > 2 and c.net_gap_m.nunique() > 1 and c.closing_speed_mps.nunique() > 1 else None}
    for name, values in [('gap', e.net_gap_m), ('positive_closing', c.closing_speed_mps), ('ttc', c.ttc_s), ('gap_positive_closing_subset', c.net_gap_m)]:
        out.update({f'{name}_{k}': v for k, v in quant(values).items()})
    out['ttc_ratio_max_abs_error_s'] = float((c.ttc_s - c.net_gap_m / c.closing_speed_mps).abs().max()) if len(c) else None
    if bootstrap:
        x = c.assign(risk=c.ttc_s.gt(0) & c.ttc_s.lt(2)).groupby('trajectory_id').agg(n=('ttc_s', 'size'), risk=('risk', 'sum'))
        rng = np.random.default_rng(20261030)
        rates = []
        a = x[['n', 'risk']].to_numpy()
        for _ in range(500):
            if not len(a):
                break
            sample = a[rng.integers(0, len(a), len(a))].sum(axis=0)
            rates.append(sample[1] / sample[0])
        out['follower_cluster_ci_low'] = float(np.quantile(rates, .025)) if rates else None
        out['follower_cluster_ci_high'] = float(np.quantile(rates, .975)) if rates else None
        out['positive_closing_followers'] = len(a)
    return out


def joint_histogram(d, label, region):
    c = d.loc[d['_eval'] & d.measurement_status.eq('valid') & d.ttc_valid.fillna(False) & d.closing_speed_mps.gt(0)]
    gb = np.array([0, 1, 2, 5, 10, 20, 40, 80, np.inf])
    cb = np.array([0, .25, .5, 1, 2, 4, 8, np.inf])
    n, _, _ = np.histogram2d(c.net_gap_m, c.closing_speed_mps, bins=(gb, cb))
    risk = c.loc[c.ttc_s.gt(0) & c.ttc_s.lt(2)]
    r, _, _ = np.histogram2d(risk.net_gap_m, risk.closing_speed_mps, bins=(gb, cb))
    assert int(n.sum()) == len(c)
    return [{'scope': label, 'region': region, 'gap_lo_m': gb[i], 'gap_hi_m': gb[i+1], 'closing_lo_mps': cb[j], 'closing_hi_mps': cb[j+1], 'rows': int(n[i,j]), 'risk_point_rows': int(r[i,j]), 'fraction_positive_closing': n[i,j]/len(c) if len(c) else None} for i in range(len(gb)-1) for j in range(len(cb)-1)]


class Context:
    def __init__(self, d):
        self.d = d
        self.groups = d.groupby('trajectory_id', sort=False).indices

    def exact(self, identity, time):
        ix = self.groups.get(str(identity), np.array([], int))
        a = ix[self.d.time_s.to_numpy()[ix] == time]
        return int(a[0]) if len(a) == 1 else None

    def segment(self, identity, time, horizon):
        center = self.exact(identity, time)
        if center is None:
            return self.d.iloc[0:0]
        ix = self.groups[str(identity)]
        ix = ix[(self.d.time_s.to_numpy()[ix] >= time-horizon-1e-8) & (self.d.time_s.to_numpy()[ix] <= time+horizon+1e-8)]
        loc = int(np.flatnonzero(ix == center)[0])
        edge = self.d['_edge'].to_numpy()
        left, right = loc, loc
        while left > 0 and edge[ix[left]]:
            left -= 1
        while right+1 < len(ix) and edge[ix[right+1]]:
            right += 1
        return self.d.iloc[ix[left:right+1]]

    def describe(self, index, horizon):
        row = self.d.loc[index]
        at, identity, leader = float(row.time_s), str(row.trajectory_id), row.leader_trajectory_id
        f = self.segment(identity, at, horizon)
        l = self.segment(str(leader), at, horizon) if pd.notna(leader) else self.d.iloc[0:0]
        ff = f.loc[f.time_s.gt(at-horizon+1e-8)]
        ll = l.loc[l.time_s.gt(at-horizon+1e-8)]
        result = {
            'horizon_s': horizon, 'follower_full_context': len(f) == int(20*horizon+1),
            'leader_onset_matched': self.exact(leader, at) is not None if pd.notna(leader) else False,
            'leader_full_context': len(l) == int(20*horizon+1),
            'follower_context_rows': len(f), 'leader_context_rows': len(l),
            'follower_lane_change': bool(ff['_lc'].any()),
            'follower_lane_change_before_or_at': bool(ff.loc[ff.time_s.le(at), '_lc'].any()),
            'follower_leader_switch': bool(ff['_ls'].any()),
            'follower_leader_switch_before_or_at': bool(ff.loc[ff.time_s.le(at), '_ls'].any()),
            'onset_leader_lane_change': bool(ll['_lc'].any()) if len(l) else None,
            'onset_leader_lane_change_before_or_at': bool(ll.loc[ll.time_s.le(at), '_lc'].any()) if len(l) else None,
            'aux_to_main_observed': bool(ff['_aux_to_main'].any() or ll['_aux_to_main'].any()) if len(l) else None,
            'any_observed_transition': bool(ff['_lc'].any() or ff['_ls'].any() or ll['_lc'].any()),
            'full_pair_role_context': len(f) == int(20*horizon+1) and len(l) == int(20*horizon+1),
            'onset_gap_m': row.net_gap_m, 'onset_closing_mps': row.closing_speed_mps, 'onset_ttc_s': row.ttc_s,
        }
        # Witness requires the actual newly reported onset leader and a prior
        # observed lane transition; it is not proof of a causal cut-in.
        switch = ff.loc[ff['_ls'] & ff.time_s.le(at) & ff.leader_trajectory_id.eq(leader)] if pd.notna(leader) else ff.iloc[0:0]
        result['new_leader_lane_entry_signature'] = any(bool(ll.loc[ll.time_s.le(t) & ll.time_s.ge(t-horizon), '_lc'].any()) for t in switch.time_s) if len(l) else None
        result['complete_context_without_observed_transition'] = result['full_pair_role_context'] and not result['any_observed_transition']
        for name in ['_gap_residual', '_position_speed_residual', '_acceleration_residual']:
            result[name[1:] + '_median'] = f[name].median()
            result[name[1:] + '_p95'] = f[name].quantile(.95)
        result['backwards_observed'] = bool(f['_backwards'].any())
        return result, f, l


def mark_event_proximity(d, events):
    ok = pd.Series(True, index=d.index)
    groups = d.groupby('trajectory_id', sort=False).indices
    for event in events.to_dict('records'):
        ix = groups.get(str(event['trajectory_id']), np.array([], int))
        times = d.time_s.to_numpy()[ix]
        excluded = (times >= float(event['event_start_s'])-3-1e-8) & (times <= float(event['event_end_s'])+3+1e-8)
        ok.iloc[ix[excluded]] = False
    return ok


def aggregate_context(records):
    d = pd.DataFrame(records)
    if d.empty:
        return pd.DataFrame()
    flags = ['follower_full_context', 'leader_onset_matched', 'leader_full_context', 'full_pair_role_context', 'complete_context_without_observed_transition', 'follower_lane_change', 'follower_lane_change_before_or_at', 'follower_leader_switch', 'follower_leader_switch_before_or_at', 'onset_leader_lane_change', 'onset_leader_lane_change_before_or_at', 'any_observed_transition', 'aux_to_main_observed', 'new_leader_lane_entry_signature', 'backwards_observed']
    out = []
    for key, g in d.groupby(['scope', 'region', 'sample_kind', 'horizon_s'], sort=True):
        row = dict(zip(['scope', 'region', 'sample_kind', 'horizon_s'], key))
        row['samples'] = len(g)
        row['unique_followers'] = g.trajectory_id.nunique()
        for flag in flags:
            row[flag + '_yes'] = int(g[flag].eq(True).sum())
            row[flag + '_known'] = int(g[flag].notna().sum())
            row[flag + '_unknown'] = int(g[flag].isna().sum())
        for metric in ['gap_residual_median', 'gap_residual_p95', 'position_speed_residual_median', 'position_speed_residual_p95', 'acceleration_residual_median', 'onset_gap_m', 'onset_closing_mps', 'onset_ttc_s']:
            row.update({metric+'_'+k: v for k, v in quant(g[metric]).items()})
        out.append(row)
    return pd.DataFrame(out)


def contexts(d, events, label, regions, local):
    ctx = Context(d)
    not_near = mark_event_proximity(d, events)
    nonrisk = d['_eval'] & ((d.measurement_status.eq('not_applicable')) | (d.ttc_valid.fillna(False) & d.ttc_s.ge(2))) & not_near
    used = set()
    rows, profiles, match = [], [], []
    for region, mask in regions.items():
        candidates = d.loc[mask & nonrisk]
        buckets = candidates.groupby(['lane_id', '_block', '_speed_bin'], sort=False).groups
        for event in events.to_dict('records'):
            index = ctx.exact(event['trajectory_id'], float(event['event_start_s']))
            if index is None:
                raise ValueError('Onset no longer unique; stop context reconstruction')
            if not bool(mask.loc[index]):
                continue
            row = d.loc[index]
            key = (row.lane_id, row['_block'], row['_speed_bin'])
            choices = list(buckets.get(key, []))
            choices = [i for i in choices if i not in used and d.at[i, 'trajectory_id'] != row.trajectory_id]
            control = None
            if choices:
                c = d.loc[choices].copy()
                c['_dv'] = c.speed_mps.sub(row.speed_mps).abs()
                c['_dt'] = c.time_s.sub(row.time_s).abs()
                control = int(c.sort_values(['_dv', '_dt', 'trajectory_id', 'time_s'], kind='stable').index[0])
                used.add(control)
            match.append({'scope': label, 'region': region, 'matched': control is not None, 'control_speed_difference_mps': abs(d.at[control, 'speed_mps']-row.speed_mps) if control is not None else None})
            for kind, ix in [('formal_event', index), ('nonrisk_control', control)]:
                if ix is None:
                    continue
                base = {'scope': label, 'region': region, 'sample_kind': kind, 'trajectory_id': str(d.at[ix, 'trajectory_id']), 'time_s': float(d.at[ix, 'time_s']), 'event_id': event['event_id']}
                for h in [1, 2, 3]:
                    result, follower, leader = ctx.describe(ix, h)
                    rows.append({**base, **result})
                    if h == 2:
                        for role, frame in [('follower', follower), ('onset_leader', leader)]:
                            for rr in frame.to_dict('records'):
                                profiles.append({**base, 'role': role, 'relative_tick': int(round((rr['time_s']-base['time_s'])*10)), 'speed_mps': rr['speed_mps'], 'gap_m': rr['net_gap_m'], 'closing_mps': rr['closing_speed_mps'], 'acceleration_mps2': rr['acceleration_mps2']})
    pd.DataFrame(rows).to_csv(local / f'{label}_identity_contexts.csv', index=False)
    pp = pd.DataFrame(profiles)
    output_profiles = []
    if not pp.empty:
        for key, g in pp.groupby(['scope', 'region', 'sample_kind', 'role', 'relative_tick'], sort=True):
            out = dict(zip(['scope', 'region', 'sample_kind', 'role', 'relative_tick'], key))
            out['samples'] = len(g)
            for metric in ['speed_mps', 'gap_m', 'closing_mps', 'acceleration_mps2']:
                out.update({metric+'_'+k: v for k, v in quant(g[metric]).items()})
            output_profiles.append(out)
    return rows, match, output_profiles


def near_contexts(d, label, mask):
    ctx = Context(d)
    near = mask & d['_eval'] & d.ttc_valid.fillna(False) & d.ttc_s.ge(2) & d.ttc_s.lt(3)
    previous_near = near.shift(fill_value=False)
    starts = d.index[near & ~(previous_near & d['_pair_edge'])]
    rows = []
    for ix in starts:
        result, _, _ = ctx.describe(ix, 2)
        rows.append({'scope': label, 'region': 'source', 'sample_kind': 'near_TTC_2_to_3', 'trajectory_id': str(d.at[ix, 'trajectory_id']), 'time_s': d.at[ix, 'time_s'], **result})
    return rows


def macro_cells(d, mask, label, region, start, end):
    rows = []
    first = math.floor(start/30)*30
    for t in np.arange(first, end, 30):
        lo, hi = max(t, start), min(t+30, end)
        g = d.loc[mask & d.time_s.ge(lo) & d.time_s.lt(hi)]
        lane_km = (REGIONS[region][1]-REGIONS[region][0])/1000*5
        density = len(g)*.1/(hi-lo)/lane_km
        speed = float(g.speed_mps.mean()) if len(g) else np.nan
        kbin, vbin = math.floor(density/7.5), math.floor(speed/5) if math.isfinite(speed) else -1
        item = joint_metrics(g, label, region, f'block_{int(t/30)}')
        rows.append({**item, 'block_start_s': lo, 'block_end_s': hi, 'effective_duration_s': hi-lo, 'density_veh_km_lane': density, 'speed_mean_mps': speed, 'density_bin': kbin, 'speed_bin': vbin})
    return rows


def population(d, mask, label, region, real, run_dir=None):
    g = d.loc[mask]
    stats = {'scope': label, 'region': region, 'observed_rows': len(g), 'observed_trajectory_ids': g.trajectory_id.nunique(), 'observed_vehicle_ids': g.vehicle_id.nunique(),
             'point_occupancy_vehicle_s': len(g)*.1, 'follower_contiguous_edges': int((mask & mask.shift(fill_value=False) & d['_edge']).sum()),
             'observed_lane_changes_both_ends_in_region': int((mask & mask.shift(fill_value=False) & d['_lc']).sum()),
             'observed_leader_switches_both_ends_in_region': int((mask & mask.shift(fill_value=False) & d['_ls']).sum()),
             'reported_pair_count': g.loc[g['_rel']].groupby(['trajectory_id', 'leader_trajectory_id']).ngroups,
             'measurement_status_counts': g.measurement_status.value_counts(dropna=False).to_dict(),
             'missing_reason_counts': g.loc[~g['_eval'], 'missing_reason'].value_counts(dropna=False).to_dict(),
             'continuous_position_edges': int((mask & d['_position_speed_residual'].notna()).sum()),
             'negative_longitudinal_displacements': int((mask & d['_backwards']).sum()),
             'class_status': 'Unknown: authorized canonical schema omits follower class/length' if real else 'declared vType/class; not observed physical equivalence'}
    for metric in ['_gap_residual', '_position_speed_residual', '_acceleration_residual']:
        stats[metric[1:]] = quant(g[metric])
    stats['per_trajectory_observed_duration_s'] = quant(g.groupby('trajectory_id').size().to_numpy()*.1)
    for name, col, mask_q in [('gap', 'net_gap_m', g['_eval']), ('positive_closing', 'closing_speed_mps', g['_eval'] & g.ttc_valid.fillna(False)), ('ttc', 'ttc_s', g['_eval'] & g.ttc_valid.fillna(False))]:
        stats['per_trajectory_median_'+name] = quant(g.loc[mask_q].groupby('trajectory_id')[col].median())
    stats['position_residual_coordinate'] = 'NGSIM metric Local_Y' if real else 'SUMO native_position within unchanged native_lane only; research y mapping is not differentiated'
    if not real:
        xml = ET.parse(run_dir / 'routes.rou.xml').getroot()
        types = {x.attrib['id']: x.attrib for x in xml.findall('vType')}
        vehicles = {x.attrib['id']: x.attrib.get('type') for x in xml.findall('vehicle')}
        observed = set(g.vehicle_id.astype(str))
        stats['declared_observed_vehicle_classes'] = pd.Series([types.get(vehicles.get(v), {}).get('vClass', 'Unknown') for v in observed]).value_counts().to_dict()
        stats['declared_observed_lengths_m'] = quant([float(types.get(vehicles.get(v), {}).get('length', 'nan')) for v in observed])
        stats['observed_vtype_counts'] = pd.Series([vehicles.get(v, 'Unknown') for v in sorted(observed)]).value_counts().to_dict()
        stats['declared_behavior_parameter_distributions'] = {key: pd.Series([types.get(vehicles.get(v), {}).get(key, 'Unknown') for v in sorted(observed)]).value_counts().to_dict() for key in ['carFollowModel', 'tau', 'sigma', 'minGap', 'accel', 'decel']}
    return stats


def concentration(d, events, mask, label, region):
    ctx = Context(d)
    records = []
    for e in events.to_dict('records'):
        ix = ctx.exact(e['trajectory_id'], float(e['event_start_s']))
        if ix is not None and mask.loc[ix]:
            records.append(e)
    ev = pd.DataFrame(records)
    out = {'scope': label, 'region': region, 'events': len(ev)}
    if ev.empty:
        return out
    counts = ev.trajectory_id.value_counts()
    blocks = np.floor(ev.event_start_s/30).value_counts()
    out.update({'event_followers': len(counts), 'max_events_per_follower': int(counts.max()), 'top5_followers_event_share': float(counts.head(5).sum()/len(ev)), 'event_30s_blocks': len(blocks), 'max_events_in_30s': int(blocks.max()), 'top3_blocks_event_share': float(blocks.nlargest(3).sum()/len(ev)), 'event_duration_s': quant(ev.event_duration_s), 'event_min_ttc_s': quant(ev.ttc_min_s)})
    return out


def bind_inputs():
    result = {'base_head': '8311336779f77cd18b1411ab299959d463a2dffc', 'inputs': {}, 'historical_evidence': {}, 'source_sha256': {}, 'reader': {'python': platform.python_version(), 'executable': sys.executable, 'pandas': pd.__version__}}
    for window, spec in t4.REAL_EXPECTED.items():
        result['inputs'][str(spec['path'].relative_to(ROOT)).replace('\\', '/')] = {'expected_sha256': spec['sha256'], 'actual_sha256': sha(spec['path'])}
    for spec in t4.SIM_EXPECTED.values():
        for name, key in [('fcd.xml', 'fcd_sha256'), ('measured_state.parquet', 'measured_state_sha256')]:
            p = t4.RUNS / spec['run_id'] / name
            result['inputs'][p.relative_to(ROOT).as_posix()] = {'expected_sha256': spec[key], 'actual_sha256': sha(p)}
        p = t4.RUNS / spec['run_id'] / 'routes.rou.xml'
        result['inputs'][p.relative_to(ROOT).as_posix()] = {'actual_sha256': sha(p), 'purpose': 'existing declared class/length/cohort only'}
    for path in [T4, T5, ROOT/'evidence/results/RES-STAGE-0.5-METHOD-EXPANSION-V1', ROOT/'evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1']:
        result['historical_evidence'][path.name] = verify_bundle(path, strict=path in [T4,T5])
        # Old metadata defects are recorded, never silently resealed or repaired.
        # Scientific summaries are reused only when their individual SHA passes.
        if 'METHOD-EXPANSION' in path.name:
            assert {'response_summary.json', 'newell_summary.json', 'response_metrics.csv'}.issubset(result['historical_evidence'][path.name]['verified_payload_files'])
        if 'ARRIVAL-TIMING' in path.name:
            assert {'arrival_summary.json', 'phase_b_wave_diagnostic.json', 'paired_analysis.json'}.issubset(result['historical_evidence'][path.name]['verified_payload_files'])
    for path in [Path(__file__), ROOT/'code/scripts/analyze_stage_0_5_round2_task4_real_source_support.py', ROOT/'code/src/riskprop/ngsim_risk_calibration.py', ROOT/'code/src/riskprop/real_trajectory.py', ROOT/'code/src/riskprop/formal_risk_measurement.py', ROOT/'code/src/riskprop/stage_0_5_sumo.py', ROOT/'code/configs/stage_0_2_formal_risk_measurement_p2_v1.json']:
        result['source_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    for value in result['inputs'].values():
        if 'expected_sha256' in value and value['expected_sha256'] != value['actual_sha256']:
            raise ValueError('Input SHA mismatch; analysis stopped')
    return result


def build():
    from riskprop.ngsim_risk_calibration import extract_rear_end_events
    from riskprop.stage_0_5_sumo import build_sumo_formal_source_frame, extract_sumo_formal_p2_events
    LOCAL.mkdir(parents=True, exist_ok=True)
    bindings = bind_inputs()
    all_joint, all_hist, all_blocks, all_context, all_profiles, all_population, all_concentration, all_match, validations = [], [], [], [], [], [], [], [], []
    datasets = [(label, True, spec) for label, spec in t4.REAL_EXPECTED.items()] + [(label, False, spec) for label, spec in t4.SIM_EXPECTED.items()]
    cohort = t4.cohort_ids(ROOT/'evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/routes.rou.xml')
    assert len(cohort) == 1112
    for label, real, spec in datasets:
        print('Analyzing sealed states:', label, flush=True)
        run_dir = None if real else t4.RUNS / spec['run_id']
        raw = pd.read_parquet(spec['path'] if real else run_dir/'measured_state.parquet')
        events = extract_rear_end_events(raw, provisional_ttc_threshold_s=2, max_gap_s=.11, minimum_duration_s=.2) if real else extract_sumo_formal_p2_events(raw)[0]
        formal = raw if real else build_sumo_formal_source_frame(raw)
        attribution = t4.attribute_event_onsets(formal, events, time_window=None if real else t4.SIM_WINDOW)
        assert attribution['unique'] == attribution['extracted_events'] and attribution['unknown'] == 0 and attribution['conservation_pass']
        check = {'scope': label, 'raw_rows': len(raw), 'full_extracted_events': len(events), 'attribution': {k:v for k,v in attribution.items() if k not in ['classified_events', 'unknown_events']}}
        if real:
            ex = t4.exposure_summary(raw, real=True)
            check['full_p2_exposure_s'] = ex['p2_evaluable_exposure_s']
            assert len(events) == spec['events'] and abs(ex['p2_evaluable_exposure_s']-spec['p2_evaluable_s']) < 1e-7
            assert [attribution['source'], attribution['target']] == ([167,174] if label == '0750_0805' else [159,252])
        else:
            assert attribution['source'] == 0 and attribution['target'] == (0 if label == 'B00_A03' else 1)
        d = normalize(raw, real)
        start, end = (float(d.time_s.min()), float(d.time_s.max())+.1) if real else t4.SIM_WINDOW
        regions = {r: t4.point_region(d, bounds) & d.time_s.ge(start) & d.time_s.lt(end) & (True if real or r == 'source' else d.vehicle_id.isin(cohort)) for r, bounds in REGIONS.items()}
        for region, mask in regions.items():
            g = d.loc[mask]
            all_joint.append(joint_metrics(g, label, region, bootstrap=True))
            all_hist.extend(joint_histogram(g, label, region))
            for speedbin in range(4):
                all_joint.append(joint_metrics(g.loc[g['_speed_bin'].eq(speedbin)], label, region, f'speed_bin_{speedbin}'))
            all_blocks.extend(macro_cells(d, mask, label, region, start, end))
            all_population.append(population(d, mask, label, region, real, run_dir))
            all_concentration.append(concentration(d, events, mask, label, region))
        rows, matches, profiles = contexts(d, events, label, regions, LOCAL)
        all_context.extend(rows); all_match.extend(matches); all_profiles.extend(profiles)
        if not real:
            all_context.extend(near_contexts(d, label, regions['source']))
        validations.append(check)
        del d, raw, formal, events
        gc.collect()
    pd.DataFrame(all_joint).to_csv(OUT/'joint_distribution_summary.csv', index=False)
    pd.DataFrame(all_hist).to_csv(OUT/'gap_closing_joint_histogram.csv', index=False)
    blocks = pd.DataFrame(all_blocks)
    blocks.to_csv(OUT/'independent_time_block_joint_metrics.csv', index=False)
    support = blocks.groupby(['scope','region','density_bin','speed_bin'], sort=True).agg(blocks=('scope','size'), observed_rows=('observed_rows','sum'), evaluable_point_rows=('evaluable_point_rows','sum'), positive_closing_rows=('positive_closing_rows','sum'), risk_point_rows=('risk_point_rows_0_lt_ttc_lt_2','sum')).reset_index()
    support.to_csv(OUT/'macro_common_support_cells.csv', index=False)
    crosswalk = []
    for real_label in t4.REAL_EXPECTED:
        for sim_label in t4.SIM_EXPECTED:
            for region in REGIONS:
                a = support.loc[support.scope.eq(real_label) & support.region.eq(region)]
                b = support.loc[support.scope.eq(sim_label) & support.region.eq(region)]
                shared = a.merge(b, on=['region','density_bin','speed_bin'], suffixes=('_real','_sim'))
                row = {'real': real_label, 'simulation': sim_label, 'region': region, 'shared_macro_cells': len(shared)}
                for role, all_cells in [('real',a),('sim',b)]:
                    for metric in ['blocks','observed_rows','positive_closing_rows','risk_point_rows']:
                        row[role+'_shared_'+metric] = int(shared[metric+'_'+role].sum())
                        row[role+'_all_'+metric] = int(all_cells[metric].sum())
                    row[role+'_shared_observation_share'] = row[role+'_shared_observed_rows']/row[role+'_all_observed_rows'] if row[role+'_all_observed_rows'] else None
                crosswalk.append(row)
    write_json(OUT/'common_support_crosswalk.json', crosswalk)
    aggregate_context(all_context).to_csv(OUT/'event_context_summary.csv', index=False)
    pd.DataFrame(all_profiles).to_csv(OUT/'event_relative_profiles.csv', index=False)
    match = pd.DataFrame(all_match)
    matching = []
    if not match.empty:
        for key,g in match.groupby(['scope','region'],sort=True):
            matching.append({'scope':key[0],'region':key[1], 'events':len(g), 'matched_controls':int(g.matched.sum()), 'unmatched_controls':int((~g.matched).sum()), 'speed_difference_mps':quant(g.control_speed_difference_mps)})
    write_json(OUT/'control_matching_audit.json',matching)
    write_json(OUT/'population_and_quality.json',all_population)
    write_json(OUT/'event_concentration.json',all_concentration)
    write_json(OUT/'source_bindings.json',bindings)
    write_json(OUT/'analysis_validation.json',{'status':'PASS', 'datasets':validations, 'cohort_ids':len(cohort), 'native_launches':0, 'traci_connections':0,'third_window_reads':0,'holdout_reads':0, 'independent_ngsim_windows':True, 'formal_equivalence_accepted':False})
    print(json.dumps(clean(validations)),flush=True)


def offline_guard(event, args):
    if event in {'subprocess.Popen', 'os.system', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'} or event.startswith('os.spawn'):
        raise RuntimeError(f'Offline boundary denied: {event}')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = str(args[0]).replace('\\','/').lower()
        if '/dataset/' in path or ('0820_0835' in path and path.endswith('.parquet')) or 'locked_holdout' in path:
            raise RuntimeError('Unauthorized trajectory access denied')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-inputs-only', action='store_true')
    args = parser.parse_args()
    sys.addaudithook(offline_guard)
    if args.verify_inputs_only:
        print(json.dumps(bind_inputs()))
    else:
        build()
