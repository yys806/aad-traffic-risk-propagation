"""Seal this task's audit files; no old candidate, result or ledger is written."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parents[1]
AUD=OUT.relative_to(ROOT).as_posix()
REPORT='docs/STAGE_0_5_B00_SCIENTIFIC_ADMISSION_REVIEW_V1_2026-10-27.md'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,sort_keys=True);stream.write('\n')


def main():
    commands=[]
    for path in sorted((OUT/'validation').glob('*/record.json')):
        item=json.loads(path.read_bytes())
        assert sha(path.parent/'stdout.log')==item['stdout_sha256']
        assert sha(path.parent/'stderr.log')==item['stderr_sha256']
        item.update(record_path=path.relative_to(ROOT).as_posix(),
            stdout_path=(path.parent/'stdout.log').relative_to(ROOT).as_posix(),
            stderr_path=(path.parent/'stderr.log').relative_to(ROOT).as_posix())
        commands.append(item)
    write('validation_record.json',dict(schema='aad.scientific-review-validation.v1',
        baseline_commit='753b666a3c9e4b8d88add2ead1973ff8e2d4439f',
        sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        commands=commands,failures_retained=[c['record_path'] for c in commands if c['exit_code']!=0],
        final_satisfied_checks=['candidate-verification','static-facts-r2','pure-guard-counterexamples',
            'remote-main-r2','review-consistency','strict-docs','portable-evidence','docs-pytest-r3',
            'supplemental-input-syntax','static-preflight-only','state-readers','review-consistency-r2','final-audit-syntax'],
        skipped=[dict(check='Full production pytest / native tests',reason='No production changes; audit-only task prohibits native simulation'),
            dict(check='New live Linux inspection',reason='This is a static evidence review; current live environment explicitly unverified'),
            dict(check='Generic evidence exporter write mode',reason='No new research result; preserve historical bytes and known independent extension registrations. Verify mode passed.')],
        assertions=dict(SUMO_launches=0,netconvert_launches=0,real_TraCI_connections=0,new_B00_research_trajectories=0,
            research_approvals_changed=False,native_locks_changed=False,production_code_changed=False),
        postcommit_validation='Recorded separately under code/tmp/scientific_review_v1_delivery_20261027 to avoid commit/hash self-reference'))
    paths=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['audit_manifest.json','SHA256SUMS']]
    paths += [ROOT/REPORT]+[ROOT/'AI_CONTEXT'/n for n in ['00_PROJECT_STATE.md','05_EXPERIMENTS.md','07_KNOWN_ISSUES.md','08_CHANGELOG.md']]
    mapping={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    write('audit_manifest.json',dict(schema='aad.scientific-review-audit-manifest.v1',files=mapping,
        exclusions=['This manifest and SHA256SUMS (no hash cycles)','Ignored pycache','Postcommit delivery receipt outside tracked tree'],
        status='REVIEW_COMPLETE_RESEARCH_APPROVAL_PENDING'))
    sums=dict(mapping);sums[AUD+'/audit_manifest.json']=sha(OUT/'audit_manifest.json')
    with (OUT/'SHA256SUMS').open('x',encoding='utf-8',newline='\n') as stream:
        stream.writelines(f'{h}  {n}\n' for n,h in sorted(sums.items()))
    print(json.dumps(dict(status='Sealed',files=len(mapping),commands=len(commands),
        failures_retained=sum(c['exit_code']!=0 for c in commands),
        audit_manifest_sha256=sha(OUT/'audit_manifest.json'),SHA256SUMS_sha256=sha(OUT/'SHA256SUMS'),
        report_sha256=sha(ROOT/REPORT))))


if __name__=='__main__': main()
