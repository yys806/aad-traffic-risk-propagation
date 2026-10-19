"""Independent truths for the positive-only admission chain; synthetic inputs."""
from copy import deepcopy
import inspect
import pytest
from riskprop.stage_0_5_positive_near_zero import classify_edge,admission,check_plan
from riskprop.stage_0_5_near_zero_observability import SOURCE_PROOF_KEYS

def states(u=2e-6):
    # At t=.05 a prior decision has reached v0=.5. Its carried acceleration
    # independently determines u. Position is an independent ballistic truth.
    a=dict(run_id="p",vehicle_id="v",incarnation_id="p|v",time_s=.05,speed_mps=.5,
        acceleration_mps2=(u-.5)/.05,position_m=10.,last_action_time_s=0.,edge_id="e",lane_id="e_0",
        traci_vehicle_control=False,numerical_config_verified=True,input_has_stops=False,remaining_stops=[],route_edges=["e","f"],route_index=0)
    b=dict(a,time_s=.1,speed_mps=0.,position_m=10.0125,acceleration_mps2=-10.)
    return a,b,{k:True for k in SOURCE_PROOF_KEYS}

def test_all_independent_links_are_required_for_target_exact():
    a,b,p=states();r=classify_edge(a,b,p,bindings_verified=True)
    assert r['classification']=='Exact Pass' and r['target_exact_pass']
    assert all(r['admission_links'].values()) and r['u_pre']>0
    assert r['u_final']==0 and r['expected_dx_m']==pytest.approx(.0125)

@pytest.mark.parametrize('u',[1e-6,4.8e-6])
def test_actual_interior_values_not_nominal_maxspeed_define_target(u):
    a,b,p=states(u);r=classify_edge(a,b,p,bindings_verified=True)
    assert r['target_exact_pass'] and r['u_pre']==pytest.approx(u)

@pytest.mark.parametrize('u',[-2e-6,0.,5e-6,5.2e-6,8e-6])
def test_negative_zero_boundary_above_cannot_satisfy_positive_target(u):
    # For these controls make a valid independent displacement/public value.
    from riskprop.stage_0_5_stopping_observability import expected_displacement
    a,b,p=states(u)
    # Use v0=0 for the exact boundary to avoid cancellation ambiguity.
    if abs(u)==5e-6:a.update(speed_mps=5e-6,acceleration_mps2=0.)
    final=0. if abs(u)<5e-6 else u
    b.update(speed_mps=max(final,0.),position_m=a['position_m']+expected_displacement(a['speed_mps'],final,.05))
    r=classify_edge(a,b,p,bindings_verified=True)
    assert not r['target_exact_pass']

def test_unknown_context_stays_unknown_despite_zero_end_and_matching_dx():
    a,b,p=states();p['fresh_vehicle_lifecycle']=False
    r=classify_edge(a,b,p,bindings_verified=True)
    assert r['classification']=='Near-Zero Context Unresolved' and r['residual_m'] is None
    b['position_m']+=.00000001
    assert classify_edge(a,b,p,bindings_verified=True)['context'] is None

def test_actual_public_nonzero_cannot_be_accepted_via_auxiliary_tolerance():
    a,b,p=states();b['speed_mps']=1e-10
    r=classify_edge(a,b,p,bindings_verified=True)
    assert r['classification']=='Engineering Blocker' and not r['target_exact_pass']

@pytest.mark.parametrize('key,val',[('last_action_time_s',None),('incarnation_id','other'),('time_s',.2),('traci_vehicle_control',True),('traci_vehicle_control',None),('numerical_config_verified',False)])
def test_shared_errors_block_not_target_pass(key,val):
    a,b,p=states();b[key]=val;r=classify_edge(a,b,p,bindings_verified=True)
    assert r['blocker'] and not r['target_exact_pass']

def test_missing_SHA_is_global_even_when_motion_matches():
    a,b,p=states();r=classify_edge(a,b,p,bindings_verified=False)
    assert r['blocker']=='source_input_binding_unverified'

def test_edge_change_is_not_fake_zero_residual():
    a,b,p=states();b.update(edge_id='f',lane_id='f_0',position_m=.1)
    r=classify_edge(a,b,p,bindings_verified=True)
    assert r['classification']=='Not Evaluable' and r['residual_m'] is None

def test_wrong_position_and_wrong_speed_cannot_create_target():
    a,b,p=states();b['position_m']+=.01
    assert classify_edge(a,b,p,bindings_verified=True)['blocker']=='exact_displacement_violation'

def test_decision_stop_is_only_bounded_and_not_target():
    a,b,p=states();a['time_s']=0.;b['time_s']=.05;b['position_m']=10.005
    r=classify_edge(a,b,p,bindings_verified=True)
    assert r['classification']=='Bounded Consistency Only' and not r['target_exact_pass']
    assert r['residual_m'] is None

def test_admission_distinguishes_observed_target_and_unattempted_runs():
    assert not admission([dict(target_exact_count=0,engineering_blockers=[])])['target_branch_verified']
    r=admission([dict(target_exact_count=1,engineering_blockers=[])])
    assert r['target_branch_verified'] and not r['C_D_allowed'] and not r['main_matrix_allowed']
    assert not admission([dict(target_exact_count=1,engineering_blockers=['clock'])])['target_branch_verified']

def test_plan_cannot_expand_into_integration_or_search():
    p=dict(version='b12p-plan-v1',main_matrix_allowed=False,C_D_allowed=False,runs=[dict(kind='P1',duration_s=2.,seed=20261019)])
    check_plan(p)
    for change in [dict(C_D_allowed=True),dict(main_matrix_allowed=True),dict(runs=[dict(kind='D',duration_s=2.,seed=20261019)]),dict(runs=[dict(kind='P1',duration_s=31.,seed=20261019)])]:
        bad=deepcopy(p);bad.update(change)
        with pytest.raises(PermissionError):check_plan(bad)

def test_plan_duplicate_or_sixth_probe_rejected():
    p=dict(version='b12p-plan-v1',main_matrix_allowed=False,C_D_allowed=False,runs=[dict(kind='P1',duration_s=2.,seed=20261019)]*2)
    with pytest.raises(PermissionError):check_plan(p)

def test_no_inverse_speed_from_displacement_interface():
    from riskprop.stage_0_5_near_zero_observability import candidate_speeds,context_from_public
    assert 'position' not in inspect.signature(candidate_speeds).parameters
    a,b,p=states();r=classify_edge(a,b,p,bindings_verified=True)
    b['position_m']+=10
    wrong=classify_edge(a,b,p,bindings_verified=True)
    assert wrong['u_pre']==r['u_pre'] and wrong['context_evidence']==r['context_evidence']

@pytest.mark.parametrize('command',['C','D','phase1','freeze-integration'])
def test_no_integration_or_main_dispatch(tmp_path,command):
    from riskprop.stage_0_5_positive_runtime import dispatch
    with pytest.raises(PermissionError,match='No integration'):
        dispatch(tmp_path,tmp_path,command)

def test_worker_has_no_vehicle_signal_or_type_control_calls():
    import ast
    from riskprop import stage_0_5_positive_worker as m
    tree=ast.parse(inspect.getsource(m));calls=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and ast.unparse(n.func.value).endswith(('vehicle','vehicletype','trafficlight')):
            calls.append(n.func.attr)
    assert calls and all(not c.startswith(('set','add','remove','move','change','replace','resume','reroute')) for c in calls)
