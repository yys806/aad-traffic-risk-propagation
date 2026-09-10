from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.ngsim_risk_calibration import write_stage_0_2_ngsim_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Stage 0.2 NGSIM calibration only; no holdout or causal-effect analysis."
    )
    parser.add_argument("--repo-root", type=Path, default=CODE_ROOT.parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provisional-ttc-threshold-s", type=float, default=2.0)
    args = parser.parse_args()
    data_root = args.repo_root / "dataset" / "NGSIM"
    sources = []
    for window in ("0750am-0805am", "0805am-0820am", "0820am-0835am"):
        sources.append(
            {
                "asset_id": "ngsim_us101",
                "site": "US-101",
                "path": data_root / "US-101-LosAngeles-CA.zip",
                "inner_zip_member": "us-101-vehicle-trajectory-data.zip",
                "csv_member": f"vehicle-trajectory-data/{window}/trajectories-{window}.csv",
                "window_id": window.replace("am-", "_").replace("am", ""),
            }
        )
    sources.append(
        {
            "asset_id": "ngsim_lankershim",
            "site": "Lankershim",
            "path": data_root / "Lankershim-Boulevard-LosAngeles-CA.zip",
            "csv_member": "NGSIM__Lankershim_Vehicle_Trajectories.csv",
            "window_id": "complete",
        }
    )
    package = write_stage_0_2_ngsim_package(
        output_dir=args.output,
        sources=sources,
        provisional_ttc_threshold_s=args.provisional_ttc_threshold_s,
    )
    audit = json.loads((package / "audit.json").read_text(encoding="utf-8"))
    print(json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
