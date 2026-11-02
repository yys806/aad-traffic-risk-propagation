"""CALIBRATION_ONLY synthetic measurement verification; no traffic-arrival truth.

V2 preserves elapsed-observation persistence, shared panels across candidates,
and disjoint calibration/validation seed families. Never imports production
measurement logic, reads traffic datasets, or launches SUMO.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

STATUS = "CALIBRATION_ONLY"
DOMAIN = "synthetic_measurement_verification"


@dataclass(frozen=True)
class Detector:
    aggregator: str = "mean"
    theta: float = 0.5
    h_s: float = 1.0
    baseline_s: float = 5.0
    q_factor: float = 1.1
    coverage_gate: float = 0.8
    individual_threshold_mps: float = 0.5


@dataclass(frozen=True)
class Scenario:
    name: str
    amplitude_mps: float = 1.0
    duration_s: float = 3.0
    affected: int = 20
    dt_s: float = 0.1
    noise_mps: float = 0.2
    missing: str = "none"
    trend_mps2: float = 0.0
    common_noise_mps: float = 0.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def scenarios() -> list[Scenario]:
    result = [Scenario("null_stationary", 0, 0, 0),
              Scenario("null_trend", 0, 0, 0, trend_mps2=0.02)]
    for amp in (0.5, 1.0):
        for duration in (0.8, 3.0):
            result.append(Scenario(f"broad_{amp}_{duration}", amp, duration))
    result += [Scenario("single_outlier", 8, 3, 1), Scenario("half_cohort", 1, 3, 10),
               Scenario("dt_005", dt_s=0.05), Scenario("dt_020", dt_s=0.2),
               Scenario("noise_050", noise_mps=0.5), Scenario("mcar_020", missing="mcar"),
               Scenario("block_040", missing="block"), Scenario("selective_dropout", missing="dropout"),
               Scenario("common_ar1", common_noise_mps=0.3), Scenario("trend_drop", trend_mps2=0.02)]
    return result


def detectors() -> list[Detector]:
    result = []
    for agg in ("mean", "median", "proportion"):
        for theta in ((0.25, 0.5, 0.75) if agg == "proportion" else (0.25, 0.5, 1.0)):
            for h in (0.5, 1.0, 2.0):
                result.append(Detector(agg, theta, h))
        base = Detector(agg)
        result += [replace(base, baseline_s=w) for w in (2.0, 10.0)]
        result += [replace(base, q_factor=q) for q in (3.1, 5.1)]
        result.append(replace(base, coverage_gate=1.0))
    return result


def panel(s: Scenario, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.arange(int(round(60 / s.dt_s)) + 1) * s.dt_s
    speed = rng.normal(15, 0.35, (20, 1)) + rng.normal(0, s.noise_mps, (20, len(t)))
    speed -= s.trend_mps2 * (t - 30)[None, :]
    if s.common_noise_mps:
        z = rng.normal(0, s.common_noise_mps * np.sqrt(1 - 0.9**2), len(t))
        for j in range(1, len(t)):
            z[j] += 0.9 * z[j - 1]
        speed += z[None, :]
    active = (t >= 30) & (t < 30 + s.duration_s)
    speed[:s.affected, active] -= s.amplitude_mps
    # Missingness begins after source; baseline is always observed in this proxy.
    mask = np.ones_like(speed, dtype=bool)
    if s.missing == "mcar":
        mask[:, t >= 30] = rng.random((20, int((t >= 30).sum()))) >= 0.2
    elif s.missing == "block":
        mask[:, (t >= 30.4) & (t < 30.8)] = False
    elif s.missing == "dropout":
        # Select the strongest four observed responders: deliberately informative.
        ranking = np.argsort(speed[:, np.flatnonzero(t >= 30)[0]])[:4]
        mask[np.ix_(ranking, np.flatnonzero(t >= 30.4))] = False
    return t, np.where(mask, speed, np.nan)


def signals(t: np.ndarray, speed: np.ndarray, d: Detector) -> tuple[np.ndarray, np.ndarray]:
    pre = (t >= 30 - d.baseline_s) & (t < 30)
    baseline = speed[:, pre].mean(axis=1)
    delta = baseline[:, None] - speed
    finite = np.isfinite(delta)
    count = finite.sum(axis=0)
    coverage = count / speed.shape[0]
    stat = np.full(len(t), np.nan)
    usable = count > 0
    if d.aggregator == "mean":
        stat[usable] = np.nansum(delta[:, usable], axis=0) / count[usable]
    elif d.aggregator == "median":
        stat[usable] = np.nanmedian(delta[:, usable], axis=0)
    elif d.aggregator == "proportion":
        stat[usable] = ((delta[:, usable] >= d.individual_threshold_mps) & finite[:, usable]).sum(axis=0) / count[usable]
    else:
        raise ValueError(d.aggregator)
    return stat, coverage


def first_confirmation(t: np.ndarray, stat: np.ndarray, valid: np.ndarray,
                       theta: float, h: float, q: float, start: float) -> dict:
    run_start = None
    previous_positive = None
    last_negative = None
    lower = None
    bridged = False
    for j, time in enumerate(t):
        if time < start:
            if valid[j] and stat[j] < theta:
                last_negative = float(time)
            continue
        if not valid[j]:
            continue  # a later positive must still satisfy the explicit q rule
        if stat[j] < theta:
            run_start = previous_positive = None
            last_negative = float(time)
            bridged = False
            continue
        if run_start is None or time - previous_positive > q + 1e-10:
            run_start = j
            lower = last_negative
            bridged = False
        elif j > previous_index + 1:
            bridged = True
        previous_positive = float(time)
        previous_index = j
        if time - t[run_start] >= h - 1e-10:
            return {"confirmation_s": float(time), "onset_lower_s": lower,
                    "onset_upper_s": float(t[run_start]), "left_censored": lower is None,
                    "gap_bridged": bridged}
    return {"confirmation_s": None, "onset_lower_s": None, "onset_upper_s": None,
            "left_censored": False, "gap_bridged": False}


def classify(result: dict, source: float, duration: float, injected: bool) -> dict:
    conf, upper = result["confirmation_s"], result["onset_upper_s"]
    detected = conf is not None
    early = bool(detected and (conf < source or upper < source))
    recovered = bool(detected and conf >= source + duration - 1e-10) if injected else False
    return {"false_alarm": bool(detected and not injected), "pre_source_alarm": early,
            "late_alarm": recovered,
            "event_detected": bool(injected and detected and not early and not recovered),
            "delay_s": conf - source if injected and detected and not early and not recovered else None}


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    center = (p + z*z / (2*n)) / (1 + z*z/n)
    half = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return max(0.0, center-half), min(1.0, center+half)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=202611020)
    p.add_argument("--validation-seed", type=int, default=202711020)
    p.add_argument("--repetitions", type=int, default=24)
    a = p.parse_args()
    if a.repetitions < 1 or abs(a.seed-a.validation_seed) < 100000:
        p.error("positive repetitions and disjoint seed families required")
    out = a.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    ds, ss = detectors(), scenarios()
    rows = []
    for split, base_seed in (("calibration", a.seed), ("validation", a.validation_seed)):
        for si, s in enumerate(ss):
            for rep in range(a.repetitions):
                seed = base_seed + si*1000 + rep
                t, speed = panel(s, seed)
                cache = {}
                for di, d in enumerate(ds):
                    key = (d.aggregator, d.baseline_s)
                    if key not in cache:
                        cache[key] = signals(t, speed, d)
                    stat, cov = cache[key]
                    valid = np.isfinite(stat) & (cov >= d.coverage_gate - 1e-12)
                    result = first_confirmation(t, stat, valid, d.theta, d.h_s, d.q_factor*s.dt_s, 30)
                    label = classify(result, 30, s.duration_s, bool(s.affected))
                    event_window = (t >= 30) & (t < 30 + s.duration_s) if s.affected else t >= 30
                    quality_unknown = bool(result["confirmation_s"] is None and not np.all(valid[event_window]))
                    rows.append({"status": STATUS, "domain": DOMAIN, "split": split,
                                 "scenario": s.name, "panel_seed": seed, "detector_id": di,
                                 **asdict(d), **result, **label,
                                 "quality_unknown": quality_unknown,
                                 "valid_fraction": float(valid[event_window].mean())})
    write_csv(out / "calibration_runs.csv", rows)
    groups = {}
    for r in rows:
        groups.setdefault((r["split"], r["scenario"], r["detector_id"]), []).append(r)
    summary = []
    for (split, scenario, di), group in groups.items():
        n = len(group)
        row = {"split": split, "scenario": scenario, "detector_id": di, **asdict(ds[di]), "n": n}
        for metric in ("false_alarm", "event_detected", "pre_source_alarm", "late_alarm", "quality_unknown", "gap_bridged"):
            k = sum(bool(r[metric]) for r in group)
            lo, hi = wilson(k, n)
            row.update({metric+"_count": k, metric+"_rate": k/n, metric+"_lo95": lo, metric+"_hi95": hi})
        delays = [r["delay_s"] for r in group if r["delay_s"] is not None]
        row.update(delay_n=len(delays), mean_delay_s=float(np.mean(delays)) if delays else None,
                   median_delay_s=float(np.median(delays)) if delays else None,
                   mean_valid_fraction=float(np.mean([r["valid_fraction"] for r in group])))
        summary.append(row)
    write_csv(out / "calibration_summary.csv", summary)
    protocol = Path("docs/research/P2/P2_TASK3_CALIBRATION_PROTOCOL.md")
    script = Path(__file__)
    write_json(out / "calibration_config.json", {"status": STATUS, "domain": DOMAIN,
               "scenarios": [asdict(s) for s in ss], "detectors": [asdict(d) for d in ds],
               "seed": a.seed, "validation_seed": a.validation_seed, "repetitions": a.repetitions,
               "baseline": "[30-W,30); monitor>=30", "source_onset_s": 30,
               "n_vehicles": 20, "horizon_s": 60, "external_validity": "NONE",
               "protocol_sha256": sha(protocol), "script_sha256": sha(script)})
    (out / "script_snapshot.py").write_bytes(script.read_bytes())
    (out / "protocol_snapshot.md").write_bytes(protocol.read_bytes())
    write_json(out / "provenance.json", {"created_utc": datetime.now(timezone.utc).isoformat(),
               "git_sha": git("rev-parse", "HEAD"), "dirty_status": git("status", "--short"),
               "python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
               "command_argv": sys.argv, "status": STATUS, "domain": DOMAIN})
    message = json.dumps({"status": STATUS, "domain": DOMAIN, "panels": len(ss)*2*a.repetitions,
                          "rows": len(rows), "summary_rows": len(summary), "output": str(out)})
    (out / "calibration_run.log").write_text(message+"\n", encoding="utf-8")
    (out / "SHA256SUMS").write_text("".join(f"{sha(f)}  {f.name}\n" for f in sorted(out.iterdir()) if f.is_file()), encoding="utf-8")
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
