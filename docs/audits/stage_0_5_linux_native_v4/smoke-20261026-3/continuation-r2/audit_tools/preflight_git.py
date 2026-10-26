"""Fresh explicit output and clone paths; existing historical audit is allowed."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_common import Runner,write,display,need,sha,BindingFailure

def check(root,clone,out):
    root=Path(root).resolve();clone=Path(clone).resolve();out=Path(out).resolve()
    need(out.is_relative_to(root/'code/tmp') and clone.is_relative_to(root/'code/tmp'),'scoped_task_directories_required')
    out.mkdir(exist_ok=False);run=Runner(out);record=dict(status='HELPER_ERROR',commands=run.commands)
    try:
        need(not clone.exists(),'new_pure_Git_clone_required')
        head=run.run('current_head',['git','rev-parse','HEAD'],cwd=root).decode().strip()
        need(run.run('current_clean',['git','status','--porcelain'],cwd=root)==b'','current_worktree_dirty')
        run.run('clone',['git','clone','--no-hardlinks','--quiet',str(root),str(clone)],cwd=root,timeout=180)
        need(run.run('clone_head',['git','rev-parse','HEAD'],cwd=clone).decode().strip()==head,'clone_HEAD_mismatch')
        need(not (clone/'dataset').exists() and not (clone/'code/outputs/formal').exists(),'data_free_clone_required')
        p=json.loads((clone/'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v5/proposal.json').read_bytes())
        for n,h in p['source_sha256'].items():need(sha(clone/n)==sha(root/n)==h,'bound_source_drift:'+n,BindingFailure)
        controller={}
        for n,h in p['controller_source_sha256'].items():
            data=run.run('git_source_'+n,['git','show','HEAD:code/scripts/'+n],cwd=root)
            need(hashlib.sha256(data).hexdigest()==h,'Git_production_source_drift:'+n,BindingFailure);controller[n]=h
        run.run('pure_git_docs',[sys.executable,'-B','code/scripts/validate_project_docs.py','--strict-git','--require-clean'],cwd=clone)
        run.run('pure_git_evidence',[sys.executable,'-B','code/scripts/export_project_evidence.py','--repo-root','.','--verify'],cwd=clone)
        tests=['tests/test_stage_0_5_native_capsule_v4.py','tests/test_stage_0_5_linux_isolation.py','tests/test_stage_0_5_smoke3_preflight.py','tests/test_project_docs.py']
        run.run('pure_git_tests',[sys.executable,'-B','-m','pytest',*tests,'-q','-p','no:cacheprovider','--basetemp=tmp/smoke3_continuation_pure_git'],cwd=clone/'code',timeout=120)
        record.update(status='Pass',current_HEAD=head,clone=str(clone),controller_source_sha256=controller,source_files_verified=len(p['source_sha256']))
    except (BindingFailure,ValueError) as e:record.update(status='CHECK_FAILED',error=repr(e));raise
    except BaseException as e:record.update(status='HELPER_ERROR',error=repr(e));raise
    finally:write(out/'git_preflight.json',record);display(dict(status=record['status'],commands=len(run.commands),output=str(out)))
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--clone',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();check(a.repo_root,a.clone,a.output_dir)
