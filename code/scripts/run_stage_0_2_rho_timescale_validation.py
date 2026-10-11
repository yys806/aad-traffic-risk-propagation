"""Stage 0.2 diagnostic validation of rho time-scale and exposure composition."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from datetime import UTC, datetime
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T15 = ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4"
DEC = ROOT / "code/outputs/formal/calibration/stage_0_2_decision_ratification_20261011_r1"
T251 = ROOT / "code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2"
TAU = 15.364279197080283

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def weighted_quantile(values, weights, q):
    x = np.asarray(values, float); w = np.asarray(weights, float)
    ok = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[ok], w[ok]
    if not len(x): return np.nan
    order = np.argsort(x, kind="stable"); x, w = x[order], w[order]
    return float(x[np.searchsorted(np.cumsum(w), q * w.sum(), side="left")])

def reliable_edges(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values(["trajectory_id", "global_time_ms", "frame_id"], kind="stable").copy()
    same = d.trajectory_id.eq(d.trajectory_id.shift()) & d.leader_trajectory_id.eq(d.leader_trajectory_id.shift())
    same &= d.global_time_ms.diff().eq(100) & d.frame_id.diff().eq(1)
    same &= d.diagnostic_clock_anchor_ms.eq(d.diagnostic_clock_anchor_ms.shift())
    same &= ~d.identity_break.fillna(True) & ~d.observation_gap.fillna(True)
    reliable = d.leader_matched.fillna(False) & ~d.identity_uncertain.fillna(True) & ~d.leader_identity_uncertain.fillna(True)
    valid = reliable & d.ttc_valid.fillna(False) & d.measurement_status.eq("valid")
    edge = same & valid & valid.shift(fill_value=False)
    d = d.loc[edge, ["source_member", "ttc_s", "drac_mps2", "net_gap_m", "time_s", "original_row_number"]].copy()
    d["weight_s"] = 0.1
    return d

def validate_contribution(status, inside, reliable, ttc, tau):
    if inside is False and reliable: return (0.0, 0.0)
    if inside is None or not reliable: return (0.0, 1.0)
    if status == "not_applicable": return (0.0, 0.0)
    if status == "valid" and ttc is not None and np.isfinite(ttc) and ttc > 0:
        r = float(np.exp(-ttc / tau)); return (r, r)
    return (0.0, 1.0)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args(); out = args.output_dir.resolve(); out.mkdir(parents=False, exist_ok=False)
    tau = float(pd.read_csv(DEC / "tau_calibration.csv").iloc[0].get("tau_s", TAU)) if False else TAU
    scales = {"tau_half": tau / 2, "tau": tau, "tau_double": tau * 2}
    bins = [("lt_2", 0, 2), ("2_5", 2, 5), ("5_10", 5, 10), ("ge_10", 10, np.inf)]
    source_rows=[]; bin_rows=[]; extreme_rows=[]; source_edges={}
    for path in sorted((T15 / "states").glob("*.parquet")):
        source = path.stem.removeprefix("ngsim_"); d = pd.read_parquet(path); e = reliable_edges(d); source_edges[source] = e
        for scale_name, scale_tau in scales.items():
            rho = np.exp(-e.ttc_s.to_numpy(float) / scale_tau); total = float(e.weight_s.sum())
            source_rows.append({"source":source,"tau_scale":scale_name,"tau_s":scale_tau,"closing_exposure_s":total,
                "rho_mean_time_weighted":float(np.average(rho,weights=e.weight_s)),
                "rho_p50":weighted_quantile(rho,e.weight_s,.5),"rho_p90":weighted_quantile(rho,e.weight_s,.9),
                "rho_p95":weighted_quantile(rho,e.weight_s,.95),"rho_p99":weighted_quantile(rho,e.weight_s,.99),
                "rho_gt_0_5_exposure_fraction":float(e.weight_s[rho>.5].sum()/total),
                "rho_gt_0_9_exposure_fraction":float(e.weight_s[rho>.9].sum()/total)})
            for label, lo, hi in bins:
                mask=(e.ttc_s>=lo)&(e.ttc_s<hi); exposure=float(e.loc[mask,"weight_s"].sum()); contribution=float(np.dot(rho[mask],e.loc[mask,"weight_s"]))
                bin_rows.append({"source":source,"tau_scale":scale_name,"tau_s":scale_tau,"ttc_bin":label,"exposure_s":exposure,
                    "exposure_fraction":exposure/total,"risk_contribution":contribution,"risk_contribution_fraction":contribution/float(np.dot(rho,e.weight_s)),
                    "conditional_rho":float(np.average(rho[mask],weights=e.loc[mask,"weight_s"])) if mask.any() else np.nan})
            extreme=((e.ttc_s<.5)|(e.drac_mps2>10)|(e.net_gap_m<1)).to_numpy(bool)
            for label,mask in [("all",np.ones(len(e),bool)),("exclude_extreme",~extreme)]:
                extreme_rows.append({"source":source,"tau_scale":scale_name,"subset":label,"exposure_s":float(e.weight_s[mask].sum()),
                    "rho_mean_time_weighted":float(np.average(rho[mask],weights=e.weight_s[mask])) if mask.any() else np.nan,
                    "flagged_rows":int(extreme.sum()),"flagged_exposure_fraction":float(e.weight_s[extreme].sum()/total)})
    source_df=pd.DataFrame(source_rows); bins_df=pd.DataFrame(bin_rows); extreme_df=pd.DataFrame(extreme_rows)
    source_df.to_csv(out/'rho_distribution_by_source.csv',index=False); bins_df.to_csv(out/'rho_exposure_composition.csv',index=False); extreme_df.to_csv(out/'rho_extreme_sensitivity.csv',index=False)
    # Rank stability and P2 event overlap diagnostic, without treating events as truth.
    rank_rows=[]
    for scale, g in source_df.groupby('tau_scale'):
        for metric in ['rho_mean_time_weighted','rho_p95','rho_gt_0_9_exposure_fraction']:
            order='>'.join(g.sort_values(metric,ascending=False).source.tolist()); rank_rows.append({'tau_scale':scale,'metric':metric,'source_rank_high_to_low':order})
    pd.DataFrame(rank_rows).to_csv(out/'source_rank_stability.csv',index=False)
    p2=pd.read_csv(T251/'event_confirmation_audit.csv'); p2=p2[(p2.rule=='P2_middle')&(p2.inclusion_status=='reliable')].copy(); p2['members']=p2.original_row_numbers.map(lambda x:set(map(int,json.loads(x))))
    high=[]
    for source,e in source_edges.items():
        # use member rows from reliable edge endpoints as a conservative overlap count
        valid_rows=set(e.original_row_number.astype(int)); pe=p2[p2.source==source]
        high.append({'source':source,'p2_events':len(pe),'p2_events_with_reliable_closing_edge_member':int(pe.members.map(lambda s:bool(s&valid_rows)).sum()),'event_truth_status':'P2 is an engineering rule, not independent accident truth'})
    pd.DataFrame(high).to_csv(out/'p2_event_rho_overlap.csv',index=False)
    cfg={'tau_s':tau,'scales':scales,'ttc_bins':bins,'weighting':'reliable same-pair same-clock 100ms edges, 0.1s each; no interpolation','formal_region_burden':'not computed; fixed region/cohort/window absent','scientific_gate_passed':False}
    audit={'tau_s':tau,'sources':len(source_edges),'rho_rows':len(source_df),'composition_rows':len(bins_df),'p2_overlap_rows':len(high),'formal_region_burden':'Unresolved','locked_holdout_opened':False,'scientific_claim_eligible':False}
    prov={'created_at':datetime.now(UTC).isoformat(),'script':'code/scripts/run_stage_0_2_rho_timescale_validation.py','input_state_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((T15/'states').glob('*.parquet'))},'source_tau_audit':str((DEC/'tau_calibration.csv').relative_to(ROOT))}
    for n,obj in [('config.json',cfg),('audit.json',audit),('provenance.json',prov)]: (out/n).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fs=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.name not in {'manifest.json','SHA256SUMS'} and p.is_file()]
    (out/'manifest.json').write_text(json.dumps({'schema_version':'stage_0_2.rho_timescale.manifest.v1','files':fs},indent=2)+'\n',encoding='utf-8')
    (out/'SHA256SUMS').write_text('\n'.join(sha(p)+'  '+p.name for p in sorted(out.iterdir()) if p.name!='SHA256SUMS' and p.is_file())+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=True))
if __name__=='__main__': main()
