"""Read-only post-run audit of isolated B calibration; no additional simulation."""
import argparse,csv,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import run_p2_task3_calibration_only as d


def response_locations(rows, responses, region, cohort):
    """Join observed response confirmations to positions; never infer causality."""
    lookup={(r['vehicle_id'],round(float(r['time_s']),8)):r for r in rows}
    result=[]
    for r in responses:
        if r['confirmation_s'] in ('',None):
            continue
        observation=lookup[(r['vehicle_id'],round(float(r['confirmation_s']),8))]
        position=float(observation['lane_position_m'])
        result.append({**r,'confirmation_position_m':position,
                       'in_region':region[0]<=position<=region[1],
                       'in_fixed_cohort':r['vehicle_id'] in cohort,
                       'qualified_witness':False})
    return result


def scope_audit(root):
    folder=root/'validation__a5.0__d6.0__seed202711020'
    output=root/'scope_audit'
    output.mkdir(exist_ok=False)
    rows=list(csv.DictReader((folder/'trajectory.csv').open()))
    responses=list(csv.DictReader((folder/'individual_response_candidates.csv').open()))
    audit=json.loads((folder/'audit.json').read_text())
    joined=response_locations(rows,responses,audit['region_m'],audit['cohort'])
    d.write_csv(output/'response_locations.csv',joined)
    metadata={'status':'CALIBRATION_ONLY','domain':'controlled_B_sumo',
              'selection':'descriptive post-run scope illustration, no inferential sample selection',
              'example_run':folder.name,'region_m':audit['region_m'],'cohort':audit['cohort'],
              'source_position_at_plan_m':audit['source_position_at_plan_m'],
              'trajectory_sha256':d.sha(folder/'trajectory.csv'),
              'response_candidates_sha256':d.sha(folder/'individual_response_candidates.csv'),
              'source_audit_sha256':d.sha(folder/'audit.json'),
              'script_sha256':d.sha(Path(__file__)),
              'command_argv':__import__('sys').argv,
              'interpretation':'candidate responses inside geometric region coexist with no fixed-cohort alarm; not Qualified or real-world causal proof'}
    (output/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    (output/'script_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (root/'SHA256SUMS').write_text(''.join(f'{d.sha(f)}  {f.relative_to(root).as_posix()}\n' for f in sorted(root.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'),encoding='utf-8')
    print(json.dumps({'scope_rows':len(joined),'output':str(output),'qualified_witness':False}))


def main():
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,required=True);p.add_argument('--scope-only',action='store_true');a=p.parse_args();root=a.input_dir
    if a.scope_only:
        scope_audit(root)
        return
    target=root/'measurement_audit.json'
    if target.exists():raise FileExistsError(target)
    records=[]
    for folder in sorted(x for x in root.iterdir() if x.is_dir() and x.name.startswith(('calibration__','validation__'))):
        audit=json.loads((folder/'audit.json').read_text())
        rows=list(csv.DictReader((folder/'trajectory.csv').open()))
        t=np.array(sorted({float(r['time_s']) for r in rows}))
        lookup={(r['vehicle_id'],float(r['time_s'])):r for r in rows}
        x=np.array([[float(lookup[(f's{i}',time)]['speed_mps']) for time in t] for i in range(5,11)])
        stat,cov=d.signals(t,x,d.Detector())
        source=[r for r in rows if r['vehicle_id']=='s0']
        before=next(r for r in source if float(r['time_s'])==30)
        after=next((r for r in source if float(r['time_s'])>30 and float(r['speed_mps'])<float(before['speed_mps'])-1e-8),None)
        records.append({'run':folder.name,'command_amplitude':audit['amplitude_command_mps'],
                        'peak_mean_decline_mps':float(stat[t>=30].max()),'min_coverage':float(cov[t>=30].min()),
                        'source_execution_s':audit['execution_s'],
                        'first_observed_speed_below_precommand_sample_s':float(after['time_s']) if after else None,
                        'source_first_decrease_interval_s':[30,float(after['time_s'])] if audit['execution_s'] is not None and after else None,
                        'source_movement_rule':'below last precommand speed; descriptive, not Formal source threshold',
                        'trajectory_sha256':d.sha(folder/'trajectory.csv')})
        for xml in folder.glob('*.xml'):ET.parse(xml)
        ET.parse(folder/'run.sumocfg')
    summaries=list(csv.DictReader((root/'calibration_summary.csv').open()))
    out={'status':'CALIBRATION_ONLY','domain':'controlled_B_sumo','runs':records,
         'total_alarm_counts_across_all_evaluations':sum(int(r['alarm_count']) for r in summaries),
         'per_run_candidate_counts_are_not_independent_repetitions':True,
         'min_peak_mean_decline_mps':min(r['peak_mean_decline_mps'] for r in records),
         'max_peak_mean_decline_mps':max(r['peak_mean_decline_mps'] for r in records),
         'xsd_validation_warning':'SUMO_HOME absent during execution; automatic XML schema validation disabled; all run XML parsed post-run for wellformedness, not schema validation',
         'audit_script_sha256':d.sha(Path(__file__))}
    target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    (root/'postprocess_provenance.json').write_text(json.dumps({'script_sha256':d.sha(Path(__file__)),'command_argv':__import__('sys').argv},indent=2)+'\n',encoding='utf-8')
    (root/'SHA256SUMS').write_text(''.join(f'{d.sha(f)}  {f.relative_to(root).as_posix()}\n' for f in sorted(root.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='runs'}))


if __name__=='__main__':main()
