# -*- coding: utf-8 -*-
"""AAD-0.4.7: BSM application scenario analysis (GNSS, PDR, latency, clock)."""
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
OUT = {}

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


# ---------- load GNSS ----------
gnss = {}
for dev in ["t1", "t2", "t3"]:
    p = BASE / "GNSS" / f"{dev}.csv"
    if not p.exists():
        continue
    lat, lon, ts = [], [], []
    for r in rows(p):
        la = fnum(r.get("Latitude")); lo = fnum(r.get("Longitude")); t = fnum(r.get("UTC_ns"))
        if la == la and lo == lo and t == t:
            lat.append(la); lon.append(lo); ts.append(t)
    gnss[dev] = {"lat": lat, "lon": lon, "ts_ns": ts}
    print(f"GNSS {dev}: n={len(ts)} span_s={((ts[-1]-ts[0])/1e9):.1f}")


def hav(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def gnss_pos(dev, t_us):
    """interpolate GNSS lat/lon at t_us (UTC_ns = us*1000)."""
    g = gnss.get(dev)
    if not g or not g["ts_ns"]:
        return None
    t = t_us * 1000.0
    ts = g["ts_ns"]
    if t < ts[0] or t > ts[-1]:
        return None
    import bisect
    i = bisect.bisect_left(ts, t)
    if i == 0:
        return g["lat"][0], g["lon"][0]
    if i >= len(ts):
        return g["lat"][-1], g["lon"][-1]
    t0, t1 = ts[i - 1], ts[i]
    f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    la = g["lat"][i - 1] + f * (g["lat"][i] - g["lat"][i - 1])
    lo = g["lon"][i - 1] + f * (g["lon"][i] - g["lon"][i - 1])
    return la, lo


# ---------- BSM scenarios ----------
scenarios = {
    "bsm_indoor_intersection_1": BASE / "bsm_only" / "indoor_timeExtend" / "intersection_1",
    "bsm_indoor_intersection_2": BASE / "bsm_only" / "indoor_timeExtend" / "intersection_2",
    "bsm_outdoor_intersection_1": BASE / "bsm_only" / "outdoor_intersection" / "intersection_1",
    "bsm_outdoor_intersection_2": BASE / "bsm_only" / "outdoor_intersection" / "intersection_2",
}

for scen, sdir in scenarios.items():
    if not sdir.exists():
        continue
    # tx logs per device
    tx = {dev: load_tx(sdir / f"tx_{dev}.csv") for dev in DEV}
    n_tx = {dev: len(s) for dev, s in tx.items()}
    # pairing + latency per ordered device pair
    pairs = [("t1", "t2"), ("t1", "t3"), ("t1", "rsu"),
             ("t2", "t1"), ("t2", "t3"), ("t2", "rsu"),
             ("t3", "t1"), ("t3", "t2"), ("t3", "rsu"),
             ("rsu", "t1"), ("rsu", "t2"), ("rsu", "t3")]
    pair_stats = {}
    all_lat = []
    per_pair_lat = {}
    for rxdev, txdev in pairs:
        p = sdir / f"rx_{rxdev}_tx_{txdev}_bsm.csv"
        if not p.exists():
            continue
        rxrows, extra = load_rx(p)
        txdev_id = DEV[txdev]
        txmap = tx[txdev]
        paired, unpaired, lats = 0, 0, []
        for r in rxrows:
            s = norm(r.get("tx_seq_num"))
            if s is not None and txmap.get(s) is not None and str(norm(r.get("tx_equipment_id"))) == txdev_id:
                paired += 1
                d = (fnum(r.get("rx_timestamp (us)")) - fnum(r.get("tx_timestamp (us)"))) / 1000.0
                if d == d:
                    lats.append(d)
            else:
                unpaired += 1
        pair_stats[f"{rxdev}<-{txdev}"] = {
            "rx_data_rows": len(rxrows), "paired": paired, "unpaired": unpaired,
            "pdr_full": round(paired / max(1, len(txmap)), 4),
            "tx_total": len(txmap),
            "latency_ms": {"n": len(lats), "p50": sorted(lats)[len(lats)//2] if lats else None,
                            "p95": sorted(lats)[int(0.95*len(lats))] if lats else None} if lats else None,
        }
        if lats:
            per_pair_lat[f"{rxdev}<-{txdev}"] = lats
            all_lat.extend(lats)

    # GNSS distance analysis (outdoor only, mobile pairs)
    dist_stats = {}
    if "outdoor" in scen and gnss:
        for rxdev, txdev in pairs:
            if rxdev not in gnss or txdev not in gnss:
                continue
            p = sdir / f"rx_{rxdev}_tx_{txdev}_bsm.csv"
            if not p.exists():
                continue
            txmap = tx[txdev]
            buckets = {}
            n_pos = 0
            for r in rows(p):
                if str(r.get("extra", "0")).strip() in ("1", "1.0"):
                    continue
                s = norm(r.get("tx_seq_num"))
                if s is None or s not in txmap:
                    continue
                tts = fnum(r.get("tx_timestamp (us)"))
                a = gnss_pos(txdev, tts); b = gnss_pos(rxdev, tts)
                if a is None or b is None:
                    continue
                n_pos += 1
                d = hav(a[0], a[1], b[0], b[1])
                b = int(d // 50) * 50
                buckets.setdefault(b, [0, 0])
                buckets[b][0] += 1
            # total sent in window
            t0 = min(v for v in txmap.values() if v == v); t1 = max(v for v in txmap.values() if v == v)
            total_sent = len(txmap)
            for bkt in buckets:
                hi = bkt + 50
                sent = sum(1 for v in txmap.values() if v == v and gnss_pos(txdev, v) and gnss_pos(rxdev, v) and bkt <= hav(*gnss_pos(txdev, v), *gnss_pos(rxdev, v)) < hi)
                buckets[bkt].append(sent)
            dist_stats[f"{rxdev}<-{txdev}"] = {
                "n_positioned": n_pos,
                "bins": {f"{b}-{b+50}m": {"received": v[0], "sent": v[2] if len(v) > 2 else None,
                                          "pdr": round(v[0]/v[2], 3) if len(v) > 2 and v[2] else None}
                          for b, v in sorted(buckets.items())},
            }

    OUT[scen] = {
        "tx_counts": n_tx,
        "pairs": pair_stats,
        "latency_pooled": {"n": len(all_lat), "p50": sorted(all_lat)[len(all_lat)//2] if all_lat else None,
                            "p95": sorted(all_lat)[int(0.95*len(all_lat))] if all_lat else None} if all_lat else None,
        "gnss_distance": dist_stats if dist_stats else None,
    }
    print(f"\n=== {scen} ===")
    print("tx_counts:", n_tx)
    for k, v in pair_stats.items():
        print(f"  {k}: paired={v['paired']}/{v['tx_total']} pdr_full={v['pdr_full']} lat={v.get('latency_ms')}")
    if dist_stats:
        for k, v in list(dist_stats.items())[:2]:
            print(f"  dist {k}: positioned={v['n_positioned']} bins={dict(list(v['bins'].items())[:5])}")

with open("code/tmp/bsm_analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1, default=str)
print("\nsaved code/tmp/bsm_analysis_results.json")
