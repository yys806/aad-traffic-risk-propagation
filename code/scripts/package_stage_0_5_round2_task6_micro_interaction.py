"""Package Task6 aggregates after analysis; never touches source trajectories."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

import analyze_stage_0_5_round2_task6_micro_interaction as analysis
import verify_stage_0_5_round2_task6_micro_interaction as independent


def prepare():
    out = analysis.OUT
    path = out/'event_relative_profiles.csv'
    full = pd.read_csv(path)
    if 'speed_mps_mean' in full:
        shutil.copyfile(path, analysis.LOCAL/'event_relative_profiles_full.csv')
    names = ['scope','region','sample_kind','role','relative_tick','samples']
    for metric in ['speed_mps','gap_m','closing_mps','acceleration_mps2']:
        names.extend(metric+'_'+stat for stat in ['n','p25','p50','p75'])
    full[names].to_csv(path,index=False, float_format='%.10g')
    binding = independent.load(out/'source_bindings.json')
    for path in [Path(__file__).resolve(), Path(independent.__file__).resolve(), analysis.ROOT/'code/tests/test_stage_0_5_round2_task6_micro_interaction.py']:
        binding['source_sha256'][path.relative_to(analysis.ROOT).as_posix()] = analysis.sha(path)
    binding['aggregate_packaging'] = 'Analysis produces full quantiles; this stage retains count and IQR/median profiles only. Full aggregate profiles remain in ignored local output.'
    analysis.write_json(out/'source_bindings.json', binding)
    return independent.verify(sealed=False)


def seal():
    result = prepare()
    engineering = independent.load(analysis.OUT/'engineering_validation.json')
    if engineering['status'] != 'PASS':
        raise ValueError('Do not seal unfinished or failed engineering validation as Pass')
    analysis.write_json(analysis.OUT/'validation_record.json', {
        'status':'PASS_OFFLINE_TASK6', 'analysis':independent.load(analysis.OUT/'analysis_validation.json'),
        'independent_aggregate_validation':result, 'engineering':engineering,
        'science_boundary':'descriptive findings only; no equivalence, Model Discrepancy, physical propagation or Gate acceptance',
        'historical_limitation':'METHOD-EXPANSION run_metadata hash mismatch and missing trajectory_coverage_matrix retained; only separately SHA-verified result summaries reused'})
    payload = sorted(p.name for p in analysis.OUT.iterdir() if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'})
    manifest = {'schema':'aad.stage05.round2.task6.manifest.v1', 'task_id':'AAD-S0.5-ROUND2-TASK6',
                'base_head':'8311336779f77cd18b1411ab299959d463a2dffc', 'payload_files':{name:analysis.sha(analysis.OUT/name) for name in payload},
                'identity_level_data_in_package':False, 'new_native_launches':0, 'source_bindings':'source_bindings.json'}
    analysis.write_json(analysis.OUT/'manifest.json',manifest)
    (analysis.OUT/'SHA256SUMS').write_text(''.join(analysis.sha(analysis.OUT/name)+'  '+name+'\n' for name in payload+['manifest.json']),encoding='utf-8')
    return independent.verify(sealed=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal',action='store_true')
    args = parser.parse_args()
    print(seal() if args.seal else prepare())
