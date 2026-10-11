"""Standalone agreed-design numerical audit; no production pipeline changes."""
import json, hashlib, argparse, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]

def weighted_median(x,w):
 x=np.asarray(x,float); w=np.asarray(w,float); ok=np.isfinite(x)&np.isfinite(w)&(w>0)
 x=x[ok]; w=w[ok]; order=np.argsort(x,kind="stable"); x=x[order]; w=w[order]
 return float(x[np.searchsorted(np.cumsum(w),w.sum()/2)]) if len(x) else float("nan")

def contribution(status,inside,reliable,ttc,tau):
 if inside is False and reliable: return (0.,0.)
 if inside is None or not reliable: return (0.,1.)
 if status=="not_applicable": return (0.,0.)
 if status=="valid" and ttc is not None and np.isfinite(ttc) and ttc>0:
  r=float(np.exp(-ttc/tau)); return (r,r)
 return (0.,1.)

def burden(vehicles,window_s):
 if window_s<=0 or not vehicles: raise ValueError("fixed vehicles/window required")
 intervals=[]
 for observations in vehicles:
  covered=sum(dt for dt,l,u in observations)
  if covered>window_s+1e-9: raise ValueError("overlapping/excess time")
  intervals.append((sum(dt*l for dt,l,u in observations)/window_s,(sum(dt*u for dt,l,u in observations)+window_s-covered)/window_s))
 return tuple(np.mean(intervals,axis=0))

def effect_interval(r11,r10,r01,r00):
 return (r11[0]-r10[1]-r01[1]+r00[0],r11[1]-r10[0]-r01[0]+r00[1])

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',required=True,type=Path); out=ap.parse_args().output_dir; out.mkdir(exist_ok=False)
 source_dir=ROOT/'code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4/states'
 summaries=[]; statuses=[]; cache=[]; inputs=[]
 for p in sorted(source_dir.glob('*.parquet')):
  d=pd.read_parquet(p).sort_values(['trajectory_id','global_time_ms','frame_id']).reset_index(drop=True)
  src=p.stem.removeprefix('ngsim_'); inputs.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p)})
  reliable=d.leader_matched.fillna(False)&~d.identity_uncertain.fillna(True)&~d.leader_identity_uncertain.fillna(True)
  adjacent=d.trajectory_id.eq(d.trajectory_id.shift())&d.leader_trajectory_id.eq(d.leader_trajectory_id.shift())&d.global_time_ms.diff().eq(100)&d.frame_id.diff().eq(1)&d.diagnostic_clock_anchor_ms.eq(d.diagnostic_clock_anchor_ms.shift())&~d.identity_break.fillna(True)&~d.observation_gap.fillna(True)
  valid=reliable&d.ttc_valid.fillna(False)&np.isfinite(d.ttc_s)&(d.ttc_s>0)&d.measurement_status.eq('valid')
  pair_edge=adjacent&reliable&reliable.shift(fill_value=False)
  edge=adjacent&valid&valid.shift(fill_value=False)
  w=(edge.astype(float)+edge.shift(-1,fill_value=False).astype(float))*.05
  x=d.ttc_s[valid].to_numpy(float); weights=w[valid].to_numpy(float)
  extreme=((d.ttc_s<.5)|(d.drac_mps2>10)|(d.net_gap_m<1))[valid].to_numpy(bool)
  clean=~extreme
  clean_edge=adjacent&(valid&~((d.ttc_s<.5)|(d.drac_mps2>10)|(d.net_gap_m<1)))
  clean_edge=clean_edge&clean_edge.shift(fill_value=False)
  cw=(clean_edge.astype(float)+clean_edge.shift(-1,fill_value=False).astype(float))*.05
  m=weighted_median(x,weights)
  summaries.append({'source':src,'states':len(d),'reliable_valid_closing_rows':int(valid.sum()),'reliable_following_edge_time_s':float(pair_edge.sum()*.1),'closing_edge_time_s':float(weights.sum()),'ttc_weighted_median_s':m,'ttc_row_median_s':float(np.median(x)),'extreme_rows':int(extreme.sum()),'median_excluding_flagged_resegmented_s':weighted_median(d.ttc_s,cw),'identity_uncertain_fraction':float(d.identity_uncertain.fillna(True).mean()),'observation_gap_fraction':float(d.observation_gap.fillna(True).mean())})
  for status,g in d.groupby('measurement_status',dropna=False): statuses.append({'source':src,'status':status,'rows':len(g),'fraction':len(g)/len(d)})
  cache.append((src,x,weights,extreme))
  del d
 tau=float(np.mean(sorted(z['ttc_weighted_median_s'] for z in summaries)[1:3]))
 risk=[]
 for src,x,w,flag in cache:
  for scale in [.5,1,2]:
   rho=np.exp(-x/(tau*scale)); risk.append({'source':src,'tau_scale':scale,'tau_s':tau*scale,'closing_time_s':float(w.sum()),'conditional_closing_time_weighted_rho':float(np.dot(rho,w)/w.sum()),'rho_row_p95':float(np.quantile(rho,.95)),'rho_row_p99':float(np.quantile(rho,.99)),'rho_gt_0_9_time_fraction':float(w[rho>.9].sum()/w.sum()),'conditional_rho_excluding_flagged':float(np.dot(rho[~flag],w[~flag])/w[~flag].sum()),'fixed_target_region_burden':'Unresolved: no fixed target cohort/region/window in NGSIM audit'})
 pd.DataFrame(summaries).to_csv(out/'tau_calibration.csv',index=False); pd.DataFrame(statuses).to_csv(out/'measurement_status.csv',index=False); pd.DataFrame(risk).to_csv(out/'continuous_risk_reference.csv',index=False)
 ev=pd.read_csv(ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2/event_confirmation_audit.csv')
 ev[ev.rule.eq('P2_middle')].to_parquet(out/'p2_observed_events.parquet',index=False)
 metrics=pd.read_csv(ROOT/'code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2/candidate_rule_metrics.csv'); metrics.to_csv(out/'rule_comparison.csv',index=False)
 config={'weighting':'only reliable 100ms same-pair same-clock edges; .05s allocated to each endpoint; no extrapolation or interpolation','tau_rule':'mean of middle two source time-weighted TTC medians','extreme_pressure_test':'TTC<0.5 or DRAC>10 or gap<1; not formal exclusion','scope':'four approved calibration sources only','production_pipeline_modified':False}
 audit={'tau_s':tau,'source_medians_s':[z['ttc_weighted_median_s'] for z in summaries],'p2_events':int(ev.rule.eq('P2_middle').sum()),'scientific_gate_passed':False,'protocol_lock_created':False,'fixed_region_burden_status':'Unresolved','inputs':inputs}
 for name,obj in [('config.json',config),('audit.json',audit),('provenance.json',{'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'script_sha256':digest(Path(__file__)),'inputs':inputs})]: (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 files=[{'path':p.name,'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir())]
 (out/'manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n',encoding='utf-8')
 (out/'SHA256SUMS').write_text('\n'.join(digest(p)+'  '+p.name for p in sorted(out.iterdir()) if p.name!='SHA256SUMS')+'\n',encoding='utf-8')
 print(json.dumps(audit,ensure_ascii=True))
if __name__=='__main__': main()
