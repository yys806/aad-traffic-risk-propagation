"""Evidence-only B00 candidate assembly. No research execution or native launch.

This auxiliary tool is outside the frozen production source closure. Existing
receipt and technical-preflight implementations remain the authority. Every
output is exclusive; historic candidates and smoke archives are read-only.
"""
from __future__ import annotations
import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage_0_5_native_capsule_v4 import canonical, sha, require, verify_receipt

BASE = "evidence/admission/AAD-0.5-READY-TO-ADMIT-V3"
V5 = BASE + "/candidate-v5"
V6 = BASE + "/candidate-v6"
PREP = "docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5"
SMOKE = "docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution"
AUDIT = "docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6"
RUN = "V3_0750_B00_DS38_s20261201"
RUNTIME_SHA = "3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc"
CLOSURE_SHA = "b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2"
EXPECTED = {
    V5 + "/proposal.json": "e4b4dcf9e559b56be0ac50c143e3e327c336927f02d9c90c63f5c0463e93442f",
    PREP + "/smoke_proposal.json": "a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550",
    PREP + "/runtime_manifest.json": RUNTIME_SHA,
    PREP + "/smoke_envelope.json": "6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463",
    SMOKE + "/authorized_envelope.json": "a9ce5a370957387690adfcfc953e7d20d5a877d3d73e628418bd73b816b1271d",
    SMOKE + "/result.json": "ae4ce45d42b37b4b42598987c9bae22c50f69641b80ee49c5c5d2449f2df0c64",
    SMOKE + "/capsule/engineering_acceptance.json": "a3276183a38b6bfd03e5c5e0eb67a61b86a8f193d4d5d541bea208ed669dd88b",
    SMOKE + "/independent_receipt_acceptance.json": "e295f312bfa2c75258db162ee42bbeb0b1d01373060fdc641097b8c6e1784894",
    SMOKE + "/capsule/archive/isolation_runtime.json": "9c4251d748ec613214682195ce27ee6235d945fd4b25e0e86a249508414a5c5f",
    SMOKE + "/capsule/archive/controller_receipt.json": "316dcb625a55a7919a54e88e7986a7477f2972383e2d0a30d0ad94f32daf7606",
}


def relative(root, name):
    """Portable repo path, including rejection of Windows drive paths on Linux."""
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name,
            "unsafe_repository_path")
    p, w = PurePosixPath(name), PureWindowsPath(name)
    require(not p.is_absolute() and not w.drive and ".." not in p.parts and p.as_posix() == name,
            "unsafe_repository_path")
    root = Path(root).resolve()
    target = root / name
    require(target.resolve().is_relative_to(root), "repository_path_escape")
    require(not any(q.is_symlink() for q in [target, *target.parents]), "repository_symlink")
    return target


def load(root, name):
    return json.loads(relative(root, name).read_bytes())


def bound(root, name, expected):
    require(sha(relative(root, name)) == expected, "bound_file_drift:" + name)


def write(path, value):
    with Path(path).open("xb") as handle:
        handle.write(value if isinstance(value, bytes) else canonical(value) + b"\n")


def verify_map(root, mapping):
    for name, expected in mapping.items():
        bound(root, name, expected)


def verify_manifests(root, folder):
    checks = {}
    sums = relative(root, folder + "/SHA256SUMS")
    for line in sums.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        bound(root, folder + "/" + name, digest)
        checks[folder + "/" + name] = digest
    for name in ["manifest.json", "audit_manifest.json", "collection.json", "capsule_collection.json"]:
        path = relative(root, folder + "/" + name)
        if not path.exists():
            continue
        record = json.loads(path.read_bytes())
        files = record.get("files", {})
        for entry, value in files.items():
            prefix = "/capsule/" if name == "capsule_collection.json" else "/"
            digest = value["sha256"] if isinstance(value, dict) else value
            target = folder + prefix + entry
            bound(root, target, digest)
            if isinstance(value, dict) and "bytes" in value:
                require(relative(root, target).stat().st_size == value["bytes"], "collection_size_drift")
            checks[target] = digest
    return checks


def check_policy(p, smoke, policy, smoke_policy):
    for key in ["executables", "environment", "host_namespaces", "kernel_readonly", "purpose", "tasks"]:
        require(policy[key] == smoke_policy[key], "isolation_policy_invariant:" + key)
    runtime = p["runtime"]
    require(runtime == smoke["runtime"] and p["runtime_manifest_sha256"] == smoke["runtime_manifest_sha256"] == RUNTIME_SHA,
            "production_runtime_mismatch")
    require(p["controller_source_sha256"] == smoke["controller_source_sha256"], "production_source_mismatch")
    binding = policy["binding"]
    require(binding["source_sha256"] == p["controller_source_sha256"] and
            binding["runtime_manifest_sha256"] == RUNTIME_SHA and
            binding["runtime_manifest_path"] == p["runtime_manifest_path"] and
            binding["capability_record_sha256"] == p["kernel_probe_sha256"], "B00_policy_binding")
    require(binding["accepted_build"] is False, "historical_build_lock_changed")
    limits = p["single_attempt_limits"]
    for key, limit in [("memory_bytes", "process_tree_rss_bytes"), ("output_bytes", "task_output_bytes"), ("wall_s", "per_attempt_wall_s")]:
        require(policy[key] == limits[limit], "B00_resource_policy_mismatch:" + key)
    require(policy["tasks"] == 32 and policy["kernel_readonly"] == ["/proc", "/sys/fs/cgroup"], "B00_kernel_scope")
    require(policy["argv"] == [runtime["python_executable"], "-I", "-B", binding["source_files"]["stage_0_5_linux_controller_v4.py"]], "B00_controller_entry")
    expected = dict(runtime["files"])
    expected[binding["runtime_manifest_path"]] = RUNTIME_SHA
    expected[binding["capability_record_path"]] = p["kernel_probe_sha256"]
    for name, digest in p["controller_source_sha256"].items():
        path = binding["source_files"][name]
        require(path == policy["capsule"] + "/controller_sources/" + name, "B00_source_path")
        expected[path] = digest
    for name, digest in p["runs"][0]["capsule_input_sha256"].items():
        expected[policy["inputs"][name]] = digest
    require(policy["file_sha256"] == expected, "B00_exact_policy_file_closure")
    require(policy["readonly_paths"] == runtime["readonly_paths"] + [policy["capsule"] + "/controller_sources"], "B00_readonly_scope")
    require(p["linux_archive_path"] == policy["archive"] == policy["capsule"] + "/archive" and
            policy["scratch"] == policy["capsule"] + "/scratch", "B00_output_scope")


def verify_existing(root):
    verify_map(root, EXPECTED)
    inventory = dict(EXPECTED)
    for folder in [PREP, SMOKE, "docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/continuation-r2"]:
        inventory.update(verify_manifests(root, folder))
    p = load(root, V5 + "/proposal.json")
    smoke = load(root, PREP + "/smoke_proposal.json")
    require(len(p["controller_source_sha256"]) == 12 and hashlib.sha256(canonical(p["controller_source_sha256"])).hexdigest() == CLOSURE_SHA,
            "production_source_closure")
    for key in ["source_sha256", "support_input_sha256", "measurement_reference_sha256"]:
        verify_map(root, p[key]); inventory.update(p[key])
    run = p["runs"][0]
    require(len(p["runs"]) == 1 and run["id"] == RUN, "exact_B00_required")
    verify_map(root, run["input_sha256"]); inventory.update(run["input_sha256"])
    for field in ["plan", "budget", "software_validation"]:
        bound(root, p[field + "_path"], p[field + "_sha256"])
        inventory[p[field + "_path"]] = p[field + "_sha256"]
    require(p["runtime"] == load(root, PREP + "/runtime_manifest.json"), "B00_manifest_content")
    policy = load(root, PREP + "/research_policy.json")
    bound(root, PREP + "/research_policy.json", p["capsule_policy_sha256"])
    check_policy(p, smoke, policy, load(root, PREP + "/smoke_policy.json"))
    acceptance = verify_receipt(relative(root, SMOKE + "/capsule/archive"), smoke,
                                EXPECTED[PREP + "/smoke_proposal.json"], smoke["capsule_policy_sha256"])
    require(acceptance == load(root, SMOKE + "/independent_receipt_acceptance.json"), "independent_acceptance_disagreement")
    coordinator = load(root, SMOKE + "/capsule/engineering_acceptance.json")
    require(all(coordinator.get(k) == v for k, v in acceptance.items()), "coordinator_acceptance_disagreement")
    result = load(root, SMOKE + "/result.json")
    control = load(root, SMOKE + "/capsule/archive/controller_receipt.json")
    require(result["proposal_sha256"] == acceptance["proposal_sha256"] and result["run_id"] == smoke["runs"][0]["id"] and
            result["task_id"] == smoke["task_id"] and result["getVersion"] == control["getVersion"] and
            result["control_steps"] == result["simulation_steps"] == len(control["controls"]) == 60,
            "smoke_summary_disagreement")
    for key in ["actual_launch_calls", "SUMO_version_processes", "SUMO_simulation_processes", "real_TraCI_connections"]:
        require(result[key] == 1, "historical_attempt_count_disagreement")
    require(result["automatic_retry"] is False and result["new_B00_research_trajectories"] == 0 and
            result["post_execution_cleanup"]["matching_remaining_processes"] == [] and result["remaining_pids"] == [], "smoke_cleanup_or_retry")
    require(all(result["outputs"][n]["sha256"] == h for n, h in acceptance["outputs"].items()), "summary_output_hashes")
    receipt = load(root, SMOKE + "/capsule/archive/isolation_runtime.json")
    require(result["peak_process_tree_rss_bytes"] == max(s["process_tree_rss_bytes"] for s in control["resource_samples"]) and
            result["resource_samples"] == len(control["resource_samples"]) and result["cgroup"] == receipt["cgroup"] and
            result["controller_namespaces"] == control["controller_namespaces"] and result["SUMO_namespaces"] == control["sumo_namespaces"] and
            result["controller_security"] == control["controller_security"] and result["SUMO_security"] == control["sumo_security"] and
            result["controller_receipt_sha256"] == acceptance["controller_sha256"] and
            result["isolation_receipt_sha256"] == acceptance["receipt_sha256"], "summary_runtime_disagreement")
    require(result["control_readbacks_all_verified"] is True and result["speed_schedule_step_counts"] == {"10":40,"5":20}, "summary_control_disagreement")
    from stage_0_5_admission_v3 import validate_config, factor_routes
    validate_config(relative(root, run["input_files"]["run.sumocfg"]).read_bytes(), run)
    factor_routes(relative(root, run["paired_base_routes"]).read_bytes(), relative(root, run["input_files"]["routes.rou.xml"]).read_bytes(), ramp=False)
    from stage_0_5_input_fidelity import audit_bundle
    inputs = {n:relative(root, q).read_bytes() for n, q in run["input_files"].items()}
    input_audit = audit_bundle(inputs["routes.rou.xml"], inputs["network.net.xml"], inputs["run.sumocfg"])
    require(input_audit["initial_count"] == 117 and input_audit["total_count"] == 1150, "B00_inventory_drift")
    references = [list(csv.DictReader(io.StringIO(relative(root, n).read_text(encoding="utf-8")))) for n in p["measurement_reference_sha256"]]
    require(len(references) == 1 and len(references[0]) == 18 and len({(r["t_block"], r["y_block"]) for r in references[0]}) == 18, "measurement_reference_units")
    budget = load(root, p["budget_path"])
    require(p["single_attempt_limits"] == run["single_attempt_limits"] == budget["single_attempt_limits"] and
            budget["workers"] == 1 and budget["automatic_retry"] is False, "B00_budget_drift")
    require(not relative(root, run["artifact_path"]).exists(), "B00_output_already_exists")
    require(relative(root, run["artifact_path"]).is_relative_to(relative(root, budget["output_root"])), "B00_output_outside_scope")
    from stage_0_5_isolation_admission import software_extension_verified
    require(software_extension_verified(root, load(root, p["software_validation_path"]), p["source_sha256"]), "software_evidence_invalid")
    require(all(p[k] is False for k in ["execution_allowed", "researcher_confirmed", "protocol_frozen"]) and
            all(v is False for v in p["admission"].values()), "historical_research_flags_changed")
    return dict(status="Pass", acceptance=acceptance, verified_files=inventory,
                production_source_sha256=p["controller_source_sha256"], production_source_closure_sha256=CLOSURE_SHA,
                input_inventory={k:v for k,v in input_audit.items() if k != "rows"}, measurement_reference_units=18,
                policy_semantics="Same guard/runtime/read-only/allowlist rules; exact distinct B00 inputs and original B00 budgets, not smoke budgets",
                scientific_scope="Static input/resource eligibility only; actual insertion, support and scientific acceptance remain unverified",
                SUMO_launches=0, real_TraCI_connections=0, new_B00_research_trajectories=0)


def scientific_diff(old, new):
    allowed = {"plan_version", "status", "git_commit", "git_state", "previous_proposal", "isolation", "linux_proposal_path",
               "integration_acceptance_path", "integration_acceptance_sha256"}
    changed = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
    require(changed <= allowed, "unauthorized_proposal_difference:" + str(sorted(changed - allowed)))
    require(old["runs"] == new["runs"], "scientific_run_changed")
    for key in ["execution_allowed", "researcher_confirmed", "protocol_frozen"]:
        require(new[key] is False, "research_approval_changed")
    require(new["admission"] == old["admission"], "research_policy_approval_changed")
    return dict(status="Pass", scientific_fields_deep_equal=True,
                all_other_top_level_fields_deep_equal=True,
                differences=[dict(field=k, before=old.get(k), after=new.get(k), reason="Candidate version, evidence-only integration proof or exact proposal location; no scientific change") for k in sorted(changed)])


def check_certificate_claims(certificate, p, verified):
    require(certificate["schema"] == "aad.native-integration-acceptance.v1" and certificate["status"] == "Pass" and
            certificate["accepted_for_new_task"] is True and certificate["input_and_test_resource_scope_accepted"] is True,
            "invalid_integration_certificate")
    require(certificate["evidence_sha256"] == verified["verified_files"] and
            certificate["controller_source_sha256"] == p["controller_source_sha256"] and
            certificate["runtime_manifest_sha256"] == p["runtime_manifest_sha256"] == RUNTIME_SHA and
            certificate["production_source_closure_sha256"] == CLOSURE_SHA, "certificate_evidence_mismatch")
    require(certificate["b00_binding"] == dict(run_id=RUN, seed=p["runs"][0]["seed"], output_artifact_path=p["runs"][0]["artifact_path"],
        source_sha256=p["source_sha256"], input_sha256=p["runs"][0]["input_sha256"],
        support_input_sha256=p["support_input_sha256"], measurement_reference_sha256=p["measurement_reference_sha256"],
        single_attempt_limits=p["single_attempt_limits"], policy_path=PREP + "/research_policy.json", policy_sha256=p["capsule_policy_sha256"]),
        "certificate_B00_scope_mismatch")
    require(certificate["candidate_v5_proposal_path"] == V5 + "/proposal.json" and
            certificate["candidate_v5_proposal_sha256"] == EXPECTED[V5 + "/proposal.json"] and
            certificate["smoke_proposal_path"] == PREP + "/smoke_proposal.json" and
            certificate["smoke_proposal_sha256"] == EXPECTED[PREP + "/smoke_proposal.json"] and
            certificate["smoke_archive_path"] == SMOKE + "/capsule/archive", "certificate_receipt_scope")
    require(certificate["historical_incident"] == "Not Accepted" and certificate["historical_incident_reclassified"] is False and
            certificate["research_authorization_migrated"] is False, "certificate_authority_exceeded")
    require("proposal_sha256" not in certificate, "certificate_self_reference")


# This read-only child queries capability interfaces, not enforcement probes.
# Prior six-mode enforcement receipts remain separately hash-verified above.
ENVIRONMENT_CODE = r'''
import ctypes,json,os,pathlib,subprocess
libc=ctypes.CDLL(None,use_errno=True)
landlock_abi=libc.syscall(444,0,0,1)
manager=subprocess.run(['/usr/bin/systemctl','--user','show','--property=Version','--property=ControlGroup'],capture_output=True,timeout=10)
print(json.dumps(dict(kernel=os.uname().release,OS_release=pathlib.Path('/etc/os-release').read_text(),
 landlock_abi=landlock_abi,seccomp_actions=pathlib.Path('/proc/sys/kernel/seccomp/actions_avail').read_text().split(),
 cgroup_controllers=pathlib.Path('/sys/fs/cgroup/cgroup.controllers').read_text().split(),
 systemd_exit_code=manager.returncode,systemd_stdout=manager.stdout.decode(),systemd_stderr=manager.stderr.decode(),
 no_native_processes_started=True)))
'''


def collect_live(root, output):
    output = Path(output)
    output.mkdir(exist_ok=False)
    p = load(root, V5 + "/proposal.json")
    base = ["wsl.exe", "-d", "Ubuntu", "--cd", "/home/shen/AAD", "--exec", p["runtime"]["python_executable"], "-I", "-B"]
    records = {}
    for name, args in [("precertificate_preflight", [p["linux_driver"], "preflight", p["linux_proposal_path"]]),
                       ("environment", ["-c", ENVIRONMENT_CODE])]:
        command = base + args
        r = subprocess.run(command, capture_output=True, timeout=120)
        for suffix, data in [("stdout", r.stdout), ("stderr", r.stderr)]:
            write(output / (name + "." + suffix), data)
        records[name] = dict(argv=command, exit_code=r.returncode, timeout_s=120,
            stdout_sha256=hashlib.sha256(r.stdout).hexdigest(), stderr_sha256=hashlib.sha256(r.stderr).hexdigest())
        write(output / (name + ".command.json"), records[name])
        require(r.returncode == 0, "read_only_Linux_check_failed:" + name)
    pre = json.loads((output / "precertificate_preflight.stdout").read_bytes())
    env = json.loads((output / "environment.stdout").read_bytes())
    require(pre["proposal_sha256"] == EXPECTED[V5 + "/proposal.json"] and pre["linux_runtime_verified"] is True and
            pre["runtime_files_verified"] == len(p["runtime"]["files"]), "live_B00_runtime_binding")
    require(env["kernel"] == p["runtime"]["kernel"] == load(root, PREP + "/probe/record.json")["kernel"] and
            env["OS_release"] == p["runtime"]["OS_release"], "current_kernel_or_OS_drift")
    require(env["landlock_abi"] >= 3 and {"allow", "errno"} <= set(env["seccomp_actions"]) and
            {"cpu", "memory", "pids"} <= set(env["cgroup_controllers"]) and env["systemd_exit_code"] == 0, "current_isolation_interfaces_unavailable")
    report = dict(status="Pass", verified_at=datetime.now(timezone.utc).isoformat(), preflight=pre, environment=env,
                  commands=records, SUMO_launches=0, real_TraCI_connections=0, new_B00_research_trajectories=0,
                  scope="Read-only current runtime/policy/resources/interfaces; no new enforcement probe, simulator or research execution")
    write(output / "live_prerequisites.json", report)
    return report


def verify_live_record(root):
    report = load(root, AUDIT + "/live/live_prerequisites.json")
    require(report["status"] == "Pass", "live_prerequisites_missing")
    for name, command in report["commands"].items():
        require(command["exit_code"] == 0, "live_command_failed")
        for suffix in ["stdout", "stderr"]:
            bound(root, AUDIT + "/live/" + name + "." + suffix, command[suffix + "_sha256"])
    return report


def prepare(root):
    root = Path(root).resolve()
    target = relative(root, V6)
    require(not target.exists(), "new_immutable_candidate_required")
    audit = relative(root, AUDIT)
    require(not audit.exists(), "new_exclusive_audit_required")
    verified = verify_existing(root)
    audit.mkdir()
    write(audit / "independent_evidence_verification.json", verified)
    live = collect_live(root, audit / "live")
    old = load(root, V5 + "/proposal.json")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    certificate = dict(schema="aad.native-integration-acceptance.v1", certificate_version=1, status="Pass",
        accepted_for_new_task=True, input_and_test_resource_scope_accepted=True,
        scope="B00 static input/read-only resource binding and verified production Linux engineering chain only",
        exclusions=["scientific hypothesis", "actual B00 insertion or measured support", "research authorization", "protocol freeze", "Stage 1.1"],
        candidate_v5_proposal_path=V5 + "/proposal.json", candidate_v5_proposal_sha256=EXPECTED[V5 + "/proposal.json"],
        smoke_proposal_path=PREP + "/smoke_proposal.json", smoke_proposal_sha256=EXPECTED[PREP + "/smoke_proposal.json"],
        smoke_archive_path=SMOKE + "/capsule/archive", evidence_sha256=verified["verified_files"],
        runtime_manifest_path=PREP + "/runtime_manifest.json", runtime_manifest_sha256=RUNTIME_SHA,
        production_source_closure_sha256=CLOSURE_SHA, controller_source_sha256=old["controller_source_sha256"],
        b00_binding=dict(run_id=RUN, seed=old["runs"][0]["seed"], output_artifact_path=old["runs"][0]["artifact_path"],
            source_sha256=old["source_sha256"], input_sha256=old["runs"][0]["input_sha256"],
            support_input_sha256=old["support_input_sha256"], measurement_reference_sha256=old["measurement_reference_sha256"],
            single_attempt_limits=old["single_attempt_limits"], policy_path=PREP + "/research_policy.json", policy_sha256=old["capsule_policy_sha256"]),
        verification_path=AUDIT + "/independent_evidence_verification.json", verification_sha256=sha(audit / "independent_evidence_verification.json"),
        live_prerequisites_path=AUDIT + "/live/live_prerequisites.json", live_prerequisites_sha256=sha(audit / "live/live_prerequisites.json"),
        verifier_path="code/scripts/prepare_stage_0_5_b00_admission_v6.py", verifier_sha256=sha(__file__),
        verified_at=live["verified_at"], observed_HEAD=head, historical_incident="Not Accepted",
        historical_incident_reclassified=False, research_authorization_migrated=False)
    target.mkdir()
    write(target / "integration_acceptance.json", certificate)
    p = copy.deepcopy(old)
    p.update(plan_version="candidate-v6-verified-linux-smoke", status="Proposed / READY_FOR_RESEARCHER_APPROVAL",
        git_commit=head, git_state=dict(observed_HEAD=head, branch="main", working_tree_dirty=True,
            semantics="Exact unchanged production/scientific closure plus separately hashed engineering helper and certificate"),
        previous_proposal=dict(path=V5 + "/proposal.json", sha256=EXPECTED[V5 + "/proposal.json"], authorization_migrated=False),
        integration_acceptance_path=V6 + "/integration_acceptance.json", integration_acceptance_sha256=sha(target / "integration_acceptance.json"),
        linux_proposal_path="/mnt/d/shen/TJU/AAD/" + V6 + "/proposal.json")
    p["isolation"].update(accepted_for_new_task=True, input_and_test_resource_scope_accepted=True,
        report_path=p["integration_acceptance_path"], report_sha256=p["integration_acceptance_sha256"],
        controller_capsule_status="Verified production smoke; static B00 input/resource eligibility accepted; research launch remains locked")
    diff = scientific_diff(old, p)
    write(target / "scientific_diff.json", diff)
    write(target / "proposal.json", p)
    from stage_0_5_linux_execution_v4 import technical_preflight_v4
    static = technical_preflight_v4(root, target / "proposal.json", RUN, inspect_runtime=False)
    write(target / "static_technical_preflight.json", static)
    require(static["technical_errors"] == ["live_Linux_runtime_and_resource_check_required"], "unexpected_static_error:" + str(static))
    command = ["wsl.exe", "-d", "Ubuntu", "--cd", "/home/shen/AAD", "--exec", p["runtime"]["python_executable"],
        "-I", "-B", p["linux_driver"], "preflight", p["linux_proposal_path"]]
    checked = subprocess.run(command, capture_output=True, timeout=120)
    write(audit / "live/candidate_preflight.stdout", checked.stdout)
    write(audit / "live/candidate_preflight.stderr", checked.stderr)
    write(audit / "live/candidate_preflight.command.json", dict(argv=command, exit_code=checked.returncode,
        stdout_sha256=hashlib.sha256(checked.stdout).hexdigest(), stderr_sha256=hashlib.sha256(checked.stderr).hexdigest()))
    require(checked.returncode == 0 and json.loads(checked.stdout)["proposal_sha256"] == sha(target / "proposal.json"), "exact_candidate_Linux_preflight")
    full = technical_preflight_v4(root, target / "proposal.json", RUN, inspect_runtime=True)
    write(target / "technical_preflight.json", full)
    require(full["technical_errors"] == [] and full["ready"] is True, "live_technical_preflight_blocked:" + str(full))
    write(target / "admission_profile.json", dict(status=full["status"], accepted_for_new_task=False,
        execution_allowed=False, researcher_confirmed=False, protocol_frozen=False, native_launch_locked=True,
        historical_incident="Not Accepted", SUMO_launches=0, real_TraCI_connections=0, new_trajectories=0))
    write(target / "manifest.json", dict(schema="aad.admission-candidate-manifest.v1", status=full["status"],
        proposal_sha256=sha(target / "proposal.json"),
        files={q.name:sha(q) for q in sorted(target.iterdir()) if q.is_file()},
        manifest_self_hash="External SHA256SUMS/audit binding; manifest excluded from its own file map"))
    return verify_candidate(root)


def verify_candidate(root):
    verified = verify_existing(root)
    p = load(root, V6 + "/proposal.json")
    manifest = load(root, V6 + "/manifest.json")
    folder = relative(root, V6)
    require(set(manifest["files"]) == {q.name for q in folder.iterdir() if q.name != "manifest.json"}, "incomplete_candidate_manifest")
    verify_map(root, {V6 + "/" + n:h for n,h in manifest["files"].items()})
    require(manifest["proposal_sha256"] == sha(folder / "proposal.json"), "candidate_proposal_drift")
    scientific_diff(load(root, V5 + "/proposal.json"), p)
    certificate = load(root, p["integration_acceptance_path"])
    bound(root, p["integration_acceptance_path"], p["integration_acceptance_sha256"])
    require(p["isolation"]["report_path"] == p["integration_acceptance_path"] and
            p["isolation"]["report_sha256"] == p["integration_acceptance_sha256"], "certificate_alias_mismatch")
    check_certificate_claims(certificate, p, verified)
    verify_map(root, certificate["evidence_sha256"])
    for key in ["verification", "live_prerequisites", "verifier"]:
        bound(root, certificate[key + "_path"], certificate[key + "_sha256"])
    verify_live_record(root)
    require(load(root, V6 + "/admission_profile.json")["native_launch_locked"] is True and
            all(load(root, V6 + "/admission_profile.json")[k] is False for k in
                ["accepted_for_new_task", "execution_allowed", "researcher_confirmed", "protocol_frozen"]), "research_profile_unlocked")
    from stage_0_5_linux_execution_v4 import technical_preflight_v4
    static = technical_preflight_v4(root, folder / "proposal.json", RUN, inspect_runtime=False)
    require(static["technical_errors"] == ["live_Linux_runtime_and_resource_check_required"], "independent_static_preflight_failed")
    full = load(root, V6 + "/technical_preflight.json")
    require(full["proposal_sha256"] == manifest["proposal_sha256"] and full["technical_errors"] == [] and
            full["status"] == "READY_FOR_RESEARCHER_APPROVAL" and full["ready"] is True and bool(full["authorization_pending"]), "candidate_technical_state")
    return dict(status=full["status"], proposal_sha256=manifest["proposal_sha256"], manifest_sha256=sha(folder / "manifest.json"),
                integration_certificate_sha256=sha(folder / "integration_acceptance.json"), verify_receipt="Pass",
                scientific_definition_unchanged=True, research_authorization=False, SUMO_launches=0,
                real_TraCI_connections=0, new_B00_research_trajectories=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify-existing", "prepare", "verify"])
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if args.mode == "verify-existing":
        report = verify_existing(args.repo_root)
        print(json.dumps(dict(status=report["status"], files_verified=len(report["verified_files"]),
            production_source_files=len(report["production_source_sha256"]), verify_receipt=report["acceptance"]["status"])))
    else:
        print(json.dumps(prepare(args.repo_root) if args.mode == "prepare" else verify_candidate(args.repo_root), sort_keys=True))


if __name__ == "__main__":
    main()
