"""New portable evidence and analytic counterexample regression; no local data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

from riskprop.stage_0_5_b12_observation import audit_transition

ROOT=Path(__file__).resolve().parents[2]


def verifier():
    spec=importlib.util.spec_from_file_location("b12_verify",ROOT/"code/scripts/verify_stage_0_5_revalidation_evidence.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def copy_portable(tmp_path):
    # Only the explicitly named portable result, never implicit local outputs.
    source=ROOT/"evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2"
    for p in source.iterdir():shutil.copyfile(p,tmp_path/p.name)


def reseal(root):
    files=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.iterdir() if p.name not in ["manifest.json","SHA256SUMS"]]
    (root/"manifest.json").write_text(json.dumps(dict(files=files)))
    files.append(dict(path="manifest.json",sha256=hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest()))
    (root/"SHA256SUMS").write_text("".join(f'{e["sha256"]}  {e["path"]}\n' for e in files))


def test_actual_portable_blocked_result_verifies(tmp_path):
    copy_portable(tmp_path)
    assert verifier().verify(tmp_path)["main_matrix_attempts"]==0


@pytest.mark.parametrize("kind",["gate","admit","ledger","counts","anomaly","history","bundle","path"])
def test_resealed_tampering_cannot_promote_or_hide_failure(tmp_path,kind):
    copy_portable(tmp_path)
    name={"gate":"audit.json","admit":"observability_integration_audit.json","ledger":"execution_ledger.json",
          "counts":"numerical_branch_coverage.json","anomaly":"numerical_branch_coverage.json",
          "history":"historical_status_preservation.json","bundle":"engineering_input_bundle.json","path":"manifest.json"}[kind]
    p=tmp_path/name;d=json.loads(p.read_text(encoding="utf-8"))
    if kind=="gate":d["gate"]="pass"
    elif kind=="admit":d["B1_2_MAIN_MATRIX_ALLOWED"]=True
    elif kind=="ledger":d["main_matrix"][0]["status"]="completed_valid"
    elif kind=="counts":d["classifications"]["Not Evaluable"]["count"]-=1
    elif kind=="anomaly":d["examples"]["candidate_terminal_speed_inconsistent"]["residual_m"]=0.
    elif kind=="history":d["B1_C"]="completed_valid"
    elif kind=="bundle":next(iter(d["files"].values()))["sha256"]="0"*64
    elif kind=="path":d["files"][0]["path"]="../outside.json"
    p.write_text(json.dumps(d),encoding="utf-8")
    if kind!="path":reseal(tmp_path)
    with pytest.raises(ValueError):verifier().verify(tmp_path)


def test_positive_nonaction_nearzero_candidate_mismatch_stays_blocked():
    # Independent near-zero example: continuation predicts +4e-6 m/s, but a
    # post-continuation snap yields zero. Never accept merely because dx is tiny.
    a=dict(run_id="r",vehicle_id="v",incarnation_id="r|v",time_s=.05,
           speed_mps=6e-6,acceleration_mps2=-4e-5,position_m=1.,last_action_time_s=0.,
           edge_id="e",lane_id="e_0",traci_vehicle_control=False,numerical_config_verified=True)
    b=dict(a,time_s=.1,speed_mps=0.,acceleration_mps2=-1.2e-4,position_m=1.+1.5e-7)
    r=audit_transition(a,b)
    assert r["blocker"]=="candidate_terminal_speed_inconsistent"
    assert r["classification"]=="Not Evaluable" and r["residual_m"] is None
