"""Independent native sampler; software cases never launch a simulator."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import time
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from stage_0_5_linux_controller_v4 import ProcessResourceWatchdog


@pytest.mark.parametrize('record,status,failure',[
    ({'sample':{'wall_s':1}},0,None),
    ({'error':'resource_limit:rss'},256,'resource_limit:rss'),
    ({'sample':{'wall_s':1}},256,'resource_sampler_failed'),
])
def test_sampler_records_are_not_replaced_with_success(tmp_path,monkeypatch,record,status,failure):
    path=tmp_path/'samples.jsonl';path.write_text(json.dumps(record)+'\n')
    supervisor=SimpleNamespace(samples=[],last=None)
    watcher=ProcessResourceWatchdog(supervisor,path);watcher.pid=99;watcher.status=status
    watcher.close(raise_on_failure=False)
    assert watcher.failure==failure
    assert supervisor.samples==([record['sample']] if 'sample' in record else [])
    watcher.close(raise_on_failure=False)
    if failure:
        with pytest.raises(RuntimeError):watcher.close()


def test_sampler_missing_log_rejects_instead_of_inventing_samples(tmp_path):
    watcher=ProcessResourceWatchdog(SimpleNamespace(samples=[],last=None),tmp_path/'absent')
    watcher.pid=99;watcher.status=0
    with pytest.raises(RuntimeError,match='FileNotFoundError'):watcher.close()


@pytest.mark.skipif(sys.platform!='linux',reason='real fork/GIL check requires Linux; no SUMO')
def test_real_sampler_continues_while_controller_holds_gil(tmp_path):
    import ctypes
    owner=os.getpid();began=time.monotonic()
    class Supervisor:
        samples=[];last=None
        def observe(self):
            self.last={'wall_s':time.monotonic()-began,'observed_controller_pid':owner}
            return self.last
    supervisor=Supervisor();watcher=ProcessResourceWatchdog(supervisor,tmp_path/'sampler.jsonl',interval_s=.05)
    watcher.start()
    try:
        time.sleep(.1)
        libc=ctypes.PyDLL(None);libc.usleep.argtypes=[ctypes.c_uint]
        libc.usleep(800000)  # Unlike CDLL/sleep, PyDLL retains this process GIL.
        watcher.observe()
    finally:watcher.close()
    samples=supervisor.samples
    assert len(samples)>=10
    assert all(s['observed_controller_pid']==owner for s in samples)
    assert max(b['wall_s']-a['wall_s'] for a,b in zip(samples,samples[1:]))<=.5
    with pytest.raises(ChildProcessError):os.waitpid(watcher.pid,os.WNOHANG)
