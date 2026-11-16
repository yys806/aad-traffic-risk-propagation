"""Scan driver-state awareness and measure whether near-conflict events appear.

WHY: the existing B00/Task8 scene starts every vehicle at the same speed with uniform
spacing and sigma=0.25, so no vehicle ever closes on its leader and P2 events stay ~0.
This script keeps that scene unchanged and adds SUMO's built-in `driverstate` device,
which injects perception errors (misjudged headway / speed difference) and lengthens
reaction time as awareness drops.

Reused from `code/scripts/run_p2_task7_parameter_experiment.py::one` (do not re-invent):
  network file, vehicle layout, spacing per density, departSpeed, tau, sigma, maxSpeed,
  SUMO binary flags, 50 s horizon, 0.05 s step, ballistic, seed handling.

New here: the vType gains driverstate params, and the output is a TTC summary rather
than a full formal pipeline.

EXPLORATORY. Not a formal P2 measurement.

Usage:
  python code/scripts/scan_driverstate_awareness.py --output <dir> --awareness 1.0 0.6 0.3
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NET = ROOT / "code/outputs/calibration/p2_task8_20261102_v1/config/network.net.xml"
SUMO_BIN = Path(r"C:/Program Files (x86)/Eclipse/Sumo/bin/sumo.exe")
SUMO_HOME = SUMO_BIN.parent.parent

DENSITIES = {"high": (64, 15.0)}
STEP = 0.05
END = 50.0
STEPS = int(round(END / STEP))
TTC_THRESH = 2.0
PERSIST = 0.2
MAX_GAP = 0.11


def vtype_xml(awareness: float, with_device: bool, reaction_s: float = 1.5,
              min_awareness: float = 0.1, headway_coef: float = 0.75) -> str:
    base = ('<vType id="native" carFollowModel="Krauss" accel="2.6" decel="4.5" '
            'emergencyDecel="9" length="5" minGap="2.5" tau="0.6" sigma="0.25" '
            'maxSpeed="10" speedFactor="1" speedDev="0" lcStrategic="-1" '
            'lcCooperative="-1" lcSpeedGain="-1" lcKeepRight="-1"')
    if not with_device:
        return base + "/>"
    params = (
        f'<param key="device.driverstate.probability" value="1"/>'
        f'<param key="device.driverstate.initialAwareness" value="{awareness}"/>'
        f'<param key="device.driverstate.headwayErrorCoefficient" value="{headway_coef}"/>'
        f'<param key="device.driverstate.speedDifferenceErrorCoefficient" value="0.15"/>'
        f'<param key="device.driverstate.maximalReactionTime" value="{reaction_s}"/>'
        f'<param key="device.driverstate.minAwareness" value="{min_awareness}"/>'
    )
    return base + ">" + params + "</vType>"


def build_scene(folder: Path, density: str, seed: int, awareness: float, with_device: bool,
                reaction_s: float = 1.5, min_awareness: float = 0.1,
                headway_coef: float = 0.75) -> Path:
    count, spacing = DENSITIES[density]
    ids = [f"s{i}" for i in range(count)] + ["decoy"]
    vehicles = "".join(
        f'<vehicle id="s{i}" type="native" route="r" depart="0" departLane="0" '
        f'departPos="{2800 - spacing * i}" departSpeed="10"/>'
        for i in range(count))
    vehicles += ('<vehicle id="decoy" type="native" route="r" depart="0" '
                 'departLane="1" departPos="2800" departSpeed="10"/>')
    route = folder / "traffic.rou.xml"
    route.write_text(
        "<routes>" + vtype_xml(awareness, with_device, reaction_s, min_awareness, headway_coef) +
        '<route id="r" edges="cal"/>' + vehicles + "</routes>", encoding="utf-8")
    return route


def simulate(folder: Path, density: str, seed: int, awareness: float, with_device: bool,
             reaction_s: float = 1.5, min_awareness: float = 0.1, headway_coef: float = 0.75,
             end_s: float = END):
    steps = int(round(end_s / STEP))
    route = build_scene(folder, density, seed, awareness, with_device, reaction_s,
                        min_awareness, headway_coef)
    os.environ["SUMO_HOME"] = str(SUMO_HOME)
    sys.path.insert(0, str(SUMO_HOME / "tools"))
    import traci  # noqa: E402

    command = [str(SUMO_BIN), "-n", str(NET), "-r", str(route),
               "--step-length", str(STEP), "--end", str(end_s), "--seed", str(seed),
               "--step-method.ballistic", "true", "--no-step-log", "true",
               "--duration-log.disable", "true", "--collision.action", "warn",
               "--log", str(folder / "sumo.log"), "--error-log", str(folder / "error.log")]

    count, _ = DENSITIES[density]
    ids = [f"s{i}" for i in range(count)] + ["decoy"]
    n = len(ids)
    v = np.full((steps, n), np.nan)
    gap = np.full((steps, n), np.nan)
    v_lead = np.full((steps, n), np.nan)
    pos = np.full((steps, n), np.nan)

    traci.start(command, label="scan", verbose=False)
    conn = traci.getConnection("scan")
    collisions = 0
    try:
        for k in range(steps):
            conn.simulationStep()
            try:
                collisions += len(conn.simulation.getCollisions())
            except Exception:  # noqa: BLE001 - older TraCI without collision API
                pass
            for j, vid in enumerate(ids):
                if vid not in conn.vehicle.getIDList():
                    continue
                v[k, j] = conn.vehicle.getSpeed(vid)
                pos[k, j] = conn.vehicle.getPosition(vid)[0]
                lead = conn.vehicle.getLeader(vid, 100.0)
                if lead:
                    gap[k, j] = lead[1]
                    v_lead[k, j] = conn.vehicle.getSpeed(lead[0])
    finally:
        conn.close()

    return v, gap, v_lead, pos, collisions


REGION = (1600.0, 3080.0)
REGION_KM = (REGION[1] - REGION[0]) / 1000.0


def p2_events(ttc, t, thresh=TTC_THRESH, persist=PERSIST, max_gap=MAX_GAP, step=STEP):
    """Formal-P2-shaped event counting: TTC below threshold, observed span >= persist,
    consecutive samples no further apart than max_gap. One event per qualifying segment."""
    events = []
    for j in range(ttc.shape[1]):
        series = ttc[:, j]
        below = np.isfinite(series) & (series < thresh)
        if not below.any():
            continue
        idx = np.flatnonzero(below)
        if idx.size == 1:
            continue
        breaks = np.flatnonzero(np.diff(idx) * step > max_gap + 1e-12)
        for g in np.split(idx, breaks + 1):
            if g.size < 2:
                continue
            span = float(t[g[-1]] - t[g[0]])
            if span >= persist - 1e-12:
                events.append({"vehicle_col": int(j), "onset_s": float(t[g[0]]),
                               "span_s": span, "min_ttc_s": float(series[g].min()),
                               "sample_count": int(g.size)})
    return events


def ttc_summary(v, gap, v_lead, pos, step=STEP):
    t = np.arange(v.shape[0]) * step
    # True TTC: gap between vehicles minus the leader's minGap allowance is already
    # baked into SUMO's getLeader distance; closing speed = ego - leader.
    out = {}
    with np.errstate(invalid="ignore"):
        closing = v - v_lead
    ttc = np.where((closing > 1e-6) & np.isfinite(gap), gap / np.maximum(closing, 1e-9), np.nan)
    valid = np.isfinite(ttc)
    out["n_ttc_samples"] = int(valid.sum())
    if valid.any():
        out["ttc_min_s"] = float(np.nanmin(ttc))
        for thr in (1.0, 2.0, 3.0, 5.0):
            out[f"below_{thr}s_samples"] = int((ttc[valid] < thr).sum())
    else:
        out["ttc_min_s"] = None
    out["gap_min_m"] = float(np.nanmin(gap)) if np.isfinite(gap).any() else None
    out["v_std_mean"] = float(np.nanmean(np.nanstd(v, axis=1)))

    # --- traffic state inside the fixed region (must stay realistic) ---
    inside = np.isfinite(pos) & (pos >= REGION[0]) & (pos < REGION[1])
    counts = inside.sum(axis=1).astype(float)
    out["veh_in_region_mean"] = float(counts.mean())
    out["density_veh_per_km_lane"] = float(counts.mean() / REGION_KM)
    v_in = np.where(inside, v, np.nan)
    out["v_mean_in_region"] = float(np.nanmean(v_in)) if np.isfinite(v_in).any() else None
    out["v_std_in_region"] = float(np.nanstd(v_in)) if np.isfinite(v_in).any() else None

    # --- P2-shaped events and rate per P2-evaluable following vehicle-hour ---
    ev = p2_events(ttc, t)
    exposure_veh_h = float(valid.sum()) * step / 3600.0
    out["p2_events"] = len(ev)
    out["exposure_veh_h"] = exposure_veh_h
    out["p2_rate_per_veh_h"] = (len(ev) / exposure_veh_h) if exposure_veh_h > 0 else None
    out["event_min_ttc"] = [round(e["min_ttc_s"], 3) for e in ev[:10]]
    out["event_span"] = [round(e["span_s"], 2) for e in ev[:10]]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--awareness", type=float, nargs="+", default=[1.0, 0.6, 0.3])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--reaction-time", type=float, default=1.5)
    ap.add_argument("--min-awareness", type=float, default=0.1)
    ap.add_argument("--headway-coef", type=float, default=0.75)
    ap.add_argument("--tag", default="", help="suffix for the summary file to avoid overwrite")
    ap.add_argument("--end", type=float, default=END, help="simulation horizon in seconds")
    ap.add_argument("--density", default="high")
    args = ap.parse_args()

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for aw in args.awareness:
        for s in range(args.seeds):
            seed = 20261116 + s
            folder = outdir / f"aw{aw:.2f}_seed{seed}"
            folder.mkdir(parents=True, exist_ok=True)
            try:
                v, gap, v_lead, pos, coll = simulate(
                    folder, args.density, seed, aw, with_device=(aw < 1.0),
                    reaction_s=args.reaction_time, min_awareness=args.min_awareness,
                    headway_coef=args.headway_coef, end_s=args.end)
                summary = ttc_summary(v, gap, v_lead, pos)
                summary.update({"awareness": aw, "seed": seed, "collisions": coll,
                                "status": "OK"})
            except Exception as exc:  # noqa: BLE001
                summary = {"awareness": aw, "seed": seed, "status": f"FAILED: {type(exc).__name__}: {exc}"}
            results.append(summary)
            print(json.dumps(summary, ensure_ascii=False), flush=True)

    tag = args.tag or f"aw{'-'.join(f'{a:g}' for a in args.awareness)}_rt{args.reaction_time:g}_mo{args.min_awareness:g}"
    (outdir / f"scan_summary_{tag}.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
