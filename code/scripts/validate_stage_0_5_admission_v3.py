"""No-data V3 software checks using the reviewed parent audit harness."""
import sys


def main():
    import pytest
    import validate_stage_0_5_research_v2 as harness
    original = pytest.main
    def selected(args):
        if "--full" in sys.argv:
            return original(args)
        i = next(i for i,v in enumerate(args) if v.startswith("-"))
        return original(["tests/test_stage_0_5_admission_v3.py","tests/test_stage_0_5_v2_admission.py",
            "tests/test_stage_0_5_research_ledger.py","tests/test_stage_0_5_d1_measurement.py",
            "tests/test_stage_0_5_physical_fcd.py","tests/test_interaction_task_boundary.py","tests/test_project_docs.py"]+args[i:])
    pytest.main=selected
    try: return harness.main()
    finally: pytest.main=original


if __name__=="__main__": raise SystemExit(main())
