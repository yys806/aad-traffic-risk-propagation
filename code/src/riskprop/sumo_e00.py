"""Minimal real-SUMO E00 runner and read-only analyzer.

This module deliberately implements only the E00 infrastructure run.  It is
not a scientific effect estimator: all generated runs are marked
``scientific_claim_eligible=False`` and risk rows are validation records.
"""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .formal_artifacts import (
    TABLE_REQUIRED_COLUMNS,
    FormalArtifactError,
    build_run_manifest,
    collect_run_provenance,
    validate_run_manifest,
    validate_theory_artifact_schema,
)
from .formal_design import (
    validate_four_cell_configs,
    validate_pre_treatment_equivalence,
    validate_protocol_lifecycle,
    validate_run_state_isolation,
    validate_simulation_time_alignment,
    validate_vehicle_id_lifecycle,
)


SUMO_CELLS = ("s0c0", "s0c1", "s1c0", "s1c1")
NET_EDGES = (
    ("src_in", "src_n0", "src_n1", 100.0),
    ("src_road", "src_n1", "src_n2", 300.0),
    ("src_out", "src_n2", "src_n3", 100.0),
    ("tgt_in", "tgt_n0", "tgt_n1", 100.0),
    ("tgt_road", "tgt_n1", "tgt_n2", 300.0),
    ("tgt_out", "tgt_n2", "tgt_n3", 100.0),
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sumo_binary() -> str:
    binary = shutil.which("sumo")
    if binary is None:
        raise FormalArtifactError("SUMO executable not found on PATH")
    return binary


def _netconvert_binary() -> str:
    sumo_path = Path(_sumo_binary())
    candidate = sumo_path.with_name("netconvert.exe")
    if candidate.is_file():
        return str(candidate)
    binary = shutil.which("netconvert")
    if binary is None:
        raise FormalArtifactError("netconvert executable not found beside SUMO or on PATH")
    return binary


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sumo_environment() -> dict[str, str]:
    executable = Path(_sumo_binary()).resolve()
    process = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode != 0:
        raise FormalArtifactError(f"SUMO version query failed: {process.stderr.strip()}")
    first_line = next((line.strip() for line in process.stdout.splitlines() if line.strip()), "")
    if not first_line:
        raise FormalArtifactError("SUMO version query returned no version text")
    return {
        "version": first_line,
        "executable": str(executable),
        "executable_sha256": _sha256_file(executable),
    }


def _ensure_traci_importable() -> None:
    """Add the tools directory belonging to the located SUMO installation."""

    executable = Path(_sumo_binary()).resolve()
    candidates = (executable.parent.parent / "tools", executable.parent / "tools")
    for tools_dir in candidates:
        if (tools_dir / "traci" / "__init__.py").is_file():
            value = str(tools_dir)
            if value not in sys.path:
                sys.path.insert(0, value)
            return
    raise FormalArtifactError(
        f"TraCI tools directory not found beside SUMO executable: {executable}"
    )


def _implementation_hashes(repo_root: Path) -> dict[str, str]:
    repo_root = Path(repo_root).resolve()
    code_root = Path(__file__).resolve().parents[2]
    files = (
        Path(__file__).resolve(),
        Path(__file__).with_name("formal_artifacts.py").resolve(),
        Path(__file__).with_name("formal_design.py").resolve(),
        code_root / "scripts" / "run_e00_sumo.py",
        code_root / "scripts" / "analyze_e00_sumo.py",
    )
    result: dict[str, str] = {}
    for path in files:
        if not path.is_file():
            raise FormalArtifactError(f"E00 implementation file is missing: {path}")
        try:
            label = path.relative_to(repo_root).as_posix()
        except ValueError:
            label = str(path)
        result[label] = _sha256_file(path)
    return result


def _write_network(work: Path) -> tuple[Path, Path, Path]:
    """Create a deterministic, physically disconnected two-corridor network."""

    nodes = [
        ("src_n0", 0, 0), ("src_n1", 100, 0), ("src_n2", 400, 0), ("src_n3", 500, 0),
        ("tgt_n0", 0, 50), ("tgt_n1", 100, 50), ("tgt_n2", 400, 50), ("tgt_n3", 500, 50),
    ]
    node_xml = "<nodes>\n" + "\n".join(
        f'  <node id="{node}" x="{x}" y="{y}" type="priority" />' for node, x, y in nodes
    ) + "\n</nodes>\n"
    edge_xml = "<edges>\n" + "\n".join(
        f'  <edge id="{edge}" from="{left}" to="{right}" priority="1" numLanes="1" speed="20" />'
        for edge, left, right, _ in NET_EDGES
    ) + "\n</edges>\n"
    node_file = work / "nodes.nod.xml"
    edge_file = work / "edges.edg.xml"
    net_file = work / "dual_corridor.net.xml"
    node_file.write_text(node_xml, encoding="utf-8", newline="\n")
    edge_file.write_text(edge_xml, encoding="utf-8", newline="\n")
    result = subprocess.run(
        [_netconvert_binary(), "-n", str(node_file), "-e", str(edge_file), "-o", str(net_file)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise FormalArtifactError(f"netconvert failed: {result.stderr.strip()}")
    return node_file, edge_file, net_file


def _write_routes(work: Path, *, seed: int) -> tuple[Path, Path]:
    route_file = work / "routes.rou.xml"
    # Vehicles are placed on separate disconnected routes.  The target leader
    # starts ahead of the receiver so SUMO supplies a valid leader relation.
    route_xml = f'''<routes>
  <vType id="passenger" accel="2.0" decel="4.5" sigma="0" length="5" minGap="2" maxSpeed="20"/>
  <route id="src_route" edges="src_in src_road src_out"/>
  <route id="tgt_route" edges="tgt_in tgt_road tgt_out"/>
  <vehicle id="source_0" type="passenger" route="src_route" depart="0" departLane="0" departPos="20" departSpeed="10"/>
  <vehicle id="target_leader" type="passenger" route="tgt_route" depart="0" departLane="0" departPos="75" departSpeed="10"/>
  <vehicle id="target_0" type="passenger" route="tgt_route" depart="0" departLane="0" departPos="35" departSpeed="10"/>
</routes>
'''
    route_file.write_text(route_xml, encoding="utf-8", newline="\n")
    cfg_file = work / "simulation.sumocfg"
    cfg_file.write_text(
        f'''<configuration>
  <input><net-file value="{work / "dual_corridor.net.xml"}"/><route-files value="{route_file}"/></input>
  <time><begin value="0"/><end value="32"/><step-length value="0.2"/></time>
  <seed value="{int(seed)}"/>
</configuration>
''', encoding="utf-8", newline="\n",
    )
    return route_file, cfg_file


def _topology_payload() -> dict[str, Any]:
    nodes = {node for _, left, right, _ in NET_EDGES for node in (left, right)}
    return {
        "schema_version": "e00.topology.v1",
        "nodes": sorted(nodes),
        "directed_edges": [
            {"edge_id": edge, "from_node": left, "to_node": right, "length_m": length}
            for edge, left, right, length in NET_EDGES
        ],
        "source_edge": "src_road",
        "target_edge": "tgt_road",
    }


def _run_cell(
    *, work: Path, run_dir: Path, cell_id: str, seed: int, repo_root: Path, command: list[str]
) -> dict[str, Any]:
    _ensure_traci_importable()
    import traci

    source_present = cell_id[1] == "1"
    channel_enabled = cell_id[3] == "1"
    # The cell directory name is not a run identifier: retain a unique ID for
    # each independently started cell while keeping the package ID as prefix.
    run_id = f"{run_dir.parent.name}_{cell_id}"
    process_command = [_sumo_binary(), "-c", str(work / "simulation.sumocfg"), "--seed", str(seed), "--no-step-log", "true"]
    started_at = _utc_now()
    traci.start(process_command, label=run_id)
    state_rows: list[dict[str, Any]] = []
    emission_rows: list[dict[str, Any]] = []
    protocol_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    risk_rows: list[dict[str, Any]] = []
    time_rows: list[dict[str, Any]] = []
    lifecycle_rows: list[dict[str, Any]] = []
    generated_time: float | None = None
    adopted_time: float | None = None
    active_vehicle_ids: set[str] = set()
    try:
        for sequence in range(160):
            next_time = round(float(traci.simulation.getTime()) + 0.2, 10)
            ids_before_step = set(traci.vehicle.getIDList())
            source_command = 0.0
            target_command = 0.0
            if source_present and 2.0 <= next_time < 3.0 and "source_0" in ids_before_step:
                source_command = -3.0
                traci.vehicle.setAcceleration("source_0", source_command, 0.2)
            if source_present and generated_time is None and next_time >= 2.0:
                generated_time = 2.0
            if source_present and channel_enabled and adopted_time is None and next_time >= 2.2:
                adopted_time = 2.2
            if adopted_time is not None and adopted_time <= next_time < adopted_time + 2.0 and "target_0" in ids_before_step:
                target_command = -1.5
                traci.vehicle.setAcceleration("target_0", target_command, 0.2)
            traci.simulationStep()
            now = float(traci.simulation.getTime())
            simulation_step = int(round(now / 0.2))
            ids = sorted(traci.vehicle.getIDList())
            current_ids = set(ids)
            for vehicle_id in sorted(current_ids - active_vehicle_ids):
                lifecycle_rows.append({"run_id": run_id, "vehicle_id": vehicle_id, "incarnation_id": f"{run_id}:{vehicle_id}:0", "event_type": "enter", "time_s": now, "event_sequence": sequence * 3})
            for vehicle_id in sorted(active_vehicle_ids - current_ids):
                lifecycle_rows.append({"run_id": run_id, "vehicle_id": vehicle_id, "incarnation_id": f"{run_id}:{vehicle_id}:0", "event_type": "exit", "time_s": now, "event_sequence": sequence * 3})
            for vehicle_id in ids:
                lane_id = traci.vehicle.getLaneID(vehicle_id)
                edge_id = traci.vehicle.getRoadID(vehicle_id)
                x, y = traci.vehicle.getPosition(vehicle_id)
                speed = float(traci.vehicle.getSpeed(vehicle_id))
                accel = float(traci.vehicle.getAcceleration(vehicle_id))
                leader = traci.vehicle.getLeader(vehicle_id, 200.0)
                leader_id = leader[0] if leader else None
                gap = float(leader[1]) if leader else None
                rel = None
                if leader_id:
                    rel = float(traci.vehicle.getSpeed(leader_id) - speed)
                row = {
                    "run_id": run_id, "experiment_id": "E00", "scenario_id": "dual_corridor_sumo_minimal",
                    "cell_id": cell_id, "configured_seed": seed, "simulation_seed": seed,
                    "time_s": now, "vehicle_id": vehicle_id, "edge_id": edge_id, "lane_id": lane_id,
                    "x_m": float(x), "y_m": float(y), "speed_mps": speed, "acceleration_mps2": accel,
                    "leader_id": leader_id, "net_gap_m": gap, "relative_speed_mps": rel,
                }
                state_rows.append(row)
                emission_rows.append({key: row.get(key) for key in TABLE_REQUIRED_COLUMNS["emission.parquet"]})
                if vehicle_id == "target_0":
                    action_rows.append({
                        "run_id": run_id, "cell_id": cell_id, "target_vehicle_id": vehicle_id,
                        "time_s": now, "command_acceleration_mps2": target_command,
                        "applied_acceleration_mps2": accel, "safety_intervened": False,
                        "action_diverged": bool(adopted_time is not None and now >= adopted_time),
                        "paired_reference_cell_id": "s0c0",
                    })
                if vehicle_id == "target_0":
                    ttc = (gap / rel) if gap is not None and rel is not None and rel > 0 else float("inf")
                    risk_rows.append({
                        "run_id": run_id, "cell_id": cell_id, "target_vehicle_id": vehicle_id,
                        "window_id": "e00_validation_window", "window_start_s": 0.0, "window_end_s": 32.0,
                        "metric": "ttc_burden_validation", "value": max(2.0 - ttc, 0.0) if ttc != float("inf") else 0.0,
                        "tau_p_lower_s": float("inf"), "attributable": False,
                        "inclusion_status": "e00_validation", "inclusion_reason": "not_calibrated_for_science",
                    })
            for stream in ("state", "emission"):
                if ids:
                    time_rows.append({"run_id": run_id, "stream_name": stream, "sequence_index": sequence, "simulation_step": simulation_step, "time_s": now})
            if "target_0" in current_ids:
                time_rows.append({"run_id": run_id, "stream_name": "action", "sequence_index": sequence, "simulation_step": simulation_step, "time_s": now})
            for vehicle_id in ids:
                lifecycle_rows.append({"run_id": run_id, "vehicle_id": vehicle_id, "incarnation_id": f"{run_id}:{vehicle_id}:0", "event_type": "active", "time_s": now, "event_sequence": sequence * 3 + 1})
            active_vehicle_ids = current_ids
        if source_present:
            protocol_rows.append({
                "run_id": run_id, "cell_id": cell_id, "message_id": f"{run_id}:message:0", "source_event_id": f"{run_id}:event:0",
                "source_vehicle_id": "source_0", "target_vehicle_id": "target_0", "generated_time_s": generated_time,
                "sent_time_s": generated_time if channel_enabled else None, "delivered_time_s": adopted_time if channel_enabled else None,
                "validation_time_s": adopted_time if channel_enabled else None, "adopted_time_s": adopted_time if channel_enabled else None,
                "message_age_s": 0.2 if channel_enabled and adopted_time is not None and generated_time is not None else None,
                "message_generated": generated_time is not None, "message_sent": channel_enabled and generated_time is not None,
                "message_dropped": not channel_enabled, "message_delivered": channel_enabled and adopted_time is not None,
                "source_valid": True, "target_valid": True, "freshness_valid": channel_enabled,
                "adopted": channel_enabled and adopted_time is not None, "rejection_reason": None if channel_enabled else "channel_closed",
                "payload_type": "braking_pulse", "payload_risk": "validation_only",
                "message_kind": "source",
            })
        elif channel_enabled:
            # Equal-load sham: exercise the open channel and all transport
            # stages without a source event or an adoptable risk payload.
            sham_time = 2.0
            protocol_rows.append({
                "run_id": run_id, "cell_id": cell_id, "message_id": f"{run_id}:sham:0", "source_event_id": None,
                "source_vehicle_id": None, "target_vehicle_id": "target_0", "generated_time_s": sham_time,
                "sent_time_s": sham_time, "delivered_time_s": sham_time + 0.2, "validation_time_s": sham_time + 0.2,
                "adopted_time_s": None, "message_age_s": None, "message_generated": True, "message_sent": True,
                "message_dropped": False, "message_delivered": True, "source_valid": False, "target_valid": True,
                "freshness_valid": False, "adopted": False, "rejection_reason": "sham_no_source_event",
                "payload_type": "sham", "payload_risk": "none", "message_kind": "sham",
            })
        else:
            protocol_rows.append({
                "run_id": run_id, "cell_id": cell_id, "message_id": f"{run_id}:message:none", "source_event_id": None,
                "source_vehicle_id": None, "target_vehicle_id": "target_0", "generated_time_s": None, "sent_time_s": None,
                "delivered_time_s": None, "validation_time_s": None, "adopted_time_s": None, "message_age_s": None,
                "message_generated": False, "message_sent": False, "message_dropped": False, "message_delivered": False,
                "source_valid": False, "target_valid": True, "freshness_valid": False, "adopted": False,
                "rejection_reason": "source_absent", "payload_type": "sham", "payload_risk": "none",
                "message_kind": "none",
            })
    finally:
        traci.close()
    for vehicle_id in sorted(active_vehicle_ids):
        lifecycle_rows.append({"run_id": run_id, "vehicle_id": vehicle_id, "incarnation_id": f"{run_id}:{vehicle_id}:0", "event_type": "exit", "time_s": 32.0, "event_sequence": 480})
    for protocol_row in protocol_rows:
        protocol_times = [
            protocol_row.get(column)
            for column in ("generated_time_s", "sent_time_s", "delivered_time_s", "validation_time_s", "adopted_time_s")
            if protocol_row.get(column) is not None
        ]
        for sequence, time_s in enumerate(protocol_times):
            time_rows.append({"run_id": run_id, "stream_name": "protocol", "sequence_index": sequence, "simulation_step": int(round(float(time_s) / 0.2)), "time_s": float(time_s)})
    tables = {
        "state.parquet": pd.DataFrame(state_rows, columns=TABLE_REQUIRED_COLUMNS["state.parquet"]),
        "emission.parquet": pd.DataFrame(emission_rows, columns=TABLE_REQUIRED_COLUMNS["emission.parquet"]),
        "protocol.parquet": pd.DataFrame(protocol_rows, columns=TABLE_REQUIRED_COLUMNS["protocol.parquet"]),
        "action.parquet": pd.DataFrame(action_rows, columns=TABLE_REQUIRED_COLUMNS["action.parquet"]),
        "risk.parquet": pd.DataFrame(risk_rows, columns=TABLE_REQUIRED_COLUMNS["risk.parquet"]),
    }
    for name, table in tables.items():
        table.to_parquet(run_dir / name, index=False)
    _write_json(run_dir / "topology.json", _topology_payload())
    pd.DataFrame(time_rows).to_parquet(run_dir / "clock.parquet", index=False)
    pd.DataFrame(lifecycle_rows).to_parquet(run_dir / "vehicle_lifecycle.parquet", index=False)
    config = {
        "schema_version": "e00.sumo.v1", "experiment_id": "E00", "theory_version": "nc-prereg-v1.0",
        "protocol_version": "e00.sumo-minimal.v1", "scenario_id": "dual_corridor_sumo_minimal", "pair_id": run_dir.parent.name,
        "configured_seed": seed, "simulation_seed": seed, "source_vehicle_id": "source_0", "target_vehicle_id": "target_0",
        "window_start_s": 0.0, "window_end_s": 32.0, "time_step_s": 0.2, "source_event_time_s": 2.0, "run_id": run_id, "cell_id": cell_id,
        "source_present": source_present, "channel_enabled": channel_enabled, "output_dir": str(run_dir),
        "fixture_only": False, "smoke_only": False, "scientific_claim_eligible": False,
    }
    _write_json(run_dir / "config_frozen.json", config)
    protocol_audit = validate_protocol_lifecycle(tables["protocol.parquet"], source_present=source_present, channel_enabled=channel_enabled)
    path_audit = analyze_physical_path_from_archived_tables(
        tables["state.parquet"],
        _topology_payload(),
        source_vehicle_id="source_0",
        target_vehicle_id="target_0",
        source_start_time_s=2.0,
    )
    audit = {
        "schema_version": "e00.audit.v1", "experiment_id": "E00", "run_id": run_id,
        "scientific_claim_eligible": False, "theory_schema_pass": True, "protocol_audit": protocol_audit,
        "physical_path_audit": path_audit,
        "note": "Real SUMO E00 infrastructure run; validation only, not a scientific effect result.",
    }
    _write_json(run_dir / "audit.json", audit)
    finished_at = _utc_now()
    provenance = collect_run_provenance(
        repo_root,
        command=command,
        started_at_utc=started_at,
        finished_at_utc=finished_at,
        exit_code=0,
    )
    provenance["sumo"] = _sumo_environment()
    provenance["implementation_sha256"] = _implementation_hashes(repo_root)
    _write_json(run_dir / "provenance.json", provenance)
    (run_dir / "run.log").write_text(f"run_kind=e00_real_sumo\ncell_id={cell_id}\nscientific_claim_eligible=false\nexit_code=0\n", encoding="utf-8", newline="\n")
    rows = validate_theory_artifact_schema(run_dir)
    build_run_manifest(run_dir, metadata={"experiment_id": "E00", "protocol_version": "e00.sumo-minimal.v1", "run_id": run_id, "cell_id": cell_id, "scientific_claim_eligible": False, "row_counts": rows})
    validate_run_manifest(run_dir)
    return {"config": config, "state": tables["state.parquet"], "action": tables["action.parquet"], "protocol": tables["protocol.parquet"], "risk": tables["risk.parquet"], "time": pd.DataFrame(time_rows), "lifecycle": pd.DataFrame(lifecycle_rows)}


def run_real_sumo_e00(output_root: Path, *, run_id: str, seed: int, repo_root: Path, command: list[str]) -> Path:
    """Run one deterministic four-cell E00 package against real SUMO."""

    output_root = Path(output_root).resolve()
    package = output_root / run_id
    if package.exists():
        raise FormalArtifactError(f"Refusing to overwrite an existing E00 package: {package}")
    package.mkdir(parents=True)
    configs: dict[str, dict[str, Any]] = {}
    states: list[pd.DataFrame] = []
    actions: list[pd.DataFrame] = []
    times: list[pd.DataFrame] = []
    lifecycles: list[pd.DataFrame] = []
    protocols: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="aad_e00_sumo_") as temp:
        work = Path(temp)
        _write_network(work)
        _write_routes(work, seed=seed)
        for cell_id in SUMO_CELLS:
            cell_dir = package / cell_id
            cell_dir.mkdir()
            result = _run_cell(work=work, run_dir=cell_dir, cell_id=cell_id, seed=seed, repo_root=repo_root, command=command)
            configs[cell_id] = result["config"]
            states.append(result["state"])
            actions.append(result["action"])
            times.append(result["time"])
            lifecycles.append(result["lifecycle"])
            protocols[cell_id] = validate_protocol_lifecycle(pd.read_parquet(cell_dir / "protocol.parquet"), source_present=cell_id[1] == "1", channel_enabled=cell_id[3] == "1")
    state = pd.concat(states, ignore_index=True)
    action = pd.concat(actions, ignore_index=True)
    target_state = state[state["vehicle_id"] == "target_0"]
    pre = validate_pre_treatment_equivalence(target_state, treatment_start_s=2.0, key_columns=("time_s", "vehicle_id"), exact_columns=("edge_id", "lane_id", "leader_id"), numeric_tolerances={"x_m": 1e-6, "y_m": 1e-6, "speed_mps": 1e-6, "acceleration_mps2": 1e-6})
    isolation = validate_run_state_isolation(pd.DataFrame([{"run_id": configs[cell]["run_id"], "state_instance_id": f"state_{cell}", "cache_namespace": f"cache_{cell}", "rng_stream_id": f"rng_{cell}", "initial_cache_entries": 0, "initial_pending_messages": 0} for cell in SUMO_CELLS]))
    time_audit = validate_simulation_time_alignment(pd.concat(times, ignore_index=True), time_step_s=0.2, time_origin_s=0.0)
    lifecycle = validate_vehicle_id_lifecycle(pd.concat(lifecycles, ignore_index=True))
    topology = _topology_payload()
    path = analyze_physical_path_from_archived_tables(
        state,
        topology,
        source_vehicle_id="source_0",
        target_vehicle_id="target_0",
    )
    report = {"schema_version": "e00.sumo-report.v1", "experiment_id": "E00", "run_id": run_id, "scientific_claim_eligible": False, "four_cell_audit": validate_four_cell_configs(configs), "pre_treatment_audit": pre, "state_isolation_audit": isolation, "time_alignment_audit": time_audit, "vehicle_lifecycle_audit": lifecycle, "protocol_audits": protocols, "physical_path_audit": path, "note": "Real SUMO four-cell package for E00 infrastructure validation only."}
    _write_json(package / "e00_report.json", report)
    return package


def analyze_real_sumo_e00(package: Path) -> dict[str, Any]:
    """Recompute E00 audit facts only from sealed files, never runner state."""

    package = Path(package).resolve()
    configs: dict[str, dict[str, Any]] = {}
    states: list[pd.DataFrame] = []
    cell_summaries: dict[str, dict[str, Any]] = {}
    protocol_summary: dict[str, dict[str, Any]] = {}
    clocks: list[pd.DataFrame] = []
    lifecycles: list[pd.DataFrame] = []
    topologies: dict[str, dict[str, Any]] = {}
    for cell in SUMO_CELLS:
        cell_dir = package / cell
        validate_run_manifest(cell_dir)
        validate_theory_artifact_schema(cell_dir)
        configs[cell] = json.loads((cell_dir / "config_frozen.json").read_text(encoding="utf-8"))
        tables = {name: pd.read_parquet(cell_dir / name) for name in TABLE_REQUIRED_COLUMNS}
        states.append(tables["state.parquet"])
        clocks.append(pd.read_parquet(cell_dir / "clock.parquet"))
        lifecycles.append(pd.read_parquet(cell_dir / "vehicle_lifecycle.parquet"))
        topologies[cell] = json.loads((cell_dir / "topology.json").read_text(encoding="utf-8"))
        protocol_summary[cell] = validate_protocol_lifecycle(
            tables["protocol.parquet"],
            source_present=bool(configs[cell]["source_present"]),
            channel_enabled=bool(configs[cell]["channel_enabled"]),
        )
        cell_summaries[cell] = {
            "row_counts": {name: int(len(table)) for name, table in tables.items()},
            "vehicle_count": int(tables["state.parquet"]["vehicle_id"].nunique()),
            "action_diverged_count": int(tables["action.parquet"]["action_diverged"].fillna(False).astype(bool).sum()),
            "risk_record_count": int(len(tables["risk.parquet"])),
            "risk_inclusion_statuses": sorted(tables["risk.parquet"]["inclusion_status"].dropna().astype(str).unique()),
        }
    target = pd.concat(states, ignore_index=True)
    target_vehicle = target[target["vehicle_id"].astype(str) == "target_0"].copy()
    canonical_topologies = {
        json.dumps(topology, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for topology in topologies.values()
    }
    if len(canonical_topologies) != 1:
        raise FormalArtifactError("Four-cell archived topologies differ")
    topology = topologies["s0c0"]
    pre = validate_pre_treatment_equivalence(
        target_vehicle,
        treatment_start_s=float(configs["s0c0"]["source_event_time_s"]),
        key_columns=("time_s", "vehicle_id"),
        exact_columns=("edge_id", "lane_id", "leader_id"),
        numeric_tolerances={"x_m": 1e-6, "y_m": 1e-6, "speed_mps": 1e-6, "acceleration_mps2": 1e-6},
    )
    path = analyze_physical_path_from_archived_tables(
        states[SUMO_CELLS.index("s1c1")],
        topology,
        source_vehicle_id="source_0",
        target_vehicle_id="target_0",
        source_start_time_s=float(configs["s1c1"]["source_event_time_s"]),
    )
    time_audit = validate_simulation_time_alignment(
        pd.concat(clocks, ignore_index=True), time_step_s=0.2, time_origin_s=0.0
    )
    lifecycle_audit = validate_vehicle_id_lifecycle(
        pd.concat(lifecycles, ignore_index=True)
    )
    return {
        "four_cell_audit": validate_four_cell_configs(configs),
        "target_rows": int(len(target[target["vehicle_id"] == "target_0"])),
        "cell_summaries": cell_summaries,
        "protocol_summary": protocol_summary,
        "pre_treatment_audit": pre,
        "physical_path_audit": path,
        "time_alignment_audit": time_audit,
        "vehicle_lifecycle_audit": lifecycle_audit,
        "clock_record_count": int(sum(len(clock) for clock in clocks)),
        "lifecycle_record_count": int(sum(len(lifecycle) for lifecycle in lifecycles)),
    }


def analyze_physical_path_from_archived_tables(
    state: pd.DataFrame,
    topology: dict[str, Any],
    *,
    source_vehicle_id: str,
    target_vehicle_id: str,
    source_start_time_s: float | None = None,
) -> dict[str, Any]:
    """Audit physical reachability using only archived state and topology."""

    required_state = {"time_s", "vehicle_id", "edge_id", "leader_id"}
    missing = sorted(required_state - set(state.columns))
    if missing:
        raise FormalArtifactError(f"Archived state is missing path fields: {', '.join(missing)}")
    edges = topology.get("directed_edges")
    if not isinstance(edges, list):
        raise FormalArtifactError("Archived topology must contain directed_edges")
    adjacency: dict[str, set[str]] = {}
    edge_nodes: dict[str, tuple[str, str]] = {}
    for edge in edges:
        try:
            edge_id, left, right = str(edge["edge_id"]), str(edge["from_node"]), str(edge["to_node"])
        except (KeyError, TypeError) as exc:
            raise FormalArtifactError("Archived topology contains an invalid edge") from exc
        edge_nodes[edge_id] = (left, right)
        adjacency.setdefault(left, set()).add(right)
    source_edge = str(topology.get("source_edge", ""))
    target_edge = str(topology.get("target_edge", ""))
    # Small mutation-test topologies may omit labels; infer them from the
    # archived state only when each endpoint is unambiguous.
    if not source_edge or not target_edge:
        source_observed = state.loc[state["vehicle_id"].astype(str) == source_vehicle_id, "edge_id"].dropna().astype(str)
        target_observed = state.loc[state["vehicle_id"].astype(str) == target_vehicle_id, "edge_id"].dropna().astype(str)
        if not source_edge and not source_observed.empty:
            source_edge = str(source_observed.iloc[0])
        if not target_edge and not target_observed.empty:
            target_edge = str(target_observed.iloc[0])
    if source_edge not in edge_nodes or target_edge not in edge_nodes:
        raise FormalArtifactError("Archived topology lacks source_edge or target_edge")
    queue = [edge_nodes[source_edge][1]]
    seen = set(queue)
    while queue:
        node = queue.pop(0)
        for nxt in adjacency.get(node, set()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    topology_reachable = edge_nodes[target_edge][0] in seen or source_edge == target_edge
    if not topology_reachable:
        return {"topology_reachable": False, "reachable": False, "tau_p": None, "status": "disconnected_topology"}

    normalized = state.copy()
    normalized["time_s"] = pd.to_numeric(normalized["time_s"], errors="coerce")
    if normalized["time_s"].isna().any():
        raise FormalArtifactError("Archived state contains a non-numeric path time")
    source = normalized[normalized["vehicle_id"].astype(str) == source_vehicle_id].sort_values("time_s")
    target = normalized[normalized["vehicle_id"].astype(str) == target_vehicle_id].sort_values("time_s")
    if source.empty or target.empty:
        return {"topology_reachable": True, "reachable": False, "tau_p": None, "status": "uncertain_missing_vehicle"}

    def transition_allowed(previous_edge: str, current_edge: str) -> bool:
        if previous_edge == current_edge:
            return True
        return (
            previous_edge in edge_nodes
            and current_edge in edge_nodes
            and edge_nodes[previous_edge][1] == edge_nodes[current_edge][0]
        )

    rows_by_node: dict[tuple[str, float], dict[str, Any]] = {}
    for row in normalized.to_dict("records"):
        node = (str(row["vehicle_id"]), float(row["time_s"]))
        if node in rows_by_node:
            raise FormalArtifactError(f"Archived state has duplicate vehicle-time rows: {node[0]} at {node[1]}")
        rows_by_node[node] = row
    graph: dict[tuple[str, float], set[tuple[str, float]]] = {node: set() for node in rows_by_node}
    for vehicle_id, vehicle in normalized.groupby(normalized["vehicle_id"].astype(str), sort=False):
        ordered = vehicle.sort_values("time_s")
        nodes = [(str(vehicle_id), float(time_s)) for time_s in ordered["time_s"]]
        for previous, current in zip(nodes, nodes[1:]):
            previous_edge = str(rows_by_node[previous]["edge_id"])
            current_edge = str(rows_by_node[current]["edge_id"])
            if transition_allowed(previous_edge, current_edge):
                graph[previous].add(current)
    for follower_node, row in rows_by_node.items():
        leader_id = row.get("leader_id")
        if leader_id is None or pd.isna(leader_id) or not str(leader_id).strip():
            continue
        leader_node = (str(leader_id), follower_node[1])
        if leader_node not in rows_by_node:
            continue
        leader_edge = str(rows_by_node[leader_node]["edge_id"])
        follower_edge = str(row["edge_id"])
        if transition_allowed(follower_edge, leader_edge) or transition_allowed(leader_edge, follower_edge):
            graph[leader_node].add(follower_node)
    start_time = float(source_start_time_s) if source_start_time_s is not None else float(source["time_s"].min())
    starts = sorted(
        (node for node in graph if node[0] == source_vehicle_id and node[1] >= start_time),
        key=lambda node: node[1],
    )
    if not starts:
        return {"topology_reachable": True, "reachable": False, "tau_p": None, "status": "right_censored"}
    start = starts[0]
    queue_nodes = [start]
    visited = {start}
    target_arrivals: list[float] = []
    while queue_nodes:
        node = queue_nodes.pop(0)
        if node[0] == target_vehicle_id:
            target_arrivals.append(node[1])
        for nxt in graph.get(node, set()):
            if nxt not in visited and nxt[1] >= node[1]:
                visited.add(nxt)
                queue_nodes.append(nxt)
    if target_arrivals:
        return {"topology_reachable": True, "reachable": True, "tau_p": min(target_arrivals), "status": "finite_arrival"}
    return {"topology_reachable": True, "reachable": False, "tau_p": None, "status": "right_censored"}
