"""Package weekly calibration evidence; never launch or rewrite raw capsules."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

TASK = 'AAD-WEEK-2026-10-27-TO-STAGE-I-V1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compact(value):
    """Portable aggregates reference full local certificates instead of ID tables."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in {'status_by_vehicle', 'runtime_files_sha256', 'vehicles', 'identities', 'ticks'}:
                result[key + '_count'] = len(item)
                result[key + '_storage'] = 'Full unchanged local source; SHA-256 in provenance.json'
            else:
                result[key] = compact(item)
        return result
    if isinstance(value, list):
        return [compact(item) for item in value]
    return value


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                          encoding='utf-8', newline='\n')


def package(root, validation_path, finalize=False):
    root = Path(root).resolve()
    read = lambda p: json.loads((root / p).read_bytes())
    admission = Path('evidence/admission') / TASK
    proposal_path = admission / 'candidate-v3/proposal.json'
    proposal = read(proposal_path)
    run = proposal['runs'][0]
    work = Path(run['artifact_path'])
    assessment = Path('code/outputs/formal/calibration/aad_week_a03_assessment_v1')
    scene_root = Path('code/outputs/formal/calibration/aad_week_scene_a03_v1')
    budget_root = Path('code/outputs/formal/calibration/stage_0_6_error_budget_week_v2')
    protocol_root = Path('code/outputs/formal/calibration/aad_week_protocol_v1')
    assessment_result = read(assessment / 'assessment_result.json')
    assert assessment_result['status'] == 'B00_EXECUTED_MEASUREMENT_ACCEPTED'
    assert all(assessment_result['checks'].values())
    measurement = read(assessment / 'measurement_acceptance.json')
    native = read(work / 'isolation_runtime.json')
    controller = read(work / 'controller_receipt.json')
    identity = read(work / 'identity_summary.json')
    for name, expected in native['artifact_sha256'].items():
        if sha(root / work / name) != expected:
            raise ValueError('sealed native artifact drift: ' + name)
    scene = read(scene_root / 'audit.json')
    budget = read(budget_root / 'audit.json')
    validation = read(validation_path)
    if finalize and not validation.get('complete'):
        raise ValueError('Final packaging requires completed validation')
    samples = controller['resource_samples']
    max_gap = max(b['wall_s'] - a['wall_s'] for a, b in zip(samples, samples[1:]))
    summary = measurement['verdicts']['initialization_accounting']['evidence']['summary']
    population = compact(summary)
    population.update(lifecycle=scene['lifecycle'],
        collision_coverage_complete=identity['collision_coverage_complete'],
        collision_required_available=identity['API_coverage']['collision_required_available'],
        identity_observations=identity['observations'],
        discard_identity_limit='SUMO provides no verified per-ID discard getter; current aggregate discarded=0 and all IDs accounted; never infer discarded IDs from FCD absence',
        pending_interpretation='Native pending IDs at finite420s end; retained, not auto-failure or inferred from FCD absence')
    failures = []
    for index in [1, 2]:
        p = Path(f'docs/audits/aad_week_20261027/a0{index}_execution_result.json')
        failures.append(dict(record_path=p.as_posix(), record_sha256=sha(root / p), result=read(p)))
    failure_archive = dict(task_id=TASK, B00_real_starts=3,
        prior_task_start_excluded='candidate-v8 first-step failure belongs to prior task; preserved separately',
        resource_rejected_attempts=failures,
        A03_coordinator_failure=dict(reason='ModuleNotFoundError: riskprop after completed native receipt',
            original_ledger_status='measurement_rejected',
            source_snapshot='docs/audits/aad_week_20261027/a03_executed_coordinator_source.py',
            source_snapshot_sha256=sha(root / 'docs/audits/aad_week_20261027/a03_executed_coordinator_source.py'),
            failure_log_sha256=sha(root / work / 'coordinator_import_failure.log'),
            remedy='Direct entry src import fix; same sealed raw trajectory independently accepted under candidate-v4-measurement, native launches0'),
        no_hidden_retries=True, no_same_failed_binding_restart=True,
        historical_Not_Accepted='Unchanged; new validation does not reverse historical scope incidents')
    audit = dict(schema_version='aad.week-native-result.v1', task_id=TASK,
        status=assessment_result['status'], run_id=run['id'],
        B00_real_starts=3, B00_completed_duration_s=[420, 420, 420],
        accepted_native_runs=1, accepted_measurements=1,
        affected_source_integration_smokes=dict(count=2, duration_s_each=3, stages=['r8', 'r9']),
        accepted_run=dict(duration_s=420, internal_step_s=.05, recording_step_s=.1,
            evaluation_window_s=run['evaluation_elapsed_s'], seed=run['seed'],
            internal_steps=len(controller['controls']), native_exit_code=controller['exit_code'],
            capsule_exit_code=native['payload_exit_code'], postrun_assessment_native_launches=0,
            resource_samples=len(samples), max_sample_gap_s=max_gap, max_allowed_gap_s=.5,
            peak_process_tree_rss_bytes=max(s['process_tree_rss_bytes'] for s in samples),
            peak_cgroup_memory_bytes=max(s['cgroup_memory_current_bytes'] for s in samples),
            last_resource_wall_s=samples[-1]['wall_s'],
            disk_free_min_bytes={k:min(s[k] for s in samples) for k in ['free_c_bytes','free_d_bytes','free_wsl_bytes','capsule_fs_free_bytes']},
            output_bytes=native['output_bytes'], watchdog_failure=controller['watchdog_failure'],
            descendants_reaped=native['descendants_reaped'], remaining_pids=native['remaining_pids'],
            resource_supervision_mode=controller['resource_supervision_mode']),
        checks=assessment_result['checks'], population=population['evidence']['final'],
        D1=scene['formal_D1'], all18_common_support=scene['all18_positive_state_and_D1_support'],
        stage_0_5_scientific_gate='blocked', scientific_effect_demonstrated=False,
        initialization_amendment='Only i0007_i0007 departSpeed15.23->10;117 initial audited, DS38 unchanged',
        result_boundary='Native engineering and D1 measurement accepted; no local source P2 event, no scientific interaction equivalence or StageI admission')
    source_names = ['code/scripts/package_aad_week_results_v1.py',
        'code/scripts/analyze_stage_0_5_week_scene_v1.py',
        'code/scripts/assess_stage_0_5_existing_capsule_v1.py',
        'code/scripts/prepare_stage_0_5_initial_speed_v1.py',
        'code/scripts/run_stage_0_5_admission_v3.py',
        'code/scripts/run_stage_0_6_error_budget_v1.py',
        'code/scripts/prepare_aad_week_protocol_v1.py']
    source_paths = [proposal_path, admission / 'candidate-v4-measurement/proposal.json',
        admission / 'candidate-v4-measurement/authorization.json',
        admission / 'candidate-v4-measurement/envelope.json',
        assessment / 'assessment_result.json', assessment / 'measurement_acceptance.json',
        scene_root / 'audit.json', budget_root / 'audit.json', protocol_root / 'manifest.json',
        work / 'identity_summary.json', work / 'controller_receipt.json',
        work / 'isolation_runtime.json', work / 'measured_state.parquet',
        work / 'postrun_assessment_provenance.json', *map(Path, source_names)]
    provenance = dict(schema_version='aad.week-provenance.v1',
        execution_base_commit='e38f5240a6542ceb12ec7325a59899dd834132be',
        execution_dirty_sources='Explicit source bindings below; base commit alone is not claimed as executed source',
        native_execution_proposal=proposal_path.as_posix(),
        native_execution_proposal_sha256=sha(root / proposal_path),
        native_controller_source_sha256=native['source_sha256'],
        executed_policy_sha256=native['policy_sha256'], runtime_manifest_sha256=native['runtime_manifest_sha256'],
        input_sha256=native['input_sha256'], raw_artifact_sha256=native['artifact_sha256'],
        source_file_sha256={p.as_posix():sha(root/p) for p in source_paths},
        native_coordinator_history='The executed coordinator is the archived a03_executed_coordinator_source.py, not the postrun import-fixed current CLI. Other native closure files retain exact executed hashes.',
        authorization_source='Explicit user chat mandate; no asserted digital signature or independent identity authentication',
        full_ID_tables_and_logs='Kept in exact local capsule; portable certificate only removes bulky ID/runtime listings with full-source hashes retained')
    scene_portable = copy.deepcopy(scene)
    scene_portable['measurement_acceptance'] = compact(measurement)
    first = dict(audit=audit, population_accounting=population, measurement_acceptance=compact(measurement),
        independent_execution_receipt=read(assessment / 'independent_execution_receipt.json'),
        scene_audit=scene_portable, failure_archive=failure_archive, provenance=provenance,
        validation_record=validation, ledger_snapshot=read('docs/audits/stage_0_5_ready_to_admit_v3/execution_events.jsonl') if False else None)
    ledger_path = Path('docs/audits/stage_0_5_ready_to_admit_v3/execution_events.jsonl')
    lines = [json.loads(line) for line in (root/ledger_path).read_text().splitlines() if line]
    selected = [line for line in lines if 'WEEK_0750_B00_IC1_' in json.dumps(line)]
    first['ledger_snapshot'] = dict(source_path=ledger_path.as_posix(), source_sha256=sha(root/ledger_path),
        scope='Selected original hash-chain records copied unchanged; full chain remains in source ledger',
        records=selected, postrun_assessment=assessment_result,
        old_status_rewritten=False)
    gates = read(protocol_root / 'current_gate_reports.json')
    second = dict(audit=budget, numerical_manifest=read(budget_root / 'manifest.json'),
        protocol_candidate=read(protocol_root / 'protocol_candidate.json'), current_gate_reports=gates,
        stage_0_5_gate=gates['stage_0_5'], stage_0_6_gate=gates['stage_0_6'],
        protocol_lock_readiness=read(protocol_root / 'protocol_lock_readiness.json'),
        protocol_lock_writer_check=read(protocol_root / 'protocol_lock_writer_check.json'),
        input_manifest=read(protocol_root / 'input_manifest.json'), provenance=provenance, validation_record=validation)
    packages = [(Path('code/outputs/formal/calibration/aad_week_20261027_v1/portable'), first),
        (Path('code/outputs/formal/calibration/stage_0_6_week_20261027_v1/portable'), second)]
    for relative, data in packages:
        output = root / relative
        if (output / 'manifest.json').exists() and read(relative/'manifest.json').get('sealed'):
            raise FileExistsError('Final package is immutable: ' + str(relative))
        output.mkdir(parents=True, exist_ok=True)
        for name, value in data.items():
            dump(output / (name+'.json'), value)
        if data is first:
            (output/'matched18.csv').write_bytes((root/scene_root/'matched18.csv').read_bytes())
        names = sorted(p.name for p in output.iterdir() if p.name not in {'manifest.json','SHA256SUMS'})
        dump(output/'manifest.json',dict(schema_version='aad.week-portable-manifest.v1',
            task_id=TASK, sealed=finalize, files={name:sha(output/name) for name in names}))
        (output/'SHA256SUMS').write_text(''.join(sha(output/name)+'  '+name+'\n' for name in names+['manifest.json']),encoding='utf-8',newline='\n')
    return dict(status=audit['status'], all18=audit['all18_common_support'],
        StageI=second['protocol_lock_readiness'], packages=[str(p) for p,_ in packages], sealed=finalize)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--validation',required=True)
    parser.add_argument('--finalize',action='store_true')
    args=parser.parse_args()
    print(json.dumps(package(args.repo_root,args.validation,args.finalize)))
