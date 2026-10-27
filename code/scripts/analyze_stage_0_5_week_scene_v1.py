"""Current-run diagnostics; no launch, gate mutation, margin or zero imputation."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from riskprop.stage_0_5_scene_reconstruction import parse_fcd,network_edge_lengths
from riskprop.stage_0_5_state_support import fcd_to_state_frame,measure_state_frame,route_length_map
from riskprop.stage_0_5_d1_measurement import local_d1_measurement,offset100_cloud,inside_region


def finite_summary(values):
    a=pd.to_numeric(pd.Series(values),errors='coerce').to_numpy(float);a=a[np.isfinite(a)]
    return dict(n=len(a),mean=float(a.mean()) if len(a) else None,
        quantiles={str(q):float(np.quantile(a,q)) for q in (.05,.5,.95)} if len(a) else None)


def analyze(root,proposal_path,output):
    root=Path(root);proposal_path=root/proposal_path;p=json.loads(proposal_path.read_bytes());run=p['runs'][0]
    work=root/run['artifact_path'];output=Path(output);output.mkdir(parents=True,exist_ok=False)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    native=json.loads((work/'isolation_runtime.json').read_bytes())
    for name,expected in native['artifact_sha256'].items():
        if digest(work/name)!=expected:raise ValueError('sealed_output_drift:'+name)
    for name,expected in run['capsule_input_sha256'].items():
        if digest(work/name)!=expected:raise ValueError('input_drift:'+name)
    if (work/'measured_state.parquet').exists():d=pd.read_parquet(work/'measured_state.parquet')
    else:
        fcd=parse_fcd(work/'fcd.xml',network_edge_lengths(work/'network.net.xml'))
        d=measure_state_frame(fcd_to_state_frame(fcd,route_length_map(work/'routes.rou.xml'),run_id=run['id'],scenario_id=run['condition'],seed=run['seed']))
    window=run['evaluation_elapsed_s'];local=d.loc[inside_region(d)&d.time_s.ge(window[0])&d.time_s.lt(window[1])]
    measured=local_d1_measurement(d,window,strict=True)
    cloud=offset100_cloud(d,window)
    cells=[]
    for row in cloud.itertuples():
        cell=local_d1_measurement(d,(row.block_start_s,row.block_end_s),region=(row.y_start_m,row.y_end_m),strict=True)
        cells.append(dict(t_block=row.t_block,y_block=row.y_block,D1_E_veh_s=cell['local_evaluable_s'],P2_events=cell['onset_events']))
    cloud=cloud.merge(pd.DataFrame(cells),on=['t_block','y_block'],validate='one_to_one')
    ref=pd.read_csv(root/run['common_support_references'][0])
    comparison=cloud.merge(ref,on=['t_block','y_block'],suffixes=('_sim','_real'),validate='one_to_one')
    deltas={}
    for name in ['density_veh_km_lane','speed_mean_mps','low_speed_share','closing_speed_mean_mps','D1_E_veh_s']:
        difference=comparison[name+'_sim']-comparison[name+'_real']
        deltas[name]=dict(sim=finite_summary(comparison[name+'_sim']),real=finite_summary(comparison[name+'_real']),paired_cell_difference=finite_summary(difference),scientific_equivalence='not established; no approved margin or independent systematic-error bound')
    identity=json.loads((work/'identity_summary.json').read_bytes());rows=identity['vehicles']
    groups={}
    for name,selection in [('initial',[r for k,r in rows.items() if k.startswith('i')]),('noninitial',[r for k,r in rows.items() if not k.startswith('i')])]:
        groups[name]=dict(declared=len(selection),inserted=sum(r['actual_departure_s'] is not None for r in selection),
            states=pd.Series([r['state'] for r in selection]).value_counts().to_dict(),
            actual_departure_s=finite_summary([r['actual_departure_s'] for r in selection]),depart_delay_s=finite_summary([r['depart_delay_s'] for r in selection]))
    valid=local.loc[local.measurement_status.eq('valid')&local.ttc_valid]
    support=bool(len(cloud)==18 and cloud.states.ge(10).all() and cloud.D1_E_veh_s.gt(0).all())
    acceptance=json.loads((work/'measurement_acceptance.json').read_bytes()) if (work/'measurement_acceptance.json').exists() else None
    result=dict(schema_version='aad.week-scene-diagnostic.v1',run_id=run['id'],proposal_sha256=digest(proposal_path),window_s=window,
        formal_D1={k:v for k,v in measured.items() if k not in ['events','incomplete_candidates']},
        all18_positive_state_and_D1_support=support,common_cell_differences=deltas,
        local_states=len(local),local_vehicle_count=local.vehicle_id.nunique(),measurement_status=local.measurement_status.value_counts().to_dict(),
        interaction=dict(net_gap_m=finite_summary(local.net_gap_m),closing_speed_mps=finite_summary(local.closing_speed_mps),ttc_s=finite_summary(valid.ttc_s),
            positive_closing_states=int(local.closing_speed_mps.gt(0).sum()),P2_risk_states=int(valid.ttc_s.gt(0).mul(valid.ttc_s.lt(2)).sum())),
        lifecycle=groups,identity_complete=identity['identity_accounting_complete'],
        measurement_acceptance=acceptance,scientific_effect_demonstrated=False,
        applicability=dict(stage_0_5_gate_status='blocked',
            accepted_diagnostic_scope='Finite420s single-seed conditional traffic/reference profiling; legal pending reported, no all-trip-completion requirement',
            source_risk_support='No confirmed local P2 source event in the existing evaluation window' if measured['onset_events']==0 else 'Confirmed local P2 sources observed; sufficiency for causal effect still requires paired mechanism design',
            limitation='A successful baseline and positive exposure do not establish interaction equivalence, a treatment effect or model-discrepancy tolerance',
            minimum_next_design='Use existing same-initialization B00/B10/B01/B11 factorial design only after meaningful source-event support and ramp pulse contract are explicitly set; calibrate paired seed variance separately; no StageI launch from this report'),
        provenance=dict(input_sha256=run['capsule_input_sha256'],raw_artifact_sha256=native['artifact_sha256'],
            analyzer_sha256=digest(Path(__file__)),scientific_modules={n:digest(root/'code/src/riskprop'/n) for n in ['stage_0_5_scene_reconstruction.py','stage_0_5_state_support.py','stage_0_5_d1_measurement.py']}))
    (output/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+chr(10),encoding='utf-8')
    comparison.to_csv(output/'matched18.csv',index=False,lineterminator=chr(10))
    (output/'manifest.json').write_text(json.dumps(dict(files={n:digest(output/n) for n in ['audit.json','matched18.csv']}),indent=2)+chr(10),encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--proposal',required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();r=analyze(a.repo_root,a.proposal,a.output)
    print(json.dumps({k:r[k] for k in ['run_id','all18_positive_state_and_D1_support','formal_D1','interaction','lifecycle','applicability']}))
