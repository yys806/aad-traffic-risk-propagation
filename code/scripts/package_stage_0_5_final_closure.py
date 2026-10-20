"""Assemble, seal and independently verify the Stage 0.5 final-closure evidence.

Reads this task's local capsule summaries plus approved sealed evidence only.
Never touches raw trajectories, the third real window or any locked holdout.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

RESULT_ID = 'RES-STAGE-0.5-FINAL-CLOSURE-V1'
ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / 'code/outputs/formal/calibration/stage_0_5_final_closure_v4'
SIM = ROOT / 'code/outputs/formal/calibration/stage_0_5_final_candidate_v1'
GROUPS = ['us101__0750_0805', 'us101__0805_0820']
RUNS = ['FC1', 'FC2']
WINDOWS = {'us101__0750_0805': [120.0, 840.0], 'us101__0805_0820': [180.0, 840.0]}
FULL = {'us101__0750_0805': [0.0, 952.8], 'us101__0805_0820': [0.0, 999.0]}
SEALED_GLOBAL_EXPOSURE = {'us101__0750_0805': 111425.9, 'us101__0805_0820': 133505.6}
SEALED_GLOBAL_EVENTS = {'us101__0750_0805': 543, 'us101__0805_0820': 732}
REAL_ONSET = {'us101__0750_0805': 147, 'us101__0805_0820': 216}
SEAL_KEYS = ['onset', 'confirmation', 'through_confirmation', 'through_end']
MAX_BYTES = 256 * 1024
EVENT_FIELDS = ['side', 'condition', 'event_id', 'trajectory_id', 'leader_trajectory_id', 'onset_s', 'confirm_s', 'end_s',
                'onset_position_m', 'confirm_position_m'] + SEAL_KEYS + ['onset_in_window', 'confirmation_in_window',
                'confirmation_after_window', 'actual_message_earliest_s', 'members']
MEMBER_FIELDS = ['side', 'condition', 'event_id', 'onset_context', 'exit_reason', 'member_sha256']
CLUSTER_FIELDS = ['side', 'condition', 'trajectory_id', 'evaluable_s', 'onset_events']


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, d): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p): return list(csv.DictReader(Path(p).open(encoding='utf-8', newline='')))


def truth(value):
    if isinstance(value, bool): return value
    if value in ('True', 'true'): return True
    if value in ('False', 'false'): return False
    raise ValueError('unknown_boolean')


def num(value): return float(value)


def key(identifier): return hashlib.sha256(str(identifier).encode('utf-8')).hexdigest()[:16]


def recount(events, clusters, published, lo, hi, label):
    """Recompute counts, exposure, rate and cluster totals from the tables themselves."""
    counts = {k: sum(1 for e in events if truth(e[k]) and lo <= num(e['onset_s']) < hi) for k in SEAL_KEYS}
    confirm_time = sum(1 for e in events if truth(e['confirmation']) and lo <= num(e['confirm_s']) < hi)
    exposure = round(sum(num(c['evaluable_s']) for c in clusters), 1)
    cluster_events = sum(int(c['onset_events']) for c in clusters)
    if counts != published['counts']: raise ValueError('recount_counts:' + label)
    if confirm_time != published['confirmation_time_sensitivity']: raise ValueError('recount_confirm_time:' + label)
    if not math.isclose(exposure, published['exposure']['local_evaluable_s'], abs_tol=0.05): raise ValueError('recount_exposure:' + label)
    if cluster_events != counts['onset']: raise ValueError('recount_cluster_events:' + label)
    rate = published['formal_local_rate_per_evaluable_vehicle_hour']
    if rate is None or abs(rate - 3600 * counts['onset'] / exposure) > 1e-6: raise ValueError('recount_rate:' + label)
    return counts, confirm_time, exposure, cluster_events


def real_side(out, event_rows, member_rows, cluster_rows):
    """Recompute every published real-window statistic from its own event/cluster table."""
    per = {}
    for g in GROUPS:
        src = REF / 'summary' / g
        entry = {}
        for label in ['interior', 'full_acquisition']:
            events = rows(src / (label + '_events.csv'))
            clusters = rows(src / (label + '_clusters.csv'))
            published = read(src / (label + '_P2.json'))
            lo, hi = WINDOWS[g] if label == 'interior' else FULL[g]
            counts, confirm_time, exposure, cluster_events = recount(events, clusters, published, lo, hi, g + ':' + label)
            if published['full_source_confirmed_events'] != SEALED_GLOBAL_EVENTS[g]: raise ValueError('sealed_event_reference:' + g)
            if len(events) != SEALED_GLOBAL_EVENTS[g]: raise ValueError('event_table_scope:' + g)
            if not math.isclose(published['exposure']['global_evaluable_s'], SEALED_GLOBAL_EXPOSURE[g], abs_tol=0.05):
                raise ValueError('sealed_denominator:' + g)
            whole = published['exposure']['whole_window_global_evaluable_s']
            if label == 'full_acquisition':
                if not math.isclose(whole, SEALED_GLOBAL_EXPOSURE[g], abs_tol=0.05): raise ValueError('whole_window_denominator:' + g)
            elif not whole <= SEALED_GLOBAL_EXPOSURE[g] + 0.05: raise ValueError('window_denominator_bound:' + g)
            if exposure >= whole: raise ValueError('local_exposure_scope:' + g)
            if published['exposure']['boundary_crossing_evaluable_s'] <= 0: raise ValueError('missing_boundary_crossings:' + g)
            in_window = [e for e in events if truth(e['onset_in_window'])]
            differing = [e for e in events if len({truth(e[k]) for k in SEAL_KEYS}) > 1]
            entry[label] = dict(window_s=[lo, hi], event_rows=len(events), counts=counts,
                                 confirmation_time_window_sensitivity=confirm_time,
                                 local_evaluable_vehicle_s=exposure, cluster_count=len(clusters),
                                 cluster_onset_total=cluster_events,
                                 rate_per_evaluable_vehicle_hour=published['formal_local_rate_per_evaluable_vehicle_hour'],
                                 cluster_interval=read(src / 'P2_cluster_uncertainty.json')['interval'] if label == 'interior' else None,
                                 onset_in_window_events=len(in_window),
                                 attribution_differing_events=len(differing),
                                 rejected_formal_candidates=published['rejected_formal_candidates'],
                                 right_censored_unconfirmed=published['right_censored_unconfirmed_candidates'],
                                 full_source_evaluable_exposure_s=published['exposure']['global_evaluable_s'],
                                 whole_window_evaluable_exposure_s=whole,
                                 boundary_crossing_evaluable_s=published['exposure']['boundary_crossing_evaluable_s'])
            for e in events:
                keep = truth(e['onset_in_window']) or len({truth(e[k]) for k in SEAL_KEYS}) > 1
                if label != 'interior' or not keep: continue
                record = dict(side='real', condition=g, **{k: e[k] for k in EVENT_FIELDS if k not in ('side', 'condition')})
                record['trajectory_id'] = key(e['trajectory_id'])
                record['leader_trajectory_id'] = key(e['leader_trajectory_id'])
                event_rows.append(record)
                member_rows.append(dict(side='real', condition=g, event_id=e['event_id'], onset_context=e['onset_context'],
                                        exit_reason=e['exit_reason'], member_sha256=e['member_sha256']))
            if label == 'interior':
                for c in clusters:
                    cluster_rows.append(dict(side='real', condition=g, trajectory_id=key(c['trajectory_id']),
                                             evaluable_s=c['evaluable_s'], onset_events=c['onset_events']))
        audit = read(src / 'source_audit.json')
        entry['provenance'] = dict(state_sha256=audit['sha256'], rows=audit['rows'], trajectories=audit['trajectories'],
                                   partitions=audit['partitions'],
                                   original_exposure_independently_reproduced=audit['original_exposure_independently_reproduced'],
                                   old_formal_events_read=audit['old_formal_events_read'],
                                   third_window_rows_materialised=audit['third_window_rows_materialised'],
                                   validation_window_read=audit['source_access']['validation_window_read'],
                                   denied_requests=audit['source_access']['denied_count'],
                                   locked_holdout_accessed=audit['source_access']['locked_holdout_accessed'],
                                   reference_plan_sha256=audit['reference_plan_sha256'])
        entry['uncertainty'] = read(src / 'joint_uncertainty.json')
        entry['traffic_metrics'] = read(src / 'traffic_metrics.json')
        entry['time_blocks'] = rows(src / 'time_blocks.csv')
        entry['statistics_time_blocks'] = rows(src / 'statistics_time_blocks.csv')
        for name in ['interior_P2.json', 'full_acquisition_P2.json', 'P2_cluster_uncertainty.json', 'joint_uncertainty.json',
                     'traffic_metrics.json', 'source_audit.json']:
            shutil.copyfile(src / name, out / ('real_' + g + '_' + name))
        per[g] = entry
    write(out / 'real_local_reference_summary.json', per)
    return per


def sim_side(out, plan, event_rows, member_rows, cluster_rows):
    summary = {}
    window = plan['evaluation']['window_s']
    for r in RUNS:
        folder = SIM / 'summary' / r
        published = read(folder / 'P2.json')
        events = rows(folder / 'events.csv')
        clusters = rows(folder / 'clusters.csv')
        run_plan = next(x for x in plan['runs'] if x['run_id'] == r)
        counts, confirm_time, exposure, cluster_events = recount(events, clusters, published, window[0], window[1], r)
        blocks = read(folder / 'state_support_blocks.json')
        run_summary = read(SIM / 'runs' / r / 'summary.json')
        if run_summary['engineering_blockers'] or run_summary['global_blockers']: raise ValueError('unrecorded_blocker:' + r)
        if run_summary['plan_sha256'] != sha(SIM / 'experiment_plan.json'): raise ValueError('run_plan_SHA:' + r)
        if run_summary['observed_s'] != run_plan['duration_s']: raise ValueError('incomplete_run:' + r)
        if blocks['global_conservation_max'] or blocks['local_balance_max']: raise ValueError('conservation_residual:' + r)
        summary[r] = dict(condition=run_plan['condition'], seed=run_plan['seed'], role=run_plan['role'],
                          status=run_summary['status'], observed_s=run_summary['observed_s'],
                          engineering_blockers=run_summary['engineering_blockers'],
                          diagnostic_warnings=run_summary['diagnostic_warnings'],
                          evidence_insufficient=run_summary['evidence_insufficient'],
                          inserted=run_summary['actual_inserted'], exited=run_summary['actual_exited'],
                          present=run_summary['present'], pending_end=run_summary['pending_end'],
                          max_pending=run_summary['max_pending'], counts=counts,
                          confirmation_time_window_sensitivity=confirm_time,
                          local_evaluable_vehicle_s=exposure, cluster_count=len(clusters),
                          cluster_onset_total=cluster_events,
                          rate_per_evaluable_vehicle_hour=published['formal_local_rate_per_evaluable_vehicle_hour'],
                          evaluation_window_s=list(plan['evaluation']['window_s']),
                          global_confirmed_events=published['full_source_confirmed_events'],
                          local_points=published['point_counts']['local_points'],
                          local_ttc_below_2=published['point_counts']['local_TTC_below2'],
                          right_censored_unconfirmed=published['right_censored_unconfirmed_candidates'],
                          numerical=dict(all_adjacent_edges=run_summary['numerical']['all_adjacent_edges'],
                                         exact_checked=run_summary['numerical']['exact_checked'],
                                         exact_passed=run_summary['numerical']['exact_passed'],
                                         bounded=run_summary['numerical']['classifications']['Bounded Consistency Only']['count'],
                                         not_evaluable=run_summary['numerical']['classifications']['Not Evaluable']['count'],
                                         blockers=run_summary['numerical']['classifications']['Engineering Blocker']['count'],
                                         max_abs_residual_m=run_summary['numerical']['max_abs_residual_m'],
                                         tolerance_m=run_summary['numerical']['tolerance_m'],
                                         context_bases=run_summary['numerical']['context_bases']),
                          conservation=dict(global_max=blocks['global_conservation_max'], local_balance_max=blocks['local_balance_max']),
                          thirty_second_blocks=blocks['blocks'],
                          time_blocks=rows(folder / 'time_blocks.csv'),
                          traffic_metrics=read(folder / 'traffic_metrics.json'))
        for e in events:
            if not (truth(e['onset_in_window']) or len({truth(e[k]) for k in SEAL_KEYS}) > 1): continue
            record = dict(side='sim', condition=r, **{k: e[k] for k in EVENT_FIELDS if k not in ('side', 'condition')})
            record['trajectory_id'] = key(e['trajectory_id'])
            record['leader_trajectory_id'] = key(e['leader_trajectory_id'])
            event_rows.append(record)
            member_rows.append(dict(side='sim', condition=r, event_id=e['event_id'], onset_context=e['onset_context'],
                                    exit_reason=e['exit_reason'], member_sha256=e['member_sha256']))
        for c in clusters:
            cluster_rows.append(dict(side='sim', condition=r, trajectory_id=key(c['trajectory_id']),
                                     evaluable_s=c['evaluable_s'], onset_events=c['onset_events']))
        shutil.copyfile(folder / 'P2.json', out / ('sim_' + r + '_P2.json'))
        shutil.copyfile(folder / 'traffic_metrics.json', out / ('sim_' + r + '_traffic_metrics.json'))
        shutil.copyfile(folder / 'state_support_blocks.json', out / ('sim_' + r + '_state_support_blocks.json'))
    return summary


def write_tables(out, event_rows, member_rows, cluster_rows):
    for name, fields, data in [('event_attribution_audit.csv', EVENT_FIELDS, event_rows),
                               ('member_support_audit.csv', MEMBER_FIELDS, member_rows),
                               ('cluster_exposure_audit.csv', CLUSTER_FIELDS, cluster_rows)]:
        with (out / name).open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            for row in data: writer.writerow(row)


def state_support(plan, real_metrics, sim):
    """Apply the plan's own frozen pre-declared rule; no new threshold is invented here."""
    rule = plan['repeat_activation']['rule']
    window = plan['evaluation']['window_s']
    checks = []
    for r in RUNS:
        condition = sim[r]['condition']
        target_speed = real_metrics[condition]['metrics']['speed_mps']['mean']
        target_density = real_metrics[condition]['density_veh_km_lane']
        speeds = [b['mean_speed_mps'] for b in sim[r]['thirty_second_blocks']]
        densities = [b['density'] for b in sim[r]['thirty_second_blocks']]
        checks.append(dict(run_id=r, condition=condition, evaluation_window_s=window,
                           predeclared_block_envelope=dict(speed_mps=[min(speeds), max(speeds)],
                                                           density_veh_km_lane=[min(densities), max(densities)]),
                           real_target=dict(mean_speed_mps=target_speed, density_veh_km_lane=target_density),
                           speed_inside_envelope=bool(min(speeds) <= target_speed <= max(speeds)),
                           density_inside_envelope=bool(min(densities) <= target_density <= max(densities)),
                           low_speed_share_sim=sim[r]['traffic_metrics']['low_speed_share'],
                           low_speed_share_real=real_metrics[condition]['low_speed_share'],
                           closing_speed_mean_sim=sim[r]['traffic_metrics']['metrics']['closing_speed_mps']['mean'],
                           closing_speed_mean_real=real_metrics[condition]['metrics']['closing_speed_mps']['mean'],
                           net_gap_mean_sim=sim[r]['traffic_metrics']['metrics']['net_gap_m']['mean'],
                           net_gap_mean_real=real_metrics[condition]['metrics']['net_gap_m']['mean'],
                           full_network_pending=sim[r]['pending_end'],
                           observed_no_pending_backlog=bool(sim[r]['pending_end'] == 0)))
    satisfied = all(c['speed_inside_envelope'] and c['density_inside_envelope'] for c in checks)
    return dict(predeclared_rule=rule, per_run=checks, all_targets_inside_envelope=satisfied,
                verdict='StateSupported' if satisfied else 'EvidenceInsufficient_StateSupport',
                consequence=('Reserved independent-seed repeats may be activated' if satisfied else
                             'Per the frozen rule: no further search or repeat; reserved runs preserved; report Evidence Insufficient'),
                note='Envelope membership is a necessary pre-declared state-support check only. It is not a science tolerance, not an equivalence test and not a Gate.',
                not_a_science_tolerance=True)


def five_layers(reference, sim, support, delta_audit, plan):
    """Conjunctive necessary-layer admission computed from the exported figures."""
    real_metrics = {g: reference[g]['traffic_metrics'] for g in GROUPS}
    run_condition = {r: sim[r]['condition'] for r in RUNS}
    comparison_ready = all(c['speed_inside_envelope'] and c['density_inside_envelope'] for c in support['per_run'])

    def versus_real(runs, metric, *, from_metrics=False, digits=4):
        parts = []
        for r in runs:
            s = sim[r]['traffic_metrics']
            v = s['metrics'][metric]['mean'] if from_metrics else s[metric]
            w = real_metrics[run_condition[r]]
            t = w['metrics'][metric]['mean'] if from_metrics else w[metric]
            parts.append('%s sim %.*g vs real %.*g' % (r, digits, v, digits, t))
        return '; '.join(parts)

    flow = '; '.join('%s sim %.1f vs real %.1f veh/h/lane' % (
        r,
        sim[r]['traffic_metrics']['density_veh_km_lane'] * sim[r]['traffic_metrics']['metrics']['speed_mps']['mean'] * 3.6,
        real_metrics[run_condition[r]]['density_veh_km_lane'] * real_metrics[run_condition[r]]['metrics']['speed_mps']['mean'] * 3.6)
        for r in RUNS)
    numerical = '; '.join('%s exact %d/%d, bounded %d, not-evaluable %d, blockers %d, max residual %.3g m against 1e-6 m' % (
        r, sim[r]['numerical']['exact_passed'], sim[r]['numerical']['exact_checked'], sim[r]['numerical']['bounded'],
        sim[r]['numerical']['not_evaluable'], sim[r]['numerical']['blockers'], sim[r]['numerical']['max_abs_residual_m']) for r in RUNS)
    real_p2 = '; '.join('%s interior onset %d, exposure %.1f veh-s, rate %.4f per evaluable vehicle-hour, interval %s' % (
        g, reference[g]['interior']['counts']['onset'], reference[g]['interior']['local_evaluable_vehicle_s'],
        reference[g]['interior']['rate_per_evaluable_vehicle_hour'], reference[g]['interior']['cluster_interval']) for g in GROUPS)
    envelope = '; '.join('%s blocks v[%.3f,%.3f] k[%.3f,%.3f] vs target v=%.4g k=%.4g' % (
        c['run_id'], c['predeclared_block_envelope']['speed_mps'][0], c['predeclared_block_envelope']['speed_mps'][1],
        c['predeclared_block_envelope']['density_veh_km_lane'][0], c['predeclared_block_envelope']['density_veh_km_lane'][1],
        c['real_target']['mean_speed_mps'], c['real_target']['density_veh_km_lane']) for c in support['per_run'])
    exposure = '; '.join('%s %.1f veh-s' % (r, sim[r]['local_evaluable_vehicle_s']) for r in RUNS)
    real_exposure = ' and '.join('%.1f' % reference[g]['interior']['local_evaluable_vehicle_s'] for g in GROUPS)
    layers = [
        dict(layer=1, name='basic kinematics', engineering_status='Computed',
             evidence='Both real windows and both candidate runs carry full state, kinematic and quality statistics with independently reproduced denominators. '
                      + versus_real(RUNS, 'speed_mps', from_metrics=True) + '. '
                      + versus_real(RUNS, 'density_veh_km_lane') + '. '
                      + versus_real(RUNS, 'low_speed_share', digits=5) + '.',
             necessary_metric_status='Comparable under the frozen common semantics; no approved margin exists',
             blocking='Without an independent measurement-error bound and an approved delta no pass may be recorded for any kinematic statistic.',
             status='Evidence Insufficient'),
        dict(layer=2, name='following and physical interaction', engineering_status='Computed',
             evidence='net_gap = getLeader distance + follower minGap with the prior 0.0 m same-lane cross-check; closing = follower - leader; the exact step-displacement chain is retained: '
                      + numerical + '. ' + versus_real(RUNS, 'closing_speed_mps', from_metrics=True) + '. '
                      + versus_real(RUNS, 'net_gap_m', from_metrics=True) + '.',
             necessary_metric_status='Distributions and gap/closing means produced on both sides; no approved margin',
             blocking='Simulated closing-speed means are positive while both real windows are negative, so the interaction regime differs in sign, not only magnitude.',
             status='Evidence Insufficient'),
        dict(layer=3, name='risk observability, identity, clock and quality', engineering_status='Verified',
             evidence='Stage 0.2 identity, clock, continuity and quality rules inherited unchanged; 0 rejected formal candidates and 0 right-censored events on every window and run; unknown is never zero-filled; '
                      'the real missing/no-leader vocabulary and the SUMO not_applicable vocabulary stay separate and neither adds to reliable following exposure.',
             necessary_metric_status='Common-semantic mapping required before any label-frequency comparison',
             blocking=None, status='Engineering Consistent (not a scientific pass)'),
        dict(layer=4, name='formal P2 events and evaluable exposure', engineering_status='Verified',
             evidence='Approved D1 attribution implemented and independently recounted; both real windows recomputed on the full follower context before any window cut; global exposure reproduces the sealed Stage 0.2 denominators exactly. '
                      + real_p2,
             necessary_metric_status='Real local P2 and rate are now Calculated (previously Unresolved / Not Calculated)',
             blocking='Comparison with the simulator still requires delta and a state-supported simulator sample.',
             status='Measurement Closed'),
        dict(layer=5, name='target state support, valid sample and precision', engineering_status='Not Satisfied',
             evidence='Every pre-declared 30 s block envelope excludes its own target: ' + envelope
                      + '. The observed internal cross-section flow is reproduced (' + flow + ') but on the free-flow branch, not the observed congested branch. '
                      'One simulator trajectory per condition and no independent-seed repeat executed; local exposure ' + exposure + ' against real interior ' + real_exposure + '.',
             necessary_metric_status='State support absent and precision h unapproved',
             blocking='A conjunctive layer 5 failure cannot be offset by other layers.',
             status='Evidence Insufficient'),
    ]
    return dict(necessary_layers=5, all_layers_required=True, no_compensation_by_weighted_score=True,
                layers=layers, comparison_ready=comparison_ready, conjunctive_verdict='Evidence Insufficient',
                blocking_layers=[layer['layer'] for layer in layers if layer['status'].startswith('Evidence Insufficient')],
                closed_layers=[layer['layer'] for layer in layers if layer['status'] in ('Verified', 'Measurement Closed')],
                scientific_delta_status=delta_audit['status'],
                approved_during_task=False, stage_0_5_gate='pending_simulation_sample',
                protocol_lock_allowed=False, stage_1_1_allowed=False, reality_coverage_accepted=False,
                scientific_claim_eligible=False)


def delta_audit():
    """Record what independent basis exists for a numeric margin and precision target."""
    return dict(
        status='Awaiting Researcher Decision',
        question='Which numeric scientific margin delta and precision h may be approved?',
        independent_evidence_available=dict(
            measurement_system_error_bound=False,
            physical_truth_independent_of_project_sources=False,
            between_seed_variance_available=False,
            downstream_effect_allowance_decided=False),
        facts=[
            'Stage 0.2 closed with independent physical truth and manual geometric truth permanently Unverified, so its residual measurement error has no demonstrated bound.',
            'Stage 0.2 inherits closing epsilon 1e-3 m/s and 100 ms semantics, and the earlier time-step sensitivity showed halving the internal step moves an event boundary by 0.2 s: both describe processing resolution, not an accepted model bias.',
            'The recorded 95% intervals quantify sampling error within one source and one trajectory-cluster structure only. They exclude shared supply, interaction dependence, between-seed variation and model bias.',
            'Two same-day calibration windows cannot identify a road population, so their spread is not an acceptable deviation envelope.',
            'The Energy Distance real-real upper bound remains Not Identifiable and 0.90/0.95 stay engineering defaults.',
            'No independent-seed repeat was executed, so between-seed variance is unobserved rather than shown to be small.',
            'Stage 0.1 numerical checks, the 1e-6 m displacement tolerance and Stage 0.6 analytic truths are engineering correctness, not a simulator-to-reality allowance.',
            'No AAD effect-size requirement has been recorded, so the downstream-impact component of a margin is absent.',
        ],
        forbidden_substitutes=['real statistical fluctuation as delta', 'engineering default as delta',
                               'closest simulator result as delta', 'overlapping confidence intervals as equivalence',
                               'non-significant difference as equivalence', 'small Energy Distance as equivalence'],
        minimum_inputs_for_a_decision=[
            'the maximum model bias later AAD conclusions can tolerate, or an external measurement-study bound',
            'whether a system-error bound B is claimed at all (currently none is demonstrable)',
            'the required precision h for each necessary scalar, with the sample-support consequence stated',
            'confirmation of the target-condition and evaluation-window design that produces a state-supported sample',
        ],
        note='No numeric delta or h was invented. All work independent of this decision was completed.')


def issues_found(reference, sim, support):
    flow_note = '; '.join('%s sim %.1f vs real %.1f veh/h/lane' % (
        r, sim[r]['traffic_metrics']['density_veh_km_lane'] * sim[r]['traffic_metrics']['metrics']['speed_mps']['mean'] * 3.6,
        reference[sim[r]['condition']]['traffic_metrics']['density_veh_km_lane']
        * reference[sim[r]['condition']]['traffic_metrics']['metrics']['speed_mps']['mean'] * 3.6) for r in RUNS)
    return dict(P0_found=0, issues=[
        dict(id='FC-P1-01', severity='P1',
             fact='Both candidate runs reproduce the observed internal cross-section flow (' + flow_note + ') yet sit on the free-flow branch: 20-22 m/s at about 20 veh/km/lane instead of 8-10.5 m/s at 43-50 veh/km/lane.',
             files=['code/scripts/run_stage_0_5_closure_candidate.py::prepare', 'state_support_verdict.json'],
             impact='Layer 5 state support fails for both target conditions, so no five-layer conjunction can be evaluated and the simulated local P2 is not comparable to the real local P2.',
             validation='Both runs completed with zero engineering blockers, zero numerical blockers, zero conservation and local-balance residuals, no pending vehicles and a 100% exact-branch pass rate inside the verified fresh/no-stop domain.',
             resolution='Stopped per the frozen pre-declared rule; no third construction run and no independent-seed repeat executed. The cause is the conditional-supply design, not a numerical failure.',
             researcher_decision='D3 target-condition and boundary-supply design, then D5 budget reuse'),
        dict(id='FC-P1-02', severity='P1',
             fact='Simulated closing-speed means are positive (%.2f and %.2f m/s) while both real windows are negative (%.2f and %.2f m/s); simulated low-speed share is %.5f and %.5f against %.5f and %.5f real.' % (
                 sim['FC1']['traffic_metrics']['metrics']['closing_speed_mps']['mean'], sim['FC2']['traffic_metrics']['metrics']['closing_speed_mps']['mean'],
                 reference['us101__0750_0805']['traffic_metrics']['metrics']['closing_speed_mps']['mean'],
                 reference['us101__0805_0820']['traffic_metrics']['metrics']['closing_speed_mps']['mean'],
                 sim['FC1']['traffic_metrics']['low_speed_share'], sim['FC2']['traffic_metrics']['low_speed_share'],
                 reference['us101__0750_0805']['traffic_metrics']['low_speed_share'],
                 reference['us101__0805_0820']['traffic_metrics']['low_speed_share']),
             files=['sim_*_traffic_metrics.json', 'real_*_traffic_metrics.json'],
             impact='Layer 2 interaction regime and layer 1 speed distribution differ in sign, not only magnitude, so a margin discussion is not yet meaningful.',
             validation='Recomputed from the archived metric files on both sides.',
             resolution='Recorded as a factual difference; no behaviour-parameter search was run to force agreement.',
             researcher_decision='D3'),
        dict(id='FC-P1-03', severity='P1',
             fact='FC1 produced zero local onset events inside the frozen evaluation window although its global confirmed-event count is %d; FC2 produced %d onset events at %.2f per evaluable vehicle-hour against real %.2f and %.2f.' % (
                 sim['FC1']['global_confirmed_events'], sim['FC2']['counts']['onset'], sim['FC2']['rate_per_evaluable_vehicle_hour'],
                 reference['us101__0750_0805']['interior']['rate_per_evaluable_vehicle_hour'],
                 reference['us101__0805_0820']['interior']['rate_per_evaluable_vehicle_hour']),
             files=['sim_FC1_P2.json', 'sim_FC2_P2.json'],
             impact='A zero numerator with a non-zero global count is a state-support artefact, not evidence of a safe state; the non-zero run is not rescued by being closer in magnitude either.',
             validation='Event and cluster tables recounted independently; interval semantics preserved.',
             resolution='No window shortened, no seed swapped, no event rule altered, no run hidden.',
             researcher_decision='D2 and D4'),
        dict(id='FC-P1-04', severity='P1',
             fact='No independent measurement-error bound exists anywhere in the closed stages, so the approved error rule cannot be evaluated even in principle at present.',
             files=['code/src/riskprop/stage_0_5_final_closure.py::equivalence', 'delta_h_basis_audit.json'],
             impact='Scientific delta and precision h stay unapproved, so Stage 0.5 cannot pass regardless of simulator state support.',
             validation='The basis audit lists every candidate source and states why each fails to constitute a bound.',
             resolution='equivalence() returns Awaiting Researcher Decision rather than defaulting; no numeric threshold invented.',
             researcher_decision='D4'),
        dict(id='FC-P2-01', severity='P2',
             fact='Three earlier work capsules remain on disk recording superseded preparation attempts: a pytest basetemp collision, a memory-limit stop at 3.23 GB against the unchanged 3 GiB cap, and a string lane_id region filter that produced an empty local set caught by the zero-exposure guard.',
             files=['code/outputs/formal/calibration/stage_0_5_final_closure_v1', 'stage_0_5_final_closure_v2', 'stage_0_5_final_closure_v3'],
             impact='Only the v4 capsule is the executed and verified reference run; earlier attempts must not be read as results.',
             validation='All v4 frozen-file hashes verified; v1-v3 excluded from the evidence export.',
             resolution='Kept locally as history, excluded from portable evidence, and disclosed here.',
             researcher_decision='None'),
        dict(id='FC-P2-02', severity='P2',
             fact='The candidate plan fixes window_s %s while the real reference windows are %s and %s; they are different objects, a 300 s finite-time simulator sample versus 720/660 s of real interior support.' % (
                 plan_window(sim), WINDOWS[GROUPS[0]], WINDOWS[GROUPS[1]]),
             files=['candidate_experiment_plan.json'],
             impact='Exposure per run is %.1f and %.1f vehicle-seconds against real %.1f and %.1f, an order of magnitude lower, so even with state support the interval width would dominate.' % (
                 sim['FC1']['local_evaluable_vehicle_s'], sim['FC2']['local_evaluable_vehicle_s'],
                 reference[GROUPS[0]]['interior']['local_evaluable_vehicle_s'], reference[GROUPS[1]]['interior']['local_evaluable_vehicle_s']),
             validation='Recorded in the budget and handoff files.',
             resolution='Reported as the minimum resource change required, without raising any authorized cap.',
             researcher_decision='D2, D4 and D5'),
    ], absence_of_findings_not_proof_of_universal_correctness=True)


def plan_window(sim):
    return read(SIM / 'experiment_plan.json')['evaluation']['window_s']


def decision_package(reference, sim, support, delta):
    """The single consolidated minimum decision set; nothing else is asked of the researcher."""
    real_rates = '; '.join('%s %.4f [%s]' % (g, reference[g]['interior']['rate_per_evaluable_vehicle_hour'],
                                            reference[g]['interior']['cluster_interval']) for g in GROUPS)
    return dict(
        status='Awaiting Researcher Decision',
        consolidated=True,
        no_further_interruption_intended=True,
        decisions=[
            dict(id='R1', title='Scientific margin delta and precision h, with or without a system-error bound B',
                 why_irreplaceable='D4 approved the error rule but no numeric value; no independent basis exists in the closed stages (see delta_h_basis_audit.json).',
                 evidence=['Real local rates ' + real_rates,
                           'interval semantics exclude shared supply, interaction dependence, between-seed variation and model bias',
                           'Stage 0.2 physical truth permanently Unverified; Energy Distance real-real upper bound Not Identifiable'],
                 options=['approve a numeric delta and h with a stated basis',
                          'authorise a separate task to establish an independent measurement-error bound first',
                          'restrict the accepted scope explicitly and record the consequence'],
                 blocks='Any scientific acceptance of Stage 0.5, regardless of simulator state support.'),
            dict(id='R2', title='Target-condition and boundary-supply design able to reach the observed congested branch',
                 why_irreplaceable='D3 requires the supply/demand/network condition to be frozen before any driving-parameter work; the observed internal flow alone selects the free-flow branch.',
                 evidence=['predeclared block envelopes exclude every target: '
                           + '; '.join('%s v[%.3f,%.3f] k[%.3f,%.3f] vs target v=%.4g k=%.4g' % (
                               c['run_id'], c['predeclared_block_envelope']['speed_mps'][0], c['predeclared_block_envelope']['speed_mps'][1],
                               c['predeclared_block_envelope']['density_veh_km_lane'][0], c['predeclared_block_envelope']['density_veh_km_lane'][1],
                               c['real_target']['mean_speed_mps'], c['real_target']['density_veh_km_lane']) for c in support['per_run']),
                           'internal cross-section flow is reproduced on the wrong fundamental-diagram branch',
                           'driving-parameter tuning is explicitly not an allowed remedy for a supply mismatch'],
                 options=['approve a downstream capacity/bottleneck construction as a conditional supply input',
                          'approve a different approved target condition or a narrower accepted scope',
                          'stop Stage 0.5 at the current measured-reference boundary'],
                 blocks='Layer 5 state support, and therefore the whole five-layer conjunction.'),
            dict(id='R3', title='Evaluation window and warmup definition for a finite-time dynamic target',
                 why_irreplaceable='D2 approved local finite-time state support but the 300 s runs leave no approved post-warmup support; window choice must be fixed before runs and never on P2 outcomes.',
                 evidence=['candidate evaluation window [180.0, 299.7] is a 119.7 s slice',
                           'local exposure per run %.1f and %.1f veh-s against real %.1f and %.1f' % (
                               sim['FC1']['local_evaluable_vehicle_s'], sim['FC2']['local_evaluable_vehicle_s'],
                               reference[GROUPS[0]]['interior']['local_evaluable_vehicle_s'],
                               reference[GROUPS[1]]['interior']['local_evaluable_vehicle_s']),
                           'the 450 s extension was not admitted and no resource cap was raised'],
                 options=['freeze a longer acquisition with a pre-declared warmup and evaluation rule',
                          'accept a finite-time dynamic target with a pre-declared profile',
                          'defer until R2 fixes the supply design'],
                 blocks='Valid sample support and therefore any precision statement.'),
            dict(id='R4', title='Reuse of the remaining three authorised trajectory runs',
                 why_irreplaceable='D5 reserves at least two runs for independent-seed repeats after freeze; the third construction run cannot cover both target conditions.',
                 evidence=['2 of 5 used (FC1, FC2), 0 repeats attempted, 3 preserved',
                           'the frozen pre-declared rule forbids further search after an envelope failure'],
                 options=['keep the budget reserved until R2 and R3 are decided',
                          'authorise a new pre-declared candidate plan together with an explicit resource change'],
                 blocks='Independent-seed uncertainty and the third-window validation.'),
            dict(id='R5', title='Third-window validation protocol',
                 why_irreplaceable='Task E only permits the third real window after code, parameters, configuration, metrics and statistics are all frozen; that precondition is unmet.',
                 evidence=['third-window rows materialised 0; locked holdout readings 0; validation window never opened',
                           'no frozen acceptance protocol exists because delta, h and layer 5 remain open'],
                 options=['defer the validation protocol to a separate authorised task',
                          'freeze the protocol together with R1-R3 and then run it once'],
                 blocks='Any claim of independent validation, and therefore Stage 0.5.5.'),
        ],
        explicitly_not_requested=['permission for ordinary engineering fixes', 'permission to keep documenting evidence',
                                  'any change to Stage 0.2 or Stage 0.3 semantics'],
        note='This is the only decision request produced by this task. No numeric threshold was invented and no failure was hidden.')


def budget_ledger():
    plan = read(SIM / 'experiment_plan.json')
    ledger = read(SIM / 'execution_ledger.json')
    return dict(previous_targeted_used=plan['budget']['previous_targeted_used'],
                authorized_new_trajectory_runs=plan['budget']['new_max'],
                actual_new_trajectory_runs=ledger['actual_new_attempts'],
                runs=[dict(run_id=x['run_id'], role=x['role'], condition=x['condition'], seed=x['seed'], status=x['status'],
                           observed_s=x.get('observed_s')) for x in ledger['runs']],
                remaining_after_task=plan['budget']['new_max'] - ledger['actual_new_attempts'],
                reserved_independent_repeats='Preserved, not attempted',
                unallocated=plan['budget']['unallocated'],
                micro_budget_remaining=plan['budget']['micro_remaining'],
                third_construction_run='Available but deliberately not used: one changed-boundary run cannot satisfy both target conditions and the frozen rule forbids further search',
                ABCD_runs=0, formal_calibration_runs=0, validation_window_rows_materialised=0,
                holdout_rows_materialised=0, new_real_raw_trajectory_reads=0,
                software_smoke_records=dict(empty_preflight_software_smokes=read(SIM / 'empty_preflight.json')['software_smokes'],
                                            counted_separately=True, included_in_trajectory_budget=False),
                scientific_claim_eligible=False)


def isolation():
    probe = read(SIM / 'isolation_probe.json')
    return dict(
        calibration_sources=GROUPS, validation_source='us101__0820_0835',
        third_window_access=False, third_window_rows_materialised=0,
        locked_holdout_access=False, old_full_source_event_table_access=False,
        guard_fail_closed=True,
        negative_role_probe=dict(passed=probe['passed'], expected_denials=probe['expected_denials'],
                                 denials=['calibration role asked for the third window',
                                          'locked-holdout role asked for a calibration source',
                                          'path outside the capsule']),
        real_data_read_by_type='Only the two SHA-bound canonical calibration state files, staged into a fresh Python -S capsule',
        python_audit_scope='Controlled Python entrypoints only; os_complete_monitoring=false, native_file_access_monitored=false, same-user administrator bypass possible; not an adversarial security boundary',
        validation_after_freeze='Not performed: the acceptance protocol is not frozen because delta, h and layer 5 remain open, so opening the third window would be unauthorized',
        failure_preserved='FC1 and FC2 records, access audits and logs retained; nothing rerun or overwritten')


def handoff(reference, sim):
    return dict(
        stage_0_5_gate='pending_simulation_sample',
        what_closed=[
            'Approved D1 attribution implemented and independently recounted on both real windows, so formal local P2 and rate are now Calculated instead of Unresolved / Not Calculated',
            'Independent cluster and pre-declared time-block uncertainty for both real target rates: '
            + '; '.join('%s %.2f events, %.1f veh-s, rate %.4f, cluster interval %s' % (
                g, reference[g]['interior']['counts']['onset'], reference[g]['interior']['local_evaluable_vehicle_s'],
                reference[g]['interior']['rate_per_evaluable_vehicle_hour'], reference[g]['interior']['cluster_interval']) for g in GROUPS),
            'A frozen, hash-bound conditional candidate design plus two completed construction runs with full numerical, conservation and accounting evidence',
            'An explicit audit of what independent basis exists for delta and h (answer: none currently demonstrable)'],
        what_remains_open=[
            'Researcher decision on the target-condition and boundary-supply design able to place the simulator on the observed congested branch (D3)',
            'Numeric scientific margin delta and precision h, plus any claimed system-error bound B (D4)',
            'Formal evaluation-window and warmup decision for a finite-time dynamic target (D2)',
            'Execution of the preserved independent-seed repeats and the frozen-code third-window validation, only after the above are frozen (D5, task E)',
            'Stage 0.6 regeneration of protocol-lock readiness under the current stage keys'],
        safe_reuse_for_stage_0_6=[
            'The unchanged Stage 0.2 P2 event core plus the D1 attribution module and its 12 hand-computed expected-value tests',
            'Real-window event, member-support and cluster tables with independently reproduced sealed denominators',
            'The conditional candidate network, demand and fleet inputs with SHA bindings, as engineering conditions and not as calibrated parameters',
            'The finite process-tree supervisor with no-retry and controller-hash guards',
            'The Python -S capsule isolation guards and the negative-role access probe'],
        must_not_be_reused_as=['Any claim of reality coverage', 'Any candidate traffic state as a calibrated parameter set',
                                'Confidence intervals as tolerances', 'The unexecuted FR1/FR2 and third-window branch as completed evidence'],
        entry_conditions_for_stage_0_6=['All five necessary layers satisfied for the approved scope',
                                        'delta and h approved with a stated basis', 'Independent-seed variability quantified',
                                        'Frozen-code third-window validation executed and retained'],
        explicitly_not_started=['Stage 0.6 protocol lock', 'Stage 1.1', 'ABCD main matrix', 'Communication intervention experiments'])


def package(staging):
    out = Path(staging) / 'summary'
    if out.exists(): raise PermissionError('new_staging_required')
    out.mkdir(parents=True)
    plan = read(SIM / 'experiment_plan.json')
    event_rows, member_rows, cluster_rows = [], [], []
    reference = real_side(out, event_rows, member_rows, cluster_rows)
    sim = sim_side(out, plan, event_rows, member_rows, cluster_rows)
    write_tables(out, event_rows, member_rows, cluster_rows)
    support = state_support(plan, {g: reference[g]['traffic_metrics'] for g in GROUPS}, sim)
    delta = delta_audit()
    write(out / 'state_support_verdict.json', support)
    write(out / 'delta_h_basis_audit.json', delta)
    write(out / 'five_layer_admission.json', five_layers(reference, sim, support, delta, plan))
    write(out / 'execution_ledger.json', budget_ledger())
    write(out / 'isolation_evidence.json', isolation())
    write(out / 'issue_discovery_report.json', issues_found(reference, sim, support))
    write(out / 'researcher_decision_package.json', decision_package(reference, sim, support, delta))
    write(out / 'stage_0_6_handoff.json', handoff(reference, sim))
    write(out / 'candidate_run_summary.json', sim)
    shutil.copyfile(SIM / 'experiment_plan.json', out / 'candidate_experiment_plan.json')
    shutil.copyfile(SIM / 'PLAN_SHA256', out / 'candidate_PLAN_SHA256')
    shutil.copyfile(SIM / 'empty_preflight.json', out / 'candidate_empty_preflight.json')
    shutil.copyfile(SIM / 'isolation_probe.json', out / 'candidate_isolation_probe.json')
    shutil.copyfile(SIM / 'execution_guard_audit.json', out / 'candidate_execution_guard_audit.json')
    shutil.copyfile(SIM / 'execution_ledger.json', out / 'candidate_run_ledger.json')
    for name in ['reference_plan.json', 'REFERENCE_PLAN_SHA256', 'statistics_plan.json', 'source_manifest.json',
                 'isolation_policy.json', 'preparation.json', 'test_pass.json']:
        shutil.copyfile(REF / name, out / ('reference_' + name))
    for path in sorted(REF.glob('*_access_audit.json')):
        shutil.copyfile(path, out / ('reference_' + path.name))
    for path in sorted(SIM.glob('*_access_audit.json')):
        shutil.copyfile(path, out / ('candidate_' + path.name))
    write(out / 'historical_status_preservation.json', dict(
        preserved=[
            'RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1 keeps its own sealed bytes; its local_measurement_candidate status was Proposed / Awaiting Researcher Decision and is superseded in policy only by the researcher D1 approval recorded 2026-10-20',
            'historical 86/87/86/83 local attribution counts on the single LF3 engineering trajectory unchanged',
            'B0 task_data_isolation_accepted=false and validation_window_rows_materialised=Unknown unchanged',
            'B1 C completed_with_engineering_blocker and D not_attempted unchanged',
            'B1.1 Pending Numerical Equivalence; B1.1-S 947/948; B1.2 terminal-speed conflict and 0/8 main matrix; B1.2-N integration_allowed=false; B1.2-P restricted branch only',
            'C/D entry spillback stays Evidence Insufficient at the about 14.35 m anchor gap',
            'Stage 0.2 and Stage 0.3 limited-scope pass records untouched; no threshold, denominator or event rule modified'],
        d1_policy_transition=dict(before='Proposed / Awaiting Researcher Decision', after='Approved Research Decision 2026-10-20',
                                 historical_package_bytes_rewritten=False),
        no_retrospective_promotion=True))
    audit = dict(result_id=RESULT_ID, status='closed_evidence_insufficient_for_acceptance',
                 gate='pending_simulation_sample', d1_policy='Approved 2026-10-20',
                 real_local_p2={g: dict(events=reference[g]['interior']['counts']['onset'],
                                        exposure_vehicle_s=reference[g]['interior']['local_evaluable_vehicle_s'],
                                        rate=reference[g]['interior']['rate_per_evaluable_vehicle_hour']) for g in GROUPS},
                 formal_local_P2='Calculated for both approved calibration windows',
                 formal_local_rate='Calculated for both approved calibration windows',
                 five_layer_verdict='Evidence Insufficient',
                 state_support=support['verdict'],
                 scientific_delta_approved=False, precision_h_approved=False,
                 new_SUMO_runs=budget_ledger()['actual_new_trajectory_runs'],
                 targeted_runs_remaining=budget_ledger()['remaining_after_task'],
                 reserved_repeats='Preserved, not attempted',
                 ABCD_runs=0, formal_calibration_runs=0,
                 actual_validation_window_reads=0, holdout_reads=0,
                 reality_coverage_accepted=False, scientific_claim_eligible=False,
                 ready_to_start_stage_0_5_4b=False, protocol_lock_allowed=False, stage_1_1_allowed=False,
                 tolerance_status='Tolerance Not Yet Justified',
                 energy_distance_real_real_upper_bound='Not Identifiable',
                 C_entry_spillback='Evidence Insufficient')
    write(out / 'audit.json', audit)
    write(out / 'provenance.json', dict(
        result_id=RESULT_ID, base_commit=read(REF / 'preparation.json')['base_commit'],
        reference_plan_sha256=sha(REF / 'reference_plan.json'),
        statistics_plan_sha256=sha(REF / 'statistics_plan.json'),
        candidate_plan_sha256=sha(SIM / 'experiment_plan.json'),
        implementation=dict(path='code/src/riskprop/stage_0_5_final_closure.py', sha256=sha(ROOT / 'code/src/riskprop/stage_0_5_final_closure.py')),
        reference_entry=dict(path='code/scripts/run_stage_0_5_final_closure.py', sha256=sha(ROOT / 'code/scripts/run_stage_0_5_final_closure.py')),
        candidate_entry=dict(path='code/scripts/run_stage_0_5_closure_candidate.py', sha256=sha(ROOT / 'code/scripts/run_stage_0_5_closure_candidate.py')),
        supervisor=dict(path='code/scripts/supervise_stage_0_5_closure.py', sha256=sha(ROOT / 'code/scripts/supervise_stage_0_5_closure.py')),
        assembler=dict(path='code/scripts/package_stage_0_5_final_closure.py', sha256=sha(Path(__file__))),
        sumo_binary_sha256=plan['sumo_binary_sha256'],
        capsules=dict(reference='code/outputs/formal/calibration/stage_0_5_final_closure_v4',
                      candidate='code/outputs/formal/calibration/stage_0_5_final_candidate_v1',
                      superseded_preparation_attempts=['stage_0_5_final_closure_v1', 'stage_0_5_final_closure_v2', 'stage_0_5_final_closure_v3']),
        raw_state_exported=False, third_window_accessed=False, holdout_accessed=False))
    return out


def seal(out):
    out = Path(out)
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name not in ('manifest.json', 'SHA256SUMS'))
    large = [p.name for p in files if p.stat().st_size > MAX_BYTES]
    if large: raise ValueError('portable_file_too_large:' + ','.join(large))
    write(out / 'manifest.json', dict(result_id=RESULT_ID, files=[dict(path=p.name, sha256=sha(p), bytes=p.stat().st_size) for p in files]))
    (out / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files + [out / 'manifest.json']), encoding='utf-8', newline='\n')


def verify(out, repo=None):
    out = Path(out)
    manifest = read(out / 'manifest.json')
    declared = {e['path']: e for e in manifest['files']}
    actual = {p.name for p in out.iterdir() if p.is_file()}
    if actual != set(declared) | {'manifest.json', 'SHA256SUMS'}: raise ValueError('file_inventory')
    for name, entry in declared.items():
        if Path(name).name != name: raise ValueError('nested_path')
        path = out / name
        if sha(path) != entry['sha256'] or path.stat().st_size != entry['bytes']: raise ValueError('file_SHA:' + name)
        if path.stat().st_size > MAX_BYTES: raise ValueError('oversize:' + name)
    for line in (out / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        if Path(name).name != name or sha(out / name) != digest: raise ValueError('sums_SHA:' + name)
    support = read(out / 'state_support_verdict.json')
    layers = read(out / 'five_layer_admission.json')
    reference = read(out / 'real_local_reference_summary.json')
    sim = read(out / 'candidate_run_summary.json')
    ledger = read(out / 'execution_ledger.json')
    isolation_file = read(out / 'isolation_evidence.json')
    delta = read(out / 'delta_h_basis_audit.json')
    audit = read(out / 'audit.json')
    # Recompute the published figures from the exported tables, not from any summary.
    events = rows(out / 'event_attribution_audit.csv')
    members = rows(out / 'member_support_audit.csv')
    clusters = rows(out / 'cluster_exposure_audit.csv')
    if {e['event_id'] for e in members} != {e['event_id'] for e in events}: raise ValueError('member_support_coverage')
    if len({(e['side'], e['condition'], e['event_id']) for e in events}) != len(events): raise ValueError('duplicate_event_row')
    counts = {}
    for g in GROUPS:
        interior = reference[g]['interior']
        lo, hi = interior['window_s']
        group = [e for e in events if e['side'] == 'real' and e['condition'] == g]
        onset = sum(1 for e in group if truth(e['onset']) and truth(e['onset_in_window']) and lo <= num(e['onset_s']) < hi)
        by_cluster = {}
        for c in clusters:
            if c['side'] == 'real' and c['condition'] == g: by_cluster[c['trajectory_id']] = (num(c['evaluable_s']), int(c['onset_events']))
        exposure = round(sum(v[0] for v in by_cluster.values()), 1)
        if onset != interior['counts']['onset']: raise ValueError('recount_onset:' + g)
        if sum(v[1] for v in by_cluster.values()) != onset: raise ValueError('recount_cluster_events:' + g)
        if not math.isclose(exposure, interior['local_evaluable_vehicle_s'], abs_tol=0.05): raise ValueError('recount_exposure:' + g)
        if abs(interior['rate_per_evaluable_vehicle_hour'] - 3600 * onset / exposure) > 1e-6: raise ValueError('recount_rate:' + g)
        counts[g] = onset
    if counts != REAL_ONSET: raise ValueError('reference_counts_promotion')
    if audit['real_local_p2'] != {g: dict(events=reference[g]['interior']['counts']['onset'],
                                          exposure_vehicle_s=reference[g]['interior']['local_evaluable_vehicle_s'],
                                          rate=reference[g]['interior']['rate_per_evaluable_vehicle_hour']) for g in GROUPS}:
        raise ValueError('audit_reference_mismatch')
    for r in RUNS:
        lo, hi = sim[r]['evaluation_window_s']
        group = [e for e in events if e['side'] == 'sim' and e['condition'] == r]
        onset = sum(1 for e in group if truth(e['onset']) and lo <= num(e['onset_s']) < hi)
        exposure = round(sum(num(c['evaluable_s']) for c in clusters if c['side'] == 'sim' and c['condition'] == r), 1)
        if onset != sim[r]['counts']['onset'] or sim[r]['cluster_onset_total'] != onset: raise ValueError('sim_recount:' + r)
        if not math.isclose(exposure, sim[r]['local_evaluable_vehicle_s'], abs_tol=0.05): raise ValueError('sim_exposure:' + r)
    if support['all_targets_inside_envelope'] or support['verdict'] != 'EvidenceInsufficient_StateSupport': raise ValueError('state_support_promotion')
    if layers['conjunctive_verdict'] != 'Evidence Insufficient' or layers['approved_during_task'] or not layers['no_compensation_by_weighted_score']:
        raise ValueError('layer_promotion')
    if {layer['layer'] for layer in layers['layers']} != {1, 2, 3, 4, 5}: raise ValueError('necessary_layers')
    if 5 not in layers['blocking_layers']: raise ValueError('blocking_layer_record')
    if delta['status'] != 'Awaiting Researcher Decision' or any(v is True for v in delta['independent_evidence_available'].values()):
        raise ValueError('delta_promotion')
    package_decisions = read(out / 'researcher_decision_package.json')
    if package_decisions['status'] != 'Awaiting Researcher Decision' or len(package_decisions['decisions']) != 5:
        raise ValueError('decision_package_state')
    if {d['id'] for d in package_decisions['decisions']} != {'R1', 'R2', 'R3', 'R4', 'R5'}:
        raise ValueError('decision_package_ids')
    if ledger['ABCD_runs'] or ledger['formal_calibration_runs'] or ledger['validation_window_rows_materialised'] or ledger['holdout_rows_materialised']:
        raise ValueError('budget_promotion')
    if ledger['actual_new_trajectory_runs'] > ledger['authorized_new_trajectory_runs'] or ledger['remaining_after_task'] != 3:
        raise ValueError('budget_state')
    if isolation_file['third_window_access'] or isolation_file['locked_holdout_access'] or isolation_file['old_full_source_event_table_access']:
        raise ValueError('isolation_promotion')
    if isolation_file['third_window_rows_materialised'] or not isolation_file['negative_role_probe']['passed']: raise ValueError('isolation_probe')
    for g in GROUPS:
        provenance = reference[g]['provenance']
        if provenance['old_formal_events_read'] or provenance['validation_window_read'] or provenance['locked_holdout_accessed'] \
                or provenance['third_window_rows_materialised'] or provenance['denied_requests']:
            raise ValueError('source_scope:' + g)
        for key in ['interior', 'full_acquisition']:
            if reference[g][key]['event_rows'] != SEALED_GLOBAL_EVENTS[g]: raise ValueError('event_scope:' + g)
            if reference[g][key]['rejected_formal_candidates'] or reference[g][key]['right_censored_unconfirmed']:
                raise ValueError('unexpected_rejection:' + g)
    if any(audit[k] for k in ['reality_coverage_accepted', 'scientific_claim_eligible', 'ready_to_start_stage_0_5_4b',
                              'protocol_lock_allowed', 'stage_1_1_allowed']): raise ValueError('gate_promotion')
    if audit['scientific_delta_approved'] or audit['precision_h_approved'] or audit['ABCD_runs']: raise ValueError('approval_promotion')
    if audit['gate'] != 'pending_simulation_sample' or audit['C_entry_spillback'] != 'Evidence Insufficient': raise ValueError('gate_state')
    if 'Calculated' not in audit['formal_local_P2'] or 'Calculated' not in audit['formal_local_rate']: raise ValueError('reference_status')
    if repo:
        prov = read(out / 'provenance.json')
        for name in ['implementation', 'reference_entry', 'candidate_entry', 'supervisor', 'assembler']:
            entry = prov[name]
            raw = (Path(repo) / entry['path']).read_bytes().replace(b'\r\n', b'\n')
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError('source_binding_' + name)
        for name, exported in [('reference_plan_sha256', 'reference_reference_plan.json'),
                               ('statistics_plan_sha256', 'reference_statistics_plan.json'),
                               ('candidate_plan_sha256', 'candidate_experiment_plan.json')]:
            if sha(out / exported) != prov[name]: raise ValueError('plan_binding_' + name)
    result = dict(passed=True, real_local_events=counts, new_SUMO_runs=ledger['actual_new_trajectory_runs'],
                  budget_remaining=ledger['remaining_after_task'], five_layer=layers['conjunctive_verdict'],
                  state_support=support['verdict'], scientific_delta=delta['status'],
                  stage_0_5_gate=audit['gate'], evidence_files=len(declared))
    print(json.dumps(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['package', 'seal', 'verify'])
    parser.add_argument('path', type=Path)
    parser.add_argument('--repo-root', type=Path)
    args = parser.parse_args()
    target = args.path.resolve()
    if args.mode == 'package':
        package(target)
    elif args.mode == 'seal':
        seal(target / 'summary' if (target / 'summary').is_dir() else target)
    else:
        verify(target / 'summary' if (target / 'summary').is_dir() else target, args.repo_root)


if __name__ == '__main__':
    main()
