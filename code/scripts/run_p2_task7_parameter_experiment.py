"""Prelisted isolated Task7 SUMO calibration; no production/holdout inputs."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import numpy as np
import psutil
import scipy
import p2_task7_measurement as m

ROOT=Path(__file__).resolve().parents[2]
CONDITIONS={'N0':(0.,0.),'N1':(8.,8.),'P11':(4.,4.),'P21':(8.,4.),
            'P12':(4.,8.),'P22':(8.,8.),'Plocal':(2.,1.),'A0':(8.,8.)}
DENSITIES={'low':(24,35.),'medium':(40,23.),'high':(64,15.)}

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()

def prepare(out):
    if out.exists(): raise FileExistsError(out)
    free=shutil.disk_usage(out.anchor).free
    if free < 30*2**30: raise RuntimeError('20GiB system reserve plus 10GiB experiment cap unavailable')
    binary=Path(shutil.which('sumo') or '')
    if not binary.is_file(): raise RuntimeError('SUMO binary missing')
    out.mkdir(parents=True)
    for name in ['raw','truth','audit','detector','config','snapshots']: (out/name).mkdir()
    home=binary.parent.parent
    (out/'config/nodes.nod.xml').write_text('<nodes><node id="a" x="0" y="0"/><node id="b" x="6000" y="0"/></nodes>')
    (out/'config/edges.edg.xml').write_text('<edges><edge id="cal" from="a" to="b" numLanes="2" speed="10"/></edges>')
    net=out/'config/network.net.xml'
    command=[str(home/'bin/netconvert.exe'),'-n',str(out/'config/nodes.nod.xml'),'-e',str(out/'config/edges.edg.xml'),'-o',str(net)]
    p=subprocess.run(command,capture_output=True,text=True,check=True)
    (out/'audit/network_build.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    units=[]
    # Distinct seed per traffic realization across conditions/densities. No reused seed pooling.
    roots={'calibration':[20261102,7,314159],'independent_validation':[20261102,7,271828]}
    seeds=np.random.SeedSequence(roots['calibration']).spawn(576)
    j=0
    for density,(count,spacing) in DENSITIES.items():
        for condition,(amplitude,hold) in CONDITIONS.items():
            for rep in range(24):
                uid=f'C_{density}_{condition}_{rep:02d}'
                units.append({'unit_id':uid,'dependency_block':uid,'split':'calibration',
                    'density':density,'condition':condition,'rep':rep,'count':count,'spacing_m':spacing,
                    'sumo_seed':int(seeds[j].generate_state(1)[0]%2147483646)+1,
                    'seed_spawn_key':list(seeds[j].spawn_key),'amplitude_mps':amplitude,'hold_s':hold,
                    'specified_source':'decoy' if condition in ('N1','A0') else 's0',
                    'actuated_source':None if condition=='N0' else 'decoy' if condition=='N1' else 's0',
                    'scenario_family':'straight_same_lane_native_Krauss_v1','input_trace':'generated_no_historical_input'})
                j+=1
    manifest={'task_id':'AAD-P2-TASK7-PARAMETER-DETERMINATION-EXPERIMENT-20261102',
        'status':'CALIBRATION_ONLY','protocol':'AAD-P2-PARAM-20261102-v1.0','truth_version':m.TRUTH_VERSION,
        'definitions':'AAD-SCI-DEF-20261102-P2T6-v0.4','region':m.REGION,'cohort':list(m.COHORT),
        'pre':m.PRE,'monitor':m.MONITOR,'followup_end':50.,'source_plan':30.,'raw_dt':.05,
        'truth_a':m.A_STAR,'truth_b':m.B_STAR,'truth_d':m.D_STAR,'truth_status':'finite model signal Proposal; no universal minimum',
        'sac':{'fpr':.01,'far':.01,'timely_recall':.95,'unknown':.05,'beta_V':.05,'power':.9,'status':'finite-domain Proposal'},
        'budget':{'workers':4,'C_units':576,'V_wall_s':7200,'max_output_bytes':10*2**30,'disk_reserve_bytes':20*2**30},
        'seed_roots':roots,'units':units,'formal_A':0,'formal_qualified':0,'stage_status_unchanged':True,
        'locked_holdout_reads':0,'communication':'disabled','binary':str(binary),'network_sha256':m.sha(net)}
    for src in [Path(__file__),Path(m.__file__),ROOT/'docs/research/P2/P2_TASK7_EXPERIMENT_PROTOCOL.md']:
        shutil.copy2(src,out/'snapshots'/src.name)
    manifest['source_hashes']={str(p.relative_to(ROOT)):m.sha(p) for p in [Path(__file__),Path(m.__file__),ROOT/'docs/research/P2/P2_TASK7_EXPERIMENT_PROTOCOL.md']}
    m.dump(out/'manifest.json',manifest)
    sys.path.insert(0,str(home/'tools'))
    import traci
    m.dump(out/'provenance.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'git_sha':git('rev-parse','HEAD'),
        'dirty_status':git('status','--short'),'dirty_diff_sha256':__import__('hashlib').sha256(git('diff','--binary').encode()).hexdigest(),
        'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__,
        'platform':platform.platform(),'cpu_logical':psutil.cpu_count(),'memory_available_bytes':psutil.virtual_memory().available,
        'disk_free_before':free,'raw_estimate_bytes':2*2**30,'temporary_estimate_bytes':2**30,
        'sumo_version':subprocess.check_output([str(binary),'--version'],text=True),'binary_sha256':m.sha(binary),
        'traci_path':traci.__file__,'traci_sha256':m.sha(traci.__file__),'manifest_sha256':m.sha(out/'manifest.json'),
        'command_argv':sys.argv,'network_command':command,'formal_logic_changed':False})
    return manifest

def one(unit,out_string,binary_string):
    out=Path(out_string);binary=Path(binary_string);home=binary.parent.parent
    os.environ['SUMO_HOME']=str(home);sys.path.insert(0,str(home/'tools'))
    import traci
    import traci.constants as tc
    uid=unit['unit_id'];folder=out/'raw'/uid;folder.mkdir(exist_ok=False)
    ids=[f's{i}' for i in range(unit['count'])]+['decoy'];mapping={v:i for i,v in enumerate(ids)}
    vehicles=[f'<vehicle id="s{i}" type="native" route="r" depart="0" departLane="0" departPos="{2800-unit["spacing_m"]*i}" departSpeed="10"/>' for i in range(unit['count'])]
    vehicles.append('<vehicle id="decoy" type="native" route="r" depart="0" departLane="1" departPos="2800" departSpeed="10"/>')
    route=folder/'traffic.rou.xml'
    route.write_text('<routes><vType id="native" carFollowModel="Krauss" accel="2.6" decel="4.5" emergencyDecel="9" length="5" minGap="2.5" tau="0.6" sigma="0.25" maxSpeed="10" speedFactor="1" speedDev="0" lcStrategic="-1" lcCooperative="-1" lcSpeedGain="-1" lcKeepRight="-1"/><route id="r" edges="cal"/>'+''.join(vehicles)+'</routes>')
    command=[str(binary),'-n',str(out/'config/network.net.xml'),'-r',str(route),'--step-length','.05','--end','50',
        '--seed',str(unit['sumo_seed']),'--step-method.ballistic','true','--no-step-log','true','--duration-log.disable','true',
        '--collision.action','warn','--log',str(folder/'sumo.log'),'--error-log',str(folder/'error.log')]
    shape=(1000,len(ids));raw={k:np.empty(shape) for k in ['v','a','x','gap','native']}
    raw.update({'t':np.empty(1000),'lane':np.empty(shape,dtype=np.int8),'leader':np.empty(shape,dtype=np.int16)})
    controls=[];begin=time.monotonic();source_onset=None;pre_source=None;conn=None;written=0
    audit={**unit,'status':'RUNNING','command':command,'controls':controls,'collisions':0,'teleports':0,
           'native_target_setters':0,'source_execution':None,'actual_source_onset':None,
           'clock':'post-step SUMO time; after-step command affects subsequent integration',
           'clock_offset':'same simulation clock; not an external-device calibration','clock_drift':'same simulation clock',
           'phase_interval_s':[0,.05],'source_attribution_truth':'Unknown except disconnected A0/N1 structural controls'}
    try:
        with contextlib.redirect_stdout(io.StringIO()): traci.start(command,label=uid,verbose=False)
        conn=traci.getConnection(uid)
        variables=[tc.VAR_SPEED,tc.VAR_ACCELERATION,tc.VAR_LANEPOSITION,tc.VAR_LANE_INDEX,tc.VAR_SPEED_WITHOUT_TRACI,tc.VAR_LEADER]
        for step in range(1000):
            conn.simulationStep();now=conn.simulation.getTime();raw['t'][step]=now
            if step==0:
                if set(conn.vehicle.getIDList()) != set(ids): raise RuntimeError('incomplete insertion')
                for vid in ids: conn.vehicle.subscribe(vid,variables,parameters={tc.VAR_LEADER:('d',2000.)})
            data=conn.vehicle.getAllSubscriptionResults()
            if set(data)!=set(ids): raise RuntimeError('identity panel incomplete')
            audit['collisions']+=conn.simulation.getCollidingVehiclesNumber();audit['teleports']+=conn.simulation.getStartingTeleportNumber()
            if audit['collisions'] or audit['teleports']: raise RuntimeError('collision or teleport')
            for vid,d in data.items():
                i=mapping[vid];leader=d[tc.VAR_LEADER];lid,dist=leader if leader else ('',-1.)
                raw['v'][step,i]=d[tc.VAR_SPEED];raw['a'][step,i]=d[tc.VAR_ACCELERATION];raw['x'][step,i]=d[tc.VAR_LANEPOSITION]
                raw['native'][step,i]=d[tc.VAR_SPEED_WITHOUT_TRACI];raw['lane'][step,i]=d[tc.VAR_LANE_INDEX]
                raw['leader'][step,i]=mapping.get(lid,-1);raw['gap'][step,i]=dist+2.5 if lid else np.nan
                if vid not in ('s0','decoy'):
                    if abs(raw['v'][step,i]-raw['native'][step,i])>1e-8: raise RuntimeError('non-native target response')
                    if lid != f's{i-1}' or raw['lane'][step,i]!=0: raise RuntimeError('leader/lane changed')
                    geometric=data[lid][tc.VAR_LANEPOSITION]-d[tc.VAR_LANEPOSITION]-5
                    if geometric<=0 or abs(geometric-raw['gap'][step,i])>1e-6: raise RuntimeError('gap convention or collision geometry')
            written=step+1
            source=unit['actuated_source'];hold=unit['hold_s'];amplitude=unit['amplitude_mps']
            if source:
                idx=mapping[source]
                if step==599:
                    pre_source=float(raw['v'][step,idx]);conn.vehicle.slowDown(source,10-amplitude,1.)
                    controls.append({'time_s':now,'method':'slowDown','vehicle':source,'speed':10-amplitude,'duration_s':1.})
                    audit['source_execution']=now
                    if source=='s0' and raw['x'][step,idx]<=m.REGION[1]: raise RuntimeError('actuated source inside target region')
                if step>=600 and source_onset is None and raw['v'][step,idx]<pre_source-1e-6 and abs(raw['v'][step,idx]-raw['native'][step,idx])>1e-6:
                    source_onset=[float(raw['t'][step-1]),now];audit['actual_source_onset']=source_onset
                if step==619:
                    conn.vehicle.setSpeed(source,10-amplitude);controls.append({'time_s':now,'method':'setSpeed','vehicle':source,'speed':10-amplitude})
                if step==int(round((31+hold)/.05))-1:
                    conn.vehicle.slowDown(source,10,1.);controls.append({'time_s':now,'method':'slowDown','vehicle':source,'speed':10,'duration_s':1.})
                if step==int(round((32+hold)/.05))-1:
                    conn.vehicle.setSpeed(source,-1);controls.append({'time_s':now,'method':'setSpeed','vehicle':source,'speed':-1})
        if source and source_onset is None: raise RuntimeError('source command no verified physical execution')
        audit['status']='COMPLETE'
    except Exception as e:
        audit['status']='FAILED_STOP';audit['error']=type(e).__name__+': '+str(e)
    finally:
        if conn is not None: conn.close()
        raw={k:v[:written] for k,v in raw.items()};np.savez_compressed(folder/'trajectory.npz',**raw)
        audit['elapsed_s']=time.monotonic()-begin;audit['rows']=written;audit['raw_sha256']=m.sha(folder/'trajectory.npz')
        m.dump(out/'audit'/f'{uid}.json',audit)
    if audit['status']=='COMPLETE': m.dump(out/'truth'/f'{uid}.json',m.truth(raw,audit))
    return {'unit_id':uid,'status':audit['status'],'elapsed_s':audit['elapsed_s'],'error':audit.get('error')}

def execute(out,pilot,workers):
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    prov=json.loads((out/'provenance.json').read_text(encoding='utf-8'))
    if m.sha(out/'manifest.json')!=prov['manifest_sha256']: raise RuntimeError('manifest drift')
    for path,value in manifest['source_hashes'].items():
        if m.sha(ROOT/path)!=value: raise RuntimeError('source version drift: '+path)
    if shutil.disk_usage(out.anchor).free<20*2**30: raise RuntimeError('disk reserve unavailable')
    if (out/'audit/FAILED_STOP.json').exists(): raise RuntimeError('prior hard stop; do not resume')
    units=manifest['units']
    if pilot: units=[u for u in units if u['rep']==0 and u['condition'] in ('N0','P22')]
    pending=[u for u in units if not (out/'audit'/f'{u["unit_id"]}.json').exists()]
    results=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(one,u,str(out),manifest['binary']):u for u in pending}
        for future in as_completed(futures):
            r=future.result();results.append(r);print(json.dumps(r),flush=True)
            if r['status']!='COMPLETE':
                m.dump(out/'audit/FAILED_STOP.json',r)
                for other in futures: other.cancel()
                raise RuntimeError('hard stop '+r['unit_id'])
    m.dump(out/'audit'/('pilot_completion.json' if pilot else 'calibration_completion.json'),
           {'completed_this_invocation':results,'completed_total':len(list((out/'truth').glob('C_*.json'))),
            'disk_free_after':shutil.disk_usage(out.anchor).free,'workers':workers})

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--prepare',action='store_true');p.add_argument('--pilot',action='store_true');p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();out=a.output_dir.resolve()
    allowed=(ROOT/'code/outputs/calibration').resolve()
    if out.parent!=allowed or not out.name.startswith('p2_task7_'): raise ValueError('Task7 isolated output only')
    if a.prepare: prepare(out);print(json.dumps({'prepared':str(out),'units':576}));return
    execute(out,a.pilot,a.workers)

if __name__=='__main__': main()
