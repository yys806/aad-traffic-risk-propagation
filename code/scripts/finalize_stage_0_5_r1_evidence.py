"""Finalize the portable R1 evidence index, acceptance, R2 review and report inputs."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

RESULT = "RES-STAGE-0.5-R1-DIAGNOSTICS-20261028"
ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "evidence/results" / RESULT
RAW = ROOT / "code/outputs/formal/calibration/stage_0_5_r1_diagnostics_20261028"

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    # Restore the accepted B00 lifecycle facts into the same reporting shape.
    b00p=EVID/'B00_unified_analysis/measurement_result.json'
    b00=json.loads(b00p.read_text(encoding='utf8'))
    pop=json.loads((ROOT/'evidence/results/RES-AAD-WEEK-20261027-V1/population_accounting.json').read_text(encoding='utf8'))
    b00['lifecycle']={
        'declared':pop['evidence']['status_by_vehicle_count'], 'inserted':pop['evidence']['actual_inserted'],
        'pending':pop['evidence']['pending'], 'discarded':pop['evidence']['explicit_discarded'],
        'active':pop['evidence']['active'], 'arrived':pop['evidence']['arrived'],
        'cohort_count':1112, 'cohort_initial_count':79,
        'cohort_sha256':'76db89e2ff2d9df997516b59a23bc4d88a85c7a0161dca6a222f2a8bfee277f8',
        'source':'evidence/results/RES-AAD-WEEK-20261027-V1/population_accounting.json',
        'acceptance':'B00_EXECUTED_MEASUREMENT_ACCEPTED; no R1 relaunch'}
    b00p.write_text(json.dumps(b00,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
    arms={}
    for arm in ['B10','B01','B11']:
        p=EVID/arm/'measurement_result.json'; d=json.loads(p.read_text(encoding='utf8'))
        d['raw_output_root']=str((RAW/arm).relative_to(ROOT)).replace('\\','/')
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
        arms[arm]=d
    arms['B00']=b00
    # Portable acceptance records separate engineering receipt from scientific
    # measurement; a zero-event arm is still complete and retained.
    for arm in ['B10','B01','B11']:
        d=arms[arm]
        acc=dict(schema='aad.r1.measurement-acceptance.v1', task_id='AAD-S0.5-R1-EXECUTE-20261028', arm=arm,
                 engineering_receipt='Pass', native_execution_complete=True, full_context_fcd=True,
                 summary_tripinfo_complete=True, identity_lifecycle_complete=bool(d['lifecycle']['identity_accounting_complete']),
                 collision_teleport_observation_complete=bool(d['lifecycle']['collision_coverage_complete']),
                 control_readback_complete=bool(d['execution']['controls']['controls_pass']),
                 measurement_contract='stage-0.5-d1-local-v1', measurement_complete=True,
                 source_P2_events=d['source_event_measurement']['onset_events'], target_P2_events=d['target_measurement']['P2_events'],
                 target_D1_E_veh_s=d['target_measurement']['D1_E_veh_s'], reliable_target_D1_E_veh_s=d['target_measurement']['reliable_D1_E_veh_s'],
                 unavailable_reasons=d['target_measurement']['measurement_status'], scientific_equivalence_accepted=False,
                 scientific_effect_claim_eligible=False, raw_output_root=d['raw_output_root'])
        write(EVID/arm/'measurement_acceptance.json',acc)
    write(EVID/'measurement_acceptance.json',dict(schema='aad.r1.measurement-acceptance-summary.v1', arms={a:json.loads((EVID/a/'measurement_acceptance.json').read_text()) for a in ['B10','B01','B11']}, B00='accepted prior A03; same contract reference'))
    source=dict(schema='aad.r1.source-event-support.v1', task_id='AAD-S0.5-R1-EXECUTE-20261028',
        rule=dict(ttc_strictly_below_s=2.0, minimum_observed_span_s=.2, maximum_allowed_gap_s=.11, confirmation='first observed qualifying timestamp'),
        region=dict(id='S_UPSTREAM_MAIN', edges=['main_0'], lanes=['1','2','3','4','5'], y_m=[0,150], window_s=[120,390]),
        arms={a:dict(source_P2_events=arms[a]['source_event_measurement']['onset_events'],
                     events=arms[a]['source_event_measurement'].get('events',[]),
                     incomplete_candidates=arms[a]['source_event_measurement'].get('incomplete_candidates',[]),
                     D1_E_veh_s=arms[a]['source_event_measurement']['D1_E_veh_s'],
                     reliable_D1_E_veh_s=arms[a]['source_event_measurement']['reliable_D1_E_veh_s']) for a in ['B00','B10','B01','B11']},
        conclusion='No qualified source P2 event was observed in B10, B01 or B11; B00 A03 also has zero.',
        status='NO_QUALIFIED_SOURCE_EVENT_SUPPORT')
    write(EVID/'source_event_support.json',source)
    path=dict(schema='aad.r1.physical-path-audit.v1', task_id='AAD-S0.5-R1-EXECUTE-20261028',
        rule=['identity continuity','<=0.11 s state continuity','verified native road/lane connection','leader-follower influence edge'],
        arms={a:dict(status=arms[a]['physical_path']['status'], source_event_count=arms[a].get('source_event_measurement',{}).get('onset_events',0),
                     event_specific_physical_arrival_times=arms[a]['physical_path'].get('event_specific_physical_arrival_times'),
                     missing_support_is_uncertain=True) for a in ['B00','B10','B01','B11']},
        conclusion='No event-specific physical arrival time is generated because no source event exists. This is not proof of physical unreachability.')
    write(EVID/'physical_path_audit.json',path)
    comparison={'schema':'aad.r1.arm-comparison.v1','arms':arms,
        'common_design':{'scene':'US-101 0750','seed':20261201,'duration_s':420,'internal_step_s':.05,'recording_step_s':.1,'window_s':[120,390],
                         'cohort':'C_INPUT_ROUTE','cohort_sha256':'76db89e2ff2d9df997516b59a23bc4d88a85c7a0161dca6a222f2a8bfee277f8'},
        'interpretation_boundary':'Observed traffic and exposure differences do not establish an effect; no source event support was obtained.'}
    write(EVID/'arm_comparison.json',comparison)
    r2=dict(schema='aad.r1.r2-gate-review.v1', task_id='AAD-S0.5-R1-EXECUTE-20261028',
        review_layers=['basic_kinematics','following_interaction','risk_observability','formal_P2_and_reliable_exposure','state_and_sample_support'],
        source_event_case='A', source_event_case_definition='B10, B01 and B11 all lack qualified source P2 events',
        arm_status={a:{'starts':1 if a!='B00' else 0,'valid_runs':1 if a!='B00' else 1,
                        'P2_events':arms[a].get('target_measurement',{}).get('P2_events',0),
                        'source_P2_events':arms[a].get('source_event_measurement',{}).get('onset_events',0),
                        'D1_E_veh_s':arms[a].get('target_measurement',{}).get('D1_E_veh_s')} for a in ['B00','B10','B01','B11']},
        conclusions=['All three R1 diagnostic arms completed and produced complete engineering/measurement evidence.',
                     'No qualified source P2 support was observed under the frozen formal rule and S_UPSTREAM_MAIN attribution.',
                     'Missing path support is retained as uncertain; no event-specific physical arrival was fabricated.',
                     'Observed traffic/lifecycle differences are diagnostics, not causal effect evidence.'],
        stage_0_5_gate='blocked', stage_0_6_status='pending_scientific_tolerances_and_dynamic_calibration',
        stage_1_status='blocked_until_protocol_lock', protocol_lock_generated=False,
        stop_rule='Stop after the three one-run arms; no seed/intensity search or additional SUMO run authorized by this task.',
        M3_interaction_incompatibility='Historical M3 evidence remains unchanged; R1 does not resolve the structural interaction-support limitation.')
    write(EVID/'r2_gate_review.json',r2)
    # Portable validation record; exact command results are filled in after the
    # final repository checks below.
    write(EVID/'validation_record.json',dict(schema='aad.r1.validation-record.v1', status='Pending final repository checks',
        native_runs={'B10':1,'B01':1,'B11':1}, correction_runs={'B10':0,'B01':0,'B11':0},
        scientific_repeats={'B10':1,'B01':1,'B11':1}, raw_failures_preserved=True,
        checks=['independent verify_receipt Pass for all three arms','unified offline measurement completed','final docs/tests/hash checks pending']))
    # Hash portable files only; raw outputs are indexed separately and remain in
    # ignored code/outputs for reproducible local remeasurement.
    files=[]
    for p in sorted(EVID.rglob('*')):
        if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'}:
            files.append(str(p.relative_to(EVID)).replace('\\','/'))
    manifest=dict(schema='aad.r1.manifest.v1', result_id=RESULT, task_id='AAD-S0.5-R1-EXECUTE-20261028',
        status='Completed diagnostics / Stage 0.5 Gate blocked', files={n:sha(EVID/n) for n in files},
        raw_output_root=str(RAW.relative_to(ROOT)).replace('\\','/'), raw_output_files={a:{p.name:sha(p) for p in sorted((RAW/a).iterdir()) if p.is_file()} for a in ['B10','B01','B11']},
        baseline_binding='WEEK_0750_B00_IC1_s20261201_A03 reused; no B00 launch',
        source_sha256={n:sha(ROOT/'code/scripts'/n) for n in ['prepare_stage_0_5_r1_execution.py','analyze_stage_0_5_r1.py','finalize_stage_0_5_r1_evidence.py']})
    write(EVID/'manifest.json',manifest)
    sums=[]
    for p in sorted(EVID.rglob('*')):
        if p.is_file() and p.name != 'SHA256SUMS': sums.append(f'{sha(p)}  {p.relative_to(EVID).as_posix()}')
    (EVID/'SHA256SUMS').write_text('\n'.join(sums)+'\n',encoding='utf8')
    print(json.dumps({'files':len(files),'manifest_sha256':sha(EVID/'manifest.json'),'sha256sums_sha256':sha(EVID/'SHA256SUMS')},ensure_ascii=False))

if __name__=='__main__': main()
