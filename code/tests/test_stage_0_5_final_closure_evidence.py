"""Portable final-closure evidence must reject any resealed scientific promotion."""
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / 'evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1'


def tool():
    spec = importlib.util.spec_from_file_location('closure_pack', ROOT / 'code/scripts/package_stage_0_5_final_closure.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_evidence(tmp_path):
    for path in RESULT.iterdir():
        if path.is_file():
            shutil.copyfile(path, tmp_path / path.name)
    return tmp_path


def test_actual_portable_closure_is_evidence_insufficient():
    result = tool().verify(RESULT)
    assert result['passed'] is True
    assert result['real_local_events'] == {'us101__0750_0805': 147, 'us101__0805_0820': 216}
    assert result['new_SUMO_runs'] == 2 and result['budget_remaining'] == 3
    assert result['five_layer'] == 'Evidence Insufficient'
    assert result['state_support'] == 'EvidenceInsufficient_StateSupport'
    assert result['scientific_delta'] == 'Awaiting Researcher Decision'
    assert result['stage_0_5_gate'] == 'pending_simulation_sample'


def test_verifier_entrypoint_matches():
    spec = importlib.util.spec_from_file_location('closure_verify', ROOT / 'code/scripts/verify_stage_0_5_final_closure.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.verify(RESULT)['passed'] is True


@pytest.mark.parametrize('kind', ['rate', 'counts', 'gate', 'state_support', 'layers', 'delta', 'budget', 'isolation',
                                  'reference_status', 'decision_package'])
def test_resealed_promotion_rejected(tmp_path, kind):
    copy_evidence(tmp_path)
    name = dict(rate='real_local_reference_summary.json', counts='real_local_reference_summary.json',
                gate='audit.json', state_support='state_support_verdict.json', layers='five_layer_admission.json',
                delta='delta_h_basis_audit.json', budget='execution_ledger.json', isolation='isolation_evidence.json',
                reference_status='audit.json', decision_package='researcher_decision_package.json')[kind]
    path = tmp_path / name
    data = json.loads(path.read_text(encoding='utf-8'))
    if kind == 'rate':
        data['us101__0750_0805']['interior']['rate_per_evaluable_vehicle_hour'] = 20.0
    elif kind == 'counts':
        data['us101__0750_0805']['interior']['counts']['onset'] = 150
    elif kind == 'gate':
        data['reality_coverage_accepted'] = True
    elif kind == 'state_support':
        data['all_targets_inside_envelope'] = True
        data['verdict'] = 'StateSupported'
    elif kind == 'layers':
        data['conjunctive_verdict'] = 'Pass'
        data['approved_during_task'] = True
    elif kind == 'delta':
        data['status'] = 'criterion_satisfied'
        data['independent_evidence_available']['measurement_system_error_bound'] = True
    elif kind == 'budget':
        data['remaining_after_task'] = 5
    elif kind == 'isolation':
        data['third_window_access'] = True
    elif kind == 'reference_status':
        data['formal_local_P2'] = 'Unresolved'
    else:
        data['status'] = 'Approved'
    path.write_text(json.dumps(data), encoding='utf-8')
    tool().seal(tmp_path)
    with pytest.raises(ValueError):
        tool().verify(tmp_path)


def test_stale_manifest_after_edit_is_rejected(tmp_path):
    copy_evidence(tmp_path)
    path = tmp_path / 'audit.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['state_support'] = 'StateSupported'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError):
        tool().verify(tmp_path)
