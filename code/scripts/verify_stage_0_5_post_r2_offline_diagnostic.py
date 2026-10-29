"""Independent read-only package verifier; never imports measurement or TraCI."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_bundle(package):
    package = Path(package).resolve()
    manifest = json.loads((package/'manifest.json').read_bytes())
    rows = manifest['files']
    paths = [r['path'] for r in rows]
    assert len(paths) == len(set(paths)), 'duplicate_manifest_path'
    assert 'manifest.json' not in paths and 'SHA256SUMS' not in paths, 'self_reference'
    actual = {p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()
              and p not in [package/'manifest.json', package/'SHA256SUMS']}
    # Historical parent bundle omits nested bundle control files by design.
    # Accept that scope only after independently verifying each nested bundle.
    nested = []
    extra = actual - set(paths)
    for name in sorted(extra):
        p = Path(name)
        if len(p.parts) > 1 and p.name in {'manifest.json', 'SHA256SUMS'}:
            parent = package/p.parent
            if not any(x['package'] == str(parent.resolve()) for x in nested):
                nested.append(verify_bundle(parent))
        else:
            raise AssertionError(('manifest_unlisted_payload', name))
    covered_controls = {str(Path(x['package']).relative_to(package)/n).replace('\\','/')
                        for x in nested for n in ['manifest.json','SHA256SUMS']}
    actual -= covered_controls
    assert set(paths) == actual, ('manifest_coverage', sorted(actual-set(paths)), sorted(set(paths)-actual))
    for row in rows:
        target = (package/row['path']).resolve()
        assert target.is_relative_to(package), 'path_escape'
        assert sha(target) == row['sha256'], ('manifest_hash', row['path'])
        assert target.stat().st_size == row['bytes'], ('manifest_size', row['path'])
    checksums = []
    for line in (package/'SHA256SUMS').read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.strip().lstrip('*')
        assert name != 'SHA256SUMS', 'SHA_self_reference'
        checksums.append(name)
        target = (package/name).resolve()
        assert target.is_relative_to(package), 'SHA_path_escape'
        assert sha(target) == digest, ('SHA_hash', name)
    assert len(checksums) == len(set(checksums)), 'duplicate_SHA_path'
    assert set(checksums) == actual | {'manifest.json'}, 'SHA_coverage'
    return dict(status='PASS', package=str(package), manifest_payloads=len(rows),
                SHA_entries=len(checksums), manifest_sha256=sha(package/'manifest.json'),
                SHA256SUMS_sha256=sha(package/'SHA256SUMS'), self_reference=False,
                nested_control_scope_independently_verified=nested)


def verify_diagnostic(root, package, raw=False):
    data = json.loads((package/'diagnostic.json').read_bytes())
    assert data['native_launches'] == data['traci_connections'] == data['locked_holdout_reads'] == 0
    assert not data['formal_equivalence_accepted'] and not data['formal_code_changed']
    for arm in data['runs'].values():
        s = arm['source']
        assert s['state_rows'] == sum(s['quality_counts'].values())
        assert s['valid_ttc_rows'] == s['risk_rows_0_lt_ttc_lt_2'] + s['near_rows_2_le_ttc_lt_3'] + s['ttc_ge_3_rows']
        assert s['state_rows'] == arm['source_cohort']['state_rows']
        assert s['risk_rows_0_lt_ttc_lt_2'] == arm['source_all_D1']['onset_events'] == 0
        assert sum(x['members'] for x in arm['near_threshold_segments']) == s['near_rows_2_le_ttc_lt_3']
        if raw:
            for item in arm['inputs'].values():
                assert sha(root/item['path']) == item['sha256'], item['path']
    for name, digest in data['source_sha256'].items():
        assert sha(root/name) == digest, ('source_hash_drift', name)
    return dict(status='PASS', raw_inputs_rehashed=raw, arms=len(data['runs']),
                scientific_equivalence_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--raw-inputs', action='store_true')
    args = parser.parse_args()
    result = verify_bundle(args.package)
    if (args.package/'diagnostic.json').exists():
        result['diagnostic'] = verify_diagnostic(args.repo_root.resolve(), args.package, args.raw_inputs)
    print(json.dumps(result, indent=2))
