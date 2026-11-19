"""逐帧分解旧场景的低 TTC 暴露，并重算 DRAC（GPT 第四十一轮 Q1/Q6 要求）

阶段：P3 ｜ 主指标换轨
脚本：code/scripts/p3_audits/decompose_low_ttc_drac.py
数据：code/outputs/analysis/P3_hw40_r06_ids/arms.npz
产物：code/outputs/analysis/P3_forensics/low_ttc_decomposed.json

为什么要拆：
  GPT 原话——「必须拆分**所有**低 TTC 帧，不能用每次试验的一个最小值代替」。
  旧的 22.9 车·秒只是总量，看不出是「高速冲向静止队尾」还是「低速蠕行收尾」。

新主指标（GPT 第四十一轮 Q2/Q3）：
  DRAC = c² / (2g)，c = 闭合速度、g = 物理净距（不减 minGap）
  即「前车保持当前速度时，后车恰好不撞所需的恒定减速度」
  主阈值 3.4 m/s²，敏感性 3.0 与 4.5
  同一次连续逼近超过阈值的帧合并成一个「事件」，记录峰值

分层变量（不排除任何一类）：
  * 后车速度：<5 / 5–15 / 15–25 / >25 m/s
  * 前车状态：运动中 / 已停住（<0.1 m/s）
  * 闭合速度：<2 / 2–5 / 5–10 / >10 m/s
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

VEH_LEN = 5.0
TARGET_X = 4000.0
BAND = 50.0
STEP = 0.05
TTC_THR = 2.0
DRAC_MAIN = 3.4
DRAC_SENS = (3.0, 4.5)
LEADER_STOPPED = 0.1


def leader_table(x: np.ndarray, ok: np.ndarray):
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


def vbin(v: float) -> str:
    if v < 5:
        return "<5"
    if v < 15:
        return "5-15"
    if v < 25:
        return "15-25"
    return ">25"


def cbin(c: float) -> str:
    if c < 2:
        return "<2"
    if c < 5:
        return "2-5"
    if c < 10:
        return "5-10"
    return ">10"


def analyse(pos, spd, ids, t0: float, label: str) -> dict:
    frames = []          # 每个低 TTC 帧一条记录
    for k in range(pos.shape[0]):
        x = pos[k].astype(np.float64)
        v = spd[k].astype(np.float64)
        ok = np.isfinite(x) & np.isfinite(v)
        if ok.sum() < 2:
            continue
        lead, gap = leader_table(x, ok)
        for i in np.where(ok)[0]:
            if abs(x[i] - TARGET_X) > BAND:
                continue
            j = lead[i]
            if j < 0:
                continue
            g = gap[i]
            c = v[i] - v[j]
            if not np.isfinite(g) or g <= 0.01 or c <= 0.05:
                continue
            ttc = g / c
            if ttc >= TTC_THR:
                continue
            drac = (c * c) / (2.0 * g)
            frames.append({
                "t": k * STEP, "t_rel": k * STEP - t0,
                "follower": str(ids[i]), "leader": str(ids[j]),
                "v_f": float(v[i]), "v_l": float(v[j]), "c": float(c),
                "g": float(g), "ttc": float(ttc), "drac": float(drac),
                "leader_stopped": bool(v[j] < LEADER_STOPPED),
            })

    if not frames:
        return {"label": label, "n_frames": 0}

    t = np.array([f["t"] for f in frames])
    drac = np.array([f["drac"] for f in frames])
    vf = np.array([f["v_f"] for f in frames])
    c = np.array([f["c"] for f in frames])
    ttc = np.array([f["ttc"] for f in frames])
    stopped = np.array([f["leader_stopped"] for f in frames])

    # 分层统计
    by_v = defaultdict(lambda: {"frames": 0, "veh_sec": 0.0, "drac_max": 0.0})
    by_c = defaultdict(lambda: {"frames": 0, "veh_sec": 0.0, "drac_max": 0.0})
    for f in frames:
        a = by_v[vbin(f["v_f"])]
        a["frames"] += 1
        a["veh_sec"] += STEP
        a["drac_max"] = max(a["drac_max"], f["drac"])
        b = by_c[cbin(f["c"])]
        b["frames"] += 1
        b["veh_sec"] += STEP
        b["drac_max"] = max(b["drac_max"], f["drac"])

    # DRAC 事件合并：同一后车、连续帧、超过阈值 -> 一个事件
    events = []
    cur = None
    for f in frames:
        over = f["drac"] >= DRAC_MAIN
        if over and cur and cur["follower"] == f["follower"] and (f["t"] - cur["t_last"]) <= STEP * 1.5:
            cur["t_last"] = f["t"]
            cur["peak"] = max(cur["peak"], f["drac"])
            cur["n"] += 1
        elif over:
            if cur:
                events.append(cur)
            cur = {"follower": f["follower"], "leader": f["leader"],
                   "t_first": f["t"], "t_last": f["t"], "peak": f["drac"], "n": 1}
    if cur:
        events.append(cur)

    return {
        "label": label,
        "n_frames": len(frames),
        "veh_sec": round(len(frames) * STEP, 2),
        "n_vehicles_involved": len({f["follower"] for f in frames}),
        "follower_speed_mps": {
            "min": round(float(vf.min()), 2), "p50": round(float(np.median(vf)), 2),
            "max": round(float(vf.max()), 2)},
        "closing_mps": {
            "min": round(float(c.min()), 2), "p50": round(float(np.median(c)), 2),
            "max": round(float(c.max()), 2)},
        "ttc_s": {"min": round(float(ttc.min()), 3),
                  "p50": round(float(np.median(ttc)), 3)},
        "drac_mps2": {"min": round(float(drac.min()), 3),
                      "p50": round(float(np.median(drac)), 3),
                      "p90": round(float(np.percentile(drac, 90)), 3),
                      "max": round(float(drac.max()), 3)},
        "frac_leader_stopped": round(float(stopped.mean()), 3),
        "by_follower_speed": {k: {"frames": v["frames"],
                                  "veh_sec": round(v["veh_sec"], 2),
                                  "drac_max": round(v["drac_max"], 2)}
                              for k, v in sorted(by_v.items())},
        "by_closing_speed": {k: {"frames": v["frames"],
                                 "veh_sec": round(v["veh_sec"], 2),
                                 "drac_max": round(v["drac_max"], 2)}
                             for k, v in sorted(by_c.items())},
        "drac_events": {
            "threshold_main": DRAC_MAIN,
            "n_events": len(events),
            "events": [{**e, "t_first": round(e["t_first"], 2),
                        "t_last": round(e["t_last"], 2),
                        "peak": round(e["peak"], 2)} for e in events[:20]],
        },
        "drac_exceed_frames": {f"{thr}": int((drac >= thr).sum()) for thr in DRAC_SENS},
    }


def main() -> int:
    src = Path("code/outputs/analysis/P3_hw40_r06_ids/arms.npz")
    d = np.load(src, allow_pickle=False)
    t0 = float(d["event_t0"])
    out = {"source": str(src), "event_t0_s": t0,
           "ttc_threshold_s": TTC_THR, "drac_main": DRAC_MAIN, "arms": []}

    for key, ids_key in (("plain", "plain_ids"), ("stop", "stop_ids")):
        ids = [str(x) for x in d[ids_key]]
        r = analyse(d[f"{key}_pos"], d[f"{key}_spd"], ids, t0, key)
        out["arms"].append(r)
        print(f"=== {key} 臂 ===")
        if r["n_frames"] == 0:
            print("  无低 TTC 帧\n")
            continue
        print(f"  低 TTC 帧 {r['n_frames']}，合计 {r['veh_sec']} 车·秒，"
              f"涉及 {r['n_vehicles_involved']} 辆后车")
        print(f"  后车速度 {r['follower_speed_mps']['min']}–{r['follower_speed_mps']['max']} m/s "
              f"(中位 {r['follower_speed_mps']['p50']})")
        print(f"  闭合速度 {r['closing_mps']['min']}–{r['closing_mps']['max']} m/s "
              f"(中位 {r['closing_mps']['p50']})")
        print(f"  DRAC 中位 {r['drac_mps2']['p50']}，p90 {r['drac_mps2']['p90']}，"
              f"最大 {r['drac_mps2']['max']} m/s²")
        print(f"  前车已停住的帧占比 {r['frac_leader_stopped']:.1%}")
        print(f"  DRAC ≥3.4 的事件数：{r['drac_events']['n_events']}")
        print(f"  超阈帧数：{r['drac_exceed_frames']}")
        print("  按后车速度分层：")
        for k, v in r["by_follower_speed"].items():
            print(f"    {k:>6} m/s: {v['frames']:>6} 帧 ({v['veh_sec']:>6.2f} 车·秒)  "
                  f"DRACmax {v['drac_max']}")
        print("  按闭合速度分层：")
        for k, v in r["by_closing_speed"].items():
            print(f"    {k:>6} m/s: {v['frames']:>6} 帧 ({v['veh_sec']:>6.2f} 车·秒)  "
                  f"DRACmax {v['drac_max']}")
        print()

    dst = Path("code/outputs/analysis/P3_forensics")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "low_ttc_decomposed.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written: {dst / 'low_ttc_decomposed.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())