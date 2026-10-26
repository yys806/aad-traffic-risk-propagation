"""Offline regressions for continuation audit tools; never starts WSL or SUMO."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import pytest

TOOLS=Path(__file__).resolve().parents[2]/'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/continuation-r2/audit_tools'
sys.path.insert(0,str(TOOLS))
import audit_common as common

@pytest.mark.parametrize('name',['unprivileged_userns_clone','max_user_namespaces'])
def test_missing_optional_sysctl_is_metadata_not_capability_failure(tmp_path,name):
    assert common.optional_text(tmp_path/name)==dict(present=False,value=None,observation='FileNotFoundError')

def test_optional_sysctl_retains_value(tmp_path):
    p=tmp_path/'sysctl';p.write_text('0\n')
    assert common.optional_text(p)==dict(present=True,value='0')

def test_existing_historical_audit_does_not_mean_launch(tmp_path):
    (tmp_path/'smoke-20261026-3').mkdir();(tmp_path/'smoke_capsule').mkdir()
    (tmp_path/'smoke_capsule/policy.json').write_text('{}')
    assert common.launch_artifacts(tmp_path)==[]

@pytest.mark.parametrize('name',['launch_attempt.json','archive/controller_receipt.json','engineering_acceptance.json','coordinator_failure.json','broker.stdout','broker.stderr'])
def test_actual_native_records_prevent_reuse(tmp_path,name):
    p=tmp_path/'smoke_capsule'/name;p.parent.mkdir(parents=True);p.write_text('retained')
    assert str(p) in common.launch_artifacts(tmp_path)

@pytest.mark.parametrize('values,expected',[(dict(LoadState='not-found',ActiveState='inactive'),True),
    (dict(LoadState='loaded',ActiveState='inactive'),False),(dict(LoadState='loaded',ActiveState='active',ControlGroup='/actual'),False)])
def test_production_unit_must_really_be_absent(values,expected):
    assert common.unit_is_absent(values)==expected

def test_command_raw_bytes_saved_before_safe_display(tmp_path,monkeypatch):
    raw=b'\xff\xfeWSL\x00\x81'
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=b'{}',stderr=raw))
    row=common.Runner(tmp_path);row.run('probe',['synthetic'],timeout=5)
    assert (tmp_path/'probe.stderr').read_bytes()==raw
    assert row.commands[0]['stderr_sha256']==hashlib.sha256(raw).hexdigest()
    output=io.StringIO();monkeypatch.setattr(sys,'stdout',output)
    common.display({'message':'中文\ufffd'})
    assert output.getvalue().isascii()

def test_timeout_preserves_diagnostics_and_marks_required_check_failure(tmp_path,monkeypatch):
    def timeout(*a,**k):raise subprocess.TimeoutExpired(a[0],5,output=b'partial',stderr=b'why')
    monkeypatch.setattr(subprocess,'run',timeout);r=common.Runner(tmp_path)
    with pytest.raises(common.RequiredCheckFailure):r.run('timeout',['synthetic'],timeout=5)
    assert (tmp_path/'timeout.stdout').read_bytes()==b'partial'
    assert r.commands[0]['exit_code']==124

def test_runner_refuses_overwrite_before_any_subprocess(tmp_path,monkeypatch):
    common.write(tmp_path/'probe.started.json',{})
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:pytest.fail('must not launch'))
    with pytest.raises(FileExistsError):common.Runner(tmp_path).run('probe',['synthetic'])

def test_existing_explicit_git_output_cannot_be_reused(tmp_path):
    from preflight_git import check
    root=tmp_path;out=root/'code/tmp/checks_r2';out.mkdir(parents=True)
    with pytest.raises(FileExistsError):check(root,root/'code/tmp/clone',out)

def test_native_process_match_does_not_match_preflight_coordinator():
    runtime=dict(sumo_binary='/runtime/sumo');p=dict(capsule='/stage/smoke_capsule',binding=dict(source_files={'stage_0_5_linux_controller_v4.py':'/stage/controller.py'}))
    rows=[dict(pid=1,exe='/python',cmdline=['python','preflight_linux.py','--stage','/stage']),
          dict(pid=2,exe='/runtime/sumo',cmdline=['sumo','--version'])]
    assert common.native_processes(runtime,p,rows)==[rows[1]]

def test_auxiliary_import_has_no_precheck_or_native_side_effects(monkeypatch):
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:pytest.fail('imports cannot launch'))
    import preflight_linux
    assert preflight_linux.STAGE.as_posix()=='/home/shen/AAD/code/tmp/stage05_v4_20261026_r5'
