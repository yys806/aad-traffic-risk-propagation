"""旧事件场景取证：22.9 车·秒的低 TTC 出在哪些车对、什么闭合阶段

阶段：P3 ｜ GPT 第四十轮 Q7 第 1 步
脚本：code/scripts/p3_audits/forensics_low_ttc.py
数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz（含车辆 ID）
产物：code/outputs/analysis/P3_forensics/low_ttc.json + 文本摘要

要回答的问题（GPT 原话）：
  「确认低 TTC 出现在什么车对、什么闭合阶段，而不只知道总量。」

口径（与主脚本一致）：
  * 目标带 x = 4000 ± 50 m
  * 以后车是否在带内确定计数，前车可在带外
  * TTC = 净距 / 闭合速度，只计闭合为正（v_ego > v_lead）
  * 低 TTC 定义 TTC < 2.0 s
  * 净距 = 前车位置 − 本车位置 − 车长（5 m）
  * THW 另按车头到车头算，两者都报，避免口径混淆
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
TARGET_X = 4000.0
BAND = 50.0
TTC_THR = 2.0
STEP = 0.05


def leader_table(x: np.ndarray, ok: np.ndarray):
    """单车道：按位置排序后，后一辆的前车是紧邻的那辆。返回 (lead_idx, gap_m)。"""
    n = x.size
    lead = np.full(n, -1, dtype=np.int64)
    gap = np.full(n, np.nan)
    if ok.sum() < 2:
        return lead, gap
    idx = np.where(ok)[0]
    order = idx[np.argsort(x[idx])]
    for a, b in zip(order[:-1], order[1:]):
        lead[a] = b
        gap[a] = (x[b] - x[a]) - VEH_LEN
    return lead, gap


def analyse(arm_key: str, pos, spd, ids, t0: float, label: str) -> dict:
    n_steps = pos.shape[0]
    events = []                       # 每一次 (帧, 后车) 的低 TTC 记录
    total_veh_sec = 0.0
    per_pair = defaultdict(lambda: {"veh_sec": 0.0, "ttc_min": 9e9,
                                    "t_first": None, "t_last": None,
                                    "gap_min": 9e9, "dv_max": 0.0})
    prev_state: dict[int, bool] = {}

    for k in range(n_steps):
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 2:
            continue
        lead, gap = leader_table(x, ok)
        t = k * STEP
        for i in np.where(ok)[0]:
            if abs(x[i] - TARGET_X) > BAND:
                continue                  # 以后车是否在带内为准
            j = lead[i]
            if j < 0:
                continue
            g = gap[i]
            dv = v[i] - v[j]
            if not np.isfinite(g) or g <= 0.5 or dv <= 0.05:
                continue                  # 不闭合不计低 TTC
            ttc = g / dv
            if ttc >= TTC_THR:
                continue
            total_veh_sec += STEP
            key = (str(ids[i]), str(ids[j]))
            rec = per_pair[key]
            rec["veh_sec"] += STEP
            rec["ttc_min"] = min(rec["ttc_min"], ttc)
            rec["gap_min"] = min(rec["gap_min"], g)
            rec["dv_max"] = max(rec["dv_max"], dv)
            if rec["t_first"] is None:
                rec["t_first"] = t
            rec["t_last"] = t

    top = sorted(per_pair.items(), key=lambda kv: -kv[1]["veh_sec"])[:15]
    return {
        "label": label,
        "arm": arm_key,
        "total_low_ttc_veh_sec": round(total_veh_sec, 2),
        "n_pairs": len(per_pair),
        "top_pairs": [
            {
                "follower": k[0], "leader": k[1],
                "veh_sec": round(r["veh_sec"], 2),
                "share": round(r["veh_sec"] / total_veh_sec, 3) if total_veh_sec else 0,
                "ttc_min_s": round(r["ttc_min"], 2),
                "gap_min_m": round(r["gap_min"], 2),
                "closing_max_mps": round(r["dv_max"], 2),
                "t_first_rel_event_s": round((r["t_first"] or 0) - t0, 2),
                "t_last_rel_event_s": round((r["t_last"] or 0) - t0, 2),
                "duration_s": round(r["veh_sec"], 2),
            }
            for k, r in top
        ],
    }


def main() -> int:
    src = Path("code/outputs/analysis/P3_hw40_r06_ids/arms.npz")
    d = np.load(src, allow_pickle=False)
    t0 = float(d["event_t0"])
    print(f"源: {src}   事件 t0 = {t0} s\n")

    out = {"source": str(src), "event_t0_s": t0, "ttc_threshold_s": TTC_THR,
           "target_band": [TARGET_X - BAND, TARGET_X + BAND], "arms": []}

    for key, ids_key in (("plain", "plain_ids"), ("stop", "stop_ids")):
        ids = [str(x) for x in d[ids_key]]
        r = analyse(key, d[f"{key}_pos"], d[f"{key}_spd"], ids, t0, key)
        out["arms"].append(r)
        print(f"=== {key} 臂 ===")
        print(f"  低 TTC 总计 {r['total_low_ttc_veh_sec']} 车·秒，涉及 {r['n_pairs']} 个车对")
        for p in r["top_pairs"][:6]:
            print(f"    {p['follower']:>8} 跟 {p['leader']:<8} "
                  f"{p['veh_sec']:>6.2f} 车·秒 ({p['share']:.0%})  "
                  f"TTCmin {p['ttc_min_s']:.2f}s  净距min {p['gap_min_m']:.2f}m  "
                  f"闭合max {p['closing_max_mps']:.2f}m/s  "
                  f"t={p['t_first_rel_event_s']:+.1f}~{p['t_last_rel_event_s']:+.1f}s")
        print()

    dst = Path("code/outputs/analysis/P3_forensics")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "low_ttc.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written: {dst / 'low_ttc.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())