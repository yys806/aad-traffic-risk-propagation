"""0.0.2 第一步：从 NGSIM 实测逐样本反推 Krauss 的 τ（期望车头时距）。

依据（GPT 第四十九轮 Q1）：
  τ̂_i = (H_i − 前车车长_i − minGap) / v_i
  其中 H_i 是车头到车头距离（本项目已确认 NGSIM 官方口径为车头到车头）。
  筛掉低速、换道附近、明显加减速、前后车速差大的片段；
  **按车辆加权**（先算每辆车的中位 τ̂，再跨车取中位），避免长轨迹凭帧数占主导。
  先按速度分层看估计值，再取目标工况的中位数；p25 只作低时距尾部验证。

数据：dataset/NGSIM（只读，英尺制）
产物：code/outputs/analysis/P3_tau_calib/tau_from_ngsim.json
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
NGSIM = ROOT / "dataset/NGSIM"
OUT = ROOT / "code/outputs/analysis/P3_tau_calib"

FT2M = 0.3048
MIN_GAP = 2.5          # 与仿真一致
V_MIN_MS = 5.0         # 低速片段剔除
ACC_MAX = 1.0          # |纵向加速度| 上限 m/s²
MAX_FRAMES = 3000


def iter_csv(outer: Path, needle: str):
    with zipfile.ZipFile(outer) as z:
        for nm in z.namelist():
            if not nm.endswith(".zip"):
                continue
            with zipfile.ZipFile(io.BytesIO(z.read(nm))) as z2:
                for f in z2.namelist():
                    if f.endswith(".csv") and needle in f and "MOTORCYCLES" not in f:
                        with z2.open(f) as fh:
                            yield f, io.TextIOWrapper(fh, encoding="utf-8-sig", errors="replace")


def collect(outer: Path, acc: list) -> int:
    n = 0
    for name, fh in iter_csv(outer, "trajectories-"):
        rdr = csv.DictReader(fh)
        frames: dict[int, list] = defaultdict(list)
        for row in rdr:
            try:
                fid = int(row["Frame_ID"])
                rec = (str(row["Lane_ID"]),
                       float(row["Local_Y"]),
                       float(row["v_Vel"]),
                       float(row["v_Length"]),
                       float(row.get("v_Acc", 0.0)),
                       str(row["Vehicle_ID"]),
                       str(row.get("Location", name)))
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
                for (y0, v0, l0, a0, vid0, loc), (y1, v1, l1, a1, vid1, _loc1) in zip(lst[:-1], lst[1:]):
                    h2h_ft = y1 - y0                      # 车头到车头（英尺）
                    v_ms = v0 * FT2M
                    if h2h_ft <= 1.0 or v_ms < V_MIN_MS:
                        continue
                    if abs(a0) > ACC_MAX or abs(v0 - v1) > 5.0:
                        continue                       # 明显加减速 / 前车速度差过大
                    thw = h2h_ft / v0                  # 秒（ft ÷ ft/s）
                    tau_hat = thw - (l1 * FT2M + MIN_GAP) / v_ms
                    if tau_hat <= 0 or tau_hat > 5.0:
                        continue
                    acc.append((tau_hat, thw, v_ms, vid0, loc))
                    n += 1
    return n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    acc: list = []
    total = 0
    for outer in sorted(NGSIM.glob("*.zip")):
        k = collect(outer, acc)
        total += k
        print(f"  {outer.name}: {k} 对", flush=True)
    if not acc:
        print("无样本")
        return 1

    tau = np.array([a[0] for a in acc])
    thw = np.array([a[1] for a in acc])
    spd = np.array([a[2] for a in acc])
    vid = np.array([a[3] for a in acc])
    print(f"\n合计 {total} 对，{len(set(vid.tolist()))} 辆车", flush=True)

    # 按车辆加权：先每辆车的 τ̂ 中位，再跨车取分位数
    per_veh = {}
    for t, v in zip(tau, vid):
        per_veh.setdefault(v, []).append(t)
    veh_med = np.array([np.median(v) for v in per_veh.values()])
    print(f"按车辆加权（{len(veh_med)} 辆）：τ̂ p25={np.percentile(veh_med,25):.3f} "
          f"p50={np.percentile(veh_med,50):.3f} p75={np.percentile(veh_med,75):.3f} s", flush=True)

    # 分速度层（按样本），并给出每层按车辆加权的中位
    bands = [(5, 16.7), (16.7, 22.2), (22.2, 29.2), (29.2, 40.0)]
    rows = []
    print(f"\n{'速度层 m/s':>12} {'样本':>9} {'车辆':>6} {'THW p50':>9} "
          f"{'τ̂样本p50':>10} {'τ̂车辆p50':>10} {'τ̂车辆p25':>10}")
    for lo, hi in bands:
        m = (spd >= lo) & (spd < hi)
        if m.sum() < 100:
            continue
        pv = {}
        for t, v in zip(tau[m], vid[m]):
            pv.setdefault(v, []).append(t)
        vm = np.array([np.median(v) for v in pv.values()])
        row = {"band_mps": [lo, hi], "n": int(m.sum()), "n_veh": len(vm),
               "thw_p50": round(float(np.median(thw[m])), 3),
               "tau_p50_sample": round(float(np.median(tau[m])), 3),
               "tau_p50_vehicle": round(float(np.median(vm)), 3),
               "tau_p25_vehicle": round(float(np.percentile(vm, 25)), 3),
               "tau_p75_vehicle": round(float(np.percentile(vm, 75)), 3)}
        rows.append(row)
        print(f"{lo:>5.1f}–{hi:<6.1f} {row['n']:>9} {len(vm):>6} {row['thw_p50']:>9.3f} "
              f"{row['tau_p50_sample']:>10.3f} {row['tau_p50_vehicle']:>10.3f} "
              f"{row['tau_p25_vehicle']:>10.3f}")

    hi_band = [r for r in rows if r["band_mps"][0] >= 22.2]
    rec = (np.median([r["tau_p50_vehicle"] for r in hi_band]) if hi_band
           else float(np.median(veh_med)))
    print(f"\n推荐 τ（≥22.2 m/s 层按车辆加权中位的跨层中位）= {rec:.3f} s")

    (OUT / "tau_from_ngsim.json").write_text(json.dumps(
        {"n_pairs": total, "n_vehicles": int(len(veh_med)),
         "tau_vehicle_weighted": {"p25": round(float(np.percentile(veh_med, 25)), 3),
                                  "p50": round(float(np.percentile(veh_med, 50)), 3),
                                  "p75": round(float(np.percentile(veh_med, 75)), 3)},
         "bands": rows, "tau_recommended_s": round(float(rec), 3),
         "filters": {"v_min_mps": V_MIN_MS, "acc_max_mps2": ACC_MAX,
                     "min_gap_m": MIN_GAP, "max_frames": MAX_FRAMES},
         "thw_definition": "head-to-head / follower speed"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT/'tau_from_ngsim.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
