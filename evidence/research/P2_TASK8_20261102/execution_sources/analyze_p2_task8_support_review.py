"""Task8 fixed-candidate review and bounded independent-V decision; no SUMO calls."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
import p2_task8_support_experiment as s

def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def units(out):return s.load(out/'manifest.json')['units']+s.load(out/'round2_manifest.json')['units']
def truth_hash_check(out):
    for phase in [1,2]:
        frozen=s.load(out/'audit'/f'round{phase}_truth_freeze.json')
        for uid,h in frozen['hashes'].items():
            for kind,path in [('raw',out/'raw'/uid/'trajectory.npz'),('truth',out/'truth'/f'{uid}.json'),('audit',out/'audit'/f'{uid}.json')]:assert s.m.sha(path)==h[kind],(uid,kind)
            for label in s.load(out/'truth'/f'{uid}.json'):
                expected=label['label_hash'];label['label_hash']=None
                assert hashlib.sha256(json.dumps(label,sort_keys=True,allow_nan=False).encode()).hexdigest()==expected

def witness(raw,audit,label):
    terminal=label.get('terminal_entity');path=[]
    source_ok=audit['status']=='COMPLETE' and audit['actuated_source']=='s0' and audit['specified_source']=='s0'
    intervals={0:audit.get('actual_source_onset')}
    if source_ok and terminal is not None:
        for i in range(1,terminal+1):
            events=s.a.fast_events(raw['t'],10-raw['v'][:,i],np.ones(len(raw['t']),bool),1.,1.,.05,stop=50.)
            intervals[i]=[events[0]['onset_lower_s'],events[0]['onset_upper_s']] if events else None
            W6=bool(intervals[i-1] and intervals[i] and intervals[i-1][1]<intervals[i][0])
            identity=bool(label.get('native_target_verified') and raw['v'].shape[1]==audit['count']+1)
            quality=bool(all(np.isfinite(raw[k][:,i-1:i+1]).all() for k in ['x','v','a'])
                and np.isfinite(raw['gap'][:,i]).all() and np.all(raw['gap'][:,i]>0)
                and np.all(np.diff(raw['t'])<=.05+1e-8))
            path.append({'leader':f's{i-1}','follower':f's{i}','parent_interval':intervals[i-1],'response_interval':intervals[i],
                'W1':bool(np.all(raw['leader'][:,i]==i-1)),'W2':identity,'W3':bool(np.all(raw['lane'][:,i-1:i+1]==0) and np.all(raw['leader'][:,i]==i-1)),
                'W4':intervals[i-1] is not None,'W5':intervals[i] is not None,'W6':W6,
                'W7':quality,'relative_speed_finite':bool(np.isfinite(raw['v'][:,i-1]-raw['v'][:,i]).all()),
                'W8':'Unknown','same_response_segment':True})
    observed=bool(source_ok and label['state_truth']=='positive' and path and all(all(p[k] for k in ['W1','W2','W3','W4','W5','W6','W7']) for p in path))
    return {'unit_id':audit['unit_id'],'density':audit['density'],'condition':audit['condition'],
        'Potential':bool(source_ok),'Observed':observed,'Qualified':False,'W1_W7_path':path,'W8':'Unknown' if source_ok else 'not a supported specified-source path',
        'W9':'Unknown: full witness requires W8' if path else 'no complete candidate chain',
        'state_positive':label['state_truth']=='positive','source_qualification_unknown':audit['condition'] not in ['N0','N1','A0'],
        'excluded_by_fixed_configuration':['traffic signals','lane changes','merges','target setters','communication controls'],
        'remaining_gap':'native stochastic and upstream/common-cause alternatives not independently certified for source-specific attribution; no independent source-propagation gold standard',
        'terminal_entity':terminal,'legacy_source_interval':audit.get('legacy_executor_source_interval'),'source_interval':audit.get('actual_source_onset')}

def history_geometry(out):
    result=[];decomposition=[]
    for density in s.runner.DENSITIES:
        for condition in ['P22','P11','Plocal','N0']:
            uid=f'C_{density}_{condition}_00'
            with np.load(s.HISTORY/'raw'/uid/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
            t=raw['t']
            for i in range(1,raw['v'].shape[1]-1):
                events=s.a.fast_events(t,10-raw['v'][:,i],np.ones(len(t),bool),1.,1.,.05,stop=50.)
                event=events[0] if events else None;j=int(np.searchsorted(t,event['onset_upper_s'])) if event else None
                result.append({'unit_id':uid,'density':density,'condition':condition,'entity':i,'fixed_cohort':i in s.m.COHORT,
                    'onset_interval':[event['onset_lower_s'],event['onset_upper_s']] if event else None,
                    'x_at_a1_onset':float(raw['x'][j,i]) if j is not None else None,
                    'inside_at_a1_onset':bool(s.m.REGION[0]<=raw['x'][j,i]<s.m.REGION[1]) if j is not None else None,
                    'leader_continuous':bool(np.all(raw['leader'][:,i]==i-1))})
            if condition=='P22':
                for window in [.1,2.]:
                    macro=s.a.fast_edie(t,raw['x'],raw['lane'],window);eligible=(t>=30)&(t<=46)
                    j=np.flatnonzero(eligible)[np.nanargmin(macro['u'][eligible])];total=macro['V'][j]
                    for i in range(raw['v'].shape[1]-1):
                        part=s.a.fast_edie(t,raw['x'][:,i:i+1],raw['lane'][:,i:i+1],window)
                        V=part['V'][j];D=part['D'][j]
                        decomposition.append({'unit_id':uid,'window_s':window,'time_s':float(t[j]),'entity':i,'vehicle_time_s':float(V),
                            'distance_m':float(D),'vehicle_time_weight':float(V/total),'local_u':float(D/V) if V>0 else None,
                            'contribution_to_region_decline_mps':float((10*V-D)/total),'region_decline_mps':float(10-macro['u'][j])})
    s.a.csv_write(out/'audit/task7_follower_geometry.csv',result);s.a.csv_write(out/'audit/task7_macro_dilution_decomposition.csv',decomposition)
    reaudits=[];legacy={r['unit_id']:r for r in rows(s.HISTORY/'audit/micro_witness_levels.csv')}
    for unit in s.load(s.HISTORY/'manifest.json')['units']:
        uid=unit['unit_id'];audit=s.load(s.HISTORY/'audit'/f'{uid}.json')
        if audit['status']!='COMPLETE':continue
        with np.load(s.HISTORY/'raw'/uid/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
        label=next(r for r in s.load(s.HISTORY/'truth'/f'{uid}.json') if r['measurement_layer']=='micro')
        old=audit['actual_source_onset'];audit['legacy_executor_source_interval']=old;audit['actual_source_onset']=s.physical_source_interval(raw,audit)
        checked=witness(raw,audit,label)
        reaudits.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],
            'legacy_source_interval':old,'signature_source_interval':audit['actual_source_onset'],
            'legacy_Observed':legacy[uid]['Observed'],'reaudit_Observed':checked['Observed'],'Qualified':False,
            'W8':'Unknown','scope':'Task8 diagnostic re-read of identical Task7 raw; original 359/47/0 retained; no new independent sample'})
    s.a.csv_write(out/'audit/task7_witness_timestamp_reaudit.csv',reaudits)
    s.dump(out/'audit/task7_timestamp_conflict.json',{'Documented Intent':'Actual source physical onset, never planned time or first final-speed/native divergence',
        'Actual Implementation':'Task7 onset required BOTH actual speed decline and speed != getSpeedWithoutTraCI; during clipped deceleration these readbacks were identical',
        'Evidence':'C_low_P22_00: 30.05s speed9.7689848 and acceleration-4.5, both speed readbacks equal; legacy onset31.75–31.8s',
        'Affected Files':['code/scripts/run_p2_task7_parameter_experiment.py','Task7 frozen audit/label source-time metadata','Task7 source-to-first-hop W6 audit'],
        'Conflict':'Late legacy onset can fail strict W6; independent any-source state/onset labels do not change',
        'Status':'Awaiting Researcher Decision for any retrospective Task7 correction; no Task7 file changed',
        'Task8_local_handling':'Independent command-lower/observed-deceleration-signature-upper interval, kept separate from physical model error; frozen before detectors',
        'legacy_Observed':sum(r['legacy_Observed']=='True' for r in reaudits),
        'diagnostic_Observed_using_signature':sum(r['reaudit_Observed'] for r in reaudits),
        'Qualified':0,'W8_unresolved':True})

def plot_representatives(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(11,9),sharex=True)
    for row,density in enumerate(s.runner.DENSITIES):
        uid=f'S2_{density}_MAX_00'
        with np.load(out/'raw'/uid/'trajectory.npz') as f: raw={k:f[k] for k in f.files}
        if not len(raw['t']):
            for ax in axes[row]:ax.text(.5,.5,'No observations',transform=ax.transAxes)
            continue
        t=raw['t'];macro=s.a.fast_edie(t,raw['x'],raw['lane'],.1)
        axes[row,0].plot(t,raw['v'][:,0],label='Source s0')
        axes[row,0].plot(t,raw['v'][:,1],label='Follower s1')
        axes[row,0].plot(t,raw['v'][:,14],label='Cohort member s14')
        axes[row,0].set_ylabel(f'{density}: speed (m/s)')
        axes[row,1].plot(t,(10-raw['v'][:,s.m.COHORT]).mean(axis=1),label='Fixed full cohort decline')
        axes[row,1].plot(t,10-macro['u'],label='Edie regional decline (0.1 s truth)')
        axes[row,1].axhline(1,color='black',ls='--',lw=.8,label='a* = 1 m/s')
        axes[row,1].axhline(2,color='gray',ls=':',lw=.8,label='2a*')
        axes[row,1].set_ylabel('Baseline-relative decline (m/s)')
        for ax in axes[row]:
            ax.axvspan(30,46,color='gray',alpha=.08);ax.set_xlim(25,50);ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8);axes[0,1].legend(fontsize=8)
    for ax in axes[-1]:ax.set_xlabel('SUMO time (s)')
    fig.suptitle('Task8 fixed representative MAX runs (rep 00): finite-state support, no source-attribution certificate')
    fig.tight_layout();(out/'figures').mkdir(exist_ok=True)
    fig.savefig(out/'figures/fixed_representative_state_traces.png',dpi=150);plt.close(fig)

def review(out):
    if (out/'detector/review_manifest.json').exists():raise FileExistsError('No repeat candidate selection/evaluation')
    truth_hash_check(out);manifest=s.load(out/'manifest.json');uu=units(out);started=time.time()
    s.dump(out/'detector/review_manifest.json',{'frozen_utc':s.utc(),'detector_script_sha256':s.m.sha(Path(s.a.__file__)),
        'analysis_script_sha256':s.m.sha(Path(__file__)),'candidates':manifest['detector_candidates'],
        'all_round_truth_frozen_before_detector':True,'candidate_count':3,'full_83_candidate_search_repeated':False,
        'validation_candidate':'center unchanged; no data-driven promotion to certified stable region'})
    evaluations=[];support=[];witnesses=[];audits=[]
    for unit in uu:
        uid=unit['unit_id'];audit=s.load(out/'audit'/f'{uid}.json');labels=s.load(out/'truth'/f'{uid}.json');audits.append(audit)
        with np.load(out/'raw'/uid/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
        detail=s.measures(raw) if len(raw['t']) else None;cache={}
        if detail:
            inside=(raw['x']>=s.m.REGION[0])&(raw['x']<s.m.REGION[1])&(raw['lane']==0)
            detail['micro']['a1']['span_s']=max(s.spans(raw['t'],inside[:,i]&(10-raw['v'][:,i]>=1-1e-10)&(raw['t']>=30))['span_s'] for i in range(1,raw['v'].shape[1]-1))
        for label in labels:
            layer=label['measurement_layer'];support.append({'unit_id':uid,'round':1 if uid.startswith('S1_') else 2,'layer':layer,'density':unit['density'],'condition':unit['condition'],
                'state':label['state_truth'],'onset':label['onset_allowed_set'],'confirmation':label['confirmation_s'],'recovery':label['recovery_interval_s'],
                'peak_mps':detail[layer]['peak_mps'] if detail else None,'a2_b1':detail[layer]['a2']['positive'] if detail else None,
                'a1_observed_span_s':detail[layer]['a1'].get('span_s') if detail else None,
                'a2_observed_span_s':detail[layer]['a2'].get('span_s') if detail else None,
                'oracle_support_coverage':detail[layer].get('coverage') if detail else None,
                'source_interval':audit.get('actual_source_onset'),'legacy_source_interval':audit.get('legacy_executor_source_interval'),
                'source_min_speed':audit.get('source_min_speed'),'source_min_acceleration':audit.get('source_min_acceleration'),
                'source_max_acceleration':audit.get('source_max_acceleration'),
                'source_final_speed':audit.get('source_final_speed'),'native_target':label['native_target_verified'],'execution_status':audit['status']})
            for name,c in manifest['detector_candidates'].items():
                r=s.a.evaluate(raw,label,s.a.Config(**c),seed=unit['sumo_seed'],cache=cache)
                evaluations.append({'unit_id':uid,'round':1 if uid.startswith('S1_') else 2,'layer':layer,'density':unit['density'],'condition':unit['condition'],'candidate':name,**r})
            if layer=='micro':witnesses.append(witness(raw,audit,label))
    s.a.csv_write(out/'detector/candidate_evaluations.csv',evaluations);s.a.csv_write(out/'truth/support_realization.csv',support);s.a.csv_write(out/'audit/witness_levels.csv',witnesses)
    s.dump(out/'audit/witness_summary.json',{k:sum(bool(r[k]) for r in witnesses) for k in ['Potential','Observed','Qualified','state_positive','source_qualification_unknown']})
    summaries=[]
    for key in sorted({tuple(r[k] for k in ['round','layer','density','condition','candidate']) for r in evaluations}):
        rr=[r for r in evaluations if tuple(r[k] for k in ['round','layer','density','condition','candidate'])==key]
        metric=s.a.summarize(rr);metric['FPR_upper_pointwise95']=s.m.cp_upper(metric['false_positive_n'],metric['negative_n'])
        metric['timely_lower_pointwise95']=s.m.cp_lower(metric['timely_n'],metric['positive_n']+metric['truth_unknown_n'])
        summaries.append(dict(zip(['round','layer','density','condition','candidate'],key))|metric)
    s.a.csv_write(out/'detector/cell_metrics.csv',summaries)
    # Paired descriptive candidate sensitivity. R1 adaptation and calibration selection are explicit.
    contrasts=[];K=max(1,len(summaries));log=math.log(2*K/.05)
    for key in sorted({tuple(r[k] for k in ['round','layer','density','condition']) for r in evaluations}):
        rr=[r for r in evaluations if tuple(r[k] for k in ['round','layer','density','condition'])==key]
        center={r['unit_id']:r for r in rr if r['candidate']=='center' and r['truth_positive']}
        for neighbor in ['theta_neighbor','h_neighbor']:
            diffs=[int(r['timely'])-int(center[r['unit_id']]['timely']) for r in rr if r['candidate']==neighbor and r['unit_id'] in center]
            n=len(diffs);mean=float(np.mean(diffs)) if n else None;radius=math.sqrt(2*log/n) if n else None
            for epsilon in [.01,.025,.05,.1,.2]:
                contrasts.append(dict(zip(['round','layer','density','condition'],key))|{'neighbor':neighbor,'epsilon_stab_scenario':epsilon,
                    'positive_blocks':n,'paired_mean':mean,'simultaneous_radius':radius,'pointwise_descriptive_within_tolerance':abs(mean)<=epsilon if n else None,
                    'bound_within_tolerance':abs(mean)+radius<=epsilon if n else None,'epsilon_not_frozen':True,
                    'sufficient_zero_difference_planning_n':math.ceil(8*log/epsilon**2),'no_scientific_stability_certification':True})
    s.a.csv_write(out/'detector/stability_tolerance_sensitivity.csv',contrasts)
    interactions=[];historical=rows(s.HISTORY/'detector/interaction_summary.csv')
    for row in historical:
        for gamma in [.01,.05,.1,.2,.5]:
            mean=float(row['mean_D']);low=float(row['lower']);high=float(row['upper'])
            interactions.append({**row,'gamma_int_scenario':gamma,'estimate_within_gamma':abs(mean)<=gamma,
                'simultaneous_bound_within_gamma':max(abs(low),abs(high))<=gamma,'gamma_not_frozen':True,
                'sufficient_zero_interaction_planning_n':math.ceil(32*math.log(2*len(historical)/.05)/gamma**2),'scope':'reuse Task7 paired calibration summaries; not new independent n'})
    s.a.csv_write(out/'detector/interaction_tolerance_sensitivity.csv',interactions)
    history_geometry(out)
    plot_representatives(out)
    complete=[r for r in audits if r['status']=='COMPLETE'];count=Counter((r['layer'],r['density'],r['state']) for r in support)
    result={'planned_units':len(uu),'completed':len(complete),'failed_or_not_executed':len(uu)-len(complete),
        'execution_status_counts':dict(Counter(r['status'] for r in audits)),'truth_labels':len(support),'candidate_evaluations':len(evaluations),
        'count_table':[dict(layer=k[0],density=k[1],state=k[2],n=v) for k,v in sorted(count.items())],
        'elapsed_analysis_s':time.time()-started,'mean_successful_run_s':float(np.mean([r['elapsed_s'] for r in complete])),
        'raw_bytes':sum((out/'raw'/u['unit_id']/'trajectory.npz').stat().st_size for u in uu),
        'collisions':sum(r['collisions'] for r in audits),'teleports':sum(r['teleports'] for r in audits),'target_setters':sum(r['native_target_setters'] for r in audits),
        'actual_resources':s.budget(out),'independent_V_units':0}
    s.dump(out/'audit/review_completion.json',result);print(json.dumps(result))

def plan(out):
    result=s.load(out/'audit/review_completion.json');families=[]
    support=rows(out/'truth/support_realization.csv')
    def add(layer,density,condition,endpoint,role,limit,truth='available'):
        families.append({'claim_id':f'V{len(families)+1:03d}','layer':layer,'density':density,'condition':condition,'endpoint':endpoint,'role':role,'limit':limit,'truth_support':truth,'candidate':'center only'})
    for layer in s.a.LAYERS:
        for density in s.runner.DENSITIES:
            for condition in ['N0','N1']:add(layer,density,condition,'FPR','state',.01)
            positive_available=any(r['layer']==layer and r['density']==density and r['condition']=='MAX' and r['state']=='positive' for r in support)
            add(layer,density,'MAX','timely_miss_including_unknown','state',.05,'available' if positive_available else 'Unknown: no positive state support in bounded MAX design')
            for condition in ['N0','N1','A0','MAX']:add(layer,density,condition,'state_unknown','state',.05)
    for density in s.runner.DENSITIES:
        for condition in ['N0','N1','A0']:add('micro',density,condition,'false_source_attribution','attribution',.01)
        add('micro',density,'MAX','source_qualification_unknown','attribution',.05)
        add('micro',density,'MAX','qualified_timely_miss','attribution',.05,'Unknown: independent specified-source positive truth absent')
    J=len(families);state_J=sum(r['role']=='state' for r in families);assert J==78 and state_J==63
    s.a.csv_write(out/'detector/validation_family.csv',families)
    plans=[];lookup={}
    for scope,j in [('fixed_state_only',state_J),('fixed_state_plus_attribution',J)]:
        for failure in [.05,.005]:
            for name,limit,good in [('FPR_FAR',.01,.002),('finite_miss_unknown',.05,.01),('eta1',.0025,.0005),('eta5',.0125,.0025)]:
                r=s.m.exact_plan(limit,good,failure/j,power=1-.1/j)
                r.update({'scope':scope,'J':j,'family_failure':failure,'endpoint':name,'zero_failure_n':math.ceil(math.log(failure/j)/math.log1p(-limit))})
                plans.append(r);lookup[(scope,failure,name)]=r
    s.a.csv_write(out/'detector/exact_power_plans.csv',plans)
    nneg=lookup[('fixed_state_plus_attribution',.05,'FPR_FAR')]['n'];npos=lookup[('fixed_state_plus_attribution',.05,'finite_miss_unknown')]['n']
    mean_bytes=result['raw_bytes']/result['planned_units'];seconds=result['mean_successful_run_s'];resource=s.budget(out)
    def cost(negative,positive):
        n=3*(3*negative+positive)
        return {'independent_runs_favorable_lower_bound':n,'negative_per_homogeneous_cell':negative,'positive_per_homogeneous_cell':positive,
            'ideal_four_worker_wall_s':n*seconds/4,'serial_mitigation_wall_s':n*seconds,'raw_bytes_lower_bound':math.ceil(n*mean_bytes),
            'assumptions':'perfect positive yield, source truth and zero invalid runs; all three layers share runs; logs/config/temporary bytes and nonpositive yield increase cost'}
    finite=cost(nneg,npos);state_cost=cost(lookup[('fixed_state_only',.05,'FPR_FAR')]['n'],lookup[('fixed_state_only',.05,'finite_miss_unknown')]['n'])
    labels=rows(out/'truth/support_realization.csv');deficits=[]
    for layer in s.a.LAYERS:
        for density in s.runner.DENSITIES:
            rr=[r for r in labels if r['layer']==layer and r['density']==density and r['condition'] in ['LONG','MAX']]
            if not any(r['state']=='positive' for r in rr):deficits.append({'layer':layer,'density':density,'reason':'no a1b1 positive under either bounded source design'})
    strict=[]
    for eta,name in [(.01,'eta1'),(.05,'eta5')]:
        p=lookup[('fixed_state_plus_attribution',.005,name)];c=cost(lookup[('fixed_state_plus_attribution',.005,'FPR_FAR')]['n'],p['n'])
        K=45;margin=eta/2;cdf=s.m.exact_plan(margin,margin/5,.02/K,power=1-.1/K)
        strict.append({'eta_scenario':eta,'eta_frozen':False,'timely_miss_max':eta/4,'unknown_max':eta/4,
            'timely_detection_target':1-eta/4,'J_measure':J,'alpha_measure_scenario':.005,'measurement_plan':p,**c,
            'CDF_grid_J':K,'CDF_scope':'one frozen source design per density x3 layers x5 H_cal points; local pulses outside this restricted proposal, no F0 claim',
            'CDF_alpha_scenario':.02,'CDF_Hoeffding_zero_early_n':math.floor(math.log(K/.02)/(2*margin**2))+1,
            'CDF_exact_good_rate_power_plan':cdf,'independent_V_positive':0,'independent_V_negative':0,
            'independent_V_timely_sensitivity':None,'independent_V_unknown':None,'independent_V_FPR':None,'independent_V_FAR':None,
            'physical_delay_mass_bound':None,'truth_clock_measurement_error':None,'Formal_F0':None,
            'budget_expression':'detected_early + unknown + epsilon_sampling + m_delay + epsilon_truth_clock_measurement < eta',
            'complete_budget_evaluable':False,'verdict':'Not established / Unknown'})
    # R2 fixed-condition finite-state CDF proxy, including known state-negative runs.
    evals=rows(out/'detector/candidate_evaluations.csv');proxy=[];r2=s.load(out/'round2_manifest.json')
    main={d['density']:d['condition'] for d in r2['selected_designs'] if d['condition'] in ['LONG','MAX']}
    for layer in s.a.LAYERS:
        for density in s.runner.DENSITIES:
            condition=main.get(density,'MAX');rr=[r for r in evals if r['round']=='2' and r['candidate']=='center' and r['density']==density and r['layer']==layer and r['condition']==condition]
            for H in [0.,4.,8.,12.,16.]:
                n=len(rr);early=unknown=0
                for r in rr:
                    label=next(x for x in s.load(out/'truth'/f'{r["unit_id"]}.json') if x['measurement_layer']==layer)
                    source=label['actual_source_onset']
                    unknown+=int(r['unknown']=='True' or not source)
                    early+=int(bool(source) and bool(r['availability_s']) and float(r['availability_s'])-source[0]<=H+4.)
                proxy.append({'layer':layer,'density':density,'condition':condition,'H_cal_s':H,'blocks':n,
                    'p_detected_early':early/n if n else None,'p_unknown':unknown/n if n else None,
                    'epsilon_sampling':math.sqrt(math.log(45/.02)/(2*n)) if n else None,
                    'm_delay_certificate':None,'epsilon_truth_clock_measurement':None,'complete_bound':None,'bridge_pass':False,'scope':'supplementary finite state proxy only; not independent V or F0'})
    s.a.csv_write(out/'detector/finite_state_cdf_budget.csv',proxy)
    decision={'status':'NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT' if deficits else 'NOT_EXECUTED_RESOURCE_LIMIT',
        'additional_blockers':['exact fixed-candidate family costs exceed remaining two-hour/10GiB budget','independent source attribution truth missing; qualified sensitivity cannot be powered'],
        'missing_state_support':deficits,'family_size':J,'state_only_family_size':state_J,'fixed_configurations_per_layer':1,
        'stability_region_claimed':False,'local_pulse_validation_claimed':False,'scope_reason':'fixed candidate and one bounded main source condition per density; all density/layer cells retained. Local pulse effects are calibration diagnostics; no stability or arbitrary source-dose extrapolation.',
        'sensitivity_delay_miss_same_binary_endpoint':True,'delay_budget_s':4.,'beta_V':.05,'alpha_measure_not_frozen':True,
        'family_power_target':.9,'good_rates':{'FPR_FAR':.002,'miss_unknown':.01},'full_power_supported':False,
        'fixed_state_plus_attribution_cost':finite,'fixed_state_only_cost':state_cost,'remaining_wall_s':7200-resource['elapsed_wall_s'],
        'remaining_output_bytes':10*2**30-resource['output_bytes'],'Independent_V_namespace':[20261102,8,303],
        'V_seeds_consumed':0,'historical_or_supplementary_data_relabelled_V':False,
        'parameters_for_freeze':False,'strict_scenarios':strict,'pre_V_manifest_executed':False,
        'family_manifest_sha256':s.m.sha(out/'detector/validation_family.csv')}
    s.dump(out/'detector/independent_V_decision.json',decision);s.dump(out/'detector/bridge_feasibility.json',strict)
    print(json.dumps({'status':decision['status'],'J':J,'state_J':state_J,'cost':finite,'missing_support':deficits,'actual_resources':resource}))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--phase',choices=['review','plan'],required=True);args=p.parse_args()
    out=args.output_dir.resolve()
    if out.parent!=s.ROOT/'code/outputs/calibration' or not out.name.startswith('p2_task8_'):raise ValueError('isolated Task8 output only')
    if args.phase=='review':review(out)
    else:plan(out)

if __name__=='__main__':main()
