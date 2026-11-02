"""Independent scalar replay of the authorized offline timestamp backfill."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import backfill_p2_task7_source_timestamps as b

def independent_source(raw,audit):
    if audit['status']!='COMPLETE' or audit.get('actuated_source') is None:return None
    j=0 if audit['actuated_source']=='s0' else raw['v'].shape[1]-1
    execution=audit['source_execution'];times=raw['t']
    pre=[i for i,t in enumerate(times) if 10<=t<=execution+1e-9]
    floor=min(float(raw['a'][i,j]) for i in pre)
    reference=float(raw['v'][max(i for i,t in enumerate(times) if t<=execution+1e-9),j])
    for i,t in enumerate(times):
        if t>execution+1e-9 and float(raw['a'][i,j])<floor-1e-6 and float(raw['v'][i,j])<reference-1e-6:
            return [float(execution),float(t)]
    return None

def independent_response(t,v,stop=50.):
    first=None;last=None
    for i,now in enumerate(t):
        if now<30-1e-9 or now>stop+1e-9:continue
        good=np.isfinite(v[i]) and 10-float(v[i])>=1-1e-10
        if not good:first=last=None;continue
        if last is None or now-t[last]>.05+1e-9:first=i
        last=i
        if now-t[first]>=1-1e-9:return [float(t[first-1]),float(t[first])]
    return None

def independent_status(parent,child,error):
    if not parent or not child:return 'Unknown_missing_interval'
    # Endpoint subtraction is intentionally not used, to retain exact strictness.
    if float(parent[1])+error<float(child[0])-error:return 'Pass'
    if float(child[1])+error<float(parent[0])-error:return 'Not_ordered_reverse'
    return 'Unknown_overlap'

def verify():
    out=b.OUTPUT;summary=b.s.load(out/'results/summary.json');sources={r['unit_id']:r for r in b.rows(out/'results/source_time_comparison.csv')}
    witnesses={r['unit_id']:r for r in b.rows(out/'results/witness_comparison.csv')}
    original={r['unit_id']:r for r in b.rows(b.HISTORY/'audit/micro_witness_levels.csv')}
    t8={r['unit_id']:r for r in b.rows(b.ROOT/'code/outputs/calibration/p2_task8_20261102_v1/audit/task7_witness_timestamp_reaudit.csv')}
    assert len(sources)==len(witnesses)==576
    manifest=b.s.load(b.HISTORY/'manifest.json');frozen=b.s.load(b.HISTORY/'audit/truth_freeze.json');labels=0;counts=Counter();responses={};short_responses={};audits={}
    for unit in manifest['units']:
        uid=unit['unit_id'];audit=b.s.load(b.HISTORY/'audit'/f'{uid}.json');audits[uid]=audit;r=sources[uid];w=witnesses[uid]
        for kind,path in {'raw':b.HISTORY/'raw'/uid/'trajectory.npz','audit':b.HISTORY/'audit'/f'{uid}.json','truth':b.HISTORY/'truth'/f'{uid}.json'}.items():
            assert b.s.m.sha(path)==r[kind+'_sha256']==frozen['hashes'][uid][kind]
        all_labels=b.s.load(b.HISTORY/'truth'/f'{uid}.json')
        for label in all_labels:
            digest=label['label_hash'];label['label_hash']=None
            assert hashlib.sha256(json.dumps(label,sort_keys=True,allow_nan=False).encode()).hexdigest()==digest;labels+=1
        label=next(r for r in all_labels if r['measurement_layer']=='micro')
        with np.load(b.HISTORY/'raw'/uid/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
        new=independent_source(raw,audit);assert new==b.interval(r['corrected_interval'])
        counts[audit['status']]+=1
        if audit['status']=='COMPLETE':
            assert len(raw['t'])==1000 and np.allclose(np.diff(raw['t']),.05,rtol=0,atol=1e-10)
            assert audit['native_target_setters']==audit['collisions']==audit['teleports']==0
            assert np.max(np.abs(raw['v'][:,1:-1]-raw['native'][:,1:-1]))<1e-8
            assert np.all(raw['leader'][:,1:-1]==np.arange(unit['count']-1)[None,:])
            assert np.all(raw['gap'][:,1:-1]>0) and np.isfinite(raw['gap'][:,1:-1]).all()
            assert np.isfinite(raw['v'][:,1:-1]).all() and np.isfinite(raw['x'][:,1:-1]).all()
            if audit['actuated_source'] is None:assert r['status']=='Not Applicable'
            elif new is None:assert r['status']=='Unknown'
            else:
                assert r['status']=='Established'
                assert any(c['vehicle']==audit['actuated_source'] and c['time_s']==new[0] and c['method']=='slowDown' for c in audit['controls'])
            assert new==b.interval(t8[uid]['signature_source_interval'])
            responses[uid]={i:independent_response(raw['t'],raw['v'][:,i]) for i in range(1,unit['count'])}
            if unit['rep'] in (0,23):short_responses[uid]={i:independent_response(raw['t'],raw['v'][:,i],46.) for i in range(1,unit['count'])}
        else:
            assert not len(raw['t']) and r['status']=='Unknown'
            assert all(x['state_truth']=='unknown' for x in all_labels)
            assert w['Potential']==w['corrected_Observed']==w['Qualified']==''
        old_path=json.loads(original[uid]['path']);new_path=json.loads(w['corrected_path'])
        assert json.loads(w['old_path'])==old_path and len(old_path)==len(new_path)
        pass_all=True
        for hop,(old,newedge) in enumerate(zip(old_path,new_path)):
            child=responses[uid][int(old['follower'][1:])]
            assert child==old['response_interval']==newedge['response_interval']
            parent=new if hop==0 else old['parent_interval']
            assert parent==newedge['parent_interval']
            passed=independent_status(parent,child,0.)=='Pass';assert passed==newedge['W6']
            pass_all &= passed
            if hop:assert old['parent_interval']==old_path[hop-1]['response_interval']
        potential=None if audit['status']!='COMPLETE' else (audit['actuated_source']=='s0' and unit['specified_source']=='s0')
        observed=None if potential is None else bool(potential and label['state_truth']=='positive' and old_path and pass_all)
        assert b.truth_bool(w['Potential']) is potential and b.truth_bool(w['corrected_Observed']) is observed
        assert w['Qualified']==original[uid]['Qualified'] and w['W8']==original[uid]['W8']
        if audit['status']=='COMPLETE':assert str(observed)==t8[uid]['reaudit_Observed']
        counts['Potential']+=potential is True;counts['Observed']+=observed is True
    assert counts['COMPLETE']==575 and counts['FAILED_STOP']==1 and labels==1728
    assert summary['Potential']==counts['Potential'] and summary['corrected_Observed']==counts['Observed']
    edge_n=0
    for row in b.rows(out/'results/all_hop_W6_comparison.csv'):
        uid=row['unit_id'];target=int(row['follower'][1:]);e=float(row['clock_each_s']);child=responses[uid][target]
        assert child==b.interval(row['response_interval_unchanged'])
        parent=b.interval(sources[uid]['corrected_interval']) if target==1 else responses[uid][target-1]
        old_parent=b.interval(sources[uid]['legacy_source_interval']) if target==1 else responses[uid][target-1]
        assert parent==b.interval(row['corrected_parent_interval']) and old_parent==b.interval(row['legacy_parent_interval'])
        assert independent_status(parent,child,e)==row['new_W6_status']
        assert independent_status(old_parent,child,e)==row['old_W6_status'];edge_n+=1
    assert edge_n==summary['all_hop_edges_main']*3
    transitions={str(e):Counter() for e in [0.,.05,.2]}
    for row in b.rows(out/'results/path_W6_comparison.csv'):
        e=float(row['clock_each_s']);before=independent_status(b.interval(row['legacy_parent_interval']),b.interval(row['response_interval_unchanged']),e)
        after=independent_status(b.interval(row['corrected_parent_interval']),b.interval(row['response_interval_unchanged']),e)
        assert before==row['old_W6_status'] and after==row['new_W6_status']
        transitions[str(e)][row['transition']]+=1
    assert {k:dict(v) for k,v in transitions.items()}==summary['path_W6_transitions']
    historical=0
    for row in b.rows(out/'results/historical_reaction_clock_reproduction.csv'):
        uid=row['unit_id'];i=int(row['target_entity']);error=float(row['clock_each_s']);child=short_responses[uid][i]
        parent=(b.interval(sources[uid]['corrected_interval']) if audits[uid]['actuated_source']=='s0' else None) if i==1 else short_responses[uid][i-1]
        assert child==b.interval(row['response_interval_unchanged']) and parent==b.interval(row['corrected_parent_interval'])
        assert independent_status(parent,child,error)==row['new_W6_status'];historical+=1
    assert historical==summary['historical_reaction_rows_reproduced']
    integrity=b.check_inputs(out)
    changes=subprocess.check_output(['git','diff','HEAD','--name-only','--','code/src','code/configs','AGENTS.md',*b.HISTORY_DOCS,*b.DEPENDENCIES],cwd=b.ROOT,text=True).strip();assert not changes,changes
    result={'status':'PASS','completed':counts['COMPLETE'],'failed':counts['FAILED_STOP'],'labels_hash_checked':labels,
        'independent_Potential':counts['Potential'],'independent_Observed':counts['Observed'],'Qualified_count':0,
        'independent_source_method':'scalar source-only scan, separate from Task8 vector implementation',
        'independent_response_method':'scalar first sustained1s span; no target detector or truth regeneration',
        'all_hop_clock_rows_independently_checked':edge_n,'historical_clock_rows_independently_checked':historical,
        'legacy_target_segments_unchanged':True,
        'Task8_saved_diagnostic_per_unit_matches':True,'integrity':integrity,'protected_code_and_reports_unchanged':True,
        'new_SUMO_runs':0,'new_seeds':0,'script_sha256':b.s.m.sha(Path(__file__))}
    b.s.dump(out/'audit/independent_verification.json',result);print(json.dumps(result))

if __name__=='__main__':verify()
