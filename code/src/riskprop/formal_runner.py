"""Stage 0.1-only runner that verifies the formal artifact chain without science claims."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run_artifact_smoke(
    output_root: Path,
    *,
    run_id: str,
    repo_root: Path,
    command: list[str] | None = None,
) -> Path:
    """Create and seal an empty Stage 0.1 run to test provenance and schemas end to end."""

    if not run_id or any(character in run_id for character in "\\/:"):
        raise FormalArtifactError("run_id must be a non-empty portable path component")
    output_root = Path(output_root).resolve()
    run_dir = output_root / run_id
    if run_dir.exists():
        raise FormalArtifactError(f"Refusing to overwrite an existing run: {run_dir}")
    run_dir.mkdir(parents=True)
    started_at = _utc_now()
    if command is None:
        command = [
            "riskprop.formal_runner.run_artifact_smoke",
            "--output-root",
            str(output_root),
            "--run-id",
            run_id,
            "--repo-root",
            str(Path(repo_root).resolve()),
        ]

    config = {
        "schema_version": "stage_0_1.config.v1",
        "experiment_id": "stage_0_1",
        "protocol_version": "stage_0_1.artifact-smoke.v1",
        "run_id": run_id,
        "run_kind": "artifact_smoke",
        "smoke_only": True,
        "scientific_claim_eligible": False,
        "source_present": False,
        "channel_enabled": False,
    }
    _write_json(run_dir / "config_frozen.json", config)
    for name, columns in TABLE_REQUIRED_COLUMNS.items():
        pd.DataFrame(columns=columns).to_parquet(run_dir / name, index=False)
    audit = {
        "schema_version": "stage_0_1.audit.v1",
        "experiment_id": "stage_0_1",
        "run_id": run_id,
        "smoke_only": True,
        "scientific_claim_eligible": False,
        "theory_schema_pass": True,
        "note": "Infrastructure smoke only; no traffic or causal effect was simulated.",
    }
    _write_json(run_dir / "audit.json", audit)
    finished_at = _utc_now()
    provenance = collect_run_provenance(
        Path(repo_root),
        command=command,
        started_at_utc=started_at,
        finished_at_utc=finished_at,
        exit_code=0,
    )
    _write_json(run_dir / "provenance.json", provenance)
    (run_dir / "run.log").write_text(
        "\n".join(
            [
                f"started_at_utc={started_at}",
                f"finished_at_utc={finished_at}",
                "run_kind=artifact_smoke",
                "scientific_claim_eligible=false",
                "exit_code=0",
            ]
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    row_counts = validate_theory_artifact_schema(run_dir)
    build_run_manifest(
        run_dir,
        metadata={
            "experiment_id": "stage_0_1",
            "protocol_version": "stage_0_1.artifact-smoke.v1",
            "run_id": run_id,
            "smoke_only": True,
            "scientific_claim_eligible": False,
            "row_counts": row_counts,
        },
    )
    validate_run_manifest(run_dir)
    return run_dir


def _fixture_protocol_row(
    cell_id: str,
    *,
    run_id: str,
    source_present: bool,
    channel_enabled: bool,
) -> dict[str, object]:
    adopted = source_present and channel_enabled
    generated = source_present
    sent = adopted
    delivered = adopted
    return {
        "run_id": run_id,
        "cell_id": cell_id,
        "message_id": f"fixture_message_{cell_id}",
        "source_event_id": "fixture_source_event" if generated else None,
        "source_vehicle_id": "source_0" if source_present else None,
        "target_vehicle_id": "target_0",
        "generated_time_s": 1.5 if generated else None,
        "sent_time_s": 1.6 if sent else None,
        "delivered_time_s": 1.7 if delivered else None,
        "validation_time_s": 1.7 if delivered else None,
        "adopted_time_s": 1.8 if adopted else None,
        "message_age_s": 0.3 if adopted else None,
        "message_generated": generated,
        "message_sent": sent,
        "message_dropped": generated and not sent,
        "message_delivered": delivered,
        "source_valid": source_present,
        "target_valid": True,
        "freshness_valid": adopted,
        "adopted": adopted,
        "rejection_reason": None
        if adopted
        else ("source_absent" if not source_present else "channel_closed"),
        "payload_type": "fixture_only" if adopted else None,
        "payload_risk": "fixture_only" if adopted else None,
        "message_kind": "source" if source_present else "none",
    }


def run_contract_fixture(
    output_root: Path,
    *,
    fixture_id: str,
    repo_root: Path,
    command: list[str] | None = None,
) -> Path:
    """Create a deterministic non-empty four-cell contract fixture, never science."""

    if not fixture_id or any(character in fixture_id for character in "\\/:"):
        raise FormalArtifactError("fixture_id must be a non-empty portable path component")
    output_root = Path(output_root).resolve()
    fixture_dir = output_root / fixture_id
    if fixture_dir.exists():
        raise FormalArtifactError(f"Refusing to overwrite an existing fixture: {fixture_dir}")
    fixture_dir.mkdir(parents=True)
    if command is None:
        command = ["riskprop.formal_runner.run_contract_fixture", fixture_id]
    configs: dict[str, dict[str, object]] = {}
    all_state: list[dict[str, object]] = []
    all_isolation: list[dict[str, object]] = []
    all_time: list[dict[str, object]] = []
    all_lifecycle: list[dict[str, object]] = []
    protocol_audits: dict[str, dict[str, object]] = {}

    for source_present in (False, True):
        for channel_enabled in (False, True):
            cell_id = f"s{int(source_present)}c{int(channel_enabled)}"
            run_id = f"{fixture_id}_{cell_id}"
            config = {
                "schema_version": "stage_0_1.four-cell.v1",
                "experiment_id": "stage_0_1",
                "theory_version": "nc-prereg-v1.0",
                "protocol_version": "stage_0_1.contract-fixture.v1",
                "scenario_id": "stage_0_1_contract_fixture",
                "pair_id": fixture_id,
                "configured_seed": 0,
                "simulation_seed": 0,
                "source_vehicle_id": "source_0",
                "target_vehicle_id": "target_0",
                "window_start_s": 0.0,
                "window_end_s": 2.0,
                "time_step_s": 0.1,
                "run_id": run_id,
                "cell_id": cell_id,
                "source_present": source_present,
                "channel_enabled": channel_enabled,
                "output_dir": str((fixture_dir / cell_id).relative_to(Path(repo_root).resolve()))
                if (fixture_dir / cell_id).is_relative_to(Path(repo_root).resolve())
                else str(fixture_dir / cell_id),
                "fixture_only": True,
                "scientific_claim_eligible": False,
            }
            configs[cell_id] = config
            run_dir = fixture_dir / cell_id
            run_dir.mkdir()
            _write_json(run_dir / "config_frozen.json", config)

            state_rows: list[dict[str, object]] = []
            for time_s, step in ((0.0, 0), (1.0, 10), (2.0, 20)):
                post_action_speed = 9.8 if cell_id == "s1c1" and time_s == 2.0 else 10.4
                state_rows.append(
                    {
                        "run_id": run_id,
                        "experiment_id": "stage_0_1",
                        "scenario_id": "stage_0_1_contract_fixture",
                        "cell_id": cell_id,
                        "configured_seed": 0,
                        "simulation_seed": 0,
                        "time_s": time_s,
                        "vehicle_id": "target_0",
                        "edge_id": "target_edge",
                        "lane_id": "target_lane",
                        "x_m": 100.0 + time_s * 10.0,
                        "y_m": 0.0,
                        "speed_mps": post_action_speed,
                        "acceleration_mps2": 0.0 if time_s < 2.0 else -1.0,
                        "leader_id": "leader_0",
                        "net_gap_m": 20.0,
                        "relative_speed_mps": 0.0,
                    }
                )
                all_state.append(state_rows[-1])
                all_time.append(
                    {
                        "run_id": run_id,
                        "stream_name": "state",
                        "sequence_index": step,
                        "simulation_step": step,
                        "time_s": time_s,
                    }
                )
            if source_present:
                for time_s, step in ((0.0, 0), (1.0, 10), (2.0, 20)):
                    state_rows.append(
                        {
                            "run_id": run_id,
                            "experiment_id": "stage_0_1",
                            "scenario_id": "stage_0_1_contract_fixture",
                            "cell_id": cell_id,
                            "configured_seed": 0,
                            "simulation_seed": 0,
                            "time_s": time_s,
                            "vehicle_id": "source_0",
                            "edge_id": "source_edge",
                            "lane_id": "source_lane",
                            "x_m": 50.0 + time_s * 10.0,
                            "y_m": 0.0,
                            "speed_mps": 10.0,
                            "acceleration_mps2": 0.0,
                            "leader_id": None,
                            "net_gap_m": None,
                            "relative_speed_mps": None,
                        }
                    )
            state = pd.DataFrame(state_rows, columns=TABLE_REQUIRED_COLUMNS["state.parquet"])
            emission = state[
                list(TABLE_REQUIRED_COLUMNS["emission.parquet"])
            ].copy()
            protocol_row = _fixture_protocol_row(
                cell_id,
                run_id=run_id,
                source_present=source_present,
                channel_enabled=channel_enabled,
            )
            protocol = pd.DataFrame(
                [protocol_row], columns=TABLE_REQUIRED_COLUMNS["protocol.parquet"]
            )
            protocol_audits[cell_id] = validate_protocol_lifecycle(
                protocol,
                source_present=source_present,
                channel_enabled=channel_enabled,
            )
            action = pd.DataFrame(
                [
                    {
                        "run_id": run_id,
                        "cell_id": cell_id,
                        "target_vehicle_id": "target_0",
                        "time_s": time_s,
                        "command_acceleration_mps2": 0.0 if time_s < 2.0 else (-1.0 if cell_id == "s1c1" else 0.0),
                        "applied_acceleration_mps2": 0.0 if time_s < 2.0 else (-1.0 if cell_id == "s1c1" else 0.0),
                        "safety_intervened": False,
                        "action_diverged": time_s >= 2.0 and cell_id == "s1c1",
                        "paired_reference_cell_id": "s0c0",
                    }
                    for time_s in (0.0, 1.0, 2.0)
                ],
                columns=TABLE_REQUIRED_COLUMNS["action.parquet"],
            )
            risk = pd.DataFrame(
                [
                    {
                        "run_id": run_id,
                        "cell_id": cell_id,
                        "target_vehicle_id": "target_0",
                        "window_id": "fixture_window",
                        "window_start_s": 1.0,
                        "window_end_s": 2.0,
                        "metric": "fixture_only_placeholder",
                        "value": 0.0,
                        "tau_p_lower_s": 0.0,
                        "attributable": False,
                        "inclusion_status": "fixture_only",
                        "inclusion_reason": "not_science",
                    }
                ],
                columns=TABLE_REQUIRED_COLUMNS["risk.parquet"],
            )
            for name, table in {
                "state.parquet": state,
                "emission.parquet": emission,
                "protocol.parquet": protocol,
                "action.parquet": action,
                "risk.parquet": risk,
            }.items():
                table.to_parquet(run_dir / name, index=False)
            _write_json(
                run_dir / "audit.json",
                {
                    "schema_version": "stage_0_1.audit.v1",
                    "experiment_id": "stage_0_1",
                    "run_id": run_id,
                    "fixture_only": True,
                    "scientific_claim_eligible": False,
                    "theory_schema_pass": True,
                    "note": "Deterministic contract fixture; no traffic or causal claim.",
                },
            )
            started_at = _utc_now()
            finished_at = _utc_now()
            _write_json(
                run_dir / "provenance.json",
                collect_run_provenance(
                    Path(repo_root),
                    command=command,
                    started_at_utc=started_at,
                    finished_at_utc=finished_at,
                    exit_code=0,
                ),
            )
            (run_dir / "run.log").write_text(
                "run_kind=contract_fixture\nscientific_claim_eligible=false\nexit_code=0\n",
                encoding="utf-8",
                newline="\n",
            )
            rows = validate_theory_artifact_schema(run_dir)
            build_run_manifest(
                run_dir,
                metadata={
                    "experiment_id": "stage_0_1",
                    "protocol_version": "stage_0_1.contract-fixture.v1",
                    "run_id": run_id,
                    "cell_id": cell_id,
                    "fixture_only": True,
                    "scientific_claim_eligible": False,
                    "row_counts": rows,
                },
            )
            validate_run_manifest(run_dir)
            all_isolation.append(
                {
                    "run_id": run_id,
                    "state_instance_id": f"state_{cell_id}",
                    "cache_namespace": f"cache_{cell_id}",
                    "rng_stream_id": f"rng_{cell_id}",
                    "initial_cache_entries": 0,
                    "initial_pending_messages": 0,
                }
            )
            all_time.extend(
                [
                    {
                        "run_id": run_id,
                        "stream_name": "action",
                        "sequence_index": step,
                        "simulation_step": step,
                        "time_s": time_s,
                    }
                    for step, time_s in ((0, 0.0), (10, 1.0), (20, 2.0))
                ]
            )
            all_time.append(
                {
                    "run_id": run_id,
                    "stream_name": "protocol",
                    "sequence_index": 15,
                    "simulation_step": 15,
                    "time_s": 1.5,
                }
            )
            for vehicle_id in (["target_0", "source_0"] if source_present else ["target_0"]):
                all_lifecycle.extend(
                    [
                        {
                            "run_id": run_id,
                            "vehicle_id": vehicle_id,
                            "incarnation_id": f"{run_id}:{vehicle_id}:0",
                            "event_type": event_type,
                            "time_s": time_s,
                            "event_sequence": sequence,
                        }
                        for sequence, (event_type, time_s) in enumerate(
                            (("enter", 0.0), ("active", 1.0), ("active", 2.0), ("exit", 3.0))
                        )
                    ]
                )

    four_cell_audit = validate_four_cell_configs(configs)
    target_state = pd.DataFrame(
        [row for row in all_state if row["vehicle_id"] == "target_0"]
    )
    pre_treatment_audit = validate_pre_treatment_equivalence(
        target_state,
        treatment_start_s=2.0,
        key_columns=("time_s", "vehicle_id"),
        exact_columns=("edge_id", "lane_id", "leader_id"),
        numeric_tolerances={
            "x_m": 1e-9,
            "speed_mps": 1e-9,
            "acceleration_mps2": 1e-9,
        },
    )
    state_isolation_audit = validate_run_state_isolation(pd.DataFrame(all_isolation))
    time_alignment_audit = validate_simulation_time_alignment(
        pd.DataFrame(all_time), time_step_s=0.1, time_origin_s=0.0
    )
    vehicle_lifecycle_audit = validate_vehicle_id_lifecycle(pd.DataFrame(all_lifecycle))
    _write_json(
        fixture_dir / "fixture_report.json",
        {
            "schema_version": "stage_0_1.fixture-report.v1",
            "experiment_id": "stage_0_1",
            "fixture_id": fixture_id,
            "fixture_only": True,
            "scientific_claim_eligible": False,
            "four_cell_audit": four_cell_audit,
            "pre_treatment_audit": pre_treatment_audit,
            "state_isolation_audit": state_isolation_audit,
            "time_alignment_audit": time_alignment_audit,
            "vehicle_lifecycle_audit": vehicle_lifecycle_audit,
            "protocol_audits": protocol_audits,
            "s1c1_protocol_audit": protocol_audits["s1c1"],
            "note": "Non-empty deterministic contract fixture; not a traffic or causal result.",
        },
    )
    return fixture_dir
