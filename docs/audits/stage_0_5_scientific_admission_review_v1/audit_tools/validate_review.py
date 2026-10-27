"""Verify review schemas, references and protected baseline without simulation."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[4]
AUD='docs/audits/stage_0_5_scientific_admission_review_v1'
REPORT='docs/STAGE_0_5_B00_SCIENTIFIC_ADMISSION_REVIEW_V1_2026-10-27.md'
CONTEXT=['AI_CONTEXT/'+n for n in ['00_PROJECT_STATE.md','05_EXPERIMENTS.md','07_KNOWN_ISSUES.md','08_CHANGELOG.md']]
CHECKOUT_DOCS={'AGENTS.md','PROJECT_CONTEXT.md'}
GIT='D:/Git/mingw64/bin/git.exe' if os.name=='nt' else 'git'


def load(n): return json.loads((ROOT/n).read_bytes())
def digest(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output([GIT,'-C',str(ROOT),*args])
def safe(name):
    p=Path(name)
    assert not p.is_absolute() and ':' not in name and '..' not in p.parts, name
    target=ROOT/p
    assert target.resolve().is_relative_to(ROOT) and not any(q.is_symlink() for q in [target,*target.parents]), name
    return target


def verify_document_checkout(name, entry, actual, blob, object_id):
    # This exception is deliberately limited to two non-scientific Markdown files.
    assert name in CHECKOUT_DOCS and entry['path']==name,name
    p=entry['checkout_provenance']
    assert p['schema']=='aad.reviewed-document-checkout.v1'
    assert p['relation']=='reviewed_CRLF_equals_baseline_LF_with_CRLF_only'
    assert p['git_blob_oid']==object_id and p['git_blob_sha256']==digest(blob)
    assert b'\r' not in blob and b'\n' in blob
    reviewed=blob.replace(b'\n',b'\r\n')
    assert digest(reviewed)==entry['sha256']==p['reviewed_bytes_sha256']
    assert actual in (blob,reviewed),name
    return 'reviewed_CRLF_bytes' if actual==reviewed else 'baseline_Git_LF_checkout'


def main():
    matrix=load(AUD+'/review_matrix.json');packet=load(AUD+'/decision_packet.json')
    assert matrix['schema']=='aad.scientific-admission-review-matrix.v1'
    assert packet['schema']=='aad.scientific-admission-decision-packet.v1'
    assert matrix['status']==packet['status']=='RESEARCH_APPROVAL_PENDING'
    evidence=load(AUD+'/evidence_manifest.json')
    entries={e['path']:e for e in evidence['files']}
    local_only_unavailable=set()
    issues={i['issue_id']:i for i in matrix['issues']};other={i['issue_id']:i for i in packet['issues']}
    assert len(issues)==len(matrix['issues'])==matrix['total_issues']==packet['total_issues']==15
    assert issues.keys()==other.keys()
    required={'issue_id','question','current_fact','evidence_paths','evidence_sha256','code_locations','observation',
        'interpretation','remaining_uncertainty','classification','available_options','scientific_implications',
        'required_validation','recommended_next_step','researcher_decision_required','current_status'}
    for ident,i in issues.items():
        assert required<=i.keys(),ident
        assert set(i['classification'])<={'RESOLVABLE_FROM_EXISTING_EVIDENCE','RESEARCHER_DECISION_REQUIRED',
            'REQUIRES_FUTURE_DYNAMIC_EXPERIMENT','ENGINEERING_AMBIGUITY_REQUIRES_REVIEW'}
        for key in other[ident]: assert i[key]==other[ident][key], (ident,key)
        assert i['evidence_paths'] and i['available_options'] and i['required_validation']
        for name,h in i['evidence_sha256'].items():
            path=safe(name)
            if not path.exists():
                assert name in entries and entries[name]['portable'] is False,name
                local_only_unavailable.add(name)
            else:
                assert digest(path.read_bytes())==h,(ident,name)
        for c in i['code_locations']:
            tree=ast.parse(safe(c['path']).read_text(encoding='utf-8-sig'))
            assert any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==c['function'] and
                n.lineno==c['line'] and n.end_lineno==c['end_line'] for n in ast.walk(tree)),c
    assert sum(i['researcher_decision_required'] for i in issues.values())==packet['decision_required_count']==9
    assert packet['execution_authorized'] is False and packet['decisions_recorded']==[]
    baseline=evidence['baseline_commit']
    assert baseline=='753b666a3c9e4b8d88add2ead1973ff8e2d4439f'
    historical_context=[];document_checkout_representations={}
    for entry in evidence['files']:
        path=safe(entry['path'])
        if not path.exists():
            assert entry['portable'] is False,entry['path']
            local_only_unavailable.add(entry['path'])
            continue
        actual=path.read_bytes();h=digest(actual)
        if 'checkout_provenance' in entry:
            assert entry['path'] not in load(AUD+'/verified_inventory.json')['files'],entry['path']
            assert entry['checkout_provenance']['baseline_commit']==baseline
            spec=baseline+':'+entry['path']
            document_checkout_representations[entry['path']]=verify_document_checkout(
                entry['path'],entry,actual,git('cat-file','blob',spec),git('rev-parse',spec).decode().strip())
            continue
        if h!=entry['sha256']:
            assert entry['path'] in CONTEXT,entry['path']
            assert digest(git('cat-file','--filters',baseline+':'+entry['path']))==entry['sha256']
            historical_context.append(entry['path'])
    # Preserve all original tracked files except the four permitted dated increments.
    changes=git('diff',baseline,'--name-only').decode().splitlines()
    assert all(n in CONTEXT or n==REPORT or n.startswith(AUD+'/') for n in changes), changes
    for name in CONTEXT:
        before=git('cat-file','--filters',baseline+':'+name).decode('utf-8')
        after=(ROOT/name).read_text(encoding='utf-8')
        title,_,tail=before.partition('\n')
        assert after.startswith(title+'\n') and after.endswith(tail.lstrip('\n')),name
    old=load('docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/audit_manifest.json')
    for name,h in old['files'].items():
        data=git('cat-file','--filters',baseline+':'+name)
        assert digest(data)==h,name
    v6='evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/'
    p=load(v6+'proposal.json');profile=load(v6+'admission_profile.json')
    assert digest((ROOT/v6/'proposal.json').read_bytes())==matrix['candidate_proposal_sha256']
    assert all(p[k] is False for k in ['execution_allowed','researcher_confirmed','protocol_frozen'])
    assert all(v is False for v in p['admission'].values())
    assert all(profile[k] is False for k in ['accepted_for_new_task','execution_allowed','researcher_confirmed','protocol_frozen'])
    assert profile['native_launch_locked'] is True
    policy=load('docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5/research_policy.json')
    assert policy['binding']['accepted_build'] is False
    ledger=load_ledger('docs/audits/stage_0_5_ready_to_admit_v3/execution_events.jsonl')
    assert len(ledger)==1 and ledger[0]['kind']=='task_created'
    assert not (ROOT/p['runs'][0]['artifact_path']).exists()
    manifest=ROOT/AUD/'audit_manifest.json'
    if manifest.exists():
        m=json.loads(manifest.read_bytes())
        for name,h in m['files'].items(): assert digest(safe(name).read_bytes())==h,name
        expected={p.relative_to(ROOT).as_posix() for p in (ROOT/AUD).rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.name not in ['audit_manifest.json','SHA256SUMS']}
        expected.update([REPORT,*CONTEXT])
        assert set(m['files'])==expected,(set(m['files'])-expected,expected-set(m['files']))
        pairs=[line.split('  ',1) for line in (ROOT/AUD/'SHA256SUMS').read_text().splitlines()]
        sums={name:h for h,name in pairs}
        assert len(sums)==len(pairs)
        assert sums==dict(m['files'],**{AUD+'/audit_manifest.json':digest(manifest.read_bytes())})
    print(json.dumps(dict(status='Pass',issues=15,researcher_decisions=9,protected_tracked_files_unchanged=True,
        historical_manifest_files=len(old['files']),baseline_context_snapshots=historical_context,
        document_checkout_representations=document_checkout_representations,
        local_raw_files_not_recomputed=sorted(local_only_unavailable),
        new_research_trajectories=0,native_launches=0,real_TraCI_connections=0),ensure_ascii=True))


def load_ledger(name): return [json.loads(line) for line in safe(name).read_bytes().splitlines()]


if __name__=='__main__': main()
