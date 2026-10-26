"""Static technical admission separated from human authorization. Never launches."""
from __future__ import annotations
import hashlib
import json
import site
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from stage_0_5_input_fidelity import config_references, inventory, xml
from stage_0_5_isolation_v2 import Scope, sha
from stage_0_5_research_ledger import canonical, resource_reason

TASK = "AAD-0.5-READY-TO-ADMIT-V3"
MANDATORY_SOURCES = ["code/scripts/" + n + ".py" for n in [
    "stage_0_5_execution_v2", "stage_0_5_identity_observation", "stage_0_5_input_fidelity", "stage_0_5_isolation_v2",
    "stage_0_5_research_ledger", "stage_0_5_acceptance_v3", "stage_0_5_admission_v3", "prepare_stage_0_5_admission_v3", "validate_stage_0_5_admission_v3", "validate_stage_0_5_research_v2", "run_stage_0_5_admission_v3"]]
MANDATORY_SOURCES += ["code/src/riskprop/" + n + ".py" for n in ["stage_0_5_scene_reconstruction", "stage_0_5_state_support",
    "stage_0_5_d1_measurement", "stage_0_5_sumo", "formal_risk_measurement"]]


def validate_config(data, run):
    refs = config_references(data, expected_inputs={"net-file":"network.net.xml", "route-files":"routes.rou.xml"})
    cfg = xml(data)
    for tag, expected in {"fcd-output":"fcd.xml", "summary-output":"summary.xml", "tripinfo-output":"tripinfo.xml",
            "tripinfo-output.write-unfinished":"true", "tripinfo-output.write-undeparted":"true",
            "device.fcd.period":"0.1", "step-method.ballistic":"true", "threads":"1"}.items():
        nodes = cfg.findall(".//" + tag)
        if len(nodes) != 1 or nodes[0].get("value") != expected:
            raise ValueError("output_or_execution_option:" + tag)
    for tag, expected in {"begin":0, "end":run["duration_s"], "step-length":.05, "seed":run["seed"]}.items():
        nodes = cfg.findall(".//" + tag)
        if len(nodes) != 1 or float(nodes[0].get("value")) != expected:
            raise ValueError("time_or_seed_option:" + tag)
    if run["evaluation_elapsed_s"] != [120,390] or run["duration_s"] != 420:
        raise ValueError("unapproved_window_or_duration")
    return refs


def factor_routes(before, after, *, ramp):
    """Exact existing 60s / 20..25s / 0.05s rule, no new scientific tolerance."""
    a, av, ai, _, _ = inventory(before)
    b, bv, bi, _, _ = inventory(after)
    if set(av) != set(bv) or set(ai) != set(bi):
        raise ValueError("factor_identity_change")
    expected = {k:dict(v.attrib) for k,v in av.items()}
    groups = {}
    for ident,v in av.items():
        if v.get("route") == "entering" and ident not in ai:
            groups.setdefault(int(float(v.get("depart")) // 60), []).append(ident)
    if ramp:
        for block, ids in groups.items():
            ids.sort(key=lambda k:(float(av[k].get("depart")),k))
            for i, ident in enumerate(ids):
                t = block * 60 + 20 + (5 * i / (len(ids)-1) if len(ids)>1 else 0)
                expected[ident]["depart"] = f"{round(t/.05)*.05:.2f}"
    if any(dict(bv[k].attrib) != attrs for k,attrs in expected.items()):
        raise ValueError("factor_attribute_scope_or_timing")
    if a.attrib != b.attrib or [ET.tostring(n) for n in a if n.tag!='vehicle'] != [ET.tostring(n) for n in b if n.tag!='vehicle']:
        raise ValueError("factor_type_or_route_definition_change")
    if any(list(av[k]) or list(bv[k]) for k in av):
        raise ValueError("unexpected_nested_vehicle_definition")
    order = sorted(av, key=lambda k:(float(expected[k]["depart"]),k)) if ramp else list(av)
    if list(bv) != order:
        raise ValueError("factor_order_change")
    return dict(vehicles=len(av),initial=len(ai),ramp_planned=sum(map(len,groups.values())),
                changed_departures=sum(av[k].attrib != bv[k].attrib for k in av),
                blocks={str(k):len(v) for k,v in groups.items()}, allowed_fields=["noninitial entering depart"] if ramp else [])


def technical_preflight(repo, proposal_path, run_id, *, resource_sample=None):
    from stage_0_5_execution_v2 import NATIVE_LAUNCH_LOCKED, environment_binding, gate_reasons
    repo = Path(repo).resolve()
    errors = []
    p = json.loads(Path(proposal_path).read_bytes())
    raw_sha = sha(proposal_path)
    pending = gate_reasons(p, {}, run_id, raw_sha, task_id=TASK)
    run = next((r for r in p.get("runs", []) if r.get("id") == run_id), None)
    if run is None:
        return dict(technical_errors=["run_not_in_proposal"], authorization_pending=pending, ready=False)
    try:
        if not set(MANDATORY_SOURCES) <= set(p["source_sha256"]):
            raise ValueError("missing_execution_or_measurement_source_binding")
        extra=set(p["source_sha256"])-set(MANDATORY_SOURCES)-{"code/tests/test_stage_0_5_admission_v3.py","AGENTS.md"}
        if any(not n.startswith("code/src/riskprop/") or not n.endswith(".py") for n in extra):
            raise ValueError("unregistered_source_role")
        if not p.get("external_file_sha256") or p.get("native_binary") not in p["external_file_sha256"]:
            raise ValueError("native_binary_binding_missing")
        if not p.get("software_validation_path") or not p.get("software_validation_sha256"):
            raise ValueError("software_validation_record_missing")
        required_tools = {"_simulation.py", "_vehicle.py", "domain.py", "connection.py", "constants.py", "tripinfo_file.xsd"}
        if not required_tools <= {Path(n).name for n in p["external_file_sha256"]}:
            raise ValueError("tool_or_output_schema_binding_missing")
        bindings = dict(p["source_sha256"]); bindings.update(run["input_sha256"])
        bindings.update(p.get("support_input_sha256", {}))
        bindings.update(p["external_file_sha256"]); bindings.update(p["measurement_reference_sha256"])
        bindings.update({p["plan_path"]:p["plan_sha256"], p["budget_path"]:p["budget_sha256"],
                         p["isolation"]["report_path"]:p["isolation"]["report_sha256"],
                         p["runtime_dependency_manifest"]:p["runtime_dependency_manifest_sha256"]})
        bindings[p["software_validation_path"]]=p["software_validation_sha256"]
        scope = Scope(repo, bindings, run["artifact_path"])
        snapshots = {n:scope.read_bound(n) for n in bindings}
        software=json.loads(snapshots[p["software_validation_path"]])
        if (software.get("source_sha256")!=p["source_sha256"] or software.get("targeted",{}).get("exit_code")!=0
                or software.get("full",{}).get("exit_code")!=0):raise ValueError("software_validation_source_mismatch")
        if set(run["input_files"]) != {"network.net.xml","routes.rou.xml","run.sumocfg"} or set(run["input_files"].values()) != set(run["input_sha256"]):
            raise ValueError("inexact_input_file_map")
        validate_config(snapshots[run["input_files"]["run.sumocfg"]],run)
        factor_routes(scope.read_bound(run["paired_base_routes"]), snapshots[run["input_files"]["routes.rou.xml"]], ramp=run["factors"]["ramp"])
        if p["environment"] != environment_binding(p["environment"]["packages"]):
            raise ValueError("environment_binding_drift")
        if not p.get("native_environment") or not p.get("runtime_dependency_manifest"):
            raise ValueError("native_environment_or_dependencies_missing")
        if (not isinstance(p.get("native_runtime_version"),list) or len(p["native_runtime_version"]) != 2 or
                not isinstance(p["native_runtime_version"][0],int) or not p["native_runtime_version"][1] or not p.get("tool_version_source")):
            raise ValueError("native_tool_version_binding_missing")
        dependency = json.loads(snapshots[p["runtime_dependency_manifest"]])
        runtime_roots = [Path(sys.base_prefix).resolve(),Path(site.getusersitepackages()).resolve(),Path(p["native_binary"]).resolve().parent,Path(p["traci_tools_root"]).resolve()]
        for n in dependency.get("files", {}):
            path=scope._lexical(n)
            if not any(path.is_relative_to(r) for r in runtime_roots):
                raise ValueError("dependency_path_outside_runtime")
        if not dependency.get("files") or any(sha(Path(n)) != h for n,h in dependency["files"].items()):
            raise ValueError("runtime_dependency_drift")
        expected_lanes = ["main_2_"+str(i) for i in range(5)]
        if run["supply_target_lanes"] != expected_lanes:
            raise ValueError("supply_lane_binding")
        expected_schedule = ([dict(start_s=0,end_s=180,speed_mps=10),dict(start_s=180,end_s=240,speed_mps=5),dict(start_s=240,end_s=420,speed_mps=10)]
                             if run["factors"]["supply"] else [dict(start_s=0,end_s=420,speed_mps=10)])
        if run["lane_speed_schedule"] != expected_schedule:
            raise ValueError("supply_schedule_binding")
        if scope.output.exists():
            raise ValueError("capsule_output_already_exists")
        if resource_sample is not None:
            limits = json.loads(snapshots[p["budget_path"]])["single_attempt_limits"]
            if resource_reason(limits,resource_sample,startup=True):
                raise ValueError("resource_preflight_failed")
        else:
            errors.append("fresh_resource_preflight_required")
        if p["isolation"].get("accepted_for_new_task") is not True:
            errors.append("OS_native_isolation_not_accepted")
        if NATIVE_LAUNCH_LOCKED:
            errors.append("native_build_remains_locked_pending_OS_acceptance_and_review")
    except (KeyError, ValueError, OSError) as error:
        errors.append(type(error).__name__+":"+str(error))
    return dict(task_id=TASK,proposal_sha256=raw_sha,run_id=run_id,technical_errors=errors,
                authorization_pending=pending,ready=not errors,
                status="READY_FOR_RESEARCHER_APPROVAL" if not errors else "BLOCKED_ENGINEERING",
                new_SUMO_launches=0,new_trajectories=0)
