from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_stage_0_6_error_budget_v1 import build_budget,sampled_rho,write_budget,observed_quantization_sensitivity

def test_production_and_independent_integral_match_with_full_right_endpoint():
    coarse,_=sampled_rho(4.,.8,.1)
    fine,independent=sampled_rho(4.,.8,.01)
    assert fine==pytest.approx(independent,abs=1e-13)
    assert fine>coarse
    with pytest.raises(ValueError,match='right endpoint'):
        sampled_rho(4.,.83,.1)
    with pytest.raises(ValueError,match='collision'):
        sampled_rho(.4,.8,.1)

def test_all_error_sources_and_scientific_scope_are_retained():
    audit=build_budget()
    assert len(audit['cases'])==15 and len(audit['reconstruction_cases'])==120
    assert all(audit['groups'][k] for k in audit['group_bounds'])
    assert audit['delta_eq_fixture_candidate']==max(audit['group_bounds'].values())
    assert audit['joint_source_sum_bound']>=audit['delta_eq_fixture_candidate']
    assert audit['compound_bounds']['four_arm_DID']==4*audit['delta_eq_fixture_candidate']
    assert audit['scientific_approval'] is False
    assert audit['analytic_truth']['pass'] and audit['physical_path_truth']['pass']

def test_budget_is_exclusive_and_hashes_recompute(tmp_path):
    import json,hashlib
    output=tmp_path/'new';write_budget(output)
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['files']['audit.json']==hashlib.sha256((output/'audit.json').read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):write_budget(output)


def test_observed_sensitivity_reports_missing_and_boundary_support(tmp_path):
    import pandas as pd
    path=tmp_path/'states.parquet'
    pd.DataFrame(dict(net_gap_m=[10,1,1,1],closing_speed_mps=[2,.005,0,1],
        measurement_status=['valid','valid','not_applicable','missing'],ttc_valid=[True,True,False,False])).to_parquet(path)
    result=observed_quantization_sensitivity(path)
    assert result['valid_states']==2 and result['supported_states']==1
    assert result['excluded_boundary_states']==1
    assert result['higher99_absolute_rho_sensitivity']>0
    assert result['treatment_contrast_direction'].startswith('Unknown')
