import importlib.util
from pathlib import Path
import sys
import pytest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('candidate', SCRIPTS / 'prepare_stage_0_5_depart_speed_candidate.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def sample():
    return (b'<routes><vType id="passenger" maxSpeed="27.78"/>'
            b'<vehicle id="i1" depart="0" departSpeed="10.00"/>'
            b'<vehicle id="i2" depart="0" departSpeed="15.23"/>'
            b'<vehicle id="m1" depart="1" departSpeed="10.00"/></routes>')


def test_only_target_initial_changed_other_bytes_and_noninitial_untouched():
    revised, ids = m.revise_routes(sample())
    assert ids == ['i1']
    assert revised == sample().replace(b'id="i1" depart="0" departSpeed="10.00"', b'id="i1" depart="0" departSpeed="max"')


@pytest.mark.parametrize('edit', [
    lambda b: b.replace(b'15.23', b'max'),
    lambda b: b.replace(b'depart="1"', b'depart="2"'),
    lambda b: b.replace(b'maxSpeed="27.78"', b'maxSpeed="28"'),
    lambda b: b.replace(b'id="m1"', b'id="m2"'),
])
def test_semantic_scope_rejects_unapproved_edits(edit):
    revised, _ = m.revise_routes(sample())
    with pytest.raises(ValueError): m.confirm_revision(sample(), edit(revised))


@pytest.mark.parametrize('data', [
    sample().replace(b'id="i2"', b'id="i1"'),
    sample().replace(b'id="i1" depart="0"', b'id="i1" depart="1"'),
    sample().replace(b'id="m1" depart="1"', b'id="m1" depart="0"'),
    b'<!DOCTYPE routes [<!ENTITY x SYSTEM="unapproved">]><routes/>',
])
def test_invalid_identity_initial_time_or_external_entity_fails_closed(data):
    with pytest.raises(ValueError): m.revise_routes(data)


def test_observation_missing_is_not_pending_or_zero_insertion(tmp_path):
    f = tmp_path / 'fcd.xml'
    f.write_text('<fcd><timestep time="0.1"><vehicle id="i1" speed="5" lane="main_2_0"/></timestep>'
                 '<timestep time="120"><vehicle id="i1" speed="4" lane="main_2_0"/></timestep></fcd>')
    s, rows = m.observe_initial(f, {'i1', 'i2'})
    assert s['initial_not_observed'] == ['i2'] and s['global_initial_present_at_120'] == 1
    assert s['first_after_0_count'] == 1 and rows['i1']['first_FCD_s'] == .1
    assert s['identities_pending'].startswith('Unknown') and 'i2' not in rows


def test_candidate_has_no_process_or_launch_mode():
    import ast
    tree = ast.parse((SCRIPTS / 'prepare_stage_0_5_depart_speed_candidate.py').read_text(encoding='utf-8'))
    assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) and
                   ('subprocess' in str(ast.dump(n)) or 'traci' in str(ast.dump(n))) for n in ast.walk(tree))
    boundary = m.Boundary([], [], Path('.'), commands=())
    with pytest.raises(PermissionError): boundary.audit('subprocess.Popen', ('sumo', ['sumo'], None, None))


def test_export_only_candidate_preserves_unrelated_manifest(tmp_path):
    import json
    import export_depart_speed_candidate_evidence as export
    portable = tmp_path / m.LOCAL / 'portable'; portable.mkdir(parents=True)
    for name in m.PORTABLE_NAMES:
        if name != 'SHA256SUMS': (portable / name).write_text('{}')
    evidence = tmp_path / 'evidence'; evidence.mkdir()
    old = {'result_id': 'UNRELATED', 'files': [{'source_path': 'do-not-read'}]}
    (evidence / 'EVIDENCE_MANIFEST.json').write_text(json.dumps({'results': [old]}))
    result = export.export(tmp_path)
    assert result['results'][0] == old and result['results'][1]['result_id'] == m.RESULT
    assert export.exporter.verify_evidence(tmp_path, {m.RESULT}) == []
