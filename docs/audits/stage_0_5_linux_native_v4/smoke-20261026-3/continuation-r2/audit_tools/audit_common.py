"""Continuation audit helpers; no production source is changed."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

class BindingFailure(ValueError):pass
class RequiredCheckFailure(ValueError):pass

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
def write(path,value):
    with Path(path).open('xb') as f:f.write(value if isinstance(value,bytes) else canonical(value)+b'\n')
def display(value):
    # ASCII JSON remains safe even when stdout uses Windows GBK. Raw bytes are
    # stored separately before any display operation.
    data=(json.dumps(value,ensure_ascii=True)+'\n').encode('ascii')
    if hasattr(sys.stdout,'buffer'):sys.stdout.buffer.write(data);sys.stdout.buffer.flush()
    else:sys.stdout.write(data.decode('ascii'))
def need(condition,reason,kind=RequiredCheckFailure):
    if not condition:raise kind(reason)
def optional_text(path):
    try:return dict(present=True,value=Path(path).read_text().strip())
    except OSError as e:return dict(present=False,value=None,observation=type(e).__name__)

class Runner:
    def __init__(self,out):self.out=Path(out);self.commands=[]
    def run(self,name,argv,*,cwd=None,timeout=30,ok=(0,)):
        write(self.out/(name+'.started.json'),dict(argv=[str(v) for v in argv],cwd=str(cwd) if cwd else None,timeout_s=timeout))
        start=time.monotonic();error=None
        try:
            v=subprocess.run(argv,cwd=cwd,capture_output=True,timeout=timeout)
            code,stdout,stderr=v.returncode,v.stdout,v.stderr
        except subprocess.TimeoutExpired as e:code,stdout,stderr=124,e.stdout or b'',e.stderr or b'';error='TimeoutExpired'
        except OSError as e:code,stdout,stderr=127,b'',repr(e).encode('utf-8');error=repr(e)
        write(self.out/(name+'.stdout'),stdout);write(self.out/(name+'.stderr'),stderr)
        row=dict(name=name,argv=[str(v) for v in argv],cwd=str(cwd) if cwd else None,timeout_s=timeout,exit_code=code,
            elapsed_s=time.monotonic()-start,stdout_sha256=sha(self.out/(name+'.stdout')),stderr_sha256=sha(self.out/(name+'.stderr')),error=error)
        self.commands.append(row);write(self.out/(name+'.json'),row)
        need(code in ok,'command_failed:'+name+':'+str(code))
        return stdout

def launch_artifacts(stage):
    capsule=Path(stage)/'smoke_capsule'
    names=['launch_attempt.json','engineering_acceptance.json','coordinator_failure.json','broker.stdout','broker.stderr',
           'archive/controller_receipt.json','archive/isolation_runtime.json','scratch/controller_receipt.json']
    found=[str(capsule/n) for n in names if (capsule/n).exists()]
    # Partially created output directories are ambiguous and cannot be reused.
    found += [str(capsule/n) for n in ['archive','scratch'] if (capsule/n).exists()]
    return found

def unit_is_absent(values):
    return values.get('LoadState')=='not-found' and values.get('ActiveState') in {'inactive','failed'} and not values.get('ControlGroup')

def namespaces_separated(fresh,current,recorded):
    names={'user','mnt','pid','net','ipc'}
    return set(fresh)==set(current)==set(recorded)==names and all(fresh[n] not in {current[n],recorded[n]} for n in names)

def native_processes(runtime,policy,processes):
    hits=[]
    controller=policy['binding']['source_files']['stage_0_5_linux_controller_v4.py']
    for row in processes:
        argv=row.get('cmdline') or []
        if row.get('exe')==runtime['sumo_binary'] or controller in argv or (
            '--child' in argv and str(Path(policy['capsule'])/'policy.json') in argv) or (
            'launch' in argv and any(v.endswith('/stage_0_5_linux_execution_v4.py') for v in argv)):
            hits.append(row)
    return hits
