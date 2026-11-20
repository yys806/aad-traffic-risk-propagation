"""0.2.10 从 NGSIM 抽完整 τ 分布（供 τ 异质性验证抽样用）

【映射依据】完全沿用 `calibrate_tau_from_ngsim.py`（0.0.2，43.8 万对已验证）：
    τ̂_i = (H_i − 前车车长_i − minGap) / v_i
    H_i = 车头到车头距离（NGSIM 官方口径，英尺，已确认）
这与 Krauss 稳态关系 g = v·τ + minGap 严格一致（H = g + L_lead）。

【筛选口径】与 0.0.2 完全一致，不得改：
  v ≥ 5 m/s；h2h > 1 ft；|自车加速度| ≤ 1.0 m/s²；τ ∈ (0, 5.0]；
  跳过 MOTORCYCLES 重建版。

【与 0.0.2 的唯一差别】0.0.2 只输出分层 p25/p50/p75 汇总；
本脚本额外把完整 τ 数组存成 .npy，供逐车抽样，不改任何筛选。

数据：dataset/NGSIM（zip，只读）
产物：code/outputs/analysis/P3_tau_dist/{tau_samples.npy, meta.json}
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(r"D:/shen/TJU/AAD")
NGSIM = ROOT / "dataset/NGSIM"
OUT = ROOT / "code/outputs/analysis/P3_tau_dist"

FT2M = 0.3048
MIN_GAP = 2.5
V_MIN_MS = 5.0
ACC_MAX = 1.0
MAX_FRAMES = 20000


def iter_csv(outer: Path):
    with zipfile.ZipFile(outer) as z:
        for nm in z.namelist():
            if not nm.endswith(".zip"):
                continue
            with zipfile.ZipFile(io.BytesIO(z.read(nm))) as z2:
                for f in z2.namelist():
                    if (f.endswith(".csv") and "trajectories-" in f
                            and "MOTORCYCLES" not in f):
                        with z2.open(f) as fh:
                            yield f, io.TextIOWrapper(fh, encoding="utf-8-sig",
                                                      errors="replace")


def collect(outer: Path, acc: list) -> int:
    n = 0
    for name, fh in iter_csv(outer):
        rdr = csv.DictReader(fh)
        frames: dict[int, list] = defaultdict(list)
        for row in rdr:
            try:
                fid = int(row["Frame_ID"])
                rec = (str(row["Lane_ID"]), float(row["Local_Y"]),
                       float(row["v_Vel"]), float(row["v_Length"]),
                       float(row.get("v_Acc", 0.0)), str(row["Vehicle_ID"]))
            except (KeyError, ValueError, TypeError):
                continue
            frames[fid].append(rec)
            if fid > MAX_FRAMES:
                break
        for fid, rows in frames.items():
            lanes: dict[str, list] = defaultdict(list)
            for rec in rows:
                lanes[rec[0]].append(rec[1:])
            for lane, lst in lanes.items():
                lst.sort(key=lambda r: r[0])
                for (y0, v0, _l0, a0, vid0), (y1, _v1, l1, _a1, _vid1) in \
                        zip(lst[:-1], lst[1:]):
                    h2h_ft = y1 - y0
                    v_ms = v0 * FT2M
                    if h2h_ft <= 1.0 or v_ms < V_MIN_MS:
                        continue
                    if abs(a0) > ACC_MAX:
                        continue
                    tau_hat = (h2h_ft * FT2M - (l1 * FT2M + MIN_GAP)) / v_ms
                    if tau_hat <= 0 or tau_hat > 5.0:
                        continue
                    acc.append((tau_hat, v_ms, str(name), vid0))
                    n += 1
    return n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    acc: list = []
    for outer in sorted(NGSIM.glob("*.zip")):
        k = collect(outer, acc)
        print(f"  {outer.name}: {k} 对", flush=True)
    if not acc:
        print("无样本")
        return 1

    tau = np.array([a[0] for a in acc], dtype=float)
    spd = np.array([a[1] for a in acc], dtype=float)
    files = np.array([a[2] for a in acc])

    print(f"\n合计 {len(tau)} 对")
    qs = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct = {f"p{q}": round(float(np.percentile(tau, q)), 3) for q in qs}
    print("τ 分位:", pct)
    print(f"τ 均值 {tau.mean():.3f}  标准差 {tau.std():.3f}")
    print(f"车速 {spd.min():.2f}-{spd.max():.2f} m/s")

    m = (spd >= 22.2) & (spd <= 29.2)
    print(f"\n高速层 22.2-29.2 m/s：{int(m.sum())} 对，τ 中位 {np.median(tau[m]):.3f}")

    for lo, hi, tag in [(10.0, 15.0, "36-54km/h"), (15.0, 22.2, "54-80km/h"),
                        (22.2, 29.2, "80-105km/h"), (29.2, 40.0, ">105km/h")]:
        mm = (spd >= lo) & (spd < hi)
        if mm.sum() > 0:
            print(f"  {tag:>10}: n={int(mm.sum()):>7} "
                  f"tau_p25={np.percentile(tau[mm], 25):.3f} "
                  f"p50={np.median(tau[mm]):.3f} "
                  f"p75={np.percentile(tau[mm], 75):.3f}")

    np.save(OUT / "tau_samples.npy", tau)
    np.save(OUT / "speed_samples.npy", spd)
    (OUT / "meta.json").write_text(json.dumps({
        "mapping": "tau = (head_to_head_ft*0.3048 - (lead_len_ft*0.3048 + minGap)) / v_ms",
        "mapping_source": "calibrate_tau_from_ngsim.py (0.0.2)，同口径",
        "filters": {"v_min_ms": V_MIN_MS, "acc_max": ACC_MAX,
                    "h2h_min_ft": 1.0, "tau_range": [0, 5.0],
                    "skip": "MOTORCYCLES 重建版"},
        "n_pairs": int(len(tau)),
        "percentiles": pct,
        "mean": round(float(tau.mean()), 3),
        "std": round(float(tau.std()), 3),
        "speed_range": [round(float(spd.min()), 2), round(float(spd.max()), 2)],
        "hi_band_22.2_29.2": {"n": int(m.sum()),
                              "tau_p50": round(float(np.median(tau[m])), 3)},
        "n_files": int(len(set(files.tolist()))),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT/'tau_samples.npy'} ({len(tau)} samples) + meta.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())