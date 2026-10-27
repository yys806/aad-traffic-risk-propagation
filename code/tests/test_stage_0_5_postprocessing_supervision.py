"""Postprocessing coverage without changing resource thresholds or identity."""
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import stage_0_5_execution_v2 as execution

def test_fcd_heartbeat_preserves_every_record_and_parser_semantics(tmp_path,monkeypatch):
    path=tmp_path/'fcd.xml'
    path.write_text('<fcd-export>'+''.join(f'<timestep time="{i/10}"><vehicle id="v"/></timestep>' for i in range(8))+'</fcd-export>')
    clock=iter(i*.1 for i in range(40));monkeypatch.setattr(execution.time,'monotonic',lambda:next(clock))
    rows=[];beats=[]
    observer=SimpleNamespace(observe_fcd=lambda ident,t:rows.append((ident,t)))
    actual=execution.attach_FCD_observations(observer,path,heartbeat=lambda:beats.append(len(rows)))
    assert rows==[('v',i/10) for i in range(8)]
    assert actual['records_observed']==8 and actual['parse_complete']
    assert beats[0]==0 and beats[-1]==8 and len(beats)>=8

def test_fcd_heartbeat_error_is_not_hidden_or_converted_to_partial(tmp_path):
    path=tmp_path/'fcd.xml';path.write_text('<fcd-export/>')
    def failure():raise RuntimeError('resource_limit:wall')
    with pytest.raises(RuntimeError,match='resource_limit'):
        execution.attach_FCD_observations(None,path,allow_partial=True,heartbeat=failure)

def test_supervisor_serializes_probes_and_preserves_limit_failure(tmp_path):
    import threading
    active=[0];maximum=[0]
    def probe():
        import time
        active[0]+=1;maximum[0]=max(maximum[0],active[0]);time.sleep(.005);active[0]-=1
        return dict(wall_s=0,process_tree_rss_bytes=1,free_c_bytes=10,free_d_bytes=10,available_memory_bytes=10)
    scope=SimpleNamespace(check=lambda p:p)
    limits=dict(per_attempt_wall_s=1,process_tree_rss_bytes=10,task_output_bytes=10,min_free_c_bytes=0,min_free_d_bytes=0,min_available_memory_bytes=0)
    supervisor=execution.ResourceSupervisor(limits,scope,tmp_path,probe)
    threads=[threading.Thread(target=supervisor.observe) for _ in range(4)]
    for thread in threads:thread.start()
    for thread in threads:thread.join()
    assert maximum==[1] and len(supervisor.samples)==4
    supervisor.limits=dict(limits,process_tree_rss_bytes=0)
    with pytest.raises(RuntimeError,match='resource_limit'):
        supervisor.observe()
