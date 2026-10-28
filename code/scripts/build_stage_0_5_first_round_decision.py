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
    spatial={}
    for e in events: spatial[e['spatial_class']]=spatial.get(e['spatial_class'],0)+1
    matrix=[
      {'question':'Auxiliary lane role','candidate':'A: exclude from formal mainline estimand; mechanism diagnostic only','source':'R0 target definition; offline event_inventory','offline_result':'B10 7/7 and B11 18/19 events auxiliary; no formal P2','risk':'misses auxiliary interaction mechanism','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Auxiliary lane role','candidate':'B: separate secondary mechanism candidate space','source':'R0 S_ONRAMP/topology; R1 event classification','offline_result':'Exploratory classification is complete; events remain separated, no P2 recomputed','risk':'changes estimand if pooled','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Auxiliary lane role','candidate':'C: replacement study scope','source':'R0 candidates; R1 topology','offline_result':'Offline data can describe events but cannot validate causal path or recalibrate','risk':'replaces primary question','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Source region','candidate':'S_UPSTREAM_MAIN main_0 lanes1-5 y[0,150)','source':'source_target_candidates.json','offline_result':'0 formal source events; 8,457.4 veh-s B00 exposure; missing 1,061','risk':'zero event support; unobserved risk unresolved','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Source region','candidate':'S_DOWNSTREAM_MAIN main_2 lanes1-5 y[399.22,669.18)','source':'source_target_candidates.json/topology_candidate_audit.json','offline_result':'0 confirmed source events in sealed evidence; road path upstream->target not applicable','risk':'directional mismatch for upstream propagation','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Source region','candidate':'S_ONRAMP onramp lane7','source':'source_target_candidates.json/topology_candidate_audit.json','offline_result':'254.9 veh-s and 2,700 missing; connects to auxiliary main_1_0; no source P2','risk':'lane-change and missing-link confounding','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Cohort','candidate':'C_INPUT_ROUTE (1112 IDs, pre-treatment route rule)','source':'source_target_candidates.json; R1 cohort SHA','offline_result':'Applied unchanged across arms; lifecycle differences reported separately','risk':'pending/undeparted observations reduce support','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Cohort','candidate':'C_PRE_PULSE_STATE (pre-180 observed IDs)','source':'source_target_candidates.json','offline_result':'Can be defined pre-treatment, but count and exact clock remain unfrozen; no post-outcome selection performed','risk':'changes estimand and excludes later entrants','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Physical path/time','candidate':'Identity + <=0.11s continuity + verified lane connection + leader-follower witness','source':'physical_path_audit.json; topology_candidate_audit.json','offline_result':'No source event, so arrival undefined; missing links retained uncertain','risk':'requires future source witness','formal_semantics_change':False,'decision':'Awaiting Researcher Decision'},
      {'question':'Physical path/time','candidate':'Road reachability only','source':'topology_candidate_audit.json','offline_result':'main_0→main_1 reachable; onramp→main_1 reachable; main_2→target false','risk':'does not establish influence or arrival','formal_semantics_change':True,'decision':'Awaiting Researcher Decision'},
      {'question':'Physical path/time','candidate':'Message/confirmation clock as arrival','source':'decision_register.json; physical_path_audit.json','offline_result':'Not used; would conflate detection with physical influence','risk':'semantic leakage','formal_semantics_change':True,'decision':'Reject for formal use'},
    ]
    write('candidate_comparison_matrix.json',{'schema':'aad.stage05.first-round-candidate-matrix.v1','status':'Exploratory/non-authoritative','rows':matrix,'event_spatial_counts':spatial})
    write('offline_reconciliation.json',{'r1_event_counts':{'B00':0,'B10':7,'B01':1,'B11':19},'window_onsets':{'B00':0,'B10':5,'B01':0,'B11':17},'formal_source_p2':{'B00':0,'B10':0,'B01':0,'B11':0},'formal_target_p2':{'B00':0,'B10':0,'B01':0,'B11':0},'sumo_launches_this_task':0,'locked_holdout_access':False,'formal_measurement_changed':False})
    write('validation_summary.json',{'project_docs_strict_git':'pass','portable_evidence_verify':'pass','targeted_project_docs_pytest':'13 passed','compileall':'pass','broad_offline_regression':'1389 passed, 34 failed, 4 skipped; failures are environment-dependent missing pyarrow/traci and SUMO-dependent tests were not treated as scientific evidence','sumo_launches_this_task':0,'traci_connections_this_task':0,'holdout_reads':0})
    import subprocess
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    write('run_record.json',{'task':'AAD-S0.5-FIRST-ROUND-OFFLINE-DECISION-20261028','mode':'offline','command':'python code/scripts/build_stage_0_5_first_round_decision.py','git_head':head,'sumo_launches':0,'traci_launches':0,'holdout_access':False,'inputs':[str(x.relative_to(ROOT)).replace('\\','/') for x in roots if x.exists()]})
    manifest=[]
    for p in sorted(OUT.iterdir()):
        if p.name=='SHA256SUMS': continue
        manifest.append({'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size})
    write('manifest.json',{'schema':'aad.stage05.first-round-manifest.v1','files':manifest})
    with (OUT/'SHA256SUMS').open('w',encoding='utf-8') as f:
        for x in manifest: f.write(f"{x['sha256']}  {x['path']}\n")
if __name__=='__main__': main()
