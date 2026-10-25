"""Portable/source stop-evidence verification; optional exact local artifacts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()

def verify(portable, local=None):
    for line in (portable / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if sha(portable / name) != digest: raise ValueError('portable_digest:' + name)
    provenance = json.loads((portable / 'provenance.json').read_text(encoding='utf-8'))
    for name, digest in provenance['source_sha256'].items():
        if sha(ROOT / name) != digest: raise ValueError('source_digest:' + name)
    approval = json.loads((portable / 'execution_freeze.json').read_text(encoding='utf-8'))
    plan = ROOT / 'docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md'
    proposal = ROOT / 'evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/review_ready_plan.json'
    assert sha(plan) == approval['plan_sha256'] and sha(proposal) == approval['proposal_sha256']
    ledger = json.loads((portable / 'execution_ledger.json').read_text())
    assert len(ledger['attempts']) == 1 and ledger['attempts'][0]['status'] == 'failed_stop'
    review = json.loads((portable / 'failure_review.json').read_text(encoding='utf-8'))
    assert review['full_window_P2_rate'] is None and review['common_cells'] < 18
    assert review['not_attempted'] == ['ID2_SUPPLY_0805', 'ID3_RAMP_0750']
    if local:
        for name, item in json.loads((portable / 'raw_artifact_sha256.json').read_text()).items():
            if sha(local / name) != item['sha256']: raise ValueError('local_digest:' + name)
    return {'portable_and_source':'verified', 'local_artifacts':'verified' if local else 'not_checked',
            'attempts':1,'result':'failed_stop; not three-run completion','Gate_changed':False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--portable',type=Path,required=True)
    parser.add_argument('--local-root',type=Path)
    a = parser.parse_args(); print(json.dumps(verify(a.portable,a.local_root)))
