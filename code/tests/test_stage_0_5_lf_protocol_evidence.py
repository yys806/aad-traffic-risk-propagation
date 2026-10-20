"""Portable candidate evidence must reject resealed scientific promotion."""
import importlib.util
import json
from pathlib import Path
import shutil
import pytest
from riskprop.stage_0_5_lf_protocol import exposure_audit

ROOT=Path(__file__).resolve().parents[2]
RESULT=ROOT/'evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1'

def tool():
    s=importlib.util.spec_from_file_location('protocol_pack',ROOT/'code/scripts/package_stage_0_5_lf_protocol.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_actual_portable_protocol_is_candidate_only():
    r=tool().verify(RESULT)
    assert r['counts']['through_confirmation']==86 and r['counts']['through_end']==83
    assert r['new_SUMO_runs']==0 and r['budget_remaining']==5

@pytest.mark.parametrize('kind',['count','rate','margin','Gate','warmup','budget','source_scope','core','local_reference','subtype','time_window'])
def test_resealed_scientific_or_measurement_promotion_rejected(tmp_path,kind):
    for p in RESULT.iterdir():shutil.copyfile(p,tmp_path/p.name)
    name=dict(count='attribution_summary.json',rate='attribution_summary.json',margin='scientific_admission_table.json',Gate='audit.json',warmup='warmup_candidate_analysis.json',
        budget='execution_ledger.json',source_scope='approved_reference_support.json',core='local_measurement_candidate.json',local_reference='approved_reference_support.json',
        subtype='event_attribution_audit.csv',time_window='temporal_boundary_audit.json')[kind]
    p=tmp_path/name
    if kind=='subtype':p.write_text(p.read_text().replace(',True,True,True,False,',',True,True,True,True,',1))
    else:
        d=json.loads(p.read_text(encoding='utf-8'))
        if kind=='count':d['counts']['through_confirmation']=83
        elif kind=='rate':d['candidate_rates']['onset']['evaluable_vehicle_s']=42404.3
        elif kind=='margin':d['metrics'][0]['scientific_margin']=.95
        elif kind=='Gate':d['reality_coverage_accepted']=True
        elif kind=='warmup':d['formal_warmup_s']=120.
        elif kind=='budget':d['targeted_remaining']=8
        elif kind=='source_scope':d['actual_validation_window_reads']=1
        elif kind=='core':d['core_unchanged']['minimum_span_s']=.1
        elif kind=='local_reference':d['windows'][0]['formal_local_event_count']=543
        elif kind=='time_window':d['windows'][0]['confirmation_spatial_same_onset_time_count']=83
        p.write_text(json.dumps(d),encoding='utf-8')
    tool().seal(tmp_path)
    with pytest.raises(ValueError):tool().verify(tmp_path)

def test_no_leader_quality_vocabulary_does_not_fabricate_exposure():
    import pandas as pd
    m=pd.DataFrame([dict(vehicle_id='v',incarnation_id='r|v',leader_id=None,leader_incarnation_id=None,time_s=i*.1,observation_index=i,
        edge_id='main_1',lane_id='main_1_0',position_m=60.,in_local=True,reliable_following_eligible=False,measurement_status='not_applicable',
        ttc_valid=False,ttc_s=float('nan'),identity_break=False,observation_gap=False) for i in range(3)])
    a=exposure_audit(m);m['measurement_status']='missing';b=exposure_audit(m)
    assert a['local_both_s']==b['local_both_s']==0.
    assert a['quality_by_local_point']!=b['quality_by_local_point']
