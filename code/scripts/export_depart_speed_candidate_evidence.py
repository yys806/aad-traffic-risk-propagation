"""Scoped additive export using existing exporter; old bound source stays intact."""
import argparse
import hashlib
from pathlib import Path
import export_project_evidence as exporter
from prepare_stage_0_5_depart_speed_candidate import LOCAL, RESULT, PORTABLE_NAMES


def export(root):
    source = root / LOCAL / 'portable'
    missing = [n for n in PORTABLE_NAMES if n != 'SHA256SUMS' and not (source / n).is_file()]
    if missing: raise FileNotFoundError(str(missing))
    lines = [hashlib.sha256((source / n).read_bytes()).hexdigest() + '  ' + n
             for n in PORTABLE_NAMES if n != 'SHA256SUMS']
    (source / 'SHA256SUMS').write_bytes(('\n'.join(lines) + '\n').encode())
    original = exporter._source_pairs
    try:
        exporter._source_pairs = lambda: {RESULT: [((LOCAL / 'portable' / n).as_posix(), n) for n in PORTABLE_NAMES]}
        return exporter.export_evidence(root, {RESULT})
    finally:
        exporter._source_pairs = original


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    if args.verify:
        issues = exporter.verify_evidence(args.repo_root, {RESULT})
        if issues: raise ValueError(str(issues))
        print('PORTABLE_EVIDENCE_OK (candidate only)')
    else:
        export(args.repo_root); print('CANDIDATE_EVIDENCE_EXPORTED; other entries preserved')
