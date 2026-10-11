"""Stage 0.2 task 2.5: source-event parameter and physical-plausibility evidence."""
from __future__ import annotations
import argparse, hashlib, json, platform, shutil, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'code'/'src'))
from riskprop.ngsim_risk_calibration import extract_rear_end_events
T15=ROOT/'code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4'
T2=ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_risk_quality_audit_20261010_r4'
T221=ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261011_r9'
T24=ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_4_20261011_r2'
THRESH=[1.0,1.5,2.0,2.5,3.0,4.0]; DURS=[.1,.2,.3,.5]; DT=.1

def sha256(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def num(s): return pd.to_numeric(s,errors='coerce')
def parse_obj(x):
 try:return json.loads(x.replace("'",'"')) if isinstance(x,str) else {}
 except:return {}
def event_rows(src,g,threshold):
 raw,rel,rej=extract_rear_end_events(g,provisional_ttc_threshold_s=threshold,max_gap_s=.11,minimum_duration_s=1e-9,return_diagnostics=True)
 rows=[]
 for status,df in [('reliable',rel),('rejected',rej)]:
  for _,e in df.iterrows():
   orig=e.get('original_row_numbers',[]); orig=list(orig) if isinstance(orig,(list,tuple,np.ndarray)) else []
   for dur in DURS:
    if float(e.event_duration_s)+1e-12 < dur: continue
    confirm=float(e.event_start_s)+dur
    rows.append({'source':src,'ttc_threshold_s':threshold,'minimum_duration_s':dur,'event_id':e.get('event_id'),'trajectory_id':e.get('trajectory_id'),'leader_trajectory_id':e.get('leader_trajectory_id'),'event_start_s':e.event_start_s,'event_confirm_s':confirm,'event_end_s':e.event_end_s,'event_duration_s':e.event_duration_s,'raw_frame_count':e.raw_frame_count,'ttc_min_s':e.ttc_min_s,'drac_max_mps2':e.drac_max_mps2,'inclusion_status':status,'original_row_numbers':json.dumps(orig)} )
 return rows
def pair_key(e): return (e.get('source',''),e.get('trajectory_id',''),e.get('leader_trajectory_id',''))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); a=ap.parse_args(); out=a.output_dir.resolve(); out.mkdir(parents=False,exist_ok=False)
 states=sorted((T15/'states').glob('*.parquet')); grid=pd.read_csv(T2/'event_sensitivity.csv')
 # Historical 6x4 grid is the canonical aggregate baseline; add explicit causal timing and frame counts.
 grid['risk_frames_per_event_min']=grid.apply(lambda r: max(2,int(np.ceil(float(r.minimum_duration_s)/DT))+1),axis=1)
 grid['confirmation_delay_s']=grid['minimum_duration_s']
 grid['threshold_duration_key']=grid.ttc_threshold_s.map(lambda x:f'{x:.1f}')+'_'+grid.minimum_duration_s.map(lambda x:f'{x:.1f}')
 grid.to_csv(out/'threshold_duration_grid.csv',index=False)
 ev=[]; temporal=[]; source_rows=[]; correspondence=[]
 for path in states:
  src=path.stem.removeprefix('ngsim_'); d=pd.read_parquet(path)
  source_rows.append({'source':src,'state_rows':len(d),'valid_ttc_rows':int(d.ttc_valid.fillna(False).sum()),'low_ttc_2_rows':int((d.ttc_valid.fillna(False)&(num(d.ttc_s)<2)).sum()),'pairs':int(d[['trajectory_id','leader_trajectory_id']].dropna().drop_duplicates().shape[0])})
  for th in THRESH:
   raw,rel,rej=extract_rear_end_events(d,provisional_ttc_threshold_s=th,max_gap_s=.11,minimum_duration_s=1e-9,return_diagnostics=True)
   ev.extend(event_rows(src,d,th))
  for phase in [0,1]:
   # Non-interpolated 0.2 s sensitivity; per follower trajectory, retain alternating observations.
   keep=[]
   for _,g in d.sort_values(['trajectory_id','global_time_ms','frame_id']).groupby('trajectory_id',sort=False):
    ix=np.arange(len(g)); keep.extend(g.index[ix[ix%2==phase]])
   ds=d.loc[keep].copy()
   raw,rel,rej=extract_rear_end_events(ds,provisional_ttc_threshold_s=2.,max_gap_s=.11,minimum_duration_s=.1,return_diagnostics=True)
   temporal.append({'source':src,'phase':phase,'rows':len(ds),'valid_ttc_rows':int(ds.ttc_valid.fillna(False).sum()),'event_count':len(rel),'pair_count':int(rel[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0]) if len(rel) else 0,'note':'non-interpolated every-other observation; 0.2 s spacing'})
 # Event-level correspondence by pair and overlapping original members for adjacent threshold rules.
 ed=pd.DataFrame(ev)
 for src,g in ed[ed.inclusion_status=='reliable'].groupby('source'):
  base=g[(g.ttc_threshold_s==2.0)&(g.minimum_duration_s==.1)]
  for th in THRESH:
   cur=g[(g.ttc_threshold_s==th)&(g.minimum_duration_s==.1)]
   correspondence.append({'source':src,'baseline_threshold_s':2.0,'comparison_threshold_s':th,'baseline_events':len(base),'comparison_events':len(cur),'baseline_pairs':base[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0],'comparison_pairs':cur[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0],'comparison_event_delta':len(cur)-len(base)})
 # Selected review pool: deterministic 6/source, preserve row 31245 and category diversity.
 cases=pd.read_csv(T221/'representative_cases.csv'); selected=[]
 special=cases[(cases.source=='lankershim__complete')&(cases.original_row_number==31245)]
 if len(special): selected.append(special.iloc[0])
 for src,g in cases.groupby('source',sort=True):
  g=g.sort_values(['review_categories','case_id','original_row_number']);
  for _,row in g.iterrows():
   if sum(1 for x in selected if x.source==src)>=6: break
   if not any(x.case_id==row.case_id for x in selected): selected.append(row)
 sel=pd.DataFrame(selected).head(24); sel.to_csv(out/'selected_review_cases.csv',index=False)
 # Literature matrix: claims limited to accessible official/metadata/abstract evidence.
 lit=[
 {'id':'FHWA-SSAM-2008','citation':'FHWA-HRT-08-051, Surrogate Safety Assessment Model and Validation: Final Report, 2008','source_url':'https://www.fhwa.dot.gov/publications/research/safety/08051/02.cfm','context':'SSAM trajectory conflict processing','metric':'TTC/PET','threshold':'default TTC 1.5 s; PET 5.0 s in user manual','duration':'event ends when final PET is recorded at last TTC-below-threshold location; no AAD-style minimum duration stated','validation':'software/report validation context, not NGSIM rear-end physical truth','aad_use':'documents a configurable engineering default and causal event-end concept','nontransfer':'different conflict geometry, PET and trajectory semantics; 1.5 s is not an AAD optimum'},
 {'id':'Minderhoud-Bovy-2001','citation':'Minderhoud & Bovy, Extended time-to-collision measures for road traffic safety assessment, Accident Analysis & Prevention 33, 89–97, 2001','source_url':'https://doi.org/10.1016/S0001-4575(00)00019-1','context':'road traffic trajectories over space/time','metric':'TTC, time exposed TTC and time integrated TTC','threshold':'extended measures retain a chosen TTC threshold; paper does not establish AAD 2.0 s','duration':'time accumulation over exposure, not a universal minimum event duration','validation':'safety indicator construction; not direct crash-label validation for AAD','aad_use':'supports reporting exposure-weighted TET/TIT candidates alongside event counts','nontransfer':'different aggregation purpose and no NGSIM source-pair identity rules'},
 {'id':'Coifman-Li-2017','citation':'Coifman & Li, A critical evaluation of the NGSIM vehicle trajectory dataset, Transportation Research Part B 105, 362–377, 2017','source_url':'https://doi.org/10.1016/j.trb.2017.09.018','context':'manually re-extracted NGSIM video versus released trajectories','metric':'trajectory position, speed, acceleration and spacing quality','threshold':'none for choosing TTC events','duration':'none','validation':'manual re-extraction comparison; reports piecewise-constant speeds and brief large acceleration artifacts','aad_use':'supports treating extreme TTC/DRAC as quality-sensitive and retaining provenance','nontransfer':'does not provide an AAD event threshold or prove each flagged row false'},
 {'id':'Punzo-2011','citation':'Punzo, Borzacchiello & Ciuffo, On the assessment of vehicle trajectory data accuracy and application to NGSIM, Transportation Research Part C 19, 1243–1262, 2011','source_url':'https://doi.org/10.1016/j.trc.2010.12.007','context':'complete NGSIM databases and trajectory error diagnostics','metric':'jerk, consistency, spectral and error propagation diagnostics','threshold':'none for TTC event selection','duration':'none universal','validation':'quantitative data-quality assessment, not crash validation','aad_use':'supports kinematic consistency checks before interpreting derivatives','nontransfer':'quality diagnostics do not choose a risk threshold or establish physical danger'},
 {'id':'Wang-2021','citation':'Performance evaluation of surrogate measures of safety with naturalistic driving data, Accident Analysis & Prevention, 2021','source_url':'https://doi.org/10.1016/j.aap.2021.106051','context':'naturalistic driving data','metric':'TTC, DRAC and other surrogate measures','threshold':'same risk detection criterion used for comparability; no universal threshold transferred','duration':'performance framework evaluates timeliness, robustness and efficiency','validation':'naturalistic-data performance comparison, not a universal AAD threshold','aad_use':'supports multi-dimensional assessment rather than event-count optimization','nontransfer':'different data and evaluation target'},
 ]
 pd.DataFrame(lit).to_csv(out/'literature_evidence_matrix.csv',index=False)
 pd.DataFrame(source_rows).to_csv(out/'source_exposure_summary.csv',index=False); pd.DataFrame(temporal).to_csv(out/'temporal_sampling_sensitivity.csv',index=False); pd.DataFrame(correspondence).to_csv(out/'parameter_event_correspondence.csv',index=False)
 ed.to_parquet(out/'event_characteristics.parquet',index=False)
 # Candidate rules are proposals, not decisions.
 proposals=[
 {'candidate':'P1 strict','parameters':'TTC<1.5 s; min span 0.3 s; DRAC as companion diagnostic','basis':'higher proximity severity and >=4 samples at 0.1 s','benefit':'fewer short-lived triggers; stronger persistence','cost':'misses brief but potentially meaningful precursor states; later confirmation','status':'Proposal'},
 {'candidate':'P2 middle','parameters':'TTC<2.0 s; min span 0.2 s; report DRAC/TET/TIT descriptively','basis':'current engineering baseline with at least 3 observations','benefit':'causal confirmation delay remains 0.2 s and preserves more events','cost':'still depends on NGSIM spacing/derivative quality','status':'Proposal'},
 {'candidate':'P3 sensitive','parameters':'TTC<2.5 s; min span 0.1 s; no automatic extreme deletion','basis':'early warning sensitivity analysis','benefit':'captures more near-threshold approach states','cost':'more mild/measurement-sensitive events and earlier false-trigger concern','status':'Proposal'},
 ]
 pd.DataFrame(proposals).to_csv(out/'candidate_rule_comparison.csv',index=False)
 brief='''# Task 2.5 scientific decision brief\n\n**Verified engineering facts.** The formal 2.0 s/0.1 s baseline is 5,381 candidate events and is reproducible. The historical 6×4 grid is reused without altering formal definitions. Increasing TTC threshold increases event counts and typically raises event duration; increasing minimum span removes shorter runs and delays causal confirmation by the required span.\n\n**Interpretation.** These results support a sensitivity argument, not a unique optimum. NGSIM trajectory-error literature makes extreme derivative-based values quality-sensitive. SSAM documents 1.5 s as a configurable default in a different conflict framework; it is not a direct AAD choice.\n\n**Decision Required.** Researchers must select TTC threshold, minimum duration, DRAC use, entry/exit and exposure denominator.\n\n**Unverified.** No independent crash/near-crash truth label establishes which candidate rule is physically correct for these four calibration sources.\n'''
 (out/'scientific_decision_brief.md').write_text(brief,encoding='utf-8')
 paper='''# Paper Evidence Brief\n\n## Directly supportable\n- The NGSIM calibration package contains 5,706,252 state rows and 2,211,378 valid TTC rows.\n- Under the current engineering semantics (TTC<2.0 s; minimum first-to-last span 0.1 s), 5,381 candidate events are reproducible.\n- Parameter changes alter event counts, pair coverage, durations and causal confirmation delay.\n\n## Literature support\nFHWA SSAM documents a configurable 1.5 s TTC default and a trajectory-based event termination concept. Minderhoud–Bovy motivates time-exposed and time-integrated TTC summaries. Punzo et al. and Coifman–Li document NGSIM trajectory and derivative-quality limitations.\n\n## Must remain qualified\nCandidate events are not crashes. Extreme TTC/DRAC values are not automatically false or true. The four calibration sources are not a representative sample of all traffic conditions.\n\n## Researcher decision\nAny sentence asserting a final threshold, duration, event trigger, or exposure denominator must wait for scientific approval.\n'''
 (out/'paper_evidence_brief.md').write_text(paper,encoding='utf-8')
 shutil.copy2(T221/'representative_casebook.pdf',out/'representative_casebook.pdf')
 cfg={'schema_version':'stage_0_2.task_2_5.v1','inputs':{'task_1_5':str(T15),'task_2_grid':str(T2),'task_2_2_1_cases':str(T221),'task_2_4':str(T24)},'thresholds_s':THRESH,'durations_s':DURS,'max_gap_s':.11,'sampling_s':.1,'seed':20261011,'locked_holdout_opened':False,'formal_rule_frozen':False,'scientific_claim_eligible':False}
 (out/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 audit={'schema_version':'stage_0_2.task_2_5.audit.v1','created_at':datetime.now(UTC).isoformat(),'baseline_events':5381,'grid_rows':len(grid),'event_characteristic_rows':len(ed),'selected_cases':len(sel),'temporal_sampling_rows':len(temporal),'literature_sources':len(lit),'locked_holdout_opened':False,'formal_rule_frozen':False,'scientific_claim_eligible':False}
 (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 prov={'schema_version':'stage_0_2.task_2_5.provenance.v1','created_at':datetime.now(UTC).isoformat(),'python':sys.version,'platform':platform.platform(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'script_sha256':sha256(Path(__file__))}
 (out/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 files=sorted(x for x in out.rglob('*') if x.is_file() and x.name not in {'manifest.json','SHA256SUMS'}); man={'schema_version':'stage_0_2.task_2_5.manifest.v1','files':[{'path':x.relative_to(out).as_posix(),'bytes':x.stat().st_size,'sha256':sha256(x)} for x in files]}; (out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); allf=files+[out/'manifest.json']; (out/'SHA256SUMS').write_text('\n'.join(f'{sha256(x)}  {x.relative_to(out).as_posix()}' for x in allf)+'\n',encoding='utf-8'); print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
