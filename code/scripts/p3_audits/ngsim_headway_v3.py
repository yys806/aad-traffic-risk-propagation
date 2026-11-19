"""NGSIM 真实轨迹：按速度分层的「时间车头距 THW」分布（v3）

目的：判断仿真场景（车头到车头 40 m @ 30 m/s = THW 1.33 s，108 km/h）能否代表真实道路。

阶段：P3（场景代表性核查）｜ 数据：dataset/NGSIM/*.zip（只读）
脚本：code/scripts/p3_audits/ngsim_headway_v3.py
产物：code/outputs/analysis/P3_scenario_check/ngsim_thw_by_speed.json

单位修正（v2 的错）：
  **NGSIM 原始数据是英尺制**——Local_Y、Space_Headway、v_Length 是 ft，v_Vel 是 ft/s。
  v2 把 v_Vel 当 m/s 乘 3.6 报 km/h，把 Local_Y 当 m 报净距，全错。
  THW = 净距 / 速度 = ft / (ft/s) = 秒，**比值本身不受影响**，所以 v2 的 THW 数值仍有效。

口径：
  * 只取同车道、同帧、按 Local_Y 排序的紧邻跟驰对
  * 只用 v_Vel > 5 m/s（≈ 11 mph）的样本
  * THW = 净距(ft) / 后车速(ft/s)
  * **按后车速度分层**：40/60/80/100/110/120 km/h 以上各层单独报 THW 分位数
  这是关键——高速下的 THW 分布才决定「108 km/h 配 1.33 s」是否成立
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

FT2M = 0.3048
V_MIN_MS = 5.0
MAX_FRAMES = 3000
BINS_KMH = [0, 40, 60, 80, 100, 110, 120, 999]


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


def profile(name: str, fh, acc_thw, acc_spd):
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

    n = 0
    for fid, rows in frames.items():
        lanes: dict[str, list] = defaultdict(list)
        for rec in rows:
            lanes[rec[0]].append(rec[1:])
        for lane, lst in lanes.items():
            lst.sort(key=lambda r: r[0])
            for (y0, v0, l0), (y1, v1, l1) in zip(lst[:-1], lst[1:]):
                gap_ft = (y1 - y0) - l0
                if gap_ft <= 1.0 or v0 < V_MIN_MS / FT2M:
                    continue
                acc_thw.append(gap_ft / v0)                  # 秒
                acc_spd.append(v0 * FT2M * 3.6)              # km/h
                n += 1
    return n


def stratify(thw: np.ndarray, spd: np.ndarray) -> dict:
    out = {}
    for lo, hi in zip(BINS_KMH[:-1], BINS_KMH[1:]):
        m = (spd >= lo) & (spd < hi)
        if m.sum() < 200:
            continue
        t = thw[m]
        out[f"{lo}-{hi if hi < 999 else '+'} km/h"] = {
            "n": int(m.sum()),
            "p10": round(float(np.percentile(t, 10)), 2),
            "p25": round(float(np.percentile(t, 25)), 2),
            "p50": round(float(np.percentile(t, 50)), 2),
            "p75": round(float(np.percentile(t, 75)), 2),
            "p90": round(float(np.percentile(t, 90)), 2),
        }
    return out


def main() -> int:
    root = Path("D:/shen/TJU/AAD/dataset/NGSIM")
    targets = ["US-101-LosAngeles-CA.zip", "I-80-Emeryville-CA.zip"]
    acc_thw: list[float] = []
    acc_spd: list[float] = []
    files = []
    for t in targets:
        p = root / t
        if not p.exists():
            print(f"缺文件: {p}")
            continue
        print(f"=== {t} ===", flush=True)
        for name, fh in iter_csv(p, "trajectories-"):
            n = profile(name, fh, acc_thw, acc_spd)
            print(f"  {name.split('/')[-1]:44} 跟驰对 {n:6d}", flush=True)
            files.append({"file": name.split("/")[-1], "n": n})

    thw = np.array(acc_thw)
    spd = np.array(acc_spd)
    out = {
        "note": "NGSIM 原始为英尺制；THW=净距(ft)/车速(ft/s) 单位为秒；速度层用后车速转换",
        "total_pairs": int(thw.size),
        "speed_range_kmh": [round(float(spd.min()), 1), round(float(spd.max()), 1)],
        "overall": {
            "p10": round(float(np.percentile(thw, 10)), 2),
            "p25": round(float(np.percentile(thw, 25)), 2),
            "p50": round(float(np.percentile(thw, 50)), 2),
            "p90": round(float(np.percentile(thw, 90)), 2),
        },
        "by_speed": stratify(thw, spd),
        "files": files,
    }
    dst = Path("code/outputs/analysis/P3_scenario_check")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "ngsim_thw_by_speed.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n总计 {thw.size} 个跟驰对，车速范围 "
          f"{spd.min():.0f}–{spd.max():.0f} km/h")
    print(f"全体 THW：p10={out['overall']['p10']} p25={out['overall']['p25']} "
          f"p50={out['overall']['p50']} p90={out['overall']['p90']} s")
    print("\n按后车速度分层：")
    for k, v in out["by_speed"].items():
        print(f"  {k:14} n={v['n']:7d}  p25={v['p25']:.2f}  p50={v['p50']:.2f}  p90={v['p90']:.2f}")
    print("\n我们的场景：108 km/h、车头到车头 40 m（净距 35 m）→ THW = 1.33 s")
    print(f"written: {dst / 'ngsim_thw_by_speed.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())