"""Authorized retrospective source-time correction. Never launches SUMO."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import csv
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import numpy as np
import p2_task8_support_experiment as s
import analyze_p2_task8_support as t8

ROOT=s.ROOT
HISTORY=s.HISTORY
TASK='AAD-P2-TASK7-SOURCE-TIMESTAMP-BACKFILL-20261102'
VERSION='AAD-P2T7-SOURCE-TIMESTAMP-BACKFILL-20261102-v1'
OUTPUT=ROOT/'code/outputs/calibration/p2_task7_timestamp_backfill_20261102_v1'
EVIDENCE=ROOT/'evidence/research/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_20261102'
REPORT='docs/research/P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md'
DEPENDENCIES=['code/scripts/p2_task8_support_experiment.py','code/scripts/analyze_p2_task8_support.py',
 'code/scripts/p2_task7_measurement.py','code/scripts/analyze_p2_task7_parameter_experiment.py',
 'code/scripts/run_p2_task7_parameter_experiment.py','code/scripts/finalize_p2_task7.py']
HISTORY_DOCS=[f'docs/research/P2/P2_TASK7_{name}.md' for name in ['FINAL_REPORT','EXPERIMENT_PROTOCOL','PARAMETER_RESULTS','RESEARCHER_RECOMMENDATIONS']]
TASK8_INPUTS=['audit/task7_witness_timestamp_reaudit.csv','audit/task7_timestamp_conflict.json','audit/task7_input_hashes.json',
 'manifest.json','provenance.json']

def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def interval(value):return json.loads(value) if value else None

def truth_bool(value):return None if value=='' else value=='True'

def ordering(parent,child,error=0.):
    """Strict interval separation, with no numerical relaxation."""
    if parent is None or child is None:return 'Unknown_missing_interval'
    if parent[1]+error<child[0]-error:return 'Pass'
    if child[1]+error<parent[0]-error:return 'Not_ordered_reverse'
    return 'Unknown_overlap'

def transition(old,new):
    if new.startswith('Unknown'):return 'unresolved_after_correction'
    if old=='Pass' and new=='Pass':return 'pass_to_pass'
    if old!='Pass' and new=='Pass':return 'not_pass_to_pass'
    if old=='Pass':return 'pass_to_not_pass'
    return 'not_pass_to_not_pass_known_reverse'

def source_record(raw,audit):
    """Use only actual actuator state; never consult a target or label."""
    if audit['status']!='COMPLETE':return {'status':'Unknown','reason':'preserved startup failure; no state observations','corrected_interval':None}
    actual=audit.get('actuated_source')
    if actual is None:return {'status':'Not Applicable','reason':'N0: no source intervention','corrected_interval':None}
    execution=audit.get('source_execution');commands=audit.get('controls',[])
    if execution is None or not any(c['vehicle']==actual and c['method']=='slowDown' and c['time_s']==execution for c in commands):
        return {'status':'Unknown','reason':'actual intervention execution not supported by command record','corrected_interval':None}
    keys=['t','v','a'];idx=0 if actual=='s0' else raw['v'].shape[1]-1
    if any(k not in raw for k in keys) or not np.isfinite(raw['t']).all() or not np.isfinite(raw['v'][:,idx]).all() or not np.isfinite(raw['a'][:,idx]).all():
        return {'status':'Unknown','reason':'missing or non-finite actuator-only observations','corrected_interval':None}
    pre=(raw['t']>=10)&(raw['t']<=execution+1e-9)
    if not pre.any() or not np.any(raw['t']>execution+1e-9):
        return {'status':'Unknown','reason':'missing pre/post actuator support','corrected_interval':None}
    corrected=s.physical_source_interval(raw,audit)
    before=np.flatnonzero(raw['t']<=execution+1e-9)[-1]
    record={'status':'Established' if corrected else 'Unknown','corrected_interval':corrected,
        'reason':'command-lower and pre-envelope deceleration-signature upper' if corrected else 'no qualifying source-only deceleration signature',
        'actuator_column':idx,'pre_acceleration_min':float(raw['a'][pre,idx].min()),
        'pre_acceleration_max':float(raw['a'][pre,idx].max()),'pre_reference_speed':float(raw['v'][before,idx]),
        'pre_samples':int(pre.sum()),'signature_tolerance':1e-6}
    if corrected:
        j=int(np.flatnonzero(raw['t']==corrected[1])[0])
        record.update({'signature_frame':j,'signature_time_s':float(raw['t'][j]),'signature_speed':float(raw['v'][j,idx]),
            'signature_acceleration':float(raw['a'][j,idx]),'native_readback_at_signature':float(raw['native'][j,idx]),
            'signature_previous_sample_s':float(raw['t'][j-1]) if j else None})
    return record

def prepare(out):
    if out.exists():raise FileExistsError('Never overwrite a prior backfill output')
    out.mkdir(parents=True);(out/'audit').mkdir();(out/'results').mkdir();(out/'snapshots').mkdir()
    # Freeze rules before examining outcomes. Old artifacts are inputs only.
    frozen={'task_id':TASK,'version':VERSION,'frozen_utc':s.utc(),'authorization':'Researcher Approved, all575 completed traces',
        'source_rule':'Reuse Task8 physical_source_interval unchanged: command execution lower, first source-only observed deceleration signature upper; pre realized acceleration envelope and speed decline, tolerance1e-6.',
        'source_inputs_only':['t','actual actuator v/a','actual execution command record'],
        'source_statuses':['Established','Unknown','Not Applicable (N0)'],
        'no_target_feedback':True,'truth_unchanged':True,'no_detector_calls':True,
        'main_W6':'U_parent < L_child exactly; missing/overlap remain Unknown, reverse intervals distinguished',
        'clock_each_s':[0.,.05,.2],'clock_formula':'U_parent+e < L_child-e; main e=0',
        'Observed_scope':'Exact original Task7 source_ok and fixed truth-positive and all frozen original terminal-path W6. Replace only first parent source interval; original target response segments unchanged.',
        'all_hop_scope':'all s0-specified/s0-actuated completed runs, all original leader followers; first a1b1 response per entity through50s. Separate horizon46s historical reaction sensitivity reproduced for original rep0/23 rows.',
        'qualification':'retain legacy Unknown for359 specified-source candidates and1 failure; never promote W8 or Qualified',
        'planned_units':576,'completed_expected_from_manifest':575,'new_SUMO_runs':0,'new_seeds':0,'new_V_runs':0,
        'historical_counts_comparison_only':[359,47,0],'Task8_119_is_comparison_not_selection_target':True,
        'git_sha':s.git('rev-parse','HEAD'),'dirty_status':s.git('status','--short'),
        'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),
        'impact_scope':'isolated offline scripts/tests/reports/index/evidence only; no production, config, truth, detector, formal definitions or Gates changed'}
    frozen['source_sha256']={rel:s.m.sha(ROOT/rel) for rel in DEPENDENCIES+[str(Path(__file__).relative_to(ROOT).as_posix())]}
    s.dump(out/'manifest.json',frozen)
    for rel in frozen['source_sha256']:shutil.copy2(ROOT/rel,out/'snapshots'/Path(rel).name)
    protected=[p for p in HISTORY.rglob('*') if p.is_file()]+[ROOT/p for p in HISTORY_DOCS+DEPENDENCIES]
    task8=ROOT/'code/outputs/calibration/p2_task8_20261102_v1'
    protected.extend(task8/p for p in TASK8_INPUTS)
    s.dump(out/'audit/input_hashes.json',{'files':{p.relative_to(ROOT).as_posix():{'sha256':s.m.sha(p),'bytes':p.stat().st_size} for p in sorted(set(protected))}})
    print(json.dumps({'prepared':str(out),'rules_frozen_before_backfill':True}))

def response_intervals(raw,stop):
    result={}
    for i in range(1,raw['v'].shape[1]-1):
        ev=s.a.fast_events(raw['t'],10-raw['v'][:,i],np.ones(len(raw['t']),bool),1.,1.,.05,stop=stop)
        result[i]=[ev[0]['onset_lower_s'],ev[0]['onset_upper_s']] if ev else None
    return result

def check_inputs(out):
    hh=s.load(out/'audit/input_hashes.json')['files']
    for rel,h in hh.items():assert s.m.sha(ROOT/rel)==h['sha256'],rel
    frozen=s.load(HISTORY/'audit/truth_freeze.json');manifest=s.load(HISTORY/'manifest.json')
    assert len(manifest['units'])==len(frozen['hashes'])==576
    assert s.m.sha(HISTORY/'manifest.json')==frozen['manifest_sha256']
    labels=0
    for u in manifest['units']:
        uid=u['unit_id']
        for kind,p in {'raw':HISTORY/'raw'/uid/'trajectory.npz','audit':HISTORY/'audit'/f'{uid}.json','truth':HISTORY/'truth'/f'{uid}.json'}.items():
            assert s.m.sha(p)==frozen['hashes'][uid][kind],(uid,kind)
        for label in s.load(HISTORY/'truth'/f'{uid}.json'):
            digest=label['label_hash'];label['label_hash']=None
            assert hashlib.sha256(json.dumps(label,sort_keys=True,allow_nan=False).encode()).hexdigest()==digest
            labels+=1
    assert labels==1728
    return {'status':'PASS','protected_files':len(hh),'planned_units':576,'original_labels_hash_checked':labels,'all_Task7_output_files_unchanged':True}

def calculate(out):
    if (out/'results/summary.json').exists():raise FileExistsError('No repeat completed backfill')
    started=time.time();integrity=check_inputs(out);units=s.load(HISTORY/'manifest.json')['units']
    for rel,h in s.load(out/'manifest.json')['source_sha256'].items():assert s.m.sha(ROOT/rel)==h
    legacy={r['unit_id']:r for r in rows(HISTORY/'audit/micro_witness_levels.csv')}
    diagnostic={r['unit_id']:r for r in rows(ROOT/'code/outputs/calibration/p2_task8_20261102_v1/audit/task7_witness_timestamp_reaudit.csv')}
    historical_reaction={(r['unit_id'],int(r['target_entity']),float(r['clock_error_each_s'])):r for r in rows(HISTORY/'detector/reaction_clock_evidence.csv')}
    source_rows=[];witness_rows=[];path_edges=[];all_edges=[];reaction_compare=[];mismatches=[];label_checks=0
    for unit in units:
        uid=unit['unit_id'];audit=s.load(HISTORY/'audit'/f'{uid}.json');labels=s.load(HISTORY/'truth'/f'{uid}.json')
        label=next(r for r in labels if r['measurement_layer']=='micro');old=legacy[uid]
        with np.load(HISTORY/'raw'/uid/'trajectory.npz') as f:raw={k:f[k] for k in f.files}
        corrected=source_record(raw,audit);old_interval=audit.get('actual_source_onset');new_interval=corrected['corrected_interval']
        row={'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'execution_status':audit['status'],
            'actual_execution_s':audit.get('source_execution'),'actuated_source':audit.get('actuated_source'),'specified_source':unit['specified_source'],
            'legacy_source_interval':old_interval,**corrected,
            'legacy_lower_minus_corrected_lower_s':old_interval[0]-new_interval[0] if old_interval and new_interval else None,
            'legacy_upper_minus_corrected_upper_s':old_interval[1]-new_interval[1] if old_interval and new_interval else None,
            'specified_source_event_status':corrected['status'] if unit['specified_source']==audit.get('actuated_source') else 'Not Applicable: no command on specified source; actual actuator recorded separately',
            **{kind+'_sha256':s.m.sha(p) for kind,p in {'raw':HISTORY/'raw'/uid/'trajectory.npz','audit':HISTORY/'audit'/f'{uid}.json','truth':HISTORY/'truth'/f'{uid}.json'}.items()}}
        if audit['status']!='COMPLETE':row['specified_source_event_status']='Unknown: preserved startup failure'
        source_rows.append(row)
        potential=None if audit['status']!='COMPLETE' else audit['actuated_source']=='s0' and unit['specified_source']=='s0'
        frozen_path=interval(old['path']);assert isinstance(frozen_path,list)
        new_path=[];sensitivity={}
        for error in [0.,.05,.2]:
            statuses=[]
            for j,edge in enumerate(frozen_path):
                parent=new_interval if j==0 else edge['parent_interval'];child=edge['response_interval']
                before=ordering(edge['parent_interval'],child,error);after=ordering(parent,child,error);statuses.append(after)
                path_edges.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'hop':j+1,
                    'leader':edge['leader'],'follower':edge['follower'],'clock_each_s':error,'legacy_parent_interval':edge['parent_interval'],
                    'corrected_parent_interval':parent,'response_interval_unchanged':child,'old_W6_status':before,'new_W6_status':after,
                    'old_strict_pass':before=='Pass','new_strict_pass':after=='Pass','transition':transition(before,after),
                    'same_entity_response_segment':True,'W8':'Unknown','qualified_count_contribution':0})
                if error==0:new_path.append({**edge,'parent_interval':parent,'W6':after=='Pass'})
            sensitivity[str(error)]=bool(potential and label['state_truth']=='positive' and statuses and all(x=='Pass' for x in statuses))
        observed=None if potential is None else bool(potential and label['state_truth']=='positive' and new_path and all(e['W6'] for e in new_path))
        old_replay=None if potential is None else bool(potential and label['state_truth']=='positive' and frozen_path and all(e['W6'] for e in frozen_path))
        assert truth_bool(old['Potential']) is potential and truth_bool(old['Observed']) is old_replay
        check=None
        if audit['status']=='COMPLETE':
            amended=copy.deepcopy(audit);amended['legacy_executor_source_interval']=old_interval;amended['actual_source_onset']=new_interval
            check=t8.witness(raw,amended,label)
            if check['Observed']!=observed or check['Potential']!=potential:mismatches.append({'unit_id':uid,'kind':'Task8 helper vs frozen legacy path'})
            if diagnostic[uid]['reaudit_Observed']!=str(observed):mismatches.append({'unit_id':uid,'kind':'Task8 saved diagnostic vs new calculation'})
            target_intervals=response_intervals(raw,50.)
            for e in frozen_path:assert target_intervals[int(e['follower'][1:])]==e['response_interval'],uid
            label_checks+=1
            if potential:
                for target,child in target_intervals.items():
                    old_parent=old_interval if target==1 else target_intervals[target-1]
                    new_parent=new_interval if target==1 else target_intervals[target-1]
                    for error in [0.,.05,.2]:
                        before=ordering(old_parent,child,error);after=ordering(new_parent,child,error)
                        all_edges.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'leader':f's{target-1}','follower':f's{target}',
                            'clock_each_s':error,'legacy_parent_interval':old_parent,'corrected_parent_interval':new_parent,'response_interval_unchanged':child,
                            'old_W6_status':before,'new_W6_status':after,'transition':transition(before,after),'path_member':target<=len(frozen_path),
                            'actual_leader_continuous':bool(np.all(raw['leader'][:,target]==target-1)),'W8':'Unknown'})
            if unit['rep'] in (0,23):
                short=response_intervals(raw,46.)
                for target,child in short.items():
                    parent=(old_interval if audit['actuated_source']=='s0' else None) if target==1 else short[target-1]
                    corrected_parent=(new_interval if audit['actuated_source']=='s0' else None) if target==1 else short[target-1]
                    for error in [0.,.05,.2]:
                        saved=historical_reaction[(uid,target,error)]
                        assert interval(saved['parent_interval'])==parent and interval(saved['child_interval'])==child
                        assert (saved['W6_strict_order']=='True')==(ordering(parent,child,error)=='Pass')
                        reaction_compare.append({'unit_id':uid,'target_entity':target,'clock_each_s':error,'scope':'original representative reaction audit, stop46s; not Observed horizon50',
                            'specified_source_path_applicable':potential,'old_parent_interval':parent,'corrected_parent_interval':corrected_parent,
                            'response_interval_unchanged':child,'old_W6_status':ordering(parent,child,error),'new_W6_status':ordering(corrected_parent,child,error),
                            'original_row_reproduced':True})
        witness_rows.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'Potential':potential,
            'legacy_Observed':old_replay,'corrected_Observed':observed,'legacy_Qualified':truth_bool(old['Qualified']),
            'Qualified':truth_bool(old['Qualified']),'qualified_count_contribution':0,'state_truth_unchanged':label['state_truth'],
            'terminal_entity_unchanged':label.get('terminal_entity'),'old_path':frozen_path,'corrected_path':new_path,'path_identity_relation_quality_verified':check is not None and (not frozen_path or all(all(e[k] for k in ['W1','W2','W3','W7']) for e in check['W1_W7_path'])),
            'Observed_clock_sensitivity':sensitivity,'Task8_helper_Observed':check['Observed'] if check else None,
            'W8':old['W8'],'W9_qualification':'Unknown: W8 not established' if potential or potential is None else 'Not Applicable: no specified-source connected path'})
    assert len(source_rows)==576 and label_checks==575
    for name,data in [('source_time_comparison',source_rows),('witness_comparison',witness_rows),('path_W6_comparison',path_edges),('all_hop_W6_comparison',all_edges),('historical_reaction_clock_reproduction',reaction_compare)]:
        s.a.csv_write(out/'results'/f'{name}.csv',data)
    def grouped(data):
        keys=['density','condition'];result=[]
        for key in sorted({tuple(r[k] for k in keys) for r in data}):
            rr=[r for r in data if tuple(r[k] for k in keys)==key]
            result.append(dict(zip(keys,key))|{'planned':len(rr),'Potential':sum(r['Potential'] is True for r in rr),
                'old_Observed':sum(r['legacy_Observed'] is True for r in rr),'corrected_Observed':sum(r['corrected_Observed'] is True for r in rr),
                'Qualified_count':0,'qualification_unknown':sum(r['Qualified'] is None for r in rr)})
        return result
    groups=grouped(witness_rows);s.a.csv_write(out/'results/group_counts.csv',groups)
    integrity_after=check_inputs(out);s.dump(out/'audit/integrity_verification.json',integrity_after)
    summary={'task_id':TASK,'version':VERSION,'status':'COMPLETE' if not mismatches else 'COMPLETE_WITH_SCOPE_DISCREPANCY',
        'planned':len(source_rows),'completed':575,'failed_units':[r['unit_id'] for r in source_rows if r['execution_status']!='COMPLETE'],
        'source_status_counts':dict(Counter(r['status'] for r in source_rows)),
        'intervals_changed':sum(r['legacy_source_interval']!=r['corrected_interval'] for r in source_rows if r['status']=='Established'),
        'upper_shift_s':dict(sorted(Counter(str(r['legacy_upper_minus_corrected_upper_s']) for r in source_rows if r['status']=='Established').items())),
        'Potential':sum(r['Potential'] is True for r in witness_rows),'old_Observed':sum(r['legacy_Observed'] is True for r in witness_rows),
        'corrected_Observed':sum(r['corrected_Observed'] is True for r in witness_rows),'Qualified':0,
        'qualification_unknown':sum(r['Qualified'] is None for r in witness_rows),
        'state_positive_unchanged':sum(r['state_truth_unchanged']=='positive' for r in witness_rows),
        'path_edges_main':sum(r['clock_each_s']==0 for r in path_edges),'all_hop_edges_main':sum(r['clock_each_s']==0 for r in all_edges),
        'path_W6_transitions':{str(e):dict(Counter(r['transition'] for r in path_edges if r['clock_each_s']==e)) for e in [0.,.05,.2]},
        'all_hop_W6_transitions':{str(e):dict(Counter(r['transition'] for r in all_edges if r['clock_each_s']==e)) for e in [0.,.05,.2]},
        'Observed_clock_sensitivity':{str(e):sum(r['Observed_clock_sensitivity'][str(e)] for r in witness_rows) for e in [0.,.05,.2]},
        'historical_reaction_rows_reproduced':len(reaction_compare),'Task8_diagnostic_Observed':sum(r['reaudit_Observed']=='True' for r in diagnostic.values()),
        'scope_discrepancies':mismatches,'original_labels_hash_checked':1728,'response_windows_reextracted_for_comparison_only':575,
        'no_truth_regeneration':True,'no_detector_evaluations':True,'new_SUMO_runs':0,'new_seeds':0,'new_V_runs':0,
        'input_integrity_before':integrity,'input_integrity_after':integrity_after,'elapsed_s':time.time()-started}
    s.dump(out/'results/summary.json',summary);print(json.dumps(summary,ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['prepare','calculate'],required=True);args=parser.parse_args()
    if args.phase=='prepare':prepare(OUTPUT)
    else:calculate(OUTPUT)

if __name__=='__main__':main()
