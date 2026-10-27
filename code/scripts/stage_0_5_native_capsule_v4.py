"""Exact authorization and independent OS/runtime receipt verification.

No native launcher is exposed here. A research authorization and an engineering
smoke authorization have disjoint task IDs and input contracts.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

SCHEMA="aad.native-admission.v4"
SMOKE_SCHEMA="aad.native-smoke.v4"
TASK="AAD-0.5-READY-TO-ADMIT-V3"
SMOKE_TASK="AAD-0.5-LINUX-INTEGRATION-V4-SMOKE"


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda:f.read(1024*1024),b""):h.update(data)
    return h.hexdigest()


def require(condition,reason):
    if not condition:raise ValueError(reason)


def safe_relative(root,name):
    require(isinstance(name,str) and not Path(name).is_absolute() and ".." not in Path(name).parts,"unsafe_relative_path")
    p=Path(root)/name
    require(not any(v.is_symlink() for v in [p,*p.parents]),"symlink_in_capsule_path")
    return p


def smoke_inputs(run,inputs):
    require(run["id"].startswith("SMOKE_V4_") and 0<run["duration_s"]<=5,"synthetic_run_scope")
    require(set(inputs)=={"network.net.xml","routes.rou.xml","run.sumocfg"},"synthetic_exact_inputs")
    net=ET.fromstring(inputs["network.net.xml"]);routes=ET.fromstring(inputs["routes.rou.xml"])
    edges=net.findall("edge");vehicles=routes.findall("vehicle")
    require(1<=len(edges)<=2 and all(e.get("id","").startswith("synth_") for e in edges),"synthetic_network_only")
    require(1<=len(vehicles)<=4 and all(v.get("id","").startswith("synth_") for v in vehicles),"synthetic_vehicles_only")
    require(all(len(e.findall("lane"))<=5 for e in edges),"synthetic_lane_bound")
    cfg=ET.fromstring(inputs["run.sumocfg"])
    require(float(cfg.find("time/end").get("value"))==run["duration_s"],"synthetic_config_duration")
    require(cfg.find("input/net-file").get("value")=="network.net.xml" and cfg.find("input/route-files").get("value")=="routes.rou.xml","synthetic_config_refs")


def authorization_reasons(proposal,approval,proposal_sha,run_id):
    errors=[]
    if not isinstance(approval,dict):return ["exact_authorization_missing"]
    expected=SMOKE_TASK if proposal.get("schema")==SMOKE_SCHEMA else TASK
    for key,value in [("proposal_sha256",proposal_sha),("task_id",expected),("run_id",run_id)]:
        if approval.get(key)!=value:errors.append("authorization_"+key+"_mismatch")
    if not approval.get("decision_record"):errors.append("human_decision_record_missing")
    if expected==SMOKE_TASK:
        if proposal.get("task_id")!=SMOKE_TASK or approval.get("engineering_authorized") is not True:
            errors.append("engineering_smoke_authorization_missing")
    else:
        if proposal.get("schema")!=SCHEMA or proposal.get("task_id")!=TASK:errors.append("wrong_research_task")
        for field in ["execution_allowed","researcher_confirmed","protocol_frozen"]:
            if approval.get(field) is not True:errors.append(field+"_not_confirmed_for_exact_proposal")
        for field in ["initialization_policy_approved","measurement_contract_approved","input_fidelity_approved"]:
            if approval.get("admission",{}).get(field) is not True:errors.append(field+"_not_confirmed")
        if proposal.get("isolation",{}).get("accepted_for_new_task") is not True:
            errors.append("capsule_build_not_accepted")
    return errors


def verify_envelope(policy,envelope_path,envelope_sha):
    raw=Path(envelope_path).read_bytes();require(hashlib.sha256(raw).hexdigest()==envelope_sha,"launch_envelope_drift")
    envelope=json.loads(raw)
    proposal_path=Path(envelope["proposal_path"])
    require(sha(proposal_path)==envelope["proposal_sha256"],"launch_proposal_drift")
    proposal=json.loads(proposal_path.read_bytes())
    require(proposal["capsule_policy_sha256"]==hashlib.sha256(canonical(policy)).hexdigest(),"proposal_policy_binding")
    run=next((r for r in proposal["runs"] if r["id"]==envelope["run_id"]),None)
    require(run is not None,"launch_run_not_bound")
    reasons=authorization_reasons(proposal,envelope["approval"],envelope["proposal_sha256"],envelope["run_id"])
    require(not reasons,";".join(reasons))
    # The research envelope is executable only when the exact policy that it
    # hashes carries an accepted production build.  Engineering smoke keeps
    # its historical false lock and is handled by the separate smoke schema.
    if proposal["schema"] == SCHEMA:
        require(policy.get("binding", {}).get("run_id") == envelope["run_id"],
                "research_policy_run_binding")
        require(policy.get("binding", {}).get("accepted_build") is True,
                "research_policy_accepted_build_false")
        require(policy.get("binding", {}).get("source_sha256") == proposal["controller_source_sha256"],
                "research_policy_source_binding")
        require(policy.get("binding", {}).get("runtime_manifest_sha256") == proposal["runtime_manifest_sha256"],
                "research_policy_runtime_binding")
    inputs={name:Path(path).read_bytes() for name,path in policy["inputs"].items()}
    require({n:hashlib.sha256(v).hexdigest() for n,v in inputs.items()}==run["capsule_input_sha256"],"launch_input_binding")
    if proposal["schema"]==SMOKE_SCHEMA:smoke_inputs(run,inputs)
    require(policy["binding"]["runtime_manifest_sha256"]==proposal["runtime_manifest_sha256"],"launch_runtime_binding")
    require(policy["binding"]["source_sha256"]==proposal["controller_source_sha256"],"launch_source_binding")
    return dict(proposal_sha256=envelope["proposal_sha256"],task_id=proposal["task_id"],run_id=run["id"],
        run=run,approval=envelope["approval"],schema=proposal["schema"],input_sha256=run["capsule_input_sha256"],
        source_sha256=proposal["controller_source_sha256"],runtime_manifest_sha256=proposal["runtime_manifest_sha256"],
        runtime=proposal["runtime"],native_environment=proposal["native_environment"],resource_limits=proposal["single_attempt_limits"],
        controller_policy=dict(host_namespaces=policy["host_namespaces"],executables=policy["executables"]),
        policy_sha256=hashlib.sha256(canonical(policy)).hexdigest())


def verify_live_context(context):
    require(sys.platform=="linux","bare_host_native_forbidden")
    status=dict(r.split(":",1) for r in Path("/proc/self/status").read_text().splitlines() if ":" in r)
    require(all(status.get(k,"").strip()==v for k,v in {"NoNewPrivs":"1","Seccomp":"2","CapEff":"0000000000000000"}.items()),"controller_kernel_restrictions_missing")
    policy=context["controller_policy"]
    require(all(os.readlink("/proc/self/ns/"+n)!=v for n,v in policy["host_namespaces"].items()),"controller_on_host_namespace")
    require(context["runtime"]["sumo_binary"] in policy["executables"],"native_binary_outside_kernel_allowlist")
    cg=Path("/sys/fs/cgroup")/Path("/proc/self/cgroup").read_text().strip().split(":",2)[2].lstrip("/")
    require((cg/"memory.max").read_text().strip()==str(context["resource_limits"]["process_tree_rss_bytes"]),"controller_cgroup_memory_mismatch")
    require((cg/"memory.swap.max").read_text().strip()=="0","controller_swap_not_bounded")
    for logical,expected in context["source_sha256"].items():
        require(sha(context["source_files"][logical])==expected,"controller_source_drift:"+logical)
    require(sha(context["runtime"]["sumo_binary"])==context["runtime"]["sumo_sha256"],"controller_binary_drift")
    for name,expected in context["input_sha256"].items():require(sha(Path.cwd()/name)==expected,"controller_input_drift")
    proposal_stub=dict(schema=context["schema"],task_id=context["task_id"],isolation=dict(accepted_for_new_task=context["accepted_build"]))
    reasons=authorization_reasons(proposal_stub,context["approval"],context["proposal_sha256"],context["run_id"])
    require(not reasons,"controller_authorization:"+";".join(reasons))
    return cg


def version_matches(actual,runtime):
    return (isinstance(actual,(list,tuple)) and len(actual)==2 and actual[0]==runtime["traci_protocol"] and
            re.fullmatch(r"SUMO "+re.escape(runtime["sumo_release"]),actual[1]) is not None)


def sumo_version_output_matches(output, release):
    """Accept a complete SUMO release line, never a version prefix or suffix.

    Build/license text may occupy other lines. Only LF/CRLF separates the
    release line; whitespace, annotations and prerelease/build suffixes on
    that line are not part of an exact release.
    """
    if not isinstance(output, str):
        return False
    token = re.escape(str(release))
    pattern = r"Eclipse SUMO sumo (?:Version )?" + token
    return any(re.fullmatch(pattern, line.removesuffix("\r")) is not None
               for line in output.split("\n"))


SUMMARY_COUNTERS = ("loaded", "inserted", "running", "waiting", "ended", "arrived", "discarded")


def summary_output_contract(data, duration_s, step_s=0.05):
    """Validate the full native summary step grid and nonnegative counters.

    Loaded, inserted, ended, arrived, discarded, collisions and teleports are
    cumulative SUMO counters. Running and waiting are current populations.
    Summary collision counters differ from TraCI colliding-vehicle counts.
    Release 1.26.0 defines ended=arrived+discarded and inserted=running+arrived.
    """
    root = ET.fromstring(data)
    require(root.tag == "summary", "native_summary_XML_root")
    expected = round(float(duration_s) / float(step_s))
    steps = root.findall("step")
    require(len(steps) == expected, "native_summary_step_count")
    rows = []
    previous = {name: 0 for name in ("loaded", "inserted", "ended", "arrived", "discarded", "collisions", "teleports")}
    for index, step in enumerate(steps):
        try:
            actual_time = float(step.get("time"))
        except (TypeError, ValueError):
            raise ValueError("native_summary_invalid_time")
        require(math.isfinite(actual_time) and abs(actual_time - index * step_s) <= 1e-7,
                "native_summary_clock")
        values = {}
        for name in SUMMARY_COUNTERS + ("collisions", "teleports"):
            raw = step.get(name)
            require(raw is not None and re.fullmatch(r"[0-9]+", raw) is not None,
                    "native_summary_invalid_counter:" + name)
            values[name] = int(raw)
        for name in previous:
            require(values[name] >= previous[name], "native_summary_counter_decreased:" + name)
            previous[name] = values[name]
        require(values["inserted"] <= values["loaded"], "native_summary_inserted_exceeds_loaded")
        require(values["running"] <= values["inserted"], "native_summary_running_exceeds_inserted")
        require(values["arrived"] <= values["ended"] <= values["loaded"], "native_summary_terminal_counter_invalid")
        require(values["discarded"] <= values["loaded"], "native_summary_discarded_exceeds_loaded")
        require(values["ended"] == values["arrived"] + values["discarded"], "native_summary_ended_balance")
        require(values["inserted"] == values["running"] + values["arrived"], "native_summary_inserted_balance")
        require(values["inserted"] + values["discarded"] + values["waiting"] <= values["loaded"], "native_summary_loaded_balance")
        rows.append(dict(time_s=actual_time, **values))
    return dict(parse_complete=True, step_count=len(rows), steps=rows,
                semantics=dict(loaded="cumulative vehicles loaded from input",
                    inserted="cumulative vehicles inserted", running="vehicles running in reported step",
                    waiting="vehicles waiting for insertion in reported step",
                    ended="cumulative vehicles reaching destination or otherwise removed",
                    arrived="cumulative ended minus discarded; includes post-departure removals",
                    discarded="cumulative never-inserted vehicles permanently discarded",
                    collisions="cumulative registered collisions; not TraCI colliding vehicle count",
                    teleports="cumulative SUMO teleport counter across causes"))


def verify_receipt(archive,proposal,proposal_sha,policy_sha):
    """Reconstruct acceptance from raw broker/controller records and artifacts."""
    archive=Path(archive);receipt=json.loads((archive/"isolation_runtime.json").read_bytes())
    control=json.loads((archive/"controller_receipt.json").read_bytes())
    require(receipt["proposal_sha256"]==proposal_sha and receipt["policy_sha256"]==policy_sha,"OS_receipt_binding_mismatch")
    require(receipt["runtime_manifest_sha256"]==proposal["runtime_manifest_sha256"],"OS_receipt_runtime_binding")
    require(receipt["source_sha256"]==proposal["controller_source_sha256"],"OS_receipt_source_binding")
    require(receipt["input_sha256"]==proposal["runs"][0]["capsule_input_sha256"],"OS_receipt_input_binding")
    for name,expected in receipt["artifact_sha256"].items():require(sha(safe_relative(archive,name))==expected,"sealed_output_drift:"+name)
    required={"controller_receipt.json","executed_policy.json","capability_record.json","broker_context.json","identity_events.jsonl","identity_summary.json"}
    require(required<=set(receipt["artifact_sha256"]),"required_runtime_record_not_sealed")
    require(sha(archive/"executed_policy.json")==policy_sha,"executed_policy_drift")
    policy=json.loads((archive/"executed_policy.json").read_bytes())
    require((archive/"executed_policy.json").read_bytes()==canonical(policy),"executed_policy_not_canonical")
    require(policy["binding"]["source_sha256"]==proposal["controller_source_sha256"],"policy_source_binding")
    guard_sha=proposal["controller_source_sha256"]["stage_0_5_linux_isolation.py"]
    require(receipt["guard_sha256"]==guard_sha,"executed_guard_drift")
    require(sha(archive/"capability_record.json")==proposal["kernel_probe_sha256"],"kernel_probe_binding")
    probe=json.loads((archive/"capability_record.json").read_bytes())
    from stage_0_5_isolation_admission import probe_checks
    capability=probe_checks(probe)
    require(probe["guard_sha256"]==guard_sha and all(capability.values()),"kernel_enforcement_probe_failed")
    require(receipt["broker_context_sha256"]==sha(archive/"broker_context.json"),"broker_context_binding")
    require(control["proposal_sha256"]==proposal_sha and control["policy_sha256"]==policy_sha,"controller_receipt_binding")
    require(version_matches(control["getVersion"],proposal["runtime"]),"TraCI_protocol_or_version_mismatch")
    require(control["sumo_binary_sha256"]==proposal["runtime"]["sumo_sha256"],"runtime_binary_mismatch")
    require(control["traci_source_sha256"]==proposal["runtime"]["traci_init_sha256"],"TraCI_source_mismatch")
    require(sumo_version_output_matches(control["sumo_version_output"],proposal["runtime"]["sumo_release"]),"SUMO_version_output_mismatch")
    require(control["controller_namespaces"]==control["sumo_namespaces"]==receipt["namespaces"],"controller_or_SUMO_outside_capsule")
    require(set(receipt["namespaces"])=={"user","mnt","pid","net","ipc"} and
        all(receipt["namespaces"][n]!=policy["host_namespaces"][n] for n in receipt["namespaces"]),"host_namespace_reused")
    security=dict(NoNewPrivs="1",Seccomp="2",CapEff="0000000000000000")
    require(control["controller_security"]==control["sumo_security"]==security,"native_security_restrictions_missing")
    require(control["network_interfaces"]==["lo"],"host_network_interface_visible")
    limits=proposal["single_attempt_limits"]
    expected_cgroup={"memory.max":str(limits["process_tree_rss_bytes"]),"memory.swap.max":"0","pids.max":str(policy["tasks"]),"cpu.max":"100000 100000"}
    require(receipt["cgroup"]==expected_cgroup,"OS_resource_limits_mismatch")
    require(policy["output_bytes"]==limits["task_output_bytes"] and policy["wall_s"]==limits["per_attempt_wall_s"],"OS_output_or_timeout_binding")
    require(set(receipt["input_mounts"])==set(receipt["input_sha256"]) and
        all("ro" in row.split()[5].split(",") for row in receipt["input_mounts"].values()),"input_mount_not_readonly")
    require(receipt["payload_exit_code"]==0 and control["exit_code"]==0 and not control.get("error"),"native_execution_failed")
    require(receipt["descendants_reaped"] is True and receipt["remaining_pids"]==[],"orphan_native_children")
    samples=control["resource_samples"]
    resource_fields=["free_c_bytes","free_d_bytes","free_wsl_bytes","capsule_fs_free_bytes","capsule_fs_capacity_bytes","process_tree_rss_bytes","wall_s"]
    require(len(samples)>=2 and all(all(isinstance(s.get(k),(int,float)) and not isinstance(s[k],bool) and math.isfinite(s[k]) and s[k]>=0 for k in resource_fields) for s in samples),"resource_observation_missing")
    from stage_0_5_research_ledger import resource_reason
    require(all(resource_reason(limits,s,startup=i==0) is None and s["free_wsl_bytes"]>=limits["task_output_bytes"]+1024**3 and
        0<s["capsule_fs_free_bytes"]<=s["capsule_fs_capacity_bytes"]==limits["task_output_bytes"] for i,s in enumerate(samples)),"resource_limit_exceeded")
    clocks=[s["wall_s"] for s in samples]
    require(clocks==sorted(clocks) and max(b-a for a,b in zip(clocks,clocks[1:]))<=limits["supervision_poll_s"] and control.get("watchdog_failure") is None,"resource_supervision_incomplete")
    run=proposal["runs"][0];controls=control["controls"];step=run["internal_step_s"]
    require(len(controls)==round(run["duration_s"]/step),"control_time_support_missing")
    for i,c in enumerate(controls):
        now=i*step;target=next(x["speed_mps"] for x in run["lane_speed_schedule"] if x["start_s"]<=now<x["end_s"])
        require(c.get("failures")==[] and abs(c["applied_before_step_s"]-now)<1e-7 and abs(c["native_clock_before_s"]-now)<1e-7 and
            c["target_mps"]==target and set(c["native_lane_limits"])==set(run["supply_target_lanes"]) and
            all(isinstance(v,(int,float)) and math.isfinite(v) and abs(v-target)<1e-9 for v in c["native_lane_limits"].values()),"control_application_or_readback_failed")
    outputs={}
    for name,tag in [("fcd.xml","fcd-export"),("summary.xml","summary"),("tripinfo.xml","tripinfos")]:
        require(name in receipt["artifact_sha256"],"required_native_output_missing:"+name)
        data=(archive/name).read_bytes()
        root=ET.fromstring(data);require(root.tag==tag,"native_output_XML_root")
        if name == "summary.xml" and proposal.get("schema") in {SCHEMA, SMOKE_SCHEMA}:
            summary_output_contract(data, proposal["runs"][0]["duration_s"], proposal["runs"][0].get("internal_step_s", .05))
        outputs[name]=receipt["artifact_sha256"][name]
    identity_check = None
    if proposal.get("schema") in {SCHEMA, SMOKE_SCHEMA}:
        from stage_0_5_identity_observation import IdentityObserver
        from stage_0_5_execution_v2 import verify_journal, attach_FCD_observations
        from stage_0_5_input_fidelity import inventory
        input_data = {}
        for name, expected in run["capsule_input_sha256"].items():
            path = archive/name if (archive/name).exists() else Path(policy["inputs"][name])
            require(sha(path) == expected, "receipt_input_binding:" + name)
            input_data[name] = path.read_bytes()
        _, declarations, initial_ids, _, _ = inventory(input_data["routes.rou.xml"])
        journal = verify_journal(archive/"identity_events.jsonl")
        observer = IdentityObserver([dict(id=i, depart_s=float(v.get("depart"))) for i, v in declarations.items()], step_s=step)
        for line in (archive/"identity_events.jsonl").read_bytes().splitlines():
            frame = json.loads(line)["payload"]
            require(frame.get("phase") == "initial_snapshot" or frame.get("collision_observation_required") is True,
                    "native_collision_contract_marker_missing")
            observer.ingest(frame)
        attach_FCD_observations(observer, archive/"fcd.xml")
        observer.observe_tripinfo((archive/"tripinfo.xml").read_bytes())
        rebuilt = observer.finish()
        require(rebuilt == json.loads((archive/"identity_summary.json").read_bytes()), "receipt_identity_summary_mismatch")
        require(journal["events"] == round(run["duration_s"]/step)+1, "receipt_identity_clock_missing")
        require(rebuilt["identity_accounting_complete"] and rebuilt["native_departure_clock_complete"] and
                rebuilt["collision_coverage_complete"], "receipt_identity_observation_incomplete")
        summary = summary_output_contract((archive/"summary.xml").read_bytes(), run["duration_s"], step)
        seen = {k:set() for k in ("loaded", "departed", "arrived", "discarded")}
        seen["loaded"].update(observer.frames[0].get("loaded") or [])
        for aggregate, frame in zip(summary["steps"], observer.frames[1:]):
            for key in seen:
                require(frame.get(key) is not None or key == "discarded", "receipt_missing_identity_getter:"+key)
                seen[key].update(x["id"] if isinstance(x,dict) else x for x in frame.get(key) or [])
            require(all(aggregate[key] == value for key,value in dict(loaded=len(seen["loaded"]),
                inserted=len(seen["departed"]), arrived=len(seen["arrived"]), discarded=len(seen["discarded"]),
                ended=len(seen["arrived"])+len(seen["discarded"]), running=len(frame["active"]), waiting=len(frame["pending"])).items()),
                "receipt_summary_identity_counter_mismatch")
            require(abs(frame["time_s"]-aggregate["time_s"]-step)<1e-7, "receipt_summary_identity_clock")
            require(aggregate["collisions"] == aggregate["teleports"] == 0, "receipt_collision_or_teleport")
        require(all(r["tripinfo"] is not None for r in rebuilt["vehicles"].values()
                    if r["declaration"]["depart_s"] < run["duration_s"]), "receipt_tripinfo_missing_identity")
        identity_check = dict(conditions=dict(replayed_identity=True, all_summary_steps=True,
            collision_coverage=True, tripinfo_identity=True))
    return dict(status="Pass",kind="OS_enforced",backend="linux-userns",proposal_sha256=proposal_sha,
        identity_checks=None if identity_check is None else identity_check["conditions"],
        policy_sha256=policy_sha,runtime_manifest_sha256=proposal["runtime_manifest_sha256"],outputs=outputs,
        receipt_sha256=sha(archive/"isolation_runtime.json"),controller_sha256=sha(archive/"controller_receipt.json"),
        probes=dict(files_read_only=capability["positive_file_controls"] and all("ro" in r.split()[5].split(",") for r in receipt["input_mounts"].values()),
            exclusive_output=policy["scratch"]!=policy["archive"] and receipt["output_bytes"]<=limits["task_output_bytes"],
            forbidden_resources_denied=capability["all_negative_access_probes"],children_confined=capability["children_confined"] and control["sumo_security"]==security,
            process_tree_limited=capability["pids_enforced"] and capability["memory_enforced"] and capability["CPU_enforced"] and capability["timeout_enforced"],
            network_confined=capability["loopback_only"] and control["network_interfaces"]==["lo"]),
        scope="Engineering runtime/control/isolation acceptance, no scientific support claim")
