from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/scripts'))
import analyze_stage_0_5_post_r2_task8_kinematic_mechanism as task


@pytest.mark.parametrize('af,al,c0',[(0,0,2),(.4,0,0),(0,-.4,0),(-.3,-.8,-1)])
def test_trapezoid_exact_signed_linear_speed_components(af,al,c0):
    t=np.arange(51)/10
    vf=10+c0+af*t
    vl=10+al*t
    g=50-c0*t-.5*(af-al)*t*t
    d=task.decompose(t,g,vf,vl)
    assert d['C_initial_m']==pytest.approx(5*c0)
    assert d['C_f_m']==pytest.approx(12.5*af)
    assert d['C_l_m']==pytest.approx(-12.5*al)
    assert d['R_m']==pytest.approx(0,abs=1e-12)


def test_residual_keeps_position_speed_inconsistency_visible():
    t=np.arange(51)/10
    d=task.decompose(t,30-2*t+.2*t,np.full(51,12),np.full(51,10))
    assert d['R_m']==pytest.approx(-1)


@pytest.mark.parametrize('bad',['missing','gap','nan'])
def test_no_missing_observation_or_irregular_clock_can_be_filled(bad):
    t=np.arange(51)/10
    g=np.full(51,30.)
    if bad=='missing':
        t=t[:-1]
    elif bad=='gap':
        t[20]+=.01
    else:
        g[20]=np.nan
    with pytest.raises(ValueError):
        task.decompose(t,g,np.full(51,10),np.full(51,10))


def pair():
    rows=[]
    for role,speed in [('f',10.),('l',8.)]:
        for tick in range(51):
            rows.append(dict(trajectory_id=role,vehicle_id=role,leader_trajectory_id='l' if role=='f' else 'z',
                             time_s=tick/10,source_member='member',source_period='period',
                             diagnostic_clock_anchor_ms=1000,global_time_ms=1000+tick*100,frame_id=tick,
                             leader_frame_id=tick,identity_break=False,observation_gap=False,identity_uncertain=False,
                             leader_matched=True,leader_identity_uncertain=False,lane_id='1',speed_mps=speed,
                             acceleration_mps2=0.,y_m=speed*tick/10,net_gap_m=30-2*tick/10,
                             closing_speed_mps=2.,ttc_s=15-tick/10,measurement_status='valid',ttc_valid=True))
    return pd.DataFrame(rows)


def test_complete_fixed_pair_integrates_all_51_observations():
    d,p=task.Precursors(pair(),True).sample('f',5.)
    assert d['strict'] and d['C_m']==pytest.approx(10)
    assert len(p)==51


def test_leader_switch_is_not_spliced_into_full_decomposition():
    raw=pair()
    raw.loc[raw.trajectory_id.eq('f')&raw.time_s.lt(2),'leader_trajectory_id']='old'
    d,p=task.Precursors(raw,True).sample('f',5.)
    assert not d['strict'] and d['status']=='leader_changed'
    assert 'C_m' not in d
    assert p.loc[p.relative_time_s.lt(-3),'fixed_pair_gap_m'].isna().all()


@pytest.mark.parametrize('flag',['identity_break','observation_gap','identity_uncertain'])
def test_explicit_flags_block_full_pair_decomposition(flag):
    raw=pair()
    raw.loc[raw.trajectory_id.eq('f')&raw.time_s.eq(2),flag]=True
    d,_=task.Precursors(raw,True).sample('f',5.)
    assert not d['strict']


def test_same_pair_lane_change_is_classified_separately_without_formal_lane_filter():
    raw=pair()
    raw.loc[raw.time_s.ge(2),'lane_id']='2'
    d,_=task.Precursors(raw,True).sample('f',5.)
    assert d['strict'] and d['status']=='complete_fixed_pair_with_lane_change'


def test_leader_frame_mismatch_remains_unknown():
    raw=pair()
    raw.loc[raw.trajectory_id.eq('f')&raw.time_s.eq(2),'leader_frame_id']=999
    d,_=task.Precursors(raw,True).sample('f',5.)
    assert not d['strict'] and d['status']=='pair_timestamp_or_frame_unmatched'


def test_anchor_cannot_be_silently_snapped_to_nearby_time():
    d,_=task.Precursors(pair(),True).sample('f',5.001)
    assert d['status']=='anchor_off_grid' and not d['strict']


def test_offline_guard_blocks_simulation_and_windows_private_paths():
    with pytest.raises(PermissionError):
        task.offline_guard('subprocess.Popen',('sumo',))
    for path in ['D:/shen/OB/private.txt','D:/x/0820_0835.parquet','D:/x/locked_holdout/a']:
        with pytest.raises(PermissionError):
            task.offline_guard('open',(path,))


def test_task8_portable_registration_is_unique_and_complete():
    import export_project_evidence as exporter
    pairs=exporter._source_pairs()[task.OUT.name]
    names=[name for _,name in pairs]
    assert len(names)==len(set(names))==28
    assert {'event_precursor_decomposition.csv','control_precursor_decomposition.csv',
            'source_bindings.json','validation_record.json','manifest.json','SHA256SUMS'} <= set(names)
    assert all(source==f'evidence/results/{task.OUT.name}/{name}' for source,name in pairs)


def test_task8_derived_csvs_pass_existing_portable_validation(tmp_path):
    import export_project_evidence as exporter
    for _,name in exporter._source_pairs()[task.OUT.name]:
        if name.endswith('.csv'):
            path=tmp_path/name
            path.write_text('scope,n\nexample,1\n',encoding='utf-8')
            exporter._validate_source(path)


def test_task8_export_does_not_relax_raw_identity_or_size_guards(tmp_path):
    import export_project_evidence as exporter
    for name in ['raw_trajectories.csv','sealed_sampling_key.json']:
        path=tmp_path/name
        path.write_text('{}',encoding='utf-8')
        with pytest.raises(ValueError):
            exporter._validate_source(path)
    large=tmp_path/'event_precursor_decomposition.csv'
    large.write_bytes(b'x'*(exporter.MAX_FILE_BYTES+1))
    with pytest.raises(ValueError,match='exceeds'):
        exporter._validate_source(large)
