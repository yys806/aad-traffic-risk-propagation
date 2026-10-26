"""Real harmless capability checks and the bound production static preflight."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_common import Runner,write,display,need,sha,canonical,optional_text,launch_artifacts,unit_is_absent,native_processes,namespaces_separated,BindingFailure,RequiredCheckFailure

STAGE=Path('/home/shen/AAD/code/tmp/stage05_v4_20261026_r5')
EXPECTED={'smoke_proposal.json':'a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550',
 'smoke_envelope.json':'6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463',
 'runtime_manifest.json':'3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc',
 'smoke_capsule/policy.json':'1762cb24ac631bf211e418a99eb2289a483d5a8df900d0391d24fc3f6b911507',
 'probe_results/record.json':'c38b6b32d54cf2b3f28852dab84ceef5811b3481418356d035e2f34234ba5513'}
INPUTS={'network.net.xml':'686042b018591e728bfd31a194d301b18233b9027b47f9bb276c4c641a039d5f','routes.rou.xml':'7ab787025b44a82fa7d4bc7b0f0b958631b094de81ba5f8f82800dee3867ef37','run.sumocfg':'f96cae379fd8557affcdfe6f108e61f3281e0ac87539a7e65c9b5095c9276930'}

def check(root,out,stage=STAGE):
    root=Path(root);out=Path(out);stage=Path(stage)
    need(stage==STAGE,'fixed_r5_required',BindingFailure)
    need(out.is_dir() and not (out/'linux_preflight.json').exists(),'new_explicit_check_output_required')
    run=Runner(out);record=dict(status='HELPER_ERROR',commands=run.commands,checks={})
    try:
        sys.path.insert(0,str(stage))
        from stage_0_5_isolation_admission import probe_checks
        from stage_0_5_linux_execution_v4 import linux_preflight
        from stage_0_5_native_capsule_v4 import smoke_inputs,verify_envelope
        git=json.loads((out/'git_preflight.json').read_bytes());need(git['status']=='Pass','fresh_Git_checks_required')
        need(not launch_artifacts(stage),'prior_native_attempt_or_outputs')
        for n,h in EXPECTED.items():need(sha(stage/n)==h,'binding_drift:'+n,BindingFailure)
        staging=json.loads((stage/'staging_record.json').read_bytes());sources=staging['source_sha256']
        need(len(sources)==12 and sources==git['controller_source_sha256'],'source_map_mismatch',BindingFailure)
        for n,h in sources.items():need(sha(stage/n)==sha(root/'code/scripts'/n)==h,'source_drift:'+n,BindingFailure)
        digest=hashlib.sha256(canonical(sources)).hexdigest()
        need(staging['source_closure_sha256']==digest=='b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2','closure_drift',BindingFailure)
        p=json.loads((stage/'smoke_proposal.json').read_bytes());policy=json.loads((stage/'smoke_capsule/policy.json').read_bytes())
        need(p['runs'][0]['id']=='SMOKE_V4_20261026_3' and p['runs'][0]['capsule_input_sha256']==INPUTS,'run_or_input_binding',BindingFailure)
        need({n:sha(stage/'smoke_inputs'/n) for n in INPUTS}==INPUTS,'input_drift',BindingFailure)
        smoke_inputs(p['runs'][0],{n:(stage/'smoke_inputs'/n).read_bytes() for n in INPUTS})
        probe=json.loads((stage/'probe_results/record.json').read_bytes());historical=probe_checks(probe)
        need(probe['guard_sha256']==sources['stage_0_5_linux_isolation.py'] and all(historical.values()) and historical==probe['checks'],'fixed_probe_invalid',BindingFailure)
        need(probe['kernel']==os.uname().release and probe['os_release']==Path('/etc/os-release').read_text(),'kernel_or_OS_identity_changed',BindingFailure)
        need(all(sha(n)==h for n,h in probe['runtime_files_sha256'].items()),'probe_dependency_drift',BindingFailure)
        record['checks']['exact_bindings']=dict(artifacts=EXPECTED,inputs=INPUTS,sources=sources,closure_sha256=digest,kernel=probe['kernel'],historical_probe_checks=historical)
        runtime=p['runtime'];import psutil
        rows=[];skipped=0
        for proc in psutil.process_iter(['pid','exe','cmdline','create_time']):
            try:rows.append(proc.info)
            except (psutil.NoSuchProcess,psutil.AccessDenied):skipped+=1
        hits=native_processes(runtime,policy,rows);need(not hits,'leftover_production_processes')
        unit='aad-stage05-'+EXPECTED['smoke_capsule/policy.json'][:24]
        raw=run.run('production_unit',['/usr/bin/systemctl','--user','show',unit,'--property=LoadState','--property=ActiveState','--property=SubState','--property=ControlGroup'],ok=(0,1))
        values=dict(line.split('=',1) for line in raw.decode('utf-8').splitlines() if '=' in line)
        need(unit_is_absent(values),'existing_production_systemd_unit')
        record['checks']['no_prior_launch']=dict(unit=unit,unit_properties=values,matching_processes=hits,processes_skipped=skipped)
        run.run('systemd_manager',['/usr/bin/systemctl','--user','show','--property=Version','--property=ControlGroup'],timeout=10)
        optional={n:optional_text(n) for n in ['/proc/sys/kernel/unprivileged_userns_clone','/proc/sys/user/max_user_namespaces']}
        current_ns={n:os.readlink('/proc/self/ns/'+n) for n in policy['host_namespaces']}
        code="import json,os;print(json.dumps({'uid':os.getuid(),'namespaces':{n:os.readlink('/proc/self/ns/'+n) for n in ['user','mnt','pid','net','ipc']}}))"
        user=json.loads(run.run('live_user_namespace',['/usr/bin/unshare','--user','--map-root-user','--mount','--pid','--fork','--net','--ipc','--uts','--mount-proc','--','/usr/bin/python3','-I','-B','-c',code],timeout=5))
        need(user['uid']==0 and namespaces_separated(user['namespaces'],current_ns,policy['host_namespaces']),'actual_namespace_isolation_failed')
        record['checks']['live_user_namespace']=dict(result=user,current_outer_namespaces=current_ns,policy_recorded_host_namespaces=policy['host_namespaces'],optional_sysctls=optional)
        abi=ctypes.CDLL(None,use_errno=True).syscall(444,0,0,1);need(abi>=3,'Landlock_ABI3_required')
        guard=stage/'stage_0_5_linux_isolation.py'
        code="""import json,runpy,sys,socket
from pathlib import Path
g=runpy.run_path(sys.argv[1]);p={'readonly_paths':[sys.argv[2]],'executables':[],'scratch':sys.argv[2],'kernel_readonly':['/proc']}
g['landlock'](p);g['seccomp']();denied={}
for name,call in [('outside_read',lambda:Path(sys.argv[3]).read_bytes()),('unix_socket',lambda:socket.socket(socket.AF_UNIX))]:
 try:call();denied[name]=False
 except PermissionError:denied[name]=True
status=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
print(json.dumps({'denied':denied,'NoNewPrivs':status['NoNewPrivs'].strip(),'Seccomp':status['Seccomp'].strip()}))
"""
        security=json.loads(run.run('live_landlock_seccomp',['/usr/bin/python3','-I','-B','-c',code,str(guard),str(out),str(stage/'smoke_proposal.json')],timeout=5))
        need(security==dict(denied=dict(outside_read=True,unix_socket=True),NoNewPrivs='1',Seccomp='2'),'live_security_enforcement_failed')
        record['checks']['live_landlock_seccomp']=dict(landlock_ABI=abi,result=security)
        controllers=Path('/sys/fs/cgroup/cgroup.controllers').read_text().split();need({'cpu','memory','pids'}<=set(controllers),'cgroup_v2_controllers_missing')
        test_unit='aad-smoke3-precheck-'+hashlib.sha256(str(out).encode()).hexdigest()[:12]
        code="""import json
from pathlib import Path
p=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split(':',2)[2].lstrip('/')
print(json.dumps({n:(p/n).read_text().strip() for n in ['memory.max','memory.swap.max','pids.max','cpu.max']}))
"""
        cg=json.loads(run.run('live_systemd_cgroup',['/usr/bin/systemd-run','--user','--wait','--pipe','--collect','--quiet','--unit='+test_unit,'-p','MemoryMax=67108864','-p','MemorySwapMax=0','-p','TasksMax=8','-p','CPUQuota=100%','-p','RuntimeMaxSec=5','-p','KillMode=control-group','/usr/bin/python3','-I','-B','-c',code],timeout=10))
        need(cg=={'memory.max':'67108864','memory.swap.max':'0','pids.max':'8','cpu.max':'100000 100000'},'live_cgroup_readback_failed')
        record['checks']['live_systemd_cgroup']=dict(unit=test_unit,controllers=controllers,readback=cg)
        try:verify_envelope(policy,stage/'smoke_envelope.json',EXPECTED['smoke_envelope.json'])
        except ValueError as e:need(str(e)=='engineering_smoke_authorization_missing','original_envelope_state_changed',BindingFailure)
        else:raise BindingFailure('original_envelope_authorized')
        # Existing production entry verifies all runtime files, readonly policy,
        # executables and current C/D/WSL/archive/memory floors without SUMO.
        raw=run.run('bound_production_preflight',[runtime['python_executable'],'-I','-B',str(stage/'stage_0_5_linux_execution_v4.py'),'preflight',str(stage/'smoke_proposal.json')],timeout=120)
        live=json.loads(raw);need(live['proposal_sha256']==EXPECTED['smoke_proposal.json'],'proposal_copy_drift',BindingFailure)
        record['checks']['bound_production_runtime_and_resources']=live
        need(not launch_artifacts(stage),'native_attempt_appeared')
        record.update(status='Pass',current_HEAD=git['current_HEAD'],original_envelope_unchanged=True,SUMO_version_processes=0,SUMO_simulation_processes=0,real_TraCI_connections=0)
    except (BindingFailure,RequiredCheckFailure) as e:record.update(status='PRELAUNCH BLOCKED',error=repr(e));raise
    except BaseException as e:record.update(status='HELPER_ERROR',error=repr(e));raise
    finally:write(out/'linux_preflight.json',record);display(dict(status=record['status'],error=record.get('error'),commands=len(run.commands),output=str(out)))
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();check(a.repo_root,a.output_dir)
