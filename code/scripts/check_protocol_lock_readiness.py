from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.protocol_lock import protocol_lock_readiness


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report protocol-lock blockers; never creates the lock itself."
    )
    parser.add_argument("--stage-0-2", dest="stage_0_2", type=Path, required=True)
    parser.add_argument("--stage-0-4", dest="stage_0_4", type=Path, required=True)
    parser.add_argument("--stage-0-5", dest="stage_0_5", type=Path, required=True)
    parser.add_argument("--stage-0-6", dest="stage_0_6", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = {}
    for name, path in (
        ("stage_0_2", args.stage_0_2),
        ("stage_0_4", args.stage_0_4),
        ("stage_0_5", args.stage_0_5),
        ("stage_0_6", args.stage_0_6),
    ):
        reports[name] = json.loads(path.read_text(encoding="utf-8"))
    result = protocol_lock_readiness(reports)
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["protocol_lock_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
