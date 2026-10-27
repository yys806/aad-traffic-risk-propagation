"""Explicit V3 preflight/authorization entry. Current build cannot execute SUMO."""
import argparse
import json
from pathlib import Path
import sys

# Direct invocation must use this checkout, without an ambient editable install.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from stage_0_5_admission_v3 import TASK,technical_preflight
from stage_0_5_execution_v2 import NATIVE_LAUNCH_LOCKED,NativeBackend,ExecutionAdapter,native_resource_probe,AdmissionRefused
from stage_0_5_research_ledger import ResearchLedger
from stage_0_5_isolation_v2 import Scope


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['preflight','execute']);p.add_argument('--proposal',type=Path,required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--approval',type=Path)
    p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    a=p.parse_args(argv);root=a.repo_root.resolve()
    guard=Scope(root,{},'code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/admission_reports')
    path=guard._lexical(a.proposal)
    if not path.is_relative_to(root):raise ValueError('proposal_outside_repository')
    try:
        proposal=json.loads(path.read_bytes())
    except (OSError,ValueError) as error:
        print(json.dumps(dict(status='Refused',reason='proposal_unreadable:'+str(error),native_processes_created=0)))
        return 2
    is_v4=proposal.get('schema')=='aad.native-admission.v4'
    if a.mode=='execute' and NATIVE_LAUNCH_LOCKED and not is_v4:
        print(json.dumps(dict(status='Refused',reason='native_build_locked',native_processes_created=0,new_trajectories=0)))
        return 2
    if a.mode=='preflight':
        if is_v4:
            from stage_0_5_linux_execution_v4 import technical_preflight_v4
            result=technical_preflight_v4(root,path,a.run_id)
        else:
            result=technical_preflight(root,path,a.run_id,resource_sample=native_resource_probe(NativeBackend())())
        print(json.dumps(result,ensure_ascii=False));return 0 if result['ready'] else 2
    if a.approval is None:raise ValueError('exact_approval_file_required')
    approved_path=guard._lexical(a.approval)
    if not approved_path.is_relative_to(root):raise ValueError('approval_outside_repository')
    approval=json.loads(approved_path.read_bytes())
    ledger=ResearchLedger(root,proposal['budget_path'],task_id=TASK)
    try:
        state=ExecutionAdapter(root,ledger,'code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/admission_reports').execute(path.relative_to(root).as_posix(),approval,a.run_id)
    except AdmissionRefused as error:
        print(json.dumps(dict(status='Refused',reason=str(error),native_processes_created=0)));return 2
    print(json.dumps(state));return 0


if __name__=='__main__':raise SystemExit(main())
