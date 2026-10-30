"""Bounded, metadata-only Round2 closure preparation; never launches simulations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = Path('code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs')
RUN_IDS = ['WEEK_0750_B00_IC1_s20261201_A03', 'AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1']
HISTORY = Path('evidence/results/RES-STAGE-0.5-METHOD-EXPANSION-V1')
REQUIRED_B = ('traceable_pair', 'time_indexed_lane_edge_connection',
              'continuous_follower_leader', 'physical_connection_basis', 'verified_transition_order')
SEEDS = [20261101, 20261102, 20261103]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml_differences(a: ET.Element, b: ET.Element, path: str = 'root') -> list[dict]:
    differences = []
    if a.tag != b.tag:
        differences.append(dict(path=path, field='tag', arm_a=a.tag, arm_b=b.tag))
    for key in sorted(set(a.attrib) | set(b.attrib)):
        if a.get(key) != b.get(key):
            differences.append(dict(path=path, field=key, arm_a=a.get(key), arm_b=b.get(key)))
    if (a.text or '').strip() != (b.text or '').strip():
        differences.append(dict(path=path, field='text', arm_a=a.text, arm_b=b.text))
    if (a.tail or '').strip() != (b.tail or '').strip():
        differences.append(dict(path=path, field='tail', arm_a=a.tail, arm_b=b.tail))
    if len(a) != len(b):
        differences.append(dict(path=path, field='children', arm_a=len(a), arm_b=len(b)))
    for index, (left, right) in enumerate(zip(a, b)):
        differences.extend(xml_differences(left, right, f'{path}/{left.tag}[{index}]'))
    return differences


def require_only_min_gap(differences: list[dict]) -> None:
    if len(differences) != 5 or any(
        d['field'] != 'minGap' or d['arm_a'] != '2.5' or d['arm_b'] != '1.0'
        or not d['path'].startswith('root/vType[') for d in differences
    ):
        raise ValueError('Unexpected arm difference; no experiment or semantic repair authorized')


def assess_b(evidence: dict) -> dict:
    """Check completeness of documented B witnesses, not their physical truth."""
    missing = [key for key in REQUIRED_B if not isinstance(evidence.get(key), dict)
               or evidence[key].get('status') != 'Verified'
               or not isinstance(evidence[key].get('evidence_reference'), str)
               or not evidence[key]['evidence_reference'].strip()]
    return {'witness_contract_status': 'Unknown' if missing else 'Documented',
            'missing_requirements': missing,
            'physical_truth_verified_by_this_checker': False}


def replay_review(rows: list[dict]) -> dict:
    result = {'historical_seeds': sorted({int(r['seed']) for r in rows}),
              'n_rows': len(rows), 'duration_s': sorted({float(r['duration_s']) for r in rows}),
              'scope': 'Historical homogeneous 12-pair replay; not current heterogeneous-B00 power evidence',
              'configurations': {}}
    for config in ('K_tau1.0', 'K_tau1.0_minGap1.0'):
        groups = {}
        for row in rows:
            if row['configuration'] == config:
                groups.setdefault((row['window'], row['pair_index']), []).append(row)
        metrics = {}
        for metric in ('brockfeld_gap_error_pct', 'nrmse_gap', 'nrmse_speed', 'response_lag_difference_s'):
            sd = [statistics.stdev([float(r[metric]) for r in group])
                  for group in groups.values() if len(group) == 3 and all(r[metric] for r in group)]
            metrics[metric] = {'pairs': len(sd), 'median_within_pair_seed_sd': statistics.median(sd) if sd else None,
                               'max_within_pair_seed_sd': max(sd) if sd else None}
        result['configurations'][config] = {'pairs': len(groups), 'metrics': metrics}
    return result


def prepare(root: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f'Preserve existing output; choose a new task directory: {output}')
    inputs = []
    for run_id in RUN_IDS:
        inputs += [RUNS / run_id / name for name in ('routes.rou.xml', 'network.net.xml', 'run.sumocfg')]
    inputs += [HISTORY / name for name in ('response_plan.json', 'response_metrics.csv', 'response_summary.json')]
    inputs += [Path('code/configs/stage_0_2_formal_risk_measurement_p2_v1.json'),
               Path('evidence/results/RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030/decision_summary.json')]
    bindings = {p.as_posix(): {'sha256': sha(root / p), 'bytes': (root / p).stat().st_size} for p in inputs}
    trees = [ET.parse(root / RUNS / name / 'routes.rou.xml').getroot() for name in RUN_IDS]
    differences = xml_differences(*trees)
    require_only_min_gap(differences)
    equal = {name: sha(root / RUNS / RUN_IDS[0] / name) == sha(root / RUNS / RUN_IDS[1] / name)
             for name in ('network.net.xml', 'run.sumocfg')}
    if not all(equal.values()):
        raise ValueError('Network/config mismatch; Awaiting Researcher Decision')
    rows = list(csv.DictReader((root / HISTORY / 'response_metrics.csv').open(encoding='utf-8-sig', newline='')))
    replay = replay_review(rows)
    if replay['historical_seeds'] != SEEDS or replay['n_rows'] != 324:
        raise ValueError('Unexpected historical replay design; no inherited seed approval')
    disk = shutil.disk_usage(root)
    path_contract = {'status': 'Agreed', 'independent_of_formal_p2_c': True,
                     'requirements': list(REQUIRED_B), 'current_available_path_witness': assess_b({}),
                     'prohibited_substitutes': ['lane_id_change', 'topology_only', 'boolean_connection_only',
                                              'event_onset_as_arrival', 'local_confirmation_as_arrival', 'unobserved_path_interpolation']}
    conditional = {
        'original_candidate': 'CLOSED_FAILED_ORIGINAL_SOURCE_CONDITION',
        'formal_p2': 'C', 'd1': 'independent_same_native_lane_local_diagnostic',
        'formal_equivalence_accepted': False, 'new_native_launches': 0, 'new_trajectory_reads': 0, 'holdout_reads': 0,
        'video_acquisition': {'decision': 'NO_GO', 'G_V1_license': 'Blocked', 'G_V2_time': 'Blocked',
            'G_V3_space': 'Blocked', 'G_V4_resource': 'Partial: capacity sufficient; final method and scratch needs unverified',
            'compressed_bytes': 1248582779, 'extracted_bytes': 1248560044, 'base_peak_bytes': 2497142823,
            'free_bytes_snapshot': disk.free, 'filesystem_total_bytes': disk.total,
            'reserve_and_tool_overhead_bytes': None, 'recheck_before_acquisition': True,
            'files': [f'sb-camera{c}-{w}.avi' for w in ('0750am-0805am', '0805am-0820am') for c in (7, 8)]},
        'human_review': {'status': 'Blocked', 'sampled_cases': 0, 'risk_cap': 24, 'unique_follower_control_cap': 12,
                         'seed': 20261030, 'preregistration_completed': False, 'human_judgments': 0},
        'fixed_leader': {'status': 'Blocked', 'seed_matrix_status': 'Proposed / Awaiting Researcher Decision',
                         'seeds': SEEDS, 'arms': ['actual_B00', 'actual_Round2_minGap1.0'],
                         'repetitions_per_arm_per_segment': 3, 'runs_per_segment': 6, 'segment_count': None,
                         'total_runs': '6*N after physical-quality qualification and approval',
                         'approved_for_execution': False, 'historical_seed_approval_transfers': False,
                         'estimated_simulated_seconds': '6*sum(T_i)',
                         'estimated_internal_steps_if_h0_05': '120*sum(T_i)',
                         'wall_time_and_output_bytes': None},
        'round3': 'NOT_READY / proposal only', 'protocol_lock_created': False, 'stage_i_executed': False}
    provenance = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
                  'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                  'dirty_worktree': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True).splitlines(),
                  'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
                  'command': 'python code/scripts/prepare_stage_0_5_round2_closure.py --output ' + output.relative_to(root).as_posix(),
                  'source_sha256': sha(Path(__file__)), 'inputs': bindings,
                  'seed_for_metadata_audit': 'Not Applicable; no stochastic execution'}
    output.mkdir(parents=True)
    for name, content in {'arm_config_audit.json': {'differences': differences, 'equal_files': equal,
          'tau_heterogeneity': [float(t.get('tau')) for t in trees[0].findall('vType')], 'scope': 'Verified XML only; no fixed-leader feasibility claim'},
          'historical_replay_review.json': replay, 'physical_path_contract.json': path_contract,
          'conditional_authorization.json': conditional, 'source_bindings.json': provenance}.items():
        (output / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('ROUND2_CLOSURE_METADATA_PREPARED ' + output.as_posix())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(ROOT, args.output.resolve())
