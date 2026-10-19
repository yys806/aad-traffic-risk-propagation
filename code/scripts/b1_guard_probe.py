"""Negative access probe uses absent synthetic paths, never real restricted data."""
import json
import sys
from pathlib import Path
from riskprop.stage_0_5_b1_isolation import install_guard

batch=Path(sys.argv[1]).resolve();audit=install_guard(batch)
results=[]
for name in ["us101__0820_0835.json","locked_holdout.json","historical_event_characteristics.parquet"]:
    fake=batch.parent/("B1_SYNTHETIC_FORBIDDEN_"+name)
    try:
        fake.read_bytes();results.append(dict(path=str(fake),refused=False))
    except PermissionError:results.append(dict(path=str(fake),refused=True,before_filesystem_read=True))
(batch/"guard_probe_result.json").write_text(json.dumps(dict(cases=results,audit=audit),indent=2),encoding="utf-8")
if not all(x["refused"] for x in results):sys.exit(1)
