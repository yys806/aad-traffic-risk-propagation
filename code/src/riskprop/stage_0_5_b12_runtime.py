"""Controlled B1.2 integration and conditional mechanism execution, independent of B1."""
from __future__ import annotations
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .stage_0_5_b12_observation import QUEUE_CONFIG, VERSION
from .stage_0_5_b12_network import coordinate_support
from .stage_0_5_boundary_bottleneck import _copy_runtime, execute_commands, arrival_times, network_contract
from .stage_0_5_sumo import _sumo_binary, _netconvert_binary, NETWORK_DESIGN_CANDIDATE
from .stage_0_5_b1_isolation import read_reference, WINDOWS

RESULT_ID="RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2"
FIXED=dict(maxSpeed=27.78,speedFactor=1.,speedDev=0.,carFollowModel="Krauss",tau=1.,minGap=2.5,
           accel=2.6,decel=4.5,apparentDecel=4.5,emergencyDecel=9.,sigma=.5,
           actionStepLength=.1,sigmaStep=1.,laneChangeModel="LC2013")
BOUNDARIES=dict(A="uniform/open",B="30s arrival blocks compressed to first15s; same fleet/order/count",
                C="23.8green/6.2yellow/30red at hwy_j2; artificial pressure only",
                D="main_2 two lanes; main_1 lane2 must change; open downstream")
SCIENCE=dict(gate="pending_simulation_sample",scientific_claim_eligible=False,
             ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,
             protocol_lock_allowed=False,stage_1_1_allowed=False,
             tolerances="Tolerance Not Yet Justified",energy_distance_upper_bound="Not Identifiable",
             local_formal_p2="Unresolved")


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def environment(batch):
    (batch/"runtime_cache/tmp").mkdir(parents=True,exist_ok=True)
    (batch/"test_tmp").mkdir(exist_ok=True)
    os.environ.update(AAD_B1_CAPSULE=str(batch),PYTHONPATH=str(batch/"runtime/code/src"),
                      PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONPYCACHEPREFIX=str(batch/"runtime_cache/pycache"),
                      MPLCONFIGDIR=str(batch/"runtime_cache/matplotlib"),
                      TEMP=str(batch/"runtime_cache/tmp"),TMP=str(batch/"runtime_cache/tmp"))


def prepare(repo,batch):
    if batch.exists():raise ValueError("new independent B1.2 directory required")
    (batch/"inputs").mkdir(parents=True);(batch/"runs").mkdir()
    source=repo/"evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1"
    manifest=read(source/"manifest.json")
    name="real_reference_summary.json"
    digest=next(f["sha256"] for f in manifest["files"] if f["path"]==name)
    write(batch/"source_staging_manifest.json",dict(source=str(source/name),sha256=digest,
          role="calibration",kind="two_window_aggregate",declared_before_read=True,
          purpose="Reuse approved two-window projection and A+ fleet only; no traffic trajectory/event table"))
    if sha(source/name)!=digest:raise PermissionError("reference SHA mismatch")
    shutil.copyfile(source/name,batch/"inputs/calibration_reference.json")
    binding=dict(calibration_reference=dict(path="calibration_reference.json",sha256=digest,
                                           role="calibration",kind="two_window_aggregate"))
    read_reference(batch/"inputs",binding,"calibration_reference",role="calibration")
    write(batch/"source_manifest.json",binding)
    _copy_runtime(repo,batch)
    # New module closure plus the old independent analytic/synthetic tests.
    for name in ["stage_0_5_b12_runtime","stage_0_5_b12_observation","stage_0_5_b12_network",
                 "stage_0_5_b12_worker","stage_0_5_stopping_observability","stage_0_5_stopping_contract",
                 "stage_0_5_queue_contract","stage_0_5_contract_fixtures"]:
        p=repo/"code/src/riskprop"/(name+".py")
        if p.exists():shutil.copyfile(p,batch/"runtime/code/src/riskprop"/p.name)
    for name in ["test_stage_0_5_b12_integration.py","test_stage_0_5_stopping_observability.py",
                 "test_stage_0_5_stopping_contract.py","test_stage_0_5_queue_contract.py"]:
        shutil.copyfile(repo/"code/tests"/name,batch/"runtime/code/tests"/name)
    shutil.copyfile(repo/"code/scripts/run_stage_0_5_boundary_revalidation.py",batch/"runtime/code/scripts/run_stage_0_5_boundary_revalidation.py")
    dependencies=[];links=batch/"dependency_links";links.mkdir()
    for name in ["numpy","pandas","pyarrow","psutil","matplotlib","pytest","packaging","dateutil"]:__import__(name)
    import _winapi
    for name,module in list(sys.modules.items()):
        if "." in name or not getattr(module,"__file__",None):continue
        p=Path(module.__file__).resolve()
        if "site-packages" not in p.parts or p.is_relative_to(Path(sys.prefix).resolve()):continue
        if p.name=="__init__.py":
            targets=[p.parent]+list(p.parent.parent.glob(name.replace("_","-")+"-*.dist-info"))
            if (p.parent.parent/(name+".libs")).is_dir():targets.append(p.parent.parent/(name+".libs"))
            for target in targets:
                link=links/target.name
                if not link.exists():_winapi.CreateJunction(str(target),str(link))
                dependencies.append(str(target))
        else:shutil.copyfile(p,links/p.name)
    write(batch/"isolation_policy.json",dict(runtime_read_roots=[str(Path(sys.prefix).resolve()),
          str(Path(_sumo_binary()).resolve().parent.parent),os.environ.get("WINDIR","C:/Windows")]+dependencies,
          executables=[sys.executable,_sumo_binary(),_netconvert_binary()],os_complete_monitoring=False,
          real_inputs="SHA-bound two calibration-window aggregate only",python_no_site_required=True))
    write(batch/"preparation_manifest.json",dict(base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
          historical_evidence_tree=subprocess.check_output(["git","rev-parse","HEAD:evidence/results"],cwd=repo,text=True).strip(),
          source_manifest_sha256=sha(batch/"source_manifest.json"),capsule=str(batch),created_epoch=time.time()))
    print("B12_PREPARED",flush=True)


def tests(batch):
    environment(batch)
    probe=subprocess.run([sys.executable,"-S",str(batch/"runtime/code/scripts/b1_guard_probe.py"),str(batch)],capture_output=True,text=True,timeout=30)
    if probe.returncode:raise ValueError("isolation rejection probe failed")
    names=[p.name for p in (batch/"runtime/code/tests").glob("test_*.py")]
    cmd=[sys.executable,"-S",str(batch/"runtime/code/scripts/b1_test_entry.py"),
         *[str(batch/"runtime/code/tests"/n) for n in sorted(names)],"-q","-c",str(batch/"runtime/code/pytest.ini"),
         "--rootdir",str(batch/"runtime/code"),"--basetemp",str(batch/"test_tmp"/str(time.time_ns())),
         "-o",f"cache_dir={batch/'runtime_cache/pytest'}"]
    r=subprocess.run(cmd,cwd=batch/"runtime/code",capture_output=True,text=True,timeout=180)
    audit=read(batch/"preflight_test_access_audit.json")
    write(batch/"synthetic_test_record.json",dict(command=cmd,returncode=r.returncode,output=r.stdout+r.stderr,
          tests={n:sha(batch/"runtime/code/tests"/n) for n in names},access_audit=audit))
    passed=r.returncode==0 and not audit["denied"]
    write(batch/"data_isolation_preflight.json",dict(passed=passed,source_manifest=read(batch/"source_manifest.json"),
          accessible_windows=list(WINDOWS),validation_rows_materialised=0,old_C_states_read=False,
          historical_whole_source_read=False,guard_probe=read(batch/"guard_probe_result.json"),
          no_site=True,unexpected_test_denials=len(audit["denied"]),os_complete_monitoring=False,native_access_monitored=False))
    write(batch/"execution_guard_audit.json",dict(passed=passed,regression="B1 synthetic actual subprocess supervisor tests",
          tested=["blocker","failure","timeout","memory","disk","SHA","no_following_launch","cancelled"],
          test_record_sha256=sha(batch/"synthetic_test_record.json")))
    print(r.stdout+r.stderr,flush=True)
    if not passed:raise ValueError("B12 synthetic preflight failed")


def build_network(root,condition,scale=1.):
    root.mkdir(parents=True,exist_ok=True);spec=copy.deepcopy(NETWORK_DESIGN_CANDIDATE)
    nodes=ET.Element("nodes");edges=ET.Element("edges")
    for n in spec["nodes"]:
        ET.SubElement(nodes,"node",dict(id=n["id"],x=str(n["x"]*scale),y=str(n["y"]*scale),
            type="traffic_light" if condition=="C" and n["id"]=="hwy_j2" else "priority"))
    for e in spec["edges"]:
        ET.SubElement(edges,"edge",dict(id=e["id"],**{"from":e["from"],"to":e["to"]},priority=str(e["priority"]),
            numLanes=str(2 if condition=="D" and e["id"]=="main_2" else e["lanes"]),speed=str(e["speed_mps"])))
    ET.ElementTree(nodes).write(root/"nodes.nod.xml");ET.ElementTree(edges).write(root/"edges.edg.xml")
    path=root/"b12.net.xml"
    cmd=[_netconvert_binary(),"-n",str(root/"nodes.nod.xml"),"-e",str(root/"edges.edg.xml"),"-o",str(path),"--no-turnarounds","true"]
    if condition=="D":
        cc=ET.Element("connections")
        for a,b,n in [("main_0","main_1",3),("main_1","main_2",2),("onramp","main_1",1),("main_1","offramp",1)]:
            for i in range(n):ET.SubElement(cc,"connection",dict(**{"from":a,"to":b},fromLane=str(i),toLane=str(i)))
        ET.ElementTree(cc).write(root/"connections.con.xml");cmd += ["--connection-files",str(root/"connections.con.xml")]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    (root/"build.log").write_text(r.stdout+r.stderr,encoding="utf-8")
    if r.returncode:raise ValueError("netconvert failed")
    if condition=="C":
        tree=ET.parse(path);logic=next(l for l in tree.getroot().findall("tlLogic") if l.attrib["id"]=="hwy_j2")
        n=len(logic.find("phase").attrib["state"])
        logic.attrib.update(type="static",programID="b12_supply_v1",offset="0")
        for child in list(logic):logic.remove(child)
        phases=[(23.8,"G"),(6.2,"y"),(30.,"r")] if scale==1 else [(5.,"G"),(6.2,"y"),(48.8,"r")]
        for duration,state in phases:ET.SubElement(logic,"phase",dict(duration=str(duration),state=state*n))
        tree.write(path,encoding="utf-8",xml_declaration=True)
    return path


def make_config(batch,run_id,network,demand,duration,seed):
    p=batch/"inputs"/(run_id+".sumocfg")
    p.write_text(f'<configuration><input><net-file value="{Path(network).relative_to(batch/"inputs").as_posix()}"/>'
                 f'<route-files value="{Path(demand).relative_to(batch/"inputs").as_posix()}"/></input>'
                 f'<time><begin value="0"/><end value="{duration}"/><step-length value="0.05"/></time>'
                 f'<processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/>'
                 f'<collision.action value="warn"/></processing><seed value="{seed}"/></configuration>',encoding="utf-8")
    return p


def frozen_files(batch):
    return {p.relative_to(batch).as_posix():sha(p) for folder in [batch/"inputs",batch/"runtime"] for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def freeze_integration(batch):
    if (batch/"integration_plan.json").exists():raise ValueError("integration plan immutable")
    if not all(read(batch/n)["passed"] for n in ["data_isolation_preflight.json","execution_guard_audit.json"]):raise PermissionError("preflight")
    ref=read_reference(batch/"inputs",read(batch/"source_manifest.json"),"calibration_reference",role="calibration")
    runs=[];networks={}
    for condition,scale,count in [("C",.2,150),("D",1.,18)]:
        run_id="b12_integration_"+condition
        net=build_network(batch/"inputs"/run_id,condition,scale)
        support=coordinate_support(net)
        if not support["coordinate_verified"]:raise ValueError(json.dumps(support["errors"]))
        networks[condition]=support
        routes=ET.Element("routes")
        for i,f in enumerate(ref["fleet"]):ET.SubElement(routes,"vType",dict(id=f"t{i}",vClass=f["vClass"],length=str(f["length_m"]),**{k:str(v) for k,v in FIXED.items()}))
        ET.SubElement(routes,"route",dict(id="through",edges="main_0 main_1 main_2"))
        for i in range(count):
            ET.SubElement(routes,"vehicle",dict(id=f"v{i:05d}",type="t1",route="through",depart=f'{.1+i*(.3 if condition=="C" else 1.):.1f}',
                          departLane=str(i%3 if condition=="C" else 2),departPos="base",departSpeed="max"))
        demand=batch/"inputs"/(run_id+".rou.xml");ET.ElementTree(routes).write(demand,encoding="utf-8",xml_declaration=True)
        config=make_config(batch,run_id,net,demand,60,20261019)
        local=dict(edge="main_1",start_m=10.,end_m=40.,lanes=3,lane_km=.09) if condition=="C" else dict(edge="main_1",start_m=50.,end_m=250.,lanes=3,lane_km=.6)
        runs.append(dict(run_id=run_id,condition=condition,network=net.relative_to(batch).as_posix(),config=config.relative_to(batch).as_posix(),
                         demand=demand.relative_to(batch).as_posix(),duration_s=60.,seed=20261019,local_space=local,
                         expected=dict(conservation=True,local_crossings=True,edge_transition=True,junction=True,
                                       all_three_lanes=True,queue_to_inlet=condition=="C",mandatory_lane_change=condition=="D",downstream_exit=True)))
    # Zero-step runtime echo check has no inserted vehicles and consumes no
    # traffic fixture. Catch unsupported options BEFORE freezing/running traffic.
    from .stage_0_5_sumo import _ensure_traci_importable
    from .stage_0_5_b12_worker import runtime_settings
    _ensure_traci_importable();import traci
    empty=[]
    for spec in runs:
        out=batch/"empty_prechecks"/spec["run_id"];out.mkdir(parents=True,exist_ok=True)
        label="empty_"+spec["condition"]
        traci.start([_sumo_binary(),"-c",str(batch/spec["config"]),"--no-step-log","true"],label=label)
        conn=traci.getConnection(label)
        try:
            settings=runtime_settings(conn,dict(fleet=ref["fleet"]),spec,out)
            settings.update(vehicles_at_check=len(conn.vehicle.getIDList()),simulation_time_s=conn.simulation.getTime())
            write(out/"runtime_echo.json",settings);empty.append(dict(condition=spec["condition"],**settings))
        finally:conn.close()
        if not settings["verified"]:raise ValueError("empty-runtime settings failed; inspect runtime_echo.json")
    write(batch/"empty_network_prechecks.json",empty)
    write(batch/"queue_integration_contract.json",dict(version=VERSION,config=QUEUE_CONFIG,main_method="lane_path_vehicle_graph",
          auxiliary="lane-separated grid",historical_sensitivity="pooled grid only; cannot override graph",
          lane_change="reset any component containing a changed member",missing_frame="reset; no interpolation",
          entry_support="persistent anchored connected component AND actual pending AND independently blocked assigned insertion lane",
          not_evaluable_policy="legal coordinate changes retained; critical coordinate support/identity/time/control/config mismatch blocks main admission",
          science="Candidate software behavior != Actual SUMO integration verified != Scientific traffic validity",
          threshold_adaptation_allowed=False))
    write(batch/"numerical_admission_policy.json",dict(version=VERSION,policy="B researcher approved for B1.2 engineering only",tolerance_m=1e-6,
          exact="positive decision endpoint; nondecision v0+a_start*h including negative; stationary zero",
          bounded="decision v1=0 with v0>0; 0<=dx<=.5*v0*h; never Exact Pass",
          legal_not_evaluable=["edge transition","lane change"],unknown_action="blocker; never treated nondecision",
          blockers=["identity","clock","control unknown","config","exact residual","bounded range","interface inconsistency"],
          arbitrary_unevaluable_fraction_limit=None,critical_location_policy="Evidence Insufficient; do not qualify mechanism if its essential position/continuity is unsupported"))
    write(batch/"coordinate_support_audit.json",dict(networks=networks,runtime_crosscheck_required=True,
          no_simple_normal_edge_sum=True,physical_world_precision="Unknown"))
    plan=dict(result_id=RESULT_ID,version="b12-integration-v1",mode="engineering_integration_fixture_only",runs=runs,fleet=ref["fleet"],
              fixed=FIXED,queue_config=QUEUE_CONFIG,**SCIENCE,
              limits=dict(max_runs=2,per_run_wall_s=180,batch_wall_s=600,memory_bytes=3*1024**3,artifact_bytes=1024**3),
              max_fixture_duration_s=60.,fixture_budget_cannot_expand=True,
              fixture_responsibilities="C compressed corridor: queue, inlet, pending, scope and crossing; D full geometry: mandatory merge, junctions and exit",
              frozen_files=frozen_files(batch))
    for name in ["source_manifest.json","isolation_policy.json","data_isolation_preflight.json","execution_guard_audit.json",
                 "numerical_admission_policy.json","queue_integration_contract.json","coordinate_support_audit.json"]:
        plan["frozen_files"][name]=sha(batch/name)
    write(batch/"integration_plan.json",plan)
    (batch/"INTEGRATION_PLAN_SHA256").write_text(sha(batch/"integration_plan.json")+"  integration_plan.json\n",encoding="utf-8")
    write(batch/"integration_ledger.json",dict(closed=False,runs=[dict(run_id=r["run_id"],status="not_attempted") for r in runs]))
    print("B12_INTEGRATION_FROZEN "+sha(batch/"integration_plan.json"),flush=True)


def load_plan(batch,name):
    from .stage_0_5_exploratory_response import verify_frozen
    sumfile="INTEGRATION_PLAN_SHA256" if name=="integration_plan.json" else "PLAN_SHA256"
    if sha(batch/name)!=(batch/sumfile).read_text().split()[0]:raise PermissionError("plan SHA mismatch")
    plan=read(batch/name);verify_frozen(batch,plan["frozen_files"])
    return plan


def run_integration(batch):
    plan=load_plan(batch,"integration_plan.json");ledger=read(batch/"integration_ledger.json")
    if ledger["closed"] or any(r["status"]!="not_attempted" for r in ledger["runs"]):raise PermissionError("no fixture rerun")
    commands=[dict(run_id=r["run_id"],command=[sys.executable,"-S",str(batch/"runtime/code/scripts/run_stage_0_5_boundary_revalidation.py"),
                  "worker","--batch",str(batch),"--run-id",r["run_id"],"--plan","integration_plan.json"],
                  verify_files={str(batch/n):plan["frozen_files"][n] for n in [r["network"],r["config"],r["demand"]]}) for r in plan["runs"]]
    result=execute_commands(batch/"runs",commands,limits=plan["limits"])
    write(batch/"integration_ledger.json",dict(result,closed=True,plan_sha256=sha(batch/"integration_plan.json")))


def admit(batch):
    plan=load_plan(batch,"integration_plan.json");ledger=read(batch/"integration_ledger.json");checks=[]
    for spec,entry in zip(plan["runs"],ledger["runs"]):
        path=batch/"runs"/entry["run_id"]/"summary.json"
        s=read(path) if path.exists() else {}
        def check(name,passed,evidence):checks.append(dict(run_id=spec["run_id"],check=name,passed=bool(passed),evidence=evidence))
        check("completed_without_engineering_blocker",entry["status"]=="completed_valid" and not s.get("engineering_blockers"),entry)
        check("full_duration",s.get("observed_s")==60.,s.get("observed_s"))
        check("numerical_layered_admission",s.get("numerical",{}).get("all_adjacent_edges",0)>0 and not s.get("numerical",{}).get("blockers",{"missing":1}),
              {k:s.get("numerical",{}).get(k) for k in ["all_adjacent_edges","classifications","max_abs_residual_m","blockers"]})
        check("local_entry_and_exit_measured",s.get("local_entered",0)>0 and s.get("local_exited",0)>0,[s.get("local_entered"),s.get("local_exited")])
        check("cross_edge_and_junction_actual",s.get("coordinate_crosschecks",{}).get("cross_edge",0)>0 and s.get("junction_states",0)>0,s.get("coordinate_crosschecks"))
        check("downstream_exit",s.get("actual_exited",0)>0,s.get("actual_exited"))
        check("physical_gap",s.get("gap_checks",0)>0 and s.get("max_gap_residual_m",1)>0-1e-10 and s.get("max_gap_residual_m",1)<=1e-6,s.get("max_gap_residual_m"))
        if spec["condition"]=="C":
            check("internal_queue",s.get("first_times",{}).get("internal_queue") is not None,s.get("first_times"))
            check("inlet_and_physical_pending",s.get("first_times",{}).get("supported_spillback") is not None,s.get("queue_state_counts"))
        if spec["condition"]=="D":check("mandatory_lane_change",s.get("lane_changes",0)>0,s.get("lane_changes"))
    allowed=all(c["passed"] for c in checks) and ledger["closed"] and read(batch/"data_isolation_preflight.json")["passed"]
    record=dict(B1_2_MAIN_MATRIX_ALLOWED=allowed,integration_plan_sha256=sha(batch/"integration_plan.json"),
                checks=checks,failed_checks=[c for c in checks if not c["passed"]],fixture_budget_used=sum(r["status"]!="not_attempted" for r in ledger["runs"]),
                fixture_budget_max=2,fixture_duration_max_s=60,extra_fixture_allowed=False,
                no_scientific_threshold_approval=True,limited_description_if_blocked="Only completed integration fixture observations; no A/B/C/D mechanism inference",
                **SCIENCE)
    write(batch/"observability_integration_audit.json",record)
    write(batch/"queue_integration_test_matrix.json",dict(checks=checks,candidate_software_behavior="Verified by synthetic tests",
          actual_SUMO_integration_verified=allowed,scientific_traffic_validity="Not Established"))
    write(batch/"local_global_accounting_audit.json",dict(passed=all(c["passed"] for c in checks if c["check"] in ["local_entry_and_exit_measured","completed_without_engineering_blocker"]),
          global_accounting="departed identities minus arrived identities == all present identities at every internal step",
          local="independent consecutive local identity-set enters/exits; causes from positions; not global insertion flux",
          density="only observed on-road vehicles / declared fixed lane-km",external="scheduled executable due - actual inserted; independently checked against TraCI pending",
          raw_evidence="runs/*/traffic_frames.csv + internal_states.parquet",checks=[c for c in checks if c["check"]=="local_entry_and_exit_measured"]))
    print(json.dumps(dict(B1_2_MAIN_MATRIX_ALLOWED=allowed,failed_checks=record["failed_checks"])),flush=True)


def freeze_main(batch):
    import numpy as np
    if (batch/"experiment_plan.json").exists():raise ValueError("immutable main plan")
    admission=read(batch/"observability_integration_audit.json")
    if not admission["B1_2_MAIN_MATRIX_ALLOWED"]:raise PermissionError("B1.2 main matrix not admitted")
    load_plan(batch,"integration_plan.json")
    ref=read_reference(batch/"inputs",read(batch/"source_manifest.json"),"calibration_reference",role="calibration")
    networks={};prechecks=[]
    for condition in ["A","C","D"]:
        path=build_network(batch/"inputs"/("main_"+condition),condition)
        support=coordinate_support(path);static=network_contract(path)
        if not support["coordinate_verified"]:raise ValueError("main coordinate support")
        networks[condition]=dict(path=path.relative_to(batch).as_posix(),version="b12_main_"+condition+"_v1",sha256=sha(path),static=static,coordinate=support)
        p=subprocess.run([_sumo_binary(),"-n",str(path),"--end",".1","--no-step-log","true"],capture_output=True,text=True,timeout=30)
        prechecks.append(dict(condition=condition,exit_code=p.returncode,empty_simulated_s=.1,stdout=p.stdout,stderr=p.stderr))
        if p.returncode:raise ValueError("empty network precheck")
    networks["B"]=copy.deepcopy(networks["A"])
    for cond in ["B","C","D"]:
        if networks[cond]["static"]["points"]!=networks["A"]["static"]["points"]:raise ValueError("common local geometry changed")
    runs=[]
    for phase,seed in [("phase1",20261019),("phase2",20261020)]:
        uniform=arrival_times(1648,600,"uniform");rng=np.random.default_rng(seed)
        classes=rng.choice(3,size=len(uniform),p=[f["share"] for f in ref["fleet"]]).tolist()
        for kind in ["uniform","platoon"]:
            routes=ET.Element("routes")
            for i,f in enumerate(ref["fleet"]):ET.SubElement(routes,"vType",dict(id=f"t{i}",vClass=f["vClass"],length=str(f["length_m"]),**{k:str(v) for k,v in FIXED.items()}))
            ET.SubElement(routes,"route",dict(id="through",edges="main_0 main_1 main_2"))
            for i,(t,cls) in enumerate(zip(arrival_times(1648,600,kind),classes)):
                ET.SubElement(routes,"vehicle",dict(id=f"v{i:05d}",type=f"t{cls}",route="through",depart=f"{t:.1f}",departLane=str(i%3),departPos="base",departSpeed="max"))
            demand=batch/"inputs"/f"b12_{kind}_{seed}.rou.xml";ET.ElementTree(routes).write(demand,encoding="utf-8",xml_declaration=True)
        for cond in ["A","B","C","D"]:
            run_id=f"b12_{cond}_s{seed}";kind="platoon" if cond=="B" else "uniform"
            demand=batch/"inputs"/f"b12_{kind}_{seed}.rou.xml";net=batch/networks[cond]["path"]
            cfg=make_config(batch,run_id,net,demand,600,seed)
            runs.append(dict(run_id=run_id,condition=cond,phase=phase,seed=seed,duration_s=600.,network=net.relative_to(batch).as_posix(),
                             demand=demand.relative_to(batch).as_posix(),config=cfg.relative_to(batch).as_posix(),planned_vehicles=len(uniform),
                             local_space=dict(edge="main_1",start_m=50.,end_m=250.,lanes=3,lane_km=.6),
                             network_hash=sha(net),demand_hash=sha(demand),fleet_hash=hashlib.sha256(json.dumps(classes).encode()).hexdigest(),
                             boundary_hash=hashlib.sha256(BOUNDARIES[cond].encode()).hexdigest()))
    write(batch/"network_variant_manifest.json",dict(networks=networks,empty_dynamic_prechecks=prechecks,common_observation_geometry=True,capacity_matched=False))
    write(batch/"boundary_condition_manifest.json",dict(boundaries=BOUNDARIES,signal_is_artificial=True,real_us101_geometry_reproduced=False))
    budget=dict(max_runs=8,per_run_wall_s=600,batch_wall_s=7200,memory_bytes=6*1024**3,artifact_bytes=4*1024**3)
    write(batch/"runtime_budget_audit.json",dict(limits=budget,estimate_per_run_wall_s=dict(freeflow=150,constrained=450),
          basis="Historical B1 freeflow71-93s/constrained178s fullP2; B1.2 audits all .05s edges and writes internal states; provision 2.5x constrained",
          expected_output_MB_per_run=dict(freeflow=100,constrained=300),expected_tree_memory_GiB=4.,
          full_P2="Included in worker hard wall and memory caps",queue="1Hz graph, at most823 vehicles, 600 snapshots; budget30s within per-run cap",
          planned_total_wall_s=2400,task_max_wall_s=7200,no_parallel_workers=True,hard_cap_not_performance_guarantee=True))
    plan=dict(result_id=RESULT_ID,version="b12-main-v1",mode="exploratory_diagnostic_only",runs=runs,fixed=FIXED,fleet=ref["fleet"],
              queue_config=QUEUE_CONFIG,networks=networks,main_flow_veh_h_lane=1648.,limits=budget,**SCIENCE,
              authorization="Independent B1.2 only; not old B1 completion",integration_admission_sha256=sha(batch/"observability_integration_audit.json"),
              stop_rules=dict(any_engineering_blocker_stops_following=True,reasonable_queues_not_errors=True,
                              unsupported_queue="Evidence Insufficient; retain descriptions; do not claim unsupported mechanism qualification",
                              core_logic_change="stop batch, preserve ledger, new plan version; no automatic retry"),
              startup_sensitivity_starts_s=[0,60,120,300],scientific_warmup_s=None,frozen_files=frozen_files(batch))
    for name in ["source_manifest.json","isolation_policy.json","observability_integration_audit.json","numerical_admission_policy.json",
                 "queue_integration_contract.json","network_variant_manifest.json","boundary_condition_manifest.json","runtime_budget_audit.json"]:
        plan["frozen_files"][name]=sha(batch/name)
    write(batch/"experiment_plan.json",plan);(batch/"PLAN_SHA256").write_text(sha(batch/"experiment_plan.json")+"  experiment_plan.json\n",encoding="utf-8")
    write(batch/"execution_ledger.json",dict(closed=False,started_epoch=None,plan_sha256=sha(batch/"experiment_plan.json"),runs=[dict(run_id=r["run_id"],status="not_attempted") for r in runs]))
    print("B12_MAIN_FROZEN "+sha(batch/"experiment_plan.json"),flush=True)


def execute_phase(batch,phase):
    plan=load_plan(batch,"experiment_plan.json");ledger=read(batch/"execution_ledger.json")
    if ledger["closed"]:raise PermissionError("closed main plan")
    if phase=="phase2" and not read(batch/"phase1_checkpoint.json")["phase2_allowed"]:raise PermissionError("checkpoint did not admit phase2")
    specs=[r for r in plan["runs"] if r["phase"]==phase]
    if any(next(e for e in ledger["runs"] if e["run_id"]==r["run_id"])["status"]!="not_attempted" for r in specs):raise PermissionError("no retry")
    if ledger["started_epoch"] is None:ledger["started_epoch"]=time.time()
    limits=dict(plan["limits"]);limits["batch_wall_s"]-=time.time()-ledger["started_epoch"]
    commands=[dict(run_id=r["run_id"],command=[sys.executable,"-S",str(batch/"runtime/code/scripts/run_stage_0_5_boundary_revalidation.py"),"worker", "--batch",str(batch),"--run-id",r["run_id"],"--plan","experiment_plan.json"],
                   verify_files={str(batch/n):plan["frozen_files"][n] for n in [r["network"],r["config"],r["demand"]]}) for r in specs]
    result=execute_commands(batch/"runs",commands,limits=limits)
    for row in result["runs"]:next(e for e in ledger["runs"] if e["run_id"]==row["run_id"]).update(row)
    ledger.update(elapsed_wall_s=time.time()-ledger["started_epoch"],stop_reason=result["stop_reason"])
    if result["stop_reason"] or phase=="phase2":ledger["closed"]=True
    write(batch/"execution_ledger.json",ledger)


def checkpoint(batch):
    plan=load_plan(batch,"experiment_plan.json");ledger=read(batch/"execution_ledger.json")
    first=ledger["runs"][:4];summaries=[]
    for r in first:
        p=batch/"runs"/r["run_id"]/"summary.json"
        if p.exists():summaries.append(read(p))
    checks=dict(all_four_completed=all(r["status"] in ["completed_valid","completed_with_diagnostic_warning"] for r in first),
                no_measurement_blocker=len(summaries)==4 and all(not s["engineering_blockers"] for s in summaries),
                data_isolation=read(batch/"data_isolation_preflight.json")["passed"],
                shared_observation_support=read(batch/"network_variant_manifest.json")["common_observation_geometry"],
                resources_remaining=plan["limits"]["batch_wall_s"]-ledger["elapsed_wall_s"]>=2400,
                mechanism_evaluable=any(s.get("first_times",{}).get("internal_queue") is not None for s in summaries))
    allowed=all(checks.values()) and not ledger["closed"]
    write(batch/"phase1_checkpoint.json",dict(phase2_allowed=allowed,checks=checks,plan_sha256=sha(batch/"experiment_plan.json"),
          first_batch=first,configuration_unchanged=True,scientific_claim_eligible=False))
    if not allowed:ledger.update(closed=True,stop_reason=ledger.get("stop_reason") or "phase2 checkpoint not admitted");write(batch/"execution_ledger.json",ledger)
    print(json.dumps(dict(phase2_allowed=allowed,checks=checks)),flush=True)


def dispatch(repo,batch,command,run_id=None,plan_name="integration_plan.json"):
    if command=="prepare":return prepare(repo,batch)
    environment(batch)
    if command=="tests":return tests(batch)
    if command=="freeze-integration":return freeze_integration(batch)
    if command=="integration":return run_integration(batch)
    if command=="admit":return admit(batch)
    if command=="freeze-main":return freeze_main(batch)
    if command in ["phase1","phase2"]:return execute_phase(batch,command)
    if command=="checkpoint":return checkpoint(batch)
    if command=="worker":
        from .stage_0_5_b12_worker import run_worker
        return run_worker(batch,run_id,plan_name)
    raise ValueError("phase not implemented or not admitted: "+command)
