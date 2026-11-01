"""Offline scientific analysis of the frozen Task18 Task9 results.

This script reads existing Primary/Supplementary trajectories and summaries;
it never starts SUMO or mutates Task17/Task18 artifacts.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE18 = ROOT / "evidence/results/RES-STAGE-0.5-TASK18-EXECUTION-INTEGRITY-20261101"
OUT = ROOT / "code/outputs/analysis/task19_20261101"
FIG = OUT / "figures"
EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-TASK19-SCIENTIFIC-RESULT-ANALYSIS-20261101"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_results() -> pd.DataFrame:
    primary = pd.read_csv(EVIDENCE18 / "primary_results.csv").assign(source="Primary", source_file="primary_results.csv")
    supplementary = pd.read_csv(EVIDENCE18 / "supplementary_results.csv").assign(source="Supplementary", source_file="supplementary_results.csv")
    out = pd.concat([primary, supplementary], ignore_index=True)
    out["scientific_usable"] = out["scientific_usable"].astype(bool)
    return out


def trajectory_features(row: pd.Series) -> dict[str, object]:
    frame = pd.read_csv(ROOT / str(row.trajectory_dir) / "trajectory_internal_0p05.csv")
    t = frame.input_time_s.to_numpy(float)
    vf = frame.follower_speed_mps.to_numpy(float)
    vl = frame.leader_speed_mps.to_numpy(float)
    gap = frame.net_gap_m.to_numpy(float)
    closing = frame.closing_speed_mps.to_numpy(float)
    acc = frame.follower_acc_mps2.to_numpy(float)
    anchor = float(row.shared_leader_perturbation_anchor_s)
    after = np.flatnonzero(t >= anchor)
    if len(after):
        peak_i = int(after[np.argmax(np.abs(vf[after] - vf[0]))])
    else:
        peak_i = int(np.argmax(np.abs(vf - vf[0])))
    positive = closing > 1e-12
    ttc = np.where(positive, gap / np.maximum(closing, 1e-12), np.nan)
    return {
        "run_id": row.run_id,
        "source": row.source,
        "candidate": row.candidate,
        "tau_index": int(row.tau_index),
        "tau_s": float(row.tau_s),
        "arm": row.arm,
        "seed": int(row.seed),
        "trajectory_sha256": row.trajectory_sha256,
        "rows": int(len(frame)),
        "horizon_s": float(t[-1] - t[0]),
        "initial_follower_speed_mps": float(vf[0]),
        "initial_leader_speed_mps": float(vl[0]),
        "initial_gap_m": float(gap[0]),
        "final_gap_m": float(gap[-1]),
        "gap_change_m": float(gap[-1] - gap[0]),
        "min_gap_m": float(gap.min()),
        "min_gap_time_s": float(t[np.argmin(gap)]),
        "follower_delta_v_min_mps": float((vf - vf[0]).min()),
        "follower_delta_v_max_mps": float((vf - vf[0]).max()),
        "follower_response_amplitude_mps": float(np.abs(vf - vf[0]).max()),
        "leader_response_amplitude_mps": float(np.abs(vl - vl[0]).max()),
        "follower_acc_abs_max_mps2": float(np.abs(acc).max()),
        "follower_acc_rms_mps2": float(np.sqrt(np.mean(acc**2))),
        "relative_speed_min_mps": float(closing.min()),
        "relative_speed_max_mps": float(closing.max()),
        "positive_closing_fraction": float(np.mean(positive)),
        "ttc_valid_fraction": float(np.mean(np.isfinite(ttc))),
        "ttc_min_recomputed_s": float(np.nanmin(ttc)) if np.isfinite(ttc).any() else np.nan,
        "leader_anchor_s": anchor,
        "follower_peak_abs_response_time_s": float(t[peak_i]),
        "descriptive_peak_lag_s": float(t[peak_i] - anchor),
        "C_initial_m": float(row.C_initial_m),
        "C_f_m": float(row.C_f_m),
        "C_l_m": float(row.C_l_m),
        "C_m": float(row.C_m),
        "C_gap_m": float(row.C_gap_m),
        "R_m": float(row.R_m),
        "closure_error_m": float(row.closure_error_m),
    }


def group_summary(features: pd.DataFrame) -> pd.DataFrame:
    metrics = ["follower_response_amplitude_mps", "follower_delta_v_min_mps", "follower_delta_v_max_mps", "follower_acc_abs_max_mps2", "follower_acc_rms_mps2", "relative_speed_min_mps", "gap_change_m", "min_gap_m", "ttc_min_recomputed_s", "descriptive_peak_lag_s", "C_f_m", "C_l_m", "C_m", "C_gap_m", "R_m"]
    rows = []
    for keys, g in features.groupby(["source", "candidate", "tau_index", "tau_s", "arm"], dropna=False):
        rec = dict(zip(["source", "candidate", "tau_index", "tau_s", "arm"], keys))
        rec["n_runs"] = len(g)
        rec["seed_values"] = ",".join(str(x) for x in sorted(g.seed.unique()))
        for m in metrics:
            a = g[m].dropna().to_numpy(float)
            rec[f"{m}_n"] = len(a)
            rec[f"{m}_mean"] = float(np.mean(a)) if len(a) else np.nan
            rec[f"{m}_sd"] = float(np.std(a, ddof=1)) if len(a) > 1 else np.nan
            rec[f"{m}_median"] = float(np.median(a)) if len(a) else np.nan
            rec[f"{m}_min"] = float(np.min(a)) if len(a) else np.nan
            rec[f"{m}_max"] = float(np.max(a)) if len(a) else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def tau_trends(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (source, candidate, arm), g in summary.groupby(["source", "candidate", "arm"]):
        g = g.sort_values("tau_s")
        for metric in ["follower_response_amplitude_mps_mean", "min_gap_m_mean", "ttc_min_recomputed_s_mean", "follower_acc_abs_max_mps2_mean", "gap_change_m_mean"]:
            y = g[metric].to_numpy(float)
            x = g.tau_s.to_numpy(float)
            valid = np.isfinite(y)
            if valid.sum() >= 3:
                ranks_x = pd.Series(x[valid]).rank().to_numpy(float)
                ranks_y = pd.Series(y[valid]).rank().to_numpy(float)
                if np.std(ranks_x) == 0 or np.std(ranks_y) == 0:
                    rho = np.nan
                else:
                    rho = float(np.corrcoef(ranks_x, ranks_y)[0, 1])
                diffs = np.diff(y[valid])
                monotonic = bool(np.all(diffs >= -1e-12) or np.all(diffs <= 1e-12))
                slope = float(np.polyfit(x[valid], y[valid], 1)[0])
            else:
                rho = np.nan; monotonic = False; slope = np.nan
            rows.append({"source": source, "candidate": candidate, "arm": arm, "metric": metric, "spearman_rho": rho, "linear_slope_per_tau_s": slope, "monotonic_across_five_tau": monotonic, "values_by_tau": ";".join(f"{a:.6g}" for a in y)})
    return pd.DataFrame(rows)


def source_consistency(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metrics = ["follower_response_amplitude_mps_mean", "min_gap_m_mean", "ttc_min_recomputed_s_mean", "follower_acc_abs_max_mps2_mean", "gap_change_m_mean", "C_m_mean"]
    for keys, g in summary.groupby(["candidate", "tau_index", "tau_s", "arm"], dropna=False):
        rec = dict(zip(["candidate", "tau_index", "tau_s", "arm"], keys))
        p = g[g.source == "Primary"].iloc[0]; s = g[g.source == "Supplementary"].iloc[0]
        for m in metrics:
            rec[f"Primary_{m}"] = float(p[m]); rec[f"Supplementary_{m}"] = float(s[m]); rec[f"Supplementary_minus_Primary_{m}"] = float(s[m] - p[m])
        rows.append(rec)
    return pd.DataFrame(rows)


def actual_pair_analysis() -> tuple[pd.DataFrame, pd.DataFrame]:
    primary = pd.read_csv(EVIDENCE18 / "paired_analysis_primary.csv")
    supp = pd.read_csv(EVIDENCE18 / "paired_analysis_supplementary.csv")
    return primary, supp


def plot_speed_profiles(features: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=False, sharey=True)
    colors = plt.cm.viridis(np.linspace(0.05, 0.95, 5))
    for ri, candidate in enumerate(["962-958-1", "926-924-1"]):
        for ci, arm in enumerate(["A", "B"]):
            ax = axes[ri, ci]
            tau_levels = sorted(features[["tau_index", "tau_s"]].drop_duplicates().itertuples(index=False, name=None))
            for j, (ti, tau) in enumerate(tau_levels):
                g = features[(features.source == "Primary") & (features.candidate == candidate) & (features.arm == arm) & (features.tau_index == ti)]
                if g.empty: continue
                profiles=[]
                for _, r in g.iterrows():
                    f=pd.read_csv(ROOT/str(r.trajectory_dir)/"trajectory_internal_0p05.csv")
                    profiles.append(f.follower_speed_mps.to_numpy(float)-float(f.follower_speed_mps.iloc[0]))
                n=min(map(len,profiles)); t=f.input_time_s.to_numpy(float)[:n]
                y=np.vstack([x[:n] for x in profiles])
                ax.plot(t,y.mean(0),color=colors[j],label=f"tau={tau:.3g}")
                ax.fill_between(t,np.percentile(y,25,axis=0),np.percentile(y,75,axis=0),color=colors[j],alpha=.12)
            ax.axhline(0,color='0.6',lw=.7); ax.set_title(f"{candidate} / Arm {arm}"); ax.set_xlabel("t (s)"); ax.set_ylabel("Follower Δv (m/s)"); ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8,ncol=2); fig.suptitle("Primary Follower speed response profiles (mean, IQR across seeds)"); fig.tight_layout(); fig.savefig(FIG/"speed_response_profiles_primary.png",dpi=180); plt.close(fig)


def plot_pair_delta(pair: pd.DataFrame) -> None:
    fig, axes=plt.subplots(1,2,figsize=(12,4.5),sharey=True)
    for ax,candidate in zip(axes,["962-958-1","926-924-1"]):
        g=pair[pair.candidate==candidate]
        for source,marker in [("Primary","o"),("Supplementary","s")]:
            z=g[g.kind==source]; ax.scatter(z.tau_s,z.delta_B_minus_A_follower_response_amplitude_mps,label=source,marker=marker,s=35)
        ax.axhline(0,color='0.5',lw=.8); ax.set_title(candidate); ax.set_xlabel("tau (s)"); ax.set_ylabel("B−A follower amplitude (m/s)"); ax.grid(alpha=.2)
    axes[0].legend(); fig.suptitle("Paired minGap effect on descriptive response amplitude"); fig.tight_layout(); fig.savefig(FIG/"paired_amplitude_delta.png",dpi=180); plt.close(fig)


def plot_gap_ttc(summary: pd.DataFrame) -> None:
    fig, axes=plt.subplots(2,2,figsize=(12,8),sharex=True)
    for ri,candidate in enumerate(["962-958-1","926-924-1"]):
        for ci,metric in enumerate(["min_gap_m_mean","ttc_min_recomputed_s_mean"]):
            ax=axes[ri,ci]
            for source,ls in [("Primary","-"),("Supplementary","--")]:
                for arm,color in [("A","tab:blue"),("B","tab:orange")]:
                    g=summary[(summary.source==source)&(summary.candidate==candidate)&(summary.arm==arm)].sort_values('tau_s')
                    ax.plot(g.tau_s,g[metric],linestyle=ls,color=color,marker='o',label=f"{source} Arm {arm}")
            ax.set_title(f"{candidate} / {metric.replace('_mean','')}"); ax.set_xlabel('tau (s)'); ax.grid(alpha=.2)
    axes[0,0].set_ylabel('m'); axes[1,0].set_ylabel('m'); axes[0,1].set_ylabel('s'); axes[1,1].set_ylabel('s'); axes[0,0].legend(fontsize=7); fig.suptitle('Gap and TTC summaries by candidate, arm and source'); fig.tight_layout(); fig.savefig(FIG/"gap_ttc_by_tau.png",dpi=180); plt.close(fig)


def plot_source_consistency(consistency: pd.DataFrame) -> None:
    fig, ax=plt.subplots(figsize=(6,5)); x=consistency.Primary_follower_response_amplitude_mps_mean; y=consistency.Supplementary_follower_response_amplitude_mps_mean
    for candidate,color in [("962-958-1","tab:blue"),("926-924-1","tab:orange")]:
        z=consistency[consistency.candidate==candidate]; ax.scatter(z.Primary_follower_response_amplitude_mps_mean,z.Supplementary_follower_response_amplitude_mps_mean,label=candidate,s=40)
    lo=min(x.min(),y.min()); hi=max(x.max(),y.max()); ax.plot([lo,hi],[lo,hi],color='0.5',lw=.8); ax.set_xlabel('Primary mean amplitude (m/s)'); ax.set_ylabel('Supplementary mean amplitude (m/s)'); ax.set_title('Primary vs Supplementary descriptive consistency'); ax.grid(alpha=.2); ax.legend(); fig.tight_layout(); fig.savefig(FIG/"primary_supplementary_consistency.png",dpi=180); plt.close(fig)


def plot_seed_variability(features: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, candidate in zip(axes, ["962-958-1", "926-924-1"]):
        for source, linestyle in [("Primary", "-"), ("Supplementary", "--")]:
            for arm, color in [("A", "tab:blue"), ("B", "tab:orange")]:
                g = features[(features.source == source) & (features.candidate == candidate) & (features.arm == arm)]
                for seed, z in g.groupby("seed"):
                    z = z.sort_values("tau_s")
                    ax.plot(z.tau_s, z.follower_response_amplitude_mps, linestyle=linestyle, color=color, alpha=.55, marker="o", ms=3)
        ax.set_title(candidate); ax.set_xlabel("tau (s)"); ax.set_ylabel("Follower response amplitude (m/s)"); ax.grid(alpha=.2)
    fig.suptitle("Seed-level variation (solid Primary, dashed Supplementary)"); fig.tight_layout(); fig.savefig(FIG/"seed_variability.png", dpi=180); plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True); EVIDENCE.mkdir(parents=True, exist_ok=True)
    results=load_results(); results.to_csv(OUT/"analysis_dataset_run_level.csv",index=False)
    feature_rows=[trajectory_features(r) | {"trajectory_dir": r.trajectory_dir} for _,r in results.iterrows()]
    features=pd.DataFrame(feature_rows); features.to_csv(OUT/"analysis_trajectory_features.csv",index=False)
    summary=group_summary(features); summary.to_csv(OUT/"stratified_descriptive_summary.csv",index=False)
    trends=tau_trends(summary); trends.to_csv(OUT/"tau_trend_diagnostics.csv",index=False)
    consistency=source_consistency(summary); consistency.to_csv(OUT/"primary_supplementary_consistency.csv",index=False)
    p_pair,s_pair=actual_pair_analysis(); p_pair.assign(source='Primary').to_csv(OUT/"paired_primary_actual.csv",index=False); s_pair.assign(source='Supplementary').to_csv(OUT/"paired_supplementary_actual.csv",index=False)
    pair=pd.concat([p_pair.assign(kind='Primary'),s_pair.assign(kind='Supplementary')],ignore_index=True); pair.to_csv(OUT/"paired_all_sources.csv",index=False)
    seed_table=features[['source','candidate','tau_index','tau_s','arm','seed','follower_response_amplitude_mps','follower_acc_abs_max_mps2','min_gap_m','ttc_min_recomputed_s','gap_change_m']].copy(); seed_table.to_csv(OUT/"seed_level_results.csv",index=False)
    plot_speed_profiles(features); plot_pair_delta(pair); plot_gap_ttc(summary); plot_source_consistency(consistency); plot_seed_variability(features)
    # Copy compact, reproducible analysis deliverables into portable evidence.
    for p in [OUT/"analysis_dataset_run_level.csv",OUT/"analysis_trajectory_features.csv",OUT/"stratified_descriptive_summary.csv",OUT/"tau_trend_diagnostics.csv",OUT/"primary_supplementary_consistency.csv",OUT/"paired_all_sources.csv",OUT/"seed_level_results.csv"]:
        shutil.copy2(p,EVIDENCE/p.name)
    for p in FIG.glob('*.png'): shutil.copy2(p,EVIDENCE/p.name)
    source_files=[EVIDENCE18/'primary_results.csv',EVIDENCE18/'supplementary_results.csv',EVIDENCE18/'paired_analysis_primary.csv',EVIDENCE18/'paired_analysis_supplementary.csv']
    manifest={'task_id':'AAD-S0.5-TASK19','status':'COMPLETED_OFFLINE_ANALYSIS','source_files':{str(p.relative_to(ROOT)):sha256(p) for p in source_files},'run_count':int(len(results)),'primary_runs':int((results.source=='Primary').sum()),'supplementary_runs':int((results.source=='Supplementary').sum()),'sumo_launches':0,'new_seeds':0,'new_experiments':0,'metrics_source':'Task18 frozen result tables plus full internal trajectories','figures':[p.name for p in FIG.glob('*.png')]}
    (EVIDENCE/'analysis_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    payload=[p for p in EVIDENCE.iterdir() if p.is_file() and p.name not in {'SHA256SUMS','sha256_manifest.json'}]
    (EVIDENCE/'sha256_manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha256(p) for p in sorted(payload)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (EVIDENCE/'SHA256SUMS').write_text('\n'.join(f'{sha256(p)}  {p.name}' for p in sorted(EVIDENCE.iterdir()) if p.is_file() and p.name!='SHA256SUMS')+'\n',encoding='utf-8')
    print(json.dumps({'TASK19_STATUS':'COMPLETED','runs_analyzed':len(results),'primary':int((results.source=='Primary').sum()),'supplementary':int((results.source=='Supplementary').sum()),'pair_records':len(pair),'figures':len(list(FIG.glob('*.png'))),'output':str(OUT.relative_to(ROOT)),'evidence':str(EVIDENCE.relative_to(ROOT))},ensure_ascii=False))


if __name__=='__main__':
    main()
