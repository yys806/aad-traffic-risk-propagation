"""核对 NGSIM 自带的 Time_Headway 到底用「净距」还是「车头到车头」

阶段：P3（口径核对，GPT 第三十九轮 Q2 要求）
脚本：code/scripts/p3_audits/verify_thw_convention.py
产物：打印三种口径的中位数与官方字段对比

为什么要查：
  标准交通工程的 THW = 车头到车头间距 / 后车速（含前车车身）。
  我之前的实现用了「净距 / 后车速」（不含前车车身），两者差一个车长。
  我们的仿真场景 40 m 是**车头到车头**，所以与 NGSIM 对比必须同口径。
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
MAX_FRAMES = 500


def main() -> int:
    p = Path("D:/shen/TJU/AAD/dataset/NGSIM/I-80-Emeryville-CA.zip")
    frames: dict[int, list] = defaultdict(list)
    with zipfile.ZipFile(p) as z:
        done = False
        for inner in [n for n in z.namelist() if n.endswith(".zip")]:
            if done:
                break
            with zipfile.ZipFile(io.BytesIO(z.read(inner))) as z2:
                tgt = [f for f in z2.namelist()
                       if f.endswith("trajectories-0400-0415.csv")]
                if not tgt:
                    continue
                with z2.open(tgt[0]) as fh:
                    fh = io.TextIOWrapper(fh, encoding="utf-8-sig", errors="replace")
                    rdr = csv.DictReader(fh)
                    for row in rdr:
                        try:
                            fid = int(row["Frame_ID"])
                        except (KeyError, ValueError, TypeError):
                            continue
                        if fid > MAX_FRAMES:
                            done = True
                            break
                        frames[fid].append((
                            str(row["Lane_ID"]), float(row["Local_Y"]), float(row["v_Vel"]),
                            float(row["v_Length"]),
                            float(row.get("Time_Headway") or 0.0),
                            float(row.get("Space_Headway") or 0.0)))
                    done = True

    net, h2h, native, spaceh, vehlen = [], [], [], [], []
    gaps, h2h_m = [], []
    for fid, rows in frames.items():
        lanes: dict[str, list] = defaultdict(list)
        for rec in rows:
            lanes[rec[0]].append(rec[1:])
        for lane, lst in lanes.items():
            lst.sort(key=lambda r: r[0])
            for (y0, v0, l0, thw0, sh0), (y1, v1, l1, _, _) in zip(lst[:-1], lst[1:]):
                gap = (y1 - y0) - l0
                if gap <= 1.0 or v0 < V_MIN_MS / FT2M:
                    continue
                net.append(gap / v0)                 # 净距 / 速度
                h2h.append((y1 - y0) / v0)           # 车头到车头 / 速度
                gaps.append(gap)
                h2h_m.append(y1 - y0)
                if thw0 > 0:
                    native.append(thw0)
                if sh0 > 0:
                    spaceh.append(sh0)
                vehlen.append(l0)

    print(f"样本 {len(net)} 对（{MAX_FRAMES} 帧内，v>5 m/s）")
    print(f"  前车车长中位：{np.median(vehlen)/FT2M:.2f} m")
    print(f"\n三种口径的 THW 中位数：")
    print(f"  净距 / 速度          = {np.median(net):.3f} s")
    print(f"  车头到车头 / 速度    = {np.median(h2h):.3f} s")
    print(f"  两者之差             = {np.median(h2h) - np.median(net):.3f} s")
    if native:
        print(f"\nNGSIM 官方 Time_Headway 中位 = {np.median(native):.3f} s")
        print(f"  与「净距」口径差 = {np.median(native) - np.median(net):+.3f} s")
        print(f"  与「车头到车头」口径差 = {np.median(native) - np.median(h2h):+.3f} s")
        which = ("净距" if abs(np.median(native) - np.median(net))
                 < abs(np.median(native) - np.median(h2h)) else "车头到车头")
        print(f"\n=> 官方字段更接近【{which}】口径")
    if spaceh:
        print(f"\nNGSIM 官方 Space_Headway 中位 = {np.median(spaceh)/FT2M:.2f} m")
        print(f"  我们算的净距中位            = {np.median(gaps)/FT2M:.2f} m")
        print(f"  车头到车头中位              = {np.median(h2h_m)/FT2M:.2f} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())