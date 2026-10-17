# -*- coding: utf-8 -*-
"""AAD-0.4.6.1: independent scientific re-audit of SEE-V2X outdoor_parkinglot.

Recomputes, per run and per metric-definition, WITHOUT reusing 0.4.6 code paths:
  PDR full-run vs common-window vs field per_ue_loss_pct;
  latency per-run distributions + cross-run offset diagnostics.
Everything is recomputed from raw tx/rx csvs in this script.
"""
from __future__ import annotations

import csv
import glob
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path("dataset/.tmp_downloads/parkinglot_extracted/outdoor_parkinglot/1_tx")


def norm(v):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def fnum(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return float("nan")


def load_tx(path):
    seqs = {}
    order = []
    for r in csv.DictReader(open(path, newline="", encoding="utf-8", errors="replace")):
        s = norm(r.get("seq_num"))
        ts = fnum(r.get("timestamp"))
        if s is not None:
            seqs[s] = ts
            order.append(s)
    return seqs, order


def load_rx(path):
    rows = []
    extra = 0
    for r in csv.DictReader(open(path, newline="", encoding="utf-8", errors="replace")):
        if str(r.get("extra", "0")).strip() in ("1", "1.0"):
            extra += 1
            continue
        rows.append(r)
    return rows, extra


def per_run(run_dir):
    tx_path = run_dir / "tx_t1.csv"
    rx_path = run_dir / "rx_t3_tx_t1.csv"
    tx, tx_order = load_tx(tx_path)
    rx, rx_extra = load_rx(rx_path)

    # pairing
    paired = []
    unpaired = 0
    for r in rx:
        s = norm(r.get("tx_seq_num"))
        if s is not None and s in tx:
            paired.append((s, fnum(r.get("tx_timestamp (us)")), fnum(r.get("rx_timestamp (us)")),
                           fnum(r.get("latency (ms)"))))
        else:
            unpaired += 1

    tx_all = set(tx)
    rx_seqs = {p[0] for p in paired}

    # FULL-RUN PDR (denominator = all tx rows)
    pdr_full = len(rx_seqs) / max(1, len(tx_all))

    # COMMON-WINDOW PDR (denominator = tx rows in [min paired seq, max paired seq])
    if rx_seqs:
        lo, hi = min(rx_seqs), max(rx_seqs)
        tx_in_win = {s for s in tx_all if lo <= s <= hi}
        pdr_win = len(rx_seqs & tx_in_win) / max(1, len(tx_in_win))
        expected_win = hi - lo + 1
    else:
        lo = hi = None
        tx_in_win = set()
        pdr_win = None
        expected_win = 0

    # field value (last non-empty)
    field_loss = None
    for r in rx:
        v = r.get("per_ue_loss_pct (%)")
        if v not in (None, ""):
            field_loss = fnum(v)

    # latency stats
    lats = [p[3] for p in paired if p[3] == p[3]]
    lats_calc = [(p[2] - p[1]) / 1000.0 for p in paired if p[1] == p[1] and p[2] == p[2]]
    lat_max_diff = max((abs(a - b) for a, b in zip(lats, lats_calc)), default=None)

    # gap analysis within paired set (seq continuity of received)
    srt = sorted(rx_seqs)
    gaps = [(srt[i + 1] - srt[i] - 1) for i in range(len(srt) - 1) if srt[i + 1] - srt[i] > 1]

    return {
        "run": run_dir.name,
        "tx_rows_total": len(tx_all),
        "tx_seq_min": min(tx_all) if tx_all else None,
        "tx_seq_max": max(tx_all) if tx_all else None,
        "tx_duplicate_seq": len(tx_order) - len(tx_all),
        "rx_data_rows": len(rx),
        "rx_extra_rows_excluded": rx_extra,
        "paired": len(paired),
        "unpaired": unpaired,
        "rx_seq_min": lo,
        "rx_seq_max": hi,
        "rx_first_seq": srt[0] if srt else None,
        "rx_last_seq": srt[-1] if srt else None,
        "pdr_full_run": round(pdr_full, 6),
        "common_window": {"lo": lo, "hi": hi, "tx_in_window": len(tx_in_win), "expected": expected_win},
        "pdr_common_window": round(pdr_win, 6) if pdr_win is not None else None,
        "rx_seq_gaps_gt1": len(gaps),
        "rx_missing_in_window": sum(gaps),
        "field_loss_pct": field_loss,
        "field_pdr_equiv": round(1 - field_loss / 100, 6) if field_loss is not None else None,
        "latency": {
            "n": len(lats),
            "col_vs_calc_abs_diff_max": lat_max_diff,
            "negative": sum(1 for x in lats_calc if x < 0),
            "min": min(lats) if lats else None,
            "p50": sorted(lats)[len(lats) // 2] if lats else None,
            "p95": sorted(lats)[int(0.95 * len(lats))] if lats else None,
            "p99": sorted(lats)[int(0.99 * len(lats))] if lats else None,
            "max": max(lats) if lats else None,
        },
    }


runs = sorted([p for p in glob.glob(str(ROOT / "*")) if (Path(p) / "tx_t1.csv").exists()],
              key=lambda p: int(Path(p).name))
results = [per_run(Path(r)) for r in runs]

print("=== per-run PDR re-audit ===")
for r in results:
    print(json.dumps({k: r[k] for k in (
        "run", "tx_rows_total", "rx_data_rows", "paired", "pdr_full_run",
        "pdr_common_window", "field_loss_pct", "field_pdr_equiv",
        "common_window", "rx_seq_gaps_gt1", "rx_missing_in_window",
        "tx_duplicate_seq")}, ensure_ascii=False))

print("\n=== per-run latency ===")
for r in results:
    print(json.dumps({"run": r["run"], **r["latency"]}, ensure_ascii=False))

# cross-run median comparison (offset diagnostic)
print("\n=== cross-run median latency (offset diagnostic) ===")
for r in results:
    print(r["run"], r["latency"]["p50"], "ms")

# aggregate distribution
all_lat = []
for r in results:
    pass  # recompute below
for run_dir in [Path(p) for p in runs]:
    tx, _ = load_tx(run_dir / "tx_t1.csv")
    rx, _ = load_rx(run_dir / "rx_t3_tx_t1.csv")
    for p in [ (norm(x.get('tx_seq_num')), fnum(x.get('tx_timestamp (us)')), fnum(x.get('rx_timestamp (us)'))) for x in rx ]:
        s, tts, rts = p
        if s in tx and tts == tts and rts == rts:
            all_lat.append((rts - tts) / 1000.0)
all_lat.sort()
n = len(all_lat)
print(json.dumps({
    "aggregate_n": n,
    "min": all_lat[0], "p5": all_lat[int(0.05 * n)], "p25": all_lat[int(0.25 * n)],
    "p50": all_lat[n // 2], "p75": all_lat[int(0.75 * n)], "p95": all_lat[int(0.95 * n)],
    "p99": all_lat[int(0.99 * n)], "max": all_lat[-1],
}, indent=1))

with open("code/tmp/reaudit_results.json", "w", encoding="utf-8") as f:
    json.dump({"runs": results}, f, ensure_ascii=False, indent=1)
print("\nsaved code/tmp/reaudit_results.json")
