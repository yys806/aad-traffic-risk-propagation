from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.e01_validation import write_e01_prelock_validation


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run preliminary E01 truth checks; never writes a protocol lock."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = write_e01_prelock_validation(args.output)
    print((output / "audit.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
