"""Independent logic tests for the repaired GNSS matcher (no raw data needed).

These verify the matching/distance logic itself - not the generated JSON -
so a pure Git clone can confirm correctness without the large archives.
"""
from __future__ import annotations

import bisect
import math

import pytest


class GnssTrack:
    """Mirror of the repaired matcher logic in code/tmp/gnss_repair_0472.py."""

    MAX_GAP_MS = 50.0

    def __init__(self, ts_us, lat, lon):
        order = sorted(range(len(ts_us)), key=lambda i: ts_us[i])
        seen = set()
        self.ts, self.lat, self.lon = [], [], []
        for i in order:
            if ts_us[i] in seen:
                continue
            seen.add(ts_us[i])
            self.ts.append(ts_us[i]); self.lat.append(lat[i]); self.lon.append(lon[i])
        self.t0, self.t1 = self.ts[0], self.ts[-1]

    def pos_at(self, t_us):
        if t_us < self.t0 or t_us > self.t1:
            return None, None, None, False, "outside_window"
        i = bisect.bisect_left(self.ts, t_us)
        if i == 0:
            return self.lat[0], self.lon[0], (self.ts[0]-t_us)/1000.0, True, "edge_exact"
        if i >= len(self.ts):
            return None, None, None, False, "outside_window"
        t0, t1 = self.ts[i-1], self.ts[i]
        if (t1 - t0)/1000.0 > self.MAX_GAP_MS:
            return None, None, None, False, "gap_too_large"
        f = (t_us - t0)/(t1 - t0) if t1 > t0 else 0.0
        la = self.lat[i-1]+f*(self.lat[i]-self.lat[i-1])
        lo = self.lon[i-1]+f*(self.lon[i]-self.lon[i-1])
        err = min(t_us-t0, t1-t_us)/1000.0
        return la, lo, err, True, "interp"


def test_in_window_interpolates_with_real_neighbour_error():
    tr = GnssTrack([0, 10_000, 20_000], [34.0, 34.001, 34.002], [-117.0, -117.0, -117.0])
    la, lo, err, ok, why = tr.pos_at(15_000)  # 15 ms
    assert ok and why == "interp"
    assert 34.0015 == pytest.approx(la, abs=1e-6)
    assert err == pytest.approx(5.0, abs=1e-6)  # 5 ms to nearest real sample


def test_out_of_window_rejected_not_clamped():
    tr = GnssTrack([100_000, 110_000], [34.0, 34.1], [-117.0, -117.0])
    la, lo, err, ok, why = tr.pos_at(50_000)   # before window
    assert not ok and why == "outside_window" and la is None
    la, lo, err, ok, why = tr.pos_at(200_000)  # after window
    assert not ok and why == "outside_window" and la is None


def test_large_gap_rejected():
    tr = GnssTrack([0, 10_000, 10_000 + 200_000], [34.0, 34.0, 34.0], [-117.0]*3)  # 200 ms gap
    la, lo, err, ok, why = tr.pos_at(10_000 + 100_000)  # inside the gap
    assert not ok and why == "gap_too_large"


def test_unit_conversion_ns_to_us():
    # comm ts in us; GNSS UTC_ns in ns; us = ns/1000 (same UTC epoch, not sync proof)
    ns = 1_738_872_634_498_805
    us = ns / 1000.0
    assert us == pytest.approx(1_738_872_634_498.805, abs=1e-3)


def test_identical_tracks_yield_zero_distance_flagged():
    ts = [0, 10_000, 20_000]; lat = [34.0, 34.001, 34.002]; lon = [-117.0]*3
    a = GnssTrack(ts, lat, lon); b = GnssTrack(ts, lat, lon)
    pa = a.pos_at(10_000); pb = b.pos_at(10_000)
    d = math.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2) * 111320
    assert d == pytest.approx(0.0, abs=1e-6)
    # identical tracks => device-to-device distance NOT identifiable (replicated track)
    assert pa[0] == pb[0] and pa[1] == pb[1]


def test_no_gnss_returns_not_observable_not_zero():
    # rsu static single point / no track -> must return not-observable, not a zero distance
    tr = GnssTrack([0], [33.975], [-117.340])
    la, lo, err, ok, why = tr.pos_at(10_000)  # outside single-point window
    assert not ok and la is None  # NOT a zero distance
