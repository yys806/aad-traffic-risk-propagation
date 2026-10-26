"""Targeted software checks in a no-data Git clone; never a native smoke."""
import json
from pathlib import Path
import sys


def main():
    import pytest
    import validate_stage_0_5_research_v2 as harness
    original=pytest.main
    class Counts:
        def pytest_sessionfinish(self,session,exitstatus):
            reporter=session.config.pluginmanager.getplugin("terminalreporter")
            self.record={k:len(reporter.stats.get(k,[])) for k in ["passed","failed","skipped","error","deselected"]}
            self.record["exit_code"]=int(exitstatus)
    counts=Counts()
    def selected(args):
        index=next(i for i,value in enumerate(args) if value.startswith("-"))
        names=["test_stage_0_5_native_capsule_v4","test_stage_0_5_linux_isolation","test_stage_0_5_admission_v3",
            "test_stage_0_5_v2_admission","test_stage_0_5_research_ledger","test_interaction_task_boundary","test_project_docs"]
        return original(["tests/"+n+".py" for n in names]+args[index:],plugins=[counts])
    pytest.main=selected
    try:
        status=harness.main()
        print("SOFTWARE_COUNTS="+json.dumps(counts.record,sort_keys=True))
        return status
    finally:pytest.main=original


if __name__=="__main__":raise SystemExit(main())
