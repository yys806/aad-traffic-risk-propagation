from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.calibration import (
    build_default_calibration_manifests,
    write_frozen_calibration_manifests,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze AAD calibration/holdout file manifests without reading scientific holdout contents."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data_manifest, split_manifest = build_default_calibration_manifests(args.repo_root)
    package = write_frozen_calibration_manifests(
        args.output, data_manifest, split_manifest
    )
    print(
        json.dumps(
            {
                "package": str(package.resolve()),
                "asset_count": len(data_manifest["assets"]),
                "scientific_claim_eligible": False,
                "holdout_contents_inspected": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
