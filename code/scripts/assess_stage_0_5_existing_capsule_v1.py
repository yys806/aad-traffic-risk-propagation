"""Explicit zero-launch re-assessment of an immutable, completed native capsule."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from stage_0_5_native_capsule_v4 import canonical,sha,require,verify_receipt
from stage_0_5_execution_v2 import measure_completed_capsule
from stage_0_5_isolation_v2 import Scope
from stage_0_5_research_ledger import CHECKS,ResearchLedger


def assess(root,proposal_path,output,candidate):
    root=Path(root).resolve();proposal_path=root/proposal_path
    p=json.loads(proposal_path.read_bytes());run=p['runs'][0];work=root/run['artifact_path']
    require((work/'isolation_runtime.json').is_file(),'existing_sealed_capsule_required')
    require(not (work/'measured_state.parquet').exists(),'existing_analysis_requires_new_explicit_version')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    candidate=Path(candidate);candidate.mkdir(parents=True,exist_ok=False)
    control=json.loads((work/'controller_receipt.json').read_bytes())
    receipt=json.loads((work/'isolation_runtime.json').read_bytes())
    require(receipt['payload_exit_code']==control['exit_code']==0,'completed_native_run_required')
    sources={n:sha(root/n) for n in p['source_sha256']}
    sources['code/scripts/assess_stage_0_5_existing_capsule_v1.py']=sha(Path(__file__))
    allowed={'code/scripts/run_stage_0_5_admission_v3.py'}
    require({n for n in p['source_sha256'] if p['source_sha256'][n]!=sources[n]}<=allowed,'unreviewed_scientific_source_change')
    runtime=dict(python=sys.version,executable=sys.executable,packages={n:importlib.metadata.version(n) for n in ['numpy','pandas','pyarrow']})
    ledger=ResearchLedger(root,p['budget_path'],task_id=p['task_id']).snapshot()
    binding=dict(schema='aad.postrun-assessment.v1',native_launch_allowed=False,native_launches=0,
        parent_proposal_path=proposal_path.relative_to(root).as_posix(),parent_proposal_sha256=sha(proposal_path),
        run_id=run['id'],raw_artifact_sha256=receipt['artifact_sha256'],native_receipt_sha256=sha(work/'isolation_runtime.json'),
        native_controller_source_sha256=receipt['source_sha256'],input_sha256=receipt['input_sha256'],
        assessment_source_sha256=sources,assessment_environment=runtime,prior_ledger_status=ledger['attempts'][run['id']]['status'],
        scope='Same sealed A03 trajectory, unchanged scientific assessor; repair direct-entry package import. No SUMO, no reservation, no old status rewrite.')
    (candidate/'proposal.json').write_bytes(canonical(binding))
    digest=sha(candidate/'proposal.json')
    authorization=dict(proposal_sha256=digest,run_id=run['id'],assessment_allowed=True,native_launch_allowed=False,
        source='Current user task authorizes necessary engineering fixes and evidence acceptance; agent applies delegated chat mandate to this exact offline binding. No digital signature or independent identity claim.')
    (candidate/'authorization.json').write_bytes(canonical(authorization))
    (candidate/'envelope.json').write_bytes(canonical(dict(proposal_sha256=digest,authorization_sha256=sha(candidate/'authorization.json'),native_launches=0,output_path=str(output))))
    accepted=verify_receipt(work,p,sha(proposal_path),p['capsule_policy_sha256'])
    (output/'independent_execution_receipt.json').write_bytes(canonical(accepted))
    runtime_evidence=dict(resource_samples=control['resource_samples'],run_finished_wall_s=control['resource_samples'][-1]['wall_s'],
        exit_code=control['exit_code'],watchdog_failure=control['watchdog_failure'],
        sealed_artifacts={n:sha(work/n) for n in ['fcd.xml','summary.xml','tripinfo.xml','identity_events.jsonl','identity_summary.json']},
        isolation=dict(kind='OS_enforced',backend='linux-userns',binding_sha256=sha(proposal_path),transcript_sha256=accepted['receipt_sha256'],probes=accepted['probes']))
    scope=Scope(root,sources,work)
    scope.bindings.update({root/n:h for n,h in p['measurement_reference_sha256'].items()})
    context=dict(work=work,scope=scope,run=run,proposal=p,validated_inputs={n:(work/n).read_bytes() for n in run['input_files']},
        resource_limits=p['single_attempt_limits'],runtime_evidence=runtime_evidence,binding_sha256=sha(proposal_path),
        native_enforcement_verified=accepted['status']=='Pass',isolation_transcript_sha256=[accepted['receipt_sha256']])
    identity=json.loads((work/'identity_summary.json').read_bytes())
    result=measure_completed_capsule(context,identity)
    (output/'measurement_acceptance.json').write_bytes(canonical(result))
    status='B00_EXECUTED_MEASUREMENT_ACCEPTED' if all(result.get(k) is True for k in CHECKS) else 'B00_EXECUTED_MEASUREMENT_LIMITED'
    (output/'assessment_result.json').write_bytes(canonical(dict(status=status,native_launches=0,run_id=run['id'],
        assessment_proposal_sha256=digest,measurement_sha256=sha(output/'measurement_acceptance.json'),
        prior_ledger_status_preserved=ledger['attempts'][run['id']]['status'],checks={k:result[k] for k in CHECKS})))
    return dict(status=status,checks={k:result[k] for k in CHECKS},output=str(output))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    for name in ['proposal','output','candidate']:parser.add_argument('--'+name,required=True)
    a=parser.parse_args();print(json.dumps(assess(a.repo_root,a.proposal,a.output,a.candidate)))
