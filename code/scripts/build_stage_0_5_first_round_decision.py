from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/results/RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028'
SRC = ROOT / 'evidence/results/RES-STAGE-0.5-OFFLINE-MECHANISM-AUDIT-20261028'
R0 = ROOT / 'evidence/results/RES-STAGE-0.5-R0-DESIGN-PACKET-20261028'
R1 = ROOT / 'evidence/results/RES-STAGE-0.5-R1-DIAGNOSTICS-20261028'
WEEK = ROOT / 'evidence/results/RES-AAD-WEEK-20261027-V1'
SOURCE_DOCS = [
    'docs/STAGE_0_5_R1_EXECUTION_2026-10-28.md',
    'docs/STAGE_0_5_OFFLINE_MECHANISM_AUDIT_2026-10-28.md',
    'docs/plans/2026-10-28-stage-0-5-r0-design-freeze.md',
    'docs/STAGE_0_5_ACCEPTANCE_PROTOCOL_DRAFT.md',
    'docs/STAGE_0_5_FINAL_CLOSURE_2026-10-20.md',
    'docs/STAGE_0_5_CONDITIONAL_STATE_SUPPORT.md',
    'docs/STAGE_0_5_METHOD_EXPANSION_SUMMARY.md',
    'docs/STAGE_0_5_TRAJECTORY_COVERAGE_AND_IDENTIFIABILITY.md',
    'docs/STAGE_0_5_ARRIVAL_TIMING_DIAGNOSTICS.md',
    'docs/STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md',
    'docs/STAGE_0_5_TRAFFIC_STATE_DEFINITION_SENSITIVITY.md',
    'docs/STAGE_0_5_INITIALIZATION_FIDELITY.md',
    'docs/STAGE_0_5_C6_C7_VALIDATION.md',
    'docs/STAGE_0_5_TASK_0_5_4A_CALIBRATION_READINESS.md',
    'docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md',
    'docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md',
    'docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md',
    'code/scripts/analyze_stage_0_5_offline_mechanism.py',
    'code/src/riskprop/stage_0_5_d1_measurement.py',
    'code/src/riskprop/stage_0_5_state_support.py',
    'code/src/riskprop/stage_0_5_scene_reconstruction.py',
    'code/src/riskprop/stage_0_5_sumo.py',
    'code/configs/stage_0_2_formal_risk_measurement_p2_v1.json',
]

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def write(name, obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def verify_sha_bundle(directory):
    sums=directory/'SHA256SUMS'
    if not sums.is_file(): return {'status':'missing_sha256sums','checked':0,'mismatches':[]}
    mismatches=[]; checked=0
    for line in sums.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest, rel=line.split(None,1); rel=rel.strip().lstrip('*'); path=directory/rel
        if not path.is_file(): mismatches.append({'path':rel,'reason':'missing'}); continue
        checked+=1; actual=sha(path)
        if actual!=digest: mismatches.append({'path':rel,'expected':digest,'actual':actual})
    return {'status':'pass' if not mismatches else 'mismatch','checked':checked,'mismatches':mismatches}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    roots=[SRC,R0,R1,WEEK,ROOT/'evidence/admission',ROOT/'docs/audits']
    targets=roots+[ROOT/x for x in SOURCE_DOCS]
    rows=[]
    for root in targets:
        if not root.exists(): continue
        paths=[root] if root.is_file() else root.rglob('*')
        for p in paths:
            if p.is_file():
                status='hashed_and_enumerated'
                if p.suffix.lower()=='.json':
                    try: json.loads(p.read_text(encoding='utf-8-sig')); status='parsed_json_and_hashed'
                    except Exception as exc: status=f'json_parse_failed:{type(exc).__name__}'
                elif p.suffix.lower() in {'.csv','.tsv'}:
                    try:
                        with p.open(newline='',encoding='utf-8-sig') as handle: sum(1 for _ in csv.reader(handle))
                        status='parsed_delimited_and_hashed'
                    except Exception as exc: status=f'delimited_parse_failed:{type(exc).__name__}'
                rows.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'type':p.suffix.lower() or 'no_extension','bytes':p.stat().st_size,'sha256':sha(p),'read_status':status})
    with (OUT/'file_audit.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(sorted(rows,key=lambda x:x['path']))
    events=[]
    with (SRC/'event_inventory.csv').open(encoding='utf-8') as f: events=list(csv.DictReader(f))
    reconciliation=json.loads((SRC/'count_reconciliation.json').read_text(encoding='utf-8'))
    arm_comparison=json.loads((R1/'arm_comparison.json').read_text(encoding='utf-8'))
    arms=('B00','B10','B01','B11')
    by_arm={arm:[e for e in events if e['arm']==arm] for arm in arms}
    spatial={}
    for e in events: spatial[e['spatial_class']]=spatial.get(e['spatial_class'],0)+1
    per_arm={}
    for arm in arms:
        rows=by_arm[arm]
        window=[e for e in rows if e['onset_in_window'].lower()=='true']
        full_spatial=dict(sorted(__import__('collections').Counter(e['spatial_class'] for e in rows).items()))
        window_spatial=dict(sorted(__import__('collections').Counter(e['spatial_class'] for e in window).items()))
        rec=reconciliation['arms'][arm]
        expected_full=int(rec.get('existing_event_array_length',rec.get('recomputed_event_array_length',0)))
        expected_window=int(rec.get('existing_window_onsets',rec.get('recomputed_window_onsets',0)))
        assert len(rows)==expected_full, (arm,len(rows),expected_full)
        assert len(window)==expected_window, (arm,len(window),expected_window)
        assert int(rec.get('recomputed_event_array_length',len(rows)))==len(rows)
        assert int(rec.get('recomputed_window_onsets',len(window)))==len(window)
        per_arm[arm]={'full_event_count':len(rows),'window_onset_count':len(window),'full_spatial_counts':full_spatial,'window_spatial_counts':window_spatial,'formal_source_p2':int(rec.get('existing_source_p2',0)),'formal_target_p2':int(rec.get('existing_target_p2',0)),'target_D1_E_veh_s':arm_comparison['arms'][arm].get('target_D1_E_veh_s')}
    assert sum(x['full_event_count'] for x in per_arm.values())==len(events)==27
    assert sum(spatial.values())==len(events)
    assert per_arm['B10']['full_spatial_counts'].get('auxiliary_or_unmapped_lane',0)==7
    assert per_arm['B11']['full_spatial_counts'].get('auxiliary_or_unmapped_lane',0)==16
    assert per_arm['B11']['window_spatial_counts'].get('auxiliary_or_unmapped_lane',0)==16
    source_integrity={str(d.relative_to(ROOT)).replace('\\','/'):verify_sha_bundle(d) for d in (SRC,R0,R1,WEEK)}
    assert all(v['status']=='pass' for v in source_integrity.values()), source_integrity
    matrix=[
      {'question':'Auxiliary lane role','candidate':'A: exclude from formal mainline estimand; mechanism diagnostic only','source':'R0 target definition; offline event_inventory','offline_result':f"B10 {per_arm['B10']['full_spatial_counts'].get('auxiliary_or_unmapped_lane',0)}/{per_arm['B10']['full_event_count']} full events auxiliary ({per_arm['B10']['window_spatial_counts'].get('auxiliary_or_unmapped_lane',0)} window onsets); B11 {per_arm['B11']['full_spatial_counts'].get('auxiliary_or_unmapped_lane',0)}/{per_arm['B11']['full_event_count']} full events auxiliary ({per_arm['B11']['window_spatial_counts'].get('auxiliary_or_unmapped_lane',0)} window onsets); no formal P2",'risk':'misses auxiliary interaction mechanism','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Auxiliary lane role','candidate':'B: separate secondary mechanism candidate space','source':'R0 S_ONRAMP/topology; R1 event classification','offline_result':'Exploratory classification is complete; events remain separated, no P2 recomputed','risk':'changes estimand if pooled','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Auxiliary lane role','candidate':'C: replacement study scope','source':'R0 candidates; R1 topology','offline_result':'Offline data can describe events but cannot validate causal path or recalibrate','risk':'replaces primary question','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Source region','candidate':'S_UPSTREAM_MAIN main_0 lanes1-5 y[0,150)','source':'source_target_candidates.json','offline_result':'0 formal source events; 8,457.4 veh-s B00 exposure; missing 1,061','risk':'zero event support; unobserved risk unresolved','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Source region','candidate':'S_DOWNSTREAM_MAIN main_2 lanes1-5 y[399.22,669.18)','source':'source_target_candidates.json/topology_candidate_audit.json','offline_result':'0 confirmed source events in sealed evidence; road path upstream->target not applicable','risk':'directional mismatch for upstream propagation','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Source region','candidate':'S_ONRAMP onramp lane7','source':'source_target_candidates.json/topology_candidate_audit.json','offline_result':'254.9 veh-s and 2,700 missing; connects to auxiliary main_1_0; no source P2','risk':'lane-change and missing-link confounding','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Cohort','candidate':'C_INPUT_ROUTE (1112 IDs, pre-treatment route rule)','source':'source_target_candidates.json; R1 cohort SHA','offline_result':'Applied unchanged across arms; lifecycle differences reported separately','risk':'pending/undeparted observations reduce support','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Cohort','candidate':'C_PRE_PULSE_STATE (pre-180 observed IDs)','source':'source_target_candidates.json; sealed measured_state.parquet paths','offline_result':'Count/support Uncomputed: the portable package has no pre-pulse ID list, raw row-level parquet reading requires unavailable pyarrow, and exact clock/region are scientifically unfrozen; this is not zero support and no post-outcome selection was performed','risk':'changes estimand and excludes later entrants','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Physical path/time','candidate':'Identity + <=0.11s continuity + verified lane connection + leader-follower witness','source':'physical_path_audit.json; topology_candidate_audit.json','offline_result':'No source event, so arrival undefined; missing links retained uncertain','risk':'requires future source witness','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Physical path/time','candidate':'Road reachability only','source':'topology_candidate_audit.json','offline_result':'main_0→main_1 reachable; onramp→main_1 reachable; main_2→target false','risk':'does not establish influence or arrival','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Physical path/time','candidate':'Message/confirmation clock as arrival','source':'decision_register.json; physical_path_audit.json','offline_result':'Not used; would conflate detection with physical influence','risk':'semantic leakage','formal_semantics_change':True,'decision':'Reject for formal use'},
    ]
    write('candidate_comparison_matrix.json',{'schema':'aad.stage05.first-round-candidate-matrix.v2','status':'Exploratory/non-authoritative','rows':matrix,'event_spatial_counts':spatial,'event_counts_by_arm':per_arm})
    write('offline_reconciliation.json',{'schema':'aad.stage05.first-round-offline-reconciliation.v2','r1_event_counts':{a:per_arm[a]['full_event_count'] for a in arms},'window_onsets':{a:per_arm[a]['window_onset_count'] for a in arms},'formal_source_p2':{a:per_arm[a]['formal_source_p2'] for a in arms},'formal_target_p2':{a:per_arm[a]['formal_target_p2'] for a in arms},'target_D1_E_veh_s':{a:per_arm[a]['target_D1_E_veh_s'] for a in arms},'event_inventory_rows':len(events),'event_spatial_counts':spatial,'source_count_reconciliation_assertions':'passed','source_manifest_sha256_verification':source_integrity,'formal_measurement_source':'evidence/results/RES-STAGE-0.5-OFFLINE-MECHANISM-AUDIT-20261028/count_reconciliation.json and evidence/results/RES-STAGE-0.5-R1-DIAGNOSTICS-20261028/arm_comparison.json','sumo_launches_this_task':0,'locked_holdout_access':False,'formal_measurement_changed':False})
    validation_path=OUT/'validation_summary.json'
    if not validation_path.exists():
        write('validation_summary.json',{'schema':'aad.stage05.first-round-validation-summary.v2','status':'pending_final_validation','event_source_assertions':'pass','manifest_self_reference':False,'sha_self_reference':False,'broad_offline_regression':'recorded in test_failure_inventory.json and pytest_broad_offline.log','sumo_launches_this_task':0,'traci_connections_this_task':0,'holdout_reads':0})
    import subprocess
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    write('run_record.json',{'task':'AAD-S0.5-FIRST-ROUND-OFFLINE-DECISION-20261028','mode':'offline','command':'python code/scripts/build_stage_0_5_first_round_decision.py','git_head':head,'sumo_launches':0,'traci_launches':0,'holdout_access':False,'inputs':[str(x.relative_to(ROOT)).replace('\\','/') for x in roots if x.exists()]})
    manifest=[]
    for p in sorted(OUT.iterdir()):
        if p.name in {'manifest.json','SHA256SUMS','validation_summary.json'}: continue
        manifest.append({'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size})
    write('manifest.json',{'schema':'aad.stage05.first-round-manifest.v2','self_reference':False,'excluded_auxiliary_files':['validation_summary.json'],'files':manifest})
    sha_entries=list(manifest)+[{'path':'manifest.json','sha256':sha(OUT/'manifest.json'),'bytes':(OUT/'manifest.json').stat().st_size}]
    with (OUT/'SHA256SUMS').open('w',encoding='utf-8') as f:
        for x in sha_entries: f.write(f"{x['sha256']}  {x['path']}\n")
if __name__=='__main__': main()
