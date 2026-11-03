"""Read-only SUMO acceptance analysis and portable packaging. Never launches SUMO."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskprop.controller_evidence import EvidenceJournal
from riskprop.message_driven_longitudinal_controller import canonical_bytes
from riskprop.p7_evidence_verification import verify_run

EPS = 1e-9  # numerical comparison only; not a formal action threshold


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(canonical_bytes(value))


def normalized_xml(p):
    return ET.canonicalize(ET.tostring(ET.parse(p).getroot(), encoding="unicode"), strip_text=True)


def difference_summary(samples, key, step_s):
    changed = [(t, d[key]) for t, d in samples if abs(d[key]) > EPS]
    runs = []
    for t, delta in changed:
        if runs and abs(t - runs[-1]["last_sample_s"] - step_s) <= EPS:
            runs[-1]["last_sample_s"] = t
            runs[-1]["samples"] += 1
        else:
            runs.append({"first_sample_s": t, "last_sample_s": t, "samples": 1})
    return {"different_samples": len(changed), "first_difference_s": changed[0][0] if changed else None,
        "last_difference_s": changed[-1][0] if changed else None,
        "max_abs_difference": max((abs(d[key]) for _, d in samples), default=None),
        "sample_support_duration_s": len(changed) * step_s,
        "first_to_last_span_s": changed[-1][0] - changed[0][0] if changed else None,
        "consecutive_sample_runs": runs,
        "duration_semantics": "sample count times dt and first-to-last span; no interpolation or formal observation window"}


def analyze(root, output):
    run = output / "enabled_v2"
    old = root / "code/outputs/engineering/p7_task2_20261103_v1"
    config = read(run / "controller_config.json")
    summary = read(run / "run_summary.json")
    preflight = read(output / "preflight/task_start.json")
    verification = verify_run(run, output / "captured_v2")
    journal = EvidenceJournal.from_dict(read(run / "controller_evidence.json"))
    audit = journal.validate()
    bykind = {kind: [r for r in journal.records if r["kind"] == kind] for kind in audit["counts_by_kind"]}
    records_by_id = {r["context"]["record_id"]: r for r in journal.records}
    unknowns_explained = all(i["code"] in {"UNKNOWN_SOURCE_QUALIFICATION", "UNKNOWN_SAFETY", "MISSING_STATE_READBACK", "UNKNOWN_EXECUTION"}
        and (i["code"] not in {"MISSING_STATE_READBACK", "UNKNOWN_EXECUTION"}
             or records_by_id[i["record_id"]]["data"].get("execution_status") == "VEHICLE_EXITED") for i in audit["issues"])
    actual = read(run / "actual_trajectory.json")
    present = [r for r in actual if r["readback_status"] == "OBSERVED"]
    events = read(run / "simulation_events.json")
    warnings = {line.strip().lower() for name in ("sumo.log", "sumo_errors.log")
        for line in (run / name).read_text(encoding="utf-8", errors="replace").splitlines()
        if "emergency braking" in line.lower()}
    min_a = min(r["acceleration_mps2"] for r in present)
    anomaly = {"native_decel_mps2": config["native_decel_mps2"], "roundoff_tolerance_mps2": EPS,
        "minimum_actual_acceleration_mps2": min_a, "maximum_observed_deceleration_mps2": max(0, -min_a),
        "abnormal_deceleration_samples": sum(r["acceleration_mps2"] < -config["native_decel_mps2"] - EPS for r in present),
        "emergency_braking_warning_count": len(warnings),
        "emergency_stopping_steps": sum(bool(e["emergency_stopping_vehicle_ids"]) for e in events),
        "collision_steps": sum(bool(e["colliding_vehicle_ids"]) for e in events),
        "teleport_steps": sum(bool(e["teleport_vehicle_ids"]) for e in events),
        "event_observation_steps": len(events), "log_hashes": {n: sha(run / n) for n in ("sumo.log", "sumo_errors.log")}}
    included = [r for r in bykind["consumption"] if r["data"]["consumption_status"] == "POLICY_INPUT_INCLUDED"]
    commands = bykind["command"]
    first_command = min(r["time"]["native_timestamp"] for r in commands)
    releases = [r for r in commands if r["data"]["command_type"] == "RESTORE_NATIVE_MAX_SPEED"]
    api = [read(run / r["data"]["execution_interface_ref"]) for r in commands]
    after_expiry = [r for r in included if r["time"]["native_timestamp"] >= config["message_valid_until_s"]]
    empty_after = []
    for decision in bykind["decision"]:
        if decision["time"]["native_timestamp"] >= config["message_valid_until_s"]:
            d = read(run / decision["data"]["decision_output_ref"])
            empty_after.append(read(run / d["input_snapshot_ref"])["messages"] == [])
    comparison, baseline_verification = {}, {}
    current_by_step = {r["simulation_step"]: r for r in present}
    physical_keys = ("speed_mps", "acceleration_mps2", "lane_position_m")
    for name in ("no_message", "disabled"):
        baseline = old / "smoke" / name
        baseline_verification[name] = verify_run(baseline, old / "captured_implementation_v1")
        previous = [r for r in read(baseline / "actual_trajectory.json") if r["vehicle_existence"]]
        pairs = [(r, current_by_step[r["simulation_step"]]) for r in previous if r["simulation_step"] in current_by_step]
        samples = [(a["simulation_time_s"], {k: b[k] - a[k] for k in physical_keys}) for a, b in pairs]
        old_config = read(baseline / "controller_config.json")
        changes = {k for k in set(old_config) | set(config) if old_config.get(k) != config.get(k)}
        allowed = {"config_version", "policy_version", "source", "reference_deceleration_mps2"}
        network_same = all(normalized_xml(run / "network" / n) == normalized_xml(baseline / "network" / n)
            for n in ("dual_corridor.net.xml", "p7.rou.xml"))
        comparison[name] = {"classification": "ENGINEERING_DIAGNOSTIC_ONLY", "baseline_reused_not_rerun": True,
            "config_differences": sorted(changes), "only_authorized_candidate_version_changes": changes <= allowed,
            "network_and_initialization_xml_semantically_identical": network_same,
            "shared_observed_steps": len(pairs),
            "common_times_identical": all(abs(a["simulation_time_s"] - b["simulation_time_s"]) <= EPS for a, b in pairs),
            "before_message_trajectory_identical": all(all(abs(d[k]) <= EPS for k in physical_keys) for t, d in samples if t < config["message_generated_time_s"]),
            "through_first_command_trajectory_identical": all(all(abs(d[k]) <= EPS for k in physical_keys) for t, d in samples if t <= first_command),
            "first_command_time_s": first_command,
            "speed_difference_mps": difference_summary(samples, "speed_mps", config["step_s"]),
            "acceleration_difference_mps2": difference_summary(samples, "acceleration_mps2", config["step_s"]),
            "post_expiry_common_samples": sum(t >= config["message_valid_until_s"] for t, _ in samples),
            "post_expiry_max_abs_speed_difference_mps": max(abs(d["speed_mps"]) for t, d in samples if t >= config["message_valid_until_s"]),
            "post_expiry_last_sample_speed_difference_mps": samples[-1][1]["speed_mps"],
            "numerical_comparison_tolerance": EPS, "formal_action_threshold_frozen": False,
            "causal_action_effect": "NOT_IDENTIFIED", "regional_risk_effect": "UNKNOWN"}
    risk = read(run / bykind["risk_observation"][0]["data"]["observation_ref"])
    start_receipt = read(run / "launch_consumed.json")
    checks = {"one_invocation_normal_completion": summary["status"] == "PASS" and read(output / "one_launch_result.json")["return_code"] == 0,
        "single_process_start_guard": start_receipt["launch_attempt"] == 1 and start_receipt["explicit_port"] > 0 and start_receipt["process_relaunch_allowed"] is False,
        "config_bytes_unchanged": sha(run / "controller_config.json") == preflight["config_hash"],
        "no_abnormal_braking_or_incident": all(anomaly[k] == 0 for k in ("abnormal_deceleration_samples", "emergency_braking_warning_count", "emergency_stopping_steps", "collision_steps", "teleport_steps")),
        "all_simulation_steps_have_event_readback": [e["simulation_step"] for e in events] == list(range(1, events[-1]["simulation_step"] + 1)),
        "actual_agreed_policy_consumption": bool(included) and all(r["data"]["adoption_boundary_status"] == "AGREED" for r in included),
        "message_generation_at_2_s": len(bykind["message"]) == 1 and bykind["message"][0]["time"]["native_timestamp"] == 2.0,
        "send_delivery_validation_present": all(bykind[k] for k in ("send", "delivery", "validation")) and any(r["data"]["validation_status"] == "VALID" for r in bykind["validation"]),
        "commands_acknowledged_with_matching_getter": bool(api) and all(r["status"] == "ACKNOWLEDGED" and r["getter_max_speed_mps"] == r["value_mps"] for r in api),
        "all_actual_readbacks_complete": all(all(r.get(k) is not None for k in ("position_xy_m", "speed_mps", "acceleration_mps2", "lane_position_m", "edge_id", "lane_id")) and (r["leader_id"] is None or all(r.get(k) is not None for k in ("leader_speed_mps", "net_gap_m"))) for r in present),
        "continuous_identity_and_exit": [r["simulation_step"] for r in actual] == list(range(actual[0]["simulation_step"], actual[-1]["simulation_step"] + 1)) and len({r["vehicle_incarnation_id"] for r in actual}) == 1 and actual[-1]["readback_status"] == "VEHICLE_EXITED",
        "native_following_retained": summary["native_speed_modes"] == [31] and summary["native_following_below_vehicle_max_samples"] > 0 and summary["native_without_traci_speed_max_abs_difference"] == 0,
        "restore_exactly_at_expiry": len(releases) == 1 and releases[0]["time"]["native_timestamp"] == 8.0 and releases[0]["data"]["command_value"] == config["target_max_speed_mps"],
        "validation_reports_expired_at_8_s": any(r["time"]["native_timestamp"] == 8.0 and r["data"]["validation_status"] == "EXPIRED" for r in bykind["validation"]),
        "no_policy_input_inclusion_at_or_after_8_s": not after_expiry and bool(empty_after) and all(empty_after),
        "post_restore_actual_max_speed_readback": all(r["vehicle_max_speed_mps"] == config["target_max_speed_mps"] for r in present if r["simulation_time_s"] > 8.0),
        "p3_structural_validation": audit["structural_status"] in ("VALID", "VALID_WITH_UNKNOWNS"),
        "all_unknown_categories_explained": unknowns_explained,
        "p4_execution_action_associations": bool(bykind["execution"]) and len(bykind["action_observation"]) == len(actual),
        "risk_stays_unknown_without_formal_scope": risk["risk_effect_status"] == "UNKNOWN" and risk["formal_rho_or_p2_recomputed"] is False and risk["formal_region"] is None,
        "no_fabricated_safety_or_formal_source": not bykind["safety"] and all(r["data"]["qualification_status"] == "UNKNOWN" for r in bykind["source"]),
        "valid_reused_baseline_comparisons": all(c["only_authorized_candidate_version_changes"] and c["network_and_initialization_xml_semantically_identical"] and c["common_times_identical"] and c["before_message_trajectory_identical"] and c["through_first_command_trajectory_identical"] and c["shared_observed_steps"] == len(present) for c in comparison.values()),
        "actual_action_response_observed": all(c["speed_difference_mps"]["different_samples"] > 0 and c["acceleration_difference_mps2"]["different_samples"] > 0 for c in comparison.values())}
    state = "ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS" if all(checks.values()) else "ENGINEERING_REVALIDATION_BLOCKED"
    return {"task_id": "AAD-P7-TASK2.1-20261103", "status": state, "checks": checks,
        "failed_checks": [k for k, v in checks.items() if not v], "anomaly": anomaly,
        "action_response_status": "ACTION_RESPONSE_OBSERVED_ENGINEERING_ONLY" if checks["actual_action_response_observed"] else "ACTION_RESPONSE_NOT_DEMONSTRATED",
        "comparison": comparison, "p3_p4": verification,
        "unknown_issue_counts": dict(Counter(i["code"] for i in audit["issues"])),
        "unknown_explanations": {"UNKNOWN_SOURCE_QUALIFICATION": "synthetic source; no formal qualification",
            "UNKNOWN_SAFETY": "no independent safety producer by D6; not a missing native-constraint check",
            "MISSING_STATE_READBACK": "only the recorded 35.4s VEHICLE_EXITED observation has null motion values",
            "UNKNOWN_EXECUTION": "VEHICLE_EXITED is recorded explicitly; no inferred motion after exit"},
        "counts_by_kind": audit["counts_by_kind"], "policy_input_included": len(included),
        "expiry": {"valid_interval_s": [2.0, 8.0], "right_endpoint_exclusive": True,
            "restoration_time_s": releases[0]["time"]["native_timestamp"] if releases else None,
            "post_expiry_included_receipts": len(after_expiry), "empty_policy_inputs_after_expiry": sum(empty_after)},
        "risk_effect_status": "UNKNOWN", "scientific_claim_eligible": False, "new_sumo_starts": 1,
        "baseline_runs_reused": 2, "additional_sumo_starts": 0,
        "environment_warning": "SUMO_HOME XML validation disabled warning preserved in runner_console.log; no emergency warning"}


def package(root, output, result):
    dest = root / "evidence/research/P7_TASK2_1_20261103"
    dest.mkdir(parents=True, exist_ok=True)
    run = output / "enabled_v2"
    write(dest / "validation.json", result)
    for name in ("controller_config.json", "run_summary.json", "run_config.json", "provenance.json", "sumo_launch.json", "launch_consumed.json", "artifact_manifest.json", "command_tenures.json"):
        (dest / name).write_bytes((run / name).read_bytes())
    for name in ("controller_evidence.json", "association_validation.json"):
        (dest / (name + ".gz")).write_bytes(gzip.compress((run / name).read_bytes(), mtime=0))
    for name in ("one_launch_invocation.json", "one_launch_result.json"):
        write(dest / name, read(output / name))
    for source, name in (("preflight/task_start.json", "task_start.json"), ("preflight/baseline_and_environment.json", "baseline_and_environment.json"),
            ("preflight/offline_tests.json", "initial_test_attempt.json"), ("preflight/offline_tests_corrected.json", "offline_test_results.json")):
        data = read(output / source)
        if "output" in data:
            text = data.pop("output")
            data["output_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            data["summary_line"] = next((s for s in reversed(text.splitlines()) if "passed" in s), None)
        write(dest / name, data)
    write(dest / "comparison.json", result["comparison"])
    write(dest / "anomaly_checks.json", result["anomaly"])
    write(dest / "p3_p4_validation.json", result["p3_p4"])
    bundle = {}
    for owner, directory in (("captured_v2", output / "captured_v2"), ("task_start_sources", output / "preflight/task_start_sources")):
        bundle[owner] = {p.relative_to(directory).as_posix(): base64.b64encode(p.read_bytes()).decode("ascii") for p in directory.rglob("*.py") if "__pycache__" not in p.parts}
    (dest / "source_bytes.json.gz").write_bytes(gzip.compress(canonical_bytes(bundle), mtime=0))
    provenance = read(run / "provenance.json")
    source_paths = list(provenance["source_closure"]) + ["code/scripts/finalize_p7_task2_1.py", "code/tests/test_p7_task2_1_revalidation.py"]
    write(dest / "source_manifest.json", {"captured_v2": provenance["source_closure"],
        "task_start_sources": read(output / "preflight/task_start.json")["task_start_source_hashes"],
        "current_source_hashes": {p: sha(root / p) for p in source_paths},
        "git_index_source_hashes": {p: hashlib.sha256(subprocess.check_output(["git", "cat-file", "blob", ":" + p], cwd=root)).hexdigest() for p in source_paths},
        "byte_view_semantics": "runtime bytes remain authoritative; a Git variant is accepted only when explicitly hashed and differing solely in CRLF/LF, never other content",
        "raw_capture_manifest_sha256": sha(run / "artifact_manifest.json"),
        "raw_trajectory_sha256": sha(run / "actual_trajectory.json"), "raw_data_portability": "LOCAL_ONLY",
        "config_original_bytes_sha256": sha(run / "controller_config.json"),
        "controller_evidence_raw_sha256": sha(run / "controller_evidence.json")})
    # Payload/first included input byte witnesses, not full raw trajectories or logs.
    records = read(run / "controller_evidence.json")["records"]
    selected = [r["data"]["payload_ref"] for r in records if r["kind"] == "message"]
    for r in records:
        if r["kind"] == "decision" and r["data"]["consumed_message_refs"]:
            selected.append(read(run / r["data"]["decision_output_ref"])["input_snapshot_ref"])
            break
    write(dest / "byte_samples.json", {p: base64.b64encode((run / p).read_bytes()).decode("ascii") for p in selected})
    command_refs = [r["data"]["execution_interface_ref"] for r in records if r["kind"] == "command"]
    command_bytes = {p: base64.b64encode((run / p).read_bytes()).decode("ascii") for p in command_refs}
    (dest / "command_bytes.json.gz").write_bytes(gzip.compress(canonical_bytes(command_bytes), mtime=0))
    execution_rows = [r for r in records if r["kind"] == "execution" and r["data"]["state_readback_ref"]]
    selected_readbacks = {execution_rows[0]["data"]["state_readback_ref"], execution_rows[-1]["data"]["state_readback_ref"]}
    post_restore = next(r for r in execution_rows if r["time"]["native_timestamp"] > 8.0)
    selected_readbacks.add(post_restore["data"]["state_readback_ref"])
    write(dest / "readback_samples.json", {p: base64.b64encode((run / p).read_bytes()).decode("ascii") for p in selected_readbacks})
    start = read(output / "preflight/task_start.json")
    protected = {p: h for p, h in start["initial_changed_hashes"].items() if p.startswith("evidence/research/P7_TASK2_20261103/")}
    protected.update(start["protected_history_hashes"])
    changed = [p for p, h in protected.items() if sha(root / p) != h]
    if changed:
        raise RuntimeError("historical evidence drift: " + repr(changed))
    write(dest / "historical_protection.json", {"files_verified": len(protected), "hashes": protected, "changed": changed})
    if (output / "project_checks.json").exists():
        write(dest / "project_checks.json", read(output / "project_checks.json"))
    entries = [{"source_path": p.relative_to(root).as_posix(), "snapshot_path": p.relative_to(root).as_posix(),
        "size_bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(dest.rglob("*"))
        if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts]
    sums = chr(10).join(e["sha256"] + "  " + Path(e["snapshot_path"]).relative_to(dest.relative_to(root)).as_posix() for e in entries) + chr(10)
    (dest / "SHA256SUMS").write_text(sums, encoding="utf-8", newline=chr(10))
    p = dest / "SHA256SUMS"
    entries.append({"source_path": p.relative_to(root).as_posix(), "snapshot_path": p.relative_to(root).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha(p)})
    path = root / "evidence/EVIDENCE_MANIFEST.json"
    manifest = read(path)
    result_id = "RES-P7-TASK2.1-20261103"
    manifest["results"] = [r for r in manifest["results"] if r["result_id"] != result_id] + [{"result_id": result_id, "files": entries}]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8", newline=chr(10))
    return len(entries)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--package", action="store_true")
    args = p.parse_args()
    root, output = args.repo_root.resolve(), args.output.resolve()
    result = analyze(root, output)
    write(output / "analysis.json", result)
    count = package(root, output, result) if args.package else None
    print(json.dumps({k: result[k] for k in ("status", "failed_checks", "anomaly", "action_response_status", "comparison", "counts_by_kind", "expiry")}, ensure_ascii=False, indent=2))
    if count:
        print("PORTABLE_FILES", count)


if __name__ == "__main__":
    main()
