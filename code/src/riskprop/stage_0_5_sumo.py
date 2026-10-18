"""Stage 0.5 no-message SUMO baseline engineering skeleton.

This module is deliberately separate from :mod:`stage_0_1_sumo`.  It provides

* candidate scenario metadata for the three approved Stage 0.5 logical scenarios;
* an explicitly *generic* multi-edge highway fixture network (never US-101 geometry);
* a ``no_message_baseline`` TraCI runner with an explicit internal/recorded time split;
* one unified vehicle-state observation contract with a verified net-gap conversion;
* a SUMO-native engineering P2 adapter and a formal-alignment adapter that itemises
  which Stage 0.2 identity/time/continuity conditions SUMO can supply itself;
* a fail-closed, auditable calibration/validation access guard.

Nothing here calibrates, validates against reality, or unlocks Stage I.  Every
scientific parameter (network, demand, vType mapping, driver behaviour, time step,
warm-up/evaluation window, tolerances, gate criteria) remains either
``engineering_fixture_only`` or ``pending_scientific``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .formal_risk_measurement import (
    P2_FORMAL_CONFIG,
    continuity_is_valid,
    extract_formal_source_events,
    observed_confirmation_time,
)

RESULT_ID = "RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1"
SCHEMA_ROOT = "stage_0_5.sumo-engineering.v2"
FORMAL_RESULT_ID = "RES-STAGE-0.5-REAL-REF-R2"
FORMAL_OBSERVATION_STEP_S = 0.1
FORMAL_MAX_GAP_S = P2_FORMAL_CONFIG.max_gap_s
FORMAL_TTC_THRESHOLD_S = P2_FORMAL_CONFIG.ttc_threshold_s
FORMAL_MINIMUM_DURATION_S = P2_FORMAL_CONFIG.minimum_duration_s
FORMAL_ALGORITHM_VERSION = P2_FORMAL_CONFIG.algorithm_version

PARAMETER_CLASSES = (
    "engineering_fixture_only",
    "researcher_approved_scientific",
    "pending_scientific",
)

#: Stage 0.2 measurement status vocabulary; reused without modification.
MEASUREMENT_STATUS = ("valid", "not_applicable", "missing", "invalid")

#: NGSIM observation-quality reasons that cannot arise in a single-process
#: deterministic simulator.  They are never fabricated for SUMO output.
NGSIM_ONLY_MISSING_REASONS = (
    "diagnostic_clock_conflict",
    "camera_occlusion_or_dropout",
    "original_frame_identity_break",
    "original_row_ambiguity",
)

#: Verified net-gap semantics.  TraCI's ``vehicle.getLeader`` distance is the
#: follower's remaining gap *relative to its own minGap*, not the physical
#: bumper-to-bumper distance.  Verified empirically on 2026-10-18 with three
#: vType pairs and a stopped-equilibrium probe (see
#: ``NET_GAP_VERIFICATION`` and ``code/tests/test_stage_0_5_sumo.py``).
NET_GAP_SEMANTICS: dict[str, Any] = {
    "schema_version": f"{SCHEMA_ROOT}.net-gap-semantics.v1",
    "reference_point": "SUMO vehicle position on lane (front bumper along the lane)",
    "traci_call": "traci.vehicle.getLeader(vehicle_id, lookahead_m)",
    "traci_distance_definition": (
        "(leader_reference_position_m - leader_length_m - follower_reference_position_m)"
        " - follower_min_gap_m"
    ),
    "physical_net_gap_rule": "net_gap_m = leader_traci_distance_m + follower_min_gap_m",
    "physical_net_gap_definition": (
        "leader_reference_position_m - leader_length_m - follower_reference_position_m"
    ),
    "verified": True,
    "verification_scope": (
        "engineering fixture only: three vType pairs plus a stopped-equilibrium probe;"
        " no reality claim"
    ),
    "not_equivalent_to": "Stage 0.1 relative_speed_mps = leader_speed - follower_speed",
}

#: Unified kinematic/following sign convention for Stage 0.5.
CLOSING_SPEED_SEMANTICS: dict[str, Any] = {
    "schema_version": f"{SCHEMA_ROOT}.closing-speed-semantics.v1",
    "definition": "closing_speed_mps = follower_speed_mps - leader_speed_mps",
    "positive": "follower is closing on the leader",
    "zero": "zero longitudinal relative speed",
    "negative": "leader is pulling away from the follower",
    "ttc_rule": "ttc_s = net_gap_m / closing_speed_mps when net_gap_m > 0 and closing_speed_mps > 0",
    "stage_0_1_conflict": (
        "Stage 0.1 validation risk used relative_speed_mps = leader_speed - follower_speed,"
        " the opposite sign; Stage 0.5 states must not reuse that interpretation"
    ),
}

UNITS: dict[str, str] = {
    "time_s": "s",
    "simulation_step": "1",
    "speed_mps": "m/s",
    "acceleration_mps2": "m/s^2",
    "x_m": "m",
    "y_m": "m",
    "longitudinal_position_m": "m",
    "net_gap_m": "m",
    "leader_traci_distance_m": "m",
    "closing_speed_mps": "m/s",
    "ttc_s": "s",
    "p2_event_count": "1",
    "p2_evaluable_following_exposure_s": "s",
    "p2_event_rate_per_vehicle_hour": "1/h",
}

#: Naming contract for reader-facing assets of the engineering package.
SCENARIO_MANIFEST: dict[str, dict[str, Any]] = {
    "us101_highway_baseline": {
        "scenario_id": "us101_highway_baseline",
        "role": "highway_following_risk_primary",
        "reference_source": {
            "result_id": FORMAL_RESULT_ID,
            "version": "R2",
            "groups": ["us101__0750_0805", "us101__0805_0820", "us101__0820_0835"],
            "role": "highway_following_risk",
        },
        "network_config_version": "generic_highway_candidate.v1",
        "demand_config_version": "engineering_fixture.v1",
        "vehicle_type_config_version": "engineering_fixture.v1",
        "time_config_version": "engineering_candidate.v1",
        "measurement_scope": [
            "speed_mps",
            "acceleration_mps2",
            "net_gap_m",
            "closing_speed_mps",
            "ttc_status",
            "p2_engineering_adapter",
        ],
        "forbidden_scope": [],
        "engineering_status": "engineering_fixture_runnable",
        "scientific_status": "pending_network_demand_vtype_time_and_tolerance_approval",
        "scientific_parameter_status": {
            "network": "pending_scientific",
            "demand": "pending_scientific",
            "vehicle_type_mapping": "pending_scientific",
            "driver_behavior": "pending_scientific",
            "time_step": "pending_scientific",
            "warmup_and_evaluation_window": "pending_scientific",
        },
    },
    "lankershim_urban_auxiliary": {
        "scenario_id": "lankershim_urban_auxiliary",
        "role": "urban_following_risk_auxiliary",
        "reference_source": {
            "result_id": FORMAL_RESULT_ID,
            "version": "R2",
            "groups": ["lankershim__complete"],
            "role": "urban_following_risk",
        },
        "network_config_version": "not_built",
        "demand_config_version": "not_built",
        "vehicle_type_config_version": "not_built",
        "time_config_version": "not_built",
        "measurement_scope": ["speed_mps", "acceleration_mps2", "following_risk_auxiliary"],
        "forbidden_scope": [],
        "engineering_status": "candidate_entry_only",
        "scientific_status": "auxiliary_network_not_built_in_stage_0_5_3",
        "scientific_parameter_status": {
            "network": "pending_scientific",
            "demand": "pending_scientific",
            "vehicle_type_mapping": "pending_scientific",
            "driver_behavior": "pending_scientific",
            "time_step": "pending_scientific",
            "warmup_and_evaluation_window": "pending_scientific",
        },
    },
    "pneuma_urban_kinematics": {
        "scenario_id": "pneuma_urban_kinematics",
        "role": "urban_kinematics_only",
        "reference_source": {
            "result_id": FORMAL_RESULT_ID,
            "version": "R2",
            "groups": ["pneuma__athens_d1"],
            "role": "urban_kinematics_only",
        },
        "network_config_version": "not_built",
        "demand_config_version": "not_built",
        "vehicle_type_config_version": "not_built",
        "time_config_version": "not_built",
        "measurement_scope": ["speed_mps", "acceleration_mps2", "vehicle_type"],
        "forbidden_scope": ["ttc", "drac", "leader", "p2", "risk_events"],
        "engineering_status": "candidate_entry_only",
        "scientific_status": "urban_kinematics_only_network_not_built_in_stage_0_5_3",
        "scientific_parameter_status": {
            "network": "pending_scientific",
            "demand": "pending_scientific",
            "vehicle_type_mapping": "pending_scientific",
            "driver_behavior": "not_applicable_kinematics_only",
            "time_step": "pending_scientific",
            "warmup_and_evaluation_window": "pending_scientific",
        },
    },
}

#: Schema for scenarios that are approved as *entries* but have no built network yet.
CANDIDATE_SCENARIO_SCHEMA = {
    "required_fields": (
        "schema_version",
        "scenario_id",
        "role",
        "reference_source",
        "build_status",
        "network",
        "demand",
        "vehicle_types",
        "time_config",
        "measurement_scope",
        "forbidden_scope",
        "engineering_status",
        "scientific_status",
        "blocking_decisions",
    ),
    "allowed_build_status": ("not_built",),
}

CANDIDATE_SCENARIO_CONFIGS: dict[str, dict[str, Any]] = {
    "lankershim_urban_auxiliary": {
        "schema_version": f"{SCHEMA_ROOT}.candidate-scenario.v1",
        "scenario_id": "lankershim_urban_auxiliary",
        "role": "urban_following_risk_auxiliary",
        "reference_source": SCENARIO_MANIFEST["lankershim_urban_auxiliary"]["reference_source"],
        "build_status": "not_built",
        "network": {
            "spec": None,
            "status": "pending_scientific",
            "required_evidence": "urban arterial/intersection geometry, signal control and lane connections",
        },
        "demand": {"spec": None, "status": "pending_scientific"},
        "vehicle_types": {"mapping": None, "status": "pending_scientific"},
        "time_config": {"spec": None, "status": "pending_scientific"},
        "measurement_scope": SCENARIO_MANIFEST["lankershim_urban_auxiliary"]["measurement_scope"],
        "forbidden_scope": [],
        "engineering_status": "candidate_entry_only",
        "scientific_status": "auxiliary_network_not_built_in_stage_0_5_3",
        "blocking_decisions": [
            "urban network geometry and real road correspondence",
            "auxiliary measurement scope inside/outside the US-101 primary gate",
        ],
    },
    "pneuma_urban_kinematics": {
        "schema_version": f"{SCHEMA_ROOT}.candidate-scenario.v1",
        "scenario_id": "pneuma_urban_kinematics",
        "role": "urban_kinematics_only",
        "reference_source": SCENARIO_MANIFEST["pneuma_urban_kinematics"]["reference_source"],
        "build_status": "not_built",
        "network": {
            "spec": None,
            "status": "pending_scientific",
            "required_evidence": "urban mixed-traffic geometry with the approved vehicle-class composition",
        },
        "demand": {"spec": None, "status": "pending_scientific"},
        "vehicle_types": {"mapping": None, "status": "pending_scientific"},
        "time_config": {"spec": None, "status": "pending_scientific"},
        "measurement_scope": SCENARIO_MANIFEST["pneuma_urban_kinematics"]["measurement_scope"],
        "forbidden_scope": SCENARIO_MANIFEST["pneuma_urban_kinematics"]["forbidden_scope"],
        "engineering_status": "candidate_entry_only",
        "scientific_status": "urban_kinematics_only_network_not_built_in_stage_0_5_3",
        "blocking_decisions": [
            "urban network geometry and real road correspondence",
            "approved raw vehicle-class to SUMO vType mapping",
        ],
    },
}

#: Parameterised candidate highway corridor.  Explicitly NOT US-101 geometry.
NETWORK_DESIGN_CANDIDATE: dict[str, Any] = {
    "schema_version": f"{SCHEMA_ROOT}.network-candidate.v1",
    "network_id": "generic_highway_candidate",
    "classification": "generic_highway_candidate",
    "claim": "not_us101_geometry",
    "design_basis": [
        "sustained longitudinal car-following on a continuous mainline",
        "multiple mainline lanes so that lane occupancy and lateral position are variable",
        "one on-ramp and one off-ramp so that entering, driving and exiting are reproducible",
        "no traffic signals and no intersections, matching a freeway mainline risk scope",
    ],
    "nodes": [
        {"id": "hwy_w", "x": 0.0, "y": 0.0},
        {"id": "hwy_j1", "x": 400.0, "y": 0.0},
        {"id": "hwy_j2", "x": 700.0, "y": 0.0},
        {"id": "hwy_e", "x": 1200.0, "y": 0.0},
        {"id": "hwy_on", "x": 200.0, "y": -160.0},
        {"id": "hwy_off", "x": 950.0, "y": -160.0},
    ],
    "edges": [
        {"id": "main_0", "from": "hwy_w", "to": "hwy_j1", "lanes": 3, "speed_mps": 27.78, "priority": 2},
        {"id": "main_1", "from": "hwy_j1", "to": "hwy_j2", "lanes": 3, "speed_mps": 27.78, "priority": 2},
        {"id": "main_2", "from": "hwy_j2", "to": "hwy_e", "lanes": 3, "speed_mps": 27.78, "priority": 2},
        {"id": "onramp", "from": "hwy_on", "to": "hwy_j1", "lanes": 1, "speed_mps": 13.89, "priority": 1},
        {"id": "offramp", "from": "hwy_j2", "to": "hwy_off", "lanes": 1, "speed_mps": 13.89, "priority": 1},
    ],
    "routes": {
        "mainline": ["main_0", "main_1", "main_2"],
        "entering": ["onramp", "main_1", "main_2"],
        "exiting": ["main_0", "main_1", "offramp"],
    },
    "lengths_m": {"mainline_total": 1200.0, "main_0": 400.0, "main_1": 300.0, "main_2": 500.0},
    "lane_change_enabled": True,
    "supports": [
        "multi_vehicle_longitudinal_following",
        "continuous_traffic",
        "multiple_lane_occupancy",
        "leader_relation_and_net_gap_measurement",
        "ordinary_deceleration_and_following_response",
        "reproducible_entry_drive_and_exit",
    ],
    "approval_table": [
        {"parameter": "number_of_mainline_lanes", "candidate": 3, "status": "pending_scientific",
         "basis": "allows lane composition variation; US-101 lane count is not confirmed as 3"},
        {"parameter": "mainline_speed_limit_mps", "candidate": 27.78, "status": "pending_scientific",
         "basis": "100 km/h engineering assumption; not derived from the US-101 reference"},
        {"parameter": "mainline_total_length_m", "candidate": 1200.0, "status": "pending_scientific",
         "basis": "long enough for stable following; not a measured corridor length"},
        {"parameter": "ramp_presence", "candidate": "one_on_ramp_and_one_off_ramp", "status": "pending_scientific",
         "basis": "required for reproducible entry/exit behaviour"},
        {"parameter": "ramp_speed_limit_mps", "candidate": 13.89, "status": "pending_scientific",
         "basis": "engineering ramp assumption"},
        {"parameter": "signal_control", "candidate": "none", "status": "pending_scientific",
         "basis": "freeway mainline following risk scope"},
    ],
}

#: Engineering fixture vTypes.  ``engineering_fixture_only`` for everything.
ENGINEERING_FIXTURE_VTYPES: dict[str, dict[str, Any]] = {
    "engineering_car": {
        "vehicle_class": "passenger",
        "length_m": 5.0,
        "min_gap_m": 2.0,
        "max_speed_mps": 27.78,
        "accel_mps2": 2.0,
        "decel_mps2": 4.5,
        "emergency_decel_mps2": 9.0,
        "tau_s": 1.0,
        "car_following_model": "sumo_default_krauss",
        "mapping_status": "engineering_fixture_only",
    },
    "engineering_heavy_fixture": {
        "vehicle_class": "heavy",
        "length_m": 10.0,
        "min_gap_m": 3.0,
        "max_speed_mps": 22.0,
        "accel_mps2": 1.2,
        "decel_mps2": 4.0,
        "emergency_decel_mps2": 7.0,
        "tau_s": 1.2,
        "car_following_model": "sumo_default_krauss",
        "mapping_status": "engineering_fixture_only",
    },
    "engineering_queue_fixture": {
        "vehicle_class": "passenger",
        "length_m": 5.0,
        "min_gap_m": 2.0,
        "max_speed_mps": 10.0,
        "accel_mps2": 2.0,
        "decel_mps2": 4.5,
        "emergency_decel_mps2": 9.0,
        "tau_s": 1.0,
        "car_following_model": "sumo_default_krauss",
        "lane_change_disabled": True,
        "mapping_status": "engineering_fixture_only",
    },
}

#: pNEUMA raw classes stay unmapped: no approved scientific mapping exists yet.
PNEUMA_RAW_VEHICLE_TYPES = (
    "Car",
    "Taxi",
    "Motorcycle",
    "Bus",
    "Medium Vehicle",
    "Heavy Vehicle",
)


def vehicle_type_mapping_candidate() -> dict[str, Any]:
    """Return the auditable vType mapping candidate (no hidden scientific default)."""

    return {
        "schema_version": f"{SCHEMA_ROOT}.vehicle-type-mapping-candidate.v1",
        "scientific_mapping_approved": False,
        "mapping_version": "candidate-v1",
        "engineering_fixtures": {
            name: {**spec, "raw_vehicle_type": name, "sumo_vtype": name, "mapping_status": "engineering_fixture_only"}
            for name, spec in ENGINEERING_FIXTURE_VTYPES.items()
        },
        "real_reference_raw_types": {
            raw: {
                "raw_vehicle_type": raw,
                "sumo_vtype": None,
                "mapping_version": "candidate-v1",
                "vehicle_length_m": None,
                "acceleration_capability": None,
                "deceleration_capability": None,
                "car_following_model": None,
                "model_parameters": None,
                "mapping_status": "unmapped",
                "reason": "no researcher-approved scientific mapping exists for this raw class",
            }
            for raw in PNEUMA_RAW_VEHICLE_TYPES
        },
        "mapping_gaps": list(PNEUMA_RAW_VEHICLE_TYPES),
        "reporting_rule": (
            "unmapped classes must be reported as gaps; they must never be silently"
            " converted to a passenger-car type and never used for scientific vehicle-class calibration"
        ),
    }


#: Versioned calibration/validation partition approved for US-101 (Stage 0.5.2, decision 1).
CALIBRATION_VALIDATION_POLICY: dict[str, Any] = {
    "schema_version": f"{SCHEMA_ROOT}.calibration-validation-policy.v1",
    "calibration": ["us101__0750_0805", "us101__0805_0820"],
    "temporal_validation": ["us101__0820_0835"],
    "auxiliary": ["lankershim__complete", "pneuma__athens_d1"],
    "reference_result_id": FORMAL_RESULT_ID,
    "reference_version": "R2",
    "locked_holdout_accessed": False,
    "internal_window_isolation_is_not_project_locked_holdout": True,
    "validation_window_previously_published": True,
    "validation_is_same_site_time_extrapolation_only": True,
    "cross_road_generalization_claimed": False,
    "leave_one_window_analysis_role": "preregistered_sensitivity_diagnostic_only",
    "source_bindings": {
        "us101__0750_0805": "684a5f0b96dc48116f16d581c278d7039c0554bf1c3cea8d6eda3e605e3e8644",
        "us101__0805_0820": "7b0ef830c97a981da018d4e24b029e38aa2630387c728ea87b57926745880a9f",
        "us101__0820_0835": "a673217765b9a57ed3ea2c743b56fae0c5f538c7517e8e78685721c750082abb",
        "lankershim__complete": "650969c29bfe0e604694dc9d4cc5a47076a6d10188bcd81443b55628a713356c",
        "pneuma__athens_d1": "15893115824c43b00069b13308d9bff5048b92d7d217ac0c38c14523c7d42d65",
        "p2_formal_events": "aa749da3c8d68521111cc59f0d0f2746fecef868121d37ae76d3c75d43c10ae1",
    },
    "denied_uses": [
        "calibration access to the temporal validation window",
        "fitting calibration normalisers on validation-window statistics",
        "selecting calibration parameters from validation outputs",
        "creating new favourable acceptance thresholds from published validation summaries",
        "labelling internal window isolation as the project locked holdout",
    ],
    "access_roles": ["calibration", "temporal_validation", "auxiliary"],
    "locked_holdout": "forbidden_in_stage_0_5_3",
}


class Stage05EngineeringError(ValueError):
    """Raised when the Stage 0.5 engineering contract is violated."""


class Stage05AccessDenied(Stage05EngineeringError):
    """Raised when a fail-closed calibration/validation access decision is denied."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


# --------------------------------------------------------------------------------------
# configuration validation
# --------------------------------------------------------------------------------------


def validate_scenario_manifest(manifest: Mapping[str, Mapping[str, Any]] | None = None) -> None:
    manifest = SCENARIO_MANIFEST if manifest is None else manifest
    required = (
        "role",
        "reference_source",
        "network_config_version",
        "demand_config_version",
        "vehicle_type_config_version",
        "time_config_version",
        "measurement_scope",
        "engineering_status",
        "scientific_status",
    )
    for scenario_id, entry in manifest.items():
        missing = [key for key in required if key not in entry]
        if missing:
            raise Stage05EngineeringError(f"{scenario_id} scenario manifest missing: {missing}")
        reference = entry["reference_source"]
        if reference.get("result_id") != FORMAL_RESULT_ID:
            raise Stage05EngineeringError(f"{scenario_id} must bind the R2 real reference")
        for key, value in entry.get("scientific_parameter_status", {}).items():
            if value not in PARAMETER_CLASSES and not str(value).startswith("not_applicable"):
                raise Stage05EngineeringError(f"{scenario_id}.{key} has unknown parameter class {value!r}")


def validate_scenario_candidate_config(config: Mapping[str, Any]) -> None:
    missing = [key for key in CANDIDATE_SCENARIO_SCHEMA["required_fields"] if key not in config]
    if missing:
        raise Stage05EngineeringError(f"candidate scenario config missing fields: {missing}")
    if config["build_status"] not in CANDIDATE_SCENARIO_SCHEMA["allowed_build_status"]:
        raise Stage05EngineeringError(
            "candidate scenario config may only describe an unb""uilt scenario in Stage 0.5.3"
        )
    if config["scenario_id"] not in SCENARIO_MANIFEST:
        raise Stage05EngineeringError(f"unknown candidate scenario id {config['scenario_id']!r}")
    for key in ("network", "demand", "vehicle_types", "time_config"):
        block = config[key]
        if not isinstance(block, Mapping) or "status" not in block:
            raise Stage05EngineeringError(f"candidate scenario {key} requires an explicit status")
        if block.get("spec") is not None:
            raise Stage05EngineeringError(
                f"candidate scenario {key} must not pre-empt an unapproved specification"
            )
        if block["status"] not in PARAMETER_CLASSES and not str(block["status"]).startswith("not_applicable"):
            raise Stage05EngineeringError(f"candidate scenario {key} has unknown status {block['status']!r}")
    if not config["blocking_decisions"]:
        raise Stage05EngineeringError("candidate scenario must declare its blocking decisions")


def validate_vehicle_type_mapping(mapping: Mapping[str, Any]) -> None:
    if mapping.get("scientific_mapping_approved") is not False:
        raise Stage05EngineeringError("no scientific vType mapping is approved in Stage 0.5.3")
    for raw, entry in mapping["real_reference_raw_types"].items():
        if entry["mapping_status"] != "unmapped" or entry["sumo_vtype"] is not None:
            raise Stage05EngineeringError(f"raw vehicle type {raw!r} must remain explicitly unmapped")
    if set(mapping["mapping_gaps"]) != set(PNEUMA_RAW_VEHICLE_TYPES):
        raise Stage05EngineeringError("mapping gaps must report every unmapped raw class")
    for name, entry in mapping["engineering_fixtures"].items():
        if entry["mapping_status"] != "engineering_fixture_only":
            raise Stage05EngineeringError(f"fixture vType {name!r} must stay engineering_fixture_only")


def validate_parameter_classification(classification: Mapping[str, str]) -> None:
    unknown = {key: value for key, value in classification.items() if value not in PARAMETER_CLASSES}
    if unknown:
        raise Stage05EngineeringError(f"unknown parameter classes: {unknown}")
    approved = {key for key, value in classification.items() if value == "researcher_approved_scientific"}
    if approved:
        raise Stage05EngineeringError(
            "Stage 0.5.3 has no researcher-approved scientific parameter frozen in code: "
            + ", ".join(sorted(approved))
        )


def validate_no_message_config(config: Mapping[str, Any]) -> None:
    if config.get("experiment_mode") != "no_message_baseline":
        raise Stage05EngineeringError(
            "Stage 0.5 baseline must use experiment_mode=no_message_baseline"
        )
    for key in (
        "communication_enabled",
        "source_risk_treatment_enabled",
        "information_adoption_enabled",
    ):
        if bool(config.get(key, True)):
            raise Stage05EngineeringError(f"no_message_baseline requires {key}=false")


def validate_demand_config(demand: Mapping[str, Any]) -> None:
    required = (
        "schema_version",
        "mode",
        "demand_status",
        "derived_from",
        "vehicle_count",
        "depart_interval_s",
        "lane_composition",
        "vehicle_type_mix",
        "seeds",
    )
    missing = [key for key in required if key not in demand]
    if missing:
        raise Stage05EngineeringError(f"demand config missing fields: {missing}")
    if demand["mode"] not in ("explicit_departures_fixture", "flow_definition"):
        raise Stage05EngineeringError(f"unsupported demand mode {demand['mode']!r}")
    if demand["demand_status"] not in PARAMETER_CLASSES:
        raise Stage05EngineeringError(f"unknown demand_status {demand['demand_status']!r}")
    if demand["demand_status"] == "researcher_approved_scientific":
        raise Stage05EngineeringError("Stage 0.5.3 has no approved scientific demand level")
    forbidden = set(demand["derived_from"]) & (
        set(CALIBRATION_VALIDATION_POLICY["temporal_validation"])
        | set(CALIBRATION_VALIDATION_POLICY["auxiliary"])
    )
    if forbidden:
        raise Stage05EngineeringError(
            "demand must not be reverse-engineered from validation or auxiliary windows: "
            + ", ".join(sorted(forbidden))
        )
    if float(demand["depart_interval_s"]) <= 0 or int(demand["vehicle_count"]) < 2:
        raise Stage05EngineeringError("demand interval and vehicle count must be positive")
    if not isinstance(demand["lane_composition"], Mapping) or not demand["lane_composition"]:
        raise Stage05EngineeringError("demand requires an explicit lane composition")
    if not isinstance(demand["seeds"], Sequence) or not demand["seeds"]:
        raise Stage05EngineeringError("demand requires at least one declared seed")
    if abs(sum(float(v) for v in demand["vehicle_type_mix"].values()) - 1.0) > 1e-9:
        raise Stage05EngineeringError("vehicle type mix must sum to 1.0")


def validate_observation_cadence(
    time_s: Sequence[float],
    *,
    declared_step_s: float,
    tolerance_s: float = 1e-6,
    minimum_links: int = 1,
) -> dict[str, Any]:
    """Fail closed when recorded observations do not match the declared cadence.

    This prevents relabelling a coarser recording (for example 0.2 s) as the formal
    0.1 s observation cadence via interpolation, frame duplication or time relabelling.
    """

    if not np.isfinite(declared_step_s) or declared_step_s <= 0:
        raise Stage05EngineeringError("declared observation step must be finite and positive")
    values = np.asarray(list(time_s), dtype=float)
    if values.size < 2:
        return {"link_count": 0, "declared_step_s": declared_step_s, "max_abs_error_s": 0.0}
    deltas = np.diff(np.sort(values))
    links = deltas[deltas > tolerance_s]
    if links.size < minimum_links:
        raise Stage05EngineeringError("not enough observation links to verify the declared cadence")
    error = float(np.max(np.abs(links - declared_step_s)))
    if error > tolerance_s:
        raise Stage05EngineeringError(
            f"recorded observation cadence does not match the declared {declared_step_s} s"
            f" (max error {error}); refusing to relabel the cadence"
        )
    return {
        "link_count": int(links.size),
        "declared_step_s": float(declared_step_s),
        "observed_min_step_s": float(links.min()),
        "observed_max_step_s": float(links.max()),
        "max_abs_error_s": error,
    }


# --------------------------------------------------------------------------------------
# calibration / validation isolation (fail closed and auditable)
# --------------------------------------------------------------------------------------


@dataclass
class AccessDecision:
    role: str
    sources: list[str]
    purpose: str
    allowed: bool
    reason: str
    restricted_sources: list[str] = field(default_factory=list)
    checked_bindings: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "sources": list(self.sources),
            "purpose": self.purpose,
            "allowed": self.allowed,
            "reason": self.reason,
            "restricted_sources": list(self.restricted_sources),
            "checked_bindings": dict(self.checked_bindings),
        }


class CalibrationValidationGuard:
    """Fail-closed access guard with a complete, auditable decision record."""

    def __init__(self, policy: Mapping[str, Any] | None = None, *, log_path: str | Path | None = None):
        self.policy = dict(CALIBRATION_VALIDATION_POLICY if policy is None else policy)
        self.log_path = Path(log_path) if log_path is not None else None
        self.decisions: list[AccessDecision] = []

    # -- policy ---------------------------------------------------------------------
    @property
    def calibration_sources(self) -> set[str]:
        return set(self.policy.get("calibration", ()))

    @property
    def validation_sources(self) -> set[str]:
        return set(self.policy.get("temporal_validation", ()))

    @property
    def auxiliary_sources(self) -> set[str]:
        return set(self.policy.get("auxiliary", ()))

    def _record(self, decision: AccessDecision) -> AccessDecision:
        self.decisions.append(decision)
        return decision

    def evaluate(self, *, role: str, sources: Sequence[str], purpose: str = "") -> AccessDecision:
        requested = list(dict.fromkeys(str(source) for source in sources))
        if role not in self.policy.get("access_roles", ()):
            return self._record(
                AccessDecision(role, requested, purpose, False, "unknown_access_role", requested)
            )
        restricted: list[str] = []
        if role == "calibration":
            restricted = sorted(set(requested) & (self.validation_sources | self.auxiliary_sources))
        elif role == "temporal_validation":
            restricted = sorted(set(requested) - self.validation_sources)
        elif role == "auxiliary":
            restricted = sorted(set(requested) - self.auxiliary_sources)
        if restricted:
            return self._record(
                AccessDecision(role, requested, purpose, False, "restricted_source_for_role", restricted)
            )
        unknown = sorted(set(requested) - (self.calibration_sources | self.validation_sources | self.auxiliary_sources))
        if unknown:
            return self._record(
                AccessDecision(role, requested, purpose, False, "source_not_declared_in_policy", unknown)
            )
        return self._record(AccessDecision(role, requested, purpose, True, "allowed_by_policy"))

    def require(self, *, role: str, sources: Sequence[str], purpose: str = "") -> None:
        decision = self.evaluate(role=role, sources=sources, purpose=purpose)
        if self.log_path is not None:
            self.flush()
        if not decision.allowed:
            raise Stage05AccessDenied(
                f"access denied for role={role} sources={decision.restricted_sources} ({decision.reason})"
            )

    def require_source_read(
        self,
        path: str | Path,
        *,
        role: str,
        source: str,
        purpose: str = "",
        expected_sha256: str | None = None,
    ) -> str:
        """Verify role permission and the bound SHA-256 before any file read."""

        decision = self.evaluate(role=role, sources=[source], purpose=purpose or f"read {path}")
        if not decision.allowed:
            if self.log_path is not None:
                self.flush()
            raise Stage05AccessDenied(
                f"refusing to read {path}: {decision.reason} ({decision.restricted_sources})"
            )
        binding = self.policy.get("source_bindings", {}).get(source)
        target = Path(path)
        if binding is None:
            decision.allowed = False
            decision.reason = "missing_source_binding"
            if self.log_path is not None:
                self.flush()
            raise Stage05AccessDenied(f"refusing to read {path}: no policy binding for {source!r}")
        if expected_sha256 is not None and expected_sha256 != binding:
            decision.allowed = False
            decision.reason = "caller_binding_disagrees_with_policy"
            if self.log_path is not None:
                self.flush()
            raise Stage05AccessDenied(f"refusing to read {path}: caller binding disagrees with policy")
        if not target.is_file():
            decision.allowed = False
            decision.reason = "source_file_missing"
            if self.log_path is not None:
                self.flush()
            raise Stage05AccessDenied(f"refusing to read {path}: file does not exist")
        actual = _sha256_file(target)
        decision.checked_bindings[source] = actual
        if actual != binding:
            decision.allowed = False
            decision.reason = "source_sha256_mismatch"
            if self.log_path is not None:
                self.flush()
            raise Stage05AccessDenied(
                f"refusing to read {path}: SHA-256 {actual} does not match the bound reference"
            )
        if self.log_path is not None:
            self.flush()
        return actual

    def flush(self) -> None:
        if self.log_path is None:
            return
        self.log_path.write_text(
            json.dumps([decision.to_dict() for decision in self.decisions], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def audit(self) -> dict[str, Any]:
        denied = [decision for decision in self.decisions if not decision.allowed]
        return {
            "schema_version": f"{SCHEMA_ROOT}.access-audit.v1",
            "policy_schema_version": self.policy.get("schema_version"),
            "access_roles": list(self.policy.get("access_roles", ())),
            "request_count": len(self.decisions),
            "denied_count": len(denied),
            "denied_requests": [decision.to_dict() for decision in denied],
            "decisions": [decision.to_dict() for decision in self.decisions],
            "fail_closed": True,
            "locked_holdout_accessed": False,
            "validation_window_read": False,
        }


# --------------------------------------------------------------------------------------
# measurement core
# --------------------------------------------------------------------------------------


def validate_state_contract(frame: pd.DataFrame) -> None:
    required = {
        "run_id",
        "scenario_id",
        "experiment_mode",
        "configured_seed",
        "vehicle_id",
        "trajectory_id",
        "incarnation_id",
        "simulation_step",
        "time_s",
        "speed_mps",
        "acceleration_mps2",
        "leader_id",
        "leader_identity_status",
        "leader_speed_mps",
        "net_gap_m",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise Stage05EngineeringError("SUMO state frame is missing columns: " + ", ".join(missing))


def _leader_present(series: pd.Series) -> np.ndarray:
    text = series.astype("string")
    return (series.notna() & text.ne("<NA>") & text.ne("")).to_numpy()


def compute_sumo_measurements(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive the unified Stage 0.5 following / TTC / quality state.

    Missing, not-applicable and invalid states are preserved with an explicit
    reason; they are never converted into a finite TTC or into zero risk.
    """

    validate_state_contract(frame)
    result = frame.copy().reset_index(drop=True)
    speed = pd.to_numeric(result["speed_mps"], errors="coerce")
    leader_speed = pd.to_numeric(result["leader_speed_mps"], errors="coerce")
    gap = pd.to_numeric(result["net_gap_m"], errors="coerce")
    has_leader = _leader_present(result["leader_id"])
    identity_status = result["leader_identity_status"].astype("string").fillna("unresolved")
    observed = identity_status.eq("observed").to_numpy()
    finite_speed = np.isfinite(speed.to_numpy(float))
    finite_leader_speed = np.isfinite(leader_speed.to_numpy(float))
    finite_gap = np.isfinite(gap.to_numpy(float))

    result["leader_observed"] = has_leader
    result["closing_speed_mps"] = (speed - leader_speed).where(has_leader, np.nan)
    closing = result["closing_speed_mps"].to_numpy(float)

    # defaults: no observed leader is *not applicable*, never zero risk.
    result["ttc_s"] = np.nan
    result["ttc_valid"] = False
    result["following_status"] = "no_leader"
    result["measurement_status"] = "not_applicable"
    result["missing_reason"] = "no_observed_leader"
    result["reliable_following_eligible"] = False
    result["p2_evaluable_eligible"] = False

    identity_unresolved = has_leader & ~observed
    output_missing = has_leader & observed & (~finite_speed | ~finite_leader_speed | ~finite_gap)
    non_positive_gap = has_leader & observed & finite_gap & (gap.to_numpy(float) <= 0)
    reliable = has_leader & observed & finite_gap & (gap.to_numpy(float) > 0) & finite_speed & finite_leader_speed
    valid_ttc = reliable & np.isfinite(closing) & (closing > 0)

    result.loc[identity_unresolved, "measurement_status"] = "missing"
    result.loc[identity_unresolved, "missing_reason"] = "leader_identity_unresolved"
    result.loc[identity_unresolved, "following_status"] = "leader_identity_unresolved"

    result.loc[output_missing, "measurement_status"] = "missing"
    result.loc[output_missing, "missing_reason"] = "simulator_output_missing"
    result.loc[output_missing, "following_status"] = "measurement_missing"

    result.loc[non_positive_gap, "measurement_status"] = "invalid"
    result.loc[non_positive_gap, "missing_reason"] = "non_positive_net_gap"
    result.loc[non_positive_gap, "following_status"] = "gap_invalid"

    result.loc[reliable, "reliable_following_eligible"] = True
    result.loc[reliable, "p2_evaluable_eligible"] = True
    result.loc[reliable, "following_status"] = "following_steady"
    result.loc[reliable & (closing < 0), "following_status"] = "following_opening"
    result.loc[reliable & (closing == 0), "following_status"] = "following_steady"
    result.loc[valid_ttc, "following_status"] = "following_closing"

    # reliable, positive-gap but non-closing states remain P2-evaluable exposure.
    result.loc[reliable, "measurement_status"] = "not_applicable"
    result.loc[reliable, "missing_reason"] = "non_closing"
    result.loc[valid_ttc, "measurement_status"] = "valid"
    result.loc[valid_ttc, "missing_reason"] = ""
    result.loc[valid_ttc, "ttc_s"] = gap.to_numpy(float)[valid_ttc] / closing[valid_ttc]
    result.loc[valid_ttc, "ttc_valid"] = True

    unknown_status = ~np.isin(result["measurement_status"].to_numpy(), MEASUREMENT_STATUS)
    if unknown_status.any():
        raise Stage05EngineeringError("measurement_status left the approved vocabulary")
    if result.loc[result["measurement_status"].eq("missing"), "missing_reason"].astype(str).str.strip().eq("").any():
        raise Stage05EngineeringError("missing measurements always require a missing_reason")
    if result.loc[result["ttc_valid"], "ttc_s"].le(0).any():
        raise Stage05EngineeringError("a valid TTC must be positive")
    return result


def to_canonical_real_state(states: pd.DataFrame) -> pd.DataFrame:
    """Project SUMO states onto the Stage 0.3 canonical real-state contract.

    The projection is what a future Stage 0.5.4 calibration input would consume.
    It does not change any measurement semantic and does not claim the projection
    has already been accepted as calibration input.
    """

    validate_state_contract(states)
    projection = pd.DataFrame(
        {
            "dataset": "sumo",
            "site": states["scenario_id"].astype(str),
            "window_id": states["run_id"].astype(str),
            "vehicle_id": states["vehicle_id"].astype(str),
            "time_s": pd.to_numeric(states["time_s"], errors="coerce"),
            "x_m": pd.to_numeric(states.get("x_m"), errors="coerce"),
            "y_m": pd.to_numeric(states.get("y_m"), errors="coerce"),
            "speed_mps": pd.to_numeric(states["speed_mps"], errors="coerce"),
            "acceleration_mps2": pd.to_numeric(states["acceleration_mps2"], errors="coerce"),
            "road_id": states.get("edge_id", pd.Series([None] * len(states))).astype("string"),
            "lane_id": states.get("lane_id", pd.Series([None] * len(states))).astype("string"),
            "leader_id": states["leader_id"].astype("string"),
            "net_gap_m": pd.to_numeric(states["net_gap_m"], errors="coerce"),
            "closing_speed_mps": pd.to_numeric(states["closing_speed_mps"], errors="coerce"),
            "measurement_status": states["measurement_status"].astype(str),
            "missing_reason": states["missing_reason"].fillna("").astype(str),
        }
    )
    return projection


# --------------------------------------------------------------------------------------
# P2 adapters
# --------------------------------------------------------------------------------------


def cadence_max_gap_s(recorded_observation_step_s: float) -> float:
    """Scale the formal 0.11 s link tolerance to the declared recorded cadence."""

    if recorded_observation_step_s <= 0:
        raise Stage05EngineeringError("recorded observation step must be positive")
    return float(recorded_observation_step_s) * (FORMAL_MAX_GAP_S / FORMAL_OBSERVATION_STEP_S)


def _risk_mask(group: pd.DataFrame, threshold_s: float) -> np.ndarray:
    ttc = pd.to_numeric(group["ttc_s"], errors="coerce").to_numpy(float)
    return group["ttc_valid"].astype(bool).to_numpy() & np.isfinite(ttc) & (ttc < threshold_s)


def _continuous_risk_segments(
    group: pd.DataFrame, *, minimum_duration_s: float, max_gap_s: float, ttc_threshold_s: float
) -> list[pd.DataFrame]:
    ordered = group.sort_values(["time_s", "simulation_step"], kind="stable").reset_index(drop=True)
    mask = _risk_mask(ordered, ttc_threshold_s)
    segments: list[list[int]] = []
    current: list[int] = []
    for position, row in enumerate(ordered.to_dict("records")):
        if not bool(mask[position]):
            if current:
                segments.append(current)
                current = []
            continue
        if not current:
            current = [position]
            continue
        previous = ordered.iloc[current[-1]]
        same_pair = (
            str(previous.get("leader_id")) == str(row.get("leader_id"))
            and str(previous.get("leader_incarnation_id")) == str(row.get("leader_incarnation_id"))
        )
        same_incarnation = str(previous.get("incarnation_id")) == str(row.get("incarnation_id"))
        dt = float(row["time_s"]) - float(previous["time_s"])
        if not same_pair or not same_incarnation or dt <= 0 or dt > max_gap_s + 1e-9:
            segments.append(current)
            current = [position]
        else:
            current.append(position)
    if current:
        segments.append(current)
    return [
        ordered.iloc[positions].copy()
        for positions in segments
        if float(ordered["time_s"].iloc[positions[-1]] - ordered["time_s"].iloc[positions[0]])
        >= minimum_duration_s - 1e-9
    ]


def build_sumo_p2_events(
    states: pd.DataFrame,
    *,
    recorded_observation_step_s: float = FORMAL_OBSERVATION_STEP_S,
    ttc_threshold_s: float = FORMAL_TTC_THRESHOLD_S,
    minimum_duration_s: float = FORMAL_MINIMUM_DURATION_S,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """SUMO-native engineering P2 adapter.

    Segments reuse the Stage 0.2 definitions (TTC threshold, minimum observed span,
    observed confirmation timestamp, leader/incarnation/time continuity) but are
    produced from simulator-native identity, so formal comparability stays pending.
    """

    max_gap_s = cadence_max_gap_s(recorded_observation_step_s)
    measured = states if "measurement_status" in states.columns else compute_sumo_measurements(states)
    measured = measured.reset_index(drop=True)
    group_columns = [
        column
        for column in ("run_id", "scenario_id", "fixture_id", "vehicle_id", "incarnation_id")
        if column in measured.columns
    ]
    events: list[dict[str, Any]] = []
    for group_key, group in measured.groupby(group_columns, dropna=False, sort=True):
        key_values = group_key if isinstance(group_key, tuple) else (group_key,)
        key_text = "|".join(str(value) for value in key_values)
        for segment_index, segment in enumerate(
            _continuous_risk_segments(
                group,
                minimum_duration_s=minimum_duration_s,
                max_gap_s=max_gap_s,
                ttc_threshold_s=ttc_threshold_s,
            )
        ):
            onset = float(segment["time_s"].iloc[0])
            confirmation_rows = segment.loc[
                pd.to_numeric(segment["time_s"], errors="coerce") - onset >= minimum_duration_s - 1e-9
            ]
            if confirmation_rows.empty:
                continue
            confirm = float(confirmation_rows["time_s"].iloc[0])
            ended = float(segment["time_s"].iloc[-1])
            following = measured[
                measured["incarnation_id"].eq(segment["incarnation_id"].iloc[0])
                & measured["time_s"].gt(ended)
            ].sort_values("time_s", kind="stable")
            if following.empty:
                exit_reason = "observation_end_right_censored"
            else:
                following_row = following.iloc[0]
                if str(following_row.get("leader_id")) != str(segment["leader_id"].iloc[0]):
                    exit_reason = "leader_switch_unknown_risk"
                elif str(following_row.get("measurement_status")) != "valid":
                    exit_reason = "measurement_unavailable_unknown_risk"
                else:
                    exit_reason = "observed_threshold_exit"
            events.append(
                {
                    "event_id": f"sumo_p2_engineering::{key_text}::{segment_index}",
                    "run_id": segment["run_id"].iloc[0] if "run_id" in segment else None,
                    "scenario_id": segment["scenario_id"].iloc[0] if "scenario_id" in segment else None,
                    "fixture_id": segment["fixture_id"].iloc[0] if "fixture_id" in segment else None,
                    "vehicle_id": segment["vehicle_id"].iloc[0],
                    "incarnation_id": segment["incarnation_id"].iloc[0],
                    "leader_id": segment["leader_id"].iloc[0],
                    "leader_incarnation_id": segment["leader_incarnation_id"].iloc[0]
                    if "leader_incarnation_id" in segment
                    else None,
                    "conflict_type": "rear_end",
                    "event_start_s": onset,
                    "event_end_s": ended,
                    "event_duration_s": float(ended - onset),
                    "event_observed_span_s": float(ended - onset),
                    "event_confirm_s": confirm,
                    "ttc_min_s": float(pd.to_numeric(segment["ttc_s"], errors="coerce").min()),
                    "raw_frame_count": int(len(segment)),
                    "inclusion_status": "engineering_only",
                    "exclusion_reason": "",
                    "rule": "P2",
                    "ttc_threshold_s": float(ttc_threshold_s),
                    "minimum_duration_s": float(minimum_duration_s),
                    "max_gap_s": float(max_gap_s),
                    "algorithm_version": FORMAL_ALGORITHM_VERSION,
                    "adapter": "sumo_native_engineering_v1",
                    "measurement_equivalence_status": "pending_sumo_adapter_review",
                    "scientific_claim_eligible": False,
                }
            )
    columns = [
        "event_id", "run_id", "scenario_id", "fixture_id", "vehicle_id", "incarnation_id",
        "leader_id", "leader_incarnation_id", "conflict_type", "event_start_s", "event_end_s",
        "event_duration_s", "event_observed_span_s", "event_confirm_s", "ttc_min_s",
        "raw_frame_count", "inclusion_status", "exclusion_reason", "rule", "ttc_threshold_s",
        "minimum_duration_s", "max_gap_s", "algorithm_version", "adapter",
        "measurement_equivalence_status", "scientific_claim_eligible",
    ]
    event_frame = pd.DataFrame(events, columns=columns)
    return event_frame, compute_exposure(measured, recorded_observation_step_s=recorded_observation_step_s)


def compute_exposure(states: pd.DataFrame, *, recorded_observation_step_s: float) -> dict[str, Any]:
    """Reliable-following, reliable-closing and P2-evaluable following exposure."""

    max_gap_s = cadence_max_gap_s(recorded_observation_step_s)
    group_columns = [
        column
        for column in ("run_id", "scenario_id", "fixture_id", "vehicle_id", "incarnation_id")
        if column in states.columns
    ]
    following = closing = evaluable = 0.0
    evaluable_status = {"valid", "not_applicable"}
    for _, group in states.groupby(group_columns, dropna=False, sort=False):
        ordered = group.sort_values(["time_s", "simulation_step"], kind="stable")
        for first, second in zip(ordered.iloc[:-1].to_dict("records"), ordered.iloc[1:].to_dict("records")):
            dt = float(second["time_s"]) - float(first["time_s"])
            same_pair = (
                str(first.get("leader_id")) == str(second.get("leader_id"))
                and str(first.get("leader_incarnation_id")) == str(second.get("leader_incarnation_id"))
                and str(first.get("incarnation_id")) == str(second.get("incarnation_id"))
            )
            if dt <= 0 or dt > max_gap_s + 1e-9 or not same_pair:
                continue
            if bool(first.get("reliable_following_eligible")) and bool(second.get("reliable_following_eligible")):
                following += dt
            if bool(first.get("ttc_valid")) and bool(second.get("ttc_valid")):
                closing += dt
            if (
                bool(first.get("p2_evaluable_eligible"))
                and bool(second.get("p2_evaluable_eligible"))
                and str(first.get("measurement_status")) in evaluable_status
                and str(second.get("measurement_status")) in evaluable_status
            ):
                evaluable += dt
    return {
        "schema_version": f"{SCHEMA_ROOT}.p2-exposure.v1",
        "recorded_observation_step_s": float(recorded_observation_step_s),
        "link_max_gap_s": float(max_gap_s),
        "reliable_following_exposure_s": following,
        "reliable_closing_exposure_s": closing,
        "p2_evaluable_following_exposure_s": evaluable,
        "p2_evaluable_following_vehicle_hours": evaluable / 3600.0,
        "exposure_unit": "vehicle-second (converted to vehicle-hour for the event rate)",
        "rate_formula": "p2_event_count / p2_evaluable_following_vehicle_hours",
        "status": "pending_measurement_equivalence",
        "formal_rate_eligible": False,
        "scientific_claim_eligible": False,
    }


#: Field-by-field correspondence between the Stage 0.2 formal contract and SUMO.
SUMO_FORMAL_FIELD_MAP: dict[str, dict[str, str]] = {
    "dataset": {"sumo_source": "constant 'sumo'", "status": "provided_by_sumo_adapter"},
    "site": {"sumo_source": "scenario_id", "status": "provided_by_sumo_adapter"},
    "window_id": {"sumo_source": "run_id", "status": "provided_by_sumo_adapter"},
    "source_member": {"sumo_source": "incarnation_id (run-scoped vehicle identity)", "status": "provided_by_sumo_adapter"},
    "source_period": {"sumo_source": "experiment_mode", "status": "provided_by_sumo_adapter"},
    "trajectory_id": {"sumo_source": "incarnation_id", "status": "provided_by_sumo_adapter"},
    "leader_trajectory_id": {"sumo_source": "leader_incarnation_id", "status": "provided_by_sumo_adapter"},
    "time_s": {"sumo_source": "traci.simulation.getTime()", "status": "provided_by_sumo_adapter"},
    "original_row_number": {
        "sumo_source": "observation_index (adapter-defined recorded observation counter)",
        "status": "adapter_defined_simulator_frame_index",
        "note": "not an NGSIM original row number; never claimed as one",
    },
    "frame_id": {"sumo_source": "observation_index", "status": "adapter_defined_simulator_frame_index"},
    "global_time_ms": {"sumo_source": "round(time_s * 1000)", "status": "provided_by_sumo_adapter"},
    "diagnostic_clock_anchor_ms": {
        "sumo_source": "constant 0 for every recorded state",
        "status": "definitional_constant",
        "note": (
            "SUMO has one monotonic simulator clock per process; NGSIM clock-conflict"
            " categories are not_applicable_to_simulator_observation"
        ),
    },
    "identity_uncertain": {"sumo_source": "constant False", "status": "provided_by_sumo_adapter"},
    "identity_break": {"sumo_source": "incarnation change detection", "status": "provided_by_sumo_adapter"},
    "observation_gap": {"sumo_source": "recorded cadence break detection", "status": "provided_by_sumo_adapter"},
    "leader_identity_uncertain": {
        "sumo_source": "leader_identity_status != 'observed'",
        "status": "provided_by_sumo_adapter",
    },
    "leader_matched": {"sumo_source": "leader observed and incarnation-resolved", "status": "provided_by_sumo_adapter"},
    "leader_frame_id": {"sumo_source": "leader observation_index (same-step leader lookup)", "status": "provided_by_sumo_adapter"},
    "measurement_status": {"sumo_source": "Stage 0.5 unified quality state", "status": "provided_by_sumo_adapter"},
    "ttc_s": {"sumo_source": "net_gap_m / closing_speed_mps", "status": "provided_by_sumo_adapter"},
    "ttc_valid": {"sumo_source": "positive net gap and positive closing speed", "status": "provided_by_sumo_adapter"},
    "drac_mps2": {
        "sumo_source": "not computed in the Stage 0.5 adapter",
        "status": "not_implemented_adapter_carries_nan",
        "note": "P2 event identity does not depend on DRAC; NaN is preserved, never fabricated",
    },
}

SUMO_FORMAL_EQUIVALENCE_STATUS = "pending_measurement_equivalence_review"


def build_sumo_formal_source_frame(
    states: pd.DataFrame, *, recorded_observation_step_s: float = FORMAL_OBSERVATION_STEP_S
) -> pd.DataFrame:
    """Map SUMO states onto the Stage 0.2 formal field contract, item by item."""

    measured = states if "measurement_status" in states.columns else compute_sumo_measurements(states)
    measured = measured.reset_index(drop=True)
    ordered = measured.sort_values(["incarnation_id", "time_s"], kind="stable").copy()
    ordered["observation_index"] = ordered.groupby("incarnation_id", sort=False).cumcount().astype("int64")
    step_ms = int(round(float(recorded_observation_step_s) * 1000))
    ordered["global_time_ms"] = (ordered["observation_index"] * step_ms).astype("int64")
    ordered["frame_id"] = ordered["observation_index"].astype("int64")
    ordered["original_row_number"] = ordered["observation_index"].astype("int64")
    ordered["leader_frame_id"] = ordered["observation_index"].astype("int64")
    ordered["diagnostic_clock_anchor_ms"] = 0
    ordered["dataset"] = "sumo"
    ordered["site"] = ordered["scenario_id"].astype(str)
    ordered["window_id"] = ordered["run_id"].astype(str)
    ordered["source_member"] = ordered["incarnation_id"].astype(str)
    ordered["source_period"] = ordered["experiment_mode"].astype(str)
    ordered["trajectory_id"] = ordered["incarnation_id"].astype(str)
    ordered["leader_trajectory_id"] = ordered["leader_incarnation_id"].astype("string")
    ordered["identity_uncertain"] = False
    ordered["identity_break"] = False
    ordered["observation_gap"] = False
    ordered["leader_identity_uncertain"] = ~ordered["leader_identity_status"].astype("string").eq("observed")
    ordered["leader_matched"] = ordered["leader_id"].notna() & ~ordered["leader_identity_uncertain"]
    ordered["drac_mps2"] = np.nan
    if abs(float(recorded_observation_step_s) - FORMAL_OBSERVATION_STEP_S) > 1e-9:
        # non-0.1 s cadence: mark every link as a gap so the formal continuity rules
        # cannot silently accept a coarser recording as 100 ms evidence.
        ordered["observation_gap"] = True
    return ordered


def extract_sumo_formal_p2_events(
    states: pd.DataFrame,
    *,
    recorded_observation_step_s: float = FORMAL_OBSERVATION_STEP_S,
    allow_nonstandard_cadence: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Reuse the Stage 0.2 formal extractor on SUMO states without NGSIM metadata.

    The adapter never fabricates NGSIM rows, Frame_IDs, clock anchors or vehicle
    identities; it supplies documented simulator-native equivalents.  Formal
    comparability therefore remains explicitly pending review.
    """

    if abs(float(recorded_observation_step_s) - FORMAL_OBSERVATION_STEP_S) > 1e-9 and not allow_nonstandard_cadence:
        raise Stage05EngineeringError(
            "the formal Stage 0.2 extractor assumes a 0.1 s cadence;"
            " a coarser recording must not be relabelled as 0.1 s evidence."
            " Pass allow_nonstandard_cadence=True only to obtain an explicitly"
            " non-comparable engineering diagnostic."
        )
    frame = build_sumo_formal_source_frame(
        states, recorded_observation_step_s=recorded_observation_step_s
    )
    raw, reliable, rejected = extract_formal_source_events(frame, P2_FORMAL_CONFIG, return_diagnostics=True)
    status = SUMO_FORMAL_EQUIVALENCE_STATUS
    if abs(float(recorded_observation_step_s) - FORMAL_OBSERVATION_STEP_S) > 1e-9:
        status = "pending_measurement_equivalence_nonstandard_cadence"
    audit = {
        "schema_version": f"{SCHEMA_ROOT}.formal-adapter-audit.v1",
        "algorithm_version": FORMAL_ALGORITHM_VERSION,
        "equivalence_status": status,
        "field_map": SUMO_FORMAL_FIELD_MAP,
        "ngsim_only_fields": {
            name: "not_applicable_to_simulator_observation" for name in NGSIM_ONLY_MISSING_REASONS
        },
        "raw_candidate_events": int(len(raw)),
        "reliable_candidate_events": int(len(reliable)),
        "rejected_candidate_events": int(len(rejected)),
        "recorded_observation_step_s": float(recorded_observation_step_s),
        "formal_comparability": False,
        "scientific_claim_eligible": False,
    }
    for frame_part in (raw, reliable, rejected):
        if not frame_part.empty:
            frame_part["adapter"] = "sumo_formal_alignment_v1"
            frame_part["measurement_equivalence_status"] = status
            frame_part["scientific_claim_eligible"] = False
    return reliable, audit


def measurement_support_matrix() -> dict[str, Any]:
    """Per-item engineering support state, kept honest and explicit."""

    return {
        "schema_version": f"{SCHEMA_ROOT}.measurement-support.v1",
        "items": {
            "speed_and_acceleration": {"status": "verified_engineering", "source": "traci.vehicle.getSpeed/getAcceleration"},
            "leader_identity": {"status": "verified_engineering", "source": "traci.vehicle.getLeader + incarnation scope"},
            "net_gap": {"status": "verified_engineering", "rule": NET_GAP_SEMANTICS["physical_net_gap_rule"]},
            "closing_speed": {"status": "verified_engineering", "rule": CLOSING_SPEED_SEMANTICS["definition"]},
            "ttc_status": {"status": "verified_engineering", "rule": CLOSING_SPEED_SEMANTICS["ttc_rule"]},
            "measurement_quality_and_reasons": {"status": "verified_engineering", "vocabulary": list(MEASUREMENT_STATUS)},
            "p2_event_extraction": {"status": "engineering_only", "reason": "SUMO-native adapter; formal equivalence pending"},
            "p2_evaluable_exposure": {"status": "engineering_only", "reason": "denominator interface prepared, not calibration-accepted"},
            "formal_p2_equivalence": {"status": "pending_measurement_equivalence"},
            "reality_coverage": {"status": "pending_scientific", "reason": "requires Stage 0.5.4 calibration and Stage 0.5.5 validation"},
        },
        "engineering_only": True,
        "scientific_claim_eligible": False,
    }


# --------------------------------------------------------------------------------------
# vehicle identity scope
# --------------------------------------------------------------------------------------


class VehicleIdentityTracker:
    """Run-scoped vehicle identity with auditable re-entry incarnations."""

    def __init__(self, run_id: str):
        self.run_id = str(run_id)
        self._active: dict[str, str] = {}
        self._next: dict[str, int] = {}
        self.events: list[dict[str, Any]] = []

    def observe(self, active_vehicle_ids: Iterable[str], *, time_s: float, observation_index: int) -> list[dict[str, str]]:
        active_ids = sorted(active_vehicle_ids)
        for vehicle_id in active_ids:
            if vehicle_id in self._active:
                continue
            index = self._next.get(vehicle_id, 0)
            self._next[vehicle_id] = index + 1
            incarnation = f"{self.run_id}|{vehicle_id}|{index}"
            self._active[vehicle_id] = incarnation
            self.events.append(
                {
                    "run_id": self.run_id,
                    "vehicle_id": vehicle_id,
                    "incarnation_id": incarnation,
                    "event_type": "enter",
                    "time_s": float(time_s),
                    "observation_index": int(observation_index),
                }
            )
        for vehicle_id in sorted(set(self._active) - set(active_ids)):
            self.events.append(
                {
                    "run_id": self.run_id,
                    "vehicle_id": vehicle_id,
                    "incarnation_id": self._active.pop(vehicle_id),
                    "event_type": "exit",
                    "time_s": float(time_s),
                    "observation_index": int(observation_index),
                }
            )
        return [{"vehicle_id": vehicle_id, "incarnation_id": incarnation} for vehicle_id, incarnation in sorted(self._active.items())]

    def incarnation_of(self, vehicle_id: str) -> str | None:
        return self._active.get(vehicle_id)

    def close(self, *, time_s: float, observation_index: int) -> None:
        for vehicle_id in sorted(self._active):
            self.events.append(
                {
                    "run_id": self.run_id,
                    "vehicle_id": vehicle_id,
                    "incarnation_id": self._active[vehicle_id],
                    "event_type": "active_at_observation_end",
                    "time_s": float(time_s),
                    "observation_index": int(observation_index),
                }
            )
        self._active.clear()


# --------------------------------------------------------------------------------------
# SUMO environment and fixture network
# --------------------------------------------------------------------------------------


def _sumo_binary() -> str:
    binary = shutil.which("sumo")
    if binary is None:
        raise Stage05EngineeringError("SUMO executable not found on PATH")
    return binary


def _netconvert_binary() -> str:
    binary = shutil.which("netconvert")
    if binary is None:
        raise Stage05EngineeringError("netconvert executable not found on PATH")
    return binary


def sumo_environment() -> dict[str, Any]:
    executable = Path(_sumo_binary()).resolve()
    netconvert = Path(_netconvert_binary()).resolve()
    result = subprocess.run([str(executable), "--version"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise Stage05EngineeringError(result.stderr.strip() or "SUMO version query failed")
    version_line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "unknown")
    import traci  # noqa: PLC0415 - imported lazily so the module stays importable without SUMO

    traci_version = getattr(getattr(traci, "version", None), "__version__", "unknown") or "unknown"
    return {
        "sumo_version": version_line,
        "sumo_executable": str(executable),
        "sumo_executable_sha256": _sha256_file(executable),
        "netconvert_executable": str(netconvert),
        "netconvert_executable_sha256": _sha256_file(netconvert),
        "traci_module": str(Path(traci.__file__).resolve()),
        "traci_version": traci_version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "sumo_home": _ensure_traci_importable(),
    }


def _ensure_traci_importable() -> str:
    executable = Path(_sumo_binary()).resolve()
    for tools_dir in (executable.parent.parent / "tools", executable.parent / "tools"):
        if (tools_dir / "traci" / "__init__.py").is_file():
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            return str(tools_dir.resolve())
    raise Stage05EngineeringError(f"TraCI tools directory not found beside {executable}")


def build_candidate_network(work: Path, spec: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the generic highway candidate network with netconvert."""

    spec = NETWORK_DESIGN_CANDIDATE if spec is None else spec
    work.mkdir(parents=True, exist_ok=True)
    node_lines = [f'  <node id="{node["id"]}" x="{node["x"]}" y="{node["y"]}" type="priority"/>' for node in spec["nodes"]]
    edge_lines = [
        f'  <edge id="{edge["id"]}" from="{edge["from"]}" to="{edge["to"]}"'
        f' priority="{edge.get("priority", 1)}" numLanes="{edge["lanes"]}" speed="{edge["speed_mps"]}"/>'
        for edge in spec["edges"]
    ]
    nodes_path = work / "nodes.nod.xml"
    edges_path = work / "edges.edg.xml"
    net_path = work / f"{spec['network_id']}.net.xml"
    nodes_path.write_text("<nodes>\n" + "\n".join(node_lines) + "\n</nodes>\n", encoding="utf-8", newline="\n")
    edges_path.write_text("<edges>\n" + "\n".join(edge_lines) + "\n</edges>\n", encoding="utf-8", newline="\n")
    result = subprocess.run(
        [_netconvert_binary(), "-n", str(nodes_path), "-e", str(edges_path), "-o", str(net_path),
         "--no-turnarounds", "true"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise Stage05EngineeringError(f"netconvert failed: {result.stderr.strip()}")
    return {
        "nodes": nodes_path,
        "edges": edges_path,
        "network": net_path,
        "command": [_netconvert_binary(), "-n", str(nodes_path), "-e", str(edges_path), "-o", str(net_path)],
        "spec": dict(spec),
    }


@dataclass(frozen=True)
class FixtureVehicle:
    vehicle_id: str
    vtype: str
    route: str
    depart_s: float
    depart_lane: str
    depart_pos_m: float
    depart_speed_mps: float
    stop_lane: str | None = None
    stop_end_pos_m: float | None = None
    stop_duration_s: float | None = None

    def to_xml(self) -> str:
        stop = ""
        if self.stop_lane is not None:
            stop = (
                f'<stop lane="{self.stop_lane}" endPos="{self.stop_end_pos_m}"'
                f' duration="{self.stop_duration_s}"/>'
            )
        return (
            f'  <vehicle id="{self.vehicle_id}" type="{self.vtype}" route="{self.route}"'
            f' depart="{self.depart_s}" departLane="{self.depart_lane}" departPos="{self.depart_pos_m}"'
            f' departSpeed="{self.depart_speed_mps}">{stop}</vehicle>'
        )


def _vt_attributes(spec: Mapping[str, Any]) -> str:
    attributes = [
        f'accel="{spec["accel_mps2"]}"',
        f'decel="{spec["decel_mps2"]}"',
        f'emergencyDecel="{spec["emergency_decel_mps2"]}"',
        'sigma="0.0"',
        f'tau="{spec["tau_s"]}"',
        f'length="{spec["length_m"]}"',
        f'minGap="{spec["min_gap_m"]}"',
        f'maxSpeed="{spec["max_speed_mps"]}"',
    ]
    if spec.get("lane_change_disabled"):
        attributes += ['lcStrategic="0"', 'lcSpeedGain="0"', 'lcCooperative="0"', 'lcKeepRight="0"']
    return " ".join(attributes)


def engineering_fixture(fixture_id: str, *, seed: int, duration_s: float) -> dict[str, Any]:
    """Return an explicitly engineering-only demand fixture."""

    common = {
        "schema_version": f"{SCHEMA_ROOT}.engineering-fixture.v1",
        "fixture_id": fixture_id,
        "engineering_only": True,
        "scientific_claim_eligible": False,
        "stimulus": "none",
        "stimulus_note": "no message, adoption, treatment or scripted remote-risk response",
        "seed": int(seed),
        "duration_s": float(duration_s),
    }
    if fixture_id == "baseline_mixed_demand":
        vehicles: list[FixtureVehicle] = []
        lanes = {"0": 5, "1": 5, "2": 4}
        index = 0
        for lane, count in lanes.items():
            for position in range(count):
                vehicles.append(
                    FixtureVehicle(
                        vehicle_id=f"main_{lane}_{position}",
                        vtype="engineering_car" if position % 4 else "engineering_heavy_fixture",
                        route="mainline",
                        depart_s=round(position * 3.0, 3),
                        depart_lane=lane,
                        depart_pos_m=float(20 + position * 70),
                        depart_speed_mps=float(15 + (position % 3) * 2),
                    )
                )
                index += 1
        vehicles.append(
            FixtureVehicle("entry_0", "engineering_car", "entering", 6.0, "0", 40.0, 12.0)
        )
        vehicles.append(
            FixtureVehicle("entry_1", "engineering_heavy_fixture", "entering", 20.0, "0", 60.0, 10.0)
        )
        vehicles.append(
            FixtureVehicle("exit_0", "engineering_car", "exiting", 10.0, "1", 40.0, 16.0)
        )
        return {
            **common,
            "purpose": "no-message baseline state / leader / gap / closing-speed / TTC chain",
            "vehicles": vehicles,
            "lane_change_enabled": True,
            "notes": "engineering positions, speeds and type mix; not a calibrated demand",
        }
    if fixture_id == "measurement_probe_queue_stop":
        # A stopped queue tail on every mainline lane, approached by faster followers.
        # The stop is a declarative SUMO <stop> element, not a scripted intervention.
        vehicles = [
            FixtureVehicle(
                vehicle_id=f"probe_lead_{lane}",
                vtype="engineering_queue_fixture",
                route="mainline",
                depart_s=0.0,
                depart_lane=lane,
                depart_pos_m=380.0,
                depart_speed_mps=0.0,
                stop_lane=f"main_0_{lane}",
                stop_end_pos_m=385.0,
                stop_duration_s=45.0,
            )
            for lane in ("0", "1", "2")
        ]
        for position in range(1, 5):
            vehicles.append(
                FixtureVehicle(
                    vehicle_id=f"probe_follow_{position}",
                    vtype="engineering_queue_fixture",
                    route="mainline",
                    depart_s=2.0,
                    depart_lane="0",
                    depart_pos_m=float(380 - position * 25),
                    depart_speed_mps=10.0,
                )
            )
        return {
            **common,
            "purpose": (
                "exercise the TTC/P2 adapter with a stopped multi-lane queue tail that is"
                " approached by faster followers"
            ),
            "stimulus": "declarative_stop_element_on_queue_tail_vehicles",
            "vehicles": vehicles,
            "lane_change_enabled": False,
            "notes": (
                "engineering probe fixture: the queue tail is a modelled stationary vehicle,"
                " not calibrated real traffic and not a remote-risk treatment"
            ),
        }
    raise Stage05EngineeringError(f"unknown engineering fixture {fixture_id!r}")


def _write_route_file(work: Path, fixture: Mapping[str, Any], *, route_spec: Mapping[str, Sequence[str]]) -> Path:
    lines = [
        f'  <vType id="{name}" {_vt_attributes(spec)}/>' for name, spec in ENGINEERING_FIXTURE_VTYPES.items()
    ]
    used_routes = {vehicle.route for vehicle in fixture["vehicles"]}
    for route_id in sorted(used_routes):
        if route_id not in route_spec:
            raise Stage05EngineeringError(f"fixture route {route_id!r} is not part of the network candidate")
        lines.append(f'  <route id="{route_id}" edges="{" ".join(route_spec[route_id])}"/>')
    lines += [vehicle.to_xml() for vehicle in sorted(fixture["vehicles"], key=lambda vehicle: (vehicle.depart_s, vehicle.vehicle_id))]
    routes_path = work / "demand.rou.xml"
    routes_path.write_text("<routes>\n" + "\n".join(lines) + "\n</routes>\n", encoding="utf-8", newline="\n")
    return routes_path


def _write_sumo_config(
    work: Path,
    *,
    net_path: Path,
    routes_path: Path,
    seed: int,
    duration_s: float,
    internal_step_s: float,
) -> Path:
    config_path = work / "simulation.sumocfg"
    config_path.write_text(
        f"""<configuration>
  <input><net-file value="{net_path.name}"/><route-files value="{routes_path.name}"/></input>
  <time><begin value="0"/><end value="{duration_s}"/><step-length value="{internal_step_s}"/></time>
  <processing><time-to-teleport value="-1"/><collision.action value="warn"/></processing>
  <seed value="{seed}"/>
</configuration>
""",
        encoding="utf-8",
        newline="\n",
    )
    return config_path


def _stride_for(*, internal_step_s: float, recorded_step_s: float) -> int:
    if internal_step_s <= 0 or recorded_step_s <= 0:
        raise Stage05EngineeringError("internal and recorded steps must be positive")
    ratio = recorded_step_s / internal_step_s
    stride = int(round(ratio))
    if stride < 1 or abs(ratio - stride) > 1e-9:
        raise Stage05EngineeringError(
            "the recorded observation step must be an exact multiple of the internal simulation step"
        )
    return stride


# --------------------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------------------


def run_stage_0_5_no_message_baseline(
    *,
    output_dir: str | Path,
    fixture_id: str = "baseline_mixed_demand",
    scenario_id: str = "us101_highway_baseline",
    seed: int = 20260907,
    duration_s: float = 40.0,
    internal_step_s: float = 0.1,
    recorded_observation_step_s: float = FORMAL_OBSERVATION_STEP_S,
    warmup_s: float = 0.0,
    run_id: str | None = None,
    guard: CalibrationValidationGuard | None = None,
) -> Path:
    """Run one small, deterministic ``no_message_baseline`` engineering fixture."""

    if scenario_id != "us101_highway_baseline":
        raise Stage05EngineeringError(
            "only us101_highway_baseline has an engineering fixture in Stage 0.5.3;"
            " lankershim_urban_auxiliary and pneuma_urban_kinematics remain candidate_entry_only"
        )
    if duration_s <= 0 or warmup_s < 0 or warmup_s >= duration_s:
        raise Stage05EngineeringError("duration and warm-up window are invalid")
    stride = _stride_for(internal_step_s=internal_step_s, recorded_step_s=recorded_observation_step_s)
    fixture = engineering_fixture(fixture_id, seed=seed, duration_s=duration_s)
    guard = guard or CalibrationValidationGuard()
    output = Path(output_dir).resolve()
    if output.exists():
        raise Stage05EngineeringError(f"refusing to overwrite engineering package: {output}")
    output.mkdir(parents=True, exist_ok=False)
    run_id = run_id or f"stage_0_5_no_message_{fixture_id}_{seed}"

    environment = sumo_environment()
    network = build_candidate_network(output)
    routes_path = _write_route_file(output, fixture, route_spec=NETWORK_DESIGN_CANDIDATE["routes"])
    config_path = _write_sumo_config(
        output,
        net_path=network["network"],
        routes_path=routes_path,
        seed=seed,
        duration_s=duration_s,
        internal_step_s=internal_step_s,
    )

    vehicle_type_mapping = vehicle_type_mapping_candidate()
    validate_vehicle_type_mapping(vehicle_type_mapping)
    demand = {
        "schema_version": f"{SCHEMA_ROOT}.demand.v1",
        "mode": "explicit_departures_fixture",
        "demand_status": "engineering_fixture_only",
        "derived_from": [],
        "vehicle_count": len(fixture["vehicles"]),
        "depart_interval_s": 3.0,
        "lane_composition": {"main_0": 3, "main_1": 3, "main_2": 3, "onramp": 1, "offramp": 1},
        "vehicle_type_mix": {"engineering_car": 0.75, "engineering_heavy_fixture": 0.25},
        "seeds": [int(seed)],
        "flow_density_calibration_status": "pending_scientific",
        "fixture_id": fixture_id,
        "fixture_note": "explicit engineering departures; not a calibrated flow, density or lane split",
    }
    validate_demand_config(demand)

    config: dict[str, Any] = {
        "schema_version": f"{SCHEMA_ROOT}.config.v1",
        "result_id": RESULT_ID,
        "scenario_id": scenario_id,
        "scenario_role": SCENARIO_MANIFEST[scenario_id]["role"],
        "fixture_id": fixture_id,
        "fixture": {
            key: value
            for key, value in fixture.items()
            if key in ("purpose", "stimulus", "stimulus_note", "lane_change_enabled", "notes")
        },
        "network_id": NETWORK_DESIGN_CANDIDATE["network_id"],
        "network_classification": NETWORK_DESIGN_CANDIDATE["classification"],
        "network_claim": NETWORK_DESIGN_CANDIDATE["claim"],
        "experiment_mode": "no_message_baseline",
        "communication_enabled": False,
        "source_risk_treatment_enabled": False,
        "information_adoption_enabled": False,
        "configured_seed": int(seed),
        "simulation_seed": int(seed),
        "duration_s": float(duration_s),
        "warmup_s": float(warmup_s),
        "evaluation_window": {"start_s": float(warmup_s), "end_s": float(duration_s)},
        "internal_step_s": float(internal_step_s),
        "recorded_observation_step_s": float(recorded_observation_step_s),
        "observation_decimation_factor": int(stride),
        "time_config_status": "engineering_candidate",
        "units": UNITS,
        "parameter_status": {
            "network": "engineering_fixture_only",
            "demand": "engineering_fixture_only",
            "vtype_mapping": "engineering_fixture_only",
            "driver_behavior": "engineering_fixture_only",
            "time_step": "engineering_fixture_only",
            "warmup_and_evaluation_window": "engineering_fixture_only",
            "scientific_tolerances": "pending_scientific",
            "gate_criteria": "pending_scientific",
        },
        "net_gap_semantics": NET_GAP_SEMANTICS,
        "closing_speed_semantics": CLOSING_SPEED_SEMANTICS,
        "calibration_validation_policy": CALIBRATION_VALIDATION_POLICY,
        "locked_holdout_accessed": False,
        "engineering_only": True,
        "scientific_claim_eligible": False,
        "gate_status": "pending_simulation_sample",
        "stage_0_5_status_for_stage_1_reference": "no_message_baseline_is_not_the_stage_1_zero_zero_cell",
    }
    validate_no_message_config(config)
    validate_parameter_classification(config["parameter_status"])
    for name, fixture_config in CANDIDATE_SCENARIO_CONFIGS.items():
        validate_scenario_candidate_config(fixture_config)
    validate_scenario_manifest()

    _write_json(output / "config.json", config)
    _write_json(output / "scenario_manifest.json", {"schema_version": f"{SCHEMA_ROOT}.scenario-manifest.v1", "scenarios": SCENARIO_MANIFEST, "candidate_scenario_configs": CANDIDATE_SCENARIO_CONFIGS})
    _write_json(output / "network_design_candidate.json", NETWORK_DESIGN_CANDIDATE)
    _write_json(output / "vehicle_type_config.json", vehicle_type_mapping)
    _write_json(output / "demand_config.json", demand)
    _write_json(output / "calibration_validation_policy.json", CALIBRATION_VALIDATION_POLICY)
    _write_json(output / "measurement_support_matrix.json", measurement_support_matrix())
    _write_json(output / "sumo_formal_field_map.json", {"schema_version": f"{SCHEMA_ROOT}.formal-field-map.v1", "fields": SUMO_FORMAL_FIELD_MAP, "equivalence_status": SUMO_FORMAL_EQUIVALENCE_STATUS, "ngsim_only_reasons": {name: "not_applicable_to_simulator_observation" for name in NGSIM_ONLY_MISSING_REASONS}})

    # The guard is exercised on policy only; no restricted source is read here.
    guard.require(role="calibration", sources=CALIBRATION_VALIDATION_POLICY["calibration"], purpose="stage_0_5_3 policy self-check")
    for denied_role, denied_sources in (
        ("calibration", CALIBRATION_VALIDATION_POLICY["temporal_validation"]),
        ("calibration", CALIBRATION_VALIDATION_POLICY["auxiliary"]),
        ("temporal_validation", CALIBRATION_VALIDATION_POLICY["calibration"]),
        ("locked_holdout", CALIBRATION_VALIDATION_POLICY["calibration"]),
    ):
        guard.evaluate(role=denied_role, sources=denied_sources, purpose="stage_0_5_3 denial self-check")

    import traci  # noqa: PLC0415 - lazy import keeps the module importable without SUMO

    tracker = VehicleIdentityTracker(run_id)
    state_rows: list[dict[str, Any]] = []
    gap_residuals: list[float] = []
    xy_residuals: list[float] = []
    started_at = _utc_now()
    sumo_command = [environment["sumo_executable"], "-c", str(config_path), "--seed", str(seed), "--no-step-log", "true"]
    departed_ids: set[str] = set()
    arrived_ids: set[str] = set()
    max_pending = 0
    network_facts: dict[str, Any] = {}
    try:
        traci.start(sumo_command, label=run_id)
        step_index = 0
        while True:
            now = float(traci.simulation.getTime())
            if now >= duration_s - 1e-9:
                break
            traci.simulationStep()
            step_index += 1
            departed_ids.update(traci.simulation.getDepartedIDList())
            arrived_ids.update(traci.simulation.getArrivedIDList())
            max_pending = max(max_pending, len(traci.simulation.getPendingVehicles()))
            now = float(traci.simulation.getTime())
            if step_index % stride != 0:
                continue
            observation_index = step_index // stride
            current = list(traci.vehicle.getIDList())
            tracker.observe(current, time_s=now, observation_index=observation_index)
            recording = warmup_s <= now + 1e-9
            for vehicle_id in sorted(current):
                incarnation = tracker.incarnation_of(vehicle_id)
                leader = traci.vehicle.getLeader(vehicle_id, 1000.0)
                leader_id = leader[0] if leader else None
                leader_incarnation = tracker.incarnation_of(leader_id) if leader_id else None
                leader_speed = float(traci.vehicle.getSpeed(leader_id)) if leader_id else None
                follower_pos = float(traci.vehicle.getLanePosition(vehicle_id))
                follower_lane = traci.vehicle.getLaneID(vehicle_id)
                min_gap = float(traci.vehicle.getMinGap(vehicle_id))
                if leader_id is None:
                    net_gap = None
                    traci_distance = None
                    leader_pos = None
                    leader_length = None
                    leader_lane = None
                    residual = None
                    xy_gap = None
                    xy_residual = None
                else:
                    traci_distance = float(leader[1])
                    net_gap = traci_distance + min_gap
                    leader_pos = float(traci.vehicle.getLanePosition(leader_id))
                    leader_length = float(traci.vehicle.getLength(leader_id))
                    leader_lane = traci.vehicle.getLaneID(leader_id)
                    residual = None
                    xy_gap = None
                    xy_residual = None
                    if leader_lane == follower_lane:
                        residual = net_gap - (leader_pos - leader_length - follower_pos)
                        gap_residuals.append(abs(residual))
                        follower_xy = traci.vehicle.getPosition(vehicle_id)
                        leader_xy = traci.vehicle.getPosition(leader_id)
                        xy_gap = float(
                            np.hypot(follower_xy[0] - leader_xy[0], follower_xy[1] - leader_xy[1]) - leader_length
                        )
                        xy_residual = net_gap - xy_gap
                        xy_residuals.append(abs(xy_residual))
                identity_status = "observed" if leader_id else "not_applicable"
                if recording:
                    position = traci.vehicle.getPosition(vehicle_id)
                    state_rows.append(
                        {
                            "run_id": run_id,
                            "scenario_id": scenario_id,
                            "fixture_id": fixture_id,
                            "experiment_mode": "no_message_baseline",
                            "configured_seed": int(seed),
                            "simulation_step": int(step_index),
                            "observation_index": int(observation_index),
                            "time_s": now,
                            "vehicle_id": vehicle_id,
                            "trajectory_id": incarnation,
                            "incarnation_id": incarnation,
                            "edge_id": traci.vehicle.getRoadID(vehicle_id),
                            "lane_id": follower_lane,
                            "x_m": float(position[0]),
                            "y_m": float(position[1]),
                            "longitudinal_position_m": follower_pos,
                            "speed_mps": float(traci.vehicle.getSpeed(vehicle_id)),
                            "acceleration_mps2": float(traci.vehicle.getAcceleration(vehicle_id)),
                            "vehicle_type": traci.vehicle.getTypeID(vehicle_id),
                            "original_vehicle_type": traci.vehicle.getTypeID(vehicle_id),
                            "vtype_mapping_version": "candidate-v1",
                            "vtype_mapping_status": "engineering_fixture_only",
                            "leader_id": leader_id,
                            "leader_incarnation_id": leader_incarnation,
                            "leader_identity_status": identity_status,
                            "leader_speed_mps": leader_speed,
                            "leader_reference_position_m": leader_pos,
                            "leader_length_m": leader_length,
                            "follower_min_gap_m": min_gap,
                            "leader_traci_distance_m": traci_distance,
                            "net_gap_m": net_gap,
                            "net_gap_crosscheck_residual_m": residual,
                            "net_gap_xy_m": xy_gap,
                            "net_gap_xy_residual_m": xy_residual,
                        }
                    )
        departed = sorted(departed_ids)
        edge_ids = sorted({edge for edge in traci.edge.getIDList() if not edge.startswith(":")})
        network_facts = {
            "source_network_sha256": _sha256_file(Path(network["network"])),
            "normalization_note": (
                "netconvert applies network offset/normalisation, so built lane geometry can differ"
                " from the design-intent node coordinates; audited lane facts come from the built network"
            ),
            "edges": {
                edge: {
                    "lane_count": int(traci.edge.getLaneNumber(edge)),
                    "lane_length_m": [
                        float(traci.lane.getLength(f"{edge}_{index}"))
                        for index in range(traci.edge.getLaneNumber(edge))
                    ],
                    "speed_limit_mps": [
                        float(traci.lane.getMaxSpeed(f"{edge}_{index}"))
                        for index in range(traci.edge.getLaneNumber(edge))
                    ],
                }
                for edge in edge_ids
            },
        }
        runtime = {
            "sumo_time_s": float(traci.simulation.getTime()),
            "simulation_step_length_s": float(traci.simulation.getDeltaT()),
            "configured_vehicles": len(fixture["vehicles"]),
            "departed_vehicles": len(departed),
            "arrived_vehicles": len(arrived_ids),
            "insertion_failures": sorted(
                vehicle.vehicle_id
                for vehicle in fixture["vehicles"]
                if vehicle.vehicle_id not in departed
                and vehicle.depart_s < duration_s - internal_step_s - 1e-9
            ),
            "not_departed_within_window": sorted(
                vehicle.vehicle_id
                for vehicle in fixture["vehicles"]
                if vehicle.vehicle_id not in departed
                and vehicle.depart_s >= duration_s - internal_step_s - 1e-9
            ),
            "max_pending_vehicles": int(max_pending),
            "collisions": int(getattr(traci.simulation, "getCollidingVehiclesNumber", lambda: 0)()),
        }
    finally:
        try:
            traci.close()
        except Exception:  # pragma: no cover - close failures must not hide results
            pass
    tracker.close(time_s=float(duration_s), observation_index=int(round(duration_s / recorded_observation_step_s)))

    raw_states = pd.DataFrame(state_rows)
    if raw_states.empty:
        raise Stage05EngineeringError("no SUMO state was recorded; refusing to emit an empty engineering package")
    cadence = validate_observation_cadence(
        raw_states.loc[raw_states["vehicle_id"].eq(raw_states["vehicle_id"].iloc[0]), "time_s"].tolist(),
        declared_step_s=recorded_observation_step_s,
    )
    measured = compute_sumo_measurements(raw_states)
    events, exposure = build_sumo_p2_events(
        measured, recorded_observation_step_s=recorded_observation_step_s
    )
    exposure["p2_event_count"] = int(len(events))
    exposure["p2_event_rate_per_vehicle_hour"] = (
        float(len(events) / exposure["p2_evaluable_following_vehicle_hours"])
        if exposure["p2_evaluable_following_vehicle_hours"] > 0
        else None
    )
    exposure["rate_formula"] = "p2_event_count / p2_evaluable_following_vehicle_hours"
    exposure["status"] = "pending_measurement_equivalence"
    exposure["formal_rate_eligible"] = False
    exposure["scientific_claim_eligible"] = False

    formal_events, formal_audit = extract_sumo_formal_p2_events(
        measured, recorded_observation_step_s=recorded_observation_step_s, allow_nonstandard_cadence=True
    )

    canonical = to_canonical_real_state(measured)
    from .calibration import validate_real_state_table  # noqa: PLC0415 - keeps import cost local

    validate_real_state_table(canonical)

    measured.to_parquet(output / "state.parquet", index=False)
    canonical.to_parquet(output / "state_canonical_projection.parquet", index=False)
    measured.loc[measured["leader_observed"]].to_parquet(output / "leader_following_observations.parquet", index=False)
    pd.DataFrame(tracker.events).to_parquet(output / "vehicle_lifecycle.parquet", index=False)
    events.to_parquet(output / "p2_engineering_events.parquet", index=False)
    formal_events.to_parquet(output / "p2_formal_alignment_events.parquet", index=False)
    _write_json(output / "p2_exposure_summary.json", exposure)
    _write_json(output / "formal_adapter_audit.json", formal_audit)
    _write_json(
        output / "measurement_status_summary.json",
        {
            "schema_version": f"{SCHEMA_ROOT}.measurement-status-summary.v1",
            "measurement_status_counts": {
                str(key): int(value) for key, value in measured["measurement_status"].value_counts().items()
            },
            "missing_reason_counts": {
                str(key): int(value) for key, value in measured["missing_reason"].value_counts().items()
            },
            "following_status_counts": {
                str(key): int(value) for key, value in measured["following_status"].value_counts().items()
            },
            "ngsim_only_reasons_not_applicable_to_simulator_observation": list(NGSIM_ONLY_MISSING_REASONS),
            "simulator_observation_defect_rows": int(
                measured["missing_reason"].eq("simulator_output_missing").sum()
            ),
            "traffic_state_not_evaluable_rows": int(
                measured["missing_reason"].isin(["no_observed_leader", "non_closing", "non_positive_net_gap"]).sum()
            ),
            "identity_unresolved_rows": int(measured["missing_reason"].eq("leader_identity_unresolved").sum()),
        },
    )
    _write_json(
        output / "runtime_diagnostics.json",
        {
            "schema_version": f"{SCHEMA_ROOT}.runtime-diagnostics.v1",
            "run_id": run_id,
            "fixture_id": fixture_id,
            "seed": int(seed),
            "sumo_command": sumo_command,
            "internal_step_s": float(internal_step_s),
            "recorded_observation_step_s": float(recorded_observation_step_s),
            "observation_decimation_factor": int(stride),
            "observation_cadence_check": cadence,
            "net_gap_crosscheck": {
                "same_lane_pair_count": len(gap_residuals),
                "lane_position_residual_max_abs_m": max(gap_residuals) if gap_residuals else None,
                "xy_gap_residual_max_abs_m": max(xy_residuals) if xy_residuals else None,
                "residual_definition": "net_gap_m minus the independently derived same-lane physical gap",
                "rule": NET_GAP_SEMANTICS["physical_net_gap_rule"],
            },
            "network_facts": network_facts,
            **runtime,
        },
    )
    audit = {
        "schema_version": f"{SCHEMA_ROOT}.audit.v1",
        "result_id": RESULT_ID,
        "created_at_utc": _utc_now(),
        "started_at_utc": started_at,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "fixture_id": fixture_id,
        "experiment_mode": "no_message_baseline",
        "communication_enabled": False,
        "source_risk_treatment_enabled": False,
        "information_adoption_enabled": False,
        "engineering_only": True,
        "scientific_claim_eligible": False,
        "stage_0_5_gate": "pending_simulation_sample",
        "protocol_lock_allowed": False,
        "stage_1_1_allowed": False,
        "real_network_geometry_confirmed": False,
        "scientific_demand_approved": False,
        "vtype_mapping_approved": False,
        "scientific_time_step_frozen": False,
        "warmup_and_evaluation_window_fixed": False,
        "formal_p2_comparability_proven": False,
        "reality_coverage_tolerance_approved": False,
        "independent_validation_performed": False,
        "state_rows": int(len(measured)),
        "vehicle_count": int(measured["vehicle_id"].nunique()),
        "incarnation_count": int(measured["incarnation_id"].nunique()),
        "leader_observed_rows": int(measured["leader_observed"].sum()),
        "ttc_valid_rows": int(measured["ttc_valid"].sum()),
        "p2_engineering_events": int(len(events)),
        "p2_engineering_event_confirm_times_s": events["event_confirm_s"].tolist() if not events.empty else [],
        "p2_measurement_equivalence_status": "pending_sumo_adapter_review",
        "formal_adapter_equivalence_status": formal_audit["equivalence_status"],
        "formal_adapter_reliable_candidate_events": formal_audit["reliable_candidate_events"],
        "environment": environment,
        "seed": int(seed),
        "parameter_status": config["parameter_status"],
        "runtime_diagnostics": runtime,
        "network_facts": network_facts,
        "measurement_support": measurement_support_matrix()["items"],
    }
    _write_json(output / "audit.json", audit)
    _write_json(output / "access_audit.json", guard.audit())
    _write_json(
        output / "provenance.json",
        {
            "schema_version": f"{SCHEMA_ROOT}.provenance.v1",
            "result_id": RESULT_ID,
            "created_at_utc": _utc_now(),
            "no_message": True,
            "locked_holdout_accessed": False,
            "validation_window_read": False,
            "engineering_only": True,
            "scientific_claim_eligible": False,
            "code_sha256": {
                "code/src/riskprop/stage_0_5_sumo.py": _sha256_file(Path(__file__).resolve()),
                "code/src/riskprop/formal_risk_measurement.py": _sha256_file(
                    Path(__file__).resolve().with_name("formal_risk_measurement.py")
                ),
                "code/scripts/run_stage_0_5_sumo_baseline.py": _sha256_file(
                    Path(__file__).resolve().parents[2] / "scripts" / "run_stage_0_5_sumo_baseline.py"
                ),
                "code/configs/stage_0_5_sumo_engineering_v1.json": _sha256_file(
                    Path(__file__).resolve().parents[2] / "configs" / "stage_0_5_sumo_engineering_v1.json"
                ),
            },
            "sumo_executable_sha256": environment["sumo_executable_sha256"],
            "netconvert_executable_sha256": environment["netconvert_executable_sha256"],
        },
    )
    _seal_engineering_package(output)
    return output


def _seal_engineering_package(output: Path) -> dict[str, Any]:
    files = sorted(
        path for path in output.iterdir()
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
    manifest = {
        "schema_version": f"{SCHEMA_ROOT}.manifest.v1",
        "result_id": RESULT_ID,
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}
            for path in files
        ],
    }
    _write_json(output / "manifest.json", manifest)
    files.append(output / "manifest.json")
    (output / "SHA256SUMS").write_text(
        "\n".join(f"{_sha256_file(path)}  {path.name}" for path in files) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest
