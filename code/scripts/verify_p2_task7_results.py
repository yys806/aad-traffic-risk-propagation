"""Independent table/hash recheck for Task7; does not rerun SUMO or tune detectors."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import p2_task7_measurement as m

def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def independent_cdf(k,n,p):
    if k<0:return 0.
    terms=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)+i*math.log(p)+(n-i)*math.log1p(-p) for i in range(k+1)]
    peak=max(terms);return min(1.,math.exp(peak)*math.fsum(math.exp(v-peak) for v in terms))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();out=args.output_dir.resolve()
    freeze=load(out/'audit/truth_freeze.json');manifest=load(out/'manifest.json');selection=load(out/'detector/calibration_selection.json')
    assert m.sha(out/'manifest.json')==freeze['manifest_sha256']
    failed=[];label_counts=Counter();label_hash_checked=0;complete=0
    for uid,hashes in freeze['hashes'].items():
        assert m.sha(out/'truth'/f'{uid}.json')==hashes['truth']
        assert m.sha(out/'raw'/uid/'trajectory.npz')==hashes['raw']
        assert m.sha(out/'audit'/f'{uid}.json')==hashes['audit']
        audit=load(out/'audit'/f'{uid}.json');labels=load(out/'truth'/f'{uid}.json')
        for label in labels:
            original=label['label_hash'];label['label_hash']=None
            assert hashlib.sha256(json.dumps(label,sort_keys=True,allow_nan=False).encode()).hexdigest()==original
            label_hash_checked+=1;label_counts[(label['measurement_layer'],label['state_truth'])]+=1
        assert audit['native_target_setters']==0 and audit['collisions']==0 and audit['teleports']==0
        assert all(c['vehicle'] in ('s0','decoy') for c in audit['controls'])
        if audit['status']=='FAILED_STOP':
            failed.append(uid);assert audit['rows']==0 and all(r['state_truth']=='unknown' for r in labels)
        else:
            complete+=1;assert audit['rows']==1000 and all(r['native_target_verified'] for r in labels)
            if audit['actuated_source']:assert audit['actual_source_onset'] is not None
    assert len(freeze['hashes'])==576 and complete==575 and len(failed)==1
    assert len({r['sumo_seed'] for r in manifest['units']})==576
    realization=rows(out/'truth/planned_signal_realization.csv')
    assert len(realization)==1080
    assert sum(r['unit_id'] in failed for r in realization)==3
    assert sum(r['condition']=='Plocal' for r in realization)==216
    assert len({(r['unit_id'],r['layer']) for r in realization})==1080
    evaluations=rows(out/'detector/parameter_evaluations.csv');checks={}
    for layer,s in selection.items():
        rr=[r for r in evaluations if r['layer']==layer and r['config_id']==s['config_id']]
        assert len(rr)==576 and len({r['unit_id'] for r in rr})==576
        metrics={'attempts':len(rr),'positive_n':sum(r['truth_positive']=='True' for r in rr),
            'negative_n':sum(r['truth_negative']=='True' for r in rr),'timely_n':sum(r['truth_positive']=='True' and r['timely']=='True' for r in rr),
            'false_positive_n':sum(r['false_positive']=='True' for r in rr),'unknown_n':sum(r['unknown']=='True' for r in rr),
            'truth_unknown_n':sum(r['truth_unknown']=='True' for r in rr)}
        for name,value in metrics.items():assert s['descriptive_metrics'][name]==value,(layer,name)
        assert all(r['unknown']=='True' and r['alarm']=='' for r in rr if r['unit_id'] in failed)
        checks[layer]=metrics
    plans=rows(out/'detector/exact_sample_size_power.csv')
    for row in plans:
        n=int(row['n']);critical=int(row['max_bad']);limit=float(row['limit']);good=float(row['good']);failure=float(row['failure']);target=float(row['target_power'])
        type_i=independent_cdf(critical,n,limit);power=independent_cdf(critical,n,good)
        assert type_i<=failure*(1+1e-7) and power>=target-1e-9
        assert independent_cdf(critical+1,n,limit)>failure*(1-1e-7)
        assert abs(power-float(row['power']))<1e-8
        assert n>=int(row['zero_bad_favorable_n'])
    val=load(out/'detector/independent_validation_manifest.json')
    assert val['status']=='NOT_EXECUTED' and val['new_validation_seeds_consumed']==0
    assert val['new_seed_namespace']!=manifest['seed_roots']['calibration']
    assert val['family_size']==len(rows(out/'detector/validation_family.csv'))
    assert m.sha(out/'detector/validation_family.csv')==val['family_manifest_sha256']
    for eta in load(out/'detector/bridge_feasibility.json'):
        assert eta['independent_V_positive_n']==0 and not eta['eta_frozen'] and not eta['budget_evaluable']
        assert eta['cdf_grid_claims']==225
        margin=eta['eta_scenario']/2
        assert eta['favorable_zero_early_mass_hoeffding_n']==math.floor(math.log(225/.02)/(2*margin**2))+1
    root=Path(__file__).resolve().parents[2]
    protected=chr(10).join(subprocess.check_output(['git','diff',*index,'--name-only','--','code/src','code/configs','AGENTS.md'],cwd=root,text=True).strip() for index in [[],['--cached']]).strip()
    assert not protected,'protected production or long-term rules changed'
    audit={'status':'PASS','scope':'raw/label hashes, all 576 attempts, selected metrics, independent math power, source setters, protected paths',
        'completed':complete,'failed':failed,'label_hashes_checked':label_hash_checked,'planned_design_layer_records':len(realization),'selected_metrics_recomputed':checks,
        'exact_plans_independently_recomputed':len(plans),'independent_V':val['status'],
        'verification_is_not_scientific_acceptance':True,'script_sha256':m.sha(Path(__file__))}
    m.dump(out/'audit/independent_recompute.json',audit);print(json.dumps(audit,ensure_ascii=False))

if __name__=='__main__':main()
