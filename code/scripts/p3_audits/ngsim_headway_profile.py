"""用 NGSIM 真实轨迹量「时间车头距」与「速度」的联合分布

目的：判断我们的仿真场景（40 m 车头距 @ 30 m/s = 1.33 s 时距）离真实高速有多远。

阶段：P3（场景代表性核查）｜ 数据：dataset/NGSIM/*.zip（只读）
脚本：code/scripts/p3_audits/ngsim_headway_profile.py
产物：code/outputs/analysis/P3_scenario_check/ngsim_headway.json

口径：
  * 只取同一车道内、前后紧邻的跟驰对（Frame_ID 相同、同 Lane_ID、按 Local_Y 排序）
  * 时间车头距 THW = 净距 / 后车速度（秒）；净距 = Leader 前端与本车前端距离（NGSIM 已给 Local_Y 与 v_Length）
  * 只用 v_Vel > 5 m/s 的样本（避免停车/排队主导分布）
  * 输出分速度层的 THW 分位数
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np


def iter_csv_from_nested_zip(outer: Path, inner_suffix: str):
    """外层 zip -> 内层 trajectory zip -> 目标 csv 的行。"""
    with zipfile.ZipFile(outer) as z:
        inner = [n for n in z.namelist() if n.endswith(".zip")]
        for nm in inner:
            data = z.read(nm)
            with zipfile.ZipFile(io.BytesIO(data)) as z2:
                for f in z2.namelist():
                    if f.endswith(".csv") and inner_suffix in f:
                        with z2.open(f) as fh:
                            yield f, io.TextIOWrapper(fh, encoding="latin-1")


def profile(csv_name: str, fh, max_frames: int = 400) -> dict:
    reader = csv.DictReader(fh)
    # 逐帧收集 (Lane, Local_Y, v_Vel, v_Length, Vehicle_ID)
    frames: dict[int, list] = defaultdict(list)
    for row in reader:
        try:
            fid = int(row["Frame_ID"])
        except (KeyError, ValueError):
            continue
        if fid > max_frames:
            break
        try:
            frames[fid].append((
                row["Lane_ID"], float(row["Local_Y"]), float(row["v_Vel"]),
                float(row["v_Length"]), row["Vehicle_ID"]))
        except (KeyError, ValueError):
            continue

    thw, gaps, speeds = [], [], []
    for fid, rows in frames.items():
        by_lane: dict[str, list] = defaultdict(list)
        for lane, y, v, ln, vid in rows:
            by_lane[lane].append((y, v, ln, vid))
        for lane, lst in by_lane.items():
            lst.sort(key=lambda r: r[0])          # Local_Y 升序 = 后 -> 前
            for (y0, v0, l0, _), (y1, v1, l1, _) in zip(lst[:-1], lst[1:]):
                gap = (y1 - y0) - l0              # 净距（前车前端 - 本车前端 - 本车长）
                if gap <= 0.5 or v0 < 5.0:
                    continue
                thw.append(gap / v0)
                gaps.append(gap)
                speeds.append(v0)
    if not thw:
        return {"file": csv_name, "n": 0}
    thw = np.array(thw)
    gaps = np.array(gaps)
    speeds = np.array(speeds)
    return {
        "file": csv_name, "n": int(thw.size),
        "thw_p10": round(float(np.percentile(thw, 10)), 2),
        "thw_p50": round(float(np.percentile(thw, 50)), 2),
        "thw_p90": round(float(np.percentile(thw, 90)), 2),
        "gap_p50": round(float(np.median(gaps)), 1),
        "speed_p50_kmh": round(float(np.median(speeds)) * 3.6, 1),
        "speed_p90_kmh": round(float(np.percentile(speeds, 90)) * 3.6, 1),
    }


def main() -> int:
    root = Path("D:/shen/TJU/AAD/dataset/NGSIM")
    targets = ["US-101-Los Angeles-CA.zip", "I-80-Emeryville-CA.zip"]
    out = {"note": "只用 v_Vel>5 m/s 的跟驰对；THW=净距/后车速度", "files": []}
    for t in targets:
        p = root / t
        if not p.exists():
            print(f"缺文件: {p}")
            continue
        print(f"=== {t} ===", flush=True)
        for name, fh in iter_csv_from_nested_zip(p, "trajectories-"):
            print(f"  读取 {name} …", flush=True)
            r = profile(name, fh)
            print(f"    n={r.get('n')}  THW p50={r.get('thw_p50')}s  "
                  f"车速 p50={r.get('speed_p50_kmh')} km/h", flush=True)
            out["files"].append(r)

    dst = Path("code/outputs/analysis/P3_scenario_check")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "ngsim_headway.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwritten: {dst / 'ngsim_headway.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())