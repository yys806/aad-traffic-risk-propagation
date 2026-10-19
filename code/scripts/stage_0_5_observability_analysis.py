"""B1.1-S descriptive packaging; does not change frozen measurements or rules."""
from __future__ import annotations

from pathlib import Path
import base64
import gzip
import hashlib
import json
import shutil

RESULT_ID = "RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seal(out):
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json", "SHA256SUMS"])
    large = [p.name for p in files if p.stat().st_size > 256 * 1024]
    if large:
        raise ValueError("portable file size limit: " + str(large))
    write(out / "manifest.json",
          dict(result_id=RESULT_ID, files=[dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in files]))
    files.append(out / "manifest.json")
    (out / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in files), encoding="utf-8", newline="\n")


def finalize(batch):
    import importlib.util
    entry = batch / "runtime/code/scripts/run_stage_0_5_stopping_observability.py"
    spec = importlib.util.spec_from_file_location("b11s_entry", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plan = module.read_plan(batch)
    ledger = read(batch / "execution_ledger.json")
    if not ledger["closed"]:
        raise ValueError("analysis requires a closed observability batch")
    out = batch / "summary"
    out.mkdir(exist_ok=True)
    for name in ["experiment_plan.json", "PLAN_SHA256", "execution_ledger.json", "data_isolation_preflight.json",
                 "official_source_manifest.json", "historical_source_manifest.json", "micro_fixture_manifest.json",
                 "source_staging_manifest.json"]:
        shutil.copyfile(batch / name, out / name)

    # ---- source audit: line locations in the pinned official source ----
    source = read(batch / "official_source_manifest.json")
    needles = {
        "microsim_MSVehicle.cpp": ["MSVehicle::executeMove(", "MSVehicle::updateState(", "MSVehicle::getDeltaPos(",
                                   "MSVehicle::checkActionStep(", "continues with constant accel",
                                   "vSafe = getSpeed() + ACCEL2SPEED(myAcceleration)",
                                   "myAcceleration = SPEED2ACCEL(MAX2", "myState.mySpeed = MAX2(vNext",
                                   "vNext = getCarFollowModel().finalizeSpeed(this, vSafe)",
                                   "MSVehicle::processTraCISpeedControl("],
        "microsim_MSVehicle.h": ["bool isActionStep(SUMOTime t) const", "double getAcceleration() const",
                                 "SUMOTime getLastActionTime() const"],
        "libsumo_Vehicle.cpp": ["Vehicle::getSpeed(", "Vehicle::getAcceleration(", "Vehicle::getLastActionTime("],
        "utils_common_SUMOTime.h": ["#define SPEED2DIST", "#define ACCEL2SPEED", "#define SPEED2ACCEL"],
    }
    locations = {}
    for name, patterns in needles.items():
        text = (batch / "official_source" / name).read_text(encoding="utf-8").splitlines()
        locations[name] = {pat: next((i + 1 for i, line in enumerate(text) if pat in line), None) for pat in patterns}
    write(out / "official_observability_source_audit.json", dict(
        source_files=source, function_line_locations=locations, reported_version="SUMO1.26.0",
        pinned_commit="fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3",
        findings=dict(
            public_speed="myState.mySpeed = max(u,0)",
            public_acceleration="myAcceleration = (max(u,0)-v0)/h ; OVERWRITTEN on action steps, CARRIED on non-action steps",
            non_action_vSafe="vSafe = v0 + myAcceleration*h ; vNext NOT recomputed",
            action_vNext="vNext = finalizeSpeed(...) then clamp/override; hidden signed candidate u",
            action_step_timing="step [t_prev->t_now] is an action step iff getLastActionTime() read at t_now equals t_prev",
            traci_speed_control="inert without vehicle control (myInfluencer None) in free/probe instances",
            decision_stop_identifiability="action step with v1==0 clamps u<=0 to 0; NOT recoverable from public v,a (non-injective)",
            non_action_identifiability="u = v0 + a_pub_start*h exact for ANY sign incl. u<0 within-step stop (verified live)"),
        binary_source_build_equivalence="not rebuilt; installed release label and behaviour checked"))

    # ---- action-step semantics ----
    write(out / "action_step_semantics.json", dict(
        getLastActionTime="myLastActionTime, set to t on each action step; also reset on depart (now+dt) and on actionStepLength change",
        isActionStep="(t - myLastActionTime) % actionStepLength == 0 on the integer-ms grid",
        decision_step="myActionStep true: processLinkApproaches + finalizeSpeed recompute vNext; myAcceleration overwritten",
        non_decision_step="myActionStep false: skips processLinkApproaches/finalizeSpeed; vSafe=v0+myAcceleration*h",
        actionStepLength_vs_internal_step="actionStepLength 0.1s is an integer multiple (2x / 1x) of internal 0.05/0.1s",
        caveat="integer ratio alone does NOT guarantee reconstruction; the clamp on negative u is the decisive limit"))

    # ---- identifiability matrix (prospective classification) ----
    write(out / "stopping_identifiability_matrix.json", dict(
        categories=["Exact Observable", "Exact Reconstructable Under Verified Conditions",
                    "Bounded Consistency Only", "Not Evaluable"],
        matrix=[
            dict(case="action step, v1>0 (no within-step stop)", classification="Exact Observable",
                 method="u = v1 (no clamp triggered)", limits="none in free/probe instances"),
            dict(case="action step, v1==0 (within-step or step-end stop)", classification="Bounded Consistency Only",
                 method="0 <= dx <= v0*h/2", limits="public a_pub clamps u<=0 to 0; cannot recover exact u"),
            dict(case="non-action step (any motion, incl. u<0 within-step stop)",
                 classification="Exact Reconstructable Under Verified Conditions",
                 method="u = v0 + a_pub_start*h; dx from official getDeltaPos formula",
                 limits="requires myInfluencer None and verified action grid"),
            dict(case="rest-to-rest (v0==v1==0)", classification="Exact Observable",
                 method="dx == 0 exactly regardless of hidden u", limits="none"),
            dict(case="edge/lane transition or identity/clock discontinuity", classification="Not Evaluable",
                 method="none", limits="no local lanePosition subtraction across discontinuity"),
            dict(case="vehicle under TraCI speed control", classification="Not Evaluable",
                 method="none", limits="processTraCISpeedControl may override vNext; excluded from instances"),
        ],
        displacement_back_inference="FORBIDDEN (circular)"))

    # ---- per-run aggregates ----
    runs = []
    total = dict(edges=0, exact_checked=0, exact_passed=0, bounded=0, not_evaluable=0, anomalies=0)
    max_resid = None
    for run in ledger["runs"]:
        path = batch / "runs" / run["run_id"] / "summary.json"
        if not path.exists():
            runs.append(dict(execution=run, measurement=None))
            continue
        s = read(path)
        runs.append(dict(execution=run, measurement=s))
        total["edges"] += s["edges"]
        total["exact_checked"] += s["exact_checked"]
        total["exact_passed"] += s["exact_passed"]
        total["bounded"] += s["bounded_consistency_only"]
        total["not_evaluable"] += s["not_evaluable"]
        total["anomalies"] += s["anomalies"]
        if s["max_abs_residual_m"] is not None:
            max_resid = s["max_abs_residual_m"] if max_resid is None else max(max_resid, s["max_abs_residual_m"])
    exact_fraction = (total["exact_checked"] / total["edges"]) if total["edges"] else None
    write(out / "independent_observation_audit.json", dict(
        runs=runs, totals=total, max_abs_residual_m=max_resid,
        exact_applicable_fraction=exact_fraction,
        exact_pass_fraction_of_applicable=(total["exact_passed"] / total["exact_checked"]) if total["exact_checked"] else None,
        note="exact-pass fraction is reported ONLY over exact-applicable edges, never over all edges",
        decision_stop_edges_bounded_only=total["bounded"],
        all_active_vehicle_edges_screened=True, displacement_back_inference_used=False,
        no_debug_binary=True, tolerance_m=1e-6))

    write(out / "debug_feasibility_audit.json", dict(
        official_debug_output_for_signed_vnext=False,
        official_param_or_log_sufficient=False,
        instrumentation_required_for_general_decision_stop=True,
        recompile_cost="high (full SUMO build); not justified for B1.1-S budget",
        status="Not Attempted",
        reason="public interface already yields exact reconstruction for non-action steps; "
               "decision-step stops are bounded and rare; a debug build is deferred as a separate authorised task"))
    write(out / "non_intrusiveness_audit.json", dict(
        debug_binary_used=False, official_binary_unmodified=True, control_runs=0,
        status="Not Applicable (no instrumentation used)",
        statement="no modified SUMO build was created or compared; vehicle behaviour untouched"))

    # ---- numerical admission options (A/B) ----
    write(out / "numerical_admission_options.json", dict(
        option_A=dict(name="strict exact admission",
                      requirement="every observed stopping edge exactly reconstructable",
                      pros="strongest numerical evidence; cleanly separates numeric vs physics",
                      cons="needs debug output for decision-step stops; extra engineering dependency; "
                           "not portable across environments",
                      feasible_now=False),
        option_B=dict(name="tiered admission",
                      requirement="exact for normal/non-action; bounded for decision-stop; not-evaluable for discontinuity; "
                                  "pre-declared anomaly stop rule",
                      pros="preserves observational uncertainty explicitly; unblocks B1.2 engineering; "
                           "no hidden circular inference",
                      cons="cannot claim all stopping edges exactly equivalent; needs pre-approved "
                           "non-evaluable fraction and stop policy; insufficient if conclusions are "
                           "sensitive to exact stopping displacement"),
        recommendation="Option B is the defensible engineering path IF the researcher pre-approves the "
                       "bounded/not-evaluable policy; Option A remains available as a separately authorised "
                       "debug-instrumentation task. Codex does NOT approve Option B unilaterally.",
        researcher_decision_required=True))

    # ---- future B1.2 preconditions ----
    write(out / "future_b1_2_preconditions.json", dict(
        numerical_stopping=dict(non_action_exact=True, decision_stop_exact=False, decision_stop_bounded=True,
                                status="Pending Researcher Admission Policy"),
        queue_contract="B1.1 candidate software tested; thresholds still require scientific approval",
        data_isolation="scoped Python capsule; not complete OS monitoring",
        B1_2_authorized=False,
        not_automatically_started=["B1.2", "formal0.5.4-B", "Stage0.5.5", "Protocol Lock", "StageI/II"]))

    # ---- historical preservation (recompute from sealed B1.1 metadata) ----
    history_manifest = read(batch / "historical_source_manifest.json")
    for name, entry in history_manifest.items():
        if sha(batch / "inputs/history" / name) != entry["sha256"]:
            raise ValueError("historical B1.1 summary changed")
    b11_hint = read(batch / "inputs/history" / "future_experiment_preconditions.json")
    write(out / "historical_status_preservation.json", dict(
        b11_future_preconditions_sha256=history_manifest["future_experiment_preconditions.json"]["sha256"],
        b11_exact_stopping_status=b11_hint["numerical_ready"]["status"],
        historical_C="completed_with_engineering_blocker (preserved, from B1; not re-read)",
        historical_D="not_attempted (preserved)",
        B0_task_data_isolation_accepted=False,
        B0_validation_window_rows_materialised="Unknown",
        historical_reclassification=False, old_C_state_read=False, old_B1_evidence_overwritten=False))

    # ---- audit / provenance / test record ----
    pre = read(batch / "preflight.json")
    logs = [read(p) for p in sorted(batch.glob("test_*.json"))]
    write(out / "test_record.json", dict(preflight=pre, all_preflight_attempts=logs,
        audited_tests=["test_stage_0_5_stopping_observability.py", "test_stage_0_5_stopping_contract.py",
                       "test_stage_0_5_boundary_bottleneck.py"],
        tests_scope="synthetic fixtures + B1 named metadata + approved code only; no real traffic data",
        root_full_pytest_run=False, full_regression="Pending pure Git clone",
        data_related_skips_not_passes=True))
    write(out / "audit.json", dict(result_id=RESULT_ID, mode="public_interface_observability_only",
        stage_0_5_gate="pending_simulation_sample", scientific_claim_eligible=False,
        ready_to_start_stage_0_5_4b=False, reality_coverage_accepted=False, protocol_lock_allowed=False,
        stage_1_1_allowed=False, tolerances="Tolerance Not Yet Justified",
        energy_distance_upper_bound="Not Identifiable", local_P2_status="Unresolved",
        historical_C="completed_with_engineering_blocker", historical_D="not_attempted",
        historical_B1_B11_overwritten=False, B0_task_data_isolation_accepted=False,
        B0_validation_window_rows_materialised="Unknown", no_real_data_inputs=True, old_C_states_read=False,
        raw_NGSIM_read=False, formal_P2_changed=False, debug_binary_used=False,
        micro_runs_attempted=sum(1 for r in ledger["runs"] if r["status"] != "not_attempted"),
        maximum_micro_runs=plan["limits"]["max_runs"], maximum_duration_s=plan["limits"]["per_run_duration_s"],
        old_B1_C_rerun=False, old_D_run=False, B1_second_seed_run=False, B1_2_run=False,
        formal_calibration_run=False))
    write(out / "provenance.json", dict(result_id=RESULT_ID,
        base_commit=read(batch / "preparation_manifest.json")["base_commit"],
        plan_sha256=sha(batch / "experiment_plan.json"),
        executed_source_and_input_sha256=plan["frozen_files"],
        external_code_sources=source, analysis_source_sha256=sha(Path(__file__)),
        historical_metadata_only=history_manifest, no_old_C_detail_access_after_freeze=True,
        b11_git_tree=read(batch / "preparation_manifest.json")["b11_git_tree"]))
    bundle = {}
    for name, digest in plan["frozen_files"].items():
        if name.startswith("inputs/") and Path(name).suffix in [".xml", ".sumocfg"]:
            raw = (batch / name).read_bytes()
            bundle[name] = dict(sha256=digest, bytes=len(raw),
                                gzip_base64=base64.b64encode(gzip.compress(raw, mtime=0)).decode())
    write(out / "micro_input_bundle.json", dict(files=bundle,
        encoding="exact gzip+base64 engineering XML bytes; no raw states or real data"))
    accesses = [dict(entry=p.name, **read(p)) for p in sorted((batch / "access_logs").glob("*.json"))]
    write(out / "controlled_access_audit.json", dict(entries=accesses,
        unexpected_denials=sum(len(a["denied"]) for a in accesses), expected_synthetic_path_denials=3,
        os_native_complete_monitoring=False))
    seal(out)
    print(json.dumps(dict(total_edges=total["edges"], exact_checked=total["exact_checked"],
                          exact_passed=total["exact_passed"], bounded=total["bounded"],
                          not_evaluable=total["not_evaluable"], anomalies=total["anomalies"],
                          max_abs_residual_m=max_resid)), flush=True)
