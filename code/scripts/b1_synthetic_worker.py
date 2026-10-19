"""Audited small subprocess fixture; never loads project data or SUMO."""
import json
import os
import sys
import time
from pathlib import Path

audit=None
if os.environ.get("AAD_B1_CAPSULE"):
    from riskprop.stage_0_5_b1_isolation import install_guard
    audit=install_guard(os.environ["AAD_B1_CAPSULE"])
kind=sys.argv[1];out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
if kind=="exit":sys.exit(3)
if kind=="missing":sys.exit(0)
if kind=="timeout":time.sleep(30)
if kind=="memory":
    allocation=bytearray(110*1024**2);time.sleep(3)
if kind=="disk":
    (out/"large.bin").write_bytes(b"x"*1_000_000);time.sleep(.5)
(out/"summary.json").write_text(json.dumps(dict(engineering_blockers=["synthetic_conservation"] if kind=="blocker" else [],
    diagnostic_warnings=["synthetic_inside_queue"] if kind=="warning" else [])))
