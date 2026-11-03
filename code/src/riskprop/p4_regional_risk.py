"""Fixed pre-assignment eligible population, Formal primitives, explicit bounds.

Region membership and interval evidence are inputs, never interpolated here.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math

import pandas as pd

from .formal_risk_measurement import (P2_FORMAL_CONFIG, contribution_bounds, continuity_is_valid,
    equal_vehicle_average, integrate_fixed_window, rho_from_ttc)
from .p4_measurement_contract import (CONTEXT, P4InputError, evidence_present, finite,
    check_record, provenance_index, require, same_context, scope_defined, sha256_json, stamp, text,
    validate_bounds, validate_states, validate_support)

REGIONAL_VERSION = "aad.p4.fixed-eligible-equal-vehicle-mean.v1"


class RegionalEligibilityRoster:
    """Defensive copy; completeness evidence is never inferred from observations."""
    def __init__(self, manifest):
        self._manifest = deepcopy(manifest)
        members = manifest.get("members", [])
        require(isinstance(members, list) and bool(members), "INCOMPLETE_ROSTER", "no predefined members")
        for field in ("member_id", "role_id"):
            values = [m.get(field) for m in members]
            require(all(text(v) for v in values) and len(set(values)) == len(values), "DUPLICATE_MEMBER", field)
        bindings = [(b.get("vehicle_id"), b.get("incarnation_id")) for m in members for b in m.get("bindings", [])]
        require(all(text(v) and text(i) for v, i in bindings) and len(set(bindings)) == len(bindings),
                "DUPLICATE_BINDING", "vehicle/incarnation")
        if "expected_N" in manifest:
            require(type(manifest["expected_N"]) is int and manifest["expected_N"] == len(members),
                    "INCOMPLETE_ROSTER", "declared N differs from predefined members")
        self.digest = sha256_json(self._manifest)

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @property
    def members(self):
        return deepcopy(self._manifest["members"])

    @property
    def expected_N(self):
        return len(self._manifest["members"])

    def scope_status(self, support, provenance):
        m = self._manifest
        same_context(m, support)
        require(m.get("region_id") == support.get("region_id") and m.get("region_version") == support.get("region_version"),
                "ROSTER_REGION_MISMATCH", "region/version")
        if not scope_defined(support, provenance):
            return "UNKNOWN_SCOPE"
        if (not finite(m.get("frozen_time_upper_s")) or
                m["frozen_time_upper_s"] >= support["assignment_time_lower_s"]):
            return "UNKNOWN_SCOPE"
        known = (m.get("complete_population") is True and text(m.get("eligibility_rule"))
            and text(m.get("eligibility_version")) and text(m.get("roster_version"))
            and evidence_present(m.get("provenance_id"), provenance)
            and evidence_present(m.get("completeness_provenance_id"), provenance)
            and all(evidence_present(x.get("qualification_provenance_id"), provenance) for x in self.members))
        return "COMPLETE_ELIGIBLE_POPULATION" if known else "UNKNOWN_SCOPE"

    def validate_state_bindings(self, states, provenance):
        members = {m["member_id"]: m for m in self.members}
        for state in states:
            mid = state.get("member_id")
            require(mid in members, "EXTRA_OR_WRONG_MEMBER", str(mid))
            bindings = members[mid].get("bindings", [])
            matches = [b for b in bindings if b.get("vehicle_id") == state["vehicle_id"]
                and b.get("incarnation_id") == state["incarnation_id"]]
            require(len(matches) == 1 and evidence_present(matches[0].get("provenance_id"), provenance),
                    "IDENTITY_BINDING_UNPROVEN", state["state_id"])


def measure_vehicle_state(state, support, provenance):
    """Validate source-qualified TTC; optional native derivation uses existing core."""
    require(evidence_present(state.get("provenance_id"), provenance), "MISSING_STATE_PROVENANCE", state["state_id"])
    policy = support.get("source_quality", {})
    source = state.get("source_type")
    qualified = (source in ("SUMO", "NGSIM", "SYNTHETIC_VALIDATION_ONLY")
        and policy.get("source_type") == source and text(policy.get("qc_version"))
        and state.get("qc_version") == policy.get("qc_version")
        and evidence_present(policy.get("provenance_id"), provenance)
        and state.get("measurement_reliable") is True and state.get("identity_reliable") is True)
    status = state.get("measurement_status", "missing")
    reason, ttc, drac = state.get("measurement_reason", "upstream_missing"), state.get("ttc_s"), state.get("drac_mps2")
    observed = (state.get("leader_observability") == "OBSERVED_RELIABLE"
        and state.get("leader_identity_reliable") is True
        and text(state.get("leader_incarnation_id")) and text(state.get("leader_vehicle_id")))
    if state.get("derive_native_measurement") is True:
        require(source in ("SUMO", "SYNTHETIC_VALIDATION_ONLY"), "SOURCE_CAPABILITY_MISMATCH", "native derivation")
        from .stage_0_5_sumo import compute_sumo_measurements
        raw = {**state, "scenario_id": support["support_id"], "experiment_mode": "P4_OFFLINE_MEASUREMENT",
            "configured_seed": None, "trajectory_id": state["incarnation_id"],
            "simulation_step": state.get("frame_id"), "leader_id": state.get("leader_vehicle_id"),
            "leader_identity_status": "observed" if observed else "unresolved"}
        row = compute_sumo_measurements(pd.DataFrame([raw])).iloc[0]
        status, reason = str(row.measurement_status), str(row.missing_reason)
        ttc = float(row.ttc_s) if finite(float(row.ttc_s)) else None
        drac = float(row.drac_mps2) if finite(float(row.drac_mps2)) else None
    if not qualified or state.get("lifecycle_status") != "PRESENT":
        status, reason = "not_measurable", "SOURCE_QC_OR_LIFECYCLE_UNPROVEN"
    elif status == "valid":
        if (not observed or not finite(ttc) or ttc <= 0 or not finite(state.get("net_gap_m"))
                or state["net_gap_m"] <= 0 or not finite(state.get("speed_mps"))
                or not finite(state.get("leader_speed_mps")) or state["speed_mps"] <= state["leader_speed_mps"]):
            status, reason = "invalid", "VALID_TTC_INPUT_INCONSISTENT"
    elif status == "not_applicable":
        nonclosing = (observed and finite(state.get("net_gap_m")) and state["net_gap_m"] > 0
            and finite(state.get("speed_mps")) and finite(state.get("leader_speed_mps"))
            and state["speed_mps"] <= state["leader_speed_mps"])
        proven_none = (source in ("SUMO", "SYNTHETIC_VALIDATION_ONLY")
            and state.get("leader_observability") == "PROVEN_NONE"
            and policy.get("native_no_leader_proof") is True
            and evidence_present(state.get("no_leader_provenance_id"), provenance))
        if not (nonclosing or proven_none):
            status, reason = "missing", "NO_RELIABLE_NOT_APPLICABLE_PROOF"
    elif status not in ("missing", "invalid", "not_measurable"):
        status, reason = "missing", "UNKNOWN_MEASUREMENT_STATUS"
    reliable = qualified and status in ("valid", "not_applicable")
    if status != "valid":
        ttc, drac = None, None
    elif drac is not None and (not finite(drac) or drac < 0):
        drac = None
    member = state.get("region_membership")
    spatial = (all(text(support.get(k)) for k in ("region_id", "region_version", "coordinate_system"))
        and state.get("region_reliable") is True and member in ("INSIDE", "OUTSIDE")
        and state.get("region_id") == support.get("region_id")
        and state.get("region_version") == support.get("region_version")
        and state.get("coordinate_system") == support.get("coordinate_system")
        and evidence_present(state.get("membership_provenance_id"), provenance))
    lo, hi, rho = contribution_bounds(measurement_status=status, in_region=(member == "INSIDE") if spatial else None,
        ttc_s=ttc, region_reliable=spatial, measurement_reliable=reliable)
    # The same frozen Formal mapping; no event threshold truncation.
    require(rho is None or rho == rho_from_ttc(ttc), "FORMAL_MAPPING_MISMATCH", state["state_id"])
    return stamp("risk_sample", {**{k: support.get(k) for k in CONTEXT},
        "risk_sample_id": "risk:" + state["state_id"], "state_id": state["state_id"], "member_id": state["member_id"],
        "time_s": state["time_s"], "incarnation_id": state["incarnation_id"],
        "measurement_status": status, "measurement_reason": reason, "measurement_reliable": reliable,
        "region_membership": member, "region_reliable": spatial, "ttc_s": ttc, "drac_mps2": drac,
        "rho": rho, "lower_contribution": lo, "upper_contribution": hi,
        "measurement_version": P2_FORMAL_CONFIG.algorithm_version, "provenance_id": state["provenance_id"]})


class RegionalRiskAssembler:
    def __init__(self, support, roster, provenance):
        self.provenance = provenance_index(provenance)
        validate_support(support, self.provenance)
        self.support = deepcopy(support)
        self.roster = roster if isinstance(roster, RegionalEligibilityRoster) else RegionalEligibilityRoster(roster)
        self.scope_status = self.roster.scope_status(self.support, self.provenance)

    def vehicle_windows(self, states):
        s = self.support
        validate_states(states, s)
        self.roster.validate_state_bindings(states, self.provenance)
        samples = [measure_vehicle_state(x, s, self.provenance) for x in states]
        by_state = {x["state_id"]: x for x in samples}
        windows, links = [], []
        for member in self.roster.members:
            selected = sorted((x for x in states if x["member_id"] == member["member_id"]), key=lambda x: x["time_s"])
            require(len({x["time_s"] for x in selected}) == len(selected), "AMBIGUOUS_RISK_PHASE", member["member_id"])
            formal = []
            previous = None
            for state in selected:
                risk = by_state[state["state_id"]]
                spatial_link = (previous is not None and state.get("previous_state_id") == previous["state_id"]
                    and state.get("region_link_status") == "PROVEN_SAME_MEMBERSHIP"
                    and state.get("region_membership") == previous.get("region_membership")
                    and risk["region_reliable"] and by_state[previous["state_id"]]["region_reliable"]
                    and evidence_present(state.get("region_interval_provenance_id"), self.provenance)
                    and state.get("lane_id") == previous.get("lane_id"))
                row = {**state.get("source_scope", {}), "trajectory_id": state["incarnation_id"],
                    "leader_trajectory_id": state.get("leader_incarnation_id"),
                    "diagnostic_clock_anchor_ms": state.get("diagnostic_clock_anchor_ms"),
                    "global_time_ms": state.get("global_time_ms"), "frame_id": state.get("frame_id"),
                    "time_s": state["time_s"], "lower": risk["lower_contribution"], "upper": risk["upper_contribution"],
                    "leader_matched": state.get("leader_observability") == "OBSERVED_RELIABLE",
                    "identity_uncertain": state.get("identity_reliable") is not True,
                    "leader_identity_uncertain": state.get("leader_identity_reliable") is not True,
                    "identity_break": state.get("identity_break") is not False,
                    "observation_gap": (not spatial_link or state.get("observation_gap") is not False
                        or state["clock_id"] != s["reference_clock_id"] or state["time_error_s"] != 0
                        or (previous is not None and (previous["clock_id"] != s["reference_clock_id"] or previous["time_error_s"] != 0)))}
                if formal:
                    proven = continuity_is_valid(formal[-1], row, expected_step_s=s["cadence"]["step_s"],
                        expected_frame_delta=s["cadence"]["frame_delta"])
                    links.append({"previous_state_id": previous["state_id"], "state_id": state["state_id"],
                        "status": "PROVEN" if proven else "UNKNOWN_INTERVAL", "spatial_link_proven": spatial_link})
                formal.append(row)
                previous = state
            if s.get("window_start_s") is None:
                windows.append(stamp("vehicle_window", {**{k: s.get(k) for k in CONTEXT},
                    "vehicle_window_id": s["support_id"] + ":window:" + member["member_id"],
                    "member_id": member["member_id"], "bindings": member.get("bindings", []),
                    **{k: s.get(k) for k in ("region_id", "region_version", "window_version", "window_start_s", "window_end_s")},
                    **{k: None for k in ("fixed_window_s", "lower_integral", "upper_integral", "lower_mean", "upper_mean",
                        "known_time_s", "unknown_time_s", "observed_pair_time_s")},
                    "coverage_status": "UNKNOWN_SCOPE", "measurement_status": "UNKNOWN_SCOPE",
                    "risk_sample_refs": [by_state[x["state_id"]]["risk_sample_id"] for x in selected],
                    "roster_sha256": self.roster.digest, "provenance_id": s["provenance_id"]}))
                continue
            result = integrate_fixed_window(pd.DataFrame(formal), window_start_s=s["window_start_s"],
                window_end_s=s["window_end_s"], expected_step_s=s["cadence"]["step_s"],
                expected_frame_delta=s["cadence"]["frame_delta"])
            windows.append(stamp("vehicle_window", {**{k: s.get(k) for k in CONTEXT}, **result,
                "vehicle_window_id": s["support_id"] + ":window:" + member["member_id"], "member_id": member["member_id"],
                "bindings": member.get("bindings", []), "region_id": s.get("region_id"), "region_version": s.get("region_version"),
                "window_version": s.get("window_version"), "window_start_s": s["window_start_s"], "window_end_s": s["window_end_s"],
                "coverage_status": "FULLY_UNOBSERVED" if not selected else "COMPLETE" if result["unknown_time_s"] == 0 else "PARTIAL",
                "measurement_status": "POINT_IDENTIFIED" if result["lower_mean"] == result["upper_mean"] else "INTERVAL_IDENTIFIED",
                "risk_sample_refs": [by_state[x["state_id"]]["risk_sample_id"] for x in selected],
                "roster_sha256": self.roster.digest, "provenance_id": s["provenance_id"]}))
        return windows, samples, links

    def aggregate(self, windows):
        s = self.support
        ids = [w.get("member_id") for w in windows]
        expected = {m["member_id"] for m in self.roster.members}
        require(len(ids) == len(set(ids)), "DUPLICATE_WINDOW_MEMBER", str(ids))
        require(not set(ids) - expected, "EXTRA_OR_WRONG_MEMBER", str(set(ids) - expected))
        base = {**{k: s.get(k) for k in CONTEXT}, "outcome_id": s["support_id"] + ":Y",
            "population_scope": self.scope_status, "unit_id": s.get("unit_id"),
            "region_id": s.get("region_id"), "region_version": s.get("region_version"),
            "window_version": s.get("window_version"), "window_start_s": s.get("window_start_s"), "window_end_s": s.get("window_end_s"),
            "expected_N": self.roster.expected_N, "received_N": len(ids), "unique_N": len(set(ids)),
            "roster_sha256": self.roster.digest, "vehicle_window_refs": [w["vehicle_window_id"] for w in windows],
            "lower_outcome": None, "upper_outcome": None, "outcome_unit": "1",
            "aggregation_version": REGIONAL_VERSION, "usage": s.get("usage", "NOT_FORMAL_PARAMETER_FREEZE"),
            "provenance_id": s["provenance_id"], "scientific_claim_eligible": False,
            "risk_causal_effect": "Unknown", "formal_parameters_fully_frozen": False}
        require(len({w["vehicle_window_id"] for w in windows}) == len(windows), "DUPLICATE_WINDOW_ID", "window IDs")
        for w in windows:
            check_record(w, "vehicle_window")
            same_context(w, s)
            for key in ("region_id", "region_version", "window_version", "window_start_s", "window_end_s"):
                require(w.get(key) == s.get(key), "WINDOW_SUPPORT_MISMATCH", key)
            require(w.get("roster_sha256") == self.roster.digest, "ROSTER_HASH_MISMATCH", w["member_id"])
            if s.get("window_start_s") is None:
                require(w.get("measurement_status") == "UNKNOWN_SCOPE"
                    and all(w.get(k) is None for k in ("fixed_window_s", "lower_mean", "upper_mean", "lower_integral", "upper_integral")),
                    "UNKNOWN_WINDOW_HAS_NUMERIC_RESULT", w["member_id"])
                continue
            validate_bounds(w.get("lower_mean"), w.get("upper_mean"))
            length = s["window_end_s"]-s["window_start_s"]
            require(w.get("fixed_window_s") == length, "WINDOW_DENOMINATOR_MISMATCH", w["member_id"])
            require(all(finite(w.get(k)) and 0 <= w[k] <= length for k in ("known_time_s", "unknown_time_s", "observed_pair_time_s"))
                and math.isclose(w["known_time_s"] + w["unknown_time_s"], length, abs_tol=1e-12)
                and w["known_time_s"] <= w["observed_pair_time_s"] + 1e-12,
                "INCONSISTENT_COVERAGE", w["member_id"])
            for which in ("lower", "upper"):
                require(finite(w.get(which+"_integral")) and math.isclose(w[which+"_integral"]/length, w[which+"_mean"], rel_tol=1e-12, abs_tol=1e-12),
                        "INCONSISTENT_WINDOW_INTEGRAL", w["member_id"])
        if self.scope_status != "COMPLETE_ELIGIBLE_POPULATION":
            return stamp("regional_outcome", {**base, "outcome_status": "UNKNOWN_SCOPE", "missing_summary": {"scope": "unproven"}})
        if set(ids) != expected:
            return stamp("regional_outcome", {**base, "outcome_status": "INCOMPLETE_ROSTER", "missing_summary": {"members": sorted(expected-set(ids))}})
        mean = equal_vehicle_average(windows)
        return stamp("regional_outcome", {**base, "lower_outcome": mean["lower_mean"], "upper_outcome": mean["upper_mean"],
            "outcome_status": "POINT_IDENTIFIED" if mean["lower_mean"] == mean["upper_mean"] else "INTERVAL_IDENTIFIED",
            "missing_summary": dict(Counter(w["coverage_status"] for w in windows))})

    def measure(self, states):
        windows, samples, links = self.vehicle_windows(states)
        return {"vehicle_windows": windows, "risk_samples": samples, "links": links, "outcome": self.aggregate(windows)}


def validated_ttc_exposure(states, *, threshold_s):
    """Optional auxiliary adapter: fail closed on valid/NaN inconsistency."""
    from .prelock_metrics import integrated_ttc_exposure
    for row in states.to_dict("records"):
        require(type(row.get("valid")) is bool, "INVALID_AUXILIARY_VALID_FLAG", "explicit Boolean required")
        if row["valid"]:
            require(finite(row.get("ttc_s")) and row["ttc_s"] > 0, "INVALID_AUXILIARY_TTC", "valid requires finite positive TTC")
    return integrated_ttc_exposure(states, threshold_s=threshold_s)
