"""Run only explicitly selected B1 tests after installing capsule protection."""
import os
import sys
import json
from pathlib import Path
from riskprop.stage_0_5_b1_isolation import install_guard
audit=install_guard(os.environ["AAD_B1_CAPSULE"])
import pytest
try:
    status=pytest.main(sys.argv[1:])
finally:
    (Path(os.environ["AAD_B1_CAPSULE"])/"preflight_test_access_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
raise SystemExit(1 if audit["denied"] else status)
