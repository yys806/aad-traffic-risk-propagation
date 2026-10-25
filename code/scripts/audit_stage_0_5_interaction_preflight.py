"""Offline preflight only: fixed two previously accessed calibration baselines.

Does not repair geometry, generate trajectories, choose another window or write
scientific gates. Geometry comparisons use only same-native-lane pairs at three
predeclared clocks; they are not a counterfactual P2 event recalculation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/src'))
from riskprop.stage_0_5_scene_reconstruction import REAL_SPAN_M, network_edge_lengths
from riskprop.stage_0_5_state_support import route_length_map
from riskprop.stage_0_5_d1_measurement import inside_region, local_d1_measurement
from audit_stage_0_5_work_package_1 import edge_and_event_audit

WINDOWS = ('us101__0750_0805', 'us101__0805_0820')
CLOCKS = (180., 210., 300.)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def gap_comparison(leader_pos, follower_pos, leader_length, scale):
    """Two explicitly different quantities; neither replaces a production field."""
    native = leader_pos - follower_pos - leader_length
    adapter = (leader_pos - follower_pos) * scale - leader_length
    return native, adapter, adapter - native


def geometry_samples(fcd, lengths, edge_lengths):
    records = []
    clock = None
    for event, element in ET.iterparse(fcd, events=('start', 'end')):
        if event == 'start' and element.tag == 'timestep':
            clock = float(element.get('time'))
        elif event == 'end' and element.tag == 'vehicle':
            if clock in CLOCKS:
                lane = element.get('lane'); edge = lane.rpartition('_')[0]
                if edge in REAL_SPAN_M:
                    records.append((clock, lane, edge, element.get('id'), float(element.get('pos'))))
            element.clear()
        elif event == 'end' and element.tag == 'timestep':
            element.clear()
    d = pd.DataFrame(records, columns=['time_s', 'native_lane', 'edge', 'id', 'pos'])
    rows = []
    for (_, _, edge), group in d.groupby(['time_s', 'native_lane', 'edge']):
        group = group.sort_values('pos').reset_index(drop=True)
        low, high = REAL_SPAN_M[edge]; scale = (high-low)/edge_lengths[edge]
        for i in range(len(group)-1):
            follower, leader = group.iloc[i], group.iloc[i+1]
            # Restrict to the same [150,350) local longitudinal support.
            y = low + follower.pos * scale
            if not 150 <= y < 350:
                continue
            native, adapter, error = gap_comparison(leader.pos, follower.pos, lengths[leader.id], scale)
            rows.append(dict(edge=edge, native_gap_m=native, adapter_gap_m=adapter, difference_m=error))
    a = pd.DataFrame(rows)
    return dict(clocks_s=list(CLOCKS), pairs=len(a),
                scope='same native lane/edge, local longitudinal region; not all leader pairs or P2',
                differences_by_edge=[dict(edge=edge, pairs=len(g), mean_m=float(g.difference_m.mean()),
                    min_m=float(g.difference_m.min()), max_m=float(g.difference_m.max()),
                    max_abs_m=float(g.difference_m.abs().max())) for edge, g in a.groupby('edge')])


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    inputs, results = {}, []
    for window in WINDOWS:
        base = ROOT/'code/outputs/formal/calibration/stage_0_5_state_support_v1/seeds'/f'B_het_{window}_vlim10.00_s20261201'
        paths = [base/'measured_state.parquet', base/'fcd.xml', base/'routes.rou.xml',
                 base/'run.sumocfg', base/'network/observed_geometry_supply_10p0_l5.net.xml']
        for path in paths:
            inputs[path.relative_to(ROOT).as_posix()] = dict(sha256=sha(path), bytes=path.stat().st_size)
        d = pd.read_parquet(paths[0]); net_lengths = network_edge_lengths(paths[-1])
        measured = local_d1_measurement(d, (120.,390.), strict=True)
        oracle = edge_and_event_audit(d, (120.,390.), real=False)
        if measured['onset_events'] != oracle['onset_N'] or abs(measured['local_evaluable_s']-oracle['D1_E_veh_s']) > 1e-7:
            raise AssertionError('independent_D1_mismatch')
        initial = d.loc[inside_region(d) & d.time_s.eq(120.) & d.vehicle_id.str.startswith('i')]
        results.append(dict(window=window, baseline_seed=20261201,
            initial_vehicles_local_at_120=len(initial), initialization_eligibility=initial.empty,
            d1=dict(onset_N=measured['onset_events'], E_veh_s=measured['local_evaluable_s'],
                    legacy_point_E_veh_s=measured['legacy_point_evaluable_s'], independent_oracle_match=True),
            coordinate_scales={e:(hi-lo)/net_lengths[e] for e,(lo,hi) in REAL_SPAN_M.items()},
            geometry=geometry_samples(paths[1],route_length_map(paths[2]),net_lengths)))
    sources = [Path(__file__), ROOT/'code/src/riskprop/stage_0_5_d1_measurement.py',
        ROOT/'code/src/riskprop/stage_0_5_state_support.py', ROOT/'code/src/riskprop/stage_0_5_scene_reconstruction.py',
        ROOT/'code/src/riskprop/stage_0_5_sumo.py', ROOT/'code/scripts/audit_stage_0_5_work_package_1.py']
    report = dict(status='Awaiting Researcher Decision', new_trajectory_attempts=0,
        plan_frozen=False, evaluation_window_s=[120,390], baselines=results,
        stop_reasons=['scaled_coordinate_gap_conflicts_with_physical_gap_definition',
                      '0750_baseline_fails_declared_initialization_eligibility'],
        inputs=inputs, sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
        git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        worktree=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(),
        python=sys.version, pandas=pd.__version__, numpy=np.__version__,
        command='python code/scripts/audit_stage_0_5_interaction_preflight.py --output '+str(output),
        scientific_claim_eligible=False, protocol_lock_allowed=False)
    target=output/'preflight.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'SHA256SUMS').write_text(sha(target)+'  preflight.json\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','new_trajectory_attempts','baselines']},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
