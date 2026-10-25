"""Offline, fail-closed DS10MAX candidate. No simulation entry point.

Only approved prepared XML, two approved baseline FCDs and the failed capsule
are read. Full vehicle audit stays local; portable records are aggregates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from interaction_task_boundary import Boundary

ROOT = Path(__file__).resolve().parents[2]
LOCAL = Path('code/outputs/formal/calibration/stage_0_5_depart_speed_candidate_v1')
RESULT = 'RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1'
PLAN = 'docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md'
OLD = Path('evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1')
PREFLIGHT = Path('evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1')
PREPARED = Path('code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs')
PARENTS = ('ID1_SUPPLY_0750', 'ID2_SUPPLY_0805', 'ID3_RAMP_0750')
DOC_URLS = {
    'current_vehicle_definitions.html': 'https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html',
    'current_vehicle_insertion.html': 'https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html',
    'v1_26_0_vehicle_definitions.md': 'https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/docs/web/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.md',
    'v1_26_0_vehicle_insertion.md': 'https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/docs/web/docs/Simulation/VehicleInsertion.md',
}
PORTABLE_NAMES = ('impact_summary.json', 'official_semantics.json', 'review_proposal.json',
                  'provenance.json', 'validation_record.json', 'boundary_summary.json',
                  'PROPOSAL_SHA256', 'SHA256SUMS')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()


def write(path, data):
    Path(path).write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def xml(data):
    if b'<!DOCTYPE' in data or b'<!ENTITY' in data:
        raise ValueError('external_XML_forbidden')
    return ET.fromstring(data)


def initial_vehicles(root):
    vehicles = root.findall('vehicle')
    if len({v.get('id') for v in vehicles}) != len(vehicles):
        raise ValueError('duplicate_vehicle_id')
    initial = [v for v in vehicles if v.get('id', '').startswith('i')]
    if any(float(v.get('depart')) != 0 for v in initial):
        raise ValueError('initial_not_at_zero')
    if any(float(v.get('depart')) == 0 for v in vehicles if v not in initial):
        raise ValueError('unclassified_zero_departure')
    return initial


def revise_routes(data):
    """Change only initial numerical speed exactly 10, preserving other bytes."""
    root = xml(data)
    targets = {v.get('id') for v in initial_vehicles(root) if float(v.get('departSpeed')) == 10.0}
    changed = []

    def replace(match):
        tag = match.group()
        vehicle = ET.fromstring(tag if tag.endswith(b'/>') else tag[:-1] + b'/>')
        if vehicle.get('id') not in targets: return tag
        tag, n = re.subn(rb'\bdepartSpeed\s*=\s*([\x22\x27])10(?:\.0*)?\1', b'departSpeed="max"', tag)
        if n != 1: raise ValueError('unsupported_target_speed_encoding')
        changed.append(vehicle.get('id'))
        return tag

    revised = re.sub(rb'<vehicle\b[^>]*>', replace, data)
    if set(changed) != targets or len(changed) != len(targets):
        raise ValueError('inexact_edit')
    confirm_revision(data, revised)
    return revised, sorted(changed)


def confirm_revision(before, after):
    a, b = xml(before), xml(after)
    if len(list(a)) != len(list(b)) or a.attrib != b.attrib:
        raise ValueError('root_changed')
    changed = []
    initial = {v.get('id') for v in initial_vehicles(a)}
    for old, new in zip(a, b):
        expected = dict(old.attrib)
        if old.tag == 'vehicle' and old.get('id') in initial and float(old.get('departSpeed')) == 10:
            expected['departSpeed'] = 'max'; changed.append(old.get('id'))
        if old.tag != new.tag or new.attrib != expected or old.text != new.text or old.tail != new.tail:
            raise ValueError('unauthorized_attribute_change')
        if [ET.tostring(c) for c in old] != [ET.tostring(c) for c in new]:
            raise ValueError('children_changed')
    return changed


def vehicle_audit(routes, network):
    root, net = xml(routes), xml(network)
    types = {v.get('id'): dict(v.attrib) for v in root.findall('vType')}
    paths = {r.get('id'): r.get('edges').split() for r in root.findall('route')}
    lanes = {l.get('id'): dict(l.attrib) for e in net.findall('edge') for l in e.findall('lane')}
    rows = []
    for v in initial_vehicles(root):
        route = paths[v.get('route')]
        lane_id = route[0] + '_' + v.get('departLane')
        lane, typ = lanes[lane_id], types[v.get('type')]
        if typ['vClass'] != 'passenger' or typ['speedFactor'] != '1.0' or typ['speedDev'] != '0.0':
            raise ValueError('unexpected_type')
        if 'allow' in lane and 'passenger' not in lane['allow'].split(): raise ValueError('lane_disallows_passenger')
        if 'passenger' in lane.get('disallow', '').split(): raise ValueError('lane_disallows_passenger')
        position = float(v.get('departPos'))
        if not 0 <= position <= float(lane['length']): raise ValueError('invalid_depart_position')
        rows.append(dict(v.attrib, native_lane=lane_id, lane_limit_mps=float(lane['speed']),
                         lane_length_m=float(lane['length']), vtype_max_mps=float(typ['maxSpeed']),
                         revised=float(v.get('departSpeed')) == 10,
                         route_lane_limits=[[e, [dict(l.attrib) for edge in net.findall('edge')
                                                  if edge.get('id') == e for l in edge.findall('lane')]] for e in route]))
    aggregate = {
        'initial_count': len(rows), 'numeric_10_candidate_count': sum(r['revised'] for r in rows),
        'numeric_speed_range_mps': [min(float(r['departSpeed']) for r in rows), max(float(r['departSpeed']) for r in rows)],
        'scheduled_depart_s': sorted({float(r['depart']) for r in rows}),
        'by_route': dict(Counter(r['route'] for r in rows)),
        'by_type': dict(Counter(r['type'] for r in rows)),
        'by_lane': dict(Counter(r['native_lane'] for r in rows)),
        'numeric_10_candidate_by_lane': dict(Counter(r['native_lane'] for r in rows if r['revised'])),
        'vtypes': types, 'all_native_lanes': lanes,
        'all_initial_geometry_and_permissions_checked': True,
        'max_depart_delay': 'Not set in config; installed runtime default not independently verified; no discard guarantee',
        'noninitial_count': len(root.findall('vehicle')) - len(rows),
    }
    return rows, aggregate


def observe_initial(path, ids):
    """100ms first/last observation proxy, never exact insertion time."""
    seen = {}; at120 = []; last_time = None
    for _, step in ET.iterparse(path, events=('end',)):
        if step.tag != 'timestep': continue
        time = float(step.get('time')); last_time = time
        for v in step.findall('vehicle'):
            ident = v.get('id')
            if ident not in ids: continue
            if ident not in seen:
                seen[ident] = {'first_FCD_s': time, 'first_speed_mps': float(v.get('speed')), 'first_lane': v.get('lane')}
            seen[ident]['last_FCD_s'] = time
            if time == 120: at120.append(ident)
        step.clear()
    first = [v['first_FCD_s'] for v in seen.values()]
    return {'last_FCD_s': last_time, 'initial_observed': len(seen),
            'initial_not_observed': sorted(ids - seen.keys()),
            'first_observation_range_s': [min(first), max(first)] if first else None,
            'first_after_0_count': sum(t > 0 for t in first),
            'first_at_or_after_120_count': sum(t >= 120 for t in first),
            'global_initial_present_at_120': len(at120),
            'identities_pending': 'Unknown; absence in FCD is not evidence of pending or discard',
            'timing_semantics': 'first FCD is 100ms observation proxy; exact insertion/departDelay unavailable'}, seen


class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)


def semantics(docroot):
    records = []
    for name, url in DOC_URLS.items():
        path = docroot / name
        raw = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            parser = Text(); parser.feed(raw); raw = ' '.join(parser.parts)
        text = ' '.join(raw.split())
        terms = ['maxDepartSpeed', 'desiredMaxSpeed', 'insertionChecks'] if 'definitions' in name else ['insertion queue', '--eager-insert']
        excerpts = {}
        for term in terms:
            start = text.find(term)
            if start < 0: raise ValueError('official_doc_term_absent:' + term)
            excerpts[term] = text[max(0, start-60):start+1100]
        records.append({'file': name, 'url': url, 'sha256': sha(path), 'size_bytes': path.stat().st_size,
                        'local_capture_mtime_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                        'prior_integrity_baseline': 'Unknown; first capture, mtime is not server publication time', 'excerpts': excerpts})
    return {'sources': records, 'current_and_v1_26_0_agree_on_depart_max': True,
            'runtime_version_source': '1.26.0 in failed FCD header; no SUMO process started here',
            'formula': 'min(laneSpeedLimit * speedFactor, desiredMaxSpeed * speedFactor, vType.maxSpeed)',
            'desiredMaxSpeed_default': '2778 m/s for passenger per both docs; runtime default not dynamically queried',
            'meaning': 'Use maxDepartSpeed when possible; may lower for leader/intersection. All safety checks retained; insertion may still be delayed.',
            'propagation': 'Default per-edge insertion scheduling can delay later vehicles after one failed insertion. No guarantee unchanged insertion queue, initial state or random trajectory.'}


def prepare():
    out = ROOT / LOCAL
    if (out / 'prepared_inputs').exists(): raise FileExistsError('candidate_exists_use_verify')
    proposal_path = ROOT / PREFLIGHT / 'review_ready_plan.json'
    old = json.loads(proposal_path.read_text(encoding='utf-8'))
    c6_path = ROOT / 'evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/provenance.json'
    c6 = json.loads(c6_path.read_text(encoding='utf-8'))
    rawsha_path = ROOT / OLD / 'raw_artifact_sha256.json'
    rawsha = json.loads(rawsha_path.read_text(encoding='utf-8'))
    old_prov_path = ROOT / OLD / 'provenance.json'
    old_prov = json.loads(old_prov_path.read_text(encoding='utf-8'))
    inputs = {}
    for run in old['runs']:
        for name, digest in run['prepared_input_sha256'].items(): inputs[(PREPARED / run['id'] / name).as_posix()] = digest
    baseline_fcd = [n for n in c6['inputs'] if n.endswith('/fcd.xml')]
    inputs.update({n: c6['inputs'][n]['sha256'] for n in baseline_fcd})
    failed_fcd = 'code/outputs/formal/calibration/stage_0_5_interaction_diagnostics_v1/ID1_SUPPLY_0750/fcd.xml'
    inputs[failed_fcd] = rawsha['ID1_SUPPLY_0750/fcd.xml']['sha256']
    preserved = {proposal_path.relative_to(ROOT).as_posix(): '0f0d84aec6881c957d10331a96dfd22c809980e53f8726af72599a27d2219f97'}
    # The immutable plan digest is checked against its existing freeze, avoiding transcription as authority.
    freeze_path = ROOT / OLD / 'execution_freeze.json'
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    preserved['docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md'] = freeze['plan_sha256']
    sources = sorted(set(old_prov['source_sha256']) | {
        Path(__file__).relative_to(ROOT).as_posix(), 'code/scripts/export_depart_speed_candidate_evidence.py',
        'code/tests/test_depart_speed_candidate.py', PLAN})
    read_paths = [ROOT / p for p in inputs] + [ROOT / p for p in sources] + [ROOT / p for p in preserved]
    read_paths += [c6_path, rawsha_path, old_prov_path, freeze_path]
    binary = Path(old_prov['sumo_binary_path'])
    read_paths += [binary] + [out / 'official_docs' / n for n in DOC_URLS]
    boundary = Boundary(read_paths, [Path(sys.base_prefix) / 'Lib', Path(sys.base_prefix) / 'DLLs'], out, commands=())
    sys.dont_write_bytecode = True
    sys.addaudithook(boundary.audit)
    try:
        for path, digest in {**inputs, **preserved, **old_prov['source_sha256']}.items():
            if sha(ROOT / path) != digest: raise ValueError('baseline_hash_mismatch:' + path)
        if sha(binary) != old_prov['sumo_binary_sha256']: raise ValueError('SUMO_binary_drift')
        (out / 'prepared_inputs').mkdir()
        portable = out / 'portable'; portable.mkdir()
        docs = semantics(out / 'official_docs'); write(portable / 'official_semantics.json', docs)
        summaries = {}; all_rows = {}; runs = []
        for parent in PARENTS:
            base = ROOT / PREPARED / parent
            data = (base / 'routes.rou.xml').read_bytes()
            rows, aggregate = vehicle_audit(data, (base / 'network.net.xml').read_bytes())
            all_rows[parent] = rows; summaries[parent] = aggregate
            if parent == 'ID2_SUPPLY_0805': continue
            revised, changed = revise_routes(data)
            if len(changed) != 38: raise ValueError('unexpected_target_count')
            ident = parent + '_DS10MAX_V1'
            target = out / 'prepared_inputs' / ident; target.mkdir()
            for name in ['network.net.xml', 'run.sumocfg']: (target / name).write_bytes((base / name).read_bytes())
            (target / 'routes.rou.xml').write_bytes(revised)
            runs.append({'id': ident, 'parent_id': parent, 'proposed_cumulative_attempt': len(runs)+2,
                         'seed': 20261201, 'duration_s': 420, 'evaluation_elapsed_s': [120,390],
                         'supply_pulse_s': [180,240] if parent.startswith('ID1') else None,
                         'supply_mps': [10,5,10] if parent.startswith('ID1') else [10],
                         'ramp': 'original 60 vehicle repeated 20–25s pulse' if parent.startswith('ID3') else 'unchanged original schedule',
                         'changed_initial_vehicle_count': len(changed), 'attempt_status': 'not_attempted',
                         'inputs': {(LOCAL / 'prepared_inputs' / ident / n).as_posix(): sha(target / n)
                                    for n in ['network.net.xml','routes.rou.xml','run.sumocfg']}})
        # Pairwise semantic comparison: only the already-approved 60 ramp departures differ.
        a, b = [xml((ROOT / PREPARED / p / 'routes.rou.xml').read_bytes()) for p in (PARENTS[0], PARENTS[2])]
        av, bv = [{v.get('id'): dict(v.attrib) for v in r.findall('vehicle')} for r in (a,b)]
        if av.keys() != bv.keys(): raise ValueError('pair_vehicle_identity_drift')
        differences = []
        for ident, attrs in av.items():
            other = bv[ident]; keys = {k for k in attrs.keys() | other.keys() if attrs.get(k) != other.get(k)}
            if keys:
                if keys != {'depart'} or attrs.get('route') != 'entering' or ident.startswith('i'):
                    raise ValueError('pair_unapproved_difference')
                differences.append(ident)
        if len(differences) != 60: raise ValueError('pair_ramp_count')
        observation = {}
        for path in baseline_fcd + [failed_fcd]:
            parent = PARENTS[1] if '0805_0820' in path else PARENTS[0]
            ids = {r['id'] for r in all_rows[parent]}
            summary, individual = observe_initial(ROOT / path, ids)
            summary['groups'] = {}
            for changed in (True, False):
                members = [r['id'] for r in all_rows[parent] if r['revised'] == changed]
                observed = [individual[i] for i in members if i in individual]
                summary['groups']['numeric10' if changed else 'other_numeric'] = {
                    'declared_count': len(members), 'observed_count': len(observed),
                    'not_observed': [i for i in members if i not in individual],
                    'first_observation_range_s': [min(o['first_FCD_s'] for o in observed), max(o['first_FCD_s'] for o in observed)] if observed else None,
                    'first_speed_range_mps': [min(o['first_speed_mps'] for o in observed), max(o['first_speed_mps'] for o in observed)] if observed else None}
            observation[path] = summary
            write(out / ('initial_observations_' + ('failed' if path == failed_fcd else parent) + '.json'), individual)
        write(out / 'initial_vehicle_audit.json', all_rows)
        summary = {'status': 'Proposed / Awaiting Researcher Decision', 'candidate_policy': 'initial_numeric_10_only_to_max',
                   'input_audits': summaries, 'historical_observations': observation,
                   'pair_only_existing_ramp_depart_differences': len(differences),
                   'all_noninitial_inputs_unchanged_relative_to_each_parent': True,
                   'unchanged_initial_0750_count': 79,
                   'remaining_initial_conflict': 'i0007_i0007 speed15.23 and other non-10 initial inputs retained; t0 warning not fixed or hidden',
                   'scope_conflict_status': 'Awaiting Researcher Decision: confirm 38-only candidate or separately authorize all117; no automatic expansion',
                   'counterfactual_limits': 'Historical baseline has different initialization policy. Pair shares declared initial input, not guaranteed realized initial state; supply and ramp both differ. No matched new initialization-only control.',
                   'new_insertion_speeds_delays_and_common_support': 'Unknown; no new simulation',
                   'new_trajectory_attempts_this_preparation': 0, 'cumulative_attempts': 1, 'remaining': 2,
                   'isolation_status': 'Not Accepted; existing incident preserved', 'Gate_changed': False}
        write(portable / 'impact_summary.json', summary)
        proposal = {'schema': 'aad.depart-speed-candidate.v1', 'task_id': 'AAD-0.5-INTERACTION-DIAGNOSTICS-V1',
                    'status': 'Proposed / Awaiting exact researcher confirmation', 'execution_allowed': False,
                    'researcher_confirmed': False, 'protocol_frozen': False,
                    'plan_path': PLAN, 'plan_sha256': sha(ROOT / PLAN),
                    'policy': 'initial_numeric_10_only_to_max', 'runs': runs,
                    'impact_summary_sha256': sha(portable / 'impact_summary.json'),
                    'official_semantics_sha256': sha(portable / 'official_semantics.json'),
                    'local_initial_audit_sha256': sha(out / 'initial_vehicle_audit.json'),
                    'budget': {'cap': 3, 'already_spent': 1, 'failed_attempt_retained': 'ID1_SUPPLY_0750',
                               'remaining': 2, 'ID2_SUPPLY_0805': 'deferred_not_reallocated_as_extra_budget'},
                    'spatial_support': {'lanes': [1,2,3,4,5], 'offset100_m': [[150,250],[250,350]], 'required_cells': 18},
                    'phases_s': [[120,180],[180,240],[240,300],[300,360],[360,390]],
                    'risk_definition_changed': False, 'Gate_changed': False, 'isolation_status': 'Not Accepted',
                    'source_sha256': {p: sha(ROOT / p) for p in sources},
                    'preserved_sha256': preserved, 'approved_input_sha256': inputs,
                    'sumo_binary': {'path': str(binary), 'sha256': sha(binary), 'launched': False},
                    'prior_tool_dependency_binding': {'proposal_path': proposal_path.relative_to(ROOT).as_posix(),
                                                      'sha256': sha(proposal_path), 'current_tools_other_than_binary': 'Not rechecked; must recheck exact prior allowlist before launch'},
                    'preparation_has_no_launch_API': True,
                    'future_execution': 'Old supervisor intentionally blocks after failed attempt. No reset/ledger mutation. Any new cumulative-budget adapter/source change needs new exact hash binding and researcher confirmation before launch.',
                    'post_run_stop_checks': ['input imposition', 'actual initialization including pending identity', 'D1 eligibility', 'all18 common cells', 'resource and isolation evidence'],
                    'no_retry_seed_window_threshold_budget_change': True}
        write(portable / 'review_proposal.json', proposal)
        (portable / 'PROPOSAL_SHA256').write_bytes((sha(portable / 'review_proposal.json') + '\n').encode())
        write(portable / 'provenance.json', {'git_baseline_sha': 'a9b1bcf3da2669c938094df8435ed65ff27287f6',
               'state': 'new uncommitted candidate files bound by SHA; commit alone not full input version',
               'command': 'python -I -S code/scripts/prepare_stage_0_5_depart_speed_candidate.py prepare',
               'python': sys.version, 'read_input_sha256': inputs,
               'local_initial_audit_sha256': sha(out / 'initial_vehicle_audit.json'),
               'SUMO_processes': 0, 'no_P2_computation_or_result_selection': True,
               'official_downloads': '4 named public official sources; complete HTML retained locally only',
               'scope': 'Python file/process audit; not OS/native full access tracing; prior incident Not Accepted'})
    finally:
        boundary.save(out / 'preparation_boundary_audit.json')
    if boundary.denied or boundary.launched: raise ValueError('offline_boundary_failure')
    write(out / 'portable/boundary_summary.json', {'denied': boundary.denied, 'processes_launched': boundary.launched,
          'opened_paths_count': len(boundary.opened), 'full_local_audit_sha256': sha(out / 'preparation_boundary_audit.json'),
          'scope': 'exact named inputs, code, official docs; stdlib runtime; task write root only',
          'isolation_incident': 'Not Accepted; no full-system zero-access claim'})
    print(json.dumps({'prepared': True, 'proposal_sha256': sha(out / 'portable/review_proposal.json'), 'SUMO_processes': 0}))


def verify(root, local=None):
    portable = root / 'evidence/results' / RESULT
    for line in (portable / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        if Path(name).name != name or sha(portable / name) != digest: raise ValueError('portable_digest:' + name)
    p = json.loads((portable / 'review_proposal.json').read_text(encoding='utf-8'))
    if sha(portable / 'review_proposal.json') != (portable / 'PROPOSAL_SHA256').read_text().strip(): raise ValueError('proposal_digest')
    if p['execution_allowed'] or p['researcher_confirmed'] or p['budget']['already_spent'] != 1: raise ValueError('authorization_or_budget')
    if sha(root / p['plan_path']) != p['plan_sha256']: raise ValueError('plan_digest')
    for field, name in [('impact_summary_sha256', 'impact_summary.json'), ('official_semantics_sha256', 'official_semantics.json')]:
        if sha(portable / name) != p[field]: raise ValueError('proposal_evidence_digest:' + name)
    for name, digest in {**p['source_sha256'], **p['preserved_sha256']}.items():
        if sha(root / name) != digest: raise ValueError('source_digest:' + name)
    if local:
        for name, digest in p['approved_input_sha256'].items():
            if sha(root / name) != digest: raise ValueError('input_drift:' + name)
        if sha(Path(p['sumo_binary']['path'])) != p['sumo_binary']['sha256']: raise ValueError('binary_drift')
        for run in p['runs']:
            for name, digest in run['inputs'].items():
                if sha(root / name) != digest: raise ValueError('candidate_input_drift:' + name)
            target = root / LOCAL / 'prepared_inputs' / run['id']
            base = root / PREPARED / run['parent_id']
            changed = confirm_revision((base / 'routes.rou.xml').read_bytes(), (target / 'routes.rou.xml').read_bytes())
            if len(changed) != 38: raise ValueError('edit_count')
            for name in ['network.net.xml','run.sumocfg']:
                if (base / name).read_bytes() != (target / name).read_bytes(): raise ValueError('unapproved_config_edit')
        docs = json.loads((portable / 'official_semantics.json').read_text(encoding='utf-8'))
        for item in docs['sources']:
            if sha(root / LOCAL / 'official_docs' / item['file']) != item['sha256']: raise ValueError('doc_digest')
        if sha(root / LOCAL / 'initial_vehicle_audit.json') != json.loads((portable / 'provenance.json').read_text(encoding='utf-8'))['local_initial_audit_sha256']:
            raise ValueError('initial_audit_digest')
    return {'portable_source_and_plan': 'verified', 'local_inputs': 'verified' if local else 'not_available_not_claimed',
            'attempts': 1, 'remaining': 2, 'candidate_not_approved': True, 'SUMO_started': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare','verify'])
    parser.add_argument('--local', action='store_true'); args = parser.parse_args()
    if args.mode == 'prepare': prepare()
    else: print(json.dumps(verify(ROOT, ROOT / LOCAL if args.local else None)))
