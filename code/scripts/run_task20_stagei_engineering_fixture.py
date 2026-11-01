"""Run the Task20 Stage I mechanism wiring fixture.

The fixture is synthetic and engineering-only.  It validates the existing
four-cell/lifecycle contracts, records an information/action/risk timeline and
keeps physical arrival Unknown unless a caller supplies an independently
evidenced event-specific time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_ROOT.parent
if str(CODE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(CODE_ROOT / "src"))

from riskprop.stage_i_mechanism import (  # noqa: E402
    audit_four_cell_mechanism_fixture,
    build_engineering_fixture,
    build_joint_timeline,
    compare_paired_action,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run(output: Path) -> Path:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    fixture = build_engineering_fixture()
    contract = audit_four_cell_mechanism_fixture(
        fixture["configs"], fixture["lifecycle"], fixture["pre_treatment"]
    )
    action = compare_paired_action(
        fixture["baseline"],
        fixture["treatment"],
        treatment_start_s=1.0,
        speed_tolerance_mps=0.2,
        sustain_s=0.5,
    )
    timeline = build_joint_timeline(
        message_events=fixture["message_events"],
        action_events=fixture["action_events"],
        risk_events=fixture["risk_events"],
        physical_arrival_time_s=None,
    )
    write_json(output / "four_cell_contract_audit.json", contract)
    write_json(output / "action_change_audit.json", action)
    write_json(output / "joint_timeline.json", timeline)
    write_json(output / "fixture_config.json", fixture["configs"])
    write_json(
        output / "provenance.json",
        {
            "schema_version": "aad.task20.stage-i-engineering-provenance.v1",
            "task_id": "AAD-S0.5-TASK20",
            "scientific_claim_eligible": False,
            "locked_holdout_read": False,
            "sumo_runs": 0,
            "fixture_only": True,
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
            ).strip(),
            "python": sys.version,
            "platform": platform.platform(),
            "command": "python code/scripts/run_task20_stagei_engineering_fixture.py --output <path>",
        },
    )
    source_paths = [
        CODE_ROOT / "src/riskprop/stage_i_mechanism.py",
        CODE_ROOT / "src/riskprop/formal_design.py",
        CODE_ROOT / "src/riskprop/prelock_metrics.py",
        CODE_ROOT / "src/riskprop/protocol_lock.py",
        REPO_ROOT / "docs/TASK19_SCIENTIFIC_RESULT_ANALYSIS_20261101.md",
        REPO_ROOT / "docs/TASK18_EXECUTION_AUDIT_20261101.md",
        REPO_ROOT / "docs/AAD_ROUND2_CLOSURE_AND_CONDITIONAL_VALIDATION_REPORT_20261030.md",
    ]
    bindings = {
        str(path.relative_to(REPO_ROOT)): sha256(path)
        for path in source_paths
        if path.exists()
    }
    write_json(
        output / "source_bindings.json",
        {
            "schema_version": "aad.task20.source-bindings.v1",
            "files": bindings,
            "note": "Hashes bind the engineering fixture and the reused evidence; no raw or locked-holdout data are copied.",
        },
    )
    files = sorted(path for path in output.iterdir() if path.is_file())
    manifest = {
        "schema_version": "aad.task20.stage-i-engineering-manifest.v1",
        "files": {path.name: sha256(path) for path in files},
    }
    write_json(output / "manifest.json", manifest)
    files = sorted(path for path in output.iterdir() if path.is_file())
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
        newline="\n",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print((result / "joint_timeline.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
