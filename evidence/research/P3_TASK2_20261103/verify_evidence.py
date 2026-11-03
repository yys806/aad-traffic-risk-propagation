"""Read-only P3 Task2 hash and synthetic linkage recomputation; never runs SUMO."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path, portable: bool) -> dict:
    bundle = root / 'evidence/research/P3_TASK2_20261103'
    errors = []
    counts = dict(bundle=0, protected_inputs=0, output_bindings=0,
                  local_skipped=0, git_blob_variants=0, scenarios=0, invalid_cases=0)

    def checked(rel: str, expected: str, count: str, git_expected: str | None = None):
        path = (root / rel).resolve()
        if not path.is_relative_to(root.resolve()):
            errors.append('unsafe path: '+rel)
        elif not path.is_file():
            errors.append('missing: '+rel)
        else:
            actual = digest(path)
            if actual == expected:
                counts[count] += 1
            elif portable and git_expected and actual == git_expected:
                counts[count] += 1
                counts['git_blob_variants'] += 1
            else:
                errors.append('SHA256 mismatch: '+rel)

    manifest = bundle/'SHA256SUMS'
    listed = set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        expected, rel = line.split('  ', 1)
        if rel in listed or not (bundle/rel).resolve().is_relative_to(bundle.resolve()):
            errors.append('unsafe/duplicate manifest path: '+rel)
            continue
        listed.add(rel)
        checked((bundle/rel).relative_to(root).as_posix(), expected, 'bundle')
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p != manifest}
    if actual != listed:
        errors.append('bundle manifest membership mismatch')
    inp = json.loads((bundle/'input_provenance.json').read_text(encoding='utf-8'))
    for rel, expected in inp['protected_inputs_sha256'].items():
        if portable and rel.startswith('code/outputs/'):
            counts['local_skipped'] += 1
            continue
        checked(rel, expected, 'protected_inputs', inp['protected_inputs_git_blob_sha256'].get(rel))
    bindings = json.loads((bundle/'output_bindings.json').read_text(encoding='utf-8'))
    for rel, expected in bindings['sha256'].items():
        checked(rel, expected, 'output_bindings', bindings.get('git_blob_sha256', {}).get(rel))
    registry = json.loads((root/'docs/PROJECT_REGISTRY.json').read_text(encoding='utf-8-sig'))
    for key, expected in bindings['unchanged_registry_current'].items():
        if registry['current'].get(key) != expected:
            errors.append('scientific state changed: '+key)
    if not portable:
        old = root/'code/outputs/analysis/task20_20261101/stage_i_engineering_fixture'
        for line in (old/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            if line:
                expected, rel = line.split('  ', 1)
                target = (old/rel).resolve()
                if not target.is_relative_to(old.resolve()):
                    errors.append('unsafe Task20 manifest path')
                    continue
                checked(target.relative_to(root).as_posix(), expected, 'protected_inputs')
    # Refuse to import a changed implementation before executing recomputation.
    if errors:
        return dict(status='FAIL', portable=portable, counts=counts, errors=errors)
    sys.path.insert(0, str(root/'code/src'))
    sys.path.insert(0, str(root/'code/scripts'))
    from riskprop.controller_evidence import EvidenceError, EvidenceJournal, schema_description
    from p3_controller_evidence_fixtures import invalid_fixtures, journal_from_records, scenario_records

    if schema_description() != json.loads((bundle/'schema.json').read_text(encoding='utf-8')):
        errors.append('schema inventory mismatch')
    expected = json.loads((bundle/'linkage_results.json').read_text(encoding='utf-8'))
    for name in ('A', 'B', 'C', 'D', 'E', 'G', 'H'):
        payload = json.loads((bundle/('fixture_'+name+'.json')).read_text(encoding='utf-8'))
        journal = EvidenceJournal.from_dict(payload)
        computed = journal.validate()
        audit = {k:v for k,v in computed.items() if k != 'timeline'}
        if audit != expected['scenarios'][name]:
            errors.append('linkage result mismatch: '+name)
        if journal.records != scenario_records(name):
            errors.append('deterministic reconstruction mismatch: '+name)
        if not audit['fixture_only'] or audit['scientific_claim_eligible']:
            errors.append('fixture grade mismatch: '+name)
        counts['scenarios'] += 1
    for name, (records, code) in invalid_fixtures().items():
        try:
            journal_from_records(records).validate()
        except EvidenceError as exc:
            actual = exc.code
        else:
            actual = 'NO_ERROR'
        if actual != code or expected['F'][name] != dict(expected=code, actual=actual, status='PASS'):
            errors.append('negative result mismatch: '+name)
        counts['invalid_cases'] += 1
    return dict(status='PASS' if not errors else 'FAIL', portable=portable, counts=counts,
                fixture_only=True, scientific_claim_eligible=False, errors=errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--portable', action='store_true')
    args = parser.parse_args()
    result = verify(args.repo_root.resolve(), args.portable)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
