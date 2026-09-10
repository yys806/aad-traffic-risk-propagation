from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

CODE_ROOT = Path(__file__).resolve().parents[1]
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.formal_artifacts import TABLE_REQUIRED_COLUMNS, validate_run_manifest
from riskprop.stage_0_1_sumo import SUMO_CELLS


def summarize(package: Path) -> dict[str, object]:
    package = package.resolve()
    cells: dict[str, object] = {}
    for cell in SUMO_CELLS:
        cell_dir = package / cell
        validate_run_manifest(cell_dir)
        tables = {name: pd.read_parquet(cell_dir / name) for name in TABLE_REQUIRED_COLUMNS}
        cells[cell] = {
            "columns": {name: list(table.columns) for name, table in tables.items()},
            "row_counts": {name: int(len(table)) for name, table in tables.items()},
            "vehicle_count": int(tables["state.parquet"]["vehicle_id"].nunique()),
            "protocol_adopted": int(tables["protocol.parquet"]["adopted"].fillna(False).astype(bool).sum()),
            "risk_status": sorted(tables["risk.parquet"]["inclusion_status"].dropna().astype(str).unique()),
        }
    report = json.loads((package / "stage_0_1_report.json").read_text(encoding="utf-8"))
    return {
        "scientific_claim_eligible": bool(report["scientific_claim_eligible"]),
        "four_cell_ids": report["four_cell_audit"]["cell_ids"],
        "pre_treatment_pass": bool(report["pre_treatment_audit"]["equivalence_pass"]),
        "physical_path": report["physical_path_audit"],
        "cells": cells,
    }


def compare(primary: Path, clean: Path) -> dict[str, object]:
    left, right = summarize(primary), summarize(clean)
    equal = left == right
    return {
        "schema_version": "stage_0_1.environment-comparison.v1",
        "primary": str(primary.resolve()),
        "clean": str(clean.resolve()),
        "structural_match": equal,
        "comparison": {"primary": left, "clean": right},
        "note": "Provenance timestamps, interpreter paths, and run IDs are intentionally excluded from structural comparison.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two sealed Stage 0.1 SUMO packages.")
    parser.add_argument("primary", type=Path)
    parser.add_argument("clean", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.primary, args.clean)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"structural_match": result["structural_match"], "output": str(args.output.resolve())}))
    return 0 if result["structural_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
