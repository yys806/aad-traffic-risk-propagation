"""Exact independent-V resource planning and finite-state CDF sensitivity."""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import sys
import numpy as np
import p2_task7_measurement as m
import analyze_p2_task7_parameter_experiment as a

def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args();out=args.output_dir.resolve()
    selected=json.loads((out/'detector/calibration_selection.json').read_text(encoding='utf-8'))
    cplan=json.loads((out/'detector/candidate_manifest.json').read_text(encoding='utf-8'))
    family=[];neighborhood={}
    for layer in a.LAYERS:
        center=a.Config(**selected[layer]['parameters']);grid=cplan['grids'][layer];neighbors=[center]
        for parameter in ['theta','h']:
            values=[v for v in grid[parameter] if v!=getattr(center,parameter)]
            value=min(values,key=lambda v:abs(v-getattr(center,parameter)))
            neighbors.append(a.replace(center,**{parameter:value}))
        neighborhood[layer]=[a.asdict(c) for c in neighbors]
        for density in a.DENSITIES:
            endpoints=[('N0','FPR'),('N1','FPR')]
            positive=['P11','P21','P12','P22']+(['Plocal'] if layer!='cohort' else [])
            endpoints +=[(condition,'timely_miss') for condition in positive]
            endpoints +=[(condition,'Unknown') for condition in a.CONDITIONS]
            if layer=='micro':
                endpoints +=[('N1','FAR'),('A0','FAR')]
                endpoints +=[(condition,'qualified_timely_miss') for condition in positive]
            for index,c in enumerate(neighbors):
                for condition,endpoint in endpoints:
                    family.append({'claim_id':f'{layer}:{density}:{condition}:{endpoint}:candidate{index}',
                        'layer':layer,'density':density,'condition':condition,'endpoint':endpoint,
                        'candidate_index':index,'candidate':a.config_key(c),'kind':'performance'})
            for index in (1,2):
                for condition,endpoint in endpoints:
                    family.append({'claim_id':f'{layer}:{density}:{condition}:{endpoint}:neighbor{index}_difference',
                        'layer':layer,'density':density,'condition':condition,'endpoint':endpoint,
                        'candidate_index':index,'candidate':a.config_key(neighbors[index]),'kind':'stability'})
    J=len(family);beta=.05;resource=json.loads((out/'audit/resource_actual.json').read_text(encoding='utf-8'))
    a.csv_write(out/'detector/validation_family.csv',family)
    plans=[]
    for budget in [.05,.005]:
        for purpose,limit,good in [('FPR_FAR',.01,.002),('finite_miss_unknown',.05,.01),
            ('eta1_miss_unknown',.0025,.0005),('eta5_miss_unknown',.0125,.0025)]:
            for method,power in [('per_claim_power',.9),('conservative_family_power',1-.1/J)]:
                result=m.exact_plan(limit,good,budget/J,power=power)
                plans.append({'purpose':purpose,'total_failure_budget':budget,'family_size':J,'power_scope':method,
                    'zero_bad_favorable_n':math.ceil(math.log(budget/J)/math.log1p(-limit)),**result})
    a.csv_write(out/'detector/exact_sample_size_power.csv',plans)
    family_plans={(r['purpose'],r['total_failure_budget']):r for r in plans if r['power_scope']=='conservative_family_power'}
    n_neg=family_plans[('FPR_FAR',.05)]['n'];n_pos=family_plans[('finite_miss_unknown',.05)]['n']
    # These are favorable realization-count lower bounds; actual positive yield can be zero.
    def cost(nbad,npositive):
        runs=3*(3*nbad+5*npositive)
        return {'planned_run_lower_bound':runs,'perfect_label_yield_assumption':True,
            'wall_s_at_measured_4workers':runs*resource['mean_run_s']/4,
            'raw_bytes_at_measured_size':runs*resource['raw_bytes']/576,
            'required_negative_per_homogeneous_cell':nbad,'required_positive_per_homogeneous_cell':npositive}
    finite_cost=cost(n_neg,n_pos);bridge=[]
    for eta,purpose in [(.01,'eta1_miss_unknown'),(.05,'eta5_miss_unknown')]:
        certificate=family_plans[(purpose,.005)]
        sampling_margin=eta/2;K=3*3*5*5  # layer x density x time x fixed design strata
        cdf_n=math.floor(math.log(K/.02)/(2*sampling_margin**2))+1
        cdf_exact=m.exact_plan(sampling_margin,sampling_margin/5,.02/K,power=1-.1/K)
        c=cost(family_plans[('FPR_FAR',.005)]['n'],certificate['n'])
        bridge.append({'eta_scenario':eta,'eta_frozen':False,'timely_miss_budget':eta/4,'unknown_budget':eta/4,
            'timely_detection_lower_target':1-eta/4,'sampling_and_detected_mass_remaining':sampling_margin,
            'formal_measure_failure_budget_scenario':.005,'measurement_exact_certificate':certificate,
            'cdf_grid_claims':K,'cdf_failure_budget_scenario':.02,
            'favorable_zero_early_mass_hoeffding_n':cdf_n,
            'cdf_exact_fixed_grid_power_plan':cdf_exact,'cdf_n_scope':'per density and homogeneous domain; not a formal F0 sample',
            **c,'independent_V_positive_n':0,'independent_V_negative_n':0,'independent_V_unknown_n':0,
            'CDF_population_F0':'Unknown: no Formal A/Qpre no-message population',
            'physical_onset_error':'Unknown: finite a*/b* state is not arbitrary earliest physical response',
            'formal_clock_error':'Unknown: same simulation phase audit only',
            'status':'Unknown / strict bridge not established',
            'complete_budget_condition':'detected_early + Unknown + sampling_upper + timely_miss + applicable_truth_clock_measurement_error < eta',
            'budget_evaluable':False})
    m.dump(out/'detector/bridge_feasibility.json',bridge)
    # Finite-state calibration CDFs only: condition-specific iid bounds, then fixed equal weights.
    # Never pool fixed, heterogeneous condition counts into an iid binomial sample.
    evals=read_csv(out/'detector/parameter_evaluations.csv');labelmap={}
    for path in (out/'truth').glob('C_*.json'):
        for label in json.loads(path.read_text(encoding='utf-8')):labelmap[(label['unit_id'],label['measurement_layer'])]=label
    chosen=[r for r in evals if r['config_id']==selected[r['layer']]['config_id']]
    cdf=[];K=3*3*5*5;alpha=.02/K
    for layer in a.LAYERS:
        for density in a.DENSITIES:
            for H in [0.,4.,8.,12.,16.]:
                cells=[]
                for condition in ['P11','P21','P12','P22','Plocal']:
                    rows=[r for r in chosen if r['layer']==layer and r['density']==density and r['condition']==condition]
                    detected=unknown=possible=timelybad=positive=0
                    for r in rows:
                        label=labelmap[(r['unit_id'],layer)];relative=label['actual_source_onset']
                        if not relative or label['state_truth']=='unknown':unknown+=1;possible+=1;continue
                        if label['state_truth']=='positive':
                            positive+=1;possible+=int(label['onset_allowed_set'][0]-relative[1]<=H)
                            timelybad+=int(r['timely']!='True')
                        unknown+=int(r['unknown']=='True')
                        if r['availability_s']:
                            detected+=int(float(r['availability_s'])-relative[0]<=H+4.)
                    n=len(rows);eps=math.sqrt(math.log(1/alpha)/(2*n))
                    cells.append({'condition':condition,'n':n,'detected_early_mass':detected/n,
                        'unknown_mass':unknown/n,'finite_truth_possible_mass':possible/n,'sampling_epsilon':eps,
                        'positive_n':positive,'timely_miss_n':timelybad,
                        'timely_miss_upper_pointwise':m.cp_upper(timelybad,positive)})
                detected=sum(c['detected_early_mass'] for c in cells)/5;unknown=sum(c['unknown_mass'] for c in cells)/5
                epsilon=sum(c['sampling_epsilon'] for c in cells)/5
                cdf.append({'layer':layer,'density':density,'H_cal_grid_s':H,'planned_independent_C_blocks':120,
                    'detected_early_mass':detected,'unknown_mass':unknown,'sampling_epsilon':epsilon,
                    'finite_truth_possible_mass':sum(c['finite_truth_possible_mass'] for c in cells)/5,
                    'CDF_upper_without_valid_delay_certificate':None,'partial_budget_floor':min(1.,detected+unknown+epsilon),
                    'strict_eta1_pass':False,'strict_eta5_pass':False,'scope':'calibration finite-state proxy only; not F0',
                    'strata':cells})
    a.csv_write(out/'detector/calibration_cdf_budget.csv',cdf)
    q={r['unit_id'] for r in chosen};expected=576
    assert len(q)==expected
    validation={'status':'NOT_EXECUTED','reason':['Required finite-domain power/sample size exceeds declared V resource budget',
        'Several predeclared density/positive cells lack actual target positives; more seeds cannot be assumed to fix support',
        'Micro source-specific attribution truth and scientific equivalence margin remain Unknown'],
        'family_size':J,'family_failure_budget':beta,'family_manifest_sha256':m.sha(out/'detector/validation_family.csv'),
        'neighborhood':neighborhood,'frozen_selection_sha256':m.sha(out/'detector/calibration_selection.json'),
        'new_seed_namespace':[20261102,7,271828],'new_validation_seeds_consumed':0,
        'finite_domain_required':finite_cost,'V_wall_budget_s':7200,'V_output_budget_bytes':10*2**30,
        'power_good_assumptions':{'FPR_FAR':.002,'finite_miss_unknown':.01,'eta1':.0005,'eta5':.0025},
        'historical_validation_reused':False,'exploration_converted_to_validation':False,
        'stability_margin':None,'stability_required_n':'Unknown without researcher-frozen equivalence margin',
        'binary_performance_claims':sum(r['kind']=='performance' for r in family),
        'stability_claims':sum(r['kind']=='stability' for r in family),
        'family_power_status':'type-II allocation for binary performance only; complete family not powered without stability margin/truth',
        'independent_validation_performance':'Unknown','recommended_for_freeze':False,
        'formal_parameters_frozen':[],'script_sha256':m.sha(Path(__file__))}
    m.dump(out/'detector/independent_validation_manifest.json',validation)
    print(json.dumps({'J_V':J,'finite_cost':finite_cost,'independent_V':'NOT_EXECUTED','eta_scenarios':[.01,.05]},ensure_ascii=False))

if __name__=='__main__':main()
