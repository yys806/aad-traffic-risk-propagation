# -*- coding: utf-8 -*-
"""AAD-0.4.7.1: strict re-audit of SEE-V2X BSM scene pairing/PDR/GNSS/clock.

Distinguishes pairing rate (rx->tx match) vs reception ratio (rx/tx) vs
link PDR (needs verified receive opportunity). Per ordered device-pair,
per scene, with receive-opportunity grading and no metric conflation.
"""
from __future__ import annotations

import csv
import glob
import io
import json
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = Path("dataset/.tmp_downloads/emulating_extracted/emulating_applications")
DEV = {"rsu": "1", "t1": "2", "t2": "3", "t3": "4"}


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


def rows(p):
    return csv.DictReader(open(p, newline="", encoding="utf-8", errors="replace"))


def load_tx(path):
    seqs = {}
    for r in rows(path):
        s = norm(r.get("seq_num"))
        if s is not None:
            seqs[s] = fnum(r.get("timestamp"))
    return seqs


def load_rx(path):
    out, extra = [], 0
    for r in rows(path):
        if str(r.get("extra", "0")).strip() in ("1", "1.0"):
            extra += 1
            continue
        out.append(r)
    return out, extra


# ---------- GNSS ----------
gnss = {}
gnss_meta = {}
for dev in ["t1", "t2", "t3"]:
    p = BASE / "GNSS" / f"{dev}.csv"
    if not p.exists():
        continue
    lat, lon, ts = [], [], []
    dups = 0
    seen_ts = set()
    gaps = 0
    for r in rows(p):
        la = fnum(r.get("Latitude")); lo = fnum(r.get("Longitude")); t = fnum(r.get("UTC_ns"))
        if la != la or lo != lo or t != t:
            continue
        if t in seen_ts:
            dups += 1
        seen_ts.add(t)
        lat.append(la); lon.append(lo); ts.append(t)
    gnss[dev] = {"lat": lat, "lon": lon, "ts_ns": ts}
    # sampling diagnostics
    import numpy as np
    dts = np.diff(ts) / 1e6 if len(ts) > 1 else np.array([0])
    gaps = int((dts > 20).sum()) if len(dts) else 0  # >20ms gap
    gnss_meta[dev] = {
        "rows": len(ts), "span_s": round((ts[-1] - ts[0]) / 1e9, 1) if len(ts) else 0,
        "median_dt_ms": round(float(np.median(dts)), 2) if len(dts) else None,
        "dup_ts": dups, "gaps_gt_20ms": gaps,
    }
    print(f"GNSS {dev}: rows={len(ts)} span={gnss_meta[dev]['span_s']}s med_dt={gnss_meta[dev]['median_dt_ms']}ms dup_ts={dups} gaps>20ms={gaps}")


def hav(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = math.radians(b[0] - a[0]); dl = math.radians(b[1] - a[1])
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))


def gnss_pos(dev, t_us):
    g = gnss.get(dev)
    if not g or not g["ts_ns"]:
        return None
    import bisect
    t = t_us * 1000.0
    ts = g["ts_ns"]
    i = bisect.bisect_left(ts, t)
    if i == 0:
        return g["lat"][0], g["lon"][0], (ts[0]-t)/1e3
    if i >= len(ts):
        return g["lat"][-1], g["lon"][-1], (t-ts[-1])/1e3
    t0, t1 = ts[i-1], ts[i]
    f = (t-t0)/(t1-t0) if t1 > t0 else 0.0
    la = g["lat"][i-1]+f*(g["lat"][i]-g["lat"][i-1])
    lo = g["lon"][i-1]+f*(g["lon"][i]-g["lon"][i-1])
    return la, lo, abs(t-(t0+f*(t1-t0)))/1e3


# ---------- scenes ----------
scenes = {
    "indoor_1": BASE/"bsm_only"/"indoor_timeExtend"/"intersection_1",
    "indoor_2": BASE/"bsm_only"/"indoor_timeExtend"/"intersection_2",
    "outdoor_1": BASE/"bsm_only"/"outdoor_intersection"/"intersection_1",
    "outdoor_2": BASE/"bsm_only"/"outdoor_intersection"/"intersection_2",
}
OUT = {"gnss_meta": gnss_meta, "scenes": {}}

for scen, sdir in scenes.items():
    if not sdir.exists():
        continue
    tx = {d: load_tx(sdir/f"tx_{d}.csv") for d in DEV}
    pairs = [(r, t) for r in DEV for t in DEV if r != t]
    scene_out = {}
    for rxdev, txdev in pairs:
        p = sdir/f"rx_{rxdev}_tx_{txdev}_bsm.csv"
        if not p.exists():
            continue
        rxrows, extra = load_rx(p)
        txmap = tx[txdev]
        txid = DEV[txdev]
        paired, dup_rx, unmatched_rx, lats, dists = 0, 0, 0, [], []
        seen_rx_keys = set()
        pos_ok, pos_time_err = 0, []
        for r in rxrows:
            s = norm(r.get("tx_seq_num"))
            rid = str(norm(r.get("tx_equipment_id")))
            key = (rid, s)
            matched = (s is not None and s in txmap and rid == txid)
            if matched:
                if key in seen_rx_keys:
                    dup_rx += 1
                    continue
                seen_rx_keys.add(key)
                paired += 1
                d = (fnum(r.get("rx_timestamp (us)")) - fnum(r.get("tx_timestamp (us)")))/1000.0
                if d == d:
                    lats.append(d)
                # GNSS distance (only if both devices have GNSS)
                if rxdev in gnss and txdev in gnss:
                    a = gnss_pos(txdev, fnum(r.get("tx_timestamp (us)")))
                    b = gnss_pos(rxdev, fnum(r.get("tx_timestamp (us)")))
                    if a and b:
                        pos_ok += 1
                        pos_time_err.append(a[2] + b[2])
                        dists.append(hav((a[0], a[1]), (b[0], b[1])))
            else:
                unmatched_rx += 1
        # receive-opportunity grading per pair
        # both devices have GNSS -> stronger; rsu has static point only -> weaker
        opp = "gnss_both" if (rxdev in gnss and txdev in gnss) else ("gnss_tx_only" if txdev in gnss else "none")
        scene_out[f"{rxdev}<-{txdev}"] = {
            "tx_total": len(txmap), "rx_data_rows": len(rxrows), "rx_extra": extra,
            "pairing_rate_rx_to_tx": round(paired/max(1, len(rxrows)), 6),
            "unique_paired": paired, "dup_rx_same_key": dup_rx, "unmatched_rx_rows": unmatched_rx,
            "reception_ratio_full_run": round(paired/max(1, len(txmap)), 6),
            "receive_opportunity_evidence": opp,
            "gnss_distance_m": {"n": len(dists), "min": round(min(dists),1) if dists else None,
                                  "p50": round(sorted(dists)[len(dists)//2],1) if dists else None,
                                  "max": round(max(dists),1) if dists else None,
                                  "pos_match_rate": round(pos_ok/max(1,paired), 4) if paired else None,
                                  "mean_pos_time_err_ms": round(sum(pos_time_err)/len(pos_time_err),1) if pos_time_err else None},
            "latency_ms": {"n": len(lats), "p50": round(sorted(lats)[len(lats)//2],2) if lats else None,
                            "p95": round(sorted(lats)[int(0.95*len(lats))],2) if lats else None} if lats else None,
        }
    OUT["scenes"][scen] = scene_out
    print(f"\n=== {scen} ===")
    for k, v in scene_out.items():
        print(f"  {k}: tx={v['tx_total']} rx={v['rx_data_rows']} pair_rx->tx={v['pairing_rate_rx_to_tx']} "
              f"reception_full={v['reception_ratio_full_run']} opp={v['receive_opportunity_evidence']} "
              f"dist={v['gnss_distance_m']} lat_p50={v['latency_ms']['p50'] if v['latency_ms'] else None}")

with open("code/tmp/bsm_reaudit_0471.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1, default=str)
print("\nsaved code/tmp/bsm_reaudit_0471.json")
