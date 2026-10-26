"""Stage only reviewed controller sources/runtime and wholly synthetic inputs.

This script never starts SUMO or a capsule. Probe and smoke launches are separate
explicit commands. Existing stages are immutable; failures are retained.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_0_5_native_capsule_v4 import canonical,sha,require,SMOKE_SCHEMA,SMOKE_TASK

SOURCES=["stage_0_5_execution_v2.py","stage_0_5_linux_isolation.py","stage_0_5_isolation_admission.py",
    "stage_0_5_identity_observation.py","stage_0_5_input_fidelity.py","stage_0_5_isolation_v2.py",
    "stage_0_5_research_ledger.py","stage_0_5_linux_runtime_v4.py","stage_0_5_native_capsule_v4.py",
    "stage_0_5_linux_controller_v4.py","stage_0_5_linux_execution_v4.py","probe_stage_0_5_linux_isolation.py"]
STAGE_PARENT=Path("/home/shen/AAD/code/tmp")


def write(path,value):
    with Path(path).open("xb") as f:f.write(value if isinstance(value,bytes) else canonical(value)+b"\n")


def stage(destination,runtime_root):
    destination=Path(destination)
    require(destination.parent==STAGE_PARENT and destination.name.startswith("stage05_v4_"),"exclusive_authorized_stage_required")
    require(not any(p.is_symlink() for p in [destination,*destination.parents]),"symlink_stage_forbidden")
    destination.mkdir(exist_ok=False)
    source=Path(__file__).resolve().parent
    for name in SOURCES:write(destination/name,(source/name).read_bytes())
    from stage_0_5_linux_runtime_v4 import runtime_manifest
    runtime=runtime_manifest(runtime_root)
    write(destination/"runtime_manifest.json",runtime)
    source_hashes={n:sha(destination/n) for n in SOURCES}
    record=dict(source_sha256=source_hashes,source_closure_sha256=hashlib.sha256(canonical(source_hashes)).hexdigest(),
        runtime_manifest_sha256=sha(destination/"runtime_manifest.json"),
        runtime_root=str(runtime_root),working_directory=os.getcwd(),SUMO_launches=0,TraCI_connections=0,new_research_trajectories=0)
    write(destination/"staging_record.json",record)
    print(json.dumps(record),flush=True)


def smoke(stage_path,run_id):
    base=Path(stage_path)
    require(base.parent==STAGE_PARENT and base.name.startswith("stage05_v4_"),"authorized_stage_required")
    import re
    require(re.fullmatch(r"SMOKE_V4_[A-Za-z0-9_]+",run_id) is not None,"unique_engineering_run_id_required")
    runtime_path=base/"runtime_manifest.json";runtime=json.loads(runtime_path.read_bytes())
    record=json.loads((base/"staging_record.json").read_bytes())
    require(record["source_sha256"]=={n:sha(base/n) for n in SOURCES},"staging_source_drift")
    require(record["runtime_manifest_sha256"]==sha(runtime_path),"staging_runtime_manifest_drift")
    from stage_0_5_linux_runtime_v4 import check_runtime
    check_runtime(runtime)
    capability=base/"probe_results/record.json"
    from stage_0_5_isolation_admission import probe_checks
    probe=json.loads(capability.read_bytes())
    require(probe["guard_sha256"]==sha(base/"stage_0_5_linux_isolation.py") and all(probe_checks(probe).values()),"current_kernel_probe_required")
    inputs=base/"smoke_inputs";inputs.mkdir(exist_ok=False)
    network=b'''<net version="1.20"><location netOffset="0.00,0.00" convBoundary="0.00,0.00,500.00,0.00" origBoundary="0.00,0.00,500.00,0.00" projParameter="!"/>
<edge id="synth_main" from="synth_start" to="synth_end" priority="1"><lane id="synth_main_0" index="0" speed="10" length="500" shape="0.00,0.00 500.00,0.00"/></edge>
<junction id="synth_start" type="dead_end" x="0" y="0" incLanes="" intLanes="" shape="0,0 0,0"/>
<junction id="synth_end" type="dead_end" x="500" y="0" incLanes="synth_main_0" intLanes="" shape="500,0 500,0"/></net>'''
    routes=b'<routes><vType id="synth_type" length="4.5" maxSpeed="10" sigma="0"/><route id="synth_route" edges="synth_main"/><vehicle id="synth_vehicle" type="synth_type" route="synth_route" depart="0.05" departLane="0" departPos="0" departSpeed="0"/></routes>'
    config=b'''<configuration><input><net-file value="network.net.xml"/><route-files value="routes.rou.xml"/></input>
<time><begin value="0"/><end value="3"/><step-length value="0.05"/></time><processing><step-method.ballistic value="true"/><threads value="1"/></processing>
<output><fcd-output value="fcd.xml"/><device.fcd.period value="0.1"/><summary-output value="summary.xml"/><tripinfo-output value="tripinfo.xml"/><tripinfo-output.write-unfinished value="true"/><tripinfo-output.write-undeparted value="true"/></output><seed value="1"/></configuration>'''
    for name,data in [("network.net.xml",network),("routes.rou.xml",routes),("run.sumocfg",config)]:write(inputs/name,data)
    # This engineering budget is stricter than the research budget and does not
    # alter its immutable limits or consume a scientific ledger attempt.
    limits=dict(per_attempt_wall_s=30,process_tree_rss_bytes=1024**3,task_output_bytes=16*1024**2,
        min_free_c_bytes=5*1024**3,min_free_d_bytes=14*1024**3,min_available_memory_bytes=4*1024**3,supervision_poll_s=.5)
    run=dict(id=run_id,duration_s=3,internal_step_s=.05,seed=1,
        supply_target_lanes=["synth_main_0"],lane_speed_schedule=[dict(start_s=0,end_s=1,speed_mps=10),dict(start_s=1,end_s=2,speed_mps=5),dict(start_s=2,end_s=3,speed_mps=10)],
        capsule_input_sha256={n:sha(inputs/n) for n in ["network.net.xml","routes.rou.xml","run.sumocfg"]},single_attempt_limits=limits)
    # Exercise the same static identity classifier used by the controller before
    # preparing a launch. A synth_* vehicle is noninitial and cannot depart at 0.
    from stage_0_5_input_fidelity import inventory
    inventory(routes)
    from stage_0_5_native_capsule_v4 import smoke_inputs
    smoke_inputs(run,{"network.net.xml":network,"routes.rou.xml":routes,"run.sumocfg":config})
    sources={n:str(base/n) for n in SOURCES}
    from stage_0_5_linux_runtime_v4 import make_policy
    path,policy=make_policy(base/"smoke_capsule",runtime,runtime_path,sources,{n:str(inputs/n) for n in run["capsule_input_sha256"]},run,accepted_build=False,capability_record=capability)
    proposal=dict(schema=SMOKE_SCHEMA,task_id=SMOKE_TASK,runs=[run],capsule_policy_path=str(path),capsule_policy_sha256=sha(path),
        status="PREPARED / AWAITING_EXPLICIT_AUTHORIZATION",
        execution_plan=dict(maximum_attempts=1,automatic_retry=False,workers=1,
            maximum_SUMO_version_processes=1,maximum_SUMO_simulation_processes=1,maximum_real_TraCI_connections=1,
            version_timeout_s=10,broker_wall_s=30,coordinator_timeout_s=60),
        runtime_manifest_path=str(runtime_path),runtime_manifest_sha256=sha(runtime_path),runtime=runtime,
        controller_source_sha256={n:sha(p) for n,p in sources.items()},single_attempt_limits=limits,kernel_probe_sha256=sha(capability),
        native_environment=dict(policy["environment"],PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1"))
    proposal_path=base/"smoke_proposal.json";write(proposal_path,proposal)
    approval=dict(task_id=SMOKE_TASK,run_id=run["id"],proposal_sha256=sha(proposal_path),engineering_authorized=False,
        decision_record="Pending a new exact single-run engineering authorization; preparation never migrates prior permission")
    write(base/"smoke_envelope.json",dict(proposal_path=str(proposal_path),proposal_sha256=sha(proposal_path),run_id=run["id"],approval=approval))
    print(json.dumps(dict(proposal_sha256=sha(proposal_path),envelope_path=str(base/"smoke_envelope.json"),envelope_sha256=sha(base/"smoke_envelope.json"))),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["stage","smoke"]);p.add_argument("path");p.add_argument("--runtime-root");p.add_argument("--run-id")
    a=p.parse_args()
    if a.mode=="stage":stage(a.path,a.runtime_root)
    else:smoke(a.path,a.run_id)
