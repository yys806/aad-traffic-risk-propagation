"""Authorized zero-trajectory C6 repair audit and P2-independent C7 evidence.

Only the two explicit previously accessed baseline directories are read. Outputs
are new immutable versions. C7 uses raw FCD identity/position/speed only, before
loading historical measurements or computing repaired TTC/P2.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import platform
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/src'))
from riskprop import stage_0_5_state_support as ss
from riskprop.stage_0_5_scene_reconstruction import parse_fcd, network_edge_lengths
from riskprop.stage_0_5_d1_measurement import local_d1_measurement, inside_region, offset100_cloud
from audit_stage_0_5_work_package_1 import sha

WINDOWS=('us101__0750_0805','us101__0805_0820')
POLICY={'status':'Proposed / Awaiting Researcher Decision','fixed_end_s':390,
    'A':'retain [120,390); explicitly describe initial vehicles, no steady-state claim',
    'B':'first shared 30s boundary >=120 and <=360 with zero locally observed initial vehicles in the preceding 30s in BOTH baseline FCDs; no interpolation; not automatically adopted',
    'selection_inputs':['FCD time','vehicle identity','mapped lane/position'],
    'state_descriptors_only':['density','speed','initial vehicle counts'],
    'excluded_selection_inputs':['TTC','P2','risk rate'],
    'old_candidate_P2_already_seen':True,'new_trajectory_budget':0}


def write(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def initialization(fcd):
    # No TTC/P2 or measured-state input enters this function.
    d=fcd.loc[inside_region(fcd)].copy()
    d['initial']=d.vehicle_id.str.startswith('i')
    rows=[]
    for start in range(0,420,30):
        g=d.loc[d.time_s.ge(start)&d.time_s.lt(start+30)]
        rows.append(dict(start_s=start,end_s=start+30,states=len(g),
            initial_states=int(g.initial.sum()),initial_vehicles=int(g.loc[g.initial,'vehicle_id'].nunique()),
            density_veh_km_lane=len(g)*.1/30,
            speed_mean_mps=float(g.speed_mps.mean()) if len(g) else None))
    initial=d.loc[d.initial]
    return dict(initial_at_120=int((initial.time_s.eq(120)).sum()),
        last_observed_local_initial_s=float(initial.time_s.max()) if len(initial) else None,
        state_blocks=rows,
        candidate_B_starts=[s for s in range(120,361,30) if not initial.time_s.between(s-30,s,inclusive='left').any()])


def event_members(frame, events):
    pieces=[]
    for event in events:
        g=frame.loc[frame.vehicle_id.eq(event['vehicle_id']) & frame.leader_id.eq(event['leader_id']) & frame.time_s.between(event['onset_s'],event['end_s'])].copy()
        g=g[['vehicle_id','leader_id','time_s','net_gap_m','ttc_s','ttc_valid']]
        g['event_id']=event['event_id'];g['member_sha256']=event['member_sha256']
        pieces.append(g)
    return pd.concat(pieces,ignore_index=True) if pieces else pd.DataFrame(columns=['vehicle_id','leader_id','time_s','net_gap_m','ttc_s','ttc_valid','event_id','member_sha256'])


def summary(r):
    return {k:r[k] for k in ['onset_events','local_evaluable_s','local_links','rate_per_evaluable_vehicle_hour','right_censored_unconfirmed','left_continuing_risk_segments','confirmation_after_window']}


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    write(out/'initialization_policy.json',POLICY)
    inputs={}; frames={}; bases={}; init={}
    for w in WINDOWS:
        b=ROOT/'code/outputs/formal/calibration/stage_0_5_state_support_v1/seeds'/f'B_het_{w}_vlim10.00_s20261201';bases[w]=b
        for relative in ['fcd.xml','routes.rou.xml','run.sumocfg','measured_state.parquet','network/observed_geometry_supply_10p0_l5.net.xml']:
            p=b/relative;inputs[p.relative_to(ROOT).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
        fcd=parse_fcd(b/'fcd.xml',network_edge_lengths(b/'network/observed_geometry_supply_10p0_l5.net.xml'))
        frames[w]=fcd;init[w]=initialization(fcd)
    common=sorted(set(init[WINDOWS[0]]['candidate_B_starts'])&set(init[WINDOWS[1]]['candidate_B_starts']))
    write(out/'initialization_evidence.json',{'policy_sha256':sha(out/'initialization_policy.json'),'windows':init,'common_B_start_s':common[0] if common else None,'selected_for_execution':False,'P2_not_selection_input':True})
    reports=[]
    for w in WINDOWS:
        print('C6 offline '+w,flush=True)
        b=bases[w];dest=out/w;dest.mkdir()
        old=pd.read_parquet(b/'measured_state.parquet')
        new=ss.measure_state_frame(ss.fcd_to_state_frame(frames[w],ss.route_length_map(b/'routes.rou.xml'),run_id=str(old.run_id.iloc[0]),scenario_id=str(old.scenario_id.iloc[0]),seed=20261201))
        new.to_parquet(dest/'repaired_measured_state.parquet',index=False)
        before=local_d1_measurement(old,(120,390),strict=True);after=local_d1_measurement(new,(120,390),strict=True)
        for label,d,r in [('before',old,before),('after',new,after)]:
            write(dest/(label+'_events.json'),r)
            event_members(d,r['events']).to_parquet(dest/(label+'_event_members.parquet'),index=False)
        cols=['vehicle_id','time_s','leader_id','net_gap_m','ttc_s','ttc_valid','measurement_status','reliable_following_eligible']
        compared=old[cols].merge(new[cols],on=['vehicle_id','time_s'],how='outer',suffixes=('_old','_new'),validate='one_to_one',indicator=True)
        if not compared._merge.eq('both').all():raise AssertionError('FCD_measurement_identity_clock_mismatch')
        compared.to_parquet(dest/'row_ttc_comparison.parquet',index=False)
        both=compared.ttc_valid_old & compared.ttc_valid_new
        delta=compared.loc[both,'ttc_s_new']-compared.loc[both,'ttc_s_old']
        oldset={e['member_sha256'] for e in before['events']};newset={e['member_sha256'] for e in after['events']}
        # Independent scalar incoming-edge oracle on repaired physical fields.
        checked=new.sort_values(['vehicle_id','time_s']);p=checked.shift()
        edges=checked.vehicle_id.eq(p.vehicle_id)&checked.leader_id.notna()&checked.leader_id.eq(p.leader_id)&checked.native_lane_id.eq(p.native_lane_id)&checked.time_s.sub(p.time_s).sub(.1).abs().le(1e-9)
        eligible=checked.reliable_following_eligible&checked.measurement_status.isin(['valid','not_applicable'])
        edges &= eligible & eligible.shift(fill_value=False)&inside_region(checked)&inside_region(checked).shift(fill_value=False)&p.time_s.ge(120)&checked.time_s.le(390)
        if int(edges.sum())!=after['local_links']:raise AssertionError('independent_edge_mismatch')
        offset100_cloud(new,(120,390)).to_csv(dest/'offset100_state.csv',index=False)
        reports.append(dict(window=w,scope='two historical matched baselines only; other historical tables not upgraded',before=summary(before),after=summary(after),
            full_context_event_members=dict(identical=len(oldset&newset),old_only=len(oldset-newset),new_only=len(newset-oldset)),
            all_context_TTC=dict(both_valid=int(both.sum()),changed=int(delta.abs().gt(1e-9).sum()),mean_delta_s=float(delta.mean()) if len(delta) else None,max_abs_delta_s=float(delta.abs().max()) if len(delta) else None,
                valid_to_unavailable=int((compared.ttc_valid_old&~compared.ttc_valid_new).sum()),unavailable_to_valid=int((~compared.ttc_valid_old&compared.ttc_valid_new).sum())),
            physical_support=new.physical_support_status.value_counts().to_dict(),independent_edge_match=True,
            scientific_claim_eligible=False))
    write(out/'comparison_summary.json',{'status':'Offline engineering evidence; initialization policy awaiting decision','new_trajectory_attempts':0,'comparisons':reports,'Gate_changed':False})
    sources=[Path(__file__),ROOT/'code/src/riskprop/stage_0_5_state_support.py',ROOT/'code/src/riskprop/stage_0_5_scene_reconstruction.py',ROOT/'code/src/riskprop/stage_0_5_d1_measurement.py',ROOT/'code/src/riskprop/stage_0_5_sumo.py']
    write(out/'provenance.json',dict(inputs=inputs,source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sources},git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),worktree=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(),python=sys.version,platform=platform.platform(),pandas=pd.__version__,numpy=np.__version__,command='python code/scripts/review_stage_0_5_c6_c7_offline.py --output '+str(out),new_trajectory_attempts=0))
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file()),encoding='utf-8')
    print(json.dumps(reports,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
