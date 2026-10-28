"""Regression checks for the sealed Stage 0.5 offline mechanism audit."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/results/RES-STAGE-0.5-OFFLINE-MECHANISM-AUDIT-20261028"


def test_count_reconciliation_preserves_formal_and_full_event_counts():
    data = json.loads((EVIDENCE / "count_reconciliation.json").read_text(encoding="utf-8"))
    assert data["arms"]["B10"]["recomputed_event_array_length"] == 7
    assert data["arms"]["B10"]["recomputed_window_onsets"] == 5
    assert data["arms"]["B01"]["recomputed_event_array_length"] == 1
    assert data["arms"]["B01"]["recomputed_window_onsets"] == 0
    assert data["arms"]["B11"]["recomputed_event_array_length"] == 19
    assert data["arms"]["B11"]["recomputed_window_onsets"] == 17
    for arm in data["arms"].values():
        assert arm["source_formal_events"] == 0
        assert arm["target_cohort_formal_events"] == 0
        assert arm["differences"] == []
    assert data["all_raw_hashes_match"] is True


def test_event_inventory_has_unique_raw_associations_and_expected_spatial_classes():
    rows = list(csv.DictReader((EVIDENCE / "event_inventory.csv").open(encoding="utf-8", newline="")))
    assert len(rows) == 27
    assert all(row["association_status"] == "unique" for row in rows)
    assert all(row["confirmation_association_status"] == "unique" for row in rows)
    assert {row["spatial_class"] for row in rows} == {
        "auxiliary_or_unmapped_lane", "target_main", "other_upstream_mainline"
    }


def test_source_observability_keeps_exposure_and_missing_states_separate():
    rows = list(csv.DictReader((EVIDENCE / "source_observability.csv").open(encoding="utf-8", newline="")))
    assert {row["arm"] for row in rows} == {"B00", "B10", "B01", "B11"}
    for row in rows:
        assert float(row["reliable_following_exposure_veh_s"]) > 0
        assert int(row["risk_state_count_ttc_lt_2"]) == 0
        assert int(row["formal_event_count"]) == 0
        assert "missing" in row["measurement_status"]
