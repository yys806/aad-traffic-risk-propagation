import importlib.util
from pathlib import Path
import subprocess
import sys
import pytest

def load():
    path = Path(__file__).parents[1] / 'scripts/interaction_task_boundary.py'
    spec = importlib.util.spec_from_file_location('boundary', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def test_boundary_read_write_and_directory_escape(tmp_path):
    m = load(); approved = tmp_path / 'approved'; work = tmp_path / 'work'
    b = m.Boundary([approved], [], work)
    b.check(approved); b.check(work / 'new', True)
    for path, writing in [(approved, True), (tmp_path / 'sealed', False), (work / '../sealed', False)]:
        with pytest.raises(PermissionError): b.check(path, writing)
    with pytest.raises(PermissionError): b.audit('os.scandir', (tmp_path / 'sealed',))

def test_exact_single_child_and_shell_denial(tmp_path):
    m = load(); argv = [sys.executable, '-I', '-c', 'pass']
    b = m.Boundary([], [], tmp_path, [{'executable': sys.executable, 'argv': argv}])
    b.audit('subprocess.Popen', (sys.executable, subprocess.list2cmdline(argv), str(tmp_path), None))
    with pytest.raises(PermissionError): b.audit('subprocess.Popen', (sys.executable, argv, None, None))
    with pytest.raises(PermissionError): b.audit('os.system', ('echo unsafe',))

def test_xml_rejects_external_input_before_any_launch(tmp_path):
    # Test the small XML validation function without importing data dependencies.
    import ast
    import xml.etree.ElementTree as ET
    source = (Path(__file__).parents[1] / 'scripts/run_stage_0_5_policy_a_confirmed.py').read_text(encoding='utf-8')
    tree = ast.parse(source); fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_xml')
    ns = {'ET': ET}; exec(compile(ast.Module(body=[fn], type_ignores=[]), 'validation', 'exec'), ns)
    (tmp_path / 'run.sumocfg').write_text('<!DOCTYPE x [<!ENTITY ext SYSTEM="private">]><configuration/>')
    with pytest.raises(ValueError, match='external_entities'): ns['validate_xml'](tmp_path)
