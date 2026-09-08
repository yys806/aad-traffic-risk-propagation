from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.sumo_e00 import analyze_real_sumo_e00  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute E00 audits from sealed SUMO artifacts.")
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze_real_sumo_e00(args.package)
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
