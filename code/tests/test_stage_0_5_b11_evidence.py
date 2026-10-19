"""B1.1 portable verification: synthetic packages only; never local traffic."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ENTRY=Path(__file__).resolve().parents[1]/"scripts/verify_stage_0_5_stopping_evidence.py"


def module():
    spec=importlib.util.spec_from_file_location("b11_verify",ENTRY)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def package(root,*,corrupt=False,historical_status="completed_with_engineering_blocker",gate="pending_simulation_sample"):
    raw=b"<routes/>";digest=hashlib.sha256(raw).hexdigest();name="inputs/fake.xml"
    contract=b'{"version":"synthetic"}'
    (root/"displacement_branch_contract.json").write_bytes(contract)
    plan=dict(frozen_files={name:digest,"displacement_branch_contract.json":hashlib.sha256(contract).hexdigest()},
        runs=[dict(run_id="micro",duration_s=30,input_sha256={name:digest})])
    values={"experiment_plan.json":plan,"audit.json":dict(stage_0_5_gate=gate,
        scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False,
        protocol_lock_allowed=False,stage_1_1_allowed=False,numerical_exact_stopping="Pending Numerical Equivalence",
        B0_task_data_isolation_accepted=False,B0_validation_window_rows_materialised="Unknown",old_C_states_read=False),
        "execution_ledger.json":dict(closed=True,runs=[dict(run_id="micro",status="completed_valid")]),
        "historical_b1_status_preservation.json":dict(C=dict(status=historical_status,
            blockers=["runtime_settings","persistent_external_demand_without_documented_spillback"]),D=dict(status="not_attempted"),
            historical_reclassification=False,old_C_state_read=False),
        "micro_input_bundle.json":dict(files={name:dict(sha256=digest,bytes=len(raw),
            gzip_base64=base64.b64encode(gzip.compress(b"bad" if corrupt else raw)).decode())})}
    for filename,data in values.items():(root/filename).write_text(json.dumps(data))
    (root/"PLAN_SHA256").write_text(hashlib.sha256((root/"experiment_plan.json").read_bytes()).hexdigest()+"  experiment_plan.json\n")
    seal(root)


def seal(root):
    files=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.iterdir() if p.name not in ["manifest.json","SHA256SUMS"]]
    (root/"manifest.json").write_text(json.dumps(dict(files=files)))
    files.append(dict(path="manifest.json",sha256=hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest()))
    (root/"SHA256SUMS").write_text("".join(f'{f["sha256"]}  {f["path"]}\n' for f in files))


def test_synthetic_portable_contract_verifies(tmp_path):
    package(tmp_path);module().verify(tmp_path)


@pytest.mark.parametrize("kind",["file","bundle","gate","history","frozen_contract","manifest_omission","path_escape"])
def test_resealed_or_unsealed_corruption_rejected(tmp_path,kind):
    package(tmp_path,corrupt=kind=="bundle",gate="pass" if kind=="gate" else "pending_simulation_sample",
        historical_status="completed_valid" if kind=="history" else "completed_with_engineering_blocker")
    if kind=="file":(tmp_path/"audit.json").write_text("{}")
    if kind=="frozen_contract":
        (tmp_path/"displacement_branch_contract.json").write_text("{}");seal(tmp_path)
    if kind in ["manifest_omission","path_escape"]:
        m=json.loads((tmp_path/"manifest.json").read_text())
        if kind=="manifest_omission":m["files"].pop()
        else:m["files"][0]["path"]="../outside.json"
        (tmp_path/"manifest.json").write_text(json.dumps(m))
    with pytest.raises(ValueError):module().verify(tmp_path)


@pytest.mark.parametrize("corrupt",[False,True])
def test_canonical_source_binding_with_explicit_original_crlf(tmp_path,monkeypatch,corrupt):
    m=module();canonical=b'print("synthetic")\n';frozen=canonical.replace(b'\n',b'\r\n')
    digest=hashlib.sha256(frozen).hexdigest();name='runtime/code/fake.py'
    (tmp_path/'git_source_binding_audit.json').write_text(json.dumps(dict(files=[dict(path='code/fake.py',
        frozen_sha256=digest,canonical_git_blob_sha256=hashlib.sha256(canonical).hexdigest(),
        byte_transform='canonical LF to original CRLF')],generated_runtime=[])))
    monkeypatch.setattr(m.subprocess,'check_output',lambda *a,**kw:b'changed\n' if corrupt else canonical)
    if corrupt:
        with pytest.raises(ValueError,match='source'):m.verify_sources(tmp_path,tmp_path,{name:digest})
    else:assert m.verify_sources(tmp_path,tmp_path,{name:digest})==1


def test_generated_capsule_bootstrap_cannot_change(tmp_path):
    m=module();raw=b'bootstrap';name='runtime/code/src/sitecustomize.py';digest=hashlib.sha256(raw).hexdigest()
    (tmp_path/'git_source_binding_audit.json').write_text(json.dumps(dict(files=[],generated_runtime=[dict(path=name,
        sha256=digest,base64=base64.b64encode(b'changed').decode())])))
    with pytest.raises(ValueError,match='bootstrap'):m.verify_sources(tmp_path,tmp_path,{name:digest})
