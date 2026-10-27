from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys
root=Path(__file__).resolve().parents[3];work=Path(__file__).resolve().parent
out=work/'postcommit';out.mkdir(exist_ok=False)
clone=work/'final_git_clone';assert not clone.exists()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
records={}
def run(name,argv,cwd=root,timeout=600):
    result=subprocess.run(argv,cwd=cwd,capture_output=True,timeout=timeout)
    for suffix,data in [('stdout',result.stdout),('stderr',result.stderr)]:
        (out/(name+'.'+suffix)).open('xb').write(data)
    row=dict(argv=argv,cwd=str(cwd),commit=head,exit_code=result.returncode,stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
    records[name]=row
    (out/(name+'.command.json')).open('xb').write(json.dumps(row,sort_keys=True).encode()+bytes([10]))
    print(name,result.returncode,flush=True)
    if result.returncode:
        print(result.stdout[-2500:].decode(errors='backslashreplace').encode('ascii',errors='backslashreplace').decode(),flush=True)
        print(result.stderr[-2500:].decode(errors='backslashreplace').encode('ascii',errors='backslashreplace').decode(),flush=True)
        raise RuntimeError('postcommit_failed:'+name)
    return result
assert not run('main_clean',['git','status','--porcelain']).stdout.strip()
run('clone',['git','clone','--no-hardlinks','--no-local',str(root),str(clone)],timeout=600)
assert run('clone_HEAD',['git','rev-parse','HEAD'],clone).stdout.decode().strip()==head
assert not run('initial_clone_clean',['git','status','--porcelain'],clone).stdout.strip()
assert not (clone/'dataset').exists() and not (clone/'code/outputs/formal').exists()
run('candidate_verify',[sys.executable,'code/scripts/prepare_stage_0_5_b00_admission_v6.py','verify'],clone)
check="from pathlib import Path;import sys,json;root=Path.cwd();sys.path.insert(0,str(root/'code/scripts'));from stage_0_5_linux_execution_v4 import technical_preflight_v4;r=technical_preflight_v4(root,root/'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/proposal.json','V3_0750_B00_DS38_s20261201',inspect_runtime=True);print(json.dumps(r));assert r['ready'] and not r['technical_errors'] and r['status']=='READY_FOR_RESEARCHER_APPROVAL'"
run('fresh_live_technical_preflight',[sys.executable,'-B','-c',check],clone)
run('auxiliary_tests',[sys.executable,'-m','pytest','tests/test_stage_0_5_b00_admission_v6.py','-q','-p','no:cacheprovider','--basetemp='+str(clone/'code/tmp/postcommit_aux_tmp')],clone/'code')
run('production_targeted_tests',[sys.executable,'code/scripts/validate_stage_0_5_linux_v4.py','--source-workspace',str(root)],clone)
run('compileall',[sys.executable,'-m','compileall','-q','code/src','code/scripts','code/tests'],clone)
run('portable_evidence_verify',[sys.executable,'code/scripts/export_project_evidence.py','--repo-root','.','--verify'],clone)
checksum_code="from pathlib import Path;import hashlib,json;root=Path.cwd();d=root/'docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6';m=json.loads((d/'audit_manifest.json').read_bytes());n=0;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();\nfor p,v in m['files'].items():\n assert h(root/p)==v,p\n n+=1\nfor l in (d/'SHA256SUMS').read_text().splitlines():\n v,p=l.split('  ',1)\n assert h(d/p)==v,p\nprint(json.dumps({'files_verified':n,'commit_scope':'fresh Git checkout'}))"
run('audit_hashes',[sys.executable,'-B','-c',checksum_code],clone)
run('strict_docs_clean',[sys.executable,'code/scripts/validate_project_docs.py','--strict-git','--require-clean'],clone)
assert not run('final_clone_clean',['git','status','--porcelain'],clone).stdout.strip()
assert not run('final_main_clean',['git','status','--porcelain']).stdout.strip()
report=dict(status='Pass',commit=head,clone=str(clone),commands=records,scope='Actual postcommit fresh no-data Git checkout; live preflight only; no launch or research execution',SUMO_launches=0,real_TraCI_connections=0,new_B00_research_trajectories=0,verified_at=datetime.now(timezone.utc).isoformat())
(out/'verification_receipt.json').open('xb').write(json.dumps(report,ensure_ascii=False,sort_keys=True).encode('utf-8')+bytes([10]))
print(json.dumps(dict(status='Pass',commit=head,receipt=str(out/'verification_receipt.json'),receipt_sha256=hashlib.sha256((out/'verification_receipt.json').read_bytes()).hexdigest())),flush=True)
