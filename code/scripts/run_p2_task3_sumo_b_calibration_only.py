"""Isolated CALIBRATION_ONLY controlled B SUMO measurement domain.

Never modifies formal code/configs, never reads holdout, no communication.
Command-conditioned alarms are not physical-arrival true-positive labels.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
import numpy as np
import run_p2_task3_calibration_only as detector


def write_json(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')


def run_one(traci, tc, binary, network, out, seed, amplitude, duration):
    out.mkdir(exist_ok=False)
    route=out/'traffic.rou.xml'
    vehicles='\n'.join(f'<vehicle id="s{i}" type="cal" route="r" depart="0" departPos="{1800-30*i}" departSpeed="15"/>' for i in range(16))
    route.write_text('<routes><vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" length="5" minGap="2.5" tau="1" sigma="0.3" maxSpeed="15" speedFactor="1" speedDev="0"/><route id="r" edges="cal"/>'+vehicles+'</routes>')
    config=out/'run.sumocfg'
    config.write_text(f'<configuration><input><net-file value="{network.as_posix()}"/><route-files value="{route.resolve().as_posix()}"/></input><time><step-length value="0.1"/><end value="39.1"/></time><random_number><seed value="{seed}"/></random_number></configuration>')
    command=[str(binary),'-c',str(config.resolve()),'--no-step-log','true','--duration-log.disable','true','--collision.action','warn','--log',str((out/'sumo.log').resolve()),'--error-log',str((out/'error.log').resolve())]
    label=out.name
    traci.start(command,label=label,verbose=False)
    conn=traci.getConnection(label)
    rows=[]; controls=[]; subscribed=set(); collision=teleport=0
    vars=[tc.VAR_SPEED,tc.VAR_ACCELERATION,tc.VAR_LANEPOSITION,tc.VAR_LANE_ID,tc.VAR_SPEED_WITHOUT_TRACI,tc.VAR_LEADER]
    source_at_plan=None
    try:
        for step in range(1,391):
            conn.simulationStep()
            now=conn.simulation.getTime()
            for vid in conn.vehicle.getIDList():
                if vid not in subscribed:
                    conn.vehicle.subscribe(vid,vars,parameters={tc.VAR_LEADER:('d',200.)})
                    subscribed.add(vid)
            data=conn.vehicle.getAllSubscriptionResults()
            if len(data)!=16:raise RuntimeError(f'incomplete panel at {now}: {len(data)}')
            collision+=conn.simulation.getCollidingVehiclesNumber()
            teleport+=conn.simulation.getStartingTeleportNumber()
            for vid,d in data.items():
                leader=d[tc.VAR_LEADER]
                lid,ldist=leader if leader else ('',None)
                row={'time_s':now,'vehicle_id':vid,'speed_mps':d[tc.VAR_SPEED],
                     'acceleration_mps2':d[tc.VAR_ACCELERATION], 'lane_position_m':d[tc.VAR_LANEPOSITION],
                     'lane_id':d[tc.VAR_LANE_ID],'leader_id':lid,'leader_distance_excluding_minGap_m':ldist,
                     'net_gap_m':ldist+2.5 if lid else None,
                     'speed_without_traci_mps':d[tc.VAR_SPEED_WITHOUT_TRACI]}
                if lid:
                    expected=f's{int(vid[1:])-1}'
                    if lid!=expected:raise RuntimeError('unexpected leader')
                    direct=data[lid][tc.VAR_LANEPOSITION]-d[tc.VAR_LANEPOSITION]-5
                    if abs(direct-(ldist+2.5))>1e-6:raise RuntimeError('net gap convention mismatch')
                if vid!='s0' and abs(row['speed_mps']-row['speed_without_traci_mps'])>1e-8:
                    raise RuntimeError('native follower diagnostic differs')
                if vid in [f's{i}' for i in range(5,11)] and now>=20 and not 1300<=row['lane_position_m']<=2240:
                    raise RuntimeError('fixed region support failure')
                rows.append(row)
            if step==300:
                source_at_plan=data['s0'][tc.VAR_LANEPOSITION]
                if source_at_plan<=2240:raise RuntimeError('source inside target region at planned onset')
            if amplitude:
                if step==300:
                    conn.vehicle.slowDown('s0',15-amplitude,1.)
                    controls.append({'planned_s':30,'executed_s':now,'vehicle_id':'s0','method':'slowDown','speed':15-amplitude,'duration':1.})
                elif step==310:
                    conn.vehicle.setSpeed('s0',15-amplitude)
                    controls.append({'planned_s':31,'executed_s':now,'vehicle_id':'s0','method':'setSpeed','speed':15-amplitude})
                elif step==int(round((30+duration)*10)):
                    conn.vehicle.slowDown('s0',15,1.)
                    controls.append({'planned_s':30+duration,'executed_s':now,'vehicle_id':'s0','method':'slowDown','speed':15,'duration':1.})
                elif step==int(round((31+duration)*10)):
                    conn.vehicle.setSpeed('s0',-1)
                    controls.append({'planned_s':31+duration,'executed_s':now,'vehicle_id':'s0','method':'setSpeed','speed':-1})
            if collision or teleport:raise RuntimeError('collision or teleport')
    finally:
        conn.close()
        if rows:detector.write_csv(out/'trajectory.csv',rows)
        write_json(out/'control_log.json',controls)
    write_json(out/'audit.json',{'status':'CALIBRATION_ONLY','domain':'controlled_B_sumo',
               'seed':seed,'amplitude_command_mps':amplitude,'duration_command_s':duration,
               'vehicles':16,'cohort':[f's{i}' for i in range(5,11)],'region_m':[1300,2240],
               'source_position_at_plan_m':source_at_plan,'command':command,'collisions':collision,
               'teleports':teleport,'native_follower_setters':0,'trajectory_rows':len(rows),
               'clock':'SUMO post-step simulation time; commands after step t affect later step',
               'planned_onset_s':30 if amplitude else None,'execution_s':controls[0]['executed_s'] if controls else None,
               'first_post_command_observation_s':30.1 if controls else None,
               'actuation_onset_interval_s':[30,30.1] if controls else None,
               'onset_interval_semantics':'actuation observation bracket, not exact physical threshold crossing',
               'formal_A_eligible':False,'qualified_witness':False})
    return rows


def evaluate(rows, ds):
    t=np.array(sorted({r['time_s'] for r in rows}))
    lookup={(r['vehicle_id'],round(r['time_s'],8)):r for r in rows}
    x=np.array([[lookup[(f's{i}',round(time,8))]['speed_mps'] for time in t] for i in range(5,11)])
    results=[]
    for di,d in enumerate(ds):
        stat,cov=detector.signals(t,x,d)
        valid=np.isfinite(stat)&(cov>=d.coverage_gate-1e-12)
        result=detector.first_confirmation(t,stat,valid,d.theta,d.h_s,d.q_factor*.1,30)
        results.append({'detector_id':di,**detector.asdict(d),**result,'alarm':result['confirmation_s'] is not None,
                        'confirmation_delay_from_command_s':result['confirmation_s']-30 if result['confirmation_s'] is not None else None,
                        'min_coverage':float(cov[t>=30].min())})
    # Individual decline candidates provide timestamp/edge evidence, never automatic qualification.
    response=[]
    allx=np.array([[lookup[(f's{i}',round(time,8))]['speed_mps'] for time in t] for i in range(16)])
    base=allx[:,(t>=25)&(t<30)].mean(axis=1)
    for i in range(16):
        r=detector.first_confirmation(t,base[i]-allx[i],np.ones(len(t),bool),.25,.5,.11,30)
        response.append({'vehicle_id':f's{i}',**r,'response_rule':'decline>=0.25m/s, observed span>=0.5s; candidate only'})
    ordered=0
    for i in range(1,16):
        a,b=response[i-1],response[i]
        if a['onset_upper_s'] is not None and b['onset_lower_s'] is not None and a['onset_upper_s']<b['onset_lower_s']:
            ordered+=1
    return results,response,ordered


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();out=a.output_dir.resolve()
    free=shutil.disk_usage(out.anchor).free
    if free<2**30:raise RuntimeError('insufficient disk reserve')
    binary=Path(shutil.which('sumo') or '')
    if not binary.is_file():raise RuntimeError('SUMO not found')
    home=binary.parent.parent;sys.path.insert(0,str(home/'tools'))
    import traci
    import traci.constants as tc
    out.mkdir(parents=True,exist_ok=False)
    (out/'nodes.nod.xml').write_text('<nodes><node id="a" x="0" y="0"/><node id="b" x="5000" y="0"/></nodes>')
    (out/'edges.edg.xml').write_text('<edges><edge id="cal" from="a" to="b" numLanes="1" speed="15"/></edges>')
    net=out/'network.net.xml'
    network_command=[str(home/'bin/netconvert.exe'),'-n',str(out/'nodes.nod.xml'),'-e',str(out/'edges.edg.xml'),'-o',str(net)]
    proc=subprocess.run(network_command,text=True,capture_output=True,check=True)
    (out/'network_build.log').write_text(proc.stdout+proc.stderr,encoding='utf-8')
    write_json(out/'provenance.json',{'status':'CALIBRATION_ONLY','domain':'controlled_B_sumo','git_sha':detector.git('rev-parse','HEAD'),
        'dirty_status':detector.git('status','--short'),'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),
        'traci_path':traci.__file__,'sumo_version':subprocess.check_output([str(binary),'--version'],text=True),
        'free_bytes_before':free,'command_argv':sys.argv,'network_command':network_command,'created_utc':datetime.now(timezone.utc).isoformat()})
    protocol=Path('docs/research/P2/P2_TASK3_CALIBRATION_PROTOCOL.md')
    for src,name in [(Path(__file__),'script_snapshot.py'),(Path(detector.__file__),'detector_snapshot.py'),(protocol,'protocol_snapshot.md')]:
        (out/name).write_bytes(src.read_bytes())
    ds=detector.detectors();allresults=[];runaudits=[]
    try:
        for split,seedbase in [('calibration',202611020),('validation',202711020)]:
            for amplitude,duration in [(0.,0.),(2.5,3.),(2.5,6.),(5.,3.),(5.,6.)]:
                for rep in range(6):
                    seed=seedbase+rep;name=f'{split}__a{amplitude}__d{duration}__seed{seed}'
                    begin=time.monotonic();rows=run_one(traci,tc,binary,net,out/name,seed,amplitude,duration)
                    results,response,ordered=evaluate(rows,ds)
                    detector.write_csv(out/name/'individual_response_candidates.csv',response)
                    for r in results:allresults.append({'split':split,'condition':f'a{amplitude}_d{duration}','seed':seed,'run':name,**r})
                    runaudits.append({'run':name,'split':split,'amplitude':amplitude,'duration':duration,'seed':seed,'status':'PASS',
                                      'strict_ordered_candidate_edges':ordered,'qualified_witness':False,'elapsed_s':time.monotonic()-begin})
                    print(json.dumps(runaudits[-1]),flush=True)
    except Exception as e:
        write_json(out/'FAILED_STOP.json',{'error':type(e).__name__+': '+str(e),'completed_runs':len(runaudits),'rule':'stop, no scenario adjustment'})
        raise
    finally:
        if allresults:detector.write_csv(out/'detector_results.csv',allresults)
        if runaudits:detector.write_csv(out/'run_audits.csv',runaudits)
    summaries=[]
    for split in ['calibration','validation']:
        for condition in sorted({r['condition'] for r in allresults}):
            for di,d in enumerate(ds):
                group=[r for r in allresults if r['split']==split and r['condition']==condition and r['detector_id']==di]
                k=sum(r['alarm'] for r in group);lo,hi=detector.wilson(k,len(group))
                delays=[r['confirmation_delay_from_command_s'] for r in group if r['alarm']]
                summaries.append({'split':split,'condition':condition,'detector_id':di,**detector.asdict(d),
                                  'n':len(group),'alarm_count':k,'alarm_fraction':k/len(group),'lo95':lo,'hi95':hi,
                                  'mean_confirmation_delay_s':float(np.mean(delays)) if delays else None,
                                  'interpretation':'null FPR' if condition=='a0.0_d0.0' else 'command-conditioned alarm, NOT arrival sensitivity'})
    detector.write_csv(out/'calibration_summary.csv',summaries)
    (out/'SHA256SUMS').write_text(''.join(f'{detector.sha(f)}  {f.relative_to(out).as_posix()}\n' for f in sorted(out.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'),encoding='utf-8')
    print(json.dumps({'status':'CALIBRATION_ONLY','domain':'controlled_B_sumo','runs':len(runaudits),'detector_evaluations':len(allresults),'summary_groups':len(summaries),'output':str(out)}))


if __name__=='__main__':main()
