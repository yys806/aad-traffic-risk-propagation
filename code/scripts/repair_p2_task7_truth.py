"""Pre-detector Task7 truth horizon repair; preserve every original label."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import p2_task7_measurement as m

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args();out=args.output_dir.resolve()
    if (out/'detector/candidate_manifest.json').exists() or (out/'audit/truth_freeze.json').exists():raise RuntimeError('no truth repair after detector start/freeze')
    archive=out/'truth/v1_end_confirmation_truncation';archive.mkdir(exist_ok=False)
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'));changes=[];counts={'complete':0,'failed':0}
    for unit in manifest['units']:
        uid=unit['unit_id'];audit=json.loads((out/'audit'/f'{uid}.json').read_text(encoding='utf-8'));path=out/'truth'/f'{uid}.json'
        before=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        if before is not None:shutil.copy2(path,archive/path.name)
        raw=out/'raw'/uid/'trajectory.npz'
        if m.sha(raw)!=audit['raw_sha256']:raise RuntimeError('raw drift')
        if audit['status']=='COMPLETE':
            labels=m.truth(dict(np.load(raw)),audit);counts['complete']+=1
        elif audit['status']=='FAILED_STOP':
            counts['failed']+=1;labels=[]
            for layer in ['cohort','macro','micro']:
                r={'truth_version':m.TRUTH_VERSION,'unit_id':uid,'measurement_layer':layer,'state_truth':'unknown',
                    'source_attribution':'unknown','onset_allowed_set':None,'confirmation_s':None,'recovery_interval_s':None,
                    'a_star_mps':1.,'b_star_s':1.,'d_star_s':4.,'truth_error_s':None,'truth_error_mps':None,
                    'clock_id':'SUMO unavailable: startup failed','sampling_s':None,'label_source':'preserved execution failure',
                    'label_scope':'Unknown; no simulation observations','native_target_verified':False,'terminal_entity':None,
                    'peak_decline_mps':None,'coverage':None,'dependency_block':uid,'density':unit['density'],
                    'condition':unit['condition'],'actual_source_onset':None,'source_execution':None,
                    'unknown_reason':audit['error'],'label_hash':None}
                r['label_hash']=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest();labels.append(r)
        else:raise RuntimeError('unfinished unit '+uid)
        for i,label in enumerate(labels):
            prior=before[i] if before else None
            if prior is None or any(prior[k]!=label[k] for k in ['state_truth','onset_allowed_set','confirmation_s','recovery_interval_s']):
                changes.append({'unit_id':uid,'layer':label['measurement_layer'],
                    'old_state':prior['state_truth'] if prior else None,'new_state':label['state_truth'],
                    'old_onset':prior['onset_allowed_set'] if prior else None,'new_onset':label['onset_allowed_set'],
                    'old_recovery':prior['recovery_interval_s'] if prior else None,'new_recovery':label['recovery_interval_s']})
        m.dump(path,labels)
    m.dump(out/'audit/truth_horizon_repair.json',{'status':'PRE_DETECTOR_ENGINEERING_CORRECTION',
        'old_version':'AAD-P2T7-TRUTH-20261102-v1','new_version':m.TRUTH_VERSION,
        'reason':'Permit confirmation/recovery through 50s for index onsets by 46s, as originally required by H_cal+d* followup',
        'semantic_scope':'same a*/b*/region/cohort; no candidate detector consulted; no source/target/run changes',
        'original_labels_preserved':str(archive.relative_to(out)),'raw_reexecuted':False,'detector_evaluations_before_repair':0,
        'changes':changes,'counts':counts,'truth_code_sha256':m.sha(Path(m.__file__)),
        'repair_script_sha256':m.sha(Path(__file__))})
    print(json.dumps({'truth_repair':counts,'changed_records':len(changes),'detector_started':False}))

if __name__=='__main__':main()
