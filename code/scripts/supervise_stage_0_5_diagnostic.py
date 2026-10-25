"""Bound execution supervisor API; CLI remains paused pending confirmation.

This module is prepared/tested without launching SUMO. Only a later explicit
researcher-confirmed proposal may be passed to run_authorized_attempt.
"""
from __future__ import annotations
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import psutil


def dependency_version(package):
    """Some installed distributions lack Version metadata; require a real value."""
    try:
        version = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        version = None
    if not version:
        version = getattr(importlib.import_module(package), '__version__', None)
    if not isinstance(version, str) or not version.strip():
        raise ValueError('dependency_version_unavailable:' + package)
    return version


def verify_dependencies(versions):
    for package, expected in versions.items():
        if not expected or dependency_version(package) != expected:
            raise ValueError('dependency_version_changed:' + package)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def authorize(proposal_path, approval):
    digest=sha(proposal_path)
    if approval.get('researcher_confirmed') is not True or approval.get('proposal_sha256')!=digest or not approval.get('decision_record'):
        raise PermissionError('researcher_confirmation_required_for_exact_proposal')
    proposal=json.loads(Path(proposal_path).read_text(encoding='utf-8'))
    if proposal['policy']!='A' or not proposal['all_baseline_cells_observed'] or not proposal['resource_snapshot_pass']:
        raise PermissionError('proposal_preflight_not_eligible')
    return proposal


def reserve_attempt(ledger_path, run_id, proposal_sha):
    path=Path(ledger_path)
    ledger=json.loads(path.read_text()) if path.exists() else {'attempts':[],'proposal_sha256':proposal_sha}
    if ledger['proposal_sha256']!=proposal_sha:raise ValueError('ledger_proposal_mismatch')
    if len(ledger['attempts'])>=3 or any(x['run_id']==run_id for x in ledger['attempts']):
        raise PermissionError('budget_or_retry_forbidden')
    if any(x['status']!='verified' for x in ledger['attempts']):
        raise PermissionError('previous_attempt_not_verified_stop')
    ledger['attempts'].append({'run_id':run_id,'status':'reserved_before_launch','attempt':len(ledger['attempts'])+1})
    path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    return ledger


def resource_reason(elapsed, rss, output_bytes, free_c, free_d):
    if elapsed>600:return 'wall_limit'
    if rss>3*1024**3:return 'process_tree_RSS_limit'
    if output_bytes>2*1024**3:return 'task_output_limit'
    if free_c<5*1024**3 or free_d<14*1024**3:return 'disk_headroom_limit'
    return None


def stop_owned_tree(process):
    try:parent=psutil.Process(process.pid)
    except psutil.NoSuchProcess:return
    children=parent.children(recursive=True)
    for child in reversed(children):
        try:child.terminate()
        except psutil.NoSuchProcess:pass
    try:parent.terminate()
    except psutil.NoSuchProcess:pass
    _,alive=psutil.wait_procs(children+[parent],timeout=5)
    for child in alive:
        try:child.kill()
        except psutil.NoSuchProcess:pass


def run_authorized_attempt(repo, proposal_path, approval, run_id, work, task_root, ledger_path, binary, tools):
    # Permission is checked before any directory write or process launch.
    proposal=authorize(proposal_path,approval)
    verify_dependencies(proposal['dependency_versions'])
    repo,work,task_root=Path(repo).resolve(),Path(work).resolve(),Path(task_root).resolve()
    if not work.is_relative_to(task_root) or work==task_root:raise ValueError('invalid_run_isolation')
    run=next(x for x in proposal['runs'] if x['id']==run_id)
    for relative,expected in proposal['source_sha256'].items():
        if sha(repo/relative)!=expected:raise ValueError('source_binding_changed:'+relative)
    for relative,expected in proposal['input_sha256'].items():
        if sha(repo/relative)!=expected:raise ValueError('baseline_or_reference_changed:'+relative)
    for filename,expected in proposal.get('external_file_sha256',{}).items():
        if sha(filename)!=expected:raise ValueError('external_tool_binding_changed:'+filename)
    if str(Path(tools).resolve())!=proposal.get('traci_tools_root'):
        raise ValueError('unexpected_traci_tools_root')
    for name,expected in run['prepared_input_sha256'].items():
        if sha(work/name)!=expected:raise ValueError('prepared_input_changed:'+name)
    if any((work/name).exists() for name in ['fcd.xml','worker_result.json','worker_console.log']):raise ValueError('existing_run_output')
    resources=json.loads((Path(proposal_path).parent/'resource_preflight.json').read_text())
    if sha(binary)!=resources['sumo_binary_sha256']:raise ValueError('binary_changed')
    reason=resource_reason(0,0,sum(p.stat().st_size for p in task_root.rglob('*') if p.is_file()),shutil.disk_usage('C:/').free,shutil.disk_usage('D:/').free)
    if reason or psutil.virtual_memory().available<4*1024**3:raise ValueError(reason or 'memory_preflight')
    ledger_file=Path(ledger_path)
    if not ledger_file.resolve().is_relative_to(task_root):raise ValueError('ledger_outside_task')
    previous={'attempts':[]}
    if ledger_file.exists():
        previous=json.loads(ledger_file.read_text())
        if sum(x.get('wall_s',0) for x in previous['attempts'])+600>3600:raise ValueError('batch_budget')
    if len(previous['attempts'])>=3 or proposal['runs'][len(previous['attempts'])]['id']!=run_id:
        raise PermissionError('fixed_run_order_or_budget')
    ledger=reserve_attempt(ledger_file,run_id,sha(proposal_path));record=ledger['attempts'][-1]
    worker=repo/'code/scripts/interaction_diagnostic_worker.py'
    # Explicit API call, not the paused CLI. No activation occurs in this task.
    snippet='import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from interaction_diagnostic_worker import execute; execute(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]),sys.argv[5]=="supply")'
    command=[sys.executable,'-S','-c',snippet,str(worker.parent),str(work),str(binary),str(tools),run['role']]
    process=None;started=time.monotonic();peak=0
    try:
        with (work/'worker_console.log').open('wb') as log:
            process=subprocess.Popen(command,cwd=work,stdout=log,stderr=subprocess.STDOUT)
            while process.poll() is None:
                try:parent=psutil.Process(process.pid)
                except psutil.NoSuchProcess:
                    if process.poll() is not None:break
                    raise
                rss=0
                for p in [parent]+parent.children(recursive=True):
                    try:rss+=p.memory_info().rss
                    except psutil.NoSuchProcess:pass
                peak=max(peak,rss)
                reason=resource_reason(time.monotonic()-started,rss,sum(p.stat().st_size for p in task_root.rglob('*') if p.is_file()),shutil.disk_usage('C:/').free,shutil.disk_usage('D:/').free)
                if reason:raise RuntimeError(reason)
                time.sleep(.5)
            if process.returncode:raise RuntimeError('worker_failed:'+str(process.returncode))
        result=json.loads((work/'worker_result.json').read_text())
        if result['status']!='completed' or result.get('sumo_exit_code')!=0:raise RuntimeError('worker_result_failed')
        record['status']='completed_pending_measurement_and_input_verification'
    except BaseException as error:
        if process is not None:stop_owned_tree(process)
        record.update(status='failed_stop',failure=f'{type(error).__name__}:{error}')
        raise
    finally:
        record.update(wall_s=time.monotonic()-started,peak_process_tree_rss_bytes=peak)
        ledger_file.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    return record


if __name__=='__main__':
    raise SystemExit('Paused: researcher must confirm the final proposal before any trajectory launch.')
