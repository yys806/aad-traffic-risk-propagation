"""Offline V4 regressions. No WSL, network, native binary or TraCI is called."""
import hashlib
import io
import json
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import prepare_stage_0_5_linux_runtime_v4 as installer
import stage_0_5_native_capsule_v4 as capsule


@pytest.mark.parametrize("url",["http://pypi.org/a","https://example.org/a","https://pypi.org.example.org/a",
    "https://user:password@pypi.org/a","file:///etc/passwd"])
def test_installer_refuses_non_official_https_sources(url):
    with pytest.raises(ValueError,match="download_url_outside_pypi_allowlist"):
        installer.validate_url(url)


@pytest.mark.parametrize("host",["pypi.org","files.pythonhosted.org"])
def test_installer_permits_only_official_metadata_and_artifact_hosts(host):
    assert installer.validate_url("https://"+host+"/package.whl")


def item(data=b"synthetic",filename="synthetic-1.0-py3-none-any.whl"):
    return dict(url="https://files.pythonhosted.org/"+filename,filename=filename,
        size=len(data),digests=dict(sha256=hashlib.sha256(data).hexdigest()))


def test_installer_reuses_only_exact_sha_and_size_without_network(tmp_path,monkeypatch):
    data=b"synthetic";spec=item(data);(tmp_path/spec["filename"]).write_bytes(data)
    monkeypatch.setattr(installer.OPENER,"open",lambda *a,**k:pytest.fail("network forbidden"))
    assert installer.download(tmp_path,spec).read_bytes()==data


def test_interrupted_artifact_is_retained_and_new_download_checked(tmp_path,monkeypatch):
    folder=tmp_path/"wheels";folder.mkdir();data=b"synthetic";spec=item(data)
    (folder/spec["filename"]).write_bytes(b"partial")
    class Remote(io.BytesIO):
        headers={"Content-Length":str(len(data))}
        def geturl(self):return spec["url"]
    monkeypatch.setattr(installer.OPENER,"open",lambda *a,**k:Remote(data))
    assert installer.download(folder,spec).read_bytes()==data
    retained=list((tmp_path/"interrupted").iterdir())
    assert len(retained)==1 and retained[0].read_bytes()==b"partial"


@pytest.mark.parametrize("fault",["size","name","hash"])
def test_installer_rejects_invalid_artifact_contract_before_network(tmp_path,monkeypatch,fault):
    spec=item()
    if fault=="size":spec["size"]=installer.MAX_WHEEL_BYTES+1
    if fault=="name":spec["filename"]="../escape.whl"
    if fault=="hash":spec["digests"]={}
    monkeypatch.setattr(installer.OPENER,"open",lambda *a,**k:pytest.fail("network forbidden"))
    with pytest.raises(ValueError):installer.download(tmp_path,spec)
    assert not list(tmp_path.iterdir())


def test_installer_refuses_other_root_before_any_subprocess(tmp_path,monkeypatch):
    monkeypatch.setattr(installer.subprocess,"run",lambda *a,**k:pytest.fail("subprocess forbidden"))
    with pytest.raises(ValueError,match="exact_project_runtime_directory_required"):
        installer.prepare(tmp_path/"other")


def test_exact_smoke_authorization_cannot_authorize_research():
    proposal=dict(schema=capsule.SMOKE_SCHEMA,task_id=capsule.SMOKE_TASK)
    approval=dict(task_id=capsule.SMOKE_TASK,proposal_sha256="a"*64,run_id="SMOKE_V4_1",
        engineering_authorized=True,decision_record="Explicit synthetic-only user authorization")
    assert capsule.authorization_reasons(proposal,approval,"a"*64,"SMOKE_V4_1")==[]
    proposal=dict(schema=capsule.SCHEMA,task_id=capsule.TASK,isolation=dict(accepted_for_new_task=False))
    assert capsule.authorization_reasons(proposal,approval,"a"*64,"B00")


@pytest.mark.parametrize("actual",[[22,"SUMO 1.18.0"],[21,"SUMO 1.26.0"],[22,"SUMO 1.26.0 extra"],None])
def test_version_or_protocol_mismatch_rejected(actual):
    assert not capsule.version_matches(actual,dict(traci_protocol=22,sumo_release="1.26.0"))


def test_exact_runtime_version_and_protocol():
    assert capsule.version_matches([22,"SUMO 1.26.0"],dict(traci_protocol=22,sumo_release="1.26.0"))


@pytest.mark.parametrize("prefix",["Eclipse SUMO sumo ","Eclipse SUMO sumo Version "])
@pytest.mark.parametrize("surround",[("",""),("","\n"),("","\r\n Build features: Linux"),
                                     ("License text\n","\nOther build text")])
def test_sumo_cli_exact_release_line(prefix,surround):
    assert capsule.sumo_version_output_matches(surround[0]+prefix+"1.26.0"+surround[1],"1.26.0")


INVALID_RELEASE_LINES=["1.26.0.1","1.26.0-dev","1.26.0+custom","1.26.0rc1",
    "1.26.00","1.26.01","11.26.0","1.26.0 extra","1.26.0 Version 1.18.0",
    "1.26.0 (custom)","1.26.0\tcustom","1.26.0 ","1.26.0\x00","1.26.0\vBuild",
    "\n1.26.0","\t1.26.0","1x26x0","1.18.0",""]


@pytest.mark.parametrize("prefix",["Eclipse SUMO sumo ","Eclipse SUMO sumo Version "])
@pytest.mark.parametrize("release_text",INVALID_RELEASE_LINES)
def test_sumo_cli_rejects_nonrelease_or_extra_inline_text(prefix,release_text):
    assert not capsule.sumo_version_output_matches(prefix+release_text+"\nBuild features: Linux","1.26.0")


@pytest.mark.parametrize("output",[None,b"Eclipse SUMO sumo 1.26.0",123,
    "Version 1.26.0","sumo 1.26.0","prefix Eclipse SUMO sumo 1.26.0",
    " Eclipse SUMO sumo 1.26.0","Eclipse SUMO sumo\nVersion 1.26.0"])
def test_sumo_cli_requires_complete_independent_version_line(output):
    assert not capsule.sumo_version_output_matches(output,"1.26.0")


@pytest.mark.parametrize("version_text",INVALID_RELEASE_LINES[:4]+["1.26.0 extra"])
def test_controller_wrong_cli_release_stops_before_socket_or_native_start(tmp_path,monkeypatch,version_text):
    from types import SimpleNamespace
    import stage_0_5_linux_controller_v4 as controller
    monkeypatch.chdir(tmp_path)
    binary=tmp_path/"synthetic-binary";binary.write_bytes(b"never executed")
    context=dict(schema="synthetic-test",run={},input_sha256={"routes.rou.xml":"unused"},
        runtime=dict(sumo_binary=str(binary),sumo_release="1.26.0",sumo_sha256=capsule.sha(binary)),native_environment={},
        proposal_sha256="p",policy_sha256="q")
    (tmp_path/"broker_context.json").write_bytes(capsule.canonical(context))
    (tmp_path/"routes.rou.xml").write_bytes(b"synthetic")
    monkeypatch.setattr(controller,"verify_live_context",lambda c:None)
    monkeypatch.setattr(controller,"inventory",lambda b:(None,{},None,None,None))
    monkeypatch.setattr(controller,"IdentityObserver",lambda rows:SimpleNamespace(finish=lambda **kw:{}))
    monkeypatch.setattr(controller,"Scope",lambda *a,**kw:SimpleNamespace(create=lambda path,data:path.write_bytes(data)))
    stopped=[]
    monkeypatch.setattr(controller,"NativeBackend",lambda:SimpleNamespace(
        start=lambda c:pytest.fail("native start forbidden"),stop=lambda:stopped.append(True)))
    monkeypatch.setattr(controller.os,"readlink",lambda p:"synthetic-namespace")
    read_text=Path.read_text
    def text(path,*args,**kwargs):
        if str(path).replace("\\","/")=="/proc/self/status":
            return "NoNewPrivs: 1\nSeccomp: 2\nCapEff: 0000000000000000"
        if str(path).replace("\\","/")=="/proc/net/dev":return "header\nheader\nlo: synthetic"
        return read_text(path,*args,**kwargs)
    monkeypatch.setattr(Path,"read_text",text)
    commands=[]
    def version(command,**kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0,stdout=("Eclipse SUMO sumo "+version_text+"\n").encode())
    monkeypatch.setattr(controller.subprocess,"run",version)
    monkeypatch.setattr(controller.socket,"socket",lambda *a,**k:pytest.fail("TraCI socket forbidden"))
    with pytest.raises(ValueError,match="SUMO_release_mismatch"):controller.main()
    assert commands==[[str(binary),"--version"]] and stopped==[True]
    receipt=json.loads((tmp_path/"controller_receipt.json").read_bytes())
    assert receipt["error"]=="ValueError:SUMO_release_mismatch" and receipt["controls"]==[]


def synthetic_receipt(tmp_path):
    """Known synthetic receipts are test inputs, never exported OS evidence."""
    from stage_0_5_isolation_admission import probe_checks
    host={n:"host:"+n for n in ["user","mnt","pid","net","ipc"]}
    namespaces={n:"capsule:"+n for n in host}
    negatives=["readonly_input","forbidden_read","forbidden_write","forbidden_metadata_write","unregistered_exec",
        "output_symlink","host_unix_socket","vsock","namespace_escape","host_loopback","external_network"]
    modes={n:dict(mode=n,exit_code=0,runtime={},observations={}) for n in ["basic","output","pids","memory","cpu","timeout"]}
    modes["basic"]["observations"]=dict({n:dict(denied=True) for n in negatives},allowed_read=True,allowed_write=True,
        child_inherits_denial=True,isolated_loopback_works=True,namespace_ids=namespaces,
        status=dict(CapEff="0000000000000000",NoNewPrivs="1",Seccomp="2"))
    modes["output"]["observations"]={n:dict(denied=True) for n in ["per_file_limit","aggregate_tmpfs_limit"]}
    modes["pids"]["observations"]=dict(pids_limit=dict(errno=11));modes["pids"]["runtime"]=dict(kernel_counters={"pids.events":"max 1"})
    modes["memory"].update(exit_code=1,runtime=dict(payload_exit_code=-9,kernel_counters={"memory.events":"oom_kill 1"},artifact_sha256={"memory_started":"x"}))
    modes["cpu"]["runtime"]=dict(kernel_counters={"cpu.stat":"nr_throttled 1"})
    modes["timeout"].update(exit_code=1,elapsed_s=2,runtime=dict(termination_signals=[15],artifact_sha256={"timeout_started":"x"}))
    probe=dict(guard_sha256="a"*64,host_namespaces=host,commands=list(modes.values()))
    assert all(probe_checks(probe).values())
    sources={"stage_0_5_linux_isolation.py":"a"*64}
    limits=dict(process_tree_rss_bytes=1024**3,task_output_bytes=16*1024**2,per_attempt_wall_s=30,
        supervision_poll_s=.5,min_free_c_bytes=1,min_free_d_bytes=1,min_available_memory_bytes=1)
    run=dict(id="SMOKE_V4_UNIT",duration_s=.1,internal_step_s=.05,capsule_input_sha256={"network.net.xml":"b"*64},
        supply_target_lanes=["synth_0"],lane_speed_schedule=[dict(start_s=0,end_s=.1,speed_mps=10)])
    policy=dict(host_namespaces=host,binding=dict(source_sha256=sources),tasks=32,output_bytes=limits["task_output_bytes"],
        wall_s=30,scratch="/synthetic/scratch",archive="/synthetic/archive")
    def write(name,value):
        (tmp_path/name).write_bytes(value if isinstance(value,bytes) else capsule.canonical(value))
    write("executed_policy.json",policy);write("capability_record.json",probe);write("broker_context.json",{})
    for name in ["identity_events.jsonl","identity_summary.json"]:write(name,b"synthetic")
    for name,tag in [("fcd.xml","fcd-export"),("summary.xml","summary"),("tripinfo.xml","tripinfos")]:write(name,("<"+tag+"/>").encode())
    proposal=dict(runs=[run],controller_source_sha256=sources,runtime_manifest_sha256="c"*64,
        kernel_probe_sha256=capsule.sha(tmp_path/"capability_record.json"),single_attempt_limits=limits,
        runtime=dict(traci_protocol=22,sumo_release="1.26.0",sumo_sha256="d"*64,traci_init_sha256="e"*64))
    policy_sha=capsule.sha(tmp_path/"executed_policy.json");proposal_sha="f"*64
    samples=[dict(free_c_bytes=10,free_d_bytes=10,free_wsl_bytes=2*1024**3,capsule_fs_free_bytes=1024**2,
        capsule_fs_capacity_bytes=limits["task_output_bytes"],process_tree_rss_bytes=1,wall_s=t,available_memory_bytes=10,task_output_bytes=0) for t in [0,.1]]
    control=dict(proposal_sha256=proposal_sha,policy_sha256=policy_sha,getVersion=[22,"SUMO 1.26.0"],sumo_binary_sha256="d"*64,
        traci_source_sha256="e"*64,sumo_version_output="Eclipse SUMO sumo Version 1.26.0",controller_namespaces=namespaces,
        sumo_namespaces=namespaces,controller_security=modes["basic"]["observations"]["status"],sumo_security=modes["basic"]["observations"]["status"],
        network_interfaces=["lo"],exit_code=0,resource_samples=samples,watchdog_failure=None,
        controls=[dict(failures=[],applied_before_step_s=i*.05,native_clock_before_s=i*.05,target_mps=10,native_lane_limits={"synth_0":10}) for i in range(2)])
    write("controller_receipt.json",control)
    receipt=dict(proposal_sha256=proposal_sha,policy_sha256=policy_sha,runtime_manifest_sha256="c"*64,source_sha256=sources,
        input_sha256=run["capsule_input_sha256"],guard_sha256="a"*64,broker_context_sha256=capsule.sha(tmp_path/"broker_context.json"),
        namespaces=namespaces,cgroup={"memory.max":str(limits["process_tree_rss_bytes"]),"memory.swap.max":"0","pids.max":"32","cpu.max":"100000 100000"},
        input_mounts={"network.net.xml":"1 2 3 / /synthetic/scratch/network.net.xml ro - ext4 /dev/synthetic rw"},
        payload_exit_code=0,descendants_reaped=True,remaining_pids=[],output_bytes=100,
        artifact_sha256={p.name:capsule.sha(p) for p in tmp_path.iterdir()})
    write("isolation_runtime.json",receipt)
    return proposal,proposal_sha,policy_sha,control,receipt


def test_independent_receipt_accepts_complete_synthetic_truth(tmp_path):
    p,d,h,_,_=synthetic_receipt(tmp_path)
    result=capsule.verify_receipt(tmp_path,p,d,h)
    assert result["status"]=="Pass" and all(result["probes"].values())


@pytest.mark.parametrize("fault",["runtime","source","input","binary","protocol","controller_host","sumo_host","security","network",
    "resource_missing","resource_exceeded","resource_gap","resource_watchdog","control_missing","control_readback","native_error","orphan","mount_rw","output_hash","receipt_missing","policy_bytes"])
def test_receipt_rejects_faults_using_real_verifier(tmp_path,fault):
    p,d,h,c,r=synthetic_receipt(tmp_path)
    if fault=="runtime":r["runtime_manifest_sha256"]="0"*64
    elif fault=="source":r["source_sha256"]={}
    elif fault=="input":r["input_sha256"]={}
    elif fault=="binary":c["sumo_binary_sha256"]="0"*64
    elif fault=="protocol":c["getVersion"][0]=0
    elif fault=="controller_host":c["controller_namespaces"]={n:"host:"+n for n in c["controller_namespaces"]}
    elif fault=="sumo_host":c["sumo_namespaces"]={n:"host:"+n for n in c["sumo_namespaces"]}
    elif fault=="security":c["sumo_security"]["Seccomp"]="0"
    elif fault=="network":c["network_interfaces"].append("eth0")
    elif fault=="resource_missing":c["resource_samples"][0].pop("free_d_bytes")
    elif fault=="resource_exceeded":c["resource_samples"][0]["process_tree_rss_bytes"]=4*1024**3
    elif fault=="resource_gap":c["resource_samples"][1]["wall_s"]=1
    elif fault=="resource_watchdog":c["watchdog_failure"]="timeout"
    elif fault=="control_missing":c["controls"].pop()
    elif fault=="control_readback":c["controls"][0]["native_lane_limits"]["synth_0"]=5
    elif fault=="native_error":c["exit_code"]=1
    elif fault=="orphan":r["remaining_pids"]=[3]
    elif fault=="mount_rw":r["input_mounts"]["network.net.xml"]=r["input_mounts"]["network.net.xml"].replace(" ro "," rw ")
    elif fault=="output_hash":(tmp_path/"fcd.xml").write_text("tampered")
    elif fault=="receipt_missing":(tmp_path/"isolation_runtime.json").unlink()
    elif fault=="policy_bytes":(tmp_path/"executed_policy.json").write_bytes((tmp_path/"executed_policy.json").read_bytes()+b"\n")
    (tmp_path/"controller_receipt.json").write_bytes(capsule.canonical(c))
    r["artifact_sha256"]["controller_receipt.json"]=capsule.sha(tmp_path/"controller_receipt.json")
    if fault!="receipt_missing":(tmp_path/"isolation_runtime.json").write_bytes(capsule.canonical(r))
    with pytest.raises((ValueError,KeyError,OSError)):
        capsule.verify_receipt(tmp_path,p,d,h)


def test_stage_rejects_other_output_before_writing(tmp_path):
    from prepare_stage_0_5_linux_stage_v4 import stage
    with pytest.raises(ValueError,match="exclusive_authorized_stage_required"):
        stage(tmp_path/"other","unused")
    assert not list(tmp_path.iterdir())


def test_stage_only_copies_sources_and_static_manifest(tmp_path,monkeypatch):
    import prepare_stage_0_5_linux_stage_v4 as staging
    import stage_0_5_linux_runtime_v4 as runtime
    import subprocess
    monkeypatch.setattr(staging,"STAGE_PARENT",tmp_path)
    monkeypatch.setattr(runtime,"runtime_manifest",lambda root:dict(runtime_root=str(root),files={}))
    monkeypatch.setattr(subprocess,"Popen",lambda *a,**k:pytest.fail("staging must not launch any process"))
    destination=tmp_path/"stage05_v4_static"
    staging.stage(destination,"synthetic-runtime")
    assert {p.name for p in destination.iterdir()}==set(staging.SOURCES)|{"runtime_manifest.json","staging_record.json"}
    record=json.loads((destination/"staging_record.json").read_bytes())
    assert record["SUMO_launches"]==record["TraCI_connections"]==record["new_research_trajectories"]==0
    assert all(capsule.sha(destination/name)==digest for name,digest in record["source_sha256"].items())
    with pytest.raises(FileExistsError):staging.stage(destination,"synthetic-runtime")


def test_static_closure_resolves_only_unique_bound_wheel_dependency(tmp_path):
    from stage_0_5_linux_runtime_v4 import resolve_dependency
    path=tmp_path/"wheel.libs/libhashed.so"
    assert resolve_dependency("libhashed.so",[],{},{str(path):"bound"})==path
    with pytest.raises(ValueError,match="unresolved_or_ambiguous"):
        resolve_dependency("libmissing.so",[],{},{str(path):"bound"})
    with pytest.raises(ValueError,match="unresolved_or_ambiguous"):
        resolve_dependency("libhashed.so",[],{},{str(path):"a",str(tmp_path/"other/libhashed.so"):"b"})


def test_production_policy_has_dedicated_exact_import_directory(tmp_path,monkeypatch):
    import stage_0_5_linux_runtime_v4 as runtime
    import os
    source=tmp_path/"stage_0_5_linux_controller_v4.py";source.write_text("# synthetic source")
    manifest=tmp_path/"runtime.json";manifest.write_text("{}")
    probe=tmp_path/"probe.json";probe.write_text("{}")
    monkeypatch.setattr(os,"readlink",lambda path:"synthetic-namespace")
    environment=dict(files={},executables=["/synthetic/python"],readonly_paths=[],python_executable="/synthetic/python",sumo_binary="/synthetic/sumo",sumo_home="/synthetic")
    path,policy=runtime.make_policy(tmp_path/"capsule",environment,manifest,{source.name:str(source)},{},
        dict(single_attempt_limits=dict(process_tree_rss_bytes=1,task_output_bytes=1,per_attempt_wall_s=1)),accepted_build=False,capability_record=probe)
    parent=tmp_path/"capsule/controller_sources"
    assert policy["readonly_paths"]==[str(parent)]
    assert {p.name for p in parent.iterdir()}=={source.name}
    assert capsule.sha(parent/source.name)==capsule.sha(source)
    assert path.read_bytes()==capsule.canonical(policy)


def test_v4_version_check_uses_bound_receipt_not_host_dpkg():
    from stage_0_5_isolation_admission import runtime_reasons
    p=dict(schema=capsule.SCHEMA,runtime=dict(sumo_release="1.26.0",traci_protocol=22,sumo_sha256="binary",traci_init_sha256="tools"))
    record=dict(getVersion=[22,"SUMO 1.26.0"],sumo_binary_sha256="binary",traci_source_sha256="tools",controller_namespaces={"net":"isolated"},sumo_namespaces={"net":"isolated"})
    assert runtime_reasons(p,dict(installed_versions="sumo\t1.18.0",controller_receipt=record))==[]
    assert runtime_reasons(p,{})==["bound_production_runtime_receipt_missing"]
    record["getVersion"][0]=0
    assert "bound_Linux_SUMO_or_TraCI_version_mismatch" in runtime_reasons(p,dict(controller_receipt=record))


def test_isolated_broker_resolves_bound_verifier_before_validation(tmp_path):
    """Reproduce -I startup in a fresh interpreter, stopping before any mount.

    The synthetic verifier raises a sentinel; reaching it proves that startup
    found the sibling dependency. No namespace, simulator or TraCI is launched.
    """
    import subprocess
    import stage_0_5_linux_isolation as guard
    broker=tmp_path/"stage_0_5_linux_isolation.py"
    broker.write_bytes(Path(guard.__file__).read_bytes())
    sources=tmp_path/"bound_sources";sources.mkdir()
    verifier=sources/"stage_0_5_isolation_admission.py"
    verifier.write_text("def probe_checks(record): return {}\n")
    # A contradictory sibling in the mixed staging parent must not be imported.
    (tmp_path/verifier.name).write_text("raise AssertionError('unbound staging import')\n")
    policy=tmp_path/"policy.json";policy.write_bytes(capsule.canonical(dict(purpose="stage0.5-production-v4",
        binding=dict(source_files={verifier.name:str(verifier)}),file_sha256={str(verifier):capsule.sha(verifier)})))
    code='''import runpy,sys
m=runpy.run_path(sys.argv[1],run_name="isolated_broker_test")
child=m["child"]; g=child.__globals__
g["os"].getpid=lambda:1; g["os"].getuid=lambda:0
def validate(policy):
    from stage_0_5_isolation_admission import probe_checks
    assert probe_checks({})=={}
    raise RuntimeError("verified_import_stop_before_mount")
g["validate"]=validate
try: child(sys.argv[2],m["sha"](sys.argv[2]))
except RuntimeError as error:
    assert str(error)=="verified_import_stop_before_mount",str(error)
else: raise AssertionError("must stop before native isolation")
print("isolated_import_verified_no_native_launch")
'''
    result=subprocess.run([sys.executable,"-I","-B","-c",code,str(broker),str(policy)],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="isolated_import_verified_no_native_launch"


def test_smoke_preparation_uses_controller_identity_contract_and_never_reauthorizes(tmp_path,monkeypatch):
    import os
    import prepare_stage_0_5_linux_stage_v4 as staging
    import stage_0_5_linux_runtime_v4 as runtime_module
    from stage_0_5_input_fidelity import inventory
    archive=tmp_path/"synthetic_receipts";archive.mkdir();synthetic_receipt(archive)
    base=tmp_path/"stage05_v4_synthetic";base.mkdir()
    monkeypatch.setattr(staging,"STAGE_PARENT",tmp_path)
    monkeypatch.setattr(os,"readlink",lambda p:"synthetic-namespace")
    for name in staging.SOURCES:(base/name).write_text("# synthetic bound source")
    record=json.loads((archive/"capability_record.json").read_bytes())
    record["guard_sha256"]=capsule.sha(base/"stage_0_5_linux_isolation.py")
    (base/"probe_results").mkdir();(base/"probe_results/record.json").write_bytes(capsule.canonical(record))
    runtime=dict(files={},executables=["/synthetic/python","/synthetic/sumo"],readonly_paths=[],
        python_executable="/synthetic/python",sumo_binary="/synthetic/sumo",sumo_home="/synthetic")
    (base/"runtime_manifest.json").write_bytes(capsule.canonical(runtime))
    (base/"staging_record.json").write_bytes(capsule.canonical(dict(
        source_sha256={n:capsule.sha(base/n) for n in staging.SOURCES},
        runtime_manifest_sha256=capsule.sha(base/"runtime_manifest.json"))))
    monkeypatch.setattr(runtime_module,"check_runtime",lambda manifest:True)
    staging.smoke(base,"SMOKE_V4_SYNTHETIC_PREPARATION_ONLY")
    _,vehicles,initial,_,_=inventory((base/"smoke_inputs/routes.rou.xml").read_bytes())
    assert list(vehicles)==["synth_vehicle"] and not initial
    envelope=json.loads((base/"smoke_envelope.json").read_bytes())
    proposal=json.loads((base/"smoke_proposal.json").read_bytes())
    assert envelope["approval"]["engineering_authorized"] is False
    assert proposal["execution_plan"]["maximum_attempts"]==1 and proposal["execution_plan"]["automatic_retry"] is False
    assert capsule.authorization_reasons(proposal,envelope["approval"],envelope["proposal_sha256"],envelope["run_id"])==["engineering_smoke_authorization_missing"]


def bind_research_policy(tmp_path, proposal):
    proposal.setdefault("controller_source_sha256", {"synthetic.py": "a"*64})
    proposal.setdefault("runtime_manifest_sha256", "b"*64)
    policy = dict(binding=dict(accepted_build=True, source_sha256=proposal["controller_source_sha256"],
        runtime_manifest_sha256=proposal["runtime_manifest_sha256"], run_id=proposal["runs"][0]["id"]))
    (tmp_path/"policy.json").write_bytes(capsule.canonical(policy))
    proposal.update(policy_binding_required=True, capsule_policy_repo_path="policy.json",
                    capsule_policy_sha256=capsule.sha(tmp_path/"policy.json"))


def v4_ledger_fixture(tmp_path):
    from stage_0_5_research_ledger import ResearchLedger
    root=Path(__file__).resolve().parents[2]
    config=json.loads((root/"code/configs/stage_0_5_ready_to_admit_v3.json").read_bytes())
    config.update(ledger_path="journal/events.jsonl",output_root="outputs",historical_references=[])
    def write(name,value):
        if name == "proposal.json":
            bind_research_policy(tmp_path, value)
        (tmp_path/name).write_bytes(value if isinstance(value,bytes) else capsule.canonical(value))
    write("budget.json",config);write("plan.md",b"synthetic plan")
    write("source.py",b"# synthetic");write("input.xml",b"<synthetic/>")
    write("isolation.json",dict(task_id=capsule.TASK,input_and_test_resource_scope_accepted=True))
    ledger=ResearchLedger(tmp_path,"budget.json",task_id=capsule.TASK);ledger.initialize()
    p=dict(schema=capsule.SCHEMA,task_id=capsule.TASK,execution_allowed=False,researcher_confirmed=False,protocol_frozen=False,
        admission=dict.fromkeys(["initialization_policy_approved","measurement_contract_approved","input_fidelity_approved"],False),
        budget_sha256=capsule.sha(tmp_path/"budget.json"),plan_path="plan.md",plan_sha256=capsule.sha(tmp_path/"plan.md"),plan_version="synthetic-v4",
        git_commit="a"*40,worktree_sha256="b"*64,environment=dict(python="synthetic"),source_sha256={"source.py":capsule.sha(tmp_path/"source.py")},
        isolation=dict(accepted_for_new_task=True,report_path="isolation.json",report_sha256=capsule.sha(tmp_path/"isolation.json")),
        runs=[dict(id="B00_SYNTHETIC",seed=1,question="synthetic",contrast="reference",condition="synthetic",factors=dict(supply=False,ramp=False),
            initialization_policy="synthetic",input_sha256={"input.xml":capsule.sha(tmp_path/"input.xml")},artifact_path="outputs/B00_SYNTHETIC")])
    write("proposal.json",p)
    approval=dict(task_id=capsule.TASK,run_id="B00_SYNTHETIC",proposal_sha256=capsule.sha(tmp_path/"proposal.json"),decision_record="synthetic unit test only",
        execution_allowed=True,researcher_confirmed=True,protocol_frozen=True,admission=dict.fromkeys(p["admission"],True))
    resources=dict(free_c_bytes=6*1024**3,free_d_bytes=15*1024**3,available_memory_bytes=5*1024**3,
        task_output_bytes=0,wall_s=0,process_tree_rss_bytes=1)
    return ledger,p,approval,resources


def test_v4_ledger_exact_external_authorization_does_not_rewrite_false_proposal(tmp_path):
    ledger,p,approval,resources=v4_ledger_fixture(tmp_path)
    before=(tmp_path/"proposal.json").read_bytes()
    state=ledger.reserve("proposal.json",approval,"B00_SYNTHETIC",resources)
    assert state["attempt_count"]==1 and state["attempts"]["B00_SYNTHETIC"]["status"]=="reserved"
    assert (tmp_path/"proposal.json").read_bytes()==before
    assert not p["execution_allowed"] and not p["researcher_confirmed"] and not p["protocol_frozen"]


@pytest.mark.parametrize("fault",["run_id","proposal_sha256","protocol_frozen","initialization_policy_approved"])
def test_v4_ledger_missing_exact_authorization_records_no_attempt(tmp_path,fault):
    ledger,_,approval,resources=v4_ledger_fixture(tmp_path)
    if fault=="initialization_policy_approved":approval["admission"][fault]=False
    else:approval[fault]=False
    before=ledger.path.read_bytes()
    with pytest.raises(ValueError):ledger.reserve("proposal.json",approval,"B00_SYNTHETIC",resources)
    assert ledger.path.read_bytes()==before and ledger.snapshot()["attempt_count"]==0


def preflight_fixture(tmp_path):
    from stage_0_5_admission_v3 import MANDATORY_SOURCES
    from prepare_stage_0_5_linux_stage_v4 import SOURCES
    def write(name,value):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value if isinstance(value,bytes) else capsule.canonical(value))
        return capsule.sha(path)
    source_names=set(MANDATORY_SOURCES)|{"code/scripts/"+n for n in SOURCES}
    sources={n:write(n,b"# synthetic source\n") for n in sorted(source_names)}
    inputs={"network.net.xml":"inputs/network.net.xml","routes.rou.xml":"inputs/routes.rou.xml","run.sumocfg":"inputs/run.sumocfg"}
    network=b'<net/>';routes=b'<routes><vType id="synth"/><route id="through" edges="synth"/></routes>'
    config=b'''<configuration><input><net-file value="network.net.xml"/><route-files value="routes.rou.xml"/></input>
<time><begin value="0"/><end value="420"/><step-length value="0.05"/></time><seed value="20261201"/>
<processing><step-method.ballistic value="true"/><threads value="1"/></processing>
<output><fcd-output value="fcd.xml"/><device.fcd.period value="0.1"/><summary-output value="summary.xml"/><tripinfo-output value="tripinfo.xml"/>
<tripinfo-output.write-unfinished value="true"/><tripinfo-output.write-undeparted value="true"/></output></configuration>'''
    hashes={name:write(name,data) for name,data in zip(inputs.values(),[network,routes,config])}
    limits=dict(per_attempt_wall_s=600,process_tree_rss_bytes=3*1024**3,task_output_bytes=2*1024**3,
        min_free_c_bytes=5*1024**3,min_free_d_bytes=14*1024**3,min_available_memory_bytes=4*1024**3,supervision_poll_s=.5)
    budget=dict(single_attempt_limits=limits,workers=1,automatic_retry=False,maximum_new_trajectory_attempts=None,output_root="outputs")
    run=dict(id="B00_SYNTHETIC",input_files=inputs,input_sha256=hashes,capsule_input_sha256={n:hashes[v] for n,v in inputs.items()},
        paired_base_routes=inputs["routes.rou.xml"],factors=dict(supply=False,ramp=False),duration_s=420,seed=20261201,
        evaluation_elapsed_s=[120,390],artifact_path="outputs/B00_SYNTHETIC",single_attempt_limits=limits)
    old_hash=write("old.json",dict(runs=[copy.deepcopy(run)]))
    previous=dict(source_sha256=sources,full=dict(exit_code=0,passed=1130))
    previous_hash=write("old_validation.json",previous)
    software=dict(validation_mode="production_capsule_targeted_extension",source_sha256=sources,targeted=dict(exit_code=0),
        reused_full_regression=dict(path="old_validation.json",sha256=previous_hash),modified_existing_sources=[],added_sources=[])
    p=dict(schema=capsule.SCHEMA,task_id=capsule.TASK,runs=[run],source_sha256=sources,
        controller_source_sha256={n:sources["code/scripts/"+n] for n in SOURCES},
        support_input_sha256={"support.txt":write("support.txt",b"synthetic")},
        measurement_reference_sha256={"reference.csv":write("reference.csv",b"synthetic")},
        previous_proposal=dict(path="old.json",sha256=old_hash),plan_path="plan.md",plan_sha256=write("plan.md",b"synthetic"),
        budget_path="budget.json",budget_sha256=write("budget.json",budget),single_attempt_limits=limits,
        software_validation_path="software.json",software_validation_sha256=write("software.json",software),
        environment=dict(linux_runtime_manifest_sha256="r"*64),runtime_manifest_sha256="r"*64,
        worktree_sha256=hashlib.sha256(capsule.canonical(sources)).hexdigest(),
        isolation=dict(accepted_for_new_task=False,report_path="integration.json",report_sha256=write("integration.json",dict(accepted_for_new_task=False))),
        execution_allowed=False,researcher_confirmed=False,protocol_frozen=False)
    bind_research_policy(tmp_path, p)
    write("proposal.json",p)
    return p


@pytest.mark.parametrize("fault,reason",[(None,"integration_not_accepted"),("source","bound_file_drift"),
    ("controller","research_policy_source_binding"),("input","scientific_input_drift"),("map","inexact_scientific_input_map"),
    ("reference","measurement_reference_drift"),("environment","Linux_environment_binding_missing"),("budget","single_attempt_budget_drift")])
def test_actual_v4_preflight_distinguishes_engineering_defect_from_authorization(tmp_path,monkeypatch,fault,reason):
    import stage_0_5_linux_execution_v4 as execution
    p=preflight_fixture(tmp_path)
    if fault=="source":(tmp_path/next(iter(p["source_sha256"]))).write_text("drift")
    elif fault=="controller":p["controller_source_sha256"]["stage_0_5_linux_execution_v4.py"]="drift"
    elif fault=="input":(tmp_path/"inputs/network.net.xml").write_text("drift")
    elif fault=="map":p["runs"][0]["input_files"].pop("network.net.xml")
    elif fault=="reference":(tmp_path/"reference.csv").write_text("drift")
    elif fault=="environment":p["environment"]["linux_runtime_manifest_sha256"]="drift"
    elif fault=="budget":p["single_attempt_limits"]=dict(p["single_attempt_limits"],per_attempt_wall_s=1)
    (tmp_path/"proposal.json").write_bytes(capsule.canonical(p))
    monkeypatch.setattr(execution.subprocess,"Popen",lambda *a,**k:pytest.fail("preflight must not launch"))
    report=execution.technical_preflight_v4(tmp_path,"proposal.json","B00_SYNTHETIC",inspect_runtime=False)
    assert report["status"]=="BLOCKED_ENGINEERING" and not report["ready"]
    assert len(report["technical_errors"])==1 and reason in report["technical_errors"][0]
    assert report["authorization_pending"]


def test_linux_preflight_response_must_match_exact_proposal_sha(monkeypatch):
    from types import SimpleNamespace
    import stage_0_5_linux_execution_v4 as execution
    p=dict(linux_distribution="Ubuntu",runtime=dict(python_executable="/synthetic/python"),linux_driver="synthetic.py",linux_proposal_path="p.json")
    monkeypatch.setattr(execution.subprocess,"run",lambda *a,**k:SimpleNamespace(returncode=0,stderr=b"",stdout=b'{"proposal_sha256":"wrong"}'))
    with pytest.raises(ValueError,match="Linux_proposal_copy_drift"):execution.inspect_linux(p,"exact")


def test_v4_engineering_pass_waits_for_approval_without_enabling_execution(tmp_path,monkeypatch):
    """Synthetic proof injection tests status semantics, never OS acceptance."""
    import stage_0_5_linux_execution_v4 as execution
    import stage_0_5_isolation_admission as admission
    p=preflight_fixture(tmp_path)
    proof=dict(accepted_for_new_task=True,input_and_test_resource_scope_accepted=True,
        controller_source_sha256=p["controller_source_sha256"],runtime_manifest_sha256=p["runtime_manifest_sha256"],
        smoke_proposal_path="smoke.json",smoke_archive_path="archive")
    smoke=dict(controller_source_sha256=p["controller_source_sha256"],runtime_manifest_sha256=p["runtime_manifest_sha256"],capsule_policy_sha256="synthetic")
    (tmp_path/"smoke.json").write_bytes(capsule.canonical(smoke))
    proof["smoke_proposal_sha256"]=capsule.sha(tmp_path/"smoke.json")
    (tmp_path/"archive").mkdir();(tmp_path/"archive/controller_receipt.json").write_text("{}")
    (tmp_path/"integration.json").write_bytes(capsule.canonical(proof))
    p["isolation"].update(accepted_for_new_task=True,report_sha256=capsule.sha(tmp_path/"integration.json"))
    (tmp_path/"proposal.json").write_bytes(capsule.canonical(p))
    before=(tmp_path/"proposal.json").read_bytes()
    monkeypatch.setattr(execution,"verify_receipt",lambda *a:dict(status="Pass"))
    monkeypatch.setattr(admission,"runtime_reasons",lambda *a:[])
    monkeypatch.setattr(execution,"inspect_linux",lambda *a:dict(linux_runtime_verified=True))
    monkeypatch.setattr(execution.subprocess,"Popen",lambda *a,**k:pytest.fail("launch forbidden"))
    report=execution.technical_preflight_v4(tmp_path,"proposal.json","B00_SYNTHETIC")
    assert report["status"]=="READY_FOR_RESEARCHER_APPROVAL" and report["ready"]
    assert report["technical_errors"]==[] and report["authorization_pending"]
    assert "capsule_build_not_accepted" not in report["authorization_pending"]
    assert (tmp_path/"proposal.json").read_bytes()==before
    assert not p["execution_allowed"] and not p["researcher_confirmed"] and not p["protocol_frozen"]
