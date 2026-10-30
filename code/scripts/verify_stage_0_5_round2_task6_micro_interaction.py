"""Read-only independent validation of portable Task6 evidence; no simulation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT_ID = 'RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def csv_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def safe_file(package, name):
    path = (package / name).resolve()
    if not path.is_relative_to(package.resolve()) or path.parent != package.resolve():
        raise ValueError('Manifest path must be a single file inside Task6 package')
    return path


def verify(root=ROOT, local_inputs=False, sealed=True):
    package = root / 'evidence/results' / RESULT_ID
    if sealed:
        manifest = load(package/'manifest.json')
        files = manifest['payload_files']
        assert 'manifest.json' not in files and 'SHA256SUMS' not in files
        for name, expected in files.items():
            assert digest(safe_file(package,name)) == expected, name
        sums = {}
        for line in (package/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected, name = line.split('  ',1)
            assert name not in sums, 'Duplicate checksum member'
            sums[name] = expected
            assert digest(safe_file(package,name)) == expected, name
        assert set(sums) == set(files) | {'manifest.json'}
        assert {p.name for p in package.iterdir() if p.is_file()} == set(sums) | {'SHA256SUMS'}
    for path in package.glob('*.csv'):
        assert path.stat().st_size <= 256*1024, f'Portable file too large: {path.name}'
        with path.open(encoding='utf-8',newline='') as stream:
            cols = next(csv.reader(stream))
        assert not set(cols) & {'vehicle_id','trajectory_id','leader_id','leader_trajectory_id','event_id'}, path.name
    binding = load(package/'source_bindings.json')
    for name, expected in binding['source_sha256'].items():
        assert digest(root/name) == expected, f'Source changed: {name}'
    input_checks = 0
    if local_inputs:
        for name, spec in binding['inputs'].items():
            assert digest(root/name) == spec['actual_sha256'], name
            if 'expected_sha256' in spec:
                assert spec['actual_sha256'] == spec['expected_sha256'], name
            input_checks += 1
    for rid in ['RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030','RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030']:
        historical = root/'evidence/results'/rid
        assert digest(historical/'SHA256SUMS') == binding['historical_evidence'][rid]['sha256sums']
        for line in (historical/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected, name = line.split('  ',1)
            assert digest(historical/name) == expected, rid+'/'+name
    validation = load(package/'analysis_validation.json')
    assert validation['status'] == 'PASS'
    expected = {'0750_0805':(543,111425.9,167,174),'0805_0820':(732,133505.6,159,252),'B00_A03':(0,None,0,0),'Round2_minGap1.0':(1,None,0,1)}
    for record in validation['datasets']:
        total, exposure, source, target = expected[record['scope']]
        assert record['full_extracted_events'] == total
        if exposure is not None:
            assert abs(record['full_p2_exposure_s']-exposure) < 1e-7
        a = record['attribution']
        assert a['source'] == source and a['target'] == target
        assert a['unique'] == total and a['unmatched'] == a['ambiguous'] == a['unknown'] == 0
        assert sum(a[k] for k in ['source','target','other_mainline','auxiliary_or_other','unknown']) == total
    joint = [r for r in csv_rows(package/'joint_distribution_summary.csv') if r['stratum']=='all']
    assert len(joint) == 8
    hist = csv_rows(package/'gap_closing_joint_histogram.csv')
    blocks = csv_rows(package/'independent_time_block_joint_metrics.csv')
    for row in joint:
        group = lambda r: r['scope']==row['scope'] and r['region']==row['region']
        assert sum(int(r['rows']) for r in hist if group(r)) == int(row['positive_closing_rows'])
        assert sum(int(r['risk_point_rows']) for r in hist if group(r)) == int(row['risk_point_rows_0_lt_ttc_lt_2'])
        for col in ['observed_rows','evaluable_point_rows','positive_closing_rows','risk_point_rows_0_lt_ttc_lt_2']:
            assert sum(int(r[col]) for r in blocks if group(r)) == int(row[col]), (row['scope'],col)
        if row['ttc_ratio_max_abs_error_s']:
            assert float(row['ttc_ratio_max_abs_error_s']) < 1e-8
    for row in blocks:
        assert 0 < float(row['effective_duration_s']) <= 30+1e-8
        assert abs(float(row['block_end_s'])-float(row['block_start_s'])-float(row['effective_duration_s'])) < 1e-7
    contexts = csv_rows(package/'event_context_summary.csv')
    for row in contexts:
        n = int(row['samples'])
        for key in row:
            if key.endswith('_yes'):
                stem = key[:-4]
                assert int(row[key]) <= int(row[stem+'_known']) <= n
                assert int(row[stem+'_known'])+int(row[stem+'_unknown']) == n
        assert int(row['complete_context_without_observed_transition_yes']) <= int(row['full_pair_role_context_yes'])
    for label, count in [('B00_A03',4),('Round2_minGap1.0',3)]:
        near = [r for r in contexts if r['scope']==label and r['sample_kind']=='near_TTC_2_to_3']
        assert len(near)==1 and int(near[0]['samples'])==count
    for match in load(package/'control_matching_audit.json'):
        assert match['events']==match['matched_controls']+match['unmatched_controls']
        for h in [1,2,3]:
            cases=[r for r in contexts if r['scope']==match['scope'] and r['region']==match['region'] and float(r['horizon_s'])==h and r['sample_kind']=='formal_event']
            controls=[r for r in contexts if r['scope']==match['scope'] and r['region']==match['region'] and float(r['horizon_s'])==h and r['sample_kind']=='nonrisk_control']
            assert len(cases)==len(controls)==1
            assert int(cases[0]['samples'])==match['events'] and int(controls[0]['samples'])==match['matched_controls']
    return {'status':'PASS', 'sealed':sealed, 'local_input_hashes_verified':input_checks, 'joint_groups':len(joint), 'context_groups':len(contexts), 'official_events_and_exposures_reproduced':True, 'historical_task4_task5_unchanged':True, 'identity_level_csv_columns':0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--local-inputs', action='store_true')
    parser.add_argument('--unsealed', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.repo_root,args.local_inputs,not args.unsealed),sort_keys=True))
