"""Offline failed-attempt audit. No launch/retry or post-hoc window selection."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from interaction_task_boundary import Boundary
from run_stage_0_5_policy_a_confirmed import ROOT, TASK, RESULT, PORTABLE, freeze, write
from supervise_stage_0_5_diagnostic import sha
sys.path.insert(0, str(ROOT / 'code/src'))
from riskprop import stage_0_5_state_support as ss
from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths
from riskprop.stage_0_5_d1_measurement import local_d1_measurement, inside_region, offset100_cloud


def descriptors(frame, low, high):
    local = frame.loc[inside_region(frame) & frame.time_s.ge(low) & frame.time_s.lt(high)]
    reliable = local.loc[local.reliable_following_eligible]
    out = {'window_s': [low, high], 'states': len(local), 'vehicle_s': len(local) * .1,
           'density_veh_km_lane': len(local) * .1 / (high-low),
           'unavailable_measurement': local.measurement_status.value_counts().to_dict()}
    for field in ['speed_mps', 'net_gap_m', 'closing_speed_mps', 'ttc_s']:
        g = local if field == 'speed_mps' else reliable
        if field == 'ttc_s': g = g.loc[g.ttc_valid]
        values = g[field].to_numpy(float); values = values[np.isfinite(values)]
        out[field] = {'n': len(values), 'mean': float(values.mean()) if len(values) else None,
                      'sd': float(values.std()) if len(values) else None,
                      'p05': float(np.quantile(values,.05)) if len(values) else None,
                      'p95': float(np.quantile(values,.95)) if len(values) else None}
    d1 = local_d1_measurement(frame, (low, high), strict=True)
    out['D1'] = {k: v for k, v in d1.items() if k not in ['events', 'incomplete_candidates']}
    return out


def audit():
    p, approval, resources = freeze()
    work = TASK / 'ID1_SUPPLY_0750'; dest = TASK / 'offline_failure_v2'
    dest.mkdir(exist_ok=False)
    # No broad dataset/output roots: only exact approved baseline and this run.
    reads = [ROOT / n for n in p['input_sha256']]
    reads += list(work.iterdir())
    reads += [PORTABLE / ('us101__0750_0805_' + n + '.csv') for n in ['real_offset100','baseline_offset100','common_support']]
    runtime = [Path(sys.base_prefix) / 'Lib', Path(sys.base_prefix) / 'DLLs']
    for m in [pd, np, __import__('pyarrow')]: runtime.append(Path(m.__file__).resolve().parent)
    boundary = Boundary(reads, runtime, dest)
    sys.dont_write_bytecode = True
    sys.addaudithook(boundary.audit)
    try:
        fcd = parse_fcd(work / 'fcd.xml', network_edge_lengths(work / 'network.net.xml'))
        routes = ET.parse(work / 'routes.rou.xml').getroot()
        vehicles = {v.get('id'): dict(v.attrib) for v in routes.findall('vehicle')}
        initial = {v for v in vehicles if v.startswith('i')}
        measured = ss.measure_state_frame(ss.fcd_to_state_frame(fcd, ss.route_length_map(work / 'routes.rou.xml'),
            run_id='ID1_SUPPLY_0750', scenario_id='policy_A', seed=20261201))
        measured.to_parquet(dest / 'partial_measured_state.parquet', index=False)
        d1 = local_d1_measurement(measured, (120,390), strict=True)
        write(dest / 'partial_full_context_D1.json', d1)
        pieces = []
        for e in d1['events']:
            g = measured.loc[measured.vehicle_id.eq(e['vehicle_id']) & measured.leader_id.eq(e['leader_id']) & measured.time_s.between(e['onset_s'], e['end_s']),
                             ['vehicle_id','leader_id','time_s','net_gap_m','closing_speed_mps','ttc_s','ttc_valid']].copy()
            g['event_id'] = e['event_id']; pieces.append(g)
        (pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=['event_id'])).to_parquet(dest / 'partial_event_members.parquet', index=False)
        cloud = offset100_cloud(measured, (120,390))
        for yi, region in enumerate([(150,250),(250,350)]):
            for ti in range(9):
                r = local_d1_measurement(measured, (120+ti*30,150+ti*30), region=region, strict=True)
                mask = cloud.t_block.eq(ti) & cloud.y_block.eq(yi)
                cloud.loc[mask, 'D1_E_veh_s'] = r['local_evaluable_s']
                cloud.loc[mask, 'onset_N_observed_only'] = r['onset_events']
        real = pd.read_csv(PORTABLE / 'us101__0750_0805_real_offset100.csv')
        base = pd.read_csv(PORTABLE / 'us101__0750_0805_baseline_offset100.csv')
        common = cloud.merge(real[['t_block','y_block','D1_E_veh_s']], on=['t_block','y_block'], suffixes=('', '_real'))
        common = common.merge(base[['t_block','y_block','D1_E_veh_s']], on=['t_block','y_block'], suffixes=('', '_baseline'))
        common['complete_state_support'] = common.block_end_s.le(float(fcd.time_s.max())+.1+1e-9)
        # D1 uses the incoming edge ending exactly at the right endpoint.
        # Half-open state-point support alone cannot certify that last edge.
        common['complete_temporal_support'] = common.block_end_s.le(float(fcd.time_s.max())+1e-9)
        common['common_observed'] = common.states.ge(10) & common.D1_E_veh_s.gt(0) & common.D1_E_veh_s_real.gt(0) & common.D1_E_veh_s_baseline.gt(0) & common.complete_temporal_support
        common['availability'] = np.where(common.complete_temporal_support, 'observed_before_failure', np.where(common.complete_state_support, 'state_points_complete_D1_right_endpoint_missing', 'not_observed_due_run_stop'))
        # Empty future cells remain explicitly missing; never report zero risk.
        common.loc[~common.complete_state_support, ['D1_E_veh_s','onset_N_observed_only','density_veh_km_lane','speed_mean_mps']] = np.nan
        common.to_csv(dest / 'common_support_18_cells.csv', index=False)
        local = fcd.loc[inside_region(fcd)]; initlocal = local.loc[local.vehicle_id.isin(initial)]
        inwindow = initlocal.loc[initlocal.time_s.ge(120)&initlocal.time_s.lt(390)]
        getter = pd.read_csv(work / 'getter_counts.csv')
        target = np.where(getter.time_s.ge(180)&getter.time_s.lt(240), 5., 10.)
        conservation = bool(getter.running.eq(getter.inserted_cumulative-getter.arrived_cumulative).all())
        summary = ET.parse(work / 'summary.xml').getroot().findall('step')
        last = dict(summary[-1].attrib)
        audits = {n: json.loads((work / n).read_text(encoding='utf-8')) for n in ['worker_boundary_audit.json','supervisor_boundary_audit.json']}
        baselinepath = next(ROOT/n for n in p['input_sha256'] if 'c6_c7_offline_v1/us101__0750_0805/' in n)
        baseline = pd.read_parquet(baselinepath)
        phases = []
        for low, high in p['phase_elapsed_s']:
            complete = high <= float(fcd.time_s.max())+1e-9
            state_complete = high <= float(fcd.time_s.max())+.1+1e-9
            phases.append({'window_s': [low,high], 'complete': complete, 'state_points_complete':state_complete,
                'run': descriptors(measured,low,high) if state_complete else None,
                'baseline': descriptors(baseline,low,high),
                'comparison_status': 'predeclared_phase_observed_only' if complete else ('state_descriptors_only_D1_endpoint_missing' if state_complete else 'not_comparable_missing_run_support')})
        result = {'status': 'failed_stop; scientific contrast not completed', 'attempts':1,'remaining_unspent':2,
            'not_attempted': ['ID2_SUPPLY_0805','ID3_RAMP_0750'], 'fcd_time_s':[float(fcd.time_s.min()),float(fcd.time_s.max())],
            'observed_states':len(fcd), 'full_frozen_window_complete':False,
            'common_cells':int(common.common_observed.sum()), 'required_cells':18,
            'state_complete_cells':int(common.complete_state_support.sum()),
            'positive_partial_D1_cells':int(cloud.D1_E_veh_s.gt(0).sum()),
            'supersedes_offline_v1':'v1 conflated half-open state completeness with D1 right-endpoint edge support; retained, not used for final comparison',
            'partial_D1':{k:d1[k] for k in ['onset_events','local_evaluable_s','right_censored_unconfirmed','confirmation_after_window','left_continuing_risk_segments']},
            'full_window_P2_rate':None,'rate_status':'not_evaluable_full_window_due_run_failure; partial exposure is not a 270s denominator',
            'physical_support_counts':measured.physical_support_status.value_counts().to_dict(),
            'initialization': {'initial_route_count':len(initial), 'local_at_120':int(initlocal.time_s.eq(120).sum()),
                'global_at_120':int((fcd.vehicle_id.isin(initial)&fcd.time_s.eq(120)).sum()),
                'last_observed_local_s':float(initlocal.time_s.max()) if len(initlocal) else None,
                'observed_window_records':len(inwindow),'observed_window_vehicle_s':len(inwindow)*.1,
                'initial_never_observed_by_stop':sorted(initial-set(fcd.vehicle_id)),
                'pending_initial_identities':'Unknown; getter only records total pending, no inferred identity completion',
                'full_window_status':'Unknown beyond failure; do not equate local absence with no pending initial vehicles'},
            'input': {'declared_noninitial':p['runs'][0]['declared_noninitial_route_vehicle_counts'],
                'lane_getter_matches_recorded_targets':bool((getter.main2_limit_min_mps.eq(target)&getter.main2_limit_max_mps.eq(target)).all()),
                'last_getter':getter.iloc[-1].to_dict(), 'full_pulse_applied':False,
                'getter_vehicle_conservation':conservation,'summary_last':last,
                'error_vehicle_declared':vehicles['i0063_i0063'],
                'error_vehicle_ever_observed':bool(fcd.vehicle_id.eq('i0063_i0063').any()),
                'native_errors':['i0007_i0007 cannot depart given velocity, slow lane ahead at0', 'i0063_i0063 departure speed too high for main_2 at180; SUMO quits'],
                'native_discarded':int(last['discarded']), 'teleports':int(last['teleports']), 'collisions':int(last['collisions'])},
            'isolation': {n:{'denied':a['denied'],'launched':a['launched']} for n,a in audits.items()},
            'isolation_limit':'Python only; blocked runtime directory probes occurred; no OS/native zero-access proof; task incident Not Accepted retained',
            'phases':phases, 'Gate_changed':False,'scientific_claim_eligible':False}
        write(dest / 'failure_review.json', result)
        write(dest / 'artifact_sha256.json', {str(f.relative_to(TASK).as_posix()):{'sha256':sha(f),'bytes':f.stat().st_size} for f in list(work.iterdir())+list(dest.iterdir()) if f.is_file()})
    finally:
        boundary.save(dest / 'offline_boundary_audit.json')
    return dest


if __name__ == '__main__':
    print(audit())
