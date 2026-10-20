"""Portable independent re-verification of RES-STAGE-0.5-FINAL-CLOSURE-V1.

Reads only the sealed portable evidence directory; no raw data, no capsule.
"""
from __future__ import annotations
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1'


def tool():
    spec = importlib.util.spec_from_file_location('closure_pack', ROOT / 'code/scripts/package_stage_0_5_final_closure.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(path=None, repo_root=None):
    target = Path(path) if path else EVIDENCE
    if not target.is_dir(): raise FileNotFoundError(f'missing portable evidence directory: {target}')
    return tool().verify(target, repo_root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--repo-root', type=Path)
    args = parser.parse_args()
    result = verify(args.evidence, args.repo_root)
    return 0 if result.get('passed') else 1


if __name__ == '__main__':
    sys.exit(main())
