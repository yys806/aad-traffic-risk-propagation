"""Stage 0.2 task 2.3: engineering quality and exploratory robustness closure."""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT=Path(__file__).resolve().parents[2]
TASK15='code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4'
TASK21='code/outputs/formal/calibration/stage_0_2_task_2_1_extreme_review_20261011_r4'
TASK221='code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261011_r9'
DT=.1

def sha256(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def finite(x): return pd.to_numeric(x,errors='coerce').replace([np.inf,-np.inf],np.nan)

def ref_runs(mask, edge, pair=None):
 m=np.asarray(mask,dtype=bool); e=np.asarray(edge,dtype=bool); out=[]; s=None
 for i,v in enumerate(m):
  if v and s is None: s=i
  elif v and not (i>0 and m[i-1] and e[i]):
   if s is not None: out.append((s,i-1))
   s=i
  elif not v and s is not None: out.append((s,i-1)); s=None
 if s is not None: out.append((s,len(m)-1))
 return out

def contiguous_edges(d):
 d=d.sort_values(['global_time_ms','frame_id']).reset_index(drop=True)
 dt=finite(d.global_time_ms).diff(); df=finite(d.frame_id).diff()
 clock=d.get('diagnostic_clock_anchor_ms',pd.Series(0,index=d.index)); same=clock.eq(clock.shift())
 cols=['identity_break','observation_gap','leader_changed','trajectory_boundary']
 boundary=d.reindex(columns=cols,fill_value=False).fillna(False).any(axis=1)
 return (dt.eq(100)&df.eq(1)&same&~boundary).to_numpy()

def event_segments(state, mask):
 rows=[]
 work=state.copy(); work['_risk_mask']=np.asarray(mask,dtype=bool)
 for _,g in work[work.trajectory_id.notna() & work.leader_trajectory_id.notna()].groupby(['trajectory_id','leader_trajectory_id'],sort=False):
  g=g.sort_values(['global_time_ms','frame_id']).reset_index(drop=True); edge=contiguous_edges(g); m=g['_risk_mask'].to_numpy(dtype=bool)
  for a,b in ref_runs(m,edge):
   rows.append({'trajectory_id':g.iloc[a].trajectory_id,'leader_trajectory_id':g.iloc[a].leader_trajectory_id,'start_s':float(g.iloc[a].time_s),'end_s':float(g.iloc[b].time_s),'frames':b-a+1,'ttc_min_s':float(finite(g.ttc_s).iloc[a:b+1].min()),'drac_max_mps2':float(finite(g.drac_mps2).iloc[a:b+1].max())})
 return pd.DataFrame(rows)

def oracle_check(rng):
 from run_stage_0_2_task_2_2_kinematic_review import extract_risk_runs
 checks=0
 for n in range(0,12):
  for _ in range(80):
   m=rng.integers(0,2,size=n,dtype=np.int8).astype(bool); e=rng.integers(0,2,size=n,dtype=np.int8).astype(bool)
   expected=ref_runs(m,e); got=extract_risk_runs(m,e)
   assert [(x[0],x[1]) for x in expected]==[(x['start_index'],x['end_index']) for x in got]
   checks+=1
 return checks

def diagnose_case(local,case):
 from run_stage_0_2_task_2_2_kinematic_review import diagnose
 d=diagnose(local,case)
 d.update({'case_id':f"{case.source}:{int(case.original_row_number)}",'source':case.source,'original_row_number':int(case.original_row_number),'trajectory_id':case.trajectory_id,'leader_trajectory_id':case.leader_trajectory_id,'vehicle_id':case.vehicle_id,'leader_id':case.leader_id,'global_time_ms':case.global_time_ms,'frame_id':case.frame_id,'time_s':case.time_s,'review_categories':case.review_categories,'baseline_event_id':case.baseline_event_id,'baseline_event_position':case.baseline_event_position})
 center=local[(local.local_role=='follower') & local.trajectory_id.astype('string').eq(str(case.trajectory_id)) & local.leader_trajectory_id.astype('string').eq(str(case.leader_trajectory_id)) & finite(local.global_time_ms).eq(float(case.global_time_ms)) & finite(local.frame_id).eq(float(case.frame_id))]
 formula_ok=False
 if len(center)==1:
  vals=center.iloc[0]; checks=[]
  for a,b in [('ttc_s','independent_ttc_s'),('drac_mps2','independent_drac_mps2'),('net_gap_m','independent_net_gap_m')]:
   if pd.notna(case.get(b)) and pd.notna(vals.get(a)): checks.append(abs(float(vals[a])-float(case[b]))<1e-6)
  formula_ok=bool(checks) and all(checks)
 d['formula_check']='pass' if formula_ok else ('unverified' if d['center_match_status']!='unique' else 'flagged')
 d['leader_match_check']='pass' if str(case.independent_match_status)=='unique' else 'flagged'
 d['input_completeness']='pass' if d['pair_rows'] and d['center_match_status']=='unique' else 'flagged'
 d['observation_continuity']='flagged' if d['observation_breaks'] else 'pass'
 d['risk_run_pattern']='pass' if d['risk_state_continuity']!='boundary_limited_or_gapped' else 'flagged'
 d['kinematic_consistency']='flagged' if d['kinematic_exploratory_flag'] else 'pass'
 d['geometry_check']='unverified'
 d['physical_truth_status']='unverified'
 return d

def plot_segments(ax,x,y,edge,label):
 x=np.asarray(x); y=np.asarray(y,dtype=float); e=np.asarray(edge,dtype=bool); valid=np.isfinite(y)
 for a,b in ref_runs(valid,e): ax.plot(x[a:b+1],y[a:b+1],label=label)

def full_quality(states):
 out=[]; exposure=[]; event_rows=[]; robust=[]
 for src,path in states.items():
  d=pd.read_parquet(path); d=d.sort_values(['trajectory_id','global_time_ms','frame_id']).reset_index(drop=True)
  valid=finite(d.ttc_s).notna() & d.ttc_valid.fillna(False)
  status=d.measurement_status.astype('string').fillna('missing')
  extreme=(valid & (finite(d.ttc_s)<.5)) | (valid & (finite(d.drac_mps2)>10)) | (finite(d.net_gap_m)<1)
  dx=finite(d.x_m).groupby(d.trajectory_id).diff(); dt=finite(d.time_s).groupby(d.trajectory_id).diff()
  kin=(dx/dt-finite(d.speed_mps)).abs()>5
  # row-level quality summary; all denominators remain explicit
  out.append({'source':src,'rows':len(d),'valid_ttc':int(valid.sum()),'invalid_ttc':int(status.eq('invalid').sum()),'missing_ttc':int(status.eq('missing').sum()),'not_applicable':int(status.eq('not_applicable').sum()),'leader_matched':int(d.leader_matched.fillna(False).sum()),'identity_break_rows':int(d.identity_break.fillna(False).sum()),'observation_gap_rows':int(d.observation_gap.fillna(False).sum()),'nonpositive_gap_rows':int((finite(d.net_gap_m)<=0).fillna(False).sum()),'ttc_lt_0_5_rows':int((valid & (finite(d.ttc_s)<.5)).sum()),'drac_gt_10_rows':int((valid & (finite(d.drac_mps2)>10)).sum()),'extreme_marker_rows':int(extreme.sum()),'kinematic_diff_flag_rows':int(kin.fillna(False).sum()),'follower_trajectories':int(d.trajectory_id.nunique()),'leader_pairs':int(d[['trajectory_id','leader_trajectory_id']].dropna().drop_duplicates().shape[0])})
  pair=d[['trajectory_id','leader_trajectory_id','global_time_ms']].dropna().drop_duplicates().sort_values(['trajectory_id','leader_trajectory_id','global_time_ms']); exposure.append({'source':src,'state_rows':len(d),'valid_ttc_rows':int(valid.sum()),'matched_rows':int(d.leader_matched.fillna(False).sum()),'follower_trajectories':int(d.trajectory_id.nunique()),'vehicle_pairs':int(d[['trajectory_id','leader_trajectory_id']].dropna().drop_duplicates().shape[0]),'pair_observation_time_s':float(pair.groupby(['trajectory_id','leader_trajectory_id']).size().sub(1).clip(lower=0).sum()*DT)})
  base=d.copy(); base['risk']=valid & (finite(d.ttc_s)<2)
  s0=event_segments(base,base.risk); s2=event_segments(base,base.risk & ~extreme)
  robust += [{'source':src,'scenario':'S0_raw_baseline','state_rows':len(d),'risk_frames':int(base.risk.sum()),'event_count':len(s0),'event_pair_count':int(s0[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0])},{'source':src,'scenario':'S1_verified_engineering_conditions','state_rows':len(d),'risk_frames':int(base.risk.sum()),'event_count':len(s0),'event_pair_count':int(s0[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0])},{'source':src,'scenario':'S2_extreme_mask_pressure_test','state_rows':len(d),'risk_frames':int((base.risk & ~extreme).sum()),'event_count':len(s2),'event_pair_count':int(s2[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0])}]
  for i,e in s0.iterrows(): event_rows.append({'source':src,'event_index':i,'scenario':'S0','min_ttc_s':e.ttc_min_s,'max_drac_mps2':e.drac_max_mps2,'extreme_by_value':bool(e.ttc_min_s<.5 or e.drac_max_mps2>10)})
 return pd.DataFrame(out),pd.DataFrame(exposure),pd.DataFrame(robust),pd.DataFrame(event_rows)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=ROOT); ap.add_argument('--output-dir',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve(); out=a.output_dir.resolve(); out.mkdir(parents=False,exist_ok=False)
 inp=root/TASK21; cases=pd.read_csv(inp/'review_cases.csv'); rows=[]
 for _,c in cases.iterrows(): rows.append(diagnose_case(pd.read_parquet(inp/f"local_{c.source}_{int(c.original_row_number)}.parquet"),c))
 diag=pd.DataFrame(rows); diag.to_csv(out/'case_diagnostics.csv',index=False)
 oracle=oracle_check(np.random.default_rng(20261022));
 r9=pd.read_csv(root/TASK221/'case_diagnostics.csv'); cmp=diag[['case_id','risk_state_continuity','extreme_rows','extreme_longest_contiguous_frames','center_match_status']].merge(r9[['case_id','risk_state_continuity','extreme_rows','extreme_longest_contiguous_frames']],on='case_id',suffixes=('_new','_r9')); cmp['continuity_changed']=cmp.risk_state_continuity_new.ne(cmp.risk_state_continuity_r9); cmp['longest_changed']=cmp.extreme_longest_contiguous_frames_new.ne(cmp.extreme_longest_contiguous_frames_r9); cmp.to_csv(out/'run_consistency_audit.csv',index=False)
 states={p.stem.removeprefix('ngsim_'):p for p in (root/TASK15/'states').glob('*.parquet')}; fq,exp,rob,ev=full_quality(states); fq.to_csv(out/'full_quality_summary.csv',index=False); exp.to_csv(out/'exposure_candidates.csv',index=False); rob.to_csv(out/'event_robustness.csv',index=False); ev.to_csv(out/'event_correspondence.csv',index=False)
 rep=pd.read_csv(root/TASK221/'representative_cases.csv'); rep=rep.merge(diag[['case_id','center_match_status','formula_check','leader_match_check','input_completeness','observation_continuity','risk_run_pattern','kinematic_consistency','geometry_check','physical_truth_status']],on='case_id',how='left'); rep.to_csv(out/'representative_cases.csv',index=False)
 cov=pd.read_csv(root/TASK221/'coverage_matrix.csv'); cov.to_csv(out/'coverage_matrix.csv',index=False)
 decision=pd.DataFrame([{'item':x,'current_fact':'not frozen','supports':'descriptive engineering evidence only','does_not_support':'scientific selection','proposal':'researcher decision required','owner':'human_researcher'} for x in ['formal TTC threshold','DRAC joint condition','minimum duration','event entry/exit','hysteresis','event deduplication','extreme handling','exposure denominator','cross-source applicability','SUMO calibration statistics']]); decision.to_csv(out/'scientific_decision_matrix.csv',index=False)
 with PdfPages(out/'representative_casebook.pdf') as pdf:
  for _,x in rep.iterrows():
   d=pd.read_parquet(inp/f"local_{x.source}_{int(x.original_row_number)}.parquet"); f=d[(d.local_role=='follower')&(d.trajectory_id.astype('string')==str(x.trajectory_id))&(d.leader_trajectory_id.astype('string')==str(x.leader_trajectory_id))].sort_values(['global_time_ms','frame_id']); l=d[(d.local_role=='leader')&(d.trajectory_id.astype('string')==str(x.leader_trajectory_id))].sort_values(['global_time_ms','frame_id']); edge=finite(f.global_time_ms).diff().eq(100)&finite(f.frame_id).diff().eq(1)&f.diagnostic_clock_anchor_ms.eq(f.diagnostic_clock_anchor_ms.shift())&~f[['identity_break','observation_gap','leader_changed','trajectory_boundary']].fillna(False).any(axis=1); fig,ax=plt.subplots(3,1,figsize=(10,8),sharex=True); plot_segments(ax[0],f.time_s,f.ttc_s,edge,'TTC pair'); plot_segments(ax[0],f.time_s,f.drac_mps2,edge,'DRAC pair'); plot_segments(ax[1],f.time_s,f.net_gap_m,edge,'net gap pair'); plot_segments(ax[1],f.time_s,f.closing_speed_mps,edge,'closing pair'); ax[2].plot(f.time_s,f.speed_mps,label='follower speed'); ax[2].plot(l.time_s,l.speed_mps,label='leader speed'); ax[2].plot(f.time_s,f.acceleration_mps2,label='follower acceleration'); [z.legend() for z in ax]; fig.suptitle(f"{x.case_id} | {x.risk_state_continuity} | center={x.center_match_status}"); fig.tight_layout(); pdf.savefig(fig); plt.close(fig)
 config={'schema_version':'stage_0_2.task_2_3.v1','cases':len(diag),'full_state_rows':int(fq.rows.sum()),'baseline_event_count':5381,'oracle_checks':oracle,'locked_holdout_opened':False,'scientific_claim_eligible':False,'exploratory_s2_is_not_exclusion_rule':True}; (out/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 audit={'schema_version':'stage_0_2.task_2_3.audit.v1','created_at':datetime.now(UTC).isoformat(),'cases':len(diag),'center_match_counts':diag.center_match_status.value_counts().to_dict(),'r9_continuity_changes':int(cmp.continuity_changed.sum()),'r9_longest_changes':int(cmp.longest_changed.sum()),'full_state_rows':int(fq.rows.sum()),'baseline_events':5381,'s0_recomputed_events':int(rob.loc[rob.scenario=='S0_raw_baseline','event_count'].sum()),'manual_review_completed':False,'locked_holdout_opened':False}; (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 prov={'schema_version':'stage_0_2.task_2_3.provenance.v1','created_at':datetime.now(UTC).isoformat(),'python':sys.version,'platform':platform.platform(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'script_sha256':sha256(Path(__file__))}; (out/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 files=sorted(p for p in out.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'}); man={'schema_version':'stage_0_2.task_2_3.manifest.v1','files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in files]}; (out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); (out/'SHA256SUMS').write_text('\n'.join(f'{sha256(p)}  {p.relative_to(out).as_posix()}' for p in files+[out/'manifest.json'])+'\n',encoding='utf-8'); print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
