from __future__ import annotations

import json
from pathlib import Path

from riskprop.prelock_validation import write_stage_0_6_prelock_validation


def test_stage_0_6_prelock_report_passes_truth_cases_but_stays_pending_calibration(
    tmp_path: Path,
) -> None:
    output = write_stage_0_6_prelock_validation(tmp_path / "stage_0_6")
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["analytic_truth"]["pass"] is True
    assert audit["physical_path_truth"]["pass"] is True
    assert audit["timestep_convergence"]["gate_status"] == "pending_delta_eq"
    assert audit["gate_status"] == "pending_e15_e17_and_frozen_tolerances"
    assert audit["scientific_claim_eligible"] is False
    assert not (output / "protocol_lock_v1.1.yaml").exists()
    assert (output / "SHA256SUMS").is_file()
