import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_stage_0_2_task_2_3_quality_robustness import ref_runs, oracle_check
from run_stage_0_2_task_2_2_kinematic_review import extract_risk_runs

def test_reference_splits_nonrisk_middle_and_boundaries():
    assert ref_runs([True, False, True], [False, True, True]) == [(0, 0), (2, 2)]
    assert ref_runs([True, True, True], [False, True, True]) == [(0, 2)]
    assert ref_runs([False, False], [False, False]) == []

def test_independent_oracle_random_combinations():
    assert oracle_check(np.random.default_rng(1234)) == 960

def test_canonical_extractor_matches_independent_reference():
    for mask, edge in [([True, False, True], [False, True, True]), ([True, True], [False, False]), ([False], [False])]:
        expected=ref_runs(mask,edge)
        got=extract_risk_runs(mask,edge)
        assert expected == [(x['start_index'],x['end_index']) for x in got]
