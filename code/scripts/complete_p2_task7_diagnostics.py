"""Additional calibration-only conditional curves and planned-signal realization audit."""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import numpy as np
import p2_task7_measurement as m
import analyze_p2_task7_parameter_experiment as a

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def longest_span(t,signal,valid,amplitude,entity=False):
    if signal.ndim==1:signal=signal[:,None];valid=valid[:,None]
    best=0.
    for i in range(signal.shape[1]):
        idx=np.flatnonzero(valid[:,i]&(signal[:,i]>=amplitude)&(t>=30)&(t<=50))
        for group in np.split(idx,np.flatnonzero(np.diff(idx)>1)+1):
            if len(group) and t[group[0]]<=46:best=max(best,float(t[group[-1]]-t[group[0]]))
    return best

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args();out=args.output_dir.resolve()
    manifest=load(out/'manifest.json');plan=load(out/'detector/candidate_manifest.json');selected=load(out/'detector/calibration_selection.json')
    curves=[];realization=[];density=[];joint=[]
    design={'P11':(1.,1.),'P21':(2.,1.),'P12':(1.,2.),'P22':(2.,2.)}
    # No new detector selection and no change to the frozen V candidate manifest.
    for unit in manifest['units']:
        uid=unit['unit_id'];raw=dict(np.load(out/'raw'/uid/'trajectory.npz'));labels=load(out/'truth'/f'{uid}.json');cache={}
        for label in labels:
            layer=label['measurement_layer'];center=a.Config(**selected[layer]['parameters']);variables=['W','model','theta','h','q']
            if layer=='cohort':variables+=['coverage','recovery','hysteresis','missing']
            if layer=='macro':variables+=['w','stride','cells']
            if layer=='micro':variables+=['stride']
            for variable in variables:
                for value in plan['grids'][layer][variable]:
                    config=a.replace(center,**{variable:value});r=a.evaluate(raw,label,config,seed=unit['sumo_seed'],cache=cache)
                    curves.append({'unit_id':uid,'layer':layer,'density':unit['density'],'condition':unit['condition'],
                        'variable':variable,'value':str(value),'config_id':a.config_key(config),**r})
            if len(raw['t']) and layer=='cohort':
                for coverage in [.8,1.]:
                    for missing in [0.,.2]:
                        r=a.evaluate(raw,label,a.replace(center,coverage=coverage),stress={'kind':'MCAR','amount':missing},seed=unit['sumo_seed'],cache=cache)
                        joint.append({'unit_id':uid,'layer':layer,'density':unit['density'],'condition':unit['condition'],
                            'interaction':'coverage_x_missing','factor_a':coverage,'factor_b':missing,**r})
        if not len(raw['t']):
            if unit['condition'] in design:
                amplitude,duration=design[unit['condition']]
                for layer in a.LAYERS:realization.append({'unit_id':uid,'layer':layer,'density':unit['density'],
                    'condition':unit['condition'],'planned_min_amplitude_mps':amplitude,'planned_min_duration_s':duration,
                    'actual_max_contiguous_span_above_planned_amplitude_s':None,'design_minimum_realized':None,
                    'role':'preserved failed attempt; no target observations','source_dose_is_not_target_truth':True})
            continue
        t=raw['t'];v=raw['v'];x=raw['x'];lane=raw['lane'];macro=a.fast_edie(t,x,lane,.1)
        pre=(t>=10)&(t<28)
        density.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],
            'pre_Edie_k_veh_km_lane':float(np.mean(macro['k'][pre])*1000),
            'pre_Edie_u_mps':float(np.mean(macro['u'][pre])),'pre_Edie_q_veh_h_lane':float(np.mean(macro['q'][pre])*3600),
            'nominal_platoon_spacing_m':unit['spacing_m'],'nominal_local_packing_veh_km':1000/unit['spacing_m']})
        if unit['condition'] in design:
            amplitude,duration=design[unit['condition']];inside=(x>=m.REGION[0])&(x<m.REGION[1])&(lane==0);inside[:,0]=False
            signals={'cohort':np.mean(10-v[:,m.COHORT],axis=1),'macro':10-macro['u'],'micro':10-v}
            validity={'cohort':((x[:,m.COHORT]>=m.REGION[0])&(x[:,m.COHORT]<m.REGION[1])&(lane[:,m.COHORT]==0)).all(axis=1),
                'macro':macro['complete']&np.isfinite(macro['u']),'micro':inside}
            for layer in a.LAYERS:
                span=longest_span(t,signals[layer],validity[layer],amplitude)
                realization.append({'unit_id':uid,'layer':layer,'density':unit['density'],'condition':unit['condition'],
                    'planned_min_amplitude_mps':amplitude,'planned_min_duration_s':duration,
                    'actual_max_contiguous_span_above_planned_amplitude_s':span,'design_minimum_realized':span>=duration-1e-8,
                    'role':'post-computation physical descriptor; does not change primary truth or selection',
                    'source_dose_is_not_target_truth':True})
        elif unit['condition']=='Plocal':
            for label in labels:
                expected='negative' if label['measurement_layer']=='cohort' else 'positive'
                realization.append({'unit_id':uid,'layer':label['measurement_layer'],'density':unit['density'],
                    'condition':unit['condition'],'planned_min_amplitude_mps':1.,'planned_min_duration_s':1.,
                    'actual_max_contiguous_span_above_planned_amplitude_s':None,
                    'design_minimum_realized':label['state_truth']==expected,'planned_state':expected,
                    'actual_primary_state':label['state_truth'],'role':'local noncohort design realization, no new truth labels',
                    'source_dose_is_not_target_truth':True})
    a.csv_write(out/'detector/conditional_single_parameter_evaluations.csv',curves)
    groups=defaultdict(list)
    for r in curves:groups[(r['layer'],r['density'],r['condition'],r['variable'],r['value'])].append(r)
    summary=[{'layer':k[0],'density':k[1],'condition':k[2],'variable':k[3],'value':k[4],**a.summarize(v)} for k,v in groups.items()]
    a.csv_write(out/'detector/conditional_single_parameter_curves.csv',summary)
    a.csv_write(out/'truth/planned_signal_realization.csv',realization)
    a.csv_write(out/'audit/actual_density.csv',density)
    a.csv_write(out/'detector/coverage_missing_interaction.csv',joint)
    # Reaction window x clock: an audit of finite response-threshold lags, not driver reaction truth.
    with (out/'detector/reaction_clock_evidence.csv').open(encoding='utf-8',newline='') as f:edges=list(csv.DictReader(f))
    clean=[r for r in edges if float(r['clock_error_each_s'])==0 and r['reaction_lower_s']]
    lags=[float(r['reaction_lower_s']) for r in clean];high=[float(r['reaction_upper_s']) for r in clean]
    windows={'observed_full_range':[min(lags),max(high)],'central_90pct':[float(np.quantile(lags,.05)),float(np.quantile(high,.95))]} if lags else {}
    rg=defaultdict(list)
    for r in edges:
        if not r['reaction_lower_s']:continue
        error=float(r['clock_error_each_s']);lower=float(r['reaction_lower_s'])-2*error;upper=float(r['reaction_upper_s'])+2*error
        for name,(L,U) in windows.items():
            passed=r['W6_strict_order']=='True' and lower>=L and upper<=U
            rg[(r['unit_id'],r['density'],r['condition'],name,error)].append(passed)
    a.csv_write(out/'detector/reaction_window_clock_summary.csv',[{'unit_id':k[0],'density':k[1],'condition':k[2],
        'reaction_window':k[3],'clock_each_s':k[4],'eligible_edge_fraction':sum(v)/len(v),'edges':len(v),
        'independent_unit':k[0],'window_bounds_s':windows[k[3]],'qualified':'Unknown_W8',
        'scope':'representative rep0/23 finite-threshold lag; no count of edges as independent n'} for k,v in rg.items()])
    m.dump(out/'audit/additional_diagnostics.json',{'conditional_evaluations':len(curves),'realization_descriptors':len(realization),
        'source_dose_never_substitutes_for_target_truth':True,'selection_unchanged':True,'new_SUMO_runs':0,'new_V_runs':0,
        'reaction_window_status':'descriptive; true reaction parameter Unknown','script_sha256':m.sha(Path(__file__))})
    print(json.dumps({'conditional_evaluations':len(curves),'planned_signal_descriptors':len(realization)}))

if __name__=='__main__':main()
