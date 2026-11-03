"""Read-only P7 byte/foreign-key verification and separate smoke acceptance."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .controller_evidence import EvidenceJournal
from .message_driven_longitudinal_controller import byte_hash, canonical_bytes


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def assess_smoke(root: Path) -> dict:
    rows = read_json(root / "actual_trajectory.json")
    logs = [root / "sumo_errors.log", root / "sumo.log"]
    warning_lines = {line.strip().lower() for p in logs if p.exists()
                     for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
                     if "emergency braking" in line.lower()}
    warnings = len(warning_lines)  # SUMO duplicates one event into --log and --error-log.
    actual = [r for r in rows if r["readback_status"] == "OBSERVED"]
    old = read_json(root / "run_summary.json")
    blocked = warnings > 0 or old["status"] != "PASS"
    return {"condition": old["condition"], "capture_reported_status": old["status"],
        "acceptance_status": "BLOCKED_ABNORMAL_BRAKING" if warnings else old["status"],
        "emergency_braking_warning_count": warnings,
        "observed_min_acceleration_mps2": min(r["acceleration_mps2"] for r in actual),
        "collision_count": old["collision_count"], "teleport_count": old["teleport_count"],
        "log_hashes": {p.name: byte_hash(p.read_bytes()) for p in logs if p.exists()},
        "new_sumo_runs_after_detection": 0, "accepted": not blocked,
        "original_capture_preserved": True}


def verify_run(root: Path, captured_source_root: Path | None = None) -> dict:
    manifest = read_json(root / "artifact_manifest.json")
    for relative, digest in manifest["files"].items():
        assert byte_hash((root / relative).read_bytes()) == digest, relative
    bundle = read_json(root / "controller_evidence.json")
    journal = EvidenceJournal.from_dict(bundle)
    audit = journal.validate()
    records = journal.records
    run_config = read_json(root / "run_config.json")
    for record in records:
        for k in ("adoption_mode", "assignment_id", "adoption_mode_source", "adoption_mode_version"):
            assert record["context"][k] == run_config[k], (record["context"]["record_id"], k)
    decisions = {r["data"]["decision_id"]: r for r in records if r["kind"] == "decision"}
    commands = {r["data"]["command_id"]: r for r in records if r["kind"] == "command"}
    checked = Counter()
    for r in records:
        d, kind = r["data"], r["kind"]
        if kind == "message":
            assert byte_hash((root / d["payload_ref"]).read_bytes()) == d["payload_hash"]
            checked["payload_byte_hash"] += 1
        if kind == "decision":
            output = read_json(root / d["decision_output_ref"])
            if d["decision_status"] != "FAILED":
                snap = read_json(root / output["input_snapshot_ref"])
                assert byte_hash((root / output["input_snapshot_ref"]).read_bytes()) == d["input_snapshot_hash"]
                if run_config["adoption_mode"] == "DISABLED":
                    assert snap["messages"] == [] and d["consumed_message_refs"] == []
                checked["input_snapshot_byte_hash"] += 1
        if kind == "consumption":
            assert d["input_snapshot_hash"] == decisions[d["decision_id"]]["data"]["input_snapshot_hash"]
            if run_config["adoption_mode"] == "DISABLED":
                assert d["consumption_status"] != "POLICY_INPUT_INCLUDED"
            checked["consumption_decision"] += 1
        if kind == "command":
            raw = read_json(root / d["execution_interface_ref"])
            assert raw["api"] == "traci.vehicle.setMaxSpeed"
            assert raw["command_id"] == d["command_id"] and raw["decision_id"] == d["decision_id"]
            assert raw["value_mps"] == d["command_value"]
            checked["actual_command_boundary"] += 1
        if kind == "execution":
            if d["state_readback_ref"] is None:
                assert d["execution_status"] in ("RIGHT_CENSORED", "UNOBSERVABLE", "UNKNOWN", "VEHICLE_EXITED")
                assert all(d[k] is None for k in ("actual_acceleration", "actual_speed", "actual_position"))
                checked["explicit_unknown_execution"] += 1
                continue
            raw = read_json(root / d["state_readback_ref"])
            assert raw["vehicle_incarnation_id"] == r["context"]["vehicle_incarnation_id"]
            assert raw["simulation_step"] == r["time"]["simulation_step"]
            assert d["command_id"] in commands
            for actual, key in (("actual_acceleration", "acceleration_mps2"), ("actual_speed", "speed_mps"), ("actual_position", "lane_position_m")):
                assert d[actual] == raw.get(key)
            checked["execution_actual_state"] += 1
        if kind == "risk_observation":
            raw = read_json(root / d["observation_ref"])
            assert raw["risk_effect_status"] == "UNKNOWN" and raw["formal_rho_or_p2_recomputed"] is False
            assert byte_hash((root / raw["measurement_ref"]).read_bytes()) == raw["measurement_sha256"]
            checked["risk_status_reference"] += 1
    provenance = read_json(root / "provenance.json")
    assert byte_hash(canonical_bytes(provenance["source_closure"])) == provenance["source_closure_hash"]
    for r in records:
        if r["kind"] == "controller":
            assert r["data"]["controller_code_hash"] == provenance["source_closure_hash"]
            assert r["data"]["policy_config_hash"] == byte_hash((root / "controller_config.json").read_bytes())
    if captured_source_root is not None:
        for relative, digest in provenance["source_closure"].items():
            assert byte_hash((captured_source_root / relative).read_bytes()) == digest, relative
    assert audit["counts_by_kind"]["safety"] == 0
    return {"status": "BYTE_AND_ASSOCIATION_VERIFIED", "artifact_files_verified": len(manifest["files"]),
        "checked_relations": dict(checked), "record_count": audit["record_count"],
        "counts_by_kind": audit["counts_by_kind"], "structural_status": audit["structural_status"],
        "unknown_issue_counts": dict(Counter(i["code"] for i in audit["issues"])),
        "producer_map": {k: sorted({r["context"]["producer_id"] for r in records if r["kind"] == k}) for k in audit["counts_by_kind"]},
        "captured_source_bytes_verified": captured_source_root is not None, "smoke_acceptance": assess_smoke(root)}
