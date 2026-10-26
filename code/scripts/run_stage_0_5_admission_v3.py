"""Explicit V3 preflight/authorization entry. Current build cannot execute SUMO."""
import argparse
import json
from pathlib import Path
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
    if a.mode=='execute' and NATIVE_LAUNCH_LOCKED:
        print(json.dumps(dict(status='Refused',reason='native_build_locked',native_processes_created=0,new_trajectories=0)))
        return 2
    guard=Scope(root,{},'code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/admission_reports')
    path=guard._lexical(a.proposal)
    if not path.is_relative_to(root):raise ValueError('proposal_outside_repository')
    if a.mode=='preflight':
        result=technical_preflight(root,path,a.run_id,resource_sample=native_resource_probe(NativeBackend())())
        print(json.dumps(result,ensure_ascii=False));return 0 if result['ready'] else 2
    if a.approval is None:raise ValueError('exact_approval_file_required')
    approved_path=guard._lexical(a.approval)
    if not approved_path.is_relative_to(root):raise ValueError('approval_outside_repository')
    proposal=json.loads(path.read_bytes());approval=json.loads(approved_path.read_bytes())
    ledger=ResearchLedger(root,proposal['budget_path'],task_id=TASK)
    try:
        state=ExecutionAdapter(root,ledger,'code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/admission_reports').execute(path.relative_to(root).as_posix(),approval,a.run_id)
    except AdmissionRefused as error:
        print(json.dumps(dict(status='Refused',reason=str(error),native_processes_created=0)));return 2
    print(json.dumps(state));return 0


if __name__=='__main__':raise SystemExit(main())
