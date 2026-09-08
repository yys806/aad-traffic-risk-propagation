from __future__ import annotations

import argparse
import sys
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop.project_docs import validate_project_docs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate AAD knowledge entries and experiment/result traceability."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="AAD repository root (defaults to the script's repository).",
    )
    args = parser.parse_args()

    issues = validate_project_docs(args.repo_root)
    if issues:
        print("PROJECT_DOCS_INVALID")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("PROJECT_DOCS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
