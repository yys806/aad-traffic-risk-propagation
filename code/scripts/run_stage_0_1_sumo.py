from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.formal_artifacts import append_failure_record  # noqa: E402
from riskprop.stage_0_1_sumo import run_real_sumo_stage_0_1  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the minimal real-SUMO Stage 0.1 four-cell package.")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int, default=2026080701)
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [sys.executable, *sys.argv]
    try:
        package = run_real_sumo_stage_0_1(
            args.output_root,
            run_id=args.run_id,
            seed=args.seed,
            repo_root=args.repo_root,
            command=command,
        )
    except Exception as error:
        append_failure_record(
            args.output_root,
            experiment_id="stage_0_1",
            run_id=args.run_id,
            stage="real_sumo",
            error=error,
            exit_code=1,
            command=command,
        )
        print(f"Stage 0.1 real SUMO run failed: {error}", file=sys.stderr)
        return 1
    print(package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
