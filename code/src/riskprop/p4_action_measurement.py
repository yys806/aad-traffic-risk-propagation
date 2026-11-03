"""D01/D02: signed real common observations; no interpolation or formal onset."""
from __future__ import annotations

from copy import deepcopy
import math

from .p4_measurement_contract import (evidence_present, finite, provenance_index, require,
    sha256_json, stamp, text, validate_states)


def validate_pair_manifest(manifest, provenance):
    require(text(manifest.get("pair_id")) and text(manifest.get("version")), "INVALID_PAIR", "identity/version")
    require(evidence_present(manifest.get("provenance_id"), provenance), "PAIR_PROVENANCE_MISSING", "pair")
    require(finite(manifest.get("sampling_step_s")) and manifest["sampling_step_s"] > 0,
            "CADENCE_UNPROVEN", "pair cadence")
    roles = manifest.get("roles", [])
    require(roles and len({r.get("role_id") for r in roles}) == len(roles)
            and all(text(r.get("role_id")) for r in roles), "ROLE_MAPPING_MISSING", "unique roles required")
    require(manifest.get("baseline", {}).get("run_id") != manifest.get("treatment", {}).get("run_id"),
            "INVALID_PAIR", "two distinct runs")
    require(manifest.get("baseline", {}).get("event_id") == manifest.get("treatment", {}).get("event_id"),
            "PAIR_EVENT_MISMATCH", "explicit common event required")
    for side in ("baseline", "treatment"):
        spec = manifest.get(side, {})
        require(all(text(spec.get(k)) for k in ("run_id", "assignment_id", "clock_id", "reference_clock_id", "mapping_version", "phase")),
                "INVALID_PAIR", side)
        require(finite(spec.get("offset_s")) and finite(spec.get("error_s")) and spec["error_s"] >= 0
                and evidence_present(spec.get("mapping_provenance_id"), provenance), "CLOCK_MAPPING_UNPROVEN", side)
        require(finite(manifest.get("frozen_time_upper_s")) and finite(spec.get("assignment_time_lower_s"))
                and manifest["frozen_time_upper_s"] < spec["assignment_time_lower_s"], "POST_ASSIGNMENT_PAIR", side)
        bindings = [r.get(side, {}) for r in roles]
        keys = [(b.get("vehicle_id"), b.get("incarnation_id")) for b in bindings]
        require(all(text(v) and text(i) for v, i in keys) and len(set(keys)) == len(keys), "ROLE_MAPPING_MISSING", side)


def compare_actions(manifest, baseline, treatment, provenance):
    p = provenance_index(provenance)
    validate_pair_manifest(manifest, p)
    validate_states(baseline + treatment)
    manifest_hash = sha256_json(manifest)
    outputs, diagnostics, timing = [], [], []
    sides = {"baseline": baseline, "treatment": treatment}
    clocks_compatible = (manifest["baseline"]["reference_clock_id"] == manifest["treatment"]["reference_clock_id"])
    for side, states in sides.items():
        spec = manifest[side]
        for row in states:
            require(all(row.get(k) == spec.get(k) for k in ("run_id", "assignment_id", "event_id")),
                    "CROSS_SCOPE_REFERENCE", row["state_id"])
            require(evidence_present(row.get("provenance_id"), p), "MISSING_STATE_PROVENANCE", row["state_id"])
        mapped = {(r[side]["vehicle_id"], r[side]["incarnation_id"]) for r in manifest["roles"]}
        for row in states:
            if (row["vehicle_id"], row["incarnation_id"]) not in mapped:
                diagnostics.append({"state_id": row["state_id"], "reason": "IDENTITY_NOT_IN_PAIR_MAPPING", "side": side})
    for role in manifest["roles"]:
        lookup = {}
        for side, states in sides.items():
            spec, binding = manifest[side], role[side]
            selected = {}
            for row in states:
                if (row["vehicle_id"], row["incarnation_id"]) != (binding["vehicle_id"], binding["incarnation_id"]):
                    continue
                reason = None
                if row["phase"] != spec["phase"]:
                    reason = "PHASE_NOT_SELECTED"
                elif not clocks_compatible or row["clock_id"] != spec["clock_id"]:
                    reason = "CLOCK_INCOMPATIBLE"
                elif spec["error_s"] != 0 or row["time_error_s"] != 0:
                    reason = "CLOCK_UNCERTAINTY_NO_EXACT_COMMON_SUPPORT"
                elif row.get("identity_reliable") is not True:
                    reason = "IDENTITY_UNRELIABLE"
                elif row.get("kinematics_reliable") is not True:
                    reason = "KINEMATIC_QUALITY_UNPROVEN"
                elif row["lifecycle_status"] != "PRESENT":
                    reason = "VEHICLE_" + row["lifecycle_status"]
                elif not finite(row.get("speed_mps")):
                    reason = "SPEED_MISSING"
                if reason:
                    diagnostics.append({"state_id": row["state_id"], "reason": reason, "side": side, "role_id": role["role_id"]})
                    continue
                t = row["time_s"] + spec["offset_s"]
                require(t not in selected, "AMBIGUOUS_COMMON_TIME", row["state_id"])
                selected[t] = row
            lookup[side] = selected
        common = sorted(set(lookup["baseline"]) & set(lookup["treatment"]))
        for side in lookup:
            for t in set(lookup[side])-set(common):
                diagnostics.append({"state_id": lookup[side][t]["state_id"], "side": side,
                    "role_id": role["role_id"], "reason": "NO_COMMON_OBSERVATION"})
        prior, segment, first_v, first_a = None, 0, None, None
        role_refs = []
        for t in common:
            b, a = lookup["baseline"][t], lookup["treatment"][t]
            breaks = []
            if prior is None:
                breaks.append("OBSERVATION_SEGMENT_START")
            else:
                if not math.isclose(t-prior[0], manifest["sampling_step_s"], rel_tol=0, abs_tol=1e-12):
                    breaks.append("OBSERVATION_GAP")
                for label, now, prev in (("BASELINE", b, prior[1]), ("TREATMENT", a, prior[2])):
                    for field, reason in (("lane_id", "LANE_CHANGE"), ("leader_incarnation_id", "LEADER_SWITCH")):
                        if now.get(field) != prev.get(field):
                            breaks.append(label + "_" + reason)
                    if now.get("observation_gap") is not False or now.get("identity_break") is not False:
                        breaks.append(label + "_CONTINUITY_UNPROVEN")
                    if now.get("previous_state_id") != prev["state_id"]:
                        breaks.append(label + "_EXPLICIT_LINK_MISSING")
                    if not text(now.get("lane_id")) or not text(now.get("leader_incarnation_id")):
                        breaks.append(label + "_INTERACTION_IDENTITY_UNKNOWN")
            if breaks:
                segment += 1
            dv = a["speed_mps"]-b["speed_mps"]
            da = a["acceleration_mps2"]-b["acceleration_mps2"] if finite(a.get("acceleration_mps2")) and finite(b.get("acceleration_mps2")) else None
            if first_v is None and dv != 0:
                first_v = t
            if first_a is None and da is not None and da != 0:
                first_a = t
            key = manifest["pair_id"] + ":" + role["role_id"] + ":" + b["state_id"] + ":" + a["state_id"]
            outputs.append(stamp("action_comparison", {"comparison_id": key, "pair_id": manifest["pair_id"],
                "pair_manifest_sha256": manifest_hash, "role_id": role["role_id"], "time_s": t,
                "baseline_state_id": b["state_id"], "treatment_state_id": a["state_id"],
                "baseline_run_id": b["run_id"], "treatment_run_id": a["run_id"],
                "baseline_assignment_id": b["assignment_id"], "treatment_assignment_id": a["assignment_id"],
                "event_id": b.get("event_id"), "comparison_status": "COMPARABLE_ACTUAL_COMMON_OBSERVATIONS",
                "delta_speed_mps": dv, "absolute_delta_speed_mps": abs(dv),
                "delta_acceleration_mps2": da, "absolute_delta_acceleration_mps2": abs(da) if da is not None else None,
                "acceleration_status": "OBSERVED" if da is not None else "MISSING_AUXILIARY",
                "segment_id": segment, "segment_break_reasons": breaks, "onset_status": "THRESHOLD_UNSET",
                "provenance_id": manifest["provenance_id"]}))
            role_refs.append(key)
            prior = (t, b, a)
        timing.append(stamp("action_timing", {"action_timing_id": manifest["pair_id"] + ":timing:" + role["role_id"],
            "pair_id": manifest["pair_id"], "role_id": role["role_id"], "comparison_refs": role_refs,
            "common_observation_count": len(common), "common_time_start_s": common[0] if common else None,
            "common_time_end_s": common[-1] if common else None,
            "first_observed_nonzero_delta_v_time_s": first_v, "first_observed_nonzero_delta_a_time_s": first_a,
            "nonzero_description_is_scientific_action_change": False,
            "candidate_onset_lower_s": None, "candidate_onset_upper_s": None,
            "persistence_confirmation_time_s": None, "formal_T_U_s": None,
            "onset_status": "THRESHOLD_UNSET", "support_status": "OBSERVED_COMMON_SUPPORT" if common else "UNKNOWN_NO_COMMON_SUPPORT",
            "observation_end_status": "RIGHT_EDGE_NO_EXTENSION", "right_censored_onset": None,
            "provenance_id": manifest["provenance_id"]}))
    return {"schema_version": "aad.p4.measurement.v1", "action_comparisons": outputs, "action_timing": timing,
            "diagnostics": diagnostics, "pair_manifest": deepcopy(manifest), "scientific_claim_eligible": False}
