from pathlib import Path
import json,re,sys
work=Path(__file__).resolve().parent;clone=work/'software_clone'
raw=(work/'full_software_log/stdout').read_text(encoding='utf-8')
states=''.join(m[1] for m in re.finditer(r'(?m)^([.s]+)\s+\[',raw))
assert states.count('s')==16,(len(states),states.count('s'))
sys.path.insert(0,str(clone/'code/scripts'))
import pytest
import validate_stage_0_5_research_v2 as harness
original=pytest.main
class Collect:
    def pytest_collection_finish(self,session):self.names=[i.nodeid for i in session.items]
class Reasons:
    def __init__(self):self.rows=[]
    def pytest_runtest_logreport(self,report):
        if report.skipped:self.rows.append(dict(nodeid=report.nodeid,phase=report.when,reason=str(report.longrepr)))
collect=Collect();reasons=Reasons()
def selected(args):
    status=original(args+['--collect-only'],plugins=[collect])
    assert status==0 and len(collect.names)==len(states),(len(collect.names),len(states))
    nodes=[n for n,s in zip(collect.names,states) if s=='s']
    status=original(nodes+args[1:]+['-rs'],plugins=[reasons])
    assert len(reasons.rows)==16,reasons.rows
    out=clone/'code/tmp/v6_skip_reasons.json'
    out.open('x',encoding='utf-8').write(json.dumps(dict(status='Pass',skipped=16,skip_is_not_pass=True,reasons=reasons.rows),ensure_ascii=False,indent=2)+'\n')
    return status
pytest.main=selected
sys.argv=[sys.argv[0],'--full','--source-workspace',str(work.parents[2])]
raise SystemExit(harness.main())
