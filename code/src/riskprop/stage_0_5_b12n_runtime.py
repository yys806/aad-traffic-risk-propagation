"""B1.2-N: <=3 micro probes + separately frozen C/D integration, no main matrix."""
from __future__ import annotations
import ast
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .stage_0_5_boundary_bottleneck import _copy_runtime,execute_commands
from .stage_0_5_b12_runtime import FIXED,SCIENCE,environment
from .stage_0_5_b12_observation import QUEUE_CONFIG
from .stage_0_5_near_zero_observability import VERSION,SOURCE_PROOF_KEYS
from .stage_0_5_sumo import _sumo_binary,_netconvert_binary

RESULT_ID="RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1"
MODE="engineering_observability_and_integration_only"
HISTORY_NAMES=["near_zero_source_audit.json","numerical_branch_coverage.json","queue_integration_test_matrix.json",
               "coordinate_support_audit.json","local_global_accounting_audit.json","execution_ledger.json",
               "researcher_decision_matrix.json","audit.json","experiment_plan.json","engineering_input_bundle.json"]


def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def source_contract(batch):
    root=batch/"official_source";manifest={**read(root/"source_manifest.json"),**read(root/"additional_source_manifest.json"),**read(root/"friend_source_manifest.json")}
    for name,e in manifest.items():
        if sha(root/name)!=e["sha256"]:raise ValueError("official source SHA mismatch")
    for name in ["microsim_MSLaneChanger.cpp","microsim_MSLaneChangerSublane.cpp"]:
        if "myStopDist" in (root/name).read_text(encoding="utf-8"):raise ValueError("friend class stop-distance mutation needs audit")
    patterns={
        "microsim_MSVehicle.cpp":["myStopDist(std::numeric_limits<double>::max())","planMoveInternal(t, ahead, myLFLinkLanes, myStopDist", "newStopDist = std::numeric_limits<double>::max()", "newStopDist = stopDist", "vSafe = getSpeed() + ACCEL2SPEED(myAcceleration)", "fabs(vNext) < NUMERICAL_EPS_SPEED", "vNext = processTraCISpeedControl", "updateState(vNext)", "deltaPos = getDeltaPos", "myAcceleration = SPEED2ACCEL(MAX2(vNext", "myState.mySpeed = MAX2(vNext", "myStopDist = 0;"],
        "microsim_MSBaseVehicle.h":["bool hasStops() const", "return !myStops.empty()"],
        "microsim_MSBaseVehicle.cpp":["MSBaseVehicle::getNextStop() const", "return myStops.front()", "MSBaseVehicle::getPrefixedParameter"],
        "libsumo_Vehicle.cpp":["Vehicle::getStops(","if (!stop.pars.collision)","Vehicle::getDrivingDistance(","Vehicle::getStopState("],
        "src_microsim_cfmodels_MSCFModel.cpp":["MSCFModel::finalizeSpeed(","veh->processNextStop(vPos)"],
        "config.h.cmake":["#define NUMERICAL_EPS 0.001","#define POSITION_EPS 0.1"],
        "utils_common_SUMOTime.h":["#define TS"],
        "tools_traci__vehicle.py":["def getStops(self, vehID, limit=0)"]}
    lines={}
    for name,needles in patterns.items():
        text=(root/name).read_text(encoding="utf-8").splitlines();lines[name]={}
        for needle in needles:
            found=[i+1 for i,line in enumerate(text) if needle in line]
            if not found:raise ValueError("source contract needle missing: "+needle)
            lines[name][needle]=found
    source=(root/"microsim_MSVehicle.cpp").read_text(encoding="utf-8").splitlines()
    assignments=[dict(line=i+1,text=line.strip()) for i,line in enumerate(source) if "myStopDist =" in line or "newStopDist =" in line]
    # The exceptional zero assignment belongs to loadState, explicitly excluded.
    load_line=next(i+1 for i,line in enumerate(source) if "MSVehicle::loadState(" in line)
    zero_line=lines["microsim_MSVehicle.cpp"]["myStopDist = 0;"][0]
    if zero_line<load_line:raise ValueError("unexpected zero stop-distance assignment")
    contract=dict(pinned_commit="fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3",manifest=manifest,line_locations=lines,
        stop_distance_assignments=assignments,load_state_zero_assignment=dict(load_state_line=load_line,zero_line=zero_line,excluded=True),
        numerical_epsilon=.001,position_epsilon_m=.1,near_zero_threshold_formula="0.1*NUMERICAL_EPS*internal_step_s",threshold_at_005_mps=5e-6,
        predicate="abs(u_pre)<eps_speed AND (myStopDist>POSITION_EPS OR (hasStops AND current route iterator==next stop iterator))",
        pipeline=["action:processLinkApproaches/finalizeSpeed/processNextStop OR nonaction:v0+a_start*h",
                  "strict near-zero conditional snap","TraCI/hybrid postprocessing (excluded by runtime proof)",
                  "updateState/getDeltaPos using signed u_final","public speed=max(u_final,0), acceleration=(public-v0)/h"],
        sufficient_context_proofs=["fresh immutable no-stop lifecycle => stopdist=doubleMax => first disjunct true",
                                   "stable ordinary first stop on same noncyclic route edge during NON-action => second disjunct true"],
        public_getter_limits=["getStops omits collision stops; require collision-free known ordinary input",
                              "getDrivingDistance is current route geometry, not cached myStopDist from last action",
                              "getStopState reports reached-state flags, not complete future-stop context",
                              "No public general-purpose myStopDist getter in audited TraCI/libsumo dispatch"],
        generic_stop_context_identifiable=False,private_variables_instrumented=False,installed_binary_modified=False,
        historical_reclassification=False,proof_requirements=list(SOURCE_PROOF_KEYS),source_audit_verified=True)
    write(batch/"near_zero_source_contract.json",contract)
    return contract


def prepare(repo,batch):
    if (batch/"preparation_manifest.json").exists():raise ValueError("new preparation required; no overwrite")
    source_contract(batch)
    (batch/"inputs/history").mkdir(parents=True,exist_ok=True);(batch/"runs").mkdir(exist_ok=True)
    previous=repo/"evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2";m=read(previous/"manifest.json")
    binding={name:next(e["sha256"] for e in m["files"] if e["path"]==name) for name in HISTORY_NAMES}
    write(batch/"source_staging_manifest.json",dict(sources=binding,role="sealed_engineering_metadata_and_inputs",declared_before_read=True,
          real_trajectory_inputs=False,old_C_state_inputs=False))
    for name,digest in binding.items():
        if sha(previous/name)!=digest:raise PermissionError("historical metadata SHA mismatch")
        shutil.copyfile(previous/name,batch/"inputs/history"/name)
    bundle=read(batch/"inputs/history/engineering_input_bundle.json")["files"];old_plan=read(batch/"inputs/history/experiment_plan.json")
    decoded={}
    for name,e in bundle.items():
        if Path(name).suffix not in [".xml",".sumocfg"]:continue
        if not name.startswith("inputs/") or ".." in Path(name).parts or ":" in name:raise ValueError("input bundle path")
        raw=gzip.decompress(base64.b64decode(e["gzip_base64"],validate=True))
        if hashlib.sha256(raw).hexdigest()!=e["sha256"] or e["sha256"]!=old_plan["frozen_files"][name]:raise ValueError("engineering bundle SHA")
        target=batch/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);decoded[name]=e["sha256"]
    write(batch/"engineering_input_lineage.json",dict(decoded=decoded,not_decoded=["inputs/calibration_reference.json"],
          source_result="RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2",old_execution_not_reopened=True))
    _copy_runtime(repo,batch)
    todo=["stage_0_5_b12n_runtime","stage_0_5_b12n_worker","stage_0_5_near_zero_observability",
          "stage_0_5_contract_fixtures","stage_0_5_stopping_contract","stage_0_5_queue_contract"]
    copied=set()
    while todo:
        name=todo.pop()
        if name in copied:continue
        source=repo/"code/src/riskprop"/(name+".py")
        if not source.exists():raise ValueError("required new source missing: "+name)
        text=source.read_text(encoding="utf-8");shutil.copyfile(source,batch/"runtime/code/src/riskprop"/source.name);copied.add(name)
        for node in ast.walk(ast.parse(text)):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module and (repo/"code/src/riskprop"/(node.module+".py")).is_file():todo.append(node.module)
    test_names=["test_stage_0_5_near_zero_observability.py","test_stage_0_5_stopping_observability.py","test_stage_0_5_stopping_contract.py",
                "test_stage_0_5_queue_contract.py","test_stage_0_5_b12_integration.py","test_stage_0_5_b12n_runtime.py"]
    for name in test_names:shutil.copyfile(repo/"code/tests"/name,batch/"runtime/code/tests"/name)
    shutil.copyfile(repo/"code/scripts/run_stage_0_5_near_zero_integration.py",batch/"runtime/code/scripts/run_stage_0_5_near_zero_integration.py")
    links=batch/"dependency_links";links.mkdir(exist_ok=True);dependencies=[]
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
    write(batch/"isolation_policy.json",dict(runtime_read_roots=[str(Path(sys.prefix).resolve()),str(Path(_sumo_binary()).resolve().parent.parent),os.environ.get("WINDIR","C:/Windows")]+dependencies,
          executables=[sys.executable,_sumo_binary(),_netconvert_binary()],python_no_site_required=True,os_complete_monitoring=False,no_real_data_inputs=True))
    write(batch/"preparation_manifest.json",dict(base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
          historical_evidence_tree=subprocess.check_output(["git","rev-parse","HEAD:evidence/results"],cwd=repo,text=True).strip(),
          copied_modules=sorted(copied),source_staging_sha256=sha(batch/"source_staging_manifest.json"),sumo_binary_sha256=sha(_sumo_binary()),netconvert_sha256=sha(_netconvert_binary())))
    print("B12N_PREPARED",flush=True)


def tests(batch):
    environment(batch)
    probe=subprocess.run([sys.executable,"-S",str(batch/"runtime/code/scripts/b1_guard_probe.py"),str(batch)],capture_output=True,text=True,timeout=30)
    if probe.returncode:raise RuntimeError("forbidden synthetic path probe")
    paths=sorted((batch/"runtime/code/tests").glob("test_*.py"))
    cmd=[sys.executable,"-S",str(batch/"runtime/code/scripts/b1_test_entry.py"),*[str(p) for p in paths],"-q",
         "-c",str(batch/"runtime/code/pytest.ini"),"--rootdir",str(batch/"runtime/code"),"--basetemp",str(batch/"test_tmp"/str(time.time_ns())),
         "-o",f"cache_dir={batch/'runtime_cache/pytest'}"]
    result=subprocess.run(cmd,cwd=batch/"runtime/code",capture_output=True,text=True,timeout=180)
    audit=read(batch/"preflight_test_access_audit.json");passed=result.returncode==0 and not audit["denied"]
    write(batch/"synthetic_test_record.json",dict(command=cmd,exit_code=result.returncode,output=result.stdout+result.stderr,
          source_sha256={p.name:sha(p) for p in paths},access_audit=audit))
    write(batch/"integration_preflight.json",dict(passed=passed,synthetic_tests_sha256=sha(batch/"synthetic_test_record.json"),
          source_contract_verified=read(batch/"near_zero_source_contract.json")["source_audit_verified"],real_trajectory_inputs=[],
          guard_probe=read(batch/"guard_probe_result.json"),unexpected_test_denials=len(audit["denied"]),
          validation_window_rows_materialised=0,old_C_states_read=False,os_complete_monitoring=False,native_access_monitored=False,
          task_max_new_traffic_runs=5,main_matrix_allowed=False))
    print(result.stdout+result.stderr,flush=True)
    if not passed:raise PermissionError("synthetic preflight failed")


def config(batch,run_id,net,demand,duration):
    p=batch/"inputs"/(run_id+".sumocfg")
    p.write_text(f'<configuration><input><net-file value="{Path(net).relative_to(batch/"inputs").as_posix()}"/>'
      f'<route-files value="{Path(demand).relative_to(batch/"inputs").as_posix()}"/></input><time><begin value="0"/><end value="{duration}"/>'
      '<step-length value=".05"/></time><processing><step-method.ballistic value="true"/><threads value="1"/>'
      '<time-to-teleport value="-1"/><collision.action value="warn"/></processing><seed value="20261019"/></configuration>',encoding="utf-8")
    return p


def make_micro(batch,kind):
    work=batch/"inputs"/kind;work.mkdir(exist_ok=True)
    nodes=ET.Element("nodes");edges=ET.Element("edges");count=3 if kind=="N3" else 1
    for i,x in enumerate([0,150,250] if kind=="N2" else [0,250]):
        ET.SubElement(nodes,"node",dict(id=f"n{i}",x=str(x),y="0",type="traffic_light" if kind=="N2" and i==1 else "priority"))
    for i in range(2 if kind=="N2" else 1):
        ET.SubElement(edges,"edge",dict(id=f"e{i}",**{"from":f"n{i}","to":f"n{i+1}"},numLanes=str(count),speed="27.78"))
    ET.ElementTree(nodes).write(work/"nodes.nod.xml");ET.ElementTree(edges).write(work/"edges.edg.xml")
    net=work/"micro.net.xml";r=subprocess.run([_netconvert_binary(),"-n",str(work/"nodes.nod.xml"),"-e",str(work/"edges.edg.xml"),"-o",str(net),"--no-turnarounds","true"],capture_output=True,text=True,timeout=30)
    (work/"build.log").write_text(r.stdout+r.stderr,encoding="utf-8")
    if r.returncode:raise ValueError("micro network build")
    if kind=="N2":
        tree=ET.parse(net);logic=tree.getroot().find("tlLogic");n=len(logic.find("phase").attrib["state"])
        logic.attrib.update(programID="b12n_micro_red",offset="0")
        for child in list(logic):logic.remove(child)
        ET.SubElement(logic,"phase",dict(duration="30",state="r"*n));tree.write(net,encoding="utf-8",xml_declaration=True)
    routes=ET.Element("routes");route_edges="e0 e1" if kind=="N2" else "e0"
    ET.SubElement(routes,"route",dict(id="through",edges=route_edges))
    for i in range(count):
        fixed=dict(FIXED)
        if kind=="N3":fixed.update(sigma=0.,maxSpeed=[3e-6,5e-6,7e-6][i])
        ET.SubElement(routes,"vType",dict(id=f"t{i}",vClass="passenger",length="4.4196",**{k:str(v) for k,v in fixed.items()}))
    for i in range(count):
        v=ET.SubElement(routes,"vehicle",dict(id=f"micro_{i}",type=f"t{i}",route="through",depart="0",departLane=str(i),departPos="base",departSpeed=str([3e-6,5e-6,7e-6][i]) if kind=="N3" else "10"))
        if kind=="N1":ET.SubElement(v,"stop",dict(lane="e0_0",endPos="80",duration="3",parking="false"))
    demand=work/"demand.rou.xml";ET.ElementTree(routes).write(demand,encoding="utf-8",xml_declaration=True)
    run_id="b12n_"+kind;cfg=config(batch,run_id,net,demand,30.)
    length=float(ET.parse(net).getroot().find("edge[@id='e0']/lane").attrib["length"])
    return dict(run_id=run_id,kind=kind,network=net.relative_to(batch).as_posix(),demand=demand.relative_to(batch).as_posix(),config=cfg.relative_to(batch).as_posix(),
                seed=20261019,duration_s=30.,local_space=dict(edge="e0",start_m=0.,end_m=length,lanes=count,lane_km=length*count/1000),
                probe_overrides=dict(sigma=0.,maxSpeed_per_type=[3e-6,5e-6,7e-6]) if kind=="N3" else {},
                expected_role=dict(N1="ordinary stop on current edge + early stop/restart",N2="no scheduled stop; native red signal; near-zero context invariant",N3="fixed deterministic threshold probe; no search; missing branches Not Observed")[kind])


def frozen(batch):
    return {p.relative_to(batch).as_posix():sha(p) for d in [batch/"runtime",batch/"inputs",batch/"official_source"] for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def save_plan(batch,name,plan):
    if (batch/name).exists():raise ValueError("frozen plan cannot be overwritten")
    plan["frozen_files"]=frozen(batch)
    for n in ["isolation_policy.json","near_zero_source_contract.json","integration_preflight.json","execution_scope_audit.json","preparation_manifest.json"]:plan["frozen_files"][n]=sha(batch/n)
    write(batch/name,plan);(batch/(name+".sha256")).write_text(sha(batch/name)+"  "+name+"\n",encoding="utf-8")


def freeze_micro(batch):
    if not read(batch/"integration_preflight.json")["passed"]:raise PermissionError("preflight")
    runs=[make_micro(batch,k) for k in ["N1","N2","N3"]]
    write(batch/"execution_scope_audit.json",dict(declared_before_runs=True,
          Global_Blocker=["source/config/SHA/isolation","identity/time/control","exact residual/final public velocity","source necessary range","shared coordinate/gap audit","collision/teleport","resource/worker failure"],
          Scenario_Specific_Blocker=["D missing required lane change","D missing downstream exit","scenario static network defect"],
          Diagnostic_Warning=["legal edge/lane numerical not-evaluable","on-road low speed","external pending"],
          Evidence_Insufficient=["unresolved near-zero context","queue continuity/inlet spillback qualification missing"],
          C_queue_EI_does_not_block_D=True,C_shared_numeric_error_blocks_D=True,main_matrix_allowed=False))
    write(batch/"near_zero_prospective_contract.json",dict(version=VERSION,source_contract_sha256=sha(batch/"near_zero_source_contract.json"),
          exact_tolerance_m=1e-6,unknown_context="Near-Zero Context Unresolved; no exact residual; no automatic zero",
          necessary_unknown_support="two source alternatives u_pre/0; no endpoint-selected context",context_false_live="Not generally identifiable; analytic test truth only",
          thresholds_scientifically_approved=False,unknown_core_location="Evidence Insufficient; no full mechanism qualification",adjust_after_results=False))
    plan=dict(result_id=RESULT_ID,version="b12n-micro-plan-v1",task_mode=MODE,result_mode="exploratory_diagnostic_only",**SCIENCE,
              runs=runs,contract_version=VERSION,limits=dict(max_runs=3,per_run_wall_s=120,batch_wall_s=600,memory_bytes=3*1024**3,artifact_bytes=1024**3),
              overall_task_limit=dict(max_new_runs=5,max_task_wall_s=1800),P2_calculated=False,main_matrix_allowed=False)
    save_plan(batch,"micro_plan.json",plan)
    write(batch/"micro_ledger.json",dict(closed=False,runs=[dict(run_id=r["run_id"],status="not_attempted") for r in runs]))
    write(batch/"task_ledger.json",dict(closed=False,started_epoch=None,max_new_runs=5,global_stop=None,
          runs=[dict(run_id="b12n_"+k,status="not_attempted") for k in ["N1","N2","N3","C","D"]]))
    print("B12N_MICRO_FROZEN "+sha(batch/"micro_plan.json"),flush=True)


def load_plan(batch,name):
    from .stage_0_5_exploratory_response import verify_frozen
    if name not in ["micro_plan.json","integration_C_plan.json","integration_D_plan.json"]:raise PermissionError("only micro/integration plans allowed")
    if sha(batch/name)!=(batch/(name+".sha256")).read_text().split()[0]:raise PermissionError("plan SHA")
    p=read(batch/name);verify_frozen(batch,p["frozen_files"])
    if p.get("main_matrix_allowed") is not False or p.get("P2_calculated") is not False:raise PermissionError("task scope")
    kinds=["N1","N2","N3"] if name=="micro_plan.json" else [name.split("_")[1]]
    if [r["kind"] for r in p["runs"]]!=kinds or any(r["duration_s"]>(30 if name=="micro_plan.json" else 60) or r["seed"]!=20261019 for r in p["runs"]):
        raise PermissionError("frozen run/duration/seed scope")
    if sha(_sumo_binary())!=read(batch/"preparation_manifest.json")["sumo_binary_sha256"]:raise PermissionError("SUMO binary SHA changed")
    return p


def global_stop_reason(entry,summary):
    """Unknown or inconsistent severity schema fails closed across C/D."""
    if entry["status"]=="not_attempted":return None
    if entry["status"]=="failed" or summary is None:return "worker/resource/output failure"
    for field in ["global_blockers","scenario_blockers","engineering_blockers","evidence_insufficient"]:
        if not isinstance(summary.get(field),list):return "unclassified worker severity"
    if set(summary["engineering_blockers"])!=set(summary["global_blockers"]+summary["scenario_blockers"]):return "inconsistent worker severity"
    if summary["global_blockers"]:return summary["global_blockers"]
    return None


def execute(batch,name,ledger_name):
    plan=load_plan(batch,name);ledger=read(batch/ledger_name);task=read(batch/"task_ledger.json")
    if task["global_stop"] or task["closed"]:raise PermissionError("global stop")
    if ledger["closed"] or any(r["status"]!="not_attempted" for r in ledger["runs"]):raise PermissionError("no retries")
    attempts=sum(r["status"]!="not_attempted" for r in task["runs"])
    if attempts+len(plan["runs"])>5:raise PermissionError("task traffic run budget")
    if task["started_epoch"] is None:task["started_epoch"]=time.time()
    remaining=1800-(time.time()-task["started_epoch"])
    if remaining<=0:raise TimeoutError("task total wall budget")
    write(batch/"task_ledger.json",task)
    specs=[dict(run_id=r["run_id"],command=[sys.executable,"-S",str(batch/"runtime/code/scripts/run_stage_0_5_near_zero_integration.py"),
                "worker","--batch",str(batch),"--run-id",r["run_id"],"--plan",name],
                verify_files={str(batch/n):plan["frozen_files"][n] for n in [r["network"],r["demand"],r["config"]]}) for r in plan["runs"]]
    limits=dict(plan["limits"]);limits["batch_wall_s"]=min(limits["batch_wall_s"],remaining)
    result=execute_commands(batch/"runs",specs,limits=limits)
    for entry in result["runs"]:
        target=next(x for x in task["runs"] if x["run_id"]==entry["run_id"]);target.update(entry)
        path=batch/"runs"/entry["run_id"]/"summary.json"
        s=read(path) if path.exists() else None
        stop=global_stop_reason(entry,s)
        if stop:task["global_stop"]=dict(run_id=entry["run_id"],reason=stop)
    ledger.update(result,closed=True,plan_sha256=sha(batch/name));write(batch/ledger_name,ledger)
    if task["global_stop"]:task["closed"]=True
    if name=="integration_D_plan.json":task["closed"]=True
    write(batch/"task_ledger.json",task)


def micro_checkpoint(batch):
    plan=load_plan(batch,"micro_plan.json");ledger=read(batch/"micro_ledger.json");task=read(batch/"task_ledger.json")
    rows=[]
    for entry in ledger["runs"]:
        p=batch/"runs"/entry["run_id"]/"summary.json"
        if p.exists():rows.append(read(p))
    exact_after=sum(r["numerical"]["classifications"]["Exact After Verified Postprocessing"]["count"] for r in rows)
    positive=sum(r["numerical"]["branch_counts"].get("positive_snap",0) for r in rows)
    allowed=ledger["closed"] and not task["global_stop"] and len(rows)==3 and all(r["observed_s"]==30. and not r["global_blockers"] for r in rows) and exact_after>0 and positive>0
    write(batch/"micro_checkpoint.json",dict(integration_allowed=allowed,micro_plan_sha256=sha(batch/"micro_plan.json"),
          observed_exact_after=exact_after,observed_positive_snap=positive,actual_runs=len(rows),global_stop=task["global_stop"],
          missing_runtime_branches="Not Observed; no search or retry",main_matrix_allowed=False))
    write(batch/"numerical_admission_candidate.json",dict(version=VERSION,source_contract_sha256=sha(batch/"near_zero_source_contract.json"),
          micro_checkpoint_sha256=sha(batch/"micro_checkpoint.json"),integration_allowed=allowed,main_matrix_allowed=False,
          exact_tolerance_m=1e-6,scope="Engineering candidate for this task only; not future scientific approval",
          unresolved_context="keep Near-Zero Context Unresolved/Evidence Insufficient; derived necessary support is not Exact",
          exact_proofs="fresh no-stop invariant OR stable regular same-edge stop on nonaction; generic contexts unresolved",
          no_inversion_from_displacement_or_public_terminal=True))
    print(json.dumps(dict(integration_allowed=allowed,exact_after=exact_after,positive_snap=positive)),flush=True)


def freeze_integration(batch):
    if not read(batch/"micro_checkpoint.json")["integration_allowed"]:raise PermissionError("micro policy not independently verified")
    load_plan(batch,"micro_plan.json")
    for kind in ["C","D"]:
        run_id="b12n_"+kind;net=batch/"inputs"/("b12_integration_"+kind)/"b12.net.xml";demand=batch/"inputs"/("b12_integration_"+kind+".rou.xml")
        if kind=="D":
            # Nine path probes, all from lane2; spacing selected analytically
            # BEFORE traffic runs to leave travel time within the 60s cap.
            tree=ET.parse(demand);root=tree.getroot();vehicles=root.findall("vehicle")
            for v in vehicles:root.remove(v)
            for i,v in enumerate(vehicles[:9]):v.set("depart",f"{.1+1.5*i:.1f}");root.append(v)
            demand=batch/"inputs/b12n_D.rou.xml";tree.write(demand,encoding="utf-8",xml_declaration=True)
        cfg=config(batch,run_id,net,demand,60.)
        spec=dict(run_id=run_id,kind=kind,condition=kind,network=net.relative_to(batch).as_posix(),demand=demand.relative_to(batch).as_posix(),config=cfg.relative_to(batch).as_posix(),
                  seed=20261019,duration_s=60.,local_space=dict(edge="main_1",start_m=10. if kind=="C" else 50.,end_m=40. if kind=="C" else 250.,lanes=3,lane_km=.09 if kind=="C" else .6),
                  expected_role="C: queue/pending/local support" if kind=="C" else "D: actual lane2 merge + route + downstream exit; queue qualification separate")
        spec["declared_vehicles"]=150 if kind=="C" else 9
        spec["input_revision_reason"]="C unchanged engineering input" if kind=="C" else "D9 spaced1.5s for <=60s path duty; fixed before runs; no driver/network tuning"
        plan=dict(result_id=RESULT_ID,version="b12n-integration-"+kind+"-v1",task_mode=MODE,result_mode="exploratory_diagnostic_only",**SCIENCE,
                  runs=[spec],contract_version=VERSION,queue_candidate=QUEUE_CONFIG,limits=dict(max_runs=1,per_run_wall_s=180,batch_wall_s=180,memory_bytes=3*1024**3,artifact_bytes=1024**3),
                  P2_calculated=False,main_matrix_allowed=False,numerical_candidate_sha256=sha(batch/"numerical_admission_candidate.json"))
        save_plan(batch,f"integration_{kind}_plan.json",plan)
        write(batch/f"integration_{kind}_ledger.json",dict(closed=False,runs=[dict(run_id=run_id,status="not_attempted")]))
    print("B12N_C_D_INDEPENDENTLY_FROZEN",flush=True)


def dispatch(repo,batch,command,run_id=None,name="micro_plan.json"):
    if command not in ["prepare","tests","freeze-micro","micro","micro-checkpoint","freeze-integration","C","D","worker"]:
        raise PermissionError("No main matrix or other action authorized")
    if command=="prepare":return prepare(repo,batch)
    environment(batch)
    if command=="tests":return tests(batch)
    if command=="freeze-micro":return freeze_micro(batch)
    if command=="micro":return execute(batch,"micro_plan.json","micro_ledger.json")
    if command=="micro-checkpoint":return micro_checkpoint(batch)
    if command=="freeze-integration":return freeze_integration(batch)
    if command in ["C","D"]:return execute(batch,f"integration_{command}_plan.json",f"integration_{command}_ledger.json")
    if command=="worker":
        from .stage_0_5_b12n_worker import run_worker
        return run_worker(batch,run_id,name)
    raise PermissionError("No main matrix or other action authorized")
