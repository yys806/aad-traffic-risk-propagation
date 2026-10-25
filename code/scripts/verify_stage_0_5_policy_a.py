"""Verify proposal bindings. No simulator launch or protocol freeze."""
import argparse
import hashlib
import json
from pathlib import Path
from supervise_stage_0_5_diagnostic import verify_dependencies

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def verify(portable, local_root=None):
    for line in (portable/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        if sha(portable/name)!=digest:raise ValueError('portable_hash:'+name)
    proposal=json.loads((portable/'review_ready_plan.json').read_text())
    if sha(portable/'review_ready_plan.json')!=(portable/'REVIEW_PROPOSAL_SHA256').read_text().strip():raise ValueError('proposal_hash')
    assert proposal['execution_allowed'] is False and proposal['protocol_frozen'] is False and proposal['attempts']==0
    for name,digest in proposal['source_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('source_hash:'+name)
    if local_root is not None:
        verify_dependencies(proposal['dependency_versions'])
        for name,digest in proposal['input_sha256'].items():
            if sha(ROOT/name)!=digest:raise ValueError('input_hash:'+name)
        for name,digest in proposal['external_file_sha256'].items():
            if sha(name)!=digest:raise ValueError('external_hash:'+name)
        for run in proposal['runs']:
            for name,digest in run['prepared_input_sha256'].items():
                if sha(local_root/'prepared_inputs'/run['id']/name)!=digest:raise ValueError('prepared_hash:'+name)
    return {'portable_and_source_bindings':'verified','local_inputs':'verified' if local_root else 'not_checked_raw_inputs_not_required_for_portable_check','SUMO_started':False,'plan_frozen':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--portable',type=Path,required=True);p.add_argument('--local-root',type=Path)
    a=p.parse_args();print(json.dumps(verify(a.portable,a.local_root)))
