"""Read-only exact capsule collection and process/unit observations after launch."""
import base64,json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/continuation-r2/audit_tools'))
from audit_common import Runner,write,sha,display,need
folder=root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution'
need((folder/'launch_invocation.json').is_file(),'actual_launch_record_required')
code="""import base64,hashlib,json,pathlib,subprocess,psutil
b=pathlib.Path('/home/shen/AAD/code/tmp/stage05_v4_20261026_r5/smoke_capsule');files=[]
paths=[b/n for n in ['launch_attempt.json','broker.stdout','broker.stderr','coordinator_failure.json','engineering_acceptance.json'] if (b/n).is_file()]
if (b/'archive').is_dir():paths+=sorted(p for p in (b/'archive').rglob('*') if p.is_file())
total=0
for p in paths:
 assert p.is_relative_to(b) and not p.is_symlink()
 data=p.read_bytes();total+=len(data);assert total<24*1024**2
 files.append({'name':p.relative_to(b).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'data':base64.b64encode(data).decode()})
policy=json.loads((b/'policy.json').read_bytes());runtime=json.loads(pathlib.Path(policy['binding']['runtime_manifest_path']).read_bytes())
hits=[]
for p in psutil.process_iter(['pid','exe','cmdline']):
 try:
  row=p.info;argv=row.get('cmdline') or []
  if row.get('exe')==runtime['sumo_binary'] or policy['binding']['source_files']['stage_0_5_linux_controller_v4.py'] in argv:hits.append(row)
 except (psutil.AccessDenied,psutil.NoSuchProcess):pass
unit='aad-stage05-'+hashlib.sha256((b/'policy.json').read_bytes()).hexdigest()[:24]
r=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property=LoadState','--property=ActiveState','--property=SubState','--property=ControlGroup'],capture_output=True,timeout=10)
print(json.dumps({'files':files,'matching_remaining_processes':hits,'unit':unit,'unit_query_exit_code':r.returncode,'unit_stdout':r.stdout.decode(errors='backslashreplace'),'unit_stderr':r.stderr.decode(errors='backslashreplace')}))
"""
cmd=['wsl.exe','-d','Ubuntu','--cd','/home/shen/AAD','--exec','/home/shen/AAD/code/runtime/stage_0_5_sumo126_v4_r2/env/bin/python3','-I','-B','-c',code]
raw=Runner(folder).run('collection',cmd,cwd=root,timeout=60);record=json.loads(raw)
target=folder/'capsule';target.mkdir(exist_ok=False);manifest={}
for row in record.pop('files'):
    name=row['name'];rel=Path(name);need(not rel.is_absolute() and '..' not in rel.parts,'unsafe_capsule_output')
    path=target/rel;path.parent.mkdir(parents=True,exist_ok=True);write(path,base64.b64decode(row.pop('data'),validate=True))
    need(sha(path)==row['sha256'],'collected_output_drift');manifest[name]=row
write(folder/'capsule_collection.json',dict(files=manifest,cleanup_observation=record))
display(dict(files=len(manifest),bytes=sum(r['bytes'] for r in manifest.values()),cleanup=record))
