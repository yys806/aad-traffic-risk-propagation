"""B1 fixed-behaviour arrival/supply/geometry mechanism exploration."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .stage_0_5_calibration_readiness import _write_json,_sha256_file,_utc_now
from .stage_0_5_exploratory_response import edge_exposure,_dist,local_mask,local_density,input_accounting,verify_frozen
from .stage_0_5_sumo import (NETWORK_DESIGN_CANDIDATE,CalibrationValidationGuard,CALIBRATION_VALIDATION_POLICY,
    _sumo_binary,_netconvert_binary,_ensure_traci_importable,build_candidate_network,compute_sumo_measurements,
    extract_sumo_formal_p2_events,FORMAL_ALGORITHM_VERSION)
from .stage_0_5_b1_isolation import read_reference,WINDOWS

RESULT_ID="RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1"
MODE="exploratory_diagnostic_only"


def classify_result(exit_code,output_exists,blockers,warnings):
    if exit_code!=0 or not output_exists:return "failed"
    if blockers:return "completed_with_engineering_blocker"
    if warnings:return "completed_with_diagnostic_warning"
    return "completed_valid"


def arrival_times(flow,duration,kind):
    headway=3600/(3*flow)
    times=np.arange(headway,duration-.1,headway)
    if kind=="platoon":times=np.floor(times/30)*30+(times%30)*.5
    return (np.ceil(times*10-1e-8)/10).tolist()


def _tree_bytes(root):return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def execute_commands(root,commands,*,synthetic=False,limits,cancelled=False):
    """Real subprocess supervision: stop all scheduling at any blocker/failure."""
    import psutil
    root=Path(root);root.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    result=dict(runs=[dict(run_id=c["run_id"],status="not_attempted") for c in commands],stop_reason=None)
    for spec,entry in zip(commands,result["runs"]):
        if cancelled:
            entry["status"]="cancelled";result["stop_reason"]="cancelled";break
        try:
            for name,digest in spec.get("verify_files",{}).items():
                if _sha256_file(Path(name))!=digest:raise ValueError("hash mismatch")
        except Exception as exc:
            entry.update(status="failed",failure="hash",detail=str(exc));result["stop_reason"]="hash";break
        out=root/spec["run_id"]
        if out.exists():raise ValueError("never overwrite an attempted run")
        out.mkdir()
        command=spec.get("command") or [sys.executable,"-S",str(Path(__file__).resolve().parents[2]/"scripts/b1_synthetic_worker.py"),spec["synthetic"],str(out)]
        start=time.monotonic();peak=0;reason=None
        entry.update(status="running",started_utc=_utc_now())
        _write_json(root/"controller_ledger.json",result)
        with (out/"worker.log").open("w",encoding="utf-8") as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            process=psutil.Process(proc.pid)
            while proc.poll() is None:
                try:
                    peak=max(peak,process.memory_info().rss+sum(c.memory_info().rss for c in process.children(recursive=True) if c.is_running()))
                except psutil.Error:pass
                if peak>limits["memory_bytes"]:reason="memory"
                if _tree_bytes(root)>limits["artifact_bytes"]:reason="disk"
                if time.monotonic()-start>limits["per_run_wall_s"]:reason=reason or "timeout"
                if time.monotonic()-started>limits["batch_wall_s"]:reason=reason or "batch_timeout"
                if reason:
                    for child in process.children(recursive=True):
                        try:child.terminate()
                        except psutil.Error:pass
                    proc.terminate();break
                time.sleep(.025 if synthetic else .25)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        exists=(out/"summary.json").exists()
        summary=json.loads((out/"summary.json").read_text(encoding="utf-8")) if exists else {}
        entry.update(status=classify_result(proc.returncode,exists,summary.get("engineering_blockers",[]),summary.get("diagnostic_warnings",[])),
            exit_code=proc.returncode,failure=reason,wall_s=time.monotonic()-start,peak_sampled_tree_rss_bytes=peak,
            blockers=summary.get("engineering_blockers",[]),warnings=summary.get("diagnostic_warnings",[]),bytes=_tree_bytes(out))
        if reason:entry["status"]="failed"
        _write_json(root/"controller_ledger.json",result)
        print(json.dumps(dict(run_id=spec["run_id"],status=entry["status"],failure=reason,
            blockers=entry["blockers"],wall_s=entry["wall_s"],peak_MB=peak/1e6)),flush=True)
        if entry["status"] in ["failed","completed_with_engineering_blocker"]:
            result["stop_reason"]=reason or entry["status"];break
    _write_json(root/"controller_ledger.json",result)
    return result


def _copy_runtime(repo,batch):
    destination=batch/"runtime/code/src/riskprop";destination.mkdir(parents=True,exist_ok=True)
    (destination/"__init__.py").write_text('"""B1 capsule: no legacy convenience imports."""\n',encoding="utf-8")
    todo=["stage_0_5_boundary_bottleneck","stage_0_5_b1_isolation","stage_0_5_b1_analysis"]
    copied=[]
    while todo:
        name=todo.pop()
        if name in copied:continue
        source=repo/"code/src/riskprop"/(name+".py")
        if not source.exists():raise ValueError(f"required code missing {name}")
        text=source.read_text(encoding="utf-8");copied.append(name)
        shutil.copyfile(source,destination/source.name)
        for node in ast.walk(ast.parse(text)):
            if isinstance(node,ast.ImportFrom) and node.module:
                relative=node.module if node.level==1 else node.module.removeprefix("riskprop.") if node.module.startswith("riskprop.") else None
                if relative and (repo/"code/src/riskprop"/(relative+".py")).is_file():todo.append(relative)
    scripts=batch/"runtime/code/scripts";scripts.mkdir(parents=True,exist_ok=True)
    for name in ["run_stage_0_5_boundary_bottleneck.py","b1_synthetic_worker.py","b1_guard_probe.py","b1_test_entry.py"]:
        shutil.copyfile(repo/"code/scripts"/name,scripts/name)
    tests=batch/"runtime/code/tests";tests.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(repo/"code/tests/test_stage_0_5_boundary_bottleneck.py",tests/"test_stage_0_5_boundary_bottleneck.py")
    (batch/"runtime/code/pytest.ini").write_text('[pytest]\npythonpath=src\ntestpaths=tests\n',encoding="utf-8")
    (batch/"runtime/code/src/sitecustomize.py").write_text('''import os,atexit,json
from pathlib import Path
if os.environ.get("AAD_B1_CAPSULE"):
    from riskprop.stage_0_5_b1_isolation import install_guard
    cap=Path(os.environ["AAD_B1_CAPSULE"])
    audit=install_guard(cap)
    def save():
        d=cap/"access_logs";d.mkdir(exist_ok=True)
        (d/f"python_{os.getpid()}.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    atexit.register(save)
''',encoding="utf-8")
    return copied


def _test_inventory(repo):
    result=[]
    for path in sorted((repo/"code/tests").glob("test_*.py")):
        text=path.read_text(encoding="utf-8")
        if path.name=="test_stage_0_5_boundary_bottleneck.py":category="synthetic_and_allowlisted_capsule"
        elif path.name=="test_project_docs.py":category="git_docs_portable_evidence"
        elif any(x in text for x in ["outputs/formal","outputs'/'formal","outputs\" / \"formal"]):category="potential_historical_full_source_local_artifacts"
        elif any(x in text for x in ["RAW_ROOT","dataset/","dataset\\"]):category="additional_local_data"
        else:category="code_or_synthetic_requires_clean_clone_audit"
        top=[]
        tree=ast.parse(text)
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
            for n in ast.walk(node):
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ["read_csv","read_parquet","read_json","read_text"]:top.append(n.lineno)
        result.append(dict(path=path.relative_to(repo).as_posix(),sha256=_sha256_file(path),category=category,
            top_level_data_read_call_lines=top,
            b1_capsule_permitted=path.name=="test_stage_0_5_boundary_bottleneck.py",
            whole_suite_permitted_only_in_clean_git_clone=True))
    return result


def prepare(repo,batch):
    if (batch/"experiment_plan.json").exists():raise ValueError("frozen B1 batch cannot be changed")
    batch.mkdir(parents=True,exist_ok=True);(batch/"inputs").mkdir(exist_ok=True);(batch/"runs").mkdir(exist_ok=True)
    base=repo/"evidence/results/RES-STAGE-0.5-CALIBRATION-GAPS-V1"
    manifest=json.loads((base/"manifest.json").read_text(encoding="utf-8"))
    allowed=["diagnostics.json","unified_strata.json","benchmark_plan.json"]
    policy=copy.deepcopy(CALIBRATION_VALIDATION_POLICY);bindings={};data={}
    for name in allowed:
        digest=next(f["sha256"] for f in manifest["files"] if f["path"]==name)
        identity="b1_allowlisted_summary::"+name
        policy["calibration"].append(identity);policy["source_bindings"][identity]=digest
        bindings[name]=dict(source=identity,sha256=digest,purpose="B1 two calibration-window aggregate projection")
    _write_json(batch/"source_staging_manifest.json",dict(allowed=bindings,role="calibration",declared_before_reads=True))
    guard=CalibrationValidationGuard(policy)
    for name,binding in bindings.items():
        guard.require_source_read(base/name,role="calibration",source=binding["source"],purpose=binding["purpose"])
        data[name]=json.loads((base/name).read_text(encoding="utf-8"))
    if set(data["diagnostics.json"]["windows"])!=set(WINDOWS):raise PermissionError("unexpected source window")
    ref=dict(kind="two_window_aggregate",windows={g:dict(interior_metrics=w["interior_local_metrics"],
        interior_coverage_s=w["interior_coverage_s"],crossings=w["interior_crossings"]) for g,w in data["diagnostics.json"]["windows"].items()},
        fleet=data["benchmark_plan.json"]["fleet"],density_thresholds=data["unified_strata.json"]["thresholds_veh_km_lane"],
        source_bindings=bindings,scope="two existing calibration summaries only; no trajectory/event table read")
    _write_json(batch/"inputs/calibration_reference.json",ref)
    _write_json(batch/"source_manifest.json",dict(calibration_reference=dict(path="calibration_reference.json",sha256=_sha256_file(batch/"inputs/calibration_reference.json"),role="calibration",kind="two_window_aggregate")))
    _write_json(batch/"source_access_audit.json",dict(accesses=guard.audit(),original_summary_bindings=bindings,
        validation_rows_materialised=0,historical_full_source_files_opened=False))
    copied=_copy_runtime(repo,batch)
    _write_json(batch/"test_scope_audit.json",dict(tests=_test_inventory(repo),
        historical_cause="Path.exists-based skipif enables unguarded full-table reads when local outputs exist; read calls are inside tests, not fixture role checks",
        capsule_test_set=["test_stage_0_5_boundary_bottleneck.py"],
        historical_inputs_not_copied=True,full_regression_only_clean_git_clone=True,
        skipped_data_tests_do_not_count_as_pass=True))
    windows_root=Path(os.environ.get("WINDIR","C:/Windows")).resolve()
    dependencies=[];links=batch/"dependency_links";links.mkdir(exist_ok=True)
    for name in ["numpy","pandas","pyarrow","psutil","matplotlib","pytest","packaging","dateutil"]:
        module=__import__(name)
        if getattr(module,"__file__",None):dependencies.append(str(Path(module.__file__).resolve().parent))
    # Expose only approved foreign packages through capsule-local junctions.
    # Do not process global/user .pth files or add their parent directory to sys.path.
    import _winapi
    dependency_links=[]
    for name,module in list(sys.modules.items()):
        if "." in name or not getattr(module,"__file__",None):continue
        source=Path(module.__file__).resolve()
        if "site-packages" not in source.parts or source.is_relative_to(Path(sys.prefix).resolve()):continue
        if source.name=="__init__.py":
            target=source.parent;link=links/name
            if not link.exists():_winapi.CreateJunction(str(target),str(link))
            dependencies.append(str(target));dependency_links.append(dict(name=name,target=str(target),initializer_sha256=_sha256_file(source)))
            libraries=target.parent/(name+".libs")
            if libraries.is_dir():
                link=links/libraries.name
                if not link.exists():_winapi.CreateJunction(str(libraries),str(link))
                dependencies.append(str(libraries))
            for metadata in target.parent.glob(name.replace("_","-")+"-*.dist-info"):
                link=links/metadata.name
                if not link.exists():_winapi.CreateJunction(str(metadata),str(link))
                dependencies.append(str(metadata))
        else:
            shutil.copyfile(source,links/source.name)
            dependency_links.append(dict(name=name,target=str(source),module_sha256=_sha256_file(source)))
    _write_json(batch/"isolation_policy.json",dict(capsule=str(batch.resolve()),runtime_read_roots=[str(Path(sys.prefix).resolve()),str(Path(_sumo_binary()).resolve().parent.parent),str(windows_root)]+dependencies,
        executables=[str(Path(sys.executable).resolve()),str(Path(_sumo_binary()).resolve()),str(Path(_netconvert_binary()).resolve())],
        forbidden_sources=["us101__0820_0835","locked_holdout","historical whole-source artifacts","unknown sources"],
        code_modules=copied,dependency_links=dependency_links,python_no_site_required=True,os_complete_monitoring=False))
    prior=batch.parent/"stage_0_5_boundary_bottleneck_v1"
    expected_prior="d637839b1c4997e69455d00d5de65648dea0657d9e9a3df2a0f5f794306a5b84"
    if _sha256_file(prior/"experiment_plan.json")!=expected_prior:raise ValueError("prior closed plan binding differs")
    old=json.loads((prior/"execution_ledger.json").read_text())
    if not old["closed"] or sum(r["status"]!="not_attempted" for r in old["runs"])!=1:raise ValueError("prior attempt count/closure differs")
    history=batch/"history/b1_plan_v1";history.mkdir(parents=True,exist_ok=True)
    history_bindings={}
    for rel in ["experiment_plan.json","execution_ledger.json","runs/b1_A_s20261019/summary.json","access_logs/worker_b1_A_s20261019.json"]:
        target=history/Path(rel).name;shutil.copyfile(prior/rel,target);history_bindings[rel]=_sha256_file(target)
    _write_json(batch/"plan_revision_audit.json",dict(revision=2,prior_plan_sha256=expected_prior,prior_closed=True,
        prior_matrix_attempts=1,new_matrix_runs=4,task_run_ceiling=8,task_total_planned=5,unused_slots=3,
        task_started_epoch=old["started_epoch"],history_bindings=history_bindings,
        reason="V1 failed closed after blocked metadata search over ambient sys.path; V2 uses -S, sanitized paths and approved dependency links; traffic design unchanged",
        v1_result_status="failed (completed traffic states retained, not promoted to valid)",second_seed="not scheduled: remaining3 slots cannot fit a full four-condition seed"))
    _write_json(batch/"preparation_manifest.json",dict(created_utc=_utc_now(),base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
        capsule=str(batch.resolve()),python_executable=sys.executable,source_manifest_sha256=_sha256_file(batch/"source_manifest.json")))
    print(json.dumps(dict(capsule=str(batch.resolve()),modules=len(copied),sources=allowed)),flush=True)


def _environment(batch):
    (batch/"runtime_cache/tmp").mkdir(parents=True,exist_ok=True)
    os.environ.update(AAD_B1_CAPSULE=str(batch),PYTHONPATH=str(batch/"runtime/code/src"),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONPYCACHEPREFIX=str(batch/"runtime_cache/pycache"),MPLCONFIGDIR=str(batch/"runtime_cache/matplotlib"),
        TEMP=str(batch/"runtime_cache/tmp"),TMP=str(batch/"runtime_cache/tmp"))


def preflight(batch):
    _environment(batch)
    source=json.loads((batch/"source_manifest.json").read_text())
    ref=read_reference(batch/"inputs",source,"calibration_reference",role="calibration")
    (batch/"test_tmp").mkdir(exist_ok=True)
    probe=subprocess.run([sys.executable,"-S",str(batch/"runtime/code/scripts/b1_guard_probe.py"),str(batch)],capture_output=True,text=True,timeout=30)
    if probe.returncode:raise RuntimeError(probe.stdout+probe.stderr)
    cmd=[sys.executable,"-S",str(batch/"runtime/code/scripts/b1_test_entry.py"),str(batch/"runtime/code/tests/test_stage_0_5_boundary_bottleneck.py"),"-q",
        "-c",str(batch/"runtime/code/pytest.ini"),"--rootdir",str(batch/"runtime/code"),
        "--basetemp",str(batch/"test_tmp"/str(time.time_ns())),"-o",f"cache_dir={batch/'runtime_cache/pytest'}"]
    result=subprocess.run(cmd,cwd=batch/"runtime/code",capture_output=True,text=True,timeout=120)
    (batch/"preflight_test.log").write_text(result.stdout+result.stderr,encoding="utf-8")
    print(result.stdout,flush=True)
    test_access=json.loads((batch/"preflight_test_access_audit.json").read_text())
    passed=result.returncode==0 and not test_access["denied"]
    _write_json(batch/"execution_guard_audit.json",dict(passed=passed,synthetic_worker_tests=True,
        tested=["normal","warning","completed_blocker","exit_failure","missing_output","timeout","memory","disk","hash","no_following_launch","cancelled"],
        test_output=result.stdout,source_sha256=_sha256_file(batch/"runtime/code/tests/test_stage_0_5_boundary_bottleneck.py")))
    _write_json(batch/"data_isolation_preflight.json",dict(passed=passed,
        summary_sources=source,source_sha256=_sha256_file(batch/"inputs/calibration_reference.json"),
        accessible_windows=list(ref["windows"]),forbidden_sources=["us101__0820_0835","locked_holdout","unknown","historical full-source"],
        guard_probe=json.loads((batch/"guard_probe_result.json").read_text()),test_set=cmd,
        test_environment=str(batch/"runtime"),actual_input_directory=str(batch/"inputs"),
        validation_window_rows_materialised=0,historical_source_data_loaded=False,
        synthetic_test_unexpected_denials=len(test_access["denied"]),python_no_site=test_access["python_no_site"],
        os_complete_monitoring=False,limitations="Python entrypoint audit plus code/data-minimal capsule; native extensions/SUMO filesystem accesses are not OS-traced; no absolute adversarial security claim"))
    if not passed:raise RuntimeError("preflight failed; matrix execution forbidden")


def network_contract(path):
    net=ET.parse(path).getroot();edges={e.attrib["id"]:e for e in net.findall("edge") if not e.attrib["id"].startswith(":")}
    main=edges["main_1"].findall("lane")
    if len(main)!=3 or any(float(l.attrib["length"])<250 or abs(float(l.attrib["speed"])-27.78)>1e-6 for l in main):
        raise ValueError("observation lane support changed")
    connections=[c.attrib for c in net.findall("connection")]
    for i in range(3):
        if not any(c["from"]=="main_0" and c["to"]=="main_1" and c["fromLane"]==str(i) and c["toLane"]==str(i) for c in connections):raise ValueError("upstream lane disconnected")
    points={}
    for lane in main:
        shape=np.array([list(map(float,p.split(","))) for p in lane.attrib["shape"].split()])
        distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(shape,axis=0),axis=1))]
        points[lane.attrib["id"]]=[[float(np.interp(x,distance,shape[:,j])) for j in [0,1]] for x in [50,150,250]]
    return dict(observation_lane_count=3,lane_km=.6,points=points,
        edge_lanes={e:len(v.findall("lane")) for e,v in edges.items()},
        edge_lengths={e:float(v.find("lane").attrib["length"]) for e,v in edges.items()},
        connections=connections,sha256=_sha256_file(path))


def _networks(batch):
    inputs=batch/"inputs";networks={}
    for condition in ["A","C","D"]:
        work=inputs/condition
        if condition=="A":
            built=build_candidate_network(work);path=Path(built["network"])
        else:
            work.mkdir(exist_ok=True)
            spec=copy.deepcopy(NETWORK_DESIGN_CANDIDATE)
            node_lines=[f'<node id="{n["id"]}" x="{n["x"]}" y="{n["y"]}" type="'+('traffic_light' if condition=="C" and n["id"]=="hwy_j2" else 'priority')+'"/>' for n in spec["nodes"]]
            edge_lines=[f'<edge id="{e["id"]}" from="{e["from"]}" to="{e["to"]}" priority="{e["priority"]}" numLanes="{2 if condition=="D" and e["id"]=="main_2" else e["lanes"]}" speed="{e["speed_mps"]}"/>' for e in spec["edges"]]
            (work/"nodes.nod.xml").write_text('<nodes>'+''.join(node_lines)+'</nodes>',encoding="utf-8")
            (work/"edges.edg.xml").write_text('<edges>'+''.join(edge_lines)+'</edges>',encoding="utf-8")
            path=work/(condition+".net.xml")
            cmd=[_netconvert_binary(),"-n",str(work/"nodes.nod.xml"),"-e",str(work/"edges.edg.xml"),"-o",str(path),"--no-turnarounds","true"]
            if condition=="D":
                connections=[dict(fr="main_0",to="main_1",a=i,b=i) for i in range(3)]+[dict(fr="main_1",to="main_2",a=i,b=i) for i in range(2)]
                connections += [dict(fr="onramp",to="main_1",a=0,b=0),dict(fr="main_1",to="offramp",a=0,b=0)]
                (work/"connections.con.xml").write_text('<connections>'+''.join(f'<connection from="{c["fr"]}" to="{c["to"]}" fromLane="{c["a"]}" toLane="{c["b"]}"/>' for c in connections)+'</connections>',encoding="utf-8")
                cmd += ["--connection-files",str(work/"connections.con.xml")]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            (work/"build.log").write_text(result.stdout+result.stderr,encoding="utf-8")
            if result.returncode:raise ValueError(result.stderr)
            if condition=="C":
                tree=ET.parse(path);logic=next(t for t in tree.getroot().findall("tlLogic") if t.attrib["id"]=="hwy_j2")
                count=len(logic.find("phase").attrib["state"])
                logic.attrib.update(type="static",programID="b1_supply_v1",offset="0")
                for child in list(logic):logic.remove(child)
                for duration,state in [(23.8,"G"),(6.2,"y"),(30,"r")]:ET.SubElement(logic,"phase",dict(duration=str(duration),state=state*count))
                tree.write(path,encoding="utf-8",xml_declaration=True)
        networks[condition]=dict(path=path.relative_to(batch).as_posix(),version=f"b1_{condition.lower()}_v1",**network_contract(path))
    networks["B"]=copy.deepcopy(networks["A"])
    for condition in ["B","C","D"]:
        for lane,points in networks["A"]["points"].items():
            if not np.allclose(points,networks[condition]["points"][lane],atol=.05,rtol=0):raise ValueError("common observation geometry moved")
    return networks


def freeze(batch):
    if (batch/"experiment_plan.json").exists():raise ValueError("cannot overwrite frozen experiment")
    for name in ["data_isolation_preflight.json","execution_guard_audit.json"]:
        if not json.loads((batch/name).read_text())["passed"]:raise PermissionError("preflight not passed")
    refs=read_reference(batch/"inputs",json.loads((batch/"source_manifest.json").read_text()),"calibration_reference",role="calibration")
    for g,expected in zip(WINDOWS,[1648.,1449.8181818181818]):
        actual=next(c["mainline_veh_h_lane"] for c in refs["windows"][g]["crossings"] if c["plane_m"]==300)
        if abs(actual-expected)>1e-8:raise PermissionError("input basis not verified")
    fixed=dict(maxSpeed=27.78,speedFactor=1.,speedDev=0.,carFollowModel="Krauss",tau=1.,minGap=2.5,
        accel=2.6,decel=4.5,apparentDecel=4.5,emergencyDecel=9.,sigma=.5,actionStepLength=.1,sigmaStep=1.,
        internal_step_s=.05,recorded_step_s=.1,step_method_ballistic=True,threads=1,laneChangeModel="LC2013",
        communication_enabled=False,source_risk_treatment_enabled=False,information_adoption_enabled=False,ramp_demand=0)
    networks=_networks(batch);fleet=refs["fleet"];inputs=batch/"inputs"
    types=ET.Element("routes")
    for i,f in enumerate(fleet):
        attrs={k:str(fixed[k]) for k in ["maxSpeed","speedFactor","speedDev","carFollowModel","tau","minGap","accel","decel","apparentDecel","emergencyDecel","sigma","actionStepLength","sigmaStep","laneChangeModel"]}
        ET.SubElement(types,"vType",dict(id=f"t{i}",vClass=f["vClass"],length=f'{f["length_m"]:.10f}',**attrs))
    ET.ElementTree(types).write(inputs/"types.rou.xml",encoding="utf-8",xml_declaration=True)
    runs=[]
    for phase,seed in [("phase1",20261019)]:
        rng=np.random.default_rng(seed);uniform=arrival_times(1648,600,"uniform")
        classes=rng.choice(3,size=len(uniform),p=[f["share"] for f in fleet]).tolist()
        for kind in ["uniform","platoon"]:
            arrivals=arrival_times(1648,600,kind);root=ET.Element("routes")
            ET.SubElement(root,"route",dict(id="through",edges="main_0 main_1 main_2"))
            for i,(t,cls) in enumerate(zip(arrivals,classes)):
                ET.SubElement(root,"vehicle",dict(id=f"v{i:05d}",type=f"t{cls}",route="through",depart=f"{t:.1f}",departLane=str(i%3),departPos="base",departSpeed="max"))
            ET.ElementTree(root).write(inputs/f"demand_{kind}_{seed}.rou.xml",encoding="utf-8",xml_declaration=True)
        for condition in ["A","B","C","D"]:
            run_id=f"b1_{condition}_s{seed}";kind="platoon" if condition=="B" else "uniform"
            network=networks[condition]["path"]
            cfg=inputs/(run_id+".sumocfg")
            cfg.write_text(f'''<configuration><input><net-file value="{str(Path(network).relative_to('inputs')).replace(chr(92),'/')}"/><route-files value="types.rou.xml,demand_{kind}_{seed}.rou.xml"/></input><time><begin value="0"/><end value="600"/><step-length value="0.05"/></time><processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/><collision.action value="warn"/></processing><seed value="{seed}"/></configuration>''',encoding="utf-8")
            runs.append(dict(run_id=run_id,condition=condition,phase=phase,seed=seed,tau=1.,minGap=2.5,
                network_path=network,network_version=networks[condition]["version"],config_path=cfg.relative_to(batch).as_posix(),
                demand_path=f"inputs/demand_{kind}_{seed}.rou.xml",vtype_path="inputs/types.rou.xml",changed_parameter=None))
    prechecks=[]
    for condition in ["A","C","D"]:
        spec=next(r for r in runs if r["condition"]==condition)
        r=subprocess.run([_sumo_binary(),"-c",str(batch/spec["config_path"]),"--end","0.1","--no-step-log","true"],capture_output=True,text=True,timeout=30)
        prechecks.append(dict(condition=condition,simulated_s=.1,departed=0,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:raise ValueError("empty network loader precheck failed")
    plan=dict(result_id=RESULT_ID,mode=MODE,scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,
        reality_coverage_accepted=False,gate="pending_simulation_sample",protocol_lock_allowed=False,stage_1_1_allowed=False,
        tolerances="Tolerance Not Yet Justified",energy_distance_upper_bound="Not Identifiable",
        duration_s=600.,main_flow_veh_h_lane=1648.,unexecuted_secondary_flow_veh_h_lane=1449.8181818181818,
        fixed=fixed,fleet=fleet,runs=runs,networks=networks,windows=dict(all_slices_retained=True,bins_s=60,warmup_s_approved=None),
        initial_vehicles=0,local_space=dict(edge="main_1",start_m=50,end_m=250,lanes=3,lane_km=.6),
        boundary=dict(A="uniform/open",B="30s cycle arrivals compressed to first15s; same IDs/classes/order/count",
            C="static service at hwy_j2:23.8green/6.2yellow/30red; normal signal compliance, no vehicle intervention",
            D="main2 two lanes; main1 lane2 must change to continuing lane before end; no duplicate merge connection"),
        revision=2,task_prior_attempts=1,task_max_runs=8,
        limits=dict(max_runs=4,batch_wall_s=7200,per_run_wall_s=600,memory_bytes=6*1024**3,artifact_bytes=4*1024**3),
        stop_rules=dict(any_blocker_stops_entire_batch=True,pending="last3 end queues nondecreasing and end>max(20,10%scheduled) blocks unless C/D with connected slow queue to inlet >=25% of final60s; spillback warns",
            slow_queue="speed<5m/s;50m normal-edge bins with>=2 slow vehicles; connected upstream from last bin before hwy_j2; descriptive only",
            conflicts="collision/teleport/conservation/identity/cadence/physical gap/runtime settings/SHA/source/resource failures block"),
        cost_estimate="B0 ~28.5s/300s freeflow;600s ~60s freeflow, provision~300s/run constrained full TTC/P2; hard limits not guarantees",
        local_formal_p2="Unresolved",postprocessing_scope="descriptive renderer separate from frozen execution/measurement; may be repaired after closure with its own source SHA, never changes inputs or core measurements",created_utc=_utc_now())
    for run in runs:
        run["input_sha256"]={p:_sha256_file(batch/p) for p in [run["network_path"],run["config_path"],run["demand_path"],run["vtype_path"]]}
    _write_json(batch/"network_variant_manifest.json",dict(networks=networks,loader_prechecks=prechecks,observation_support_equal=True,capacity_matched=False))
    _write_json(batch/"boundary_condition_manifest.json",dict(boundaries=plan["boundary"],real_arrival_or_supply_identified=False,signal_yellow_basis_s=27.78/4.5,no_vehicle_command_interventions=True))
    frozen={p.relative_to(batch).as_posix():_sha256_file(p) for d in [batch/"runtime",batch/"inputs"] for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name!="stage_0_5_b1_analysis.py"}
    for name in ["source_manifest.json","isolation_policy.json","data_isolation_preflight.json","execution_guard_audit.json","network_variant_manifest.json","boundary_condition_manifest.json"]:frozen[name]=_sha256_file(batch/name)
    plan["frozen_files"]=frozen
    _write_json(batch/"experiment_plan.json",plan)
    (batch/"PLAN_SHA256").write_text(_sha256_file(batch/"experiment_plan.json")+"  experiment_plan.json\n",encoding="utf-8",newline="\n")
    revision=json.loads((batch/"plan_revision_audit.json").read_text())
    _write_json(batch/"execution_ledger.json",dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),started_epoch=revision["task_started_epoch"],runs=[dict(run_id=r["run_id"],status="not_attempted") for r in runs],closed=False))
    print(json.dumps(dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),runs=4,networks={k:v["sha256"] for k,v in networks.items()})),flush=True)


def read_plan(batch):
    digest=(batch/"PLAN_SHA256").read_text().split()[0]
    if _sha256_file(batch/"experiment_plan.json")!=digest:raise ValueError("plan SHA mismatch")
    plan=json.loads((batch/"experiment_plan.json").read_text())
    verify_frozen(batch,plan["frozen_files"])
    if len(plan["runs"])!=4 or plan["fixed"]["tau"]!=1 or plan["fixed"]["minGap"]!=2.5:raise ValueError("frozen matrix mismatch")
    return plan


def execute_phase(batch,phase):
    ledger=json.loads((batch/"execution_ledger.json").read_text())
    if ledger["closed"]:raise PermissionError("B1 batch already closed; no retries or replacements")
    try:
        plan=read_plan(batch)
        read_reference(batch/"inputs",json.loads((batch/"source_manifest.json").read_text()),"calibration_reference",role="calibration")
    except Exception as exc:
        ledger.update(closed=True,stop_reason="frozen/source verification failed",failure=str(exc))
        _write_json(batch/"execution_ledger.json",ledger);raise
    if phase=="phase2":
        decision=json.loads((batch/"phase1_checkpoint.json").read_text())
        if not decision["phase2_allowed"] or decision["plan_sha256"]!=ledger["plan_sha256"]:raise PermissionError("phase2 checkpoint did not admit this plan")
    specs=[r for r in plan["runs"] if r["phase"]==phase]
    if any(next(e for e in ledger["runs"] if e["run_id"]==r["run_id"])["status"]!="not_attempted" for r in specs):raise ValueError("no B1 retries")
    if ledger["started_epoch"] is None:ledger["started_epoch"]=time.time()
    remaining=plan["limits"]["batch_wall_s"]-(time.time()-ledger["started_epoch"])
    if remaining<=0:
        ledger.update(closed=True,stop_reason="batch wall limit");_write_json(batch/"execution_ledger.json",ledger);return
    _write_json(batch/"execution_ledger.json",ledger)
    commands=[]
    for r in specs:
        commands.append(dict(run_id=r["run_id"],verify_files={str(batch/p):h for p,h in r["input_sha256"].items()},
            command=[sys.executable,"-S",str(batch/"runtime/code/scripts/run_stage_0_5_boundary_bottleneck.py"),"worker","--batch",str(batch),"--run-id",r["run_id"]]))
    limits=dict(plan["limits"]);limits["batch_wall_s"]=remaining
    result=execute_commands(batch/"runs",commands,limits=limits)
    for row in result["runs"]:
        target=next(r for r in ledger["runs"] if r["run_id"]==row["run_id"]);target.update(row)
        if (batch/"runs"/row["run_id"]/"summary.json").exists():target["summary_sha256"]=_sha256_file(batch/"runs"/row["run_id"]/"summary.json")
    if result["stop_reason"]:ledger.update(closed=True,stop_reason=result["stop_reason"])
    if phase=="phase2" and not result["stop_reason"]:ledger.update(closed=True,stop_reason="all eight predefined runs completed")
    if phase=="phase1" and len(plan["runs"])==4 and not result["stop_reason"]:ledger.update(closed=True,stop_reason="all four V2 runs completed; task total5 including failed V1; no partial second seed")
    ledger["elapsed_wall_s"]=time.time()-ledger["started_epoch"]
    _write_json(batch/"execution_ledger.json",ledger)


def checkpoint(batch):
    plan=read_plan(batch);ledger=json.loads((batch/"execution_ledger.json").read_text())
    first=[r for r in ledger["runs"] if next(s for s in plan["runs"] if s["run_id"]==r["run_id"])["phase"]=="phase1"]
    first_valid=len(first)==4 and all(r["status"] in ["completed_valid","completed_with_diagnostic_warning"] for r in first)
    allowed=False # V2 has only one complete seed; no partial second-seed matrix.
    rows=[]
    for r in first:
        p=batch/"runs"/r["run_id"]/"summary.json"
        if p.exists():
            s=json.loads(p.read_text());rows.append(dict(run_id=r["run_id"],condition=s["condition"],speed=s["local_metrics"]["speed_mps"]["mean"],density=s["local_density_veh_km_lane"],
                low_speed=s["local_low_speed_fraction"],pending=s["accounting"]["unserved_at_end"],blockers=s["engineering_blockers"],warnings=s["diagnostic_warnings"]))
        else:rows.append(r)
    record=dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),created_utc=_utc_now(),phase2_allowed=allowed,
        first_batch_engineering_valid=first_valid,authorization="V2 four-condition single-seed plan closed; no second seed scheduled within cumulative budget",first_batch=rows,
        isolation_preflight_passed=True,scientific_claim_eligible=False)
    _write_json(batch/"phase1_checkpoint.json",record)
    print(json.dumps(record),flush=True)


def dispatch(repo,batch,command,run_id=None):
    if command=="prepare":return prepare(repo,batch)
    _environment(batch)
    if command in ["preflight","tests"]:return preflight(batch)
    if command=="freeze":return freeze(batch)
    if command=="worker":return run_worker(batch,run_id)
    if command=="checkpoint":return checkpoint(batch)
    if command in ["phase1","phase2"]:return execute_phase(batch,command)
    if command=="analyze":
        from .stage_0_5_b1_analysis import finalize
        return finalize(batch)


def analyze_run(out: Path, plan: dict, spec: dict, run_audit: dict) -> dict:
    s=pd.read_parquet(out/"state.parquet")
    times=s.sort_values(["vehicle_id","time_s"]).groupby("vehicle_id").time_s.diff().dropna()
    cadence_error=float((times-.1).abs().max()) if len(times) else None
    duplicate=int(s.duplicated(["incarnation_id","time_s"]).sum())
    local=s[local_mask(s)]
    reliable=local.reliable_following_eligible
    stats={k:_dist(local.loc[mask,k]) for k,mask in [
        ("speed_mps",pd.Series(True,index=local.index)),("acceleration_mps2",pd.Series(True,index=local.index)),
        ("net_gap_m",reliable & local.net_gap_m.gt(0)),("closing_speed_mps",reliable),
        ("ttc_s",local.ttc_valid)]}
    stats["low_speed_gap_m"]=_dist(local.loc[reliable & local.speed_mps.lt(5) & local.net_gap_m.gt(0),"net_gap_m"])
    exposure=edge_exposure(s)
    if spec["run_id"]==plan["runs"][0]["run_id"]:
        from .stage_0_5_sumo import compute_exposure
        slow=compute_exposure(s,recorded_observation_step_s=.1)
        differences={k:exposure[k]-slow[k] for k in ["reliable_following_exposure_s","p2_evaluable_following_exposure_s","reliable_closing_exposure_s"]}
        _write_json(out/"core_exposure_equivalence.json",dict(differences_s=differences,maximum_allowed_float_error_s=1e-6,core_rules_unchanged=True))
        if max(abs(x) for x in differences.values())>1e-6: raise ValueError("full-run exposure differs from existing core")
    events,formal=extract_sumo_formal_p2_events(s,recorded_observation_step_s=.1)
    events.to_parquet(out/"full_network_exploratory_p2.parquet",index=False)
    frames=pd.read_csv(out/"traffic_frames.csv")
    bins=[]
    for a in range(0,600,60):
        f=frames[frames.time_s.gt(a)&frames.time_s.le(a+60)]
        c=local[local.time_s.gt(a)&local.time_s.le(a+60)]
        if f.empty: continue
        bins.append(dict(start_s=a,end_s=a+60,observed_s=len(f)*.1,
            density_veh_km_lane=float(f.local_vehicles.mean()/.6),
            mean_speed_mps=float(c.speed_mps.mean()) if len(c) else None,
            low_speed_fraction=float(c.speed_mps.lt(5).mean()) if len(c) else None,
            mean_present=float(f.present.mean()),pending_start=int(f.pending.iloc[0]),pending_end=int(f.pending.iloc[-1]),
            pending_max=int(f.pending.max()),inserted=int(f.inserted_step.sum()),arrived=int(f.arrived_step.sum()),
            crossings=int(f.local_crossings.sum()),initial_present=0,initial_local_share=0.,
            conservation_max_abs=int(f.conservation_residual.abs().max())))
    vals=s[s.net_gap_crosscheck_residual_m.notna()].net_gap_crosscheck_residual_m
    fingerprint=s[["time_s","vehicle_id","edge_id","lane_id","longitudinal_position_m",
        "speed_mps","acceleration_mps2","leader_id","net_gap_m","closing_speed_mps","ttc_s"]].copy()
    fingerprint=fingerprint.sort_values(["time_s","vehicle_id"])
    digest=hashlib.sha256(pd.util.hash_pandas_object(fingerprint,index=False).to_numpy().tobytes()).hexdigest()
    ten=[]
    for a in range(0,600,10):
        c=local[local.time_s.gt(a)&local.time_s.le(a+10)]
        ten.append(float(c.speed_mps.mean()) if len(c) else None)
    sustained=any(all(v is not None and v<5 for v in ten[i:i+3]) for i in range(len(ten)-2))
    summary=dict(**spec,status=run_audit["status"],failure=run_audit["failure"],mode=MODE,
        scientific_claim_eligible=False,observed_s=len(frames)*.1,planned_s=600.,numerical=run_audit["numerical"],runtime=run_audit["runtime"],
        accounting=run_audit["accounting"],plan_sha256=_sha256_file(out.parent.parent/"experiment_plan.json"),
        local_metrics=stats,local_density_veh_km_lane=local_density(len(local),len(frames)*.1),
        local_low_speed_fraction=float(local.speed_mps.lt(5).mean()) if len(local) else None,
        local_positive_closing_fraction=float(local.loc[reliable,"closing_speed_mps"].gt(1e-3).mean()) if reliable.any() else None,
        local_ttc_valid_fraction=float(local.ttc_valid.mean()) if len(local) else None,
        local_following_fraction=float(reliable.mean()) if len(local) else None,
        global_measurement_status_counts={str(k):int(v) for k,v in s.measurement_status.value_counts().items()},
        full_network_p2=dict(events=len(events),**exposure,
            event_rate_per_evaluable_vehicle_hour=len(events)/exposure["p2_evaluable_following_vehicle_hours"] if exposure["p2_evaluable_following_vehicle_hours"] else None,
            event_boundaries=events[[k for k in ["vehicle_id","leader_id","event_start_s","event_end_s","event_confirm_s","ttc_min_s","exit_reason"] if k in events]].to_dict("records"),
            formal_adapter_status=formal["equivalence_status"],authorization="B0 exploratory computation only; no measurement Gate"),
        local_stratum_formal_p2_rate="Unresolved",time_bins=bins,
        cadence_max_abs_error_s=cadence_error,duplicate_identity_time_rows=duplicate,
        net_gap_geometry_checked_rows=len(vals),net_gap_geometry_max_abs_m=float(vals.abs().max()) if len(vals) else None,
        closing_sign_max_error=float((s.closing_speed_mps-(s.speed_mps-s.leader_speed_mps)).abs().max()),
        state_fingerprint=digest,state_rows=len(s),state_sha256=_sha256_file(out/"state.parquet"),
        low_speed_10s_means=ten,sustained_local_low_speed_30s=sustained,
        local_crossings=int(frames.local_crossings.sum()),mainline_lane_changes=int(frames.lane_changes.sum()),
        insertion_delays_s=_dist(pd.read_csv(out/"departures.csv").delay_s))
    blockers=[]
    if summary["status"]!="completed":blockers.append("run_failure")
    if cadence_error is None or cadence_error>1e-6 or duplicate:blockers.append("cadence_or_identity")
    if summary["net_gap_geometry_max_abs_m"] is None or summary["net_gap_geometry_max_abs_m"]>1e-6:blockers.append("net_gap_geometry")
    if summary["closing_sign_max_error"]>1e-8:blockers.append("closing_sign")
    if run_audit["accounting"]["conservation_residual"] or frames.conservation_residual.abs().max():blockers.append("conservation")
    if run_audit["collisions"] or run_audit["teleports"]:blockers.append("collision_or_teleport")
    if not summary["numerical"].get("verified"):blockers.append("runtime_settings")
    if summary["global_measurement_status_counts"].get("missing",0) or summary["global_measurement_status_counts"].get("invalid",0):blockers.append("measurement_quality")
    warnings=[]
    if frames.onroad_low_vehicles.max()>0:warnings.append("onroad_low_speed_observed")
    if frames.pending.max()>0:warnings.append("external_pending_observed")
    tail=frames[frames.time_s.gt(540)]
    spillback=float(tail.queue_connected_front_m.le(50).mean())>=.25
    tails=[b["pending_end"] for b in bins[-3:]]
    persistent=tails==sorted(tails) and tails[-1]>max(20,.1*summary["accounting"]["scheduled_vehicles"])
    if persistent:
        if spec["condition"] in ["C","D"] and spillback:warnings.append("documented_connected_onroad_spillback")
        else:blockers.append("persistent_external_demand_without_documented_spillback")
    summary.update(engineering_blockers=blockers,diagnostic_warnings=warnings,condition=spec["condition"],
        spillback_qualified=spillback,queue_front_min_m=float(frames.queue_connected_front_m.min()) if frames.queue_connected_front_m.notna().any() else None,
        onroad_low_vehicle_s=float(frames.onroad_low_vehicles.sum()*.1),
        queue_time_series_columns=["queue_connected_front_m","upstream_low_vehicles","onroad_low_vehicles"],
        status=classify_result(1 if run_audit["failure"] else 0,True,blockers,warnings))
    _write_json(out/"summary.json",summary)
    return summary


def run_worker(batch: Path, run_id: str) -> None:
    """One frozen run; outer batch controller enforces hard wall/memory/disk caps."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    plan=read_plan(batch)
    spec=next(r for r in plan["runs"] if r["run_id"]==run_id)
    out=batch/"runs"/run_id
    if (out/"summary.json").exists(): raise ValueError("refusing to overwrite run")
    out.mkdir(exist_ok=True)
    start=time.perf_counter()
    _ensure_traci_importable()
    import traci
    import traci.constants as c
    demand=ET.parse(batch/spec["demand_path"]).getroot().findall("vehicle")
    scheduled={v.attrib["id"]:float(v.attrib["depart"]) for v in demand}
    types={v.attrib["id"]:int(v.attrib["type"][1:]) for v in demand}
    grid=np.array(sorted(scheduled.values()))
    departed=set();arrived=set();collisions=set();teleports=set();present=set();departures=[]
    frames=[];rows=[];counts={};prev_record={};audit_prev={};ballistic=[];row_count=0;writer=None
    numerical={};failure=None;conn=None;tick_insert=0;tick_exit=0
    def flush():
        nonlocal rows,writer,row_count
        if not rows: return
        m=compute_sumo_measurements(pd.DataFrame(rows))
        table=pa.Table.from_pandas(m,preserve_index=False)
        if writer is None: writer=pq.ParquetWriter(out/"state.parquet",table.schema,compression="zstd")
        writer.write_table(table.cast(writer.schema));row_count+=len(rows);rows=[]
    command=[str(Path(traci.__file__).resolve().parents[2]/"bin/sumo.exe"),"-c",str((batch/spec["config_path"]).resolve()),
        "--no-step-log","true","--duration-log.disable","true","--error-log",str((out/"sumo_errors.log").resolve())]
    # Resolve through the same existing executable lookup used by Stage0.5.
    from .stage_0_5_sumo import _sumo_binary
    command[0]=_sumo_binary()
    _write_json(out/"run_config.json",dict(plan_sha256=_sha256_file(batch/"experiment_plan.json"),run=spec,fixed=plan["fixed"],command=command))
    try:
        traci.start(command,label=run_id)
        conn=traci.getConnection(run_id)
        options={k:conn.simulation.getOption(k) for k in ["step-method.ballistic","step-length","seed","time-to-teleport","threads","random"]}
        actual_types={}
        for i,fleet in enumerate(plan["fleet"]):
            tid=f"t{i}"
            actual_types[tid]={k:getattr(conn.vehicletype,method)(tid) for k,method in dict(
                tau="getTau",minGap="getMinGap",actionStepLength="getActionStepLength",maxSpeed="getMaxSpeed",
                length="getLength",vClass="getVehicleClass",sigma="getImperfection",accel="getAccel",decel="getDecel",
                apparentDecel="getApparentDecel",emergencyDecel="getEmergencyDecel",speedFactor="getSpeedFactor",speedDev="getSpeedDeviation").items()}
        conn.simulation.saveState(str((out/"runtime_initial_state.xml").resolve()))
        echo={v.attrib["id"]:v.attrib for v in ET.parse(out/"runtime_initial_state.xml").getroot().iter("vType")}
        checks=[]
        checks.append(options["step-method.ballistic"].lower() in ["true","1"])
        checks.append(abs(float(options["step-length"])-.05)<1e-10)
        checks.append(int(options["seed"])==spec["seed"])
        checks.append(int(options["threads"])==1)
        checks.append(options["random"].lower() in ["false","0"])
        checks.append(abs(conn.simulation.getDeltaT()-.05)<1e-10)
        for i,fleet in enumerate(plan["fleet"]):
            values=actual_types[f"t{i}"]
            expected={k:plan["fixed"][k] for k in ["actionStepLength","maxSpeed","sigma","accel","decel","apparentDecel","emergencyDecel","speedFactor","speedDev"]}
            expected.update(tau=spec["tau"],minGap=spec["minGap"],length=fleet["length_m"])
            checks.extend(abs(values[k]-v)<1e-8 for k,v in expected.items())
            checks.append(values["vClass"]==fleet["vClass"])
            checks.append(abs(float(echo.get(f"t{i}",{}).get("sigmaStep","nan"))-1)<1e-10)
        numerical=dict(options=options,actual_types=actual_types,runtime_vtype_echo=echo,
            verified=bool(all(checks)),checks=len(checks),sigmaStep_evidence="runtime save-state vType echo; TraCI has no direct sigmaStep getter")
        numerical["sumo_version"]=conn.getVersion()
        if spec["condition"]=="C":
            logic=next(l for l in conn.trafficlight.getAllProgramLogics("hwy_j2") if l.programID=="b1_supply_v1")
            numerical["service_program"]=[dict(duration=p.duration,state=p.state) for p in logic.phases]
            if [p.duration for p in logic.phases]!=[23.8,6.2,30.]:raise ValueError("supply program mismatch")
        _write_json(out/"runtime_numerical_audit.json",numerical)
        if not numerical["verified"]: raise ValueError("declared runtime numerical/type settings did not take effect")
        sim_vars=(c.VAR_TIME,c.VAR_DEPARTED_VEHICLES_IDS,c.VAR_ARRIVED_VEHICLES_IDS,c.VAR_COLLIDING_VEHICLES_IDS,c.VAR_TELEPORT_STARTING_VEHICLES_IDS,c.VAR_PENDING_VEHICLES)
        conn.simulation.subscribe(sim_vars)
        variables=(c.VAR_SPEED,c.VAR_ACCELERATION,c.VAR_POSITION,c.VAR_LANE_ID,c.VAR_LANEPOSITION,c.VAR_ROAD_ID,c.VAR_LEADER)
        for step in range(1,12001):
            conn.simulationStep()
            sv=conn.simulation.getSubscriptionResults()
            actual_time=float(sv[c.VAR_TIME])
            if abs(actual_time-step*.05)>1e-6: raise ValueError("SUMO runtime clock disagrees with declared cadence")
            now=round(actual_time,6)
            new=sv[c.VAR_DEPARTED_VEHICLES_IDS];gone=sv[c.VAR_ARRIVED_VEHICLES_IDS]
            collisions.update(sv[c.VAR_COLLIDING_VEHICLES_IDS]);teleports.update(sv[c.VAR_TELEPORT_STARTING_VEHICLES_IDS])
            if collisions or teleports: raise ValueError("unexpected collision or teleport; preserve partial run")
            for vid in new:
                if vid in departed: raise ValueError("vehicle identity reused")
                departed.add(vid);tick_insert+=1
                departures.append(dict(vehicle_id=vid,scheduled_s=scheduled[vid],departed_s=now,delay_s=now-scheduled[vid],initial=False))
                conn.vehicle.subscribe(vid,variables,parameters={c.VAR_LEADER:("d",1000.)})
            arrived.update(gone);tick_exit+=len(gone)
            data=conn.vehicle.getAllSubscriptionResults()
            # Independent positional integration check on a fixed upstream ID subset.
            for vid in sorted(data)[:10]:
                v=data[vid];current=(v[c.VAR_ROAD_ID],v[c.VAR_LANE_ID],v[c.VAR_LANEPOSITION],v[c.VAR_SPEED],now)
                prior=audit_prev.get(vid)
                if prior and current[:2]==prior[:2] and abs(now-prior[4]-.05)<1e-8 and abs(current[3]-prior[3])>1e-5:
                    ballistic.append(abs(current[2]-prior[2]-(current[3]+prior[3])*.5*.05))
                audit_prev[vid]=current
            if step%2: continue
            present=set(data);nlocal=0;nlow=0;crossings=0;lane_changes=0;speed_sum=0;local_speed_sum=0;halted=0
            slow_positions=[];upstream_low=0;onroad_low=0
            for vid,v in sorted(data.items()):
                road=v[c.VAR_ROAD_ID];lane=v[c.VAR_LANE_ID];pos=v[c.VAR_LANEPOSITION];speed=v[c.VAR_SPEED]
                islocal=road=="main_1" and 50<=pos<250
                onroad_low+=speed<5
                if road in ["main_0","main_1"] and speed<5:
                    upstream_low+=road=="main_0" and pos<50
                    offset=0 if road=="main_0" else plan["networks"][spec["condition"]]["edge_lengths"]["main_0"]
                    slow_positions.append(offset+pos)
                nlocal+=islocal;nlow+=islocal and speed<5;halted+=speed<.1
                speed_sum+=speed;local_speed_sum+=speed if islocal else 0
                previous=prev_record.get(vid)
                if previous and previous[0]==road:
                    crossings+=road=="main_1" and previous[2]<150<=pos
                    lane_changes+=previous[1]!=lane
                prev_record[vid]=(road,lane,pos)
                leader=v[c.VAR_LEADER];lid=leader[0] if leader and leader[0] else None
                lv=data.get(lid);gap=leader[1]+spec["minGap"] if lid else np.nan
                residual=np.nan
                if lv and lv[c.VAR_ROAD_ID]==road and lv[c.VAR_LANE_ID]==lane:
                    physical=lv[c.VAR_LANEPOSITION]-plan["fleet"][types[lid]]["length_m"]-pos
                    residual=gap-physical
                obs=counts.get(vid,0);counts[vid]=obs+1
                rows.append(dict(run_id=run_id,scenario_id="us101_highway_baseline",fixture_id="b1_no_message",
                    experiment_mode="no_message_baseline",configured_seed=spec["seed"],simulation_step=step,
                    time_s=now,observation_index=obs,vehicle_id=vid,incarnation_id=run_id+"|"+vid,trajectory_id=run_id+"|"+vid,
                    edge_id=road,lane_id=lane,longitudinal_position_m=pos,x_m=v[c.VAR_POSITION][0],y_m=v[c.VAR_POSITION][1],
                    speed_mps=speed,acceleration_mps2=v[c.VAR_ACCELERATION],vehicle_type=f"t{types[vid]}",initial_vehicle=False,
                    vehicle_length_m=plan["fleet"][types[vid]]["length_m"],follower_min_gap_m=spec["minGap"],
                    leader_id=lid,leader_incarnation_id=run_id+"|"+lid if lv else None,
                    leader_identity_status="observed" if lv else "unresolved" if lid else "not_applicable",
                    leader_speed_mps=lv[c.VAR_SPEED] if lv else np.nan,leader_traci_distance_m=leader[1] if lid else np.nan,
                    net_gap_m=gap,net_gap_crosscheck_residual_m=residual))
            pending=len(sv[c.VAR_PENDING_VEHICLES])
            gate=sum(plan["networks"][spec["condition"]]["edge_lengths"][e] for e in ["main_0","main_1"])
            histogram=np.bincount((np.array(slow_positions)//50).astype(int),minlength=int(gate//50)+1)
            cell=int((gate-1)/50);front=np.nan
            while cell>=0 and histogram[cell]>=2:
                front=cell*50.;cell-=1
            frames.append(dict(time_s=now,scheduled_due=int(np.searchsorted(grid,now,side="right")),
                departed=len(departed),arrived=len(arrived),present=len(present),pending=pending,
                inserted_step=tick_insert,arrived_step=tick_exit,local_crossings=crossings,lane_changes=lane_changes,
                local_vehicles=nlocal,local_low_speed_vehicles=nlow,halted=halted,
                speed_sum=speed_sum,local_speed_sum=local_speed_sum,
                conservation_residual=len(departed)-len(arrived)-len(present),initial_present=0,
                queue_connected_front_m=front,upstream_low_vehicles=upstream_low,onroad_low_vehicles=onroad_low,
                tls_state=conn.trafficlight.getRedYellowGreenState("hwy_j2") if spec["condition"]=="C" else "none"))
            if frames[-1]["conservation_residual"]:raise ValueError("vehicle conservation failed")
            tick_insert=tick_exit=0
            if step%600==0: flush()
            if time.perf_counter()-start>plan["limits"]["per_run_wall_s"]-5: raise TimeoutError("worker wall cap")
    except Exception as exc:
        failure=f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try: conn.close()
            except Exception: pass
        flush()
        if writer is not None: writer.close()
    pd.DataFrame(frames).to_csv(out/"traffic_frames.csv",index=False)
    pd.DataFrame(departures,columns=["vehicle_id","scheduled_s","departed_s","delay_s","initial"]).to_csv(out/"departures.csv",index=False)
    numerical["ballistic_displacement_checked_edges"]=len(ballistic)
    numerical["ballistic_displacement_max_abs_m"]=float(max(ballistic)) if ballistic else None
    if not ballistic or max(ballistic)>1e-6: numerical["verified"]=False
    run_audit=dict(status="failed" if failure else "completed",failure=failure,mode=MODE,
        numerical=numerical,accounting=input_accounting(len(demand),departed,arrived,present,initial_ids=set()),
        collisions=sorted(collisions),teleports=sorted(teleports),
        runtime=dict(sumo_recording_wall_s=time.perf_counter()-start,output_rows=row_count))
    _write_json(out/"run_audit.json",run_audit)
    if row_count:
        summary=analyze_run(out,plan,spec,run_audit)
        summary["runtime"]["total_worker_wall_s"]=time.perf_counter()-start
        _write_json(out/"summary.json",summary)
        print(json.dumps(dict(run_id=run_id,status=summary["status"],blockers=summary["engineering_blockers"],
            speed=summary["local_metrics"]["speed_mps"]["mean"],density=summary["local_density_veh_km_lane"],
            p2=summary["full_network_p2"]["events"],wall_s=summary["runtime"]["total_worker_wall_s"])),flush=True)
    elif failure: raise RuntimeError(failure)

