"""Portable B1 verification uses synthetic data only, with no local output lookup."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location("b1_verify",Path(__file__).resolve().parents[1]/"scripts/verify_stage_0_5_boundary_evidence.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def package(root,*,corrupt_bundle=False,gate="pending_simulation_sample"):
    raw=b"<routes/>";sha=hashlib.sha256(raw).hexdigest();name="inputs/fake.xml"
    plan=dict(frozen_files={name:sha},runs=[dict(input_sha256={name:sha})])
    audit=dict(stage_0_5_gate=gate,scientific_claim_eligible=False,ready_to_start_stage_0_5_4b=False,
        reality_coverage_accepted=False,protocol_lock_allowed=False,stage_1_1_allowed=False,
        b0_task_data_isolation_accepted=False,b0_validation_window_rows_materialised="Unknown")
    for filename,data in {"experiment_plan.json":plan,"audit.json":audit,"run_manifest.json":dict(task_attempts=5),
        "engineering_input_bundle.json":dict(files={name:dict(sha256=sha,bytes=len(raw),
            gzip_base64=base64.b64encode(gzip.compress(b"corrupt" if corrupt_bundle else raw)).decode())})}.items():
        (root/filename).write_text(json.dumps(data))
    (root/"PLAN_SHA256").write_text(hashlib.sha256((root/"experiment_plan.json").read_bytes()).hexdigest()+"  experiment_plan.json\n")
    files=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.iterdir()]
    (root/"manifest.json").write_text(json.dumps(dict(files=files)))
    files.append(dict(path="manifest.json",sha256=hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest()))
    (root/"SHA256SUMS").write_text("".join(f'{f["sha256"]}  {f["path"]}\n' for f in files))


def test_portable_bundle_verifies_without_real_data(tmp_path):
    package(tmp_path);module.verify(tmp_path)


def test_tampered_portable_file_is_rejected(tmp_path):
    package(tmp_path);(tmp_path/"audit.json").write_text("{}")
    with pytest.raises(ValueError,match="manifest"):module.verify(tmp_path)


def test_resealed_corrupt_input_cannot_pass_frozen_plan(tmp_path):
    package(tmp_path,corrupt_bundle=True)
    with pytest.raises(ValueError,match="bundle"):module.verify(tmp_path)


def test_resealed_package_cannot_approve_scientific_gate(tmp_path):
    package(tmp_path,gate="pass")
    with pytest.raises(ValueError,match="scientific"):module.verify(tmp_path)
