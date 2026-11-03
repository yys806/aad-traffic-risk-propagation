"""P4 offline deterministic acceptance. SYNTHETIC_VALIDATION_ONLY; no launches."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p4_validation_cases import associations, inputs, paired_inputs
from riskprop.p4_action_measurement import compare_actions
from riskprop.p4_evidence_bridge import link_p3_state, native_state_bridge, link_risk_actions
from riskprop.p4_measurement_bundle import build_bundle, validate_bundle, assignment_result
from riskprop.p4_measurement_contract import P4InputError, provenance_index, sha256_json, stamp
from riskprop.p4_regional_risk import RegionalEligibilityRoster, RegionalRiskAssembler, measure_vehicle_state, validated_ttc_exposure


def test_three_member_independent_expected_interval():
    s,r,x,p = inputs()
    a = RegionalRiskAssembler(s,r,p).measure(x)
    assert len(a["vehicle_windows"]) == 3
    assert a["outcome"]["expected_N"] == 3
    assert a["outcome"]["lower_outcome"] == pytest.approx(7/36)
    assert a["outcome"]["upper_outcome"] == pytest.approx(3/4)
    w1,w2,w3 = a["vehicle_windows"]
    assert (w1["lower_integral"], w1["upper_integral"]) == pytest.approx((1.5,1.5))
    assert (w2["lower_integral"], w2["upper_integral"]) == pytest.approx((.25,2.25))
    assert (w3["lower_mean"], w3["upper_mean"]) == (0,1)
    assert w3["coverage_status"] == "FULLY_UNOBSERVED"


def test_point_complete_population():
    s,r,x,p = inputs(partial=False)
    o = RegionalRiskAssembler(s,r,p).measure(x)["outcome"]
    assert o["outcome_status"] == "POINT_IDENTIFIED"
    assert o["lower_outcome"] == pytest.approx(5/12)


@pytest.mark.parametrize("field,value", [("complete_population", False), ("eligibility_rule", None),
    ("completeness_provenance_id", None), ("provenance_id", None), ("frozen_time_upper_s", 0.),
    ("frozen_time_upper_s", 1.), ("roster_version", None)])
def test_unproven_roster_is_unknown_not_numeric(field,value):
    s,r,x,p = inputs()
    r[field] = value
    out = RegionalRiskAssembler(s,r,p).measure(x)
    assert len(out["vehicle_windows"]) == 3
    assert out["outcome"]["outcome_status"] == "UNKNOWN_SCOPE"
    assert out["outcome"]["lower_outcome"] is None


@pytest.mark.parametrize("mode", ["duplicate", "count", "empty", "duplicate_role", "duplicate_binding"])
def test_bad_predefined_roster_rejected(mode):
    s,r,x,p = inputs()
    if mode == "duplicate": r["members"].append(deepcopy(r["members"][0]))
    if mode == "count": r["expected_N"] = 4
    if mode == "empty": r["members"] = []
    if mode == "duplicate_role": r["members"][1]["role_id"] = "role1"
    if mode == "duplicate_binding": r["members"][1]["bindings"] = deepcopy(r["members"][0]["bindings"])
    with pytest.raises(P4InputError): RegionalEligibilityRoster(r)


@pytest.mark.parametrize("mode", ["extra", "wrong_same_N", "wrong_binding", "cross_run", "duplicate_time"])
def test_bad_state_membership_rejected(mode):
    s,r,x,p = inputs()
    if mode in ("extra", "wrong_same_N"): x[0]["member_id"] = "impostor"
    if mode == "wrong_binding": x[0]["vehicle_id"] = "impostor"
    if mode == "cross_run": x[0]["run_id"] = "other"
    if mode == "duplicate_time":
        extra = deepcopy(x[0]); extra["state_id"] = "duplicate"; x.append(extra)
    with pytest.raises(P4InputError): RegionalRiskAssembler(s,r,p).measure(x)


def test_aggregate_missing_duplicate_same_N_and_wrong_support():
    s,r,x,p = inputs()
    a = RegionalRiskAssembler(s,r,p)
    ws,_,_ = a.vehicle_windows(x)
    assert a.aggregate(ws[:-1])["outcome_status"] == "INCOMPLETE_ROSTER"
    for field,value in (("member_id","impostor"), ("window_version","other"), ("region_version","other"),
            ("window_end_s",4.), ("run_id","other"), ("fixed_window_s",2.), ("known_time_s",-1.),
            ("lower_mean",-1.), ("lower_integral",100.)):
        bad = deepcopy(ws); bad[0] = stamp("vehicle_window", {**bad[0],field:value})
        with pytest.raises(P4InputError): a.aggregate(bad)
    with pytest.raises(P4InputError): a.aggregate(ws+[ws[0]])


@pytest.mark.parametrize("ttc", [float("nan"), float("inf"), -1., 0., None])
def test_bad_valid_ttc_cannot_be_zero_risk(ttc):
    s,r,x,p = inputs(); x[0]["ttc_s"] = ttc
    risk = measure_vehicle_state(x[0],s,provenance_index(p))
    assert risk["measurement_status"] == "invalid"
    assert risk["ttc_s"] is None and risk["rho"] is None
    assert (risk["lower_contribution"],risk["upper_contribution"]) == (0,1)
    json.dumps(risk, allow_nan=False)


@pytest.mark.parametrize("mode", ["missing", "invalid", "unobserved_leader", "identity_unknown", "leader_unknown",
    "region_unknown", "region_unreliable", "position_wrong_version", "source_pneuma", "exited"])
def test_quality_states_preserve_unknown(mode):
    s,r,x,p = inputs(); state = x[0]
    if mode in ("missing","invalid"): state["measurement_status"] = mode
    if mode == "unobserved_leader": state.update(measurement_status="not_applicable",leader_observability="UNOBSERVED")
    if mode == "identity_unknown": state["identity_reliable"] = False
    if mode == "leader_unknown": state["leader_identity_reliable"] = False
    if mode == "region_unknown": state["region_membership"] = "UNKNOWN"
    if mode == "region_unreliable": state["region_reliable"] = False
    if mode == "position_wrong_version": state["region_version"] = "other"
    if mode == "source_pneuma": state["source_type"] = "pNEUMA"
    if mode == "exited": state["lifecycle_status"] = "EXITED"
    risk = measure_vehicle_state(state,s,provenance_index(p))
    assert (risk["lower_contribution"], risk["upper_contribution"]) == (0,1)


@pytest.mark.parametrize("mode", ["outside", "nonclosing", "proven_native_none"])
def test_only_reliable_zero_cases(mode):
    s,r,x,p = inputs(); state = x[0]
    if mode == "outside": state.update(region_membership="OUTSIDE",measurement_status="missing")
    if mode == "nonclosing": state.update(measurement_status="not_applicable",leader_speed_mps=12.)
    if mode == "proven_native_none": state.update(measurement_status="not_applicable",leader_observability="PROVEN_NONE",no_leader_provenance_id="synthetic")
    risk = measure_vehicle_state(state,s,provenance_index(p))
    assert (risk["lower_contribution"],risk["upper_contribution"]) == (0,0)


@pytest.mark.parametrize("break_field,value", [("leader_incarnation_id","other"), ("lane_id","other"),
    ("region_membership","OUTSIDE"), ("region_link_status","UNKNOWN"), ("observation_gap",True),
    ("identity_break",True), ("clock_id","other"), ("time_error_s",.01), ("source_scope",{}),
    ("previous_state_id",None)])
def test_no_cross_gap_or_boundary_point_identification(break_field,value):
    s,r,x,p = inputs(partial=False); x[1][break_field]=value
    out = RegionalRiskAssembler(s,r,p).measure(x)
    assert out["vehicle_windows"][0]["unknown_time_s"] > 0


def test_no_extrapolation_prefix_suffix_or_entire_missing():
    s,r,x,p = inputs(partial=False)
    x = [v for v in x if v["member_id"]=="m1" and v["time_s"] in (1.,2.)]
    ws = RegionalRiskAssembler(s,r,p).measure(x)["vehicle_windows"]
    assert ws[0]["known_time_s"] == 1 and ws[0]["unknown_time_s"] == 2
    assert ws[1]["upper_mean"] == ws[2]["upper_mean"] == 1


def test_undefined_window_preserves_member_placeholders():
    s,r,x,p = inputs(); s.update(window_start_s=None,window_end_s=None)
    out=RegionalRiskAssembler(s,r,p).measure(x)
    assert len(out["vehicle_windows"])==3
    assert all(w["lower_mean"] is None for w in out["vehicle_windows"])
    assert out["outcome"]["outcome_status"]=="UNKNOWN_SCOPE"


def test_cadence_must_be_explicit_and_proven():
    s,r,x,p=inputs(); s["cadence"]={}
    with pytest.raises(P4InputError,match="CADENCE"): RegionalRiskAssembler(s,r,p)


@pytest.mark.parametrize("ttc", [float("nan"), float("inf"), -1., 0.])
def test_auxiliary_valid_nan_fails_closed(ttc):
    with pytest.raises(P4InputError): validated_ttc_exposure(pd.DataFrame([dict(time_s=0.,ttc_s=ttc,valid=True)]),threshold_s=2.)


def test_native_derivation_is_pure_offline_existing_formula():
    s,r,x,p=inputs(); x[0]["derive_native_measurement"]=True
    risk=measure_vehicle_state(x[0],s,provenance_index(p))
    assert risk["ttc_s"]==x[0]["net_gap_m"] and risk["rho"]==pytest.approx(.5)


@pytest.mark.parametrize("mode", ["identical","speed","acceleration"])
def test_action_signed_primary_auxiliary_no_threshold(mode):
    m,b,t,p=paired_inputs()
    if mode=="speed": t[1]["speed_mps"]-=1
    if mode=="acceleration": t[1]["acceleration_mps2"]=-2
    out=compare_actions(m,b,t,p)
    assert len(out["action_comparisons"])==4
    assert out["action_comparisons"][1]["delta_speed_mps"]==(-1 if mode=="speed" else 0)
    assert out["action_comparisons"][1]["delta_acceleration_mps2"]==(-2 if mode=="acceleration" else 0)
    assert out["action_timing"][0]["onset_status"]=="THRESHOLD_UNSET"
    assert out["action_timing"][0]["formal_T_U_s"] is None


@pytest.mark.parametrize("mode", ["no_mapping","duplicate_time","wrong_scope","estimated_state"])
def test_action_rejects_invalid_keys_and_mapping(mode):
    m,b,t,p=paired_inputs()
    if mode=="no_mapping": m["roles"]=[]
    if mode=="duplicate_time":
        v=deepcopy(t[0]);v["state_id"]="duplicate";t.append(v)
    if mode=="wrong_scope": t[0]["assignment_id"]="other"
    if mode=="estimated_state": t[0]["observation_basis"]="INTERPOLATED"
    with pytest.raises(P4InputError): compare_actions(m,b,t,p)


@pytest.mark.parametrize("mode", ["wrong_identity","different_clock","clock_error","no_common_time","exit"])
def test_action_unavailable_has_reasons(mode):
    m,b,t,p=paired_inputs()
    for v in t:
        if mode=="wrong_identity": v["vehicle_id"]="impostor"
        if mode=="different_clock": v["clock_id"]="other"
        if mode=="clock_error": v["time_error_s"]=.001
        if mode=="no_common_time": v["time_s"]+=.5
        if mode=="exit": v["lifecycle_status"]="EXITED"
    out=compare_actions(m,b,t,p)
    assert not out["action_comparisons"] and out["diagnostics"]
    assert out["action_timing"][0]["support_status"]=="UNKNOWN_NO_COMMON_SUPPORT"


@pytest.mark.parametrize("mode", ["gap","leader","lane","incarnation","exit","right_censor"])
def test_action_segments_never_extend_last_or_cross_breaks(mode):
    m,b,t,p=paired_inputs()
    if mode=="gap": del t[1]
    if mode=="leader": t[1]["leader_incarnation_id"]="new"
    if mode=="lane": t[1]["lane_id"]="new"
    if mode=="incarnation": t[1]["incarnation_id"]="new"
    if mode=="exit": t[1]["lifecycle_status"]="EXITED"
    if mode=="right_censor": t=t[:2]
    out=compare_actions(m,b,t,p); timing=out["action_timing"][0]
    assert timing["common_time_end_s"]== (1. if mode=="right_censor" else 3.)
    assert timing["persistence_confirmation_time_s"] is None
    if mode!="right_censor": assert max(c["segment_id"] for c in out["action_comparisons"])>1


def test_explicit_clock_mapping_offset_without_interpolation():
    m,b,t,p=paired_inputs();m["treatment"]["offset_s"]=-10.
    for v in t: v["time_s"]+=10.
    assert len(compare_actions(m,b,t,p)["action_comparisons"])==4


def test_bundle_roundtrip_and_native_all_assignments():
    s,r,x,p=inputs();b=build_bundle(s,r,x,p,associations=associations(x))
    assert b["records"]["provenance"][0]["source_derivation_version"]==p[0]["derivation_version"]
    assert validate_bundle(json.loads(json.dumps(b)))["status"]=="VALID_WITH_LIMITATIONS"
    assert assignment_result(b)["independent_unit"]=="ASSIGNMENT_NOT_VEHICLE_OR_SAMPLE"
    for label in ("NO_MESSAGE","DISABLED","MESSAGE_FAILED","NOT_ADOPTED"):
        s["treatment_label"]=label
        out=build_bundle(s,None,x,p,associations=associations(x))
        assert out["records"]["regional_outcome"][0]["outcome_status"]=="UNKNOWN_SCOPE"
        assert out["records"]["regional_outcome"][0]["expected_N"] is None


def test_bundle_tampering_and_foreign_key_rejection():
    s,r,x,p=inputs();b=build_bundle(s,r,x,p,associations=associations(x))
    bad=deepcopy(b);bad["records"]["risk_sample"][0]["rho"]=0
    with pytest.raises(P4InputError): validate_bundle(bad)
    bad=deepcopy(b);bad["records"]["risk_action_bridge"][0]=stamp("risk_action_bridge",{
        **bad["records"]["risk_action_bridge"][0],"bridge_id":"missing"})
    bad["bundle_sha256"]=sha256_json({k:v for k,v in bad.items() if k!="bundle_sha256"})
    with pytest.raises(P4InputError,match="ORPHAN"): validate_bundle(bad)


def test_provenance_real_bytes_required_when_requested(tmp_path):
    s,r,x,p=inputs();b=build_bundle(s,r,x,p,associations=associations(x))
    (tmp_path/"synthetic_source.json").write_text("incorrect",encoding="utf-8")
    with pytest.raises(P4InputError,match="SOURCE_HASH"): validate_bundle(b,artifact_root=tmp_path)


def test_actual_saved_p7_explicit_message_receipt_bridge():
    root=Path(__file__).resolve().parents[2]/"code/outputs/engineering/p7_task2_20261103_v2_revalidation/enabled_v2"
    records=json.loads((root/"controller_evidence.json").read_text(encoding="utf-8"))["records"]
    action=next(r for r in records if r["kind"]=="action_observation" and r["data"]["execution_refs"]
        and r["time"]["time_lower"]>3.)
    c=action["context"];tm=action["time"]
    state=dict(state_id="saved-state",run_id=c["run_id"],assignment_id=c["assignment_id"],support_id="read-only",
        event_id=None,vehicle_id=c["vehicle_id"],incarnation_id=c["vehicle_incarnation_id"],
        readback_ref=action["data"]["observation_ref"],clock_id=tm["reference_clock_id"],time_s=tm["time_lower"],time_error_s=0.)
    # Source event is explicit in the command/consumption records.
    execution=next(r for r in records if r["kind"]=="execution" and r["data"]["execution_id"]==action["data"]["execution_refs"][0])
    command=next(r for r in records if r["kind"]=="command" and r["data"]["command_id"]==execution["data"]["command_id"])
    decision=next(r for r in records if r["kind"]=="decision" and r["data"]["decision_id"]==command["data"]["decision_id"])
    receipt_id=decision["data"]["consumed_message_refs"][0]["consumption_receipt_id"]
    receipt=next(r for r in records if r["kind"]=="consumption" and r["data"]["consumption_receipt_id"]==receipt_id)
    state["event_id"]=receipt["context"]["source_event_id"]
    bridge=link_p3_state(state,action["data"]["action_observation_id"],records,provenance_id="saved-p7")
    assert bridge["command_status"]=="EXPLICIT_COMMAND_CHAIN"
    assert bridge["message_refs"] and bridge["consumption_refs"]
    state["readback_ref"]="nearby-time-is-not-a-reference"
    with pytest.raises(P4InputError,match="READBACK"): link_p3_state(state,action["data"]["action_observation_id"],records,provenance_id="saved-p7")


def test_many_to_many_exact_state_risk_links():
    s,r,x,p=inputs();risk=measure_vehicle_state(x[0],s,provenance_index(p))
    b=native_state_bridge(x[0],provenance_id="synthetic",native_evidence_ref=x[0]["readback_ref"])
    b2=stamp("action_execution_bridge",{**b,"bridge_id":"other-explicit-observation"})
    assert len(link_risk_actions([risk],[b,b2]))==2


def test_action_missing_acceleration_stays_auxiliary_unknown():
    m,b,t,p=paired_inputs();t[0]["acceleration_mps2"]=None
    out=compare_actions(m,b,t,p)["action_comparisons"][0]
    assert out["delta_speed_mps"]==0 and out["delta_acceleration_mps2"] is None
    assert out["acceleration_status"]=="MISSING_AUXILIARY"


def test_action_kinematic_quality_and_event_guard():
    m,b,t,p=paired_inputs()
    for x in t:x["kinematics_reliable"]=False
    assert not compare_actions(m,b,t,p)["action_comparisons"]
    m["treatment"]["event_id"]="different-event"
    with pytest.raises(P4InputError,match="PAIR_EVENT"):compare_actions(m,b,t,p)


@pytest.mark.parametrize("source",["NGSIM","pNEUMA","SPMD"])
def test_source_cannot_assert_native_no_leader_without_capability(source):
    s,r,x,p=inputs();s["source_quality"]["source_type"]=source
    state=x[0];state.update(source_type=source,measurement_status="not_applicable",leader_observability="PROVEN_NONE",no_leader_provenance_id="synthetic")
    risk=measure_vehicle_state(state,s,provenance_index(p))
    assert risk["upper_contribution"]==1


def test_missing_geometry_not_faked_by_inside_label():
    s,r,x,p=inputs();s["coordinate_system"]=None
    risk=measure_vehicle_state(x[0],s,provenance_index(p))
    assert risk["region_reliable"] is False and risk["upper_contribution"]==1


def test_json_nonfinite_blocked_before_serialization():
    with pytest.raises(P4InputError,match="INVALID_JSON"):stamp("state_observation",{"ttc_s":float("nan")})


def test_unknown_scope_still_checks_wrong_run_window():
    s,r,x,p=inputs();r["complete_population"]=False
    a=RegionalRiskAssembler(s,r,p);ws,_,_=a.vehicle_windows(x)
    ws[0]=stamp("vehicle_window",{**ws[0],"run_id":"impostor"})
    with pytest.raises(P4InputError,match="CROSS_SCOPE"):a.aggregate(ws)
