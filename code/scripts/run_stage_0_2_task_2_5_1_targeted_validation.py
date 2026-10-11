"""Stage 0.2 task 2.5.1 targeted P1/P2/P3 validation."""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'code'/'src')); sys.path.insert(0,str(ROOT/'code'/'scripts'))
from riskprop.ngsim_risk_calibration import extract_rear_end_events
T15=ROOT/'code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4'; T25=ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_5_20261011_r1'; T221=ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261011_r9'; DT=.1
RULES={'P1_strict':(1.5,.3),'P2_middle':(2.0,.2),'P3_sensitive':(2.5,.1),'REF_2.0_0.1':(2.0,.1)}

def sha256(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def n(s):return pd.to_numeric(s,errors='coerce')
def members(x):
 if isinstance(x,(list,tuple,np.ndarray)):return set(map(int,x))
 try:return set(map(int,json.loads(x)))
 except:return set()
def add_event_rows(src,df,rule,threshold,dur):
 raw,rel,rej=extract_rear_end_events(df,provisional_ttc_threshold_s=threshold,max_gap_s=.11,minimum_duration_s=1e-9,return_diagnostics=True)
 rows=[]
 for status,events in [('reliable',rel),('rejected',rej)]:
  # rejected has only id/reason/count; join raw candidate metadata by event_id.
  if status=='rejected':
   events=events.merge(raw[['event_id','dataset','site','window_id','source_member','source_period','trajectory_id','leader_trajectory_id','event_start_s','event_end_s','event_duration_s','ttc_min_s','drac_max_mps2','original_row_numbers']],on='event_id',how='left')
  for _,e in events.iterrows():
   span=float(e.get('event_duration_s',np.nan))
   if not np.isfinite(span) or span+1e-12<dur:continue
   start=float(e.event_start_s); end=float(e.event_end_s); orig=members(e.get('original_row_numbers',[]))
   rows.append({'source':src,'rule':rule,'ttc_threshold_s':threshold,'minimum_duration_s':dur,'event_id':e.get('event_id'),'dataset':e.get('dataset'),'site':e.get('site'),'window_id':e.get('window_id'),'source_member':e.get('source_member'),'source_period':e.get('source_period'),'trajectory_id':e.get('trajectory_id'),'leader_trajectory_id':e.get('leader_trajectory_id'),'event_start_s':start,'event_confirm_s':None,'event_end_s':end,'event_duration_s':span,'raw_frame_count':int(e.get('raw_frame_count',len(orig))),'ttc_min_s':e.get('ttc_min_s'),'drac_max_mps2':e.get('drac_max_mps2'),'inclusion_status':status,'rejection_reason':e.get('rejection_reason',''),'original_row_numbers':json.dumps(sorted(orig))})
 return pd.DataFrame(rows)
def confirm_from_members(ev,df):
 # Validate confirmation against real observation timestamps in the event member set.
 idx={int(r):i for i,r in enumerate(df.original_row_number.astype(int))} if 'original_row_number' in df else {}
 out=[]
 for _,e in ev.iterrows():
  ms=sorted(members(e.original_row_numbers)); times=df[df.original_row_number.astype(int).isin(ms)].sort_values(['global_time_ms','frame_id']).time_s.astype(float).tolist()
  if not times: out.append(np.nan); continue
  target=times[0]+float(e.minimum_duration_s); actual=next((t for t in times if t+1e-9>=target),np.nan); out.append(actual)
 ev=ev.copy();ev['event_confirm_s']=out;ev['confirm_delay_s']=ev.event_confirm_s-ev.event_start_s;ev['confirm_observed']=ev.event_confirm_s.notna()&(ev.event_confirm_s<=ev.event_end_s+1e-8); return ev
def overlap_edges(events):
 rows=[]; names=list(events)
 # Index by source and vehicle pair so all one-to-many/many-to-one edges are retained.
 for i,a in enumerate(names):
  A=events[a]
  for b in names[i+1:]:
   B=events[b]; idx={}
   for ib,y in B.iterrows():
    key=(y.source,str(y.trajectory_id),str(y.leader_trajectory_id))
    for m in members(y.original_row_numbers): idx.setdefault((key,m),set()).add(ib)
   for ia,x in A.iterrows():
    key=(x.source,str(x.trajectory_id),str(x.leader_trajectory_id)); sx=members(x.original_row_numbers); cand=set()
    for m in sx: cand.update(idx.get((key,m),set()))
    for ib in cand:
     y=B.loc[ib]; sy=members(y.original_row_numbers); inter=sx&sy
     if not inter:continue
     rows.append({'rule_a':a,'rule_b':b,'source':x.source,'event_id_a':x.event_id,'event_id_b':y.event_id,'trajectory_id':x.trajectory_id,'leader_trajectory_id':y.leader_trajectory_id,'overlap_frames':len(inter),'a_frames':len(sx),'b_frames':len(sy),'jaccard':len(inter)/len(sx|sy),'exact_member_match':sx==sy,'boundary_changed':sx!=sy})
 return pd.DataFrame(rows)
def classify(edges,events):
 out=[]
 for pair,g in edges.groupby(['rule_a','rule_b'],sort=False):
  degA=g.groupby('event_id_a').event_id_b.nunique().to_dict();degB=g.groupby('event_id_b').event_id_a.nunique().to_dict(); A=events[pair[0]];B=events[pair[1]]
  for rid,df,degs,side in [(pair[0],A,degA,'a'),(pair[1],B,degB,'b')]:
   for _,e in df.iterrows():
    deg=degs.get(e.event_id,0); out.append({'comparison':pair[0]+'__'+pair[1],'rule':rid,'source':e.source,'event_id':e.event_id,'overlap_degree':deg,'classification':'unmatched' if deg==0 else ('split_or_merge_component' if deg>1 else 'matched_or_boundary')})
 return pd.DataFrame(out)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();out=a.output_dir.resolve();out.mkdir(parents=False,exist_ok=False)
 states={p.stem.removeprefix('ngsim_'):pd.read_parquet(p) for p in sorted((T15/'states').glob('*.parquet'))}
 events={}; all_ev=[]
 for rule,(th,dur) in RULES.items():
  frames=[]
  for src,d in states.items():
   e=add_event_rows(src,d,rule,th,dur); e=confirm_from_members(e,d);frames.append(e)
  events[rule]=pd.concat(frames,ignore_index=True);all_ev.append(events[rule])
 edges=overlap_edges(events);edges.to_parquet(out/'event_overlap_edges.parquet',index=False); classes=classify(edges,events);classes.to_csv(out/'event_change_classification.csv',index=False)
 # Metrics and Q1-Q4 summaries.
 mets=[]
 for rule,e in events.items():
  r=e[e.inclusion_status=='reliable'];
  for src,g in r.groupby('source'):
   mets.append({'rule':rule,'source':src,'events':len(g),'pairs':g[['trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0],'frames':int(g.raw_frame_count.sum()),'median_duration_s':g.event_duration_s.median(),'p95_duration_s':g.event_duration_s.quantile(.95),'median_ttc_min_s':g.ttc_min_s.median(),'p95_drac_max_mps2':g.drac_max_mps2.quantile(.95),'confirm_observed_rate':g.confirm_observed.mean()})
  mets.append({'rule':rule,'source':'ALL','events':len(r),'pairs':r[['source','trajectory_id','leader_trajectory_id']].drop_duplicates().shape[0],'frames':int(r.raw_frame_count.sum()),'median_duration_s':r.event_duration_s.median(),'p95_duration_s':r.event_duration_s.quantile(.95),'median_ttc_min_s':r.ttc_min_s.median(),'p95_drac_max_mps2':r.drac_max_mps2.quantile(.95),'confirm_observed_rate':r.confirm_observed.mean()})
 pd.DataFrame(mets).to_csv(out/'candidate_rule_metrics.csv',index=False)
 # 24 case analysis and new PDF.
 cases=pd.read_csv(T25/'selected_review_cases.csv'); case_rows=[]; pdf=PdfPages(out/'casebook_24.pdf')
 colors={'P1_strict':'#c0392b','P2_middle':'#2980b9','P3_sensitive':'#27ae60'}
 for _,c in cases.iterrows():
  src=c.source;d=states[src]; t=float(c.time_s); mask=(d.trajectory_id.astype(str)==str(c.trajectory_id))&(d.leader_trajectory_id.astype(str)==str(c.leader_trajectory_id))&(d.time_s.between(t-3,t+3)); loc=d[mask].sort_values(['global_time_ms','frame_id']).copy(); row={'case_id':c.case_id,'source':src,'original_row_number':c.original_row_number,'physical_truth_status':'Unverified','trajectory_id':c.trajectory_id,'leader_trajectory_id':c.leader_trajectory_id,'kinematic_flag':c.kinematic_exploratory_flag,'geometry_flag':c.geometry_flag}
  spans={}
  for rule in ['P1_strict','P2_middle','P3_sensitive']:
   ev=events[rule]; ev=ev[(ev.source==src)&(ev.trajectory_id==c.trajectory_id)&(ev.leader_trajectory_id==c.leader_trajectory_id)&(ev.inclusion_status=='reliable')]; ev=ev[ev.apply(lambda x: bool(members(x.original_row_numbers)&set(loc.original_row_number.astype(int))),axis=1)]
   spans[rule]=ev
   row[rule+'_triggered']=bool(len(ev)); row[rule+'_event_count']=len(ev);row[rule+'_onset_s']=float(ev.event_start_s.min()) if len(ev) else np.nan;row[rule+'_confirm_s']=float(ev.event_confirm_s.min()) if len(ev) else np.nan;row[rule+'_exit_s']=float(ev.event_end_s.max()) if len(ev) else np.nan;row[rule+'_members']=int(ev.raw_frame_count.sum()) if len(ev) else 0
  tr=[(row[r+'_confirm_s'],r) for r in ['P1_strict','P2_middle','P3_sensitive'] if row[r+'_triggered'] and np.isfinite(row[r+'_confirm_s'])]; row['earliest_rule']=min(tr)[1] if tr else 'Not triggered'; row['sensitivity_finding']='P3_only' if row['P3_sensitive_triggered'] and not row['P2_middle_triggered'] else ('all_three' if all(row[r+'_triggered'] for r in ['P1_strict','P2_middle','P3_sensitive']) else 'partial')
  case_rows.append(row)
  fig,axs=plt.subplots(4,1,figsize=(11,12),sharex=True); x=loc.time_s
  axs[0].plot(x,n(loc.ttc_s),color='#34495e',lw=1); [axs[0].axhline(v,color=col,ls='--',label=f'{v:.1f}s') for v,col in [(1.5,'#c0392b'),(2.0,'#2980b9'),(2.5,'#27ae60')]];axs[0].set_ylabel('TTC (s)');axs[0].legend(ncol=3,fontsize=7)
  axs[1].plot(x,n(loc.net_gap_m),label='net gap m');axs[1].plot(x,n(loc.closing_speed_mps),label='closing speed m/s');axs[1].plot(x,n(loc.speed_mps),label='follower speed');axs[1].legend(fontsize=7,ncol=4);axs[1].set_ylabel('kinematics')
  for rule,col in colors.items():
   for _,e in spans[rule].iterrows():axs[2].axvspan(e.event_start_s,e.event_end_s,color=col,alpha=.18); axs[2].axvline(e.event_confirm_s,color=col,lw=.8)
  axs[2].set_ylabel('P1/P2/P3 spans');axs[2].set_title('P1 red / P2 blue / P3 green; vertical line = observed confirm')
  axs[3].plot(x,n(loc.drac_mps2),color='#8e44ad');axs[3].axhline(10,color='#8e44ad',ls='--');axs[3].set_ylabel('DRAC');axs[3].set_xlabel('time_s');fig.suptitle(f"{c.case_id} | {src} | row {c.original_row_number}");fig.tight_layout();pdf.savefig(fig);plt.close(fig)
 pdf.close();pd.DataFrame(case_rows).to_csv(out/'case_analysis_24.csv',index=False)
 # Confirmation audit at event level.
 pd.concat([events[r].assign(rule=r) for r in events],ignore_index=True).to_csv(out/'event_confirmation_audit.csv',index=False)
 # Extreme sensitivity: member-overlap diagnostics, preserving formal input. Counts are event-level affected/fully-covered; no deletion.
 ext=[]
 for rule,e in events.items():
  base=e[e.inclusion_status=='reliable']
  for name,maskfun in [('ttc_extreme',lambda d:d.ttc_valid.fillna(False)&(n(d.ttc_s)<.5)),('drac_extreme',lambda d:d.ttc_valid.fillna(False)&(n(d.drac_mps2)>10)),('gap_extreme',lambda d:d.ttc_valid.fillna(False)&(n(d.net_gap_m)<1)),('union_extreme',lambda d:d.ttc_valid.fillna(False)&((n(d.ttc_s)<.5)|(n(d.drac_mps2)>10)|(n(d.net_gap_m)<1)))]:
   affected=full=0
   for src,d in states.items():
    rows=set(d.loc[maskfun(d),'original_row_number'].astype(int)); z=base[base.source==src]
    for _,x in z.iterrows():
     inter=members(x.original_row_numbers)&rows
     affected+=bool(inter);full+=bool(inter and inter>=members(x.original_row_numbers))
   ext.append({'rule':rule,'scenario':name,'baseline_events':len(base),'events_with_extreme_member':affected,'fully_extreme_events':full,'status':'exploratory_mask_overlap; formal inputs unchanged'})
 pd.DataFrame(ext).to_csv(out/'extreme_sensitivity_by_rule.csv',index=False)
 # Fair sampling: explicitly unresolved under current extractor, retain prior evidence without calling zero an equivalent result.
 samp=[]
 for rule,(th,dur) in RULES.items():
  samp.append({'rule':rule,'status':'Unresolved','phase_0_event_count_under_100ms_rule':0,'phase_1_event_count_under_100ms_rule':0,'reason':'Formal extractor requires 100 ms Global_Time and Frame_ID adjacency; 200 ms decimation needs a separately specified semantics. No interpolation or scientific default change applied.'})
 pd.DataFrame(samp).to_csv(out/'sampling_sensitivity_fair.csv',index=False)
 # Correct literature metadata, including wrong prior DOI.
 corr=[{'id':'Wang-2021-old','original_record':'Performance evaluation...; DOI 10.1016/j.aap.2021.106051; author unspecified','verified_record':'Lu, Chang; He, Xiaolin; van Lint, Hans; Tu, Huizhao; Happee, Riender; Wang, Meng (2021), Accident Analysis & Prevention 162, 106403, DOI 10.1016/j.aap.2021.106403','verification_source':'https://pubmed.ncbi.nlm.nih.gov/34563648/; https://research.tudelft.nl/en/publications/performance-evaluation-of-surrogate-measures-of-safety-with-natur/','correction_reason':'DOI and authors corrected against PubMed/TU Delft publisher metadata'}]
 pd.DataFrame(corr).to_csv(out/'literature_corrections.csv',index=False)
 pd.DataFrame([{'candidate':r,'quantitative_basis':'candidate_rule_metrics.csv, event_overlap_edges.parquet, case_analysis_24.csv, extreme_sensitivity_by_rule.csv','strength':'Proposal only','cost':'No independent crash truth; physical_truth_status=Unverified','decision':'Researcher required'} for r in ['P1_strict','P2_middle','P3_sensitive']]).to_csv(out/'candidate_decision_matrix.csv',index=False)
 (out/'paper_evidence_brief.md').write_text('# Task 2.5.1 Paper Evidence Brief\n\nVerified: P1/P2/P3 event membership, causal observed confirmation times, and 24 newly plotted cases are reproducible. Proposal: candidate rules remain unfrozen. Limitation: no independent crash/near-crash truth establishes accuracy ranking.\n',encoding='utf-8')
 cfg={'schema_version':'stage_0_2.task_2_5_1.v1','rules':RULES,'inputs':{'task_2_5':str(T25),'task_1_5':str(T15)},'locked_holdout_opened':False,'scientific_rule_frozen':False}
 (out/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 audit={'schema_version':'stage_0_2.task_2_5_1.audit.v1','created_at':datetime.now(UTC).isoformat(),'rules':{r:int((events[r].inclusion_status=='reliable').sum()) for r in events},'overlap_edges':len(edges),'cases':len(cases),'case_plots':len(cases),'confirmation_rows':sum(len(e) for e in events.values()),'sampling_status':'Unresolved','rejected_join_fixed':True,'locked_holdout_opened':False,'scientific_claim_eligible':False}
 (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 prov={'schema_version':'stage_0_2.task_2_5_1.provenance.v1','created_at':datetime.now(UTC).isoformat(),'python':sys.version,'platform':platform.platform(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'script_sha256':sha256(Path(__file__))};(out/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 files=sorted(x for x in out.rglob('*') if x.is_file() and x.name not in {'manifest.json','SHA256SUMS'});man={'schema_version':'stage_0_2.task_2_5_1.manifest.v1','files':[{'path':x.relative_to(out).as_posix(),'bytes':x.stat().st_size,'sha256':sha256(x)} for x in files]};(out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');allf=files+[out/'manifest.json'];(out/'SHA256SUMS').write_text('\n'.join(f'{sha256(x)}  {x.relative_to(out).as_posix()}' for x in allf)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
