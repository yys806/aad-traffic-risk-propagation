"""Close B1.2-N's failed positive-snap admission checkpoint; never runs SUMO."""
import argparse
import base64
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

RESULT_ID="RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1"
REPORT="docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md"

def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json","SHA256SUMS"])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError("portable size limit")
    write(out/"manifest.json",dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]))
    files.append(out/"manifest.json")
    (out/"SHA256SUMS").write_text("".join(f'{sha(p)}  {p.name}\n' for p in files),encoding="utf-8",newline="\n")

def stage(repo,batch):
    plan=read(batch/"micro_plan.json");checkpoint=read(batch/"micro_checkpoint.json")
    if checkpoint["integration_allowed"] or checkpoint["observed_positive_snap"]:raise ValueError("this closure describes missing positive-snap coverage")
    if any((batch/f"integration_{k}_plan.json").exists() for k in ["C","D"]):raise ValueError("unexpected C/D plan")
    task=read(batch/"task_ledger.json")
    if not task["closed"]:
        shutil.copyfile(batch/"task_ledger.json",batch/"task_ledger_before_administrative_closure.json")
        task.update(closed=True,closure_reason="Predeclared positive-snap runtime branch Not Observed; integration admission false; no additional runs")
        write(batch/"task_ledger.json",task)
    out=batch/"summary";out.mkdir(exist_ok=True)
    for name in ["micro_plan.json","micro_checkpoint.json","micro_ledger.json","task_ledger.json","near_zero_source_contract.json",
                 "numerical_admission_candidate.json","integration_preflight.json","execution_scope_audit.json","preparation_manifest.json",
                 "source_staging_manifest.json","engineering_input_lineage.json"]:shutil.copyfile(batch/name,out/name)
    shutil.copyfile(batch/"micro_plan.json",out/"experiment_plan.json")
    (out/"PLAN_SHA256").write_text(sha(out/"experiment_plan.json")+"  experiment_plan.json\n")
    files=[];generated=[];bundle={}
    for name,digest in plan["frozen_files"].items():
        if sha(batch/name)!=digest:raise ValueError("frozen file changed: "+name)
        raw=(batch/name).read_bytes()
        if name.startswith("runtime/code/"):
            relative=name.removeprefix("runtime/")
            if relative in ["code/pytest.ini","code/src/sitecustomize.py","code/src/riskprop/__init__.py"]:
                generated.append(dict(path=name,sha256=digest,base64=base64.b64encode(raw).decode()))
            else:
                canonical=raw.replace(b"\r\n",b"\n");transform="none" if raw==canonical else "canonical LF to original CRLF"
                if transform!="none" and canonical.replace(b"\n",b"\r\n")!=raw:raise ValueError("noncanonical newline")
                files.append(dict(path=relative,frozen_sha256=digest,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),byte_transform=transform))
        if name.startswith("inputs/") and Path(name).suffix in [".xml",".sumocfg"]:
            bundle[name]=dict(bytes=len(raw),sha256=digest,gzip_base64=base64.b64encode(gzip.compress(raw,mtime=0)).decode())
    write(out/"git_source_binding_audit.json",dict(files=files,generated_runtime=generated,source_of_bytes="executed frozen capsule",new_runs_by_analysis=0))
    write(out/"engineering_input_bundle.json",dict(files=bundle,no_traffic_states=True,no_real_trajectories=True))
    shutil.copyfile(repo/REPORT,out/"report.md")
    entry=batch/"analysis_entry.py";shutil.copyfile(Path(__file__).resolve(),entry)
    write(batch/"analysis_source_manifest.json",dict(source="code/scripts/finalize_stage_0_5_near_zero_integration.py",sha256=sha(entry),report_sha256=sha(repo/REPORT)))
    return subprocess.call([sys.executable,"-S",str(entry),str(batch),"--render"])

def render(batch):
    sys.path.insert(0,str(batch/"runtime/code/src"))
    from riskprop.stage_0_5_b1_isolation import install_guard
    guard=install_guard(batch)
    try:
        from riskprop.stage_0_5_b12_runtime import environment,SCIENCE,FIXED
        environment(batch)
        import pandas as pd
        out=batch/"summary";plan=read(out/"experiment_plan.json");task=read(out/"task_ledger.json")
        summaries={k:read(batch/"runs"/("b12n_"+k)/"summary.json") for k in ["N1","N2","N3"]}
        cc=Counter();reasons=Counter();contexts=Counter();branches=Counter();locations={};total=exact=passed=0;max_res=None
        accounting={};observed=[]
        for k,s in summaries.items():
            n=s["numerical"];total+=n["all_adjacent_edges"];exact+=n["exact_checked"];passed+=n["exact_passed"]
            for c,e in n["classifications"].items():cc[c]+=e["count"]
            reasons.update(n["reasons"]);contexts.update(n["context_bases"]);branches.update(n["branch_counts"])
            locations[k]=n["locations"];max_res=max(max_res or 0.,n["max_abs_residual_m"] or 0.)
            f=pd.read_csv(batch/"runs"/s["run_id"]/"traffic_frames.csv")
            accounting[k]=dict(max_global_residual=int(f.global_conservation_residual.abs().max()),max_local_set_residual=int(f.local_set_balance_residual.abs().max()),
                local_space=s["local_space"],local_entered=s["local_entered"],local_exited=s["local_exited"],local_vehicle_s=s["local_vehicle_s"],
                actual_inserted=s["actual_inserted"],actual_exited=s["actual_exited"],present=s["present"],pending_end=s["pending_end"],
                scoped_counts_separated=True,traffic_role="micro only; does not validate C/D queue integration")
            observed.append(dict(kind=k,**{x:s[x] for x in ["status","observed_s","planned_vehicles","actual_inserted","actual_exited","present","runtime","first_times","runtime_settings"]},
                         numerical=n))
        coverage=dict(all_adjacent_edges=total,classifications={k:dict(count=v,fraction=v/total) for k,v in cc.items()},exact_checked=exact,exact_passed=passed,
            exact_pass_fraction=passed/exact,max_abs_residual_m=max_res,tolerance_m=1e-6,reasons=dict(reasons),context_bases=dict(contexts),branch_counts=dict(branches),
            locations=locations,per_fixture={k:s["numerical"] for k,s in summaries.items()},unobserved_runtime_branch="positive nonaction near-zero snap",
            counts_are_only_this_task=True,bounded_is_exact=False,unresolved_is_exact=False)
        write(out/"numerical_branch_coverage.json",coverage)
        write(out/"near_zero_runtime_diagnostics.json",dict(fixtures=observed,positive_nonaction_snap="Not Observed",negative_nonaction_snap="Observed in N3 at0.10->0.15s; u_pre=-3e-6,u_final=0",
            equality_to_strict_threshold="N3 nominal speed caps probe threshold sides; decision u_pre hidden; no claim all internal threshold crossings observed",
            historical_positive_counterexample="sealed B1.2 metadata only; not a new run, not retrospectively accepted",decision_near_zero_pre="Not independently observable"))
        write(out/"local_global_accounting_audit.json",accounting)
        write(out/"unresolved_context_audit.json",dict(runtime_near_zero_unresolved=cc["Near-Zero Context Unresolved"],general_context_identifiable=False,
             missing_positive_runtime_coverage=True,unknown_not_silently_allowed=True,context_basis_counts=dict(contexts),
             context_basis_unknown_does_not_mean_unresolved_numeric_edge=True,
             reason="Outside strict near-zero interval, positive decision final, or zero displacement fixed point needs no private predicate",
             locations=locations,core_C_D_impact="Evidence Insufficient; C/D not admitted"))
        matrix=[dict(context="fresh immutable no-stop lifecycle",source="constructor/reset doubleMax; only first stop makes finite value; state load excluded",observable="frozen inputs + public stops/routes/devices + collision/time proof",predicate=True,
                     qualification="restricted sufficient proof; negative snap observed; positive nonaction snap Not Observed"),
                dict(context="stable same-edge ordinary stop on nonaction",source="second disjunct; nonaction skips finalizeSpeed/processNextStop",observable="stable public first stop, route index/noncyclic route, current edge",predicate=True,qualification="101 ordinary-stop context edges in N1; near-zero snap Not Observed there"),
                dict(context="general stop-distance / first-stop mutation / state load",source="private myStopDist; filtered public stops/current geometric distance not equivalent",observable="Incomplete",predicate=None,qualification="Near-Zero Context Unresolved when candidate nonzero within strict threshold"),
                dict(context="independently false context",source="full OR predicate false",observable="analytic truth-table fixtures only",predicate=False,qualification="No live False proof claimed")]
        write(out/"near_zero_observability_matrix.json",dict(rows=matrix,terminal_speed_and_displacement_never_select_context=True))
        write(out/"near_zero_test_matrix.json",dict(synthetic_passed=203,numerical_cases=50,source="code/tests/test_stage_0_5_near_zero_observability.py",
            covered=["normal continuation","below threshold context true/false/unknown","strict positive/negative threshold boundary","decision stop bounded","nonaction early stop",
                     "stationary/restart","unknown missing proof key","illegal control/time/identity/config","legal edge/lane not evaluable","exact/range violations","no inverse displacement API"],
            runtime_runs=3,runtime_positive_snap="Not Observed",runtime_negative_snap="Observed",no_search_or_retry=True,
            integration_C="Not Attempted",integration_D="Not Attempted",runtime_generic_false_context="Not Observed"))
        for kind in ["C","D"]:
            write(out/f"integration_{kind}_audit.json",dict(status="Not Attempted",plan_frozen=False,runs=0,reason="shared predeclared positive-snap admission checkpoint not satisfied",
                observed_s=None,numerical_coverage=None,queue_qualification="Evidence Insufficient",dynamic_network_verified=False,
                not_a_scenario_result=True,historical_results_unchanged=True))
        write(out/"lane_change_and_exit_diagnostics.json",dict(D_status="Not Attempted",actual_lane_changes=None,vehicles_exited=None,
              D_planned_candidate_vehicles=9,D_candidate_depart_spacing_s=1.5,driver_or_network_tuning=False,
              candidate_not_frozen=True,reason="shared precondition; no inference of lane-change failure"))
        write(out/"queue_integration_diagnostics.json",dict(C="Not Attempted",D="Not Attempted",internal_queue=None,inlet_adjacent=None,external_pending=None,
            persistent_entry_spillback="Evidence Insufficient",candidate_thresholds_scientifically_approved=False,
            previous_B12=dict(edge_transitions=83,cross_edge_distance_checks=71,junction_states=439,physical_gap_checks=7332,preserved=True),
            gaps=["C inlet/internal queue/pending and continuous physical entry evidence unfinished","D real lane change/path/outlet unverified",
                  "conservative edge/lane membership resets","no bridging across unknown paths","engineering thresholds lack traffic-science approval"],
            slower_vehicles_are_not_qualified_queue=True,pending_alone_not_spillback=True))
        ledger_rows=task["runs"]
        bindings=[dict(run_id=r["run_id"],seed=r["seed"],duration_s=r["duration_s"],
             inputs={k:dict(path=r[k],sha256=plan["frozen_files"][r[k]]) for k in ["network","demand","config"]}) for r in plan["runs"]]
        write(out/"run_manifest.json",dict(runs=ledger_rows,input_bindings=bindings,micro_runs=3,integration_runs=0,main_matrix_runs=0,
             main_plan_frozen=False,main_matrix_authorized=False,C_D_plans_frozen=False,closure_reason=task["closure_reason"]))
        write(out/"runtime_budget_audit.json",dict(max_new_traffic_runs=5,actual_traffic_runs=3,unused_C_D_runs=2,plan_limits=plan["limits"],overall_wall_limit_s=1800,
             supervisor_total_wall_s=sum(r.get("wall_s",0) for r in ledger_rows),max_sampled_tree_rss_bytes=max(r.get("peak_sampled_tree_rss_bytes",0) for r in ledger_rows),
             per_run=ledger_rows,queue_compute_cost="Not Measured; C/D not executed",P2_compute_cost="Not Attempted; outside task",resources_sampled_not_absolute_peak=True))
        history=dict(B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised="Unknown",B1_C="completed_with_engineering_blocker",B1_D="not_attempted",
              B11="Pending Numerical Equivalence",B11S_exact=947,B11S_total=948,B12_MAIN_MATRIX_ALLOWED=False,B12_main_runs=0,B12_D="not_attempted",
              B12_positive_mismatch="Engineering Blocker retained",historical_results_modified=False,historical_reclassification=False)
        write(out/"historical_status_preservation.json",history)
        decisions=[dict(item=i,status=s,recommendation=r,approval_needed=a) for i,s,r,a in [
            ("Near-zero policy","Partially runtime verified","Keep strict source-qualified layered candidate;1e-6m unchanged","Future measurement policy and missing positive-snap verification design"),
            ("Unknown stop context","Generally unidentifiable","Near-Zero Context Unresolved/Evidence Insufficient; source-derived necessary support never Exact","Location/duration/core-evidence policy before future runs"),
            ("Queue qualification","Incomplete","Retain conservative per-path/per-lane rules; complete C duties","New limited integration allocation after shared admission"),
            ("D dynamic network","Not Attempted","Validate actual lane2 merge/path/exit separately","New D integration plan after shared admission"),
            ("New A/B/C/D matrix","Still requires remediation","Do not start; positive runtime domain and C/D duties missing","Separate explicit researcher approval and newly frozen plan"),
            ("Geometry and supply","Generic/artificial","Geometry/arrival/supply evidence remains needed; no realism/capacity equivalence","Researcher design choice"),
            ("Formal calibration","Not Ready","Need stable qualified traffic states/demand/observation ownership","Scientific protocol, tolerances and local P2 ownership")]]
        write(out/"researcher_decision_matrix.json",decisions)
        logs=[]
        for p in sorted((batch/"access_logs").glob("*.json")):
            d=read(p);logs.append(dict(file=p.name,sha256=sha(p),denied=d["denied"],allowed_open_events=d.get("allowed_open_events")))
        write(out/"controlled_access_audit.json",dict(logs=logs,unexpected_denials=sum(len(x["denied"]) for x in logs),no_real_trajectory_inputs=True,
              Python_audit_only=True,native_access_monitored=False,os_complete_monitoring=False,synthetic_probe_separate=True))
        write(out/"audit.json",dict(result_id=RESULT_ID,status="closed_at_positive_snap_admission_gap",task_mode="engineering_observability_and_integration_only",
              result_mode="exploratory_diagnostic_only",**SCIENCE,integration_allowed=False,main_matrix_allowed=False,main_matrix_attempts=0,
              micro_runs=3,integration_attempts=0,exact_checked=exact,exact_passed=passed,bounded=cc["Bounded Consistency Only"],
              near_zero_unresolved=cc["Near-Zero Context Unresolved"],not_evaluable=cc["Not Evaluable"],engineering_blockers=cc["Engineering Blocker"],
              positive_snap_runtime="Not Observed",validation_window_rows_materialised=0,old_C_states_read=False,private_variables_instrumented=False,
              installed_binary_modified=False,researcher_decision_required=True))
        write(out/"provenance.json",dict(result_id=RESULT_ID,base_commit=read(batch/"preparation_manifest.json")["base_commit"],
              micro_plan_sha256=sha(batch/"micro_plan.json"),executed_source_and_input_sha256=plan["frozen_files"],analysis=read(batch/"analysis_source_manifest.json"),
              real_data_inputs=[],old_C_states_read=False,new_runs_by_analysis=0,postrun_execution_logic_changed=False))
        write(out/"config.json",dict(fixed_engineering_candidate=FIXED,actual_micro_overrides="N3 sigma0 and three nominal maxSpeeds3e-6/5e-6/7e-6, probe only; all runtime types echoed",runs=plan["runs"],
              C_D_inputs="engineering candidates only; not frozen or run",P2_calculated=False,scientific_tolerance="Tolerance Not Yet Justified",
              Energy_Distance_real_real_upper_bound="Not Identifiable",local_formal_P2="Unresolved"))
        pre=read(batch/"synthetic_test_record.json")
        if not (out/"test_record.json").exists():
            write(out/"test_record.json",dict(pre_freeze=dict(passed=203,failed=0,skipped=0,command=pre["command"],record_sha256=sha(batch/"synthetic_test_record.json")),
                  preparation_failure_retained="test-only capsule dependency omissions repaired before freeze; no SUMO consumed",final_validation="Pending",data_skips_are_not_scientific_pass=True))
        write(out/"analysis_access_audit.json",guard)
        if guard["denied"]:raise PermissionError("analysis denied access")
        seal(out);print("B12N_PORTABLE_SUMMARY_READY")
    finally:write(batch/"analysis_access_audit.json",guard)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("batch",type=Path);p.add_argument("--render",action="store_true");p.add_argument("--seal",action="store_true")
    a=p.parse_args();b=a.batch.resolve()
    if a.render:render(b)
    elif a.seal:seal(b/"summary")
    else:raise SystemExit(stage(Path(__file__).resolve().parents[2],b))
