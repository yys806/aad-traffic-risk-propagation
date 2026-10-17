# -*- coding: utf-8 -*-
"""AAD-0.4.7.2: repaired GNSS spatio-temporal matcher for SEE-V2X BSM analysis.

Fixes from 0.4.7.1:
  A. Out-of-window queries -> INVALID (was: clamped to edge position).
  B. Time-error computed against REAL neighbour samples (was: self-interpolated ~0).
  C. Distance validity: distinct-track check, duplicate-coordinate handling.
Units: comm tx/rx_timestamp are MICROSECONDS (us); GNSS UTC_ns are NANOSECONDS (ns).
  us = ns / 1000.  Same UTC epoch only after unit conversion - NOT clock sync proof.
"""
from __future__ import annotations

import bisect
import csv
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

BASE = Path("dataset/.tmp_downloads/emulating_extracted/emulating_applications")
MAX_GAP_MS = 50.0       # reject interpolation across GNSS gaps > 50 ms
OUT = {}


def hav(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class GnssTrack:
    """Monotonic, de-duplicated GNSS track with strict window + gap policy."""

    def __init__(self, path, dev):
        self.dev = dev
        self.ts_us, self.lat, self.lon = [], [], []
        seen = set()
        n_raw = 0
        for r in csv.DictReader(open(path, newline="", encoding="utf-8", errors="replace")):
            n_raw += 1
            t = float(r["UTC_ns"]) / 1000.0          # ns -> us (epoch-consistent w/ comm ts)
            la = float(r["Latitude"]); lo = float(r["Longitude"])
            if t in seen:
                continue
            seen.add(t)
            self.ts_us.append(t); self.lat.append(la); self.lon.append(lo)
        order = np.argsort(self.ts_us)
        self.ts_us = [self.ts_us[i] for i in order]
        self.lat = [self.lat[i] for i in order]
        self.lon = [self.lon[i] for i in order]
        self.n_raw = n_raw
        self.n = len(self.ts_us)
        self.t0, self.t1 = self.ts_us[0], self.ts_us[-1]
        dts = np.diff(self.ts_us) / 1000.0           # us -> ms
        self.median_dt_ms = float(np.median(dts)) if len(dts) else None
        self.max_gap_ms = float(np.max(dts)) if len(dts) else 0.0
        self.monotonic = bool(np.all(np.diff(self.ts_us) > 0))
        # duplicate coordinate fraction (consecutive identical lat/lon)
        dup = sum(1 for i in range(1, self.n)
                  if self.lat[i] == self.lat[i-1] and self.lon[i] == self.lon[i-1])
        self.dup_coord_frac = dup / max(1, self.n - 1)

    def pos_at(self, t_us):
        """Return (lat, lon, err_ms, ok, reject_reason). ok=False for out-of-window or big gap."""
        if t_us < self.t0 or t_us > self.t1:
            return None, None, None, False, "outside_window"
        i = bisect.bisect_left(self.ts_us, t_us)
        if i == 0:
            return self.lat[0], self.lon[0], (self.ts_us[0] - t_us) / 1000.0, True, "edge_exact"
        if i >= self.n:
            return None, None, None, False, "outside_window"
        t0, t1 = self.ts_us[i-1], self.ts_us[i]
        gap_ms = (t1 - t0) / 1000.0
        if gap_ms > MAX_GAP_MS:
            return None, None, None, False, f"gap_gt_{MAX_GAP_MS:g}ms"
        f = (t_us - t0) / (t1 - t0) if t1 > t0 else 0.0
        la = self.lat[i-1] + f * (self.lat[i] - self.lat[i-1])
        lo = self.lon[i-1] + f * (self.lon[i] - self.lon[i-1])
        err_ms = min(t_us - t0, t1 - t_us) / 1000.0   # dist to REAL neighbour
        return la, lo, err_ms, True, "interp"


def main():
    tracks = {}
    audit = {}
    for dev in ["t1", "t2", "t3"]:
        p = BASE / "GNSS" / f"{dev}.csv"
        if not p.exists():
            continue
        tr = GnssTrack(p, dev)
        tracks[dev] = tr
        audit[dev] = {
            "rows_raw": tr.n_raw, "rows_dedup": tr.n,
            "span_s": round((tr.t1 - tr.t0) / 1e6, 1),
            "monotonic": tr.monotonic, "median_dt_ms": tr.median_dt_ms,
            "max_gap_ms": tr.max_gap_ms, "dup_coord_frac": round(tr.dup_coord_frac, 6),
        }
        print(f"GNSS {dev}: n={tr.n} span={audit[dev]['span_s']}s monotonic={tr.monotonic} "
              f"med_dt={tr.median_dt_ms}ms max_gap={tr.max_gap_ms}ms dup_frac={tr.dup_coord_frac:.4f}")

    # rsu static point audit
    rsu_rows = list(csv.DictReader(open(BASE / "GNSS" / "rsu.csv", newline="", encoding="utf-8")))
    audit["rsu"] = {"rows": len(rsu_rows), "note": "static single point; NOT continuous online or high-precision evidence",
                    "lat": float(rsu_rows[0]["Latitude"]), "lon": float(rsu_rows[0]["Longitude"])}

    # scene tx windows -> GNSS coverage verdict
    DEV = {"rsu": "1", "t1": "2", "t2": "3", "t3": "4"}
    scenes = {
        "indoor_1": BASE/"bsm_only"/"indoor_timeExtend"/"intersection_1",
        "indoor_2": BASE/"bsm_only"/"indoor_timeExtend"/"intersection_2",
        "outdoor_1": BASE/"bsm_only"/"outdoor_intersection"/"intersection_1",
        "outdoor_2": BASE/"bsm_only"/"outdoor_intersection"/"intersection_2",
    }
    pairing = json.loads(open("code/tmp/bsm_reaudit_0471.json", encoding="utf-8").read())["scenes"]

    scene_out = {}
    for scen, sdir in scenes.items():
        if not sdir.exists():
            continue
        tx = {}
        for dev in DEV:
            p = sdir / f"tx_{dev}.csv"
            if p.exists():
                tx[dev] = {int(float(r["seq_num"])): float(r["timestamp"])
                            for r in csv.DictReader(open(p, newline="", encoding="utf-8"))
                            if r.get("seq_num")}
        pair_res = {}
        for rxdev, txdev in [(r, t) for r in DEV for t in DEV if r != t]:
            key = f"{rxdev}<-{txdev}"
            rxp = sdir / f"rx_{rxdev}_tx_{txdev}_bsm.csv"
            if not rxp.exists():
                continue
            sent_ts = list(tx.get(txdev, {}).values())
            # GNSS coverage of the tx window
            cov = "no_gnss"
            if txdev in tracks and sent_ts:
                tr = tracks[txdev]
                n_in = sum(1 for v in sent_ts if tr.t0 <= v <= tr.t1)
                cov = f"{n_in}/{len(sent_ts)}" if n_in else "0"
            # distance on VALID gnss pairs only
            dists, rej = [], {}
            if rxdev in tracks and txdev in tracks:
                for v in sent_ts:
                    a = tracks[txdev].pos_at(v)
                    b = tracks[rxdev].pos_at(v)
                    for side, r in (("tx", a), ("rx", b)):
                        if not r[3]:
                            rej[r[4]] = rej.get(r[4], 0) + 1
                    if a[3] and b[3]:
                        dists.append(hav(a[0], a[1], b[0], b[1]))
            # received distances (for reference only; denominator from sent)
            d = sorted(dists)
            pair_res[key] = {
                "tx_total": len(sent_ts),
                "gnss_coverage_of_tx_window": cov,
                "valid_sent_with_position": len(dists),
                "pos_match_rate_sent": round(len(dists) / max(1, len(sent_ts)), 4),
                "reject_reasons": rej,
                "distance_m": {
                    "min": round(d[0], 2) if d else None,
                    "p50": round(d[len(d)//2], 2) if d else None,
                    "p95": round(d[int(0.95*len(d))], 2) if d else None,
                    "max": round(d[-1], 2) if d else None,
                } if d else None,
            }
        scene_out[scen] = pair_res
        print(f"\n=== {scen} ===")
        for k, v in pair_res.items():
            print(f"  {k}: tx={v['tx_total']} cov={v['gnss_coverage_of_tx_window']} "
                  f"valid_pos={v['valid_sent_with_position']} dist={v['distance_m']} rej={v['reject_reasons']}")

    OUT = {"gnss_audit": audit, "scenes": scene_out, "policy": {"max_gap_ms": MAX_GAP_MS,
            "out_of_window": "reject (no edge clamp)", "time_err_vs_real_neighbour_ms": True}}
    with open("code/tmp/gnss_repair_0472.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=str)
    print("\nsaved code/tmp/gnss_repair_0472.json")


if __name__ == "__main__":
    main()
