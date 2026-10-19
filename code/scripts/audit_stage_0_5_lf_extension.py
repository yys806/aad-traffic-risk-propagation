"""Additional offline prefix/cost audit; separate source fingerprint, no SUMO."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch',type=Path);p.add_argument('--inside',action='store_true');a=p.parse_args();b=a.batch.resolve()
    if not a.inside:
        copy=b/'lf_extension_audit_entry.py';shutil.copyfile(Path(__file__).resolve(),copy)
        write(b/'lf_extension_audit_source.json',dict(path='code/scripts/audit_stage_0_5_lf_extension.py',sha256=sha(copy)))
        raise SystemExit(subprocess.call([sys.executable,'-S',str(copy),str(b),'--inside'],timeout=120))
    sys.path.insert(0,str(b/'runtime/code/src'))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(b)
    try:
        from riskprop.stage_0_5_b12_runtime import environment
        environment(b)
        import pandas as pd
        out=b/'summary';pair=read(out/'paired_equivalence.json');rm=read(out/'run_manifest.json')
        first=pd.read_parquet(b/'runs/lf1_LF2/internal_states.parquet').sort_values(['time_s','vehicle_id']).reset_index(drop=True)
        extended=pd.read_parquet(b/'runs/lf1_LF3/internal_states.parquet',filters=[('time_s','<=',120.)]).sort_values(['time_s','vehicle_id']).reset_index(drop=True)
        columns=[c for c in first if c not in ['run_id','incarnation_id']]
        bad=['shape'] if len(first)!=len(extended) else [c for c in columns if not (first[c].eq(extended[c])|(first[c].isna()&extended[c].isna())).all()]
        write(out/'prefix_consistency_audit.json',dict(passed=not bad,rows=len(first),prefix_end_s=120.,columns_compared=columns,mismatches=bad,
            roles='LF1/LF2 same-seed transport pair; LF3 extends same-seed acquisition. Not independent traffic replicates; do not pool events/exposure',new_SUMO_runs=0))
        if bad:raise ValueError('extended_prefix_observation_mismatch')
        s=next(s for s in rm['summaries'] if s['run_id']=='lf1_LF3');cost=s['runtime']['total_worker_wall_s']/s['runtime']['internal_state_rows']
        write(out/'full600_forecast_scenarios.json',dict(full600_run_performed=False,observed_reference_duration_s=300.,observed_worker_wall_s=s['runtime']['total_worker_wall_s'],
            scenarios=dict(uncongested_44s_residence_all823_wall_s=cost*823*44*20,
                same_observed_mean_population_and_cost_wall_s=s['runtime']['total_worker_wall_s']*2,
                scheduled_no_exit_upper_vehicle_time_scenario=pair['conservative_forecast_600_wall_s']),
            uncertainty='Engineering scenarios, not confidence bounds or verified full600 cost; future supply/pending/occupancy change matters; no stationary extrapolation assumed',no_resource_limit_increase=True))
        provenance=read(out/'provenance.json');provenance['additional_analysis_sources']=[read(b/'lf_extension_audit_source.json')];write(out/'provenance.json',provenance)
        print('LF_PREFIX_AND_COST_AUDIT_OK',flush=True)
    finally:write(b/'lf_extension_access_audit.json',guard)
    if guard['denied']:raise PermissionError('extension_unexpected_access')
