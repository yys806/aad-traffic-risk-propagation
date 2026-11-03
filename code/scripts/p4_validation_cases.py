"""SYNTHETIC_VALIDATION_ONLY. No traffic experiment, calibration or simulator."""
from copy import deepcopy
import math

from riskprop.formal_risk_measurement import P2_FORMAL_CONFIG
from riskprop.p4_measurement_contract import sha256_json

SOURCE = {"purpose": "SYNTHETIC_VALIDATION_ONLY", "cadence_s": 1,
    "window_s": [0, 3], "preassignment_population": ["m1", "m2", "m3"],
    "scope": "synthetic region, not a scientific boundary"}


def inputs(*, partial=True):
    p = [{"provenance_id": "synthetic", "source_ref": "synthetic_source.json",
        "source_sha256": sha256_json(SOURCE), "derivation_version": "synthetic-fixture.v1"}]
    s = dict(support_id="support", run_id="run", assignment_id="assignment", event_id="event",
        unit_id="randomization-unit", reference_clock_id="simulation", region_id="region",
        region_version="synthetic-only.v1", window_version="synthetic-only.v1",
        coordinate_system="synthetic-lane-m", window_start_s=0., window_end_s=3.,
        assignment_time_lower_s=0., scope_frozen_time_upper_s=-1., scope_provenance_id="synthetic",
        provenance_id="synthetic", usage="SYNTHETIC_VALIDATION_ONLY",
        cadence={"step_s": 1., "frame_delta": 1, "provenance_id": "synthetic"},
        source_quality={"source_type": "SYNTHETIC_VALIDATION_ONLY", "qc_version": "fixture.v1",
            "native_no_leader_proof": True, "provenance_id": "synthetic"})
    roster = {k: s[k] for k in ("support_id", "run_id", "assignment_id", "event_id", "region_id", "region_version")}
    roster.update(expected_N=3, complete_population=True, frozen_time_upper_s=-1.,
        eligibility_rule="exact synthetic demand roles", eligibility_version="fixture.v1", roster_version="fixture.v1",
        provenance_id="synthetic", completeness_provenance_id="synthetic", members=[
            {"member_id": "m"+str(i), "role_id": "role"+str(i), "qualification_provenance_id": "synthetic",
             "bindings": [{"vehicle_id": "v"+str(i), "incarnation_id": "v"+str(i)+"@1", "provenance_id": "synthetic"}]} for i in range(1,4)])
    states = []
    for i in (1,2,3):
        if partial and i == 3:
            continue
        times = (0,1,3) if partial and i == 2 else (0,1,2,3)
        ttc = P2_FORMAL_CONFIG.tau_s * math.log(2 if i != 2 else 4)
        previous = None
        for t in times:
            key = "v"+str(i)+":"+str(t)
            row = {k: s[k] for k in ("support_id", "run_id", "assignment_id", "event_id", "region_id", "region_version", "coordinate_system")}
            row.update(state_id=key, member_id="m"+str(i), vehicle_id="v"+str(i), incarnation_id="v"+str(i)+"@1",
                clock_id="simulation", time_s=float(t), time_error_s=0., phase="ACTUAL_READBACK",
                observation_basis="SYNTHETIC_VALIDATION_ONLY", source_type="SYNTHETIC_VALIDATION_ONLY",
                qc_version="fixture.v1", lifecycle_status="PRESENT", identity_reliable=True,
                measurement_reliable=True, kinematics_reliable=True, measurement_status="valid", measurement_reason="",
                speed_mps=11., acceleration_mps2=0., lane_position_m=10.+11*t, lane_id="lane",
                leader_vehicle_id="leader", leader_incarnation_id="leader@1", leader_speed_mps=10.,
                leader_observability="OBSERVED_RELIABLE", leader_identity_reliable=True,
                net_gap_m=ttc, ttc_s=ttc, drac_mps2=1/(2*ttc),
                region_membership="INSIDE", region_reliable=True, membership_provenance_id="synthetic",
                region_link_status="PROVEN_SAME_MEMBERSHIP", region_interval_provenance_id="synthetic",
                previous_state_id=previous, observation_gap=False, identity_break=False,
                source_scope=dict(dataset="synthetic", site="fixture", window_id="synthetic-window",
                    source_member="fixture", source_period="synthetic"),
                diagnostic_clock_anchor_ms=0, global_time_ms=t*1000, frame_id=t,
                provenance_id="synthetic", readback_ref="synthetic_source.json#"+key)
            states.append(row)
            previous = key
    return s, roster, states, p


def associations(states):
    return [{"state_id": s["state_id"], "command_status": "NATIVE_NO_COMMAND", "provenance_id": "synthetic",
        "native_evidence_ref": s["readback_ref"]} for s in states]


def paired_inputs():
    s, roster, base, p = inputs(partial=False)
    base = [x for x in base if x["member_id"] == "m1"]
    treat = deepcopy(base)
    for x in treat:
        x.update(run_id="treatment", assignment_id="treat-assignment", state_id="treat:"+x["state_id"],
            vehicle_id="different-ID", incarnation_id="different-ID@1",
            previous_state_id="treat:"+x["previous_state_id"] if x["previous_state_id"] else None)
    spec = dict(run_id="run", assignment_id="assignment", event_id="event", clock_id="simulation",
        reference_clock_id="simulation", mapping_version="identity.v1", phase="ACTUAL_READBACK",
        offset_s=0., error_s=0., assignment_time_lower_s=0., mapping_provenance_id="synthetic")
    manifest = dict(pair_id="pair", version="fixture.v1", provenance_id="synthetic", sampling_step_s=1.,
        frozen_time_upper_s=-1., baseline=spec, treatment={**spec, "run_id": "treatment", "assignment_id": "treat-assignment"},
        roles=[dict(role_id="role1", baseline=dict(vehicle_id="v1", incarnation_id="v1@1"),
            treatment=dict(vehicle_id="different-ID", incarnation_id="different-ID@1"))])
    return manifest, base, treat, p
