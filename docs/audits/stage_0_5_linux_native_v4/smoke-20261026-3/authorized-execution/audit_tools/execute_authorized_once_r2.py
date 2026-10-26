"""One exact authorized launch only; collection is a separate read-only step."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone

root=Path(__file__).resolve().parents[3]
tools=root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/continuation-r2/audit_tools'
sys.path.insert(0,str(tools))
from audit_common import write,sha,Runner,need,display
checks=root/'code/tmp/smoke3_20261026_checks_r3'
git=json.loads((checks/'git_preflight.json').read_bytes());linux=json.loads((checks/'linux_preflight.json').read_bytes())
need(git['status']==linux['status']=='Pass','completed_live_preflight_required')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
need(head==git['current_HEAD'] and subprocess.check_output(['git','status','--porcelain'],cwd=root)==b'','prelaunch_Git_changed')
folder=root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution'
need(not folder.exists(),'exclusive_execution_directory_already_exists')
original=root/'docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5/smoke_envelope.json'
need(sha(original)=='6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463','original_envelope_drift')
envelope=json.loads(original.read_bytes());proposal=envelope['proposal_sha256']
need(proposal=='a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550' and envelope['run_id']=='SMOKE_V4_20261026_3','exact_authorization_required')
envelope['approval']=dict(task_id='AAD-0.5-LINUX-INTEGRATION-V4-SMOKE',run_id=envelope['run_id'],proposal_sha256=proposal,
 engineering_authorized=True,decision_record='Researcher explicitly authorized this exact single synthetic engineering smoke on 2026-10-26 and explicitly continued that same unconsumed authorization after auxiliary precheck repairs; proposal SHA-256 '+proposal+'. One actual launch only; no automatic retry; no B00 or research trajectory.')
folder.mkdir(exist_ok=False);path=folder/'authorized_envelope.json';write(path,envelope);digest=sha(path)
write(folder/'authorized_envelope_sha256.json',dict(sha256=digest,path=str(path),original_envelope_sha256=sha(original),original_envelope_unchanged=True))
linux_path='/mnt/d/shen/TJU/AAD/'+path.relative_to(root).as_posix()
runtime='/home/shen/AAD/code/runtime/stage_0_5_sumo126_v4_r2/env/bin/python3'
driver='/home/shen/AAD/code/tmp/stage05_v4_20261026_r5/stage_0_5_linux_execution_v4.py'
argv=['wsl.exe','-d','Ubuntu','--cd','/home/shen/AAD','--exec',runtime,'-I','-B',driver,'launch',linux_path,digest]
need(sha(path)==digest,'new_authorized_envelope_drift')
write(folder/'launch_invocation.json',dict(launch_call=1,argv=argv,commit=head,authorized_envelope_sha256=digest,
 preflight_git_sha256=sha(checks/'git_preflight.json'),preflight_linux_sha256=sha(checks/'linux_preflight.json'),
 time_UTC=datetime.now(timezone.utc).isoformat(),maximum_attempts=1,automatic_retry=False,coordinator_timeout_s=60))
runner=Runner(folder)
try:runner.run('launch',argv,cwd=root,timeout=60)
except Exception as e:
 write(folder/'outer_failure.json',dict(error=repr(e),automatic_retry=False,launch_calls=1))
 # Exact unit only; never signals unrelated WSL processes.
 unit='aad-stage05-1762cb24ac631bf211e418a9'
 cleanup=['wsl.exe','-d','Ubuntu','--cd','/home/shen/AAD','--exec','/usr/bin/systemctl','--user','stop',unit]
 try:runner.run('outer_cleanup',cleanup,cwd=root,timeout=15,ok=(0,1,5))
 except Exception as cleanup_error:write(folder/'outer_cleanup_error.json',dict(error=repr(cleanup_error)))
display(dict(execution_directory=str(folder),authorized_envelope_sha256=digest,launch_calls=1,
 launch_exit_code=json.loads((folder/'launch.json').read_bytes())['exit_code'],automatic_retry=False))
