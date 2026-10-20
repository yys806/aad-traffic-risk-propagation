"""Reproduce v1's explicit pre-freeze A+ summary supplement; no raw data reads.

Run after design_stage_0_5_lf_protocol.py prepare and before tests/freeze.
The executed v1 used the same declared SHA-bound step before freezing; this
utility packages that step for future reconstruction, without rerunning v1.
"""
import argparse
import hashlib
import json
from pathlib import Path

def supplement(repo,batch):
    repo=Path(repo).resolve();batch=Path(batch).resolve()
    if (batch/'PLAN_SHA256').exists():raise PermissionError('frozen_capsule')
    p=batch/'source_manifest.json';data=json.loads(p.read_text(encoding='utf-8'))
    folder=repo/'evidence/results/RES-STAGE-0.5-CALIBRATION-GAPS-V1'
    entries={e['path']:e for e in json.loads((folder/'manifest.json').read_text())['files']}
    specifications=[('diagnostics.json','real_Aplus_diagnostics.json'),('unified_strata.json','real_Aplus_strata.json')]
    additions=[]
    for name,alias in specifications:
        target='inputs/'+alias
        if any(e['target']==target for e in data['files']):raise PermissionError('already_supplemented')
        additions.append(dict(source=str(folder/name),target=target,sha256=entries[name]['sha256'],role='calibration_summary',declared_before_read=True))
    previous=hashlib.sha256(p.read_bytes()).hexdigest()
    data['files'].extend(additions)
    data['pre_freeze_revision']=dict(previous_manifest_sha256=previous,reason='Reproduce audited two-window A+ lightweight summary supplement; no raw trajectory/event access')
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for e in additions:
        raw=Path(e['source']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise PermissionError('source_SHA')
        dst=batch/e['target'];dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():raise PermissionError('refuse_existing_target')
        dst.write_bytes(raw)
    return dict(copied=2,real_raw_reads=0,plan_frozen=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
    print(json.dumps(supplement(a.repo_root,a.batch)))
