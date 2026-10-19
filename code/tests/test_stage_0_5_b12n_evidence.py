"""Portable-only negative checks, including missing positive runtime branch."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT=Path(__file__).resolve().parents[2]

def verifier():
    spec=importlib.util.spec_from_file_location("b12n_verify",ROOT/"code/scripts/verify_stage_0_5_near_zero_evidence.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def copy_portable(tmp):
    for p in (ROOT/"evidence/results/RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1").iterdir():shutil.copyfile(p,tmp/p.name)

def reseal(tmp):
    entries=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in tmp.iterdir() if p.name not in ["manifest.json","SHA256SUMS"]]
    (tmp/"manifest.json").write_text(json.dumps(dict(files=entries)))
    entries.append(dict(path="manifest.json",sha256=hashlib.sha256((tmp/"manifest.json").read_bytes()).hexdigest()))
    (tmp/"SHA256SUMS").write_text("".join(f'{e["sha256"]}  {e["path"]}\n' for e in entries))

def test_actual_closed_result_verifies(tmp_path):
    copy_portable(tmp_path);assert not verifier().verify(tmp_path)["integration_allowed"]

@pytest.mark.parametrize("kind",["gate","admit","C","D","count","exact","history","bundle","path"])
def test_resealed_tamper_cannot_promote_missing_coverage(tmp_path,kind):
    copy_portable(tmp_path)
    name=dict(gate="audit.json",admit="micro_checkpoint.json",C="integration_C_audit.json",D="task_ledger.json",
              count="numerical_branch_coverage.json",exact="numerical_branch_coverage.json",history="historical_status_preservation.json",bundle="engineering_input_bundle.json",path="manifest.json")[kind]
    p=tmp_path/name;d=json.loads(p.read_text(encoding="utf-8"))
    if kind=="gate":d["scientific_claim_eligible"]=True
    elif kind=="admit":d["integration_allowed"]=True
    elif kind=="C":d["observed_s"]=0
    elif kind=="D":d["runs"][4]["status"]="completed_valid"
    elif kind=="count":d["classifications"]["Bounded Consistency Only"]["count"]-=1
    elif kind=="exact":d["bounded_is_exact"]=True
    elif kind=="history":d["B12_MAIN_MATRIX_ALLOWED"]=True
    elif kind=="bundle":next(iter(d["files"].values()))["sha256"]="0"*64
    elif kind=="path":d["files"][0]["path"]="../escape.json"
    p.write_text(json.dumps(d),encoding="utf-8")
    if kind!="path":reseal(tmp_path)
    with pytest.raises(ValueError):verifier().verify(tmp_path)

def test_missing_positive_runtime_snap_cannot_admit_C_D(tmp_path,monkeypatch):
    from riskprop import stage_0_5_b12n_runtime as runtime
    monkeypatch.setattr(runtime,"load_plan",lambda *_:{})
    def put(p,d):p.write_text(json.dumps(d))
    put(tmp_path/"micro_plan.json",{})
    put(tmp_path/"micro_ledger.json",dict(closed=True,runs=[dict(run_id="n"+str(i)) for i in range(3)]))
    put(tmp_path/"task_ledger.json",dict(global_stop=None))
    put(tmp_path/"near_zero_source_contract.json",{})
    for i in range(3):
        out=tmp_path/"runs"/("n"+str(i));out.mkdir(parents=True)
        put(out/"summary.json",dict(observed_s=30.,global_blockers=[],numerical=dict(classifications={"Exact After Verified Postprocessing":dict(count=1)},branch_counts=dict(negative_snap=1))))
    runtime.micro_checkpoint(tmp_path)
    c=json.loads((tmp_path/"micro_checkpoint.json").read_text())
    assert c["observed_exact_after"]==3 and c["observed_positive_snap"]==0 and not c["integration_allowed"]
    with pytest.raises(PermissionError):runtime.freeze_integration(tmp_path)
