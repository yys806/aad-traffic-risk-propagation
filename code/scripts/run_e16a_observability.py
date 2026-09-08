from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.e16a import build_e16a_status_package


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seal the current E16-A observability boundary without inferring packet loss or adoption."
    )
    parser.add_argument("--rv-rx-profile", type=Path, required=True)
    parser.add_argument("--rv-rx-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--official-url", required=True)
    parser.add_argument("--http-status", type=int, required=True)
    parser.add_argument(
        "--access-status",
        choices=(
            "official_asset_inaccessible_from_current_environment",
            "downloaded_and_verified",
        ),
        required=True,
    )
    args = parser.parse_args()
    output = build_e16a_status_package(
        rv_rx_profile_path=args.rv_rx_profile,
        rv_rx_zip_path=args.rv_rx_zip,
        output_dir=args.output,
        packet_access={
            "source": "official_usdot",
            "url": args.official_url,
            "http_status": args.http_status,
            "status": args.access_status,
        },
    )
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    print(json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
