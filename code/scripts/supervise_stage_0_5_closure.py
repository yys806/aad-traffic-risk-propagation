"""Finite process-tree supervision for closure analysis and actual SUMO workers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import psutil


def supervise(batch,label,command,*,wall_s,memory_bytes=3*1024**3,artifact_bytes=2*1024**3):
    if (batch/'experiment_plan.json').exists():
        p=json.loads((batch/'experiment_plan.json').read_text(encoding='utf-8'))
        actual=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if p.get('controller_sha256')!=actual:raise PermissionError('controller_SHA')
    audit=batch/'supervision';audit.mkdir(exist_ok=True)
    target=audit/(label+'.json')
    if target.exists():raise PermissionError('no_supervised_retry_or_overwrite')
    start=time.monotonic();peak=0;reason=None
    with (audit/(label+'.log')).open('w',encoding='utf-8') as log:
        p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        process=psutil.Process(p.pid)
        while p.poll() is None:
            try:peak=max(peak,process.memory_info().rss+sum(c.memory_info().rss for c in process.children(recursive=True) if c.is_running()))
            except psutil.Error:pass
            total=sum(f.stat().st_size for folder in ['summary','runs','supervision'] for f in (batch/folder).rglob('*') if f.is_file())
            if peak>memory_bytes:reason='memory'
            elif total>artifact_bytes:reason='disk'
            elif time.monotonic()-start>wall_s:reason='timeout'
            if reason:
                for child in process.children(recursive=True):
                    try:child.terminate()
                    except psutil.Error:pass
                p.terminate();break
            time.sleep(.25)
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    r=dict(label=label,command=command,exit_code=p.returncode,failure=reason,wall_s=time.monotonic()-start,peak_sampled_tree_RSS_bytes=peak,
        limits=dict(wall_s=wall_s,memory_bytes=memory_bytes,artifact_bytes=artifact_bytes),passed=p.returncode==0 and reason is None)
    target.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r),flush=True)
    return 0 if r['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True,type=Path);p.add_argument('--label',required=True);p.add_argument('--wall-s',required=True,type=float);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    sys.exit(supervise(a.batch.resolve(),a.label,a.command[1:] if a.command[:1]==['--'] else a.command,wall_s=a.wall_s))
