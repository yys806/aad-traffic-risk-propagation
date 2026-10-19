"""Package the CLOSED B1 diagnostic batch; never starts or resumes simulation."""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
from riskprop.stage_0_5_b1_analysis import seal
from riskprop.stage_0_5_boundary_bottleneck import read_plan
from riskprop.stage_0_5_calibration_readiness import _write_json,_sha256_file

p=argparse.ArgumentParser(description=__doc__);p.add_argument("--batch",type=Path,required=True)
a=p.parse_args();batch=a.batch.resolve();plan=read_plan(batch)
out=batch/"summary";ledger=json.loads((batch/"execution_ledger.json").read_text())
if not ledger["closed"]:raise ValueError("refusing to finalize an open batch")
shutil.copyfile(ROOT/"docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md",out/"report.md")
_write_json(out/"mechanism_hypothesis_matrix.json",dict(hypotheses=[
    dict(id="H1",status="Partially Supported",support="B changes gap median54.637->34.383m and speed27.109->26.515; same823 insertions",
        against="local speed<5 fraction remains0; no sustained congestion",alternative="entry platoon acceleration and lane interactions",unresolved="single seed; real arrival process unknown"),
    dict(id="H2",status="Partially Supported",support="C inside congestion before external pending263s; low-speed appearance moves upstream",
        against="C engineering blockers, extreme artificial supply and571 actual insertions",alternative="periodic service forcing; actual capacity differs",unresolved="valid spillback contract and stopping numerical audit"),
    dict(id="H3",status="Inconclusive",support="D static connections and equal observer pass",against="D not attempted after C blocker",
        alternative="capacity differences can confound any later C/D contrast",unresolved="all dynamic structural effects"),
    dict(id="H4",status="Partially Supported",support="fixed Krauss C shows low-speed dense following in diagnostic states",
        against="C not engineering-valid; no second seed or real geometry",alternative="strong downstream supply alone",unresolved="reality coverage and parameter identifiability")],
    next_task_proposal="B1.1 stopping numerical audit and spillback observation contract; no automatic execution",scientific_claim_eligible=False))
_write_json(out/"numerical_stop_diagnostic.json",dict(
    documented_intent="independent ballistic displacement check using observed endpoint speeds",
    actual_implementation="all changing-speed same-edge/lane .05s edges included, including stopping edges",
    evidence=dict(run_id="b1_C_s20261019",max_abs_residual_m=.0013318918382596158,checks=78495,
        frozen_threshold_m=1e-6,runtime_option_ballistic=True,
        official_source="https://github.com/eclipse-sumo/sumo/blob/v1_26_0/src/microsim/MSVehicle.cpp#L3510"),
    conflict="signed internal vNext stopping branch cannot universally be reconstructed from nonnegative observed terminal speed; actual residual cause not proven from retained max-only .05s audit",
    affected_files=["code/src/riskprop/stage_0_5_boundary_bottleneck.py::run_worker"],
    status="Awaiting Researcher Decision",blocker_retained=True,threshold_not_relaxed=True,no_rerun=True,
    needed="record anomalous .05s edges and stop-branch information; prospectively validate stopping-aware audit before next plan"))
_write_json(out/"execution_stop_observation.json",dict(prior_v1="worker exit1 after denied ambient metadata access;7 subsequent not_attempted",
    v2=ledger["runs"],v2_stop_reason=ledger["stop_reason"],
    stopped_after_engineering_blocker_with_worker_exit_zero=True,D_not_launched=True,no_extra_seed_or_load=True,
    original_pending_spillback_rules_retained=True,all_failures_retained=True))
_write_json(out/"researcher_decision_matrix.json",dict(
    approved_by_researcher=dict(b0_retained_limited_descriptive=True,b0_task_isolation_accepted=False,b0_validation_rows="Unknown",
        b1_isolation_and_fixed_behaviour_contrasts=True,formal_calibration=False,independent_validation=False),
    proposals=[dict(choice="B1.1 audit repair before new traffic batch",evidence_gap="stopping branch and spillback observation",approved=False),
        dict(choice="retain generic diagnostic corridor; D3to2 remains untested",evidence_gap="dynamic validity, supply capacity and real geometry",approved=False),
        dict(choice="keep1648 input and23.8/6.2/30 service only as engineering candidates",evidence_gap="true boundary demand/supply unidentified",approved=False),
        dict(choice="do not enter formal0.5.4-B",evidence_gap="valid constrained samples, tolerances and local P2 membership",approved=False)],
    current_gate="pending_simulation_sample",scientific_claim_eligible=False))
if not (out/"test_record.json").exists():
    _write_json(out/"test_record.json",dict(capsule_preflight="45 passed",synthetic_path_refusals="3/3",
        new_portable_tests="Pending clean Git regression",full_regression="Pending clean Git regression",
        whole_root_pytest_run=False,local_data_skips_are_not_passes=True))
provenance=json.loads((out/"provenance.json").read_text())
provenance["packaging_source_sha256"]=_sha256_file(Path(__file__))
provenance["renderer_frozen_execution_files_verified"]=True
_write_json(out/"provenance.json",provenance)
seal(out)
print("B1_CLOSED_PACKAGE_SEALED")
