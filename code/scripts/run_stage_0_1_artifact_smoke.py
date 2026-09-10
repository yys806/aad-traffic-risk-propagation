from __future__ import annotations

import argparse
import sys
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.formal_artifacts import append_failure_record  # noqa: E402
from riskprop.formal_runner import run_artifact_smoke  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a sealed Stage 0.1 artifact smoke run without science claims."
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [sys.executable, *sys.argv]
    try:
        run_dir = run_artifact_smoke(
            args.output_root,
            run_id=args.run_id,
            repo_root=args.repo_root,
            command=command,
        )
    except Exception as error:
        exit_code = 1
        append_failure_record(
            args.output_root,
            experiment_id="stage_0_1",
            run_id=args.run_id,
            stage="artifact_smoke",
            error=error,
            exit_code=exit_code,
            command=command,
        )
        print(f"Stage 0.1 artifact smoke failed: {error}", file=sys.stderr)
        return exit_code
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
