"""用 NGSIM 真实轨迹量「时间车头距 THW」与速度的联合分布（v2）

目的：判断我们的仿真场景（车头到车头 40 m @ 30 m/s = THW 1.33 s）离真实高速有多远。

阶段：P3（场景代表性核查）｜ 数据：dataset/NGSIM/*.zip（只读）
脚本：code/scripts/p3_audits/ngsim_headway_profile_v2.py
产物：code/outputs/analysis/P3_scenario_check/ngsim_headway.json

v1 失败原因：CSV 带 UTF-8 BOM，DictReader 的键首字符是 \ufeff，导致全部取值 ValueError，n=0。
v2 修正：encoding="utf-8-sig"；并**同时**用两条路算 THW 交叉验证：
  (a) 用 NGSIM 自带的 Space_Headway / Time_Headway 列
  (b) 用同帧 Local_Y 与 v_Length 自算净距，再除以 v_Vel
若两者一致，说明自带字段与位置自洽；不一致则只用自算，并记录差异。
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

V_MIN = 5.0          # m/s，只统计在跑的跟驰对
MAX_FRAMES = 3000    # 每文件最多取多少帧


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


def profile(name: str, fh) -> dict:
    rdr = csv.DictReader(fh)
    frames: dict[int, list] = defaultdict(list)
    native = []          # NGSIM 自带的 Time_Headway
    for row in rdr:
        try:
            fid = int(row["Frame_ID"])
        except (KeyError, ValueError, TypeError):
            continue
        if fid > MAX_FRAMES:
            break
        try:
            frames[fid].append((
                str(row["Lane_ID"]), float(row["Local_Y"]), float(row["v_Vel"]),
                float(row["v_Length"]),
                float(row.get("Time_Headway") or 0.0),
                float(row.get("Space_Headway") or 0.0)))
        except (KeyError, ValueError, TypeError):
            continue

    thw, gaps, spd, native_thw = [], [], [], []
    for fid, rows in frames.items():
        lanes: dict[str, list] = defaultdict(list)
        for rec in rows:
            lanes[rec[0]].append(rec[1:])
        for lane, lst in lanes.items():
            lst.sort(key=lambda r: r[0])          # Local_Y 升序：后 -> 前
            for (y0, v0, l0, thw0, sh0), (y1, v1, l1, _, _) in zip(lst[:-1], lst[1:]):
                gap = (y1 - y0) - l0              # 净距
                if gap <= 0.5 or v0 < V_MIN:
                    continue
                thw.append(gap / v0)
                gaps.append(gap)
                spd.append(v0)
                if thw0 > 0:
                    native_thw.append(thw0)
    if not thw:
        return {"file": name, "n": 0}
    thw = np.array(thw)
    gaps = np.array(gaps)
    spd = np.array(spd)
    out = {
        "file": name, "n": int(thw.size),
        "thw_p10": round(float(np.percentile(thw, 10)), 2),
        "thw_p25": round(float(np.percentile(thw, 25)), 2),
        "thw_p50": round(float(np.percentile(thw, 50)), 2),
        "thw_p75": round(float(np.percentile(thw, 75)), 2),
        "thw_p90": round(float(np.percentile(thw, 90)), 2),
        "gap_p50_m": round(float(np.median(gaps)), 1),
        "spd_p50_kmh": round(float(np.median(spd)) * 3.6, 1),
        "spd_p90_kmh": round(float(np.percentile(spd, 90)) * 3.6, 1),
    }
    if native_thw:
        nt = np.array(native_thw)
        out["native_time_headway_p50"] = round(float(np.median(nt)), 2)
        out["native_vs_recomputed_median_diff"] = round(
            float(np.median(nt) - np.median(thw)), 3)
    return out


def main() -> int:
    root = Path("D:/shen/TJU/AAD/dataset/NGSIM")
    targets = ["US-101-LosAngeles-CA.zip", "I-80-Emeryville-CA.zip"]
    out = {"note": "只用 v_Vel>5 m/s 的同车道紧邻跟驰对；THW=净距/后车速度；"
                   "并报 NGSIM 自带 Time_Headway 作交叉验证（防派生字段含未来帧）",
           "v_min_mps": V_MIN, "files": []}
    for t in targets:
        p = root / t
        if not p.exists():
            print(f"缺文件: {p}")
            continue
        print(f"=== {t} ===", flush=True)
        for name, fh in iter_csv(p, "trajectories-"):
            r = profile(name, fh)
            print(f"  {name.split('/')[-1]:42} n={r.get('n', 0):6d}  "
                  f"THW p50={r.get('thw_p50')}  "
                  f"车速 p50={r.get('spd_p50_kmh')} km/h", flush=True)
            out["files"].append(r)

    dst = Path("code/outputs/analysis/P3_scenario_check")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "ngsim_headway.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = [f for f in out["files"] if f.get("n", 0) > 0]
    if ok:
        allp50 = [f["thw_p50"] for f in ok]
        print(f"\n汇总：{len(ok)} 个文件有效")
        print(f"  THW 中位数范围：{min(allp50)} – {max(allp50)} s")
        print(f"  我们的场景：车头到车头 40 m @ 30 m/s → THW = 1.33 s")
    print(f"\nwritten: {dst / 'ngsim_headway.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())