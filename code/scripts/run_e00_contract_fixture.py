from __future__ import annotations

import argparse
import sys
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.formal_artifacts import append_failure_record  # noqa: E402
from riskprop.formal_runner import run_contract_fixture  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a non-empty E00 contract fixture without science claims."
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [sys.executable, *sys.argv]
    try:
        fixture_dir = run_contract_fixture(
            args.output_root,
            fixture_id=args.fixture_id,
            repo_root=args.repo_root,
            command=command,
        )
    except Exception as error:
        append_failure_record(
            args.output_root,
            experiment_id="E00",
            run_id=args.fixture_id,
            stage="contract_fixture",
            error=error,
            exit_code=1,
            command=command,
        )
        print(f"E00 contract fixture failed: {error}", file=sys.stderr)
        return 1
    print(fixture_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
