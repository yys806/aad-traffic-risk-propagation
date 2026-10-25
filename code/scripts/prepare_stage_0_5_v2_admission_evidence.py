"""Offline engineering summaries. No input mutation, simulator import or process."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path

from stage_0_5_input_fidelity import audit_bundle, compare_initial_policy, inventory
from stage_0_5_isolation_v2 import sha

TASK = "AAD-0.5-INTERACTION-RESEARCH-V2"
LOCAL = Path("code/outputs/formal/calibration/stage_0_5_v2_admission_engineering_v1")
RESULT = "RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1"
MODULES = ["stage_0_5_identity_observation", "stage_0_5_input_fidelity", "stage_0_5_isolation_v2", "stage_0_5_execution_v2",
           "review_stage_0_5_c6_admission_v1", "verify_stage_0_5_c6_admission_v1", "validate_stage_0_5_v2_admission",
           "prepare_stage_0_5_v2_admission_evidence", "export_stage_0_5_v2_admission_evidence"]


def write(path, value):
    with path.open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def prepare(root, output):
    if not output.resolve().is_relative_to((root / LOCAL).resolve()):
        raise ValueError("preparation_output_scope")
    output.mkdir(parents=True, exist_ok=False)
    read_bindings = {}
    def read(name):
        data = (root / name).read_bytes()
        read_bindings[name] = hashlib.sha256(data).hexdigest()
        return json.loads(data)
    ds = read("evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/review_proposal.json")
    old = read("evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/review_ready_plan.json")
    current = read("docs/audits/stage_0_5_interaction_research_v2/review_proposal.json")
    failure = read("evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/failure_review.json")
    for name, expected in ds["source_sha256"].items():
        if sha(root / name) != expected:
            raise ValueError("historical_bound_source_changed:" + name)
    audit, full = {}, {}
    parent_root = Path("code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs")
    for parent in ["ID1_SUPPLY_0750", "ID2_SUPPLY_0805", "ID3_RAMP_0750"]:
        data = {}
        for filename in ["routes.rou.xml", "network.net.xml", "run.sumocfg"]:
            name = (parent_root / parent / filename).as_posix()
            if sha(root / name) != ds["approved_input_sha256"][name]:
                raise ValueError("original_input_drift:" + name)
            data[filename] = (root / name).read_bytes()
            read_bindings[name] = hashlib.sha256(data[filename]).hexdigest()
        value = audit_bundle(data["routes.rou.xml"], data["network.net.xml"], data["run.sumocfg"])
        full[parent] = value
        audit[parent] = {k: v for k, v in value.items() if k != "rows"}
    comparisons = []
    for run in ds["runs"]:
        files = {}
        for name, expected in run["inputs"].items():
            if sha(root / name) != expected:
                raise ValueError("candidate_input_drift")
            files[Path(name).name] = (root / name).read_bytes()
            read_bindings[name] = expected
        parent = root / parent_root / run["parent_id"]
        before = (parent / "routes.rou.xml").read_bytes()
        _, _, initial, _, _ = inventory(before)
        targets = [ident for ident, v in initial.items() if float(v.get("departSpeed")) == 10]
        changed = compare_initial_policy(before, files["routes.rou.xml"], target_ids=targets)
        if any(files[n] != (parent / n).read_bytes() for n in ["network.net.xml", "run.sumocfg"]):
            raise ValueError("candidate_network_or_config_changed")
        candidate = audit_bundle(files["routes.rou.xml"], files["network.net.xml"], files["run.sumocfg"])
        comparisons.append(dict(id=run["id"], comparison=changed,
            potential_main2_dynamic_numeric_speed_conflicts=candidate["potential_dynamic_pulse_conflicts"],
            actual_insertion="Unknown; no trajectory generated"))
    init_report = dict(status="static_input_scope_verified_not_dynamic_acceptance", originals=audit, candidates=comparisons,
        main2_0805_other_numeric_speeds_mps=sorted(float(row["depart_speed"]) for row in full["ID2_SUPPLY_0805"]["rows"]
                                                if row["edge"] == "main_2" and float(row["depart_speed"]) != 10),
        i0007_0750=next(row for row in full["ID1_SUPPLY_0750"]["rows"] if row["id"] == "i0007_i0007"),
        i0007_warning_still_unresolved=True, warning_source="RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/failure_review.json/native_errors",
        discarded_identity="Unknown from existing total count alone", historical_discarded_total=failure["input"]["native_discarded"],
        policy_options=[dict(id="DS38_0750_only", scope="0750 38 initial vehicles; 0805 paused", status="Proposed", dynamic_eligible=False),
                        dict(id="affected_start_edge", scope="0750 38 /0805 52 on main_2; upstream anomalies remain", status="Proposed_not_prepared", dynamic_eligible=False),
                        dict(id="broader_reconstruction", scope="researcher-defined; all initial max not assumed", status="Proposed_not_prepared", dynamic_eligible=False)],
        new_formal_XML_written=False, Gate_changed=False)
    write(output / "initialization_audit.json", init_report)
    write(output / "initialization_full_local.json", full)
    tools = Path(old["traci_tools_root"])
    api_files = {}
    wanted = {"_simulation.py": ["getTime", "getDeltaT", "getLoadedIDList", "getDepartedIDList", "getArrivedIDList", "getPendingVehicles", "getStartingTeleportIDList", "getEndingTeleportIDList", "getCollidingVehiclesNumber"],
              "_vehicle.py": ["getDeparture", "getDepartDelay", "getLaneID", "getSpeed"], "domain.py": ["getIDList"]}
    for filename, names in wanted.items():
        path = tools / "traci" / filename
        digest = sha(path)
        if digest != old["external_file_sha256"][str(path)]:
            raise ValueError("installed_API_file_changed:" + filename)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = {node.name: node.lineno for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names}
        if set(functions) != set(names):
            raise ValueError("required_API_missing")
        api_files[filename] = dict(path=str(path), sha256=digest, functions=functions, matches_prior_tool_binding=True)
    binary = ds["sumo_binary"]
    if sha(Path(binary["path"])) != binary["sha256"]:
        raise ValueError("installed_SUMO_binary_hash_changed")
    api = dict(schema="aad.identity-contract.v1", implementation="code/scripts/stage_0_5_identity_observation.py",
        installed_API=api_files, installed_binary_sha256=binary["sha256"],
        version_evidence="1.26.0 recorded in prior failed FCD header; binary/API hashes match prior bindings; no current native query",
        runtime_handshake="Unknown; getVersion may only be checked after a future separately authorized connection",
        official_version_sources=["https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/tools/traci/_simulation.py",
                                  "https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/tools/traci/_vehicle.py",
                                  "https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/src/libsumo/Vehicle.cpp"],
        semantics=dict(event_lists="last completed simulation step, recorded with observation time and evidence interval",
                       pending="explicit getter identity snapshot", visible_IDs="on-road, parking or remote-controlled; not the complete loaded set",
                       on_road="separate nonempty getLaneID observation", actual_departure="getDeparture; no replacement by event observation time or FCD",
                       actual_insertion_speed="Unknown without native departure-speed output; post-step getSpeed is separately labelled",
                       discard="no verified native ID getter; explicit identity evidence required; absence/counts cannot establish it",
                       initial_snapshot="no completed-step interval; event lists unavailable, separate from subsequent coverage",
                       None_vs_empty="None unavailable; [] available empty", interruption="nonterminal identities right censored; unknown remains unknown"),
        states=["Unknown", "pending_native", "active_native", "teleporting_native", "arrived_native", "discarded_explicit_evidence"],
        synthetic_validation_only=True, native_insertion_accepted=False)
    write(output / "identity_contract.json", api)
    local = root / LOCAL
    history = json.loads((local / "inputs/history_allowlist_v2.json").read_text(encoding="utf-8"))
    comparison = json.loads((local / "measurements_v2/comparison_summary.json").read_text(encoding="utf-8"))
    independent = json.loads((local / "independent_verification_v1/independent_verification.json").read_text(encoding="utf-8"))
    independent["read_sha256"] = {Path(k).relative_to(root).as_posix(): v for k, v in independent["read_sha256"].items()}
    comparison["event_member_sets_scope"] = "full-context lists, distinct from local onset-attributed frozen-window N"
    write(output / "history_allowlist.json", history)
    write(output / "C6_comparison.json", comparison)
    write(output / "C6_independent_verification.json", independent)
    profile = dict(task_id=TASK, schema="aad.v2-admission-engineering.v1", execution_allowed=False, researcher_confirmed=False,
        protocol_frozen=False, accepted_for_new_task=False, native_launch_build_lock=True,
        scientific_matrix="Proposed", initialization_policy="Awaiting Researcher Decision", delta=None, h=None, B=None,
        budget_sha256=sha(root / "code/configs/stage_0_5_interaction_research_v2.json"),
        existing_unapproved_proposal_sha256=sha(root / "docs/audits/stage_0_5_interaction_research_v2/review_proposal.json"),
        native_adapter="interfaces implemented; no native process/connection/trajectory tested",
        historical_isolation_incident="POLICY-A-VALIDATION-SCOPE-01: Not Accepted", native_isolation="Unknown / Not Accepted",
        native_processes_created=0, new_trajectories=0, Gate_changed=False,
        pending=["scientific plan/init/repeat decisions", "native OS access proof", "native actual insertion/fidelity evidence",
                 "future per-run manipulation acceptance contract; conservative default rejects unproved native checks"])
    write(output / "admission_profile.json", profile)
    source_names = ["code/scripts/" + n + ".py" for n in MODULES] + ["code/tests/test_stage_0_5_v2_admission.py",
        "code/scripts/stage_0_5_research_ledger.py", "code/scripts/validate_stage_0_5_research_v2.py", "code/configs/stage_0_5_interaction_research_v2.json"]
    source_names += list(history["core_sha256"])
    source_hashes = {name: sha(root / name) for name in source_names}
    write(output / "provenance.json", dict(task_id=TASK, result_id=RESULT, git_base="5899465f7c934c7544f04ef2ba290147e4999deb",
        source_sha256=source_hashes, static_input_sha256=read_bindings, scientific_source_changed=False,
        offline_allowlist_sha256=sha(local / "inputs/history_allowlist_v2.json"),
        offline_full_result_sha256=sha(local / "measurements_v2/comparison_summary.json"),
        independent_full_result_sha256=sha(local / "independent_verification_v1/independent_verification.json"),
        executed_measurement_wrapper_sources={p.name: sha(p) for p in (local / "executed_sources_measurements_v2").iterdir()},
        history_preserved="No historical inputs/results/ledgers written; old manifests must also match at closeout",
        new_trajectories=0, native_isolation_accepted=False))
    write(output / "validation_record.json", dict(status="software_tests_in_progress", native_processes_created=0, new_trajectories=0,
        recorded_offline_failures=["prepare v1 rejected output grouping tag; corrected without changing XML", "measurements_v1 could not import installed pyarrow in restricted environment; six failures retained"],
        native_execution_tested=False))
    return profile


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.repo_root.resolve(), a.output.resolve()), ensure_ascii=False))
