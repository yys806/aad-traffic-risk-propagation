"""Current B00 software regression in a separate no-data Git checkout."""
import json
import sys


def main():
    import pytest
    import validate_stage_0_5_research_v2 as harness
    original = pytest.main
    class Counts:
        def pytest_sessionfinish(self, session, exitstatus):
            reporter = session.config.pluginmanager.getplugin("terminalreporter")
            self.record = {k: len(reporter.stats.get(k, [])) for k in
                           ["passed", "failed", "skipped", "error", "deselected"]}
            self.record["exit_code"] = int(exitstatus)
    counts = Counts()
    def selected(args):
        if "--full" in sys.argv:
            return original(args, plugins=[counts])
        index = next(i for i, value in enumerate(args) if value.startswith("-"))
        names = ["b00_closure_v1", "native_capsule_v4", "b00_admission_v6", "admission_v3",
                 "v2_admission", "research_ledger", "linux_isolation"]
        return original(["tests/test_stage_0_5_"+n+".py" for n in names]+args[index:], plugins=[counts])
    pytest.main = selected
    try:
        status = harness.main()
        print("SOFTWARE_COUNTS="+json.dumps(counts.record, sort_keys=True))
        return status
    finally:
        pytest.main = original


if __name__ == "__main__":
    raise SystemExit(main())
