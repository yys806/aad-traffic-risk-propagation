"""Verify kernel observations and keep capability distinct from runtime admission."""
import hashlib
import json
from pathlib import Path
import re
import sys


def probe_checks(record):
    """Recompute from observations/counters, never trust a supplied all-true map."""
    records={r["mode"]:r for r in record["commands"]}
    if set(records)!={"basic","output","pids","memory","cpu","timeout"}:
        raise ValueError("incomplete_kernel_probe_modes")
    basic=records["basic"].get("observations",{})
    def count(mode,name,key):
        data=records[mode].get("runtime",{}).get("kernel_counters",{}).get(name,"")
        return int(dict(row.split() for row in data.splitlines()).get(key,"0"))
    negatives=["readonly_input","forbidden_read","forbidden_write","forbidden_metadata_write","unregistered_exec",
               "output_symlink","host_unix_socket","vsock","namespace_escape","host_loopback","external_network"]
    return dict(
        positive_file_controls=basic.get("allowed_read") is True and basic.get("allowed_write") is True,
        all_negative_access_probes=all(basic.get(n,{}).get("denied") is True for n in negatives),
        children_confined=basic.get("child_inherits_denial") is True,
        loopback_only=basic.get("isolated_loopback_works") is True and basic.get("host_loopback",{}).get("denied") is True,
        all_namespaces_changed=bool(record.get("host_namespaces")) and all(basic.get("namespace_ids",{}).get(n) not in [None,v] for n,v in record["host_namespaces"].items()),
        kernel_security_status=basic.get("status")==dict(CapEff="0000000000000000",NoNewPrivs="1",Seccomp="2"),
        output_enforced=all(records["output"].get("observations",{}).get(n,{}).get("denied") is True for n in ["per_file_limit","aggregate_tmpfs_limit"]),
        pids_enforced=records["pids"].get("observations",{}).get("pids_limit",{}).get("errno")==11 and count("pids","pids.events","max")>0,
        memory_enforced=records["memory"].get("runtime",{}).get("payload_exit_code")==-9 and count("memory","memory.events","oom_kill")>0,
        CPU_enforced=count("cpu","cpu.stat","nr_throttled")>0,
        timeout_enforced=records["timeout"]["elapsed_s"]<5 and bool(records["timeout"].get("runtime",{}).get("termination_signals")),
        failure_outputs_preserved=all(n+"_started" in records[n].get("runtime",{}).get("artifact_sha256",{}) for n in ["memory","timeout"]),
        successful_controls=all(records[n]["exit_code"]==0 for n in ["basic","output","pids","cpu"]),
        expected_resource_failures=all(records[n]["exit_code"]!=0 for n in ["memory","timeout"]))


def capability_report(repo, record_path, expected_sha):
    root=Path(repo).resolve();path=(root/record_path).resolve()
    if not path.is_relative_to(root):raise ValueError("probe_evidence_outside_repository")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha:raise ValueError("probe_evidence_drift")
    record=json.loads(data)
    guard=root/"code/scripts/stage_0_5_linux_isolation.py"
    if hashlib.sha256(guard.read_bytes()).hexdigest()!=record["guard_sha256"]:
        raise ValueError("kernel_guard_source_drift")
    checks=probe_checks(record)
    if checks!=record["checks"]:raise ValueError("probe_summary_observation_mismatch")
    if not all(checks.values()):raise ValueError("kernel_probe_failed")
    return dict(capability_verified=True,scope="Linux harmless capsules only",checks=checks,
                kernel=record["kernel"],installed_versions=record["installed_versions"],
                source_sha256=record["guard_sha256"],runtime_files_sha256=record["runtime_files_sha256"],
                accepted_for_new_task=False)


def runtime_reasons(proposal, capability):
    if proposal.get("schema")=="aad.native-admission.v4":
        from stage_0_5_native_capsule_v4 import version_matches
        runtime=proposal.get("runtime",{});observed=capability.get("controller_receipt",{})
        errors=[]
        if not runtime or not observed:return ["bound_production_runtime_receipt_missing"]
        if runtime.get("sumo_release")!="1.26.0" or not version_matches(observed.get("getVersion"),runtime):
            errors.append("bound_Linux_SUMO_or_TraCI_version_mismatch")
        for actual,expected in [("sumo_binary_sha256","sumo_sha256"),("traci_source_sha256","traci_init_sha256")]:
            if not runtime.get(expected) or observed.get(actual)!=runtime[expected]:errors.append("bound_runtime_hash_mismatch:"+actual)
        if not observed.get("controller_namespaces") or observed.get("controller_namespaces")!=observed.get("sumo_namespaces"):
            errors.append("production_controller_and_SUMO_namespace_mismatch")
        return errors
    errors=[]
    version=proposal["native_runtime_version"][1].removeprefix("SUMO ")
    packages=dict(row.split("\t",1) for row in capability["installed_versions"].splitlines() if "\t" in row)
    installed=re.split(r"[+~-]",packages.get("sumo","Unknown"))[0]
    if installed!=version:
        errors.append("Linux_SUMO_version_mismatch:installed="+installed+",required="+version)
    if sys.platform!="linux" or not str(proposal["native_binary"]).startswith("/"):
        errors.append("Windows_native_controller_not_inside_verified_Linux_capsule")
    # Native path needs both controller and SUMO in one isolated net namespace.
    if proposal.get("isolation",{}).get("controller_capsule_policy") is None:
        errors.append("exact_Linux_controller_capsule_and_runtime_not_bound")
    return errors


def require_native_context(context):
    """Defense before Popen: no bare host-native process after future unlock."""
    if sys.platform!="linux":raise PermissionError("native_controller_requires_OS_capsule")
    policy=context.get("controller_capsule_policy")
    if not isinstance(policy,dict):raise PermissionError("controller_capsule_policy_missing")
    status=Path("/proc/self/status").read_text()
    values=dict(line.split(":",1) for line in status.splitlines() if ":" in line)
    if any(values.get(k,"").strip()!=v for k,v in dict(NoNewPrivs="1",Seccomp="2",CapEff="0000000000000000").items()):
        raise PermissionError("native_controller_kernel_restrictions_missing")
    if any(__import__("os").readlink("/proc/self/ns/"+name)==value for name,value in policy["host_namespaces"].items()):
        raise PermissionError("native_controller_namespace_not_separated")
    if context["native_command"][0] not in policy["executables"]:
        raise PermissionError("native_binary_not_in_OS_policy")
    return True


def software_extension_verified(repo,record,sources):
    """Reuse the existing full regression only for unchanged scientific sources.

    This is explicitly an isolation-only targeted extension, never a claim that
    the old 1130 tests were rerun on the new source tree.
    """
    if record.get("validation_mode") not in {"isolation_targeted_extension","production_capsule_targeted_extension"} or record.get("source_sha256")!=sources:
        return False
    if record.get("targeted",{}).get("exit_code")!=0:return False
    reuse=record["reused_full_regression"]
    path=(Path(repo)/reuse["path"]).resolve()
    if not path.is_relative_to(Path(repo).resolve()):return False
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=reuse["sha256"]:return False
    previous=json.loads(data)
    if previous["full"]["exit_code"]!=0:return False
    permitted={"code/scripts/stage_0_5_execution_v2.py","code/scripts/stage_0_5_admission_v3.py","code/scripts/stage_0_5_acceptance_v3.py"}
    if record["validation_mode"]=="production_capsule_targeted_extension":
        permitted.update("code/scripts/"+n+".py" for n in ["stage_0_5_research_ledger","run_stage_0_5_admission_v3",
            "stage_0_5_linux_isolation","stage_0_5_isolation_admission"])
        permitted.add("code/tests/test_stage_0_5_linux_isolation.py")
    changed={n for n,h in previous["source_sha256"].items() if sources.get(n)!=h}
    if not changed<=permitted or changed!=set(record["modified_existing_sources"]):return False
    added=set(sources)-set(previous["source_sha256"])
    if added!=set(record["added_sources"]):return False
    return all(not n.startswith("code/src/") for n in added)
