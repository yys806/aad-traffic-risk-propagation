from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from riskprop.calibration import (
    CalibrationContractError,
    build_blind_audit_exports,
    build_default_calibration_manifests,
    cohens_kappa,
    energy_distance,
    fit_robust_scaler,
    select_blind_audit_windows,
    validate_real_state_table,
    validate_risk_event_table,
    validate_checksum_package,
    validate_split_manifest,
    write_frozen_calibration_manifests,
)


def test_default_split_is_group_level_and_keeps_holdout_sealed(tmp_path: Path) -> None:
    assets = tmp_path / "docs" / "归档" / "真实数据与NC文献调研" / "datasets"
    paths = [
        assets / "NGSIM" / "US-101-LosAngeles-CA.zip",
        assets / "NGSIM" / "I-80-Emeryville-CA.zip",
        assets / "NGSIM" / "Lankershim-Boulevard-LosAngeles-CA.zip",
        assets / "NGSIM" / "Peachtree-Street-Atlanta-GA.zip",
        assets / "pNEUMA" / "20181101_d1_0800_0830.csv",
        assets / "pNEUMA" / "osm" / "athens_d1_bbox_20260907.osm",
        assets / "SPMD" / "selected" / "RV_RX.csv.zip",
    ]
    for index, path in enumerate(paths):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"fixture-{index}".encode())

    data_manifest, split_manifest = build_default_calibration_manifests(tmp_path)

    validate_split_manifest(split_manifest)
    assert set(split_manifest["calibration"]) == {
        "ngsim_us101",
        "ngsim_lankershim",
        "pneuma_d1_0800_0830",
        "pneuma_d1_osm_20260907",
        "spmd_rv_rx_calibration_trips",
    }
    assert set(split_manifest["locked_holdout"]) == {
        "ngsim_i80",
        "ngsim_peachtree",
        "spmd_rv_rx_holdout_trips",
    }
    assert all(item["sha256"] for item in data_manifest["assets"])
    assert data_manifest["scientific_claim_eligible"] is False


def test_split_validator_rejects_any_group_overlap() -> None:
    with pytest.raises(CalibrationContractError, match="overlap"):
        validate_split_manifest(
            {"calibration": ["site_a"], "locked_holdout": ["site_a"]}
        )


def test_frozen_manifests_refuse_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "frozen"
    write_frozen_calibration_manifests(
        output,
        {"assets": [], "scientific_claim_eligible": False},
        {"calibration": ["a"], "locked_holdout": ["b"]},
    )
    with pytest.raises(FileExistsError):
        write_frozen_calibration_manifests(
            output,
            {"assets": [], "scientific_claim_eligible": False},
            {"calibration": ["a"], "locked_holdout": ["b"]},
        )
    assert json.loads((output / "split_manifest.json").read_text(encoding="utf-8"))[
        "locked_holdout"
    ] == ["b"]


def test_checksum_package_detects_tampering(tmp_path: Path) -> None:
    output = tmp_path / "frozen"
    write_frozen_calibration_manifests(
        output,
        {"assets": [], "scientific_claim_eligible": False},
        {"calibration": ["a"], "locked_holdout": ["b"]},
    )
    result = validate_checksum_package(output)
    assert result["pass"] is True
    (output / "data_manifest.json").write_text("tampered", encoding="utf-8")
    with pytest.raises(CalibrationContractError, match="checksum mismatch"):
        validate_checksum_package(output)


def test_state_contract_requires_missing_reason_instead_of_silent_zero() -> None:
    valid = pd.DataFrame(
        [
            {
                "dataset": "ngsim",
                "site": "us101",
                "window_id": "0750_0805",
                "vehicle_id": "1",
                "time_s": 0.0,
                "x_m": 1.0,
                "y_m": 2.0,
                "speed_mps": 3.0,
                "acceleration_mps2": 0.0,
                "road_id": "r0",
                "lane_id": "1",
                "leader_id": pd.NA,
                "net_gap_m": float("nan"),
                "closing_speed_mps": float("nan"),
                "measurement_status": "missing",
                "missing_reason": "no_reported_leader",
            }
        ]
    )
    validate_real_state_table(valid)

    invalid = valid.copy()
    invalid.loc[0, "net_gap_m"] = 0.0
    invalid.loc[0, "missing_reason"] = ""
    with pytest.raises(CalibrationContractError, match="missing_reason"):
        validate_real_state_table(invalid)


def test_event_contract_rejects_frame_as_independent_event() -> None:
    event = pd.DataFrame(
        [
            {
                "event_id": "e1",
                "dataset": "ngsim",
                "site": "us101",
                "window_id": "0750_0805",
                "vehicle_id": "1",
                "leader_id": "2",
                "conflict_type": "rear_end",
                "event_start_s": 1.0,
                "event_end_s": 1.2,
                "event_duration_s": 0.2,
                "ttc_min_s": 1.0,
                "drac_max_mps2": 2.0,
                "pet_s": float("nan"),
                "inclusion_status": "included",
                "exclusion_reason": "",
                "algorithm_version": "e15a.v1",
                "raw_frame_count": 3,
            }
        ]
    )
    validate_risk_event_table(event)
    event.loc[0, "raw_frame_count"] = 1
    event.loc[0, "event_duration_s"] = 0.0
    with pytest.raises(CalibrationContractError, match="frame-level"):
        validate_risk_event_table(event)


def test_blind_audit_pack_is_deterministic_balanced_and_hides_algorithm_labels() -> None:
    rows = []
    for category in ("algorithm_positive", "near_threshold", "random_negative"):
        for index in range(120):
            rows.append(
                {
                    "event_id": f"{category}-{index}",
                    "audit_category": category,
                    "dataset": "ngsim" if index % 2 else "pneuma",
                    "site": "site_a",
                    "window_id": "w0",
                    "vehicle_id": str(index),
                    "window_start_s": float(index),
                    "window_end_s": float(index + 2),
                    "algorithm_prediction": category == "algorithm_positive",
                }
            )
    candidates = pd.DataFrame(rows)

    first = select_blind_audit_windows(candidates, total=300, seed=20260907)
    second = select_blind_audit_windows(candidates, total=300, seed=20260907)

    assert first.equals(second)
    assert len(first) == 300
    assert first["audit_category"].value_counts().to_dict() == {
        "algorithm_positive": 100,
        "near_threshold": 100,
        "random_negative": 100,
    }
    assert "algorithm_prediction" not in first.columns
    assert first["blind_id"].is_unique

    review, sealed_key = build_blind_audit_exports(first, round_number=1)
    assert "event_id" not in review.columns
    assert "audit_category" not in review.columns
    assert "algorithm_prediction" not in review.columns
    assert {"reviewer_risk_label", "reviewer_leader_correct", "reviewer_uncertain"} <= set(
        review.columns
    )
    assert {"blind_id", "event_id", "audit_category"} <= set(sealed_key.columns)
    assert review["blind_id"].tolist() == sealed_key["blind_id"].tolist()


def test_kappa_and_energy_distance_have_known_behavior() -> None:
    assert cohens_kappa(["risk", "safe", "risk"], ["risk", "safe", "risk"]) == pytest.approx(1.0)
    same = pd.DataFrame({"speed": [1.0, 2.0], "gap": [3.0, 4.0]})
    shifted = pd.DataFrame({"speed": [11.0, 12.0], "gap": [13.0, 14.0]})
    assert energy_distance(same, same, ["speed", "gap"]) == pytest.approx(0.0)
    assert energy_distance(same, shifted, ["speed", "gap"]) > 0.0


def test_energy_distance_uses_a_frozen_real_reference_scaler() -> None:
    reference = pd.DataFrame({"speed": [0.0, 10.0, 20.0], "gap": [5.0, 10.0, 15.0]})
    scaler = fit_robust_scaler(reference, ["speed", "gap"])
    nearby = pd.DataFrame({"speed": [1.0, 11.0, 19.0], "gap": [5.5, 10.5, 14.5]})
    far = pd.DataFrame({"speed": [50.0, 60.0, 70.0], "gap": [40.0, 50.0, 60.0]})

    near_distance = energy_distance(reference, nearby, ["speed", "gap"], scaler=scaler)
    far_distance = energy_distance(reference, far, ["speed", "gap"], scaler=scaler)

    assert scaler["reference"] == "real_calibration"
    assert near_distance < far_distance
