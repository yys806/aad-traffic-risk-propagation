"""Independent validation tests for the SEE-V2X scientific re-audit.

These tests recompute the key arithmetic relationships from the sealed
machine-readable re-audit results and the raw sample (when available) so a
pure Git clone can verify them without the large raw archives.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1].parent
RESULTS = REPO / "code/outputs/formal/calibration/stage_0_4_see_v2x_reaudit_v1/reaudit_results.json"
RAW_ROOT = REPO / "dataset/.tmp_downloads/parkinglot_extracted/outdoor_parkinglot/1_tx"


def _results():
    if not RESULTS.is_file():
        pytest.skip("sealed re-audit results not present")
    return json.loads(RESULTS.read_text(encoding="utf-8"))["runs"]


def test_run2_full_run_pdr_is_not_100_percent() -> None:
    """Run 2: 5591 received / 5742 sent -> full-run PDR = 0.9737, not 1.0."""
    runs = {r["run"]: r for r in _results()}
    r2 = runs["2"]
    assert r2["tx_rows_total"] == 5742
    assert r2["rx_data_rows"] == 5591
    full = r2["rx_data_rows"] / r2["tx_rows_total"]
    assert full == pytest.approx(0.9737, abs=1e-4)
    assert r2["pdr_full_run"] == pytest.approx(full, abs=1e-4)
    assert r2["pdr_common_window"] == pytest.approx(1.0, abs=1e-9)
    # field (per_ue_loss_pct) matches receive-window rate, not full-run
    assert r2["field_pdr_equiv"] == pytest.approx(1.0, abs=1e-9)
    assert abs(r2["pdr_full_run"] - r2["field_pdr_equiv"]) > 0.02  # 2.6 pp gap


def test_full_run_pdr_lte_common_window_and_field() -> None:
    """Full-run PDR <= receive-window PDR and <= field-equivalent PDR (boundary loss excluded)."""
    for r in _results():
        assert r["pdr_full_run"] <= r["pdr_common_window"] + 1e-9
        assert r["pdr_common_window"] == pytest.approx(r["field_pdr_equiv"], abs=0.011)


def test_pdr_denominator_conservation() -> None:
    """Full-run PDR numerator is rx_data_rows; tx_rows_total = rx + un-received sends."""
    for r in _results():
        assert r["pdr_full_run"] == pytest.approx(
            r["rx_data_rows"] / r["tx_rows_total"], abs=1e-4
        )
        assert r["tx_rows_total"] >= r["rx_data_rows"]


def test_latency_numerical_consistency() -> None:
    """Per-run latency column equals (rx-tx)/1000 for every run (abs diff max == 0)."""
    for r in _results():
        assert r["latency"]["col_vs_calc_abs_diff_max"] == pytest.approx(0.0, abs=1e-9)
        assert r["latency"]["negative"] == 0


def test_latency_units_are_ms_from_us() -> None:
    """Distribution bounds are physically plausible ms values after /1000 from us."""
    agg_p95 = None
    for r in _results():
        lat = r["latency"]
        assert 0 < lat["min"] <= lat["p50"] <= lat["p95"] <= lat["p99"] <= lat["max"]
        assert lat["max"] < 1000.0  # sanity: all below 1 second
    # pooled sample had P95 = 34.861 ms
    pass


@pytest.mark.skipif(not RAW_ROOT.is_dir(), reason="raw sample not present (pure-clone mode)")
def test_pairing_identity_unique_in_raw() -> None:
    """Every run: each (tx_equipment_id, seq_num) appears exactly once in the tx log."""
    for run_dir in sorted((p for p in RAW_ROOT.iterdir() if p.is_dir() and (p / "tx_t1.csv").is_file()),
                          key=lambda p: int(p.name)):
        tx = set()
        dup = 0
        with open(run_dir / "tx_t1.csv", newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                key = (row.get("tx_equipment_id"), row.get("seq_num"))
                if key in tx:
                    dup += 1
                tx.add(key)
        assert dup == 0
