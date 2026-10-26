"""Actual pure-Git checks; no native SUMO."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[3]
out=root/'code/tmp/smoke3_20261026_checks';out.mkdir(exist_ok=False)
clone=root/'code/tmp/v4_smoke3_prelaunch_git_20261026_r1'
assert not (root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3').exists()
assert (clone/'.git').is_dir() and not (clone/'dataset').exists() and not (clone/'code/outputs/formal').exists()
commands=[]
def run(name,argv,cwd):
 start=time.monotonic();r=subprocess.run(argv,cwd=cwd,capture_output=True,timeout=120)
 for ext,data in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (out/(name+'.'+ext)).open('xb') as f:f.write(data)
 commands.append(dict(name=name,argv=argv,cwd=str(cwd),exit_code=r.returncode,elapsed_s=time.monotonic()-start,stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest()))
 assert r.returncode==0,(name,r.stderr[-2000:])
 return r.stdout
status='Failed';error=None;controller={};head=None
try:
 head=run('current_head',['git','rev-parse','HEAD'],root).decode().strip()
 assert run('current_clean',['git','status','--porcelain'],root)==b''
 assert run('clone_head',['git','rev-parse','HEAD'],clone).decode().strip()==head
 assert run('clone_clean',['git','status','--porcelain'],clone)==b''
 proposal=json.loads((clone/'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v5/proposal.json').read_bytes())
 for n,h in proposal['source_sha256'].items():
  assert hashlib.sha256((clone/n).read_bytes()).hexdigest()==hashlib.sha256((root/n).read_bytes()).hexdigest()==h
 for n,h in proposal['controller_source_sha256'].items():
  data=run('git_source_'+n,['git','show','HEAD:code/scripts/'+n],root)
  assert hashlib.sha256(data).hexdigest()==h;controller[n]=h
 run('pure_git_docs',[sys.executable,'-B','code/scripts/validate_project_docs.py','--strict-git','--require-clean'],clone)
 run('pure_git_evidence',[sys.executable,'-B','code/scripts/export_project_evidence.py','--repo-root','.','--verify'],clone)
 tests=run('pure_git_tests',[sys.executable,'-B','-m','pytest','tests/test_stage_0_5_native_capsule_v4.py','tests/test_project_docs.py','-q','-p','no:cacheprovider','--basetemp=tmp/smoke3_prelaunch_pure_git'],clone/'code')
 assert b'135 passed' in tests
 run('current_docs',[sys.executable,'-B','code/scripts/validate_project_docs.py','--strict-git','--require-clean'],root)
 status='Pass'
except BaseException as exc:error=repr(exc);raise
finally:
 record=dict(status=status,error=error,current_HEAD=head,original_authorized_commit='6a8864372560712e4f127f93219edad073da0d9f',clone=str(clone),commands=commands,controller_source_sha256=controller,bound_sources_verified=38,pure_Git_V4_and_docs_passed=135 if status=='Pass' else None,SUMO_version_processes=0,SUMO_simulation_processes=0,real_TraCI_connections=0)
 with (out/'git_preflight.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
 print(json.dumps(dict(status=status,error=error,current_HEAD=head,commands=len(commands))))
