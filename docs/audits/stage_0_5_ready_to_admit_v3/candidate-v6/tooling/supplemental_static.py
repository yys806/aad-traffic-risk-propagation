from pathlib import Path
import json,sys,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'code/scripts'))
from prepare_stage_0_5_b00_admission_v6 import V5,V6,AUDIT,load,bound,sha,write
from stage_0_5_input_fidelity import inventory,compare_initial_policy
v5manifest=load(root,V5+'/manifest.json')
for name,digest in v5manifest['files'].items():bound(root,V5+'/'+name,digest)
original='code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs/ID1_SUPPLY_0750/routes.rou.xml'
bound(root,original,'4b1ee23fa4745d6c6b928f4a0f27bd752a6e057c4f8a50cf0221e1480167756e')
p=load(root,V6+'/proposal.json');candidate=p['runs'][0]['input_files']['routes.rou.xml']
bound(root,candidate,p['runs'][0]['input_sha256'][candidate])
before=(root/original).read_bytes();after=(root/candidate).read_bytes()
_,_,initial,_,_=inventory(before)
targets=[k for k,v in initial.items() if float(v.get('departSpeed'))==10]
result=compare_initial_policy(before,after,target_ids=targets)
assert len(targets)==result['changed_initial_count']==38
_,_,new_initial,_,_=inventory(after)
assert initial['i0007_i0007'].attrib==new_initial['i0007_i0007'].attrib and initial['i0007_i0007'].get('departSpeed')=='15.23'
record=dict(status='Pass',scope='Static exact input bytes only; no original trajectories read or copied, no insertion/safety claim',
    original_input_path=original,original_input_sha256=sha(root/original),B00_input_path=candidate,B00_input_sha256=sha(root/candidate),
    comparison=result,unchanged_other_initial_vehicles=79,i0007_unchanged=True,candidate_v5_manifest_verified=True,
    target_ids=targets,SUMO_launches=0,real_TraCI_connections=0,new_B00_research_trajectories=0)
write(root/AUDIT/'supplemental_DS38_static_verification.json',record)
print(json.dumps(record))
