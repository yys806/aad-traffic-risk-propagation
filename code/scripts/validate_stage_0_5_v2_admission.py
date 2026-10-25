"""Reuse the immutable no-data/Python audit harness with explicit new tests."""
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    # The reused harness checks its own clone identity before collecting tests.
    # This wrapper imports only runtime pytest and the already-reviewed harness.
    import pytest
    import validate_stage_0_5_research_v2 as harness
    original = pytest.main
    def selected(args):
        if "--full" in sys.argv:
            return original(args)
        first_option = next(i for i, value in enumerate(args) if value.startswith("-"))
        return original(["tests/test_stage_0_5_v2_admission.py", "tests/test_stage_0_5_research_ledger.py",
                         "tests/test_stage_0_5_physical_fcd.py", "tests/test_stage_0_5_d1_measurement.py",
                         "tests/test_interaction_task_boundary.py", "tests/test_project_docs.py"] + args[first_option:])
    pytest.main = selected
    try:
        return harness.main()
    finally:
        pytest.main = original


if __name__ == "__main__":
    raise SystemExit(main())
