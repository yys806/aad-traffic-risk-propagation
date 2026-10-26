"""Post-stop read-only preservation check, not a new prelaunch attempt."""
import hashlib,json
from pathlib import Path
stage=Path('/home/shen/AAD/code/tmp/stage05_v4_20261026_r5')
root=Path('/mnt/d/shen/TJU/AAD')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
names=['smoke_proposal.json','smoke_envelope.json','runtime_manifest.json','smoke_capsule/policy.json','probe_results/record.json','staging_record.json']
names += ['smoke_inputs/'+n for n in ['network.net.xml','routes.rou.xml','run.sumocfg']]
staging=json.loads((stage/'staging_record.json').read_bytes())
files={n:sha(stage/n) for n in names}
record=dict(purpose='Post-stop preservation only; no capability or resource recheck and no launch',
 staging=str(stage),artifact_sha256=files,source_sha256={n:sha(stage/n) for n in staging['source_sha256']},
 original_envelope_approval=json.loads((stage/'smoke_envelope.json').read_bytes())['approval'],
 attempt_or_outputs={n:(stage/'smoke_capsule'/n).exists() for n in ['launch_attempt.json','archive','scratch','engineering_acceptance.json','coordinator_failure.json','broker.stdout','broker.stderr']},
 optional_sysctl_present=Path('/proc/sys/kernel/unprivileged_userns_clone').exists(),
 SUMO_version_processes=0,SUMO_simulation_processes=0,real_TraCI_connections=0)
assert all(record['source_sha256'][n]==h for n,h in staging['source_sha256'].items())
assert not any(record['attempt_or_outputs'].values())
assert files['smoke_proposal.json']=='a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550'
assert files['smoke_envelope.json']=='6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463'
assert record['original_envelope_approval']['engineering_authorized'] is False
with (root/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/preservation.json').open('x') as f:json.dump(record,f,indent=2)
print(json.dumps(dict(no_attempt_records=True,original_envelope_unchanged=True,optional_sysctl_present=record['optional_sysctl_present'])))
