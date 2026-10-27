"""Build a traceable proposal and recompute real gates; never invent approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from riskprop.protocol_lock import REQUIRED_FROZEN_FIELDS,ProtocolLockError,protocol_lock_readiness,write_protocol_lock


def threshold_proposals(budget):
    required={'numerical_errors','timestep_errors','analyzer_errors','reconstruction_errors'}
    if set(budget['group_bounds'])!=required or not all(
            isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0
            for v in budget['group_bounds'].values()):
        raise ValueError('four finite nonnegative error-source bounds required')
    joint=sum(budget['group_bounds'].values())
    return dict(status='Proposed; no scientific approval inferred',
        metric='dimensionless formal exponential-rho mean; not P2 events/veh-h',
        preferred=dict(delta_eq_per_arm_fixture=joint,delta_eq_paired_fixture=2*joint,
            delta_eq_four_arm_fixture=4*joint,delta_R=.05,delta_plan=.10,h=.0125),
        alternative=dict(delta_R=.10,delta_plan=.20,h=.025,
            meaning='10 percentage points on the full [0,1] proxy scale; less sensitive scientific target, not a repair if preferred fails'),
        basis='Four source higher99% fixture quantiles summed conservatively; triangle bound for arm contrasts. SESOI5 percentage points is an explicit value judgment, not inferred from tests or real-world accident risk.',
        adoption_conditions=['Endpoint/cohort/window and actual dynamic error budget approved',
            'No extrapolation beyond stated smooth/gap/closing/precision fixture domain',
            'Do not raise delta_R automatically if measured total error reaches it'],
        B=dict(value=None,status='Unknown',definition='Independent simulator-to-world systematic bias bound for the chosen causal contrast; neither numerical tolerance nor confidence interval',
            implication='No physical-world effect claim without independent evidence or explicitly restricted simulator-only estimand'),
        planning=dict(alpha_one_sided=.025,power=.90,minimum_confirmatory_pairs=100,
            h_rule='min(0.25*delta_R,0.5*(delta_plan-delta_R))',
            paired_variance=None,confirmatory_sample_size=None,
            formula='existing paired_confirmatory_sample_size; max(100,n_power,n_precision); one baseline seed and deterministic repeats do not estimate paired treatment variance',
            calibration_seed_proposal=list(range(20261201,20261221)),
            confirmatory_seed_rule='Freeze a disjoint sequence before confirmatory access; independent of calibration; no seed picking',
            pilot_design='After meaningful source support and a valid intervention design, use the same seed and identical pre-treatment inputs across paired arms; preserve every failed/missing run; do not launch from this proposal'))


def prepare(root,proposal_path,scene_path,budget_path,output):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    read=lambda p:json.loads((root/p).read_bytes())
    p=read(proposal_path);scene=read(scene_path);budget=read(budget_path)
    assert scene['proposal_sha256']==digest(root/proposal_path),'scene/proposal binding'
    rules=threshold_proposals(budget);run=p['runs'][0]
    gate_paths=dict(stage_0_2='evidence/results/RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4/scientific_gate_report.json',
        stage_0_4='evidence/results/RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1/gate_report.json')
    gates={k:read(v) for k,v in gate_paths.items()}
    gates['stage_0_5']=dict(gate_status='blocked',status='Verified diagnostic scope; scientific interaction gate blocked',
        support18=scene['all18_positive_state_and_D1_support'],local_source_events=scene['formal_D1']['onset_events'],
        diagnostic_scope=scene['applicability'],evidence_path=str(scene_path),evidence_sha256=digest(root/scene_path),
        reason='No local P2 source event in the fixed B00 window; full state/exposure support does not supply event-triggered effect support or prove interaction equivalence')
    gates['stage_0_6']=dict(gate_status=budget['gate_status'],analytic_truth=budget['analytic_truth']['pass'],
        physical_path_truth=budget['physical_path_truth']['pass'],timestep_fixture='computed; dynamic contrast not established',
        effect_direction='Unknown for actual paired interventions; positive fixture-rho signs are not effect direction evidence',
        scientific_approval=False,evidence_path=str(budget_path),evidence_sha256=digest(root/budget_path))
    fields={}
    def add(name,value,status,source,remaining=None):
        fields[name]=dict(value=value,status=status,source=source,remaining=remaining)
    input_manifest=output/'input_manifest.json'
    input_manifest.write_text(json.dumps(dict(scope='B00 calibration inputs only; StageI data freeze pending',files=run['capsule_input_sha256']),sort_keys=True,indent=2)+'\n',encoding='utf-8')
    add('data_manifest_sha256',digest(input_manifest),'Verified B00 binding; not StageI data-manifest freeze',str(input_manifest))
    add('split_manifest_sha256',None,'Unknown','Current B00 is a calibration-only run','Bind the actual StageI calibration/confirmatory split manifest after design approval')
    add('target_region_rule',dict(mainline_lanes=[1,2,3,4,5],y_m=[150,350]),'Agreed B00 scope; Proposed for StageI',str(proposal_path))
    add('target_vehicle_eligibility_rule','Pre-message fixed target cohort in the declared region; no post-treatment survival/observability selection','Proposed','existing target cohort interface','Researcher must adopt the cohort rule in a valid StageI design')
    add('primary_risk_type','descriptive longitudinal following-risk proxy; exponential rho','Agreed','code/configs/stage_0_2_formal_risk_measurement_p2_v1.json')
    add('primary_endpoint','Paired contrast of vehicle-equal fixed-window integrated formal rho before independently established physical arrival; missing intervals retain [0,1] bounds','Proposed','formal_risk_measurement.py + current project objective','Freeze exact contrast, cohort and pre-physical-arrival estimand; B00 source support absent')
    add('secondary_endpoint','D1-attributed confirmed P2 events per evaluable vehicle-hour; never apply rho tolerance to this count rate','Proposed','stage_0_5_d1_measurement.py')
    add('ttc_threshold_s',2.0,'Agreed','formal risk config')
    add('event_merge_rule',dict(minimum_duration_s=.2,max_gap_s=.11,confirmation='first observed timestamp meeting span'),'Agreed','formal risk config')
    add('valid_observation_mask','Existing reliable identity/leader/clock/status mask; missing never zero; D1 requires both endpoint supports','Agreed','formal_risk_measurement.py + stage_0_5_d1_measurement.py')
    add('time_step_s',dict(native=.05,recording=.1),'Agreed B00; StageI freeze pending',str(proposal_path))
    add('risk_window_s',2.0,'Proposed','Finite fixed-window endpoint interface','2s candidate requires scientific choice; not applied to this B00 measurement')
    add('observation_window_s',run['evaluation_elapsed_s'],'Agreed B00; Proposed for StageI',str(proposal_path))
    add('epsilon_input',dict(exact_input_hash_mismatch=0,paired_untreated_input_difference=0),'Proposed exact matching','current hash/paired-input engineering contract')
    add('epsilon_state',dict(position_difference_quantization_m=.01,speed_difference_quantization_mps=.01,clock_grid_s=.1),'Proposed resolution floor only','Actual FCD precision2, timestamp0.1; error-budget reconstruction fixtures','Not a validated dynamical divergence tolerance; measure matched initial-state errors and sustain rule')
    add('physical_path_rule','Existing directed topology plus archived temporal leader chain; missing IDs => uncertain, unreachable topology distinct, earliest finite arrival only for complete path','Verified implementation; scientific freeze pending','stage_0_1_sumo.analyze_physical_path_from_archived_tables')
    add('right_censoring_rule','Keep right-censored/uncertain paths and observation gaps; no inferring zero or infinite causal isolation; exclude unsupported attribution with counts retained','Proposed preserving existing failure semantics','physical path and D1 contracts')
    add('delta_eq',rules['preferred']['delta_eq_paired_fixture'],'Proposed fixture-only paired contrast floor',str(budget_path),'Actual dynamic and endpoint-specific full budget required; four-arm contrast uses its own bound')
    for k in ['delta_R','delta_plan']:
        add(k,rules['preferred'][k],'Proposed scientific judgment','threshold_proposals/preferred','Researcher SESOI and planning-effect adoption required')
    add('calibration_seeds',rules['planning']['calibration_seed_proposal'],'Proposed; only20261201 B00 executed','Predeclared consecutive seed proposal','No pilot run launched')
    add('paired_variance',None,'Unknown','No approved paired treatment pilot','Estimate from paired seed contrasts; deterministic A01/A02 repetition is not independent variance')
    add('stage_1_1_sample_size',None,'Unknown','prelock_metrics.paired_confirmatory_sample_size','Compute after real paired variance and approved endpoint/SESOI; minimum100 is not the final n')
    add('communication_observability',gates['stage_0_4']['accepted_scope'],'Agreed limited scope',gate_paths['stage_0_4'],'PDR/latency/distance remain uncalibrated sensitivity parameters')
    add('simulation_applicability',gates['stage_0_5'],'Blocked for confirmatory source-triggered effects',str(scene_path))
    add('extrapolation_exclusions',['real accident probability','natural-traffic V2V PDR/latency calibration','unobserved physical truth','unvalidated interaction regimes'],'Proposed retaining accepted limits','Stage0.2/0.4 reports + current Stage0.5 evidence')
    add('missing_failure_inclusion_rules','Register every start; retain failure, pending and censored evidence; no replacement zero or seed selection; no same-envelope restart','Agreed engineering; scientific freeze pending','Current task and native output/ledger contract')
    add('runner_version',p['controller_source_sha256'],'Verified exact executed closure',str(proposal_path))
    add('analyzer_version',scene['provenance']['scientific_modules'],'Verified exact diagnostic closure',str(scene_path))
    add('environment_version',dict(runtime_manifest_sha256=p['runtime_manifest_sha256'],SUMO='1.26.0',TraCI=22),'Verified',str(proposal_path))
    add('code_commit',p['git_commit'],'Verified base SHA plus exact enumerated dirty closure; not a clean-run claim',str(proposal_path))
    assert set(fields)==REQUIRED_FROZEN_FIELDS
    values={k:r['value'] for k,r in fields.items()}
    candidate=dict(schema_version='aad.week.protocol-candidate.v1',status='Proposed / not locked',fields=fields,
        required_field_count=len(REQUIRED_FROZEN_FIELDS),missing_field_keys=[],
        unresolved_scientific_fields=[k for k,r in fields.items() if r['remaining']],thresholds=rules,
        actual_frozen=False,stage_I_launch_allowed=False)
    readiness=protocol_lock_readiness(gates)
    try:
        write_protocol_lock(output_path=output/'protocol_lock.json',gate_reports=gates,frozen_values=values)
    except ProtocolLockError as error:
        refusal=dict(status='Correctly refused',reason=str(error),lock_created=False)
    else:
        raise AssertionError('Unapproved weekly candidate must not create a scientific lock')
    results={'protocol_candidate.json':candidate,'current_gate_reports.json':gates,
        'protocol_lock_readiness.json':readiness,'protocol_lock_writer_check.json':refusal}
    for name,value in results.items():
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    sources={str(path):digest(root/path) for path in [proposal_path,scene_path,budget_path,*gate_paths.values(),
        'code/src/riskprop/protocol_lock.py','code/src/riskprop/prelock_metrics.py','code/scripts/prepare_aad_week_protocol_v1.py']}
    (output/'manifest.json').write_text(json.dumps(dict(files={n:digest(output/n) for n in [*results,'input_manifest.json']},sources=sources),indent=2)+'\n',encoding='utf-8')
    return readiness


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    for name in ['proposal','scene','budget','output']:parser.add_argument('--'+name,required=True)
    a=parser.parse_args();print(json.dumps(prepare(a.repo_root,a.proposal,a.scene,a.budget,a.output)))
