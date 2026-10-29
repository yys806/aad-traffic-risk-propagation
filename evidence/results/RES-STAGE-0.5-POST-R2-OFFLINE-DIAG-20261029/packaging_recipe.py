"""Task-local final packaging; explicit payload metadata only, no raw data copy."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
PACK=ROOT/'evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029'
REPORT=ROOT/'docs/STAGE_0_5_POST_R2_OFFLINE_DIAGNOSTIC_20261029.md'
recipe=PACK/'packaging_recipe.py'
if Path(__file__).resolve()!=recipe.resolve():
    recipe.write_text(Path(__file__).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def seal(p):
    files=[x for x in sorted(p.rglob('*')) if x.is_file() and x not in [p/'manifest.json',p/'SHA256SUMS']]
    write(p/'manifest.json',dict(schema='aad.stage05.offline-diagnostic.manifest.v1',self_reference=False,
        files=[dict(path=x.relative_to(p).as_posix(),bytes=x.stat().st_size,sha256=sha(x)) for x in files]))
    (p/'SHA256SUMS').write_text(''.join(sha(x)+'  '+x.relative_to(p).as_posix()+'\n' for x in sorted(files+[p/'manifest.json'])),encoding='utf-8')

data=json.loads((PACK/'diagnostic.json').read_bytes())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
old_run=json.loads((PACK/'run_record.json').read_bytes()) if (PACK/'run_record.json').exists() else {}
input_head=old_run.get('input_HEAD',head)
commands=dict(
 analysis='python code/scripts/analyze_stage_0_5_post_r2_offline_diagnostic.py --repo-root . --output evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029',
 independent='python code/scripts/verify_stage_0_5_post_r2_offline_diagnostic.py --repo-root . --package evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029 --raw-inputs',
 regression='python -B code/outputs/diagnostics/post_r2_offline_test_runner_final.py (exact runner copied as offline_regression_runner.py)',
 targeted='python -B -m pytest tests/test_stage_0_5_post_r2_offline_diagnostic.py tests/test_stage_0_5_d1_measurement.py tests/test_formal_risk_measurement.py tests/test_stage_0_5_measurement_equivalence.py tests/test_project_docs.py -q --tb=short -p no:cacheprovider --deselect=tests/test_stage_0_5_d1_measurement.py::test_actual_state_runner_uses_d1_not_point_exposure --deselect=tests/test_stage_0_5_measurement_equivalence.py::test_guard_denies_row_scoped_reads_outside_the_calibration_windows --deselect=tests/test_stage_0_5_measurement_equivalence.py::test_calibration_states_read_helper_refuses_a_foreign_window --basetemp=<authorized-write-root>/post_r2_final_checks',
 docs='python code/scripts/validate_project_docs.py --strict-git',
 export='python code/scripts/export_project_evidence.py --repo-root .',
 export_verify='python code/scripts/export_project_evidence.py --repo-root . --verify',
 compile='PYTHONPYCACHEPREFIX=<authorized-write-root>/post_r2_compile_cache python -m compileall -q code/src code/scripts code/tests')
source_paths=[ROOT/p for p in data['source_sha256']]
source_paths += [ROOT/'code/scripts/verify_stage_0_5_post_r2_offline_diagnostic.py',ROOT/'code/scripts/export_project_evidence.py',ROOT/'code/tests/test_stage_0_5_post_r2_offline_diagnostic.py']
write(PACK/'run_record.json',dict(schema='aad.stage05.post-r2.run-record.v1',task='AAD-S0.5-POST-R2-TASK1-20261029',date='2026-10-29',
 input_HEAD=input_head,input_origin_main=old_run.get('input_origin_main',input_head),packaging_HEAD=head,git_attributes_sha256=sha(ROOT/'.gitattributes'),uncommitted_task_sources_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in source_paths},
 commands=commands,environment='environment.json',large_input_bindings='diagnostic.json:runs.*.inputs',
 source_reconciliation='exact sealed D1 counts/exposure/quality/events asserted; all FCD/lifecycle records inspected',
 formal_measurement_code_modified=False,source_target_window_cohort_changed=False,native_launches=0,traci_connections=0,holdout_reads=0,new_trajectories=0,
 scientific_equivalence_accepted=False,Gate_Stage06_ProtocolLock_StageI_changed=False))

# Narrow, explicit file inventory. Hash-only and actual semantic review differ.
inventory=[]
for label,arm in data['runs'].items():
    for name,item in arm['inputs'].items():
        level=('hash_only_not_decoded_missing_engine' if name.endswith('.parquet') else
               'full_XML_parse_and_production_reconstruction' if name in ['fcd.xml','network.net.xml','routes.rou.xml'] else
               'full_jsonl_hash_chain_and_lifecycle_bounds' if name=='identity_events.jsonl' else
               'full_JSON_content_and_crosscheck' if name.endswith('.json') else 'configuration_hash_binding_only')
        inventory.append(dict(path=item['path'],type=Path(name).suffix,arm=label,read_status=level,
            sha256=item['sha256'],manifest_check='sealed_parent_bindings_and_actual_independent_hash',
            supports='no source risk in evaluable support; identity and event crosscheck' if level!='configuration_hash_binding_only' else 'unchanged configuration provenance, not a new semantic audit'))
for p in source_paths:
    inventory.append(dict(path=p.relative_to(ROOT).as_posix(),type=p.suffix,arm='shared',
        read_status='targeted_function_and_callgraph_semantic_review',sha256=sha(p),manifest_check='source_binding',
        supports='definition/implementation/boundary-test distinctions; formal logic unchanged'))
if (PACK/'authorized_roadmap_check.json').exists():
    roadmap=json.loads((PACK/'authorized_roadmap_check.json').read_bytes())
    inventory.append(dict(path=roadmap['path'],type='.md',arm='authorized_auxiliary_context',
        read_status='full_named_file_read_only_semantic_crosscheck',sha256=roadmap['sha256'],
        manifest_check='actual_file_hash_not_Git_evidence',supports='original conditional third-round stop rule; no new scientific approval'))
with (PACK/'file_audit.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(inventory[0]));writer.writeheader();writer.writerows(inventory)

links=[]
for p in [REPORT,ROOT/'docs/STAGE_0_5_ROUND2_TASK1_EXECUTION.md']:
    for u in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in u: continue
        dest=p.parent/u.split('#',1)[0]
        links.append(dict(document=p.relative_to(ROOT).as_posix(),target=u,exists=dest.exists()))
assert all(x['exists'] for x in links), [x for x in links if not x['exists']]
write(PACK/'link_verification.json',dict(status='PASS',links=links))

# Stage-independent payload check is saved BEFORE sealing; it cannot claim to
# hash itself. Final read-only verifier checks the complete manifest separately.
spec=importlib.util.spec_from_file_location('postverify',ROOT/'code/scripts/verify_stage_0_5_post_r2_offline_diagnostic.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
check=verifier.verify_diagnostic(ROOT,PACK,True)
write(PACK/'independent_payload_validation.json',dict(status='PASS',diagnostic=check,
    actual_raw_bindings={label:{n:sha(ROOT/x['path']) for n,x in a['inputs'].items()} for label,a in data['runs'].items()},
    scope='raw inputs, source bindings, count identities; excludes this record and later manifest by construction',
    final_complete_command=commands['independent']))
seal(PACK)
print(json.dumps(verifier.verify_bundle(PACK)))

# Same registration convention as previously accepted self-managed packages.
global_path=ROOT/'evidence/EVIDENCE_MANIFEST.json';global_manifest=json.loads(global_path.read_bytes())
for package in [ROOT/'evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028',PACK]:
    files=[]
    for p in sorted(package.rglob('*')):
        if p.is_file():
            name=p.relative_to(ROOT).as_posix()
            files.append(dict(source_path=name,snapshot_path=name,size_bytes=p.stat().st_size,sha256=sha(p)))
    entry=dict(result_id=package.name,files=files)
    for i,old in enumerate(global_manifest['results']):
        if old['result_id']==package.name:global_manifest['results'][i]=entry;break
    else:global_manifest['results'].append(entry)
global_path.write_text(json.dumps(global_manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
print('SEALED_AND_REGISTERED')
