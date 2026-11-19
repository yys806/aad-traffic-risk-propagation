"""把 NGSIM 实测的（车速, THW）样本抽出来，存成可复用的抽样池

阶段：P3（场景改造）｜ 数据：dataset/NGSIM（只读）
脚本：code/scripts/p3_audits/extract_ngsim_pool.py
产物：code/outputs/analysis/P3_scenario_check/ngsim_pool.npz

用途：改造后的仿真场景，初始车头距与目标速度从这个池子里抽，
      保证异质性的方差与形状来自实测，而不是拍出来的。

注意：NGSIM 是英尺制。速度 ft/s -> m/s。
THW 用**车头到车头**口径（= (y1-y0)/v），与 NGSIM 官方 Time_Headway 一致，
也与我们的仿真场景（40 m 车头到车头）同口径。用净距会系统性低估一个车长/速度。
"""
from __future__ import annotations

import csv
import io
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

FT2M = 0.3048
V_MIN_MS = 5.0
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


def collect(outer: Path, thw_acc: list, spd_acc: list) -> int:
    n = 0
    for name, fh in iter_csv(outer, "trajectories-"):
        rdr = csv.DictReader(fh)
        frames: dict[int, list] = defaultdict(list)
        for row in rdr:
            try:
                fid = int(row["Frame_ID"])
            except (KeyError, ValueError, TypeError):
                continue
            if fid > MAX_FRAMES:
                break
            try:
                frames[fid].append((str(row["Lane_ID"]), float(row["Local_Y"]),
                                    float(row["v_Vel"]), float(row["v_Length"])))
            except (KeyError, ValueError, TypeError):
                continue
        for fid, rows in frames.items():
            lanes: dict[str, list] = defaultdict(list)
            for rec in rows:
                lanes[rec[0]].append(rec[1:])
            for lane, lst in lanes.items():
                lst.sort(key=lambda r: r[0])
                for (y0, v0, l0), (y1, v1, l1) in zip(lst[:-1], lst[1:]):
                    h2h_ft = (y1 - y0)                     # 车头到车头（标准口径）
                    if h2h_ft <= 1.0 or v0 < V_MIN_MS / FT2M:
                        continue
                    thw_acc.append(h2h_ft / v0)          # s
                    spd_acc.append(v0 * FT2M)            # m/s
                    n += 1
    return n


def main() -> int:
    root = Path("D:/shen/TJU/AAD/dataset/NGSIM")
    thw: list[float] = []
    spd: list[float] = []
    for name in ["US-101-LosAngeles-CA.zip", "I-80-Emeryville-CA.zip"]:
        p = root / name
        if not p.exists():
            print(f"缺文件: {p}")
            continue
        n = collect(p, thw, spd)
        print(f"{name:34} 跟驰对 {n:7d}", flush=True)

    thw_a = np.array(thw, dtype=np.float32)
    spd_a = np.array(spd, dtype=np.float32)
    print(f"\n合计 {thw_a.size} 对")
    print(f"车速 {spd_a.min()*3.6:.1f}–{spd_a.max()*3.6:.1f} km/h")
    print(f"THW {np.percentile(thw_a,10):.2f} (p10) / "
          f"{np.percentile(thw_a,50):.2f} (p50) / {np.percentile(thw_a,90):.2f} (p90) s")

    # 也存一份 80–105 km/h 层的子集，供高速场景抽样
    hi = (spd_a * 3.6 >= 80.0) & (spd_a * 3.6 <= 105.0)
    print(f"80–105 km/h 层：{hi.sum()} 对，"
          f"THW p25={np.percentile(thw_a[hi],25):.2f} "
          f"p50={np.percentile(thw_a[hi],50):.2f} "
          f"p90={np.percentile(thw_a[hi],90):.2f}")

    dst = Path("code/outputs/analysis/P3_scenario_check")
    dst.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(dst / "ngsim_pool.npz",
                        thw=thw_a, spd_mps=spd_a, hi_band=hi)
    print(f"written: {dst / 'ngsim_pool.npz'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())