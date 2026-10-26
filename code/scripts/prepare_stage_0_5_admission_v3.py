"""Create a new immutable V3 candidate package. XML only; never runs SUMO."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import sysconfig
import xml.etree.ElementTree as ET

from stage_0_5_admission_v3 import TASK, MANDATORY_SOURCES, factor_routes, technical_preflight
from stage_0_5_input_fidelity import compare_initial_policy, inventory
from stage_0_5_execution_v2 import environment_binding, native_resource_probe, NativeBackend
from stage_0_5_isolation_v2 import sha
from stage_0_5_research_ledger import ResearchLedger, canonical

BASELINE = "8327068c25b5a6da5a7f56d3aa659fac75efbc1b"
AUDIT = Path("docs/audits/stage_0_5_ready_to_admit_v3")
EVIDENCE = Path("evidence/admission/AAD-0.5-READY-TO-ADMIT-V3")
PLAN = "docs/plans/2026-10-26-stage-0-5-ready-to-admit-v3.md"
BUDGET = "code/configs/stage_0_5_ready_to_admit_v3.json"


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data if isinstance(data,bytes) else canonical(data)+b"\n")


def dependencies(binary, tools):
    import importlib
    files = {Path(sys.executable), binary}
    for folder in [binary.parent, Path(sys.executable).parent, Path(sys.executable).parent / "DLLs"]:
        files.update(folder.glob("*.dll")); files.update(folder.glob("*.pyd"))
    stdlib = Path(sysconfig.get_path("stdlib"))
    for directory,children,names in os.walk(stdlib):
        children[:]=[n for n in children if n not in {"site-packages","test","tests","__pycache__","idlelib","tkinter","turtledemo","ensurepip"}]
        files.update(Path(directory)/n for n in names if n.endswith(".py"))
    for name in ["numpy","pandas","pyarrow","psutil"]:
        folder = Path(importlib.import_module(name).__file__).parent
        files.update(p for p in folder.rglob("*") if p.is_file() and p.suffix in {".py",".pyd",".dll",".json"} and not {"test","tests","__pycache__"} & set(p.parts))
        sibling = folder.parent / (name + ".libs")
        if sibling.exists(): files.update(p for p in sibling.rglob("*") if p.is_file())
    for name in ["traci","sumolib"]:
        files.update((tools / name).rglob("*.py"))
    return {str(p.resolve()):sha(p) for p in sorted(files) if p.is_file()}


def prepare(root, revision):
    if not re.fullmatch(r"candidate-v[1-9][0-9]*",revision):
        raise ValueError("versioned_candidate_required")
    folder = root / EVIDENCE / revision
    if folder.exists(): raise FileExistsError("immutable_candidate_exists")
    approved = json.loads((root / "evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/review_proposal.json").read_bytes())
    ds = approved["runs"][0]
    snapshots = {}
    for n,expected in ds["inputs"].items():
        data = (root/n).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected: raise ValueError("original_DS_input_drift")
        snapshots[Path(n).name] = data
    original_name="code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs/ID1_SUPPLY_0750/routes.rou.xml"
    original=(root/original_name).read_bytes()
    if hashlib.sha256(original).hexdigest()!=approved["approved_input_sha256"][original_name]:raise ValueError("original_initial_input_drift")
    _,_,initial,_,_=inventory(original)
    targets=[k for k,v in initial.items() if float(v.get("departSpeed"))==10]
    static_initial=compare_initial_policy(original,snapshots["routes.rou.xml"],target_ids=targets)
    log_name="code/outputs/formal/calibration/stage_0_5_interaction_diagnostics_v1/ID1_SUPPLY_0750/worker_console.log"
    old_log=(root/log_name).read_bytes()
    if hashlib.sha256(old_log).hexdigest()!="2eaf711e946b275deb93cfba10660475ada7223f936ba2596f562b9b5ad4d258":raise ValueError("historical_log_drift")
    write_new(folder/"initialization_static_audit.json",dict(policy="Proposed DS38 only",comparison=static_initial,
        original_routes_sha256=sha(root/original_name),DS_routes_sha256=hashlib.sha256(snapshots["routes.rou.xml"]).hexdigest(),
        i0007_original=dict(initial["i0007_i0007"].attrib),old_log_sha256=hashlib.sha256(old_log).hexdigest(),
        observation="native log names i0007 cannot depart with given velocity at0; no identity-specific discarded assertion",
        discarded_identity="Unknown; aggregate discarded=1 is insufficient",actual_insertion="Unknown; no new simulation",
        first_run_consequence="native error / unaccounted identity stops run, prevents B00 reuse; no deletion or accepted discard"))
    binary = Path(approved["sumo_binary"]["path"])
    if sha(binary) != approved["sumo_binary"]["sha256"]: raise ValueError("native_binary_drift")
    old_tools = json.loads((root / "evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/review_ready_plan.json").read_bytes())
    tools = Path(old_tools["traci_tools_root"])
    reference = "evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/us101__0750_0805_real_offset100.csv"
    cfg = ET.fromstring(snapshots["run.sumocfg"])
    for tag,value in {"tripinfo-output":"tripinfo.xml","tripinfo-output.write-unfinished":"true","tripinfo-output.write-undeparted":"true"}.items():
        ET.SubElement(cfg.find("output"),tag,value=value)
    cfg_bytes = ET.tostring(cfg,encoding="utf-8",xml_declaration=True)
    inputs = folder / "inputs"
    write_new(inputs/"network.net.xml",snapshots["network.net.xml"])
    write_new(inputs/"run.sumocfg",cfg_bytes)
    runs=[]
    for arm,supply,ramp in [("B00",False,False),("S10",True,False),("R01",False,True),("SR11",True,True)]:
        routes = ET.fromstring(snapshots["routes.rou.xml"])
        if ramp:
            group={}
            for v in routes.findall("vehicle"):
                if v.get("route")=="entering" and not v.get("id").startswith("i"):
                    group.setdefault(int(float(v.get("depart"))//60),[]).append(v)
            for block, vehicles in group.items():
                vehicles.sort(key=lambda v:(float(v.get("depart")),v.get("id")))
                for i,v in enumerate(vehicles):
                    t=block*60+20+(5*i/(len(vehicles)-1) if len(vehicles)>1 else 0)
                    v.set("depart",f"{round(t/.05)*.05:.2f}")
            vehicles=routes.findall("vehicle")
            for v in vehicles: routes.remove(v)
            routes.extend(sorted(vehicles,key=lambda v:(float(v.get("depart")),v.get("id"))))
        data=ET.tostring(routes,encoding="utf-8",xml_declaration=True) if ramp else snapshots["routes.rou.xml"]
        static=factor_routes(snapshots["routes.rou.xml"],data,ramp=ramp)
        route_path=inputs/arm/"routes.rou.xml"; write_new(route_path,data)
        files={"network.net.xml":(inputs/"network.net.xml").relative_to(root).as_posix(),
               "routes.rou.xml":route_path.relative_to(root).as_posix(),"run.sumocfg":(inputs/"run.sumocfg").relative_to(root).as_posix()}
        ident=f"V3_0750_{arm}_DS38_s20261201"
        output="code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/"+ident
        env={"SystemRoot":os.environ.get("SystemRoot","C:/Windows"),"WINDIR":os.environ.get("WINDIR","C:/Windows"),
             "PATH":str(binary.parent)+os.pathsep+str(Path(os.environ.get("SystemRoot","C:/Windows"))/"System32"),
             "TEMP":str(root/output/"tmp"),"TMP":str(root/output/"tmp"),"PYTHONNOUSERSITE":"1","PYTHONDONTWRITEBYTECODE":"1"}
        runs.append(dict(id=ident,task_id=TASK,condition="us101__0750_0805",arm=arm,seed=20261201,duration_s=420,internal_step_s=.05,
            evaluation_elapsed_s=[120,390],question="same-initialization factorial candidate; B00 first is initialization and support qualification",
            contrast="reference" if arm=="B00" else ("S10-B00" if arm=="S10" else "R01-B00" if arm=="R01" else "(SR11-R01)-(S10-B00)"),
            factors=dict(supply=supply,ramp=ramp),initialization_policy="DS38 proposed: exactly 38 original numeric10 initial vehicles; i0007 unchanged; stop on native error or unaccounted identity",
            input_files=files,input_sha256={n:sha(root/n) for n in files.values()},artifact_path=output,
            common_support_references=[reference],paired_base_routes=(inputs/"B00/routes.rou.xml").relative_to(root).as_posix(),
            static_factor_check=static,ramp_acceptance=dict(researcher_decision=None,legacy_90_percent="Proposed only"),
            supply_target_lanes=["main_2_"+str(i) for i in range(5)],native_environment=env,
            lane_speed_schedule=([dict(start_s=0,end_s=180,speed_mps=10),dict(start_s=180,end_s=240,speed_mps=5),dict(start_s=240,end_s=420,speed_mps=10)]
                                 if supply else [dict(start_s=0,end_s=420,speed_mps=10)])))
    dep=dependencies(binary,tools); dep_path=folder/"runtime_dependencies.json"
    write_new(dep_path,dict(files=dep,policy="exact Python stdlib/package native files, SUMO DLLs and TraCI/sumolib sources; OS system dependencies remain an isolation blocker"))
    environment_report=(root/AUDIT/"environment_probe.json")
    # Explicit import closure of the called C6/D1 modules and riskprop.__init__;
    # unused calibration/plotting prototypes are not execution dependencies.
    source_names=MANDATORY_SOURCES+["code/tests/test_stage_0_5_admission_v3.py"]
    source_names += ["code/src/riskprop/"+n+".py" for n in ["__init__","legacy/__init__","legacy/events","legacy/pipeline",
        "legacy/propagation","ngsim_risk_calibration","calibration","real_trajectory"]]
    source_sha={n:sha(root/n) for n in source_names}
    validation_path=root/AUDIT/"validation_record.json"
    software_qualified=False
    if validation_path.exists():
        validation=json.loads(validation_path.read_bytes())
        software_qualified=(validation.get("source_sha256")==source_sha and validation.get("full",{}).get("exit_code")==0
                            and validation.get("targeted",{}).get("exit_code")==0)
        if not software_qualified:raise ValueError("final_validation_source_binding_mismatch")
        write_new(folder/"validation_record.json",validation_path.read_bytes())
    external={str(binary):sha(binary)}
    for path in list((tools/"traci").glob("*.py"))+[tools.parent/"data/xsd/tripinfo_file.xsd"]:
        external[str(path)]=sha(path)
    protocol_text=(tools/"traci/constants.py").read_text(encoding="utf-8")
    protocol=int(re.search(r"TRACI_VERSION\s*=\s*(\d+)",protocol_text).group(1))
    git_state=dict(observed_HEAD=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
        branch=subprocess.check_output(["git","branch","--show-current"],cwd=root,text=True).strip(),
        tracked_status=subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=root,text=True).splitlines(),
        semantics="Preparation observation; exact source/input hashes are authoritative across the subsequent metadata commit; final HEAD is recorded independently after commit")
    proposal=dict(schema="aad.ready-to-admit.v3",task_id=TASK,status="Proposed / BLOCKED_ENGINEERING",plan_version=revision,
        execution_allowed=False,researcher_confirmed=False,protocol_frozen=False,
        plan_path=PLAN,plan_sha256=sha(root/PLAN),budget_path=BUDGET,budget_sha256=sha(root/BUDGET),
        git_commit=BASELINE,git_state=git_state,worktree_sha256=hashlib.sha256(canonical(source_sha)).hexdigest(),worktree_binding_semantics="exact final source file set relative to baseline; current Git HEAD independently recorded in validation",
        environment=environment_binding(["numpy","pandas","pyarrow","psutil"]),native_binary=str(binary),traci_tools_root=str(tools),
        native_runtime_version=[protocol,"SUMO 1.26.0"],tool_version_source="prior native FCD header + unchanged binary SHA; no native query in V3",
        software_validation_path=(folder/"validation_record.json").relative_to(root).as_posix() if software_qualified else None,
        software_validation_sha256=sha(folder/"validation_record.json") if software_qualified else None,
        external_file_sha256=external,runtime_dependency_manifest=dep_path.relative_to(root).as_posix(),runtime_dependency_manifest_sha256=sha(dep_path),
        native_environment=runs[0]["native_environment"],source_sha256=source_sha,
        measurement_reference_sha256={reference:sha(root/reference)},support_input_sha256={runs[0]["paired_base_routes"]:sha(root/runs[0]["paired_base_routes"])},
        admission=dict(initialization_policy_approved=False,measurement_contract_approved=False,input_fidelity_approved=False),
        isolation=dict(accepted_for_new_task=False,report_path=environment_report.relative_to(root).as_posix(),report_sha256=sha(environment_report),historical_incident="Not Accepted"),
        candidate_run_order=[r["id"] for r in runs],first_approval_candidate_run_ids=[runs[0]["id"]],runs=runs)
    write_new(folder/"proposal.json",proposal)
    resource=native_resource_probe(NativeBackend())()
    write_new(folder/"resource_snapshot.json",resource)
    report=technical_preflight(root,folder/"proposal.json",runs[0]["id"],resource_sample=resource)
    write_new(folder/"technical_preflight.json",report)
    write_new(folder/"admission_profile.json",dict(task_id=TASK,status=report["status"],proposal_sha256=sha(folder/"proposal.json"),
        execution_allowed=False,researcher_confirmed=False,protocol_frozen=False,accepted_for_new_task=False,
        native_launch_build_lock=True,software_validation_source_matched=software_qualified,native_isolation="Unknown / Blocked",
        historical_incident="Not Accepted",Gate_changed=False,new_SUMO_launches=0,real_TraCI_connections=0,new_trajectories=0))
    entries={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob("*") if p.is_file()}
    write_new(folder/"manifest.json",dict(task_id=TASK,files=entries,proposal_sha256=sha(folder/"proposal.json"),status=report["status"],new_trajectories=0))
    return report


def verify_package(root, folder, *, portable_only=False):
    folder=folder.resolve()
    if not folder.is_relative_to((root/EVIDENCE).resolve()): raise ValueError("package_scope")
    m=json.loads((folder/"manifest.json").read_bytes())
    for name,expected in m["files"].items():
        path=folder/name
        if ".." in Path(name).parts or not path.resolve().is_relative_to(folder) or sha(path)!=expected:
            raise ValueError("package_drift:"+name)
    p=json.loads((folder/"proposal.json").read_bytes())
    if sha(folder/"proposal.json")!=m["proposal_sha256"]:raise ValueError("proposal_digest")
    for name,expected in p["source_sha256"].items():
        if sha(root/name)!=expected:raise ValueError("current_source_drift:"+name)
    if not all(p[k] is False for k in ["execution_allowed","researcher_confirmed","protocol_frozen"]):
        raise ValueError("unapproved_preparation_flags")
    if p["isolation"]["accepted_for_new_task"] is not False:raise ValueError("unproved_native_isolation")
    if not portable_only:
        if p["environment"]!=environment_binding(p["environment"]["packages"]):raise ValueError("environment_drift")
        for name,expected in p["external_file_sha256"].items():
            if sha(Path(name))!=expected:raise ValueError("external_tool_drift")
        deps=json.loads((root/p["runtime_dependency_manifest"]).read_bytes())
        for name,expected in deps["files"].items():
            if sha(Path(name))!=expected:raise ValueError("runtime_dependency_drift:"+name)
    return dict(current_package_verified=True,proposal_sha256=m["proposal_sha256"],status=m["status"],native_isolation_accepted=False,new_trajectories=0)


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--revision");p.add_argument("--verify",type=Path);p.add_argument("--portable-only",action="store_true")
    a=p.parse_args()
    if a.verify: result=verify_package(a.repo_root.resolve(),a.verify,portable_only=a.portable_only)
    elif a.revision: result=prepare(a.repo_root.resolve(),a.revision)
    else: p.error("choose --revision or --verify")
    print(json.dumps(result,ensure_ascii=False))
