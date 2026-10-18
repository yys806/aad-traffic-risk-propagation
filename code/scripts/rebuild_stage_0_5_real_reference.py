"""Rebuild the approved Stage 0.5 R2 real-reference package.

This entry point consumes only the sealed Stage 0.2/0.3 inputs declared by
``write_formal_stage_0_5_reference_r2``.  It does not run SUMO or change any
scientific measurement rule.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.simulation_real_coverage import write_formal_stage_0_5_reference_r2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-rows-per-group", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260907)
    args = parser.parse_args()
    if args.max_rows_per_group <= 0:
        parser.error("--max-rows-per-group must be positive")
    output = write_formal_stage_0_5_reference_r2(
        repo_root=args.repo_root,
        output_dir=args.output,
        max_rows_per_group=args.max_rows_per_group,
        seed=args.seed,
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    print(json.dumps({"output": output.as_posix(), "audit": audit}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
