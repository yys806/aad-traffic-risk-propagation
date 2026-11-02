"""Task8-specific invariants; no production inputs or historical run mutation."""
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import p2_task8_support_experiment as s

def test_source_signature_does_not_wait_for_legacy_native_inequality():
    raw={'t':np.array([29.95,30.,30.05,30.1]),'v':np.array([[10.],[10.],[9.775],[9.55]]),
         'a':np.array([[0.],[0.],[-4.5],[-4.5]])}
    assert s.physical_source_interval(raw,{'actuated_source':'s0','source_execution':30.,'actual_source_onset':[31.75,31.8]})==[30.,30.05]

def test_missing_source_signature_is_unknown_not_planned_time():
    raw={'t':np.array([29.95,30.,30.05]),'v':np.ones((3,1))*10,'a':np.zeros((3,1))}
    assert s.physical_source_interval(raw,{'actuated_source':'s0','source_execution':30.}) is None
    assert s.physical_source_interval(raw,{'actuated_source':None}) is None

def test_truth_span_requires_full_second_and_cannot_start_after_monitor():
    t=np.arange(1000)/20+.05
    assert not s.spans(t,(t>=35)&(t<36))['positive']
    assert s.spans(t,(t>=45.5)&(t<=47))['positive']
    assert not s.spans(t,(t>=47)&(t<=49))['positive']

def test_micro_truth_does_not_stitch_different_entities():
    t=np.arange(1000)/20+.05;v=np.ones((1000,20))*10
    v[(t>=35)&(t<=35.6),3]=8;v[(t>=35.65)&(t<=36.25),4]=8
    x=np.tile(2100-np.arange(20)*15,(1000,1))+np.cumsum(v*.05,axis=0)
    r=s.measures({'t':t,'v':v,'x':x,'lane':np.zeros_like(v,int)})
    assert not r['micro']['a1']['positive']

def test_round_namespaces_are_distinct_and_reproducible():
    design=[dict(density='low',condition='MAX',amplitude=10.,hold=12.,n=8)]
    first=s.units_for(design,1);second=s.units_for(design,2)
    assert first==s.units_for(design,1)
    assert not {u['sumo_seed'] for u in first}&{u['sumo_seed'] for u in second}
    assert len({u['dependency_block'] for u in first+second})==16

def test_failure_labels_keep_unknown_and_valid_hashes():
    unit={'unit_id':'failed_fixture','density':'low','condition':'MAX'}
    labels=s.hash_labels(s.failed_labels(unit,'startup failed'))
    assert len(labels)==3 and all(r['state_truth']=='unknown' and r['onset_allowed_set'] is None and len(r['label_hash'])==64 for r in labels)


def test_ideal_native_response_chain_cannot_supply_missing_W8():
    from analyze_p2_task8_support import witness
    t=np.arange(1000)/20+.05;v=np.ones((1000,3))*10
    v[t>=32,1]=8
    raw={'t':t,'v':v,'a':np.zeros_like(v),'x':np.ones_like(v)*2000,
         'gap':np.ones_like(v)*10,'lane':np.zeros_like(v,int),'leader':np.tile([-1,0,-1],(1000,1))}
    audit={'unit_id':'fixture','status':'COMPLETE','density':'low','condition':'MAX','actuated_source':'s0',
           'specified_source':'s0','actual_source_onset':[30.,30.05],'count':2}
    result=witness(raw,audit,{'terminal_entity':1,'state_truth':'positive','native_target_verified':True})
    assert result['Observed'] and not result['Qualified'] and result['W8']=='Unknown'


def test_independent_binomial_cdf_matches_enumerated_small_case():
    from verify_p2_task7_results import independent_cdf
    assert independent_cdf(-1,4,.5)==0
    assert independent_cdf(1,4,.5)==pytest.approx(5/16)
    assert independent_cdf(4,4,.5)==pytest.approx(1)
