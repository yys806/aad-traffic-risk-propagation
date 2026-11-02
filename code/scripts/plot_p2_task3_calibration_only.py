"""Plot existing CALIBRATION_ONLY summaries; never re-fit or select detectors."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',type=Path,required=True)
    a=p.parse_args(); root=a.input_dir
    rows=list(csv.DictReader((root/'calibration_summary.csv').open(encoding='utf-8')))
    target=root/'sensitivity_curves.png'
    if target.exists(): raise FileExistsError(target)
    def select(agg,scenario,**filters):
        return [r for r in rows if r['split']=='validation' and r['aggregator']==agg and r['scenario']==scenario and all(abs(float(r[k])-v)<1e-8 for k,v in filters.items())]
    fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for agg in ['mean','median','proportion']:
        selected=sorted(select(agg,'broad_0.5_3.0',h_s=1,baseline_s=5,q_factor=1.1,coverage_gate=.8),key=lambda r:float(r['theta']))
        ax[0,0].plot([float(r['theta']) for r in selected],[float(r['event_detected_rate']) for r in selected],marker='o',label=agg)
        selected=sorted(select(agg,'broad_1.0_0.8',theta=.5,baseline_s=5,q_factor=1.1,coverage_gate=.8),key=lambda r:float(r['h_s']))
        ax[0,1].plot([float(r['h_s']) for r in selected],[float(r['event_detected_rate']) for r in selected],marker='o',label=agg)
    for scenario in ['block_040','mcar_020']:
        selected=sorted(select('mean',scenario,theta=.5,h_s=1,baseline_s=5,coverage_gate=.8),key=lambda r:float(r['q_factor']))
        ax[1,0].plot([float(r['q_factor']) for r in selected],[float(r['event_detected_rate']) for r in selected],marker='o',label=scenario)
    for scenario in ['null_stationary','null_trend']:
        selected=sorted(select('mean',scenario,theta=.5,h_s=1,q_factor=1.1,coverage_gate=.8),key=lambda r:float(r['baseline_s']))
        ax[1,1].plot([float(r['baseline_s']) for r in selected],[float(r['false_alarm_rate']) for r in selected],marker='o',label=scenario)
    titles=['0.5 m/s decline for 3 s','1 m/s decline for 0.8 s','Missing observations: mean statistic','Null source: stationary vs natural trend']
    xlabels=['Threshold (mean/median: m/s; proportion: fraction)','Observed persistence span (s)','Maximum gap / sampling interval','Baseline window (s)']
    for k,axis in enumerate(ax.flat):
        axis.set(title=titles[k],xlabel=xlabels[k],ylabel='Per-panel alarm / detection fraction',ylim=(-.04,1.04));axis.grid(alpha=.25);axis.legend(fontsize=8)
    fig.suptitle('CALIBRATION_ONLY: synthetic verification, 24 held-out panels per cell\nNo traffic threshold recommendation; point estimates, not simultaneous bands',fontsize=12)
    fig.savefig(target,dpi=160);plt.close(fig)
    prov={'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'input_summary_sha256':hashlib.sha256((root/'calibration_summary.csv').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'matplotlib':matplotlib.__version__}
    (root/'plot_provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
    (root/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n' for f in sorted(root.iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
    print(json.dumps(prov))


if __name__=='__main__':main()
