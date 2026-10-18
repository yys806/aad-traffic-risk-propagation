"""Four predeclared engineering runs; no search, calibration or event-rate fit."""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import psutil

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
from riskprop.stage_0_5_calibration_gaps import seal_package
from riskprop.stage_0_5_calibration_readiness import _sha256_file, _write_json
from riskprop.stage_0_5_sumo import (
    _ensure_traci_importable, sumo_environment, build_candidate_network,
    _write_sumo_config, compute_sumo_measurements, _sumo_binary,
)


def make_plan(diagnostics: dict, strata: dict) -> dict:
    rows=[r for r in strata["slices"] if r["eligible"]]
    fleet=[]
    windows=diagnostics["windows"]
    total=sum(w["fleet"]["vehicles"] for w in windows.values())
    for i in range(3):
        items=[w["fleet"]["classes"][i] for w in windows.values()]
        # Per-window medians are averaged by class count; this is a benchmark
        # surrogate, not a claim to be the exact pooled empirical median.
        count=sum(s["vehicles"] for s in items)
        fleet.append(dict(code=i+1,share=count/total,vClass=items[0]["candidate_vClass"],
            length_m=sum(s["length_m"]["quantiles"]["0.5"]*s["vehicles"] for s in items)/count))
    runs=[]
    for label in ["Low-density","Medium-density","High-density"]:
        subset=[r for r in rows if r["density_stratum"]==label]
        target_k=float(np.median([r["density_veh_km_lane"] for r in subset]))
        target_v=float(np.median([r["mean_speed_mps"] for r in subset]))
        for dt in ([.05,.1] if label=="Medium-density" else [.05]):
            runs.append(dict(id=label.lower().replace("-density","")+f"_{dt:.2f}",
                load=label,target_density_veh_km_lane=target_k,speed_cap_mps=target_v,
                inflow_veh_h=target_k*target_v*3.6*3,internal_step_s=dt))
    return dict(mode="engineering_benchmark_only",seed=20261018,duration_s=300.,
        recorded_step_s=.1,diagnostic_window_s=[60.,300.],
        diagnostic_window_note="predeclared engineering summary only; not an approved warmup",
        fleet=fleet,runs=runs,optimization=False,p2_events_computed=False,
        fixture="distributed initial occupancy plus deterministic open-boundary throughflow; cap at observed stratum speed",
        ramp_demand=0,ramp_note="no identifiable ramp demand; topology retained, structural behavior not tested",
        limits=dict(wall_timeout_s=300,collision_action="warn",teleport_disabled=True),
        cost_scope="network build + SUMO + subscription recorder + unified row measurements + parquet; formal P2 extraction not included")


def account(configured: int,departed: set,arrived: set,present: set) -> dict:
    return dict(configured_vehicles=configured,departed_vehicles=len(departed),arrived_vehicles=len(arrived),
        insertion_unserved_at_end=configured-len(departed),present_at_end=len(present),
        conservation_residual=len(departed)-len(arrived)-len(present))


def run_one(plan: dict,spec: dict,out: Path) -> dict:
    if out.exists(): raise ValueError(f"refusing overwrite {out}")
    out.mkdir()
    start=time.perf_counter()
    peak=dict(sampled_combined_rss_bytes=0,python_rss_bytes=0,sumo_rss_bytes=0)
    stop=threading.Event()
    proc=psutil.Process()
    def sample():
        while not stop.is_set():
            try:
                p=proc.memory_info().rss
                children=[c.memory_info().rss for c in proc.children(recursive=True) if c.is_running()]
                s=sum(children)
                peak["sampled_combined_rss_bytes"]=max(peak["sampled_combined_rss_bytes"],p+s)
                peak["python_rss_bytes"]=max(peak["python_rss_bytes"],p)
                peak["sumo_rss_bytes"]=max(peak["sumo_rss_bytes"],s)
            except psutil.Error: pass
            stop.wait(.02)
    thread=threading.Thread(target=sample,daemon=True)
    thread.start()
    _ensure_traci_importable()
    import traci
    import traci.constants as c
    network=build_candidate_network(out)
    netroot=ET.parse(network["network"]).getroot()
    lengths={e.attrib["id"]:float(e.find("lane").attrib["length"]) for e in netroot.findall("edge") if not e.attrib["id"].startswith(":")}
    routes=["main_0","main_1","main_2"]
    length=sum(lengths[e] for e in routes)
    rng=np.random.default_rng(plan["seed"])
    vehicles=[]
    types={}
    fleet=plan["fleet"]
    def choose(): return int(rng.choice(3,p=[v["share"] for v in fleet]))
    n_lane=int(round(spec["target_density_veh_km_lane"]*length/1000))
    for lane in range(3):
        for i in range(n_lane):
            routepos=(i+.5)*length/n_lane
            edge=0
            while routepos>=lengths[routes[edge]]:
                routepos-=lengths[routes[edge]]; edge+=1
            v=choose(); vid=f"initial_{lane}_{i}"; types[vid]=v
            vehicles.append((0.,f'<vehicle id="{vid}" type="t{v}" route="main" depart="0" departEdge="{edge}" departLane="{lane}" departPos="{routepos:.5f}" departSpeed="{spec["speed_cap_mps"]:.5f}"/>'))
    headway=3600/spec["inflow_veh_h"]
    for i,t in enumerate(np.arange(headway,plan["duration_s"]-spec["internal_step_s"],headway)):
        v=choose(); vid=f"inflow_{i}"; types[vid]=v
        vehicles.append((float(t),f'<vehicle id="{vid}" type="t{v}" route="main" depart="{t:.5f}" departLane="{i%3}" departPos="base" departSpeed="{spec["speed_cap_mps"]:.5f}"/>'))
    vtypes=[f'<vType id="t{i}" vClass="{v["vClass"]}" length="{v["length_m"]:.7f}" carFollowModel="Krauss" minGap="2.5" tau="1" accel="2.6" decel="4.5" emergencyDecel="9" apparentDecel="4.5" sigma="0.5" sigmaStep="1" actionStepLength="0.1" maxSpeed="{spec["speed_cap_mps"]:.7f}" speedFactor="1" speedDev="0"/>' for i,v in enumerate(fleet)]
    routepath=out/"demand.rou.xml"
    routepath.write_text('<routes>\n'+'\n'.join(vtypes)+'\n<route id="main" edges="main_0 main_1 main_2"/>\n'+'\n'.join(v for _,v in sorted(vehicles,key=lambda x:x[0]))+'\n</routes>\n',encoding="utf-8")
    cfg=_write_sumo_config(out,net_path=network["network"],routes_path=routepath,seed=plan["seed"],duration_s=plan["duration_s"],internal_step_s=spec["internal_step_s"])
    _write_json(out/"config.json",dict(plan=plan,run=spec,preload_vehicles=n_lane*3,
        built_edge_lengths_m=lengths,configuration_sha256={p.name:_sha256_file(p) for p in [cfg,routepath,network["network"]]}))
    departed=set();arrived=set();teleport=set();collision=set();max_pending=0;rows=[];frames=[];count=0
    writer=None
    def flush():
        nonlocal rows,writer,count
        if not rows: return
        frame=compute_sumo_measurements(pd.DataFrame(rows))
        # Stable schema even if a batch has no leader or no type category.
        table=pa.Table.from_pandas(frame,preserve_index=False)
        if writer is None: writer=pq.ParquetWriter(out/"state.parquet",table.schema,compression="zstd")
        table=table.cast(writer.schema)
        writer.write_table(table)
        count+=len(frame)
        rows=[]
    failure=None
    runid=spec["id"]
    present=set()
    try:
        traci.start([_sumo_binary(),"-c",str(cfg),"--no-step-log","true","--duration-log.disable","true","--error-log",str(out/"sumo_errors.log")],label=runid)
        conn=traci.getConnection(runid)
        dt=spec["internal_step_s"]
        stride=round(.1/dt)
        variables=(c.VAR_SPEED,c.VAR_ACCELERATION,c.VAR_POSITION,c.VAR_LANE_ID,c.VAR_LANEPOSITION,c.VAR_ROAD_ID,c.VAR_LEADER)
        for step in range(1,round(plan["duration_s"]/dt)+1):
            conn.simulationStep()
            dep=conn.simulation.getDepartedIDList(); departed.update(dep)
            arrived.update(conn.simulation.getArrivedIDList())
            teleport.update(conn.simulation.getStartingTeleportIDList())
            collision.update(conn.simulation.getCollidingVehiclesIDList())
            for vid in dep:
                conn.vehicle.subscribe(vid,variables,parameters={c.VAR_LEADER:("d",1000.)})
            if step%stride: continue
            now=round(step*dt,6)
            data=conn.vehicle.getAllSubscriptionResults()
            present=set(data)
            pending=len(conn.simulation.getPendingVehicles());max_pending=max(max_pending,pending)
            nlocal=0;speeds=[];local_speeds=[];halted=0
            for vid,values in data.items():
                leader=values[c.VAR_LEADER]
                lid=leader[0] if leader and leader[0] else None
                leader_values=data.get(lid)
                road=values[c.VAR_ROAD_ID];pos=values[c.VAR_LANEPOSITION]
                if road=="main_1" and 50<=pos<250:
                    nlocal+=1;local_speeds.append(values[c.VAR_SPEED])
                speed=values[c.VAR_SPEED];speeds.append(speed);halted+=speed<.1
                rows.append(dict(run_id=runid,scenario_id="us101_highway_baseline",experiment_mode="no_message_baseline",
                    configured_seed=plan["seed"],simulation_step=step,time_s=now,vehicle_id=vid,
                    trajectory_id=runid+"|"+vid,incarnation_id=runid+"|"+vid,
                    edge_id=road,lane_id=values[c.VAR_LANE_ID],longitudinal_position_m=pos,
                    x_m=values[c.VAR_POSITION][0],y_m=values[c.VAR_POSITION][1],
                    speed_mps=speed,acceleration_mps2=values[c.VAR_ACCELERATION],
                    vehicle_type=f"t{types[vid]}",leader_id=lid,
                    leader_incarnation_id=runid+"|"+lid if leader_values else None,
                    leader_identity_status="observed" if leader_values else "unresolved" if lid else "not_applicable",
                    leader_speed_mps=leader_values[c.VAR_SPEED] if leader_values else np.nan,
                    net_gap_m=leader[1]+2.5 if lid else np.nan))
            frames.append(dict(time_s=now,present=len(data),local_vehicles=nlocal,
                mean_speed_mps=float(np.mean(speeds)) if speeds else None,
                local_mean_speed_mps=float(np.mean(local_speeds)) if local_speeds else None,
                halted=halted,pending=pending,
                departed=len(departed),arrived=len(arrived)))
            if step%round(30/dt)==0: flush()
            if time.perf_counter()-start>plan["limits"]["wall_timeout_s"]:
                failure="predeclared_wall_timeout";break
    except Exception as exc:
        failure=f"{type(exc).__name__}: {exc}"
    finally:
        try: conn.close()
        except Exception: pass
        try: flush()
        finally:
            if writer is not None: writer.close()
            stop.set();thread.join(timeout=2)
    wall=time.perf_counter()-start
    f=pd.DataFrame(frames)
    f.to_csv(out/"network_frames.csv",index=False)
    evals=f[f.time_s.ge(60)] if len(f) else f
    at60=f[f.time_s.le(60)].iloc[-1] if len(f) else None
    eval_duration=float(f.time_s.max()-60) if len(evals) else 0
    summary=dict(id=runid,status="failed" if failure else "completed",failure=failure,engineering_benchmark_only=True,
        **account(len(vehicles),departed,arrived,present),
        max_pending_vehicles=max_pending,collision_vehicle_ids=sorted(collision),teleport_vehicle_ids=sorted(teleport),
        wall_s=wall,simulated_s=float(f.time_s.max()) if len(f) else 0,
        wall_s_per_simulated_s=wall/float(f.time_s.max()) if len(f) else None,
        memory=peak,memory_sampling_interval_s=.02,output_rows=count,
        output_state_bytes=(out/"state.parquet").stat().st_size if (out/"state.parquet").exists() else 0,
        output_total_bytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file()),
        evaluation_achieved_density_veh_km_lane=float(evals.local_vehicles.mean()/.2/3) if len(evals) else None,
        evaluation_mean_speed_mps=float(np.average(evals.mean_speed_mps,weights=evals.present)) if len(evals) else None,
        evaluation_local_mean_speed_mps=float(np.average(evals.local_mean_speed_mps,weights=evals.local_vehicles)) if len(evals) else None,
        evaluation_mean_present=float(evals.present.mean()) if len(evals) else None,
        evaluation_max_halted=int(evals.halted.max()) if len(evals) else None,
        evaluation_achieved_exit_flow_veh_h=(len(arrived)-int(at60.arrived))*3600/eval_duration if eval_duration>0 else None,
        engineering_gridlock=bool(len(evals) and evals.tail(600).mean_speed_mps.max()<.1),
        scope_note=plan["cost_scope"],recorded_step_s=.1,internal_step_s=spec["internal_step_s"],seed=plan["seed"])
    if len(f):
        summary["time_bins_60s"]=[dict(start_s=a,end_s=a+60,
            mean_present=float(part.present.mean()),mean_local_density_veh_km_lane=float(part.local_vehicles.mean()/.6),
            mean_speed_mps=float(np.average(part.mean_speed_mps,weights=part.present)),
            max_pending=int(part.pending.max()),max_halted=int(part.halted.max()))
            for a in range(0,300,60)
            if len(part:=f[f.time_s.gt(a)&f.time_s.le(a+60)])]
    _write_json(out/"summary.json",summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    if a.output.exists(): raise ValueError("refusing to overwrite benchmark")
    a.output.mkdir(parents=True)
    d=json.loads((a.diagnostics/"diagnostics.json").read_text(encoding="utf-8"))
    s=json.loads((a.diagnostics/"unified_strata.json").read_text(encoding="utf-8"))
    plan=make_plan(d,s)
    plan["input_sha256"]={n:_sha256_file(a.diagnostics/n) for n in ["diagnostics.json","unified_strata.json"]}
    plan["benchmark_script_sha256"]=_sha256_file(Path(__file__))
    _write_json(a.output/"benchmark_plan.json",plan)  # frozen before any SUMO run
    _ensure_traci_importable()
    env=sumo_environment()
    _write_json(a.output/"environment.json",env)
    results=[]
    for spec in plan["runs"]:
        summary=run_one(plan,spec,a.output/spec["id"])
        results.append(summary)
        print(json.dumps(summary),flush=True)
        _write_json(a.output/"benchmark_summary.json",dict(environment=env,
            plan_sha256=_sha256_file(a.output/"benchmark_plan.json"),results=results,
            config_sha256={r["id"]:_sha256_file(a.output/r["id"]/"config.json") for r in results}))
    seal_package(a.output)


if __name__=="__main__": main()
