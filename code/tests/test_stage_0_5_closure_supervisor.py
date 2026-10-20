"""Real subprocess stop tests; no SUMO, real data or project outputs."""
import importlib.util
from pathlib import Path
import sys
import json
import pytest

P=Path(__file__).resolve().parents[1]/'scripts/supervise_stage_0_5_closure.py'
spec=importlib.util.spec_from_file_location('closure_supervisor',P)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_success_failure_and_no_retry(tmp_path):
    assert module.supervise(tmp_path,'success',[sys.executable,'-c','print(1)'],wall_s=10)==0
    with pytest.raises(PermissionError):module.supervise(tmp_path,'success',[sys.executable,'-c','print(2)'],wall_s=10)
    assert module.supervise(tmp_path,'failure',[sys.executable,'-c','raise SystemExit(7)'],wall_s=10)==1


def test_timeout_terminates_real_child(tmp_path):
    assert module.supervise(tmp_path,'timeout',[sys.executable,'-c','import time; time.sleep(10)'],wall_s=.1)==1


def test_memory_and_output_caps_terminate(tmp_path):
    assert module.supervise(tmp_path,'memory',[sys.executable,'-c','import time; x=bytearray(20*1024**2);time.sleep(10)'],wall_s=10,memory_bytes=1024**2)==1
    assert module.supervise(tmp_path,'output',[sys.executable,'-c','import time; print("x"*100000,flush=True);time.sleep(10)'],wall_s=10,artifact_bytes=1000)==1


def test_changed_controller_cannot_launch_frozen_run(tmp_path):
    (tmp_path/'experiment_plan.json').write_text(json.dumps(dict(controller_sha256='0'*64)))
    with pytest.raises(PermissionError):module.supervise(tmp_path,'changed',[sys.executable,'-c','print(1)'],wall_s=10)
    assert not (tmp_path/'supervision').exists()
