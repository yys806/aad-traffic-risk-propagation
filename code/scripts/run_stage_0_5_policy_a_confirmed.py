"""Researcher-approved policy A: one attempt per invocation, fail closed."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import xml.etree.ElementTree as ET
import psutil
import numpy
import pandas
import pyarrow
import supervise_stage_0_5_diagnostic as supervisor
from interaction_task_boundary import Boundary

ROOT = Path(__file__).resolve().parents[2]
PORTABLE = ROOT / 'evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1'
RESULT = ROOT / 'evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1'
TASK = ROOT / 'code/outputs/formal/calibration/stage_0_5_interaction_diagnostics_v1'
PLAN = ROOT / 'docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md'
PLAN_SHA = 'ba79b36733fcb93b37898250c5c12dbe074efa36af8798ac0cc3644a7bbd39a7'
PROPOSAL_SHA = '0f0d84aec6881c957d10331a96dfd22c809980e53f8726af72599a27d2219f97'
PREPARED = ROOT / 'code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs'


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def runtime_roots():
    roots = [Path(sysconfig.get_path('stdlib')), Path(sys.base_prefix) / 'DLLs',
             Path(sys.base_prefix) / 'python313.zip']
    # User packages are outside the conda stdlib. Permit installed runtime code,
    # never the user's profile or task-unrelated project directories.
    for m in [numpy, pandas, pyarrow, psutil]:
        roots.append(Path(m.__file__).resolve().parent)
    for name in ['dateutil', 'pytz', 'tzdata', 'six']:
        m = __import__(name)
        roots.append(Path(m.__file__).resolve().parent if hasattr(m, '__path__') else Path(m.__file__).resolve())
    return [str(p.resolve()) for p in roots]


def validate_xml(work):
    for name in ['run.sumocfg', 'network.net.xml', 'routes.rou.xml']:
        data = (work / name).read_bytes()
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            raise ValueError('XML_external_entities_forbidden')
        root = ET.fromstring(data)
        for node in root.iter():
            for key, value in node.attrib.items():
                if key.lower() in ('file', 'href'):
                    raise ValueError('nested_file_reference_forbidden')
    cfg = ET.parse(work / 'run.sumocfg').getroot()
    expected = {'net-file': 'network.net.xml', 'route-files': 'routes.rou.xml',
                'fcd-output': 'fcd.xml', 'summary-output': 'summary.xml'}
    for group in cfg:
        for node in group:
            if 'file' in node.tag or 'output' in node.tag:
                if node.tag not in expected or node.get('value') != expected[node.tag]:
                    raise ValueError('unregistered_native_file_reference:' + node.tag)
    for tag, value in expected.items():
        if cfg.find('.//' + tag).get('value') != value:
            raise ValueError('native_file_binding')


def freeze():
    TASK.mkdir(exist_ok=True, parents=True); RESULT.mkdir(exist_ok=True, parents=True)
    proposal_path = PORTABLE / 'review_ready_plan.json'
    if supervisor.sha(PLAN) != PLAN_SHA or supervisor.sha(proposal_path) != PROPOSAL_SHA:
        raise ValueError('approved_exact_plan_or_proposal_changed')
    p = json.loads(proposal_path.read_text())
    rows = []
    for kind in ['source_sha256', 'input_sha256', 'external_file_sha256']:
        for name, expected in p[kind].items():
            path = Path(name) if kind == 'external_file_sha256' else ROOT / name
            actual = supervisor.sha(path)
            rows.append({'kind': kind, 'path': name, 'baseline_sha256': expected,
                         'actual_sha256': actual, 'match': actual == expected})
    for run in p['runs']:
        for name, expected in run['prepared_input_sha256'].items():
            actual = supervisor.sha(PREPARED / run['id'] / name)
            rows.append({'kind': 'prepared', 'path': run['id'] + '/' + name,
                         'baseline_sha256': expected, 'actual_sha256': actual, 'match': actual == expected})
        validate_xml(PREPARED / run['id'])
    resources = json.loads((PORTABLE / 'resource_preflight.json').read_text())
    actual = supervisor.sha(resources['sumo_binary_path'])
    rows.append({'kind': 'binary', 'path': resources['sumo_binary_path'], 'baseline_sha256': resources['sumo_binary_sha256'], 'actual_sha256': actual, 'match': actual == resources['sumo_binary_sha256']})
    if not all(r['match'] for r in rows):
        raise ValueError('readonly_binding_mismatch')
    supervisor.verify_dependencies(p['dependency_versions'])
    engineering = {str(Path(__file__).relative_to(ROOT).as_posix()): supervisor.sha(__file__),
                   'code/scripts/interaction_task_boundary.py': supervisor.sha(ROOT / 'code/scripts/interaction_task_boundary.py')}
    approval = {'researcher_confirmed': True, 'proposal_sha256': PROPOSAL_SHA,
                'plan_sha256': PLAN_SHA, 'decision_record': '2026-10-25 researcher message: 研究者决定：批准政策 A 的最终诊断计划，并对 POLICY-A-VALIDATION-SCOPE-01 作如下裁决。',
                'scope': 'Exact existing scientific proposal confirmed; additive engineering isolation only. Not a Protocol Lock.',
                'incident_isolation_status': 'Not Accepted; deviation retained; researcher permits finite continuation',
                'engineering_sha256': engineering, 'scientific_configuration_changed': False,
                'unknown_baselines': ['New isolation scripts have no historical pre-change baseline; current bytes frozen only', 'No complete runtime file access history for original scope incident'],
                'Gate_changed': False}
    target = RESULT / 'execution_freeze.json'
    if target.exists() and json.loads(target.read_text(encoding='utf-8')) != approval:
        raise ValueError('frozen_engineering_changed_requires_review')
    if not target.exists():
        write(target, approval)
        write(RESULT / 'readonly_hash_verification.json', {'utc': datetime.now(timezone.utc).isoformat(), 'files': rows, 'access': 'read-only byte hashing; no interpretation of unapproved resources'})
    return p, approval, resources


def launch(run_id):
    p, approval, resources = freeze()
    run = next(r for r in p['runs'] if r['id'] == run_id)
    work = TASK / run_id
    if work.exists():
        raise ValueError('existing_capsule_no_retry')
    work.mkdir()
    for name in run['prepared_input_sha256']:
        shutil.copyfile(PREPARED / run_id / name, work / name)
    validate_xml(work)
    binary = Path(resources['sumo_binary_path']).resolve()
    roots = runtime_roots()
    worker_files = [str(ROOT / name) for name in p['source_sha256']]
    worker_files += list(p['external_file_sha256'])
    spec = {'work': str(work), 'binary': str(binary), 'tools': p['traci_tools_root'],
            'scripts': str(ROOT / 'code/scripts'), 'runtime_roots': roots,
            'read_files': worker_files, 'supply': run['role'] == 'supply'}
    write(work / 'boundary_spec.json', spec)
    bootstrap = ROOT / 'code/scripts/interaction_task_boundary.py'
    command = [sys.executable, '-I', '-S', str(bootstrap), str(work / 'boundary_spec.json')]
    reads = worker_files + [str(PORTABLE / 'review_ready_plan.json'), str(PORTABLE / 'resource_preflight.json')]
    reads += [str(ROOT / name) for name in p['input_sha256']]
    reads += [str(bootstrap), str(PLAN), str(binary)]
    reads += [str(PREPARED / r['id'] / name) for r in p['runs'] for name in r['prepared_input_sha256']]
    # Metadata reads by already-loaded dependency verification are runtime only.
    boundary = Boundary(reads, roots, TASK, [{'executable': sys.executable, 'argv': command}])
    original = subprocess.Popen
    def isolated_popen(argv, **kwargs):
        if argv[0] != sys.executable or 'interaction_diagnostic_worker' not in argv[3]:
            raise PermissionError('unexpected_supervisor_command')
        return original(command, executable=sys.executable, **kwargs)
    subprocess.Popen = isolated_popen
    # Already checked above before installing the file boundary. Do not let
    # importlib.metadata enumerate unrelated sys.path entries during execution.
    supervisor.verify_dependencies = lambda versions: None if versions == p['dependency_versions'] else (_ for _ in ()).throw(ValueError('dependency_spec_changed'))
    sys.dont_write_bytecode = True
    sys.addaudithook(boundary.audit)
    snapshot = {'utc': datetime.now(timezone.utc).isoformat(), 'free_C': shutil.disk_usage('C:/').free,
                'free_D': shutil.disk_usage('D:/').free, 'available_memory': psutil.virtual_memory().available}
    write(work / 'resource_before.json', snapshot)
    try:
        supervisor.run_authorized_attempt(ROOT, PORTABLE / 'review_ready_plan.json', approval,
            run_id, work, TASK, TASK / 'execution_ledger.json', binary, Path(p['traci_tools_root']))
    finally:
        boundary.save(work / 'supervisor_boundary_audit.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-only', action='store_true')
    parser.add_argument('--run', choices=['ID1_SUPPLY_0750', 'ID2_SUPPLY_0805', 'ID3_RAMP_0750'])
    a = parser.parse_args()
    if a.freeze_only:
        freeze(); print('EXACT_APPROVAL_AND_READONLY_BINDINGS_VERIFIED; attempts unchanged')
    elif a.run:
        launch(a.run)
    else:
        parser.error('select freeze-only or one approved run')
