"""Package Task8 derived evidence; reads saved results/config/source, never runs SUMO."""
from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

import analyze_stage_0_5_post_r2_task8_kinematic_mechanism as a

OUT,LOCAL,ROOT=a.OUT,a.LOCAL,a.ROOT


def original_hash(path):
    entries={}
    for line in (path.parent/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split('  ',1)
            entries[name]=digest
    actual=a.sha(path)
    if path.name not in entries or entries[path.name]!=actual:
        raise ValueError(f'Historical payload not verified: {path}')
    return {'path':path.relative_to(ROOT).as_posix(),'expected_sha256':entries[path.name],'actual_sha256':actual}


def source_map():
    folder=LOCAL/'sumo_source'
    tag=a.load(folder/'tag_object.json')
    commit=tag['object']['sha']
    assert commit=='fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3'
    groups={
      'src/microsim/cfmodels/MSCFModel_Krauss.cpp':['MSCFModel_Krauss::followSpeed','MSCFModel_Krauss::patchSpeedBeforeLC','MSCFModel_Krauss::dawdle2'],
      'src/microsim/cfmodels/MSCFModel.cpp':['MSCFModel::maximumSafeFollowSpeed','MSCFModel::maximumSafeStopSpeedBallistic','MSCFModel::brakeGap','MSCFModel::getSecureGap','MSCFModel::insertionFollowSpeed','MSCFModel::calculateEmergencyDeceleration','MSCFModel::finalizeSpeed','MSCFModel::maxNextSpeed','MSCFModel::minNextSpeedEmergency'],
      'src/microsim/cfmodels/MSCFModel_KraussOrig1.cpp':['MSCFModel_KraussOrig1::MSCFModel_KraussOrig1'],
      'src/microsim/MSVehicle.cpp':['MSVehicle::adaptToLeaders','MSVehicle::adaptToLeader','MSVehicle::checkActionStep','MSVehicle::getCurrentApparentDecel'],
      'src/microsim/MSLane.cpp':['MSLane::safeInsertionSpeed'],
      'src/microsim/MSLaneChanger.cpp':['MSLaneChanger::checkChange'],
      'src/microsim/lcmodels/MSLCM_LC2013.cpp':['MSLCM_LC2013::patchSpeed','MSLCM_LC2013::_patchSpeed'],
    }
    records=[]
    for path,functions in groups.items():
        p=folder/Path(path).name
        lines=p.read_text(encoding='utf-8').splitlines()
        spans=[]
        for function in functions:
            indices=[i for i,line in enumerate(lines) if line.startswith(function+'(')]
            if not indices:
                raise ValueError(f'Missing official function {function}')
            start=indices[0]
            end=next(i for i in range(start+1,len(lines)) if lines[i]=='}')
            spans.append({'function':function,'start_line':start+1,'end_line':end+1})
        records.append({'source_path':path,'sha256':a.sha(p),'bytes':p.stat().st_size,
                        'url':f'https://github.com/eclipse-sumo/sumo/blob/{commit}/{path}',
                        'functions':spans})
    return {'status':'Verified official tagged source, not a documentation-only interpretation',
            'tag':'v1_26_0','tag_object_sha':tag['sha'],'commit':commit,'files':records,
            'additional_files_sha256':{p.name:a.sha(p) for p in folder.iterdir() if p.is_file()},
            'normal_follow_chain':['MSVehicle::adaptToLeaders subtracts follower minGap from physical net gap',
              'MSVehicle::adaptToLeader passes current speed, adjusted gap, leader speed and current apparent decel',
              'Krauss::followSpeed applies optional driver perception then maximumSafeFollowSpeed',
              'maximumSafeFollowSpeed uses tau and leader brakeGap, including emergency correction outside lane-change calculation',
              'followSpeed clips to maxNextSpeed and the ballistic emergency deceleration floor',
              'finalizeSpeed applies stops/deceleration/speed limits then dawdling then lane-change speed coordination',
              'non-action internal steps continue the previously chosen acceleration'],
            'insertion_chain':['MSLane::safeInsertionSpeed subtracts minGap, rejects negative space if collision check enabled',
              'insertionFollowSpeed calls maximumSafeFollowSpeed with onInsertion=true and egoSpeed=0 for ballistic',
              'ballistic insertion branch solves constant insertion speed plus subsequent braking; it does not use the normal dynamic branch'],
            'lc_chain':['MSLaneChanger::checkChange extrapolates front/back speeds using tauRemainder when action step differs from native step',
              'front/back secure gaps use car-follow getSecureGap and lane-change safety factor',
              'LC2013 advice can alter wanted speed within the finalizeSpeed bounds; it can generate leader changes and disturbances'],
            'current_step_safe_speed_not_an_absolute_historical_state_feasibility_test':True}


def configurations():
    runs=a.t6.t4.RUNS
    specs=a.t6.t4.SIM_EXPECTED
    roots={name:ET.parse(runs/spec['run_id']/'routes.rou.xml').getroot() for name,spec in specs.items()}
    names=list(roots)
    aa=list(roots[names[0]].iter());bb=list(roots[names[1]].iter())
    assert len(aa)==len(bb)
    changes=[]
    for x,y in zip(aa,bb):
        assert x.tag==y.tag
        for k in set(x.attrib)|set(y.attrib):
            if x.get(k)!=y.get(k):
                changes.append({'element':x.tag,'id':x.get('id'),'attribute':k,'B00':x.get(k),'Round2':y.get(k)})
    assert len(changes)==5 and all(x['element']=='vType' and x['attribute']=='minGap' and x['B00']=='2.5' and x['Round2']=='1.0' for x in changes)
    files={}
    for name,spec in specs.items():
        folder=runs/spec['run_id']
        files[name]={p:a.sha(folder/p) for p in ['routes.rou.xml','network.net.xml','run.sumocfg']}
    assert files[names[0]]['network.net.xml']==files[names[1]]['network.net.xml']
    assert files[names[0]]['run.sumocfg']==files[names[1]]['run.sumocfg']
    return {'status':'Verified','vtypes':{n:[x.attrib for x in r.findall('vType')] for n,r in roots.items()},
            'exact_route_attribute_differences':changes,'files_sha256':files,
            'internal_step_s':.05,'ballistic':True,'action_step_s':.1,'sigma_step_s':1.,
            'NGSIM_tau_identity':'Unknown; no tau assigned from observed gap, event, or vehicle ID',
            'scope':'Historical homogeneous tau1.0/1.6 replay is not these actual heterogeneous vTypes.'}


def history():
    expansion=ROOT/'evidence/results/RES-STAGE-0.5-METHOD-EXPANSION-V1'
    replay=ROOT/'evidence/results/RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1'
    checked=[original_hash(expansion/x) for x in ['response_plan.json','response_metrics.csv','response_summary.json','newell_summary.json','init_summary.json']]
    checked += [original_hash(replay/x) for x in ['replay_plan.json','replay_summary.json']]
    response=a.load(expansion/'response_summary.json')
    old=a.load(replay/'replay_summary.json')
    metrics=pd.read_csv(expansion/'response_metrics.csv')
    assert len(metrics)==324 and metrics.configuration.nunique()==9 and metrics.trajectory_id.nunique()==12
    summary={name:{k:value.get(k) for k in ['model','rows','pairs','seeds','brockfeld_gap_error_pct','nrmse_speed','response_amplitude_ratio','response_lag_difference_s']} for name,value in response['configurations'].items()}
    return {'status':'Verified named payloads only; no historical experiment repeated',
      'verified_named_payloads':checked, 'response_grid':{'rows':len(metrics),'pairs':metrics.trajectory_id.nunique(),
         'configurations':metrics.configuration.nunique(),'seeds':sorted(metrics.seed.unique().tolist()),
         'duration_s':sorted(metrics.duration_s.unique().tolist()),'configuration_summaries':summary},
      'old_replay':{k:old[k] for k in ['pairs_selected','distinct_pairs_replayed','pair_config_combinations_replayed','insertion_rejection_count','insertion_rejection_share','budget_used','paired_difference']},
      'historical_conflicts':[{'Documented Intent':'Historical narrative says 44% of initial pair/config states rejected and 48 independent process invocations.',
         'Actual Implementation':'Saved replay_summary records 26/48 rejection entries =54.1667%, 48 planned invocations and 43 reported executed invocations; 43 scored pair/config combinations and 23 distinct pairs.',
         'Evidence':'RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1/replay_summary.json; STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md sections1,3',
         'Affected Files':['docs/STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md','evidence/results/RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1/replay_summary.json'],
         'Conflict':'Arithmetic discrepancy is verified; actual native process count cannot be re-certified from this summary alone. No re-execution or historical correction.',
         'Status':'Awaiting Researcher Decision'}],
      'retained_limitations':['METHOD-EXPANSION run_metadata hash mismatch and missing trajectory_coverage_matrix were already reported in Task6; no new full-bundle Pass is claimed.',
         'Old homogeneous tau replay and selected pair strata are not current B00 or a population-level network causal comparison.',
         'Primary exact-initial-state and secondary clamped-initial-state outcomes must remain separate.',
         'Historical response lag/amplitude uses episodes selected from differentiated leader positions separately in observed and simulated series; not an independent measured reaction-time truth.'],
      'newell':'Existing prototype summaries only; not SUMO-native Newell and not a model-selection result.',
      'new_historical_experiment_runs':0}


def supplementary():
    data=pd.read_csv(OUT/'event_precursor_decomposition.csv')
    # First packaging after analysis-script split: migrate only this task's own new table.
    if not data.sample_kind.eq('formal_event').all():
        data.to_csv(LOCAL/'all_precursor_decomposition.csv',index=False,float_format='%.12g')
        data.loc[data.sample_kind.eq('nonrisk_control')].to_csv(OUT/'control_precursor_decomposition.csv',index=False,float_format='%.12g')
        data=data.loc[data.sample_kind.eq('formal_event')]
        data.to_csv(OUT/'event_precursor_decomposition.csv',index=False,float_format='%.12g')
    raw=pd.read_csv(LOCAL/'strict_pair_profiles.csv')
    keys=pd.read_csv(LOCAL/'identity_bindings.csv')
    risk=(raw.fixed_pair_closing_mps.gt(0)&(raw.net_gap_m/raw.fixed_pair_closing_mps).between(0,2,inclusive='neither'))
    record=[]
    for key,g in raw.groupby(['scope','region','sample_kind'],sort=True):
        r=risk.loc[g.index]
        record.append({'scope':key[0],'region':key[1],'sample_kind':key[2],'strict_samples':g.unit_index.nunique(),
                       'any_prior_threshold_point_samples':g.loc[r&g.relative_time_s.lt(0)].unit_index.nunique(),
                       'threshold_point_before_minus3_samples':g.loc[r&g.relative_time_s.lt(-3)].unit_index.nunique(),
                       'meaning':'Point diagnostic only, not a new Formal P2 count. Original Task6 nonrisk anchor did not guarantee all five seconds are risk-free; controls are retained unchanged.'})
    a.dump(OUT/'precursor_window_caveats.json',record)
    # Source contribution signs and additive means: no ratios dividing by near-zero closure.
    signs=[]
    for scope,g in data.loc[data.region.eq('source')&data.strict].groupby('scope'):
        signs.append({'scope':scope,'strict_events':len(g),'leader_positive_follower_negative':int((g.C_l_m.gt(0)&g.C_f_m.lt(0)).sum()),
                      'leader_largest_positive_component':int((g.C_l_m.gt(0)&g.C_l_m.gt(g.C_f_m)&g.C_l_m.gt(g.C_initial_m)).sum()),
                      'component_means_m':{m:g[m].mean() for m in ['C_initial_m','C_f_m','C_l_m','C_m']}})
    a.dump(OUT/'contribution_signs.json',signs)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(3,2,figsize=(12,10),sharex=True)
    reps=[]
    for col,scope in enumerate(a.t6.t4.WINDOWS):
        e=data.loc[data.scope.eq(scope)&data.region.eq('source')&data.strict]
        controls=keys.loc[keys.scope.eq(scope)&keys.region.eq('source')&keys.sample_kind.eq('nonrisk_control')]
        candidates=e.merge(keys.loc[keys.scope.eq(scope)&keys.sample_kind.eq('formal_event'),['unit_index','event_id8']],on='unit_index')
        candidates=candidates.merge(controls[['unit_index','event_id8']].rename(columns={'unit_index':'control_unit'}),on='event_id8')
        strict_controls=set(raw.loc[raw.scope.eq(scope)&raw.region.eq('source')&raw.sample_kind.eq('nonrisk_control'),'unit_index'])
        candidates=candidates.loc[candidates.control_unit.isin(strict_controls)].copy()
        m=['initial_gap_m','initial_closing_mps','C_f_m','C_l_m']
        scale=e[m].quantile(.75)-e[m].quantile(.25)
        scale=scale.where(scale.gt(0),1.)
        candidates['distance']=((candidates[m]-e[m].median()).abs()/scale).sum(axis=1)
        pick=candidates.sort_values(['distance','unit_index'],kind='stable').iloc[0]
        reps.append({'scope':scope,'event_unit_index':int(pick.unit_index),'original_control_unit_index':int(pick.control_unit),
                     'selection':'smallest L1 distance to source strict-event medians of initial gap/closing and Cf/Cl, scaled by IQR; original matched control must also be complete; tie by saved analysis unit order',
                     'physical_audit_sample':False})
        for unit,kind,color in [(pick.unit_index,'formal_event','#b43232'),(pick.control_unit,'nonrisk_control','#2865a3')]:
            p=raw.loc[raw.scope.eq(scope)&raw.unit_index.eq(unit)]
            x=p.relative_time_s.to_numpy()
            axes[0,col].plot(x,p.speed_mps,color=color,label=kind+' follower')
            axes[0,col].plot(x,p.onset_leader_speed_mps,color=color,ls='--',label=kind+' fixed leader')
            axes[1,col].plot(x,p.net_gap_m,color=color,label=kind)
            axes[2,col].plot(x,p.fixed_pair_closing_mps,color=color,label=kind)
        axes[0,col].set_title(f'{scope}: central observed pair example, not a physical audit case')
        axes[0,col].legend(fontsize=7)
        for row,label in enumerate(['speed (m/s)','net gap (m)','closing (m/s)']):
            axes[row,col].set_ylabel(label)
            axes[row,col].grid(alpha=.2)
        axes[2,col].set_xlabel('Original observed seconds before onset / control anchor')
    figure.tight_layout()
    dest=LOCAL/'figures/representative_original_matched_pairs.png'
    figure.savefig(dest,dpi=160)
    plt.close(figure)
    a.dump(OUT/'representative_profile_selection.json',reps)
    index=a.load(OUT/'figure_index.json')
    index['local_figures']=sorted(set(index['local_figures']+[dest.relative_to(ROOT).as_posix()]))
    a.dump(OUT/'figure_index.json',index)


def matrices():
    mechanisms=[
      {'mechanism':'H1 initial following state','Observation':'Task6 joint gap/closing support differs; Task8 paired initial gap median differences -1.679448/-0.697992 m.',
       'Derived':'Initial closing contribution differences +0.02286/-0.89916 m in 94/89 complete original matched pairs.',
       'Interpretation':'Smaller initial gap contributes, but positive initial closing alone is not a general five-second explanation.',
       'counterevidence':'Initial closing medians are near zero; event trajectories gain closing during the window.',
       'Hypothesis':'Selection at five-second origin, initial state and earlier interactions may contribute simultaneously.',
       'judgment':'Partial descriptive support for gap; initial-positive-closing-only explanation weakened'},
      {'mechanism':'H2 follower dynamic response','Observation':'Cf medians -0.478536/-2.470556 m; positive Cf 46/105 and26/107.',
       'Derived':'Cl>0 with Cf<0 in50/105 and78/107; follower speed may decrease while closing still grows.',
       'Interpretation':'General follower acceleration is not necessary; relative timing and amplitude of slowing remain relevant.',
       'counterevidence':'No current heterogeneous-B00 replay under qualified common input has been executed; observed kinematic contribution is not an estimated controller response function.',
       'Hypothesis':'Model response conditional on common input differs from observed response.',
       'judgment':'Open; blanket follower-acceleration explanation weakened'},
      {'mechanism':'H3 leader disturbance','Observation':'Cl positive70/105 and91/107; source event Cl medians3.48234/7.387742 m.',
       'Derived':'Paired Cl median differences1.140181/4.021836 m; average Cl exceeds net C because follower/initial terms can offset it.',
       'Interpretation':'Leader speed decline is an important within-window kinematic pathway, especially0805.',
       'counterevidence':'SUMO stable case3 has10.83m/s leader drawdown but only0.449m net closure; network disturbance prevalence is not identified by7 selected cases.',
       'Hypothesis':'Disturbance timing, state conditioning and joint organization differ in current network.',
       'judgment':'Descriptive kinematic support; causal source and real-versus-network population mechanism Unknown'},
      {'mechanism':'H4 lane changes and multi-vehicle interaction','Observation':'Task6 transitions occur near a subset of events. Five-second strict source support105/167 and107/159 without observed lane/leader change.',
       'Derived':'5/7 SUMO near-threshold precursors change leader; strict full-window decomposition available in only1 case per arm.',
       'Interpretation':'Switches are real opportunities in SUMO and matter for case histories, but are insufficient as a universal explanation.',
       'counterevidence':'Stable-pair real events persist; incomplete observation cannot be labeled longitudinal-only.',
       'Hypothesis':'Upstream or earlier multi-vehicle disturbances may feed the observed fixed-pair window.',
       'judgment':'Subset association supported; all-events-cut-in and SUMO-no-lane-change explanations weakened'},
      {'mechanism':'H5 measurement quality','Observation':'Strict event median absolute5s residual .0201168/.0138684m; controls .0221742/.0184404m.',
       'Derived':'Small integrated residual preserves internal consistency, not independent physical truth.',
       'Interpretation':'A gross integrated gap-speed mismatch is not a universal description of the strict subset.',
       'counterevidence':'Shared extraction can make position and speed mutually consistent; excluded identities and lane/headway annotation remain unresolved; Task7 physical reference unavailable.',
       'Hypothesis':'Some extreme or excluded states contain extraction error.',
       'judgment':'Unknown physical truth; cannot assign artifact fraction'},
      {'mechanism':'H6 Krauss and LC constraints','Observation':'Direct official1.26.0 source verified; current B00 five tau/minGap2.5, R2 minGap1 only.',
       'Derived':'Ballistic current-speed-dependent safe acceleration, emergency correction/floor, dawdle acceleration memory and LC secure-gap checks interact.',
       'Interpretation':'Model structure can couple small gap to limited closing; minGap shifts a buffer but does not remove tau/braking/decision constraints.',
       'counterevidence':'SUMO can have high closing and severe leader slowing; source map is not measured native active-constraint telemetry or proof of the unique cause.',
       'Hypothesis':'Which bound binds in current event-like regimes remains to be discriminated with qualified fixed-input evidence.',
       'judgment':'Implementation constraints Verified; attribution of source zero Unknown'}]
    for x in mechanisms:
        x['Proposal']='Preserve all scientific definitions and competing explanations; qualified fixed-input paired analysis is a future conditional discriminator, not authorized here.'
    a.dump(OUT/'mechanism_evidence_matrix.json',mechanisms)
    cases=[
      {'outcome':'Both arms match observed follower speed/gap/closing and C under identical qualified leader input and identical achieved initial physical state',
       'supports':'Conditional response is representable on these cases; network input/state organization becomes a stronger competing explanation.',
       'does_not_support':'No proof that network disturbance generation alone is the cause, no population equivalence, no automatic Round3 candidate.'},
      {'outcome':'Both arms miss observed speed response and Cf consistently under verified common input; minGap-only delta small',
       'supports':'Response mismatch persists beyond the minGap-only contrast in the tested context.',
       'does_not_support':'Does not isolate tau, Krauss safety, sigma, timing, heterogeneity or measurement as a unique cause.'},
      {'outcome':'minGap1 changes gap but not speed/Cf/closing/lag or amplitude',
       'supports':'Spacing or buffer shift with weak dynamic-response discrimination.',
       'does_not_support':'Not a dynamic response repair or restored regional risk equivalence.'},
      {'outcome':'minGap1 moves speed/Cf/closing toward observed response, reproducibly within the approved paired seeds',
       'supports':'minGap-dependent conditional response for the qualified states.',
       'does_not_support':'Not original Round2 source confirmation or proof of network source events or accepted simulation equivalence.'},
      {'outcome':'TTC or P2 changes while core follower response misses observations',
       'supports':'Risk geometry can change without faithful response.',
       'does_not_support':'A threshold crossing alone does not validate a mechanism or the simulator.'},
      {'outcome':'Leader enforcement differs, initial states differ, one arm cannot insert, or identity/exposure fails',
       'supports':'Engineering/input representability limitation or missing comparison support.',
       'does_not_support':'No fair conditional dynamic comparison; no clipping, retry, extra seed or hidden exclusion.'},
      {'outcome':'Effects differ across cases, tau assignments, metrics or approved seeds',
       'supports':'Conditional heterogeneity or insufficient discriminating input.',
       'does_not_support':'No single root-cause identification, power guarantee or favorable-seed selection.'}]
    a.dump(OUT/'fixed_leader_design_assessment.json',{
       'status':'Proposed minimum clarifications; direction retained; execution Blocked and Not Run',
       'existing_design_sufficiency':'Conceptually sufficient for a minGap-only conditional paired contrast after all gates; not sufficient for unique structural mechanism identification.',
       'exact_cancellation':'For common enforced leader speeds, common initial leader speed and equal achieved follower initial speed: delta_C_initial=0, delta_C_l=0, so delta_C=delta_C_f; delta_C_gap=delta_C_f+delta_R. Use the same physical net gap, not minGap-adjusted gap, for initial matching.',
       'minimum_clarifications':[
         'Freeze existing heterogeneous vType assignment before outcomes; NGSIM tau identity is unobserved. Do not substitute a homogeneous type or add a five-type repetition matrix without researcher decision.',
         'Use shared leader disturbance anchors and the same observable horizon in both arms/seeds; old code detects episodes separately from differentiated positions and cannot serve as the new frozen lag estimator.',
         'Report original measured follower/leader speed, physical gap and closing profiles plus signed C_initial,Cf,Cl,Cgap,R; do not score unvalidated acceleration as truth.',
         'Separate descriptive minimum-to-minimum lag from reaction time; multiple minima, flat input, short windows and censored responses remain Unknown with support counts.',
         'Report absolute leader/follower speed response amplitude; undefined or unresolved denominators do not become zero or an arbitrarily stabilized ratio.',
         'Preserve initial insertion failures, achieved-state mismatches, all per-seed results, Formal P2 and separate D1 evaluable exposure; no arm-specific clipping or settling to rescue matching.'],
       'unchanged_seed_repetition_authority':'No seed selection, new N or repeat count set; existing proposed matrix remains awaiting researcher approval.',
       'physical_reference_gate':'Unchanged; independent reference, permission, PTS/time and lane coverage not verified.',
       'discrimination_matrix':cases,'new_simulations':0})


def prepare():
    supplementary()
    a.dump(OUT/'krauss_source_map.json',source_map())
    a.dump(OUT/'sealed_configuration_audit.json',configurations())
    a.dump(OUT/'historical_evidence_review.json',history())
    a.dump(OUT/'krauss_constraint_scope.json',{
      'status':'Not computed; source call-chain analysis completed',
      'reason':'No claim of a full native next-step speed envelope from100ms records: .05s internal action phase, dawdle acceleration memory, lane-change advice, potentially multiple native leaders and perception/control context are not all sealed in measured_state. A standalone insertion quadratic or equilibrium spacing formula is not a substitute.',
      'exact_counterfactual_bounds_produced':False,'NGSIM_tau_assigned':False,
      'current_step_bound_not_absolute_historical_state_feasibility':True})
    review=a.load(a.t6.OUT/'literature_review.json')
    review['task8_reuse']='Re-read Task6 method audit and existing full-text method notes; no new paper, full-text acquisition or calibration method. Raw five-second velocity integration is the researcher-specified diagnostic.'
    a.dump(OUT/'literature_reuse_review.json',review)
    matrices()
    bindings=a.load(OUT/'source_bindings.json')
    bindings['named_historical_payloads']=a.load(OUT/'historical_evidence_review.json')['verified_named_payloads']
    bindings['source_sha256']={p.relative_to(ROOT).as_posix():a.sha(p) for p in [
      Path(a.__file__).resolve(),Path(__file__).resolve(),ROOT/'code/tests/test_stage_0_5_post_r2_task8_kinematic_mechanism.py',
      ROOT/'code/scripts/analyze_stage_0_5_round2_task6_micro_interaction.py',
      ROOT/'code/scripts/analyze_stage_0_5_round2_task4_real_source_support.py',
      ROOT/'code/scripts/export_project_evidence.py']}
    for name in ['analysis_validation.json','event_context_summary.csv','control_matching_audit.json','literature_review.json','joint_distribution_summary.csv']:
        bindings['inputs'][(a.t6.OUT/name).relative_to(ROOT).as_posix()]={'sha256':a.sha(a.t6.OUT/name),'kind':'Task6 portable prior evidence'}
    a.dump(OUT/'source_bindings.json',bindings)
    config=a.load(OUT/'analysis_config.json')
    config['status']='Verified offline analysis complete; scientific mechanism attribution remains conditional'
    a.dump(OUT/'analysis_config.json',config)
    return {'status':'PREPARED_NOT_SEALED','files':len(list(OUT.iterdir()))}


def seal():
    validation=a.load(OUT/'validation_record.json')
    if validation['status']!='PASS_TARGETED_OFFLINE_TASK8':
        raise ValueError('Task8 verification not complete')
    payload=sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'})
    if any((OUT/p).stat().st_size>256*1024 for p in payload):
        raise ValueError('Portable file exceeds existing evidence cap')
    a.dump(OUT/'manifest.json',{'schema':'aad.stage05.post_r2.task8.manifest.v1','task_id':'AAD-S0.5-POST-R2-TASK8',
      'base_head':'832e09520eaac68b5cef898372b664c880b10bdc','payload_files':{n:a.sha(OUT/n) for n in payload},
      'identity_level_payload':False,'raw_trajectories_or_images_in_package':False,'new_simulations':0,
      'scientific_equivalence_accepted':False,'gate_status':'blocked','source_bindings':'source_bindings.json'})
    (OUT/'SHA256SUMS').write_text(''.join(a.sha(OUT/n)+'  '+n+'\n' for n in payload+['manifest.json']),encoding='utf-8')
    return {'status':'SEALED','payload_files':len(payload)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal',action='store_true')
    args=parser.parse_args()
    print(seal() if args.seal else prepare())
