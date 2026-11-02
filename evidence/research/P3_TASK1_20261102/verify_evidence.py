"""Read-only byte checks for the P3 Task1 documentation audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path, portable: bool) -> dict:
    bundle = root / 'evidence/research/P3_TASK1_20261102'
    errors = []
    counts = {'bundle': 0, 'protected_inputs': 0, 'output_bindings': 0, 'local_skipped': 0}
    counts['git_blob_byte_variants'] = 0

    def bound(path: Path, expected: str, label: str, count: str):
        if not path.is_file():
            errors.append('missing: ' + label)
        elif digest(path) != expected:
            errors.append('SHA mismatch: ' + label)
        else:
            counts[count] += 1

    for line in (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        if not line:
            continue
        expected, rel = line.split('  ', 1)
        path = (bundle / rel).resolve()
        if not path.is_relative_to(bundle.resolve()):
            errors.append('unsafe bundle path: ' + rel)
            continue
        bound(path, expected, rel, 'bundle')
    inputs = json.loads((bundle / 'input_provenance.json').read_text(encoding='utf-8'))
    for rel, expected in inputs['protected_inputs_sha256'].items():
        if portable and rel.startswith('code/outputs/'):
            counts['local_skipped'] += 1
            continue
        path = root / rel
        git_expected = inputs.get('protected_inputs_git_blob_sha256', {}).get(rel)
        if portable and path.is_file() and digest(path) != expected and digest(path) == git_expected:
            counts['protected_inputs'] += 1
            counts['git_blob_byte_variants'] += 1
            continue
        bound(root / rel, expected, rel, 'protected_inputs')
    outputs = json.loads((bundle / 'output_bindings.json').read_text(encoding='utf-8'))
    for rel, expected in outputs['sha256'].items():
        bound(root / rel, expected, rel, 'output_bindings')
    if not portable:
        planning = json.loads((bundle / 'planning_revision.json').read_text(encoding='utf-8'))
        path = Path(planning['external_path'])
        bound(path, planning['new_sha256'], 'authorized OB roadmap', 'output_bindings')
        fixture = root / 'code/outputs/analysis/task20_20261101/stage_i_engineering_fixture'
        for line in (fixture / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            if line:
                expected, rel = line.split('  ', 1)
                bound(fixture / rel, expected, 'Task20 ' + rel, 'protected_inputs')
    registry = json.loads((root / 'docs/PROJECT_REGISTRY.json').read_text(encoding='utf-8-sig'))
    frozen = outputs['unchanged_registry_current']
    for key, value in frozen.items():
        if registry['current'].get(key) != value:
            errors.append('formal status changed: ' + key)
    return {'status': 'PASS' if not errors else 'FAIL', 'portable': portable, 'counts': counts, 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--portable', action='store_true')
    args = parser.parse_args()
    result = verify(args.repo_root.resolve(), args.portable)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
