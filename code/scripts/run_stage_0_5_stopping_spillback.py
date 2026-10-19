"""B1.1: isolated independent contracts and <=4 declared SUMO micro fixtures."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
RESULT_ID="RES-STAGE-0.5-STOPPING-SPILLBACK-CONTRACT-V1"
SUMO_SOURCE_COMMIT="fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3"
HISTORY=["numerical_stop_diagnostic.json","queue_diagnostics.json","execution_stop_observation.json",
    "data_isolation_preflight.json","experiment_plan.json","run_manifest.json"]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def prepare(batch):
    if (batch/"experiment_plan.json").exists():raise ValueError("sealed micro batch cannot be prepared again")
    from riskprop.stage_0_5_boundary_bottleneck import _copy_runtime
    from riskprop.stage_0_5_sumo import _sumo_binary,_netconvert_binary
    batch.mkdir(parents=True,exist_ok=True);(batch/"inputs/history").mkdir(parents=True,exist_ok=True)
    base=ROOT/"evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1"
    manifest=json.loads((base/"manifest.json").read_text(encoding="utf-8"))
    bindings={name:dict(path=name,role="engineering_metadata",kind="historical_b1_metadata",
        sha256=next(f["sha256"] for f in manifest["files"] if f["path"]==name)) for name in HISTORY}
    write(batch/"source_staging_manifest.json",dict(sources=bindings,declared_before_reads=True,
        no_real_data_inputs=True,no_old_C_states=True,prohibited=["us101__0820_0835","locked_holdout","historical Stage0.2 full-source artifacts"]))
    for name,entry in bindings.items():
        if sha(base/name)!=entry["sha256"]:raise PermissionError("historical metadata SHA mismatch")
        shutil.copyfile(base/name,batch/"inputs/history"/name)
    write(batch/"historical_source_manifest.json",bindings)
    sources=batch/"official_source";sources.mkdir(exist_ok=True)
    source_manifest={}
    for tail in ["microsim/MSVehicle.cpp","microsim/MSVehicle.h","libsumo/Vehicle.cpp","utils/common/SUMOTime.h"]:
        url="https://raw.githubusercontent.com/eclipse-sumo/sumo/"+SUMO_SOURCE_COMMIT+"/src/"+tail
        target=sources/(tail.replace("/","_"))
        source_manifest[target.name]=dict(url=url,tag="v1_26_0",resolved_commit=SUMO_SOURCE_COMMIT,purpose="official implementation audit only")
    write(batch/"official_source_request_manifest.json",source_manifest)
    for name,entry in source_manifest.items():
        target=sources/name
        if not target.exists() or not (sources/"immutable_verified.json").exists():
            old_sha=sha(target) if target.exists() else None
            with urllib.request.urlopen(entry["url"],timeout=30) as response:raw=response.read(2_000_000)
            target.write_bytes(raw)
            entry["initial_tag_fetch_sha256"]=old_sha;entry["tag_and_immutable_fetch_equal"]=old_sha==sha(target) if old_sha else None
        entry["sha256"]=sha(target);entry["bytes"]=target.stat().st_size
    write(batch/"official_source_manifest.json",source_manifest)
    write(sources/"immutable_verified.json",dict(commit=SUMO_SOURCE_COMMIT,files={name:entry["sha256"] for name,entry in source_manifest.items()}))
    _copy_runtime(ROOT,batch)
    for name in ["stage_0_5_stopping_contract.py","stage_0_5_queue_contract.py","stage_0_5_contract_fixtures.py"]:
        source=ROOT/"code/src/riskprop"/name
        if source.exists():shutil.copyfile(source,batch/"runtime/code/src/riskprop"/name)
    for name in ["test_stage_0_5_stopping_contract.py","test_stage_0_5_queue_contract.py"]:
        source=ROOT/"code/tests"/name
        if source.exists():shutil.copyfile(source,batch/"runtime/code/tests"/name)
    shutil.copyfile(Path(__file__),batch/"runtime/code/scripts"/Path(__file__).name)
    dependencies=[];links=batch/"dependency_links";links.mkdir(exist_ok=True)
    for name in ["numpy","pandas","pyarrow","psutil","matplotlib","pytest","packaging","dateutil"]:__import__(name)
    import _winapi
    for name,module in list(sys.modules.items()):
        if "." in name or not getattr(module,"__file__",None):continue
        source=Path(module.__file__).resolve()
        if "site-packages" not in source.parts or source.is_relative_to(Path(sys.prefix).resolve()):continue
        if source.name=="__init__.py":
            targets=[source.parent]+list(source.parent.parent.glob(name.replace("_","-")+"-*.dist-info"))
            if (source.parent.parent/(name+".libs")).is_dir():targets.append(source.parent.parent/(name+".libs"))
            for target in targets:
                link=links/target.name
                if not link.exists():_winapi.CreateJunction(str(target),str(link))
                dependencies.append(str(target))
        else:shutil.copyfile(source,links/source.name)
    write(batch/"isolation_policy.json",dict(runtime_read_roots=[str(Path(sys.prefix).resolve()),str(Path(_sumo_binary()).resolve().parent.parent),os.environ.get("WINDIR","C:/Windows")]+dependencies,
        executables=[sys.executable,str(Path(_sumo_binary()).resolve()),str(Path(_netconvert_binary()).resolve())],
        no_real_data_sources=True,os_complete_monitoring=False))
    write(batch/"preparation_manifest.json",dict(base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        historical_git_tree=subprocess.check_output(["git","rev-parse","HEAD:evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1"],cwd=ROOT,text=True).strip()))
    print("B11_CAPSULE_PREPARED",flush=True)


def environment(batch):
    (batch/"runtime_cache/tmp").mkdir(parents=True,exist_ok=True)
    (batch/"test_tmp").mkdir(exist_ok=True)
    os.environ.update(AAD_B1_CAPSULE=str(batch),PYTHONPATH=str(batch/"runtime/code/src"),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTHONPYCACHEPREFIX=str(batch/"runtime_cache/pycache"),TEMP=str(batch/"runtime_cache/tmp"),TMP=str(batch/"runtime_cache/tmp"))


def tests(batch):
    environment(batch)
    probe=subprocess.run([sys.executable,"-S",str(batch/"runtime/code/scripts/b1_guard_probe.py"),str(batch)],capture_output=True,text=True,timeout=30)
    if probe.returncode:raise RuntimeError("synthetic forbidden-path probe failed")
    names=["test_stage_0_5_stopping_contract.py","test_stage_0_5_queue_contract.py","test_stage_0_5_boundary_bottleneck.py"]
    paths=[str(batch/"runtime/code/tests"/n) for n in names if (batch/"runtime/code/tests"/n).exists()]
    cmd=[sys.executable,"-S",str(batch/"runtime/code/scripts/b1_test_entry.py"),*paths,"-q","-c",str(batch/"runtime/code/pytest.ini"),"--rootdir",str(batch/"runtime/code"),"--basetemp",str(batch/"test_tmp"/str(time.time_ns())),"-o",f"cache_dir={batch/'runtime_cache/pytest'}"]
    r=subprocess.run(cmd,cwd=batch/"runtime/code",capture_output=True,text=True,timeout=120)
    name=f"test_{time.time_ns()}";(batch/(name+".log")).write_text(r.stdout+r.stderr,encoding="utf-8")
    write(batch/(name+".json"),dict(command=cmd,exit_code=r.returncode,output=r.stdout+r.stderr,
        test_sha256={str(p):sha(p) for p in paths},access_audit=json.loads((batch/"preflight_test_access_audit.json").read_text(encoding="utf-8"))))
    write(batch/"preflight.json",dict(passed=r.returncode==0,last_test=name))
    write(batch/"data_isolation_preflight.json",dict(passed=r.returncode==0,
        history_metadata_manifest=json.loads((batch/"historical_source_manifest.json").read_text(encoding="utf-8")),
        official_code_manifest=json.loads((batch/"official_source_manifest.json").read_text(encoding="utf-8")),
        real_data_inputs=[],old_C_state_access=False,historical_Stage0_2_full_source_access=False,
        synthetic_path_probe=json.loads((batch/"guard_probe_result.json").read_text(encoding="utf-8")),
        controlled_python_no_site=True,unexpected_test_denials=0 if r.returncode==0 else "see test access audit",
        os_complete_monitoring=False,native_access_monitored=False,test_log=name))
    print(r.stdout+r.stderr,flush=True)
    if r.returncode:raise RuntimeError("contract tests failed; micro execution forbidden")


def freeze(batch):
    if (batch/"experiment_plan.json").exists():raise ValueError("never overwrite a frozen micro plan")
    if not json.loads((batch/"preflight.json").read_text())["passed"]:raise PermissionError("synthetic preflight not passed")
    from riskprop.stage_0_5_contract_fixtures import QUEUE_CONFIG,synthetic_queue_cases
    from riskprop.stage_0_5_sumo import _sumo_binary,_netconvert_binary
    inputs=batch/"inputs";runs=[]
    for name,split in [("straight",False),("transition",True)]:
        folder=inputs/name;folder.mkdir(exist_ok=True)
        (folder/"nodes.nod.xml").write_text('<nodes><node id="n0" x="0" y="0"/><node id="n1" x="250" y="0"/>'+('<node id="n2" x="500" y="0"/>' if split else '')+'</nodes>',encoding="utf-8")
        (folder/"edges.edg.xml").write_text('<edges><edge id="e0" from="n0" to="n1" numLanes="1" speed="27.78"/>'+('<edge id="e1" from="n1" to="n2" numLanes="1" speed="27.78"/>' if split else '')+'</edges>',encoding="utf-8")
        r=subprocess.run([_netconvert_binary(),"-n",str(folder/"nodes.nod.xml"),"-e",str(folder/"edges.edg.xml"),"-o",str(folder/"micro.net.xml"),"--no-turnarounds","true"],capture_output=True,text=True,timeout=30)
        (folder/"build.log").write_text(r.stdout+r.stderr,encoding="utf-8")
        if r.returncode:raise RuntimeError("micro network generation failed")
    fixed=dict(carFollowModel="Krauss",tau=1.,minGap=2.5,accel=2.6,decel=4.5,apparentDecel=4.5,emergencyDecel=9.,sigma=.5,
        maxSpeed=27.78,speedFactor=1.,speedDev=0.,actionStepLength=.1,sigmaStep=1.,laneChangeModel="LC2013",length=5.)
    for name,step,stop,network in [("motion_005",.05,False,"straight"),("stop_restart_005",.05,True,"straight"),
        ("stop_restart_010",.1,True,"straight"),("transition_005",.05,False,"transition")]:
        route=ET.Element("routes");ET.SubElement(route,"vType",dict(id="fixed",**{k:str(v) for k,v in fixed.items()}))
        vehicle=ET.SubElement(route,"vehicle",dict(id="micro_v",type="fixed",depart="0",departSpeed="10",departLane="0"))
        ET.SubElement(vehicle,"route",dict(edges="e0 e1" if network=="transition" else "e0"))
        if stop:ET.SubElement(vehicle,"stop",dict(lane="e0_0",endPos="80",duration="3",parking="false"))
        demand=inputs/(name+".rou.xml");ET.ElementTree(route).write(demand,encoding="utf-8",xml_declaration=True)
        config=inputs/(name+".sumocfg")
        config.write_text(f'<configuration><input><net-file value="{network}/micro.net.xml"/><route-files value="{name}.rou.xml"/></input><time><begin value="0"/><end value="30"/><step-length value="{step}"/></time><processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/><collision.action value="warn"/></processing><seed value="20261019"/></configuration>',encoding="utf-8")
        runs.append(dict(run_id=name,config=config.relative_to(batch).as_posix(),network=f"inputs/{network}/micro.net.xml",demand=demand.relative_to(batch).as_posix(),step_s=step,duration_s=30.,seed=20261019,expected_ordinary_stop=stop,expected_coordinate_transition=network=="transition"))
    write(batch/"displacement_branch_contract.json",dict(version="b11-displacement-v1",status="Candidate for future scoped audit",integration="explicit ballistic",tolerance_m=1e-6,
        exact_branches=["normal_motion","decelerating_without_stop","starting_from_rest","already_stopped"],
        stop_exact_requires="independent signed internal vNext; TraCI mean acceleration cannot supply it",
        observed_terminal_stop="0<=dx<=v0*dt/2 is a necessary consistency interval only; exact Pending Numerical Equivalence",
        no_internal_speed_inferred_from_tested_displacement=True,all_vehicle_lightweight_screen=True,cohort_modulus=1,
        anomaly_limit=16,quantile_limit=2048,coordinate_transitions="not_evaluable",old_B1_unchanged=True))
    write(batch/"queue_observation_contract.json",QUEUE_CONFIG)
    write(batch/"synthetic_queue_truth.json",synthetic_queue_cases())
    write(batch/"micro_fixture_manifest.json",dict(runs=runs,fixed=fixed,mode="numerical_observation_fixture_only",
        no_risk_experiment=True,P2_computed=False,driving_parameter_search=False,real_data_inputs=False))
    frozen={p.relative_to(batch).as_posix():sha(p) for folder in [batch/"runtime",batch/"inputs",batch/"official_source"] for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name!="stage_0_5_contract_analysis.py"}
    for name in ["isolation_policy.json","official_source_manifest.json","historical_source_manifest.json","preflight.json","data_isolation_preflight.json","displacement_branch_contract.json","queue_observation_contract.json","synthetic_queue_truth.json","micro_fixture_manifest.json"]:frozen[name]=sha(batch/name)
    plan=dict(result_id=RESULT_ID,mode="independent_measurement_contract_only",runs=runs,fixed=fixed,scientific_claim_eligible=False,
        ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,gate="pending_simulation_sample",protocol_lock_allowed=False,stage_1_1_allowed=False,
        limits=dict(max_runs=4,per_run_wall_s=120,batch_wall_s=1800,memory_bytes=2*1024**3,artifact_bytes=256*1024**2),
        stopper=dict(any_engineering_blocker_stops_all_following=True,exact_residual_or_bound_violation_m=1e-6,
            stopping_timing_unresolved="diagnostic warning/Pending, never exact Pass",expected_coordinate_transitions="not_evaluable, diagnostic warning",
            identity_clock_conservation_collision_teleport_resource_SHA_errors="blocker"),frozen_files=frozen,
        analysis_renderer="separate unfrozen descriptive packaging only; cannot change checked measurements or rules")
    write(batch/"experiment_plan.json",plan);(batch/"PLAN_SHA256").write_text(sha(batch/"experiment_plan.json")+"  experiment_plan.json\n",encoding="utf-8")
    write(batch/"execution_ledger.json",dict(plan_sha256=sha(batch/"experiment_plan.json"),closed=False,runs=[dict(run_id=r["run_id"],status="not_attempted") for r in runs]))
    print("B11_FROZEN "+sha(batch/"experiment_plan.json"),flush=True)


def read_plan(batch):
    from riskprop.stage_0_5_exploratory_response import verify_frozen
    digest=(batch/"PLAN_SHA256").read_text().split()[0]
    if sha(batch/"experiment_plan.json")!=digest:raise ValueError("micro plan SHA mismatch")
    plan=json.loads((batch/"experiment_plan.json").read_text(encoding="utf-8"));verify_frozen(batch,plan["frozen_files"])
    return plan


def worker(batch,run_id):
    from riskprop.stage_0_5_stopping_contract import audit_edge,AuditAccumulator
    from riskprop.stage_0_5_sumo import _sumo_binary,_ensure_traci_importable
    _ensure_traci_importable();import traci
    plan=read_plan(batch);spec=next(r for r in plan["runs"] if r["run_id"]==run_id);out=batch/"runs"/run_id
    if (out/"summary.json").exists():raise ValueError("no micro retries")
    audit=AuditAccumulator();previous={};departed=set();arrived=set();observations=0;initial=0;failure=None;conservation=0
    collision=set();teleports=set();old_stop_residuals=[];source_clock_errors=0;conn=None;settings={}
    command=[_sumo_binary(),"-c",str(batch/spec["config"]),"--no-step-log","true","--duration-log.disable","true","--error-log",str(out/"sumo_errors.log")]
    with (out/"micro_states.jsonl").open("w",encoding="utf-8") as raw:
        try:
            traci.start(command,label=run_id);conn=traci.getConnection(run_id)
            settings={k:conn.simulation.getOption(k) for k in ["step-method.ballistic","step-length","seed","threads","time-to-teleport"]}
            settings["sumo_version"]=conn.getVersion();settings["actual_action_step_s"]=conn.vehicletype.getActionStepLength("fixed")
            conn.simulation.saveState(str(out/"initial_runtime.xml"))
            echo=next(v.attrib for v in ET.parse(out/"initial_runtime.xml").getroot().iter("vType") if v.attrib["id"]=="fixed")
            settings["type_echo"]=echo
            settings["actual_type"]={key:getattr(conn.vehicletype,method)("fixed") for key,method in dict(tau="getTau",minGap="getMinGap",accel="getAccel",decel="getDecel",apparentDecel="getApparentDecel",emergencyDecel="getEmergencyDecel",sigma="getImperfection",length="getLength",maxSpeed="getMaxSpeed",speedFactor="getSpeedFactor",speedDev="getSpeedDeviation").items()}
            checks=[settings["step-method.ballistic"].lower() in ["1","true"],abs(float(settings["step-length"])-spec["step_s"])<1e-12,
                int(settings["seed"])==spec["seed"],int(settings["threads"])==1,abs(settings["actual_action_step_s"]-.1)<1e-12,
                abs(float(echo.get("sigmaStep","nan"))-1)<1e-12,
                all(abs(value-plan["fixed"][key])<1e-12 for key,value in settings["actual_type"].items())]
            settings["verified"]=all(checks)
            if not settings["verified"]:raise ValueError("micro runtime settings mismatch")
            for tick in range(1,round(spec["duration_s"]/spec["step_s"])+1):
                conn.simulationStep();now=conn.simulation.getTime()
                if abs(now-tick*spec["step_s"])>1e-9:source_clock_errors+=1;raise ValueError("runtime cadence")
                new=set(conn.simulation.getDepartedIDList());gone=set(conn.simulation.getArrivedIDList())
                if new&departed:raise ValueError("vehicle identity reused")
                departed|=new;arrived|=gone
                collision.update(conn.simulation.getCollidingVehiclesIDList());teleports.update(conn.simulation.getStartingTeleportIDList())
                ids=conn.vehicle.getIDList();conservation=max(conservation,abs(len(departed)-len(arrived)-len(ids)))
                if collision or teleports or conservation:raise ValueError("collision/teleport/conservation")
                for vid in ids:
                    row=dict(run_id=run_id,vehicle_id=vid,incarnation_id=f"{run_id}|{vid}|0",time_s=now,
                        edge_id=conn.vehicle.getRoadID(vid),lane_id=conn.vehicle.getLaneID(vid),position_m=conn.vehicle.getLanePosition(vid),
                        speed_mps=conn.vehicle.getSpeed(vid),reported_acceleration_mps2=conn.vehicle.getAcceleration(vid))
                    raw.write(json.dumps(row)+"\n");observations+=1
                    if vid in previous:
                        result=audit_edge(previous[vid],row,spec["step_s"]);audit.add(result)
                        if result["branch"]=="stopping_timing_unresolved":old_stop_residuals.append(result["old_trapezoid_residual_m"])
                        if result["anomaly"]:raise ValueError("independent displacement check anomaly")
                        if result["branch"]=="insufficient_observation":raise ValueError("observation identity/clock/coordinate quality")
                    else:initial+=1
                    previous[vid]=row
        except Exception as exc:failure=f"{type(exc).__name__}: {exc}"
        finally:
            if conn is not None:
                try:conn.close()
                except Exception:pass
    result=audit.summary();warnings=[]
    if result["branches"].get("stopping_timing_unresolved"):warnings.append("exact_stopping_equivalence_pending")
    if result["branches"].get("edge_or_lane_transition"):warnings.append("expected_coordinate_transition_not_evaluable")
    blockers=[failure] if failure else []
    write(out/"summary.json",dict(run_id=run_id,engineering_blockers=blockers,diagnostic_warnings=warnings,
        status="failed" if failure else "completed_with_diagnostic_warning" if warnings else "completed_valid",
        audit=result,runtime_settings=settings,observed_states=observations,first_observations_without_prior=initial,
        vehicles=len(departed),arrived=len(arrived),conservation_max_abs=conservation,collisions=list(collision),teleports=list(teleports),
        old_trapezoid_stop_residuals_m=old_stop_residuals,all_active_vehicles_observed=True,exact_stop_signed_trace_available=False,
        numerical_tolerance_m=1e-6,no_P2_calculation=True,scientific_claim_eligible=False,plan_sha256=sha(batch/"experiment_plan.json")))


def run(batch):
    from riskprop.stage_0_5_boundary_bottleneck import execute_commands
    plan=read_plan(batch);ledger=json.loads((batch/"execution_ledger.json").read_text())
    if ledger["closed"] or any(r["status"]!="not_attempted" for r in ledger["runs"]):raise PermissionError("no reopening micro batch")
    commands=[dict(run_id=r["run_id"],verify_files={str(batch/n):plan["frozen_files"][n] for n in [r["config"],r["network"],r["demand"]]},
        command=[sys.executable,"-S",str(Path(__file__)),"worker","--batch",str(batch),"--run-id",r["run_id"]]) for r in plan["runs"]]
    environment(batch);started=time.time();result=execute_commands(batch/"runs",commands,limits=plan["limits"])
    write(batch/"execution_ledger.json",dict(plan_sha256=sha(batch/"experiment_plan.json"),closed=True,runs=result["runs"],stop_reason=result["stop_reason"] or "all4 declared micro fixtures completed",elapsed_wall_s=time.time()-started))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("command",choices=["prepare","tests","freeze","run","worker","finalize"])
    p.add_argument("--batch",type=Path,required=True);p.add_argument("--run-id");a=p.parse_args();batch=a.batch.resolve()
    audit=None
    if a.command!="prepare":
        if not Path(__file__).resolve().is_relative_to(batch/"runtime"):raise PermissionError("use capsule entrypoint")
        from riskprop.stage_0_5_b1_isolation import install_guard
        audit=install_guard(batch)
    try:
        if a.command=="prepare":prepare(batch)
        elif a.command=="tests":tests(batch)
        elif a.command=="freeze":freeze(batch)
        elif a.command=="run":run(batch)
        elif a.command=="worker":worker(batch,a.run_id)
        else:
            from riskprop.stage_0_5_contract_analysis import finalize
            finalize(batch)
    finally:
        if audit is not None:
            folder=batch/"access_logs";folder.mkdir(exist_ok=True)
            write(folder/f"{a.command}_{a.run_id or time.time_ns()}.json",audit)
            if audit["denied"]:raise PermissionError("unexpected capsule denial")
