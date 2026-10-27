"""One-use correction of this review only; preserve prior commit and failure bytes."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parents[1]
BASE='753b666a3c9e4b8d88add2ead1973ff8e2d4439f'
FIRST='92d3bee3bfe0225712b1e91eb9d2cf85d6317872'
GIT='D:/Git/mingw64/bin/git.exe'
OLD='helper未在12源闭包中，不参与native控制；软件验证记录另行绑定helper。'
NEW='helper未在12源闭包或原生软件验证记录中，不参与native控制；工程集成证书verifier路径/SHA和独立工程审计清单另行绑定helper。'

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_bytes())
def write(path,value,mode='x'):
    with path.open(mode,encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
def git(*args): return subprocess.check_output([GIT,'-C',str(ROOT),*args])

def main():
    assert git('rev-parse','HEAD').decode().strip()==FIRST
    assert not (OUT/'delivery_correction.json').exists()
    names=['review_matrix.json','decision_packet.json','evidence_manifest.json',
           'validation_record.json','audit_manifest.json','SHA256SUMS']
    before={n:sha(git('cat-file','blob',FIRST+':'+(OUT/n).relative_to(ROOT).as_posix())) for n in names}
    helper='code/scripts/prepare_stage_0_5_b00_admission_v6.py'
    cert_path='evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/integration_acceptance.json'
    cert=read(ROOT/cert_path)
    expected='2f378e4b69757b0f030d6fc1160364af9e462813052addd7e4520febf79ade3a'
    assert cert['verifier_path']==helper and cert['verifier_sha256']==expected==sha((ROOT/helper).read_bytes())
    old_manifest_path='docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/audit_manifest.json'
    assert read(ROOT/old_manifest_path)['files'][helper]==expected
    proposal=read(ROOT/'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/proposal.json')
    software_path=proposal['software_validation_path']
    assert helper not in (ROOT/software_path).read_text(encoding='utf-8')
    for n in ['review_matrix.json','decision_packet.json']:
        original=json.loads(git('cat-file','blob',FIRST+':'+(OUT/n).relative_to(ROOT).as_posix()))
        value=json.loads(json.dumps(original));issue=next(i for i in value['issues'] if i['issue_id']=='GIT-01')
        for key in ['current_fact','observation']:
            if key not in issue:
                assert n=='decision_packet.json' and key=='observation'
                continue
            assert issue[key].count(OLD)==1
            issue[key]=issue[key].replace(OLD,NEW)
        current=read(OUT/n);assert current in [original,value]
        if current!=value: write(OUT/n,value,'w')
    evidence=read(OUT/'evidence_manifest.json');inventory=read(OUT/'verified_inventory.json')['files']
    provenance=[]
    for n in ['AGENTS.md','PROJECT_CONTEXT.md']:
        assert n not in inventory
        entry=next(e for e in evidence['files'] if e['path']==n)
        blob=git('cat-file','blob',BASE+':'+n);actual=(ROOT/n).read_bytes()
        assert b'\r' not in blob and actual==blob.replace(b'\n',b'\r\n')
        assert sha(actual)==entry['sha256']
        entry['checkout_provenance']=dict(schema='aad.reviewed-document-checkout.v1',
            baseline_commit=BASE,git_blob_oid=git('rev-parse',BASE+':'+n).decode().strip(),
            git_blob_sha256=sha(blob),reviewed_bytes_sha256=sha(actual),
            relation='reviewed_CRLF_equals_baseline_LF_with_CRLF_only',
            scope='Non-scientific Markdown checkout representation only; no change to any scientific binding SHA')
        provenance.append(dict(path=n,**entry['checkout_provenance']))
    evidence['hash_semantics']+=' Two explicitly named non-scientific documents retain reviewed CRLF SHA plus baseline Git blob SHA/OID; pure Git permits only that exact LF/CRLF representation. Scientific bindings remain byte-exact.'
    write(OUT/'evidence_manifest.json',evidence,'w')
    source=ROOT/'code/tmp/scientific_review_v1_delivery_20261027/puregit-review'
    target=OUT/'validation/postcommit-review-initial-failure';target.mkdir(exist_ok=False)
    failure=read(source/'record.json');assert failure['exit_code']==1 and failure['commit']==FIRST
    for n in ['stdout.log','stderr.log','record.json']:
        with (target/n).open('xb') as f: f.write((source/n).read_bytes())
    assert sha((target/'stdout.log').read_bytes())==failure['stdout_sha256']
    assert sha((target/'stderr.log').read_bytes())==failure['stderr_sha256']
    write(OUT/'delivery_correction.json',dict(schema='aad.scientific-review-delivery-correction.v1',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        prior_review_commit=FIRST,baseline_commit=BASE,prior_review_file_sha256=before,
        helper_provenance_correction=dict(previous_claim=OLD,corrected_claim=NEW,
            helper_path=helper,helper_sha256=expected,
            evidence={n:sha((ROOT/n).read_bytes()) for n in [cert_path,old_manifest_path,software_path]}),
        checkout_document_provenance=provenance,
        preserved_failure_directory=target.relative_to(ROOT).as_posix(),
        production_or_scientific_or_historical_binding_changed=False))
    print(json.dumps(dict(status='Corrected review only',documents_with_exact_checkout_provenance=2,prior_failure_retained=True)))

if __name__=='__main__': main()
