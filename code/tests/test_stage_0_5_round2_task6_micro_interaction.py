from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/scripts'))
import analyze_stage_0_5_round2_task6_micro_interaction as task


def states(times=(0., .1, .2, .3), leader='l'):
    rows = []
    for j, t in enumerate(times):
        rows.append(dict(trajectory_id='f', vehicle_id='f', leader_trajectory_id=leader, time_s=t,
                         source_member='source', source_period='period', diagnostic_clock_anchor_ms=1000,
                         global_time_ms=1000+int(round(t*1000)), frame_id=int(round(t*10)),
                         identity_break=False, observation_gap=False, identity_uncertain=False,
                         leader_matched=True, leader_identity_uncertain=False, lane_id='1',
                         speed_mps=10., acceleration_mps2=0., y_m=10.+10*t,
                         net_gap_m=5.-2*t, closing_speed_mps=2., ttc_s=(5.-2*t)/2,
                         measurement_status='valid', ttc_valid=True, missing_reason=''))
    return pd.DataFrame(rows)


def test_joint_dependence_changes_tail_with_identical_marginals():
    d = task.normalize(states((0., .1)), True)
    d['net_gap_m'] = [2., 6.]
    d['closing_speed_mps'] = [1., 3.]
    d['ttc_s'] = d.net_gap_m/d.closing_speed_mps
    a = task.joint_metrics(d, 'a', 'source')
    d['closing_speed_mps'] = [3., 1.]
    d['ttc_s'] = d.net_gap_m/d.closing_speed_mps
    b = task.joint_metrics(d, 'b', 'source')
    assert a['joint_tail_fraction_positive'] == 0
    assert b['joint_tail_fraction_positive'] == .5
    assert a['product_marginal_tail_fraction'] == b['product_marginal_tail_fraction'] == .25


@pytest.mark.parametrize('flag', ['identity_break', 'observation_gap', 'identity_uncertain'])
def test_explicit_break_cuts_context(flag):
    d = states()
    d.loc[2, flag] = True
    d = task.normalize(d, True)
    context = task.Context(d).segment('f', .3, 1)
    assert context.time_s.min() >= .2


def test_observation_gap_is_not_filled():
    d = task.normalize(states((0., .1, .3)), True)
    assert len(task.Context(d).segment('f', .3, 1)) == 1


def test_duplicate_onset_records_fail_closed():
    d = states()
    with pytest.raises(ValueError, match='Ambiguous'):
        task.normalize(pd.concat([d, d.iloc[[0]]]), True)


def test_no_approximate_onset_matching():
    ctx = task.Context(task.normalize(states(), True))
    assert ctx.exact('f', .10001) is None


def test_unknown_leader_context_is_not_zero_transition():
    ctx = task.Context(task.normalize(states(), True))
    result, _, _ = ctx.describe(1, 1)
    assert result['leader_onset_matched'] is False
    assert result['onset_leader_lane_change'] is None
    assert result['new_leader_lane_entry_signature'] is None


def test_pair_residual_and_leader_switch_have_distinct_support():
    d = states()
    d.loc[2:, 'leader_trajectory_id'] = 'new_leader'
    d = task.normalize(d, True)
    assert d.loc[1, '_gap_residual'] == pytest.approx(0.)
    assert d.loc[2, '_ls']
    assert pd.isna(d.loc[2, '_gap_residual'])


def test_histogram_conserves_all_positive_closing_states():
    d = task.normalize(states(), True)
    h = task.joint_histogram(d, 'a', 'source')
    assert sum(r['rows'] for r in h) == 4
    assert sum(r['risk_point_rows'] for r in h) == 0


def test_rank_correlation_does_not_require_scipy():
    d = task.normalize(states(), True)
    d['closing_speed_mps'] = [1., 2., 3., 4.]
    d['ttc_s'] = d.net_gap_m / d.closing_speed_mps
    assert task.joint_metrics(d, 'a', 'source')['spearman_gap_positive_closing'] == pytest.approx(-1.)


def test_sumo_physical_quality_uses_native_coordinate_and_no_edge_reset():
    d = states()
    d['incarnation_id'] = 'f'
    d['reliable_following_eligible'] = True
    d['native_position_m'] = 10+10*d.time_s
    d['native_lane_id'] = 'main_0_0'
    d['y_m'] = 30+30*d.time_s
    d.loc[2:, 'native_lane_id'] = 'main_1_0'
    d.loc[2:, 'native_position_m'] -= 12
    result = task.normalize(d, False)
    assert result.loc[1, '_position_speed_residual'] == pytest.approx(0.)
    assert pd.isna(result.loc[2, '_position_speed_residual'])


def test_historical_bundle_mismatch_is_explicit_and_never_resealed(tmp_path):
    (tmp_path/'payload.json').write_text('{}')
    (tmp_path/'SHA256SUMS').write_text('0'*64+'  payload.json\n'+'1'*64+'  missing.json\n')
    before = (tmp_path/'SHA256SUMS').read_bytes()
    with pytest.raises(ValueError):
        task.verify_bundle(tmp_path)
    result = task.verify_bundle(tmp_path, strict=False)
    assert result['pass'] is False and len(result['mismatches']) == 2
    assert result['verified_payload_files'] == []
    assert (tmp_path/'SHA256SUMS').read_bytes() == before


def test_manifest_paths_cannot_escape_package(tmp_path):
    import verify_stage_0_5_round2_task6_micro_interaction as verify
    with pytest.raises(ValueError):
        verify.safe_file(tmp_path, '../other.json')


def test_partial_block_uses_observed_support():
    d = task.normalize(states((30.2, 30.3, 30.4)), True)
    r = task.macro_cells(d, pd.Series(True, index=d.index), 'a', 'source', 30.2, 30.5)[0]
    assert r['effective_duration_s'] == pytest.approx(.3)
    assert r['density_veh_km_lane'] == pytest.approx(1/.75)


def test_nonrisk_control_exclusion_includes_full_event_and_buffer():
    d = task.normalize(states((0., .1, .2, 5.)), True)
    e = pd.DataFrame([dict(trajectory_id='f', event_start_s=.1, event_end_s=.2)])
    assert task.mark_event_proximity(d, e).tolist() == [False, False, False, True]


@pytest.mark.parametrize('event,args', [('subprocess.Popen', ()), ('socket.connect', ()), ('open', ('x/0820_0835.parquet', 'r'))])
def test_offline_guard_denies_forbidden_access(event, args):
    with pytest.raises(RuntimeError):
        task.offline_guard(event, args)

def test_task6_export_accepts_only_explicit_aggregate_csvs(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("task6_export", ROOT / "code/scripts/export_project_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pairs = module._source_pairs()[task.RESULT_ID]
    for source, name in pairs:
        assert source.startswith("evidence/results/" + task.RESULT_ID + "/")
        path = tmp_path / name
        path.write_text("aggregate fixture", encoding="utf-8")
        module._validate_source(path)
    raw = tmp_path / "raw_trajectory.csv"
    raw.write_text("vehicle_id,time_s", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported evidence"):
        module._validate_source(raw)
