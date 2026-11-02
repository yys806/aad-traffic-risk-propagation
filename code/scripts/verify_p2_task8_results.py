"""Read-only experiment verification; writes only its own Task8 audit result."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import numpy as np
import p2_task8_support_experiment as s
import analyze_p2_task8_support as a
from verify_p2_task7_results import independent_cdf


def verify(out):
    manifest=s.load(out/'manifest.json'); uu=a.units(out)
    assert len(uu)==268 and len({u['unit_id'] for u in uu})==268
    assert s.m.sha(out/'manifest.json')==s.load(out/'provenance.json')['manifest_sha256']
    for rel,digest in manifest['source_hashes'].items():
        assert s.m.sha(s.ROOT/rel)==digest,rel
        assert s.m.sha(out/'snapshots'/Path(rel).name)==digest,rel
    history=s.load(out/'audit/task7_input_hashes.json')['hashes']
    for uid,hh in history.items():
        for key,path in {'raw':s.HISTORY/'raw'/uid/'trajectory.npz','truth':s.HISTORY/'truth'/f'{uid}.json','audit':s.HISTORY/'audit'/f'{uid}.json'}.items():
            assert s.m.sha(path)==hh[key],(uid,key)
    assert s.m.sha(s.HISTORY/'audit/truth_freeze.json')==s.load(out/'provenance.json')['history_truth_freeze_sha256']
    a.truth_hash_check(out)
    review=s.load(out/'detector/review_manifest.json')
    assert review['analysis_script_sha256']==s.m.sha(out/'snapshots/analyze_p2_task8_support_review.py')
    assert s.load(out/'audit/analysis_revision.json')['planning_sha256']==s.m.sha(s.ROOT/'code/scripts/analyze_p2_task8_support.py')
    histories={u['sumo_seed'] for u in s.load(s.HISTORY/'manifest.json')['units']}
    seeds={u['sumo_seed'] for u in uu}
    assert len(seeds)==len(uu) and not seeds&histories
    assert len({u['dependency_block'] for u in uu})==len(uu)
    assert all(u['dependency_block']==u['unit_id'] for u in uu)
    assert manifest['seed_namespaces']['independent_V'] not in [manifest['seed_namespaces']['calibration_R1'],manifest['seed_namespaces']['supplementary_R2']]
    for round_number in [1,2]:
        serial=s.load(out/'audit'/f'round{round_number}_serial_manifest.json')
        assert serial['attempted_failed_seeds_retried']==0
        assert serial['source_hash']==s.m.sha(s.ROOT/'code/scripts/run_p2_task8_serial_continuation.py')
    evals=a.rows(out/'detector/candidate_evaluations.csv')
    assert len(evals)==len(uu)*3*3
    assert len({(r['unit_id'],r['layer'],r['candidate']) for r in evals})==len(evals)
    center={(r['unit_id'],r['layer']):r for r in evals if r['candidate']=='center'}
    counts=Counter();states=Counter();failure=[];replayed=[];label_n=0
    for u in uu:
        uid=u['unit_id'];audit=s.load(out/'audit'/f'{uid}.json');labels=s.load(out/'truth'/f'{uid}.json')
        assert len(labels)==3 and {r['measurement_layer'] for r in labels}==set(s.a.LAYERS)
        assert audit['native_target_setters']==audit['collisions']==audit['teleports']==0
        assert all(c['vehicle']==u['actuated_source'] and c['vehicle'] in ['s0','decoy'] for c in audit.get('controls',[]))
        counts[audit['status']]+=1
        with np.load(out/'raw'/uid/'trajectory.npz') as f: raw={k:f[k] for k in f.files}
        if audit['status']=='COMPLETE':
            assert len(raw['t'])==audit['rows']==1000
            assert np.allclose(np.diff(raw['t']),.05,rtol=0,atol=1e-10)
            assert raw['v'].shape==(1000,u['count']+1)
            assert all(np.isfinite(raw[k]).all() for k in ['v','a','x','native'])
            assert np.all(raw['lane'][:,:-1]==0) and np.all(raw['lane'][:,-1]==1)
            assert np.all(raw['leader'][:,1:-1]==np.arange(u['count']-1)[None,:])
            assert np.all(raw['gap'][:,1:-1]>0)
            assert audit['source_min_speed']>=-1e-9
            assert audit['source_min_acceleration']>=-4.5-1e-6 and audit['source_max_acceleration']<=2.6+1e-6
            assert audit['actual_source_onset']==s.physical_source_interval(raw,audit)
            oracle={r['measurement_layer']:r for r in s.m.truth(raw,audit)}
            for label in labels:
                for key in ['state_truth','onset_allowed_set','confirmation_s','recovery_interval_s','terminal_entity','native_target_verified','coverage']:
                    assert label[key]==oracle[label['measurement_layer']][key],(uid,key)
        else:
            failure.append(uid);assert not len(raw['t']) and not audit.get('controls')
            assert all(r['state_truth']=='unknown' for r in labels)
        cache={}
        for label in labels:
            label_n+=1;layer=label['measurement_layer'];states[(layer,u['density'],label['state_truth'])]+=1
            r=s.a.evaluate(raw,label,s.a.Config(**manifest['detector_candidates']['center']),seed=u['sumo_seed'],cache=cache)
            saved=center[(uid,layer)]
            for key in ['truth_positive','truth_negative','truth_unknown','alarm','valid_detection','timely','early_alarm','unknown','false_positive','false_attribution']:
                assert saved[key]==('' if r[key] is None else str(r[key])),(uid,layer,key)
            for key in ['delay_lower_s','delay_upper_s','availability_s','coverage']:
                assert (saved[key]=='' and r[key] is None) or (r[key] is not None and math.isclose(float(saved[key]),r[key],abs_tol=1e-10)),(uid,key)
            replayed.append({'layer':layer,**r})
    assert failure==['S1_medium_MAX_01'] and counts['COMPLETE']==267
    summaries={layer:s.a.summarize([r for r in replayed if r['layer']==layer]) for layer in s.a.LAYERS}
    plans=a.rows(out/'detector/exact_power_plans.csv');assert len(plans)==16
    for r in plans:
        n=int(r['n']);k=int(r['max_bad']);limit=float(r['limit']);good=float(r['good']);f=float(r['failure']);power=independent_cdf(k,n,good)
        assert independent_cdf(k,n,limit)<=f*(1+1e-7)
        assert independent_cdf(k+1,n,limit)>f*(1-1e-7)
        assert power>=float(r['target_power'])-1e-9 and abs(power-float(r['power']))<1e-8
        assert n>=int(r['zero_failure_n'])
    d=s.load(out/'detector/independent_V_decision.json');family=a.rows(out/'detector/validation_family.csv')
    assert len(family)==d['family_size']==78 and sum(r['role']=='state' for r in family)==63
    assert d['V_seeds_consumed']==0 and d['status']=='NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT'
    assert s.m.sha(out/'detector/validation_family.csv')==d['family_manifest_sha256']
    assert len(d['missing_state_support'])==3 and not d['full_power_supported']
    for r in d['strict_scenarios']:
        assert r['independent_V_positive']==r['independent_V_negative']==0
        assert not r['complete_budget_evaluable'] and not r['eta_frozen']
        assert r['CDF_Hoeffding_zero_early_n']==math.floor(math.log(45/.02)/(2*(r['eta_scenario']/2)**2))+1
        assert r['physical_delay_mass_bound'] is None and r['truth_clock_measurement_error'] is None
        assert r['negative_per_homogeneous_cell']==max(r['negative_sample_requirement_components'].values())
        assert r['independent_runs_favorable_lower_bound']==3*(3*r['negative_per_homogeneous_cell']+r['measurement_plan']['n'])
        cdf=r['CDF_exact_good_rate_power_plan']
        assert independent_cdf(cdf['max_bad'],cdf['n'],cdf['limit'])<=cdf['failure']*(1+1e-7)
        assert independent_cdf(cdf['max_bad'],cdf['n'],cdf['good'])>=cdf['target_power']-1e-9
    w=s.load(out/'audit/witness_summary.json');assert w['Qualified']==0
    protected='\n'.join(subprocess.check_output(['git','diff',*index,'--name-only','--','code/src','code/configs','AGENTS.md'],cwd=s.ROOT,text=True).strip() for index in [[],['--cached']]).strip()
    assert not protected,protected
    # A later read-only reproduction must not compare today's clock with an
    # already finished experiment's start time. Enforce its sealed run records.
    resources=s.load(out/'audit/review_completion.json')['actual_resources']
    assert resources['elapsed_wall_s']<7200 and resources['output_bytes']<10*2**30
    assert s.load(out/'audit/round2_serial_completion.json')['resources']['elapsed_wall_s']<7200
    current_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    assert current_bytes<10*2**30
    result={'status':'PASS','completed':counts['COMPLETE'],'planned':len(uu),'failed':failure,'labels_checked':label_n,
        'task7_hash_units_unchanged':len(history),'seed_namespaces_disjoint':True,'V_seeds_consumed':0,
        'center_operator_replays':len(center),'center_metrics_recomputed':summaries,
        'independent_exact_binomial_plan_checks':len(plans),'independent_CDF_exact_plan_checks':2,
        'native_target_controls':0,'collisions':0,'teleports':0,
        'sealed_experiment_resources':resources,'output_bytes_at_recompute':current_bytes,
        'protected_paths_unchanged':True,'script_sha256':s.m.sha(Path(__file__)),
        'scope':'all raw/truth/audit and source hashes; native state oracle replay; fixed-center detector replay; independent lgamma binomial CDF; no new simulation or parameter search',
        'scientific_certification':False}
    s.dump(out/'audit/independent_recompute.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);verify(p.parse_args().output_dir.resolve())
