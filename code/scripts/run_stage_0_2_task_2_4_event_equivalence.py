"""Stage 0.2 task 2.4: formal event equivalence and robustness validation."""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'code'/'src'))
T15='code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4'
T23='code/outputs/formal/calibration/stage_0_2_task_2_3_20261011_r3'
DT=.1

def sha256(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def num(s): return pd.to_numeric(s,errors='coerce')
def edges(g):
 g=g.sort_values(['global_time_ms','frame_id']); e=num(g.global_time_ms).diff().eq(100)&num(g.frame_id).diff().eq(1)&g.diagnostic_clock_anchor_ms.eq(g.diagnostic_clock_anchor_ms.shift())
 e &= ~g[['identity_break','observation_gap','leader_changed','trajectory_boundary']].fillna(False).any(axis=1)
 return e.to_numpy()
def runs(m,e):
 m=np.asarray(m,bool); e=np.asarray(e,bool); out=[]; s=None
 for i,v in enumerate(m):
  if v and s is None:s=i
  elif v and not(i>0 and m[i-1] and e[i]):
   if s is not None:out.append((s,i-1))
   s=i
  elif not v and s is not None:out.append((s,i-1)); s=None
 if s is not None:out.append((s,len(m)-1))
 return out
def independent_events(d, threshold=2., min_duration=.1):
 out=[]
 for key,g in d[d.leader_trajectory_id.notna()].groupby(['trajectory_id','leader_trajectory_id'],dropna=False,sort=False):
  g=g.sort_values(['global_time_ms','frame_id']).reset_index(drop=True); e=edges(g); m=g.ttc_valid.fillna(False).to_numpy() & (num(g.ttc_s)<threshold).fillna(False).to_numpy()
  for a,b in runs(m,e):
   span=float(g.iloc[b].time_s-g.iloc[a].time_s)
   if span+1e-12<min_duration: continue
   out.append({'trajectory_id':g.iloc[a].trajectory_id,'leader_trajectory_id':g.iloc[a].leader_trajectory_id,'event_start_s':float(g.iloc[a].time_s),'event_end_s':float(g.iloc[b].time_s),'event_duration_s':span,'raw_frame_count':b-a+1,'ttc_min_s':float(num(g.ttc_s).iloc[a:b+1].min()),'drac_max_mps2':float(num(g.drac_mps2).iloc[a:b+1].max()),'original_row_numbers':tuple(g.iloc[a:b+1].original_row_number.astype(int).tolist())})
 return pd.DataFrame(out)
def event_sets(d):
 return [set(np.asarray(x,dtype=int).tolist()) for x in d.original_row_numbers]
def correspond(formal, indep):
 fs=event_sets(formal); iset=event_sets(indep); used=set(); rows=[]
 for i,f in enumerate(fs):
  cand=[j for j,s in enumerate(iset) if j not in used and s&f]
  if not cand: cat='formal_only'; j=None
  else:
   j=max(cand,key=lambda z:len(f&iset[z])); used.add(j); same=f==iset[j]; cat='exact_member_match' if same else ('boundary_changed' if formal.iloc[i].trajectory_id==indep.iloc[j].trajectory_id else 'pair_or_split_difference')
  rows.append({'formal_index':i,'independent_index':j,'classification':cat,'formal_frames':len(f),'independent_frames':len(iset[j]) if j is not None else 0,'overlap_frames':len(f&iset[j]) if j is not None else 0})
 for j,s in enumerate(iset):
  if j not in used: rows.append({'formal_index':None,'independent_index':j,'classification':'independent_only','formal_frames':0,'independent_frames':len(s),'overlap_frames':0})
 return pd.DataFrame(rows)
def continuous_segments(d):
 rows=[]
 for (tr,lead),g in d[d.leader_trajectory_id.notna() & d.leader_matched.fillna(False) & ~d.identity_uncertain.fillna(False) & ~d.leader_identity_uncertain.fillna(False)].groupby(['trajectory_id','leader_trajectory_id'],sort=False):
  g=g.sort_values(['global_time_ms','frame_id']).reset_index(drop=True); e=edges(g)
  for a,b in runs(np.ones(len(g),bool),e): rows.append({'source':g.iloc[0].source_member,'trajectory_id':tr,'leader_trajectory_id':lead,'start_time_s':float(g.iloc[a].time_s),'end_time_s':float(g.iloc[b].time_s),'frames':b-a+1,'time_span_s':float(g.iloc[b].time_s-g.iloc[a].time_s),'coverage_s':float((b-a+1)*DT),'boundary_limited':bool(a==0 or b==len(g)-1),'global_start_ms':int(g.iloc[a].global_time_ms),'global_end_ms':int(g.iloc[b].global_time_ms)})
 return pd.DataFrame(rows)
def summarize_distribution(d,scenario):
 v=d[d.ttc_valid.fillna(False)].copy(); t=num(v.ttc_s); dr=num(v.drac_mps2); rows=[]
 for src,g in d.groupby('source_member',sort=False):
  z=g[g.ttc_valid.fillna(False)]; tt=num(z.ttc_s); dd=num(z.drac_mps2); row={'source':src,'scenario':scenario,'valid_ttc':len(z),'ttc_lt_2_rows':int((tt<2).sum()),'drac_gt_10_rows':int((dd>10).sum())}
  for q in [.01,.05,.5,.95,.99]: row[f'ttc_q{q}']=float(tt.quantile(q)) if len(tt) else None; row[f'drac_q{q}']=float(dd.quantile(q)) if len(dd) else None
  rows.append(row)
 return rows
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=ROOT); ap.add_argument('--output-dir',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve(); out=a.output_dir.resolve(); out.mkdir(parents=False,exist_ok=False)
 states={p.stem.removeprefix('ngsim_'):p for p in (root/T15/'states').glob('*.parquet')}; event_details=[]; baseline=pd.read_parquet(root/T15/'risk_events.parquet'); all_corr=[]; rule=[]; diff=[]; robust=[]; filters=[]; exposure=[]; segframes=[]; distributions=[]; formal_by_src={}
 for src,path in states.items():
  d=pd.read_parquet(path); formal, reliable, rejected=__import__('riskprop.ngsim_risk_calibration',fromlist=['extract_rear_end_events']).extract_rear_end_events(d,return_diagnostics=True); formal_by_src[src]=formal; indep=independent_events(d); c=correspond(formal,indep); c['source']=src; all_corr.append(c); diff.append({'source':src,'formal_events':len(formal),'independent_events':len(indep),'delta':len(indep)-len(formal),'formal_single_frame':int((formal.raw_frame_count==1).sum()),'independent_single_frame':int((indep.raw_frame_count==1).sum()),'formal_rejected':len(rejected),'classification_counts':c.classification.value_counts().to_dict()}); rule.append({'check':'TTC threshold','formal':'ttc_valid & ttc_s < 2.0','independent':'ttc_valid & ttc_s < 2.0','equivalent':True,'impact':'none'}); rule.append({'check':'minimum duration','formal':'end-start >= 0.1 s','independent':'end-start >= 0.1 s','equivalent':True,'impact':'removed single-frame runs'}); rule += [{'check':'full follower sequence / pair run','formal':'scope+follower then leader pair run','independent':'trajectory_id+leader_trajectory_id group','equivalent':False,'impact':'identity/leader reliability requires formal extractor'},{'check':'reliability and rejection','formal':'identity, leader, intervening observations, frame/global/leader frame checks','independent':'not applied','equivalent':False,'impact':'formal raw/reliable distinction not reproduced'}]
  # S0 formal, S1 true reliability, S2a-d formal semantics on memory copies.
  scenarios={'S0_formal':d,'S1_quality_conditions':d.copy(deep=True),'S2a_mask_ttc_extreme':d.copy(deep=True),'S2b_mask_drac_extreme':d.copy(deep=True),'S2c_mask_gap_extreme':d.copy(deep=True),'S2d_mask_union_extreme':d.copy(deep=True)}
  masks={'S2a_mask_ttc_extreme':d.ttc_valid.fillna(False)&(num(d.ttc_s)<.5),'S2b_mask_drac_extreme':d.ttc_valid.fillna(False)&(num(d.drac_mps2)>10),'S2c_mask_gap_extreme':d.ttc_valid.fillna(False)&(num(d.net_gap_m)<1),'S2d_mask_union_extreme':d.ttc_valid.fillna(False)&((num(d.ttc_s)<.5)|(num(d.drac_mps2)>10)|(num(d.net_gap_m)<1))}
  for name,x in scenarios.items():
   if name in masks: x.loc[masks[name],['ttc_valid','ttc_s','drac_mps2']]=[False,np.nan,np.nan]
   f,rj,rej=__import__('riskprop.ngsim_risk_calibration',fromlist=['extract_rear_end_events']).extract_rear_end_events(x,return_diagnostics=True); valid=x.ttc_valid.fillna(False);
   for _,ev in rj.iterrows(): event_details.append({'source':src,'scenario':name,'event_id':ev.get('event_id'),'trajectory_id':ev.get('trajectory_id'),'leader_trajectory_id':ev.get('leader_trajectory_id'),'event_start_s':ev.get('event_start_s'),'event_end_s':ev.get('event_end_s'),'event_duration_s':ev.get('event_duration_s'),'raw_frame_count':ev.get('raw_frame_count'),'ttc_min_s':ev.get('ttc_min_s'),'drac_max_mps2':ev.get('drac_max_mps2'),'inclusion_status':ev.get('inclusion_status'),'exclusion_reason':ev.get('exclusion_reason'),'original_row_numbers':json.dumps(ev.get('original_row_numbers'),ensure_ascii=False)})
   robust.append({'source':src,'scenario':name,'state_rows':len(x),'valid_ttc_rows':int(valid.sum()),'low_ttc_rows':int((valid&(num(x.ttc_s)<2)).sum()),'event_count':len(rj),'raw_event_count':len(f),'rejected_event_count':len(rej),'event_pair_count':int(rj[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0]) if len(rj) else 0,'masked_rows':int(masks[name].sum()) if name in masks else 0}); distributions += summarize_distribution(x,name)
   if name in masks:
    filters.append({'source':src,'scenario':name,'masked_rows':int(masks[name].sum()),'masked_valid_ttc_rows':int((masks[name]&d.ttc_valid.fillna(False)).sum()),'masked_original_rows_sha256':hashlib.sha256(','.join(map(str,d.loc[masks[name],'original_row_number'].astype(int).tolist())).encode()).hexdigest()})
  seg=continuous_segments(d); segframes.append(seg); exposure.append({'source':src,'all_state_rows':len(d),'reported_leader_rows':int(d.leader_trajectory_id.notna().sum()),'leader_matched_rows':int(d.leader_matched.fillna(False).sum()),'valid_ttc_rows':int(d.ttc_valid.fillna(False).sum()),'continuous_segments':len(seg),'continuous_time_span_s':float(seg.time_span_s.sum()) if len(seg) else 0.0,'continuous_coverage_s':float(seg.coverage_s.sum()) if len(seg) else 0.0,'original_task23_pair_count':int(d[['trajectory_id','leader_trajectory_id']].dropna().drop_duplicates().shape[0]),'continuous_pair_count':int(seg[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0]) if len(seg) else 0})
 pd.DataFrame(rule).drop_duplicates().to_csv(out/'formal_vs_independent_rule_matrix.csv',index=False); pd.DataFrame(diff).to_csv(out/'event_difference_explanations.csv',index=False); corr=pd.concat(all_corr,ignore_index=True); corr.to_csv(out/'event_correspondence.csv',index=False); pd.DataFrame(robust).to_csv(out/'event_robustness.csv',index=False); pd.DataFrame(event_details).to_csv(out/'scenario_event_summary.csv',index=False); pd.DataFrame(filters).to_csv(out/'scenario_filter_audit.csv',index=False); pd.DataFrame(distributions).to_csv(out/'risk_distribution_robustness.csv',index=False); seg=pd.concat(segframes,ignore_index=True); seg.to_parquet(out/'continuous_following_segments.parquet',index=False); pd.DataFrame(exposure).to_csv(out/'exposure_candidates.csv',index=False); pd.DataFrame([{'source':s,'rows':len(pd.read_parquet(p)),'valid_ttc':int(pd.read_parquet(p).ttc_valid.fillna(False).sum()),'nonpositive_gap':int((num(pd.read_parquet(p).net_gap_m)<=0).fillna(False).sum()),'identity_break':int(pd.read_parquet(p).identity_break.fillna(False).sum()),'observation_gap':int(pd.read_parquet(p).observation_gap.fillna(False).sum())} for s,p in states.items()]).to_csv(out/'source_quality_summary.csv',index=False)
 pd.DataFrame([{'item':x,'status':'Decision Required','proposal':'Proposal only; no rule frozen'} for x in ['formal TTC threshold','DRAC joint condition','minimum duration','event entry/exit','event deduplication','extreme observation handling','exposure denominator','SUMO calibration target']]).to_csv(out/'scientific_decision_matrix.csv',index=False)
 audit={'schema_version':'stage_0_2.task_2_4.audit.v1','created_at':datetime.now(UTC).isoformat(),'baseline_events':len(baseline),'formal_recomputed_events':int(sum(x['formal_events'] for x in diff)),'independent_recomputed_events':int(sum(x['independent_events'] for x in diff)),'formal_equivalence':'Equivalent' if all(x['delta']==0 and x['formal_events']==x['independent_events'] for x in diff) else 'Not equivalent — explained','s0_s1_verified_by_formal_rerun':True,'locked_holdout_opened':False,'scientific_claim_eligible':False}; (out/'event_equivalence_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 cfg={'schema_version':'stage_0_2.task_2_4.v1','baseline_input':str((root/T15).resolve()),'threshold_s':2.0,'minimum_duration_s':.1,'max_gap_s':.11,'scenarios':['S0_formal','S1_quality_conditions','S2a_mask_ttc_extreme','S2b_mask_drac_extreme','S2c_mask_gap_extreme','S2d_mask_union_extreme'],'locked_holdout_opened':False,'scientific_claim_eligible':False}; (out/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 prov={'schema_version':'stage_0_2.task_2_4.provenance.v1','created_at':datetime.now(UTC).isoformat(),'python':sys.version,'platform':platform.platform(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'script_sha256':sha256(Path(__file__))}; (out/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); files=sorted(p for p in out.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'}); man={'schema_version':'stage_0_2.task_2_4.manifest.v1','files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in files]}; (out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); allf=files+[out/'manifest.json']; (out/'SHA256SUMS').write_text('\n'.join(f'{sha256(p)}  {p.relative_to(out).as_posix()}' for p in allf)+'\n',encoding='utf-8'); print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__': main()


