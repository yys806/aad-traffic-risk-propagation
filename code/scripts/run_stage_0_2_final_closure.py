"""Stage 0.2 final closure: full-sequence independent and sampling audit.

No holdout, pipeline defaults or scientific decisions are changed.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, platform, subprocess, sys, shutil
from datetime import UTC, datetime
from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'code/src'));sys.path.insert(0,str(ROOT/'code/scripts'))
from riskprop.formal_risk_measurement import P2_FORMAL_CONFIG, extract_formal_source_events
from stage_0_2_closure_analysis import PAIR, SCOPE, ordered_states, sequence_events, event_edges, correspondence_summary
BASE=ROOT/'code/outputs/formal/calibration'
T15=BASE/'stage_0_2_task_1_5_20261010_r4';T251=BASE/'stage_0_2_task_2_5_1_20261011_r2';DEC=BASE/'stage_0_2_decision_ratification_20261011_r1';RHO=BASE/'stage_0_2_rho_timescale_validation_20261011_r1';T23=BASE/'stage_0_2_task_2_3_20261011_r3';T221=BASE/'stage_0_2_task_2_2_1_20261011_r9';T252=BASE/'stage_0_2_task_2_5_2_20261011_r1'
RULES={'P1_strict':(1.5,.3),'P2_middle':(2.,.2),'P3_sensitive':(2.5,.1)}
TAU=15.364279197080283

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def q(x,w,p=.5):
    x,w=np.asarray(x,float),np.asarray(w,float);good=np.isfinite(x)&(w>0)
    x,w=x[good],w[good];order=np.argsort(x,kind='stable');x,w=x[order],w[order]
    return float(x[np.searchsorted(np.cumsum(w),p*w.sum())]) if len(x) else np.nan

def parse_events(path):
    f=pd.read_csv(path);f=f[f.inclusion_status.eq('reliable')].copy();f['original_row_numbers']=f.original_row_numbers.map(ast.literal_eval);return f

def event_key(e):return (*[str(e[k]) for k in PAIR],tuple(sorted(map(int,e.original_row_numbers))))

def audit_event_match(a,b,source,rule,label):
    reference={event_key(e):e for _,e in a.iterrows()}; new={event_key(e):e for _,e in b.iterrows()}
    common=reference.keys()&new.keys(); rows=[]
    for key in sorted(reference.keys()|new.keys()):
        x,y=reference.get(key),new.get(key)
        row={'source':source,'rule':rule,'comparison':label,'member_hash':hashlib.sha256(str(key).encode()).hexdigest(),'status':'matched' if x is not None and y is not None else 'missing' if y is None else 'added'}
        for col in ['event_start_s','event_confirm_s','event_end_s','raw_frame_count','ttc_min_s','drac_max_mps2']:
            row[col+'_delta']=float(y[col])-float(x[col]) if x is not None and y is not None else np.nan
        rows.append(row)
    return rows,{'source':source,'rule':rule,'comparison':label,'reference_events':len(a),'new_events':len(b),'exact_member_scope_matches':len(common),'missing':len(reference.keys()-new.keys()),'added':len(new.keys()-reference.keys())}

def collect_inventory():
    rows=[]
    # Existing sealed outputs: verify all hashes and keep limitations, rather than
    # silently rewriting stale historical artifacts.
    for directory in [T15,T251,DEC,RHO,T23,T221,T252,BASE/'stage_0_2_task_2_4_20261011_r2']:
        sums=directory/'SHA256SUMS'
        for line in sums.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():continue
            digest,name=line.split(maxsplit=1);name=name.strip().lstrip('*');p=directory/name
            actual=sha(p) if p.is_file() else None
            rows.append({'package':directory.name,'file':name,'path':str(p.relative_to(ROOT)),'expected_sha256':digest,'actual_sha256':actual,'status':'Verified' if actual==digest else 'Blocked'})
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=BASE/'stage_0_2_final_closure_20261012_r4');args=ap.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    reference=parse_events(T251/'event_confirmation_audit.csv');case447=pd.read_csv(T23/'case_diagnostics.csv'); selected48=pd.read_csv(T221/'representative_cases.csv'); selected11=pd.read_csv(T252/'key_difference_cases.csv')
    inventory=collect_inventory();pd.DataFrame(inventory).to_csv(out/'historical_sha256_audit.csv',index=False)
    samples=[];sampling_edges=[];comparisons=[];matches=[];case_checks=[];tau=[];risks=[];exposures=[];statesummary=[];reasons=[];all_events=[];extremes=[];overlaps=[];psummary=[];transitions=[];diagnostics=[]
    for path in sorted((T15/'states').glob('*.parquet')):
        source=path.stem.removeprefix('ngsim_'); print('source',source,flush=True)
        # Load one approved source at a time. Never load all 5.7 million rows.
        original=pd.read_parquet(path)
        raw,formal,rejected=extract_formal_source_events(original,P2_FORMAL_CONFIG,return_diagnostics=True)
        diagnostics.append({'source':source,'raw_events':len(raw),'reliable_events':len(formal),'rejected_events':len(rejected),'confirmation_observed_and_message_aligned':bool(formal.event_confirm_s.eq(formal.message_earliest_generation_s).all()),'rejected_reason_counts':rejected.rejection_reason.value_counts().to_dict()})
        formal['rule']='P2_middle';formal['source']=source;all_events.append(formal)
        d=ordered_states(original); del original
        valid=d._reliable&d.ttc_valid.fillna(False)&d.measurement_status.eq('valid')&np.isfinite(d.ttc_s)&d.ttc_s.gt(0)
        closed_link=d._link&valid&valid.shift(fill_value=False)
        weights=(closed_link.astype(float)+closed_link.shift(-1,fill_value=False).astype(float))*.05
        flags=(d.ttc_s.lt(.5)|d.drac_mps2.gt(10)|d.net_gap_m.lt(1))&valid
        clean=valid&~flags;clean_link=d._link&clean&clean.shift(fill_value=False);cw=(clean_link.astype(float)+clean_link.shift(-1,fill_value=False).astype(float))*.05
        follow_s=float(d._link.sum()*.1);closing_s=float(weights.sum());median=q(d.ttc_s,weights)
        tau.append({'source':source,'state_rows':len(d),'reliable_valid_closing_rows':int(valid.sum()),'reliable_following_time_s':follow_s,'closing_time_s':closing_s,'ttc_weighted_median_s':median,'time_weighted_median_screened_s':q(d.ttc_s,cw),'diagnostic_clock_missing_rows':int(d.diagnostic_clock_anchor_ms.isna().sum()),'identity_uncertain_rows':int(d.identity_uncertain.fillna(True).sum()),'observation_gap_rows':int(d.observation_gap.fillna(True).sum())})
        base_ref=reference[(reference.source==source)&reference.rule.eq('P2_middle')]
        rm,sm=audit_event_match(base_ref,formal,source,'P2_middle','formal_v2_vs_task251');matches.extend(rm);comparisons.append(sm)
        pair_count=len(formal[PAIR].drop_duplicates());followers=len(formal[SCOPE+['trajectory_id']].drop_duplicates())
        psummary.append({'source':source,'event_count':len(formal),'unique_followers':followers,'unique_pairs':pair_count,'duration_median_s':float((formal.event_end_s-formal.event_start_s).median()),'confirm_delay_median_s':float((formal.event_confirm_s-formal.event_start_s).median()),'exit_reason_counts':json.dumps(formal.exit_reason.value_counts().to_dict())})
        exposures.append({'source':source,'reliable_following_edge_seconds':follow_s,'reliable_closing_edge_seconds':closing_s,'p2_events':len(formal),'diagnostic_events_per_1000_following_edge_seconds':len(formal)/follow_s*1000,'diagnostic_events_per_1000_closing_edge_seconds':len(formal)/closing_s*1000,'independent_units':'source-scoped follower/leader trajectories; events are repeated observations','official_rate_denominator_selected':False})
        for status,g in d.groupby('measurement_status',dropna=False):statesummary.append({'source':source,'measurement_status':str(status),'mapped_status':'not_measurable' if status=='missing' else str(status),'rows':len(g),'fraction_of_source_states':len(g)/len(d)})
        for (status,reason),g in d.groupby(['measurement_status','missing_reason'],dropna=False):reasons.append({'source':source,'status':str(status),'missing_reason':str(reason),'rows':len(g)})
        previous=d.shift();adjacent=pd.Series(True,index=d.index)
        for k in SCOPE+['trajectory_id','diagnostic_clock_anchor_ms']:adjacent &= d[k].notna()&previous[k].notna()&d[k].eq(previous[k])
        adjacent &= d.global_time_ms.diff().eq(100)&d.frame_id.diff().eq(1)&~d.identity_break.fillna(True)&~d.observation_gap.fillna(True)
        pairs=pd.DataFrame({'from_status':previous.measurement_status[adjacent],'to_status':d.measurement_status[adjacent]})
        for (a,b),n in pairs.value_counts().items():transitions.append({'source':source,'from_status':a,'to_status':b,'adjacent_observed_edges':int(n),'time_s':float(n*.1)})
        for scale in [.5,1.,2.]:
            rho=np.exp(-pd.to_numeric(d.ttc_s,errors='coerce').to_numpy(float)/(TAU*scale)); rho[~valid.to_numpy(bool)]=np.nan
            finite=np.isfinite(rho);w=weights.to_numpy(float);s=float(np.nansum(rho*w))
            risks.append({'source':source,'tau_scale':scale,'tau_s':TAU*scale,'closing_edge_seconds':closing_s,'conditional_rho_mean':s/closing_s,'rho_p50':q(rho,w,.5),'rho_p95':q(rho,w,.95),'rho_p99':q(rho,w,.99),'rho_integral_s':s,'screened_closing_seconds':float(cw.sum()),'conditional_rho_mean_screened_resegmented':float(np.nansum(rho*cw.to_numpy(float))/cw.sum()),'conditional_closed_scope_not_fixed_region_burden':True})
        # Independent 100 ms implementation must match members, not only totals.
        rule_events={}
        for rule,(threshold,duration) in RULES.items():
            ref=reference[(reference.source==source)&reference.rule.eq(rule)]
            e,coverage=sequence_events(d,threshold,duration)
            rm,sm=audit_event_match(ref,e,source,rule,'independent_100ms_vs_task251');matches.extend(rm);comparisons.append(sm);rule_events[rule]=e
            samples.append({'source':source,'rule':rule,'step_ms':100,'phase_ms':0,**coverage,**correspondence_summary(e,e,event_edges(e,e))})
            screened,scov=sequence_events(d,threshold,duration,mask_extreme=True)
            edges=event_edges(e,screened); summary=correspondence_summary(e,screened,edges);extremes.append({'source':source,'rule':rule,'scenario':'union_TTC_lt0.5_DRAC_gt10_gap_lt1','original_preserved':True,**summary})
            for phase in [0,100]:
                sampled,cov=sequence_events(d,threshold,duration,step_ms=200,phase_ms=phase)
                edges=event_edges(e,sampled);summary=correspondence_summary(e,sampled,edges);samples.append({'source':source,'rule':rule,'step_ms':200,'phase_ms':phase,**cov,**summary})
                for frame in (edges,):
                    frame['source']=source;frame['rule']=rule;frame['step_ms']=200;frame['phase_ms']=phase
                    if len(frame):
                        frame['reference_event_key']=frame.a.map(e.event_key);frame['sampled_event_key']=frame.b.map(sampled.event_key)
                    sampling_edges.append(frame)
                sampled['source']=source;sampled['rule']=rule;sampled['step_ms']=200;sampled['phase_ms']=phase
                sampled.to_parquet(out/f'sampled_events_{source}_{rule}_{phase}.parquet',index=False)
        for ra,rb in [('P1_strict','P2_middle'),('P2_middle','P3_sensitive'),('P1_strict','P3_sensitive')]:
            edge=event_edges(rule_events[ra],rule_events[rb]);overlaps.append({'source':source,'rule_a':ra,'rule_b':rb,**correspondence_summary(rule_events[ra],rule_events[rb],edge)})
        # Recheck exact centers and math of all fixed 447 cases; deterministic
        # priority remains an objective flag, never a physical-truth verdict.
        origidx=d.set_index('original_row_number',drop=False)
        pevents=rule_events['P2_middle']; membership={}
        for _,ev in pevents.iterrows():
            for orig in ev.original_row_numbers:membership[int(orig)]=ev.event_key
        for _,c in case447[case447.source.eq(source)].iterrows():
            orig=int(c.original_row_number);center=origidx.loc[[orig]]
            exact=center[(center.trajectory_id==c.trajectory_id)&(center.leader_trajectory_id==c.leader_trajectory_id)&(center.global_time_ms==c.global_time_ms)&(center.frame_id==c.frame_id)]
            unique=len(exact)==1;r=exact.iloc[0] if unique else None
            ttc_ok=drac_ok=None
            if unique and bool(r.ttc_valid) and r.net_gap_m>0 and r.closing_speed_mps>0:
                ttc_ok=bool(np.isclose(r.ttc_s,r.net_gap_m/r.closing_speed_mps,rtol=1e-9,atol=1e-9));drac_ok=bool(np.isclose(r.drac_mps2,r.closing_speed_mps**2/(2*r.net_gap_m),rtol=1e-9,atol=1e-9))
            is48=bool(((selected48.source==source)&(selected48.original_row_number==orig)).any());is11=bool(((selected11.source==source)&(selected11.center_original_row_number==orig)).any())
            affects=orig in membership
            case_checks.append({'case_id':c.case_id,'source':source,'original_row_number':orig,'unique_center':unique,'ttc_formula_pass':ttc_ok,'drac_formula_pass':drac_ok,'case_in_48':is48,'case_in_11':is11,'p2_center_member':affects,'p2_event_key':membership.get(orig),'kinematic_flag':c.kinematic_exploratory_flag,'geometry_check':'same-source formula only; independent reference unavailable','physical_truth_status':'Unverified','review_priority':1 if affects and (bool(c.kinematic_exploratory_flag) or (r is not None and r.ttc_valid and (r.ttc_s<.5 or r.drac_mps2>10 or r.net_gap_m<1))) else 2 if is48 or is11 else 3,'manual_physical_judgement':''})
        print('done',source,'P2',len(formal),flush=True)
        del d,origidx
    pd.concat(all_events,ignore_index=True).to_parquet(out/'p2_formal_events.parquet',index=False)
    pd.DataFrame(transitions).to_csv(out/'measurement_status_transitions.csv',index=False)
    (out/'p2_online_diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n',encoding='utf-8')
    for name,rows in [('p2_summary.csv',psummary),('event_member_time_comparison.csv',matches),('event_equivalence_summary.csv',comparisons),('sampling_sensitivity.csv',samples),('extreme_sensitivity.csv',extremes),('rule_member_correspondence_summary.csv',overlaps),('tau_recalculation.csv',tau),('rho_scale_sensitivity.csv',risks),('exposure_denominators.csv',exposures),('measurement_status.csv',statesummary),('missing_reason_counts.csv',reasons),('case_447_final_audit.csv',case_checks)]:pd.DataFrame(rows).to_csv(out/name,index=False)
    pd.concat(sampling_edges,ignore_index=True).to_parquet(out/'sampling_overlap_edges.parquet',index=False)
    recalculated=float(np.mean(sorted(x['ttc_weighted_median_s'] for x in tau)[1:3]));assert abs(recalculated-TAU)<1e-12
    cc=pd.DataFrame(comparisons);mm=pd.DataFrame(matches);bad_times=int((mm.filter(regex='_delta$').fillna(0).abs().gt(1e-8).any(axis=1)).sum())
    assert cc.missing.sum()==0 and cc.added.sum()==0 and bad_times==0, 'member/time/metric mismatch'
    for src,directory,name in [('coverage48',T221,'coverage_matrix.csv'),('template48',T221,'manual_review_template.csv'),('cases48',T221,'representative_cases.csv'),('cases11',T252,'key_difference_cases.csv'),('rho_previous',RHO,'rho_distribution_by_source.csv'),('rho_extreme_previous',RHO,'rho_extreme_sensitivity.csv')]:shutil.copyfile(directory/name,out/(src+Path(name).suffix))
    # A concise review index links existing charts, keeping human judgement blank.
    (out/'manual_review_index.md').write_text('# 人工复核入口\n\nPhysical Truth Unverified。447 个案例新核对结果见 case_447_final_audit.csv；按 review_priority 排序，不推算总体异常比例。\n\n48 案例图册：'+str((T221/'representative_casebook.pdf').relative_to(ROOT))+'\n\n24 案例三规则图册：'+str((T251/'casebook_24.pdf').relative_to(ROOT))+'\n\n11 差异案例图册：'+str((T252/'key_difference_casebook.pdf').relative_to(ROOT))+'\n\n保留 Lankershim 31245；独立视频、几何参考或真人审核才可能补充物理真实性。\n',encoding='utf-8')
    # Read-only paper audit: latest by dated filename; marked-up version also indexed.
    import fitz
    paper=ROOT/'paper/历史记录/20261010_YYS.pdf';doc=fitz.open(paper);text='\n'.join(page.get_text() for page in doc);(out/'paper_readonly_excerpts.txt').write_text('\n'.join(line for line in text.splitlines() if any(k in line.lower() for k in ['ttc','risk','风险','缺失','不适用','持续','确认','源事件'])),encoding='utf-8');doc.close()
    audit={'schema_version':'stage_0_2.final_closure.audit.v2','p2_events':sum(x['event_count'] for x in psummary),'unique_followers':sum(x['unique_followers'] for x in psummary),'unique_pairs':sum(x['unique_pairs'] for x in psummary),'member_time_metric_differences':bad_times,'independent_event_missing':int(cc.missing.sum()),'independent_event_added':int(cc.added.sum()),'tau_s':recalculated,'states':sum(x['state_rows'] for x in tau),'cases':len(case_checks),'unique_case_centers':sum(x['unique_center'] for x in case_checks),'historical_hash_mismatches':sum(x['status']!='Verified' for x in inventory),'physical_truth_status':'Unverified','scientific_gate_passed':False,'gate_candidate':'pending final evidence review','protocol_lock_created':False,'stage_I_run':False,'locked_holdout_opened':False,'paper_sha256':sha(paper)}
    cfg={'schema_version':'stage_0_2.final_closure.config.v2','formal_config':P2_FORMAL_CONFIG.to_dict(),'rules':RULES,'sampling':'NGSIM anchors, 200 ms phases 0/100; full 100ms identity/reliability blocks constrain discarded observations; sampled non-risk splits; no interpolation','tau_weighting':'strict reliable closing edges; .05s per endpoint; source-balanced middle median mean','exposure':'observed link spans only, no final-frame extrapolation; rates diagnostic only','region_fixed_burden':'not applicable to Stage 0.2 descriptive NGSIM scope','scientific_gate_passed':False}
    inputs={str(path.relative_to(ROOT)):sha(path) for path in (T15/'states').glob('*.parquet')}
    for directory,name in [(T251,'event_confirmation_audit.csv'),(DEC,'tau_calibration.csv'),(T23,'case_diagnostics.csv'),(T221,'representative_cases.csv'),(T252,'key_difference_cases.csv')]:inputs[str((directory/name).relative_to(ROOT))]=sha(directory/name)
    prov={'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'created_utc':datetime.now(UTC).isoformat(),'python':sys.version,'inputs':inputs,'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'code/scripts/stage_0_2_closure_analysis.py',ROOT/'code/src/riskprop/formal_risk_measurement.py']},'paper':str(paper.relative_to(ROOT)),'paper_sha256':sha(paper)}
    for name,obj in [('audit.json',audit),('config.json',cfg),('provenance.json',prov)]: (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    seal(out);print(json.dumps(audit,ensure_ascii=False,indent=2),flush=True)

def seal(out):
    files=sorted(x for x in out.iterdir() if x.is_file() and x.name not in {'manifest.json','SHA256SUMS'});(out/'manifest.json').write_text(json.dumps({'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]},indent=2)+'\n',encoding='utf-8');(out/'SHA256SUMS').write_text('\n'.join(sha(p)+'  '+p.name for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS')+'\n',encoding='utf-8')
if __name__=='__main__':main()
