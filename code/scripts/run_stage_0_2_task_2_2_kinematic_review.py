"""Stage 0.2 task 2.2: continuity, kinematic and geometry diagnostics.

Read-only diagnostics over the frozen task 2.1 case/local-trajectory package.
No measurement rule, event table, or historical label is changed.
"""
from __future__ import annotations

import argparse, hashlib, json, platform, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261022
EXPECTED_CASES = 447
DT = 0.1

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def finite(x): return pd.to_numeric(x, errors='coerce').replace([np.inf,-np.inf],np.nan)

def runs(mask, contiguous):
    mask=np.asarray(mask,dtype=bool); edge=np.asarray(contiguous,dtype=bool)
    lengths=[]; start=None
    for i,v in enumerate(mask):
        connected=i>0 and i<len(edge) and bool(edge[i])
        if v and (start is None or not connected):
            if start is not None: lengths.append(i-start)
            start=i
        elif not v and start is not None:
            lengths.append(i-start); start=None
    if start is not None: lengths.append(len(mask)-start)
    return int(mask.sum()), max(lengths,default=0), len(lengths)
def diagnose(local: pd.DataFrame, case: pd.Series) -> dict:
    f=local[local.local_role.eq('follower')].sort_values(['global_time_ms','frame_id']).copy()
    pair=f[f.leader_trajectory_id.astype('string').eq(str(case.leader_trajectory_id))].copy()
    pair['dt']=finite(pair.global_time_ms).diff()/1000
    pair['df']=finite(pair.frame_id).diff()
    contiguous=(pair.dt.sub(DT).abs()<1e-9)&pair.df.eq(1)
    # Sequence continuity is measured only on the same follower/leader pair.
    obs_total,obs_long,obs_runs=runs(np.ones(len(pair),bool),contiguous)
    obs_breaks=int((~contiguous.iloc[1:]).sum()) if len(pair)>1 else 0
    risk=pair.ttc_valid.fillna(False)
    extreme=(risk & (finite(pair.ttc_s)<2)) | (risk & (finite(pair.drac_mps2)>10))
    ttc05=risk & (finite(pair.ttc_s)<.5)
    ttc20=risk & (finite(pair.ttc_s)<2)
    drac10=risk & (finite(pair.drac_mps2)>10)
    risk_cont=contiguous & contiguous.shift(-1,fill_value=False)
    def stats(m):
        z=pair[m].copy(); return {'rows':int(len(z)),'longest_contiguous_frames':int(runs(m & contiguous,contiguous)[1]),'runs':int(runs(m & contiguous,contiguous)[2]),'min_ttc_s':float(finite(z.ttc_s).min()) if finite(z.ttc_s).notna().any() else None,'max_drac_mps2':float(finite(z.drac_mps2).max()) if finite(z.drac_mps2).notna().any() else None}
    # Difference diagnostics are exploratory; report errors rather than assert physical truth.
    dt=finite(pair.global_time_ms).diff()/1000
    vx=finite(pair.x_m).diff()/dt; vy=finite(pair.y_m).diff()/dt
    pos_speed=np.sqrt(vx**2+vy**2)
    speed_err=pos_speed-finite(pair.speed_mps)
    accel_diff=finite(pair.speed_mps).diff()/dt-finite(pair.acceleration_mps2)
    finite_speed=speed_err.replace([np.inf,-np.inf],np.nan).dropna()
    finite_acc=accel_diff.replace([np.inf,-np.inf],np.nan).dropna()
    # No normative physical cutoff: 5 m/s and 5 m/s2 are declared exploratory flags.
    kin_flag=bool((finite_speed.abs()>5).any() or (finite_acc.abs()>5).any())
    gap=finite(pair.net_gap_m); head=finite(pair.raw_space_headway_ft)*0.3048
    # The local package intentionally does not copy the matched leader length;
    # therefore a non-tautological headway/length/gap geometry residual cannot
    # be computed here and remains Unverified.
    geom_available=False
    geom_resid=pd.Series(dtype=float)
    geom_flag=False
    risk_stats={'ttc_lt_0_5':stats(ttc05),'ttc_lt_2_0':stats(ttc20),'drac_gt_10':stats(drac10),'extreme':stats(extreme)}
    extreme_rows=int(extreme.sum()); extreme_cont=bool((extreme & contiguous & extreme.shift(-1,fill_value=False)).any())
    if len(pair)<2: continuity='unable_to_determine'
    elif obs_breaks: continuity='boundary_limited_or_gapped'
    elif extreme_rows==0: continuity='no_extreme_state_in_pair_window'
    elif extreme_rows==1: continuity='single_frame_spike'
    elif extreme_cont: continuity='multi_frame_continuous'
    else: continuity='intermittent'
    applicable='applicable' if len(pair)>=2 else 'not_applicable'
    labels=[]
    if kin_flag: labels.append('kinematic_exploratory_flag')
    if geom_flag: labels.append('geometry_residual_flag')
    if obs_breaks: labels.append('observation_gap_or_boundary')
    if not geom_available: labels.append('geometry_unverified_missing_reference')
    if continuity=='single_frame_spike': labels.append('single_frame_extreme')
    if continuity=='multi_frame_continuous': labels.append('continuous_extreme')
    if continuity=='intermittent': labels.append('intermittent_extreme')
    if not labels: labels=['no_automatic_conflict_found']
    # Overall label reflects implemented checks; geometry evidence is retained
    # separately as Unverified rather than downgrading every case to E.
    # Exploratory threshold flags are evidence for C/manual review, never an
    # automatic B (B requires an explicit, validated contradiction rule).
    auto='E' if len(pair)<2 else ('C' if kin_flag or geom_flag or extreme_rows else 'D')
    return {'pair_rows':len(pair),'pair_start_s':float(pair.time_s.min()) if len(pair) else None,'pair_end_s':float(pair.time_s.max()) if len(pair) else None,'observation_contiguous':not bool(obs_breaks),'observation_breaks':obs_breaks,'risk_state_continuity':continuity,'ttc_lt_0_5_rows':int(ttc05.sum()),'ttc_lt_2_0_rows':int(ttc20.sum()),'drac_gt_10_rows':int(drac10.sum()),'extreme_rows':extreme_rows,'extreme_longest_contiguous_frames':int(runs(extreme & contiguous,contiguous)[1]),'risk_contiguous':bool((extreme & contiguous).any()),'kinematic_check_applicability':applicable,'position_speed_max_abs_error_mps':float(finite_speed.abs().max()) if len(finite_speed) else None,'speed_acceleration_max_abs_error_mps2':float(finite_acc.abs().max()) if len(finite_acc) else None,'kinematic_exploratory_flag':kin_flag,'geometry_check_applicability':'applicable' if geom_available else 'unverified_missing_fields','geometry_residual_max_abs_m':float(geom_resid.abs().dropna().max()) if geom_resid.notna().any() else None,'geometry_flag':geom_flag,'net_gap_nonpositive_rows':int((gap<=0).fillna(False).sum()),'risk_stats_json':json.dumps(risk_stats,ensure_ascii=False),'automatic_diagnostic_labels':';'.join(labels),'automatic_quality_label':auto,'manual_judgement':'','manual_basis':'','unable_to_judge_reason':'','reviewer_notes':''}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=ROOT); ap.add_argument('--input-dir',type=Path); ap.add_argument('--output-dir',type=Path,required=True); a=ap.parse_args(); root=a.repo_root.resolve()
    inp=(a.input_dir or root/'code/outputs/formal/calibration/stage_0_2_task_2_1_extreme_review_20261011_r4').resolve(); out=a.output_dir.resolve(); out.mkdir(parents=True,exist_ok=False)
    cases=pd.read_csv(inp/'review_cases.csv'); assert len(cases)==EXPECTED_CASES, len(cases)
    rows=[]
    for _,case in cases.iterrows():
        p=inp/f"local_{case.source}_{int(case.original_row_number)}.parquet"; d=pd.read_parquet(p); r=diagnose(d,case); r.update({'case_id':f"{case.source}:{int(case.original_row_number)}",'source':case.source,'original_row_number':int(case.original_row_number),'trajectory_id':case.trajectory_id,'leader_trajectory_id':case.leader_trajectory_id,'vehicle_id':case.vehicle_id,'leader_id':case.leader_id,'time_s':case.time_s,'review_categories':case.review_categories,'historical_quality_class':case.quality_class,'baseline_event_id':case.baseline_event_id,'baseline_event_position':case.baseline_event_position,'ttc_s':case.ttc_s,'drac_mps2':case.drac_mps2,'net_gap_m':case.net_gap_m,'closing_speed_mps':case.closing_speed_mps}); rows.append(r)
    diag=pd.DataFrame(rows); diag.to_csv(out/'case_diagnostics.csv',index=False)
    baseline=pd.read_csv(root/'code/outputs/formal/calibration/stage_0_2_task_2_2_kinematic_review_20261010_r6/case_diagnostics.csv')
    comparison=baseline[['case_id','risk_state_continuity','extreme_longest_contiguous_frames','automatic_diagnostic_labels','automatic_quality_label']].merge(diag[['case_id','risk_state_continuity','extreme_longest_contiguous_frames','automatic_diagnostic_labels','automatic_quality_label','baseline_event_id']],on='case_id',suffixes=('_old','_new'))
    comparison['continuity_changed']=comparison.risk_state_continuity_old.ne(comparison.risk_state_continuity_new)
    comparison['reason']=comparison.continuity_changed.map({True:'corrected adjacent same-pair edge requirement',False:'no classification change'})
    comparison.to_csv(out/'r6_vs_221_case_comparison.csv',index=False)
    # Explicit per-source quota slots: ordinary, threshold, TTC, DRAC,
    # non-positive gap, near-zero gap, continuity, and extreme.
    selected=[]
    for src,g in diag.groupby('source',sort=True):
        g=g.sort_values(['ttc_s','original_row_number'],na_position='last'); chosen=[]; used=set()
        strata=[('ordinary_valid',1),('threshold_near_',1),('ttc_lt_0_5',2),('drac_gt_10',2),('nonpositive_gap',1),('near_zero_positive_gap',1)]
        for cat,n in strata:
            pool=g[g.review_categories.str.contains(cat)]
            for _,row in pool.iterrows():
                key=(row.trajectory_id,row.leader_trajectory_id,row.baseline_event_id)
                if key in used: continue
                chosen.append(row); used.add(key)
                if sum(1 for z in chosen if cat in str(z.review_categories))>=n: break
        pool=g[g.risk_state_continuity.isin(['single_frame_spike','multi_frame_continuous','intermittent','boundary_limited_or_gapped'])]
        for _,row in pool.iterrows():
            if len(chosen)>=11: break
            key=(row.trajectory_id,row.leader_trajectory_id,row.baseline_event_id)
            if key not in used: chosen.append(row); used.add(key)
        pool=g[g.review_categories.str.contains('ttc_lt_0_5|drac_gt_10|near_zero_positive_gap')]
        for _,row in pool.iterrows():
            if len(chosen)>=12: break
            key=(row.trajectory_id,row.leader_trajectory_id,row.baseline_event_id)
            if key not in used: chosen.append(row); used.add(key)
        for _,row in g.iterrows():
            if len(chosen)>=12: break
            key=(row.trajectory_id,row.leader_trajectory_id,row.baseline_event_id)
            if key not in used: chosen.append(row); used.add(key)
        if src=='lankershim__complete' and not any(int(row.original_row_number)==31245 for row in chosen):
            special=g[g.original_row_number.eq(31245)]
            if len(special): chosen[-1]=special.iloc[0]
        selected.extend(chosen[:12])
    sel=pd.DataFrame(selected); sel['selection_seed']=SEED; sel['selection_reason']='explicit per-source quota; deterministic strata; deduplicated follower-leader-event'; sel.to_csv(out/'representative_cases.csv',index=False)
    coverage=[]
    for src,g in sel.groupby('source'):
        for cat in ['ordinary_valid','threshold_','ttc_lt_0_5','drac_gt_10','nonpositive_gap','near_zero_positive_gap']:
            coverage.append({'source':src,'stratum':cat,'n':int(g.review_categories.str.contains(cat).sum()),'covered':bool(g.review_categories.str.contains(cat).any())})
        for cat in ['single_frame_spike','multi_frame_continuous','boundary_limited_or_gapped','intermittent']:
            coverage.append({'source':src,'stratum':cat,'n':int(g.risk_state_continuity.eq(cat).sum()),'covered':bool(g.risk_state_continuity.eq(cat).any())})
    pd.DataFrame(coverage).to_csv(out/'coverage_matrix.csv',index=False)
    template=sel[['case_id','source','original_row_number','trajectory_id','leader_trajectory_id','review_categories','automatic_quality_label','automatic_diagnostic_labels']].copy(); template['check_item']=''; template['manual_judgement']=''; template['basis']=''; template['unable_to_determine_reason']=''; template['reviewer_notes']=''; template.to_csv(out/'manual_review_template.csv',index=False)
    summary=[]
    for label in ['single_frame_spike','multi_frame_continuous','intermittent','boundary_limited_or_gapped','unable_to_determine']:
        n=int(diag.risk_state_continuity.eq(label).sum()); summary.append({'category':label,'n':n,'denominator':len(diag),'proportion':n/len(diag)})
    pd.DataFrame(summary).to_csv(out/'continuity_summary.csv',index=False)
    with PdfPages(out/'representative_casebook.pdf') as pdf:
      for _,x in sel.iterrows():
        d=pd.read_parquet(inp/f"local_{x.source}_{int(x.original_row_number)}.parquet"); f=d[d.local_role.eq('follower') & d.leader_trajectory_id.astype('string').eq(str(x.leader_trajectory_id))].sort_values('time_s').copy(); l=d[d.local_role.eq('leader')]; edge=finite(f.global_time_ms).diff().eq(100)&finite(f.frame_id).diff().eq(1); f.loc[(~edge) & (np.arange(len(f)) != 0), ['ttc_s','drac_mps2','net_gap_m','closing_speed_mps']]=np.nan; fig,ax=plt.subplots(3,1,figsize=(10,8),sharex=True); ax[0].plot(f.time_s,f.ttc_s.replace([np.inf,-np.inf],np.nan),label='TTC (pair)'); ax[0].plot(f.time_s,f.drac_mps2,label='DRAC (pair)'); ax[0].legend(); ax[1].plot(f.time_s,f.net_gap_m,label='net gap (pair)'); ax[1].plot(f.time_s,f.closing_speed_mps,label='closing (pair)'); ax[1].legend(); ax[2].plot(f.time_s,f.speed_mps,label='follower speed'); ax[2].plot(l.time_s,l.speed_mps,label='leader speed'); ax[2].plot(f.time_s,f.acceleration_mps2,label='follower accel'); ax[2].legend(); [q.axvline(x.time_s,color='k',lw=.7) for q in ax]; fig.suptitle(f"{x.case_id} | {x.review_categories} | {x.risk_state_continuity} | auto {x.automatic_quality_label}"); fig.tight_layout(); pdf.savefig(fig); plt.close(fig)
    inputs=[inp/'review_cases.csv',inp/'manifest.json',inp/'SHA256SUMS']; config={'schema_version':'stage_0_2.task_2_2.review.v1','seed':SEED,'cases':len(diag),'representative_cases':len(sel),'exploratory_thresholds':{'ttc_lt_0_5_s':0.5,'ttc_lt_2_s':2.0,'drac_gt_10_mps2':10.0,'position_speed_error_mps':5.0,'speed_acceleration_error_mps2':5.0},'locked_holdout_opened':False,'scientific_claim_eligible':False}; (out/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit={'schema_version':'stage_0_2.task_2_2.audit.v1','created_at':datetime.now(UTC).isoformat(),'input_sha256':{str(p.relative_to(inp)):sha256(p) for p in inputs if p.exists()},'cases':len(diag),'continuity_counts':{str(k):int(v) for k,v in diag.risk_state_continuity.value_counts().items()},'automatic_quality_counts':{str(k):int(v) for k,v in diag.automatic_quality_label.value_counts().items()},'representative_cases':len(sel),'candidate_event_cases':int(diag.baseline_event_position.eq('member').sum()),'manual_review_completed':False}; (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prov={'schema_version':'stage_0_2.task_2_2.provenance.v1','created_at':datetime.now(UTC).isoformat(),'python':sys.version,'platform':platform.platform(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'script_sha256':sha256(Path(__file__))}; (out/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files=sorted(p for p in out.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'}); man={'schema_version':'stage_0_2.task_2_2.manifest.v1','files':[{'path':str(p.relative_to(out)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in files]}; (out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); allf=files+[out/'manifest.json']; (out/'SHA256SUMS').write_text('\n'.join(f'{sha256(p)}  {p.relative_to(out).as_posix()}' for p in allf)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
