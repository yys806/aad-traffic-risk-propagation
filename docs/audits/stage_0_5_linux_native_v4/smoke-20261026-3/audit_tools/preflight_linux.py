"""Read-only r5/runtime/kernel/resource checks; no SUMO or capsule launch."""
import ctypes,hashlib,json,os,subprocess,sys
from pathlib import Path
stage=Path('/home/shen/AAD/code/tmp/stage05_v4_20261026_r5');root=Path('/mnt/d/shen/TJU/AAD')
sys.path.insert(0,str(stage))
from stage_0_5_native_capsule_v4 import canonical,sha,require,smoke_inputs,verify_envelope
from stage_0_5_isolation_admission import probe_checks
from stage_0_5_linux_execution_v4 import linux_preflight
expected={'smoke_proposal.json':'a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550','smoke_envelope.json':'6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463','runtime_manifest.json':'3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc','smoke_capsule/policy.json':'1762cb24ac631bf211e418a99eb2289a483d5a8df900d0391d24fc3f6b911507','probe_results/record.json':'c38b6b32d54cf2b3f28852dab84ceef5811b3481418356d035e2f34234ba5513'}
inputs={'network.net.xml':'686042b018591e728bfd31a194d301b18233b9027b47f9bb276c4c641a039d5f','routes.rou.xml':'7ab787025b44a82fa7d4bc7b0f0b958631b094de81ba5f8f82800dee3867ef37','run.sumocfg':'f96cae379fd8557affcdfe6f108e61f3281e0ac87539a7e65c9b5095c9276930'}
out=root/'code/tmp/smoke3_20261026_checks';status='Failed';error=None;result={}
try:
 git=json.loads((out/'git_preflight.json').read_bytes());require(git['status']=='Pass','fresh_Git_checks_required')
 require(not (root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3').exists(),'audit_directory_already_exists')
 for n in ['launch_attempt.json','archive','scratch','engineering_acceptance.json','coordinator_failure.json','broker.stdout','broker.stderr']:
  require(not (stage/'smoke_capsule'/n).exists(),'prior_attempt_or_output:'+n)
 require(all(sha(stage/n)==h for n,h in expected.items()),'exact_authorization_artifact_drift')
 record=json.loads((stage/'staging_record.json').read_bytes());sources=record['source_sha256']
 require(len(sources)==12 and sources==git['controller_source_sha256'],'staging_Git_source_map_mismatch')
 for n,h in sources.items():require(sha(stage/n)==sha(root/'code/scripts'/n)==h,'source_drift:'+n)
 digest=hashlib.sha256(canonical(sources)).hexdigest();require(record['source_closure_sha256']==digest=='b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2','source_closure_drift')
 p=json.loads((stage/'smoke_proposal.json').read_bytes());policy=json.loads((stage/'smoke_capsule/policy.json').read_bytes())
 require(p['task_id']=='AAD-0.5-LINUX-INTEGRATION-V4-SMOKE' and len(p['runs'])==1 and p['runs'][0]['id']=='SMOKE_V4_20261026_3','exact_run_required')
 require(p['runs'][0]['capsule_input_sha256']==inputs and {n:sha(stage/'smoke_inputs'/n) for n in inputs}==inputs,'synthetic_input_drift')
 require(p['controller_source_sha256']==sources,'proposal_source_binding')
 smoke_inputs(p['runs'][0],{n:(stage/'smoke_inputs'/n).read_bytes() for n in inputs})
 probe=json.loads((stage/'probe_results/record.json').read_bytes());checks=probe_checks(probe)
 require(probe['guard_sha256']==sources['stage_0_5_linux_isolation.py'] and all(checks.values()) and checks==probe['checks'],'probe_failure')
 require(probe['kernel']==os.uname().release and probe['os_release']==Path('/etc/os-release').read_text(),'kernel_or_OS_changed')
 require(all(sha(n)==h for n,h in probe['runtime_files_sha256'].items()),'probe_runtime_drift')
 libc=ctypes.CDLL(None,use_errno=True);abi=libc.syscall(444,0,0,1);require(abi>=3,'Landlock_ABI3_required')
 userns=int(Path('/proc/sys/kernel/unprivileged_userns_clone').read_text());maximum=int(Path('/proc/sys/user/max_user_namespaces').read_text());require(userns==1 and maximum>0,'user_namespace_unavailable')
 controllers=Path('/sys/fs/cgroup/cgroup.controllers').read_text().split();require({'cpu','memory','pids'}<=set(controllers),'cgroup_v2_controllers_unavailable')
 manager=subprocess.run(['/usr/bin/systemctl','--user','show','--property=Version','--property=ControlGroup'],capture_output=True,timeout=10);require(manager.returncode==0,'user_systemd_manager_unavailable')
 require(all(os.readlink('/proc/self/ns/'+n)==v for n,v in policy['host_namespaces'].items()),'host_namespaces_changed_since_policy')
 try:verify_envelope(policy,stage/'smoke_envelope.json',expected['smoke_envelope.json'])
 except ValueError as exc:require(str(exc)=='engineering_smoke_authorization_missing','unexpected_original_envelope_result')
 else:raise ValueError('original_envelope_authorized')
 live=linux_preflight(p,policy)
 result=dict(artifact_sha256=expected,input_sha256=inputs,source_sha256=sources,source_closure_sha256=digest,current_HEAD=git['current_HEAD'],probe_checks=checks,kernel=probe['kernel'],OS_release=probe['os_release'],landlock_ABI=abi,unprivileged_userns_clone=userns,max_user_namespaces=maximum,cgroup_controllers=controllers,systemd_manager_stdout=manager.stdout.decode(),systemd_manager_stderr=manager.stderr.decode(),live_runtime_and_resources=live,original_envelope_unmodified_and_unauthorized=True,no_prior_attempt=True)
 status='Pass'
except BaseException as exc:error=repr(exc);raise
finally:
 record=dict(status=status,error=error,result=result,SUMO_version_processes=0,SUMO_simulation_processes=0,real_TraCI_connections=0,command=[sys.executable,'-I','-B',__file__],working_directory=os.getcwd())
 with (out/'linux_preflight.json').open('xb') as f:f.write(canonical(record)+b'\n')
 print(json.dumps(record))
