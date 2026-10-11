from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code'/'src'))
import ast, json, hashlib, platform, subprocess
import pandas as pd
from riskprop.formal_risk_measurement import P2_FORMAL_CONFIG, extract_formal_source_events, rho_from_ttc, contribution_bounds, integrate_fixed_window, did_interval

OUT=ROOT/'code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r1'
OUT.mkdir(parents=True, exist_ok=False)
state_dir=ROOT/'code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states'
paths=sorted(state_dir.glob('*.parquet'))
rows=[]
for path in paths:
    states=pd.read_parquet(path)
    events=extract_formal_source_events(states, P2_FORMAL_CONFIG)
    for _,e in events.iterrows():
        rows.append({'source_file':path.name,'dataset':e['dataset'],'site':e['site'],'window_id':e['window_id'],'source_member':e['source_member'],'trajectory_id':e['trajectory_id'],'leader_trajectory_id':e['leader_trajectory_id'],'event_id':e['event_id'],'event_start_s':e['event_start_s'],'event_confirm_s':e['event_confirm_s'],'event_end_s':e['event_end_s'],'raw_frame_count':e['raw_frame_count'],'ttc_min_s':e['ttc_min_s'],'drac_max_mps2':e['drac_max_mps2'],'original_row_numbers_sha256':hashlib.sha256(json.dumps(list(e['original_row_numbers']),sort_keys=True).encode()).hexdigest()})
events_df=pd.DataFrame(rows)
events_df.to_csv(OUT/'p2_event_revalidation.csv',index=False)
summary=events_df.groupby(['site','window_id'],dropna=False).agg(event_count=('event_id','size'),pair_count=('trajectory_id',lambda x:x.astype(str).nunique()),min_ttc_s=('ttc_min_s','min'),median_duration_s=('event_end_s',lambda x:0)).reset_index()
# add duration summary
if not events_df.empty:
    events_df['duration_s']=events_df['event_end_s']-events_df['event_start_s']
    summary=events_df.groupby(['site','window_id'],dropna=False).agg(event_count=('event_id','size'),pair_count=('trajectory_id',lambda x:x.astype(str).nunique()),min_ttc_s=('ttc_min_s','min'),median_duration_s=('duration_s','median'),max_duration_s=('duration_s','max')).reset_index()
summary.to_csv(OUT/'p2_source_summary.csv',index=False)
# independent formula/status fixture audit
fixture=[]
for status,in_region,ttc in [('valid',True,2.0),('not_applicable',True,8.0),('invalid',True,2.0),('missing',True,2.0),('valid',False,2.0),('valid',None,2.0)]:
    lo,hi,rho=contribution_bounds(measurement_status=status,in_region=in_region,ttc_s=ttc)
    fixture.append({'status':status,'in_region':in_region,'ttc_s':ttc,'lower':lo,'upper':hi,'rho':rho})
pd.DataFrame(fixture).to_csv(OUT/'contribution_fixture_audit.csv',index=False)
# temporal semantic fixture
sem=[]
for step in (0.1,0.2):
    times=[0.0,step,2*step]
    sem.append({'sampling_step_s':step,'frame_delta':1 if step==0.1 else 2,'span_s':times[-1]-times[0],'p2_min_span_s':0.2,'causal_confirm_s':times[2] if times[-1]-times[0]>=0.2 else None,'formal_100ms_compatible':step==0.1})
pd.DataFrame(sem).to_csv(OUT/'temporal_semantics_validation.csv',index=False)
# baseline comparison
pd.DataFrame([{'metric':'p2_reliable_event_count','formal_v1':len(events_df),'task_2_5_1_p2_reference':4545,'status':'compare'}]).to_csv(OUT/'historical_comparison.csv',index=False)
config={'schema_version':P2_FORMAL_CONFIG.schema_version,'algorithm_version':P2_FORMAL_CONFIG.algorithm_version,'p2':P2_FORMAL_CONFIG.to_dict(),'inputs':[str(p.relative_to(ROOT)) for p in paths],'target_region_status':'Unresolved','evaluation_window_status':'Unresolved','locked_holdout_opened':False}
(OUT/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
audit={'event_count':int(len(events_df)),'source_count':len(paths),'p2_expected_reference':4545,'p2_count_matches_reference':bool(len(events_df)==4545),'target_burden_computed':False,'reason':'target region, fixed cohort, and evaluation window are not approved in config','tests':'test_formal_risk_measurement.py'}
(OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
prov={'script':'code/scripts/run_stage_0_2_formal_risk_measurement_validation.py','python':platform.python_version(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'inputs':[str(p.relative_to(ROOT)) for p in paths]}
(OUT/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2))
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
manifest={'artifact_dir':str(OUT.relative_to(ROOT)),'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(
    f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files
))
print('events',len(events_df),'out',OUT)
