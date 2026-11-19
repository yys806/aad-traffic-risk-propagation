"""P3 准入审计 2：目标窗有效跟驰样本、通行量、TTC 缺测处理

阶段：P3 ｜ 数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz
脚本：code/scripts/p3_audits/audit_window_samples.py
产物：code/outputs/analysis/P3_audit_window/samples.json

回答三件事（GPT 第三十四轮指定的审计项）：
1. 目标窗内到底有多少「有效跟驰样本」（有前车、净距 > 0），
   以及有多少帧是「无闭合」（dv<=0，TTC 无定义）——后者是缺测，不能算作零暴露。
2. 两臂的通行量（通过 x=4000 的车数）分别多少，是否可比。
3. TTC 对「无闭合」与「无前车」的处理是否一致、是否会人为压低暴露。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SRC = Path("code/outputs/analysis/P3_hw40_r06_ids/arms.npz")
VEH_LEN = 5.0
TARGET_X = 4000.0
BAND = 50.0
TTC_THR = 2.0
GAP_EPS = 0.5


def analyse(pos, spd, ids, t0, step):
    k0 = int(round(t0 / step))
    n_steps = pos.shape[0]

    frames_in_band = 0          # 目标窗内有车的帧
    veh_steps_in_band = 0       # 区内车·步
    pair_steps_valid = 0        # 有效跟驰对·步（有前车且净距 > GAP_EPS）
    pair_steps_no_leader = 0    # 区内有车但无前车
    pair_steps_no_closing = 0   # 有前车但 dv <= 0（TTC 无定义 = 缺测）
    pair_steps_closing = 0      # 有闭合
    ttc_lt2_steps = 0           # TTC<2 的帧·对
    crossings = 0               # 通过 x=4000 的车数
    crossed = set()

    for k in range(k0, n_steps):
        ok = np.isfinite(pos[k]) & np.isfinite(spd[k])
        if ok.sum() == 0:
            continue
        idxs = np.where(ok)[0]
        x = pos[k][idxs]
        v = spd[k][idxs]
        inb = (x >= TARGET_X - BAND) & (x <= TARGET_X + BAND)
        if inb.any():
            frames_in_band += 1
            veh_steps_in_band += int(inb.sum())

        order = idxs[np.argsort(x)]
        xo = pos[k][order]
        vo = spd[k][order]
        for a, b in zip(range(len(order) - 1), range(1, len(order))):
            xa, xb = xo[a], xo[b]
            if not (TARGET_X - BAND <= xa <= TARGET_X + BAND):
                continue
            g = (xb - xa) - VEH_LEN
            if g <= GAP_EPS:
                continue
            pair_steps_valid += 1
            dv = vo[a] - vo[b]
            if dv > 0:
                pair_steps_closing += 1
                if g / dv < TTC_THR:
                    ttc_lt2_steps += 1
            else:
                pair_steps_no_closing += 1

    # 通过 x=4000 的车数：任一帧位置 > 4000 且上一帧 <= 4000
    for i in range(pos.shape[1]):
        col = pos[:, i]
        fin = np.isfinite(col)
        if fin.sum() < 2:
            continue
        idx = np.where(fin)[0]
        for a, b in zip(idx[:-1], idx[1:]):
            if col[a] <= TARGET_X < col[b]:
                crossed.add(i)
                break
    crossings = len(crossed)

    return {
        "frames_with_vehicle_in_band": frames_in_band,
        "veh_steps_in_band": veh_steps_in_band,
        "pair_steps_valid_gap": pair_steps_valid,
        "pair_steps_closing": pair_steps_closing,
        "pair_steps_no_closing": pair_steps_no_closing,
        "no_closing_share": round(pair_steps_no_closing / max(pair_steps_valid, 1), 4),
        "ttc_lt2_pair_steps": ttc_lt2_steps,
        "ttc_lt2_veh_seconds": round(ttc_lt2_steps * step, 3),
        "vehicles_crossing_x4000": crossings,
    }


def main() -> int:
    d = np.load(SRC, allow_pickle=False)
    t0 = float(d["event_t0"])
    step = float(d["step_s"])

    out = {"source": str(SRC), "event_t0_s": t0, "target_x": TARGET_X,
           "band_m": BAND, "ttc_thr_s": TTC_THR, "gap_eps_m": GAP_EPS}
    for arm, pkey, skey, ikey in (("plain", "plain_pos", "plain_spd", "plain_ids"),
                                  ("stop", "stop_pos", "stop_spd", "stop_ids")):
        ids = [str(x) for x in d[ikey]]
        out[arm] = analyse(d[pkey], d[skey], ids, t0, step)

    dst = Path("code/outputs/analysis/P3_audit_window")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "samples.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                      encoding="utf-8")

    print(f"{'指标':>34} {'plain':>12} {'stop':>12}")
    keys = ["frames_with_vehicle_in_band", "veh_steps_in_band", "pair_steps_valid_gap",
            "pair_steps_closing", "pair_steps_no_closing", "no_closing_share",
            "ttc_lt2_pair_steps", "ttc_lt2_veh_seconds", "vehicles_crossing_x4000"]
    labels = ["目标窗内有车的帧", "区内车·步", "有效跟驰对·步（g>0.5）",
              "其中有闭合（dv>0）", "其中无闭合（TTC 无定义=缺测）", "无闭合占比",
              "TTC<2 的对·步", "TTC<2 车·秒", "通过 x=4000 的车数"]
    for k, lb in zip(keys, labels):
        print(f"{lb:>34} {str(out['plain'][k]):>12} {str(out['stop'][k]):>12}")
    print(f"\nwritten: {dst / 'samples.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())