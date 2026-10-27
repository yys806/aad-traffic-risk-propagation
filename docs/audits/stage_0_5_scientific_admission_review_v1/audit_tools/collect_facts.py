"""Read-only scientific admission audit. Never prepares or executes a run."""
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
V6 = 'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6'
sys.path.insert(0, str(ROOT / 'code/scripts'))
from prepare_stage_0_5_b00_admission_v6 import verify_existing, verify_candidate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_bytes())


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    git = 'D:/Git/mingw64/bin/git.exe' if os.name == 'nt' else 'git'
    def g(*args):
        return subprocess.check_output([git, '-C', str(ROOT), *args]).decode('utf-8').strip()
    p = read(V6 + '/proposal.json'); run = p['runs'][0]
    verified = verify_existing(ROOT)
    inventory = dict(verified['verified_files'])
    assert len(inventory) == 347
    candidate = verify_candidate(ROOT)
    inventory.update({(V6 + '/' + q.name): digest(q) for q in (ROOT / V6).iterdir() if q.is_file()})
    original = 'code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs/ID1_SUPPLY_0750/'
    ds = 'code/outputs/formal/calibration/stage_0_5_depart_speed_candidate_v1/prepared_inputs/ID1_SUPPLY_0750_DS10MAX_V1/'
    def vehicles(name):
        return {v.get('id'): dict(v.attrib) for v in ET.parse(ROOT / name).getroot().findall('vehicle')}
    a = vehicles(original + 'routes.rou.xml'); b = vehicles(run['input_files']['routes.rou.xml'])
    assert list(a) == list(b)
    changed = [dict(id=k, before=a[k], after=b[k]) for k in a if a[k] != b[k]]
    initial = [k for k in a if k.startswith('i')]
    assert len(a) == 1150 and len(initial) == 117 and len(changed) == 38
    assert all(x['id'] in initial and float(x['before']['departSpeed']) == 10 and
               x['after'] == dict(x['before'], departSpeed='max') for x in changed)
    assert all(float(a[k]['depart']) == 0 for k in initial)
    assert all(a[k] == b[k] for k in a if k not in initial)
    def xml_options(name):
        root = ET.parse(ROOT / name).getroot()
        return {n.tag: n.get('value') for n in root.iter() if n.get('value') is not None}
    comparisons = []
    for role in ['network.net.xml', 'routes.rou.xml', 'run.sumocfg']:
        names = [original + role, ds + role, run['input_files'][role]]
        for name in names:
            inventory[name] = digest(ROOT / name)
        entry = dict(role=role, files=[dict(path=n, sha256=inventory[n]) for n in names],
                     original_candidate_bytes_equal=(ROOT/names[0]).read_bytes() == (ROOT/names[2]).read_bytes())
        if role == 'run.sumocfg':
            opts = [xml_options(n) for n in names]
            entry['option_differences'] = {k: [x.get(k) for x in opts] for k in set().union(*opts) if len({x.get(k) for x in opts}) > 1}
            entry['candidate_options'] = opts[2]
        comparisons.append(entry)
    refname = next(iter(p['measurement_reference_sha256']))
    with (ROOT/refname).open(encoding='utf-8') as stream:
        refs = list(csv.DictReader(stream))
    assert {(int(r['t_block']), int(r['y_block'])) for r in refs} == {(t,y) for t in range(9) for y in range(2)}
    assert all(float(r['states']) >= 10 and float(r['D1_E_veh_s']) > 0 and r['support_status']=='observed' for r in refs)
    policyname = 'docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5/research_policy.json'
    policy = read(policyname)
    fields = {'accepted_for_new_task', 'accepted_build', 'native_launch_locked', 'execution_allowed',
              'researcher_confirmed', 'protocol_frozen'}
    readers=[]; locations={}
    for folder in ['code/scripts', 'code/src/riskprop']:
        for path in sorted((ROOT/folder).glob('*.py')):
            source = path.read_text(encoding='utf-8-sig'); lines = source.splitlines(); tree = ast.parse(source)
            name = path.relative_to(ROOT).as_posix()
            hits = [dict(line=i, text=line.strip()) for i,line in enumerate(lines,1)
                    if any(f in line for f in fields)]
            if hits:
                readers.append(dict(path=name, sha256=digest(path), hits=hits))
            if name in p['source_sha256'] or name.endswith('prepare_stage_0_5_b00_admission_v6.py'):
                inventory[name] = digest(path)
                locations[name] = [dict(function=n.name, line=n.lineno, end_line=n.end_lineno)
                    for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    heads={n:g('rev-parse',n) for n in ['HEAD','origin/main']}
    source_git=[]
    for name, expected in p['source_sha256'].items():
        blob = subprocess.check_output([git,'-C',str(ROOT),'show',heads['HEAD']+':'+name])
        h = hashlib.sha256(blob).hexdigest()
        checkout = subprocess.check_output([git,'-C',str(ROOT),'cat-file','--filters',heads['HEAD']+':'+name])
        checkout_sha = hashlib.sha256(checkout).hexdigest()
        assert checkout_sha == digest(ROOT/name) == expected, name
        source_git.append(dict(path=name, expected_sha256=expected, current_git_blob_sha256=h,
            git_attribute_checkout_sha256=checkout_sha, raw_blob_matches=h==expected))
    budget = read(p['budget_path'])
    # Inspect existence only; never construct ResearchLedger or create its lock.
    ledger_keys = {k:v for k,v in budget.items() if any(s in k.lower() for s in ['ledger','output','execution','budget'])}
    previous_audit = read('docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/audit_manifest.json')
    history_log = 'code/outputs/formal/calibration/stage_0_5_interaction_diagnostics_v1/ID1_SUPPLY_0750/worker_console.log'
    inventory[history_log]=digest(ROOT/history_log)
    historical_lines=[dict(line=i,text=s) for i,s in enumerate((ROOT/history_log).read_text(encoding='utf-8',errors='replace').splitlines(),1)
                       if any(k in s for k in ['i0007','i0063','Error:','discard'])]
    facts=dict(schema='aad.scientific-review-facts.v1', baseline=heads, candidate=candidate,
        historical_bindings_reverified=347, generation_git_snapshot=p['git_state'],
        source_git_verification=source_git, controller_source_count=len(p['controller_source_sha256']),
        production_source_closure_sha256=verified['production_source_closure_sha256'],
        input_comparison=comparisons, DS38=dict(total=len(a),initial=len(initial),noninitial=len(a)-len(initial),
            changes=changed, unchanged_initial_ids=sorted(set(initial)-{x['id'] for x in changed}),
            noninitial_depart_min_s=min(float(v['depart']) for k,v in a.items() if k not in initial),
            noninitial_depart_max_s=max(float(v['depart']) for k,v in a.items() if k not in initial),
            i0007=b['i0007_i0007'], actual_insertion='unknown; no new native run'),
        reference_units=refs, research_policy=dict(path=policyname,sha256=digest(ROOT/policyname),
            accepted_build=policy['binding']['accepted_build'],binding_limits=p['single_attempt_limits']),
        protected_flags=dict(proposal={k:p[k] for k in ['execution_allowed','researcher_confirmed','protocol_frozen']},
            admission=p['admission'],profile=read(V6+'/admission_profile.json')),
        research_output_exists=(ROOT/run['artifact_path']).exists(), budget_relevant=ledger_keys,
        historical_error_lines=historical_lines, source_locations=locations,
        archive_only_scope=True,SUMO_launches=0,real_TraCI_connections=0,new_B00_research_trajectories=0)
    inventory['.gitattributes']=digest(ROOT/'.gitattributes')
    write('static_facts.json',facts)
    write('state_field_readers.json',dict(schema='aad.state-field-reader-inventory.v1',
        scope=['code/scripts/*.py','code/src/riskprop/*.py'],readers=readers,
        semantics='Lexical inventory includes writers/tests-as-evidence/historical code; active call paths are classified separately.'))
    write('verified_inventory.json',dict(schema='aad.rechecked-file-inventory.v1',files=inventory))
    print(json.dumps(dict(status='Pass',historical_bound_files=347,source_files=len(source_git),
        DS38_changes=len(changed),reference_units=len(refs),research_output_exists=facts['research_output_exists'],
        comparison=comparisons,ledger=ledger_keys),ensure_ascii=True))


if __name__=='__main__':
    main()
